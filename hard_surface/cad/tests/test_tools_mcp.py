import asyncio
import json


def _text(r):
    if hasattr(r, "content"):
        r = r.content
    if isinstance(r, tuple):
        r = r[0]
    if isinstance(r, list):
        r = r[0]
    return json.loads(getattr(r, "text", r) if not isinstance(r, dict) else json.dumps(r))


def test_mcp_registration_and_roundtrip(tmp_path, monkeypatch):
    import mcp_tools
    from mcp.server.mcpserver import MCPServer
    monkeypatch.setattr(mcp_tools, "SESS_DIR", str(tmp_path))
    mcp_tools._SESS.clear()
    srv = MCPServer("t")
    mcp_tools.register(srv)
    names = {t.name for t in asyncio.run(srv.list_tools())}
    from cadkit.tools import OPS
    assert {f"op_{k}" for k in OPS} <= names and {"cad_new", "cad_select", "cad_set_param"} <= names

    def call(n, **a):
        return _text(asyncio.run(srv.call_tool(n, a)))
    assert call("cad_new", session="s")["ok"]
    r = call("op_box", session="s", params={"name": "b", "size": [1, 1, 1]})
    assert r["ok"] and r["objects"]["b"]["volume"] == 1
    r = call("op_fillet", session="s", params={"body": "b", "edges": {"parallel": "z"}, "radius": 5, "min_frac": 0.99})
    assert not r["ok"] and r["hint"]
    assert call("cad_select", session="s", ref={"obj": "b", "faces": {"normal": "+z"}})["count"] == 1
    assert call("cad_set_param", session="s", node=0, key="size", value=[2, 1, 1])["objects"]["b"]["volume"] == 2
    mcp_tools._SESS.clear()  # reload from disk journal
    assert call("cad_state", session="s")["objects"]["b"]["volume"] == 2
