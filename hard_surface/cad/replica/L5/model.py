"""L5 replica: Porsche 911 Carrera S (992.1, 2019+) coupe - body + wheels.

Every dimension comes from refdata.py (spec sheet values + traces of the photos in REFS.md, registered to the spec
length / wheelbase / height). Authored in mm; front -X, left -Y, Z up, ground Z=0.

Construction
  body  = ONE loft through 24 full-width cross-sections. Each section's centre-top height is read off the traced
          side silhouette (roof / windshield / engine lid; for the front the traced silhouette is the FENDER crown and
          the hood centre sits HOOD_DROP below it). Half-widths: spec W at the rear haunch; other widths from the
          front/rear photos (est., see NOTES). 'inner(d)' re-lofts the same stations pulled in by d = parametric
          skin offset used for every recess / inlay (OCCT 3D offset of this loft is unreliable, ladder L5 lesson).
  glass = windshield, side DLO (traced), backlight: recessed 6 mm + 5 mm glass inlay.
  shut lines (doors traced from photo, hood + engine lid from front/rear photos): 4 mm grooves, 3 mm deep.
  lights: oval headlights on the fender noses, full-width tail band, intakes, exhaust tips, louvre grille.
  wheels: Carrera S 20"/21" five-spoke, 245/35 ZR20 + 305/30 ZR21, discs + red calipers, at spec track.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import *  # noqa: E402,F401,F403
import refdata as R  # noqa: E402

UNITS = "mm"
TRI_BUDGET = 60000
FAIL = []
import time as _t
_T0 = _t.time()
def T(msg):
    print(f'[{_t.time()-_T0:7.1f}s] {msg}', flush=True)
          # features that could not be built (reported in NOTES)

# ---------------------------------------------------------------- body sections
WB_HALF = R.W / 2           # 926 rear haunch (spec width)
WF_HALF = 912.0             # front fender half width (est. from F1: front track 1591 + 245 tyre = 1836 outer)
WD_HALF = 898.0             # door / sill half width (est. from R1+F1: body waisted between arches)
HOOD_DROP = 38.0            # hood centre below fender crown (F1: fenders stand proud of the hood)
ROOF_G = 535.0              # roof half width at the top (F1/R1 roof ~ 0.61 W)


def top_mm(x):
    """centre-top Z of the traced side silhouette at model X."""
    pts = sorted(R.side_poly_mm(R.SIDE_TOP_PX))
    xs, zs = zip(*pts)
    return float(np.interp(x, xs, zs))


import numpy as np  # noqa: E402

X0, X1 = R.X_FRONT + 4, R.X_REAR - 4
END_R = 110.0   # nose/tail cap rounding (photos: no sharp end edges)
# x, half-width w, bottom zb, z of max width zw, belt / fender crown zs, roof half-width g (None = hood station)
ST = [
    (X0,     560, 235, 360, None, None),
    (-2215,  745, 175, 390, None, None),
    (-2131,  815, 150, 410, None, None),
    (-1965,  870, 140, 430, None, None),
    (-1836,  895, 142, 440, None, None),
    (-1580,  WF_HALF - 4, 150, 455, None, None),
    (R.X_AF, WF_HALF, 160, 470, None, None),
    (-1050,  WF_HALF - 4, 162, 480, None, None),
    (-925,   WF_HALF - 8, 163, 485, None, None),
    (-800,   WD_HALF + 4, 165, 490, 915, 640),
    (-600,   WD_HALF, 165, 495, 915, 612),
    (-350,   WD_HALF, 165, 495, 915, 590),
    (-100,   WD_HALF, 165, 495, 915, ROOF_G),
    (250,    WD_HALF + 2, 165, 500, 918, ROOF_G - 5),
    (600,    912, 172, 505, 935, 548),
    (900,    WB_HALF - 3, 190, 520, 950, 515),
    (R.X_AR, WB_HALF, 205, 530, 960, 470),
    (1400,   WB_HALF - 4, 212, 540, 955, 410),
    (1700,   905, 215, 560, 925, 320),
    (1950,   862, 215, 580, 890, 220),
    (2131,   800, 212, 600, 835, 140),
    (X1,     700, 215, 620, 790, 80),
]


def half_pts(x, w, zb, zw, zs, g, d=0.0):
    """9 half-section points (y>=0) bottom-centre -> top-centre, pulled in by d."""
    zt = top_mm(x)
    if g is None:   # hood station: traced silhouette = fender crown
        zf = zt
        zc = zt - HOOD_DROP * (1.0 if x < -1500 else 0.6)
        w, zb, zf, zc = w - d, zb + d, zf - d, zc - d
        return [(0, zb), (0.80 * w, zb), (0.965 * w, zb + 0.3 * (zw - zb)), (w, zw), (0.975 * w, zw + 0.55 * (zf - zw)),
                (0.86 * w, zf), (0.66 * w, zc + 0.45 * (zf - zc)), (0.32 * w, zc + 2), (0, zc)]
    zt = max(zt, zs + 25)
    w, zb, zs, zt, g = w - d, zb + d, zs - d * 0.3, zt - d, g - d
    return [(0, zb), (0.80 * w, zb), (0.965 * w, zb + 0.3 * (zw - zb)), (w, zw), (0.975 * w, zw + 0.55 * (zs - zw)),
            (0.905 * w, zs), (g + 0.30 * (0.905 * w - g), zs + 0.55 * (zt - zs)), (0.55 * g, zt - 9), (0, zt)]


def section(st, d=0.0):
    x = st[0]
    half = half_pts(*st[:6], d=d)
    drop = st[6] if len(st) > 6 else 0.0
    half = [(y, z - drop * (y / max(st[1], 1)) ** 0 if i == len(half) - 1 or i >= 5 else z) for i, (y, z) in enumerate(half)]
    pts = half + [(-y, z) for y, z in reversed(half[1:-1])]
    return make_face(Spline(*[Vector(x, y, z) for y, z in pts], periodic=True))


def end_round(st):
    """Round nose / tail in plan + section: replace each end station by a quarter-round run of stations
    (cap_round on the loft made every later boolean fall back to Manifold, 30+ min runs -> pure-loft rounding)."""
    # one extra shrunk tip station per end (dense quarter-round stations made booleans 10x slower)
    x0, x1 = st[0][0], st[-1][0]
    f0 = (x0, st[0][1] * 0.80, st[0][2] + 35, st[0][3], st[0][4], st[0][5], 25.0)
    f1 = (x0 + 45,) + st[0][1:] + (0.0,)
    r1 = (x1 - 45,) + st[-1][1:] + (0.0,)
    r0 = (x1, st[-1][1] * 0.80, st[-1][2] + 40, st[-1][3], st[-1][4], (st[-1][5] or 0) * 0.8, 30.0)
    mid = [s_ + (0.0,) for s_ in st[1:-1] if min(abs(s_[0] - x0), abs(s_[0] - x1)) > 80]
    return [f0, f1] + mid + [r1, r0]


def body_loft(d=0.0):
    st = list(ST)
    st[0] = (st[0][0] + d,) + st[0][1:]
    st[-1] = (st[-1][0] - d,) + st[-1][1:]
    b = loft([section(s, d) for s in end_round(st)])
    return b


bare = body_loft(0)
T('bare loft')
body = bare
_inner = {}


def inner(d):
    if d not in _inner:
        _inner[d] = body_loft(d)
    return _inner[d]


def recess(b, tool, d, label):
    """cut 'tool' into the skin to depth d (only the part of the tool within d of the surface)."""
    try:
        return cut(b, cut(tool, inner(d), label + " skin tool"), label)
    except Exception as e:  # noqa: BLE001  (CadOpError or an invalid inner loft)
        FAIL.append(f"{label}: {type(e).__name__}: {str(e)[:120]}")
        return b


def inlay(tool, d0, d1, label):
    """body-conforming panel between skin offsets d0 and d1 inside 'tool'."""
    try:
        return cut(common(inner(d0), tool, label + " common"), inner(d1), label)
    except Exception as e:  # noqa: BLE001  (CadOpError or an invalid inner loft)
        FAIL.append(f"{label}: {type(e).__name__}: {str(e)[:120]}")
        return None


def strip_xz(pts, half=2.0):
    """thin closed strip around a polyline in the XZ plane (for grooves)."""
    out_a, out_b = [], []
    for i, (x, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, tz) or 1
        nx, nz = -tz / n * half, tx / n * half
        out_a.append((x + nx, z + nz))
        out_b.append((x - nx, z - nz))
    return out_a + out_b[::-1]


def prism_xz(poly, y0, y1):
    """polygon in XZ, extruded over Y in [y0, y1]."""
    f = Plane.XZ * make_face(Polyline(*poly, close=True))     # Plane.XZ normal = -Y
    return Pos(0, y1, 0) * extrude(f, amount=y1 - y0)


def prism_xy(poly, z0, z1):
    return Pos(0, 0, z0) * extrude(make_face(Polyline(*poly, close=True)), z1 - z0)


def both_sides(fn):
    return [fn(1), fn(-1)]


# ---------------------------------------------------------------- wheel wells (spec axles, tyre radii + traced gap)
ARCH_F = R.R_TF + 30.0      # traced arch-to-tyre gap (S1: ~13-18 px)
ARCH_R = R.R_TR + 33.0
for (xa, ra, za, y_in) in [(R.X_AF, ARCH_F, R.R_TF, R.TRACK_F / 2 - 160), (R.X_AR, ARCH_R, R.R_TR, R.TRACK_R / 2 - 190)]:
    for s in (1, -1):
        well = Pos(xa, s * (y_in + 300), za) * (Rot(90, 0, 0) * Cylinder(ra, 600))
        body = cut(body, well, "wheel well")

T('wells')
# ---------------------------------------------------------------- glass
dlo = R.side_poly_mm(R.SIDE_DLO_PX)
ws_tool = prism_xy([(-905, -628), (-108, -560), (-108, 560), (-905, 628)], 860, 1400)
bl_tool = prism_xy([(330, -540), (1480, -455), (1480, 455), (330, 540)], 900, 1400)
dlo_tool = [prism_xz(dlo, 500, 1100), prism_xz(dlo, -1100, -500)]
GLASS_T = [ws_tool, bl_tool] + dlo_tool
glass = []
for k, t in enumerate(GLASS_T):
    body = recess(body, t, 6, f"glass recess {k}")
    g_ = inlay(t, 1.5, 6.5, f"glass {k}")
    if g_ is not None:
        glass.append(g_)

T('glass')
# ---------------------------------------------------------------- shut lines (4 mm grooves, 3 mm deep)
door_f = R.side_poly_mm(R.DOOR_FRONT_PX)
door_r = R.side_poly_mm(R.DOOR_REAR_PX)
zdb = R.side_px2mm(0, R.DOOR_BOTTOM_PY)[1]
door_loop = [door_f[0]] + door_f[1:] + [(door_f[-1][0], zdb), (door_r[-1][0], zdb)] + door_r[::-1]
grooves = []
for s in (1, -1):
    y0, y1 = (600, 1100) if s > 0 else (-1100, -600)
    grooves.append(prism_xz(strip_xz(door_f + [(door_f[-1][0] + 3, zdb)]), y0, y1))
    grooves.append(prism_xz(strip_xz(door_r), y0, y1))
    grooves.append(prism_xz(strip_xz([(door_f[-1][0], zdb), (door_r[-1][0] - 60, zdb), (door_r[-1][0], zdb + 40)]),
                            y0, y1))
# hood outline in plan (F1: hood edge runs from the windshield base corners to the bumper top between the lamps)
hood = [(-930, 600), (-1500, 545), (-1950, 470), (-2120, 400), (-2165, 0)]
hood_pl = hood + [(x, -y) for x, y in reversed(hood[:-1])]
grooves.append(prism_xy(strip_xz(hood_pl), 380, 1000))
# engine lid (R1: lid spans the louvre grille to the tail band, sides at ~ +-600)
lid = [(1520, 610), (2160, 600)]
for s in (1, -1):
    grooves.append(prism_xy(strip_xz([(x, s * y) for x, y in lid]), 600, 1200))
grooves.append(prism_xy(strip_xz([(1520, -610), (1520, 610)]), 600, 1200))
for k, gtool in enumerate(grooves):
    body = recess(body, gtool, 3, f"shut line {k}")

T('shut lines')
# ---------------------------------------------------------------- lights, intakes, louvres, exhaust
HL_Y, HL_Z, HL_R = 718.0, 690.0, 118.0          # F1 headlight centre / radius (registered)
hl_tools = [Pos(-2000, s * HL_Y, HL_Z) * (Rot(0, 90, 0) * Cylinder(HL_R, 700)) for s in (1, -1)]
for k, t in enumerate(hl_tools):
    body = recess(body, t, 14, f"headlight pocket {k}")
head = [h for h in (inlay(t, 9, 30, f"headlight lens {k}") for k, t in enumerate(hl_tools)) if h is not None]

TAIL_Z0, TAIL_Z1 = 772.0, 806.0                 # S1 tail band (px 640-668 -> 762-827, minus lid gap)
tail_tool = prism_xy([(2050, -900), (2400, -900), (2400, 900), (2050, 900)], TAIL_Z0, TAIL_Z1)
body = recess(body, tail_tool, 8, "tail band")
tail = [t for t in [inlay(tail_tool, 3, 12, "tail lens")] if t is not None]

T('headlights+tail')
# front intakes (F1): two side intakes + centre slot, recessed 45 mm, dark backing
intakes = [prism_xy([(-2400, s * 380), (-1900, s * 380), (-1900, s * 845), (-2400, s * 845)], 130, 335) for s in (1, -1)]
intakes.append(prism_xy([(-2400, -360), (-1950, -360), (-1950, 360), (-2400, 360)], 150, 255))
for k, t in enumerate(intakes):
    body = recess(body, t, 45, f"intake {k}")
dark = [d_ for d_ in (inlay(t, 40, 47, f"intake mesh {k}") for k, t in enumerate(intakes)) if d_ is not None]

T('intakes')
# engine-lid louvre grille behind the backlight (S1 dark band px 175-290 / R1 slats)
louv = prism_xy([(1530, -470), (1880, -430), (1880, 430), (1530, 470)], 800, 1300)
body = recess(body, louv, 10, "louvre recess")
FAIL.append("louvre floor/slats inlay: dropped - r2/r3 inlay returned an untrimmed block above the deck")
T('louvres')
# rear diffuser band + oval exhaust tips (Carrera S: 2 oval tips, R1)
diff = prism_xy([(2000, -760), (2400, -760), (2400, 760), (2000, 760)], 200, 300)
body = recess(body, diff, 25, "diffuser")
dd = inlay(diff, 22, 28, "diffuser dark")
if dd is not None:
    dark.append(dd)
tips = []
for s in (1, -1):
    o = extrude(Plane.YZ * make_face(Ellipse(68, 42)), 230)
    i_ = extrude(Plane.YZ * make_face(Ellipse(60, 34)), 240)
    tips.append(Pos(2005, s * 420, 255) * cut(o, Pos(-5, 0, 0) * i_, "tip bore"))

T('diffuser+tips')
# door handle (flush) + fuel flap (right front fender, S1)
hx0, hz0 = R.side_px2mm(R.HANDLE_PX[0], R.HANDLE_PX[3])
hx1, hz1 = R.side_px2mm(R.HANDLE_PX[1], R.HANDLE_PX[2])
for s in (1, -1):
    y0, y1 = (600, 1100) if s > 0 else (-1100, -600)
    body = recess(body, prism_xz([(hx1, hz0), (hx0, hz0 + 4), (hx0, hz1), (hx1, hz1 - 4)], y0, y1), 4, "door handle")
fx0, fz0 = R.side_px2mm(R.FUEL_PX[0], R.FUEL_PX[3])
fx1, fz1 = R.side_px2mm(R.FUEL_PX[1], R.FUEL_PX[2])
fcx, fcz, frx, frz = (fx0 + fx1) / 2, (fz0 + fz1) / 2, abs(fx1 - fx0) / 2, abs(fz1 - fz0) / 2
ring = Pos(fcx, 800, fcz) * (Rot(90, 0, 0) * (Cylinder(1, 400)))
fo = Plane.XZ * make_face(Ellipse(frx, frz).moved(Location((fcx, fcz, 0))))
fi = Plane.XZ * make_face(Ellipse(frx - 4, frz - 4).moved(Location((fcx, fcz, 0))))
fuel_ring = Pos(0, 1100, 0) * extrude(fo, 500) - Pos(0, 1100, 0) * extrude(fi, 500)
body = recess(body, fuel_ring, 3, "fuel flap")

T('handle+fuel')
# ---------------------------------------------------------------- mirrors (S1 head px box; F1 reach)
mx0, mz1 = R.side_px2mm(R.MIRROR_PX[0], R.MIRROR_PX[2])
mx1, mz0 = R.side_px2mm(R.MIRROR_PX[1], R.MIRROR_PX[3])
mirrors = []
for s in (1, -1):
    head_ = Box(abs(mx0 - mx1), 135, (mz1 - mz0) * 0.78)
    head_ = safe_fillet(head_, head_.edges(), 38, label="mirror head")
    head_ = Pos((mx0 + mx1) / 2 + 10, s * 945, mz0 + (mz1 - mz0) * 0.55) * head_
    arm = Pos((mx0 + mx1) / 2 + 40, s * 880, mz0 + 40) * Box(90, 120, 45)
    arm = safe_fillet(arm, arm.edges().filter_by(Axis.Y), 18, label="mirror arm")
    mirrors.append(fuse(head_, arm, "mirror"))

# ---------------------------------------------------------------- wheels (Carrera S 20/21 five-spoke)


def wheel(r_tyre, width, rim_in):
    rr = rim_in * 25.4 / 2          # bead seat radius
    hw = width / 2
    prof = Polyline((rr - 5, -hw + 8), (rr + 30, -hw), (r_tyre - 30, -hw + 4), (r_tyre - 4, -hw + 22),
                    (r_tyre, -hw + 45), (r_tyre, hw - 45), (r_tyre - 4, hw - 22), (r_tyre - 30, hw - 4),
                    (rr + 30, hw), (rr - 5, hw - 8), close=True)
    tyre = revolve(Plane.XY * make_face(prof), Axis.Y)
    # rim: barrel + outer lip + 5 tapered spokes + centre hub (outer face at -Y)
    barrel = Rot(90, 0, 0) * (Cylinder(rr, width - 30) - Cylinder(rr - 14, width + 10))
    lip = Pos(0, -hw + 22, 0) * (Rot(90, 0, 0) * (Cylinder(rr + 12, 18) - Cylinder(rr - 20, 30)))
    hub = Pos(0, -hw + 55, 0) * (Rot(90, 0, 0) * Cylinder(85, 50))
    cap = Pos(0, -hw + 28, 0) * (Rot(90, 0, 0) * Cylinder(42, 12))
    spokes = []
    for k in range(5):
        sp = extrude(Plane.XZ * make_face(Polygon((-26, 60), (26, 60), (44, rr - 8), (-44, rr - 8), align=None)), 34)
        sp = Pos(0, -hw + 40 + 17, 0) * sp
        spokes.append(Rot(0, 72 * k, 0) * sp)
    rim = fuse(barrel, [lip, hub, cap] + spokes, "rim")
    disc = Pos(0, -hw + 120, 0) * (Rot(90, 0, 0) * (Cylinder(175, 30) - Cylinder(80, 40)))
    return tyre, rim, disc


def caliper(r_disc, ang):
    c = Box(120, 70, 210)
    c = safe_fillet(c, c.edges(), 20, label="caliper")
    return Rot(0, ang, 0) * Pos(r_disc - 40, 0, 0) * c


WHEELS = []
for (xa, rt, tw, rim_in, tr, cal_ang) in [(R.X_AF, R.R_TF, R.TYRE_F[0], R.TYRE_F[2], R.TRACK_F, 180),
                                          (R.X_AR, R.R_TR, R.TYRE_R[0], R.TYRE_R[2], R.TRACK_R, 0)]:
    tyre, rim, disc = wheel(rt, tw, rim_in)
    cal = Pos(0, -tw / 2 + 120, 0) * caliper(175, cal_ang)
    for s in (1, -1):
        parts = [tyre, rim, disc, cal]
        if s > 0:
            parts = [p.mirror(Plane.XZ) for p in parts]
        WHEELS.append([Pos(xa, s * tr / 2, rt) * p for p in parts])

T('wheels')
# ---------------------------------------------------------------- parts
PARTS = {"body": (body, "#c9ccd0"), "glass": (Compound(glass), "#141a20"),
         "headlights": (Compound(head), "#dfe6ea"), "taillights": (Compound(tail), "#8a0d12"),
         "dark_trim": (Compound(dark + tips), "#202224"), "mirrors": (Compound(mirrors), "#c9ccd0")}
for i, (ty, ri, di, ca) in enumerate(WHEELS):
    PARTS[f"tyre{i}"] = (ty, "#1a1b1d")
    PARTS[f"rim{i}"] = (ri, "#8d9196")
    PARTS[f"disc{i}"] = (di, "#5a5d61")
    PARTS[f"caliper{i}"] = (ca, "#b3121b")
SPEC = {"L": R.L / 1000, "W": R.W / 1000, "H": R.H / 1000}
print("FAILED FEATURES:", FAIL)
