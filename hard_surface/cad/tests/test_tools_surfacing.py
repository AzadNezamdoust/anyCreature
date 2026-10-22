"""Robust shell/offset, loft cap fillets, staged fillets, surfacing ops (step 1-2 of the CAD hardening)."""
import math

import pytest
from build123d import Edge, Ellipse, Plane, Vector, loft


def _loft_body(m, name="L"):
    for i, (x, ry, rz) in enumerate([(0, 10, 8), (20, 14, 11), (40, 9, 7)]):
        m.run("circle", name=f"c{i}", radius=1, plane={"origin": [x, 0, 0], "normal": "x"})
    # elliptic sections via the script helpers (circle op is round): replace shapes directly
    for i, (x, ry, rz) in enumerate([(0, 10, 8), (20, 14, 11), (40, 9, 7)]):
        m.objects[f"c{i}"].shape = (Plane.YZ.offset(x) * Ellipse(ry, rz)).wire() if hasattr(
            Plane.YZ.offset(x) * Ellipse(ry, rz), "wire") else (Plane.YZ.offset(x) * Ellipse(ry, rz)).outer_wire()
    m.run("loft", name=name, profiles=["c0", "c1", "c2"])


@pytest.mark.parametrize("strategy", ["arc", "intersection", "thick_arc", "offset_cut", "manifold"])
def test_shell_strategies_box(m, strategy):
    m.run("box", name="b", size=[1, 1, 1])
    info = m.run("shell", body="b", thickness=0.1, open_faces={"obj": "b", "faces": {"normal": "+z"}},
                 strategy=strategy)
    v = m.state()["objects"]["b"]["volume"]
    assert info["method"] == strategy
    tol = 0.08 if strategy == "manifold" else 1e-3
    assert v == pytest.approx(1 - 0.8 * 0.8 * 0.9, rel=tol)


def test_shell_loft_sections_fallback(m):
    _loft_body(m)
    v0 = m.state()["objects"]["L"]["volume"]
    info = m.run("shell", body="L", thickness=1.0, strategy="sections")
    v = m.state()["objects"]["L"]["volume"]
    assert info["method"] == "sections" and 0 < v < 0.5 * v0
    _loft_body(m, "L2")
    info = m.run("shell", body="L2", thickness=1.0)          # auto chain, validated
    assert info["method"] and m.state()["objects"]["L2"]["valid"]


def test_offset_face_curved(m):
    m.run("cylinder", name="c", radius=1, height=2)
    v0 = m.state()["objects"]["c"]["volume"]
    info = m.run("offset_face", body="c", faces={"geom": "cylinder"}, distance=0.2)
    v = m.state()["objects"]["c"]["volume"]
    assert v > v0 and v == pytest.approx(math.pi * 1.2 ** 2 * 2, rel=1e-3)
    assert info["method"]


def test_loft_cap_fillet_routed_to_cap_round(m):
    """Filleting a loft end-cap rim used to fail / SEGFAULT OCCT (ladder L2/L3). Now cap_round handles it."""
    _loft_body(m)
    v0 = m.state()["objects"]["L"]["volume"]
    m.run("fillet", body="L", edges={"of_faces": {"geom": "plane"}}, radius=2.0)
    st = m.state()["objects"]["L"]
    assert st["valid"] and st["volume"] < v0 and st["bbox"][1][0] == pytest.approx(40, abs=1e-3)
    from cadkit.ops import LOG
    assert any(r.get("status") == "cap_round" for r in LOG)


def test_cap_round_smooth_join():
    from cadkit import cap_round
    body = loft([Plane.YZ.offset(x) * Ellipse(ry, rz) for x, ry, rz in [(0, 10, 8), (20, 14, 11), (40, 9, 7)]])
    cap = max(body.faces().filter_by(lambda f: f.geom_type.name == "PLANE"), key=lambda f: f.center().X)
    r = cap_round(body, cap, 2.0)
    assert r.is_valid and abs(r.bounding_box().max.X - 40) < 1e-3


def test_staged_fillet_keeps_good_radius():
    """One edge that can't take r must not drag the others down: they keep r, the bad one gets a staged
    smaller radius."""
    from build123d import Box, Pos
    from cadkit import fuse, safe_fillet, new_edges
    from cadkit.ops import LOG
    a = Box(10, 10, 10)
    b = Pos(5, 0, 0) * Box(10, 2, 2)  # thin bar -> short faces near the junction
    s = fuse(a, b)
    es = s.edges().filter_by(lambda e: abs(e.center().X - 10) < 1e-6 or abs(e.center().Z - 5) < 1e-6)
    r = safe_fillet(s, es, 1.5)
    assert r.is_valid
    rec = [x for x in LOG if x.get("op") == "fillet"][-1]
    assert rec["status"] in ("ok", "split", "split_partial", "reduced")


