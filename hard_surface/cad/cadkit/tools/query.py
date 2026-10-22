"""Read-only queries for an LLM driver (no journal entry): measure, curvature, draft analysis, deviation to a
reference, silhouette IoU vs a reference image, suggest_refs (stable ref strings near a point), explain_failure,
state diff.  Spec section 1 Utility/analysis (measure distance/radius, section/continuity analysis) + section 3
(geometry-based refs)."""
from __future__ import annotations

import inspect as _pyinspect
import math

import numpy as np
from build123d import Compound, GeomType, Shape, ShapeList, Vector

from .core import OPS, ToolError, _desc, resolve, vec


def _r(v, n=6):
    return [round(float(x), n) for x in (tuple(v) if not isinstance(v, (list, tuple)) else v)]


def _shape(m, ref):
    s = resolve(m, ref)
    if isinstance(s, (list, ShapeList)):
        if not s:
            raise ToolError(f"ref {ref!r} matched nothing", "use cad_suggest_refs")
        return s[0] if len(s) == 1 else Compound(list(s))
    return s


# ------------------------------------------------------------------ measure / curvature
def _props(s):
    d = _desc(s) if type(s).__name__ in ("Face", "Edge", "Vertex") else {"type": type(s).__name__}
    t = type(s).__name__
    try:
        if t == "Edge" and s.geom_type in (GeomType.CIRCLE,):
            d["radius"] = round(s.radius, 6)
        if t == "Face":
            if s.geom_type in (GeomType.CYLINDER, GeomType.SPHERE):
                d["radius"] = round(s.radius, 6)
        if t not in ("Face", "Edge", "Vertex", "Wire") and s.volume > 0:
            bb = s.bounding_box()
            d.update(volume=round(s.volume, 9), area=round(s.area, 9), bbox=[_r(bb.min), _r(bb.max)],
                     size=_r(bb.size), center_of_mass=_r(s.center()))
    except Exception:
        pass
    return d


def _dir_of(s):
    t = type(s).__name__
    if t == "Face" and s.geom_type == GeomType.PLANE:
        return s.normal_at(s.center()), "normal"
    if t == "Edge" and s.geom_type == GeomType.LINE:
        return (s.position_at(1) - s.position_at(0)).normalized(), "direction"
    return None, None


def measure(m, a, b=None):
    """a alone -> properties (length/area/volume/radius/normal). a+b -> min distance + closest points, and the
    angle when both are planar faces or straight edges."""
    sa = _shape(m, a)
    if b is None:
        return {"a": _props(sa)}
    sb = _shape(m, b)
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    ex = BRepExtrema_DistShapeShape(sa.wrapped, sb.wrapped)
    ex.Perform()
    out = {"a": _props(sa), "b": _props(sb)}
    if ex.IsDone() and ex.NbSolution():
        pa, pb = ex.PointOnShape1(1), ex.PointOnShape2(1)
        out.update(distance=round(ex.Value(), 9), point_a=_r((pa.X(), pa.Y(), pa.Z())),
                   point_b=_r((pb.X(), pb.Y(), pb.Z())))
    da, ka = _dir_of(sa)
    db, kb = _dir_of(sb)
    if da is not None and db is not None:
        ang = math.degrees(math.acos(max(-1.0, min(1.0, da.dot(db)))))
        out["angle_deg"] = round(ang if (ka, kb) != ("normal", "direction") else abs(90 - ang), 4)
    return out


