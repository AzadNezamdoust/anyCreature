"""Primitives, curves/sketch, regions, cplanes.  Provenance per op in @op(spec=...)."""
from __future__ import annotations

import math

from build123d import (Box, Cone, Cylinder, Edge, Face, Plane, Pos, Sphere, Torus, Vector, Wire, Location, Rot,
                       ShapeList, extrude, Compound)

from .core import ToolError, op, resolve, vec

_NAMED = {"XY": Plane.XY, "XZ": Plane.XZ, "YZ": Plane.YZ, "ZX": Plane.ZX, "YX": Plane.YX, "ZY": Plane.ZY}


def get_plane(model, p):
    """None|'XY'|'XZ'|'YZ'|cplane name|{origin, normal, x_dir}."""
    if p is None:
        return Plane.XY
    if isinstance(p, str):
        if p in _NAMED:
            return _NAMED[p]
        if p in model.cplanes:
            return model.cplanes[p]
        raise ToolError(f"no cplane '{p}'", f"cplanes: {sorted(model.cplanes)} or XY/XZ/YZ")
    o = Vector(*p.get("origin", (0, 0, 0)))
    n = vec(p.get("normal", "z"))
    xd = p.get("x_dir")
    return Plane(o, x_dir=vec(xd) if xd else None, z_dir=n)


def _place(model, shape, at, pl):
    pl = get_plane(model, pl)
    return pl.location * Pos(*(at or (0, 0, 0))) * shape


# ------------------------------------------------------------------ primitives (spec 1 Primitives, 5 must-have 3)
@op("box", "spec 1 Primitives: Box (width/length/height, base plane)")
def box(m, name, size, at=None, plane=None, align="center"):
    """Box size [x,y,z] at [x,y,z] on plane. align 'center' or 'min' (corner at `at`) or 'base' (z from 0)."""
    from build123d import Align
    al = {"center": (Align.CENTER,) * 3, "min": (Align.MIN,) * 3,
          "base": (Align.CENTER, Align.CENTER, Align.MIN)}[align]
    m.put(name, "solid", _place(m, Box(*size, align=al), at, plane))
    return {"name": name}


@op("cylinder", "spec 1 Primitives: Cylinder (radius, height)")
def cylinder(m, name, radius, height, at=None, plane=None):
    """Cylinder centred at `at`, axis = plane normal."""
    m.put(name, "solid", _place(m, Cylinder(radius, height), at, plane))
    return {"name": name}


@op("cone", "spec 1 Primitives: Cone (radius1/radius2, height)")
def cone(m, name, radius1, radius2, height, at=None, plane=None):
    m.put(name, "solid", _place(m, Cone(radius1, radius2, height), at, plane))
    return {"name": name}


@op("sphere", "spec 1 Primitives: Sphere (center, radius)")
def sphere(m, name, radius, at=None):
    m.put(name, "solid", Pos(*(at or (0, 0, 0))) * Sphere(radius))
    return {"name": name}


@op("torus", "spec 1 Primitives (torus: generic revolve primitive; not in spec table)")
def torus(m, name, major, minor, at=None, plane=None):
    m.put(name, "solid", _place(m, Torus(major, minor), at, plane))
    return {"name": name}


@op("prism", "spec 1 Primitives / 3 Region extrude: prism from a region")
def prism(m, name, region, height):
    """Solid from a region (planar face) along its normal."""
    f = _one_face(m, region)
    m.put(name, "solid", extrude(f, height))
    return {"name": name}


# ------------------------------------------------------------------ curves (spec 1 Curves/sketch, 5.5)
def _pts(model, pts, pl):
    pl = get_plane(model, pl)
    out = []
    for p in pts:
        p = list(p) + [0] * (3 - len(p))
        out.append(pl.from_local_coords(Vector(*p)))
    return out


@op("line", "spec 1 Curves: Polyline/line")
def line(m, name, points, plane=None, closed=False):
    """Polyline through points (2D on plane or 3D). closed -> wire closed back to first point."""
    P = _pts(m, points, plane)
    if closed:
        P = P + [P[0]]
    edges = [Edge.make_line(a, b) for a, b in zip(P, P[1:])]
    m.put(name, "curve", Wire(edges))
    return {"name": name, "edges": len(edges)}


