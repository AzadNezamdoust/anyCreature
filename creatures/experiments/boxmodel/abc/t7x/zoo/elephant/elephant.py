import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
import parts as PT

# t7 hand box model (zoo workflow v2), template zoo/rhino: one spine loft of 14-vertex half rings (tail tip -> rump ->
# barrel -> neck -> head -> trunk tip: the trunk is the face's loft carried on forward and down, its rings turning from
# upright to level), the thin tail a 6-vertex run joined to the rump by an uneven open-row bridge; column legs extruded
# from BROAD 4 x 3-face windows on the lower flank through a 45 %-inset transition ring; the fan ears extruded from a
# TALL 1 x 6-face window on the side of the skull (a broad root, not a stalk) as a thick slab that sweeps out and back.
META = dict(creature='elephant', model='opus', stage1_tris=(2200, 4600), total_tris=(2800, 6200),
            closeups=[('head', (0.0, -1.15, 2.25), 0.75, 'hero'),
                      ('ear root', (0.45, -0.80, 2.35), 0.55, 'back34'),
                      ('front foot', (0.40, -0.36, 0.25), 0.40, 'hero'),
                      ('hind foot', (0.40, 1.55, 0.25), 0.40, 'hero')])

# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png (height 3.0 m)
J = dict(
    hips=(0.0, 1.45, 1.85), spine=(0.0, 0.60, 1.90), chest=(0.0, -0.25, 1.95),
    neck=(0.0, -0.55, 2.10), skull=(0.0, -0.80, 2.30), skull2=(0.0, -0.95, 2.36), face=(0.0, -1.40, 2.25),
    tr0=(0.0, -1.47, 2.02), tr1=(0.0, -1.59, 1.45), tr2=(0.0, -1.61, 0.85), tr3=(0.0, -1.58, 0.35), tr4=(0.0, -1.48, 0.14),
    tail0=(0.0, 2.10, 1.83), tail1=(0.0, 2.16, 1.72), tail2=(0.0, 2.21, 1.10), tail3=(0.0, 2.21, 0.45),
    shoulder=(0.40, -0.30, 1.55), elbow=(0.40, -0.33, 0.95), wrist=(0.40, -0.36, 0.35),
    fpaw=(0.40, -0.36, 0.06), ftoe=(0.40, -0.62, 0.0),
    hipL=(0.40, 1.55, 1.65), knee=(0.40, 1.52, 0.95), hock=(0.40, 1.55, 0.35),
    hpaw=(0.40, 1.55, 0.06), htoe=(0.40, 1.30, 0.0),
    ear=(0.43, -0.86, 2.40), ear1=(0.88, -0.52, 2.34), eartip=(1.17, 0.22, 2.38),
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


# the barrel, hand placed (rhino's): j0-j2 a broad back plane, j2-j5 the shoulder bevel, j5-j8 the flank plane, j8-j12
# the lower-flank bevel the legs grow from (window j9-j12), j12-j13 the belly strip
BODY = [(0, 1), (0.32, 0.975), (0.60, 0.89), (0.80, 0.73), (0.92, 0.52), (0.985, 0.27), (1.0, 0.02),
        (0.975, -0.22), (0.92, -0.43), (0.83, -0.62), (0.66, -0.79), (0.44, -0.91), (0.20, -0.985), (0, -1)]
NECK = prof(2.6, 2.4, 0.8)
HEAD = prof(2.6, 2.3, 0.78)
TRUNK = prof(2.3, 2.1, 0.85)
TAIL = prof(2.2, 2.2, 0.85, nv=6)
LJ = 9                           # leg windows: ring vertices j9 (outer) .. j12 (inner), 3 faces round, 4 spans long
EJ, EB = 2, 6                    # ear windows: ring vertices j2 .. j8 on the side of the skull (6 faces), 1 span long


def tb(nm, top, bot, W, pr):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, pr)


def tc(nm, c, a, h, W, pr):
    """A section from its centre (y, z), its tilt a (deg; 0 = an upright ring, 90 = a level ring whose 'top' seam
    point is the rear, -90 = a level ring whose 'top' is the front: the hanging trunk) and its half height h."""
    return (nm, c, a, h, h, W, pr)


