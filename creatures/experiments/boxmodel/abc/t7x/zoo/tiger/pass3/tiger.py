import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# Bengal tiger, t7 hand box-model: one spine loft of 6-vertex half rings (tail tip -> nose), legs extruded as
# 2-face regions from the lower flank, ears as 1-face extrusions; stage 2 joint rings, eye socket, stripe loops;
# stage 3 lens eyes, cheek ruff, claws, colour along the loops; stage 4 rig and clips.
META = dict(creature='tiger', model='opus', stage1_tris=(1200, 2600), total_tris=(2000, 4600),
            closeups=[('head', (0.0, -0.71, 0.88), 0.22, 'hero'),
                      ('front paw', (0.16, -0.50, 0.05), 0.11, 'hero'),
                      ('hind paw', (0.15, 0.40, 0.06), 0.11, 'hero'),
                      ('tail', (0.0, 0.70, 0.32), 0.26, 'hero')])

# the skeleton (x >= 0 half; .L on +X), read off reference/side.png + front.png
J = dict(
    hips=(0.0, 0.30, 0.64), spine=(0.0, 0.02, 0.64), chest=(0.0, -0.30, 0.66),
    neck=(0.0, -0.48, 0.80), head=(0.0, -0.61, 0.87), nose=(0.0, -0.90, 0.80),
    tail0=(0.0, 0.47, 0.63), tail1=(0.0, 0.59, 0.43), tail2=(0.0, 0.71, 0.25), tail3=(0.0, 0.92, 0.168),
    shoulder=(0.15, -0.38, 0.62), elbow=(0.16, -0.43, 0.27), wrist=(0.155, -0.465, 0.11),
    fpaw=(0.155, -0.48, 0.02), ftoe=(0.155, -0.60, 0.02),
    hipL=(0.145, 0.30, 0.62), knee=(0.15, 0.28, 0.40), hock=(0.145, 0.47, 0.20),
    hpaw=(0.145, 0.41, 0.03), htoe=(0.145, 0.30, 0.02),
    ear=(0.175, -0.545, 1.06), eartip=(0.175, -0.545, 1.12),
)

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = [(0, 1), (0.6, 0.92), (1, 0.3), (0.88, -0.35), (0.5, -0.8), (0, -1)]
CHEST = [(0, 1), (0.65, 0.9), (1, 0.35), (0.85, -0.3), (0.4, -0.8), (0, -1)]
HEADB = [(0, 1), (0.62, 0.95), (1, 0.35), (0.88, -0.4), (0.5, -0.85), (0, -1)]
HEAD = [(0, 1), (0.7, 0.92), (1, 0.3), (0.88, -0.4), (0.5, -0.85), (0, -1)]
HEADF = [(0, 1), (0.75, 0.86), (1, 0.1), (0.88, -0.45), (0.5, -0.85), (0, -1)]
MUZ = [(0, 1), (0.65, 0.95), (1, 0.35), (0.95, -0.3), (0.6, -0.85), (0, -1)]
TAIL = [(0, 1), (0.7, 0.7), (1, 0.1), (0.8, -0.5), (0.4, -0.9), (0, -1)]


def roundp(p):
    """Density pass 3: 6 -> 10 points per half ring. A rounded point goes into each of the first four spans
    (Catmull-Rom midpoint on the ring mirrored across the seam), so the cross-section reads round, not hexagonal.
    Old point i sits at new index O[i]."""
    m = [(-p[1][0], p[1][1])] + list(p) + [(-p[4][0], p[4][1])]
    out = []
    for i in range(5):
        out.append(p[i])
        if i < 4:
            a, b, c, d = m[i], m[i + 1], m[i + 2], m[i + 3]
            out.append(tuple(round((-a[j] + 9 * b[j] + 9 * c[j] - d[j]) / 16, 4) for j in range(2)))
    out.append(p[5])
    return out


O = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 9}
BODY, CHEST, HEADB, HEAD, HEADF, MUZ, TAIL = [roundp(q) for q in (BODY, CHEST, HEADB, HEAD, HEADF, MUZ, TAIL)]


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


