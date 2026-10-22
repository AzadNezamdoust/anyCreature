"""High-poly + CAD-aware low-poly via B-rep (re)tessellation. Every triangle carries its B-rep face id, so face
boundaries survive exactly at every LOD (OCCT meshes each face against shared edge discretisations -> watertight)."""
from __future__ import annotations

import os
import runpy
import sys
import time

import numpy as np

from cadkit.worker import collect_parts, mesh_shape, _hex


def load_model(model_py):
    sys.path.insert(0, os.path.dirname(os.path.abspath(model_py)))
    ns = runpy.run_path(model_py, run_name="__cadmodel__")
    scale = 0.001 if ns.get("UNITS", "m") == "mm" else 1.0
    return collect_parts(ns), scale, ns


def _diag(parts):
    from build123d import Compound
    return Compound([p for p, _ in parts.values()]).bounding_box().diagonal


def _mesh_all(parts, lin, ang):
    return {k: mesh_shape(s, lin, ang) for k, (s, _) in parts.items()}


def retess_to_budget(parts, budget, lin0=None, ang0=0.35, iters=14):
    """Coarsest-needed B-rep tessellation <= budget tris (geometric search on deflection). Returns meshes, tris, params."""
    diag = _diag(parts)
    lin, ang = lin0 or diag * 0.0015, ang0
    best = None
    for it in range(iters):
        ms = _mesh_all(parts, lin, ang)
        tris = sum(len(m[1]) for m in ms.values())
        best = (ms, tris, {"linear_deflection": lin, "angular_deflection": ang, "iterations": it + 1})
        if tris <= budget:
            break
        lin *= 1.45
        ang = min(ang * 1.3, 1.4)
    return best


def build_meshes(model_py, out_npz, lod_fracs=(1.0, 0.5, 0.25), lod0_budget=None, hi_rel=3e-4, hi_ang=0.08):
    """Exec model, write npz with hi + LOD tessellations. Returns info dict.
    LOD0 budget: model TRI_BUDGET, else lod0_budget, else 8000."""
    t0 = time.time()
    parts, S, ns = load_model(model_py)
    diag = _diag(parts)
    hi = _mesh_all(parts, diag * hi_rel, hi_ang)
    budget = int(lod0_budget or ns.get("TRI_BUDGET") or 8000)
    names = list(parts)
    arrs = {"names": np.array(names), "colours": np.array([_hex(parts[k][1]) for k in names], "f4"),
            "scale": np.array(S), "lod_fracs": np.array(lod_fracs, "f4")}
    info = {"parts": names, "scale": S, "brep_faces": {k: len(parts[k][0].faces()) for k in names},
            "hi_tris": sum(len(m[1]) for m in hi.values()), "lod0_budget": budget, "lods": []}
    for i, k in enumerate(names):
        V, T, F = hi[k]
        arrs[f"hi_v_{i}"], arrs[f"hi_t_{i}"], arrs[f"hi_f_{i}"] = V * S, T, F
    lin = None
    for li, fr in enumerate(lod_fracs):
        ms, tris, p = retess_to_budget(parts, int(budget * fr), lin0=lin)
        lin = p["linear_deflection"]
        info["lods"].append({"lod": li, "budget": int(budget * fr), "tris": tris,
                             "linear_deflection_m": lin * S, "angular_deflection": p["angular_deflection"]})
        for i, k in enumerate(names):
            V, T, F = ms[k]
            arrs[f"l{li}_v_{i}"], arrs[f"l{li}_t_{i}"], arrs[f"l{li}_f_{i}"] = V * S, T, F
    info["diag_m"] = diag * S
    info["tess_s"] = round(time.time() - t0, 2)
    os.makedirs(os.path.dirname(os.path.abspath(out_npz)), exist_ok=True)
    np.savez_compressed(out_npz, **arrs)
    return info
