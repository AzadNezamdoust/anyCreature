import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet, load_ref
import numpy as np

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull), then hand detail
META = dict(creature='wolf', model='opus', engine_glb='')


EAR_TIP = (0.097, -0.548, 1.100)                    # front + side outline ear tip

# colour borders: planes (point, normal, region) cut into the base in stage 1, so every border in
# stage 3 runs along an edge path (no saw-tooth). Normals have no X part: seam verts stay on x = 0.
# Read off reference/side.png on a 0.1 m grid. region(c) picks the faces the plane may cut.
def _pl(a, b, side):
    """Plane through side-view points a, b = (y, z); normal in the YZ plane toward `side` (y, z)."""
    dy, dz = b[0] - a[0], b[1] - a[1]
    n = Vector((0.0, -dz, dy)).normalized()
    if n.dot(Vector((0.0, side[0] - a[0], side[1] - a[1]))) < 0:
        n = -n
    return Vector((0.0, a[0], a[1])), n

CUTS = {
    # name: (plane, region)    the region is the face-centre box the border lives in
    'nose':   (_pl((-0.772, 0.70), (-0.782, 0.90), (-0.9, 0.8)), lambda c: c.y < -0.70 and c.z > 0.68),
    'lip':    (_pl((-0.80, 0.792), (-0.50, 0.835), (-0.6, 0.6)), lambda c: c.y < -0.47 and c.z > 0.66),
    'bib':    (_pl((-0.50, 0.86), (-0.33, 0.44), (-0.6, 0.4)), lambda c: -0.62 < c.y < -0.20 and 0.40 < c.z < 0.90),
    'saddle': (_pl((-0.32, 0.785), (0.42, 0.74), (0.0, 1.0)), lambda c: -0.36 < c.y < 0.50 and c.z > 0.62),
    'belly':  (_pl((-0.30, 0.56), (0.22, 0.645), (0.0, 0.3)), lambda c: -0.32 < c.y < 0.26 and 0.42 < c.z < 0.70),
    'fleg':   (_pl((-0.50, 0.44), (-0.05, 0.44), (0.0, 0.0)), lambda c: c.y < -0.05 and c.z < 0.52),
    'hleg':   (_pl((0.25, 0.42), (0.55, 0.22), (0.0, 0.0)), lambda c: 0.15 < c.y < 0.62 and c.z < 0.56),
    'tailtip': (_pl((0.62, 0.36), (0.83, 0.27), (0.9, 0.0)), lambda c: c.y > 0.55 and c.z < 0.45),
}


def side_of(name, c):
    (p, n), _ = CUTS[name]
    return (Vector(c) - p).dot(n) > 0


def cut(bm, name, snap=0.013):
    """Bisect the region with the plane; verts within `snap` go onto it first (no slivers)."""
    (p, n), region = CUTS[name]
    faces = [f for f in bm.faces if region(f.calc_center_median())]
    verts = {v for f in faces for v in f.verts}
    for v in verts:
        d = (v.co - p).dot(n)
        if abs(d) < snap:
            v.co -= n * d
    edges = {e for f in faces for e in f.edges}
    bmesh.ops.bisect_plane(bm, geom=faces + list(edges) + list(verts), plane_co=p, plane_no=n, dist=1e-5)


# The side view of the sheet shows the near AND far legs staggered; a visual hull turns that into a
# 0.2 m long fused forefoot and TWO hind legs per side (six legs after the mirror). Hand edit of
# the carve input: inside each leg zone the side mask is cleared and redrawn as ONE designed leg
# (polygons in side-view metres (y, z), read off reference/side.png on a 0.1 m grid).
LEG_CLEAR = [
    [(-0.50, 0.445), (-0.16, 0.445), (-0.16, -0.01), (-0.50, -0.01)],
    [(0.10, 0.53), (0.50, 0.53), (0.585, 0.30), (0.63, 0.10), (0.63, -0.01), (0.10, -0.01)],
]
LEG_DRAW = [
    # foreleg: straight column, elbow tucked back, small forward wrist, paw toes leading
    [(-0.440, 0.50), (-0.420, 0.30), (-0.402, 0.13), (-0.407, 0.070), (-0.460, 0.030), (-0.466, 0.0),
     (-0.308, 0.0), (-0.314, 0.050), (-0.333, 0.120), (-0.318, 0.25), (-0.298, 0.360), (-0.250, 0.450),
     (-0.200, 0.50)],
    # hind leg (the near leg of the sheet): thigh forward to the stifle, shin back to a pointed hock,
    # near-vertical cannon, oval paw
    [(0.200, 0.56), (0.300, 0.47), (0.385, 0.370), (0.430, 0.290), (0.465, 0.210), (0.462, 0.100),
     (0.450, 0.060), (0.405, 0.025), (0.398, 0.0), (0.545, 0.0), (0.540, 0.060), (0.548, 0.150),
     (0.590, 0.205), (0.570, 0.300), (0.548, 0.400), (0.545, 0.50), (0.550, 0.56)],
]


def _inside(P, Y, Z):
    P = np.array(P)
    ins = np.zeros(Y.shape, bool)
    for i in range(len(P)):
        (y1, z1), (y2, z2) = P[i], P[i - 1]
        c = ((z1 > Z) != (z2 > Z)) & (Y < (y2 - y1) * (Z - z1) / (z2 - z1 + 1e-12) + y1)
        ins ^= c
    return ins


