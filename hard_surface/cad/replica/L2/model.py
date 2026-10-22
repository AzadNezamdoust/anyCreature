"""Replica L2: Logitech G502 HERO wired gaming mouse (no invention - every number from refs/L2, see REFS.md).

Sources:
  [SPEC] Logitech support 360023303534 "Specification G502 HERO": length 132 mm, width 75 mm, height 40 mm, 121 g.
  [TOP]  logitechg.com gallery-1 (top view), registered to 132 mm length -> 0.179 mm/px (ref_extract.py).
  [SIDE] logitechg.com gallery-6 (right profile), 132 mm length, pad->crest 40 mm (elevated shot, own v-scale).
  [LEFT] gallery-2 (left profile) / [BACK] gallery-4: part breaks, thumb buttons, thumb rest, DPI LEDs.
Convention: X length (front -X), Y width (left -Y = thumb side), Z up, mm.
"""
import math

from cadkit import *

UNITS = "mm"
import os as _os, time as _time
_T0 = _time.time()


def _prog(msg):  # build progress log (replica/L2 debugging of slow booleans on a loaded box)
    with open(_os.path.join(_os.environ.get("TEMP", "."), "l2_progress.log"), "a") as f:
        f.write(f"{_time.time() - _T0:7.1f} {msg}" + chr(10))


L_SPEC, W_SPEC, H_SPEC = 132.0, 75.0, 40.0          # [SPEC]

# ---- station table [TOP]+[SIDE] via ref_extract.py: (X, y_left, y_right, z_crest, z_underside)
ST_ALL = [(-64, -13.0, 13.0, 13.6, 7.8), (-60, -14.0, 18.9, 16.0, 7.2), (-56, -21.0, 23.9, 18.2, 4.9),
      (-52, -24.8, 27.5, 24.0, 3.7), (-48, -26.7, 29.1, 26.4, 3.3), (-44, -28.2, 30.0, 28.6, 2.9),
      (-40, -29.4, 30.8, 30.1, 2.4), (-36, -30.9, 31.3, 32.7, 1.9), (-32, -32.1, 31.6, 34.9, 1.2),
      (-28, -32.3, 31.8, 36.0, 0.5), (-24, -32.5, 31.8, 35.9, 0.0), (-20, -32.8, 31.8, 35.9, 0.0),
      (-16, -33.5, 31.8, 36.7, 0.1), (-12, -33.0, 31.6, 37.9, 0.2), (-8, -35.5, 31.6, 39.0, 0.3),
      (-4, -39.3, 31.8, 38.8, 0.5), (0, -40.7, 32.4, 39.3, 0.6), (4, -41.2, 32.7, 39.8, 0.6),
      (8, -41.6, 33.1, 39.9, 0.7), (12, -42.0, 33.6, 40.0, 0.8), (16, -42.0, 34.0, 39.8, 0.8),
      (20, -42.1, 34.2, 39.5, 0.9), (24, -41.1, 34.3, 39.1, 1.0), (28, -37.7, 33.8, 38.3, 1.2),
      (32, -34.3, 33.3, 37.4, 1.3), (36, -31.4, 33.4, 36.3, 1.5), (40, -28.7, 32.5, 34.9, 1.7),
      (44, -26.4, 31.1, 33.2, 2.1), (48, -23.9, 29.3, 31.3, 4.2), (52, -21.7, 26.8, 28.9, 4.5),
      (56, -19.6, 23.8, 26.1, 5.1), (60, -16.7, 19.5, 22.3, 6.2), (64, -9.9, 12.7, 16.7, 7.9)]
def _smooth(rows):
    """[1,2,1]/4 smoothing along X of the measured table (pixel jitter made the r3 zebra lumpy); ends kept."""
    out = [rows[0]]
    for a, b, c in zip(rows, rows[1:], rows[2:]):
        out.append(tuple([b[0]] + [(a[k] + 2 * b[k] + c[k]) / 4 for k in range(1, 5)]))
    return out + [rows[-1]]


