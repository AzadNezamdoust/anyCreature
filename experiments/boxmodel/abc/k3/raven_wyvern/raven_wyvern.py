import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

META = dict(creature='raven_wyvern', model='opus')

# the skeleton the model is built on (left side = +X)
J = dict(
    hips=(0, -0.10, 0.62), chest=(0, -0.48, 0.72), neck0=(0, -0.80, 0.78),
    neck1=(0, -0.92, 0.94), head=(0, -0.95, 1.14), bill=(0, -1.34, 1.10),
    tail0=(0, 0.20, 0.42), tail1=(0, 0.55, 0.30), tail2=(0, 0.95, 0.27), tail3=(0, 1.36, 0.27),
    hipL=(0.12, -0.42, 0.62), kneeL=(0.14, -0.40, 0.37), hockL=(0.135, -0.32, 0.25),
    ankleL=(0.13, -0.49, 0.05), toeL=(0.14, -0.77, 0.02), halluxL=(0.13, -0.37, 0.015),
    shoulderL=(0.17, -0.60, 0.78), elbowL=(0.24, -0.66, 0.93), wristL=(0.26, -0.70, 1.06),
    tipL=(0.29, 0.15, 0.20),
)

# half-ring profile: (fraction along the dorsal->ventral chord, fraction of half width)
PROF = ((0.0, 0.0), (0.22, 0.8), (0.55, 1.0), (0.85, 0.62), (1.0, 0.0))

# body sections, bill tip -> tail tip: dorsal seam point (y, z), ventral seam point (y, z), half width
SECS = [
    ((-1.372, 1.105), (-1.366, 1.062), 0.012),   # 0 bill tip (hooked)
    ((-1.29, 1.160), (-1.28, 1.085), 0.040),     # 1 bill
    ((-1.17, 1.235), (-1.16, 1.075), 0.075),     # 2 bill base / gape
    ((-1.07, 1.330), (-1.08, 1.060), 0.125),     # 3 brow / eye
    ((-0.95, 1.340), (-1.09, 1.000), 0.140),     # 4 skull (bend: throat)
    ((-0.83, 1.270), (-1.10, 0.880), 0.160),     # 5 occiput
    ((-0.78, 1.100), (-1.09, 0.750), 0.170),     # 6 neck
    ((-0.75, 0.970), (-1.02, 0.600), 0.200),     # 7 neck base
    ((-0.62, 0.990), (-0.80, 0.470), 0.230),     # 8 shoulder / keel
    ((-0.47, 0.990), (-0.55, 0.400), 0.235),     # 9 front of leg
    ((-0.28, 0.930), (-0.30, 0.380), 0.215),     # 10 behind leg
    ((-0.08, 0.720), (-0.06, 0.360), 0.160),     # 11 rump
    ((0.14, 0.520), (0.13, 0.330), 0.100),       # 12 tail base
    ((0.34, 0.410), (0.33, 0.280), 0.072),       # 13
    ((0.55, 0.335), (0.55, 0.248), 0.050),       # 14
    ((0.75, 0.310), (0.75, 0.240), 0.038),       # 15
    ((0.94, 0.295), (0.94, 0.235), 0.030),       # 16 fin root
    ((1.15, 0.360), (1.15, 0.170), 0.016),       # 17 fin
    ((1.35, 0.450), (1.36, 0.100), 0.010),       # 18 fin tip
]


# stage-2 S-curve of the neck: y shift per body section (the mid-neck ring back, the throat/skull ring forward)
NECK_DY = {4: -0.02, 6: 0.07}


def sec(D, Vv, w, prof=PROF):
    return [(xf * w, D[0] + s * (Vv[0] - D[0]), D[1] + s * (Vv[1] - D[1])) for s, xf in prof]


def box(c, a, b):
    c, a, b = Vector(c), Vector(a), Vector(b)
    return [c + a + b, c - a + b, c - a - b, c + a - b]


