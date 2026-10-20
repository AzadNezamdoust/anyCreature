import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet, load_ref
import numpy as np

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull), then hand detail
META = dict(creature='boar', model='opus', engine_glb='')

# The side view of the sheet shows the near AND far legs staggered (fore 5 cm, hind 15 cm apart); a
# visual hull keeps both. Hand edit of the carve input (as the wolf): inside each leg zone the side
# mask is cleared and redrawn as ONE designed leg, polygons in side-view metres (y, z) read off
# reference/side.png on a 0.1 m grid.
LEG_CLEAR = [
    [(-0.27, 0.285), (0.02, 0.285), (0.02, -0.01), (-0.27, -0.01)],
    [(0.24, 0.31), (0.566, 0.31), (0.575, 0.20), (0.575, -0.01), (0.24, -0.01)],
]
LEG_DRAW = [
    # foreleg: a column under the shoulder, slim wrist, short pastern, hoof toe leading
    [(-0.235, 0.34), (-0.215, 0.22), (-0.200, 0.13), (-0.198, 0.07), (-0.212, 0.03), (-0.222, 0.0),
     (-0.095, 0.0), (-0.100, 0.03), (-0.115, 0.07), (-0.117, 0.13), (-0.105, 0.20), (-0.080, 0.28),
     (-0.055, 0.34)],
    # hind leg: ham forward to the stifle, shin back to a pointed hock, near-vertical cannon, hoof
    [(0.300, 0.38), (0.330, 0.29), (0.365, 0.225), (0.400, 0.150), (0.425, 0.080), (0.425, 0.035),
     (0.410, 0.0), (0.535, 0.0), (0.535, 0.040), (0.528, 0.100), (0.548, 0.170), (0.553, 0.240),
     (0.553, 0.38)],
]

# The crest's spikes in the side view intersect the front view's narrow peak into stacked terraces
# along the spine (top, az180). The side mask above this line is cleared: the base keeps a smooth
# mane ridge over the hump (the front view keeps it narrow), the spikes come back as stage-3 clumps.
CREST_LINE = [(-0.50, 0.66), (-0.42, 0.74), (-0.30, 0.805), (-0.20, 0.845), (-0.10, 0.858), (0.00, 0.845),
              (0.10, 0.815), (0.20, 0.775), (0.30, 0.725), (0.40, 0.690)]


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
    m[_inside(CREST_LINE + [(0.40, 1.2), (-0.50, 1.2)], Y, Z)] = False
    m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
    _set_mask(sd, m)


def _set_mask(v, m):
    H, W = m.shape
    v.mask = m
    I = np.zeros((H + 1, W + 1), np.float64)
    I[1:, 1:] = m.astype(np.float64).cumsum(0).cumsum(1)
    v.I = I


# The sheet's plan view is shorter than its side view: both bboxes are 1.33 m, but the plan's tail
# lies flat (0.18 m) where the side's hangs, so the plan's rump ends at y 0.48 against the side's
# 0.62 and the hull cuts the hindquarters to a blade. Hand edit: the plan mask is resampled along y
# so snout and rump land on the side's (top y = -0.665 + (y + 0.665) * TOP_K), plus a thin tail strip.
TOP_K = (0.48 + 0.665) / (0.62 + 0.665)
TAIL_STRIP = (0.55, 0.70, 0.035)                  # y0, y1, half-width


def fix_top_mask(k):
    tp = load_ref(k.dir)['top']
    H, W = tp.mask.shape
    cols = np.arange(W)
    y = (cols + tp.c0 - tp.cmid) * tp.s
    src = np.clip(np.round((-0.665 + (y + 0.665) * TOP_K) / tp.s + tp.cmid - tp.c0).astype(int), 0, W - 1)
    m = tp.mask[:, src].copy()
    rows = np.arange(H)
    x = (rows + tp.r0 - tp.axis) * tp.s
    y0, y1, hw = TAIL_STRIP
    m[np.ix_(np.abs(x) < hw, (y > y0) & (y < y1))] = True
    m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
    _set_mask(tp, m)


