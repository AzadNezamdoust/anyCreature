import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
from smooth_borders import smooth_borders

# brown bear, t7 hand box-model: one spine loft of 10-vertex half rings (tail stub -> nose, 27 stations), legs
# extruded as 3x3-face regions of the lower flank into 12-sided horizontal rings, ears as 1-face extrusions.
# Poly pass 3: stations and ring vertices re-fitted to the traced sheet (blueprint.json), world coordinates.
META = dict(creature='bear', model='opus', stage1_tris=(1200, 3200), total_tris=(2200, 4500),
            closeups=[('head', (0.0, -0.76, 0.95), 0.22, 'hero'),
                      ('front paw', (0.205, -0.38, 0.06), 0.14, 'hero'),
                      ('hind paw', (0.205, 0.50, 0.06), 0.14, 'hero')])

# fix pass 1 head transform, kept only to map world points back for the colour rule
HS, HPY, HPZ, HDY = 1.10, -0.60, 0.93, -0.03
def hx(y, z):
    return (HPY + (y - HPY) * HS + HDY, HPZ + (z - HPZ) * HS)
def hinv(y, z):
    return (HPY + (y - HDY - HPY) / HS, HPZ + (z - HPZ) / HS)


J = dict(
    hips=(0.0, 0.55, 0.78), spine=(0.0, 0.15, 0.80), chest=(0.0, -0.25, 0.85),
    neck=(0.0, -0.45, 0.95), head=(0.0, -0.64, 0.95), nose=(0.0, -0.92, 0.83),
    tail0=(0.0, 0.84, 0.84), tail1=(0.0, 0.91, 0.81),
    shoulder=(0.205, -0.21, 0.62), elbow=(0.205, -0.215, 0.36), wrist=(0.205, -0.25, 0.10),
    fpaw=(0.205, -0.29, 0.03), ftoe=(0.205, -0.48, 0.02),
    hipL=(0.21, 0.60, 0.62), knee=(0.21, 0.62, 0.34), hock=(0.205, 0.665, 0.10),
    hpaw=(0.205, 0.63, 0.03), htoe=(0.205, 0.40, 0.02),
    ear=(0.16, -0.635, 1.12), eartip=(0.164, -0.64, 1.21),
)

# half-ring profiles, top seam -> bottom seam, 10 vertices: (x as a fraction of W, h as a fraction of T / B)
# MIX pass: torso keeps the before3 6-vertex sections; the 4 extra ring vertices sit ON the old edges (flat planes)
def _rs(p6):
    m = lambda a, b, t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    v = p6
    return [v[0], m(v[0], v[1], 0.5), v[1], m(v[1], v[2], 1 / 3), m(v[1], v[2], 2 / 3), v[2], m(v[2], v[3], 0.5), v[3], v[4], v[5]]
BODY = _rs([(0, 1), (0.68, 0.93), (1, -0.05), (0.92, -0.5), (0.5, -0.88), (0, -1)])
REAR = _rs([(0, 1), (0.65, 0.9), (1, 0.2), (0.9, -0.45), (0.5, -0.87), (0, -1)])
HEADB = [(0, 1), (0.3, 1), (0.58, 0.97), (0.82, 0.82), (0.96, 0.55), (1, 0.15), (0.94, -0.3), (0.78, -0.62), (0.48, -0.88), (0, -1)]
HEADF = [(0, 1), (0.38, 0.97), (0.68, 0.86), (0.88, 0.62), (0.97, 0.3), (1, -0.05), (0.92, -0.42), (0.76, -0.7), (0.46, -0.9), (0, -1)]
MUZ = [(0, 1), (0.38, 0.98), (0.68, 0.9), (0.9, 0.68), (1, 0.35), (1, 0.0), (0.95, -0.35), (0.8, -0.65), (0.5, -0.88), (0, -1)]
TAIL = [(0, 1), (0.4, 0.92), (0.7, 0.72), (0.9, 0.45), (1, 0.12), (0.97, -0.2), (0.85, -0.5), (0.65, -0.75), (0.38, -0.92), (0, -1)]
NV = 10
EYE_J = 3                    # the eye face: ring verts 3-4 between H1 and H2
LEG_J = (5, 7)               # leg roots: faces 5..7 of the lower flank


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off the traced side outline."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)



