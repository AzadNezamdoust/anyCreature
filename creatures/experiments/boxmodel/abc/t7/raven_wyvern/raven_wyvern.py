import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from mathutils import Vector, Quaternion

META = dict(creature='raven_wyvern', model='opus')

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    hip=(0.0, 0.16, 0.74), belly=(0.0, -0.04, 0.78), chest=(0.0, -0.30, 0.84),
    neckb=(0.0, -0.43, 0.86), neckt=(0.0, -0.56, 1.06), head=(0.0, -0.64, 1.18), bill=(0.0, -1.04, 1.13),
    tail0=(0.0, 0.30, 0.74), tail1=(0.0, 0.55, 0.69), tail2=(0.0, 0.82, 0.64), tail3=(0.0, 1.22, 0.62),
    hipL=(0.18, 0.08, 0.64), thighL=(0.245, 0.03, 0.52), kneeL=(0.245, -0.10, 0.34),
    hockL=(0.225, 0.10, 0.15), ballL=(0.215, 0.0, 0.04), toeL=(0.215, -0.11, 0.032),
    shoulderL=(0.275, -0.25, 0.90), armL=(0.29, -0.27, 1.00), wristL=(0.275, -0.23, 1.10),
    fingerL=(0.30, 0.12, 0.98), tipL=(0.295, 0.45, 0.80),
)

# half-ring shapes: three side points (x fraction of w, height fraction of up (+) / dn (-))
SH = dict(
    bill=[(0.70, 0.70), (1.0, 0.0), (0.60, -0.75)],
    head=[(0.80, 0.75), (1.0, 0.05), (0.75, -0.70)],
    neck=[(0.75, 0.75), (1.0, 0.0), (0.80, -0.75)],
    keel=[(0.85, 0.70), (1.0, 0.05), (0.55, -0.70)],
    belly=[(0.85, 0.70), (1.0, 0.0), (0.70, -0.75)],
    hips=[(0.90, 0.70), (1.0, -0.05), (0.80, -0.75)],
    tail=[(0.70, 0.70), (1.0, 0.0), (0.70, -0.70)],
    fin=[(0.60, 0.75), (1.0, 0.0), (0.60, -0.75)],
)

# spine stations bill -> tail: (y, z, pitch of the head-ward direction deg, w, up, dn, shape)
ST = [
    (-1.05, 1.085, -32, 0.014, 0.024, 0.018, 'bill'),   # 0 bill tip (hooked down)
    (-0.98, 1.130, -14, 0.052, 0.072, 0.055, 'bill'),   # 1 hooked culmen
    (-0.89, 1.165, -5, 0.088, 0.105, 0.080, 'bill'),    # 2 bill root: heavy
    (-0.82, 1.190, 0, 0.140, 0.140, 0.115, 'head'),     # 3 face: the stop
    (-0.71, 1.200, 0, 0.170, 0.165, 0.155, 'head'),     # 4 skull, eye
    (-0.60, 1.175, 30, 0.155, 0.145, 0.150, 'head'),    # 5 back of skull, jaw
    (-0.545, 1.045, 70, 0.140, 0.125, 0.135, 'neck'),   # 6 upper neck: thick
    (-0.505, 0.935, 62, 0.150, 0.130, 0.145, 'neck'),   # 7 mid neck
    (-0.43, 0.850, 42, 0.165, 0.130, 0.150, 'neck'),    # 8 neck base
    (-0.33, 0.790, 20, 0.210, 0.170, 0.270, 'keel'),    # 9 chest (wing root)
    (-0.16, 0.770, 10, 0.235, 0.180, 0.270, 'keel'),    # 10 rib cage
    (0.02, 0.760, 4, 0.220, 0.160, 0.210, 'belly'),     # 11 waist (leg root)
    (0.18, 0.760, 0, 0.190, 0.140, 0.170, 'hips'),      # 12 hips
    (0.32, 0.740, -5, 0.145, 0.115, 0.120, 'tail'),     # 13 tail root
    (0.50, 0.700, -8, 0.100, 0.085, 0.080, 'tail'),     # 14
    (0.70, 0.660, -6, 0.070, 0.060, 0.055, 'tail'),     # 15
    (0.88, 0.635, -2, 0.045, 0.045, 0.040, 'tail'),     # 16
    (1.04, 0.620, 0, 0.025, 0.060, 0.050, 'fin'),       # 17 fin base
    (1.17, 0.620, 0, 0.012, 0.030, 0.025, 'fin'),       # 18 tip
]

