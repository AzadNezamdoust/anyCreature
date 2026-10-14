import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='goblin', model='opus',
            keep_valleys=lambda c: c.y < -0.10 and 0.58 < c.z < 0.92)   # eye sockets and the grin dent in

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    pelvis=(0, 0.15, 0.30), spine=(0, 0.16, 0.46), chest=(0, 0.16, 0.60), neck=(0, 0.13, 0.66),
    head=(0, 0.05, 0.76), crown=(0, 0.0, 1.02),
    hip=(0.10, 0.13, 0.25), knee=(0.195, 0.0, 0.19), ankle=(0.20, 0.14, 0.07), toe=(0.22, -0.05, 0.02),
    shoulder=(0.16, 0.145, 0.61), elbow=(0.345, 0.155, 0.41), wrist=(0.40, 0.08, 0.235),
    hand=(0.415, 0.03, 0.08), ear=(0.20, 0.10, 0.88), eartip=(0.53, 0.21, 0.93),
)

XA, YA, ZA = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

# ---------------------------------------------------------------- body rings
# (y_front, z_front, y_back, z_back, half-width, profile); a ring lies in the plane
# through its front and back seam points and the X axis; profile = 4 (t, x/w) points
T = [(0.08, 0.72), (0.33, 1.0), (0.67, 1.0), (0.92, 0.70)]          # torso: boxy 10-gon
P = [(0.12, 0.30), (0.30, 1.0), (0.70, 1.0), (0.88, 0.30)]          # pelvis: leg quad outside
H = [(0.10, 0.62), (0.35, 1.0), (0.62, 1.0), (0.87, 0.65)]          # skull
HJ = [(0.08, 0.80), (0.33, 1.0), (0.62, 1.0), (0.87, 0.62)]          # jaw: square front corners
HN = [(0.06, 0.36), (0.33, 1.0), (0.62, 1.0), (0.87, 0.65)]         # nose root narrow, eye plane wide
RINGS = [
    (0.03, 0.240, 0.230, 0.260, 0.130, P),      # R0 crotch / hips
    (-0.050, 0.350, 0.280, 0.370, 0.142, T),    # R1 belt
    (-0.085, 0.450, 0.295, 0.470, 0.152, T),    # R2 pot belly
    (-0.030, 0.545, 0.305, 0.565, 0.136, T),    # R3 lower chest
    (0.020, 0.620, 0.285, 0.660, 0.148, T),     # R4 armpit / shoulders
    (0.030, 0.645, 0.230, 0.735, 0.120, T),     # R5 neck base (traps, hunched)
    (-0.010, 0.655, 0.140, 0.770, 0.100, H),    # R6 neck top: throat -> nape
    (-0.180, 0.585, 0.185, 0.815, 0.165, HJ),   # R7 jaw: chin
    (-0.222, 0.655, 0.205, 0.840, 0.190, HJ),   # R8 mouth
    (-0.232, 0.755, 0.212, 0.875, 0.190, HN),   # R9 nose base / cheek
    (-0.258, 0.875, 0.205, 0.955, 0.200, HN),   # R10 brow / eyes
    (-0.220, 0.985, 0.165, 1.035, 0.180, H),    # R11 forehead
    (-0.110, 1.075, 0.070, 1.090, 0.100, H),    # R12 crown
]


LEG = [((0.105, 0.12, 0.20), (0.35, -0.55, -1.0), 0.062, 0.055),
((0.195, 0.000, 0.185), (0.55, -0.1, -1.0), 0.050, 0.046),
((0.205, 0.070, 0.130), (0.0, 0.75, -0.65), 0.042, 0.040),
((0.200, 0.145, 0.070), (-0.05, 0.3, -1.0), 0.036, 0.036),
((0.210, 0.075, 0.034), (0.1, -1.0, -0.3), 0.032, 0.052)]
ARM = [((0.205, 0.145, 0.575), (0.7, 0.0, -1.0), 0.052, 0.058),
((0.280, 0.150, 0.490), (0.5, 0.0, -1.0), 0.040, 0.046),
((0.345, 0.155, 0.410), (0.3, -0.1, -1.0), 0.036, 0.042),
((0.375, 0.120, 0.320), (0.25, -0.35, -1.0), 0.033, 0.035),
((0.400, 0.080, 0.235), (0.2, -0.3, -1.0), 0.024, 0.026)]


