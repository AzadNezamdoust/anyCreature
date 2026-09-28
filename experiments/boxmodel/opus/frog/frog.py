"""Frog: a squat sitting stylised game frog, box-modelled in four stages.

Stage 1 is one stack of 8-point half rings running along the body (snout ->
rump; top seam -> side -> belly seam), tilted up at the front. The eye domes,
front legs and hind legs are swept out of sockets left open in that stack, so
the base is one closed mirrored shell: eye domes rise from 2x2 sockets on the
skull, the short front legs drop from the chest and end in a flat hand that
splits into four toes; the hind legs fold in a Z along the flank (thigh
forward, shin back, long foot forward) and end in a wide webbed foot that
splits into five toes.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *
from mathutils import Quaternion, Matrix, Euler
import mathutils.kdtree

META = dict(creature='frog', model='opus', engine_glb='')

# the skeleton the model is built on (left side, x >= 0; the frog faces -Y)
J = dict(
    pelvis=(0.0, 0.12, 0.10), spine=(0.0, 0.03, 0.14), chest=(0.0, -0.05, 0.155),
    head=(0.0, -0.09, 0.17), snout=(0.0, -0.262, 0.19),
    jaw=(0.0, -0.08, 0.15), chin=(0.0, -0.25, 0.165),
    throat=(0.0, -0.13, 0.15), throat_lo=(0.0, -0.13, 0.115),
    eye=(0.105, -0.145, 0.25), eyetop=(0.12, -0.145, 0.335),
    shoulder=(0.105, -0.025, 0.115), elbow=(0.132, -0.075, 0.062), wrist=(0.143, -0.112, 0.032),
    palm=(0.148, -0.137, 0.015), knuckle=(0.15, -0.162, 0.013), fingertip=(0.15, -0.215, 0.008),
    hip=(0.09, 0.122, 0.072), knee=(0.225, -0.078, 0.074), ankle=(0.252, 0.11, 0.04),
    heel=(0.272, 0.152, 0.03), ball=(0.325, 0.0, 0.012), toetip=(0.34, -0.075, 0.008),
)

# ---------------------------------------------------------------- the stack
# 8 points per half ring: 0 top seam, 1 back, 2 dorsolateral ridge, 3 upper
# side, 4 mouth line / mid flank, 5 jaw / lower flank, 6 belly side, 7 belly seam
RINGS = [  # name, y, z top, z bottom, half width, z of the widest point
    ('S0', -0.258, 0.205, 0.160, 0.080, 0.180),
    ('S1', -0.238, 0.229, 0.146, 0.118, 0.178),
    ('E0', -0.185, 0.247, 0.128, 0.142, 0.178),
    ('E1', -0.145, 0.254, 0.117, 0.150, 0.176),
    ('E2', -0.105, 0.255, 0.107, 0.150, 0.172),
    ('N',  -0.055, 0.252, 0.093, 0.130, 0.160),   # behind the head: a slight waist
    ('B0',  0.000, 0.250, 0.078, 0.138, 0.150),
    ('B1',  0.048, 0.238, 0.056, 0.136, 0.135),   # the belly swells
    ('B2',  0.095, 0.218, 0.036, 0.122, 0.118),
    ('B3',  0.138, 0.188, 0.024, 0.100, 0.104),
    ('B4',  0.172, 0.150, 0.020, 0.074, 0.090),
    ('B5',  0.196, 0.108, 0.030, 0.042, 0.075),
]


def sec(y, zt, zb, w, zw):
    return [(0.0, y, zt),
            (0.50 * w, y, zt - 0.08 * (zt - zw)),
            (0.86 * w, y, zw + 0.55 * (zt - zw)),
            (1.00 * w, y, zw + 0.15 * (zt - zw)),
            (0.98 * w, y, zw - 0.12 * (zw - zb)),
            (0.82 * w, y, zb + 0.45 * (zw - zb)),
            (0.45 * w, y, zb + 0.06 * (zw - zb)),
            (0.0, y, zb)]


# sockets: faces NOT created in the band that starts at a ring (cols)
SKIP = {'E0': {1, 2}, 'E1': {1, 2},        # eye dome (2x2; E1 col 2 goes)
        'N': {4, 5},                         # front leg
        'B2': {4, 5}}                        # hind leg


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def tube(bm, loop, secs, W0, cap=None, roundt=False):
    """Sweep a socket loop through sections. secs: [(centre, r, D, f)] where r
    is a radius (or (rw, rt) along the transported frame) and the section is
    squashed by f along the world direction D (projected into its plane).
    Frames are parallel-transported, so the loop's own shape rides along."""
    C0 = centre(loop)
    pts = [C0] + [Vector(s[0]) for s in secs]
    A = (pts[1] - pts[0]).normalized()
    W = Vector(W0)
    W = (W - A * W.dot(A)).normalized()
    T = W.cross(A)
    tm = [((v.co - C0).dot(W), (v.co - C0).dot(T)) for v in loop]
    mw = max(abs(a) for a, b in tm) or 1
    mt = max(abs(b) for a, b in tm) or 1
    tm = [(a / mw, b / mt) for a, b in tm]
    if roundt:                                  # the loop's angles on a circle (an octagon, not a box)
        tm = [(a / math.hypot(a, b), b / math.hypot(a, b)) for a, b in tm]
    rings = [list(loop)]
    Ap = A
    for i, (C, r, D, f) in enumerate(secs):
        C = Vector(C)
        nxt = pts[i + 2] if i + 2 < len(pts) else C + (C - pts[i])
        An = (nxt - pts[i]).normalized()
        W = Ap.rotation_difference(An) @ W
        W = (W - An * W.dot(An)).normalized()
        T = W.cross(An)
        Ap = An
        rw, rt = (r, r) if isinstance(r, (int, float)) else r
        Dp = None
        if D is not None:
            Dv = Vector(D)
            Dp = Dv - An * Dv.dot(An)
            Dp = Dp.normalized() if Dp.length > 1e-6 else None
        P = []
        for a, b in tm:
            d = W * a * rw + T * b * rt
            if Dp is not None:
                d = d + Dp * d.dot(Dp) * (f - 1)
            P.append(C + d)
        rg = ring(bm, P)
        bridge(bm, rings[-1], rg, closed=True)
        rings.append(rg)
    if cap == 'face':
        bm.faces.new(rings[-1])
    elif cap is not None:
        v = bm.verts.new(Vector(cap))
        R = rings[-1]
        for i in range(len(R)):
            bm.faces.new([R[i], R[(i + 1) % len(R)], v])
    return rings, (W, T, Ap)


def zip_rings(bm, A, B, C, W, T):
    """Join a ring to one with more vertices (a flat-shaded 6 -> 10 / 12
    reduction): walk both by angle round C in the (W, T) plane; quads where
    the two rings line up, triangles where the wider ring has an extra vertex."""
    def ang(v):
        d = v.co - C
        return math.atan2(d.dot(T), d.dot(W))

    def orient(R):
        s = 0.0
        for i in range(len(R)):
            p, q = R[i].co - C, R[(i + 1) % len(R)].co - C
            s += p.dot(W) * q.dot(T) - p.dot(T) * q.dot(W)
        return s
    B = list(B)
    if orient(A) * orient(B) < 0:
        B.reverse()
    sg = 1 if orient(A) > 0 else -1
    a0 = ang(A[0])
    tau = 2 * math.pi

    def rel(v):
        return ((ang(v) - a0) * sg) % tau
    j0 = min(range(len(B)), key=lambda j: min(rel(B[j]), tau - rel(B[j])))
    B = B[j0:] + B[:j0]
    n, m = len(A), len(B)
    ra = [rel(A[i]) for i in range(n)] + [tau]
    rb = [rel(B[j]) for j in range(m)]
    if rb[0] > math.pi:
        rb[0] -= tau
    rb.append(tau + rb[0])
    i = j = 0
    while i < n or j < m:
        if i < n and j < m and abs(ra[i + 1] - rb[j + 1]) < 0.15:
            bm.faces.new([A[i], A[(i + 1) % n], B[(j + 1) % m], B[j]]); i += 1; j += 1
        elif j >= m or (i < n and ra[i + 1] < rb[j + 1]):
            bm.faces.new([A[i], A[(i + 1) % n], B[j % m]]); i += 1
        else:
            bm.faces.new([A[i % n], B[(j + 1) % m], B[j]]); j += 1


