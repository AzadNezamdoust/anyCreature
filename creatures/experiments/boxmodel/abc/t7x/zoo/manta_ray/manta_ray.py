import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# manta ray (t7x zoo, wave-new). One spine loft of 12-vertex half rings (mouth -> rear body), a 6 -> 3 vertex
# tail whip, and everything else grown out of that loft:
# - the WINGS: the 2 x 14 equator faces under the whole wing root (y -0.90 .. 0.08) are opened and bridged out
#   level by level (a hug ring, then sections at constant span with fewer chord segments towards the tip), each
#   section a closed airfoil slab (top row, bottom row, a rim vertex at the leading and trailing edge), so the
#   wing is thick at the root and tapers, never a plate; the rim vertex loop is the back / belly colour border;
# - the CEPHALIC LOBES: a 3-face region on the head's front corner, extruded forward and curled down / in;
# - the DORSAL FIN: 4 top-seam faces extruded (the mirror closes it).
# Swimming: everything sits LIFT above the floor (the blueprint is the floor trace moved up by LIFT, rigidly).
LIFT = 0.45
META = dict(creature='manta_ray', model='opus', engine_glb='', stage1_tris=(1500, 4500), total_tris=(1800, 5500),
            closeups=[('head', (0.0, -1.18, 0.66), 0.30, 'hero'),
                      ('wing root', (0.42, -0.45, 0.66), 0.40, 'hero'),
                      ('wing tip', (1.05, -0.25, 0.70), 0.30, 'hero'),
                      ('tail root', (0.0, 0.40, 0.64), 0.30, 'back34')])

# ---------------------------------------------------------------- the loft (pre-lift z)
# (name, y, z bottom, z top, z equator, half width at the equator)
BODY = [
    ('H0', -1.10, 0.110, 0.335, 0.210, 0.200),
    ('H1', -1.04, 0.070, 0.362, 0.205, 0.262),
    ('H2', -0.97, 0.046, 0.383, 0.200, 0.300),
    ('W00', -0.90, 0.030, 0.390, 0.195, 0.322),       # wing root front
    ('W01', -0.83, 0.015, 0.393, 0.192, 0.335),
    ('W02', -0.76, 0.004, 0.395, 0.190, 0.340),
    ('W03', -0.69, 0.000, 0.393, 0.190, 0.340),
    ('W04', -0.62, 0.000, 0.390, 0.190, 0.336),
    ('W05', -0.55, 0.003, 0.385, 0.190, 0.330),
    ('W06', -0.48, 0.010, 0.378, 0.190, 0.320),
    ('W07', -0.41, 0.020, 0.372, 0.191, 0.310),
    ('W08', -0.34, 0.034, 0.368, 0.192, 0.298),
    ('W09', -0.27, 0.048, 0.362, 0.194, 0.284),
    ('W10', -0.20, 0.060, 0.355, 0.196, 0.268),
    ('W11', -0.13, 0.073, 0.346, 0.198, 0.250),
    ('W12', -0.06, 0.082, 0.334, 0.200, 0.230),
    ('W13', 0.01, 0.090, 0.316, 0.200, 0.210),
    ('W14', 0.08, 0.100, 0.292, 0.200, 0.190),        # wing root rear
    ('R0', 0.16, 0.112, 0.262, 0.193, 0.150),
    ('R1', 0.24, 0.124, 0.240, 0.186, 0.112),
    ('R2', 0.32, 0.137, 0.226, 0.182, 0.080),
    ('R3', 0.40, 0.150, 0.214, 0.180, 0.056),
]
# the tail whip: (name, y, z centre, half width); half height 0.8 x half width
TAIL = [('T0', 0.50, 0.178, 0.040), ('T1', 0.62, 0.175, 0.030), ('T2', 0.76, 0.171, 0.025), ('T3', 0.90, 0.167, 0.021),
        ('T4', 1.03, 0.164, 0.018), ('T5', 1.15, 0.161, 0.015), ('T6', 1.26, 0.158, 0.0125), ('T7', 1.36, 0.156, 0.010),
        ('T8', 1.44, 0.154, 0.008)]
