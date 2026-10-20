import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# Golden eagle standing with its wings spread wide, t7 hand box model: one spine loft of 13-point half rings
# (fan-tail tip -> hooked beak tip) leaning like the sheet's upright side view; the wings are extruded from broad
# 10 x 2 face regions of the shoulder (the back's top plane runs into the upper wing, the flank into the
# underwing), the feathered legs from 4 x 3 regions of the lower belly. Wing primaries ("fingers"), tail feather
# tips, lens eyes and the yellow raptor feet are stage-3 pieces. Sheet: side view for the body (its folded wings
# are ignored), front and top views for the spread wings.
META = dict(creature='eagle', detail_tier=2, model='opus', stage1_tris=(2400, 4600), total_tris=(3200, 7000),
            closeups=[('head', (0.0, -0.33, 0.79), 0.12, 'hero'),
                      ('foot', (0.07, -0.16, 0.06), 0.10, 'hero'),
                      ('wing root', (0.12, -0.08, 0.62), 0.22, 'hero'),
                      ('wing tip', (0.80, -0.08, 0.68), 0.25, 'hero')])

J = dict(
    hips=(0.0, 0.06, 0.36), spine=(0.0, -0.04, 0.47), chest=(0.0, -0.12, 0.58),
    neck=(0.0, -0.20, 0.70), head=(0.0, -0.26, 0.78), beak=(0.0, -0.43, 0.75),
    tail0=(0.0, 0.15, 0.26), tail1=(0.0, 0.40, 0.05),
    hipL=(0.088, -0.11, 0.29), knee=(0.086, -0.125, 0.15), ankle=(0.078, -0.125, 0.05), toe=(0.078, -0.22, 0.02),
    wing=(0.09, -0.12, 0.66), elbow=(0.36, -0.13, 0.70), wrist=(0.56, -0.14, 0.72), wtip=(0.92, -0.12, 0.68),
)


def dens(p):
    """The 2x density rule: a point on the straight midpoint of every span of the 7-point profile (13 points)."""
    out = []
    for a, b in zip(p, p[1:]):
        out += [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)]
    return out + [p[-1]]


# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = dens([(0, 1), (0.55, 0.95), (0.9, 0.62), (1, 0.12), (0.94, -0.38), (0.62, -0.82), (0, -1)])
NECK = dens([(0, 1), (0.6, 0.93), (0.93, 0.55), (1, 0.0), (0.93, -0.5), (0.6, -0.88), (0, -1)])
HEAD = dens([(0, 1), (0.45, 0.96), (0.82, 0.76), (1, 0.32), (1, -0.15), (0.78, -0.66), (0, -1)])
BEAK = dens([(0, 1), (0.6, 0.86), (0.95, 0.42), (1, -0.08), (0.82, -0.55), (0.45, -0.9), (0, -1)])
KEEL = dens([(0, 1), (0.55, 0.95), (0.9, 0.62), (1, 0.12), (0.94, -0.38), (0.6, -0.86), (0, -1.2)])   # s1 r11: belly keel between the thighs (r15 tried -1.3: worse, reverted)
TAIL = dens([(0, 1), (0.45, 1.0), (0.85, 0.75), (1, 0.0), (0.85, -0.75), (0.45, -1.0), (0, -1)])   # flat fan


def tb(nm, top, bot, W, prof):
    """A section from its top (back) and bottom (front) seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, a, h, h, W, prof)


def ax(nm, c, d, h, W, prof=TAIL):
    """A tail section from its centre and the tail's direction (y, z)."""
    l = math.hypot(*d)
    py, pz = d[1] / l, -d[0] / l
    if pz < 0:
        py, pz = -py, -pz
    return tb(nm, (c[0] + py * h, c[1] + pz * h), (c[0] - py * h, c[1] - pz * h), W, prof)


