"""Product-modelling ops that close PARITY.md gaps: push/pull with automatic re-fillet, boolean + fillet of the new
intersection edges, symmetrize (half-model + mirror), curve-network surface, offset curve on a face, draft-angle
face edit.  Clean-room from docs/plasticity_spec.md (section 2.5 "forgiving direct edits", section 1 Mirror,
Surfaces, Curves edit)."""
from __future__ import annotations

import math

from build123d import Edge, Face, GeomType, Keep, Shape, Vector

from cadkit.ops import CadOpError, safe_boolean, safe_fillet
from .core import ToolError, op, resolve, vec
from .edit import _cast_solid, _defeature, _maxr, _solid
from .geom import _one_face, _wire, get_plane


def _blend_radius(f):
    g = f.geom_type
    try:
        if g == GeomType.CYLINDER:
            return f.radius
        if g == GeomType.TORUS:
            return f.minor_radius
        if g == GeomType.SPHERE:
            return f.radius
    except Exception:
        return None
    return None


def _blends(s, max_radius, exclude=()):
    out = []
    for f in s.faces():
        if any(f.is_same(x) for x in exclude):
            continue
        r = _blend_radius(f)
        if r is not None and r <= max_radius:
            out.append((f, r))
    return out


def _faces(m, body, ref):
    ref = {"obj": body, "faces": ref} if isinstance(ref, dict) and "obj" not in ref else ref
    fs = list(resolve(m, ref, "faces"))
    if not fs:
        raise ToolError(f"face ref {ref!r} matched nothing", "inspect with cad_suggest_refs / cad_select")
    return fs


def _refillet_groups(s, groups):
    """groups = [(radius, [edge centres + dirs])]; re-find the nearest edges on s each round, fillet biggest first."""
    done = 0
    for r, keys in sorted(groups, key=lambda g: -g[0]):
        es = []
        for c, d, tol in keys:
            best = None
            for e in s.edges():
                dist = (e.center() - c).length
                if dist > tol:
                    continue
                if d is not None and e.geom_type == GeomType.LINE:
                    ed = (e.position_at(1) - e.position_at(0)).normalized()
                    if abs(abs(ed.dot(d)) - 1) > 1e-3:
                        continue
                if best is None or dist < best[0]:
                    best = (dist, e)
            if best and not any(best[1].is_same(x) for x in es):
                es.append(best[1])
        if not es:
            continue
        try:
            s = safe_fillet(s, es, r, min_frac=0.3, label="push_pull:refillet")
        except CadOpError as e:
            raise ToolError(f"re-fillet r={r} failed after the face move: {e}", "smaller move, or pass refillet=false "
                            "and fillet by hand", {"max_feasible": _maxr(str(e))}) from e
        done += len(es)
    return s, done


@op("push_pull", "spec 2.5 forgiving direct edits: push/pull faces of an already-filleted body, blends rebuilt "
                 "(remove blends -> offset face -> re-fillet the healed edges at their old radii)", out=False)
def push_pull(m, body, faces, distance, refillet=True, max_radius=0.05):
    """Move faces along their normals by `distance` on a filleted body and rebuild the blends.
    Blends = cylinder/torus/sphere faces with radius <= max_radius (not the moved faces themselves).
    Example: {"body": "case", "faces": {"normal": "+x"}, "distance": 0.02}"""
    from cadkit.surf import robust_offset_face
    s0 = _solid(m, body)
    targets = _faces(m, body, faces)
    blends = _blends(s0, max_radius, exclude=targets) if refillet else []
    meta = m.get(body).meta
    if not blends:
        res, method = robust_offset_face(s0, targets, distance, label=body)
        m.put(body, "solid", res, **meta)
        return {"name": body, "method": method, "refilleted": 0}
    old = [e.center() for e in s0.edges()]
    s1 = _defeature(s0, [f for f, _ in blends])
    boxes = [(f.bounding_box(), r) for f, r in blends]
    groups: dict = {}
    for e in s1.edges():
        c = e.center()
        if min((c - o).length for o in old) < 1e-6:
            continue
        for bb, r in boxes:
            pad = r * 0.5 + 1e-6
            if all(lo - pad <= v <= hi + pad for v, lo, hi in zip(tuple(c), tuple(bb.min), tuple(bb.max))):
                d = (e.position_at(1) - e.position_at(0)).normalized() if e.geom_type == GeomType.LINE else None
                groups.setdefault(round(r, 9), []).append((c, d, abs(distance) * 1.01 + r + 1e-6))
                break
    m.put(body, "solid", s1, **meta)                       # re-resolve the semantic face ref on the healed body
    try:
        t1 = _faces(m, body, faces)
        try:
            res, method = robust_offset_face(s1, t1, distance, label=body)
        except CadOpError as e:
            raise ToolError(str(e), "smaller distance") from e
        res, n = _refillet_groups(res, list(groups.items()))
    except Exception:
        m.put(body, "solid", s0, **meta)
        raise
    m.put(body, "solid", res, **meta)
    return {"name": body, "method": method, "blends_removed": len(blends), "refilleted": n,
            "radii": sorted(groups)}


