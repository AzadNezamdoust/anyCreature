"""Brown bear: a staged box model (stage 1 blockout -> 4 rig and clips).

Facing -Y, left flank +X, feet on z = 0. The left half is modelled; the kit mirrors it.
The body is one loft of 6-vertex half rings (a 10-sided section: spine seam, back edge,
widest flank, lower flank, belly side, keel) from the nose disc to the stub tail. The
shoulder HUMP is the tallest ring, the head hangs below it. Legs are extruded from two
stacked lower-flank faces as hexagons (flat outer/inner sides, a front and a back ridge),
and end in plantigrade paws: a sloping paw-top level and a flat sole.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='bear', model='opus', engine_glb='')

# The skeleton the model is built on (stage 1 places the leg levels on it; stage 4 rigs it).
J = dict(
    pelvis=(0.0, 0.494, 0.78), spine=(0.0, 0.116, 0.80), chest=(0.0, -0.16, 0.80),
    neck=(0.0, -0.40, 0.72), head=(0.0, -0.46, 0.70), snout=(0.0, -0.91, 0.62),
    ear=(0.175, -0.499, 0.823), ear_tip=(0.225, -0.505, 0.988),
    tail=(0.0, 0.750, 0.700), tail_tip=(0.0, 0.805, 0.690),
    # foreleg: shoulder, elbow, wrist, paw (toes)
    shoulder=(0.245, -0.200, 0.640), elbow=(0.262, -0.165, 0.340), wrist=(0.220, -0.232, 0.120),
    fpaw=(0.192, -0.395, 0.035),
    # hind leg: hip, knee (stifle), ankle (heel), paw (toes)
    hip=(0.245, 0.534, 0.660), knee=(0.245, 0.467, 0.380), ankle=(0.230, 0.575, 0.130),
    hpaw=(0.230, 0.382, 0.035),
)

# ---------------------------------------------------------------------------- design tables
# Half rings, nose to rump: y, then six (x, z): spine/top seam, back edge, widest flank,
# lower flank, belly side, keel/bottom seam. An optional third number is a y offset for that vertex.
RINGS = [
    ('N0', -0.907, [(0, 0.662), (0.057, 0.658), (0.076, 0.620, 0.006), (0.076, 0.551, 0.022), (0.057, 0.516, 0.036), (0, 0.511, 0.040)]),  # nose disc, tilted: the chin recedes
    ('N1', -0.873, [(0, 0.674), (0.069, 0.669), (0.092, 0.625), (0.092, 0.531, 0.010), (0.069, 0.485, 0.018), (0, 0.478, 0.020)]),  # behind the nose
    ('N2', -0.796, [(0, 0.688), (0.083, 0.683), (0.113, 0.637), (0.115, 0.528), (0.085, 0.474), (0, 0.465)]),  # muzzle: a flat-topped box
    ('N3', -0.730, [(0, 0.706), (0.097, 0.701), (0.133, 0.654), (0.143, 0.536), (0.103, 0.470), (0, 0.460)]),  # muzzle root, foot of the stop
    ('H1', -0.665, [(0, 0.821), (0.121, 0.809), (0.190, 0.735), (0.201, 0.568), (0.140, 0.476), (0, 0.460)]),  # brow: the forehead rises steeply
    ('H2', -0.554, [(0, 0.884), (0.132, 0.869), (0.224, 0.769), (0.236, 0.579), (0.163, 0.476), (0, 0.460)]),  # domed skull, broad cheeks
    ('H3', -0.450, [(0, 0.884), (0.136, 0.873), (0.218, 0.781), (0.224, 0.579), (0.161, 0.482), (0, 0.470)]),  # back of skull
    ('NK', -0.370, [(0, 0.860), (0.140, 0.850), (0.232, 0.770), (0.232, 0.600), (0.162, 0.510), (0, 0.495)]),  # thick neck
    ('B0', -0.300, [(0, 0.975), (0.167, 0.955), (0.282, 0.780), (0.262, 0.570), (0.158, 0.435), (0, 0.415)]),  # chest front
    ('B1', -0.100, [(0, 1.020), (0.189, 0.995), (0.313, 0.800), (0.280, 0.560), (0.170, 0.405), (0, 0.380)]),  # the HUMP
    ('B2', 0.098, [(0, 0.915), (0.192, 0.895), (0.336, 0.765), (0.298, 0.560), (0.180, 0.400), (0, 0.380)]),   # barrel
    ('B3', 0.296, [(0, 0.895), (0.183, 0.878), (0.313, 0.760), (0.280, 0.570), (0.170, 0.440), (0, 0.425)]),   # loin
    ('B4', 0.440, [(0, 0.915), (0.177, 0.897), (0.295, 0.780), (0.277, 0.580), (0.166, 0.470), (0, 0.455)]),   # hip
    ('B5', 0.620, [(0, 0.870), (0.144, 0.852), (0.236, 0.745), (0.236, 0.585), (0.144, 0.495), (0, 0.480)]),   # rump
    ('B6', 0.701, [(0, 0.835), (0.105, 0.820), (0.176, 0.725), (0.176, 0.600), (0.105, 0.530), (0, 0.515)]),   # rump back
    ('B7', 0.750, [(0, 0.780), (0.050, 0.770), (0.085, 0.710), (0.085, 0.630), (0.050, 0.585), (0, 0.575)]),   # tail root
]

# Stub tail rings: centre, the ring's "up" direction, radius.
TAIL = [((0.0, 0.780, 0.728), (0, 0.3, 1.0), 0.040),
        ((0.0, 0.805, 0.700), (0, 0.8, 0.6), 0.020)]

# Leg levels below the root: (cx, cy, z, half-width x, half-depth y[, z of the inner side]).
FORE = [(0.245, -0.200, 0.560, 0.088, 0.100, 0.360),   # shoulder: the muscle bulges past the flank
        (0.262, -0.165, 0.340, 0.096, 0.122),          # elbow: out and back (the bow)
        (0.245, -0.200, 0.220, 0.088, 0.110),          # forearm, angling in
        (0.220, -0.232, 0.120, 0.080, 0.094)]          # wrist: in and forward
HIND = [(0.245, 0.534, 0.600, 0.090, 0.095, 0.400),    # ham
        (0.245, 0.467, 0.380, 0.094, 0.124),           # knee forward
        (0.236, 0.530, 0.240, 0.084, 0.100),           # shin
        (0.230, 0.575, 0.130, 0.076, 0.086)]           # ankle, above the heel
# Paws: (cx, hw, y front, y back, z front, z back, toe-in) for the paw top; the sole is the same plan at z = 0.
FPAW = (0.214, 0.092, -0.395, -0.140, 0.070, 0.062, 0.022)
# AD r2 O4 (stage 2): the forearm stands near vertical -- the wrist and forepaw loops slide back under the hump
FORE_BACK = dict(forearm=0.040, wrist=0.060, paw=0.060)
FPAW2 = FPAW[:2] + (FPAW[2] + FORE_BACK['paw'], FPAW[3] + FORE_BACK['paw']) + FPAW[4:]   # where the paw ends up


def fore_back(p, key='paw'):
    return (p[0], p[1] + FORE_BACK[key], p[2])
HPAW = (0.230, 0.090, 0.382, 0.660, 0.072, 0.064, 0.0)


def hexpts(cx, cy, z, hw, hd, zin=None, f=0.72):
    """Leg section in loop order FO, FC, FI, BI, BC, BO: flat outer and inner sides,
    a front and a back ridge (deeper than wide). zin tilts the section (outer at z, inner at zin)."""
    zi = z if zin is None else zin
    zm = (z + zi) / 2
    return [(cx + hw, cy - hd * f, z), (cx, cy - hd, zm), (cx - hw, cy - hd * f, zi),
            (cx - hw, cy + hd * f, zi), (cx, cy + hd, zm), (cx + hw, cy + hd * f, z)]


def pawpts(cx, hw, yf, yb, zf, zb, ti=0.0, z=None):
    """Paw plan in loop order FO, FC, FI, BI, BC, BO: a rounded toe front, a square heel.
    ti: toe-in, the front edge shifted toward the midline (pigeon-toed forepaws)."""
    zf_, zb_ = (zf, zb) if z is None else (z, z)
    return [(cx + hw - ti, yf + 0.035, zf_), (cx - ti, yf, zf_), (cx - hw * 0.95 - ti, yf + 0.030, zf_),
            (cx - hw * 0.9, yb, zb_), (cx, yb + 0.010, zb_), (cx + hw * 0.9, yb, zb_)]


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
    r = extrude(bm, faces)
    nl = match([v for v in r['verts'] if any(f in r['faces'] for f in v.link_faces)], old)
    place(nl, targets)
    return r['faces'], nl


def leg(bm, ra, rb, levels, paw):
    loop = [ra[2], ra[3], ra[4], rb[4], rb[3], rb[2]]
    faces = [face_of([ra[2], ra[3], rb[3], rb[2]]), face_of([ra[3], ra[4], rb[4], rb[3]])]
    for lv in levels:
        faces, loop = extrude_loop(bm, faces, loop, hexpts(*lv))
    faces, loop = extrude_loop(bm, faces, loop, pawpts(*paw))       # paw top, sloping to the toes
    extrude_loop(bm, faces, loop, pawpts(*paw, z=0.0))              # the flat sole


def ear(bm, ra, rb):
    """A small round ear from the upper-side skull face between two head rings."""
    loop = [ra[1], ra[2], rb[2], rb[1]]          # front-inner, front-outer, back-outer, back-inner
    faces = [face_of(loop)]
    base = Vector(J['ear'])
    u = Vector((0.42, -0.04, 0.91)).normalized()   # up the ear, leaning out
    t = Vector((0.0, 1.0, 0.0))                    # thickness: the cup faces forward
    t = (t - u * t.dot(u)).normalized()
    w = t.cross(u).normalized()
    if w.x < 0:
        w = -w

    def quad(c, hw, ht):
        return [c - w * hw - t * ht, c + w * hw - t * ht, c + w * hw + t * ht, c - w * hw + t * ht]
    faces, loop = extrude_loop(bm, faces, loop, quad(base, 0.038, 0.028))
    faces, loop = extrude_loop(bm, faces, loop, quad(base + u * 0.075, 0.060, 0.024))
    extrude_loop(bm, faces, loop, quad(Vector(J['ear_tip']), 0.034, 0.016))


def debug_report(bm):
    for e in bm.edges:
        if len(e.link_faces) != 2 and not all(abs(v.co.x) < 1e-6 for v in e.verts):
            say('NONMAN', len(e.link_faces), [tuple(round(c, 3) for c in v.co) for v in e.verts])
    from mathutils.bvhtree import BVHTree
    bm.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(bm)
    for i, j in t.overlap(t):
        if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
            say('HIT', [tuple(round(c, 3) for c in bm.faces[q].calc_center_median()) for q in (i, j)])


def stage1(k):
    bm = bmesh.new()
    R = {name: ring(bm, [(p[0], y + (p[2] if len(p) > 2 else 0.0), p[1]) for p in pts]) for name, y, pts in RINGS}
    rows = [R[r[0]] for r in RINGS] + [tail_ring(bm, *t) for t in TAIL]
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)
    leg(bm, R['B0'], R['B1'], FORE, FPAW)
    leg(bm, R['B4'], R['B5'], HIND, HPAW)
    ear(bm, R['H2'], R['H3'])
    recalc_normals(bm)
    if os.environ.get('BEAR_DEBUG'):
        debug_report(bm)
    return object_from_bm('body', bm)


def V_(bm, p):
    """The base vertex at the design point p (stage-1 coordinates)."""
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < 1e-3, ('no vertex at', p, tuple(v.co))
    return v


def ringv(name, i):
    """Stage-1 position of vertex i of ring `name` (with its y offset)."""
    for nm, y, pts in RINGS:
        if nm == name:
            p = pts[i]
            return (p[0], y + (p[2] if len(p) > 2 else 0.0), p[1])
    raise KeyError(name)


def mid(a, b):
    return tuple((x + y) / 2 for x, y in zip(a, b))


def ear_frame():
    """The ear's axes as ear() builds them: u up the ear, t thickness (forward), w width (outward)."""
    u = Vector((0.42, -0.04, 0.91)).normalized()
    t = Vector((0.0, 1.0, 0.0))
    t = (t - u * t.dot(u)).normalized()
    w = t.cross(u).normalized()
    if w.x < 0:
        w = -w
    return u, t, w


