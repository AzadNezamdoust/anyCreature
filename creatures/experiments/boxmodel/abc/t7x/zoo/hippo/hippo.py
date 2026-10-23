import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
from smooth_borders import smooth_borders
import parts as PT

# t7 hand box model (zoo workflow v2), template zoo/rhino: one spine loft of 14-vertex hand-placed half rings (tail tip
# -> muzzle front), the short flat tail a 6-vertex run joined to the rump by an uneven open-row bridge; legs extruded
# from BROAD 4 x 3-face windows on the lower-flank bevel through a transition ring that slopes from the window rim into
# the leg (rhino's leg-root trick); small ears from 1 x 2-face windows on the flat skull top. The muzzle is a wide box
# (high-exponent sections, a broad flat front), the stop a steep step up to the eye bumps on the skull top.
META = dict(creature='hippo', model='opus', stage1_tris=(1800, 3800), total_tris=(2400, 5800),
            closeups=[('head', (0.0, -1.20, 1.10), 0.50, 'hero'),
                      ('front foot', (0.31, -0.29, 0.12), 0.25, 'hero'),
                      ('hind foot', (0.31, 1.18, 0.12), 0.25, 'hero'),
                      ('tail', (0.0, 1.62, 0.95), 0.25, 'az090')])

# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png
J = dict(
    hips=(0.0, 1.15, 1.05), spine=(0.0, 0.45, 1.00), chest=(0.0, -0.25, 1.00),
    neck=(0.0, -0.62, 1.12), head=(0.0, -0.86, 1.15), nose=(0.0, -1.55, 0.95),
    tail0=(0.0, 1.60, 1.03), tail1=(0.0, 1.645, 0.93), tail2=(0.0, 1.685, 0.81), tail3=(0.0, 1.705, 0.73),
    shoulder=(0.31, -0.28, 0.72), elbow=(0.31, -0.28, 0.40), wrist=(0.305, -0.30, 0.14),
    fpaw=(0.31, -0.32, 0.04), ftoe=(0.31, -0.50, 0.0),
    hipL=(0.31, 1.20, 0.80), knee=(0.31, 1.19, 0.42), hock=(0.305, 1.17, 0.16),
    hpaw=(0.31, 1.155, 0.04), htoe=(0.31, 0.98, 0.0),
    ear=(0.235, -0.855, 1.50), eartip=(0.275, -0.86, 1.62),
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


# the barrel, hand placed: j0-j2 a broad back plane, j2-j5 the shoulder bevel, j5-j8 the flank plane, j8-j12 the full
# lower flank / belly the legs grow from (window j9-j12), j12-j13 the belly strip
BODY = [(0, 1), (0.27, 0.975), (0.47, 0.90), (0.66, 0.75), (0.82, 0.55), (0.93, 0.33), (0.99, 0.10),   # s1 r2: a domed
        (1.0, -0.13), (0.97, -0.36), (0.89, -0.58), (0.74, -0.76), (0.50, -0.90), (0.21, -0.985), (0, -1)]   # back, sagging belly
RUMP = prof(2.2, 2.2, 0.9)       # the rump's last ring: EVEN angles (elephant s2 r6: no bunched verts fanned to the tail)
NECK = prof(2.6, 2.6, 0.9)
HEAD = prof(3.0, 2.8, 0.88)      # broad flat skull top, wide jaw
MUZ = prof(4.5, 4.0, 0.95)       # the square muzzle box: flat top, flat sides, flat underside
TAIL = prof(2.2, 2.2, 0.85, nv=6)
LJ = 9                           # leg windows: ring vertices j9 (outer) .. j12 (inner), 3 faces round, 4 spans long
EJ = 1                           # ear windows: j1 .. j3 on the skull top (2 faces), 1 span long


def tb(nm, top, bot, W, pr):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, pr)


def tc(nm, c, a, h, W, pr):
    """A section from its centre (y, z), its tilt a (deg; 0 = an upright ring, 90 = a level ring whose 'top' seam
    point is the rear) and its half height h."""
    return (nm, c, a, h, h, W, pr)


