import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from mathutils import Quaternion

META = dict(creature='crab', model='opus',
            keep_valleys=lambda c: c.y < -0.24 and c.z > 0.28 and abs(c.x) < 0.16)

# ---------------------------------------------------------------------------
# body sections along Y: (y, rim half-width w, top z, rim z, bottom z)
SECT = [(-0.30, 0.12, 0.335, 0.285, 0.13),
        (-0.25, 0.205, 0.360, 0.285, 0.11),
        (-0.16, 0.275, 0.378, 0.282, 0.095),
        (-0.08, 0.305, 0.385, 0.279, 0.09),
        (0.03, 0.318, 0.385, 0.275, 0.09),
        (0.14, 0.295, 0.370, 0.270, 0.095),
        (0.24, 0.225, 0.345, 0.265, 0.11),
        (0.33, 0.10, 0.315, 0.260, 0.135)]


def half_ring(y, w, top, rim, bot):
    return [(0.0, y, top),                          # T  top seam
            (0.55 * w, y, top - 0.22 * (top - rim)),  # D  dome shoulder
            (w, y, rim),                            # R  rim edge
            (0.84 * w, y, rim - 0.055),             # U  under the rim
            (0.72 * w, y, bot + 0.035),             # L  lower side (legs between U and L)
            (0.42 * w, y, bot + 0.004),             # B  belly
            (0.0, y, bot)]                          # S  bottom seam


RINGS = [half_ring(*s) for s in SECT]


def side_centre(i):
    """centre of the U-L face between sections i and i+1"""
    a, b = RINGS[i], RINGS[i + 1]
    return tuple((a[3][k] + a[4][k] + b[3][k] + b[4][k]) / 4 for k in range(3))


def vadd(p, r, s, z):
    return (p[0] + r[0] * s, p[1] + r[1] * s, z)


# walking legs: (section interval, yaw degrees from +X toward +Y, length scale)
LEGS = [(2, -22.0, 0.92), (3, 16.0, 1.0), (4, 44.0, 1.0), (5, 68.0, 0.92)]
# leg profile: (s along the leg's radial direction, z, width, depth)
LEGP = [(0.07, 0.185, 0.074, 0.080),
        (0.11, 0.202, 0.070, 0.084),
        (0.24, 0.292, 0.064, 0.076),
        (0.28, 0.292, 0.060, 0.070),
        (0.38, 0.165, 0.054, 0.060),
        (0.395, 0.135, 0.046, 0.050),
        (0.418, 0.000, 0.0, 0.0)]
# stage 2 leg profile: knee rings swell (~1.2x the femur), tarsus thins, the second bend moves out
LEG_RING_SCALE = {2: 1.3, 3: 1.3, 4: 0.92, 5: 0.9}
BEND_OUT = 0.016
LEG_TAPER = {4: 0.86, 5: 0.80}     # extra across-plane taper on the tibia end and the tarsus
KNEE_BUMP = 0.008
# repair K=2 item 2: knees lower and further out (splay, not peak); the tip cone shorter
KNEE_DROP = 0.012        # ~3 % of the creature height (6 % costs side IoU 0.898)
KNEE_OUT = 0.020         # ~4 % of the leg span, along the leg's reach
TIP_UP = 0.0            # 0.027 (20 %) lifts the bbox: IoU 0.891 in every view


def leg_pts(i):
    si, yaw, ls = LEGS[i]
    root = side_centre(si)
    r = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
    pts = [vadd(root, r, s * ls, z) for s, z, w, h in LEGP]
    return root, r, pts


# cheliped (big claw)
CLAW_ROOT_SI = 1
U = Vector((-0.5, -0.866, 0.0))           # palm axis (forward, a little inward)
CLAW_ARM = [((0.28, -0.26, 0.170), (0.064, 0.066)),
            ((0.35, -0.31, 0.175), (0.070, 0.074)),
            ((0.395, -0.345, 0.170), (0.080, 0.086)),
            ((0.39, -0.375, 0.160), (0.130, 0.160)),
            ((0.35, -0.44, 0.155), (0.155, 0.200)),
            ((0.305, -0.51, 0.150), (0.125, 0.170))]
