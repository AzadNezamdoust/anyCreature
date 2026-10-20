import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from mathutils import Vector

META = dict(creature='boar', model='opus')
class _Valleys(str):
    """keep_valleys as a JSON-safe callable (META is written into the lock file)."""
    def __call__(self, c):
        return (c[1] < -0.69) or (abs(abs(c[0]) - 0.11) < 0.04 and abs(c[1] + 0.405) < 0.05 and abs(c[2] - 0.55) < 0.05)


META['keep_valleys'] = _Valleys('snout disc nostrils and eye sockets dent in')

# the skeleton the model is built on (x >= 0 half; Z up; faces -Y)
J = dict(
    hips=(0, 0.50, 0.62), spine=(0, 0.26, 0.66), chest=(0, 0.02, 0.70), neck=(0, -0.16, 0.64),
    head=(0, -0.30, 0.56), snout=(0, -0.70, 0.38), tail0=(0, 0.63, 0.645), tail1=(0, 0.69, 0.48),
    shoulder=(0.15, -0.07, 0.50), elbow=(0.155, -0.05, 0.24), wrist=(0.15, -0.085, 0.10), fhoof=(0.15, -0.10, 0.0),
    hipL=(0.13, 0.45, 0.52), stifle=(0.13, 0.41, 0.24), hock=(0.13, 0.48, 0.14), hhoof=(0.13, 0.435, 0.0),
)

# half sections, snout -> rump: y, top z, upper (x,z), side (x,z), low (x,z), belly (x,z), bottom z
SEC = [
    (-0.72, 0.43, (0.050, 0.42), (0.075, 0.38), (0.070, 0.33), (0.040, 0.300), 0.29),   # 0 snout disc
    (-0.67, 0.44, (0.048, 0.43), (0.068, 0.385), (0.062, 0.335), (0.035, 0.305), 0.30),  # 1 behind disc
    (-0.54, 0.50, (0.075, 0.495), (0.100, 0.44), (0.100, 0.34), (0.065, 0.285), 0.275),     # 2 muzzle
    (-0.45, 0.565, (0.085, 0.555), (0.120, 0.49), (0.125, 0.35), (0.085, 0.27), 0.26),    # 3 stop
    (-0.36, 0.64, (0.095, 0.62), (0.140, 0.54), (0.150, 0.36), (0.100, 0.26), 0.245),    # 4 brow
    (-0.25, 0.73, (0.105, 0.71), (0.165, 0.60), (0.175, 0.38), (0.110, 0.27), 0.26),     # 5 skull back / jowl
    (-0.13, 0.84, (0.095, 0.77), (0.200, 0.66), (0.200, 0.45), (0.125, 0.31), 0.30),     # 6 nape / front shoulder
    (-0.01, 0.91, (0.105, 0.82), (0.230, 0.70), (0.215, 0.44), (0.130, 0.31), 0.30),     # 7 hump
    (0.12, 0.88, (0.110, 0.805), (0.220, 0.68), (0.205, 0.45), (0.120, 0.33), 0.32),      # 8 ribs
    (0.26, 0.815, (0.105, 0.77), (0.190, 0.65), (0.175, 0.47), (0.100, 0.37), 0.36),     # 9 waist
    (0.38, 0.76, (0.100, 0.735), (0.175, 0.64), (0.170, 0.48), (0.095, 0.41), 0.40),     # 10 hip front
    (0.50, 0.725, (0.100, 0.705), (0.170, 0.62), (0.165, 0.48), (0.085, 0.42), 0.41),      # 11 haunch
    (0.60, 0.69, (0.080, 0.675), (0.130, 0.61), (0.120, 0.50), (0.060, 0.45), 0.44),      # 12 rump
]
TAIL = [((0, 0.625, 0.645), (0, 1, 0), 0.020), ((0, 0.655, 0.625), (0, 0.6, -0.8), 0.016),
        ((0, 0.68, 0.56), (0, 0.2, -1), 0.014), ((0, 0.69, 0.49), (0, 0.05, -1), 0.012)]
FRONT = [(J['elbow'], .060, .085), ((0.152, -0.07, 0.15), .042, .052), ((0.15, -0.085, 0.08), .032, .036),
         ((0.15, -0.095, 0.045), .045, .055), ((0.15, -0.10, 0.0), .050, .065)]