SECS = [
    # the tail, tip -> root: short and flat, hanging down-back off the rump's upper rear (6-vertex rings)
    tc('T0', (1.712, 0.715), 72, 0.012, 0.018, TAIL),
    tc('T1', (1.705, 0.752), 72, 0.026, 0.040, TAIL),     # the dark tip
    tc('T2', (1.690, 0.800), 72, 0.024, 0.036, TAIL),
    tc('T3', (1.670, 0.862), 68, 0.028, 0.042, TAIL),
    tc('T4', (1.650, 0.925), 58, 0.034, 0.050, TAIL),
    tc('T5', (1.630, 0.978), 42, 0.042, 0.060, TAIL),
    # the tail root ring (6-vertex, broad) and the rump's rear
    tc('Rt', (1.612, 1.03), 20, 0.064, 0.088, TAIL),
    tb('R0', (1.582, 1.125), (1.60, 0.865), 0.17, RUMP),
    tb('R1', (1.530, 1.215), (1.585, 0.700), 0.31, BODY),
    # hind-leg window rings (rear -> front)
    tb('B0', (1.47, 1.300), (1.47, 0.510), 0.41, BODY),
    tb('B1', (1.34, 1.385), (1.34, 0.478), 0.485, BODY),
    tb('B2', (1.21, 1.456), (1.21, 0.452), 0.545, BODY),
    tb('B3', (1.08, 1.517), (1.08, 0.426), 0.595, BODY),
    tb('B4', (0.95, 1.556), (0.95, 0.398), 0.62, BODY),
    # the barrel: the belly hangs lowest at y 0.5
    tb('M0', (0.81, 1.583), (0.81, 0.367), 0.645, BODY),
    tb('M1', (0.67, 1.594), (0.67, 0.335), 0.67, BODY),
    tb('M2', (0.53, 1.592), (0.53, 0.305), 0.69, BODY),
    tb('M3', (0.39, 1.577), (0.39, 0.320), 0.69, BODY),
    tb('M4', (0.25, 1.560), (0.25, 0.340), 0.685, BODY),
    tb('M5', (0.11, 1.543), (0.11, 0.360), 0.665, BODY),
    # fore-leg window rings (rear -> front)
    tb('F0', (-0.03, 1.527), (-0.03, 0.380), 0.635, BODY),
    tb('F1', (-0.16, 1.508), (-0.16, 0.395), 0.58, BODY),
    tb('F2', (-0.29, 1.508), (-0.29, 0.410), 0.55, BODY),
    tb('F3', (-0.42, 1.525), (-0.42, 0.420), 0.535, BODY),
    tb('F4', (-0.55, 1.545), (-0.55, 0.460), 0.52, BODY),
    # neck: short and thick, the throat dropping into the chest
    tb('N0', (-0.66, 1.548), (-0.66, 0.550), 0.47, NECK),
    tb('N1', (-0.76, 1.541), (-0.76, 0.665), 0.43, NECK),
    # head: skull (ear window H0-H1, eye on H2), the stop H3 -> H4, the square muzzle H4-H9
    tb('H0', (-0.79, 1.535), (-0.79, 0.700), 0.405, HEAD),
    tb('H1', (-0.92, 1.505), (-0.92, 0.724), 0.40, HEAD),
    tb('H2', (-1.04, 1.465), (-1.04, 0.726), 0.375, HEAD),
    tb('H3', (-1.14, 1.420), (-1.14, 0.718), 0.35, HEAD),
    tb('H4', (-1.23, 1.305), (-1.23, 0.705), 0.355, MUZ),
    tb('H5', (-1.33, 1.255), (-1.33, 0.695), 0.385, MUZ),
    tb('H6', (-1.43, 1.205), (-1.43, 0.693), 0.40, MUZ),
    tb('H7', (-1.51, 1.155), (-1.51, 0.720), 0.39, MUZ),
    tb('H8', (-1.565, 1.115), (-1.565, 0.780), 0.36, MUZ),
    tb('H9', (-1.598, 1.060), (-1.588, 0.840), 0.32, MUZ),    # the broad flat muzzle front (capped)
]