LEG = []    # stage 1 -> 2 -> 4: (section label, vertex positions) of every hind-leg ring
TIPS = []   # (tip centre, direction, up, size) of every toe, for the stage-3 pads


def toe(bm, slot, d, segs, up=(0, 0, 1)):
    """A toe from a quad slot: segs = [(advance, thick, wide, dz)], blunt tip."""
    C = centre(slot)
    A = Vector(d).normalized()
    secs = []
    for adv, th, wd, dz in segs:
        C = C + A * adv + Vector((0, 0, dz))
        secs.append((C.copy(), (th, wd), None, 1.0))
    rings, (W, T, An) = tube(bm, slot, secs, up, cap='face')
    TIPS.append((centre(rings[-1]).copy(), An.copy(), W.copy(), segs[-1][2]))
    return rings


def eye_dome():
    loop = [RP('E0', 1), RP('E0', 2), RP('E0', 3), RP('E1', 3), RP('E2', 3), RP('E2', 2), RP('E2', 1), RP('E1', 1)]
    return dict(c=sum((Vector(p) for p in loop), Vector()) / 8)


def build_eye(bm, R):
    loop = [R['E0'][1], R['E0'][2], R['E0'][3], R['E1'][3], R['E2'][3], R['E2'][2], R['E2'][1], R['E1'][1]]
    C = centre(loop)
    X, Z = Vector((1, 0, 0)), Vector((0, 0, 1))
    secs = [(C + X * 0.008 + Z * 0.024, 0.052, None, 1.0),    # the bulge: a ball, wider than its socket
            (C + X * 0.016 + Z * 0.052, 0.056, None, 1.0),    # its equator, out past the head's side
            (C + X * 0.018 + Z * 0.077, 0.036, None, 1.0)]
    tube(bm, loop, secs, (0, 1, 0), cap=C + X * 0.018 + Z * 0.087, roundt=True)


def build_arm(bm, R):
    loop = [R['N'][4], R['N'][5], R['N'][6], R['B0'][6], R['B0'][5], R['B0'][4]]
    sh, el, wr = (Vector(J[n]) for n in ('shoulder', 'elbow', 'wrist'))
    secs = [(lerp(sh, el, 0.25) + Vector((0.01, 0, 0)), 0.040, None, 1.0),    # shoulder
            (el, 0.030, (0, 1, 0), 0.85),                                    # elbow
            (lerp(el, wr, 0.55), 0.029, None, 1.0),                          # forearm: chunky
            (wr, 0.022, (0, 0, 1), 0.8)]                                     # wrist
    rings, (W, T, A) = tube(bm, loop, secs, (0, 1, 0))
    # the hand: a flat block, palm ring (10: top row outer->inner, bottom row inner->outer)
    def hand_ring(c, hw, zt, zb):
        c = Vector(c)
        xs = [1, 0.5, 0, -0.5, -1]
        top = [(c.x + hw * s, c.y, zt) for s in xs]
        bot = [(c.x - hw * s, c.y, zb) for s in xs]
        return ring(bm, top + bot)
    P = hand_ring(J['palm'], 0.036, 0.032, 0.002)
    zip_rings(bm, rings[-1], P, Vector(J['palm']), Vector((1, 0, 0)), Vector((0, 0, 1)))
    Kr = hand_ring(J['knuckle'], 0.048, 0.024, 0.002)
    bridge(bm, P, Kr, closed=True)
    dirs = [(0.60, -0.8, 0), (0.18, -1, 0), (-0.18, -1, 0), (-0.55, -0.85, 0)]
    for j in range(4):
        slot = [Kr[j], Kr[j + 1], Kr[8 - j], Kr[9 - j]]
        toe(bm, slot, dirs[j], [(0.024, 0.009, 0.010, 0.0), (0.022, 0.008, 0.009, -0.003)])


def build_leg(bm, R):
    loop = [R['B2'][4], R['B2'][5], R['B2'][6], R['B3'][6], R['B3'][5], R['B3'][4]]
    X, Z = (1, 0, 0), (0, 0, 1)
    secs = [((0.150, 0.100, 0.096), 0.046, X, 0.95),    # thigh root
            ((0.200, 0.035, 0.130), 0.052, X, 0.85),    # thigh: the fat drumstick
            ((0.215, -0.028, 0.124), 0.038, X, 0.9),
            ((0.222, -0.062, 0.098), 0.034, X, 0.9),    # over the knee
            ((0.225, -0.078, 0.074), 0.030, None, 1.0),  # knee
            ((0.230, -0.052, 0.052), 0.024, None, 1.0),  # under the knee
            ((0.242, 0.030, 0.047), 0.021, None, 1.0),   # shin
            (J['ankle'], 0.020, None, 1.0),              # ankle
            (J['heel'], 0.019, Z, 0.8),                  # heel
            ((0.300, 0.118, 0.016), 0.028, Z, 0.45),     # foot
            ((0.314, 0.058, 0.013), 0.036, Z, 0.35)]
    rings, (W, T, A) = tube(bm, loop, secs, (0, 0, 1), roundt=True)
    LEG.clear()                                     # stage 4 weights the leg ring by ring (not by bone heat)
    for i, rg in enumerate(rings[1:]):
        LEG.append(('s%d' % i, [v.co.copy() for v in rg]))
    c = Vector(J['ball'])
    xs = [1, 0.6, 0.2, -0.2, -0.6, -1]
    hw = 0.055
    top = [(c.x + hw * s, c.y, 0.022) for s in xs]
    bot = [(c.x - hw * s, c.y, 0.002) for s in xs]
    P = ring(bm, top + bot)
    zip_rings(bm, rings[-1], P, c, Vector((1, 0, 0)), Vector((0, 0, 1)))
    dirs = [(0.75, -0.65, 0), (0.35, -0.95, 0), (0.05, -1, 0), (-0.25, -0.97, 0), (-0.55, -0.85, 0)]
    for j in range(5):
        slot = [P[j], P[j + 1], P[10 - j], P[11 - j]]
        L = (0.85, 1.0, 1.1, 1.0, 0.8)[j]
        tr = toe(bm, slot, dirs[j], [(0.032 * L, 0.008, 0.010, 0.0), (0.030 * L, 0.007, 0.009, -0.002)])
        LEG.append(('t1', [v.co.copy() for v in tr[1]])); LEG.append(('t2', [v.co.copy() for v in tr[2]]))
    LEG.append(('P', [v.co.copy() for v in P]))


