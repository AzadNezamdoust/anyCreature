"""
build.py (assault_rifle) -- WF v10 DIRECT look build (no gold model). Passes 1-2 = the harness proof (block-out,
masses: pass1_build.py / pass2_build.py); passes 3-8 = the look build (scripts/hs/method.md,
out/blender-hs/BUILD-DIRECT.md, feature inventory in FEATURES.md); passes 9+ = the polish round after the Fable
review (review_fable.md, item by item in POLISH.md; numbers re-measured on side.png with scripts/v7/measure.mjs).

FRAME (classes/weapon.md): metres, muzzle +z, the weapon's left flank +x, y up, y = 0 at the lowest point (the
magazine floor plate's rear corner), x centred on the bore plane, z centred on the overall length.

SOURCES. Every (X, Y) pair below is a pixel of subjects/assault_rifle/turnaround/side.png, turned into metres by
the registration out/blender-hs/assault_rifle/frame.json (s 887.22 px/m, side ox 511.5 oy 653):
    z = Z(X) = (511.5 - X) / s        y = Y(Yp) = (653 - Yp) / s
Widths (x) come from front.png / rear.png / top.png and the concept refs/assault_rifle.png; the three disagree
(handguard 0.072 top / 0.083 front, butt plate 0.069 rear / 0.098 top) and are settled by sense in FEATURES.md.
Colours are sampled from refs/assault_rifle.png and side.png (flank values).
Registered dims: L 0.900 (anchor), H 0.317, W 0.100 with the knob.

INK. run_pass inks creases sharper than 46 deg. Edge-break chamfers (45 deg) therefore erase a line: features the
source draws with a line (charging slot, receiver seam, rail gaps, magazine grooves, pad, rear foot of the front
sight) are cut / added AFTER the chamfer so they stay sharp; shallow facet lines (lower panel line, stock ridge)
are marked (mark_line -> edge.use_freestyle_mark).

RIGGABLE (scripts/hs/rig.md "Handheld weapons"): own objects trigger, magazine, charging_handle, bolt, selector.
  magazine  straight box leaning 18.8 deg forward inside the well, its rear face flaring below the well mouth
            (side.png: front edge 18.4 deg, rear 12.2 deg); the well is a pocket on the SAME axis (2.2 mm
            clearance): it slides out along MAG_AXIS = (x 0, y -0.9468, z +0.3217) from MAG_O; out after ~0.055 m.
  bolt      a cylinder in a closed channel inside the upper receiver, seen through the ejection port (right
            flank); travels -z 0.06 with the charging handle, whose stem rides in a blind groove (left flank).
  trigger   hangs in its own pocket in the lower receiver, pin (x axis) at y 0.176, z -0.120.
  selector  hub on the left flank, axis x through (y 0.193, z -0.1685), 2 mm off the flank.
  barrel + muzzle brake: bodies of revolution on the bore line x 0, y BORE_Y; the brake has a real bore.
"""
import math

import bmesh

import hs
from hs import A, box, bore, cylinder, finish, loft, prism

SUBJECT = "assault_rifle"

PALETTE = {
    "gunmetal": "#4e4e4e",   # receiver, collars                  (concept #565656 lit / #464647 shade; side.png 76-80)
    "sight": "#4e4e4e",      # rail, front / rear sight           (side.png 71-78 = the receiver family; was #434343)
    "steel": "#4e4e4e",      # barrel, muzzle brake               (side.png 69-77; was #5c5c5c, read silvery)
    "bolt": "#484848",       # bolt in the charging slot: the slot interior reads = the flank (side.png 75-78)
    "shadow": "#3a3a3a",     # the receiver's front lug strip X 501..511 (side.png #393939)
    "polymer": "#313131",    # handguard, stock, grip, magazine, trigger guard (concept #2d2d2d .. #3a3a3a)
    "pad": "#404040",        # butt plate                         (side.png 54-65, lighter than the bar)
    "trigger": "#2c2c2c",    # trigger blade                      (side.png 29-52)
    "lever": "#6c6c6c",      # selector, pins, windage knob       (concept #737474)
    "dark": "#141414",       # bore, vents, pockets, grooves      (concept #131413)
    "accent": "#f8690b",     # floor plate, charging knob, handguard band (concept #f8690b / #ea5900)
}

S_PX = 887.2222222222222
BORE_Y = 0.2265
MUZZLE_Z, BUTT_Z = 0.450, -0.449


def Z(X):
    return (511.5 - X) / S_PX


def Y(Yp):
    return (653.0 - Yp) / S_PX


def PX(pts):
    """side.png pixels -> (z, y) profile for prism(axis 'x')."""
    return [(Z(x), Y(y)) for x, y in pts]


