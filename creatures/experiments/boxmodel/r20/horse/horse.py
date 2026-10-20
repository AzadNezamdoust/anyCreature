"""Stylised low-poly horse (r20), box-modelled in four stages (experiments/boxmodel/BRIEF.md).

One chain of 8-sided half rings muzzle -> head -> arched neck -> barrel -> tail dock; four legs extruded from
two lower-flank quads each through placed sections down to a flat hoof; ears pulled out of the skull quads.
Mane, forelock, tail and eyes are stage-3 pieces. Every shape number is in PARAMS.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit'))
sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from boxlib5 import *

META = dict(creature='horse', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
# head axis: muzzle front -> poll; rings are (t along the axis, half width, half height front, half height jaw)
HEAD_M, HEAD_P = (-1.22, 1.10), (-0.93, 1.60)
HEAD = [(0.00, 0.060, 0.050, 0.060), (0.08, 0.078, 0.070, 0.080), (0.30, 0.070, 0.068, 0.070),
        (0.55, 0.098, 0.074, 0.110), (0.78, 0.112, 0.070, 0.130), (0.97, 0.088, 0.060, 0.110)]
# neck: (y, z, dir, half width, crest half height, throat half height)
NECK = [(-0.80, 1.50, (0.55, -0.55), 0.105, 0.085, 0.115), (-0.71, 1.40, (0.50, -0.60), 0.135, 0.130, 0.150),
        (-0.63, 1.30, (0.55, -0.60), 0.160, 0.170, 0.175), (-0.565, 1.21, (0.70, -0.45), 0.180, 0.205, 0.200)]
# barrel: (y, z, half width, top, bottom)
BODY = [(-0.44, 1.10, 0.190, 0.250, 0.250), (-0.34, 1.07, 0.225, 0.340, 0.300), (-0.22, 1.06, 0.245, 0.350, 0.310),
        (-0.08, 1.06, 0.255, 0.300, 0.300), (0.10, 1.08, 0.262, 0.265, 0.290), (0.28, 1.10, 0.250, 0.285, 0.250),
        (0.42, 1.12, 0.240, 0.270, 0.210), (0.55, 1.12, 0.200, 0.215, 0.200)]
TAIL = [(0.64, 1.24, (0.6, -0.4), 0.055, 0.055), (0.70, 1.17, (0.4, -0.9), 0.040, 0.040)]
R_FORE, R_HIND = 11, 15            # chain ring where each leg's two-quad root starts (flank -> keel corner)
FORE = [((0.170, -0.30, 0.80), 0.085, 0.120), ((0.160, -0.27, 0.66), 0.082, 0.105), ((0.150, -0.31, 0.50), 0.074, 0.090),
        ((0.145, -0.33, 0.40), 0.062, 0.070), ((0.140, -0.33, 0.25), 0.046, 0.052), ((0.140, -0.34, 0.14), 0.050, 0.056),
        ((0.140, -0.365, 0.08), 0.044, 0.046), ((0.140, -0.375, 0.055), 0.060, 0.066), ((0.140, -0.38, 0.0), 0.066, 0.076)]
HIND = [((0.190, 0.40, 0.82), 0.100, 0.180), ((0.180, 0.31, 0.66), 0.075, 0.100), ((0.170, 0.42, 0.53), 0.072, 0.100),
        ((0.160, 0.52, 0.42), 0.056, 0.080), ((0.150, 0.50, 0.25), 0.046, 0.052), ((0.150, 0.49, 0.14), 0.050, 0.056),
        ((0.150, 0.465, 0.08), 0.044, 0.046), ((0.150, 0.455, 0.055), 0.060, 0.066), ((0.150, 0.45, 0.0), 0.066, 0.076)]
EAR_RING, EAR_TIP = 4, (0.080, -0.89, 1.72)
# ================================================================ end PARAMS

J = dict(hip=(0, 0.40, 1.15), spine=(0, -0.05, 1.12), chest=(0, -0.40, 1.15), neck0=(0, -0.50, 1.25),
         neck1=(0, -0.68, 1.42), head=(0, -0.88, 1.56), snout=(0, -1.20, 1.12),
         tail0=(0, 0.60, 1.22), tail1=(0, 0.70, 1.12),
         shoulderL=(0.17, -0.32, 0.98), elbowL=(0.16, -0.27, 0.66), kneeL=(0.145, -0.33, 0.40),
         fetL=(0.14, -0.34, 0.14), hoofL=(0.14, -0.38, 0.0),
         hipL=(0.19, 0.38, 1.02), stifleL=(0.18, 0.31, 0.66), hockL=(0.16, 0.52, 0.42),
         hfetL=(0.15, 0.49, 0.14), hhoofL=(0.15, 0.45, 0.0))


def head_rings():
    my, mz = HEAD_M; py, pz = HEAD_P
    d = (py - my, pz - mz)
    return [hring((my + d[0] * t, mz + d[1] * t), d, w, ht, hb) for t, w, ht, hb in HEAD]


def chain():
    C = head_rings()
    C += [hring((y, z), dd, w, ht, hb) for y, z, dd, w, ht, hb in NECK]
    C += [hring((y, z), (1, 0), w, ht, hb) for y, z, w, ht, hb in BODY]
    C += [hring((y, z), dd, w, h) for y, z, dd, w, h in TAIL]
    return C


CHAIN = chain()
BODY_SX = 1.10                     # barrel width factor (rings of BODY)
CHAIN[10:18] = [[(p[0] * BODY_SX, p[1], p[2]) for p in r_] for r_ in CHAIN[10:18]]
LEG_DX = 0.02                      # legs move out with the wider barrel
LEGS = {}


def secs(tab):
    return [dict(c=(c[0] + LEG_DX, c[1], c[2]), w=w, d=d, ff=0.6, fb=0.5) for c, w, d in tab]


def stage1(k):
    bm = bmesh.new()
    R = build_chain(bm, CHAIN)
    spike(bm, R[EAR_RING][1], R[EAR_RING][2], R[EAR_RING + 1][2], R[EAR_RING + 1][1], EAR_TIP)
    for name, i0, tab in (('fore', R_FORE, FORE), ('hind', R_HIND, HIND)):
        LEGS[name] = freeze(build_limb(bm, R, i0, 2, 2, secs(tab)))
    recalc_normals(bm)
    return object_from_bm('body', bm)


def P(i, j):
    return Vector(CHAIN[i][j])


def stage2(k, body):
    bm = edit(body)
    for leg, a, t, why in (('fore', 1, 0.5, 'elbow: a second loop at the elbow bend'),
                           ('fore', 2, 0.55, 'knee (carpus): loop above the knee'),
                           ('fore', 3, 0.45, 'knee (carpus): loop below the knee'),
                           ('fore', 4, 0.5, 'fetlock: loop above the fetlock'),
                           ('hind', 1, 0.5, 'stifle: loop below the stifle'),
                           ('hind', 2, 0.55, 'hock: loop above the hock'),
                           ('hind', 3, 0.5, 'hock: loop below the hock'),
                           ('hind', 4, 0.5, 'fetlock: loop above the fetlock')):
        with k.topo(bm, 'loop', why):
            limb_loop(bm, LEGS[leg], a, t)
    with k.topo(bm, 'loop', 'throatlatch: a loop between poll and neck for the head nod'):
        loopcut(bm, edge_near(bm, (P(5, 0) + P(6, 0)) / 2), t=0.5, near=vert_near(bm, P(5, 0)))
    with k.topo(bm, 'loop', 'neck base: a loop where the neck meets the withers'):
        loopcut(bm, edge_near(bm, (P(8, 0) + P(9, 0)) / 2), t=0.5, near=vert_near(bm, P(8, 0)))
    for i in (1, 2):                                  # the nostril corner flares out
        vert_near(bm, P(i, 2)).co.x += 0.010
    vert_near(bm, P(4, 3)).co.x += 0.012               # the round jaw plate stands out
    commit(body, bm)


PALETTE = {'coat': '#8b5a3c', 'dark': '#2e2522', 'muzzle': '#b49478', 'hoof': '#4f4640',
           'blaze': '#ece5d8', 'iris': '#5a3420'}


def pal(*keys):
    return {q: PALETTE[q] for q in keys}


def head_t(y, z):
    my, mz = HEAD_M; py, pz = HEAD_P
    dy, dz = py - my, pz - mz
    L2 = dy * dy + dz * dz
    t = ((y - my) * dy + (z - mz) * dz) / L2
    dist = abs((y - my) * dz - (z - mz) * dy) / math.sqrt(L2)
    return t, dist


def body_rule(c, n, i):
    x, y, z = c
    if z < 0.065:
        return 'hoof'
    t, dist = head_t(y, z)
    if z > 1.0 and -0.05 < t < 1.1 and dist < 0.16:
        if z > 1.68:
            return 'dark'                               # ear tips
        if t < 0.22:
            return 'muzzle'
        if x < 0.035 and n.y < -0.4 and 0.25 < t < 0.9:
            return 'blaze'
        return 'coat'
    if z < 0.30:
        return 'dark'                                   # black points below the knees and hocks
    return 'coat'


def mane(tree):
    """A stepped blade along the crest, poll -> withers (a separate piece; the neck keeps its loops)."""
    bm = bmesh.new()
    base, ups, hs, ws = [], [], [], []
    N = 9
    for q in range(N):
        u = q / (N - 1)
        i = 5 + u * 4.4                                   # chain ring 5 (poll) .. ~9.4 (withers)
        i0 = int(i); f = i - i0
        p = P(i0, 0).lerp(P(i0 + 1, 0), f)
        nrm = (p - (P(i0, 4).lerp(P(i0 + 1, 4), f))).normalized()
        loc, _ = on_skin(tree, p, nrm)
        base.append(loc); ups.append(nrm)
        hs.append((0.075 if q % 2 == 0 else 0.055) * (1.0 - 0.35 * abs(u - 0.4)))
        ws.append(0.030)
    crest(bm, base, ups, hs, ws)
    return mk('mane', bm, pal('dark'), lambda c, n, i: 'dark')


def forelock(tree):
    bm = bmesh.new()
    loc, n = on_skin(tree, (0, -0.93, 1.62), (0, -0.4, 1))
    cone(bm, loc, (0, -0.85, -0.35), 0.035, 0.14, sides=4, bury=0.35, bend=(0, 0.2, -1), flat=0.6)
    return mk('forelock', bm, pal('dark'), lambda c, n, i: 'dark', mirror=False)


def tail_piece():
    bm = bmesh.new()
    pts = [(0, 0.62, 1.24), (0, 0.72, 1.16), (0, 0.80, 1.00), (0, 0.85, 0.82), (0, 0.87, 0.64)]
    rad = [(0.045, 0.045), (0.060, 0.065), (0.075, 0.085), (0.080, 0.090), (0.060, 0.070)]
    tube(bm, pts, rad, sides=6, tip=(0, 0.875, 0.54))
    return mk('tail', bm, pal('dark'), lambda c, n, i: 'dark', mirror=False)


def stage3(k, body):
    paint(body, pal('coat', 'dark', 'muzzle', 'hoof', 'blaze'), body_rule)
    tree = body_tree(body)
    eyes = eye_pair(tree, (0.09, -1.02, 1.47), (1, -0.35, 0.35), 0.024,
                    mats={'eye_rim': 'dark', 'eye_socket': 'dark', 'iris': 'iris', 'pupil': 'dark',
                          'glint': 'blaze', 'lid': 'coat'}, colours={'iris': PALETTE['iris']}, brow_wedge=False)
    return [mane(tree), forelock(tree), tail_piece()] + eyes


def bones():
    return [('hips', J['hip'], J['spine'], None),
            ('chest', J['spine'], J['neck0'], 'hips', True),
            ('neck', J['neck0'], J['neck1'], 'chest', True),
            ('neck2', J['neck1'], J['head'], 'neck', True),
            ('head', J['head'], J['snout'], 'neck2', True),
            ('tail0', J['tail0'], (0, 0.75, 1.10), 'hips'),
            ('tail1', (0, 0.75, 1.10), (0, 0.83, 0.88), 'tail0', True),
            ('tail2', (0, 0.83, 0.88), (0, 0.87, 0.58), 'tail1', True),
            ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
            ('forearm.L', J['elbowL'], J['kneeL'], 'upperarm.L', True),
            ('cannon.L', J['kneeL'], J['fetL'], 'forearm.L', True),
            ('pastern.L', J['fetL'], J['hoofL'], 'cannon.L', True),
            ('thigh.L', J['hipL'], J['stifleL'], 'hips'),
            ('shin.L', J['stifleL'], J['hockL'], 'thigh.L', True),
            ('hcannon.L', J['hockL'], J['hfetL'], 'shin.L', True),
            ('hpastern.L', J['hfetL'], J['hhoofL'], 'hcannon.L', True)]


CB = ('hips', 'chest', 'neck', 'neck2', 'head', 'tail0', 'tail1', 'tail2')


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_eye') or 'forelock' in p.name:
            bind(p, rig, bone='head')
        elif 'tail' in p.name:
            bind(p, rig)
        else:
            bind(p, rig, body=body)
    T = lambda z: {'tail0': (-6, 0, z), 'tail1': (4, 0, z * 0.8), 'tail2': (4, 0, z * 0.6)}
    clip(rig, 'idle', {1: T(0), 12: {'chest': (1.5, 0, 0), 'neck': (-3, 0, 2), 'head': (4, 0, 3), **T(12)},
                       24: {'neck': (2, 0, 0), 'head': (-2, 0, 0), **T(0)},
                       36: {'chest': (1.5, 0, 0), 'neck': (-3, 0, -2), 'head': (4, 0, -3), **T(-12)}, 48: T(0)})

    def trot(af, ah, bf, bh, la, lb):         # diagonal pairs A = fore.L + hind.R, B = fore.R + hind.L
        return {'upperarm.L': (af, 0, 0), 'thigh.R': (ah, 0, 0), 'upperarm.R': (bf, 0, 0), 'thigh.L': (bh, 0, 0),
                'forearm.L': (45 * la, 0, 0), 'forearm.R': (45 * lb, 0, 0),
                'cannon.L': (15 * la, 0, 0), 'cannon.R': (15 * lb, 0, 0),
                'shin.R': (-20 * la, 0, 0), 'shin.L': (-20 * lb, 0, 0),
                'hcannon.R': (30 * la, 0, 0), 'hcannon.L': (30 * lb, 0, 0),
                'neck': (-3 if not (la or lb) else 2, 0, 0), 'tail0': (-12, 0, 0), 'tail1': (8, 0, 0)}
    r_, b_ = -18, 14
    A, B = trot(r_, r_, b_, b_, 0, 0), trot(b_, b_, r_, r_, 0, 0)
    As, Bs = trot(0, 0, 0, 0, 1, 0), trot(0, 0, 0, 0, 0, 1)
    clip(rig, 'move', {1: B, 4: As, 7: A, 10: Bs, 13: B, 16: As, 19: A, 22: Bs, 25: B},
         loc={f: {'hips': (0, 0, -0.025 if f in (1, 7, 13, 19, 25) else 0.01)} for f in (1, 4, 7, 10, 13, 16, 19, 22, 25)})
    up = both({'upperarm': (-45, 0, 0), 'forearm': (70, 0, 0), 'cannon': (20, 0, 0), 'neck': (-10, 0, 0),
               'head': (12, 0, 0), 'chest': (-8, 0, 0), 'thigh': (14, 0, 0), 'shin': (-8, 0, 0),
               'tail0': (-20, 0, 0)}, CB)
    strike = both({'upperarm': (-20, 0, 0), 'forearm': (25, 0, 0), 'neck': (6, 0, 0), 'head': (-6, 0, 0),
                   'chest': (-3, 0, 0), 'thigh': (6, 0, 0), 'tail0': (-10, 0, 0)}, CB)
    clip(rig, 'attack', {1: {}, 10: up, 18: strike, 24: {'neck': (8, 0, 0)}, 32: {}},
         loc={1: {'hips': (0, 0, 0)}, 10: {'hips': (0, 0, 0.04)}, 18: {'hips': (0, 0, -0.01)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
