import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# Nile crocodile, t7 hand box-model: one spine loft of 6-vertex half rings (tail tip -> snout) is the whole long
# body; the sprawled legs are 2-face regions of the lower flank extruded OUT, then down (the section turns from a
# vertical to a horizontal hexagon); the eye turrets are 1-face extrusions from the skull top. Stage 2 joint
# rings, eye socket, flat skull and muzzle planes; stage 3 lens eyes, scutes, teeth, claws; stage 4 rig and clips.
META = dict(creature='crocodile', model='opus', stage1_tris=(1200, 3200), total_tris=(3000, 5500),
            closeups=[('head', (0.0, -1.12, 0.26), 0.30, 'hero'),
                      ('front foot', (0.44, -0.58, 0.04), 0.12, 'hero'),
                      ('hind foot', (0.45, 0.15, 0.04), 0.12, 'hero'),
                      ('back scutes', (0.0, -0.15, 0.36), 0.35, 'hero')])

# the skeleton (x >= 0 half; .L on +X), read off reference/side.png + top.png
J = dict(
    hips=(0.0, 0.20, 0.20), spine=(0.0, -0.12, 0.22), chest=(0.0, -0.50, 0.22),
    neck=(0.0, -0.72, 0.23), head=(0.0, -0.86, 0.24), nose=(0.0, -1.43, 0.235),
    tail0=(0.0, 0.36, 0.17), tail1=(0.0, 0.62, 0.15), tail2=(0.0, 0.90, 0.13), tail3=(0.0, 1.12, 0.115),
    tail4=(0.0, 1.34, 0.10),
    shoulder=(0.17, -0.44, 0.17), elbow=(0.37, -0.50, 0.12), wrist=(0.43, -0.56, 0.032),
    fpaw=(0.44, -0.59, 0.015), ftoe=(0.45, -0.70, 0.01),
    hipL=(0.17, 0.12, 0.17), knee=(0.38, 0.15, 0.12), hock=(0.44, 0.18, 0.032),
    hpaw=(0.45, 0.15, 0.015), htoe=(0.455, 0.04, 0.01),
)

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
# poly pass 3: 11-vertex half rings (was 6), re-fit to the sheet's front mound (body) and the cartoon head
# pass 9: 11-vertex half rings with every extra vertex ON the before3 hexagon planes (co-planar faces, crisp ridges)
BODY = [(0, 1), (0.33, 0.95), (0.66, 0.9), (0.83, 0.425), (1, -0.05), (0.95, -0.3), (0.9, -0.55), (0.725, -0.725), (0.55, -0.9), (0.275, -0.95), (0, -1)]
TAIL = [(0, 1), (0.275, 0.925), (0.55, 0.85), (0.775, 0.5), (1, 0.15), (0.96, -0.15), (0.92, -0.45), (0.71, -0.675), (0.5, -0.9), (0.25, -0.95), (0, -1)]
HEAD = [(0, 1), (0.31, 0.985), (0.62, 0.97), (0.81, 0.635), (1, 0.3), (0.975, -0.025), (0.95, -0.35), (0.775, -0.615), (0.6, -0.88), (0.3, -0.94), (0, -1)]
MUZ = [(0, 1), (0.34, 0.975), (0.68, 0.95), (0.84, 0.625), (1, 0.3), (0.975, -0.025), (0.95, -0.35), (0.775, -0.615), (0.6, -0.88), (0.3, -0.94), (0, -1)]
JAW = 6                     # the upper-jaw ridge vertex of HEAD / MUZ
ROOT = (4, 5, 6, 7, 8)      # the lower-flank vertices a leg root spans (4 faces: a 10-gon limb)
EYEF = 2                    # the skull-top face (v2-v3) the eye turret grows from


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


def v(nm, y, top, bot, W, prof):
    return tb(nm, (y, top), (y, bot), W, prof)


