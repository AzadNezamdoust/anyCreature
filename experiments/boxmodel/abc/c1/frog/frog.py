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
    key = hashlib.sha256(repr((MASK, CARVE, BELLY, TURRET, belly_x.__code__.co_consts, REAR, rear_cut.__code__.co_consts)).encode()).hexdigest()
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
    F = rear_cut(F, X, Y, Z, vs)
    return F.astype(np.float32)


# ---- rear (team notes must-fix 1, STAGE-1 UNLOCK): the hull's rear is a crate (front mask x top mask
# extrude two square haunches with vertical outer walls, square floor corners and a flat back). The
# reference rear is one round dome (falling toward the rear wall) with two smaller rounded thigh lobes
# beside it and light between belly and thigh at the floor. A 3D cut behind y 0.035: nothing outside
# body-egg U thigh-lobe U foot-paddle. Only removes occupancy; the side mask is untouched.
REAR = dict(y0=0.02, fade=0.02, bw=0.11, by0=0.05, by1=0.145, bzc=0.06, bzb=0.07,
            ztop=((0.06, 0.235), (0.19, 0.08)), zexp=1.5,
            xo=((0.03, 0.20), (0.05, 0.16), (0.15, 0.142), (0.175, 0.13), (0.195, 0.10)),
            xi=((0.05, 0.095), (0.19, 0.07)), tz=0.07, trz=0.088, tilt=28.0,
            foot=(0.11, 0.185, 0.032))


def rear_cut(F, X, Y, Z, vs):
    R = REAR
    wr = np.clip((Y - R['y0']) / R['fade'], 0.0, 1.0)
    yy = Y[0, :, 0]
    # body egg: plan half-width xb(y), (x,z) ellipse whose top falls toward the rear wall
    xb = R['bw'] * np.sqrt(np.clip(1.0 - (np.maximum(yy - R['by0'], 0.0) / R['by1']) ** 2, 1e-4, 1.0))
    (ya, za), (yb, zb) = R['ztop']
    zl = za - (za - zb) * np.clip((yy - ya) / (yb - ya), 0.0, 1.0) ** R['zexp']
    xb, zl = xb[None, :, None], zl[None, :, None]
    zc = R['bzc']
    qz = np.where(Z > zc, (Z - zc) / (zl - zc), (zc - Z) / R['bzb'])
    q = np.sqrt((X / xb) ** 2 + qz ** 2)
    s_body = (1.0 - q) * np.minimum(xb, 0.08)
    # thigh lobe: (x,z) ellipse between xi(y) and xo(y)
    xo = np.interp(yy, *zip(*R['xo']))[None, :, None]
    xi = np.interp(yy, *zip(*R['xi']))[None, :, None]
    xt, rx = (xo + xi) / 2, np.maximum((xo - xi) / 2, 1e-3)
    # verify pass (item 1 NOT): an upright ellipse left vertical outer walls as tall as the belly. The
    # lobe section is tilted: its top leans in against the body, its outer face slopes down and out.
    ct, st = math.cos(math.radians(R['tilt'])), math.sin(math.radians(R['tilt']))
    U, Vv = (X - xt) * ct + (Z - R['tz']) * st, -(X - xt) * st + (Z - R['tz']) * ct
    q = np.sqrt((U / rx) ** 2 + (Vv / R['trz']) ** 2)
    s_thigh = (1.0 - q) * np.minimum(rx, R['trz'])
    # foot paddle lying on the ground beside the thigh
    fa, fb, fz = R['foot']
    s_foot = np.minimum(np.minimum(X - fa, fb - X), fz - Z)
    s = np.maximum(np.maximum(s_body, s_thigh), s_foot)
    G = np.clip(0.5 + s / (2 * vs), 0.0, 1.0)
    return np.minimum(F, np.maximum(G, 1.0 - wr))


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
    # side cream patch behind the foreleg: 'arm' = a vertical plane ~1 cm behind the foreleg's back,
    # 'side' = the patch's front-low edge from the throat seam to the floor in front of the thigh
    'arm':    (_pl((-0.042, 0.0), (-0.042, 0.3), (0.2, 0.0)), lambda c: 0.03 < c.x < 0.175 and -0.07 < c.y < -0.015 and 0.03 < c.z < 0.21),
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
                w = min(1.0, (c.z - 0.12) / 0.025) * max(0.0, min(1.0, (0.105 - c.x) / 0.02))   # fades out toward the shoulder (new base: a full move there folded 1 tri)
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
    def bmhits():
        t = BVHTree.FromBMesh(bm); bm.faces.ensure_lookup_table()
        return sum(1 for i, j in t.overlap(t) if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)))
    say('FROG pre-cut hits %d' % bmhits())
    for name in CUTS:
        cut(k, bm, name)
        say('FROG cut %s hits %d' % (name, bmhits()))
    snap_seam(bm, 1e-6)
    commit(body, bm)
    say('FROG s2 hits %s' % selfhits(body))


