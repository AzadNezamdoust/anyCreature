import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
import parts as PT

# t7 hand box model (zoo workflow v2): one spine loft of 14-vertex half rings (tail tip -> snout front), the thin tail
# a 6-vertex run joined to the rump by an uneven open-row bridge; legs extruded from BROAD 4 x 3-face windows on the
# lower flank (14-sided legs) through a transition ring that slopes from the window rim down into the leg, so the leg
# rises out of the flank in two folds instead of one knife fold; ears from 2-face windows on the flat skull top.
META = dict(creature='rhino', model='opus', stage1_tris=(1800, 3600), total_tris=(2600, 5800),
            later={'horn': dict(chain=['horn0', 'horn1'], radius=0.07), 'horn2': dict(chain=['horn2', 'horn3'], radius=0.05)},
            closeups=[('head', (0.0, -1.12, 1.15), 0.42, 'hero'),
                      ('front foot', (0.24, -0.27, 0.12), 0.2, 'hero'),
                      ('hind foot', (0.245, 1.04, 0.12), 0.2, 'hero'),
                      ('horn', (0.0, -1.33, 1.35), 0.25, 'az090')])

# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png
J = dict(
    hips=(0.0, 0.95, 1.10), spine=(0.0, 0.35, 1.10), chest=(0.0, -0.25, 1.15),
    neck=(0.0, -0.58, 1.22), head=(0.0, -0.80, 1.22), nose=(0.0, -1.40, 0.98),
    tail0=(0.0, 1.35, 0.99), tail1=(0.0, 1.41, 0.93), tail2=(0.0, 1.435, 0.78), tail3=(0.0, 1.445, 0.60),
    shoulder=(0.27, -0.25, 0.80), elbow=(0.255, -0.245, 0.42), wrist=(0.24, -0.255, 0.17),
    fpaw=(0.24, -0.265, 0.04), ftoe=(0.24, -0.43, 0.0),
    hipL=(0.27, 0.99, 0.86), knee=(0.26, 1.02, 0.45), hock=(0.245, 1.045, 0.19),
    hpaw=(0.245, 1.04, 0.04), htoe=(0.245, 0.87, 0.0),
    ear=(0.19, -0.84, 1.47), eartip=(0.28, -0.86, 1.70),
    horn0=(0.0, -1.33, 1.17), horn1=(0.0, -1.37, 1.50), horn2=(0.0, -1.10, 1.25), horn3=(0.0, -1.12, 1.39),
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


# the barrel, hand placed: j0-j2 a broad back plane, j2-j5 the shoulder bevel, j5-j8 the flank plane, j8-j12 the
# lower-flank bevel the legs grow from (window j9-j12), j12-j13 the narrow keel/belly strip
BODY = [(0, 1), (0.32, 0.975), (0.60, 0.89), (0.80, 0.73), (0.92, 0.52), (0.985, 0.27), (1.0, 0.02),
        (0.975, -0.22), (0.92, -0.43), (0.83, -0.62), (0.66, -0.79), (0.44, -0.91), (0.20, -0.985), (0, -1)]
NECK = prof(2.6, 2.4, 0.8)
HEAD = prof(2.8, 2.3, 0.72)
MUZ = prof(3.0, 2.6, 0.82)
TAIL = prof(2.2, 2.2, 0.85, nv=6)
LJ = 9                           # leg windows: ring vertices j9 (outer) .. j12 (inner), 3 faces round, 4 spans long
EJ = 1                           # ear windows: j1 .. j4 on the skull top (3 faces), 1 span long


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
    # the tail, tip -> root: a hook out of the rump top, then hanging (6-vertex rings)
    tc('T0', (1.445, 0.60), 90, 0.016, 0.018, TAIL),
    tc('T1', (1.445, 0.67), 88, 0.034, 0.042, TAIL),      # the dark tuft
    tc('T2', (1.435, 0.775), 87, 0.022, 0.026, TAIL),
    tc('T3', (1.425, 0.875), 75, 0.026, 0.030, TAIL),
    tc('T4', (1.405, 0.945), 50, 0.032, 0.040, TAIL),
    tc('T5', (1.38, 0.975), 25, 0.040, 0.050, TAIL),
    # the tail root ring (s1 r7: 6-vertex and broad, the 14 -> 6 bridge moved to R0 -> Rt) and the rump dome
    tc('Rt', (1.352, 0.985), 12, 0.062, 0.080, TAIL),
    tb('R0', (1.33, 1.08), (1.32, 0.86), 0.16, BODY),
    tb('R1', (1.305, 1.16), (1.29, 0.72), 0.30, BODY),
    # hind-leg window rings (rear -> front)
    tb('B0', (1.25, 1.235), (1.245, 0.645), 0.41, BODY),
    tb('B1', (1.12, 1.35), (1.12, 0.62), 0.47, BODY),
    tb('B2', (0.99, 1.43), (0.99, 0.61), 0.51, BODY),
    tb('B3', (0.86, 1.48), (0.86, 0.60), 0.53, BODY),
    tb('B4', (0.73, 1.50), (0.73, 0.565), 0.53, BODY),
    # the barrel
    tb('M0', (0.61, 1.50), (0.61, 0.525), 0.515, BODY),
    tb('M1', (0.49, 1.50), (0.49, 0.495), 0.50, BODY),
    tb('M2', (0.37, 1.495), (0.37, 0.49), 0.50, BODY),
    tb('M3', (0.25, 1.495), (0.25, 0.50), 0.505, BODY),
    tb('M4', (0.13, 1.505), (0.13, 0.52), 0.51, BODY),
    # fore-leg window rings (rear -> front), the hump over them
    tb('F0', (0.01, 1.545), (0.01, 0.545), 0.525, BODY),
    tb('F1', (-0.12, 1.625), (-0.12, 0.54), 0.55, BODY),
    tb('F2', (-0.25, 1.685), (-0.25, 0.54), 0.56, BODY),
    tb('F3', (-0.38, 1.69), (-0.38, 0.565), 0.55, BODY),
    tb('F4', (-0.51, 1.65), (-0.51, 0.63), 0.50, BODY),
    # neck: short and thick, the head hung low
    tb('N0', (-0.60, 1.60), (-0.63, 0.76), 0.43, NECK),
    tb('N1', (-0.70, 1.515), (-0.73, 0.845), 0.36, NECK),   # s1 r9: lower, a level plateau behind the ears
    # head: skull, eye, horns, square muzzle
    tb('H0', (-0.765, 1.505), (-0.79, 0.84), 0.315, HEAD),   # s1 r13: H0/H1 spread: a 0.16 m ear window
    tb('H1', (-0.925, 1.40), (-0.94, 0.795), 0.27, HEAD),
    tb('H2', (-1.02, 1.32), (-1.03, 0.77), 0.245, HEAD),
    tb('H3', (-1.14, 1.245), (-1.14, 0.745), 0.22, MUZ),
    tb('H4', (-1.26, 1.20), (-1.25, 0.75), 0.20, MUZ),
    tb('H5', (-1.36, 1.17), (-1.33, 0.79), 0.175, MUZ),
    tb('H6', (-1.415, 1.13), (-1.385, 0.855), 0.14, MUZ),
    tb('H7', (-1.445, 1.085), (-1.425, 0.915), 0.085, MUZ),   # s1 r2: the muzzle rounds off into a small front cap
]