ST_ALL = _smooth(_smooth(ST_ALL))
ST = [s for s in ST_ALL if s[0] in (-64, -60, -56, -48, -40, -32, -24, -16, -8, 0, 8, 16, 24, 32, 40, 48, 56, 60, 64)]
# (all 33 stations made every boolean on the loft 5-60 s and the shut-line pass > 20 min: thinned, NOTES r3)
WING_X = (-10.0, 30.0)        # thumb-rest span [TOP] rows 440-640 (left flare)
WING_TOP = 13.0               # thumb-rest top surface height [LEFT] (below G6 sniper button)
WING_GAP = 1.5                # main-body left side inset under the thumb rest [TOP]/[BACK] mirror of right side


def section(x, yl, yr, zt, zb, n=28, pt=2.3, pb=5.0):
    """Closed YZ section: superellipse, top half exp pt, flat-ish bottom half exp pb, widest at 35 % height."""
    zb = zb - 1.5 if zb < 1.0 else zb              # dips below z=0 only where the pad is flat; split flat afterwards
    zm = zb + 0.35 * (zt - zb)
    yc, a = (yl + yr) / 2, (yr - yl) / 2
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        p, h = (pt, zt - zm) if s >= 0 else (pb, zm - zb)
        pts.append(Vector(x, yc + a * math.copysign(abs(c) ** (2 / p), c), zm + h * math.copysign(abs(s) ** (2 / p), s)))
    return make_face(Spline(*pts, periodic=True))


def main_left(X, yl, yr):
    return max(yl, -(yr + WING_GAP)) if WING_X[0] - 6 <= X <= WING_X[1] + 6 else yl


# ---- main shell (top cover + side walls, one loft); tiny end stations stand in for the caps (cap fillet segfaults)
def main_loft(d=0.0, z_pad=0.0):
    """d != 0: analytic offset = same stations inflated by d (OCCT offset_3d fails on this loft: kit gap, NOTES)."""
    secs = [section(-66.0 - d, -9.0 - d, 9.0 + d, 12.0 + d, 8.5 - d, pb=2.3)]   # blunt button tips, ~18 mm wide [TOP] row 125
    secs += [section(X, main_left(X, yl, yr) - d, yr + d, zt + d, zb - d) for X, yl, yr, zt, zb in ST]
    secs += [section(66.0 + d, -5.0 - d, 6.0 + d, 13.0 + d, 9.5 - d, pb=2.3)]    # rear lip ~11 mm wide [TOP] row 845
    lo = loft(secs)
    return lo if z_pad is None else lo.split(Plane.XY.offset(z_pad), keep=Keep.TOP).fix()   # cut() by a half-space box failed all 3 paths (kit gap)


body = main_loft()

# ---- thumb rest (separate moulding on the real mouse) [TOP]/[LEFT]
wst = [(X, yl, yr) for X, yl, yr, zt, zb in ST_ALL if WING_X[0] <= X <= WING_X[1]]
wsec = []
for i, (X, yl, yr) in enumerate(wst):
    inner = -(yr + WING_GAP) + 6.0
    outer = yl if 0 < i < len(wst) - 1 else -(yr + WING_GAP) - 1.0
    wsec.append(section(X, outer, inner, WING_TOP if 0 < i < len(wst) - 1 else WING_TOP - 4, 0.0, pt=2.0, pb=6.0))
wing = loft(wsec)
wing = wing.split(Plane.XY, keep=Keep.TOP).fix()

# ================= features (all positions from [TOP] px -> mm: X=-66+(row-99)*0.179, Y=(col-562)*0.179)
GROOVE_W, GROOVE_D = 0.7, 0.9          # shut-line width / depth (typical moulded split; not measurable from photos)


def seg_xy(p, q, z0, z1, t=GROOVE_W):
    """Vertical fence along an XY segment (cuts a shut line seen from above)."""
    (x0, y0), (x1, y1) = p, q
    ln = math.hypot(x1 - x0, y1 - y0)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * (Rot(0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0)))
                                                               * Box(ln + t, t, z1 - z0))


