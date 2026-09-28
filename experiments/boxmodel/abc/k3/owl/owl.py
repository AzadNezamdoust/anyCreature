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
    # wing tip: the lowest outer face (W1 outer front -> W2 outer) was a 5.7 deg needle: bring the W2
    # outer front vert 8 mm forward and 8 mm up so the face is less skewed
    v = vert_near(bm, (0.128, 0.088, 0.130)); v.co.y -= 0.008; v.co.z += 0.008
    # eye socket: one loop inside the eye face, pushed in
    f = face_near(bm, (0.066, -0.200, 0.502), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face'):
        inner = inset(bm, [f], 0.22)
    for v in inner[0].verts:
        v.co.y += 0.006
    commit(body, bm)


PAL = {'brown': '#7a5a3c', 'dark': '#4a3424', 'cream': '#efe3c6',
       'orange': '#f08a1c', 'black': '#111111', 'beak': '#d8b870'}
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


def box(bm, ends):
    """ends: two 4-vertex sections (same winding) -> a closed hexahedron."""
    a, b = ring(bm, ends[0]), ring(bm, ends[1])
    bridge(bm, a, b, closed=True); cap(bm, a); cap(bm, list(reversed(b)))


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if z > 0.585 and x > 0.075:
        return 'dark'                                     # ear tufts
    if 0.43 < z < 0.57 and y < -0.12 and x < 0.118:
        if x > 0.06 and (z < 0.47 or z > 0.535):
            return 'dark'                                 # the disc's square corners: rim, so the cream reads round
        return 'cream' if (n.y < -0.40 and x < 0.112 and 0.438 < z < 0.56) else 'dark'   # disc + dark rim
    if y > 0.15 and z < 0.14 and x < 0.1:
        return 'dark'                                     # fan tail
    if z < 0.075:
        return 'cream'                                    # feathered legs and feet
    if x > 0.148 or (x > 0.10 and y > 0.06 and z < 0.30):
        return 'dark' if z < 0.21 else 'brown'            # folded wing, darker primaries
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
    bm = bmesh.new()
    r0 = ring(bm, [(0, -0.180, 0.494), (0.019, -0.180, 0.468), (0, -0.180, 0.438)])
    r1 = ring(bm, [(0, -0.212, 0.484), (0.012, -0.210, 0.462), (0, -0.210, 0.445)])
    tip = ring(bm, [(0, -0.230, 0.428)])[0]
    bridge(bm, r0, r1)
    bm.faces.new([r1[0], r1[1], tip]); bm.faces.new([r1[1], r1[2], tip]); cap(bm, r0)
    out.append(object_from_bm('beak', bm)); paint(out[-1], {'beak': PAL['beak']}, lambda c, n, i: 'beak')
    # V brows: tapered wedge plates lying on the disc's upper rim (thick inner end, thin outer end),
    # half sunk into the head along the surface normal, 15 deg down toward the centre
    me = body.data
    tree = BVHTree.FromPolygons([body.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    bm = bmesh.new()
    stations = []
    for i in range(BROW_N):
        f = i / (BROW_N - 1)
        x, z = 0.016 + (0.096 - 0.016) * f, 0.536 + (0.558 - 0.536) * f
        hit, nrm, _, _ = tree.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))
        stations.append((hit, nrm.normalized(), 0.0075 - 0.0045 * f, 0.007 - 0.003 * f))
    secs = []
    for i, (S, N, hh, t) in enumerate(stations):
        T = (stations[min(i + 1, BROW_N - 1)][0] - stations[max(i - 1, 0)][0]).normalized()
        A = N.cross(T).normalized()
        if A.z < 0:
            A = -A
        secs.append(ring(bm, [S - A * hh - N * t / 2, S - A * hh + N * t / 2, S + A * hh + N * t / 2, S + A * hh - N * t / 2]))
    for a, b in zip(secs, secs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, secs[0]); cap(bm, list(reversed(secs[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    out.append(object_from_bm('brow', bm)); paint(out[-1], {'dark': PAL['dark']}, lambda c, n, i: 'dark')
    # talons: three forward hooks per foot and one back, roots sunk in the toe
    hx, hy = J['hipL'][0], J['hipL'][1]
    bm = bmesh.new()
    # roots 11 mm inside the toe with their tops under its upper face (the toe top is at z .017 at
    # y -.105 and the slanted toe front drops to z 0 at y -.125); tips forward and down to the ground
    for tx, dx in ((hx - 0.027, -0.006), (hx, 0.0), (hx + 0.028, 0.006)):
        base = ring(bm, [(tx - 0.005, -0.106, 0.002), (tx + 0.005, -0.106, 0.002), (tx + 0.004, -0.106, 0.010), (tx - 0.004, -0.106, 0.010)])
        t = ring(bm, [(tx + dx, -0.146, 0.001)])[0]
        for i in range(4):
            bm.faces.new([base[i], base[(i + 1) % 4], t])
        cap(bm, base)
    base = ring(bm, [(hx - 0.006, 0.000, 0.002), (hx + 0.006, 0.000, 0.002), (hx + 0.005, 0.000, 0.010), (hx - 0.005, 0.000, 0.010)])
    t = ring(bm, [(hx, 0.036, 0.001)])[0]
    for i in range(4):
        bm.faces.new([base[i], base[(i + 1) % 4], t])
    cap(bm, base)
    out.append(object_from_bm('talons', bm)); paint(out[-1], {'black': PAL['black']}, lambda c, n, i: 'black')
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
    P = dict(zip(['eye', 'pupil', 'lid', 'beak', 'brow', 'talons'], pieces))   # stage3 order
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
    H = lambda a: {'head': (0, a, 0)}
    act_idle = clip(rig, 'idle', {1: H(0), 10: H(35), 22: H(35), 24: H(35), 26: H(35),
                       32: H(-25), 40: H(-25), 48: H(0)})
    blink(rig, act_idle, {1: 1.0, 22: 1.0, 24: 1.8, 26: 1.0, 48: 1.0})   # f24 is the packet's idle posed frame
    W = lambda a: {'wing.L': (0, 0, a), 'wing.R': (0, 0, -a)}     # both bones' X points -x under auto roll: mirror the Z sign
    clip(rig, 'move', {1: {}, 6: {**W(30), 'thigh.L': (-15, 0, 0), 'thigh.R': (-15, 0, 0)},
                       12: {**W(5), 'thigh.L': (-20, 0, 0), 'thigh.R': (-20, 0, 0), 'tail': (-10, 0, 0)},
                       18: {**W(30)}, 24: {}},
         loc={1: {}, 6: {'root': (0, 0.03, 0)}, 12: {'root': (0, 0.06, 0)}, 18: {'root': (0, 0.02, 0)}, 24: {}})
    clip(rig, 'attack', {1: {}, 8: {**W(35), 'spine': (-10, 0, 0), 'head': (-8, 0, 0)},
                         16: {**W(40), 'spine': (12, 0, 0), 'head': (-10, 0, 0),
                              'thigh.L': (55, 0, 0), 'thigh.R': (55, 0, 0), 'foot.L': (-30, 0, 0), 'foot.R': (-30, 0, 0)},
                         24: {**W(20), 'spine': (4, 0, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