# leg sections: (cx, cy, z, rx, ry, exponent): level rounded boxes, deeper front-to-back; secs[0] is the target the
# transition ring slopes toward (it sits at T1 of the way from the window rim)
FORE = [(0.255, -0.25, 0.44, 0.150, 0.190, 2.6),   # upper arm / elbow mass under the chest
        (0.250, -0.245, 0.34, 0.140, 0.175, 2.6),  # forearm
        (0.245, -0.25, 0.25, 0.130, 0.155, 2.6),
        (0.240, -0.255, 0.17, 0.122, 0.145, 2.6),  # wrist, the narrowest
        (0.240, -0.26, 0.10, 0.130, 0.150, 2.6),
        (0.240, -0.265, 0.045, 0.148, 0.170, 2.4),  # the round foot flaring
        (0.240, -0.27, 0.0, 0.152, 0.175, 2.4)]
HIND = [(0.260, 1.00, 0.46, 0.155, 0.200, 2.6),    # stifle / thigh under the haunch
        (0.255, 1.02, 0.35, 0.145, 0.180, 2.6),    # gaskin
        (0.250, 1.035, 0.26, 0.130, 0.158, 2.6),
        (0.245, 1.045, 0.18, 0.122, 0.146, 2.6),   # hock
        (0.245, 1.045, 0.10, 0.130, 0.150, 2.6),
        (0.245, 1.04, 0.045, 0.148, 0.170, 2.4),
        (0.245, 1.035, 0.0, 0.152, 0.175, 2.4)]
