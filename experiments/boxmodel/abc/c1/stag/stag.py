import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet, load_ref
import numpy as np

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull), then hand detail
META = dict(creature='stag', model='opus', engine_glb='')


# ---------------------------------------------------------------- carve input edits (side mask)
# Read off reference/side.png on a 0.05 m grid (side-view metres (y, z)).
# 1. The antlers: a visual hull of thin branching tines is a blob; the hull is cut at the skull top
#    and the antlers are built as rooted pieces in stage 3 (the ear stays in the mask).
# 2. The legs: the sheet shows the near and far legs staggered (two hind legs per side in the side
#    view); each leg zone is cleared and redrawn as ONE designed leg (as the wolf did).
SIDE_CLEAR = [
    # antlers and ears above the skull line (the poll, then the mane line down the back of the neck)
    [(-0.85, 1.80), (0.15, 1.80), (0.15, 1.10), (-0.25, 1.10), (-0.30, 1.20), (-0.38, 1.262), (-0.45, 1.29),
     (-0.53, 1.295), (-0.85, 1.295)],
    # foreleg zone
    [(-0.36, 0.53), (-0.06, 0.53), (-0.06, -0.01), (-0.36, -0.01)],
    # hind leg zone (both staggered legs), below the stifle/belly
    [(0.26, 0.56), (0.62, 0.56), (0.66, 0.52), (0.76, 0.52), (0.76, -0.01), (0.26, -0.01)],
]
SIDE_DRAW = [
    # foreleg: forearm under the elbow, a small forward knee (carpus), cannon, fetlock, hoof
    # (stylised: ~25% deeper than the sheet's slim legs so the low-poly column survives decimation)
    [(-0.285, 0.56), (-0.272, 0.45), (-0.262, 0.36), (-0.258, 0.31), (-0.252, 0.20), (-0.250, 0.115),
     (-0.258, 0.075), (-0.305, 0.012), (-0.310, 0.0), (-0.212, 0.0), (-0.200, 0.040), (-0.180, 0.090),
     (-0.186, 0.20), (-0.188, 0.30), (-0.176, 0.35), (-0.160, 0.45), (-0.130, 0.52), (-0.090, 0.56)],
    # hind leg (the near leg of the sheet): thigh, stifle forward, shin back to a pointed hock,
    # near-vertical cannon, fetlock, hoof
    [(0.350, 0.60), (0.450, 0.50), (0.520, 0.440), (0.555, 0.380), (0.590, 0.300), (0.606, 0.200),
     (0.616, 0.120), (0.612, 0.070), (0.585, 0.012), (0.582, 0.0), (0.680, 0.0), (0.680, 0.050),
     (0.695, 0.090), (0.695, 0.20), (0.698, 0.330), (0.712, 0.405), (0.690, 0.460), (0.668, 0.520),
     (0.645, 0.60)],
]


def _inside(P, Y, Z):
    P = np.array(P)
    ins = np.zeros(Y.shape, bool)
    for i in range(len(P)):
        (y1, z1), (y2, z2) = P[i], P[i - 1]
        c = ((z1 > Z) != (z2 > Z)) & (Y < (y2 - y1) * (Z - z1) / (z2 - z1 + 1e-12) + y1)
        ins ^= c
    return ins


# The plan (top) view hides the legs under the body, and its rump tapers to the tail: the hull cut
# the hind cannons off where the plan narrows (r02). Leg footprints (x, y) are added to the plan.
TOP_DRAW = [
    [(0.045, -0.32), (0.150, -0.32), (0.150, -0.08), (0.045, -0.08)],      # foreleg column
    [(0.045, 0.34), (0.150, 0.34), (0.150, 0.60), (0.115, 0.715), (0.045, 0.715)],  # hind leg column (tapered: r05's square corner squared the rump)
]
# ears and antlers off the front and plan views: the hull fused them into a hammer across the
# head (r01-r03); the ears are stage-3 leaf pieces, the antlers stage-3 rooted pieces
FRONT_CLEAR = [
    [(0.085, 1.17), (0.6, 1.17), (0.6, 1.80), (0.085, 1.80)],
    [(0.0, 1.335), (0.6, 1.335), (0.6, 1.80), (0.0, 1.80)],
    # the mane's shaggy spread (+-0.17 at z 0.9) made the neck a column as wide as the chest with the
    # head poking out of it (r04 hero): the neck is carved slim, the mane is a stage-3 piece
    [(0.085, 1.171), (0.085, 1.10), (0.100, 1.00), (0.125, 0.90), (0.160, 0.80), (0.6, 0.80), (0.6, 1.171)],
]
TOP_CLEAR = [
    [(0.085, -0.85), (0.6, -0.85), (0.6, -0.36), (0.085, -0.36)],
    [(0.110, -0.36), (0.6, -0.36), (0.6, -0.26), (0.110, -0.26)],
]
FRONT_DRAW = []


