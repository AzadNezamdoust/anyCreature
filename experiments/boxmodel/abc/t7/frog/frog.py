import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
import numpy as np

META = dict(creature='frog', model='opus', keep_valleys=lambda c: c.z > 0.25)

# the skeleton the model is built on (metres; faces -Y; left flank +X)
J = dict(
    hip=(0.0, 0.15, 0.08), spine=(0.0, 0.02, 0.11), neck=(0.0, -0.07, 0.14), snout=(0.0, -0.21, 0.18),
    jaw0=(0.0, -0.06, 0.10), jaw1=(0.0, -0.23, 0.105), throat0=(0.0, -0.09, 0.066), throat1=(0.0, -0.17, 0.08),
    eye=(0.106, -0.135, 0.205), eyetop=(0.106, -0.135, 0.29),
    shoulder=(0.095, -0.035, 0.078), elbow=(0.135, -0.05, 0.052), wrist=(0.15, -0.095, 0.022), fingers=(0.16, -0.145, 0.008),
    hipL=(0.14, 0.095, 0.078), kneeF=(0.215, -0.035, 0.072), knee=(0.24, -0.045, 0.062), shin0=(0.285, -0.012, 0.042),
    ankle=(0.315, 0.135, 0.03), heel=(0.339, 0.16, 0.016), ball=(0.375, 0.04, 0.009), toes=(0.37, -0.05, 0.007))

# body rings, snout -> rump: (y, z top, z bottom, half width, z lip, lip gap)
RINGS = [
    (-0.255, 0.150, 0.105, 0.045, 0.122, 0.008),
    (-0.225, 0.188, 0.088, 0.088, 0.120, 0.010),
    (-0.170, 0.218, 0.072, 0.122, 0.118, 0.012),
    (-0.100, 0.232, 0.060, 0.134, 0.115, 0.012),
    (-0.060, 0.232, 0.052, 0.132, 0.112, 0.014),
    (-0.010, 0.226, 0.040, 0.136, 0.106, 0.030),
    (0.060, 0.215, 0.026, 0.146, 0.098, 0.052),
    (0.130, 0.195, 0.016, 0.142, 0.090, 0.056),
    (0.185, 0.158, 0.012, 0.118, 0.080, 0.040),
    (0.225, 0.100, 0.020, 0.070, 0.065, 0.020),
]


def half_ring(y, zt, zb, hw, zl, gap):
    z4 = zl - gap
    return [(0.0, y, zt), (0.70 * hw, y, zt - 0.1 * (zt - zl)), (0.95 * hw, y, zl + 0.45 * (zt - zl)),
            (hw, y, zl), (0.93 * hw, y, z4), (0.55 * hw, y, zb + 0.25 * (z4 - zb)), (0.0, y, zb)]


def sec(c, h, v, t=1.0):
    """A quad section; t < 1 narrows its top edge (a mound, not a crate)."""
    c, h, v = V(c), V(h), V(v)
    return [c + v + h * t, c + v - h * t, c - v - h, c - v + h]


def step(bm, face, corners):
    """Extrude one quad and place its new corners, matched to the old ones with the least travel."""
    old = [l.vert for l in face.loops]
    r = extrude(bm, [face])
    nv = set(r['verts'])
    seq = [next(e.other_vert(v) for e in v.link_edges if e.other_vert(v) in nv) for v in old]
    best = None
    for d in (1, -1):
        for s in range(4):
            cost = sum((old[i].co - corners[(d * i + s) % 4]).length_squared for i in range(4))
            if best is None or cost < best[0]:
                best = (cost, d, s)
    _, d, s = best
    for i in range(4):
        seq[i].co = corners[(d * i + s) % 4].copy()
    return r['faces'][0]


def chain(bm, face, secs):
    for s in secs:
        face = step(bm, face, sec(*s))
    return face


