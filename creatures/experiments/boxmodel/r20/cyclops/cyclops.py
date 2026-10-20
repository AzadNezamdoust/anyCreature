"""Cyclops (r20): a hulking pot-bellied giant with ONE huge eye under a heavy brow, a single horn, tusks, a
loincloth and a club. One vertical chain of 5-vertex half rings crown -> crotch (top seam = front, bottom
seam = back); arms extruded from the shoulder band, legs from the hip band, both from two side quads."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit')); sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from r20lib import *
import parts as P

META = dict(creature='cyclops', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
TORSO = [  # (y, z), half width, front depth, back depth
    ((0.000, 1.800), 0.070, 0.055, 0.055),    # 0 crown
    ((-0.010, 1.730), 0.160, 0.150, 0.120),   # 1 brow
    ((-0.010, 1.630), 0.175, 0.150, 0.130),   # 2 eye / cheek
    ((0.000, 1.510), 0.165, 0.160, 0.120),    # 3 jaw
    ((0.010, 1.430), 0.125, 0.125, 0.100),    # 4 chin
    ((0.030, 1.370), 0.140, 0.105, 0.105),    # 5 neck
    ((0.030, 1.275), 0.330, 0.150, 0.160),    # 6 shoulders (arm 6-7)
    ((0.020, 1.150), 0.360, 0.190, 0.165),    # 7 chest
    ((0.000, 1.020), 0.350, 0.240, 0.160),    # 8 upper belly
    ((0.000, 0.900), 0.340, 0.265, 0.150),    # 9 belly
    ((0.000, 0.800), 0.310, 0.225, 0.150),    # 10 low belly
    ((0.010, 0.720), 0.280, 0.165, 0.150),    # 11 hips (leg 11-12)
    ((0.010, 0.640), 0.170, 0.100, 0.100),    # 12 crotch
]
HUNCH = [(-0.13, -0.07), (-0.13, -0.07), (-0.13, -0.07), (-0.12, -0.06), (-0.10, -0.05), (-0.05, -0.02)]   # head rings 0-5 (dy, dz): the head juts forward and down
ARM_RING, LEG_RING = 6, 11
ARM = [  # c, lateral half, fore-aft half
    ((0.420, 0.030, 1.215), 0.060, 0.100, (1, 0, -0.25)),   # shoulder cap (out of the deltoid)
    ((0.490, 0.025, 1.090), 0.095, 0.100),    # upper arm
    ((0.515, 0.010, 0.960), 0.080, 0.085),    # elbow
    ((0.555, -0.020, 0.800), 0.095, 0.095),   # forearm swell
    ((0.575, -0.040, 0.640), 0.065, 0.065),   # wrist
    ((0.585, -0.055, 0.540), 0.085, 0.095),   # fist
    ((0.585, -0.055, 0.450), 0.060, 0.070),   # knuckles
]
LEG = [
    ((0.200, 0.010, 0.560), 0.125, 0.135),    # thigh
    ((0.210, -0.020, 0.380), 0.100, 0.100),   # knee
    ((0.210, 0.020, 0.240), 0.095, 0.105),    # calf
    ((0.210, 0.000, 0.100), 0.070, 0.070),    # ankle
    ((0.210, -0.050, 0.040), 0.095, 0.150, (0, 0, -1)),   # foot
    ((0.210, -0.050, 0.000), 0.095, 0.150, (0, 0, -1)),   # sole
]
EYE = ((0.0, -0.30, 1.575), 0.075)
HORN = dict(base=(0.0, -0.16, 1.72), length=0.22, radius=0.05)
TUSK = dict(base=(0.08, -0.28, 1.41), length=0.08, radius=0.02)
EAR = dict(base=(0.17, -0.13, 1.56), length=0.10)
CLUB = [(-0.585, -0.055, 0.62), (-0.585, -0.07, 0.45), (-0.60, -0.12, 0.25), (-0.61, -0.16, 0.12), (-0.615, -0.18, 0.05)]
CLUB_R = [(0.035, 0.035), (0.045, 0.045), (0.085, 0.085), (0.110, 0.110), (0.070, 0.070)]
PALETTE = {'skin': '#b98c68', 'dark': '#6a4636', 'cloth': '#6f7d3a', 'eye': '#f2ede0', 'iris': '#3a8fd2',
           'horn': '#e6dabe', 'wood': '#8a6440', 'pupil': '#1d1414'}
# ================================================================ end PARAMS

J = dict(hip=(0, 0.01, 0.74), spine=(0, 0.01, 1.00), chest=(0, 0.02, 1.30), neck=(0, -0.05, 1.40),
         crown=(0, -0.13, 1.73), shoulderL=(0.36, 0.03, 1.24), elbowL=(0.515, 0.01, 0.96), wristL=(0.575, -0.04, 0.64),
         handL=(0.585, -0.055, 0.44), hipL=(0.18, 0.01, 0.66), kneeL=(0.21, -0.02, 0.38), ankleL=(0.21, 0.0, 0.10),
         toeL=(0.21, -0.17, 0.02))
LE = {}


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
    R = chain(bm, [dict(c=(c[0] + (HUNCH[i][0] if i < 6 else 0), c[1] + (HUNCH[i][1] if i < 6 else 0)), w=w, hu=hu, hd=hd)
                   for i, (c, w, hu, hd) in enumerate(TORSO)], front=True)
    for nm, r0, tab in (('arm', ARM_RING, ARM), ('leg', LEG_RING, LEG)):
        rs = limb(bm, [chain_face(R, r0, 1), chain_face(R, r0, 2)], S(tab), even=True)
        LE[nm] = [limb_edge(rs, a) for a in range(len(rs) - 1)]
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    for nm, a, t, why in (('arm', 1, 0.5, 'elbow: a second loop above the bend'), ('leg', 1, 0.5, 'knee: a loop above the bend'),
                          ('leg', 2, 0.4, 'knee: a loop below the bend')):
        mid, near = LE[nm][a]
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, mid), t=t, near=vert_near(bm, near))
    # the heavy brow overhangs the eye
    for v in bm.verts:
        if 1.70 < v.co.z < 1.76 and v.co.y < -0.08:
            v.co.y -= 0.025
    commit(body, bm)


def body_rule(c, n, i):
    x, y, z = c
    ax = abs(x)
    if z < 0.05:
        return 'dark'
    if ax < 0.36 and 0.60 < z < 0.80 and not (ax > 0.30 and z < 0.7):
        return 'cloth'
    if z > 1.62 and n.y > 0.4 and ax < 0.12 and z < 1.78 and y > 0.05:
        return 'dark'
    return 'skin'


def stage3(k, body):
    paint(body, PALETTE, body_rule)
    tree = body_tree(body)
    pieces = []
    ep, er = EYE
    loc, nrm = on_skin(tree, ep, (0, 1, 0), back=0.3)
    e = P.eye_set(tuple(loc), er, forward=(0, -1, 0), up=(0, 0, 1), side=1, style='toon', expression='angry', name='eye')
    pieces.append(recolor(e, {'sclera': 'eye', 'outline': 'pupil', 'pupil': 'pupil', 'glint': 'eye', 'iris': 'iris',
                              'lid': 'skin', 'eye_rim': 'dark', 'eye_socket': 'pupil'}, 'skin'))
    loc, _ = on_skin(tree, (0.0, HORN['base'][1], 2.2), (0, 0, -1), back=0.0)
    h = P.horn(tuple(loc), length=HORN['length'], radius=HORN['radius'], forward=(0, -0.3, 1), up=(0, -1, 0), curve=35,
               sides=5, segs=3, name='horn')
    pieces.append(recolor(h, {'horn': 'horn', 'horn_tip': 'dark'}, 'horn'))
    loc, _ = on_skin(tree, TUSK['base'], (0, 1, 0), back=0.3)
    pieces += pair(P.tusk, tuple(loc + Vector((0, 0.01, 0))), (0.2, -0.3, 1), (0, -1, 0), {}, 'horn', 'tusk',
                   length=TUSK['length'], radius=TUSK['radius'], curve=30)
    loc, _ = on_skin(tree, EAR['base'], (-1, 0, 0), back=0.3)
    pieces += pair(P.ear_cup, tuple(loc), (0, -1, 0), (1, 0.2, 0.3), {'ear': 'skin', 'ear_inner': 'dark'}, 'skin',
                   'ear', length=EAR['length'], kind='pointed')
    c = sweep('club', CLUB, CLUB_R, up=(0, -1, 0), sides=6, key='wood')
    pieces.append(paint_keys(c, PALETTE))
    return pieces


def bones():
    return [('hips', J['hip'], J['spine'], None), ('chest', J['spine'], J['chest'], 'hips', True),
            ('neck', J['chest'], J['neck'], 'chest', True), ('head', J['neck'], J['crown'], 'neck', True),
            ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'), ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
            ('hand.L', J['wristL'], J['handL'], 'forearm.L', True),
            ('thigh.L', J['hipL'], J['kneeL'], 'hips'), ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
            ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True)]


C = ('hips', 'chest', 'neck', 'head')


def stage4(k, body, pieces):
    rig = armature(bones(), roll='auto')
    skin(body, rig)
    for p in pieces:
        if 'club' in p.name:
            bind(p, rig, bone='hand.R')
        elif any(s in p.name for s in ('eye', 'horn', 'tusk', 'ear')):
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'head': (0, 0, 8), 'upperarm.L': (0, 0, 3)},
                       24: {'chest': (0, 0, 0), 'head': (-3, 0, 0)},
                       36: {'chest': (2, 0, 0), 'head': (0, 0, -8), 'upperarm.R': (0, 0, -3)}, 48: {}})

    def step(s):
        return {'thigh.L': (20 * s, 0, 0), 'thigh.R': (-20 * s, 0, 0), 'shin.L': (-12 * max(-s, 0), 0, 0),
                'shin.R': (-12 * max(s, 0), 0, 0), 'upperarm.L': (-14 * s, 0, 0), 'upperarm.R': (14 * s, 0, 0),
                'chest': (0, 4 * s, 0)}

    def passing(s):
        d = {'thigh.L' if s > 0 else 'thigh.R': (12, 0, 0), 'shin.L' if s > 0 else 'shin.R': (-28, 0, 0)}
        return d
    clip(rig, 'move', {1: step(1), 9: passing(-1), 17: step(-1), 25: passing(1), 33: step(1)},
         loc={f: {'hips': (0, 0, 0 if f in (1, 17, 33) else 0.02)} for f in (1, 9, 17, 25, 33)})
    clip(rig, 'attack', {1: {}, 10: {'upperarm.R': (110, 0, 0), 'forearm.R': (50, 0, 0), 'chest': (-8, 0, 0)},
                         16: {'upperarm.R': (-30, 0, 0), 'forearm.R': (10, 0, 0), 'chest': (12, 0, 0), 'head': (6, 0, 0)},
                         22: {'upperarm.R': (-20, 0, 0), 'chest': (8, 0, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
