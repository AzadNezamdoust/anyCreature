"""Model state, op registry, journal tree and semantic refs for cadkit.tools.

Every modelling op is a pure function  op(model, **params) -> info dict  registered with @op.  Model.run() records
{op, params} in a journal TREE (undo = move head to parent, a new op after undo = new branch, set_param = edit an
old op and replay).  Params hold only JSON data: geometry is picked with *ref specs* (semantic queries) that are
re-resolved on every replay, never raw topology ids (spec plasticity_spec.md section 3 "topology naming is not stable").

Ref spec forms (see resolve()):
    "crate"                                    whole object
    {"obj": "crate", "faces": {...filter}}     faces of an object   (also "edges", "vertices", "solids")
filter keys: normal "+z"|[x,y,z] (+ angle_tol deg), geom "plane|cylinder|cone|sphere|torus|bspline|line|circle",
    pick "max"|"min" (+ axis "x|y|z", default z) | "largest"|"smallest", near [x,y,z] (+ radius), within [[min],[max]],
    parallel "x|y|z" (edges), longer/shorter (edges), of_faces {sub-filter} (edges/vertices of matching faces),
    loop "outer"|"inner"|"all" (with of_faces: edges of that face loop), tangent_chain true (grow edges along G1
    neighbours), tag "name" (a tag stored with the 'tag' op), expect N (error if count != N), first N.
"""
from __future__ import annotations

import copy
import json
import math

from build123d import Axis, GeomType, ShapeList, Vector

OPS: dict[str, dict] = {}


class ToolError(RuntimeError):
    """Error with an LLM-actionable hint. str(e) = message; e.hint; e.data (JSON-able)."""

    def __init__(self, msg, hint="", data=None):
        super().__init__(msg)
        self.hint, self.data = hint, data or {}

    def as_dict(self):
        return {"ok": False, "error": str(self), "hint": self.hint, **({"data": self.data} if self.data else {})}


def op(name, spec="", out=True):
    """Register a tool. spec = which plasticity_spec.md section it implements (provenance)."""
    def deco(fn):
        OPS[name] = {"fn": fn, "spec": spec, "doc": (fn.__doc__ or "").strip(), "out": out}
        return fn
    return deco


class Obj:
    __slots__ = ("kind", "shape", "meta")

    def __init__(self, kind, shape, meta=None):
        self.kind, self.shape, self.meta = kind, shape, dict(meta or {})


