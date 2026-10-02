import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'kit')))
from bmkit import *
from mathutils.bvhtree import BVHTree

META = dict(creature='owl', model='opus',
            keep_valleys=lambda c: 0.44 < c.z < 0.56 and c.y < -0.15)   # the dished face disc and eye sockets dent in

# the skeleton the model is built on (left side; .R mirrors)
J = dict(
    root=(0.0, 0.02, 0.10), spine=(0.0, -0.02, 0.25), chest=(0.0, -0.04, 0.39),
    head=(0.0, -0.07, 0.43), crown=(0.0, -0.08, 0.61),
    tail0=(0.0, 0.10, 0.13), tail1=(0.0, 0.21, 0.075),
    hipL=(0.057, -0.025, 0.09), ankleL=(0.057, -0.025, 0.028), toeL=(0.057, -0.11, 0.01),
    shoulderL=(0.165, -0.05, 0.37), wingtipL=(0.13, 0.17, 0.12),
)
EPS = 1e-6

# section shapes: (fx, fy) per point; x = fx*w, y = lerp(yf, yb, fy); p0 front seam, p6 back seam
BODY = [(0, 0), (0.50, 0.05), (0.86, 0.22), (1.0, 0.46), (0.90, 0.72), (0.50, 0.94), (0, 1)]
HEAD = [(0, 0), (0.50, 0.03), (0.88, 0.18), (1.0, 0.45), (0.88, 0.72), (0.48, 0.93), (0, 1)]

# levels: (z, y_front, y_back, half_width, shape)
LEVELS = [
    (0.085, -0.050, 0.060, 0.065, BODY),   # Lb  belly bottom (capped)
    (0.115, -0.075, 0.100, 0.110, BODY),   # L0  legs + tail root
    (0.165, -0.135, 0.140, 0.135, BODY),   # L1
    (0.205, -0.160, 0.140, 0.146, BODY),   # L1b
    (0.255, -0.178, 0.130, 0.152, BODY),   # L2  belly
    (0.330, -0.188, 0.100, 0.155, BODY),   # L3  chest; wing root below L4
    (0.395, -0.172, 0.065, 0.140, BODY),   # L4  neck notch / shoulder
    (0.435, -0.186, 0.045, 0.130, HEAD),   # L5  chin, face disc bottom
    (0.480, -0.200, 0.030, 0.133, HEAD),   # L6  eye low
    (0.525, -0.200, 0.012, 0.130, HEAD),   # L6b eye high / brow
    (0.555, -0.172, -0.004, 0.118, HEAD),  # L7  crown, tuft root
    (0.590, -0.136, -0.030, 0.086, HEAD),  # L8  dome
    (0.612, -0.100, -0.056, 0.042, HEAD),  # L9  top (capped)
]


def section(z, yf, yb, w, shape):
    return [(fx * w, yf + (yb - yf) * fy, z) for fx, fy in shape]


def ext(bm, faces, fn):
    r = extrude(bm, faces)
    for v in r['verts']:
        v.co = Vector(fn(v.co.copy()))
    return r


def split_place(verts, key_a, key_b, table):
    """Sort verts into groups by key_a (ascending), each group by key_b; place from table[group][i]."""
    vs = sorted(verts, key=key_a)
    n = len(table[0])
    for g, pts in enumerate(table):
        grp = sorted(vs[g * n:(g + 1) * n], key=key_b)
        for v, p in zip(grp, pts):
            v.co = Vector(p)


