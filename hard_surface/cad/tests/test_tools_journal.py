import json

import pytest

from cadkit.tools import Model, ToolError


def test_undo_redo_branch(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    m.undo()
    assert m.state()["objects"]["b"]["faces"] == 6
    m.redo()
    assert m.state()["objects"]["b"]["faces"] == 10
    m.undo()
    m.run("chamfer", body="b", edges={"parallel": "z"}, distance=0.1)  # new branch
    assert len(m.nodes) == 3 and m.nodes[2]["parent"] == 0


def test_set_param_replays_and_rolls_back(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    v0 = m.state()["objects"]["b"]["volume"]
    m.set_param(1, "radius", 0.2)
    v = m.state()["objects"]["b"]["volume"]
    assert v < v0
    with pytest.raises(ToolError):
        m.set_param(1, "edges", {"parallel": "z", "expect": 9})
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(v)


def test_json_roundtrip(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    m2 = Model.from_json(json.loads(json.dumps(m.to_json())))
    assert m2.state()["objects"]["b"]["volume"] == pytest.approx(m.state()["objects"]["b"]["volume"])


def test_failed_op_leaves_state(m):
    m.run("box", name="b", size=[1, 1, 1])
    with pytest.raises(ToolError) as e:
        m.run("boolean", kind="cut", target="b", tools=["nope"])
    assert "objects" in e.value.hint and len(m.nodes) == 1