def stage1(k):
    bm = bmesh.new()
    R = {}
    for name, *p in RINGS:
        R[name] = ring(bm, sec(*p))
    names = [n for n, *_ in RINGS]
    for a, b in zip(names, names[1:]):
        r0, r1 = R[a], R[b]
        for i in range(7):
            if i not in SKIP.get(a, ()):
                bm.faces.new([r0[i], r0[i + 1], r1[i + 1], r1[i]])
    bm.verts.remove(R['E1'][2])
    # snout: the front cap, split at the mouth line by a seam vertex
    S = R['S0']
    M = bm.verts.new(Vector((0.0, -0.266, S[4].co.z)))
    for f in ([S[0], S[1], S[2], M], [M, S[2], S[3], S[4]], [M, S[4], S[5], S[6]], [M, S[6], S[7]]):
        bm.faces.new(f)
    Bk = R['B5']                                   # rump: a blunt fan round the vent, not a flat end cap
    V = bm.verts.new(Vector((0.0, 0.214, 0.062)))
    for i in range(7):
        bm.faces.new([Bk[i], Bk[i + 1], V])
    build_eye(bm, R)
    build_arm(bm, R)
    build_leg(bm, R)
    ob = object_from_bm('body', bm)
    hits(ob)
    return ob


def hits(ob):
    if os.environ.get('FROG_DBG'):
        b2 = evaluated_bm(ob); b2.faces.ensure_lookup_table()
        t = BVHTree.FromBMesh(b2)
        for i, j in t.overlap(t):
            if i < j and not (set(b2.faces[i].verts) & set(b2.faces[j].verts)):
                say('HIT', tuple(round(x, 3) for x in b2.faces[i].calc_center_median()), tuple(round(x, 3) for x in b2.faces[j].calc_center_median()))



# ---------------------------------------------------------------- stage 2
def RP(name, col):
    """The locked stage-1 position of a stack point."""
    r = next(x for x in RINGS if x[0] == name)
    return sec(*r[1:])[col]


SPOTS = []   # stage 2 -> stage 3: centres of the spot insets (and ('drum', centre))


def centre_of(P):
    return sum(P, Vector()) / len(P)


HIP = {}     # stage 2 -> stage 4: body stack positions and the hip loop, for the hip weight blend
MOUTH = {}   # stage 2 -> stage 3: the lip line and the loop under it (positions)


def edge_of(a, b):
    return next(e for e in a.link_edges if e.other_vert(a) is b)


def flat_sym(verts):
    """flatten() for a plane that crosses the mirror seam: the best plane containing
    the X axis (fit in y-z), so seam vertices stay on x = 0."""
    P = np.array([(v.co.y, v.co.z) for v in verts])
    c = P.mean(axis=0)
    n = np.linalg.svd(P - c)[2][-1]
    for v in verts:
        q = np.array((v.co.y, v.co.z))
        q = q - np.dot(q - c, n) * n
        v.co.y, v.co.z = float(q[0]), float(q[1])


SHANK = tuple(float(x) for x in os.environ.get('FROG_SHANK', '1.3,1.3,1.15').split(','))