def _world(v, R, C):
    """(a, b) world coords of crop pixel (R, C) in view v: side (y, z), front (x, z), top (x, y)."""
    if v.name == 'side':
        return (C + v.c0 - v.cmid) * v.s, (v.ground - v.r0 - R) * v.s
    if v.name == 'front':
        return (C + v.c0 - v.axis) * v.s, (v.ground - v.r0 - R) * v.s
    return (R + v.r0 - v.axis) * v.s, (C + v.c0 - v.cmid) * v.s


def _edit_mask(v, clear, draw, mirror=False):
    H, W = v.mask.shape
    R, C = np.mgrid[0:H, 0:W].astype(np.float64)
    A, Bc = _world(v, R, C)
    m = v.mask.copy()
    for P in clear:
        m[_inside(P, A, Bc)] = False
        if mirror:
            m[_inside(P, -A, Bc)] = False
    for P in draw:
        m[_inside(P, A, Bc)] = True
        if mirror:
            m[_inside(P, -A, Bc)] = True
    m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
    v.mask = m
    I = np.zeros((H + 1, W + 1), np.float64)
    I[1:, 1:] = m.astype(np.float64).cumsum(0).cumsum(1)
    v.I = I


def fix_masks(k):
    views = load_ref(k.dir)
    _edit_mask(views['side'], SIDE_CLEAR, SIDE_DRAW)
    _edit_mask(views['front'], FRONT_CLEAR, FRONT_DRAW, mirror=True)
    _edit_mask(views['top'], TOP_CLEAR, TOP_DRAW, mirror=True)


CARVE = dict(voxel_div=150, target_tris=(900, 1300))


def stage1(k):
    # carve_base's cache key does not see the mask edit: key it here (a changed polygon re-carves)
    import hashlib
    key = hashlib.sha256(repr((SIDE_CLEAR, SIDE_DRAW, TOP_CLEAR, TOP_DRAW, FRONT_CLEAR, FRONT_DRAW, CARVE)).encode()).hexdigest()
    kf, cf = os.path.join(k.dir, 'carve_mask.key'), os.path.join(k.dir, 'carve_base.json')
    if not os.path.exists(kf) or open(kf).read() != key:
        if os.path.exists(cf):
            os.remove(cf)
        open(kf, 'w').write(key)
    fix_masks(k)
    body = carve_base(k, **CARVE)
    bm = edit(body)
    fins = [e for e in bm.edges if len(e.link_faces) == 2 and all(abs(v.co.x) < 1e-6 for v in e.verts)]
    say('STAG seam fins', len(fins), [tuple(round(c, 3) for c in (e.verts[0].co + e.verts[1].co) / 2) for e in fins])
    if fins:
        r = bmesh.ops.subdivide_edges(bm, edges=fins, cuts=1)
        for v in [g for g in r['geom_inner'] if isinstance(g, bmesh.types.BMVert)]:
            v.co.x = 0.002
    # a face lying IN the seam plane (all verts on x = 0) is dropped by the mirror merge: a hole.
    # The ones the carve leaves are tiny (4 mm, under the chest): merge each into one vertex.
    for f in [f for f in bm.faces if all(abs(v.co.x) < 1e-6 for v in f.verts)]:
        if f.is_valid:
            c = f.calc_center_median()
            say('STAG seam face merged', tuple(round(x, 3) for x in c), round(f.calc_area(), 6))
            bmesh.ops.pointmerge(bm, verts=list(f.verts), merge_co=c)
    snap_seam(bm, 1e-6)
    bad = [e for e in bm.edges if len(e.link_faces) != 2 and not (len(e.link_faces) == 1 and all(abs(v.co.x) < 1e-6 for v in e.verts))]
    say('STAG bad edges', len(bad), [(len(e.link_faces), tuple(round(c, 3) for c in (e.verts[0].co + e.verts[1].co) / 2)) for e in bad][:12])
    commit(body, bm)
    eb = evaluated_bm(body)
    nm = [e for e in eb.edges if len(e.link_faces) != 2]
    say('STAG mirrored non-manifold', [(len(e.link_faces), tuple(round(c, 4) for c in e.verts[0].co), tuple(round(c, 4) for c in e.verts[1].co)) for e in nm])
    eb.free()
    return body


# ---------------------------------------------------------------- colour borders
# planes (point, normal, region) bisected into the base in stage 2 (logged as loops), so every border
# in stage 3 runs along an edge path, not the decimated hull's saw-tooth. Read off reference/side.png
# and front.png on a 0.05 m grid. region(c) is the face-centre box the border lives in.
def _pl(a, b, side):
    """Plane through side-view points a, b = (y, z); normal in the YZ plane toward `side` (y, z)."""
    dy, dz = b[0] - a[0], b[1] - a[1]
    n = Vector((0.0, -dz, dy)).normalized()
    if n.dot(Vector((0.0, side[0] - a[0], side[1] - a[1]))) < 0:
        n = -n
    return Vector((0.0, a[0], a[1])), n


