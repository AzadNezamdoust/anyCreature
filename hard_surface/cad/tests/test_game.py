"""cadkit.game: tessellation (face ids, LOD budgets), UV metrics, curvature. Blender path covered by
test_game_blender (slow, opt-in: CADKIT_GAME_BLENDER=1)."""
import os

import numpy as np
import pytest

from cadkit.game import build_meshes, retess_to_budget, uv_report, curvature_from_normal

MODEL = """from cadkit import *
b = Box(40, 30, 20)
b = safe_fillet(b, b.edges().filter_by(Axis.Z), 4)
b = cut(b, Cylinder(5, 30), "hole")
PARTS = {"blk": (b, "#888888")}
UNITS = "mm"
TRI_BUDGET = 1200
"""


@pytest.fixture(scope="module")
def model(tmp_path_factory):
    d = tmp_path_factory.mktemp("m")
    p = d / "model.py"; p.write_text(MODEL)
    return p, d


def test_build_meshes_lods(model):
    p, d = model
    info = build_meshes(str(p), str(d / "m.npz"), (1.0, 0.5, 0.25))
    z = np.load(d / "m.npz")
    assert info["hi_tris"] > info["lods"][0]["tris"]
    for i, l in enumerate(info["lods"]):
        assert l["tris"] <= l["budget"] or i == 2  # coarsest may floor at B-rep minimum
    tr = [l["tris"] for l in info["lods"]]
    assert tr[0] >= tr[1] >= tr[2]
    nf = info["brep_faces"]["blk"]
    for pre in ("hi", "l0", "l1", "l2"):
        f = z[f"{pre}_f_0"]
        assert len(np.unique(f)) == nf, f"{pre}: every B-rep face survives"
    assert abs(float(z["scale"]) - 0.001) < 1e-12
    assert np.ptp(z["hi_v_0"][:, 0]) == pytest.approx(0.040, rel=1e-3)  # metres


def test_retess_budget_monotone(model):
    from cadkit.game.tess import load_model
    parts, _, _ = load_model(str(model[0]))
    _, t1, _ = retess_to_budget(parts, 2000)
    _, t2, _ = retess_to_budget(parts, 400)
    assert t2 <= t1


def test_uv_report_identity_and_stretch():
    P = np.array([[[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[1, 0, 0], [1, 1, 0], [0, 1, 0]]], float)
    UV = P[:, :, :2] * 0.5
    r = uv_report(P, UV, island=np.array([0, 0]), res=1024)
    assert r["stretch_mean"] == pytest.approx(1.0, abs=1e-6)
    assert r["texel_px_per_m"] == pytest.approx(512, rel=1e-6)
    assert r["texel_cv"] == pytest.approx(0, abs=1e-9)
    UV2 = UV.copy(); UV2[..., 0] *= 2
    assert uv_report(P, UV2)["stretch_mean"] == pytest.approx(2.0, rel=1e-6)


def test_uv_texel_cv_detects_mismatch():
    P = np.array([[[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[5, 0, 0], [6, 0, 0], [5, 1, 0]]], float)
    UV = np.array([[[0, 0], [.1, 0], [0, .1]], [[.5, .5], [.9, .5], [.5, .9]]])
    assert uv_report(P, UV, island=np.array([0, 1]))["texel_cv"] > 0.5


def test_curvature_flat_and_bump():
    flat = np.full((32, 32, 3), [0.5, 0.5, 1.0])
    assert np.allclose(curvature_from_normal(flat), 0.5)
    x = np.linspace(-1, 1, 64)
    nx = np.tile(0.3 * x, (64, 1))  # normals tilt outward along +x -> convex
    n = np.dstack([nx * 0.5 + 0.5, np.full_like(nx, 0.5), np.ones_like(nx)])
    assert curvature_from_normal(n)[32, 32] > 0.5


@pytest.mark.skipif(os.environ.get("CADKIT_GAME_BLENDER") != "1", reason="slow Blender end-to-end; set CADKIT_GAME_BLENDER=1")
def test_game_blender_end_to_end(model, tmp_path):
    from cadkit.game.pipeline import run
    rep = run(str(model[0]), str(tmp_path / "g"), "blk", res=256, quad=False, preview_res=128)
    assert rep["build"]["lods"]["LOD0"]["tris"] > 0
    assert os.path.exists(tmp_path / "g" / "maps" / "LOD0" / "n_tan.png")
    assert os.path.exists(tmp_path / "g" / "blk_LOD0.glb") and os.path.exists(tmp_path / "g" / "blk.fbx")
