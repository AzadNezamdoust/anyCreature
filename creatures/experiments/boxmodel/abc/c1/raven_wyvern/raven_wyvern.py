import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet, load_ref
import math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull) plus hand edits; detail in stages 2-4
META = dict(creature='raven_wyvern', model='opus', engine_glb='')

# The skeleton (metres, faces -Y, left flank +X, feet on z = 0), read off reference/side.png and front.png
J = dict(
    hips=(0, -0.10, 0.70), chest=(0, -0.48, 0.76), neck0=(0, -0.80, 0.78),
    neck1=(0, -0.92, 0.96), head=(0, -0.97, 1.16), bill=(0, -1.36, 1.12),
    tail0=(0, 0.25, 0.38), tail1=(0, 0.55, 0.30), tail2=(0, 0.92, 0.27), tail3=(0, 1.34, 0.27),
    hipL=(0.12, -0.42, 0.69), kneeL=(0.13, -0.43, 0.52), hockL=(0.125, -0.32, 0.34),     # team pass: longer legs
    ankleL=(0.125, -0.46, 0.06), toeL=(0.13, -0.70, 0.02),
    shoulderL=(0.19, -0.60, 0.82), wristL=(0.30, -0.70, 1.05), tipL=(0.30, 0.26, 0.36),
)

# ---- the carve input, redrawn where a visual hull cannot work (logged in NOTES.md)
# side view (y, z) polygons cleared: the horns (stage-3 pieces), the folded wing where it hangs below the
# belly behind the leg (it would carve a slab under the tail base), the tail behind y 0.42 (hand-built rings)
SIDE_CLEAR = [
    [(-0.99, 1.325), (-0.50, 1.325), (-0.50, 1.50), (-0.99, 1.50)],
    [(-0.24, 0.375), (0.42, 0.265), (0.42, -0.01), (-0.24, -0.01)],
    [(0.42, -0.01), (1.45, -0.01), (1.45, 0.60), (0.42, 0.60)],
]
# front view: the folded wings beside the torso are cleared (they are extruded from the shoulder instead), so
# the torso keeps its own width: half width per height (z, x)
FRONT_W = [(0.27, 0.18), (0.45, 0.19), (0.55, 0.215), (0.70, 0.225), (0.85, 0.22), (0.95, 0.20), (1.05, 0.17)]
# top view: the same for the plan (the folded wings merge with the flank between y -0.5 and 0): half width per y
TOP_W = [(-0.80, 0.17), (-0.65, 0.21), (-0.45, 0.225), (-0.20, 0.21), (0.0, 0.16), (0.15, 0.10)]
HORN_Z = 1.31          # front view above this (outside the crown |x| < 0.07) is horn: cleared


def interp(tab, z):
    if z <= tab[0][0]:
        return tab[0][1]
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z <= z1:
            return a + (b - a) * (z - z0) / (z1 - z0)
    return tab[-1][1]


def _inside(P, Y, Z):
    P = np.array(P)
    ins = np.zeros(Y.shape, bool)
    for i in range(len(P)):
        (y1, z1), (y2, z2) = P[i], P[i - 1]
        c = ((z1 > Z) != (z2 > Z)) & (Y < (y2 - y1) * (Z - z1) / (z2 - z1 + 1e-12) + y1)
        ins ^= c
    return ins


def _reint(vw):
    m = vw.mask
    m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
    I = np.zeros((m.shape[0] + 1, m.shape[1] + 1), np.float64)
    I[1:, 1:] = m.astype(np.float64).cumsum(0).cumsum(1)
    vw.I = I


def fix_masks(k):
    views = load_ref(k.dir)
    sd = views['side']
    H, W = sd.mask.shape
    R, C = np.mgrid[0:H, 0:W].astype(np.float64)
    Z = (sd.ground - sd.r0 - R) * sd.s
    Y = (C + sd.c0 - sd.cmid) * sd.s
    m = sd.mask.copy()
    for P in SIDE_CLEAR:
        m[_inside(P, Y, Z)] = False
    sd.mask = m
    _reint(sd)
    fr = views['front']
    H, W = fr.mask.shape
    R, C = np.mgrid[0:H, 0:W].astype(np.float64)
    Z = (fr.ground - fr.r0 - R) * fr.s
    X = np.abs((C + fr.c0 - fr.axis) * fr.s)
    wz = np.vectorize(lambda z: interp(FRONT_W, z))(Z)
    m = fr.mask.copy()
    m[(Z > 0.27) & (Z < 1.06) & (X > wz)] = False
    m[(Z > 0.45) & (Z < 1.06) & (X <= wz)] = True       # the torso the wings hide in the sheet
    m[(Z > HORN_Z) & (X > 0.07)] = False
    fr.mask = m
    _reint(fr)
    tp = views['top']
    H, W = tp.mask.shape
    R, C = np.mgrid[0:H, 0:W].astype(np.float64)
    X = np.abs((R + tp.r0 - tp.axis) * tp.s)
    Y = (C + tp.c0 - tp.cmid) * tp.s
    wy = np.vectorize(lambda y: interp(TOP_W, y))(Y)
    m = tp.mask.copy()
    m[(Y > -0.80) & (Y < 0.15) & (X > wy)] = False
    m[(Y > -0.80) & (Y < 0.15) & (X <= wy)] = True
    tp.mask = m
    _reint(tp)


# ---- hand-built parts grafted onto the hull
PROF = ((0.0, 0.0), (0.22, 0.8), (0.55, 1.0), (0.85, 0.62), (1.0, 0.0))
TAIL_CUT = 0.14
# tail sections behind the cut: y, dorsal z, ventral z, half width (the sheet's side view; a vertical spade fin)
TAIL = [(0.24, 0.455, 0.305, 0.080), (0.38, 0.390, 0.275, 0.060), (0.54, 0.335, 0.252, 0.044), (0.72, 0.305, 0.240, 0.033),
        (0.90, 0.293, 0.234, 0.027), (1.00, 0.315, 0.205, 0.022), (1.13, 0.385, 0.150, 0.016),
        (1.27, 0.445, 0.100, 0.010), (1.36, 0.400, 0.150, 0.007)]


def tsec(y, zd, zv, w):
    return [(xf * w, y, zd + s * (zv - zd)) for s, xf in PROF]


