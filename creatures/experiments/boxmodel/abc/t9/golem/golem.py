import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'kit'))
sys.path.insert(0, KIT)
from bmkit import *
from smooth_borders import smooth_borders
sys.path.insert(0, HERE)

# stone golem (t9 RECREATE 2026-10-23), t7 hand box model. ONE upright spine loft of 13-vertex half rings (2x),
# crotch -> crown, each ring from 5 control points (front seam, front corner, side, back corner, back seam) so the
# boulder chest is a ROUND mass with planes. The sheet's identity cue is in the base: a huge round chest boulder,
# a small head SUNK at the front of the dome between two giant shoulder boulders, massive segmented arm stones
# (shoulder boulder, upper-arm stone, forearm boulder, fist) hanging to the knees, short stone legs.
#  - arms: grown from a 3 x 3 window of the upper chest side (C2..S1: the chest's widest rings carry the shoulder
#    line, minotaur trick), first ring = 45 % transition ring, then the boulder (a vertical ring, a 45 deg ring) and
#    level rings down the arm, each stone a swell with a groove between;
#  - legs: 3 x 4 window of the pelvis underside/flank (broad root) + 45 % transition ring, level rings;
#  - head: extruded FORWARD from a 3 x 2 window of the dome front at the seam (seam walls removed: the mirror
#    closes it), so it sits low and sunk in the chest, not on top of it.
META = dict(creature='golem', model='opus', stage1_tris=(1500, 4500), total_tris=(2500, 7500), detail_tier=3,
            closeups=[('head', (0.0, -0.36, 1.78), 0.30, 'hero'),
                      ('fist', (0.89, -0.05, 0.42), 0.32, 'hero'),
                      ('shoulder', (0.70, 0.05, 1.62), 0.40, 'hero'),
                      ('foot', (0.38, -0.08, 0.10), 0.28, 'hero')])

J = dict(
    hips=(0.0, 0.02, 0.70), spine=(0.0, 0.02, 1.00), chest=(0.0, 0.02, 1.35), neck=(0.0, -0.08, 1.62),
    head=(0.0, -0.20, 1.70), top=(0.0, -0.34, 1.93),
    shoulder=(0.62, 0.07, 1.58), elbow=(0.86, 0.04, 1.11), wrist=(0.89, -0.09, 0.62), fist=(0.89, -0.12, 0.23),
    hipL=(0.33, 0.03, 0.66), knee=(0.345, 0.03, 0.41), ankle=(0.36, 0.01, 0.17), toe=(0.38, -0.34, 0.04),
)


# ---------------------------------------------------------------- the loft
def torso5(yf, yb, W, fx=0.62, fy=0.10, sy=0.45, bx=0.72, by=0.14):
    D = yb - yf
    return [(0.0, yf), (W * fx, yf + D * fy), (W, yf + D * sy), (W * bx, yb - D * by), (0.0, yb)]


RND = 0.55


def ring13(c5, z, rnd=RND):
    """13 points front seam -> back seam: 3 steps per control segment, a blend of the straight chord (planes) and
    a Catmull-Rom curve (round-over), the seam ends mirrored for the tangent (the mirror stays smooth)."""
    P = [Vector((x, y)) for x, y in c5]
    G = [Vector((-P[1].x, P[1].y))] + P + [Vector((-P[3].x, P[3].y))]
    out = []
    for s in range(4):
        p0, p1, p2, p3 = G[s], G[s + 1], G[s + 2], G[s + 3]
        for u in (0.0, 1 / 3, 2 / 3):
            lin = p1.lerp(p2, u)
            cr = 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                        + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
            q = lin.lerp(cr, rnd)
            out.append((max(q.x, 0.0) if s or u else 0.0, q.y, z))
    out.append((0.0, P[4].y, z))
    return out


