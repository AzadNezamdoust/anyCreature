import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# Western dragon, t7 hand box-model: one spine loft of 6-vertex half rings (spade tip -> nose), legs extruded as
# 2-face regions from the lower flank, horns as 1-face extrusions from the skull; stage 2 joint rings, eye socket,
# muzzle planes; stage 3 lens eyes, back spikes, folded bat wings (spars + one flat membrane), claws, colour
# along the loops; stage 4 rig and clips.
META = dict(creature='dragon', detail_tier=3, model='opus', stage1_tris=(2400, 3800), total_tris=(3800, 6000),
            closeups=[('head', (0.0, -1.88, 1.48), 0.30, 'hero'),
                      ('front paw', (0.26, -1.48, 0.06), 0.18, 'hero'),
                      ('wing', (0.45, -0.75, 1.05), 0.95, 'hero'),
                      ('tail spade', (0.0, 1.62, 0.22), 0.30, 'hero')])

# the skeleton (x >= 0 half; .L on +X), read off reference/side.png + front.png (head at -Y)
J = dict(
    hips=(0.0, -0.45, 0.60), spine=(0.0, -0.85, 0.70), chest=(0.0, -1.22, 0.74),
    neck=(0.0, -1.50, 0.92), head=(0.0, -1.78, 1.44), nose=(0.0, -2.02, 1.38),
    tail0=(0.0, -0.22, 0.48), tail1=(0.0, 0.30, 0.31), tail2=(0.0, 0.85, 0.19), tail3=(0.0, 1.45, 0.21),
    tailtip=(0.0, 1.84, 0.215),
    shoulder=(0.24, -1.36, 0.72), elbow=(0.27, -1.37, 0.42), wrist=(0.26, -1.40, 0.11),
    fpaw=(0.26, -1.44, 0.03), ftoe=(0.26, -1.60, 0.02),
    hipL=(0.24, -0.55, 0.62), knee=(0.28, -0.62, 0.40), hock=(0.26, -0.46, 0.15),
    hpaw=(0.26, -0.55, 0.03), htoe=(0.26, -0.70, 0.02),
    horn=(0.12, -1.77, 1.62), horntip=(0.21, -1.56, 1.80),
)

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = [(0, 1), (0.6, 0.92), (1, 0.3), (0.88, -0.35), (0.5, -0.8), (0, -1)]
CHEST = [(0, 1), (0.65, 0.9), (1, 0.35), (0.85, -0.3), (0.4, -0.8), (0, -1)]
NECK = [(0, 1), (0.65, 0.9), (1, 0.2), (0.85, -0.45), (0.45, -0.85), (0, -1)]
HEADB = [(0, 1), (0.75, 0.97), (1, 0.4), (0.85, -0.4), (0.5, -0.85), (0, -1)]
HEAD = [(0, 1), (0.75, 0.93), (1, 0.3), (0.85, -0.4), (0.5, -0.85), (0, -1)]
HEADF = [(0, 1), (0.75, 0.88), (1, 0.1), (0.85, -0.45), (0.5, -0.85), (0, -1)]
MUZ = [(0, 1), (0.65, 0.95), (1, 0.4), (0.95, -0.3), (0.6, -0.85), (0, -1)]
TAIL = [(0, 1), (0.7, 0.7), (1, 0.1), (0.8, -0.5), (0.4, -0.9), (0, -1)]
SPADE = [(0, 1), (0.35, 0.6), (1, 0.05), (0.5, -0.5), (0.35, -0.88), (0, -1)]       # pass 3: fuller underside (no needle quads)


def roundp(p):
    """Density pass 3: 6 -> 14 points per half ring. Catmull-Rom points (ring mirrored across the seam) go into
    each span: 1 into the top and bottom spans, 2 into each of the three side spans, so the cross-section reads
    round. Old point i sits at new index O[i]."""
    m = [(-p[1][0], p[1][1])] + list(p) + [(-p[4][0], p[4][1])]
    out = []
    for i in range(5):
        out.append(p[i])
        a, b, c, d = m[i], m[i + 1], m[i + 2], m[i + 3]
        ts = (0.5,) if i in (0, 4) else (1 / 3, 2 / 3)
        for t in ts:
            t2, t3 = t * t, t * t * t
            w = (-0.5 * t3 + t2 - 0.5 * t, 1.5 * t3 - 2.5 * t2 + 1, -1.5 * t3 + 2 * t2 + 0.5 * t, 0.5 * t3 - 0.5 * t2)
            out.append(tuple(round(w[0] * a[j] + w[1] * b[j] + w[2] * c[j] + w[3] * d[j], 4) for j in range(2)))
    out.append(p[5])
    return out


O = {0: 0, 1: 2, 2: 5, 3: 8, 4: 11, 5: 13}
BODY, CHEST, NECK, HEADB, HEAD, HEADF, MUZ, TAIL, SPADE = [roundp(q) for q in (BODY, CHEST, NECK, HEADB, HEAD, HEADF, MUZ, TAIL, SPADE)]