def stage2(k, body):
    bm = edit(body)
    vs = lambda n, c: vert_near(bm, RP(n, c))
    SV = {(n, c): vs(n, c) for n in ('N', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5') for c in range(8)}
    SV[('V', 0)] = vert_near(bm, (0.0, 0.214, 0.062))
    S0v = {c: vs('S0', c) for c in range(8)}      # captured before any move (cols 3-4 are 6 mm apart)
    M = vert_near(bm, (0.0, -0.266, RP('S0', 4)[2]))
    LEGV = []                                       # the leg rings as vertices: they are followed through the moves
    for lab, P_ in LEG:
        vv = [vert_near(bm, p) for p in P_]
        assert max((v.co - p).length for v, p in zip(vv, P_)) < 1e-5, lab
        LEGV.append((lab, vv))
    # --- head planes: the cheek is one flat side plane from the snout to behind the eye (before
    #     the lip moves, so the lip still overhangs it); the snout top slopes down to the nose
    flatten([vs(n, c) for n in ('S1', 'E0', 'E1', 'E2') for c in (3, 4)])
    for c, dz in ((0, -0.010), (1, -0.010), (2, -0.005)):
        vs('S0', c).co.z += dz
    for c, dz in ((0, -0.006), (1, -0.006)):
        vs('S1', c).co.z += dz
    # --- the mouth: a partial loop just under the lip line, from the snout to the corner
    start = edge_of(M, vs('S0', 6))
    end = edge_of(vs('E2', 4), vs('E2', 5))
    with k.topo(bm, 'partial_loop', 'mouth: a loop under the lip line from the snout to the corner, '
                'terminated in the snout cap and at the corner (a thin band for the mouth colour and the jaw)'):
        ms = partial_loop(bm, start, end, t=0.22, near=M, terminate='fan')
    lip = [M] + [vs(n, 4) for n in ('S0', 'S1', 'E0', 'E1', 'E2')]
    for v in ms:                                   # the lower lip tucks in under the upper
        d = Vector((v.co.x, 0.0, 0.0))
        v.co += Vector((-0.10 * v.co.x, 0.0, -0.002))
    for v in lip[1:]:                              # the upper lip overhangs
        v.co += Vector((0.006, 0.0, 0.0)) if v.co.x > 0.05 else Vector((0.0, -0.004, 0.0))
    M.co.y -= 0.004
    # --- r105: the snout cap fans from M (on the seam, 8 cm away) to cols 2-5, which spanned only
    #     ~7 deg seen from M, so each quad split into needles. Open the fan (col 2 up, col 3 up,
    #     col 5 down) and slide the loop's snout vertex along S4-S5 to the angular midpoint.
    S0v[2].co.z += 0.008; S0v[3].co.z += 0.0045; S0v[5].co.z -= 0.007
    s4, s5 = S0v[4].co.copy(), S0v[5].co.copy()
    mv = min(ms, key=lambda v: (v.co - s4).length)
    ang = lambda a, b: (a - M.co).angle(b - M.co, 0.0)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        t = (lo + hi) / 2
        if ang(s4, s4.lerp(s5, t)) < ang(s4.lerp(s5, t), s5):
            lo = t
        else:
            hi = t
    mv.co = s4.lerp(s5, lo)
    MOUTH['pale_extra'] = [S0v[5].co.copy()]
    # --- the eye dome's top: round the flat turret lid (top ring out and up, apex up)
    ED0 = eye_dome()['c']
    top_c = ED0 + Vector((0.018, 0.0, 0.077))
    top = verts_where(bm, lambda c: abs(c.z - top_c.z) < 0.008 and (c - top_c).length < 0.045)
    for v in top:
        d = v.co - top_c
        v.co = top_c + Vector((d.x * 1.25, d.y * 1.25, d.z)) + Vector((0.0, 0.0, 0.004))
    vert_near(bm, ED0 + Vector((0.018, 0.0, 0.087))).co.z = ED0.z + 0.104
    # --- the eye: a socket (inset) in the two outer-front faces of the dome's equator bands
    ED = eye_dome()
    look = Vector((0.80, -0.58, 0.12)).normalized()
    fs = []
    for zc in (ED['c'].z + 0.038, ED['c'].z + 0.066):
        p = Vector((ED['c'].x + 0.016, ED['c'].y, zc)) + look * 0.05
        fs.append(face_near(bm, p, n=look))
    MOUTH['eye'] = [[v.co.copy() for v in f.verts] for f in fs]
    # r137: the eye-socket inset is gone (the gold ball covers the dome front; its 16 small faces per
    #       side made the head read dense)
    # --- the hip: a second loop at the thigh root, so the hop can swing the thigh without tearing
    h4 = vs('B2', 4)
    stack = [Vector(p) for r in RINGS for p in sec(*r[1:])]
    he = next(e for e in h4.link_edges if min((e.other_vert(h4).co - p).length for p in stack) > 1e-3)
    with k.topo(bm, 'loop', 'hip loop: the socket -> thigh-root band gets a middle ring for the hop'):
        hl = loopcut(bm, he, t=0.5, near=h4)
    hc = centre(hl)
    for v in hl:                                    # eased outward: the haunch grows out of the body
        v.co += Vector((0.004, 0.0, 0.0))
    # --- the thigh tapers from the haunch to the knee (knee ~60% of the hip loop): the two rings
    #     between the drumstick and the knee pulled in toward their centres
    tp = [Vector(p) for p in ((0.200, 0.035, 0.130), (0.215, -0.028, 0.124), (0.222, -0.062, 0.098), (0.225, -0.078, 0.074))]
    for i, k_ in ((1, 0.84), (2, 0.86)):
        A = (tp[i + 1] - tp[i - 1]).normalized()
        rv = verts_where(bm, lambda c: abs((c - tp[i]).dot(A)) < 0.004 and (c - tp[i]).length < 0.06)
        say('TAPER ring', i, len(rv))
        if len(rv) == 6:
            for v in rv:
                v.co = tp[i] + (v.co - tp[i]) * k_
    # --- r103: the lower leg's rings (under the knee -> the foot) carry the socket loop's uneven
    #     angles, so one column is 6-9 mm wide on 7-8 cm faces (needles). Even the angles out in
    #     each ring's own plane (the flat foot rings are un-squashed first, then squashed back).
    path = [Vector(p) for p in ((0.225, -0.078, 0.074), (0.230, -0.052, 0.052), (0.242, 0.030, 0.047), J['ankle'],
                                J['heel'], (0.300, 0.118, 0.016), (0.314, 0.058, 0.013), J['ball'])]
    squash = [None, 1.0, 1.0, 1.0, 0.8, 0.45, 0.35]
    for i in range(1, 7):
        C, A = path[i], (path[i + 1] - path[i - 1]).normalized()
        rv = verts_where(bm, lambda c: abs((c - C).dot(A)) < 0.004 and (c - C).length < 0.045)
        if len(rv) != 6:
            say('EVEN ring', i, 'skipped', len(rv)); continue
        f_ = squash[i]
        Dz = Vector((0, 0, 1)) - A * A.z
        Dz.normalize()
        Q_ = A.cross(Dz)
        pol = []
        for v in rv:
            d = v.co - C
            a, b = d.dot(Q_), d.dot(Dz) / f_
            pol.append((math.atan2(b, a), math.hypot(a, b), v))
        pol.sort(key=lambda t: t[0])
        ph = math.atan2(sum(math.sin(t[0] - j * math.pi / 3) for j, t in enumerate(pol)),
                        sum(math.cos(t[0] - j * math.pi / 3) for j, t in enumerate(pol)))
        for j, (_, r, v) in enumerate(pol):
            t = ph + j * math.pi / 3
            v.co = C + (v.co - C).dot(A) * A + Q_ * (r * math.cos(t)) + Dz * (r * math.sin(t) * f_)
    # --- r132: the shank read as a thin rod once the hop unfolds it (r .021 against the thigh's
    #     .052): its rings swell 30% (the ankle 15%), still tucked under the thigh at rest
    for lab, vv in LEGV:
        f_ = {'s5': SHANK[0], 's6': SHANK[1], 's7': SHANK[2]}.get(lab)
        if f_:
            C = centre(vv)
            for v in vv:
                v.co = C + (v.co - C) * f_
    # --- the crown: one flat plane between the eyes, from the snout top to behind the eyes
    flat_sym([vs(n, c) for n in ('S1', 'E0', 'E1', 'E2') for c in (0, 1)])
    # --- the dorsolateral ridge: a crease from behind the eye to the hip, a flat back between
    for n, lift in (('E2', 0.003), ('N', 0.006), ('B0', 0.007), ('B1', 0.007), ('B2', 0.006), ('B3', 0.004)):
        vs(n, 2).co += Vector((0.004, 0.0, lift))
        if n != 'E2':
            vs(n, 1).co.z -= 0.004
            vs(n, 0).co.z -= 0.002
    # --- back planes: a flat back plate across the spine (cols 0-1) and a flat flank plate
    #     (cols 2-3) on each of the front and rear halves; the plane changes run on edge loops
    flat_sym([vs(n, c) for n in ('N', 'B0', 'B1') for c in (0, 1)])
    flat_sym([vs(n, c) for n in ('B2', 'B3', 'B4') for c in (0, 1)])
    flatten([vs(n, c) for n in ('N', 'B0', 'B1') for c in (2, 3)])
    flatten([vs(n, c) for n in ('B2', 'B3') for c in (2, 3)] + [vs('B4', 2)])
    # --- spots and the ear drum: insets (loops inside one face) replace the old decal plates.
    #     Each spot's inner quad is turned and scaled unevenly so none reads as a rectangle.
    def band_face(a, b, c):
        q = {vs(a, c), vs(a, c + 1), vs(b, c), vs(b, c + 1)}
        return next(f for f in vs(a, c).link_faces if q <= set(f.verts))

    def shaped_inset(f, amount, depth, turn, sc):
        n = f.normal.copy()
        (inner,) = inset(bm, [f], amount, depth=depth)
        c = inner.calc_center_median()
        for v, s_ in zip(inner.verts, sc):
            d = Quaternion(n, math.radians(turn)) @ (v.co - c)
            v.co = c + d * s_
        return [v.co.copy() for v in inner.verts]

    # r135: the spot insets (topo #4) are gone: they read as windows. Spots are painted on whole
    #       body faces in stage 3 (SPOT_FACES)
    SPOTS.clear(); HIP['flat'] = []
    fd = band_face('E2', 'N', 2)
    with k.topo(bm, 'inset', 'ear drum: a loop inside the face behind the eye dome, sunk 2 mm (the rim reads)'):
        P_ = shaped_inset(fd, 0.30, -0.002, 0, (1.0, 1.0, 1.0, 1.0))
        SPOTS.append(('drum', centre_of(P_))); HIP['flat'].extend(P_)
    MOUTH['lip'] = [v.co.copy() for v in lip]
    HIP['stack'] = {key: v.co.copy() for key, v in SV.items()}
    HIP['loop'] = [v.co.copy() for v in hl]
    MOUTH['low'] = [v.co.copy() for v in ms]
    HIP['leg'] = [(lab, [v.co.copy() for v in vv]) for lab, vv in LEGV]
    commit(body, bm)
    hits(body)



# ---------------------------------------------------------------- stage 3
PAL = {'back': '#6aa840', 'spot': '#3f6e2a', 'belly': '#fae8c0', 'mouth': '#2c3a1e',
       'gold': '#e8b830', 'pupil': '#111111', 'drum': '#579336', 'tongue': '#c8505a'}


def piece(name, bm, key, mirror=True):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: PAL[key]}, lambda c, n, i: key)
    return ob


def lens(bm, C, u, v, n, ru, rv, back, front, sides=6, rot=0.0):
    """A low-poly domed disc: back ring, smaller front ring, a front apex."""
    pts = []
    for a in range(sides):
        t = math.radians(a * 360 / sides + rot)
        pts.append((math.cos(t) * ru, math.sin(t) * rv))
    b = ring(bm, [C + u * x + v * y - n * back for x, y in pts])
    f = ring(bm, [C + (u * x + v * y) * 0.72 + n * front for x, y in pts])
    bridge(bm, b, f, closed=True)
    ap = bm.verts.new(C + n * (front * 1.3))
    for i in range(sides):
        bm.faces.new([f[i], f[(i + 1) % sides], ap])
    bm.faces.new(list(reversed(b)))


def near_any(p, pts, eps=2e-4):
    return any((p - q).length < eps for q in pts)


