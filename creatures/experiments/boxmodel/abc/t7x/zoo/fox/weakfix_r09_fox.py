import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

META = dict(creature='fox', model='opus', stage1_tris=(400, 3000), total_tris=(500, 4500))   # keep_valleys is set in stage2 (a lambda cannot go in the lock JSON)

# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png
J = dict(
    hips=(0.0, 0.28, 0.61), spine=(0.0, 0.0, 0.61), chest=(0.0, -0.30, 0.64),
    neck=(0.0, -0.46, 0.76), head=(0.0, -0.58, 0.86), nose=(0.0, -0.83, 0.75),
    tail0=(0.0, 0.43, 0.62), tail1=(0.0, 0.53, 0.51), tail2=(0.0, 0.64, 0.33), tail3=(0.0, 0.82, 0.13),
    shoulder=(0.11, -0.38, 0.58), elbow=(0.11, -0.40, 0.36), wrist=(0.11, -0.42, 0.09),
    fpaw=(0.11, -0.44, 0.02), ftoe=(0.11, -0.51, 0.02),
    hipL=(0.11, 0.27, 0.60), knee=(0.11, 0.27, 0.42), hock=(0.10, 0.45, 0.22),
    hpaw=(0.10, 0.415, 0.03), htoe=(0.10, 0.35, 0.02),
    ear=(0.105, -0.555, 0.98), eartip=(0.135, -0.548, 1.15),
)

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = [(0, 1), (0.6, 0.92), (1, 0.3), (0.85, -0.35), (0.45, -0.8), (0, -1)]
CHEST = [(0, 1), (0.62, 0.9), (1, 0.35), (0.8, -0.3), (0.35, -0.8), (0, -1)]
HEADB = [(0, 1), (0.75, 0.97), (1, 0.4), (0.85, -0.4), (0.5, -0.85), (0, -1)]     # skull back: ear face high
HEAD = [(0, 1), (0.75, 0.93), (1, 0.3), (0.85, -0.4), (0.5, -0.85), (0, -1)]
HEADF = [(0, 1), (0.75, 0.88), (1, 0.1), (0.85, -0.45), (0.5, -0.85), (0, -1)]   # stop: eye face low
MUZ = [(0, 1), (0.62, 0.95), (1, 0.4), (0.95, -0.3), (0.6, -0.85), (0, -1)]
TAIL = [(0, 1), (0.7, 0.7), (1, 0.1), (0.85, -0.5), (0.45, -0.9), (0, -1)]


