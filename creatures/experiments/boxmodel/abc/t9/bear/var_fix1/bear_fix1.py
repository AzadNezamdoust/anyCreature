import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
from smooth_borders import smooth_borders

# t9 RECREATE of zoo/bear (2026-10-23), built from the t9 fox program (same t7 hand box model + proven tricks):
# one spine loft of 14-vertex half rings (rump cap -> nose), legs grown from BROAD 4 x 3 lower-flank windows through a
# 45 % transition ring, small round ears from 1 x 2 skull windows (ring morph of the root shape), colour borders on
# placed loops + kit/smooth_borders, chunky claws, a small lens eye. Identity: shoulder hump, dish face + tan muzzle,
# massive columnar legs, small round ears, stub tail.
META = dict(creature='bear', model='opus', stage1_tris=(1200, 3600), total_tris=(1500, 4800), detail_tier=2,
            closeups=[('head', (0.0, -0.75, 0.95), 0.35, 'hero'),
                      ('front foot', (0.20, -0.27, 0.12), 0.25, 'hero'),
                      ('hind foot', (0.20, 0.66, 0.12), 0.25, 'hero'),
                      ('rump', (0.0, 0.85, 0.75), 0.30, 'az090')])

J = dict(
    hips=(0.0, 0.62, 0.85), spine=(0.0, 0.15, 0.85), chest=(0.0, -0.25, 0.90),
    neck=(0.0, -0.48, 0.95), head=(0.0, -0.60, 0.95), nose=(0.0, -0.93, 0.84),
    shoulder=(0.20, -0.23, 0.75), elbow=(0.20, -0.24, 0.40), wrist=(0.20, -0.25, 0.12),
    fpaw=(0.20, -0.27, 0.04), ftoe=(0.20, -0.42, 0.02),
    hipL=(0.20, 0.64, 0.75), knee=(0.20, 0.62, 0.40), hock=(0.20, 0.68, 0.15),
    hpaw=(0.20, 0.66, 0.04), htoe=(0.20, 0.52, 0.02),
    ear=(0.155, -0.595, 1.12), eartip=(0.165, -0.59, 1.20),
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
HEAD = prof(2.8, 2.6, 0.85)
MUZ = prof(3.2, 2.8, 0.90)
LJ = 9                           # leg windows: ring vertices j9 (outer) .. j12 (inner), 3 faces round, 4 spans long
EJ = 1                           # ear windows: j1 .. j3 on the skull's upper side (2 faces), 1 span long


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
    # rump (capped) + hind-leg window rings (B0..B4, rear -> front)
    tb('R0', (0.905, 0.775), (0.905, 0.500), 0.20, BODY),
    tb('R1', (0.85, 0.855), (0.85, 0.405), 0.30, BODY),
    tb('B0', (0.78, 0.895), (0.78, 0.370), 0.345, BODY),
    tb('B1', (0.70, 0.948), (0.70, 0.355), 0.370, BODY),
    tb('B2', (0.62, 1.000), (0.62, 0.345), 0.380, BODY),
    tb('B3', (0.54, 1.030), (0.54, 0.340), 0.380, BODY),
    tb('B4', (0.46, 1.045), (0.46, 0.338), 0.375, BODY),
    # the barrel
    tb('M0', (0.37, 1.057), (0.37, 0.337), 0.370, BODY),
    tb('M1', (0.28, 1.060), (0.28, 0.336), 0.365, BODY),
    tb('M2', (0.19, 1.062), (0.19, 0.336), 0.362, BODY),
    tb('M3', (0.10, 1.068), (0.10, 0.355), 0.362, BODY),
    tb('M4', (0.02, 1.115), (0.02, 0.372), 0.366, BODY),
    # fore-leg window rings under the shoulder hump (F0..F4)
    tb('F0', (-0.06, 1.162), (-0.06, 0.380), 0.372, BODY),
    tb('F1', (-0.14, 1.190), (-0.14, 0.382), 0.380, BODY),
    tb('F2', (-0.22, 1.200), (-0.22, 0.386), 0.380, BODY),
    tb('F3', (-0.30, 1.178), (-0.31, 0.392), 0.374, BODY),
    tb('F4', (-0.38, 1.158), (-0.40, 0.405), 0.360, BODY),
    # brisket + thick short neck
    tb('C0', (-0.44, 1.156), (-0.47, 0.470), 0.335, BODY),
    tb('N0', (-0.50, 1.160), (-0.53, 0.600), 0.305, NECK),
    # head: broad skull (ear window H0 -> H1), eye on H2/H3, the stop H3 -> H4, the tan muzzle H4-H7
    tb('H0', (-0.565, 1.150), (-0.585, 0.668), 0.272, HEAD),
    tb('H1', (-0.635, 1.120), (-0.635, 0.700), 0.268, HEAD),
    tb('H2', (-0.690, 1.080), (-0.690, 0.712), 0.238, HEAD),
    tb('H3', (-0.745, 1.025), (-0.745, 0.726), 0.190, HEAD),
    tb('H4', (-0.795, 0.955), (-0.795, 0.737), 0.142, MUZ),
    tb('H5', (-0.850, 0.918), (-0.850, 0.748), 0.118, MUZ),
    tb('H6', (-0.900, 0.890), (-0.900, 0.775), 0.092, MUZ),
    tb('H7', (-0.930, 0.872), (-0.930, 0.800), 0.062, MUZ),
]

