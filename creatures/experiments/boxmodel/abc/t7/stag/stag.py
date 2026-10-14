import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='stag', model='opus',
            keep_valleys=lambda c: c.x > 0.05 and -0.86 < c.y < -0.74 and 1.22 < c.z < 1.37)   # the eye socket

# the skeleton the model is built on (x >= 0 half; -Y forward, Z up)
J = dict(
    hips=(0.0, 0.46, 0.84), spine=(0.0, 0.05, 0.84), chest=(0.0, -0.30, 0.86),
    neck=(0.0, -0.44, 0.96), neck2=(0.0, -0.56, 1.14), head=(0.0, -0.64, 1.30), snout=(0.0, -0.98, 1.22),
    shoulder=(0.12, -0.30, 0.74), elbow=(0.12, -0.26, 0.45), knee=(0.12, -0.30, 0.25),
    ffet=(0.12, -0.31, 0.09), ftoe=(0.12, -0.33, 0.0),
    hipL=(0.13, 0.40, 0.78), stifle=(0.125, 0.33, 0.46), hock=(0.125, 0.49, 0.32),
    hfet=(0.125, 0.47, 0.09), htoe=(0.125, 0.45, 0.0),
    ear=(0.14, -0.62, 1.32), eartip=(0.31, -0.58, 1.41),
    tail=(0.0, 0.62, 0.94), tailtip=(0.0, 0.70, 0.80),
)

T = (0.12, 0.38, 0.66, 0.90)
BEAM = [((0.095, -0.70, 1.45), 0.032), ((0.17, -0.67, 1.52), 0.026),
        ((0.26, -0.63, 1.60), 0.021), ((0.29, -0.66, 1.71), 0.011)]


def sec(top, bot, xs, ts=T):
    """A half section: top seam vertex, four side vertices, bottom seam vertex."""
    pts = [(0.0, top[0], top[1])]
    for t, x in zip(ts, xs):
        pts.append((x, top[0] + (bot[0] - top[0]) * t, top[1] + (bot[1] - top[1]) * t))
    pts.append((0.0, bot[0], bot[1]))
    return pts


# rear -> nose: (name, top (y, z), bottom (y, z), half widths at T)
SECS = [
    ('rump',   (0.64, 0.92), (0.55, 0.64), (0.06, 0.10, 0.09, 0.04)),
    ('hip',    (0.48, 0.99), (0.50, 0.60), (0.11, 0.205, 0.195, 0.10)),
    ('flank',  (0.26, 0.97), (0.26, 0.63), (0.11, 0.20, 0.185, 0.095)),
    ('waist',  (0.02, 0.96), (0.02, 0.57), (0.10, 0.185, 0.175, 0.08)),
    ('ribs',   (-0.20, 1.00), (-0.20, 0.50), (0.11, 0.215, 0.20, 0.07)),
    ('shldr',  (-0.38, 1.05), (-0.38, 0.52), (0.10, 0.195, 0.175, 0.06)),
    ('neck0',  (-0.44, 1.12), (-0.54, 0.72), (0.11, 0.17, 0.165, 0.10)),
    ('neck1',  (-0.52, 1.25), (-0.68, 0.95), (0.09, 0.135, 0.13, 0.08)),
    ('occ',    (-0.58, 1.36), (-0.72, 1.12), (0.075, 0.10, 0.095, 0.06)),
    ('poll',   (-0.65, 1.39), (-0.77, 1.12), (0.08, 0.11, 0.10, 0.065)),
    ('brow',   (-0.75, 1.38), (-0.81, 1.14), (0.088, 0.115, 0.095, 0.06)),
    ('stop',   (-0.86, 1.33), (-0.88, 1.16), (0.062, 0.07, 0.066, 0.052)),
    ('muzzle', (-1.00, 1.275), (-0.99, 1.165), (0.046, 0.05, 0.05, 0.042)),
]


def quad(a, b, c, d):
    fs = set(a.link_faces) & set(b.link_faces) & set(c.link_faces) & set(d.link_faces)
    assert len(fs) == 1, 'quad: no single face on these corners'
    return fs.pop()


