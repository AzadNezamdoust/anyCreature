import math

import pytest


def test_box_cyl_cone_sphere_torus(m):
    m.run("box", name="b", size=[1, 2, 3])
    m.run("cylinder", name="c", radius=0.5, height=2, at=[3, 0, 0])
    m.run("cone", name="k", radius1=0.5, radius2=0.1, height=1, at=[6, 0, 0])
    m.run("sphere", name="s", radius=0.5, at=[9, 0, 0])
    m.run("torus", name="t", major=1, minor=0.2, at=[12, 0, 0])
    st = m.state()["objects"]
    assert st["b"]["volume"] == pytest.approx(6)
    assert st["c"]["volume"] == pytest.approx(math.pi * 0.25 * 2, rel=1e-6)
    assert st["k"]["volume"] == pytest.approx(math.pi / 3 * (0.25 + 0.05 + 0.01), rel=1e-4)
    assert st["s"]["volume"] == pytest.approx(4 / 3 * math.pi * 0.125, rel=1e-4)
    assert st["t"]["volume"] == pytest.approx(2 * math.pi ** 2 * 1 * 0.04, rel=1e-4)
    assert all(o["valid"] for o in st.values())


def test_box_align_and_cplane(m):
    m.run("cplane", cname="side", origin=[0, 0, 1], normal="x")
    m.run("box", name="b", size=[1, 1, 1], align="min", plane="side")
    bb = m.state()["objects"]["b"]["bbox"]
    assert bb[0][0] == pytest.approx(0) and bb[1][0] == pytest.approx(1)


def test_cplane_from_face(m):
    m.run("box", name="b", size=[1, 1, 1])
    info = m.run("cplane", cname="top", face={"obj": "b", "faces": {"normal": "+z"}})
    assert info["origin"][2] == pytest.approx(0.5) and info["normal"][2] == pytest.approx(1)


def test_prism_from_region(m):
    m.run("circle", name="c", radius=1)
    m.run("regions", curves=["c"])
    m.run("prism", name="p", region="region1", height=2)
    assert m.state()["objects"]["p"]["volume"] == pytest.approx(2 * math.pi, rel=1e-6)
