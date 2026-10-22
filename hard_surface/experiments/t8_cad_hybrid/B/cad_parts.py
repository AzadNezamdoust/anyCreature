"""cad_parts.py -- t8 candidate B (CAD hybrid): the assault_rifle LOCKED PART TREE + DIMENSIONAL PLAN (plan.json,
real metres, the same numbers as the baseline build: out/blender-hs/assault_rifle/build.py + FEATURES.md) realised as
exact B-rep solids in build123d (exact booleans, true fillets/chamfers), tessellated to one STL per part.
Blender (build.py) then welds, paints materials, sets sharp edges + Weighted Normal, UVs.
Author frame: x = left flank, y up, z muzzle (metres).   Run: venv/Scripts/python cad_parts.py
"""
import json
import math
import os
import sys

from build123d import (Axis, Box, Plane, Pos, Solid, Vector, Wire, Face, Edge, export_stl, chamfer, fillet)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "parts")
os.makedirs(OUT, exist_ok=True)
V = Vector

S_PX = 887.2222222222222
BORE_Y = 0.2265
MUZZLE_Z, BUTT_Z = 0.450, -0.449
TOL, ANG = 0.0006, 0.45          # tessellation: 0.6 mm chord, 0.45 rad (~14 segments per full circle)


def Z(X):
    return (511.5 - X) / S_PX


def Y(Yp):
    return (653.0 - Yp) / S_PX


def PX(pts):
    return [(Z(x), Y(y)) for x, y in pts]


# ------------------------------------------------------------------------------------------------ CAD helpers
def xprism(zy, x0, x1):
    """side profile (z, y) extruded along x from x0 to x1."""
    f = Face(Wire.make_polygon([V(x0, y, z) for z, y in zy], close=True))
    return Solid.extrude(f, V(x1 - x0, 0, 0))


def yprism(xz, y0, y1):
    f = Face(Wire.make_polygon([V(x, y0, z) for x, z in xz], close=True))
    return Solid.extrude(f, V(0, y1 - y0, 0))


def _pface(pts):
    return Face(Wire.make_polygon([V(*p) for p in pts], close=True))


def _planar(pts, tol=1e-7):
    a, b, c = (V(*p) for p in pts[:3])
    n = (b - a).cross(c - a)
    if n.length < 1e-12:
        return False
    n = n.normalized()
    return all(abs((V(*p) - a).dot(n)) < tol for p in pts[3:])


def loft3(rings):
    """ruled loft as a sewn shell of PLANAR faces (quads, split into 2 triangles where not planar) + planar caps:
    a ruled B-spline loft tessellates its flat sides densely; planar faces triangulate minimally."""
    from build123d import Shell
    rings = [[tuple(p) for p in r] for r in rings]
    fs = [_pface(rings[0][::-1]), _pface(rings[-1])]
    for r0, r1 in zip(rings, rings[1:]):
        n = len(r0)
        for i in range(n):
            q = [r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]]
            if (V(*q[0]) - V(*q[3])).length < 1e-9 and (V(*q[1]) - V(*q[2])).length < 1e-9:
                continue
            if _planar(q):
                fs.append(_pface(q))
            else:
                fs += [_pface([q[0], q[1], q[2]]), _pface([q[0], q[2], q[3]])]
    sol = Solid(Shell(fs))
    if sol.volume < 0:
        sol = Solid(Shell([f.reversed() if hasattr(f, "reversed") else f for f in fs]))
    return sol.clean().fix()


def zloft(secs):
    return loft3([[(x, y, z) for x, y in pts] for z, pts in secs])


def ngon(c, u, v, r, n, phase):
    return [tuple(c[i] + r * (math.cos(phase + 2 * math.pi * k / n) * u[i] + math.sin(phase + 2 * math.pi * k / n) * v[i])
                  for i in range(3)) for k in range(n)]


