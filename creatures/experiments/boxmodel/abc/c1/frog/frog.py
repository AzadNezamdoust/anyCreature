import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet, load_ref
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import numpy as np

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull), then hand detail
META = dict(creature='frog', model='opus', engine_glb='')


# ---------------------------------------------------------------- carve input: mask hand edits
# The sheet's toes and fingers are thinner than the hull voxel (they carve into spikes): they are
# cleared from every view and come back as stage-3 pieces. The side view shows the near and far
# forelegs staggered (a 0.07 m deep fused block): redrawn as ONE foreleg with a hand pad. The front
# view is redrawn below z 0.135 so the belly is round-bottomed with a slot to the foreleg column.
# Polygons in view metres: side (y, z), front (x, z), top (x, y); front/top polygons are the x >= 0
# half and are mirrored.
MASK = {
    'side': dict(
        clear=[[(-0.21, 0.115), (-0.10, 0.115), (-0.045, 0.095), (-0.035, 0.05), (-0.03, -0.01), (-0.21, -0.01)],
               [(-0.035, 0.032), (0.075, 0.032), (0.075, -0.01), (-0.035, -0.01)],
               # hind leg: the knee rounds off over a long foot paddle lying forward on the ground
               [(0.02, 0.078), (0.05, 0.066), (0.09, 0.046), (0.13, 0.036), (0.13, 0.021), (0.02, 0.021)]],
        draw=[[(-0.100, 0.118), (-0.088, 0.065), (-0.084, 0.026), (-0.112, 0.014), (-0.118, 0.0), (-0.052, 0.0),
               (-0.054, 0.016), (-0.058, 0.035), (-0.060, 0.075), (-0.052, 0.112)],
              [(0.035, 0.0), (0.19, 0.0), (0.19, 0.03), (0.13, 0.026), (0.06, 0.021), (0.035, 0.015)]]),
    'front': dict(
        clear=[[(0.0, -0.01), (0.26, -0.01), (0.26, 0.135), (0.0, 0.135)]],
        draw=[[(0.0, 0.04), (0.03, 0.042), (0.05, 0.05), (0.062, 0.065), (0.070, 0.085), (0.073, 0.137), (0.0, 0.137)],
              [(0.073, 0.137), (0.078, 0.08), (0.082, 0.03), (0.072, 0.012), (0.070, 0.0), (0.125, 0.0), (0.118, 0.012),
               (0.108, 0.03), (0.112, 0.08), (0.118, 0.137)],
              [(0.108, 0.137), (0.118, 0.152), (0.14, 0.158), (0.162, 0.150), (0.176, 0.125), (0.174, 0.095),
               (0.168, 0.075), (0.178, 0.04), (0.180, 0.0), (0.125, 0.0), (0.118, 0.03), (0.112, 0.08), (0.108, 0.10)]]),
    'top': dict(
        clear=[[(0.105, -0.25), (0.26, -0.25), (0.26, -0.035), (0.13, -0.035), (0.13, -0.13), (0.105, -0.13)],
               [(0.178, -0.035), (0.26, -0.035), (0.26, 0.25), (0.178, 0.25)]],
        draw=[[(0.065, -0.125), (0.13, -0.125), (0.13, -0.03), (0.065, -0.03)]]),
}


def _inside(P, A, B):
    P = np.array(P)
    ins = np.zeros(A.shape, bool)
    for i in range(len(P)):
        (a1, b1), (a2, b2) = P[i], P[i - 1]
        ins ^= ((b1 > B) != (b2 > B)) & (A < (a2 - a1) * (B - b1) / (b2 - b1 + 1e-12) + a1)
    return ins


