import math

import pytest

from cadkit.tools import ToolError


def test_line_arc_spline_lengths(m):
    m.run("line", name="l", points=[[0, 0], [1, 0], [1, 1]])
    m.run("arc", name="a", start=[0, 0], mid=[1, 1], end=[2, 0])
    m.run("spline", name="s", points=[[0, 0, 0], [1, 1, 0], [2, 0, 1]])
    st = m.state()["objects"]
    assert st["l"]["length"] == pytest.approx(2)
    assert st["a"]["length"] == pytest.approx(math.pi)
    assert st["s"]["length"] > 2.4


def test_rect_polygon_circle_closed(m):
    m.run("rectangle", name="r", width=2, height=1, corner_radius=0.2)
    m.run("polygon", name="p", sides=6, radius=1)
    m.run("circle", name="c", radius=1, center=[5, 0])
    st = m.state()["objects"]
    assert all(st[k]["closed"] for k in "rpc")
    assert st["r"]["length"] == pytest.approx(6 - 8 * 0.2 + 2 * math.pi * 0.2, rel=1e-6)
    assert st["p"]["length"] == pytest.approx(6, rel=1e-6)


def test_offset_and_fillet_curve(m):
    m.run("rectangle", name="r", width=2, height=1)
    m.run("offset_curve", name="o", curve="r", distance=-0.1, kind="intersection")
    m.run("fillet_curve", name="f", curve="r", radius=0.1)
    st = m.state()["objects"]
    assert st["o"]["length"] == pytest.approx(6 - 0.8, rel=1e-6)
    assert st["f"]["length"] < 6
    with pytest.raises(ToolError) as e:
        m.run("fillet_curve", name="bad", curve="r", radius=5)
    assert "keep r <" in e.value.hint


def test_regions_overlap_and_nested(m):
    m.run("rectangle", name="r", width=4, height=2)
    m.run("circle", name="c", radius=0.5)
    m.run("circle", name="c2", radius=0.5, center=[2, 0])  # straddles the rect's right edge
    info = m.run("regions", curves=["r", "c", "c2"])
    areas = sorted(r["area"] for r in info["regions"])
    assert len(areas) == 4  # rect minus holes, inner disk, two half-disks of c2
    assert sum(areas) == pytest.approx(8 + math.pi * 0.25 / 2, rel=1e-4)


def test_regions_open_curve_error(m):
    m.run("line", name="l", points=[[0, 0], [1, 0]])
    with pytest.raises(ToolError):
        m.run("regions", curves=["l"])


def test_project_curve(m):
    m.run("sphere", name="s", radius=1)
    m.run("circle", name="c", radius=0.3, plane={"origin": [0, 0, 2]})
    info = m.run("project_curve", name="pc", curve="c", body="s", direction="-z")
    assert info["pieces"] >= 1
    bb = m.state()["objects"]["pc"]["bbox"]
    assert bb[0][2] > 0.9  # landed on the top of the sphere