def eyeface(p):
    """Pass 5: the eye face (ring points 3-4 in the upper side span 2-5) takes 70 % of that span, so a larger
    round eye fits in one clean socket."""
    p = list(p)
    a, b = p[2], p[5]
    for i, t in ((3, 0.15), (4, 0.85)):
        p[i] = tuple(round(a[j] + (b[j] - a[j]) * t + (0.04 if j == 0 else 0.0), 4) for j in range(2))
    return p


HEADB, HEAD, HEADF = eyeface(HEADB), eyeface(HEAD), eyeface(HEADF)


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
    py, pz = d[1] / l, -d[0] / l
    if pz < 0:
        py, pz = -py, -pz
    return tb(nm, (c[0] + py * h, c[1] + pz * h), (c[0] - py * h, c[1] - pz * h), W, prof)


# density pass 3: the tail centreline (name, y, z, half height, half width), refitted to the sheet's side view (the
# sheet's tail is lower and 15-40 % thicker than the old fit); stations about 1.8 radii apart (no needle quads)
TAILK = [('T2', 1.44, 0.222, 0.050, 0.052), ('T3', 1.17, 0.188, 0.062, 0.066), ('T4', 0.78, 0.172, 0.083, 0.087),
         ('T5', 0.42, 0.205, 0.108, 0.110), ('T6', 0.08, 0.345, 0.137, 0.137)]
TAILMID = {('T2', 'T3'): [(1.36, 0.209, 0.053), (1.27, 0.197, 0.057)],                 # sheet columns between knots
           ('T3', 'T4'): [(1.05, 0.178, 0.068), (0.92, 0.172, 0.075)],
           ('T4', 'T5'): [(0.60, 0.183, 0.096)], ('T5', 'T6'): [(0.25, 0.250, 0.122)]}


def _tailc():
    """Stations between the knots about 1.35 radii apart (a quad on a 14-point ring stays above 6 deg), each one
    read off the sheet's tail line (piecewise through the sheet columns), W/h as at the knots."""
    out = []
    for (n0, y0, z0, h0, w0), (n1, y1, z1, h1, w1) in zip(TAILK, TAILK[1:]):
        out.append((n0, y0, z0, h0, w0))
        line = [(y0, z0, h0)] + TAILMID[(n0, n1)] + [(y1, z1, h1)]
        k = max(2, math.ceil((y0 - y1) / (1.35 * min(h0, h1))))
        for j in range(1, k):
            y = y0 + (y1 - y0) * j / k
            for (ya, za, ha), (yb, zb, hb) in zip(line, line[1:]):
                if yb <= y <= ya:
                    t = (ya - y) / (ya - yb)
                    z, h = za + (zb - za) * t, ha + (hb - ha) * t
            r = w0 / h0 + (w1 / h1 - w0 / h0) * j / k
            out.append((f'{n0}_{j}', round(y, 4), round(z, 4), round(h, 4), round(h * r, 4)))
    out.append(TAILK[-1])
    return out


TAILC = _tailc()


def tail_secs():
    out = []
    for i, (nm, y, z, h, W) in enumerate(TAILC):
        p = TAILC[max(0, i - 1)]; q = TAILC[min(len(TAILC) - 1, i + 1)]
        out.append(ax(nm, (y, z), (p[1] - q[1], p[2] - q[2]), h, W))
    return out


