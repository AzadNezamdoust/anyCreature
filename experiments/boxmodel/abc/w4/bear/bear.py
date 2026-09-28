import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='bear', model='opus')
# the eye socket should stay dented in, not be turned into a ridge
META['keep_valleys'] = lambda c: -0.59 < c.y < -0.49 and 0.6 < c.z < 0.8 and c.x > 0.05

# the skeleton the model is built on (x >= 0 half; -Y forward, Z up)
J = dict(
    pelvis=(0.0, 0.47, 0.70), spine=(0.0, 0.18, 0.78), chest=(0.0, -0.08, 0.80),
    neck=(0.0, -0.24, 0.74), head=(0.0, -0.42, 0.70), snout=(0.0, -0.68, 0.60),
    tail0=(0.0, 0.64, 0.66), tail1=(0.0, 0.72, 0.57),
    shoulder=(0.20, -0.04, 0.62), elbow=(0.20, 0.00, 0.30), wrist=(0.20, -0.03, 0.08), fpaw=(0.20, -0.19, 0.02),
    hip=(0.19, 0.48, 0.62), knee=(0.19, 0.47, 0.26), ankle=(0.19, 0.56, 0.08), hpaw=(0.19, 0.37, 0.02),
)

# half-ring profiles: 6 verts (10-sided sections) from the top seam to the bottom seam, (x as fraction of w, z as fraction top..bottom)
HEAD = [(0, 1), (0.62, 0.95), (1.0, 0.55), (0.8, 0.12), (0.4, 0.0), (0, 0.0)]
TORSO = [(0, 1), (0.45, 0.93), (1.0, 0.38), (0.92, 0.05), (0.28, 0.02), (0, 0.0)]
MID = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(HEAD, TORSO)]

# rings nose -> tail: (y, top z, bottom z, half width, profile)
RINGS = [
    (-0.705, 0.640, 0.545, 0.058, HEAD),   # 0 nose pad
    (-0.650, 0.690, 0.512, 0.070, HEAD),   # 1 muzzle
    (-0.585, 0.712, 0.500, 0.078, HEAD),   # 2 stop
    (-0.500, 0.830, 0.505, 0.150, HEAD),   # 3 brow / eye
    (-0.410, 0.862, 0.510, 0.175, HEAD),   # 4 skull back / ears
    (-0.310, 0.880, 0.500, 0.200, MID),    # 5 neck
    (-0.210, 0.930, 0.440, 0.270, TORSO),  # 6 chest / shoulder front
    (-0.120, 0.985, 0.320, 0.320, TORSO),  # 7 front leg front
    (-0.020, 0.998, 0.310, 0.330, TORSO),  # 8 hump
    (0.080, 0.945, 0.315, 0.330, TORSO),   # 9 front leg back
    (0.360, 0.914, 0.290, 0.315, TORSO),   # 10 hind leg front
    (0.490, 0.870, 0.300, 0.320, TORSO),   # 11 hip
    (0.610, 0.780, 0.340, 0.280, TORSO),   # 12 hind leg back
    (0.665, 0.720, 0.460, 0.190, TORSO),   # 13 rump
    (0.715, 0.610, 0.520, 0.050, HEAD),    # 14 tail stub
]

# leg segments below the body: (z, y front, y back, x outer, x inner)
FRONT = [(0.24, -0.130, 0.110, 0.305, 0.095), (0.15, -0.118, 0.080, 0.285, 0.112),
         (0.08, -0.110, 0.055, 0.270, 0.130), (0.035, -0.200, 0.035, 0.285, 0.110),
         (0.0, -0.230, 0.005, 0.280, 0.115)]
HIND = [(0.22, 0.365, 0.620, 0.300, 0.095), (0.13, 0.425, 0.625, 0.282, 0.112),
        (0.075, 0.460, 0.625, 0.265, 0.130), (0.035, 0.350, 0.620, 0.280, 0.115),
        (0.0, 0.330, 0.600, 0.275, 0.120)]


def half_ring(bm, y, top, bot, w, prof):
    H = top - bot
    return ring(bm, [(xf * w, y, bot + zf * H) for xf, zf in prof])


def shared_face(*vs):
    s = set(vs[0].link_faces)
    for v in vs[1:]:
        s &= set(v.link_faces)
    return next(iter(s))


