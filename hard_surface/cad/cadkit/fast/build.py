"""Fast build worker: model script with the op cache, fine face-id mesh (cached per final part), op watchdog,
feature checklist + continuity measurement (need OCCT, so they run here; gate.py only composes).

usage: python -m cadkit.fast.build <model.py> <out_dir> [--cache DIR] [--features spec.json] [--no-cache]
       [--op-timeout S] [--step]
writes out_dir/state.json (kit state + cache stats + per-op timings), mesh.npz (mm, per part v/t/f/n),
       features.json, continuity.json.
Per-op watchdog: if ONE wrapped op runs > --op-timeout s, this process writes state {error: op_timeout, op} and
exits itself (os._exit) - nothing else is killed; completed ops stay cached so the next round resumes.
"""
from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
import threading
import time
import traceback

import numpy as np

CAD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _arg(argv, k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d


# ------------------------------------------------------------------ mesh
def mesh_part(shape, lin, ang):
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopAbs import TopAbs_REVERSED
    BRepMesh_IncrementalMesh(shape.wrapped, lin, False, ang, True)
    V, T, F = [], [], []
    off = 0
    for fi, face in enumerate(shape.faces()):
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face.wrapped, loc)
        if tri is None:
            continue
        tr = loc.Transformation()
        n = tri.NbNodes()
        V.extend(tri.Node(i).Transformed(tr).Coord() for i in range(1, n + 1))
        rev = face.wrapped.Orientation() == TopAbs_REVERSED
        for i in range(1, tri.NbTriangles() + 1):
            a, b, c = tri.Triangle(i).Get()
            T.append((off + a - 1, off + c - 1, off + b - 1) if rev else (off + a - 1, off + b - 1, off + c - 1))
        F.extend([fi] * tri.NbTriangles())
        off += n
    V = np.array(V, "f4").reshape(-1, 3)
    T = np.array(T, "i4").reshape(-1, 3)
    # smooth normals inside a B-rep face (vertices are per face -> face borders stay hard = honest zebra)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return V, T, np.array(F, "i4"), N.astype("f4")


def mesh_all(parts, cache_dir, scale):
    from cadkit.fast import cache
    from build123d import Compound
    diag = Compound([p for p, _ in parts.values()]).bounding_box().diagonal
    lin, ang = diag * 4e-4, 0.12
    out, hits = {}, 0
    for k, (s, _) in parts.items():
        p = None
        if cache_dir:
            key = hashlib.sha1(f"{cache.shape_key(s)}|{lin:.6g}|{ang}".encode()).hexdigest()
            p = os.path.join(cache_dir, "m" + key + ".npz")
            if os.path.exists(p):
                z = np.load(p)
                out[k] = (z["v"], z["t"], z["f"], z["n"])
                hits += 1
                continue
        out[k] = mesh_part(s, lin, ang)
        if p:
            np.savez(p, v=out[k][0], t=out[k][1], f=out[k][2], n=out[k][3])
    return out, hits


# ------------------------------------------------------------------ features (named checklist)
def _bb(shapes):
    from build123d import Compound
    b = Compound(list(shapes)).bounding_box()
    return np.array(tuple(b.min)), np.array(tuple(b.max))


