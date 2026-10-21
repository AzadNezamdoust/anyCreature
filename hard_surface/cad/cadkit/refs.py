"""Semantic refs: tags re-resolved on every re-run (never raw indices) + selector helpers.

tag("muzzle_face", face_or_list)  -> recorded in state.json "tags" with count/centres/area
"""
from __future__ import annotations

from build123d import Axis, Vector, GeomType

TAGS: dict[str, list] = {}


def tag(name, shapes):
    lst = [shapes] if hasattr(shapes, "wrapped") else list(shapes)
    TAGS[name] = lst
    return shapes


def tagged(name):
    if name not in TAGS:
        raise KeyError(f"no tag '{name}'. Known: {sorted(TAGS)}")
    return TAGS[name]


def describe_tags():
    out = {}
    for k, lst in TAGS.items():
        items = []
        for s in lst[:8]:
            c = s.center()
            d = {"type": type(s).__name__, "center": [round(c.X, 5), round(c.Y, 5), round(c.Z, 5)]}
            if hasattr(s, "area") and type(s).__name__ == "Face":
                d["area"] = round(s.area, 7)
            if type(s).__name__ == "Edge":
                d["length"] = round(s.length, 6)
            items.append(d)
        out[k] = {"count": len(lst), "items": items}
    return out


# ---- selectors (all take a Shape, return ShapeList) -------------------------------------------------------------
_AX = {"x": Axis.X, "y": Axis.Y, "z": Axis.Z}


def face_at(shape, axis="z", side="max"):
    """Extreme face along axis ('max' top / 'min' bottom)."""
    fs = shape.faces().sort_by(_AX[axis])
    return fs[-1] if side == "max" else fs[0]


def edges_of_face(shape, axis="z", side="max"):
    return face_at(shape, axis, side).edges()


def edges_parallel(shape, axis="z"):
    return shape.edges().filter_by(_AX[axis])


def edges_on_plane(shape, axis="z", value=None, side="max", tol=1e-4):
    """Edges lying at axis==value (or at the max/min extent)."""
    es = shape.edges()
    if value is None:
        bb = shape.bounding_box()
        value = getattr(bb.max if side == "max" else bb.min, axis.upper())
    i = "xyz".index(axis)
    return es.filter_by(lambda e: abs(tuple(e.center())[i] - value) < tol and
                        abs(tuple(e.bounding_box().max)[i] - tuple(e.bounding_box().min)[i]) < tol)


def edges_near(shape, point, radius):
    p = Vector(*point)
    return shape.edges().filter_by(lambda e: (e.center() - p).length <= radius)


def edges_longer(shape, length):
    return shape.edges().filter_by(lambda e: e.length >= length)


def edges_circular(shape):
    return shape.edges().filter_by(GeomType.CIRCLE)


def new_edges(result, *inputs, tol=1e-4):
    """Edges of `result` that did not exist (same midpoint) in any of `inputs` = the intersection curves a
    fuse/cut created. The thing you want to blend after a boolean; seam/spine edges of sweeps are excluded."""
    from build123d import Vector
    old = []
    for s in inputs:
        for e in s.edges():
            old.append(e)

    def is_old(e):
        c = e.center()
        p = e.position_at(0.37)
        for o in old:
            if (o.center() - c).length < tol * 10 + 1e-9 or o.distance_to(p) < tol:
                return True
        return False
    return [e for e in result.edges() if not is_old(e)]