def zip_rows(bm, A, B):
    """Triangles between two seam-to-seam rows of different lengths, advancing by arc-length parameter."""
    def par(R):
        L = [0.0]
        for p, q in zip(R, R[1:]):
            L.append(L[-1] + (q.co - p.co).length)
        return [l / L[-1] for l in L]
    ta, tb = par(A), par(B)
    i = j = 0
    while i < len(A) - 1 or j < len(B) - 1:
        if j == len(B) - 1 or (i < len(A) - 1 and ta[i + 1] <= tb[j + 1]):
            bm.faces.new([A[i], A[i + 1], B[j]]); i += 1
        else:
            bm.faces.new([A[i], B[j + 1], B[j]]); j += 1


def zip_loops(bm, A, B, c, n):
    """Triangles between two closed loops round the axis (c, n), merged by angle."""
    n = Vector(n).normalized()
    u = n.orthogonal().normalized(); w = n.cross(u)
    ang = lambda v: math.atan2((v.co - c).dot(w), (v.co - c).dot(u)) % (2 * math.pi)
    A = sorted(A, key=ang); B = sorted(B, key=ang)
    ta = [ang(v) for v in A] + [2 * math.pi + ang(A[0])]
    tb = [ang(v) for v in B] + [2 * math.pi + ang(B[0])]
    A = A + [A[0]]; B = B + [B[0]]
    i = j = 0
    while i < len(A) - 1 or j < len(B) - 1:
        if j == len(B) - 1 or (i < len(A) - 1 and ta[i + 1] <= tb[j + 1]):
            bm.faces.new([A[i], A[i + 1], B[j]]); i += 1
        else:
            bm.faces.new([A[i], B[j + 1], B[j]]); j += 1


def next_ring(prev, pts):
    """Order pts (a closed ring) for the least twist against the previous ring."""
    pts = [Vector(p) for p in pts]
    n, best = len(pts), None
    for d in (1, -1):
        for s in range(n):
            order = [pts[(s + d * i) % n] for i in range(n)]
            cost = sum((o.co - p).length for o, p in zip(prev, order))
            if best is None or cost < best[0]:
                best = (cost, order)
    return best[1]


def frame_box(c, d, a, b, up=(0, 0, 1)):
    """4 points round c across direction d: half sizes a (along up') and b (across)."""
    c, d = Vector(c), Vector(d).normalized()
    u = Vector(up) - d * Vector(up).dot(d); u.normalize()
    s = d.cross(u).normalized()
    return [c + u * a + s * b, c - u * a + s * b, c - u * a - s * b, c + u * a - s * b]


# the folded wing (= forelimb): shoulder socket on the flank -> elbow -> wrist knuckle (up), then the membrane
# blade folded back-down along the flank to the tip under the tail base
WING_ARM = [
    lambda P: frame_box(P + Vector((0.035, 0.0, 0.01)), (1, 0, 0.35), 0.045, 0.04),
    lambda P: frame_box(J['wristL'], (0.35, -0.3, 1), 0.03, 0.035, up=(0, -1, 0)),
]
# the blade grows from the back face of the forearm strut (a branch, as in k3): a flat diamond across the
# membrane, then the tip
WING_BLADE = [
    # team second pass (must-fix 2): the blade rides the raised torso (it hung below the new belly and hid the leg)
    [(0.325, -0.05, 0.74), (0.385, -0.24, 0.62), (0.365, -0.42, 0.525), (0.31, -0.24, 0.635)],
    [(0.33, 0.22, 0.35), (0.355, 0.20, 0.32), (0.35, 0.17, 0.30), (0.325, 0.20, 0.32)],
]


def grow(bm, face, pts):
    """Extrude one face and place its new ring at pts (cyclic order chosen for the least twist)."""
    old = list(face.verts)
    r = extrude(bm, [face])
    nf = r['faces'][0]
    part = {}
    for v in nf.verts:
        for e in v.link_edges:
            w = e.other_vert(v)
            if w in old:
                part[w] = v
    new = [part[o] for o in old]
    for v, p in zip(new, next_ring(old, pts)):
        v.co = p
    bm.normal_update()
    return nf


SOCKET_R = 0.06
LEG_FOOT, LEG_B0, LEG_B1, LEG_TOP, LEG_HOCK, LEG_LEAN = 0.035, 0.31, 0.50, 0.90, 0.34, 0.08


def leg_z(z):
    """Team pass: the carved hull's height remap (feet kept, legs stretched, torso compressed, head kept)."""
    if z <= LEG_FOOT or z >= LEG_TOP:
        return z
    if z <= LEG_B0:
        return LEG_FOOT + (z - LEG_FOOT) * (LEG_B1 - LEG_FOOT) / (LEG_B0 - LEG_FOOT)
    return LEG_B1 + (z - LEG_B0) * (LEG_TOP - LEG_B1) / (LEG_TOP - LEG_B0)


def leg_dy(z):
    """The shank leans back (+y) from the foot up to the hock, the thigh comes forward again up to the belly."""
    if z <= LEG_FOOT or z >= LEG_B1 + 0.02:
        return 0.0
    if z <= LEG_HOCK:
        return LEG_LEAN * (z - LEG_FOOT) / (LEG_HOCK - LEG_FOOT)
    return LEG_LEAN * (LEG_B1 + 0.02 - z) / (LEG_B1 + 0.02 - LEG_HOCK)
WING_FB, WING_TB, WING_TIP = (-0.45, 0.53), (-0.02, 0.74), (0.27, 0.37)     # team pass: the blade's front-bottom corner and tip (y, z)
WING_TUCK = (0.0, 0.05)                            # the blade moved in toward the flank: bottom, top edge
WING_CONV = 0.0                                     # second pass: the blade converging on the tail base in plan (IoU: 0)
WING_WEBZ = 0.66
WING_FBIN = 0.12                                    # second pass: the front-bottom corner in against the flank
SPAR_Y = (-0.30, -0.09, 0.12)                       # the spars' ends on the trailing edge (y)
WING_ARMF = 0.36                                    # the dark arm band: the top fraction of the blade's height


def _lerp_line(P, y):
    for (y0, z0), (y1, z1) in zip(P, P[1:]):
        if y <= y1:
            return z0 + (z1 - z0) * max(0.0, (y - y0)) / (y1 - y0)
    return P[-1][1]