TD = (0.255, -0.215)          # tail direction, root -> tip
BASE = [
    ax('T0', (0.40, 0.05), TD, 0.016, 0.19),
    ax('T1', (0.335, 0.105), TD, 0.020, 0.17),
    ax('T2', (0.27, 0.16), TD, 0.026, 0.145),
    ax('T3', (0.21, 0.21), TD, 0.036, 0.115),
    ax('T4', (0.165, 0.25), TD, 0.050, 0.09),     # r04: thicker fan root (undertail coverts)
    tb('R0', (0.178, 0.316), (0.08, 0.23), 0.075, BODY),
    tb('R1', (0.156, 0.382), (0.03, 0.258), 0.095, BODY),
    tb('R2', (0.137, 0.45), (-0.045, 0.278), 0.108, KEEL),
    tb('M0', (0.111, 0.517), (-0.13, 0.28), 0.118, KEEL),
    tb('M1', (0.076, 0.567), (-0.19, 0.325), 0.124, KEEL),
    tb('M2', (0.041, 0.612), (-0.245, 0.375), 0.127, BODY),
    tb('C0', (0.003, 0.65), (-0.28, 0.43), 0.127, BODY),
    tb('C1', (-0.037, 0.681), (-0.30, 0.49), 0.122, BODY),
    tb('C2', (-0.082, 0.704), (-0.31, 0.55), 0.115, BODY),
    tb('C3', (-0.127, 0.721), (-0.31, 0.61), 0.105, NECK),
    tb('N0', (-0.17, 0.74), (-0.305, 0.66), 0.09, NECK),
    tb('N1', (-0.20, 0.77), (-0.305, 0.70), 0.076, NECK),
    tb('H0', (-0.225, 0.805), (-0.31, 0.722), 0.070, HEAD),
    tb('H1', (-0.255, 0.835), (-0.33, 0.73), 0.066, HEAD),
    tb('H2', (-0.29, 0.848), (-0.35, 0.738), 0.060, HEAD),
    tb('H3', (-0.325, 0.84), (-0.365, 0.745), 0.052, HEAD),
    tb('H4', (-0.355, 0.822), (-0.378, 0.752), 0.036, BEAK),     # cere
    tb('B0', (-0.38, 0.808), (-0.388, 0.756), 0.026, BEAK),
    tb('B1', (-0.40, 0.797), (-0.40, 0.756), 0.021, BEAK),
    tb('B2', (-0.418, 0.783), (-0.41, 0.752), 0.017, BEAK),
    tb('B3', (-0.43, 0.763), (-0.417, 0.742), 0.012, BEAK),
    tb('B4', (-0.43, 0.742), (-0.42, 0.728), 0.006, BEAK),       # the hook, tipped down
]
DENSE_FROM, DENSE_TO = 'T2', 'H2'      # 2x: a flat in-between station in every span of the tail, body, neck and skull


def _lerp_sec(a, b, t, nm):
    _, ca, aa, Ta, Ba, Wa, pa = a
    _, cb, ab, Tb, Bb, Wb, pb = b
    L = lambda u, v: u + (v - u) * t
    return (nm, (L(ca[0], cb[0]), L(ca[1], cb[1])), L(aa, ab), L(Ta, Tb), L(Ba, Bb), L(Wa, Wb),
            [(L(p[0], q[0]), L(p[1], q[1])) for p, q in zip(pa, pb)])


def build_secs():
    names = [s[0] for s in BASE]
    i0, i1 = names.index(DENSE_FROM), names.index(DENSE_TO)
    out = []
    for i, s in enumerate(BASE):
        out.append(s)
        if i0 <= i < i1:
            out.append(_lerp_sec(s, BASE[i + 1], 0.5, s[0] + 'b'))
    return out


SECS = build_secs()
IDX = {s[0]: i for i, s in enumerate(SECS)}


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def P(nm):
    nm_, c, a, T, B, W, p = SECS[IDX[nm]]
    return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


# ------------------------------------------------------------------------------------------------ the legs
SUPER = 3.0
TRANS = 0.45          # the transition ring: this far from the body region toward the first section
LEG = [((0.092, -0.125, 0.255), 0.064, 0.094, 0.064, 0.074),   # trouser top; r06 centre out; r09 broad; r23 fuller;
       ((0.09, -0.13, 0.19), 0.058, 0.076, 0.058, 0.068),      # r24 rear half depth 0.064 (rear wall under the R2b rim); r25 0.074          # r22: back to the r14 symmetric rings (the r16-r21 inner/rear/front
                                                     # half widths made a thin inner strip; the s2 relax rounds the rim)
       ((0.085, -0.122, 0.145), 0.047, 0.062),       # trouser tuft
       ((0.08, -0.124, 0.118), 0.030, 0.032),        # yellow tarsus
       ((0.078, -0.125, 0.08), 0.024, 0.027),
       ((0.078, -0.125, 0.052), 0.026, 0.030)]       # ankle: the foot piece takes over