def bend(bm, face, P, sgn, r, steps, t=1.0):
    """A U-turn about a vertical axis at P: each section swings round the pivot
    (inner corner at radius r), so the fold keeps its inside edge and never twists."""
    for deg, w, hv, z in steps:
        a = math.radians(deg)
        u = V(-math.cos(a), sgn * math.sin(a), 0.0)
        c = V(P[0], P[1], z) + u * (r + w / 2)
        face = step(bm, face, sec(c, u * (w / 2), (0, 0, hv), t))
    return face


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, half_ring(*r)) for r in RINGS]
    bands = [bridge(bm, a, b) for a, b in zip(rows, rows[1:])]
    cap(bm, rows[0]); cap(bm, rows[-1])
    recalc_normals(bm)
    eye_f, arm_f, leg_f = bands[2][1], bands[4][4], bands[6][3]
    # eye turret: up out of the head's top-side plane
    chain(bm, eye_f, [((0.112, -0.135, 0.228), (0.040, 0, 0), (0, 0.044, 0)),
                      ((0.110, -0.135, 0.262), (0.029 * math.cos(math.radians(40)), 0.029 * math.sin(math.radians(40)), 0),
                       (-0.029 * math.sin(math.radians(40)), 0.029 * math.cos(math.radians(40)), 0))])
    # front leg: straight, splayed hand on the ground
    chain(bm, arm_f, [(J['elbow'], (0.022, 0, 0), (0, 0.024, 0)),
                      (J['wrist'], (0.016, 0, 0), (0, 0.017, 0)),
                      ((0.16, -0.14, 0.010), (0.034, 0, 0), (0, 0, 0.009))])
    # hind leg: thigh forward, knee turns out, shin back, heel turns out, long foot forward
    f = chain(bm, leg_f, [((0.198, 0.055, 0.078), (0.041, 0.021, 0), (0, 0, 0.046), 0.5),
                          (J['kneeF'], (0.036, 0, 0), (0, 0, 0.040), 0.55)])
    f = bend(bm, f, (0.257, -0.035), -1, 0.006, [(60, 0.060, 0.037, 0.066), (120, 0.050, 0.033, 0.056),
                                                  (180, 0.044, 0.028, 0.046)], 0.6)
    f = chain(bm, f, [(J['ankle'], (0.018, 0, 0), (0, 0, 0.021), 0.6)])
    f = bend(bm, f, (0.339, 0.135), 1, 0.006, [(60, 0.036, 0.018, 0.025), (120, 0.040, 0.014, 0.018),
                                               (180, 0.044, 0.011, 0.012)], 0.75)
    chain(bm, f, [(J['ball'], (0.032, 0.004, 0), (0, 0, 0.008), 0.75),
                  (J['toes'], (0.036, 0.006, 0), (0, 0, 0.006), 0.8)])
    snap_seam(bm)
    _hits(bm)
    return object_from_bm('body', bm)


def _hits(bm):
    from mathutils.bvhtree import BVHTree
    bm.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(bm)
    for i, j in t.overlap(t):
        if i < j and not set(bm.faces[i].verts) & set(bm.faces[j].verts):
            say('HIT', tuple(round(x, 3) for x in bm.faces[i].calc_center_median()),
                tuple(round(x, 3) for x in bm.faces[j].calc_center_median()))


def _limb_edge(bm, root, pred):
    v = vert_near(bm, root)
    return next(e for e in v.link_edges if pred(e.other_vert(v).co))


def stage2(k, body):
    bm = edit(body)
    r4, r6 = half_ring(*RINGS[4]), half_ring(*RINGS[6])
    with k.topo(bm, 'loop', 'hip loop round the thigh root: the hop swings the thigh here'):
        loopcut(bm, _limb_edge(bm, r6[3], lambda c: c.x > 0.165), t=0.4)
    with k.topo(bm, 'loop', 'chest loop behind the jaw hinge (its ring runs on down the front of the upper arm): the head nods here'):
        loopcut(bm, _limb_edge(bm, r4[4], lambda c: c.x > 0.125 and c.z < 0.08), t=0.45)
    with k.topo(bm, 'inset', 'eye socket in the top of each eye bulge: the gold eye sits in it'):
        inset(bm, [face_near(bm, (0.110, -0.135, 0.262), n=(0, 0, 1))], 0.22, -0.004)
    # upper lip overhangs the chin: the mouth line reads from the side
    for v in verts_where(bm, lambda c: c.y < -0.2 and c.z < 0.116):
        v.co.y += 0.008
    # throat sac: the chin rounds down a little
    for v in verts_where(bm, lambda c: -0.18 < c.y < -0.09 and c.z < 0.075 and c.x < 0.1):
        v.co.z -= 0.006
    # dorsolateral ridges along the back: a crease where the back plane turns to the flank
    for r in RINGS[4:9]:
        v = vert_near(bm, half_ring(*r)[1])
        v.co.z += 0.007; v.co.x += 0.004
    commit(body, bm)