# leg sections: (cx, cy, z, rx, ry, exponent): level rounded boxes, deeper front-to-back; secs[0] is the target the
# transition ring slopes toward (it sits at T1 of the way from the window rim). Short thick columns, round feet.
FORE = [(0.31, -0.28, 0.36, 0.172, 0.190, 2.6),   # upper arm under the chest
        (0.31, -0.285, 0.27, 0.165, 0.182, 2.6),
        (0.305, -0.29, 0.19, 0.157, 0.172, 2.6),
        (0.305, -0.30, 0.12, 0.155, 0.170, 2.6),  # wrist, the narrowest
        (0.31, -0.315, 0.05, 0.172, 0.192, 2.4),  # the round foot flaring
        (0.31, -0.325, 0.0, 0.178, 0.198, 2.4)]
HIND = [(0.31, 1.20, 0.38, 0.178, 0.200, 2.6),    # thigh under the haunch
        (0.31, 1.19, 0.29, 0.168, 0.188, 2.6),
        (0.305, 1.18, 0.20, 0.158, 0.175, 2.6),
        (0.305, 1.17, 0.12, 0.155, 0.170, 2.6),   # hock
        (0.31, 1.16, 0.05, 0.172, 0.192, 2.4),
        (0.31, 1.155, 0.0, 0.178, 0.198, 2.4)]
# small round ears on the skull top: (cx, cy, z, rx, ry, exponent, tilt); tilt: the ring tips with the skull's side
# slope (rhino s1 r14) so the ear rises square off it
EAR = [(0.232, -0.855, 1.565, 0.046, 0.036, 2.4, 0.3),     # s1 r5: the root ring 3 cm inside the window rim on every
       (0.245, -0.858, 1.595, 0.058, 0.040, 2.2, 0.15),    # side and 4-6 cm above it (r4: 1 cm outer margin = a 10 mm
       (0.258, -0.860, 1.622, 0.048, 0.030, 2.2, 0.05),    # strip); the cup flares above the root, blunt round top
       (0.265, -0.862, 1.638, 0.026, 0.016, 2.0)]
T1_LEG, T1_EAR = 0.45, 0.45   # s1 r4: the ear transition slopes like the legs'


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
    tilt = sec[6] if len(sec) > 6 else 0.0
    if abs(u) > 0.999 or abs(s) > 0.999:
        th = math.atan2(s, u)
        if amap:
            th = amap[akey(th)]
        c, sn = math.cos(th), math.sin(th)
        x = cx + rx * math.copysign(abs(c) ** (2 / n), c)
        return Vector((x, cy + ry * math.copysign(abs(sn) ** (2 / n), sn), z - tilt * (x - cx)))
    x = cx + u * rx * 0.85
    return Vector((x, cy + s * ry * 0.85, z - tilt * (x - cx)))


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

    th_, tv = (t1, t1) if not isinstance(t1, tuple) else t1

    def first(p0, ro):
        q = role_pos(secs[0], *ro)          # the transition ring keeps the window's own angles (no skew)
        return Vector((p0.x + (q.x - p0.x) * th_, p0.y + (q.y - p0.y) * th_, p0.z + (q.z - p0.z) * tv))
    faces, roles = step(faces, roles, first)
    for sec in secs:
        faces, roles = step(faces, roles, lambda p0, ro, sec=sec: rp(sec, *ro))
    return faces


def bridge_rows(bm, a, b):
    """Quads and triangles between two OPEN rows (top seam -> bottom seam) of different lengths, matched by their
    normalised index; a quad where both advance together, a triangle where one does (the shorter new edge wins:
    elephant s1 r12)."""
    na, nb = len(a) - 1, len(b) - 1
    i = j = 0
    out = []
    while i < na or j < nb:
        ta = (i + 1) / na if i < na else 9.0
        tq = (j + 1) / nb if j < nb else 9.0
        if abs(ta - tq) < 0.3 / max(na, nb):
            out.append(bm.faces.new([a[i], a[i + 1], b[j + 1], b[j]])); i += 1; j += 1
        elif j >= nb or (i < na and (a[i + 1].co - b[j].co).length <= (a[i].co - b[j + 1].co).length):
            out.append(bm.faces.new([a[i], a[i + 1], b[j]])); i += 1
        else:
            out.append(bm.faces.new([a[i], b[j + 1], b[j]])); j += 1
    return out


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) if len(rings[i]) == len(rings[i + 1]) else bridge_rows(bm, rings[i], rings[i + 1])
             for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    grow(bm, rings, spans, idx['B0'], LJ, 4, 3, HIND, T1_LEG)
    grow(bm, rings, spans, idx['F0'], LJ, 4, 3, FORE, T1_LEG)
    grow(bm, rings, spans, idx['H0'], EJ, 1, 2, EAR, T1_EAR)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.0, -1.04, 1.36))     # the eye point on the side view (y, z); x from a ray on the head side
