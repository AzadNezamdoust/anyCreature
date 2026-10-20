import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# red deer stag, t7 hand box model: one spine loft of 6-vertex half rings (tail tip -> nose), legs extruded from
# 2-face flank regions, ears and antler beams extruded from 1-face skull regions; tines, eyes and the neck mane are
# stage-3 pieces.
META = dict(creature='stag', model='opus', stage1_tris=(1200, 3600), total_tris=(2400, 5200),
            closeups=[('head', (0.0, -0.92, 1.38), 0.22, 'hero'),
                      ('antlers', (0.0, -0.62, 1.75), 0.42, 'hero'),
                      ('front hoof', (0.16, -0.34, 0.06), 0.1, 'hero'),
                      ('hind hoof', (0.14, 1.03, 0.06), 0.1, 'hero')])

J = dict(
    hips=(0.0, 0.70, 1.05), spine=(0.0, 0.15, 1.0), chest=(0.0, -0.33, 1.0),
    neck=(0.0, -0.52, 1.12), head=(0.0, -0.78, 1.40), nose=(0.0, -1.10, 1.29),
    tail0=(0.0, 1.03, 1.02), tail1=(0.0, 1.09, 0.80),
    shoulder=(0.17, -0.30, 0.85), elbow=(0.17, -0.29, 0.52), wrist=(0.16, -0.31, 0.23),
    fpaw=(0.16, -0.33, 0.06), ftoe=(0.16, -0.40, 0.0),
    hipL=(0.17, 0.80, 0.92), knee=(0.17, 0.80, 0.60), hock=(0.14, 1.06, 0.38),
    hpaw=(0.14, 1.01, 0.07), htoe=(0.14, 0.94, 0.0),
    ear=(0.12, -0.76, 1.44), eartip=(0.34, -0.77, 1.53),
)

BODY = [(0, 1), (0.6, 0.92), (1, 0.3), (0.85, -0.35), (0.45, -0.8), (0, -1)]
CHEST = [(0, 1), (0.62, 0.9), (1, 0.35), (0.8, -0.3), (0.35, -0.8), (0, -1)]
HEADB = [(0, 1), (0.45, 1), (0.85, 0.75), (1, 0.15), (0.6, -0.8), (0, -1)]       # skull: antler face on top, ear face high on the side
HEAD = [(0, 1), (0.75, 0.93), (1, 0.3), (0.85, -0.4), (0.5, -0.85), (0, -1)]
HEADF = [(0, 1), (0.75, 0.88), (1, 0.1), (0.85, -0.45), (0.5, -0.85), (0, -1)]
MUZ = [(0, 1), (0.62, 0.95), (1, 0.4), (0.95, -0.3), (0.6, -0.85), (0, -1)]
TAIL = [(0, 1), (0.7, 0.7), (1, 0.1), (0.85, -0.5), (0.45, -0.9), (0, -1)]

# poly pass 3: every 6-point half ring gets 4 rounded in-between points (Catmull-Rom midpoints) on the back,
# the upper flank, the lower flank and the belly: 10 vertices per half ring. Old index i -> new index OI[i].
OI = [0, 2, 4, 5, 7, 9]


def dense(prof):
    Q = [(-prof[1][0], prof[1][1])] + list(prof) + [(-prof[4][0], prof[4][1])]
    cr = lambda a, b, c, d: tuple((-a[j] + 9 * b[j] + 9 * c[j] - d[j]) / 16 for j in (0, 1))
    out = []
    for i in range(5):
        out.append(prof[i])
        if i in (0, 1, 3, 4):
            out.append(cr(Q[i], Q[i + 1], Q[i + 2], Q[i + 3]))
    out.append(prof[5])
    return out


BODY, CHEST, HEADB, HEAD, HEADF, MUZ, TAIL = [dense(p_) for p_ in (BODY, CHEST, HEADB, HEAD, HEADF, MUZ, TAIL)]


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