KEY = [   # (name, z, front y, back y, half width) bottom -> top, read off reference/front.png + side.png (m)
    ('L0', 0.54, -0.14, 0.16, 0.12),     # crotch
    ('L0b', 0.60, -0.22, 0.25, 0.26),    # pelvis underside
    ('L0c', 0.67, -0.27, 0.30, 0.36),    # hip floor (the thighs rise out of it)
    ('L1', 0.76, -0.31, 0.33, 0.40),     # pelvis stone top / hips
    ('B0', 0.86, -0.37, 0.35, 0.42),     # under the belly stone
    ('B1', 0.95, -0.47, 0.41, 0.47),     # belly stone
    ('C0', 1.07, -0.53, 0.44, 0.52),     # chest boulder: lower round-over (rebuild2: +4 cm forward, sheet side)
    ('C1', 1.22, -0.565, 0.46, 0.55),     # chest boulder front-most (sheet side: the bulge well ahead of the arm)
    ('C2', 1.38, -0.55, 0.47, 0.55),     # chest boulder widest
    ('C3', 1.50, -0.47, 0.47, 0.51),     # upper chest; the boulder window's bottom
    ('S0', 1.60, -0.37, 0.46, 0.47),     # the head root's bottom
    ('S1', 1.70, -0.31, 0.44, 0.42),     # dome round-over behind the head
    ('S2', 1.79, -0.22, 0.40, 0.34),
    ('T0', 1.86, -0.12, 0.33, 0.26),     # back hump top; the boulder window's top
    ('T1', 1.91, -0.04, 0.20, 0.14),     # crown of the dome (capped): low between the boulders
]
SECS = [(nm, ring13(torso5(yf, yb, W), z)) for nm, z, yf, yb, W in KEY]


def P(nm):
    for n, pts in SECS:
        if n == nm:
            return [Vector(q) for q in pts]


# ---------------------------------------------------------------- limb sections
# (centre, e_p, e_q, r_p, r_q, n): e_p is the window's ring direction (p = -1 first ring of the window .. +1 last),
# e_q its column direction (q = -1 first column .. +1 last); n the superellipse exponent (2 round, 3+ boxy).
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
D45 = (0.7071, 0, 0.7071)


def lev(c, rx, ry, n=2.4):
    return (c, X, Y, rx, ry, n)


def tilt(deg):
    t = math.radians(deg)
    return (math.sin(t), 0.0, math.cos(t))


def fan(K, deg, d0, L, rq, n=2.2, yc=None):
    """A boulder ring fanned about the armpit pivot K: its plane holds the pivot's y axis direction and e_p at `deg`
    from vertical toward +x; its inner end d0 from K, its outer end d0 + L (so the rings of the turn share the armpit
    and never cross there)."""
    ep = tilt(deg)
    c = Vector(K) + Vector(ep) * (d0 + L / 2)
    if yc is not None:
        c.y = yc
    return (tuple(c), ep, Y, L / 2, rq, n)


KP = (0.64, 0.06, 1.37)          # the armpit pivot under the shoulder boulder
def arc(pin, deg, L, rq, n=2.2, yc=0.06):
    """A shoulder-turn ring: its inner end at `pin` (x, z), e_p at `deg` from vertical toward +x, length L. The inner
    ends step round the armpit so the 180 deg turn from the chest wall to the arm's inner wall is spread over five
    folds under 60 deg each (s1 r10: one notch apex read as a 110-170 deg knife)."""
    ep = tilt(deg)
    c = Vector((pin[0], yc, pin[1])) + Vector(ep) * (L / 2)
    return (tuple(c), ep, Y, L / 2, rq, n)


ARM = [arc((0.585, 1.565), 0, 0.355, 0.34),             # shoulder mass inner ring (over the chest top, to 1.92)
       arc((0.63, 1.53), 0, 0.40, 0.37),                # widest: vertical ring x 0.63 (to 1.93)
       arc((0.645, 1.47), 42, 0.45, 0.34),              # turning down over the shoulder
       arc((0.645, 1.40), 72, 0.33, 0.30, yc=0.05),     # outer-underside (the S3 boulder sits over all four)
       lev((0.83, 0.07, 1.33), 0.20, 0.23),             # groove under the boulder (upper-arm stone top)
       lev((0.84, 0.07, 1.23), 0.235, 0.26),            # upper-arm stone (rebuild2: narrower, set back under the boulder)
       lev((0.86, 0.04, 1.11), 0.20, 0.22),             # elbow groove
       lev((0.88, 0.00, 1.02), 0.28, 0.28),             # forearm boulder top (rebuild2: the forearm swings forward
       lev((0.90, -0.04, 0.86), 0.31, 0.30),            #   and out, the biggest arm stone, sheet front + side)
       lev((0.90, -0.07, 0.72), 0.28, 0.28),            # forearm boulder bottom
       lev((0.89, -0.09, 0.62), 0.19, 0.20),            # wrist groove
       lev((0.89, -0.11, 0.53), 0.26, 0.25),            # fist top
       lev((0.89, -0.12, 0.38), 0.27, 0.25),            # fist
       lev((0.89, -0.12, 0.23), 0.22, 0.20)]            # fist bottom (the end cap): low, near the knee (sheet)