def ax(nm, c, d, h, W, prof=TAIL):
    """A tail section from its centre and the tail's direction (y, z) in the side view."""
    l = math.hypot(*d)
    py, pz = d[1] / l, -d[0] / l          # perpendicular, pointing up
    if pz < 0:
        py, pz = -py, -pz
    return tb(nm, (c[0] + py * h, c[1] + pz * h), (c[0] - py * h, c[1] - pz * h), W, prof)


# the spine loft, tail tip -> nose
SECS = [
    ax('T0', (0.895, 0.175), (1.0, 0.1), 0.05, 0.05),
    ax('T1', (0.815, 0.18), (1.0, -0.45), 0.068, 0.068),
    ax('T2', (0.715, 0.255), (1.0, -1.0), 0.07, 0.072),
    ax('T2b', (0.668, 0.312), (0.8, -1.0), 0.075, 0.077),      # pass 3: tail bend, on the traced tail midline
    ax('T3', (0.625, 0.385), (0.6, -1.0), 0.078, 0.08),
    ax('T3b', (0.59, 0.475), (0.55, -1.0), 0.08, 0.086),       # pass 3: tail root curve
    ax('T4', (0.555, 0.57), (0.5, -1.0), 0.08, 0.09),
    tb('R0', (0.47, 0.70), (0.475, 0.485), 0.15, BODY),        # pass 3: bottom forward of T4's, no fold
    tb('R0b', (0.415, 0.745), (0.43, 0.44), 0.185, BODY),      # pass 3: rump curve (sheet top 0.739)
    tb('R1', (0.36, 0.79), (0.36, 0.40), 0.205, BODY),
    tb('R2', (0.20, 0.83), (0.20, 0.43), 0.205, BODY),
    tb('R2b', (0.125, 0.833), (0.125, 0.415), 0.20, BODY),     # pass 3: belly tuck behind the ribs
    tb('W0', (0.05, 0.835), (0.05, 0.41), 0.20, BODY),
    tb('W0b', (-0.03, 0.836), (-0.03, 0.39), 0.202, BODY),     # pass 3: belly (sheet 0.836 / 0.388)
    tb('M0', (-0.11, 0.835), (-0.11, 0.37), 0.205, BODY),
    tb('M0b', (-0.19, 0.842), (-0.19, 0.345), 0.225, CHEST),   # pass 3: back stays flat to the shoulder (sheet 0.84)
    tb('C0', (-0.27, 0.885), (-0.27, 0.30), 0.24, CHEST),
    tb('C1', (-0.42, 0.93), (-0.44, 0.31), 0.245, CHEST),
    tb('C1b', (-0.455, 0.955), (-0.515, 0.355), 0.242, CHEST), # pass 3: round chest front
    tb('C2', (-0.49, 0.98), (-0.58, 0.42), 0.235, CHEST),
    tb('C2b', (-0.51, 0.99), (-0.61, 0.49), 0.24, BODY),       # pass 3: shoulder-neck, throat curve
    tb('N0', (-0.53, 1.02), (-0.63, 0.57), 0.24, BODY),
    tb('N0b', (-0.552, 1.053), (-0.648, 0.598), 0.235, HEADB), # pass 3: nape and ruff (sheet jaw 0.583)
    tb('H0', (-0.575, 1.075), (-0.665, 0.635), 0.225, HEADB),
    tb('H0b', (-0.645, 1.06), (-0.705, 0.635), 0.21, HEAD),
    tb('H1', (-0.72, 0.99), (-0.745, 0.64), 0.185, HEADF),
    tb('H1b', (-0.745, 0.955), (-0.758, 0.642), 0.177, HEADF), # pass 3: round forehead into the stop
    tb('H2', (-0.765, 0.895), (-0.77, 0.645), 0.165, MUZ),
    tb('H2b', (-0.80, 0.884), (-0.80, 0.655), 0.155, MUZ),     # pass 3: muzzle bridge (sheet 0.914)
    tb('H3', (-0.84, 0.86), (-0.835, 0.67), 0.14, MUZ),
    tb('H4', (-0.895, 0.83), (-0.885, 0.73), 0.105, MUZ),
]