P2 = Vector(CLAW_ARM[-1][0])
PMID = (Vector(CLAW_ARM[-2][0]) + P2) / 2 + Vector((0, 0, 0.092))
U2 = Vector((-0.87, -0.49, 0.0))         # the fingers curl inward, across the front
_f1 = P2 + U * 0.05 + Vector((0, 0, -0.045))
_f2 = _f1 + U2 * 0.06 + Vector((0, 0, -0.018))
FINGER = [(tuple(_f1), (0.060, 0.060)),
          (tuple(_f2), (0.040, 0.042)),
          (tuple(_f2 + U2 * 0.055 + Vector((0, 0, 0.008))), (0.0, 0.0))]
_d1 = PMID + U * 0.08 + Vector((0, 0, 0.035))
_d2 = _d1 + U2 * 0.065 + Vector((0, 0, -0.05))
DACTYL = [(tuple(PMID + Vector((0, 0, 0.045))), (0.075, 0.060)),
          (tuple(_d1), (0.060, 0.054)),
          (tuple(_d2), (0.040, 0.040)),
          (tuple(_d2 + U2 * 0.05 + Vector((0, 0, -0.055))), (0.0, 0.0))]

# ---------------------------------------------------------------------------
# skeleton: the same points the model is built on
J = dict(body_a=(0.0, 0.16, 0.22), body_b=(0.0, -0.16, 0.22))
for _i in range(4):
    _root, _r, _p = leg_pts(_i)
    J[f'l{_i}_root'] = _root
    J[f'l{_i}_hip'] = _p[1]
    J[f'l{_i}_knee'] = tuple(Vector(_p[2]) + Vector((_r[0], _r[1], 0)) * KNEE_OUT * LEGS[_i][2] - Vector((0, 0, KNEE_DROP)))
    J[f'l{_i}_bend'] = tuple(Vector(_p[4]) + Vector((_r[0], _r[1], 0)) * BEND_OUT * LEGS[_i][2])
    J[f'l{_i}_tip'] = tuple(Vector(_p[6]) + Vector((0, 0, TIP_UP)))
J['c_root'] = side_centre(CLAW_ROOT_SI)
J['c_elbow'] = CLAW_ARM[1][0]
J['c_wrist'] = CLAW_ARM[3][0]
J['c_palm'] = CLAW_ARM[5][0]
J['c_ftip'] = FINGER[-1][0]
J['c_droot'] = tuple(PMID)
J['c_dtip'] = DACTYL[-1][0]


def fcentre(f):
    return f.calc_center_median()


def limb(bm, face, pts, afix=None):
    """Extrude `face` through pts = [(point, (width, depth)), ...]; each new section is the
    old one re-scaled into a frame perpendicular to the path. (0, 0) at the end = a point."""
    cur, prev, steps, alast = face, None, [], afix
    Z = Vector((0, 0, 1))
    for i, (p, (w, h)) in enumerate(pts):
        p = Vector(p)
        back = Vector(pts[i - 1][0]) if i else fcentre(cur)
        din = (p - back).normalized()
        dout = (Vector(pts[i + 1][0]) - p).normalized() if i + 1 < len(pts) else din
        d = (din + dout).normalized()
        if afix is not None:
            a = Vector(afix)
        else:
            dh = Vector((d.x, d.y, 0))
            a = Z.cross(dh).normalized() if dh.length > 0.2 else alast
        b = d.cross(a).normalized()
        a = b.cross(d).normalized()
        alast = a
        pa, pb = prev if prev else (a, b)
        r = extrude(bm, [cur])
        f = r['faces'][0]
        vs = list(f.verts)
        c = centre(vs)
        us = [(v.co - c).dot(pa) for v in vs]
        ws = [(v.co - c).dot(pb) for v in vs]
        mu, mw = max(abs(x) for x in us), max(abs(x) for x in ws)
        if w == 0:
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=p)
            steps.append((None, r['sides']))
            break
        for v, u_, w_ in zip(vs, us, ws):
            v.co = p + a * (u_ / mu) * w / 2 + b * (w_ / mw) * h / 2
        prev = (a, b)
        steps.append((f, r['sides']))
        cur = f
    return steps


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, pts) for pts in RINGS]
    side = {}
    for i in range(len(rows) - 1):
        fs = bridge(bm, rows[i], rows[i + 1])
        for j, f in enumerate(fs):
            side[(i, j)] = f
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    bm.normal_update()
    # walking legs
    for i in range(4):
        si, yaw, ls = LEGS[i]
        root, r, pts = leg_pts(i)
        a = Vector((0, 0, 1)).cross(Vector((r[0], r[1], 0))).normalized()
        dims = [(w * 1.0, h) for s, z, w, h in LEGP]
        limb(bm, side[(si, 3)], list(zip(pts, dims)), afix=a)
    # cheliped: arm and palm, then the fixed finger from the palm end and the
    # movable finger (dactyl) from the top of the last palm segment
    steps = limb(bm, side[(CLAW_ROOT_SI, 3)], CLAW_ARM)
    end_face, last_sides = steps[-1]
    for f in last_sides:
        f.normal_update()
    top = max(last_sides, key=lambda f: f.normal.z)
    apalm = Vector((0, 0, 1)).cross(U).normalized()
    limb(bm, end_face, FINGER, afix=apalm)
    limb(bm, top, DACTYL, afix=apalm)
    snap_seam(bm)
    return object_from_bm('body', bm)