TAIL_TIP = (0.0, 1.48, 0.153)
# 12-ring profile (x / W, z / H): 7 upper + 5 lower vertices; 6 = the equator. r01: a low roof that slopes into the
# wing, the wing root region is v4..v8 (4 faces tall, ~0.2 m), so the root is a broad slab, not a slot in a capsule
UPPER = [(0, 1), (0.30, 0.96), (0.56, 0.84), (0.78, 0.66), (0.93, 0.50), (0.985, 0.25), (1, 0)]
LOWER = [(0.985, -0.25), (0.93, -0.50), (0.74, -0.80), (0.42, -0.96), (0, -1)]
ROOT = (4, 8)                                    # the wing root region: faces 4..7 (vertices 4..8)
MOUTH = dict(y=-1.094,   # relock 3: 6 mm recess (2.5 cm made a creased lip edge with needle fans)
             zm=0.165, sx=0.78, sz=0.42)    # the lip ring: the front ring scaled about the mouth line

# wing sections: (x at the leading edge, x at the trailing edge, chord segments, z of the mid surface, thickness)
WING = [(0.46, 0.40, 12, 0.195, 0.150),          # r01: thicker (sheet front: ~0.2 at the root, ~0.1 at mid span)
        (0.57, 0.53, 10, 0.188, 0.125),          # r03: mid span thicker again, plus a nose-up chord pitch
        (0.69, 0.66, 8, 0.186, 0.102),
        (0.81, 0.79, 7, 0.191, 0.082),
        (0.93, 0.92, 6, 0.203, 0.064),
        (1.04, 1.03, 4, 0.224, 0.048),
        (1.12, 1.11, 3, 0.249, 0.036),
        (1.18, 1.17, 2, 0.273, 0.028)]
WING_TIP = (1.215, 1.205, 1, 0.290, 0.022, -0.240, -0.165)    # + its own leading / trailing y
LE = [(0.30, -0.94), (0.371, -0.892), (0.99, -0.452), (1.177, -0.285), (1.25, -0.20)]    # top trace, leading edge
TE = [(0.10, 0.19), (0.175, 0.151), (0.733, -0.134), (1.039, -0.159), (1.169, -0.118), (1.25, -0.10)]
EDGE_MIN = 0.014
PITCH = 0.06                                         # r03: leading edge up, trailing edge down (per m of span left)                                     # no wing edge thinner than this (membrane floor ~11.6 mm)

# cephalic lobes: (centre x, centre y, z top, z bottom, thickness, inward curl of the lower edge)
LOBE = [(0.232, -1.150, 0.290, 0.150, 0.060, 0.000),      # r02: the path curls in (top view "C" pair), lower edge rolls in
        (0.245, -1.230, 0.300, 0.090, 0.050, 0.020),      # r04: further forward and lower (side view C to y -1.47, z 0.03)
        (0.238, -1.310, 0.300, 0.035, 0.044, 0.045),
        (0.205, -1.385, 0.285, 0.030, 0.040, 0.055),
        (0.145, -1.430, 0.250, 0.045, 0.036, 0.050),
        (0.085, -1.440, 0.205, 0.075, 0.032, 0.040)]
# pelvic fins (top view notches by the tail root): (x, front y, rear y, z centre, height)
PELVIC = [(0.150, 0.170, 0.250, 0.186, 0.055),
          (0.192, 0.225, 0.290, 0.180, 0.032)]
# dorsal fin: (lead y, lead z, trail y, trail z, half thickness)
DORSAL = [(-0.235, 0.395, 0.005, 0.345, 0.032),
          (-0.160, 0.445, -0.005, 0.410, 0.020),
          (-0.085, 0.500, -0.015, 0.480, 0.012),
          (-0.045, 0.545, -0.020, 0.540, 0.008)]

