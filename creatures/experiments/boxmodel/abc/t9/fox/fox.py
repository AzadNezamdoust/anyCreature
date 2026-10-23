import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
from smooth_borders import smooth_borders

# t9 RECREATE of zoo/fox (2026-10-23), t7 hand box model, zoo workflow v2 + proven tricks from day one:
# one spine loft of 14-vertex half rings (tail tip -> nose, the brush on the same loft), legs grown from BROAD 4 x 3
# lower-flank windows through a 45 % transition ring (rhino/hippo leg-root trick), ears grown from 1 x 2 skull-side
# windows by a ring morph of the root shape (root vertex angles kept), colour borders on placed loops +
# kit/smooth_borders, chunky claws, a small lens eye. Template code: zoo/hippo/hippo.py (grow, role_pos).
META = dict(creature='fox', model='opus', stage1_tris=(1200, 3600), total_tris=(1500, 4800), detail_tier=2,
            closeups=[('head', (0.0, -0.62, 0.86), 0.30, 'hero'),
                      ('front foot', (0.11, -0.34, 0.10), 0.16, 'hero'),
                      ('hind foot', (0.11, 0.37, 0.12), 0.16, 'hero'),
                      ('tail', (0.0, 0.62, 0.35), 0.30, 'az090')])

# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png
J = dict(
    hips=(0.0, 0.28, 0.62), spine=(0.0, 0.0, 0.62), chest=(0.0, -0.30, 0.66),
    neck=(0.0, -0.42, 0.78), head=(0.0, -0.54, 0.87), nose=(0.0, -0.84, 0.74),
    tail0=(0.0, 0.44, 0.60), tail1=(0.0, 0.53, 0.47), tail2=(0.0, 0.66, 0.30), tail3=(0.0, 0.82, 0.20),
    shoulder=(0.11, -0.30, 0.58), elbow=(0.11, -0.31, 0.34), wrist=(0.106, -0.335, 0.10),
    fpaw=(0.106, -0.35, 0.03), ftoe=(0.106, -0.42, 0.02),
    hipL=(0.11, 0.28, 0.56), knee=(0.11, 0.25, 0.34), hock=(0.106, 0.37, 0.18),
    hpaw=(0.106, 0.37, 0.03), htoe=(0.106, 0.30, 0.02),
    ear=(0.10, -0.51, 0.99), eartip=(0.125, -0.50, 1.10),
)

NV = 14


def prof(nt, nb, taper=1.0, nv=NV):
    """A superellipse half ring, top seam -> bottom seam: the top half exponent nt, the bottom nb, the bottom
    narrowing to `taper` of W at the bottom seam."""
    out = []
    for j in range(nv):
        t = math.pi * j / (nv - 1)
        c, s = math.cos(t), math.sin(t)
        n = nt if c >= 0 else nb
        fx = abs(s) ** (2 / n) if j not in (0, nv - 1) else 0.0
        fh = math.copysign(abs(c) ** (2 / n), c)
        if c < 0:
            fx *= 1 - (1 - taper) * abs(c)
        out.append((round(fx, 4), round(fh, 4)))
    return out


# the torso, hand placed: j0-j2 the back plane, j2-j5 the shoulder/hip bevel, j5-j8 the flank, j9-j12 the lower flank
# the legs grow from (window j9..j12, 3 faces), j12-j13 the belly strip; a keel: the bottom narrows
BODY = [(0, 1), (0.30, 0.975), (0.55, 0.89), (0.76, 0.74), (0.90, 0.55), (0.98, 0.32), (1.0, 0.08),
        (0.98, -0.17), (0.92, -0.40), (0.82, -0.60), (0.66, -0.77), (0.45, -0.90), (0.20, -0.98), (0, -1)]
NECK = prof(2.4, 2.4, 0.85)
HEAD = prof(2.6, 2.4, 0.80)
MUZ = prof(3.0, 2.6, 0.85)
TAIL = prof(2.2, 2.2, 0.95)
LJ = 9                           # leg windows: ring vertices j9 (outer) .. j12 (inner), 3 faces round, 4 spans long
EJ = 1                           # ear windows: j1 .. j5, skull top onto the side (4 faces: s1 r4 broad sheet ear), 1 span long


def tb(nm, top, bot, W, pr):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, pr)