def grow(bm, face, pts):
    """Extrude one face and place its new ring at pts (cyclic order chosen for the shortest sides)."""
    old = list(face.verts)
    r = extrude(bm, [face])
    nf = r['faces'][0]
    part = {}
    for v in nf.verts:
        for e in v.link_edges:
            w = e.other_vert(v)
            if w in old:
                part[w] = v
    new = [part[o] for o in old]
    pts = [Vector(p) for p in pts]
    n, best = len(pts), None
    for d in (1, -1):
        for s in range(n):
            order = [pts[(s + d * i) % n] for i in range(n)]
            cost = sum((o.co - p).length for o, p in zip(old, order))
            if best is None or cost < best[0]:
                best = (cost, order)
    for v, p in zip(new, best[1]):
        v.co = p
    return nf, r['sides']


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, sec(D, Vv, w)) for D, Vv, w in SECS]
    bands = [bridge(bm, rows[i], rows[i + 1]) for i in range(len(rows) - 1)]
    cap(bm, rows[0]); cap(bm, rows[-1])
    # leg: drumstick -> reversed hock -> tarsus -> foot block -> toe paddle + hallux
    f = bands[9][2]
    f, _ = grow(bm, f, box((0.14, -0.39, 0.37), (0, 0.075, 0), (0.055, 0, 0)))
    f, _ = grow(bm, f, box(J['hockL'], (0, 0.045, 0.012), (0.04, 0, 0)))
    f, _ = grow(bm, f, box((0.13, -0.47, 0.10), (0, 0.035, 0), (0.03, 0, 0)))
    f, sides = grow(bm, f, box((0.13, -0.49, 0.0), (0, 0.06, 0), (0.05, 0, 0)))
    front = min(sides, key=lambda g: g.calc_center_median().y)
    back = max(sides, key=lambda g: g.calc_center_median().y)
    grow(bm, front, box((0.14, -0.77, 0.02), (0.08, 0, 0), (0, 0, 0.02)))
    grow(bm, back, box(J['halluxL'], (0.025, 0, 0), (0, 0, 0.015)))
    # wing = forelimb: humerus up to the wrist, then the folded hand/membrane blade back to the tip
    f = bands[8][1]
    f, _ = grow(bm, f, box(J['elbowL'], (0, 0.045, 0), (0.035, 0, 0)))
    f, sides = grow(bm, f, box(J['wristL'], (0, 0.04, 0), (0.03, 0, 0)))
    back = max(sides, key=lambda g: g.calc_center_median().y)
    f, _ = grow(bm, back, [(0.27, -0.03, 0.66), (0.35, -0.22, 0.50), (0.32, -0.42, 0.34), (0.255, -0.22, 0.52)])
    grow(bm, f, [(0.28, 0.17, 0.23), (0.31, 0.15, 0.20), (0.30, 0.12, 0.18), (0.27, 0.15, 0.20)])
    snap_seam(bm)
    return object_from_bm('body', bm)


EYE = (0.10, -1.12, 1.21)


def near_eye(c):
    return abs(c[0]) > 0.04 and -1.17 < c[1] < -1.07 and 1.14 < c[2] < 1.27


META['keep_valleys'] = near_eye


