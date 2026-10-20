import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# great white shark (t7x zoo): no legs, so the spine loft of 6-vertex half rings (caudal fork -> snout) IS the
# body; every fin is a face extruded off that loft. Fins on the mirror seam (dorsal, second dorsal, anal, both
# caudal lobes) are grown from a seam face, the wall each extrusion leaves on x = 0 is removed, and the mirror
# closes them; paired fins (pectoral, pelvic) are grown from a lower-flank face.
META = dict(creature='shark', model='opus', stage1_tris=(1000, 2200), total_tris=(1400, 4500),
            closeups=[('head', (0.0, -1.12, 0.47), 0.26, 'hero'),
                      ('pectoral fin', (0.40, -0.45, 0.21), 0.3, 'hero'),
                      ('dorsal fin', (0.0, -0.18, 0.84), 0.3, 'hero'),
                      ('caudal fin', (0.0, 1.05, 0.45), 0.45, 'hero')])

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = [(0, 1), (0.74, 0.8), (1, 0.15), (0.94, -0.42), (0.6, -0.86), (0, -1)]     # s1 r2: rounder back
HEAD = [(0, 1), (0.72, 0.88), (1, 0.15), (0.9, -0.45), (0.6, -0.9), (0, -1)]
KEEL = [(0, 1), (0.5, 0.8), (1, 0.05), (0.5, -0.75), (0.28, -0.95), (0, -1)]     # caudal peduncle, lateral keel


def dense(prof, spans=(0, 1, 2, 4), sharp=()):
    """Density pass 3: 6 -> 10 (then 12) vertices per half ring. A point goes into spans 0, 1, 2 and 4 (span 3, the
    paired-fin root face, stays whole) at the Catmull-Rom midpoint of the closed ring (the half mirrored across
    the seam), so the cross-section rounds out instead of keeping the hexagon's flats. Spans in `sharp` (the
    keel) get the straight midpoint so the keel edge stays crisp."""
    n = len(prof)
    loop = [(-x, h) for x, h in reversed(prof[1:-1])]
    ext = lambda i: prof[i] if 0 <= i < n else ((-prof[-i][0], prof[-i][1]) if i < 0 else (-prof[2 * n - 2 - i][0], prof[2 * n - 2 - i][1]))
    out = []
    for i, p in enumerate(prof):
        out.append(p)
        if i in spans:
            a, b, c, d = ext(i - 1), ext(i), ext(i + 1), ext(i + 2)
            if i in sharp:
                m = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)
            else:
                m = tuple((-a[j] + 9 * b[j] + 9 * c[j] - d[j]) / 16 for j in range(2))
            out.append((round(m[0], 4), round(m[1], 4)))
    return out


KEEL6 = KEEL                                       # r8: the thin peduncle rings stay 6 (12 there were needles)
BODY, HEAD, KEEL = dense(BODY), dense(HEAD), dense(KEEL, sharp=(1, 2))
# r6/r10: two more points over the shoulder of the back (the dome of the sheet front); not at the widest
# point, where the long fin-root spans turned them into needles
BODY, HEAD, KEEL = dense(BODY, (1, 2)), dense(HEAD, (1, 2)), dense(KEEL, (1, 2))
# old 6-ring index -> new 12-ring index: 0->0, 1->3, 2->6, 3->8, 4->9, 5->11; eye face 5-6

