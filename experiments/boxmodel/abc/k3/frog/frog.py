import os, sys, math, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

META = dict(creature='frog', model='opus', engine_glb='',
            keep_valleys=lambda c: c.y < -0.16 and c.z > 0.25)

# ---------------------------------------------------------------- skeleton (stage 1 AND stage 4)
J = dict(
    root=(0.0, 0.11, 0.11), chest=(0.0, -0.02, 0.15), neck=(0.0, -0.075, 0.20), snout=(0.0, -0.185, 0.245),
    jaw0=(0.0, -0.07, 0.195), jawtip=(0.0, -0.18, 0.225),
    eye0=(0.068, -0.094, 0.262), eyetop=(0.068, -0.096, 0.298),
    shoulder=(0.140, -0.050, 0.118), elbow=(0.145, -0.065, 0.068), wrist=(0.142, -0.080, 0.030),
    hand=(0.150, -0.125, 0.008),
    hip=(0.108, 0.135, 0.118), knee=(0.165, 0.02, 0.095), heel=(0.182, 0.184, 0.034),
    toe=(0.21, 0.07, 0.009),
)

# ---------------------------------------------------------------- body stations: y, half ring (x, z) top -> bottom
# 0 top seam, 1 dorsal, 2 brow / upper flank, 3 mouth corner / flank, 4 jaw / low flank, 5 bottom seam
ST = [
    (-0.188, [(0, 0.250), (0.022, 0.249), (0.038, 0.243), (0.044, 0.232), (0.030, 0.222), (0, 0.219)]),
    (-0.160, [(0, 0.266), (0.040, 0.264), (0.070, 0.255), (0.083, 0.236), (0.055, 0.206), (0, 0.198)]),
    (-0.118, [(0, 0.274), (0.050, 0.274), (0.095, 0.262), (0.112, 0.232), (0.075, 0.172), (0, 0.155)]),
    (-0.068, [(0, 0.268), (0.055, 0.266), (0.100, 0.250), (0.120, 0.200), (0.100, 0.120), (0, 0.100)]),
    (-0.042, [(0, 0.261), (0.058, 0.258), (0.103, 0.235), (0.124, 0.168), (0.106, 0.094), (0, 0.070)]),
    (-0.015, [(0, 0.256), (0.060, 0.252), (0.108, 0.218), (0.126, 0.140), (0.100, 0.068), (0, 0.045)]),
    (0.045,  [(0, 0.238), (0.058, 0.232), (0.098, 0.196), (0.110, 0.122), (0.090, 0.064), (0, 0.046)]),
    (0.100,  [(0, 0.200), (0.045, 0.194), (0.075, 0.165), (0.080, 0.112), (0.064, 0.075), (0, 0.064)]),
    (0.140,  [(0, 0.155), (0.025, 0.150), (0.040, 0.135), (0.042, 0.112), (0.026, 0.096), (0, 0.092)]),
]


def sec(c, n, a, b, k=4, phase=0.0):
    """k points of an ellipse section at c, perpendicular to n: a along the horizontal axis, b the other."""
    c, n = Vector(c), Vector(n).normalized()
    e1 = n.cross(Vector((0, 0, 1)))
    if e1.length < 1e-4:
        e1 = Vector((1, 0, 0))
    e1.normalize()
    e2 = n.cross(e1).normalized()
    return [c + e1 * (a * math.cos(math.radians(phase + 360 * i / k))) + e2 * (b * math.sin(math.radians(phase + 360 * i / k)))
            for i in range(k)]


def boundary_loop(faces):
    fs = set(faces)
    edges = [e for f in faces for e in f.edges if sum(1 for g in e.link_faces if g in fs) == 1]
    nxt = {}
    for f in faces:
        for l in f.loops:
            if l.edge in edges:
                nxt[l.vert] = l.link_loop_next.vert
    v0 = next(iter(nxt))
    out, v = [v0], nxt[v0]
    while v != v0:
        out.append(v); v = nxt[v]
    return out