LEG = [lev((0.33, 0.05, 0.52), 0.18, 0.20),             # thigh stone top
       lev((0.34, 0.03, 0.44), 0.19, 0.21),             # thigh stone
       lev((0.345, 0.03, 0.36), 0.165, 0.18),           # knee groove
       lev((0.35, 0.02, 0.28), 0.18, 0.19),             # shin stone
       lev((0.36, 0.01, 0.18), 0.16, 0.17),             # ankle
       lev((0.38, -0.03, 0.11), 0.22, 0.32, 2.6),       # foot stone top (rebuild2: heel 5 cm further back, sheet side)
       lev((0.38, -0.03, 0.0), 0.235, 0.34, 2.8)]       # sole
HEAD = [((0.0, -0.41, 1.775), Z, X, 0.165, 0.205, 3.2),   # skull back (s1 r7: every head ring ahead of the window's
        ((0.0, -0.45, 1.78), Z, X, 0.160, 0.205, 3.2),    #   bottom edge, chin above the chest slope: no fold-back)
        ((0.0, -0.475, 1.77), Z, X, 0.135, 0.175, 2.6)]    # face front bevel (the end cap = the face plane)   # face front bevel (the end cap = the face plane)
T1_ARM, T1_LEG, T1_HEAD = 0.45, 0.45, 0.45


def spow(c, e):
    return math.copysign(abs(c) ** e, c)


def sec_pos(sec, th):
    c, ep, eq, rp, rq, n = sec
    e = 2.0 / n
    return Vector(c) + Vector(ep) * (rp * spow(math.cos(th), e)) + Vector(eq) * (rq * spow(math.sin(th), e))


def sec_inner(sec, p, q, k_=0.85):
    c, ep, eq, rp, rq, n = sec
    return Vector(c) + Vector(ep) * (p * rp * k_) + Vector(eq) * (q * rq * k_)


def akey(t):
    return round(t if t < math.pi - 1e-6 else -math.pi, 4)


def grow(bm, rings, spans, i0, A, j0, B, secs, t1, half=False):
    """Extrude the A x B window (rings i0..i0+A, ring vertices j0..j0+B) section by section. Window roles: p from
    the ring index (-1 .. +1), q from the column (-1 .. +1; half=True: 0 at the seam column .. 1). Boundary roles sit
    on each section's superellipse at evenly spaced angles; interior roles inside it (the end cap grid). The first
    new ring is the 45 % transition ring: the window rim t1 of the way to secs[0], keeping the window's own angles.
    half=True: the window touches the mirror seam; the seam walls of every extrusion are removed."""
    faces = [spans[i0 + a][j0 + b] for a in range(A) for b in range(B)]
    roles = []
    for a in range(A + 1):
        for b in range(B + 1):
            p = 2 * a / A - 1
            q = (b / B) if half else (2 * b / B - 1)
            roles.append((rings[i0 + a][j0 + b].co.copy(), (p, q)))
    bnd = lambda p, q: abs(p) > 0.999 or abs(q) > 0.999
    kf = (lambda t: round(t, 4)) if half else akey
    th = sorted({kf(math.atan2(q, p)) for _c, (p, q) in roles if bnd(p, q)})
    N = len(th)
    if half:
        amap = {t: math.pi * i / (N - 1) for i, t in enumerate(th)}
    else:
        off = 0.0 if any(abs(t) < 1e-6 for t in th) else math.pi / N
        base = min(range(N), key=lambda i: abs(th[i] - (-math.pi + off)))
        amap = {th[(base + i) % N]: -math.pi + off + 2 * math.pi * i / N for i in range(N)}

    def place(sec, p0, ro, first):
        p, q = ro
        if bnd(p, q):
            t = kf(math.atan2(q, p))
            tgt = sec_pos(sec, t if first else amap[t])
        else:
            tgt = sec_inner(sec, p, q)
        return p0.lerp(tgt, t1) if first else tgt

    def step(faces, roles, sec, first):
        r = extrude(bm, faces)
        new = []
        for v in r['verts']:
            o = min(roles, key=lambda o_: (o_[0] - v.co).length)
            new.append((v, o))
        for v, (p0, ro) in new:
            v.co = place(sec, p0, ro, first)
            if half and abs(ro[1]) < 1e-9:
                v.co.x = 0.0
        if half:
            walls = [f for f in r['sides'] if all(abs(w.co.x) < 1e-6 for w in f.verts)]
            bmesh.ops.delete(bm, geom=walls, context='FACES')
        return r['faces'], [(v.co.copy(), ro) for v, (p0, ro) in new]
    faces, roles = step(faces, roles, secs[0], True)
    for sec in secs:
        faces, roles = step(faces, roles, sec, False)
    return faces, roles


