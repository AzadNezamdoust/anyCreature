"""One replica round: build model.py -> out/replica/L5/r<N>/, hq render, silhouette IoU vs refs, overlays.

venv_cad python replica/L5/round.py <N>
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAD)
sys.path.insert(0, HERE)
from cadkit import runner  # noqa: E402

rnd = int(sys.argv[1])
out = os.path.join(CAD, "out", "replica", "L5", f"r{rnd}")
os.makedirs(out, exist_ok=True)
t0 = time.time()
p = subprocess.run([runner.PY, "-m", "cadkit.worker", os.path.join(HERE, "model.py"), out, "--tris", "60000", "--hq"],
                   capture_output=True, text=True, timeout=1800, cwd=CAD, env=dict(os.environ, PYTHONPATH=CAD))
print(p.stdout[-3000:])
st = json.load(open(os.path.join(out, "state.json")))
rec = {"round": rnd, "ok": st.get("ok"), "build_s": round(time.time() - t0, 1)}
if not st.get("ok"):
    rec.update(error=st.get("error"), tb=st.get("traceback", "")[-1500:])
    print(json.dumps(rec, indent=1))
    sys.exit(1)
rec.update(bbox=st["bbox"], valid=st["all_valid"], events=[o for o in st["ops"] if o.get("status") != "ok"])
if "--norender" not in sys.argv:
    runner._blender("render_hq.py", [st["hq_glb"], os.path.join(out, "render"), "--res", "1100"], 900)
import compare  # noqa: E402
rec["compare"] = compare.run(st["hq_glb"], out)
with open(os.path.join(HERE, "rounds.jsonl"), "a") as f:
    f.write(json.dumps(rec, default=str) + "\n")
print(json.dumps(rec, indent=1, default=str))