# (ring the band starts at, column): whole back faces painted as spots; neighbours join into 5+-sided
# blotches of mixed size, staggered (not in rows); the seam ones join their mirror across the spine
SPOT_FACES = [('N', 1), ('N', 2),                   # behind the head, across the ridge (a bent hexagon)
              ('B1', 1), ('B2', 1), ('B2', 2),      # the big one on the back, an L
              ('B0', 3), ('B1', 3),                 # the upper flank, over the arm, along the body
              ('B4', 0)]                            # the rump tip (joins its mirror: a small one)
PUPIL_DOWN = float(os.environ.get('FROG_PD', '22'))


def stage3(k, body):
    # ---- regions on the base, all on loops placed for them
    bm = edit(body)
    lip = MOUTH['lip']; low = MOUTH['low']
    pale = [Vector(RP(r[0], c)) for r in RINGS for c in (5, 6, 7)] + low + [lip[0], Vector((0.0, 0.214, 0.062))] \
        + MOUTH.get('pale_extra', [])
    mouth, belly, spot = set(), set(), set()
    RN = [r[0] for r in RINGS]
    for a_, c_ in SPOT_FACES:                      # r135: a spot = 1-3 adjacent body faces, an irregular 5+-gon
        b_ = RN[RN.index(a_) + 1]
        Q_ = [HIP['stack'][(a_, c_)], HIP['stack'][(a_, c_ + 1)], HIP['stack'][(b_, c_)], HIP['stack'][(b_, c_ + 1)]]
        for f in bm.faces:
            if len(f.verts) == 4 and all(near_any(v.co, Q_) for v in f.verts):
                spot.add(f.index)
    say('SPOT faces', len(spot), 'of', len(SPOT_FACES))
    for f in bm.faces:
        P = [v.co for v in f.verts]
        if all(near_any(p, lip + low) for p in P) and any(near_any(p, low) for p in P):
            mouth.add(f.index)
        elif all(near_any(p, pale) for p in P):
            belly.add(f.index)
    bm.free()

    def region(c, n, i):
        if i in mouth:
            return 'mouth'
        if i in belly:
            return 'belly'
        if n.z < -0.55 and c.z < 0.05:
            return 'belly'                                     # soles and the underside of the legs
        if i in spot:
            return 'spot'
        for sp in SPOTS:
            key, q = ('drum', sp[1]) if isinstance(sp, tuple) else ('spot', sp)
            if (c - q).length < 0.002:
                return key
        return 'back'
    paint(body, PAL, region)
    pieces = []
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(body, dg)

    def hit(o, d):
        r = tree.ray_cast(Vector(o), Vector(d).normalized())
        return (r[0], r[1]) if r[0] is not None else (None, None)

    # ---- eyes: a gold eyeball (a low-poly ball about the dome's size) seated ~40% into the front of
    #      the green dome; a horizontal lozenge pupil that follows the ball's curve 2.5 mm proud; a glint
    Cd = eye_dome()['c'] + Vector((0.016, 0.0, 0.052))           # the dome's equator centre
    n = Vector((0.55, -0.70, 0.45)).normalized()                  # forward, out and up
    S, _ = hit(Cd + n * 0.2, -n)
    rb = 0.038
    B = S + n * 0.006
    # r106: the seat stays on n; the ball's pole (and the pupil) turn 20 deg forward-down-in, so
    #       face-on the pupil sits on the front of the ball, and the front is a dome (apex +30% of
    #       the radius, falling off to the plain ball at 60 deg) instead of a flat 8-fan octagon
    k_ = Vector((0, -1, 0)) - n * n.dot(Vector((0, -1, 0)))
    n = (n + k_.normalized() * math.tan(math.radians(20))).normalized()
    u = n.cross(Vector((0, 0, 1))).normalized()                   # horizontal across the eye
    v = u.cross(n).normalized()
    if v.z < 0:
        v = -v

    def Rd(th):                                                   # the domed radius at th deg off the pole
        return rb * (1.0 + 0.22 * math.cos(math.radians(1.5 * th))) if th < 60 else rb   # r107: .30 read as an acorn at az090

    # r134: face-on the pupil sat on the ball's top rim (a lid). The pupil and glint now sit on their
    #       own axis np, the ball's pole turned PUPIL_DOWN deg down about the ball's horizontal axis u,
    #       so gold shows above and below the lozenge from the front; the radius still follows the
    #       ball's dome (measured from the ball's own pole n)
    pd = math.radians(PUPIL_DOWN)
    np_ = (n * math.cos(pd) - v * math.sin(pd)).normalized()
    vp = (v * math.cos(pd) + n * math.sin(pd)).normalized()

    def sph(a, b, dr, domed=True):
        ta, tb = math.tan(math.radians(a)), math.tan(math.radians(b))
        d = (np_ + u * ta + vp * tb).normalized()
        th = math.degrees(d.angle(n, 0.0))
        return B + d * ((Rd(th) if domed else rb) + dr)

    bm = bmesh.new()
    rings_ = []
    for th in (18, 38, 60, 110):                                  # r136: one back ring (buried in the dome)
        rings_.append(ring(bm, [B + (n * math.cos(math.radians(th)) + (u * math.cos(math.radians(p_ * 45 + 22.5))
                                 + v * math.sin(math.radians(p_ * 45 + 22.5))) * math.sin(math.radians(th))) * Rd(th)
                                for p_ in range(8)]))
    for r0, r1 in zip(rings_, rings_[1:]):
        bridge(bm, r0, r1, closed=True)
    for R_, ap in ((rings_[0], B + n * Rd(0)), (rings_[-1], B - n * rb)):
        a = bm.verts.new(ap)
        for i in range(8):
            bm.faces.new([R_[i], R_[(i + 1) % 8], a])
    pieces.append(piece('eye', bm, 'gold'))

    loz = [(36, 0), (12, 14), (-12, 14), (-36, 0), (-12, -14), (12, -14)]
    bm = bmesh.new()
    fr = ring(bm, [sph(a, b, 0.0025) for a, b in loz])
    fm = ring(bm, [sph(a / 2, b / 2, 0.0030) for a, b in loz])    # a mid ring so the pupil follows the dome
    bk = ring(bm, [sph(a, b, -0.006, domed=False) for a, b in loz])
    bridge(bm, bk, fr, closed=True)
    bridge(bm, fr, fm, closed=True)
    for R_, ap in ((fm, sph(0, 0, 0.0035)), (bk, sph(0, 0, -0.007, domed=False))):
        a = bm.verts.new(ap)
        for i in range(6):
            bm.faces.new([R_[i], R_[(i + 1) % 6], a])
    pieces.append(piece('pupil', bm, 'pupil'))

    bm = bmesh.new()
    gl = ring(bm, [sph(-9 + 3.5 * math.cos(math.radians(q)), 5 + 3.5 * math.sin(math.radians(q)), 0.002)
                   for q in (0, 90, 180, 270)])
    a = bm.verts.new(sph(-9, 5, 0.0065))
    for i in range(4):
        bm.faces.new([gl[i], gl[(i + 1) % 4], a])
    bm.faces.new(list(reversed(gl)))
    pieces.append(piece('glint', bm, 'belly'))

    # ---- toe pads: a round pale bulb on every toe tip
    #      r133: the old bulb's back ring (1.25x the toe's width, 4 mm behind the tip) came out through
    #      the toe's side walls. Now the back ring sits 6 mm inside the toe at 70% of its section, and
    #      the bulb (0.8x the old size) swells only past the tip cap, so no facet leaves the toe wall
    bm = bmesh.new()
    for tc, A, up, sz in TIPS:
        side = A.cross(up).normalized()
        u_ = up.normalized()
        th = sz * 0.78                                  # the tip ring's height (toe segs: th ~ 0.78 wd)
        def rg(c, ru, rv):
            return ring(bm, [c + side * (math.cos(math.radians(a * 60)) * ru) + u_ * (math.sin(math.radians(a * 60)) * rv)
                             for a in range(6)])
        m = rg(tc + A * 0.0015, sz * 1.0, sz * 0.76)   # r136: a bipyramid (12 tris, was 22): the back
        for tip_, rev in ((tc - A * 0.006, True), (tc + A * 0.0065, False)):   # cone stays inside the toe
            ap = bm.verts.new(tip_)
            for i in range(6):
                f_ = [m[i], m[(i + 1) % 6], ap]
                bm.faces.new(list(reversed(f_)) if rev else f_)
    pieces.append(piece('pads', bm, 'belly'))

    # ---- webbing between the hind toes: closed scalloped wedges (6 mm, ~40% of the toe's depth),
    #      low between the toes and sunk into both toes and the sole, so they show from below
    bm = bmesh.new()
    hind = TIPS[4:]
    L = [0.062 * s for s in (0.85, 1.0, 1.1, 1.0, 0.8)]
    for j in range(4):
        (t0, a0, _, _), (t1, a1, _, _) = hind[j], hind[j + 1]
        r0, r1 = t0 - a0 * L[j], t1 - a1 * L[j + 1]
        m0, m1 = r0.lerp(t0, 0.72), r1.lerp(t1, 0.72)
        notch = (r0.lerp(t0, 0.40) + r1.lerp(t1, 0.40)) / 2
        pts = [r0, m0, notch, m1, r1]
        # r139: a wedge section: 11 mm at the toe roots, tapering to 5 mm at the free edge's notch
        top = ring(bm, [Vector((q.x, q.y, z)) for q, z in zip(pts, (0.0150, 0.0130, 0.0115, 0.0130, 0.0150))])
        bot = ring(bm, [Vector((q.x, q.y, z)) for q, z in zip(pts, (0.0040, 0.0055, 0.0065, 0.0055, 0.0040))])
        bm.faces.new(top); bm.faces.new(list(reversed(bot)))
        bridge(bm, bot, top, closed=True)
    pieces.append(piece('web', bm, 'spot'))

    # ---- the tongue: a rounded bar (6-sided, thickness ~0.45x its width) lying along the mouth
    #      floor inside the head, its tip resting 2 mm behind the snout's inner surface; long enough
    #      that at full reach (attack) ~25% of it is still inside the mouth
    #      r91: the root (the first three rows, created first) rides the mouth floor with the skin's
    #      weights and the pad rides the tongue bone, so the tongue STRETCHES out of the mouth with its
    #      root inside; the end is a wide rounded sticky pad (1.5x the neck), not a needle
    tip, _ = hit((0.0, -0.20, 0.171), (0, -1, 0))
    bm = bmesh.new()
    rows = []
    for y, z, w, h in ((-0.060, 0.150, 0.010, 0.0065), (-0.085, 0.152, 0.011, 0.007), (-0.110, 0.155, 0.012, 0.0075),
                       (-0.150, 0.160, 0.016, 0.0085), (-0.190, 0.164, 0.016, 0.0085),
                       (-0.206, 0.166, 0.021, 0.0095), (-0.222, 0.168, 0.026, 0.0100), (-0.237, 0.169, 0.025, 0.0100),
                       (tip.y + 0.009, 0.170, 0.018, 0.0080)):
        rows.append(ring(bm, [(0.0, y, z + h), (0.8 * w, y, z + 0.55 * h), (0.8 * w, y, z - 0.55 * h), (0.0, y, z - h)]))
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1)
    for R_, apex in ((rows[-1], Vector((0.0, tip.y + 0.002, 0.170))), (rows[0], Vector((0.0, -0.050, 0.150)))):
        a = bm.verts.new(apex)
        for i in range(3):
            bm.faces.new([R_[i], R_[i + 1], a])
    pieces.append(piece('tongue', bm, 'tongue'))
    return pieces