def mid(a, b, t, nm):
    """A straight in-between section of two stations (density rule 3.2: centre, tilt, sizes lerped, same profile)."""
    (_n, ca, aa, Ta, Ba, Wa, pa), (_m, cb, ab, Tb, Bb, Wb, pb) = a, b
    L = lambda u, v: u + (v - u) * t
    return (nm, (L(ca[0], cb[0]), L(ca[1], cb[1])), L(aa, ab), L(Ta, Tb), L(Ba, Bb), L(Wa, Wb), pa)


def densify(secs, pairs):
    """Insert n straight in-between rings after each named station (s1 r10: the thin tail's faces under 3:1)."""
    out = []
    for i, s_ in enumerate(secs):
        out.append(s_)
        n = pairs.get(s_[0], 0)
        for k_ in range(1, n + 1):
            out.append(mid(s_, secs[i + 1], k_ / (n + 1), f'{s_[0]}_{k_}'))
    return out


SECS = [
    # the tail, tip -> root: hanging off the rump's upper back, a dark tuft at the end (6-vertex rings)
    tc('T0', (2.21, 0.46), 90, 0.022, 0.024, TAIL),
    tc('T1', (2.21, 0.60), 90, 0.066, 0.068, TAIL),      # the dark tuft
    tc('T2', (2.21, 0.74), 90, 0.046, 0.048, TAIL),
    tc('T3', (2.21, 0.86), 90, 0.042, 0.045, TAIL),
    tc('T4', (2.21, 1.03), 89, 0.045, 0.047, TAIL),
    tc('T5', (2.205, 1.28), 86, 0.05, 0.054, TAIL),
    tc('T6', (2.19, 1.53), 75, 0.058, 0.063, TAIL),
    tc('T7', (2.15, 1.73), 50, 0.07, 0.078, TAIL),
    # s1 r11: T3-Rt x 1.35 (the sheet's tail thickness)
    # the tail root ring (6-vertex, broad) and the rump dome
    tc('Rt', (2.10, 1.83), 25, 0.101, 0.115, TAIL),
    tb('R0', (2.065, 1.94), (2.08, 1.62), 0.26, BODY),
    tb('R1', (2.02, 2.02), (2.04, 1.40), 0.48, BODY),
    tb('R2', (1.95, 2.13), (1.97, 1.25), 0.64, BODY),
    # hind-leg window rings (rear -> front)
    tb('B0', (1.89, 2.22), (1.89, 1.15), 0.72, BODY),
    tb('B1', (1.72, 2.37), (1.72, 1.08), 0.77, BODY),
    tb('B2', (1.55, 2.47), (1.55, 1.03), 0.80, BODY),
    tb('B3', (1.38, 2.52), (1.38, 1.00), 0.81, BODY),
    tb('B4', (1.21, 2.54), (1.21, 0.98), 0.82, BODY),
    # the barrel
    tb('M0', (1.00, 2.55), (1.00, 0.96), 0.82, BODY),
    tb('M1', (0.80, 2.57), (0.80, 0.95), 0.82, BODY),
    tb('M2', (0.60, 2.59), (0.60, 0.96), 0.82, BODY),
    tb('M3', (0.40, 2.60), (0.40, 1.00), 0.82, BODY),
    tb('M4', (0.20, 2.61), (0.20, 1.03), 0.82, BODY),
    # fore-leg window rings (rear -> front)
    tb('F0', (0.02, 2.62), (0.02, 1.05), 0.81, BODY),
    tb('F1', (-0.14, 2.63), (-0.14, 1.06), 0.80, BODY),
    tb('F2', (-0.30, 2.64), (-0.30, 1.08), 0.78, BODY),
    tb('F3', (-0.44, 2.66), (-0.46, 1.12), 0.75, BODY),
    tb('F4', (-0.54, 2.68), (-0.62, 1.20), 0.70, BODY),
    # neck: short and thick, hidden behind the ears
    tb('N0', (-0.62, 2.71), (-0.77, 1.48), 0.57, NECK),       # s1 r9: no wider than the skull behind the ear
    tb('N1', (-0.70, 2.76), (-0.86, 1.62), 0.48, NECK),
    # head: a tall dome, the ear window H0-H1 on its side, the eye on H3, the face front H4
    tb('H0', (-0.78, 2.82), (-0.93, 1.70), 0.47, HEAD),
    tb('H1', (-0.95, 2.86), (-1.03, 1.74), 0.45, HEAD),
    tb('H2', (-1.11, 2.84), (-1.15, 1.73), 0.43, HEAD),
    tb('H3', (-1.25, 2.73), (-1.26, 1.72), 0.40, HEAD),
    tb('H4', (-1.38, 2.56), (-1.32, 1.74), 0.35, HEAD),
    # the trunk: the face's loft carried forward and down, rings turning from upright to level, a small curl at the tip
    tc('K0', (-1.48, 2.03), -22, 0.32, 0.29, TRUNK),
    tc('K1', (-1.56, 1.79), -48, 0.245, 0.235, TRUNK),
    tc('K2', (-1.585, 1.52), -74, 0.205, 0.205, TRUNK),
    tc('K3', (-1.595, 1.22), -88, 0.180, 0.185, TRUNK),
    tc('K4', (-1.595, 0.92), -91, 0.165, 0.165, TRUNK),
    tc('K5', (-1.59, 0.64), -92, 0.150, 0.148, TRUNK),
    tc('K6', (-1.58, 0.42), -95, 0.138, 0.135, TRUNK),
    tc('K7', (-1.565, 0.26), -105, 0.125, 0.122, TRUNK),
    tc('K8', (-1.53, 0.18), -125, 0.105, 0.108, TRUNK),
    tc('K9', (-1.47, 0.15), -150, 0.075, 0.082, TRUNK),
]
SECS = densify(SECS, {'T4': 2, 'T5': 2, 'T6': 1, 'T7': 1})