def ringpts(yf, zf, yb, zb, w, prof):
    F, B = Vector((0, yf, zf)), Vector((0, yb, zb))
    pts = [F]
    for t, xf in prof:
        p = F.lerp(B, t)
        pts.append(Vector((xf * w, p.y, p.z)))
    pts.append(B)
    return pts


def frame(a, r):
    a = Vector(a).normalized(); r = Vector(r)
    f = (r - r.dot(a) * a).normalized()
    s = a.cross(f).normalized()
    return a, s, f


def corners(c, a, r, w, d):
    a, s, f = frame(a, r)
    c = Vector(c)
    return [c - w * s - d * f, c + w * s - d * f, c + w * s + d * f, c - w * s + d * f]


def classify(verts, a, r):
    """Quadrants (s-,f-), (s+,f-), (s+,f+), (s-,f+) of a quad in the frame (a, r)."""
    _, s, f = frame(a, r)
    c = centre(verts)
    out = [None] * 4
    for v in verts:
        o = v.co - c
        out[{(False, False): 0, (True, False): 1, (True, True): 2, (False, True): 3}[(o.dot(s) > 0, o.dot(f) > 0)]] = v
    assert None not in out, 'classify: quadrant collision'
    return out


def seam_clean(bm):
    for f in [f for f in bm.faces if all(abs(v.co.x) < 1e-5 for v in f.verts)]:
        bm.faces.remove(f)
    for e in [e for e in bm.edges if not e.link_faces]:
        bm.edges.remove(e)


def limb(bm, face, secs, r, a0=None, seam=False):
    """Extrude a chain: secs = [(centre, axis, w, d)]. Returns the end face."""
    prev = a0 if a0 is not None else secs[0][1]
    cur = face
    for c, a, w, d in secs:
        ex = extrude(bm, [cur])
        nf = ex['faces'][0]
        q = classify(list(nf.verts), prev, r)
        for v, p in zip(q, corners(c, a, r, w, d)):
            v.co = p
            if seam and abs(v.co.x) < 1e-4:
                v.co.x = 0.0
        if seam:
            seam_clean(bm)
        prev, cur = a, nf
    return cur