def seg(bm, face, c, u, hu, v, hv):
    """Extrude one face and place its four new corners on the rectangle
    c +- u*hu +- v*hv; each corner keeps its side (sign along u and v)."""
    old = face.calc_center_median().copy()
    u, v = V(u).normalized(), V(v).normalized()
    r = extrude(bm, [face])
    for w in r['verts']:
        d = w.co - old
        w.co = V(c) + u * (hu if d.dot(u) > 0 else -hu) + v * (hv if d.dot(v) > 0 else -hv)
    return r


def leg(bm, face, rows):
    """rows: (x, y, z, half depth (y), half width (x)) from the root down."""
    r = None
    for x, y, z, hd, hw in rows:
        r = seg(bm, face, (x, y, z), (0, 1, 0), hd, (1, 0, 0), hw)
        face = r['faces'][0]
    return r


def stage1(k):
    bm = bmesh.new()
    R = [ring(bm, sec(t, b, xs)) for _, t, b, xs in SECS]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    cap(bm, R[0])
    cap(bm, list(reversed(R[-1])))
    I = {n: i for i, (n, *_) in enumerate(SECS)}

    # forelegs from the ribs->shoulder lower-side quad; the elbow tucked behind the chest
    x, y, z = J['elbow']
    leg(bm, quad(R[I['ribs']][3], R[I['ribs']][4], R[I['shldr']][3], R[I['shldr']][4]), [
        (x, y, z, 0.07, 0.045),
        (0.12, -0.30, 0.25, 0.042, 0.032),
        (0.12, -0.31, 0.09, 0.03, 0.026),
        (0.12, -0.32, 0.05, 0.04, 0.03),
        (0.12, -0.335, 0.0, 0.045, 0.032),
    ])
    # hind legs from the flank->hip lower-side quad: stifle forward, hock back
    leg(bm, quad(R[I['flank']][3], R[I['flank']][4], R[I['hip']][3], R[I['hip']][4]), [
        (0.125, 0.33, 0.46, 0.08, 0.045),
        (0.125, 0.49, 0.32, 0.045, 0.03),
        (0.125, 0.47, 0.09, 0.03, 0.026),
        (0.125, 0.46, 0.05, 0.04, 0.03),
        (0.125, 0.45, 0.0, 0.045, 0.032),
    ])

    # ears: leaf, out and up from the occiput->poll side-upper quad; flat faces forward
    ax = (V(J['eartip']) - V(J['ear'])).normalized()
    up = V((-ax.z, 0, ax.x))
    f = quad(R[I['occ']][2], R[I['occ']][3], R[I['poll']][2], R[I['poll']][3])
    for c, th, w in (((0.16, -0.62, 1.34), 0.018, 0.035), ((0.24, -0.60, 1.38), 0.016, 0.055),
                     ((0.31, -0.58, 1.41), 0.006, 0.012)):
        f = seg(bm, f, c, (0, 1, 0), th, up, w)['faces'][0]

    # antlers: main beam from the poll->brow top quad, with brow and trez tines forward
    f = quad(R[I['poll']][1], R[I['poll']][2], R[I['brow']][1], R[I['brow']][2])
    beam = []
    for c, h in BEAM:
        r = seg(bm, f, c, (0, 1, 0), h, (1, 0, 0), h)
        f = r['faces'][0]
        beam.append(r)
    for bi, pts in ((1, (((0.135, -0.735, 1.49), 0.018), ((0.15, -0.84, 1.50), 0.008))),
                    (2, (((0.215, -0.715, 1.57), 0.018), ((0.23, -0.80, 1.62), 0.007)))):
        tf = min(beam[bi]['sides'], key=lambda q: q.calc_center_median().y)
        ax = (V(BEAM[bi][0]) - V(BEAM[bi - 1][0])).normalized()      # along the beam
        ac = ax.cross(V((0, 1, 0))).normalized()                        # across it
        for c, h in pts:
            tf = seg(bm, tf, c, ac, h, ax, h)['faces'][0]

    snap_seam(bm)
    ob = object_from_bm('body', bm)
    if True:  # dump self-intersecting face pairs (diagnostic only)
        from mathutils.bvhtree import BVHTree
        eb = evaluated_bm(ob); eb.faces.ensure_lookup_table()
        t = BVHTree.FromBMesh(eb)
        for i, j in t.overlap(t):
            if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
                say('HIT', [round(c, 3) for c in eb.faces[i].calc_center_median()],
                    [round(c, 3) for c in eb.faces[j].calc_center_median()])
    return ob



