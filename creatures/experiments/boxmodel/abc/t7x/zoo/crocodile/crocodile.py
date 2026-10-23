import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
from smooth_borders import smooth_borders

# t9 RECREATE of zoo/crocodile (2026-10-23), t7 hand box model, zoo workflow v2 + proven tricks from day one.
# Judge's reason the zoo model fails: the sheet is a CHUNKY croc (broad rounded head, round scutes, stocky legs
# under the body); the zoo model is a stick-thin flat loft with small square scute teeth and tent-splayed legs.
# So stage 1 is measured off refs/gpt/v3/crocodile/sheet_1.png (side wins): one spine loft of 14-vertex half rings
# (tail tip -> snout), a deep round trunk (0.08-0.48 m, half width 0.25), a broad round snout (half width 0.08) and
# fat jowls, brow bumps carrying the eyes, stocky legs grown from BROAD 4 x 3 lower-flank windows through a 45 %
# transition ring and going straight down beside the belly (not splayed out), round dome scutes as pieces.
META = dict(creature='crocodile', model='opus', stage1_tris=(1200, 3800), total_tris=(2000, 5500), detail_tier=2,
            closeups=[('head', (0.0, -0.95, 0.40), 0.36, 'hero'),
                      ('front foot', (0.30, -0.45, 0.06), 0.17, 'hero'),
                      ('hind foot', (0.30, 0.12, 0.06), 0.17, 'hero'),
                      ('back scutes', (0.0, -0.10, 0.48), 0.40, 'hero')])

# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png
J = dict(
    hips=(0.0, 0.14, 0.28), spine=(0.0, -0.12, 0.29), chest=(0.0, -0.40, 0.30),
    neck=(0.0, -0.64, 0.34), head=(0.0, -0.74, 0.37), nose=(0.0, -1.20, 0.39),
    tail0=(0.0, 0.40, 0.23), tail1=(0.0, 0.62, 0.18), tail2=(0.0, 0.84, 0.155), tail3=(0.0, 1.02, 0.14),
    tail4=(0.0, 1.20, 0.14),
    shoulder=(0.235, -0.36, 0.26), elbow=(0.30, -0.34, 0.14), wrist=(0.30, -0.40, 0.045),
    ftoe=(0.31, -0.58, 0.015),
    hipL=(0.235, 0.14, 0.26), knee=(0.30, 0.11, 0.14), hock=(0.30, 0.17, 0.045),
    htoe=(0.31, -0.02, 0.015),
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


# the trunk, hand placed: j0-j2 the broad back plane (scute row), j2-j5 the back bevel, j5-j8 the bulging flank,
# j8-j11 the lower flank the legs grow from (window, 3 faces), j11-j13 the round belly (a slight keel)
BODY = [(0, 1), (0.26, 0.99), (0.50, 0.95), (0.70, 0.87), (0.85, 0.74), (0.95, 0.56), (1.0, 0.32), (1.0, 0.06),
        (0.97, -0.20), (0.91, -0.44), (0.82, -0.64), (0.70, -0.81), (0.42, -0.94), (0, -1)]   # s1 r6: rounder belly
TAIL = prof(2.1, 2.8, 0.90)
HEAD = prof(3.0, 2.6, 0.86)
MUZ = prof(3.2, 2.6, 0.88)
LJ = 5                           # leg windows: ring vertices j5 (upper) .. j9 (lower), 4 faces round, 5 spans long
                                 # (s4 r2: was 4 x 3 at j6-j9: the leg walls met the flank square (knife 2.2 r) and
                                 # the leg top was a level shelf; a broader window makes the walls slope in)
LA, LB = 5, 4
                                 # (s1 r2: was j8-j11; the front view showed a notch + shelf between flank and leg)

# brow bumps that carry the eyes (sheet front: two domes over the skull, a valley between): z lift per ring vertex
BUMP = {'C1': {1: 0.012, 2: 0.022, 3: 0.012, 4: 0.003},        # s1 r8: taller domes (sheet front: 0.05 over the skull)
        'H0': {1: 0.030, 2: 0.052, 3: 0.034, 4: 0.008},
        'H0b': {1: 0.024, 2: 0.042, 3: 0.026, 4: 0.006},
        'H1': {1: 0.006, 2: 0.012, 3: 0.006}}


def tb(nm, top, bot, W, pr):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, pr)


def v(nm, y, top, bot, W, pr):
    return tb(nm, (y, top), (y, bot), W, pr)


