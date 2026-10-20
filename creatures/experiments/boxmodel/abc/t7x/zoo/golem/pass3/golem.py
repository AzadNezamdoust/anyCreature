import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# stone golem (biped), t7 hand box-model adapted to a biped: ONE vertical spine loft of 6-vertex half rings
# (crotch -> crown; each ring horizontal, front seam -> back seam), legs extruded from the 3-face region of the
# crotch-hip span, arms from the 3-face side region of the upper-chest span, as 8-sided limb rings.
META = dict(creature='golem', model='opus', stage1_tris=(1200, 3200), total_tris=(2000, 5000),
            closeups=[('head', (0.0, -0.32, 1.83), 0.28, 'hero'),
                      ('fist', (0.89, -0.06, 0.42), 0.28, 'hero'),
                      ('foot', (0.40, -0.12, 0.08), 0.24, 'hero')])

J = dict(
    hips=(0.0, 0.0, 0.66), spine=(0.0, 0.0, 0.95), chest=(0.0, 0.0, 1.25), neck=(0.0, -0.10, 1.60),
    head=(0.0, -0.22, 1.75), crown=(0.0, -0.24, 2.005),
    shoulder=(0.56, 0.0, 1.58), elbow=(0.85, -0.01, 1.12), wrist=(0.90, -0.05, 0.62), fist=(0.89, -0.05, 0.26),
    hipL=(0.30, 0.0, 0.62), knee=(0.33, 0.0, 0.32), ankle=(0.35, 0.0, 0.10), toe=(0.40, -0.40, 0.03),
)

# horizontal half-ring profiles, front seam -> back seam: (x as a fraction of W, h: +1 front (-Y) .. -1 back)
# pass 3: 10-vertex half rings (was 6): a rounded super-ellipse torso (stone mass, still flat facets) and a head
# with one flat front plane for the lens eye and a tapering skull back.
def _sup(n, k=10):
    out = []
    for i in range(k):
        t = math.pi * i / (k - 1)
        sx, cx = math.sin(t), math.cos(t)
        out.append((round(abs(sx) ** (2 / n), 4) if 0 < i < k - 1 else 0.0, round(math.copysign(abs(cx) ** (2 / n), cx), 4)))
    return out


TORSO = _sup(2.8)
HEAD = [(0, 1), (0.7, 0.92), (0.88, 0.72), (0.98, 0.42), (1, 0.1), (0.98, -0.2), (0.92, -0.5), (0.8, -0.75), (0.5, -0.95), (0, -1)]


def hs(nm, z, yc, F, Bk, W, prof):
    """A horizontal section at height z: front depth F, back depth Bk about yc, half-width W."""
    return (nm, z, yc, F, Bk, W, prof)