# leg sections: (cx, cy, z, rx, ry, exponent): level rounded boxes, round columns; secs[0] is the target the
# transition ring slopes toward (it sits at T1 of the way from the window rim)
FORE = [(0.40, -0.32, 0.86, 0.250, 0.300, 2.4),   # upper arm under the chest (s1 r5 deeper; r7 6 cm rear margin)
        (0.40, -0.33, 0.70, 0.238, 0.280, 2.4),
        (0.40, -0.34, 0.52, 0.226, 0.255, 2.4),   # knee (wrist)
        (0.40, -0.36, 0.34, 0.220, 0.245, 2.4),
        (0.40, -0.36, 0.18, 0.228, 0.255, 2.4),
        (0.40, -0.365, 0.07, 0.250, 0.280, 2.3),  # the round foot flaring
        (0.40, -0.37, 0.0, 0.256, 0.286, 2.3)]
HIND = [(0.40, 1.55, 0.88, 0.255, 0.335, 2.4),    # thigh under the haunch (s1 r5: deeper, broad into the haunch)
        (0.40, 1.53, 0.72, 0.240, 0.295, 2.4),
        (0.40, 1.53, 0.54, 0.228, 0.258, 2.4),    # stifle/gaskin
        (0.40, 1.55, 0.35, 0.220, 0.245, 2.4),    # hock
        (0.40, 1.55, 0.18, 0.226, 0.252, 2.4),
        (0.40, 1.55, 0.07, 0.248, 0.276, 2.3),
        (0.40, 1.55, 0.0, 0.254, 0.282, 2.3)]
T1_LEG = 0.45

# ear stations: (x, y, zc, Ht, Hb, t, gx, gy, cup, lean): centre, half heights above/below, half thickness, growth
# direction (the slab's long axis in plan), the cup (front face hollowed back by this much at mid height) and the lean
# (the top rim tipped out along the front normal: the ear shows as a lobe from above)
EAR = [(0.66, -0.88, 2.37, 0.51, 0.51, 0.05, 0.95, 0.31, 0.0, 0.0),
       (0.88, -0.70, 2.32, 0.66, 0.66, 0.036, 0.74, 0.67, 0.03, 0.0),
       (1.02, -0.4, 2.36, 0.56, 0.56, 0.032, 0.55, 0.83, 0.045, 0.0),
       (1.15, -0.16, 2.375, 0.375, 0.375, 0.03, 0.38, 0.92, 0.04, 0.0),
       (1.24, 0.06, 2.37, 0.23, 0.23, 0.028, 0.22, 0.97, 0.025, 0.0),
       (1.28, 0.22, 2.36, 0.1, 0.1, 0.026, 0.1, 0.99, 0.01, 0.0)]