# the trunk + tail, measured off reference/side.png (top/bottom seam z) and top.png (half width), as a key table; the
# stations are placed from it (s1 r4: the leg windows moved to the sheet's leg positions, rings 0.055 apart there so
# a 4-span window is the sheet's round 0.22 m shoulder / thigh, not a 0.30 m slab)
KEY = [(1.200, 0.152, 0.128, 0.020), (1.150, 0.168, 0.112, 0.030), (1.080, 0.183, 0.098, 0.042),
       (1.000, 0.200, 0.085, 0.054), (0.920, 0.215, 0.075, 0.066), (0.840, 0.232, 0.068, 0.078),
       (0.760, 0.250, 0.064, 0.090), (0.680, 0.270, 0.064, 0.104), (0.600, 0.292, 0.067, 0.122),
       (0.530, 0.315, 0.071, 0.144), (0.460, 0.338, 0.075, 0.168), (0.395, 0.362, 0.080, 0.196),
       (0.320, 0.395, 0.086, 0.218), (0.245, 0.420, 0.088, 0.234), (0.170, 0.440, 0.088, 0.243),
       (0.095, 0.455, 0.087, 0.249), (0.020, 0.466, 0.085, 0.252), (-0.060, 0.472, 0.081, 0.253),
       (-0.140, 0.477, 0.079, 0.252), (-0.220, 0.481, 0.078, 0.250), (-0.300, 0.485, 0.079, 0.246),
       (-0.375, 0.490, 0.084, 0.239), (-0.450, 0.495, 0.094, 0.231), (-0.525, 0.500, 0.112, 0.222),
       (-0.600, 0.504, 0.138, 0.212)]


def key_at(y):
    for (ya, *a), (yb, *b) in zip(KEY, KEY[1:]):
        if yb <= y <= ya:
            t = (ya - y) / (ya - yb)
            return [p + (q - p) * t for p, q in zip(a, b)]
    raise ValueError(y)


TRUNK_Y = [('T0', 1.20), ('T1', 1.15), ('T2', 1.08), ('T3', 1.00), ('T4', 0.92), ('T5', 0.84), ('T6', 0.76),
           ('T7', 0.68), ('T8', 0.605), ('T9', 0.535), ('R00', 0.465), ('R0', 0.395), ('R1', 0.335),
           ('B0', 0.2775), ('B1', 0.2225), ('B2', 0.1675), ('B3', 0.1125), ('B4', 0.0575), ('B5', 0.0025),  # hind window
           ('M0', -0.055), ('M1', -0.11), ('M2', -0.165),
           ('F0', -0.2225), ('F1', -0.2775), ('F2', -0.3325), ('F3', -0.3875), ('F4', -0.4425), ('F5', -0.4975),  # fore
           ('F6', -0.55), ('F7', -0.60)]
SECS = [v(nm, y, *key_at(y), TAIL if y > 0.50 else BODY) for nm, y in TRUNK_Y] + [
    # jowls + throat (no neck: the head sits on the chest), the big cream cheeks behind the mouth corner
    v('C0', -0.645, 0.506, 0.158, 0.218, HEAD),     # s1 r9: fat jowls (sheet front 0.21 at z 0.39)
    v('C1', -0.700, 0.505, 0.190, 0.212, HEAD),
    # head: the eye station with the brow bumps (H0, H0b), then the long broad snout, rounded at the tip
    v('H0', -0.760, 0.497, 0.228, 0.190, HEAD),
    v('H0b', -0.805, 0.490, 0.255, 0.170, HEAD),
    v('H1', -0.860, 0.478, 0.284, 0.148, HEAD),
    v('H2', -0.920, 0.468, 0.300, 0.124, MUZ),
    v('H3', -0.980, 0.458, 0.310, 0.108, MUZ),
    v('H4', -1.040, 0.449, 0.317, 0.095, MUZ),
    v('H5', -1.100, 0.448, 0.322, 0.088, MUZ),
    v('H6', -1.150, 0.453, 0.328, 0.085, MUZ),
    v('H7', -1.180, 0.446, 0.340, 0.078, MUZ),
    v('H8', -1.199, 0.432, 0.355, 0.062, MUZ),     # s1 r8: the tip rounds over two more rings (was a flat disc)
    v('H9', -1.211, 0.414, 0.370, 0.036, MUZ),
]

