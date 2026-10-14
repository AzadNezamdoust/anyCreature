"""
build.py (<subject>) -- TEMPLATE. Copy to out/blender-hs/<subject>/build.py and replace every TODO with numbers
measured on the subject's registered turnaround (frame.json `s` px/m; scripts/v7/measure.mjs) and concept.

WF v11 (research/WORKFLOW-V11.md; a subject with subjects/<s>/spec.json): do NOT start from this template. Pass 1 is
GENERATED from the spec: `python scripts/hs/spec_blockout.py --subject <s>` writes out/blender-hs/<s>/build.py (one
named primitive per spec part = the frozen camera's proxy masses) with the v11 head
    SPEC = hs.load_spec(SUBJECT)
    C = hs.consts(SPEC, overrides=os.environ.get("HS_CONST_JSON"))
and every primary dimension is a C["KEY"] or SPEC.part("<id>").L / .H / .W / .D / .pos (a local number >= 0.02 m in a
part_* function carries `# local: <why>`; scripts/hs/spec_lint.py lists the rest). This template stays the v10 /
vehicle starting point.

CONTRACT (run_pass.py imports this file and calls build()):
  build() -> (root, parts)   root = the empty from hs.begin(); parts = list of mesh objects, each parented to root
                             (hs.finish does that), each with ob["part"] = a semantic role.
FRAME: every number in METRES in the AUTHOR frame of subjects/<s>/turnaround/views.json: near flank +x, y up,
nose +z, ground y = 0, x and z centred. hs.A(x, y, z) -> Blender (x, -z, y): Blender Z-up, nose -Y, near flank +X.
Never place geometry in Blender coordinates directly; always go through A() / the hs primitives.
Materials: names from PALETTE (sRGB hex). Build symmetric parts on +x and hs.mirror_x() them.

Run (from hard_surface):
  "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" -b --factory-startup --python-exit-code 1 ^
      --python scripts/hs/run_pass.py -- --subject <s> --pass N [--final]
"""
import math  # noqa: F401  (handy for angles)

import bmesh
from mathutils import Vector  # noqa: F401

import hs
from hs import A, box, bore, cylinder, finish, prism  # noqa: F401

SUBJECT = "TODO_subject"

PALETTE = {  # TODO: sample from the concept's lit faces / views.json families
    "body": "#737750",
    "chassis": "#3d4029",
    "tyre": "#2f302d",
    "hub": "#60643f",
    "metal": "#4a4c4d",
    "dark": "#1c1d1b",
}

# ---------------------------------------------------------------------------------------------------- dimensions (TODO)
BELLY_Y = 0.40
ROOF_Y = 1.70
HALF_W = 1.10
WHEEL_Z = (1.40, -1.40)          # axle z
WHEEL_Y, WHEEL_R = 0.50, 0.46    # axle height, tyre radius (carcass; tread adds tread_h)
WHEEL_X, TYRE_HW = 1.05, 0.18    # tyre centre plane x, tyre half width

# side profile (z, y), nose first, clockwise; front profile right half (x, y) bottom-centre up
SIDE_PROFILE = [(2.40, 1.10), (2.30, BELLY_Y), (-2.30, BELLY_Y), (-2.40, 1.20), (-2.30, ROOF_Y), (1.60, ROOF_Y)]
FRONT_HALF = [(0.85, 0.30), (HALF_W, 0.80), (HALF_W, 1.30), (HALF_W - 0.15, ROOF_Y + 0.05)]


# ---------------------------------------------------------------------------------------------------- parts
def part_hull():
    """Front-profile prism INTERSECT side-profile prism, minus wheel wells, then a 1-segment angle-limited chamfer."""
    hull = hs.profile_object("hull", hs.mirror_profile(FRONT_HALF), "z", -3.0, 3.0, ["body", "chassis"], "hull")
    bm = bmesh.new()
    prism(bm, SIDE_PROFILE, "x", -1.6, 1.6)
    side = hs.temp_object(bm, "cut_side")
    hs.boolean(hull, side, "INTERSECT")
    bm = bmesh.new()  # wheel wells: one polygon per axle, both flanks (keep cutters past the surface, never coplanar)
    for c in WHEEL_Z:
        well = [(c + 0.62, 0.10), (c + 0.55, 1.05), (c - 0.55, 1.05), (c - 0.62, 0.10)]
        prism(bm, well, "x", 0.80, 1.7)
        prism(bm, well, "x", -1.7, -0.80)
    wells = hs.temp_object(bm, "cut_wells")
    hs.boolean(hull, wells, "DIFFERENCE")
    hs.bevel_mod(hull, 0.025, angle_deg=25)
    hs.apply_modifiers(hull)
    for ob in (side, wells):
        hs.kill(ob)
    for p in hull.data.polygons:  # undersides -> chassis colour (Blender Z = author y)
        if p.normal.z < -0.85:
            p.material_index = 1
    return hull


def part_wheels():
    """Tyres with staggered block tread + recessed hubs with bolt studs, built on +x and mirrored."""
    bt, bh = bmesh.new(), bmesh.new()
    for c in WHEEL_Z:
        hs.wheel(bt, bh, (WHEEL_X, WHEEL_Y, c), WHEEL_R, TYRE_HW, tread_h=0.04, scale=WHEEL_R / 0.468)
    tyres = finish(bt, "tyres", ["tyre"], "wheel")
    hubs = finish(bh, "hubs", ["hub"], "hub")
    return hs.mirror_x(tyres), hs.mirror_x(hubs)


def part_details():
    """Examples: chamfered box, tube with a real bore (lip inset + zero-thickness inset with depth), offset 2 mm off
    the hull surface so no face is coplanar with it."""
    bm = bmesh.new()
    box(bm, (0.0, ROOF_Y + 0.002 + 0.06, -0.8), (0.9, 0.12, 0.7), chamfer=0.015)       # roof box (2 mm proud)
    _, f = cylinder(bm, (0.0, ROOF_Y + 0.25, 0.4), (0.0, ROOF_Y + 0.25, 1.6), 0.06, 8)  # barrel along +z
    bore(bm, f[-1], wall=0.02, depth=0.06, mat=1)
    return finish(bm, "details", ["metal", "dark"], "gun")


# ---------------------------------------------------------------------------------------------------- build
def build():
    root = hs.begin(SUBJECT, PALETTE, guards=True)
    parts = [part_hull(), *part_wheels(), part_details()]
    hs.end(parts)
    return root, parts