def map_place(verts, src, dst):
    """Each new vert (still where the previous row was) goes to the dst point of its nearest src point."""
    for v in verts:
        i = min(range(len(src)), key=lambda j: (v.co - Vector(src[j])).length)
        v.co = Vector(dst[i])


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, section(*L)) for L in LEVELS]
    bands = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0])
    cap(bm, rings[-1])

    # --- legs: from the belly-bottom side face (band Lb-L0, p2-p3), straight down to the toes
    hx = J['hipL'][0]; hy = J['hipL'][1]
    r = extrude(bm, [bands[0][1]])
    split_place(r['verts'], lambda v: v.co.x, lambda v: v.co.y, [
        [(hx - 0.024, hy - 0.034, 0.060), (hx - 0.024, hy + 0.032, 0.060)],
        [(hx + 0.024, hy - 0.034, 0.060), (hx + 0.024, hy + 0.032, 0.060)]])
    r = extrude(bm, r['faces'])
    split_place(r['verts'], lambda v: v.co.x, lambda v: v.co.y, [
        [(hx - 0.018, hy - 0.022, 0.028), (hx - 0.018, hy + 0.020, 0.028)],
        [(hx + 0.018, hy - 0.022, 0.028), (hx + 0.018, hy + 0.020, 0.028)]])
    r = extrude(bm, r['faces'])
    split_place(r['verts'], lambda v: v.co.x, lambda v: v.co.y, [
        [(hx - 0.030, hy - 0.036, 0.0), (hx - 0.024, hy + 0.040, 0.0)],
        [(hx + 0.032, hy - 0.036, 0.0), (hx + 0.026, hy + 0.040, 0.0)]])
    front = min(r['sides'], key=lambda f: f.calc_center_median().y)
    t = extrude(bm, [front])
    split_place(t['verts'], lambda v: v.co.z, lambda v: v.co.x, [
        [(hx - 0.040, hy - 0.100, 0.0), (hx + 0.042, hy - 0.100, 0.0)],
        [(hx - 0.026, hy - 0.080, 0.017), (hx + 0.028, hy - 0.080, 0.017)]])

    # --- tail: from the lower back (band L0-L1, p5-p6), a short wedge out and down
    t0, t1 = J['tail0'], J['tail1']
    r = extrude(bm, [bands[1][5]])
    for v in r['verts']:
        seam, up = v.co.x < EPS, v.co.z > 0.14
        v.co = Vector(((0.0 if seam else (0.092 if up else 0.080)),
                       t1[1] + (0.005 if up else -0.012) - (0.0 if seam else 0.006),
                       t1[2] + (0.010 if up else -0.014)))
    seamf = [f for f in bm.faces if all(abs(v.co.x) < EPS for v in f.verts)]
    bmesh.ops.delete(bm, geom=seamf, context='FACES')

    # --- ear tufts: from the crown (band L7-L8, p3-p4), a short blade up and out
    r = extrude(bm, [bands[10][3]])
    split_place(r['verts'], lambda v: v.co.z, lambda v: v.co.y, [
        [(0.122, -0.082, 0.612), (0.116, -0.050, 0.607)],
        [(0.110, -0.070, 0.648), (0.106, -0.058, 0.645)]])

    # --- folded wings: from the chest side (band L3-L4, p2-p4) a shoulder cap, then a slab down the flank
    sx, sy, sz = J['shoulderL']
    ROOT_LO = [(0.176, -0.110, 0.318), (0.186, -0.040, 0.314), (0.176, 0.030, 0.320)]
    r = extrude(bm, [bands[5][2], bands[5][3]])
    split_place(r['verts'], lambda v: v.co.z, lambda v: v.co.y, [
        ROOT_LO,
        [(0.158, -0.100, 0.370), (0.170, -0.042, 0.368), (0.160, 0.030, 0.366)]])
    bot = [f for f in r['sides'] if max(v.co.z for v in f.verts) < 0.34]
    WING = [  # (inner row, outer row) per level, front to back: flares at the belly, tucks at the bottom
        ([(0.160, -0.075, 0.250), (0.168, -0.012, 0.248), (0.128, 0.082, 0.252)],
         [(0.192, -0.068, 0.250), (0.200, -0.006, 0.248), (0.155, 0.094, 0.252)]),
        ([(0.150, -0.020, 0.172), (0.146, 0.040, 0.170), (0.120, 0.100, 0.172)],
         [(0.170, -0.012, 0.174), (0.168, 0.046, 0.172), (0.142, 0.106, 0.174)]),
        ([(0.112, 0.084, 0.132), (0.108, 0.134, 0.122), (0.104, 0.178, 0.116)],
         [(0.128, 0.088, 0.130), (0.122, 0.138, 0.120), (0.114, 0.183, 0.112)]),
    ]
    faces = bot
    prev = [tuple(v.co) for v in rings[5][2:5]] + ROOT_LO
    for inner, outer in WING:
        r = extrude(bm, faces)
        map_place(r['verts'], prev, inner + outer)
        prev = inner + outer
        faces = r['faces']

    snap_seam(bm)
    return object_from_bm('body', bm)


