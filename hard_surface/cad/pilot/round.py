"""One render-compare round for a pilot asset.

venv_cad python pilot/round.py <asset> <round_no> [--res 640]
Runs pilot/<asset>/model.py -> out/pilot/<asset>/r<N>/ (state.json, model.step, model.glb, LODs, render/sheet.png),
snapshots the script as r<N>_model.py, appends a line to pilot/<asset>/rounds.jsonl (time, tris, op summary).
"""
import json
import os
import shutil
import sys
import time

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
from cadkit import runner  # noqa: E402

asset, rnd = sys.argv[1], int(sys.argv[2])
res = int(sys.argv[sys.argv.index("--res") + 1]) if "--res" in sys.argv else 640
src = os.path.join(CAD, "pilot", asset, "model.py")
out = os.path.join(CAD, "out", "pilot", asset, f"r{rnd}")
os.makedirs(out, exist_ok=True)
shutil.copy(src, os.path.join(CAD, "pilot", asset, f"r{rnd}_model.py"))
t0 = time.time()
st = runner.run_model(src, out, timeout=300)
rec = {"round": rnd, "ok": st.get("ok"), "t_model_s": round(time.time() - t0, 1)}
if st.get("ok"):
    t1 = time.time()
    mr = runner.mesh(out)
    rr = runner.render(os.path.join(out, "model.glb"), os.path.join(out, "render"), res=res)
    rec.update(t_mesh_render_s=round(time.time() - t1, 1), tris=mr["tris"], lod_tris=mr["lod_tris"],
               bodies=st["body_count"], all_valid=st["all_valid"], size=st["bbox"]["size"], spec=st.get("spec"),
               ops=st["ops_summary"], sheet=os.path.join(out, "render", "sheet.png"))
    events = [o for o in st["ops"] if o.get("status") != "ok"]
    rec["op_events"] = events
else:
    rec.update(error=st.get("error"), hint=st.get("hint"), tb=(st.get("traceback") or "")[-800:],
               ops=[o for o in st.get("ops", []) if o.get("status") != "ok"])
with open(os.path.join(CAD, "pilot", asset, "rounds.jsonl"), "a") as f:
    f.write(json.dumps(rec, default=str) + "\n")
print(json.dumps(rec, indent=1, default=str))
if st.get("ok"):
    print(runner.measure(st))
