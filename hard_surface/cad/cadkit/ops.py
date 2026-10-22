"""Robust op wrappers: fillet/chamfer with retry + max-feasible radius, booleans with fuzzy tol + Manifold fallback.

Every call appends a record to LOG (the worker dumps it into state.json -> "ops").
"""
from __future__ import annotations

import math
import os
import time

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

    def run_edges(es, r):
        try:
            x = _apply(fn, part, es, r)
            return x if _ok(x) else None
        except Exception:
            return None

    def run_set(es):
        return run_edges(es, radius) is not None

    def remap(newpart, olds):
        out_ = []
        ne = newpart.edges()
        for e in olds:
            c, ln = e.center(), e.length
            best_ = min(ne, key=lambda x: (x.center() - c).length + 0.2 * abs(x.length - ln), default=None)
            if best_ is not None and (best_.center() - c).length < 1e-6 + 0.02 * ln:
                out_.append(best_)
        return out_

    # loft/sweep end caps: OCCT fillet fails or SEGFAULTS on the closed rim of a planar cap (ladder L2/L3) ->
    # never hand those to OCCT; round them with surf.cap_round (trim + quarter-round loft), then do the rest.
    if kind == "fillet":
        from .surf import is_loft_cap_edge, cap_round
        caps = [(e, is_loft_cap_edge(part, e)) for e in edges]
        caps = [(e, f) for e, f in caps if f is not None]
        if caps:
            rest = [e for e in edges if not any(e.is_same(c) for c, _ in caps)]
            cur = part
            for e, f in caps:
                rr = radius
                for k in (1.0, 0.75, 0.5, 0.35, 0.25):  # staged: largest radius the cap can take
                    try:
                        cur2 = remap_face(cur, f)
                        cur = cap_round(cur, cur2, radius * k, label=f"{label}/cap")
                        rr = None
                        break
                    except Exception:
                        continue
                if rr is not None:
                    LOG.append({"op": kind, "label": f"{label}/cap", "status": "cap_failed", "radius": radius})
            rec.update(status="cap_round", caps=len(caps))
            LOG.append(rec)
            if not rest:
                return cur
            return _round(kind, cur, remap(cur, rest), radius, min_frac, label + "/rest")
    res = run(radius)
    if res is not None:
        LOG.append(rec)
        return res
    # split: one bad edge used to drag the whole set's bisection down (L1 ladder: 44 edges -> 0.25 mm).
    # Fillet the edges that work alone at full radius, then retry the rest (remapped by centre) smaller.
    if len(edges) > 1:
        good, bad = [], []
        for e in edges:
            rec["retries"] += 1
            (good if run_set([e]) else bad).append(e)
        if good and bad:
            r1 = run_edges(good, radius)
            if r1 is None:  # good edges fail together (they interact): apply them one by one instead
                r1, n_ok = part, 0
                for e in good:
                    hit = remap(r1, [e])
                    x = _apply_on(fn, r1, hit, radius) if hit else None
                    if x is not None:
                        r1, n_ok = x, n_ok + 1
                    else:
                        bad.append(e)
                rec["sequential"] = n_ok
                if n_ok == 0:
                    r1 = None
            if r1 is not None:
                rec.update(status="split", split_bad=len(bad))
                LOG.append(rec)
                # staged: each remaining edge alone on the evolving body at the largest radius from a ladder
                # that works; one bad edge never shrinks the whole set (L3 foot blend, L5 flare blend)
                staged, skipped = 0, 0
                for e in bad:
                    hit = remap(r1, [e])
                    done = False
                    for k in (1.0, 0.75, 0.5, 0.35, 0.25, 0.15):
                        if k < min_frac or not hit:
                            break
                        x = _apply_on(fn, r1, hit, radius * k)
                        if x is not None:
                            r1, done = x, True
                            staged += 1
                            break
                    skipped += not done
                rec.update(staged=staged, rest_skipped=skipped)
                if skipped:
                    rec["status"] = "split_partial"
                return r1
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


