"""Booleans, fillet/chamfer (constant, variable, smooth), shell/thicken/offset face, direct face edits
(delete+heal, remove/refillet blends), split / imprint, tags."""
from __future__ import annotations

import math

from build123d import Compound, Edge, Face, Kind, Part, Plane, Shape, ShapeList, Solid, Vector, Wire, chamfer, \
    extrude, offset, thicken as _thicken

from cadkit.ops import CadOpError, safe_boolean, safe_chamfer, safe_fillet
from .core import ToolError, describe, op, resolve, vec
from .geom import _one_face, _wire, get_plane


def _solid(m, name):
    return m.get(name, ("solid",)).shape


def _part(s):
    return s if isinstance(s, Part) else Part(s.wrapped) if hasattr(s, "wrapped") else s


def _cast_solid(occ):
    s = Shape.cast(occ)
    sols = s.solids()
    if len(sols) == 1:
        return sols[0]
    return Compound(list(sols)) if sols else s


def _list(items):
    try:
        from OCP.collections import List_TopoDS_Shape as L
    except ImportError:
        from OCP.TopTools import TopTools_ListOfShape as L
    lst = L()
    for s in items:
        lst.Append(s.wrapped)
    return lst


# ------------------------------------------------------------------ booleans (spec 1 Booleans, 5.1)
@op("boolean", "spec 1 Booleans: Union/Difference/Intersect (keepTools); fallback fuzzy -> Manifold (cadkit.ops)")
def boolean(m, name, kind, target, tools, keep_tools=False):
    """kind union|cut|intersect. target body is replaced (or result goes to `name` if name != auto and
    keep target via name). tools = list of body names; removed unless keep_tools."""
    k = {"union": "fuse", "cut": "cut", "intersect": "common", "fuse": "fuse", "common": "common"}.get(kind)
    if k is None:
        raise ToolError(f"bad kind '{kind}'", "union|cut|intersect")
    tools = [tools] if isinstance(tools, str) else list(tools)
    a = _solid(m, target)
    ts = [_solid(m, t) for t in tools]
    try:
        res = safe_boolean(k, a, ts if len(ts) > 1 else ts[0], label=f"{kind}:{target}")
    except CadOpError as e:
        raise ToolError(str(e), "move tool off coplanar faces by ~1e-4 or split the tool list") from e
    out = target if name.startswith("boolean") else name
    m.put(out, "solid", res, **m.get(target).meta)
    if not keep_tools:
        for t in tools:
            if t != out:
                m.objects.pop(t, None)
    return {"name": out, "volume": round(res.volume, 9), "faces": len(res.faces())}


# ------------------------------------------------------------------ fillet / chamfer (spec 1 Fillet/chamfer, 5.2)
@op("fillet", "spec 1 Fillet: constant radius, shape round|smooth (OCCT polynomial ~G2 approx)|quasi_angular; "
              "retry + max-radius hint (cadkit.ops.safe_fillet)", out=False)
def fillet_op(m, body, edges, radius, shape="round", min_frac=0.15):
    """Fillet edges (ref) of body. On failure bisects to max feasible radius; applies it if >= min_frac*radius,
    else error data.max_feasible."""
    s = _solid(m, body)
    es = _edges(m, body, edges)
    if shape == "round":
        try:
            res = safe_fillet(s, es, radius, min_frac=min_frac, label=body)
        except CadOpError as e:
            raise ToolError(str(e), "lower radius or split edges", {"max_feasible": _maxr(str(e))}) from e
    else:
        res = _occ_fillet_retry(s, es, lambda mk, e, f: mk.Add(radius * f, e.wrapped), shape, radius, min_frac)
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "edges": len(es), "faces": len(res.faces())}


def _maxr(msg):
    import re
    g = re.search(r"max feasible radius ~([0-9.eE+-]+)", msg)
    return float(g.group(1)) if g else None


def _edges(m, body, ref):
    if isinstance(ref, dict) and "obj" not in ref:
        ref = {"obj": body, "edges": ref}
    es = resolve(m, ref, "edges")
    es = ShapeList(es if isinstance(es, (list, ShapeList)) else es.edges())
    if not es:
        raise ToolError(f"edge ref {ref!r} matched nothing", "use the select tool to inspect")
    return es