LEG = [('thighL', 0.095, 0.130), ('kneeL', 0.066, 0.075), ('hockL', 0.050, 0.055),
       ('ballL', 0.060, 0.040), ('toeL', 0.066, 0.034)]

# r03: the body sits lower on shorter, chunkier legs (hip-to-ground ~1.1x torso depth)
DZ = -0.06
for _k in list(J):
    if _k not in ('hockL', 'ballL', 'toeL'):
        _x, _y, _z = J[_k]
        J[_k] = (_x, _y, _z + (DZ * 0.5 if _k == 'kneeL' else DZ))
ST = [(s[0], s[1] + DZ) + tuple(s[2:]) for s in ST]
WING = [('shoulderL', 0.060, 0.075), ('armL', 0.048, 0.060), ('wristL', 0.048, 0.055),
        ('fingerL', 0.028, 0.085), ('tipL', 0.012, 0.030)]


def half_ring(st):
    y, z, th, w, up, dn, sh = st
    t = math.radians(th)
    u = Vector((0, math.sin(t), math.cos(t)))
    C = Vector((0, y, z))
    pts = [C + u * up]
    for ax, az in SH[sh]:
        h = az * up if az > 0 else az * dn
        p = C + u * h
        pts.append(Vector((ax * w, p.y, p.z)))
    pts.append(C - u * dn)
    return pts


def _frame(d):
    X, Z = Vector((1, 0, 0)), Vector((0, 0, 1))
    s = X - d * X.dot(d)
    if s.length < 0.3:
        s = Z - d * Z.dot(d)
    s.normalize()
    return s, d.cross(s).normalized()


def seg(bm, face, dprev, c, dn, hs, hf):
    """Extrude one limb face and place the new ring: a hs x hf rectangle centred on c,
    its plane normal dn; vertices keep their angular order (no twist)."""
    r = extrude(bm, [face])
    f = r['faces'][0]
    vs = list(f.verts)
    c0 = centre(vs)
    R = dprev.rotation_difference(dn)
    s, fa = _frame(dn)
    corners = [Vector(c) + s * hs * a + fa * hf * b for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    ang = lambda o: math.atan2(o.dot(fa), o.dot(s))
    va = sorted(vs, key=lambda v: ang(R @ (v.co - c0)))
    ca = sorted(corners, key=lambda p: ang(p - Vector(c)))
    best = min(range(4), key=lambda k: sum(abs(math.remainder(ang(R @ (va[i].co - c0)) - ang(ca[(i + k) % 4] - Vector(c)), 2 * math.pi)) for i in range(4)))
    for i in range(4):
        va[i].co = ca[(i + best) % 4]
    return f


def limb(bm, face, chain):
    n = face.normal.copy()
    if n.x < 0:
        n = -n
    pts = [face.calc_center_median()] + [Vector(J[j]) for j, _, _ in chain]
    dprev = n.normalized()
    for i, (j, hs, hf) in enumerate(chain, start=1):
        din = (pts[i] - pts[i - 1]).normalized()
        dn = din if i == len(chain) else (din + (pts[i + 1] - pts[i]).normalized()).normalized()
        face = seg(bm, face, dprev, pts[i], dn, hs, hf)
        dprev = dn
    return face


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, half_ring(st)) for st in ST]
    bands = [bridge(bm, rows[i], rows[i + 1]) for i in range(len(rows) - 1)]
    cap(bm, rows[0])
    cap(bm, rows[-1])
    recalc_normals(bm)
    limb(bm, bands[11][2], LEG)
    limb(bm, bands[9][1], WING)
    # feet flat on the ground
    for v in verts_where(bm, lambda c: c.z < 0.012 and c.x > 0.1):
        v.co.z = 0.0
    snap_seam(bm)
    return object_from_bm('body', bm)



EYE = Vector((0.152, -0.765, 1.196))          # socket centre: the upper skull side face, under the brow (after DZ)
META['keep_valleys'] = lambda c: (Vector((abs(c[0]), c[1], c[2])) - EYE).length < 0.07