def fix_side_mask(k):
    sd = load_ref(k.dir)['side']
    H, W = sd.mask.shape
    R, C = np.mgrid[0:H, 0:W].astype(np.float64)
    Z = (sd.ground - sd.r0 - R) * sd.s
    Y = (C + sd.c0 - sd.cmid) * sd.s
    m = sd.mask.copy()
    for P in LEG_CLEAR:
        m[_inside(P, Y, Z)] = False
    for P in LEG_DRAW:
        m[_inside(P, Y, Z)] = True
    m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
    sd.mask = m
    I = np.zeros((H + 1, W + 1), np.float64)
    I[1:, 1:] = m.astype(np.float64).cumsum(0).cumsum(1)
    sd.I = I


# Team pass (STAGE-1 UNLOCK, AD must-fix 1): a visual hull cannot see the space between the legs
# (no view looks through it), so the forelegs came out one column from the chest down. The hull
# field is cleared in a channel between the legs: (y0, y1, z top, half gap x). A y-bounded box, so
# the tail (centred on x = 0 behind the hocks) is untouched. The half gaps sit at the legs' current
# inner faces (fore ~0.05, hind ~0.04 at the paws), so the leg sections keep their width.
LEG_CHANNEL = [(-0.52, -0.16, 0.55, 0.050), (0.20, 0.585, 0.45, 0.040)]


def _patch_hull():
    import carve
    if getattr(carve.hull_field, 'wolf_channel', False):
        return
    orig = carve.hull_field

    def hull_field(views, vs, *a, **kw):
        F, org = orig(views, vs, *a, **kw)
        x = org[0] + np.arange(F.shape[0]) * vs
        y = org[1] + np.arange(F.shape[1]) * vs
        z = org[2] + np.arange(F.shape[2]) * vs
        for y0, y1, zt, hg in LEG_CHANNEL:
            mx = np.abs(x) < hg
            my = (y > y0) & (y < y1)
            mz = z < zt
            F[np.ix_(mx, my, mz)] = 0.0
        return F, org
    hull_field.wolf_channel = True
    carve.hull_field = hull_field


def stage1(k):
    # carve_base's cache key does not see this mask edit: key it here (a changed polygon re-carves)
    import hashlib
    _patch_hull()
    key = hashlib.sha256(repr((LEG_CLEAR, LEG_DRAW, LEG_CHANNEL)).encode()).hexdigest()
    kf, cf = os.path.join(k.dir, 'carve_mask.key'), os.path.join(k.dir, 'carve_base.json')
    if not os.path.exists(kf) or open(kf).read() != key:
        if os.path.exists(cf):
            os.remove(cf)
        open(kf, 'w').write(key)
    fix_side_mask(k)
    body = carve_base(k, voxel_div=120, target_tris=(850, 1200))
    bm = edit(body)
    # ---- seam fins: an edge lying ON x = 0 with two faces doubles to four after the mirror (the hull
    # pinches to the seam there). Split it and lift its midpoint 2 mm off the seam.
    fins = [e for e in bm.edges if len(e.link_faces) == 2 and all(abs(v.co.x) < 1e-6 for v in e.verts)]
    print('WOLF seam fins', len(fins), [tuple(round(c, 3) for c in (e.verts[0].co + e.verts[1].co) / 2) for e in fins])
    if fins:
        r = bmesh.ops.subdivide_edges(bm, edges=fins, cuts=1)
        for v in [g for g in r['geom_inner'] if isinstance(g, bmesh.types.BMVert)]:
            v.co.x = 0.002
    # ---- ears: the hull leaves a flat-topped stub; the 4 plateau verts merge into one tip
    top = verts_where(bm, lambda c: c.x > 0.06 and c.z > 1.05 and -0.60 < c.y < -0.47)
    assert len(top) >= 3, top
    bmesh.ops.pointmerge(bm, verts=top, merge_co=Vector(EAR_TIP))
    # thin the ear front-to-back (the hull base is 0.12 deep; the reference ear ~0.07) and lean
    # the inner edge in, so it reads as a tall pointed blade, not a pyramid
    for v in verts_where(bm, lambda c: c.x > 0.05 and c.z > 0.985 and -0.62 < c.y < -0.42):
        w = min(1.0, (v.co.z - 0.985) / 0.05)
        v.co.y = EAR_TIP[1] + (v.co.y - EAR_TIP[1]) * (1.0 - 0.40 * w)
    # ---- colour borders as edge paths (see CUTS)
    for name in CUTS:
        cut(bm, name)
    snap_seam(bm, 1e-6)
    commit(body, bm)
    return body


TAIL_NARROW, TAIL_THIN, TAIL_SWING = 0.45, 0.25, 0.15
TAIL_FRONT, TAIL_LEAN, WEB_Z, WEB_K = 0.35, 0.04, 0.46, 0.60
BELLY_TUCK = 0.085
HEAD_WIDE = 0.14
EYE = (0.092, -0.632, 0.885)                        # the eye socket centre (reference side: -0.625, 0.905)


def vn(bm, p, tol=0.004):
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < tol, f'no vertex at {p}: nearest {tuple(v.co)}'
    return v