def revolve_z(cy, zr, n=20):
    """game-res body of revolution about (0, cy, z): n-gon rings (vertex radius r / cos(pi/n) so flats sit on r)."""
    return loft3([ngon((0, cy, z), (1, 0, 0), (0, 1, 0), r / math.cos(math.pi / n), n, math.pi / n) for z, r in zr])


def cyl(p0, p1, r, n=12):
    """game-res cylinder: an n-gon prism p0 -> p1 (flats on r)."""
    p0v, p1v = V(*p0), V(*p1)
    d = (p1v - p0v).normalized()
    u = d.cross(V(0, 0, 1)) if abs(d.Z) < 0.9 else d.cross(V(1, 0, 0))
    u = u.normalized()
    v = d.cross(u)
    R = r / math.cos(math.pi / n)
    return loft3([ngon(p, tuple(u), tuple(v), R, n, math.pi / n) for p in (p0, p1)])


def box(c, size):
    return Solid.make_box(*size, Plane(origin=(c[0] - size[0] / 2, c[1] - size[1] / 2, c[2] - size[2] / 2)))


def xslot(cz, cy, hl, r, x0, x1):
    """stadium (rounded slot) along z, through x0..x1: exact (box + two cylinders)."""
    s = box(((x0 + x1) / 2, cy, cz), (abs(x1 - x0), 2 * r, 2 * (hl - r)))
    for sz in (1, -1):
        s = s + cyl((x0, cy, cz + sz * (hl - r)), (x1, cy, cz + sz * (hl - r)), r, 8)
    return s


def yslot(cz, cx, hl, r, y0, y1):
    s = box((cx, (y0 + y1) / 2, cz), (2 * r, abs(y1 - y0), 2 * (hl - r)))
    for sz in (1, -1):
        s = s + cyl((cx, y0, cz + sz * (hl - r)), (cx, y1, cz + sz * (hl - r)), r, 8)
    return s


def edges_sharper(sol, deg):
    """edges whose two adjacent faces meet at more than deg (edge->face ancestor map, normals at the edge centre)."""
    adj = {}
    for f in sol.faces():
        for e in f.edges():
            adj.setdefault(hash(e), [e, []])[1].append(f)
    out = []
    for e, fs in adj.values():
        if len(fs) != 2:
            continue
        try:
            p = e.center()
            n0, n1 = fs[0].normal_at(p), fs[1].normal_at(p)
        except Exception:
            continue
        a = math.degrees(math.acos(max(-1.0, min(1.0, n0.dot(n1)))))
        if a > deg:
            out.append(e)
    return out


def ch(sol, w, deg=40.0, rnd=False):
    """CAD edge break: chamfer (or fillet) every edge sharper than deg; falls back edge by edge, then to none."""
    es = edges_sharper(sol, deg)
    if not es:
        return sol
    op = fillet if rnd else chamfer
    try:
        return op(es, w) if not rnd else sol.fillet(w, es)
    except Exception:
        pass
    try:
        return sol.fillet(w, es) if rnd else sol.chamfer(w, None, es)
    except Exception:
        pass
    # edge by edge: OCC refuses a whole set where two breaks meet at a ruled-loft vertex; keep the ones it takes.
    # only ORIGINAL edges (matched by midpoint within 1.5 w and length): never re-break the new chamfer edges
    orig = [(e.center(), e.length) for e in es]
    src = sol
    tried = []

    def is_orig(e):
        c, L = e.center(), e.length
        return any((c - oc).length < 1.5 * w + 1e-6 and L > 0.4 * oL for oc, oL in orig)

    def seen(e):
        c = e.center()
        return any((c - t).length < 1.5 * w + 1e-6 for t in tried)

    done = 0
    for _ in range(len(es) + 2):
        todo = [e for e in edges_sharper(sol, deg) if is_orig(e) and not seen(e)]
        if not todo:
            break
        e = todo[0]
        tried.append(e.center())
        try:
            nxt = sol.fillet(w, [e]) if rnd else sol.chamfer(w, None, [e])
            if nxt.is_valid:
                sol, done = nxt, done + 1
        except Exception:
            pass
    if not sol.is_valid:
        sol = src
        done = 0
    LOG.append(f"edge-break {w}: {done}/{len(es)} edges broken one by one")
    return sol