def ear_quads(levels):
    u, t, w = ear_frame()
    out = []
    for c, hw, ht in levels:
        c = Vector(c)
        out.append([tuple(c - w * hw - t * ht), tuple(c + w * hw - t * ht), tuple(c + w * hw + t * ht),
                    tuple(c - w * hw + t * ht)])
    return out


_EU = ear_frame()[0]
EAR_OLD = [(J['ear'], 0.038, 0.028), (Vector(J['ear']) + _EU * 0.075, 0.060, 0.024), (J['ear_tip'], 0.034, 0.016)]
_EB = Vector(J['ear']) + Vector((0.012, 0.0, -0.008))       # the base slid out and down the skull corner
EAR_NEW = [(_EB, 0.042, 0.030), (_EB + _EU * 0.048, 0.062, 0.030), (_EB + _EU * 0.086, 0.050, 0.025)]


EAR_MIDF_DROP = 0.026      # AD r2 O3: the mid quad's front edge slides down the ear, so the cup face is tall


def ear_new_quads():
    """EAR_NEW quads with the stage-2 drop of the mid quad's front edge applied."""
    q = ear_quads(EAR_NEW)
    u = ear_frame()[0]
    q[1][0], q[1][1] = (tuple(Vector(q[1][0]) - u * EAR_MIDF_DROP), tuple(Vector(q[1][1]) - u * EAR_MIDF_DROP))
    return q