# leg sections: (cx, cy, cz, ru, rs, exponent, theta): a rounded box whose u axis is (sin theta, 0, cos theta), s
# along y: theta 90 = a level section of a leg going straight down, theta 50 = the shoulder / haunch section turning
# out of the flank. secs[0] is the target the 45 % transition ring slopes toward. Stocky (sheet front: the leg
# column x 0.16-0.37, the outer edge nearly vertical), straight down beside the belly, broad flat feet.
FORE = [(0.278, -0.355, 0.245, 0.110, 0.112, 2.0, 32),   # shoulder: a round ball on the flank (sheet side)
        (0.290, -0.345, 0.160, 0.100, 0.120, 2.0, 68),    # elbow (back): the widest bulge
        (0.285, -0.375, 0.095, 0.083, 0.090, 2.2, 86),    # forearm
        (0.282, -0.395, 0.048, 0.066, 0.070, 2.3, 90),    # wrist (s1 r7: pulled in, the foot flares out of it)
        (0.292, -0.440, 0.017, 0.095, 0.118, 2.4, 90),    # foot pad, forward of the wrist
        (0.293, -0.450, 0.000, 0.097, 0.122, 2.4, 90)]
HIND = [(0.278, 0.140, 0.245, 0.114, 0.116, 2.0, 32),     # haunch / thigh: the sheet's big round thigh
        (0.292, 0.115, 0.160, 0.104, 0.125, 2.0, 68),     # knee (forward)
        (0.287, 0.150, 0.095, 0.085, 0.092, 2.2, 86),     # shin
        (0.283, 0.170, 0.048, 0.068, 0.072, 2.3, 90),     # ankle
        (0.292, 0.130, 0.017, 0.097, 0.122, 2.4, 90),     # foot pad
        (0.293, 0.120, 0.000, 0.099, 0.126, 2.4, 90)]
T1_LEG = 0.33                     # s4 r3: was 0.45 (lower-corner knife folds); unused since s4 r4
CORNER_OUT = 0.007
TS_LEG, TN_LEG = 0.55, 0.26       # s4 r4: fillet transition ring (along the flank / off it)


def sec_pts(nm, c, a, T, B, W, pr):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    bump = BUMP.get(nm, {})
    out = []
    for j, (fx, fh) in enumerate(pr):
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co + bump.get(j, 0.0)))
    return out


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(n, c, a, T, B, W, p)]


def akey(t):
    return round(t if t < math.pi - 1e-6 else -math.pi, 4)


def role_pos(sec, u, s, amap=None):
    """u across (+1 = the window's upper row), s front/back (+1 = rear). Boundary roles sit on the section's
    superellipse at the angle of (u, s) (amap: grid angle -> evenly spaced angle); interior roles inside it."""
    cx, cy, cz, ru, rs, n, th = sec
    ua = Vector((math.sin(math.radians(th)), 0.0, math.cos(math.radians(th))))
    if abs(u) > 0.999 or abs(s) > 0.999:
        t = math.atan2(s, u)
        if amap:
            t = amap[akey(t)]
        c, sn = math.cos(t), math.sin(t)
        du, ds = ru * math.copysign(abs(c) ** (2 / n), c), rs * math.copysign(abs(sn) ** (2 / n), sn)
    else:
        du, ds = u * ru * 0.85, s * rs * 0.85
    return Vector((cx, cy, cz)) + ua * du + Vector((0.0, ds, 0.0))


def grow(bm, rings, spans, i0, j0, A, B, secs, t1):
    """Extrude the A x B face window (rings i0..i0+A, ring vertices j0..j0+B) section by section. The first new
    ring slopes from the window rim t1 of the way to secs[0] (the broad transition), then one ring per section."""
    faces = [spans[i0 + a][j0 + b] for a in range(A) for b in range(B)]
    G = [[rings[i0 + a][j0 + b] for b in range(B + 1)] for a in range(A + 1)]
    su = 1 if G[A // 2][0].co.z > G[A // 2][B].co.z else -1
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
        for vv in r['verts']:
            o = min(roles, key=lambda o_: (o_[0] - vv.co).length)
            new.append((vv, o))
        for vv, (p0, ro) in new:
            vv.co = place(p0, ro)
        return r['faces'], [(vv.co.copy(), ro) for vv, (p0, ro) in new]

    wn = sum((f.normal for f in faces), Vector()).normalized()     # the window's outward normal

    def first(p0, ro):
        q = role_pos(secs[0], *ro)          # the transition ring keeps the window's own angles (no skew)
        d = q - p0                          # s4 r4: a fillet: the ring narrows TS of the way along the flank
        dn = wn * d.dot(wn)                 # but rises only TN of the way off it (the walls start tangential)
        return p0 + (d - dn) * TS_LEG + dn * TN_LEG
    faces, roles = step(faces, roles, first)
    for sec in secs:
        faces, roles = step(faces, roles, lambda p0, ro, sec=sec: rp(sec, *ro))
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(nm, c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    grow(bm, rings, spans, idx['B0'], LJ, LA, LB, HIND, T1_LEG)
    grow(bm, rings, spans, idx['F0'], LJ, LA, LB, FORE, T1_LEG)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.13, -0.775, 0.488))    # the eye aim point on the brow bump's outer side; a ray from out-up hits it
