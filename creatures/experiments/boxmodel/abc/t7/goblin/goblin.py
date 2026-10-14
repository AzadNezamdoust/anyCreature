import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='goblin', model='opus')

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    hips=(0.0, 0.02, 0.44), chest=(0.0, 0.0, 0.62), neck=(0.0, -0.10, 0.74), head=(0.0, -0.13, 0.80),
    crown=(0.0, -0.13, 1.08),
    hipL=(0.105, 0.02, 0.40), kneeL=(0.165, -0.12, 0.235), ankleL=(0.135, 0.0, 0.08), toeL=(0.13, -0.16, 0.02),
    shoulderL=(0.17, -0.05, 0.70), elbowL=(0.255, -0.02, 0.48), wristL=(0.27, -0.095, 0.29),
    handL=(0.28, -0.14, 0.16),
    earL=(0.16, -0.10, 0.96), eartipL=(0.41, -0.03, 1.02),
)

FRONT = Vector((0, -1, 0))
ANG = [0, 30, 60, 75, 105, 125, 155, 180]          # torso half-ring stations (deg from the front)


def tring(z, yc, a, df, db, zf=0.0):
    """Torso half ring: front seam -> side -> back seam. zf tilts the front up/down."""
    pts = []
    for d in ANG:
        t = math.radians(d)
        c = math.cos(t)
        y = yc - (df if c > 0 else db) * c
        pts.append((a * math.sin(t) if 0 < d < 180 else 0.0, y, z + zf * max(c, 0)))
    return pts


def frame_of_dir(d):
    d = Vector(d).normalized()
    w = FRONT - d * FRONT.dot(d)
    if w.length < 1e-6:
        w = Vector((0, 0, 1)) - d * d.z
    w.normalize()
    return d, d.cross(w), w


class Limb:
    """Extrude a face region along a path; each section is a box (a x b half-extents)
    placed on the bisector plane of the path, vertices keeping their parametric angle."""

    def __init__(self, bm, faces, d0):
        self.bm, self.faces = bm, list(faces)
        self.fr = frame_of_dir(d0)
        self.c = centre(list({v for f in self.faces for v in f.verts}))

    def run(self, secs):
        pts = [self.c] + [Vector(s[0]) for s in secs]
        out = []
        for i, s in enumerate(secs):
            c, a, b = Vector(s[0]), s[1], s[2]
            rot = s[3] if len(s) > 3 else 0.0
            din = (pts[i + 1] - pts[i]).normalized()
            d = din + (pts[i + 2] - pts[i + 1]).normalized() if i + 2 < len(pts) else din
            out.append(self.step(c, a, b, d, rot))
        return out

    def step(self, c, a, b, d, rot=0.0):
        _, u0, w0 = self.fr
        oc = self.c
        r = extrude(self.bm, self.faces)
        self.faces = r['faces']
        offs = [(v, (v.co - oc).dot(u0), (v.co - oc).dot(w0)) for v in r['verts']]
        mu = max(abs(o[1]) for o in offs) or 1.0
        mw = max(abs(o[2]) for o in offs) or 1.0
        self.fr = frame_of_dir(d)
        _, u, w = self.fr
        for v, ou, ow in offs:
            th = math.atan2(ow / mw, ou / mu) + math.radians(rot)
            cs, sn = math.cos(th), math.sin(th)
            m = max(abs(cs), abs(sn))
            v.co = c + u * (a * cs / m) + w * (b * sn / m)
        self.c = Vector(c)
        return r


def ladder(bm, R, flip=False):
    """Close a half ring with quads (rungs P1-P6, P2-P5, P3-P4). Returns the three faces."""
    fs = [[R[0], R[1], R[6], R[7]], [R[1], R[2], R[5], R[6]], [R[2], R[3], R[4], R[5]]]
    return [bm.faces.new(list(reversed(f)) if flip else f) for f in fs]


