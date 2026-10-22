"""Content-addressed op cache for model scripts (incremental rebuild).

Model scripts are plain Python, not journals, so "prefix" caching is done per op call: every expensive kit /
build123d op is wrapped; its key = sha1(op name + kit-source salt + canonical params + input-geometry keys).
Input geometry key = provenance key when the shape came out of a cached op (free), else sha1 of its BREP text.
Edit op N -> ops before N see identical inputs -> disk hits; N..end see new inputs -> recompute.  No false hits
unless an op reads hidden global state (none of the wrapped ones do).  Results that are not Shapes / lists of
Shapes, or params whose repr has a memory address (lambdas), are simply not cached.

Cached per entry: <key>.N.bbrep (BinTools binary B-rep, lossless), <key>.json (class names, labels, LOG slice, error).
LOG entries (fillet reduced / manifold fallback ...) are replayed on hits so the gate still sees them.
Exceptions are cached too (re-raised with the same type) - try/except radius loops replay instantly.

    from cadkit.fast import cache; cache.install(dir)   # before runpy of the model
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import time

_DIR = None
_PROV: dict[int, tuple[object, str]] = {}   # id(shape) -> (shape, key)  (strong ref keeps id unique)
_DEPTH = [0]
CURRENT = None   # (op, t_start, model line) of the op running now - read by the build watchdog
STATS = {"hits": 0, "misses": 0, "uncacheable": 0, "hit_s": 0.0, "miss_s": 0.0, "hash_s": 0.0, "calls": []}

CADKIT_OPS = ["safe_fillet", "safe_chamfer", "variable_fillet", "safe_boolean", "cut", "fuse", "common",
              "robust_shell", "robust_offset_face", "rail_loft", "patch", "coons_patch", "blend_surface", "cap_round"]
B3D_OPS = ["fillet", "chamfer", "revolve", "extrude", "loft", "sweep", "offset", "split", "section", "thicken"]


class Uncacheable(Exception):
    pass


def _salt():
    import build123d
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    h = hashlib.sha1(build123d.__version__.encode())
    for f in ("ops.py", "surf.py", "isolate.py", "refs.py"):
        p = os.path.join(here, f)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:12]


def _bin(shape):
    """Exact binary B-rep (BinTools, in memory): lossless doubles -> a loaded hit hashes like the fresh shape."""
    from OCP.BinTools import BinTools
    bio = io.BytesIO()
    BinTools.Write_s(getattr(shape, "wrapped", shape), bio)
    return bio.getvalue()


def _fingerprint(shape):
    """Geometric fingerprint, independent of serialization artefacts (BREP location-table order, -0 vs 0, flags):
    shape type + orientation + sorted per-vertex coords, per-edge (type, ends, mid), per-face (type, bbox),
    rounded to 1e-6. Rounding-boundary noise can only cause a miss, never a false hit of different geometry."""
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    w = getattr(shape, "wrapped", shape)

    def r(*v):
        return tuple(round(x, 6) + 0.0 for x in v)
    vs, es, fs = [], [], []
    ex = TopExp_Explorer(w, TopAbs_VERTEX)
    while ex.More():
        p = BRep_Tool.Pnt_s(TopoDS.Vertex(ex.Current()))
        vs.append(r(p.X(), p.Y(), p.Z()))
        ex.Next()
    ex = TopExp_Explorer(w, TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge(ex.Current())
        if BRep_Tool.Degenerated_s(e):
            es.append((-1,))
        else:
            c = BRepAdaptor_Curve(e)
            a, b = c.FirstParameter(), c.LastParameter()
            pts = [c.Value(a + (b - a) * t) for t in (0.0, 0.37, 1.0)]
            es.append((int(c.GetType()), int(e.Orientation())) + sum((r(q.X(), q.Y(), q.Z()) for q in pts), ()))
        ex.Next()
    ex = TopExp_Explorer(w, TopAbs_FACE)
    while ex.More():
        f = TopoDS.Face(ex.Current())
        bb = Bnd_Box()
        BRepBndLib.Add_s(f, bb, False)
        lo, hi = bb.CornerMin(), bb.CornerMax()
        fs.append((int(BRepAdaptor_Surface(f, False).GetType()), int(f.Orientation()))
                  + r(lo.X(), lo.Y(), lo.Z(), hi.X(), hi.Y(), hi.Z()))
        ex.Next()
    return repr((int(w.ShapeType()), int(w.Orientation()), sorted(vs), sorted(es), sorted(fs))).encode()


def _unbin(data):
    from OCP.BinTools import BinTools
    from OCP.TopoDS import TopoDS_Shape
    sh = TopoDS_Shape()
    BinTools.Read_s(sh, io.BytesIO(data))
    return sh


def shape_key(s):
    hit = _PROV.get(id(s))
    if hit is not None and hit[0] is s:
        return hit[1]
    t = time.perf_counter()
    k = "g" + hashlib.sha1(_fingerprint(s)).hexdigest()
    STATS["hash_s"] += time.perf_counter() - t
    _PROV[id(s)] = (s, k)
    return k


def _canon(x):
    from build123d import Shape
    if isinstance(x, Shape):
        return "S:" + shape_key(x)
    if isinstance(x, (list, tuple)):
        return "[" + ",".join(_canon(i) for i in x) + "]"
    if isinstance(x, dict):
        return "{" + ",".join(f"{k}:{_canon(v)}" for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))) + "}"
    if isinstance(x, float):
        return repr(round(x, 12))
    if isinstance(x, (int, str, bool)) or x is None:
        return repr(x)
    if hasattr(x, "wrapped") and hasattr(x, "to_tuple"):
        return type(x).__name__ + repr(tuple(round(v, 12) for v in x.to_tuple()))
    r = repr(x)
    if " at 0x" in r or "object at" in r:
        raise Uncacheable(type(x).__name__)
    return type(x).__name__ + ":" + r


def _save(key, res, log_slice, err=None):
    from build123d import Shape
    meta = {"log": log_slice, "t": time.time()}
    if err is not None:
        meta["error"] = [type(err).__name__, str(err)[:4000]]
    else:
        items, single = (res, False) if isinstance(res, (list, tuple)) else ([res], True)
        if not all(isinstance(i, Shape) for i in items):
            raise Uncacheable("result type " + type(res).__name__)
        meta.update(single=single, seq=type(res).__name__,
                    cls=[type(i).__name__ for i in items], labels=[getattr(i, "label", "") for i in items])
        for n, i in enumerate(items):
            with open(os.path.join(_DIR, f"{key}.{n}.bbrep"), "wb") as fh:
                fh.write(_bin(i))
    tmp = os.path.join(_DIR, key + ".json.tmp")
    json.dump(meta, open(tmp, "w"), default=str)
    os.replace(tmp, os.path.join(_DIR, key + ".json"))   # json last = entry complete


def _load(key):
    p = os.path.join(_DIR, key + ".json")
    if not os.path.exists(p):
        return None
    meta = json.load(open(p))
    if "error" in meta:
        return meta, None
    import build123d as bd
    out = []
    for n, (cn, lb) in enumerate(zip(meta["cls"], meta["labels"])):
        q = os.path.join(_DIR, f"{key}.{n}.bbrep")
        if not os.path.exists(q):
            return None
        sh = _unbin(open(q, "rb").read())
        cls = getattr(bd, cn, None)
        try:
            obj = cls(sh) if cls is not None else bd.Shape.cast(sh)
        except Exception:
            obj = bd.Shape.cast(sh)
        if lb:
            obj.label = lb
        out.append(obj)
    if meta["single"]:
        return meta, out[0]
    if meta["seq"] == "ShapeList":
        return meta, bd.ShapeList(out)
    return meta, (tuple(out) if meta["seq"] == "tuple" else list(out))


def _reraise(name, msg):
    import builtins
    import build123d
    from cadkit import ops
    cls = getattr(builtins, name, None) or getattr(ops, name, None) or getattr(build123d, name, None)
    if not (isinstance(cls, type) and issubclass(cls, BaseException)):
        cls = RuntimeError
    try:
        e = cls(msg)
    except Exception:
        e = RuntimeError(f"{name}: {msg}")
    raise e


def CURRENT_LINE(fr):
    return f"{os.path.basename(fr.f_code.co_filename)}:{fr.f_lineno}"


def _wrap(name, fn, salt):
    from cadkit.ops import LOG

    def w(*a, **kw):
        if _DEPTH[0] or _DIR is None:
            return fn(*a, **kw)
        try:
            th = time.perf_counter()
            key = "o" + hashlib.sha1(f"{salt}|{name}|{_canon(a)}|{_canon(kw)}".encode()).hexdigest()
            STATS["hash_s"] += time.perf_counter() - th
        except Uncacheable:
            STATS["uncacheable"] += 1
            return fn(*a, **kw)
        t = time.perf_counter()
        got = _load(key)
        if got is not None:
            meta, res = got
            LOG.extend(meta["log"])
            dt = time.perf_counter() - t
            STATS["hits"] += 1
            STATS["hit_s"] += dt
            STATS["calls"].append([name, "hit", round(dt, 3)])
            if res is None:
                _reraise(*meta["error"])
            for r in (res if isinstance(res, (list, tuple)) else [res]):
                _PROV[id(r)] = (r, key + f".{id(r)}" if isinstance(res, (list, tuple)) else key)
            return res
        n0 = len(LOG)
        _DEPTH[0] += 1
        global CURRENT
        import sys
        fr = sys._getframe(1)
        CURRENT = (name, time.perf_counter(), f"{os.path.basename(fr.f_code.co_filename)}:{fr.f_lineno}")
        try:
            res = fn(*a, **kw)
        except Exception as e:
            _DEPTH[0] -= 1
            CURRENT = None
            if "Isolation" not in type(e).__name__ and "Timeout" not in type(e).__name__:
                try:
                    _save(key, None, LOG[n0:], err=e)
                except Exception:
                    pass
            raise
        _DEPTH[0] -= 1
        CURRENT = None
        dt = time.perf_counter() - t
        STATS["misses"] += 1
        STATS["miss_s"] += dt
        STATS["calls"].append([name, "miss", round(dt, 3), CURRENT_LINE(fr)])
        try:
            _save(key, res, LOG[n0:])
            if not isinstance(res, (list, tuple)):
                _PROV[id(res)] = (res, key)
        except Uncacheable:
            STATS["uncacheable"] += 1
        return res
    w.__wrapped__ = fn
    w.__name__ = name
    return w


def install(cache_dir):
    """Wrap the kit + build123d op names exported by `cadkit` (what `from cadkit import *` binds)."""
    global _DIR
    _DIR = cache_dir
    os.makedirs(cache_dir, exist_ok=True)
    import cadkit
    salt = _salt()
    for n in CADKIT_OPS + B3D_OPS:
        f = getattr(cadkit, n, None)
        if callable(f) and not hasattr(f, "__wrapped__"):
            setattr(cadkit, n, _wrap(n, f, salt))
    return salt


def uninstall():
    global _DIR
    import cadkit
    for n in CADKIT_OPS + B3D_OPS:
        f = getattr(cadkit, n, None)
        if hasattr(f, "__wrapped__"):
            setattr(cadkit, n, f.__wrapped__)
    _DIR = None
    _PROV.clear()