SOCKET = []
VAR = os.environ.get('CROC_VAR', 'v1')     # fix r1 adopted variant: v1


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    d = Vector((-1.0, 0.0, -0.35)).normalized()
    hit, hn = tree.ray_cast(EYE - d * 1.0, d, 2.0)[:2]
    f = face_near(bm, hit, n=hn)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the brow bump face'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.006)
    sc = sum((v_.co for v_ in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    # deliberate snout planes (BRIEF 2.2): one flat top (j0-j3) per side, H2 -> H6
    MZ = [P(nm) for nm in ('H2', 'H3', 'H4', 'H5', 'H6')]
    flatten([vert_near(bm, R_[j]) for R_ in MZ for j in (0, 1, 2, 3)])
    # s4 r5: soften the leg windows' lower front/rear corners (junction probe: small knife folds in the armpit /
    # groin): the corner root vertex and the flank vertex under it ease out along the flank normal
    for a, b in (('F0', 'F5'), ('B0', 'B5')):
        for nm in (a, b):
            R_ = P(nm)
            for j, k_ in ((LJ + LB, CORNER_OUT),):
                q = vert_near(bm, R_[j])
                nx = Vector((q.co.x, 0.0, -0.35 * q.co.x)).normalized()
                q.co += nx * k_
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.035 and abs(c.y - ec0.y) < 0.035 and abs(c.z - ec0.z) < 0.035)
    commit(body, bm)


PAL = {'olive': '#7a7656', 'cream': '#ead6a0', 'scute': '#68644a',   # s3 r4: sampled off the sheet (khaki olive)
       'claw': '#3a3536', 'tooth': '#f3efe2',
       'amber': '#e0a030', 'pupil': '#1a1615'}

_ST = sorted([(c[0], c[1], T) for (nm, c, a, T, B_, W, p) in SECS])
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
    for y0, y1 in ((-0.62, -0.20), (-0.06, 0.30)):
        if y0 < y < y1 and x > 0.20 and z < 0.245:
            return True
    return False


def mouth_z(y):
    """The mouth line: level along the snout, a little smile rise to the corner at y -0.66."""
    return 0.366 + 0.012 * max(0.0, min(1.0, (y + 0.86) / 0.20))


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if _leg(c):
        return 'olive'
    if y < -0.64:
        return 'cream' if z < mouth_z(y) else 'olive'      # lower jaw, jowls and throat cream (sheet side)
    zc, h = _frame(y)
    fh = (z - zc) / h
    return 'cream' if fh < (-0.10 if y < 0.45 else -0.22) else 'olive'   # s3 r4: belly + lower flank to j8 (sheet), tail underside


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
    """A chunky claw: an arched 6-sided section swept out of the toe tip, a root sunk 2 cm in, a blunt tip."""
    out = Vector(out).normalized()
    side = out.cross(Vector((0, 0, 1))).normalized()
    up = Vector((0, 0, 1))
    SEC = [(-1, 0), (1, 0), (0.85, 0.6), (0.4, 1.0), (-0.4, 1.0), (-0.85, 0.6)]
    rows = []
    for off, sw, sh, dz in ((-0.010, 0.75, 0.75, 0.0), (d * 0.6, 0.9, 0.85, -0.002), (d, 0.6, 0.5, -0.004)):      # s4 r10: root 10 mm in, 75 % section: stays inside the toe tip (qa hit 8)
        c = base + out * off + up * (0.004 + dz)
        rows.append([bm.verts.new(c + side * su * w * sw / 2 + up * (sz * hgt * sh)) for su, sz in SEC])
    n = len(SEC)
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(n):
            bm.faces.new([a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]])
    bm.faces.new(rows[-1])


