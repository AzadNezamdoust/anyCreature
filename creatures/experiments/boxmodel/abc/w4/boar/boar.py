import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='boar', model='opus')

# the skeleton the model is built on (left side; the rig mirrors .L)
J = dict(
    hip=(0.0, 0.44, 0.55), spine=(0.0, 0.14, 0.60), chest=(0.0, -0.10, 0.62), neck=(0.0, -0.20, 0.62),
    head=(0.0, -0.32, 0.60), snout=(0.0, -0.645, 0.36),
    shoulderL=(0.105, -0.075, 0.42), elbowL=(0.10, -0.07, 0.21), wristL=(0.10, -0.07, 0.11),
    fetlockL=(0.105, -0.078, 0.05), hoofL=(0.11, -0.09, 0.0),
    hipL=(0.105, 0.44, 0.42), hockL=(0.10, 0.48, 0.22), cannonL=(0.10, 0.475, 0.13),
    hfetlockL=(0.10, 0.455, 0.05), hhoofL=(0.10, 0.43, 0.0),
)

BODY = dict(ku=.64, hu=.15, hs=.58, kl=.88, hl=.22, kb=.45, hb=.02)
HUMP = dict(BODY, ku=.52, hu=.12)
HEAD = dict(ku=.50, hu=.04, hs=.70, kl=.92, hl=.22, kb=.50, hb=.02)
MUZZ = dict(ku=.80, hu=.05, hs=.55, kl=.96, hl=.20, kb=.56, hb=.02)   # flat broad forehead, square muzzle

# y, top z, bottom z, half width, profile  (rump -> snout)
RINGS = [
    (0.562, 0.55, 0.42, 0.055, BODY),   # R0 rump end (cap)
    (0.520, 0.635, 0.315, 0.135, BODY),  # R1 hind leg back
    (0.430, 0.665, 0.29, 0.155, BODY),  # R2 hind leg mid
    (0.340, 0.69, 0.29, 0.160, BODY),   # R3 hind leg front / flank fold
    (0.220, 0.715, 0.28, 0.175, BODY),  # R4
    (0.090, 0.765, 0.27, 0.190, BODY),  # R5
    (0.000, 0.80, 0.28, 0.200, HUMP),   # R6 front leg back
    (-0.080, 0.845, 0.29, 0.205, HUMP), # R7 front leg mid, hump
    (-0.160, 0.845, 0.31, 0.200, HUMP),  # R8 front leg front, hump crest
    (-0.220, 0.80, 0.34, 0.180, HEAD),  # R9 nape, ear back
    (-0.290, 0.75, 0.33, 0.155, HEAD),  # R10 ear front, jowl
    (-0.360, 0.68, 0.31, 0.135, MUZZ),  # R11 brow
    (-0.470, 0.55, 0.29, 0.100, MUZZ),  # R12 muzzle
    (-0.580, 0.455, 0.27, 0.075, MUZZ), # R13 snout base
    (-0.645, 0.41, 0.29, 0.070, MUZZ),  # R14 snout disc (cap)
]


def section(y, zt, zb, w, p):
    H = zt - zb
    return [(0.0, y, zt), (p['ku'] * w, y, zt - p['hu'] * H), (w, y, zb + p['hs'] * H),
            (p['kl'] * w, y, zb + p['hl'] * H), (p['kb'] * w, y, zb + p['hb'] * H), (0.0, y, zb)]


def leg_level(c, hd, hw):
    cx, cy, z = c
    def f(key):
        pos, side = key
        s = 1 if side == 'o' else -1
        if pos == 'm':
            return (cx + s * hw, cy, z)
        return (cx + s * 0.55 * hw, cy + (hd if pos == 'b' else -hd), z)
    return f


def ear_level(c, ha, ht):
    a = Vector((1.0, 0.0, -0.55)).normalized()
    t = Vector((0.0, 1.0, 0.0))
    def f(key):
        pos, side = key
        return tuple(Vector(c) + a * (ha if side == 'o' else -ha) + t * (ht if pos == 'b' else -ht))
    return f


