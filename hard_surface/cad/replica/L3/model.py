"""L3 replica: DeWalt DCD777 20V MAX brushless compact drill/driver + DCB201 1.5Ah compact pack.

Side profile registered to the official DeWalt side photo (refs/L3/DCD777C2_1.png, 1680px) with scale from the
dealer spec "head length 7.52 in" = 191 mm  ->  0.13871 mm/px (chuck tip px 144 .. housing rear px 1521).
Every side coordinate below = (px - 1521) * S, (259 - py) * S  (rear of motor housing X=0, chuck axis Z=0).
Widths (Y) are NOT in any ref we found (no front/top view published) -> marked EST, from the 3/4 photo
DCD777B_2 proportions (housing width ~ 0.85 * housing height). Authored in mm; front (chuck) at -X.
"""
from cadkit import *

UNITS = "mm"
S = 191.0 / (1521 - 144)          # mm per px  (REFS.md #1 + spec head length 7.52 in)

# ---------------- overall (ref side photo DCD777C2_1, measured)
HEAD_LEN = 191.0                  # spec 7.52 in (dealer listing, REFS.md #3)
TOP_Z = 33.0                      # top of housing hump  (mask col X=-48: 32.7..33.2)
BOT_Z = -193.8                    # bottom of DCB201 pack (mask)
# ---------------- chuck / clutch / gearcase radii (mask column profile)
CHUCK_TIP_X, CHUCK_NOSE_R = -191.0, 11.0
CHUCK_R = 21.2                    # sleeve, X -169..-140
CLUTCH_X0, CLUTCH_X1, CLUTCH_R = -137.0, -98.0, 27.6
GEAR_X1, GEAR_R = -77.0, 28.6     # black gearcase -> yellow housing break at px 965
# ---------------- widths (EST, no ref)
W_HOUSE = 58.0
W_NOSE = 44.0                     # yellow trigger-housing under the motor
W_GRIP = 40.0
W_TRIG = 13.0
W_FOOT = 74.0
W_BATT = 76.0

# ---------------- chuck + clutch collar + gearcase: revolved from mask radius profile
cp = Polyline((CHUCK_TIP_X, 0), (CHUCK_TIP_X, CHUCK_NOSE_R), (-186, 15.3), (-181.8, 17.0), (-177.7, 18.7),
              (-173.5, 20.1), (-169.4, 21.0), (-140, CHUCK_R), (-138, CHUCK_R), (-138, 0), close=True)

chuck = revolve(Plane.XY * make_face(cp), Axis.X)
# metal nose ring (silver) is the front 8 mm of the chuck in the photo (px 144..205)
nose = revolve(Plane.XY * make_face(Polyline((CHUCK_TIP_X - 0.01, 0), (CHUCK_TIP_X - 0.01, CHUCK_NOSE_R + 0.2),
                                              (-183.0, 16.6), (-183.0, 0), close=True)), Axis.X)
chuck = cut(chuck, Pos(CHUCK_TIP_X, 0, 0) * (Rot(0, 90, 0) * Cylinder(5.0, 30)), "bit bore")
# 6 longitudinal grip ribs (photo: raised flats on sleeve) -> grooves between them
grooves = [Rot(a, 0, 0) * Pos(-153, 0, CHUCK_R) * Box(26, 3.0, 2.4) for a in range(0, 360, 30)]
chuck = cut(chuck, grooves, "sleeve grooves")

clutch = revolve(Plane.XY * make_face(Polyline((-138, 0), (-138, 23.0), (-136.1, 24.4), (-131.9, 26.4),
                                               (-123.6, 27.3), (-111, CLUTCH_R), (CLUTCH_X1, CLUTCH_R),
                                               (CLUTCH_X1, 0), close=True)), Axis.X)
# clutch ring lugs: 16 raised ribs around the torque ring
clutch = cut(clutch, [Rot(a, 0, 0) * Pos(-126, 0, CLUTCH_R + 0.3) * Box(18, 3.2, 2.0) for a in range(0, 360, 24)],
             "clutch grip flutes")
chuck = cut(chuck, nose, "nose ring split")
gear = revolve(Plane.XY * make_face(Polyline((CLUTCH_X1, 0), (CLUTCH_X1, 27.0), (-90, 28.4), (GEAR_X1 - 2, GEAR_R),
                                             (GEAR_X1 - 2, 0), close=True)), Axis.X)

def side_solid(pts, width, r, label, corner=4.0):
    """Side-profile slab: polyline traced from the ref mask, 2D vertex fillets (tangent line/arc chain), extruded in Y,
    rim filleted. (A periodic-spline profile + 3D rim fillet crashed OCCT: heap corruption 0xc0000374 - see NOTES.)"""
    f = make_face(Polyline(*pts, close=True))
    for rc in (corner, corner * 0.6, corner * 0.35, corner * 0.2):
        try:
            g = fillet(f.vertices(), rc)
            if g.is_valid:
                f = g
                break
        except Exception:
            pass
    s = extrude(Plane.XZ * f, amount=width / 2, both=True)
    try:
        s = safe_fillet(s, [e for e in s.edges() if abs(abs(e.center().Y) - width / 2) < 1e-3], r, label=label)
    except CadOpError:
        pass
    return s

