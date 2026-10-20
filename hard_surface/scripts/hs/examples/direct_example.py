"""
direct_example.py -- a minimal WF v10 DIRECT build (no gold model): a small pneumatic hand tool, 7 parts, ~640 tris.
Run it on any registered subject as the frame (here it_pneumatic_pick), into a scratch dir:
  blender -b --factory-startup --python-exit-code 1 --python scripts/hs/run_pass.py -- --subject it_pneumatic_pick `
      --pass 1 --build scripts/hs/examples/direct_example.py --out-dir out/score/example
It shows: registered dims + frame.json, hs.begin(guards=True), a palette sampled from the concept, part roles in
ob["part"], a box with chamfer, a round barrel with a real bore, a ribbed grip (ring_stack), a pyramid point, a hose
(tube_path), and a trigger that is its own object with clearance in its slot (riggable: pivot at PIVOT).
Frame: author metres, near flank +x, y up, nose / pick point +z, y = 0 at the butt; hs.A maps it to Blender.
"""
import json
import os

import bmesh

import hs
from hs import box, cylinder, finish

SUBJECT = "it_pneumatic_pick"

# 1. SIZE. Registered dims = what the four turnaround views agree on (hull sees hoses / straps too):
#      node scripts/v7/hull.mjs --subject it_pneumatic_pick --no-concept   ->  "dims W 0.139 H 0.570 L 0.550 m"
#    They win over facts.json (estimate: H 0.52). Never pre-scale: SIGMA in the run_pass output should print ~1.00.
W, H, L = 0.139, 0.570, 0.550

# frame.json = the registration of the drawings: s px/m, per view ox/oy; author point p -> px = ox + s (p.right),
# py = oy - s (p.up). Side view: right = -z, up = y.  Use it to turn a pixel you read into metres.
FRAME = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "out", "blender-hs",
                                    SUBJECT, "frame.json")))
SIDE = FRAME["views"]["side"]


def side_px(px, py):
    """side-view pixel -> author (z, y) in metres."""
    return (SIDE["ox"] - px) / FRAME["s"], (SIDE["oy"] - py) / FRAME["s"]


# the pixel -> metre route in use: the hose crest is the highest foreground row of the side view (a column run of
#   node scripts/v7/measure.mjs profile --subject it_pneumatic_pick --view side --axis col --from -0.02 --to 0.02 --step 0.01
# says up 0.001..0.569 at right 0.000, i.e. py ~ 133); converted with frame.json it must agree with the registered H.
HOSE_TOP_Y = side_px(0, 133)[1]                    # 0.567 m
assert abs(HOSE_TOP_Y - H) < 0.01                  # the registered H includes the hose, so the hose crest sets it

# 2. PALETTE, sampled from the concept (median of a rect: x,y,w,h in px of refs/<s>.png):
#      node scripts/v7/measure.mjs sample --subject it_pneumatic_pick --view concept 560,230,12,12 250,270,12,12 560,780,12,12
#    and sizes read off the drawings:  node scripts/v7/measure.mjs profile --subject it_pneumatic_pick --view side --axis row --step 0.04
PALETTE = {"shell": "#4a5763", "steel": "#423f3c", "haft": "#2c2b2b", "rubber": "#41403f"}

HY = 0.457                          # housing axis height
PIVOT = (0.0, 0.40, 0.07)           # trigger hinge pin (rig.json: joint "trigger" pivot)


def part_housing():                 # chamfered box body with a slot for the trigger (a real cut, 1.5 mm clearance)
    bm = bmesh.new()
    box(bm, (0.0, HY, 0.0), (0.11, 0.13, 0.18), chamfer=0.01)           # centred on z = 0: x +-0.055, y 0.392..0.522
    ob = finish(bm, "housing", ["shell"], "housing")
    slot = bmesh.new()
    box(slot, (0.0, 0.395, 0.072), (0.015, 0.03, 0.04))                  # trigger is 12 mm wide: 1.5 mm each side
    hs.cut(ob, slot, "DIFFERENCE", name="trigger_slot")
    return ob


def part_barrel():                  # round barrel with a REAL bore (inset lip, then straight walls), n=12 facets
    bm = bmesh.new()
    _, faces = cylinder(bm, (0.0, HY, 0.09), (0.0, HY, 0.18), 0.04, 12)
    hs.bore(bm, faces[-1], wall=0.008, depth=0.05)                       # faces[-1] = the c1 end cap
    return finish(bm, "barrel", ["steel"], "barrel")


def part_point():                   # pick tip: pyramid on the barrel, base in the xy plane (axis "z"), tip along +z
    bm = bmesh.new()
    hs.pyramid(bm, (0.0, HY, 0.18), 0.03, 0.036, (0.0, HY, 0.31), axis="z")
    return finish(bm, "point", ["steel"], "pick")


def part_haft():                    # grip tube; the ribbed sleeve is its own part so the rubber has its own material
    bm = bmesh.new()
    cylinder(bm, (0.0, 0.0, 0.0165), (0.0, 0.395, 0.0165), 0.027, 12)
    return finish(bm, "haft", ["haft"], "haft")


def part_grip():                    # ribs = alternating radii: 6 ribs, y 0.02..0.18, bigger than the haft so no coplanar faces
    bm = bmesh.new()
    hs.ring_stack(bm, (0.0, 0.02, 0.0165), (0.0, 0.18, 0.0165), [0.030, 0.034] * 6 + [0.030], 12)
    return finish(bm, "grip", ["rubber"], "grip")


def part_hose():                    # swept tube along a polyline (z, y) on x = 0, end caps closed
    path = [(0.0, y, z) for z, y in ((0.027, 0.50), (0.012, 0.560), (-0.010, 0.566), (-0.040, 0.548), (-0.052, 0.505),
                                     (-0.050, 0.46), (-0.042, 0.415))]
    bm = bmesh.new()
    hs.tube_path(bm, path, 0.0125, n=8)
    return finish(bm, "hose", ["rubber"], "hose")


def part_trigger():                 # SEPARATE object: its top sits in the housing slot with clearance, pivot at PIVOT
    bm = bmesh.new()
    poly = [(0.066, 0.40), (0.080, 0.40), (0.104, 0.345), (0.094, 0.335), (0.080, 0.360), (0.066, 0.385)]    # (z, y)
    hs.prism(bm, poly, "x", -0.006, 0.006)                               # 12 mm wide; 1.5 mm free each side of the slot
    return finish(bm, "trigger", ["steel"], "trigger")


def build():
    root = hs.begin("example", PALETTE, guards=True)          # guards ON for every new build (see hs.py docstring)
    parts = [part_housing(), part_barrel(), part_point(), part_haft(), part_grip(), part_hose(), part_trigger()]
    hs.end(parts)                                             # weld + dissolve degenerates + flat shading
    for w in hs.GUARD_WARN:                                   # clamps / out-of-range calls the guards made
        print("GUARD", w)
    return root, parts
