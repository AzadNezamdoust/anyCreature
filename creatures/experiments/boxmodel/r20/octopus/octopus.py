"""Stylised low-poly octopus (r20), box-modelled in four stages (experiments/boxmodel/BRIEF.md).

One chain of 12-sided half rings (7 verts) that runs from the face, under the head and up the back into a tall
bulbous mantle tilted back. Eight arms (four a side) are extruded from one lower quad each and laid out on the
ground in a fan, tapering to tips that curl up. Big eyes on the head front, suckers and brow are stage 3.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit'))
sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from boxlib5 import *

META = dict(creature='octopus', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
# chain: (y, z, half width, half height front/top, half height back/bottom); direction = the curve's tangent
CH = [(-0.195, 0.230, 0.170, 0.115, 0.085), (-0.150, 0.240, 0.235, 0.160, 0.115), (-0.09, 0.250, 0.250, 0.170, 0.125),
      (0.02, 0.290, 0.270, 0.180, 0.130), (0.11, 0.380, 0.300, 0.190, 0.150), (0.15, 0.510, 0.315, 0.200, 0.165),
      (0.14, 0.650, 0.290, 0.180, 0.155), (0.08, 0.770, 0.215, 0.135, 0.120), (0.01, 0.825, 0.090, 0.065, 0.055)]
ARM_J = 4                              # arms come out of ring vertices 4 -> 5 (the lower flank)
ARM_RING = (0, 1, 2, 3)                # one quad each: rings i -> i+1
ARM_DIR = [(0.45, -0.89), (0.95, -0.30), (0.93, 0.36), (0.50, 0.87)]   # ground direction (x, y) of each arm
ARM_D = (0.33, 0.44, 0.55, 0.65)       # distance of each section from the arm's origin on the body axis
ARM_Z = (0.075, 0.045, 0.045, 0.075)
ARM_W = (0.075, 0.068, 0.052, 0.036)
ARM_BEND = 1.2                         # rad per metre: each arm sweeps sideways (alternating) as it goes
ARM_TIP = (0.71, 0.14)                 # tip distance, tip height: the curl
# ================================================================ end PARAMS


def chain():
    out = []
    for q, (y, z, w, ht, hb) in enumerate(CH):
        a = CH[max(q - 1, 0)]; b = CH[min(q + 1, len(CH) - 1)]
        d = (b[0] - a[0], b[1] - a[1])
        out.append(hring((y, z), d, w, ht, hb, shape=SHAPE7, up=(-d[1], d[0])))
    return out


CHAIN = chain()
ARMS = {}


def P(i, j):
    return Vector(CHAIN[i][j])


def arm_secs(n):
    i = ARM_RING[n]
    oy = (CH[i][0] + CH[i + 1][0]) / 2 * 0.5
    a0 = math.atan2(ARM_DIR[n][1], ARM_DIR[n][0])
    sg = -1                                # every arm sweeps the same way (pinwheel): no two arms converge

    def at(d):
        a = a0 + sg * ARM_BEND * max(0.0, d - ARM_D[0]) * (d - ARM_D[0] + 0.2)
        return math.cos(a) * d, oy + math.sin(a) * d
    secs = [dict(c=(*at(d), z), w=w, d=w * 1.1) for d, z, w in zip(ARM_D, ARM_Z, ARM_W)]
    tip = (*at(ARM_TIP[0]), ARM_TIP[1])
    return secs, tip


def stage1(k):
    bm = bmesh.new()
    R = build_chain(bm, CHAIN)
    for n in range(4):
        secs, tip = arm_secs(n)
        ARMS[n] = freeze(build_limb(bm, R, ARM_RING[n], 1, ARM_J, secs, tip=tip))
    recalc_normals(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    for n in range(4):
        for a in range(3):
            with k.topo(bm, 'loop', 'arm %d: loop %d for the curl' % (n, a)):
                limb_loop(bm, ARMS[n], a, 0.5)
    with k.topo(bm, 'loop', 'head / mantle junction: the mantle sways on it'):
        loopcut(bm, edge_near(bm, (P(3, 0) + P(4, 0)) / 2), t=0.5, near=vert_near(bm, P(3, 0)))
    with k.topo(bm, 'loop', 'mantle: mid loop for the breathing swell'):
        loopcut(bm, edge_near(bm, (P(5, 0) + P(6, 0)) / 2), t=0.5, near=vert_near(bm, P(5, 0)))
    for j in (1, 2):                                     # brow ridge over the eyes stands out
        vert_near(bm, P(2, j)).co += Vector((0.0, -0.012, 0.010))
    commit(body, bm)


PALETTE = {'coral': '#d65a40', 'spot': '#a83c2d', 'cream': '#f1d8b8', 'white': '#f5f1e6', 'black': '#1f1b1b'}


def pal(*keys):
    return {q: PALETTE[q] for q in keys}


def body_rule(c, n, i):
    x, y, z = c
    if z < 0.13 and math.hypot(x, y) > 0.24 and n.z < 0.3:
        return 'cream'                                   # sucker side of the arms
    return 'coral'


def warts(tree):
    """Low darker spots on the mantle and head (raised, a separate piece)."""
    bm = bmesh.new()
    spots = [(0.16, 0.10, 0.55), (0.22, 0.18, 0.45), (0.10, 0.22, 0.66), (0.20, 0.06, 0.70), (0.08, 0.16, 0.38),
             (0.24, 0.04, 0.55), (0.12, -0.02, 0.78)]
    for x, y, z in spots:
        d = Vector((x, y - 0.1, z - 0.5)).normalized()
        loc, nrm = on_skin(tree, (x, y, z), d)
        cone(bm, loc, nrm, 0.040, 0.020, sides=5, bury=0.6, taper=0.35)
    return mk('warts', bm, pal('spot'), lambda c, n_, i: 'spot')


def suckers(tree):
    bm = bmesh.new()
    for n in range(4):
        secs, tip = arm_secs(n)
        for s in secs[1:]:
            c = Vector(s['c'])
            side = Vector((c.x, c.y - 0.0, 0)).normalized().cross(Vector((0, 0, 1)))
            p = c + side * s['w'] * 0.55 + Vector((0, 0, -0.01))
            loc, nrm = on_skin(tree, p, side)
            cone(bm, loc, nrm, 0.018, 0.012, sides=5, bury=0.6, taper=0.2)
    return mk('suckers', bm, pal('cream'), lambda c, n_, i: 'cream')


def stage3(k, body):
    paint(body, pal('coral', 'cream'), body_rule)
    tree = body_tree(body)
    eyes = eye_pair(tree, (0.12, -0.18, 0.31), (0.5, -1, 0.35), 0.072,
                    mats={'outline': 'spot', 'sclera': 'white', 'pupil': 'black', 'glint': 'white', 'lid': 'coral'},
                    colours={'spot': PALETTE['spot']}, style='toon', brow_wedge=True)
    return [warts(tree), suckers(tree)] + eyes


def bones():
    out = [('body', (0, -0.10, 0.25), (0, 0.10, 0.36), None),
           ('mantle', (0, 0.10, 0.36), (0, 0.15, 0.58), 'body', True),
           ('mantle2', (0, 0.15, 0.58), (0, 0.06, 0.80), 'mantle', True)]
    for n in range(4):
        secs, tip = arm_secs(n)
        i = ARM_RING[n]
        root = (0.13, (CH[i][0] + CH[i + 1][0]) / 2, 0.16)
        out += [('arm%da.L' % n, root, secs[1]['c'], 'body'),
                ('arm%db.L' % n, secs[1]['c'], secs[3]['c'], 'arm%da.L' % n, True),
                ('arm%dc.L' % n, secs[3]['c'], tip, 'arm%db.L' % n, True)]
    return out


CB = ('body', 'mantle', 'mantle2')


def ripple(ph, amp):
    d = {}
    for n in range(4):
        for sd, s in (('L', 1), ('R', -1)):
            w = math.sin(ph + n * 1.3 + (0 if s > 0 else 2.0))
            d['arm%db.%s' % (n, sd)] = (amp * w, 0, 0)
            d['arm%dc.%s' % (n, sd)] = (amp * 1.6 * w, 0, 0)
    return d


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_eye'):
            bind(p, rig, bone='body')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {f: {**ripple(f / 48 * 2 * math.pi, 8), 'mantle': (4 * math.sin(f / 48 * 2 * math.pi), 0, 0)}
                       for f in (1, 13, 25, 37, 49)})
    clip(rig, 'move', {f: {**ripple(f / 24 * 2 * math.pi, 14), 'mantle': (6 * math.sin(f / 24 * 2 * math.pi), 0, 0),
                           'mantle2': (4 * math.sin(f / 24 * 2 * math.pi + 1), 0, 0)} for f in (1, 7, 13, 19, 25)},
         loc={f: {'body': (0, 0, 0.02 * abs(math.sin(f / 24 * 2 * math.pi)))} for f in (1, 7, 13, 19, 25)})
    up = both({'arm0a': (-25, 0, 0), 'arm0b': (-20, 0, 0), 'arm0c': (-25, 0, 0), 'mantle': (-8, 0, 0)}, CB)
    lash = both({'arm0a': (10, 0, 0), 'arm0b': (15, 0, 0), 'arm0c': (20, 0, 0), 'mantle': (8, 0, 0)}, CB)
    clip(rig, 'attack', {1: {}, 10: up, 16: lash, 24: both({'arm0b': (4, 0, 0)}, CB), 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
