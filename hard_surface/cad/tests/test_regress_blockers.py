"""Phase-A blockers found by the real-product replicas (L3 drill, L4 Xbox). Each reproduces the original failure."""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "regress"))


def test_isolation_child_crash_and_hang_kill_only_child():
    from build123d import Box
    from cadkit import isolate
    w = isolate.OpWorker()
    b = Box(10, 10, 10)
    with pytest.raises(isolate.IsolationFailure, match="crashed"):
        w.run("debug_crash", b, b.edges()[:1], 1.0, 60)
    t = time.time()
    with pytest.raises(isolate.IsolationFailure, match="timed out"):
        w.run("debug_hang", b, b.edges()[:1], 1.0, 3)
    assert time.time() - t < 30
    r = w.run("fillet", b, b.edges()[:4], 1.0, 60)  # child restarted lazily, parent unaffected
    assert r is not None and r.is_valid and r.volume < 1000
    w.kill()


def test_isolated_edge_indices_survive_brep_roundtrip():
    from build123d import Box, Cylinder
    from cadkit import isolate
    b = Box(10, 10, 10) - Cylinder(2, 20)
    es = b.edges().filter_by(lambda e: e.geom_type.name == "CIRCLE")
    w = isolate.OpWorker()
    r = w.run("fillet", b, es, 0.5, 60)
    w.kill()
    ref = b.fillet(0.5, es)
    assert r.volume == pytest.approx(ref.volume, rel=1e-9)


@pytest.mark.parametrize("which", ["HOUSE", "GRIP"])
def test_l3_periodic_spline_rim_fillet_no_crash(which, monkeypatch):
    """Was: 0xc0000374 heap corruption (HOUSE r14) / >600 s hang (GRIP r9). Root cause: r > tightest radius of
    curvature of the profile (6.4 / 5.6) -> no rolling-ball solution, OCCT crashes instead of failing."""
    import l3_profiles
    from cadkit.ops import CadOpError, safe_fillet, edge_curvature_limit
    monkeypatch.setenv("CADKIT_OP_BUDGET", "240")
    s, rim, r = l3_profiles.slab(getattr(l3_profiles, which))
    lim = edge_curvature_limit(rim)
    assert lim < r  # the capture still has the infeasible radius
    t = time.time()
    with pytest.raises(CadOpError, match="tightest radius of curvature"):  # clear failure, no crash, no shrink
        safe_fillet(s, rim, r, label=which)
    assert time.time() - t < 30
    out = safe_fillet(s, rim, 0.85 * lim, label=which + " feasible")  # feasible radius applies exactly
    assert out.is_valid and out.volume < s.volume


def test_l4_r7_centre_rise_perimeter_fillet():
    """Was: OCCT segfault in the all-edge perimeter round of the r7 Xbox body (CENTRE_RISE=8)."""
    import l4_body
    from cadkit.ops import safe_fillet
    b, r = l4_body.build(8.0)
    from cadkit.ops import CadOpError
    t = time.time()
    try:  # must either apply exactly r or fail loudly - never crash the process, never shrink silently
        out = safe_fillet(b, b.edges(), r, label="l4 r7 perimeter")
        assert out.is_valid and 0.9 * b.volume < out.volume < b.volume
    except CadOpError as e:
        assert "r=5" in str(e)
    assert time.time() - t < 600


def _l4_body0():
    from build123d import Shape
    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools
    from OCP.TopoDS import TopoDS_Shape
    sh = TopoDS_Shape()
    BRepTools.Read_s(sh, os.path.join(os.path.dirname(__file__), "regress", "l4_body0.brep"), BRep_Builder())
    return Shape.cast(sh).solids()[0]  # replica/L4 r6 BODY0 (lofted + perimeter-rounded Xbox body), mm


def test_l4_shell_exact_not_manifold():
    """Was: robust_shell burned ~240 s on arc/thick strategies then fell to Manifold (faceted mesh body)."""
    from cadkit.ops import LOG
    from cadkit.surf import robust_shell
    b = _l4_body0()
    t = time.time()
    r = robust_shell(b, 2.0, [], False, label="l4 shell")
    assert time.time() - t < 120
    rec = [o for o in LOG if o.get("op") == "shell"][-1]
    assert rec["method"] == "simple" and r.is_valid
    assert 0.1 * b.volume < r.volume < 0.3 * b.volume
    assert all(f.geom_type.name != "PLANE" or f.area > 1e-3 for f in r.faces())  # not triangle soup
    assert len(r.faces()) < 100


@pytest.mark.skipif(os.environ.get("CADKIT_SLOW") != "1", reason="~10 min (4 OCCT attempts x 130 s)")
def test_l4_underside_skin_cut_not_silent_noop():
    """Was: cut(BODY0, BODY0 shifted +0.6 z) returned a VALID body with the FULL volume (no-op) -> silent wrong
    geometry. Now the no-op is rejected; without the mesh fallback it fails loudly."""
    from build123d import Pos
    from cadkit.ops import CadOpError, safe_boolean
    b = _l4_body0()
    try:
        r = safe_boolean("cut", b, Pos(0, 0, 0.6) * b, "l4 underskin", allow_mesh=False)
        assert r.volume < 0.2 * b.volume
    except CadOpError:
        pass