# the skeleton (x >= 0 half; .L on +X), lifted
def L(x, y, z):
    return (x, y, z + LIFT)


J = dict(root=L(0, 0.40, 0.19), body=L(0, -0.40, 0.20), head=L(0, -0.80, 0.21), nose=L(0, -1.10, 0.21),
         tail0=L(0, 0.40, 0.18), tail1=L(0, 0.62, 0.175), tail2=L(0, 0.95, 0.166), tail3=L(0, 1.46, 0.154),
         wing=L(0.30, -0.42, 0.195), wingmid=L(0.74, -0.36, 0.19), wingtip=L(1.19, -0.21, 0.28),
         lobe=L(0.215, -1.08, 0.215), lobemid=L(0.236, -1.30, 0.19), lobetip=L(0.12, -1.45, 0.14))


def interp(tab, x):
    for (x0, y0), (x1, y1) in zip(tab, tab[1:]):
        if x <= x1 or (x1, y1) == tab[-1]:
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return tab[-1][1]


def ring12(y, zb, zt, ze, W):
    return ([(W * fx, y, ze + (zt - ze) * fz + LIFT) for fx, fz in UPPER] +
            [(W * fx, y, ze + (ze - zb) * fz + LIFT) for fx, fz in LOWER])


def ring_tail(y, zc, w, n):
    h = 0.8 * w
    if n == 6:      # angles 90, 45, 0, -36, -72, -90 (the 12-ring's 0, 3, 6, 8, 10, 11)
        ang = [90, 45, 0, -36, -72, -90]
    else:
        ang = [90, 0, -90]
    pts = []
    for a in ang:
        t = math.radians(a)
        pts.append((0.0 if abs(a) == 90 else w * math.cos(t) ** 0.8, y, zc + h * math.sin(t) + LIFT))
    return pts


def bridge_map(bm, a, b, m):
    """b[i] sits over a[m[i]]: each span of b takes the run of a between, as one face (quad or n-gon)."""
    return [bm.faces.new(a[m[i]:m[i + 1] + 1] + [b[i + 1], b[i]]) for i in range(len(b) - 1)]


def walk(bm, A, B, ua, ub):
    """Quads and triangles between two open rows (A over param ua, B over ub, both 0 -> 1)."""
    fs = []
    i = j = 0
    while i < len(A) - 1 or j < len(B) - 1:
        if i == len(A) - 1:
            fs.append(bm.faces.new([A[i], B[j + 1], B[j]])); j += 1
        elif j == len(B) - 1:
            fs.append(bm.faces.new([A[i], A[i + 1], B[j]])); i += 1
        else:
            da, db = ua[i + 1], ub[j + 1]
            step = min(ua[i + 1] - ua[i], ub[j + 1] - ub[j])
            if abs(da - db) < 0.35 * step:
                fs.append(bm.faces.new([A[i], A[i + 1], B[j + 1], B[j]])); i += 1; j += 1
            elif da < db:
                fs.append(bm.faces.new([A[i], A[i + 1], B[j]])); i += 1
            else:
                fs.append(bm.faces.new([A[i], B[j + 1], B[j]])); j += 1
    return fs


def wing_section(xf, xr, m, zc, t, yl=None, yt=None):
    """One wing level: {'top': [...], 'bot': [...], 'fm': p, 'rm': p, 'u': [...]} (points)."""
    yl = interp(LE, xf) if yl is None else yl
    yt = interp(TE, xr) if yt is None else yt
    us = [i / m for i in range(m + 1)]
    top, bot = [], []
    for u in us:
        x = xf + (xr - xf) * u
        y = yl + (yt - yl) * u
        tl = max(EDGE_MIN, t * (0.55 + 0.45 * math.sin(math.pi * u ** 0.75)) * (1 - 0.25 * u))
        zm = zc + 0.15 * t * math.sin(math.pi * u) + PITCH * max(0.0, 1.25 - x) * (0.5 - u)
        top.append((x, y, zm + tl / 2 + LIFT))
        bot.append((x, y, zm - tl / 2 + LIFT))
    t0 = abs(top[0][2] - bot[0][2]); t1 = abs(top[-1][2] - bot[-1][2])
    fm = (xf, yl - 0.35 * t0, (top[0][2] + bot[0][2]) / 2)
    rm = (xr, yt + 0.25 * t1, (top[-1][2] + bot[-1][2]) / 2)
    return dict(top=top, bot=bot, fe=[fm], re=[rm], u=us)


