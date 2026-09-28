import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='giant', model='opus')

# the skeleton the model is built on (left side; .R mirrors)
J = dict(
    hip=(0.0, 0.0, 1.35), spine=(0.0, 0.02, 2.0), chest=(0.0, 0.08, 2.7), neck=(0.0, -0.3, 3.4),
    head=(0.0, -0.8, 3.1), head_end=(0.0, -1.36, 3.12),
    shoulder=(1.30, 0.06, 2.95), elbow=(1.62, 0.02, 2.05), wrist=(1.66, -0.14, 1.28), fist=(1.68, -0.2, 0.66),
    hipL=(0.55, -0.02, 1.2), knee=(0.58, -0.1, 0.66), ankle=(0.62, 0.0, 0.24), toe=(0.64, -0.62, 0.08),
)


def trow(F, B, w, s=0.5, kf=0.86, ff=0.68, kb=0.86, bb=0.68, lift=0.0):
    """A half torso section from the front seam F=(y,z) round the flank to the back seam B."""
    S = (F[0] + (B[0] - F[0]) * s, F[1] + (B[1] - F[1]) * s + lift)
    P1 = (kf * w, S[0] + (F[0] - S[0]) * ff, S[1] + (F[1] - S[1]) * ff)
    P3 = (kb * w, S[0] + (B[0] - S[0]) * bb, S[1] + (B[1] - S[1]) * bb)
    return [(0.0, F[0], F[1]), P1, (w, S[0], S[1]), P3, (0.0, B[0], B[1])]


# torso rings, crotch to face (front seam, back seam, half width, ...)
TORSO = [
    None,                                                   # R0: built from the leg socket
    dict(F=(-0.86, 1.48), B=(0.62, 1.45), w=0.92, ff=0.55),  # R1 hips / low pot belly
    dict(F=(-1.08, 1.92), B=(0.62, 2.00), w=1.00, kf=0.82, ff=0.52),  # R2 belly
    dict(F=(-0.86, 2.45), B=(0.72, 2.50), w=0.98, kf=0.8, ff=0.55, kb=0.8, bb=0.55),   # R3 ribs
    dict(F=(-0.72, 2.80), B=(0.86, 2.95), w=0.98, kf=0.75, ff=0.55, kb=0.8, bb=0.55),  # R4 chest, armpit (keel)
    dict(F=(-0.78, 2.86), B=(1.00, 3.58), w=1.08, kb=0.8, bb=0.55),         # R5 shoulder (socket top)
    dict(F=(-0.80, 2.92), B=(0.30, 4.00), w=1.10, lift=0.12, ff=0.55, kb=0.8, bb=0.55),  # R6 hump / trapezius
    dict(F=(-1.00, 2.84), B=(-0.46, 3.46), w=0.52, ff=0.6),  # R7 nape dip under the hump
    dict(F=(-1.14, 2.76), B=(-0.74, 3.52), w=0.42, kf=0.95, kb=0.75),  # R8 skull back / jaw hinge
    dict(F=(-1.28, 2.70), B=(-1.02, 3.50), w=0.42, kf=1.0, kb=0.7),   # R9 cheek / eye, wide jaw
    dict(F=(-1.40, 2.80), B=(-1.40, 3.30), w=0.36, kf=0.95, kb=0.65), # R10 face front (cap)
]


def aring(c, phi, a, d):
    """Arm hexagon: inner-front, inner, inner-back, outer-back, outer, outer-front.
    phi tilts the section from horizontal (0, arm hanging) to vertical (90, arm out)."""
    p = math.radians(phi)
    X = Vector((math.cos(p), 0.0, math.sin(p)))
    c = Vector(c)
    loc = [(-0.55 * a, -d), (-a, 0.0), (-0.55 * a, d), (0.55 * a, d), (a, 0.0), (0.55 * a, -d)]
    return [tuple(c + X * u + Vector((0, v, 0))) for u, v in loc]


def lring(c, a, d, loc=None):
    """Leg hexagon: front, outer, back, inner-back, inner, inner-front (horizontal)."""
    loc = loc or [(0.05 * a, -d), (a, 0.0), (0.05 * a, d), (-0.9 * a, 0.5 * d), (-a, 0.0), (-0.9 * a, -0.5 * d)]
    return [(c[0] + u, c[1] + v, c[2]) for u, v in loc]