def grow(bm, faces, pts, n1):
    """Extrude a face region and place its boundary loop on the section pts (cyclic order kept)."""
    faces = list(faces)
    for f in faces:
        f.normal_update()
    n0 = sum((f.normal for f in faces), Vector()).normalized()
    c0 = centre(boundary_loop(faces))
    r = extrude(bm, faces)
    loop = boundary_loop(r['faces'])
    c1 = sum(pts, Vector()) / len(pts)
    R = n0.rotation_difference(Vector(n1).normalized())
    dirs = [(R @ (v.co - c0)).normalized() for v in loop]
    tgt = [(p - c1).normalized() for p in pts]
    best, bs = None, -1e9
    m = len(pts)
    for rev in (False, True):
        order = list(range(m))[::-1] if rev else list(range(m))
        for s in range(m):
            perm = [order[(i + s) % m] for i in range(m)]
            sc = sum(dirs[i].dot(tgt[perm[i]]) for i in range(m))
            if sc > bs:
                bs, best = sc, perm
    for i, v in enumerate(loop):
        v.co = pts[best[i]].copy()
    return r['faces']


def body_face(bm, i_st, seg):
    """The body quad between station i_st and i_st+1 on ring segment seg."""
    y = (ST[i_st][0] + ST[i_st + 1][0]) / 2
    a0, a1 = ST[i_st][1][seg], ST[i_st][1][seg + 1]
    b0, b1 = ST[i_st + 1][1][seg], ST[i_st + 1][1][seg + 1]
    x = (a0[0] + a1[0] + b0[0] + b1[0]) / 4
    z = (a0[1] + a1[1] + b0[1] + b1[1]) / 4
    return min(bm.faces, key=lambda f: (f.calc_center_median() - Vector((x, y, z))).length)


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, [(x, y, z) for x, z in pts]) for y, pts in ST]
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b)
    cap(bm, list(reversed(rings[0])))
    cap(bm, rings[-1])
    recalc_normals(bm)
    bm.faces.ensure_lookup_table()
    # the four extrusions are picked before any of them changes the face list
    f_eye = body_face(bm, 2, 1)
    f_arm = [body_face(bm, 3, 3), body_face(bm, 4, 3)]
    f_hip = [body_face(bm, 7, 1), body_face(bm, 7, 2), body_face(bm, 7, 3)]

    # eye turret: the big bulge on top of the wide head
    e = grow(bm, [f_eye], sec((0.072, -0.095, 0.284), (0.15, -0.1, 1), 0.031, 0.030, 4, 0), (0.15, -0.1, 1))
    grow(bm, e, sec((0.071, -0.093, 0.302), (0.1, 0.1, 1), 0.016, 0.016, 4, 0), (0.1, 0.1, 1))

    # front leg: shoulder, elbow, wrist, then a flat hand on the ground
    a = grow(bm, f_arm, sec(J['shoulder'], (0.35, -0.1, -1), 0.028, 0.022, 6), (0.35, -0.1, -1))
    a = grow(bm, a, sec(J['elbow'], (0.05, -0.25, -1), 0.022, 0.018, 6), (0.05, -0.25, -1))
    a = grow(bm, a, sec(J['wrist'], (0.0, -0.3, -1), 0.016, 0.014, 6), (0.0, -0.3, -1))
    a = grow(bm, a, sec((0.145, -0.100, 0.011), (0.1, -1, -0.4), 0.022, 0.008, 6), (0.1, -1, -0.4))
    grow(bm, a, sec(J['hand'], (0.15, -1, 0), 0.026, 0.006, 6), (0.15, -1, 0))

    # hind leg, folded Z: thigh forward to the knee, shin back to the heel, long foot forward
    h = grow(bm, f_hip, sec(J['hip'], (1, 0.25, 0), 0.044, 0.046, 8, 22.5), (1, 0.25, 0))
    h = grow(bm, h, sec((0.150, 0.085, 0.113), (0.45, -1, 0), 0.040, 0.050, 8, 22.5), (0.45, -1, 0))
    h = grow(bm, h, sec((0.162, 0.030, 0.108), (0.1, -1, -0.1), 0.030, 0.036, 8, 22.5), (0.1, -1, -0.1))
    h = grow(bm, h, sec((0.172, 0.006, 0.078), (0, -0.7, -1), 0.026, 0.022, 8, 22.5), (0, -0.7, -1))
    h = grow(bm, h, sec((0.178, 0.035, 0.050), (0, 1, 0), 0.023, 0.022, 8, 22.5), (0, 1, 0))
    h = grow(bm, h, sec((0.176, 0.150, 0.048), (0, 1, 0), 0.020, 0.021, 8, 22.5), (0, 1, 0))
    h = grow(bm, h, sec(J['heel'], (0, 0.3, -1), 0.020, 0.016, 8, 22.5), (0, 0.3, -1))
    h = grow(bm, h, sec((0.196, 0.160, 0.012), (0.3, -1, 0), 0.024, 0.008, 8, 22.5), (0.3, -1, 0))
    grow(bm, h, sec(J['toe'], (0.25, -1, 0), 0.028, 0.006, 8, 22.5), (0.25, -1, 0))

    snap_seam(bm)
    selfhits(bm)
    return object_from_bm('body', bm)