PAL = {'skin': '#5fae3c', 'spot': '#2f6b2a', 'belly': '#efe0b0', 'eye': '#f2c230', 'pupil': '#151515', 'tongue': '#d8677a'}


# spots (team notes must-fix 2): painted carve triangles read as random dark facets; the reference
# has round spots of one size. Separate 6-sided disc pieces, every vertex projected onto the skin
# (+1 mm), a sunk apex below: (axis, a, b) = cast down at (x, y) for 'top', in from +X at (y, z)
# for 'side'. x >= 0 half; the mirror repeats them.
SPOT_R = 0.017
SPOTS = [('top', 0.040, -0.030), ('top', 0.045, 0.062), ('top', 0.040, 0.125),
         ('side', -0.012, 0.178), ('side', 0.075, 0.180), ('top', 0.118, 0.120)]


def spot_disc(bm, tree, kind, a, b, r=SPOT_R, k=6, lift=0.0015):
    """Verify pass (item 2 PARTLY): discs projected vertex-by-vertex onto the facets came out in
    different sizes with slivers dipping under the skin. Now ONE planar regular hexagon per spot:
    the plane is fitted to the skin under the rim and lifted clear of every facet under it; a
    sunk apex cone below closes the piece into the skin."""
    if kind == 'top':
        o, d = Vector((a, b, 0.6)), Vector((0, 0, -1))
    else:
        o, d = Vector((0.6, a, b)), Vector((-1, 0, 0))
    p, n, _, _ = tree.ray_cast(o, d)
    if p is None:
        say('FROG spot miss %s %.3f %.3f' % (kind, a, b)); return
    def hit(q, nn):
        h = tree.ray_cast(q + nn * 0.02, -nn, 0.04)[0]
        return h if h is not None else q
    def frame(nn):
        e1 = nn.cross(Vector((0, 0, 1)) if abs(nn.z) < 0.9 else Vector((1, 0, 0))).normalized()
        return e1, nn.cross(e1).normalized()
    for _ in range(2):                              # plane normal = fit to the skin under the rim
        e1, e2 = frame(n)
        hs = [hit(p + (e1 * math.cos(2 * math.pi * j / k) + e2 * math.sin(2 * math.pi * j / k)) * r, n) for j in range(k)]
        nn = Vector()
        for j in range(k):
            nn += (hs[j] - p).cross(hs[(j + 1) % k] - p)
        if nn.dot(n) < 0:
            nn = -nn
        n = nn.normalized()
    e1, e2 = frame(n)
    ring_ = lambda rr: [p + (e1 * math.cos(2 * math.pi * j / k) + e2 * math.sin(2 * math.pi * j / k)) * rr for j in range(k)]
    samp = [p] + ring_(r) + ring_(r * 0.5)
    h = max((hit(q, n) - q).dot(n) for q in samp) + lift
    low = min((hit(q, n) - q).dot(n) for q in samp)
    say('FROG spot %s %.3f %.3f hover max %.1f mm' % (kind, a, b, (h - low) * 1000))
    vc, va = bm.verts.new(p + n * h), bm.verts.new(p + n * (low - 0.012))
    rv = [bm.verts.new(q + n * h) for q in ring_(r)]
    for j in range(k):
        bm.faces.new([vc, rv[j], rv[(j + 1) % k]]); bm.faces.new([rv[(j + 1) % k], rv[j], va])


