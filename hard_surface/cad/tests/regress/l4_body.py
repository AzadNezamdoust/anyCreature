"""Regression capture: L4 Xbox controller body (replica/L4/model.py r6/r7 body, before the perimeter round).
build(centre_rise) -> (body, R_BOT). centre_rise=8.0 is the r7 shape whose all-edge perimeter fillet segfaulted OCCT."""
import math
import numpy as np
from build123d import *

W, D = 153.0, 102.0
HALF_W = W / 2
PLAN_R = [(-49.5, 0), (-49.5, 22), (-49.0, 32), (-48.0, 40), (-46.0, 47), (-42.5, 53.5), (-35, 59.5), (-23.5, 65.5),
          (-9, 70), (4, 73.4), (15.6, 75.5), (27, 76.5), (38.7, 75.3), (45.5, 72), (49.6, 66.5), (50.5, 60),
          (48.5, 54), (43, 48), (36, 41.5), (30, 36), (26.5, 30.5), (25.6, 22), (25.5, 0)]
SIDE_TOP = [(-51.5, 42.5), (-46, 47), (-36, 49), (-22, 49), (-8, 47), (6, 43.5), (20, 37.5), (33, 30.5), (44, 25.5),
            (51.5, 21)]
SIDE_BOT = [(51.5, 3.5), (47, 0.6), (40, 0.0), (30, 1.5), (18, 5.5), (5, 9.5), (-10, 11.5), (-30, 12.5), (-45, 13.5),
            (-51.5, 15)]
DROP, LIFT = 11.0, 12.0
_sx = [p[0] for p in SIDE_TOP]; _sz = [p[1] for p in SIDE_TOP]
_bx = [p[0] for p in SIDE_BOT][::-1]; _bz = [p[1] for p in SIDE_BOT][::-1]


def ztop(x, y):
    return float(np.interp(x, _sx, _sz)) - DROP * min(1.0, abs(y) / HALF_W) ** 2.5


def build(centre_rise=0.0):
    def top_section(x):
        ys = [-95 + 190 * i / 24 for i in range(25)]
        top = Spline(*[Vector(x, y, ztop(x, y) if abs(y) <= HALF_W else ztop(x, HALF_W) - (abs(y) - HALF_W) * 0.6)
                       for y in ys])
        p0, p1 = top @ 0, top @ 1
        return make_face(Wire([top, Line(p1, Vector(x, 95, -20)), Line(Vector(x, 95, -20), Vector(x, -95, -20)),
                               Line(Vector(x, -95, -20), p0)]))

    def zbot(x, y):
        return (float(np.interp(x, _bx, _bz)) + LIFT * max(0.0, (abs(y) - 58.0) / (HALF_W - 58.0)) ** 2
                + centre_rise * max(0.0, 1 - (y / 34.0) ** 2) ** 2 * min(1.0, max(0.0, (x + 5) / 22.0)))

    def bot_section(x):
        ys = [-95 + 190 * i / 24 for i in range(25)]
        bot = Spline(*[Vector(x, y, zbot(x, y)) for y in ys])
        p0, p1 = bot @ 0, bot @ 1
        return make_face(Wire([bot, Line(p1, Vector(x, 95, 90)), Line(Vector(x, 95, 90), Vector(x, -95, 90)),
                               Line(Vector(x, -95, 90), p0)]))

    plan_pts = PLAN_R + [(x, -y) for x, y in reversed(PLAN_R[1:-1])]
    k = plan_pts.index((27, 76.5)); plan_pts = plan_pts[k:] + plan_pts[:k]
    plan = extrude(make_face(Plane.XY * Spline(*[Vector(*p) for p in plan_pts], periodic=True)), 80)
    side = loft([bot_section(x) for x in (-60, -45, -30, -10, 5, 18, 30, 40, 47, 60)])
    toptool = loft([top_section(x) for x in (-60, -46, -36, -22, -8, 6, 20, 33, 44, 60)])
    return (plan & side) & toptool, 5.0