def tc(nm, c, a, h, W, pr):
    """A section from its centre (y, z), its tilt a (deg; 0 = upright, + tips the top toward +y) and half height."""
    return (nm, c, a, h, h, W, pr)


SECS = [
    # the brush, tip -> root: a fat round tail hanging down-back, the tip turning level (sheet side)
    tc('T0', (0.832, 0.200), 80, 0.030, 0.030, TAIL),
    tc('T1', (0.805, 0.205), 72, 0.070, 0.065, TAIL),
    tc('T2', (0.760, 0.222), 63, 0.105, 0.100, TAIL),
    tc('T3', (0.700, 0.262), 54, 0.130, 0.122, TAIL),
    tc('T4', (0.630, 0.325), 46, 0.140, 0.130, TAIL),
    tc('T5', (0.565, 0.398), 42, 0.128, 0.120, TAIL),
    tc('T6', (0.515, 0.468), 37, 0.108, 0.104, TAIL),
    tc('T7', (0.470, 0.548), 28, 0.090, 0.098, TAIL),     # the tail root ring, as wide as the brush's first station
    # rump + hind-leg window rings (R0..B3, rear -> front)
    tb('R0', (0.39, 0.712), (0.39, 0.450), 0.145, BODY),
    tb('B0', (0.33, 0.735), (0.33, 0.440), 0.158, BODY),
    tb('B1', (0.27, 0.750), (0.27, 0.430), 0.163, BODY),
    tb('B2', (0.21, 0.758), (0.21, 0.425), 0.165, BODY),
    tb('B3', (0.15, 0.762), (0.15, 0.425), 0.165, BODY),
    # the barrel: belly tucked, straight back
    tb('M0', (0.08, 0.762), (0.08, 0.425), 0.165, BODY),
    tb('M1', (0.01, 0.762), (0.01, 0.415), 0.167, BODY),
    tb('M2', (-0.06, 0.764), (-0.06, 0.402), 0.170, BODY),
    tb('M3', (-0.12, 0.772), (-0.12, 0.392), 0.174, BODY),
    # fore-leg window rings (F0..F4, rear -> front): the chest deepens, the shoulder rises
    tb('F0', (-0.18, 0.790), (-0.18, 0.386), 0.180, BODY),
    tb('F1', (-0.24, 0.820), (-0.24, 0.382), 0.188, BODY),
    tb('F2', (-0.30, 0.855), (-0.30, 0.384), 0.194, BODY),
    tb('F3', (-0.335, 0.895), (-0.36, 0.392), 0.194, BODY),
    tb('F4', (-0.37, 0.935), (-0.42, 0.410), 0.188, BODY),
    # brisket + thick neck (tilted rings: the top turns less than the throat)
    tb('C0', (-0.40, 0.965), (-0.475, 0.455), 0.178, BODY),
    tb('C1', (-0.43, 0.988), (-0.52, 0.525), 0.170, NECK),
    tb('N0', (-0.46, 1.000), (-0.555, 0.600), 0.166, NECK),
    # head: back of skull + cheek ruff (ear window H0 -> H1), eye on H2/H3, the stop H3 -> H4, the tapered muzzle
    tb('H0', (-0.478, 1.005), (-0.585, 0.665), 0.170, HEAD),
    tb('H1', (-0.555, 0.995), (-0.615, 0.690), 0.175, HEAD),
    tb('H2', (-0.605, 0.960), (-0.640, 0.702), 0.160, HEAD),
    tb('H3', (-0.650, 0.925), (-0.668, 0.706), 0.128, HEAD),
    tb('H4', (-0.700, 0.866), (-0.705, 0.704), 0.100, MUZ),
    tb('H5', (-0.750, 0.812), (-0.750, 0.700), 0.080, MUZ),
    tb('H6', (-0.800, 0.782), (-0.798, 0.708), 0.058, MUZ),
    tb('H7', (-0.838, 0.766), (-0.834, 0.716), 0.036, MUZ),
]

