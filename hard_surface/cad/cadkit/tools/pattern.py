"""Mirror, linear/radial arrays, linked instances, transforms (move/rotate/scale), duplicate."""
from __future__ import annotations

import math

from build123d import Axis, Compound, Location, Part, Plane, Pos, Vector, mirror as _mirror

from cadkit.ops import safe_boolean
from .core import ToolError, op, vec
from .geom import get_plane


def _get(m, name):
    o = m.get(name)
    return o, o.shape


def _combine(m, base, pieces, union):
    if union:
        return safe_boolean("fuse", base, pieces if len(pieces) > 1 else pieces[0], "pattern")
    return Compound([base] + list(pieces))


@op("mirror", "spec 1 Mirror across a plane or face (keep or replace, auto-union across symmetry plane); spec 5.6")
def mirror_op(m, name, body, plane="YZ", keep=True, union=True):
    """Mirror body across plane (XY/XZ/YZ, cplane, {origin, normal}). keep+union -> fused symmetric body
    replaces `body`; keep+not union -> copy as `name`; keep=False -> body replaced by its mirror."""
    o, s = _get(m, body)
    pl = get_plane(m, plane)
    mir = _mirror(s, about=pl)
    if not keep:
        m.put(body, o.kind, mir, **o.meta)
        return {"name": body}
    if union and o.kind == "solid":
        m.put(body, "solid", safe_boolean("fuse", s, mir, "mirror"), **o.meta)
        return {"name": body}
    m.put(name, o.kind, mir, mirror_of=body)
    return {"name": name}


@op("linear_array", "spec 1 Rectangular arrays (count, spacing); spec 5.6")
def linear_array(m, name, body, count, step, count2=1, step2=None, union=False):
    """count copies spaced by vector `step` (optionally a 2nd direction count2/step2). union -> fuse into one
    body `name`; else a compound `name` (body itself is removed and becomes element 0)."""
    o, s = _get(m, body)
    st, st2 = Vector(*step), Vector(*(step2 or (0, 0, 0)))
    pcs = [Pos(*(st * i + st2 * j)) * s for j in range(count2) for i in range(count) if i or j]
    m.put(name, o.kind if union else "solid", _combine(m, s, pcs, union), array_of=body, count=count * count2)
    if name != body:
        m.objects.pop(body, None)
    return {"name": name, "count": count * count2}


@op("radial_array", "spec 1 Radial arrays (count, angle); spec 5.6")
def radial_array(m, name, body, count, axis_origin=(0, 0, 0), axis_dir="z", angle=360.0, union=False):
    o, s = _get(m, body)
    ax = Axis(Vector(*axis_origin), vec(axis_dir))
    full = abs(angle - 360) < 1e-9
    da = angle / (count if full else max(count - 1, 1))
    pcs = [s.rotate(ax, da * i) for i in range(1, count)]
    m.put(name, "solid", _combine(m, s, pcs, union), array_of=body, count=count)
    if name != body:
        m.objects.pop(body, None)
    return {"name": name, "count": count}


@op("instance", "spec 1 Linked instances (CreateInstance) / realize (RealizeInstance)")
def instance(m, name, source, move=(0, 0, 0), rotate=None):
    """Linked copy: geometry is re-derived from `source` on every replay, so editing the source's ops updates all
    instances. rotate = [axis_dir, degrees] about the source centre."""
    o, s = _get(m, source)
    t = s
    if rotate:
        t = t.rotate(Axis(s.center(), vec(rotate[0])), rotate[1])
    m.put(name, o.kind, Pos(*move) * t, instance_of=source, xform=[list(move), rotate])
    return {"name": name}


@op("realize", "spec 1 RealizeInstance: instance -> independent copy", out=False)
def realize(m, name):
    o = m.get(name)
    o.meta.pop("instance_of", None)
    return {"name": name}


@op("duplicate", "spec 1 Duplicate")
def duplicate(m, name, source):
    o, s = _get(m, source)
    m.put(name, o.kind, s.moved(Location()), **o.meta)
    return {"name": name}


@op("move", "spec 1 Transforms: Move (typed values)", out=False)
def move(m, obj, by):
    o, s = _get(m, obj)
    m.put(obj, o.kind, Pos(*by) * s, **o.meta)
    return {"name": obj}


@op("rotate", "spec 1 Transforms: Rotate (pivot = given point / bbox centre)", out=False)
def rotate(m, obj, axis_dir, angle, pivot=None):
    o, s = _get(m, obj)
    pv = Vector(*pivot) if pivot else s.bounding_box().center()
    m.put(obj, o.kind, s.rotate(Axis(pv, vec(axis_dir)), angle), **o.meta)
    return {"name": obj}


@op("scale", "spec 1 Transforms: Scale (uniform, pivot)", out=False)
def scale(m, obj, factor, pivot=None):
    o, s = _get(m, obj)
    pv = Vector(*pivot) if pivot else s.bounding_box().center()
    r = Pos(*pv) * (Pos(*(-pv)) * s).scale(factor)
    m.put(obj, o.kind, r, **o.meta)
    return {"name": obj}


@op("delete", "utility: delete object", out=False)
def delete(m, obj):
    m.get(obj)
    m.objects.pop(obj)
    return {"deleted": obj}
