"""Subprocess worker: exec a model script, write state.json, model.step, mesh.npz (face-id tessellation).

usage: python -m cadkit.worker <model.py> <out_dir> [--tris N] [--no-step]
"""
from __future__ import annotations

import json
import os
import runpy
import sys
import time
import traceback

import numpy as np


def _hex(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _mm_to_m(shp):
    """Uniform 0.001 scale that also scales the TopLoc location (build123d Shape.scale left located parts at
    mm offsets: L1 knob ended up 3 m away)."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf, gp_Pnt
    from build123d import Shape
    t = gp_Trsf()
    t.SetScale(gp_Pnt(0, 0, 0), 0.001)
    return Shape.cast(BRepBuilderAPI_Transform(shp.wrapped, t, True).Shape())


S = 1.0  # model-unit -> metre factor for reporting / mesh.npz


def collect_parts(ns):
    parts = ns.get("PARTS")
    if parts is None:
        m = ns.get("MODEL") or ns.get("result") or ns.get("model")
        if m is None:
            raise RuntimeError("model script defined neither PARTS nor MODEL. Set PARTS = {name: (shape, '#rrggbb')}")
        parts = {"model": m}
    out = {}
    for k, v in parts.items():
        shp, col = (v if isinstance(v, tuple) else (v, "#808080"))
        # UNITS="mm": shapes stay in mm (OCCT fillets fail far more at metre scale); the worker reports metres
        # (S below) and exports with unit=MM. Scaling the B-rep itself broke located parts in glTF (L5 r6-7).
        out[k] = (shp, col)
    return out


def mesh_shape(shape, lin, ang):
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.BRepTools import BRepTools
    BRepTools.Clean_s(shape.wrapped)
    BRepMesh_IncrementalMesh(shape.wrapped, lin, False, ang, True)
    V, T, F = [], [], []
    off = 0
    for fi, face in enumerate(shape.faces()):
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face.wrapped, loc)
        if tri is None:
            continue
        tr = loc.Transformation()
        n = tri.NbNodes()
        for i in range(1, n + 1):
            p = tri.Node(i).Transformed(tr)
            V.append((p.X(), p.Y(), p.Z()))
        rev = face.wrapped.Orientation() == TopAbs_REVERSED
        for i in range(1, tri.NbTriangles() + 1):
            a, b, c = tri.Triangle(i).Get()
            T.append((off + a - 1, off + c - 1, off + b - 1) if rev else (off + a - 1, off + b - 1, off + c - 1))
            F.append(fi)
        off += n
    return np.array(V, "f8").reshape(-1, 3), np.array(T, "i4").reshape(-1, 3), np.array(F, "i4")


def tessellate(parts, budget):
    from build123d import Compound
    diag = Compound([p for p, _ in parts.values()]).bounding_box().diagonal
    lin, ang = diag * 0.0015, 0.30
    for it in range(10):
        meshes = {k: mesh_shape(s, lin, ang) for k, (s, _) in parts.items()}
        tris = sum(len(m[1]) for m in meshes.values())
        if budget is None or tris <= budget:
            break
        lin *= 1.6
        ang = min(ang * 1.35, 1.2)
    return meshes, tris, {"linear_deflection": lin, "angular_deflection": ang, "iterations": it + 1}


def state_of(parts, ns, t_exec):
    from build123d import Compound
    from cadkit.ops import LOG
    from cadkit.refs import describe_tags
    bodies = {}
    for k, (s, col) in parts.items():
        bb = s.bounding_box()
        try:
            valid = bool(s.is_valid)
        except Exception:
            valid = False
        bodies[k] = {
            "colour": col, "volume": round(s.volume * S ** 3, 9), "solids": len(s.solids()),
            "faces": len(s.faces()), "edges": len(s.edges()), "valid": valid,
            "bbox_min": [round(v * S, 5) for v in tuple(bb.min)], "bbox_max": [round(v * S, 5) for v in tuple(bb.max)],
            "size": [round(v * S, 5) for v in tuple(bb.size)],
        }
    allbb = Compound([s for s, _ in parts.values()]).bounding_box()
    st = {
        "ok": True, "exec_s": round(t_exec, 2),
        "bodies": bodies, "body_count": len(bodies),
        "all_valid": all(b["valid"] for b in bodies.values()),
        "bbox": {"min": [round(v * S, 5) for v in tuple(allbb.min)], "max": [round(v * S, 5) for v in tuple(allbb.max)],
                 "size": [round(v * S, 5) for v in tuple(allbb.size)]},
        "faces": sum(b["faces"] for b in bodies.values()), "edges": sum(b["edges"] for b in bodies.values()),
        "tags": describe_tags(), "ops": LOG,
        "ops_summary": {
            "fillet_chamfer": sum(1 for o in LOG if o["op"] in ("fillet", "chamfer")),
            "fillet_reduced": sum(1 for o in LOG if o["op"] in ("fillet", "chamfer") and o["status"] == "reduced"),
            "fillet_failed": sum(1 for o in LOG if o["op"] in ("fillet", "chamfer") and o["status"] == "failed"),
            "fillet_retries": sum(o.get("retries", 0) for o in LOG if o["op"] in ("fillet", "chamfer")),
            "booleans": sum(1 for o in LOG if o["op"] == "boolean"),
            "boolean_fuzzy": sum(1 for o in LOG if o["op"] == "boolean" and o["status"] == "fuzzy"),
            "boolean_manifold": sum(1 for o in LOG if o["op"] == "boolean" and o["status"] == "manifold"),
            "boolean_failed": sum(1 for o in LOG if o["op"] == "boolean" and o["status"] == "failed"),
        },
    }
    spec = ns.get("SPEC")
    if spec:
        size = dict(zip("LWH", st["bbox"]["size"]))
        st["spec"] = {k: {"target": v, "got": size.get(k), "err_pct": round(100 * (size[k] - v) / v, 1)}
                      for k, v in spec.items() if k in size}
    return st


def main(argv):
    model, out = argv[0], argv[1]
    budget = int(argv[argv.index("--tris") + 1]) if "--tris" in argv else None
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(model)))
    t0 = time.time()
    try:
        ns = runpy.run_path(model, run_name="__cadmodel__")
        global S
        S = 0.001 if ns.get("UNITS", "m") == "mm" else 1.0
        parts = collect_parts(ns)
        st = state_of(parts, ns, time.time() - t0)
        budget = budget or ns.get("TRI_BUDGET")
        meshes, tris, tess = tessellate(parts, budget)
        st["tris"], st["tessellation"], st["tri_budget"] = tris, tess, budget
        np.savez_compressed(
            os.path.join(out, "mesh.npz"),
            names=np.array(list(meshes)),
            colours=np.array([_hex(parts[k][1]) for k in meshes], "f4"),
            **{f"v_{i}": m[0] * S for i, m in enumerate(meshes.values())},
            **{f"t_{i}": m[1] for i, m in enumerate(meshes.values())},
            **{f"f_{i}": m[2] for i, m in enumerate(meshes.values())},
        )
        if "--no-step" not in argv:
            from build123d import Compound, export_step, Unit
            kids = []
            for k, (s, _) in parts.items():
                s.label = k
                kids.append(s)
            comp = Compound(children=kids)
            export_step(comp, os.path.join(out, "model.step"), unit=Unit.MM if S != 1.0 else Unit.M)
            st["step"] = os.path.join(out, "model.step")
        if "--hq" in argv:  # fine B-rep tessellation for surface-quality renders (not the game mesh)
            from build123d import Compound, export_gltf, Unit, Color
            kids = []
            for k, (s, c) in parts.items():
                s.label, s.color = k, Color(c)
                kids.append(s)
            comp = Compound(children=kids)
            dg = comp.bounding_box().diagonal
            t1 = time.time()
            export_gltf(comp, os.path.join(out, "model_hq.glb"), unit=Unit.MM if S != 1.0 else Unit.M, binary=True,
                        linear_deflection=dg * 3e-4, angular_deflection=0.08)
            st["hq_glb"], st["hq_s"] = os.path.join(out, "model_hq.glb"), round(time.time() - t1, 2)
    except Exception as e:
        tb = traceback.format_exc()
        from cadkit.ops import LOG
        st = {"ok": False, "error": f"{type(e).__name__}: {e}", "traceback": tb[-3000:], "ops": LOG,
              "hint": _hint(e, tb)}
    st["total_s"] = round(time.time() - t0, 2)
    with open(os.path.join(out, "state.json"), "w") as f:
        json.dump(st, f, indent=1, default=str)
    print(json.dumps({k: st[k] for k in ("ok", "total_s") if k in st}))
    return 0 if st["ok"] else 2


def _hint(e, tb):
    s = str(e) + tb
    if "CadOpError" in tb:
        return "a cadkit op gave up; its message says the max feasible radius / what to try."
    if "StdFail_NotDone" in s or "BRep_API: command not done" in s:
        return ("OCCT op not done - usually a fillet/chamfer too big for an adjacent short edge, or a boolean on "
                "coplanar faces. Use safe_fillet/safe_chamfer/cut/fuse from cadkit for auto-retry + diagnosis.")
    if "NameError" in s:
        return "undefined name - the script must start with `from cadkit import *` (build123d is re-exported)."
    if "ValueError" in s and "fillet" in s.lower():
        return "fillet radius too large; try half the radius or select fewer edges."
    return "read the traceback's last frame inside the model script."


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
