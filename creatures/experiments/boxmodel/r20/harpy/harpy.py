"""Harpy (r20): a woman-bird. Human face and bust under a wild dark crest, arms that ARE wings (a fan of slate
feathers hanging from each arm), feathered thighs, reverse-kneed scaly bird legs on taloned feet, a tail fan.
One vertical chain of 5-vertex half rings crown -> crotch; arms and legs extruded from two side quads."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit')); sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from r20lib import *
import parts as P

META = dict(creature='harpy', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
TORSO = [  # (y, z), half width, front depth, back depth
    ((0.020, 1.560), 0.060, 0.050, 0.050),    # 0 crown
    ((0.000, 1.505), 0.098, 0.100, 0.105),    # 1 brow
    ((-0.005, 1.425), 0.095, 0.105, 0.100),   # 2 cheek
    ((0.005, 1.350), 0.072, 0.085, 0.080),    # 3 jaw
    ((0.020, 1.285), 0.055, 0.060, 0.060),    # 4 neck
    ((0.020, 1.205), 0.185, 0.090, 0.090),    # 5 shoulders (arm 5-6)
    ((0.010, 1.085), 0.165, 0.120, 0.090),    # 6 bust
    ((0.010, 0.985), 0.135, 0.095, 0.085),    # 7 ribs
    ((0.015, 0.900), 0.115, 0.080, 0.080),    # 8 waist
    ((0.020, 0.800), 0.160, 0.100, 0.115),    # 9 hips (leg 9-10)
    ((0.030, 0.700), 0.100, 0.070, 0.080),    # 10 crotch
]
HEAD_S = 1.22                      # head rings 0-3 section scale (a bigger, more expressive head)
ARM_RING, LEG_RING = 5, 9
ARM = [  # c, half sizes, [dir]
    ((0.235, 0.020, 1.160), 0.050, 0.065, (1, 0, -0.35)),
    ((0.360, 0.025, 1.050), 0.048, 0.055),
    ((0.480, 0.030, 0.945), 0.040, 0.045),
    ((0.600, 0.030, 0.850), 0.040, 0.042),
    ((0.700, 0.020, 0.775), 0.030, 0.032),
    ((0.770, 0.000, 0.725), 0.032, 0.026),
]
LEG = [
    ((0.125, 0.000, 0.640), 0.095, 0.105),    # feathered thigh
    ((0.135, -0.090, 0.500), 0.060, 0.065),   # knee (forward)
    ((0.135, 0.020, 0.360), 0.040, 0.045),    # shin
    ((0.135, 0.130, 0.240), 0.034, 0.036),    # ankle (backward: the bird joint)
    ((0.135, 0.080, 0.130), 0.028, 0.030),    # tarsus
    ((0.135, 0.040, 0.075), 0.026, 0.028),    # tarsus end
]
FOOT = dict(toe_length=0.10)
FEATHERS = 7                       # primaries per wing, shoulder -> hand
FEATHER_LEN = (0.20, 0.42)         # shoulder .. hand feather length
FEATHER_T = (0.0, 0.25, 0.5, 0.75, 1.0)          # stations along a feather
FEATHER_W = (0.6, 1.0, 1.0, 0.8, 0.3)            # width at each station, x feather width
FEATHER_THICK = 0.022
FEATHER_WIDTH = (0.030, 0.006)     # feather half width at the shoulder, + toward the hand
FEATHER_SPLAY = (0.15, 0.35)        # outward lean of a feather at the shoulder, + extra toward the hand
CREST = [((0.03, 0.06, 1.55), (0.15, 0.6, 0.6), 0.18), ((0.06, 0.09, 1.50), (0.45, 0.6, 0.35), 0.16),
         ((0.0, 0.10, 1.47), (0.0, 0.8, 0.2), 0.20)]
TAIL = [(0.0, 0.32, 0.25), (0.35, 0.30, 0.22)]     # x lean, length, ...
EYE = ((0.055, -0.115, 1.455), 0.026)
PALETTE = {'skin': '#e2b48d', 'feather': '#56698c', 'tip': '#c9d3e1', 'hair': '#3d2f4c', 'scale': '#d6a238',
           'claw': '#2a2228', 'eye': '#e94a3a', 'lip': '#a84a50'}
# ================================================================ end PARAMS

J = dict(hip=(0, 0.02, 0.76), spine=(0, 0.015, 0.98), chest=(0, 0.02, 1.22), neck=(0, 0.02, 1.33),
         crown=(0, 0.0, 1.56), shoulderL=(0.17, 0.02, 1.19), elbowL=(0.48, 0.03, 0.945), wristL=(0.70, 0.02, 0.775),
         handL=(0.79, 0.0, 0.71), hipL=(0.11, 0.02, 0.72), kneeL=(0.135, -0.09, 0.50), ankleL=(0.135, 0.13, 0.24),
         footL=(0.135, 0.04, 0.06))
LE = {}
ARMP = []


def S(tab):
    out = []
    for t in tab:
        s = dict(c=t[0], w=t[1], d=t[2], e=2.6)
        if len(t) > 3:
            s['dir'] = t[3]
        out.append(s)
    return out


def stage1(k):
    bm = bmesh.new()
    R = chain(bm, [dict(c=c, w=w * f, hu=hu * f, hd=hd * f) for i, (c, w, hu, hd) in enumerate(TORSO)
                   for f in [HEAD_S if i <= 3 else 1.0]], front=True)
    for nm, r0, tab in (('arm', ARM_RING, ARM), ('leg', LEG_RING, LEG)):
        rs = limb(bm, [chain_face(R, r0, 1), chain_face(R, r0, 2)], S(tab), even=True)
        LE[nm] = [limb_edge(rs, a) for a in range(len(rs) - 1)]
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    for nm, a, t, why in (('arm', 2, 0.5, 'elbow: a loop past the bend'), ('leg', 1, 0.5, 'knee: a loop below the bend'),
                          ('leg', 3, 0.5, 'ankle: a loop below the bird joint')):
        mid, near = LE[nm][a]
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, mid), t=t, near=vert_near(bm, near))
    for v in bm.verts:                      # a small nose ridge and chin
        if abs(v.co.x) < 1e-4 and v.co.y < -0.09 and 1.40 < v.co.z < 1.46:
            v.co.y -= 0.015
    commit(body, bm)


def body_rule(c, n, i):
    x, y, z = c
    ax = abs(x)
    if z > 1.30:
        if n.y < -0.35 and z < 1.50:
            return 'skin'
        return 'hair'
    if ax > 0.2 and z > 0.7:
        return 'feather'
    if z < 0.42:
        return 'scale'
    if z < 0.96 or ax > 0.16:
        return 'feather'
    return 'skin'


def feather(name, root, tip, w):
    pts = [tuple(root[i] + (tip[i] - root[i]) * t for i in range(3)) for t in FEATHER_T]
    o = sweep(name, pts, [(w * f, FEATHER_THICK) for f in FEATHER_W], up=(0, 1, 0), sides=4,
              keys=['feather'] * (len(pts) - 3) + ['tip', 'tip'], mirror=True, point=True)
    return paint_keys(o, PALETTE)


def stage3(k, body):
    paint(body, PALETTE, body_rule)
    tree = body_tree(body)
    pieces = []
    a0, a1 = Vector(ARM[0][0]), Vector(ARM[-1][0])
    for i in range(FEATHERS):
        t = 0.1 + 0.9 * i / (FEATHERS - 1)
        p = a0.lerp(a1, t)
        L = FEATHER_LEN[0] + (FEATHER_LEN[1] - FEATHER_LEN[0]) * t
        root = (p.x, p.y + 0.005, p.z + 0.005)
        dirv = Vector((FEATHER_SPLAY[0] + FEATHER_SPLAY[1] * t, 0.18, -1.0)).normalized()
        tip = tuple(Vector(root) + dirv * L)
        pieces.append(feather(f'wing{i}', root, tip, FEATHER_WIDTH[0] + FEATHER_WIDTH[1] * t))
    for i, (p, d, L) in enumerate(CREST):
        loc, _ = on_skin(tree, p, (0, 0, -1), back=0.1)
        h = P.horn(tuple(loc), length=L, radius=0.03, forward=d, up=(0, 0, -1), curve=40, sides=3, segs=3,
                   name=f'crest{i}')
        pieces.append(recolor(h, {'horn': 'hair', 'horn_tip': 'feather'}, 'hair'))
        if p[0] > 0:
            h2 = P.horn(tuple((-loc.x, loc.y, loc.z)), length=L, radius=0.03, forward=(-d[0], d[1], d[2]), up=(0, 0, -1),
                        curve=40, sides=3, segs=3, side=-1, name=f'crest{i}R')
            pieces.append(recolor(h2, {'horn': 'hair', 'horn_tip': 'feather'}, 'hair'))
    for i, (lx, L, _) in enumerate(TAIL):
        for s in ((1, -1) if lx else (1,)):
            base = (0.03 * s if lx else 0.0, 0.10, 0.78)
            loc, _ = on_skin(tree, base, (0, -1, 0), back=0.3)
            h = P.horn(tuple(loc), length=L, radius=0.04, forward=(lx * s, 1, -0.6), up=(0, 0, 1), curve=15, sides=3,
                       segs=2, name=f'tail{i}{s}')
            pieces.append(recolor(h, {'horn': 'feather', 'horn_tip': 'tip'}, 'feather'))
    ep, er = EYE
    loc, nrm = on_skin(tree, ep, (0, 1, 0), back=0.2)
    pieces += pair(P.eye_set, tuple(loc), tuple((Vector(nrm) + Vector((0, -0.6, 0))).normalized()), (0, 0, 1),
                   {'iris': 'eye', 'pupil': 'claw', 'glint': 'tip', 'eye_rim': 'hair', 'eye_socket': 'claw',
                    'lid': 'skin', 'sclera': 'tip'}, 'hair', 'eye', radius=er, expression='angry')
    c = LEG[-1][0]
    pieces += pair(P.bird_foot, (c[0], c[1], c[2] - 0.01), (0, -1, 0), (0, 0, 1), {'scale': 'scale', 'claw': 'claw'},
                   'scale', 'foot', toe_length=FOOT['toe_length'], talon_len=0.5)
    return pieces


def bones():
    return [('hips', J['hip'], J['spine'], None), ('chest', J['spine'], J['chest'], 'hips', True),
            ('neck', J['chest'], J['neck'], 'chest', True), ('head', J['neck'], J['crown'], 'neck', True),
            ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'), ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
            ('hand.L', J['wristL'], J['handL'], 'forearm.L', True),
            ('thigh.L', J['hipL'], J['kneeL'], 'hips'), ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
            ('tarsus.L', J['ankleL'], J['footL'], 'shin.L', True)]


def stage4(k, body, pieces):
    rig = armature(bones(), roll='auto')
    skin(body, rig)
    for p in pieces:
        if any(s in p.name for s in ('eye', 'crest')):
            bind(p, rig, bone='head')
        elif 'foot' in p.name:
            bind(p, rig, bone='tarsus.L' if p.name.endswith('_L') else 'tarsus.R')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'upperarm.L': (0, 0, 6), 'upperarm.R': (0, 0, -6), 'head': (0, 0, 10), 'chest': (2, 0, 0)},
                       24: {'head': (-4, 0, 0)},
                       36: {'upperarm.L': (0, 0, 6), 'upperarm.R': (0, 0, -6), 'head': (0, 0, -10), 'chest': (2, 0, 0)},
                       48: {}})

    def step(s):
        return {'thigh.L': (16 * s, 0, 0), 'thigh.R': (-16 * s, 0, 0), 'chest': (0, 5 * s, 0),
                'upperarm.L': (0, 0, 4 * s), 'upperarm.R': (0, 0, 4 * s)}

    def passing(s):
        side = 'L' if s > 0 else 'R'
        return {f'thigh.{side}': (20, 0, 0), f'shin.{side}': (-25, 0, 0), f'tarsus.{side}': (20, 0, 0)}
    clip(rig, 'move', {1: step(1), 9: passing(-1), 17: step(-1), 25: passing(1), 33: step(1)},
         loc={f: {'hips': (0, 0, 0 if f in (1, 17, 33) else 0.025)} for f in (1, 9, 17, 25, 33)})
    clip(rig, 'attack', {1: {}, 10: {'upperarm.L': (0, 0, 35), 'upperarm.R': (0, 0, -35), 'chest': (-8, 0, 0), 'head': (-6, 0, 0)},
                         16: {'upperarm.L': (40, 0, -10), 'upperarm.R': (40, 0, 10), 'chest': (10, 0, 0), 'head': (8, 0, 0)},
                         22: {'upperarm.L': (25, 0, 0), 'upperarm.R': (25, 0, 0), 'chest': (6, 0, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