def stage2(k, body):
    bm = edit(body)
    L1 = verts_where(bm, lambda c: abs(c.z - 0.37) < 0.006 and 0.07 < c.x < 0.2 and -0.47 < c.y < -0.31)
    L2 = verts_where(bm, lambda c: 0.23 < c.z < 0.27 and 0.08 < c.x < 0.19 and -0.38 < c.y < -0.26)
    L3 = verts_where(bm, lambda c: abs(c.z - 0.10) < 0.006 and 0.09 < c.x < 0.17 and -0.51 < c.y < -0.43)
    assert len(L1) == len(L2) == len(L3) == 4, (len(L1), len(L2), len(L3))

    def up_edge(v):
        return max(v.link_edges, key=lambda e: e.other_vert(v).co.z)
    with k.topo(bm, 'loop', 'drumstick loop: the thigh bends where the leg leaves the body'):
        loopcut(bm, up_edge(L1[0]), t=0.5, near=L1[0])
    with k.topo(bm, 'loop', 'second hock loop, above the reversed ankle: the bend'):
        loopcut(bm, up_edge(L2[0]), t=0.35, near=L2[0])
    with k.topo(bm, 'loop', 'third hock loop, below the reversed ankle: the bend'):
        loopcut(bm, up_edge(L3[0]), t=0.75, near=L3[0])
    eyef = face_near(bm, EYE, n=(1, 0, 0))
    en = eyef.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face'):
        inner = inset(bm, [eyef], 0.38)
    move(list(inner[0].verts), -0.014 * en)
    # brow ridge overhangs the socket; bill base pinched so the bill reads as its own block
    move(verts_where(bm, lambda c: c.x > 0.05 and abs(c.y + 1.072) < 0.004 and abs(c.z - 1.271) < 0.006), (0.022, -0.02, 0.01))
    for v in verts_where(bm, lambda c: c.x > 0.05 and abs(c.y + 1.165) < 0.01 and 1.09 < c.z < 1.21):
        v.co.x *= 0.85
    # tarsus thicker (the sheet's shank is sturdy), toes fanned
    scale(L3, (1.45, 1.3, 1.0)); scale(L2, (1.2, 1.15, 1.0))
    for v in verts_where(bm, lambda c: c.y < -0.74 and c.z < 0.05 and c.x > 0.03):
        v.co.x = 0.14 + (v.co.x - 0.14) * 1.35
    # fin: the spade fans out in plan (the sheet's fin reads in the top and rear views)
    for v in verts_where(bm, lambda c: c.y > 1.3):
        v.co.x *= 3.5
    for v in verts_where(bm, lambda c: 1.1 < c.y < 1.2):
        v.co.x *= 1.8
    # sliver fix: the wing tip ring and the wrist block were needle-thin against the long blade faces
    tip = verts_where(bm, lambda c: c.y > 0.1 and c.x > 0.25 and c.z < 0.3)
    assert len(tip) == 4, len(tip)
    scale(tip, (2.0, 3.0, 3.0))
    for zc in (0.93, 1.06):
        scale(verts_where(bm, lambda c: abs(c.z - zc) < 0.02 and 0.19 < c.x < 0.3 and -0.75 < c.y < -0.6), (1.4, 1.4, 1.0))
    s16 = verts_where(bm, lambda c: abs(c.y - 0.94) < 0.005)
    c16 = centre(s16)
    scale(s16, (1.6, 1.0, 1.5), pivot=(0.0, c16.y, c16.z))
    # tail (item 4): the tail rings taper from 100% at the base (sec 12) to 55% at the fin root (sec 16)
    for i in range(13, 17):
        f = 1.0 - 0.2 * (i - 12) / 4
        yc = (SECS[i][0][0] + SECS[i][1][0]) / 2
        rv = verts_where(bm, lambda c: abs(c.y - yc) < 0.012 and c.z < 0.6)
        assert len(rv) == 5, (i, len(rv))
        cz = centre(rv).z
        scale(rv, (f, 1.0, f), pivot=(0.0, yc, cz))
    # fin (item 4): the trailing edge notched between three points (top, middle, bottom): the two verts
    # between them pulled forward by 10% of the fin length
    fin = verts_where(bm, lambda c: c.y > 1.3)
    zs = sorted({round(v.co.z, 3) for v in fin})
    assert len(zs) == 5, zs
    for v in fin:
        if round(v.co.z, 3) in (zs[1], zs[3]):
            v.co.y -= 0.04
    # neck S (item 3): the mid-neck ring back, the skull/throat ring forward (y only: rear/front IoU hold)
    for i, dy in NECK_DY.items():
        ringv = [vert_near(bm, p) for p in sec(*SECS[i])]
        assert all((v.co - Vector(p)).length < 1e-4 for v, p in zip(ringv, sec(*SECS[i]))), i
        move(ringv, (0.0, dy, 0.0))
    # repair r2 item 5: the brow overhangs the eye: the upper verts of the brow (sec 3) and skull (sec 4) rings
    # above the eye forward 0.014, down 0.004 (outward moves fail the rear: out 0.011 az180 IoU 0.898, out 0.004 0.899)
    brow = verts_where(bm, lambda c: c.x > 0.05 and -1.10 < c.y < -0.97 and 1.255 < c.z < 1.29)
    assert len(brow) == 2, len(brow)
    move(brow, (0.0, -0.014, -0.004))
    # wing (item 1): two cross loops put verts on the trailing edge between the finger spars, and those
    # are pulled up into membrane bays. (Moving the outer ridge vert up/out for a thinner arm band and an
    # edge thickness dropped the az180 IoU to 0.878-0.896 against the 0.9 floor: not done.)
    bf, bt = vert_near(bm, (0.32, -0.42, 0.34)), vert_near(bm, (0.31, 0.065, 0.135))
    e = next(e for e in bf.link_edges if e.other_vert(bf) is bt)
    with k.topo(bm, 'loop', 'wing membrane: cross loop at the rear spar bay, so the trailing edge can scallop'):
        r1 = loopcut(bm, e, t=0.68, near=bf)
    m1 = min(r1, key=lambda v: v.co.z)
    e = next(e for e in bf.link_edges if e.other_vert(bf) is m1)
    with k.topo(bm, 'loop', 'wing membrane: cross loop at the front spar bay, so the trailing edge can scallop'):
        r2 = loopcut(bm, e, t=0.34, near=bf)
    m2 = min(r2, key=lambda v: v.co.z)
    move([m1, m2], (0.0, 0.0, 0.035))
    commit(body, bm)