# The front view's crest is a saw-tooth (half-width jumps 0.20 -> 0.12 -> 0.05 between z 0.74 and 0.84,
# the ears beside it): every step became a terrace along the whole back (top, az180). The front mask
# above z 0.62 is clipped to a smooth roof (x, z) that rises to the mane ridge; ears are stage-3 pieces.
FRONT_ROOF = [(0.215, 0.62), (0.19, 0.68), (0.15, 0.74), (0.11, 0.79), (0.07, 0.83), (0.035, 0.855), (0.0, 0.868)]


def fix_front_mask(k):
    fr = load_ref(k.dir)['front']
    H, W = fr.mask.shape
    R, C = np.mgrid[0:H, 0:W].astype(np.float64)
    Z = (fr.ground - fr.r0 - R) * fr.s
    X = np.abs((C + fr.c0 - fr.axis) * fr.s)
    rx = np.array([p[0] for p in FRONT_ROOF]); rz = np.array([p[1] for p in FRONT_ROOF])
    lim = np.interp(Z, rz, rx, left=1.0, right=-1.0)
    m = fr.mask.copy()
    m[(Z > 0.62) & (X > lim)] = False
    _set_mask(fr, m)


CARVE = dict(voxel_div=120, target_tris=(850, 1200))


def stage1(k):
    # carve_base's cache key does not see this mask edit: key it here (a changed polygon re-carves)
    import hashlib
    key = hashlib.sha256(repr((LEG_CLEAR, LEG_DRAW, CARVE, TOP_K, TAIL_STRIP, CREST_LINE, FRONT_ROOF)).encode()).hexdigest()
    kf, cf = os.path.join(k.dir, 'carve_mask.key'), os.path.join(k.dir, 'carve_base.json')
    if not os.path.exists(kf) or open(kf).read() != key:
        if os.path.exists(cf):
            os.remove(cf)
        open(kf, 'w').write(key)
    fix_side_mask(k)
    fix_top_mask(k)
    fix_front_mask(k)
    body = carve_base(k, **CARVE)
    bm = edit(body)
    fins = [e for e in bm.edges if len(e.link_faces) == 2 and all(abs(v.co.x) < 1e-6 for v in e.verts)]
    print('BOAR seam fins', len(fins), [tuple(round(c, 3) for c in (e.verts[0].co + e.verts[1].co) / 2) for e in fins])
    if fins:
        r = bmesh.ops.subdivide_edges(bm, edges=fins, cuts=1)
        for v in [g for g in r['geom_inner'] if isinstance(g, bmesh.types.BMVert)]:
            v.co.x = 0.002
    # ---- back: the narrow mane ridge descends through the voxel layers in steps (terraces across the
    # spine, top view). Smooth the back verts in z only (x and y stay: the outline in front/top holds).
    back = verts_where(bm, lambda c: c.z > 0.62 and -0.40 < c.y < 0.50)
    for _ in range(6):
        bmesh.ops.smooth_vert(bm, verts=back, factor=0.5, use_axis_z=True)
    snap_seam(bm, 1e-6)
    commit(body, bm)
    return body


def V_(bm, p, tol=0.004):
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < tol, f'no vertex at {p}: nearest {tuple(round(c, 3) for c in v.co)}'
    return v


def nudge(bm, moves):
    for p, d in moves:
        V_(bm, p).co += Vector(d)


def _pl(a, b, side):
    """Plane through side-view points a, b = (y, z); normal in the YZ plane toward `side` (y, z)."""
    dy, dz = b[0] - a[0], b[1] - a[1]
    n = Vector((0.0, -dz, dy)).normalized()
    if n.dot(Vector((0.0, side[0] - a[0], side[1] - a[1]))) < 0:
        n = -n
    return Vector((0.0, a[0], a[1])), n


