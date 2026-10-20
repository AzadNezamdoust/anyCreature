"""Crystal beetle (r20): a pony-sized rhinoceros beetle whose domed teal shell grows violet crystal spikes and a
crystal horn. One chain of 5-vertex half rings mandible -> abdomen tip; six legs, each extruded from one
lower-flank quad (4-sided, insect section) through coxa / femur up to a high knee / tibia down."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit')); sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from r20lib import *
import parts as P

META = dict(creature='crystal_beetle', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
CHAIN = [  # (y, z), half width, above, below
    ((-0.570, 0.170), 0.050, 0.040, 0.035),     # 0 clypeus
    ((-0.510, 0.185), 0.100, 0.070, 0.055),     # 1 head front
    ((-0.430, 0.200), 0.130, 0.090, 0.065),     # 2 head
    ((-0.355, 0.210), 0.115, 0.080, 0.065),     # 3 neck
    ((-0.290, 0.235), 0.200, 0.120, 0.085),     # 4 pronotum front (fore leg 4-5)
    ((-0.180, 0.265), 0.245, 0.145, 0.095),     # 5 pronotum
    ((-0.080, 0.265), 0.215, 0.125, 0.095),     # 6 waist (mid leg 6-7)
    ((0.040, 0.280), 0.285, 0.190, 0.105),      # 7 elytra front
    ((0.180, 0.290), 0.305, 0.215, 0.105),      # 8 elytra (hind leg 8-9)
    ((0.320, 0.275), 0.285, 0.195, 0.100),      # 9
    ((0.440, 0.245), 0.220, 0.145, 0.080),      # 10
    ((0.530, 0.215), 0.100, 0.070, 0.050),      # 11 tip
]
LEGS = {  # root y (two bands from the ring there), sections (c, w, d)
    'fore': (-0.29, [((0.290, -0.270, 0.230), 0.050, 0.055), ((0.400, -0.330, 0.310), 0.034, 0.030),
                 ((0.470, -0.390, 0.120), 0.030, 0.030), ((0.490, -0.420, 0.000), 0.028, 0.034)]),
    'mid': (-0.08, [((0.300, -0.020, 0.230), 0.050, 0.055), ((0.440, 0.000, 0.320), 0.034, 0.030),
                ((0.540, 0.010, 0.120), 0.030, 0.030), ((0.560, 0.010, 0.000), 0.028, 0.034)]),
    'hind': (0.18, [((0.370, 0.270, 0.230), 0.050, 0.055), ((0.470, 0.350, 0.310), 0.034, 0.030),
                 ((0.530, 0.460, 0.120), 0.030, 0.030), ((0.550, 0.500, 0.000), 0.028, 0.034)]),
}
LEG_STRIP = 2
LEG_SPREAD, LEG_THICK = 0.80, 1.25     # leg sections pulled toward the first one in x; section scale
REFINE_FROM = 3                # chain rings from this one get a mid ring between neighbours (two bands per leg root)
HORN = dict(base=(0.0, -0.47, 0.25), length=0.30, radius=0.055, forward=(0, -0.55, 1), curve=55)
CRYSTALS = [  # (x, y, length, lean x, lean y)
    (0.10, 0.02, 0.20, 0.25, 0.15), (0.17, 0.16, 0.26, 0.45, 0.2), (0.09, 0.30, 0.18, 0.3, 0.45),
    (0.0, 0.14, 0.30, 0.0, 0.1), (0.0, -0.18, 0.14, 0.0, -0.2)]
EYE = ((0.10, -0.47, 0.235), 0.022)
MANDIBLE = dict(base=(0.045, -0.555, 0.145), length=0.11, radius=0.022, curve=70)
PALETTE = {'shell': '#2f7377', 'dark': '#1f3d4c', 'under': '#4d3d58', 'leg': '#2d2833', 'crystal': '#9a6ee0',
           'crystal_lt': '#d8c6ff', 'eye': '#f0b030', 'bone': '#e6dcc0'}
# ================================================================ end PARAMS

J = dict(tip=(0, 0.53, 0.23), thorax=(0, -0.08, 0.27), neck=(0, -0.35, 0.21), head=(0, -0.57, 0.18))
LEGJ = {}
LR = {}


def halfwidth(y, z):
    ys = [c[0][0] for c in CHAIN]
    if y <= ys[0] or y >= ys[-1]:
        return 0.0
    for a, b in zip(CHAIN, CHAIN[1:]):
        if a[0][0] <= y <= b[0][0]:
            t = (y - a[0][0]) / (b[0][0] - a[0][0])
            return a[1] + (b[1] - a[1]) * t
    return 0.0


def stage1(k):
    bm = bmesh.new()
    rows = []
    for i, (c, w, hu, hd) in enumerate(CHAIN):
        if i > REFINE_FROM:
            (c0, w0, u0, d0) = CHAIN[i - 1]
            rows.append(dict(c=((c0[0] + c[0]) / 2, (c0[1] + c[1]) / 2), w=(w0 + w) / 2, hu=(u0 + hu) / 2, hd=(d0 + hd) / 2))
        rows.append(dict(c=c, w=w, hu=hu, hd=hd))
    R = chain(bm, rows)
    for nm, (y0, tab) in LEGS.items():
        r0 = min(range(len(rows) - 2), key=lambda i: abs(rows[i]['c'][0] - y0))
        rs = limb(bm, [chain_face(R, r0, LEG_STRIP), chain_face(R, r0 + 1, LEG_STRIP)],
                  [dict(c=(tab[0][0][0] + (c[0] - tab[0][0][0]) * LEG_SPREAD, c[1], c[2]), w=w * LEG_THICK, d=d * LEG_THICK, e=2.4) for c, w, d in tab], even=True)
        LR[nm] = rs
        root = sum((v.co for v in rs[0]), Vector()) / len(rs[0])
        LEGJ[nm] = [tuple(root)] + [(tab[0][0][0] + (c[0] - tab[0][0][0]) * LEG_SPREAD, c[1], c[2]) for c, _, _ in tab]
    recalc_normals(bm)
    for nm in LR:
        LR[nm] = [limb_edge(LR[nm], a) for a in range(len(LR[nm]) - 1)]
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    for nm in LEGS:
        for seg, t, why in ((2, 0.35, 'a loop under the knee for the bend'), (1, 0.5, 'mid-femur loop (keeps the quads near square)')):
            mid, near = LR[nm][seg]
            with k.topo(bm, 'loop', f'{nm} leg: {why}'):
                loopcut(bm, edge_near(bm, mid), t=t, near=vert_near(bm, near))
    with k.topo(bm, 'loop', 'elytra: the shell rim loop between pronotum and wing cases'):
        a, b = Vector(CHAIN[6][0] + (0,)), None
        loopcut(bm, edge_near(bm, (0.0, -0.02, 0.27 + 0.16)), t=0.5)
    # pronotum front edge lifts into a lip over the head
    for v in bm.verts:
        if -0.30 < v.co.y < -0.28 and v.co.z > 0.33:
            v.co.y -= 0.02
    commit(body, bm)


def body_rule(c, n, i):
    x, y, z = c
    if x > halfwidth(y, z) * 1.02 + 0.01 or z < 0.13:
        return 'leg'
    if n.z < -0.3:
        return 'under'
    if y < -0.33:
        return 'dark'
    if -0.33 <= y < -0.03:
        return 'dark' if n.z > 0.75 else 'shell'
    if x < 0.025 and n.z > 0.5:
        return 'dark'
    if n.z < 0.2:
        return 'under'
    return 'shell'


def crystal(name, base, fwd, L, r):
    o = P.horn(base, length=L, radius=r, forward=fwd, up=(0, 1, 0), curve=4, sides=4, segs=2, taper=1.6,
               tip_from=0.55, name=name)
    return recolor(o, {'horn': 'crystal', 'horn_tip': 'crystal_lt'}, 'crystal')


def stage3(k, body):
    paint(body, PALETTE, body_rule)
    tree = body_tree(body)
    pieces = []
    h = HORN
    loc, _ = on_skin(tree, (0.0, h['base'][1], 0.6), (0, 0, -1), back=0.0)
    pieces.append(crystal('horn', tuple(loc), h['forward'], h['length'], h['radius']))
    for i, (x, y, L, lx, ly) in enumerate(CRYSTALS):
        loc, _ = on_skin(tree, (x, y, 0.8), (0, 0, -1), back=0.0)
        if x == 0:
            pieces.append(crystal(f'cr{i}', tuple(loc), (0, ly, 1), L, L * 0.2))
        else:
            for s in (1, -1):
                pieces.append(crystal(f'cr{i}{"LR"[s < 0]}', (loc.x * s, loc.y, loc.z), (lx * s, ly, 1), L, L * 0.2))
    ep, er = EYE
    loc, nrm = on_skin(tree, ep, (-1, 0, 0), back=0.25)
    pieces += pair(P.eye_set, tuple(loc), tuple(nrm), (0, 0, 1),
                   {'iris': 'eye', 'pupil': 'leg', 'glint': 'bone', 'sclera': 'eye'}, 'dark', 'eye',
                   radius=er, brow_wedge=False)
    m = MANDIBLE
    pieces += pair(P.horn, m['base'], (0.5, -1, -0.1), (-1, 0, 0), {'horn': 'bone', 'horn_tip': 'leg'}, 'bone',
                   'mandible', length=m['length'], radius=m['radius'], curve=m['curve'], sides=4, segs=3)
    return pieces


def bones():
    b = [('thorax', J['thorax'], J['neck'], None),
         ('abdomen', J['thorax'], J['tip'], 'thorax'),
         ('head', J['neck'], J['head'], 'thorax', True)]
    for nm in LEGS:
        j = LEGJ[nm]
        b += [(f'{nm}0.L', j[0], j[1], 'thorax'), (f'{nm}1.L', j[1], j[2], f'{nm}0.L', True),
              (f'{nm}2.L', j[2], j[4], f'{nm}1.L', True)]
    return b


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        bind(p, rig, bone='head' if ('mandible' in p.name or 'eye' in p.name or 'horn' in p.name) else None,
             body=body)
    clip(rig, 'idle', {1: {}, 16: {'head': (4, 0, 6), 'abdomen': (-3, 0, 0)}, 32: {'head': (-2, 0, -6)},
                       48: {}})
    # tripod gait: A = fore.L, mid.R, hind.L ; B = the others. Swing = yaw about the coxa (Z), lift = femur
    def tri(sa, la):
        d = {}
        for nm, s in (('fore', 1), ('mid', -1), ('hind', 1)):
            for side, sg in (('L', 1), ('R', -1)):
                grp = sa if (s == sg) else -sa
                lift = la if (s == sg) else 0
                d[f'{nm}0.{side}'] = (0, 0, 14 * grp * sg)
                d[f'{nm}1.{side}'] = (0, 0, 0) if not lift else (0, -18 * sg * lift, 0)
        return d
    clip(rig, 'move', {1: tri(1, 0), 5: tri(0, 1), 9: tri(-1, 0), 13: tri(0, -0.0), 17: tri(1, 0)})
    clip(rig, 'attack', {1: {}, 8: {'thorax': (8, 0, 0), 'head': (12, 0, 0)},
                         14: {'thorax': (-6, 0, 0), 'head': (-16, 0, 0)}, 20: {'head': (-6, 0, 0)}, 30: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