SECS = [   # poly pass 3: 32 stations (was 20); the new ones (*) on the rump, hip, belly, shoulder, brisket, neck, muzzle
    tb('T0', (1.12, 0.785), (1.065, 0.785), 0.035, TAIL),
    tb('T1', (1.125, 0.92), (1.065, 0.875), 0.05, TAIL),
    tb('T2', (1.085, 1.04), (1.075, 0.935), 0.055, TAIL),
    tb('Tr', (1.05, 1.09), (1.06, 0.90), 0.10, BODY),            # * tail root into the rump
    tb('R0', (1.00, 1.14), (1.04, 0.85), 0.15, BODY),
    tb('Ra', (0.945, 1.195), (0.975, 0.765), 0.205, BODY),       # * rump round-over (sheet top 1.14-1.17)
    tb('R1', (0.88, 1.24), (0.90, 0.70), 0.24, BODY),
    tb('Rm', (0.79, 1.275), (0.80, 0.675), 0.26, BODY),          # * hip: the hind leg root spans R1-Rm-R2
    tb('R2', (0.70, 1.30), (0.70, 0.67), 0.27, BODY),
    tb('Rb', (0.55, 1.28), (0.55, 0.655), 0.285, BODY),          # * flank behind the belly tuck
    tb('W0', (0.40, 1.25), (0.40, 0.66), 0.29, BODY),
    tb('Wm', (0.25, 1.237), (0.25, 0.632), 0.30, BODY),          # * sheet back 1.236, belly 0.631
    tb('M0', (0.10, 1.22), (0.10, 0.62), 0.30, BODY),
    tb('Mc', (-0.03, 1.24), (-0.03, 0.60), 0.30, BODY),          # * girth, back rising to the withers
    tb('Cq', (-0.09, 1.255), (-0.09, 0.59), 0.30, CHEST),        # * chest girth behind the elbow
    tb('C0', (-0.15, 1.27), (-0.15, 0.58), 0.30, CHEST),
    tb('Cm', (-0.27, 1.30), (-0.275, 0.57), 0.29, CHEST),        # * shoulder: the foreleg root spans C0-Cm-C1
    tb('C1', (-0.38, 1.33), (-0.40, 0.58), 0.27, CHEST),
    tb('Cn', (-0.43, 1.352), (-0.49, 0.645), 0.245, CHEST),      # * brisket round-over
    tb('C2', (-0.48, 1.37), (-0.58, 0.72), 0.22, CHEST),
    tb('Nb', (-0.53, 1.405), (-0.64, 0.835), 0.193, BODY),       # * neck base (sheet top 1.42)
    tb('N0', (-0.58, 1.44), (-0.70, 0.95), 0.17, BODY),
    tb('Na', (-0.62, 1.47), (-0.745, 1.05), 0.148, BODY),        # * throat curve
    tb('N1', (-0.66, 1.50), (-0.79, 1.15), 0.13, BODY),
    tb('N2', (-0.695, 1.517), (-0.815, 1.168), 0.132, BODY),     # * nape into the skull
    tb('H0', (-0.73, 1.53), (-0.84, 1.18), 0.135, HEADB),
    tb('Hk', (-0.79, 1.53), (-0.87, 1.19), 0.135, HEADB),
    tb('H0b', (-0.86, 1.47), (-0.90, 1.20), 0.13, HEAD),
    tb('H1', (-0.95, 1.41), (-0.95, 1.20), 0.095, HEADF),
    tb('H1b', (-0.985, 1.384), (-0.985, 1.203), 0.082, HEADF),   # * stop into the muzzle
    tb('H2', (-1.02, 1.36), (-1.02, 1.21), 0.07, MUZ),
    tb('H2b', (-1.05, 1.344), (-1.046, 1.214), 0.065, MUZ),     # * muzzle side plane
    tb('H3', (-1.08, 1.33), (-1.07, 1.22), 0.06, MUZ),
    tb('H3b', (-1.10, 1.322), (-1.09, 1.236), 0.053, MUZ),       # * nose round-over
    tb('H4', (-1.12, 1.315), (-1.11, 1.255), 0.045, MUZ),
]