EYE_SOCKET = None      # set in stage2: centre of the eye socket face (x > 0)
BAND_PTS, SOCKET_PTS = [], []


def stage2(k, body):
    global EYE_SOCKET
    bm = edit(body)
    R = RINGS
    # 1. rim band: one full loop along the carapace slope, the plane change from dome to rim
    #    and the border of the dark-ridge colour
    def dr(i):
        return edge_near(bm, (Vector(R[i][1]) + Vector(R[i][2])) / 2)
    with k.topo(bm, 'partial_loop', 'rim band: the carapace slope turns into the flat rim; dark-ridge colour border; '
                                    'terminated on the flat front and rear slope (no bend there)'):
        band = partial_loop(bm, dr(1), dr(6), t=0.6, near=vert_near(bm, R[1][1]), terminate='fan')
    for v in band:                       # a slight crown: the band edge stands proud of the slope
        v.co.z += 0.010
        v.co.x += 0.006
    # 2. eye sockets: an inset in the front slope face (sections 0-1), where the stalks root
    c = sum((Vector(R[i][j]) for i in (0, 1) for j in (1, 2)), Vector()) / 4
    f = face_near(bm, c, n=(0, -0.3, 1))
    with k.topo(bm, 'inset', 'eye socket: the orbit the eye stalk rises from'):
        inner = inset(bm, [f], 0.45, 0.0)
    for v in inner[0].verts:
        v.co += inner[0].normal * -0.012
    EYE_SOCKET = tuple(inner[0].calc_center_median())
    SOCKET_PTS[:] = [tuple(v.co) for v in inner[0].verts]
    BAND_PTS[:] = [tuple(v.co) for v in band]
    # 3. carapace crown: the seam row rises to a low central peak, the dome planes converge on it
    for i, dz in ((2, 0.008), (3, 0.016), (4, 0.016), (5, 0.008)):
        vert_near(bm, R[i][0]).co.z += dz
    # 4. flat belly plate
    flatten([v for v in bm.verts if v.co.z < 0.14 and v.co.x < 0.15 and abs(v.co.y) < 0.3])
    # 5. walking legs: knee swell, thinner tarsus, and the second bend pushed out so it reads
    cands = []                                    # (centre, leg, ring index); -1 = the root face
    for i in range(4):
        root, r, pts = leg_pts(i)
        cands.append((Vector(root), i, -1))
        cands += [(Vector(p), i, j) for j, p in enumerate(pts[:-1])]
    rings = {}
    for v in bm.verts:
        best = min(cands, key=lambda t: (v.co - t[0]).length)
        if (v.co - best[0]).length < 0.075 and best[2] >= 0:
            rings.setdefault((best[1], best[2]), []).append(v)
    for i in range(4):
        _, r, pts = leg_pts(i)
        a = Vector((0, 0, 1)).cross(Vector((r[0], r[1], 0))).normalized()   # across the leg plane
        for j, f in LEG_RING_SCALE.items():
            vs = rings.get((i, j), [])
            assert len(vs) == 4, (i, j, len(vs))
            if j in (2, 3):
                # knee: swell across the leg plane only (scaling in the bend plane pinches the
                # inside of the knee), plus a low bump on top
                c = centre(vs)
                for v in vs:
                    v.co += a * ((v.co - c).dot(a) * (f - 1))
                    if v.co.z > c.z:
                        v.co.z += KNEE_BUMP
            else:
                scale(vs, f, centre(vs))
                # repair K=2 item 5: taper toward the tip, across the leg plane only
                c = centre(vs)
                for v in vs:
                    v.co += a * ((v.co - c).dot(a) * (LEG_TAPER[j] - 1))
        out = Vector((r[0], r[1], 0)) * BEND_OUT * LEGS[i][2]
        move(rings[(i, 4)] + rings[(i, 5)], out)
        move(rings[(i, 2)] + rings[(i, 3)], Vector((r[0], r[1], 0)) * KNEE_OUT * LEGS[i][2] - Vector((0, 0, KNEE_DROP)))
        vert_near(bm, pts[6]).co.z += TIP_UP
    claw_pincer(bm)
    commit(body, bm)