def check_features(spec, parts, ns):
    """spec["features"]: [{name, find: {...}, center?|size?|min?|max?: [x,y,z] (null = unchecked axis) | radius?: r, tol?: 1.0}] (model units)
    find kinds:  {"part": name}                       bbox of a PARTS body
                 {"tag": name}                        bbox of refs.tag()ged shapes
                 {"var": name}                        bbox of a model-script variable (shape / list)
                 {"region": [[x0,y0,z0],[x1,y1,z1]], "part"?: name}   faces whose centre lies in the box
                 {"cyl": [x,y,z], "part"?: name, "axis"?: "x|y|z"}     nearest cylindrical face -> radius + axis pos
    Missing value None = not checked. Every listed number must match within tol (default 1.0 mm)."""
    from build123d import GeomType
    from cadkit.refs import TAGS
    res = []
    bodies = {k: s for k, (s, _) in parts.items()}
    for f in spec.get("features", []):
        r = {"name": f["name"], "pass": False}
        tol = f.get("tol", 1.0)
        try:
            fd = f["find"]
            pool = [bodies[fd["part"]]] if "part" in fd else list(bodies.values())
            if "cyl" in fd:
                p0 = np.array(fd["cyl"], float)
                best = None
                for b in pool:
                    for fc in b.faces():
                        if fc.geom_type != GeomType.CYLINDER:
                            continue
                        c = np.array(tuple(fc.center()))
                        d = np.linalg.norm(c - p0)
                        if best is None or d < best[0]:
                            best = (d, fc)
                if best is None:
                    raise LookupError("no cylindrical face")
                fc = best[1]
                from OCP.BRepAdaptor import BRepAdaptor_Surface
                cy = BRepAdaptor_Surface(fc.wrapped).Cylinder()
                got_r = cy.Radius()
                lo, hi = _bb([fc])
                r["got"] = {"radius": round(got_r, 3), "center": np.round((lo + hi) / 2, 3).tolist(),
                            "dist_from_hint": round(best[0], 3)}
                errs = {}
                if f.get("radius") is not None:
                    errs["radius"] = abs(got_r - f["radius"])
                if f.get("center") is not None:
                    ax = fd.get("axis")
                    c = (lo + hi) / 2
                    e = np.abs(c - np.array(f["center"], float))
                    if ax:  # along-axis position of a through-hole is meaningless
                        e["xyz".index(ax)] = 0.0
                    errs["center"] = float(e.max())
            else:
                if "part" in fd and "region" not in fd:
                    shapes = [bodies[fd["part"]]]
                elif "tag" in fd:
                    shapes = TAGS[fd["tag"]]
                elif "var" in fd:
                    v = ns[fd["var"]]
                    shapes = v if isinstance(v, (list, tuple)) else [v]
                else:
                    a, b = np.array(fd["region"][0], float), np.array(fd["region"][1], float)
                    shapes = [fc for bd in pool for fc in bd.faces()
                              if np.all((np.array(tuple(fc.center())) >= a) & (np.array(tuple(fc.center())) <= b))]
                    if not shapes:
                        raise LookupError("no faces in region")
                lo, hi = _bb(shapes)
                r["got"] = {"center": np.round((lo + hi) / 2, 3).tolist(), "size": np.round(hi - lo, 3).tolist(),
                            "min": np.round(lo, 3).tolist(), "max": np.round(hi, 3).tolist()}
                errs = {}
                for key, val in (("center", (lo + hi) / 2), ("size", hi - lo), ("min", lo), ("max", hi)):
                    if f.get(key) is not None:
                        exp = np.array([np.nan if x is None else x for x in f[key]], float)
                        errs[key] = float(np.nanmax(np.abs(val - exp)))
            r["err"] = {k: round(v, 3) for k, v in errs.items()}
            r["pass"] = bool(errs) and all(v <= tol for v in errs.values())
            r["tol"] = tol
        except Exception as e:
            r["error"] = f"{type(e).__name__}: {e}"
        res.append(r)
    return res