SOCKET = []
NOSTRIL = []


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    hit, hn = tree.ray_cast(Vector((1.0, EYE.y, EYE.z)), Vector((-1, 0, 0)), 2.0)[:2]
    f = face_near(bm, hit, n=hn)
    # s2 r1: the eye bump: the skull round the eye face raised out and up (a soft 9 cm falloff), so the eye sits on a
    # mound above the skull top as on the sheet (front view: the eyes stand above the forehead)
    bump = (Vector(hn) * 0.55 + Vector((0, 0, 0.45))).normalized()
    for v in bm.verts:
        d = (v.co - hit).length
        if v.co.x > 0.05 and d < 0.09:
            v.co += bump * 0.03 * (1 - d / 0.09)
    f.normal_update()
    # s2 r2: the nostril mounds on the muzzle top front (sheet front/top: two raised nostrils at x 0.19)
    nh = tree.ray_cast(Vector((0.18, -1.52, 2.0)), Vector((0, 0, -1)), 3.0)[0]
    for v in bm.verts:
        d = (v.co - nh).length
        if v.co.x > 0.04 and d < 0.08:
            v.co += Vector((0.0, -0.3, 1.0)).normalized() * 0.022 * (1 - d / 0.08)
    NOSTRIL[:] = [nh + Vector((0.0, -0.007, 0.022))]
    # s2 r3: the neck collar (hero: a ridge ring round the neck behind the head): N0 re-placed as the straight
    # in-between of F4 and N1 (density rule 3.2), so the BODY -> NECK profile change is spread over two spans
    for a_, b_, c_ in zip(P('F4'), P('N0'), P('N1')):
        vert_near(bm, b_).co = (a_ + c_) / 2
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face on the skull top'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.006)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.05 and abs(c.y - ec0.y) < 0.05 and abs(c.z - ec0.z) < 0.05)
    commit(body, bm)


PAL = {'skin': '#7e7081', 'pink': '#b9888d', 'nail': '#cfc6bc', 'dark': '#40363b', 'eye': '#3b2a22',
       'muzzle': '#c4959a'}   # detail pass 10-23: the pink muzzle + inner ears a step lighter than the belly (sheet)

# s3 r1: colour borders on edge loops. fh = the face centre's height in its ring's frame (-1 bottom seam .. 1 top), from
# the loft stations by y: the belly border is the leg-window top loop (BODY j9), the jaw border HEAD j8, the muzzle
# border the H4 ring loop and its top-plane loop (MUZ j3)
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
    for y0, y1 in ((-0.58, 0.0), (0.92, 1.50)):
        if y0 < y < y1 and x > 0.09:
            zc, h = _frame(y)
            if z < zc + BODY[LJ][1] * h - 0.006:
                return True
    return False


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y > 1.685 and z < 0.81:
        return 'dark'                                   # tail tip
    if NOSTRIL and (Vector((x, y, z)) - NOSTRIL[0]).length < 0.03:
        return 'dark'                                   # nostril
    if _leg(c) or y > 1.60:
        return 'skin'                                   # legs, tail
    if z > 1.46 and x > 0.17 and -0.95 < y < -0.75 and n.y < -0.3:
        return 'muzzle'                                 # detail pass: the inner (front) face of the ear cup
    zc, h = _frame(y)
    fh = (z - zc) / h
    if y < -1.235:
        return 'muzzle' if fh < 0.86 or y < -1.585 else 'skin'    # muzzle box below its top plane, the front
    if y < -0.60:
        return 'pink' if fh < -0.45 else 'skin'         # jaw, throat
    if -0.60 < y < 0.96:
        return 'pink' if fh < -0.62 else 'skin'         # s4 r5: belly + chest on ONE loop (BODY j9 = the leg-window top)
    return 'skin'                                       # haunch and rump stay grey (sheet rear)


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