class Model:
    def __init__(self):
        self.nodes: list[dict] = []          # journal tree
        self.head: int | None = None
        self.objects: dict[str, Obj] = {}
        self.tags: dict[str, dict] = {}
        self.cplanes: dict = {}
        self._snap: dict = {}                # node id -> snapshot (cache, not persisted)

    # ------------------------------------------------------------------ state snapshots
    def _take(self):
        return ({k: Obj(o.kind, o.shape, o.meta) for k, o in self.objects.items()}, dict(self.tags), dict(self.cplanes))

    def _put(self, s):
        self.objects = {k: Obj(o.kind, o.shape, o.meta) for k, o in s[0].items()}
        self.tags, self.cplanes = dict(s[1]), dict(s[2])

    # ------------------------------------------------------------------ run / journal
    def _exec(self, opname, params):
        if opname not in OPS:
            raise ToolError(f"unknown op '{opname}'", f"known ops: {sorted(OPS)}")
        before = self._take()
        try:
            info = OPS[opname]["fn"](self, **params)
        except ToolError:
            self._put(before)
            raise
        except TypeError as e:
            self._put(before)
            raise ToolError(f"{opname}: bad params: {e}", f"see describe_ops()['{opname}']") from e
        except Exception as e:  # kernel failure -> hint
            self._put(before)
            raise ToolError(f"{opname} failed: {type(e).__name__}: {e}"[:600], kernel_hint(opname, e)) from e
        self._refresh_instances()
        return info or {}

    def _refresh_instances(self):
        """Linked instances follow their source (spec 1 CreateInstance)."""
        from build123d import Axis, Pos
        for k, o in self.objects.items():
            src = o.meta.get("instance_of")
            if not src or src not in self.objects:
                continue
            s = self.objects[src].shape
            mv, rot = o.meta.get("xform", [[0, 0, 0], None])
            if rot:
                s = s.rotate(Axis(s.center(), vec(rot[0])), rot[1])
            o.shape = Pos(*mv) * s

    def run(self, opname, **params):
        """Apply op, record it as child of head. Returns info dict (adds 'node')."""
        from .query import diff, summary
        params = json.loads(json.dumps(params))  # params must be JSON (refs, numbers, strings)
        if OPS.get(opname, {}).get("out") and not params.get("name"):
            params["name"] = self._autoname(opname)
        cache = getattr(self, "_sum", None)
        before = cache[1] if cache and cache[0] == self.head else summary(self)
        info = self._exec(opname, params)
        nid = len(self.nodes)
        self.nodes.append({"id": nid, "parent": self.head, "op": opname, "params": params})
        self.head = nid
        self._snap[nid] = self._take()
        after = summary(self)
        self._sum = (nid, after)
        info["node"] = nid
        info["diff"] = diff(before, after)  # concise: added / removed / only the changed fields
        return info

    def _autoname(self, opname):
        i = 1
        while f"{opname}{i}" in self.objects:
            i += 1
        return f"{opname}{i}"

    def path(self, nid=None):
        nid = self.head if nid is None else nid
        out = []
        while nid is not None:
            out.append(nid)
            nid = self.nodes[nid]["parent"]
        return out[::-1]

    def checkout(self, nid):
        """Rebuild state at node nid (None = empty) from the nearest cached ancestor."""
        self._sum = None  # state diff cache is per head revision
        p = self.path(nid) if nid is not None else []
        start = 0
        self.objects, self.tags, self.cplanes = {}, {}, {}
        for i in range(len(p) - 1, -1, -1):
            if p[i] in self._snap:
                self._put(self._snap[p[i]])
                start = i + 1
                break
        for n in p[start:]:
            nd = self.nodes[n]
            self._exec(nd["op"], nd["params"])
            self._snap[n] = self._take()
        self.head = nid

    def undo(self):
        if self.head is None:
            raise ToolError("nothing to undo")
        self.checkout(self.nodes[self.head]["parent"])

    def redo(self):
        kids = [n["id"] for n in self.nodes if n["parent"] == self.head]
        if not kids:
            raise ToolError("nothing to redo")
        self.checkout(kids[-1])

    def set_param(self, nid, key, value):
        """Parametric edit of an old op (the history Plasticity lacks, spec section 4/5.12). Replays head path."""
        nd = self.nodes[nid]
        old = nd["params"].get(key, None)
        nd["params"][key] = json.loads(json.dumps(value))
        stale = set(self.path_descendants(nid))
        for s in stale:
            self._snap.pop(s, None)
        try:
            self.checkout(self.head)
        except ToolError as e:
            if old is None:
                nd["params"].pop(key, None)
            else:
                nd["params"][key] = old
            for s in stale:
                self._snap.pop(s, None)
            self.checkout(self.head)
            raise ToolError(f"set_param node {nid} {key}={value!r} broke replay: {e}", e.hint) from e

    def path_descendants(self, nid):
        out, todo = [], [nid]
        while todo:
            n = todo.pop()
            out.append(n)
            todo += [m["id"] for m in self.nodes if m["parent"] == n]
        return out

    # ------------------------------------------------------------------ persistence
    def to_json(self):
        return {"version": 1, "nodes": self.nodes, "head": self.head}

    @classmethod
    def from_json(cls, d):
        m = cls()
        m.nodes = copy.deepcopy(d["nodes"])
        m.checkout(d.get("head"))
        return m

    # ------------------------------------------------------------------ access
    def get(self, name, kinds=None):
        if name not in self.objects:
            raise ToolError(f"no object '{name}'", f"objects: {sorted(self.objects)}")
        o = self.objects[name]
        if kinds and o.kind not in kinds:
            raise ToolError(f"'{name}' is a {o.kind}, need {kinds}")
        return o

    def put(self, name, kind, shape, **meta):
        self.objects[name] = Obj(kind, shape, meta)
        return name

    def state(self):
        objs = {}
        for k, o in self.objects.items():
            s = o.shape
            d = {"kind": o.kind}
            try:
                bb = s.bounding_box()
                d["bbox"] = [[round(v, 5) for v in tuple(bb.min)], [round(v, 5) for v in tuple(bb.max)]]
                if o.kind == "solid":
                    d.update(volume=round(s.volume, 9), faces=len(s.faces()), edges=len(s.edges()),
                             valid=bool(s.is_valid))
                elif o.kind in ("region", "sheet"):
                    d.update(area=round(s.area, 9), faces=len(s.faces()))
                elif o.kind == "curve":
                    d.update(length=round(s.length, 6), closed=bool(_closed(s)))
            except Exception as e:  # noqa
                d["error"] = str(e)[:120]
            d.update({kk: vv for kk, vv in o.meta.items() if isinstance(vv, (str, int, float, bool, list))})
            objs[k] = d
        return {"head": self.head, "nodes": len(self.nodes), "objects": objs, "tags": self.tags,
                "cplanes": sorted(self.cplanes)}