def ridge_z(y):      # the blade's top edge (the folded arm and finger ridge), side view
    return _lerp_line(((-0.70, 1.05), WING_TB, WING_TIP), y)


def trail_z(y):      # the blade's trailing edge, side view
    return _lerp_line((WING_FB, WING_TIP), y)


def band_z(y):       # the arm band's lower border on the blade
    r = ridge_z(y)
    return r - WING_ARMF * (r - trail_z(y))


def in_blade(c):     # a blade vertex (either side): behind the forearm strut, out on the flank
    x = abs(c.x)
    return (x > 0.235 and c.y > -0.5 and c.z < 0.75) or (x > 0.27 and c.y > -0.68 and c.z < 1.0)


def stage1(k):
    import hashlib
    key = hashlib.sha256(repr((SIDE_CLEAR, FRONT_W, HORN_Z, TOP_W)).encode()).hexdigest()
    kf, cf = os.path.join(k.dir, 'carve_mask.key'), os.path.join(k.dir, 'carve_base.json')
    if not os.path.exists(kf) or open(kf).read() != key:
        if os.path.exists(cf):
            os.remove(cf)
        open(kf, 'w').write(key)
    fix_masks(k)
    ob = carve_base(k)
    bm = edit(ob)
    # 0. team pass, STAGE-1 UNLOCK (ad_notes_team must-fix 2): longer legs. The hull's z is remapped in front of the
    # tail cut: the legs stretch (belly 0.31 -> LEG_B1), the torso is compressed above it up to LEG_TOP (head, wing
    # socket and tail kept), feet kept; the shank leans back up to a hock (the reversed bend), foot forward of it
    for v in bm.verts:
        x, y, z = v.co
        w = min(1.0, max(0.0, (0.06 - y) / 0.18))
        v.co.z = z + w * (leg_z(z) - z)
        if y < -0.15:
            v.co.y += leg_dy(v.co.z)
    # 1. tail: the hull behind y = TAIL_CUT goes; the rim is zipped to hand-built rings out to the fin
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=0.004,
                           plane_co=Vector((0, TAIL_CUT, 0)), plane_no=Vector((0, 1, 0)), clear_outer=True)
    bnd = [e for e in bm.edges if len(e.link_faces) == 1 and not all(abs(v.co.x) < 1e-5 for v in e.verts)]
    adj = {}
    for e in bnd:
        for v in e.verts:
            adj.setdefault(v, []).append(e.other_vert(v))
    ends = [v for v, l in adj.items() if len(l) == 1]
    say('tail rim: edges', len(bnd), 'ends', [tuple(round(c, 3) for c in v.co) for v in ends])
    A, prev = [max(ends, key=lambda v: v.co.z)], None
    while True:
        nx = [w for w in adj[A[-1]] if w is not prev]
        if not nx:
            break
        prev = A[-1]; A.append(nx[0])
    for v in (A[0], A[-1]):
        v.co.x = 0.0
    rows = [ring(bm, tsec(*t)) for t in TAIL]
    zip_rows(bm, A, rows[0])
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[-1])
    # 2. wings: a socket hole on the flank at the shoulder, zipped to the wing's first ring, then the chain
    tree = BVHTree.FromBMesh(bm)
    P, N, fi, _ = tree.ray_cast(Vector((0.6, J['shoulderL'][1], J['shoulderL'][2])), Vector((-1, 0, 0)))
    say('shoulder surface', tuple(round(c, 3) for c in P), tuple(round(c, 2) for c in N))
    bm.faces.ensure_lookup_table()
    hole = [bm.faces[fi]]
    grown = True
    while grown:     # the edge-connected disc of faces round the hit, centres within SOCKET_R
        grown = False
        for f in list(hole):
            for e in f.edges:
                for g in e.link_faces:
                    if g not in hole and (g.calc_center_median() - P).length < SOCKET_R:
                        hole.append(g); grown = True
    hv = {v for f in hole for v in f.verts}
    bmesh.ops.delete(bm, geom=hole, context='FACES_ONLY')
    loop = [v for v in hv if v.is_valid and any(len(e.link_faces) == 1 for e in v.link_edges)]
    say('socket loop', len(loop), 'hole faces', len(hole))
    for e in [e for e in bm.edges if not e.link_faces]:
        bm.edges.remove(e)
    rings = []
    for mk in WING_ARM:
        pts = mk(P)
        if rings:
            pts = next_ring(rings[-1], pts)
        rings.append(ring(bm, pts))
    zip_loops(bm, loop, rings[0], P, N)
    band = bridge(bm, rings[0], rings[1], closed=True)
    cap(bm, rings[-1])
    recalc_normals(bm)
    f = max(band, key=lambda g: g.normal.y)
    for pts in WING_BLADE:
        f = grow(bm, f, pts)
    recalc_normals(bm)
    snap_seam(bm)
    say('belly z (seam, y -0.55..-0.15):', round(min(v.co.z for v in bm.verts if abs(v.co.x) < 1e-4 and -0.55 < v.co.y < -0.15), 3))
    commit(ob, bm)
    if os.environ.get('RW_DBG'):
        for e in bm.edges:
            if len(e.link_faces) != 2:
                say('OPEN', len(e.link_faces), [tuple(round(c, 3) for c in v.co) for v in e.verts])
        eb = evaluated_bm(ob); eb.faces.ensure_lookup_table(); t = BVHTree.FromBMesh(eb)
        for i, j in t.overlap(t):
            if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
                say('HIT', tuple(round(x, 3) for x in eb.faces[i].calc_center_median()), tuple(round(x, 3) for x in eb.faces[j].calc_center_median()))
    return ob


EYE = (0.10, -1.115, 1.185)           # team pass: the eye on the side of the head at the bill's top line (was on
                                      # the crown's front edge at z 1.232, facing up)


SOCK = []                             # the socket's inner face (centre, normal), set by stage 2 for the lens


def near_eye(c):
    return abs(c[0]) > 0.03 and (Vector((abs(c[0]), c[1], c[2])) - Vector(EYE)).length < 0.05


class _Valleys(str):
    """keep_valleys as a str subclass: the stage-1 lock writes META to JSON (a plain function fails there)."""
    def __call__(self, c):
        return near_eye(c)


META['keep_valleys'] = _Valleys('near_eye')