def _occ_fillet_retry(s, es, add, shape, nominal, min_frac=0.15):
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
    from OCP.ChFi3d import ChFi3d_FilletShape
    fs = {"round": ChFi3d_FilletShape.ChFi3d_Rational, "smooth": ChFi3d_FilletShape.ChFi3d_Polynomial,
          "quasi_angular": ChFi3d_FilletShape.ChFi3d_QuasiAngular}.get(shape)
    if fs is None:
        raise ToolError(f"bad fillet shape '{shape}'", "round|smooth|quasi_angular")

    def run(f):
        try:
            mk = BRepFilletAPI_MakeFillet(s.wrapped, fs)
            for e in es:
                add(mk, e, f)
            mk.Build()
            if not mk.IsDone():
                return None
            r = _cast_solid(mk.Shape())
            return r if r.is_valid and r.volume > 0 else None
        except Exception:
            return None
    r = run(1.0)
    if r is not None:
        return r
    lo, hi, best = 0.0, 1.0, None
    for _ in range(7):
        mid = (lo + hi) / 2
        rr = run(mid)
        lo, hi, best = (mid, hi, rr) if rr is not None else (lo, mid, best)
    if best is not None and lo >= min_frac:
        return best
    raise ToolError(f"fillet failed; max feasible scale ~{lo:.3f} of requested", "lower radii",
                    {"max_feasible": round(nominal * lo, 6)})


@op("variable_fillet", "spec 1 Fillet: variable radius (points along the edge, each with its own radius)",
    out=False)
def variable_fillet(m, body, edges, radii, shape="round"):
    """radii = [[t, r], ...] with t in 0..1 along each edge (>=2 points), or [r_start, r_end]."""
    try:
        from OCP.collections import Array1_gp_Pnt2d as TColgp_Array1OfPnt2d
    except ImportError:
        from OCP.TColgp import TColgp_Array1OfPnt2d
    from OCP.gp import gp_Pnt2d
    s = _solid(m, body)
    es = _edges(m, body, edges)
    pts = radii if isinstance(radii[0], (list, tuple)) else [[0, radii[0]], [1, radii[1]]]

    def add(mk, e, f):
        u0, u1 = e.param_at(0), e.param_at(1)
        arr = TColgp_Array1OfPnt2d(1, len(pts))
        for i, (t, r) in enumerate(pts, 1):
            arr.SetValue(i, gp_Pnt2d(u0 + t * (u1 - u0), r * f))
        mk.Add(e.wrapped)
        mk.SetRadius(arr, mk.NbContours(), 1)
    res = _occ_fillet_retry(s, es, add, shape, max(r for _, r in pts))
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "edges": len(es)}


@op("chamfer", "spec 1 Fillet/chamfer: chamfer by distance, 2 distances, or distance+angle", out=False)
def chamfer_op(m, body, edges, distance, distance2=None, angle=None):
    s = _solid(m, body)
    es = _edges(m, body, edges)
    if distance2 is None and angle is None:
        try:
            res = safe_chamfer(s, es, distance, label=body)
        except CadOpError as e:
            raise ToolError(str(e), "lower distance", {"max_feasible": _maxr(str(e))}) from e
    else:
        ref = es[0].topo_parent.faces().filter_by(lambda f: any(f_e.is_same(es[0]) for f_e in f.edges()))[0] \
            if es[0].topo_parent else None
        res = chamfer(es, distance, length2=distance2, angle=angle, reference=ref)
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "edges": len(es)}


# ------------------------------------------------------------------ shell / thicken / offset (spec 1 Shell, 5.8)
@op("shell", "spec 1 Shell/hollow: faces to remove, thickness, inward/outward; robust fallbacks (cadkit.surf."
             "robust_shell: offset arc/intersection, MakeThickSolid joins/tol, offset+cut, re-loft sections, "
             "Manifold erosion)", out=False)
def shell(m, body, thickness, open_faces=None, outward=False, strategy=None):
    """Hollow body to wall `thickness`, removing open_faces (ref). strategy = force one of
    arc|intersection|thick_arc|thick_intersection|thick_tol|offset_cut|sections|manifold (default: try in order,
    validated). Result info.method says which one worked."""
    from cadkit.surf import robust_shell
    from cadkit.ops import LOG
    s = _solid(m, body)
    faces = list(resolve(m, open_faces, "faces")) if open_faces else []
    try:
        res = robust_shell(s, thickness, faces, outward, sections=m.get(body).meta.get("_sections"),
                           strategy=strategy, label=body)
    except CadOpError as e:
        raise ToolError(str(e), "thickness < smallest fillet radius; shell before filleting") from e
    meta = {k: v for k, v in m.get(body).meta.items() if k != "_sections"}
    m.put(body, "solid", res, **meta)
    return {"name": body, "volume": round(res.volume, 9), "method": LOG[-1].get("method")}

@op("thicken", "spec 1 Thicken sheet -> solid (thickness1/2)")
def thicken_op(m, name, face, thickness, both=False):
    f = _one_face(m, face)
    m.put(name, "solid", _thicken(f, thickness, both=both))
    return {"name": name}


