"""PARITY.md gap ops (cadkit/tools/advanced.py) + LLM queries (cadkit/tools/query.py)."""
import inspect

import pytest


def _o(m, k):
    return m.state()["objects"][k]


# ------------------------------------------------------------------ modelling gaps
def test_push_pull_refillets(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    info = m.run("push_pull", body="b", faces={"normal": "+x"}, distance=0.3, max_radius=0.15)
    st = _o(m, "b")
    assert info["refilleted"] == 4 and st["valid"] and st["faces"] == 10
    assert st["bbox"][1][0] == pytest.approx(0.8, abs=1e-6)
    assert info["diff"]["changed"]["b"]["bbox"]


def test_push_pull_all_edges_filleted(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={}, radius=0.05)
    f0 = _o(m, "b")["faces"]
    m.run("push_pull", body="b", faces={"normal": "+z"}, distance=0.2, max_radius=0.06)
    st = _o(m, "b")
    assert st["valid"] and st["faces"] == f0 and st["bbox"][1][2] == pytest.approx(0.7, abs=1e-6)


def test_boolean_fillet_rounds_seam(m):
    m.run("box", name="b", size=[1, 1, 0.2])
    m.run("cylinder", name="c", radius=0.2, height=0.3, at=[0, 0, 0.2])
    info = m.run("boolean_fillet", kind="union", target="b", tools=["c"], radius=0.03)
    st = _o(m, "b")
    assert st["valid"] and info["seam_edges"] >= 1 and "c" not in m.objects
    assert any(f.geom_type.name == "TORUS" for f in m.objects["b"].shape.faces())


def test_symmetrize(m):
    m.run("box", name="b", size=[1, 1, 1], at=[0.2, 0, 0])
    m.run("symmetrize", body="b", plane="YZ", keep="+")
    st = _o(m, "b")
    assert st["bbox"][0][0] == pytest.approx(-0.7) and st["bbox"][1][0] == pytest.approx(0.7)
    assert st["volume"] == pytest.approx(1.4, rel=1e-6)


def test_curve_network_follows_interior(m):
    pts = [[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]
    for i in range(4):
        m.run("line", name=f"e{i}", points=[pts[i], pts[(i + 1) % 4]])
    m.run("spline", name="crown", points=[[-0.9, 0, 0.3], [0, 0, 0.5], [0.9, 0, 0.3]])
    m.run("curve_network", name="s", boundary=["e0", "e1", "e2", "e3"], interior=["crown"])
    from cadkit.tools import query
    d = query.measure(m, "s", "crown")
    assert d["distance"] < 0.02
    assert m.objects["s"].shape.bounding_box().max.Z > 0.4


def test_offset_curve_on_face_plane_and_cylinder(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("line", name="l", points=[[-0.3, 0, 0.5], [0.3, 0, 0.5]])
    m.run("offset_curve_on_face", name="o", curve="l", face={"obj": "b", "faces": {"normal": "+z"}}, distance=0.1)
    c = m.objects["o"].shape
    assert abs(c.center().Y) == pytest.approx(0.1, abs=1e-4) and c.center().Z == pytest.approx(0.5, abs=1e-6)
    m.run("cylinder", name="cy", radius=0.3, height=1.0)
    m.run("circle", name="rim", radius=0.3, center=[0, 0], plane={"origin": [0, 0, 0.3], "normal": "z"})
    m.run("offset_curve_on_face", name="o2", curve="rim", face={"obj": "cy", "faces": {"geom": "cylinder"}},
          distance=0.1)
    e = m.objects["o2"].shape
    for t in (0.0, 0.3, 0.7):
        p = e.position_at(t)
        assert (p.X ** 2 + p.Y ** 2) ** 0.5 == pytest.approx(0.3, abs=1e-4)
        assert abs(p.Z - 0.3) == pytest.approx(0.1, abs=1e-3)


def test_draft_face_and_analysis(m):
    from cadkit.tools import query
    m.run("box", name="b", size=[1, 1, 1], align="min") if False else m.run("box", name="b", size=[1, 1, 1])
    a0 = query.draft_analysis(m, "b", "+z", 1.0)
    assert a0["counts"]["vertical_needs_draft"] == 4
    m.run("draft_face", body="b", faces={"geom": "plane", "normal": "+x"}, angle=3, pull="+z")
    a1 = query.draft_analysis(m, "b", "+z", 1.0)
    assert a1["counts"]["vertical_needs_draft"] == 3 and _o(m, "b")["valid"]


# ------------------------------------------------------------------ queries
def test_measure_and_curvature(m):
    from cadkit.tools import query
    m.run("box", name="b", size=[1, 2, 3])
    r = query.measure(m, {"obj": "b", "faces": {"normal": "+z"}}, {"obj": "b", "faces": {"normal": "-z"}})
    assert r["distance"] == pytest.approx(3) and r["angle_deg"] == pytest.approx(180)
    r = query.measure(m, {"obj": "b", "faces": {"normal": "+z"}}, {"obj": "b", "faces": {"normal": "+x"}})
    assert r["angle_deg"] == pytest.approx(90)
    assert query.measure(m, "b")["a"]["volume"] == pytest.approx(6)
    m.run("sphere", name="s", radius=0.5)
    k = query.curvature(m, {"obj": "s", "faces": {}})
    assert abs(k["k1"]) == pytest.approx(2, rel=1e-4) and abs(k["r2"]) == pytest.approx(0.5, rel=1e-4)


def test_deviation(m):
    from cadkit.tools import query
    m.run("box", name="a", size=[1, 1, 1])
    m.run("box", name="b", size=[1, 1, 1.02])
    d = query.deviation(m, "b", "a", samples=4000)
    assert d["hausdorff"] == pytest.approx(0.01, abs=1e-4) and d["a_to_b"]["mean"] < 0.01


def test_compare_to_ref(m, tmp_path):
    from PIL import Image, ImageDraw
    from cadkit.tools import query
    img = Image.new("RGB", (200, 200), "white")
    ImageDraw.Draw(img).rectangle([50, 50, 149, 149], fill="black")
    p = str(tmp_path / "ref.png")
    img.save(p)
    m.run("box", name="b", size=[1, 1, 1])
    r = query.compare_to_ref(m, p, "front", m_per_px=0.01, origin_px=[100, 100], out=str(tmp_path / "d.png"))
    assert r["iou"] > 0.97
    r2 = query.compare_to_ref(m, p, "front")  # scale-free
    assert r2["iou"] > 0.97 and r2["m_per_px"] == pytest.approx(0.01, rel=0.03)
    m.run("move", obj="b", by=[0.5, 0, 0])
    assert query.compare_to_ref(m, p, "front", m_per_px=0.01, origin_px=[100, 100])["iou"] < 0.4


def test_suggest_refs_are_verified(m):
    from cadkit.tools import query, resolve
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    s = query.suggest_refs(m, "b", near=[0.5, 0.5, 0], kind="faces", n=3)
    top = s["candidates"][0]
    assert top["geom"] == "cylinder" and top["stable_refs"]
    for c in s["candidates"]:
        for ref in c["stable_refs"] + [c["near_ref"]]:
            assert len(resolve(m, ref, "faces" if "faces" in ref else "edges")) == 1
    e = query.suggest_refs(m, "b", near=[0.5, 0, 0.5], kind="edges", n=2)
    assert e["candidates"]


def test_explain_failure(m):
    from cadkit.tools import query
    m.run("box", name="b", size=[1, 1, 0.1])
    r = query.explain_failure(m, "fillet", {"body": "b", "edges": {"parallel": "z"}, "radius": 2, "min_frac": 0.99})
    assert r["ok"] is False and r["refs"]["edges"]["count"] == 4 and any("shortest edge" in c for c in r["checks"])
    assert m.objects["b"].shape.volume == pytest.approx(0.1)  # untouched
    r = query.explain_failure(m, "filet", {})
    assert "fillet" in r["did_you_mean"]
    r = query.explain_failure(m, "fillet", {"body": "b", "edgs": {}, "radius": 0.01})
    assert "edgs" in r["unknown"] and "edges" in r["missing"]
    m.run("box", name="far", size=[0.1, 0.1, 0.1], at=[5, 0, 0])
    r = query.explain_failure(m, "boolean", {"kind": "cut", "target": "b", "tools": ["far"]})
    assert any("do not overlap" in c for c in r["checks"])


def test_state_diff_concise(m):
    i = m.run("box", name="b", size=[1, 1, 1])
    assert "b" in i["diff"]["added"]
    i = m.run("offset_face", body="b", faces={"normal": "+z"}, distance=0.1)
    ch = i["diff"]["changed"]["b"]
    assert ch["volume"]["delta"] == pytest.approx(0.1) and "faces" not in ch
    i = m.run("delete", obj="b")
    assert i["diff"]["removed"] == ["b"]


def test_examples_match_signatures():
    from cadkit.tools import OPS, describe_ops
    from cadkit.tools.examples import EXAMPLES
    assert set(EXAMPLES) <= set(OPS)
    missing = [k for k in OPS if k not in EXAMPLES and not k.startswith("debug_")]
    assert not missing, missing
    for k, ex in EXAMPLES.items():
        acc = set(inspect.signature(OPS[k]["fn"]).parameters)
        assert set(ex) <= acc, (k, set(ex) - acc)
    assert "example" in describe_ops()["fillet"]


def test_mcp_query_tools(tmp_path, monkeypatch):
    import asyncio
    import json
    import mcp_tools
    from mcp.server.mcpserver import MCPServer
    monkeypatch.setattr(mcp_tools, "SESS_DIR", str(tmp_path))
    monkeypatch.setenv("CADKIT_INPROC", "1")
    mcp_tools._SESS.clear()
    srv = MCPServer("t")
    mcp_tools.register(srv)
    tools = {t.name: t for t in asyncio.run(srv.list_tools())}
    assert {"cad_measure", "cad_suggest_refs", "cad_explain_failure", "cad_compare_to_ref", "cad_deviation",
            "cad_draft_analysis", "cad_curvature"} <= set(tools)
    assert "example params" in tools["op_fillet"].description

    def call(n, **a):
        r = asyncio.run(srv.call_tool(n, a))
        r = r.content if hasattr(r, "content") else r
        r = r[0] if isinstance(r, (list, tuple)) else r
        r = r[0] if isinstance(r, list) else r
        return json.loads(getattr(r, "text", r))
    call("cad_new", session="q")
    r = call("op_box", session="q", params={"name": "b", "size": [1, 1, 1]})
    assert "b" in r["info"]["diff"]["added"]
    assert call("cad_suggest_refs", session="q", obj="b", near=[0, 0, 1])["candidates"][0]["stable_refs"]
    assert call("cad_measure", session="q", a="b")["a"]["volume"] == 1
    assert call("cad_explain_failure", session="q", op="fillet", params={"body": "b", "radius": 0.1})["missing"]