# colour borders cut into the base (planes): (point, normal, region box)
BILL_BASE = ((0, -1.150, 1.20), (0, 1, -0.35))       # black bill in front of this
BILL_TIP = ((0, -1.342, 1.162), (0, 1, 0.2))         # pale tip in front of this (team: the front 30% of the bill,
                                                      # the plane through the moved tip ring's top and the mandible)
SHANK_Z = 0.47                                        # grey-brown shank below this (legs only; team pass: the longer leg)
in_head = lambda c: c.y < -1.0 and c.z > 0.98
in_leg = lambda c: c.z < SHANK_Z + 0.08 and -0.75 < c.y < -0.15 and 0.02 < abs(c.x) < 0.25
CUTS = {
    'black bill: border loop round the bill base': (*BILL_BASE, in_head),
    'pale bill tip: border loop round the hook': (*BILL_TIP, in_head),
    'grey-brown shank: border loop round each leg at z 0.47': ((0, 0, SHANK_Z), (0, 0, 1), in_leg),
}


def side_of(c, plane):
    co, no = plane
    return (Vector(c) - Vector(co)).dot(Vector(no).normalized())


def V_(bm, p, tol=0.004):
    """The base vertex at a known position; asserts it is there."""
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < tol, ('no vertex at', p, tuple(v.co))
    return v


def cut(k, bm, co, no, box, reason, dist=0.012):
    """A planar loop through the faces whose vertices all satisfy box (bisect_plane, logged as a loop: the carve is
    triangles, so loopcut has no quad ring to follow). Vertices within dist of the plane count as on it."""
    faces = [f for f in bm.faces if all(box(v.co) for v in f.verts)]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    with k.topo(bm, 'loop', reason):
        bmesh.ops.bisect_plane(bm, geom=geom, dist=dist, plane_co=Vector(co), plane_no=Vector(no).normalized())


def stage2(k, body):
    bm = edit(body)
    # --- r01 face planes: the hooked bill (tip forward and down, the lower mandible tucked back under it), the
    # bill base pinched so the bill reads as its own block, an eye socket under a brow
    move([V_(bm, (0.0, -1.335, 1.135))], (0.0, -0.037, -0.05))
    move([V_(bm, (0.0, -1.332, 1.074))], (0.0, 0.03, 0.0))
    move([V_(bm, (0.029, -1.318, 1.111))], (-0.008, -0.012, -0.012))
    move([V_(bm, (0.0, -1.297, 1.172))], (0.0, -0.01, 0.0))
    # team r33 (must-fix 5): the long hooked raven bill: the tip ring 4 cm forward and 1 cm down, half as wide; the
    # tip point a further 1.5 cm down (the hook), the lower mandible only 2 cm forward (it tucks under the hook)
    ringv = [V_(bm, p) for p in ((0.0, -1.372, 1.085), (0.021, -1.33, 1.099), (0.0, -1.307, 1.172), (0.021, -1.297, 1.173))]
    move(ringv, (0.0, -0.04, -0.01))
    for v in ringv:
        v.co.x *= 0.5
    move([ringv[0]], (0.0, 0.0, -0.015))
    move([V_(bm, (0.0, -1.302, 1.074))], (0.0, -0.02, -0.01))
    for p in ((0.063, -1.179, 1.209), (0.048, -1.154, 1.08)):
        v = V_(bm, p); v.co.x *= 0.82                    # bill base pinch
    sock = face_near(bm, EYE, n=(1, 0, 0))
    en = sock.normal.copy()
    sv = set(sock.verts)
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face'):
        inner = inset(bm, [sock], 0.38)
    move(list(inner[0].verts), -0.012 * en)
    move([V_(bm, (0.042, -1.096, 1.275))], (0.022, -0.012, 0.0))      # brow out and forward over the socket
    # team r27: the brow ledge over the side eye: the socket face's top corners out 1 cm and forward
    say('socket verts', [tuple(round(c, 3) for c in v.co) for v in sv])
    brow = [v for v in sv if v.co.z > EYE[2] + 0.01]           # the socket face's top corner(s)
    assert brow, 'no brow vertex over the eye'
    move(brow, (0.012, -0.012, 0.0))
    bm.normal_update()
    SOCK[:] = [inner[0].calc_center_median().copy(), inner[0].normal.copy()]
    # --- r01 tail fin: the trailing edge notched (the end ring's mid point forward, the lobes back)
    end = verts_where(bm, lambda c: abs(c.y - 1.36) < 0.004)
    assert len(end) == 5, len(end)
    for v in end:
        s = (0.40 - v.co.z) / 0.25            # 0 dorsal .. 1 ventral on the old ring
        v.co.y = 1.39 - 0.08 * math.sin(math.pi * min(1.0, max(0.0, s)))
        v.co.z = 0.46 + (0.08 - 0.46) * min(1.0, max(0.0, s))
    # --- r03 the S-neck: the hull's throat is a vertical wall (chin to chest at y -1.07); the throat between
    # z 0.68 and 0.98 is pulled back (up to 7 cm at z 0.83) and the neck narrowed there, so the chest bulges
    # forward under a slimmer curved neck
    for v in bm.verts:
        x, y, z = v.co
        if 0.66 < z < 1.0 and y < -0.86:
            b = math.sin(math.pi * (z - 0.66) / 0.34)
            v.co.y += 0.07 * b * min(1.0, (-0.86 - y) / 0.15)
            v.co.x *= 1.0 - 0.15 * b
    # --- r02 slivers: the wing blade's long faces taper to a tiny tip ring (needle triangles): tip ring 2-3x
    tip = verts_where(bm, lambda c: c.y > 0.1 and c.x > 0.3 and c.z < 0.4)
    assert len(tip) == 4, len(tip)
    scale(tip, (2.0, 3.0, 3.0))
    # --- r04 wing membrane (k3's move): two cross loops put verts on the trailing edge between the finger spars,
    # pulled up into membrane bays (the scalloped edge of the reference's folded wing)
    dia = [V_(bm, p) for p in WING_BLADE[0]]                  # the blade's diamond ring (top, outer, bottom, inner)
    bf, bt = V_(bm, WING_BLADE[0][2]), min(tip, key=lambda v: v.co.z)
    e = next(e for e in bf.link_edges if e.other_vert(bf) is bt)
    with k.topo(bm, 'loop', 'wing membrane: cross loop at the rear spar bay, so the trailing edge can scallop'):
        r1 = loopcut(bm, e, t=0.68, near=bf)
    m1 = min(r1, key=lambda v: v.co.z)
    e = next(e for e in bf.link_edges if e.other_vert(bf) is m1)
    with k.topo(bm, 'loop', 'wing membrane: cross loop at the front spar bay, so the trailing edge can scallop'):
        r2 = loopcut(bm, e, t=0.34, near=bf)
    m2 = min(r2, key=lambda v: v.co.z)
    move([m1, m2], (0.0, 0.0, 0.04))
    # --- team r10 the tapered folded wing: the blade (diamond, bays, tip) is mapped in the side plane piecewise
    # affinely (above / below the wrist-tip line): it keeps the wrist, lifts the front-bottom corner under the shoulder and sends the tip up and
    # back beside the tail base; then the blade is tucked in against the flank (top edge most)
    blade = verts_where(bm, lambda c: c.x > 0.27 and c.y > -0.5 and c.z < 0.80)
    say('blade verts', len(blade))
    W, T0 = (-0.70, 1.05), (0.1975, 0.3225)
    tri = lambda a, b: np.linalg.solve(np.array([[y, z, 1.0] for y, z in (W, a, T0)]), np.array([W, b, WING_TIP]))
    Mu, Ml = tri((-0.05, 0.74), WING_TB), tri((-0.42, 0.525), WING_FB)     # above / below the wrist-tip line
    for v in blade:
        y, z = v.co.y, v.co.z
        above = z > W[1] + (T0[1] - W[1]) * (y - W[0]) / (T0[0] - W[0])
        v.co.y, v.co.z = np.array([y, z, 1.0]) @ (Mu if above else Ml)
    for v in blade:
        t = min(1.0, max(0.0, (v.co.z - 0.60) / 0.14))
        v.co.x -= WING_TUCK[0] + (WING_TUCK[1] - WING_TUCK[0]) * t + WING_CONV * min(1.0, max(0.0, (v.co.y + 0.30) / 0.55))
    bf.co.x -= WING_FBIN          # second pass: the front-bottom corner in against the flank (closes the front view's daylight)
    say('blade', [tuple(round(c, 3) for c in v.co) for v in blade])
    # second pass (must-fix 1, the daylight in az000): the strut's two lower shoulder points slide down the flank, so
    # its underside is a web from the flank to the wrist, in the plane of the leading edge (the plan view keeps: the
    # strut already covers it)
    web = sorted(verts_where(bm, lambda c: 0.22 < c.x < 0.275 and -0.66 < c.y < -0.54 and 0.74 < c.z < 0.90), key=lambda v: (v.co.z, v.co.y))[:2]
    say('web verts', [tuple(round(c, 3) for c in v.co) for v in web])
    tree = BVHTree.FromBMesh(bm)
    for v in web[:1]:
        y = v.co.y
        loc = tree.ray_cast(Vector((0.001, y, WING_WEBZ)), Vector((1, 0, 0)))[0]
        v.co = Vector((loc.x + 0.05, y, WING_WEBZ))
    # the blade's mid lines (each ring's outer and inner points: the diamond, the two bay loops, the tip ring) slide
    # up to the arm band border, so the dark arm is the top third of the blade and the purple the bays below
    for rg in (dia, r1, r2, tip):
        for v in sorted(rg, key=lambda v: v.co.z)[1:3]:
            v.co.z = band_z(v.co.y)
    bm.normal_update()
    # --- r01 colour borders on edge loops (planar cuts)
    for name, (co, no, box) in CUTS.items():
        cut(k, bm, co, no, box, name)
    commit(body, bm)
    if os.environ.get('RW_DBG'):
        eb = evaluated_bm(body); eb.faces.ensure_lookup_table(); t = BVHTree.FromBMesh(eb)
        for i, j in t.overlap(t):
            if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
                say('HIT', [tuple(round(x, 3) for x in v.co) for v in eb.faces[i].verts], [tuple(round(x, 3) for x in v.co) for v in eb.faces[j].verts])