def _closed(s):
    try:
        return s.is_closed
    except Exception:
        return False


def kernel_hint(opname, e):
    s = f"{type(e).__name__} {e}"
    if opname in ("fillet", "chamfer", "variable_fillet", "refillet"):
        return "radius too big for a neighbouring short edge/face: lower it or split the edge set (error data has max)."
    if opname == "boolean" or "boolean" in s.lower():
        return "nudge tools ~1e-4 off coplanar/tangent faces or simplify the tool."
    if opname in ("shell", "offset_face", "thicken"):
        return "thickness bigger than the smallest local radius of curvature/fillet: shell before filleting or thin it."
    if opname in ("loft", "sweep", "pipe"):
        return "profiles must be closed, same edge count helps loft; sweep path should be G1 with radius > profile size."
    return "check the refs resolve to what you expect (use the select tool) and the params' units (metres)."


# ====================================================================== refs / selection (spec section 1 Selection, 5.9)
_AX = {"x": Vector(1, 0, 0), "y": Vector(0, 1, 0), "z": Vector(0, 0, 1)}


def vec(v):
    if isinstance(v, str):
        sgn = -1 if v.startswith("-") else 1
        return _AX[v.strip("+-").lower()] * sgn
    return Vector(*v)


_GEOM = {"plane": GeomType.PLANE, "cylinder": GeomType.CYLINDER, "cone": GeomType.CONE, "sphere": GeomType.SPHERE,
         "torus": GeomType.TORUS, "bspline": GeomType.BSPLINE, "bezier": GeomType.BEZIER, "line": GeomType.LINE,
         "circle": GeomType.CIRCLE, "ellipse": GeomType.ELLIPSE, "revolution": GeomType.REVOLUTION,
         "extrusion": GeomType.EXTRUSION, "offset": GeomType.OFFSET}


