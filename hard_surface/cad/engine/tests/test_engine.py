"""pytest engine/tests -q   (venv_cad python). Needs engine/bin/cadengine.exe (engine/build.bat)."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAD)
sys.path.insert(0, HERE)

from cadkit.engine_client import Engine, EngineError  # noqa: E402
from cases import CASES  # noqa: E402
import equiv  # noqa: E402


@pytest.fixture(scope="module")
def eng():
    e = Engine(env={"CADENGINE_DEBUG_OPS": "1", "CADENGINE_OP_TIMEOUT": "3"})
    yield e
    e.close()


@pytest.mark.parametrize("name", list(CASES))
def test_equivalent_to_python_kit(eng, name):
    po, pe, _ = equiv.run_py(CASES[name])
    co, ce, _ = equiv.run_cpp(eng, CASES[name], "eq_" + name)
    bad = [r for r in equiv.compare(po, co) if not r["ok"]]
    assert not bad, bad
    assert [e[:2] for e in pe] == [e[:2] for e in ce]


def test_fillet_too_big_fails_with_max_radius(eng):
    eng.new("f")
    eng.run("box", session="f", name="b", size=[1, 2, 3])
    with pytest.raises(EngineError) as ei:
        eng.run("fillet", session="f", body="b", edges={"parallel": "z"}, radius=0.9)
    assert 0.4 < ei.value.data["max_feasible"] < 0.5
    assert eng.state("f")["objects"]["b"]["faces"] == 6  # unchanged, no silent shrink


def test_boolean_noop_is_error(eng):
    eng.new("n")
    eng.run("box", session="n", name="a", size=[1, 1, 1])
    eng.run("box", session="n", name="b", size=[1, 1, 1], at=[5, 0, 0])
    r = eng.run("boolean", session="n", kind="cut", target="a", tools=["b"])  # disjoint: legit no change
    assert abs(r["volume"] - 1) < 1e-9


def test_edit_replays_only_from_edited_op_and_cache_on_revert(eng):
    eng.new("c")
    eng.run("box", session="c", name="b", size=[1, 1, 1])
    eng.run("fillet", session="c", body="b", edges={"parallel": "z"}, radius=0.1)
    eng.run("box", session="c", name="d", size=[0.2, 0.2, 0.2], at=[3, 0, 0])
    r = eng.set_param(2, "size", [0.3, 0.3, 0.3], session="c")
    assert r["replayed_ops"] == 1
    r = eng.set_param(0, "size", [1.2, 1, 1], session="c")
    assert r["replayed_ops"] == 3
    r = eng.set_param(0, "size", [1, 1, 1], session="c")
    assert r["replayed_ops"] == 0  # whole chain (size 1, fillet, d 0.3) was computed by the first edit: cache hit


def test_crash_and_hang_isolated(eng):
    eng.new("x")
    eng.run("box", session="x", name="b", size=[1, 1, 1])
    with pytest.raises(EngineError) as ei:
        eng.run("debug_crash", session="x", how="segv")
    assert ei.value.crashed and "crashed" in str(ei.value)
    with pytest.raises(EngineError) as ei:
        eng.run("debug_crash", session="x", how="hang")
    assert "timed out" in str(ei.value)
    eng.run("fillet", session="x", body="b", edges={"parallel": "z"}, radius=0.1)  # worker restarted
    assert eng.state("x")["objects"]["b"]["faces"] == 10
    assert eng.stats("x")["isolation"]["crashes"] >= 1


def test_render_iou_deviation(eng, tmp_path):
    eng.new("g")
    eng.run("box", session="g", name="b", size=[1, 0.5, 0.3])
    eng.run("fillet", session="g", body="b", edges={"parallel": "z"}, radius=0.1)
    r = eng.render(str(tmp_path / "s.png"), session="g", modes=["clay", "zebra", "curvature"], res=128)
    assert os.path.exists(r["path"]) and r["size"] == [384, 768]
    m = str(tmp_path / "m.png")
    eng.render(m, session="g", views=["top"], mode="mask", cols=1, res=256)
    eng.register_ref("t", m, view="top")
    assert eng.iou(session="g")["refs"]["t"]["iou"] > 0.98
    eng.run("duplicate", session="g", name="c", source="b")
    eng.run("move", session="g", obj="c", by=[0, 0, 0.01])
    d = eng.deviation("b", "c", session="g")
    assert 0.009 < d["a_to_b"]["max"] < 0.011