BRIEF = dict(plumage='#2c3346', membrane='#6a3f9a', bill='#1c1c22', billtip='#d8cfb8',
             eye='#f0a020', shank='#6e665e', horn='#e4dcc8')
Z = Vector((0, 0, 1))
RUFF = '#4e5262'                      # the throat ruff: one step lighter than the plumage (team notes)
# the throat ruff wedges: (y, z) of the root on the neck's side (found by a ray from +X), direction, length
HACKLES = (((-1.05, 1.01), (0.0, 0.3, -1.0), 0.11), ((-1.00, 0.93), (0.0, 0.3, -1.0), 0.12),
           ((-0.97, 0.85), (0.0, 0.25, -1.0), 0.115))


def _rgb(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def sheet_palette(k, body):
    """colour_from_sheet's clusters, each brief role taking its nearest sheet colour where one is near (the sheet's
    own values); the paint itself is by rules on the stage-2 loops, so the borders are clean."""
    sheet = colour_from_sheet(k, [body])
    say(f'sheet clusters: {sheet}')
    pal = {}
    for role, h in BRIEF.items():
        best = min(sheet.values(), key=lambda s: sum((p - q) ** 2 for p, q in zip(_rgb(s), _rgb(h))))
        d = sum((p - q) ** 2 for p, q in zip(_rgb(best), _rgb(h))) ** 0.5
        pal[role] = best if d < 40 and best not in pal.values() else h
    say(f'palette (sheet where near, else brief): {pal}')
    return pal


def around(c, d, r1, r2, n=4, phase=45.0, up=None):
    c, d = Vector(c), Vector(d).normalized()
    if up is not None:
        up = Vector(up)
        u = up - d * up.dot(d)
    else:
        u = d.cross(Z) if abs(d.dot(Z)) < 0.95 else d.cross(Vector((1, 0, 0)))
    u.normalize(); v = d.cross(u).normalized()
    return [c + u * (r1 * math.cos(math.radians(phase + 360.0 * i / n))) + v * (r2 * math.sin(math.radians(phase + 360.0 * i / n)))
            for i in range(n)]


def tube(bm, centres, radii, tip, flat=1.0, up=None, n=4, phase=45.0):
    """A tapered n-gon spike through centres, closed at the root, ending in a point (k3's)."""
    rs = []
    for i, c in enumerate(centres):
        d = Vector(centres[min(i + 1, len(centres) - 1)]) - Vector(centres[max(i - 1, 0)])
        rs.append(ring(bm, around(c, d, radii[i], radii[i] * flat, n=n, up=up, phase=phase)))
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, rs[0])
    t = bm.verts.new(Vector(tip))
    m = len(rs[-1])
    for i in range(m):
        bm.faces.new([rs[-1][i], rs[-1][(i + 1) % m], t])


