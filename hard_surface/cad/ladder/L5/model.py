"""L5: sports coupe body. ONE lofted surface through 13 full-car cross-sections (rocker, shoulder bulge, belt,
tumblehome greenhouse, roof) -> smooth single-face main body; wheel arches cut with fused flare lips (filleted);
glass (windshield / side DLO / backlight) recessed into the body skin + separate glass bodies inset along the
surface; shut lines (doors, hood, decklid) as grooves following the skin; recessed head/tail lights with lenses;
5-spoke wheels + tyres (revolved). Authored in mm; front -X, Z up."""
from cadkit import *
import math

UNITS = "mm"


def section(x, w, zs, zb, zr, wr, z0=180.0):
    """Half-section points (y>=0) bottom-centre -> roof-centre, mirrored; closed periodic spline in plane x."""
    half = [(0.0, z0), (0.62 * w, z0 + 2), (0.86 * w, z0 + 40), (0.985 * w, zs - 170), (1.0 * w, zs),
            (0.965 * w, zb), (wr + 0.42 * (0.95 * w - wr), zb + 0.42 * (zr - zb)), (wr, zr - 0.12 * (zr - zb)),
            (0.45 * wr, zr - 4)]
    pts = half[:1] + half[1:] + [(0.0, zr)] + [(-y, z) for y, z in reversed(half[1:])]
    return make_face(Spline(*[Vector(x, y, z) for y, z in pts], periodic=True))


#     x      w    zs   zb    zr    wr    z0      (r4: lower roof, tapered nose/tail, tucked rocker)
ST = [(-2250, 240, 400, 440, 465, 170, 250),
      (-2215, 600, 450, 530, 570, 450, 225),
      (-2080, 840, 545, 650, 700, 620, 200),
      (-1750, 915, 615, 760, 800, 690, 185),
      (-1180, 945, 660, 840, 880, 690, 180),
      (-720, 955, 675, 860, 1050, 590, 180),
      (-250, 962, 685, 875, 1170, 555, 180),
      (300, 972, 690, 885, 1165, 555, 180),
      (850, 982, 690, 895, 1050, 600, 180),
      (1350, 968, 685, 905, 960, 690, 185),
      (1850, 900, 670, 885, 920, 690, 195),
      (2195, 760, 630, 845, 870, 590, 220)]   # r4: a narrower closing tail station broke 3D offset (weights)
body = loft([section(*s_) for s_ in ST])
bare = body

# ---- skin layers on the CLEAN loft (3D offsets fail once features exist: L2/L4 lesson)
# r5: OCCT offset_3d of this loft returned INVALID solids (vol 1e6 vs 6e9) -> "parametric offset": re-loft the
# same stations with the section parameters pulled in by d (exact in YZ, ~cos(slope) on raked faces).
def inner(d):
    st = []
    for i, (x, w, zs, zb, zr, wr, z0) in enumerate(ST):
        x2 = x + d if i == 0 else (x - d if i == len(ST) - 1 else x)
        st.append((x2, w - d, zs, zb, zr - d, wr - d, z0 + d))
    return loft([section(*s_) for s_ in st])


in3, in7, in12 = inner(3), inner(7), inner(12)
# (r1: body - in3 'skin' boolean failed plain/fuzzy/manifold on the 4.4 m loft -> never build skins; instead
#  tool - inner_offset = the part of a tool within d of the surface (plus air outside, harmless for a cut))

# ---- glass tools: windshield / backlight from the top (XY), side DLO from the side (XZ), clear of each other
ws = extrude(Pos(0, 0, 845) * Polygon((-1060, -545), (-300, -545), (-300, 545), (-1060, 545), align=None), 600)
ws = safe_fillet(ws, ws.edges().filter_by(Axis.Z), 120, label="windshield corners")
bl = extrude(Pos(0, 0, 915) * Polygon((700, -500), (1400, -470), (1400, 470), (700, 500), align=None), 500)
bl = safe_fillet(bl, bl.edges().filter_by(Axis.Z), 110, label="backlight corners")
dlo_o = Spline((-900, 900), (-540, 1040), (-120, 1110), (420, 1100), (900, 990), (1110, 915), (300, 902),
               periodic=True)
dlo = [Pos(0, s * 600, 0) * extrude(Plane.XZ * make_face(dlo_o), amount=-s * 600) for s in (1, -1)]
glass_tools = [ws, bl] + dlo
for k, t in enumerate(glass_tools):
    body = cut(body, cut(t, in7, f"glass recess tool {k}"), f"glass recess {k}")
glass = [cut(common(in3, t, f"glass {k}"), in12, f"glass back {k}") for k, t in enumerate(glass_tools)]
glass = Compound(glass)

# ---- shut lines: grooves = thin plates & 3 mm skin (they follow the body surface)
plates = [Pos(-960, 0, 560) * Box(5, 2400, 700),   # door front (A-post) cut
          Pos(330, 0, 560) * Box(5, 2400, 700)]    # door rear cut
