"""STEP / IGES import as a journal op + deviation of a model vs an imported reference body.

Legal route only: neutral exchange formats (STEP AP203/214/242, IGES) that the user exports from their own tools
(e.g. Plasticity -> File > Export > STEP). Native .plasticity files and Parasolid .x_t/.x_b are intentionally NOT
parsed (proprietary formats; out of scope by decision, see docs/LEARNINGS.md).
"""
from __future__ import annotations

import hashlib
import os

import numpy as np
from build123d import Compound, Shape, ShapeList

from .core import ToolError, op, resolve

_UNIT_SCALE = {"m": 0.001, "auto": 0.001, "mm": 1.0, "cm": 0.1, "in": 1 / 25.4}  # OCCT reads into mm


def _read(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".step", ".stp"):
        from build123d import import_step
        return import_step(path)
    if ext in (".iges", ".igs"):
        from OCP.IGESControl import IGESControl_Reader
        from OCP.IFSelect import IFSelect_RetDone
        rd = IGESControl_Reader()
        if rd.ReadFile(path) != IFSelect_RetDone:
            raise ToolError(f"IGES read failed: {path}")
        rd.TransferRoots()
        return Shape.cast(rd.OneShape())
    if ext in (".plasticity", ".x_t", ".x_b", ".xmt_txt"):
        raise ToolError(f"{ext} is a proprietary native format and is intentionally not parsed",
                        "export STEP (AP214/242) from the source app and import that")
    raise ToolError(f"unsupported extension {ext}", ".step/.stp/.iges/.igs")


@op("import_step", "exchange: STEP/IGES import -> editable solids (+ sheets), tags per solid and per face")
def import_step(m, name, path, units="auto", tag_faces=True, max_face_tags=300):
    """Read a STEP/IGES file into bodies. units: auto|m (session metres, file values are mm after OCCT unit
    conversion -> x0.001) | mm (keep mm numbers) | cm | in. One solid -> object `name`; several -> name_1..n
    (STEP product labels kept in meta.label). Free sheets -> `name_sheet_i`. Tags: `<obj>` (whole body) and,
    if tag_faces, `<obj>/f<i>` = {"obj", "faces": {"near": centre}} semantic refs, re-resolved on replay, so
    fillet / push_pull / boolean / split take them like any native ref. Re-import on replay re-reads the file;
    info.sha256 lets you detect that the file changed."""
    p = os.path.abspath(path)
    if not os.path.exists(p):
        raise ToolError(f"no such file {p}")
    k = _UNIT_SCALE.get(units)
    if k is None:
        raise ToolError(f"bad units '{units}'", "|".join(_UNIT_SCALE))
    shp = _read(p)
    if k != 1.0:
        shp = shp.scale(k)
    sols = list(shp.solids())
    labels = []
    try:
        labels = [c.label for c in shp.children] if getattr(shp, "children", None) else []
    except Exception:
        labels = []
    out = []
    for i, s in enumerate(sols):
        nm = name if len(sols) == 1 else f"{name}_{i + 1}"
        meta = {"source": p, "units": units}
        if i < len(labels) and labels[i]:
            meta["label"] = str(labels[i])
        m.put(nm, "solid", s, **meta)
        m.tags[nm] = {"obj": nm}
        if tag_faces:
            for j, f in enumerate(s.faces()[:max_face_tags]):
                c = f.center()
                m.tags[f"{nm}/f{j}"] = {"obj": nm, "faces": {"near": [round(c.X, 9), round(c.Y, 9), round(c.Z, 9)]}}
        out.append(nm)
    if not sols:
        for i, f in enumerate(shp.faces()):
            m.put(f"{name}_sheet_{i + 1}", "sheet", f, source=p)
            out.append(f"{name}_sheet_{i + 1}")
    if not out:
        raise ToolError("file contains no solids or faces", "check the export settings (solids/surfaces)")
    sha = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    return {"name": out[0], "objects": out, "solids": len(sols), "sha256": sha,
            "faces": sum(len(m.get(o).shape.faces()) for o in out)}


