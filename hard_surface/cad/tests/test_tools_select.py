import pytest

from cadkit.tools import ToolError, select, tangent_chain


def _holed(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("cylinder", name="c", radius=0.2, height=1, at=[0, 0, 0])
    m.run("boolean", kind="cut", target="b", tools=["c"])


def test_by_normal_geom_pick(m):
    _holed(m)
    assert select(m, {"obj": "b", "faces": {"geom": "cylinder"}})["count"] == 1
    assert select(m, {"obj": "b", "faces": {"normal": "-z"}})["count"] == 1
    assert select(m, {"obj": "b", "faces": {"pick": "max", "axis": "x"}})["items"][0]["center"][0] == 0.5
    assert select(m, {"obj": "b", "edges": {"geom": "circle"}})["count"] == 2


def test_loops(m):
    _holed(m)
    assert select(m, {"obj": "b", "edges": {"of_faces": {"normal": "+z"}, "loop": "outer"}})["count"] == 4
    assert select(m, {"obj": "b", "edges": {"of_faces": {"normal": "+z"}, "loop": "inner"}})["count"] == 1


def test_tags_reresolve_after_edit(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("tag", tag="top", ref={"obj": "b", "faces": {"pick": "max", "axis": "z"}})
    m.run("offset_face", body="b", faces={"tag": "top"}, distance=0.5)
    m.set_param(0, "size", [2, 1, 1])  # replay: the tag re-resolves on the new geometry
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(3, rel=1e-6)


def test_expect_error(m):
    m.run("box", name="b", size=[1, 1, 1])
    with pytest.raises(ToolError) as e:
        m.run("fillet", body="b", edges={"parallel": "z", "expect": 2}, radius=0.1)
    assert "expected 2" in str(e.value)


def test_tangent_chain(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    s = m.objects["b"].shape
    top = [e for e in s.edges() if e.center().Z > 0.49]
    assert len(tangent_chain(s, top[:1])) == 8
