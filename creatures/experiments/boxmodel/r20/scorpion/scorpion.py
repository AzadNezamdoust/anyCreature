"""Stylised low-poly scorpion (r20), box-modelled in four stages (experiments/boxmodel/BRIEF.md).

One chain of 8-sided half rings: blunt carapace front -> flat segmented body -> a five-segment tail that curls
up and forward over the back -> the bulbous telson. Two pedipalp arms (swollen pincer palms) from the carapace
flank and four arched walking legs a side from the lower flank, each from one chain quad. Pincer fingers, the
stinger barb and the eyes are stage-3 pieces.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit'))
sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from boxlib5 import *

META = dict(creature='scorpion', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
# body rings: (y, z, half width, top, bottom)
BODY = [(-0.40, 0.140, 0.060, 0.030, 0.030), (-0.36, 0.145, 0.110, 0.045, 0.040), (-0.26, 0.150, 0.150, 0.055, 0.045),
        (-0.14, 0.150, 0.170, 0.058, 0.045), (-0.02, 0.150, 0.180, 0.058, 0.045), (0.10, 0.150, 0.170, 0.055, 0.045),
        (0.20, 0.150, 0.150, 0.052, 0.042), (0.29, 0.150, 0.120, 0.048, 0.040)]
# tail rings along the curl: (y, z, half width, half height); the direction is the curve's tangent
TAIL = [(0.37, 0.165, 0.075, 0.050), (0.45, 0.215, 0.066, 0.048), (0.51, 0.305, 0.062, 0.046),
        (0.53, 0.415, 0.060, 0.045), (0.49, 0.520, 0.058, 0.044), (0.41, 0.585, 0.055, 0.042),
        (0.32, 0.600, 0.060, 0.052), (0.25, 0.585, 0.068, 0.062), (0.19, 0.545, 0.040, 0.038)]
# walking legs: root ring pair i (lower flank quad), fore/aft lean dy, knee height
LEGS_T = [(2, -0.08, 0.27), (3, -0.03, 0.28), (4, 0.03, 0.28), (5, 0.08, 0.27)]
LEG_REACH = (0.25, 0.34, 0.43, 0.46)     # x of the root section, the knee, the shin, the tip
LEG_W = (0.032, 0.028, 0.021)
# pincer arm: from ring 1 -> 2, flank quad (ring vertices 1 -> 2)
ARM = [((0.19, -0.38, 0.17), 0.034, 0.034), ((0.25, -0.47, 0.19), 0.030, 0.030),
       ((0.23, -0.55, 0.19), 0.032, 0.032), ((0.19, -0.63, 0.19), 0.050, 0.060),
       ((0.16, -0.72, 0.19), 0.058, 0.064), ((0.14, -0.79, 0.19), 0.040, 0.046)]
# ================================================================ end PARAMS


def tail_rings():
    out = []
    for q, (y, z, w, h) in enumerate(TAIL):
        a = TAIL[max(q - 1, 0)]; b = TAIL[min(q + 1, len(TAIL) - 1)]
        d = (b[0] - a[0], b[1] - a[1])
        out.append(hring((y, z), d, w, h, h, up=(-d[1], d[0])))   # dorsal side = outside of the curl
    return out


BODY_H = 1.45                      # body depth factor: a segmented slab, not a plank
CHAIN = [hring((y, z + 0.01), (1, 0), w, ht * BODY_H, hb * 1.15) for y, z, w, ht, hb in BODY] + tail_rings()
N_BODY = len(BODY)
LIMBS = {}


def P(i, j):
    return Vector(CHAIN[i][j])


def leg_secs(i, dy, knee):
    y0 = (BODY[i][0] + BODY[i + 1][0]) / 2
    x0, xk, xs, xt = LEG_REACH
    return ([dict(c=(x0, y0 + dy * 0.3, 0.17), w=LEG_W[0], d=LEG_W[0]),
             dict(c=(xk, y0 + dy * 0.8, knee), w=LEG_W[1], d=LEG_W[1]),
             dict(c=(xs, y0 + dy * 1.3, 0.08), w=LEG_W[2], d=LEG_W[2])],
            (xt, y0 + dy * 1.6, 0.0))


def stage1(k):
    bm = bmesh.new()
    R = build_chain(bm, CHAIN)
    LIMBS['arm'] = freeze(build_limb(bm, R, 1, 1, 1, [dict(c=c, w=w, d=d) for c, w, d in ARM]))
    for n, (i, dy, knee) in enumerate(LEGS_T):
        secs, tip = leg_secs(i, dy, knee)
        LIMBS['leg%d' % n] = freeze(build_limb(bm, R, i, 1, 2, secs, tip=tip))
    recalc_normals(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'pincer arm: elbow loop'):
        limb_loop(bm, LIMBS['arm'], 0, 0.5)
    with k.topo(bm, 'loop', 'pincer arm: wrist loop before the palm swells'):
        limb_loop(bm, LIMBS['arm'], 2, 0.4)
    for n in range(4):
        with k.topo(bm, 'loop', 'leg %d: knee loop' % n):
            limb_loop(bm, LIMBS['leg%d' % n], 0, 0.6)
    for n in range(4):
        with k.topo(bm, 'loop', 'leg %d: ankle loop above the pointed foot' % n):
            limb_loop(bm, LIMBS['leg%d' % n], 1, 0.5)
    for q in range(N_BODY - 1, N_BODY + len(TAIL) - 2):
        with k.topo(bm, 'loop', 'tail joint %d: a loop between segments for the curl / strike' % q):
            loopcut(bm, edge_near(bm, (P(q, 0) + P(q + 1, 0)) / 2), t=0.5, near=vert_near(bm, P(q, 0)))
    # tergites: alternate abdomen rings step up so the back reads as overlapping plates
    for i in (3, 5, 7):
        for j in (0, 1):
            vert_near(bm, P(i, j)).co.z += 0.010
    for j in range(5):                                  # the waist behind the carapace pinches in
        v = vert_near(bm, P(4, j)); v.co.x *= 0.94
    commit(body, bm)


PALETTE = {'amber': '#b5742c', 'dark': '#6e3f1b', 'pale': '#dcb47a', 'black': '#221d19'}
TAIL_Y0 = 0.33


def pal(*keys):
    return {q: PALETTE[q] for q in keys}


def body_rule(c, n, i):
    x, y, z = c
    if z < 0.045 and abs(x) > 0.3:
        return 'black'                                   # foot tips
    if y > 0.15 and z > 0.50 and y < 0.30:
        return 'dark'                                    # telson
    if abs(x) < 0.2 and y < TAIL_Y0 and n.z < -0.4:
        return 'pale'                                    # underside
    if abs(x) < 0.2 and y < TAIL_Y0 and n.z > 0.45 and y > -0.30:
        return 'dark' if int((y + 0.30) / 0.12) % 2 else 'amber'
    if y > TAIL_Y0 and int(((z - 0.15) + abs(y - 0.45)) / 0.11) % 2:
        return 'dark'                                    # tail segment bands
    return 'amber'


def fingers():
    bm = bmesh.new()
    tip = LIMBS['arm'][-1]
    c = sum(tip.values(), Vector()) / len(tip)
    cone(bm, c + Vector((0.022, -0.035, 0.0)), (-0.15, -1, 0), 0.034, 0.17, sides=4, bury=0.3, bend=(-1, 0, 0), flat=0.8)
    cone(bm, c + Vector((-0.026, -0.035, 0.006)), (0.25, -1, 0), 0.030, 0.15, sides=4, bury=0.3, bend=(1, 0, 0), flat=0.8)
    return mk('fingers', bm, pal('dark', 'black'), lambda c_, n_, i: 'dark')


def stinger():
    bm = bmesh.new()
    y, z = TAIL[-1][0], TAIL[-1][1]
    cone(bm, (0, y - 0.01, z - 0.01), (0, -0.55, -1), 0.030, 0.12, sides=4, bury=0.35, bend=(0, -1, 0), segs=2)
    return mk('stinger', bm, pal('black'), lambda c_, n_, i: 'black', mirror=False)


def eyes(tree):
    bm = bmesh.new()
    for x, y in ((0.035, -0.30), (0.075, -0.36)):
        loc, n = on_skin(tree, (x, y, 0.3), (0.2, -0.3, 1))
        cone(bm, loc, n, 0.014, 0.018, sides=4, bury=0.5, taper=0.4)
    return mk('eyes', bm, pal('black'), lambda c_, n_, i: 'black')


def stage3(k, body):
    paint(body, pal('amber', 'dark', 'pale', 'black'), body_rule)
    tree = body_tree(body)
    return [fingers(), stinger(), eyes(tree)]


def bones():
    T = [(0, t[0], t[1]) for t in TAIL]
    out = [('body', (0, 0.05, 0.17), (0, -0.36, 0.17), None),
           ('abdomen', (0, 0.05, 0.17), (0, 0.33, 0.17), 'body'),
           ('tail0', T[0], T[2], 'abdomen'), ('tail1', T[2], T[4], 'tail0', True),
           ('tail2', T[4], T[6], 'tail1', True), ('sting', T[6], T[8], 'tail2', True),
           ('arm.L', (0.13, -0.33, 0.17), ARM[2][0], 'body'),
           ('claw.L', ARM[2][0], (0.14, -0.86, 0.19), 'arm.L', True)]
    for n, (i, dy, knee) in enumerate(LEGS_T):
        secs, tip = leg_secs(i, dy, knee)
        y0 = (BODY[i][0] + BODY[i + 1][0]) / 2
        out += [('leg%da.L' % n, (0.16, y0, 0.15), secs[1]['c'], 'body' if n < 2 else 'abdomen'),
                ('leg%db.L' % n, secs[1]['c'], tip, 'leg%da.L' % n, True)]
    return out


CB = ('body', 'abdomen', 'tail0', 'tail1', 'tail2', 'sting')


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        if 'fingers' in p.name:
            bind(p, rig)
        elif 'stinger' in p.name:
            bind(p, rig, bone='sting')
        else:
            bind(p, rig, bone='body')
    clip(rig, 'idle', {1: {}, 12: both({'tail0': (0, 0, 4), 'tail1': (3, 0, 0), 'arm': (0, 0, 5)}, CB),
                       24: both({'tail1': (-2, 0, 0), 'claw': (0, 0, -6)}, CB),
                       36: both({'tail0': (0, 0, -4), 'tail1': (3, 0, 0), 'arm': (0, 0, -3)}, CB), 48: {}})

    def walk(s):
        d = {}
        for n in range(4):
            side_a = (n % 2 == 0)
            for sd in ('L', 'R'):
                ph = s * (1 if side_a == (sd == 'L') else -1)
                d['leg%da.%s' % (n, sd)] = (0, 0, 12 * ph)
        d['abdomen'] = (0, 0, 2 * s); d['tail0'] = (0, 0, -3 * s)
        return d
    clip(rig, 'move', {1: walk(1), 7: walk(-1), 13: walk(1), 19: walk(-1), 25: walk(1)})
    clip(rig, 'attack', {1: {}, 8: both({'tail0': (-8, 0, 0), 'tail1': (-10, 0, 0), 'tail2': (-8, 0, 0),
                                         'arm': (0, 0, 10), 'claw': (0, 0, -10)}, CB),
                         14: both({'tail0': (14, 0, 0), 'tail1': (16, 0, 0), 'tail2': (12, 0, 0), 'sting': (10, 0, 0),
                                   'arm': (0, 0, -6), 'claw': (0, 0, 8)}, CB),
                         22: both({'tail0': (4, 0, 0), 'tail1': (4, 0, 0)}, CB), 30: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
