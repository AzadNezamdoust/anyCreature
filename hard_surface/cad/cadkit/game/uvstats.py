"""Pure-numpy UV quality metrics + normal-map curvature (no Blender; unit-testable)."""
from __future__ import annotations

import numpy as np


def _tri_areas(P):
    return 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=-1)


def uv_report(P, UV, island=None, res=2048):
    """P: (n,3,3) triangle corners in metres, UV: (n,3,2), island: (n,) island id per tri.
    Returns texel density (px/m) stats, stretch (area-weighted singular-value ratio), UV coverage."""
    P, UV = np.asarray(P, "f8"), np.asarray(UV, "f8")
    a3 = _tri_areas(P)
    uv3 = np.concatenate([UV, np.zeros(UV.shape[:2] + (1,))], -1)
    a2 = _tri_areas(uv3)
    ok = (a3 > 1e-14) & (a2 > 1e-14)
    # per-tri Jacobian singular values (3D -> UV)
    e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
    l1 = np.linalg.norm(e1, axis=1) + 1e-30
    x = e1 / l1[:, None]
    n = np.cross(e1, e2)
    y = np.cross(n, x)
    y /= np.linalg.norm(y, axis=1)[:, None] + 1e-30
    q = np.stack([np.stack([l1, np.zeros_like(l1)], 1), np.stack([(e2 * x).sum(1), (e2 * y).sum(1)], 1)], 1)  # local 2D
    u = np.stack([UV[:, 1] - UV[:, 0], UV[:, 2] - UV[:, 0]], 1)
    J = np.zeros((len(P), 2, 2))
    det = q[:, 0, 0] * q[:, 1, 1] - q[:, 0, 1] * q[:, 1, 0]
    good = ok & (np.abs(det) > 1e-20)
    qi = np.linalg.inv(np.where(good[:, None, None], q, np.eye(2)))
    J = np.einsum("nij,njk->nik", qi, u)  # rows: local basis -> uv
    s = np.linalg.svd(J, compute_uv=False)
    ratio = np.where(good, s[:, 0] / np.maximum(s[:, 1], 1e-12), 1.0)
    w = np.where(good, a3, 0)
    dens = np.sqrt(np.where(good, a2 / np.maximum(a3, 1e-30), 0)) * res  # px per metre
    rep = {"uv_coverage": float(a2[ok].sum()),
           "stretch_mean": float((ratio * w).sum() / max(w.sum(), 1e-30)),
           "stretch_p95": float(np.percentile(ratio[good], 95)) if good.any() else 1.0,
           "flipped_frac": float(w[(u[:, 0, 0] * u[:, 1, 1] - u[:, 0, 1] * u[:, 1, 0]) * np.sign(det) < 0].sum() / max(w.sum(), 1e-30))}
    if island is not None:
        island = np.asarray(island)
        ids = np.unique(island[good])
        d = np.array([np.sqrt(a2[good & (island == i)].sum() / a3[good & (island == i)].sum()) * res for i in ids])
        wi = np.array([a3[good & (island == i)].sum() for i in ids])
        mu = float((d * wi).sum() / wi.sum())
        rep.update(islands=int(len(ids)), texel_px_per_m=mu,
                   texel_cv=float(np.sqrt((wi * (d - mu) ** 2).sum() / wi.sum()) / mu))
    else:
        mu = float((dens * w).sum() / max(w.sum(), 1e-30))
        rep.update(texel_px_per_m=mu)
    return rep


def curvature_from_normal(n_rgb, strength=4.0):
    """Tangent-space normal map (H,W,3 in 0..1) -> curvature map (0.5 flat, >0.5 convex, <0.5 concave)."""
    n = np.asarray(n_rgb, "f4")[..., :3] * 2 - 1
    dx = np.gradient(n[..., 0], axis=1)
    dy = np.gradient(n[..., 1], axis=0)
    c = dx - dy  # image rows run top->bottom while tangent V runs up
    # suppress UV-island borders (big jumps) so seams do not read as edges
    c = np.where(np.abs(c) > 0.5, 0, c)
    return np.clip(0.5 + strength * c, 0, 1)