def resolve(model, ref, want=None):
    """ref spec -> ShapeList (sub-shapes) or a whole shape (for a bare object name and want None)."""
    if isinstance(ref, str):
        if ref in model.tags and ref not in model.objects:
            return resolve(model, model.tags[ref], want)
        o = model.get(ref)
        if want:
            return ShapeList(getattr(o.shape, want)())
        return o.shape
    if not isinstance(ref, dict) or "obj" not in ref:
        if isinstance(ref, dict) and "tag" in ref and len(ref) == 1:
            return resolve(model, model.tags[ref["tag"]], want)
        raise ToolError(f"bad ref {ref!r}", 'use "name" or {"obj": name, "faces"|"edges"|"vertices": {filter}}')
    shape = model.get(ref["obj"]).shape
    kind = next((k for k in ("faces", "edges", "vertices", "solids", "wires") if k in ref), None)
    if kind is None:
        return shape
    flt = ref[kind] or {}
    items = select(model, shape, kind, flt)
    if want and want != kind:
        items = ShapeList([x for it in items for x in getattr(it, want)()])
    return items


def select(model, shape, kind, flt):
    if "tag" in flt:
        t = model.tags.get(flt["tag"])
        if t is None:
            raise ToolError(f"no tag '{flt['tag']}'", f"tags: {sorted(model.tags)}")
        base = resolve(model, t)
        base = ShapeList(base if isinstance(base, (list, ShapeList)) else getattr(base, kind)())
        items = _same_in(shape, kind, base)
    elif "of_faces" in flt and kind in ("edges", "vertices"):
        faces = select(model, shape, "faces", flt["of_faces"])
        loop = flt.get("loop", "all")
        items = []
        for f in faces:
            if loop == "outer":
                items += f.outer_wire().edges() if kind == "edges" else f.outer_wire().vertices()
            elif loop == "inner":
                for w in f.inner_wires():
                    items += w.edges() if kind == "edges" else w.vertices()
            else:
                items += getattr(f, kind)()
        items = _same_in(shape, kind, _dedupe(items))
    else:
        items = list(getattr(shape, kind)())
    if "geom" in flt:
        g = _GEOM[flt["geom"]]
        items = [s for s in items if s.geom_type == g]
    if "normal" in flt:
        n, tol = vec(flt["normal"]).normalized(), math.radians(flt.get("angle_tol", 5))
        items = [f for f in items if _face_normal_ok(f, n, tol)]
    if "parallel" in flt:
        a = vec(flt["parallel"]).normalized()
        items = [e for e in items if e.geom_type == GeomType.LINE and abs(abs(_edir(e).dot(a)) - 1) < 1e-4]
    if "longer" in flt:
        items = [e for e in items if e.length >= flt["longer"]]
    if "shorter" in flt:
        items = [e for e in items if e.length <= flt["shorter"]]
    if "within" in flt:
        lo, hi = Vector(*flt["within"][0]), Vector(*flt["within"][1])
        items = [s for s in items if all(lo_ - 1e-7 <= c <= hi_ + 1e-7 for c, lo_, hi_ in
                                         zip(tuple(s.center()), tuple(lo), tuple(hi)))]
    if "near" in flt:
        p = Vector(*flt["near"])
        if "radius" in flt:
            items = [s for s in items if (s.center() - p).length <= flt["radius"]]
        else:
            items = sorted(items, key=lambda s: (s.center() - p).length)[:1]
    if "pick" in flt and items:
        pk = flt["pick"]
        if pk in ("largest", "smallest"):
            key = (lambda s: s.area) if kind == "faces" else (lambda s: s.length) if kind == "edges" else \
                (lambda s: s.volume)
            items = [sorted(items, key=key)[-1 if pk == "largest" else 0]]
        else:
            ax = vec(flt.get("axis", "z"))
            vals = [s.center().dot(ax) for s in items]
            tgt = max(vals) if pk == "max" else min(vals)
            items = [s for s, v in zip(items, vals) if abs(v - tgt) < flt.get("tol", 1e-6)]
    if flt.get("tangent_chain") and kind == "edges":
        items = tangent_chain(shape, items)
    if "first" in flt:
        items = items[: flt["first"]]
    if "expect" in flt and len(items) != flt["expect"]:
        raise ToolError(f"ref matched {len(items)} {kind}, expected {flt['expect']}", "loosen/tighten the filter",
                        {"matched": [_desc(s) for s in items[:6]]})
    return ShapeList(items)