def grow(bm, faces, slots, levels):
    """Extrude the region once per level; each new vertex keeps the slot of the vertex it came from."""
    for lev in levels:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            key = min(slots, key=lambda k_: (slots[k_].co - v.co).length)
            new[key] = v
        assert len(new) == len(slots), 'grow: slot clash'
        for key, v in new.items():
            v.co = Vector(lev(key))
        slots, faces = new, r['faces']
    return slots, faces


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, section(*r)) for r in RINGS]
    segs = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0])
    cap(bm, rings[-1])
    # front leg from the lower-side faces of R6-R8
    sl = {('b', 'o'): rings[6][3], ('b', 'i'): rings[6][4], ('m', 'o'): rings[7][3], ('m', 'i'): rings[7][4],
          ('f', 'o'): rings[8][3], ('f', 'i'): rings[8][4]}
    grow(bm, [segs[6][3], segs[7][3]], sl, [
        leg_level(J['elbowL'], 0.068, 0.052), leg_level(J['wristL'], 0.040, 0.034),
        leg_level(J['fetlockL'], 0.036, 0.031), leg_level(J['hoofL'], 0.056, 0.038)])
    # hind leg from R1-R3
    sl = {('b', 'o'): rings[1][3], ('b', 'i'): rings[1][4], ('m', 'o'): rings[2][3], ('m', 'i'): rings[2][4],
          ('f', 'o'): rings[3][3], ('f', 'i'): rings[3][4]}
    grow(bm, [segs[1][3], segs[2][3]], sl, [
        leg_level(J['hockL'], 0.072, 0.050), leg_level(J['cannonL'], 0.044, 0.034),
        leg_level(J['hfetlockL'], 0.036, 0.031), leg_level(J['hhoofL'], 0.056, 0.037)])
    # ear from the upper-side face between R9 and R10
    sl = {('b', 'i'): rings[9][1], ('b', 'o'): rings[9][2], ('f', 'i'): rings[10][1], ('f', 'o'): rings[10][2]}
    grow(bm, [segs[9][1]], sl, [
        ear_level((0.14, -0.255, 0.80), 0.056, 0.028), ear_level((0.182, -0.275, 0.848), 0.044, 0.014),
        ear_level((0.21, -0.305, 0.885), 0.008, 0.005)])
    snap_seam(bm)
    return object_from_bm('body', bm)


def R(i, j):
    """Stage-1 position of vertex j of ring i."""
    return section(*RINGS[i])[j]


def mid(*pts):
    return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))


def stage2(k, body):
    bm = edit(body)
    fl1 = leg_level(J['elbowL'], 0.068, 0.052)(('m', 'o'))
    hl1 = leg_level(J['hockL'], 0.072, 0.050)(('m', 'o'))
    with k.topo(bm, 'loop', 'upper foreleg loop: shoulder/elbow bend support'):
        loopcut(bm, edge_near(bm, mid(R(7, 3), fl1)), t=0.5)
    with k.topo(bm, 'loop', 'upper hind-leg loop: hip/stifle bend support'):
        loopcut(bm, edge_near(bm, mid(R(2, 3), hl1)), t=0.5)
    eyef = face_near(bm, mid(R(11, 1), R(11, 2), R(12, 1), R(12, 2)), n=(1, 0, 0))
    with k.topo(bm, 'inset', 'eye socket in the side plane of the muzzle, under the brow'):
        eye_in = inset(bm, [eyef], 0.58, -0.010)
    nf = face_near(bm, mid(*section(*RINGS[14])), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'nostril in the snout disc'):
        inset(bm, [nf], 0.62, -0.012)
    bm.verts.ensure_lookup_table()
    # brow overhangs the socket; jowls bulge; the disc gets a lip; the belly tucks toward the flank
    move([vert_near(bm, R(11, 1))], (0.014, 0.0, 0.012))
    move([vert_near(bm, R(10, 3))], (0.016, 0.0, 0.0))
    move([vert_near(bm, R(11, 3))], (0.014, 0.0, -0.004))
    for j in (1, 2, 3, 4):
        v = vert_near(bm, R(13, j)); v.co.x *= 0.90
    move([vert_near(bm, R(4, 4)), vert_near(bm, R(4, 5))], (0, 0, 0.02))
    commit(body, bm)
    bm.free()