def ear_cup_point():
    """Centre of the ear's forward face between the mid and the tip quads (after the stage-2 reshape)."""
    q = ear_new_quads()
    return centre_pts([q[1][0], q[1][1], q[2][0], q[2][1]])


def centre_pts(ps):
    return sum((Vector(p) for p in ps), Vector()) / len(ps)


NOSE = {}          # stage 2 -> stage 3: where the nose pad and the mouth line ended up


def stage2(k, body):
    bm = edit(body)
    # AD repair refs: grab the stage-1 verts now, before any op moves them
    hump = {(n, i): V_(bm, ringv(n, i)) for n in ('NK', 'B0', 'B1', 'B2') for i in (0, 1, 2)}
    fore = [[V_(bm, p) for p in hexpts(*lv)] for lv in FORE]
    fpaw = [V_(bm, p) for p in pawpts(*FPAW)] + [V_(bm, p) for p in pawpts(*FPAW, z=0.0)]
    # --- the eye: a small socket in the side of the stop, under an overhanging brow ------------
    ec = centre([V_(bm, ringv(n, i)) for n in ('N3', 'H1') for i in (1, 2)])
    eye_face = face_near(bm, ec, n=(0.6, -0.5, 0.4))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the stop-side face (N3-H1, back edge to widest)'):
        sock = inset(bm, [eye_face], 0.40, depth=0.0)[0]
    sv = list(sock.verts)
    n = sock.normal.copy()
    scale(sv, (0.95, 0.85, 0.80), pivot=centre(sv))     # a small almond, wider than tall
    move(sv, n * -0.014 + Vector((0, 0.004, -0.006)))    # sunk, a little down under the brow
    V_(bm, ringv('H1', 1)).co += Vector((0.014, -0.022, -0.004))   # the brow ridge overhangs the eye
    V_(bm, ringv('H1', 2)).co += Vector((0.010, -0.010, 0.000))    # the cheekbone below/behind it
    # --- the nose pad and the mouth ----------------------------------------------------------
    disc = face_near(bm, centre([V_(bm, ringv('N0', i)) for i in range(6)]), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'nostril: a loop inside the nose disc (the half cap = one nostril per side)'):
        nos = inset(bm, [disc], 0.50, depth=0.0)[0]
    # AD note 3: the inner ring becomes the nose PAD -- the upper front of the disc, with a straight
    # bottom edge at z .600 (it was a sunk oval whose seam rim painted as a spike down to the chin).
    # The pad stands 8 mm proud of the disc so it reads as a distinct block.
    outer = [V_(bm, ringv('N0', i)) for i in range(6)]
    oc = centre(outer)
    nv = list(nos.verts)
    inner = [min(nv, key=lambda w: (w.co - o.co.lerp(oc, 0.5)).length) for o in outer]
    def disc_y(z):
        return -0.907 + (0.662 - z) * (0.040 / 0.151) - 0.008
    for w, (x, z) in zip(inner, [(0.008, 0.655), (0.052, 0.650), (0.060, 0.619), (0.056, 0.600),
                                 (0.038, 0.598), (0.008, 0.598)]):
        w.co = Vector((x, disc_y(z), z))
    NOSE['pad'] = tuple(centre(inner))
    with k.topo(bm, 'partial_loop', 'mouth line: from the nose-disc rim back to the cheek under the eye, '
                                   'fan-terminated in the disc-rim quad and the cheek quad (skull: nothing bends)'):
        mouth = partial_loop(bm, edge_near(bm, mid(ringv('N0', 3), ringv('N0', 4))),
                             edge_near(bm, mid(ringv('H2', 3), ringv('H2', 4))), t=0.40)
    NOSE['mouth'] = mouth
    for v in mouth:
        v.co.x -= 0.010                                  # the lip line creases in
        v.co.z += 0.008 * max(0.0, (v.co.y + 0.90) / 0.25)   # and lifts a little toward the corner
    NOSE['mouth'] = [tuple(v.co) for v in NOSE['mouth']]
    # --- AD note 4: a low, round, thick bear ear (was a tall canine plank): the three ear quads are
    # re-placed 38% lower, deeper (>= 40% of the width) and slid out/down the skull corner; the tip
    # cap gets an inset whose inner ring is raised into a dome, so the top reads as a half disc
    ev = [[V_(bm, p) for p in q] for q in ear_quads(EAR_OLD)]
    for vs_, q in zip(ev, ear_new_quads()):
        place(vs_, q)
    tipf = face_of(ev[2])
    with k.topo(bm, 'inset', 'ear top: a loop inside the ear tip cap, raised into a dome (round ear top)'):
        dome = inset(bm, [tipf], 0.40, depth=0.0)[0]
    dv = list(dome.verts)
    u_, t_, w_ = ear_frame()
    scale(dv, (0.85, 0.85, 0.85), pivot=centre(dv))
    move(dv, u_ * 0.020)
    # --- the ear cup: the forward face of the round ear is hollowed, not a flat card -------------
    ef = face_near(bm, ear_cup_point(), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'ear cup: a loop inside the forward face of the ear'):
        cup = inset(bm, [ef], 0.30, depth=0.0)[0]
    cv = list(cup.verts)
    cc = centre(cv)
    for v in cv:                                          # a narrower, shorter hollow: wider rim quads, no needles
        d = v.co - cc
        v.co = cc + w_ * (d.dot(w_) * 0.75) + u_ * (d.dot(u_) * 0.80) + t_ * d.dot(t_)
    move(cv, cup.normal * -0.012)
    # --- planes: a few big deliberate facets instead of a gently curving loft -----------------------
    planes = [[V_(bm, ringv(n, i)) for n in names for i in idx] for names, idx in (
        (('N1', 'N2', 'N3'), (0, 1)),          # the flat muzzle bridge
        (('N1', 'N2', 'N3'), (2, 3)),          # the muzzle side, one facet
        (('B0', 'B1'), (1, 2)),                # the shoulder blade under the hump
        (('B1', 'B2', 'B3'), (2, 3)),          # the barrel: one lower-flank plane
        (('B4', 'B5'), (1, 2)))]               # the rump's top-side plane
    for vs in planes:
        seam = [v for v in vs if abs(v.co.x) < 1e-6]
        flatten(vs)
        for v in seam:
            v.co.x = 0.0
    # --- bone, muscle and fur landmarks (vertex moves only) ----------------------------------------
    def lv(level, i):
        return hexpts(*level)[i]
    moves = [
        (ringv('H2', 3), (0.022, 0.0, -0.012)),        # the cheek ruff: broad fur jowls under the ears
        (ringv('H3', 3), (0.016, 0.0, -0.010)),
        (ringv('H2', 2), (0.010, 0.0, 0.000)),
        (ringv('B1', 1), (0.006, 0.0, 0.014)),         # the hump's muscle crest over the shoulder blades
        (ringv('B1', 0), (0.0, 0.0, 0.012)),
        (lv(FORE[1], 4), (0.0, 0.020, 0.0)),           # the elbow point, back
        (lv(HIND[1], 1), (0.0, -0.016, 0.0)),          # the knee, forward
        (lv(HIND[3], 4), (0.0, 0.012, -0.006)),        # the heel above the long hind foot
        (ringv('NK', 4), (0.0, 0.0, 0.0)),              # (AD note 2: the throat-ruff drop folded in the rear-up; removed)
    ]
    vs = [(V_(bm, p), Vector(d)) for p, d in moves]
    for v, d in vs:
        v.co += d
    # --- AD note 1: the hump lives in the base -- the shoulder-top loop rises ~7% of withers height,
    # peaking over the forelegs (between B0 and B1), easing into the neck and the saddle
    for (n, i), dz in {('B0', 0): 0.060, ('B0', 1): 0.055, ('B0', 2): 0.020,
                       ('B1', 0): 0.070, ('B1', 1): 0.065, ('B1', 2): 0.025,
                       ('B2', 0): 0.022, ('B2', 1): 0.020, ('NK', 0): 0.012, ('NK', 1): 0.010}.items():
        hump[(n, i)].co.z += dz
    # --- AD note 6: the forelegs were constant posts -- the wrist narrows 15%, the elbow level moves
    # back 3 cm (the forearm leans forward to the wrist), and the forearm front becomes one flat plane
    wr = fore[3]
    wc = centre(wr)
    scale(wr, (0.85, 0.85, 1.0), pivot=wc)
    # AD r2 F3: the forelegs still read as posts from the front -- the wrist narrows another 15% in x
    # (~.72 of its stage-1 width, ~.66 of the shoulder) and the forearm level 10%, so the leg tapers below the elbow
    scale(wr, (0.85, 1.0, 1.0), pivot=wc)
    scale(fore[2], (0.90, 1.0, 1.0), pivot=centre(fore[2]))
    # AD r2 O4: the forearm raked ~20 deg forward (the paws landed well ahead of the hump); the wrist and
    # both paw loops slide back 8 cm, the forearm level 5 cm, the elbow stays -> the forearm stands near vertical
    move(fore[2], (0.0, FORE_BACK['forearm'], 0.0))
    move(fore[3], (0.0, FORE_BACK['wrist'], 0.0))
    move(fpaw, (0.0, FORE_BACK['paw'], 0.0))
    move(fore[1], (0.0, 0.030, 0.0))
    flatten([v for lvl in fore[1:] for v in lvl[:3]])      # FO, FC, FI of elbow, forearm and wrist
    commit(body, bm)