# the spine loft, spade tip -> nose (pass 3: 23 -> 40 stations; the new ones sit where the side line curves)
SECS = [
    ax('T0', (1.80, 0.232), (1.0, 0.0), 0.05, 0.055, SPADE),    # pass 3: blunt tip built in (was a x3 scale in s2)
    tb('T0b', (1.74, 0.31), (1.74, 0.155), 0.075, SPADE),        # pass 3: the spade's rear blade (sheet)
    tb('T0c', (1.64, 0.357), (1.64, 0.105), 0.095, SPADE),   # pass 3: spade a wider diamond (top view)
    tb('T1', (1.53, 0.382), (1.53, 0.074), 0.10, SPADE),          # the spade's barbs
    *tail_secs(),
    tb('R0t', (-0.05, 0.54), (-0.07, 0.21), 0.21, BODY),         # pass 3: tail root (sheet 0.19-0.53)
    tb('R0', (-0.18, 0.64), (-0.22, 0.30), 0.26, BODY),
    tb('R0b', (-0.29, 0.695), (-0.31, 0.33), 0.31, BODY),        # pass 3: rump curve
    tb('R1', (-0.38, 0.76), (-0.42, 0.37), 0.35, BODY),
    tb('R2', (-0.56, 0.83), (-0.62, 0.41), 0.34, BODY),
    tb('R2b', (-0.66, 0.862), (-0.71, 0.42), 0.34, BODY),        # pass 3: belly tuck behind the ribs
    tb('W0', (-0.74, 0.89), (-0.82, 0.45), 0.335, BODY),
    tb('W0b', (-0.83, 0.915), (-0.95, 0.40), 0.355, BODY),         # pass 3: deeper belly (sheet 0.39 at y -0.95)
    tb('M0', (-0.92, 0.94), (-1.08, 0.40), 0.37, BODY),
    tb('M0b', (-1.00, 0.962), (-1.19, 0.392), 0.39, CHEST),      # pass 3: ribcage into the shoulder
    tb('C0', (-1.08, 0.98), (-1.30, 0.39), 0.41, CHEST),
    tb('C1', (-1.25, 1.03), (-1.58, 0.44), 0.36, CHEST),
    tb('C1b', (-1.33, 1.11), (-1.645, 0.555), 0.30, CHEST),     # pass 3: round chest front, shoulder into neck
    tb('N0', (-1.40, 1.20), (-1.68, 0.70), 0.225, NECK),        # fix pass 1: neck +45%, three rings, head raised 0.20 m
    tb('N0b', (-1.46, 1.29), (-1.73, 0.85), 0.205, NECK),        # pass 3: neck curve
    tb('N1', (-1.52, 1.38), (-1.76, 1.00), 0.185, NECK),
    tb('N1b', (-1.58, 1.455), (-1.785, 1.10), 0.16, NECK),      # pass 3: throat curve
    tb('N2', (-1.64, 1.52), (-1.80, 1.20), 0.15, NECK),
    tb('H0', (-1.74, 1.59), (-1.81, 1.31), 0.175, HEADB),   # fix pass 2: head W x1.2
    tb('H0b', (-1.815, 1.575), (-1.855, 1.305), 0.17, HEAD),
    tb('H1', (-1.905, 1.515), (-1.915, 1.31), 0.14, HEADF),
    tb('H1b', (-1.935, 1.49), (-1.94, 1.315), 0.12, HEADF),     # pass 3: brow into the muzzle
    tb('H2', (-1.96, 1.46), (-1.96, 1.318), 0.104, MUZ),
    tb('H2b', (-1.98, 1.447), (-1.98, 1.325), 0.093, MUZ),      # pass 3: muzzle bridge
    tb('H3', (-1.998, 1.432), (-1.998, 1.332), 0.08, MUZ),
    tb('H4', (-2.025, 1.412), (-2.022, 1.352), 0.062, MUZ),
]

# limb sections: (centre xyz, rx, ry) — horizontal hexagons, deeper front-to-back
# pass 3: 14-vertex leg rings (6-face root strip) and a forearm, pastern, gaskin and cannon station each
# pass 5: legs 5 cm out with the wider torso and 20-30 % thicker (the sheet's heavy pillars)
# pass 6 (owner crop 2): wrist and hock were the narrowest rings (a pinched band over a flared paw); filled out
# to a steady taper into the paw
_FORE = [(J['elbow'], 0.156, 0.192), ((0.27, -1.36, 0.26), 0.134, 0.158), ((0.265, -1.38, 0.18), 0.126, 0.146),
        (J['wrist'], 0.122, 0.144), ((0.26, -1.43, 0.08), 0.12, 0.154),
        ((0.26, -1.45, 0.05), 0.12, 0.168), ((0.26, -1.46, 0.0), 0.132, 0.192)]
_HIND = [((0.29, -0.62, 0.40), 0.185, 0.276), ((0.27, -0.52, 0.27), 0.145, 0.172), ((0.265, -0.49, 0.21), 0.112, 0.125),
        (J['hock'], 0.10, 0.105), ((0.26, -0.49, 0.11), 0.097, 0.106),
        ((0.26, -0.52, 0.07), 0.096, 0.11), ((0.26, -0.57, 0.035), 0.10, 0.13), ((0.26, -0.58, 0.0), 0.11, 0.15)]
LEGX = 0.05
LEGJ = ('shoulder', 'elbow', 'wrist', 'fpaw', 'ftoe', 'hipL', 'knee', 'hock', 'hpaw', 'htoe')
# pass 7 (owner: legs too thick and heavy): explicit (rx, ry) per ring, the elbow/thigh rings kept, the forearm,
# shin and ankle slimmed 10-20 % to a clear taper; below the wrist/hock the rings only widen into the paw (no pinch)
_FR = [(0.190, 0.227), (0.150, 0.168), (0.136, 0.152), (0.128, 0.146), (0.130, 0.158), (0.140, 0.188), (0.161, 0.227)]
_HR = [(0.200, 0.304), (0.160, 0.188), (0.120, 0.136), (0.107, 0.115), (0.106, 0.116), (0.110, 0.126), (0.120, 0.152), (0.1375, 0.183)]
FORE = [((c[0] + LEGX, c[1], c[2]), rx, ry) for (c, _a, _b), (rx, ry) in zip(_FORE, _FR)]
HIND = [((c[0] + LEGX, c[1], c[2]), rx, ry) for (c, _a, _b), (rx, ry) in zip(_HIND, _HR)]
HORN = [((0.12, -1.765, 1.63), 0.05, 0.055, 0.012), ((0.17, -1.68, 1.715), 0.034, 0.036, 0.006),
        ((0.19, -1.62, 1.758), 0.026, 0.027, 0.003), ((0.21, -1.56, 1.80), 0.018, 0.018, 0.0)]