T1_EAR = 0.45


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


def _step(bm, faces, roles, place):
    r = extrude(bm, faces)
    new = []
    for v in r['verts']:
        o = min(roles, key=lambda o_: (o_[0] - v.co).length)
        new.append((v, o))
    for v, (p0, ro) in new:
        v.co = place(p0, ro)
    return r['faces'], [(v.co.copy(), ro) for v, (p0, ro) in new]


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

    def first(p0, ro):
        q = role_pos(secs[0], *ro)
        return p0 + (q - p0) * t1
    faces, roles = _step(bm, faces, roles, first)
    for sec in secs:
        faces, roles = _step(bm, faces, roles, lambda p0, ro, sec=sec: rp(sec, *ro))
    return faces


def ear_pos(st, b, s, B=EB):
    """A vertex of an ear station: b along the height (0 = top rim), s = +1 the front face, -1 the back face."""
    x, y, zc, Ht, Hb, t, gx, gy, cup, lean = st
    v = 1 - 2 * b / B
    z = zc + v * (Ht if v >= 0 else Hb)
    g = Vector((gx, gy, 0)).normalized()
    n = Vector((g.y, -g.x, 0))                   # front-out normal of the slab
    k = 0.9 + 0.1 * math.sqrt(max(0.0, 1 - v * v))          # s1 r13: a square-ish rim (was 0.6 + 0.4: thin rim strips)
    return Vector((x, y, z)) + n * (s * t * k - cup * (1 - v * v) + lean * max(v, 0.0) ** 1.5)


def grow_ear(bm, rings, spans, i0, j0, B, stations, t1):
    """The fan ear: extrude the 1 x B window (rings i0, i0+1; ring vertices j0..j0+B) as a slab. The first ring is
    the 45 %-inset transition toward stations[0]; then one ring per station, the slab sweeping out and back."""
    faces = [spans[i0][j0 + b] for b in range(B)]
    G = [[rings[i0 + a][j0 + b] for b in range(B + 1)] for a in range(2)]
    front = 0 if G[0][B // 2].co.y < G[1][B // 2].co.y else 1
    roles = [(G[a][b].co.copy(), (b, 1 if a == front else -1)) for a in range(2) for b in range(B + 1)]
    faces, roles = _step(bm, faces, roles, lambda p0, ro: p0 + (ear_pos(stations[0], *ro) - p0) * t1)
    for st in stations:
        faces, roles = _step(bm, faces, roles, lambda p0, ro, st=st: ear_pos(st, *ro))
    return faces


def bridge_rows(bm, a, b):
    """Quads and triangles between two OPEN rows (top seam -> bottom seam) of different lengths, matched by their
    normalised index; a quad where both advance together, a triangle where one does."""
    na, nb = len(a) - 1, len(b) - 1
    i = j = 0
    out = []
    while i < na or j < nb:
        ta = (i + 1) / na if i < na else 9.0
        tq = (j + 1) / nb if j < nb else 9.0
        if abs(ta - tq) < 0.3 / max(na, nb):
            out.append(bm.faces.new([a[i], a[i + 1], b[j + 1], b[j]])); i += 1; j += 1
        elif j >= nb or (i < na and (a[i + 1].co - b[j].co).length <= (a[i].co - b[j + 1].co).length):
            out.append(bm.faces.new([a[i], a[i + 1], b[j]])); i += 1   # s1 r12: the shorter new edge wins
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
    grow_ear(bm, rings, spans, idx['H0'], EJ, EB, EAR, T1_EAR)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.0, -1.27, 2.32))     # the eye point on the side view (y, z); x from a ray on the head side
SOCKET = []