def sec_by_name():
    return {s[0]: s for s in BODY}


SIX = [(0, 1), (0.72, 0.72), (1, 0), (0.8, -0.6), (0.42, -0.95), (0, -1)]
RING6 = ('R2', 'R3')          # relock 2: the thin rear stations are 6-vertex rings (12 there left 8 mm equator strips)


def ring6(y, zb, zt, ze, W):
    return [(W * fx, y, ze + (zt - ze if fz >= 0 else ze - zb) * fz + LIFT) for fx, fz in SIX]


def body_rings_pts():
    out = []
    for (nm, y, zb, zt, ze, W) in BODY:
        out.append((nm, (ring6 if nm in RING6 else ring12)(y, zb, zt, ze, W)))
    return out


def grow(bm, faces, place):
    """Extrude a face region level by level. The region's vertices get a role from role0 (computed once on the
    base); place(level, role) -> xyz. Walls an extrusion leaves on the mirror plane are removed."""
    faces = list(faces)
    base = {v for f in faces for v in f.verts}
    roles = {v: place('role', v) for v in base}
    lev = 0
    while True:
        if place(lev, None) is None:
            break
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        wall = [f for f in r['sides'] if all(abs(v.co.x) < 1e-6 for v in f.verts)]
        if wall:
            bmesh.ops.delete(bm, geom=wall, context='FACES')
        for v, ro in new.items():
            v.co = Vector(place(lev, ro))
        faces, roles = r['faces'], new
        lev += 1
    return faces


def lobe_place(base_verts_info):
    """Roles: (side f/r, vertical param 0 top .. 1 bottom). Each level: a vertical plate along the lobe path."""
    C = [Vector((cx, cy, 0)) for (cx, cy, *_r) in LOBE]

    def f(lev, ro):
        if lev == 'role':
            return base_verts_info(ro)
        if lev >= len(LOBE):
            return None
        if ro is None:
            return True
        cx, cy, zt, zb, th, curl = LOBE[lev]
        a = C[max(0, lev - 1)] if lev > 0 else Vector((J['lobe'][0], J['lobe'][1], 0))
        b = C[min(len(C) - 1, lev + 1)]
        T = (b - a).normalized()
        n = Vector((0, 0, 1)).cross(T).normalized()       # outward (+x when going forward)
        side, v = ro
        z = zt + (zb - zt) * v + LIFT
        c = Vector((cx, cy, z)) - n * curl * v * v
        return tuple(c + n * (th / 2 if side == 'r' else -th / 2))
    return f


def pelvic_place(roles):
    def f(lev, ro):
        if lev == 'role':
            return roles[ro]
        if lev >= len(PELVIC):
            return None
        if ro is None:
            return True
        x, yf, yr, zc, h = PELVIC[lev]
        side, v = ro
        return (x, yf if side == 'f' else yr, zc + (0.5 - v) * h + LIFT)
    return f


def dorsal_place(y0, y1):
    def f(lev, ro):
        if lev == 'role':
            v = ro
            return ((v.co.y - y0) / (y1 - y0), 's' if abs(v.co.x) < 1e-6 else 'o')
        if lev >= len(DORSAL):
            return None
        if ro is None:
            return True
        yl, zl, yt, zt, ht = DORSAL[lev]
        u, side = ro
        y = yl + (yt - yl) * u
        z = zl + (zt - zl) * u + LIFT
        return (0.0 if side == 's' else ht, y, z)
    return f