HORN = [((c[0] + 0.02, c[1], c[2] + 0.01), rx, ry, dz) for c, rx, ry, dz in HORN]      # pass 5: out with the wider skull                 # pass 3: blunt tip built in (was a x2.5 scale in s2)


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
    k = math.sqrt(max(0.0, 1.0 - (1.0 - corner * corner) * u * u))     # pass 3: elliptical for the in-between roles
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
    ends = [cap(bm, rings[0]), cap(bm, rings[-1])]
    bmesh.ops.poke(bm, faces=ends)                 # pass 3: 14-point end caps fan from a centre (no needle fan)
    recalc_normals(bm)

    def limb(span_name, secs):
        i = idx[span_name]
        rr, rf = rings[i], rings[i + 1]
        us = (1, 2 / 3, 1 / 3, 0, -1 / 3, -2 / 3, -1)
        roles = {**{rf[5 + j]: (u, -1) for j, u in enumerate(us)}, **{rr[5 + j]: (u, 1) for j, u in enumerate(us)}}
        grow(bm, [spans[i][j] for j in range(5, 11)], roles, secs)

    limb('C0', FORE)
    limb('R1', HIND)
    i = idx['H0']
    rr, rf = rings[i], rings[i + 1]
    us = (-1, -1 / 3, 1 / 3, 1)
    grow(bm, [spans[i][j] for j in range(2, 5)], {**{rf[2 + j]: (u, -1) for j, u in enumerate(us)},
                                                   **{rr[2 + j]: (u, 1) for j, u in enumerate(us)}}, HORN, corner=1.0)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    H0b, H1 = P('H0b'), P('H1')
    return (H0b[3] + H0b[4] + H1[3] + H1[4]) / 4       # pass 3: the middle of the three stop faces


def stage2(k, body):
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ec0 = eye_face_centre()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    with topo(bm, k.log, 'loop', 'elbow ring: the bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(FORE[0], 1, 1), role_pos(FORE[1], 1, 1))), t=0.5)
    with topo(bm, k.log, 'loop', 'stifle ring: the bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(HIND[0], 1, 1), role_pos(HIND[1], 1, 1))), t=0.5)
    with topo(bm, k.log, 'loop', 'neck-skull ring: the head turn'):
        loopcut(bm, edge_near(bm, mid(P('N2')[0], P('H0')[0])), t=0.5)
    # pass 3: the s2 r2 tail loops and tip scales are gone: the new s1 tail stations and blunt tips do that job
    H0b, H1, H2, H2b, H3, H4 = P('H0b'), P('H1'), P('H2'), P('H2b'), P('H3'), P('H4')
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with topo(bm, k.log, 'inset', 'eye socket'):
        inner = inset(bm, [f], 0.16, 0.0)         # pass 5: a wide clean socket
    ev = list(inner[0].verts)
    move(ev, -fn * 0.014)
    scale(ev, (1.0, 1.0, 0.8))
    move([vert_near(bm, H1[2])], (0.01, -0.012, 0.006))           # brow corner forward and out
    move([vert_near(bm, H0b[5])], (0.012, 0.0, 0.0))              # cheekbone out
    flatten([vert_near(bm, R[j]) for R in (H2, H2b, H3, H4) for j in range(5, 9)])       # flat muzzle side
    flatten([vert_near(bm, R[j]) for R in (H2, H2b, H3, H4) for j in range(0, 3)])       # flat muzzle top
    move([vert_near(bm, H4[j]) for j in range(0, 3)], (0.0, -0.012, -0.004))
    move([vert_near(bm, H4[j]) for j in range(11, 14)], (0.0, 0.016, 0.0))
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'red': '#9a2b25', 'belly': '#d8ad7c', 'bone': '#ece0c4', 'amber': '#e8a820', 'pupil': '#1a1412',
       'membrane': '#d2a06c'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -1.3 and z > 1.615:
        return 'bone'                                    # horns
    if -1.84 < y < -1.2 and z < 1.34 and x < 0.12 and n.dot(Vector((0, -0.72, -0.69))) > 0.25:
        return 'belly'                                   # pass 5: one clean throat-chest band (ventral facing)
    if -1.4 < y < -0.3 and n.z < -0.45 and z < 0.55 and x < 0.2:
        return 'belly'                                   # belly
    if y > -0.3 and n.z < -0.35 and y < 1.46 and x < 0.12:
        return 'belly'                                   # tail underside
    return 'red'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 5 for k_ in range(10)]]      # pass 5: 10 sides, reads round
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(10):
        a, b = j, (j + 1) % 10
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def _orient(bm, faces, centre):
    for f in faces:
        if f.normal.dot(f.calc_center_median() - centre) < 0:
            f.normal_flip()