def octa(cy, hw, hh, fw, fh):
    return [(fw, cy - hh), (hw, cy - fh), (hw, cy + fh), (fw, cy + hh), (-fw, cy + hh), (-hw, cy + fh),
            (-hw, cy - fh), (-fw, cy - hh)]


def scl(pts, k, cy):
    return [(x * k, cy + (y - cy) * k) for x, y in pts]


LOG = []

# ------------------------------------------------------------------------------------------------ parts (plan.json order)
def part_barrel():
    return revolve_z(BORE_Y, [(0.020, 0.0120), (0.386, 0.0120)], 24)


def part_muzzle_brake():
    b = revolve_z(BORE_Y, [(0.3815, 0.0168), (0.3840, 0.0195), (0.3930, 0.0195), (0.3942, 0.0175),
                           (0.3962, 0.0175), (0.3975, 0.0200), (0.4465, 0.0200), (MUZZLE_Z, 0.0168)], 24)
    b = b - cyl((0, BORE_Y, MUZZLE_Z - 0.058), (0, BORE_Y, MUZZLE_Z + 0.01), 0.0095)
    for dy in (0.0088, -0.0088):
        for x0, x1 in ((0.0140, 0.03), (-0.03, -0.0140)):
            b = b - xslot(0.4225, BORE_Y + dy, 0.0165, 0.0048, x0, x1)
    for dx in (0.0088, -0.0088):
        b = b - yslot(0.4225, dx, 0.0165, 0.0048, BORE_Y + 0.0140, BORE_Y + 0.03)
    return b


def part_front_sight():
    prof = PX([(219.5, 441), (219.5, 386), (223, 382.5), (234, 382.5), (268.7, 421), (268.7, 441), (258, 441),
               (258, 434.5), (231, 434.5), (231, 441)])
    yb, yt = Y(435), Y(382.5)
    # tapered tower = loft of the side profile scaled in x: built as an x-prism then cut by two tapered planes
    s = xprism(prof, -0.017, 0.017)
    s = ch(s, 0.0018, 30.0)
    s = s - xprism(PX([(231, 395.5), (231, 426), (258, 426)]), -0.03, 0.03)
    for sx in (1, -1):    # taper: 0.034 at the bar -> 0.018 at the top (wedge cutters)
        k = 0.47 * 0.017
        w = loft3([[(sx * 0.017, yb, -0.5), (sx * 0.017, yb, 0.5), (sx * 0.06, yb, 0.5), (sx * 0.06, yb, -0.5)],
                   [(sx * (0.017 - k), yt, -0.5), (sx * (0.017 - k), yt, 0.5), (sx * 0.06, yt, 0.5),
                    (sx * 0.06, yt, -0.5)]])
        s = s - w
    s = s - box((0, Y(382.5), Z(228)), (0.0090, 0.020, 0.030))
    s = s + revolve_z(BORE_Y, [(Z(230.5), 0.0180), (Z(229), 0.0195), (Z(221), 0.0195), (Z(219.5), 0.0180)])
    s = s + revolve_z(BORE_Y, [(0.2715, 0.0195), (Z(259.5), 0.0195), (Z(258), 0.0180)])
    s = s + box((0, Y(382.5) - 0.0065, Z(228)), (0.0026, 0.015, 0.0026))
    s = s + xprism(PX([(259.5, 436), (259.5, 414), (268.7, 424.2), (268.7, 436)]), -0.0195, 0.0195)
    return s