PAL = {'brown': '#6f5040', 'bristle': '#3e2c24', 'snout': '#b88e7e', 'tusk': '#efe3c8',
       'hoof': '#2a201c', 'eye': '#1a1414'}


def zt_at(y):
    """Top-seam height of the locked base at y (linear between rings)."""
    rs = sorted((r[0], r[1]) for r in RINGS)
    for (y0, z0), (y1, z1) in zip(rs, rs[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return rs[0][1] if y < rs[0][0] else rs[-1][1]


def tube(bm, path, radii, n=4, apex=None, spin=45.0):
    """A closed low-poly tube along path; start capped, end capped or fanned to apex."""
    rings_ = []
    for i, p in enumerate(path):
        p = Vector(p)
        t = (Vector(path[min(i + 1, len(path) - 1)]) - Vector(path[max(i - 1, 0)])).normalized()
        a = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 0, 1))
        u = t.cross(a).normalized(); w = t.cross(u).normalized()
        pts = []
        for j in range(n):
            ang = math.radians(spin + 360.0 * j / n)
            pts.append(p + (u * math.cos(ang) + w * math.sin(ang)) * radii[i])
        rings_.append(ring(bm, pts))
    for a_, b_ in zip(rings_, rings_[1:]):
        bridge(bm, a_, b_, closed=True)
    cap(bm, list(reversed(rings_[0])))
    if apex is None:
        cap(bm, rings_[-1])
    else:
        tip = bm.verts.new(Vector(apex))
        last = rings_[-1]
        for j in range(n):
            bm.faces.new([last[j], last[(j + 1) % n], tip])
    return rings_


def solid(name, key, build, mirror):
    bm = bmesh.new()
    build(bm)
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: PAL[key]}, lambda c, n, i: key)
    return ob