# the spine loft, tail tip -> snout tip (top / bottom z from the side view, W = half width from the top view)
SECS = [   # poly pass 3: 35 stations (was 19), added where the silhouette curves; re-fit to the side / top traces
    v('T0', 1.33, 0.112, 0.086, 0.016, TAIL),
    v('T0a', 1.295, 0.122, 0.083, 0.020, TAIL),
    v('T0b', 1.25, 0.134, 0.080, 0.025, TAIL),
    v('T0c', 1.20, 0.146, 0.077, 0.029, TAIL),
    v('T1', 1.15, 0.158, 0.073, 0.033, TAIL),
    v('T1b', 1.05, 0.182, 0.067, 0.040, TAIL),
    v('T2', 0.95, 0.205, 0.061, 0.048, TAIL),
    v('T2b', 0.85, 0.220, 0.057, 0.055, TAIL),
    v('T3', 0.75, 0.232, 0.053, 0.063, TAIL),
    v('T3b', 0.65, 0.242, 0.049, 0.073, TAIL),
    v('T4', 0.55, 0.252, 0.046, 0.086, TAIL),
    v('R0', 0.40, 0.278, 0.044, 0.118, BODY),
    v('R0b', 0.31, 0.300, 0.044, 0.165, BODY),
    v('R1', 0.22, 0.325, 0.044, 0.21, BODY),
    v('R2', 0.02, 0.382, 0.040, 0.26, BODY),
    v('R2b', -0.04, 0.397, 0.038, 0.27, BODY),
    v('W0', -0.10, 0.408, 0.036, 0.275, BODY),
    v('W1', -0.185, 0.418, 0.035, 0.28, BODY),
    v('M0', -0.27, 0.420, 0.038, 0.275, BODY),
    v('C0', -0.34, 0.410, 0.048, 0.255, BODY),
    v('C1', -0.55, 0.388, 0.075, 0.18, BODY),
    v('C2', -0.65, 0.372, 0.088, 0.148, BODY),
    v('C2b', -0.70, 0.365, 0.094, 0.138, BODY),
    v('N0', -0.75, 0.358, 0.100, 0.128, BODY),
    v('H0', -0.86, 0.352, 0.120, 0.13, HEAD),
    v('H1', -0.99, 0.342, 0.150, 0.098, HEAD),
    v('H1b', -1.045, 0.330, 0.162, 0.084, HEAD),
    v('H2', -1.103, 0.314, 0.170, 0.070, MUZ),
    v('H2c', -1.14, 0.306, 0.174, 0.065, MUZ),
    v('H2b', -1.18, 0.298, 0.178, 0.060, MUZ),
    v('H3', -1.253, 0.284, 0.186, 0.053, MUZ),
    v('H3b', -1.31, 0.290, 0.190, 0.050, MUZ),
    v('H4', -1.365, 0.284, 0.194, 0.046, MUZ),
    v('H4b', -1.40, 0.276, 0.201, 0.040, MUZ),
    v('H5', -1.434, 0.262, 0.208, 0.032, MUZ),
]

# limb sections: (centre xyz, ru, rs, theta) — a hexagon whose u axis is (sin theta, 0, cos theta): theta 0 = the
# vertical section of a limb running OUT from the flank, theta 90 = the horizontal section of a limb hanging down
# poly pass 3: 12 sections a leg (was 6), 10-gon rings; a shoulder / thigh bulge off the flank, a taper to the wrist
FORE = [((0.285, -0.455, 0.155), 0.082, 0.086, 0), ((0.308, -0.468, 0.148), 0.076, 0.082, 5),
        ((0.33, -0.48, 0.14), 0.07, 0.078, 12), ((0.352, -0.49, 0.131), 0.066, 0.074, 20),
        ((0.37, -0.50, 0.12), 0.063, 0.071, 30), ((0.40, -0.52, 0.095), 0.057, 0.064, 52),
        ((0.418, -0.535, 0.068), 0.052, 0.06, 72), ((0.426, -0.548, 0.05), 0.05, 0.06, 82),
        ((0.43, -0.56, 0.035), 0.05, 0.062, 90), ((0.437, -0.585, 0.02), 0.055, 0.078, 90),
        ((0.44, -0.60, 0.01), 0.061, 0.091, 90), ((0.445, -0.61, 0.0), 0.064, 0.098, 90)]