EYE_R = (0.017, 0.022, 0.009, 0.013, 0.010)   # rim radii (up, side), front ring / apex / back depth

PAL = {'fur': '#6b4a32', 'legs': '#4e3627', 'back': '#5e4230', 'muzzle': '#b08e6c', 'nose': '#221a15',
       'inner_ear': '#8a6a50', 'eye': '#221a15', 'glint': '#f3ead8', 'chest': '#785338'}
# AD note 7: 'eye' shares the nose's near-black (one colour), freeing a slot for a lighter chest/throat


def pal(*keys):
    return {k_: PAL[k_] for k_ in keys}


def sweep(bm, pts, radii, sides=3, up=(0, 0, 1), roll=0.0, squash=1.0):
    """A tapering tube along pts (radius 0 at the end = a point). squash scales the `up` axis."""
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
        rows.append([bm.verts.new(p + (a * (math.cos(q) * squash) + b * math.sin(q)) * r)
                     for q in [roll + 2 * math.pi * j / sides for j in range(sides)]])
    for ra, rb in zip(rows, rows[1:]):
        if len(rb) == 1:
            for j in range(len(ra)):
                bm.faces.new([ra[j], ra[(j + 1) % len(ra)], rb[0]])
        else:
            bridge(bm, ra, rb, closed=True)
    if len(rows[0]) > 2:
        bm.faces.new(list(reversed(rows[0])))
    if len(rows[-1]) > 2:
        bm.faces.new(rows[-1])