# limb sections: (centre xyz, rx, ry) — horizontal hexagons, deeper front-to-back
# pass 3: 10-vertex leg rings (4-face root strip) and a forearm, ankle, thigh and gaskin station each
FORE = [(J['elbow'], 0.10, 0.13), ((0.16, -0.44, 0.225), 0.096, 0.12), ((0.16, -0.45, 0.18), 0.088, 0.108),
        (J['wrist'], 0.08, 0.094), ((0.155, -0.472, 0.08), 0.09, 0.112),
        ((0.155, -0.48, 0.05), 0.104, 0.135), ((0.155, -0.49, 0.0), 0.11, 0.15)]
HIND = [(J['knee'], 0.11, 0.16), ((0.15, 0.335, 0.345), 0.098, 0.13), ((0.15, 0.39, 0.29), 0.085, 0.10),
        ((0.148, 0.43, 0.245), 0.076, 0.086), (J['hock'], 0.068, 0.072),
        ((0.145, 0.45, 0.10), 0.072, 0.078), ((0.145, 0.41, 0.045), 0.095, 0.115), ((0.145, 0.40, 0.0), 0.10, 0.135)]
EAR = [((0.175, -0.545, 1.09), 0.045, 0.032, 0.012), ((0.175, -0.545, 1.125), 0.024, 0.016, 0.0)]


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
    k = math.sqrt(max(0.0, 1.0 - (1.0 - corner * corner) * u * u))
    return (c[0] + u * rx, c[1] + s * ry * k, c[2] - u * dz)


def grow(bm, faces, roles, secs, corner=0.55):
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (u, s) in new.items():
            v.co = Vector(role_pos(sec, u, s, corner))
        faces, roles = r['faces'], new
    return faces, roles


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(span_name, secs):
        i = idx[span_name]
        rr, rf = rings[i], rings[i + 1]
        us = (1, 0.5, 0, -0.5, -1)
        roles = {**{rf[4 + j]: (u, -1) for j, u in enumerate(us)}, **{rr[4 + j]: (u, 1) for j, u in enumerate(us)}}
        grow(bm, [spans[i][4], spans[i][5], spans[i][6], spans[i][7]], roles, secs)

    limb('C0', FORE)
    limb('R1', HIND)
    i = idx['H0']
    rr, rf = rings[i], rings[i + 1]
    grow(bm, [spans[i][2]], {rf[2]: (-1, -1), rf[3]: (1, -1), rr[2]: (-1, 1), rr[3]: (1, 1)}, EAR, corner=1.0)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    H0b, H1 = P('H0b'), P('H1')
    return (H0b[2] + H0b[3] + H1[2] + H1[3]) / 4


# stripe bands: (rear section, front section, t of the first cut, band width as a fraction of the span)
STRIPE_SPANS = [('T3b', 'T4', 0.25, 0.5), ('T2b', 'T3', 0.25, 0.5), ('T1', 'T2', 0.45, 0.4),
                ('R0', 'R0b', 0.25, 0.5), ('R2', 'R2b', 0.25, 0.5), ('W0b', 'M0', 0.25, 0.5),
                ('M0b', 'C0', 0.25, 0.5), ('C1', 'C1b', 0.25, 0.5)]


