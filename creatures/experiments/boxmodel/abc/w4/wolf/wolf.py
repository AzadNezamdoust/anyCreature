import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='wolf', model='opus')

# the skeleton the model is built on (metres, faces -Y, left flank +X, feet on z = 0)
J = dict(
    hip=(0.0, 0.30, 0.60), spine=(0.0, 0.08, 0.63), chest=(0.0, -0.12, 0.64),
    neck=(0.0, -0.20, 0.70), head=(0.0, -0.37, 0.86), snout=(0.0, -0.64, 0.81),
    ear=(0.085, -0.40, 0.99), ear_tip=(0.10, -0.41, 1.09),
    shoulder=(0.11, -0.19, 0.58), elbow=(0.105, -0.19, 0.37), wrist=(0.10, -0.205, 0.12),
    ftoe=(0.10, -0.31, 0.01),
    thigh=(0.11, 0.25, 0.56), knee=(0.115, 0.245, 0.33), hock=(0.11, 0.37, 0.19),
    hball=(0.10, 0.325, 0.05), htoe=(0.10, 0.26, 0.01),
    tail0=(0.0, 0.39, 0.58), tail1=(0.0, 0.49, 0.44), tail2=(0.0, 0.57, 0.29), tail3=(0.0, 0.68, 0.20),
)


def tsec(c, d, t, w):
    """A tail section: centre (y, z), path direction (dy, dz), half thickness t, half width w."""
    L = math.hypot(*d)
    dy, dz = d[0] / L, d[1] / L
    uy, uz = -dz, dy                       # 'up' of the section: perpendicular, pointing up-back
    if uz < 0:
        uy, uz = -uy, -uz
    prof = [(0.0, 1.0), (0.6, 0.8), (1.0, 0.3), (0.95, -0.4), (0.55, -0.85), (0.0, -1.0)]
    return [(w * a, c[0] + uy * t * b, c[1] + uz * t * b) for a, b in prof]


# the loft: each ring runs from the dorsal seam vertex to the ventral seam vertex
# [top, v1 (ear-inner / saddle edge), v2 (brow corner / upper flank), v3 (cheek / lower flank),
#  v4 (jaw / keel side), bottom]
RINGS = [
    # head
    [(0, -0.668, 0.842), (0.02, -0.668, 0.840), (0.030, -0.672, 0.820), (0.032, -0.672, 0.790), (0.022, -0.660, 0.765), (0, -0.655, 0.760)],
    [(0, -0.585, 0.868), (0.028, -0.585, 0.866), (0.050, -0.585, 0.845), (0.056, -0.585, 0.790), (0.045, -0.585, 0.752), (0, -0.585, 0.745)],
    [(0, -0.510, 0.930), (0.035, -0.510, 0.930), (0.076, -0.505, 0.895), (0.092, -0.500, 0.800), (0.060, -0.500, 0.748), (0, -0.500, 0.742)],
    [(0, -0.445, 0.985), (0.045, -0.445, 0.990), (0.112, -0.440, 0.945), (0.137, -0.435, 0.840), (0.075, -0.440, 0.750), (0, -0.450, 0.735)],
    [(0, -0.360, 0.985), (0.045, -0.360, 0.990), (0.130, -0.355, 0.950), (0.165, -0.350, 0.830), (0.100, -0.400, 0.720), (0, -0.450, 0.700)],
    # neck (tilted rings: the neck runs up and forward)
    [(0, -0.270, 0.930), (0.050, -0.270, 0.930), (0.160, -0.280, 0.880), (0.190, -0.330, 0.740), (0.115, -0.405, 0.675), (0, -0.462, 0.640)],
    [(0, -0.150, 0.830), (0.060, -0.150, 0.830), (0.178, -0.170, 0.760), (0.192, -0.250, 0.600), (0.118, -0.355, 0.530), (0, -0.445, 0.495)],
    # chest: the front-leg root quad is v3-v4 between these two rings
    [(0, -0.060, 0.765), (0.070, -0.070, 0.760), (0.175, -0.120, 0.660), (0.155, -0.270, 0.470), (0.070, -0.300, 0.405), (0, -0.310, 0.400)],
    [(0, 0.030, 0.740), (0.075, 0.030, 0.735), (0.160, 0.000, 0.640), (0.150, -0.130, 0.460), (0.070, -0.140, 0.395), (0, -0.140, 0.385)],
    [(0, 0.110, 0.725), (0.075, 0.110, 0.720), (0.140, 0.090, 0.640), (0.125, 0.010, 0.500), (0.055, -0.010, 0.420), (0, -0.020, 0.410)],
    # waist, then the hips: the hind-leg root quad is v3-v4 between the two hip rings
    [(0, 0.170, 0.718), (0.070, 0.170, 0.713), (0.115, 0.150, 0.640), (0.110, 0.080, 0.530), (0.050, 0.070, 0.475), (0, 0.070, 0.468)],
    [(0, 0.220, 0.712), (0.075, 0.220, 0.707), (0.140, 0.200, 0.640), (0.150, 0.150, 0.505), (0.070, 0.150, 0.475), (0, 0.150, 0.472)],
    [(0, 0.340, 0.670), (0.075, 0.340, 0.665), (0.140, 0.340, 0.600), (0.140, 0.350, 0.470), (0.070, 0.330, 0.435), (0, 0.320, 0.432)],
    # rump into the tail root
    [(0, 0.400, 0.640), (0.040, 0.400, 0.638), (0.075, 0.402, 0.605), (0.075, 0.385, 0.545), (0.040, 0.372, 0.515), (0, 0.366, 0.508)],
    tsec((0.425, 0.490), (0.15, -1.0), 0.066, 0.064),
    tsec((0.452, 0.360), (0.3, -0.95), 0.078, 0.074),
    tsec((0.510, 0.250), (0.75, -0.65), 0.072, 0.066),
    tsec((0.595, 0.198), (1.0, -0.15), 0.048, 0.046),
    tsec((0.672, 0.200), (1.0, 0.05), 0.012, 0.012),
]
FRONT_ROOT = 7      # ring index: quad v3-v4 between rings 7 and 8
HIND_ROOT = 11      # quad v3-v4 between rings 11 and 12
EAR_ROOT = 3        # quad v1-v2 between rings 3 and 4