def blade(bm, c, nrm, tip, fwd, back, hw, sink=0.012):
    """A fur clump: a diamond base on the surface at c (normal nrm) and one tip."""
    c, nrm, tip = Vector(c), Vector(nrm).normalized(), Vector(tip)
    a = tip - c
    a = (a - nrm * a.dot(nrm)).normalized()
    b = nrm.cross(a).normalized()
    c = c - nrm * sink
    F, L, B, R = (bm.verts.new(c - a * fwd), bm.verts.new(c + b * hw),
                  bm.verts.new(c + a * back), bm.verts.new(c - b * hw))
    T = bm.verts.new(tip)
    for f in ([F, L, T], [L, B, T], [B, R, T], [R, F, T], [F, R, B, L]):
        bm.faces.new(f)


def paw_front(paw, x):
    """(y, z) of the sole's rounded front edge at x (pawpts at z = 0)."""
    cx, hw, yf = paw[0] - paw[6], paw[1], paw[2]
    return yf + 0.033 * min(1.0, abs(x - cx) / hw)


def stage3(k, body):
    # read (never write) the base to find the socket, the nostril and the ear cup
    bm = edit(body)
    sock = face_near(bm, centre([vert_near(bm, ringv(n, i)) for n in ('N3', 'H1') for i in (1, 2)]), n=(0.6, -0.5, 0.4))
    s_c, s_n = sock.calc_center_median(), sock.normal.copy()
    socket_i = sock.index
    nostril_i = face_near(bm, NOSE['pad'], n=(0, -1, 0)).index
    # the mouth line: the strip of faces just under the mouth partial loop (>= 2 mouth verts, centre below it)
    mp = [Vector(p) for p in NOSE['mouth']]
    mouth_f = set()
    for f in bm.faces:
        hit = [v for v in f.verts if min((v.co - q).length for q in mp) < 1e-4]
        if len(hit) >= 2 and f.calc_center_median().z < sum(v.co.z for v in hit) / len(hit) - 1e-4:
            mouth_f.add(f.index)
    cupf = face_near(bm, ear_cup_point(), n=(0, -1, 0))
    cup_i = cupf.index
    # AD r2 O3: the inner ear is the (now tall) hollow: a lighter oval inside a dark rim
    inner_ear = {cup_i}
    shoulder = [(vert_near(bm, ringv(n, 2)).co.copy(), vert_near(bm, ringv(n, 1)).co.copy()) for n in ('NK', 'B0', 'B1')]
    bm.free()

    def body_rule(c, n, i):
        if i == socket_i:
            return 'nose'
        if i in inner_ear:
            return 'inner_ear'
        if i == nostril_i or (c.y < -0.868 and c.z > 0.625):
            return 'nose'                                    # the nose pad + the top strip behind it (not the sides)
        if i in mouth_f:
            return 'legs'                                    # a thin dark lip line on the lower muzzle loop
        if c.y < -0.735:
            return 'muzzle'                                  # everything ahead of the N3 loop (the stop)
        ear = (c - Vector(J['ear'])).length < 0.10 and c.z > 0.80 and abs(c.x) > 0.13
        if ear:
            return 'legs'
        if c.z < 0.345 or (c.y > 0.25 and c.z < 0.385 and abs(c.x) > 0.13):
            return 'legs'                                    # stockings: below the elbow / knee loops
        if n.z > 0.72 and c.y > -0.42 and c.z > 0.80:
            return 'back'                                    # the dark saddle along the back edge loops
        if -0.46 < c.y < -0.05 and 0.36 < c.z < 0.78 and n.y < -0.45 and abs(c.x) < 0.20:
            return 'chest'                                   # AD r2 O2: a broad front-facing chest plane between the
                                                             # forelegs (no side faces), fur hue at +12% value
        return 'fur'
    paint(body, pal('fur', 'legs', 'back', 'muzzle', 'nose', 'inner_ear', 'chest'), body_rule)

    pieces = []
    # AD note 5: eyes are solid dark beads, 1.5x the old bipyramid, seated 30% in the socket, with a
    # tiny glint: rim ring (8) -> a half-size front ring -> the apex; the glint is ONE small apex facet
    bm = bmesh.new()
    up = Vector((0, 0, 1))
    a = (up - s_n * up.dot(s_n)).normalized()
    b = s_n.cross(a).normalized()
    ra, rb, fr_d, ap_d, bk_d = EYE_R
    c = s_c + s_n * (bk_d - 0.30 * (ap_d + bk_d))      # 30% of the bead's depth sits below the socket floor
    ang = [2 * math.pi * (j + 0.5) / 8 for j in range(8)]
    rim = [bm.verts.new(c + a * (ra * math.cos(q)) + b * (rb * math.sin(q))) for q in ang]
    fro = [bm.verts.new(c + s_n * fr_d + a * (0.5 * ra * math.cos(q)) + b * (0.5 * rb * math.sin(q))) for q in ang]
    apex = bm.verts.new(c + s_n * ap_d)
    bk = bm.verts.new(c - s_n * bk_d)
    for j in range(8):
        k2 = (j + 1) % 8
        bm.faces.new([rim[j], rim[k2], fro[k2], fro[j]])
        bm.faces.new([fro[j], fro[k2], apex])
        bm.faces.new([rim[k2], rim[j], bk])
    gq = (fro[0].co + fro[1].co + apex.co) / 3                        # the upper apex facet: the glint
    eye = object_from_bm('eye', bm, mirror=True)
    paint(eye, pal('nose', 'glint'), lambda cc, n, i: 'glint' if (cc - gq).length < 0.1 * ra else 'nose')
    pieces.append(eye)

    # toes and claws: four toe lumps over the front of each paw, a dark hooked claw out of each
    toes, claws = bmesh.new(), bmesh.new()
    for paw in (FPAW2, HPAW):
        cx, hw, ti = paw[0] - paw[6], paw[1], paw[6]
        # AD r2 F2: every claw points along the paw axis (heel centre -> toe centre, the toe-in included),
        # fanned at most +-4 deg, the outer claws 20-25% shorter than the middle ones
        ax = Vector((-ti, paw[2] - paw[3], 0.0)).normalized()
        for f, sz in ((-0.72, 0.75), (-0.24, 1.0), (0.24, 0.95), (0.72, 0.8)):
            x = cx + f * hw * 0.95
            yf = paw_front(paw, x)
            sweep(toes, [(x, yf + 0.050, 0.060), (x, yf + 0.012, 0.052), (x, yf - 0.012, 0.030)],
                  [0.020, 0.023, 0.012], sides=5, up=(0, 0, 1), squash=0.8)
            d = Matrix.Rotation(math.radians(4.0 * f / 0.72), 3, 'Z') @ ax
            p0 = Vector((x, yf - 0.004, 0.034))
            p1 = p0 + d * (0.026 * sz) + Vector((0, 0, -0.004 * sz))
            p2 = p0 + d * (0.044 * sz) + Vector((0, 0, -0.028 * sz))
            sweep(claws, [p0, p1, p2], [0.010 * (0.5 + 0.5 * sz), 0.008 * (0.5 + 0.5 * sz), 0.0],
                  sides=3, up=(0, 0, 1), roll=math.pi / 2)
    toe = object_from_bm('toes', toes, mirror=True)
    paint(toe, pal('legs'), lambda cc, n, i: 'legs')
    claw = object_from_bm('claws', claws, mirror=True)
    paint(claw, pal('nose'), lambda cc, n, i: 'nose')
    pieces += [toe, claw]

    # AD note 1: the ruff plates read as shards / a second pair of ears -- removed; the hump is in the base
    return pieces