# Pass 9 (dense + clean): the before3 torso sections are the KEYS; 17 torso stations (the 2x count) are sampled
# on a Catmull-Rom curve through them, so ring sizes change smoothly (no rib bands), straight runs stay co-planar
# (collinear keys give linear stations) and the hump and rump bends get the extra rings. The brisket keys are
# deeper than r8 so the chest closes down onto the fore-leg tops (owner crop: white gap at the fore-leg root).
KEYS = [  # (top (y, z), bottom (y, z), W)
    ((0.83, 0.90), (0.875, 0.45), 0.22),    # R0
    ((0.74, 0.95), (0.82, 0.38), 0.33),     # R1
    ((0.60, 0.99), (0.58, 0.35), 0.38),     # R2
    ((0.42, 1.04), (0.42, 0.34), 0.37),     # W0
    ((0.22, 1.07), (0.22, 0.33), 0.37),     # M0
    ((0.03, 1.13), (0.03, 0.34), 0.37),     # M1
    ((-0.12, 1.25), (-0.12, 0.365), 0.38),  # C0
    ((-0.24, 1.29), (-0.31, 0.39), 0.36),   # C1
    ((-0.36, 1.22), (-0.46, 0.48), 0.3),    # C2
    ((-0.48, 1.14), (-0.56, 0.67), 0.25),   # N0
]


def key_at(u):
    """Catmull-Rom through KEYS at fractional key index u."""
    i = min(int(u), len(KEYS) - 2); t = u - i
    g = lambda k: KEYS[max(0, min(len(KEYS) - 1, k))]
    p0, p1, p2, p3 = g(i - 1), g(i), g(i + 1), g(i + 2)
    cr = lambda a, b, c, d: 0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3)
    pt = lambda m: tuple(cr(p0[m][q], p1[m][q], p2[m][q], p3[m][q]) for q in range(2))
    return pt(0), pt(1), cr(p0[2], p1[2], p2[2], p3[2])


TORSO = [('R0', 0), ('R0a', 0.5), ('R1', 1), ('R1a', 1.67), ('R1b', 2.33), ('W0', 3), ('W1', 3.5), ('M0', 4),
         ('M0a', 4.5), ('M1', 5), ('M1a', 5.25), ('C0', 6), ('C0a', 6.5), ('C1', 7), ('C2', 8), ('C2a', 8.5), ('N0', 9)]

SECS = [
    tb('T0', (0.905, 0.84), (0.905, 0.79), 0.035, TAIL),
    tb('T1', (0.875, 0.88), (0.89, 0.755), 0.065, TAIL),
] + [tb(nm, *key_at(u), REAR if nm == 'R0' else BODY) for nm, u in TORSO] + [
    tb('N1', (-0.565, 1.155), (-0.59, 0.69), 0.225, HEADB),
    tb('H0', (-0.615, 1.15), (-0.635, 0.70), 0.2, HEADB),
    tb('H0b', (-0.675, 1.09), (-0.69, 0.712), 0.165, HEADB),
    tb('H1', (-0.735, 1.04), (-0.745, 0.725), 0.15, HEADF),
    tb('H2', (-0.79, 0.955), (-0.795, 0.733), 0.112, MUZ),
    tb('H2a', (-0.835, 0.926), (-0.84, 0.741), 0.094, MUZ),
    tb('H3', (-0.875, 0.902), (-0.875, 0.755), 0.08, MUZ),
    tb('H4', (-0.925, 0.866), (-0.912, 0.79), 0.062, MUZ),
]
IDX = {nm: i for i, (nm, *_r) in enumerate(SECS)}
FORE_ROOT, HIND_ROOT, EAR_SPAN = ('M1a', 3), ('R1', 3), 'H0'   # fore M1a..C1, hind R1..W0