# stage 2 claw: thick pincer fingers with a lens gap (repair K=2 item 1)
FING_SCALE = {('f', 0): 1.35, ('f', 1): 1.45, ('d', 0): 1.15, ('d', 1): 1.35, ('d', 2): 1.45}
FTIPS = []              # the moved finger tips, for the stage-3 dark-tip rule
TIP_PULL = 0.12         # the point moves 12 % back toward the last ring: a short blunt tip
FIX_EXTEND = 0.3       # fixed finger tip moves 30 % of its last segment further out
TIP_CURL = 15.0         # fixed finger tip up, moving finger tip down (deg)
PALM_SHAVE = 0.0        # any shave costs side IoU (8 %: 0.899); the knees need that room


def claw_pincer(bm):
    secs = {('f', j): (Vector(p), w, h) for j, (p, (w, h)) in enumerate(FINGER)}
    secs.update({('d', j): (Vector(p), w, h) for j, (p, (w, h)) in enumerate(DACTYL)})
    secs.update({('p', j): (Vector(p), w, h) for j, (p, (w, h)) in enumerate(CLAW_ARM) if j >= 4})
    # walk the rings back from each tip point along the extrusion edges
    grp = {}
    for side, pts in (('f', FINGER), ('d', DACTYL)):
        tip = min(bm.verts, key=lambda v: (v.co - Vector(pts[-1][0])).length)
        rings_ = [[tip]]
        prev_set = {tip}
        for j in range(len(pts) - 2, -1, -1):
            nxt = {e.other_vert(v) for v in rings_[-1] for e in v.link_edges} - prev_set
            if j < len(pts) - 2:
                nxt -= set(rings_[-2])
            nxt = [v for v in nxt if v not in rings_[-1]]
            rings_.append(nxt)
            prev_set |= set(nxt)
        for j, vs in enumerate(reversed(rings_)):
            grp[(side, j)] = vs
    # palm rings 4 and 5 by distance to their centre (the palm is large and square)
    for j in (4, 5):
        p, (w, h) = Vector(CLAW_ARM[j][0]), CLAW_ARM[j][1]
        grp[('p', j)] = sorted(bm.verts, key=lambda v: abs((v.co - p).length - math.hypot(w, h) / 2))[:4]
    for key, (p, w, h) in secs.items():
        n = 1 if w == 0 else 4
        assert len(grp.get(key, [])) == n, (key, len(grp.get(key, [])))
    # palm: the bottom of the two palm rings comes in so palm and fingers read as one pincer
    for j in (4, 5):
        vs = grp[('p', j)]
        zc = centre(vs).z
        for v in vs:
            if v.co.z < zc:
                v.co.z += PALM_SHAVE
    # fingers: thicker rings, tips curled toward each other and pulled back (blunt)
    for key, f in FING_SCALE.items():
        vs = grp[key]
        scale(vs, f, centre(vs))
    apalm = Vector((0, 0, 1)).cross(U).normalized()
    for side, sign in (('f', 1), ('d', -1)):
        pts = FINGER if side == 'f' else DACTYL
        last = len(pts) - 1
        tip = grp[(side, last)][0]
        prev = Vector(pts[last - 1][0])
        tip.co = tip.co.lerp(prev, TIP_PULL if side == 'd' else -FIX_EXTEND)   # the fixed finger is short: lengthen it
        root = Vector(pts[0][0])
        ax = (tip.co - root).cross(Vector((0, 0, 1))).normalized()
        # rotate the tip (fully) and the last ring (half) about the root, so the tip curls in z
        for vs, deg in ((grp[(side, last - 1)], TIP_CURL * 0.5), ([tip], TIP_CURL)):
            for v in vs:
                q = v.co - root
                ang = math.radians(deg)
                cand = [Quaternion(ax, ang) @ q, Quaternion(ax, -ang) @ q]
                v.co = root + max(cand, key=lambda c: sign * c.z)
        FTIPS.append((tuple(tip.co), (tip.co - centre(grp[(side, last - 1)])).length))