plates += [Pos(-1600, s * 640, 900) * Box(1000, 5, 300) for s in (1, -1)]       # hood side lines
plates += [Pos(-1105, 0, 900) * Box(5, 1290, 300)]                                # hood rear line
plates += [Pos(1840, s * 610, 950) * Box(760, 5, 300) for s in (1, -1)]         # decklid side lines
plates += [Pos(1460, 0, 960) * Box(5, 1230, 300)]                                 # decklid front line
for k, pl in enumerate(plates):
    try:
        body = cut(body, cut(pl, in3, f"shut tool {k}"), f"shut line {k}")
    except CadOpError:
        pass

# ---- wheel arches with flare lips
WX, WZ, RT = (-1400, 1360), 330, 330
for x in WX:
    for s in (1, -1):
        lip = Pos(x, s * 900, WZ) * (Rot(90, 0, 0) * (Cylinder(445, 150) - Cylinder(372, 160)))
        lip = common(lip, Pos(x, s * 900, WZ + 560) * Box(1200, 300, 1000), "lip upper half")
        b0 = body
        body = fuse(body, lip, "flare lip")
        try:
            body = safe_fillet(body, new_edges(body, b0, lip), 25, label="flare blend")
        except CadOpError:
            pass
    arch = Pos(x, 0, WZ) * (Rot(90, 0, 0) * Cylinder(372, 2600))
    body = cut(body, arch, "wheel arch")
arim = [e for e in body.edges() if e.geom_type == GeomType.CIRCLE and abs(e.radius - 372) < 1]
try:
    body = safe_fillet(body, arim, 10, label="arch rims")
except CadOpError:
    pass

# ---- recessed lights + lenses
hl_tool = [Pos(-2150, s * 640, 610) * (Rot(0, 0, s * 18) * Box(260, 380, 95)) for s in (1, -1)]
hl_tool = [safe_fillet(t, t.edges(), 40, label="headlight tool") for t in hl_tool]
tl_tool = [Pos(2215, 0, 790) * Box(120, 1300, 70)]
tl_tool = [safe_fillet(t, t.edges().filter_by(Axis.X), 30, label="taillight tool") for t in tl_tool]
lights = hl_tool + tl_tool
body = cut(body, lights, "light pockets")
head = common(bare, [Pos(14, 0, 0) * t for t in hl_tool], "head lenses")
tail = common(bare, [Pos(-12, 0, 0) * t for t in tl_tool], "tail lens")
grille = Pos(-2190, 0, 400) * Box(200, 900, 130)
grille = safe_fillet(grille, grille.edges().filter_by(Axis.X), 55, label="intake tool")
body = cut(body, grille, "front intake")

# ---- wheels: tyre + 5-spoke rim (revolved about Y), instanced to 4 corners
tyre = revolve(Plane.XY * make_face(Polyline((170, -115), (RT - 20, -120), (RT, -95), (RT, 95), (RT - 20, 120),
                                             (170, 115), close=True)), Axis.Y)
tyre = safe_fillet(tyre, [e for e in tyre.edges() if e.geom_type == GeomType.CIRCLE and e.radius > 300], 18, label="tyre shoulder")
rim = Cylinder(245, 210)
rim = Rot(90, 0, 0) * rim
dish = Pos(0, -95, 0) * (Rot(90, 0, 0) * Cylinder(215, 40))
rim = cut(rim, dish, "rim face recess")
wins = []
for k in range(5):
    a = 72 * k + 36
    win = Rot(0, a, 0) * Pos(0, -60, 145) * (Rot(90, 0, 0) * extrude(
        Polygon((-62, -70), (62, -70), (28, 60), (-28, 60), align=None), 200, both=True))
    wins.append(win)
rim = cut(rim, wins, "spoke windows")
try:
    rim = safe_fillet(rim, [e for e in rim.edges() if e.length < 200 and abs(e.center().Y) < 100], 6,
                      label="spoke edges")
except CadOpError:
    pass
hub = Pos(0, -80, 0) * (Rot(90, 0, 0) * Cylinder(55, 30))
rim = fuse(rim, hub, "hub")
WH = []
for x in WX:
    for s in (1, -1):
        y = s * 835
        # rim face points outward (-Y side of the part faces -Y): mirror for the +Y side
        r_ = rim if s < 0 else rim.mirror(Plane.XZ)
        t_ = tyre
        WH.append((Pos(x, y, WZ) * r_, Pos(x, y, WZ) * t_))

PARTS = {"body": (body, "#9e1b1b"), "glass": (glass, "#1a222b"), "headlights": (head, "#e8eef2"),
         "taillights": (tail, "#7a0a0a")}
for i, (r_, t_) in enumerate(WH):
    PARTS[f"rim{i}"] = (r_, "#b9bcc0")
    PARTS[f"tyre{i}"] = (t_, "#1b1c1e")
SPEC = {"L": 4.44, "W": 1.97, "H": 1.25}
