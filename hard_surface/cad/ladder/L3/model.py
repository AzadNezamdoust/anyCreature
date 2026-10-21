"""L3 hard: cordless power drill. Lofted motor housing (elliptic stations), handle SWEPT along a curved spline,
filleted boolean blend handle<->housing on curved faces, axial vents patterned around the curved rear housing,
revolved chuck with grip flutes, trigger, battery pack. Authored in mm; front (chuck) at -X."""
from cadkit import *
import math

UNITS = "mm"

# ---------------- motor housing: loft through elliptic stations along X
ST = [(-72, 19, 19), (-62, 23, 24), (-35, 27, 29), (0, 28.5, 31), (35, 28, 31), (58, 25, 28), (70, 20, 23),
      (75, 13.5, 16), (77.5, 4, 5)]
house = loft([Plane.YZ.offset(x) * Ellipse(ry, rz) for x, ry, rz in ST])
# (rear-cap fillet on loft end failed at every r, r1 -> closing near-point station instead)

# ---------------- handle: elliptic section swept along a curved spine, raked back
spine = Spline((2, 0, 5), (8, 0, -40), (20, 0, -90), (30, 0, -122), tangents=[(0.05, 0, -1), (0.35, 0, -1)])
t0 = spine % 0
sec = Plane(origin=spine @ 0, x_dir=(0, 1, 0), z_dir=t0) * Ellipse(16.5, 21)
handle = sweep(sec, path=spine)
body = fuse(house, handle, "handle+housing")
blend = new_edges(body, house, handle)
body = safe_fillet(body, blend, 7.0, label="handle blend (curved boolean)")

# ---------------- vents: 7 axial slots x 2 sides, patterned around the X axis on the curved rear housing
vents = []
for side in (-1, 1):
    for k in range(7):
        a = side * (40 + k * 14)                       # degrees around +X from +Z
        v = Pos(46, 0, 0) * Rot(a, 0, 0) * Pos(0, 0, 30) * Box(16, 2.6, 8)
        vents.append(v)
body = cut(body, vents, "vents")
vrim = [e for e in body.edges() if 36 < e.center().X < 56 and e.center().Z > -20 and e.length < 20
        and abs(e.center().Y) > 3]
try:
    body = safe_fillet(body, vrim, 0.7, label="vent rims")
except CadOpError:
    pass  # logged as failed; vents stay sharp

# ---------------- trigger: profile in XZ, extruded in Y, filleted
tp = Spline((-14, -30), (-20, -36), (-22, -48), (-17, -58), tangents=[(-0.6, -1), (0.6, -1)]) + \
    Polyline((-17, -58), (-8, -56), (-6, -32), (-14, -30))
trig = extrude(Plane.XZ * make_face(tp), amount=5.5, both=True)
trig = safe_fillet(trig, trig.edges(), 2.2, label="trigger")

# ---------------- chuck + collar (revolved about X), grip flutes
cp = Polyline((-72, 0), (-72, 17.5), (-77, 18), (-79, 16.5), (-81, 16.5), (-82, 18), (-104, 16.5), (-112, 13),
              (-118, 7), (-123, 6), (-123, 0), close=True)
chuck = revolve(Plane.XY * make_face(cp), Axis.X)
chuck = safe_fillet(chuck, [e for e in chuck.edges() if e.geom_type == GeomType.CIRCLE and e.center().X < -110],
                    1.5, label="chuck nose")
flutes = [Rot(a, 0, 0) * Pos(-93, 0, 17.6) * Box(18, 2.2, 3) for a in range(0, 360, 20)]
chuck = cut(chuck, flutes, "chuck flutes")
chuck = cut(chuck, Pos(-122, 0, 0) * (Rot(0, 90, 0) * Cylinder(3.5, 12)), "bit bore")
collar = revolve(Plane.XY * make_face(Polyline((-70, 0), (-70, 20.5), (-66, 21), (-60, 25.5), (-60, 0),
                                                close=True)), Axis.X)
collar = safe_fillet(collar, collar.edges().filter_by(GeomType.CIRCLE), 1.0, label="collar")

# ---------------- battery pack + foot
bat = Pos(36, 0, -138) * Box(84, 64, 30)
bat = safe_fillet(bat, bat.edges().filter_by(Axis.Z), 9.0, label="battery verticals")
bat = safe_fillet(bat, bat.edges(), 3.5, label="battery rim")
latch = Pos(78, 0, -132) * Box(6, 30, 10)
latch = safe_fillet(latch, latch.edges(), 1.5, label="latch")
bat = fuse(bat, latch, "latch")
foot = Pos(32, 0, -121) * Box(66, 46, 10)
foot = safe_fillet(foot, foot.edges().filter_by(Axis.Z), 10.0, label="foot verticals")
b0 = body
body = fuse(body, foot, "foot")
fb = new_edges(body, b0, foot)
body = safe_fillet(body, fb, 3.5, label="foot blend")

PARTS = {"housing": (body, "#c9a23a"), "trigger": (trig, "#202124"), "chuck": (chuck, "#2a2b2e"),
         "collar": (collar, "#3b3d41"), "battery": (bat, "#202124")}
SPEC = {"L": 0.20, "H": 0.18}