def fix_masks(k):
    views = load_ref(k.dir)
    for name, ed in MASK.items():
        v = views[name]
        H, W = v.mask.shape
        R, C = np.mgrid[0:H, 0:W].astype(np.float64)
        if name == 'side':
            A, Bv = (C + v.c0 - v.cmid) * v.s, (v.ground - v.r0 - R) * v.s
        elif name == 'front':
            A, Bv = np.abs(C + v.c0 - v.axis) * v.s, (v.ground - v.r0 - R) * v.s
        else:
            A, Bv = np.abs(R + v.r0 - v.axis) * v.s, (C + v.c0 - v.cmid) * v.s
        m = v.mask.copy()
        for P in ed['clear']:
            m[_inside(P, A, Bv)] = False
        for P in ed['draw']:
            m[_inside(P, A, Bv)] = True
        m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
        v.mask = m
        I = np.zeros((H + 1, W + 1), np.float64)
        I[1:, 1:] = m.astype(np.float64).cumsum(0).cumsum(1)
        v.I = I


CARVE = dict(plan_roundness=2.5, target_tris=(900, 1400))


def stage1(k):
    # carve_base's cache key does not see the mask edit: key it here (a changed polygon re-carves)
    import hashlib
    key = hashlib.sha256(repr((MASK, CARVE, BELLY, TURRET, belly_x.__code__.co_consts)).encode()).hexdigest()
    kf, cf = os.path.join(k.dir, 'carve_mask.key'), os.path.join(k.dir, 'carve_base.json')
    if not os.path.exists(kf) or open(kf).read() != key:
        if os.path.exists(cf):
            os.remove(cf)
        open(kf, 'w').write(key)
    fix_masks(k)
    import carve as CV
    if not hasattr(CV, '_frog_orig_hull'):
        CV._frog_orig_hull = CV.hull_field
    def hull_field(*a, **kw):
        F, org = CV._frog_orig_hull(*a, **kw)
        return belly_cut(F, org, a[1]), org
    CV.hull_field = hull_field                     # runtime wrap in this program (the kit file is untouched)
    body = carve_base(k, **CARVE)
    CV.hull_field = CV._frog_orig_hull
    say('FROG hits %s' % selfhits(body))
    return body


def selfhits(ob):
    bm = evaluated_bm(ob)
    t = BVHTree.FromBMesh(bm)
    bm.faces.ensure_lookup_table()
    out = [tuple(round(c, 3) for c in bm.faces[i].calc_center_median()) for i, j in t.overlap(t)
           if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts))]
    bm.free()
    return out


# ---- belly: the front view's foreleg column extrudes along Y into a flat wall between the fore and
# hind legs; the reference belly is a round cream ball narrower than the legs. A 3D cut of the hull
# occupancy (a carve-input edit, like the masks): between the legs, below z 0.15, nothing outside
# the belly profile; faded in over the leg edges.
TURRET = dict(c=(0.074, -0.105, 0.266), r=0.034)
BELLY = dict(y0=-0.05, y1=0.035, fade=0.02, ztop=0.15)