def P(level, i):
    return section(*LEVELS[level])[i]


def stage2(k, body):
    bm = edit(body)
    # neck: a full loop between shoulder ring L4 and chin ring L5, so the head turns on a band, not a crease
    with k.topo(bm, 'loop', 'neck loop between L4 and L5: the head turn bends here'):
        loopcut(bm, edge_near(bm, (0.0, -0.179, 0.415)), t=0.5)
    # face disc: open the eye band (L6 down, L6b up) and centre face p1-p2 on the eye (x .026-.106)
    for lv, dz in ((8, -0.010), (9, 0.010)):
        z0 = LEVELS[lv][0]
        p1, p2 = vert_near(bm, P(lv, 1)), vert_near(bm, P(lv, 2))
        for v in verts_where(bm, lambda c: abs(c.z - z0) < 1e-5 and c.z > 0.4):
            v.co.z += dz
        p1.co.x = 0.026
        p2.co.x = 0.106; p2.co.y -= 0.006
    # dish the disc: seam and inner column sit back, the p2 column (the rim) stays forward
    for lv in (7, 8, 9, 10):
        for i in (0, 1):
            vert_near(bm, (P(lv, i)[0] if i == 0 else (0.026 if lv in (8, 9) else P(lv, i)[0]),
                           P(lv, i)[1], LEVELS[lv][0] + {8: -0.010, 9: 0.010}.get(lv, 0))).co.y += 0.007
    # beak root: the seam at eye-low level pushed forward a touch to carry the beak
    vert_near(bm, (0.0, P(8, 0)[1] + 0.007, LEVELS[8][0] - 0.010)).co.y -= 0.010
    # tail: a wedge section, not a plate: the tip's underside drops 12 mm (tip 36 mm deep, was 24),
    # the top edge lifts 3 mm, so the long side faces no longer triangulate into slivers
    for p, dz in (((0.0, 0.198, 0.061), -0.012), ((0.080, 0.192, 0.061), -0.012),
                  ((0.0, 0.215, 0.085), 0.003), ((0.092, 0.209, 0.085), 0.003)):
        vert_near(bm, p).co.z += dz
    # r2 must-fix 4: tail end notched (the seam tip pulls 16 mm, ~15% of the tail, toward the body), and the wing
    # tip given thickness (the outer tip verts pushed out from the inner ones)
    for p in ((0.0, 0.198, 0.049), (0.0, 0.215, 0.088)):
        vert_near(bm, p).co.y -= 0.016
    vert_near(bm, (0.114, 0.183, 0.112)).co.x += 0.008
    vert_near(bm, (0.122, 0.138, 0.120)).co.x += 0.004
    # tail feather bands: two loops across the tail (a cut along its length crosses top, outer side and bottom)
    with k.topo(bm, 'loop', 'tail band 1: across the tail, for the dark/brown feather bands'):
        loopcut(bm, edge_near(bm, (0.080, 0.166, 0.127)), t=0.5)
    with k.topo(bm, 'loop', 'tail band 2: across the tail tip half, for the feather bands'):
        loopcut(bm, edge_near(bm, (0.086, 0.188, 0.107)), t=0.5)
    # wing tip: the lowest outer face (W1 outer front -> W2 outer) was a 5.7 deg needle: bring the W2
    # outer front vert 8 mm forward and 8 mm up so the face is less skewed
    v = vert_near(bm, (0.128, 0.088, 0.130)); v.co.y -= 0.008; v.co.z += 0.008
    # toes: three partial loops down the toe (leg front -> toe top -> toe front -> toe bottom -> foot sole) split the
    # flat foot plate; on the toe front the two notch cuts pull back and the middle cut is the middle toe's tip
    hx, hy = J['hipL'][0], J['hipL'][1]
    cuts = []
    rt = rb = None                                                     # the middle cut's root verts (top, sole)
    for i, (cx, kind) in enumerate(((hx + 0.001, 'tip'), (hx - 0.014, 'notch'), (hx + 0.015, 'notch'))):
        with k.topo(bm, 'partial', 'toe split %d: three toes out of the foot plate (terminators on the leg front / sole, or toe top / bottom)' % (i + 1)):
            if i == 0:
                st, en = edge_near(bm, (hx, hy - 0.034, 0.060)), edge_near(bm, (hx + 0.001, hy + 0.040, 0.0))
            else:
                et, eb = (hx - 0.018, hx - 0.030) if i == 1 else (hx + 0.018, hx + 0.032)
                st = edge_near(bm, ((rt + et) / 2, hy - 0.022, 0.028))
                en = edge_near(bm, ((rb + eb) / 2, hy - 0.036, 0.0))
            ms = partial_loop(bm, st, en, t=0.5)
        for v in ms:
            v.co.x = cx if v.co.y < hy - 0.07 else hx + (cx - hx) * 0.6
            if i == 0 and v.co.y >= hy - 0.07:
                if v.co.z > 0.01: rt = v.co.x
                else: rb = v.co.x
        cuts.append((ms, kind))
    for ms, kind in cuts:
        for v in ms:
            if v.co.y < hy - 0.07:
                if kind == 'notch':
                    v.co.y += 0.026 if v.co.z < 0.005 else 0.014              # notch between toes, back ~20% of the foot
                else:
                    v.co.y -= 0.004                                            # middle toe tip a touch forward
    # eye socket: one loop inside the eye face, pushed in
    f = face_near(bm, (0.066, -0.200, 0.502), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face'):
        inner = inset(bm, [f], 0.22)
    for v in inner[0].verts:
        v.co.y += 0.006
    commit(body, bm)


PAL = {'brown': '#7a5a3c', 'dark': '#4a3424', 'cream': '#efe3c6',
       'orange': '#f08a1c', 'black': '#111111', 'covert': '#9c7752'}
BROW_N = 5
EYE_C, EYE_N = Vector((0.066, -0.175, 0.502)), Vector((0.258, -0.966, 0.0)).normalized()


def prism(bm, c, n, r, sides, front, back, rot=22.5, squash=1.0):
    """A closed low-poly disc: `sides`-gon of radius r facing n, from c+n*back to c+n*front."""
    n = Vector(n).normalized(); u = n.cross(Vector((0, 0, 1))).normalized(); w = u.cross(n)
    pts = [u * math.cos(math.radians(rot + 360 * i / sides)) * r +
           w * math.sin(math.radians(rot + 360 * i / sides)) * r * squash for i in range(sides)]
    a = ring(bm, [c + n * back + q for q in pts]); b = ring(bm, [c + n * front + q for q in pts])
    bridge(bm, a, b, closed=True); cap(bm, a); cap(bm, list(reversed(b)))


def dome(bm, c, n, rings, apex, sides=12, rot=15.0):
    """A closed low-poly dome facing n: rings = [(radius, depth along n), ...] back to front,
    a flat cap on the back ring and a fan to the apex vertex at depth `apex`."""
    n = Vector(n).normalized(); u = n.cross(Vector((0, 0, 1))).normalized(); w = u.cross(n)
    dirs = [u * math.cos(math.radians(rot + 360 * i / sides)) + w * math.sin(math.radians(rot + 360 * i / sides))
            for i in range(sides)]
    rs = [ring(bm, [c + n * d + q * r for q in dirs]) for r, d in rings]
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, rs[0])
    top = ring(bm, [c + n * apex])[0]
    last = rs[-1]
    for i in range(sides):
        bm.faces.new([last[i], last[(i + 1) % sides], top])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def lens(bm, c, n, rim, back, back_apex, front, front_apex, sides=12, rot=15.0):
    """A closed curved shell facing n: one sharp rim ring, back and front rings (radius, depth), two apexes."""
    n = Vector(n).normalized(); u = n.cross(Vector((0, 0, 1))).normalized(); w = u.cross(n)
    dirs = [u * math.cos(math.radians(rot + 360 * i / sides)) + w * math.sin(math.radians(rot + 360 * i / sides))
            for i in range(sides)]
    rr = ring(bm, [c + n * rim[1] + q * rim[0] for q in dirs])
    for rows, apex in ((back, back_apex), (front, front_apex)):
        prev = rr
        for r, d in rows:
            cur = ring(bm, [c + n * d + q * r for q in dirs]); bridge(bm, prev, cur, closed=True); prev = cur
        top = ring(bm, [c + n * apex])[0]
        for i in range(sides):
            bm.faces.new([prev[i], prev[(i + 1) % sides], top])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