def nudge(bm, moves, tol=0.03):
    # team pass: the re-carved base (leg channel) moved every vertex a little; each move takes the
    # nearest vertex within `tol`, once; seam verts keep x = 0, and no vertex crosses onto the seam
    used = set()
    for p, d in moves:
        v = min((u for u in bm.verts if u not in used), key=lambda u: (u.co - Vector(p)).length)
        assert (v.co - Vector(p)).length < tol, f'no vertex near {p}: nearest {tuple(v.co)}'
        used.add(v)
        d = Vector(d)
        if v.co.x < 1e-6:
            d.x = 0.0
        v.co += d
        if v.co.x > 1e-6 and v.co.x < 0.004:
            v.co.x = 0.004


def stage2(k, body):
    bm = edit(body)
    # ---- face: eye socket under an overhanging brow, a stop, an overhanging nose over a receding chin
    ef = face_near(bm, EYE, n=(1, -0.5, 0.2))
    print('WOLF eye face', tuple(round(c, 3) for c in ef.calc_center_median()), len(ef.verts))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the brow-cheek face; the eye piece sits in it'):
        inset(bm, [ef], 0.30, -0.008)
    nudge(bm, [
        ((0.107, -0.572, 0.948), (0.010, -0.016, 0.0)),     # outer brow overhangs the socket
        ((0.039, -0.669, 0.928), (0.008, -0.006, 0.004)),   # inner brow
        ((0.0, -0.673, 0.915), (0.0, 0.0, -0.016)),         # the stop: a step between skull and muzzle
        ((0.0, -0.774, 0.744), (0.0, 0.026, 0.008)),        # chin back under the nose
        ((0.036, -0.775, 0.762), (-0.008, 0.022, 0.004)),
        ((0.062, -0.676, 0.786), (-0.008, 0.0, 0.0)),       # lower jaw narrower than the upper lip
        ((0.091, -0.627, 0.799), (-0.007, 0.0, 0.0)),
    ])
    # ---- muzzle: taper the last 6 cm toward the nose (the front read as a flat box in az000)
    for v in verts_where(bm, lambda c: c.y < -0.715 and c.z > 0.70 and c.x > 0.0):
        t = min(1.0, (-0.715 - v.co.y) / 0.06)
        v.co.x *= 1.0 - 0.30 * t
    # ---- paws: oval pads with the middle toes leading: front corners rounded back and in,
    # heels narrowed, the knuckle raised over a forward toe line
    nudge(bm, [
        ((0.116, -0.452, 0.000), (-0.016, 0.022, 0.0)),    # fore: outer toe corner (team-pass base)
        ((0.126, -0.455, 0.026), (-0.014, 0.018, 0.0)),
        ((0.140, -0.438, 0.018), (-0.014, 0.010, 0.0)),
        ((0.049, -0.461, 0.013), (0.008, 0.000, 0.0)),     # fore: inner toe corner in
        ((0.049, -0.312, 0.006), (0.010, -0.010, 0.0)),    # fore heel narrower
        ((0.127, -0.313, 0.002), (-0.014, -0.010, 0.0)),
        ((0.138, -0.312, 0.025), (-0.014, -0.006, 0.0)),
        ((0.116, 0.416, 0.007), (-0.012, 0.016, 0.0)),     # hind: outer toe corner
        ((0.099, 0.417, 0.028), (-0.008, 0.012, 0.0)),
        ((0.044, 0.409, 0.008), (0.010, -0.004, 0.0)),     # hind: inner toe in
        ((0.041, 0.537, 0.010), (0.010, -0.008, 0.0)),     # hind heel narrower
    ])
    # ---- team pass (AD 2): the tail was a slab hanging straight off the rump. Narrower in x (35%),
    # the root thinner front-to-back (25%), the lower half swung back so the tip trails the hocks.
    def is_tail(c):
        return (c.y > 0.60 and c.z < 0.66) or (c.x < 0.02 and c.y > 0.575 and c.z < 0.46)
    for v in verts_where(bm, is_tail):
        c = v.co
        k_ = min(1.0, max(0.0, (0.66 - c.z) / 0.10))
        c.x *= 1.0 - TAIL_NARROW * k_
        yf = 0.585 + (0.62 - c.z) * 0.05                       # the tail's front line
        if c.z > 0.36 and c.y > yf:
            c.y = yf + (c.y - yf) * (1.0 - TAIL_THIN * min(1.0, (c.z - 0.36) / 0.10))
        t = min(1.0, max(0.0, (0.48 - c.z) / 0.30))
        c.y += TAIL_SWING * t ** 1.3
    # second team pass (verifier: tail still deep and fused into the thigh): below the root the
    # tail's FRONT is pulled toward its back line (per 8 cm z band), opening a notch behind the hock
    tv = verts_where(bm, is_tail)
    back = {v: max(u.co.y for u in tv if abs(u.co.z - v.co.z) < 0.04) for v in tv}
    for v in tv:
        f = TAIL_FRONT * min(1.0, max(0.0, (0.60 - v.co.z) / 0.12))
        v.co.y = back[v] - (back[v] - v.co.y) * (1.0 - f)
    # ---- team pass (AD 5): belly tuck-up. The underside behind the ribcage (elbow line to the
    # stifle) rises up to 5.5 cm, most just ahead of the thigh; verts on a colour-cut plane stay put.
    bm.normal_update()
    planes = [pn for pn, _ in CUTS.values()]
    nb = 0
    for v in bm.verts:
        c = v.co
        if not (-0.15 < c.y < 0.34 and 0.40 < c.z < 0.62 and v.normal.z < -0.35):
            continue
        if any(abs((c - pp).dot(nn)) < 1e-5 for pp, nn in planes):
            continue
        w = (c.y + 0.15) / 0.37 if c.y < 0.22 else (0.34 - c.y) / 0.12
        c.z += BELLY_TUCK * max(0.0, min(1.0, w))
        nb += 1
    # the tail left the body at z 0.45, as a slab off the thigh: the rump-side back line leans out
    # (up to 4 cm at z 0.53) and the crotch vertex between tail and thigh goes up 6 cm, so the tail
    # leaves the rump at z ~0.5 with a notch against the thigh
    for v in tv:
        if 0.46 < v.co.z < 0.60:
            v.co.y += TAIL_LEAN * math.sin(math.pi * (v.co.z - 0.46) / 0.14)
    nudge(bm, [((0.0, 0.640, 0.447), (0.0, 0.010, 0.060))], tol=0.01)
    # the hull filled a web between the back of the hind leg and the tail down to the hock (the
    # slab): the leg-side verts of that web slide up the back of the leg to z ~0.42, so the web
    # ends there and the tail hangs free below it
    tvs = set(tv)
    web = [u for u in bm.verts if u not in tvs and u.co.x > 0.02 and u.co.y > 0.535 and 0.21 < u.co.z < WEB_Z]
    for u in web:      # graded: full at the back of the leg, none at its side; the hock ring stays
        g = min(1.0, (u.co.y - 0.535) / 0.045) * min(1.0, (u.co.z - 0.21) / 0.07)
        u.co.z += (WEB_Z - u.co.z) * WEB_K * g
    print('WOLF belly verts', nb)
    # ---- team pass (should-fix): hind paws +20% about the paw centre; ear tips 10% taller
    for v in verts_where(bm, lambda c: c.z < 0.06 and 0.38 < c.y < 0.56 and c.x > 0.0):
        v.co.x = 0.078 + (v.co.x - 0.078) * 1.2
        v.co.y = 0.478 + (v.co.y - 0.478) * 1.2
    for v in verts_where(bm, lambda c: c.x > 0.05 and c.z > 1.02 and -0.62 < c.y < -0.42):
        v.co.z += 0.012 * min(1.0, (v.co.z - 1.02) / 0.08)
    # second team pass (AD 4): the head read small against the ruff in az000. Skull and cheeks 14%
    # wider (x about the seam), fading out toward the neck (y -0.56..-0.47) and below the ears
    # (z 0.95..0.99: the ear blades and EAR_TIP stay where the rig and the inner-ear plates expect)
    for v in bm.verts:
        c = v.co
        wy = min(1.0, max(0.0, (-0.47 - c.y) / 0.09))
        wz = min(1.0, max(0.0, (0.99 - c.z) / 0.04)) * min(1.0, max(0.0, (c.z - 0.70) / 0.05))
        c.x *= 1.0 + HEAD_WIDE * wy * wz
    unsliver(bm)
    if os.environ.get('WOLF_DBG'):
        with open(os.environ['WOLF_DBG'], 'w') as fh:
            from mathutils.bvhtree import BVHTree
            bm.faces.ensure_lookup_table(); t_ = BVHTree.FromBMesh(bm)
            for i, j in t_.overlap(t_):
                if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
                    print('HIT', [tuple(round(x, 3) for x in v.co) for v in bm.faces[i].verts], [tuple(round(x, 3) for x in v.co) for v in bm.faces[j].verts], file=fh)
            for u in bm.verts:
                if u not in tvs and any(e.other_vert(u) in tvs for e in u.link_edges):
                    print('ADJ %.3f %.3f %.3f ->' % tuple(u.co), [tuple(round(x, 3) for x in e.other_vert(u).co) for e in u.link_edges if e.other_vert(u) in tvs], file=fh)
            for v in sorted(bm.verts, key=lambda v: -v.co.z):
                if v.co.y > 0.48 and v.co.z < 0.70:
                    print('%.3f %.3f %.3f %d' %  (v.co.x, v.co.y, v.co.z, 2 if v in web else v in tvs), file=fh)
    commit(body, bm)