def spike(bm, p, up, back, L, H, s):
    """A half spike on the mirror seam (x >= 0; the Mirror closes it): a base sunk 3 cm under the seam point p,
    L long and s wide, its tip H out along `up`, swept back."""
    up, back = Vector(up).normalized(), Vector(back).normalized()
    F = p - back * L * 0.5 - up * 0.03
    R = p + back * L * 0.5 - up * 0.03
    T = p + up * H + back * H * 0.55
    X = Vector((s, 0, 0))
    F0, R0, T0 = bm.verts.new(F), bm.verts.new(R), bm.verts.new(T)
    F1, R1 = bm.verts.new(F + X + up * 0.01), bm.verts.new(R + X + up * 0.01)
    M = bm.verts.new(p + up * H * 0.35 + back * L * 0.15 + X * 0.55)
    fs = [bm.faces.new([F0, F1, R1, R0]), bm.faces.new([F0, T0, M, F1]), bm.faces.new([F1, M, R1]),
          bm.faces.new([R1, M, T0, R0])]
    for f in fs:
        f.normal_update()
    _orient(bm, fs, (F + R) / 2 + up * H * 0.25 + X * 0.15)


def prism(bm, a, b, ra, rb, up=(0, 0, 1)):
    """A 4-sided closed spar from a to b, half-sizes ra at a and rb at b."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    u = d.cross(Vector(up))
    u = u.normalized() if u.length > 1e-4 else d.orthogonal().normalized()
    w = d.cross(u).normalized()
    A = [bm.verts.new(a + (u * cu + w * cw) * ra) for cu, cw in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    B = [bm.verts.new(b + (u * cu + w * cw) * rb) for cu, cw in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    nseg = max(1, math.ceil((b - a).length / 0.12))      # s3 r2: short segments (no needle sides)
    rings_ = [A]
    for j_ in range(1, nseg):
        c_ = a.lerp(b, j_ / nseg); r_ = ra + (rb - ra) * j_ / nseg
        rings_.append([bm.verts.new(c_ + (u * cu + w * cw) * r_) for cu, cw in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    rings_.append(B)
    fs = [bm.faces.new(list(reversed(A))), bm.faces.new(B)]
    for R0_, R1_ in zip(rings_, rings_[1:]):
        for j in range(4):
            fs.append(bm.faces.new([R0_[j], R0_[(j + 1) % 4], R1_[(j + 1) % 4], R1_[j]]))
    for f in fs:
        f.normal_update()
    for f in fs:
        fc = f.calc_center_median()
        ax_ = a + d * max(0.0, min((b - a).length, (fc - a).dot(d)))
        if f in fs[:2]:
            ax_ = (a + b) / 2
        if f.normal.dot(fc - ax_) < 0:
            f.normal_flip()
    return fs


def spar(bm, pts, rs, up=(0, 0, 1)):
    """pass 6 (owner crop 1): a 4-sided spar along a polyline; the bend shares one mitred ring (the two butted
    prisms left a stepped notch at the elbow)."""
    pts = [Vector(p) for p in pts]
    ds = [(b - a).normalized() for a, b in zip(pts, pts[1:])]
    def fr(d):
        u = d.cross(Vector(up)); u = u.normalized() if u.length > 1e-4 else d.orthogonal().normalized()
        return u, d.cross(u).normalized()
    C = ((1, 1), (-1, 1), (-1, -1), (1, -1))
    rings_ = []
    for j, (p, r) in enumerate(zip(pts, rs)):
        if 0 < j < len(pts) - 1:
            d = (ds[j - 1] + ds[j]).normalized(); m = 1.0 / max(0.75, ds[j - 1].dot(d))
        else:
            d = ds[min(j, len(ds) - 1)]; m = 1.0
        u, w = fr(d)
        if j > 0:
            a, b = pts[j - 1], p
            nseg = max(1, math.ceil((b - a).length / 0.12))
            for k_ in range(1, nseg):
                c_ = a.lerp(b, k_ / nseg); r_ = rs[j - 1] + (r - rs[j - 1]) * k_ / nseg
                u2, w2 = fr(ds[j - 1])
                rings_.append([bm.verts.new(c_ + (u2 * cu + w2 * cw) * r_) for cu, cw in C])
        rings_.append([bm.verts.new(p + (u * cu + w * cw) * r * m) for cu, cw in C])
    fs = [bm.faces.new(list(reversed(rings_[0]))), bm.faces.new(rings_[-1])]
    for R0_, R1_ in zip(rings_, rings_[1:]):
        for j in range(4):
            fs.append(bm.faces.new([R0_[j], R0_[(j + 1) % 4], R1_[(j + 1) % 4], R1_[j]]))
    for f in fs:
        f.normal_update()
    def near(c):
        best = None
        for a, b in zip(pts, pts[1:]):
            d = b - a; t_ = max(0.0, min(1.0, (c - a).dot(d) / d.length_squared)); q = a + d * t_
            if best is None or (c - q).length < (c - best).length:
                best = q
        return best
    for f in fs:
        fc = f.calc_center_median()
        ax_ = near(fc) if f not in fs[:2] else (pts[0] * 0.8 + pts[1] * 0.2 if f is fs[0] else pts[-1] * 0.8 + pts[-2] * 0.2)
        if f.normal.dot(fc - ax_) < 0:
            f.normal_flip()
    return fs


def cone(bm, a, b, r, up=(0, 0, 1)):
    """A 4-sided claw: square root at a (half-size r), point at b."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    u = d.cross(Vector(up))
    u = u.normalized() if u.length > 1e-4 else d.orthogonal().normalized()
    w = d.cross(u).normalized()
    A = [bm.verts.new(a + (u * cu + w * cw) * r) for cu, cw in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    T = bm.verts.new(b)
    fs = [bm.faces.new(list(reversed(A)))]
    for j in range(4):
        fs.append(bm.faces.new([A[j], A[(j + 1) % 4], T]))
    for f in fs:
        f.normal_update()
    _orient(bm, fs, a * 0.7 + b * 0.3)
    return fs


# the folded wing (x >= 0 half): wrist high over the shoulder, three finger spars swept back over the flank and
# tail root, one flat membrane between them; the root edge sinks into the back
# fix pass 1: shoulder raised, an elbow, wrist high and out, fingers opened down and out (two panels: arm | hand)
# fix pass 2: root forward over the shoulders, wrist higher and wider, fingers spread wider (bigger wing)
WING = dict(root=(0.10, -1.10, 0.92), E=(0.36, -1.08, 1.26), Rf=(0.15, -1.07, 0.95), W=(0.55, -0.76, 1.66),
            F1=(0.70, 0.22, 0.46), S1=(0.66, -0.04, 0.72), F2=(0.74, -0.30, 0.52), S2=(0.68, -0.46, 0.80),
            F3=(0.68, -0.66, 0.80), S3=(0.54, -0.74, 1.02), Rr=(0.14, -0.82, 0.90))


def wing_bm():
    """Returns the half bmesh and the face-index sets: spars (red), membrane (tan), claws (bone)."""
    bm = bmesh.new()
    G = {k_: Vector(v) for k_, v in WING.items()}
    out = ['W', 'F1', 'S1', 'F2', 'S2', 'F3', 'S3', 'Rr', 'Rf']
    n = (G['F1'] - G['W']).cross(G['Rr'] - G['W']).normalized()
    n = n if n.x > 0 else -n
    # s3 r2: a lens membrane - rim vertices shared by both sides, interior split +-t along n - fanned on rays
    # from the wrist in 8 steps (r1's thin side walls and long fan triangles were needle triangles)
    # pass 6 (owner crop 1): the shared zero-thickness rim read as a paper edge; every rim point is now split
    # +-tr along n and closed by a wall strip, so the membrane has a 12 mm edge all round
    t, tr, N = 0.01, 0.006, 8
    rays = ['F1', 'F2', 'F3', 'Rr', 'Rf']               # s3 r3: scallops are rim points, not rays (6-deg fan apexes)
    # pass 7 (owner crop 3): the leading edge ran straight W-Rf under the bent arm spar (W-E-root), an open
    # see-through triangle at the wing root; a last ray to the elbow E plus a rim point Q half way down the spar
    # make the rim follow the spar W-E-Q-Rf, all inside the spar; that rim runs 26 mm thick (in the 35-40 mm spar)
    # so its long wall quads stay above the sliver angle
    G['Q'] = (G['E'] + G['root']) * 0.5
    rays.append('E')
    scal = {0: 'S1', 1: 'S2', 2: 'S3', 4: 'Q'}
    te = 0.013
    Wv = {1: bm.verts.new(G['W'] + n * tr), -1: bm.verts.new(G['W'] - n * tr)}
    pts = {}
    for i, r in enumerate(rays):
        for kk in range(1, N + 1):
            p = G['W'].lerp(G[r], kk / N)
            tt = tr if (kk == N or i in (0, len(rays) - 1)) else t
            if r == 'E' or (r == 'Rf' and kk == N):
                tt = te
            pts[(i, kk, 1)] = bm.verts.new(p + n * tt); pts[(i, kk, -1)] = bm.verts.new(p - n * tt)
    Sv = {(i, sd): bm.verts.new(G[sn] + n * (te if sn == 'Q' else tr) * sd) for i, sn in scal.items() for sd in (1, -1)}
    for i in range(len(rays) - 1):
        for sd in (1, -1):
            q = lambda a, b: pts[(a, b, sd)]
            fs = [[Wv[sd], q(i, 1), q(i + 1, 1)]] + [[q(i, kk), q(i, kk + 1), q(i + 1, kk + 1), q(i + 1, kk)] for kk in range(1, N - 1)]
            if i in scal and scal[i] == 'Q':     # pass 7: quad + triangle, not a 5-gon (its fan made needle triangles)
                fs += [[q(i, N - 1), q(i, N), Sv[(i, sd)], q(i + 1, N - 1)], [q(i + 1, N - 1), Sv[(i, sd)], q(i + 1, N)]]
            elif i in scal:
                fs.append([q(i, N - 1), q(i, N), Sv[(i, sd)], q(i + 1, N), q(i + 1, N - 1)])
            else:
                fs.append([q(i, N - 1), q(i, N), q(i + 1, N), q(i + 1, N - 1)])
            for f in fs:
                bm.faces.new(f if sd == 1 else list(reversed(f)))
    L = len(rays) - 1
    loop = ['W'] + [(0, kk) for kk in range(1, N + 1)]
    for i in range(1, L + 1):
        if i - 1 in scal:
            loop.append(('S', i - 1))
        loop.append((i, N))
    loop += [(L, kk) for kk in range(N - 1, 0, -1)]
    def rv(key, sd):
        return Wv[sd] if key == 'W' else Sv[(key[1], sd)] if key[0] == 'S' else pts[(key[0], key[1], sd)]
    for a_, b_ in zip(loop, loop[1:] + loop[:1]):
        bm.faces.new([rv(a_, 1), rv(b_, 1), rv(b_, -1), rv(a_, -1)])
    recalc_normals(bm)
    nm = len(bm.faces)
    sp = []
    sp += spar(bm, [G['root'], G['E'], G['W']], [0.04, 0.035, 0.03])      # pass 6: one bent arm spar (no elbow notch)
    for f in ('F1', 'F2', 'F3'):
        tip = G[f]
        sp += prism(bm, G['W'] + (tip - G['W']).normalized() * -0.02, tip, 0.022, 0.012)
    cl = []
    cl += cone(bm, G['W'] + Vector((0, 0.01, 0)), G['W'] + Vector((0.01, -0.13, 0.04)), 0.03)   # thumb claw
    for f in ('F1', 'F2', 'F3'):
        d = (G[f] - G['W']).normalized()
        cl += cone(bm, G[f] - d * 0.02, G[f] + d * 0.08, 0.016)
    bm.faces.index_update()
    idx_sp = set(range(nm, nm + len(sp)))
    idx_cl = set(range(nm + len(sp), len(bm.faces)))
    return bm, idx_sp, idx_cl


def claw(bm, h, d, s=1.6):
    x0 = h.x
    yr, ym, yt = h.y + 0.012 * s, h.y - 0.008 * s, h.y - 0.024 * s
    xm, xt = x0 + d * 0.1, x0 + d * 0.2
    rows = [[(x0 - 0.012 * s, yr, 0.014), (x0 + 0.012 * s, yr, 0.014), (x0 + 0.012 * s, yr, 0.03 * s), (x0 - 0.012 * s, yr, 0.03 * s)],
            [(xm - 0.009 * s, ym, 0.012), (xm + 0.009 * s, ym, 0.012), (xm + 0.008 * s, ym, 0.022 * s), (xm - 0.008 * s, ym, 0.022 * s)],
            [(xt - 0.004 * s, yt, 0.009), (xt + 0.004 * s, yt, 0.009), (xt + 0.004 * s, yt, 0.017), (xt - 0.004 * s, yt, 0.017)]]
    R = [[bm.verts.new(p) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in ((R[0], R[1]), (R[1], R[2])):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[2])


# back spikes along the top seam: (rear section, front section, t from rear, height, length)
SPIKES = [('N1', 'N2', 0.5, 0.10, 0.10), ('N0', 'N1', 0.5, 0.12, 0.12), ('C0', 'C1', 0.5, 0.14, 0.14),   # fix pass 1: 10 larger
          ('W0', 'M0', 0.5, 0.13, 0.14), ('R1', 'R2', 0.5, 0.13, 0.14), ('T6', 'R0', 0.3, 0.13, 0.14),
          ('T5', 'T6', 0.5, 0.12, 0.13), ('T4', 'T5', 0.5, 0.11, 0.12), ('T3', 'T4', 0.5, 0.095, 0.11),
          ('T2', 'T3', 0.5, 0.08, 0.09)]


def seam_at(a, b, t):
    names = [n for (n, *_r) in SECS]
    ia, ib = names.index(a), names.index(b)
    step = 1 if ib > ia else -1
    pts = [P(names[q])[0] for q in range(ia, ib + step, step)]
    L = [0.0]
    for p_, q_ in zip(pts, pts[1:]):
        L.append(L[-1] + (q_ - p_).length)
    s_ = t * L[-1]
    for q in range(len(pts) - 1):
        if L[q + 1] >= s_:
            return pts[q].lerp(pts[q + 1], (s_ - L[q]) / max(1e-9, L[q + 1] - L[q]))
    return pts[-1]


def stage3(k, body):
    paint(body, PAL, body_rule)
    bm0 = edit(body); tree = BVHTree.FromBMesh(bm0); bm0.free()
    # eye: small amber lens with a dark pupil, proud of the socket floor
    H0b, H1 = P('H0b'), P('H1')
    fn = (H1[3] - H0b[3]).cross(H0b[4] - H0b[3]).normalized()
    fn = fn if fn.x > 0 else -fn
    c, n, _i, _d = tree.find_nearest(eye_face_centre() - fn * 0.014)
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.024, 0.013)               # pass 5: larger round lens
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.011 and n_.dot(n) > 0.5 else 'amber')
    # back spikes: one row on the seam from the nape to the spade
    bm = bmesh.new()
    for a, b, t, H, L in SPIKES:
        pa, pb = P(a)[0], P(b)[0]
        p = seam_at(a, b, t)                        # pass 3: on the seam through the new stations
        d = (pb - pa).normalized()                  # toward the head
        up = Vector((0.0, -d.z, d.y)) if d.y < 0 else Vector((0.0, d.z, -d.y))
        up = up if up.z > 0 else -up
        spike(bm, p, up, -d, L, H, 0.035 * L / 0.1)
    spikes = object_from_bm('spikes', bm)
    paint(spikes, {'bone': PAL['bone']}, lambda c_, n_, i: 'bone')
    # wings
    bm, isp, icl = wing_bm()
    wing = object_from_bm('wing', bm)
    paint(wing, {'red': PAL['red'], 'membrane': PAL['membrane'], 'bone': PAL['bone']},
          lambda c_, n_, i: 'red' if i in isp else ('bone' if i in icl else 'membrane'))
    # claws: four per paw, rooted in the paw front
    bm = bmesh.new()
    for sole in (FORE[-1], HIND[-1]):
        (cx, cy, _), rx, ry = sole
        for d in (-0.075, -0.025, 0.025, 0.075):
            o = Vector((cx + d, cy - ry - 0.2, 0.025))
            hit = tree.ray_cast(o, Vector((0, 1, 0)), 0.4)[0]
            h = hit if hit is not None else Vector((cx + d, cy - ry * 0.8, 0.025))
            claw(bm, h, d)
    claws = object_from_bm('claws', bm)
    paint(claws, {'bone': PAL['bone']}, lambda c_, n_, i: 'bone')
    return [eye, spikes, wing, claws]