HG_CY = BORE_Y
HG_O = (0.039, 0.043, 0.019, 0.0233)
HG_OCT = octa(HG_CY, *HG_O)
HG_Z0, HG_Z1 = Z(477.5), Z(290)
VENTS = [(314, 352.5), (362.5, 400.5), (412.5, 449.5)]


def part_handguard():
    s = zloft([(HG_Z0, scl(HG_OCT, 0.93, HG_CY)), (HG_Z0 + 0.004, HG_OCT), (HG_Z1, HG_OCT)])
    s = ch(s, 0.0010, 50.0)
    for x0, x1 in VENTS:
        for a, b in ((0.030, 0.06), (-0.06, -0.030)):
            s = s - xslot((Z(x0) + Z(x1)) / 2, Y(451.2), (Z(x0) - Z(x1)) / 2, 0.0085, a, b)
    cap = zloft([(0.2580, scl(HG_OCT, 0.88, HG_CY)), (0.2645, scl(HG_OCT, 0.88, HG_CY)),
                 (0.2735, scl(HG_OCT, 0.66, HG_CY))])
    return s + cap


def part_band():
    o = scl(HG_OCT, 0.955, HG_CY)
    return zloft([(HG_Z1 - 0.003, o), (Z(277.5), o)])


RAIL_TEETH = 22


def part_rail():
    sec = [(-0.017, 0.262), (0.017, 0.262), (0.017, 0.268), (0.0145, 0.2715), (-0.0145, 0.2715), (-0.017, 0.268)]
    s = zloft([(Z(699), sec), (Z(307), sec)])
    tooth = [(-0.0158, 0.2705), (0.0158, 0.2705), (0.0158, 0.2765), (-0.0158, 0.2765)]
    for k in range(RAIL_TEETH):
        x0 = 309 + (652 - 309) / (RAIL_TEETH - 1) * k
        s = s + zloft([(Z(x0 + 11.5), tooth), (Z(x0), tooth)])
    return s


UP_Y0, UP_Y1 = 0.2125, 0.267
UP_HW, LO_HW = 0.033, 0.0295
SEAM_Y = 0.2172
UP_SEC = [(0.030, UP_Y0), (UP_HW, 0.2155), (UP_HW, 0.254), (0.021, UP_Y1), (-0.021, UP_Y1), (-UP_HW, 0.254),
          (-UP_HW, 0.2155), (-0.030, UP_Y0)]
UP_Z0, UP_Z1 = Z(700), 0.004
CH_Y0, CH_Y1, CH_HW = 0.2175, 0.2445, 0.0135
BOLT_Y = 0.231
SLOT_Y, SLOT_R = 0.2355, 0.0075
LUG = [(0.0265, 0.187), (0.0305, 0.191), (0.0305, 0.2435), (0.015, 0.264), (-0.015, 0.264), (-0.0305, 0.2435),
       (-0.0305, 0.191), (-0.0265, 0.187)]
NECK = [(0.0212, 0.190), (0.0244, 0.1935), (0.0244, 0.2435), (0.012, 0.263), (-0.012, 0.263), (-0.0244, 0.2435),
        (-0.0244, 0.1935), (-0.0212, 0.190)]