BONES = [
    ('hips', J['pelvis'], J['spine'], None),
    ('chest', J['spine'], J['chest'], 'hips', True),
    ('neck', J['chest'], J['head'], 'chest', True),
    ('head', J['head'], J['snout'], 'neck', True),
    ('ear.L', J['ear'], J['ear_tip'], 'head'),
    ('tail', J['tail'], J['tail_tip'], 'hips'),
    ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
    ('forearm.L', J['elbow'], fore_back(J['wrist'], 'wrist'), 'upperarm.L', True),   # AD r2 O4: wrist/paw moved back
    ('forepaw.L', fore_back(J['wrist'], 'wrist'), fore_back(J['fpaw']), 'forearm.L', True),
    ('thigh.L', J['hip'], J['knee'], 'hips'),
    ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
    ('hindpaw.L', J['ankle'], J['hpaw'], 'shin.L', True),
]


def walk_keys(n=8, period=32, amp_f=22.0, amp_h=20.0):
    """A lumbering four-beat walk: LH, LF, RH, RF a quarter cycle apart. Positive bone-X swings a
    leg back; the recovering (forward-swinging) leg folds its elbow/wrist or knee."""
    phase = {'thigh.L': 0.0, 'upperarm.L': 0.25, 'thigh.R': 0.5, 'upperarm.R': 0.75}
    keys = {}
    for j in range(n + 1):
        t = j / n
        f = 1 + round(t * period)
        kf = {}
        for bone, ph in phase.items():
            u = 2 * math.pi * (t + ph)
            swing = math.sin(u)                     # +1 = back, -1 = forward
            recover = max(0.0, -math.cos(u))        # >0 while the leg swings forward (sin decreasing)
            side = bone[-1]
            if bone.startswith('upperarm'):
                kf[bone] = (amp_f * swing, 0, 0)
                kf['forearm.' + side] = (30 * recover, 0, 0)
                kf['forepaw.' + side] = (35 * recover, 0, 0)
            else:
                kf[bone] = (amp_h * swing, 0, 0)
                kf['shin.' + side] = (28 * recover, 0, 0)
                kf['hindpaw.' + side] = (20 * recover, 0, 0)
        w = math.sin(2 * math.pi * t)                     # the roll of a heavy body, once per cycle
        w2 = math.sin(4 * math.pi * t)
        kf['hips'] = (0, 0, 2.5 * w)
        kf['chest'] = (1.5 * w2, 0, -3.5 * w)
        kf['neck'] = (2.0 * w2, 0, 3.0 * w)
        kf['head'] = (-2.5 * w2, 0, 4.0 * w)           # the low head swings side to side
        kf['tail'] = (0, 0, -8 * w)
        keys[f] = kf
    return keys