PAL = {'skin': '#5fae3c', 'spot': '#2f6b2a', 'belly': '#efe0b0', 'gold': '#f2c230', 'black': '#151515'}
EYE_C = (0.110, -0.135, 0.272)


def _lip(y):
    ys = [r[0] for r in RINGS]
    return float(np.interp(y, ys, [r[4] for r in RINGS])), float(np.interp(y, ys, [r[5] for r in RINGS]))


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    zl, g = _lip(y)
    if y < -0.058 and x > 0.02 and abs(n.z) < 0.75 and abs(z - (zl - g / 2)) < g / 2 + 0.002:
        return 'black'                       # the wide mouth line: the lip strip between v3 and v4
    if z > 0.25 and x > 0.07:
        return 'gold'                        # eye socket (under the eye piece)
    if y < -0.058 and x < 0.14 and 0.03 < z < zl - g - 0.001:
        return 'belly'                       # cream jaw and throat
    if n.z < -0.3 and z < 0.15:
        return 'belly'
    return 'skin'


def prism(bm, a, b):
    ra, rb = ring(bm, a), ring(bm, b)
    fs = bridge(bm, ra, rb, closed=True)
    return fs + [cap(bm, ra), cap(bm, rb[::-1])]


def digit(bm, p0, p1, w0, w1, h0, h1):
    """A tapered toe lying on the ground from p0 to p1, and its pad at the tip. Returns (toe faces, pad faces)."""
    p0, p1 = V(p0), V(p1)
    d = (p1 - p0).normalized(); s_ = V(-d.y, d.x, 0)
    toe = prism(bm, sec(p0, s_ * w0, (0, 0, h0), 0.7), sec(p1, s_ * w1, (0, 0, h1), 0.7))
    c = p1 + d * 0.002
    pad = prism(bm, sec(c - d * 0.007, s_ * (w1 * 1.7), (0, 0, h1 * 1.5), 0.8), sec(c + d * 0.007, s_ * (w1 * 1.5), (0, 0, h1 * 1.3), 0.8))
    return toe, pad


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    paint(body, PAL, body_rule)
    pieces = []
    # eyes: a faceted gold dome seated in the socket, a horizontal black pupil looking out and forward
    bm = bmesh.new()
    c = V(EYE_C)
    rows = []
    for dz, r in ((-0.020, 0.024), (-0.002, 0.029), (0.014, 0.022), (0.022, 0.010)):
        rows.append(ring(bm, [c + V(r * math.cos(math.radians(22.5 + 45 * i)), r * math.sin(math.radians(22.5 + 45 * i)), dz) for i in range(8)]))
    for a_, b_ in zip(rows, rows[1:]):
        bridge(bm, a_, b_, closed=True)
    cap(bm, rows[0]); cap(bm, rows[-1][::-1])
    eye = object_from_bm('eye', bm); paint(eye, {'gold': PAL['gold']}, lambda c_, n_, i_: 'gold'); pieces.append(eye)
    bm = bmesh.new()
    d = V(1.0, -0.55, 0.2).normalized(); th = d.cross(V(0, 0, 1)).normalized(); tv = th.cross(d)
    p = c + d * 0.0275
    prism(bm, sec(p - d * 0.003, th * 0.012, tv * 0.0045, 0.8), sec(p + d * 0.0025, th * 0.011, tv * 0.004, 0.8))
    pupil = object_from_bm('pupil', bm); paint(pupil, {'black': PAL['black']}, lambda c_, n_, i_: 'black'); pieces.append(pupil)
    # back spots: irregular dark plates seated on the skin
    ebm = evaluated_bm(body); tree = BVHTree.FromBMesh(ebm)
    bm = bmesh.new()
    SP = [(0.045, -0.03, 0.024, 0), (0.105, 0.03, 0.017, 1), (0.05, 0.075, 0.027, 2), (0.10, 0.135, 0.017, 3),
          (0.04, 0.165, 0.015, 4), (0.035, -0.175, 0.012, 5), (0.205, 0.02, 0.016, 6), (0.298, 0.06, 0.009, 7)]
    for x, y, r, sd in SP:
        loc, nrm, _, _ = tree.ray_cast(V(x, y, 0.6), V(0, 0, -1))
        if loc is None:
            say('spot missed', x, y); continue
        t1 = nrm.cross(V(0, 1, 0)).normalized(); t2 = nrm.cross(t1)
        rr = [r * (0.75 + 0.25 * ((sd * 7 + i * 5) % 4) / 3) for i in range(6)]
        off = [t1 * (rr[i] * math.cos(math.radians(60 * i + 15 * sd))) + t2 * (rr[i] * math.sin(math.radians(60 * i + 15 * sd))) for i in range(6)]
        top = [loc + nrm * 0.003 + o for o in off]
        bot = [loc - nrm * 0.004 + o * 0.9 for o in off]
        prism(bm, bot, top)
    spots = object_from_bm('spots', bm); paint(spots, {'spot': PAL['spot']}, lambda c_, n_, i_: 'spot'); pieces.append(spots)
    # front hands: three splayed fingers with cream pads
    bm = bmesh.new(); padf = set()
    h0 = V(0.16, -0.14, 0.009)
    for ang, L in ((-38, 0.036), (-5, 0.042), (30, 0.036)):
        dd = V(math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0)
        _, pf = digit(bm, h0 + dd * 0.010 + V(0, 0.008, 0), h0 + dd * (0.012 + L), 0.008, 0.0055, 0.0075, 0.0055)
        padf |= set(pf)
    bm.faces.ensure_lookup_table(); pads_i = {f.index for f in padf}
    hands = object_from_bm('hand_toes', bm)
    paint(hands, {'skin': PAL['skin'], 'belly': PAL['belly']}, lambda c_, n_, i_: 'belly' if i_ in pads_i else 'skin'); pieces.append(hands)
    # hind feet: four long toes fanning from the foot end, cream pads, dark webbing between them
    bm = bmesh.new(); padf = set(); webf = set()
    f0 = V(J['toes'][0], J['toes'][1] + 0.004, 0.007)
    tips = []
    for ang, L, ox in ((-24, 0.050, -0.026), (-6, 0.062, -0.009), (12, 0.060, 0.009), (30, 0.048, 0.026)):
        dd = V(math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0)
        root = f0 + V(ox, 0, 0)
        _, pf = digit(bm, root, root + dd * L, 0.0075, 0.0055, 0.0065, 0.005)
        padf |= set(pf); tips.append(root + dd * (L * 0.78))
    web_top = [f0 + V(-0.03, 0.002, -0.001)] + [t_ + V(0, 0, -0.002) for t_ in tips] + [f0 + V(0.03, 0.002, -0.001)]
    web_bot = [q + V(0, 0, -0.005) for q in web_top]
    webf |= set(prism(bm, web_bot, web_top))
    bm.faces.ensure_lookup_table(); pads_i = {f.index for f in padf}; web_i = {f.index for f in webf}
    feet = object_from_bm('foot_toes', bm)
    paint(feet, {'skin': PAL['skin'], 'belly': PAL['belly'], 'spot': PAL['spot']},
          lambda c_, n_, i_: 'belly' if i_ in pads_i else ('spot' if i_ in web_i else 'skin')); pieces.append(feet)
    return pieces