# pass 3: 18 stations (was 12), new ones where the silhouette curves; torso widths re-read from the front trace
# (z < 1.15, where the torso is clear of the arms), depths blended toward the side trace.
SECS = [
    hs('P0', 0.60, 0.0, 0.14, 0.16, 0.07, TORSO),     # crotch
    hs('P1', 0.74, 0.0, 0.28, 0.34, 0.45, TORSO),     # hips (trace W 0.45)
    hs('P1a', 0.81, 0.0, 0.31, 0.38, 0.41, TORSO),    # pass 3: hip -> waist curve (trace W 0.41)
    hs('P2', 0.88, 0.0, 0.35, 0.40, 0.39, TORSO),     # waist (trace W 0.385)
    hs('P2a', 0.96, -0.01, 0.41, 0.45, 0.43, TORSO),  # pass 3: belly swell (trace W 0.43)
    hs('P3', 1.04, -0.02, 0.48, 0.49, 0.49, TORSO),   # belly
    hs('P3a', 1.14, -0.03, 0.55, 0.54, 0.52, TORSO),  # pass 3: belly -> chest overhang (trace W 0.52)
    hs('P4', 1.25, -0.04, 0.59, 0.58, 0.54, TORSO),   # chest
    hs('P4a', 1.35, -0.03, 0.58, 0.61, 0.53, TORSO),  # pass 3: pec -> back hump
    hs('P5', 1.45, -0.02, 0.54, 0.62, 0.50, TORSO),   # upper chest / back hump
    hs('P6', 1.60, 0.0, 0.44, 0.50, 0.44, TORSO),     # shoulder shelf
    hs('N0', 1.66, -0.14, 0.23, 0.25, 0.18, HEAD),    # neck
    hs('H0', 1.75, -0.24, 0.23, 0.18, 0.22, HEAD),    # jaw
    hs('H0a', 1.80, -0.25, 0.23, 0.18, 0.235, HEAD),  # pass 3: cheek (front trace head W 0.25 near z 1.85)
    hs('H1', 1.865, -0.26, 0.22, 0.17, 0.235, HEAD),  # eye line
    hs('H1a', 1.915, -0.25, 0.20, 0.16, 0.205, HEAD), # pass 3: brow -> skull curve
    hs('H2', 1.955, -0.24, 0.17, 0.15, 0.165, HEAD),  # skull
    hs('H3', 2.005, -0.24, 0.09, 0.08, 0.075, HEAD),  # crown
]

# limb sections: (centre, axis, r along Y, r across). Pass 3: 12-sided rings (was 8), arm 9 -> 13 and leg 7 -> 11
# sections; the forearm and elbow re-read from the front trace (arm centre/half-width at each height).
ARM = [((0.48, 0.0, 1.60), (1, 0, 0), 0.22, 0.15),         # 0 shoulder root
       ((0.48, 0.0, 1.705), (0.988, 0, 0.161), 0.27, 0.248),   # 1 pass 3: boulder inner wall, top over the shoulder at x 0.44 z 1.95 (front trace top x 0.35 z 1.96)
       ((0.605, 0.0, 1.70), (0.989, 0, -0.149), 0.29, 0.235),  # 2 pass 3: boulder crown (trace outer x 0.66 at z 1.85)
       ((0.72, 0.0, 1.63), (0.862, 0, -0.507), 0.26, 0.197),   # 3 pass 3: boulder outer shoulder, rounding down
       ((0.78, 0.0, 1.52), (0.5, 0, -0.87), 0.235, 0.19),      # 4 pass 3: turning into the upper arm (trace outer x 0.91 at z 1.6)
       ((0.79, 0.0, 1.36), (0.25, 0, -1), 0.23, 0.205),     # 5 upper arm
       ((0.845, -0.01, 1.13), (0.2, 0, -1), 0.215, 0.21),   # 6 elbow (trace r 0.27)
       ((0.87, -0.02, 1.00), (0.1, 0, -1), 0.26, 0.25),     # 7 pass 3: forearm top (trace c 0.87 r 0.25)
       ((0.89, -0.03, 0.88), (0, 0, -1), 0.29, 0.275),      # 8 forearm
       ((0.89, -0.04, 0.74), (0, 0, -1), 0.26, 0.25),       # 9 pass 3: forearm low (trace r 0.26)
       ((0.88, -0.05, 0.62), (0, 0, -1), 0.19, 0.185),      # 10 wrist
       ((0.87, -0.05, 0.44), (0, 0, -1), 0.23, 0.24),       # 11 fist
       ((0.86, -0.05, 0.25), (0, 0, -1), 0.20, 0.21)]       # 12 fist end