# limb sections: (centre xyz, rx, ry) - horizontal 12-gons; bear legs are thick pillars (sheet side view)
FORE = [((0.215, -0.215, 0.36), 0.17, 0.19), ((0.205, -0.225, 0.29), 0.14, 0.18), ((0.205, -0.235, 0.22), 0.137, 0.172),
        ((0.203, -0.245, 0.16), 0.134, 0.165), ((0.2, -0.255, 0.10), 0.13, 0.16), ((0.2, -0.29, 0.045), 0.14, 0.2),
        ((0.2, -0.32, 0.0), 0.145, 0.24)]
HIND = [((0.215, 0.605, 0.34), 0.17, 0.175), ((0.21, 0.635, 0.29), 0.145, 0.2), ((0.205, 0.67, 0.22), 0.14, 0.21),
        ((0.205, 0.685, 0.15), 0.135, 0.215), ((0.205, 0.685, 0.10), 0.13, 0.215), ((0.205, 0.625, 0.045), 0.135, 0.255),
        ((0.205, 0.605, 0.0), 0.14, 0.265)]
EAR = [((0.155, -0.635, 1.15), 0.045, 0.038, 0.01), ((0.157, -0.637, 1.185), 0.041, 0.031, 0.0), ((0.159, -0.64, 1.21), 0.021, 0.015, 0.0)]


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


def leg_grid(nsp, j0, j1):
    """Roles of a leg-root region: the (ring a = 0..nsp from the rear, vertex b = j0..j1+1) grid. The boundary
    walks round as an even 12-gon (corner (rear, outer) at 45 deg); inner grid points keep their (u, s)."""
    nb = j1 + 2 - j0
    per = [(0, b) for b in range(j0, j1 + 2)] + [(a, j1 + 1) for a in range(1, nsp + 1)] + \
          [(nsp, b) for b in range(j1, j0 - 1, -1)] + [(a, j0) for a in range(nsp - 1, 0, -1)]
    roles = {g: ('b', math.radians(45 + 360.0 * k / len(per))) for k, g in enumerate(per)}
    for a in range(1, nsp):
        for b in range(j0 + 1, j1 + 1):
            roles[(a, b)] = ('i', 1 - 2.0 * (b - j0) / (nb - 1), 1 - 2.0 * a / nsp)
    return roles


def leg_pos(sec, role):
    (cx, cy, cz), rx, ry = sec
    if role[0] == 'b':
        return (cx + rx * math.cos(role[1]), cy + ry * math.sin(role[1]), cz)
    return (cx + rx * 0.7 * role[1], cy + ry * 0.7 * role[2], cz)


