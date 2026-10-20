"""Stylised low-poly crocodile (r20), box-modelled in four stages (experiments/boxmodel/BRIEF.md).

One chain of 8-sided half rings: long flat snout -> skull with raised eye turrets -> broad flat body -> a thick
tail that tapers to a point. Four sprawling legs (out sideways, elbow / knee, then down to a flat splayed foot)
extruded from one lower-flank quad each. Scute rows, teeth, claws and eyes are stage-3 pieces.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit'))
sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from boxlib5 import *

META = dict(creature='crocodile', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
# chain rings: (y, z, half width, top half height, bottom half height)
CH = [(-1.00, 0.140, 0.060, 0.028, 0.035), (-0.93, 0.145, 0.082, 0.040, 0.045), (-0.76, 0.150, 0.080, 0.042, 0.050),
      (-0.58, 0.160, 0.100, 0.052, 0.058), (-0.46, 0.175, 0.135, 0.068, 0.062), (-0.35, 0.180, 0.150, 0.072, 0.072),
      (-0.25, 0.185, 0.140, 0.075, 0.072), (-0.13, 0.195, 0.175, 0.085, 0.085), (-0.01, 0.200, 0.195, 0.090, 0.092),
      (0.13, 0.200, 0.215, 0.090, 0.100), (0.27, 0.200, 0.215, 0.090, 0.100), (0.40, 0.195, 0.185, 0.090, 0.092),
      (0.52, 0.190, 0.155, 0.085, 0.082), (0.66, 0.180, 0.125, 0.080, 0.070), (0.83, 0.165, 0.095, 0.070, 0.056),
      (1.01, 0.150, 0.070, 0.058, 0.045), (1.19, 0.135, 0.048, 0.044, 0.034), (1.35, 0.120, 0.028, 0.030, 0.024),
      (1.47, 0.110, 0.010, 0.014, 0.012)]
R_FORE, R_HIND = 7, 11                  # one lower-flank quad each (rings i, i+1; flank -> keel corner)
FORE = [((0.25, -0.08, 0.170), 0.058, 0.058), ((0.32, -0.08, 0.130), 0.052, 0.052),
        ((0.33, -0.10, 0.070), 0.044, 0.046), ((0.335, -0.11, 0.035), 0.040, 0.044, (0, 0, -1)),
        ((0.34, -0.13, 0.0), 0.060, 0.072, (0, 0, -1))]
HIND = [((0.27, 0.47, 0.175), 0.070, 0.074), ((0.35, 0.45, 0.135), 0.058, 0.058),
        ((0.36, 0.48, 0.070), 0.048, 0.050), ((0.365, 0.48, 0.035), 0.044, 0.048, (0, 0, -1)),
        ((0.37, 0.45, 0.0), 0.066, 0.084, (0, 0, -1))]
EYE_TURRET = (4, (0.110, -0.415, 0.262))  # ring, tip: a low pyramid on the skull for each eye
# ================================================================ end PARAMS

J = dict(hip=(0, 0.40, 0.20), spine=(0, 0.05, 0.20), chest=(0, -0.20, 0.19), head=(0, -0.36, 0.18),
         snout=(0, -1.00, 0.14), tail0=(0, 0.52, 0.19), tail1=(0, 0.80, 0.165), tail2=(0, 1.10, 0.14),
         tail3=(0, 1.47, 0.11),
         shoulderL=(0.16, -0.08, 0.17), elbowL=(0.36, -0.08, 0.14), wristL=(0.385, -0.11, 0.03),
         footL=(0.39, -0.22, 0.01),
         hipL=(0.15, 0.46, 0.17), kneeL=(0.39, 0.45, 0.14), ankleL=(0.415, 0.48, 0.03), hfootL=(0.42, 0.36, 0.01))

SX = [1.30] * 4 + [1.40] * 10 + [1.25] * 5      # stylised chunk: width factor per ring
SZ = [1.20] * 4 + [1.30] * 10 + [1.20] * 5      # height factor per ring
LEG_DX = 0.07                                   # legs out with the wider body
DROP = 0.045                                   # the whole body lower: belly near the ground
CHAIN = [hring((y, z + 0.12 * (sz - 1) - DROP), (1, 0), w * sx, ht * sz, hb * sz)
         for (y, z, w, ht, hb), sx, sz in zip(CH, SX, SZ)]
LEGS = {}


def P(i, j):
    return Vector(CHAIN[i][j])


def secs(tab):
    return [dict(c=(t[0][0] + LEG_DX, t[0][1], t[0][2] + (0.012 - DROP) * (t[0][2] > 0.05) - 0.4 * DROP * (0.0 < t[0][2] <= 0.05)), w=t[1], d=t[2], dir=(t[3] if len(t) > 3 else None)) for t in tab]


def stage1(k):
    bm = bmesh.new()
    R = build_chain(bm, CHAIN)
    i, tip = EYE_TURRET
    spike(bm, R[i][0], R[i][1], R[i + 1][1], R[i + 1][0], tip) if False else \
        spike(bm, R[i][1], R[i][2], R[i + 1][2], R[i + 1][1], tip)
    for name, i0, tab in (('fore', R_FORE, FORE), ('hind', R_HIND, HIND)):
        LEGS[name] = freeze(build_limb(bm, R, i0, 1, 2, secs(tab)))
    recalc_normals(bm)
    return object_from_bm('body', bm)


MOUTH_T = 0.40          # lip line: fraction from the flank vertex to the jaw corner


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'partial_loop', 'mouth line along the snout side, ends on the cheek behind the jaw hinge'):
        e0 = edge_near(bm, (P(0, 2) + P(0, 3)) / 2)
        e1 = edge_near(bm, (P(6, 2) + P(6, 3)) / 2)
        mouth = partial_loop(bm, e0, e1, t=MOUTH_T, near=vert_near(bm, P(0, 2)))
    for leg, a, t, why in (('fore', 0, 0.55, 'elbow: a second loop at the bend'),
                           ('fore', 1, 0.5, 'forearm: loop between elbow and wrist'),
                           ('hind', 0, 0.55, 'knee: a second loop at the bend'),
                           ('hind', 1, 0.5, 'shin: loop between knee and ankle')):
        with k.topo(bm, 'loop', why):
            limb_loop(bm, LEGS[leg], a, t)
    for i, why in ((5, 'neck: a loop behind the jaw hinge for the head lift'),
                   (13, 'tail root: a loop for the sweep'), (15, 'mid tail: a loop for the sweep')):
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, (P(i, 0) + P(i + 1, 0)) / 2), t=0.5, near=vert_near(bm, P(i, 0)))
    for v in mouth:                                     # the lip line: a groove
        if v.co.x > 0.01:
            v.co.x -= 0.010
    for i in (1, 2, 3):                                  # flat snout top
        for j in (0, 1):
            vert_near(bm, P(i, j)).co.z -= 0.006
    commit(body, bm)


PALETTE = {'olive': '#7d8f46', 'dark': '#55652f', 'belly': '#d9c98c', 'tooth': '#efe8d0',
           'iris': '#d9b23a', 'black': '#23211d'}


def pal(*keys):
    return {q: PALETTE[q] for q in keys}


def body_rule(c, n, i):
    x, y, z = c
    if n.z < -0.35 or (z < 0.10 and x < 0.17 and n.z < 0.2 and y < 0.9):
        return 'belly'
    if n.z > 0.55 and y > -0.45 and int((y + 0.45) / 0.16) % 2 == 0:
        return 'dark'                                   # cross bands on the back and tail
    return 'olive'


def scutes():
    """Two rows of low faceted scutes down the back that merge into one tail crest (mirrored piece)."""
    tree = TREE[0]
    bm = bmesh.new()
    for y in [-0.20 + 0.12 * q for q in range(16)]:
        rows = (0.045, 0.105) if y < 0.55 else (0.030,)
        for x in rows:
            if y > 1.25:
                continue
            loc, n = on_skin(tree, (x, y, 0.2), (0, 0, 1))
            s = 1.0 - 0.45 * max(0.0, (y - 0.5) / 0.8)
            cone(bm, loc, (0, 0.25, 1), 0.026 * s, 0.050 * s, sides=4, bury=0.4, flat=0.7)
    return mk('scutes', bm, pal('dark'), lambda c, n, i: 'dark')


def claws():
    bm = bmesh.new()
    for leg in ('fore', 'hind'):
        sole = LEGS[leg][-1]
        c0 = sum(sole.values(), Vector()) / len(sole)
        front = min(v.y for v in sole.values())
        for dx in (-0.032, 0.0, 0.032):
            base = Vector((c0.x + dx * 1.2, front + 0.012, 0.016))
            cone(bm, base, (dx * 4, -1, -0.25), 0.012, 0.055, sides=3, bury=0.35, bend=(0, 0, -1))
    return mk('claws', bm, pal('black'), lambda c, n, i: 'black')


def teeth():
    import parts as P_
    obs = []
    for side in (1, -1):
        a = P(1, 2).lerp(P(1, 3), MOUTH_T); b = P(5, 2).lerp(P(5, 3), MOUTH_T)
        st = (side * (a.x - 0.018), a.y + 0.03, a.z - 0.004); en = (side * (b.x - 0.025), b.y - 0.02, b.z - 0.004)
        obs.append(P_.tooth_row(st, en, out=(side, 0, 0), up=(0, 0, -1), n=7, height=0.022, bulge=0.05, gum=False,
                                name='teeth' + ('L' if side > 0 else 'R'), mats={'tooth': 'tooth'},
                                colours={'tooth': PALETTE['tooth']}))
    return obs


TREE = []


def stage3(k, body):
    paint(body, pal('olive', 'dark', 'belly'), body_rule)
    TREE[:] = [body_tree(body)]
    eyes = eye_pair(TREE[0], (0.11, -0.43, 0.25), (0.55, -0.35, 0.75), 0.024,
                    mats={'eye_rim': 'olive', 'eye_socket': 'black', 'iris': 'iris', 'pupil': 'black',
                          'glint': 'tooth', 'lid': 'olive'}, colours={'iris': PALETTE['iris']},
                    pupil='slit', brow_wedge=False)
    return [scutes(), claws()] + teeth() + eyes


def bones():
    return [('hips', J['hip'], J['spine'], None),
            ('chest', J['spine'], J['chest'], 'hips', True),
            ('neck', J['chest'], J['head'], 'chest', True),
            ('head', J['head'], J['snout'], 'neck', True),
            ('tail0', J['tail0'], J['tail1'], 'hips'),
            ('tail1', J['tail1'], J['tail2'], 'tail0', True),
            ('tail2', J['tail2'], J['tail3'], 'tail1', True),
            ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
            ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
            ('foot.L', J['wristL'], J['footL'], 'forearm.L', True),
            ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
            ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
            ('hfoot.L', J['ankleL'], J['hfootL'], 'shin.L', True)]


CB = ('hips', 'chest', 'neck', 'head', 'tail0', 'tail1', 'tail2')
SWING = 2         # bone-local axis that swings a sprawled upper limb fore / aft (0 X, 1 Y, 2 Z)


def sw(deg):
    r = [0, 0, 0]; r[SWING] = deg
    return tuple(r)


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_eye') or 'teeth' in p.name:
            bind(p, rig, bone='head')
        elif 'claws' in p.name:
            bind(p, rig)
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'tail0': (0, 0, 6), 'tail1': (0, 0, 8), 'tail2': (0, 0, 10), 'head': (-3, 0, 0)},
                       24: {'head': (1, 0, 0)},
                       36: {'tail0': (0, 0, -6), 'tail1': (0, 0, -8), 'tail2': (0, 0, -10), 'head': (-3, 0, 0)}, 48: {}})

    def gait(s):              # s = +1 / -1: diagonal pair A (fore.L + hind.R) forward, body bends toward it
        a, b = 22 * s, -22 * s
        return {'upperarm.L': sw(a), 'thigh.R': sw(-a), 'upperarm.R': sw(-b), 'thigh.L': sw(b),
                'chest': (0, 0, 6 * s), 'hips': (0, 0, -4 * s), 'neck': (0, 0, -5 * s),
                'tail0': (0, 0, 10 * s), 'tail1': (0, 0, 12 * s), 'tail2': (0, 0, 10 * s)}
    lift = lambda L, R: {'forearm.L': (0, 0, 0), **({} if not L else {}), **({} if not R else {})}
    clip(rig, 'move', {1: gait(1), 9: gait(-1), 17: gait(1), 25: gait(-1), 33: gait(1)})
    clip(rig, 'attack', {1: {}, 8: {'neck': (-14, 0, 0), 'head': (-8, 0, 0), 'chest': (-4, 0, 0), 'tail0': (0, 0, 8)},
                         14: {'neck': (6, 0, 0), 'head': (8, 0, 0), 'chest': (2, 0, 0), 'tail0': (0, 0, -12),
                              'tail1': (0, 0, -10)},
                         22: {'neck': (2, 0, 0), 'head': (3, 0, 0), 'tail0': (0, 0, -4)}, 30: {}},
         loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.03, 0)}, 14: {'hips': (0, -0.06, 0)}, 30: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
