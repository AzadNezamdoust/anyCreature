"""Goblin: a small hunched stylised game goblin, box-modelled in four stages.

Stage 1 is one vertical stack of 7-point half rings (front seam -> side -> back
seam) from the crotch to the crown; arms, legs, ears and nose are swept out of
sockets left open in that stack, so the base is one closed mirrored shell.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='goblin', model='opus', engine_glb='')

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    pelvis=(0.0, 0.02, 0.36), spine=(0.0, 0.0, 0.50), chest=(0.0, -0.03, 0.60),
    neck=(0.0, -0.07, 0.70), head=(0.0, -0.10, 0.79), crown=(0.0, -0.12, 1.06),
    clav=(0.03, -0.04, 0.665), shoulder=(0.19, -0.04, 0.625), elbow=(0.245, -0.05, 0.455),
    wrist=(0.27, -0.095, 0.305), knuckle=(0.282, -0.128, 0.198), fingertip=(0.27, -0.14, 0.13),
    hip=(0.095, 0.01, 0.33), knee=(0.135, -0.105, 0.195), ankle=(0.12, 0.0, 0.085),
    ball=(0.125, -0.10, 0.025), toetip=(0.13, -0.19, 0.015),
    ear=(0.19, -0.075, 0.95), eartip=(0.40, 0.11, 1.05),
)

# ---------------------------------------------------------------- the stack
# 7 points per half ring: 0 front seam, 1 front, 2 front corner, 3 side front,
# 4 side back, 5 back corner, 6 back seam.  (x, y, z)
STACK = [
    ('C',  [(0, -0.10, 0.335), (0.05, -0.11, 0.325), (0.12, -0.075, 0.335), (0.15, 0.01, 0.34),
            (0.12, 0.09, 0.335), (0.05, 0.115, 0.325), (0, 0.12, 0.335)]),
    ('H', [(0, -0.16, 0.405), (0.085, -0.15, 0.405), (0.14, -0.08, 0.41), (0.165, 0.01, 0.41), (0.14, 0.1, 0.415), (0.08, 0.15, 0.42), (0, 0.155, 0.42)]),
    ('B1', [(0, -0.228, 0.452), (0.097, -0.207, 0.452), (0.157, -0.11, 0.458), (0.17, 0.005, 0.462), (0.143, 0.092, 0.468), (0.075, 0.133, 0.475), (0, 0.137, 0.475)]),
    ('B2', [(0, -0.218, 0.565), (0.1, -0.197, 0.565), (0.155, -0.105, 0.565), (0.163, -0.002, 0.565), (0.137, 0.078, 0.57), (0.075, 0.12, 0.575), (0, 0.125, 0.575)]),
    ('CH', [(0, -0.17, 0.615), (0.085, -0.165, 0.615), (0.14, -0.085, 0.61), (0.155, -0.025, 0.61), (0.135, 0.04, 0.625), (0.08, 0.115, 0.645), (0, 0.125, 0.645)]),
    ('S', [(0, -0.165, 0.665), (0.07, -0.16, 0.67), (0.12, -0.105, 0.68), (0.14, -0.05, 0.685), (0.12, 0.01, 0.7), (0.07, 0.08, 0.715), (0, 0.09, 0.72)]),
    ('N1', [(0, -0.155, 0.72), (0.05, -0.145, 0.72), (0.08, -0.11, 0.73), (0.09, -0.06, 0.745), (0.075, -0.01, 0.76), (0.04, 0.02, 0.77), (0, 0.025, 0.775)]),
    ('J0', [(0, -0.305, 0.735), (0.04, -0.272, 0.745), (0.1, -0.2, 0.752), (0.122, -0.11, 0.765), (0.12, -0.03, 0.785), (0.07, 0.04, 0.792), (0, 0.06, 0.792)]),
    ('L0', [(0, -0.285, 0.785), (0.055, -0.28, 0.79), (0.12, -0.2, 0.8), (0.148, -0.11, 0.81), (0.148, -0.035, 0.82), (0.09, 0.04, 0.822), (0, 0.06, 0.822)]),
    ('M', [(0, -0.265, 0.803), (0.055, -0.26, 0.805), (0.122, -0.19, 0.812), (0.152, -0.11, 0.826), (0.152, -0.035, 0.835), (0.095, 0.048, 0.84), (0, 0.07, 0.84)]),
    ('U', [(0, -0.3, 0.82), (0.06, -0.295, 0.822), (0.13, -0.205, 0.83), (0.16, -0.11, 0.845), (0.16, -0.035, 0.855), (0.108, 0.06, 0.86), (0, 0.085, 0.86)]),
    ('NB', [(0, -0.295, 0.85), (0.05, -0.29, 0.852), (0.13, -0.215, 0.87), (0.175, -0.11, 0.88), (0.175, -0.035, 0.885), (0.12, 0.072, 0.89), (0, 0.1, 0.89)]),
    ('EB', [(0, -0.292, 0.928), (0.042, -0.285, 0.925), (0.13, -0.235, 0.915), (0.18, -0.1, 0.915), (0.18, -0.05, 0.92), (0.13, 0.082, 0.925), (0, 0.12, 0.925)]),
    ('ET', [(0, -0.3, 0.948), (0.045, -0.268, 0.95), (0.13, -0.226, 0.958), (0.185, -0.1, 0.958), (0.185, -0.05, 0.96), (0.135, 0.088, 0.96), (0, 0.13, 0.96)]),
    ('BR', [(0, -0.305, 0.966), (0.05, -0.31, 0.968), (0.135, -0.245, 1.0), (0.19, -0.105, 0.995), (0.19, -0.05, 0.995), (0.135, 0.088, 0.995), (0, 0.13, 0.995)]),
    ('FH', [(0, -0.25, 1.04), (0.06, -0.245, 1.04), (0.135, -0.2, 1.04), (0.182, -0.1, 1.045), (0.182, -0.04, 1.045), (0.125, 0.078, 1.04), (0, 0.115, 1.04)]),
    ('TOP', [(0, -0.19, 1.09), (0.05, -0.185, 1.095), (0.1, -0.15, 1.095), (0.13, -0.09, 1.1), (0.13, -0.03, 1.1), (0.09, 0.045, 1.09), (0, 0.07, 1.088)]),
]
# faces NOT created in the stack band that starts at a ring: they are sockets
SKIP = {'CH': {2, 3},          # arm socket (CH->S, cols 2-4)
        'NB': {0},             # nose root (NB->EB, col 0-1)
        'EB': {3}, 'ET': {3}}  # ear socket (EB->BR, cols 3-4)

ARM6 = [(1, .45), (0, 1), (-1, .45), (-1, -.45), (0, -1), (1, -.45)]
HAND6 = [(1, .8), (0, 1), (-1, .8), (-1, -.8), (0, -1), (1, -.8)]
KN8 = [(1, 1), (1 / 3, 1.15), (-1 / 3, 1.15), (-1, 1), (-1, -1), (-1 / 3, -1.1), (1 / 3, -1.1), (1, -1)]
LEG6 = [(0.8, -0.55), (0.8, 0.55), (0, 1), (-0.8, 0.55), (-0.8, -0.55), (0, -1)]
EAR6 = [(-1, -0.7), (-1, 0.5), (0, 1), (1, 0.5), (1, -0.7), (0, -0.1)]
FWD, UP = Vector((0, -1, 0)), Vector((0, 0, 1))


def frame(A, F):
    A = Vector(A).normalized()
    F = Vector(F)
    W = (F - A * F.dot(A)).normalized()
    return W, W.cross(A)


def section(C, A, F, tmpl, w, t):
    W, T = frame(A, F)
    C = Vector(C)
    return [C + W * (a * w) + T * (b * t) for a, b in tmpl]


def root_tmpl(loop, A, F):
    """The normalised (w, t) shape of an existing loop, to sweep it on."""
    c = centre(loop)
    W, T = frame(A, F)
    ws = [(v.co - c).dot(W) for v in loop]
    ts = [(v.co - c).dot(T) for v in loop]
    mw, mt = max(abs(x) for x in ws) or 1, max(abs(x) for x in ts) or 1
    return [(a / mw, b / mt) for a, b in zip(ws, ts)]


def sweep(bm, loop, secs, closed=True):
    rings = [list(loop)]
    for pts in secs:
        r = ring(bm, pts)
        bridge(bm, rings[-1], r, closed=closed)
        rings.append(r)
    return rings


def fan(bm, loop, p):
    v = bm.verts.new(Vector(p))
    for i in range(len(loop)):
        bm.faces.new([loop[i], loop[(i + 1) % len(loop)], v])
    return v


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


TIPS = []    # (tip centre, direction, nail side, size) of every digit, recorded for the stage-3 claws
DIGITS = []  # (root centre, [vertex positions], TIPS index) of every digit, for the stage-2 moves


def digit(bm, loop, A, F, segs, nail='W'):
    """A finger / toe / thumb: segs = [(advance, w, t, bend_vector)], blunt quad tip."""
    tm = root_tmpl(loop, A, F)
    C = centre(loop)
    A = Vector(A).normalized()
    secs = []
    for adv, w, t, bend in segs:
        A = (A + Vector(bend)).normalized()
        C = C + A * adv
        secs.append(section(C, A, F, tm, w, t))
    rings = sweep(bm, loop, secs)
    bm.faces.new(rings[-1])
    W, T = frame(A, F)
    TIPS.append((centre(rings[-1]).copy(), A.copy(), (T if nail == 'T' else W).copy(), (segs[-1][1] + segs[-1][2]) / 2))
    DIGITS.append((centre(loop).copy(), [v.co.copy() for r in rings[1:] for v in r], len(TIPS) - 1))
    return rings


def build_arm(bm, R):
    S, CH = R['S'], R['CH']
    loop = [S[2], S[3], S[4], CH[4], CH[3], CH[2]]
    sh, el, wr, kn = (Vector(J[n]) for n in ('shoulder', 'elbow', 'wrist', 'knuckle'))
    up_arm, fore, hand = el - sh, wr - el, kn - wr
    secs = [
        section(sh + Vector((0.0, 0.0, 0.0)), (0.7, 0, -0.7), FWD, ARM6, 0.048, 0.042),     # deltoid
        section(lerp(sh, el, 0.45), up_arm, FWD, ARM6, 0.036, 0.031),                        # skinny upper arm
        section(lerp(sh, el, 0.88), up_arm, FWD, ARM6, 0.034, 0.030),                        # above the elbow
        section(lerp(el, wr, 0.15), fore, FWD, ARM6, 0.044, 0.040),                          # below the elbow
        section(lerp(el, wr, 0.50), fore, FWD, ARM6, 0.064, 0.056),                          # chunky forearm
        section(lerp(el, wr, 0.97), fore, FWD, ARM6, 0.040, 0.032),                          # wrist
        section(lerp(wr, kn, 0.45), hand, FWD, HAND6, 0.064, 0.030),                         # palm
    ]
    rings = sweep(bm, loop, secs)
    p = rings[-1]
    k = ring(bm, section(kn, hand, FWD, KN8, 0.068, 0.028))
    for f in ([p[0], p[1], k[1], k[0]], [p[1], k[2], k[1]], [p[1], p[2], k[3], k[2]],
              [p[2], p[3], k[4], k[3]],
              [p[3], p[4], k[5], k[4]], [p[4], k[6], k[5]], [p[4], p[5], k[7], k[6]]):
        bm.faces.new(f)
    hd = hand.normalized()
    # three fingers: front (index) splays forward, back one backward; all curl in (-x)
    for j, spread in ((0, -0.22), (1, 0.0), (2, 0.22)):
        fl = [k[j], k[j + 1], k[6 - j], k[7 - j]]
        A = Vector((hd.x, hd.y + spread, hd.z))
        L = 1.0 if j == 1 else 0.9
        digit(bm, fl, A, FWD, [(0.043 * L, 0.019, 0.021, (0, 0, 0)),
                               (0.036 * L, 0.016, 0.018, (-0.35, 0, 0))], nail='T')
    # thumb from the front face of the palm -> knuckle band
    tl = [p[5], p[0], k[0], k[7]]
    digit(bm, tl, (-0.35, -0.75, -0.55), (1, 0, 0), [(0.036, 0.020, 0.019, (0, 0, 0)),
                                                      (0.031, 0.017, 0.016, (0.0, 0.1, -0.35))])


def build_leg(bm, R, X):
    C = R['C']
    loop = [C[1], C[2], C[3], C[4], C[5], X]
    hp, kn, an = (Vector(J[n]) for n in ('hip', 'knee', 'ankle'))
    th, sh = kn - hp, an - kn
    secs = [
        section(lerp(hp, kn, 0.30) + Vector((0.005, 0, 0)), th, FWD, LEG6, 0.062, 0.052),   # thigh root
        section(lerp(hp, kn, 0.70), th, FWD, LEG6, 0.050, 0.043),                             # thigh
        section(kn + Vector((0, -0.005, 0.012)), th + sh * 0.5, FWD, LEG6, 0.048, 0.041),     # knee cap
        section(lerp(kn, an, 0.30), sh, FWD, LEG6, 0.047, 0.040),                             # below the knee
        section(lerp(kn, an, 0.62), sh, FWD, LEG6, 0.043, 0.036),                             # calf
        section(an + Vector((0, 0, 0.005)), sh, FWD, LEG6, 0.034, 0.031),                     # ankle
    ]
    rings = sweep(bm, loop, secs)
    A = rings[-1]          # fi, fo, o, bo, bi, i
    B = ring(bm, [(0.08, -0.05, 0.004), (0.165, -0.05, 0.004), (0.175, 0.005, 0.008),
                  (0.155, 0.06, 0.004), (0.09, 0.06, 0.004), (0.072, 0.005, 0.008)])
    for i in (2, 3, 4):
        bm.faces.new([A[i], A[i + 1], B[i + 1], B[i]])
    bm.faces.new(list(reversed(B)))                                   # heel sole
    fl = [A[5], A[0], A[1], A[2], B[2], B[1], B[0], B[5]]
    FF = ring(bm, [(0.065, -0.105, 0.045), (0.105, -0.115, 0.052), (0.15, -0.11, 0.05), (0.19, -0.095, 0.04),
                   (0.19, -0.095, 0.003), (0.15, -0.11, 0.003), (0.105, -0.115, 0.003), (0.065, -0.105, 0.003)])
    bridge(bm, fl, FF, closed=True)
    for j, d in ((0, (-0.30, -1, -0.05)), (1, (0.02, -1, -0.08)), (2, (0.40, -1, -0.10))):
        tl = [FF[j], FF[j + 1], FF[6 - j], FF[7 - j]]
        digit(bm, tl, d, UP, [(0.040, 0.020, 0.019, (0, 0, 0)), (0.034, 0.015, 0.016, (0, 0, -0.25))])


def ear_sections():
    root, tip = Vector(J['ear']), Vector(J['eartip'])
    A = tip - root
    return [section(lerp(root, tip, 0.18), A, UP, EAR6, 0.058, 0.022),
            section(lerp(root, tip, 0.48) + Vector((0, 0, 0.012)), A, UP, EAR6, 0.050, 0.018),
            section(lerp(root, tip, 0.76) + Vector((0, 0, 0.010)), A, UP, EAR6, 0.030, 0.012)]


def build_ear(bm, R):
    EB, ET, BR = R['EB'], R['ET'], R['BR']
    loop = [EB[3], EB[4], ET[4], BR[4], BR[3], ET[3]]
    tip = Vector(J['eartip'])
    rings = sweep(bm, loop, ear_sections())
    fan(bm, rings[-1], tip)


def build_nose(bm, R):
    NB, EB = R['NB'], R['EB']
    loop = [NB[0], NB[1], EB[1], EB[0]]            # seam edge is last -> first: not bridged
    secs = [[(0, -0.345, 0.84), (0.055, -0.335, 0.845), (0.045, -0.345, 0.915), (0, -0.355, 0.92)],
            [(0, -0.395, 0.81), (0.04, -0.385, 0.815), (0.038, -0.405, 0.875), (0, -0.415, 0.878)]]
    rings = sweep(bm, loop, secs, closed=False)
    bm.faces.new(rings[-1])


def stage1(k):
    bm = bmesh.new()
    R = {}
    for name, pts in STACK:
        R[name] = ring(bm, pts)
    names = [n for n, _ in STACK]
    for a, b in zip(names, names[1:]):
        r0, r1 = R[a], R[b]
        for i in range(6):
            if i not in SKIP.get(a, ()):
                bm.faces.new([r0[i], r0[i + 1], r1[i + 1], r1[i]])
    T = R['TOP']
    for f in ([T[0], T[1], T[5], T[6]], [T[1], T[2], T[4], T[5]], [T[2], T[3], T[4]]):
        bm.faces.new(f)
    C = R['C']
    X, s = ring(bm, [(0.045, 0.005, 0.30), (0, 0.005, 0.29)])
    bm.faces.new([C[0], C[1], X, s])
    bm.faces.new([s, X, C[5], C[6]])
    build_leg(bm, R, X)
    build_arm(bm, R)
    build_ear(bm, R)
    build_nose(bm, R)
    return object_from_bm('body', bm)



# ---------------------------------------------------------------- stage 2
def SP(name, col):
    """The locked stage-1 position of a stack point."""
    return dict(STACK)[name][col]


def stage2(k, body):
    bm = edit(body)
    vs = lambda name, col: vert_near(bm, SP(name, col))
    # --- the eye: open the eye band into a tall socket, then inset it
    eb1, eb2, et1, et2 = vs('EB', 1), vs('EB', 2), vs('ET', 1), vs('ET', 2)
    br1, br2 = vs('BR', 1), vs('BR', 2)
    eb1.co = Vector((0.044, -0.287, 0.902)); eb2.co = Vector((0.132, -0.238, 0.894))
    et1.co = Vector((0.046, -0.272, 0.957)); et2.co = Vector((0.132, -0.230, 0.968))
    br1.co = Vector((0.052, -0.312, 0.975)); br2.co = Vector((0.137, -0.248, 1.006))
    eye_face = next(f for f in eb1.link_faces if eb2 in f.verts and et1 in f.verts)
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face, pushed in for the eye piece'):
        inner = inset(bm, [eye_face], 0.22, depth=0.0)
    iv = {min(inner[0].verts, key=lambda v: (v.co - c.co).length): c for c in (eb1, eb2, et1, et2)}
    shape = {eb1: (0.052, -0.271, 0.912), eb2: (0.118, -0.235, 0.912),       # lower lid: outer lifted
             et1: (0.056, -0.262, 0.944), et2: (0.122, -0.226, 0.962)}      # upper: inner pressed down
    for v, c in iv.items():
        v.co = Vector(shape[c])
    for c, d in ((eb2, (0, 0, 0.008)), (et1, (0, -0.004, -0.006))):         # the socket rim follows
        c.co += Vector(d)
    # --- the mouth: a grin curving up at the corners, upper jaw overbiting the lower lip
    grin = {('M', 0): (0, -0.252, 0.80), ('M', 1): (0.058, -0.25, 0.806), ('M', 2): (0.126, -0.18, 0.836),
            ('M', 3): (0.15, -0.115, 0.854), ('U', 2): (0.133, -0.20, 0.848), ('U', 3): (0.16, -0.11, 0.862),
            ('L0', 0): (0, -0.278, 0.782), ('L0', 1): (0.056, -0.273, 0.786), ('L0', 2): (0.124, -0.19, 0.818),
            ('L0', 3): (0.15, -0.112, 0.838)}             # note 7: corners lifted ~1/3 of the mouth height
    gv = {key: vs(*key) for key in grin}
    for key, v in gv.items():
        v.co = Vector(grin[key])
    # --- the neck: a second loop between shoulder ring and neck ring, for the bend
    s3, n3 = vs('S', 3), vs('N1', 3)
    ne = next(e for e in s3.link_edges if e.other_vert(s3) is n3)
    with k.topo(bm, 'loop', 'neck loop: S->N1 band gets a middle ring so the neck bends in 3 loops'):
        nl = loopcut(bm, ne, t=0.5)
    ax = Vector((0.0, -0.09, 0.0))
    for v in nl:
        d = Vector((v.co.x, v.co.y - ax.y, 0.0))
        v.co -= d * 0.06
    # --- repair r2 item 4: the top-front shoulder quad (socket S2-S3 -> deltoid d0-d1) is made one
    # plane, so it splits on its short diagonal: the long S2-d1 split collapsed in the arm raise
    dl = section(Vector(J['shoulder']), (0.7, 0, -0.7), FWD, ARM6, 0.048, 0.042)
    flatten([vs('S', 2), vs('S', 3), vert_near(bm, dl[0]), vert_near(bm, dl[1])])
    # --- the ears: thicker blade, a cupped inner face, a slight droop
    root, tip = Vector(J['ear']), Vector(J['eartip'])
    A = tip - root
    W, T = frame(A, UP)
    er = [[vert_near(bm, p) for p in pts] for pts in ear_sections()]
    tv = vert_near(bm, tip)
    for r, (dt, dw, rb) in zip(er, ((0.022, 0.006, 0.010), (0.013, 0.006, 0.005), (0.006, 0.004, 0.0))):
        for i in (1, 2, 3):
            r[i].co += T * (dt + (rb if i == 2 else 0.0))     # note 7: root ~2x, rounded back plane
        r[0].co += W * -dw; r[3].co += W * dw; r[4].co += W * dw; r[1].co += W * -dw
    cup = [f for f in er[1][4].link_faces if er[2][4] in f.verts and (er[1][5] in f.verts)] +           [f for f in er[1][5].link_faces if er[2][5] in f.verts and (er[1][0] in f.verts)]
    with k.topo(bm, 'inset', 'inner ear: a loop inside the two front faces of the middle ear segment, pushed back as the cup'):
        inner = inset(bm, cup, 0.16, depth=0.0)
    for f in inner:
        for v in f.verts:
            v.co += T * 0.012
    ear = {v for r in er[1:] for v in r} | {tv} | {v for f in inner for v in f.verts}
    rotate(list(ear), Vector((0, 1, 0)), 9.0, pivot=root + A * 0.18)
    hands_and_feet(bm)
    # --- note 4: the nose hooks — the tip drops ~30% of the nose length and comes back 10%, the
    # bridge tapers (top verts drop more than the bottom ones), so it hangs over the lip;
    # repair r2 O8: the bridge 20% narrower, the tip ~12% wider, so the nose widens to the tip
    for p, d in (((0, -0.395, 0.81), (0, 0.018, -0.036)), ((0.04, -0.385, 0.815), (0.0, 0.018, -0.034)),
                 ((0.038, -0.405, 0.875), (-0.006, 0.008, -0.046)), ((0, -0.415, 0.878), (0, 0.006, -0.046)),
                 ((0, -0.345, 0.84), (0, 0.004, -0.010)), ((0.055, -0.335, 0.845), (-0.004, 0.004, -0.010)),
                 ((0.045, -0.345, 0.915), (-0.015, 0.0, -0.010)), ((0, -0.355, 0.92), (0, 0.0, -0.008))):
        vert_near(bm, p).co += Vector(d)
    # --- note 5: dome the skull — the crown rises ~12% of the head height at the centre and the
    # top ring draws in, so the FH->TOP band becomes a slanted rim plane instead of a lid edge
    for col, dz in ((0, 0.044), (1, 0.040), (2, 0.036), (3, 0.028), (4, 0.030), (5, 0.040), (6, 0.036)):
        v = vs('TOP', col)
        c = Vector((0.0, -0.06, v.co.z))
        v.co = c + (v.co - c) * 0.9 + Vector((0, 0, dz))
        if col in (0, 6):
            v.co.x = 0.0
    # --- note 6 / repair r2 item 3: a pot belly. The belly's low front corner (B1 cols 0-1) comes
    # forward and up, so the gut overhangs the belt slung on the underside below it; the B2 loop
    # arches (high at the centre, low at the front corner) to carry the belly colour's curved top
    for (nm, col), d in ((('B1', 0), (0, -0.040, 0.018)), (('B1', 1), (0, -0.029, 0.016)), (('B2', 0), (0, -0.014, 0.010)),
                         (('B2', 1), (0, -0.011, -0.030)), (('B2', 2), (0, -0.002, -0.068)), (('CH', 0), (0, -0.008, 0)),
                         (('CH', 1), (0, -0.006, 0))):
        vs(nm, col).co += Vector(d)
    # --- note 7: forearm 15% wider, and a flat plane on the back of the elbow
    sh, el, wr = (Vector(J[n]) for n in ('shoulder', 'elbow', 'wrist'))
    fore, up_arm = wr - el, el - sh
    for t_, w_, d_ in ((0.15, 0.044, 0.040), (0.50, 0.064, 0.056)):
        c = lerp(el, wr, t_)
        rv = [vert_near(bm, p) for p in section(c, fore, FWD, ARM6, w_, d_)]
        scale(rv, 1.15, pivot=c)
    back = []
    for c, A_, w_, d_ in ((lerp(sh, el, 0.88), up_arm, 0.034, 0.030), (lerp(el, wr, 0.15), fore, 0.044 * 1.15, 0.040 * 1.15)):
        for p in section(c, A_, FWD, ARM6, w_, d_):
            if (Vector(p) - c).y > 0.01:
                back.append(vert_near(bm, p))
    flatten(back)
    commit(body, bm)
    if os.environ.get('GOB_DBG'):
        from bmkit import evaluated_bm
        eb = evaluated_bm(body); eb.faces.ensure_lookup_table()
        t = BVHTree.FromBMesh(eb)
        for i, j in t.overlap(t):
            if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
                print('BMK DBG selfhit', tuple(round(x, 3) for x in eb.faces[i].calc_center_median()),
                      tuple(round(x, 3) for x in eb.faces[j].calc_center_median()))


def _xf(M, verts, tips=(), s=1.0):
    for v in verts:
        v.co = M @ v.co
    R = M.to_3x3().normalized()
    for i in tips:
        c, A, nl, sz = TIPS[i]
        TIPS[i] = (M @ c, (R @ A).normalized(), (R @ nl).normalized(), sz * s)


def hands_and_feet(bm):
    """Note 3: bigger hands with spread fingers, longer spread toes (vertex moves only).
    The recorded digit tips (TIPS) move with them, so the stage-3 claws follow."""
    wr, kn = Vector(J['wrist']), Vector(J['knuckle'])
    hd = (kn - wr).normalized()
    W, T = frame(hd, FWD)
    hand_dig = [d for d in DIGITS if d[0].z > 0.1]
    foot_dig = [d for d in DIGITS if d[0].z <= 0.1]
    # fingers splay: the back finger turns 12 deg away from the middle one about the palm normal
    # (the index stays: it would run into the thumb)
    dv = set()
    for root, pts, ti in hand_dig:
        vs_ = [vert_near(bm, p) for p in pts]
        dv |= set(vs_)
        tip = TIPS[ti][0]
        lat = (tip - kn).dot(W)
        if (root - kn).dot(W) > -0.02 or (root - kn).dot(hd) < -0.01:
            continue                                     # middle finger, index and thumb stay
        for sgn in (1, -1):
            M = Matrix.Translation(root) @ Matrix.Rotation(math.radians(12 * sgn), 4, T) @ Matrix.Translation(-root)
            if abs(((M @ tip) - kn).dot(W)) > abs(lat):
                break
        _xf(M, vs_, [ti])
    # the whole hand about the wrist: 1.3x long, 1.25x wide, same thickness
    seg = Vector(J['fingertip']) - wr
    def near_hand(p):
        t = max(0.0, min(1.0, (p - wr).dot(seg) / seg.length_squared))
        return (p - (wr + seg * t)).length < 0.09
    hv = list({v for v in bm.verts if v.co.x > 0.2 and (v.co - wr).dot(hd) > 0.0 and near_hand(v.co)} | dv)
    S = Matrix.Scale(1.3, 4, hd) @ Matrix.Scale(1.25, 4, W)          # longer and wider, not thicker
    M = Matrix.Translation(wr) @ S @ Matrix.Translation(-wr)
    _xf(M, hv, [ti for _, _, ti in hand_dig], 1.3)
    # toes: 1.06x longer along their axis (not wider: neighbours share the root ring), outer two splay 6 deg
    for root, pts, ti in foot_dig:
        vs_ = [vert_near(bm, p) for p in pts]
        M = Matrix.Translation(root) @ Matrix.Scale(1.06, 4, TIPS[ti][1]) @ Matrix.Translation(-root)
        side = (TIPS[ti][0] - root).x
        mid = sorted(foot_dig, key=lambda d: d[0].x)[len(foot_dig) // 2][0]
        if (root - mid).length > 0.02:
            ang = 6 if root.x > mid.x else -6
            M = Matrix.Translation(root) @ Matrix.Rotation(math.radians(ang), 4, UP) @ Matrix.Translation(-root) @ M
        _xf(M, vs_, [ti], 1.0)


PAL = {'skin': '#6f9a3a', 'skin_dark': '#4d6e28', 'belly': '#8cb050', 'cloth': '#6b4a2e',
       'leather': '#3a2a1e', 'teeth': '#e8e0c0', 'eye': '#ffd23a', 'pupil': '#111111'}
EYE_SOCKET = [(0.052, -0.271, 0.912), (0.118, -0.235, 0.912), (0.122, -0.226, 0.962), (0.056, -0.262, 0.944)]


def piece(name, bm, key, mirror=True):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: PAL[key]}, lambda c, n, i: key)
    return ob


def lens(bm, C, u, v, n, ru, rv, back, front, slant=0.0, sides=6):
    """A low-poly domed disc: back ring, smaller front ring, a front apex."""
    pts = []
    for a in range(sides):
        t = math.radians(a * 360 / sides + 90 / sides)
        x, y = math.cos(t) * ru, math.sin(t) * rv
        pts.append((x, y + slant * x))
    b = ring(bm, [C + u * x + v * y - n * back for x, y in pts])
    f = ring(bm, [C + (u * x + v * y) * 0.72 + n * front for x, y in pts])
    bridge(bm, b, f, closed=True)
    fan(bm, f, C + n * (front * 1.35))
    bm.faces.new(list(reversed(b)))


def export_tree(body):
    """A BVH of the body as it will be exported: the kit folds every non-planar quad OUT
    (techqa.triangulate_convex) before export, so pieces are fitted to that surface."""
    import techqa
    cp = body.copy(); cp.data = body.data.copy()
    bpy.context.scene.collection.objects.link(cp)
    techqa.triangulate_convex(cp)
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(cp, dg)
    me = cp.data
    bpy.data.objects.remove(cp); bpy.data.meshes.remove(me)
    return tree


def body_hit(tree, o, d):
    hit = tree.ray_cast(Vector(o), Vector(d).normalized())
    return hit[0]


def stage3(k, body):
    # ---- regions on the base: belly, brow / sockets / inner ear (dark), mouth (leather)
    bm = edit(body)
    mv = [vert_near(bm, p) for p in ((0, -0.252, 0.80), (0.058, -0.25, 0.806), (0.126, -0.18, 0.826))]
    mouth = {f.index for v in mv for f in v.link_faces if f.calc_center_median().y < -0.14}
    b2 = sorted(((v.co.x, v.co.z) for v in (vert_near(bm, SP('B2', c_)) for c_ in (0, 1, 2))))
    bm.free()

    def b2_arch(x):                                   # repair r2 item 3: the belly colour's curved top
        for (x0, z0), (x1, z1) in zip(b2, b2[1:]):
            if x <= x1:
                return z0 + (z1 - z0) * max(0.0, x - x0) / (x1 - x0)
        return b2[-1][1]

    def region(c, n, i):
        if i in mouth:
            return 'leather'
        if c.x > 0.195 and c.z > 0.86 and n.y < -0.2:
            return 'skin_dark'                                    # inside of the ear
        if -0.315 < c.y < -0.2 and 0.895 < c.z < 1.012 and c.x < 0.15:
            return 'skin_dark'                                    # brow ridge and eye sockets
        if 0.40 < c.z < b2_arch(c.x) - 0.004 and c.y < -0.10 and c.x < 0.16 and n.y < -0.3:
            return 'belly'                                        # lower belly only: under the arched B2 loop
        return 'skin'
    paint(body, PAL, region)
    pieces = []

    # ---- eyes: a gold lens in each socket, a black pupil, a small highlight
    P = [Vector(p) for p in EYE_SOCKET]
    C = sum(P, Vector()) / 4
    u = (P[1] - P[0]).normalized()
    n = (P[1] - P[0]).cross(P[3] - P[0]).normalized()
    if n.y > 0:
        n = -n
    v = n.cross(u).normalized()
    if v.z < 0:
        v = -v
    C = C + n * 0.004
    bm = bmesh.new(); lens(bm, C, u, v, n, 0.036, 0.022, 0.006, 0.006, slant=0.25)
    pieces.append(piece('eye', bm, 'eye'))
    pc = C - u * 0.006 - v * 0.002
    bm = bmesh.new(); lens(bm, pc, u, v, n, 0.012, 0.013, -0.004, 0.0105, sides=5)
    pieces.append(piece('pupil', bm, 'pupil'))
    hc = pc + u * 0.004 + v * 0.006
    bm = bmesh.new(); lens(bm, hc, u, v, n, 0.0035, 0.0035, -0.010, 0.0135, sides=4)
    pieces.append(piece('glint', bm, 'teeth'))

    # ---- fangs: two upper fangs over the lower lip (the overbite)
    bm = bmesh.new()
    for x, h, k_, z0 in ((0.052, 0.036, 1.0, 0.828), (0.098, 0.044, 1.5, 0.834)):   # note 7: outer fangs 1.7x
        b = ring(bm, [(x - 0.009 * k_, -0.283 + (x - 0.05) * 0.9, z0), (x + 0.009 * k_, -0.281 + (x - 0.05) * 0.9, z0),
                      (x + 0.008 * k_, -0.268 + (x - 0.05) * 0.9, z0 + 0.002), (x - 0.008 * k_, -0.270 + (x - 0.05) * 0.9, z0 + 0.002)])
        fan(bm, b, (x + 0.002, -0.286 + (x - 0.05) * 0.9, z0 - h))
        bm.faces.new(list(reversed(b)))
    pieces.append(piece('fangs', bm, 'teeth'))

    # ---- claws: a nail wedge on every finger, thumb and toe, rooted 1 cm inside the digit on its
    # nail side, tapering through a mid ring to a short tip hooked toward the palm / sole
    bm = bmesh.new()
    for tc, A, nail, sz in TIPS:
        side = A.cross(nail).normalized()
        nl = (nail - A * nail.dot(A)).normalized()
        cb = tc - A * 0.010 + nl * sz * 0.20
        b = ring(bm, [cb + side * sz * 0.55 + nl * sz * 0.35, cb - side * sz * 0.55 + nl * sz * 0.35,
                      cb - side * sz * 0.55 - nl * sz * 0.30, cb + side * sz * 0.55 - nl * sz * 0.30])
        cm = tc + A * sz * 0.60 + nl * sz * 0.12
        m = ring(bm, [cm + side * sz * 0.46 + nl * sz * 0.26, cm - side * sz * 0.46 + nl * sz * 0.26,
                      cm - side * sz * 0.40 - nl * sz * 0.20, cm + side * sz * 0.40 - nl * sz * 0.20])
        bridge(bm, b, m, closed=True)
        fan(bm, m, tc + A * sz * 1.45 - nl * sz * 0.40)
        bm.faces.new(list(reversed(b)))
    pieces.append(piece('claws', bm, 'skin_dark'))

    # ---- belt, buckle and loincloth: closed solids fitted by casting rays at the base.
    # Cylindrical frame about a vertical axis through the waist: a point is (angle, z, r).
    tree = export_tree(body)
    CY = -0.03

    def dirn(a):
        t = math.radians(a)
        return Vector((math.sin(t), -math.cos(t), 0.0))

    def at(a, z, r):
        p = Vector((0.0, CY, z)) + dirn(a) * r
        if a in (0, 180):
            p.x = 0.0
        return p

    def r_in1(a, z):
        h = body_hit(tree, (0.0, CY, z), dirn(a))
        return (h - Vector((0.0, CY, z))).dot(dirn(a)) if h is not None else 0.16

    def r_in(a, z):                                   # the waist surface, from inside: the envelope
        return max(r_in1(min(180, max(0, a + da)), z + dz) for da in (-8, 0, 8) for dz in (-0.007, 0, 0.007))

    def r_out(a, z, z1=None):                         # the outermost surface (legs too), from outside
        best = 0.0
        for zz in ([z] if z1 is None else [z + (z1 - z) * s / 4 for s in range(5)]):
            for aa in (min(180, max(0, a + da)) for da in (-8, 0, 8)):
                o = Vector((0.0, CY, zz)) + dirn(aa) * 0.25   # inside the hanging hands
                h = body_hit(tree, o, -dirn(aa))
                if h is not None:
                    best = max(best, (h - Vector((0.0, CY, zz))).dot(dirn(aa)))
        return best

    GAP, DEPTH, BH = 0.004, 0.017, 0.022              # belt: 3 mm off the skin, 1.7 cm deep, 4.4 cm tall
    zc = lambda a: 0.412 + 0.040 * a / 180.0          # the belt dips at the front, slung under the belly
    bm = bmesh.new()
    secs = []
    for a in range(0, 181, 15):
        zs = (zc(a) - BH, zc(a), zc(a) + BH)
        ri = [r_in(a, z) + GAP for z in zs]
        sec = [at(a, z, r) for z, r in zip(zs, ri)] + [at(a, z, r + DEPTH) for z, r in reversed(list(zip(zs, ri)))]
        secs.append(ring(bm, sec))
        if a == 0:
            belt0 = [p.copy() for p in sec]
    for s0, s1 in zip(secs, secs[1:]):
        bridge(bm, s0, s1, closed=True)
    pieces.append(piece('belt', bm, 'leather'))

    # buckle (repair r2 item 1): a chunky bevelled block in the frame of the belt's front face
    # (t runs down its slope, n is its outward normal), about half as deep as it is wide, its
    # back 5 mm sunk into the belt; the sides sink 3 mm more where the belt curves away
    ot, om, ob = (belt0[i].copy() for i in (3, 4, 5))
    t = (ob - ot).normalized()
    n = Vector((0.0, t.z, -t.y))
    if n.y > 0:
        n = -n
    HW, HH, D, SINK, BEV = 0.016, 0.016, 0.016, 0.005, 0.004
    def rect(c, hw, hh, side_back=0.0):
        return [c - t * hh, c - t * hh + Vector((hw, 0, 0)) - n * side_back,
                c + t * hh + Vector((hw, 0, 0)) - n * side_back, c + t * hh]
    bm = bmesh.new()
    back = rect(om - n * SINK, HW, HH, 0.003)
    mid = rect(om + n * (D - SINK - BEV), HW, HH)
    fr = rect(om + n * (D - SINK), HW - BEV, HH - BEV)
    for q in (back, mid, fr):
        q[0].x = q[3].x = 0.0
    b = ring(bm, back); m = ring(bm, mid); f = ring(bm, fr)
    for r0, r1 in ((b, m), (m, f)):
        for i in range(3):
            bm.faces.new([r0[i], r0[i + 1], r1[i + 1], r1[i]])
    bm.faces.new(f); bm.faces.new(list(reversed(b)))
    pieces.append(piece('buckle', bm, 'teeth'))

    # loincloth: a front and a back flap (two pieces), slabs 0.7 cm thick at the top (tucked
    # inside the belt) thickening to 1.4 cm at the hem, hanging clear of the legs; ragged hem
    for nm, cols, hem, flare in (('loincloth_front', (0, 14, 28, 42), 0.215, (0.0, 0.012, 0.030)),
                                 ('loincloth_back', (180, 166, 152, 138), 0.20, (0.0, 0.004, 0.014))):
        bm = bmesh.new()
        ztop = zc(cols[0])
        zbb = ztop - BH + 0.004                       # still inside the belt: the flap leaves by its bottom
        rows_z = [ztop, zbb, (zbb + hem) / 2, hem]
        half = [0.0035, 0.004, 0.007, 0.007]
        I, O = [], []
        for j, a in enumerate(cols):
            jag = (-0.028 if j % 2 else 0.0) + (0.012 if j == len(cols) - 1 else 0.0)
            zr = list(rows_z); zr[3] += jag
            rc = r_in(a, ztop) + GAP + DEPTH / 2
            rs = [rc, r_in(a, zbb) + GAP + DEPTH / 2]
            for k in (2, 3):
                want = rs[-1] + flare[k - 1] + (0.0 if k == 1 else 0.0)
                need = r_out(a, zr[k], zr[k - 1]) + 0.004 + half[k]
                rs.append(max(want, need))
            I.append(ring(bm, [at(a, z, r - h) for z, r, h in zip(zr, rs, half)]))
            O.append(ring(bm, [at(a, z, r + h) for z, r, h in zip(zr, rs, half)]))
        for j in range(len(cols) - 1):
            bridge(bm, I[j], I[j + 1]); bridge(bm, O[j], O[j + 1])
            for k in (0, 3):
                bm.faces.new([I[j][k], I[j + 1][k], O[j + 1][k], O[j][k]])
        bridge(bm, I[-1], O[-1])                     # the outer side edge of the flap
        pieces.append(piece(nm, bm, 'cloth'))
    if os.environ.get('GOB_DBG'):
        dg = bpy.context.evaluated_depsgraph_get()
        def tr(o):
            e = o.evaluated_get(dg); m = e.to_mesh()
            V = [v.co.copy() for v in m.vertices]; m.loop_triangles
            T = [tuple(t.vertices) for t in m.loop_triangles]
            return BVHTree.FromPolygons(V, T, all_triangles=True), V, T
        tb = tr(body)
        for p in pieces:
            tp = tr(p)
            pr = tp[0].overlap(tb[0])
            if pr:
                cs = sorted({tuple(round(x, 3) for x in sum((tb[1][v] for v in tb[2][j]), Vector()) / 3) for _, j in pr})
                print('BMK DBG', p.name, len(pr), cs[:12])
    return pieces


# ---------------------------------------------------------------- stage 4
def ramp_joint(body, head, tail, child, parents, radius, lo, hi, keep=lambda p, sx: True):
    """Replace bone heat's hard seam at a joint with a smooth ramp along the child bone's axis:
    the child's weight grows 0 -> 1 over [lo, hi] m from the joint; the rest goes to the
    parents by share. Both sides (.L and .R, mirrored in x)."""
    groups = {g.name: g for g in body.vertex_groups}
    for side, sx in (('L', 1), ('R', -1)):
        h = Vector((head[0] * sx, head[1], head[2]))
        ax = (Vector((tail[0] * sx, tail[1], tail[2])) - h).normalized()
        nm = lambda n: n.replace('.S', '.' + side)
        for v in body.data.vertices:
            p = v.co
            if sx * p.x <= 0 or (p - h).length > radius or not keep(p, sx):
                continue
            t = min(1.0, max(0.0, ((p - h).dot(ax) - lo) / (hi - lo)))
            s = t * t * (3 - 2 * t)
            for g in body.vertex_groups:
                g.remove([v.index])
            for n, w in [(nm(child), s)] + [(nm(pn), (1 - s) * sh) for pn, sh in parents]:
                g = groups.get(n) or body.vertex_groups.new(name=n)
                groups[n] = g
                if w > 1e-4:
                    g.add([v.index], w, 'REPLACE')


def smooth_weights(body, centre, radius, iters, share=0.5):
    """Repair r2 item 4: Laplacian-smooth every weight of the skin near a joint (both sides), so a
    raised arm spreads the bend over the shoulder instead of collapsing one band."""
    me = body.data
    nb = {}
    for e in me.edges:
        a, b = e.vertices
        nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
    names = [g.name for g in body.vertex_groups]
    W = [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in me.vertices]
    sel = []
    for sx in (1, -1):
        c = Vector((centre[0] * sx, centre[1], centre[2]))
        sel += [v.index for v in me.vertices if sx * v.co.x > 0 and (v.co - c).length < radius]
    for _ in range(iters):
        new = {}
        for i in sel:
            acc = {}
            for j in nb.get(i, []):
                for n, w in W[j].items():
                    acc[n] = acc.get(n, 0.0) + w / len(nb[i])
            m = {n: (1 - share) * W[i].get(n, 0.0) + share * acc.get(n, 0.0) for n in set(W[i]) | set(acc)}
            tot = sum(m.values()) or 1.0
            new[i] = {n: w / tot for n, w in m.items() if w / tot > 1e-4}
        for i, m in new.items():
            W[i] = m
    groups = {g.name: g for g in body.vertex_groups}
    for i in sel:
        for g in body.vertex_groups:
            g.remove([i])
        for n, w in W[i].items():
            groups[n].add([i], w, 'REPLACE')


def torso_off_arm(body):
    """Bone heat gives the flank under the armpit some upper-arm weight (the hanging arm is
    close): the flank below the arm socket follows the chest and spine only."""
    for sx, side in ((1, 'L'), (-1, 'R')):
        arm = [body.vertex_groups.get(n + side) for n in ('upperarm.', 'forearm.', 'hand.', 'fingers.')]
        chest, spine = body.vertex_groups.get('chest'), body.vertex_groups.get('spine')
        for v in body.data.vertices:
            p = v.co
            if not (0.02 < sx * p.x < 0.178 and 0.44 < p.z < 0.605):
                continue
            for g in arm:
                if g:
                    g.remove([v.index])
            tot = sum(g.weight for g in v.groups)
            if tot < 0.5:
                w = min(1.0, max(0.0, (p.z - 0.50) / 0.08))
                chest.add([v.index], w, 'ADD'); spine.add([v.index], 1 - w, 'ADD')


def waist_weights(piece, body, allow=('hips', 'spine', 'chest', 'thigh.L', 'thigh.R'), cy=-0.03):
    """Repair r2 item 2: a belt vertex takes the torso and thigh weights of the skin straight in from it
    (a horizontal ray to the waist axis), not of the nearest surface: the nearest surface at the
    flank is the hanging forearm, whose weights fold the band."""
    me = body.data
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(pl.vertices) for pl in me.polygons])
    gi = {g.index: g.name for g in body.vertex_groups}
    for g in list(piece.vertex_groups):
        piece.vertex_groups.remove(g)
    out = {n: piece.vertex_groups.new(name=n) for n in allow}
    for v in piece.data.vertices:
        p = piece.matrix_world @ v.co
        o = Vector((0.0, cy, p.z))
        d = Vector((p.x, p.y - cy, 0.0))
        hit = tree.ray_cast(o, d.normalized()) if d.length > 1e-6 else (None,)
        w = {}
        if hit[0] is not None:
            pl = me.polygons[hit[2]]
            for vi in pl.vertices:
                k_ = 1.0 / max(1e-4, (me.vertices[vi].co - hit[0]).length)
                for ge in me.vertices[vi].groups:
                    nm = gi[ge.group]
                    if nm in out:
                        w[nm] = w.get(nm, 0.0) + ge.weight * k_
        tot = sum(w.values())
        if tot < 1e-6:
            w, tot = {'hips': 1.0}, 1.0
        for nm, x in w.items():
            out[nm].add([v.index], x / tot, 'REPLACE')


def stage4(k, body, pieces):
    Jv = {n: Vector(p) for n, p in J.items()}
    ear_tip = Vector((0.37, 0.10, 0.99))                   # the drooped tip (stage 2 rotates 9 deg)
    rig = armature([
        ('hips', (0, 0.02, 0.34), (0, 0.0, 0.46), None),
        ('spine', (0, 0.0, 0.46), (0, -0.03, 0.58), 'hips', True),
        ('chest', (0, -0.03, 0.58), (0, -0.06, 0.68), 'spine', True),
        ('neck', (0, -0.06, 0.68), (0, -0.09, 0.78), 'chest', True),
        ('head', (0, -0.09, 0.78), (0, -0.12, 1.06), 'neck', True),
        ('ear.L', (0.185, -0.075, 0.955), tuple(ear_tip), 'head'),
        ('clavicle.L', (0.03, -0.06, 0.665), (0.15, -0.045, 0.645), 'chest'),
        ('upperarm.L', (0.17, -0.04, 0.63), J['elbow'], 'clavicle.L'),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('hand.L', J['wrist'], J['knuckle'], 'forearm.L', True),
        ('fingers.L', J['knuckle'], (0.275, -0.15, 0.12), 'hand.L', True),
        ('thigh.L', J['hip'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
        ('foot.L', J['ankle'], (0.125, -0.105, 0.03), 'shin.L', True),
        ('toes.L', (0.125, -0.105, 0.03), (0.13, -0.19, 0.015), 'foot.L', True),
    ])
    skin(body, rig)
    torso_off_arm(body)
    ramp_joint(body, (0.17, -0.04, 0.63), J['elbow'], 'upperarm.S', [('clavicle.S', 0.6), ('chest', 0.4)],
               0.12, -0.075, 0.07, keep=lambda p, sx: p.z > 0.60 or sx * p.x > 0.20)
    smooth_weights(body, (0.17, -0.04, 0.63), 0.09, 4)          # repair r2 item 4
    ramp_joint(body, J['knee'], J['ankle'], 'shin.S', [('thigh.S', 1.0)], 0.075, -0.035, 0.035)
    for p in pieces:
        nm = p.name
        if any(t in nm for t in ('eye', 'pupil', 'glint', 'fangs')):
            bind(p, rig, bone='head')
        elif 'loincloth' in nm:
            bind(p, rig, bone='hips')                      # rigid to the pelvis: no fold-over
        elif any(t in nm for t in ('belt', 'buckle')):
            # repair r2 item 2: the belt rides the waist skin under it (drift), but not the
            # thigh weights of the skin at the hip, which fold the stiff band in a stride
            bind(p, rig, bone='hips')
            waist_weights(p, body)
        else:
            bind(p, rig, body=body)                        # claws follow their digit's skin

    def both(d, bone, l, r=None):
        d[bone + '.L'] = l
        d[bone + '.R'] = r if r is not None else (l[0], -l[1], -l[2])

    # idle: 48 f � weight shift L/R, breathing, head looks around, one ear twitches
    idle = {}
    for f, sway, look, tw in ((1, 0, 0, 0), (12, 1, 18, 0), (20, 1, 18, 1), (24, 0, 0, 0),
                              (36, -1, -18, 0), (48, 0, 0, 0)):
        d = {'hips': (0, 0, 3 * sway), 'spine': (2 + abs(sway), 0, -1.5 * sway), 'chest': (1.5, 0, -1.5 * sway),
             'neck': (0, look * 0.4, 0), 'head': (-4 * abs(sway), look * 0.6, 3 * sway)}
        both(d, 'thigh', (-3 * sway, 0, 0), (3 * sway, 0, 0))
        both(d, 'shin', (4 * max(sway, 0), 0, 0), (4 * max(-sway, 0), 0, 0))
        both(d, 'upperarm', (4, 0, 0))
        both(d, 'ear', (18 * tw, 0, 0), (0, 0, 0))
        idle[f] = d
    clip(rig, 'idle', idle, loc={1: {'hips': (0, 0, 0)}, 12: {'hips': (0.012, -0.004, 0)}, 24: {'hips': (0, 0, 0)},
                               36: {'hips': (-0.012, -0.004, 0)}, 48: {'hips': (0, 0, 0)}})

    # move: 24 f � a sneaky crouched walk, legs and arms in opposition
    mv, lc = {}, {}
    for f, ph in ((1, 0.0), (7, 0.25), (13, 0.5), (19, 0.75), (25, 1.0)):
        a = math.sin(ph * 2 * math.pi)
        c = math.cos(ph * 2 * math.pi)
        d = {'hips': (0, 4 * a, 0), 'spine': (10, -4 * a, 0), 'chest': (6, -3 * a, 0), 'neck': (-10, 0, 0), 'head': (-4, 5 * a, 0)}
        d['thigh.L'] = (28 * a, 0, 0); d['thigh.R'] = (-28 * a, 0, 0)
        d['shin.L'] = (35 * max(c, 0) + 8, 0, 0); d['shin.R'] = (35 * max(-c, 0) + 8, 0, 0)
        d['foot.L'] = (-12 * a, 0, 0); d['foot.R'] = (12 * a, 0, 0)
        d['upperarm.L'] = (-22 * a, 0, 0); d['upperarm.R'] = (22 * a, 0, 0)
        d['forearm.L'] = (-15, 0, 0); d['forearm.R'] = (-15, 0, 0)
        both(d, 'ear', (-8 * abs(a), 0, 0))
        mv[f] = d
        lc[f] = {'hips': (0, -0.02 + 0.012 * abs(c), 0)}
    clip(rig, 'move', mv, loc=lc)

    # attack: 32 f � wind up, right claw raised overhead, lunge and swipe down across, recover
    at = {}
    for f, w, s_ in ((1, 0, 0), (9, 1, 0), (15, 1, 0.3), (19, 0, 1), (24, 0, 0.6), (32, 0, 0)):
        d = {'hips': (0, -10 * w + 12 * s_, 0), 'spine': (-8 * w + 16 * s_, -10 * w + 14 * s_, 0),
             'chest': (-6 * w + 10 * s_, -8 * w + 10 * s_, 0), 'neck': (6 * w - 6 * s_, 0, 0), 'head': (4 * w - 8 * s_, 6 * w, 0)}
        # bone-local X on the limb bones: + swings the tail back/up, - forward (probed)
        d['clavicle.R'] = (32 * w + 6 * s_, 0, 0)          # the shoulder shrugs up with the raise
        d['upperarm.R'] = (-125 * w - 35 * s_, 0, 40 * w + 10 * s_)
        d['forearm.R'] = (-45 * w - 10 * s_, 0, 0)
        d['hand.R'] = (20 * w - 30 * s_, 0, 0)
        d['fingers.R'] = (30 * w - 25 * s_, 0, 0)
        d['upperarm.L'] = (25 * w - 35 * s_, 0, 0)
        d['forearm.L'] = (-20 * w - 10 * s_, 0, 0)
        d['thigh.L'] = (10 * w - 30 * s_, 0, 0); d['thigh.R'] = (-6 * w + 14 * s_, 0, 0)
        d['shin.L'] = (10 * w + 25 * s_, 0, 0); d['shin.R'] = (6 * w + 8 * s_, 0, 0)
        d['ear.L'] = (-15 * w + 10 * s_, 0, 0); d['ear.R'] = (-15 * w + 10 * s_, 0, 0)
        at[f] = d
    clip(rig, 'attack', at, loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, -0.01, 0.02)}, 19: {'hips': (0, -0.03, -0.05)},
                                 32: {'hips': (0, 0, 0)}})
    if os.environ.get('GOB_DBG'):
        import techqa as Q
        for o in [body] + list(pieces):
            Q.triangulate_convex(o)
        for nm, act in ((a.name, a) for a in bpy.data.actions):
            counts, flags, _ = Q.measure(body, pieces, (1.1, 1.1, 1.1), rig, {nm: act})
            fl = [p for p, c in flags['body'].items() if c == 'flip']
            cs = [tuple(round(x, 3) for x in body.data.polygons[p].center) for p in fl]
            print('BMK DBG', nm, counts['body']['flip'], cs[:20])
            if os.environ.get('GOB_DBGF') and nm == 'attack':
                for f in (5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27):
                    act.use_frame_range = True; act.frame_start = f; act.frame_end = f + 0.01
                    counts, flags, _ = Q.measure(body, pieces, (1.1, 1.1, 1.1), rig, {nm: act})
                    print('BMK DBGF', f, counts['body']['flip'])
                act.use_frame_range = False
    return rig


run(META, stage1, stage2, stage3, stage4)
