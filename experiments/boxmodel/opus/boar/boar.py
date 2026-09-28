"""Wild boar: a staged box model (stage 1 blockout -> 4 rig and clips).

Facing -Y, left flank +X, feet on z = 0. The left half is modelled; the kit mirrors it.
The body is one loft of 6-vertex half rings (a 10-sided section with a spine ridge,
a back plane, the widest flank point, a lower flank, a belly side and a keel), from
the flat nose disc to the tail tip. Legs are extruded from two stacked lower-flank
faces, so each leg is a hexagon with flat outer/inner sides and a front/back ridge,
and its bottom splits into two toe blocks: the cloven hoof.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='boar', model='opus', engine_glb='')

# The skeleton the model is built on (stage 1 places the leg levels on it; stage 4 rigs it).
J = dict(
    pelvis=(0.0, 0.40, 0.60), spine=(0.0, 0.10, 0.66), chest=(0.0, -0.12, 0.68),
    neck=(0.0, -0.24, 0.66), head=(0.0, -0.34, 0.64), snout=(0.0, -0.80, 0.45),
    jaw=(0.0, -0.40, 0.48), jaw_tip=(0.0, -0.74, 0.40),
    ear=(0.15, -0.30, 0.77), ear_tip=(0.20, -0.33, 0.925),
    tail=(0.0, 0.59, 0.572), tail_tip=(0.0, 0.656, 0.44),
    # foreleg: shoulder, elbow, wrist (the "knee"), hoof
    shoulder=(0.145, -0.11, 0.50), elbow=(0.14, -0.09, 0.26), wrist=(0.13, -0.126, 0.10),
    fhoof=(0.13, -0.155, 0.0),
    # hind leg: hip, stifle, hock, hoof
    hip=(0.13, 0.38, 0.54), stifle=(0.135, 0.33, 0.31), hock=(0.122, 0.448, 0.148),
    hhoof=(0.122, 0.41, 0.0),
)

# ---------------------------------------------------------------------------- design tables
# Half rings, nose to rump: y, then six (x, z): spine/top seam, back edge, widest flank,
# lower flank, belly side, keel/bottom seam.
RINGS = [
    ('H0', -0.720, [(0, 0.494), (0.058, 0.490), (0.074, 0.458), (0.074, 0.398), (0.056, 0.368), (0, 0.362)]),  # disc
    ('H1', -0.690, [(0, 0.484), (0.052, 0.481), (0.066, 0.452), (0.068, 0.402), (0.050, 0.374), (0, 0.368)]),  # behind disc
    ('H2', -0.600, [(0, 0.545), (0.064, 0.540), (0.082, 0.500), (0.084, 0.420), (0.064, 0.376), (0, 0.362)]),  # snout
    ('H3', -0.500, [(0, 0.625), (0.078, 0.618), (0.112, 0.560), (0.120, 0.435), (0.084, 0.362), (0, 0.346)]),  # muzzle base
    ('H4', -0.420, [(0, 0.698), (0.090, 0.688), (0.136, 0.600), (0.148, 0.455), (0.100, 0.350), (0, 0.332)]),  # eye / cheek
    ('H5', -0.340, [(0, 0.748), (0.112, 0.724), (0.156, 0.640), (0.162, 0.455), (0.104, 0.342), (0, 0.322)]),  # skull, jowl
    ('H6', -0.260, [(0, 0.790), (0.118, 0.760), (0.166, 0.645), (0.168, 0.470), (0.104, 0.352), (0, 0.325)]),  # nape
    ('B0', -0.180, [(0, 0.835), (0.114, 0.800), (0.196, 0.610), (0.176, 0.450), (0.094, 0.352), (0, 0.322)]),  # chest front
    ('B1', -0.040, [(0, 0.902), (0.130, 0.862), (0.222, 0.630), (0.188, 0.440), (0.094, 0.320), (0, 0.290)]),  # hump
    ('B2', 0.120, [(0, 0.832), (0.124, 0.806), (0.206, 0.600), (0.184, 0.440), (0.100, 0.338), (0, 0.312)]),   # barrel
    ('B3', 0.280, [(0, 0.728), (0.108, 0.708), (0.168, 0.574), (0.158, 0.462), (0.080, 0.398), (0, 0.378)]),   # loin, tuck
    ('B4', 0.460, [(0, 0.660), (0.094, 0.642), (0.150, 0.546), (0.142, 0.462), (0.068, 0.432), (0, 0.424)]),   # hip
    ('B5', 0.560, [(0, 0.600), (0.064, 0.590), (0.100, 0.528), (0.092, 0.468), (0.046, 0.444), (0, 0.436)]),   # rump back
]

# Tail rings: centre, the direction the ring's "top" points (it rotates from +Z to +Y as the
# tail droops), radius.
TAIL = [((0.0, 0.590, 0.572), (0, 0.0, 1.0), 0.026),
        ((0.0, 0.630, 0.552), (0, 0.6, 0.8), 0.019),
        ((0.0, 0.656, 0.490), (0, 1.0, 0.25), 0.013)]

# Leg levels below the root: (cx, cy, z, half-width x, half-depth y).
FORE = [(0.152, -0.112, 0.440, 0.070, 0.086, 0.310),   # shoulder: the muscle bulges past the flank
        (0.142, -0.092, 0.262, 0.066, 0.090),          # elbow, tucked back
        (0.136, -0.114, 0.176, 0.056, 0.070),          # forearm, tapering
        (0.130, -0.126, 0.106, 0.038, 0.044),          # wrist (the "knee"): the narrow point
        (0.130, -0.142, 0.060, 0.037, 0.042),          # pastern, slanting forward
        (0.130, -0.150, 0.040, 0.046, 0.054)]          # coronet (hoof top)
HIND = [(0.140, 0.365, 0.450, 0.066, 0.105, 0.360),    # ham: the thigh bulges past the flank
        (0.136, 0.328, 0.312, 0.070, 0.098),           # stifle, knee forward
        (0.130, 0.388, 0.216, 0.056, 0.074),           # gaskin
        (0.122, 0.448, 0.148, 0.038, 0.052),           # hock, set back: the narrow point
        (0.122, 0.422, 0.060, 0.035, 0.042),           # pastern
        (0.122, 0.412, 0.040, 0.046, 0.054)]           # coronet


def hexpts(cx, cy, z, hw, hd, zin=None, f=0.72):
    """Leg section in loop order FO, FC, FI, BI, BC, BO: flat outer and inner sides,
    a front and a back ridge (deeper than wide). zin tilts the section (outer at z, inner at zin)."""
    zi = z if zin is None else zin
    zm = (z + zi) / 2
    return [(cx + hw, cy - hd * f, z), (cx, cy - hd, zm), (cx - hw, cy - hd * f, zi),
            (cx - hw, cy + hd * f, zi), (cx, cy + hd, zm), (cx + hw, cy + hd * f, z)]


def tail_ring(bm, c, up, r):
    c, u, X = Vector(c), Vector(up).normalized(), Vector((1, 0, 0))
    prof = [(0, 1.0), (0.62, 0.78), (1.0, 0.1), (0.9, -0.45), (0.5, -0.88), (0, -1.0)]
    return ring(bm, [c + X * (r * a) + u * (r * b) for a, b in prof])


def face_of(vs):
    s = set(vs[0].link_faces)
    for v in vs[1:]:
        s &= set(v.link_faces)
    assert len(s) == 1, 'face_of: %d faces' % len(s)
    return s.pop()


def match(newv, pts):
    """New (coincident) verts ordered like the old positions pts."""
    return [min(newv, key=lambda v: (v.co - Vector(p)).length) for p in pts]


def extrude_loop(bm, faces, loop, targets):
    """Extrude the face region whose boundary is `loop` (ordered verts) and place the
    new boundary at targets. Returns (new faces, new ordered loop)."""
    old = [v.co.copy() for v in loop]
    inner = {e for f in faces for e in f.edges}
    r = extrude(bm, faces)
    loose = [e for e in inner if e.is_valid and not e.link_faces]   # the region's interior edge
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='EDGES')
    nl = match(r['verts'], old)
    place(nl, targets)
    return r['faces'], nl


def leg(bm, ra, rb, levels, gap=0.011):
    loop = [ra[2], ra[3], ra[4], rb[4], rb[3], rb[2]]
    faces = [face_of([ra[2], ra[3], rb[3], rb[2]]), face_of([ra[3], ra[4], rb[4], rb[3]])]
    for lv in levels:
        faces, loop = extrude_loop(bm, faces, loop, hexpts(*lv))
    # cloven hoof: the outer and inner halves of the coronet each extrude to a toe
    cx, cy, z, hw, hd = levels[-1][:5]
    FO, FC, FI, BI, BC, BO = loop
    outer = face_of([FO, FC, BC, BO])
    inner = face_of([FC, FI, BI, BC])
    extrude_loop(bm, [outer], [FO, FC, BC, BO],
                 [(cx + hw * 0.92, cy - hd * 1.02, 0.0), (cx + gap, cy - hd * 1.32, 0.0),
                  (cx + gap, cy + hd * 0.78, 0.0), (cx + hw * 0.92, cy + hd * 0.74, 0.0)])
    extrude_loop(bm, [inner], [FC, FI, BI, BC],
                 [(cx - gap, cy - hd * 1.32, 0.0), (cx - hw * 0.92, cy - hd * 1.02, 0.0),
                  (cx - hw * 0.92, cy + hd * 0.74, 0.0), (cx - gap, cy + hd * 0.78, 0.0)])


def ear(bm, ra, rb):
    """Ear from the upper-side face between two head rings: a leaf, its cup facing forward-out."""
    loop = [ra[1], ra[2], rb[2], rb[1]]          # front-inner, front-outer, back-outer, back-inner
    faces = [face_of(loop)]
    base = Vector((0.150, -0.300, 0.768))
    u = Vector((0.50, -0.08, 0.86)).normalized()   # up the ear, leaning out and a little forward
    t = Vector((-0.42, 0.90, 0.0))                 # thickness: the cup faces forward-out, not straight ahead
    t = (t - u * t.dot(u)).normalized()
    w = t.cross(u).normalized()                    # across the ear
    if w.x < 0:
        w = -w

    def quad(c, hw, ht, lean=0.0):
        return [c - w * hw - t * ht, c + w * hw - t * ht, c + w * hw + t * ht, c - w * hw + t * ht]
    faces, loop = extrude_loop(bm, faces, loop, quad(base, 0.036, 0.022))
    faces, loop = extrude_loop(bm, faces, loop, quad(base + u * 0.085 + Vector((0, -0.02, 0)), 0.042, 0.012))
    extrude_loop(bm, faces, loop, quad(Vector(J['ear_tip']), 0.006, 0.004))


def stage1(k):
    bm = bmesh.new()
    R = {name: ring(bm, [(x, y, z) for x, z in pts]) for name, y, pts in RINGS}
    order = [r[0] for r in RINGS]
    rows = [R[n] for n in order] + [tail_ring(bm, *t) for t in TAIL]
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)
    leg(bm, R['B0'], R['B1'], FORE)
    leg(bm, R['B3'], R['B4'], HIND)
    ear(bm, R['H5'], R['H6'])
    recalc_normals(bm)
    if os.environ.get('BOAR_DEBUG'):
        for e in bm.edges:
            if len(e.link_faces) != 2 and not all(abs(v.co.x) < 1e-6 for v in e.verts):
                say('NONMAN', len(e.link_faces), [tuple(round(c, 3) for c in v.co) for v in e.verts])
        from mathutils.bvhtree import BVHTree
        bm.faces.ensure_lookup_table()
        t = BVHTree.FromBMesh(bm)
        for i, j in t.overlap(t):
            if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
                say('HIT', [tuple(round(c, 3) for c in bm.faces[q].calc_center_median()) for q in (i, j)])
    return object_from_bm('body', bm)


def V_(bm, p):
    """The base vertex at the design point p (stage-1 coordinates)."""
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < 1e-3, ('no vertex at', p, tuple(v.co))
    return v


SADDLE_LINE = []   # the saddle border (y, z) points at B0 and B1, filled by stage 2
MOUTH = []      # the mouth-line (y, z) points, filled by stage 2; stage 3 paints the lower jaw below them


def mouth_z(y):
    pts = MOUTH or [(-0.72, 0.383), (-0.34, 0.41)]
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[-1][1]


def stage2(k, body):
    bm = edit(body)
    # --- the eye: a socket under an overhanging brow -------------------------------------
    eye_face = face_near(bm, (0.124, -0.38, 0.663), n=(1, 0, 0.5))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face (H4-H5, brow edge to cheek)'):
        sock = inset(bm, [eye_face], 0.42, depth=0.0)[0]
    sv = list(sock.verts)
    c = centre(sv)
    n = sock.normal.copy()
    scale(sv, (0.95, 0.80, 0.80), pivot=c)            # an almond, longer than tall
    move(sv, n * -0.012 + Vector((0, -0.006, -0.008)))  # sunk, a little forward and down under the brow
    brow = V_(bm, (0.090, -0.420, 0.688))
    brow.co += Vector((0.030, -0.004, 0.010))           # the brow ridge overhangs the eye (AD note 4: +1 cm)
    V_(bm, (0.112, -0.340, 0.724)).co += Vector((0.006, 0, 0.008))   # (AD r2 note 3: less, it lined up the ear wall)
    # --- the snout: nostrils in the disc, a mouth line along the jaw ----------------------
    disc = face_near(bm, (0.035, -0.720, 0.430), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'nostril: a loop inside the flat disc (half cap = one nostril per side)'):
        nos = inset(bm, [disc], 0.52, depth=0.0)[0]
    nv = list(nos.verts)
    scale(nv, (0.85, 1, 0.70), pivot=centre(nv))      # AD r2 O3: a shorter oval (was 0.75 x 1.0, a slot)
    rotate(nv, (0, 1, 0), 14, pivot=centre(nv))       # tilted 14 deg, the top outward: a pig nostril, not a socket
    move(nv, (-0.006, 0.012, 0.0))                       # sunk into the disc, 8 mm in (off the disc corner's line)
    with k.topo(bm, 'partial_loop', 'mouth line: from the disc rim back to under the eye, fan-terminated '
                                   'in the disc-rim quad and in the cheek quad (skull, nothing bends there)'):
        mouth = partial_loop(bm, edge_near(bm, (0.065, -0.720, 0.383)), edge_near(bm, (0.133, -0.340, 0.3985)), t=0.45)
    for v in mouth:
        v.co.x -= 0.018                                   # the lip line creases in (AD note 4: deeper)
        v.co.z += 0.014 * (v.co.y + 0.72) / 0.30          # and lifts toward the mouth corner
    MOUTH[:] = sorted((v.co.y, v.co.z) for v in mouth)
    # --- planes: a few big deliberate facets instead of a gently curving loft ---------------
    def plane(pts):
        vs = [V_(bm, p) for p in pts]
        seam = [v for v in vs if abs(v.co.x) < 1e-6]
        flatten(vs)
        for v in seam:
            v.co.x = 0.0
    # the forehead-to-disc top plane (one facet per side from the brow to the disc rim)
    plane([(0.058, -0.720, 0.490), (0.052, -0.690, 0.481), (0.064, -0.600, 0.540), (0.078, -0.500, 0.618)])
    # the barrel: one lower-flank plane from behind the shoulder to the loin
    plane([(0.206, 0.120, 0.600), (0.184, 0.120, 0.440), (0.168, 0.280, 0.574), (0.158, 0.280, 0.462)])
    # the snout side: one plane from the disc rim back to the tusk bulge
    plane([(0.074, -0.720, 0.458), (0.066, -0.690, 0.452), (0.082, -0.600, 0.500), (0.112, -0.500, 0.560)])
    # --- the ear cup: the forward-facing leaf is hollowed, not a flat card -------------------
    ef = face_near(bm, (0.171, -0.318, 0.804), n=(0.42, -0.90, 0.0))
    with k.topo(bm, 'inset', 'ear cup: a loop inside the front face of the ear'):
        cup = inset(bm, [ef], 0.30, depth=0.0)[0]
    cv = list(cup.verts)
    move(cv, cup.normal * -0.010)
    # --- the ears (AD note 2): shorter, splayed out, a broader thicker root (vertex moves) -----
    eb = Vector((0.150, -0.300, 0.768))                  # the ear() base in stage 1
    eu = Vector((0.50, -0.08, 0.86)).normalized()
    et = Vector((-0.42, 0.90, 0.0))
    et = (et - eu * et.dot(eu)).normalized()
    near = [v for v in bm.verts if v.co.x > 0.10 and (v.co - eb).length < 0.25]
    root = [v for v in near if abs((v.co - eb).dot(eu)) < 0.004 and (v.co - eb).length < 0.07]
    upper = [v for v in near if (v.co - eb).dot(eu) > 0.010]
    tipv = [v for v in upper if (v.co - eb).dot(eu) > 0.14]
    assert len(root) == 4 and len(tipv) == 4, (len(root), len(tipv))
    scale(root, 1.3, pivot=eb)                            # base 30% wider and thicker
    scale(tipv, 2.0, pivot=centre(tipv))                  # a blunt tip, not a needle
    for v in upper:
        d = v.co - eb
        s_ = 0.49 if v in tipv else 0.40                  # AD r2: the tip segment carries the further 15%
        v.co = eb + d - eu * (d.dot(eu) * s_)
    # AD r2 note 3: splayed out/down 24 deg and tipped forward 22 deg as HINGES on the root's outer and
    # front edges (a turn about the root centre swung the leaning side down into the root: needles);
    # then the tip segment folds forward a further 20 deg on the mid ring's front edge
    po = centre(sorted(root, key=lambda v: -v.co.x)[:2])
    pf = centre(sorted(root, key=lambda v: v.co.y)[:2])
    rotate(upper, et, 24, pivot=po)
    rotate(upper, (1, 0, 0), 22, pivot=pf)
    rotate(upper, (0, 1, 0), 6, pivot=po)
    midv = list({n for t_ in tipv for e in t_.link_edges for n in e.verts if n not in tipv})
    assert len(midv) == 4, len(midv)
    pm = centre(sorted(midv, key=lambda v: v.co.y)[:2])
    rotate(tipv, (1, 0, 0), 20, pivot=pm)
    fi = min(root, key=lambda v: (v.co - Vector((0.12, -0.344, 0.781))).length)
    fi.co.x += 0.015        # the root's front-inner corner out: the ear's front wall was a needle (H5.v1 on its line)
    if os.environ.get('BOAR_DEBUG'):
        for v in sorted(near, key=lambda v: (v.co - eb).dot(eu)):
            if (v.co - eb).dot(eu) > -0.03:
                say('EAR', 'root' if v in root else ('tip' if v in tipv else ('up' if v in upper else '-')),
                    tuple(round(q, 3) for q in v.co), round((v.co - eb).dot(eu), 3))
    # --- bone and muscle landmarks (vertex moves only) ------------------------------------
    V_(bm, (0.120, -0.500, 0.435)).co += Vector((0.012, 0.0, 0.006))    # tusk boss on the upper jaw
    V_(bm, (0.162, -0.340, 0.455)).co += Vector((0.012, 0.0, -0.012))   # heavy jowl under the ear
    V_(bm, (0.168, -0.260, 0.470)).co += Vector((0.006, 0.0, -0.010))
    V_(bm, (0.094, 0.460, 0.642)).co += Vector((0.012, 0.0, 0.010))     # hip bone point on the rump
    V_(bm, (0.130, -0.040, 0.862)).co += Vector((0.008, 0.0, 0.008))    # shoulder-blade top under the hump
    # --- the underline (AD note 7): a deeper brisket keel, a tucked groin; the seam keel only
    # where the foreleg roots on the belly side (moving those would fold the leg's inner wall)
    for p_, dz in [((0, -0.180, 0.322), -0.020), ((0, -0.040, 0.290), -0.026),
                   ((0, 0.120, 0.312), -0.004), ((0.100, 0.120, 0.338), 0.010),
                   ((0, 0.280, 0.378), 0.034), ((0.080, 0.280, 0.398), 0.022),
                   ((0, 0.460, 0.424), 0.020), ((0.068, 0.460, 0.432), 0.012)]:
        V_(bm, p_).co.z += dz
    # --- the foreleg: a heavier elbow/forearm, a pinched pastern (x/y about each level's centre)
    for lv, f_ in [(FORE[1], 1.15), (FORE[2], 1.08), (FORE[4], 0.90)]:
        vs = [V_(bm, q) for q in hexpts(*lv[:5])]
        scale(vs, (f_, f_, 1.0), pivot=centre(vs))
    # --- the saddle border (AD r2 note 2): a partial loop along the upper flank, H6 to B2 (cuts the B0
    # and B1 ring edges between the back-edge and widest-flank loops), slid so its edge runs diagonally
    # from low at the chest front to high behind the hump; stage 3 paints the saddle above it
    e_h6 = edge_near(bm, (0.142, -0.260, 0.7025))
    e_b2 = edge_near(bm, (0.165, 0.120, 0.703))
    with k.topo(bm, 'partial_loop', 'saddle border: a diagonal line across the upper flank from the chest '
                                   'front (low) to behind the hump (high), fan-terminated in the nape quad '
                                   'and the barrel quad (mid-back, nothing bends there)'):
        sm = partial_loop(bm, e_h6, e_b2, t=0.5)
    for m in sm:
        a_, b_ = sorted([v for e in m.link_edges for v in e.verts if v is not m
                         and abs(v.co.y - m.co.y) < 1e-4], key=lambda v: -v.co.z)[:2]
        s_ = 0.80 if m.co.y < -0.10 else 0.30           # B0: near the widest-flank loop; B1: near the back edge
        m.co = a_.co.lerp(b_.co, s_)
    SADDLE_LINE[:] = sorted((m.co.y, m.co.z) for m in sm)
    commit(body, bm)


# AD r2 O6: the leg stockings a step lighter than the saddle; hooves share the bristle near-black (8 colours max)
PAL = {'hide': '#7d614d', 'dark': '#4f3d33', 'stocking': '#5d493c', 'snout': '#6a5a5d', 'eye': '#1a1a1a',
       'bristle': '#2e2622', 'tusk': '#e8dfc8', 'glint': '#f0c060'}


def pal(*keys):
    return {k_: PAL[k_] for k_ in keys}


def sweep(bm, pts, radii, sides=3, up=(0, 0, 1), roll=0.0):
    """A tapering tube along pts (radius 0 at the end = a point). Returns the verts."""
    P = [Vector(p) for p in pts]
    rows = []
    for i, (p, r) in enumerate(zip(P, radii)):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        a = Vector(up) - t * Vector(up).dot(t)
        a.normalize()
        b = t.cross(a)
        if r <= 0:
            rows.append([bm.verts.new(p)])
            continue
        rows.append([bm.verts.new(p + (a * math.cos(q) + b * math.sin(q)) * r)
                     for q in [roll + 2 * math.pi * j / sides for j in range(sides)]])
    for ra, rb in zip(rows, rows[1:]):
        if len(rb) == 1:
            for j in range(len(ra)):
                bm.faces.new([ra[j], ra[(j + 1) % len(ra)], rb[0]])
        else:
            bridge(bm, ra, rb, closed=True)
    if len(rows[0]) > 2:
        bm.faces.new(list(reversed(rows[0])))
    return [v for r in rows for v in r]


def spike(bm, base, fwd, back, half_w, tip, lean_x=0.0):
    """A bristle blade: a diamond base on the ridge (front, side, back, side) and one tip."""
    b = Vector(base)
    F = bm.verts.new(b + Vector((0, -fwd, 0.004)))
    B = bm.verts.new(b + Vector((0, back, -0.004)))
    L = bm.verts.new(b + Vector((half_w, 0.0, -0.012)))
    R = bm.verts.new(b + Vector((-half_w, 0.0, -0.012)))
    T = bm.verts.new(Vector(tip) + Vector((lean_x, 0, 0)))
    for f in ([F, L, T], [L, B, T], [B, R, T], [R, F, T], [F, R, B, L]):
        bm.faces.new(f)


def ridge_z(y):
    """The spine ridge height at y (the stage-1 top seam, linearly between rings)."""
    tops = [(yy, pts[0][1]) for _, yy, pts in RINGS]
    for (y0, z0), (y1, z1) in zip(tops, tops[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return tops[-1][1]


# the tusk sweep (stage-3 piece): centre line and radii, root inside the lower jaw at y ~ -0.50
# AD r2 note 4: longer, out and forward past the lip, then up and hooking back, so the tip clears the
# snout's top line by ~3 cm in profile
TUSK = [(0.064, -0.498, 0.384), (0.102, -0.510, 0.394), (0.138, -0.530, 0.408),
        (0.165, -0.558, 0.448), (0.180, -0.582, 0.505), (0.183, -0.588, 0.560), (0.177, -0.568, 0.602)]
TUSK_R = [0.019, 0.018, 0.016, 0.014, 0.011, 0.007, 0.0]


# crest clumps: (base y, height); irregular heights, the tallest over the hump (AD r2: lowered 15%),
# each leaning back
CREST = [(-0.300, 0.046), (-0.222, 0.080), (-0.128, 0.090), (-0.030, 0.066), (0.072, 0.074),
         (0.158, 0.036)]


def crest_columns():
    """Columns along the crest strip: (y, top z, shoulder z, shoulder x, shoulder y, base z, base x,
    top half-width, roll deg, ridge z, side offset). Each clump ends in a blunt flat (a front and a
    back tip column, 2 cm flat top), rolls +-16 deg about the spine and shifts +-1 cm sideways
    alternately so the ridge fans out from the front, and stays wide to half its height."""
    lean = 1.0                              # tips 45 deg behind their base
    peaks = []
    for i, (yb, h) in enumerate(CREST):
        yt = yb + lean * h
        s = 1 if i % 2 else -1
        xb = 0.036 if h > 0.05 else 0.030
        peaks.append([(yt - 0.008, h, xb, 0.011, 16.0 * s, 0.010 * s),
                      (yt + 0.012, h - 0.012, xb, 0.010, 16.0 * s, 0.010 * s)])
    cols = []
    y0 = peaks[0][0][0] - 0.050
    cols.append((y0, 0.008, None, 0.024, 0.008, 0.0, 0.0))
    for i, pk in enumerate(peaks):
        yf = pk[0][0]
        yprev = cols[-1][0]
        for y, h, xb, tw, roll, off in pk:
            cols.append((y, h, min(0.30 * h, max(yf - yprev - 0.016, 0.0)), xb, tw, roll, off))
        if i + 1 < len(peaks):
            yv = (pk[1][0] + peaks[i + 1][0][0]) / 2     # the valley, midway to the next clump
            cols.append((yv, 0.55 * min(CREST[i][1], CREST[i + 1][1]), None, 0.034, 0.013, 0.0, 0.0))
    cols.append((cols[-1][0] + 0.045, 0.006, None, 0.022, 0.008, 0.0, 0.0))
    out = []
    for y, ht, fwd, xb, tw, roll, off in cols:
        zr = ridge_z(y)
        zt = zr + ht
        zb = zr - 0.026
        zm = zr + 0.50 * ht
        ym = y - (fwd or 0.0)
        xm = xb * (0.78 if fwd is not None else 0.82)
        out.append((y, zt, zm, xm, ym, zb, xb, tw, roll, zr, off))
    return out


def SADDLE(c, n):
    """The dark mane saddle (AD r2 note 2): a staircase V on existing loops, no straight border.
    Nape/neck side dark down to the lower-flank loop, the hump down to the widest-flank loop, then
    the front walls of the leg root and the front of the upper arm carry it down to the elbow;
    behind the hump only the back strip stays dark (the back-strip rule)."""
    x = abs(c.x)
    if x < 0.02:
        return False
    if -0.26 < c.y < -0.18 and c.z > 0.44 and n.z > -0.3:
        return True                                     # neck side, H6-B0, down to the lower-flank loop
    (y0, z0), (y1, z1) = SADDLE_LINE or [(-0.18, 0.648), (-0.04, 0.80)]
    if -0.18 < c.y < 0.12 and c.z > (z0 + z1) / 2 + (c.y - (y0 + y1) / 2) * 0.45:
        return True                                     # above the diagonal border loop, B0 to B2
    if -0.22 < c.y < -0.06 and 0.26 < c.z < 0.62 and n.y < -0.35 and x > 0.07:
        return True                                     # front of the leg root and upper arm, to the elbow
    return False


def stage3(k, body):
    # read (never write) the base to find the socket, the nostrils and the lip line
    bm = edit(body)
    sock = face_near(bm, (0.124, -0.386, 0.655), n=(1, 0, 0.5))
    s_c, s_n = sock.calc_center_median(), sock.normal.copy()
    nostril = face_near(bm, (0.036, -0.708, 0.430), n=(0, -1, 0)).index
    socket_i = sock.index
    bm.free()

    def body_rule(c, n, i):
        if i == nostril:
            return 'eye'                                    # near-black nostrils
        if i == socket_i:
            return 'eye'
        if c.z < 0.041:
            return 'bristle'                                # the toe blocks (hooves): the bristle near-black
        if c.y < -0.695:
            return 'snout'
        if c.y < -0.36 and c.z < mouth_z(c.y) and c.x > 0.02:
            return 'dark'                                   # the lower jaw: its border is the mouth line                                  # disc + its rim, bordered by the H1 ring
        if abs(c.x) > 0.05 and c.z < 0.262 and c.y > -0.25:
            return 'stocking'                               # legs below the elbow / stifle-gaskin loop
        if c.y > 0.585:
            return 'dark'                                   # tail
        if abs(c.x) > 0.125 and c.z > 0.74 and -0.37 < c.y < -0.24:
            return 'dark'                                   # ears
        if n.z > 0.80 and c.y > -0.30:
            return 'dark'                                   # the back strip, bordered by the back-edge loop
        if SADDLE(c, n):
            return 'dark'
        return 'hide'
    paint(body, pal('hide', 'dark', 'stocking', 'snout', 'bristle', 'eye'), body_rule)

    pieces = []
    # eyes: a small dark bipyramid seated in the socket, a warm glint on the upper-front facet
    bm = bmesh.new()
    up = Vector((0, 0, 1))
    a = (up - s_n * up.dot(s_n)).normalized()
    b = s_n.cross(a).normalized()
    c = s_c + s_n * 0.002
    rim = [bm.verts.new(c + a * (0.013 * math.cos(q)) + b * (0.018 * math.sin(q)))   # 1.2x (AD note 4)
           for q in [2 * math.pi * j / 6 for j in range(6)]]
    fr = bm.verts.new(c + s_n * 0.009)
    bk = bm.verts.new(c - s_n * 0.008)
    for j in range(6):
        bm.faces.new([rim[j], rim[(j + 1) % 6], fr])
        bm.faces.new([rim[(j + 1) % 6], rim[j], bk])
    eye = object_from_bm('eye', bm, mirror=True)
    glint_c = c + a * 0.008 + s_n * 0.006
    paint(eye, pal('eye', 'glint'),
          lambda cc, n, i: 'glint' if (cc - glint_c).length < 0.0062 and n.z > 0.2 else 'eye')
    pieces.append(eye)

    # tusks: rooted INSIDE the lower jaw under the lip crease, out past the upper-lip overhang,
    # then up and a little back, clear of the muzzle (AD note 1)
    bm = bmesh.new()
    path = [Vector(p_) for p_ in TUSK]
    sweep(bm, path, TUSK_R, sides=3, up=(0, 1, 0), roll=0.5)
    tusk = object_from_bm('tusk', bm, mirror=True)
    paint(tusk, pal('tusk'), lambda cc, n, i: 'tusk')
    pieces.append(tusk)
    if os.environ.get('BOAR_DEBUG'):
        from mathutils.bvhtree import BVHTree
        bb = edit(body)
        tree = BVHTree.FromBMesh(bb)
        for q, r in zip(path, TUSK_R):
            loc, nrm, _, d = tree.find_nearest(q)
            say('TUSK', tuple(round(x, 3) for x in q), 'r', r, 'surf', round(d, 4),
                'out' if (q - loc).dot(nrm) > 0 else 'IN', 'clear', round(d - r, 4))
        bb.free()

    # the bristle crest (AD note 3): ONE ridge strip of overlapping swept-back clumps, fused at the base
    # and sunk 2 cm into the spine; a tent section (top line, a shoulder row, a base row each side)
    bm = bmesh.new()
    rows = []
    for y, zt, zm, xm, ym, zb, xb, tw, roll, zr, off in crest_columns():
        pts = [(off - tw, y, zt), (off - xm, ym, zm), (-xb, y, zb), (xb, y, zb), (off + xm, ym, zm), (off + tw, y, zt)]
        vs = [bm.verts.new(p_) for p_ in pts]      # TR', MR', BR', BL, ML, TL: a hexagon section
        if roll:
            rotate(vs, (0, 1, 0), roll, pivot=(0.0, y, zr))
        rows.append(vs)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(6):
            bm.faces.new([r0[j], r0[(j + 1) % 6], r1[(j + 1) % 6], r1[j]])
    bm.faces.new(list(rows[0]))
    bm.faces.new(list(reversed(rows[-1])))
    recalc_normals(bm)
    mane = object_from_bm('crest', bm, mirror=False)
    paint(mane, pal('bristle'), lambda cc, n, i: 'bristle')
    pieces.append(mane)

    # the tail tuft: a flared brush at the tail tip
    bm = bmesh.new()
    tip = Vector(TAIL[-1][0])
    sweep(bm, [tip + Vector((0, -0.004, 0.012)), tip + Vector((0, 0.004, -0.02)),
               tip + Vector((0, 0.010, -0.050)), tip + Vector((0, 0.012, -0.075))],
          [0.012, 0.024, 0.020, 0.0], sides=5, up=(0, 1, 0))
    tuft = object_from_bm('tuft', bm, mirror=False)
    paint(tuft, pal('bristle'), lambda cc, n, i: 'bristle')
    pieces.append(tuft)
    return pieces


BONES = [
    ('hips', J['pelvis'], J['spine'], None),
    ('chest', J['spine'], J['chest'], 'hips', True),
    ('neck', J['chest'], J['head'], 'chest', True),
    ('head', J['head'], J['snout'], 'neck', True),
    ('ear.L', J['ear'], J['ear_tip'], 'head'),
    ('tail', J['tail'], TAIL[1][0], 'hips'),
    ('tail2', TAIL[1][0], J['tail_tip'], 'tail', True),
    ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
    ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
    ('forefoot.L', J['wrist'], J['fhoof'], 'forearm.L', True),
    ('thigh.L', J['hip'], J['stifle'], 'hips'),
    ('shin.L', J['stifle'], J['hock'], 'thigh.L', True),
    ('hindfoot.L', J['hock'], J['hhoof'], 'shin.L', True),
]
SWING = 1.0     # checked on the r01 posed renders: a positive bone-X rotation swings a leg BACK (and the head DOWN)


def debug_slivers(obs, L=1.4):
    """BOAR_DEBUG: print needle triangles (min angle < 6 deg, longest edge >= 1% of L) per object."""
    import techqa as Q
    for ob in obs:
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        tmp = bpy.data.objects.new('dbg_tmp', me)
        tmp.matrix_world = ob.matrix_world.copy()
        bpy.context.scene.collection.objects.link(tmp)
        Q.triangulate_convex(tmp, keep=META.get('keep_valleys'))
        bm = bmesh.new()
        bm.from_mesh(tmp.data)
        bpy.data.objects.remove(tmp)
        for f in bm.faces:
            a, b, c = (ob.matrix_world @ v.co for v in f.verts)
            if max((a - b).length, (b - c).length, (c - a).length) < 0.01 * L:
                continue
            angs = [math.degrees((y - x).angle(z - x, 0)) for x, y, z in ((a, b, c), (b, c, a), (c, a, b))]
            if min(angs) < 6.0:
                cc = (a + b + c) / 3
                say('SLIVER', ob.name, tuple(round(q, 3) for q in cc), round(min(angs), 1),
                    [tuple(round(q, 3) for q in p) for p in (a, b, c)])
        bm.free()


def stage4(k, body, pieces):
    if os.environ.get('BOAR_DEBUG'):
        debug_slivers([body] + list(pieces))
    rig = armature(BONES)
    skin(body, rig)
    for p in pieces:
        nm = p.name.replace('piece_', '')
        if nm == 'crest':
            bind(p, rig, body=body)
        elif nm == 'tuft':
            bind(p, rig, bone='tail2')
        else:
            bind(p, rig, bone='head')
    S = SWING
    # idle: snuffling head bob, an ear flick, a tail twitch, breathing
    clip(rig, 'idle', {
        1: {},
        8: {'head': (-5, 0, 0), 'neck': (2, 0, 0), 'chest': (1, 0, 0)},
        14: {'head': (3, 0, 1), 'neck': (1, 0, 0), 'chest': (0, 0, 0)},
        20: {'head': (-6, 0, -2), 'neck': (2, 0, 0), 'ear.L': (0, 0, 0), 'ear.R': (0, 0, 0)},
        23: {'head': (-5, 0, -2), 'neck': (2, 0, 0), 'ear.L': (-25, 0, 0), 'ear.R': (0, 0, 0)},
        26: {'head': (-3, 0, -1), 'neck': (1, 0, 0), 'ear.L': (0, 0, 0), 'ear.R': (0, 0, 0), 'chest': (1, 0, 0)},
        34: {'head': (2, 0, 0), 'tail': (0, 0, 20), 'tail2': (0, 0, 15)},
        38: {'head': (1, 0, 0), 'tail': (0, 0, -15), 'tail2': (0, 0, -10)},
        42: {'head': (0, 0, 0), 'tail': (0, 0, 8), 'tail2': (0, 0, 0)},
        48: {},
    })
    # move: a trot � diagonal pairs (fore L + hind R, fore R + hind L), the recovering legs fold
    a, f = 24 * S, 38

    def trot(sg, fold_fore, fold_hind):
        """sg: +1 fore L / hind R reach back ... ; fold_*: which side (L/R) is the recovering leg (1 = folded)."""
        k_ = {'upperarm.L': (sg * a, 0, 0), 'upperarm.R': (-sg * a, 0, 0),
              'thigh.R': (sg * a * 0.8, 0, 0), 'thigh.L': (-sg * a * 0.8, 0, 0),
              'head': (-3 * sg, 0, 0), 'chest': (0, 0, 2 * sg), 'tail': (8, 0, 0)}
        for side, on in zip('LR', fold_fore):      # carpus flexes: the hoof tucks back and up
            k_['forearm.' + side] = (-12 * on, 0, 0)
            k_['forefoot.' + side] = (f * 1.5 * on, 0, 0)
        for side, on in zip('LR', fold_hind):      # stifle and hock flex: the hind hoof lifts under
            k_['shin.' + side] = (18 * on, 0, 0)
            k_['hindfoot.' + side] = (f * on, 0, 0)
        return k_
    clip(rig, 'move', {
        1: trot(1, (0, 0), (0, 0)),
        7: trot(0, (0, 1), (1, 0)),
        13: trot(-1, (0, 0), (0, 0)),
        19: trot(0, (1, 0), (0, 1)),
        25: trot(1, (0, 0), (0, 0)),
    })
    # attack: lower the head and brace, charge, then a hard upward toss of the tusks
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (14, 0, 0), 'head': (16, 0, 0), 'chest': (4, 0, 0),
            'upperarm.L': (-14 * S, 0, 0), 'upperarm.R': (-14 * S, 0, 0), 'thigh.L': (12 * S, 0, 0), 'thigh.R': (12 * S, 0, 0),
            'ear.L': (-20, 0, 0), 'ear.R': (-20, 0, 0), 'tail': (-25, 0, 0)},
        14: {'neck': (16, 0, 0), 'head': (20, 0, 0), 'chest': (2, 0, 0),
             'upperarm.L': (18 * S, 0, 0), 'upperarm.R': (6 * S, 0, 0), 'thigh.L': (-18 * S, 0, 0), 'thigh.R': (-10 * S, 0, 0),
             'ear.L': (-25, 0, 0), 'ear.R': (-25, 0, 0), 'tail': (-25, 0, 0)},
        18: {'neck': (-18, 0, 0), 'head': (-30, 0, 6), 'chest': (-6, 0, 0),
             'upperarm.L': (10 * S, 0, 0), 'upperarm.R': (10 * S, 0, 0), 'thigh.L': (-8 * S, 0, 0), 'thigh.R': (-8 * S, 0, 0),
             'ear.L': (10, 0, 0), 'ear.R': (10, 0, 0), 'tail': (-10, 0, 0)},
        24: {'neck': (-6, 0, 0), 'head': (-10, 0, 2), 'chest': (-2, 0, 0)},
        32: {},
    })
    return rig


run(META, stage1, stage2, stage3, stage4)
