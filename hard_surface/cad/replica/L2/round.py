"""One replica round: build -> silhouette IoU vs registered refs -> hq render -> overlays.

venv_cad python replica/L2/round.py <round_no> [--no-render]
out/replica/L2/r<N>/ ; appends replica/L2/rounds.jsonl
"""
import json
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAD)
from cadkit import runner  # noqa: E402

rnd = int(sys.argv[1])
out = os.path.join(CAD, "out", "replica", "L2", f"r{rnd}")
os.makedirs(out, exist_ok=True)
t0 = time.time()
p = subprocess.run([runner.PY, "-m", "cadkit.worker", os.path.join(HERE, "model.py"), out, "--tris", "6000", "--hq"],
                   capture_output=True, text=True, timeout=5400, cwd=CAD, env=dict(os.environ, PYTHONPATH=CAD))
sp = os.path.join(out, "state.json")
st = json.load(open(sp)) if os.path.exists(sp) else {"ok": False, "stderr": p.stderr[-3000:]}
rec = {"round": rnd, "ok": st.get("ok"), "build_s": st.get("exec_s")}
if not st.get("ok"):
    rec["err"] = (st.get("traceback") or st.get("error") or st.get("stderr") or p.stderr)[-2500:]
    print(json.dumps(rec, indent=1)); sys.exit(1)

R = np.load(os.path.join(CAD, "refs", "L2", "registered.npz"))
G = float(R["grid"])
mz = np.load(os.path.join(out, "mesh.npz"))
Vs, Ts, off = [], [], 0
for k in sorted(f for f in mz.files if f.startswith("v_")):
    Vs.append(mz[k]); Ts.append(mz["t_" + k[2:]] + off); off += len(mz[k])
V, T = np.concatenate(Vs), np.concatenate(Ts)
if np.ptp(V[:, 0]) < 1.0:
    V = V * 1000.0  # metres -> mm


def raster(a, b, lo_a, lo_b, shape):
    im = Image.new("1", (shape[0], shape[1]), 0)
    d = ImageDraw.Draw(im)
    A = (V[:, a] - lo_a) / G
    B = (V[:, b] - lo_b) / G
    for t in T:
        d.polygon([(A[i], B[i]) for i in t], fill=1)
    return np.array(im).T  # [a, b]


views = {"top": (0, 1, -70, -45, R["top"]), "side": (0, 2, -70, -5, R["side"])}
iou, err = {}, {}
for name, (a, b, la, lb, ref) in views.items():
    mm = raster(a, b, la, lb, ref.shape)
    iou[name] = round(float((mm & ref).sum() / max(1, (mm | ref).sum())), 4)
    rgb = np.full(ref.shape + (3,), 255, np.uint8)
    rgb[ref & ~mm] = (220, 60, 60)      # ref only: red (model too small)
    rgb[mm & ~ref] = (60, 110, 230)     # model only: blue (model too big)
    rgb[mm & ref] = (170, 170, 170)
    img = Image.fromarray(np.flipud(rgb.transpose(1, 0, 2)) if name == "side" else rgb.transpose(1, 0, 2))
    if name == "side":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)  # right view: front on the right, like the ref photo
    img.save(os.path.join(out, f"overlay_{name}.png"))
    # per-station error (mm) along X
    rows = []
    for X in range(-60, 61, 10):
        i = int((X - la) / G)
        rm, mmc = np.where(ref[i])[0], np.where(mm[i])[0]
        if len(rm) and len(mmc):
            rows.append((X, round((mmc.min() - rm.min()) * G, 1), round((mmc.max() - rm.max()) * G, 1)))
    err[name] = rows
bb = st["bbox"]["size"]
rec.update(iou=iou, bbox_mm=[round(x * (1000 if bb[0] < 1 else 1), 1) for x in bb], valid=st.get("all_valid"),
           faces=st.get("faces"), ops=st.get("ops_summary"), events=[o for o in st["ops"] if o.get("status") != "ok"],
           station_err_lo_hi_mm=err)
if "--no-render" not in sys.argv:
    runner._blender("render_hq.py", [st["hq_glb"], os.path.join(out, "render"), "--res", "900"], 900)
rec["total_s"] = round(time.time() - t0, 1)
with open(os.path.join(HERE, "rounds.jsonl"), "a") as f:
    f.write(json.dumps(rec, default=str) + "\n")
print(json.dumps(rec, indent=1, default=str))
