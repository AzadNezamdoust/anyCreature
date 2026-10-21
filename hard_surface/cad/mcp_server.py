"""cadkit MCP server (stdio). Tools: run_model, get_state, render, measure, export.

Every model run executes in a fresh subprocess (timeout) so a bad script or an OCCT crash never kills the server.
Runs live in <cad>/out/runs/<name>/.  Register: see README.md.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cadkit import runner  # noqa: E402

try:
    from mcp.server.mcpserver import MCPServer as _Server  # mcp >= 2
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

RUNS = os.path.join(HERE, "out", "runs")
server = _Server("cadkit", instructions=(
    "LLM-first B-rep CAD. Write ONE build123d script per model (`from cadkit import *`, set PARTS = {name: (shape, "
    "'#rrggbb')}, optional SPEC = {'L','W','H'} metres, TRI_BUDGET). Undo = edit + re-run. Use safe_fillet / "
    "safe_chamfer / cut / fuse (auto-retry, report max feasible radius) and tag()/face_at()/edges_* selectors "
    "instead of raw indices. Axes: X length (front = -X), Y width (left flank = -Y), Z up. Loop: run_model -> "
    "render -> look at sheet.png -> fix."))


def _dir(name):
    d = os.path.join(RUNS, name)
    os.makedirs(d, exist_ok=True)
    return d


def _short(st):
    keep = ("ok", "error", "hint", "tris", "body_count", "all_valid", "bbox", "faces", "edges", "spec", "ops_summary",
            "tags", "exec_s", "wall_s")
    s = {k: st[k] for k in keep if k in st}
    if not st.get("ok") and "traceback" in st:
        s["traceback_tail"] = st["traceback"][-1200:]
    fails = [o for o in st.get("ops", []) if o.get("status") in ("failed", "reduced", "manifold", "fuzzy")]
    if fails:
        s["op_events"] = fails[:20]
    return s


@server.tool()
def run_model(name: str, script_path: str = "", code: str = "", timeout_s: int = 180, tri_budget: int = 0) -> str:
    """Run a build123d model script (file path or inline code) in a subprocess. Writes out/runs/<name>/{model.py,
    state.json, model.step, mesh.npz}. Returns compact JSON state (validity, bbox, faces, spec errors, fillet/boolean
    events, tags) or the error + a hint on what to try next."""
    d = _dir(name)
    dst = os.path.join(d, "model.py")
    if code:
        open(dst, "w", encoding="utf-8").write(code)
    elif script_path:
        if not os.path.exists(script_path):
            return json.dumps({"ok": False, "error": f"no file {script_path}", "hint": "pass an absolute path or code="})
        if os.path.abspath(script_path) != os.path.abspath(dst):
            shutil.copy(script_path, dst)
    else:
        return json.dumps({"ok": False, "error": "give script_path or code"})
    st = runner.run_model(dst, d, timeout=timeout_s, tris=tri_budget or None)
    return json.dumps(_short(st), default=str)


@server.tool()
def get_state(name: str, full: bool = False) -> str:
    """Last state.json of a run (full=True includes every op record)."""
    p = os.path.join(RUNS, name, "state.json")
    if not os.path.exists(p):
        return json.dumps({"ok": False, "error": f"no run '{name}'", "hint": "call run_model first",
                           "runs": sorted(os.listdir(RUNS)) if os.path.isdir(RUNS) else []})
    st = json.load(open(p))
    return json.dumps(st if full else _short(st), default=str)


@server.tool()
def render(name: str, res: int = 640, smart_uv: bool = False) -> str:
    """Mesh the last run in Blender (sharp edges + UV seams from B-rep faces, LODs, model.glb) and render 6 views.
    Returns paths: sheet.png (top row iso,left,right; bottom front,back,top) - open it and compare to the reference."""
    d = os.path.join(RUNS, name)
    st = json.load(open(os.path.join(d, "state.json"))) if os.path.exists(os.path.join(d, "state.json")) else {}
    if not st.get("ok"):
        return json.dumps({"ok": False, "error": "last run failed or missing", "hint": "fix run_model errors first"})
    try:
        mr = runner.mesh(d, smart_uv=smart_uv)
        rr = runner.render(os.path.join(d, "model.glb"), os.path.join(d, "render"), res=res)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)[-1500:],
                           "hint": "Blender path set by CADKIT_BLENDER env; mesh.npz must exist (run_model ok)."})
    return json.dumps({"ok": True, "sheet": os.path.join(d, "render", "sheet.png"),
                       "views": {v: os.path.join(d, "render", f"view_{v}.png") for v in rr["views"]},
                       "tris": mr["tris"], "lod_tris": mr["lod_tris"], "size": rr["size"]})


@server.tool()
def measure(name: str, spec_json: str = "") -> str:
    """Markdown measure table (per-part size/volume/faces/validity + spec errors). spec_json e.g. '{"L":0.9,"H":0.26}'."""
    p = os.path.join(RUNS, name, "state.json")
    if not os.path.exists(p):
        return f"no run '{name}' - call run_model first"
    return runner.measure(json.load(open(p)), json.loads(spec_json) if spec_json else None)


@server.tool()
def export(name: str, fmt: str = "glb", dest: str = "") -> str:
    """Export a run: fmt 'step' (B-rep, from run_model) or 'glb' (game mesh + LODs, runs Blender meshing if needed).
    dest = optional folder to copy into."""
    d = os.path.join(RUNS, name)
    if fmt == "step":
        src = [os.path.join(d, "model.step")]
    elif fmt == "glb":
        if not os.path.exists(os.path.join(d, "model.glb")):
            try:
                runner.mesh(d)
            except Exception as e:
                return json.dumps({"ok": False, "error": str(e)[-800:]})
        src = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".glb")]
    else:
        return json.dumps({"ok": False, "error": f"fmt {fmt}", "hint": "use step or glb"})
    missing = [s for s in src if not os.path.exists(s)]
    if missing:
        return json.dumps({"ok": False, "error": f"missing {missing}", "hint": "run_model ok first"})
    if dest:
        os.makedirs(dest, exist_ok=True)
        src = [shutil.copy(s, dest) for s in src]
    return json.dumps({"ok": True, "files": src})


import mcp_tools  # noqa: E402  direct-modelling ops (cadkit.tools)
mcp_tools.register(server)

if __name__ == "__main__":
    server.run()