def stage1(k):
    bm = bmesh.new()
    names = [s[0] for s in BODY]
    idx = {n: i for i, n in enumerate(names)}
    rings = [ring(bm, p) for _n, p in body_rings_pts()]
    def angp(vs):
        zc = (vs[0].co.z + vs[-1].co.z) / 2
        return [(90.0 - math.degrees(math.atan2(v.co.z - zc, max(v.co.x, 1e-9)))) / 180.0 for v in vs]
    spans = [bridge(bm, rings[i], rings[i + 1]) if len(rings[i]) == len(rings[i + 1])
             else walk(bm, rings[i], rings[i + 1], angp(rings[i]), angp(rings[i + 1])) for i in range(len(rings) - 1)]
    # the mouth: a lip ring recessed behind the front ring, capped (the mouth floor)
    H0 = BODY[0]
    zm = MOUTH['zm'] + LIFT
    lip = ring(bm, [(p[0] * MOUTH['sx'], MOUTH['y'], zm + (p[2] - zm) * MOUTH['sz']) for p in ring12(*H0[1:])])
    bridge(bm, rings[0], lip)
    cap(bm, lip)
    # the tail: 12 -> 6 -> 3 vertex rings, ending in a point
    tr = [ring(bm, ring_tail(y, zc, w, 6 if i == 0 else 3)) for i, (_n, y, zc, w) in enumerate(TAIL)]
    # relock 1: quads + triangles walked by angle round the ring (the n-gon fans left a 9 mm seam strip, s4 r02)
    bridge(bm, rings[-1], tr[0])
    walk(bm, tr[0], tr[1], angp(tr[0]), angp(tr[1]))
    for a, b in zip(tr[1:], tr[2:]):
        bridge(bm, a, b)
    tip = bm.verts.new(Vector((TAIL_TIP[0], TAIL_TIP[1], TAIL_TIP[2] + LIFT)))
    bm.faces.new([tr[-1][0], tr[-1][1], tip]); bm.faces.new([tr[-1][1], tr[-1][2], tip])
    recalc_normals(bm)

    # ---- cephalic lobes: faces 4..6 of the H0-H1 span (the head's front corner)
    lobe_faces = [spans[idx['H0']][j] for j in (4, 5, 6)]
    vf = {rings[idx['H0']][j]: ('f', (j - 4) / 3) for j in (4, 5, 6, 7)}
    vf.update({rings[idx['H1']][j]: ('r', (j - 4) / 3) for j in (4, 5, 6, 7)})
    grow(bm, lobe_faces, lobe_place(lambda v: vf[v]))

    # ---- pelvic fins: faces 4..7 of the R0-R1 span
    pr = {rings[idx['R0']][j]: ('f', (j - 4) / 4) for j in range(4, 9)}
    pr.update({rings[idx['R1']][j]: ('r', (j - 4) / 4) for j in range(4, 9)})
    grow(bm, [spans[idx['R0']][j] for j in range(4, 8)], pelvic_place(pr))

    # ---- dorsal fin: top seam faces of W09..W13
    dfaces = [spans[i][0] for i in range(idx['W09'], idx['W13'])]
    grow(bm, dfaces, dorsal_place(BODY[idx['W09']][1], BODY[idx['W13']][1]))

    # ---- wings: open the 4 x 14 faces under the root (v4..v8), bridge the sections out
    a, b = idx['W00'], idx['W14']
    j0, j1 = ROOT
    region = [spans[s][j] for s in range(a, b) for j in range(j0, j1)]
    bmesh.ops.delete(bm, geom=region, context='FACES')
    uu = [(BODY[s][1] - BODY[a][1]) / (BODY[b][1] - BODY[a][1]) for s in range(a, b + 1)]
    L0 = dict(top=[rings[s][j0] for s in range(a, b + 1)], bot=[rings[s][j1] for s in range(a, b + 1)],
              fe=[rings[a][j] for j in range(j0 + 1, j1)], re=[rings[b][j] for j in range(j0 + 1, j1)], u=uu)
    # level 1: the hug ring, 5.5 cm out, a little thinner
    ze = lambda s: BODY[s][4] + LIFT
    def hug(v, s):
        p = v.co
        return (p.x + 0.055, p.y, ze(s) + (p.z - ze(s)) * 0.92)
    L1p = dict(top=[hug(rings[s][j0], s) for s in range(a, b + 1)], bot=[hug(rings[s][j1], s) for s in range(a, b + 1)],
               fe=[hug(v, a) for v in L0['fe']], re=[hug(v, b) for v in L0['re']], u=uu)
    L1p['fe'] = [(p[0], p[1] - 0.02, p[2]) for p in L1p['fe']]
    secs = [L1p] + [wing_section(*w) for w in WING] + [wing_section(*WING_TIP[:5], yl=WING_TIP[5], yt=WING_TIP[6])]

    def colp(c):
        zs = [v.co.z for v in c]
        return [(zs[0] - z) / (zs[0] - zs[-1]) for z in zs]
    prev = L0
    for S in secs:
        cur = dict(top=ring(bm, S['top']), bot=ring(bm, S['bot']), fe=ring(bm, S['fe']), re=ring(bm, S['re']), u=S['u'])
        walk(bm, prev['top'], cur['top'], prev['u'], cur['u'])
        walk(bm, prev['bot'], cur['bot'], prev['u'], cur['u'])
        for e in ('fe', 're'):
            i_ = 0 if e == 'fe' else -1
            A = [prev['top'][i_]] + prev[e] + [prev['bot'][i_]]
            B = [cur['top'][i_]] + cur[e] + [cur['bot'][i_]]
            walk(bm, A, B, colp(A), colp(B))
        prev = cur
    cap(bm, prev['top'] + prev['re'] + list(reversed(prev['bot'])) + list(reversed(prev['fe'])))
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def ring_pt(nm, j):
    sec = next(b for b in BODY if b[0] == nm)
    return Vector(ring12(*sec[1:])[j])