# colour borders cut into the base (stage 2, logged loops): (plane, region of face centres). Read off
# reference/side.png on a 0.1 m grid. Normals have no X part: seam verts stay on x = 0.
CUTS = {
    'disc':   (_pl((-0.648, 0.1), (-0.648, 0.5), (-0.8, 0.3)), lambda c: c.y < -0.58 and c.z < 0.45),
    'hoof':   (_pl((-1.0, 0.045), (1.0, 0.045), (0.0, -1.0)), lambda c: c.z < 0.13),
    'mfront': (_pl((-0.40, 0.72), (-0.28, 0.48), (0.0, 0.6)), lambda c: -0.46 < c.y < -0.20 and c.z > 0.40),
    # team r23: the mantle's lower edge was one straight diagonal; now it dips over the shoulder blade
    # (z 0.46 behind the foreleg, ~12 cm lower than before) and rises to the back toward the hip
    'mlow':   (_pl((-0.28, 0.48), (-0.04, 0.45), (0.0, 1.0)), lambda c: -0.32 < c.y < -0.02 and c.z > 0.40),
    # team r34 (verify: still a near-straight diagonal): a saddle. Behind the shoulder blade the edge
    # rises steeply to the back (56 deg), then runs under the spine to a soft point at the hip.
    'mlow2':  (_pl((-0.04, 0.45), (0.10, 0.66), (0.0, 1.0)), lambda c: -0.07 < c.y < 0.13 and c.z > 0.40),
    'mlow3':  (_pl((0.10, 0.66), (0.44, 0.69), (0.0, 1.0)), lambda c: 0.07 < c.y < 0.47 and c.z > 0.58),
}
MLOW = [(-0.28, 0.48), (-0.04, 0.45), (0.10, 0.66), (0.44, 0.69)]


def above_mantle(c):
    return c.z > float(np.interp(c.y, [q[0] for q in MLOW], [q[1] for q in MLOW]))


def side_of(name, c):
    (p, n), _ = CUTS[name]
    return (Vector(c) - p).dot(n) > 0


def in_cut(name, c):
    return CUTS[name][1](c) and side_of(name, c)


def cut(k, bm, name, snap=0.012):
    """Bisect the region with the plane (a logged loop); verts within `snap` go onto it first (no slivers)."""
    (p, n), region = CUTS[name]
    faces = [f for f in bm.faces if region(f.calc_center_median())]
    verts = {v for f in faces for v in f.verts}
    for v in verts:
        d = (v.co - p).dot(n)
        if abs(d) < snap and abs(v.co.x) > 1e-6 or abs(d) < snap and abs(n.x) < 1e-9:
            v.co -= n * d
    edges = {e for f in faces for e in f.edges}
    with k.topo(bm, 'loop', f'colour border {name}: a planar cut so the border runs on an edge path'):
        bmesh.ops.bisect_plane(bm, geom=faces + list(edges) + list(verts), plane_co=p, plane_no=n, dist=1e-5)


EYE = (0.135, -0.475, 0.515)                       # reference side eye (-0.48, 0.51)


