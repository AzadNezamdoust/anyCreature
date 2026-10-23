import os, sys, math, json, bisect
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# koi carp (t7x zoo): no legs, so the spine loft of 6-vertex half rings (caudal peduncle -> snout) IS the body.
# Every fin is a face region extruded off that loft: dorsal, anal and the caudal lobes from seam faces (the wall an
# extrusion leaves on x = 0 is removed and the mirror closes the fin), the caudal plate from the tail end cap,
# pectoral and pelvic fins from a lower-flank face. Rig: swim (move), idle, attack.
META = dict(creature='koi', model='opus', stage1_tris=(900, 2200), total_tris=(1100, 3000),
            closeups=[('head', (0.0, -0.29, 0.13), 0.14, 'hero'),
                      ('pectoral and pelvic fins', (0.09, -0.12, 0.05), 0.2, 'hero'),
                      ('dorsal fin', (0.0, 0.02, 0.23), 0.2, 'hero'),
                      ('caudal fin', (0.0, 0.27, 0.13), 0.2, 'az090')])

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T)
# poly pass 3: 10-vertex half rings. BODY from the sheet's front view: an egg, widest a little below the middle
# (h -0.28), the back rounding to the dorsal ridge, the belly round
BODY = [(0, 1), (0.38, 0.93), (0.66, 0.74), (0.86, 0.46), (0.98, 0.12), (1.0, -0.28), (0.9, -0.6), (0.68, -0.84),
        (0.36, -0.97), (0, -1)]


def resample(prof, splits):
    """Split each edge of a coarse profile into n collinear pieces: more vertices, same flat planes."""
    out = [prof[0]]
    for (a, b), n in zip(zip(prof, prof[1:]), splits):
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return out


# fix9 (dense kept): head and peduncle use the before3 6-vertex sections, resampled collinear to 10
# vertices so they still bridge to the dense body but keep their flat planes; the eye face (old edge 1) is unsplit
KEEL = resample([(0, 1), (0.6, 0.8), (1, 0.05), (0.6, -0.75), (0.3, -0.95), (0, -1)], (2, 2, 2, 2, 1))
HEAD = resample([(0, 1), (0.7, 0.6), (1, -0.3), (0.82, -0.7), (0.48, -0.93), (0, -1)], (2, 1, 2, 2, 2))  # eye face = vertices 2-3

# the loft, tail -> snout: (name, y, z bottom, z top, half-width W); z read off reference/side.png, W off top.png
# poly pass 3: 15 -> 23 stations, z and W re-read off the sheet trace (side.png columns, top.png rows; W x1.05)
SECS = [
    ('P0', 0.195, 0.091, 0.159, 0.014, KEEL),
    ('Pa', 0.180, 0.094, 0.1575, 0.016, KEEL),     # fix9: Pa/Pc on the P0-P1-P2 lines (no rib bands)
    ('P1', 0.165, 0.097, 0.156, 0.018, KEEL),
    ('Pc', 0.145, 0.0945, 0.1615, 0.0225, KEEL),
    ('P2', 0.125, 0.092, 0.167, 0.027, BODY),
    ('Pb', 0.105, 0.088, 0.174, 0.033, BODY),
    ('B0', 0.085, 0.082, 0.181, 0.039, BODY),
    ('Ba', 0.065, 0.075, 0.190, 0.047, BODY),
    ('B1', 0.045, 0.069, 0.199, 0.054, BODY),
    ('Bb', 0.022, 0.066, 0.207, 0.060, BODY),
    ('B2', 0.000, 0.063, 0.213, 0.065, BODY),
    ('B3', -0.050, 0.059, 0.220, 0.070, BODY),
    ('Bc', -0.073, 0.057, 0.222, 0.072, BODY),
    ('B4', -0.095, 0.056, 0.223, 0.073, BODY),
    ('B5', -0.150, 0.057, 0.222, 0.074, BODY),
    ('Bd', -0.180, 0.059, 0.218, 0.072, BODY),
    ('H0', -0.210, 0.063, 0.208, 0.069, BODY),
    ('H1', -0.260, 0.073, 0.193, 0.067, HEAD),     # fix9: before3 head stations, Ha on the H2-H3 line
    ('H2', -0.300, 0.083, 0.170, 0.052, HEAD),
    ('Ha', -0.3125, 0.0865, 0.161, 0.0445, HEAD),
    ('H3', -0.325, 0.090, 0.152, 0.037, HEAD),
    ('H4', -0.341, 0.097, 0.136, 0.026, HEAD),
    ('H5', -0.351, 0.104, 0.125, 0.014, HEAD),
]