def part_upper():
    cyu = (UP_Y0 + UP_Y1) / 2
    s = ch(zloft([(UP_Z0, scl(UP_SEC, 0.94, cyu)), (UP_Z0 + 0.004, UP_SEC), (UP_Z1 - 0.004, UP_SEC),
                  (UP_Z1, scl(UP_SEC, 0.94, cyu))]), 0.0010, 42.0)
    ring = octa(BORE_Y, 0.0375, 0.040, 0.0175, 0.0215)
    s = s + ch(zloft([(0.0135, scl(ring, 0.92, BORE_Y)), (0.0165, ring), (0.038, ring),
                      (0.042, scl(ring, 0.92, BORE_Y))]), 0.0010, 42.0)
    s = s + ch(zloft([(-0.001, LUG), (0.0110, LUG)]), 0.0010, 42.0)
    col = octa(0.2355, 0.024, 0.0295, 0.012, 0.016)
    s = s + ch(zloft([(Z(723.5), scl(col, 0.90, 0.2355)), (Z(720), col), (Z(703), col),
                      (Z(698), scl(col, 0.90, 0.2355))]), 0.0010, 42.0)
    s = s + zloft([(0.0090, NECK), (0.0155, NECK)])
    s = s - box((0, (CH_Y0 + CH_Y1) / 2, -0.1025), (2 * CH_HW, CH_Y1 - CH_Y0, 0.205))
    s = s - xslot((Z(517) + Z(608)) / 2, SLOT_Y, (Z(517) - Z(608)) / 2, SLOT_R, 0.0165, 0.05)
    s = s - box((-0.030, 0.2315, -0.054), (0.040, 0.020, 0.060))
    for sx in (1, -1):
        s = s - box((sx * 0.0395, (0.2090 + SEAM_Y) / 2, -0.1055), (0.022, SEAM_Y - 0.2090, 0.207))
    s = s - xslot((Z(517) + Z(608)) / 2, SLOT_Y, (Z(517) - Z(608)) / 2 + 0.0012, SLOT_R + 0.0012, UP_HW - 0.0012, 0.05)
    # dust cover (open, hinge rod) + deflector, right flank; front pivot pins -> fused (one object = the receiver)
    xc = -UP_HW - 0.0012
    s = s + ch(box((xc, 0.2105, -0.054), (0.0030, 0.021, 0.062)), 0.001, 30)
    s = s + cyl((xc, 0.2218, -0.088), (xc, 0.2218, -0.020), 0.0022)
    s = s + xprism([(-0.090, 0.2445), (-0.090, 0.2215), (-0.104, 0.2215), (-0.104, 0.2445)], -UP_HW - 0.0055, -UP_HW + 0.002)
    for sx in (1, -1):
        p = cyl((sx * 0.026, Y(479), Z(505.5)), (sx * 0.0325, Y(479), Z(505.5)), 0.0045)
        p = p - cyl((sx * 0.0315, Y(479), Z(505.5)), (sx * 0.04, Y(479), Z(505.5)), 0.0018)
        s = s + p
    return s


def part_bolt():
    return revolve_z(BOLT_Y, [(-0.105, 0.0100), (-0.103, 0.0110), (-0.008, 0.0110), (-0.006, 0.0100)], 12)


def part_charging_handle():
    zf, zr = Z(525), Z(551)
    xi, xo = UP_HW + 0.002, UP_HW + 0.018
    y0, y1 = Y(457), Y(437)
    k = box(((xi + xo) / 2, (y0 + y1) / 2, (zf + zr) / 2), (xo - xi, y1 - y0, zf - zr))
    k = ch(k, 0.0015, 30.0)                                 # CAD chamfered knob (fillets: 18k tris)
    for yg in (Y(450), Y(443.5)):                           # two grooves, true V cut
        k = k - xprism([(zf + 0.01, yg - 0.0014), (zf + 0.01, yg + 0.0014), (zr - 0.01, yg + 0.0014),
                        (zr - 0.01, yg - 0.0014)], xo - 0.0008, xo + 0.01)
    k = k + box((0.0275, SLOT_Y, (Z(532.5) + Z(545)) / 2), (0.017, 0.011, Z(532.5) - Z(545)))
    return k


MAG_O = (-0.0466, 0.183)
MAG_A = (0.3217, -0.9468)
MAG_P = (-0.9468, -0.3217)
MAG_TF, MAG_TR, MAG_HW = -0.030, 0.032, 0.023
MAG_CL = 0.0022
MAG_GROOVES = (-0.0070, 0.0175)


def M(s, t, x):
    return (x, MAG_O[1] + s * MAG_A[1] + t * MAG_P[1], MAG_O[0] + s * MAG_A[0] + t * MAG_P[0])