# ---------------------------------------------------------------- stage 4
def lip_z(y):
    L = sorted((p.y, p.z) for p in MOUTH['lip'])
    if y <= L[0][0]:
        return L[0][1]
    for (y0, z0), (y1, z1) in zip(L, L[1:]):
        if y <= y1:
            return z0 + (z1 - z0) * (y - y0) / max(y1 - y0, 1e-9)
    return L[-1][1]


def split_jaw(body):
    """Automatic weights blur the head into the jaw; the mouth must open on the lip line.
    Everything at or above the lip line is head, everything under it jaw (the thin mouth band
    between the lip line and the stage-2 loop stretches into the open mouth)."""
    g = body.vertex_groups
    if g.get('tongue'):
        g.remove(g['tongue'])                    # the tongue bone moves the tongue piece only
    head, jaw = g['head'], g.get('jaw') or g.new(name='jaw')
    for v in body.data.vertices:
        p = v.co
        if not (p.y < -0.098 and p.z > 0.095 and abs(p.x) < 0.17):
            continue
        w = {g[e.group].name: e.weight for e in v.groups}
        tot = w.get('head', 0.0) + w.get('jaw', 0.0)
        if tot <= 1e-4:
            continue
        below = p.z < lip_z(p.y) - 0.0015
        (jaw if below else head).add([v.index], tot, 'REPLACE')
        (head if below else jaw).remove([v.index])


KNEE = tuple(float(x) for x in os.environ.get('FROG_KNEE', '.3,.6,.9').split(','))
SOCK = tuple(float(x) for x in os.environ.get('FROG_SOCK', '.8,.3,1.0,.5').split(','))
LEGW = {'s0': {'hipmid': 1 - SOCK[3], 'thigh': SOCK[3]}, 's1': {'thigh': 1.0}, 's2': {'thigh': 1.0},
        's3': {'thigh': 1 - KNEE[0], 'shin': KNEE[0]}, 's4': {'thigh': 1 - KNEE[1], 'shin': KNEE[1]},
        's5': {'thigh': 1 - KNEE[2], 'shin': KNEE[2]},
        's6': {'shin': 1.0}, 's7': {'shin': 1.0}, 's8': {'shin': .5, 'foot': .5},
        's9': {'foot': 1.0}, 's10': {'foot': 1.0}, 'P': {'foot': 1.0},
        't1': {'foot': .5, 'toes': .5}, 't2': {'toes': 1.0}}
LEGB = ('thigh', 'hipmid', 'shin', 'foot', 'toes')


