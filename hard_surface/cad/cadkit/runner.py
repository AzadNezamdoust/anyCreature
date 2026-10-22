"""Host-side API (plain Python, no OCCT import): run a model script in a subprocess with timeout, mesh in Blender,
render, measure.  Used by mcp_server.py and the pilot loop.

    from cadkit.runner import run_model, mesh, render, measure
    st = run_model("pilot/rifle/model.py", "out/rifle/r1", timeout=120, tris=8000)
"""
from __future__ import annotations

import json
import os
import subprocess

_NOWIN_KW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}  # no stray console windows (Windows)
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(HERE)
BLENDER = os.environ.get("CADKIT_BLENDER", r"E:\gen3d\blender\blender-5.2.2-windows-x64\blender.exe")
PY = os.environ.get("CADKIT_PYTHON", sys.executable)


def _blender(script, args, timeout):
    cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "--python", os.path.join(HERE, script), "--"] + args
    p = subprocess.run(**_NOWIN_KW, args=cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        tail = (p.stdout[-1500:] + "\n" + p.stderr[-1500:]).strip()
        raise RuntimeError(f"blender {script} failed (exit {p.returncode}):\n{tail}")
    return p.stdout


def run_model(script, out, timeout=180, tris=None, step=True):
    """Exec the model in a fresh subprocess. Returns state dict (state.json). Never raises on model errors."""
    os.makedirs(out, exist_ok=True)
    args = [PY, "-m", "cadkit.worker", os.path.abspath(script), os.path.abspath(out)]
    if tris:
        args += ["--tris", str(tris)]
    if not step:
        args += ["--no-step"]
    env = dict(os.environ, PYTHONPATH=CAD + os.pathsep + os.environ.get("PYTHONPATH", ""))
    t0 = time.time()
    try:
        p = subprocess.run(**_NOWIN_KW, args=args, capture_output=True, text=True, timeout=timeout, env=env, cwd=CAD)
    except subprocess.TimeoutExpired:
        st = {"ok": False, "error": f"timeout after {timeout}s",
              "hint": "model too slow: big fillet sets / many booleans / fine splines. Split work, fillet fewer "
                      "edges per call, or raise timeout."}
        json.dump(st, open(os.path.join(out, "state.json"), "w"), indent=1)
        return st
    sp = os.path.join(out, "state.json")
    if not os.path.exists(sp):
        return {"ok": False, "error": "worker crashed before writing state", "stderr": p.stderr[-2000:],
                "hint": "OCCT segfault/abort - usually a degenerate boolean; bisect the script."}
    st = json.load(open(sp))
    st["wall_s"] = round(time.time() - t0, 2)
    return st


def mesh(out, lods="0.5,0.25", smart_uv=False, timeout=600):
    args = [os.path.abspath(out), "--lods", lods] + (["--smart-uv"] if smart_uv else [])
    _blender("blender_mesh.py", args, timeout)
    return json.load(open(os.path.join(out, "mesh_report.json")))


def render(src, out_dir, res=640, timeout=600):
    _blender("render.py", [os.path.abspath(src), os.path.abspath(out_dir), "--res", str(res)], timeout)
    return json.load(open(os.path.join(out_dir, "render_report.json")))


def measure(state, spec=None):
    """Markdown measure table from a state dict (+ optional spec {part: [Lx,Wy,Hz]} or {"L":..} overall)."""
    rows = ["| part | size x | size y | size z | volume | faces | valid |", "|---|---|---|---|---|---|---|"]
    for k, b in state.get("bodies", {}).items():
        s = b["size"]
        rows.append(f"| {k} | {s[0]:.4f} | {s[1]:.4f} | {s[2]:.4f} | {b['volume']:.3e} | {b['faces']} | {b['valid']} |")
    s = state.get("bbox", {}).get("size")
    if s:
        rows.append(f"| **ALL** | {s[0]:.4f} | {s[1]:.4f} | {s[2]:.4f} | | {state.get('faces')} | {state.get('all_valid')} |")
    sp = state.get("spec") or {}
    if spec:
        size = dict(zip("LWH", s or [0, 0, 0]))
        sp = {k: {"target": v, "got": size.get(k), "err_pct": round(100 * (size[k] - v) / v, 1)}
              for k, v in spec.items() if k in size}
    if sp:
        rows += ["", "| dim | target | got | err % |", "|---|---|---|---|"]
        rows += [f"| {k} | {v['target']} | {v['got']} | {v['err_pct']} |" for k, v in sp.items()]
    return "\n".join(rows)