LEG = [((0.30, 0.0, 0.55), (0, 0, -1), 0.20, 0.17),         # 0 thigh top
       ((0.32, 0.0, 0.50), (0, 0, -1), 0.215, 0.19),        # 1 pass 3: thigh upper
       ((0.34, 0.0, 0.44), (0, 0, -1), 0.22, 0.20),         # 2 thigh
       ((0.345, 0.0, 0.38), (0, 0, -1), 0.20, 0.19),        # 3 pass 3: above the knee
       ((0.35, 0.0, 0.32), (0, 0, -1), 0.17, 0.17),         # 4 knee
       ((0.355, 0.0, 0.26), (0, 0, -1), 0.18, 0.18),        # 5 pass 3: below the knee
       ((0.36, 0.0, 0.20), (0, 0, -1), 0.19, 0.19),         # 6 shin
       ((0.37, 0.0, 0.10), (0, 0, -1), 0.17, 0.18),         # 7 ankle
       ((0.39, -0.07, 0.06), (0, 0, -1), 0.27, 0.215),      # 8 pass 3: foot top bevel
       ((0.40, -0.10, 0.04), (0, 0, -1), 0.32, 0.23),       # 9 foot slab
       ((0.40, -0.10, 0.0), (0, 0, -1), 0.32, 0.23)]        # 10 sole


def sec_pts(z, yc, F, Bk, W, prof):
    return [(fx * W, yc - fh * (F if fh >= 0 else Bk), z) for fx, fh in prof]


def P(nm):
    for s in SECS:
        if s[0] == nm:
            return [Vector(q) for q in sec_pts(*s[1:])]


def frame_of_axis(ax):
    a = Vector(ax).normalized()
    e1 = Vector((0, 1, 0)) - a * a.y
    e1.normalize()
    return a, e1, a.cross(e1)