# leg sections: (cx, cy, z, rx, ry, exponent): level rounded boxes, deeper front-to-back; secs[0] is the target the
# transition ring slopes toward. Chunky legs (sheet front: socks 0.09-0.10 wide), broad paws.
FORE = [(0.115, -0.300, 0.400, 0.072, 0.098, 2.6),   # upper arm under the chest
        (0.112, -0.305, 0.335, 0.058, 0.072, 2.6),   # elbow
        (0.110, -0.315, 0.270, 0.050, 0.058, 2.6),   # forearm: the sock border loop
        (0.108, -0.325, 0.190, 0.045, 0.050, 2.6),
        (0.106, -0.335, 0.115, 0.042, 0.046, 2.6),   # wrist
        (0.106, -0.352, 0.055, 0.050, 0.062, 2.4),   # paw
        (0.106, -0.362, 0.0, 0.054, 0.070, 2.4)]
HIND = [(0.120, 0.285, 0.400, 0.080, 0.112, 2.6),    # thigh under the haunch
        (0.115, 0.255, 0.330, 0.062, 0.085, 2.6),    # stifle (forward)
        (0.110, 0.305, 0.270, 0.052, 0.066, 2.6),    # gaskin: the sock border loop
        (0.107, 0.360, 0.195, 0.044, 0.052, 2.6),    # hock (back)
        (0.106, 0.372, 0.125, 0.041, 0.047, 2.6),    # metatarsus
        (0.106, 0.368, 0.055, 0.050, 0.062, 2.4),    # paw
        (0.106, 0.362, 0.0, 0.054, 0.070, 2.4)]
# ears: (centre, scale across, scale front-back, keep of the root's z slope): a ring morph of the root window's
# own shape, rising off the skull's upper side, flattening front-back to a blunt point
EAR = [((0.129, -0.510, 1.052), 0.88, 0.58, 0.45),     # s4 r2: the first ring is now the 45 % transition toward
       ((0.133, -0.505, 1.080), 0.58, 0.38, 0.28),     # this station (r1: a fixed ring 3 cm over the root left a
       ((0.136, -0.502, 1.104), 0.16, 0.13, 0.10)]     # 12.5 mm seam strip on the ear's back root, 1.91 r)
T1_EAR = 0.45
T1_LEG = 0.45


def sec_pts(c, a, T, B, W, pr):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in pr:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def akey(t):
    return round(t if t < math.pi - 1e-6 else -math.pi, 4)


def role_pos(sec, u, s, amap=None):
    """u across (+1 = +x side), s front/back (+1 = rear). Boundary roles sit on the section's superellipse at the
    angle of (u, s) (amap: grid angle -> evenly spaced angle); interior roles (the sole grid) inside it."""
    cx, cy, z, rx, ry, n = sec[:6]
    if abs(u) > 0.999 or abs(s) > 0.999:
        th = math.atan2(s, u)
        if amap:
            th = amap[akey(th)]
        c, sn = math.cos(th), math.sin(th)
        return Vector((cx + rx * math.copysign(abs(c) ** (2 / n), c), cy + ry * math.copysign(abs(sn) ** (2 / n), sn), z))
    return Vector((cx + u * rx * 0.85, cy + s * ry * 0.85, z))