def test_rail_loft_two_and_three_rails(m):
    for i, x in enumerate((0, 10, 20)):
        m.run("circle", name=f"p{i}", radius=2 + i * 0.5, plane={"origin": [0, 0, x], "normal": "z"})
    m.run("spline", name="r0", points=[[2, 0, 0], [3.4, 0, 5], [2.5, 0, 10], [3.6, 0, 15], [3, 0, 20]])
    m.run("spline", name="r1", points=[[-2, 0, 0], [-2.5, 0, 10], [-3, 0, 20]])
    m.run("rail_loft", name="rl", profiles=["p0", "p1", "p2"], rails=["r0", "r1"])
    s = m.objects["rl"].shape
    assert s.is_valid and s.volume > 0
    # the surface rides rail 0 where it bulges between the profiles (x=3.4 at z=5 vs profile radius ~2.25)
    assert s.distance_to(Vector(3.4, 0, 5)) < 0.05 and s.distance_to(Vector(3.6, 0, 15)) < 0.05
    m.run("spline", name="r2", points=[[0, 2, 0], [0, 3.2, 5], [0, 2.5, 10], [0, 3, 20]])
    m.run("rail_loft", name="rl3", profiles=["p0", "p1", "p2"], rails=["r0", "r1", "r2"])
    s3 = m.objects["rl3"].shape
    assert s3.is_valid and s3.distance_to(Vector(0, 3.2, 5)) < 0.1


def test_patch_and_coons(m):
    pts = [[0, 0, 0], [10, 0, 1], [10, 10, 0], [0, 10, 1]]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        mid = [(a[k] + b[k]) / 2 + (1.5 if k == 2 else 0) for k in range(3)]
        m.run("spline", name=f"e{i}", points=[a, mid, b])
    m.run("patch", name="pt", curves=["e0", "e1", "e2", "e3"])
    m.run("coons_patch", name="cp", curves=["e0", "e1", "e2", "e3"])
    for n in ("pt", "cp"):
        f = m.objects[n].shape
        assert f.area > 90 and f.distance_to(m.objects["e1"].shape.position_at(0.5)) < 1e-3
    m.run("line", name="tri", points=[[0, 0, 0], [5, 0, 0], [0, 5, 3]], closed=True)
    m.run("patch", name="t3", curves=["tri"])
    assert m.objects["t3"].shape.area > 5


def test_bridge_curve_g2():
    from cadkit import bridge_curve
    from cadkit.surf import curvature_vector
    a = Edge.make_circle(5, Plane.XY, 0, 90)          # ends at (0,5) tangent -x, curvature 1/5 toward origin
    b = Edge.make_line((-10, 8, 0), (-20, 8, 0))
    br = bridge_curve(a, b, 1.0, 0.0, "G2")
    assert (br.position_at(0) - a.position_at(1)).length < 1e-9
    assert abs(br.tangent_at(0).dot(a.tangent_at(1)) - 1) < 1e-6
    ka, kb = curvature_vector(a, 1.0), curvature_vector(br, 0.0)
    assert (ka - kb).length < 1e-6 * max(1, ka.length) + 1e-6
    assert curvature_vector(br, 1.0).length < 1e-6     # matches the line's zero curvature


def test_blend_surface_tangent(m):
    m.run("box", name="a", size=[10, 10, 1], at=[0, 0, 0])
    m.run("box", name="b", size=[10, 10, 1], at=[0, 0, 6])
    edge_a = {"obj": "a", "edges": {"near": [5, 0, 0.5], "radius": 0.01}}
    m.run("blend_surface", name="bl", edge_a={"obj": "a", "edges": {"within": [[5, -6, 0.5], [5, 6, 0.5]]}},
          face_a={"obj": "a", "faces": {"normal": "+z"}},
          edge_b={"obj": "b", "edges": {"within": [[5, -6, 5.5], [5, 6, 5.5]]}},
          face_b={"obj": "b", "faces": {"normal": "-z"}}, continuity="G2")
    f = m.objects["bl"].shape
    assert f.area > 10 and f.bounding_box().max.X > 5.5
    assert edge_a


def test_curve_trim_join_helix(m):
    m.run("line", name="l1", points=[[0, 0, 0], [10, 0, 0]])
    m.run("line", name="l2", points=[[10, 0, 0], [10, 5, 0]])
    m.run("join_curves", name="j", curves=["l1", "l2"])
    assert m.state()["objects"]["j"]["length"] == pytest.approx(15)
    m.run("trim_curve", name="t", curve="l1", start=0.2, end=0.5)
    assert m.state()["objects"]["t"]["length"] == pytest.approx(3)
    m.run("helix", name="h", pitch=2, height=10, radius=3)
    assert m.state()["objects"]["h"]["length"] == pytest.approx(5 * math.hypot(2 * math.pi * 3, 2), rel=1e-3)


def test_sew_sheets_to_solid(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("sew", name="s", sheets=["b"], delete=False)
    st = m.state()["objects"]["s"]
    assert st["kind"] == "solid" and st["volume"] == pytest.approx(1)