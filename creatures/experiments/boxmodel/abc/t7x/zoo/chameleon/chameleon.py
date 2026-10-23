import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

META = dict(creature='chameleon', detail_tier=1, model='opus', stage1_tris=(1400, 2800), total_tris=(1800, 4500),
            closeups=[('head', (0.0, -0.65, 0.80), 0.20, 'hero'),
                      ('front foot', (0.19, -0.47, 0.04), 0.09, 'hero'),
                      ('hind foot', (0.20, 0.23, 0.04), 0.09, 'hero'),
                      ('tail spiral', (0.0, 0.71, 0.16), 0.17, 'az090')])

# the skeleton (x >= 0 half; .L on +X), read off reference/side.png + front.png (1.1 m to the casque tip)
J = dict(
    hips=(0.0, 0.28, 0.58), spine=(0.0, 0.0, 0.62), chest=(0.0, -0.30, 0.63),
    neck=(0.0, -0.40, 0.66), head=(0.0, -0.47, 0.70), nose=(0.0, -0.84, 0.66),
    shoulder=(0.12, -0.33, 0.47), elbow=(0.235, -0.40, 0.30), wrist=(0.205, -0.45, 0.07), ftoe=(0.205, -0.53, 0.02),
    hipL=(0.12, 0.21, 0.46), knee=(0.235, 0.25, 0.30), ankle=(0.205, 0.245, 0.07), htoe=(0.205, 0.17, 0.02),
)

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = [(0, 1), (0.55, 0.9), (1, 0.25), (0.95, -0.35), (0.5, -0.85), (0, -1)]
TAIL = [(0, 1), (0.7, 0.7), (1, 0.1), (0.85, -0.5), (0.45, -0.9), (0, -1)]


def roundp(p):
    """Poly pass 3: 6 -> 10 points per half ring. A rounded point goes into each of the first four spans
    (Catmull-Rom midpoint, the ring mirrored across the seam), so cross-sections read round. Old i -> new O[i]."""
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
BODY, TAIL = roundp(BODY), roundp(TAIL)


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


# the tail path, base -> tip: (y, z, thickness, half-width). Three sections down the back, then a spiral
# of 45-degree steps about (0.70, 0.15), the radius and the thickness shrinking toward the tip
TPATH = [(0.51, 0.485, 0.165, 0.072), (0.62, 0.43, 0.135, 0.062), (0.73, 0.36, 0.12, 0.054)]
for phi, R, th in ((40, 0.17, 0.11), (0, 0.14, 0.10), (-45, 0.125, 0.09), (-90, 0.11, 0.08), (-135, 0.10, 0.075),
                   (-180, 0.09, 0.07), (-225, 0.08, 0.06), (-270, 0.07, 0.05), (-315, 0.058, 0.045),
                   (-360, 0.047, 0.04), (-405, 0.037, 0.034), (-450, 0.029, 0.028), (-495, 0.022, 0.024)):
    a_ = math.radians(phi)
    TPATH.append((0.70 + R * math.cos(a_), 0.15 + R * math.sin(a_), th, max(0.012, th * 0.42)))
TP0 = list(TPATH)   # the original stations: colour bands and tail bones


def spiral(phi, R, th):
    a_ = math.radians(phi)
    return (0.70 + R * math.cos(a_), 0.15 + R * math.sin(a_), th, max(0.012, th * 0.42))


# poly pass 3: extra loft stations where the tail curves most: the root off the rump, and the half steps of the
# outer spiral turn (largest radius), each placed on the spiral, not on a chord
TPATH = ([(0.455, 0.515, 0.19, 0.084)] + TP0[:4] + [spiral(20, 0.155, 0.105), TP0[4], spiral(-22, 0.132, 0.095),
         TP0[5], spiral(-67, 0.117, 0.085)] + TP0[6:])