def stage1(k):
    bm = bmesh.new()
    rings = [
        # R0 crotch: a rounded rectangle, the leg root is its outer quad
        [(0, -0.06, 0.40), (0.04, -0.065, 0.40), (0.07, -0.06, 0.40), (0.14, -0.03, 0.40),
         (0.14, 0.07, 0.40), (0.07, 0.11, 0.40), (0.04, 0.11, 0.405), (0, 0.11, 0.405)],
        tring(0.47, 0.03, 0.17, 0.15, 0.13),             # R1 hips / lower belly
        tring(0.545, 0.0, 0.195, 0.22, 0.11),            # R2 pot belly
        tring(0.615, -0.02, 0.165, 0.17, 0.15),          # R3 upper belly
        tring(0.67, -0.04, 0.14, 0.10, 0.20),            # R4 narrow chest, hump
        tring(0.725, -0.07, 0.15, 0.08, 0.20),           # R5 sloped shoulders, hunched back
        tring(0.755, -0.10, 0.085, 0.06, 0.08),          # R6 neck
        # R7 jaw underside
        [(0, -0.235, 0.77), (0.07, -0.225, 0.775), (0.125, -0.155, 0.785), (0.13, -0.07, 0.79),
         (0.11, 0.0, 0.79), (0.08, 0.035, 0.785), (0.04, 0.05, 0.78), (0, 0.05, 0.78)],
        # R8 mouth: grin corners up
        [(0, -0.255, 0.83), (0.075, -0.25, 0.832), (0.145, -0.175, 0.855), (0.16, -0.08, 0.85),
         (0.15, 0.02, 0.84), (0.12, 0.07, 0.83), (0.06, 0.09, 0.83), (0, 0.09, 0.83)],
        # R9 nose tip (drooping) and cheek
        [(0, -0.35, 0.845), (0.035, -0.30, 0.865), (0.11, -0.19, 0.88), (0.16, -0.09, 0.885),
         (0.16, 0.03, 0.885), (0.13, 0.09, 0.88), (0.065, 0.115, 0.88), (0, 0.12, 0.88)],
        # R10 eyes / nose bridge
        [(0, -0.25, 0.94), (0.04, -0.23, 0.94), (0.10, -0.17, 0.935), (0.16, -0.09, 0.93),
         (0.165, 0.04, 0.93), (0.14, 0.10, 0.94), (0.07, 0.13, 0.94), (0, 0.135, 0.94)],
        # R11 heavy brow
        [(0, -0.24, 0.98), (0.055, -0.255, 0.985), (0.12, -0.215, 0.975), (0.155, -0.10, 0.99),
         (0.155, 0.04, 0.99), (0.13, 0.10, 0.99), (0.07, 0.13, 0.99), (0, 0.135, 0.99)],
        # R12 dome
        [(0, -0.17, 1.05), (0.05, -0.165, 1.05), (0.10, -0.13, 1.05), (0.125, -0.07, 1.055),
         (0.125, 0.03, 1.055), (0.10, 0.08, 1.05), (0.05, 0.10, 1.05), (0, 0.10, 1.05)],
        # R13 crown
        [(0, -0.09, 1.095), (0.03, -0.09, 1.095), (0.06, -0.07, 1.095), (0.07, -0.03, 1.10),
         (0.07, 0.02, 1.10), (0.055, 0.05, 1.095), (0.03, 0.06, 1.095), (0, 0.06, 1.095)],
    ]
    HY = -0.07                                        # the head sits forward of the chest (hunch)
    rings = rings[:7] + [[(x, y + HY, z) for x, y, z in r] for r in rings[7:]]
    R = [ring(bm, r) for r in rings]
    bands = [bridge(bm, R[i], R[i + 1]) for i in range(len(R) - 1)]
    ladder(bm, R[-1])
    bot = ladder(bm, R[0], flip=True)
    recalc_normals(bm)

    # legs out of the crotch's outer quad: thigh, knee forward, shin back, ankle, heel block
    leg = Limb(bm, [bot[2]], (0, 0, -1))
    rs = leg.run([((0.13, -0.04, 0.335), 0.058, 0.074),
                  ((0.165, -0.12, 0.235), 0.045, 0.052),
                  ((0.155, -0.06, 0.145), 0.036, 0.044),
                  ((0.135, 0.0, 0.08), 0.028, 0.034),
                  ((0.13, 0.01, 0.03), 0.04, 0.048)])
    for v in {v for f in leg.faces for v in f.verts}:
        v.co.z = 0.0
    front = min(rs[-1]['sides'], key=lambda f: f.calc_center_median().y)
    toe = extrude(bm, [front])
    cx = centre(toe['verts']).x
    for v in toe['verts']:
        v.co.y -= 0.13
        v.co.x = cx + (v.co.x - cx) * 1.45
        if v.co.z > 0.01:
            v.co.z = 0.045

    # arms out of the shoulder band's side quad: shoulder, upper arm, elbow, forearm, wrist, palm, fingers
    arm = Limb(bm, [bands[4][3]], (1, 0, 0))
    rs = arm.run([((0.19, -0.05, 0.668), 0.04, 0.042),
                  ((0.235, -0.035, 0.575), 0.032, 0.036),
                  ((0.255, -0.02, 0.48), 0.027, 0.03),
                  ((0.265, -0.06, 0.38), 0.033, 0.036),
                  ((0.27, -0.095, 0.29), 0.021, 0.026),
                  ((0.275, -0.12, 0.225), 0.026, 0.046),
                  ((0.28, -0.145, 0.155), 0.02, 0.042)])
    palm = rs[-2]
    tf = min(palm['sides'], key=lambda f: f.calc_center_median().y)
    th = extrude(bm, [tf])
    scale(th['verts'], 0.7)
    move(th['verts'], (-0.014, -0.04, -0.035))

    # ears out of the eye/brow band's side quad: long, horizontal, pointed, flat to the front
    ear = Limb(bm, [bands[10][3]], (1, 0, 0))
    ear.run([((0.20, -0.09, 0.965), 0.035, 0.03),
             ((0.28, -0.07, 0.985), 0.046, 0.014),
             ((0.35, -0.05, 1.0), 0.028, 0.01),
             ((0.41, -0.03, 1.02), 0.006, 0.004)])
    snap_seam(bm, 1e-6)
    return object_from_bm('body', bm)