def cut(bm, a, b, t):
    """Loop cut across the ring of the edge a-b (found by its end points), t from a."""
    va, vb = vert_near(bm, a), vert_near(bm, b)
    e = next(e for e in va.link_edges if e.other_vert(va) is vb)
    return loopcut(bm, e, t=t, near=va)


FKNEE, FELB, FFET = (0.152, -0.342, 0.25), (0.165, -0.33, 0.45), (0.146, -0.34, 0.09)
HHOCK, HSTIF, HFET = (0.155, 0.445, 0.32), (0.17, 0.25, 0.46), (0.151, 0.44, 0.09)


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'foreleg wrist (knee): a loop above and below it so it bends'):
        cut(bm, FKNEE, FELB, 0.2)
        cut(bm, FKNEE, FFET, 0.2)
    with k.topo(bm, 'loop', 'hind hock: a loop above and below it so it bends'):
        cut(bm, HHOCK, HSTIF, 0.2)
        cut(bm, HHOCK, HFET, 0.2)
    with k.topo(bm, 'loop', 'elbow: a loop above it, the upper arm leaves the chest'):
        cut(bm, FELB, (0.175, -0.38, 0.70), 0.3)
    with k.topo(bm, 'loop', 'neck: two loops between the base, mid and top rings so the neck bends without collapsing'):
        cut(bm, (0, -0.44, 1.12), (0, -0.52, 1.25), 0.5)
        cut(bm, (0, -0.52, 1.25), (0, -0.58, 1.36), 0.5)
    with k.topo(bm, 'inset', 'eye socket in the brow->stop upper-side face, under the brow'):
        f = face_near(bm, (0.095, -0.80, 1.30), n=(1, 0, 0.3))
        inset(bm, [f], 0.3, depth=-0.012)
    # the stop: a step down from the forehead to the nasal plane
    for v in verts_where(bm, lambda c: abs(c.y + 0.86) < 0.012 and c.z > 1.29):
        v.co.z -= 0.014
    # hooves: the sole flares a little and the toe leads, a wedge not a post
    for cx, cy in ((0.12, -0.335), (0.125, 0.45)):
        sole = verts_where(bm, lambda c: c.z < 1e-3 and abs(c.y - cy) < 0.08)
        scale(sole, (1.2, 1.25, 1.0), pivot=(cx, cy, 0.0))
        move(sole, (0, -0.012, 0))
    commit(body, bm)


PAL = {'coat': '#8a5a3a', 'mane': '#6a4630', 'cream': '#d9c3a0', 'antler': '#d8c8a8',
       'hoof': '#231a16', 'eye': '#111111'}
TINES = [(BEAM[1][0], (0.15, -0.84, 1.50)), (BEAM[2][0], (0.23, -0.80, 1.62))]


def _sd(p, a, b):
    p, a, b = V(p), V(a), V(b)
    d = b - a
    t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared))
    return (a + d * t - p).length


def is_antler(c):
    if c.z < 1.395:
        return False
    segs = [(BEAM[i][0], BEAM[i + 1][0]) for i in range(3)] + TINES
    return min(_sd(c, a, b) for a, b in segs) < 0.045


def body_rule(c, n, i):
    if is_antler(c):
        return 'antler'
    if c.z < 0.052:
        return 'hoof'
    if c.y < -0.975:
        return 'hoof'                                   # black nose pad
    if c.y > 0.5 and n.y > 0.55:
        return 'cream'                                  # rump patch (the rear plane)
    if c.y < -0.70 and n.z < -0.35 and c.z > 1.05:
        return 'cream'                                  # pale jaw line
    if n.z < -0.6 and -0.2 < c.y < 0.45 and c.z > 0.5:
        return 'cream'                                  # belly
    return 'coat'


def half_tube(bm, rings_out, rings_in, closed_ends=True):
    A = [ring(bm, r) for r in rings_out]
    B = [ring(bm, r) for r in rings_in]
    for a, b in zip(A, A[1:]):
        bridge(bm, a, b)
    for a, b in zip(B, B[1:]):
        bridge(bm, b, a)
    bridge(bm, B[0], A[0])
    bridge(bm, A[-1], B[-1])