HIND = [((0.135, 0.44, 0.34), .065, .100), (J['stifle'], .050, .065), (J['hock'], .036, .045),
        ((0.13, 0.455, 0.075), .032, .036), ((0.13, 0.44, 0.045), .045, .055), ((0.13, 0.435, 0.0), .050, .065)]
EAR = [((0.13, -0.305, 0.73), .045, .016), ((0.155, -0.335, 0.80), .030, .011), ((0.175, -0.37, 0.87), .006, .004)]
PAL = dict(body='#6f5040', bristle='#3e2c24', snout='#b88e7e', tusk='#efe3c8', hoof='#2a201c', eye='#1a1414')
G = {}


def half(y, zt, u, s, l, b, zb):
    return [(0, y, zt), (u[0], y, u[1]), (s[0], y, s[1]), (l[0], y, l[1]), (b[0], y, b[1]), (0, y, zb)]


def tube(c, d, r, n=6):
    """half ring perpendicular to d, dorsal side first."""
    d = Vector(d).normalized(); X = Vector((1, 0, 0)); w = X.cross(d)
    out = []
    for i in range(n):
        a = math.pi * i / (n - 1)
        p = Vector(c) + X * r * math.sin(a) + w * r * math.cos(a)
        if i in (0, n - 1):
            p.x = 0.0
        out.append(tuple(p))
    return out


def quad(rows, i, j):
    s = set(rows[i][j].link_faces) & set(rows[i][j + 1].link_faces) & set(rows[i + 1][j].link_faces)
    return next(iter(s))


def limb(bm, face, rings):
    f = face
    for c, hw, hd in rings:
        r = extrude(bm, [f])
        vs = sorted(r['verts'], key=lambda v: v.co.y)
        fr = sorted(vs[:2], key=lambda v: -v.co.x); bk = sorted(vs[2:], key=lambda v: -v.co.x)
        c = Vector(c)
        place([fr[0], fr[1], bk[0], bk[1]], [c + Vector((hw, -hd, 0)), c + Vector((-hw, -hd, 0)),
                                             c + Vector((hw, hd, 0)), c + Vector((-hw, hd, 0))])
        f = r['faces'][0]
    return f


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, half(*s)) for s in SEC] + [ring(bm, tube(*t)) for t in TAIL]
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, list(reversed(rows[0])))
    cap(bm, rows[-1])
    fl, hl, ea = quad(rows, 6, 3), quad(rows, 10, 3), quad(rows, 4, 1)
    limb(bm, fl, FRONT)
    limb(bm, hl, HIND)
    limb(bm, ea, EAR)
    snap_seam(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'neck loop between skull and nape: the neck bend'):
        loopcut(bm, edge_near(bm, (0.18, -0.19, 0.625)), t=0.5)
    with k.topo(bm, 'loop', 'mouth-corner ring between muzzle and stop: tusk root, jaw plane'):
        loopcut(bm, edge_near(bm, (0.11, -0.495, 0.36)), t=0.5)
    with k.topo(bm, 'loop', 'mid-spine loop behind the ribs: the back bend'):
        loopcut(bm, edge_near(bm, (0.205, 0.19, 0.665)), t=0.5)
    with k.topo(bm, 'loop', 'foreleg loop below the elbow: the elbow bend'):
        loopcut(bm, edge_near(bm, (0.204, -0.128, 0.195)), t=0.5)
    with k.topo(bm, 'loop', 'hind-leg loop between stifle and hock: the gaskin'):
        loopcut(bm, edge_near(bm, (0.173, 0.39, 0.19)), t=0.5)
    disc = face_near(bm, (0.035, -0.72, 0.36), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'nostril in the snout disc'):
        nos = inset(bm, [disc], 0.55, -0.012)[0]
    ef = face_near(bm, (0.11, -0.405, 0.55), n=(1, 0, 0.3))
    with k.topo(bm, 'inset', 'eye socket under the brow'):
        eye = inset(bm, [ef], 0.45, -0.012)[0]
    # free moves: wedge hooves (toe forward, heel up), brow ridge over the eye
    for cy in (-0.10, 0.435):
        for v in verts_where(bm, lambda c: c.z < 0.001 and abs(c.y - cy) < 0.08 and c.y < cy):
            v.co.y -= 0.015
        for v in verts_where(bm, lambda c: abs(c.z - 0.045) < 0.002 and abs(c.y - cy) < 0.08 and c.y > cy):
            v.co.z += 0.012
    # slivers: thicken the needle-thin tail rings and the ear tips
    for (c, d, r), f in zip(TAIL, (2.4, 1.8, 1.7, 1.6)):
        ring_v = [v for v in bm.verts if (v.co - Vector(c)).length < r * 1.3]
        scale(ring_v, (f, 1, f) if d == (0, 1, 0) else f, pivot=c)
    tip = [v for v in bm.verts if (v.co - Vector(EAR[-1][0])).length < 0.012]
    scale(tip, (2.0, 2.0, 1.0), pivot=EAR[-1][0])
    brow = vert_near(bm, (0.095, -0.36, 0.62))
    brow.co.x += 0.018; brow.co.z += 0.006
    recalc_normals(bm)
    G['nostril'] = nos.calc_center_median().copy()
    G['eye'] = eye.calc_center_median().copy(); G['eye_n'] = eye.normal.copy()
    commit(body, bm)