def stage2(k, body):
    bm = edit(body)
    # ---- face (r01): a flat snout disc, an eye socket under a brow
    disc = verts_where(bm, lambda c: c.y < -0.635)
    for v in disc:
        v.co.y = -0.664
    ef = face_near(bm, EYE, n=(1, -0.3, 0.2))
    print('BOAR eye face', tuple(round(c, 3) for c in ef.calc_center_median()), len(ef.verts))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face; the eye piece sits in it'):
        inner = inset(bm, [ef], 0.35, -0.008)
    # r03 (from s3 r07, az000): no brow, the face reads blank. The socket's upper rim verts push out
    # and forward into a brow that overhangs the eye; the lower rim stays (a cheek under it).
    ec = sum((v.co for v in inner[0].verts), Vector()) / len(inner[0].verts)
    rim = {v for f in inner[0].verts[0].link_faces for v in f.verts} | {v for vv in inner[0].verts for f in vv.link_faces for v in f.verts}
    rim -= set(inner[0].verts)
    for v in rim:
        if v.co.z > ec.z + 0.004 and v.co.x > 0.02:
            v.co += Vector((0.010, -0.010, 0.004)) + Vector((1, -0.3, 0.2)).normalized() * 0.006   # team r19: +6 mm out, the lens in its shadow
            say(f'BOAR brow vert {tuple(round(c, 3) for c in v.co)}')
    # ---- team r20 (must-fix 4): the hind leg was a straight column (az090). A back-shear of the leg, zero
    # at the hoof ring and above the ham, peaking 6 cm at the hock band: the shin runs back to a hock and
    # the cannon angles forward to the planted hoof.
    HOCK = [(0.0, 0.0), (0.065, 0.0), (0.18, 0.055), (0.27, 0.045), (0.38, 0.0)]   # r21: kept under the ham (r20 sheared the rump: 2 self-hits)

    def hock_dy(z):
        for (z0, d0), (z1, d1) in zip(HOCK, HOCK[1:]):
            if z0 <= z <= z1:
                return d0 + (d1 - d0) * (z - z0) / (z1 - z0)
        return 0.0
    for v in verts_where(bm, lambda c: c.y > 0.28 and c.x > 0.04 and c.z < 0.38):
        v.co.y += hock_dy(v.co.z)
    # ---- team r22: the forelegs 10 % narrower in x below the elbow (about the leg's own centre line),
    # blended to nothing at the elbow (z 0.29) and at the hoof ring (z 0.045)
    fl = verts_where(bm, lambda c: -0.36 < c.y < 0.0 and c.x > 0.04 and c.z < 0.29)
    if fl:
        xc = sum(v.co.x for v in fl) / len(fl)
        for v in fl:
            z = v.co.z
            kf = 0.0 if z < 0.06 else min(1.0, (z - 0.06) / 0.04, (0.29 - z) / 0.04)
            v.co.x = xc + (v.co.x - xc) * (1.0 - 0.10 * kf)
    # ---- colour borders (r02)
    for name in CUTS:
        cut(k, bm, name)
    snap_seam(bm, 1e-6)
    commit(body, bm)


BRIEF = {'brown': '#6f5040', 'dark': '#3e2c24', 'snout': '#b88e7e', 'tusk': '#efe3c8', 'hoof': '#2a201c',
         'eye': '#1a1414'}


def _rgb(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def sheet_palette(k, body):
    """colour_from_sheet's clusters, each brief role taking its nearest sheet colour (the sheet's own
    values) when one is near; the paint itself is by rules on the stage-2 loops (clean borders)."""
    sheet = colour_from_sheet(k, [body])
    say(f'BOAR sheet clusters: {sheet}')
    pal = {}
    for role, h in BRIEF.items():
        best = min(sheet.values(), key=lambda q: sum((a - b) ** 2 for a, b in zip(_rgb(q), _rgb(h))))
        d = sum((a - b) ** 2 for a, b in zip(_rgb(best), _rgb(h))) ** 0.5
        pal[role] = best if d < 40 and best not in pal.values() else h
    pal['brown'] = '#6f5040'                     # r02: #7d5843 (the sheet's lit #635149 rendered near black); team r23: the brief's #6f5040 (7d5843 read orange)
    pal['dark'] = '#46322a'
    say(f'BOAR palette: {pal}')
    return pal


# team r17: the dark brow-to-cheek mask over the eye and the jowl patch beside the tusk root (5_reference front)
BROW_C, BROW_R = Vector((0.125, -0.495, 0.545)), 0.050
JOWL_C, JOWL_R = Vector((0.115, -0.560, 0.330)), 0.040


def body_rule(c, n, i):
    if in_cut('disc', c):
        return 'snout'
    if in_cut('hoof', c):
        return 'hoof'
    if c.x > 0.07 and ((Vector(c) - BROW_C).length < BROW_R or (Vector(c) - JOWL_C).length < JOWL_R):
        return 'dark'
    if c.x > 0.06 and -0.54 < c.y < -0.43 and 0.50 < c.z < 0.63 and n.y < -0.25:   # r18: the brow band over the eye
        say(f'BOAR brow face {tuple(round(q, 3) for q in c)} n {tuple(round(q, 2) for q in n)}')
        return 'dark'
    if in_cut('mfront', c) and above_mantle(c):
        return 'dark'
    if -0.20 < c.y < 0.44 and c.z > 0.40 and above_mantle(c):
        return 'dark'
    return 'brown'


def hit(tree, o, d):
    loc, nor, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
    assert loc is not None, f'no surface from {o} along {d}'
    return loc, nor


def tube(bm, path, radii, sides=4, up=Vector((0, 0, 1))):
    """A tapered tube along path (points), radius per point; a last radius 0 makes a point."""
    rings = []
    for i, (p, r) in enumerate(zip(path, radii)):
        d = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        u = d.cross(up)
        if u.length < 1e-4:
            u = d.orthogonal()
        u.normalize(); w = u.cross(d).normalized()
        if r <= 0:
            rings.append(ring(bm, [p])); continue
        rings.append(ring(bm, [p + (u * math.cos(2 * math.pi * j / sides + math.pi / sides) +
                                    w * math.sin(2 * math.pi * j / sides + math.pi / sides)) * r for j in range(sides)]))
    for a, b in zip(rings, rings[1:]):
        if len(b) == 1:
            for j in range(len(a)):
                bm.faces.new([a[j], a[(j + 1) % len(a)], b[0]])
        else:
            bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rings[0])))


