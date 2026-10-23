import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
from smooth_borders import smooth_borders
import parts as PT

# rhinoceros beetle (t7 hand box model, zoo workflow v2). One spine loft of 16-vertex half rings runs the elytra tip ->
# the domed wing case -> the pronotum shield -> the head -> and on up the big curved head horn (the horn IS the loft's
# front end, so the identity cue is in the locked base). Each half ring is a shell section: a dome down to the widest
# line, the wing-case rim, a small tuck under the rim and a boxy under-curve to the belly. The six legs grow from
# 4 x 3-face windows on that under-curve (14-sided legs) through a transition ring set 45 % of the way from the window
# rim to the coxa section (the rhino leg-root trick: two soft folds instead of one knife fold); the leg sections are
# carried along the leg path in a parallel-transported frame.
META = dict(creature='beetle', model='opus', stage1_tris=(2500, 6500), total_tris=(3000, 8000),
            closeups=[('head and horn', (0.0, -0.36, 0.40), 0.24, 'hero'),
                      ('front leg root', (0.17, -0.14, 0.19), 0.12, 'hero_low'),
                      ('mid leg root', (0.19, 0.05, 0.17), 0.12, 'az090'),
                      ('hind leg', (0.24, 0.24, 0.12), 0.16, 'back34')])

# the skeleton the model is built on (x >= 0 half; .L on +X), read off reference/side.png + front.png
J = dict(
    abd=(0.0, 0.40, 0.29), thx=(0.0, 0.0, 0.31), neck=(0.0, -0.205, 0.31), head=(0.0, -0.30, 0.30),
    horn=(0.0, -0.43, 0.52),
)

NV = 16


def shell(zt, zw, W, zr, zb, n=2.2, m=2.6, tuck=0.9, rim=0.985):
    """A shell half ring (x, z), top seam -> bottom seam, 16 vertices: j0-j7 a superellipse dome (exponent n) from the
    top seam zt down to the widest line (W at zw); j8 the rim (W x rim at zr); j9-j15 the under-curve (exponent m)
    from the tuck (W x tuck, zr - 0.012) to the bottom seam zb."""
    out = []
    for j in range(8):
        t = (math.pi / 2) * j / 7
        out.append((W * math.sin(t) ** (2 / n), zw + (zt - zw) * math.cos(t) ** (2 / n)))
    out[0] = (0.0, zt)
    out.append((W * rim, zr))
    a, z0 = W * tuck, zr - 0.012
    b = z0 - zb
    for i in range(7):
        p = (math.pi / 2) * i / 6
        out.append((a * math.cos(p) ** (2 / m), z0 - b * math.sin(p) ** (2 / m)))
    out[-1] = (0.0, zb)
    return out


def prof(nt, nb, taper=1.0, nv=NV):
    """A superellipse half ring (fx, fh), top seam -> bottom seam (the horn rings)."""
    out = []
    for j in range(nv):
        t = math.pi * j / (nv - 1)
        c, s = math.cos(t), math.sin(t)
        e = nt if c >= 0 else nb
        fx = abs(s) ** (2 / e) if j not in (0, nv - 1) else 0.0
        fh = math.copysign(abs(c) ** (2 / e), c)
        if c < 0:
            fx *= 1 - (1 - taper) * abs(c)
        out.append((fx, fh))
    return out


HORN = prof(2.3, 2.3, 0.9)