@op("offset_face", "spec 1 Offset face (push/pull, neighbours adapt) / Direct edit Move face; spec 5.3", out=False)
def offset_face(m, body, faces, distance):
    """Push (+) / pull (-) faces along their normals; neighbours extend/trim (OCCT BRepOffset per-face offset).
    Fallback for planar faces: extrude-face union/cut."""
    s = _solid(m, body)
    fs = list(resolve(m, {"obj": body, "faces": faces} if "obj" not in faces else faces, "faces"))
    if not fs:
        raise ToolError("face ref matched nothing")
    from cadkit.surf import robust_offset_face
    try:
        res, method = robust_offset_face(s, fs, distance, label=body)
    except CadOpError as e:
        raise ToolError(str(e), "smaller distance, or offset before filleting the neighbours") from e
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "method": method, "volume": round(res.volume, 9)}

def _per_face_offset(s, fs, d):
    try:
        from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin
        from OCP.GeomAbs import GeomAbs_Intersection
        mk = BRepOffset_MakeOffset()
        mk.Initialize(s.wrapped, 0.0, 1e-6, BRepOffset_Skin, True, False, GeomAbs_Intersection, False, False)
        for f in fs:
            mk.SetOffsetOnFace(f.wrapped, d)
        mk.MakeOffsetShape()
        if not mk.IsDone():
            return None
        r = _cast_solid(mk.Shape())
        dv = r.volume - s.volume
        if not r.is_valid or r.volume <= 0 or (d > 0) != (dv > 0) or abs(dv) < 1e-15:
            return None
        return r
    except Exception:
        return None


# ------------------------------------------------------------------ direct edits (spec 1 Direct face editing)
def _defeature(s, faces):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Defeaturing
    d = BRepAlgoAPI_Defeaturing()
    d.SetShape(s.wrapped)
    for f in faces:
        d.AddFaceToRemove(f.wrapped)
    d.SetRunParallel(True)
    d.Build()
    if not d.IsDone():
        raise ToolError("delete face / heal failed", "remove a smaller connected set (whole blend chain, whole boss)")
    r = _cast_solid(d.Shape())
    if not r.is_valid:
        raise ToolError("healed body invalid", "the neighbours cannot extend to close the gap; delete more faces")
    return r


@op("delete_face", "spec 1 Direct edit: delete face (heal) - neighbours extend to close", out=False)
def delete_face(m, body, faces):
    s = _solid(m, body)
    fs = list(resolve(m, {"obj": body, "faces": faces} if "obj" not in faces else faces, "faces"))
    res = _defeature(s, fs)
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "removed": len(fs), "faces": len(res.faces())}


def _blend_faces(m, body, faces, max_radius):
    if faces:
        return list(resolve(m, {"obj": body, "faces": faces} if "obj" not in faces else faces, "faces"))
    out = []
    for f in _solid(m, body).faces():
        g = f.geom_type.name
        if g in ("CYLINDER", "TORUS"):
            try:
                r = f.radius if g == "CYLINDER" else f.minor_radius
            except Exception:
                r = None
            if r is not None and r <= max_radius:
                out.append(f)
    return out


@op("remove_fillets", "spec 1 Fillet: remove fillets (detect + delete blends)", out=False)
def remove_fillets(m, body, faces=None, max_radius=0.01):
    """Delete blend faces and heal back to sharp edges. faces = ref, or auto (cylinder/torus faces with
    radius <= max_radius)."""
    fs = _blend_faces(m, body, faces, max_radius)
    if not fs:
        raise ToolError("no blend faces found", "pass faces ref or raise max_radius")
    res = _defeature(_solid(m, body), fs)
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "removed": len(fs)}


@op("refillet", "spec 1 Fillet: refillet an existing blend with a new radius (remove + re-apply); "
                "spec 5.2/2.5 re-fillet after edit", out=False)
def refillet(m, body, radius, faces=None, max_radius=0.01):
    s0 = _solid(m, body)
    fs = _blend_faces(m, body, faces, max_radius)
    if not fs:
        raise ToolError("no blend faces found")
    boxes = [f.bounding_box() for f in fs]
    old = [e.center() for e in s0.edges()]
    s1 = _defeature(s0, fs)
    pad = max(radius, max_radius) * 0.5 + 1e-6

    def inside(c):
        return any(all(lo - pad <= v <= hi + pad for v, lo, hi in zip(tuple(c), tuple(b.min), tuple(b.max)))
                   for b in boxes)
    new = [e for e in s1.edges() if inside(e.center()) and min((e.center() - o).length for o in old) > 1e-6]
    if not new:
        raise ToolError("could not find the healed sharp edges", "fillet them explicitly with a ref")
    try:
        res = safe_fillet(s1, new, radius, label=f"refillet:{body}")
    except CadOpError as e:
        raise ToolError(str(e), "lower radius", {"max_feasible": _maxr(str(e))}) from e
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "edges": len(new)}


