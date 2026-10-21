import math

import pytest


def test_extrude_both_sides_draft_thin(m):
    m.run("rectangle", name="sq", width=1, height=1)
    m.run("extrude", name="e", profile="sq", distance=1, distance2=0.5)
    bb = m.state()["objects"]["e"]["bbox"]
    assert bb[0][2] == pytest.approx(-0.5) and bb[1][2] == pytest.approx(1)
    m.run("extrude", name="d", profile="sq", distance=1, draft=10)
    assert m.state()["objects"]["d"]["volume"] < 1
    m.run("extrude", name="t", profile="sq", distance=1, thickness=0.1)
    assert m.state()["objects"]["t"]["volume"] == pytest.approx(1 - 0.64, rel=1e-3)


@pytest.mark.parametrize("mode,vol", [("union", 1.125), ("cut", 0.875), ("intersect", 0.125)])
def test_extrude_modes(m, mode, vol):
    m.run("box", name="b", size=[1, 1, 1], align="min")
    m.run("rectangle", name="r", width=0.5, height=0.5, center=[1, 0.25])
    m.run("extrude", name="x", profile="r", distance=1, mode=mode, target="b")
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(vol, rel=1e-6)


def test_revolve(m):
    m.run("rectangle", name="r", width=0.2, height=1, center=[1, 0], plane="XZ")
    m.run("revolve", name="ring", profile="r", axis_dir="z")
    assert m.state()["objects"]["ring"]["volume"] == pytest.approx(2 * math.pi * 1 * 0.2, rel=1e-4)


def test_sweep_and_pipe(m):
    m.run("spline", name="sp", points=[[0, 0, 0], [0.3, 0, 0.6], [1, 0, 1]], tangents=["z", "x"])
    m.run("pipe", name="p", path="sp", radius=0.05, inner_radius=0.03)
    st = m.state()["objects"]
    assert st["p"]["valid"]
    assert st["p"]["volume"] == pytest.approx(math.pi * (0.05 ** 2 - 0.03 ** 2) * st["sp"]["length"], rel=0.02)
    m.run("circle", name="prof", radius=0.05)
    m.run("sweep", name="sw", profile="prof", path="sp")
    assert m.state()["objects"]["sw"]["valid"]


def test_loft_plain_and_guided(m):
    m.run("rectangle", name="a", width=1, height=1)
    m.run("circle", name="b", radius=0.4, plane={"origin": [0, 0, 1]})
    m.run("loft", name="l", profiles=["a", "b"])
    assert m.state()["objects"]["l"]["valid"]
    m.run("circle", name="c0", radius=0.2)
    m.run("circle", name="c1", radius=0.1, plane={"origin": [0.5, 0, 1], "normal": "x"})
    m.run("spline", name="g", points=[[0, 0, 0], [0, 0, 0.6], [0.5, 0, 1]], tangents=["z", "x"])
    m.run("loft", name="lg", profiles=["c0", "c1"], guide="g")
    st = m.state()["objects"]["lg"]
    assert st["volume"] > 0 and st["bbox"][1][0] > 0.45