# body stations rear -> front: (name, y, zt top, zw widest line, W half width, zr rim, zb bottom, tuck)
BODY = [
    ('E0', 0.472, 0.262, 0.236, 0.040, 0.212, 0.196, 0.9),   # elytra tip
    ('E1', 0.460, 0.295, 0.240, 0.068, 0.210, 0.186, 0.9),
    ('E2', 0.445, 0.325, 0.243, 0.098, 0.209, 0.178, 0.9),
    ('E3', 0.425, 0.355, 0.247, 0.128, 0.208, 0.170, 0.9),
    ('E4', 0.400, 0.380, 0.252, 0.155, 0.207, 0.163, 0.9),
    ('E5', 0.370, 0.402, 0.256, 0.177, 0.206, 0.156, 0.9),
    ('E6', 0.340, 0.420, 0.259, 0.193, 0.205, 0.150, 0.9),
    ('E7', 0.310, 0.435, 0.261, 0.203, 0.204, 0.146, 0.9),
    ('E8', 0.280, 0.447, 0.262, 0.208, 0.204, 0.143, 0.9),
    ('B0', 0.250, 0.458, 0.263, 0.213, 0.203, 0.141, 0.9),   # hind-leg window B0..B4
    ('B1', 0.225, 0.466, 0.263, 0.216, 0.203, 0.140, 0.9),
    ('B2', 0.200, 0.472, 0.263, 0.218, 0.203, 0.140, 0.9),
    ('B3', 0.175, 0.477, 0.263, 0.219, 0.203, 0.140, 0.9),
    ('B4', 0.150, 0.480, 0.263, 0.219, 0.203, 0.140, 0.9),
    ('M5', 0.128, 0.481, 0.263, 0.218, 0.204, 0.141, 0.9),
    ('M0', 0.105, 0.481, 0.263, 0.216, 0.205, 0.142, 0.9),   # mid-leg window M0..M4
    ('M1', 0.080, 0.480, 0.264, 0.213, 0.206, 0.143, 0.9),
    ('M2', 0.055, 0.477, 0.266, 0.208, 0.208, 0.145, 0.9),
    ('M3', 0.030, 0.472, 0.268, 0.200, 0.210, 0.147, 0.9),
    ('M4', 0.005, 0.462, 0.272, 0.186, 0.215, 0.150, 0.9),   # the wing-case front edge
    ('P0', -0.012, 0.474, 0.300, 0.172, 0.255, 0.152, 0.9),  # the pronotum's rear edge (a step over the wing case)
    ('P1', -0.030, 0.472, 0.300, 0.176, 0.250, 0.155, 0.9),
    ('P2', -0.055, 0.468, 0.300, 0.178, 0.250, 0.160, 0.9),
    ('F0', -0.080, 0.462, 0.300, 0.177, 0.250, 0.165, 0.9),  # fore-leg window F0..F4
    ('F1', -0.105, 0.455, 0.302, 0.172, 0.255, 0.170, 0.9),
    ('F2', -0.130, 0.447, 0.305, 0.163, 0.265, 0.175, 0.9),
    ('F3', -0.155, 0.440, 0.310, 0.150, 0.275, 0.182, 0.9),
    ('F4', -0.180, 0.433, 0.315, 0.135, 0.290, 0.190, 0.9),
    ('P3', -0.198, 0.428, 0.318, 0.124, 0.298, 0.196, 0.93),  # the shield's front edge
    ('H0', -0.218, 0.415, 0.305, 0.106, 0.280, 0.204, 0.97),  # head
    ('H1', -0.245, 0.408, 0.302, 0.101, 0.276, 0.201, 0.97),
    ('H2', -0.272, 0.400, 0.300, 0.100, 0.272, 0.199, 0.97),  # eye station
    ('H3', -0.300, 0.392, 0.298, 0.094, 0.268, 0.200, 0.97),
]
# the face and the head horn, as (top/back point, bottom/front point, half width): the back line runs over the head
# top into the horn's back, the front line from the mouth up the horn's front edge (reference/side.png)
HORNS = [
    ('H4', (-0.327, 0.389), (-0.332, 0.204), 0.085),
    ('H5', (-0.346, 0.392), (-0.360, 0.222), 0.075),   # mouth front
    ('H6', (-0.356, 0.402), (-0.376, 0.262), 0.066),
    ('H7', (-0.364, 0.414), (-0.388, 0.298), 0.058),   # the horn's underside starts over the mouth
    ('H8', (-0.372, 0.430), (-0.410, 0.322), 0.052),
    ('H9', (-0.380, 0.447), (-0.435, 0.348), 0.046),
    ('H10', (-0.387, 0.468), (-0.455, 0.385), 0.041),
    ('H11', (-0.392, 0.493), (-0.467, 0.430), 0.036),
    ('H12', (-0.396, 0.520), (-0.470, 0.480), 0.031),
    ('H13', (-0.399, 0.548), (-0.462, 0.530), 0.026),
    ('H14', (-0.400, 0.572), (-0.445, 0.565), 0.019),
    ('H15', (-0.401, 0.590), (-0.425, 0.590), 0.011),
]


