"""Exports (spec 3 Export, 5.4 game meshing, 5.13): STEP / glTF / OBJ / STL, run dir for the existing Blender game
mesh step (cadkit/blender_mesh.py) and the smooth + zebra surface render (cadkit/render_hq.py)."""
from __future__ import annotations

import json
import os

import numpy as np
from build123d import Color, Compound, Unit, export_gltf, export_step, export_stl

from .core import ToolError

COLOURS = ["#8a8f96", "#c9a227", "#3b4a5a", "#b04a2f", "#6d8b5a", "#5a5f66"]


def parts_of(model, names=None):
    names = names or [k for k, o in model.objects.items() if o.kind == "solid"]
    if not names:
        raise ToolError("no solids to export")
    out = {}
    for i, k in enumerate(names):
        o = model.get(k)
        out[k] = (o.shape, o.meta.get("colour", COLOURS[i % len(COLOURS)]))
    return out


def _compound(parts):
    kids = []
    for k, (s, c) in parts.items():
        s.label, s.color = k, Color(c)
        kids.append(s)
    return Compound(children=kids)


def export_file(model, path, fmt=None, names=None, fine=False):
    """fmt step|gltf|glb|obj|stl (from extension if None). fine -> dense tessellation (render quality)."""
    fmt = (fmt or os.path.splitext(path)[1][1:]).lower()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    parts = parts_of(model, names)
    comp = _compound(parts)
    dg = comp.bounding_box().diagonal
    if fmt == "step":
        export_step(comp, path)
    elif fmt in ("gltf", "glb"):
        lin, ang = (dg * 1.5e-4, 0.06) if fine else (dg * 1e-3, 0.3)
        export_gltf(comp, path, unit=Unit.M, binary=fmt == "glb", linear_deflection=lin, angular_deflection=ang)
    elif fmt == "stl":
        export_stl(comp, path, tolerance=dg * 1e-3)
    elif fmt == "obj":
        _obj(parts, path, dg)
    else:
        raise ToolError(f"fmt {fmt}", "step|gltf|glb|obj|stl")
    return path


def _obj(parts, path, dg):
    from cadkit.worker import mesh_shape
    lines, off = ["# cadkit.tools OBJ (one group per body, one smoothing group per B-rep face)"], 1
    for k, (s, _) in parts.items():
        V, T, F = mesh_shape(s, dg * 1e-3, 0.3)
        lines.append(f"o {k}")
        lines += [f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in V]
        cur = None
        for (a, b, c), fi in zip(T, F):
            if fi != cur:
                lines.append(f"g {k}_face{fi}")
                lines.append(f"s {fi + 1}")
                cur = fi
            lines.append(f"f {a + off} {b + off} {c + off}")
        off += len(V)
    open(path, "w").write("\n".join(lines) + "\n")


def write_run(model, out, tris=None, names=None, hq=True):
    """Write a worker-compatible run dir: mesh.npz (face-id tessellation), model.step, model_hq.glb, state.json.
    Then runner.mesh(out) -> game glb + LODs, runner._blender('render_hq.py', ...) -> smooth + zebra sheet."""
    from cadkit.worker import _hex, tessellate
    os.makedirs(out, exist_ok=True)
    parts = parts_of(model, names)
    meshes, ntris, tess = tessellate(parts, tris)
    np.savez_compressed(
        os.path.join(out, "mesh.npz"), names=np.array(list(meshes)),
        colours=np.array([_hex(parts[k][1]) for k in meshes], "f4"),
        **{f"v_{i}": mm[0] for i, mm in enumerate(meshes.values())},
        **{f"t_{i}": mm[1] for i, mm in enumerate(meshes.values())},
        **{f"f_{i}": mm[2] for i, mm in enumerate(meshes.values())})
    export_file(model, os.path.join(out, "model.step"), "step", names)
    st = {"ok": True, "tris": ntris, "tessellation": tess, "model": model.state(), "journal": model.to_json()}
    if hq:
        st["hq_glb"] = export_file(model, os.path.join(out, "model_hq.glb"), "glb", names, fine=True)
    json.dump(st, open(os.path.join(out, "state.json"), "w"), indent=1, default=str)
    return st


def game_mesh(model, out, tris=4000, lods="0.5,0.25"):
    from cadkit import runner
    write_run(model, out, tris, hq=False)
    return runner.mesh(out, lods=lods)


def render(model, out, res=900):
    """Smooth (part colours + clay) + zebra surface-quality sheet via cadkit/render_hq.py."""
    from cadkit import runner
    st = write_run(model, out)
    runner._blender("render_hq.py", [st["hq_glb"], os.path.join(out, "render"), "--res", str(res)], 900)
    return os.path.join(out, "render", "sheet.png")
