from cadkit import *
import math

OLIVE, GREY, WIN = "#5d6b3a", "#3c3f42", "#a8b4bd"


def prism_x(r, x0, x1, y=0.0, z=0.0, n=8):
    """n-sided prism along X from x0 to x1 (x0<x1)."""
    p = extrude(RegularPolygon(r, n, rotation=180 / n), amount=x1 - x0)
    return Pos(x0, y, z) * (Rot(0, 90, 0) * p)


def planform(pts, z):
    return Plane.XY.offset(z) * Polygon(*pts, align=None)


def sym(half):  # half = list of (x,y) on +Y side from front to rear -> closed loop CCW
    return half + [(x, -y) for x, y in reversed(half)]


# ---------------- turret body: loft lower ring -> belt -> roof (sloped cheeks + wedge front)
low = sym([(-1.75, 0.55), (-1.25, 1.55), (1.55, 1.55), (1.9, 1.25)])
belt = sym([(-2.05, 0.65), (-1.35, 1.8), (1.65, 1.8), (2.05, 1.4)])
roof = sym([(-1.45, 0.55), (-0.95, 1.45), (1.5, 1.45), (1.9, 1.15)])
lower = loft([planform(low, 0.0), planform(belt, 0.35)])
upper = loft([planform(belt, 0.35), planform(roof, 0.95)])
body = fuse(lower, upper, "belt")
# bustle at rear
bustle = Pos(2.15, 0, 0.6) * Box(0.7, 2.3, 0.6)
body = fuse(body, bustle, "bustle")
body = safe_chamfer(body, edges_on_plane(body, "z", side="max"), 0.06, label="roof edge")
# loader hatch plate (left, -Y) + small ring
hatch = Pos(0.2, -0.65, 0.98) * Box(0.85, 0.75, 0.07)
hatch = safe_chamfer(hatch, hatch.edges().group_by(Axis.Z)[-1], 0.03, label="hatch")
body = fuse(body, hatch, "hatch")

# ---------------- gun: mantlet + stepped barrel (pivot at trunnion x=-1.8, z=0.55)
PIV = (-1.8, 0, 0.55)
mant = Pos(-2.1, 0, 0.55) * Box(0.7, 0.9, 0.7)
mant = safe_chamfer(mant, mant.edges().group_by(Axis.X)[0], 0.12, label="mantlet front")
gun = mant
for (r, a, b) in [(0.2, -2.75, -2.4), (0.15, -4.3, -2.7), (0.22, -4.9, -4.25),
                  (0.13, -6.8, -4.85), (0.18, -7.15, -6.75)]:
    gun = fuse(gun, prism_x(r, a, b, z=0.55), f"barrel r{r}")
gun = cut(gun, prism_x(0.08, -7.2, -6.9, z=0.55), "bore")

# ---------------- commander cupola (right, +Y), octagonal with vision blocks
CX, CY, CZ = 0.55, 0.7, 0.95
cup = Pos(CX, CY, CZ) * extrude(RegularPolygon(0.5, 8), amount=0.32)
cup = safe_chamfer(cup, cup.edges().group_by(Axis.Z)[-1], 0.06, label="cupola rim")
lid = Pos(CX, CY, CZ + 0.32) * extrude(RegularPolygon(0.38, 8), amount=0.08)
cup = fuse(cup, lid, "lid")
hinge = Pos(CX + 0.35, CY, CZ + 0.38) * Box(0.12, 0.3, 0.1)
cup = fuse(cup, hinge, "hinge")
wins = []
for i in range(8):
    if i in (0,):  # rear faces hinge side
        continue
    a = math.radians(i * 45)
    d = 0.5 * math.cos(math.pi / 8)
    wins.append(Pos(CX + d * math.cos(a), CY + d * math.sin(a), CZ + 0.17)
                * Rot(0, 0, i * 45) * Box(0.06, 0.2, 0.11))
windows = wins[0]
for w in wins[1:]:
    windows = fuse(windows, w, "win")

# ---------------- roof MG on pintle, in front of cupola
mg = Pos(-0.25, 0.75, 1.15) * Cylinder(0.05, 0.4)
mg = fuse(mg, Pos(-0.3, 0.75, 1.38) * Box(0.35, 0.14, 0.15), "mg body")
mg = fuse(mg, prism_x(0.03, -1.05, -0.45, y=0.75, z=1.40, n=6), "mg barrel")
mg = fuse(mg, Pos(-0.15, 0.75, 1.5) * Box(0.18, 0.12, 0.1), "mg box")

# ---------------- smoke launchers: 4 tubes per flank front corner, angled forward/up
smoke = None
for side in (-1, 1):
    base = Pos(-1.05, side * 1.62, 0.55) * Box(0.35, 0.18, 0.4)
    grp = base
    for dy, dz in ((-0.07, -0.08), (0.07, -0.08), (-0.07, 0.08), (0.07, 0.08)):
        t = prism_x(0.065, -0.45, 0.0, n=8)
        t = Pos(-1.1, side * 1.62 + dy * 1.4, 0.62 + dz * 1.4) * (Rot(0, 25, side * 15) * t)
        grp = fuse(grp, t, "smoke tube")
    smoke = grp if smoke is None else fuse(smoke, grp, "smoke side")

PARTS = {
    "turret": (body, OLIVE),
    "gun": (gun, GREY),
    "cupola": (cup, OLIVE),
    "cupola_windows": (windows, WIN),
    "roof_mg": (mg, GREY),
    "smoke_launchers": (smoke, GREY),
}
SPEC = {"L": 9.65, "W": 3.6, "H": 1.55}
TRI_BUDGET = 6000