# limb sections: (centre xyz, rx, ry[, dz])
# poly pass 3: 9 sections per leg (was 6): forearm muscle, knee knob, slim cannon; 10-vertex rings
FORE = [(J['elbow'], 0.085, 0.115), ((0.165, -0.295, 0.44), 0.077, 0.102), ((0.16, -0.30, 0.36), 0.066, 0.082),
        ((0.16, -0.305, 0.29), 0.057, 0.068), (J['wrist'], 0.057, 0.065), ((0.16, -0.315, 0.175), 0.048, 0.054),
        ((0.16, -0.32, 0.12), 0.05, 0.055), ((0.16, -0.33, 0.06), 0.045, 0.056), ((0.16, -0.35, 0.0), 0.05, 0.075)]
# fix pass: reverse hock — the gaskin runs back to a sharp hock behind the knee, the cannon drops forward to the hoof
HIND = [(J['knee'], 0.095, 0.135), ((0.163, 0.87, 0.54), 0.085, 0.118), ((0.155, 0.94, 0.48), 0.07, 0.095),
        ((0.148, 1.00, 0.43), 0.058, 0.08), (J['hock'], 0.05, 0.069), ((0.14, 1.045, 0.29), 0.046, 0.055),
        ((0.14, 1.03, 0.20), 0.048, 0.054), ((0.14, 1.01, 0.07), 0.043, 0.053), ((0.14, 0.99, 0.0), 0.048, 0.072)]
# ear: sideways, its width is vertical (dz), its depth along y
EAR = [((0.22, -0.76, 1.49), 0.018, 0.035, 0.068), ((0.36, -0.77, 1.585), 0.005, 0.008, 0.014)]
# antler main beam: up, out and back from the skull top
_BEAM0 = [((0.085, -0.80, 1.57), 0.0483, 0.0483, 0.0), ((0.16, -0.74, 1.61), 0.0437, 0.046, 0.0138),
          ((0.30, -0.62, 1.67), 0.0391, 0.0414, 0.0207), ((0.42, -0.50, 1.77), 0.0333, 0.0356, 0.0184),
          ((0.48, -0.42, 1.88), 0.0253, 0.0276, 0.0092), ((0.50, -0.38, 1.97), 0.0126, 0.0126, 0.0)]
# poly pass 3: the beam ring is a 6-vertex round (was a 4-corner square): radii x1.2 keep its section area
BEAM = [(c_, rx_ * 1.2, ry_ * 1.2, dz_) for c_, rx_, ry_, dz_ in _BEAM0]   # fix pass: beam ~1.35x thicker


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


def region_roles(faces):
    """Roles for a face region (poly pass 3): boundary vertices get evenly spaced angles round the region centre
    (0 = +x, outward), interior ones a fraction across x. Keyed by position: extrude deletes the interior vertices."""
    fs = set(faces)
    vs = {v for f in faces for v in f.verts}
    bnd = [v for v in vs if not all(f in fs for f in v.link_faces)]
    inn = [v for v in vs if v not in bnd]
    c = sum((v.co for v in bnd), Vector()) / len(bnd)
    ex = max(v.co.x for v in bnd) - min(v.co.x for v in bnd)
    ey = max(v.co.y for v in bnd) - min(v.co.y for v in bnd)
    ang = {v: math.atan2((v.co.y - c.y) / ey, (v.co.x - c.x) / ex) for v in bnd}
    order = sorted(bnd, key=lambda v: (ang[v], v.co.x, v.co.y, v.co.z))
    n = len(order); st = 2 * math.pi / n
    sx = sum(math.cos(ang[v] - i * st) for i, v in enumerate(order))
    sy = sum(math.sin(ang[v] - i * st) for i, v in enumerate(order))
    base = math.atan2(sy, sx)
    roles = [(tuple(v.co), ('b', base + i * st)) for i, v in enumerate(order)]
    roles += [(tuple(v.co), ('i', 0.4 * (v.co.x - c.x) / (ex / 2))) for v in inn]
    return roles


def ring_pos(sec, role):
    c, rx, ry = sec[0], sec[1], sec[2]
    dz = sec[3] if len(sec) > 3 else 0.0
    if role[0] == 'b':
        ca, sa = math.cos(role[1]), math.sin(role[1])
        return (c[0] + rx * ca, c[1] + ry * sa, c[2] - dz * ca)
    return (c[0] + rx * role[1], c[1], c[2] - dz * role[1])