def seg_xz(p, q, y0, y1, t=GROOVE_W):
    """Fence along an XZ segment (shut line on a side wall seen from the side)."""
    (x0, z0), (x1, z1) = p, q
    ln = math.hypot(x1 - x0, z1 - z0)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * (Rot(0, -math.degrees(math.atan2(z1 - z0, x1 - x0)), 0)
                                                               * Box(ln + t, y1 - y0, t))


def poly_xy(pts, z0, z1):
    return [seg_xy(pts[i], pts[i + 1], z0, z1) for i in range(len(pts) - 1)]


# centre strip (wheel, wheel-mode button, G9) between the L/R primary buttons: cols 537..607 -> Y -4.5..8.1
STRIP_Y = (-4.5, 8.1)
STRIP_END = (2.2, -1.7)                 # strip rear corners X at left / right (V apex rows 480 / 458)
R_BTN_REAR = [(-1.7, 8.1), (4.9, 31.9), (5.5, 40.0)]      # right primary button rear edge rows 458-495
L_BTN_REAR = [(2.2, -4.5), (12.0, -25.4), (13.0, -40.0)]  # left primary button rear edge rows 480-535
DPI_EDGE_Y = -21.8                       # inner edge of G7/G8 (cols ~440)
G8_X, G7_X = (-51.5, -36.3), (-36.3, -23.8)  # rows 180-265 / 265-335
fences = [seg_xy((-70, STRIP_Y[0]), (STRIP_END[0], STRIP_Y[0]), 20, 50),
          seg_xy((-70, STRIP_Y[1]), (STRIP_END[1], STRIP_Y[1]), 20, 50),
          seg_xy((STRIP_END[0], STRIP_Y[0]), (STRIP_END[1], STRIP_Y[1]), 30, 50)]
fences += poly_xy(R_BTN_REAR, 22, 50) + poly_xy(L_BTN_REAR, 24, 50)
fences += [seg_xy((G8_X[0], DPI_EDGE_Y), (G7_X[1], DPI_EDGE_Y), 22, 50)]
fences += [seg_xy((x, DPI_EDGE_Y), (x - 1.0, -40.0), 18, 50) for x in (G8_X[0], G7_X[0], G7_X[1])]
# right-side grip panel break [SIDE]: top edge cols 305->930 rows 405->505, rear edge cols 305->240 rows 405->600.
# Z from the elevated shot is unreliable -> registered to the crest-relative heights 22 mm (rear) / 13 mm (front).
GRIP_R = [(46.7, 1.0), (36.8, 22.0), (-56.0, 13.0)]
fences += [seg_xz(GRIP_R[i], GRIP_R[i + 1], 15, 50) for i in range(2)]

_prog('body_clean = body')
body_clean = body
outer_loft = main_loft(1.6, z_pad=None)     # pad plane moved off z=0: coplanar pads broke the booleans
skin_in = main_loft(-GROOVE_D, z_pad=None)                       # 3D offset of the clean loft (before any feature)
# per-fence: (fence & body) - (fence & inner) keeps every boolean small (body - inner loft hung > 500 s in OCCT)
def groove(f):
    outer = common(f, outer_loft, "fence&outer")   # tool pokes 1.6 mm out: no coincident faces with the skin
    try:
        return cut(outer, common(f, skin_in, "fence&inner"), "groove")
    except CadOpError:          # fence never reaches below the skin (empty common) -> whole piece is skin
        return outer


grooves = []
for f in fences:
    grooves.append(groove(f)); _prog("groove")
_prog('GROOVE_FAIL = []')
GROOVE_FAIL = []
for i, g in enumerate(grooves):
    try:
        body = cut(body, g, f"shut line {i}"); _prog(f"cut {i}")
    except CadOpError as e:
        GROOVE_FAIL.append(i)

