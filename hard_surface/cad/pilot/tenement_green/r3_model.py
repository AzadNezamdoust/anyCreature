from cadkit import *
import math

W, D = 8.0, 9.0          # X width (door facade, -Y), Y depth
CH = 2.6                 # chamfer at (-X,-Y) corner
BASE_H = 1.2
FLOOR = 3.0
WALL_TOP = BASE_H + 3 * FLOOR   # 10.2
CORN_H, CORN_OUT = 0.5, 0.4
PARA_H = 0.5

def footprint(off=0.0, ch=CH):
    pts = [(ch - off * 0.414, -off), (W + off, -off), (W + off, D + off), (-off, D + off), (-off, ch - off * 0.414)]
    return Polygon(*pts, align=None)

def slab(z0, h, off=0.0):
    return extrude(Plane.XY.offset(z0) * footprint(off), h)

# ---------------- masses
base = slab(0, BASE_H, 0.06)
walls = slab(BASE_H, WALL_TOP - BASE_H)
cornice = fuse(slab(WALL_TOP, CORN_H, CORN_OUT), slab(WALL_TOP - 0.25, 0.25, 0.15), label="cornice")
parapet = slab(WALL_TOP + CORN_H, PARA_H, 0.05)
roof_well = slab(WALL_TOP + CORN_H + 0.15, PARA_H, -0.3)
parapet = cut(parapet, roof_well, label="roof_well")
bands = [slab(BASE_H + i * FLOOR - 0.08, 0.22, 0.08) for i in (1, 2)]
roof = slab(WALL_TOP + CORN_H, 0.15, -0.3)

# ---------------- window placements: (x, y, rot_deg) on facade plane; module faces -Y at origin
facade = []
for x in (3.0, 4.8):                      # -Y facade (door at x=6.7)
    facade.append((x, 0.0, 0))
facade_door_col = (6.7, 0.0, 0)
for y in (3.4, 5.4, 7.4):                 # -X facade
    facade.append((0.0, y, -90))
cm = CH / 2
facade.append((cm, cm, -45))              # chamfer face

WW, WH = 0.95, 1.85
def window_locs(include_ground=True):
    locs = []
    for i in range(3):
        z = BASE_H + i * FLOOR + 0.6
        cols = facade + ([facade_door_col] if i > 0 else [])
        for (x, y, r) in cols:
            locs.append(Location((x, y, z), (0, 0, r)))
    return locs

LOCS = window_locs()

# window module (built once, placed by Location)
recess = Box(WW, 0.5, WH, align=(Align.CENTER, Align.CENTER, Align.MIN))
frame = cut(Box(WW + 0.16, 0.12, WH + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN)),
    Box(WW - 0.08, 0.3, WH - 0.12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, 0.06))), label="window_frame")
mullion = Box(0.06, 0.06, WH, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0.08, 0)))
transom = Box(WW, 0.06, 0.06).moved(Location((0, 0.08, WH * 0.55)))
sill = Box(WW + 0.35, 0.22, 0.1).moved(Location((0, -0.06, -0.05)))
lintel = Box(WW + 0.3, 0.16, 0.22).moved(Location((0, -0.03, WH + 0.16)))
trim_mod = Compound([frame.moved(Location((0, -0.0, 0))), sill, lintel, mullion, transom])
glass_mod = Box(WW, 0.04, WH, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0.12, 0)))

walls = cut(walls, Compound([recess.moved(l) for l in LOCS]), label="window_recesses")

# door on -Y facade, ground floor
DX, DW, DH = 6.7, 1.0, 2.2
door_z = BASE_H + 0.1
walls = cut(walls, Box(DW, 0.5, DH, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((DX, 0, door_z))),
            label="door_recess")
door = Box(DW, 0.06, DH, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((DX, 0.17, door_z)))
door_frame = Box(DW + 0.3, 0.14, DH + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((DX, 0, door_z)))
door_frame = cut(door_frame, Box(DW, 0.5, DH, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((DX, 0, door_z))),
                 label="door_frame")
door_frame = safe_chamfer(door_frame, door_frame.edges().filter_by(Axis.Y), 0.03, label="door_frame")

# basement windows in base course
base_locs = [Location((x, -0.06, 0.3), (0, 0, 0)) for x in (3.0, 4.8)] + \
            [Location((-0.06, y, 0.3), (0, 0, -90)) for y in (3.4, 5.4, 7.4)]
bw = Box(0.7, 0.3, 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
base = cut(base, Compound([bw.moved(l) for l in base_locs]), label="basement_windows")
bglass = [Box(0.7, 0.03, 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0.1, 0))).moved(l) for l in base_locs]

# stoop: steps + newel posts with balls, in front of door
steps = []
n = 4
for i in range(n):
    depth = 0.35 * (n - i)
    steps.append(Box(1.6, depth, BASE_H / n * (i + 1) + 0.1,
                     align=(Align.CENTER, Align.MAX, Align.MIN)).moved(Location((DX, 0, 0))))
stoop = steps[0]
stoop = fuse(stoop, Compound(steps[1:]), label="stoop")
stoop = safe_chamfer(stoop, stoop.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], 0.03, label="stoop_nose")
posts = []
for sx in (-1, 1):
    p = Box(0.35, 0.35, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((DX + sx * 0.95, -1.25, 0)))
    p = safe_chamfer(p, p.edges().group_by(Axis.Z)[-1], 0.05, label="post_cap")
    ball = Sphere(0.2).moved(Location((DX + sx * 0.95, -1.25, 1.68)))
    posts += [p, ball]

# rooftop vent housing (sloped front) + louvres + chimney pipe
RZ = WALL_TOP + CORN_H + 0.15
vent = extrude(Plane.YZ.offset(1.5) * Polygon((2.5, 0), (5.0, 0), (5.0, 1.6), (3.6, 1.6), align=None), 2.0)
vent = vent.moved(Location((0, 0, RZ)))
vent = safe_chamfer(vent, vent.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], 0.05, label="vent_top")
louvres = [Box(0.06, 0.9, 0.06).moved(Location((1.47, 4.3, RZ + 0.35 + i * 0.16))) for i in range(6)]
louvre_box = Box(0.04, 1.1, 1.1, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((1.48, 4.3, RZ + 0.25)))
chimney = Cylinder(0.14, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN), resolution=None).moved(Location((1.0, 1.8, RZ))) \
    if False else Cylinder(0.14, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((1.2, 2.2, RZ)))
cap = Cylinder(0.2, 0.12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((1.2, 2.2, RZ + 1.2)))

trims = [trim_mod.moved(l) for l in LOCS] + [door_frame] + bands + [cornice, parapet] + louvres
PARTS = {
    "walls": (walls, "#9fd3b4"),
    "base": (base, "#a8838f"),
    "trim": (Compound(trims), "#e8e2c8"),
    "glass": (Compound([glass_mod.moved(l) for l in LOCS] + bglass), "#9fc3d4"),
    "door": (door, "#7a4a2a"),
    "roof": (roof, "#8c9a90"),
    "vent": (Compound([vent, louvre_box]), "#9fd3b4"),
    "chimney": (Compound([chimney, cap]), "#8c9a90"),
    "stoop": (Compound([stoop] + posts), "#b9b39a"),
}
SPEC = {"L": 8.4, "W": 10.6, "H": 12.4}
TRI_BUDGET = 10000