EAR = [(0.200, -0.846, 1.515, 0.064, 0.046, 2.4, 0.55),   # cup ears from a 3-face window, wide across, leaning out;
       (0.250, -0.856, 1.615, 0.088, 0.048, 2.2, 0.35),   # s1 r14: the root rings tipped with the skull's side slope
       (0.295, -0.862, 1.705, 0.072, 0.036, 2.2, 0.15),   # (0.64), so the ear rises square off it; a rounded leaf tip
       (0.318, -0.866, 1.750, 0.034, 0.018, 2.0)]
T1_LEG, T1_EAR = 0.45, (0.7, 0.2)   # s1 r8: the ear transition ring slides in more than it rises (a flared root)


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
    tilt = sec[6] if len(sec) > 6 else 0.0      # s1 r14: z drops tilt x (x - cx): a ring tipped with the sloping skull
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
    # s1 r10: the boundary roles at EVEN angles round the section (the grid's own angles bunch at the window corners
    # and leave thin faces down the ear and leg edges: the seam strips)
    th = sorted({akey(math.atan2(s_, u_)) for _p, (u_, s_) in roles if abs(u_) > 0.999 or abs(s_) > 0.999})
    N = len(th)
    off = 0.0 if any(abs(t) < 1e-6 for t in th) else math.pi / N
    th = sorted(th)
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

    th, tv = (t1, t1) if not isinstance(t1, tuple) else t1

    def first(p0, ro):
        q = role_pos(secs[0], *ro)          # s1 r11: the transition ring keeps the window's own angles (no skew)
        return Vector((p0.x + (q.x - p0.x) * th, p0.y + (q.y - p0.y) * th, p0.z + (q.z - p0.z) * tv))
    faces, roles = step(faces, roles, first)
    for sec in secs:
        faces, roles = step(faces, roles, lambda p0, ro, sec=sec: rp(sec, *ro))
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
        elif ta < tq:
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
    grow(bm, rings, spans, idx['H0'], EJ, 1, 3, EAR, T1_EAR)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.0, -0.955, 1.10))     # the eye point on the side view (y, z); x from a ray on the head side
SOCKET = []


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    hit = tree.ray_cast(Vector((1.0, EYE.y, EYE.z)), Vector((-1, 0, 0)), 2.0)[0]
    f = face_near(bm, hit, n=(1, 0, 0))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face, under the brow'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.006)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.05 and abs(c.y - ec0.y) < 0.05 and abs(c.z - ec0.z) < 0.05)
    # s2 r4: the ear root re-placed in the WINDOW's own frame (r1-r3 scaled level rings and kept folding): the transition
    # ring is the window rim pulled 30 % toward its centre and lifted 2 cm along the window normal (a flared foot), E1 the
    # rim pulled 42 % in and lifted 7.5 cm. Both follow the skull's sideways and forward slope, so every root wall leaves
    # the skull at ~45 deg and then turns up into the cup.
    box = lambda c: c.x > 0.09 and -0.94 < c.y < -0.75 and c.z > 1.25
    rim = [v for v in bm.verts if box(v.co) and (abs(v.co.y + 0.767) < 0.006 or abs(v.co.y + 0.926) < 0.006)
           and v.co.z < 1.52]
    rims = set(rim)
    pair_t = {}
    for v in rim:
        for e in v.link_edges:
            u = e.other_vert(v)
            if u not in rims and box(u.co) and -0.91 < u.co.y < -0.78:
                pair_t[u] = v
    pair_e = {}
    for u, v in pair_t.items():
        for e in u.link_edges:
            w = e.other_vert(u)
            if w not in rims and w not in pair_t and box(w.co):
                pair_e[w] = v
    RP = np.array([v.co[:] for v in rim])
    C = Vector(RP.mean(0))
    nrm = Vector(np.linalg.svd(RP - RP.mean(0))[2][2])
    nrm = nrm if nrm.z > 0 else -nrm
    for layer, kin, lift in ((pair_t, 0.30, 0.02), (pair_e, 0.42, 0.075)):     # s2 r4 values (r5/r6 were worse)
        for u, v in layer.items():
            u.co = v.co + (C - v.co) * kin + nrm * lift
    say(f'ear root: rim {len(rim)} transition {len(pair_t)} E1 {len(pair_e)} normal {tuple(round(c, 2) for c in nrm)}')
    # s4 r19: the notch under the tail root (crops j4 A/B): the tail root's underside (Rt j4-j5) 2.5 cm down and the
    # rump's last ring bottom (R0 j11-j13) 2 cm up and 1 cm back, so the tail's underside runs into the rump in one slope
    for j in (4, 5):
        q = P('Rt')[j]
        move([vert_near(bm, q)], (0.0, -0.005, -0.025))
    for j in (11, 12, 13):
        q = P('R0')[j]
        move([vert_near(bm, q)], (0.0, 0.01, 0.02))
    # s2 r7's head loop through the ear span was dropped at s3 r1: no visible gain in the crops, strip 1.54 -> 2.81 r
    commit(body, bm)


