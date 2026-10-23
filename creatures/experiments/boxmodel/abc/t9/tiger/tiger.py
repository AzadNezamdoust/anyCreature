import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
from smooth_borders import smooth_borders

# t9 RECREATE of zoo/tiger (2026-10-23), t7 hand box model, built from the t9 fox program (zoo workflow v2 + proven
# tricks): one spine loft of 16-vertex half rings (tail tip -> nose), the KEY stations hand placed off the sheet
# (reference/side.png + front.png measured), the torso and tail spans split into straight co-planar in-between rings
# (3x torso, 2x tail: the density the stripes need, the planes stay those of the key loft), heavy legs grown from BROAD
# 9 x 3 lower-flank windows through a 45 % transition ring, round ears from 1 x 3 skull windows (ring morph), stripes
# painted in the loft's own (ring, angle) frame: tapered, slanted, varied, following the ring tilt; smooth_borders.
# Identity cue (judge 10-23): a STOCKY tiger with a BIG round head + white cheek ruff, a deep chest, heavy forelegs and
# big paws, a thick tail with a black club tip, stripes that follow the body and taper (no barcode).
META = dict(creature='tiger', model='opus', stage1_tris=(3000, 7000), total_tris=(3500, 8000), detail_tier=2,
            closeups=[('head', (0.0, -0.74, 0.88), 0.32, 'hero'),
                      ('front foot', (0.13, -0.48, 0.10), 0.18, 'hero'),
                      ('hind foot', (0.13, 0.33, 0.12), 0.18, 'hero'),
                      ('tail', (0.0, 0.70, 0.30), 0.30, 'az090')])

# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png
J = dict(
    hips=(0.0, 0.30, 0.62), spine=(0.0, 0.0, 0.62), chest=(0.0, -0.36, 0.68),
    neck=(0.0, -0.52, 0.82), head=(0.0, -0.63, 0.88), nose=(0.0, -0.90, 0.77),
    tail0=(0.0, 0.47, 0.60), tail1=(0.0, 0.56, 0.40), tail2=(0.0, 0.69, 0.24), tail3=(0.0, 0.89, 0.177),
    shoulder=(0.133, -0.41, 0.60), elbow=(0.130, -0.435, 0.34), wrist=(0.123, -0.462, 0.105),
    fpaw=(0.125, -0.48, 0.03), ftoe=(0.125, -0.58, 0.02),
    hipL=(0.133, 0.25, 0.58), knee=(0.130, 0.24, 0.32), hock=(0.123, 0.345, 0.185),
    hpaw=(0.125, 0.33, 0.03), htoe=(0.125, 0.23, 0.02),
    ear=(0.118, -0.61, 1.04), eartip=(0.132, -0.608, 1.13),
)

NV = 16


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


# the torso, hand placed: j0-j2 the back plane, j2-j5 the shoulder/hip bevel, j5-j9 the flank, j10-j11 the lower
# flank turn, j11-j14 the leg windows (3 faces round), j14-j15 the belly strip; a keel: the bottom narrows
BODY = [(0, 1), (0.25, 0.985), (0.48, 0.94), (0.67, 0.84), (0.82, 0.70), (0.93, 0.52), (0.985, 0.31), (1.0, 0.09),
        (0.995, -0.12), (0.98, -0.30), (0.955, -0.46), (0.91, -0.61), (0.79, -0.76), (0.58, -0.875), (0.29, -0.96),
        (0, -1)]                    # s1 r5: a boxier lower flank (j9-j11 out) so the leg windows reach the outline
NECK = prof(2.4, 2.4, 0.85)
HEAD = prof(2.6, 2.4, 0.80)
MUZ = prof(3.4, 2.8, 0.90)          # s1 r3: a broad boxy cat muzzle (was 3.0/2.6/0.85)
TAIL = prof(2.2, 2.2, 0.95)
LJ = 11                          # leg windows: ring vertices j11 (outer) .. j14 (inner), 3 faces round
EJ = 1                           # ear windows: j1 .. j4 on the skull's upper side (3 faces), 1 span long