def body_rule(body):
    me = body.data
    fv = [[Vector((abs(me.vertices[j].co.x), me.vertices[j].co.y, me.vertices[j].co.z)) for j in p.vertices] for p in me.polygons]
    tol = 0.013

    def rule(c, n, i):
        vs = fv[i]
        c = Vector((abs(c.x), c.y, c.z))
        if near_eye(c) and n.x * (1 if c.x >= 0 else -1) > -1:
            return 'bill'                                   # the dark face mask round the eye
        if all(in_head(v) and side_of(v, BILL_TIP) < tol for v in vs):
            return 'billtip'
        if all(in_head(v) and side_of(v, BILL_BASE) < tol for v in vs):
            return 'bill'
        if all(v.y > 0.99 for v in vs):
            return 'membrane'                               # the fin (behind the y 1.0 tail ring)
        if c.x > 0.235 and c.y > -0.66 and c.z < 1.0:       # the wing blade: the dark arm band over purple bays
            # (the strut's back-face points at the root count as on the band: they are the arm)
            dark = all(v.z > (0.60 if v.y < -0.5 else band_z(v.y)) - 0.012 for v in vs)
            return 'plumage' if dark else 'membrane'
        if all(v.z < SHANK_Z + tol for v in vs) and c.y < -0.15:
            return 'shank'
        return 'plumage'
    return rule


def piece(name, bm, key, pal, mirror=True):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: pal[key]}, lambda c, n, i: key)
    return ob