_prog('# ---- scroll wheel')
# ---- scroll wheel slot + wheel: slot rows 228..355 cols 545..605 -> X -42.9..-20.2, Y -3.0..7.7
WHEEL_X, WHEEL_Y = -31.5, 2.3
SLOT_L, SLOT_W = 22.7, 10.7
WHEEL_D, WHEEL_T = 24.0, 7.5            # chord seen 22.7 mm -> D ~24; width from cols 556..598
WHEEL_Z = 23.5                          # wheel crown ~1.5 mm proud of the 36 mm crest line [SIDE]
body = cut(body, Pos(WHEEL_X, WHEEL_Y, 30) * extrude(RectangleRounded(SLOT_L, SLOT_W, 2.5), 25), "wheel slot")
wheel = Pos(WHEEL_X, WHEEL_Y, WHEEL_Z) * (Rot(90, 0, 0) * Cylinder(WHEEL_D / 2, WHEEL_T))
wheel = safe_fillet(wheel, wheel.edges(), 1.2, label="wheel tyre edge")
ribs = [Pos(WHEEL_X, WHEEL_Y, WHEEL_Z) * (Rot(0, a, 0) * Pos(WHEEL_D / 2, 0, 0) * Box(1.6, WHEEL_T - 2.0, 1.2))
        for a in range(0, 360, 20)]                     # 18 notches: rubber tyre tread of the metal wheel
wheel = cut(wheel, ribs, "wheel tread")

_prog('# ---- G9 + wheel-mo')
# ---- G9 + wheel-mode buttons in the strip (rows 430-460 / 375-410)
small = []
for (xa, xb, ya, yb) in ((-6.7, -1.4, 0.5, 6.4), (-16.6, -10.3, -1.3, 6.8)):
    tool = Pos((xa + xb) / 2, (ya + yb) / 2, 30) * extrude(RectangleRounded(xb - xa, yb - ya, 1.2), 20)
    body = cut(body, tool, "button pocket")
    ct = Pos((xa + xb) / 2, (ya + yb) / 2, 30) * extrude(RectangleRounded(xb - xa - 0.6, yb - ya - 0.6, 0.9), 20)
    small.append(cut(common(Pos(0, 0, -0.6) * body_clean, ct, "cap"), common(Pos(0, 0, -2.6) * body_clean, ct, "cap in"),
                     "button cap 2 mm, 0.6 mm sunk"))

_prog('# ---- thumb buttons')
# ---- thumb buttons G5 / G4 / G6 sniper + DPI LED bar on the left wall, as skin-following caps [LEFT]+[TOP]
# X: average of [TOP] rows 345-525 and [LEFT] cols 385-745 mappings (they disagree by ~8 mm, see NOTES); Z from [LEFT].
THUMB = {"G5": (-19.0, -4.0, 20.0, 24.5), "G4": (-3.6, 13.0, 20.0, 24.5), "G6": (-24.0, -9.0, 8.5, 15.5),
         "dpi_led": (-17.0, 2.0, 25.5, 29.0)}
caps = {}
for k, (xa, xb, za, zb) in THUMB.items():
    bx = Pos((xa + xb) / 2, -40, (za + zb) / 2) * Box(xb - xa, 20, zb - za)
    caps[k] = cut(common(outer_loft, bx, k), common(body_clean, bx, k + " body part"), k + " minus body")
# (0.5 mm edge fillet on these 1.6 mm skin caps hung safe_fillet > 10 min in r3: left sharp, NOTES)

_prog('PARTS = {')
PARTS = {"shell": (body, "#1c1d1f"), "thumb_rest": (wing, "#232427"), "wheel": (wheel, "#5a5d62"),
         "g9": (small[0], "#2a2b2e"), "mode": (small[1], "#2a2b2e"), "G5": (caps["G5"], "#2a2b2e"),
         "G4": (caps["G4"], "#2a2b2e"), "G6": (caps["G6"], "#3a3c40"), "dpi_led": (caps["dpi_led"], "#4fa8ff")}

SPEC = {"L": L_SPEC / 1000, "W": W_SPEC / 1000, "H": H_SPEC / 1000}