# ------------------------------------------------------------------ continuity (zebra metric, exact B-rep)
def continuity(shape, smooth_deg=12.0):
    """Prefer the kit's exact classifier (cadkit.network.edge_continuity, G1 < 0.5 deg, G2 dk_rel < 0.05);
    edges with angle > smooth_deg are design creases and are skipped. Fallback: own sampler below."""
    try:
        from cadkit.network import edge_continuity
    except ImportError:
        return _continuity_own(shape, smooth_deg=smooth_deg)
    rows = [r for r in edge_continuity(shape, samples=7, g1_deg=0.1, g2_rel=0.05)["edges"]
            if r["cls"] != "open" and r.get("angle_deg", 99) <= smooth_deg]
    n = max(len(rows), 1)
    g1 = [r for r in rows if r["cls"] in ("G1", "G2")]
    g2 = [r for r in rows if r["cls"] == "G2"]
    worst = sorted(rows, key=lambda r: (-r["angle_deg"], -r["dk_rel"]))[:8]
    return {"src": "cadkit.network.edge_continuity", "smooth_edges": len(rows), "g1_ok": len(g1), "g2_ok": len(g2),
            "max_g1_deg": max([r["angle_deg"] for r in rows], default=0.0),
            "g1_frac": round(len(g1) / n, 3), "g2_frac": round(len(g2) / n, 3),
            "worst": [{"at": r["centre"], "g1_deg": r["angle_deg"], "g2_jump": r["dk_rel"]} for r in worst]}


def _continuity_own(shape, n_samp=7, smooth_deg=12.0):
    """For every edge shared by two faces of `shape`: G1 = max normal angle along the edge, G2 = max relative jump
    of the normal curvature measured ACROSS the edge. Edges with angle > smooth_deg are design creases (skipped).
    G1 ok <= 0.5 deg ; G2 ok  rel jump <= 0.25 (|k1-k2| / max(|k1|,|k2|, 1/(10*diag)))."""
    from OCP.TopExp import TopExp
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    try:
        from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
    except ImportError:  # OCP 8.x
        from OCP.collections import             IndexedDataMap_TopoDS_Shape_List_TopoDS_Shape_TopTools_ShapeMapHasher as             TopTools_IndexedDataMapOfShapeListOfShape
    from OCP.TopoDS import TopoDS
    from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
    from OCP.BRepLProp import BRepLProp_SLProps
    from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
    from OCP.BRep import BRep_Tool
    from OCP.gp import gp_Vec
    m = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape.wrapped, TopAbs_EDGE, TopAbs_FACE, m)
    diag = shape.bounding_box().diagonal
    kfloor = 1.0 / (10 * diag)
    out = {"smooth_edges": 0, "g1_ok": 0, "g2_ok": 0, "max_g1_deg": 0.0, "worst": []}
    for i in range(1, m.Extent() + 1):
        fl = m.FindFromIndex(i)
        faces = []
        it = fl.cbegin() if hasattr(fl, "cbegin") else None
        try:
            for f in fl:
                faces.append(TopoDS.Face(f))
        except TypeError:
            continue
        uniq = []
        for f in faces:
            if not any(f.IsSame(g) for g in uniq):
                uniq.append(f)
        if len(uniq) != 2:
            continue
        e = TopoDS.Edge(m.FindKey(i))
        if BRep_Tool.Degenerated_s(e):
            continue
        ca = BRepAdaptor_Curve(e)
        t0, t1 = ca.FirstParameter(), ca.LastParameter()
        g1, g2 = 0.0, 0.0
        okp = 0
        for s in np.linspace(0.1, 0.9, n_samp):
            t = t0 + (t1 - t0) * s
            p = ca.Value(t)
            tan = gp_Vec()
            ca.D1(t, p, tan)
            if tan.Magnitude() < 1e-12:
                continue
            ns_, ks = [], []
            for f in uniq:
                srf = BRep_Tool.Surface_s(f)
                pr = GeomAPI_ProjectPointOnSurf(p, srf)
                if pr.NbPoints() == 0:
                    break
                u, v = pr.LowerDistanceParameters()
                pp = BRepLProp_SLProps(BRepAdaptor_Surface(f), u, v, 2, 1e-7)
                if not pp.IsNormalDefined():
                    break
                nn = gp_Vec(pp.Normal().XYZ())
                if f.Orientation() == 1:  # REVERSED
                    nn.Reverse()
                ns_.append(nn)
                if pp.IsCurvatureDefined():
                    across = nn.Crossed(tan).Normalized()
                    k1, k2 = pp.MaxCurvature(), pp.MinCurvature()
                    d1 = pp.CurvatureDirections if False else None
                    from OCP.gp import gp_Dir
                    dmax, dmin = gp_Dir(), gp_Dir()
                    pp.CurvatureDirections(dmax, dmin)
                    c = across.Dot(gp_Vec(dmax))
                    ks.append(k1 * c * c + k2 * (1 - c * c))
                else:
                    ks.append(None)
            if len(ns_) != 2:
                continue
            okp += 1
            ang = np.degrees(ns_[0].Angle(ns_[1]))
            g1 = max(g1, ang)
            if None not in ks:
                g2 = max(g2, abs(abs(ks[0]) - abs(ks[1])) / max(abs(ks[0]), abs(ks[1]), kfloor))
        if not okp or g1 > smooth_deg:
            continue
        out["smooth_edges"] += 1
        out["g1_ok"] += int(g1 <= 0.5)
        out["g2_ok"] += int(g1 <= 0.5 and g2 <= 0.25)
        out["max_g1_deg"] = max(out["max_g1_deg"], round(float(g1), 3))
        c = ca.Value((t0 + t1) / 2)
        out["worst"].append({"at": [round(c.X(), 2), round(c.Y(), 2), round(c.Z(), 2)], "g1_deg": round(float(g1), 3),
                             "g2_jump": round(float(g2), 3)})
    out["worst"] = sorted(out["worst"], key=lambda w: (-w["g1_deg"], -w["g2_jump"]))[:8]
    n = max(out["smooth_edges"], 1)
    out["g1_frac"], out["g2_frac"] = round(out["g1_ok"] / n, 3), round(out["g2_ok"] / n, 3)
    return out