def eye_face_centre():
    """Centre of face 4 of the H2-W00 span (vertices 4-5): the head side just ahead of the wing's leading edge.
    s4 r02: moved one span back and out (was H1-H2, x 0.27) so the lobe root no longer hides it from the front."""
    return (ring_pt('H2', 4) + ring_pt('H2', 5) + ring_pt('W00', 4) + ring_pt('W00', 5)) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.035 and abs(c.y - ec0.y) < 0.05
                                        and abs(c.z - ec0.z) < 0.04)
    bm = edit(body)
    f = face_near(bm, ec0, n=Vector((1, 0, 0.5)).normalized())
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face'):
        inner = inset(bm, [f], 0.30, 0.0)
    move(list(inner[0].verts), -fn * 0.008)
    # f3: bevel the forehead: the front ring's top (v0..v3) back 25 mm and down 12 mm, so the head front is a sloped
    # plane over the mouth, not a vertical wall (az0)
    for j in range(4):
        v = vert_near(bm, ring_pt('H0', j))
        v.co.y += 0.025
        if j < 3:
            v.co.z -= 0.012
    scroll_lobes(bm)
    swept_tips(bm)
    commit(body, bm)
    bm.free()


# ---- weakfix 2026-10-23: rolled scroll lobes (were flat vertical plates), swept pointed wing tips
ROLL = [0.0, 0.25, 0.47, 0.47, 0.38, 0.25]          # r15: x0.85 (r14 slivers 2.0 % at the limit); r14 gentler (r13: 12 hits)
ROLL_R = 0.05                                      # roll radius


