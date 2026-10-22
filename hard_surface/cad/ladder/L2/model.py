"""L2 medium: computer mouse. Curved spline body (plan x side-profile intersection), variable + constant fillets,
shelled to 1.8 mm wall, split lines that follow the curved skin (groove = plate & outer skin layer), scroll-wheel
slot through the curved top, thumb buttons, separate wheel. Authored in mm."""
from cadkit import *

UNITS = "mm"
L, W, H = 120.0, 64.0, 40.0
WALL = 1.8

import math


def section(x, w, ztop, zb=-8.0, n=20, p=2.6):
    """Superellipse cross-section in the YZ plane at station x (closed periodic spline), extends below z=0."""
    h = ztop - zb
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s_ = math.cos(t), math.sin(t)
        pts.append(Vector(x, w / 2 * math.copysign(abs(c) ** (2 / p), c),
                          zb + h / 2 + h / 2 * math.copysign(abs(s_) ** (2 / p), s_)))
    return make_face(Spline(*pts, periodic=True))


# --- loft through 10 stations nose(-X) -> tail; crown peaks just behind the middle
ST = [(-61.5, 3, 1.5), (-60, 16, 5), (-58, 30, 9), (-52, 44, 19), (-40, 52, 26.5), (-20, 56, 32), (0, 58, 35), (20, 62, 35.5),
      (38, 58, 31), (52, 44, 21), (57.5, 26, 13), (60.5, 4, 3)]
body = loft([section(*s_) for s_ in ST])
# (r10: blunt caps + cap_round worked, but the later flat-base cut then fell to Manifold -> kept near-point ends)
body = cut(body, Pos(0, 0, -50) * Box(300, 300, 100), "flat base")
# (nose/tail cap fillet r=3 SEGFAULTED OCCT in round 2 -> end stations shrunk to near-points instead)
# variable fillet on the base rim: 3 mm at the palm (rear) -> 1 mm at the nose
rim = [e for e in body.edges().filter_by_position(Axis.Z, -1e-3, 1e-3) if e.length > 20]
body = variable_fillet(body, rim, 1.0, 2.5, label="base rim variable")

# --- offsets FIRST on the clean lofted body (OCCT 3D offset failed once the slot pocket was in: round 6)
inner = offset(body, amount=-WALL)                   # cavity solid
cav = fuse(inner, extrude(inner.faces().filter_by(GeomType.PLANE).sort_by(Axis.Z)[0], amount=-5), "cavity + bottom opening")
skin_in = offset(body, amount=-0.7)                  # for split-line depth

# --- scroll-wheel slot: pocket + rim fillet on the SOLID (rim fillet on the offset shell failed at any r: r4-5)
slot = Pos(-36, 0, 18) * extrude(RectangleRounded(16, 7.5, 3.6), 30)
body = cut(body, slot, "wheel slot pocket")
slot_rim = [e for e in body.edges() if abs(e.center().X + 36) < 9 and abs(e.center().Y) < 4.5 and e.center().Z > 20]
body = safe_fillet(body, slot_rim, 0.8, label="slot rim")
skin = cut(body, skin_in, "skin layer")
shell = cut(body, cav, "shell = body - cavity")
bottom = body.faces().filter_by(GeomType.PLANE).sort_by(Axis.Z)[0]
inner = skin_in

# --- split lines: centre gap between L/R buttons + transverse line behind the buttons + thumb buttons outline
g_mid = Pos(-38, 0, 30) * Box(48, 0.8, 30)
g_back = Pos(-12, 0, 30) * (Rot(0, 0, 0) * Box(0.8, 80, 30))
grooves = [g_mid, g_back]
for x0 in (-14, 6):  # thumb buttons on the left flank (-Y)
    ring = Pos(x0, -30, 20) * (Rot(90, 0, 0) * (extrude(RectangleRounded(17, 8, 3.5), 20, both=True)
                                                - extrude(RectangleRounded(15.6, 6.6, 2.8), 20, both=True)))
    grooves.append(ring)
groove = common(skin, grooves, "split-line tools on skin")
shell = cut(shell, groove, "split lines")

wheel = Pos(-36, 0, 20.5) * (Rot(90, 0, 0) * Cylinder(10.5, 6))
wheel = safe_fillet(wheel, wheel.edges(), 1.4, label="wheel tyre")
ribs = [Rot(0, a, 0) * Pos(10.6, 0, 0) * Box(1.2, 8, 1.0) for a in range(0, 360, 15)]
wheel = cut(wheel, [Pos(-36, 0, 20.5) * r for r in ribs], "wheel ribs")

# --- base plate with feet
bf = inner.faces().filter_by(GeomType.PLANE).sort_by(Axis.Z)[0]                       # planar bottom of the -0.7 offset solid
c = bf.center()
base = Pos(c.X, c.Y, 0.2) * extrude((Pos(-c.X, -c.Y, -c.Z) * bf).scale(0.955), 1.4)   # 2D offset of a spline face failed

PARTS = {"shell": (shell, "#d8dade"), "wheel": (wheel, "#26282b"), "base": (base, "#3a3c40")}
SPEC = {"L": 0.12, "W": 0.064, "H": 0.040}