def _js(o):
    return o.item() if hasattr(o, "item") else str(o)


# ------------------------------------------------------------------ main
_WD = {"path": None, "t0": 0.0, "op_to": 240.0, "started": False}


def _watchdog():
    from cadkit.fast import cache
    from cadkit.ops import LOG
    while True:
        time.sleep(0.5)
        cur = cache.CURRENT
        if cur and _WD["path"] and time.perf_counter() - cur[1] > _WD["op_to"]:
            json.dump({"ok": False, "error": f"op_timeout: '{cur[0]}' ran > {_WD['op_to']:.0f}s (only this build "
                       "process exited; ops before it are cached)", "op": cur[0], "line": cur[2], "ops": LOG,
                       "cache": {k: v for k, v in cache.STATS.items() if k != "calls"},
                       "total_s": round(time.time() - _WD["t0"], 2)}, open(_WD["path"], "w"), indent=1, default=str)
            os._exit(3)


def reset():
    """Per-build reset of kit module state (lets one warm process run many builds - see serve.py)."""
    from cadkit.fast import cache
    from cadkit import ops, refs
    ops.LOG.clear()
    refs.TAGS.clear()
    cache._PROV.clear()
    cache.CURRENT = None
    for k in ("hits", "misses", "uncacheable"):
        cache.STATS[k] = 0
    for k in ("hit_s", "miss_s", "hash_s"):
        cache.STATS[k] = 0.0
    cache.STATS["calls"] = []