def long_edge(bm, a, b):
    """The edge running along a limb between joints a and b (nearest the midpoint)."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    m = (a + b) / 2
    cand = [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized().dot(d)) > 0.7]
    return min(cand, key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2 - m).length)


def near_long(bm, a, b, t):
    """loopcut on the limb segment a->b, t measured from the a end."""
    e = long_edge(bm, a, b)
    v0 = min(e.verts, key=lambda v: (v.co - Vector(a)).length)
    return loopcut(bm, e, t=t, near=v0)


def stage2(k, body):
    bm = edit(body)
    L = [J[j] for j in ('thighL', 'kneeL', 'hockL', 'ballL')]
    with k.topo(bm, 'loop', 'knee: loop above the stifle so the thigh bends cleanly'):
        near_long(bm, L[0], L[1], 0.70)
    with k.topo(bm, 'loop', 'knee: loop below the stifle (knee = 3 loops)'):
        near_long(bm, L[1], L[2], 0.22)
    with k.topo(bm, 'loop', 'hock: loop above the reversed ankle'):
        near_long(bm, L[1], L[2], 0.80)
    with k.topo(bm, 'loop', 'wing: loop at the wrist knuckle, finger side'):
        near_long(bm, J['wristL'], J['fingerL'], 0.18)
    with k.topo(bm, 'loop', 'wing: loop at the shoulder so the wing can mantle'):
        near_long(bm, J['shoulderL'], J['armL'], 0.45)
    with k.topo(bm, 'loop', 'neck: extra loop mid-neck, the S bend'):
        r7 = half_ring(ST[7]); r8 = half_ring(ST[8])
        e = min(bm.edges, key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2 - (r7[2] + r8[2]) / 2).length)
        loopcut(bm, e, t=0.5)
    with k.topo(bm, 'socket', 'eye socket: a loop inside the skull side face'):
        f = face_near(bm, EYE, n=(1, 0, 0))
        inner = inset(bm, [f], 0.35, -0.010)
    # secondary shape: the brow overhangs the socket, the cheek is a plane
    r3, r4 = half_ring(ST[3]), half_ring(ST[4])
    for p in (r3[1], r4[1]):
        v = vert_near(bm, p)
        v.co.x += 0.018
        v.co.z += 0.008
    # the knee and hock read as joints: pinch the joint rings a touch front-to-back
    for j, s in (('kneeL', 0.92), ('hockL', 0.9)):
        vs = [v for v in bm.verts if (v.co - Vector(J[j])).length < 0.11]
        scale(vs, (1.0, s, s), pivot=J[j])
    snap_seam(bm)
    commit(body, bm)


PAL = {'plumage': '#2c3346', 'belly': '#454f68', 'membrane': '#6a3f9a', 'bill': '#1c1c22',
       'billtip': '#d8cfb8', 'eye': '#f0a020', 'shank': '#6e665e', 'horn': '#e4dcc8'}
DZV = Vector((0, 0, DZ))


def _pal(keys):
    return {k_: PAL[k_] for k_ in keys}


def tube(bm, pts, sizes, up=(0, 0, 1), tip=None, diamond=True):
    """A 4-sided tapered bar through pts (sizes = (side, up) half sizes); a cone tip if given.
    Returns the faces of the tip fan (the claw) for painting."""
    pts = [Vector(p) for p in pts]
    U = Vector(up)
    rows = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        s = d.cross(U)
        s = s.normalized() if s.length > 1e-4 else Vector((1, 0, 0))
        u = s.cross(d).normalized()
        a, b = sizes[i]
        crn = [(a, 0), (0, b), (-a, 0), (0, -b)] if diamond else [(a, b), (-a, b), (-a, -b), (a, -b)]
        rows.append(ring(bm, [p + s * x + u * y for x, y in crn]))
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1, closed=True)
    cap(bm, list(reversed(rows[0])))
    tipf = []
    if tip is not None:
        t = bm.verts.new(Vector(tip))
        r = rows[-1]
        tipf = [bm.faces.new([r[i], r[(i + 1) % 4], t]) for i in range(4)]
    else:
        cap(bm, rows[-1])
    return tipf


def bipyr(bm, c, n, r, front, back, sides=8, up=(0, 0, 1)):
    c, n = Vector(c), Vector(n).normalized()
    s = n.cross(Vector(up)).normalized(); u = s.cross(n).normalized()
    rw = ring(bm, [c + (s * math.cos(a) + u * math.sin(a)) * r for a in [2 * math.pi * i / sides for i in range(sides)]])
    f, b = bm.verts.new(c + n * front), bm.verts.new(c - n * back)
    for i in range(sides):
        bm.faces.new([rw[i], rw[(i + 1) % sides], f]); bm.faces.new([rw[(i + 1) % sides], rw[i], b])


def piece(name, bm, keys, rule=None, mirror=True):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, _pal(keys), rule or (lambda c, n, i: keys[0]))
    return ob


def stage3(k, body):
    def body_rule(c, n, i):
        if c.y < -0.99: return 'billtip'
        if c.y < -0.87: return 'bill'
        if c.z < 0.30 and abs(c.x) > 0.1: return 'shank'
        if n.z < -0.45 and c.z > 0.3 and abs(c.x) < 0.2: return 'belly'
        return 'plumage'
    paint(body, _pal(['plumage', 'belly', 'bill', 'billtip', 'shank']), body_rule)
    ebm = evaluated_bm(body)
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromBMesh(ebm)
    P = []
    # eyes: amber lens in the socket, a black pupil ahead and down, a pale highlight
    bm = edit(body)
    sock = face_near(bm, EYE, n=(1, 0, 0))
    ec, en = sock.calc_center_median().copy(), sock.normal.copy()
    bm.free()
    en = (en + Vector((0, -0.25, 0))).normalized()
    b = bmesh.new(); bipyr(b, ec + en * 0.012, en, 0.042, 0.018, 0.035)
    P.append(piece('eye', b, ['eye']))
    pc = ec + en * 0.026 + Vector((0, -0.010, -0.006))
    b = bmesh.new(); bipyr(b, pc, en, 0.022, 0.012, 0.012, sides=6)
    P.append(piece('pupil', b, ['bill']))
    b = bmesh.new(); bipyr(b, pc + en * 0.006 + Vector((0, -0.006, 0.011)), en, 0.007, 0.008, 0.006, sides=4)
    P.append(piece('glint', b, ['horn']))
    # brow: a dark bar, buried behind, front end low over the iris (determined)
    b = bmesh.new()
    tube(b, [ec + Vector((-0.035, 0.075, 0.040)), ec + Vector((-0.004, 0.0, 0.040)), ec + Vector((0.0, -0.055, 0.020))],
         [(0.020, 0.018), (0.024, 0.020), (0.012, 0.012)], up=(1, 0, 0.3))
    P.append(piece('brow', b, ['bill']))
    # horns: swept back off the skull
    b = bmesh.new()
    tube(b, [V(0.07, -0.66, 1.17), V(0.095, -0.58, 1.22), V(0.11, -0.49, 1.25)],
         [(0.034, 0.030), (0.028, 0.025), (0.018, 0.016)], tip=V(0.12, -0.38, 1.24))
    P.append(piece('horns', b, ['horn']))
    # throat hackles: three shaggy blades
    b = bmesh.new()
    for r_, t_, w_ in (((0.05, -0.63, 0.96), (0.075, -0.73, 0.82), 0.032), ((0.085, -0.60, 0.90), (0.13, -0.69, 0.77), 0.028),
                       ((0.05, -0.575, 0.82), (0.075, -0.66, 0.67), 0.026)):
        r_, t_ = V(r_), V(t_)
        tube(b, [r_, r_.lerp(t_, 0.45)], [(w_, 0.012), (w_ * 1.1, 0.012)], up=(1, 0, 0), tip=t_, diamond=False)
    P.append(piece('hackles', b, ['belly']))
    # graded dorsal spines on the midline
    b = bmesh.new()
    ys = [-0.40, -0.30, -0.18, -0.05, 0.08, 0.22, 0.38, 0.56, 0.74, 0.90]
    for i, y in enumerate(ys):
        hit = tree.ray_cast(V(0.001, y, 2.0), V(0, 0, -1))[0]
        z = hit.z if hit else 0.8
        h = 0.10 - 0.065 * i / (len(ys) - 1)
        L_, W_ = 0.45 * h + 0.012, 0.18 * h + 0.006
        base = [V(0, y - L_, z - 0.02), V(W_, y, z - 0.02), V(0, y + L_, z - 0.02), V(-W_, y, z - 0.02)]
        bv = ring(b, base); t = b.verts.new(V(0, y + 0.45 * h, z + h))
        for j in range(4):
            b.faces.new([bv[j], bv[(j + 1) % 4], t])
        b.faces.new(list(reversed(bv)))
    P.append(piece('spines', b, ['membrane'], mirror=False))
    # tail fin: a leaf around the tail tip
    b = bmesh.new()
    ol = ring(b, [V(0, 0.93, 0.545), V(0, 1.08, 0.69), V(0, 1.18, 0.64), V(0, 1.33, 0.53), V(0, 1.18, 0.44), V(0, 1.08, 0.40)])
    cp, cm = b.verts.new(V(0.034, 1.10, 0.54)), b.verts.new(V(-0.034, 1.10, 0.54))
    for j in range(6):
        b.faces.new([ol[j], ol[(j + 1) % 6], cp]); b.faces.new([ol[(j + 1) % 6], ol[j], cm])
    P.append(piece('fin', b, ['membrane'], mirror=False))
    # folded membrane: a thick sail under the wing arm and finger blade
    OL = [(0.275, -0.23, 1.05), (0.30, 0.12, 0.97), (0.296, 0.45, 0.74), (0.30, 0.32, 0.64), (0.30, 0.20, 0.70),
          (0.295, 0.06, 0.73), (0.29, -0.05, 0.80), (0.28, -0.21, 0.86), (0.285, -0.23, 0.95)]
    # a lens: the rim is one ring, the belly of the sail bulges +-2 cm (no thin side walls = no needles)
    b = bmesh.new()
    rim = ring(b, [V(p) + DZV for p in OL])
    co, ci = b.verts.new(V(0.318, 0.10, 0.88 + DZ)), b.verts.new(V(0.282, 0.10, 0.88 + DZ))
    n_ = len(OL)
    for j_ in range(n_):
        b.faces.new([rim[j_], rim[(j_ + 1) % n_], co]); b.faces.new([rim[(j_ + 1) % n_], rim[j_], ci])
    P.append(piece('membrane', b, ['membrane']))
    # finger spars on the sail: segmented so no facet is a needle; one object each (one contact each)
    W_ = V(0.287, -0.225, 1.05 + DZ)
    for si, tip_ in enumerate(((0.312, 0.32, 0.645 + DZ), (0.305, 0.06, 0.735 + DZ))):
        tip_ = V(tip_)
        nseg = max(3, int((tip_ - W_).length / 0.09))
        pts = [W_.lerp(tip_, q / (nseg + 1)) for q in range(nseg + 1)]
        szs = [(0.018 - 0.008 * q / nseg,) * 2 for q in range(nseg + 1)]
        b = bmesh.new()
        tube(b, pts, szs, up=(1, 0, 0), tip=tip_)
        P.append(piece('spar%d' % (si + 1), b, ['plumage']))
    b = bmesh.new()
    claw = tube(b, [V(0.285, -0.245, 1.05 + DZ), V(0.292, -0.30, 1.075 + DZ)], [(0.018, 0.018), (0.012, 0.012)],
                up=(1, 0, 0), tip=V(0.292, -0.345, 1.055 + DZ))
    P.append(piece('thumb', b, ['horn']))
    # toes with talons: three forward, one back
    b = bmesh.new(); claws = []
    for r_ in ([(0.215, -0.08, 0.03), (0.215, -0.17, 0.028), (0.215, -0.23, 0.02)],
               [(0.235, -0.08, 0.03), (0.275, -0.16, 0.028), (0.30, -0.21, 0.02)],
               [(0.195, -0.08, 0.03), (0.16, -0.16, 0.028), (0.14, -0.21, 0.02)],
               [(0.215, -0.01, 0.032), (0.215, 0.07, 0.026)]):
        d = (V(r_[-1]) - V(r_[-2])).normalized()
        tp = V(r_[-1]) + d * 0.045 + V(0, 0, -0.014)
        sz = [(0.022, 0.020), (0.018, 0.016), (0.014, 0.012)][:len(r_)]
        claws += tube(b, [V(p) for p in r_], sz, tip=tp)
    b.faces.index_update(); ci_ = {f.index for f in claws}
    P.append(piece('toes', b, ['shank', 'bill'], rule=lambda c, n, i: 'bill' if i in ci_ else 'shank'))
    ebm.free()
    return P


def stage4(k, body, pieces):
    j = lambda n_: Vector(J[n_])
    rig = armature([
        ('hips', J['hip'], J['belly'], None),
        ('chest', J['belly'], J['neckb'], 'hips', True),
        ('neck', J['neckb'], J['neckt'], 'chest', True),
        ('head', J['neckt'], J['bill'], 'neck', True),
        ('tail1', J['tail0'], J['tail1'], 'hips'),
        ('tail2', J['tail1'], J['tail2'], 'tail1', True),
        ('tail3', J['tail2'], J['tail3'], 'tail2', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L', True),
        ('foot.L', J['hockL'], J['ballL'], 'shin.L', True),
        ('toe.L', J['ballL'], J['toeL'], 'foot.L', True),
        ('wing.L', tuple(j('shoulderL') + Vector((-0.10, 0.0, -0.02))), J['wristL'], 'chest'),
        ('hand.L', J['wristL'], J['tipL'], 'wing.L', True),
    ], roll='auto')
    skin(body, rig)
    sail = next(p for p in pieces if p.name == 'piece_membrane')
    for p in pieces:        # spars ride the sail's own weights (they lie on it); everything else the skin's
        if not p.name.startswith('piece_spar'):
            bind(p, rig, body=body)
    root = Vector((0.287, -0.225, 1.05 + DZ))
    grab = lambda ob: [{ob.vertex_groups[g.group].name: g.weight for g in v.groups} for v in ob.data.vertices]
    for p in pieces:        # spar root: the wrist skin; spar length: the sail it lies on (blend over 0.3 m)
        if not p.name.startswith('piece_spar'):
            continue
        bind(p, rig, body=body); wb = grab(p)
        p.modifiers.remove(p.modifiers['armature'])
        bind(p, rig, body=sail); ws = grab(p)
        p.vertex_groups.clear()
        for i, v in enumerate(p.data.vertices):
            w_co = p.matrix_world @ v.co
            w_co.x = abs(w_co.x)                  # both sides (the mirror is applied)
            t = min(1.0, max(0.0, (w_co - root).length / 0.30))
            mix = {}
            for g_, w_ in wb[i].items(): mix[g_] = mix.get(g_, 0) + (1 - t) * w_
            for g_, w_ in ws[i].items(): mix[g_] = mix.get(g_, 0) + t * w_
            for g_, w_ in mix.items():
                if w_ > 1e-4:
                    (p.vertex_groups.get(g_) or p.vertex_groups.new(name=g_)).add([i], w_, 'REPLACE')
    clip(rig, 'idle', {1: {}, 16: {'chest': (3, 0, 0), 'neck': (-3, 0, 0), 'head': (0, 8, 0)},
                       32: {'chest': (-1, 0, 0), 'head': (0, -6, 0)}, 48: {}})
    W = {1: (20, 0, 0, 0, 0, -20, 0, 0), 9: (0, 0, 0, 0, 0, 0, 25, -20), 17: (-20, 0, 0, 0, 0, 20, 0, 0),
         25: (0, 25, -20, 0, 0, 0, 0, 0), 33: (20, 0, 0, 0, 0, -20, 0, 0)}
    mv = {}
    for f, (tl, sl, fl, _, __, tr, sr, fr) in W.items():
        bob = 5 if f in (1, 17, 33) else -5
        mv[f] = {'thigh.L': (tl, 0, 0), 'shin.L': (sl, 0, 0), 'foot.L': (fl, 0, 0),
                 'thigh.R': (tr, 0, 0), 'shin.R': (sr, 0, 0), 'foot.R': (fr, 0, 0),
                 'neck': (bob, 0, 0), 'head': (-bob, 0, 0), 'tail1': (0, 0, 5 if f in (1, 33) else (-5 if f == 17 else 0))}
    clip(rig, 'move', mv)
    clip(rig, 'attack', {1: {}, 12: {'neck': (-14, 0, 0), 'head': (8, 0, 0), 'chest': (4, 0, 0),
                                     'wing.L': (0, 0, -18), 'wing.R': (0, 0, 18), 'hand.L': (18, 0, 0), 'hand.R': (18, 0, 0)},
                         20: {'neck': (22, 0, 0), 'head': (-8, 0, 0), 'chest': (-6, 0, 0),
                              'wing.L': (0, 0, -22), 'wing.R': (0, 0, 22), 'hand.L': (25, 0, 0), 'hand.R': (25, 0, 0)},
                         30: {'neck': (6, 0, 0), 'wing.L': (0, 0, -8), 'wing.R': (0, 0, 8)}, 40: {}})
    return rig


run(META, stage1, globals().get('stage2'), globals().get('stage3'), globals().get('stage4'))