def curvature(m, face, point=None):
    """Principal curvatures (k1,k2, 1/m), radii and directions of a face at the surface point nearest `point`
    (default face centre)."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepLProp import BRepLProp_SLProps
    from OCP.ShapeAnalysis import ShapeAnalysis_Surface
    from OCP.gp import gp_Dir, gp_Pnt
    f = _shape(m, face)
    if type(f).__name__ != "Face":
        raise ToolError("curvature needs one face", "ref with faces filter + expect 1")
    p = Vector(*point) if point else f.center()
    uv = ShapeAnalysis_Surface(BRep_Tool.Surface_s(f.wrapped)).ValueOfUV(gp_Pnt(p.X, p.Y, p.Z), 1e-7)
    pr = BRepLProp_SLProps(BRepAdaptor_Surface(f.wrapped), uv.X(), uv.Y(), 2, 1e-7)
    if not pr.IsCurvatureDefined():
        return {"defined": False}
    k1, k2 = pr.MaxCurvature(), pr.MinCurvature()
    d1, d2 = gp_Dir(), gp_Dir()
    pr.CurvatureDirections(d1, d2)
    q = pr.Value()
    rad = lambda k: None if abs(k) < 1e-12 else round(1 / k, 6)  # noqa: E731
    return {"defined": True, "point": _r((q.X(), q.Y(), q.Z())), "k1": round(k1, 6), "k2": round(k2, 6),
            "r1": rad(k1), "r2": rad(k2), "mean": round(pr.MeanCurvature(), 6),
            "gaussian": round(pr.GaussianCurvature(), 6), "dir1": _r((d1.X(), d1.Y(), d1.Z()), 4),
            "dir2": _r((d2.X(), d2.Y(), d2.Z()), 4), "geom": f.geom_type.name.lower()}


# ------------------------------------------------------------------ draft analysis
def draft_analysis(m, body, pull="+z", min_draft=1.0, samples=3):
    """Per-face draft angle vs pull direction (moulding / machining check). draft = 90 - angle(normal, pull):
    +90 faces the pull, 0 vertical (no draft), <0 undercut-ish (faces away). Faces with |draft| < min_draft that
    are not ~perpendicular are 'insufficient'. Each face gets a near-ref to act on."""
    s = _shape(m, body)
    d = vec(pull).normalized()
    rows, counts = [], {"positive": 0, "negative": 0, "insufficient": 0, "vertical_needs_draft": 0}
    for f in s.faces():
        angs = []
        for u in np.linspace(0.15, 0.85, samples):
            for v in np.linspace(0.15, 0.85, samples):
                try:
                    n = f.normal_at(u, v)
                except Exception:
                    n = f.normal_at(f.center())
                angs.append(90 - math.degrees(math.acos(max(-1, min(1, n.dot(d))))))
        lo, hi = min(angs), max(angs)
        cls = "positive" if lo >= min_draft else "negative" if hi <= -min_draft else \
            "vertical_needs_draft" if abs(lo) < min_draft and abs(hi) < min_draft else "insufficient"
        counts[cls] += 1
        c = f.center()
        rows.append({"ref": {"obj": body, "faces": {"near": _r(c, 5)}} if isinstance(body, str) else None,
                     "geom": f.geom_type.name.lower(), "draft_min": round(lo, 3), "draft_max": round(hi, 3),
                     "class": cls, "area": round(f.area, 8)})
    bad = [r for r in rows if r["class"] in ("insufficient", "vertical_needs_draft")]
    return {"pull": _r(d, 4), "min_draft": min_draft, "counts": counts, "needs_draft": bad[:40],
            "faces": len(rows)}


# ------------------------------------------------------------------ deviation to reference
def _tess(shape, tol=1e-3):
    import trimesh
    bb = shape.bounding_box()
    v, t = shape.tessellate(max(tol, bb.diagonal * 1e-3))
    return trimesh.Trimesh(np.array([tuple(p) for p in v]), np.array(t), process=False)


def _mesh_of(m, ref):
    import trimesh
    if isinstance(ref, str) and ref.lower().endswith((".stl", ".obj", ".glb", ".gltf", ".ply", ".off")):
        mm = trimesh.load(ref, force="mesh")
        return mm
    return _tess(_shape(m, ref))


def _exact_dist(pts, mesh, n_dense, k=12):
    """Exact point -> mesh surface distance: KD-tree on dense samples picks candidate triangles, then exact
    point-triangle distance (trimesh.triangles.closest_point) on those."""
    from scipy.spatial import cKDTree
    import trimesh
    sp, fi = trimesh.sample.sample_surface(mesh, int(n_dense), seed=3)
    sp = np.vstack([sp, mesh.triangles_center])
    fi = np.concatenate([fi, np.arange(len(mesh.faces))])
    _, idx = cKDTree(sp).query(pts, k=min(k, len(sp)))
    cand = fi[idx]                                           # (n, k) triangle ids
    tri = mesh.triangles[cand.ravel()]
    q = np.repeat(pts, cand.shape[1], axis=0)
    cp = trimesh.triangles.closest_point(tri, q)
    d = np.linalg.norm(cp - q, axis=1).reshape(cand.shape)
    return d.min(axis=1)


def deviation(m, a, b, samples=20000, scale_b=1.0):
    """Surface deviation of object a vs reference b (object name/ref or a mesh file path). Samples a's surface,
    exact nearest distance to b's (tessellated) surface. Returns max/mean/rms/p95 (metres), worst point, and the
    symmetric hausdorff (b sampled vs a too)."""
    import trimesh
    ma, mb = _mesh_of(m, a), _mesh_of(m, b)
    if scale_b != 1.0:
        mb.apply_scale(scale_b)
    n = int(samples)
    pa, _ = trimesh.sample.sample_surface(ma, n, seed=1)
    pa = np.vstack([pa, ma.vertices])
    pb, _ = trimesh.sample.sample_surface(mb, n, seed=2)
    pb = np.vstack([pb, mb.vertices])
    da = _exact_dist(pa, mb, n * 2)
    db = _exact_dist(pb, ma, n * 2)
    w = int(np.argmax(da))
    return {"a_to_b": {"max": round(float(da.max()), 6), "mean": round(float(da.mean()), 6),
                       "rms": round(float(np.sqrt((da ** 2).mean())), 6), "p95": round(float(np.percentile(da, 95)), 6),
                       "worst_point": _r(pa[w], 5)},
            "b_to_a": {"max": round(float(db.max()), 6), "mean": round(float(db.mean()), 6)},
            "hausdorff": round(float(max(da.max(), db.max())), 6)}


# ------------------------------------------------------------------ silhouette IoU vs reference image
_VIEWS = {"front": (0, 2, 1), "back": (0, 2, -1), "side": (1, 2, 1), "right": (1, 2, 1), "left": (1, 2, -1),
          "top": (0, 1, 1), "bottom": (0, 1, -1)}


def _ref_mask(img, threshold=128):
    a = np.asarray(img)
    if a.ndim == 3 and a.shape[2] == 4 and a[..., 3].min() < 250:
        return a[..., 3] > 127
    g = a if a.ndim == 2 else a[..., :3].mean(axis=2)
    corners = np.concatenate([g[:4, :4].ravel(), g[-4:, -4:].ravel(), g[:4, -4:].ravel(), g[-4:, :4].ravel()])
    return g < threshold if corners.mean() >= threshold else g >= threshold


def _bbox(mask):
    ys, xs = np.nonzero(mask)
    return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else None


def compare_to_ref(m, image, view="front", names=None, m_per_px=None, origin_px=None, threshold=128,
                   out=None):
    """Silhouette IoU of the model (orthographic, view front=XZ / side=YZ / top=XY) vs a reference image.
    Known scale: m_per_px + origin_px = pixel [x, y] of world (0,0) -> absolute fit. Without scale: both
    silhouettes are bbox-normalised (shape-only IoU) and the implied scale is returned. out = optional diff png
    (red = model only, blue = ref only, white = both). Reference mask: alpha if present, else dark-on-light (or
    light-on-dark, from the corners)."""
    from PIL import Image, ImageDraw
    img = Image.open(image)
    ref = _ref_mask(img, threshold)
    H, W = ref.shape
    ix, iy, _ = _VIEWS[view]
    objs = names or [k for k, o in m.objects.items() if o.kind in ("solid", "sheet")]
    tris = []
    for k in objs:
        msh = _tess(m.get(k).shape)
        tris.append(msh.vertices[msh.faces][:, :, [ix, iy]])
    if not tris:
        raise ToolError("no solids to compare")
    P = np.concatenate(tris)
    flip = _VIEWS[view][2]
    P[..., 0] *= flip
    if m_per_px:
        ox, oy = origin_px or (W / 2, H / 2)
        X, Y = ox + P[..., 0] / m_per_px, oy - P[..., 1] / m_per_px
        mode = "absolute"
    else:
        rb = _bbox(ref)
        if rb is None:
            raise ToolError("reference image has no silhouette", "check threshold / background")
        lo, hi = P.reshape(-1, 2).min(0), P.reshape(-1, 2).max(0)
        sc = (rb[3] - rb[1]) / max(hi[1] - lo[1], 1e-12)
        X = rb[0] + (P[..., 0] - lo[0]) * sc + ((rb[2] - rb[0]) - (hi[0] - lo[0]) * sc) / 2
        Y = rb[3] - (P[..., 1] - lo[1]) * sc
        m_per_px = 1 / sc
        mode = "normalised (height-fit, centred)"
    can = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(can)
    for tx, ty in zip(X, Y):
        dr.polygon(list(zip(tx.tolist(), ty.tolist())), fill=255)
    mod = np.asarray(can) > 127
    inter, uni = (mod & ref).sum(), (mod | ref).sum()
    res = {"iou": round(float(inter / max(uni, 1)), 4), "mode": mode, "view": view,
           "m_per_px": round(float(m_per_px), 8), "model_px": int(mod.sum()), "ref_px": int(ref.sum()),
           "model_only_frac": round(float((mod & ~ref).sum() / max(uni, 1)), 4),
           "ref_only_frac": round(float((ref & ~mod).sum() / max(uni, 1)), 4)}
    mb, rb = _bbox(mod), _bbox(ref)
    if mb and rb:
        res["bbox_px"] = {"model": [int(v) for v in mb], "ref": [int(v) for v in rb]}
        res["size_ratio_model_over_ref"] = [round((mb[2] - mb[0]) / max(rb[2] - rb[0], 1), 4),
                                            round((mb[3] - mb[1]) / max(rb[3] - rb[1], 1), 4)]
    if out:
        rgb = np.zeros((H, W, 3), np.uint8)
        rgb[mod & ~ref] = (230, 40, 40)
        rgb[ref & ~mod] = (40, 90, 230)
        rgb[mod & ref] = (255, 255, 255)
        Image.fromarray(rgb).save(out)
        res["diff_png"] = out
    return res


# ------------------------------------------------------------------ suggest_refs
def _try(m, ref, target, kind):
    try:
        got = resolve(m, ref, kind)
        return len(got) == 1 and got[0].is_same(target)
    except Exception:
        return False


def suggest_refs(m, obj, near=None, kind="faces", n=6):
    """Entities of `obj` nearest `near` (default: all, by size) with ref specs VERIFIED to select exactly that one
    entity. 'stable' refs are semantic (normal / geom + pick extreme / of_faces) and survive edits that move
    things; the 'near' ref always works on the current revision."""
    s = m.get(obj).shape
    items = list(getattr(s, kind)())
    if near is not None:
        p = Vector(*near)
        items.sort(key=lambda x: (x.center() - p).length)
    elif kind == "faces":
        items.sort(key=lambda x: -x.area)
    elif kind == "edges":
        items.sort(key=lambda x: -x.length)
    out = []
    for it in items[:n]:
        c = it.center()
        cands = []
        g = it.geom_type.name.lower() if hasattr(it, "geom_type") else None
        if kind == "faces":
            if it.geom_type == GeomType.PLANE:
                nr = it.normal_at(c)
                ax = max(range(3), key=lambda i: abs(tuple(nr)[i]))
                if abs(tuple(nr)[ax]) > 0.9999:
                    cands.append({"normal": ("+" if tuple(nr)[ax] > 0 else "-") + "xyz"[ax]})
                    cands.append({"normal": ("+" if tuple(nr)[ax] > 0 else "-") + "xyz"[ax], "pick": "max" if
                                  tuple(nr)[ax] > 0 else "min", "axis": "xyz"[ax]})
                else:
                    cands.append({"normal": _r(nr, 4)})
            for ax in "xyz":
                cands += [{"geom": g, "pick": "max", "axis": ax}, {"geom": g, "pick": "min", "axis": ax}]
            cands += [{"geom": g, "pick": "largest"}, {"geom": g, "pick": "smallest"}]
        elif kind == "edges":
            if it.geom_type == GeomType.LINE:
                d = (it.position_at(1) - it.position_at(0)).normalized()
                ax = max(range(3), key=lambda i: abs(tuple(d)[i]))
                if abs(tuple(d)[ax]) > 0.9999:
                    for ax2 in "xyz":
                        if ax2 != "xyz"[ax]:
                            cands += [{"parallel": "xyz"[ax], "pick": pk, "axis": ax2} for pk in ("max", "min")]
            cands += [{"geom": g, "pick": "longest_hint", "_skip": True}]
            for ax in "xyz":
                cands += [{"geom": g, "pick": "max", "axis": ax}, {"geom": g, "pick": "min", "axis": ax}]
        stable = []
        for f in cands:
            if f.get("_skip"):
                continue
            f = {k: v for k, v in f.items() if v is not None}
            ref = {"obj": obj, kind: dict(f, expect=1)}
            if _try(m, {"obj": obj, kind: f}, it, kind) and ref not in stable:
                stable.append(ref)
            if len(stable) >= 3:
                break
        nearref = {"obj": obj, kind: {"near": _r(c, 5)}}
        out.append({**_desc(it), "distance": round((c - Vector(*near)).length, 6) if near is not None else None,
                    "stable_refs": stable, "near_ref": nearref})
    return {"obj": obj, "kind": kind, "count_total": len(list(getattr(s, kind)())), "candidates": out}


# ------------------------------------------------------------------ explain_failure
def _ref_like(v):
    return isinstance(v, dict) and ("obj" in v or "tag" in v)


def explain_failure(m, op, params):
    """Dry-run `op` with params on the current state (state restored after), and diagnose: unknown/missing/extra
    params, every ref param resolved (count + what it hit), op-specific checks (fillet: shortest adjacent edge,
    boolean: overlap volume, loft/sweep: closed profiles), the kernel error + hint, and what to try next."""
    if op not in OPS:
        import difflib
        return {"ok": False, "problem": f"unknown op '{op}'", "did_you_mean": difflib.get_close_matches(op, OPS, 3)}
    fn = OPS[op]["fn"]
    sig = _pyinspect.signature(fn)
    accepted = [p for p in list(sig.parameters)[1:]]
    required = [k for k, p in list(sig.parameters.items())[1:] if p.default is _pyinspect._empty and k != "name"]
    rep = {"op": op, "accepted_params": accepted, "missing": [k for k in required if k not in params],
           "unknown": [k for k in params if k not in accepted], "refs": {}, "checks": []}
    for k, v in params.items():
        vals = v if isinstance(v, list) else [v]
        for i, x in enumerate(vals):
            if _ref_like(x) or (isinstance(x, str) and (x in m.objects or x in m.tags)):
                key = k if not isinstance(v, list) else f"{k}[{i}]"
                try:
                    r = resolve(m, x)
                    lst = list(r) if isinstance(r, (list, ShapeList)) else [r]
                    rep["refs"][key] = {"count": len(lst), "items": [_desc(s) for s in lst[:4]]}
                    if not lst:
                        rep["checks"].append(f"{key} matched nothing -> loosen the filter (cad_suggest_refs)")
                except ToolError as e:
                    rep["refs"][key] = {"error": str(e), "hint": e.hint}
            elif isinstance(x, dict) and k in ("edges", "faces") and "body" in params:
                try:
                    lst = list(resolve(m, {"obj": params["body"], k: x}, k))
                    rep["refs"][k] = {"count": len(lst), "items": [_desc(s) for s in lst[:4]]}
                    if not lst:
                        rep["checks"].append(f"{k} filter matched nothing on {params['body']}")
                except ToolError as e:
                    rep["refs"][k] = {"error": str(e), "hint": e.hint}
    try:
        _op_checks(m, op, params, rep)
    except Exception as e:  # noqa
        rep["checks"].append(f"check error: {e}")
    before = m._take()
    try:
        info = fn(m, **({"name": "_explain_probe"} if OPS[op]["out"] and "name" not in params else {}), **params)
        rep.update(ok=True, would_succeed=True, info=info)
    except ToolError as e:
        rep.update(ok=False, error=str(e), hint=e.hint, data=e.data)
    except TypeError as e:
        rep.update(ok=False, error=f"bad params: {e}")
    except Exception as e:  # noqa
        from .core import kernel_hint
        rep.update(ok=False, error=f"{type(e).__name__}: {e}"[:400], hint=kernel_hint(op, e))
    finally:
        m._put(before)
    if rep["missing"]:
        rep["checks"].insert(0, f"missing required params: {rep['missing']}")
    if rep["unknown"]:
        rep["checks"].insert(0, f"unknown params (typo?): {rep['unknown']}")
    return rep


def _op_checks(m, op, p, rep):
    if op in ("fillet", "chamfer", "variable_fillet", "refillet", "push_pull") and "body" in p:
        s = m.get(p["body"]).shape
        if "edges" in p:
            es = resolve(m, p["edges"] if "obj" in p["edges"] else {"obj": p["body"], "edges": p["edges"]}, "edges")
            adj = []
            for e in es:
                for f in s.faces():
                    if any(fe.is_same(e) for fe in f.edges()):
                        adj += [x.length for x in f.edges() if not x.is_same(e)]
            if adj:
                mn = min(adj)
                rep["checks"].append(f"shortest edge on faces next to the selection = {mn:.5g} m; radius above "
                                     f"~{mn / 2:.5g} usually fails there")
    if op in ("boolean", "boolean_fillet") and "target" in p:
        from cadkit.ops import safe_boolean
        a = m.get(p["target"]).shape
        for t in ([p["tools"]] if isinstance(p.get("tools"), str) else p.get("tools") or []):
            ba, bt = a.bounding_box(), m.get(t).shape.bounding_box()
            if any(lo1 > hi2 + 1e-9 or lo2 > hi1 + 1e-9 for lo1, hi1, lo2, hi2 in
                   zip(tuple(ba.min), tuple(ba.max), tuple(bt.min), tuple(bt.max))):
                rep["checks"].append(f"target and {t} do not overlap (bboxes disjoint): union makes 2 lumps, cut/"
                                     "intersect do nothing -> move the tool")
                continue
            try:
                v = safe_boolean("common", a, m.get(t).shape, "explain").volume
                rep["checks"].append(f"overlap volume target & {t} = {v:.6g} m^3" +
                                     (" -> tools do not overlap (union makes 2 lumps, cut does nothing)" if v < 1e-12
                                      else ""))
            except Exception as e:  # noqa
                rep["checks"].append(f"common({t}) failed: {e}"[:200])
    if op in ("loft", "sweep", "extrude", "revolve", "rail_loft"):
        for k in ("profiles", "profile"):
            for x in ([p[k]] if k in p and not isinstance(p[k], list) else p.get(k, [])):
                try:
                    s = resolve(m, x)
                    cl = getattr(s, "is_closed", None)
                    rep["checks"].append(f"profile {x!r}: closed={cl}, edges={len(s.edges())}")
                except Exception:
                    pass


# ------------------------------------------------------------------ state diff
def summary(model):
    out = {}
    for k, o in model.objects.items():
        s = o.shape
        d = {"kind": o.kind}
        try:
            bb = s.bounding_box()
            d["bbox"] = [_r(bb.min, 5), _r(bb.max, 5)]
            if o.kind == "solid":
                d.update(volume=round(s.volume, 9), faces=len(s.faces()), edges=len(s.edges()))
            elif o.kind in ("sheet", "region"):
                d.update(area=round(s.area, 9), faces=len(s.faces()))
            elif o.kind == "curve":
                d["length"] = round(s.length, 6)
        except Exception:
            pass
        out[k] = d
    return out


def diff(before, after):
    """Concise state diff: added/removed objects, and per changed object only the fields that changed."""
    res = {"added": {k: after[k] for k in after if k not in before}, "removed": [k for k in before if k not in after],
           "changed": {}}
    for k in after:
        if k in before and before[k] != after[k]:
            ch = {}
            for f in after[k]:
                a, b = before[k].get(f), after[k][f]
                if a != b:
                    ch[f] = [a, b] if not isinstance(b, (int, float)) or a is None else \
                        {"from": a, "to": b, "delta": round(b - a, 9)}
            res["changed"][k] = ch
    return {k: v for k, v in res.items() if v}