def remap_face(part, f):
    """Same planar face in a newer revision (by centre + normal)."""
    c, n = f.center(), f.normal_at(f.center())
    best = min(part.faces(), key=lambda g: (g.center() - c).length)
    return best


def _apply_on(fn, part, edges, r):
    try:
        x = _apply(fn, part, edges, r)
        return x if _ok(x) else None
    except Exception:
        return None


_DEADLINE = [None]
_ISO_EVENTS: list = []


def _apply(fn, part, edges, r):
    # build123d's fillet()/chamfer() act on the edges' topo_parent (edges taken from `part`).
    # Free-form bodies: the attempt runs in the isolation child (crash/hang kills only that child; cadkit.isolate).
    from . import isolate
    if _DEADLINE[0] is not None and time.time() > _DEADLINE[0]:
        raise CadOpError("op time budget exceeded (CADKIT_OP_BUDGET)")
    if fn in (_fillet, _chamfer) and isolate.needs_isolation(part):
        left = isolate.timeout_s()
        if _DEADLINE[0] is not None:
            left = max(1.0, min(left, _DEADLINE[0] - time.time()))
        try:
            res = isolate.worker().run("fillet" if fn is _fillet else "chamfer", part, list(edges), r, left)
        except isolate.IsolationFailure as e:
            _ISO_EVENTS.append(str(e))
            return None
        if res is None:
            return None
        sols = res.solids()
        return sols[0] if len(sols) == 1 else res
    return fn(edges, r)


def edge_curvature_limit(edges, n=400):
    """Smallest radius of curvature over the edges (sampled). A rolling-ball fillet larger than the wall's radius of
    curvature has no solution; on free-form edges OCCT then crashes/hangs instead of failing (L3 root cause:
    r=14 asked on a periodic-spline rim whose tightest corner is r=6.4)."""
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.BRepLProp import BRepLProp_CLProps
    from OCP.GeomAbs import GeomAbs_Line
    kmax = 0.0
    for e in edges:
        c = BRepAdaptor_Curve(e.wrapped)
        if c.GetType() == GeomAbs_Line:
            continue
        u0, u1 = c.FirstParameter(), c.LastParameter()
        for i in range(n + 1):
            try:
                pr = BRepLProp_CLProps(c, u0 + (u1 - u0) * i / n, 2, 1e-7)
                kmax = max(kmax, pr.Curvature())
            except Exception:
                pass
    return 1.0 / kmax if kmax > 1e-12 else math.inf