def dense(prof):
    """6-vertex half ring -> 10: a rounding vertex (Catmull-Rom midpoint, bulges out toward the curve) between
    each pair from the top seam to the lower flank; the belly plane (last pair) stays one flat face.
    Old index j -> new index OLDJ[j]."""
    P_ = [(-prof[1][0], prof[1][1])] + list(prof)
    out = []
    for j in range(5):
        out.append(prof[j])
        if j < 4:
            p0, p1, p2, p3 = P_[j], P_[j + 1], P_[j + 2], P_[j + 3]
            out.append(tuple(round((-a + 9 * b + 9 * c - d) / 16, 4) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(prof[5])
    return out


def flat(prof):
    """6-vertex half ring -> 10 with straight midpoints: the before3 torso planes stay flat (no rounding bulge)."""
    out = []
    for j in range(5):
        out.append(prof[j])
        if j < 4:
            out.append(tuple(round((a + b) / 2, 4) for a, b in zip(prof[j], prof[j + 1])))
    out.append(prof[5])
    return out


OLDJ = (0, 2, 4, 6, 8, 9)
BODYF, CHESTF = flat(BODY), flat(CHEST)   # torso (R0..C2): before3 sections, flat planes
BODY, CHEST, HEADB, HEAD, HEADF, MUZ, TAIL = map(dense, (BODY, CHEST, HEADB, HEAD, HEADF, MUZ, TAIL))


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


# the spine loft, tail tip -> nose: top and bottom of each section from the side view, W from front/top
SECS = [
    tb('T0', (0.84, 0.15), (0.80, 0.115), 0.03, TAIL),
    tb('T0x', (0.83, 0.235), (0.741, 0.112), 0.087, TAIL),
    tb('T1', (0.79, 0.31), (0.68, 0.13), 0.19, TAIL),
    tb('T1x', (0.746, 0.368), (0.622, 0.141), 0.22, TAIL),
    tb('T2', (0.70, 0.43), (0.585, 0.20), 0.225, TAIL),
    tb('T2x', (0.642, 0.473), (0.540, 0.274), 0.205, TAIL),
    tb('T3', (0.60, 0.55), (0.50, 0.36), 0.17, TAIL),
    tb('T3x', (0.531, 0.581), (0.468, 0.458), 0.132, TAIL),
    tb('T4', (0.49, 0.65), (0.44, 0.53), 0.10, TAIL),
    tb('T4x', (0.451, 0.663), (0.416, 0.519), 0.103, TAIL),
    tb('R0', (0.42, 0.70), (0.39, 0.48), 0.12, BODYF),
    tb('R1', (0.32, 0.735), (0.32, 0.43), 0.155, BODYF),
    tb('R2', (0.19, 0.755), (0.19, 0.45), 0.145, BODYF),
    tb('W0', (0.05, 0.76), (0.05, 0.43), 0.15, BODYF),
    tb('M0', (-0.14, 0.77), (-0.14, 0.39), 0.165, BODYF),
    tb('C0', (-0.33, 0.81), (-0.33, 0.37), 0.20, CHESTF),
    tb('C1', (-0.36, 0.89), (-0.47, 0.42), 0.20, CHESTF),
    tb('C2', (-0.40, 0.95), (-0.52, 0.52), 0.18, CHESTF),
    tb('C2x', (-0.415, 1.002), (-0.548, 0.583), 0.154, BODY),
    tb('N0', (-0.45, 1.0), (-0.575, 0.635), 0.13, BODY),
    tb('H0', (-0.525, 1.015), (-0.60, 0.69), 0.12, HEADB),
    tb('H0b', (-0.595, 0.965), (-0.62, 0.705), 0.112, HEAD),
    tb('H1', (-0.655, 0.915), (-0.655, 0.705), 0.082, HEADF),
    tb('H2', (-0.70, 0.865), (-0.70, 0.70), 0.052, MUZ),
    tb('H2x', (-0.739, 0.812), (-0.739, 0.692), 0.044, MUZ),
    tb('H3', (-0.78, 0.805), (-0.78, 0.69), 0.038, MUZ),
    tb('H4', (-0.845, 0.765), (-0.84, 0.71), 0.026, MUZ),
]


def _mid(a, b, nm, t=0.5):
    """An in-between torso station on the straight line between two sections: every face it splits stays
    co-planar with its neighbour (density without rib bands; the shoulder / hip breaks stay at C0 / R1)."""
    lerp = lambda p, q: tuple(round(x + (y - x) * t, 4) for x, y in zip(p, q))
    return (nm, lerp(a[1], b[1]), round(a[2] + (b[2] - a[2]) * t, 2), round(a[3] + (b[3] - a[3]) * t, 4),
            round(a[4] + (b[4] - a[4]) * t, 4), round(a[5] + (b[5] - a[5]) * t, 4), a[6])


# density pass 9: the 2x torso stations back (R0x, R2x, W0x, M0x, C1x), placed on the planes, not bulged
for _a, _nm in (('R0', 'R0x'), ('R2', 'R2x'), ('W0', 'W0x'), ('M0', 'M0x'), ('C1', 'C1x')):
    _i = [q[0] for q in SECS].index(_a)
    SECS.insert(_i + 1, _mid(SECS[_i], SECS[_i + 1], _nm))

# limb sections: (centre xyz, rx, ry) — horizontal hexagons, deeper front-to-back
# decagon rings (10 vertices: the 4-face flank region's border); new stations at the forearm taper and the
# gaskin -> hock -> cannon curve, ry read off the side trace (fore 0.20-0.18 m deep at z 0.29/0.155, hind 0.10-0.09)
FORE = [(J['elbow'], 0.05, 0.065), ((0.11, -0.405, 0.29), 0.04, 0.053), ((0.11, -0.41, 0.22), 0.034, 0.045),
        ((0.11, -0.415, 0.155), 0.031, 0.04), (J['wrist'], 0.03, 0.036),
        ((0.11, -0.435, 0.04), 0.042, 0.055), ((0.11, -0.45, 0.0), 0.045, 0.07)]
HIND = [(J['knee'], 0.072, 0.115), ((0.105, 0.37, 0.31), 0.053, 0.072), ((0.102, 0.415, 0.265), 0.04, 0.052),
        (J['hock'], 0.032, 0.04), ((0.10, 0.44, 0.15), 0.029, 0.036),
        ((0.10, 0.43, 0.075), 0.029, 0.034), ((0.10, 0.415, 0.036), 0.042, 0.055), ((0.10, 0.405, 0.0), 0.045, 0.068)]
EAR = [((0.112, -0.558, 1.01), 0.068, 0.05, 0.022), ((0.128, -0.552, 1.075), 0.04, 0.026, 0.006), ((0.135, -0.548, 1.15), 0.008, 0.006, 0.0)]


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def role_pos(sec, u, s, corner=0.55):
    c, rx, ry = sec[0], sec[1], sec[2]
    dz = sec[3] if len(sec) > 3 else 0.0
    k = 1.0 if u == 0 else corner
    return (c[0] + u * rx, c[1] + s * ry * k, c[2] - u * dz)


def limb_pos(sec, th):
    """A decagon leg ring: th = angle round the leg (0 = outer side, -90 = front, +90 = back)."""
    c, rx, ry = sec[0], sec[1], sec[2]
    return (c[0] + rx * math.cos(math.radians(th)), c[1] + ry * math.sin(math.radians(th)), c[2])


def grow(bm, faces, roles, secs, corner=0.55, pos=None):
    """Extrude a face region section by section; each new vertex keeps the role
    (u across the ring, s front/back) of the vertex it was extruded from."""
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, r_ in new.items():
            v.co = Vector(pos(sec, r_) if pos else role_pos(sec, *r_, corner))
        faces, roles = r['faces'], new
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(span_name, secs):
        i = idx[span_name]          # span between ring i (rear) and ring i+1 (front)
        rr, rf = rings[i], rings[i + 1]
        roles = {rf[4 + q]: -18 - 36 * q for q in range(5)}
        roles.update({rr[4 + q]: 18 + 36 * q for q in range(5)})
        grow(bm, [spans[i][q] for q in (4, 5, 6, 7)], roles, secs, pos=limb_pos)

    limb('C0', FORE)
    limb('R1', HIND)
    i = idx['H0']
    rr, rf = rings[i], rings[i + 1]
    grow(bm, [spans[i][2], spans[i][3]], {rf[2]: (-1, -1), rf[3]: (0, -1), rf[4]: (1, -1), rr[2]: (-1, 1), rr[3]: (0, 1),
                                          rr[4]: (1, 1)}, EAR, corner=1.0)
    snap_seam(bm)
    return object_from_bm('body', bm)


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def eye_face_centre():
    """Centre of the stop face between H0b and H1 (the outer quad above the cheek line): the eye socket."""
    H0b, H1 = P('H0b'), P('H1')
    return (H0b[3] + H0b[4] + H1[3] + H1[4]) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.035 and abs(c.y - ec0.y) < 0.035
                                        and abs(c.z - ec0.z) < 0.05)
    bm = edit(body)
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    with k.topo(bm, 'loop', 'elbow: a second ring between elbow and forearm so the elbow bends, not kinks'):
        loopcut(bm, edge_near(bm, mid(limb_pos(FORE[0], 18), limb_pos(FORE[1], 18))), t=0.5)
    with k.topo(bm, 'loop', 'stifle: a second ring between stifle and gaskin for the hind-leg bend'):
        loopcut(bm, edge_near(bm, mid(limb_pos(HIND[0], 18), limb_pos(HIND[1], 18))), t=0.5)
    with k.topo(bm, 'loop', 'neck: a ring between N0 and the skull so the head-down lunge bends the neck in two places'):
        loopcut(bm, edge_near(bm, mid(P('N0')[0], P('H0')[0])), t=0.5)
    H0b, H1, H2, H2x, H3, H4 = P('H0b'), P('H1'), P('H2'), P('H2x'), P('H3'), P('H4')
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the stop face, under the brow'):
        inner = inset(bm, [f], 0.26, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.008)
    scale(ev, (1.0, 1.0, 0.85))
    # brow overhang: the front top corner of the eye face forward and out; the cheekbone under the eye out
    move([vert_near(bm, H1[2]), vert_near(bm, H1[3])], (0.004, -0.008, 0.002))
    move([vert_near(bm, H0b[4])], (0.01, 0.0, 0.0))
    # deliberate planes on the muzzle: one flat side, one flat bridge
    flatten([vert_near(bm, R_[j]) for R_ in (H2, H2x, H3, H4) for j in (4, 5, 6)])
    flatten([vert_near(bm, R_[j]) for R_ in (H2, H2x, H3, H4) for j in (0, 1, 2)])
    # nose: the flat end cap becomes a forward-down slanted pad (top edge forward, chin edge back)
    move([vert_near(bm, H4[j]) for j in (0, 1, 2)], (0.0, -0.018, -0.004))
    move([vert_near(bm, H4[j]) for j in (8, 9)], (0.0, 0.016, 0.0))
    scale([vert_near(bm, q) for q in H4], (0.85, 1.0, 1.0), pivot=(0.0, 0.0, 0.0))
    # tail tip: a 3 cm ring 17 cm past T1 makes needle triangles; widen it to a blunt tip (the brush clump makes the point)
    T0 = P('T0'); tc = sum(T0, Vector()) / len(T0)
    scale([vert_near(bm, q) for q in T0], 1.8, pivot=(0.0, tc.y, tc.z))
    commit(body, bm)


# colours picked off the reference sheet: orange coat, cream chin/throat/chest/belly/tail tip, black-brown socks and ear backs
PAL = {'fur': '#d0601e', 'cream': '#efe4cf', 'sock': '#3a2a24', 'amber': '#e0a030', 'nose': '#1a1414'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.81 and z > 0.735:
        return 'nose'                                   # black nose pad
    if z > 1.0 and -0.63 < y < -0.45 and 0.03 < x < 0.22:
        return 'cream' if n.y < -0.3 else 'sock'        # ears: cream forward wall, black back
    if y > 0.62:
        return 'cream'                                  # white tail tip
    if y > 0.42 and z > 0.32:
        return 'fur'                                    # tail
    if z < 0.27:
        return 'sock'                                   # black-brown stockings, fore and hind
    if y < -0.66 and (n.z < -0.2 or z < 0.75):
        return 'cream'                                  # lips and lower jaw
    if -0.68 < y < -0.55 and z < 0.82 and x > 0.06 and n.z < 0.3:
        return 'cream'                                  # cheeks under the eye
    if -0.64 < y < -0.36 and n.y < -0.3 and 0.42 < z < 0.85 and x < 0.14:
        return 'cream'                                  # throat and chest
    if (n.z < -0.4 and z < 0.5 and y < 0.2) or (-0.36 < y < 0.12 and z < 0.5 and n.z < 0.25):
        return 'cream'                                  # belly and the lower-flank underline
    return 'fur'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A low-poly eye: back cone, iris ring, pupil fan. Returns the pupil faces."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 3 for k_ in range(6)]]
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    pup = []
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        pup.append(bm.faces.new([I[a], I[b], A]))
    return pup


def clump(bm, a, n, lay, s, L):
    """A chunky fur clump: a sunk square base, a narrower mid ring, a tip laid back along `lay`."""
    n, lay = Vector(n).normalized(), Vector(lay).normalized()
    u = n.cross(lay).normalized(); w = u.cross(n)
    b = a - n * 0.025
    base = [bm.verts.new(b + u * su * s + w * sw * s) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = a + n * 0.018 + lay * L * 0.4
    mid = [bm.verts.new(m + u * su * s * 0.6 + w * sw * s * 0.5) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    tip = bm.verts.new(a + n * L * 0.3 + lay * L)
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip])


def out_n(nm, j):
    for (n_, c, a, T, B, W, p) in SECS:
        if n_ == nm:
            q = P(nm)[j]
            return q, (q - Vector((0.0, c[0], c[1]))).normalized()


def surf(a, b, t, jf):
    """A point on the loft between sections a and b (t from a to b) at fractional ring index jf, and its
    outward normal (radial from the interpolated section centre)."""
    names = [n_ for (n_, *_r) in SECS]
    ia, ib = names.index(a), names.index(b)
    if abs(ib - ia) == 2:                  # a station was added between a and b: walk the real surface
        m = names[(ia + ib) // 2]
        a, b, t = (a, m, 2 * t) if t <= 0.5 else (m, b, 2 * t - 1)
    j0o = min(int(jf), 4); fo = jf - j0o
    jf = OLDJ[j0o] + fo * (OLDJ[j0o + 1] - OLDJ[j0o])      # jf is given in the old 6-vertex ring index
    A, Bq = P(a), P(b)
    j0 = min(int(jf), 8); f = jf - j0
    pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
    p = pa.lerp(pb, t)
    ca = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == a][0]))
    cb = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == b][0]))
    c = ca.lerp(cb, t)
    return p, (p - c).normalized()


