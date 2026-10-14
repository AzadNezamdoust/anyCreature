import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'kit')))
from bmkit import *

META = dict(creature='wolf', model='opus',
            keep_valleys=lambda c: abs(abs(c.x) - 0.10) < 0.035 and -0.745 < c.y < -0.685 and 0.875 < c.z < 0.97)

# the skeleton the model is built on (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.28, 0.64), spine=(0.0, 0.04, 0.64), chest=(0.0, -0.24, 0.64),
    neck=(0.0, -0.40, 0.70), head=(0.0, -0.55, 0.87), nose=(0.0, -0.89, 0.86),
    tail0=(0.0, 0.43, 0.66), tail1=(0.0, 0.56, 0.58), tail2=(0.0, 0.68, 0.44), tail3=(0.0, 0.80, 0.26),
    shoulder=(0.13, -0.25, 0.60), elbow=(0.135, -0.235, 0.36), wrist=(0.13, -0.265, 0.085),
    fpaw=(0.13, -0.29, 0.02), ftoe=(0.13, -0.345, 0.02),
    hipL=(0.13, 0.22, 0.60), knee=(0.135, 0.16, 0.38), hock=(0.13, 0.305, 0.14),
    hpaw=(0.13, 0.265, 0.02), htoe=(0.13, 0.20, 0.02),
    ear=(0.11, -0.595, 0.97), eartip=(0.118, -0.585, 1.10),
)

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = [(0, 1), (0.6, 0.92), (1, 0.3), (0.85, -0.35), (0.45, -0.8), (0, -1)]
CHEST = [(0, 1), (0.62, 0.9), (1, 0.35), (0.8, -0.3), (0.35, -0.8), (0, -1)]
HEAD = [(0, 1), (0.7, 0.95), (1, 0.3), (0.85, -0.4), (0.5, -0.85), (0, -1)]
MUZ = [(0, 1), (0.62, 0.95), (1, 0.4), (0.95, -0.3), (0.6, -0.85), (0, -1)]
TAIL = [(0, 1), (0.7, 0.7), (1, 0.1), (0.85, -0.5), (0.45, -0.9), (0, -1)]

# the spine loft, tail tip -> nose: (name, (y, z) centre, tilt deg, T, B, W, profile)
SECS = [
    ('T0', (0.80, 0.26), 62, 0.02, 0.02, 0.02, TAIL),
    ('T1', (0.745, 0.35), 58, 0.06, 0.06, 0.06, TAIL),
    ('T2', (0.655, 0.47), 50, 0.075, 0.075, 0.072, TAIL),
    ('T3', (0.555, 0.585), 40, 0.055, 0.055, 0.052, TAIL),
    ('T4', (0.47, 0.655), 25, 0.042, 0.042, 0.04, TAIL),
    ('R0', (0.39, 0.61), 10, 0.11, 0.10, 0.135, BODY),
    ('R1', (0.28, 0.61), 0, 0.15, 0.15, 0.175, BODY),
    ('R2', (0.16, 0.64), 0, 0.115, 0.11, 0.16, BODY),
    ('W0', (0.04, 0.645), 0, 0.11, 0.10, 0.14, BODY),
    ('M0', (-0.08, 0.615), 0, 0.16, 0.16, 0.18, BODY),
    ('C0', (-0.20, 0.585), 0, 0.215, 0.215, 0.205, CHEST),
    ('C1', (-0.32, 0.60), 0, 0.23, 0.23, 0.20, CHEST),
    ('C2', (-0.42, 0.655), 15, 0.21, 0.205, 0.175, CHEST),
    ('N0', (-0.48, 0.75), 35, 0.16, 0.15, 0.165, BODY),
    ('N1', (-0.535, 0.81), 35, 0.135, 0.12, 0.15, BODY),
    ('H0', (-0.58, 0.87), 20, 0.105, 0.115, 0.135, HEAD),
    ('H0b', (-0.63, 0.872), 5, 0.112, 0.12, 0.15, HEAD),
    ('H1', (-0.69, 0.868), 0, 0.106, 0.105, 0.145, HEAD),
    ('H2', (-0.745, 0.85), 0, 0.068, 0.074, 0.094, MUZ),
    ('H3', (-0.84, 0.848), 0, 0.049, 0.052, 0.068, MUZ),
    ('H4', (-0.895, 0.855), -5, 0.034, 0.03, 0.048, MUZ),
]

