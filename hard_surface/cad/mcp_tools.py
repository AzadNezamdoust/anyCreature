"""MCP tools for cadkit.tools (direct-modelling ops). Registered by mcp_server.py via register(server).

One tool per op (`op_<name>(session, params)`) plus session/journal/query/export tools. A session = one Model
(journal tree) kept in memory and saved to out/tools_sessions/<session>.json after every change, so a restarted
server replays it.  Ops run in-process (fast, interactive); an OCCT segfault would take the server down - the
journal on disk survives, and run_model (subprocess) stays the safe path for whole scripts.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SESS_DIR = os.path.join(HERE, "out", "tools_sessions")
_SESS: dict = {}


def _tools():
    import cadkit.tools as T
    return T


def _load(name, create=False):
    T = _tools()
    if name in _SESS:
        return _SESS[name]
    p = os.path.join(SESS_DIR, f"{name}.json")
    if os.path.exists(p):
        _SESS[name] = T.Model.from_json(json.load(open(p)))
    elif create:
        _SESS[name] = T.Model()
    else:
        raise KeyError(f"no session '{name}' (call cad_new)")
    return _SESS[name]


def _save(name):
    os.makedirs(SESS_DIR, exist_ok=True)
    json.dump(_SESS[name].to_json(), open(os.path.join(SESS_DIR, f"{name}.json"), "w"), indent=1)


def _call(fn):
    T = _tools()
    try:
        return json.dumps({"ok": True, **(fn() or {})}, default=str)
    except T.ToolError as e:
        return json.dumps(e.as_dict(), default=str)
    except KeyError as e:
        return json.dumps({"ok": False, "error": str(e), "hint": "cad_new(session) first"})
    except Exception as e:  # noqa
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"[:800]})


def _op_tool(server, opname, meta):
    def f(session: str, params: dict | None = None) -> str:
        def go():
            m = _load(session)
            info = m.run(opname, **(params or {}))
            _save(session)
            return {"info": info, "objects": m.state()["objects"]}
        return _call(go)
    f.__name__ = f"op_{opname}"
    desc = f"{meta['doc']}\n[provenance: {meta['spec']}]\nparams = this op's keyword args as a JSON object; refs: " \
           f"see cad_help."
    server.tool(name=f"op_{opname}", description=desc[:1800])(f)


def register(server):
    T = _tools()
    for name, meta in sorted(T.OPS.items()):
        _op_tool(server, name, meta)

    @server.tool(name="cad_help")
    def cad_help() -> str:
        """Ref-spec grammar + every op with its params doc and spec provenance."""
        return json.dumps({"refs": T.core.__doc__, "ops": T.describe_ops()})

    @server.tool(name="cad_new")
    def cad_new(session: str) -> str:
        """Start (or reset) a direct-modelling session."""
        def go():
            _SESS[session] = T.Model()
            _save(session)
            return {"session": session}
        return _call(go)

    @server.tool(name="cad_state")
    def cad_state(session: str) -> str:
        """Objects (kind, bbox, volume, faces, valid), tags, cplanes, head node."""
        return _call(lambda: _load(session).state())

    @server.tool(name="cad_journal")
    def cad_journal(session: str) -> str:
        """Journal tree: [{id, parent, op, params}], head."""
        return _call(lambda: _load(session).to_json())

    @server.tool(name="cad_select")
    def cad_select(session: str, ref: dict | str) -> str:
        """Resolve a ref spec without changing anything: count + centres/normals/areas/lengths."""
        return _call(lambda: T.select(_load(session), ref))

    @server.tool(name="cad_undo")
    def cad_undo(session: str) -> str:
        def go():
            m = _load(session)
            m.undo()
            _save(session)
            return m.state()
        return _call(go)

    @server.tool(name="cad_redo")
    def cad_redo(session: str) -> str:
        def go():
            m = _load(session)
            m.redo()
            _save(session)
            return m.state()
        return _call(go)

    @server.tool(name="cad_checkout")
    def cad_checkout(session: str, node: int) -> str:
        """Jump to any journal node (branch switch)."""
        def go():
            m = _load(session)
            m.checkout(node)
            _save(session)
            return m.state()
        return _call(go)

    @server.tool(name="cad_set_param")
    def cad_set_param(session: str, node: int, key: str, value: object) -> str:
        """Parametric edit: change param `key` of journal node and replay (refs re-resolve). Rolls back on error."""
        def go():
            m = _load(session)
            m.set_param(node, key, value)
            _save(session)
            return m.state()
        return _call(go)

    @server.tool(name="cad_export")
    def cad_export(session: str, path: str, fmt: str = "", names: list[str] | None = None) -> str:
        """Export solids to step|glb|gltf|obj|stl (fmt from extension if empty)."""
        return _call(lambda: {"file": T.export_file(_load(session), path, fmt or None, names)})

    @server.tool(name="cad_game_mesh")
    def cad_game_mesh(session: str, tris: int = 4000) -> str:
        """Game mesh via the Blender step (sharp edges + UV seams from B-rep faces, LODs, glb)."""
        out = os.path.join(HERE, "out", "tools_runs", session)
        return _call(lambda: {"dir": out, "report": T.game_mesh(_load(session), out, tris)})

    @server.tool(name="cad_render")
    def cad_render(session: str, res: int = 900) -> str:
        """Smooth + clay + zebra surface render sheet (Blender Workbench). Returns sheet.png path - look at it."""
        out = os.path.join(HERE, "out", "tools_runs", session)
        return _call(lambda: {"sheet": T.render(_load(session), out, res)})