def tail_secs():
    """Each tail section stands across the path; its top seam is the dorsal side (outside of the curl)."""
    out = []
    P0 = [(0.40, 0.54)] + [(y, z) for y, z, _t, _w in TPATH]
    for i, (y, z, th, W) in enumerate(TPATH):
        a, b = P0[i], P0[min(i + 2, len(P0) - 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ty, tz)
        dy, dz = -tz / L, ty / L
        out.append(tb('T%d' % i, (y + dy * th / 2, z + dz * th / 2), (y - dy * th / 2, z - dz * th / 2), W, TAIL))
    return out[::-1]


# head sections: explicit half rings (x, z) at a y, top seam -> bottom seam (the casque is the tall narrow top)
HEADS = [
    ('H0', -0.43, [(0, 1.12), (0.07, 1.065), (0.118, 0.72), (0.11, 0.53), (0.06, 0.45), (0, 0.43)]),
    ('H0b', -0.50, [(0, 1.08), (0.072, 1.005), (0.124, 0.73), (0.116, 0.545), (0.064, 0.462), (0, 0.443)]),
    ('H1', -0.575, [(0, 1.02), (0.072, 0.93), (0.122, 0.73), (0.115, 0.56), (0.065, 0.48), (0, 0.46)]),
    ('H1b', -0.635, [(0, 0.935), (0.075, 0.875), (0.118, 0.725), (0.11, 0.58), (0.062, 0.50), (0, 0.482)]),
    ('H2', -0.694, [(0, 0.835), (0.075, 0.80), (0.11, 0.71), (0.10, 0.60), (0.055, 0.525), (0, 0.505)]),
    ('H2b', -0.737, [(0, 0.79), (0.07, 0.77), (0.1, 0.695), (0.092, 0.612), (0.053, 0.555), (0, 0.54)]),
    ('H3', -0.779, [(0, 0.75), (0.06, 0.735), (0.085, 0.68), (0.08, 0.625), (0.05, 0.585), (0, 0.575)]),
    ('H4', -0.843, [(0, 0.70), (0.035, 0.695), (0.048, 0.665), (0.045, 0.64), (0.028, 0.62), (0, 0.615)]),
]
HEADS = [(n, y, roundp(p)) for n, y, p in HEADS]

# the spine loft, tail tip -> nose
SECS = tail_secs() + [
    tb('R0', (0.40, 0.655), (0.40, 0.425), 0.11, BODY),
    tb('R0b', (0.34, 0.717), (0.34, 0.392), 0.132, BODY),
    tb('R1', (0.28, 0.765), (0.28, 0.37), 0.15, BODY),
    tb('R1b', (0.205, 0.815), (0.205, 0.35), 0.166, BODY),
    tb('R2', (0.13, 0.85), (0.13, 0.335), 0.175, BODY),
    tb('M0b', (0.055, 0.877), (0.055, 0.312), 0.186, BODY),
    tb('M0', (-0.02, 0.895), (-0.02, 0.30), 0.19, BODY),
    tb('M1', (-0.17, 0.89), (-0.17, 0.315), 0.19, BODY),
    tb('M1b', (-0.235, 0.884), (-0.235, 0.328), 0.187, BODY),
    tb('C0', (-0.29, 0.875), (-0.29, 0.35), 0.18, BODY),
    tb('C0b', (-0.33, 0.868), (-0.33, 0.37), 0.169, BODY),
    tb('C1', (-0.37, 0.86), (-0.37, 0.395), 0.155, BODY),
] + HEADS

# limb sections: (centre xyz, rx, ry) — horizontal hexagons; the legs splay out from the flank (front view)
FORE = [(J['elbow'], 0.065, 0.075), ((0.25, -0.415, 0.20), 0.052, 0.058), (J['wrist'], 0.044, 0.05),
        ((0.205, -0.465, 0.035), 0.05, 0.07), ((0.205, -0.47, 0.0), 0.05, 0.08)]
HIND = [(J['knee'], 0.068, 0.08), ((0.25, 0.265, 0.20), 0.054, 0.06), (J['ankle'], 0.045, 0.05),
        ((0.205, 0.235, 0.035), 0.05, 0.07), ((0.205, 0.23, 0.0), 0.05, 0.08)]
# fix pass 9: a short shoulder / hip collar ring first, so the tall flank root strip becomes a stubby upper limb
# instead of one long web from the flank to the elbow (the review's "knee fin"); density kept, +10 verts per leg
SHOULDER = ((0.21, -0.315, 0.50), 0.05, 0.068, 0.10)   # 4th value: tilt, z rises with u (outer side up)
HIPRING = ((0.21, 0.24, 0.50), 0.05, 0.072, 0.10)


def sec_pts(sec):
    nm = sec[0]
    if len(sec) == 3:
        return [(x, sec[1], z) for x, z in sec[2]]
    _n, (y0, z0), a, T, B, W, prof = sec
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def role_pos(sec, u, s, corner=0.55):
    c, rx, ry = sec[0], sec[1], sec[2]
    # poly pass 4 (review MIX): legs back to the before3 hexagon section; the u = +-0.5 vertices sit on the
    # flat planes between the hexagon corners, so the leg faces stay crisp (no elliptical knee flare)
    k = 1.0 - (1.0 - corner) * abs(u)
    return (c[0] + u * rx, c[1] + s * ry * k, c[2] + (u * sec[3] if len(sec) > 3 else 0.0))


def grow(bm, faces, roles, secs, corner=0.55):
    """Extrude a face region section by section; each new vertex keeps the role
    (u across the ring, s front/back) of the vertex it was extruded from."""
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


def stage1(k):
    bm = bmesh.new()
    idx = {s[0]: i for i, s in enumerate(SECS)}
    rings = [ring(bm, sec_pts(s)) for s in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(span_name, secs):
        i = idx[span_name]          # span between ring i (rear) and ring i+1 (front)
        rr, rf = rings[i], rings[i + 1]
        us = (1, 0.5, 0, -0.5, -1)       # poly pass 3: 4-face root strip -> 10-vertex leg rings
        for r_ in (rr, rf):             # poly pass 4: flat root strip (before3 planes), no rounded flank fin
            for j in (5, 7):
                r_[j].co = (r_[j - 1].co + r_[j + 1].co) / 2
        roles = {**{rf[4 + j]: (u, -1) for j, u in enumerate(us)}, **{rr[4 + j]: (u, 1) for j, u in enumerate(us)}}
        grow(bm, [spans[i][4], spans[i][5], spans[i][6], spans[i][7]], roles, secs, corner=0.8)

    limb('C0', [SHOULDER] + FORE)
    limb('R1', [HIPRING] + HIND)
    snap_seam(bm)
    return object_from_bm('body', bm)


def P(nm):
    for s in SECS:
        if s[0] == nm:
            return [Vector(q) for q in sec_pts(s)]


def centre_of(nm):
    q = P(nm)
    return Vector((0.0, (q[0].y + q[5].y) / 2, (q[0].z + q[5].z) / 2))


def eye_face_centre():
    """The side of the head under the casque: H1b ring vertex 3 (the old H1-H2 face, ring index 1-2)."""
    return P('H1b')[3]


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.04 and abs(c.y - ec0.y) < 0.06
                                        and abs(c.z - ec0.z) < 0.06)
    bm = edit(body)
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    with k.topo(bm, 'loop', 'elbow: a second ring between elbow and forearm so the elbow bends, not kinks'):
        loopcut(bm, edge_near(bm, mid(role_pos(FORE[0], 1, 1), role_pos(FORE[1], 1, 1))), t=0.5)
    with k.topo(bm, 'loop', 'knee: a second ring between knee and shin for the hind-leg bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(HIND[0], 1, 1), role_pos(HIND[1], 1, 1))), t=0.5)
    with k.topo(bm, 'loop', 'neck: a ring between the shoulder ring and the casque back so the head turns'):
        loopcut(bm, edge_near(bm, mid(P('C1')[6], P('H0')[6])), t=0.5)
    ev0 = vert_near(bm, ec0)
    fs = list(ev0.link_faces)
    fn = sum((f_.normal for f_ in fs), Vector()).normalized()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the four side faces round H1b[3] under the casque rim'):
        inner = inset(bm, fs, 0.30, 0.0)
    ev = list({v for f_ in inner for v in f_.verts})
    move(ev, -fn * 0.008)
    # casque rim: the top-outer vertex of the eye ring out a little (a brow over the eye); flat snout side
    H2, H3, H4 = P('H2'), P('H3'), P('H4')
    move([vert_near(bm, P(n_)[2]) for n_ in ('H1', 'H1b')], (0.008, 0.0, 0.0))
    flatten([vert_near(bm, q) for q in (H3[4], H3[5], H3[6], H4[4], H4[5], H4[6])])
    # tail tip: widen the last ring a little so its cap does not fan needles
    T0 = P(SECS[0][0]); tc = sum(T0, Vector()) / len(T0)
    scale([vert_near(bm, q) for q in T0], 1.3, pivot=(0.0, tc.y, tc.z))
    commit(body, bm)


# colours picked off the reference sheet: sage green, yellow bands, teal bands, cream belly and feet, dark claws
PAL = {'green': '#94b878', 'yellow': '#d9c662', 'teal': '#6fa596', 'cream': '#e4dcae', 'dark': '#262422'}
BANDS = [(-0.20, -0.08, 'yellow'), (-0.06, 0.05, 'teal'), (0.12, 0.23, 'yellow'), (0.26, 0.34, 'teal'), (0.40, 0.48, 'yellow')]
TS = [0.0]
for i in range(1, len(TP0)):
    TS.append(TS[-1] + math.hypot(TP0[i][0] - TP0[i - 1][0], TP0[i][1] - TP0[i - 1][1]))


def tail_band(c):
    i = min(range(len(TP0)), key=lambda j: (TP0[j][0] - c.y) ** 2 + (TP0[j][1] - c.z) ** 2)
    s = TS[i]
    return ('teal', 'yellow', 'green')[int(s / 0.085) % 3]


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if x > 0.13 and z < 0.32:
        if z < 0.10:
            return 'green'                              # foot block (the cream is on the grip pads)
        return 'yellow' if 0.17 < z < 0.25 else 'green'  # legs, a yellow band at the shin
    if x > 0.15 and z < 0.62 and (-0.40 < y < -0.24 or 0.17 < y < 0.32):
        return 'green'                                  # fix pass 9: shoulder / hip collar, no cream wedge
    if y > 0.48:
        return tail_band(c)                             # banded tail and spiral
    if y < -0.40:                                       # head
        if z < 0.60 and n.z < 0.2:
            return 'cream'                              # jaw and throat
        if z > 0.84 and y > -0.47:
            return 'yellow'                             # casque back rim
        if -0.56 < y < -0.47 and z < 0.78:
            return 'yellow'                             # band behind the eye
        return 'green'
    if z < 0.40 or (n.z < -0.5 and z < 0.5):
        return 'cream'                                  # belly
    for a, b, col in BANDS:
        if a < y < b:
            return col
    return 'green'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h, rl):
    """A chameleon eye turret: a cone from a base ring r (sunk into the socket) up to height h, with a small
    flat lens ring rl and a pupil fan at its tip."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 3 for k_ in range(6)]]
    R, T, I = ring_(r, 0.0), ring_(rl, h), ring_(rl * 0.55, h + 0.004)
    A, B = bm.verts.new(c + n * (h + 0.006)), bm.verts.new(c - n * 0.012)
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], T[b], T[a]])
        bm.faces.new([T[a], T[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def crest(bm, tree, y, s, h):
    """A half dorsal spike on the mirror plane (the mirror closes it): a base sunk 1.5 cm into the back."""
    hit = tree.ray_cast(Vector((0.0005, y, 1.5)), Vector((0, 0, -1)), 2.0)
    loc, nrm = hit[0], hit[1]
    up = Vector(nrm); up.x = 0.0; up.normalize()
    fw = Vector((0.0, up.z, -up.y))                       # along the back, toward the tail
    b = Vector((0.0, loc.y, loc.z)) - up * 0.015
    # detail pass 10-23: a blunt chunky crest block (a half frustum, >= 28 mm thick to its top; tier-1 floor 26.9 mm),
    # was a pointed half pyramid (t 14.6 mm)
    A = bm.verts.new(b - fw * s); Bv = bm.verts.new(b + fw * s)
    C = bm.verts.new(b + Vector((s * 0.6, 0, 0)))
    tp = b + up * (0.015 + h) + fw * s * 0.3
    A2 = bm.verts.new(tp - fw * s * 0.5); B2 = bm.verts.new(tp + fw * s * 0.5)
    C2 = bm.verts.new(tp + Vector((0.0145, 0, 0)))
    bm.faces.new([A, Bv, C]); bm.faces.new([A2, C2, B2])
    bm.faces.new([A, C, C2, A2]); bm.faces.new([C, Bv, B2, C2])


def bundle(bm, root, d, L, w, h, z0=0.001):
    """A clamp-foot toe bundle: a box sunk in the foot at root, running out along d (unit, in xy) on the ground,
    tapering to a rounded tip. Returns the tip centre."""
    d = Vector(d).normalized(); s = Vector((-d.y, d.x, 0.0))
    rows = []
    for t, k in ((-0.02, 1.0), (L * 0.55, 0.92), (L, 0.75)):     # detail pass 10-23: blunter tip (t 23.6 < 26.9 mm)
        p = root + d * t
        hh = h * (1.0 if t < L else 0.82)
        rows.append([bm.verts.new(p + s * su * w * k + Vector((0, 0, z))) for su, z in ((-1, z0), (1, z0), (1, hh), (-1, hh))])
    bm.faces.new(list(reversed(rows[0])))
    for a, b in ((rows[0], rows[1]), (rows[1], rows[2])):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(rows[2])
    return root + d * L


def claw(bm, tip, d):
    """A small dark hook past a toe-bundle tip, sunk 1 cm into it."""
    d = Vector(d).normalized(); s = Vector((-d.y, d.x, 0.0))
    b = tip - d * 0.01
    base = [bm.verts.new(b + s * su * 0.007 + Vector((0, 0, z))) for su, z in ((-1, 0.004), (1, 0.004), (0, 0.016))]
    t = bm.verts.new(tip + d * 0.018 + Vector((0, 0, 0.002)))
    bm.faces.new([base[0], base[2], base[1]])
    bm.faces.new([base[0], base[1], t]); bm.faces.new([base[1], base[2], t]); bm.faces.new([base[2], base[0], t])


def stage3(k, body):
    paint(body, PAL, body_rule)
    tree = body_bvh(body)
    # eye: a small green lens with a dark pupil, proud of the socket floor
    ec = eye_face_centre()
    bmb = edit(body)
    H1, H2 = P('H1'), P('H2')
    fn = (H2[2] - H1[2]).cross(H1[4] - H1[2]).normalized()
    fn = fn if fn.x > 0 else -fn
    v_ = vert_near(bmb, ec)
    c = v_.co.copy()
    n = sum((f_.normal for f_ in v_.link_faces), Vector()).normalized()
    n = n if n.x > 0 else -n
    bmb.free()
    c = c - n * 0.008                                   # the socket floor depth, as before
    bm = bmesh.new()
    lens(bm, c, n, 0.05, 0.04, 0.02)
    eye = object_from_bm('eye', bm)
    paint(eye, {'green': PAL['green'], 'yellow': PAL['yellow'], 'dark': PAL['dark']},
          lambda c_, n_, i: ('green' if (c_ - c).dot(n) < 0.037 else
                             'dark' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.008 else 'yellow'))
    # dorsal crest: small half spikes along the back ridge and the tail base
    bm = bmesh.new()
    for y in (-0.27, -0.14, -0.01, 0.12, 0.25, 0.38):
        crest(bm, tree, y, 0.036, 0.05 if -0.2 < y < 0.3 else 0.04)
    cr = object_from_bm('crest', bm)
    paint(cr, {'green': PAL['green']}, lambda c_, n_, i: 'green')
    # zygodactyl feet: two opposed grip pads per foot (one forward-in, one back-out), a V gap between them
    bm = bmesh.new()
    for sole in (FORE[4], HIND[4]):
        (cx, cy, _), rx, ry = sole
        for j, (d, L) in enumerate((((-0.35, -1.0), 0.035), ((0.35, 1.0), 0.028))):   # detail pass r11: shorter (L/t 6.8 -> r10 4.6-5.2 > 4.5)
            dv = Vector((d[0], d[1], 0.0)).normalized()
            root = Vector((cx + dv.x * 0.015, cy + dv.y * (ry * 0.35), 0.0))
            bundle(bm, root, dv, ry * 0.6 + L + 0.02, 0.036 - 0.003 * j, 0.045 - 0.002 * j, 0.006 + 0.002 * j)   # r11: 5 mm taller (t 26.7 < 26.9 mm)
    toes = object_from_bm('toes', bm)
    paint(toes, {'cream': PAL['cream']}, lambda c_, n_, i: 'cream')
    return [eye, cr, toes]


def stage4(k, body, pieces):
    TB = [(0.40, 0.54)] + [(TP0[i][0], TP0[i][1]) for i in (1, 3, 5, 7, 9, 11, 14)]
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('tail0', J['hips'], (0.0,) + TB[0], 'hips')]
    for i in range(len(TB) - 1):
        B.append(('tail%d' % (i + 1), (0.0,) + TB[i], (0.0,) + TB[i + 1], 'tail%d' % i, True))
    B += [('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
          ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
          ('hand.L', J['wrist'], J['ftoe'], 'forearm.L', True),
          ('thigh.L', J['hipL'], J['knee'], 'hips'),
          ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
          ('foot.L', J['ankle'], J['htoe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: slow breathing, a sway of the casque, the spiral tightening a touch and back
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (0, 0, 3), 'tail2': (3, 0, 0)},
                       24: {'neck': (0, 0, -3), 'head': (2, 0, 0)}, 36: {'chest': (1.5, 0, 0), 'tail2': (-3, 0, 0)}, 48: {}})
    # move: the chameleon's diagonal walk (LF + RH, then RF + LH), a body sway, the head held level
    A = 16
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'spine': (0, 0, 3)},
        9: {'forearm.R': (-25, 0, 0), 'shin.L': (-20, 0, 0), 'head': (0, 0, -2)},
        17: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'spine': (0, 0, -3)},
        25: {'forearm.L': (-25, 0, 0), 'shin.R': (-20, 0, 0), 'head': (0, 0, 2)},
        33: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'spine': (0, 0, 3)}})
    # attack: rock back, then a forward head strike with the casque
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-8, 0, 0), 'chest': (3, 0, 0), 'head': (-4, 0, 0), 'tail1': (4, 0, 0)},
        16: {'neck': (10, 0, 0), 'chest': (-6, 0, 0), 'head': (6, 0, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0)},
        20: {'neck': (12, 0, 0), 'chest': (-6, 0, 0), 'head': (10, 0, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.02, 0)}, 16: {'hips': (0, -0.04, 0)}, 20: {'hips': (0, -0.04, 0)},
             32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
