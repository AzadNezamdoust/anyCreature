import pytest

from cadkit.tools import ToolError


@pytest.mark.parametrize("kind,vol,keep", [("union", 1.5, False), ("cut", 0.5, True), ("intersect", 0.5, False)])
def test_boolean(m, kind, vol, keep):
    m.run("box", name="a", size=[1, 1, 1], align="min")
    m.run("box", name="b", size=[1, 1, 1], at=[0.5, 0, 0], align="min")
    m.run("boolean", kind=kind, target="a", tools=["b"], keep_tools=keep)
    assert m.state()["objects"]["a"]["volume"] == pytest.approx(vol, rel=1e-6)
    assert ("b" in m.objects) == keep


def test_boolean_multi_tool_coplanar(m):
    m.run("box", name="a", size=[2, 1, 1], align="min")
    m.run("box", name="t1", size=[0.2, 1, 0.2], at=[0.2, 0, 0.8], align="min")  # coplanar top + sides
    m.run("box", name="t2", size=[0.2, 1, 0.2], at=[1.2, 0, 0.8], align="min")
    m.run("boolean", kind="cut", target="a", tools=["t1", "t2"])
    assert m.state()["objects"]["a"]["volume"] == pytest.approx(2 - 0.08, rel=1e-6)


def test_boolean_bad_kind(m):
    m.run("box", name="a", size=[1, 1, 1])
    m.run("box", name="b", size=[1, 1, 1])
    with pytest.raises(ToolError):
        m.run("boolean", kind="xor", target="a", tools=["b"])