PAL = dict(plumage='#2c3346', membrane='#6a3f9a', bill='#1c1c22', billtip='#d8cfb8',
           eye='#f0a020', shank='#6e665e', horn='#e4dcc8')
Z = Vector((0, 0, 1))


def around(c, d, r1, r2, n=4, phase=45.0, up=None):
    c, d = Vector(c), Vector(d).normalized()
    if up is not None:          # a fixed frame: no twist between rings when the direction swings
        up = Vector(up)
        u = up - d * up.dot(d)
    else:
        u = d.cross(Z) if abs(d.dot(Z)) < 0.95 else d.cross(Vector((1, 0, 0)))
    u.normalize(); v = d.cross(u).normalized()
    out = []
    for i in range(n):
        a = math.radians(phase + 360.0 * i / n)
        out.append(c + u * (r1 * math.cos(a)) + v * (r2 * math.sin(a)))
    return out


def tube(bm, centres, radii, tip, flat=1.0, up=None):
    """A tapered n-gon spike through centres, closed at the root, ending in a point."""
    rs = []
    for i, c in enumerate(centres):
        d = Vector(centres[min(i + 1, len(centres) - 1)]) - Vector(centres[max(i - 1, 0)])
        rs.append(ring(bm, around(c, d, radii[i], radii[i] * flat, up=up)))
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, rs[0])
    t = bm.verts.new(Vector(tip))
    n = len(rs[-1])
    for i in range(n):
        bm.faces.new([rs[-1][i], rs[-1][(i + 1) % n], t])


def ridge_z(y):
    pts = [(D[0], D[1]) for D, _, _ in SECS[7:17]]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[-1][1]


def surf(i, s, xf):
    D, Vv, w = SECS[i]
    dy = NECK_DY.get(i, 0.0)
    P = Vector((xf * w, D[0] + dy + s * (Vv[0] - D[0]), D[1] + s * (Vv[1] - D[1])))
    M = Vector((0, (D[0] + Vv[0]) / 2 + dy, (D[1] + Vv[1]) / 2))
    o = Vector((P.x, 0, 0)) + 0.6 * (P - M - Vector((P.x, 0, 0)))
    return P, o.normalized()


# side view (y, z) of the blade's outer ridge verts, wrist -> tip: faces above it are the wing arm's top band
ARM = ((-0.644, 1.06), (-0.22, 0.50), (-0.133, 0.491), (0.035, 0.318), (0.155, 0.195))


def arm_z(y):
    for (y0, z0), (y1, z1) in zip(ARM, ARM[1:]):
        if y <= y1:
            return z0 + (z1 - z0) * max(0.0, (y - y0)) / (y1 - y0)
    return ARM[-1][1]


def body_rule(c, n, i):
    x, y, z = abs(c[0]), c[1], c[2]
    if near_eye(c):
        return 'bill'
    if y < -1.30 and z > 1.0:
        return 'billtip'
    if y < -1.165 and z > 1.0:
        return 'bill'
    if y > 1.08:
        return 'membrane'          # the fan; the fin's front third stays blue-black
    if x > 0.24 and y > -0.66 and z < 1.0:
        # dark wing arm (top faces from the wrist back to the second cross loop) over the purple membrane
        return 'plumage' if z > arm_z(y) and y < -0.02 else 'membrane'
    if z < 0.31 and y < -0.2 and x > 0.02:
        return 'shank'
    return 'plumage'