# leg levels: (cx, cy, cz, half-width x, half-depth y)
FRONT_LEG = [(0.105, -0.200, 0.340, 0.045, 0.060), (0.102, -0.200, 0.240, 0.036, 0.046),
             (0.100, -0.207, 0.130, 0.030, 0.036), (0.100, -0.258, 0.055, 0.040, 0.050),
             (0.100, -0.285, 0.000, 0.047, 0.052)]
HIND_LEG = [(0.118, 0.240, 0.400, 0.052, 0.090), (0.115, 0.262, 0.320, 0.046, 0.072),
            (0.112, 0.325, 0.250, 0.038, 0.052), (0.108, 0.372, 0.190, 0.033, 0.038),
            (0.102, 0.330, 0.058, 0.040, 0.046), (0.100, 0.298, 0.000, 0.047, 0.052)]
EAR = [((0.094, -0.405, 1.045), 0.62), ((0.110, -0.412, 1.100), 0.10)]


def leg(bm, face, levels):
    f = face
    for cx, cy, cz, wx, dy in levels:
        f = extrude(bm, [f])['faces'][0]
        c = centre(f.verts)
        for v in f.verts:
            sx = 1 if v.co.x > c.x else -1
            sy = 1 if v.co.y > c.y else -1
            v.co = Vector((cx + sx * wx, cy + sy * dy, cz))
    return f


def taper(bm, face, levels):
    f = face
    pc, ps = centre(f.verts), 1.0
    for c, s in levels:
        f = extrude(bm, [f])['faces'][0]
        for v in f.verts:
            v.co = Vector(c) + (v.co - pc) * (s / ps)
        pc, ps = Vector(c), s
    return f


def quad(rings, i, a, b):
    return [rings[i][a], rings[i][b], rings[i + 1][b], rings[i + 1][a]]