@op("export_step", "exchange: write objects to STEP (AP214, mm or m)", out=False)
def export_step_op(m, path, objects=None, units="mm"):
    """Write objects (default: all solids) to STEP. units mm (default; session metres x1000) | m."""
    from build123d import export_step, Unit
    names = objects or [k for k, o in m.objects.items() if o.kind in ("solid", "sheet")]
    kids = []
    for n in names:
        s = m.get(n).shape
        s = s.scale(1000.0) if units == "mm" else s
        s.label = n
        kids.append(s)
    p = os.path.abspath(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    export_step(Compound(children=kids), p, unit=Unit.MM if units == "mm" else Unit.M)
    return {"path": p, "objects": names}


@op("deviation_to_ref", "query: model vs imported reference body - Hausdorff, mean, per-face table + heatmap png",
    out=False)
def deviation_to_ref(m, model, ref, samples=20000, per_face=True, heatmap=None, tol=None):
    """Surface deviation of `model` (object/ref) vs `ref` (object/ref, e.g. an import_step body). Returns
    hausdorff, a->b max/mean/rms/p95, per-face {tag, mean, max} sorted worst first (top 20), and if heatmap=path a
    PNG (3 views, faces coloured by mean deviation, red = far). tol: faces with max > tol listed in over_tol."""
    from .query import _exact_dist, _shape, _tess, deviation
    res = deviation(m, model, ref, samples=samples)
    if not per_face and not heatmap:
        return res
    a = _shape(m, model)
    mb = _tess(_shape(m, ref))
    rows, tri_pts, tri_val = [], [], []
    import trimesh
    for j, f in enumerate(a.faces()):
        try:
            mf = _tess(f)
        except Exception:
            continue
        if len(mf.faces) == 0:
            continue
        n = max(50, int(samples * f.area / max(a.area, 1e-18)))
        pts, _ = trimesh.sample.sample_surface(mf, min(n, 4000), seed=j)
        d = _exact_dist(np.vstack([pts, mf.vertices]), mb, max(4000, len(mb.faces) * 2))
        rows.append({"face": j, "tag": f"{model}/f{j}" if isinstance(model, str) else j,
                     "mean": round(float(d.mean()), 7), "max": round(float(d.max()), 7),
                     "centre": [round(v, 5) for v in tuple(f.center())]})
        tri_pts.append(mf.triangles)
        tri_val.append(np.full(len(mf.faces), d.mean()))
    rows.sort(key=lambda r: -r["max"])
    res["per_face"] = rows[:20]
    if tol is not None:
        res["over_tol"] = [r["face"] for r in rows if r["max"] > tol]
    if heatmap and tri_pts:
        res["heatmap"] = _heatmap(np.vstack(tri_pts), np.concatenate(tri_val), heatmap)
    return res


def _heatmap(tris, vals, path, size=420):
    """3 orthographic views (iso, top, front), painter-sorted flat triangles, turbo-ish ramp (PIL only)."""
    from PIL import Image, ImageDraw
    vmax = max(float(vals.max()), 1e-12)

    def ramp(x):  # blue -> cyan -> green -> yellow -> red
        stops = [(0, (40, 60, 200)), (.25, (40, 200, 230)), (.5, (60, 200, 80)), (.75, (240, 220, 40)), (1, (220, 40, 30))]
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if x <= b:
                t = (x - a) / (b - a)
                return tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))
        return stops[-1][1]
    c = np.cos
    views = {"iso": np.array([[c(0.8), -np.sin(0.8), 0], [-0.35, -0.35, 0.87], [0.6, 0.6, 0.5]]),
             "top": np.eye(3), "front": np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])}
    img = Image.new("RGB", (size * 3, size + 40), (250, 250, 250))
    dr = ImageDraw.Draw(img)
    for vi, (nm, R) in enumerate(views.items()):
        P = tris.reshape(-1, 3) @ R.T
        lo, hi = P.min(0), P.max(0)
        sc = 0.9 * size / max(hi[0] - lo[0], hi[1] - lo[1], 1e-12)
        P2 = P.reshape(-1, 3, 3)
        for ti in np.argsort(P2[:, :, 2].mean(1)):
            q = P2[ti]
            pts = [(vi * size + size / 2 + (x - (lo[0] + hi[0]) / 2) * sc, size / 2 - (y - (lo[1] + hi[1]) / 2) * sc)
                   for x, y, _ in q]
            dr.polygon(pts, fill=ramp(float(vals[ti]) / vmax))
        dr.text((vi * size + 8, 8), nm, fill=(0, 0, 0))
    for i in range(size * 3 - 40):
        dr.line([(20 + i, size + 12), (20 + i, size + 30)], fill=ramp(i / (size * 3 - 40)))
    dr.text((20, size + 14), "0", fill=(0, 0, 0))
    dr.text((size * 3 - 120, size + 14), f"{vmax:.3g} (mean dev/face)", fill=(0, 0, 0))
    p = os.path.abspath(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)
    return p