# ---------------------------------------------------------------------------------------------------- helpers
def chamfer(bm, w, min_deg=30.0):
    """1-segment bevel on every edge sharper than min_deg (call before other islands are added)."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(min_deg)]
    bmesh.ops.bevel(bm, geom=es, offset=w, offset_type="OFFSET", segments=1, profile=0.5, affect="EDGES",
                    clamp_overlap=True)
    return bm


def ob_chamfer(ob, w, min_deg=40.0):
    """Edge-break chamfer on a finished (booleaned) object: every edge sharper than min_deg."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    chamfer(bm, w, min_deg)
    for _ in range(2):                                    # bevels across boolean seams leave sub-0.01 mm2 slivers
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-4)
        bmesh.ops.dissolve_degenerate(bm, dist=2e-4, edges=bm.edges[:])
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def tidy(ob, d=2e-4):
    """Weld the sub-0.2 mm slivers a boolean made after the chamfer (zero-area faces)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for _ in range(2):
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=d)
        bmesh.ops.dissolve_degenerate(bm, dist=d, edges=bm.edges[:])
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def pprism(pts_px, hw, bevel=0.0, mat=0):
    """Side-profile (pixels) prism, x from -hw to +hw, optional chamfer -> new bmesh."""
    bm = bmesh.new()
    prism(bm, PX(pts_px), "x", -hw, hw, mat=mat)
    if bevel > 0:
        chamfer(bm, bevel)
    return bm


def zloft(bm, secs, mat=0):
    """secs = [(z, [(x, y), ...]), ...] -> loft along z."""
    return loft(bm, [[A(x, y, z) for x, y in pts] for z, pts in secs], mat=mat)


def octa(cy, hw, hh, fw, fh):
    """Octagon (x, y): half width hw, half height hh, top / bottom flat half width fw, side flat half height fh."""
    return [(fw, cy - hh), (hw, cy - fh), (hw, cy + fh), (fw, cy + hh), (-fw, cy + hh), (-hw, cy + fh),
            (-hw, cy - fh), (-fw, cy - hh)]


def scl(pts, k, cy):
    return [(x * k, cy + (y - cy) * k) for x, y in pts]


def stadium(cu, cv, hl, r, n=3):
    """Rounded slot outline (u, v): half length hl along u, half height r."""
    out = []
    for sgn, a0 in ((1, -90.0), (-1, 90.0)):
        for i in range(n + 1):
            a = math.radians(a0 + 180.0 * i / n)
            out.append((cu + sgn * (hl - r) + r * math.cos(a), cv + r * math.sin(a)))
    return out


def union(ob, bm):
    return hs.cut(ob, bm, "UNION", "u")


def diff(ob, bm):
    return hs.cut(ob, bm, "DIFFERENCE", "d")


def add_islands(ob, bm):
    """Append a bmesh's closed islands to an object's mesh (no boolean)."""
    full = bmesh.new()
    full.from_mesh(ob.data)
    tmp = hs.temp_object(bm, "islands")
    full.from_mesh(tmp.data)
    hs.kill(tmp)
    full.to_mesh(ob.data)
    full.free()
    return ob


def in_oct(x, dy, o, k):
    """Inside the octagon octa(...) scaled by k about its centre (dy = y - centre)."""
    hw, hh, fw, fh = o
    ax, ay = abs(x) / k, abs(dy) / k
    return ax < hw and ay < hh and (ax - fw) / (hw - fw) + (ay - fh) / (hh - fh) < 1.0


def paint(ob, pred, mat):
    """Material by face centre (author x, y, z)."""
    for p in ob.data.polygons:
        c = p.center
        if pred(c.x, c.z, -c.y):
            p.material_index = mat


def xcyl(bm, x0, x1, y, z, r, n=10, mat=0):
    return cylinder(bm, (x0, y, z), (x1, y, z), r, n, mat=mat)


def pin(bm, sx, x_in, x_out, y, z, r, n=12, mat=0, dimple=None, dimple_r=0.0018):
    """A cross pin / knob on flank sx with a real dark centre dimple (1 mm deep) in its outer face."""
    _, f = xcyl(bm, sx * x_in, sx * x_out, y, z, r, n, mat=mat)
    if dimple is not None:
        bore(bm, f[-1], wall=r * math.cos(math.pi / n) - dimple_r, depth=0.0010, mat=dimple)


def rings_z(bm, cy, zr, n=16, mat=0):
    """Body of revolution about the bore line: zr = [(z, r), ...]."""
    return loft(bm, [hs.circle((0, cy, z), (1, 0, 0), (0, 1, 0), r, n, math.pi / n) for z, r in zr], mat=mat)


MARKS = []            # (object, side.png polyline, tolerance m, min |x|): applied in build() after hs.end


def _mark_edge(me, e):
    try:
        e.use_freestyle_mark = True
    except AttributeError:
        at = me.attributes.get("freestyle_edge") or me.attributes.new("freestyle_edge", "BOOLEAN", "EDGE")
        at.data[e.index].value = True


def mark_line(ob, pts_px, tol, xmin):
    """Ink a shallow facet line (a crease under 46 deg gets no Freestyle line): mark the mesh edges that lie on the
    side.png polyline pts_px, on either flank, with |x| >= xmin."""
    seg = PX(pts_px)

    def dist(z, y):
        best = 1e9
        for (z0, y0), (z1, y1) in zip(seg, seg[1:]):
            dz, dy = z1 - z0, y1 - y0
            t = max(0.0, min(1.0, ((z - z0) * dz + (y - y0) * dy) / (dz * dz + dy * dy)))
            best = min(best, math.hypot(z - z0 - t * dz, y - y0 - t * dy))
        return best

    me, n = ob.data, 0
    for e in me.edges:
        a, b = me.vertices[e.vertices[0]].co, me.vertices[e.vertices[1]].co
        if a.x * b.x <= 0 or min(abs(a.x), abs(b.x)) < xmin or abs(a.x - b.x) > 0.0006:
            continue
        if (a - b).length > 0.0015 and dist(-a.y, a.z) < tol and dist(-b.y, b.z) < tol:
            _mark_edge(me, e)
            n += 1
    print("MARK", ob.name, n)
    return n


# ---------------------------------------------------------------------------------------------------- barrel group
def part_barrel():
    """Barrel Y 442.5..464 (dia 0.024), from inside the receiver collar to inside the brake."""
    bm = bmesh.new()
    rings_z(bm, BORE_Y, [(0.020, 0.0120), (0.386, 0.0120)], 24)
    return finish(bm, "barrel", ["steel"], "barrel")


def part_muzzle_brake():
    """Brake X 112.5..172.5, Y 435..472 (side.png col 136: 37 px with ink -> dia 0.040): rear collar X 161..172.5
    behind a groove, chamfered ends, two slots per flank (X 122..150 = 33 mm, Y 443..449 / 458..463) and two on
    top (top.png) as dark blind pockets whose floors (13.5 mm off the axis) stay outside the bore (r 9.5 mm), so
    they read black, not grey; a real bore (dia 0.019, 58 mm deep)."""
    bm = bmesh.new()
    _, f = rings_z(bm, BORE_Y, [(0.3815, 0.0168), (0.3840, 0.0195), (0.3930, 0.0195), (0.3942, 0.0175),
                                (0.3962, 0.0175), (0.3975, 0.0200), (0.4465, 0.0200), (MUZZLE_Z, 0.0168)], 24)
    bore(bm, f[-1], wall=0.0073, depth=0.058, mat=1)
    ob = finish(bm, "muzzle_brake", ["steel", "dark"], "muzzle_device")
    cb = bmesh.new()
    for dy in (0.0088, -0.0088):                           # r 4.8 mm: the grey ink at the rim eats ~1 px
        for x0, x1 in ((0.0140, 0.03), (-0.03, -0.0140)):
            prism(cb, stadium(0.4225, BORE_Y + dy, 0.0165, 0.0048, 4), "x", x0, x1, mat=1)
    diff(ob, cb)
    cb = bmesh.new()
    for dx in (0.0088, -0.0088):
        prism(cb, [(dx + v - BORE_Y, u) for u, v in stadium(0.4225, BORE_Y, 0.0165, 0.0048, 4)], "y",
              BORE_Y + 0.0140, BORE_Y + 0.03, mat=1)
    diff(ob, cb)
    paint(ob, lambda x, y, z: math.hypot(x, y - BORE_Y) < 0.0192 and 0.402 < z < 0.443, 1)
    return ob


def part_front_sight():
    """A-frame tower: post X 219.5..231 up to Y 382.5, diagonal down to the rear foot X 259..268.7 (its own block,
    inked at X 259), a bar at Y 426..434.5 with a slit over the barrel, triangular window = side.png white
    (232,396.5) (232,424.5) (256.6,424.5); two barrel clamps (dia 0.039). Width: front.png / top.png draw a wide
    tower (0.051 at the base, 0.027 at the top), the concept a slim plate (~0.02): built 0.034 at the bar tapering
    to 0.018 at the top. Two ears + a post."""
    bm = pprism([(219.5, 441), (219.5, 386), (223, 382.5), (234, 382.5), (268.7, 421), (268.7, 441), (258, 441),
                 (258, 434.5), (231, 434.5), (231, 441)], 0.017, bevel=0.0018)
    ob = finish(bm, "front_sight", ["sight"], "sight")
    cb = bmesh.new()
    prism(cb, PX([(231, 395.5), (231, 426), (258, 426)]), "x", -0.03, 0.03)
    diff(ob, cb)
    yb, yt = Y(435), Y(382.5)
    for v in ob.data.vertices:                              # taper in x above the bar
        t = min(1.0, max(0.0, (v.co.z - yb) / (yt - yb)))
        v.co.x *= 1.0 - 0.47 * t
    cb = bmesh.new()
    box(cb, (0, Y(382.5), Z(228)), (0.0090, 0.020, 0.030))          # the ear notch, 10 mm deep
    diff(ob, cb)
    ub = bmesh.new()
    rings_z(ub, BORE_Y, [(Z(230.5), 0.0180), (Z(229), 0.0195), (Z(221), 0.0195), (Z(219.5), 0.0180)], 20)
    union(ob, ub)
    ub = bmesh.new()
    rings_z(ub, BORE_Y, [(0.2715, 0.0195), (Z(259.5), 0.0195), (Z(258), 0.0180)], 20)
    union(ob, ub)
    ub = bmesh.new()
    box(ub, (0, Y(382.5) - 0.0065, Z(228)), (0.0026, 0.015, 0.0026))  # the post, tip at y 0.3035
    union(ob, ub)
    union(ob, pprism([(259.5, 436), (259.5, 414), (268.7, 424.2), (268.7, 436)], 0.0195))   # rear foot, sharp
    return tidy(ob)


# ---------------------------------------------------------------------------------------------------- handguard
HG_CY = BORE_Y
HG_O = (0.039, 0.043, 0.019, 0.0233)                    # width: top.png 0.072, front.png 0.083 -> 0.078
HG_OCT = octa(HG_CY, *HG_O)                             # side facets Y 432.5 / 473.75, top flat 34 px (top.png)
HG_Z0, HG_Z1 = Z(477.5), Z(290)                          # 0.0383 .. 0.2497
VENTS = [(314, 352.5), (362.5, 400.5), (412.5, 449.5)]   # side.png row 451: 315-351, 364-399, 414-448; col 332: 444-458


def part_handguard():
    """Octagonal handguard, chamfered rear end, three oval vents per flank (42 x 17 mm) as 9 mm deep dark pockets
    (the source draws them black), tapered front cap X 268.7..277.5 in front of the band."""
    bm = bmesh.new()
    zloft(bm, [(HG_Z0, scl(HG_OCT, 0.93, HG_CY)), (HG_Z0 + 0.004, HG_OCT), (HG_Z1, HG_OCT)])
    ob = finish(bm, "handguard", ["polymer", "dark"], "handguard")
    cb = bmesh.new()
    for x0, x1 in VENTS:
        for a, b in ((0.030, 0.06), (-0.06, -0.030)):
            prism(cb, stadium((Z(x0) + Z(x1)) / 2, Y(451.2), (Z(x0) - Z(x1)) / 2, 0.0085, 6), "x", a, b, mat=1)
    diff(ob, cb)
    ob_chamfer(ob, 0.0010, 50.0)
    cap = bmesh.new()
    zloft(cap, [(0.2580, scl(HG_OCT, 0.88, HG_CY)), (0.2645, scl(HG_OCT, 0.88, HG_CY)),
                (0.2735, scl(HG_OCT, 0.66, HG_CY))])
    add_islands(ob, cap)
    paint(ob, lambda x, y, z: 0.06 < z < 0.23 and abs(y - Y(451.2)) < 0.0088 and 0.0295 < abs(x) < 0.0388, 1)
    return ob


def part_band():
    """Orange band X 277.5..290, Y 417..487.5: a touch smaller than the handguard (front.png shows it inside)."""
    bm = bmesh.new()
    o = scl(HG_OCT, 0.955, HG_CY)
    zloft(bm, [(HG_Z1 - 0.003, o), (Z(277.5), o)])
    return finish(bm, "handguard_band", ["accent"], "handguard")


# ---------------------------------------------------------------------------------------------------- rail
RAIL_TEETH = 22                                            # side.png row 411: 22 teeth, first at 309, last at 652


def part_rail():
    """Rail slab + 22 square-cut teeth (11.5 px long, pitch 16.33 px; un-chamfered so the gaps ink)."""
    bm = bmesh.new()
    zloft(bm, [(Z(699), [(-0.017, 0.262), (0.017, 0.262), (0.017, 0.268), (0.0145, 0.2715), (-0.0145, 0.2715),
                         (-0.017, 0.268)]),
               (Z(307), [(-0.017, 0.262), (0.017, 0.262), (0.017, 0.268), (0.0145, 0.2715), (-0.0145, 0.2715),
                         (-0.017, 0.268)])])
    tooth = [(-0.0158, 0.2705), (0.0158, 0.2705), (0.0158, 0.2765), (-0.0158, 0.2765)]
    for k in range(RAIL_TEETH):
        x0 = 309 + (652 - 309) / (RAIL_TEETH - 1) * k
        zloft(bm, [(Z(x0 + 11.5), tooth), (Z(x0), tooth)])
    ob = finish(bm, "rail", ["sight", "dark"], "rail")
    paint(ob, lambda x, y, z: abs(y - 0.2715) < 0.0002 and abs(x) < 0.0146, 1)     # gap floors: dark from the top
    return ob


# ---------------------------------------------------------------------------------------------------- receiver
UP_Y0, UP_Y1 = 0.2125, 0.267
UP_HW = 0.033                                              # top.png 0.070, rear.png ~0.080 -> 0.066
LO_HW = 0.0295                                             # 3.5 mm step under the upper (seam)
SEAM_Y = 0.2172                                            # side.png col 620: seam line Y 459..460
UP_SEC = [(0.030, UP_Y0), (UP_HW, 0.2155), (UP_HW, 0.254), (0.021, UP_Y1), (-0.021, UP_Y1), (-UP_HW, 0.254),
          (-UP_HW, 0.2155), (-0.030, UP_Y0)]
UP_Z0, UP_Z1 = Z(700), 0.004
CH_Y0, CH_Y1, CH_HW = 0.2175, 0.2445, 0.0135               # bolt channel (closed box inside the upper)
BOLT_Y = 0.231
SLOT_Y, SLOT_R = 0.2355, 0.0075                            # charging slot X 517..608 (Y 437..450)
LUG = [(0.0265, 0.187), (0.0305, 0.191), (0.0305, 0.2435), (0.015, 0.264), (-0.015, 0.264), (-0.0305, 0.2435),
       (-0.0305, 0.191), (-0.0265, 0.187)]                 # front lug strip X 501..512, Y 425..487 (side.png)
NECK = [(0.0212, 0.190), (0.0244, 0.1935), (0.0244, 0.2435), (0.012, 0.263), (-0.012, 0.263), (-0.0244, 0.2435),
        (-0.0244, 0.1935), (-0.0212, 0.190)]               # dark neck between the barrel collar and the lug


def part_upper():
    """Upper receiver X 501..700, Y 417..464: chamfered section, front barrel collar (octagon X 474..500,
    Y 417..488) behind a dark 2.5 mm neck, the dark front lug strip X 501..512 with the pivot pin (505.5,479) as
    a ring with a centre dimple, rear buffer collar X 700..723 (Y 418..470, 0.048 wide: top.png); bolt channel;
    cut sharp after the chamfer so they ink: charging groove (left, blind, with a dark counter-bore rim), ejection port (right), the receiver seam (the
    flank under y 0.2172 = Y 460 is stepped back 4.5 mm, both flanks); open dust cover + deflector (right)."""
    bm = bmesh.new()
    cyu = (UP_Y0 + UP_Y1) / 2
    zloft(bm, [(UP_Z0, scl(UP_SEC, 0.94, cyu)), (UP_Z0 + 0.004, UP_SEC), (UP_Z1 - 0.004, UP_SEC),
               (UP_Z1, scl(UP_SEC, 0.94, cyu))])
    ob = finish(bm, "upper", ["gunmetal", "dark", "lever", "shadow"], "receiver")
    ring = octa(BORE_Y, 0.0375, 0.040, 0.0175, 0.0215)
    ub = bmesh.new()
    zloft(ub, [(0.0135, scl(ring, 0.92, BORE_Y)), (0.0165, ring), (0.038, ring), (0.042, scl(ring, 0.92, BORE_Y))])
    union(ob, ub)
    ub = bmesh.new()
    zloft(ub, [(-0.001, LUG), (0.0110, LUG)])
    union(ob, ub)
    col = octa(0.2355, 0.024, 0.0295, 0.012, 0.016)
    ub = bmesh.new()
    zloft(ub, [(Z(723.5), scl(col, 0.90, 0.2355)), (Z(720), col), (Z(703), col), (Z(698), scl(col, 0.90, 0.2355))])
    union(ob, ub)
    ob_chamfer(ob, 0.0010, 42.0)
    cb = bmesh.new()                                                              # bolt channel
    box(cb, (0, (CH_Y0 + CH_Y1) / 2, -0.1025), (2 * CH_HW, CH_Y1 - CH_Y0, 0.205), mat=0)
    diff(ob, cb)
    cb = bmesh.new()                                                              # charging slot, left flank
    # FUNCTION (rig): a BLIND groove (floor 3 mm outside the bolt channel): with the bolt back, an open slot showed
    # daylight through the ejection port on the other flank. Its floor reads = the flank, as side.png draws it.
    prism(cb, stadium((Z(517) + Z(608)) / 2, SLOT_Y, (Z(517) - Z(608)) / 2, SLOT_R), "x", 0.0165, 0.05, mat=0)
    diff(ob, cb)
    cb = bmesh.new()                                                              # ejection port, right flank
    box(cb, (-0.030, 0.2315, -0.054), (0.040, 0.020, 0.060), mat=1)
    diff(ob, cb)
    cb = bmesh.new()                                                              # receiver seam, both flanks
    for sx in (1, -1):
        box(cb, (sx * 0.0395, (0.2090 + SEAM_Y) / 2, -0.1055), (0.022, SEAM_Y - 0.2090, 0.207), mat=0)
    diff(ob, cb)
    cb = bmesh.new()                                                              # slot counter-bore (dark rim)
    prism(cb, stadium((Z(517) + Z(608)) / 2, SLOT_Y, (Z(517) - Z(608)) / 2 + 0.0012, SLOT_R + 0.0012), "x",
          UP_HW - 0.0012, 0.05, mat=1)
    diff(ob, cb)
    tidy(ob)
    paint(ob, lambda x, y, z: abs(x) < UP_HW - 0.0015 and CH_Y0 - 0.001 < y < CH_Y1 + 0.0005 and -0.206 < z < 0.001,
          0)
    paint(ob, lambda x, y, z: -UP_HW + 0.0015 < x < -0.0125 and CH_Y0 < y < CH_Y1 and -0.09 < z < -0.02, 1)
    paint(ob, lambda x, y, z: 0.0283 < abs(x) < 0.0331 and y < SEAM_Y + 0.0001 and -0.2095 < z < -0.0015,
          1)                               # seam recess: a dark line Y 460..463 (side.png draws it bold X 593..690,
    #                                        faint dashes in front; the step runs the whole length, all of it dark)
    paint(ob, lambda x, y, z: 0.0170 < x < UP_HW - 0.0002 and abs(y - SLOT_Y) < SLOT_R + 0.0015
          and Z(610) < z < Z(515), 1)                                             # slot walls + counter-bore floor
    paint(ob, lambda x, y, z: 0.0026 < z < 0.0106, 3)                             # the lug strip
    paint(ob, lambda x, y, z: 0.0106 <= z < 0.0137, 1)                            # the neck (dark seam X 499..501)
    ub = bmesh.new()                                                              # dust cover, hanging open
    zloft(ub, [(0.0090, NECK), (0.0155, NECK)], mat=1)                           # dark neck, collar | lug
    xc = -UP_HW - 0.0012
    box(ub, (xc, 0.2105, -0.054), (0.0030, 0.021, 0.062), chamfer=0.001)
    cylinder(ub, (xc, 0.2218, -0.088), (xc, 0.2218, -0.020), 0.0022, 6)
    prism(ub, [(-0.090, 0.2445), (-0.090, 0.2215), (-0.104, 0.2215), (-0.104, 0.2445)], "x", -UP_HW - 0.0055, -UP_HW + 0.002)
    for sx in (1, -1):                                                            # front pivot pin (505,479), r 4 px
        pin(ub, sx, 0.026, 0.0325, Y(479), Z(505.5), 0.0045, 12, mat=2, dimple=1)
    add_islands(ob, ub)
    return ob


def part_bolt():
    """Bolt carrier in the channel (2.5 mm clear), seen through the port and the slot."""
    bm = bmesh.new()
    rings_z(bm, BOLT_Y, [(-0.105, 0.0100), (-0.103, 0.0110), (-0.008, 0.0110), (-0.006, 0.0100)], 12)
    return finish(bm, "bolt", ["bolt"], "bolt")


def part_charging_handle():
    """Orange knob X 525..551, Y 437..457, 16 mm proud of the flank (top.png 0.018): a rounded box (1.5 mm
    chamfers) with 2 horizontal grooves at Y 443.5 / 450 (side.png col 540: three stacked bands); a stem through
    the slot (2 mm clear of the slot edges, 2 mm off the flank)."""
    bm = bmesh.new()
    zf, zr = Z(525), Z(551)
    xi, xo = UP_HW + 0.002, UP_HW + 0.018
    y0, y1 = Y(457), Y(437)
    c, gd = 0.0015, 0.0008                 # grooves with 45 deg walls: shaded bands, no ink line (ink is grey)

    def sec(d):
        pts = [(xi, y0 + d), (xo - c - d, y0 + d), (xo - d, y0 + c + d)]
        for yg in (Y(450), Y(443.5)):
            pts += [(xo - d, yg - 0.0014), (xo - d - gd, yg - 0.0006), (xo - d - gd, yg + 0.0006), (xo - d, yg + 0.0014)]
        return pts + [(xo - d, y1 - c - d), (xo - c - d, y1 - d), (xi, y1 - d)]

    zloft(bm, [(zf, sec(c)), (zf - c, sec(0)), (zr + c, sec(0)), (zr, sec(c))])
    box(bm, (0.0275, SLOT_Y, (Z(532.5) + Z(545)) / 2), (0.017, 0.011, Z(532.5) - Z(545)))   # 2.5 mm off the floor
    return finish(bm, "charging_handle", ["accent"], "charging_handle")


# magazine frame: straight box leaning 18.8 deg (side.png front edge 503 @ Y 550 -> 483 @ Y 610)
MAG_O = (-0.0466, 0.183)            # (z, y) the magazine's top, inside the well
MAG_A = (0.3217, -0.9468)           # axis, down and forward (dz, dy)
MAG_P = (-0.9468, -0.3217)          # across, toward the grip
MAG_TF, MAG_TR, MAG_HW = -0.030, 0.032, 0.023   # front / rear face across the axis inside the well, half width
MAG_CL = 0.0022                     # well clearance
MAG_GROOVES = (-0.0070, 0.0175)     # side.png row 600: dark lines 508-510 / 533-534 (thirds of the flank)


def M(s, t, x):
    return A(x, MAG_O[1] + s * MAG_A[1] + t * MAG_P[1], MAG_O[0] + s * MAG_A[0] + t * MAG_P[0])


def mag_ring(sec, s):
    return [M(s, t, x) for t, x in sec]


def mag_st(y, z):
    dz, dy = z - MAG_O[0], y - MAG_O[1]
    return dz * MAG_A[0] + dy * MAG_A[1], dz * MAG_P[0] + dy * MAG_P[1]


def part_receiver():
    """Lower receiver X 510..712 (0.059 wide, 3.5 mm inside the upper): flat flanks, magazine well block with a
    sloping mouth (510,513.5) -> (575.5,535) and a flared lip along it (a wedge, 4.5 -> 7.5 mm proud), a raised
    panel (3 mm) under the line (519,486.5) (562,486.5) (568.5,491.5) (marked: it inks), the well block's rear
    wall X 581.5 = the front of the trigger window, with the trigger guard's front bar let into it as a polymer
    rabbet X 576.5..581.5 (side.png row 515: ink 576, dark bar 577..580, window from 581); trigger pocket; rear
    takedown pin (682,469); bolt release (right)."""
    hw = LO_HW
    bm = pprism([(510, 462.7), (700, 462.7), (712, 470), (690, 494), (688, 505), (581.5, 505), (581.5, 537),
                 (575.5, 535), (510, 513.5)], hw, bevel=0.002)
    ob = finish(bm, "receiver", ["gunmetal", "dark", "lever", "polymer"], "receiver")
    union(ob, pprism([(517, 486.5), (562, 486.5), (568.5, 491.5), (575, 491.5), (575, 533.5), (517, 514)],
                     LO_HW + 0.003))
    ub = bmesh.new()                                                              # flared lip along the mouth
    xt, xb = LO_HW + 0.0045, LO_HW + 0.0075
    top, bot = PX([(509, 503.5), (575.5, 525)]), PX([(509, 514), (575.5, 535.5)])
    loft(ub, [[A(-xt, top[0][1], top[0][0]), A(xt, top[0][1], top[0][0]), A(xt, top[1][1], top[1][0]),
               A(-xt, top[1][1], top[1][0])],
              [A(-xb, bot[0][1], bot[0][0]), A(xb, bot[0][1], bot[0][0]), A(xb, bot[1][1], bot[1][0]),
               A(-xb, bot[1][1], bot[1][0])]])
    union(ob, ub)
    cb = bmesh.new()                                                              # magazine well
    sec = [(MAG_TF - MAG_CL, -MAG_HW - MAG_CL), (MAG_TR + MAG_CL, -MAG_HW - MAG_CL),
           (MAG_TR + MAG_CL, MAG_HW + MAG_CL), (MAG_TF - MAG_CL, MAG_HW + MAG_CL)]
    loft(cb, [mag_ring(sec, -0.002), mag_ring(sec, 0.12)], mat=1)
    diff(ob, cb)
    cb = bmesh.new()                                                              # trigger pocket
    box(cb, (0, 0.170, (Z(607) + Z(630)) / 2), (0.013, 0.030, Z(607) - Z(630)), mat=1)
    diff(ob, cb)
    ob_chamfer(ob, 0.0009, 42.0)
    cb = bmesh.new()                                                              # guard front bar rabbet (sharp)
    for sx in (1, -1):
        box(cb, (sx * 0.0435, (Y(505.5) + Y(541)) / 2, (Z(576.5) + Z(584)) / 2), (0.033, Y(505.5) - Y(541), Z(576.5) - Z(584)))
    diff(ob, cb)
    tidy(ob)
    paint(ob, lambda x, y, z: abs(x) > 0.0262 and Z(581.7) < z < Z(576.3) and Y(538) < y < Y(505), 3)
    ex = bmesh.new()
    for sx in (1, -1):
        pin(ex, sx, 0.024, LO_HW + 0.0015, Y(469), Z(682), 0.0036, 8, mat=2)                 # rear takedown pin
    box(ex, (-LO_HW - 0.001, Y(478), Z(592)), (0.004, 0.012, 0.016), chamfer=0.001, mat=2)   # bolt release, right flank
    add_islands(ob, ex)
    MARKS.append((ob, [(514, 486.5), (562, 486.5), (571, 493.4)], 0.0016, LO_HW + 0.002))
    return ob


def part_magazine():
    """Box magazine: straight inside the well (62 mm deep), the rear face flaring to 70.5 mm below the mouth
    (side.png rows 550 / 610: 62 -> 68 px wide), two thin dark grooves per flank (3.2 mm wide, 1 mm deep,
    45 deg walls: no ink line, the harness ink is lighter than the polymer), chamfered front; orange floor plate 3 mm proud all round, lowest corner at y 0."""
    bm = bmesh.new()
    w, g = MAG_HW, 0.0010                  # grooves 3.2 mm wide, 1 mm deep, 45 deg walls (no ink), painted dark

    def sec(tr):
        half = [(MAG_TF, w - 0.006), (MAG_TF + 0.006, w)]
        for tg in MAG_GROOVES:
            half += [(tg - 0.0016, w), (tg - 0.0006, w - g), (tg + 0.0006, w - g), (tg + 0.0016, w)]
        half += [(tr - 0.004, w), (tr, w - 0.004)]
        return half + [(t, -x) for t, x in reversed(half)]

    tb = 0.0405
    loft(bm, [mag_ring(sec(MAG_TR), 0.0), mag_ring(sec(MAG_TR), 0.045), mag_ring(sec(tb), 0.130),
              mag_ring(sec(tb), 0.163)])
    pf, pr, pw = MAG_TF - 0.003, tb + 0.003, w + 0.0025
    plate = [(pf, -pw), (pr, -pw), (pr, pw), (pf, pw)]
    plate_in = [(pf + 0.003, -pw + 0.003), (pr - 0.003, -pw + 0.003), (pr - 0.003, pw - 0.003), (pf + 0.003, pw - 0.003)]
    loft(bm, [mag_ring(plate_in, 0.1585), mag_ring(plate, 0.1615), mag_ring(plate, 0.1755), mag_ring(plate_in, 0.1785)],
         mat=1)
    ob = finish(bm, "magazine", ["polymer", "accent", "dark"], "magazine")

    def groove(x, y, z):
        s, t = mag_st(y, z)
        return (s < 0.158 and w - g - 0.0001 < abs(x) < w - 0.0001
                and any(abs(t - tg) < 0.0015 for tg in MAG_GROOVES))

    paint(ob, groove, 2)
    return ob


def part_trigger_guard():
    """Guard loop (polymer, 0.040 wide = 2/3 of the lower: it shows under the receiver in the concept): bottom bar
    Y 535..544, rear bar X 632..642 running into the grip, rounded lower corners; window X 581.5..632 (side.png
    row 515: white 581..631). The front bar is the rabbet in the lower's well block; a stub X 577..579.5 inside
    that block carries the bottom bar (clear of the magazine's rear face)."""
    bm = pprism([(577, 520), (579.5, 520), (579.5, 529), (581.5, 531.5), (583.5, 533.5), (587, 535), (625.5, 535),
                 (630, 532.5), (632, 528), (632, 497), (642, 497), (642, 536), (640, 541), (635, 544), (585, 544),
                 (579.5, 541.5), (577, 537)], 0.020)
    ob = finish(bm, "trigger_guard", ["polymer"], "trigger_guard")
    return ob_chamfer(ob, 0.0012, 42.0)


def part_trigger():
    """Curved blade X 608..625 (side.png row 515: 613..624), tip Y 530; top inside the trigger pocket (2.5 mm
    clear), pin at (618,497)."""
    bm = pprism([(613.5, 493.5), (614.6, 505), (614.4, 513), (613.2, 519.5), (611, 524.5), (608, 528),
                 (609.8, 530.6), (613.5, 528.3), (619.5, 523.5), (622, 517), (623.5, 509), (625, 501),
                 (625, 493.5)], 0.004, bevel=0.0008)
    return finish(bm, "trigger", ["trigger"], "trigger")


def part_selector():
    """Selector on the left flank: hub (661,481.7) r 7 px, arm forward X 630..661, tail down to Y 508."""
    bm = bmesh.new()
    yh, zh = Y(481.7), Z(661)
    xi = LO_HW + 0.002
    xcyl(bm, xi, xi + 0.012, yh, zh, 0.0098, 16)
    ob = finish(bm, "selector", ["lever"], "selector")
    ub = pprism([(630, 476), (661, 475.5), (661, 488), (630, 487.5)], 0.003)
    bmesh.ops.translate(ub, verts=ub.verts[:], vec=(xi + 0.0055, 0, 0))
    union(ob, ub)
    ub = pprism([(655, 484), (667, 484), (665.5, 509.5), (656.5, 509.5)], 0.003)
    bmesh.ops.translate(ub, verts=ub.verts[:], vec=(xi + 0.0055, 0, 0))
    union(ob, ub)
    return ob_chamfer(ob, 0.0007, 50.0)


# ---------------------------------------------------------------------------------------------------- furniture
def part_grip():
    """Pistol grip: vertical neck X 640 (side.png row 515: grip from 640) to Y 535, front edge to (669,613), heel
    (679,620) (727,602) (732,594), back strap up to (691,507). The front edge carries a wide flat facet (10 mm
    bevel: side.png shows a 10-11 px dark facet), the rest 5 mm chamfers."""
    bm = bmesh.new()
    prism(bm, PX([(640, 497), (691, 497), (694, 510), (732, 594), (727, 602), (679, 620), (669, 613), (646, 540),
                  (640, 535)]), "x", -0.022, 0.022)
    (za, ya), (zb, yb) = PX([(646, 540), (669, 613)])

    def on_front(v):
        z, y = -v.co.y, v.co.z
        return min(math.hypot(z - za, y - ya), math.hypot(z - zb, y - yb)) < 0.0005

    es = [e for e in bm.edges if all(on_front(v) for v in e.verts) and abs(e.verts[0].co.x - e.verts[1].co.x) < 1e-6]
    bmesh.ops.bevel(bm, geom=es, offset=0.010, offset_type="OFFSET", segments=1, profile=0.5, affect="EDGES",
                    clamp_overlap=True)
    chamfer(bm, 0.005, 50.0)
    return finish(bm, "grip", ["polymer"], "grip")


def part_stock():
    """Fixed stock: bar X 720..882 (top Y 420 -> 406.7, bottom 468 -> 476.7) with a lit top facet 18 mm tall at
    both ends (its ridge line marked: it inks) and a 7 mm bottom facet; butt plate X 878..910, Y 390..560 (own
    lighter material): elongated octagon (12 mm corner cuts), its top-front / bottom-front corners cut 12 mm, a
    raised inset pad on the rear face; strut from under the bar to the plate's foot (window (812,477) (875,477)
    (875,523))."""
    def sec(yt, yb):
        yr = yt - 0.018
        return [(0.017, yb), (0.025, yb + 0.007), (0.025, yr), (0.010, yt), (-0.010, yt), (-0.025, yr),
                (-0.025, yb + 0.007), (-0.017, yb)]
    bm = bmesh.new()
    zloft(bm, [(Z(882), sec(Y(406.7), Y(476.7))), (Z(720), sec(Y(420), Y(468)))])
    ob = finish(bm, "stock", ["polymer", "pad"], "stock")
    ub = bmesh.new()
    y0, y1, hw, c, f = Y(560), Y(390), 0.040, 0.012, 0.012

    def face(d):
        return [(hw - c, y0 + d), (hw, y0 + d + c), (hw, y1 - d - c), (hw - c, y1 - d), (-hw + c, y1 - d),
                (-hw, y1 - d - c), (-hw, y0 + d + c), (-hw + c, y0 + d)]
    zloft(ub, [(BUTT_Z + 0.003, face(0.007)), (BUTT_Z + 0.010, face(0)), (Z(878) - f, face(0)), (Z(878), face(f))])
    union(ob, ub)
    union(ob, pprism([(768, 470), (800, 470), (884, 531), (884, 555)], 0.011, bevel=0.002))
    ob_chamfer(ob, 0.0012, 42.0)
    cyp = (y0 + y1) / 2
    ub = bmesh.new()                                                              # the pad, sharp so it inks
    zloft(ub, [(BUTT_Z, scl(face(0), 0.80, cyp)), (BUTT_Z + 0.0015, scl(face(0), 0.85, cyp)),
               (BUTT_Z + 0.006, scl(face(0), 0.85, cyp))])
    union(ob, ub)
    paint(ob, lambda x, y, z: z < Z(877.0), 1)
    MARKS.append((ob, [(715, 436.4), (885, 422.4)], 0.0012, 0.0235))
    return ob


def part_rear_sight():
    """Rear sight housing X 668..697 (side.png row 390: ink 667-669, body 671-697), Y 373..413, top corners cut;
    two ears with an OPEN U-channel, a thin aperture leaf (20 x 22 x 3 mm, top 4.5 mm under the ears) with a real
    hole inside it; windage knobs (684,386) as lighter discs with a dark centre dimple; a low step block
    X 697..712 behind."""
    bm = bmesh.new()
    y0, ye, yt = 0.2695, 0.2970, Y(373)

    def sec(d):
        return [(-0.023, y0), (0.023, y0), (0.023, yt - 0.003 - d), (0.020, yt - d), (0.0125, yt - d), (0.0125, ye),
                (-0.0125, ye), (-0.0125, yt - d), (-0.020, yt - d), (-0.023, yt - 0.003 - d)]
    zloft(bm, [(Z(697), sec(0.004)), (Z(697) + 0.004, sec(0)), (Z(668) - 0.004, sec(0)), (Z(668), sec(0.004))])
    chamfer(bm, 0.0012)
    ob = finish(bm, "rear_sight", ["sight", "dark", "lever"], "sight")
    ub = bmesh.new()
    box(ub, (0, 0.300, Z(684)), (0.020, 0.022, 0.003))
    union(ob, ub)
    cb = bmesh.new()
    cylinder(cb, (0, 0.3045, Z(684) - 0.01), (0, 0.3045, Z(684) + 0.01), 0.0030, 12, mat=1)
    diff(ob, cb)
    ob_chamfer(ob, 0.0007, 50.0)
    ex = bmesh.new()
    for sx in (1, -1):
        pin(ex, sx, 0.021, 0.027, Y(386), Z(684), 0.0056, 12, mat=2, dimple=1, dimple_r=0.0020)
    box(ex, (0, (0.263 + Y(398)) / 2, (Z(697) + Z(712)) / 2), (0.038, Y(398) - 0.263, Z(697) - Z(712)), chamfer=0.003)
    add_islands(ob, ex)
    return ob


# ---------------------------------------------------------------------------------------------------- build
def build():
    del MARKS[:]
    root = hs.begin(SUBJECT, PALETTE)
    parts = [part_receiver(), part_upper(), part_bolt(), part_handguard(), part_band(), part_barrel(),
             part_muzzle_brake(), part_front_sight(), part_rail(), part_rear_sight(), part_stock(), part_grip(),
             part_magazine(), part_trigger_guard(), part_trigger(), part_charging_handle(), part_selector()]
    hs.end(parts)
    for ob, pts, tol, xmin in MARKS:
        mark_line(ob, pts, tol, xmin)
    return root, parts
