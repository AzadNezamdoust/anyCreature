"""L4 very hard: sci-fi helmet. Multi-section loft (7 superellipse stations, compound curvature), shelled 4 mm
(open neck), visor opening cut through the curved front with filleted rim + separate visor glass following the
shell, panel lines following curvature (thin plates & outer skin layer), ear pods and a swept crest fused with
filleted blends, chin vent pockets with all-edge fillets (3-edge corners). Authored in mm; front -X."""
from cadkit import *
import math

UNITS = "mm"
WALL = 4.0


def station(z, a, b, xoff=0.0, n=24, p=2.4):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s_ = math.cos(t), math.sin(t)
        pts.append(Vector(xoff + a * math.copysign(abs(c) ** (2 / p), c),
                          b * math.copysign(abs(s_) ** (2 / p), s_), z))
    return make_face(Spline(*pts, periodic=True))


ST = [(0, 128, 98, -6), (55, 140, 112, -3), (125, 143, 116, -2), (195, 130, 106, 0), (245, 98, 82, 4),
      (275, 55, 46, 8), (289, 14, 12, 10)]
body = loft([station(*s_) for s_ in ST])

# ---- offsets on the CLEAN loft (3D offset fails once features are added - L2 lesson)
cav0 = offset(body, amount=-WALL)
cav = fuse(cav0, extrude(cav0.faces().filter_by(GeomType.PLANE).sort_by(Axis.Z)[0], amount=-10), "neck opening")
skin_in = offset(body, amount=-1.1)
glass_o = offset(body, amount=-WALL - 0.5)
glass_i = offset(body, amount=-WALL - 3.0)
bare = body

# ---- visor: outline in YZ, extruded through the front half
vo = Spline((-100, 150), (-84, 178), (0, 188), (84, 178), (100, 150), (74, 114), (0, 104), (-74, 114),
            periodic=True)
visor_tool = extrude(Plane.YZ * make_face(vo), amount=200)   # Plane.YZ normal +X -> flip below
visor_tool = Pos(-200, 0, 0) * visor_tool
body = cut(body, visor_tool, "visor opening")
vrim = new_edges(body, bare, visor_tool)
body = safe_fillet(body, vrim, 3.0, label="visor rim")

# ---- ear pods (Y-axis), rim-filleted then fused with a blend fillet
for side in (-1, 1):
    pod = Pos(18, side * 112, 118) * (Rot(90, 0, 0) * Cylinder(46, 34))
    pod = safe_fillet(pod, [e for e in pod.edges() if abs(e.center().Y) > 120], 7.0, label="pod rim")
    disc = Pos(18, side * 129.5, 118) * (Rot(90, 0, 0) * Cylinder(30, 3))
    pod = cut(pod, disc, "pod recess")
    b0 = body
    body = fuse(body, pod, "pod fuse")
    body = safe_fillet(body, new_edges(body, b0, pod), 6.0, label="pod blend")

# ---- crest: rectangle swept over the crown, filleted, fused + blended
path = Spline((-105, 0, 200), (-70, 0, 258), (0, 0, 288), (70, 0, 272), (112, 0, 205))
prof = Plane(origin=path @ 0, x_dir=(0, 1, 0), z_dir=path % 0) * Rectangle(22, 16)
crest = sweep(prof, path=path)
crest = safe_fillet(crest, [e for e in crest.edges() if e.length > 100], 4.0, label="crest long edges")
crest = Pos(0, 0, 2) * crest
b0 = body
body = fuse(body, crest, "crest fuse")
try:  # r1: failed at every radius on all 17 intersection edges (sweep x loft tangent-ish contact)
    body = safe_fillet(body, new_edges(body, b0, crest), 2.5, label="crest blend")
except CadOpError:
    pass

# ---- chin vents: blind pockets, ALL pocket edges filleted (3-edge corners)
for y in (-26, 0, 26):
    b0 = body
    tool = Pos(-150, y, 52) * Box(40, 10, 22)
    body = cut(body, tool, "chin vent")
    body = safe_fillet(body, new_edges(body, b0, tool), 1.6, label="chin vent rim")

# ---- shell (before panel lines: r3 shell cut failed after grooves were in the solid)
body = cut(body, cav, "shell")

# ---- panel lines on the outer skin (follow the compound curvature); cut into the SOLID one plate at a time
# (r2: one cut of the combined groove compound into the shell failed plain/fuzzy/manifold)
skin = cut(bare, skin_in, "skin layer")
plates = [Pos(0, 0, 95) * Box(400, 400, 1.4),                                           # brow / jaw ring
          Pos(-61.3, 0, 40) * Box(1.4, 400, 60),                                         # cheek split (vertical, below visor)
          Pos(20.3, 51.37, 240) * Box(300, 1.5, 120), Pos(20.3, -51.37, 240) * Box(300, 1.5, 120)]  # crown meridians
for k, pl in enumerate(plates):
    try:
        body = cut(body, common(skin, pl, f"groove tool {k}"), f"panel line {k}")
    except CadOpError:
        pass

# ---- visor glass: slice of the shell interior layer behind the opening
glass = common(cut(glass_o, glass_i, "glass layer"), Pos(-5, 0, 0) * visor_tool, "visor glass")

PARTS = {"helmet": (body, "#d9dbdd"), "visor": (glass, "#1d2a38")}
SPEC = {"L": 0.29, "W": 0.26, "H": 0.30}