def body_pts(st):
    nm, y, zt, zw, W, zr, zb, tk = st
    return [(x, y, z) for x, z in shell(zt, zw, W, zr, zb, tuck=tk)]


def horn_pts(st):
    nm, (yt, zt), (yb, zb), W = st
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.atan2(yt - yb, zt - zb)
    s, co = math.sin(a), math.cos(a)
    return [(fx * W, c[0] + fh * h * s, c[1] + fh * h * co) for fx, fh in HORN]


SECS = [(s[0], body_pts(s)) for s in BODY] + [(s[0], horn_pts(s)) for s in HORNS]
IDX = {nm: i for i, (nm, _p) in enumerate(SECS)}


def P(nm):
    return [Vector(q) for q in SECS[IDX[nm]][1]]


LJ = 10           # leg windows: ring vertices j10 .. j13 on the under-curve (s1 r6: one below the rim tuck), 3 faces round, 4 spans long
T1_LEG = 0.45     # the transition ring: 45 % of the way from the window rim to the coxa section
# legs (x >= 0 half): window's rear ring, then knee, ankle, tarsus tip; radii: coxa, femur bulge, knee, tibia bulge,
# ankle, tarsus (across, along y)
LEGS = [
    ('leg1', 'F0', (0.215, -0.205, 0.125), (0.235, -0.285, 0.055), (0.245, -0.325, 0.024)),   # fore: forward and out
    ('leg2', 'M0', (0.300, 0.040, 0.135), (0.322, 0.035, 0.055), (0.345, 0.020, 0.024)),      # mid: straight out
    ('leg3', 'B0', (0.278, 0.250, 0.120), (0.305, 0.330, 0.055), (0.315, 0.372, 0.024)),      # hind: back and out
]
LR = dict(coxa=(0.040, 0.046), neck=(0.030, 0.034), femur=(0.038, 0.042), femur_end=(0.032, 0.035),   # s1 r3 beads
          knee=(0.023, 0.025), tibia_top=(0.029, 0.031), tibia=(0.034, 0.037), tibia_end=(0.028, 0.030),
          ankle=(0.018, 0.019), tarsus=(0.023, 0.024), tneck=(0.017, 0.018), tip=(0.021, 0.022))
SE_LEG = 2.4


def akey(t):
    return round(t if t < math.pi - 1e-6 else -math.pi, 4)


def window(rings, i0, j0, A=4, B=3):
    G = [[rings[i0 + a][j0 + b] for b in range(B + 1)] for a in range(A + 1)]
    return G


def leg_sections(G, knee, ankle, tip, normal):
    """The leg's section centres and radii: the coxa out along the window normal, then femur, knee (two rings),
    tibia, ankle, tarsus and the tip."""
    A, B = len(G) - 1, len(G[0]) - 1
    R = sum((G[a][b].co for a in range(A + 1) for b in range(B + 1)), Vector()) / ((A + 1) * (B + 1))
    K, An, T = Vector(knee), Vector(ankle), Vector(tip)
    C = R + normal * 0.030
    L = lambda p, q, t: p.lerp(q, t)
    d1, d2, d3 = (K - C).normalized(), (An - K).normalized(), (T - An).normalized()
    # s1 r1: each bend is three rings (in, on the joint, out), the in/out rings a joint radius and a half off the
    # joint along their own segment, so the inner side of a 90 deg knee no longer folds through itself
    # s1 r3: bead segments (sheet): every segment swells between narrow necks (coxa, femur, tibia, two tarsus beads)
    return R, [
        (C, LR['coxa']),
        (L(C, K, 0.22), LR['neck']),
        (L(C, K, 0.55), LR['femur']),
        (K - d1 * 0.036, LR['femur_end']),
        (K, LR['knee']),
        (K + d2 * 0.036, LR['tibia_top']),
        (L(K, An, 0.55), LR['tibia']),
        (An - d2 * 0.026, LR['tibia_end']),
        (An, LR['ankle']),
        (An + d3 * 0.020, LR['tarsus']),
        (L(An, T, 0.62), LR['tneck']),
        (T, LR['tip']),
    ]