def blend_hips(body):
    """r131: the hind leg is weighted ring by ring, not by bone heat. Heat bled the thigh, shin and
    foot into each other (the Z-folded segments lie side by side), so unfolding the hop stretched
    the shank into a rod. Each leg ring gets its segment (LEGW; 50/50 only at the knee and heel
    rings). The hip rotates through a helper bone (hipmid) that turns half the thigh's angle, so
    the pelvis-to-thigh blend never averages two poses 130 deg apart (the neck): socket ring
    hips 60 / hipmid 40, the ring round it 70/30, the hip loop hipmid 100, the thigh root
    hipmid 50 / thigh 50. The rest of the body carries no leg weight at all."""
    g = body.vertex_groups
    for sd in 'LR':
        if g.get('hipmid.' + sd) is None:
            g.new(name='hipmid.' + sd)
    share = {}
    socket = {('B2', 4), ('B2', 5), ('B2', 6), ('B3', 4), ('B3', 5), ('B3', 6)}
    around = {(n, c) for n in ('B1', 'B2', 'B3', 'B4') for c in range(3, 8)} - socket
    for key, p in HIP['stack'].items():
        share[p.freeze()] = ('pool', {'hips': 1 - SOCK[0], 'hipmid': SOCK[0]} if key in socket else
                             {'hips': 1 - SOCK[1], 'hipmid': SOCK[1]} if key in around else {'hips': 1.0})
    for p in HIP['flat']:                          # spot and drum insets: body skin
        share[p.freeze()] = ('pool', {'hips': 1.0})
    for p in HIP['loop']:
        share[p.freeze()] = ('pool', {'hips': 1 - SOCK[2], 'hipmid': SOCK[2]} if SOCK[2] <= 1 else
                             {'hipmid': 2 - SOCK[2], 'thigh': SOCK[2] - 1})
    for lab, P_ in HIP['leg']:
        for p in P_:
            share[p.freeze()] = ('all', LEGW[lab])
    kd = mathutils.kdtree.KDTree(len(share))
    keys = list(share)
    for i, p in enumerate(keys):
        kd.insert(p, i)
    kd.balance()
    legg = {g[nm + '.' + sd].index for nm in LEGB for sd in 'LR' if g.get(nm + '.' + sd)}
    pool_g = legg | {g['hips'].index}
    n = 0
    for v in body.data.vertices:
        q = Vector((abs(v.co.x), v.co.y, v.co.z))
        _, i, d = kd.find(q)
        side = 'L' if v.co.x >= 0 else 'R'
        if d > 1e-4:                                # not a listed vertex: strip any stray leg weight into the hips
            T = sum(e.weight for e in v.groups if e.group in legg)
            if T > 1e-6:
                for gi in [e.group for e in v.groups if e.group in legg]:
                    g[gi].remove([v.index])
                g['hips'].add([v.index], T, 'ADD')
            continue
        mode, w = share[keys[i]]
        grp = [e.group for e in v.groups]
        if mode == 'all':
            T = 1.0
            for gi in grp:
                g[gi].remove([v.index])
        else:
            T = sum(e.weight for e in v.groups if e.group in pool_g)
            if T < 1e-6:
                continue
            for gi in grp:
                if gi in pool_g:
                    g[gi].remove([v.index])
        for nm, x in w.items():
            gn = nm if nm == 'hips' else nm + '.' + side
            if x > 0:
                g[gn].add([v.index], x * T, 'ADD')
        n += 1
    say('LEGW set on', n, 'verts')


def stretch_tongue(p, rig, body):
    """The root rows keep the skin's weights (they stay seated in the mouth floor); from y -0.125
    to -0.20 the share moves to the tongue bone, so the pad shoots out while the root stays in."""
    bind(p, rig, body=body)
    g = p.vertex_groups
    tg = g.get('tongue') or g.new(name='tongue')
    for v in p.data.vertices:
        s_ = max(0.0, min(1.0, (-v.co.y - 0.125) / 0.075))
        for e in list(v.groups):
            nm = g[e.group].name
            if nm == 'tongue':
                continue
            if s_ >= 1.0:
                g[e.group].remove([v.index])
            else:
                g[e.group].add([v.index], e.weight * (1.0 - s_), 'REPLACE')
        if s_ > 0:
            tg.add([v.index], s_, 'REPLACE')


def leg_gauge(body, rig):
    """Print, at rest and at move f012, each leg segment's length (ring centre to ring centre)
    and the mean section radius of the hip loop, the thigh root and the drumstick: the fold-over
    gauge does not see a stretched shank or a necked hip."""
    rings = {lab: P_ for lab, P_ in HIP['leg'] if lab.startswith('s')}
    rings['hl'] = HIP['loop']
    idx = {}; idr = {}
    for v in body.data.vertices:
        q = Vector((abs(v.co.x), v.co.y, v.co.z))
        for lab, P_ in rings.items():
            for p in P_:
                if (q - p).length < 1e-4:
                    (idx if v.co.x > 0 else idr).setdefault(lab, []).append(v.index)

    def meas(tag):
        dg = bpy.context.evaluated_depsgraph_get()
        me = body.evaluated_get(dg).to_mesh()
        C = {}; R = {}
        for lab, ii in idx.items():
            P_ = [me.vertices[i].co.copy() for i in ii]
            C[lab] = sum(P_, Vector()) / len(P_)
            R[lab] = sum((p - C[lab]).length for p in P_) / len(P_)
        CR = {}
        for lab in ('s4', 's8', 's10'):
            P_ = [me.vertices[i].co.copy() for i in idr[lab]]
            CR[lab] = sum(P_, Vector()) / len(P_)
            CR[lab].x *= -1
        say('GAUGE', tag, 'mirror gap knee/heel/foot cm', [round((C[x] - CR[x]).length * 100, 2) for x in ('s4', 's8', 's10')])
        body.evaluated_get(dg).to_mesh_clear()
        L = lambda a, b: round((C[a] - C[b]).length * 100, 1)
        say('GAUGE', tag, 'thigh s1-s4', L('s1', 's4'), 'shin s4-s8', L('s4', 's8'), 'foot s8-s10', L('s8', 's10'),
            'r hl/s0/s1/s6', [round(R[x] * 100, 2) for x in ('hl', 's0', 's1', 's6')])
    import techqa
    techqa._zero_pose(rig)
    bpy.context.scene.frame_set(1)
    meas('rest')
    for f in (10, 12, 14):
        pose(rig, bpy.data.actions['move'], f)
        meas('move f%d' % f)
    techqa._zero_pose(rig)
    rig.animation_data.action = None
    bpy.context.scene.frame_set(1)


HM = float(os.environ.get('FROG_HM', '0.5'))
KICK = tuple(float(x) for x in os.environ.get('FROG_KICK', '-106,-40,-80,80').split(','))


