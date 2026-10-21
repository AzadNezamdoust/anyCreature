"""Robust op wrappers: fillet/chamfer with retry + max-feasible radius, booleans with fuzzy tol + Manifold fallback.

Every call appends a record to LOG (the worker dumps it into state.json -> "ops").
"""
from __future__ import annotations

import math

from build123d import Shape, Solid, Compound, Part, fillet as _fillet, chamfer as _chamfer

LOG: list[dict] = []


class CadOpError(RuntimeError):
    """Raised with an LLM-actionable hint in the message."""


def _edges_desc(edges, n=4):
    out = []
    for e in list(edges)[:n]:
        c = e.center()
        out.append(f"({c.X:.4g},{c.Y:.4g},{c.Z:.4g}) len={e.length:.4g}")
    more = "" if len(list(edges)) <= n else f" +{len(list(edges)) - n} more"
    return "; ".join(out) + more


def _ok(shape) -> bool:
    try:
        return shape is not None and shape.is_valid and shape.volume > 1e-12
    except Exception:
        return False


def _round(kind, part, edges, radius, min_frac=0.15, label=""):
    fn = _fillet if kind == "fillet" else _chamfer
    edges = list(edges)
    rec = {"op": kind, "label": label, "radius": radius, "edges": len(edges), "retries": 0,
           "status": "ok", "applied": radius}
    if not edges:
        rec.update(status="skipped", note="no edges selected")
        LOG.append(rec)
        return part

    def run(r):
        try:
            res = _apply(fn, part, edges, r)
            return res if _ok(res) else None
        except Exception:
            return None

    res = run(radius)
    if res is not None:
        LOG.append(rec)
        return res
    # bisection for max feasible radius
    lo, hi, best = 0.0, radius, None
    for _ in range(7):
        mid = (lo + hi) / 2
        rec["retries"] += 1
        r2 = run(mid)
        if r2 is not None:
            lo, best = mid, r2
        else:
            hi = mid
    if best is not None and lo >= radius * min_frac:
        rec.update(status="reduced", applied=round(lo, 6),
                   note=f"{kind} r={radius:g} infeasible; applied max feasible ~{lo:.4g}")
        LOG.append(rec)
        return best
    # per-edge diagnosis: which edges fail at the requested radius
    bad = []
    for e in edges:
        try:
            if not _ok(_apply(fn, part, [e], radius)):
                bad.append(e)
        except Exception:
            bad.append(e)
    rec.update(status="failed", applied=0, max_feasible=round(lo, 6), bad_edges=len(bad))
    LOG.append(rec)
    raise CadOpError(
        f"{kind} '{label}' r={radius:g} failed on {len(edges)} edges; max feasible radius ~{lo:.4g}"
        f" (bisection). {len(bad)} edge(s) fail alone at r={radius:g}: {_edges_desc(bad)}. "
        f"Try: r<={lo * 0.9:.4g}, drop/split those edges into a separate smaller {kind}, "
        f"or {kind} before the boolean that created short edges.")


def _apply(fn, part, edges, r):
    # build123d's fillet()/chamfer() act on the edges' topo_parent (edges taken from `part`)
    return fn(edges, r)


def safe_fillet(part, edges, radius, min_frac=0.15, label=""):
    """Fillet `edges` (of `part`). On failure bisect to the max feasible radius; apply it if >= min_frac*radius,
    else raise CadOpError naming the bad edges and the max feasible radius."""
    return _round("fillet", part, edges, radius, min_frac, label)


def safe_chamfer(part, edges, length, min_frac=0.15, label=""):
    return _round("chamfer", part, edges, length, min_frac, label)


# ---------------------------------------------------------------- booleans
def _occ_bool(kind, a, b, fuzzy=0.0):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
    from OCP.TopTools import TopTools_ListOfShape
    op = {"cut": BRepAlgoAPI_Cut, "fuse": BRepAlgoAPI_Fuse, "common": BRepAlgoAPI_Common}[kind]()
    la, lb = TopTools_ListOfShape(), TopTools_ListOfShape()
    la.Append(a.wrapped)
    for t in (b if isinstance(b, (list, tuple)) else [b]):
        lb.Append(t.wrapped)
    op.SetArguments(la)
    op.SetTools(lb)
    if fuzzy > 0:
        op.SetFuzzyValue(fuzzy)
    op.SetRunParallel(True)
    op.Build()
    if not op.IsDone():
        return None
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    u = ShapeUpgrade_UnifySameDomain(op.Shape(), True, True, True)
    u.Build()
    res = Shape.cast(u.Shape())
    res = Part(res) if not isinstance(res, Part) else res
    return res