def grow_leg(bm, rings, spans, i0, j0, knee, ankle, tip, A=4, B=3, t1=T1_LEG):
    """Extrude the A x B face window (rings i0..i0+A, ring vertices j0..j0+B) section by section. The first new ring
    slopes from the window rim t1 of the way to the coxa section (the broad transition), then one ring per section,
    each placed in a frame carried along the leg path (parallel transport from the window's own axes)."""
    faces = [spans[i0 + a][j0 + b] for a in range(A) for b in range(B)]
    G = window(rings, i0, j0, A, B)
    Uw = (G[A // 2][0].co - G[A // 2][B].co).normalized()      # role u = +1: the window's upper/outer edge
    Sw = (G[0][B // 2].co - G[A][B // 2].co).normalized()      # role s = +1: the window's ring i0 side
    nrm = sum((f.normal for f in faces), Vector()).normalized()
    R, secs = leg_sections(G, knee, ankle, tip, nrm)
    roles = [(G[a][b].co.copy(), (1 - 2 * b / B, 1 - 2 * a / A)) for a in range(A + 1) for b in range(B + 1)]
    th = sorted({akey(math.atan2(s_, u_)) for _p, (u_, s_) in roles if abs(u_) > 0.999 or abs(s_) > 0.999})
    N = len(th)
    off = 0.0 if any(abs(t) < 1e-6 for t in th) else math.pi / N
    base = min(range(N), key=lambda i: abs(th[i] - (-math.pi + off)))
    amap = {th[(base + i) % N]: -math.pi + off + 2 * math.pi * i / N for i in range(N)}
    # frames: the tangent at each section, E1 (role u) and E2 (role s) carried along
    pts = [R] + [p for p, _r in secs]
    frames = []
    E1 = None
    for k, (p, rr) in enumerate(secs):
        a_, b_ = pts[k], pts[k + 2] if k + 2 < len(pts) else p + (p - pts[k])
        Tn = (b_ - a_).normalized()
        if E1 is None:
            E1 = (Uw - Tn * Tn.dot(Uw)).normalized()
        else:
            q = frames[-1][1].rotation_difference(Tn)
            E1 = q @ E1
            E1 = (E1 - Tn * Tn.dot(E1)).normalized()
        E2 = Tn.cross(E1)
        if E2.dot(Sw) < 0:
            E2 = -E2
        frames.append((p, Tn, E1, E2, rr))

    def pos(fr, u, s, even=True):
        p, Tn, E1, E2, (ru, rs) = fr
        if abs(u) > 0.999 or abs(s) > 0.999:
            t = math.atan2(s, u)
            if even:
                t = amap[akey(t)]
            c, sn = math.cos(t), math.sin(t)
            return p + E1 * (ru * math.copysign(abs(c) ** (2 / SE_LEG), c)) + E2 * (rs * math.copysign(abs(sn) ** (2 / SE_LEG), sn))
        return p + E1 * (u * ru * 0.85) + E2 * (s * rs * 0.85)

    def step(faces, roles, place):
        r = extrude(bm, faces)
        new = []
        for v in r['verts']:
            o = min(roles, key=lambda o_: (o_[0] - v.co).length)
            new.append((v, o))
        for v, (p0, ro) in new:
            v.co = place(p0, ro)
        return r['faces'], [(v.co.copy(), ro) for v, (p0, ro) in new]

    faces, roles = step(faces, roles, lambda p0, ro: p0.lerp(pos(frames[0], *ro, even=False), t1))
    for fr in frames:
        faces, roles = step(faces, roles, lambda p0, ro, fr=fr: pos(fr, *ro))
    return R, nrm


LEG_ROOTS = {}


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, pts) for _nm, pts in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    for nm, w, knee, ankle, tip in LEGS:
        R, n = grow_leg(bm, rings, spans, IDX[w], LJ, knee, ankle, tip)
        LEG_ROOTS[nm] = (R.copy(), n.copy())
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.0, -0.285, 0.300))     # the eye point on the side view (y, z); x from a ray on the head side
SOCKET = []


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    hit = tree.ray_cast(Vector((1.0, EYE.y, EYE.z)), Vector((-1, 0, 0)), 2.0)[0]
    f = face_near(bm, hit, n=(1, 0, 0))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face on the head side'):
        inner = inset(bm, [f], 0.22, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.004)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    # s2 r1: the elytra suture: the wing-case seam vertices 8 mm down, a shallow V groove along the midline
    for nm in [s_[0] for s_ in BODY[1:IDX['M4'] + 1]]:
        move([vert_near(bm, P(nm)[0])], (0.0, 0.0, -0.015))   # s4 r6: 8 -> 15 mm
    # s4 r5: a slimmer head horn across (front view): H7 x 0.9, H8-H14 x 0.82 (the side outline is the sheet's already)
    for nm, f_ in [('H7', 0.9)] + [(f'H{i}', 0.82) for i in range(8, 15)]:
        for q in P(nm):
            v = vert_near(bm, q)
            v.co.x *= f_
    # s3 r3: the head horn's tip: the last ring pulled to a point that hooks back (it was a flat disc)
    h15 = [vert_near(bm, q) for q in P('H15')]
    c15 = sum((v.co for v in h15), Vector()) / len(h15)
    for v in h15:
        d = v.co - c15
        v.co = Vector((v.co.x * 0.7, c15.y + d.y * 0.35 + 0.012, c15.z + d.z * 0.35 + 0.012))
    move([vert_near(bm, q) for q in P('H14')], (0.0, 0.005, 0.0))
    k.meta['keep_valleys'] = lambda c: ((abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.03 and abs(c.z - ec0.z) < 0.03)
                                        or (abs(c.x) < 0.05 and c.y > -0.005 and c.z > 0.3))
    commit(body, bm)


PAL = {'shell': '#743529', 'chitin': '#555157', 'leg': '#4c484f', 'belly': '#453f43', 'eye': '#4a2416',   # s4 r7: both renderers
       'pupil': '#140d0b'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if z < 0.196 and x > 0.205:
        return 'leg'
    if z < 0.135:
        return 'leg'
    if y > -0.003 and z > 0.197:
        return 'shell'
    if z < 0.205 and y > -0.21 and n.z < -0.2:
        return 'belly'
    return 'chitin'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h, sides=10):
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


def hook(bm, base, fwd, down, L, w, curve=75.0, segs=4):
    """A hooked claw: a 4-sided section swept along an arc that starts along fwd and bends toward down, tapering
    to a point; the root sunk 30 % of a width into the foot."""
    f, d = Vector(fwd).normalized(), Vector(down).normalized()
    d = (d - f * f.dot(d)).normalized()
    side = f.cross(d).normalized()
    pts, dirs = [], []
    p, t = base - f * w * 0.3, f.copy()
    for i in range(segs + 1):
        pts.append(p.copy()); dirs.append(t.copy())
        ang = math.radians(curve) * (i + 1) / segs
        t = (f * math.cos(ang) + d * math.sin(ang)).normalized()
        p = p + t * (L / segs)
    rows = []
    for i, (p, t) in enumerate(zip(pts, dirs)):
        s = w * (1 - i / (segs + 0.6))
        nn = side.cross(t).normalized()
        rows.append([bm.verts.new(p + side * su * s + nn * sv * s) for su, sv in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    tip = bm.verts.new(pts[-1] + dirs[-1] * w * 0.6)
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    for j in range(4):
        bm.faces.new([rows[-1][j], rows[-1][(j + 1) % 4], tip])
    recalc_normals(bm)


def stage3(k, body):
    paint(body, PAL, body_rule)
    # night 10-23 border pass (owner 10-21 approved kit/smooth_borders, as frog r17): anti-stair cuts + tangential relax
    # r09: guard the leg roots (r08 unguarded: femur2 seam strip 1.04 r FAIL)
    gl = [(tuple(R), 0.11, 0.0) for R, _n in LEG_ROOTS.values()]
    gl += [((-c[0], c[1], c[2]), r_, f_) for c, r_, f_ in gl]
    smooth_borders(body, k=k, iters=8, guard=gl)
    pieces = []
    # eye: a small round lens in the socket, a dark pupil disc
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.35, 0.0))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.003, n, 0.017, 0.010)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.008 and n_.dot(n) > 0.5 else 'eye')
    pieces.append(eye)
    # the thorax horn on the pronotum's midline (library horn, one shell), growing up and bending forward
    th = PT.horn((0.0, -0.135, 0.435), length=0.13, radius=0.046, taper=1.4, forward=(0, 0.15, 1), up=(0, -1, 0),   # s3 r2
                 curve=60, segs=4, sides=6, name='horn_thorax', mats={'horn': 'chitin', 'horn_tip': 'chitin'},
                 colours={'horn': PAL['chitin'], 'horn_tip': PAL['chitin']})
    pieces.append(th)
    # mandibles: two short hooks under the horn base, curving down and in
    bm = bmesh.new()
    hook(bm, Vector((0.032, -0.352, 0.232)), (0.25, -1, -0.35), (-0.6, 0, -1), 0.045, 0.011, curve=80)
    mand = object_from_bm('mandible', bm)
    paint(mand, {'leg': PAL['leg']}, lambda c_, n_, i: 'leg')
    pieces.append(mand)
    # claws: two hooks per tarsus tip, splayed, bending down to the ground
    bm = bmesh.new()
    for nm, w, knee, ankle, tip in LEGS:
        An, T = Vector(ankle), Vector(tip)
        d3 = (T - An)
        d3.z = 0
        d3.normalize()
        sd = Vector((0, 0, 1)).cross(d3)
        for sgn in (1, -1):
            f = (d3 + sd * 0.45 * sgn).normalized()
            hook(bm, T + sd * 0.009 * sgn, f, (0, 0, -1), 0.050, 0.009, curve=80)
    claws = object_from_bm('claws', bm)
    paint(claws, {'leg': PAL['leg']}, lambda c_, n_, i: 'leg')
    pieces.append(claws)
    return pieces