def split3(bm, face, a0, r, c, a, W, D, spread='s', arch=0.0):
    """A knuckle row: the end quad becomes a section with three end quads (three digits)."""
    q = classify(list(face.verts), a0, r)
    A, s, f = frame(a, r)
    if spread == 's':
        sp, ot = s, f
        pp, nn = [q[3], q[2]], [q[0], q[1]]
    else:
        sp, ot = f, s
        pp, nn = [q[1], q[2]], [q[0], q[3]]
    c = Vector(c)
    us = (-1.0, -1 / 3, 1 / 3, 1.0)
    k = [bm.verts.new(c + u * W * sp + D * ot + (arch * (1 - abs(u))) * A) for u in us]
    j = [bm.verts.new(c + u * W * sp - D * ot + (arch * (1 - abs(u))) * A) for u in us]
    bm.faces.remove(face)
    N = bm.faces.new
    N([pp[0], pp[1], k[3], k[2]]); N([pp[0], k[2], k[1], k[0]])
    N([nn[0], j[0], j[1], j[2]]); N([nn[0], j[2], j[3], nn[1]])
    N([pp[1], nn[1], j[3], k[3]]); N([pp[0], k[0], j[0], nn[0]])
    return [N([k[i], k[i + 1], j[i + 1], j[i]]) for i in range(3)]


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, ringpts(*R)) for R in RINGS]
    for rr in rings:
        rr[0].co.x = rr[-1].co.x = 0.0
    strips = [bridge(bm, a, b) for a, b in zip(rings, rings[1:])]
    b0, t0 = rings[0], rings[-1]
    bm.faces.new([b0[0], b0[1], b0[4], b0[5]])
    legf = bm.faces.new([b0[1], b0[2], b0[3], b0[4]])
    bm.faces.new([t0[0], t0[1], t0[4], t0[5]])
    bm.faces.new([t0[1], t0[2], t0[3], t0[4]])
    recalc_normals(bm)

    # ---- legs (r = X): hip, knee, shin, ankle, foot, three toes
    rl = XA
    leg = LEG
    end = limb(bm, legf, leg, rl, a0=(0, 0, -1))
    toes = split3(bm, end, leg[-1][1], rl, (0.220, -0.005, 0.024), (0.12, -1.0, 0.0), 0.052, 0.022,
                  spread='f', arch=0.008)
    # toe ends ordered along f (+X side last); tips splay outward
    for tf, (tx, ty) in zip(toes, [(0.162, -0.070), (0.222, -0.078), (0.285, -0.066)]):
        mid = ((tx + 0.205) / 2 + 0.0, (ty - 0.005) / 2 - 0.005, 0.02)
        limb(bm, tf, [((tx, ty, 0.012), (tx - 0.220, -0.07, -0.01), 0.010, 0.011)], rl, a0=(0.12, -1.0, 0.0))

    # ---- arms (r = -Y): deltoid, upper arm, elbow, forearm, wrist, hand, three fingers
    ra = -YA
    armf = strips[3][2]
    arm = ARM
    end = limb(bm, armf, arm, ra, a0=(1, 0, 0))
    ha = (0.1, -0.25, -1.0)
    rh = Vector((0.5, -0.87, 0.0))        # the palm turned 30 deg: fingers read from the front and the side
    fing = split3(bm, end, arm[-1][1], rh, (0.418, 0.045, 0.160), ha, 0.050, 0.024, spread='f', arch=0.012)
    for ff in fing:
        c0 = centre(list(ff.verts))
        dx, dy = (c0.x - 0.418) * 1.3, (c0.y - 0.045) * 1.3
        mid = (c0.x + dx * 0.3 + 0.004, c0.y + dy * 0.3 - 0.014, 0.106)
        tip = (c0.x + dx * 0.7 - 0.004, c0.y + dy * 0.7 - 0.040, 0.066)
        limb(bm, ff, [(mid, (0.05, -0.25, -1.0), 0.015, 0.015),
                      (tip, (0.0, -0.7, -1.0), 0.007, 0.007)], rh, a0=ha)

    # ---- ears (r = Z): long horizontal blades, sweeping slightly back
    re = ZA
    earf = strips[9][3]
    limb(bm, earf, [((0.255, 0.105, 0.878), (1.0, 0.25, 0.05), 0.022, 0.066),
                    ((0.385, 0.155, 0.902), (1.0, 0.35, 0.12), 0.015, 0.038),
                    ((0.535, 0.212, 0.930), (1.0, 0.4, 0.15), 0.004, 0.006)], re, a0=(1, 0, 0))

    # ---- hooked nose: a seam extrusion out of the nose-root quad (half sections, x in [0, 2w])
    nosef = strips[9][0]
    limb(bm, nosef, [((0.030, -0.285, 0.800), (0, -1.0, -0.35), 0.030, 0.045),
                     ((0.022, -0.322, 0.765), (0, -0.7, -1.0), 0.022, 0.030),
                     ((0.011, -0.335, 0.728), (0, -0.2, -1.0), 0.011, 0.012)], ZA, a0=(0, -1, 0), seam=True)
    snap_seam(bm, 1e-4)
    recalc_normals(bm)
    return object_from_bm('body', bm)