def HPIV():
    """The hip helper's pivot: the joint, or (FROG_PIV=1) the hip loop's own centre."""
    if os.environ.get('FROG_PIV', '0') == '1':
        return tuple(sum(HIP['loop'], Vector()) / len(HIP['loop']))
    return J['hip']


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], (0.0, -0.06, 0.16), 'hips', True),
        ('head', (0.0, -0.06, 0.16), (0.0, -0.24, 0.205), 'spine', True),
        ('jaw', (0.0, -0.085, 0.150), (0.0, -0.25, 0.158), 'head'),
        ('throat', (0.0, -0.14, 0.140), (0.0, -0.14, 0.105), 'head'),
        ('tongue', (0.0, -0.11, 0.163), (0.0, -0.235, 0.170), 'jaw'),
        ('eye.L', (0.115, -0.145, 0.255), (0.130, -0.150, 0.335), 'head'),
        ('upperarm.L', J['shoulder'], J['elbow'], 'spine'),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('hand.L', J['wrist'], J['knuckle'], 'forearm.L', True),
        ('fingers.L', J['knuckle'], J['fingertip'], 'hand.L', True),
        ('thigh.L', J['hip'], J['knee'], 'hips'),
        ('hipmid.L', HPIV(), tuple(Vector(HPIV()) + (Vector(J['knee']) - Vector(J['hip'])) * 0.35), 'hips'),   # r131: turns half the thigh
        ('shin.L', J['knee'], J['heel'], 'thigh.L', True),
        ('foot.L', J['heel'], J['ball'], 'shin.L', True),
        ('toes.L', J['ball'], J['toetip'], 'foot.L', True),
    ])
    for b in ('thigh.L', 'shin.L', 'head', 'jaw', 'upperarm.L', 'spine'):
        M = rig.data.bones[b].matrix_local.to_3x3()
        say('AXES', b, 'x', tuple(round(c, 2) for c in M.col[0]), 'y', tuple(round(c, 2) for c in M.col[1]),
            'z', tuple(round(c, 2) for c in M.col[2]))
    skin(body, rig)
    say('TRIS', {o.name: sum(len(p_.vertices) - 2 for p_ in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
                 for o in [body] + list(pieces)})
    split_jaw(body)
    blend_hips(body)
    for p in pieces:
        nm = p.name
        if any(t in nm for t in ('eye', 'pupil', 'glint')):
            bind(p, rig)                                   # each eye to its nearest bone: eye.L / eye.R
        elif 'tongue' in nm:
            stretch_tongue(p, rig, body)
        else:
            bind(p, rig, body=body)                        # spots, drums, pads, webbing ride the skin

    def allk(keys):
        """Key EVERY bone in every clip (rest where unused): a clip that leaves a bone unkeyed
        inherits the last clip's pose (the r03 attack kept the hop's kicked legs)."""
        f0 = min(keys)
        for b in rig.pose.bones:
            keys[f0].setdefault(b.name, (0, 0, 0))

    Mx = Matrix.Diagonal((-1.0, 1.0, 1.0))

    def both(d, bone, l, r=None):
        """r131: the .R key is the true mirror of the .L key through each bone's own rest frame
        (the default rolls are not mirrored, so negating Y and Z bent the far leg differently)."""
        d[bone + '.L'] = l
        if r is None:
            BL = rig.data.bones[bone + '.L'].matrix_local.to_3x3()
            BR = rig.data.bones[bone + '.R'].matrix_local.to_3x3()
            RL = Euler([math.radians(x) for x in l], 'XYZ').to_matrix()
            RR = BR.transposed() @ Mx @ BL @ RL @ BL.transposed() @ Mx @ BR
            r = tuple(math.degrees(a) for a in RR.to_euler('XYZ'))
        d[bone + '.R'] = r

    # idle: 48 f - the throat pulses twice, a slow head bob, a blink
    idle, il = {}, {}
    for f, th, bob, blink in ((1, 0, 0, 0), (8, 1, 0.5, 0), (14, 0, 1, 0), (20, 1, 0.5, 0), (26, 0, 0, 0),
                              (31, 0, -0.5, 0), (33, 0, -0.5, 1), (35, 0, -0.5, 0), (41, 0, -1, 0), (48, 0, 0, 0)):
        idle[f] = {'spine': (1.5 * th, 0, 0), 'head': (3 * bob, 0, 0)}
        il[f] = {'throat': (0, 0.014 * th, 0), 'eye.L': (0, -0.016 * blink, 0), 'eye.R': (0, -0.016 * blink, 0)}
    allk(idle); clip(rig, 'idle', idle, loc=il)

    # move: 24 f - a hop in place: crouch, kick the hind legs out, fly, land on the hands, settle
    mv, ml = {}, {}
    for f, c, e, up, fw, ar in ((1, 0, 0, 0, 0, 0), (5, 1, 0, -0.012, 0, 0), (9, 0, 0.7, 0.03, -0.02, -0.5),
                                (13, 0, 1, 0.07, -0.03, -1), (18, 0, 0.3, 0.02, -0.01, 0.6), (21, 0.6, 0, -0.008, 0, 0.3),
                                (24, 0, 0, 0, 0, 0)):
        # probed axes: hips/spine/head/jaw have local Z DOWN, so +X pitches the front down and
        # +Z loc moves down; thigh/shin/foot have Z up, so -X swings the tip down and back
        # the leg folds are nearly horizontal (the knee axis is the shin's local Z, not X): solved
        # from the AXES print - thigh (-150, 0, -54) aims it back-out-down, shin Z -140 and foot
        # Z +140 unfold the knee and heel so the leg trails straight behind
        d = {'hips': (6 * c - 10 * e, 0, 0), 'spine': (4 * c - 5 * e, 0, 0), 'head': (-8 * c + 5 * e, 0, 0)}
        tx, tz, sz, fz = KICK
        both(d, 'thigh', (12 * c + tx * e, 0, tz * e))
        both(d, 'hipmid', ((12 * c + tx * e) * HM, 0, tz * HM * e))    # r131: the hip ring turns part way
        both(d, 'shin', (0, 0, sz * e))
        both(d, 'foot', (0, 0, fz * e))
        both(d, 'upperarm', (30 * ar, 0, 0))
        both(d, 'forearm', (-20 * abs(ar) - 15 * c, 0, 0))
        mv[f] = d
        ml[f] = {'hips': (0, -fw, -up)}
    allk(mv); clip(rig, 'move', mv, loc=ml)

    # attack: 32 f - draw back, lunge with the jaw dropping and the tongue flicking out, snap shut
    at, al = {}, {}
    for f, w, s_, t in ((1, 0, 0, 0), (8, 1, 0, 0), (12, 0, 1, 0.6), (15, 0, 1, 1), (18, 0, 0.8, 0.4),
                        (22, 0, 0.3, 0), (27, 0, 0, 0), (32, 0, 0, 0)):
        d = {'spine': (5 * w - 8 * s_, 0, 0), 'head': (6 * w - 12 * s_, 0, 0), 'jaw': (34 * s_, 0, 0)}
        both(d, 'upperarm', (6 * w - 12 * s_, 0, 0))
        at[f] = d
        al[f] = {'hips': (0, -0.015 * w + 0.03 * s_, 0.006 * w - 0.012 * s_), 'tongue': (0, 0.15 * t, 0)}
    allk(at); clip(rig, 'attack', at, loc=al)
    if os.environ.get('FROG_GAUGE') or os.environ.get('FROG_DBG'):
        leg_gauge(body, rig)
    if os.environ.get('FROG_DBG'):
        import techqa as Q
        Q.triangulate_convex(body)                 # measure on the export triangulation, as the gate does
        for nm in ('idle', 'move', 'attack'):
            act = bpy.data.actions[nm]
            cnt, fl, _ = Q.measure(body, [], (0.83, 0.48, 0.3), rig, {nm: act})
            ps = sorted(p for p, c in fl[body.name].items() if c == 'flip')
            if nm == 'idle':
                cnt, fl, _ = Q.measure(body, pieces, (0.83, 0.48, 0.3))
                say('SLIVERN', {o: c_.get('sliver', 0) for o, c_ in cnt.items()})
                for p, c in fl[body.name].items():
                    if c == 'sliver' and body.data.polygons[p].center.x > 0:
                        P_ = body.data.polygons[p]
                        say('SLIVER', tuple(round(x, 3) for x in P_.center),
                            [tuple(round(x, 3) for x in body.data.vertices[i].co) for i in P_.vertices])
            say('FLIP', nm, cnt[body.name]['flip'], [tuple(round(x, 3) for x in body.data.polygons[p].center) for p in ps[:40]])
            if nm == 'move':
                act.use_frame_range = True
                for fr_ in (5, 10, 14, 19):
                    act.frame_start = act.frame_end = fr_
                    c2, f2, _ = Q.measure(body, [], (0.83, 0.48, 0.3), rig, {nm: act})
                    say('FLIPF', fr_, c2[body.name]['flip'] // 4,
                        [tuple(round(x, 3) for x in body.data.polygons[p].center) for p, c in f2[body.name].items() if c == 'flip'])
                    for p, c in f2[body.name].items():
                        if c == 'flip' and body.data.polygons[p].center.x > 0:
                            for vi in body.data.polygons[p].vertices:
                                vv = body.data.vertices[vi]
                                say('  FV', tuple(round(x, 3) for x in vv.co),
                                    {body.vertex_groups[e.group].name: round(e.weight, 2) for e in vv.groups if e.weight > 0.01})
                act.use_frame_range = False
    return rig


run(META, stage1, stage2, stage3, stage4)