def _face_normal_ok(f, n, tol):
    try:
        if f.geom_type != GeomType.PLANE:
            return False
        fn = f.normal_at(f.center())
        return fn.get_angle(n) * math.pi / 180 <= tol if hasattr(fn, "get_angle") else False
    except Exception:
        return False


def _edir(e):
    return (e.position_at(1) - e.position_at(0)).normalized()


def _dedupe(items):
    out = []
    for s in items:
        if not any(s.is_same(o) for o in out):
            out.append(s)
    return out


def _same_in(shape, kind, base):
    """Map sub-shapes (maybe from an older revision) onto `shape` by is_same, then by centre+size match."""
    cur = list(getattr(shape, kind)())
    out = []
    for b in base:
        hit = next((c for c in cur if c.is_same(b)), None)
        if hit is None:
            bc = b.center()
            cands = sorted(cur, key=lambda c: (c.center() - bc).length)
            if cands and (cands[0].center() - bc).length < 1e-5:
                hit = cands[0]
        if hit is not None and not any(hit.is_same(o) for o in out):
            out.append(hit)
    return out


def tangent_chain(shape, seeds, ang_tol_deg=2.0):
    """Grow edge set along neighbours that meet G1 (tangent) at a shared vertex (spec 'tangent-chain select')."""
    edges = list(shape.edges())
    chain = _dedupe(list(seeds))
    tol = math.cos(math.radians(ang_tol_deg))
    grew = True
    while grew:
        grew = False
        for e in edges:
            if any(e.is_same(c) for c in chain):
                continue
            for c in chain:
                if _tangent_join(c, e, tol):
                    chain.append(e)
                    grew = True
                    break
    return chain


def _tangent_join(a, b, tol):
    for ta in (0.0, 1.0):
        pa = a.position_at(ta)
        for tb in (0.0, 1.0):
            if (pa - b.position_at(tb)).length < 1e-6:
                da, db = a.tangent_at(ta), b.tangent_at(tb)
                if abs(da.dot(db)) >= tol:
                    return True
    return False


def _desc(s):
    c = s.center()
    d = {"type": type(s).__name__, "center": [round(c.X, 5), round(c.Y, 5), round(c.Z, 5)]}
    try:
        d["geom"] = s.geom_type.name.lower()
    except Exception:
        pass
    if type(s).__name__ == "Face":
        d["area"] = round(s.area, 8)
        if s.geom_type == GeomType.PLANE:
            n = s.normal_at(c)
            d["normal"] = [round(n.X, 4), round(n.Y, 4), round(n.Z, 4)]
    elif type(s).__name__ == "Edge":
        d["length"] = round(s.length, 6)
    return d


def describe(items, n=12):
    items = list(items)
    return {"count": len(items), "items": [_desc(s) for s in items[:n]]}


def describe_ops():
    from .examples import EXAMPLES
    return {k: {"spec": v["spec"], "doc": v["doc"], **({"example": EXAMPLES[k]} if k in EXAMPLES else {})}
            for k, v in sorted(OPS.items())}


def apply_mode(model, name, new, mode="new", target=None, label=""):
    """Combine a freshly built solid with an existing body (spec Extrude operationType new/union/cut/intersect)."""
    from cadkit.ops import safe_boolean
    if mode == "new" or not target:
        if mode != "new":
            raise ToolError(f"mode '{mode}' needs target", "pass target=<body name>")
        model.put(name, "solid", new)
        return name
    kind = {"union": "fuse", "cut": "cut", "intersect": "common"}.get(mode)
    if kind is None:
        raise ToolError(f"bad mode '{mode}'", "new|union|cut|intersect")
    t = model.get(target, ("solid",))
    model.put(target, "solid", safe_boolean(kind, t.shape, new, label or name), **t.meta)
    return target