def leg(bm, R, a, b, c, segs):
    keys = [(a, 3, 'f', 'o'), (a, 4, 'f', 'i'), (b, 3, 'm', 'o'), (b, 4, 'm', 'i'), (c, 3, 'b', 'o'), (c, 4, 'b', 'i')]
    cur = {(p, s): R[i][j] for i, j, p, s in keys}
    faces = [shared_face(R[a][3], R[a][4], R[b][3], R[b][4]), shared_face(R[b][3], R[b][4], R[c][3], R[c][4])]
    for z, yf, yb, xo, xi in segs:
        e = extrude(bm, faces)
        new = {}
        for key, v in cur.items():
            new[key] = min(e['verts'], key=lambda w: (w.co - v.co).length)
        for (p, s), v in new.items():
            y = {'f': yf, 'b': yb, 'm': (yf + yb) / 2}[p]
            x = xo if s == 'o' else xi
            if p == 'm':
                x += 0.018 if s == 'o' else -0.012
            v.co = Vector((x, y, z))
        faces, cur = e['faces'], new
    return cur


def ear(bm, R):
    f = shared_face(R[3][1], R[3][2], R[4][1], R[4][2])
    e = extrude(bm, [f])
    # round ear on the top corner of the skull: mostly up, a little out, thin front-to-back
    move(e['verts'], (0.03, 0.012, 0.045))
    scale(e['verts'], (1.0, 0.75, 1.0))
    e2 = extrude(bm, e['faces'])
    move(e2['verts'], (0.016, 0.0, 0.03))
    scale(e2['verts'], (0.8, 0.85, 0.6))


