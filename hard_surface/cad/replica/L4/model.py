"""L4 replica: Xbox Wireless Controller (Xbox Series X|S, model 1914). Authored in mm.

Frame: X = depth (-X = bumper/trigger edge facing away from the player, +X = grip tips), Y = width (+Y = ABXY side),
Z up (Z=0 = grip bottoms resting on a table).
Sources (see REFS.md):
  [S1] overall 153 x 102 x 61 mm, 287 g - Wikipedia infobox / Clubic / Backmarket (model 1914)
  [P1] top-down photo  refs/L4/Xbox_Series_Controller_Carbon_Black.jpg  (plan outline + every face feature; traced
       px -> mm with sx = 102/705 px (depth), sy = 153/988 px (width); face-feature centreline = px 695)
  [P2] rear photo      refs/L4/Xbox_Series_Controller_Gold_Shadow_Special_Edition_top.jpg (rear elevation, USB-C,
       sync button, battery-door line, top/bottom shell split, bumper/trigger forms)
  [P3] side photo      refs/L4/Xbox_Series_SX_Controller_Starfield_Limited_Edition_Right_Side.jpg (side profile,
       grip texture panel break)
"""
import math
from cadkit import *

UNITS = "mm"
TRI_BUDGET = 20000

# ---------------- overall [S1]
W, D, H = 153.0, 102.0, 61.0          # width, depth, height incl. thumbstick caps
HALF_W = W / 2

# ---------------- plan outline, right half (X, Y), traced from [P1], symmetrised
PLAN_R = [(-49.5, 0), (-49.5, 22), (-49.0, 32), (-48.0, 40), (-46.0, 47), (-42.5, 53.5), (-35, 59.5), (-23.5, 65.5),
          (-9, 70), (4, 73.4), (15.6, 75.5), (27, 76.5), (38.7, 75.3), (45.5, 72), (49.6, 66.5), (50.5, 60),
          (48.5, 54), (43, 48), (36, 41.5), (30, 36), (26.5, 30.5), (25.6, 22), (25.5, 0)]
# ---------------- side profile (X, Z) envelope [P3]+[P2]: top face rises towards the bumpers, grips drop to Z=0
SIDE_TOP = [(-51.5, 42.5), (-46, 47), (-36, 49), (-22, 49), (-8, 47), (6, 43.5), (20, 37.5), (33, 30.5), (44, 25.5),
            (51.5, 21)]   # r4: grip tips stay ~15 mm thick [P3]; r3: +5.5 mm so stick caps (12.5 mm proud of the face, [P2]) top out at the 61 mm spec
SIDE_BOT = [(51.5, 3.5), (47, 0.6), (40, 0.0), (30, 1.5), (18, 5.5), (5, 9.5), (-10, 11.5), (-30, 12.5), (-45, 13.5),
            (-51.5, 15)]
R_TOP = 7.0           # top perimeter round (rear-view mask: shoulder rolls from z~33 at the edge to the top)
R_BOT = 5.0           # bottom perimeter round (rear-view mask: grip underside rolls up to z~17 at |y|=69)

# ---------------- face features [P1] (X, Y) mm, diameters mm
LOGO = (-39.0, 0.0, 13.6)                 # guide button (Xbox logo)
STICK_L = (-23.3, -44.0)                  # left stick; mirrored by the ABXY diamond centre
ABXY_C = (-23.3, 44.0)
ABXY_PITCH = 10.3                         # centre-to-diamond-centre (Y-X, X-A ...)
ABXY_D = 10.0
DPAD_C = (1.8, -24.0)                     # d-pad; mirrored by the right stick
STICK_R = (1.8, 24.0)
DPAD_D = 27.0                             # hybrid d-pad dish outer diameter
STICK_CAP_D, STICK_WELL_D = 21.0, 27.5
VIEW = (-23.9, -12.5)
MENU = (-23.9, 12.5)
SMALL_D = 7.8
SHARE = (-14.8, 0.0, 9.3, 4.6)            # share pill (len, width)
SPLIT_Z = 31.0
STICK_PROUD = 12.5                         # cap top above the local face [P2] (rear view: caps ~0.8 cap-dia above shell)                            # top/bottom shell split height at the rim [P2]