def leg_pos(sec, u, s):
    """(u, s) on the region grid (u +1 = the leg's outer side, s +1 = rear) onto the section's rounded box."""
    c, rx, ry = sec[0], sec[1], sec[2]
    if u < 0 and len(sec) > 3:
        rx = sec[3]
    if s > 0 and len(sec) > 4:
        ry = sec[4]
    e = (abs(u) ** SUPER + abs(s) ** SUPER) ** (1.0 / SUPER) if (u or s) else 1.0
    m = max(abs(u), abs(s))
    f = m / e if e > 0 else 0.0
    return Vector((c[0] + u * f * rx, c[1] + s * f * ry, c[2]))


# ------------------------------------------------------------------------------------------------ the wings
# per span station: x, leading edge (y, z), chord, chord angle below horizontal (deg, back-down), thickness at
# the leading edge, at the trailing edge. Front view: the leading edge rises to the wrist and droops to the tip;
# top view: a straight leading edge, the chord shortening toward the fingered tip.
WSEC = [(0.150, (-0.170, 0.715), 0.34, 48, 0.075, 0.030),
        (0.210, (-0.185, 0.732), 0.37, 46, 0.060, 0.024),
        (0.280, (-0.195, 0.748), 0.39, 44, 0.052, 0.021),     # r03: the secondaries bulge (sheet top / front)
        (0.360, (-0.200, 0.762), 0.39, 42, 0.047, 0.019),
        (0.440, (-0.205, 0.773), 0.37, 40, 0.043, 0.018),
        (0.520, (-0.205, 0.779), 0.33, 38, 0.040, 0.017),     # wrist: the hand narrows to the fingers
        (0.600, (-0.200, 0.773), 0.29, 36, 0.035, 0.016),
        (0.670, (-0.195, 0.762), 0.25, 34, 0.031, 0.015),
        (0.740, (-0.190, 0.748), 0.22, 32, 0.027, 0.015),
        (0.800, (-0.185, 0.734), 0.20, 30, 0.024, 0.015),
        (0.850, (-0.180, 0.722), 0.19, 30, 0.022, 0.015)]
WS, WF = 10, 3         # the shoulder region: 10 spans along the body (chord) x 3 faces (thickness; r12: 2 -> 3, a lower underwing root)
COV_COL = 4            # the covert / flight-feather colour border runs along this chord column
TOOTH = 0.045          # trailing-edge feather tips: every other station's trailing edge this much further back
CAMBER = 0.018


def wdirs(a):
    a = math.radians(a)
    return Vector((0, math.cos(a), -math.sin(a))), Vector((0, math.sin(a), math.cos(a)))


def wing_pos(k, u, s):
    x, (ly, lz), c, a, thl, tht = WSEC[k]
    d, n = wdirs(a)
    t = (s + 1) / 2
    col = round(t * WS)
    if col == COV_COL:
        t += 0.035 if k % 2 else -0.035                     # covert tips: the border zig-zags station to station
    if abs(u) > 0.5 and col == 0:
        t = 0.045                                            # rounded leading edge
    if abs(u) > 0.5 and col == WS:
        t = 0.94                                             # blunt trailing edge (r14: 0.975 -> 0.94, no needle end faces)
    if col >= WS - 1 and k % 2 == 1 and 1 <= k <= len(WSEC) - 2:
        t += TOOTH / c * (1.0 if col == WS else 0.5)         # feather tips: the trailing edge steps back (r13: the
                                                             # last two columns share the step, no needle faces)
    th = thl + (tht - thl) * min(1.0, t) ** 0.8
    p = Vector((x, ly, lz)) + d * (c * t) + n * (CAMBER * math.sin(math.pi * min(1.0, t)) + u * th / 2)
    return p


# ------------------------------------------------------------------------------------------------ stage 1
def region(rings, spans, i0, S, j0, F):
    """The body region of S spans (rings i0..i0+S) x F faces (points j0..j0+F) and its (u, s) roles."""
    faces = [spans[i0 + a][j0 + b] for a in range(S) for b in range(F)]
    roles = {}
    for a in range(S + 1):
        for b in range(F + 1):
            roles[rings[i0 + a][j0 + b]] = (1 - 2 * b / F, 1 - 2 * a / S)
    return faces, roles