def stage1(k):
    bm = bmesh.new()
    R = [half_ring(bm, *r) for r in RINGS]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    cap(bm, R[0])
    cap(bm, R[-1])
    bm.normal_update()
    recalc_normals(bm)
    leg(bm, R, 7, 8, 9, FRONT)
    leg(bm, R, 10, 11, 12, HIND)
    bm.normal_update()
    ear(bm, R)
    snap_seam(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    # brow: the skull ring's upper corner comes forward over the eye; the forehead with it
    vert_near(bm, (0.0925, -0.50, 0.81)).co.y -= 0.022
    vert_near(bm, (0.0, -0.50, 0.83)).co.y -= 0.012
    # chest keel: the breast seam drops and comes forward, the throat with it (a V from the front)
    v = vert_near(bm, (0.0, -0.21, 0.44)); v.co.y -= 0.03; v.co.z -= 0.045
    v = vert_near(bm, (0.0756, -0.21, 0.4426)); v.co.y -= 0.012; v.co.z -= 0.012
    vert_near(bm, (0.0, -0.31, 0.50)).co.z -= 0.015
    # broad dished face: cheek corners of rings 3-4 out, muzzle sides one flat plane each
    for p, dx in (((0.150, -0.50, 0.6835), 0.018), ((0.175, -0.41, 0.6901), 0.012)):
        vert_near(bm, p).co.x += dx
    side = [v for v in bm.verts if v.co.y < -0.58 and v.co.x > 0.03 and 0.53 < v.co.z < 0.70]
    flatten(side)
    # shoulder mass over the foreleg: widest verts of rings 7-9 out and down a touch (the upper-arm plane),
    # the hip corner of ring 11 out for the thigh
    for v in bm.verts:
        if -0.13 < v.co.y < 0.09 and v.co.x > 0.30 and 0.5 < v.co.z < 0.65:
            v.co.x += 0.018; v.co.z -= 0.02
        if 0.48 < v.co.y < 0.50 and v.co.x > 0.30 and 0.5 < v.co.z < 0.65:
            v.co.x += 0.012
    # eye socket in the stop/cheek face under the brow
    eye_f = face_near(bm, (0.092, -0.54, 0.706), n=(1, 0, 0))
    with k.topo(bm, 'inset', 'eye socket under the brow'):
        inset(bm, [eye_f], 0.42, -0.012)
    commit(body, bm)


PAL = {'fur': '#6b4a33', 'dark': '#4a3222', 'chest': '#9c7a5a', 'muzzle': '#c9a57d', 'nose': '#1e1714'}


def socket(body):
    """Centre and normal of the inset eye face (the smallest face near the socket)."""
    bm = edit(body)
    p = Vector((0.092, -0.54, 0.70))
    cand = [f for f in bm.faces if (f.calc_center_median() - p).length < 0.05 and f.normal.x > 0.3]
    f = min(cand, key=lambda f: f.calc_area())
    c, n = f.calc_center_median().copy(), f.normal.copy()
    bm.free()
    return c, n


def body_rule(eye_c):
    def rule(c, n, i):
        if c.y < -0.69:
            return 'nose'
        if c.y < -0.585:
            return 'muzzle'
        if (Vector((abs(c.x), c.y, c.z)) - eye_c).length < 0.035:
            return 'dark'
        if -0.34 < c.y < -0.1 and n.y < -0.25 and 0.34 < c.z < 0.64 and abs(c.x) < 0.2:
            return 'chest'
        if c.z < 0.2 or n.z < -0.6:
            return 'dark'
        return 'fur'
    return rule


def eye_piece(c, n):
    """A small faceted lens sitting in the socket, proud of the socket floor."""
    bm = bmesh.new()
    t = n.cross(Vector((0, 0, 1))).normalized()
    u = n.cross(t).normalized()
    ctr = c + n * 0.004
    rim = ring(bm, [ctr + (t * math.cos(a) * 0.017 + u * math.sin(a) * 0.021) for a in
                    [i * math.pi / 3 for i in range(6)]])
    front = ring(bm, [ctr + n * 0.012])[0]
    back = ring(bm, [ctr - n * 0.010])[0]
    for i in range(6):
        bm.faces.new([rim[i], rim[(i + 1) % 6], front])
        bm.faces.new([rim[(i + 1) % 6], rim[i], back])
    ob = object_from_bm('eye', bm, mirror=True)
    paint(ob, {'eye': '#151010'}, lambda c_, n_, i_: 'eye')
    return ob


def claws(name, xs, base_y, tip_y, fwd):
    """Four hooked claw wedges per paw; the base sits inside the toe, the tip hooks down in front."""
    bm = bmesh.new()
    for x in xs:
        b = ring(bm, [(x - 0.013, base_y, 0.008), (x + 0.013, base_y, 0.008),
                      (x + 0.011, base_y, 0.030), (x - 0.011, base_y, 0.030)])
        m = ring(bm, [(x - 0.008, base_y + fwd * 0.035, 0.010), (x + 0.008, base_y + fwd * 0.035, 0.010),
                      (x + 0.006, base_y + fwd * 0.035, 0.024), (x - 0.006, base_y + fwd * 0.035, 0.024)])
        tip = ring(bm, [(x, tip_y, 0.003)])[0]
        bm.faces.new(list(reversed(b)))
        bridge(bm, b, m, closed=True)
        for i in range(4):
            bm.faces.new([m[i], m[(i + 1) % 4], tip])
    ob = object_from_bm(name, bm, mirror=True)
    paint(ob, {'claw': '#2a221e'}, lambda c_, n_, i_: 'claw')
    return ob


def stage3(k, body):
    c, n = socket(body)
    paint(body, PAL, body_rule(c))
    eye = eye_piece(c, n)
    fc = claws('claws_front', (0.135, 0.175, 0.215, 0.255), -0.200, -0.262, -1)
    hc = claws('claws_hind', (0.140, 0.178, 0.216, 0.254), 0.352, 0.300, -1)
    return [eye, fc, hc]


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['snout'], 'neck', True),
        ('tail', J['tail0'], J['tail1'], 'hips'),
        ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('fpaw.L', J['wrist'], J['fpaw'], 'forearm.L', True),
        ('thigh.L', J['hip'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
        ('hpaw.L', J['ankle'], J['hpaw'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: slow breath in the chest, the head lifts to sniff twice
    clip(rig, 'idle', {1: {}, 12: {'spine': (1.5, 0, 0), 'neck': (-3, 0, 0), 'head': (-8, 0, 0)},
                       24: {'spine': (0, 0, 0), 'head': (3, 0, 0)},
                       36: {'spine': (1.5, 0, 0), 'neck': (-2, 0, 2), 'head': (-6, 0, 3)}, 48: {}})
    # move: heavy diagonal walk, front L with hind R; the swinging paw folds back
    A, B = 14, 12
    def walk(s, lift_l, lift_r):
        return {'upperarm.L': (A * s, 0, 0), 'upperarm.R': (-A * s, 0, 0),
                'thigh.L': (-B * s, 0, 0), 'thigh.R': (B * s, 0, 0),
                'forearm.L': (-lift_l, 0, 0), 'forearm.R': (-lift_r, 0, 0),
                'shin.L': (-lift_r * 0.6, 0, 0), 'shin.R': (-lift_l * 0.6, 0, 0),
                'chest': (0, 0, 3 * s), 'hips': (0, 0, -2 * s), 'head': (0, 0, -3 * s)}
    clip(rig, 'move', {1: walk(1, 0, 0), 9: walk(0, 0, 28), 17: walk(-1, 0, 0), 25: walk(0, 28, 0), 33: walk(1, 0, 0)})
    # attack: rear back, raise the left paw, swipe across and down, recover
    clip(rig, 'attack', {
        1: {},
        12: {'spine': (7, 0, 0), 'chest': (5, 0, 0), 'neck': (4, 0, 0), 'head': (6, 0, 0),
             'upperarm.L': (42, 0, 0), 'forearm.L': (28, 0, 0), 'fpaw.L': (-30, 0, 0)},
        20: {'spine': (-4, 0, 0), 'chest': (-3, 0, -4), 'neck': (-5, 0, 0), 'head': (-6, 0, 0),
             'upperarm.L': (24, 0, 16), 'forearm.L': (8, 0, 0), 'fpaw.L': (-10, 0, 0)},
        30: {'spine': (-2, 0, 0), 'head': (-3, 0, 0), 'upperarm.L': (4, 0, 4)},
        40: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