HIND = [((0.285, 0.125, 0.16), 0.094, 0.1, 0), ((0.31, 0.13, 0.151), 0.088, 0.094, 5),
        ((0.335, 0.135, 0.14), 0.081, 0.088, 12), ((0.358, 0.142, 0.131), 0.076, 0.083, 20),
        ((0.38, 0.15, 0.12), 0.071, 0.078, 30), ((0.41, 0.16, 0.095), 0.063, 0.07, 52),
        ((0.428, 0.17, 0.068), 0.057, 0.066, 72), ((0.435, 0.175, 0.05), 0.055, 0.065, 82),
        ((0.44, 0.18, 0.035), 0.053, 0.064, 90), ((0.447, 0.165, 0.02), 0.06, 0.082, 90),
        ((0.45, 0.15, 0.01), 0.066, 0.1, 90), ((0.455, 0.14, 0.0), 0.07, 0.108, 90)]
ELB = 4                     # the elbow / knee section: the s2 joint ring goes between it and the next
# fix2: legs 1.25x thicker and moved out with the wider trunk (both reviews: legs tiny; sheet: chunky splayed limbs)
# eye turret over the skull top (role u across x, s along y; dz tilts the top inward)
EYE = [((0.088, -0.925, 0.368), 0.026, 0.032, 0.0), ((0.085, -0.93, 0.384), 0.017, 0.022, 0.004)]


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def role_pos(sec, u, s, corner=0.55):
    c, ru, rs = sec[0], sec[1], sec[2]
    th = math.radians(sec[3]) if len(sec) > 3 else math.pi / 2
    k = 1.0 if u == 0 else max(corner, math.sqrt(max(0.0, 1 - u * u)))   # pass 3: 10-gon (u = +-1, +-0.5, 0)
    return (c[0] + u * ru * math.sin(th), c[1] + s * rs * k, c[2] + u * ru * math.cos(th))


def eye_pos(sec, u, s):
    c, rx, ry, dz = sec
    return (c[0] + u * rx, c[1] + s * ry, c[2] - u * dz)


def grow(bm, faces, roles, secs, pos):
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for vv in r['verts']:
            ov = min(roles, key=lambda o: (o.co - vv.co).length)
            new[vv] = roles[ov]
        for vv, (u, s) in new.items():
            vv.co = Vector(pos(sec, u, s))
        faces, roles = r['faces'], new
    return faces, roles


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def capq(bm, r):
    """An end cap as a ladder of quads between the upper and lower halves of the half ring, a triangle at the side."""
    n = len(r)
    j = 0
    while j + 1 < n - 2 - j:
        bm.faces.new([r[j], r[j + 1], r[n - 2 - j], r[n - 1 - j]])
        j += 1
    if j + 1 == n - 2 - j:
        bm.faces.new([r[j], r[j + 1], r[j + 2]])


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    capq(bm, rings[0]); capq(bm, rings[-1])               # pass 3: ladder caps (an 11-gon fan is all needles)
    recalc_normals(bm)

    def limb(span_name, secs):
        i = idx[span_name]
        rr, rf = rings[i], rings[i + 1]
        us = [1 - 2 * j / (len(ROOT) - 1) for j in range(len(ROOT))]
        roles = {**{rf[j]: (u, -1) for j, u in zip(ROOT, us)}, **{rr[j]: (u, 1) for j, u in zip(ROOT, us)}}
        grow(bm, [spans[i][j] for j in ROOT[:-1]], roles, secs, role_pos)

    limb('C0', FORE)
    limb('R1', HIND)
    i = idx['H0']
    rr, rf = rings[i], rings[i + 1]
    e = EYEF
    grow(bm, [spans[i][e]], {rf[e]: (-1, -1), rf[e + 1]: (1, -1), rr[e]: (-1, 1), rr[e + 1]: (1, 1)}, EYE, eye_pos)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_centre():
    """The turret's outer wall, upper part: where the lens sits."""
    c, rx, ry, dz = EYE[1]
    c0 = EYE[0][0]
    return Vector(((c[0] + rx + c0[0] + EYE[0][1]) / 2, (c[1] + c0[1]) / 2, (c[2] + c0[2]) / 2 - 0.002))


