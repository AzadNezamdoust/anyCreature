"""Benchmarks: C++ engine vs Python kit (cadkit.tools.Model) on the replica L1 journal (cases.py).
Writes engine/tests/bench_report.json. Run with E:\\gen3d\\venv_cad\\Scripts\\python.exe engine/tests/bench.py"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(CAD, "out", "engine_bench")
sys.path.insert(0, CAD)
sys.path.insert(0, HERE)
os.makedirs(OUT, exist_ok=True)
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)

from cases import CASES  # noqa: E402

J = CASES["replica_L1"]
R = {}


def t(f, n=1):
    best = 1e9
    for _ in range(n):
        t0 = time.perf_counter()
        r = f()
        best = min(best, time.perf_counter() - t0)
    return best * 1000, r


def node_of(op_index):
    return op_index  # linear journal: node id == op index


# ---------------------------------------------------------------- cold start
code = "import time;t=time.perf_counter();import sys;sys.path.insert(0,r'%s');import cadkit.tools;print(time.perf_counter()-t)" % CAD
p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, creationflags=NOWIN)
R["cold_start_py_import_s"] = round(float(p.stdout.strip().splitlines()[-1]), 2)
from cadkit.engine_client import Engine  # noqa: E402
ms, eng = t(lambda: Engine())
R["cold_start_cpp_ms"] = round(ms, 1)

# ---------------------------------------------------------------- full build
from cadkit.tools import Model  # noqa: E402


def py_build():
    m = Model()
    for op, prm in J:
        m.run(op, **prm)
    return m


def cpp_build():
    eng.new("L1")
    for op, prm in J:
        eng.run(op, session="L1", **prm)


R["full_build_py_ms"], pm = t(py_build)
R["full_build_cpp_ms"], _ = t(cpp_build)
eng2 = Engine(env={"CADENGINE_ISOLATE": "0"})


def cpp_build_noiso():
    eng2.new("L1")
    for op, prm in J:
        eng2.run(op, session="L1", **prm)


R["full_build_cpp_noisolate_ms"], _ = t(cpp_build_noiso)

# ---------------------------------------------------------------- edits (journal stays, one param changes)
last = len(J) - 1                       # move bolt
fil = 1                                 # plan-corner fillet radius (op 1): replays everything after it
pcb = next(i for i, (op, p) in enumerate(J) if op == "fillet" and p["body"] == "pcb")


def py_edit(n, k, v):
    return lambda: pm.set_param(n, k, v)


def cpp_edit(e, n, k, v):
    return lambda: e.set_param(n, k, v, session="L1")


R["late_edit_py_ms"], _ = t(py_edit(last, "by", [-20, 76, 7.5]))
R["late_edit_cpp_ms"], _ = t(cpp_edit(eng, last, "by", [-20, 76, 7.5]))
R["mid_edit_pcb_fillet_py_ms"], _ = t(py_edit(pcb, "radius", 2.5))
R["mid_edit_pcb_fillet_cpp_ms"], _ = t(cpp_edit(eng, pcb, "radius", 2.5))
R["early_edit_py_ms"], _ = t(py_edit(fil, "radius", 5.5))
R["early_edit_cpp_ms"], r = t(cpp_edit(eng, fil, "radius", 5.5))
R["early_edit_cpp_replayed_ops"] = r["replayed_ops"]
R["early_edit_cpp_noisolate_ms"], _ = t(cpp_edit(eng2, fil, "radius", 5.5))
R["revert_early_edit_py_ms"], _ = t(py_edit(fil, "radius", 6.0))
R["revert_early_edit_cpp_ms"], r = t(cpp_edit(eng, fil, "radius", 6.0))
R["revert_early_edit_cpp_replayed_ops"] = r["replayed_ops"]

# ---------------------------------------------------------------- GPU
sheet = os.path.join(OUT, "L1_sheet.png")
r0 = eng.render(sheet, session="L1", res=300)                 # first: tessellation + shader warm-up
R["render_first_ms"] = r0["total_ms"]
ms, r1 = t(lambda: eng.render(sheet, session="L1", res=300), 5)
R["render_6view_clay_ms"] = round(ms, 1)
R["render_6view_clay_gpu_ms"] = r1["gpu_ms"]
R["render_6view_clay_png_ms"] = r1["encode_ms"]
ms, r2 = t(lambda: eng.render(os.path.join(OUT, "L1_sheet3.jpg"), session="L1", res=300,
                              modes=["clay", "zebra", "curvature"]), 3)
R["render_18tile_clay_zebra_curv_ms"] = round(ms, 1)
R["renderer"] = r1["renderer"]
R["tris"] = r1["tris"]
eng.set_param(pcb, "radius", 3.0, session="L1")
ms, r3 = t(lambda: eng.render(sheet, session="L1", res=300))
R["render_after_edit_ms"] = round(ms, 1)
R["render_after_edit_tess_ms"] = r3["tess_ms"]

# silhouette IoU: front mask of the model itself as a 'reference' (sanity: IoU ~1) + Python compare_to_ref on it
mask = os.path.join(OUT, "L1_front_mask.png")
eng.render(mask, session="L1", res=600, views=["front"], mode="mask", cols=1)
eng.register_ref("front", mask, view="front")
ms, iou = t(lambda: eng.iou(session="L1"), 5)
R["iou_cpp_ms"] = round(ms, 2)
R["iou_cpp"] = iou["refs"]["front"]["iou"]
from cadkit.tools import query  # noqa: E402
ms, piou = t(lambda: query.compare_to_ref(pm, mask, view="front"))
R["iou_py_ms"] = round(ms, 1)
R["iou_py"] = piou["iou"]

# deviation heatmap: STEP round trip (export -> import) vs original white lid
step = os.path.join(OUT, "L1_white.step")
eng.run("export_step", session="L1", path=step, objects=["white"])
eng.run("import_step", session="L1", name="white_rt", path=step)
ms, dv = t(lambda: eng.deviation("white", "white_rt", heatmap=os.path.join(OUT, "L1_dev.png"), session="L1"), 3)
R["deviation_cpp_ms"] = round(ms, 1)
R["deviation_gpu_ms"] = dv["gpu_ms"]
R["deviation_max_mm"] = dv["a_to_b"]["max"]
R["deviation_pairs"] = dv["points"] * dv["ref_tris"]
R["isolation"] = eng.stats("L1")["isolation"]
eng.close()
eng2.close()
for k, v in R.items():
    print(f"{k:40s} {v}")
json.dump(R, open(os.path.join(HERE, "bench_report.json"), "w"), indent=1)