def scroll_pt(lev, side, v):
    """The lobe cross-section as a J-scroll: straight down the outer face, the lower edge rolled inward and up."""
    cx, cy, zt, zb, th, curl = LOBE[lev]
    C = [Vector((c_[0], c_[1], 0)) for c_ in LOBE]
    a = C[max(0, lev - 1)] if lev > 0 else Vector((J['lobe'][0], J['lobe'][1], 0))
    b = C[min(len(C) - 1, lev + 1)]
    T = (b - a).normalized()
    n = Vector((0, 0, 1)).cross(T).normalized()
    H = zt - zb
    R = min(0.42 * H, ROLL_R) * ROLL[lev]
    # (inward u, z) polyline for v = 0, 1/3, 2/3, 1
    flat = [(0.0, zt), (0.0, zt - H / 3), (0.0, zt - 2 * H / 3), (0.0, zb)]
    roll = [(0.0, zt), (0.0, zb + 1.6 * R), (0.7 * R, zb + 0.15 * R), (1.4 * R, zb + 0.6 * R)]
    th = th * (1 - 0.3 * ROLL[lev])                   # r11: a thinner rolled edge (no inner-side crossing)
    w = ROLL[lev]
    pts = [(fa[0] + (fb[0] - fa[0]) * w, fa[1] + (fb[1] - fa[1]) * w) for fa, fb in zip(flat, roll)]
    k = int(round(v * 3))
    pa, pb = pts[max(0, k - 1)], pts[min(3, k + 1)]
    tu, tz = pb[0] - pa[0], pb[1] - pa[1]
    ln = math.hypot(tu, tz) or 1.0
    nu, nz = tz / ln, -tu / ln                       # outward normal in (u, z): (-1, 0) on the straight part
    sgn = -1 if side == 'r' else 1                   # r13: 'r' sits at +n (r10-r12 had the sides swapped: a twist at the root)
    u = pts[k][0] - nu * sgn * th / 2 + curl * v * v
    z = pts[k][1] + nz * sgn * th / 2
    c = Vector((cx, cy, z + LIFT)) - n * u
    return c


def scroll_lobes(bm):
    f = lobe_place(lambda v: None)
    for lev in range(len(LOBE)):
        for side in ('f', 'r'):
            for k in range(4):
                v_ = k / 3
                p = Vector(f(lev, (side, v_)))
                vt = vert_near(bm, p)
                if vt is None or (vt.co - p).length > 1e-4:
                    continue
                vt.co = scroll_pt(lev, side, v_)


def swept_tips(bm):
    """The outer wing (x > 0.95) narrows and sweeps back into a point, the tip curling up (sheet top / front)."""
    for v in bm.verts:
        x = v.co.x
        if x <= 0.95:
            continue
        s = min(1.0, (x - 0.95) / (WING_TIP[0] - 0.95))
        ym = (interp(LE, min(x, 1.25)) + interp(TE, min(x, 1.25))) / 2
        v.co.y = ym + (v.co.y - ym) * (1 - 0.0 * s * s) + 0.10 * s * s   # r15: no chord squeeze (r14 0.3: slivers 2.0 %)
        v.co.z += 0.05 * s * s                        # r11: no span extension (r10 +7 cm: tips dipped under the belly in the flap)