def grow(bm, rings, spans, i0, j0, A, B, secs, t1):
    """Extrude the A x B face window (rings i0..i0+A, ring vertices j0..j0+B) section by section. The first new
    ring slopes from the window rim t1 of the way to secs[0] (the broad transition), then one ring per section."""
    faces = [spans[i0 + a][j0 + b] for a in range(A) for b in range(B)]
    G = [[rings[i0 + a][j0 + b] for b in range(B + 1)] for a in range(A + 1)]
    su = 1 if G[A // 2][0].co.x > G[A // 2][B].co.x else -1
    ss = 1 if G[0][B // 2].co.y > G[A][B // 2].co.y else -1
    roles = [(G[a][b].co.copy(), (su * (1 - 2 * b / B), ss * (1 - 2 * a / A))) for a in range(A + 1) for b in range(B + 1)]
    th = sorted({akey(math.atan2(s_, u_)) for _p, (u_, s_) in roles if abs(u_) > 0.999 or abs(s_) > 0.999})
    N = len(th)
    off = 0.0 if any(abs(t) < 1e-6 for t in th) else math.pi / N
    base = min(range(N), key=lambda i: abs(th[i] - (-math.pi + off)))
    amap = {th[(base + i) % N]: -math.pi + off + 2 * math.pi * i / N for i in range(N)}
    rp = lambda sec, u_, s_: role_pos(sec, u_, s_, amap)

    def step(faces, roles, place):
        r = extrude(bm, faces)
        new = []
        for v in r['verts']:
            o = min(roles, key=lambda o_: (o_[0] - v.co).length)
            new.append((v, o))
        for v, (p0, ro) in new:
            v.co = place(p0, ro)
        return r['faces'], [(v.co.copy(), ro) for v, (p0, ro) in new]

    def first(p0, ro):
        q = role_pos(secs[0], *ro)          # the transition ring keeps the window's own angles (no skew)
        return p0.lerp(q, t1)
    faces, roles = step(faces, roles, first)
    for sec in secs:
        faces, roles = step(faces, roles, lambda p0, ro, sec=sec: rp(sec, *ro))
    return faces


def grow_ear(bm, rings, spans, i0, j0, stations, nb=3):
    """Ear: extrude the 1 x nb skull window; every ring is the root window's own outline (its vertex angles kept),
    re-centred, scaled across / front-back and with its z slope eased toward level."""
    faces = [spans[i0][j0 + b] for b in range(nb)]
    root = [rings[i0 + a][j0 + b] for a in range(2) for b in range(nb + 1)]
    c0 = sum((v.co for v in root), Vector()) / len(root)
    roles = [(v.co.copy(), v.co - c0) for v in root]
    pos = lambda st, off: Vector(st[0]) + Vector((off.x * st[1], off.y * st[2], off.z * st[3]))
    r = extrude(bm, faces)                       # the broad transition ring: T1_EAR of the way to station 0
    new = []
    for v in r['verts']:
        p0, off = min(roles, key=lambda o_: (o_[0] - v.co).length)
        v.co = p0.lerp(pos(stations[0], off), T1_EAR)
        new.append((v.co.copy(), off))
    faces, roles = r['faces'], new
    for c, sx, sy, kz in stations:
        r = extrude(bm, faces)
        new = []
        for v in r['verts']:
            p0, off = min(roles, key=lambda o_: (o_[0] - v.co).length)
            v.co = Vector(c) + Vector((off.x * sx, off.y * sy, off.z * kz))
            new.append((v.co.copy(), off))
        faces, roles = r['faces'], new
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    grow(bm, rings, spans, idx['R0'], LJ, 4, 3, HIND, T1_LEG)
    grow(bm, rings, spans, idx['F0'], LJ, 4, 3, FORE, T1_LEG)
    grow_ear(bm, rings, spans, idx['H0'], EJ, EAR, nb=4)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.0, -0.640, 0.845))     # the eye point on the side view (y, z); x from a ray on the head side
SOCKET = []
VAR = os.environ.get('FOX_VAR', 'v2')     # fix-loop variant switch; 'v2' = champion (fix1 won both orders)


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    hit, hn = tree.ray_cast(Vector((1.0, EYE.y, EYE.z)), Vector((-1, 0, 0)), 2.0)[:2]
    f = face_near(bm, hit, n=hn)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face under the brow'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.006)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    # deliberate muzzle planes (BRIEF 2.2): one flat bridge (j0-j3) and one flat side (j4-j9) per side, H4 -> H7
    MZ = [P(nm) for nm in ('H4', 'H5', 'H6', 'H7')]
    flatten([vert_near(bm, R_[j]) for R_ in MZ for j in (1, 2, 3)])
    flatten([vert_near(bm, R_[j]) for R_ in MZ for j in (5, 6, 7, 8)])
    # nose pad: the cap's top edge forward, the chin edge back (a forward-down slanted pad)
    H7 = MZ[-1]
    move([vert_near(bm, H7[j]) for j in (0, 1, 2, 3)], (0.0, -0.012, 0.0))
    move([vert_near(bm, H7[j]) for j in (11, 12, 13)], (0.0, 0.010, 0.0))
    if VAR in ('v1', 'v2', 'v3', 'v4'):
        # fix1: a wider brush from the rear (sheet rear: the brush covers 2/3 of the hips); ramp in from the root
        TC = [Vector((0.0, *c)) for (nm, c, *_r) in SECS if nm.startswith('T')]
        for v in bm.verts:
            if v.co.y > 0.47 and v.co.z > 0.1:
                f = min(1.0, (v.co.y - 0.47) / 0.08)
                if VAR == 'v1':
                    v.co.x *= 1 + 0.16 * f
                else:
                    c = min(TC, key=lambda q: (Vector((0.0, v.co.y, v.co.z)) - q).length)
                    d = Vector((0.0, v.co.y, v.co.z)) - c
                    v.co.x *= 1 + 0.12 * f
                    v.co.y, v.co.z = c.y + d.y * (1 + 0.08 * f), c.z + d.z * (1 + 0.08 * f)
    if VAR in ('v3', 'v4'):
        # fix2: the ear reads as a solid cone from the side (r2: a flat spike); scale the ear rings above the root
        # front-back about the ear axis (v3 x1.4; v4 x1.25 deep and x1.1 across), ramped in over the first 4 cm
        ax = Vector(EAR[0][0])
        for v in bm.verts:
            if v.co.z > 0.995 and -0.58 < v.co.y < -0.43 and v.co.x > 0.05:
                f = min(1.0, (v.co.z - 0.995) / 0.04)
                sy, sx = (1.4, 1.0) if VAR == 'v3' else (1.25, 1.1)
                v.co.y = ax.y + (v.co.y - ax.y) * (1 + (sy - 1) * f)
                v.co.x = ax.x + (v.co.x - ax.x) * (1 + (sx - 1) * f)
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.03 and abs(c.z - ec0.z) < 0.03)
    commit(body, bm)