def piece(name, bm, key, mirror=True):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: PAL[key]}, lambda c, n, i: key)
    return ob


def stage3(k, body):
    paint(body, PAL, body_rule)
    pieces = []
    # eye lens, proud of its socket
    bm0 = edit(body)
    f = face_near(bm0, EYE, n=(1, 0, 0))
    ec, en = f.calc_center_median().copy(), f.normal.copy()
    bm0.free()
    bm = bmesh.new()
    # a lens 1.3x wider than before (0.08 across, ~1/7 of the head), depth 0.024 < 1/3 of its width
    # repair r2 item 5: the lens tilted 15 deg forward, so it looks along the bill
    en = (en * math.cos(math.radians(15)) + Vector((0, -1, 0)) * math.sin(math.radians(15))).normalized()
    c = ec + en * 0.004
    eq = around(c, en, 0.040, 0.030, n=6, phase=0.0)
    vs = ring(bm, eq)
    fp, bp = bm.verts.new(c + en * 0.012), bm.verts.new(c - en * 0.012)
    for i in range(6):
        bm.faces.new([vs[i], vs[(i + 1) % 6], fp]); bm.faces.new([vs[(i + 1) % 6], vs[i], bp])
    pieces.append(piece('eye', bm, 'eye'))
    # repair r2 item 5: a brow shelf over the lens (stage 2 could not push the brow out: az180 IoU floor),
    # rooted in the skull behind the eye, running forward over it to a point above the bill base
    bm = bmesh.new()
    tube(bm, [ec + Vector((0, 0.06, 0.035)) - en * 0.02, ec + Vector((0, 0.0, 0.045)) + en * 0.012],
         [0.013, 0.011], ec + Vector((0, -0.045, 0.032)) + en * 0.006, flat=2.2, up=(0, 0, 1))
    pieces.append(piece('brow', bm, 'plumage'))
    # swept-back horns
    bm = bmesh.new()
    tube(bm, [(0.06, -0.94, 1.24), (0.09, -0.86, 1.335), (0.125, -0.78, 1.37), (0.15, -0.71, 1.40)],
         [0.035, 0.027, 0.018, 0.010], (0.165, -0.655, 1.435))
    pieces.append(piece('horn', bm, 'horn'))
    # thumb claw: a hook at the wrist knuckle, forward then down; talons on the toes and hallux
    bm = bmesh.new()
    tube(bm, [(0.265, -0.715, 1.035), (0.28, -0.77, 1.105), (0.29, -0.83, 1.105)], [0.032, 0.026, 0.018],
         (0.29, -0.87, 1.045))
    # talons 2x: curved hooks (3 rings, tip down) rooted in the toe ends, and the hallux talon
    for x, dx in ((0.06, -0.35), (0.14, 0.0), (0.22, 0.35)):
        tube(bm, [(x, -0.75, 0.025), (x + dx * 0.06, -0.82, 0.05), (x + dx * 0.10, -0.88, 0.045)],
             [0.026, 0.02, 0.013], (x + dx * 0.13, -0.925, 0.004))
    tube(bm, [(0.13, -0.385, 0.02), (0.13, -0.33, 0.04), (0.13, -0.28, 0.035)], [0.02, 0.015, 0.01],
         (0.13, -0.25, 0.004))
    pieces.append(piece('claws', bm, 'bill'))
    # three finger spars fanning from the wrist knuckle over the membrane's outer face to the trailing-edge
    # points between the bays; each ring sits on the blade surface (ray cast), 30% of its diameter sunk in
    bm0 = edit(body)
    tree = BVHTree.FromBMesh(bm0)
    bm = bmesh.new()
    K = Vector((-0.62, 1.0))
    for E in ((-0.34, 0.36), (-0.17, 0.31), (0.055, 0.14)):
        E = Vector(E)
        cs, rs = [], (0.026, 0.024, 0.022, 0.020, 0.018, 0.0165, 0.015)
        for s_, r in zip((0.06, 0.20, 0.34, 0.48, 0.62, 0.76, 0.90), rs):
            yz = K.lerp(E, s_)
            loc, nrm, _, _ = tree.ray_cast(Vector((0.6, yz.x, yz.y)), Vector((-1, 0, 0)))
            cs.append(loc + nrm * (0.4 * r))
        yz = K.lerp(E, 1.07)
        tip = Vector((cs[-1].x, yz.x, yz.y))
        tube(bm, cs, rs, tip, up=(1, 0, 0))
    pieces.append(piece('spar', bm, 'plumage'))
    # three dark fin ribs fanning from the fin root to the trailing-edge points, on the fin's side face
    bm = bmesh.new()
    R = Vector((0.98, 0.27))
    for E in ((1.33, 0.42), (1.33, 0.27), (1.33, 0.13)):
        E = Vector(E)
        cs, rs = [], (0.014, 0.012, 0.010, 0.008)
        for s_, r in zip((0.05, 0.33, 0.61, 0.88), rs):
            yz = R.lerp(E, s_)
            loc, nrm, _, _ = tree.ray_cast(Vector((0.3, yz.x, yz.y)), Vector((-1, 0, 0)))
            cs.append(loc + nrm * (0.4 * r))
        yz = R.lerp(E, 1.0)
        tube(bm, cs, rs, Vector((cs[-1].x, yz.x, yz.y)), up=(1, 0, 0))
    bm0.free()
    pieces.append(piece('finribs', bm, 'plumage'))
    # repair r2 item 4: dorsal plates, graded: height 1.0 at the shoulders, 0.85 mid-back, then linearly to 0.3
    # at the fin root; spacing wide over the back, close on the tail; each leans back 25 deg and is flattened
    # sideways (width across 60% of the length along); dark plumage with cream tips (a ring at 60% height)
    bm = bmesh.new()
    N, tipf = 12, []
    lean = math.tan(math.radians(25))
    for j in range(N):
        u = j / (N - 1)
        y = -0.60 + 1.54 * u * (1.4 - 0.4 * u)
        g = 1.0 - 0.15 * (y + 0.60) / 0.40 if y < -0.20 else 0.85 - 0.55 * (y + 0.20) / 1.14
        h, L = 0.12 * g, 0.055 * g
        ws = 0.6 * L
        zr = ridge_z(y)
        base = [Vector((0, y - L, ridge_z(y - L) - 0.03)), Vector((ws, y, zr - 0.035)),
                Vector((0, y + L, ridge_z(y + L) - 0.03)), Vector((-ws, y, zr - 0.035))]
        bv = ring(bm, base)
        m = 0.6 * h
        mc = Vector((0, y + 0.15 * L + m * lean, zr + m - 0.02))
        mv = ring(bm, [mc + (q - Vector((0, y, zr - 0.033))) * 0.42 for q in base])
        bridge(bm, bv, mv, closed=True)
        tp = bm.verts.new(Vector((0, y + 0.3 * L + h * lean, zr + h)))
        cap(bm, bv)
        for i in range(4):
            tipf.append(bm.faces.new([mv[i], mv[(i + 1) % 4], tp]))
    bm.faces.index_update()
    tips = {f.index for f in tipf}
    ob = object_from_bm('spines', bm, mirror=False)
    paint(ob, {'plumage': PAL['plumage'], 'horn': PAL['horn']}, lambda c, n, i: 'horn' if i in tips else 'plumage')
    pieces.append(ob)
    # repair r2 item 3: 5 shingled clumps per side, broad flat wedges lying down the throat (tip along the
    # surface toward the chest, 25 deg off it), width 0.7 L, thickness 0.4 W, L 0.08-0.14 (biggest mid-throat),
    # roots sunk 0.03. No under-jaw clump (r13: it clipped when the head turned)
    bm = bmesh.new()
    for i, sv, xf, ln in ((5, 0.62, 0.92, 0.09), (6, 0.58, 0.95, 0.12), (6, 0.86, 0.50, 0.14),
                          (7, 0.60, 0.92, 0.11), (7, 0.86, 0.50, 0.08)):
        P, o = surf(i, sv, xf)
        tg = surf(i + 1, sv, xf)[0] - P
        tg = (tg - o * tg.dot(o)).normalized()
        dr = tg * math.cos(math.radians(25)) + o * math.sin(math.radians(25))
        W, T = 0.7 * ln, 0.28 * ln
        root = P - o * 0.03
        tip = root + dr * ln
        tip = tip + o * 0.03
        mid = root.lerp(tip, 0.4) + o * 0.04
        r = T / 2 / 0.707
        tube(bm, [root, mid], [r, 0.8 * r], tip, flat=W / T, up=o)
    pieces.append(piece('hackles', bm, 'plumage'))
    return pieces