# the loft, tail -> snout: (name, y, z bottom, z top, half-width W); z read off reference/side.png, W from the
# front and top views
SECS = [
    ('T0', 1.05, 0.39, 0.47, 0.02, KEEL6),
    ('T1', 0.88, 0.382, 0.487, 0.04, KEEL6),        # fix pass: smooth peduncle (no kink)
    ('T2', 0.78, 0.38, 0.486, 0.05, KEEL6),
    ('T2b', 0.725, 0.376, 0.501, 0.06, KEEL),       # pass 3 stations: z off the traced side line, W off the top view
    ('T3', 0.67, 0.37, 0.514, 0.07, BODY),
    ('T4', 0.55, 0.348, 0.547, 0.10, BODY),
    ('T4b', 0.475, 0.334, 0.565, 0.12, BODY),
    ('B0', 0.40, 0.32, 0.583, 0.14, BODY),
    ('B1', 0.28, 0.29, 0.614, 0.165, BODY),
    ('B1b', 0.21, 0.272, 0.630, 0.178, BODY),
    ('B2', 0.14, 0.258, 0.647, 0.19, BODY),
    ('B2b', 0.07, 0.243, 0.662, 0.208, BODY),
    ('B3', 0.0, 0.232, 0.68, 0.225, BODY),
    ('M0', -0.36, 0.205, 0.73, 0.25, BODY),
    ('C0', -0.68, 0.217, 0.69, 0.24, BODY),
    ('C0b', -0.74, 0.225, 0.682, 0.233, BODY),      # gill region
    ('G0', -0.80, 0.235, 0.673, 0.225, HEAD),
    ('G0b', -0.86, 0.246, 0.659, 0.218, HEAD),      # head-to-body transition
    ('H0', -0.92, 0.26, 0.645, 0.21, HEAD),
    ('H0b', -0.975, 0.277, 0.631, 0.20, HEAD),
    ('H1', -1.03, 0.30, 0.62, 0.19, HEAD),
    ('H1b', -1.08, 0.321, 0.603, 0.177, HEAD),
    ('H2', -1.13, 0.345, 0.585, 0.16, HEAD),
    ('H2b', -1.175, 0.374, 0.567, 0.138, HEAD),     # the eye span
    ('H3', -1.22, 0.395, 0.55, 0.11, HEAD),
    ('H3b', -1.255, 0.421, 0.536, 0.086, HEAD),     # snout taper
    ('H4', -1.29, 0.44, 0.52, 0.06, HEAD),
    ('H5', -1.318, 0.465, 0.505, 0.022, HEAD),
]

# seam fins: levels of (lead (y, z), trail (y, z), half thickness); lead = the front edge of the fin
DORSAL = [((-0.33, 0.78), (0.0, 0.73), 0.03), ((-0.205, 0.87), (-0.045, 0.85), 0.02), ((-0.08, 0.99), (-0.06, 0.985), 0.005)]
DORSAL2 = [((0.565, 0.565), (0.665, 0.535), 0.015), ((0.625, 0.588), (0.66, 0.58), 0.005)]
ANAL = [((0.57, 0.335), (0.665, 0.355), 0.014), ((0.635, 0.30), (0.66, 0.305), 0.005)]
UPPER = [((1.03, 0.665), (1.16, 0.58), 0.014), ((1.19, 0.785), (1.245, 0.71), 0.009), ((1.30, 0.835), (1.315, 0.825), 0.003)]
LOWER = [((0.98, 0.20), (1.095, 0.28), 0.012), ((1.12, 0.07), (1.165, 0.115), 0.007), ((1.195, 0.03), (1.21, 0.035), 0.003)]   # fix pass: longer lower lobe
# paired fins: levels of (x, z, lead y, trail y, half thickness) and the blade normal (x, z)
PECTORAL = ([(0.21, 0.30, -0.68, -0.34, 0.036), (0.40, 0.21, -0.47, -0.25, 0.018), (0.60, 0.12, -0.24, -0.18, 0.005)],   # fix2: root up, ~25 deg below horizontal (sheet front)
            (0.42, 0.91))
PELVIC = ([(0.15, 0.25, 0.30, 0.41, 0.02), (0.18, 0.21, 0.32, 0.38, 0.006)], (0.93, 0.36))

# s2 r2: blunt fin tips and thicker pectoral/pelvic edges (stage-2 vertex moves; the stage-1 tables stay locked)
# s2 r3: the caudal lobes, anal fin and the tips a step thicker again (slivers 2.6 %, at the caudal root)
BLUNT = dict(DORSAL={2: ((-0.095, 0.985), (-0.045, 0.975), 0.011)},
             ANAL={1: ((0.635, 0.30), (0.66, 0.305), 0.008)},
             UPPER={0: ((1.03, 0.665), (1.16, 0.58), 0.026), 1: ((1.19, 0.785), (1.245, 0.71), 0.016),
                    2: ((1.285, 0.84), (1.322, 0.815), 0.007)},
             LOWER={0: ((0.98, 0.20), (1.095, 0.28), 0.024), 1: ((1.12, 0.07), (1.165, 0.115), 0.014),
                    2: ((1.18, 0.035), (1.215, 0.05), 0.008)},
             PECTORAL={1: (0.40, 0.21, -0.47, -0.25, 0.024), 2: (0.595, 0.125, -0.26, -0.17, 0.018)},
             PELVIC={0: (0.15, 0.25, 0.30, 0.41, 0.025), 1: (0.18, 0.21, 0.32, 0.38, 0.01)})

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    root=(0.0, 0.05, 0.46), chest=(0.0, -0.40, 0.47), head=(0.0, -0.85, 0.46), nose=(0.0, -1.30, 0.48),
    tail0=(0.0, 0.40, 0.45), tail1=(0.0, 0.70, 0.44), tail2=(0.0, 0.95, 0.43), tail3=(0.0, 1.25, 0.60),
    pec=(0.20, -0.50, 0.30), pectip=(0.59, -0.21, 0.12),
)