def _to_mesh(shape, tol=1e-3):
    import numpy as np
    verts, tris = shape.tessellate(tol, 0.3)
    return np.array([(v.X, v.Y, v.Z) for v in verts], dtype="float64"), np.array(tris, dtype="uint32")


def _manifold_bool(kind, a, b):
    import manifold3d as m3
    import numpy as np

    def man(s):
        v, f = _to_mesh(s)
        return m3.Manifold(m3.Mesh(vert_properties=v.astype("float32"), tri_verts=f))
    ma = man(a)
    for t in (b if isinstance(b, (list, tuple)) else [b]):
        mb = man(t)
        ma = {"cut": ma - mb, "fuse": ma + mb, "common": ma ^ mb}[kind]
    mesh = ma.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return _sew(v, f)


def _sew(v, f):
    """Mesh -> B-rep solid (planar triangle faces, sewn). Coarse but valid; good enough to keep going."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, \
        BRepBuilderAPI_MakeSolid
    from OCP.gp import gp_Pnt
    from OCP.TopoDS import TopoDS
    sew = BRepBuilderAPI_Sewing(1e-6)
    for t in f:
        p = BRepBuilderAPI_MakePolygon()
        for i in t:
            p.Add(gp_Pnt(*map(float, v[i])))
        p.Close()
        fc = BRepBuilderAPI_MakeFace(p.Wire(), True)
        if fc.IsDone():
            sew.Add(fc.Face())
    sew.Perform()
    sh = sew.SewedShape()
    try:
        solid = BRepBuilderAPI_MakeSolid(TopoDS.Shell_s(sh)).Solid()
        return Part(Solid(solid))
    except Exception:
        return Part(Shape.cast(sh))


def safe_boolean(kind, a, b, label="", fuzzy_steps=(1e-6, 1e-5, 1e-4), allow_mesh=True):
    """kind in cut|fuse|common. Plain OCCT -> fuzzy OCCT (growing tol) -> Manifold mesh boolean (sewn back)."""
    rec = {"op": "boolean", "kind": kind, "label": label, "status": "ok", "retries": 0}
    if isinstance(b, (list, tuple)):
        b = Compound(list(b))  # list tools -> one compound (pilot bug: lists always failed)
    try:
        res = {"cut": lambda: a - b, "fuse": lambda: a + b, "common": lambda: a & b}[kind]()
    except Exception:
        res = None
    if not _ok(res):
        res = None
        diag = max((a.bounding_box().diagonal), 1e-9)
        for fz in fuzzy_steps:
            rec["retries"] += 1
            try:
                r = _occ_bool(kind, a, b, fuzzy=fz * diag)
            except Exception:
                r = None
            if _ok(r):
                res = r
                rec.update(status="fuzzy", fuzzy=fz * diag)
                break
    if res is None and allow_mesh:
        rec["retries"] += 1
        try:
            r = _manifold_bool(kind, a, b)
            if r is not None and r.volume > 1e-12:
                res = r
                rec.update(status="manifold", note="mesh fallback: later fillets on this body will fail")
        except Exception as e:  # noqa
            rec["manifold_error"] = str(e)[:200]
    if res is None:
        rec["status"] = "failed"
        LOG.append(rec)
        raise CadOpError(f"boolean {kind} '{label}' failed (plain, fuzzy {fuzzy_steps}, manifold). Try: move the "
                         f"tool off coplanar/tangent faces by ~1e-4, simplify the tool, or fillet after the boolean.")
    LOG.append(rec)
    return res


def cut(a, b, label=""):
    return safe_boolean("cut", a, b, label)


def fuse(a, b, label=""):
    return safe_boolean("fuse", a, b, label)


def common(a, b, label=""):
    return safe_boolean("common", a, b, label)