def grow(bm, faces, roles, n, pos, trans=TRANS, puff=0.0, fillet=None):
    """Transition ring(s) from the body region to section 0, then sections 0..n-1.
    Default: one ring TRANS of the way to section 0, first pushed PUFF out along the region's mean normal.
    fillet = [(puff, flare, trans), ...]: one ring each, the region vertex pushed puff along the normal and flare
    along the surface away from the region centre, then lerped trans toward section 0 (s1 r19: a fillet that
    turns from the body into the limb over two rings, no single fold past ~60 deg)."""
    nrm = sum((f.normal for f in faces), Vector()).normalized()
    reg = {v: v.co.copy() for f in faces for v in f.verts}
    cen = sum(reg.values(), Vector()) / len(reg)
    ring_steps = fillet or [(puff, 0.0, trans)]
    steps = [('t', q) for q in ring_steps] + [('s', k) for k in range(n)]
    origin = {}
    for kind, q in steps:
        keyed = [(o.co.copy(), rl, origin.get(o, o.co.copy())) for o, rl in roles.items()]
        r = extrude(bm, faces)
        new, org = {}, {}
        for v in r['verts']:
            hit = min(keyed, key=lambda w: (w[0] - v.co).length)
            new[v], org[v] = hit[1], hit[2]
        for v, (u, s) in new.items():
            if kind == 't':
                p, fl, t = q
                o = org[v]
                tang = (o - cen) - nrm * (o - cen).dot(nrm)
                tang = tang.normalized() if tang.length > 1e-9 else Vector()
                v.co = (o + nrm * p + tang * fl).lerp(pos(0, u, s), t)
            else:
                v.co = pos(q, u, s)
        faces, roles, origin = r['faces'], new, org
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    ends = [cap(bm, rings[0]), cap(bm, rings[-1])]
    bmesh.ops.poke(bm, faces=ends)
    recalc_normals(bm)
    # wings: the shoulder region M1..C3 (10 spans), ring points 2..4 (back-top corner): the back plane runs on
    # into the upper wing, the flank into the underwing
    f, r = region(rings, spans, IDX['M1'], WS, 2, WF)
    grow(bm, f, r, len(WSEC), wing_pos)
    # legs: the lower belly R2b..M1b (4 spans), ring points 7..10
    f, r = region(rings, spans, IDX['R2b'], 4, 8, 2)     # s1 r06: R2b..M1b; r10: points 8..10 (lower root, 2-face belly strip)
    grow(bm, f, r, len(LEG), lambda k_, u, s: leg_pos(LEG[k_], u, s), trans=0.5, puff=0.02)   # s1 r09-10 (r19 fillet: worse); r26 trans 0.35 -> 0.5
    snap_seam(bm)
    return object_from_bm('body', bm)


import parts as PT

EYE = Vector((0.05, -0.33, 0.805))
THIGH_ROOT = Vector((0.08, -0.13, 0.30))       # s2 r02: the thigh root rim + transition ring, relaxed (r04: centre 1.5 cm fwd)
RELAX_IT, RELAX_K = 4, 0.35         # s2 r03: 4 -> 2; r05: 3 x 0.35; r08 1 x 0.5 and r09 2 x 0.35 worse; r10: 4 x 0.35 on r26


def relax(bm, c, rad, it, k):
    """Laplacian relax of the vertices within rad of c (seam vertices keep x = 0): rounds the rim fold where the
    thigh wall leaves the belly into a blend (vertex moves only)."""
    vs = [v for v in bm.verts if (v.co - c).length < rad]
    seam = {v for v in vs if abs(v.co.x) < 1e-5}
    for _ in range(it):
        tgt = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in vs}
        for v in vs:
            v.co = v.co.lerp(tgt[v], k)
            if v in seam:
                v.co.x = 0.0


def stage2(k, body):
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    relax(bm, THIGH_ROOT, 0.10, RELAX_IT, RELAX_K)    # s2 r04: radius 0.085 -> 0.10
    f = face_near(bm, EYE, n=Vector((1, 0, 0)))
    fn = f.normal.copy()
    with topo(bm, k.log, 'inset', 'eye socket: one inset in the side face under the brow'):
        inner = inset(bm, [f], 0.2, 0.0)
    move(list(inner[0].verts), -fn * 0.005)
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'body': '#7a573c', 'gold': '#d69c55', 'cov': '#a07a55', 'flight': '#503b2c', 'yellow': '#e6b640',   # s3 r02: mid values
       'horn': '#3e3a36', 'eye': '#a0661f'}