# seam fins: base y -> the fin's outer-edge point (y, z) that base vertex reaches; levels (fraction, half thickness).
# s1 r5 (re-lock): three levels and 4-6 mm half thickness, so no fin wall or rim face is a needle (each face's
# width / length >= tan 6 deg, the kit's sliver line); stage-2 r1 found 18% slivers on 1.5-4.5 mm fins
DORSAL = [(-0.095, (0.0, 0.284)), (-0.05, (0.015, 0.262)), (0.0, (0.035, 0.236)), (0.045, (0.07, 0.220)),
          (0.09, (0.105, 0.204)), (0.125, (0.138, 0.186))]
DORSAL_LV = [(0.35, 0.0096), (0.7, 0.0083), (1.0, 0.0074)]  # fix2: x1.6, reads from front/rear
ANAL = [(0.085, (0.147, 0.061)), (0.125, (0.175, 0.070))]  # fix pass: swept back, tucked
ANAL_LV = [(0.5, 0.0045), (1.0, 0.004)]
UPPER = [(0.195, (0.29, 0.198)), (0.225, (0.325, 0.211)), (0.255, (0.35, 0.218))]
LOWER = [(0.195, (0.29, 0.057)), (0.225, (0.325, 0.044)), (0.255, (0.35, 0.037))]
LOBE_LV = [(0.35, 0.0075), (0.7, 0.007), (1.0, 0.0065)]  # fix2: thicker lobes
# caudal plate: (y, z bottom, z top, half thickness) of the two segments behind the tail cap; the notch end is
# 3.5 cm tall so its plate strips stay wider than needles
PLATE = [(0.225, 0.078, 0.175, 0.005), (0.255, 0.110, 0.145, 0.005)]
# paired fins: levels of (x, lead (y, z), trail (y, z), half thickness) and the blade normal (x, y, z)
# s1 r2: the pectoral chord drops from lead to trail, so the paddle shows its face from the front as in the ref;
# s1 r3: a broad paddle (chord 9 cm); s1 r5: three levels, the rim a short rounded end, uniform thickness
# fix pass (zoo reviews): pectorals swept back and down, pelvics laid flat along the belly, shorter
# fix2: paddles near-horizontal, broader, tips a little under the belly, above the pelvics (no legs on the floor)
PECTORAL = ([(0.118, (-0.205, 0.074), (-0.115, 0.058), 0.006), (0.156, (-0.172, 0.058), (-0.078, 0.043), 0.005),
             (0.176, (-0.130, 0.046), (-0.092, 0.040), 0.004)], (0.29, 0.41, 0.83))
PELVIC = ([(0.058, (-0.030, 0.056), (0.000, 0.052), 0.004), (0.062, (0.000, 0.048), (0.035, 0.046), 0.003)],
          (1.0, 0.0, 0.0))

# the skeleton (x >= 0 half; .L on +X)
J = dict(spine=(0.0, 0.04, 0.14), chest=(0.0, -0.08, 0.14), head=(0.0, -0.20, 0.138), nose=(0.0, -0.35, 0.115),
         tail1=(0.0, 0.13, 0.132), tail2=(0.0, 0.20, 0.127), tail3=(0.0, 0.33, 0.127),
         pec=(0.08, -0.18, 0.074), pectip=(0.17, -0.10, 0.042))


def sec_pts(y, zb, zt, W, prof):
    zc, T = (zb + zt) / 2, (zt - zb) / 2
    return [(fx * W, y, zc + fh * T) for fx, fh in prof]


def P(nm):
    for (n, y, zb, zt, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(y, zb, zt, W, p)]


SEC_Y = [s[1] for s in reversed(SECS)]          # snout -> tail, increasing y
SEC_ZB = [s[2] for s in reversed(SECS)]
SEC_ZT = [s[3] for s in reversed(SECS)]
SEC_W = [s[4] for s in reversed(SECS)]


def body_at(y):
    """(z bottom, z top, W) of the loft at y (linear between rings)."""
    y = min(max(y, SEC_Y[0]), SEC_Y[-1])
    j = min(max(bisect.bisect_right(SEC_Y, y) - 1, 0), len(SEC_Y) - 2)
    t = (y - SEC_Y[j]) / (SEC_Y[j + 1] - SEC_Y[j])
    L = lambda a: a[j] + (a[j + 1] - a[j]) * t
    return L(SEC_ZB), L(SEC_ZT), L(SEC_W)