@op("arc", "spec 1 Curves: Arc (3-pt)")
def arc(m, name, start, mid, end, plane=None):
    a, b, c = _pts(m, [start, mid, end], plane)
    m.put(name, "curve", Wire([Edge.make_three_point_arc(a, b, c)]))
    return {"name": name}


@op("spline", "spec 1 Curves: Curve (NURBS/cubic, CurveFactory)")
def spline(m, name, points, plane=None, closed=False, tangents=None):
    """Interpolating B-spline through points; optional end tangents [[t0],[t1]]."""
    P = _pts(m, points, plane)
    tg = [vec(t) for t in tangents] if tangents else None
    m.put(name, "curve", Wire([Edge.make_spline(P, tangents=tg, periodic=closed)]))
    return {"name": name}


@op("circle", "spec 1 Curves: Circle (center)")
def circle(m, name, radius, center=None, plane=None):
    pl = get_plane(m, plane)
    c = pl_point(pl, center)
    pl2 = Plane(c, x_dir=pl.x_dir, z_dir=pl.z_dir)
    m.put(name, "curve", Wire([Edge.make_circle(radius, pl2)]))
    return {"name": name}


def pl_point(pl, p):
    p = list(p or (0, 0)) + [0] * (3 - len(p or (0, 0)))
    return pl.from_local_coords(Vector(*p))


@op("rectangle", "spec 1 Primitives: Rectangle (corner/center)")
def rectangle(m, name, width, height, center=None, plane=None, corner_radius=0.0):
    cx, cy = (center or (0, 0))[:2]
    w, h = width / 2, height / 2
    pts = [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)]
    wire = Wire.make_polygon(_pts(m, pts, plane), close=True)
    if corner_radius > 0:
        wire = wire.fillet_2d(corner_radius, wire.vertices())
    m.put(name, "curve", wire)
    return {"name": name}


@op("polygon", "spec 1 Primitives: Polygon (sides)")
def polygon(m, name, sides, radius, center=None, plane=None, rotation=0.0):
    cx, cy = (center or (0, 0))[:2]
    a0 = math.radians(rotation)
    pts = [(cx + radius * math.cos(a0 + 2 * math.pi * i / sides), cy + radius * math.sin(a0 + 2 * math.pi * i / sides))
           for i in range(sides)]
    m.put(name, "curve", Wire.make_polygon(_pts(m, pts, plane), close=True))
    return {"name": name}


@op("offset_curve", "spec 1 Curves edit: Offset planar curve (distance, side)")
def offset_curve(m, name, curve, distance, kind="arc"):
    """Offset a planar wire by distance (+ out / - in for closed). kind arc|intersection."""
    from build123d import Kind
    w = _wire(m, curve)
    m.put(name, "curve", w.offset_2d(distance, kind=Kind.ARC if kind == "arc" else Kind.INTERSECTION))
    return {"name": name}


@op("fillet_curve", "spec 1 Curves edit: Fillet a curve vertex (radius)")
def fillet_curve(m, name, curve, radius, near=None):
    """Round planar wire corners (all, or the vertex nearest each point in `near`)."""
    w = _wire(m, curve)
    vs = w.vertices()
    if near:
        vs = [min(vs, key=lambda v: (Vector(v) - Vector(*p)).length) for p in near]
    try:
        m.put(name, "curve", w.fillet_2d(radius, vs))
    except Exception as e:
        short = min(e_.length for e_ in w.edges())
        raise ToolError(f"fillet_curve r={radius} failed: {e}", f"shortest segment {short:.4g}: keep r < {short / 2:.4g}")
    return {"name": name}


def _wire(m, ref):
    s = resolve(m, ref)
    if isinstance(s, Wire):
        return s
    if isinstance(s, Edge):
        return Wire([s])
    if isinstance(s, (list, ShapeList)):
        return Wire(list(s))
    raise ToolError(f"{ref!r} is not a curve")