def selfhits(bm):
    bm.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(bm)
    bad = []
    for i, j in t.overlap(t):
        if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
            bad.append(tuple(round(c, 3) for c in bm.faces[i].calc_center_median()))
    say('selfhits', len(bad), bad[:12])


def limb_loop(k, bm, p0, p1, off, t, why):
    """A full loop round a limb, in the segment p0 -> p1, t measured from the p0 end."""
    p0, p1 = Vector(p0), Vector(p1)
    e = edge_near(bm, (p0 + p1) / 2 + Vector(off))
    near = min(e.verts, key=lambda v: (v.co - p0).length)
    with k.topo(bm, 'loop', why):
        loopcut(bm, e, t=t, near=near)


def stage2(k, body):
    bm = edit(body)
    limb_loop(k, bm, J['shoulder'], J['elbow'], (0.02, 0, 0), 0.7, 'elbow: second loop above the bend')
    limb_loop(k, bm, J['elbow'], J['wrist'], (0.018, 0, 0), 0.3, 'elbow: third loop below the bend')
    limb_loop(k, bm, J['hip'], (0.150, 0.085, 0.113), (0, 0, 0.046), 0.35, 'hip: a loop where the thigh leaves the body')
    limb_loop(k, bm, (0.178, 0.035, 0.050), (0.176, 0.150, 0.048), (0, 0, 0.02), 0.5, 'shin: mid loop for the hop stretch')
    bm.faces.ensure_lookup_table()
    fn = face_near(bm, (0.040, -0.174, 0.258), (0, -0.3, 1))
    with k.topo(bm, 'inset', 'nostril on the snout top'):
        nf = inset(bm, [fn], 0.86, -0.002)[0]
    # a flat, wide frog skull: the top of the head is one plane from the snout to behind the eyes
    top = verts_where(bm, lambda c: c.y < -0.10 and c.z > 0.245 and c.x < 0.052)
    flatten(top)
    # upper lip ridge: the mouth corner row pushed out so the jaw line catches a crease
    for v in verts_where(bm, lambda c: c.y < -0.06 and abs(c.z - 0.233) < 0.006 and c.x > 0.04):
        v.co.x += 0.006
    # paddle ends (hind foot, hand) were 1.2 cm thick: their side faces were slivers. Thicken the tops.
    for c, r, dz in ((J['toe'], 0.03, 0.009), ((0.196, 0.160, 0.012), 0.03, 0.006),
                     (J['hand'], 0.03, 0.007), ((0.145, -0.100, 0.011), 0.025, 0.005)):
        c = Vector(c)
        for v in verts_where(bm, lambda q: (q - c).length < r and q.z > c.z and q.z < 0.03):
            v.co.z += dz
    # a rounder, lower belly: the low-flank corners (ring point 4) out and down, the belly seam
    # (ring point 5) down between the legs, so az000 is not a box and az090 has no gap under the body
    for i_st, (dx, dz4, dz5) in {3: (0.008, -0.006, -0.004), 4: (0.010, -0.008, -0.008), 5: (0.010, -0.008, -0.012),
                                 6: (0.008, -0.010, -0.014), 7: (0.0, 0.0, -0.014)}.items():
        y, pts = ST[i_st]
        if dx or dz4:
            v = vert_near(bm, (pts[4][0], y, pts[4][1])); v.co.x += dx; v.co.z += dz4
        v = vert_near(bm, (0.0, y, pts[5][1])); v.co.z += dz5
    # eye turret lowered: the gold ball, not a green dome behind it, owns the top of the head
    for v in verts_where(bm, lambda c: c.z > 0.272 and (c.x - 0.071) ** 2 + (c.y + 0.094) ** 2 < 0.045 ** 2):
        v.co.z -= EYE_DROP * min(1.0, (v.co.z - 0.272) / 0.030)
    # mouth line as geometry: a partial loop just above the lip ridge (stations 0..3), so the black
    # mouth is a strip of the head's own faces and cannot stand off or poke past the cheek
    ridge = []
    for i_st in range(4):
        y = ST[i_st][0]
        ridge.append(min((v for v in bm.verts if abs(v.co.y - y) < 1e-4 and v.co.x > 0.03), key=lambda v: abs(v.co.z - ST[i_st][1][3][1]) + abs(v.co.x - ST[i_st][1][3][0])))
    def seg2(i_st):
        r = ridge[i_st]
        return min((e for e in r.link_edges if abs(e.other_vert(r).co.y - r.co.y) < 1e-4 and e.other_vert(r).co.z > r.co.z),
                   key=lambda e: e.calc_length())
    with k.topo(bm, 'partial_loop', 'mouth line: a thin strip of faces just above the lip ridge, painted black in stage 3'):
        ms = partial_loop(bm, seg2(0), seg2(3), t=MOUTH_T, near=ridge[0], terminate='fan')
    # the snout front is one n-gon cap: an inset gives it a rim, and the rim along its lower edges
    # (mouth corner -> jaw tip -> seam) is the front of the mouth line, a shallow V as on the sheet
    cap_f = next(f for f in ridge[0].link_faces if len(f.verts) > 4)
    cv = list(cap_f.verts)
    with k.topo(bm, 'inset', 'snout front: a rim whose lower edges carry the front of the mouth line'):
        inner = inset(bm, [cap_f], 0.2, 0.0)[0]
    zr = ridge[0].co.z + 1e-4
    for f in [g for e in inner.edges for g in e.link_faces if g is not inner]:
        orig = [v for v in f.verts if v in cv]
        if len(orig) == 2 and all(v.co.z <= zr for v in orig):
            STRIP.append(f.calc_center_median().copy())
    keep = set(ms) | set(ridge)
    STRIP[:] = STRIP + [f.calc_center_median().copy() for f in bm.faces
                if set(f.verts) <= keep and set(f.verts) & set(ms)]
    NOSTRIL[:] = [nf.calc_center_median().copy()]      # after the skull flatten moved it
    say('mouth strip faces', len(STRIP), [tuple(round(q, 3) for q in c) for c in STRIP])
    commit(body, bm)