@op("boolean_fillet", "spec 1 Booleans + Fillet: boolean, then fillet only the NEW intersection edges "
                      "(fillet propagation across the seam)", out=False)
def boolean_fillet(m, kind, target, tools, radius, keep_tools=False, shape="round"):
    """union|cut|intersect target with tools, then round the seam edges (edges lying on the section curve).
    Example: {"kind": "union", "target": "body", "tools": ["boss"], "radius": 0.005}"""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from .edit import boolean as _bool
    tools = [tools] if isinstance(tools, str) else list(tools)
    a = _solid(m, target)
    secs = []
    for t in tools:
        sec = BRepAlgoAPI_Section(a.wrapped, _solid(m, t).wrapped)
        sec.Build()
        secs.append(Shape.cast(sec.Shape()))
    info = _bool(m, name="boolean_auto", kind=kind, target=target, tools=tools, keep_tools=keep_tools)
    s = _solid(m, target)
    seam = [e for e in s.edges() if any(sc.edges() and sc.distance_to(e.center()) < 1e-5 for sc in secs)]
    if not seam:
        raise ToolError("boolean ok but no seam edges found", "tools may only touch the target; nothing to fillet")
    if shape == "chamfer":
        from cadkit.ops import safe_chamfer
        fn = lambda: safe_chamfer(s, seam, radius, label=f"boolean_fillet:{target}")  # noqa: E731
    else:
        fn = lambda: safe_fillet(s, seam, radius, label=f"boolean_fillet:{target}")  # noqa: E731
    try:
        res = fn()
    except CadOpError as e:
        raise ToolError(str(e), "lower radius", {"max_feasible": _maxr(str(e))}) from e
    m.put(target, "solid", res, **m.get(target).meta)
    return {"name": target, "seam_edges": len(seam), "volume": round(res.volume, 9), "boolean": info}


@op("symmetrize", "spec 1 Mirror (auto-union across the symmetry plane) + spec 5.6: half-model workflow - cut the "
                  "body at the plane, keep one side, mirror it back and fuse (exactly symmetric result)", out=False)
def symmetrize(m, body, plane="YZ", keep="+"):
    """Make body exactly symmetric about plane (XY/XZ/YZ, cplane name, {origin, normal}). keep '+' = side the
    plane normal points to is the master half. Model the half you like, call this after every few edits.
    Example: {"body": "car", "plane": "XZ", "keep": "+"}"""
    s = _solid(m, body)
    pl = get_plane(m, plane)
    half = s.split(pl, keep=Keep.TOP if keep == "+" else Keep.BOTTOM)
    sols = half.solids() if hasattr(half, "solids") else [half]
    if not sols:
        raise ToolError("nothing on the kept side of the plane", "flip keep or move the plane")
    h = sols[0] if len(sols) == 1 else safe_boolean("fuse", sols[0], sols[1:], "symmetrize")
    from build123d import mirror as _mirror
    res = safe_boolean("fuse", h, _mirror(h, about=pl), "symmetrize")
    res = _cast_solid(res.wrapped) if len(res.solids()) == 1 else res
    m.put(body, "solid", res, **{**m.get(body).meta, "symmetry": str(plane)})
    return {"name": body, "volume": round(res.volume, 9), "solids": len(res.solids())}