def grow_round(bm, faces, secs):
    roles = region_roles(faces)
    for sec in secs:
        r = extrude(bm, faces)
        new = [(v, min(roles, key=lambda o: (Vector(o[0]) - v.co).length)[1]) for v in r['verts']]
        for v, role in new:
            v.co = Vector(ring_pos(sec, role))
        faces = r['faces']
        roles = [(tuple(v.co), role) for v, role in new]
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(span_name, secs):
        # poly pass 3: the leg root is 3 profile faces (old lower flank) x 2 station spans -> a 10-vertex leg ring
        i = idx[span_name]
        grow_round(bm, [spans[j][q] for j in (i, i + 1) for q in (4, 5, 6)], secs)

    limb('R1', HIND)
    limb('C0', FORE)
    i = idx['H0']
    rr, rf = rings[i], rings[i + 1]
    grow(bm, [spans[i][4]], {rf[4]: (-1, -1), rf[5]: (1, -1), rr[4]: (-1, 1), rr[5]: (1, 1)}, EAR, corner=1.0)
    i = idx['Hk']
    grow_round(bm, [spans[i][2], spans[i][3]], BEAM)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def eye_face_centre():
    # poly pass 3: the old upper-side stop face is two faces now; the socket goes in the lower one (3-4)
    H0b, H1 = P('H0b'), P('H1')
    return (H0b[3] + H0b[4] + H1[3] + H1[4]) / 4


def stage2(k, body):
    """Joint rings (elbow, stifle, neck), the eye socket, brow, flat muzzle planes and a slanted nose pad."""
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ec0 = eye_face_centre()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    with topo(bm, k.log, 'loop', 'elbow ring: the foreleg bends here'):
        loopcut(bm, edge_near(bm, mid(ring_pos(FORE[0], ('b', 0.0)), ring_pos(FORE[1], ('b', 0.0)))), t=0.5)
    with topo(bm, k.log, 'loop', 'stifle ring: the hind leg bends here'):
        loopcut(bm, edge_near(bm, mid(ring_pos(HIND[0], ('b', 0.0)), ring_pos(HIND[1], ('b', 0.0)))), t=0.5)
    with topo(bm, k.log, 'loop', 'knee ring (poly pass 3): the fore cannon bends here'):
        loopcut(bm, edge_near(bm, mid(ring_pos(FORE[4], ('b', 0.0)), ring_pos(FORE[5], ('b', 0.0)))), t=0.5)
    with topo(bm, k.log, 'loop', 'hock ring (poly pass 3): the hind cannon bends here'):
        loopcut(bm, edge_near(bm, mid(ring_pos(HIND[4], ('b', 0.0)), ring_pos(HIND[5], ('b', 0.0)))), t=0.5)
    with topo(bm, k.log, 'loop', 'neck ring: the head nods here'):
        loopcut(bm, edge_near(bm, mid(P('N0')[0], P('Na')[0])), t=0.5)
    H0b, H1, H2, H3, H3b, H4 = P('H0b'), P('H1'), P('H2'), P('H3'), P('H3b'), P('H4')
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with topo(bm, k.log, 'inset', 'eye socket in the stop face'):
        inner = inset(bm, [f], 0.34, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.014)
    move([vert_near(bm, H1[2])], (0.008, -0.012, 0.004))
    mz = (H2, P('H2b'), H3, H3b, H4)
    flatten([vert_near(bm, R_[j]) for R_ in mz for j in (4, 5)])
    flatten([vert_near(bm, R_[j]) for R_ in mz for j in (0, 1, 2)])
    move([vert_near(bm, H4[j]) for j in (0, 1, 2)], (0.0, -0.014, -0.004))
    move([vert_near(bm, H4[j]) for j in (7, 8, 9)], (0.0, 0.016, 0.0))
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