def long_edge(bm, a, b):
    """The limb edge running from section a toward section b nearest their midpoint; near = its end at a."""
    a, b = V(a), V(b)
    m, d = (a + b) / 2, (b - a).normalized()
    cand = [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized().dot(d)) > 0.6]
    e = min(cand, key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2 - m).length)
    return e, min(e.verts, key=lambda v: (v.co - a).length)


def edge_between(bm, p, q):
    v, w = vert_near(bm, p), vert_near(bm, q)
    return next(e for e in v.link_edges if e.other_vert(v) == w), v


LEG = [(0.105, 0.0225, 0.40), (0.13, -0.04, 0.335), (0.165, -0.12, 0.235), (0.155, -0.06, 0.145), (0.135, 0.0, 0.08)]
ARM = [(0.155, -0.03, 0.70), (0.19, -0.05, 0.668), (0.235, -0.035, 0.575), (0.255, -0.02, 0.48), (0.265, -0.06, 0.38),
       (0.27, -0.095, 0.29)]
EYE = (0.079, -0.2875, 0.959)
META['keep_valleys'] = lambda c: abs(c[0] - EYE[0]) < 0.045 and abs(c[2] - EYE[2]) < 0.04 and c[1] < -0.22


def stage2(k, body):
    bm = edit(body)
    cuts = [('loop', 'hip root loop: the thigh swings from here', LEG[0], LEG[1], 0.45),
            ('loop', 'knee loop above the bend', LEG[1], LEG[2], 0.72),
            ('loop', 'knee loop below the bend', LEG[2], LEG[3], 0.3),
            ('loop', 'ankle loop: the foot pivots', LEG[3], LEG[4], 0.7),
            ('loop', 'shoulder loop: the deltoid bend', ARM[1], ARM[2], 0.35),
            ('loop', 'elbow loop above the bend', ARM[2], ARM[3], 0.72),
            ('loop', 'elbow loop below the bend', ARM[3], ARM[4], 0.3)]
    for kind, why, a, b, t in cuts:
        with k.topo(bm, kind, why):
            e, nv = long_edge(bm, a, b)
            loopcut(bm, e, t, near=nv)
    R = lambda z, yc, a, df, db: tring(z, yc, a, df, db)
    r5, r6 = R(0.725, -0.07, 0.15, 0.08, 0.20), R(0.755, -0.10, 0.085, 0.06, 0.08)
    with k.topo(bm, 'loop', 'neck loop: the head nods without collapsing the neck'):
        e, nv = edge_between(bm, r5[5], r6[5])
        loopcut(bm, e, 0.5, near=nv)
    r1, r2 = R(0.47, 0.03, 0.17, 0.15, 0.13), R(0.545, 0.0, 0.195, 0.22, 0.11)
    with k.topo(bm, 'loop', 'waist loop: the belt line under the pot belly (colour border)'):
        e, nv = edge_between(bm, r1[3], r2[3])
        belt = loopcut(bm, e, 0.3, near=nv)
    with k.topo(bm, 'loop', 'mouth loop: the lip line of the wide grin'):
        e, nv = edge_between(bm, (0.13, -0.14, 0.79), (0.16, -0.15, 0.85))
        mouth = loopcut(bm, e, 0.55, near=nv)
    with k.topo(bm, 'inset', 'eye socket under the brow'):
        sock = inset(bm, [face_near(bm, EYE)], 0.28, 0.0)
    # vertex moves
    for v in mouth:                       # the grin: the lip line dents in at the front, corners tucked up
        if v.co.y < -0.2:
            v.co.y += 0.018 if v.co.x < 0.1 else 0.012
            if v.co.x > 0.1:
                v.co.z += 0.012
    for v in sock[0].verts:               # the socket dents in
        v.co += sock[0].normal * -0.012
    for v in belt:                        # the belt line tucks in under the belly
        v.co.x *= 0.97; v.co.y = v.co.y * 0.97
    commit(body, bm)