@op("curve_network", "spec 1 Surfaces (network surface): boundary loop + interior guide curves the surface must "
                     "pass through (GeomPlate free constraints); per-boundary C0/G1/G2 to support faces")
def curve_network(m, name, boundary, interior=None, continuity="C0", support=None, points=None):
    """Surface over a closed boundary loop (curve refs) that also follows `interior` curves (u/v network lines,
    need not touch the boundary). Result: sheet. Sew / thicken it after.
    Example: {"boundary": ["e1","e2","e3","e4"], "interior": ["mid_u", "mid_v"], "continuity": "C0"}"""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
    from OCP.GeomAbs import GeomAbs_C0, GeomAbs_G1, GeomAbs_G2
    from OCP.gp import gp_Pnt
    cont = {"C0": GeomAbs_C0, "G1": GeomAbs_G1, "G2": GeomAbs_G2}
    bedges = [e for c in boundary for e in _wire(m, c).edges()]
    sup = [(_one_face(m, s) if s is not None else None) for s in support] if support else None
    mk = BRepOffsetAPI_MakeFilling(3, 15, 2, False, 1e-5, 1e-4, 1e-2, 0.1, 8, 9)
    for i, e in enumerate(bedges):
        c = (continuity[i] if isinstance(continuity, (list, tuple)) else continuity) or "C0"
        sf = sup[i] if sup and i < len(sup) else None
        if sf is not None and c != "C0":
            mk.Add(e.wrapped, sf.wrapped, cont[c], True)
        else:
            mk.Add(e.wrapped, GeomAbs_C0, True)
    for c in interior or []:
        for e in _wire(m, c).edges():
            mk.Add(e.wrapped, GeomAbs_C0, False)
    for p in points or []:
        mk.Add(gp_Pnt(*p))
    mk.Build()
    if not mk.IsDone():
        raise ToolError("curve network surface failed", "boundary must be a closed loop (shared ends); interior curves "
                        "should lie inside the loop and not cross each other far off the surface")
    f = Shape.cast(mk.Shape())
    f = f if isinstance(f, Face) else f.faces()[0]
    m.put(name, "sheet", f)
    return {"name": name, "area": round(f.area, 9)}


def _project_on_face(f, p):
    from OCP.BRep import BRep_Tool
    from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
    from OCP.gp import gp_Pnt
    pr = GeomAPI_ProjectPointOnSurf(gp_Pnt(p.X, p.Y, p.Z), BRep_Tool.Surface_s(f.wrapped))
    if pr.NbPoints() == 0:
        return p
    q = pr.NearestPoint()
    return Vector(q.X(), q.Y(), q.Z())


@op("offset_curve_on_face", "spec 1 Curves edit: Offset curve (on a surface, geodesic-ish: step sideways in the face "
                            "tangent plane, re-project) - panel lines / trim borders on curved bodies")
def offset_curve_on_face(m, name, curve, face, distance, samples=64):
    """Offset a curve lying on face sideways by `distance` (sign = side: +n x tangent). Result curve stays on the
    face's surface. Example: {"curve": "rim", "face": {"obj":"shell","faces":{"geom":"bspline","pick":"largest"}},
    "distance": 0.004}"""
    w = _wire(m, curve)
    f = _one_face(m, face)
    closed = bool(w.is_closed)
    n = max(8, int(samples))
    pts = []
    for i in range(n + (0 if closed else 1)):
        t = i / n
        p = w.position_at(t)
        tan = w.tangent_at(t)
        nrm = f.normal_at(_project_on_face(f, p))
        side = nrm.cross(tan)
        if side.length < 1e-9:
            raise ToolError("curve tangent parallel to face normal", "the curve must lie on / along the face")
        q = p + side.normalized() * distance
        for _ in range(2):  # step + re-project twice (keeps the arc length offset on curved faces)
            q = _project_on_face(f, q)
        pts.append(q)
    e = Edge.make_spline(pts, periodic=closed)
    m.put(name, "curve", e, source=str(curve))
    return {"name": name, "length": round(e.length, 6), "closed": closed}


