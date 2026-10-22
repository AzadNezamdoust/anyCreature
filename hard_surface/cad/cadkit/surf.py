"""Robust shell/offset, loft end-cap rounding, and surfacing helpers (multi-rail loft, boundary patch, G2 bridge
curve, G2 blend surface, curve trim/join, helix). Plain build123d/OCP; usable from model scripts
(`from cadkit import *`) and wrapped as cadkit.tools ops. Every op validates its result and logs to ops.LOG.
"""
from __future__ import annotations

import math

import numpy as np
from build123d import (Edge, Face, Kind, Plane, Shape, Solid, Vector, Wire, extrude, loft as _loft, offset as _offset,
                       split as _split, Keep)

from .ops import LOG, CadOpError, _ok, safe_boolean


def _rec(**kw):
    LOG.append(kw)
    return kw


def _cast(occ):
    s = Shape.cast(occ)
    sols = s.solids()
    return sols[0] if len(sols) == 1 else s


# ====================================================================== shell / offset
def _thick_solid(s, t, faces, join_arc, tol):
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid
    from OCP.BRepOffset import BRepOffset_Skin
    from OCP.GeomAbs import GeomAbs_Arc, GeomAbs_Intersection
    try:
        from OCP.collections import List_TopoDS_Shape as L
    except ImportError:
        from OCP.TopTools import TopTools_ListOfShape as L
    lst = L()
    for f in faces:
        lst.Append(f.wrapped)
    mk = BRepOffsetAPI_MakeThickSolid()
    mk.MakeThickSolidByJoin(s.wrapped, lst, t, tol, BRepOffset_Skin, not join_arc, False,
                            GeomAbs_Arc if join_arc else GeomAbs_Intersection, False)
    mk.Build()
    return _cast(mk.Shape()) if mk.IsDone() else None


def _offset_solid(s, d, join_arc=True, tol=1e-6):
    """Closed offset solid (no openings): BRepOffsetAPI_MakeOffsetShape."""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
    from OCP.BRepOffset import BRepOffset_Skin
    from OCP.GeomAbs import GeomAbs_Arc, GeomAbs_Intersection
    mk = BRepOffsetAPI_MakeOffsetShape()
    mk.PerformByJoin(s.wrapped, d, tol, BRepOffset_Skin, False, False,
                     GeomAbs_Arc if join_arc else GeomAbs_Intersection, False)
    if not mk.IsDone():
        return None
    r = Shape.cast(mk.Shape())
    sols = r.solids()
    if sols:
        return sols[0]
    shells = r.shells()
    return solid_from_shell(shells[0]) if shells else None