def stage2(k, body):
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    with topo(bm, k.log, 'loop', 'elbow ring: the bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(FORE[ELB], 1, 1), role_pos(FORE[ELB + 1], 1, 1))), t=0.5)
    with topo(bm, k.log, 'loop', 'knee ring: the bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(HIND[ELB], 1, 1), role_pos(HIND[ELB + 1], 1, 1))), t=0.5)
    with topo(bm, k.log, 'loop', 'neck-skull ring: the head turn'):
        loopcut(bm, edge_near(bm, mid(P('N0')[0], P('H0')[0])), t=0.5)
    with topo(bm, k.log, 'loop', 'tail-root ring: the tail swing'):
        loopcut(bm, edge_near(bm, mid(P('T4')[0], P('R0')[0])), t=0.5)
    # pass 3: the s2 r3 tail sliver rings are now base stations (T0b, T1b)
    # eye socket: the turret's outer wall inset and pushed in, the lens sits in it
    f = face_near(bm, eye_centre())
    fn = f.normal.copy()
    with topo(bm, k.log, 'inset', 'eye socket'):
        inner = inset(bm, [f], 0.3, 0.0)
    move(list(inner[0].verts), -fn * 0.005)
    # flat skull and muzzle planes, the upper-jaw edge as a crisp ridge, a raised nostril pad at the snout end
    H2, H2c, H3, H4, H5 = P('H2'), P('H2c'), P('H3'), P('H4'), P('H5')
    flatten([vert_near(bm, q[j]) for q in (H2, H2c, H3, H4) for j in (0, 1, 2)])
    move([vert_near(bm, q[JAW]) for q in (H2, H2c, H3, H4)], (-0.006, 0.0, 0.0))
    move([vert_near(bm, q[j]) for q in (H2, H2c, H3, H4) for j in (JAW - 1, JAW + 1)], (-0.003, 0.0, 0.0))   # pass 9: the plane midpoints follow (flat jaw planes, no cream slits)
    move([vert_near(bm, H4[0]), vert_near(bm, H4[1]), vert_near(bm, H4[2])], (0.0, 0.0, 0.012))
    move([vert_near(bm, H5[9]), vert_near(bm, H5[10])], (0.0, 0.012, 0.0))
    # s2 r2: the tail tip ring is too small for its 18 cm span (needle triangles): blunt it, 1.7x about its centre
    T0 = P('T0'); tc = sum(T0, Vector()) / len(T0)
    scale([vert_near(bm, q) for q in T0], 1.7, pivot=(0.0, tc.y, tc.z))
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'olive': '#666d42', 'scute': '#545a36', 'cream': '#d8d09a', 'amber': '#e0a030', 'pupil': '#1a1615',
       'claw': '#4a4452', 'tooth': '#f2eedc'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if x > 0.29 and z < 0.2:                             # s3 r4: was 0.215; fix2: 0.29 for the wider trunk
        return 'olive'                                   # sprawled legs and feet
    if y < -0.70 and n.z < -0.2:
        return 'cream'                                   # lower jaw and throat, border on the v3 (jaw) loop
    if -0.75 < y < 1.0 and z < 0.14 and n.z < -0.02:   # pass 9: only the down-facing lower-flank plane (no patches)
        return 'cream'                                   # s3 r3: the ref's cream lower-flank band, border on the v3 loop
    if n.z < -0.25:
        return 'cream'                                   # belly and the lower flank / tail underside
    return 'olive'


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


def block(bm, a, n, fwd, sx, sy, h, top=0.6, sink=0.012):
    """A scute: a flat-topped frustum, base sx x sy sunk into the body along -n, top `top` of the base at h."""
    n, fwd = Vector(n).normalized(), Vector(fwd)
    fwd = (fwd - n * fwd.dot(n)).normalized()
    u = fwd.cross(n).normalized()
    b, t = a - n * sink, a + n * h
    base = [bm.verts.new(b + u * su * sx + fwd * sf * sy) for su, sf in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    tp = [bm.verts.new(t + u * su * sx * top + fwd * sf * sy * top) for su, sf in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lo = min(q.co.x for q in base + tp)
    if lo < 0.003:
        for q in base + tp:
            q.co.x += 0.003 - lo
    bm.faces.new(base)
    for j in range(4):
        bm.faces.new([base[(j + 1) % 4], base[j], tp[j], tp[(j + 1) % 4]])
    bm.faces.new(list(reversed(tp)))


def surf(a, b, t, jf):
    A, Bq = P(a), P(b)
    j0 = min(int(jf), len(A) - 2); f = jf - j0
    pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
    return pa.lerp(pb, t)


def sec_at(y):
    """Bracketing sections and t for a y along the loft."""
    ys = [(n, c[0]) for (n, c, *_r) in SECS]
    for (na, ya), (nb, yb) in zip(ys, ys[1:]):
        if yb <= y <= ya:
            return na, nb, (ya - y) / (ya - yb)
    return None


def claw(bm, h, d, out):
    """A claw from the foot front h: a root 2 cm wide, a mid ring, a blunt tip 3 cm out along `out` dropping to the ground."""
    o = Vector(out).normalized()
    side = Vector((-o.y, o.x, 0.0))
    rows = []
    for dist, w, z0, z1 in ((-0.012, 0.010, 0.011, 0.026), (0.014, 0.007, 0.007, 0.018), (0.032, 0.003, 0.003, 0.008)):  # s3 r2: root lifted off the sole plane (z-fight)
        p = h + o * dist
        rows.append([(p + side * sw * w + Vector((0, 0, zz))) for sw, zz in ((-1, z0), (1, z0), (1, z1), (-1, z1))])
    R = [[bm.verts.new(p) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in ((R[0], R[1]), (R[1], R[2])):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[2])


def tooth(bm, p, l):
    """A chunky white peg hanging from the upper-jaw edge (detail pass 2026-10-23: a blunt 4-sided frustum
    >= 6.5 mm thick to its tip, gate floor 5.6 mm; it was a 4 mm-thin wedge, t 1.5 mm, L/t 11.7)."""
    top = [p + Vector((sx * 0.0055, sy * 0.008, 0.005)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bot = [p + Vector((0.0015 + sx * 0.0036, sy * 0.0042, -l)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    A = [bm.verts.new(q) for q in top]
    B = [bm.verts.new(q) for q in bot]
    bm.faces.new(A); bm.faces.new(list(reversed(B)))
    for j in range(4):
        bm.faces.new([A[j], B[j], B[(j + 1) % 4], A[(j + 1) % 4]])


def stage3(k, body):
    paint(body, PAL, body_rule)
    bm0 = edit(body); tree = BVHTree.FromBMesh(bm0); bm0.free()
    # eye: a small amber lens with a dark pupil in the turret's socket, facing out and up
    c, n, _i, _d = tree.find_nearest(eye_centre() - Vector((0.004, 0, 0)))
    n = n if n.x > 0 else -n
    n = (n + Vector((0, -0.3, 0.25))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.003, n, 0.014, 0.008)        # s3 r2: proud of the socket floor (z-fight)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.006 and n_.dot(n) > 0.5 else 'amber')
    # scutes: three rows a side on the trunk and neck, a paired crest on the tail
    bm = bmesh.new()
    y = -0.70
    while y < 0.37:
        a, b, t = sec_at(y)
        for jf, sx in ((0.5, 0.034), (1.5, 0.032)):        # pass 3: same x on the 11-vertex ring          # fix pass: 2 rows of large flat wedges (was a 3-row bump grid)
            p = surf(a, b, t, jf)
            loc, fn, _i, _d = tree.find_nearest(p)
            block(bm, loc, fn, (0, -1, 0), sx, 0.058, 0.048, top=0.55)   # fix2: 1.6x taller
        y += 0.15
    y = 0.44
    while y < 1.29:
        a, b, t = sec_at(y)
        p = surf(a, b, t, 0.7)
        loc, fn, _i, _d = tree.find_nearest(p)
        f = 1.0 - (y - 0.44) / 1.1
        block(bm, loc, (fn + Vector((0, 0, 1.5))).normalized(), (0, -1, 0), 0.015, 0.048, 0.03 + 0.05 * f, top=0.4)  # fix2: bigger crest
        y += 0.12
    scutes = object_from_bm('scutes', bm)
    paint(scutes, {'scute': PAL['scute']}, lambda c_, n_, i: 'scute')
    # teeth: five small white wedges a side under the upper-jaw edge (the v3 loop of the muzzle)
    bm = bmesh.new()
    for yy in (-1.38, -1.30, -1.21, -1.12, -1.03):
        a, b, t = sec_at(yy)
        p = surf(a, b, t, float(JAW))
        loc, fn, _i, _d = tree.find_nearest(p)
        tooth(bm, loc + Vector((-0.004, 0, 0)), 0.018 if yy in (-1.30, -1.12) else 0.013)
    teeth = object_from_bm('teeth', bm)
    paint(teeth, {'tooth': PAL['tooth']}, lambda c_, n_, i: 'tooth')
    # claws: four per foot along the foot front, spread like a fan
    bm = bmesh.new()
    for sole in (FORE[5], HIND[5]):
        (cx, cy, _), ru, rs = sole[0], sole[1], sole[2]
        for d, ang in ((-0.042, -20), (-0.014, -5), (0.014, 10), (0.042, 25)):
            o = Vector((cx + d, cy - rs - 0.15, 0.012))
            hit = tree.ray_cast(o, Vector((0, 1, 0)), 0.3)[0]
            h = hit if hit is not None else Vector((cx + d, cy - rs * 0.8, 0.0))
            h = Vector((h.x, h.y, 0.0))
            a_ = math.radians(ang)
            claw(bm, h, d, (math.sin(a_), -math.cos(a_), 0.0))
    claws = object_from_bm('claws', bm)
    paint(claws, {'claw': PAL['claw']}, lambda c_, n_, i: 'claw')
    return [eye, scutes, teeth, claws]


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('tail3', J['tail3'], J['tail4'], 'tail2', True),
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
    # idle: slow breathing, a lazy tail sway, the head lifting a touch
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.0, 0, 0), 'tail1': (0, 0, 4), 'tail2': (0, 0, 5)},
                       24: {'head': (-3, 0, 0)}, 36: {'chest': (1.0, 0, 0), 'tail1': (0, 0, -4), 'tail2': (0, 0, -5)},
                       48: {}})
    # move: high walk, diagonal pairs swing (about the upper bone's local X), the trunk and tail S-bend with them
    A, S = 22, 6
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0),
            'spine': (0, 0, S), 'tail0': (0, 0, -S), 'tail1': (0, 0, -S), 'tail2': (0, 0, S)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0),
             'spine': (0, 0, -S), 'tail0': (0, 0, S), 'tail1': (0, 0, S), 'tail2': (0, 0, -S)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0),
             'spine': (0, 0, S), 'tail0': (0, 0, -S), 'tail1': (0, 0, -S), 'tail2': (0, 0, S)}})
    # attack: head drops and pulls back, then a sideways snap forward with the head tipped up (jaws are one piece)
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (6, 0, 0), 'head': (4, 0, 0), 'tail0': (0, 0, 8)},
        14: {'neck': (-8, 0, 12), 'head': (-14, 0, 6), 'tail0': (0, 0, -10), 'tail1': (0, 0, -8)},
        18: {'neck': (-6, 0, 10), 'head': (-10, 0, 4), 'tail0': (0, 0, -10), 'tail1': (0, 0, -8)},
        26: {'neck': (2, 0, 2), 'head': (2, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, 0)}, 14: {'hips': (0, 0.08, 0)}, 18: {'hips': (0, 0.08, 0)},
             26: {'hips': (0, 0.02, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