def nail(bm, base, out, w, hgt, d):
    """A toenail: an arched 6-sided section (flat sole edge, rounded top) swept out of the foot: a root ring sunk
    3 cm in, a mid ring and a blunt rounded tip; the sole edge 8 mm off the ground (no z-fight with the sole)."""
    out = Vector(out).normalized()
    side = out.cross(Vector((0, 0, 1))).normalized()
    up = Vector((0, 0, 1))
    SEC = [(-1, 0), (1, 0), (0.85, 0.6), (0.4, 1.0), (-0.4, 1.0), (-0.85, 0.6)]
    rows = []
    for off, sw, sh in ((-0.03, 1.0, 1.0), (d * 0.6, 0.95, 0.9), (d, 0.65, 0.55)):
        c = base + out * off + up * 0.008
        rows.append([bm.verts.new(c + side * su * w * sw / 2 + up * (sz * hgt * sh)) for su, sz in SEC])
    n = len(SEC)
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(n):
            bm.faces.new([a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]])
    bm.faces.new(rows[-1])


def stage3(k, body):
    paint(body, PAL, body_rule)
    # night 10-23 border pass (owner 10-21 approved kit/smooth_borders, as frog r17): anti-stair cuts + tangential relax
    smooth_borders(body, k=k, iters=8)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.2, 0.0))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.004, n, 0.033, 0.015)       # s4 r6: 66 mm (r4-r5: 58-60 mm sat on the 0.06-of-head floor)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'dark': '#141210'},
          lambda c_, n_, i: 'dark' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.015 and n_.dot(n) > 0.5 else 'eye')
    pieces.append(eye)
    bm = bmesh.new()
    for sec in (FORE[-2], HIND[-2]):
        cx, cy, z, rx, ry, nn = sec
        for ang in (-62, -82, -102, -122):
            th = math.radians(ang)
            d = Vector((math.cos(th), math.sin(th), 0.0))
            o = Vector((cx, cy, 0.03)) + d * 0.5
            hit = tree.ray_cast(o, -d, 1.0)[0]
            base = Vector((hit.x, hit.y, 0.0)) if hit is not None else Vector((cx, cy, 0.0)) + d * ry
            nail(bm, base - d * 0.004, d, 0.065, 0.06, 0.022)
    nails = object_from_bm('nails', bm)
    paint(nails, {'nail': PAL['nail']}, lambda c_, n_, i: 'nail')
    pieces.append(nails)
    return pieces + detail_pass(body, tree)


