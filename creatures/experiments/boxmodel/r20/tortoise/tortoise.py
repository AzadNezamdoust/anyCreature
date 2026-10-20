"""Stylised low-poly tortoise (r20), box-modelled in four stages (experiments/boxmodel/BRIEF.md).

One chain of 12-sided half rings (7 verts): blunt head -> short neck -> a tall domed shell whose rim overhangs
the body (the lower ring vertices pulled in) -> stub tail. Four elephant-column legs extruded from one underside
quad each, under the rim. Raised scute plates, toenails and eyes are stage-3 pieces.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit'))
sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from boxlib5 import *

META = dict(creature='tortoise', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
# chain rings: (y, z, half width, top, bottom, kind) kind 'h' head/neck, 's' shell, 't' tail
CH = [(-0.80, 0.360, 0.060, 0.048, 0.046, 'h'), (-0.75, 0.365, 0.095, 0.082, 0.074, 'h'),
      (-0.64, 0.360, 0.112, 0.098, 0.084, 'h'), (-0.54, 0.315, 0.080, 0.072, 0.070, 'h'),
      (-0.46, 0.270, 0.092, 0.084, 0.084, 'h'),
      (-0.40, 0.220, 0.250, 0.190, 0.090, 's'), (-0.32, 0.220, 0.320, 0.290, 0.120, 's'),
      (-0.15, 0.220, 0.360, 0.330, 0.120, 's'), (0.05, 0.220, 0.370, 0.340, 0.120, 's'),
      (0.22, 0.220, 0.350, 0.310, 0.120, 's'), (0.36, 0.220, 0.300, 0.250, 0.110, 's'),
      (0.43, 0.220, 0.220, 0.160, 0.090, 's'),
      (0.50, 0.180, 0.040, 0.030, 0.030, 't'), (0.56, 0.150, 0.014, 0.012, 0.012, 't')]
SHELL_SQ = (1, 1, 1, 1, 0.80, 0.62, 1)     # rim overhang: the lower ring vertices pulled in under the shell
R_FORE, R_HIND, LEG_J = 6, 9, 4            # one underside quad each (rings i, i+1; ring vertices 4 -> 5)
FORE = [((0.235, -0.26, 0.105), 0.066, 0.068), ((0.245, -0.27, 0.045), 0.072, 0.074, (0, 0, -1)),
        ((0.25, -0.275, 0.0), 0.080, 0.084, (0, 0, -1))]
HIND = [((0.23, 0.29, 0.105), 0.070, 0.072), ((0.24, 0.30, 0.045), 0.076, 0.078, (0, 0, -1)),
        ((0.245, 0.30, 0.0), 0.084, 0.088, (0, 0, -1))]
# ================================================================ end PARAMS

J = dict(hip=(0, 0.25, 0.25), spine=(0, -0.05, 0.27), chest=(0, -0.38, 0.25), neck=(0, -0.45, 0.255),
         head=(0, -0.60, 0.30), snout=(0, -0.80, 0.30), tail0=(0, 0.45, 0.20), tail1=(0, 0.57, 0.15),
         shoulderL=(0.21, -0.24, 0.16), elbowL=(0.27, -0.27, 0.10), footL=(0.30, -0.30, 0.0),
         hipL=(0.21, 0.28, 0.16), kneeL=(0.26, 0.30, 0.10), hfootL=(0.29, 0.31, 0.0))

LIFT = 0.05                                 # the whole body up: room for real legs under the rim
DOME = 1.22                                 # shell top half-height factor: a tall dome, not a loaf
CHAIN = [hring((y, z + LIFT), (1, 0), w, ht * (DOME if kind == 's' else 1.0), hb, shape=SHAPE7, sq=SHELL_SQ if kind == 's' else None)
         for y, z, w, ht, hb, kind in CH]
LEGS = {}


def P(i, j):
    return Vector(CHAIN[i][j])


def secs(tab):
    return [dict(c=t[0], w=t[1], d=t[2], dir=(t[3] if len(t) > 3 else None)) for t in tab]


def stage1(k):
    bm = bmesh.new()
    R = build_chain(bm, CHAIN)
    for name, i0, tab in (('fore', R_FORE, FORE), ('hind', R_HIND, HIND)):
        LEGS[name] = freeze(build_limb(bm, R, i0, 1, LEG_J, secs(tab)))
    recalc_normals(bm)
    return object_from_bm('body', bm)


MOUTH_T = 0.45


def stage2(k, body):
    bm = edit(body)
    mouth = []                                          # (r08: the mouth partial loop made 3 % slivers; dropped)
    # (r09: the knee loops made needle triangles on the short inner leg band; the legs bend at the root)
    tl = [vert_near(bm, P(12, j)) for j in range(7)]    # tail root ring 1.8x: no needles from the shell back
    c = sum((v.co for v in tl), Vector()) / 7
    for v in tl:
        v.co = Vector((v.co.x * 1.8, c.y, c.z + (v.co.z - c.z) * 1.8))
    with k.topo(bm, 'loop', 'neck: a loop mid neck for the head reach'):
        loopcut(bm, edge_near(bm, (P(3, 0) + P(4, 0)) / 2), t=0.5, near=vert_near(bm, P(3, 0)))
    for v in mouth:
        if v.co.x > 0.01:
            v.co.x -= 0.008
    for j in (0, 1):                                    # the beak: the nose ridge drops a little (a hook)
        vert_near(bm, P(0, j)).co.z -= 0.012
    commit(body, bm)


PALETTE = {'shell': '#7c5c36', 'scute': '#b88d4a', 'skin': '#8f987a', 'plastron': '#dcc893', 'nail': '#3b342c'}
SHELL_Y = (-0.415, 0.445)
RIM_Z = 0.262


def pal(*keys):
    return {q: PALETTE[q] for q in keys}


def body_rule(c, n, i):
    x, y, z = c
    if SHELL_Y[0] < y < SHELL_Y[1] and (y > -0.38 or abs(x) > 0.10 or z > 0.40):
        if z >= RIM_Z:
            return 'shell'
        if n.z < -0.5 and z > 0.12:
            return 'plastron'
    if SHELL_Y[0] < y < SHELL_Y[1] and z >= RIM_Z + 0.05:
        return 'shell'
    if -0.47 < y < -0.38 and math.hypot(x, z - 0.30) > 0.13 and z > 0.17:
        return 'shell'                                  # r11: the front annulus round the neck opening
    if 0.43 < y < 0.52 and z >= RIM_Z and abs(x) > 0.05:
        return 'shell'                                  # r11: the shell back over the tail
    if y < -0.80 and z > 0.37:
        return 'nail'                                   # beak tip
    return 'skin'


def plates(tree, mirror):
    """Raised hexagonal scute knobs on the dome: the spine row (unmirrored) or the side rows (mirrored)."""
    bm = bmesh.new()
    if mirror:
        spots = [(0.19, y) for y in (-0.22, -0.02, 0.18)] + [(0.30, y) for y in (-0.26, -0.10, 0.06, 0.22)]
    else:
        spots = [(0.0, y) for y in (-0.24, -0.04, 0.16, 0.33)]
    for x, y in spots:
        loc, n = on_skin(tree, (x, y, 0.4), (x * 2.2, 0, 1))
        r = 0.098 if x < 0.25 else 0.078
        cone(bm, loc, n, r, 0.036, sides=6, bury=0.55, taper=0.30)
    return mk('plates_side' if mirror else 'plates_spine', bm, pal('scute'), lambda c, n_, i: 'scute', mirror=mirror)


def nails():
    bm = bmesh.new()
    for leg in ('fore', 'hind'):
        sole = LEGS[leg][-1]
        c0 = sum(sole.values(), Vector()) / len(sole)
        front = min(v.y for v in sole.values())
        for dx in (-0.04, 0.0, 0.04):
            cone(bm, (c0.x + dx, front + 0.010, 0.022), (dx * 3, -1, -0.5), 0.016, 0.040, sides=4, bury=0.4)
    return mk('nails', bm, pal('nail'), lambda c, n_, i: 'nail')


def stage3(k, body):
    paint(body, pal('shell', 'skin', 'plastron', 'nail'), body_rule)
    tree = body_tree(body)
    eyes = eye_pair(tree, (0.10, -0.70, 0.40), (1, -0.4, 0.4), 0.018,
                    mats={'eye_rim': 'skin', 'eye_socket': 'nail', 'iris': 'nail', 'pupil': 'nail',
                          'glint': 'plastron', 'lid': 'skin'}, brow_wedge=False, expression='neutral')
    return [plates(tree, True), plates(tree, False), nails()] + eyes


def bones():
    return [('hips', (0, 0.30, 0.30), (0, -0.05, 0.32), None),
            ('chest', (0, -0.05, 0.32), (0, -0.40, 0.30), 'hips', True),
            ('neck', (0, -0.40, 0.30), (0, -0.60, 0.36), 'chest', True),
            ('head', (0, -0.60, 0.36), (0, -0.84, 0.37), 'neck', True),
            ('tail', (0, 0.45, 0.25), (0, 0.58, 0.19), 'hips'),
            ('upperarm.L', (0.20, -0.25, 0.16), FORE[0][0], 'chest'),
            ('forearm.L', FORE[0][0], (FORE[2][0][0], FORE[2][0][1] - 0.06, 0.0), 'upperarm.L', True),
            ('thigh.L', (0.20, 0.28, 0.16), HIND[0][0], 'hips'),
            ('shin.L', HIND[0][0], (HIND[2][0][0], HIND[2][0][1] - 0.05, 0.0), 'thigh.L', True)]


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_eye'):
            bind(p, rig, bone='head')
        elif 'plates' in p.name:
            bind(p, rig, body=body)
        else:
            bind(p, rig)
    clip(rig, 'idle', {1: {}, 12: {'neck': (-6, 0, 4), 'head': (4, 0, 3)}, 24: {'neck': (-2, 0, 0), 'head': (-3, 0, 0)},
                       36: {'neck': (-6, 0, -4), 'head': (4, 0, -3)}, 48: {}})

    def step(s):
        return {'upperarm.L': (-14 * s, 0, 0), 'thigh.R': (-14 * s, 0, 0), 'upperarm.R': (14 * s, 0, 0),
                'thigh.L': (14 * s, 0, 0), 'chest': (0, 2 * s, 0), 'neck': (0, 0, 3 * s), 'tail': (0, 0, -8 * s)}
    lift = lambda s: {**step(0), ('forearm.L' if s > 0 else 'forearm.R'): (12, 0, 0),
                      ('shin.R' if s > 0 else 'shin.L'): (12, 0, 0)}
    clip(rig, 'move', {1: step(1), 9: lift(-1), 17: step(-1), 25: lift(1), 33: step(1)})
    clip(rig, 'attack', {1: {}, 8: {'neck': (-12, 0, 0), 'head': (-8, 0, 0)},
                         13: {'neck': (14, 0, 0), 'head': (10, 0, 0), 'chest': (3, 0, 0)},
                         20: {'neck': (6, 0, 0), 'head': (2, 0, 0)}, 28: {}},
         loc={1: {'hips': (0, 0, 0)}, 13: {'hips': (0, -0.03, 0)}, 28: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