def _guarded(kind, part, edges, radius, min_frac, label):
    """Free-form bodies: (1) clamp the radius below the edge curvature limit, (2) whole set isolated first,
    (3) heal (ShapeFix tolerances + split C0 faces) and retry, (4) the retry ladder (_round) with every OCCT
    attempt isolated and a time budget for the whole call."""
    from . import isolate
    edges = list(edges)
    if not edges or not isolate.needs_isolation(part):
        return _round(kind, part, edges, radius, min_frac, label)
    fn = _fillet if kind == "fillet" else _chamfer
    outer = _DEADLINE[0] is None
    if outer:
        _DEADLINE[0] = time.time() + isolate.budget_s()
    n_ev = len(_ISO_EVENTS)
    try:
        r = radius
        if kind == "fillet":
            # only edges bounding a planar face: there the edge curvature IS the wall section curvature
            pl = [e for e in edges if any(f.geom_type.name == "PLANE" for f in part.faces()
                                          if any(x.is_same(e) for x in f.edges()))]
            lim = edge_curvature_limit(pl) if pl else math.inf
            if r > 0.9 * lim:
                # no silent shrink: report as failure with the geometric reason + the feasible ceiling
                LOG.append({"op": kind, "label": label, "status": "failed", "reason": "curvature_limit",
                            "radius": radius, "applied": 0, "max_feasible": round(0.9 * lim, 6)})
                raise CadOpError(f"{kind} '{label}' r={radius:g} impossible: the rim's tightest radius of curvature "
                                 f"is {lim:.4g} (a larger rolling ball has no solution; OCCT used to crash/hang "
                                 f"here). max feasible ~{0.9 * lim:.4g}: lower r, or soften that profile corner.")
        from .surf import is_loft_cap_edge
        if kind == "fillet" and any(is_loft_cap_edge(part, e) is not None for e in edges):
            return _strict(_round(kind, part, edges, r, min_frac, label), label, radius)
        x = _apply_on(fn, part, edges, r)
        if x is not None:
            LOG.append({"op": kind, "label": label, "radius": radius, "edges": len(edges), "retries": 0,
                        "status": "ok" if r == radius else "reduced", "applied": r, "isolated": True})
            return x
        healed = heal(part)
        if healed is not part:
            hed = _remap_edges(healed, edges)
            if hed:
                x = _apply_on(fn, healed, hed, r)
                if x is not None:
                    LOG.append({"op": kind, "label": label, "radius": radius, "edges": len(edges),
                                "status": "healed", "applied": r, "isolated": True})
                    return x
        return _strict(_round(kind, part, edges, r, min_frac, label), label, radius)
    finally:
        if len(_ISO_EVENTS) > n_ev:
            LOG.append({"op": kind, "label": label, "status": "isolated_events", "events": _ISO_EVENTS[n_ev:][:6]})
        if outer:
            _DEADLINE[0] = None


def _strict(res, label, radius):
    """Free-form path: a reduced / partial result is a FAILURE (caller asked for r), not a quiet shrink."""
    rec = next((o for o in reversed(LOG) if o.get("label", "").startswith(label) and o.get("op") in
                ("fillet", "chamfer") and "status" in o and o["status"] != "isolated_events"), None)
    if rec and rec["status"] in ("reduced", "split_partial", "cap_failed") and os.environ.get(
            "CADKIT_ALLOW_SHRINK") != "1":
        raise CadOpError(f"fillet '{label}' r={radius:g} could only be applied partially/reduced "
                         f"({rec['status']}, applied {rec.get('applied')}); set CADKIT_ALLOW_SHRINK=1 to accept, or "
                         f"lower r / split the edge set.")
    return res


def heal(part):
    """ShapeFix (tolerances, small edges) + split faces at C0 knots (ShapeUpgrade_ShapeDivideContinuity C1).
    Returns `part` itself when nothing changed / healing failed."""
    try:
        from OCP.ShapeFix import ShapeFix_Shape
        from OCP.ShapeUpgrade import ShapeUpgrade_ShapeDivideContinuity
        from OCP.GeomAbs import GeomAbs_C1
        fx = ShapeFix_Shape(part.wrapped)
        fx.SetPrecision(1e-6)
        fx.SetMaxTolerance(1e-3)
        fx.Perform()
        dv = ShapeUpgrade_ShapeDivideContinuity(fx.Shape())
        dv.SetBoundaryCriterion(GeomAbs_C1)
        dv.SetPCurveCriterion(GeomAbs_C1)
        dv.SetSurfaceCriterion(GeomAbs_C1)
        dv.Perform()
        sols = Shape.cast(dv.Result()).solids()
        if len(sols) != 1 or not sols[0].is_valid:
            return part
        res = sols[0]
        if len(res.faces()) == len(part.faces()) and len(res.edges()) == len(part.edges()):
            return part
        return res
    except Exception:
        return part


def _remap_edges(newpart, olds):
    """Edges of newpart lying on any of the old edges (healing may split an edge into pieces)."""
    out = []
    for ne in newpart.edges():
        pm = ne.position_at(0.5)
        for e in olds:
            try:
                if e.distance_to(pm) < 1e-4:
                    out.append(ne)
                    break
            except Exception:
                pass
    return out