# ---------------- motor housing: side profile from mask columns (r5 loft through rounded rects twisted at the seam ->
# replaced by profile slab with big rim round, the same build as the real two-shell clamshell housing)
HOUSE = [(-79, 29.3), (-66, 29.8), (-36, 29.4), (-30, 32.0), (-24, 32.6), (-12, 31.6), (-7, 29.1), (-3.5, 20.0),
         (-1.5, 0.0), (-3.0, -16.6), (-7.0, -23.7), (-12, -32.5), (-20, -35.0), (-79, -33.0)]
house = side_solid(HOUSE, W_HOUSE, 14.0, "housing rim", corner=6.0)
# top hump / belt-hook boss (photo px 1150..1200 top, X -52..-41, Z to 33)
hump = Pos(-46, 0, 31) * Box(13, 22, 5)
hump = safe_fillet(hump, hump.edges().filter_by(Axis.X), 2.0, label="hump")
house = fuse(house, hump, "hump")
# rear side vent slots: 5 horizontal slots each side at rear rim (photo px 1440..1500, Z -13..+20)
vents = [Pos(-8, s * (W_HOUSE / 2 - 3), z) * Box(9, 10, 2.6) for s in (-1, 1) for z in (-12, -5, 2, 9, 16)]
house = cut(house, vents, "rear vents")
# top vent slot + lower slot (photo px 1130..1200 at y 160 and 440)
house = cut(house, [Pos(-48, sy, z) * Box(10, 6, 3) for sy in (-W_HOUSE / 2, W_HOUSE / 2) for z in (13.7, -25.0)], "side slots")

# ---------------- yellow trigger housing / grip core: side profile polygon (mask rows), extruded + rounded

NOSE = [(-114, -24), (-114.5, -37.6), (-108, -43), (-84, -44), (-84, -60), (-60, -60), (-40, -46), (-36.5, -41),
        (-30, -36), (-60, -26)]
nose_h = side_solid(NOSE, W_NOSE, 8.0, "trigger housing rim")
GRIP = [(-86, -40), (-80.2, -72.3), (-78.5, -79.2), (-77.1, -89.6), (-75.0, -96.5), (-72.5, -103.5),
        (-70.2, -110.4), (-69.1, -117.3), (-69.1, -124.3), (-70.5, -132), (-31.5, -132), (-31.9, -120.8),
        (-31.3, -110.4), (-31.6, -96.5), (-32.9, -89.6), (-34.0, -82.7), (-35.9, -75.7), (-37.7, -68.8),
        (-38.8, -61.9), (-39.0, -54.9), (-38.4, -48.0), (-37.0, -40)]
grip = side_solid(GRIP, W_GRIP, 9.0, "grip rim")
# grip ribs (photo: horizontal ribs on the grip, Z -95..-125) -> shallow grooves each side
grip = cut(grip, [Pos(-70, 0, z) * Box(10, W_GRIP + 2, 1.2) for z in range(-122, -94, 4)], "grip ribs")
TRIG = [(-105, -44), (-105.5, -58), (-103, -64), (-96, -66), (-86, -68.5), (-84, -66), (-86, -44)]
trig = side_solid(TRIG, W_TRIG, 3.0, "trigger")
# forward/reverse button (photo px 870..960, y 500..540)
fr = Pos(-80, 0, -42) * Box(12, W_NOSE + 6, 6)
fr = safe_fillet(fr, fr.edges(), 2.5, label="fwd/rev button")

# ---------------- foot (battery interface), mask rows Z -128..-158
FOOT = [(-104, -128), (-110, -134.7), (-117.5, -141.6), (-125, -148.6), (-130.8, -155.5), (-132, -158.5),
        (-20.5, -158.5), (-19.4, -155.5), (-22.2, -148.6), (-25.9, -141.6), (-29.1, -134.7), (-32, -128)]
foot = side_solid(FOOT, W_FOOT, 6.0, "foot rim")
foot = cut(foot, [Pos(x, -W_FOOT / 2, -146) * Box(9, 4, 2.4) for x in (-95, -82, -69, -56)], "foot vents")

# ---------------- DCB201 pack: mask rows Z -158..-193.8
BATT = [(-133, -158.5), (-133.4, -176.3), (-131.4, -186.7), (-125.9, -190.2), (-115, -193.6), (-33.2, -193.6),
        (-26.4, -190.2), (-22.6, -186.7), (-21.4, -179.8), (-21.1, -169.4), (-26.8, -165.9), (-26.8, -162.4),
        (-22.1, -159.0), (-21.5, -158.5)]
batt = side_solid(BATT, W_BATT, 4.0, "battery rim")
# release button pocket front + label recess band
batt = cut(batt, Pos(-133, 0, -172) * Box(5, 26, 9), "release button")
batt = cut(batt, [Pos(-74, sy, -181) * Box(66, 2, 9) for sy in (-W_BATT / 2, W_BATT / 2)], "label band")

YEL, BLK, GRY, SIL = "#f2b705", "#1d1d1f", "#2b2c30", "#c8c9cc"
PARTS = {"housing": (house, YEL), "trigger_housing": (nose_h, YEL), "grip": (grip, BLK), "trigger": (trig, BLK),
         "fwd_rev": (fr, BLK), "gearcase": (gear, BLK), "clutch": (clutch, GRY), "chuck": (chuck, BLK),
         "chuck_nose": (nose, SIL), "foot": (foot, BLK), "battery": (batt, BLK)}
SPEC = {"L": 0.1914, "H": 0.2268}