# limb sections: (centre xyz, rx, ry) — horizontal hexagons, deeper front-to-back
FORE = [(J['elbow'], 0.056, 0.078), ((0.13, -0.255, 0.22), 0.044, 0.058), (J['wrist'], 0.036, 0.042),
        ((0.13, -0.285, 0.042), 0.05, 0.064), ((0.13, -0.295, 0.0), 0.054, 0.075)]
HIND = [(J['knee'], 0.058, 0.09), ((0.13, 0.23, 0.26), 0.045, 0.062), (J['hock'], 0.034, 0.048),
        ((0.13, 0.285, 0.068), 0.033, 0.038), ((0.13, 0.262, 0.036), 0.048, 0.058), ((0.13, 0.25, 0.0), 0.052, 0.07)]
EAR = [((0.112, -0.598, 1.045), 0.05, 0.026, 0.014), ((0.12, -0.588, 1.105), 0.008, 0.005, 0.0)]


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def role_pos(sec, u, s, corner=0.55):
    c, rx, ry = sec[0], sec[1], sec[2]
    dz = sec[3] if len(sec) > 3 else 0.0
    k = 1.0 if u == 0 else corner
    return (c[0] + u * rx, c[1] + s * ry * k, c[2] - u * dz)


def grow(bm, faces, roles, secs, corner=0.55):
    """Extrude a face region section by section; each new vertex keeps the role
    (u across the ring, s front/back) of the vertex it was extruded from."""
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (u, s) in new.items():
            v.co = Vector(role_pos(sec, u, s, corner))
        faces, roles = r['faces'], new
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(span_name, secs):
        i = idx[span_name]          # span between ring i (rear) and ring i+1 (front)
        rr, rf = rings[i], rings[i + 1]
        roles = {rf[2]: (1, -1), rf[3]: (0, -1), rf[4]: (-1, -1), rr[2]: (1, 1), rr[3]: (0, 1), rr[4]: (-1, 1)}
        grow(bm, [spans[i][2], spans[i][3]], roles, secs)

    limb('C0', FORE)
    limb('R1', HIND)
    i = idx['H0']
    rr, rf = rings[i], rings[i + 1]
    grow(bm, [spans[i][1]], {rf[1]: (-1, -1), rf[2]: (1, -1), rr[1]: (-1, 1), rr[2]: (1, 1)}, EAR, corner=1.0)
    snap_seam(bm)
    return object_from_bm('body', bm)


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'elbow: a second ring between elbow and forearm so the elbow bends, not kinks'):
        loopcut(bm, edge_near(bm, (0.1825, -0.2075, 0.29)), t=0.5)
    with k.topo(bm, 'loop', 'stifle: a second ring between knee and gaskin for the hind-leg bend'):
        loopcut(bm, edge_near(bm, (0.184, 0.237, 0.32)), t=0.5)
    with k.topo(bm, 'loop', 'neck: a mid-neck ring so the head-down lunge bends the neck in two places'):
        loopcut(bm, edge_near(bm, (0.0, -0.423, 0.90)), t=0.5)
    H1, H2, H3, H4, H0b = P('H1'), P('H2'), P('H3'), P('H4'), P('H0b')
    ec = (H1[1] + H1[2] + H2[1] + H2[2]) / 4
    f = face_near(bm, ec)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the stop face, under the brow'):
        inner = inset(bm, [f], 0.36, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.012)
    scale(ev, (1.0, 1.0, 0.85))
    # brow overhang: the brow corner forward and out, the cheekbone out
    move([vert_near(bm, H1[1])], (0.008, -0.014, 0.004))
    move([vert_near(bm, H0b[2])], (0.01, 0.0, 0.0))
    # deliberate planes on the muzzle: one flat side, one flat bridge
    flatten([vert_near(bm, q) for q in (H2[2], H2[3], H3[2], H3[3], H4[2], H4[3])])
    flatten([vert_near(bm, q) for q in (H2[0], H2[1], H3[0], H3[1], H4[0], H4[1])])
    # nose: the flat end cap becomes a forward-down slanted pad (top edge forward, chin edge back)
    move([vert_near(bm, H4[0]), vert_near(bm, H4[1])], (0.0, -0.022, -0.004))
    move([vert_near(bm, H4[4]), vert_near(bm, H4[5])], (0.0, 0.018, 0.0))
    scale([vert_near(bm, q) for q in H4], (0.85, 1.0, 1.0), pivot=(0.0, 0.0, 0.0))
    commit(body, bm)