def clumps(spec, colour):
    """spec: [(a, b, t, jf, lay, s, L)] -> one mirrored piece of fur clumps; colour(c, n, i) -> palette key."""
    bm = bmesh.new()
    for a, b, t, jf, lay, s_, L_ in spec:
        p, n_ = surf(a, b, t, jf)
        clump(bm, p, n_, Vector(lay), s_, L_)
    return bm


def stage3(k, body):
    paint(body, PAL, body_rule)
    # eyes: amber lenses with a black pupil fan, proud of the socket floor
    H0b, H1 = P('H0b'), P('H1')
    fn = (H1[3] - H0b[3]).cross(H0b[4] - H0b[3]).normalized()
    fn = fn if fn.x > 0 else -fn
    ec = eye_face_centre()
    bmb = edit(body)
    f = face_near(bmb, ec - fn * 0.008, n=fn)
    c, n = f.calc_center_median().copy(), f.normal.copy()
    n = n if n.x > 0 else -n
    bmb.free()
    bm = bmesh.new()
    lens(bm, c + n * 0.007, n, 0.026, 0.012)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'nose': PAL['nose']},
          lambda c_, n_, i: 'nose' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.010 and n_.dot(n) > 0.5 else 'amber')
    # bib and brush pieces removed (pass 5): the cream chest and tail tip are flat colour blocks on the body planes
    # toe claws: three per paw, the middle one leading
    bm = bmesh.new()
    for (sole, top) in ((FORE[-1], FORE[-2]), (HIND[-1], HIND[-2])):
        (cx, cy, _), rx, ry = sole
        for d in (-0.024, 0.0, 0.024):
            yf = cy - ry * (1 - 0.45 * abs(d) / rx) + 0.004
            x = cx + d
            t = bm.verts.new((x, yf - 0.022 - (0.006 if d == 0 else 0), 0.012))
            b = [bm.verts.new(p_) for p_ in ((x - 0.009, yf + 0.012, 0.005), (x + 0.009, yf + 0.012, 0.005), (x, yf + 0.012, 0.024))]
            bm.faces.new([b[0], b[1], b[2]]); bm.faces.new([b[0], t, b[1]]); bm.faces.new([b[1], t, b[2]]); bm.faces.new([b[2], t, b[0]])
    claws = object_from_bm('claws', bm)
    paint(claws, {'nose': PAL['nose']}, lambda c_, n_, i: 'nose')
    return [eye, claws]


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
    # idle: breathing through the chest, a slow tail sway, one ear twitch
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 4)},
                       20: {'ear.L': (0, 0, -14)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -4)}, 48: {}})
    # move: trot, diagonal pairs (LF + RH, then RF + LH); the swinging leg flexes
    A = 18
    TL = -16     # r09: negative lifts (r08 +16 pushed the brush into the thighs: clip 16 %); weakfix 10-23: the trotting fox carries its brush lifted clear of the hind legs' swing (was hanging
                 # into it: tail vs thigh posed clip 7-8 %); the side sway 5 -> 3 deg
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, 3)},
        7: {'forearm.R': (-35, 0, 0), 'paw.R': (-30, 0, 0), 'shin.L': (-20, 0, 0), 'foot.L': (25, 0, 0), 'neck': (2, 0, 0), 'tail0': (TL, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, -3)},
        19: {'forearm.L': (-35, 0, 0), 'paw.L': (-30, 0, 0), 'shin.R': (-20, 0, 0), 'foot.R': (25, 0, 0), 'neck': (2, 0, 0), 'tail0': (TL, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail0': (TL, 0, 0), 'tail1': (0, 0, 3)}})
    # attack: rear back, then a head-down lunge and a snap of the head
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