def stage3(k, body):
    pal = sheet_palette(k, body)
    paint(body, pal, body_rule)
    ebm = evaluated_bm(body)
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromBMesh(ebm)
    pieces = []

    # ---- eyes: a dark almond lens standing proud in the socket
    bm0 = edit(body)
    sf = face_near(bm0, EYE, n=(1, -0.3, 0.2))
    c, n = sf.calc_center_median(), sf.normal.copy()
    bm0.free()
    fa = Vector((0, -1, 0.15)); fa = (fa - n * fa.dot(n)).normalized(); fb = n.cross(fa).normalized()
    if fb.z < 0:
        fb = -fb
    ha, hb = 0.040, 0.024                      # r08: bigger lens (a pin-prick in az000); team r17: 1.4x again
    alm = [(-1.0, 0.0), (-0.38, 0.62), (0.40, 0.58), (1.0, 0.0), (0.40, -0.55), (-0.38, -0.60)]
    tl = math.radians(10)                      # team r17: the outer (rear, -fa) corner 10 deg lower: the mean look
    alm = [((a * ha * math.cos(tl) - b * hb * math.sin(tl)) / ha, (a * ha * math.sin(tl) + b * hb * math.cos(tl)) / hb) for a, b in alm]
    bm = bmesh.new()
    lo = ring(bm, [c + fa * (a * ha) + fb * (b * hb) - n * 0.003 for a, b in alm])
    hi = ring(bm, [c + fa * (a * ha * 0.75) + fb * (b * hb * 0.80) + n * 0.020 for a, b in alm])   # r09: 12 mm proud of the rim (was buried)
    bridge(bm, lo, hi, closed=True); cap(bm, list(reversed(lo))); cap(bm, hi)
    eye = object_from_bm('eyes', bm)
    paint(eye, {'eye': pal['eye']}, lambda cc, nn, i: 'eye')
    pieces.append(eye)

    # ---- nostrils: two dark ovals set on the snout disc
    bm = bmesh.new()
    nc = Vector((0.030, -0.664, 0.292))
    hexa = [(math.cos(math.pi * j / 3), math.sin(math.pi * j / 3)) for j in range(6)]
    f0 = ring(bm, [nc + Vector((a * 0.014, 0.008, b * 0.017)) for a, b in hexa])
    f1 = ring(bm, [nc + Vector((a * 0.012, -0.003, b * 0.015)) for a, b in hexa])
    bridge(bm, f0, f1, closed=True); cap(bm, list(reversed(f0))); cap(bm, f1)
    nos = object_from_bm('nostrils', bm)
    paint(nos, {'hoof': pal['hoof']}, lambda cc, nn, i: 'hoof')
    pieces.append(nos)

    # ---- tusks: from the lower-jaw corner, out and then curving up past the snout top
    bm = bmesh.new()
    path = [Vector(p) for p in [(0.060, -0.590, 0.270), (0.095, -0.605, 0.285), (0.130, -0.600, 0.315),
                                (0.150, -0.578, 0.360), (0.150, -0.552, 0.405), (0.138, -0.535, 0.440)]]
    tube(bm, path, [0.030, 0.029, 0.025, 0.019, 0.011, 0.0], sides=5, up=Vector((0, 1, 0)))
    tusk = object_from_bm('tusks', bm)
    paint(tusk, {'tusk': pal['tusk']}, lambda cc, nn, i: 'tusk')
    pieces.append(tusk)

    # ---- ears (team r11): a broad cupped leaf, base ~0.11 wide (eye-to-eye), 0.14 long, leaning 30 deg
    # forward and 35 deg out (tip ahead of the base, az090); a lens section (edges thin, 4-6 mm at the
    # centre line, no 3 mm side walls = no slivers); outside brown, the front cup dark; rigid to head.
    bm = bmesh.new()
    base, _ = hit(tree, (0.092, -0.420, 1.0), (0, 0, -1))   # r37: 15 mm forward, the deep cup's back clear of the hump in the toss
    say(f'BOAR ear base {tuple(round(c, 3) for c in base)}')
    # team r32: 45 deg out made the far ear a horizontal horn in hero; now 30 out / 25 forward (upright leaf)
    ax = Vector((math.tan(math.radians(30)), -math.tan(math.radians(25)), 1.0)).normalized()
    # r13: the leaf's face (its cup) opens forward and out; the width lies across it. At r12 the width ran
    # outward along the lean, so from the front the leaf was seen edge-on as a spike.
    fw = Vector((0.65, -0.75, 0.15))   # r15: turned 15 deg more to the flank (a spike in az090)
    fw = (fw - ax * fw.dot(ax)).normalized()
    out = ax.cross(fw).normalized()
    EL = 0.20                                  # r12: 45 deg out, 0.16 long: at 35/0.14 the leaf hid against the hump (az000)

    def seat(p):
        loc, _ = hit(tree, (p.x, p.y, 1.0), (0, 0, -1))
        return Vector((p.x, p.y, min(p.z, loc.z - 0.004)))   # sunk 4 mm into the skull

    def sec(t, w, cup, th):
        p = base + ax * (EL * t)
        L, R = p + out * w, p - out * w
        lm, rm = p + out * (w * 0.62) - fw * (cup * 0.55), p - out * (w * 0.62) - fw * (cup * 0.55)
        cf, cb = p - fw * cup, p - fw * (cup + th)
        return [L, lm, cf, rm, R, cb]
    # team r31 (verify: a thin spike in hero/az090): a DEEP cup (45 mm at the widest row), so the leaf has
    # breadth from the side as well as from the front
    rows = [sec(-0.06, 0.058, 0.020, 0.004), sec(0.30, 0.072, 0.055, 0.006), sec(0.66, 0.054, 0.040, 0.005)]   # r33: wider, deeper
    b0 = rows[0]
    rows[0] = [seat(b0[0]), seat(b0[1] + fw * 0.008), seat(b0[2] + fw * 0.012), seat(b0[3] + fw * 0.008),
               seat(b0[4]), seat(b0[5] - fw * 0.012)]
    rr = [ring(bm, P) for P in rows] + [ring(bm, [base + ax * EL])]
    for r_a, r_b in zip(rr, rr[1:-1]):
        bridge(bm, r_a, r_b, closed=True)
    for j in range(6):
        bm.faces.new([rr[-2][j], rr[-2][(j + 1) % 6], rr[-1][0]])
    cap(bm, list(reversed(rr[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ears = object_from_bm('ears', bm)
    fwd, outv = fw.copy(), out.copy()

    def ear_rule(cc, nn, i):
        # r14: dark only on the inner cup, a brown rim round it and a brown back (it read all dark)
        qq = Vector((abs(cc[0]), cc[1], cc[2])) - base           # the mirrored half folds onto +X
        t = qq.dot(ax) / EL
        wt = 0.072 if t < 0.3 else 0.072 - (t - 0.3) / 0.7 * 0.072
        front = Vector((abs(nn[0]), nn[1], nn[2])).dot(fwd) > 0.3
        return 'dark' if front and t > 0.1 and abs(qq.dot(outv)) < 0.5 * wt else 'brown'
    paint(ears, {'brown': pal['brown'], 'dark': pal['dark']}, ear_rule)
    pieces.append(ears)

    # ---- crest (team r16): one connected strip of 9 bristle clumps, from 2 cm behind the ear seat to
    # mid-back; base lengths, widths and heights all differ (tallest 0.092 at the withers, nape 0.05, the
    # last two ~0.03); each clump overlaps the next by a third of its base; peaks sit behind the clump
    # centre (combed back ~17 deg). r09's comb was 7 identical teeth on a fixed pitch with a bare nape.
    bm = bmesh.new()
    BL = [0.125, 0.100, 0.150, 0.140, 0.110, 0.150, 0.105, 0.125, 0.090]      # base length along y
    HT = [0.050, 0.062, 0.080, 0.092, 0.078, 0.065, 0.048, 0.032, 0.026]      # height
    WD = [0.042, 0.034, 0.050, 0.046, 0.038, 0.050, 0.036, 0.040, 0.030]      # half-width in x
    starts = [-0.385]
    for bl in BL[:-1]:
        starts.append(starts[-1] + bl * 0.67)

    def surf(y):
        loc, _ = hit(tree, (0.0, y, 1.5), (0, 0, -1))
        return loc.z

    def section(y, h, w):
        z0 = surf(y)
        sk = 0.004 if y < 0.15 else 0.012     # r37: the rear clumps' skirt deeper (their underside cut the skin when the spine bends)
        return [(0.0, y, z0 + h), (w * 0.55, y, z0 + h * 0.55), (w, y, z0 - sk), (0.0, y, z0 - 0.030 - sk),
                (-w, y, z0 - sk), (-w * 0.55, y, z0 + h * 0.55)]
    prof = [section(starts[0] - 0.012, -0.008, 0.028)]   # r36: both end sections buried (4 mm proud, they cut the skin in a bend: clip 2)
    for i, (s, bl, h, w) in enumerate(zip(starts, BL, HT, WD)):
        pk = s + bl * 0.62                                     # the peak behind the centre: combed back
        prof.append(section(pk - bl * 0.30, h * 0.62, w))       # rising front slope
        prof.append(section(pk, h, w * 0.80))                   # the peak
        prof.append(section(pk + bl * 0.14, h * 0.72, w * 0.85))   # the steep combed back
        if i + 1 < len(BL):
            vy = (s + bl + starts[i + 1]) / 2                   # valley: middle of the overlap
            prof.append(section(vy, 0.35 * min(h, HT[i + 1]), (w + WD[i + 1]) / 2))
    prof.append(section(starts[-1] + BL[-1], -0.008, 0.026))
    rings_ = [ring(bm, P) for P in prof]
    for a, b in zip(rings_, rings_[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rings_[0]))); cap(bm, rings_[-1])
    crest = object_from_bm('crest', bm, mirror=False)
    paint(crest, {'dark': pal['dark']}, lambda cc, nn, i: 'dark')
    pieces.append(crest)

    # ---- tail tuft: a dark blunt wedge round the tail end
    bm = bmesh.new()
    # team r24 (should-fix): thinner base, tuft 30 % longer, hanging
    path = [Vector(p) for p in [(0.0, 0.640, 0.420), (0.0, 0.656, 0.340), (0.0, 0.668, 0.260), (0.0, 0.672, 0.170)]]
    tube(bm, path, [0.011, 0.034, 0.030, 0.0], sides=4, up=Vector((1, 0, 0)))
    tuft = object_from_bm('tuft', bm, mirror=False)
    paint(tuft, {'dark': pal['dark']}, lambda cc, nn, i: 'dark')
    pieces.append(tuft)
    ebm.free()
    return pieces


# the skeleton, read off the carved base (LEG_DRAW polygons, the front view's leg x, the hull's head and tail)
J = dict(
    hips=(0.0, 0.46, 0.56), spine=(0.0, 0.10, 0.60), chest=(0.0, -0.20, 0.62),
    neck=(0.0, -0.29, 0.55), snout=(0.0, -0.66, 0.29),
    shoulderL=(0.115, -0.16, 0.50), elbowL=(0.115, -0.158, 0.29), wristL=(0.115, -0.158, 0.10),
    hoofL=(0.115, -0.165, 0.0),
    hipL=(0.115, 0.45, 0.50), stifleL=(0.115, 0.43, 0.26), hockL=(0.115, 0.50, 0.15),
    fhoofL=(0.115, 0.47, 0.0),
    tail0=(0.0, 0.58, 0.52), tail1=(0.0, 0.665, 0.25),
    earL=(0.098, -0.405, 0.645), earTipL=(0.190, -0.440, 0.800),
)


def stage4(k, body, pieces):
    # k3/boar's rig and clips, on this base's joints
    tm = tuple((Vector(J['tail0']) + Vector(J['tail1'])) / 2)
    rig = armature([
        ('spine', J['spine'], J['chest'], None),
        ('hips', J['spine'], J['hips'], 'spine'),
        ('neck', J['chest'], J['neck'], 'spine', True),
        ('head', J['neck'], J['snout'], 'neck', True),
        ('ear.L', J['earL'], J['earTipL'], 'head'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'spine'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hoof.L', J['wristL'], J['hoofL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['stifleL'], 'hips'),
        ('shin.L', J['stifleL'], J['hockL'], 'thigh.L', True),
        ('foot.L', J['hockL'], J['fhoofL'], 'shin.L', True),
        ('tail', J['tail0'], tm, 'hips'),
        ('tail2', tm, J['tail1'], 'tail', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        if 'ears' in p.name:
            bind(p, rig, bone='head')      # r05: rigid to head, the neck joint moved back so the skin under the ear is head
        else:
            bind(p, rig, body=body)
    # idle: sniffing and rooting (head dips, snout sways), tail flick. r04: no ear keys (the ear bone
    # folded the leaf: 12 flips with body weights)
    clip(rig, 'idle', {1: {}, 12: {'neck': (-6, 0, 0), 'head': (-10, 0, 0), 'tail': (0, 0, 14)},
                       24: {'neck': (-2, 0, 0), 'head': (-5, 3, 0)},
                       36: {'neck': (-6, 0, 0), 'head': (-11, -3, 0), 'tail': (0, 0, -14)},
                       48: {}})

    def A(s):
        return {'upperarm.L': (14 * s, 0, 0), 'thigh.R': (14 * s, 0, 0), 'upperarm.R': (-14 * s, 0, 0),
                'thigh.L': (-14 * s, 0, 0), 'spine': (0, 2 * s, 0), 'head': (3, 0, 0), 'tail': (-12, 0, 3 * s)}

    def mid(s):
        return {('forearm.L' if s > 0 else 'forearm.R'): (-22, 0, 0), ('shin.L' if s < 0 else 'shin.R'): (20, 0, 0),
                'head': (-2, 0, 0)}
    clip(rig, 'move', {1: A(1), 7: mid(-1), 13: A(-1), 19: mid(1), 25: A(1)})
    # attack: head-down charge, then the tusk toss
    down = {'spine': (-5, 0, 0), 'neck': (-8, 0, 0), 'head': (-12, 0, 0), 'thigh.L': (-12, 0, 0), 'thigh.R': (-12, 0, 0), 'tail': (-12, 0, 0)}
    # team r24: ~10 cm more head lift in the toss (neck 10 -> 18, head 15 -> 20) so it reads in silhouette
    # r38: head roll in the toss 10 -> 5 (the right ear's cup cut the hump: clip 1)
    toss = {'spine': (2, 0, 0), 'neck': (18, 0, 0), 'head': (20, 5, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0)}
    clip(rig, 'attack', {1: {}, 8: down, 10: down, 16: toss, 18: toss,
                         25: {'neck': (2, 0, 0), 'head': (4, 0, 0)}, 32: {}},
         loc={1: {}, 10: {}, 16: {'spine': (0, 0.06, 0)}, 18: {'spine': (0, 0.06, 0)},
              25: {'spine': (0, 0.015, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