# leg sections: (cx, cy, z, rx, ry, exponent): level rounded boxes, deeper front-to-back; secs[0] is the target the
# transition ring slopes toward. Chunky legs (sheet front: socks 0.09-0.10 wide), broad paws.
FORE = [(0.218, -0.230, 0.380, 0.138, 0.170, 2.6),   # upper arm under the hump (s1 r2: inner wall clear of the belly)
        (0.208, -0.235, 0.300, 0.132, 0.150, 2.6),   # elbow
        (0.200, -0.240, 0.220, 0.130, 0.140, 2.6),   # forearm
        (0.200, -0.248, 0.130, 0.128, 0.138, 2.6),   # wrist
        (0.200, -0.262, 0.060, 0.145, 0.170, 2.4),   # paw
        (0.200, -0.275, 0.0, 0.150, 0.190, 2.4)]
HIND = [(0.220, 0.640, 0.360, 0.140, 0.200, 2.6),    # thigh under the haunch (s1 r2: inner wall clear of the belly)
        (0.210, 0.655, 0.290, 0.133, 0.160, 2.6),
        (0.200, 0.670, 0.210, 0.130, 0.142, 2.6),
        (0.200, 0.680, 0.130, 0.128, 0.138, 2.6),    # hock
        (0.200, 0.670, 0.060, 0.145, 0.170, 2.4),
        (0.200, 0.660, 0.0, 0.150, 0.190, 2.4)]
# small round ears: ring morph of the 1 x 2 root window (station 0 is approached through the 45 % transition ring)
EAR = [((0.160, -0.598, 1.165), 0.95, 0.80, 0.45),
       ((0.164, -0.596, 1.195), 0.75, 0.62, 0.25),
       ((0.166, -0.595, 1.212), 0.35, 0.30, 0.10)]
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
    grow(bm, rings, spans, idx['B0'], LJ, 4, 3, HIND, T1_LEG)
    grow(bm, rings, spans, idx['F0'], LJ, 4, 3, FORE, T1_LEG)
    grow_ear(bm, rings, spans, idx['H0'], EJ, EAR, nb=2)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.0, -0.725, 0.985))     # the eye point on the side view (y, z); x from a ray on the head side
SOCKET = []
VAR = os.environ.get('BEAR_VAR', '')


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
    if VAR != 'base':
        # fix1 (judge vs zoo: no hump, a capsule barrel): the shoulder hump raised over the fore-leg window and the
        # back behind it dropped to a saddle, smooth cos falloff on the upper half of the body only
        for v in bm.verts:
            if v.co.z > 0.80:
                w = max(0.0, (v.co.z - 0.80) / 0.40)
                hump = 0.055 * max(0.0, math.cos(min(math.pi / 2, abs(v.co.y + 0.20) / 0.26 * math.pi / 2)))
                sad = -0.030 * max(0.0, math.cos(min(math.pi / 2, abs(v.co.y - 0.25) / 0.30 * math.pi / 2)))
                v.co.z += (hump + sad) * w * (1.0 - 0.5 * min(1.0, abs(v.co.x) / 0.38))
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.03 and abs(c.z - ec0.z) < 0.03)
    commit(body, bm)


PAL = {'fur': '#9c6842', 'dark': '#5e3b27', 'muzzle': '#d2ab80', 'nose': '#181313', 'claw': '#e8d5b3',
       'iris': '#5a3418'}     # the zoo bear's palette (owner-seen); sheet: brown coat, darker legs/belly, tan muzzle