PAL = {'coat': '#a85a32', 'dark': '#4e3324', 'cream': '#dcc29a', 'black': '#1c1a1a',
       'antler': '#7a5e44', 'tip': '#cdb894'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if z > 1.555 and x > 0.03 and y > -0.86:
        return 'antler'                                       # main beam
    if x > 0.145 and -0.83 < y < -0.69 and 1.36 < z < 1.57:
        return 'cream' if n.y < -0.35 else 'coat'             # ear: cream inner wall
    if y < -1.09 and z > 1.265:
        return 'black'                                        # nose pad
    if z < 0.075:
        return 'black'                                        # hooves
    if y > 1.04 and z < 1.07:
        return 'dark' if n.y > -0.2 else 'cream'              # tail: dark, pale front
    if y > 0.86 and n.y > 0.15 and (x / 0.2) ** 2 + ((z - 1.0) / 0.19) ** 2 < 1.0:
        return 'cream'                                        # rump patch: round, follows the rump ring (fix pass 2)
    if y < -0.98 and (z < 1.265 or n.z < -0.3):
        return 'cream'                                        # lips and chin
    if z < 0.45 or (y < 0 and z < 0.62 and x > 0.07 and n.z < 0.5):
        return 'dark'                                         # dark lower legs, whole foreleg
    if -0.84 < y < -0.72 and n.z < -0.4:
        return 'cream'                                        # throat patch under the jaw
    if -0.72 - 0.33 * (1.5 - z) < y < -0.40 + 0.08 * (1.3 - z):
        return 'dark'                                         # dark neck mane and chest
    if -0.2 < y < 0.7 and z < 0.72 and n.z < 0.3:
        return 'cream'                                        # belly and the lower-flank underline
    return 'coat'


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


def tine(bm, base, d, r0, L):
    """An antler tine (fix pass): a square root sunk in the beam, two tapering rings and a blunt tip L out along d."""
    n, u, w = frame3(d)
    rows = [(-0.4 * r0, r0 * 0.75), (L * 0.25, r0 * 0.88), (L * 0.5, r0 * 0.75), (L * 0.75, r0 * 0.6), (L, r0 * 0.42)]
    cs = [(math.cos(k_ * math.pi / 2), math.sin(k_ * math.pi / 2)) for k_ in range(4)]
    R = [[bm.verts.new(base + n * off + (u * su + w * sw) * r) for su, sw in cs] for off, r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def surf(a, b, t, jf):
    A, Bq = P(a), P(b)
    o0 = min(int(jf), 4)                                       # jf is an old (6-point) profile index
    jf = OI[o0] + (jf - o0) * (OI[o0 + 1] - OI[o0])
    j0 = min(int(jf), 8); f = jf - j0
    pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
    p = pa.lerp(pb, t)
    ca = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == a][0]))
    cb = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == b][0]))
    c = ca.lerp(cb, t)
    return p, (p - c).normalized()


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def clumps(spec, tree):
    bm = bmesh.new()
    for a, b, t, jf, lay, s_, L_ in spec:
        p, n_ = surf(a, b, t, jf)
        loc, fn, _i, _d = tree.find_nearest(p)
        clump(bm, loc, (fn + n_).normalized(), Vector(lay), s_, L_)
    return bm


def beam_pt(i, t):
    a, b = Vector(BEAM[i][0]), Vector(BEAM[i + 1][0])
    return a.lerp(b, t)