DROP = 11.0                               # top face falls ~11 mm from centreline to the side rim [P2]

def spline_face(pts, plane):
    return make_face(plane * Spline(*[Vector(*p) for p in pts], periodic=True))

_sx = [p[0] for p in SIDE_TOP]; _sz = [p[1] for p in SIDE_TOP]
def ztop(x, y):
    """Top skin height (analytic copy of the lofted top tool) - used to seat face features."""
    import numpy as np
    return float(np.interp(x, _sx, _sz)) - DROP * min(1.0, abs(y) / HALF_W) ** 2.5

def top_section(x):
    ys = [-95 + 190 * i / 24 for i in range(25)]
    top = Spline(*[Vector(x, y, ztop(x, y) if abs(y) <= HALF_W else ztop(x, HALF_W) - (abs(y) - HALF_W) * 0.6)
                   for y in ys])
    p0, p1 = top @ 0, top @ 1
    return make_face(Wire([top, Line(p1, Vector(x, 95, -20)), Line(Vector(x, 95, -20), Vector(x, -95, -20)),
                           Line(Vector(x, -95, -20), p0)]))

# ---------------- body: plan extrusion  side-profile underside  lofted domed top skin, then perimeter rounds
plan_pts = PLAN_R + [(x, -y) for x, y in reversed(PLAN_R[1:-1])]
k = plan_pts.index((27, 76.5)); plan_pts = plan_pts[k:] + plan_pts[:k]   # r4: spline seam off the USB-C / jack
plan = extrude(spline_face(plan_pts, Plane.XY), 80)
_bx = [p[0] for p in SIDE_BOT][::-1]; _bz = [p[1] for p in SIDE_BOT][::-1]
CENTRE_RISE = 0.0   # r7 tried 8.0 -> OCCT segfault in the perimeter fillet; reverted. rear mask: underside between the grips sits ~10 mm above the grip bottoms
LIFT = 12.0      # r4: underside rolls up towards the outer rim (rear mask: z~17 at |y|=69, ~33 at the rim)
def zbot(x, y):
    import numpy as np
    return (float(np.interp(x, _bx, _bz)) + LIFT * max(0.0, (abs(y) - 58.0) / (HALF_W - 58.0)) ** 2   # r5: roll only outboard of the grip centre-line
           + CENTRE_RISE * max(0.0, 1 - (y / 34.0) ** 2) ** 2 * min(1.0, max(0.0, (x + 5) / 22.0)))  # r7

def bot_section(x):
    ys = [-95 + 190 * i / 24 for i in range(25)]
    bot = Spline(*[Vector(x, y, zbot(x, y)) for y in ys])
    p0, p1 = bot @ 0, bot @ 1
    return make_face(Wire([bot, Line(p1, Vector(x, 95, 90)), Line(Vector(x, 95, 90), Vector(x, -95, 90)),
                           Line(Vector(x, -95, 90), p0)]))
side = loft([bot_section(x) for x in (-60, -45, -30, -10, 5, 18, 30, 40, 47, 60)])
toptool = loft([top_section(x) for x in (-60, -46, -36, -22, -8, 6, 20, 33, 44, 60)])
body = common(common(plan, side, "plan  underside (lofted, rolled)"), toptool, "  domed top skin")

# r6: the periodic plan wall gives 1-3 long rim edges that wander between top and underside -> round them all at once
body = safe_fillet(body, body.edges(), R_BOT, label="perimeter round (all rim edges)")
BODY0 = body

# ---------------- face features: holes in the shell + separate button parts
def at(x, y, z_off=0.0):
    return Pos(x, y, ztop(x, y) + z_off)