PAL = {'fur': '#d0601e', 'cream': '#efe4cf', 'sock': '#3a2a24', 'amber': '#e0a030', 'nose': '#1a1414',
       'claw': '#5a4a42'}

_ST = sorted([(c[0], c[1], T) for (nm, c, a, T, B_, W, p) in SECS if not nm.startswith('T')])
_SY = [q[0] for q in _ST]


def _frame(y):
    if y <= _SY[0]:
        return _ST[0][1], _ST[0][2]
    if y >= _SY[-1]:
        return _ST[-1][1], _ST[-1][2]
    i = max(i_ for i_ in range(len(_SY)) if _SY[i_] <= y)
    t = (y - _SY[i]) / (_SY[i + 1] - _SY[i])
    return (_ST[i][1] + (_ST[i + 1][1] - _ST[i][1]) * t, _ST[i][2] + (_ST[i + 1][2] - _ST[i][2]) * t)


def _leg(c):
    x, y, z = abs(c.x), c.y, c.z
    for y0, y1 in ((-0.46, -0.16), (0.13, 0.42)):
        if y0 < y < y1 and x > 0.035 and z < (0.47 if x > 0.06 else 0.40):     # s3 r3: + the transition ring
            return True
    return False


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.815 and z > 0.728:
        return 'nose'                                   # nose pad on the muzzle tip
    if z > 1.0 and -0.56 < y < -0.46 and x > 0.04:
        return 'cream' if n.y < -0.45 else 'sock'       # ears: cream inner (front) face, dark back
    if _leg(c):
        return 'sock' if z < 0.272 else 'fur'           # dark stockings below the forearm / gaskin loop
    if y > (0.655 if VAR in ('v1', 'v2', 'v3', 'v4') else 0.70):
        return 'cream'                                  # white brush tip (fix1: the last third, sheet side)
    if y > 0.40:
        return 'fur'
    zc, h = _frame(y)
    fh = (z - zc) / h
    if y < -0.47:
        return 'cream' if fh < -0.05 else 'fur'         # s3 r2: cheeks + muzzle sides below the eye line, jaw
    if y < -0.16:                                       # s3 r2: the bib faces forward (sheet front), the side stays fur
        return 'cream' if (n.y < -0.35 and x < 0.13 and fh < 0.25) or fh < -0.86 else 'fur'
    return 'cream' if fh < -0.88 else 'fur'             # s3 r2: belly underside only (j11-j13), not the lower flank


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h, sides=8):
    """A low-poly eye lens: back cone, iris ring, pupil cap."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * 2 * math.pi / sides for k_ in range(sides)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, Bv = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.4)
    for j in range(sides):
        a, b = j, (j + 1) % sides
        bm.faces.new([Bv, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def claw(bm, base, out, w, hgt, d):
    """A chunky claw: an arched 6-sided section swept out of the paw front, a root sunk 2 cm in, a blunt tip."""
    out = Vector(out).normalized()
    side = out.cross(Vector((0, 0, 1))).normalized()
    up = Vector((0, 0, 1))
    SEC = [(-1, 0), (1, 0), (0.85, 0.6), (0.4, 1.0), (-0.4, 1.0), (-0.85, 0.6)]
    rows = []
    for off, sw, sh, dz in ((-0.02, 1.0, 1.0, 0.0), (d * 0.6, 0.9, 0.85, -0.002), (d, 0.6, 0.5, -0.004)):
        c = base + out * off + up * (0.006 + dz)
        rows.append([bm.verts.new(c + side * su * w * sw / 2 + up * (sz * hgt * sh)) for su, sz in SEC])
    n = len(SEC)
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(n):
            bm.faces.new([a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]])
    bm.faces.new(rows[-1])


def stage3(k, body):
    paint(body, PAL, body_rule)
    smooth_borders(body, k=k, iters=8)      # owner 10-21: borders follow the form (kit/smooth_borders)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.35, 0.0))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.004, n, 0.017, 0.009)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'nose': PAL['nose']},
          lambda c_, n_, i: 'nose' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.008 and n_.dot(n) > 0.5 else 'amber')
    pieces.append(eye)
    bm = bmesh.new()
    for sec in (FORE[-2], HIND[-2]):
        cx, cy, z, rx, ry, nn = sec
        for ang in (-60, -80, -100, -120):
            th = math.radians(ang)
            d = Vector((math.cos(th), math.sin(th), 0.0))
            o = Vector((cx, cy, 0.025)) + d * 0.3
            hit = tree.ray_cast(o, -d, 0.6)[0]
            base = Vector((hit.x, hit.y, 0.0)) if hit is not None else Vector((cx, cy, 0.0)) + d * ry
            claw(bm, base - d * 0.003, d, 0.024, 0.02, 0.026)
    claws = object_from_bm('claws', bm)
    paint(claws, {'claw': PAL['claw']}, lambda c_, n_, i: 'claw')
    pieces.append(claws)
    return pieces + details(tree)


def details(tree):
    """Tier-2 readable details (detail gate: 6-16 groups): nose pad, cheek ruff tufts, the white brush tuft."""
    import detail_pieces as D
    out = []

    def piece(name, bm, key, mirror=True):
        ob = object_from_bm(name, bm, mirror=mirror)
        paint(ob, {key: PAL[key]}, lambda c_, n_, i: key)
        out.append(ob)
    # nose pad: a chunky dark knob on the muzzle tip
    h_ = D.cast_in(tree, (0.002, -1.2, 0.742), (0, 1, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.026, 0.014, sides=8, sq=(0.8, 1.15), top=0.55)
    piece('nose', bm, 'nose', mirror=False)
    # cheek ruff: two chunky cream tufts per side sweeping back-out-down off the cheek (sheet front: wide white cheeks)
    bm = bmesh.new()
    for (y, z, d) in ((-0.575, 0.770, (0.30, 0.90, -0.30)), (-0.540, 0.720, (0.25, 0.85, -0.50))):
        h_ = D.cast_in(tree, (1.0, y, z), (-1, 0, 0))     # s3 r3: flatter, laid back along the cheek (r2 read as muffs)
        D.fan(bm, h_[0] - h_[1] * 0.006, d, (0, 0, 1), 0.065, 0.06, 0.024, sink=0.03, spread=1.1, tip=0.4)
    piece('ruff', bm, 'cream')
    # brush tip: a fat cream tuft carrying the tail's point
    bm = bmesh.new()
    D.fan(bm, (0.0, 0.805, 0.205), (0, 1, -0.25), (1, 0, 0), 0.06, 0.085, 0.062, sink=0.035, spread=0.9, tip=0.4)
    piece('tuft', bm, 'cream', mirror=False)
    return out


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
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 4)},
                       20: {'ear.L': (0, 0, -12)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -4)}, 48: {}})
    A = 18
    TL = -16      # the trotting fox carries its brush lifted clear of the hind legs' swing
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, 3)},
        7: {'forearm.R': (-35, 0, 0), 'paw.R': (-30, 0, 0), 'shin.L': (-20, 0, 0), 'foot.L': (25, 0, 0), 'neck': (2, 0, 0), 'tail0': (TL, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, -3)},
        19: {'forearm.L': (-35, 0, 0), 'paw.L': (-30, 0, 0), 'shin.R': (-20, 0, 0), 'foot.R': (25, 0, 0), 'neck': (2, 0, 0), 'tail0': (TL, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, 3)}})
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