from mathutils.bvhtree import BVHTree

PAL = {'shell': '#c8502e', 'ridge': '#8e3420', 'belly': '#efc9a0', 'tip': '#2a1c18',
       'eye': '#111111', 'barnacle': '#e6d6bc'}


def frustum(bm, a, b, ra, rb, n, rot=0.0):
    """closed n-sided frustum (rb = 0: a cone) from point a to point b"""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    e1 = d.cross(ref).normalized(); e2 = d.cross(e1).normalized()
    ang = [math.radians(rot) + 2 * math.pi * i / n for i in range(n)]
    ra_ = [bm.verts.new(a + (e1 * math.cos(t) + e2 * math.sin(t)) * ra) for t in ang]
    bm.faces.new(list(reversed(ra_)))
    if rb == 0:
        tip = bm.verts.new(b)
        for i in range(n):
            bm.faces.new([ra_[i], ra_[(i + 1) % n], tip])
        return ra_, None
    rb_ = [bm.verts.new(b + (e1 * math.cos(t) + e2 * math.sin(t)) * rb) for t in ang]
    bridge(bm, ra_, rb_, closed=True)
    return ra_, bm.faces.new(rb_)


def bicone(bm, c, r, h, n):
    c = Vector(c)
    rv = [bm.verts.new(c + Vector((math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, 0)))
          for i in range(n)]
    top, bot = bm.verts.new(c + Vector((0, 0, h))), bm.verts.new(c - Vector((0, 0, h * 0.8)))
    for i in range(n):
        bm.faces.new([rv[i], rv[(i + 1) % n], top])
        bm.faces.new([rv[(i + 1) % n], rv[i], bot])


def ball(bm, c, r, n):
    """low-poly ball (repair K=2 item 4): n-sided equator, rings at +-0.7r (radius 0.71r) and
    +-0.95r (radius 0.31r) with small n-gon caps, so it reads round in every view"""
    c = Vector(c)
    rows = []
    for zf in (-0.95, -0.7, 0.0, 0.7, 0.95):
        rf = math.sqrt(max(0.0, 1 - zf * zf))
        rows.append([bm.verts.new(c + Vector((math.cos(2 * math.pi * (i + 0.5) / n) * r * rf,
                                              math.sin(2 * math.pi * (i + 0.5) / n) * r * rf, zf * r)))
                     for i in range(n)])
    bm.faces.new(list(reversed(rows[0])))
    for a_, b_ in zip(rows, rows[1:]):
        bridge(bm, a_, b_, closed=True)
    bm.faces.new(rows[-1])


