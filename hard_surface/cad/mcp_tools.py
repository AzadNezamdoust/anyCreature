"""MCP tools for cadkit.tools (direct-modelling ops). Registered by mcp_server.py via register(server).

One tool per op (`op_<name>(session, params)`) plus cad_run (any op by name) and session/journal/query/export
tools. A session = one Model (journal tree), saved to out/tools_sessions/<session>.json after every change.

Crash isolation: every handler runs in a persistent kernel WORKER subprocess (cadkit/tools/sandbox.py). The MCP
server process never runs OCCT, so a segfault/abort/hang only kills the worker; it is restarted and rebuilds the
session by replaying the on-disk journal. Set CADKIT_INPROC=1 to run in-process (debugging only).
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SESS_DIR = os.path.join(HERE, "out", "tools_sessions")
_SESS: dict = {}
_POOL = None


def _tools():
    import cadkit.tools as T
    return T


def _load(name, create=False):
    T = _tools()
    key = (SESS_DIR, name)
    if key in _SESS:
        return _SESS[key]
    p = os.path.join(SESS_DIR, f"{name}.json")
    if os.path.exists(p):
        _SESS[key] = T.Model.from_json(json.load(open(p)))
    elif create:
        _SESS[key] = T.Model()
    else:
        raise KeyError(f"no session '{name}' (call cad_new)")
    return _SESS[key]


def _save(name):
    os.makedirs(SESS_DIR, exist_ok=True)
    p = os.path.join(SESS_DIR, f"{name}.json")
    json.dump(_SESS[(SESS_DIR, name)].to_json(), open(p + ".tmp", "w"), indent=1)
    os.replace(p + ".tmp", p)  # atomic: a crash never leaves a half-written journal


# ---------------------------------------------------------------- handlers (run inside the kernel worker)
def h_new(session):
    _SESS[(SESS_DIR, session)] = _tools().Model()
    _save(session)
    return {"session": session}


def h_run(session, op, params=None):
    m = _load(session)
    info = m.run(op, **(params or {}))
    _save(session)
    return {"info": info, "objects": m.state()["objects"]}


def _mut(fn):
    def h(session, **kw):
        m = _load(session)
        fn(m, **kw)
        _save(session)
        return m.state()
    return h


def h_export(session, path, fmt="", names=None):
    return {"file": _tools().export_file(_load(session), path, fmt or None, names)}


def h_game_mesh(session, tris=4000):
    out = os.path.join(HERE, "out", "tools_runs", session)
    return {"dir": out, "report": _tools().game_mesh(_load(session), out, tris)}


def h_render(session, res=900):
    out = os.path.join(HERE, "out", "tools_runs", session)
    return {"sheet": _tools().render(_load(session), out, res)}


HANDLERS = {
    "help": lambda: {"refs": _tools().core.__doc__, "ops": _tools().describe_ops()},
    "new": h_new,
    "run": h_run,
    "state": lambda session: _load(session).state(),
    "journal": lambda session: _load(session).to_json(),
    "select": lambda session, ref: _tools().select(_load(session), ref),
    "undo": _mut(lambda m: m.undo()),
    "redo": _mut(lambda m: m.redo()),
    "checkout": _mut(lambda m, node: m.checkout(node)),
    "set_param": _mut(lambda m, node, key, value: m.set_param(node, key, value)),
    "export": h_export,
    "game_mesh": h_game_mesh,
    "render": h_render,
    "ping": lambda: {"pid": os.getpid()},
    # read-only queries (no journal entry) - cadkit/tools/query.py
    "measure": lambda session, a, b=None: _q().measure(_load(session), a, b),
    "curvature": lambda session, face, point=None: _q().curvature(_load(session), face, point),
    "draft_analysis": lambda session, body, pull="+z", min_draft=1.0: _q().draft_analysis(_load(session), body,
                                                                                          pull, min_draft),
    "deviation": lambda session, a, b, samples=20000: _q().deviation(_load(session), a, b, samples),
    "compare_to_ref": lambda session, image, view="front", names=None, m_per_px=None, origin_px=None,
    threshold=128, out=None: _q().compare_to_ref(_load(session), image, view, names, m_per_px, origin_px,
                                                 threshold, out),
    "suggest_refs": lambda session, obj, near=None, kind="faces", n=6: _q().suggest_refs(_load(session), obj, near,
                                                                                       kind, n),
    "explain_failure": lambda session, op, params=None: _q().explain_failure(_load(session), op, params or {}),
}


def _q():
    from cadkit.tools import query
    return query


def inproc(method, args):
    """Run a handler here; always returns a JSON string (errors -> ok false + hint)."""
    T = _tools()
    try:
        return json.dumps({"ok": True, **(HANDLERS[method](**args) or {})}, default=str)
    except T.ToolError as e:
        return json.dumps(e.as_dict(), default=str)
    except KeyError as e:
        return json.dumps({"ok": False, "error": str(e), "hint": "cad_new(session) first"})
    except Exception as e:  # noqa
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"[:800]})


def pool():
    global _POOL
    if _POOL is None:
        from cadkit.tools.sandbox import KernelPool
        _POOL = KernelPool(timeout=float(os.environ.get("CADKIT_OP_TIMEOUT", "300")))
    return _POOL


def dispatch(method, args, timeout=None):
    if os.environ.get("CADKIT_INPROC") == "1":
        return inproc(method, args)
    return pool().request(method, args, SESS_DIR, timeout)


# ---------------------------------------------------------------- MCP registration (server process)
def _op_tool(server, opname, meta):
    def f(session: str, params: dict | None = None) -> str:
        return dispatch("run", {"session": session, "op": opname, "params": params or {}})
    f.__name__ = f"op_{opname}"
    from cadkit.tools.examples import EXAMPLES
    ex = f"\nexample params: {json.dumps(EXAMPLES[opname])}" if opname in EXAMPLES else ""
    desc = f"{meta['doc']}{ex}\n[provenance: {meta['spec']}]\nparams = this op's keyword args as a JSON object; " \
           f"refs: see cad_help. Result has diff (added/removed/changed fields). On error: cad_explain_failure."
    server.tool(name=f"op_{opname}", description=desc[:1800])(f)


def register(server):
    T = _tools()  # only the op REGISTRY (docs) is read here; ops execute in the worker
    for name, meta in sorted(T.OPS.items()):
        if not name.startswith("debug_"):
            _op_tool(server, name, meta)

    @server.tool(name="cad_help")
    def cad_help() -> str:
        """Ref-spec grammar + every op with its params doc and spec provenance."""
        return json.dumps({"refs": T.core.__doc__, "ops": T.describe_ops()})

    @server.tool(name="cad_run")
    def cad_run(session: str, op: str, params: dict | None = None) -> str:
        """Run any op by name (same as op_<name>). Ops run in a crash-isolated kernel worker: on a kernel crash
        you get ok=false, crashed=true and the session is unchanged."""
        return dispatch("run", {"session": session, "op": op, "params": params or {}})

    @server.tool(name="cad_new")
    def cad_new(session: str) -> str:
        """Start (or reset) a direct-modelling session."""
        return dispatch("new", {"session": session})

    @server.tool(name="cad_state")
    def cad_state(session: str) -> str:
        """Objects (kind, bbox, volume, faces, valid), tags, cplanes, head node."""
        return dispatch("state", {"session": session})

    @server.tool(name="cad_journal")
    def cad_journal(session: str) -> str:
        """Journal tree: [{id, parent, op, params}], head."""
        return dispatch("journal", {"session": session})

    @server.tool(name="cad_select")
    def cad_select(session: str, ref: dict | str) -> str:
        """Resolve a ref spec without changing anything: count + centres/normals/areas/lengths."""
        return dispatch("select", {"session": session, "ref": ref})

    @server.tool(name="cad_undo")
    def cad_undo(session: str) -> str:
        return dispatch("undo", {"session": session})

    @server.tool(name="cad_redo")
    def cad_redo(session: str) -> str:
        return dispatch("redo", {"session": session})

    @server.tool(name="cad_checkout")
    def cad_checkout(session: str, node: int) -> str:
        """Jump to any journal node (branch switch)."""
        return dispatch("checkout", {"session": session, "node": node})

    @server.tool(name="cad_set_param")
    def cad_set_param(session: str, node: int, key: str, value: object) -> str:
        """Parametric edit: change param `key` of journal node and replay (refs re-resolve). Rolls back on error."""
        return dispatch("set_param", {"session": session, "node": node, "key": key, "value": value})

    @server.tool(name="cad_export")
    def cad_export(session: str, path: str, fmt: str = "", names: list[str] | None = None) -> str:
        """Export solids to step|glb|gltf|obj|stl (fmt from extension if empty)."""
        return dispatch("export", {"session": session, "path": path, "fmt": fmt, "names": names})

    @server.tool(name="cad_game_mesh")
    def cad_game_mesh(session: str, tris: int = 4000) -> str:
        """Game mesh via the Blender step (sharp edges + UV seams from B-rep faces, LODs, glb)."""
        return dispatch("game_mesh", {"session": session, "tris": tris}, timeout=900)

    @server.tool(name="cad_render")
    def cad_render(session: str, res: int = 900) -> str:
        """Smooth + clay + zebra surface render sheet (Blender Workbench). Returns sheet.png path - look at it."""
        return dispatch("render", {"session": session, "res": res}, timeout=900)

    @server.tool(name="cad_measure")
    def cad_measure(session: str, a: dict | str, b: dict | str | None = None) -> str:
        """a alone: length/area/volume/radius/normal/bbox. a+b: min distance, closest points, angle (planar faces /
        straight edges). e.g. a={"obj":"body","faces":{"normal":"+z"}}, b={"obj":"body","faces":{"normal":"-z"}}"""
        return dispatch("measure", {"session": session, "a": a, "b": b})

    @server.tool(name="cad_curvature")
    def cad_curvature(session: str, face: dict | str, point: list[float] | None = None) -> str:
        """Principal curvatures k1/k2 (1/m), radii, directions of one face at the point nearest `point`."""
        return dispatch("curvature", {"session": session, "face": face, "point": point})

    @server.tool(name="cad_draft_analysis")
    def cad_draft_analysis(session: str, body: str, pull: str | list[float] = "+z", min_draft: float = 1.0) -> str:
        """Per-face draft vs pull direction; lists faces needing draft with a near-ref to feed op_draft_face."""
        return dispatch("draft_analysis", {"session": session, "body": body, "pull": pull, "min_draft": min_draft})

    @server.tool(name="cad_deviation")
    def cad_deviation(session: str, a: dict | str, b: dict | str, samples: int = 20000) -> str:
        """Surface deviation a vs b (object/ref or mesh file .stl/.obj/.glb): max/mean/rms/p95/hausdorff, worst point."""
        return dispatch("deviation", {"session": session, "a": a, "b": b, "samples": samples})

    @server.tool(name="cad_compare_to_ref")
    def cad_compare_to_ref(session: str, image: str, view: str = "front", names: list[str] | None = None,
                           m_per_px: float | None = None, origin_px: list[float] | None = None,
                           threshold: int = 128, out: str | None = None) -> str:
        """Silhouette IoU vs a reference image (view front=XZ, side=YZ, top=XY). With m_per_px+origin_px (pixel of
        world 0,0) = absolute; without = shape-only (height-fit) and returns implied m_per_px. out = diff png path
        (red model-only, blue ref-only)."""
        return dispatch("compare_to_ref", {"session": session, "image": image, "view": view, "names": names,
                                           "m_per_px": m_per_px, "origin_px": origin_px, "threshold": threshold,
                                           "out": out})

    @server.tool(name="cad_suggest_refs")
    def cad_suggest_refs(session: str, obj: str, near: list[float] | None = None, kind: str = "faces",
                         n: int = 6) -> str:
        """Entities of obj nearest `near` with VERIFIED ref specs: stable_refs (semantic, survive edits) + near_ref.
        Paste one into any op's faces/edges param."""
        return dispatch("suggest_refs", {"session": session, "obj": obj, "near": near, "kind": kind, "n": n})

    @server.tool(name="cad_explain_failure")
    def cad_explain_failure(session: str, op: str, params: dict | None = None) -> str:
        """Dry-run an op (state untouched): missing/unknown params, what each ref resolves to, op checks (fillet
        shortest neighbour edge, boolean overlap, profile closed), kernel error + hint."""
        return dispatch("explain_failure", {"session": session, "op": op, "params": params or {}})