def _only(ob, idx, name):
    for g in ob.vertex_groups:
        g.remove([idx])
    (ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)).add([idx], 1.0, 'REPLACE')


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hip'], J['spine'], None),
        ('chest', J['spine'], J['neck'], 'hips', True),
        ('head', J['neck'], J['snout'], 'chest', True),
        ('jaw', J['jaw0'], J['jaw1'], 'head'),
        ('throat', J['throat0'], J['throat1'], 'head'),
        ('eye.L', J['eye'], J['eyetop'], 'head'),
        ('arm.L', J['shoulder'], J['elbow'], 'chest'),
        ('forearm.L', J['elbow'], J['wrist'], 'arm.L', True),
        ('hand.L', J['wrist'], J['fingers'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
        ('foot.L', J['ankle'], J['ball'], 'shin.L', True),
        ('toes.L', J['ball'], J['toes'], 'foot.L', True),
    ], roll='auto')
    skin(body, rig)
    # the head splits cleanly at the mouth line: jaw below, head above; eye bulges ride their eye bones;
    # the throat patch under the chin is its own bone (the pulse)
    for v in body.data.vertices:
        c = body.matrix_world @ v.co
        x, y, z = abs(c.x), c.y, c.z
        side = 'L' if c.x >= 0 else 'R'
        if z > 0.222 and x > 0.06 and -0.19 < y < -0.08:
            _only(body, v.index, 'eye.' + side)
        elif y < -0.062 and z > 0.03 and not (x > 0.11 and z < 0.09):
            zl, g = _lip(y)
            if -0.19 < y < -0.08 and z < 0.075 and x < 0.1:
                _only(body, v.index, 'throat')
            elif z < zl - g + 0.001:
                _only(body, v.index, 'jaw')
            else:
                _only(body, v.index, 'head')
    # the foot end under the toe fan rides the toes bone alone, and so does the fan (rigid: no web fold-overs)
    for v in body.data.vertices:
        c = body.matrix_world @ v.co
        if (V(abs(c.x), c.y, c.z) - V(J['toes'])).length < 0.03:
            _only(body, v.index, 'toes.' + ('L' if c.x >= 0 else 'R'))
    for p in pieces:
        bind(p, rig, body=body)
        if p.name.endswith('foot_toes'):
            for v in p.data.vertices:
                _only(p, v.index, 'toes.' + ('L' if (p.matrix_world @ v.co).x >= 0 else 'R'))
    legs = lambda t, s_, fa: {'thigh.L': (0, 0, t), 'thigh.R': (0, 0, -t), 'shin.L': (0, 0, s_), 'shin.R': (0, 0, -s_),
                              'foot.L': (fa, 0, 0), 'foot.R': (fa, 0, 0)}
    clip(rig, 'idle', {1: {}, 8: {'chest': (1.5, 0, 0)}, 16: {}, 24: {'chest': (1.5, 0, 0)}, 32: {}, 38: {}, 40: {}, 42: {}, 48: {}},
         loc={1: {}, 8: {'throat': (0, 0, -0.007)}, 16: {}, 24: {'throat': (0, 0, -0.007)}, 32: {},
              38: {}, 40: {'eye.L': (0, -0.012, 0), 'eye.R': (0, -0.012, 0)}, 42: {}, 48: {}})
    clip(rig, 'move', {1: {}, 5: {'chest': (-6, 0, 0), 'head': (-4, 0, 0)},
                       9: dict(legs(22, -22, 0), chest=(8, 0, 0), head=(4, 0, 0)),
                       13: dict(legs(28, -28, 0), chest=(6, 0, 0)),
                       18: dict(legs(8, -8, 0), chest=(-4, 0, 0)), 24: {}},
         loc={1: {}, 5: {}, 9: {'hips': (0, 0.03, 0.05)}, 13: {'hips': (0, 0.045, 0.075)}, 18: {'hips': (0, 0.015, 0.01)}, 24: {}})
    clip(rig, 'attack', {1: {}, 6: {'chest': (-5, 0, 0), 'head': (-4, 0, 0)},
                         10: {'chest': (6, 0, 0), 'head': (10, 0, 0), 'jaw': (-28, 0, 0)},
                         14: {'chest': (4, 0, 0), 'head': (6, 0, 0), 'jaw': (-32, 0, 0)},
                         18: {'head': (-3, 0, 0), 'jaw': (0, 0, 0)}, 24: {}},
         loc={1: {}, 6: {'hips': (0, -0.01, 0)}, 10: {'hips': (0, 0.04, 0.01)}, 14: {'hips': (0, 0.04, 0.01)}, 18: {}, 24: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