def _interp(table, y):
    ys = [a for a, _ in table]
    j = min(max(bisect.bisect_right(ys, y) - 1, 0), len(ys) - 2)
    t = (y - ys[j]) / (ys[j + 1] - ys[j])
    (a0, b0), (a1, b1) = table[j][1], table[j + 1][1]
    return a0 + (a1 - a0) * t, b0 + (b1 - b0) * t


def grow_seam(bm, faces, tgt, levels):
    """Extrude a face region level by level. Each new vertex keeps its base vertex; at level (k, th) it sits k of
    the way from its base position to tgt(base) (y, z), on x = 0 if its base is on the seam, else at x = th.
    Walls an extrusion leaves on the mirror plane are removed, so the mirror closes the fin. Returns the last
    faces and the kept side walls of every level."""
    base = {v: v.co.copy() for f in faces for v in f.verts}
    roles = {v: v for v in base}
    walls = []
    for k, th in levels:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        wall = [f for f in r['sides'] if all(abs(v.co.x) < 1e-6 for v in f.verts)]
        if wall:
            bmesh.ops.delete(bm, geom=wall, context='FACES')
        for v, b in new.items():
            b0 = base[b]
            ty, tz = tgt(b0)
            v.co = Vector((0.0 if abs(b0.x) < 1e-6 else th, b0.y + (ty - b0.y) * k, b0.z + (tz - b0.z) * k))
        walls.append([f for f in r['sides'] if f.is_valid])
        faces, roles = r['faces'], new
    return faces, walls