def stage3(k, body):
    pal = sheet_palette(k, body)
    paint(body, pal, body_rule(body))
    bm0 = edit(body)
    tree = BVHTree.FromBMesh(bm0)
    hit = lambda o, d: tree.ray_cast(Vector(o), Vector(d).normalized())
    pieces = []
    # eye: a 6-sided amber lens in the socket, proud of the rim, turned 15 deg along the bill
    # team r27: on the side of the head (the socket found by a ray from +X), facing out and ~30 deg forward,
    # 25% larger than before
    ec, en = SOCK[0].copy(), SOCK[1].copy()
    en = (en + Vector((math.cos(math.radians(30)), -math.sin(math.radians(30)), 0))).normalized()
    say('eye at', tuple(round(q, 3) for q in ec), 'facing', tuple(round(q, 2) for q in en))
    c = ec + en * 0.019 + Vector((0, -0.004, -0.012))        # proud of the socket, tucked under the brow ledge
    bm = bmesh.new()
    vs = ring(bm, around(c, en, 0.037, 0.030, n=6, phase=0.0, up=(0, 0, 1)))
    fp, bp = bm.verts.new(c + en * 0.012), bm.verts.new(c - en * 0.014)
    for i in range(6):
        bm.faces.new([vs[i], vs[(i + 1) % 6], fp]); bm.faces.new([vs[(i + 1) % 6], vs[i], bp])
    pieces.append(piece('eye', bm, 'eye', pal))
    # horns: swept back and up from the crown behind the eye (the sheet's side and front views)
    bm = bmesh.new()
    tube(bm, [(0.05, -0.99, 1.24), (0.08, -0.93, 1.32), (0.11, -0.86, 1.365), (0.14, -0.79, 1.395)],
         [0.034, 0.027, 0.019, 0.011], (0.16, -0.72, 1.43), n=5)
    pieces.append(piece('horn', bm, 'horn', pal))
    # claws: the thumb hook on the wrist knuckle; three talons per foot + the hallux, rooted by rays
    bm = bmesh.new()
    w = Vector(J['wristL'])
    tube(bm, [w + Vector((0, -0.005, 0.0)), w + Vector((0.005, -0.06, 0.055)), w + Vector((0.01, -0.115, 0.05))],
         [0.03, 0.024, 0.016], w + Vector((0.01, -0.15, -0.005)))
    for x, dx in ((0.065, -0.3), (0.125, 0.0), (0.185, 0.3)):
        p = hit((x, -1.2, 0.03), (0, 1, 0))[0]
        assert p is not None, ('toe ray missed', x)
        r = Vector((x, p.y + 0.02, 0.03))
        tube(bm, [r, r + Vector((dx * 0.06, -0.07, 0.025)), r + Vector((dx * 0.10, -0.125, 0.018))],
             [0.024, 0.019, 0.012], r + Vector((dx * 0.13, -0.17, -0.025)))
    p = hit((0.13, 0.2, 0.03), (0, -1, 0))[0]
    assert p is not None
    r = Vector((0.13, p.y - 0.015, 0.03))
    tube(bm, [r, r + Vector((0, 0.05, 0.02)), r + Vector((0, 0.095, 0.012))], [0.02, 0.015, 0.01], r + Vector((0, 0.125, -0.026)))
    pieces.append(piece('claws', bm, 'bill', pal))
    # finger spars (team r12): three tapered rods radiating from the wrist knuckle down and back across the purple
    # bays to the trailing edge; each starts just above the arm band border; each ring sits on the blade (ray)
    bm = bmesh.new()
    K = Vector((-0.66, 1.0))
    from mathutils.geometry import intersect_ray_tri
    bm0.faces.ensure_lookup_table()

    def outer(yz):
        """The blade's outer surface at (y, z) seen from +X, whichever way its non-planar quads get split."""
        loc, nrm, fi, _ = hit((0.8, yz.x, yz.y), (-1, 0, 0))
        if loc is None:
            return None, None
        vs = [v.co for v in bm0.faces[fi].verts]
        best = (loc, nrm)
        o, d = Vector((0.8, yz.x, yz.y)), Vector((-1, 0, 0))
        tris = [(vs[0], vs[1], vs[2]), (vs[0], vs[2], vs[3]), (vs[0], vs[1], vs[3]), (vs[1], vs[2], vs[3])] if len(vs) == 4 else []
        for t in tris:
            p = intersect_ray_tri(*t, d, o, True)
            if p is not None and p.x > best[0].x:
                n = (t[1] - t[0]).cross(t[2] - t[0]).normalized()
                best = (p, n if n.x > 0 else -n)
        return best
    for ye in SPAR_Y:
        E = Vector((ye, trail_z(ye) + 0.012))
        s0 = next(t / 100 for t in range(100) if K.lerp(E, t / 100).y < band_z(K.lerp(E, t / 100).x) + 0.03)
        on = lambda t: (lambda h: h[0] is not None and h[0].x > 0.3)(hit((0.8, *K.lerp(E, t)), (-1, 0, 0)))
        s1 = max(t / 100 for t in range(int(s0 * 100), 125) if on(t / 100)) - 0.02
        cs, rs = [], (0.017, 0.0165, 0.016, 0.0155, 0.015, 0.0145, 0.014)
        for s_, r in zip([s0 + (s1 - 0.05 - s0) * i / 6 for i in range(7)], rs):
            yz = K.lerp(E, s_)
            loc, nrm = outer(yz)
            assert loc is not None, ('spar ray missed', yz)
            cs.append(loc + nrm * (0.75 * r))
        yz = K.lerp(E, s1)
        loc, nrm = outer(yz)
        say('spar', ye, 's', s0, s1, 'from', tuple(round(c, 2) for c in cs[0]), 'to', tuple(round(c, 2) for c in loc))
        # triangular section, one corner sunk in the blade (no face parallel to it: no z-fight)
        tube(bm, cs, rs, loc + nrm * 0.004, up=(1, 0, 0), n=3, phase=180.0, flat=1.3)
    pieces.append(piece('spar', bm, 'plumage', pal))
    # dorsal spines: graded plates on the ridge (found by rays down the seam), big over the shoulders, small on
    # the tail; dark with horn-coloured tips (k3's form)
    def ridge(y):
        loc = hit((0.0005, y, 2.0), (0, 0, -1))[0]
        assert loc is not None, ('ridge ray missed', y)
        return loc.z
    bm = bmesh.new()
    N, tipf = 13, []
    lean = math.tan(math.radians(25))
    for j in range(N):
        u = j / (N - 1)
        y = -0.66 + 1.62 * u * (1.35 - 0.35 * u)
        g = 1.0 - 0.15 * (y + 0.66) / 0.46 if y < -0.20 else 0.85 - 0.55 * (y + 0.20) / 1.16
        h, L = 0.13 * g, 0.055 * g
        ws = 0.6 * L
        zr = min(ridge(y - L), ridge(y), ridge(y + L))
        base = [Vector((0, y - L, zr - 0.03)), Vector((ws, y, zr - 0.035)), Vector((0, y + L, zr - 0.03)), Vector((-ws, y, zr - 0.035))]
        bv = ring(bm, base)
        m = 0.6 * h
        mc = Vector((0, y + 0.15 * L + m * lean, zr + m - 0.02))
        mv = ring(bm, [mc + (q - Vector((0, y, zr - 0.033))) * 0.42 for q in base])
        bridge(bm, bv, mv, closed=True)
        tp = bm.verts.new(Vector((0, y + 0.3 * L + h * lean, zr + h)))
        cap(bm, bv)
        for i in range(4):
            tipf.append(bm.faces.new([mv[i], mv[(i + 1) % 4], tp]))
    bm.faces.index_update()
    tips = {f.index for f in tipf}
    ob = object_from_bm('spines', bm, mirror=False)
    paint(ob, {'plumage': pal['plumage'], 'horn': pal['horn']}, lambda c, n, i: 'horn' if i in tips else 'plumage')
    pieces.append(ob)
    # hackles (team r32): a ruff of 3 wedges per side at the throat only, under the jaw, hanging down and back along
    # the stage-2 throat hollow (11-12 cm long, 7 cm wide, rooted 3 cm in), one step lighter than the plumage; the
    # nape is left to the dorsal spines
    bm = bmesh.new()
    for (y, z), dirn, ln in HACKLES:
        loc, nrm, _, _ = hit((0.6, y, z), (-1, 0, 0))
        assert loc is not None, ('hackle ray missed', y, z)
        o = (nrm + Vector((0.4, 0, 0))).normalized()
        tg = Vector(dirn); tg = (tg - o * tg.dot(o)).normalized()
        dr = tg * math.cos(math.radians(25)) + o * math.sin(math.radians(25))
        W, T = 0.62 * ln, 0.3 * ln
        root = loc - o * 0.03
        tip = root + dr * ln + o * 0.03
        mid = root.lerp(tip, 0.4) + o * 0.04
        r = T / 2 / 0.707
        tube(bm, [root, mid], [r, 0.8 * r], tip, flat=W / T, up=o)
    pal['ruff'] = RUFF
    pieces.append(piece('hackles', bm, 'ruff', pal))
    bm0.free()
    return pieces


def pin_blade(body):
    """The folded blade (|x| >= 0.27 behind the wrist) is weighted 100% to its side's hand bone (heat weights leak
    the thigh onto it: the walk would swing it through the flank); the wing root on the flank gives its thigh
    weight to the chest (k3's fix)."""
    for side, bone in ((1, 'hand.L'), (-1, 'hand.R')):
        ids = [v.index for v in body.data.vertices if (side * v.co.x >= 0.27 and v.co.y > -0.68 and v.co.z < 1.0)
               or (side * v.co.x >= 0.25 and v.co.z > 0.97 and v.co.y > -0.8)]     # + the wrist ring
        for g in body.vertex_groups:
            g.remove(ids)
        body.vertex_groups[bone].add(ids, 1.0, 'REPLACE')
        th, ch = body.vertex_groups['thigh' + bone[-2:]], body.vertex_groups['chest']
        for v in body.data.vertices:
            c = v.co
            if side * c.x > 0.17 and -0.8 < c.y < -0.45 and c.z > 0.6:
                w = next((g.weight for g in v.groups if g.group == th.index), 0.0)
                if w > 0:
                    th.remove([v.index]); ch.add([v.index], w, 'ADD')