PAL = {'skin': '#6aa84f', 'belly': '#9ccc7a', 'belt': '#4a3222', 'cloth': '#7a5a3a', 'fang': '#efe6cf',
       'eye': '#f2d23c'}
ZB = 0.4925                                        # the waist loop (stage 2): belt line / colour border


def body_rule(c, n, i):
    if 0.797 < c.z < 0.836 and c.y < -0.26 and abs(c.x) < 0.14 and n.y < 0.2:
        return 'belt'                              # the dark grin line
    if 0.395 <= c.z < ZB and abs(c.x) < 0.2:
        return 'cloth'                             # the loin wrap under the belt
    if ZB < c.z < 0.672 and n.y < -0.45 and abs(c.x) < 0.15:
        return 'belly'
    return 'skin'


def spike(bm, base, tip, r):
    """A four-sided claw / fang: a square base (buried) and a point."""
    base, tip = V(base), V(tip)
    d = (tip - base).normalized()
    u = d.cross(V(0, 0, 1) if abs(d.z) < 0.9 else V(1, 0, 0)).normalized()
    w = d.cross(u)
    b = ring(bm, [base + (u * math.cos(a) + w * math.sin(a)) * r for a in (0.3, 1.87, 3.44, 5.01)])
    t = bm.verts.new(tip)
    for i in range(4):
        bm.faces.new([b[i], b[(i + 1) % 4], t])
    bm.faces.new(list(reversed(b)))