def pin_blade(body):
    """The folded blade (membrane ring + tip ring, |x| >= 0.245 behind the wrist) is weighted 100% to
    its side's hand bone: heat weights leaked the thigh/hips onto it, so the walk swung the blade
    face through the shoulder (clip warning, move f1/f17)."""
    for side, bone in ((1, 'hand.L'), (-1, 'hand.R')):
        ids = [v.index for v in body.data.vertices if side * v.co.x >= 0.245 and v.co.y > -0.5]
        for g in body.vertex_groups:
            g.remove(ids)
        body.vertex_groups[bone].add(ids, 1.0, 'REPLACE')
        # the wing root on the flank: heat gave it the thigh (0.76 at the shoulder vertex), so the walk
        # shoved the shoulder face into the blade; hand that weight to the chest
        th, ch = body.vertex_groups['thigh' + bone[-2:]], body.vertex_groups['chest']
        for v in body.data.vertices:
            c = v.co
            if side * c.x > 0.2 and -0.8 < c.y < -0.45 and c.z > 0.6:
                w = next((g.weight for g in v.groups if g.group == th.index), 0.0)
                if w > 0:
                    th.remove([v.index]); ch.add([v.index], w, 'ADD')


def pin_hand(ob, pred, name='hand'):
    for side, bone in ((1, name + '.L'), (-1, name + '.R')):
        ids = [v.index for v in ob.data.vertices if side * v.co.x > 0 and pred(v.co)]
        if not ids:
            continue
        for g in ob.vertex_groups:
            g.remove(ids)
        (ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)).add(ids, 1.0, 'REPLACE')