def ring_pts(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return sec_pts(c, a, T, B, W, p)


def ear_face(rings_pts):
    """The skull face (index j on span EAR_SPAN) nearest the ear base."""
    i = IDX[EAR_SPAN]
    A, Bq, e = rings_pts[i], rings_pts[i + 1], EAR[0][0]
    d = lambda j: sum(((A[j][k] + A[j + 1][k] + Bq[j][k] + Bq[j + 1][k]) / 4 - e[k]) ** 2 for k in range(3))
    return min(range(NV - 1), key=d)


def geo_polys():
    """Pure-python stage-1 surface (x >= 0 half) as 3D polygons, for the silhouette preview."""
    R = [sec_pts(c, a, T, B, W, p) for (nm, c, a, T, B, W, p) in SECS]
    out = [R[0], R[-1]]
    for i in range(len(R) - 1):
        for j in range(NV - 1):
            out.append([R[i][j], R[i][j + 1], R[i + 1][j + 1], R[i + 1][j]])
    for (nm, nsp), secs in ((FORE_ROOT, FORE), (HIND_ROOT, HIND)):
        i0 = IDX[nm]
        roles = leg_grid(nsp, *LEG_J)
        bnd = sorted([g for g, r in roles.items() if r[0] == 'b'], key=lambda g: roles[g][1])
        prev = [R[i0 + a][b] for a, b in bnd]
        for sec in secs:
            cur = [leg_pos(sec, roles[g]) for g in bnd]
            for k in range(len(bnd)):
                out.append([prev[k], prev[(k + 1) % len(bnd)], cur[(k + 1) % len(bnd)], cur[k]])
            prev = cur
        out.append(prev)
    j = ear_face(R); i = IDX[EAR_SPAN]
    prev = [R[i][j], R[i][j + 1], R[i + 1][j + 1], R[i + 1][j]]
    for sec in EAR:
        cur = [role_pos(sec, u, s, 1.0) for u, s in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
        for k in range(4):
            out.append([prev[k], prev[(k + 1) % 4], cur[(k + 1) % 4], cur[k]])
        prev = cur
    out.append(prev)
    return out


def grow(bm, faces, roles, secs, pos):
    for sec in secs:
        old = [(o.co.copy(), rl) for o, rl in roles.items()]      # interior verts go with the extruded faces
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(old, key=lambda o: (o[0] - v.co).length)[1]
        for v, rl in new.items():
            v.co = Vector(pos(sec, rl))
        faces, roles = r['faces'], new
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(root, secs):
        (nm, nsp), (j0, j1) = root, LEG_J
        i0 = IDX[nm]
        roles = {rings[i0 + a][b]: r for (a, b), r in leg_grid(nsp, j0, j1).items()}
        faces = [spans[i0 + a][j] for a in range(nsp) for j in range(j0, j1 + 1)]
        grow(bm, faces, roles, secs, leg_pos)

    limb(FORE_ROOT, FORE)
    limb(HIND_ROOT, HIND)
    i = IDX[EAR_SPAN]
    j = ear_face([sec_pts(c, a, T, B, W, p) for (nm, c, a, T, B, W, p) in SECS])
    rr, rf = rings[i], rings[i + 1]
    grow(bm, [spans[i][j]], {rf[j]: (-1, -1), rf[j + 1]: (1, -1), rr[j]: (-1, 1), rr[j + 1]: (1, 1)}, EAR,
         lambda sec, r: role_pos(sec, r[0], r[1], 1.0))
    snap_seam(bm)
    return object_from_bm('body', bm)


def P(nm):
    return [Vector(q) for q in ring_pts(nm)]


def eye_face_centre():
    A, B_ = P('H1'), P('H2')
    return (A[EYE_J] + A[EYE_J + 1] + B_[EYE_J] + B_[EYE_J + 1]) / 4


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.04 and abs(c.y - ec0.y) < 0.04 and abs(c.z - ec0.z) < 0.05


def stage2(k, body):
    """Joint rings (elbow, knee, neck-skull, wrist, hock, belly, chest, lower neck), the eye socket, brow, muzzle
    planes, nose pad - on the poly-pass-3 topology."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ec0 = eye_face_centre()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    lp = lambda sec: leg_pos(sec, ('b', math.radians(45)))
    cuts = [('elbow ring: the elbow bend', mid(lp(FORE[0]), lp(FORE[1]))),
            ('knee ring: the stifle bend', mid(lp(HIND[0]), lp(HIND[1]))),
            ('neck-skull ring: the head nod', mid(P('N1')[0], P('H0')[0])),
            ('wrist ring: the wrist bend', mid(lp(FORE[3]), lp(FORE[4]))),
            ('hock ring: the hock bend', mid(lp(HIND[3]), lp(HIND[4]))),
            ('belly ring: the back bend', mid(P('W0')[0], P('M0')[0])),
            ('chest ring: the spine bend behind the shoulder', mid(P('M1')[0], P('M1a')[0])),
            ('lower neck ring: the neck bend', mid(P('C2')[0], P('N0')[0]))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_), t=0.5)
    H1, H2, H2a, H3, H4 = P('H1'), P('H2'), P('H2a'), P('H3'), P('H4')
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the brow face, its floor pushed in'):
        inner = inset(bm, [f], 0.3, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.012)
    move([vert_near(bm, H1[EYE_J])], (0.008, -0.01, 0.006))                     # brow corner forward / out
    flatten([vert_near(bm, q[j]) for q in (H2a, H3, H4) for j in (4, 5, 6)])     # flat muzzle side
    flatten([vert_near(bm, q[j]) for q in (H2, H2a, H3, H4) for j in (0, 1)])    # flat bridge
    move([vert_near(bm, H4[j]) for j in (0, 1, 2)], (0.0, -0.012, 0.0))         # nose pad overhang
    move([vert_near(bm, H4[j]) for j in (7, 8, 9)], (0.0, 0.02, 0.0))           # slanted nose pad
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


PAL = {'fur': '#9c6842', 'dark': '#5e3b27', 'muzzle': '#d2ab80', 'nose': '#181313', 'claw': '#e8d5b3',
       'iris': '#5a3418'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.905 and z > 0.80 and n.y < -0.3:
        return 'nose'
    if y < -0.9 and z > 0.845:
        return 'nose'
    if y < -0.805:
        return 'muzzle'
    if z > 1.155 and -0.70 < y < -0.57 and x > 0.1:
        return 'dark'                       # ears
    if z < 0.50:
        return 'dark'                       # legs and belly, dark brown as in the ref
    return 'fur'


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


def claw(bm, h, d, lead, w=1.4, L=1.3):
    """A blunt cream claw rooted in the paw front at h, curving down to the ground."""
    x0 = h.x
    yr, ym, yt = h.y + 0.012, h.y - (0.012 + lead * 0.5) * L, h.y - (0.030 + lead) * L
    xm, xt = x0 + d * 0.15, x0 + d * 0.3
    a, b, c_, e = 0.012 * w, 0.009 * w, 0.008 * w, 0.004 * w
    rows = [[(x0 - a, yr, 0.008), (x0 + a, yr, 0.008), (x0 + a, yr, 0.038), (x0 - a, yr, 0.038)],
            [(xm - b, ym, 0.006), (xm + b, ym, 0.006), (xm + c_, ym, 0.028), (xm - c_, ym, 0.028)],
            [(xt - e, yt, 0.002), (xt + e, yt, 0.002), (xt + e, yt, 0.010), (xt - e, yt, 0.010)]]
    R = [[bm.verts.new(p) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in ((R[0], R[1]), (R[1], R[2])):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[2])


def clump(bm, a, n, lay, s, L):
    """A chunky fur clump: a square base sunk in the body, a thick mid section standing off the surface
    (sideways 0.8 s, 0.9 s deep), and a blunt narrow tip laid back along `lay` - a bold wedge, not a shard."""
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
    if lo < 0.003:                                  # never across the mirror plane
        for v in shell:
            v.co.x += 0.003 - lo
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip[(j + 1) % 4], tip[j]])
    bm.faces.new(tip)


def surf(a, b, t, jf):
    """A point on the coarse loft between sections a and b (t from a to b) at fractional ring index jf, and its
    outward normal (radial from the interpolated section centre)."""
    A, Bq = P(a), P(b)
    j0 = min(int(jf), NV - 2); f = jf - j0
    pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
    p = pa.lerp(pb, t)
    ca = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == a][0]))
    cb = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == b][0]))
    c = ca.lerp(cb, t)
    return p, (p - c).normalized()


def clumps(spec, tree):
    """spec: [(a, b, t, jf, lay, s, L)] -> one mirrored piece of fur clumps, each rooted on the nearest point
    of the subdivided, fitted body (the coarse loft only says where)."""
    bm = bmesh.new()
    for a, b, t, jf, lay, s_, L_ in spec:
        p, n_ = surf(a, b, t, jf)
        loc, fn, _i, _d = tree.find_nearest(p)
        n2 = (fn + n_).normalized()
        clump(bm, loc, n2, Vector(lay), s_, L_)
    return bm


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('fur', 'dark', 'muzzle', 'nose')}, body_rule)
    # night 10-23 border pass (owner 10-21 approved kit/smooth_borders, as frog r17): anti-stair cuts + tangential relax
    smooth_borders(body, k=k, iters=8)
    tree = body_bvh(body)
    ec = eye_face_centre()
    c, n, _i, _d = tree.find_nearest(ec - Vector((0.012, 0, 0)))
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.016, 0.009)
    eye = object_from_bm('eye', bm)
    paint(eye, {'iris': PAL['iris'], 'nose': PAL['nose']},
          lambda c_, n_, i: 'nose' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.007 and n_.dot(n) > 0.5 else 'iris')
    bm = bmesh.new()
    for sole in (FORE[4], HIND[4]):
        (cx, cy, _), rx, ry = sole
        for d in (-0.075, -0.025, 0.025, 0.075):
            o = Vector((cx + d, cy - ry - 0.2, 0.02))
            hit = tree.ray_cast(o, Vector((0, 1, 0)), 0.4)[0]
            h = hit if hit is not None else Vector((cx + d, cy - ry, 0.02))
            claw(bm, h, d, 0.006 if abs(d) < 0.05 else 0.0)
    claws = object_from_bm('claws', bm)
    paint(claws, {'claw': PAL['claw']}, lambda c_, n_, i: 'claw')
    # fur: a cheek ruff under each ear and a shoulder hump, broad blunt clumps laid back
    back = (0, 0.85, -0.5)
    fur = [('H0', 'H0b', 0.5, 4.7, (0.1, 0.8, -0.6), 0.04, 0.075), ('N1', 'H0', 0.5, 5.4, (0.1, 0.8, -0.6), 0.045, 0.08),
           ('N1', 'H0', 0.4, 6.7, (0.05, 0.6, -0.8), 0.04, 0.075)]
    furo = object_from_bm('fur', clumps(fur, tree))
    paint(furo, {'fur': PAL['fur']}, lambda c_, n_, i: 'fur')
    return [eye, claws, furo]


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
         ('foot.L', J['hock'], J['htoe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'head': (0, 0, 3)},
                       20: {'ear.L': (0, 0, -10)}, 24: {'head': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.2, 0, 0), 'neck': (-1.5, 0, 0), 'head': (0, 0, -3)}, 48: {}})
    A = 14
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'head': (0, 0, 3)},
        9: {'forearm.R': (-30, 0, 0), 'paw.R': (-20, 0, 0), 'shin.L': (-15, 0, 0), 'foot.L': (20, 0, 0)},
        17: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'head': (0, 0, -3)},
        25: {'forearm.L': (-30, 0, 0), 'paw.L': (-20, 0, 0), 'shin.R': (-15, 0, 0), 'foot.R': (20, 0, 0)},
        33: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'head': (0, 0, 3)}})
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (-8, 0, 0), 'neck': (-8, 0, 0), 'head': (-6, 0, 0), 'upperarm.L': (-25, 0, 0), 'forearm.L': (-30, 0, 0)},
        18: {'chest': (6, 0, 0), 'neck': (12, 0, 0), 'head': (10, 0, 0), 'upperarm.L': (30, 0, 0), 'forearm.L': (-10, 0, 0)},
        24: {'chest': (3, 0, 0), 'neck': (8, 0, 0), 'head': (5, 0, 0), 'upperarm.L': (10, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 10: {'hips': (0, 0.03, 0)}, 18: {'hips': (0, -0.05, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