def stage1(k):
    bm = bmesh.new()
    R = [ring(bm, r) for r in RINGS]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    cap(bm, list(reversed(R[0])))
    cap(bm, R[-1])
    bm.faces.ensure_lookup_table()

    def face_of(vs):
        s = set(vs)
        return next(f for f in bm.faces if set(f.verts) == s)

    fl = face_of(quad(R, FRONT_ROOT, 3, 4))
    hl = face_of(quad(R, HIND_ROOT, 3, 4))
    er = face_of(quad(R, EAR_ROOT, 1, 2))
    leg(bm, fl, FRONT_LEG)
    leg(bm, hl, HIND_LEG)
    ear = taper(bm, er, EAR)
    snap_seam(bm, 1e-6)
    return object_from_bm('body', bm)


EYE_FACE = (0.104, -0.470, 0.870)
META['keep_valleys'] = lambda c: (Vector(c) - Vector((abs(c[0]), c[1], c[2])) * 0 - Vector(EYE_FACE)).length < 0.035     if c[0] >= 0 else (Vector((-c[0], c[1], c[2])) - Vector(EYE_FACE)).length < 0.035


def stage2(k, body):
    bm = edit(body)
    # --- the face: a nose block and an eye socket under a brow
    with k.topo(bm, 'loop', 'nose block: a loop round the muzzle behind the nose pad (black nose border)'):
        nose = loopcut(bm, edge_near(bm, (0, -0.6265, 0.855)), t=0.38, near=vert_near(bm, (0, -0.668, 0.842)))
    with k.topo(bm, 'inset', 'eye socket in the side-of-face plane under the brow'):
        eye = inset(bm, [face_near(bm, EYE_FACE, n=(1, 0, 0))], 0.45)[0]
    ev = list(eye.verts)
    scale(ev, 0.75)
    move(ev, (-0.008, -0.004, 0.012))
    move(ev, -eye.normal * 0.014)                          # sink the socket so the eye piece sits in it
    for v in verts_where(bm, lambda c: abs(c.y + 0.44) < 0.006 and abs(c.z - 0.945) < 0.006):
        v.co += Vector((0.008, -0.012, 0.004))          # the brow corner overhangs the socket
    for v in nose:                                        # the nose pad steps down from the muzzle bridge
        if v.co.z > 0.82:
            v.co.z += 0.006
    # --- the muzzle as a tapered box: one side plane and one bridge plane
    side = verts_where(bm, lambda c: c.y < -0.49 and c.x > 0.025 and 0.775 < c.z < 0.905)
    flatten(side)
    bridge_ = verts_where(bm, lambda c: -0.6 < c.y < -0.49 and c.z > 0.86 and c.x < 0.04)
    flatten(bridge_)
    # the tail tip: open the last ring so the brush ends in a blunt point, not needles
    tip = verts_where(bm, lambda c: c.y > 0.66)
    tc = centre(tip)
    scale(tip, (1.9, 1.0, 1.9), pivot=(0.0, tc.y, tc.z))     # pivot on the seam: seam verts stay at x = 0
    commit(body, bm)


PAL = dict(grey='#9c978e', saddle='#65636b', tan='#b59d76', cream='#efe6cf', amber='#e0a030', black='#1e1b1b')


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.637:
        return 'cream' if z < 0.815 else 'grey'                                   # nose pad, bordered by the stage-2 nose loop
    if y > 0.585 and z < 0.30:
        return 'black'                                   # the dark tail tip (last tail span)
    if z > 0.995 and n.y < -0.35:
        return 'cream'                                   # inner ear
    if y < -0.40 and z < 0.785 and n.z < 0.5:
        return 'cream'                                   # lip and jaw, border on the v3 line
    if y < -0.25 and 0.43 < z < 0.80 and n.y < -0.3 and x < 0.15:
        return 'cream'                                   # the bib down the brisket keel
    if z < 0.345 and y < 0.45:
        return 'tan'                                     # legs below elbow and stifle
    if n.z > 0.72 and -0.16 < y < 0.43 and z > 0.6:
        return 'saddle'                                  # the dark back saddle on the dorsal plane
    return 'grey'


def pyramid(bm, base, tip):
    vs = ring(bm, base)
    t = bm.verts.new(Vector(tip))
    bm.faces.new(vs)
    for i in range(len(vs)):
        bm.faces.new([vs[i], vs[(i + 1) % len(vs)], t])


def clump(bm, c, n, r, tipdir, sink=0.014, sides=3):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized()
    w = n.cross(u)
    b0 = Vector(c) - n * sink
    base = [b0 + (u * math.cos(a) + w * math.sin(a)) * r for a in [2 * math.pi * i / sides for i in range(sides)]]
    pyramid(bm, base, Vector(c) + Vector(tipdir))


