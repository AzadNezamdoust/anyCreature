"""Kraken hound (r20): a wolf-sized sea hound. One chain of 5-vertex half rings nose -> tail tip, legs extruded
from two lower-flank quads, finned ears pulled from the skull. Pieces: two shoulder tentacles arching over the
back, a beard of jaw tentacles, a dorsal fin row, eyes, claws."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit')); sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from r20lib import *
import parts as P

META = dict(creature='kraken_hound', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
# (y, z), half width, height above, depth below[, squareness]
CHAIN = [
    ((-0.840, 0.650), 0.040, 0.035, 0.035),     # 0 nose
    ((-0.805, 0.660), 0.062, 0.050, 0.055),     # 1
    ((-0.740, 0.675), 0.080, 0.062, 0.072),     # 2 muzzle
    ((-0.640, 0.700), 0.118, 0.105, 0.088),     # 3 brow / stop
    ((-0.540, 0.715), 0.140, 0.120, 0.098),     # 4 skull, cheek
    ((-0.440, 0.705), 0.130, 0.110, 0.100),     # 5 skull back
    ((-0.340, 0.640), 0.130, 0.115, 0.130),     # 6 neck
    ((-0.240, 0.570), 0.155, 0.135, 0.165),     # 7 neck base
    ((-0.130, 0.530), 0.185, 0.155, 0.200),     # 8 shoulder (fore root)
    ((-0.030, 0.515), 0.195, 0.160, 0.205),     # 9 chest
    ((0.070, 0.515), 0.185, 0.150, 0.175),      # 10 chest back
    ((0.170, 0.520), 0.165, 0.140, 0.140),      # 11 ribs
    ((0.270, 0.525), 0.140, 0.125, 0.105),      # 12 waist
    ((0.370, 0.535), 0.160, 0.125, 0.120),      # 13 hip (hind root)
    ((0.470, 0.535), 0.165, 0.125, 0.130),      # 14 haunch
    ((0.565, 0.520), 0.120, 0.105, 0.105),      # 15 rump
    ((0.650, 0.500), 0.062, 0.055, 0.055),      # 16 tail root
    ((0.770, 0.440), 0.050, 0.045, 0.045),      # 17
    ((0.880, 0.370), 0.036, 0.034, 0.034),      # 18
    ((0.970, 0.320), 0.016, 0.016, 0.016),      # 19 tail tip
]
CHUNK = dict(head=(1.45, 1.35), torso=(1.30, 1.12))   # (width, height) scale: head rings 0-5, torso 7-15
LEG_X, LEG_S = dict(fore=0.070, hind=0.070), dict(fore=1.2, hind=1.2)   # leg x shift, section scale
FORE_ROOT, HIND_ROOT = 8, 13          # legs come out of rings r..r+2, strip 2 (flank -> lower corner)
FORE = [  # c, w (lateral half), d (fore-aft half)
    ((0.160, -0.075, 0.330), 0.072, 0.095),
    ((0.155, -0.060, 0.230), 0.056, 0.068),
    ((0.150, -0.080, 0.100), 0.042, 0.046),
    ((0.150, -0.100, 0.035), 0.054, 0.068, (0, 0, -1)),
    ((0.150, -0.100, 0.000), 0.056, 0.072, (0, 0, -1)),
]
HIND = [
    ((0.165, 0.460, 0.360), 0.075, 0.115),
    ((0.160, 0.400, 0.250), 0.058, 0.072),
    ((0.150, 0.520, 0.135), 0.042, 0.052),
    ((0.148, 0.495, 0.055), 0.040, 0.046),
    ((0.148, 0.480, 0.030), 0.054, 0.068, (0, 0, -1)),
    ((0.148, 0.480, 0.000), 0.056, 0.072, (0, 0, -1)),
]
EAR_RING, EAR_TIP = 4, (0.235, -0.390, 0.880)
EYE = ((0.105, -0.610, 0.745), 0.030)        # approx skin point, radius
J = dict(hip=(0, 0.37, 0.55), spine=(0, 0.02, 0.55), neck=(0, -0.20, 0.58), head=(0, -0.42, 0.72),
         snout=(0, -0.86, 0.66), tail0=(0, 0.62, 0.51), tail1=(0, 0.77, 0.44), tail2=(0, 0.97, 0.32),
         shoulderL=(0.16, -0.06, 0.46), elbowL=(0.155, -0.06, 0.23), wristL=(0.15, -0.08, 0.10),
         pawL=(0.15, -0.14, 0.02),
         hipL=(0.165, 0.43, 0.46), stifleL=(0.16, 0.40, 0.25), hockL=(0.15, 0.52, 0.135), hpawL=(0.148, 0.44, 0.02))
TENT = [(0.10, -0.08, 0.60), (0.15, -0.02, 0.76), (0.17, 0.10, 0.87), (0.15, 0.24, 0.90), (0.12, 0.34, 0.85),
        (0.10, 0.38, 0.76)]
TENT_R = [0.070, 0.066, 0.058, 0.046, 0.032, 0.012]
BEARD = [((0.050, -0.700, 0.630), (0.060, -0.700, 0.500), (0.060, -0.740, 0.440)),
         ((0.025, -0.770, 0.630), (0.030, -0.780, 0.520), (0.030, -0.820, 0.470))]
FINS = [(-0.30, 0.10), (-0.10, 0.12), (0.10, 0.10), (0.30, 0.08)]   # y, height of each dorsal blade
PALETTE = {'skin': '#3d7d76', 'dark': '#284a57', 'belly': '#cdc79a', 'tent': '#7b4a8a', 'sucker': '#e0a2b4',
           'eye': '#f2d23a', 'claw': '#ece3c8', 'fin': '#c8644a'}
# ================================================================ end PARAMS

RINGS, LEG, LIMB_RINGS = [], {}, {}


def secs(table, dx=0.0, sc=1.0):
    out = []
    for t in table:
        s = dict(c=(t[0][0] + dx, t[0][1], t[0][2]), w=t[1] * sc, d=t[2] * sc)
        if len(t) > 3:
            s['dir'] = t[3]
        out.append(s)
    return out


def stage1(k):
    bm = bmesh.new()
    rows = []
    for i, (c, w, hu, hd) in enumerate(CHAIN):
        sw, sh = CHUNK['head'] if i <= 5 else CHUNK['torso'] if 7 <= i <= 15 else (1.0, 1.0)
        rows.append(dict(c=c, w=w * sw, hu=hu * sh, hd=hd * sh))
    R = chain(bm, rows)
    for nm, r0, tab in (('fore', FORE_ROOT, FORE), ('hind', HIND_ROOT, HIND)):
        fs = [chain_face(R, r0, 2), chain_face(R, r0 + 1, 2)]
        LIMB_RINGS[nm] = limb(bm, fs, secs(tab, LEG_X[nm], LEG_S[nm]))
    spike(bm, chain_face(R, EAR_RING, 1), EAR_TIP)
    recalc_normals(bm)
    RINGS[:] = [[tuple(v.co) for v in r] for r in R]
    for nm, rs in LIMB_RINGS.items():
        LEG[nm] = [limb_edge(rs, a) for a in range(len(rs) - 1)]
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    for nm, a, why in (('fore', 2, 'elbow: a loop above the elbow bend'), ('fore', 3, 'wrist loop'),
                       ('hind', 2, 'stifle: a loop below the knee'), ('hind', 3, 'hock loop')):
        mid, near = LEG[nm][a]
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, mid), t=0.5, near=vert_near(bm, near))
    with k.topo(bm, 'loop', 'neck: a third loop for the head-down bend'):
        loopcut(bm, edge_near(bm, ((Vector(RINGS[6][0]) + Vector(RINGS[7][0])) / 2)), t=0.5)
    # brow ridge overhang and a deeper stop
    vert_near(bm, RINGS[3][1]).co += Vector((0.012, -0.006, 0.010))
    vert_near(bm, RINGS[2][0]).co.z -= 0.010
    # jaw corner flares, belly tucks
    vert_near(bm, RINGS[5][3]).co += Vector((0.012, 0, -0.010))
    vert_near(bm, RINGS[12][4]).co.z += 0.02
    commit(body, bm)


def body_rule(c, n, i):
    x, y, z = c
    if y < -0.86:
        return 'dark'
    if z < 0.045:
        return 'dark'
    if n.z < -0.45 and -0.75 < y < 0.45 and x < 0.12 and z > 0.25:
        return 'belly'
    if y < -0.6 and z < 0.64:
        return 'belly'
    if n.z > 0.6 and z > 0.6 and -0.5 < y < 0.7:
        return 'dark'
    if y > 0.85:
        return 'fin'
    return 'skin'


def stage3(k, body):
    paint(body, PALETTE, body_rule)
    for kk, hx in PALETTE.items():
        material(kk, srgb(hx))
    tree = body_tree(body)
    pieces = []
    t = sweep('tentacle', TENT, [(r, r * 0.9) for r in TENT_R], up=(1, 0, 0), sides=5, mirror=True, point=True,
              keys=['tent', 'tent', 'tent', 'sucker', 'sucker'])
    pieces.append(paint_keys(t, PALETTE))
    for b in BEARD:
        bt = sweep('beard', list(b), [(0.024, 0.024), (0.018, 0.018), (0.004, 0.004)], up=(0, -1, 0), sides=4,
                   mirror=True, point=True, keys=['tent', 'sucker'])
        pieces.append(paint_keys(bt, PALETTE))
    for y, h in FINS:
        loc, _ = on_skin(tree, (0.0, y, 1.0), (0, 0, -1), back=0.0)
        f = P.horn(tuple(loc), length=h, radius=0.035, forward=(0, 0.35, 1), up=(0, 1, 0), curve=35, sides=3,
                   segs=2, name='fin')
        pieces.append(recolor(f, {'horn': 'fin', 'horn_tip': 'fin'}, 'fin'))
    ep, er = EYE
    loc, nrm = on_skin(tree, ep, (-1, 0.5, 0), back=0.2)
    fw = Vector(nrm) + Vector((0, -0.4, 0))
    pieces += pair(P.eye_set, tuple(loc), tuple(fw.normalized()), (0, 0, 1),
                   {'iris': 'eye', 'pupil': 'dark', 'glint': 'claw', 'eye_rim': 'dark', 'eye_socket': 'dark',
                    'lid': 'skin', 'sclera': 'eye'}, 'dark', 'eye', radius=er, expression='angry', pupil='slit')
    for nm, tab in (('fore', FORE), ('hind', HIND)):
        (cx, cy, _), _w, d = tab[-1][:3]
        cx += LEG_X[nm]
        for dx in (-0.03, 0.0, 0.03):
            base = (cx + dx, cy - d * LEG_S[nm] * 0.8, 0.022)
            pieces += pair(P.horn, base, (0, -1, -0.25), (0, 0, -1), {}, 'claw', 'claw',
                           length=0.045, radius=0.012, curve=50, sides=3, segs=2)
    return pieces


def bones():
    fp = (J['pawL'][0], J['pawL'][1] - 0.03, 0.02)
    hp0 = (J['hpawL'][0], J['hpawL'][1] + 0.06, 0.045)
    hp1 = (J['hpawL'][0], J['hpawL'][1] - 0.04, 0.01)
    return [('hips', J['hip'], J['spine'], None),
            ('chest', J['spine'], J['neck'], 'hips', True),
            ('neck', J['neck'], J['head'], 'chest', True),
            ('head', J['head'], J['snout'], 'neck', True),
            ('tail0', J['tail0'], J['tail1'], 'hips'),
            ('tail1', J['tail1'], J['tail2'], 'tail0', True),
            ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
            ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
            ('paw.L', J['wristL'], fp, 'forearm.L', True),
            ('thigh.L', J['hipL'], J['stifleL'], 'hips'),
            ('shin.L', J['stifleL'], J['hockL'], 'thigh.L', True),
            ('meta.L', J['hockL'], hp0, 'shin.L', True),
            ('hpaw.L', hp0, hp1, 'meta.L', True)]


CENTRE = ('hips', 'chest', 'neck', 'head', 'tail0', 'tail1')


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        if 'eye' in p.name:
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {
        1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (0, 0, 6), 'head': (2, 0, 5), 'tail0': (0, 0, 8)},
        24: {'neck': (-3, 0, 0), 'head': (3, 0, 0)},
        36: {'chest': (1.5, 0, 0), 'neck': (0, 0, -6), 'head': (2, 0, -5), 'tail0': (0, 0, -8)}, 48: {}})
    reach, back_ = -22, 18

    def trot(af, ah, bf, bh, la, lb):
        return {'upperarm.L': (af, 0, 0), 'thigh.R': (ah, 0, 0), 'upperarm.R': (bf, 0, 0), 'thigh.L': (bh, 0, 0),
                'forearm.L': (40 * la, 0, 0), 'shin.R': (26 * la, 0, 0), 'meta.R': (-18 * la, 0, 0),
                'forearm.R': (40 * lb, 0, 0), 'shin.L': (26 * lb, 0, 0), 'meta.L': (-18 * lb, 0, 0),
                'paw.L': (-(af if not la else 0), 0, 0), 'paw.R': (-(bf if not lb else 0), 0, 0),
                'hpaw.R': (-(ah if not la else 0), 0, 0), 'hpaw.L': (-(bh if not lb else 0), 0, 0),
                'tail0': (-6, 0, 6 * (la - lb))}
    A, B = trot(reach, reach, back_, back_, 0, 0), trot(back_, back_, reach, reach, 0, 0)
    As, Bs = trot(0, 0, 0, 0, 1, 0), trot(0, 0, 0, 0, 0, 1)
    clip(rig, 'move', {1: B, 4: As, 7: A, 10: Bs, 13: B, 16: As, 19: A, 22: Bs, 25: B},
         loc={f: {'hips': (0, 0, -0.03 if f in (1, 7, 13, 19, 25) else 0.008)} for f in (1, 4, 7, 10, 13, 16, 19, 22, 25)})
    clip(rig, 'attack', {
        1: {},
        8: both({'neck': (-12, 0, 0), 'head': (-6, 0, 0), 'chest': (-4, 0, 0), 'upperarm': (8, 0, 0),
                 'thigh': (-10, 0, 0)}, CENTRE),
        15: both({'neck': (24, 0, 0), 'head': (-10, 0, 0), 'chest': (4, 0, 0), 'upperarm': (-22, 0, 0),
                  'forearm': (6, 0, 0), 'thigh': (16, 0, 0), 'shin': (-8, 0, 0), 'tail0': (6, 0, 0)}, CENTRE),
        21: both({'neck': (18, 0, 0), 'head': (-4, 0, 0), 'chest': (3, 0, 0), 'upperarm': (-16, 0, 0),
                  'thigh': (12, 0, 0), 'shin': (-6, 0, 0)}, CENTRE),
        30: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, 0)}, 15: {'hips': (0, 0.07, 0)},
             21: {'hips': (0, 0.05, 0)}, 30: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