def stage3(k, body):
    paint(body, PAL, body_rule)
    bm = edit(body)
    ev = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ev)
    pieces = []

    # eyes: a low lens in the socket, the dark pupil ring in its own loop
    f = face_near(bm, EYE)
    c0, n = f.calc_center_median(), f.normal.copy()
    u = n.cross(V(0, 0, 1)).normalized(); w = u.cross(n)
    eb = bmesh.new()
    rim = ring(eb, [c0 + n * 0.011 + (u * math.cos(a) + w * math.sin(a)) * 0.024 for a in [i * math.pi / 3 for i in range(6)]])
    mid = ring(eb, [c0 + n * 0.018 + (u * math.cos(a) + w * math.sin(a)) * 0.012 for a in [i * math.pi / 3 for i in range(6)]])
    ap, bk = eb.verts.new(c0 + n * 0.021), eb.verts.new(c0 - n * 0.005)
    bridge(eb, rim, mid, closed=True)
    for i in range(6):
        eb.faces.new([mid[i], mid[(i + 1) % 6], ap]); eb.faces.new([rim[(i + 1) % 6], rim[i], bk])
    eye = object_from_bm('eye', eb, mirror=True)
    def eye_rule(c, nn, i, c0=c0, n=n):
        q = c - c0
        return 'belt' if (q - n * q.dot(n)).length < 0.011 and q.dot(n) > 0.012 else 'eye'
    paint(eye, PAL, eye_rule)
    pieces.append(eye)

    # fangs: two hanging from the upper lip over the grin, two small ones from the corners
    fb = bmesh.new()
    spike(fb, (0.06, -0.31, 0.838), (0.058, -0.318, 0.782), 0.011)
    spike(fb, (0.115, -0.25, 0.848), (0.118, -0.262, 0.812), 0.008)
    fangs = object_from_bm('fangs', fb, mirror=True)
    paint(fangs, PAL, lambda c, nn, i: 'fang')
    pieces.append(fangs)

    # claws: two on the finger block, one on the thumb, three on each foot
    cb = bmesh.new()
    fe = face_near(bm, (0.28, -0.145, 0.155), n=(0, 0, -1))
    fc = fe.calc_center_median()
    for dy in (-0.022, 0.02):
        p = fc + V(0, dy, 0)
        spike(cb, p + V(0, 0, 0.008), p + V(0, -0.02, -0.04), 0.009)
    tf = face_near(bm, (0.258, -0.19, 0.222), n=(0, -1, 0))
    tc, tn = tf.calc_center_median(), tf.normal
    spike(cb, tc - tn * 0.006, tc + V(0, -0.03, -0.02), 0.008)
    te = face_near(bm, (0.13, -0.17, 0.022), n=(0, -1, 0))
    tfc = te.calc_center_median()
    for dx in (-0.036, 0.0, 0.036):
        p = V(tfc.x + dx, tfc.y, 0.016)
        spike(cb, p + V(0, 0.008, 0), p + V(dx * 0.3, -0.035, -0.008), 0.009)
    claws = object_from_bm('claws', cb, mirror=True)
    paint(claws, PAL, lambda c, nn, i: 'fang')
    pieces.append(claws)

    # belt: a band that rests on the waist loop, plus a chunky buckle on the seam
    lv = sorted([v.co.copy() for v in bm.verts if abs(v.co.z - ZB) < 0.002 and v.co.x < 0.22],
                key=lambda p: math.atan2(p.x, -(p.y - 0.015)))
    bb = bmesh.new()
    secs = []
    for j, p in enumerate(lv):
        sec = []
        for dz, off in ((0.03, 0.022), (-0.03, 0.022), (-0.03, 0.003), (0.03, 0.003)):
            loc, nrm, _, _ = tree.find_nearest(p + V(0, 0, dz))
            q = loc + nrm * off
            if j in (0, len(lv) - 1):
                q.x = 0.0
            sec.append(q)
        secs.append(ring(bb, sec))
    for s0, s1 in zip(secs, secs[1:]):
        bridge(bb, s0, s1, closed=True)
    fy = secs[0][0].co.y
    bx = [(0, fy + 0.006, ZB - 0.04), (0, fy - 0.016, ZB - 0.04), (0, fy - 0.016, ZB + 0.04), (0, fy + 0.006, ZB + 0.04)]
    box = ring(bb, bx) + ring(bb, [(0.045, y, z) for _, y, z in bx])
    for q in ([4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]):
        bb.faces.new([box[i] for i in q])
    belt = object_from_bm('belt', bb, mirror=True)
    paint(belt, PAL, lambda c, nn, i: 'fang' if c.y < fy - 0.012 and c.x < 0.046 and abs(c.z - ZB) < 0.041 else 'belt')
    pieces.append(belt)

    # loincloth: tattered front and back flaps tucked under the belt
    by = secs[-1][0].co.y                          # the belt's outer surface on the back seam
    for yt, sag, bot, t in ((fy + 0.012, (0.0, -0.006, -0.02), (0.305, 0.35, 0.315), 0.010),
                            (by - 0.012 - 0.013, (0.0, 0.055, 0.062), (0.345, 0.375, 0.35), 0.013)):
        lb = bmesh.new()
        xs = (0.0, 0.03, 0.056)
        zs = [[ZB + (0.012 if yt > 0 else -0.005)] * 3, [0.40] * 3, list(bot)]
        rows = [[(x, yt + sag[r], zs[r][j]) for j, x in enumerate(xs)] for r in range(3)]
        F = [ring(lb, r) for r in rows]
        B = [ring(lb, [(x, y + t, z) for x, y, z in r]) for r in rows]
        for i in range(2):
            bridge(lb, F[i], F[i + 1]); bridge(lb, B[i + 1], B[i])
            lb.faces.new([F[i][2], F[i + 1][2], B[i + 1][2], B[i][2]])
        bridge(lb, B[0], F[0]); bridge(lb, F[2], B[2])
        loin = object_from_bm('loin_front' if yt < 0 else 'loin_back', lb, mirror=True)   # one flap per object:
        paint(loin, PAL, lambda c, nn, i: 'cloth')                                          # one contact per belt side
        pieces.append(loin)
    bm.free(); ev.free()
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('hips', (0, 0.03, 0.40), (0, 0.01, 0.53), None),
        ('spine', (0, 0.01, 0.53), (0, -0.03, 0.66), 'hips', True),
        ('chest', (0, -0.03, 0.66), J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['crown'], 'neck', True),
        ('ear.L', J['earL'], J['eartipL'], 'head'),
        ('shoulder.L', (0.06, -0.06, 0.71), (0.17, -0.045, 0.69), 'chest'),
        ('upperarm.L', ARM[1], ARM[3], 'shoulder.L'),
        ('forearm.L', ARM[3], ARM[5], 'upperarm.L', True),
        ('hand.L', ARM[5], J['handL'], 'forearm.L', True),
        ('thigh.L', (0.105, 0.02, 0.42), J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    # the waist belongs to the pelvis: heat gave the thigh bones the flanks up to the belt, so the
    # belt band (which borrows these weights) folded when a leg swung
    thighs = {body.vertex_groups[n].index for n in ('thigh.L', 'thigh.R') if n in body.vertex_groups}
    hips = body.vertex_groups['hips']
    for v in body.data.vertices:
        if v.co.z > 0.445 and abs(v.co.x) < 0.19:
            for g in v.groups:
                if g.group in thighs:
                    g.weight = 0.0
            if sum(g.weight for g in v.groups) < 1e-4:
                hips.add([v.index], 1.0, 'REPLACE')
    for p in pieces:
        if p.name.startswith(('piece_loin', 'piece_belt')):
            bind(p, rig, bone='hips')        # belt + flaps: rigid to the pelvis (the waist skin is hips-only)
        else:
            bind(p, rig, body=body)
    # idle: breathe, look left and right, ears twitch, fingers fidget
    clip(rig, 'idle', {
        1: {},
        12: {'chest': (3, 0, 0), 'head': (0, 22, 0), 'ear.L': (0, 0, 6), 'hand.L': (12, 0, 0)},
        24: {'chest': (0, 0, 0), 'head': (6, 0, 0), 'ear.R': (0, 0, -6), 'hand.R': (12, 0, 0)},
        36: {'chest': (3, 0, 0), 'head': (0, -22, 0), 'ear.L': (0, 0, -4), 'hand.L': (-8, 0, 0)},
        48: {}})
    # move: a sneaky crouched walk, chest pitched forward, arms counter-swinging
    lean = {'chest': (8, 0, 0), 'head': (-6, 0, 0)}
    def step(tl, sl, tr, sr, al, tw):
        return dict(lean, **{'thigh.L': (tl, 0, 0), 'shin.L': (sl, 0, 0), 'thigh.R': (tr, 0, 0), 'shin.R': (sr, 0, 0),
                             'upperarm.L': (al, 0, 0), 'upperarm.R': (-al, 0, 0), 'hips': (0, tw, 0)})
    clip(rig, 'move', {1: step(20, -10, -15, -20, -12, 4), 9: step(0, -5, 5, -40, 0, 0),
                       17: step(-15, -20, 20, -10, 12, -4), 25: step(5, -40, 0, -5, 0, 0),
                       33: step(20, -10, -15, -20, -12, 4)})
    # attack: wind up, swipe the left claw across, follow through
    clip(rig, 'attack', {
        1: {},
        8: {'upperarm.L': (-40, 0, 0), 'forearm.L': (35, 0, 0), 'chest': (-4, 12, 0), 'head': (0, -6, 0),
            'thigh.L': (10, 0, 0), 'shin.L': (-12, 0, 0)},
        14: {'upperarm.L': (65, 0, 0), 'forearm.L': (10, 0, 0), 'hand.L': (15, 0, 0), 'chest': (12, -14, 0),
             'head': (4, 8, 0), 'thigh.L': (18, 0, 0), 'shin.L': (-18, 0, 0)},
        20: {'upperarm.L': (45, 0, 0), 'forearm.L': (30, 0, 0), 'chest': (8, -8, 0), 'thigh.L': (12, 0, 0),
             'shin.L': (-14, 0, 0)},
        28: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