@op("draft_face", "spec 1 Direct edit: draft face (taper side faces by an angle about a neutral plane, pull dir)",
    out=False)
def draft_face(m, body, faces, angle, pull="+z", neutral=None):
    """Tilt faces by `angle` degrees (moulding draft). neutral = plane {origin, normal} / cplane name (default:
    plane through body bbox min along pull). Example: {"body":"case","faces":{"geom":"plane","normal":"+x"},
    "angle": 2}"""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_DraftAngle
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
    s = _solid(m, body)
    fs = _faces(m, body, faces)
    d = vec(pull).normalized()
    if neutral is None:
        bb = s.bounding_box()
        o = Vector(*[lo if c > 0 else hi for c, lo, hi in zip(tuple(d), tuple(bb.min), tuple(bb.max))])
        pl_o, pl_n = o, d
    else:
        pl = get_plane(m, neutral)
        pl_o, pl_n = pl.origin, pl.z_dir
    pln = gp_Pln(gp_Pnt(pl_o.X, pl_o.Y, pl_o.Z), gp_Dir(pl_n.X, pl_n.Y, pl_n.Z))
    mk = BRepOffsetAPI_DraftAngle(s.wrapped)
    for f in fs:
        mk.Add(f.wrapped, gp_Dir(d.X, d.Y, d.Z), math.radians(angle), pln)
        if not mk.AddDone():
            raise ToolError("draft not possible on a face", "draft planar/ruled side faces; remove fillets first")
    mk.Build()
    if not mk.IsDone():
        raise ToolError("draft failed", "remove neighbouring fillets first, then refillet")
    res = _cast_solid(mk.Shape())
    if not res.is_valid:
        raise ToolError("draft gave an invalid body", "smaller angle / fewer faces")
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "faces": len(fs), "volume": round(res.volume, 9)}


@op("network_surface", "spec 1 Surfaces (network): Gordon surface through a u/v curve network (sections x feature "
                       "lines), normalised + fitted as one C2 B-spline; reports per-curve deviation")
def network_surface(m, name, u_curves, v_curves, tol=None, grid=60):
    """u_curves: sections (curve refs), v_curves: feature lines; every u-curve must cross every v-curve (any
    direction/degree/knots: they are oriented, sorted and reparametrised). Result: sheet (one C2 face).
    info.max_dev = worst distance of a network curve to the surface (model units). Then mirror / sew / thicken."""
    from cadkit.network import gordon_surface
    from cadkit.ops import CadOpError
    us = [_wire(m, c) for c in u_curves]
    vs = [_wire(m, c) for c in v_curves]
    try:
        f, rep = gordon_surface(us, vs, nu=grid, nv=grid, tol=tol)
    except CadOpError as e:
        raise ToolError(str(e), "make sure each section crosses each feature line (snap ends onto the lines)") from e
    m.put(name, "sheet", f)
    return {"name": name, "area": round(f.area, 9), "max_dev": rep["max_dev"], "per_curve_max_dev":
            rep["per_curve_max_dev"]}


@op("continuity", "query: edge continuity report G0/G1/G2 (gap, normal angle, cross-curvature jump) per shared edge",
    out=False)
def continuity_op(m, obj, edges=None, g1_deg=0.1, g2_rel=0.05):
    """For every edge shared by 2 faces of obj (or the edge ref): gap, angle_deg, dk_rel, cls G2|G1|G0|open.
    Use after sew / blend to prove class-A joins (target: G2 on visible joins)."""
    from cadkit.network import edge_continuity
    s = m.get(obj).shape
    es = list(resolve(m, edges, "edges")) if edges else None
    r = edge_continuity(s, es, g1_deg=g1_deg, g2_rel=g2_rel)
    r["edges"] = r["edges"][:60]
    return r


@op("zebra", "query: isophote zebra of a face - kink (crease detector, ~1-3 smooth) / wiggle (waviness) + png",
    out=False)
def zebra_op(m, face, png=None, light=(0.35, -0.45, 0.82)):
    from cadkit.network import zebra
    return zebra(_one_face(m, face), png=png, light=light)