def mag_ring(sec, s):
    return [M(s, t, x) for t, x in sec]


def part_receiver():
    hw = LO_HW
    s = xprism(PX([(510, 462.7), (700, 462.7), (712, 470), (690, 494), (688, 505), (581.5, 505), (581.5, 537),
                   (575.5, 535), (510, 513.5)]), -hw, hw)
    s = ch(s, 0.002, 30.0)
    s = s + ch(xprism(PX([(517, 486.5), (562, 486.5), (568.5, 491.5), (575, 491.5), (575, 533.5), (517, 514)]),
                      -LO_HW - 0.003, LO_HW + 0.003), 0.0009, 42.0)
    xt, xb = LO_HW + 0.0045, LO_HW + 0.0075
    top, bot = PX([(509, 503.5), (575.5, 525)]), PX([(509, 514), (575.5, 535.5)])
    s = s + ch(loft3([[(-xt, top[0][1], top[0][0]), (xt, top[0][1], top[0][0]), (xt, top[1][1], top[1][0]),
                    (-xt, top[1][1], top[1][0])],
                   [(-xb, bot[0][1], bot[0][0]), (xb, bot[0][1], bot[0][0]), (xb, bot[1][1], bot[1][0]),
                    (-xb, bot[1][1], bot[1][0])]]), 0.0009, 42.0)
    sec = [(MAG_TF - MAG_CL, -MAG_HW - MAG_CL), (MAG_TR + MAG_CL, -MAG_HW - MAG_CL),
           (MAG_TR + MAG_CL, MAG_HW + MAG_CL), (MAG_TF - MAG_CL, MAG_HW + MAG_CL)]
    s = s - loft3([mag_ring(sec, -0.002), mag_ring(sec, 0.12)])
    s = s - box((0, 0.170, (Z(607) + Z(630)) / 2), (0.013, 0.030, Z(607) - Z(630)))
    for sx in (1, -1):
        s = s - box((sx * 0.0435, (Y(505.5) + Y(541)) / 2, (Z(576.5) + Z(584)) / 2),
                    (0.033, Y(505.5) - Y(541), Z(576.5) - Z(584)))
        s = s + cyl((sx * 0.024, Y(469), Z(682)), (sx * (LO_HW + 0.0015), Y(469), Z(682)), 0.0036)
    s = s + ch(box((-LO_HW - 0.001, Y(478), Z(592)), (0.004, 0.012, 0.016)), 0.001, 30)
    return s


def part_magazine():
    w, g = MAG_HW, 0.0010

    def sec(tr):
        half = [(MAG_TF, w - 0.006), (MAG_TF + 0.006, w)]
        for tg in MAG_GROOVES:
            half += [(tg - 0.0016, w), (tg - 0.0006, w - g), (tg + 0.0006, w - g), (tg + 0.0016, w)]
        half += [(tr - 0.004, w), (tr, w - 0.004)]
        return half + [(t, -x) for t, x in reversed(half)]

    tb = 0.0405
    s = loft3([mag_ring(sec(MAG_TR), 0.0), mag_ring(sec(MAG_TR), 0.045), mag_ring(sec(tb), 0.130),
               mag_ring(sec(tb), 0.163)])
    pf, pr, pw = MAG_TF - 0.003, tb + 0.003, w + 0.0025
    plate = [(pf, -pw), (pr, -pw), (pr, pw), (pf, pw)]
    pin_ = [(pf + 0.003, -pw + 0.003), (pr - 0.003, -pw + 0.003), (pr - 0.003, pw - 0.003), (pf + 0.003, pw - 0.003)]
    p = loft3([mag_ring(pin_, 0.1585), mag_ring(plate, 0.1615), mag_ring(plate, 0.1755), mag_ring(pin_, 0.1785)])
    return s + p