AJ, LJ, HJ = 3, 4, 0       # first window column of the arm, leg and head windows


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, _p) in enumerate(SECS)}
    rings = [ring(bm, pts) for _n, pts in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    grow(bm, rings, spans, idx['C3'], 4, AJ, 6, ARM, T1_ARM)
    grow(bm, rings, spans, idx['L0'], 3, LJ, 5, LEG, T1_LEG)
    faces, roles = grow(bm, rings, spans, idx['S0'], 3, HJ, 2, HEAD, T1_HEAD, half=True)
    for v in {v for f in faces for v in f.verts}:      # the face plane bows forward at the seam (eyes face out)
        if v.co.x < 1e-6:
            v.co.y -= 0.03
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
EYE = Vector((0.115, -0.47, 1.785))     # the eye point on the face plane (x, z); y from a ray from the front
SOCKET = []


def head_verts(bm, pred):
    return [v for v in bm.verts if v.co.y < -0.30 and v.co.z > 1.58 and pred(v.co)]


def stage2(k, body):
    """Eye sockets on face planes turned 30 deg outward, a brow ridge over them, a jaw step; flat face planes."""
    bm = edit(body)
    recalc_normals(bm)
    # face planes: the outer face column (x > 0.05) turns outward (its outer edge 3.5 cm back), so the eye looks
    # front and side; the brow row (z > 1.80) comes 2 cm forward over it; the jaw row (z < 1.73) 1 cm forward
    outer = head_verts(bm, lambda c: c.x > 0.14 and c.y < -0.42)
    move(outer, (0.0, 0.035, 0.0))
    brow = head_verts(bm, lambda c: c.z > 1.81 and c.y < -0.39)
    move(brow, (0.0, -0.02, 0.006))
    jaw = head_verts(bm, lambda c: c.z < 1.715 and c.y < -0.41)
    move(jaw, (0.0, -0.012, -0.004))
    recalc_normals(bm)
    tree = BVHTree.FromBMesh(bm)
    hit, hn = tree.ray_cast(Vector((EYE.x, -1.2, EYE.z)), Vector((0, 1, 0)), 2.0)[:2]
    f = face_near(bm, hit, n=hn)
    fn = f.normal.copy()
    say('golem eye face', tuple(round(q, 3) for q in f.calc_center_median()), 'normal', tuple(round(q, 2) for q in fn),
        'verts', len(f.verts))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face under the brow'):
        inner = inset(bm, [f], 0.22, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.008)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.04 and abs(c.y - ec0.y) < 0.04 and abs(c.z - ec0.z) < 0.04)
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


PAL = {'stone': '#aea89f', 'plate': '#c2bbb0', 'seam': '#7f7a73', 'moss': '#76a440', 'glow': '#62e4ff',
       'pupil': '#1b7895'}
PAL['moss'] = '#6b8f3c'                                   # rebuild2: olive moss (sheet), not the bright cap green
GROOVES_ARM = (1.33, 1.12, 0.63)        # z of the arm's groove rings (stone seams)
GROOVES_LEG = (0.36, 0.18)


def is_leg(c):
    x, y, z = abs(c.x), c.y, c.z
    return z < 0.535 and math.hypot(x - 0.37, (y + 0.02) * 0.8) < 0.30


