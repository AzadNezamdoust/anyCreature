"""Surfacing ops: multi-rail loft, boundary patch (GeomPlate) / Coons patch, G2 bridge curve, G2 blend surface,
curve trim/join, helix, loft end-cap round, sew sheets -> solid. Geometry in cadkit.surf."""
from __future__ import annotations

from build123d import Edge, Shape, Solid, Wire

from cadkit import surf
from cadkit.ops import CadOpError
from .core import ToolError, apply_mode, op, resolve
from .geom import _one_face, _wire


def _wires(m, refs):
    return [_wire(m, r) for r in refs]


def _edge(m, ref):
    s = resolve(m, ref)
    if isinstance(s, Edge):
        return s
    if isinstance(s, Wire) and len(s.edges()) == 1:
        return s.edges()[0]
    if isinstance(s, (list,)) or hasattr(s, "filter_by"):
        if len(s) == 1:
            return s[0]
    if isinstance(s, Wire):
        return Edge.make_spline([s.position_at(i / 40) for i in range(41)])
    raise ToolError(f"{ref!r} must be one curve/edge")


def _wrap(fn, hint):
    try:
        return fn()
    except CadOpError as e:
        raise ToolError(str(e), hint) from e


@op("rail_loft", "spec 1 Shape-from-profile: Loft with guides (2+ rails: sections are blended and fitted so "
                 "their contact points ride every rail)")
def rail_loft_op(m, name, profiles, rails, sections=12, ruled=False, mode="new", target=None):
    """Multi-rail loft. profiles = curve refs (closed -> solid, open -> sheet) that touch every rail; rails = 2+
    guide curve refs. sections = intermediate stations."""
    res = _wrap(lambda: surf.rail_loft(_wires(m, profiles), _wires(m, rails), n=sections, ruled=ruled),
                "every profile must touch every rail (nearest points); order rails consistently")
    if isinstance(res, Solid) or res.solids():
        return {"name": apply_mode(m, name, res if isinstance(res, Solid) else res.solids()[0], mode, target)}
    m.put(name, "sheet", res)
    return {"name": name, "kind": "sheet"}


@op("patch", "spec 1 Surfaces: patch / fill N-sided boundary (GeomPlate), C0/G1/G2 to support faces")
def patch_op(m, name, curves, continuity="C0", support=None, points=None):
    """Surface from a closed loop of 3+ boundary curves (refs). continuity C0|G1|G2 (single or per curve);
    support = per-curve face ref (the neighbour the patch must be tangent/curvature continuous to) or null.
    points = interior points to pass through."""
    edges = [e for c in curves for e in _wire(m, c).edges()]
    sup = [(_one_face(m, s) if s is not None else None) for s in support] if support else None
    f = _wrap(lambda: surf.patch(edges, continuity, sup, points or []), "close the loop (shared end points)")
    m.put(name, "sheet", f)
    return {"name": name, "area": round(f.area, 9)}


@op("coons_patch", "spec 1 Surfaces: 4-sided boundary surface (Coons / curved / stretch style)")
def coons_op(m, name, curves, style="coons"):
    """Exact 4-curve boundary surface; curves in loop order (end points shared)."""
    if len(curves) != 4:
        raise ToolError("coons_patch needs exactly 4 curves", "use patch for 3 or 5+")
    f = surf.coons_patch(*[_edge(m, c) for c in curves], style=style)
    m.put(name, "sheet", f)
    return {"name": name, "area": round(f.area, 9)}


@op("bridge_curve", "spec 1 Curves edit: Bridge / blend curve between two curve ends (G1 cubic, G2 quintic)")
def bridge_op(m, name, a, b, a_end=1.0, b_end=0.0, continuity="G2", tension=1.0):
    """Curve from the end of curve a (a_end 0|1) to curve b (b_end 0|1), tangent (G1) or curvature (G2) matched."""
    e = surf.bridge_curve(_edge(m, a), _edge(m, b), a_end, b_end, continuity, tension)
    m.put(name, "curve", Wire([e]))
    return {"name": name, "length": round(e.length, 6)}


@op("trim_curve", "spec 1 Curves edit: Trim / split curve (param range)")
def trim_op(m, name, curve, start=0.0, end=1.0):
    """Keep the part of curve between normalised params start..end."""
    w = _wire(m, curve)
    e = surf.trim_curve(w, start, end)
    m.put(name, "curve", e if isinstance(e, Wire) else Wire([e]))
    return {"name": name}


@op("join_curves", "spec 1 Curves edit: Join curves into one wire")
def join_op(m, name, curves, tol=1e-6, delete=False):
    w = surf.join_curves(_wires(m, curves), tol)
    m.put(name, "curve", w)
    if delete:
        for c in curves:
            if isinstance(c, str) and c != name:
                m.objects.pop(c, None)
    return {"name": name, "closed": bool(w.is_closed), "edges": len(w.edges())}


@op("helix", "spec 1 Curves: Helix / spiral (pitch, height, radius)")
def helix_op(m, name, pitch, height, radius, center=None, direction="z", lefthand=False):
    from .core import vec
    d = vec(direction)
    m.put(name, "curve", surf.helix(pitch, height, radius, center or (0, 0, 0), (d.X, d.Y, d.Z), lefthand))
    return {"name": name}


@op("blend_surface", "spec 1 Fillet 'smooth' / surfaces: blend surface between two face edges, G1 or true G2 "
                     "(OCCT has no G2 fillet: bridge-curve network -> B-spline surface)")
def blend_op(m, name, edge_a, face_a, edge_b, face_b, continuity="G2", tension=1.0, flip_a=False, flip_b=False):
    """edge_a/face_a, edge_b/face_b = refs (edge on its face). Result = sheet; use sew to close a solid."""
    f = surf.blend_surface(_edge(m, edge_a), _one_face(m, face_a), _edge(m, edge_b), _one_face(m, face_b),
                           continuity, tension=tension, flip_a=flip_a, flip_b=flip_b)
    m.put(name, "sheet", f)
    return {"name": name, "area": round(f.area, 9)}


@op("cap_round", "spec 1 Fillet: round a loft/sweep end cap (cap-face handling: trim + quarter-round loft)",
    out=False)
def cap_round_op(m, body, face, radius):
    """face = ref of the planar end cap. The plain fillet op routes cap rims here automatically."""
    s = m.get(body, ("solid",)).shape
    f = _one_face(m, {"obj": body, "faces": face} if isinstance(face, dict) and "obj" not in face else face)
    res = _wrap(lambda: surf.cap_round(s, f, radius, label=body), "radius < half the cap's narrowest width")
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "faces": len(res.faces())}


@op("sew", "spec 1 Surfaces: join/sew sheets (and solids' faces) into a shell/solid")
def sew_op(m, name, sheets, tol=1e-5, delete=True):
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
    sw = BRepBuilderAPI_Sewing(tol)
    for r in sheets:
        for f in resolve(m, r).faces():
            sw.Add(f.wrapped)
    sw.Perform()
    sh = Shape.cast(sw.SewedShape())
    shells = sh.shells() if hasattr(sh, "shells") else []
    kind, out = "sheet", sh
    if len(shells) == 1:
        try:
            s = surf.solid_from_shell(shells[0])
            if s is not None:
                kind, out = "solid", s
        except Exception:
            pass
    m.put(name, kind, out)
    if delete:
        for r in sheets:
            if isinstance(r, str) and r != name:
                m.objects.pop(r, None)
    return {"name": name, "kind": kind}