def part_trigger_guard():
    s = xprism(PX([(577, 520), (579.5, 520), (579.5, 529), (581.5, 531.5), (583.5, 533.5), (587, 535), (625.5, 535),
                   (630, 532.5), (632, 528), (632, 497), (642, 497), (642, 536), (640, 541), (635, 544), (585, 544),
                   (579.5, 541.5), (577, 537)]), -0.020, 0.020)
    return ch(s, 0.0012, 42.0)


def part_trigger():
    s = xprism(PX([(613.5, 493.5), (614.6, 505), (614.4, 513), (613.2, 519.5), (611, 524.5), (608, 528),
                   (609.8, 530.6), (613.5, 528.3), (619.5, 523.5), (622, 517), (623.5, 509), (625, 501),
                   (625, 493.5)]), -0.004, 0.004)
    return ch(s, 0.0008, 30.0)


def part_selector():
    yh, zh = Y(481.7), Z(661)
    xi = LO_HW + 0.002
    s = ch(cyl((xi, yh, zh), (xi + 0.012, yh, zh), 0.0098, 16), 0.0007, 50.0)
    s = s + ch(xprism(PX([(630, 476), (661, 475.5), (661, 488), (630, 487.5)]), xi + 0.0025, xi + 0.0085), 0.0007, 50)
    s = s + ch(xprism(PX([(655, 484), (667, 484), (665.5, 509.5), (656.5, 509.5)]), xi + 0.0025, xi + 0.0085), 0.0007, 50)
    return s


def part_grip():
    s = xprism(PX([(640, 497), (691, 497), (694, 510), (732, 594), (727, 602), (679, 620), (669, 613), (646, 540),
                   (640, 535)]), -0.022, 0.022)
    (za, ya), (zb, yb) = PX([(646, 540), (669, 613)])
    front = [e for e in s.edges() if abs(e.start_point().X - e.end_point().X) < 1e-6 and
             min(math.hypot(e.start_point().Z - za, e.start_point().Y - ya),
                 math.hypot(e.start_point().Z - zb, e.start_point().Y - yb)) < 0.0005 and
             min(math.hypot(e.end_point().Z - za, e.end_point().Y - ya),
                 math.hypot(e.end_point().Z - zb, e.end_point().Y - yb)) < 0.0005]
    try:
        s = s.chamfer(0.010, None, front)
    except Exception:
        LOG.append("grip front facet chamfer failed")
    return ch(s, 0.005, 50.0)


def part_stock():
    def sec(yt, yb):
        yr = yt - 0.018
        return [(0.017, yb), (0.025, yb + 0.007), (0.025, yr), (0.010, yt), (-0.010, yt), (-0.025, yr),
                (-0.025, yb + 0.007), (-0.017, yb)]
    s = ch(zloft([(Z(882), sec(Y(406.7), Y(476.7))), (Z(720), sec(Y(420), Y(468)))]), 0.0012, 42.0)
    y0, y1, hw, c, f = Y(560), Y(390), 0.040, 0.012, 0.012

    def face(d):
        return [(hw - c, y0 + d), (hw, y0 + d + c), (hw, y1 - d - c), (hw - c, y1 - d), (-hw + c, y1 - d),
                (-hw, y1 - d - c), (-hw, y0 + d + c), (-hw + c, y0 + d)]
    s = s + ch(zloft([(BUTT_Z + 0.003, face(0.007)), (BUTT_Z + 0.010, face(0)), (Z(878) - f, face(0)),
                      (Z(878), face(f))]), 0.0012, 42.0)
    s = s + ch(xprism(PX([(768, 470), (800, 470), (884, 531), (884, 555)]), -0.011, 0.011), 0.002, 30)
    cyp = (y0 + y1) / 2
    s = s + zloft([(BUTT_Z, scl(face(0), 0.80, cyp)), (BUTT_Z + 0.0015, scl(face(0), 0.85, cyp)),
                   (BUTT_Z + 0.006, scl(face(0), 0.85, cyp))])
    return s