def solid_from_shell(sh):
    """Closed shell -> oriented solid (None if not closed/valid)."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
    from OCP.ShapeFix import ShapeFix_Solid
    from build123d.topology.shape_core import downcast
    mk = BRepBuilderAPI_MakeSolid(sh.wrapped)
    fx = ShapeFix_Solid(mk.Solid())
    fx.Perform()
    s = Solid(downcast(fx.Solid()))
    return s if s.is_valid and s.volume > 0 else None


def _open_cutters(faces, inner, t):
    """Tools that punch each opening through the wall: the INNER solid's matching face (same normal, nearest)
    pushed out through the opening by 3t (planar: extrude; curved: thicken)."""
    out = []
    for f in faces:
        c, n = f.center(), f.normal_at(f.center())
        cands = []
        for g in inner.faces():
            try:
                if g.normal_at(g.center()).dot(n) > 0.95:
                    cands.append(g)
            except Exception:
                pass
        if not cands:
            continue
        g = min(cands, key=lambda g: (g.center() - c).length)
        try:
            if g.geom_type.name == "PLANE":
                out.append(extrude(g, amount=3 * t, dir=n))
            else:
                from build123d import thicken
                out.append(thicken(g, 3 * t))
        except Exception:
            pass
    return out


def _manifold_erode(s, t):
    """Last resort: inner (eroded) solid by mesh erosion (Manifold minkowski difference with a sphere), sewn."""
    import manifold3d as m3
    from .ops import _to_mesh, _sew
    v, f = _to_mesh(s, tol=max(t * 0.25, 1e-6))
    q = np.round(v / 1e-6).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    v, f = v[first], inv.reshape(-1)[f]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    mm = m3.Manifold(m3.Mesh(vert_properties=v.astype("float32"), tri_verts=f.astype("uint32")))
    inner = mm.minkowski_difference(m3.Manifold.sphere(t, 16))
    mi = inner.to_mesh()
    return _sew(np.asarray(mi.vert_properties)[:, :3], np.asarray(mi.tri_verts))


def shell_check(s, r, t, outward, openings):
    """Result validation: valid solid, volume moves the right way, wall volume ~ area * t."""
    if not _ok(r):
        return False
    v0, v = s.volume, r.volume
    area = s.area - sum(f.area for f in openings)
    return 0.2 * area * t <= v <= 3.0 * area * t and (outward or v <= v0 * 1.0001)


SHELL_STRATEGIES = ("arc", "intersection", "thick_arc", "thick_intersection", "thick_tol", "offset_cut",
                    "sections", "manifold")


def robust_shell(s, thickness, openings=(), outward=False, sections=None, strategy=None, label="shell"):
    """Hollow `s` to wall `thickness`. Tries (in order, or only `strategy`): build123d offset ARC / INTERSECTION,
    BRepOffsetAPI_MakeThickSolid (arc / intersection join, looser tol), closed offset solid + boolean cut + punched
    openings, re-loft of shrunk `sections` (list of planar section faces of a loft; 2D-offset each and loft) + cut,
    Manifold mesh erosion (minkowski) as the last resort. Each candidate is validated (shell_check).
    Returns the shell; ops.LOG gets {op: shell, method, tried}."""
    openings = list(openings or [])
    t = abs(thickness)
    sgn = 1 if outward else -1
    diag = s.bounding_box().diagonal
    tried = []

    def hollow(inner, tag):
        r = safe_boolean("cut", s, inner, f"{label}:{tag}", allow_mesh=(tag == "erode"))
        for c in _open_cutters(openings, inner, t):
            r = safe_boolean("cut", r, c, f"{label}:opening", allow_mesh=(tag == "erode"))
        return r

    def cand(name):
        if name == "arc":
            return _offset(s, amount=sgn * t, openings=openings or None, kind=Kind.ARC)
        if name == "intersection":
            return _offset(s, amount=sgn * t, openings=openings or None, kind=Kind.INTERSECTION)
        if name == "thick_arc":
            return _thick_solid(s, sgn * t, openings, True, 1e-6)
        if name == "thick_intersection":
            return _thick_solid(s, sgn * t, openings, False, 1e-6)
        if name == "thick_tol":
            return _thick_solid(s, sgn * t, openings, True, max(1e-4 * diag, 1e-6))
        if outward:
            return None  # the remaining strategies build an INNER solid
        if name == "offset_cut":
            o = _offset_solid(s, -t) or _offset_solid(s, -t, join_arc=False)
            return hollow(o, "offset_cut") if o is not None and _ok(o) else None
        if name == "sections":
            return hollow(_loft([inset_face(f, t) for f in sections]), "reloft") if sections else None
        if name == "manifold":
            return hollow(_manifold_erode(s, t), "erode")
        raise CadOpError(f"unknown shell strategy {name}; use one of {SHELL_STRATEGIES}")

    for name in ([strategy] if strategy else SHELL_STRATEGIES):
        try:
            r = cand(name)
        except CadOpError:
            if strategy:
                raise
            r = None
        except Exception:
            r = None
        ok = r is not None and shell_check(s, r, t, outward, openings)
        tried.append(name if ok else name + ":bad")
        if ok:
            _rec(op="shell", label=label, status="ok" if name == "arc" else "fallback", method=name, tried=tried)
            return r
    _rec(op="shell", label=label, status="failed", tried=tried)
    raise CadOpError(f"shell '{label}' t={t:g} failed with every strategy {tried}. Try: thinner wall (< smallest "
                     f"fillet / curvature radius), shell BEFORE fillets/features, or pass sections=<loft stations>.")


def inset_face(f, d):
    """Planar face inset by d (2D offset; fallback: per-point offset of a sampled outer wire)."""
    w = f.outer_wire()
    try:
        w2 = w.offset_2d(-d, kind=Kind.ARC)
        f2 = Face(w2)
        if f2.area < f.area:
            return f2
    except Exception:
        pass
    return Face(inset_wire(w, d, f.normal_at(f.center())))


def inset_wire(w, d, n, k=64):
    """Closed planar wire moved inward by d point-wise (sampled, re-splined periodic). Works for convex-ish loops."""
    n = Vector(n).normalized()
    pts = [w.position_at(i / k) for i in range(k)]
    tg = [w.tangent_at(i / k) for i in range(k)]
    c = sum(pts, Vector()) / k
    out = []
    for p, t in zip(pts, tg):
        m = n.cross(t).normalized()
        if m.dot(c - p) < 0:
            m = -m
        out.append(p + m * d)
    return Wire([Edge.make_spline(out, periodic=True)])


def robust_offset_face(s, faces, d, label="offset_face"):
    """Push/pull faces (planar or curved) with neighbours adapting. Strategies: BRepOffset per-face offset (arc,
    intersection join), then thicken the faces into slabs and union (d>0) / cut (d<0). Validated by volume sign."""
    from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin
    from OCP.GeomAbs import GeomAbs_Arc, GeomAbs_Intersection
    v0 = s.volume
    tried = []

    def good(r):
        return _ok(r) and (r.volume - v0) * d > 0

    for join, jn in ((GeomAbs_Intersection, "brep_intersection"), (GeomAbs_Arc, "brep_arc")):
        try:
            mk = BRepOffset_MakeOffset()
            mk.Initialize(s.wrapped, 0.0, 1e-6, BRepOffset_Skin, True, False, join, False, False)
            for f in faces:
                mk.SetOffsetOnFace(f.wrapped, d)
            mk.MakeOffsetShape()
            r = _cast(mk.Shape()) if mk.IsDone() else None
        except Exception:
            r = None
        tried.append(jn if good(r) else jn + ":bad")
        if good(r):
            _rec(op="offset_face", label=label, status="ok", method=jn)
            return r, jn
    from build123d import thicken
    r = s
    try:
        for f in faces:
            n = f.normal_at(f.center())
            if f.geom_type.name == "PLANE":
                slab = extrude(f, amount=abs(d), dir=n if d > 0 else -n)
            else:
                slab = thicken(f, d)  # thicken along the face normal (+ outward)
                if not _ok(slab):
                    slab = thicken(f, -d)
            r = safe_boolean("fuse" if d > 0 else "cut", r, slab, f"{label}:slab")
    except Exception:
        r = None
    tried.append("slab" if r is not None and good(r) else "slab:bad")
    if r is not None and good(r):
        _rec(op="offset_face", label=label, status="fallback", method="slab", tried=tried)
        return r, "slab"
    _rec(op="offset_face", label=label, status="failed", tried=tried)
    raise CadOpError(f"offset_face '{label}' d={d:g} failed {tried}. Try a smaller distance or offset before fillets.")


# ====================================================================== loft end caps
def is_loft_cap_edge(part, e):
    """Closed edge bounding a planar face whose other neighbour is a free-form (B-spline) face = loft end cap.
    OCCT fillets on these fail or SEGFAULT (ladder L2/L3) -> handled by cap_round instead."""
    if not e.is_closed:
        return None
    adj = [f for f in part.faces() if any(x.is_same(e) for x in f.edges())]
    caps = [f for f in adj if f.geom_type.name == "PLANE"]
    free = [f for f in adj if f.geom_type.name in ("BSPLINE", "BEZIER", "OFFSET", "REVOLUTION", "EXTRUSION")]
    if len(caps) == 1 and free and len(caps[0].edges()) == 1:
        return caps[0]
    return None


def cap_round(part, cap, radius, n=7, label="cap_round"):
    """Round the rim of a planar end cap of a lofted/swept solid by radius r WITHOUT the OCCT fillet: cut the last r
    off, then loft a quarter-round of inset sections (inset r(1-cos a), advance r sin a) onto a cap inset by r.
    G1 at the junction to within the loft fit; smooth zebra. Returns the new solid."""
    n_out = cap.normal_at(cap.center())
    c = cap.center()
    r = radius
    pl = Plane(c - n_out * r, z_dir=-n_out)
    trimmed = _split(part, pl, keep=Keep.TOP)
    trimmed = trimmed.solids()[0] if trimmed.solids() else trimmed
    sec = [f for f in trimmed.faces() if f.geom_type.name == "PLANE" and
           abs((f.center() - pl.origin).dot(n_out)) < 1e-6 * max(1, r) + 1e-9]
    if not sec:
        raise CadOpError(f"{label}: no section face at the trim plane")
    sec = max(sec, key=lambda f: f.area)
    w0 = sec.outer_wire()
    faces = []
    for i in range(n):
        a = (math.pi / 2) * (1 - math.cos(math.pi * i / (2 * (n - 1))))  # cluster near the cap tip
        a = (math.pi / 2) * i / (n - 1) if i in (0, n - 1) else a
        inset, adv = r * (1 - math.cos(a)), r * math.sin(a)
        f = sec if inset < 1e-12 else Face(inset_wire(w0, inset, n_out) if i else w0)
        faces.append(f.moved(_loc(n_out * adv)) if adv else f)
    cap_solid = _loft(faces)
    res = safe_boolean("fuse", trimmed, cap_solid, f"{label}:fuse")
    if not _ok(res):
        raise CadOpError(f"{label}: invalid result")
    _rec(op="fillet", label=label, status="cap_round", radius=r, applied=r, edges=1)
    return res


def _loc(v):
    from build123d import Location
    return Location(v)


# ====================================================================== curves
def bridge_curve(a, b, a_end=1.0, b_end=0.0, continuity="G2", tension=1.0):
    """Blend curve from curve a (at param a_end) to curve b (at b_end), G1 (cubic) or G2 (quintic Bezier with
    end curvature matched: C''(0) = |C'(0)|^2 * kappa_a * N_a). Returns an Edge."""
    pa, pb = a.position_at(a_end), b.position_at(b_end)
    ta = a.tangent_at(a_end) * (1 if a_end > 0.5 else -1)
    tb = b.tangent_at(b_end) * (1 if b_end < 0.5 else -1)   # direction INTO b
    L = (pb - pa).length * tension
    if continuity == "G1":
        d = L / 3
        P = [pa, pa + ta * d, pb - tb * d, pb]
        return Edge.make_bezier(*P)
    nd = 5
    d = L / nd * 1.6
    ka, kb = curvature_vector(a, a_end), curvature_vector(b, b_end)
    p1 = pa + ta * d
    p2 = p1 * 2 - pa + ka * ((nd * d) ** 2 / (nd * (nd - 1)))
    q1 = pb - tb * d
    q2 = q1 * 2 - pb + kb * ((nd * d) ** 2 / (nd * (nd - 1)))
    return Edge.make_bezier(pa, p1, p2, q2, q1, pb)


def curvature_vector(e, u):
    """kappa * N at normalised param u (0 for lines)."""
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.gp import gp_Pnt, gp_Vec
    ad = BRepAdaptor_Curve(e.wrapped)
    t = ad.FirstParameter() + u * (ad.LastParameter() - ad.FirstParameter())
    p, d1, d2 = gp_Pnt(), gp_Vec(), gp_Vec()
    ad.D2(t, p, d1, d2)
    v1, v2 = Vector(d1.X(), d1.Y(), d1.Z()), Vector(d2.X(), d2.Y(), d2.Z())
    s2 = v1.dot(v1)
    if s2 < 1e-30:
        return Vector()
    return (v2 - v1 * (v2.dot(v1) / s2)) / s2


def trim_curve(c, u0=0.0, u1=1.0):
    """Sub-curve between normalised params (Edge or Wire)."""
    e = c if isinstance(c, Edge) else Edge(c.wrapped) if False else None
    if isinstance(c, Wire):
        if len(c.edges()) == 1:
            e = c.edges()[0]
        else:
            return c.trim(u0, u1)
    return e.trim(u0, u1)


def join_curves(curves, tol=1e-6):
    """Edges/wires -> one wire (ordered, gaps <= tol closed by sewing)."""
    edges = [x for c in curves for x in (c.edges() if hasattr(c, "edges") else [c])]
    return Wire.combine(edges, tol=tol)[0]


def helix(pitch, height, radius, center=(0, 0, 0), direction=(0, 0, 1), lefthand=False):
    return Wire([Edge.make_helix(pitch, height, radius, Vector(*center), Vector(*direction), lefthand=lefthand)])


# ====================================================================== multi-rail loft
def _sample_loop(w, k, start):
    """k points around closed wire w, starting at the sample nearest `start`."""
    pts = [w.position_at(i / k) for i in range(k)]
    j = min(range(k), key=lambda i: (pts[i] - start).length)
    return pts[j:] + pts[:j]


def rail_loft(profiles, rails, n=12, k=48, closed=None, ruled=False):
    """Multi-rail (2+ guides) loft. profiles = ordered section wires that touch every rail; rails = guide curves
    running across the profiles. Builds n intermediate sections: blend the neighbouring profiles, then map them
    with a frame fit so their rail-contact points land exactly on the rails (2 rails: similarity; 3+: least-
    squares in-plane affine), then loft through all. Returns Solid (closed profiles) or Shell/Face."""
    profiles = [p if isinstance(p, Wire) else Wire([p]) if isinstance(p, Edge) else p.outer_wire() for p in profiles]
    rails = [r if isinstance(r, Wire) else Wire([r]) for r in rails]
    if len(rails) < 2:
        raise CadOpError("rail_loft needs >= 2 rails (use loft guide= for one)")
    closed = all(p.is_closed for p in profiles) if closed is None else closed
    # rail params at each profile
    U = np.array([[_closest_param(r, p) for r in rails] for p in profiles])  # [profile, rail]
    order = np.argsort(U[:, 0])
    profiles, U = [profiles[i] for i in order], U[order]
    C = [[r.position_at(U[i, j]) for j, r in enumerate(rails)] for i in range(len(profiles))]
    # resample profiles aligned on rail-0 contact
    S = []
    for i, p in enumerate(profiles):
        if closed:
            S.append(_sample_loop(p, k, C[i][0]))
        else:
            a, b = p.position_at(0), p.position_at(1)
            pts = [p.position_at(t / (k - 1)) for t in range(k)]
            S.append(pts if (a - C[i][0]).length <= (b - C[i][0]).length else pts[::-1])
    secs = []
    us = np.linspace(U[0, 0], U[-1, 0], n)
    for u in us:
        i = int(np.clip(np.searchsorted(U[:, 0], u) - 1, 0, len(profiles) - 2))
        w = (u - U[i, 0]) / max(U[i + 1, 0] - U[i, 0], 1e-12)
        pts = [a * (1 - w) + b * w for a, b in zip(S[i], S[i + 1])]
        src = [C[i][j] * (1 - w) + C[i + 1][j] * w for j in range(len(rails))]
        dst = [r.position_at(float(U[i, j] * (1 - w) + U[i + 1, j] * w)) for j, r in enumerate(rails)]
        nrm = _plane_normal(pts)
        tan = rails[0].tangent_at(float(u))
        pts = _frame_map(pts, src, dst, nrm, tan)
        secs.append(Wire([Edge.make_spline(pts, periodic=True)]) if closed else Wire([Edge.make_spline(pts)]))
    if closed:
        return _loft([Face(s) for s in secs], ruled=ruled)
    return _loft(secs, ruled=ruled)


def _closest_param(w, p):
    """Normalised param on wire w nearest to shape p (coarse sample + local refine)."""
    k = 200
    ts = np.linspace(0, 1, k)
    d = [p.distance_to(w.position_at(float(t))) for t in ts]
    i = int(np.argmin(d))
    lo, hi = ts[max(i - 1, 0)], ts[min(i + 1, k - 1)]
    for _ in range(30):
        a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if p.distance_to(w.position_at(float(a))) < p.distance_to(w.position_at(float(b))):
            hi = b
        else:
            lo = a
    return float((lo + hi) / 2)


def _plane_normal(pts):
    P = np.array([tuple(p) for p in pts])
    P = P - P.mean(0)
    n = np.linalg.svd(P)[2][2]
    return Vector(*n)


def _frame_map(pts, src, dst, nrm, tan):
    """Map points so src contacts -> dst. Frame: x = c1-c0, z = section normal; target z follows the rail
    tangent. In-plane scale fitted to all rails (x exact for rails 0/1, y least squares for 3+)."""
    def frame(o, x, z):
        x = x.normalized()
        z = (z - x * z.dot(x)).normalized()
        return o, x, z.cross(x), z
    zs = nrm if nrm.dot(tan) >= 0 else -nrm
    o, x, y, z = frame(src[0], src[1] - src[0], zs)
    O, X, Y, Z = frame(dst[0], dst[1] - dst[0], tan)
    sx = (dst[1] - dst[0]).length / max((src[1] - src[0]).length, 1e-12)
    sy = sx
    if len(src) > 2:
        a = np.array([(s - o).dot(y) for s in src[2:]])
        b = np.array([(d - O).dot(Y) for d in dst[2:]])
        if np.abs(a).max() > 1e-12:
            sy = float(a.dot(b) / a.dot(a))
    out = []
    for p in pts:
        q = p - o
        out.append(O + X * (q.dot(x) * sx) + Y * (q.dot(y) * sy) + Z * (q.dot(z) * sx))
    return out


# ====================================================================== surface patch / blend
def patch(boundary, continuity=None, support_faces=None, points=(), degree=3, max_segments=9):
    """N-sided surface patch from 3-4+ boundary curves (BRepOffsetAPI_MakeFilling = GeomPlate). boundary = edges or
    wires forming a closed loop. continuity per edge 'C0'|'G1'|'G2' with support_faces (the faces the patch must be
    tangent / curvature-continuous to). points = extra interior points to pass through. Returns Face."""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
    from OCP.GeomAbs import GeomAbs_C0, GeomAbs_G1, GeomAbs_G2
    from OCP.gp import gp_Pnt
    edges = [x for c in boundary for x in (c.edges() if hasattr(c, "edges") and not isinstance(c, Edge) else [c])]
    cont = {"C0": GeomAbs_C0, "G1": GeomAbs_G1, "G2": GeomAbs_G2}
    mk = BRepOffsetAPI_MakeFilling(degree, 15, 2, False, 1e-5, 1e-4, 1e-2, 0.1, 8, max_segments)
    for i, e in enumerate(edges):
        c = (continuity[i] if isinstance(continuity, (list, tuple)) else continuity) or "C0"
        sf = support_faces[i] if support_faces and i < len(support_faces) else None
        if sf is not None and c != "C0":
            mk.Add(e.wrapped, sf.wrapped, cont[c], True)
        else:
            mk.Add(e.wrapped, GeomAbs_C0, True)
    for p in points:
        mk.Add(gp_Pnt(*p))
    mk.Build()
    if not mk.IsDone():
        raise CadOpError("patch failed: boundary must be a closed loop of 3+ curves (check gaps)")
    f = Shape.cast(mk.Shape())
    return f if isinstance(f, Face) else f.faces()[0]


def coons_patch(c1, c2, c3, c4, style="coons"):
    """Exact 4-sided patch through 4 B-spline boundary curves (GeomFill_BSplineCurves). Curves in loop order."""
    from OCP.GeomFill import GeomFill_BSplineCurves, GeomFill_CoonsStyle, GeomFill_CurvedStyle, GeomFill_StretchStyle
    from OCP.GeomConvert import GeomConvert
    from OCP.BRep import BRep_Tool
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    st = {"coons": GeomFill_CoonsStyle, "curved": GeomFill_CurvedStyle, "stretch": GeomFill_StretchStyle}[style]
    bs = []
    for e in (c1, c2, c3, c4):
        e = e if isinstance(e, Edge) else e.edges()[0]
        from OCP.BRepAdaptor import BRepAdaptor_Curve
        ad = BRepAdaptor_Curve(e.wrapped)
        a, b = ad.FirstParameter(), ad.LastParameter()
        crv = BRep_Tool.Curve_s(e.wrapped, 0.0, 1.0)
        from OCP.Geom import Geom_TrimmedCurve
        bs.append(GeomConvert.CurveToBSplineCurve_s(Geom_TrimmedCurve(crv, a, b)))
    for sty in [st] + [x for x in (GeomFill_CurvedStyle, GeomFill_StretchStyle, GeomFill_CoonsStyle) if x != st]:
        try:
            fill = GeomFill_BSplineCurves(bs[0], bs[1], bs[2], bs[3], sty)
            return Face(BRepBuilderAPI_MakeFace(fill.Surface(), 1e-6).Face())
        except Exception:
            continue
    # OCCT rejects some curve sets (degree/orientation) -> GeomPlate patch through the same 4 boundaries
    _rec(op="coons_patch", status="fallback", method="patch")
    return patch([c1, c2, c3, c4])


def blend_surface(edge_a, face_a, edge_b, face_b, continuity="G2", n=24, m=11, tension=1.0, flip_a=False,
                  flip_b=False):
    """Blend surface between two face edges (G1 or G2 across both boundaries). For each of n stations: G1/G2
    bridge curve leaving face_a along its cross-tangent (normal x edge tangent, pointing off the face) and arriving
    on face_b; the m x n point grid is interpolated with a bicubic B-spline surface. Use when an OCCT fillet can't
    (OCCT has no G2 fillet). Returns Face."""
    from OCP.GeomAPI import GeomAPI_PointsToBSplineSurface
    from OCP.GeomAbs import GeomAbs_C2
    try:
        from OCP.collections import Array2_gp_Pnt as TColgp_Array2OfPnt  # OCP 8
    except ImportError:
        from OCP.TColgp import TColgp_Array2OfPnt
    from OCP.gp import gp_Pnt
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    pb0, pb1 = edge_b.position_at(0), edge_b.position_at(1)
    rev = (edge_a.position_at(0) - pb0).length + (edge_a.position_at(1) - pb1).length > \
        (edge_a.position_at(0) - pb1).length + (edge_a.position_at(1) - pb0).length
    grid = []
    for i in range(n):
        u = i / (n - 1)
        ub = 1 - u if rev else u
        pa, pb = edge_a.position_at(u), edge_b.position_at(ub)
        da = _cross_dir(face_a, edge_a, u, pb, flip_a)
        db = _cross_dir(face_b, edge_b, ub, pa, flip_b)
        L = (pb - pa).length * tension
        if continuity == "G1":
            P = [pa, pa + da * (L / 3), pb + db * (L / 3), pb]
        else:  # G2 to the faces' cross-curvature ~0 along the cross direction (exact for planar/ruled support)
            d = L / 5 * 1.6
            P = [pa, pa + da * d, pa + da * (2 * d), pb + db * (2 * d), pb + db * d, pb]
        bz = Edge.make_bezier(*P)
        grid.append([bz.position_at(j / (m - 1)) for j in range(m)])
    arr = TColgp_Array2OfPnt(1, n, 1, m)
    for i in range(n):
        for j in range(m):
            p = grid[i][j]
            arr.SetValue(i + 1, j + 1, gp_Pnt(p.X, p.Y, p.Z))
    srf = GeomAPI_PointsToBSplineSurface(arr, 3, 8, GeomAbs_C2, 1e-6).Surface()
    return Face(BRepBuilderAPI_MakeFace(srf, 1e-6).Face())


def _cross_dir(face, edge, u, toward, flip):
    p, t = edge.position_at(u), edge.tangent_at(u)
    nrm = face.normal_at(p)
    d = nrm.cross(t).normalized()
    # point off the face: the face's interior is on one side; pick the side away from the face centre
    probe = face.center()
    if (probe - p).dot(d) > 0:
        d = -d
    return -d if flip else d