def grow_side(bm, face, levels, nrm):
    """A paired fin from one lower-flank quad: roles front/rear (y) x upper/lower (z); each level is a blade
    section (x, lead (y, z), trail (y, z), half thickness) with the blade normal nrm."""
    n = Vector(nrm).normalized()
    vs = list(face.verts)
    ys = sorted(v.co.y for v in vs)
    ymid = (ys[1] + ys[2]) / 2
    zmid = sum(v.co.z for v in vs) / 4
    roles = {v: ('f' if v.co.y < ymid else 'r') + ('u' if v.co.z > zmid else 'l') for v in vs}
    faces = [face]
    for x, (yl, zl), (yt, zt), ht in levels:
        L, T = Vector((x, yl, zl)), Vector((x, yt, zt))
        fr, rr = L.lerp(T, 0.12), L.lerp(T, 0.94)
        tgt = {'fu': fr + n * ht, 'fl': fr - n * ht, 'ru': rr + n * ht, 'rl': rr - n * ht}
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, ro in new.items():
            v.co = Vector(tgt[ro])
        faces, roles = r['faces'], new
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {s[0]: i for i, s in enumerate(SECS)}
    rings = [ring(bm, sec_pts(y, zb, zt, W, p)) for (nm, y, zb, zt, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    tail = cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    sp = lambda nm, j: spans[idx[nm]][j]
    # dorsal: the top seam faces from P2 to B4 (y 0.125 .. -0.095), swept back to a high front tip
    grow_seam(bm, [sp(n, 0) for n in ('P2', 'Pb', 'B0', 'Ba', 'B1', 'Bb', 'B2', 'B3', 'Bc')], lambda b: _interp(DORSAL, b.y), DORSAL_LV)
    grow_seam(bm, [sp('P2', 8), sp('Pb', 8)], lambda b: _interp(ANAL, b.y), ANAL_LV)
    # caudal: a thin plate from the tail cap to the fork notch, then the two lobes from its top and bottom walls;
    # the plate's vertices are spread evenly over its height by their rank (top seam 1 ... bottom seam 0)
    segs = []
    faces = [tail]
    for y, zb, zt, th in PLATE:
        zs = sorted(v.co.z for v in faces[0].verts)
        rank = {round(z, 7): i / (len(zs) - 1) for i, z in enumerate(zs)}
        f = lambda b, y=y, zb=zb, zt=zt, rank=rank: (y, zb + rank[round(b.z, 7)] * (zt - zb))
        faces, walls = grow_seam(bm, faces, f, [(1.0, th)])
        segs.append(walls[0])
    mz = lambda f: sum(v.co.z for v in f.verts) / len(f.verts)
    top = [max(w, key=mz) for w in segs]
    bot = [min(w, key=mz) for w in segs]
    grow_seam(bm, top, lambda b: _interp(UPPER, b.y), LOBE_LV)
    grow_seam(bm, bot, lambda b: _interp(LOWER, b.y), LOBE_LV)
    grow_side(bm, sp('B5', 6), *PECTORAL)
    grow_side(bm, sp('B2', 6), *PELVIC)
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    """The upper-side head face (ring vertices 2-3, the before3 eye face) between H1 and H2: the eye socket."""
    H1, H2 = P('H1'), P('H2')
    return (H1[2] + H1[3] + H2[2] + H2[3]) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.02 and abs(c.y - ec0.y) < 0.025
                                        and abs(c.z - ec0.z) < 0.025)
    bm = edit(body)
    mid = lambda a, b: (a + b) / 2
    # joint rings: the tail joint (peduncle), the mid-body flex and the gill line behind the head
    for a, b, why in (('P1', 'Pc', 'tail joint: a ring in the peduncle span, where the caudal swings'),
                      ('B4', 'B5', 'body flex: a ring in the free span behind the pectoral girdle'),
                      ('H0', 'H1', 'gill line: a ring where the operculum ends, the head joint')):
        e = edge_near(bm, mid(P(a)[2], P(b)[2]))
        with k.topo(bm, 'loop', why):
            loopcut(bm, e, t=0.5)
    recalc_normals(bm)
    # the gill ring stands proud a little (operculum edge) and the crown over the eyes is one flat plane
    H2, Ha, H3, H4, H5 = (P(n) for n in ('H2', 'Ha', 'H3', 'H4', 'H5'))
    flatten([vert_near(bm, q) for H in (H2, Ha, H3, H4) for q in H[:3]])
    # snout: the end cap slants down-forward to a blunt mouth pad
    move([vert_near(bm, q) for q in H5[:3]], (0.0, 0.004, -0.002))
    move([vert_near(bm, q) for q in H5[7:]], (0.0, 0.003, 0.0))
    # a blunt koi snout, not a shark point: the last two rings wider
    scale([vert_near(bm, q) for q in H5], (1.5, 1.0, 1.0), pivot=(0.0, 0.0, 0.0))
    scale([vert_near(bm, q) for q in H4], (1.15, 1.0, 1.0), pivot=(0.0, 0.0, 0.0))
    recalc_normals(bm)
    f = face_near(bm, ec0, n=(1, 0, 0.2))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the upper-side head face between H1 and H2'):
        inner = inset(bm, [f], 0.5, 0.0)
    move(list(inner[0].verts), -fn * 0.004)
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


# ---- colour: white ground, red-orange patches (head cap, shoulder, rear flank), one black patch, orange fin roots
PAL = {'white': '#f2efea', 'orange': '#e2501c', 'black': '#1d1d21', 'iris': '#6b4630'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    zb, zt, W = body_at(y)
    zc, T = (zb + zt) / 2, max((zt - zb) / 2, 1e-4)
    h = (z - zc) / T
    if y > 0.198:
        return 'orange' if y < 0.25 else 'white'                       # caudal: orange root, white lobes
    if z > zt + 0.003 and x < 0.012:
        return 'orange' if (y < -0.03 and z < 0.255) else 'white'      # dorsal: orange front root
    if y < -0.085 and x > W + 0.003:
        return 'orange' if x < 0.125 else 'white'                     # pectoral: orange root band
    if z < zb - 0.003 and x > 0.02:
        return 'orange' if z > 0.051 else 'white'                    # pelvic
    if z < zb - 0.003:
        return 'orange' if z > 0.075 else 'white'                     # anal
    if y < -0.33:
        return 'white'                                                 # snout and lips
    if y < -0.20:
        return 'orange' if h > 0.2 else 'white'                        # head cap
    if y < -0.175:
        return 'orange' if h > 0.5 else 'white'
    if y < -0.075:
        return 'orange' if h > 0.3 else 'white'                        # shoulder patch (fix2: upper rows only, not a band)
    if y < 0.015:
        return 'black' if h > 0.45 else 'white'                        # the black (sumi) patch
    if y < 0.15:
        return 'orange' if (h > 0.3 and y < 0.10) else 'white'  # rear patch (fix2: upper rows, ends before the peduncle)
    return 'white'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A small low-poly eye: back cone, iris ring, pupil fan."""
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


def barbel(bm, rows):
    """A tapered square barbel: rows of (x, y, z, half size), root sunk in the lip."""
    # detail pass r17: the square section is built PERPENDICULAR to the barbel axis (r15/r16: a level square on a
    # barbel running down-forward was a thin sheared slice, t 3-4 mm)
    p0, p1 = Vector(rows[0][:3]), Vector(rows[-1][:3])
    d = (p1 - p0).normalized()
    u = d.cross(Vector((1, 0, 0))).normalized()
    w = d.cross(u).normalized()
    R = [[bm.verts.new(Vector((x, y, z)) + (u * sx + w * sy) * s) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
         for x, y, z, s in rows]
    bm.faces.new(R[0])
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(list(reversed(R[-1])))


def stage3(k, body):
    paint(body, PAL, body_rule)
    ec = eye_face_centre()
    bmb = edit(body)
    f = face_near(bmb, ec + Vector((-0.004, 0, 0)), n=(1, 0, 0.2))
    c, n = f.calc_center_median().copy(), f.normal.copy()
    n = n if n.x > 0 else -n
    bmb.free()
    bm = bmesh.new()
    lens(bm, c, n, 0.0085, 0.005)
    eye = object_from_bm('eye', bm)
    paint(eye, {'iris': PAL['iris'], 'black': PAL['black']},
          lambda c_, n_, i: 'black' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.0035 and n_.dot(n) > 0.5 else 'iris')
    # barbels: one pair at the mouth corners, hanging down and a little forward
    bm = bmesh.new()
    barbel(bm, [(0.020, -0.338, 0.103, 0.0046), (0.022, -0.348, 0.095, 0.0039)])  # detail pass 10-23: stubby + chunky (tier-1 floor 5.9 mm; was t 2.2 mm, r15 3.2 mm)
    bar = object_from_bm('barbels', bm)
    paint(bar, {'white': PAL['white']}, lambda c_, n_, i: 'white')
    return [eye, bar]


SWIM = 0.25


def stage4(k, body, pieces):
    B = [('spine', J['spine'], J['chest'], None),
         ('chest', J['chest'], J['head'], 'spine', True),
         ('head', J['head'], J['nose'], 'chest', True),
         ('tail1', J['spine'], J['tail1'], 'spine'),
         ('tail2', J['tail1'], J['tail2'], 'tail1', True),
         ('tail3', J['tail2'], J['tail3'], 'tail2', True),
         ('pec.L', J['pec'], J['pectip'], 'chest')]
    rig = armature(B)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            eb.align_roll(Vector((0, 0, 1)))        # local Z up: rot Z = sideways (yaw), rot X = pitch
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, bone='head')
    # idle: hover, a slow tail sway and a pectoral paddle
    clip(rig, 'idle', {1: {}, 12: {'tail2': (0, 0, 5), 'tail3': (0, 0, 8), 'pec.L': (12, 0, 0), 'pec.R': (12, 0, 0)},
                       24: {'head': (0, 0, 1.5), 'pec.L': (-8, 0, 0), 'pec.R': (-8, 0, 0)},
                       36: {'tail2': (0, 0, -5), 'tail3': (0, 0, -8), 'pec.L': (12, 0, 0), 'pec.R': (12, 0, 0)}, 48: {}})
    # move (swim): a sideways wave running from the head to the caudal, fins tucked
    chain = [('head', 3.0, -1), ('chest', 4.0, -1), ('tail1', 9.0, 1), ('tail2', 14.0, 1), ('tail3', 18.0, 1)]
    keys = {}
    for f in (1, 7, 13, 19, 25):
        ph = 2 * math.pi * (f - 1) / 24
        d = {b: (0, 0, round(A * sg * math.sin(ph - j * 0.9), 2)) for j, (b, A, sg) in enumerate(chain)}
        d['pec.L'] = (-15, 0, 0); d['pec.R'] = (-15, 0, 0)
        keys[f] = d
    clip(rig, 'move', keys)
    # attack: coil into a C, then dart forward with the head snapping down to bite, and settle
    clip(rig, 'attack', {
        1: {},
        9: {'chest': (0, 0, 10), 'head': (0, 0, 8), 'tail1': (0, 0, -12), 'tail2': (0, 0, -16), 'tail3': (0, 0, -18),
            'pec.L': (20, 0, 0), 'pec.R': (20, 0, 0)},
        15: {'chest': (0, 0, -4), 'head': (8, 0, -2), 'tail1': (0, 0, 10), 'tail2': (0, 0, 16), 'tail3': (0, 0, 20),
             'pec.L': (-20, 0, 0), 'pec.R': (-20, 0, 0)},
        20: {'head': (6, 0, 0), 'tail2': (0, 0, -6), 'tail3': (0, 0, -8)},
        32: {}},
        loc={1: {'spine': (0, 0, 0)}, 9: {'spine': (0, -0.02, 0)}, 15: {'spine': (0, 0.09, 0)},
             20: {'spine': (0, 0.10, 0)}, 32: {'spine': (0, 0, 0)}})
    # weakfix 2026-10-23: the koi swims: the rig (body + pieces parented to it) rides SWIM above the floor
    # (the fins were 3.7 cm off z 0)
    rig.location.z += SWIM
    bpy.context.view_layer.update()
    return rig


run(META, stage1, stage2, stage3, stage4)