PAL = {'fur': '#9c978e', 'saddle': '#65636b', 'tan': '#b59d76', 'cream': '#efe6cf', 'amber': '#e0a030', 'nose': '#1e1b1b'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.866 and z > 0.835:
        return 'nose'                                   # black nose pad
    if y > 0.735:
        return 'saddle'                                 # dark tail tip
    if y < -0.6 and (n.z < -0.35 or (y < -0.78 and z < 0.835)):
        return 'cream'                                  # lip and lower jaw
    if z < 0.34:
        return 'tan'                                    # legs
    if -0.62 < y < -0.34 and n.y < -0.25 and z < 0.78 and x < 0.12:
        return 'cream'                                  # throat and bib
    if n.z < -0.55 and z > 0.35 and y < 0.2:
        return 'cream'                                  # belly
    if n.z > 0.72 and -0.34 < y < 0.40 and z > 0.68:
        return 'saddle'                                 # back saddle
    return 'fur'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A low-poly eye: back cone, iris ring, pupil fan. Returns the pupil faces."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 3 for k_ in range(6)]]
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    pup = []
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        pup.append(bm.faces.new([I[a], I[b], A]))
    return pup


def clump(bm, a, n, lay, s, L):
    """A chunky fur clump: a sunk square base, a narrower mid ring, a tip laid back along `lay`."""
    n, lay = Vector(n).normalized(), Vector(lay).normalized()
    u = n.cross(lay).normalized(); w = u.cross(n)
    b = a - n * 0.025
    base = [bm.verts.new(b + u * su * s + w * sw * s) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = a + n * 0.018 + lay * L * 0.4
    mid = [bm.verts.new(m + u * su * s * 0.6 + w * sw * s * 0.5) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    tip = bm.verts.new(a + n * L * 0.3 + lay * L)
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip])


def out_n(nm, j):
    for (n_, c, a, T, B, W, p) in SECS:
        if n_ == nm:
            q = P(nm)[j]
            return q, (q - Vector((0.0, c[0], c[1]))).normalized()


def stage3(k, body):
    paint(body, PAL, body_rule)
    H1, H2 = P('H1'), P('H2')
    fn = (H2[1] - H1[1]).cross(H1[2] - H1[1]).normalized()
    fn = fn if fn.x > 0 else -fn
    ec = (H1[1] + H1[2] + H2[1] + H2[2]) / 4
    bmb = edit(body)
    f = face_near(bmb, ec - fn * 0.012, n=fn)
    c, n = f.calc_center_median().copy(), f.normal.copy()
    n = n if n.x > 0 else -n
    bmb.free()
    bm = bmesh.new()
    pup = lens(bm, c, n, 0.019, 0.009)
    pidx = {f_.index for f_ in pup} if False else None
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'nose': PAL['nose']},
          lambda c_, n_, i: 'nose' if (c_ - (eye.matrix_world @ c)).length < 0.0075 and n_.dot(n) > 0.5 else 'amber')
    # neck ruff: clumps laid back and down; cheek ruff; cream bib clumps under the throat
    bm = bmesh.new()
    back = Vector((0, 0.85, -0.5))
    for nm, j, s_, L_, lay in (('N0', 1, 0.035, 0.09, back), ('N0', 2, 0.04, 0.10, back), ('N0', 3, 0.038, 0.095, back),
                               ('N1', 2, 0.035, 0.085, back), ('N1', 3, 0.033, 0.08, back), ('C2', 2, 0.035, 0.085, back),
                               ('H0', 3, 0.028, 0.07, Vector((0.2, 0.9, -0.4)))):
        a, n_ = out_n(nm, j)
        clump(bm, a, n_, lay, s_, L_)
    ruff = object_from_bm('ruff', bm)
    paint(ruff, {'fur': PAL['fur']}, lambda c_, n_, i: 'fur')
    bm = bmesh.new()
    for nm, j in (('N1', 4), ('C2', 4), ('N0', 4)):
        a, n_ = out_n(nm, j)
        clump(bm, a, n_, Vector((0.15, 0.3, -1.0)), 0.03, 0.075)
    bib = object_from_bm('bib', bm)
    paint(bib, {'cream': PAL['cream']}, lambda c_, n_, i: 'cream')
    # tail brush: clumps laid toward the tip, the last one dark
    bm = bmesh.new()
    tl = Vector((0, 0.55, -0.83))
    for nm, j in (('T3', 2), ('T2', 1), ('T2', 3), ('T1', 2)):
        a, n_ = out_n(nm, j)
        clump(bm, a, n_, tl, 0.03, 0.08)
    brush = object_from_bm('brush', bm)
    paint(brush, {'fur': PAL['fur'], 'saddle': PAL['saddle']}, lambda c_, n_, i: 'saddle' if c_.y > 0.74 else 'fur')
    # toe claws: three per paw, the middle one leading
    bm = bmesh.new()
    for (sole, top) in ((FORE[4], FORE[3]), (HIND[5], HIND[4])):
        (cx, cy, _), rx, ry = sole
        for d in (-0.024, 0.0, 0.024):
            yf = cy - ry * (1 - 0.45 * abs(d) / rx) + 0.004
            x = cx + d
            t = bm.verts.new((x, yf - 0.022 - (0.006 if d == 0 else 0), 0.012))
            b = [bm.verts.new(p_) for p_ in ((x - 0.009, yf + 0.012, 0.005), (x + 0.009, yf + 0.012, 0.005), (x, yf + 0.012, 0.024))]
            bm.faces.new([b[0], b[1], b[2]]); bm.faces.new([b[0], t, b[1]]); bm.faces.new([b[1], t, b[2]]); bm.faces.new([b[2], t, b[0]])
    claws = object_from_bm('claws', bm)
    paint(claws, {'nose': PAL['nose']}, lambda c_, n_, i: 'nose')
    return [eye, ruff, bib, brush, claws]


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('paw.L', J['wrist'], J['ftoe'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
         ('foot.L', J['hock'], J['hpaw'], 'shin.L', True),
         ('toe.L', J['hpaw'], J['htoe'], 'foot.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing through the chest, a slow tail sway, one ear twitch
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 4)},
                       20: {'ear.L': (0, 0, -14)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -4)}, 48: {}})
    # move: trot, diagonal pairs (LF + RH, then RF + LH); the swinging leg flexes
    A = 18
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 5)},
        7: {'forearm.R': (-35, 0, 0), 'paw.R': (-30, 0, 0), 'shin.L': (-20, 0, 0), 'foot.L': (25, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -5)},
        19: {'forearm.L': (-35, 0, 0), 'paw.L': (-30, 0, 0), 'shin.R': (-20, 0, 0), 'foot.R': (25, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 5)}})
    # attack: rear back, then a head-down lunge and a snap of the head
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-10, 0, 0), 'chest': (4, 0, 0), 'head': (-4, 0, 0), 'tail0': (8, 0, 0)},
        16: {'neck': (20, 0, 0), 'chest': (-11, 0, 0), 'head': (8, 0, 0), 'upperarm.L': (14, 0, 0), 'upperarm.R': (14, 0, 0),
             'ear.L': (-12, 0, 0)},
        20: {'neck': (17, 0, 0), 'chest': (-11, 0, 0), 'head': (20, 0, 0), 'upperarm.L': (14, 0, 0), 'upperarm.R': (14, 0, 0),
             'ear.L': (-12, 0, 0)},
        24: {'neck': (18, 0, 0), 'chest': (-5, 0, 0), 'head': (6, 0, 0), 'upperarm.L': (8, 0, 0), 'upperarm.R': (8, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, 0)}, 16: {'hips': (0, 0.06, 0)}, 20: {'hips': (0, 0.06, 0)},
             24: {'hips': (0, 0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
