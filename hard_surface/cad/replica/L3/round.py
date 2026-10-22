"""One render-compare round for a CAD-ladder level.

venv_cad python ladder/round.py L1 <round_no> [--res 900]
ladder/L1/model.py -> out/ladder/L1/r<N>/ (state.json, model.step, model_hq.glb, render/sheet.png);
appends ladder/L1/rounds.jsonl (times, op summary, non-ok op events, script lines).
"""
import json
import os
import sys
import time

CAD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, CAD)
from cadkit import runner  # noqa: E402

lvl, rnd = sys.argv[1], int(sys.argv[2])
res = int(sys.argv[sys.argv.index("--res") + 1]) if "--res" in sys.argv else 900
src = os.path.join(CAD, "replica", lvl, "model.py")
out = os.path.join(CAD, "out", "replica", lvl, f"r{rnd}")
os.makedirs(out, exist_ok=True)
t0 = time.time()
args = [runner.PY, "-m", "cadkit.worker", src, out, "--tris", "4000", "--hq"]
import subprocess  # noqa: E402
p = subprocess.run(args, capture_output=True, text=True, timeout=900, cwd=CAD,
                   env=dict(os.environ, PYTHONPATH=CAD))
st = json.load(open(os.path.join(out, "state.json"))) if os.path.exists(os.path.join(out, "state.json")) else \
    {"ok": False, "error": "crash", "stderr": p.stderr[-2000:]}
rec = {"round": rnd, "ok": st.get("ok"), "build_s": st.get("exec_s"), "total_s": st.get("total_s"),
       "lines": sum(1 for _ in open(src))}
if st.get("ok"):
    t1 = time.time()
    rr = runner._blender("render_hq.py", [st["hq_glb"], os.path.join(out, "render"), "--res", str(res)], 900)
    rec.update(render_s=round(time.time() - t1, 1), hq_tris=json.load(open(os.path.join(out, "render",
               "render_report.json")))["tris"], faces=st["faces"], valid=st["all_valid"], size=st["bbox"]["size"],
               ops_n=len(st["ops"]), ops=st["ops_summary"], sheet=os.path.join(out, "render", "sheet.png"),
               events=[o for o in st["ops"] if o.get("status") != "ok"])
else:
    rec.update(error=st.get("error"), tb=(st.get("traceback") or st.get("stderr") or "")[-1200:],
               events=[o for o in st.get("ops", []) if o.get("status") != "ok"])
with open(os.path.join(CAD, "replica", lvl, "rounds.jsonl"), "a") as f:
    f.write(json.dumps(rec, default=str) + "\n")
print(json.dumps(rec, indent=1, default=str))