def unsliver(bm, deg=7.5, rounds=4, w=0.4):
    """Team pass: the re-carved base carries ~15 needle triangles per side along the colour cuts.
    Each vertex of a needle (on a beauty triangulation of a copy) slides tangentially toward its
    neighbours' centroid; seam verts stay on x = 0 and verts on a cut plane stay on it (the colour
    borders keep their edge paths)."""
    planes = [pn for pn, _ in CUTS.values()]
    for _ in range(rounds):
        c2 = bm.copy()
        bmesh.ops.triangulate(c2, faces=c2.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
        c2.verts.ensure_lookup_table()
        bad = set()
        for f in c2.faces:
            a, b, c = (v.co for v in f.verts)
            if max((a - b).length, (b - c).length, (c - a).length) < 0.015:
                continue
            for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
                u, t = y - x, z - x
                if u.length > 1e-9 and t.length > 1e-9 and math.degrees(u.angle(t)) < deg:
                    bad |= {v.index for v in f.verts}
                    break
        c2.free()
        if not bad:
            break
        bm.verts.ensure_lookup_table()
        for i in bad:
            v = bm.verts[i]
            nb = [e.other_vert(v).co for e in v.link_edges]
            d = sum(nb, Vector()) / len(nb) - v.co
            d -= v.normal * d.dot(v.normal)
            if abs(v.co.x) < 1e-6:
                d.x = 0.0
            for pp, nn in planes:
                if abs((v.co - pp).dot(nn)) < 1e-5:
                    d -= nn * d.dot(nn)
            v.co += d * w
        print('WOLF unsliver', len(bad))


PAL = {'fur': '#9c978e', 'saddle': '#65636b', 'tan': '#b59d76', 'cream': '#efe6cf',
       'eye': '#e0a030', 'nose': '#1e1b1b'}


def body_rule(c, n, i):
    if CUTS['nose'][1](c) and side_of('nose', c):
        return 'cream' if side_of('lip', c) else 'nose'       # black pad over a cream chin
    if c.z > 0.99 and c.x > 0.04 and n.y > 0.05:
        return 'saddle'                                        # backs of the ears
    if CUTS['tailtip'][1](c) and side_of('tailtip', c):
        return 'saddle'
    if CUTS['fleg'][1](c) and side_of('fleg', c):
        return 'tan'
    if CUTS['hleg'][1](c) and side_of('hleg', c):
        return 'tan'
    if CUTS['lip'][1](c) and side_of('lip', c):
        return 'cream'
    if CUTS['bib'][1](c) and side_of('bib', c):
        return 'cream'
    if CUTS['belly'][1](c) and side_of('belly', c):
        return 'cream'
    if CUTS['saddle'][1](c) and side_of('saddle', c):
        return 'saddle'
    return 'fur'


def frame3(d, n):
    """(d, u, v): d the length axis, u across, v the thickness axis turned toward n."""
    d = d.normalized()
    u = d.cross(n)
    if u.length < 1e-4:
        u = d.orthogonal()
    u.normalize()
    v = u.cross(d).normalized()
    if v.dot(n) < 0:
        v = -v
    return d, u, v


def blade(bm, base, d, n, L, w, t, sink=0.010):
    """A claw / tuft: a 4-sided root buried `sink` along -n, a point at base + d * L."""
    d, u, v = frame3(Vector(d), n)
    b = base - n * sink
    q = ring(bm, [b + u * w / 2 + v * t / 2, b - u * w / 2 + v * t / 2, b - u * w / 2 - v * t / 2, b + u * w / 2 - v * t / 2])
    tip = ring(bm, [base + d * L])[0]
    for i in range(4):
        bm.faces.new([q[i], q[(i + 1) % 4], tip])
    bm.faces.new(list(reversed(q)))


def shingle(bm, base, d, n, L, w, t, sink=0.3, sh=(0.40, 0.32)):
    """A fur clump: a thick root plate (w x t) sunk `sink` of its thickness, a broad shoulder ring,
    a blunt point; it lies along d and stands off the skin by its thickness."""
    d, u, v = frame3(Vector(d), n)
    b = base + v * (t / 2 - sink * t)
    q = ring(bm, [b + u * w / 2 + v * t / 2, b - u * w / 2 + v * t / 2, b - u * w / 2 - v * t / 2, b + u * w / 2 - v * t / 2])
    m = b + d * (sh[0] * L) + v * (0.35 * t)
    r = ring(bm, [m + u * sh[1] * w + v * 0.30 * t, m - u * sh[1] * w + v * 0.30 * t,
                  m - u * sh[1] * w - v * 0.30 * t, m + u * sh[1] * w - v * 0.30 * t])
    tip = ring(bm, [b + d * L + v * 0.25 * t])[0]
    bridge(bm, q, r, closed=True)
    for i in range(4):
        bm.faces.new([r[i], r[(i + 1) % 4], tip])
    bm.faces.new(list(reversed(q)))


def hit(tree, o, d):
    loc, nor, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
    assert loc is not None, f'no surface from {o} along {d}'
    return loc, nor


SWEEP = Vector((0.0, 0.70, -0.40))                      # fur lies back and down


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    paint(body, PAL, body_rule)
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)
    pieces = []

    # ---- eyes: an amber almond lens standing proud in the socket, a dark pupil set into it
    bm0 = edit(body)
    sf = face_near(bm0, EYE, n=(1, -0.5, 0.2))
    c, n = sf.calc_center_median(), sf.normal.copy()
    vs = [v.co.copy() for v in sf.verts]
    bm0.free()
    print('WOLF socket', tuple(round(x, 3) for x in c), tuple(round(x, 2) for x in n), len(vs))
    fa = Vector((0, -1, 0.25)); fa = (fa - n * fa.dot(n)).normalized(); fb = n.cross(fa).normalized()
    if fb.z < 0:
        fb = -fb
    # team pass (AD 3): lens +40% (7 x 4.2 cm), 15 mm proud, and its top plane tilted forward and
    # up from the socket normal so both eyes look at the viewer in az000
    ha = 0.035
    hb = 0.021
    ne = (n + Vector((0.10, -0.45, -0.25))).normalized()      # ~30 deg forward of the socket normal
    ga = (fa - ne * fa.dot(ne)).normalized(); gb = ne.cross(ga).normalized()
    if gb.z < 0:
        gb = -gb
    alm = [(-1.0, 0.0), (-0.38, 0.62), (0.40, 0.58), (1.0, 0.0), (0.40, -0.55), (-0.38, -0.60)]
    bm = bmesh.new()
    top = c + n * 0.017
    lo = ring(bm, [c + fa * (a * ha) + fb * (b * hb) - n * 0.004 for a, b in alm])
    hi = ring(bm, [top + ga * (a * ha * 0.74) + gb * (b * hb * 0.74) for a, b in alm])
    bridge(bm, lo, hi, closed=True); cap(bm, list(reversed(lo))); cap(bm, hi)
    pc = top + ga * (-0.10 * ha)                               # the pupil looks a little forward
    pr = [(0.0, 1.0), (0.55, 0.0), (0.0, -1.0), (-0.55, 0.0)]
    pl = ring(bm, [pc + ga * (a * 0.42 * ha) + gb * (b * 0.74 * hb) - ne * 0.003 for a, b in pr])
    ph = ring(bm, [pc + ga * (a * 0.34 * ha) + gb * (b * 0.62 * hb) + ne * 0.0035 for a, b in pr])
    bridge(bm, pl, ph, closed=True); cap(bm, list(reversed(pl))); cap(bm, ph)
    eye = object_from_bm('eyes', bm)
    paint(eye, {'eye': PAL['eye'], 'nose': PAL['nose']},
          lambda cc, nn, i: 'nose' if i >= 8 else 'eye')       # faces 0-7: lens, 8+: pupil
    pieces.append(eye)

    # ---- nose pad: a black wedge capping the muzzle tip (whole piece, no mirror)
    bm = bmesh.new()
    NP = Vector((0.0, -0.800, 0.812))
    q0 = ring(bm, [NP + Vector(p) for p in [(-0.024, 0.030, 0.020), (0.024, 0.030, 0.020), (0.026, 0.002, -0.020), (-0.026, 0.002, -0.020)]])
    q1 = ring(bm, [NP + Vector(p) for p in [(-0.017, -0.012, 0.015), (0.017, -0.012, 0.015), (0.020, -0.015, -0.013), (-0.020, -0.015, -0.013)]])
    bridge(bm, q0, q1, closed=True); cap(bm, list(reversed(q0))); cap(bm, q1)
    nose = object_from_bm('nose', bm, mirror=False)
    paint(nose, {'nose': PAL['nose']}, lambda cc, nn, i: 'nose')
    pieces.append(nose)

    # ---- mouth (team pass, AD 3): a dark lip strip on the lip edge path, nose to mouth corner
    bm = bmesh.new()
    (lp, ln), _ = CUTS['lip']
    ld = Vector((0.0, ln.z, -ln.y)); ld = ld if ld.y > 0 else -ld      # along the lip line, toward +Y
    rings = []
    for i in range(6):
        y = -0.772 + i * (0.172 / 5)
        z = lp.z + (y - lp.y) * ld.z / ld.y
        loc, nor = hit(tree, (0.6, y, z), (-1, 0, 0))
        hw = 0.0045 * (1.0 - 0.5 * i / 5)                          # tapers to the corner
        up = Vector((0, 0, 1)); up = (up - nor * up.dot(nor)).normalized()
        rings.append(ring(bm, [loc + up * hw + nor * 0.005, loc - up * hw + nor * 0.005,
                               loc - up * hw - nor * 0.004, loc + up * hw - nor * 0.004]))
    for r0, r1 in zip(rings, rings[1:]):
        bridge(bm, r0, r1, closed=True)
    cap(bm, list(reversed(rings[0]))); cap(bm, rings[-1])
    mouth = object_from_bm('mouth', bm)
    paint(mouth, {'nose': PAL['nose']}, lambda cc, nn, i: 'nose')
    pieces.append(mouth)

    # ---- inner ears: a cream plate set in the front of each ear
    bm = bmesh.new()
    tip = Vector(EAR_TIP)
    pts = []
    for (x, z) in [(0.068, 1.008), (0.109, 1.026), (0.098, 1.082)]:
        loc, nor = hit(tree, (x, -0.9, z), (0, 1, 0))
        pts.append((loc, nor))
    cen = sum((p for p, _ in pts), Vector()) / 3
    nn_ = sum((q for _, q in pts), Vector()).normalized()
    f = ring(bm, [cen + (p - cen) * 0.92 + nn_ * 0.007 for p, _ in pts])
    bk = ring(bm, [cen + (p - cen) * 0.92 - nn_ * 0.006 for p, _ in pts])
    bridge(bm, f, bk, closed=True); cap(bm, f); cap(bm, list(reversed(bk)))
    ears = object_from_bm('inner_ears', bm)
    paint(ears, {'cream': PAL['cream']}, lambda cc, nn, i: 'cream')
    pieces.append(ears)

    # ---- neck ruff: three rows of clumps round the neck, swept back and down; cheek tufts;
    # a cream bib of clumps down the chest
    bm = bmesh.new(); roots = []
    NU = Vector((0, 0.62, 0.78))                               # the neck's up axis
    for P, rw, row in [((0, -0.52, 0.90), 0.072, [(62, 0.110, 'fur'), (30, 0.115, 'fur'), (0, 0.110, 'fur'), (-26, 0.100, 'cream')]),
                   ((0, -0.45, 0.83), 0.118, [(70, 0.125, 'fur'), (44, 0.130, 'fur'), (16, 0.125, 'fur'), (-20, 0.115, 'fur'), (-42, 0.100, 'cream')]),
                   ((0, -0.37, 0.78), 0.095, [(74, 0.125, 'saddle'), (50, 0.130, 'fur'), (24, 0.125, 'fur'), (-4, 0.115, 'fur'), (-18, 0.100, 'fur')])]:
        for a, L, col in row:
            ar = math.radians(a)
            dr = Vector((math.cos(ar), 0, 0)) + NU * math.sin(ar)
            loc, nor = hit(tree, Vector(P) + dr * 0.8, -dr)
            shingle(bm, loc, nor * 0.55 + SWEEP, nor, L * rw / 0.105, rw, 0.032)   # team: a big row between two smaller
            roots.append((loc.copy(), col))
    # team pass (AD 4, and the drift gate: the low row hung into the new leg channel): one bib row,
    # clumps -30%, ending at the elbow (z ~0.57), not the knee
    for (x, z), L in [((0.045, 0.665), 0.080), ((0.100, 0.645), 0.075)]:
        loc, nor = hit(tree, (x, -1.2, z), (0, 1, 0))              # bib clumps hang down the chest
        shingle(bm, loc, nor * 0.45 + Vector((0, 0.10, -1.0)), nor, L, 0.060, 0.022)
        roots.append((loc.copy(), 'cream'))
    for (y, z), L in []:                                            # second team pass: no cheek tuft (it stacked beside the jaw in az000)                    # team pass: one tuft, behind the jaw                     # team pass: one tuft, behind the jaw
        loc, nor = hit(tree, (0.6, y, z), (-1, 0, 0))               # cheek tufts flare back and out
        shingle(bm, loc, nor * 0.65 + Vector((0, 0.75, -0.35)), nor, L, 0.070, 0.024)
        roots.append((loc.copy(), 'cream'))
    print('WOLF roots', [tuple(round(x, 3) for x in r[0]) for r in roots])
    ruff = object_from_bm('ruff', bm)
    paint(ruff, {'fur': PAL['fur'], 'cream': PAL['cream'], 'saddle': PAL['saddle']},
          lambda cc, nn, i: min(roots, key=lambda r: (r[0] - cc).length)[1])
    pieces.append(ruff)

    # ---- tail brush: side clumps along the tail and a dark tip
    bm = bmesh.new()
    ax = Vector((0, 0.55, -0.83))                             # team pass: the tail now trails back
    for (y, z), a, L in [((0.70, 0.46), 10, 0.07), ((0.76, 0.37), 0, 0.07), ((0.785, 0.345), -5, 0.055)]:      # second team pass: on the tail only, none on the thigh
        ar = math.radians(a)
        loc, nor = hit(tree, (0.8 * math.cos(ar), y, z + 0.8 * math.sin(ar)), (-math.cos(ar), 0, -math.sin(ar)))
        blade(bm, loc, nor * 0.35 + ax, nor, L, 0.060, 0.024)
    tipv = max((v for v in ebm.verts if v.co.y > 0.6 and v.co.x >= 0), key=lambda v: v.co.y - 0.5 * v.co.z)
    tc = tipv.co.copy(); print('WOLF tail tip', tuple(round(x, 3) for x in tc))
    loc, nor = hit(tree, tc + Vector((0.4, -0.10, 0.08)), (-1, 0, 0))
    blade(bm, loc, ax * 0.9 + Vector((0, 0.25, 0)) + nor * 0.35, nor, 0.08, 0.045, 0.024)
    tail = object_from_bm('tailbrush', bm)
    paint(tail, {'fur': PAL['fur'], 'saddle': PAL['saddle']},
          lambda cc, nn, i: 'saddle' if CUTS['tailtip'][1](cc) and side_of('tailtip', cc) else 'fur')
    pieces.append(tail)

    # ---- claws: four per paw, the middle pair leading
    bm = bmesh.new()
    for (px, py, sc) in [(0.085, -0.462, 0.95), (0.084, 0.396, 0.75)]:
        for dx, L, sp, pz in [(-0.030, 0.024, -10, -0.60), (-0.010, 0.030, -3, -0.50), (0.010, 0.030, 3, -0.50), (0.030, 0.024, 10, -0.60)]:
            for f_ in (1.0, 0.8, 0.6, 0.4):          # the toe line is rounded: step in until the ray lands
                loc, nor, _, _ = tree.ray_cast(Vector((px + dx * sc * f_, py - 0.2, 0.020)), Vector((0, 1, 0)))
                if loc is not None:
                    break
            assert loc is not None, (px, dx)
            s_ = math.radians(sp)
            blade(bm, loc, Vector((0.85 * math.sin(s_), -0.85 * math.cos(s_), pz)), nor, L, 0.012, 0.018)
    claws = object_from_bm('claws', bm)
    paint(claws, {'nose': PAL['nose']}, lambda cc, nn, i: 'nose')
    pieces.append(claws)
    ebm.free()
    return pieces