def RP(i, j):
    """Stage-1 position of ring i, profile point j."""
    return ringpts(*RINGS[i])[j]


def seg_edge(bm, secs, i, t=0.5):
    """An edge running ALONG a limb between sections i and i+1 (for a ring cut)."""
    (c0, a0, w0, d0), (c1, a1, w1, d1) = secs[i], secs[i + 1]
    r = XA if secs is LEG else -YA
    p = corners(c0, a0, r, w0, d0)[2].lerp(corners(c1, a1, r, w1, d1)[2], t)
    return edge_near(bm, p)


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'brow loop above R10: the heavy brow ridge gets its own row to overhang the eyes'):
        e = edge_near(bm, RP(10, 3).lerp(RP(11, 3), 0.5))
        loopcut(bm, e, t=0.35, near=vert_near(bm, RP(10, 3)))
    with k.topo(bm, 'loop', 'mouth loop between chin R7 and R8: the grin line and the lip plane'):
        e = edge_near(bm, RP(7, 3).lerp(RP(8, 3), 0.5))
        loopcut(bm, e, t=0.55, near=vert_near(bm, RP(7, 3)))
    with k.topo(bm, 'loop', 'second elbow loop: the arm bends at A3'):
        loopcut(bm, seg_edge(bm, ARM, 1), t=0.6)
    with k.topo(bm, 'loop', 'second knee loop: the crouched knee bends at L2'):
        loopcut(bm, seg_edge(bm, LEG, 0), t=0.6)
    eyec = (RP(9, 1) + RP(9, 2) + RP(10, 1) + RP(10, 2)) / 4
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye quad under the brow'):
        ins = inset(bm, [face_near(bm, eyec, n=(0.3, -1, 0.1))], 0.32, depth=-0.012)
    for f in ins:
        for v in f.verts:
            v.co.z += 0.012
    # ---- vertex moves: the brow overhangs, the cheekbones stand out, the grin is cut in
    for j, dy in ((0, -0.010), (1, -0.022), (2, -0.016)):
        vert_near(bm, RP(10, j)).co.y += dy
    brow = verts_where(bm, lambda c: 0.90 < c.z < 0.95 and c.y < -0.12)
    for v in brow:
        v.co.y -= 0.012
    for j in (2,):
        v = vert_near(bm, RP(9, j)); v.co.x += 0.012; v.co.y -= 0.006
    mouth = verts_where(bm, lambda c: 0.60 < c.z < 0.66 and c.y < -0.17)
    for v in mouth:
        v.co.y += 0.018
    # chin and jaw: flat planes
    flatten([vert_near(bm, RP(7, j)) for j in (0, 1, 2)] + [vert_near(bm, RP(6, j)) for j in (0, 1)])
    # pot belly: push the belly front forward and down a touch; flatten the chest plate
    for j in (0, 1):
        vert_near(bm, RP(2, j)).co.y -= 0.012
    flatten([vert_near(bm, RP(i, j)) for i in (3, 4) for j in (0, 1)])
    # hooked nose: narrow root, a ridge along the bridge, a fleshy drooping tip
    vert_near(bm, RP(9, 1)).co.x -= 0.014
    vert_near(bm, RP(10, 1)).co.x -= 0.010
    NC = [(Vector((0, -0.285, 0.800)), Vector((0, -1.0, -0.35))), (Vector((0, -0.322, 0.765)), Vector((0, -0.7, -1.0))),
          (Vector((0, -0.335, 0.728)), Vector((0, -0.2, -1.0)))]
    for v in verts_where(bm, lambda c: c.y < -0.265 and c.x > 0.004):
        c, a = min(NC, key=lambda q: (Vector((0, v.co.y, v.co.z)) - q[0]).length)
        _, _, f = frame(a, ZA)
        if (v.co - c).dot(f) > 0:          # the upper edge: pulled to the middle -> a bridge ridge
            v.co.x *= 0.55
        else:                               # the lower edge: the nostril wings spread a touch
            v.co.x *= 1.15
    commit(body, bm)