def tb(nm, top, bot, W, pr, sub=1):
    """A section from its top and bottom seam points (y, z) read off reference/side.png; `sub` = straight co-planar
    sub-spans toward the next station."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, pr, sub)


def tc(nm, c, a, h, W, pr, sub=1):
    """A section from its centre (y, z), its tilt a (deg; 0 = upright, + tips the top toward +y) and half height."""
    return (nm, c, a, h, h, W, pr, sub)


SECS = [
    # the tail, tip -> root: thick (0.15 m, sheet side), hanging down-back at 55-60 deg, the black club levelling out
    tc('T0', (0.903, 0.178), -12, 0.032, 0.032, TAIL),
    tc('T1', (0.888, 0.177), -8, 0.062, 0.060, TAIL, 2),
    tc('T2', (0.845, 0.176), 0, 0.074, 0.070, TAIL, 2),
    tc('T3', (0.790, 0.182), 12, 0.074, 0.070, TAIL, 2),
    tc('T4', (0.735, 0.205), 28, 0.073, 0.069, TAIL, 2),
    tc('T5', (0.680, 0.248), 40, 0.072, 0.068, TAIL, 2),
    tc('T6', (0.625, 0.310), 50, 0.072, 0.068, TAIL, 2),
    tc('T7', (0.567, 0.390), 55, 0.074, 0.070, TAIL, 2),
    tc('T8', (0.515, 0.470), 45, 0.080, 0.088, TAIL, 2),
    tb('T9', (0.482, 0.684), (0.438, 0.478), 0.140, TAIL, 2),    # s4 r4: W 0.10 -> 0.14, a broad root over the buttock    # the tail root ring: upright, blended over the rump
    # (s4 r2 T9 bottom 0.452 made the root knife worse 1.37 -> 1.85 r: reverted)
    # rump + hind-leg window rings (R0..B2, rear -> front): the haunch is the widest mass behind (s1 r6: sheet rear 0.24)
    tb('R0', (0.445, 0.728), (0.430, 0.452), 0.195, BODY, 3),
    tb('B0', (0.375, 0.772), (0.360, 0.425), 0.226, BODY, 3),
    tb('B1', (0.290, 0.812), (0.280, 0.405), 0.238, BODY, 3),
    tb('B2', (0.205, 0.828), (0.195, 0.395), 0.232, BODY, 3),
    tb('B3', (0.120, 0.833), (0.115, 0.390), 0.214, BODY, 3),
    # the barrel: a level back at 0.83, the belly at 0.36-0.39 (deep: 0.45 m)
    tb('M0', (0.035, 0.829), (0.035, 0.385), 0.198, BODY, 3),
    tb('M1', (-0.050, 0.825), (-0.050, 0.372), 0.198, BODY, 3),
    tb('M2', (-0.135, 0.830), (-0.135, 0.360), 0.203, BODY, 3),
    # fore-leg window rings (F1..F4): the chest deepens forward, the withers rise into the thick neck
    tb('F0', (-0.215, 0.850), (-0.220, 0.352), 0.213, BODY, 3),
    tb('F1', (-0.290, 0.890), (-0.300, 0.352), 0.228, BODY, 3),
    tb('F2', (-0.360, 0.935), (-0.385, 0.358), 0.236, BODY, 3),
    tb('F3', (-0.425, 0.978), (-0.470, 0.375), 0.237, BODY, 3),
    tb('F4', (-0.480, 1.012), (-0.550, 0.410), 0.232, BODY, 2),
    # brisket + short thick neck under the ruff (tilted rings: the throat runs forward under the head)
    tb('C0', (-0.525, 1.038), (-0.605, 0.470), 0.222, BODY),
    tb('N0', (-0.560, 1.056), (-0.645, 0.535), 0.215, NECK),
    # the big round head: back of skull + cheek ruff (ear window H0 -> H1), eye on H3, the stop H3 -> H4, the broad
    # short cat muzzle H4-H7
    tb('H0', (-0.590, 1.066), (-0.670, 0.595), 0.217, HEAD),
    tb('H1', (-0.638, 1.070), (-0.700, 0.635), 0.222, HEAD),
    tb('H2', (-0.687, 1.048), (-0.730, 0.655), 0.215, HEAD),
    tb('H3', (-0.736, 1.008), (-0.765, 0.665), 0.190, HEAD),
    tb('H4', (-0.782, 0.958), (-0.797, 0.665), 0.155, MUZ),
    tb('H5', (-0.828, 0.895), (-0.833, 0.665), 0.135, MUZ),
    tb('H6', (-0.868, 0.848), (-0.868, 0.678), 0.112, MUZ),
    tb('H7', (-0.900, 0.808), (-0.898, 0.708), 0.082, MUZ),
]

# leg sections: (cx, cy, z, rx, ry, exponent): level rounded boxes (flat sides, exponent 3), deeper front-to-back;
# secs[0] is the target the transition ring slopes toward. Heavy legs (sheet front: 0.13-0.15 wide), big paws.
FORE = [(0.133, -0.425, 0.360, 0.069, 0.112, 3.0),   # upper arm under the chest (s1 r2: below the window's inner rim)
        (0.130, -0.435, 0.290, 0.067, 0.096, 3.0),   # elbow
        (0.126, -0.445, 0.225, 0.063, 0.083, 3.0),   # forearm
        (0.124, -0.455, 0.160, 0.059, 0.075, 3.0),
        (0.123, -0.462, 0.105, 0.057, 0.070, 3.0),   # wrist
        (0.125, -0.480, 0.050, 0.078, 0.098, 2.6),   # paw
        (0.125, -0.490, 0.0, 0.080, 0.105, 2.6)]
HIND = [(0.133, 0.250, 0.385, 0.069, 0.112, 3.0),    # thigh under the haunch (s4 r3: window B0..B3, 6 cm forward)
        (0.130, 0.240, 0.320, 0.065, 0.105, 3.0),    # stifle (rear wall in line with the thigh's)
        (0.126, 0.285, 0.250, 0.059, 0.085, 3.0),    # gaskin
        (0.123, 0.345, 0.185, 0.053, 0.068, 3.0),    # hock (back)
        (0.122, 0.350, 0.115, 0.051, 0.063, 3.0),    # metatarsus
        (0.125, 0.330, 0.050, 0.076, 0.095, 2.6),    # paw
        (0.125, 0.320, 0.0, 0.078, 0.102, 2.6)]
# ears: (centre, scale across, scale front-back, keep of the root's z slope): a ring morph of the root window's own
# shape rising off the skull's upper side to a ROUND top (sheet: round cups, base x 0.06-0.17)
EAR = [((0.126, -0.612, 1.088), 1.00, 1.40, 0.45),    # s1 r4: deeper front-back (was 0.72/0.58/0.32: a thin spike
       ((0.133, -0.610, 1.116), 0.80, 1.25, 0.25),    # from the side; sheet side: a round cup ~0.10 deep);
       ((0.137, -0.608, 1.133), 0.40, 0.70, 0.10)]    # s1 r8: taller; r9: rounded top (0.80/0.40), tips lean out
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


def build_rings():
    """Key stations + their straight in-between rings (vertex lerps: every split face stays co-planar)."""
    pts = [sec_pts(c, a, T, B, W, p) for (nm, c, a, T, B, W, p, sub) in SECS]
    rings, idx = [], {}
    for i, (nm, *_r, sub) in enumerate(SECS):
        idx[nm] = len(rings)
        rings.append(pts[i])
        if i + 1 < len(SECS):
            for s in range(1, sub):
                t = s / sub
                rings.append([tuple(a_ + (b_ - a_) * t for a_, b_ in zip(pa, pb)) for pa, pb in zip(pts[i], pts[i + 1])])
    return rings, idx


RINGS, RIDX = build_rings()


def _frames():
    F = []
    for r in RINGS:
        top, bot = Vector(r[0][1:]), Vector(r[-1][1:])
        c = (top + bot) / 2
        up = (top - bot).normalized()
        F.append(dict(c=c, up=up, ax=Vector((up[1], -up[0])),
                      H=(top - bot).length / 2, W=max(p[0] for p in r), s=top.x))
    return F


FR = _frames()


def loft_param(p):
    """(u, s, v) of a point in the loft frame: u the continuous ring index, s the top-seam y at u (metres along the
    back), v the angle round the half ring (0 top seam, 0.5 the side, 1 bottom seam)."""
    q = Vector((p[1], p[2]))
    d = [(q - f['c']).dot(f['ax']) for f in FR]
    best = None
    for i in range(len(FR) - 1):
        if d[i] <= 0 <= d[i + 1] or d[i] >= 0 >= d[i + 1]:
            t = 0.0 if d[i + 1] == d[i] else -d[i] / (d[i + 1] - d[i])
            c = FR[i]['c'].lerp(FR[i + 1]['c'], t)
            e = (q - c).length
            if best is None or e < best[0]:
                best = (e, i, t, c)
    if best is None:
        i = 0 if abs(d[0]) < abs(d[-1]) else len(FR) - 2
        t = 0.0 if i == 0 else 1.0
        best = (0, i, t, FR[i]['c'].lerp(FR[i + 1]['c'], t))
    _e, i, t, c = best
    A, B_ = FR[i], FR[i + 1]
    up = A['up'].lerp(B_['up'], t).normalized()
    H = A['H'] + (B_['H'] - A['H']) * t
    W = A['W'] + (B_['W'] - A['W']) * t
    s = A['s'] + (B_['s'] - A['s']) * t
    h = (q - c).dot(up)
    v = math.atan2(abs(p[0]) / max(W, 1e-6), h / max(H, 1e-6)) / math.pi
    return i + t, s, v


def P(nm):
    return [Vector(q) for q in RINGS[RIDX[nm]]]


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
    rings = [ring(bm, r) for r in RINGS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    grow(bm, rings, spans, RIDX['B0'], LJ, RIDX['B3'] - RIDX['B0'], 3, HIND, T1_LEG)   # s4 r3: B0..B3 (R0 free: the buttock ring)
    grow(bm, rings, spans, RIDX['F1'], LJ, RIDX['F4'] - RIDX['F1'], 3, FORE, T1_LEG)
    grow_ear(bm, rings, spans, RIDX['H0'], EJ, EAR, nb=3)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.078, -0.752, 0.878))     # the eye point (front view x 0.065-0.08, side y -0.75, z 0.87)
EYE_IN = Vector((-0.62, 0.78, 0.0)).normalized()   # a forward-out facing lens (front + side visible)
SOCKET = []


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    hit, hn = tree.ray_cast(EYE - EYE_IN * 0.6, EYE_IN, 2.0)[:2]
    f = face_near(bm, hit, n=hn)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face under the brow'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.006)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    # deliberate muzzle planes (BRIEF 2.2): one flat bridge (j1-j3) and one flat side (j5-j10) per side, H4 -> H7
    MZ = [P(nm) for nm in ('H4', 'H5', 'H6', 'H7')]
    flatten([vert_near(bm, R_[j]) for R_ in MZ for j in (1, 2, 3)])
    flatten([vert_near(bm, R_[j]) for R_ in MZ for j in (5, 6, 7, 8, 9, 10)])
    # nose pad: the cap's top edge forward, the chin edge back (a forward-down slanted pad)
    H7 = MZ[-1]
    move([vert_near(bm, H7[j]) for j in (0, 1, 2, 3)], (0.0, -0.010, 0.0))
    move([vert_near(bm, H7[j]) for j in (12, 13, 14, 15)], (0.0, 0.010, 0.0))
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.03 and abs(c.z - ec0.z) < 0.03)
    commit(body, bm)


PAL = {'fur': '#dc8236', 'cream': '#f7ead2', 'stripe': '#2e2420', 'amber': '#e0a030', 'nose': '#b8675c',
       'claw': '#2a2220'}

# flank stripes in the loft frame: (s0 top-seam y at the spine, lean ds/dv, bend ds/dv^2, half width, v_start, v_end)
# full width from v_start, tapering to a point at v_end; long / short alternate, the lean turns from '/' on the
# shoulder (the rings' own forward tilt) through upright mid-body to a ')' sweep round the haunch (sheet side + top)
STRIPES = [            # s3 r2: 11 + 1 stripes 0.085 apart, long (w 0.024) / short (w 0.017, starting off the spine)
    (-0.500, -0.02, 0.00, 0.020, 0.0, 0.46),     # (r1: 14 stripes 0.07 apart, w 0.02-0.032: a dark saddle)
    (-0.430, -0.05, 0.00, 0.024, 0.0, 0.62),
    (-0.345, -0.03, 0.00, 0.017, 0.10, 0.42),
    (-0.260, 0.00, 0.00, 0.024, 0.0, 0.64),
    (-0.175, 0.03, 0.00, 0.017, 0.08, 0.44),
    (-0.090, 0.05, 0.00, 0.024, 0.0, 0.62),
    (-0.005, 0.05, 0.00, 0.017, 0.10, 0.46),
    (0.080, 0.07, -0.02, 0.024, 0.0, 0.64),
    (0.165, 0.10, -0.06, 0.017, 0.08, 0.50),
    (0.250, 0.13, -0.10, 0.024, 0.0, 0.62),
    (0.330, 0.10, -0.09, 0.017, 0.06, 0.48),
    (0.405, 0.04, -0.03, 0.018, 0.0, 0.36),
]
VAR = os.environ.get('TIGER_VAR', 'c0')     # fix-loop variant switch; 'c0' = champion 0 (s4 r4)
if VAR in ('v1', 'v3', 'v4'):
    # fix1 v1 (won both orders, r1): irregular spacing (6-11 cm), varied starts (some off the spine), two forked
    # stripes, mixed widths
    STRIPES = [
        (-0.505, -0.03, 0.00, 0.020, 0.0, 0.44), (-0.440, -0.06, 0.00, 0.026, 0.0, 0.64),
        (-0.380, -0.02, 0.00, 0.016, 0.16, 0.40), (-0.315, -0.04, 0.02, 0.024, 0.0, 0.58),
        (-0.289, -0.12, 0.00, 0.015, 0.30, 0.60), (-0.230, 0.00, 0.00, 0.022, 0.04, 0.66),
        (-0.165, 0.03, 0.00, 0.015, 0.12, 0.38), (-0.120, 0.05, 0.00, 0.026, 0.0, 0.62),
        (-0.040, 0.06, 0.00, 0.020, 0.0, 0.50), (0.005, 0.04, 0.00, 0.014, 0.20, 0.44),
        (0.065, 0.08, -0.03, 0.026, 0.0, 0.66), (0.036, 0.16, 0.00, 0.015, 0.32, 0.60),
        (0.150, 0.10, -0.06, 0.018, 0.10, 0.48), (0.205, 0.13, -0.10, 0.026, 0.0, 0.62),
        (0.285, 0.12, -0.10, 0.022, 0.0, 0.56), (0.335, 0.08, -0.06, 0.014, 0.14, 0.40),
        (0.400, 0.04, -0.03, 0.018, 0.0, 0.36)]
elif VAR == 'v2':
    # fix1 v2: the same rhythm with twice the lean (shoulder '/', mid '\', haunch ')') and the short stripes
    # starting off the spine (v 0.14), so the back is not a row of equal bars from the top
    STRIPES = [(s0, 2 * k1, 1.5 * k2, w0, (0.14 if w0 < 0.02 else va), vb) for (s0, k1, k2, w0, va, vb) in STRIPES]
# belly wedges: short stripes rising out of the cream border between the long ones (v_start low on the flank)
WEDGES = [(-0.215, 0.0, 0.0, 0.017, 0.68, 0.52), (-0.045, 0.02, 0.0, 0.017, 0.68, 0.50), (0.125, 0.05, 0.0, 0.017, 0.68, 0.52)]
# the face: short forehead dashes and two cheek stripes sweeping back under the eye
FACE = [(-0.700, 0.0, 0.0, 0.018, 0.05, 0.20), (-0.660, 0.02, 0.0, 0.018, 0.10, 0.28),
        (-0.640, 0.05, 0.0, 0.020, 0.36, 0.56), (-0.600, 0.06, 0.0, 0.020, 0.30, 0.52)]


def _ds(u):
    i = min(int(u), len(FR) - 2)
    return abs(FR[i]['s'] - FR[i + 1]['s'])


def _in_stripe(s, v, u, lst):
    ds = max(_ds(u), 0.012)
    for (s0, k1, k2, w0, va, vb) in lst:
        lo, hi = min(va, vb), max(va, vb)
        if not (lo <= v <= hi):
            continue
        f = abs(v - va) / max(abs(vb - va), 1e-6)       # 0 at the full-width end, 1 at the point
        w = w0 * min(1.0, 1.5 * (1.0 - f))
        sc = s0 + k1 * v + k2 * v * v
        ov = min(s + ds / 2, sc + w) - max(s - ds / 2, sc - w)
        if 2 * w > 0.3 * ds and ov >= 0.5 * min(ds, 2 * w):
            return True
    return False


TAIL_BANDS = (0.745, 0.680, 0.615, 0.552, 0.495)      # tail band centres (y of the span's top seam), dark club y > 0.79


V1_STRIPES = [
    (-0.505, -0.03, 0.00, 0.020, 0.0, 0.44), (-0.440, -0.06, 0.00, 0.026, 0.0, 0.64),
    (-0.380, -0.02, 0.00, 0.016, 0.16, 0.40), (-0.315, -0.04, 0.02, 0.024, 0.0, 0.58),
    (-0.289, -0.12, 0.00, 0.015, 0.30, 0.60), (-0.230, 0.00, 0.00, 0.022, 0.04, 0.66),
    (-0.165, 0.03, 0.00, 0.015, 0.12, 0.38), (-0.120, 0.05, 0.00, 0.026, 0.0, 0.62),
    (-0.040, 0.06, 0.00, 0.020, 0.0, 0.50), (0.005, 0.04, 0.00, 0.014, 0.20, 0.44),
    (0.065, 0.08, -0.03, 0.026, 0.0, 0.66), (0.036, 0.16, 0.00, 0.015, 0.32, 0.60),
    (0.150, 0.10, -0.06, 0.018, 0.10, 0.48), (0.205, 0.13, -0.10, 0.026, 0.0, 0.62),
    (0.285, 0.12, -0.10, 0.022, 0.0, 0.56), (0.335, 0.08, -0.06, 0.014, 0.14, 0.40),
    (0.400, 0.04, -0.03, 0.018, 0.0, 0.36)]
if VAR in ('v3', 'v4'):
    STRIPES = list(V1_STRIPES)
    if VAR == 'v4':
        STRIPES = [st for st in STRIPES if st[4] < 0.25]          # v4: no forks (branches starting low on a parent)

_SPAN_C = None
_GRID = None


def _span_centres():
    out = []
    for i in range(len(RINGS) - 1):
        row = []
        for j in range(NV - 1):
            q = [RINGS[i][j], RINGS[i][j + 1], RINGS[i + 1][j], RINGS[i + 1][j + 1]]
            row.append(Vector([sum(p[k] for p in q) / 4 for k in range(3)]))
        out.append(row)
    return out


def _stripe_grid():
    """fix2 (v3/v4): the flank stripes on the loft's own face grid, one id per stripe, then a separation pass: a cell
    touching (8-neighbour) a cell of ANOTHER stripe is dropped from the narrower stripe, so stripes never fuse into
    closed loops or letter shapes (r1 champion v1: 'glyph' loops at forks and wedge ends)."""
    C = _span_centres()
    L = STRIPES + WEDGES
    G = {}
    for i in range(RIDX['R0'], RIDX['C0']):
        for j in range(NV - 1):
            u, s, v = loft_param(C[i][j])
            if v > 0.68:
                continue
            for k, st in enumerate(L):
                if _in_stripe(s, v, u, [st]):
                    G[(i, j)] = k
                    break
    w = {k: st[3] for k, st in enumerate(L)}
    drop = set()
    for (i, j), k in G.items():
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                o = G.get((i + di, j + dj))
                if o is not None and o != k and (w[k], -k) < (w[o], -o):
                    drop.add((i, j))
    return {c: k for c, k in G.items() if c not in drop}


def _grid_stripe(c, u):
    global _SPAN_C, _GRID
    if _GRID is None:
        _SPAN_C = _span_centres()
        _GRID = _stripe_grid()
    i = min(max(int(u), 0), len(_SPAN_C) - 1)
    p = Vector((abs(c.x), c.y, c.z))
    j = min(range(NV - 1), key=lambda j_: (_SPAN_C[i][j_] - p).length)
    return (i, j) in _GRID


def _leg(c):
    x, y, z = abs(c.x), c.y, c.z
    for y0, y1 in ((-0.62, -0.26), (0.10, 0.44)):
        if y0 < y < y1 and x > 0.04 and z < (0.46 if x > 0.07 else 0.355):
            return True
    return False


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.893 and z > 0.765:
        return 'nose'                                   # nose pad on the muzzle tip
    if z > 1.055 and -0.66 < y < -0.56 and x > 0.05:
        return 'cream' if n.y < -0.35 else 'stripe'     # ears: cream inner (front) cup, dark back
    if _leg(c):
        if z < 0.075:
            return 'cream'                              # big cream paws
        ny = n.y if y < 0 else -n.y                     # fore: + = back; hind: + = front
        if n.x < -0.25 or (ny > 0.55 and z < 0.30):
            return 'cream'                              # inner side + the back of the fore / hind lower leg
        return 'fur'
    if SOCKET:                                          # s3 r5: a small cream brow spot over the eye (sheet: white
        e = SOCKET[0]                                   # patches above the eyes), not a ring
        if (Vector((x, y, z)) - Vector((e.x + 0.004, e.y + 0.004, e.z + 0.034))).length < 0.026:
            return 'cream'
    u, s, v = loft_param(c)
    if u < RIDX['T9']:                                  # the tail
        if s > 0.79:
            return 'stripe'                             # the black club tip
        for b in TAIL_BANDS:
            if abs(s - b) < 0.013:
                return 'stripe' if v < 0.92 else 'cream'
        return 'cream' if v > 0.70 and s < 0.60 else 'fur'
    if u >= RIDX['H4']:                                 # the muzzle: cream below the nose bridge, chin
        return 'cream' if v > 0.42 else 'fur'
    if u >= RIDX['N0']:                                 # head + ruff: cream cheeks/ruff below the eye line
        if _in_stripe(s, v, u, FACE):
            return 'stripe'
        return 'cream' if v > (0.44 if u >= RIDX['H1'] else 0.50) else 'fur'      # s3 r5: cheeks from v 0.44
    if u >= RIDX['F3'] and (v > 0.56 or (n.y < -0.35 and v > 0.42)):
        return 'cream'                                  # chest bib + throat (sheet front: cream between the legs)
    if v > 0.68:
        return 'cream'                                  # belly + lower flank
    if VAR in ('v3', 'v4'):
        if _grid_stripe(c, u):
            return 'stripe'
    elif _in_stripe(s, v, u, STRIPES) or _in_stripe(s, v, u, WEDGES):
        return 'stripe'
    return 'fur'


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
    smooth_borders(body, k=k, iters=8, despeckle=False)   # owner 10-21 borders; s3 r3: no despeckle (it broke the 1-face stripes)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c + n * 0.010, n, 0.019, 0.010)         # s3 r5: 38 mm; s4 r1: disc 4 mm proud (r5: rim under the skin)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'nose': PAL['stripe']},
          lambda c_, n_, i: 'nose' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.007 and n_.dot(n) > 0.5 else 'amber')
    pieces.append(eye)
    bm = bmesh.new()
    for sec in (FORE[-2], HIND[-2]):
        cx, cy, z, rx, ry, nn = sec
        for ang in (-58, -78, -102, -122):
            th = math.radians(ang)
            d = Vector((math.cos(th), math.sin(th), 0.0))
            o = Vector((cx, cy, 0.025)) + d * 0.3
            hit = tree.ray_cast(o, -d, 0.6)[0]
            base = Vector((hit.x, hit.y, 0.0)) if hit is not None else Vector((cx, cy, 0.0)) + d * ry
            claw(bm, base - d * 0.003, d, 0.026, 0.022, 0.028)
    claws = object_from_bm('claws', bm)
    paint(claws, {'claw': PAL['claw']}, lambda c_, n_, i: 'claw')
    pieces.append(claws)
    return pieces + details(tree)


def details(tree):
    """Tier-2 readable details (detail gate: 6-16 groups): nose pad, cheek ruff tufts, whisker pads."""
    import detail_pieces as D
    out = []

    def piece(name, bm, key, mirror=True):
        ob = object_from_bm(name, bm, mirror=mirror)
        paint(ob, {key: PAL[key]}, lambda c_, n_, i: key)
        out.append(ob)
    # nose pad: a broad pink-brown knob on the muzzle tip (sheet: a wide triangle)
    h_ = D.cast_in(tree, (0.002, -1.2, 0.785), (0, 1, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.030, 0.014, sides=8, sq=(0.75, 1.25), top=0.55)
    piece('nose', bm, 'nose', mirror=False)
    # cheek ruff: two chunky cream tufts per side sweeping back-out-down off the cheek (sheet front: the white ruff)
    bm = bmesh.new()
    for (y, z, d) in ((-0.665, 0.760, (0.50, 0.66, -0.56)), (-0.625, 0.700, (0.45, 0.62, -0.64))):   # s3 r4: stand off the cheek
        h_ = D.cast_in(tree, (1.0, y, z), (-1, 0, 0))     # s3 r5: longer, thinner, swept back-down (r4 read as blocks)
        D.fan(bm, h_[0] - h_[1] * 0.006, d, (0, 0, 1), 0.090, 0.062, 0.022, sink=0.035, spread=1.0, tip=0.35)
    piece('ruff', bm, 'cream')
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
                       20: {'ear.L': (0, 0, -10)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -4)}, 48: {}})
    A = 16
    TL = -14      # the walking tiger carries its tail a little lifted, clear of the hind legs' swing
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, 3)},
        7: {'forearm.R': (-32, 0, 0), 'paw.R': (-28, 0, 0), 'shin.L': (-18, 0, 0), 'foot.L': (22, 0, 0), 'neck': (2, 0, 0), 'tail0': (TL, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, -3)},
        19: {'forearm.L': (-32, 0, 0), 'paw.L': (-28, 0, 0), 'shin.R': (-18, 0, 0), 'foot.R': (22, 0, 0), 'neck': (2, 0, 0), 'tail0': (TL, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, 3)}})
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-10, 0, 0), 'chest': (4, 0, 0), 'head': (-4, 0, 0), 'tail0': (8, 0, 0)},
        16: {'neck': (18, 0, 0), 'chest': (-10, 0, 0), 'head': (8, 0, 0), 'upperarm.L': (14, 0, 0), 'upperarm.R': (14, 0, 0),
             'ear.L': (-12, 0, 0)},
        20: {'neck': (15, 0, 0), 'chest': (-10, 0, 0), 'head': (18, 0, 0), 'upperarm.L': (14, 0, 0), 'upperarm.R': (14, 0, 0),
             'ear.L': (-12, 0, 0)},
        24: {'neck': (16, 0, 0), 'chest': (-5, 0, 0), 'head': (6, 0, 0), 'upperarm.L': (8, 0, 0), 'upperarm.R': (8, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, 0)}, 16: {'hips': (0, 0.06, 0)}, 20: {'hips': (0, 0.06, 0)},
             24: {'hips': (0, 0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