def pin_to(ob, pred, name):
    for side, bone in ((1, name + '.L'), (-1, name + '.R')):
        ids = [v.index for v in ob.data.vertices if side * v.co.x > 0 and pred(v.co)]
        if not ids:
            continue
        for g in ob.vertex_groups:
            g.remove(ids)
        (ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)).add(ids, 1.0, 'REPLACE')


def copy_weights(ob, body, pred, root_of):
    """Each matching piece vertex (per side) takes the skin weights of the body vertex nearest root_of(side):
    a rigid hook that rides the knuckle or the toe it grows from (no drift)."""
    for side in (1, -1):
        r = root_of(side)
        src = min(body.data.vertices, key=lambda v: (v.co - r).length)
        ws = {body.vertex_groups[g.group].name: g.weight for g in src.groups if g.weight > 0}
        ids = [v.index for v in ob.data.vertices if side * v.co.x > 0 and pred(v.co)]
        for g in ob.vertex_groups:
            g.remove(ids)
        for nm, w in ws.items():
            (ob.vertex_groups.get(nm) or ob.vertex_groups.new(name=nm)).add(ids, w, 'REPLACE')


def rigid_shells(ob, body):
    """Each connected shell of a piece takes, whole, the skin weights of the body vertex nearest its root (the
    shell's lowest-index ring = its root ring): broad hackle wedges ride the neck without folding."""
    me = ob.data
    adj = {i: set() for i in range(len(me.vertices))}
    for e in me.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    seen = set()
    for i in range(len(me.vertices)):
        if i in seen:
            continue
        comp, st = [], [i]
        seen.add(i)
        while st:
            x = st.pop(); comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); st.append(y)
        root = sum((me.vertices[j].co for j in sorted(comp)[:4]), Vector()) / 4
        near = [v for v in body.data.vertices if (v.co - root).length < 0.07] or             [min(body.data.vertices, key=lambda v: (v.co - root).length)]
        ws = {}
        for v in near:                       # the mean skin weights round the root
            for g in v.groups:
                nm = body.vertex_groups[g.group].name
                ws[nm] = ws.get(nm, 0.0) + g.weight / len(near)
        for g in ob.vertex_groups:
            g.remove(comp)
        for nm, w in ws.items():
            (ob.vertex_groups.get(nm) or ob.vertex_groups.new(name=nm)).add(comp, w, 'REPLACE')


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hips'], J['chest'], None),
        ('chest', J['chest'], J['neck0'], 'hips', True),
        ('neck0', J['neck0'], J['neck1'], 'chest', True),
        ('neck1', J['neck1'], J['head'], 'neck0', True),
        ('head', J['head'], J['bill'], 'neck1', True),
        ('tail0', J['hips'], J['tail0'], 'hips'),
        ('tail1', J['tail0'], J['tail1'], 'tail0', True),
        ('tail2', J['tail1'], J['tail2'], 'tail1', True),
        ('tail3', J['tail2'], J['tail3'], 'tail2', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L', True),
        ('tarsus.L', J['hockL'], J['ankleL'], 'shin.L', True),
        ('toe.L', J['ankleL'], J['toeL'], 'tarsus.L', True),
        ('arm.L', J['shoulderL'], J['wristL'], 'chest'),
        ('hand.L', J['wristL'], J['tipL'], 'arm.L', True),
    ], roll='auto')
    skin(body, rig)
    pin_blade(body)
    for p in pieces:
        bind(p, rig, body=body)
        if p.name.endswith('spar'):
            pin_to(p, lambda c: True, 'hand')                 # the spars ride the blade
        if p.name.endswith('claws'):
            w = Vector(J['wristL'])
            copy_weights(p, body, lambda c: c.z > 0.9, lambda s: Vector((s * w.x, w.y, w.z)))
    # idle: breathing and a curious head tilt
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'head': (0, 0, 7), 'neck1': (-3, 0, 0)},
                       24: {'chest': (-1, 0, 0), 'head': (0, 0, 0)},
                       36: {'chest': (2, 0, 0), 'head': (0, 0, -6), 'neck1': (3, 0, 0)}, 48: {}})
    # move: bird-like stalking walk, head bobbing, tail swaying
    A, B = 14, 12
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'neck1': (6, 0, 0), 'tail1': (0, 0, 5), 'hips': (0, 0, 3)},
        9: {'thigh.R': (5, 0, 0), 'shin.R': (-B, 0, 0), 'tarsus.R': (2 * B, 0, 0), 'neck1': (-4, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'neck1': (6, 0, 0), 'tail1': (0, 0, -5), 'hips': (0, 0, -3)},
        25: {'thigh.L': (5, 0, 0), 'shin.L': (-B, 0, 0), 'tarsus.L': (2 * B, 0, 0), 'neck1': (-4, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'neck1': (6, 0, 0), 'tail1': (0, 0, 5), 'hips': (0, 0, 3)}})
    # attack: coil back, lunge the neck with the wings mantled up and out, recover
    # the mantle turns the whole wing on the arm bone (the hand stays straight on it): the blade's faces span the
    # shoulder socket and the wrist, so a wrist bend would shear them under the spars (drift)
    def arms(x, z, hx=None, roll=0):
        return {'arm.L': (x, roll, z), 'arm.R': (x, -roll, -z)}
    MANTLE = dict(z=30, roll=20)
    clip(rig, 'attack', {
        1: {},
        12: {'neck0': (-12, 0, 0), 'neck1': (-8, 0, 0), 'head': (8, 0, 0), **arms(12, 15)},
        17: {'neck0': (16, 0, 0), 'neck1': (12, 0, 0), 'chest': (7, 0, 0), 'tail1': (4, 0, 0), **arms(18, **MANTLE)},
        20: {'neck0': (26, 0, 0), 'neck1': (20, 0, 0), 'head': (-8, 0, 0), 'chest': (11, 0, 0), 'tail1': (6, 0, 0),
             **arms(18, **MANTLE)},              # team r35 (should-fix): a longer lunge, the chest pitched ~10 deg
        23: {'neck0': (18, 0, 0), 'neck1': (14, 0, 0), 'head': (-4, 0, 0), 'chest': (8, 0, 0), 'tail1': (5, 0, 0),
             **arms(18, **MANTLE)},
        30: {'neck0': (6, 0, 0), 'neck1': (4, 0, 0), **arms(8, 10)},
        40: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