PAL = {'skin': '#6aa84f', 'belly': '#9ccc7a', 'belt': '#4a3222', 'cloth': '#7a5a3a',
       'fang': '#efe6cf', 'eye': '#f2d23c', 'buckle': '#a89f86'}


def body_rule(c, n, i):
    ax = abs(c.x)
    if c.y < -0.15 and 0.600 < c.z < 0.662 and ax < 0.15 and n.y < -0.2:
        return 'belt'                                      # the grin: dark mouth band on the mouth loop
    if 0.36 < c.z < 0.63 and c.y < 0.10 and ax < 0.115 and n.y < -0.35:
        return 'belly'                                     # chest plate and pot belly, on ring edges
    return 'skin'


def spike(bm, base, tip, r, n=4, up=None):
    """A low-poly cone: an n-gon base (radius r) at `base`, apex at `tip`."""
    base, tip = Vector(base), Vector(tip)
    a = (tip - base).normalized()
    u = (up or Vector((0.3, 0.2, 1.0))).cross(a).normalized()
    w = a.cross(u)
    vs = [bm.verts.new(base + r * (math.cos(t) * u + math.sin(t) * w)) for t in [2 * math.pi * i / n for i in range(n)]]
    t = bm.verts.new(tip)
    for i in range(n):
        bm.faces.new([vs[i], vs[(i + 1) % n], t])
    bm.faces.new(vs[::-1])


def band_row(z_t, off, hb=None):
    """A belt row on the body between R1 and R2 (z_t > 0) or R1 and R0 (z_t < 0), pushed out by off.
    hb: the base bmesh, so the row follows the stage-2 surface (not the stage-1 rings)."""
    ymid = 0.5 * (RINGS[1][0] + RINGS[1][2])
    P_ = (lambda i, j: vert_near(hb, RP(i, j)).co.copy()) if hb is not None else RP
    R = []
    for j in range(6):
        p = P_(1, j).lerp(P_(2, j), z_t) if z_t >= 0 else P_(1, j).lerp(P_(0, j), -z_t)
        q = p + Vector((p.x, p.y - ymid, 0)).normalized() * off
        if j in (0, 5):
            q.x = 0.0
        R.append(q)
    return R


def flap(name, y_top, y_bot, z_top, hem, thick):
    """A loincloth flap: a thin closed plate, seam at x = 0, jagged hem."""
    xs = [0.0, 0.035, 0.065, 0.095]
    top = [Vector((x, y_top, z_top)) for x in xs]
    bot = [Vector((x, y_bot, z)) for x, z in zip(xs, hem)]
    sg = 1 if y_top > 0 else -1
    bm = bmesh.new()
    Ft, Fb = ring(bm, top), ring(bm, bot)
    Kt = ring(bm, [p + Vector((0, -sg * thick, 0)) for p in top])
    Kb = ring(bm, [p + Vector((0, -sg * thick, 0)) for p in bot])
    bridge(bm, Ft, Fb); bridge(bm, Kb, Kt); bridge(bm, Kt, Ft); bridge(bm, Fb, Kb)
    bm.faces.new([Ft[3], Kt[3], Kb[3], Fb[3]])
    ob = object_from_bm(name, bm)
    paint(ob, PAL, lambda c, n, i: 'cloth')
    return ob