DISC_R = (0.034, 0.055, 0.063)     # inner (eye hole), rim border (~12% of the radius), outer: the discs meet at the beak


def disc_piece(me, sides=12):
    n = EYE_N; u = n.cross(Vector((0, 0, 1))).normalized(); w = u.cross(n)
    dirs = [u * math.cos(math.radians(15 + 360 * i / sides)) + w * math.sin(math.radians(15 + 360 * i / sides))
            for i in range(sides)]
    # the export turns each non-planar quad's diagonal so it folds out: raycast both triangulations, keep the front one
    vs = [v.co.copy() for v in me.vertices]
    trees = []
    for alt in (0, 1):
        tris = []
        for pg in me.polygons:
            ids = list(pg.vertices)
            if len(ids) == 4 and alt:
                ids = ids[1:] + ids[:1]
            tris += [(ids[0], ids[j], ids[j + 1]) for j in range(1, len(ids) - 1)]
        trees.append(BVHTree.FromPolygons(vs, tris))
    def skin(q, r):
        ds = []
        for t in trees:
            hit, _, _, dist = t.ray_cast(EYE_C + q * r + n * 0.1, -n)
            if hit:
                ds.append(0.1 - dist)
        return max(ds) if ds else -0.03
    def at(q, r, d):
        p = EYE_C + q * r + n * d
        p.x = max(p.x, 0.006)
        return p
    bm = bmesh.new()
    front, back = [], []
    for r in DISC_R:
        pts = []
        for i, q in enumerate(dirs):
            # the skin can ridge between two samples (the p2 rim column): take the highest of 5 samples across
            # each front face, so no skin edge pokes through the cream
            d = max(skin((q * (1 - t) + dirs[(i + s) % sides] * t).normalized(), r)
                    for s in (1, -1) for t in (0.0, 0.25, 0.5))
            pts.append(at(q, r, max(d + 0.004, -0.010)))
        front.append(ring(bm, pts))
    for r in (DISC_R[0], DISC_R[2]):
        back.append(ring(bm, [at(q, r, skin(q, r) - (0.003 if r < 0.05 else 0.008)) for q in dirs]))   # outer rim sunk deeper: rooted, so poses do not cut it
    bridge(bm, front[0], front[1], closed=True); bridge(bm, front[1], front[2], closed=True)
    bridge(bm, front[2], back[1], closed=True); bridge(bm, back[1], back[0], closed=True)
    bridge(bm, back[0], front[0], closed=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = object_from_bm('disc', bm)
    def rule(c, nn, i):
        v = Vector(c) - EYE_C
        rr = (v - n * v.dot(n)).length
        return 'cream' if rr < 0.050 else 'dark'
    paint(ob, {'cream': PAL['cream'], 'dark': PAL['dark']}, rule)
    return ob


def box(bm, ends):
    """ends: two 4-vertex sections (same winding) -> a closed hexahedron."""
    a, b = ring(bm, ends[0]), ring(bm, ends[1])
    bridge(bm, a, b, closed=True); cap(bm, a); cap(bm, list(reversed(b)))


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if z > 0.585 and x > 0.075:
        return 'dark'                                     # ear tufts
    if 0.43 < z < 0.57 and y < -0.12 and x < 0.118:
        return 'brown'                                    # face skin under the round disc pieces: square corners brown
    if y > 0.12 and z < 0.14 and x < 0.1:
        return 'brown' if 0.168 < y < 0.19 else 'dark'    # fan tail: dark / brown / dark feather bands
    if z < 0.075:
        return 'cream'                                    # feathered legs and feet
    if x > 0.148 or (x > 0.10 and y > 0.06 and z < 0.30):
        return 'dark' if z < 0.21 else ('covert' if z > 0.30 else 'brown')   # folded wing: light coverts, brown, dark primaries
    if n.y < -0.35 and 0.08 < z < 0.33 and x < 0.12:
        return 'cream'                                    # belly; the chest above it stays brown feathers
    return 'brown'


def stage3(k, body):
    paint(body, PAL, body_rule)
    out = []
    # eye: a 12-sided shallow dome (rim proud of the socket, centre raised 5 mm), root sunk in the socket
    bm = bmesh.new(); dome(bm, EYE_C, EYE_N, [(0.032, -0.008), (0.032, 0.003), (0.018, 0.0068)], 0.008)
    out.append(object_from_bm('eye', bm)); paint(out[-1], {'orange': PAL['orange']}, lambda c, n, i: 'orange')
    # pupil: a small dome seated on the eye's front, its back ring just under the eye surface (no step)
    bm = bmesh.new(); dome(bm, EYE_C, EYE_N, [(0.0145, 0.0064), (0.0145, 0.0078)], 0.0092)
    out.append(object_from_bm('pupil', bm)); paint(out[-1], {'black': PAL['black']}, lambda c, n, i: 'black')
    # beak: a short hooked wedge on the seam, root sunk in the face
    # blink lid: a brown dome hidden INSIDE the eye at rest; the eye bone scales it x1.8 about the eye
    # centre so it closes over eye and pupil. Not seated on the skin, so its scale is not drift.
    bm = bmesh.new(); lens(bm, EYE_C, EYE_N, (0.0193, 0.0021), [(0.0108, 0.0047)], 0.0054, [(0.0115, 0.0054)], 0.0061)
    out.append(object_from_bm('lid', bm)); paint(out[-1], {'brown': PAL['brown']}, lambda c, n, i: 'brown')
    # beak: dark hooked beak, 1.4x longer; root sunk in the face, ~60% of it out in front of the disc, tip hooked down 30 deg
    bm = bmesh.new()
    r0 = ring(bm, [(0, -0.183, 0.506), (0.020, -0.183, 0.470), (0, -0.183, 0.436)])
    r1 = ring(bm, [(0, -0.222, 0.500), (0.014, -0.222, 0.472), (0, -0.222, 0.448)])
    r2 = ring(bm, [(0, -0.240, 0.486), (0.008, -0.240, 0.466), (0, -0.240, 0.452)])
    tip = ring(bm, [(0, -0.252, 0.430)])[0]
    bridge(bm, r0, r1); bridge(bm, r1, r2)
    bm.faces.new([r2[0], r2[1], tip]); bm.faces.new([r2[1], r2[2], tip]); cap(bm, r0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    beak = object_from_bm('beak', bm); paint(beak, {'black': PAL['black']}, lambda c, n, i: 'black')
    out.append(beak)
    # facial disc: a 12-sided cream dish around each eye (hole for the eye), dark outer rim ring, conformed to
    # the face by raycast: front 2 mm proud of the skin (flattened to a dish where the head curves away), back sunk 3 mm
    me = body.data
    btree = BVHTree.FromPolygons([body.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    disc = disc_piece(me)
    tv, tf = [v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons]
    o = len(tv); tv += [v.co.copy() for v in disc.data.vertices]; tf += [tuple(i + o for i in p.vertices) for p in disc.data.polygons]
    tree = BVHTree.FromPolygons(tv, tf)                  # brows raycast onto body + disc rim
    # V brows: tapered wedge plates lying on the disc's upper rim (thick inner end, thin outer end),
    # half sunk into the head along the surface normal, 15 deg down toward the centre
    bm = bmesh.new()
    stations = []
    # r2 must-fix 5: the outer end sweeps up and back ~30% further, to the ear-tuft base (x .116, z .607)
    BROW_XZ = [(0.016 + 0.020 * i, 0.536 + 0.0055 * i) for i in range(5)] + [(0.100, 0.564), (0.104, 0.570), (0.109, 0.579), (0.113, 0.588)]
    for i, (x, z) in enumerate(BROW_XZ):
        f = i / (len(BROW_XZ) - 1)
        hit, nrm, _, _ = btree.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))       # skin: the root
        top = tree.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))[0]                # disc rim or skin: the face
        stations.append((hit, nrm.normalized(), 0.0075 - 0.003 * f, 0.007 - 0.002 * f, top))
    secs = []
    for i, (S, N, hh, t, Sf) in enumerate(stations):
        T = (stations[min(i + 1, len(stations) - 1)][0] - stations[max(i - 1, 0)][0]).normalized()
        A = N.cross(T).normalized()
        if A.z < 0:
            A = -A
        # root always 2 mm in the skin (one continuous contact), face t/2 proud of the disc rim or skin
        secs.append(ring(bm, [S - A * hh - N * 0.002, Sf - A * hh + N * t / 2, Sf + A * hh + N * t / 2, S + A * hh - N * 0.002]))
    for a, b in zip(secs, secs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, secs[0]); cap(bm, list(reversed(secs[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    out.append(object_from_bm('brow', bm)); paint(out[-1], {'dark': PAL['dark']}, lambda c, n, i: 'dark')
    # talons: three forward hooks per foot and one back, roots sunk in the toe
    hx, hy = J['hipL'][0], J['hipL'][1]
    bm = bmesh.new()
    # thick hooked talons, one per toe (r2 toe split): base 12 x 12 mm sunk inside the toe front, a mid ring
    # arching up, the tip hooked ~40 deg down to the ground; the same 36-40 mm length as before
    def talon(bx, by, dx, fwd, sgn=-1):
        base = ring(bm, [(bx - 0.006, by, 0.001), (bx + 0.006, by, 0.001), (bx + 0.005, by, 0.013), (bx - 0.005, by, 0.013)])
        my = by + sgn * fwd * 0.62
        mid = ring(bm, [(bx + dx * 0.6 - 0.0035, my, 0.004), (bx + dx * 0.6 + 0.0035, my, 0.004),
                        (bx + dx * 0.6 + 0.003, my, 0.012), (bx + dx * 0.6 - 0.003, my, 0.012)])
        bridge(bm, base, mid, closed=True)
        t = ring(bm, [(bx + dx, by + sgn * fwd, 0.0006)])[0]
        for i in range(4):
            bm.faces.new([mid[i], mid[(i + 1) % 4], t])
        cap(bm, base)
    for bx, by, dx in ((hx - 0.029, -0.096, -0.007), (hx + 0.001, -0.100, 0.0), (hx + 0.031, -0.096, 0.007)):
        talon(bx, by, dx, 0.038)
    talon(hx, 0.000, 0.0, 0.034, sgn=1)                                  # hind toe
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    out.append(object_from_bm('talons', bm)); paint(out[-1], {'black': PAL['black']}, lambda c, n, i: 'black')
    out.append(disc)
    return out


def add_eye_bones(rig):
    """Eye bones added AFTER skinning, so the body has no eye weights; the eye pieces follow them for the blink."""
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        eb = rig.data.edit_bones
        for sx, nm in ((1, 'eye.L'), (-1, 'eye.R')):
            b = eb.new(nm)
            b.head = Vector((EYE_C.x * sx, EYE_C.y, EYE_C.z))
            b.tail = b.head + Vector((EYE_N.x * sx, EYE_N.y, EYE_N.z)) * 0.03
            b.parent = eb['head']
        bpy.ops.object.mode_set(mode='OBJECT')


def blink(rig, act, keys):
    """Key a uniform scale on both eye bones into a clip's action (clip() keys rotation and location only)."""
    ad = rig.animation_data
    ad.action = act
    for f, sc in keys.items():
        for nm in ('eye.L', 'eye.R'):
            rig.pose.bones[nm].scale = (sc, sc, sc)
            rig.pose.bones[nm].keyframe_insert('scale', frame=f)
    ad.action = None
    rest(rig)


def stage4(k, body, pieces):
    hx, hy = J['hipL'][0], J['hipL'][1]
    rig = armature([
        ('root', J['root'][:2] + (0.05,), (0.0, 0.0, 0.20), None),
        ('spine', (0.0, 0.0, 0.20), J['chest'], 'root', True),
        ('head', (0.0, -0.05, 0.41), J['crown'], 'spine'),
        ('tail', J['tail0'], J['tail1'], 'root'),
        ('thigh.L', (hx, hy, 0.10), (hx, hy, 0.03), 'root'),
        ('foot.L', (hx, hy, 0.03), J['toeL'], 'thigh.L', True),
        ('wing.L', J['shoulderL'], J['wingtipL'], 'spine'),
    ], roll='auto')
    skin(body, rig)
    add_eye_bones(rig)
    P = dict(zip(['eye', 'pupil', 'lid', 'beak', 'brow', 'talons', 'disc'], pieces))   # stage3 order
    bind(P['eye'], rig, body=body); bind(P['pupil'], rig, body=body)   # the face skin is part spine: borrow its weights
    # lid: the face skin's weights, with its head share handed to the eye bone (a child of head, so it
    # moves as head until the blink scales it): it follows the eye piece exactly and still blinks
    bind(P['lid'], rig, body=body)
    lid = P['lid']; hg = lid.vertex_groups.get('head')
    eg = {1: lid.vertex_groups.new(name='eye.L'), -1: lid.vertex_groups.new(name='eye.R')}
    ws = []
    for v in lid.data.vertices:
        w = next((g.weight for g in v.groups if g.group == hg.index), 0.0)
        ws.append(w)
        if w > 0:
            hg.remove([v.index]); eg[1 if (lid.matrix_world @ v.co).x > 0 else -1].add([v.index], w, 'REPLACE')
    print('OWL lid head->eye weight min %.3f mean %.3f' % (min(ws), sum(ws) / len(ws)))
    bind(P['beak'], rig, body=body)                        # the face skin under it is part spine: borrow its weights
    bind(P['brow'], rig, body=body)
    bind(P['talons'], rig, body=body)                      # toe skin is part thigh: borrow its weights
    bind(P['disc'], rig, body=body)                        # facial disc rides the face skin's weights
    H = lambda a: {'head': (0, a, 0)}
    act_idle = clip(rig, 'idle', {1: H(0), 10: H(35), 22: H(35), 24: H(35), 26: H(35),
                       32: H(-25), 40: H(-25), 48: H(0)})
    blink(rig, act_idle, {1: 1.0, 22: 1.0, 24: 1.8, 26: 1.0, 48: 1.0})   # f24 is the packet's idle posed frame
    W = lambda a: {'wing.L': (0, 0, a), 'wing.R': (0, 0, -a)}     # both bones' X points -x under auto roll: mirror the Z sign
    clip(rig, 'move', {1: {}, 6: {**W(30), 'thigh.L': (-15, 0, 0), 'thigh.R': (-15, 0, 0)},
                       12: {**W(5), 'thigh.L': (-20, 0, 0), 'thigh.R': (-20, 0, 0), 'tail': (-10, 0, 0)},
                       18: {**W(30)}, 24: {}},
         loc={1: {}, 6: {'root': (0, 0.03, 0)}, 12: {'root': (0, 0.06, 0)}, 18: {'root': (0, 0.02, 0)}, 24: {}})
    # strike at f16 (50%): both wings raised (-X lifts the back-hanging tip) and opened 60 deg, talons thrown forward
    WR = lambda up, a: {'wing.L': (-up, 0, a), 'wing.R': (-up, 0, -a)}
    clip(rig, 'attack', {1: {}, 8: {**WR(25, 40), 'spine': (-10, 0, 0), 'head': (-8, 0, 0)},
                         16: {**WR(50, 60), 'spine': (12, 0, 0), 'head': (-10, 0, 0),
                              'thigh.L': (55, 0, 0), 'thigh.R': (55, 0, 0), 'foot.L': (-30, 0, 0), 'foot.R': (-30, 0, 0)},
                         24: {**W(20), 'spine': (4, 0, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