def stage4(k, body, pieces):
    J = {n: ((p[0] + LEGX, p[1], p[2]) if n in LEGJ else (p[0] + 0.02, p[1], p[2] + 0.01) if n.startswith('horn') else p)
         for n, p in globals()['J'].items()}   # pass 5: legs and horns out
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('horn.L', J['horn'], J['horntip'], 'head'),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('tail3', J['tail3'], J['tailtip'], 'tail2', True),
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
        if p.name.endswith('wing'):
            bind(p, rig, bone='spine')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-2, 0, 0), 'tail1': (0, 0, 4), 'tail2': (0, 0, 5)},
                       24: {'head': (3, 0, 0)}, 36: {'chest': (1.5, 0, 0), 'neck': (-2, 0, 0), 'tail1': (0, 0, -4),
                                                     'tail2': (0, 0, -5)}, 48: {}})
    A = 14
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 4)},
        7: {'forearm.R': (-28, 0, 0), 'paw.R': (-22, 0, 0), 'shin.L': (-16, 0, 0), 'foot.L': (20, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -4)},
        19: {'forearm.L': (-28, 0, 0), 'paw.L': (-22, 0, 0), 'shin.R': (-16, 0, 0), 'foot.R': (20, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 4)}})
    # attack: rear the neck back, then a head-down lunge and bite, tail lashing
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-12, 0, 0), 'chest': (4, 0, 0), 'head': (-6, 0, 0), 'tail1': (0, 0, 6)},
        16: {'neck': (18, 0, 0), 'chest': (-8, 0, 0), 'head': (10, 0, 0), 'tail1': (0, 0, -6)},
        20: {'neck': (16, 0, 0), 'chest': (-8, 0, 0), 'head': (18, 0, 0)},
        24: {'neck': (10, 0, 0), 'chest': (-4, 0, 0), 'head': (5, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.03, 0)}, 16: {'hips': (0, -0.06, 0)}, 20: {'hips': (0, -0.06, 0)},
             24: {'hips': (0, -0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