def body_rule(c, n, i):
    if side_of('jaw', c) and side_of('throat', c) and side_of('flank', c):
        return 'belly'
    # flank (team notes must-fix 5): one cream edge from the throat down behind the foreleg to the
    # floor in front of the thigh, on the 'arm' and 'side' cut edge paths
    # verify pass (item 5 PARTLY): the separate 'side' edge left a green wedge and a jagged lower end.
    # Now the flank patch shares the throat plane's edge path (one straight diagonal from the mouth
    # corner down to the thigh) and stops at the belly/thigh crease.
    if side_of('arm', c) and side_of('throat', c) and side_of('jaw', c) and c.z > 0.004 and not (c.y > 0.012 and abs(c.x) > 0.085):
        return 'belly'
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
    rs = [sec(root, d, w * 1.2, w * 0.8, 4, 45), sec(tip - d * 0.009, d, w * 0.8, w * 0.6, 4, 45),   # (budget: no mid ring)
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
    rs = [sec(root, d, w * 1.2 * sw, w * 0.8 * sd, 4, 45),                       # (budget: no mid ring)
          sec(tip - d * 0.002, d, w * 0.8 * sw, w * 0.6 * sd, 4, 45)]
    vs = [ring(bm, r) for r in rs]
    for x, y in zip(vs, vs[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, list(reversed(vs[0]))); cap(bm, vs[-1])
    R = 1.2 * 2 * (w * 0.8 * sw * 0.707)              # pad radius = 1.2 x the toe tip's full width (team should-fix)
    pc = tip - d * 0.002 + d * (R * 0.4)              # 30% of the pad's diameter overlaps the toe
    pc.z = 0.0036
    side = Vector((-d.y, d.x, 0)).normalized()
    hx = lambda r_, z: [pc + (d * math.cos(math.pi * j / 3) + side * math.sin(math.pi * j / 3)) * r_ + Vector((0, 0, z)) for j in range(6)]
    pr = [ring(bm, hx(R, -0.0029)), ring(bm, hx(R, 0.0029))]   # a 6-sided prism (budget: 20 tris, was 32)
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
MOUTH_END = -0.075                # the mouth line ends under the back of the eye
TONGUE_IN = 0.014                  # idle/move key the tongue 14 mm back inside the snout (no pink at idle)
EYE_C, EYE_R = (0.089, -0.116, 0.288), 0.037
GAZE = Vector((0.5, -0.85, 0.05)).normalized()


def stage3(k, body):
    paint(body, PAL, body_rule)
    eb = evaluated_bm(body)
    tree = BVHTree.FromBMesh(eb)
    pieces = []
    bm = bmesh.new()
    for sp_ in SPOTS:
        spot_disc(bm, tree, *sp_)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    spots = object_from_bm('spots', bm); paint(spots, PAL, lambda q, n, i: 'spot'); pieces.append(spots)
    # ---- eyes: a gold low-poly ball on the front-outer face of each turret, a horizontal black pupil bar
    bm = bmesh.new()
    # team notes must-fix 3: x1.5 (r 0.025 -> 0.037), rises 1/3 of its diameter above the turret top
    # (0.300), 0.7 cm outboard, so it breaks the skull outline from the front and the side
    c = Vector(EYE_C)
    r, lats, nl = EYE_R, (-60, -12, 12, 44.4, 71.8), 10
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
    # team notes must-fix 4: the path stops at the snout corner; the reference mouth runs back under
    # the eye. Continue it on the jaw plane's border (the paint border) by casting in from +X.
    (jp, jn), _ = CUTS['jaw']
    zj = lambda y: jp.z - (jn.y * (y - jp.y)) / jn.z
    y = half[-1].y + 0.012
    while y <= MOUTH_END + 1e-6:
        hit = tree.ray_cast(Vector((0.5, y, zj(y))), Vector((-1, 0, 0)))[0]
        if hit is not None and hit.x > half[-1].x - 0.02:
            half.append(hit)
        y += 0.012
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
          ((yt + 0.005, 0.2245), 0.0120, 0.0060), ((yt + 0.0014, 0.225), 0.0115, 0.0058), ((yt, 0.225), 0.0080, 0.0040)]
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
    # verify pass (tongue stretch 5.55x): the lash was taken by two ring gaps. Graded weights spread it
    # evenly over the four gaps behind the pad (ring y -0.122 / -0.14 / -0.164 / -0.178 and the tip).
    gj = tg.vertex_groups.get('jaw') or tg.vertex_groups.new(name='jaw')
    for v in tg.data.vertices:
        y = v.co.y
        if y > -0.1135:
            continue                                    # root ring rides the jaw skin
        w1, w2 = (0.39, 0.0) if y > -0.131 else (0.80, 0.0) if y > -0.152 else (0.48, 0.52) if y > -0.171 else (0.0, 1.0)
        for g in list(tg.vertex_groups):
            g.remove([v.index])
        for g, w in ((gj, 1.0 - w1 - w2), (g1, w1), (g2, w2)):
            if w > 1e-6:
                g.add([v.index], w, 'REPLACE')
    TR = {'tongue1': (0, -TONGUE_IN, 0), 'tongue2': (0, 0, 0)}  # retracted TONGUE_IN in idle and move (bone +Y = out)
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
         loc={1: {}, 8: {}, 11: {'tongue1': (0, 0.085, 0), 'tongue2': (0, 0.057, 0)}, 14: {'tongue1': (0, 0.085, 0), 'tongue2': (0, 0.057, 0)},
              18: {}, 24: {}})
    return rig




run(META, stage1, stage2, stage3, stage4)