def stage3(k, body):
    paint(body, PAL, body_rule)
    me = body.data
    polys = [(p.center.copy(), p.normal.copy(), p.area) for p in me.polygons]
    pieces = []
    # eyes: a lens in each socket, proud of the socket floor
    cand = [q for q in polys if (q[0] - Vector(EYE_FACE)).length < 0.03 and q[1].x > 0.3]
    ec, en, _ = min(cand, key=lambda q: q[2])
    bm = bmesh.new()
    u = en.cross(Vector((0, 0, 1))).normalized(); w = en.cross(u)
    rim = [ec + en * 0.004 + (u * math.cos(a) * 1.25 + w * math.sin(a)) * 0.014 for a in [math.pi * i / 3 for i in range(6)]]
    rv = ring(bm, rim)
    f, b = bm.verts.new(ec + en * 0.011), bm.verts.new(ec - en * 0.010)
    for i in range(6):
        bm.faces.new([rv[i], rv[(i + 1) % 6], f]); bm.faces.new([rv[(i + 1) % 6], rv[i], b])
    eye = object_from_bm('eye', bm, mirror=True); paint(eye, {'amber': PAL['amber']}, lambda c, n, i: 'amber')
    pieces.append(eye)
    # neck ruff: bold clumps on the neck sides and cheeks, raked back and down
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons])
    bm = bmesh.new()
    # shingled blades lying back along the neck: few, big, raked (not thorns standing off the surface)
    for c0 in [(0.15, -0.36, 0.80), (0.17, -0.30, 0.70), (0.175, -0.24, 0.60), (0.155, -0.22, 0.80),
               (0.16, -0.16, 0.70), (0.145, -0.37, 0.72)]:
        hit, n, _, _ = bvh.find_nearest(Vector(c0))
        clump(bm, hit, n, 0.042, n * 0.05 + Vector((0.0, 0.07, -0.035)), sink=0.012)
    ruff = object_from_bm('ruff', bm, mirror=True); paint(ruff, {'grey': PAL['grey']}, lambda c, n, i: 'grey')
    pieces.append(ruff)
    # cream bib: clumps hanging off the brisket
    bm = bmesh.new()
    for c, n, a in polys:
        if c.y < -0.30 and 0.46 < c.z < 0.70 and n.y < -0.5 and c.x > 0.035:
            clump(bm, c, n, 0.028, n * 0.025 + Vector((0.0, 0.0, -0.055)))
    bib = object_from_bm('bib', bm, mirror=True); paint(bib, {'cream': PAL['cream']}, lambda c, n, i: 'cream')
    pieces.append(bib)
    # tail brush tip: one dark blade past the tail end (on the seam, built whole)
    bm = bmesh.new()
    tip = [v.co.copy() for v in me.vertices if v.co.y > 0.66]
    tc = sum(tip, Vector()) / len(tip)
    pyramid(bm, [tc + Vector((0.018, -0.02, 0.0)), tc + Vector((0.0, -0.02, 0.022)),
                 tc + Vector((-0.018, -0.02, 0.0)), tc + Vector((0.0, -0.02, -0.022))], tc + Vector((0.0, 0.065, -0.01)))
    brush = object_from_bm('brush', bm, mirror=False); paint(brush, {'black': PAL['black']}, lambda c, n, i: 'black')
    pieces.append(brush)
    # nose pad: a black block capping the top front of the muzzle (built whole, across the seam)
    bm = bmesh.new()
    top = ring(bm, [(-0.026, -0.650, 0.848), (0.026, -0.650, 0.848), (0.022, -0.690, 0.836), (-0.022, -0.690, 0.836)])
    bot = ring(bm, [(-0.024, -0.650, 0.806), (0.024, -0.650, 0.806), (0.018, -0.684, 0.803), (-0.018, -0.684, 0.803)])
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    for i in range(4):
        bm.faces.new([top[i], bot[i], bot[(i + 1) % 4], top[(i + 1) % 4]])
    nosep = object_from_bm('nose', bm, mirror=False); paint(nosep, {'black': PAL['black']}, lambda c, n, i: 'black')
    pieces.append(nosep)
    # toe claws: two per paw, the middle toes leading
    bm = bmesh.new()
    for x in (0.085, 0.115):
        for yb, yt in ((-0.326, -0.352), (0.262, 0.238)):
            pyramid(bm, [(x - 0.007, yb, 0.009), (x + 0.007, yb, 0.009), (x + 0.007, yb, 0.021), (x - 0.007, yb, 0.021)],
                    (x, yt, 0.006))
    claws = object_from_bm('claws', bm, mirror=True); paint(claws, {'black': PAL['black']}, lambda c, n, i: 'black')
    pieces.append(claws)
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hip'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['snout'], 'neck', True),
        ('ear.L', J['ear'], J['ear_tip'], 'head'),
        ('tail1', J['tail0'], J['tail1'], 'hips'),
        ('tail2', J['tail1'], J['tail2'], 'tail1', True),
        ('tail3', J['tail2'], J['tail3'], 'tail2', True),
        ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('fpaw.L', J['wrist'], J['ftoe'], 'forearm.L', True),
        ('thigh.L', J['thigh'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
        ('meta.L', J['hock'], J['hball'], 'shin.L', True),
        ('hpaw.L', J['hball'], J['htoe'], 'meta.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing through the chest, an ear twitch, a lazy tail
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 4)},
                       20: {'chest': (2.5, 0, 0), 'neck': (-2.5, 0, 0), 'ear.L': (-14, 0, 6), 'tail1': (0, 0, 6)},
                       24: {'chest': (2.5, 0, 0), 'neck': (-2.5, 0, 0), 'ear.L': (0, 0, 0), 'tail1': (0, 0, 5)},
                       36: {'chest': (1.0, 0, 0), 'neck': (-1.0, 0, 0), 'tail1': (0, 0, -4)}, 48: {}})
    # move: a trot, diagonal pairs (L fore + R hind, R fore + L hind)
    def trot(a, fold_a, fold_b):
        b = -a
        return {'upperarm.L': (a, 0, 0), 'thigh.R': (a * 0.8, 0, 0), 'upperarm.R': (b, 0, 0), 'thigh.L': (b * 0.8, 0, 0),
                'forearm.L': (fold_a, 0, 0), 'meta.R': (-fold_a * 0.7, 0, 0),
                'forearm.R': (fold_b, 0, 0), 'meta.L': (-fold_b * 0.7, 0, 0),
                'neck': (abs(a) * 0.1, 0, 0), 'tail1': (0, 0, a * 0.3)}
    clip(rig, 'move', {1: trot(16, 0, 0), 7: trot(0, 0, -28), 13: trot(-16, 0, 0), 19: trot(0, -28, 0), 25: trot(16, 0, 0)})
    # attack: gather, head-down lunge, snap, recover
    clip(rig, 'attack', {
        1: {},
        8: {'spine': (4, 0, 0), 'neck': (-6, 0, 0), 'head': (4, 0, 0), 'thigh.L': (10, 0, 0), 'thigh.R': (10, 0, 0),
            'upperarm.L': (-8, 0, 0), 'upperarm.R': (-8, 0, 0), 'tail1': (8, 0, 0)},
        16: {'spine': (-5, 0, 0), 'neck': (-22, 0, 0), 'head': (10, 0, 0), 'thigh.L': (-12, 0, 0), 'thigh.R': (-12, 0, 0),
             'upperarm.L': (18, 0, 0), 'upperarm.R': (18, 0, 0), 'forearm.L': (-6, 0, 0), 'forearm.R': (-6, 0, 0),
             'ear.L': (-20, 0, 0), 'tail1': (-6, 0, 0)},
        20: {'spine': (-5, 0, 0), 'neck': (-20, 0, 0), 'head': (-6, 0, 0), 'thigh.L': (-12, 0, 0), 'thigh.R': (-12, 0, 0),
             'upperarm.L': (18, 0, 0), 'upperarm.R': (18, 0, 0), 'forearm.L': (-6, 0, 0), 'forearm.R': (-6, 0, 0),
             'ear.L': (-20, 0, 0), 'tail1': (-6, 0, 0)},
        24: {'spine': (-3, 0, 0), 'neck': (-14, 0, 0), 'head': (8, 0, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0),
             'ear.L': (-12, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