def detail_pass(body, tree):
    """Tier-3 detail pass (2026-10-23, zoo/detail_audit.md hippo list): nostril mounds, eye bumps, mouth line, a
    cheek bulge, a neck fold, wrist wrinkles, a tail brush; chunky blended seated pieces (STEP: raised ridges read
    as straps - rhino judge)."""
    import detail_pieces as D
    out = []

    def piece(name, bm, col, mirror=True, rule=None):
        ob = object_from_bm(name, bm, mirror=mirror)
        cols = col if isinstance(col, dict) else {col: PAL[col]}
        paint(ob, cols, rule or (lambda c_, n_, i: next(iter(cols))))
        out.append(ob)
        return ob
    # 1. nostril mounds: a raised dome round each painted nostril, a dark cap
    q = NOSTRIL[0]
    h_ = D.cast_in(tree, (q.x, q.y, q.z + 1.0), (0, 0, -1))
    nn = h_[1]
    bm = bmesh.new()
    D.knob(bm, h_[0], nn, 0.05, 0.026, sides=7, top=0.55)
    piece('nostril', bm, {'muzzle': PAL['muzzle'], 'dark': PAL['dark']},
          rule=lambda c_, n_, i: 'dark' if n_.dot(nn) > 0.9 else 'muzzle')
    # 2. eye bumps: the eyes sit on raised knobs on the skull top (a brow mound over each eye)
    e = SOCKET[0]
    h_ = D.cast_in(tree, (e.x - 0.03, e.y + 0.075, 3.0), (0, 0, -1))      # r10: behind + above the eye (r09 hid the lens)
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.055, 0.028, sides=8, sq=(0.9, 1.15), top=0.5)
    piece('brow', bm, 'skin')
    # 3. mouth line: a dark lip line from the muzzle front back to the cheek
    pts = [(1.5, y, z) for y, z in ((-1.57, 0.875), (-1.47, 0.855), (-1.37, 0.848), (-1.27, 0.852), (-1.18, 0.868),
                                    (-1.11, 0.895))]
    bm = bmesh.new()
    D.band(bm, D.stations_from_hits(D.path_stations(tree, pts, (-1, 0, 0)), side_hint=(0, 0, 1)), 0.036, 0.032,
           prof=D.ROUND, taper=0.7, sink=0.02)
    piece('mouth', bm, 'dark')
    # 4. cheek bulge at the mouth corner (side view)
    h_ = D.cast_in(tree, (1.5, -1.08, 0.86), (-1, 0, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.075, 0.03, sides=7, sq=(1.2, 1.0), top=0.55)
    piece('cheek', bm, 'muzzle')
    # 5. neck fold: a broad blended skin step on the side of the neck behind the jaw (side only, no collar)
    hits = []
    for i in range(7):
        t = i / 6
        sc = D.section_centre(tree, -0.70 + 0.05 * t)
        if sc is None:
            continue
        a = 55 + 80 * t
        hits += D.ring_stations(tree, sc[0], (0, 1, 0), (0, 0, 1), a, a + 1e-3, 2)[:1]
    bm = bmesh.new()
    D.band(bm, D.stations_from_hits(hits, side_hint=(0, 1, 0)), 0.18, 0.035, prof=D.STEP, taper=0.3)
    piece('fold_neck', bm, 'skin')
    # 6. wrist wrinkles: a short stepped arc on the front of each lower leg above the foot
    bm = bmesh.new()
    for sec in (FORE[3], HIND[3]):
        hits = D.ring_stations(tree, (sec[0], sec[1], 0.21), (0, 0, 1), (0, -1, 0), -65, 65, 6)
        D.band(bm, D.stations_from_hits(hits, side_hint=(0, 0, -1)), 0.065, 0.024, prof=D.STEP)
    piece('fold_leg', bm, 'skin')
    # 7. tail brush: a flat dark tuft at the tail tip
    bm = bmesh.new()
    D.fan(bm, (0.0, 1.708, 0.765), (0, 0.12, -1), (0, 1, 0), 0.10, 0.06, 0.032)
    piece('tuft', bm, 'dark', mirror=False)
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
         ('hand.L', J['wrist'], J['ftoe'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
         ('foot.L', J['hock'], J['hpaw'], 'shin.L', True),
         ('toe.L', J['hpaw'], J['htoe'], 'foot.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 8)},
                       20: {'ear.L': (0, 0, -12), 'head': (3, 0, 0)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -8)}, 48: {}})
    A = 10
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 5)},
        7: {'forearm.R': (-18, 0, 0), 'hand.R': (-12, 0, 0), 'shin.L': (-10, 0, 0), 'foot.L': (12, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -5)},
        19: {'forearm.L': (-18, 0, 0), 'hand.L': (-12, 0, 0), 'shin.R': (-10, 0, 0), 'foot.R': (12, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 5)}})
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (10, 0, 0), 'head': (8, 0, 0), 'chest': (-2, 0, 0), 'tail0': (10, 0, 0)},
        16: {'neck': (12, 0, 0), 'head': (10, 0, 0), 'upperarm.L': (8, 0, 0), 'upperarm.R': (8, 0, 0),
             'thigh.L': (-7, 0, 0), 'thigh.R': (-7, 0, 0)},
        20: {'neck': (-8, 0, 5), 'head': (-14, 0, 8), 'upperarm.L': (4, 0, 0), 'upperarm.R': (4, 0, 0)},
        24: {'neck': (-4, 0, 2), 'head': (-6, 0, 3)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.04, 0)}, 16: {'hips': (0, -0.08, 0)}, 20: {'hips': (0, -0.09, 0)},
             24: {'hips': (0, -0.04, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