def body_rule(c, n, i):
    if c.y < -0.628:
        return 'snout'
    if c.z < 0.05 and abs(c.x) > 0.04:
        return 'hoof'
    if -0.22 < c.y < 0.0 and c.z > 0.66:
        return 'bristle'
    return 'brown'


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('brown', 'bristle', 'snout', 'hoof')}, body_rule)
    pieces = []
    # eye: a small lens in the socket, back point in the socket floor, front point proud
    bm = edit(body)
    f = face_near(bm, mid(R(11, 1), R(11, 2), R(12, 1), R(12, 2)), n=(1, 0, 0))
    c, nrm = f.calc_center_median(), f.normal.copy()
    bm.free()
    if nrm.x < 0:
        nrm = -nrm
    u = nrm.cross(Vector((0, 0, 1))).normalized(); w = u.cross(nrm).normalized()
    def eye(bm):
        rim = ring(bm, [c + nrm * 0.004 + (u * math.cos(a) * 0.020 + w * math.sin(a) * 0.014)
                        for a in [math.radians(30 + 60 * j) for j in range(6)]])
        front = bm.verts.new(c + nrm * 0.011); back = bm.verts.new(c - nrm * 0.006)
        for j in range(6):
            bm.faces.new([rim[j], rim[(j + 1) % 6], front]); bm.faces.new([rim[(j + 1) % 6], rim[j], back])
    pieces.append(solid('eye', 'eye', eye, True))
    # tusks: from inside the lower jaw, curving out and up
    pieces.append(solid('tusk', 'tusk', lambda bm: tube(
        bm, [(0.050, -0.545, 0.300), (0.100, -0.560, 0.328), (0.140, -0.566, 0.378), (0.156, -0.560, 0.430)],
        [0.024, 0.022, 0.017, 0.011], n=4, apex=(0.152, -0.550, 0.472)), True))
    # crest: blunt clumps from the nape to mid-back, bases sunk in the ridge
    def crest(bm):
        for y, h in [(-0.30, 0.055), (-0.22, 0.075), (-0.14, 0.085), (-0.06, 0.08), (0.02, 0.065), (0.10, 0.05), (0.18, 0.035)]:
            y0, y1 = y - 0.039, y + 0.039
            b = ring(bm, [(-0.040, y0, zt_at(y0) - 0.040), (0.040, y0, zt_at(y0) - 0.040),
                          (0.040, y1, zt_at(y1) - 0.040), (-0.040, y1, zt_at(y1) - 0.040)])
            t = ring(bm, [(-0.012, y + 0.058, zt_at(y) + h), (0.012, y + 0.058, zt_at(y) + h)])
            bm.faces.new([b[3], b[2], b[1], b[0]])
            bm.faces.new([b[0], b[1], t[1], t[0]])
            bm.faces.new([b[2], b[3], t[0], t[1]])
            bm.faces.new([b[1], b[2], t[1]])
            bm.faces.new([b[3], b[0], t[0]])
    pieces.append(solid('crest', 'bristle', crest, False))
    # tail: a thin whip from inside the rump, tufted end
    bm = bmesh.new()
    tube(bm, [(0.0, 0.540, 0.505), (0.0, 0.585, 0.480), (0.0, 0.608, 0.405), (0.0, 0.618, 0.345), (0.0, 0.624, 0.295)],
         [0.015, 0.012, 0.009, 0.020, 0.017], n=4, apex=(0.0, 0.628, 0.245))
    tail = object_from_bm('tail', bm, mirror=False)
    paint(tail, {'brown': PAL['brown'], 'bristle': PAL['bristle']}, lambda c, n, i: 'bristle' if c.z < 0.37 else 'brown')
    pieces.append(tail)
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hip'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('neck', J['chest'], (0.0, -0.24, 0.61), 'spine', True),
        ('head', (0.0, -0.24, 0.61), (0.0, -0.62, 0.40), 'neck', True),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'spine'),
        ('forearm.L', J['elbowL'], J['fetlockL'], 'upperarm.L', True),
        ('fhoof.L', J['fetlockL'], J['hoofL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['hockL'], 'hips'),
        ('shank.L', J['hockL'], J['hfetlockL'], 'thigh.L', True),
        ('hhoof.L', J['hfetlockL'], J['hhoofL'], 'shank.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: sniffing and rooting (head dips, snout works side to side)
    clip(rig, 'idle', {1: {}, 12: {'neck': (-5, 0, 0), 'head': (-10, 0, 3)},
                       24: {'neck': (-9, 0, 0), 'head': (-20, 0, -3)},
                       32: {'neck': (-9, 0, 0), 'head': (-14, 0, 3)},
                       40: {'neck': (-4, 0, 0), 'head': (-8, 0, 0)}, 48: {}})
    # move: trot, diagonal pairs (FL+HR / FR+HL)
    A = {'upperarm.L': (18, 0, 0), 'upperarm.R': (-16, 0, 0), 'thigh.R': (16, 0, 0), 'thigh.L': (-16, 0, 0)}
    B = {'upperarm.L': (-16, 0, 0), 'upperarm.R': (18, 0, 0), 'thigh.R': (-16, 0, 0), 'thigh.L': (16, 0, 0)}
    LA = {'forearm.R': (-30, 0, 0), 'shank.L': (22, 0, 0), 'head': (-3, 0, 0)}
    LB = {'forearm.L': (-30, 0, 0), 'shank.R': (22, 0, 0), 'head': (-3, 0, 0)}
    clip(rig, 'move', {1: A, 7: LA, 13: B, 19: LB, 25: A})
    # attack: head down charge, then a tusk toss
    clip(rig, 'attack', {1: {},
                         8: {'neck': (-8, 0, 0), 'head': (-18, 0, 0), 'upperarm.L': (-10, 0, 0), 'upperarm.R': (-10, 0, 0)},
                         14: {'neck': (-10, 0, 0), 'head': (-22, 0, 0), 'upperarm.L': (14, 0, 0), 'upperarm.R': (14, 0, 0),
                              'thigh.L': (-12, 0, 0), 'thigh.R': (-12, 0, 0)},
                         19: {'neck': (6, 0, 0), 'head': (18, 0, -8), 'upperarm.L': (6, 0, 0), 'upperarm.R': (6, 0, 0)},
                         25: {'neck': (2, 0, 0), 'head': (6, 0, 0)}, 32: {}},
         loc={1: {}, 8: {'hips': (0, -0.02, 0)}, 14: {'hips': (0, 0.06, 0)}, 19: {'hips': (0, 0.05, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