def _sc(q, j, sx, sh):
    """Where stage 2 r1 put vertex j of a ring (scaled about its seam centre)."""
    c = (q[0] + q[-1]) / 2
    d = q[j] - c
    return Vector((q[j].x * sx, c.y + d.y * sh, c.z + d.z * sh))


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    hit = tree.ray_cast(Vector((2.0, EYE.y, EYE.z)), Vector((-1, 0, 0)), 3.0)[0]
    f = face_near(bm, hit, n=(1, 0, 0))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face, under the brow'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.012)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.08 and abs(c.y - ec0.y) < 0.08 and abs(c.z - ec0.z) < 0.08)
    # s2 r1: the tail-root fan (crops j4: creases radiating over the rump): R0 pulled toward the tail root, Rt widened,
    # so the 14 -> 6 bridge is 1.4:1 instead of 2.3:1
    r0 = [s_ for s_ in SECS if s_[0] == 'R0'][0]
    R0N = sec_pts(r0[1], r0[2], r0[3] * 0.84, r0[4] * 0.84, r0[5] * 0.77, prof(2.2, 2.2, 0.9))   # s2 r6: even angles
    for p, t_ in zip(P('R0'), R0N):
        vert_near(bm, p).co = Vector(t_)
    q = P('Rt')
    c = (q[0] + q[-1]) / 2
    for v, p in zip([vert_near(bm, p) for p in q], q):
        d = p - c
        v.co = Vector((p.x * 1.22, c.y + d.y * 1.19, c.z + d.z * 1.19))
    # s2 r3: the notch under the tail root: Rt's bottom (j4, j5) back and down, R0's bottom (j12, j13) up
    for j in (4, 5):
        move([vert_near(bm, _sc(P("Rt"), j, 1.22, 1.19))], (0.0, 0.01, -0.012))   # s2 r4: 3 cm back crossed T7_1
    for j in (12, 13):
        move([vert_near(bm, Vector(R0N[j]))], (0.0, 0.0, 0.025))
    commit(body, bm)