def sec_pts(y, zb, zt, W, prof):
    zc, T = (zb + zt) / 2, (zt - zb) / 2
    return [(fx * W, y, zc + fh * T) for fx, fh in prof]


def P(nm):
    for (n, y, zb, zt, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(y, zb, zt, W, p)]


def S(nm):
    return next(s for s in SECS if s[0] == nm)


def grow_fin(bm, face, place):
    """Extrude one face level by level; place(level, role) gives each new vertex its position. A vertex's
    role is fixed by the base face (front/rear by y, seam/outer or upper/lower). Walls an extrusion leaves
    on the mirror plane are removed, so the mirror closes the fin."""
    vs = list(face.verts)
    ys = sorted(v.co.y for v in vs)
    ymid = (ys[1] + ys[2]) / 2
    zmid = sum(v.co.z for v in vs) / 4
    roles = {}
    for v in vs:
        fb = 'f' if v.co.y < ymid else 'r'
        if any(abs(w.co.x) < 1e-6 for w in vs):
            roles[v] = fb + ('s' if abs(v.co.x) < 1e-6 else 'o')
        else:
            roles[v] = fb + ('u' if v.co.z > zmid else 'l')
    faces = [face]
    lev = 0
    while True:
        tgt = place(lev)
        if tgt is None:
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
            v.co = Vector(tgt[ro])
        faces, roles = r['faces'], new
        lev += 1
    return faces


def seam_place(levels):
    def f(i):
        if i >= len(levels):
            return None
        (yl, zl), (yt, zt), t = levels[i]
        L, T = Vector((0, yl, zl)), Vector((0, yt, zt))
        a, b = L.lerp(T, 0.3), L.lerp(T, 0.65)
        return {'fs': L, 'rs': T, 'fo': Vector((t, a.y, a.z)), 'ro': Vector((t, b.y, b.z))}
    return f


def side_place(levels, nrm):
    n = Vector((nrm[0], 0.0, nrm[1])).normalized()

    def f(i):
        if i >= len(levels):
            return None
        x, z, yl, yt, ht = levels[i]
        c = yt - yl
        fr, rr = Vector((x, yl + 0.12 * c, z)), Vector((x, yt - 0.06 * c, z))
        return {'fu': fr + n * ht, 'fl': fr - n * ht, 'ru': rr + n * ht * 0.6, 'rl': rr - n * ht * 0.6}
    return f


def bridge_half(bm, a, b):
    """A 6-vertex half ring (a) onto a 12-vertex one (b): each old span becomes a quad, or one n-gon over the
    points the dense ring put into it (old index -> new: 0, 3, 6, 8, 9, 11)."""
    m = [0, 3, 6, 8, 9, 11]
    return [bm.faces.new([a[i], a[i + 1]] + [b[j] for j in range(m[i + 1], m[i] - 1, -1)]) for i in range(len(a) - 1)]