def pin_wrist(ob, body):
    """The thumb hook (z > 0.9) copies the skin weights of the nearest wrist-block vertex (|x| > 0.2, z > 0.95),
    whole hook alike: pinned to one bone it slid off the knuckle when the hand rolled for the mantle (drift)."""
    wr = [v for v in body.data.vertices if abs(v.co.x) > 0.2 and v.co.z > 0.95]
    root = {1: Vector((0.265, -0.715, 1.035)), -1: Vector((-0.265, -0.715, 1.035))}
    for side in (1, -1):
        src = min((v for v in wr if side * v.co.x > 0), key=lambda v: (v.co - root[side]).length)
        ws = {body.vertex_groups[g.group].name: g.weight for g in src.groups if g.weight > 0}
        ids = [v.index for v in ob.data.vertices if side * v.co.x > 0 and v.co.z > 0.9]
        for g in ob.vertex_groups:
            g.remove(ids)
        for nm, w in ws.items():
            (ob.vertex_groups.get(nm) or ob.vertex_groups.new(name=nm)).add(ids, w, 'REPLACE')


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hips'], J['chest'], None),
        ('chest', J['chest'], J['neck0'], 'hips', True),
        ('neck0', J['neck0'], J['neck1'], 'chest', True),
        ('neck1', J['neck1'], J['head'], 'neck0', True),
        ('head', J['head'], J['bill'], 'neck1', True),
        ('tail0', J['hips'], J['tail0'], 'hips'),
        ('tail1', J['tail0'], J['tail1'], 'tail0', True),
        ('tail2', J['tail1'], J['tail2'], 'tail1', True),
        ('tail3', J['tail2'], J['tail3'], 'tail2', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L', True),
        ('tarsus.L', J['hockL'], J['ankleL'], 'shin.L', True),
        ('toe.L', J['ankleL'], J['toeL'], 'tarsus.L', True),
        ('arm.L', J['shoulderL'], J['wristL'], 'chest'),
        ('hand.L', J['wristL'], J['tipL'], 'arm.L', True),
    ], roll='auto')
    skin(body, rig)
    pin_blade(body)
    for p in pieces:
        bind(p, rig, body=body)
        # the spars ride the blade: 100% the hand bone, like the blade; the thumb hook sits on the wrist
        # block: 100% the arm (nearest-face weights gave the hook tip neck/head weights, so it folded)
        pin_hand(p, lambda c: p.name.endswith('spar'))
        if p.name.endswith('claws'):
            pin_wrist(p, body)
    # repair r2 item 2: a base S-neck under every key of every clip (stage 2 is at the az180 IoU floor): the
    # neck base pitched forward/down, the upper neck back/up, the head down so the bill stays level
    NECK = {'neck0': (25, 0, 0), 'neck1': (-35, 0, 0), 'head': (10, 0, 0)}

    def sclip(rig, name, keys):
        out = {}
        for f, kv in keys.items():
            kv = dict(kv)
            for b, r in NECK.items():
                kv[b] = tuple(a + c for a, c in zip(kv.get(b, (0, 0, 0)), r))
            out[f] = kv
        return clip(rig, name, out)
    # idle: breathing and a curious head tilt
    sclip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'head': (0, 0, 7), 'neck1': (-3, 0, 0)},
                       24: {'chest': (-1, 0, 0), 'head': (0, 0, 0)},
                       36: {'chest': (2, 0, 0), 'head': (0, 0, -6), 'neck1': (3, 0, 0)}, 48: {}})
    # move: bird-like stalking walk, head bobbing, tail swaying
    A, B = 16, 12
    sclip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'neck1': (6, 0, 0), 'tail1': (0, 0, 5), 'hips': (0, 0, 3)},
        9: {'thigh.R': (5, 0, 0), 'shin.R': (-B, 0, 0), 'tarsus.R': (2 * B, 0, 0), 'neck1': (-4, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'neck1': (6, 0, 0), 'tail1': (0, 0, -5), 'hips': (0, 0, -3)},
        25: {'thigh.L': (5, 0, 0), 'shin.L': (-B, 0, 0), 'tarsus.L': (2 * B, 0, 0), 'neck1': (-4, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'neck1': (6, 0, 0), 'tail1': (0, 0, 5), 'hips': (0, 0, 3)}})
    # attack: coil back, lunge the neck with the wings mantled up and out (held f17-23), recover.
    # arm Z swings the wing out from the flank first so the blade clears it
    def arms(x, z, hx=None, roll=0):   # the arm lifts (X); the hand swings the blade out (Z), up (X), rolls (Y)
        hx = z / 2 if hx is None else hx
        return {'arm.L': (x, 0, 0), 'arm.R': (x, 0, 0), 'hand.L': (hx, roll, -z), 'hand.R': (hx, -roll, z)}
    # repair r2 item 1: the hand bone runs back-down from the wrist, so hand X alone lifts the blade into a
    # flat plank behind the body. Swept out 70 about its up-back axis, lifted 45, rolled 40: the tip goes out
    # and up (0.83, 0.23, 0.51) and the membrane's outer face turns forward (normal -Y 0.97): a spread mantle
    MANTLE = dict(z=70, hx=45, roll=40)
    sclip(rig, 'attack', {
        1: {},
        12: {'neck0': (-12, 0, 0), 'neck1': (-8, 0, 0), 'head': (8, 0, 0), **arms(15, 15)},
        17: {'neck0': (12, 0, 0), 'neck1': (9, 0, 0), 'head': (0, 0, 0), 'chest': (3, 0, 0), 'tail1': (4, 0, 0),
             **arms(22, **MANTLE)},
        20: {'neck0': (18, 0, 0), 'neck1': (14, 0, 0), 'head': (-4, 0, 0), 'chest': (4, 0, 0), 'tail1': (6, 0, 0),
             **arms(22, **MANTLE)},
        23: {'neck0': (14, 0, 0), 'neck1': (10, 0, 0), 'head': (-2, 0, 0), 'chest': (3, 0, 0), 'tail1': (5, 0, 0),
             **arms(22, **MANTLE)},
        30: {'neck0': (6, 0, 0), 'neck1': (4, 0, 0), **arms(10, 10)},
        40: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