def grow(bm, faces, ring_, pts):
    """E then place: extrude the region and put its new boundary (in ring_ order) at pts."""
    r = extrude(bm, faces)
    nv = set(r['verts'])
    new = [next(e.other_vert(v) for e in v.link_edges if e.other_vert(v) in nv) for v in ring_]
    place(new, pts)
    return r['faces'], new


LEG0 = dict(c=(0.55, -0.02, 1.15), a=0.42, d=0.42)
LEGS = [
    lring((0.55, -0.02, 0.92), 0.42, 0.45),          # thigh
    lring((0.58, -0.10, 0.66), 0.34, 0.36),          # knee
    lring((0.60, -0.02, 0.44), 0.34, 0.36),          # calf
    lring((0.62, 0.00, 0.24), 0.25, 0.26),           # ankle
    lring((0.64, -0.18, 0.14), 1, 1, [(0.0, -0.55), (0.34, -0.05), (0.0, 0.32), (-0.30, 0.20), (-0.33, -0.05), (-0.30, -0.42)]),
    lring((0.64, -0.18, 0.0), 1, 1, [(0.0, -0.58), (0.36, -0.05), (0.0, 0.34), (-0.32, 0.21), (-0.35, -0.05), (-0.32, -0.44)]),
]
ARMS = [
    aring((1.44, 0.08, 3.02), 30, 0.38, 0.44),       # deltoid
    aring((1.55, 0.05, 2.55), 10, 0.33, 0.39),       # upper arm
    aring(J['elbow'], 6, 0.26, 0.31),                # elbow
    aring((1.64, -0.08, 1.70), 4, 0.32, 0.38),       # forearm
    aring(J['wrist'], 0, 0.20, 0.25),                # wrist
    aring((1.66, -0.18, 1.16), 0, 0.30, 0.42),       # fist top
    aring((1.66, -0.22, 0.64), 0, 0.28, 0.40),       # fist bottom (knuckles down)
]


def stage1(k):
    bm = bmesh.new()
    cx, cy, cz = LEG0['c']; a, d = LEG0['a'], LEG0['d']
    lp = lring(LEG0['c'], a, d)
    r0 = [(0.0, -0.55, 1.30), lp[0], lp[1], lp[2], (0.0, 0.45, 1.25)]
    R = [ring(bm, r0)] + [ring(bm, trow(**t)) for t in TORSO[1:]]
    band = [bridge(bm, R[i], R[i + 1]) for i in range(len(R) - 1)]
    i3, i2, i1 = ring(bm, [lp[3], lp[4], lp[5]])
    s, m, t = ring(bm, [(0.0, lp[5][1], cz), (0.0, lp[4][1], cz - 0.03), (0.0, lp[3][1], cz)])
    for f in ([R[0][0], R[0][1], i1, s], [s, i1, i2, m], [m, i2, i3, t], [t, i3, R[0][3], R[0][4]]):
        bm.faces.new(f)
    legf = [bm.faces.new([R[0][1], R[0][2], i2, i1]), bm.faces.new([R[0][2], R[0][3], i3, i2])]
    cap(bm, R[-1])
    recalc_normals(bm)
    # legs
    rg = [R[0][1], R[0][2], R[0][3], i3, i2, i1]
    for pts in LEGS:
        legf, rg = grow(bm, legf, rg, pts)
    # arms, out of the flank faces between the chest and shoulder rings
    armf = [band[4][1], band[4][2]]
    rg = [R[4][1], R[4][2], R[4][3], R[5][3], R[5][2], R[5][1]]
    for pts in ARMS:
        armf, rg = grow(bm, armf, rg, pts)
    snap_seam(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    r9s, r10s = vert_near(bm, (0.42, -1.15, 3.10)), vert_near(bm, (0.36, -1.40, 3.05))
    e = next(x for x in r10s.link_edges if x.other_vert(r10s) is r9s)
    with k.topo(bm, 'loop', 'face loop round the head just behind the face: cheek plane and eye depth'):
        loopcut(bm, e, t=0.4, near=r10s)
    eyef = face_near(bm, (0.31, -1.34, 3.16), n=(0.5, -0.8, 0.0))
    with k.topo(bm, 'socket', 'eye socket under the brow (inset, pushed in)'):
        inner = inset(bm, [eyef], 0.3, -0.04)
    # face planes: heavy brow forward over the socket, cheekbone out, underbite jaw forward
    for p, q in [((0.0, -1.40, 3.30), (0.0, -1.49, 3.30)),        # brow centre
                 ((0.234, -1.40, 3.22), (0.27, -1.48, 3.24)),     # brow corner, overhangs the eye
                 ((0.36, -1.40, 3.05), (0.39, -1.39, 3.02)),      # cheekbone
                 ((0.342, -1.40, 2.88), (0.38, -1.47, 2.84)),     # jaw corner forward (underbite)
                 ((0.0, -1.40, 2.80), (0.0, -1.49, 2.75))]:       # chin
        vert_near(bm, p).co = Vector(q)
    # deep-set eye: the socket floor tilts down under the brow
    for v in inner[0].verts:
        v.co.y += 0.02
    # confident planes: flatten the back of the hump and the front of the pot belly
    flatten(verts_where(bm, lambda c: c.z > 3.3 and c.y > 0.1 and c.x < 0.95 and c.x > -0.01 and c.z < 4.1 and c.y < 1.1 and c.x < 0.9))
    commit(body, bm)


PAL = dict(hide='#66727f', dark='#343b46', stone='#8b867c', moss='#6f8f3a',
           leather='#a58c67', tusk='#d6c9a6', amber='#f4b427')
AX = (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))