def _one_face(m, ref):
    s = resolve(m, ref)
    if isinstance(s, (list, ShapeList)):
        if len(s) != 1:
            raise ToolError(f"ref {ref!r} gave {len(s)} faces, need 1")
        s = s[0]
    if isinstance(s, Face):
        return s
    fs = s.faces()
    if len(fs) == 1:
        return fs[0]
    raise ToolError(f"{ref!r} is not a single face/region")


@op("regions", "spec 1 Curves: Regions (closed planar curves split automatically into fillable faces, no solver)",
    out=False)
def regions(m, curves, prefix="region"):
    """All closed planar curves -> arrangement of faces (overlaps split, nested curves make holes/islands).
    Creates <prefix>1..N region objects, sorted by area desc. Returns their names, areas, centres."""
    from OCP.BOPAlgo import BOPAlgo_Builder
    if len(curves) == 1:
        w = _wire(m, curves[0])
        if not w.is_closed:
            raise ToolError(f"curve {curves[0]!r} is open", "close it (line closed=true) or join curves first")
        m.put(f"{prefix}1", "region", Face(w))
        f = m.objects[f"{prefix}1"].shape
        return {"regions": [{"name": f"{prefix}1", "area": round(f.area, 8)}]}
    faces = []
    for c in curves:
        w = _wire(m, c)
        if not w.is_closed:
            raise ToolError(f"curve {c!r} is open", "close it (line closed=true) or join curves first")
        faces.append(Face(w))
    b = BOPAlgo_Builder()
    for f in faces:
        b.AddArgument(f.wrapped)
    b.Perform()
    if b.HasErrors():
        raise ToolError("region split failed", "curves must be coplanar")
    frags = sorted(_faces_of(b.Shape()), key=lambda f: -f.area)
    names = []
    for i, f in enumerate(frags, 1):
        nm = f"{prefix}{i}"
        m.put(nm, "region", f)
        names.append({"name": nm, "area": round(f.area, 8), "center": [round(v, 5) for v in tuple(f.center())]})
    return {"regions": names}


def _faces_of(occ):
    from build123d import Shape
    return Shape.cast(occ).faces()


@op("project_curve", "spec 1 Curves edit: Project curve onto body (ProjectCurveBody)")
def project_curve(m, name, curve, body, direction="-z"):
    """Project a curve onto a body along direction -> curve object (edges on the body's faces)."""
    w = _wire(m, curve)
    tgt = resolve(m, body)
    res = w.project_to_shape(tgt, vec(direction))
    if not res:
        raise ToolError("projection hit nothing", "check direction points from the curve towards the body")
    from .edit import _nearest
    m.put(name, "curve", _nearest(res, w, vec(direction)), source=str(curve))
    return {"name": name, "pieces": len(res)}


# ------------------------------------------------------------------ cplanes (spec 1 Construction planes)
@op("cplane", "spec 1 Construction planes: custom cplane from face / 3 points / origin+normal", out=False)
def cplane(m, cname, face=None, points=None, origin=None, normal=None, x_dir=None, offset=0.0):
    """Named construction plane. face=ref (planar face: origin=centre, normal=face normal) | points=[p0,p1,p2] |
    origin+normal(+x_dir). offset moves it along its normal."""
    if face is not None:
        f = _one_face(m, face)
        c = f.center()
        pl = Plane(c, x_dir=None, z_dir=f.normal_at(c))
    elif points:
        a, b, c = (Vector(*p) for p in points)
        pl = Plane(a, x_dir=(b - a), z_dir=(b - a).cross(c - a))
    else:
        pl = Plane(Vector(*(origin or (0, 0, 0))), x_dir=vec(x_dir) if x_dir else None, z_dir=vec(normal or "z"))
    if offset:
        pl = pl.offset(offset)
    m.cplanes[cname] = pl
    return {"cplane": cname, "origin": [round(v, 5) for v in tuple(pl.origin)],
            "normal": [round(v, 5) for v in tuple(pl.z_dir)]}