def stage3(k, body):
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)

    def hit(o, d):
        loc, nrm, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
        return loc, nrm

    # ---- body colours: shell, dark ridge band, cream underside, dark leg and finger tips
    ring_pts = [Vector(p) for r in RINGS for p in r] + [Vector(p) for p in BAND_PTS + SOCKET_PTS]
    me = body.data
    body_face = {p.index for p in me.polygons
                 if all(min((me.vertices[v].co - q).length for q in ring_pts) < 0.03 for v in p.vertices)}
    tips = [(Vector(t), ln) for t, ln in FTIPS]      # only the last ~30 % of each finger is dark

    def u_z(y):             # z of the under-rim loop (U vertex) at y
        ys = [s[0] for s in SECT]
        y = min(max(y, ys[0]), ys[-1])
        for (y0, _, _, r0, _), (y1, _, _, r1, _) in zip(SECT, SECT[1:]):
            if y <= y1:
                t = (y - y0) / (y1 - y0)
                return (r0 + (r1 - r0) * t) - 0.055
        return SECT[-1][3] - 0.055

    def rule(c, n, i):
        q = Vector((abs(c.x), c.y, c.z))
        if any((q - t).length < 0.72 * ln for t, ln in tips):
            return 'tip'
        if i in body_face:
            zs = [me.vertices[v].co.z for v in me.polygons[i].vertices]
            # cream only at or below the rim's lower edge loop (U): the underside and a low
            # band; the front wall and the rim lip above it stay shell
            below = max(zs) <= u_z(c.y) + 0.004
            if below or (n.z < -0.2 and n.y > -0.5):      # front-facing lip faces stay shell
                return 'belly'
            if n.z > 0.1 and max(zs) < 0.335:
                return 'ridge'
            return 'shell'
        if c.z < 0.10 and math.hypot(q.x, q.y) > 0.36:
            return 'tip'
        return 'shell'
    paint(body, {k_: PAL[k_] for k_ in ('shell', 'ridge', 'belly', 'tip')}, rule)
    pieces = []

    # ---- eye stalks rooted in the sockets, black bulb eyes
    bm = bmesh.new()
    sk = Vector(EYE_SOCKET)
    top = sk + Vector((-0.004, -0.018, 0.075)) * 0.84         # stalk 1.4x the r13 height, 0.8x its radius
    frustum(bm, sk - Vector((0, 0, 0.018)), top, 0.0184, 0.0136, 5)
    ball(bm, top + Vector((0, -0.003, 0.013)), 0.029, 10)     # round eye, ~1.6x the stalk width
    eye = object_from_bm('eyes', bm)
    zt = top.z
    paint(eye, {'shell': PAL['shell'], 'eye': PAL['eye']}, lambda c, n, i: 'eye' if c.z > zt - 0.008 else 'shell')
    pieces.append(eye)

    # ---- toothed front rim (repair K=2 item 3): 6 thick pyramids per side from the front edge to
    #      the claw joint; base depth 65 % of the base width, height 70 %, tip tilted 15 deg down,
    #      sunk 35 %; graded 70 % at the eyes up to 100 % at the anterolateral corner; shell red
    bm = bmesh.new()
    zz = Vector((0, 0, 1))
    c15, s15 = math.cos(math.radians(15)), math.sin(math.radians(15))

    def tooth(p, tg, o, bw):
        h, bd = 0.7 * bw, 0.65 * bw
        bc = p - o * 0.35 * h
        vs = [bm.verts.new(bc + tg * sx * bw / 2 + zz * sz)
              for sx, sz in ((-1, -0.65 * bd), (1, -0.65 * bd), (1, 0.35 * bd), (-1, 0.35 * bd))]
        tip = bm.verts.new(bc + (o * c15 - zz * s15) * h)
        bm.faces.new(vs)
        for j in range(4):
            bm.faces.new([vs[(j + 1) % 4], vs[j], tip])

    t0, d0 = Vector(RINGS[0][0]), Vector(RINGS[0][1])
    path = [t0.lerp(d0, 0.55), d0] + [Vector(RINGS[i][2]) for i in range(0, 4)]
    segs = list(zip(path, path[1:]))
    # one on the front edge between the eyes, then five past the eye stalk (a tooth in front of the
    # stalk put the stalk through it: hit), largest at the anterolateral corner
    for arc, bw in ((0.020, 0.035), (0.168, 0.050), (0.225, 0.050), (0.282, 0.047), (0.337, 0.043), (0.390, 0.038)):
        s_ = arc
        for a_, b_ in segs:
            ln = (b_ - a_).length
            if s_ <= ln:
                break
            s_ -= ln
        p = a_.lerp(b_, min(s_ / ln, 1.0))
        tg = b_ - a_; tg.z = 0; tg.normalize()
        o = Vector((tg.y, -tg.x, 0))
        if o.dot(Vector((p.x, p.y + 0.02, 0))) < 0:
            o = -o
        tooth(p, tg, o, bw)
    teeth = object_from_bm('rim_teeth', bm)
    paint(teeth, {'shell': PAL['shell']}, lambda c, n, i: 'shell')
    pieces.append(teeth)

    # (pincer spur spikes dropped in repair K=2: they read as needles and stretched across the gap)

    # ---- barnacle cluster on the rear rim: pale 8-sided cones with a dark crater (5_reference rear);
    #      the two smallest sink 45 % so the cluster beds into the shell (repair K=2 should-fix)
    bm = bmesh.new()
    craters = []
    for x, z, r in ((0.004, 0.302, 0.028), (0.046, 0.296, 0.020), (-0.040, 0.299, 0.023),
                    (0.020, 0.326, 0.016), (-0.018, 0.278, 0.017)):
        loc, nrm = hit((x, 0.9, z + 0.57), (0, -0.6, -0.57))
        if loc is None:
            continue
        h = 1.1 * r
        sink = 0.45 if r < 0.018 else 0.3
        _, topf = frustum(bm, loc - nrm * sink * h, loc + nrm * (1 - sink) * h, r, r * 0.6, 8, rot=x * 900)
        craters.append((loc + nrm * (1 - sink) * h, r))
        inset(bm, [topf], 0.4, -h * 0.3)      # the crater
    bar = object_from_bm('barnacles', bm, mirror=False)
    paint(bar, {'barnacle': PAL['barnacle'], 'tip': PAL['tip']},
          lambda c, n, i: 'tip' if any((c - p).length < 0.4 * r_ for p, r_ in craters) else 'barnacle')
    pieces.append(bar)
    ebm.free()
    return pieces