PAL = {'skin': '#aba69f', 'leg': '#c6bfb4', 'dark': '#55504b', 'horn': '#e0d6c4', 'eye': '#4a3322', 'belly': '#bbb5ab'}   # s4 r18: mid warm grey for both renderers (s3 r2 washed out in EEVEE)


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y > 1.40 and z < 0.73:
        return 'dark'                                   # tail tuft
    if z < 0.30 and x > 0.06:
        return 'leg'                                    # lower legs, lighter
    if n.z < -0.55 and z < 0.78 and -0.45 < y < 1.15:
        return 'belly'                                  # detail pass: the paler underside (sheet)
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
    3 cm in, a mid ring and a blunt rounded tip. The sole edge sits 8 mm off the ground (s3 r1: it z-fought the
    foot's sole at z = 0)."""
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
    from smooth_borders import smooth_borders
    smooth_borders(body, k=k)                    # owner 10-21: borders follow the form
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []
    # eye: a small round lens in the socket, a dark pupil disc
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.2, 0.05))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.004, n, 0.034, 0.016)     # s3 r1: 68 mm (the eye check: >= 0.06 of the head)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'dark': '#141210'},
          lambda c_, n_, i: 'dark' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.016 and n_.dot(n) > 0.5 else 'eye')
    pieces.append(eye)
    # horns: on the midline (library horn, one shell, no mirror)
    h1 = PT.horn((0.0, -1.335, 1.15), length=0.40, radius=0.11, taper=1.5,   # s3 r3: thicker (sheet base ~0.2 m)
                 forward=(0, -0.22, 1), up=(0, 1, 0), curve=38,
                 segs=4, sides=6, name='horn_front', mats={'horn': 'horn', 'horn_tip': 'horn'}, colours={'horn': PAL['horn'], 'horn_tip': PAL['horn']})
    h2 = PT.horn((0.0, -1.10, 1.235), length=0.18, radius=0.07, taper=1.3, forward=(0, -0.1, 1), up=(0, 1, 0), curve=25,
                 segs=3, sides=6, name='horn_back', mats={'horn': 'horn', 'horn_tip': 'horn'}, colours={'horn': PAL['horn'], 'horn_tip': PAL['horn']})
    pieces += [h1, h2]
    # toenails: three per foot round the front of the foot
    bm = bmesh.new()
    for sec in (FORE[-2], HIND[-2]):
        cx, cy, z, rx, ry, nn = sec
        for ang in (-90, -125, -55):
            th = math.radians(ang)
            d = Vector((math.cos(th), math.sin(th), 0.0))
            o = Vector((cx, cy, 0.03)) + d * 0.5
            hit = tree.ray_cast(o, -d, 1.0)[0]
            base = Vector((hit.x, hit.y, 0.0)) if hit is not None else Vector((cx, cy, 0.0)) + d * ry
            nail(bm, base - d * 0.004, d, 0.06, 0.065, 0.022)
    nails = object_from_bm('nails', bm)
    paint(nails, {'dark': PAL['dark']}, lambda c_, n_, i: 'dark')
    pieces.append(nails)
    pieces += detail_pass(body)
    return pieces