# flat colours off the sheet: slate back, white belly, darker fins / tail, a dark mouth, black lens
PAL = {'back': '#47505a', 'belly': '#e8e7e2', 'fin': '#3a4149', 'mouth': '#2a2e34', 'eye': '#0e0f11'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z - LIFT
    if abs(y - MOUTH['y']) < 0.0008 and n.y < -0.95 and x < 0.16:
        return 'mouth'                                           # the recessed mouth floor
    if -1.105 < y < -1.07 and x < 0.21 and n.y < -0.6:                 # s3 r2: the head front, white chin under the mouth
        return 'belly' if z < MOUTH['zm'] + 0.01 else 'back'
    if y > 0.42:
        return 'fin'                                             # the whip tail
    if z > 0.40 or (-0.30 < y < 0.06 and z > 0.33 and x < 0.04):
        return 'fin'                                             # dorsal fin
    if y < -1.11 and x > 0.04:                                   # cephalic lobes: dark outside, white inside
        if n.z > 0.6 or n.z < -0.85:                             # f1: no white blocks on the outer face
            return 'back' if n.z > 0 else 'belly'
        px, py = 0.13 - x, -1.27 - y                             # s3 r3: inner = faces turned to the C's centre
        return 'belly' if (n.x if c.x > 0 else -n.x) * px + n.y * py > 0 else 'back'
    return 'back' if n.z >= -0.05 else 'belly'                   # the border runs on the rim / equator loops


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A small low-poly lens eye: back cone, ring, front fan."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 4 for k_ in range(8)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.4)
    for j in range(8):
        a, b = j, (j + 1) % 8
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


EYE_R = 0.023                                           # s4 r02: 46 mm (was 38 = 0.059 head)


def stage3(k, body):
    paint(body, PAL, body_rule)
    tree = body_bvh(body)
    c, n, _i, _d = tree.find_nearest(eye_face_centre() - Vector((0.008, 0, 0)))
    n = n if n.x > 0 else -n
    n = (n + Vector((0, -0.55, 0))).normalized()                # look forward (s4 r02: front view)
    bm = bmesh.new()
    lens(bm, c + n * 0.002, n, EYE_R, 0.009)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, lambda c_, n_, i: 'eye')
    return [eye]


def stage4(k, body, pieces):
    B = [('root', L(0, 0.35, 0.19), L(0, -0.35, 0.20), None),
         ('chest', L(0, -0.35, 0.20), L(0, -0.92, 0.205), 'root', True),
         ('head', L(0, -0.92, 0.205), L(0, -1.12, 0.21), 'chest', True),
         ('tail0', J['tail0'], J['tail1'], 'root'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('wing.L', J['wing'], J['wingmid'], 'root'),
         ('wing1.L', J['wingmid'], J['wingtip'], 'wing.L', True),
         ('lobe.L', J['lobe'], J['lobemid'], 'head'),
         ('lobe1.L', J['lobemid'], J['lobetip'], 'lobe.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)

    def flap(a, b, lob=0.0, tl=0.0):
        return {'wing.L': (0, 0, a), 'wing1.L': (0, 0, b), 'wing.R': (0, 0, -a), 'wing1.R': (0, 0, -b),
                'lobe.L': (0, 0, lob), 'lobe.R': (0, 0, -lob), 'tail1': (tl, 0, 0), 'tail2': (tl * 1.5, 0, 0)}
    # idle: a slow glide, the wing tips trimming, lobes breathing
    idle, idl = {}, {}
    for f in range(1, 50, 8):
        ph = 2 * math.pi * (f - 1) / 48
        idle[f] = flap(5 * math.sin(ph), 4 * math.sin(ph - 0.9), 3 * math.sin(ph), 2 * math.sin(ph))
        idl[f] = {'root': (0, 0, -0.012 * math.sin(ph))}
    clip(rig, 'idle', idle, loc=idl)
    # move: the swim stroke, the wing wave runs root -> tip, the body heaves against it
    mv, ml = {}, {}
    for f in range(1, 34, 4):
        ph = 2 * math.pi * (f - 1) / 32
        mv[f] = flap(22 * math.sin(ph), 16 * math.sin(ph - 0.8), 0.0, 4 * math.sin(ph - 1.5))
        ml[f] = {'root': (0, 0, -0.03 * math.sin(ph))}
    clip(rig, 'move', mv, loc=ml)
    # attack: wind up, one hard power stroke and a lunge with the lobes flared, recover
    clip(rig, 'attack', {1: flap(0, 0), 8: flap(28, 18, -6, -4), 14: flap(-26, -10, 14, 6), 20: flap(-10, -18, 14, 4),
                         26: flap(8, 2, 6, 0), 32: flap(0, 0)},
         loc={1: {'root': (0, 0, 0)}, 8: {'root': (0, 0.05, -0.02)}, 14: {'root': (0, -0.22, 0.05)},
              20: {'root': (0, -0.30, 0.03)}, 26: {'root': (0, -0.12, 0.0)}, 32: {'root': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