def set_rolls(rig):
    """local Z = the limb plane's normal (Z x the limb's horizontal reach), so +Z rotation swings
    every limb tip DOWN on both sides and +X yaws it counter-clockwise seen from above"""
    Zv = Vector((0, 0, 1))
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            sx = -1 if eb.name.endswith('.R') else 1
            if eb.name == 'body':
                eb.align_roll(Zv)
                continue
            if eb.name.startswith('leg'):
                i = int(eb.name[3])
                r = Vector(J[f'l{i}_tip']) - Vector(J[f'l{i}_root'])
                r = Vector((r.x * sx, r.y, 0))
            elif 'dactyl' in eb.name or 'pollex' in eb.name:
                r = Vector((U.x * sx, U.y, 0))
            else:
                r = eb.tail - eb.head
                r = Vector((r.x, r.y, 0))
            eb.align_roll(Zv.cross(r.normalized()))
        bpy.ops.object.mode_set(mode='OBJECT')


def M(rot):           # the .R twin of a bone-local rotation: yaw (X) and twist (Y) flip
    return (-rot[0], -rot[1], rot[2])


def K(**kw):
    out = {}
    for nm, rot in kw.items():
        out[nm + '.L'] = rot
        out[nm + '.R'] = M(rot)
    return out


def stage4(k, body, pieces):
    bones = [('body', J['body_a'], J['body_b'], None)]
    for i in range(4):
        q = lambda n_, i=i: J[f'l{i}_{n_}']
        bones += [(f'leg{i}_coxa.L', q('root'), q('hip'), 'body'),
                  (f'leg{i}_femur.L', q('hip'), q('knee'), f'leg{i}_coxa.L', True),
                  (f'leg{i}_tibia.L', q('knee'), q('bend'), f'leg{i}_femur.L', True),
                  (f'leg{i}_tarsus.L', q('bend'), q('tip'), f'leg{i}_tibia.L', True)]
    bones += [('claw_arm.L', J['c_root'], J['c_elbow'], 'body'),
              ('claw_wrist.L', J['c_elbow'], J['c_wrist'], 'claw_arm.L', True),
              ('claw_palm.L', J['c_wrist'], J['c_palm'], 'claw_wrist.L', True),
              ('claw_pollex.L', J['c_palm'], J['c_ftip'], 'claw_palm.L', True),
              ('claw_dactyl.L', J['c_droot'], J['c_dtip'], 'claw_palm.L')]
    rig = armature(bones)
    set_rolls(rig)
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: two claw clicks, a slow breath
    clip(rig, 'idle', {1: K(claw_dactyl=(0, 0, 0), claw_arm=(0, 0, 0)),
                       8: K(claw_dactyl=(0, 0, -24), claw_arm=(0, 0, -2)),
                       12: K(claw_dactyl=(0, 0, 2), claw_arm=(0, 0, -3)),
                       20: K(claw_dactyl=(0, 0, -24), claw_arm=(0, 0, -4)),
                       24: K(claw_dactyl=(0, 0, 2), claw_arm=(0, 0, -4)),
                       36: K(claw_dactyl=(0, 0, 0), claw_arm=(0, 0, -2)),
                       48: K(claw_dactyl=(0, 0, 0), claw_arm=(0, 0, 0))},
         loc={1: {'body': (0, 0, 0)}, 24: {'body': (0, 0, 0.006)}, 48: {'body': (0, 0, 0)}})
    # move: sideways scuttle, alternating leg sets (A: L0 L2 R1 R3; B: the others)
    A = {('leg0', 'L'), ('leg2', 'L'), ('leg1', 'R'), ('leg3', 'R')}
    lift = dict(coxa=(0, 0, -14), tibia=(0, 0, -8))
    push = dict(coxa=(0, 0, 3), tibia=(0, 0, 5))

    def legs(pa, pb):
        out = {}
        for i in range(4):
            for sd in 'LR':
                ph = pa if (f'leg{i}', sd) in A else pb
                for seg in ('coxa', 'tibia'):
                    r = ph.get(seg, (0, 0, 0))
                    out[f'leg{i}_{seg}.{sd}'] = r if sd == 'L' else M(r)
        out.update(K(claw_arm=(0, 0, -5)))
        return out
    clip(rig, 'move', {1: legs({}, {}), 7: legs(lift, push), 13: legs({}, {}), 19: legs(push, lift), 25: legs({}, {})},
         loc={1: {'body': (0, 0, 0)}, 7: {'body': (-0.014, 0, 0.008)}, 13: {'body': (0, 0, 0)},
              19: {'body': (0.014, 0, 0.008)}, 25: {'body': (0, 0, 0)}})
    # attack: claws rise and open, lunge, snap shut, recover
    clip(rig, 'attack', {1: K(claw_arm=(0, 0, 0), claw_wrist=(0, 0, 0), claw_dactyl=(0, 0, 0)),
                         8: K(claw_arm=(0, 0, -16), claw_wrist=(0, 0, -8), claw_dactyl=(0, 0, -26)),
                         14: K(claw_arm=(0, 0, 5), claw_wrist=(0, 0, 6), claw_dactyl=(0, 0, -26)),
                         16: K(claw_arm=(0, 0, 6), claw_wrist=(0, 0, 6), claw_dactyl=(0, 0, 3)),
                         24: K(claw_arm=(0, 0, 2), claw_wrist=(0, 0, 2), claw_dactyl=(0, 0, 2)),
                         32: K(claw_arm=(0, 0, 0), claw_wrist=(0, 0, 0), claw_dactyl=(0, 0, 0))},
         loc={1: {'body': (0, 0, 0)}, 8: {'body': (0, -0.02, 0.01)}, 14: {'body': (0, 0.035, 0)},
              24: {'body': (0, 0.01, 0)}, 32: {'body': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