def stage2(k, body):
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ec0 = eye_face_centre()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    # joint rings: elbow, stifle, neck-skull
    with topo(bm, k.log, 'loop', 'elbow ring: the bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(FORE[0], 1, 1), role_pos(FORE[1], 1, 1))), t=0.5)
    with topo(bm, k.log, 'loop', 'stifle ring: the bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(HIND[0], 1, 1), role_pos(HIND[1], 1, 1))), t=0.5)
    with topo(bm, k.log, 'loop', 'neck-skull ring: the head turn'):
        loopcut(bm, edge_near(bm, mid(P('N0b')[0], P('H0')[0])), t=0.5)
    # stripe loops: two rings close together in a span; the band between them is the stripe
    bands = []
    for a, b, t0, w in STRIPE_SPANS:
        A, B_ = P(a)[0], P(b)[0]
        e = edge_near(bm, mid(A, B_))
        near = vert_near(bm, A)
        with topo(bm, k.log, 'loop', f'stripe loop A in {a}-{b}: colour border'):
            va = loopcut(bm, e, t=t0, near=near)
        top = max(va, key=lambda v: v.co.z if abs(v.co.x) < 1e-6 else -9)
        top = min(va, key=lambda v: (v.co - (A.lerp(B_, t0))).length)
        e2 = edge_near(bm, mid(top.co, B_))
        tb_ = w / (1 - t0)
        with topo(bm, k.log, 'loop', f'stripe loop B in {a}-{b}: colour border'):
            vb = loopcut(bm, e2, t=tb_, near=top)
        bands.append(set(va) | set(vb))
    # eye socket, brow, cheekbone, muzzle planes, nose pad
    H0b, H1, H2, H2b, H3, H4 = P('H0b'), P('H1'), P('H2'), P('H2b'), P('H3'), P('H4')
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with topo(bm, k.log, 'inset', 'eye socket (pass 3: the upper face of the split stop face)'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.012)
    scale(ev, (1.0, 1.0, 0.8))
    move([vert_near(bm, H1[O[1]])], (0.008, -0.012, 0.004))
    move([vert_near(bm, H0b[O[2]])], (0.012, 0.0, 0.0))
    mz = (H2, H2b, H3, H4)
    flatten([vert_near(bm, S[j]) for S in mz for j in (4, 5, 6)])           # flat muzzle side plane
    flatten([vert_near(bm, S[j]) for S in mz for j in (0, 1, 2)])           # flat muzzle top plane
    move([vert_near(bm, H4[j]) for j in (0, 1, 2)], (0.0, -0.012, -0.004))
    move([vert_near(bm, H4[j]) for j in (7, 8, 9)], (0.0, 0.014, 0.0))
    recalc_normals(bm)
    lay = bm.faces.layers.int.new('stripe')
    n = 0
    for f in bm.faces:
        if any(all(v in s for v in f.verts) for s in bands):
            f[lay] = 1; n += 1
    say(f'stripe band faces: {n}')
    commit(body, bm)
    bm.free()


PAL = {'orange': '#d27326', 'stripe': '#2a221e', 'cream': '#eee3cf', 'nose': '#9a5a52',
       'amber': '#e0a030', 'pupil': '#1a1615'}


def body_rule(c, n, s):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.875 and z > 0.79 and x < 0.025:
        return 'nose'
    if z > 1.085 and -0.62 < y < -0.47 and x > 0.10:
        return 'cream' if (n.y < -0.5 and z < 1.115) else 'stripe'       # ears: cream front, dark back
    if y > 0.83:
        return 'stripe'                                  # dark tail tip
    if y < -0.76 and (z < 0.79 or n.z < -0.3):
        return 'cream'                                   # lips and chin
    if -0.67 < y < -0.40 and n.y < -0.3 and z < 0.72 and x < 0.10:
        return 'cream'                                   # throat and chest
    if z < 0.11 and y < 0.55:
        return 'cream'                                   # paws
    if (n.z < -0.4 and z < 0.62) or (-0.30 < y < 0.20 and z < 0.47 and n.z < 0.3):
        return 'cream'                                   # belly and lower flank
    if z < 0.40 and n.y > 0.45 and y < 0.55:
        return 'cream'                                   # backs of the legs
    if s:
        return 'stripe'
    return 'orange'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 3 for k_ in range(6)]]
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def clump(bm, a, n, lay, s, L):
    n, lay = Vector(n).normalized(), Vector(lay).normalized()
    u = n.cross(lay).normalized(); w = u.cross(n)
    b = a - n * 0.03
    base = [bm.verts.new(b + u * su * s + w * sw * s) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    sn = 0.45 * s
    m = a + n * (0.9 * sn) + lay * L * 0.4
    mid = [bm.verts.new(m + u * su * s * 0.8 + n * sv * sn) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    t = a + n * L * 0.32 + lay * L
    tip = [bm.verts.new(t + u * su * s * 0.14 + n * sv * s * 0.12) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    shell = base + mid + tip
    lo = min(v.co.x for v in shell)
    if lo < 0.003:
        for v in shell:
            v.co.x += 0.003 - lo
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip[(j + 1) % 4], tip[j]])
    bm.faces.new(tip)


def surf(a, b, t, jf):
    A, Bq = P(a), P(b)
    j0 = min(int(jf), len(A) - 2); f = jf - j0
    pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
    p = pa.lerp(pb, t)
    ca = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == a][0]))
    cb = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == b][0]))
    return p, (p - ca.lerp(cb, t)).normalized()