def cyl(d, h, x, y, z0):
    return Pos(x, y, z0) * Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))

parts = {}
dark, abxy_col = "#1b1c1e", {"Y": "#e6c619", "X": "#2c74d6", "B": "#d23a2e", "A": "#5dbb2f"}
holes = []
# sticks: recessed well + shaft + concave knurled-rim cap, cap tops at the 61 mm overall height [S1]
for nm, (x, y) in (("stick_L", STICK_L), ("stick_R", STICK_R)):
    zf = ztop(x, y)
    holes.append(cyl(STICK_WELL_D, 20, x, y, zf - 3.0))
    zc = zf + STICK_PROUD
    shaft = cyl(9.0, zc - zf + 1, x, y, zf - 4.0)
    cap = cyl(STICK_CAP_D, 4.0, x, y, zc - 4.0)
    cap = safe_fillet(cap, cap.edges().sort_by(Axis.Z)[-1:], 1.6, label=nm + " cap rim")
    cap = cut(cap, Pos(x, y, zc + 24.0) * Sphere(24.6), nm + " concave dish")
    ring = cyl(STICK_WELL_D - 1.2, 2.2, x, y, zf - 3.0)  # gimbal skirt filling the well
    ring = fuse(ring, common(Pos(x, y, zf - 9.5) * Sphere(13.0), cyl(STICK_WELL_D - 1.2, 20, x, y, zf - 3.0)), nm + " gimbal dome")
    parts[nm] = (fuse(fuse(shaft, cap, nm), ring, nm + " skirt"), dark)
# ABXY diamond
for nm, (dx, dy) in {"Y": (-1, 0), "A": (1, 0), "X": (0, -1), "B": (0, 1)}.items():
    x, y = ABXY_C[0] + dx * ABXY_PITCH, ABXY_C[1] + dy * ABXY_PITCH
    zf = ztop(x, y)
    holes.append(cyl(ABXY_D + 0.6, 20, x, y, zf - 4))
    b = cyl(ABXY_D, 6.0, x, y, zf - 3.5)
    b = safe_fillet(b, b.edges().sort_by(Axis.Z)[-1:], 2.2, label="btn " + nm)
    parts["btn_" + nm] = (b, abxy_col[nm])
# guide (logo), view, menu, share
for nm, x, y, d, h in (("guide", LOGO[0], LOGO[1], LOGO[2], 4.6), ("view", *VIEW, SMALL_D, 4.4), ("menu", *MENU, SMALL_D, 4.4)):
    zf = ztop(x, y)
    holes.append(cyl(d + 0.6, 20, x, y, zf - 4))
    b = cyl(d, h, x, y, zf - 3.5)
    parts["btn_" + nm] = (safe_fillet(b, b.edges().sort_by(Axis.Z)[-1:], 1.2, label=nm), "#f2f2f2" if nm == "guide" else dark)
x, y, L_, W_ = SHARE
zf = ztop(x, y)
holes.append(Pos(x, y, zf - 4) * extrude(Rot(0, 0, 90) * SlotOverall(L_ + 0.6, W_ + 0.6), 20))
sh = Pos(x, y, zf - 3.5) * extrude(Rot(0, 0, 90) * SlotOverall(L_, W_), 4.3)
parts["btn_share"] = (safe_fillet(sh, sh.edges().sort_by(Axis.Z)[-1:], 1.0, label="share"), dark)
# hybrid d-pad: shallow dish + disc + cross
x, y = DPAD_C
zf = ztop(x, y)
holes.append(cyl(DPAD_D + 0.6, 20, x, y, zf - 4))
disc = cyl(DPAD_D, 4.0, x, y, zf - 3.5)
disc = cut(disc, Pos(x, y, zf + 60) * Sphere(60.0), "d-pad dish")
cross = fuse(Pos(x, y, zf - 1) * Box(22, 7.6, 3.4, align=(Align.CENTER, Align.CENTER, Align.MIN)),
             Pos(x, y, zf - 1) * Box(7.6, 22, 3.4, align=(Align.CENTER, Align.CENTER, Align.MIN)), "d-pad cross")
