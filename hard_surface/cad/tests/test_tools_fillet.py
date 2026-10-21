import pytest

from cadkit.tools import ToolError


def test_constant_fillet_and_chamfer(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    assert m.state()["objects"]["b"]["faces"] == 10
    m.run("chamfer", body="b", edges={"of_faces": {"normal": "+z"}}, distance=0.05)
    assert m.state()["objects"]["b"]["valid"]


def test_chamfer_two_dist_angle(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("chamfer", body="b", edges={"parallel": "x", "first": 1}, distance=0.1, distance2=0.2)
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(1 - 0.01, rel=1e-6)
    m.run("box", name="c", size=[1, 1, 1])
    m.run("chamfer", body="c", edges={"parallel": "x", "first": 1}, distance=0.1, angle=30)
    assert m.state()["objects"]["c"]["valid"] and m.state()["objects"]["c"]["faces"] == 7


def test_fillet_auto_reduce_and_hint(m):
    m.run("box", name="b", size=[1, 1, 0.1])
    m.run("fillet", body="b", edges={"parallel": "x"}, radius=0.06)  # > half thickness -> reduced
    assert m.state()["objects"]["b"]["valid"]
    m.run("box", name="c", size=[1, 1, 0.1])
    with pytest.raises(ToolError) as e:
        m.run("fillet", body="c", edges={"parallel": "x"}, radius=0.9, min_frac=0.9)
    assert e.value.data.get("max_feasible") is not None


def test_variable_fillet(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("variable_fillet", body="b", edges={"parallel": "z", "first": 1}, radii=[0.05, 0.2])
    m.run("box", name="c", size=[1, 1, 1])
    m.run("variable_fillet", body="c", edges={"parallel": "z", "first": 1},
          radii=[[0, 0.1], [0.5, 0.25], [1, 0.1]])
    st = m.state()["objects"]
    assert st["b"]["valid"] and st["c"]["valid"] and st["b"]["faces"] == 7


def test_smooth_fillet(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1, shape="smooth")
    assert m.state()["objects"]["b"]["valid"]


def test_tangent_chain_fillet(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    m.run("fillet", body="b", edges={"of_faces": {"normal": "+z"}, "near": [0.5, 0, 0.5],
                                     "tangent_chain": True}, radius=0.05)
    st = m.state()["objects"]["b"]
    assert st["valid"] and st["faces"] > 10