# the skeleton, read off the carved base (the leg polygons of LEG_DRAW, the hull's head and tail)
J = dict(
    pelvis=(0.0, 0.40, 0.66), spine=(0.0, 0.05, 0.70), chest=(0.0, -0.25, 0.73),
    head=(0.0, -0.52, 0.88), snout=(0.0, -0.80, 0.80),
    tail0=(0.0, 0.56, 0.68), tail1=(0.0, 0.64, 0.54), tail2=(0.0, 0.755, 0.38), tail3=(0.0, 0.90, 0.185),
    shoulderL=(0.10, -0.34, 0.60), elbowL=(0.088, -0.352, 0.40), wristL=(0.085, -0.368, 0.11),
    fpawL=(0.085, -0.43, 0.012),
    hipL=(0.09, 0.40, 0.62), kneeL=(0.082, 0.43, 0.38), hockL=(0.075, 0.535, 0.195),
    hpawL=(0.072, 0.44, 0.012),
    earL=(0.097, -0.548, 1.00), eartipL=EAR_TIP,
)


def stage4(k, body, pieces):
    rig = armature([
        ('spine', J['pelvis'], J['spine'], None),
        ('chest', J['spine'], J['chest'], 'spine', True),
        ('neck', J['chest'], J['head'], 'chest', True),
        ('head', J['head'], J['snout'], 'neck', True),
        ('ear.L', J['earL'], J['eartipL'], 'head'),
        ('tail0', J['tail0'], J['tail1'], 'spine'),
        ('tail1', J['tail1'], J['tail2'], 'tail0', True),
        ('tail2', J['tail2'], J['tail3'], 'tail1', True),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('fpaw.L', J['wristL'], J['fpawL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'spine'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L', True),
        ('hpaw.L', J['hockL'], J['hpawL'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing through the chest, an ear twitch, a lazy tail
    br = lambda a: {'chest': (a, 0, 0), 'neck': (-a * 0.5, 0, 0), 'tail0': (0, 0, a * 2)}
    clip(rig, 'idle', {1: br(0), 12: br(2.5), 20: br(3), 22: {**br(3), 'ear.L': (-14, 0, 6)},
                       24: {**br(3), 'ear.L': (0, 0, 0)}, 26: {**br(3), 'ear.L': (-10, 0, 4)},
                       28: br(2.5), 36: br(1.5), 48: br(0)})
    # move: trot, diagonal pairs (left fore + right hind together)
    def trot(s, flexR, flexL):
        return {'upperarm.L': (18 * s, 0, 0), 'upperarm.R': (-18 * s, 0, 0),
                'thigh.R': (10 * s, 0, 0), 'thigh.L': (-10 * s, 0, 0),
                'forearm.R': (-38 * flexR, 0, 0), 'forearm.L': (-38 * flexL, 0, 0),
                'fpaw.R': (-20 * flexR, 0, 0), 'fpaw.L': (-20 * flexL, 0, 0),
                'shin.L': (-20 * flexR, 0, 0), 'shin.R': (-20 * flexL, 0, 0),
                'hpaw.L': (24 * flexR, 0, 0), 'hpaw.R': (24 * flexL, 0, 0),
                'neck': (3 * abs(s), 0, 0), 'tail0': (0, 0, 6 * s)}
    clip(rig, 'move', {1: trot(1, 0, 0), 7: trot(0, 1, 0), 13: trot(-1, 0, 0), 19: trot(0, 0, 1), 25: trot(1, 0, 0)})
    # attack: rear back, head-down lunge, snap, recover
    clip(rig, 'attack', {1: {}, 8: {'neck': (12, 0, 0), 'head': (6, 0, 0), 'chest': (4, 0, 0), 'thigh.L': (-8, 0, 0), 'thigh.R': (-8, 0, 0)},
                         14: {'neck': (-12, 0, 0), 'head': (-14, 0, 0), 'chest': (-9, 0, 0), 'upperarm.L': (14, 0, 0), 'upperarm.R': (14, 0, 0),
                              'thigh.L': (10, 0, 0), 'thigh.R': (10, 0, 0)},
                         17: {'neck': (-14, 0, 0), 'head': (-22, 0, 0), 'chest': (-10, 0, 0), 'upperarm.L': (14, 0, 0), 'upperarm.R': (14, 0, 0),
                              'thigh.L': (10, 0, 0), 'thigh.R': (10, 0, 0)},
                         20: {'neck': (-12, 0, 0), 'head': (-10, 0, 0), 'chest': (-8, 0, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0),
                              'thigh.L': (6, 0, 0), 'thigh.R': (6, 0, 0)},
                         26: {'neck': (-6, 0, 0), 'head': (-2, 0, 0)}, 32: {}},
         loc={1: {'spine': (0, 0, 0)}, 8: {'spine': (0, -0.03, -0.02)}, 14: {'spine': (0, 0.06, -0.03)},
              20: {'spine': (0, 0.05, -0.02)}, 32: {'spine': (0, 0, 0)}})
    if os.environ.get('WOLF_DBG'):                              # per-clip diagnosis of drift / folds
        import techqa as Q, bpy
        for nm in ('idle', 'move', 'attack'):
            counts, flags, tris = Q.measure(body, pieces, (0.4, 1.6, 1.1), rig, {nm: bpy.data.actions[nm]})
            for o in [body] + list(pieces):
                for pi, cls in flags[o.name].items():
                    if cls in ('drift', 'flip', 'zfight', 'hit', 'sliver'):
                        c = o.data.polygons[pi].center
                        print('WOLFDBG', nm, o.name, cls, tuple(round(x, 3) for x in c), file=open(os.environ['WOLF_DBG'] + '.s4', 'a'))
    return rig


run(META, stage1, stage2, stage3, stage4)
