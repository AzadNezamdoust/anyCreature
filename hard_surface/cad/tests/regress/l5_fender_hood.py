"""911 (992) front fender + hood region network from replica/L5 (refdata side trace + model.py ST hood stations,
half_pts hood branch). u-curves = full-width upper sections (fender side -> crown -> hood -> other side),
v-curves = feature lines through the same section points along X. mm."""
import os
import sys

import numpy as np
from build123d import Spline, Vector

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "replica", "L5"))
import refdata as R  # noqa: E402

WF_HALF, HOOD_DROP = 912.0, 38.0
ST = [(-2131, 815, 150, 410), (-1965, 870, 140, 430), (-1836, 895, 142, 440), (-1580, WF_HALF - 4, 150, 455),
      (R.X_AF, WF_HALF, 160, 470), (-1050, WF_HALF - 4, 162, 480), (-925, WF_HALF - 8, 163, 485)]


def top_mm(x):
    xs, zs = zip(*sorted(R.side_poly_mm(R.SIDE_TOP_PX)))
    return float(np.interp(x, xs, zs))


def half_upper(x, w, zb, zw):
    zf = top_mm(x)
    zc = zf - HOOD_DROP * (1.0 if x < -1500 else 0.6)
    return [(w, zw), (0.975 * w, zw + 0.55 * (zf - zw)), (0.86 * w, zf), (0.66 * w, zc + 0.45 * (zf - zc)),
            (0.32 * w, zc + 2), (0, zc)]


def grid():
    """(stations x points) array of 3D points, full width (11 points per section)."""
    G = []
    for x, w, zb, zw in ST:
        h = half_upper(x, w, zb, zw)
        full = h + [(-y, z) for y, z in reversed(h[:-1])]
        G.append([(x, y, z) for y, z in full])
    return np.array(G, float)


def network():
    G = grid()
    u = [Spline(*[Vector(*p) for p in row]) for row in G]                 # sections
    v = [Spline(*[Vector(*p) for p in G[:, k]]) for k in range(G.shape[1])]  # feature lines
    return u, v, G
