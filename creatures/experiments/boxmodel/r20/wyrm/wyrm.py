"""Wyrm (r20): a legless crimson serpent-dragon, its neck reared high like a cobra and its body thrown into two
humps over the ground. One chain of 5-vertex half rings snout -> tail tip along a vertical S path (the S is in
y-z so the mirror holds); horns, dorsal fin blades, tail blade, eyes and fangs are separate pieces."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'kit')); sys.path.insert(0, os.path.join(HERE, '..'))
from bmkit import *
from r20lib import *
import parts as P

META = dict(creature='wyrm', model='opus', engine_glb='', total_tris=(900, 2200))

# ================================================================ PARAMS
PATH = [  # (y, z), half width, above, below
    ((-1.110, 0.790), 0.040, 0.030, 0.035),   # 0 snout tip
    ((-1.060, 0.800), 0.072, 0.048, 0.052),   # 1 nose
    ((-0.930, 0.815), 0.092, 0.062, 0.072),   # 2 jaw
    ((-0.800, 0.835), 0.115, 0.088, 0.080),   # 3 brow
    ((-0.710, 0.835), 0.120, 0.092, 0.086),   # 4 skull
    ((-0.630, 0.800), 0.100, 0.080, 0.080),   # 5 skull back
    ((-0.560, 0.720), 0.085, 0.074, 0.074),   # 6 neck
    ((-0.505, 0.585), 0.092, 0.082, 0.082),   # 7
    ((-0.470, 0.445), 0.102, 0.092, 0.092),   # 8
    ((-0.420, 0.340), 0.112, 0.102, 0.102),   # 9
    ((-0.330, 0.240), 0.122, 0.112, 0.112),   # 10
    ((-0.190, 0.185), 0.130, 0.120, 0.125),   # 11 ground
    ((-0.040, 0.250), 0.132, 0.125, 0.100),   # 12
    ((0.110, 0.340), 0.132, 0.125, 0.085),    # 13 hump
    ((0.260, 0.270), 0.126, 0.120, 0.100),    # 14
    ((0.410, 0.195), 0.120, 0.112, 0.120),    # 15
    ((0.560, 0.165), 0.110, 0.102, 0.110),    # 16 ground
    ((0.720, 0.205), 0.098, 0.090, 0.090),    # 17
    ((0.880, 0.225), 0.084, 0.078, 0.078),    # 18 small hump
    ((1.030, 0.170), 0.068, 0.062, 0.062),    # 19
    ((1.170, 0.120), 0.050, 0.046, 0.046),    # 20
    ((1.300, 0.080), 0.030, 0.028, 0.028),    # 21
    ((1.400, 0.050), 0.012, 0.012, 0.012),    # 22 tail tip
]
THICK = dict(head=1.85, body=1.45)    # section scale: path rings 0-5 / the rest
REFINE = range(6, 22)          # a mid ring after each of these path rings (even faces along the body)
HORN = dict(base=(0.070, -0.690, 0.915), length=0.42, radius=0.060, forward=(0.35, 0.8, 0.45), curve=40)
FINS = [(-0.47, 0.17), (-0.33, 0.19), (0.10, 0.25), (0.25, 0.21), (0.88, 0.16)]   # path y, blade length
EYE = ((0.085, -0.790, 0.865), 0.026)
FANG = dict(base=(0.060, -1.000, 0.500), length=0.06, radius=0.013)
TAIL_BLADE = dict(base=(0.0, 1.36, 0.06), length=0.20, radius=0.05)
PALETTE = {'scale': '#8c302a', 'dark': '#4e2025', 'belly': '#e2b968', 'fin': '#d9862b', 'horn': '#ebdfc4',
           'eye': '#f5e050', 'mouth': '#2a1418'}
# ================================================================ end PARAMS

CEN = []


def rows():
    out = []
    P_ = [(c, w * f, hu * f, hd * f) for i, (c, w, hu, hd) in enumerate(PATH)
          for f in [THICK['head'] if i <= 5 else THICK['body']]]
    for i, (c, w, hu, hd) in enumerate(P_):
        out.append(dict(c=c, w=w, hu=hu, hd=hd, src=i))
        if i in REFINE:
            (c1, w1, u1, d1) = P_[i + 1]
            out.append(dict(c=((c[0] + c1[0]) / 2, (c[1] + c1[1]) / 2), w=(w + w1) / 2, hu=(hu + u1) / 2,
                            hd=(hd + d1) / 2, src=i + 0.5))
    return out


def stage1(k):
    bm = bmesh.new()
    rs = rows()
    R = chain(bm, [{q: r[q] for q in ('c', 'w', 'hu', 'hd')} for r in rs])
    CEN[:] = [(0.0, r['c'][0], r['c'][1]) for r in rs]
    return object_from_bm('body', bm)


def path_pt(i):
    c = PATH[i][0]
    return (0.0, c[0], c[1])


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'mouth: a loop through the jaw so the mouth line has an edge'):
        loopcut(bm, edge_near(bm, ((0, -0.925, 0.81 + 0.055))), t=0.5)
    with k.topo(bm, 'loop', 'neck: an extra loop at the tightest bend (rear-up)'):
        loopcut(bm, edge_near(bm, (0.0, -0.53, 0.72)), t=0.5)
    # brow ridge: the brow corner overhangs the eye
    v = vert_near(bm, (0.115 * 0.78, -0.80, 0.835 + 0.088 * 0.72))
    v.co += Vector((0.014, -0.004, 0.006))
    # lower jaw drops a little (an open-mouthed hiss)
    for q in bm.verts:
        if q.co.y < -0.86 and q.co.z < 0.775:
            q.co.z -= 0.012
    commit(body, bm)


def body_rule(c, n, i):
    p = Vector(c)
    j = min(range(len(CEN)), key=lambda q: (Vector(CEN[q]) - p).length)
    a = Vector(CEN[max(j - 1, 0)]); b = Vector(CEN[min(j + 1, len(CEN) - 1)])
    d = (b - a).normalized()
    u = Vector((0, -d.z, d.y))
    if u.z < 0:
        u = -u
    if c[1] < -0.99:
        return 'dark'
    if n.dot(u) < -0.45 and abs(c[0]) < 0.10:
        return 'belly'
    if n.dot(u) > 0.8:
        return 'dark'
    return 'scale'


def stage3(k, body):
    paint(body, PALETTE, body_rule)
    tree = body_tree(body)
    pieces = []
    h = HORN
    pieces += pair(P.horn, h['base'], h['forward'], (0, 0, 1), {'horn': 'horn', 'horn_tip': 'dark'}, 'horn', 'horn',
                   length=h['length'], radius=h['radius'], curve=h['curve'], sides=5, segs=3)
    for i, (y, L) in enumerate(FINS):
        loc, nrm = on_skin(tree, (0.0, y, 1.5), (0, 0, -1), back=0.0)
        f = P.horn(tuple(loc), length=L, radius=0.04, forward=tuple(Vector(nrm) + Vector((0, 0.6, 0))),
                   up=(0, 1, 0), curve=30, sides=3, segs=2, name=f'fin{i}')
        pieces.append(recolor(f, {'horn': 'fin', 'horn_tip': 'dark'}, 'fin'))
    tb = TAIL_BLADE
    t = P.horn(tb['base'], length=tb['length'], radius=tb['radius'], forward=(0, 1, 0.5), up=(0, 0, 1), curve=20,
               sides=3, segs=2, name='tailblade')
    pieces.append(recolor(t, {'horn': 'fin', 'horn_tip': 'dark'}, 'fin'))
    ep, er = EYE
    loc, nrm = on_skin(tree, ep, (-1, 0.3, 0), back=0.2)
    pieces += pair(P.eye_set, tuple(loc), tuple(nrm), (0, 0, 1),
                   {'iris': 'eye', 'pupil': 'mouth', 'glint': 'horn', 'eye_rim': 'dark', 'eye_socket': 'mouth',
                    'lid': 'scale', 'sclera': 'eye'}, 'dark', 'eye', radius=er, expression='angry', pupil='slit')
    fg = FANG
    loc, _ = on_skin(tree, fg['base'], (0, 0, 1), back=0.0)
    pieces += pair(P.horn, tuple(loc + Vector((0, 0, 0.012))), (0, -0.2, -1), (0, -1, 0), {'horn': 'horn', 'horn_tip': 'horn'}, 'horn',
                   'fang', length=fg['length'], radius=fg['radius'], curve=20, sides=4, segs=2)
    return pieces


BONES = [('body0', 11, 13, None), ('neck3', 11, 9, 'body0'), ('neck2', 9, 7, 'neck3'), ('neck1', 7, 5, 'neck2'),
         ('head', 5, 0, 'neck1'), ('body1', 13, 15, 'body0'), ('body2', 15, 17, 'body1'), ('tail0', 17, 19, 'body2'),
         ('tail1', 19, 22, 'tail0')]


def stage4(k, body, pieces):
    rig = armature([(n, path_pt(a), path_pt(b), p, p is not None and n not in ('neck3',)) for n, a, b, p in BONES])
    skin(body, rig)
    for p in pieces:
        if any(s in p.name for s in ('horn', 'eye', 'fang')):
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'neck2': (3, 0, 4), 'neck1': (0, 0, 5), 'head': (-3, 0, 3), 'tail1': (0, 0, 8)},
                       24: {'neck2': (-2, 0, 0), 'head': (3, 0, 0)},
                       36: {'neck2': (3, 0, -4), 'neck1': (0, 0, -5), 'head': (-3, 0, -3), 'tail1': (0, 0, -8)},
                       48: {}})
    body_b = ['body1', 'body2', 'tail0', 'tail1']
    mv = {}
    for f in range(0, 5):
        ph = f / 4.0
        d = {b: (9 * math.sin(2 * math.pi * (ph - 0.18 * i)), 0, 0) for i, b in enumerate(body_b)}
        d['neck3'] = (4 * math.sin(2 * math.pi * (ph + 0.2)), 0, 0)
        d['head'] = (-4 * math.sin(2 * math.pi * (ph + 0.2)), 0, 0)
        mv[1 + f * 8] = d
    mv[33] = mv[1]
    clip(rig, 'move', mv)
    clip(rig, 'attack', {1: {}, 10: {'neck3': (-10, 0, 0), 'neck2': (-12, 0, 0), 'head': (-10, 0, 0)},
                         16: {'neck3': (14, 0, 0), 'neck2': (16, 0, 0), 'neck1': (8, 0, 0), 'head': (12, 0, 0)},
                         22: {'neck3': (8, 0, 0), 'neck2': (8, 0, 0), 'head': (4, 0, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