# ------------------------------------------------------------------ split / imprint (spec 1 Cut/split, imprint)
def _splitter(shape, tools):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
    sp = BRepAlgoAPI_Splitter()
    sp.SetArguments(_list([shape]))
    sp.SetTools(_list(tools))
    sp.SetRunParallel(True)
    sp.Build()
    if not sp.IsDone():
        raise ToolError("split/imprint failed", "tool must cross the body; nudge off coplanar faces")
    return Shape.cast(sp.Shape())


def _sheet_from_curve(m, curve, cplane, depth):
    w = _wire(m, curve)
    pl = get_plane(m, cplane)
    n = pl.z_dir
    w0 = w.moved(_loc(-n * depth))
    from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCP.gp import gp_Vec
    v = n * (2 * depth)
    return Shape.cast(BRepPrimAPI_MakePrism(w0.wrapped, gp_Vec(v.X, v.Y, v.Z)).Shape())


def _loc(v):
    from build123d import Location
    return Location(v)


@op("split", "spec 1 Cut or split by curve, face or plane (mode split vs cut away)", out=False)
def split_op(m, body, plane=None, curve=None, cplane=None, keep="both", prefix=None):
    """Split body by a plane ({origin, normal} / cplane name) or by a curve extruded along cplane normal.
    keep both -> <prefix>_1.._N (sorted along the plane normal); 'above'/'below' -> replaces body."""
    s = _solid(m, body)
    diag = s.bounding_box().diagonal
    if curve is not None:
        tool = _sheet_from_curve(m, curve, cplane, diag)
        nrm = get_plane(m, cplane).z_dir
    else:
        pl = get_plane(m, plane if plane is not None else cplane)
        tool = Face.make_rect(diag * 3, diag * 3, pl)
        nrm = pl.z_dir
    res = _splitter(s, [tool])
    sols = sorted(res.solids(), key=lambda x: x.center().dot(nrm))
    if len(sols) < 2:
        raise ToolError("split produced 1 piece", "the plane/curve must cross the body")
    if keep in ("above", "below"):
        if curve is not None:
            raise ToolError("keep above/below only for plane splits")
        pick = sols[-1] if keep == "above" else sols[0]
        m.put(body, "solid", pick, **m.get(body).meta)
        return {"name": body}
    prefix = prefix or body
    names = []
    for i, x in enumerate(sols, 1):
        names.append(m.put(f"{prefix}_{i}", "solid", x))
    if prefix != body:
        m.objects.pop(body, None)
    else:
        m.objects.pop(body, None)
    return {"pieces": names}


@op("imprint", "spec 1 Imprint curves on faces (splits faces, solid unchanged); spec 5.5 imprint panel lines",
    out=False)
def imprint(m, body, curves, direction="-z"):
    """Project curves along direction onto body and split its faces with them (panel lines). Volume unchanged."""
    s = _solid(m, body)
    tools = []
    for c in curves:
        w = _wire(m, c)
        res = w.project_to_shape(s, vec(direction))
        if not res:
            raise ToolError(f"curve {c!r} misses the body along {direction}")
        tools += [e for e in _nearest(res, w, vec(direction)).edges()]
    out = _splitter(s, tools)
    sols = out.solids()
    if len(sols) != 1:
        raise ToolError(f"imprint gave {len(sols)} solids", "curves must lie inside faces")
    res = sols[0]
    m.put(body, "solid", res, **m.get(body).meta)
    return {"name": body, "faces_before": len(s.faces()), "faces": len(res.faces())}


def _nearest(res, w, d):
    """project_to_shape returns hits on every face crossed; keep the one first met along d."""
    c = w.center()
    return min(res, key=lambda r: (r.center() - c).dot(d))


# ------------------------------------------------------------------ tags (spec 5.9 stable geometric references)
@op("tag", "spec 3 / 5.9: stable references re-resolved from geometry (named semantic query)", out=False)
def tag_op(m, tag, ref):
    """Store a named ref spec; later refs use {"tag": name} or filter {"tag": name}."""
    items = resolve(m, ref)
    m.tags[tag] = ref
    return {"tag": tag, **(describe(items) if isinstance(items, (list, ShapeList)) else {"count": 1})}