def build(argv):
    model, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    os.makedirs(out, exist_ok=True)
    cache_dir = None if "--no-cache" in argv else os.path.abspath(
        _arg(argv, "--cache", os.path.join(os.path.dirname(model), ".fastcache")))
    op_to = float(_arg(argv, "--op-timeout", os.environ.get("CADKIT_FAST_OP_TIMEOUT", "240")))
    spec_p = _arg(argv, "--features")
    if os.path.dirname(model) not in sys.path:
        sys.path.insert(0, os.path.dirname(model))
    t0 = time.time()
    from cadkit.fast import cache
    import cadkit.worker as kw
    from cadkit.ops import LOG
    reset()
    if cache_dir:
        cache.install(cache_dir)
    else:
        cache.uninstall()
    st_path = os.path.join(out, "state.json")
    _WD.update(path=st_path, t0=t0, op_to=op_to)
    if not _WD["started"]:
        threading.Thread(target=_watchdog, daemon=True).start()
        _WD["started"] = True
    tim = {}
    try:
        ns = runpy.run_path(model, run_name="__cadmodel__")
        tim["exec_s"] = round(time.time() - t0, 2)
        kw.S = 0.001 if ns.get("UNITS", "m") == "mm" else 1.0
        parts = kw.collect_parts(ns)
        st = kw.state_of(parts, ns, tim["exec_s"])
        t1 = time.time()
        meshes, mhits = mesh_all(parts, cache_dir, kw.S)
        tim["mesh_s"], tim["mesh_hits"] = round(time.time() - t1, 2), mhits
        mm = 1.0 if kw.S == 0.001 else 1000.0  # mesh.npz always in mm
        np.savez(os.path.join(out, "mesh.npz"), names=np.array(list(meshes)),
                 colours=np.array([kw._hex(parts[k][1]) for k in meshes], "f4"),
                 **{f"v_{i}": m[0] * mm for i, m in enumerate(meshes.values())},
                 **{f"t_{i}": m[1] for i, m in enumerate(meshes.values())},
                 **{f"f_{i}": m[2] for i, m in enumerate(meshes.values())},
                 **{f"n_{i}": m[3] for i, m in enumerate(meshes.values())})
        st["tris"] = int(sum(len(m[1]) for m in meshes.values()))
        spec = json.load(open(spec_p)) if spec_p else {}
        t2 = time.time()
        if spec.get("features"):
            json.dump(check_features(spec, parts, ns), open(os.path.join(out, "features.json"), "w"), indent=1,
                      default=_js)
        mains = spec.get("main_surfaces", [])
        if mains:
            cont = {}
            for k in mains:
                ck = None
                if cache_dir:
                    ck = os.path.join(cache_dir, "c" + hashlib.sha1(cache.shape_key(parts[k][0]).encode()).hexdigest()
                                      + ".json")
                    if os.path.exists(ck):
                        cont[k] = json.load(open(ck))
                        continue
                cont[k] = continuity(parts[k][0])
                if ck:
                    json.dump(cont[k], open(ck, "w"), default=_js)
            json.dump(cont, open(os.path.join(out, "continuity.json"), "w"), indent=1, default=_js)
        tim["checks_s"] = round(time.time() - t2, 2)   # continuity is cached per final-shape key too
        if "--step" in argv:
            from build123d import Compound, export_step, Unit
            kids = []
            for k, (s, _) in parts.items():
                s.label = k
                kids.append(s)
            export_step(Compound(children=kids), os.path.join(out, "model.step"),
                        unit=Unit.MM if kw.S != 1.0 else Unit.M)
    except Exception as e:
        tb = traceback.format_exc()
        st = {"ok": False, "error": f"{type(e).__name__}: {e}", "traceback": tb[-3000:], "ops": LOG,
              "hint": kw._hint(e, tb)}
    st["timing"] = tim
    st["cache"] = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in cache.STATS.items()}
    st["total_s"] = round(time.time() - t0, 2)
    json.dump(st, open(st_path, "w"), indent=1, default=str)
    _WD["path"] = None
    return st


def main(argv):
    st = build(argv)
    print(json.dumps({"ok": st["ok"], "total_s": st["total_s"], "hits": st["cache"]["hits"],
                      "misses": st["cache"]["misses"]}))
    sys.stdout.flush()
    os._exit(0 if st["ok"] else 2)   # skip OCCT teardown (slow on big models)


if __name__ == "__main__":
    main(sys.argv[1:])