def station_of(c):
    """Fractional loft station of a point (between the planar cut lines)."""
    best = None
    for i in range(len(SECS) - 1):
        _, ca, aa, *_r = SECS[i]
        _, cb, ab, *_r2 = SECS[i + 1]
        def d(cc, a):
            n = Vector((0, math.cos(math.radians(a)), -math.sin(math.radians(a))))
            return (Vector((0, c[1], c[2])) - Vector((0, cc[0], cc[1]))).dot(n)
        na = Vector((0, math.cos(math.radians(aa)), -math.sin(math.radians(aa))))
        sgn = 1 if (Vector((0, cb[0] - ca[0], cb[1] - ca[1]))).dot(na) > 0 else -1
        da, db = d(ca, aa) * sgn, d(cb, ab) * sgn
        if da >= 0 and db <= 0:
            t = da / max(da - db, 1e-9)
            cc = Vector((0, ca[0] + (cb[0] - ca[0]) * t, ca[1] + (cb[1] - ca[1]) * t))
            dist = (Vector((0, c[1], c[2])) - cc).length
            if best is None or dist < best[0]:           # s3 r03: the nearest bracketing span, not the first
                best = (dist, i + t)                     # (tail cut planes extended through the back)
    return best[1] if best else None


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if x > 0.138 and z > 0.4:                       # wing (s3 r04: 0.125 -> 0.138, the flank's widest faces stay body)
        up = n.y * 0.7 + n.z * 0.7 > 0
        xs = [w[0] for w in WSEC]
        kk = min(range(len(WSEC)), key=lambda q: abs(xs[q] - x))
        _, (ly, lz), ch, a, *_r = WSEC[kk]
        d, _n = wdirs(a)
        t = (Vector((0, y - ly, z - lz))).dot(d) / ch
        if t < COV_COL / WS:
            return 'cov' if up else 'body'
        return 'flight'
    if z < 0.125 and x > 0.03 and -0.2 < y < -0.05:
        return 'yellow'                                 # tarsus
    s = station_of(c)
    if s is None:
        return 'body'
    if s < IDX['R0'] - 0.5:
        return 'flight'                                 # tail fan
    if s >= IDX['B2']:
        return 'horn'                                   # hooked beak tip
    if s >= IDX['H4']:
        return 'yellow'                                 # cere and beak base
    if s >= IDX['N0']:
        nm_, cc, a, T, B, W, p = SECS[int(s)]
        h = (Vector((0, y - cc[0], z - cc[1]))).dot(Vector((0, math.sin(math.radians(a)), math.cos(math.radians(a)))))
        return 'gold' if h > -0.25 * T else 'body'      # golden crown, nape and cheek over a brown throat
    return 'body'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 5 for k_ in range(10)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(10):
        a, b = j, (j + 1) % 10
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def feather(bm, root, d, side, L, w, th, tipw=0.35):
    """A closed feather slab: root (buried), along d, width along side, thickness along side x d; a rounded,
    narrowed tip."""
    d = Vector(d).normalized(); side = Vector(side).normalized()
    nrm = d.cross(side).normalized()
    rows = []
    for t, ww, tt in ((0.0, w, th), (0.6, w * 1.0, th * 0.9), (0.88, w * 0.8, th * 0.75), (1.0, w * tipw, th * 0.6)):
        c = root + d * (L * t)
        rows.append([bm.verts.new(c + side * su * ww / 2 + nrm * sv * tt / 2)
                     for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(rows[-1])


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('body', 'gold', 'cov', 'flight', 'yellow', 'horn')}, body_rule)
    bm0 = edit(body); tree = BVHTree.FromBMesh(bm0); bm0.free()
    pieces = []
    # eye: a round amber-brown lens with a dark pupil, part in the socket, part proud
    c, n, _i, _d = tree.find_nearest(EYE)
    n = n if n.x > 0 else -n
    look = (n + Vector((0.0, -0.25, 0.0))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.002, look, 0.012, 0.007)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'horn': PAL['horn']},
          lambda c_, n_, i: 'horn' if ((c_ - c) - look * (c_ - c).dot(look)).length < 0.0055 and n_.dot(look) > 0.5 else 'eye')
    pieces.append(eye)
    # the primaries: six fingers fanning out of the wing tip
    x, (ly, lz), ch, a, thl, tht = WSEC[-1]
    d_, n_ = wdirs(a)
    bm = bmesh.new()
    for q in range(6):
        t = 0.08 + q * 0.165
        root = Vector((x - 0.05, ly, lz)) + d_ * (ch * t) + n_ * (CAMBER * math.sin(math.pi * t))
        spread = math.radians(-8 + q * 7.5)
        dirv = Vector((math.cos(spread), math.sin(spread) * math.cos(math.radians(a)),
                       -math.sin(spread) * math.sin(math.radians(a)) - 0.08)).normalized()
        L = 0.17 - abs(q - 2.2) * 0.018
        feather(bm, root, dirv, d_, L, 0.042, 0.014)
    prim = object_from_bm('primaries', bm)
    paint(prim, {'flight': PAL['flight']}, lambda c_, n_, i: 'flight')
    pieces.append(prim)
    # the tail feather tips: five rounded feather ends past the fan's end
    _, tc, ta, tT, tB, tW, tp = SECS[0]
    td = Vector((0, TD[0], TD[1])).normalized()
    bm = bmesh.new()
    for q in range(3):
        xq = 0.03 + q * 0.065
        root = Vector((xq, tc[0], tc[1])) - td * 0.03
        dirv = (td + Vector((0.12 * q, 0, 0))).normalized()
        feather(bm, root, dirv, Vector((1, 0, 0)), 0.075 - q * 0.008, 0.07, 0.018, tipw=0.5)
    tf = object_from_bm('tailfeathers', bm)
    paint(tf, {'flight': PAL['flight']}, lambda c_, n_, i: 'flight')
    pieces.append(tf)
    # raptor feet on the tarsus ends
    for sd in (1, -1):
        (cx, cy, cz), rx, ry = LEG[-1]
        ft = PT.bird_foot((cx * sd, cy, cz), toe_length=0.10, forward=(0, -1, 0), up=(0, 0, 1), side=sd, height=cz,
                          radius=0.026, spread=30.0, hallux=0.7, talon_len=0.5, name='foot' + ('L' if sd > 0 else 'R'),
                          mats={'scale': 'yellow', 'claw': 'horn'})
        pieces.append(ft)
    return pieces


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['beak'], 'neck', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('wing.L', J['wing'], J['elbow'], 'chest'),
         ('wing1.L', J['elbow'], J['wrist'], 'wing.L', True),
         ('wing2.L', J['wrist'], J['wtip'], 'wing1.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_foot'):
            bind(p, rig, bone='foot.' + p.name[-1])
        elif 'primaries' in p.name or 'tailfeathers' in p.name:
            bind(p, rig, body=body)
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'head': (0, 0, 14), 'wing1.L': (0, 0, 3), 'wing1.R': (0, 0, -3)},
                       24: {'head': (0, 0, 14)}, 30: {},
                       36: {'chest': (1.5, 0, 0), 'head': (0, 0, -14)}, 48: {}})
    clip(rig, 'move', {1: {},
                       6: {'wing.L': (0, 0, 18), 'wing.R': (0, 0, -18), 'wing1.L': (0, 0, 8), 'wing1.R': (0, 0, -8),
                           'thigh.L': (15, 0, 0), 'thigh.R': (15, 0, 0), 'shin.L': (-18, 0, 0), 'shin.R': (-18, 0, 0)},
                       12: {'wing.L': (0, 0, -16), 'wing.R': (0, 0, 16), 'wing2.L': (0, 0, -8), 'wing2.R': (0, 0, 8)},
                       18: {'wing.L': (0, 0, 10), 'wing.R': (0, 0, -10)},
                       24: {}},
         loc={1: {'hips': (0, 0, 0)}, 6: {'hips': (0, 0, -0.01)}, 12: {'hips': (0, -0.03, 0.04)}, 24: {'hips': (0, 0, 0)}})
    clip(rig, 'attack', {1: {},
                         10: {'wing.L': (0, 0, 20), 'wing.R': (0, 0, -20), 'neck': (-10, 0, 0), 'head': (-6, 0, 0)},
                         18: {'neck': (14, 0, 0), 'head': (10, 0, 0), 'spine': (6, 0, 0), 'thigh.L': (-20, 0, 0),
                              'shin.L': (25, 0, 0), 'wing.L': (0, 0, -8), 'wing.R': (0, 0, 8)},
                         24: {'neck': (6, 0, 0), 'head': (4, 0, 0)},
                         32: {}},
         loc={1: {'hips': (0, 0, 0)}, 10: {'hips': (0, 0.02, 0)}, 18: {'hips': (0, -0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