def safe_fillet(part, edges, radius, min_frac=0.15, label=""):
    """Fillet `edges` (of `part`). On failure bisect to the max feasible radius; apply it if >= min_frac*radius,
    else raise CadOpError naming the bad edges and the max feasible radius. Free-form bodies: curvature clamp, heal,
    crash/hang-isolated attempts + time budget (cadkit.isolate)."""
    return _guarded("fillet", part, edges, radius, min_frac, label)


def safe_chamfer(part, edges, length, min_frac=0.15, label=""):
    return _guarded("chamfer", part, edges, length, min_frac, label)


# ---------------------------------------------------------------- booleans
def _occ_bool(kind, a, b, fuzzy=0.0):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
    try:  # OCP 8.x moved NCollection list bindings to OCP.collections (fuzzy retry always ImportError'd before)
        from OCP.collections import List_TopoDS_Shape as TopTools_ListOfShape
    except ImportError:
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
        # weld: OCCT tessellation duplicates verts along B-rep face seams -> Manifold saw an open mesh and returned
        # empty (L4: 'Null TopoDS_Shape' on every fallback). Quantise + unique to make it watertight.
        q = np.round(v / 1e-6).astype(np.int64)
        _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
        v, f = v[first], inv.reshape(-1)[f]
        f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
        mm = m3.Manifold(m3.Mesh(vert_properties=v.astype("float32"), tri_verts=f.astype("uint32")))
        if mm.is_empty():
            raise RuntimeError(f"manifold input not watertight: {mm.status()}")
        return mm
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
    from build123d.topology.shape_core import downcast  # OCP 8.x: TopoDS.Shell_s is gone (fallback always died)
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.ShapeFix import ShapeFix_Solid
    shells = []
    ex = TopExp_Explorer(sh, TopAbs_SHELL)
    while ex.More():  # hollow results (skins, shells) sew into >1 shell -> compound (L5: MakeSolid TypeError)
        shells.append(downcast(ex.Current()))
        ex.Next()
    mk = BRepBuilderAPI_MakeSolid()
    for shl in shells:
        mk.Add(shl)
    fx = ShapeFix_Solid(mk.Solid())  # orients the inner shell(s) as voids
    fx.Perform()
    return Solid(downcast(fx.Solid()))


def _overlap_estimate(a, b, n=6):
    """Monte-Carlo-on-a-grid volume of a & b inside the bbox intersection (n^3 probes, point classification)."""
    try:
        from OCP.BRepClass3d import BRepClass3d_SolidClassifier
        from OCP.TopAbs import TopAbs_IN
        from OCP.gp import gp_Pnt
        A, B = a.bounding_box(), b.bounding_box()
        lo = [max(x, y) for x, y in zip(tuple(A.min), tuple(B.min))]
        hi = [min(x, y) for x, y in zip(tuple(A.max), tuple(B.max))]
        if any(h <= l for l, h in zip(lo, hi)):
            return 0.0
        ca, cb = BRepClass3d_SolidClassifier(a.wrapped), BRepClass3d_SolidClassifier(b.wrapped)
        hit = 0
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    p = gp_Pnt(*[l + (h - l) * (q + 0.5) / n for l, h, q in zip(lo, hi, (i, j, k))])
                    ca.Perform(p, 1e-7)
                    if ca.State() != TopAbs_IN:
                        continue
                    cb.Perform(p, 1e-7)
                    hit += cb.State() == TopAbs_IN
        vol = (hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2])
        return vol * hit / n ** 3
    except Exception:
        return None