def _plf(a, b, side):
    """Plane through front-view points a, b = (x, z); normal in the XZ plane toward `side` (x, z)."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    n = Vector((-dz, 0.0, dx)).normalized()
    if n.dot(Vector((side[0] - a[0], 0.0, side[1] - a[1]))) < 0:
        n = -n
    return Vector((a[0], 0.0, a[1])), n


CUTS = {
    'nose':   (_pl((-0.672, 1.06), (-0.680, 1.20), (-0.8, 1.1)), lambda c: c.y < -0.62 and c.z > 1.03),
    'jaw':    (_pl((-0.74, 1.112), (-0.50, 1.085), (-0.6, 0.9)), lambda c: -0.70 < c.y < -0.47 and 1.02 < c.z < 1.15),
    'manef':  (_pl((-0.53, 1.03), (-0.41, 1.29), (-0.3, 1.1)), lambda c: -0.58 < c.y < -0.32 and c.z > 0.98),
    'maneb':  (_pl((-0.48, 0.76), (-0.10, 0.99), (-0.4, 1.0)), lambda c: -0.53 < c.y < -0.04 and 0.70 < c.z < 1.06),
    'bib':    (_plf((0.065, 1.07), (0.0, 0.90), (0.0, 1.05)), lambda c: c.y < -0.40 and 0.86 < c.z < 1.10 and c.x < 0.10),
    'belly':  (_pl((-0.28, 0.585), (0.36, 0.615), (0.0, 0.4)), lambda c: -0.30 < c.y < 0.40 and 0.48 < c.z < 0.70),
    'rump':   (_pl((0.615, 0.90), (0.650, 0.58), (0.8, 0.7)), lambda c: c.y > 0.52 and c.z > 0.64),
    'shin':   (_pl((-1.0, 0.26), (1.0, 0.26), (0.0, 0.0)), lambda c: c.z < 0.36),   # team should-fix: was z 0.31 (dark from the knee read heavy)
    'hoof':   (_pl((-1.0, 0.058), (1.0, 0.058), (0.0, 0.0)), lambda c: c.z < 0.12),
    # team repair: the mane's lower edge on the chest is a V (front plane), its point ~55% of the way
    # from the throat (z 1.0) to the elbow (z 0.53); a cream diamond sits under the point
    # verify pass: the V was shallow (slope 0.6: a trapezoid with a notch); now slope 1.5, the arms run
    # from the point up to the neck's edge at the throat, so the mane tapers to mid-chest
    'manev':  (_plf((0.0, 0.74), (0.16, 0.98), (0.0, 1.0)), lambda c: c.y < -0.28 and 0.66 < c.z < 1.0),
    'chestlo': (_plf((0.0, 0.60), (0.05, 0.67), (0.0, 0.70)), lambda c: c.y < -0.28 and 0.55 < c.z < 0.71 and c.x < 0.09),
    'chesthi': (_plf((0.0, 0.74), (0.05, 0.67), (0.0, 0.60)), lambda c: c.y < -0.33 and 0.62 < c.z < 0.78 and c.x < 0.09),
}
SMALL_CUTS = ('shin', 'hoof', 'rump', 'chestlo', 'chesthi')


def side_of(name, c):
    (p, n), _ = CUTS[name]
    return (Vector(c) - p).dot(n) > 0


def in_cut(name, c):
    return CUTS[name][1](c) and side_of(name, c)


def cut(bm, name, snap=0.018):
    """Bisect the region with the plane; verts within `snap` go onto it first (no slivers);
    seam verts only slide when the plane keeps them on x = 0."""
    (p, n), region = CUTS[name]
    faces = [f for f in bm.faces if region(f.calc_center_median())]
    verts = {v for f in faces for v in f.verts}
    for v in verts:
        d = (v.co - p).dot(n)
        if abs(d) < snap and (abs(v.co.x) > 1e-6 or abs(n.x) < 1e-9):
            if abs(v.co.x) > 1e-6 and (v.co - n * d).x < 0.004:
                continue                     # a snap must not push a vertex onto or across the seam (open edges, r29)
            v.co -= n * d
    edges = {e for f in faces for e in f.edges}
    bmesh.ops.bisect_plane(bm, geom=faces + list(edges) + list(verts), plane_co=p, plane_no=n, dist=1e-5)


EYE = (0.062, -0.548, 1.195)                       # the eye socket centre (reference side: -0.55, 1.20)


def vn(bm, p, tol=0.004):
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < tol, f'no vertex at {p}: nearest {tuple(v.co)}'
    return v


def nudge(bm, moves):
    for p, d in moves:
        vn(bm, p).co += Vector(d)


def stage2(k, body):
    bm = edit(body)
    # ---- head: the hull's head is 0.10 wide at the eyes (the sheet's ~0.17): the cheeks and skull
    # widen 30%, tapering to 10% at the nose (the front view showed a blade of a face)
    for v in verts_where(bm, lambda c: c.y < -0.455 and c.z > 1.03 and c.x > 1e-6):
        t = min(1.0, max(0.0, (v.co.y + 0.70) / 0.12))         # 0 at the nose tip, 1 behind y -0.58
        v.co.x *= 1.10 + 0.20 * t
    # ---- the eye socket under a brow, a blunt nose
    ef = face_near(bm, EYE, n=(1, -0.3, 0.2))
    say('STAG eye face', tuple(round(c, 3) for c in ef.calc_center_median()), len(ef.verts), tuple(round(c, 2) for c in ef.normal))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the brow-cheek face; the eye piece sits in it'):
        inset(bm, [ef], 0.30, -0.008)
    # ---- colour borders as edge paths (see CUTS)
    for name in CUTS:
        with k.topo(bm, 'loop', f'colour border {name}: a planar edge path (bisect) for a clean region border'):
            cut(bm, name, snap=0.014 if name == 'shin' else 0.008 if name in SMALL_CUTS else 0.018)
    snap_seam(bm, 1e-6)
    commit(body, bm)
    _hits(body)


def _hits(body):
    from mathutils.bvhtree import BVHTree
    eb = evaluated_bm(body)
    eb.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(eb)
    out = []
    for a, b in t.overlap(t):
        if a < b and not (set(eb.faces[a].verts) & set(eb.faces[b].verts)):
            out.append(tuple(round(x, 3) for x in eb.faces[a].calc_center_median()))
    say('STAG hits', len(out), out[:12])
    eb.free()



# ---------------------------------------------------------------- stage 3
BRIEF_PAL = {'body': '#8a5a3a', 'mane': '#6a4630', 'cream': '#d9c3a0', 'antler': '#d8c8a8',
             'antler_dk': '#7d5f45', 'hoof': '#231a16', 'eye': '#111111'}


def _hex(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def sheet_palette(k, body):
    """colour_from_sheet's clusters, mapped to the brief's roles: each role takes the nearest sheet
    cluster when it is close (the sheet's own tone), else the brief's hex."""
    got = colour_from_sheet(k, [body])
    say('STAG sheet clusters', got)
    pal = {}
    for role, h in BRIEF_PAL.items():
        best = min(got.values(), key=lambda g: np.linalg.norm(_hex(g) - _hex(h)))
        d = np.linalg.norm(_hex(best) - _hex(h))
        pal[role] = best if d < 40 and role not in ('eye', 'hoof', 'antler', 'antler_dk') else h
    say('STAG palette', pal)
    return pal


def body_rule(c, n, i):
    if in_cut('hoof', c):
        return 'hoof'
    if in_cut('nose', c):
        return 'hoof'
    if in_cut('shin', c):
        return 'mane'
    if in_cut('jaw', c):
        return 'cream'
    chest = c.y < -0.33 and 0.55 < c.z < 0.94 and n.y < -0.2       # the chest's front plane
    if chest and side_of('chestlo', c) and side_of('chesthi', c) and c.x < 0.06:
        return 'cream'                                             # the chest diamond under the mane's V
    mane_lo = in_cut('manev', c) if (c.y < -0.28 and 0.55 < c.z < 1.0) else side_of('maneb', c)   # the V holds on every chest/neck-front face, not only the front-facing ones
    if side_of('manef', c) and mane_lo and c.y < -0.04 and c.z > 0.70:
        if in_cut('bib', c) and n.y < -0.25:
            return 'cream'
        return 'mane'
    if in_cut('belly', c) and (c.y > -0.07 or c.x < 0.04):         # forelegs stay body-brown to the knee
        return 'cream'
    if in_cut('rump', c):
        return 'cream'
    return 'body'


def frame(t, up=Vector((0, 0, 1))):
    t = t.normalized()
    u = t.cross(up)
    if u.length < 1e-4:
        u = t.orthogonal()
    u.normalize()
    return t, u, u.cross(t).normalized()


def tube(bm, pts, radii, sides=5, flat=1.0, up=Vector((0, 0, 1)), tip=True):
    """A tapered tube along pts (radii per point); the last point is a sharp tip when tip=True.
    flat < 1 squashes the section along v."""
    rings = []
    n = len(pts) - (1 if tip else 0)
    for i in range(n):
        a = Vector(pts[i])
        t = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)]))
        _, u, v = frame(t, up)
        r = radii[i]
        rings.append(ring(bm, [a + u * (r * math.cos(2 * math.pi * j / sides)) + v * (r * flat * math.sin(2 * math.pi * j / sides))
                               for j in range(sides)]))
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rings[0])))
    if tip:
        tv = ring(bm, [Vector(pts[-1])])[0]
        r = rings[-1]
        for j in range(sides):
            bm.faces.new([r[j], r[(j + 1) % sides], tv])
    else:
        cap(bm, rings[-1])
    return rings


def taper(bm, pts, r0, r1, sides=5, flat=0.85, up=Vector((0, 0, 1)), tip_k=4.0, seg_k=4.5):
    """A horn/tine along the polyline pts, radius r0 -> r1 at the last ring, then a point tip_k * r1
    beyond it. Rings are spaced <= seg_k * edge so no side or tip triangle is a needle (< 6 deg)."""
    P = [Vector(p) for p in pts]
    seg = [(a - b).length for a, b in zip(P[1:], P)]
    Ltot = sum(seg)
    def at(sv):                                   # point and tangent at arc length sv
        acc = 0.0
        for i, l in enumerate(seg):
            if sv <= acc + l or i == len(seg) - 1:
                t = min(1.0, max(0.0, (sv - acc) / l))
                return P[i].lerp(P[i + 1], t), (P[i + 1] - P[i])
            acc += l
    e = 2 * math.sin(math.pi / sides)               # edge / radius
    Lb = Ltot - tip_k * r1                         # the last ring sits here
    ss, sv = [0.0], 0.0
    while True:
        r = r0 + (r1 - r0) * min(1.0, sv / Lb)
        sv += seg_k * e * r
        if sv >= Lb - 0.3 * seg_k * e * r:
            break
        ss.append(sv)
    ss.append(Lb)
    rings = []
    for sv in ss:
        c, t = at(sv)
        _, u, v = frame(t, up)
        r = r0 + (r1 - r0) * min(1.0, sv / Lb)
        rings.append(ring(bm, [c + u * (r * math.cos(2 * math.pi * j / sides)) + v * (r * flat * math.sin(2 * math.pi * j / sides))
                               for j in range(sides)]))
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rings[0])))
    tv = ring(bm, [at(Ltot)[0]])[0]
    for j in range(sides):
        bm.faces.new([rings[-1][j], rings[-1][(j + 1) % sides], tv])


def frame3(d, n):
    d = d.normalized()
    u = d.cross(n)
    if u.length < 1e-4:
        u = d.orthogonal()
    u.normalize()
    v = u.cross(d).normalized()
    if v.dot(n) < 0:
        v = -v
    return d, u, v


def shingle(bm, base, d, n, L, w, t, sink=0.45, sh=(0.45, 0.36)):
    """A fur lock: a thick root plate sunk into the skin, a broad shoulder ring, a blunt point."""
    d, u, v = frame3(Vector(d), n)
    b = base + v * (t / 2 - sink * t)
    q = ring(bm, [b + u * w / 2 + v * t / 2, b - u * w / 2 + v * t / 2, b - u * w / 2 - v * t / 2, b + u * w / 2 - v * t / 2])
    m = b + d * (sh[0] * L) + v * (0.30 * t)
    r = ring(bm, [m + u * sh[1] * w + v * 0.30 * t, m - u * sh[1] * w + v * 0.30 * t,
                  m - u * sh[1] * w - v * 0.30 * t, m + u * sh[1] * w - v * 0.30 * t])
    tip = ring(bm, [b + d * L + v * 0.25 * t])[0]
    bridge(bm, q, r, closed=True)
    for i in range(4):
        bm.faces.new([r[i], r[(i + 1) % 4], tip])
    bm.faces.new(list(reversed(q)))


def hug_lock(bm, tree, base, d0, L, w, t):
    """A fur lock lying on the skin: root plate (centre 2 mm under the skin), a broad shoulder ring
    at 45% (inner face ~2 mm over the skin), a blunt tip 4 mm over it; each station projected onto
    the body along the hint direction d0 (made tangent to the skin)."""
    def on_skin(p):
        loc, nor, _, _ = tree.find_nearest(p)
        return loc, nor.normalized()
    loc0, n0 = on_skin(base)
    d = (d0 - n0 * d0.dot(n0)).normalized()
    stations = []
    for s, off, hw, ht in [(0.0, -0.002, 0.5, 0.5), (0.45, 0.011, 0.42, 0.30)]:
        loc, nn = on_skin(loc0 + d * (s * L))
        dd = (d - nn * d.dot(nn)).normalized()
        u = dd.cross(nn).normalized()
        # each edge of the section is projected on its own, so the plate bends round the neck
        (pl, nl), (pr, nr) = on_skin(loc + u * hw * w), on_skin(loc - u * hw * w)
        stations.append(ring(bm, [pl + nl * (off + ht * t), pr + nr * (off + ht * t),
                                  pr + nr * (off - ht * t), pl + nl * (off - ht * t)]))
    tl, tn = on_skin(loc0 + d * L)
    tip = ring(bm, [tl + tn * 0.008])[0]
    q, r = stations
    bridge(bm, q, r, closed=True)
    for i in range(4):
        bm.faces.new([r[i], r[(i + 1) % 4], tip])
    bm.faces.new(list(reversed(q)))


def hit(tree, o, d):
    loc, nor, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
    assert loc is not None, f'no surface from {o} along {d}'
    return loc, nor


# the antler (left), read off the side, front and plan views: the beam from the burr up, back and
# out to the crown; forward brow and bez tines, an upright trez tine, a three-point crown
ANT_BEAM = [(0.040, -0.455, 1.255), (0.065, -0.450, 1.315), (0.115, -0.425, 1.370), (0.180, -0.350, 1.425),
            (0.235, -0.245, 1.480), (0.265, -0.150, 1.560), (0.300, -0.060, 1.680)]
ANT_BEAM_R = [0.024, 0.024, 0.021, 0.019, 0.017, 0.015, 0.0]
ANT_TINES = [  # (root beam index, root t toward next, tip, base radius)
    (1, 0.3, (0.120, -0.680, 1.440), 0.014),   # brow
    (2, 0.4, (0.170, -0.580, 1.480), 0.013),   # bez
    (3, 0.5, (0.215, -0.420, 1.570), 0.012),   # trez
    (5, 0.0, (0.205, -0.235, 1.675), 0.011),   # crown, inner
    (5, 0.4, (0.250, -0.155, 1.715), 0.010),   # crown, middle
]
ANT_SPREAD, ANT_PITCH = 0.60, 25.0   # tine x scale
ANT_XMAX = 0.165                     # verify pass: beam centre max x (az000 spread <= 1.6 head widths; 0.227 measured ~1.9)
EAR_UP, EAR_YAW, EAR_BACK = 28.0, -15.0, 0.03   # yaw < 0: back (forward put the ear through the thicker beam, r15)
EAR_ROOT, EAR_TIP = Vector((0.052, -0.430, 1.228)), Vector((0.215, -0.355, 1.335))


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    pal = sheet_palette(k, body)
    paint(body, {r: pal[r] for r in ('body', 'mane', 'cream', 'hoof')}, body_rule)
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)
    pieces = []

    # ---- eyes: a dark almond lens standing proud in the socket
    bm0 = edit(body)
    sf = face_near(bm0, EYE, n=(1, -0.3, 0.2))
    c, n = sf.calc_center_median(), sf.normal.copy()
    bm0.free()
    say('STAG socket', tuple(round(x, 3) for x in c), tuple(round(x, 2) for x in n))
    fa = Vector((0, -1, 0.15)); fa = (fa - n * fa.dot(n)).normalized(); fb = n.cross(fa).normalized()
    if fb.z < 0:
        fb = -fb
    # team repair: a round-almond dome ~0.032 x 0.026 m (was a 0.044 x 0.016 slit), its crown ~4 mm
    # proud of the face around the 8 mm socket
    ha, hb = 0.016, 0.015
    alm = [(-1.0, -0.05), (-0.62, 0.72), (0.0, 0.88), (0.62, 0.72), (1.0, 0.05), (0.55, -0.70), (-0.55, -0.72)]
    bm = bmesh.new()
    lo = ring(bm, [c + fa * (a * ha) + fb * (b * hb) - n * 0.003 for a, b in alm])
    mid = ring(bm, [c + fa * (a * ha * 0.95) + fb * (b * hb * 0.95) + n * 0.007 for a, b in alm])
    hi = ring(bm, [c + fa * (a * ha * 0.62) + fb * (b * hb * 0.62) + n * 0.012 for a, b in alm])
    bridge(bm, lo, mid, closed=True); bridge(bm, mid, hi, closed=True); cap(bm, list(reversed(lo))); cap(bm, hi)
    eye = object_from_bm('eyes', bm)
    paint(eye, {'eye': pal['eye']}, lambda cc, nn, i: 'eye')
    pieces.append(eye)

    # ---- ears: leaf blades, cupped (the inner face sunk), cream inside a body-colour rim
    bm = bmesh.new()
    d = (EAR_TIP - EAR_ROOT)
    # team repair: the ears stood out like wings: pitched up EAR_UP about the root, yawed EAR_YAW
    # forward, 15% shorter (the root stays sunk in the skull)
    h = Vector((d.x, d.y, 0.0))
    yaw = math.atan2(h.y, h.x) - math.radians(EAR_YAW)
    el = math.atan2(d.z, h.length) + math.radians(EAR_UP)
    d = Vector((math.cos(yaw) * math.cos(el), math.sin(yaw) * math.cos(el), math.sin(el))) * (d.length * 0.85)
    ear_root = EAR_ROOT + Vector((0.0, EAR_BACK, 0.008))
    ear_tip = ear_root + d
    say('STAG ear tip', tuple(round(x, 3) for x in ear_tip))
    L = d.length
    d.normalize()
    front = Vector((0.25, -1.0, 0.15)); front = (front - d * front.dot(d)).normalized()
    w = d.cross(front).normalized()
    secs = [(0.0, 0.020, 0.012), (0.30, 0.042, 0.016), (0.62, 0.040, 0.014), (0.86, 0.022, 0.010)]
    rings_ = []
    for s_, hw, th in secs:
        o = ear_root + d * (s_ * L) - front * 0.004
        rings_.append(ring(bm, [o + w * hw, o + w * 0.55 * hw + front * (0.2 * th), o - w * 0.55 * hw + front * (0.2 * th),
                                o - w * hw, o - w * 0.5 * hw - front * th, o + w * 0.5 * hw - front * th]))
    for a, b in zip(rings_, rings_[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rings_[0])))
    tv = ring(bm, [ear_tip])[0]
    for j in range(6):
        bm.faces.new([rings_[-1][j], rings_[-1][(j + 1) % 6], tv])
    ears = object_from_bm('ears', bm)
    paint(ears, {'body': pal['body'], 'cream': pal['cream']},
          lambda cc, nn, i: 'cream' if nn.dot(front) > 0.80 and (cc - ear_root).dot(d) < 0.80 * L else 'body')
    pieces.append(ears)

    # ---- antlers: beam + 5 tines, 5-sided, rooted in the skull
    # team repair (rake -> crown): the side spread is pulled in (x about the root * ANT_SPREAD) so the
    # front-view spread is ~1.6 head widths; tines pitched ANT_PITCH toward vertical (tips up, brow
    # still forward), 20% shorter; beam base radius +25%; the dark burr only on the beam's bottom 10%
    bm = bmesh.new()
    old = [Vector(p) for p in ANT_BEAM]
    x0 = old[0].x
    # verify pass: a lyre, not a V: the beam swings out early to ANT_XMAX and then rises (a linear
    # pull-in to the 1.6-head-width limit bunched beams and tines into two upright spikes, r25)
    xs = old[-1].x - x0
    beam = [Vector((x0 + (ANT_XMAX - x0) * (1 - (1 - (p.x - x0) / xs) ** 2), p.y, p.z)) for p in old]
    taper(bm, beam, 0.040, 0.011, sides=5, flat=0.8, seg_k=3.5)
    for bi, tt, tip, r0 in ANT_TINES:
        root0 = old[bi].lerp(old[bi + 1], tt)
        root = beam[bi].lerp(beam[bi + 1], tt)
        d = Vector(tip) - root0
        L = d.length * 0.80
        d.x *= ANT_SPREAD
        h = Vector((d.x, d.y, 0.0))
        a = min(math.radians(80), math.atan2(d.z, h.length) + math.radians(ANT_PITCH))
        dr = (h.normalized() * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)).normalized()
        say('STAG tine', bi, tuple(round(x, 3) for x in root), tuple(round(x, 2) for x in dr), round(L, 3))
        taper(bm, [root - dr * 0.012, root + dr * L], r0 * 1.5, 0.009, sides=5, flat=0.85, seg_k=3.2)   # verify pass: tines still thin
    ant = object_from_bm('antlers', bm)
    zb = beam[0].z + 0.10 * (beam[-1].z - beam[0].z) + 0.05      # the burr: the beam's bottom 10% above the skull
    paint(ant, {'antler': pal['antler'], 'antler_dk': pal['antler_dk']},
          lambda cc, nn, i: 'antler_dk' if cc.z < zb else 'antler')
    pieces.append(ant)

    # ---- mane: a jagged fringe of few, broad locks lying on the skin along the mane's lower
    # border (the neck itself is painted dark), hanging down and back over the shoulder; two
    # throat locks either side of the cream bib
    # team repair: the straight shingles stood off as cards where the shoulder falls away under the
    # neck (hero plate, az000 vest bars, back34 throat shard). Each lock now follows the skin: its
    # root, shoulder ring and tip are projected onto the body (find_nearest) and offset along the
    # local normal, root sunk, outer face <= ~15 mm off the skin. 3 locks per side, no throat lock.
    bm = bmesh.new()
    # (r31: the two shoulder locks are shorter and swept back, so the mane's front-view corners sit
    # high, at the shoulder, and the V below them is deep)
    for (y, z), L in [((-0.27, 0.89), 0.10), ((-0.19, 0.935), 0.10)]:
        loc, nor = hit(tree, (0.6, y, z + 0.035), (-1, 0, 0))
        hug_lock(bm, tree, loc, Vector((0.0, 0.9, -1.0)), L, 0.11, 0.018)
    # verify pass: the front lock sits on the V's arm (chest front) and hangs toward the V's point
    loc, nor = hit(tree, (0.085, -1.0, 0.885), (0, 1, 0))
    hug_lock(bm, tree, loc, Vector((-0.45, 0.0, -1.0)), 0.12, 0.08, 0.018)
    say('STAG lock skin offsets (m, max/verts>15mm)', round(max((v.co - tree.find_nearest(v.co)[0]).length for v in bm.verts), 4),
        [tuple(round(x, 3) for x in v.co) for v in bm.verts if (v.co - tree.find_nearest(v.co)[0]).length > 0.015])
    mane = object_from_bm('mane', bm)
    paint(mane, {'mane': pal['mane']}, lambda cc, nn, i: 'mane')
    pieces.append(mane)

    # ---- tail: a short hanging wedge from the rump top
    bm = bmesh.new()
    tp = [Vector((0.0, 0.660, 0.800)), Vector((0.0, 0.718, 0.765)), Vector((0.0, 0.746, 0.660)), Vector((0.0, 0.736, 0.530))]   # team should-fix: +20%, a slight hang
    tube(bm, tp, [0.030, 0.032, 0.026, 0.0], sides=6, flat=0.7, up=Vector((1, 0, 0)))
    tail = object_from_bm('tail', bm, mirror=False)
    paint(tail, {'mane': pal['mane']}, lambda cc, nn, i: 'mane')
    pieces.append(tail)
    ebm.free()
    return pieces



# ---------------------------------------------------------------- stage 4
# the skeleton, read off the carved base (the leg polygons of SIDE_DRAW, leg x from the hull)
J = dict(
    hip=(0.0, 0.55, 0.80), spine=(0.0, 0.15, 0.83), chest=(0.0, -0.20, 0.85),
    neck0=(0.0, -0.30, 0.92), neck1=(0.0, -0.42, 1.18), nose=(0.0, -0.68, 1.14),
    tail0=(0.0, 0.67, 0.80), tail1=(0.0, 0.73, 0.60),
    fsh=(0.10, -0.17, 0.75), felb=(0.10, -0.21, 0.53), fknee=(0.095, -0.22, 0.33),
    ffet=(0.095, -0.215, 0.10), fhoof=(0.095, -0.26, 0.01),
    hhip=(0.10, 0.50, 0.76), hstf=(0.10, 0.52, 0.46), hhock=(0.095, 0.665, 0.385),
    hfet=(0.095, 0.655, 0.09), hhoof=(0.095, 0.63, 0.01),
    ear0=(0.07, -0.40, 1.235), ear1=(0.123, -0.341, 1.38),   # team repair: follows the raised ear (r16)
)


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hip'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('neck', J['neck0'], J['neck1'], 'spine'),
        ('head', J['neck1'], J['nose'], 'neck', True),
        ('ear.L', J['ear0'], J['ear1'], 'head'),
        ('tail', J['tail0'], J['tail1'], 'hips'),
        ('upper.L', J['fsh'], J['felb'], 'spine'),
        ('fore.L', J['felb'], J['fknee'], 'upper.L', True),
        ('cannon.L', J['fknee'], J['ffet'], 'fore.L', True),
        ('pastern.L', J['ffet'], J['fhoof'], 'cannon.L', True),
        ('thigh.L', J['hhip'], J['hstf'], 'hips'),
        ('shin.L', J['hstf'], J['hhock'], 'thigh.L', True),
        ('hcannon.L', J['hhock'], J['hfet'], 'shin.L', True),
        ('hpastern.L', J['hfet'], J['hhoof'], 'hcannon.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: lower the head to graze (the pitch shared by neck and head), lift, flick an ear
    clip(rig, 'idle', {1: {}, 10: {'neck': (16, 0, 0), 'head': (-8, 0, 0)},
                       20: {'neck': (26, 0, 0), 'head': (-14, 0, 0)}, 26: {'neck': (26, 0, 0), 'head': (-10, 0, 0)},
                       34: {'neck': (12, 0, 0), 'head': (-4, 0, 0)}, 40: {'ear.L': (12, 0, 0), 'tail': (0, 0, 8)},
                       43: {'ear.L': (-5, 0, 0), 'ear.R': (9, 0, 0)}, 48: {}})
    # move: a diagonal-pair walk; the swinging leg folds at the knee / hock (swing kept small: the
    # mane fringe hangs over the shoulder)
    A, B = 12, -12
    clip(rig, 'move', {
        1: {'upper.L': (A, 0, 0), 'upper.R': (B, 0, 0), 'thigh.R': (A, 0, 0), 'thigh.L': (B, 0, 0)},
        7: {'fore.R': (-34, 0, 0), 'cannon.R': (-12, 0, 0), 'shin.L': (12, 0, 0), 'hcannon.L': (-24, 0, 0),
            'neck': (3, 0, 0), 'tail': (0, 0, 5)},
        13: {'upper.L': (B, 0, 0), 'upper.R': (A, 0, 0), 'thigh.R': (B, 0, 0), 'thigh.L': (A, 0, 0)},
        19: {'fore.L': (-34, 0, 0), 'cannon.L': (-12, 0, 0), 'shin.R': (12, 0, 0), 'hcannon.R': (-24, 0, 0),
             'neck': (3, 0, 0), 'tail': (0, 0, -5)},
        25: {'upper.L': (A, 0, 0), 'upper.R': (B, 0, 0), 'thigh.R': (A, 0, 0), 'thigh.L': (B, 0, 0)}})
    # attack: rear back, then drop the head and drive the antlers forward
    charge = {'neck': (24, 0, 0), 'head': (-20, 0, 0), 'upper.L': (-6, 0, 0), 'upper.R': (-6, 0, 0),
              'thigh.L': (-6, 0, 0), 'thigh.R': (-6, 0, 0)}
    clip(rig, 'attack', {1: {}, 8: {'neck': (-10, 0, 0), 'head': (8, 0, 0)}, 14: charge,
                         20: dict(charge, head=(-24, 0, 0)), 32: {}},
         loc={1: {'hips': (0, 0, 0)}, 14: {'hips': (0, -0.05, -0.02)}, 20: {'hips': (0, -0.07, -0.02)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