def blend_throat(body, its=4):
    """AD note 2: the neck/chest seam folded over in the rear-up. Blend the spine weights (chest / neck /
    head) across the throat loops by a few Laplacian passes over the neck region, so the seam is a
    ~50/50 ramp instead of a step; each vertex keeps its total spine share (limb weights untouched)."""
    me = body.data
    spine = [g for g in ('hips', 'chest', 'neck', 'head') if g in body.vertex_groups]
    gi = {body.vertex_groups[g].index: g for g in spine}
    nbr = {v.index: set() for v in me.vertices}
    for e in me.edges:
        a, b = e.vertices
        nbr[a].add(b); nbr[b].add(a)
    region = [v.index for v in me.vertices if -0.56 < v.co.y < -0.20 and v.co.z > 0.40]
    W = {v.index: {gi[g.group]: g.weight for g in v.groups if g.group in gi} for v in me.vertices}
    for _ in range(its):
        new = {}
        for i in region:
            share = sum(W[i].values())
            if share < 1e-4:
                continue
            acc = {}
            ring_ = [i] + list(nbr[i])
            for j in ring_:
                tot = sum(W[j].values())
                for g, w in W[j].items():
                    acc[g] = acc.get(g, 0.0) + (w / tot if tot > 1e-6 else 0.0)
            z = sum(acc.values())
            new[i] = {g: share * w / z for g, w in acc.items()} if z > 1e-9 else W[i]
        W.update(new)
    for i in region:
        for g in spine:
            vg = body.vertex_groups[g]
            w = W[i].get(g, 0.0)
            if w > 1e-5:
                vg.add([i], w, 'REPLACE')
            else:
                vg.remove([i])


def blend_all(body, pred, its=6):
    """AD note 2 (measured): the rear-up swipe folds the chest-front faces between the throat and the
    raised upper arms (y -.33, z .46-.52). Smooth ALL deform weights there (Laplacian, normalised) so
    the chest front ramps from chest to upperarm instead of stepping."""
    me = body.data
    names = {g.index: g.name for g in body.vertex_groups}
    nbr = {v.index: set() for v in me.vertices}
    for e in me.edges:
        a, b = e.vertices
        nbr[a].add(b); nbr[b].add(a)
    region = [v.index for v in me.vertices if pred(v.co)]
    W = {v.index: {g.group: g.weight for g in v.groups if g.weight > 1e-5} for v in me.vertices}
    for _ in range(its):
        new = {}
        for i in region:
            acc = {}
            for j in [i] + list(nbr[i]):
                tot = sum(W[j].values())
                for g, w in W[j].items():
                    acc[g] = acc.get(g, 0.0) + (w / tot if tot > 1e-6 else 0.0)
            z = sum(acc.values())
            if z > 1e-9:
                new[i] = {g: w / z for g, w in acc.items()}
        W.update(new)
    for i in region:
        for gidx, nm in names.items():
            w = W[i].get(gidx, 0.0)
            if w > 1e-4:
                body.vertex_groups[nm].add([i], w, 'REPLACE')
            else:
                body.vertex_groups[nm].remove([i])