def safe_boolean(kind, a, b, label="", fuzzy_steps=(1e-6, 1e-5, 1e-4), allow_mesh=True):
    """kind in cut|fuse|common. Plain OCCT -> fuzzy OCCT (growing tol) -> Manifold mesh boolean (sewn back)."""
    rec = {"op": "boolean", "kind": kind, "label": label, "status": "ok", "retries": 0}
    if isinstance(b, (list, tuple)):
        b = Compound(list(b))  # list tools -> one compound (pilot bug: lists always failed)
    va = a.volume
    vb = sum(t.volume for t in b.solids()) if hasattr(b, "solids") else b.volume

    def sane(r):  # volume sanity: OCCT sometimes returns a VALID but wrong (inverted/partial) solid (L5 r6)
        if not _ok(r):
            return False
        v, tol = r.volume, 1e-3 * max(va, vb) + 1e-9
        if kind == "cut":
            if not (v <= va + tol and v >= va - vb - tol):
                return False
            # silent no-op guard (L4 underside skin: cut of a near-coincident shifted copy came back VALID with
            # the full volume): if the tool clearly overlaps `a`, the cut must remove a matching share of it
            est = _overlap_estimate(a, b)
            if est is not None and est > 0.02 * va and (va - v) < 0.4 * est:
                rec["noop_rejected"] = round(est / va, 4)
                return False
            return True
        if kind == "fuse":
            return v >= max(va, vb) - tol and v <= va + vb + tol
        return v <= min(va, vb) + tol

    try:
        res = {"cut": lambda: a - b, "fuse": lambda: a + b, "common": lambda: a & b}[kind]()
    except Exception:
        res = None
    if res is not None and _ok(res) and not sane(res):
        rec["insane_plain"] = round(res.volume / max(va, 1e-12), 4)
    if not sane(res):
        res = None
        diag = max((a.bounding_box().diagonal), 1e-9)
        for fz in fuzzy_steps:
            rec["retries"] += 1
            try:
                r = _occ_bool(kind, a, b, fuzzy=fz * diag)
            except Exception:
                r = None
            if sane(r):
                res = r
                rec.update(status="fuzzy", fuzzy=fz * diag)
                break
    if res is None and allow_mesh:
        rec["retries"] += 1
        try:
            r = _manifold_bool(kind, a, b)
            if r is not None and sane(r):
                res = r
                rec.update(status="manifold", note="mesh fallback: later fillets on this body will fail")
        except Exception as e:  # noqa
            rec["manifold_error"] = str(e)[:200]
    if res is None:
        rec["status"] = "failed"
        LOG.append(rec)
        raise CadOpError(f"boolean {kind} '{label}' failed (plain, fuzzy {fuzzy_steps}, manifold). Try: move the "
                         f"tool off coplanar/tangent faces by ~1e-4, simplify the tool, or fillet after the boolean.")
    rec["vol"] = round(res.volume, 6)
    LOG.append(rec)
    return res


def cut(a, b, label=""):
    return safe_boolean("cut", a, b, label)


def fuse(a, b, label=""):
    return safe_boolean("fuse", a, b, label)


def common(a, b, label=""):
    return safe_boolean("common", a, b, label)


def variable_fillet(part, edges, r_start, r_end, label=""):
    """Linear-varying radius fillet per edge (OCCT BRepFilletAPI_MakeFillet.Add(r1, r2, edge)); build123d has no
    variable fillet. On failure scales both radii down (x0.75 up to 6x) and logs; raises CadOpError if none work."""
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
    edges = list(edges)
    rec = {"op": "fillet", "label": label or "variable", "radius": [r_start, r_end], "edges": len(edges),
           "retries": 0, "status": "ok", "applied": [r_start, r_end], "variable": True}
    k = 1.0
    for i in range(7):
        try:
            mk = BRepFilletAPI_MakeFillet(part.wrapped)
            for e in edges:
                mk.Add(r_start * k, r_end * k, e.wrapped)
            mk.Build()
            if mk.IsDone():
                res = Part(Shape.cast(mk.Shape()))
                if _ok(res):
                    if i:
                        rec.update(status="reduced", applied=[r_start * k, r_end * k])
                    LOG.append(rec)
                    return res
        except Exception:
            pass
        rec["retries"] += 1
        k *= 0.75
    rec.update(status="failed", applied=0)
    LOG.append(rec)
    raise CadOpError(f"variable fillet '{label}' {r_start}->{r_end} failed on {len(edges)} edges even at x{k:.2f}")