def detail_pass(body):
    """Tier-3 detail pass (2026-10-23, zoo/detail_audit.md rhino list): chunky seated pieces, flat colour."""
    import detail_pieces as D
    tree = D.body_tree(body)
    out = []

    def piece(name, bm, col, mirror=True, rule=None):
        ob = object_from_bm(name, bm, mirror=mirror)
        cols = col if isinstance(col, dict) else {col: PAL[col]}     # palette KEY: materials are shared by name
        paint(ob, cols, rule or (lambda c_, n_, i: next(iter(cols))))
        out.append(ob)
        return ob

    def trunk_fold(y0, y1, a0, a1, n=9):
        """Stations round the barrel from angle a0 to a1 (0 = the back seam), the fold line leaning from y0 (at a0)
        to y1 (at a1) in the side view: each ray leaves the trunk axis at its own y."""
        hits = []
        for i in range(n):
            t = i / (n - 1)
            c = D.section_centre(tree, y0 + (y1 - y0) * t)[0]
            hits += D.ring_stations(tree, c, (0, 1, 0), (0, 0, 1), a0 + (a1 - a0) * t, a0 + (a1 - a0) * t + 1e-3, 2)[:1]
        return D.stations_from_hits(hits, side_hint=(0, 1, 0))     # STEP: the overhang step faces the rear

    # 1-3. armour skin folds (the sheet's signature, side view): the neck fold behind the head; the shoulder shield's
    # rear edge from over the shoulder back and down behind the elbow; the flank fold from mid flank down into the
    # front of the thigh. The first two open on the back seam (they cross the back, top view), all taper into the skin.
    # r24 (judge r23: raised bands read as straps / a collar / cuffs): side-only folds, broad and low, a gentle front
    # slope rising to one overhang step at the rear (blended skin step, not a strap); no cuffs, no rump ridges
    STEP = [(-0.5, 0.12), (-0.15, 0.6), (0.3, 1.0), (0.5, 0.18)]
    for nm, y0, y1, a0, a1, w, h in (('fold_neck', -0.585, -0.54, 35, 125, 0.18, 0.035),
                                     ('fold_shoulder', -0.13, 0.03, 30, 118, 0.22, 0.04),
                                     ('fold_flank', 0.87, 0.72, 48, 124, 0.18, 0.035)):
        bm = bmesh.new()
        D.band(bm, trunk_fold(y0, y1, a0, a1), w, h, prof=STEP, taper=0.3)
        piece(nm, bm, 'skin')
    # 6. brow ridge: a raised arc over each eye
    e = SOCKET[0]
    bm = bmesh.new()
    pts = [(1.0, e.y + 0.06 * t, e.z + 0.05 - 0.018 * t * t) for t in (-1.0, -0.5, 0.0, 0.5, 1.0)]
    D.band(bm, D.stations_from_hits(D.path_stations(tree, pts, (-1, 0, 0)), side_hint=(0, 0, 1)), 0.045, 0.026,
           prof=D.ROUND)
    piece('brow', bm, 'skin')
    # 7. mouth line: a dark lip groove-line from the muzzle front back to under the eye
    bm = bmesh.new()
    pts = [(1.0, y, z) for y, z in ((-1.405, 0.905), (-1.34, 0.878), (-1.26, 0.862), (-1.18, 0.866), (-1.11, 0.885))]
    D.band(bm, D.stations_from_hits(D.path_stations(tree, pts, (-1, 0, 0)), side_hint=(0, 0, 1)), 0.034, 0.022,
           prof=D.ROUND)
    piece('mouth', bm, 'dark')
    # 8. nostrils: a raised mound on each side of the muzzle front with a dark nostril cap
    h_ = D.cast_in(tree, (0.072, -2.5, 0.965), (0, 1, 0))
    bm = bmesh.new()
    nc, nn = h_[0], (h_[1] + Vector((0.35, 0, 0))).normalized()
    D.knob(bm, nc, nn, 0.034, 0.02, sides=6, top=0.6)
    piece('nostril', bm, {'skin': PAL['skin'], 'dark': PAL['dark']},
          rule=lambda c_, n_, i: 'dark' if n_.dot(nn) > 0.9 else 'skin')
    # 9. tail-tip tuft: a flat dark brush (one midline piece)
    bm = bmesh.new()
    D.fan(bm, (0.0, 1.447, 0.665), (0, 0.06, -1), (0, 1, 0), 0.13, 0.075, 0.038)
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
        if p.name.startswith('horn') or p.name.startswith('eye'):
            bind(p, rig, body=body)
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 8)},
                       20: {'ear.L': (0, 0, -12), 'head': (3, 0, 0)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -8)}, 48: {}})
    A = 12
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 5)},
        7: {'forearm.R': (-22, 0, 0), 'hand.R': (-15, 0, 0), 'shin.L': (-12, 0, 0), 'foot.L': (15, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -5)},
        19: {'forearm.L': (-22, 0, 0), 'hand.L': (-15, 0, 0), 'shin.R': (-12, 0, 0), 'foot.R': (15, 0, 0), 'neck': (2, 0, 0)},
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