def body_rule(c, n, i):
    p = Vector((abs(c.x), c.y, c.z))
    if 'eye' in G and ((p - G['eye']).length < 0.004 or (p - G['nostril']).length < 0.004):
        return 'eye'
    if c.z < 0.052:
        return 'hoof'
    if c.y < -0.66:
        return 'snout'
    if -0.25 < c.y < 0.12 and n.z > 0.3:
        return 'bristle'
    return 'body'


def solid(name, rows, colour, mirror=True, closed=False):
    bm = bmesh.new()
    rs = [ring(bm, r) for r in rows]
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=closed)
    cap(bm, list(reversed(rs[0]))); cap(bm, rs[-1])
    if mirror:
        snap_seam(bm)
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {colour: PAL[colour]}, lambda c, n, i: colour)
    return ob


def ring4(c, d, r, n=5):
    d = Vector(d).normalized(); u = d.cross(Vector((0, 0, 1)))
    if u.length < 1e-3:
        u = d.cross(Vector((1, 0, 0)))
    u.normalize(); w = d.cross(u)
    return [tuple(Vector(c) + (u * math.cos(2 * math.pi * i / n) + w * math.sin(2 * math.pi * i / n)) * r) for i in range(n)]


def top_z(y):
    ys = [s[0] for s in SEC]; zs = [s[1] for s in SEC]
    for (y0, z0), (y1, z1) in zip(zip(ys, zs), zip(ys[1:], zs[1:])):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return zs[-1]