cross = safe_fillet(cross, cross.edges().filter_by(Axis.Z), 1.0, label="d-pad cross corners")
parts["dpad"] = (fuse(disc, cross, "d-pad"), "#3a3b3e")

body = cut(body, holes, "button / stick openings")

# ---------------- rear face: USB-C, pair button [P2]; front: 3.5 mm jack
body = cut(body, Pos(-52.0, 0, 22.0) * (Rot(0, 90, 0) * extrude(SlotOverall(8.4, 2.6, rotation=90), 6)), "USB-C port")
body = cut(body, Pos(-49.0, -10.5, 29.0) * (Rot(0, 90, 0) * Cylinder(2.6, 8)), "pair button hole")
parts["btn_pair"] = (Pos(-50.2, -10.5, 29.0) * (Rot(0, 90, 0) * Cylinder(2.2, 4)), dark)
body = cut(body, Pos(27.0, 0, 12.0) * (Rot(0, 90, 0) * Cylinder(1.9, 12)), "3.5 mm jack")

# ---------------- bumpers (wrap the shoulders) and triggers (below them, on the rear face) [P1][P2]
def sc(shp, f):
    c = shp.bounding_box().center()
    return Pos(c.X, c.Y, c.Z) * (Pos(-c.X, -c.Y, -c.Z) * shp).scale(f)

bump_shell = cut(sc(BODY0, 1.035), BODY0, "bumper skin")
for sgn, nm in ((1, "R"), (-1, "L")):
    zone = Pos(-46, sgn * 47, 39.0) * Box(16, 30, 8)
    bm = common(bump_shell, zone, "bumper " + nm)
    try:
        bm = safe_fillet(bm, [e for e in bm.edges() if e.length > 2], 0.6, label="bumper edges " + nm)
    except Exception:
        pass
    parts["bumper_" + nm] = (bm, "#2e2f32")
    TP = [(-40, 33.5), (-47, 33.5), (-50.5, 29), (-51, 22), (-49, 15.5), (-45.5, 11.5), (-42.5, 12.5), (-44.5, 17.5), (-45.8, 23), (-44, 29.5)]  # r4: curved lever [P2], inside 102 mm
    def tsec(dy, f):   # trigger section at Y offset dy, shrunk by f about the profile centre -> soft side rounds
        return make_face(Plane.XZ.offset(-(sgn * 49 + dy)) * Spline(
            *[Vector(-46 + (x + 46) * f, 23 + (z - 23) * f) for x, z in TP], periodic=True))
    trig = loft([tsec(-9, 0.82), tsec(-8.2, 0.96), tsec(8.2, 0.96), tsec(9, 0.82)])
    trig = cut(trig, BODY0, "trigger clear of body " + nm)
    parts["trigger_" + nm] = (trig, "#2e2f32")

# ---------------- part breaks: top/bottom shell split groove, battery door [P2]
groove_tool = cut(Pos(0, 0, SPLIT_Z) * Box(200, 200, 0.7), sc(BODY0, 0.985), "split-line ring")
body = cut(body, common(groove_tool, BODY0, "split ring on skin"), "top/bottom shell split")
door = cut(Pos(12.5, 0, -5) * Box(23, 54, 30), Pos(12.5, 0, -5) * Box(22.2, 53.2, 30), "battery door outline")
underskin = cut(BODY0, Pos(0, 0, 0.6) * BODY0, "underside skin")
body = cut(body, common(door, underskin, "door line on skin"), "battery door line")

parts = {"body": (body, "#2a2b2e"), **parts}
PARTS = parts
SPEC = {"L": D / 1000, "W": W / 1000, "H": H / 1000}