def stage4(k, body, pieces):
    rig = armature(BONES)
    skin(body, rig)
    blend_throat(body)
    blend_all(body, lambda c: -0.44 < c.y < -0.16 and 0.34 < c.z < 0.76 and abs(c.x) > 0.04)
    for p in pieces:
        nm = p.name.replace('piece_', '')
        if nm in ('ruff', 'eye'):
            bind(p, rig, body=body)                  # AD r2 must-fix: the eye beads ride the face skin (drift 0)
        else:
            bind(p, rig)                             # toes/claws: the nearest bone per vertex (L and R paws)
    # idle: breathing, a slow head sway, a sniff (head up, two quick bobs), ear flicks
    clip(rig, 'idle', {
        1: {},
        8: {'chest': (-1.5, 0, 0), 'neck': (1, 0, 3), 'head': (2, 0, 6), 'hips': (0.5, 0, 0)},
        16: {'chest': (0.5, 0, 0), 'neck': (-4, 0, 2), 'head': (-12, 0, 3), 'ear.L': (0, 0, 0)},
        19: {'chest': (0.5, 0, 0), 'neck': (-4, 0, 2), 'head': (-8, 0, 3), 'ear.L': (-20, 0, 0)},
        22: {'chest': (0.5, 0, 0), 'neck': (-4, 0, 2), 'head': (-13, 0, 3), 'ear.L': (0, 0, 0)},
        25: {'chest': (0.0, 0, 0), 'neck': (-3, 0, 1), 'head': (-8, 0, 2)},
        34: {'chest': (-1.5, 0, 0), 'neck': (1, 0, -3), 'head': (3, 0, -6), 'hips': (0.5, 0, 0), 'tail': (0, 0, 10)},
        42: {'chest': (0.5, 0, 0), 'neck': (0, 0, -1), 'head': (0, 0, -2), 'ear.R': (-15, 0, 0), 'tail': (0, 0, -6)},
        48: {},
    })
    clip(rig, 'move', walk_keys())
    # attack: crouch, rear up on the hind legs, a left then a right forepaw swipe, drop back down
    up = {'hips': (-32, 0, 0), 'thigh.L': (26, 0, 0), 'thigh.R': (26, 0, 0), 'shin.L': (8, 0, 0), 'shin.R': (8, 0, 0),
          'hindpaw.L': (-4, 0, 0), 'hindpaw.R': (-4, 0, 0), 'chest': (-8, 0, 0), 'neck': (4, 0, 0), 'head': (11, 0, 0),   # AD note 2: -15 deg on the neck/head bend
          'tail': (20, 0, 0)}

    def rear(extra):
        d = dict(up)
        d.update(extra)
        return d
    clip(rig, 'attack', {
        1: {},
        8: {'chest': (6, 0, 0), 'neck': (8, 0, 0), 'head': (8, 0, 0), 'thigh.L': (-6, 0, 0), 'thigh.R': (-6, 0, 0),
            'upperarm.L': (8, 0, 0), 'upperarm.R': (8, 0, 0), 'ear.L': (-25, 0, 0), 'ear.R': (-25, 0, 0)},
        16: rear({'upperarm.L': (-58, 0, -12), 'forearm.L': (48, 0, 0), 'forepaw.L': (30, 0, 0),
                  'upperarm.R': (-50, 0, 8), 'forearm.R': (52, 0, 0), 'forepaw.R': (30, 0, 0),
                  'ear.L': (-30, 0, 0), 'ear.R': (-30, 0, 0)}),
        22: rear({'upperarm.L': (-10, 0, 25), 'forearm.L': (10, 0, 0), 'forepaw.L': (-10, 0, 0),
                  'upperarm.R': (-52, 0, 8), 'forearm.R': (52, 0, 0), 'forepaw.R': (30, 0, 0),
                  'chest': (-8, 0, 10), 'head': (16, 0, -8), 'ear.L': (-30, 0, 0), 'ear.R': (-30, 0, 0)}),
        28: rear({'upperarm.L': (-52, 0, -8), 'forearm.L': (52, 0, 0), 'forepaw.L': (30, 0, 0),
                  'upperarm.R': (-10, 0, -25), 'forearm.R': (10, 0, 0), 'forepaw.R': (-10, 0, 0),
                  'chest': (-8, 0, -10), 'head': (16, 0, 8), 'ear.L': (-30, 0, 0), 'ear.R': (-30, 0, 0)}),
        36: {'chest': (4, 0, 0), 'neck': (4, 0, 0), 'head': (4, 0, 0), 'upperarm.L': (-8, 0, 0), 'upperarm.R': (-8, 0, 0)},
        44: {},
    }, loc={1: {}, 16: {'hips': (0, 0, 0.06)}, 22: {'hips': (0, 0, 0.06)}, 28: {'hips': (0, 0, 0.06)}, 36: {}, 44: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