def part_rear_sight():
    y0, ye, yt = 0.2695, 0.2970, Y(373)

    def sec(d):
        return [(-0.023, y0), (0.023, y0), (0.023, yt - 0.003 - d), (0.020, yt - d), (0.0125, yt - d), (0.0125, ye),
                (-0.0125, ye), (-0.0125, yt - d), (-0.020, yt - d), (-0.023, yt - 0.003 - d)]
    s = zloft([(Z(697), sec(0.004)), (Z(697) + 0.004, sec(0)), (Z(668) - 0.004, sec(0)), (Z(668), sec(0.004))])
    s = ch(s, 0.0012, 30.0)
    s = s + box((0, 0.300, Z(684)), (0.020, 0.022, 0.003))
    s = s - cyl((0, 0.3045, Z(684) - 0.01), (0, 0.3045, Z(684) + 0.01), 0.0030)
    for sx in (1, -1):
        p = cyl((sx * 0.021, Y(386), Z(684)), (sx * 0.027, Y(386), Z(684)), 0.0056)
        p = p - cyl((sx * 0.026, Y(386), Z(684)), (sx * 0.04, Y(386), Z(684)), 0.0020)
        s = s + p
    s = s + ch(box((0, (0.263 + Y(398)) / 2, (Z(697) + Z(712)) / 2), (0.038, Y(398) - 0.263, Z(697) - Z(712))),
               0.003, 30)
    return s


PARTS = {   # locked part tree: object -> (builder, role, rig note)
    "receiver": (part_receiver, "receiver", "static"),
    "upper": (part_upper, "receiver", "static"),
    "bolt": (part_bolt, "bolt", "slides -z 0.06"),
    "handguard": (part_handguard, "handguard", "static"),
    "handguard_band": (part_band, "handguard", "static"),
    "barrel": (part_barrel, "barrel", "static"),
    "muzzle_brake": (part_muzzle_brake, "muzzle_device", "static"),
    "front_sight": (part_front_sight, "sight", "static"),
    "rail": (part_rail, "rail", "static"),
    "rear_sight": (part_rear_sight, "sight", "static"),
    "stock": (part_stock, "stock", "static"),
    "grip": (part_grip, "grip", "static"),
    "magazine": (part_magazine, "magazine", "slides along MAG_A"),
    "trigger_guard": (part_trigger_guard, "trigger_guard", "static"),
    "trigger": (part_trigger, "trigger", "pin x at y .176 z -.120"),
    "charging_handle": (part_charging_handle, "charging_handle", "slides -z 0.06"),
    "selector": (part_selector, "selector", "hub axis x"),
}

if __name__ == "__main__":
    only = sys.argv[1:]
    plan = {}
    for name, (fn, role, rig) in PARTS.items():
        if only and name not in only:
            continue
        LOG.clear()
        sol = fn()
        if not sol.is_valid:
            sol = sol.fix()
            LOG.append(f"ShapeFix -> valid {sol.is_valid}")
        if hasattr(sol, "solids") and len(sol.solids()) > 1:
            LOG.append(f"{len(sol.solids())} solids")
        bb = sol.bounding_box()
        path = os.path.join(OUT, name + ".stl")
        export_stl(sol, path, tolerance=TOL, angular_tolerance=ANG)
        plan[name] = {"role": role, "rig": rig, "volume_m3": sol.volume, "valid": bool(sol.is_valid),
                      "bbox_min": list(bb.min), "bbox_max": list(bb.max), "log": list(LOG)}
        print(name, "valid", sol.is_valid, "vol %.3e" % sol.volume, LOG, flush=True)
    old = {}
    pj = os.path.join(HERE, "plan.json")
    if only and os.path.exists(pj):
        old = json.load(open(pj))
    old.update(plan)
    json.dump(old, open(pj, "w"), indent=1)