def stage3(k, body):
    paint(body, PAL, body_rule)
    from mathutils.bvhtree import BVHTree
    eb = evaluated_bm(body)
    tree = BVHTree.FromBMesh(eb)

    def hit(o, d):
        loc, nor, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
        return loc, nor

    pieces = []
    # ---- belt: a thick closed band following the body, proud of the skin
    hb0 = edit(body)
    bm = bmesh.new()
    rows = [ring(bm, r) for r in (band_row(0.42, 0.022, hb0), band_row(0.02, 0.022, hb0),
                                  band_row(0.02, 0.006, hb0), band_row(0.42, 0.006, hb0))]
    hb0.free()
    for a, b in zip(rows, rows[1:] + rows[:1]):
        bridge(bm, a, b)
    belt = object_from_bm('belt', bm)
    paint(belt, PAL, lambda c, n, i: 'belt')
    pieces.append(belt)
    # ---- buckle: a chunky plate on the front seam, proud of the belt
    fy = min(band_row(0.42, 0.022)[0].y, band_row(0.02, 0.022)[0].y)
    bm = bmesh.new()
    x1, y0, y1, z0, z1 = 0.045, fy - 0.014, fy + 0.010, 0.358, 0.418
    v = [bm.verts.new(p) for p in [(0, y0, z0), (x1, y0, z0), (x1, y1, z0), (0, y1, z0),
                                   (0, y0, z1), (x1, y0, z1), (x1, y1, z1), (0, y1, z1)]]
    for f in ([0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [0, 3, 2, 1], [4, 5, 6, 7]):
        bm.faces.new([v[i] for i in f])
    buckle = object_from_bm('buckle', bm)
    paint(buckle, PAL, lambda c, n, i: 'buckle')
    pieces.append(buckle)
    # ---- tattered loincloth, front and back
    pieces.append(flap('cloth_front', -0.079, -0.064, 0.370, [0.10, 0.175, 0.145, 0.225], 0.010))
    pieces.append(flap('cloth_back', 0.303, 0.325, 0.390, [0.12, 0.185, 0.150, 0.235], 0.010))
    # ---- claws on the finger and toe tip faces (found on the base, read only)
    hb = edit(body)
    tips = [f for f in hb.faces if f.calc_center_median().z < 0.075 and f.calc_center_median().x > 0.33
            and f.normal.z < -0.3 and f.calc_area() < 4e-4]
    toes = [f for f in hb.faces if f.calc_center_median().y < -0.06 and f.calc_center_median().z < 0.04
            and f.normal.y < -0.6]
    say('claw sites', len(tips), len(toes))
    bm = bmesh.new()
    for f in tips:
        c, n = f.calc_center_median(), f.normal
        d = (n + Vector((0, -0.25, 0))).normalized()
        spike(bm, c - d * 0.004, c + d * 0.030, 0.007)
    for f in toes:
        c, n = f.calc_center_median(), f.normal
        d = (n + Vector((0, 0, -0.25))).normalized()
        spike(bm, c - d * 0.004, c + d * 0.026, 0.008)
    hb.free()
    claws = object_from_bm('claws', bm)
    paint(claws, PAL, lambda c, n, i: 'fang')
    pieces.append(claws)
    # ---- fangs: two big lower tusks up over the lip, two small upper teeth down
    bm = bmesh.new()
    for x, z0, z1, r, lean in ((0.085, 0.612, 0.690, 0.013, 0.010), (0.035, 0.668, 0.630, 0.008, 0.0)):
        loc, nor = hit((x, -0.6, (z0 + z1) / 2), (0, 1, 0))
        yb = loc.y + 0.006
        spike(bm, (x, yb, z0), (x + lean, yb - 0.012, z1), r, up=Vector((1, 0, 0)))
    fangs = object_from_bm('fangs', bm)
    paint(fangs, PAL, lambda c, n, i: 'fang')
    pieces.append(fangs)
    # ---- eyes: a low disc lens in each socket, proud of it; the pupil is the inner fan
    loc, nor = hit((0.118, -0.6, 0.838), (0, 1, 0))
    bm = bmesh.new()
    n = (nor + Vector((0, -0.4, 0))).normalized()
    u = Vector((0, 0, 1)).cross(n).normalized(); w = n.cross(u)
    c = loc + n * 0.004
    angs = [2 * math.pi * i / 6 for i in range(6)]
    outer = [bm.verts.new(c + 0.037 * math.cos(t) * u + 0.025 * math.sin(t) * w) for t in angs]
    inner = [bm.verts.new(c + n * 0.006 + 0.011 * math.cos(t) * u + 0.014 * math.sin(t) * w) for t in angs]
    front, back = bm.verts.new(c + n * 0.008), bm.verts.new(c - n * 0.010)
    pupil = set()
    for i in range(6):
        j = (i + 1) % 6
        bm.faces.new([outer[i], outer[j], inner[j], inner[i]])
        bm.faces.new([inner[i], inner[j], front])
        bm.faces.new([outer[j], outer[i], back])
    eye = object_from_bm('eye', bm)
    fc = c + n * 0.0065
    paint(eye, PAL, lambda cc, nn, i: 'belt' if (cc - fc).length < 0.008 else 'eye')
    pieces.append(eye)
    eb.free()
    return pieces


def stage4(k, body, pieces):
    L = lambda n: J[n]
    rig = armature([
        ('hips', L('pelvis'), L('spine'), None),
        ('spine', L('spine'), (0, 0.16, 0.60), 'hips', True),
        ('neck', (0, 0.16, 0.60), (0, 0.10, 0.70), 'spine', True),
        ('head', (0, 0.10, 0.70), (0, 0.0, 1.02), 'neck', True),
        ('ear.L', L('ear'), L('eartip'), 'head'),
        ('thigh.L', L('hip'), L('knee'), 'hips'),
        ('shin.L', L('knee'), L('ankle'), 'thigh.L', True),
        ('foot.L', L('ankle'), L('toe'), 'shin.L', True),
        ('upperarm.L', L('shoulder'), L('elbow'), 'spine'),
        ('forearm.L', L('elbow'), L('wrist'), 'upperarm.L', True),
        ('hand.L', L('wrist'), L('hand'), 'forearm.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathe, look left and right, flick an ear, fidget the fingers
    clip(rig, 'idle', {
        1: {},
        12: {'head': (0, 18, 4), 'spine': (3, 0, 0), 'hand.L': (12, 0, 0), 'ear.L': (0, 0, 8)},
        24: {'head': (-6, 0, 0), 'spine': (0, 0, 0), 'hand.R': (12, 0, 0)},
        36: {'head': (0, -18, -4), 'spine': (3, 0, 0), 'ear.R': (0, 0, -8), 'hand.L': (6, 0, 0)},
        48: {}})
    # move: sneaky crouched walk, low arms swinging against the legs
    A = {'thigh.L': (22, 0, 0), 'shin.L': (-10, 0, 0), 'thigh.R': (-18, 0, 0), 'shin.R': (14, 0, 0),
         'upperarm.L': (-14, 0, 0), 'upperarm.R': (14, 0, 0), 'spine': (6, 4, 0), 'head': (-4, -4, 0)}
    B = {'thigh.R': (22, 0, 0), 'shin.R': (-10, 0, 0), 'thigh.L': (-18, 0, 0), 'shin.L': (14, 0, 0),
         'upperarm.R': (-14, 0, 0), 'upperarm.L': (14, 0, 0), 'spine': (6, -4, 0), 'head': (-4, 4, 0)}
    clip(rig, 'move', {1: A, 17: B, 33: A})
    # attack: wind up the right claw high, swipe down and across, recover
    clip(rig, 'attack', {
        1: {},
        8: {'upperarm.R': (105, 0, 30), 'forearm.R': (45, 0, 0), 'hand.R': (-15, 0, 0), 'spine': (-5, -14, 0), 'head': (-8, 0, 0)},
        13: {'upperarm.R': (30, 0, -30), 'forearm.R': (10, 0, 0), 'hand.R': (25, 0, 0), 'spine': (9, 16, 0)},
        18: {'upperarm.R': (15, 0, -10), 'spine': (4, 6, 0)},
        24: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