def mesh_piece(name, verts, faces, mirror=False, colour=None, rule=None):
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(p)) for p in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, PAL, rule or (lambda c, n, i: colour))
    return ob


def frame(n):
    n = Vector(n).normalized()
    t1 = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized()
    return n, t1, n.cross(t1).normalized()


def box(c, h):
    c = Vector(c)
    vs = [c + Vector((sx * h[0], sy * h[1], sz * h[2])) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return vs, fs


def stack(rings, cap0=True, cap1=True, tip=None):
    """Rings of equal length bridged in order; optional end caps or a tip vertex."""
    vs, fs, n = [], [], len(rings[0])
    for r in rings:
        vs += [Vector(p) for p in r]
    for j in range(len(rings) - 1):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            fs.append((a, b, b + n, a + n))
    if cap0:
        fs.append(tuple(reversed(range(n))))
    if tip is not None:
        vs.append(Vector(tip)); t = len(vs) - 1; o = (len(rings) - 1) * n
        fs += [(o + i, o + (i + 1) % n, t) for i in range(n)]
    elif cap1:
        fs.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
    return vs, fs


def around(c, n, r, k=6, rot=0.0, jit=None):
    n, t1, t2 = frame(n)
    return [Vector(c) + (t1 * math.cos(rot + 2 * math.pi * i / k) + t2 * math.sin(rot + 2 * math.pi * i / k))
            * r * (jit[i] if jit else 1.0) for i in range(k)]


def body_rule(c, n, i):
    if c.z < 0.16 or (abs(c.x) > 1.3 and c.z < 1.22):
        return 'dark'                                   # feet and fists
    if (c.z > 2.4 and n.y > 0.35) or (c.z > 3.3 and n.z > 0.6 and c.y > -0.5):
        return 'dark'                                   # dark saddle over the back and hump
    if n.y < -0.55 and 1.25 < c.z < 2.6 and abs(c.x) < 0.75:
        return 'stone'                                  # paler pot belly
    return 'hide'


def stage3(k, body):
    paint(body, PAL, body_rule)
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)

    def hit(o, d):
        loc, nrm, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
        assert loc is not None, ('no hit', o, d)
        return loc, nrm

    P = []
    # eyes: amber lens with a dark pupil, proud of the socket floor
    loc, n = hit((0.325 + 0.33, -1.36 - 0.5, 3.15), (-0.55, 0.83, 0.0))
    n = (n + Vector((0, -0.4, -0.15))).normalized()          # look ahead and slightly down
    c = loc + n * 0.012
    vs, fs = stack([around(c - n * 0.03, n, 0.075), around(c + n * 0.03, n, 0.042)], cap0=False, tip=c + n * 0.05)
    vs.append(c - n * 0.07); b = len(vs) - 1
    fs += [((i + 1) % 6, i, b) for i in range(6)]
    pc = c + n * 0.04
    P.append(mesh_piece('eye', vs, fs, mirror=True, rule=lambda cc, nn, i: 'dark' if (cc - pc).length < 0.03 else 'amber'))
    # brow: one heavy dark ridge over both eyes, inner end lower (a scowl)
    st = []
    for x, z in ((0.0, 3.22), (0.18, 3.27), (0.36, 3.30)):
        l, _ = hit((x + 1e-4, -2.2, z), (0, 1, 0))
        st.append([(x, l.y + 0.10, z + 0.02), (x, l.y - 0.08, z + 0.06), (x, l.y - 0.07, z - 0.05)])
    vs, fs = stack(st, cap0=False)
    P.append(mesh_piece('brow', vs, fs, mirror=True, colour='dark'))
    # nose: a blunt wedge under the brow
    l, _ = hit((1e-4, -2.2, 3.08), (0, 1, 0))
    vs = [(0.0, l.y + 0.06, 3.19), (0.0, l.y - 0.13, 3.00), (0.0, l.y + 0.06, 2.95), (0.12, l.y - 0.03, 3.02)]
    P.append(mesh_piece('nose', vs, [(0, 1, 3), (1, 2, 3), (2, 0, 3)], mirror=True, colour='hide'))
    # tusks rising from the lower jaw
    rings = [around(p, (0.2, -0.6, 1.0), r, k=4, rot=0.785) for p, r in
             (((0.22, -1.38, 2.80), 0.055), ((0.25, -1.52, 2.96), 0.045), ((0.28, -1.60, 3.08), 0.025))]
    vs, fs = stack(rings, tip=(0.30, -1.63, 3.16))
    P.append(mesh_piece('tusk', vs, fs, mirror=True, colour='tusk'))
    # moss clumps and flat rocks bedded on the hump and shoulders
    for nm, (x, y), r, kind in (('moss_a', (0.50, 0.76), 0.26, 'moss'), ('moss_b', (0.85, -0.12), 0.24, 'moss'),
                                ('rock_a', (0.15, 0.30), 0.20, 'stone'), ('rock_b', (0.72, 0.32), 0.17, 'stone')):
        l, n = hit((x, y, 6.0), (0, 0, -1))
        if kind == 'moss':
            j = [1.0, 0.8, 1.1, 0.9, 1.05, 0.75, 0.95]
            vs, fs = stack([around(l - n * 0.08, n, r * 0.8, 7, jit=j), around(l + n * 0.07, n, r, 7, jit=j),
                            around(l + n * 0.15, n, r * 0.55, 7, 0.3, jit=j)], tip=l + n * 0.2)
        else:
            n = (n + Vector((0.15, -0.1, 0))).normalized()
            vs, fs = stack([around(l - n * 0.05, n, r, 6, 0.4), around(l + n * 0.07, n, r * 0.85, 6, 0.4)])
        P.append(mesh_piece(nm, vs, fs, mirror=True, colour=kind))
    # belt: a triangular-section band round the waist
    inner, top, bot = [], [], []
    for i in range(12):
        a = 2 * math.pi * i / 12
        d = Vector((math.sin(a), -math.cos(a), 0))
        l, _ = hit((0, -0.1, 1.62), d)
        inner.append(l - d * 0.05); top.append(l + d * 0.07 + Vector((0, 0, 0.09))); bot.append(l + d * 0.07 - Vector((0, 0, 0.09)))
    vs = inner + top + bot
    fs = []
    for i in range(12):
        j = (i + 1) % 12
        fs += [(i, j, 12 + j, 12 + i), (12 + i, 12 + j, 24 + j, 24 + i), (24 + i, 24 + j, j, i)]
    P.append(mesh_piece('belt', vs, fs, colour='leather'))
    # loincloth hanging from the belt front (a thick flap)
    fy = hit((1e-4, -0.1, 1.62), (0, -1, 0))[0].y + 0.035
    grid = [[(x, fy, 1.64), (x * 0.95, fy - 0.03, 1.28), (x * 0.9, fy + 0.02, 0.96 - (0.08 if x == 0 else 0))]
            for x in (-0.32, 0.0, 0.32)]
    vs = [p for col in grid for p in col] + [(p[0], p[1] + 0.045, p[2]) for col in grid for p in col]
    fs = []
    for ci in range(2):
        for ri in range(2):
            a, b = ci * 3 + ri, (ci + 1) * 3 + ri
            fs += [(a, b, b + 1, a + 1), (a + 9, a + 10, b + 10, b + 9)]
    rim = [0, 1, 2, 5, 8, 7, 6, 3]
    fs += [(rim[i], rim[(i + 1) % 8], rim[(i + 1) % 8] + 9, rim[i] + 9) for i in range(8)]
    P.append(mesh_piece('loincloth', vs, fs, colour='leather'))
    # fists: a knuckle row of four fingers with stone nails; stone toenails
    for i, dx in enumerate((-0.165, -0.055, 0.055, 0.165)):
        x = 1.66 + dx
        l, _ = hit((x, -2.0, 0.76), (0, 1, 0))
        zb = 0.60 if i in (1, 2) else 0.64
        vs, fs = box((x, l.y - 0.02, (zb + 0.88) / 2), (0.049, 0.09, (0.88 - zb) / 2))
        P.append(mesh_piece('finger%d' % i, vs, fs, mirror=True, colour='dark'))
        vs, fs = box((x, l.y - 0.115, zb + 0.07), (0.036, 0.03, 0.045))
        P.append(mesh_piece('nail%d' % i, vs, fs, mirror=True, colour='stone'))
    for i, dx in enumerate((-0.15, 0.0, 0.15)):
        l, _ = hit((0.64 + dx, -2.0, 0.07), (0, 1, 0))
        vs, fs = box((0.64 + dx, l.y - 0.01, 0.07), (0.055, 0.06, 0.05))
        P.append(mesh_piece('toenail%d' % i, vs, fs, mirror=True, colour='stone'))
    ebm.free()
    return P


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hip'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], (0.0, -0.35, 3.25), 'spine', True),
        ('neck', (0.0, -0.35, 3.25), (0.0, -0.80, 3.12), 'chest', True),
        ('head', (0.0, -0.80, 3.12), (0.0, -1.40, 3.10), 'neck', True),
        ('clavicle.L', (0.30, 0.02, 3.15), J['shoulder'], 'chest'),
        ('upperarm.L', J['shoulder'], J['elbow'], 'clavicle.L', True),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('hand.L', J['wrist'], J['fist'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
        ('foot.L', J['ankle'], J['toe'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: heavy breathing sway
    clip(rig, 'idle', {1: {}, 12: {'hips': (0, 0, 2), 'chest': (-2, 0, -1)},
                       24: {'spine': (-2, 0, 0), 'chest': (-4, 0, 0), 'head': (4, 0, 0),
                            'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0)},
                       36: {'hips': (0, 0, -2), 'chest': (-2, 0, 1)}, 48: {}})
    # move: lumbering walk (contact, passing, contact, passing)
    c1 = {'thigh.L': (22, 0, 0), 'shin.L': (-10, 0, 0), 'thigh.R': (-18, 0, 0), 'shin.R': (-25, 0, 0),
          'upperarm.L': (-14, 0, 0), 'upperarm.R': (14, 0, 0), 'hips': (0, 5, 3), 'chest': (6, -6, -2), 'head': (-2, 0, 0)}
    p1 = {'shin.L': (-5, 0, 0), 'thigh.R': (8, 0, 0), 'shin.R': (-35, 0, 0), 'chest': (9, 0, 0), 'head': (-5, 0, 0)}
    c2 = {'thigh.L': (-18, 0, 0), 'shin.L': (-25, 0, 0), 'thigh.R': (22, 0, 0), 'shin.R': (-10, 0, 0),
          'upperarm.L': (14, 0, 0), 'upperarm.R': (-14, 0, 0), 'hips': (0, -5, -3), 'chest': (6, 6, 2), 'head': (-2, 0, 0)}
    p2 = {'thigh.L': (8, 0, 0), 'shin.L': (-35, 0, 0), 'shin.R': (-5, 0, 0), 'chest': (9, 0, 0), 'head': (-5, 0, 0)}
    clip(rig, 'move', {1: c1, 9: p1, 17: c2, 25: p2, 33: c1})
    # attack: two-handed overhead slam
    up = {'upperarm.L': (120, 0, 0), 'upperarm.R': (120, 0, 0), 'forearm.L': (30, 0, 0), 'forearm.R': (30, 0, 0),
          'chest': (-14, 0, 0), 'spine': (-8, 0, 0), 'head': (8, 0, 0)}
    slam = {'upperarm.L': (35, 0, 0), 'upperarm.R': (35, 0, 0), 'forearm.L': (5, 0, 0), 'forearm.R': (5, 0, 0),
            'chest': (22, 0, 0), 'spine': (12, 0, 0), 'head': (-8, 0, 0)}
    hold = {'upperarm.L': (30, 0, 0), 'upperarm.R': (30, 0, 0), 'chest': (18, 0, 0), 'spine': (10, 0, 0), 'head': (-5, 0, 0)}
    clip(rig, 'attack', {1: {}, 14: up, 21: slam, 28: hold, 40: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