def stage1(k):
    bm = bmesh.new()
    idx = {s[0]: i for i, s in enumerate(SECS)}
    rings = [ring(bm, sec_pts(y, zb, zt, W, p)) for (nm, y, zb, zt, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) if len(rings[i]) == len(rings[i + 1]) else bridge_half(bm, rings[i], rings[i + 1])
             for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    sp = lambda nm, j: spans[idx[nm]][j]
    grow_fin(bm, sp('B3', 0), seam_place(DORSAL))
    grow_fin(bm, sp('T3', 0), seam_place(DORSAL2))
    grow_fin(bm, sp('T3', 10), seam_place(ANAL))
    grow_fin(bm, sp('T0', 0), seam_place(UPPER))
    grow_fin(bm, sp('T0', 4), seam_place(LOWER))
    grow_fin(bm, sp('M0', 8), side_place(*PECTORAL))
    grow_fin(bm, sp('B0', 8), side_place(*PELVIC))
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    """Centre of the H2-H2b upper-side face (ring vertices 5-6): the eye socket (ref eye at y -1.15, z 0.51)."""
    A, B = P('H2'), P('H2b')
    return (A[5] + A[6] + B[5] + B[6]) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.04
                                        and abs(c.z - ec0.z) < 0.04)
    bm = edit(body)
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    # flex rings along the swim chain, each in a span no fin grows from
    for a, b, why in (('T1', 'T2', 'peduncle: the caudal stroke bends here'),
                      ('B1b', 'B2', 'mid body: the second bend of the swim wave'),
                      ('C0', 'C0b', 'gill region: the head yaw bends behind the head')):
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, mid(P(a)[2], P(b)[2])), t=0.5)
    # pectoral root ring: the fin flaps at the root, not across the flank
    L0, L1 = side_place(*PECTORAL)(0), side_place(*PECTORAL)(1)
    with k.topo(bm, 'loop', 'pectoral root: a ring between the root and mid sections so the fin flaps'):
        loopcut(bm, edge_near(bm, mid(L0['fu'], L1['fu'])), t=0.5)
    # eye socket: a loop inside the eye face, pushed in under a brow corner
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face'):
        inner = inset(bm, [f], 0.36, 0.0)
    move(list(inner[0].verts), -fn * 0.01)
    # s2 r2: blunt the fin tips and thicken the paired-fin edges (needle triangles, 5.8 % slivers in r1)
    for nm, tab in BLUNT.items():
        if nm in ('PECTORAL', 'PELVIC'):
            lv, nrm = globals()[nm]
            old, new = side_place(lv, nrm), side_place([tab.get(i, l) for i, l in enumerate(lv)], nrm)
        else:
            lv = globals()[nm]
            old, new = seam_place(lv), seam_place([tab.get(i, l) for i, l in enumerate(lv)])
        for i in tab:
            o, n_ = old(i), new(i)
            for ro in o:
                vert_near(bm, o[ro]).co = n_[ro]
    # s2 r3: the thin caudal root rings wider (T0 x2, T1 x1.4): the keel, and no needle faces at the fork
    for nm, f_ in (('T0', 2.0), ('T1', 1.4)):
        scale([vert_near(bm, q) for q in P(nm)], (f_, 1.0, 1.0), pivot=(0.0, 0.0, 0.0))
    H1, H1b, H2, H2b, H3, H3b, H4 = (P(n_) for n_ in ('H1', 'H1b', 'H2', 'H2b', 'H3', 'H3b', 'H4'))
    move([vert_near(bm, H2[5])], (0.008, 0.0, 0.006))          # brow corner over the eye, out and up
    # deliberate snout planes: one flat bridge and one flat underside (the ref's conical snout, flat below)
    flatten([vert_near(bm, R_[j]) for R_ in (H2, H2b, H3, H3b, H4) for j in (0, 1, 2, 3)])
    flatten([vert_near(bm, R_[j]) for R_ in (H1, H1b, H2, H2b, H3) for j in (9, 10, 11)])
    commit(body, bm)
    bm.free()


# colours picked off the reference sheet: slate back, white belly, darker fins, black eye
PAL = {'back': '#76818c', 'belly': '#e8e6e2', 'fin': '#545d66', 'tip': '#2e3338', 'eye': '#0d0d0f'}


