"""Shape-from-profile: extrude (push/pull), revolve, sweep, loft (+guide/spine), pipe."""
from __future__ import annotations

import math

from build123d import Axis, Edge, Face, Plane, Solid, Vector, Wire, extrude, loft as _loft, revolve as _revolve, \
    sweep as _sweep

from .core import ToolError, apply_mode, op, resolve, vec
from .geom import _one_face, _wire


def _profile(m, ref):
    """Region / face / closed curve -> Face."""
    s = resolve(m, ref)
    if isinstance(s, (Wire, Edge)):
        w = s if isinstance(s, Wire) else Wire([s])
        if not w.is_closed:
            raise ToolError(f"profile {ref!r} is an open curve", "close it, or make regions from it first")
        return Face(w)
    return _one_face(m, ref)


@op("extrude", "spec 1 Shape-from-profile: Extrude (distance1/2, draft per side, thickness1/2, "
               "operationType new/union/difference/intersect); spec 5.1/5.3")
def extrude_op(m, name, profile, distance, distance2=0.0, draft=0.0, draft2=None, thickness=0.0, mode="new",
               target=None, direction=None):
    """Push/pull a region/face/closed curve. distance along normal (or `direction`), distance2 the other way.
    draft deg (+ = taper in), thickness>0 -> thin wall of that width (inset of the profile). mode new|union|cut|
    intersect with target body."""
    f = _profile(m, profile)
    if thickness > 0:
        inner = f.outer_wire().offset_2d(-thickness)
        try:
            f = Face(f.outer_wire(), [inner])
        except Exception as e:
            raise ToolError(f"thin-wall inset {thickness} failed: {e}", "thickness < half the narrowest profile width")
    n = vec(direction).normalized() if direction else f.normal_at(f.center())
    parts = []
    if abs(distance) > 1e-12:
        parts.append(extrude(f, amount=distance, dir=n, taper=draft))
    if abs(distance2) > 1e-12:
        parts.append(extrude(f, amount=distance2, dir=-n, taper=draft if draft2 is None else draft2))
    if not parts:
        raise ToolError("extrude distance is 0")
    new = parts[0] if len(parts) == 1 else parts[0] + parts[1]
    out = apply_mode(m, name, new, mode, target, f"extrude:{name}")
    return {"name": out, "volume": round(m.get(out).shape.volume, 9)}


@op("revolve", "spec 1 Shape-from-profile: Revolve (axis, angle, thickness)")
def revolve_op(m, name, profile, axis_origin=(0, 0, 0), axis_dir="z", angle=360.0, mode="new", target=None):
    f = _profile(m, profile)
    ax = Axis(Vector(*axis_origin), vec(axis_dir))
    new = _revolve(f, ax, angle)
    return {"name": apply_mode(m, name, new, mode, target)}


@op("sweep", "spec 1 Shape-from-profile: Sweep (profile, path, mode)")
def sweep_op(m, name, profile, path, frenet=False, transition="right", mode="new", target=None):
    """Sweep a profile (closed curve/region, placed at the path start) along a path curve."""
    from build123d import Transition
    f = _profile(m, profile)
    p = _wire(m, path)
    tr = {"right": Transition.RIGHT, "round": Transition.ROUND, "transformed": Transition.TRANSFORMED}[transition]
    new = _sweep(f, p, is_frenet=frenet, transition=tr)
    return {"name": apply_mode(m, name, new, mode, target)}


@op("loft", "spec 1 Shape-from-profile: Loft (ordered curves/regions, guides, closed, ruled)")
def loft_op(m, name, profiles, ruled=False, guide=None, mode="new", target=None):
    """Loft ordered profiles. guide = path curve: sections are swept along it as a spine (pipe-shell loft:
    OCCT has no true multi-rail guide loft)."""
    fs = [_profile(m, p) for p in profiles]
    if len(fs) < 2:
        raise ToolError("loft needs >= 2 profiles")
    if guide is None:
        new = _loft(fs, ruled=ruled)
    else:
        new = _guided_loft(fs, _wire(m, guide))
    if not new.is_valid:
        raise ToolError("loft produced an invalid solid", "use profiles with equal edge counts and no twist")
    return {"name": apply_mode(m, name, new, mode, target)}


def _guided_loft(faces, spine):
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
    from build123d import Shape
    ps = BRepOffsetAPI_MakePipeShell(spine.wrapped)
    for f in faces:
        ps.Add(f.outer_wire().wrapped, False, False)
    ps.Build()
    if not ps.IsDone():
        raise ToolError("guided loft failed", "profiles should sit on/near the guide; try without guide")
    ps.MakeSolid()
    return Solid(ps.Shape()) if Shape.cast(ps.Shape()).__class__.__name__ == "Solid" else Shape.cast(ps.Shape())


@op("pipe", "spec 1 Shape-from-profile: Pipe (path, radius, inner radius)")
def pipe_op(m, name, path, radius, inner_radius=0.0, mode="new", target=None):
    """Round tube along a path curve (cables, hoses). inner_radius>0 -> hollow."""
    p = _wire(m, path)
    if inner_radius >= radius:
        raise ToolError("inner_radius must be < radius")
    t0 = p.tangent_at(0)
    pl = Plane(p.position_at(0), z_dir=t0)
    w = Wire([Edge.make_circle(radius, pl)])
    inner = [Wire([Edge.make_circle(inner_radius, pl)])] if inner_radius > 0 else []
    from build123d import Transition
    new = _sweep(Face(w, inner), p, transition=Transition.ROUND)
    return {"name": apply_mode(m, name, new, mode, target)}