def claw(bm, h, d, lead):
    x0 = h.x
    yr, ym, yt = h.y + 0.012, h.y - 0.008 - lead * 0.5, h.y - 0.022 - lead
    xm, xt = x0 + d * 0.1, x0 + d * 0.2
    rows = [[(x0 - 0.012, yr, 0.006), (x0 + 0.012, yr, 0.006), (x0 + 0.012, yr, 0.03), (x0 - 0.012, yr, 0.03)],
            [(xm - 0.009, ym, 0.005), (xm + 0.009, ym, 0.005), (xm + 0.008, ym, 0.022), (xm - 0.008, ym, 0.022)],
            [(xt - 0.004, yt, 0.003), (xt + 0.004, yt, 0.003), (xt + 0.004, yt, 0.008), (xt - 0.004, yt, 0.008)]]
    R = [[bm.verts.new(p) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in ((R[0], R[1]), (R[1], R[2])):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[2])


def stage3(k, body):
    att = body.data.attributes['stripe'].data
    paint(body, PAL, lambda c, n, i: body_rule(c, n, att[i].value))
    bm0 = edit(body); tree = BVHTree.FromBMesh(bm0); bm0.free()
    # eye: small amber lens with a dark pupil, proud of the socket floor
    H0b, H1 = P('H0b'), P('H1')
    fn = (H1[1] - H0b[1]).cross(H0b[2] - H0b[1]).normalized()
    fn = fn if fn.x > 0 else -fn
    c, n, _i, _d = tree.find_nearest(eye_face_centre() - fn * 0.012)
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.019, 0.010)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.008 and n_.dot(n) > 0.5 else 'amber')
    # claws: four per paw, rooted in the paw front
    bm = bmesh.new()
    for sole in (FORE[-1], HIND[-1]):
        (cx, cy, _), rx, ry = sole
        for d in (-0.06, -0.02, 0.02, 0.06):
            o = Vector((cx + d, cy - ry - 0.15, 0.018))
            hit = tree.ray_cast(o, Vector((0, 1, 0)), 0.3)[0]
            h = hit if hit is not None else Vector((cx + d, cy - ry * 0.8, 0.018))
            claw(bm, h, d, 0.004 if abs(d) < 0.02 else 0.0)
    claws = object_from_bm('claws', bm)
    paint(claws, {'stripe': PAL['stripe']}, lambda c_, n_, i: 'stripe')
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
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 5), 'tail2': (0, 0, 6)},
                       20: {'ear.L': (0, 0, -12)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -5), 'tail2': (0, 0, -6)}, 48: {}})
    A = 16
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 4)},
        7: {'forearm.R': (-30, 0, 0), 'paw.R': (-25, 0, 0), 'shin.L': (-18, 0, 0), 'foot.L': (22, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -4)},
        19: {'forearm.L': (-30, 0, 0), 'paw.L': (-25, 0, 0), 'shin.R': (-18, 0, 0), 'foot.R': (22, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 4)}})
    # attack: crouch back, then a pounce-swipe forward with the head down
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-8, 0, 0), 'chest': (4, 0, 0), 'head': (-4, 0, 0), 'tail0': (8, 0, 0)},
        16: {'neck': (16, 0, 0), 'chest': (-10, 0, 0), 'head': (8, 0, 0), 'upperarm.L': (30, 0, 0), 'forearm.L': (-20, 0, 0),
             'ear.L': (-15, 0, 0)},
        20: {'neck': (14, 0, 0), 'chest': (-10, 0, 0), 'head': (16, 0, 0), 'upperarm.L': (10, 0, 0), 'ear.L': (-15, 0, 0)},
        24: {'neck': (12, 0, 0), 'chest': (-4, 0, 0), 'head': (5, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, 0)}, 16: {'hips': (0, 0.06, 0)}, 20: {'hips': (0, 0.06, 0)},
             24: {'hips': (0, 0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