def limb(bm, faces, secs):
    """Extrude a face region section by section; each region vertex keeps an angle around the limb axis
    (evenly spaced in the region's own order), each section is an ellipse across its axis."""
    vs = list({v for f in faces for v in f.verts})
    c0 = sum((v.co for v in vs), Vector()) / len(vs)
    n0 = sum((f.normal for f in faces), Vector()).normalized()
    a, e1, e2 = frame_of_axis(n0)
    raw = {v: math.atan2((v.co - c0).dot(e2), (v.co - c0).dot(e1)) for v in vs}
    # pass 3: walk the region's boundary loop (a wide 12-vertex region seen from a tilted normal is not star-shaped,
    # so an angle sort mis-orders it), oriented so the angle increases
    fs = set(faces)
    nb = {v: [] for v in vs}
    for e in {e for f in faces for e in f.edges}:
        if sum(1 for lf in e.link_faces if lf in fs) == 1:
            a_, b_ = e.verts
            nb[a_].append(b_); nb[b_].append(a_)
    loop = [min(vs, key=lambda v: raw[v])]
    prev = None
    while True:
        nxt = [w for w in nb[loop[-1]] if w is not prev][0]
        if nxt is loop[0]:
            break
        prev = loop[-1]; loop.append(nxt)
    wrap = lambda d: (d + math.pi) % (2 * math.pi) - math.pi
    if sum(wrap(raw[loop[(i + 1) % len(loop)]] - raw[loop[i]]) for i in range(len(loop))) < 0:
        loop = [loop[0]] + loop[:0:-1]
    order = loop
    n = len(order)
    off = math.atan2(sum(math.sin(raw[v] - 2 * math.pi * i / n) for i, v in enumerate(order)),
                     sum(math.cos(raw[v] - 2 * math.pi * i / n) for i, v in enumerate(order)))
    st = 2 * math.pi / n
    off = round((off - st / 2) / st) * st + st / 2         # s1 r5: an edge (not a vertex) on top, front and sides
    ang = {v: off + st * i for i, v in enumerate(order)}
    for c, ax, ry, rx in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(ang, key=lambda o: (o.co - v.co).length)
            new[v] = ang[ov]
        _a, f1, f2 = frame_of_axis(ax)
        for v, t in new.items():
            v.co = Vector(c) + f1 * (math.cos(t) * ry) + f2 * (math.sin(t) * rx)
        faces, ang = r['faces'], new
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {s[0]: i for i, s in enumerate(SECS)}
    rings = [ring(bm, sec_pts(*s[1:])) for s in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    limb(bm, [spans[idx['P0']][j] for j in (2, 3, 4, 5, 6)], LEG)     # pass 3: 5 of 9 faces -> 12-sided rings
    limb(bm, [spans[idx['P5']][j] for j in (2, 3, 4, 5, 6)], ARM)
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    A, B_ = P('H0a'), P('H1')                           # pass 3: the flat front plane of the cheek-eye span
    return (A[0] + A[1] + B_[0] + B_[1]) / 4


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.05 and abs(c.y - ec0.y) < 0.05 and abs(c.z - ec0.z) < 0.06


def ring_pt(sec, t):
    c, ax, ry, rx = sec
    _a, f1, f2 = frame_of_axis(ax)
    return Vector(c) + f1 * (math.cos(t) * ry) + f2 * (math.sin(t) * rx)


def between(secs, i):
    """A point on the limb side between sections i and i+1, on a longitudinal edge (vertex angle 75 deg on the 12-sided ring)."""
    t = math.radians(75)
    return tuple((ring_pt(secs[i], t) + ring_pt(secs[i + 1], t)) / 2)


def stage2(k, body):
    """Joint rings (elbow, wrist, knee, ankle, waist, neck), the eye socket and the brow."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    cuts = [('elbow ring: the elbow bend', between(ARM, 5)),
            ('wrist ring: the wrist bend', between(ARM, 9)),
            ('knee ring: the knee bend', between(LEG, 3)),
            ('ankle ring: the ankle bend', between(LEG, 6)),
            ('waist ring: the spine bend', mid(P('P1a')[0], P('P2')[0])),
            ('neck ring: the head nod', mid(P('N0')[0], P('H0')[0]))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_), t=0.5)
    ec0 = eye_face_centre()
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    # fix pass: the eye-socket inset is gone (it read as a visor mask); the lens sits on plain face planes
    H1 = P('H1')
    move([vert_near(bm, H1[0]), vert_near(bm, H1[1])], (0.0, -0.025, 0.0))     # brow ridge over the eyes
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


PAL = {'stone': '#b3aea6', 'dark': '#928d86', 'light': '#cbc5bb', 'moss': '#7fa040', 'glow': '#5ee6ff'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if z > 1.66 and x > 0.38 and n.z > 0.45:
        return 'moss'                                   # moss on the shoulder boulders
    if x > 0.78 and 1.30 < z < 1.70 and n.x > 0.55 and c.y < 0.05:
        return 'moss'                                   # fix pass: a second moss patch down the outer upper arm
    if z < 0.64 or (x > 0.62 and z < 0.70):
        return 'dark'                                   # legs, pelvis floor and fists
    if x < 0.32 and 0.86 < z < 1.08 and n.y < -0.5:
        return 'light'                                  # the pale lower belly plate
    return 'stone'


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


def keep_x(vs):
    lo = min(v.co.x for v in vs)
    if lo < 0.003:                                      # never across the mirror plane
        for v in vs:
            v.co.x += 0.003 - lo


def clump(bm, a, n, lay, s, L):
    """A flat moss clump: square base sunk in the body, a thick mid, a blunt tip laid along `lay`."""
    n, lay = Vector(n).normalized(), Vector(lay).normalized()
    u = n.cross(lay).normalized(); w = u.cross(n)
    b = a - n * 0.03
    base = [bm.verts.new(b + u * su * s + w * sw * s) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    sn = 0.35 * s
    m = a + n * (0.9 * sn) + lay * L * 0.4
    mid = [bm.verts.new(m + u * su * s * 0.85 + n * sv * sn) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    t = a + n * L * 0.12 + lay * L
    tip = [bm.verts.new(t + u * su * s * 0.3 + n * sv * s * 0.1) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    keep_x(base + mid + tip)
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip[(j + 1) % 4], tip[j]])
    bm.faces.new(tip)


def slab(bm, a, n, up, w, h, t):
    """A chunky stone plate: a w x h box sunk 2.5 cm into the surface at a, standing t proud, top face 80 %."""
    n = Vector(n).normalized()
    u = Vector(up) - n * Vector(up).dot(n); u.normalize()
    r = u.cross(n)
    lo = [bm.verts.new(a - n * 0.025 + r * sr * w + u * su * h) for sr, su in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    hi = [bm.verts.new(a + n * t + r * sr * w * 0.8 + u * su * h * 0.8) for sr, su in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    keep_x(lo + hi)
    bm.faces.new(list(reversed(lo))); bm.faces.new(hi)
    for j in range(4):
        bm.faces.new([lo[j], lo[(j + 1) % 4], hi[(j + 1) % 4], hi[j]])


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def hit(tree, o, d):
    loc, nrm, _i, _d = tree.ray_cast(Vector(o), Vector(d).normalized(), 4.0)
    if loc is None:
        raise RuntimeError('no surface from %s along %s' % (o, d))
    return loc, (nrm if nrm.dot(Vector(d)) < 0 else -nrm)


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('stone', 'dark', 'light', 'moss')}, body_rule)
    tree = body_bvh(body)
    # eyes: small glowing lenses on the socket floors
    ec = eye_face_centre()
    c, n = hit(tree, (ec.x, -1.5, ec.z), (0, 1, 0))
    bm = bmesh.new()
    lens(bm, c, n, 0.022, 0.009)
    eye = object_from_bm('eye', bm)
    paint(eye, {'glow': PAL['glow']}, lambda c_, n_, i: 'glow')
    # stone plates: knee caps, forearm guard, knuckles, toes
    bm = bmesh.new()
    p_, n_ = hit(tree, (0.35, -1.5, 0.30), (0, 1, 0)); slab(bm, p_, n_, (0, 0, 1), 0.08, 0.07, 0.03)
    p_, n_ = hit(tree, (2.0, -0.03, 0.88), (-1, 0, 0)); slab(bm, p_, n_, (0, 0, 1), 0.12, 0.13, 0.035)
    p_, n_ = hit(tree, (0.87, -1.5, 0.38), (0, 1, 0)); slab(bm, p_, n_, (0, 0, 1), 0.12, 0.055, 0.04)   # fix2: one knuckle block
    p_, n_ = hit(tree, (0.22, -1.5, 1.36), (0, 1, 0)); slab(bm, p_, n_, (0, 0, 1), 0.15, 0.12, 0.03)   # fix pass: pec slab
    p_, n_ = hit(tree, (0.14, -1.5, 0.98), (0, 1, 0)); slab(bm, p_, n_, (0, 0, 1), 0.13, 0.08, 0.03)   # fix2: belly plate (sheet)
    p_, n_ = hit(tree, (0.22, 1.5, 1.42), (0, -1, 0)); slab(bm, p_, n_, (0, 0, 1), 0.17, 0.15, 0.03)   # fix2: upper back plates (sheet rear)
    p_, n_ = hit(tree, (0.14, 1.5, 1.02), (0, -1, 0)); slab(bm, p_, n_, (0, 0, 1), 0.13, 0.09, 0.03)   # fix2: lower back plate
    plates = object_from_bm('plates', bm)
    paint(plates, {'stone': PAL['stone']}, lambda c_, n_, i: 'stone')   # fix2: plates same grey, shape only
    bm = bmesh.new()                                    # fix pass: 3 square stone toes on the foot slab front
    for x in (0.30, 0.40, 0.50):
        p_, n_ = hit(tree, (x, -1.5, 0.035), (0, 1, 0)); slab(bm, p_, n_, (0, 0, 1), 0.042, 0.032, 0.05)
    toes = object_from_bm('toes', bm)
    paint(toes, {'dark': PAL['dark']}, lambda c_, n_, i: 'dark')
    return [eye, plates, toes]          # fix pass: the painted chest crack (a liner) is dropped                 # s4 r7: the moss clumps drift with the boulder skin in the swings; moss stays a colour zone


def shell_rigid(p):
    """s4 r2: every connected shell of a piece takes ONE weight set (its mean), so a clump moves as a block."""
    me = p.data
    adj = {v.index: set() for v in me.vertices}
    for e in me.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    seen = set()
    for s0 in adj:
        if s0 in seen:
            continue
        sh, st = [], [s0]
        seen.add(s0)
        while st:
            i = st.pop(); sh.append(i)
            for j in adj[i] - seen:
                seen.add(j); st.append(j)
        acc = {}
        for i in sh:
            for g in me.vertices[i].groups:
                acc[g.group] = acc.get(g.group, 0.0) + g.weight / len(sh)
        for g in p.vertex_groups:
            w = acc.get(g.index, 0.0)
            if w > 1e-4:
                g.add(sh, w, 'REPLACE')
            else:
                g.remove(sh)


def stage4(k, body, pieces):
    B = [('hips', (0, 0, 0.62), (0, 0, 0.90), None),
         ('spine', (0, 0, 0.90), (0, -0.02, 1.25), 'hips', True),
         ('chest', (0, -0.02, 1.25), (0, -0.10, 1.60), 'spine', True),
         ('neck', (0, -0.10, 1.60), (0, -0.22, 1.75), 'chest', True),
         ('head', (0, -0.22, 1.75), (0, -0.24, 2.01), 'neck', True),
         ('shoulder.L', (0.18, 0, 1.60), (0.58, 0, 1.66), 'chest'),
         ('upperarm.L', (0.58, 0, 1.66), (0.84, -0.01, 1.13), 'shoulder.L', True),
         ('forearm.L', (0.84, -0.01, 1.13), (0.88, -0.05, 0.62), 'upperarm.L', True),
         ('hand.L', (0.88, -0.05, 0.62), (0.86, -0.05, 0.24), 'forearm.L', True),
         ('thigh.L', (0.30, 0, 0.62), (0.35, 0, 0.32), 'hips'),
         ('shin.L', (0.35, 0, 0.32), (0.37, 0, 0.10), 'thigh.L', True),
         ('foot.L', (0.37, 0, 0.10), (0.40, -0.40, 0.03), 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)

    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0)},
                       24: {'head': (0, 0, 5)}, 36: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, -3)}, 48: {}})
    A, S = 20, 12
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 4)},
        9: {'shin.R': (-35, 0, 0), 'thigh.R': (5, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0), 'spine': (0, 0, -4)},
        25: {'shin.L': (-35, 0, 0), 'thigh.L': (5, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 4)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0, -0.025)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0, -0.025)},
             33: {'hips': (0, 0, 0)}})
    up = {'upperarm.L': (75, 0, 0), 'upperarm.R': (75, 0, 0), 'forearm.L': (25, 0, 0), 'forearm.R': (25, 0, 0)}
    clip(rig, 'attack', {
        1: {},
        12: dict(up, chest=(-8, 0, 0), head=(-5, 0, 0)),
        19: {'upperarm.L': (25, 0, 0), 'upperarm.R': (25, 0, 0), 'chest': (14, 0, 0), 'spine': (6, 0, 0), 'head': (4, 0, 0)},
        26: {'upperarm.L': (20, 0, 0), 'upperarm.R': (20, 0, 0), 'chest': (12, 0, 0), 'spine': (5, 0, 0)},
        36: {}},
        loc={1: {'hips': (0, 0, 0)}, 12: {'hips': (0, 0.03, 0)}, 19: {'hips': (0, -0.05, -0.04)}, 26: {'hips': (0, -0.05, -0.04)},
             36: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