def stage3(k, body):
    paint(body, PAL, body_rule)
    pieces = []
    # tusks: from the mouth corner, curving out and up
    pts = [(0.088, -0.53, 0.335), (0.128, -0.545, 0.36), (0.158, -0.54, 0.42), (0.152, -0.51, 0.485)]
    rad = [0.020, 0.018, 0.013, 0.005]
    rows = []
    for i, (p, r) in enumerate(zip(pts, rad)):
        d = Vector(pts[min(i + 1, 3)]) - Vector(pts[max(i - 1, 0)])
        rows.append(ring4(p, d, r, 4))
    pieces.append(solid('tusk', rows, 'tusk', mirror=True, closed=True))
    # eyes: a squat bipyramid lens proud of the socket floor
    c, n = G['eye'], G['eye_n']
    rim = ring4(c + n * 0.004, n, 0.017, 5)
    bm = bmesh.new()
    rv = ring(bm, rim); f = ring(bm, [tuple(c + n * 0.011)]); b = ring(bm, [tuple(c - n * 0.008)])
    for i in range(5):
        bm.faces.new([rv[i], rv[(i + 1) % 5], f[0]]); bm.faces.new([rv[(i + 1) % 5], rv[i], b[0]])
    eye = object_from_bm('eye', bm, mirror=True); paint(eye, {'eye': PAL['eye']}, lambda c, n, i: 'eye')
    pieces.append(eye)
    # crest: blunt leaning clumps on the spine ridge, nape to mid-back
    bm = bmesh.new()
    for y0 in (-0.27, -0.20, -0.13, -0.06, 0.01, 0.08, 0.15):
        h = 0.6 + 0.4 * max(0.0, 1 - abs(y0 + 0.08) / 0.25)
        y1 = y0 + 0.07; z0, z1 = top_z(y0), top_z(y1 - 0.01)
        fr = [(0, y0, z0 + 0.05 * h), (0.026, y0, z0 + 0.042 * h), (0.045, y0, z0 - 0.03), (0, y0, z0 - 0.05)]
        bk = [(0, y1, z1 + 0.085 * h), (0.028, y1, z1 + 0.075 * h), (0.045, y1, z1 - 0.03), (0, y1, z1 - 0.05)]
        a, b = ring(bm, fr), ring(bm, bk)
        bridge(bm, a, b); cap(bm, list(reversed(a))); cap(bm, b)
    crest = object_from_bm('crest', bm, mirror=True)
    paint(crest, {'bristle': PAL['bristle']}, lambda c, n, i: 'bristle')
    pieces.append(crest)
    # tail tuft
    tuft = [tube((0, 0.688, 0.505), (0, 0.05, -1), 0.008, 4), tube((0, 0.69, 0.46), (0, 0.05, -1), 0.04, 4),
            tube((0, 0.695, 0.41), (0, 0.05, -1), 0.008, 4)]
    pieces.append(solid('tuft', tuft, 'bristle', mirror=True))
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hips'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['snout'], 'neck', True),
        ('tail', J['tail0'], J['tail1'], 'hips'),
        ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('fhoof.L', J['wrist'], J['fhoof'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['stifle'], 'hips'),
        ('shin.L', J['stifle'], J['hock'], 'thigh.L', True),
        ('hhoof.L', J['hock'], J['hhoof'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 10: {'neck': (-6, 0, 0), 'head': (-14, 0, 0)}, 16: {'neck': (-6, 0, 0), 'head': (-8, 0, 3)},
                       22: {'neck': (-7, 0, 0), 'head': (-16, 0, -3)}, 32: {'neck': (2, 0, 0), 'head': (6, 0, 0), 'tail': (0, 0, 15)},
                       40: {'neck': (0, 0, 0), 'head': (2, 0, 0), 'tail': (0, 0, -15)}, 48: {}})
    A, B = 18, 30
    s1 = {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'head': (3, 0, 0)}
    s2 = {'upperarm.L': (12, 0, 0), 'forearm.L': (-50, 0, 0), 'fhoof.L': (-35, 0, 0), 'upperarm.R': (0, 0, 0),
          'thigh.R': (0, 0, 0), 'shin.R': (B, 0, 0), 'thigh.L': (0, 0, 0), 'head': (-3, 0, 0), 'tail': (0, 0, 10)}
    s3 = {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'head': (3, 0, 0)}
    s4 = {'upperarm.R': (12, 0, 0), 'forearm.R': (-50, 0, 0), 'fhoof.R': (-35, 0, 0), 'shin.L': (B, 0, 0), 'head': (-3, 0, 0), 'tail': (0, 0, -10)}
    clip(rig, 'move', {1: s1, 7: s2, 13: s3, 19: s4, 25: s1},
         loc={1: {'hips': (0, 0, 0)}, 7: {'hips': (0, 0, 0.015)}, 13: {'hips': (0, 0, 0)}, 19: {'hips': (0, 0, 0.015)}, 25: {'hips': (0, 0, 0)}})
    crouch = {'neck': (-10, 0, 0), 'head': (-18, 0, 0), 'upperarm.L': (-10, 0, 0), 'upperarm.R': (-10, 0, 0),
              'thigh.L': (10, 0, 0), 'thigh.R': (10, 0, 0)}
    lunge = {'neck': (-8, 0, 0), 'head': (-22, 0, 0), 'upperarm.L': (12, 0, 0), 'upperarm.R': (12, 0, 0),
             'thigh.L': (-12, 0, 0), 'thigh.R': (-12, 0, 0)}
    toss = {'neck': (10, 0, 0), 'head': (22, 0, 8), 'upperarm.L': (6, 0, 0), 'upperarm.R': (6, 0, 0)}
    clip(rig, 'attack', {1: {}, 8: crouch, 15: lunge, 21: toss, 27: {'head': (4, 0, 0)}, 33: {}},
         loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, -0.02)}, 15: {'hips': (0, 0.08, 0)}, 21: {'hips': (0, 0.05, 0.01)},
              27: {'hips': (0, 0.0, 0)}, 33: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