def stage4(k, body, pieces):
    B = [('abdomen', (0.0, 0.42, 0.30), (0.0, 0.02, 0.31), None),
         ('thorax', (0.0, 0.02, 0.31), (0.0, -0.205, 0.33), 'abdomen', True),
         ('head', (0.0, -0.205, 0.33), (0.0, -0.40, 0.48), 'thorax', True)]
    par = {'leg1': 'thorax', 'leg2': 'thorax', 'leg3': 'abdomen'}
    for nm, w, knee, ankle, tip in LEGS:
        R = LEG_ROOTS[nm][0]
        i = nm[-1]
        B += [(f'femur{i}.L', tuple(R), knee, par[nm]),
              (f'tibia{i}.L', knee, ankle, f'femur{i}.L', True),
              (f'tarsus{i}.L', ankle, tip, f'tibia{i}.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    A = 14
    ga = ['femur1.L', 'femur2.R', 'femur3.L']
    gb = ['femur1.R', 'femur2.L', 'femur3.R']
    sw = lambda g, a: {b: (0, 0, a if b.endswith('.L') else -a) for b in g}
    lift = lambda g: {b.replace('femur', 'tibia'): (-10, 0, 0) for b in g}
    clip(rig, 'idle', {1: {}, 12: {'thorax': (1.5, 0, 0), 'head': (-2, 0, 0)}, 24: {'head': (2, 0, 2)},
                       36: {'thorax': (1.5, 0, 0), 'head': (-2, 0, -2)}, 48: {}})
    clip(rig, 'move', {1: {**sw(ga, A), **sw(gb, -A)},
                       7: {**lift(ga)},
                       13: {**sw(ga, -A), **sw(gb, A)},
                       19: {**lift(gb)},
                       25: {**sw(ga, A), **sw(gb, -A)}})
    clip(rig, 'attack', {1: {}, 8: {'thorax': (-6, 0, 0), 'head': (-14, 0, 0)},
                         14: {'thorax': (-8, 0, 0), 'head': (-20, 0, 0)},
                         20: {'thorax': (6, 0, 0), 'head': (16, 0, 0)}, 26: {'thorax': (2, 0, 0), 'head': (6, 0, 0)},
                         32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