def zline(y):
    """The counter-shading border: low behind the pectoral, high on the head (the ref's white jaw and cheek)."""
    pts = [(-1.4, 0.50), (-1.0, 0.47), (-0.7, 0.45), (-0.3, 0.45), (0.3, 0.43), (0.7, 0.42), (1.0, 0.41)]   # s3 r3: up to the mid flank, as the ref
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return 0.4


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y > 0.86:
        return 'fin'                                    # caudal fin and its root
    if x > 0.24 and z < 0.3 and -0.75 < y < -0.05:               # pectoral: dark tip, white under, slate top
        return 'tip' if x > 0.5 else ('belly' if n.z < -0.3 else 'fin')
    if z > 0.76 or (0.53 < y < 0.70 and z > 0.53):
        return 'fin'                                    # dorsal and second dorsal
    if z < 0.33 and 0.5 < y < 0.7 and x < 0.03:
        return 'fin'                                    # anal fin
    if 0.27 < y < 0.43 and z < 0.27 and x > 0.1:
        return 'fin' if n.z > -0.2 else 'belly'         # pelvic fins
    if n.z < -0.25 or (z < zline(y) and n.z < 0.5):
        return 'belly'                                  # the white underside, up to the lateral line
    return 'back'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A small low-poly lens eye: back cone, ring, front fan."""
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


def slit(bm, p, n, h, w, d):
    """A gill slit: a thin plate standing in the flank (rooted d deep, 10 mm proud), h tall, leaning back."""
    n = Vector(n).normalized()
    up = Vector((0, 0.25, 1)).normalized()
    up = (up - n * up.dot(n)).normalized()
    side = up.cross(n).normalized()
    out_, in_ = p + n * 0.008, p - n * d             # fix pass: shallower (8 mm proud; 5 mm z-fights)
    rows = []
    for o, s in ((in_, 1.0), (out_, 0.8)):
        rows.append([bm.verts.new(o + up * su * h * s * 0.5 + side * sw * w * 0.5)
                     for su, sw in ((-1, -1), (-1, 1), (1, 1), (1, -1))])
    bm.faces.new(list(reversed(rows[0])))
    for j in range(4):
        bm.faces.new([rows[0][j], rows[0][(j + 1) % 4], rows[1][(j + 1) % 4], rows[1][j]])
    bm.faces.new(rows[1])


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def stage3(k, body):
    paint(body, PAL, body_rule)
    tree = body_bvh(body)
    # eye: a small black lens proud of the socket floor
    c, n, _i, _d = tree.find_nearest(eye_face_centre() - Vector((0.012, 0, 0)))
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.016, 0.008)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, lambda c_, n_, i: 'eye')
    # five gill slits in front of the pectoral, the rear ones taller (ref side: y -0.80 .. -0.63)
    bm = bmesh.new()
    for j, y in enumerate((-0.80, -0.765, -0.73, -0.695, -0.66)):
        hit, hn, _i, _d = tree.ray_cast(Vector((0.6, y, 0.43)), Vector((-1, 0, 0)), 1.0)
        slit(bm, hit, hn, 0.09 + 0.01 * j, 0.02, 0.015)   # s3 r2: wider, prouder slits (r1 needles + z-fight)
    gills = object_from_bm('gills', bm)
    paint(gills, {'fin': PAL['fin']}, lambda c_, n_, i: 'fin')   # fix pass: slate grooves, not black decals
    return [eye, gills]


def stage4(k, body, pieces):
    B = [('root', J['root'], J['chest'], None),
         ('chest', J['chest'], J['head'], 'root', True),
         ('head', J['head'], J['nose'], 'chest', True),
         ('tail0', J['root'], J['tail0'], 'root'),
         ('tail1', J['tail0'], J['tail1'], 'tail0', True),
         ('tail2', J['tail1'], J['tail2'], 'tail1', True),
         ('tail3', J['tail2'], J['tail3'], 'tail2', True),
         ('fin.L', J['pec'], J['pectip'], 'chest')]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: a slow glide, a gentle tail wave and the pectorals trimming
    clip(rig, 'idle', {1: {}, 12: {'tail1': (0, 0, 5), 'tail2': (0, 0, 7), 'tail3': (0, 0, 4), 'head': (0, 0, -2), 'fin.L': (0, 0, 4)},
                       24: {'tail1': (0, 0, 0), 'tail2': (0, 0, 0), 'tail3': (0, 0, 0)},
                       36: {'tail1': (0, 0, -5), 'tail2': (0, 0, -7), 'tail3': (0, 0, -4), 'head': (0, 0, 2), 'fin.L': (0, 0, -4)},
                       48: {}})
    # move (swim): a travelling wave head -> caudal, the tail beating, the head counter-yawing
    W = lambda a: {'chest': (0, 0, -3 * a), 'head': (0, 0, -4 * a), 'tail0': (0, 0, 5 * a), 'tail1': (0, 0, 10 * a),
                   'tail2': (0, 0, 14 * a), 'tail3': (0, 0, 16 * a)}
    lag = lambda b: {'tail0': (0, 0, 0), 'tail1': (0, 0, 0), 'tail2': (0, 0, 14 * b), 'tail3': (0, 0, 16 * b),
                     'chest': (0, 0, 0), 'head': (0, 0, 0)}
    clip(rig, 'move', {1: W(1), 7: lag(1), 13: W(-1), 19: lag(-1), 25: W(1)})
    # attack: coil the tail, lunge forward with the head lifting, then a head shake
    clip(rig, 'attack', {
        1: {},
        8: {'tail1': (0, 0, 14), 'tail2': (0, 0, 18), 'tail3': (0, 0, 16), 'head': (0, 0, -6), 'chest': (0, 0, -4)},
        14: {'tail1': (0, 0, -16), 'tail2': (0, 0, -20), 'tail3': (0, 0, -18), 'head': (12, 0, 0), 'chest': (5, 0, 0),
             'fin.L': (0, 0, -10)},
        20: {'head': (12, 0, 10), 'chest': (5, 0, 6), 'tail2': (0, 0, 8)},
        24: {'head': (10, 0, -10), 'chest': (4, 0, -6), 'tail2': (0, 0, -8)},
        32: {}},
        loc={1: {'root': (0, 0, 0)}, 8: {'root': (0, 0.04, 0)}, 14: {'root': (0, -0.18, 0)}, 20: {'root': (0, -0.22, 0)},
             24: {'root': (0, -0.2, 0)}, 32: {'root': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