def stage3(k, body):
    paint(body, PAL, body_rule)
    tree = body_bvh(body)
    # eyes: small dark lenses with a black pupil, in the socket
    H0b, H1 = P('H0b'), P('H1')
    fn = (H1[3] - H0b[3]).cross(H0b[4] - H0b[3]).normalized()
    fn = fn if fn.x > 0 else -fn
    c, n, _i, _d = tree.find_nearest(eye_face_centre() - fn * 0.014)
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.019, 0.010)
    eye = object_from_bm('eye', bm)
    paint(eye, {'dark': PAL['dark'], 'black': PAL['black']},
          lambda c_, n_, i: 'black' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.008 and n_.dot(n) > 0.5 else 'dark')
    # neck mane (fix pass): 5 large flat wedges down the throat and lower neck, no small spikes
    dn = (0.15, 0.35, -0.92)
    sd = (0.3, 0.6, -0.75)
    mane = [('N1', 'H0', 0.5, 4.0, dn, 0.06, 0.083), ('N0', 'N1', 0.5, 4.2, dn, 0.08, 0.105),
            ('N0', 'N1', 0.5, 2.8, sd, 0.08, 0.094), ('C2', 'N0', 0.6, 4.3, dn, 0.09, 0.11),
            ('C2', 'N0', 0.45, 3.1, sd, 0.085, 0.099)]
    hi = [m for m in mane if m[0] in ('N0', 'N1')]
    lo = [m for m in mane if m[0] not in ('N0', 'N1')]
    maneo = object_from_bm('mane', clumps(lo, tree))
    paint(maneo, {'dark': PAL['dark']}, lambda c_, n_, i: 'dark')
    maneh = object_from_bm('mane_neck', clumps(hi, tree))
    paint(maneh, {'dark': PAL['dark']}, lambda c_, n_, i: 'dark')
    # antler tines on the main beam: brow, trez, and a forked crown
    bm = bmesh.new()
    # fix pass: thicker tines, roots sunk in the thicker beam, alternating out/in of the beam plane
    tine(bm, beam_pt(0, 0.6), (0.1, -0.85, 0.6), 0.026, 0.24)        # brow, forward and up
    tine(bm, beam_pt(1, 0.4), (0.25, -0.45, 0.86), 0.024, 0.24)      # bez, out
    tine(bm, beam_pt(2, 0.45), (-0.22, -0.2, 0.95), 0.023, 0.25)     # trez, in
    tine(bm, beam_pt(2, 0.95), (0.25, -0.15, 0.95), 0.021, 0.23)     # crown, out
    tine(bm, beam_pt(3, 0.6), (-0.25, 0.25, 0.93), 0.019, 0.2)       # crown, in
    tines = object_from_bm('tines', bm)
    paint(tines, {'antler': PAL['antler'], 'tip': PAL['tip']},
          lambda c_, n_, i: 'tip' if c_.z > 1.0 and min((c_ - beam_pt(j, 0.5)).length for j in range(5)) > 0.08 else 'antler')
    return [eye, maneo, maneh, tines]


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('paw.L', J['wrist'], J['ftoe'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
         ('foot.L', J['hock'], J['hpaw'], 'shin.L', True),
         ('toe.L', J['hpaw'], J['htoe'], 'foot.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    # the antler beams are bone: rigid on the head (auto weights split them between head, ear and neck)
    hg = body.vertex_groups['head']
    for v in body.data.vertices:
        if v.co.z > 1.555 and abs(v.co.x) > 0.03 and v.co.y > -0.86:
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            hg.add([v.index], 1.0, 'REPLACE')
    for p in pieces:
        if p.name.endswith('tines'):
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'tail0': (0, 0, 6)},
                       20: {'ear.L': (0, 0, -12)}, 24: {'tail0': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'head': (2, 0, 0), 'tail0': (0, 0, -6)}, 48: {}})
    A = 16
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0)},
        7: {'forearm.R': (-30, 0, 0), 'paw.R': (-25, 0, 0), 'shin.L': (-18, 0, 0), 'foot.L': (22, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0)},
        19: {'forearm.L': (-30, 0, 0), 'paw.L': (-25, 0, 0), 'shin.R': (-18, 0, 0), 'foot.R': (22, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0)}})
    # attack: rear up a little, then lower the antlers and thrust forward
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-8, 0, 0), 'chest': (4, 0, 0), 'head': (-6, 0, 0)},
        16: {'neck': (22, 0, 0), 'head': (25, 0, 0), 'chest': (-6, 0, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0)},
        20: {'neck': (24, 0, 0), 'head': (30, 0, 0), 'chest': (-6, 0, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0)},
        26: {'neck': (10, 0, 0), 'head': (8, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, 0)}, 16: {'hips': (0, 0.07, 0)}, 20: {'hips': (0, 0.07, 0)},
             26: {'hips': (0, 0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