def tooth(bm, p, out, l, w):
    """A chunky blunt tooth hanging from the upper-jaw edge: a 4-sided frustum, the root sunk into the lip."""
    out = Vector(out).normalized()
    fw = Vector((0, 1, 0))
    top = [p - out * 0.008 + out * su * w * 0.5 + fw * sf * w * 0.55 + Vector((0, 0, 0.006)) for su, sf in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bot = [p + out * 0.002 + out * su * w * 0.30 + fw * sf * w * 0.32 + Vector((0, 0, -l)) for su, sf in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    A = [bm.verts.new(q) for q in top]
    B = [bm.verts.new(q) for q in bot]
    bm.faces.new(A); bm.faces.new(list(reversed(B)))
    for j in range(4):
        bm.faces.new([A[j], B[j], B[(j + 1) % 4], A[(j + 1) % 4]])
    recalc_normals(bm)


def cone_tooth(bm, p, out, l, r, sides=6):
    """fix loop r1: a chunky white cone tooth hanging from the mouth line, root sunk 9 mm into the lip, tip
    blunt, leaning a little out so it stands proud of the lower jaw (sheet: white triangular teeth)."""
    out = Vector((out[0], 0.0, 0.0)).normalized() if abs(out[0]) > 1e-6 else Vector((1, 0, 0))
    ax = (Vector((0, 0, -1)) + out * 0.25).normalized()
    u = out.cross(ax).normalized(); w = ax.cross(u).normalized()
    rows = []
    for off, rr in ((-0.009, 1.0), (l * 0.55, 0.62), (l, 0.28)):
        c = p - ax * 0.0 + ax * off + out * 0.004
        rows.append([bm.verts.new(c + (u * math.cos(t) + w * math.sin(t)) * r * rr)
                     for t in [2 * math.pi * (k_ + 0.5) / sides for k_ in range(sides)]])
    bm.faces.new(list(reversed(rows[0])))
    for A, B in zip(rows, rows[1:]):
        for j in range(sides):
            bm.faces.new([A[j], A[(j + 1) % sides], B[(j + 1) % sides], B[j]])
    bm.faces.new(rows[-1])
    recalc_normals(bm)


TOE = 'cream' if VAR == 'v2' else 'olive'                       # fix r1 v2: cream toes (sheet top view) for claw contrast
CLAW = (0.034, 0.028, 0.032) if VAR in ('v1', 'v2') else (0.026, 0.022, 0.024)   # fix r1: bigger dark claws


def stage3(k, body):
    import parts as PT
    import detail_pieces as D
    PT.set_style('game')
    paint(body, PAL, body_rule)
    smooth_borders(body, k=k, iters=8)      # owner 10-21: borders follow the form (kit/smooth_borders)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []

    def piece(name, bm, key, mirror=True):
        ob = object_from_bm(name, bm, mirror=mirror)
        paint(ob, {key: PAL[key]}, lambda c_, n_, i: key)
        pieces.append(ob)
        return ob
    # eye: a small amber lens with a dark pupil in the brow-bump socket, facing out, up and a little forward
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.25, 0.15))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.004, n, 0.020, 0.010)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.009 and n_.dot(n) > 0.5 else 'amber')
    pieces.append(eye)
    # scutes: one central row of round domes from the nape down the back and tail (sheet top + rear), shrinking
    bm = bmesh.new()
    y = -0.66
    while y < 1.10:
        h_ = D.cast_in(tree, (0.002, y, 2.0), (0, 0, -1))
        if h_:
            f = max(0.0, min(1.0, (y - 0.25) / 0.85))
            r = 0.052 - 0.030 * f
            hh = 0.034 - 0.016 * f
            nrm = Vector((0.0, h_[1].y, abs(h_[1].z))).normalized()
            D.knob(bm, (0.0, h_[0].y, h_[0].z), nrm, r, hh, sides=8, sink=0.012, sq=(1.15, 0.85),
                   up=(0, -1, 0), top=0.5)
        y += 0.125 - 0.035 * max(0.0, min(1.0, (y - 0.25) / 0.85))
    piece('scutes', bm, 'scute', mirror=False)
    # nostrils: two small domes on the snout tip
    bm = bmesh.new()
    h_ = D.cast_in(tree, (0.038, -1.165, 2.0), (0, 0, -1))
    D.knob(bm, h_[0], h_[1], 0.019, 0.012, sides=6, sink=0.008, top=0.5)
    piece('nostrils', bm, 'scute')
    # teeth: four chunky blunt pegs a side hanging from the mouth line of the upper jaw
    bm = bmesh.new()
    if VAR == 'v1':          # fix r1 v1: four chunky cone teeth a side
        for yy, l in ((-1.15, 0.032), (-1.07, 0.026), (-0.99, 0.030), (-0.92, 0.024)):
            h_ = D.cast_in(tree, (1.0, yy, mouth_z(yy) + 0.004), (-1, 0, 0))
            cone_tooth(bm, h_[0], h_[1], l, 0.012)
    elif VAR == 'v2':        # fix r1 v2: three big cone teeth a side (front, mid, back of the snout)
        for yy, l in ((-1.14, 0.038), (-1.03, 0.032), (-0.93, 0.036)):
            h_ = D.cast_in(tree, (1.0, yy, mouth_z(yy) + 0.004), (-1, 0, 0))
            cone_tooth(bm, h_[0], h_[1], l, 0.015)
    else:
        for yy, l in ((-1.15, 0.026), (-1.07, 0.020), (-0.99, 0.024), (-0.92, 0.018)):
            h_ = D.cast_in(tree, (1.0, yy, mouth_z(yy) + 0.004), (-1, 0, 0))
            tooth(bm, h_[0], h_[1], l, 0.016)
    piece('teeth', bm, 'tooth')
    # toes: four fat splayed toes per foot (parts library digits_splayed, game style), claws on the tips
    bmc = bmesh.new()
    toes = []
    for sec, fwd in ((FORE[-1], (0.30, -1.0, 0.0)), (HIND[-1], (0.40, -1.0, 0.0))):
        cx, cy, cz, ru, rs = sec[:5]
        for sd in (1, -1):                       # the parts are not mirrored: build both sides (side=-1 mirrors)
            fw = Vector((fwd[0] * sd, fwd[1], 0.0)).normalized()
            ctr = Vector((cx * sd, cy, 0.0)) + fw * (rs * 0.55)
            tob = PT.digits_splayed(ctr, lengths=(0.046, 0.054, 0.054, 0.048), width=0.042, height=0.030,
                                    spread=104.0, r0=0.040, forward=tuple(fw), up=(0, 0, 1), side=sd, knobs=True,   # s3 r5: fat toes
                                    lift=0.006, name='toes', mats={'skin': TOE, 'tip': TOE},
                                    colours={'skin': PAL[TOE], 'tip': PAL[TOE]})
            toes.append(tob)
            if sd < 0:
                continue                         # claws: built on the left, the live mirror makes the right
            for tip in PT.attach(tob)['finger_tips']:
                d_ = Vector((tip.x - ctr.x, tip.y - ctr.y, 0.0)).normalized()
                claw(bmc, Vector((tip.x, tip.y, 0.0)) - d_ * 0.006, d_, *CLAW)
    for t in toes:
        pieces.append(t)
    piece('claws', bmc, 'claw')
    return pieces


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('tail3', J['tail3'], J['tail4'], 'tail2', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('paw.L', J['wrist'], J['ftoe'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
         ('foot.L', J['hock'], J['htoe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.0, 0, 0), 'tail1': (0, 0, 4), 'tail2': (0, 0, 5)},
                       24: {'head': (-3, 0, 0)}, 36: {'chest': (1.0, 0, 0), 'tail1': (0, 0, -4), 'tail2': (0, 0, -5)},
                       48: {}})
    A, S = 16, 5
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0),
            'spine': (0, 0, S), 'tail0': (0, 0, -S), 'tail1': (0, 0, -S), 'tail2': (0, 0, S)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0),
             'spine': (0, 0, -S), 'tail0': (0, 0, S), 'tail1': (0, 0, S), 'tail2': (0, 0, -S)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0),
             'spine': (0, 0, S), 'tail0': (0, 0, -S), 'tail1': (0, 0, -S), 'tail2': (0, 0, S)}})
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (6, 0, 0), 'head': (4, 0, 0), 'tail0': (0, 0, 8)},
        14: {'neck': (-8, 0, 10), 'head': (-12, 0, 5), 'tail0': (0, 0, -10), 'tail1': (0, 0, -8)},
        18: {'neck': (-6, 0, 8), 'head': (-9, 0, 3), 'tail0': (0, 0, -10), 'tail1': (0, 0, -8)},
        26: {'neck': (2, 0, 2), 'head': (2, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.03, 0)}, 14: {'hips': (0, -0.06, 0)}, 18: {'hips': (0, -0.06, 0)},
             26: {'hips': (0, -0.02, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
