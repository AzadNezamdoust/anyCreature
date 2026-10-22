"""Class-A-lite: Gordon network surface on the 911 (L5) front fender + hood network, continuity report, zebra."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "regress"))


def test_911_fender_hood_gordon_smooth(tmp_path):
    import l5_fender_hood as N
    from cadkit.network import gordon_surface, zebra
    u, v, G = N.network()
    f, rep = gordon_surface(u, v)
    assert rep["max_dev"] < 0.5  # mm: surface passes through every section AND feature line
    z = zebra(f, png=str(tmp_path / "zebra.png"))
    assert z["kink"] < 5.0  # no crease / fold (was 31-54 before the end-node snap)
    assert os.path.exists(z["png"])


def test_gordon_accepts_mixed_orientation_and_degree():
    from build123d import Spline, Polyline, Vector
    from cadkit.network import gordon_surface
    import numpy as np

    def zf(x, y):
        return 0.1 * np.sin(x) + 0.05 * y * y

    us = [Spline(*[Vector(x, y, zf(x, y)) for y in np.linspace(-1, 1, 7)]) for x in (0, 1, 2, 3)]
    us[1] = Spline(*[Vector(1, y, zf(1, y)) for y in np.linspace(1, -1, 9)])        # reversed, other point count
    vs = [Spline(*[Vector(x, y, zf(x, y)) for x in np.linspace(0, 3, 6)]) for y in (-1, 0, 1)]
    vs[2] = Spline(*[Vector(x, 1, zf(x, 1)) for x in np.linspace(3, 0, 11)])        # reversed
    f, rep = gordon_surface(us, vs)
    assert rep["max_dev"] < 1e-3


def test_gordon_rejects_open_network():
    from build123d import Line
    from cadkit.network import gordon_surface
    from cadkit.ops import CadOpError
    us = [Line((0, 0, 0), (0, 1, 0)), Line((1, 0, 0), (1, 1, 0))]
    vs = [Line((0, 0, 0), (1, 0, 0)), Line((0, 1, 5), (1, 1, 5))]
    with pytest.raises(CadOpError, match="do not meet"):
        gordon_surface(us, vs)


def test_continuity_report_classes():
    from build123d import Box, Plane, Cylinder
    from cadkit.network import edge_continuity
    from cadkit.ops import safe_fillet
    b = Box(10, 10, 10)
    r = edge_continuity(b)
    assert r["summary"]["G0"] == 12  # sharp box edges
    fb = safe_fillet(b, b.edges().filter_by(lambda e: e.center().Z > 4.9), 2.0)
    r2 = edge_continuity(fb)
    assert r2["summary"]["G1"] + r2["summary"]["G2"] >= 4  # fillet joins tangent (circular blend: G1, not G2)
    # a smooth surface split in two: the cut edge is G2
    s = Cylinder(5, 10).split(Plane.XZ, keep=__import__("build123d").Keep.BOTH)
    from build123d import Compound
    from cadkit.network import sew
    parts = s if isinstance(s, (tuple, list)) else [s]
    side = [f for p in parts for f in p.faces() if f.geom_type.name == "CYLINDER"]
    sh = sew(side)
    rr = edge_continuity(sh)
    assert any(e["cls"] == "G2" for e in rr["edges"])


def test_class_a_lite_workflow_ops(m):
    """sections + feature lines -> network surface -> thicken -> solid, all as journal ops."""
    import l5_fender_hood as N
    G = N.grid() / 1000.0
    for i, row in enumerate(G):
        m.run("spline", name=f"s{i}", points=[list(p) for p in row])
    for k in range(G.shape[1]):
        m.run("spline", name=f"f{k}", points=[list(p) for p in G[:, k]])
    info = m.run("network_surface", name="skin", u_curves=[f"s{i}" for i in range(len(G))],
                 v_curves=[f"f{k}" for k in range(G.shape[1])])
    assert info["max_dev"] < 5e-4
    z = m.run("zebra", face="skin")
    assert z["kink"] < 5
    m.run("thicken", name="panel", face="skin", thickness=0.003)
    st = m.state()["objects"]["panel"]
    assert st["valid"] and st["volume"] > 0
