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
}


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
    desc = f"{meta['doc']}\n[provenance: {meta['spec']}]\nparams = this op's keyword args as a JSON object; refs: " \
           f"see cad_help."
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