def is_arm(c):
    return abs(c.x) > 0.56 and c.z < 1.50 and not is_leg(c)


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if is_arm(c):
        if any(abs(z - g) < 0.032 for g in GROOVES_ARM):
            return 'seam'                                # the grooves between the arm stones
        # moss drips down the outer upper arm from under the shoulder boulder (sheet front + side)
        for yk, z0 in ((-0.07, 1.10), (0.13, 1.18)):     # two tapering streaks, widest under the boulder
            if x > 0.78 and n.x > 0.2 and z0 < z < 1.42 and abs(y - yk) < 0.025 + 0.075 * (z - z0) / (1.42 - z0):
                return 'moss'
        return 'stone'
    if is_leg(c):
        if any(abs(z - g) < 0.028 for g in GROOVES_LEG):
            return 'seam'
        return 'stone'
    return 'stone'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h, sides=8):
    """A low-poly eye lens: back cone, iris ring, pupil cap (domed, so it shows from the side too)."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * 2 * math.pi / sides for k_ in range(sides)]]
    R, I = ring_(r, 0.0), ring_(r * 0.6, h * 0.75)
    A, Bv = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.4)
    for j in range(sides):
        a, b = j, (j + 1) % sides
        bm.faces.new([Bv, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def full_tree(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def cast(tree, o, d, far=4.0):
    d = Vector(d).normalized()
    loc, nrm, _i, _d = tree.ray_cast(Vector(o), d, far)
    if loc is None:
        return None
    nrm = nrm.normalized()
    return loc, (nrm if nrm.dot(d) < 0 else -nrm)


def conform(bm, tree, o, d, up, a, b, h, na=4, nb=None, sink=0.02, rim=0.012, keepx=True, disc=0.6):
    """A stone plate that follows the body: a quad grid over a rounded-rectangle outline (half sizes a along `up`,
    b across) laid on the surface hit from o along d; every grid point cast onto the body, the top raised a dome
    profile (rim 1.2 cm, centre h) along the local normal, the bottom sunk `sink` under the skin, closed by a rim
    wall: a closed, seated slab of near-square quads (no centre fan, no needles)."""
    C, N = cast(tree, o, d)
    up = Vector(up)
    U = (up - N * up.dot(N)).normalized()
    V = N.cross(U)
    nb = nb or max(3, min(12, int(round(na * b / a))))
    G = []
    for i in range(na + 1):
        row = []
        for j in range(nb + 1):
            s_, t_ = 2 * i / na - 1, 2 * j / nb - 1
            ds, dt = s_ * math.sqrt(1 - t_ * t_ / 2), t_ * math.sqrt(1 - s_ * s_ / 2)
            u_, v_ = s_ + (ds - s_) * disc, t_ + (dt - t_) * disc
            Q = C + U * (a * u_) + V * (b * v_)
            r = cast(tree, Q + N * 0.30, -N, 2.0)          # s4 r4: far 0.6 -> 2.0 (edge samples on a curving
            if r is None:                                  #   dome missed and stood as plane points: spikes)
                r = cast(tree, Q + N * 0.30, (C - N * 0.4) - (Q + N * 0.30), 2.0)
            S, Ns = r if r is not None else (Q, N)
            Ns = (Ns + N).normalized()
            rho = max(abs(s_), abs(t_))
            hh = rim if rho > 0.999 else rim + (h - rim) * (1 - rho ** 2.5)
            row.append((S + Ns * hh, S - Ns * sink))
        G.append(row)
    if keepx:
        lo = min(min(p[0].x, p[1].x) for row in G for p in row)
        if lo < 0.004:
            sh = Vector((0.004 - lo, 0, 0))
            G = [[(p[0] + sh, p[1] + sh) for p in row] for row in G]
    T = [[bm.verts.new(p[0]) for p in row] for row in G]
    Bt = [[bm.verts.new(p[1]) for p in row] for row in G]
    for i in range(na):
        for j in range(nb):
            bm.faces.new([T[i][j], T[i + 1][j], T[i + 1][j + 1], T[i][j + 1]])
            bm.faces.new([Bt[i][j], Bt[i][j + 1], Bt[i + 1][j + 1], Bt[i + 1][j]])
    loop = [(0, j) for j in range(nb)] + [(i, nb) for i in range(na)] + [(na, j) for j in range(nb, 0, -1)] +            [(i, 0) for i in range(na, 0, -1)]
    for q in range(len(loop)):
        (i0, j0), (i1, j1) = loop[q], loop[(q + 1) % len(loop)]
        bm.faces.new([T[i0][j0], T[i1][j1], Bt[i1][j1], Bt[i0][j0]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def rock(bm, c, r, sect=12, stacks=7, flat=0.0, rb=None):
    """A low-poly boulder: an ellipsoid of `stacks` rings x `sect` sectors, every other ring turned half a sector
    (diamond facets: a cut stone, not a lathe), poles capped by one vertex each."""
    c = Vector(c)
    rings = []
    for i in range(1, stacks):
        ph = math.pi * i / stacks - math.pi / 2
        off = (math.pi / sect) * (i % 2)
        ring_ = []
        for j in range(sect):
            t = 2 * math.pi * j / sect + off
            rz = r[2] if (ph >= 0 or rb is None) else rb
            ring_.append(bm.verts.new(c + Vector((r[0] * math.cos(ph) * math.cos(t), r[1] * math.cos(ph) * math.sin(t),
                                                  rz * math.sin(ph)))))
        rings.append(ring_)
    bot = bm.verts.new(c - Vector((0, 0, (r[2] if rb is None else rb) * (1 - flat))))
    top = bm.verts.new(c + Vector((0, 0, r[2])))
    for j in range(sect):
        bm.faces.new([bot, rings[0][(j + 1) % sect], rings[0][j]])
        bm.faces.new([top, rings[-1][j], rings[-1][(j + 1) % sect]])
    for A, B in zip(rings, rings[1:]):
        for j in range(sect):
            bm.faces.new([A[j], A[(j + 1) % sect], B[(j + 1) % sect], B[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def crack(bm, tree, pts, w, up=0.010, sink=0.012):
    """The glowing chest crack (sheet front: a blue zig-zag down the chest boulder's centre): a ribbon of quads cast
    onto the body from the front, raised `up` over the skin and sunk `sink` under it, closed by end and side walls
    (a seated closed slab, not a decal)."""
    S, N = [], []
    dense = []
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):       # 4 casts per zig segment: the chord never dips under the skin
        dense += [(x0 + (x1 - x0) * u / 4, z0 + (z1 - z0) * u / 4) for u in range(4)]
    dense.append(pts[-1])
    for x, z in dense:
        r = cast(tree, (x, -1.5, z), (0, 1, 0))
        S.append(r[0]); N.append(r[1])
    T, Bt = [], []
    for i in range(len(S)):
        a, b = S[max(i - 1, 0)], S[min(i + 1, len(S) - 1)]
        t = (b - a).normalized()
        side = N[i].cross(t).normalized()
        ww = w * (0.55 if i in (0, len(S) - 1) else 1.0)
        for sgn in (-1, 1):
            T.append(bm.verts.new(S[i] + side * (sgn * ww / 2) + N[i] * up))
            Bt.append(bm.verts.new(S[i] + side * (sgn * ww / 2) - N[i] * sink))
    n = len(S)
    for i in range(n - 1):
        a0, a1, b0, b1 = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        bm.faces.new([T[a0], T[a1], T[b1], T[b0]])
        bm.faces.new([Bt[a0], Bt[b0], Bt[b1], Bt[a1]])
        bm.faces.new([T[a0], T[b0], Bt[b0], Bt[a0]])
        bm.faces.new([T[a1], Bt[a1], Bt[b1], T[b1]])
    bm.faces.new([T[0], Bt[0], Bt[1], T[1]])
    bm.faces.new([T[-2], T[-1], Bt[-1], Bt[-2]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


CRACK = [(0.022, 1.535), (0.042, 1.50), (0.020, 1.435), (0.044, 1.365), (0.022, 1.30), (0.042, 1.245), (0.026, 1.20)]   # all on x > 0: techqa splits a centre piece by side


def toe(bm, base, out, w, h, L):
    """A chunky stone toe: a rounded-square section pushed out of the foot front, root sunk 3 cm, blunt round tip."""
    out = Vector(out).normalized()
    side = out.cross(Vector((0, 0, 1))).normalized()
    up = Vector((0, 0, 1))
    SEC = [(-1, 0), (-0.8, 0.7), (-0.35, 1.0), (0.35, 1.0), (0.8, 0.7), (1, 0)]
    rows = []
    for off, sw, sh in ((-0.03, 1.0, 1.0), (L * 0.55, 1.0, 0.95), (L, 0.7, 0.6)):
        cc = base + out * off
        rows.append([bm.verts.new(cc + side * (su * w / 2 * sw) + up * (sz * h * sh)) for su, sz in SEC])
    n = len(SEC)
    bm.faces.new(list(reversed(rows[0])))
    for A, B in zip(rows, rows[1:]):
        for j in range(n):
            bm.faces.new([A[j], A[(j + 1) % n], B[(j + 1) % n], B[j]])
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


BOULDER = ((0.66, 0.06, 1.68), (0.38, 0.41, 0.34), 0.13)   # shoulder boulder (centre, radii, lower z radius): top 2.0,
BOULDER_TILT = 20.0   # rebuild2: the boulder rolled 20 deg outward (outer side low over the upper arm, a round stone,
#   not a flat cap; its inner underside stays above the armpit so the body crosses it once)
#   a flatter underside at 1.57 resting on the shoulder mass, so the mass's underside stays outside it (one crossing)


VAR = os.environ.get('GOLEM_VAR', '')


def boulder_rule(c, n, i):
    cc = Vector(BOULDER[0])
    d = c - cc
    th = math.atan2(d.y, d.x)
    # rebuild2: moss drapes the top-outer of the stone (sheet front/top: the inner top stays bare stone next to the
    # head) and hangs down the outer side in uneven drip lobes that run on into the upper-arm streaks
    lobe = math.cos(5 * th + 0.6) + 0.5 * math.cos(9 * th + 1.7)
    if n.z > 0.30 and d.x > -0.10 - 0.06 * math.cos(3 * th):
        return 'moss'
    if d.x > 0.05 and n.z > -0.45 and lobe > 0.55:
        return 'moss'
    return 'plate'


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('stone', 'seam', 'moss')}, body_rule)
    smooth_borders(body, k=k, iters=8)                   # owner 10-21: borders follow the form
    tree = full_tree(body)
    pieces = []

    def piece(name, bm, cols, rule=None, mirror=True):
        ob = object_from_bm(name, bm, mirror=mirror)
        cols = cols if isinstance(cols, dict) else {cols: PAL[cols]}
        paint(ob, cols, rule or (lambda c_, n_, i: next(iter(cols))))
        pieces.append(ob)
        return ob
    # eye: a glowing round lens with a darker pupil disc, domed, its normal turned out toward the side
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = (n + Vector((0.25, -0.05, 0.0))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.002, n, 0.022, 0.016)
    piece('eye', bm, {'glow': PAL['glow'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.009 and n_.dot(n) > 0.6 else 'glow')
    # brow: one heavy stone ridge over both eyes
    import detail_pieces as D
    e = SOCKET[0]
    bm = bmesh.new()       # one heavy stone ridge across both eyes (r3: two knobs read as cartoon eyebrows)
    conform(bm, tree, (0.0, -1.2, e.z + 0.048), (0, 1, 0), (0, 0, 1), 0.026, 0.13, 0.03, na=2, nb=6, keepx=False)
    piece('brow', bm, 'plate', mirror=False)
    # shoulder boulders: round stones over the shoulder masses, moss on top dripping down
    bm = bmesh.new()
    rock(bm, BOULDER[0], BOULDER[1], sect=12, stacks=7, rb=BOULDER[2])
    ct, a_ = Vector(BOULDER[0]), math.radians(BOULDER_TILT)
    for v in bm.verts:
        d_ = v.co - ct
        v.co = ct + Vector((d_.x * math.cos(a_) + d_.z * math.sin(a_), d_.y, -d_.x * math.sin(a_) + d_.z * math.cos(a_)))
    piece('boulder', bm, {'plate': PAL['plate'], 'moss': PAL['moss']}, boulder_rule)
    # torso stone plates (sheet front: two pec plates, a belly band, the pelvis plate; rear: two back plates, a band,
    # the rump plate); the darker body between them reads as the seams
    PL = [('plate_chest', (0.27, -1.5, 1.38), (0, 1, 0), 0.19, 0.20, 0.05, True),
          ('plate_back', (0.235, 1.5, 1.50), (0, -1, 0), 0.25, 0.20, 0.05, True),
          ('plate_belly', (0.0, -1.5, 1.05), (0, 1, 0), 0.13, 0.34, 0.05, False),   # rebuild2: a taller lens-shaped plate, not a band
          ('plate_pelvis', (0.0, -1.5, 0.73), (0, 1, 0), 0.10, 0.27, 0.04, False),
          ('plate_lowback', (0.0, 1.5, 1.13), (0, -1, 0), 0.11, 0.38, 0.045, False),
          ('plate_rump', (0.0, 1.5, 0.75), (0, -1, 0), 0.10, 0.28, 0.04, False),
          ('plate_forearm', (1.6, -0.01, 0.88), (-1, 0, 0), 0.12, 0.17, 0.045, True),
          ('plate_knee', (0.345, -1.5, 0.40), (0, 1, 0), 0.06, 0.09, 0.04, True),
          ('plate_shin', (0.35, -1.5, 0.26), (0, 1, 0), 0.055, 0.085, 0.035, True)]
    for nm, o, d, a_, b_, h_, mir in PL:
        bm = bmesh.new()
        conform(bm, tree, o, d, (0, 0, 1), a_, b_, h_, keepx=mir)
        piece(nm, bm, 'plate', mirror=mir)
    # the glowing chest crack (sheet identity cue: blue zig-zag down the chest boulder's centre)
    bm = bmesh.new()
    crack(bm, tree, CRACK, 0.032)
    piece('crack', bm, 'glow', mirror=False)
    # fist: three chunky knuckle blocks across the front of each fist
    bm = bmesh.new()
    for x in (0.79, 0.885, 0.98):
        conform(bm, tree, (x, -1.5, 0.37), (0, 1, 0), (0, 0, 1), 0.075, 0.042, 0.05, na=3, nb=2)
    piece('knuckle_plate', bm, 'plate')
    # toes: three fat stone toes on the front of each foot
    bm = bmesh.new()
    for x in (0.285, 0.38, 0.475):
        r = cast(tree, (x, -1.5, 0.045), (0, 1, 0))
        toe(bm, Vector((x, r[0].y + 0.01, 0.008)), (0, -1, 0), 0.085, 0.085, 0.085)
    piece('toe', bm, 'stone')
    return pieces


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['top'], 'neck', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['fist'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: slow heavy breathing through the chest, a head turn, the fists sway
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0)},
                       24: {'head': (0, 0, 6)}, 36: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, -4)}, 48: {}})
    # move: a heavy stomp; the swinging leg folds at the knee, the arms swing against the legs, the hips bob
    A, S = 18, 12
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 4)},
        9: {'shin.R': (-32, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0), 'spine': (0, 0, -4)},
        25: {'shin.L': (-32, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 4)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0, -0.025)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0, -0.025)},
             33: {'hips': (0, 0, 0)}})
    # attack: a two-fist overhead smash (raise, then slam down and forward with a chest lunge)
    up = {'upperarm.L': (70, 0, 0), 'upperarm.R': (70, 0, 0), 'forearm.L': (25, 0, 0), 'forearm.R': (25, 0, 0)}   # +X = forward/up (roll auto)
    clip(rig, 'attack', {
        1: {},
        12: dict(up, chest=(-8, 0, 0), head=(-5, 0, 0)),
        19: {'upperarm.L': (22, 0, 0), 'upperarm.R': (22, 0, 0), 'chest': (14, 0, 0), 'spine': (6, 0, 0), 'head': (4, 0, 0)},
        26: {'upperarm.L': (18, 0, 0), 'upperarm.R': (18, 0, 0), 'chest': (12, 0, 0), 'spine': (5, 0, 0)},
        36: {}},
        loc={1: {'hips': (0, 0, 0)}, 12: {'hips': (0, 0.03, 0)}, 19: {'hips': (0, -0.05, -0.04)}, 26: {'hips': (0, -0.05, -0.04)},
             36: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