PAL = {'skin': '#8e8073', 'pale': '#a08f81',   # s4 r17: sheet's warm grey (EEVEE read light)
       'dark': '#4b4642', 'ivory': '#ece2cf', 'eye': '#3a2a1e', 'inner': '#a39488'}   # detail pass r19: the ear face a step lighter (sheet; r18 pink was not on the sheet)


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y > 2.15 and z < 0.82:
        return 'dark'                                   # tail tuft
    if z < 0.22 and x > 0.10 and y > -1.3:
        return 'pale'                                   # the feet, lighter (sheet)
    if x > 0.55 and z > 2.0 and n.y < -0.35:
        return 'inner'                                  # detail pass 10-23: the inner (front) face of the ear
    return 'skin'


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
    3 cm in, a mid ring and a blunt rounded tip; the sole edge 1 cm off the ground (no z-fight with the sole)."""
    out = Vector(out).normalized()
    side = out.cross(Vector((0, 0, 1))).normalized()
    up = Vector((0, 0, 1))
    SEC = [(-1, 0), (1, 0), (0.85, 0.6), (0.4, 1.0), (-0.4, 1.0), (-0.85, 0.6)]
    rows = []
    for off, sw, sh in ((-0.04, 1.0, 1.0), (d * 0.6, 0.95, 0.9), (d, 0.65, 0.55)):
        c = base + out * off + up * 0.01
        rows.append([bm.verts.new(c + side * su * w * sw / 2 + up * (sz * hgt * sh)) for su, sz in SEC])
    n = len(SEC)
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(n):
            bm.faces.new([a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]])
    bm.faces.new(rows[-1])


def stage3(k, body):
    paint(body, PAL, body_rule)
    from smooth_borders import smooth_borders
    smooth_borders(body, k=k)                    # owner 10-21: borders follow the form (the new inner-ear border)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []
    # eye: a small round lens in the socket, a dark pupil disc
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.3, 0.05))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.006, n, 0.042, 0.02)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'dark': '#141210'},
          lambda c_, n_, i: 'dark' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.02 and n_.dot(n) > 0.5 else 'eye')
    pieces.append(eye)
    # tusks: library horn, out of the trunk base's sides, forward-down then curving up (one per side)
    for sd in (1, -1):
        t = PT.horn((0.21 * sd, -1.40, 1.82), length=1.05, radius=0.092, taper=2.0, forward=(0.10 * sd, -0.72, -0.68),
                    up=(0.0, -0.3, 1.0), side=sd, curve=48, segs=5, sides=8,   # s3 r2: thick, blunt, curving up tip_from=1.0,
                    name='tusk_L' if sd > 0 else 'tusk_R', mats={'horn': 'ivory', 'horn_tip': 'ivory'},
                    colours={'horn': PAL['ivory'], 'horn_tip': PAL['ivory']})
        pieces.append(t)
    # toenails: three per foot round the front of the foot
    bm = bmesh.new()
    for sec in (FORE[-2], HIND[-2]):
        cx, cy, z, rx, ry, nn = sec
        for ang in (-90, -128, -52):
            th = math.radians(ang)
            d = Vector((math.cos(th), math.sin(th), 0.0))
            o = Vector((cx, cy, 0.04)) + d * 0.8
            hit = tree.ray_cast(o, -d, 1.5)[0]
            base = Vector((hit.x, hit.y, 0.0)) if hit is not None else Vector((cx, cy, 0.0)) + d * ry
            nail(bm, base - d * 0.006, d, 0.10, 0.085, 0.03)
    nails = object_from_bm('nails', bm)
    paint(nails, {'ivory': PAL['ivory']}, lambda c_, n_, i: 'ivory')
    pieces.append(nails)
    return pieces + detail_pass(body, tree)


def detail_pass(body, tree):
    """Tier-3 detail pass (2026-10-23, zoo/detail_audit.md elephant list): trunk rings, knee folds, brow, tail
    brush, a side fold; chunky blended seated pieces (STEP profile: raised ridges read as straps - rhino judge)."""
    import detail_pieces as D
    out = []

    def piece(name, bm, col, mirror=True, rule=None):
        ob = object_from_bm(name, bm, mirror=mirror)
        cols = col if isinstance(col, dict) else {col: PAL[col]}
        paint(ob, cols, rule or (lambda c_, n_, i: next(iter(cols))))
        out.append(ob)
        return ob
    # 1. trunk rings: 5 stepped wrinkle arcs round the front and sides of the trunk (open behind)
    bm = bmesh.new()
    A, B = Vector(J['tr1']), Vector(J['tr3'])
    for t in (0.08, 0.28, 0.48, 0.68, 0.88):
        c = A.lerp(B, t)
        ax = (B - A).normalized()
        side = 1 if ax.cross(Vector((0, -1, 0))).x > 0 else -1          # the angle sign that turns toward +x
        hits = D.ring_stations(tree, c, ax, (0, -1, 0), 0, side * 100, 5)
        if len(hits) >= 3:
            D.band(bm, D.stations_from_hits(hits, side_hint=(0, 0, -1)), 0.06, 0.022, prof=D.STEP, open_start=True)
    piece('fold_trunk', bm, 'skin')
    # 2. lower lip: the lip mound under the trunk root, behind the tusk (sheet side view; r18 knee arcs read as cuffs)
    h_ = None
    for y, z in ((-1.30, 1.72), (-1.26, 1.80), (-1.22, 1.88), (-1.18, 1.95)):
        h_ = h_ or D.cast_in(tree, (1.5, y, z), (-1, 0, 0))
    bm = bmesh.new()
    if h_ is not None:
        D.knob(bm, h_[0], h_[1], 0.07, 0.035, sides=8, sq=(0.8, 1.3), top=0.5)
        piece('lip', bm, 'skin')
    # 3. brow ridge over each eye
    e = SOCKET[0]
    pts = [(1.5, e.y + 0.07 * t, e.z + 0.075 - 0.02 * t * t) for t in (-1.0, -0.5, 0.0, 0.5, 1.0)]
    bm = bmesh.new()
    D.band(bm, D.stations_from_hits(D.path_stations(tree, pts, (-1, 0, 0)), side_hint=(0, 0, 1)), 0.07, 0.032,
           prof=D.ROUND)
    piece('brow', bm, 'skin')
    # 4. tail brush: a flat dark tuft at the tail tip (sheet)
    bm = bmesh.new()
    tp = Vector(J['tail3'])
    D.fan(bm, tp + Vector((0, 0, 0.14)), (0, 0.04, -1), (0, 1, 0), 0.24, 0.10, 0.05)
    piece('tuft', bm, 'dark', mirror=False)
    # 5. shoulder fold: a broad blended skin step on the side behind the ear, down toward the elbow
    hits = []
    for i in range(8):
        t = i / 7
        y = 0.05 + 0.12 * t
        sc = D.section_centre(tree, y)
        if sc is None:
            continue
        a = 45 + 70 * t
        hits += D.ring_stations(tree, sc[0], (0, 1, 0), (0, 0, 1), a, a + 1e-3, 2)[:1]
    bm = bmesh.new()
    D.band(bm, D.stations_from_hits(hits, side_hint=(0, 1, 0)), 0.24, 0.045, prof=D.STEP, taper=0.3)
    piece('fold_shoulder', bm, 'skin')
    return out


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['skull'], 'chest', True),
         ('skull', J['skull'], J['skull2'], 'neck', True),
         ('head', J['skull2'], J['face'], 'skull', True),
         ('trunk0', J['tr0'], J['tr1'], 'skull'),
         ('trunk1', J['tr1'], J['tr2'], 'trunk0', True),
         ('trunk2', J['tr2'], J['tr3'], 'trunk1', True),
         ('trunk3', J['tr3'], J['tr4'], 'trunk2', True),
         ('ear.L', J['ear'], J['ear1'], 'skull'),
         ('earTip.L', J['ear1'], J['eartip'], 'ear.L', True),
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
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.0, 0, 0), 'skull': (-2, 0, 0), 'trunk1': (4, 0, 0), 'trunk2': (6, 0, 0), 'tail1': (0, 0, 6)},
                       20: {'ear.L': (0, 0, 8), 'earTip.L': (0, 0, 6), 'trunk2': (3, 0, 0)}, 24: {'tail1': (0, 0, 0)},
                       30: {'ear.L': (0, 0, -6)},
                       36: {'chest': (1.0, 0, 0), 'skull': (-2, 0, 0), 'trunk1': (-3, 0, 0), 'trunk2': (-5, 0, 0), 'tail1': (0, 0, -6)},
                       48: {}})
    A = 10
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 5),
            'trunk1': (5, 0, 0)},
        7: {'forearm.R': (-18, 0, 0), 'hand.R': (-12, 0, 0), 'shin.L': (-10, 0, 0), 'foot.L': (12, 0, 0), 'skull': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -5),
             'trunk1': (-5, 0, 0)},
        19: {'forearm.L': (-18, 0, 0), 'hand.L': (-12, 0, 0), 'shin.R': (-10, 0, 0), 'foot.R': (12, 0, 0), 'skull': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 5),
             'trunk1': (5, 0, 0)}})
    clip(rig, 'attack', {          # s4 r16: +X raises the trunk forward (roll='auto'); r15's minus curled it into the tusks
        1: {},
        10: {'skull': (-10, 0, 0), 'trunk0': (12, 0, 0), 'trunk1': (22, 0, 0), 'trunk2': (18, 0, 0), 'ear.L': (0, 0, 18),
             'earTip.L': (0, 0, 10), 'upperarm.L': (-8, 0, 0), 'upperarm.R': (-8, 0, 0)},
        18: {'skull': (-14, 0, 0), 'trunk0': (16, 0, 0), 'trunk1': (28, 0, 0), 'trunk2': (22, 0, 0), 'ear.L': (0, 0, 22),
             'earTip.L': (0, 0, 12)},
        24: {'skull': (6, 0, 0), 'trunk0': (-6, 0, 0), 'trunk1': (-8, 0, 0), 'ear.L': (0, 0, 8)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 10: {'hips': (0, 0.06, 0)}, 18: {'hips': (0, 0.04, 0)}, 24: {'hips': (0, -0.08, 0)},
             32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