NOSTRIL = []        # centre of the nostril's inner face (stage 2 -> stage 3 paint)
STRIP = []          # centres of the mouth-strip faces (stage 2 -> stage 3 paint)
MOUTH_T = 0.28
EYE_DROP = 0.016    # turret top comes down 1.6 cm: a low rim
WEB_L = 0.62        # hind webs reach 62% of the toe length
LENS_DROP = 0.006   # the lens only 6 mm, so the gold ball stays proud on the rim

PAL = {'skin': '#5fae3c', 'spot': '#2f6b2a', 'belly': '#efe0b0', 'eye': '#f2c230', 'pupil': '#151515', 'tongue': '#d8677a'}


def body_rule(c, n, i):
    ax = abs(c.x)
    if any((Vector((ax, c.y, c.z)) - q).length < 0.0015 for q in STRIP):
        return 'pupil'                                     # mouth line
    if any((Vector((ax, c.y, c.z)) - q).length < 0.001 for q in NOSTRIL):
        return 'pupil'                                     # nostril: the inset's inner face only, a dot
    if ax > 0.118 or (c.y > 0.07 and ax > 0.06):
        return 'skin'                                      # limbs and thighs
    if c.y < -0.075:
        mz = 0.231 if c.y < -0.10 else 0.231 - (c.y + 0.10) * 0.6
        return 'belly' if c.z < mz else 'skin'             # jaw below the mouth ridge
    if (n.z < -0.2 and c.y < 0.09) or (n.y < -0.45 and c.z < 0.2):
        return 'belly'
    return 'skin'