_ST = sorted([(c[0], c[1], T) for (nm, c, a, T, B_, W, p) in SECS ])
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
    for y0, y1 in ((-0.46, 0.05), (0.40, 0.86)):
        if y0 < y < y1 and x > 0.07 and z < (0.42 if x > 0.12 else 0.36):
            return True
    return False


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.915 and z > 0.835 and x < 0.05:
        return 'nose'                                   # nose pad (s4 r2: the tip only; r1 blacked the whole cap)
    if z > 1.13 and -0.66 < y < -0.53 and x > 0.08:
        return 'dark'                                   # ears
    if _leg(c) and (z < 0.30 or VAR == 'base'):
        return 'dark'                                   # fix1: dark from the elbow/stifle loop down (r2: a dark band
    if _leg(c):                                         # on the transition ring read as a stuck-on leg top)
        return 'fur'
    zc, h = _frame(y)
    fh = (z - zc) / h
    if y < -0.79:
        return 'muzzle'                                 # tan muzzle box, on the H4 loop
    if y > -0.47:
        return 'dark' if fh < -0.80 else 'fur'          # s4 r2: belly underside only (r1: the lower half went dark)
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
    smooth_borders(body, k=k, iters=8)      # owner 10-21: borders follow the form (kit/smooth_borders)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.35, 0.0))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.004, n, 0.021, 0.010)
    eye = object_from_bm('eye', bm)
    paint(eye, {'iris': PAL['iris'], 'nose': PAL['nose']},
          lambda c_, n_, i: 'nose' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.010 and n_.dot(n) > 0.5 else 'iris')
    pieces.append(eye)
    bm = bmesh.new()
    for sec in (FORE[-2], HIND[-2]):
        cx, cy, z, rx, ry, nn = sec
        for ang in (-55, -78, -102, -125):
            th = math.radians(ang)
            d = Vector((math.cos(th), math.sin(th), 0.0))
            o = Vector((cx, cy, 0.03)) + d * 0.5
            hit = tree.ray_cast(o, -d, 1.0)[0]
            base = Vector((hit.x, hit.y, 0.0)) if hit is not None else Vector((cx, cy, 0.0)) + d * ry
            claw(bm, base - d * 0.004, d, 0.042, 0.030, 0.050)
    claws = object_from_bm('claws', bm)
    paint(claws, {'claw': PAL['claw']}, lambda c_, n_, i: 'claw')
    pieces.append(claws)
    return pieces + details(tree)


def details(tree):
    """Tier-2 readable details: nose pad, stub tail."""
    import detail_pieces as D
    out = []

    def piece(name, bm, key, mirror=True):
        ob = object_from_bm(name, bm, mirror=mirror)
        paint(ob, {key: PAL[key]}, lambda c_, n_, i: key)
        out.append(ob)
    h_ = D.cast_in(tree, (0.002, -1.4, 0.835), (0, 1, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.045, 0.022, sides=8, sq=(0.75, 1.2), top=0.55)
    piece('nose', bm, 'nose', mirror=False)
    h_ = D.cast_in(tree, (0.002, 2.0, 0.80), (0, -1, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.055, 0.05, sides=8, sq=(1.0, 0.9), top=0.5)
    piece('tail', bm, 'fur', mirror=False)
    # s4 r2: brow mounds above-behind each eye (the bear's heavy brow; detail count 5 -> 6)
    e = SOCKET[0]
    h_ = D.cast_in(tree, (e.x + 1.0, e.y + 0.035, e.z + 0.05), (-1, 0, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.04, 0.016, sides=7, sq=(0.8, 1.3), top=0.5)
    piece('brow', bm, 'fur')
    return out


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
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
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0)}, 20: {'ear.L': (0, 0, -10), 'head': (2, 0, 3)},
                       27: {}, 36: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'head': (0, 0, -3)}, 48: {}})
    A = 14
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0)},
        7: {'forearm.R': (-28, 0, 0), 'paw.R': (-22, 0, 0), 'shin.L': (-14, 0, 0), 'foot.L': (18, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0)},
        19: {'forearm.L': (-28, 0, 0), 'paw.L': (-22, 0, 0), 'shin.R': (-14, 0, 0), 'foot.R': (18, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0)}})
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-8, 0, 0), 'chest': (3, 0, 0), 'head': (-6, 0, 0)},
        16: {'neck': (14, 0, 0), 'chest': (-8, 0, 0), 'head': (10, 0, 0), 'upperarm.L': (12, 0, 0), 'upperarm.R': (12, 0, 0),
             'ear.L': (-10, 0, 0)},
        20: {'neck': (12, 0, 0), 'chest': (-8, 0, 0), 'head': (16, 0, 0), 'upperarm.L': (12, 0, 0), 'upperarm.R': (12, 0, 0)},
        24: {'neck': (10, 0, 0), 'chest': (-4, 0, 0), 'head': (5, 0, 0), 'upperarm.L': (6, 0, 0), 'upperarm.R': (6, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.03, 0)}, 16: {'hips': (0, -0.06, 0)}, 20: {'hips': (0, -0.06, 0)},
             24: {'hips': (0, -0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