def belly_cut(F, org, vs):
    nx, ny, nz = F.shape
    X = np.abs(org[0] + np.arange(nx) * vs)[:, None, None]
    Y = (org[1] + np.arange(ny) * vs)[None, :, None]
    Z = (org[2] + np.arange(nz) * vs)[None, None, :]
    w = np.clip(np.minimum((Y - BELLY['y0']) / BELLY['fade'], (BELLY['y1'] - Y) / BELLY['fade']), 0.0, 1.0)
    w = w * np.clip((BELLY['ztop'] - Z) / 0.03, 0.0, 1.0)
    bx = np.vectorize(belly_x)(Z)
    lim = bx + (1.0 - w) * 0.3
    G = np.clip(0.5 + (lim - X) / (2 * vs), 0.0, 1.0)
    F = np.minimum(F, G)
    # eye turrets: the reference's big bulging eyes are thinner than the mask blur in two views and
    # carve as low bumps; the silhouette cue needs them in the base: a turret ball (union) per side
    c, r = np.array(TURRET['c']), TURRET['r']
    d = np.sqrt((X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2)
    F = np.maximum(F, np.clip(0.5 + (r - d) / (2 * vs), 0.0, 1.0))
    return F.astype(np.float32)


def belly_x(z):
    """Half width of the reference belly (front view) at height z."""
    P = [(0.0, 0.0), (0.040, 0.0), (0.042, 0.03), (0.05, 0.05), (0.065, 0.062), (0.085, 0.070), (0.137, 0.075), (0.2, 0.08)]
    for (z0, x0), (z1, x1) in zip(P, P[1:]):
        if z <= z1:
            return x0 + (x1 - x0) * max(0.0, (z - z0)) / (z1 - z0)
    return P[-1][1]


# ---------------------------------------------------------------- colour borders (stage 2 cuts)
def _pl(a, b, side, ax=(1, 2)):
    """Plane through view points a, b (coords on axes ax, e.g. (y, z)); normal in that plane toward `side`."""
    d0, d1 = b[0] - a[0], b[1] - a[1]
    n = [0.0, 0.0, 0.0]; n[ax[0]], n[ax[1]] = -d1, d0
    n = Vector(n).normalized()
    p = [0.0, 0.0, 0.0]; p[ax[0]], p[ax[1]] = a
    s = [0.0, 0.0, 0.0]; s[ax[0]], s[ax[1]] = side
    p, s = Vector(p), Vector(s)
    if n.dot(s - p) < 0:
        n = -n
    return p, n


CUTS = {
    # name: (plane (positive side = cream), region of faces the plane may cut)
    'jaw':    (_pl((-0.195, 0.228), (-0.06, 0.197), (-0.1, 0.0)), lambda c: c.y < -0.03 and 0.15 < c.z < 0.26),
    'throat': (_pl((-0.06, 0.205), (0.07, 0.035), (-0.2, 0.0)), lambda c: -0.10 < c.y < 0.10 and c.z < 0.23),
    'flank':  (_pl((0.109, 0.2), (0.07, 0.05), (0.0, 0.1), ax=(0, 2)), lambda c: c.y < 0.09 and c.z < 0.215 and 0.04 < c.x < 0.13),
}


def side_of(name, c):
    (p, n), _ = CUTS[name]
    return (Vector(c) - p).dot(n) > 0


def cut(k, bm, name, snap=0.004):
    (p, n), region = CUTS[name]
    faces = [f for f in bm.faces if region(f.calc_center_median())]
    verts = {v for f in faces for v in f.verts}
    for v in verts:                                # vertices near the plane go onto it (no slivers)
        d = (v.co - p).dot(n)
        if abs(d) < snap and abs(v.co.x) > 1e-6:
            v.co -= n * d
        elif abs(d) < snap:
            v.co -= Vector((0.0, n.y, n.z)) * d / max(1e-6, n.y * n.y + n.z * n.z)
    edges = {e for f in faces for e in f.edges}
    with k.topo(bm, 'loop', f'colour border {name}: a bisect plane cut, the paint border runs on its edge path'):
        bmesh.ops.bisect_plane(bm, geom=faces + list(edges) + list(verts), plane_co=p, plane_no=n, dist=1e-5)


MOVED = []


def stage2(k, body):
    bm = edit(body)
    # ---- throat: the hull sets the throat sides back under the jaw, a dark shelf in az000/hero; the
    # reference throat is a cream bulge flush with the lower lip. Bring them forward onto the seam's
    # front profile (slightly rounded back toward the sides).
    prof = [(0.06, -0.06), (0.115, -0.10), (0.172, -0.136), (0.182, -0.141), (0.2, -0.164), (0.212, -0.181)]
    def yseam(z):
        for (z0, y0), (z1, y1) in zip(prof, prof[1:]):
            if z <= z1:
                return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
        return prof[-1][1]
    for v in bm.verts:
        c = v.co
        if c.y < -0.04 and 0.12 < c.z < 0.206 and 0.0 < c.x < 0.105:
            yt = yseam(c.z) + 0.9 * c.x * c.x
            if c.y > yt:
                w = min(1.0, (c.z - 0.12) / 0.025)
                c.y += (yt - c.y) * w
                MOVED.append(tuple(round(q, 3) for q in c))
    say('FROG throat moved %d' % len(MOVED))
    # ---- throat and chest: the hull's front is a stair of horizontal terraces (az000); relax it into
    # one convex ball (vertex moves only, seam verts stay on x = 0)
    zone = [v for v in bm.verts if v.co.y < -0.02 and 0.06 < v.co.z < 0.212 and v.co.x < 0.085]
    for _ in range(8):
        bmesh.ops.smooth_vert(bm, verts=[v for v in zone if v.co.x > 1e-6], factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bmesh.ops.smooth_vert(bm, verts=[v for v in zone if v.co.x <= 1e-6], factor=0.5,
                              use_axis_x=False, use_axis_y=True, use_axis_z=True)
    for name in CUTS:
        cut(k, bm, name)
    snap_seam(bm, 1e-6)
    commit(body, bm)


PAL = {'skin': '#5fae3c', 'spot': '#2f6b2a', 'belly': '#efe0b0', 'eye': '#f2c230', 'pupil': '#151515', 'tongue': '#d8677a'}


# spots: whole carve triangles painted dark (the carve's irregular triangles give polygonal blobs like
# the reference's), picked by face centre: top-view spots (x, y, r) on up-facing faces, flank spots
# (y, z, r) on side-facing faces. x >= 0 half; the mirror repeats them.
SPOTS_TOP = [(0.0, 0.005, 0.036), (0.045, 0.085, 0.034), (0.085, 0.045, 0.030), (0.055, -0.012, 0.026),
             (0.095, -0.035, 0.020), (0.035, -0.062, 0.018)]
SPOTS_SIDE = [(0.060, 0.175, 0.026), (0.125, 0.165, 0.020), (0.000, 0.205, 0.016)]


def body_rule(c, n, i):
    if side_of('jaw', c) and side_of('throat', c) and side_of('flank', c):
        return 'belly'
    ax = abs(c.x)
    if c.z > 0.14 and n.z > 0.3 and any((ax - x) ** 2 + (c.y - y) ** 2 < r * r for x, y, r in SPOTS_TOP):
        return 'spot'
    if c.z > 0.14 and abs(n.x) > 0.5 and any((c.y - y) ** 2 + (c.z - z) ** 2 < r * r for y, z, r in SPOTS_SIDE):
        return 'spot'
    return 'skin'


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


def hind_toe(bm, root, tip, w, sw=1.5, sd=1.3):
    """A thick toe (sw x the old width, sd x the depth) ending in a 6-sided, flattened round pad
    about 2x the toe width, sunk 30% into the toe tip."""
    d = (tip - root).normalized()
    L = (tip - root).length
    rs = [sec(root, d, w * 1.2 * sw, w * 0.8 * sd, 4, 45), sec(root + d * (L * 0.5), d, w * 1.05 * sw, w * 0.75 * sd, 4, 45),
          sec(tip - d * 0.002, d, w * 0.8 * sw, w * 0.6 * sd, 4, 45)]
    vs = [ring(bm, r) for r in rs]
    for x, y in zip(vs, vs[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, list(reversed(vs[0]))); cap(bm, vs[-1])
    R = 2 * (w * 0.8 * sw * 0.707)                    # pad radius = the toe tip's full width
    pc = tip - d * 0.002 + d * (R * 0.4)              # 30% of the pad's diameter overlaps the toe
    pc.z = 0.0036
    side = Vector((-d.y, d.x, 0)).normalized()
    hx = lambda r_, z: [pc + (d * math.cos(math.pi * j / 3) + side * math.sin(math.pi * j / 3)) * r_ + Vector((0, 0, z)) for j in range(6)]
    pr = [ring(bm, hx(R * 0.65, -0.0029)), ring(bm, hx(R, 0.0)), ring(bm, hx(R * 0.65, 0.0029))]
    for x, y in zip(pr, pr[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, list(reversed(pr[0]))); cap(bm, pr[-1])


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



def mouth_path(body):
    """The jaw cut's edge path on the +X half, from the seam round the snout to the mouth corner."""
    (p, n), region = CUTS['jaw']
    bm = edit(body)
    on = lambda v: abs((v.co - p).dot(n)) < 2e-5 and region(v.co)
    adj = {}
    for e in bm.edges:
        a, b = e.verts
        if on(a) and on(b):
            adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    start = min((v for v in adj if abs(v.co.x) < 1e-6), key=lambda v: v.co.y)
    path, prev, cur = [start.co.copy()], None, start
    while True:
        nxt = [w for w in adj[cur] if w is not prev and w.co.x > cur.co.x - 0.02 and w.co.copy() not in path]
        if not nxt:
            break
        prev, cur = cur, max(nxt, key=lambda w: (w.co - start.co).length)
        path.append(cur.co.copy())
    bm.free()
    return path


TURRET_C = Vector(TURRET['c'])
GAZE = Vector((0.5, -0.85, 0.05)).normalized()


def stage3(k, body):
    paint(body, PAL, body_rule)
    say('FROG spot faces %d' % sum(1 for p in body.data.polygons if body.data.materials[p.material_index].name.startswith('spot')))
    eb = evaluated_bm(body)
    tree = BVHTree.FromBMesh(eb)
    pieces = []
    # ---- eyes: a gold low-poly ball on the front-outer face of each turret, a horizontal black pupil bar
    bm = bmesh.new()
    c = TURRET_C + Vector((0.45, -0.8, 0.40)).normalized() * 0.017
    r, lats, nl = 0.025, (-60, -12, 12, 44.4, 71.8), 12
    rings_ = [ring(bm, [c + V3(r * math.cos(math.radians(la)) * math.cos(2 * math.pi * j / nl),
                               r * math.cos(math.radians(la)) * math.sin(2 * math.pi * j / nl),
                               r * math.sin(math.radians(la))) for j in range(nl)]) for la in lats]
    for x, y in zip(rings_, rings_[1:]):
        bridge(bm, x, y, closed=True)
    sp, np_ = bm.verts.new(c + V3(0, 0, -r)), bm.verts.new(c + V3(0, 0, r))
    for j in range(nl):
        bm.faces.new([rings_[0][(j + 1) % nl], rings_[0][j], sp]); bm.faces.new([rings_[-1][j], rings_[-1][(j + 1) % nl], np_])
    eye = object_from_bm('eye', bm)
    def eye_rule(q, n, i):
        g = Vector((GAZE.x * (1 if q.x > 0 else -1), GAZE.y, GAZE.z))
        h = Vector((n.x, n.y, 0)).normalized() if abs(n.z) < 0.99 else Vector()
        return 'pupil' if abs(n.z) < 0.3 and h.dot(Vector((g.x, g.y, 0)).normalized()) > 0.80 else 'eye'
    paint(eye, PAL, eye_rule)
    pieces.append(eye)
    # ---- mouth: a black square tube along the jaw cut, half sunk into the skin, one piece across the seam
    half = mouth_path(body)
    say('FROG mouth path %d pts %s .. %s' % (len(half), tuple(round(q, 3) for q in half[0]), tuple(round(q, 3) for q in half[-1])))
    pts = [Vector((-q.x, q.y, q.z)) for q in reversed(half[1:])] + half
    bm = bmesh.new(); rs = []
    for i, q in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        loc, nor, _, _ = tree.find_nearest(q)
        nor = (nor - t * nor.dot(t)).normalized()
        u = t.cross(nor).normalized()
        w = 0.0028 if 0 < i < len(pts) - 1 else 0.0016
        o = q + nor * 0.0006
        rs.append(ring(bm, [o + nor * w + u * w, o - nor * w + u * w, o - nor * w - u * w, o + nor * w - u * w]))
    for x, y in zip(rs, rs[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, list(reversed(rs[0]))); cap(bm, rs[-1])
    mouth = object_from_bm('mouth', bm, mirror=False)
    paint(mouth, PAL, lambda q, n, i: 'pupil')
    pieces.append(mouth)
    # ---- front fingers: four splayed fingers with round pad tips, rooted in the hand pad
    bm = bmesh.new()
    for root, tip in fan(HAND, (0.2, -1, 0), (-0.016, -0.006, 0.005, 0.015), (-38, -12, 12, 38),
                         (0.042, 0.050, 0.050, 0.042), 0.0058, 0.010):
        toe(bm, root, tip, 0.0058)
    fingers = object_from_bm('fingers', bm); paint(fingers, PAL, lambda q, n, i: 'skin'); pieces.append(fingers)
    # ---- hind toes: five long toes forward off the foot paddle, webbed to WEB_L of their length
    bm = bmesh.new()
    tt = fan(FOOT, (0.25, -1, 0), (-0.022, -0.011, 0.0, 0.011, 0.022), (-30, -13, 3, 18, 34),
             (0.050, 0.062, 0.070, 0.062, 0.052), 0.0045, 0.009)
    for root, tip in tt:
        hind_toe(bm, root, tip, 0.0045)
    for (r0, t0), (r1, t1) in zip(tt, tt[1:]):
        B_, D_ = r0.lerp(t0, WEB_L), r1.lerp(t1, WEB_L)
        C_ = ((B_ + D_) / 2).lerp((r0 + r1) / 2, 0.12)
        slab(bm, [r0, B_, C_, D_, r1], t=0.0025)
    toes = object_from_bm('toes', bm); paint(toes, PAL, lambda q, n, i: 'skin'); pieces.append(toes)
    # ---- tongue: a 6-sided pink tube folded inside the head, root first; only its pad tip touches
    # the snout front at the mouth line (it lashes out in the attack clip)
    loc, nor, _, _ = tree.ray_cast(Vector((0.0, -0.12, 0.225)), Vector((0, -1, 0)))
    yt = loc.y + 0.0004
    say('FROG tongue tip surface y %.4f' % loc.y)
    ts = [((-0.105, 0.205), 0.010, 0.0055), ((-0.122, 0.209), 0.011, 0.006), ((-0.14, 0.213), 0.011, 0.006),
          ((yt + 0.024, 0.219), 0.0095, 0.0055), ((yt + 0.0105, 0.2235), 0.009, 0.005),
          ((yt + 0.005, 0.2245), 0.0145, 0.0075), ((yt + 0.0014, 0.225), 0.0140, 0.0072), ((yt, 0.225), 0.0080, 0.0040)]
    bm = bmesh.new()
    order = [0, 1, len(ts) - 1] + list(range(2, len(ts) - 1))
    made = {i: ring(bm, sec(V3(0, ts[i][0][0], ts[i][0][1]), (0, -1, 0.3), ts[i][1], ts[i][2], 6, 0)) for i in order}
    tv = [made[i] for i in range(len(ts))]
    for x, y in zip(tv, tv[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, list(reversed(tv[0]))); cap(bm, tv[-1])
    tongue = object_from_bm('tongue', bm, mirror=False)
    paint(tongue, PAL, lambda q, n, i: 'tongue'); pieces.append(tongue)
    eb.free()
    return pieces


HAND = (0.100, -0.108, 0.008)      # hand pad front centre (carve: x 0.071-0.13, y -0.117..-0.053)
FOOT = (0.148, 0.048, 0.008)       # foot paddle front centre (carve: x 0.111-0.18, y 0.038..0.166)
WEB_L = 0.62


# the skeleton, read off the carved base (the MASK polygons, the turret, the jaw cut)
J = dict(
    root=(0.0, 0.13, 0.11), chest=(0.0, -0.02, 0.15), neck=(0.0, -0.075, 0.20),
    head0=(0.0, -0.07, 0.236), head1=(0.0, -0.172, 0.256), jaw0=(0.0, -0.06, 0.19), jaw1=(0.0, -0.172, 0.218),
    tg0=(0.0, -0.13, 0.212), tg1=(0.0, -0.165, 0.221), tg2=(0.0, -0.183, 0.225),
    eye0=TURRET['c'], eyetop=(TURRET['c'][0], TURRET['c'][1] - 0.002, TURRET['c'][2] + 0.035),
    shoulder=(0.095, -0.076, 0.120), elbow=(0.096, -0.074, 0.066), wrist=(0.097, -0.072, 0.026),
    hand=(0.100, -0.108, 0.008),
    hip=(0.06, 0.125, 0.11), knee=(0.142, 0.050, 0.085), heel=(0.150, 0.178, 0.030), toe=(0.148, 0.050, 0.008),
)
TONGUE_SPLIT, TONGUE_SPLIT2 = -0.14, -0.168


def stage4(k, body, pieces):
    rig = armature([
        ('root', J['root'], J['chest'], None),
        ('chest', J['chest'], J['neck'], 'root', True),
        ('head', J['head0'], J['head1'], 'chest'),
        ('jaw', J['jaw0'], J['jaw1'], 'chest'),
        ('eye.L', J['eye0'], J['eyetop'], 'head'),
        ('tongue1', J['tg0'], J['tg1'], 'jaw'),
        ('tongue2', J['tg1'], J['tg2'], 'tongue1', True),
        ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
        ('thigh.L', J['hip'], J['knee'], 'root'),
        ('shin.L', J['knee'], J['heel'], 'thigh.L', True),
        ('foot.L', J['heel'], J['toe'], 'shin.L', True),
    ], roll='auto')
    for b in ('tongue1', 'tongue2'):
        rig.data.bones[b].use_deform = False          # the skin never follows the tongue
    skin(body, rig)
    for b in ('tongue1', 'tongue2'):
        rig.data.bones[b].use_deform = True
    # the long hind-foot paddle is rigid with the foot bone, so the rigid toes and webs stay seated on it
    fh, ft = Vector(J['heel']), Vector(J['toe'])
    sk, sh = Vector(J['knee']), Vector(J['heel'])

    def segd(p, a, b):
        t = max(0.0, min(1.0, (p - a).dot(b - a) / (b - a).length_squared))
        return (p - a.lerp(b, t)).length
    for v in body.data.vertices:
        q = Vector((abs(v.co.x), v.co.y, v.co.z))
        if q.x > 0.105 and q.z < 0.03 and q.y > 0.03 and segd(q, fh, ft) < segd(q, sk, sh):
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
    for v in tg.data.vertices:                         # sections 1-3 (y > -0.15) ride the jaw skin; the rest lash out
        if v.co.y < TONGUE_SPLIT:
            for g in list(tg.vertex_groups):
                g.remove([v.index])
            (g2 if v.co.y < TONGUE_SPLIT2 else g1).add([v.index], 1.0, 'REPLACE')
    TR = {'tongue1': (0, 0, 0), 'tongue2': (0, 0, 0)}  # the tongue keyed at rest (retracted) in idle and move
    # idle: throat pulse (jaw drops a little, twice) and a blink (eyes pull down into the head)
    clip(rig, 'idle', {1: {}, 8: {'jaw': (-4, 0, 0), 'chest': (1, 0, 0)}, 16: {}, 24: {'jaw': (-4, 0, 0), 'chest': (1, 0, 0)},
                       32: {}, 48: {}},
         loc={1: dict(TR), 36: {}, 40: {'eye.L': (0, -0.010, 0), 'eye.R': (0, -0.010, 0)}, 44: {}, 48: {}})
    # move: a hop - crouch, launch (legs extend, body pitches up), land
    crouch = {'root': (-6, 0, 0), 'thigh.L': (6, 0, 0), 'thigh.R': (6, 0, 0)}
    launch = {'root': (12, 0, 0), 'thigh.L': (-8, 0, 0), 'thigh.R': (-8, 0, 0), 'shin.L': (-18, 0, 0), 'shin.R': (-18, 0, 0)}
    land = {'root': (-4, 0, 0)}
    clip(rig, 'move', {1: {}, 5: crouch, 11: launch, 17: land, 24: {}},
         loc={1: dict(TR), 5: {'root': (0, 0, -0.008), **TR}, 11: {'root': (0, 0.03, 0.05), **TR}, 17: {'root': (0, 0.05, 0.0), **TR}, 24: dict(TR)})
    # attack: tongue lash - lean in, jaw drops, tongue shoots out and snaps back
    clip(rig, 'attack', {1: {}, 6: {'chest': (-6, 0, 0), 'head': (4, 0, 0)}, 10: {'chest': (-8, 0, 0), 'jaw': (-14, 0, 0)},
                         14: {'chest': (-8, 0, 0), 'jaw': (-14, 0, 0)}, 19: {'chest': (-3, 0, 0), 'jaw': (-3, 0, 0)}, 24: {}},
         loc={1: {}, 8: {}, 11: {'tongue1': (0, 0.09, 0), 'tongue2': (0, 0.06, 0)}, 14: {'tongue1': (0, 0.09, 0), 'tongue2': (0, 0.06, 0)},
              18: {}, 24: {}})
    return rig




run(META, stage1, stage2, stage3, stage4)