def off(pts, ds):
    """Push a half section's points away from its seam axis by ds[i]."""
    m = (V(pts[0]) + V(pts[-1])) / 2
    out = []
    for p, d in zip(pts, ds):
        q = V(p); w = q - m
        out.append(tuple(q + w.normalized() * d))
    return out


def mix(a, b, t):
    return [tuple(V(p).lerp(V(q), t)) for p, q in zip(a, b)]


def stage3(k, body):
    paint(body, PAL, body_rule)
    S = {n: sec(t, b, xs) for n, t, b, xs in SECS}
    pieces = []

    # neck mane: a shaggy dark sleeve from the withers to behind the ears, V bib at the throat
    rs = [S['neck0'], S['neck0'], mix(S['neck0'], S['neck1'], 0.5), S['neck1'], mix(S['neck1'], S['occ'], 0.35)]
    rs[0] = mix(S['shldr'], S['neck0'], 0.6)
    outer_d = [(0.05, 0.04, 0.03, 0.035, 0.05, 0.06), (0.07, 0.05, 0.03, 0.04, 0.06, 0.07),
               (0.05, 0.04, 0.025, 0.035, 0.05, 0.06), (0.06, 0.045, 0.025, 0.03, 0.045, 0.05),
               (0.045, 0.04, 0.035, 0.035, 0.04, 0.045)]
    bm = bmesh.new()
    outs = [off(r, d) for r, d in zip(rs, outer_d)]
    ins = [off(r, [-0.012 if j == 0 else 0.015] * 6) for j, r in enumerate(rs)]   # seated at the withers only
    b0 = list(outs[0][-1]); outs[0][-1] = (0.0, b0[1] + 0.03, b0[2] - 0.13)     # the V bib point
    b1 = list(outs[1][-1]); outs[1][-1] = (0.0, b1[1] - 0.01, b1[2] - 0.05)
    half_tube(bm, outs, ins)
    mane = object_from_bm('mane', bm)
    paint(mane, PAL, lambda c, n, i: 'mane')
    pieces.append(mane)

    # eyes: a hexagonal lens seated in the socket, proud of its floor
    me = body.data
    cand = [p for p in me.polygons if (p.center - V((0.095, -0.80, 1.30))).length < 0.035 and p.normal.x > 0.3]
    f = min(cand, key=lambda p: p.area)
    c, n = f.center.copy(), f.normal.copy()
    t1 = n.cross(V((0, 0, 1))).normalized(); t2 = n.cross(t1)
    hexa = [t1 * math.cos(a) + t2 * math.sin(a) for a in [i * math.pi / 3 for i in range(6)]]
    bm = bmesh.new()
    back = ring(bm, [c - n * 0.003 + h * 0.012 for h in hexa])
    front = ring(bm, [c + n * 0.014 + h * 0.01 for h in hexa])
    bridge(bm, back, front, closed=True)
    cap(bm, list(reversed(back))); cap(bm, front)
    eye = object_from_bm('eye', bm)
    paint(eye, PAL, lambda c, n, i: 'eye')
    pieces.append(eye)

    # antler crowns: three prongs at the top of each beam
    bm = bmesh.new()
    for base, apex, h in (((0.29, -0.66, 1.70), (0.30, -0.69, 1.76), 0.007),
                          ((0.283, -0.645, 1.665), (0.355, -0.63, 1.72), 0.006),
                          ((0.271, -0.630, 1.64), (0.27, -0.57, 1.70), 0.006)):
        a = (V(apex) - V(base)).normalized()
        u = a.cross(V((0, 1, 0)) if abs(a.y) < 0.8 else V((1, 0, 0))).normalized(); w = a.cross(u)
        sq = ring(bm, [V(base) + (u * sx + w * sy) * h for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
        tip = bm.verts.new(V(apex))
        cap(bm, list(reversed(sq)))
        for i in range(4):
            bm.faces.new([sq[i], sq[(i + 1) % 4], tip])
    crown = object_from_bm('crown', bm)
    paint(crown, PAL, lambda c, n, i: 'antler')
    pieces.append(crown)

    # tail: short hanging wedge, dark on top, cream under
    bm = bmesh.new()
    T3 = [sec((0.56, 0.93), (0.56, 0.84), (0.03, 0.045, 0.045, 0.03)),
          sec((0.66, 0.92), (0.64, 0.82), (0.035, 0.05, 0.05, 0.03)),
          sec((0.72, 0.84), (0.68, 0.76), (0.03, 0.04, 0.04, 0.025)),
          sec((0.735, 0.74), (0.70, 0.70), (0.012, 0.018, 0.018, 0.01))]
    R3 = [ring(bm, r) for r in T3]
    for a, b in zip(R3, R3[1:]):
        bridge(bm, a, b)
    cap(bm, R3[0]); cap(bm, list(reversed(R3[-1])))
    tail = object_from_bm('tail', bm)
    paint(tail, PAL, lambda c, n, i: 'cream' if n.y < -0.2 or n.z < -0.5 else 'mane')
    pieces.append(tail)
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hips'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('neck', J['neck'], J['neck2'], 'spine'),
        ('neck2', J['neck2'], J['head'], 'neck', True),
        ('head', J['head'], J['snout'], 'neck2', True),
        ('ear.L', J['ear'], J['eartip'], 'head'),
        ('tail', J['tail'], J['tailtip'], 'hips'),
        ('upperarm.L', J['shoulder'], J['elbow'], 'spine'),
        ('forearm.L', J['elbow'], J['knee'], 'upperarm.L', True),
        ('cannon.L', J['knee'], J['ffet'], 'forearm.L', True),
        ('hoof.L', J['ffet'], J['ftoe'], 'cannon.L', True),
        ('thigh.L', J['hipL'], J['stifle'], 'hips'),
        ('shin.L', J['stifle'], J['hock'], 'thigh.L', True),
        ('hcannon.L', J['hock'], J['hfet'], 'shin.L', True),
        ('hhoof.L', J['hfet'], J['htoe'], 'hcannon.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)          # every piece borrows the skin under it: no drift
    # idle: grazing dip and an ear flick (bone-local +X tips a neck forward/down; on the head +X lifts the nose)
    graze = {'neck': (22, 0, 0), 'neck2': (12, 0, 0), 'head': (-8, 0, 0)}
    clip(rig, 'idle', {1: {}, 12: dict(graze), 22: dict(graze, **{'ear.L': (0, 0, 0)}),
                       26: dict(graze, **{'ear.L': (-30, 0, 0)}), 30: dict(graze),
                       40: {'ear.L': (0, 0, 0)}, 48: {}})
    # move: walk, diagonal pairs (fore L with hind R)
    def walk(a, flexF, flexH):
        return {'upperarm.L': (14 * a, 0, 0), 'upperarm.R': (-14 * a, 0, 0),
                'thigh.R': (12 * a, 0, 0), 'thigh.L': (-12 * a, 0, 0),
                'cannon.L': (flexF[0], 0, 0), 'cannon.R': (flexF[1], 0, 0),
                'hcannon.L': (flexH[0], 0, 0), 'hcannon.R': (flexH[1], 0, 0),
                'neck': (3 * abs(a), 0, 0)}
    clip(rig, 'move', {1: walk(1, (0, 0), (0, 0)), 9: walk(0, (0, -35), (22, 0)),
                       17: walk(-1, (0, 0), (0, 0)), 25: walk(0, (-35, 0), (0, 22)),
                       33: walk(1, (0, 0), (0, 0))})
    # attack: rear back, then drive the antlers down and forward
    back = {'neck': (-8, 0, 0), 'neck2': (-6, 0, 0), 'head': (10, 0, 0), 'upperarm.L': (8, 0, 0), 'upperarm.R': (8, 0, 0)}
    ram = {'neck': (30, 0, 0), 'neck2': (15, 0, 0), 'head': (-20, 0, 0), 'upperarm.L': (-10, 0, 0),
           'upperarm.R': (-10, 0, 0), 'thigh.L': (-12, 0, 0), 'thigh.R': (-12, 0, 0), 'spine': (-4, 0, 0)}
    clip(rig, 'attack', {1: {}, 10: back, 18: ram, 24: ram, 33: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