def V3(*a):
    return Vector(a)


def toe(bm, root, tip, w):
    d = (tip - root).normalized()
    L = (tip - root).length
    rs = [sec(root, d, w * 1.2, w * 0.8, 4, 45), sec(root + d * (L * 0.5), d, w * 1.05, w * 0.75, 4, 45), sec(tip - d * 0.009, d, w * 0.8, w * 0.6, 4, 45),
          sec(tip - d * 0.004, d, w * 1.9, w * 1.0, 4, 45), sec(tip + d * 0.002, d, w * 1.1, w * 0.7, 4, 45)]
    vs = [ring(bm, r) for r in rs]
    for x, y in zip(vs, vs[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, list(reversed(vs[0]))); cap(bm, vs[-1])
    return vs


def fan(end, fwd, offs, angs, lens, w, zroot):
    fwd = Vector(fwd).normalized(); side = Vector((-fwd.y, fwd.x, 0))
    if side.x < 0:
        side = -side
    out = []
    for o, a_, L in zip(offs, angs, lens):
        root = Vector(end) - fwd * 0.012 + side * o
        root.z = zroot
        dr = Matrix.Rotation(math.radians(a_), 3, 'Z') @ fwd
        tip = root + dr * L
        tip.z = 0.707 * w + 0.0006
        out.append((root, tip))
    return out


def slab(bm, pts, t=0.0015):
    A, B, C, D, E = pts
    pts = [A, A.lerp(B, 0.5), B, C, D, E.lerp(D, 0.5), E]
    up = Vector((0, 0, t))
    top = ring(bm, [p + up for p in pts]); bot = ring(bm, [p - up for p in pts])
    for tri in ((0, 1, 5), (0, 5, 6), (1, 2, 3), (1, 3, 5), (3, 4, 5)):
        bm.faces.new([top[j] for j in tri]); bm.faces.new([bot[j] for j in reversed(tri)])
    m = len(pts)
    for j in range(m):
        bm.faces.new([top[j], bot[j], bot[(j + 1) % m], top[(j + 1) % m]])


def stage3(k, body):
    paint(body, PAL, body_rule)
    eb = evaluated_bm(body)
    tree = BVHTree.FromBMesh(eb)
    pieces = []
    # eyes: a gold low-poly ball with a horizontal black pupil band, sitting proud of the turret
    bm = bmesh.new()
    c, r, lats, nl = V3(0.083, -0.108, 0.284 - LENS_DROP), 0.027, (-60, -12, 12, 60), 10
    rings_ = [ring(bm, [c + V3(r * math.cos(math.radians(la)) * math.cos(2 * math.pi * j / nl),
                               r * math.cos(math.radians(la)) * math.sin(2 * math.pi * j / nl),
                               r * math.sin(math.radians(la))) for j in range(nl)]) for la in lats]
    for x, y in zip(rings_, rings_[1:]):
        bridge(bm, x, y, closed=True)
    sp, np_ = bm.verts.new(c + V3(0, 0, -r)), bm.verts.new(c + V3(0, 0, r))
    for j in range(nl):
        bm.faces.new([rings_[0][(j + 1) % nl], rings_[0][j], sp]); bm.faces.new([rings_[-1][j], rings_[-1][(j + 1) % nl], np_])
    eye = object_from_bm('eye', bm)
    view = V3(0.6, -0.8, 0).normalized()
    paint(eye, PAL, lambda q, n, i: 'pupil' if abs(n.z) < 0.3 and n.y < -0.3 and n.x * (1 if q.x > 0 else -1) > -0.3 else 'eye')   # front bar only
    pieces.append(eye)
    # spots: low irregular domes, rim sunk 1 mm into the skin
    bm = bmesh.new()
    for (x, y, rr), rot in zip([(0.032, -0.035, 0.024), (0.085, -0.005, 0.026), (0.038, 0.035, 0.028), (0.09, 0.055, 0.021),
                                (0.045, 0.092, 0.019), (0.11, -0.055, 0.017)],     # six, 1.6x, sizes varied as on the sheet top
                               (0, 17, 33, 8, 41, 25)):
        loc, n0, _, _ = tree.ray_cast(V3(x, y, 0.6), V3(0, 0, -1))
        e1 = n0.cross(V3(0, 1, 0)).normalized(); e2 = n0.cross(e1).normalized()
        rim, top = [], []
        for j, f in enumerate((1.0, 0.82, 1.08, 0.9, 1.05, 0.78)):
            ang = math.radians(rot + 60 * j)
            q = loc + (e1 * math.cos(ang) + e2 * math.sin(ang)) * rr * f
            l1, n1, _, _ = tree.find_nearest(q); rim.append(l1 - n1 * 0.001)
            l2, n2, _, _ = tree.find_nearest(loc + (q - loc) * 0.62); top.append(l2 + n2 * 0.0025)
        rv, tv = ring(bm, rim), ring(bm, top)
        cv = bm.verts.new(loc + n0 * 0.003)
        bridge(bm, rv, tv, closed=True)
        for j in range(6):
            bm.faces.new([tv[j], tv[(j + 1) % 6], cv])
        cap(bm, list(reversed(rv)))
    spots = object_from_bm('spots', bm); paint(spots, PAL, lambda q, n, i: 'spot'); pieces.append(spots)
    # front toes: four splayed toes with round pad tips
    bm = bmesh.new()
    for root, tip in fan(J['hand'], (0.15, -1, 0), (-0.011, -0.004, 0.004, 0.011), (-40, -13, 13, 40), (0.034, 0.041, 0.041, 0.034), 0.0055, 0.011):   # 1.3x thicker
        toe(bm, root, tip, 0.0055)
    fingers = object_from_bm('fingers', bm); paint(fingers, PAL, lambda q, n, i: 'skin'); pieces.append(fingers)
    # hind toes: five long toes, webbed to 70 % of their length
    bm = bmesh.new()
    tt = fan(J['toe'], (0.25, -1, 0), (-0.016, -0.008, 0.0, 0.008, 0.016), (-32, -14, 2, 18, 36), (0.045, 0.058, 0.066, 0.058, 0.048), 0.0045, 0.013)
    for root, tip in tt:
        toe(bm, root, tip, 0.0045)
    for (r0, t0), (r1, t1) in zip(tt, tt[1:]):
        B, D = r0.lerp(t0, WEB_L), r1.lerp(t1, WEB_L)
        C = ((B + D) / 2).lerp((r0 + r1) / 2, 0.12)       # a shallow notch: the web fills toe to toe
        slab(bm, [r0, B, C, D, r1], t=0.0025)
    toes = object_from_bm('toes', bm)
    paint(toes, PAL, lambda q, n, i: 'skin'); pieces.append(toes)
    # tongue: folded inside the head, root first (the root stays on the jaw when it lashes)
    bm = bmesh.new()
    ts = [((-0.105, 0.198), 0.010, 0.004), ((-0.122, 0.205), 0.011, 0.004), ((-0.14, 0.212), 0.012, 0.004),
          ((-0.158, 0.219), 0.012, 0.0038), ((-0.174, 0.225), 0.011, 0.0035), ((-0.1868, 0.229), 0.008, 0.003)]
    tv = [ring(bm, sec(V3(0, y, z), (0, -1, 0.3), a_, b_, 4, 45)) for (y, z), a_, b_ in ts]
    for x, y in zip(tv, tv[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, list(reversed(tv[0]))); cap(bm, tv[-1])
    tongue = object_from_bm('tongue', bm, mirror=False)
    paint(tongue, PAL, lambda q, n, i: 'tongue'); pieces.append(tongue)
    eb.free()
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('root', (0, 0.13, 0.11), J['chest'], None),
        ('chest', J['chest'], J['neck'], 'root', True),
        ('head', (0, -0.07, 0.236), (0, -0.172, 0.256), 'chest'),
        ('jaw', (0, -0.06, 0.188), (0, -0.172, 0.222), 'chest'),
        ('eye.L', J['eye0'], J['eyetop'], 'head'),
        ('tongue1', (0, -0.14, 0.212), (0, -0.172, 0.224), 'jaw'),
        ('tongue2', (0, -0.172, 0.224), (0, -0.19, 0.229), 'tongue1', True),
        ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
        ('thigh.L', (0.06, 0.125, 0.11), J['knee'], 'root'),
        ('shin.L', J['knee'], J['heel'], 'thigh.L', True),
        ('foot.L', J['heel'], (0.215, 0.05, 0.01), 'shin.L', True),
    ], roll='auto')
    for b in ('tongue1', 'tongue2'):
        rig.data.bones[b].use_deform = False          # the skin never follows the tongue
    skin(body, rig)
    for b in ('tongue1', 'tongue2'):
        rig.data.bones[b].use_deform = True
    # the long hind-foot paddle is rigid with the foot bone, so the rigid toes and webs stay seated on it
    fh, ft = Vector(J['heel']), Vector((0.215, 0.05, 0.01))
    sk, sh = Vector(J['knee']), Vector(J['heel'])

    def segd(p, a, b):
        t = max(0.0, min(1.0, (p - a).dot(b - a) / (b - a).length_squared))
        return (p - a.lerp(b, t)).length
    for v in body.data.vertices:
        q = Vector((abs(v.co.x), v.co.y, v.co.z))
        if q.x > 0.14 and q.z < 0.032 and segd(q, fh, ft) < segd(q, sk, sh):
            side = 'L' if v.co.x > 0 else 'R'
            for g in body.vertex_groups:
                g.remove([v.index])
            body.vertex_groups['foot.' + side].add([v.index], 1.0, 'REPLACE')
    for p in pieces:
        if p.name.endswith('toes'):
            bind(p, rig)                                # rigid per vertex to the nearest bone: foot.L / foot.R
        else:
            bind(p, rig, body=body)
    tg = next(p for p in pieces if 'tongue' in p.name)
    g1 = tg.vertex_groups.get('tongue1') or tg.vertex_groups.new(name='tongue1')
    g2 = tg.vertex_groups.get('tongue2') or tg.vertex_groups.new(name='tongue2')
    for v in tg.data.vertices:                         # sections 1-3 (12 verts) ride the jaw skin; 4-6 lash out
        if v.index >= 12:
            for g in list(tg.vertex_groups):
                g.remove([v.index])
            (g2 if v.index >= 20 else g1).add([v.index], 1.0, 'REPLACE')
    # idle: throat pulse (jaw drops a little, twice) and a blink (eyes pull down into the head)
    clip(rig, 'idle', {1: {}, 8: {'jaw': (-4, 0, 0), 'chest': (1, 0, 0)}, 16: {}, 24: {'jaw': (-4, 0, 0), 'chest': (1, 0, 0)},
                       32: {}, 48: {}},
         loc={1: {}, 36: {}, 40: {'eye.L': (0, -0.010, 0), 'eye.R': (0, -0.010, 0)}, 44: {}, 48: {}})
    # move: a hop - crouch, launch (legs extend, body pitches up), land
    crouch = {'root': (-6, 0, 0), 'thigh.L': (6, 0, 0), 'thigh.R': (6, 0, 0)}
    launch = {'root': (12, 0, 0), 'thigh.L': (-8, 0, 0), 'thigh.R': (-8, 0, 0), 'shin.L': (-18, 0, 0), 'shin.R': (-18, 0, 0)}
    land = {'root': (-4, 0, 0)}
    clip(rig, 'move', {1: {}, 5: crouch, 11: launch, 17: land, 24: {}},
         loc={1: {}, 5: {'root': (0, 0, -0.008)}, 11: {'root': (0, 0.03, 0.05)}, 17: {'root': (0, 0.05, 0.0)}, 24: {}})
    # attack: tongue lash - lean in, jaw drops, tongue shoots out and snaps back
    clip(rig, 'attack', {1: {}, 6: {'chest': (-6, 0, 0), 'head': (4, 0, 0)}, 10: {'chest': (-8, 0, 0), 'jaw': (-14, 0, 0)},
                         14: {'chest': (-8, 0, 0), 'jaw': (-14, 0, 0)}, 19: {'chest': (-3, 0, 0), 'jaw': (-3, 0, 0)}, 24: {}},
         loc={1: {}, 8: {}, 11: {'tongue1': (0, 0.09, 0), 'tongue2': (0, 0.06, 0)}, 14: {'tongue1': (0, 0.09, 0), 'tongue2': (0, 0.06, 0)},
              18: {}, 24: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
