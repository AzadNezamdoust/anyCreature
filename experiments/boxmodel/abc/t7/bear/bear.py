import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(_HERE, '..', '..', '..', 'kit')))
from bmkit import *

META = dict(creature='bear', model='opus',
            keep_valleys=lambda c: 0.13 < abs(c.x) < 0.23 and -0.66 < c.y < -0.52 and 0.52 < c.z < 0.73)

# the skeleton the model is built on (left side, x >= 0)
J = dict(
    hip=(0.0, 0.46, 0.74), spine=(0.0, 0.10, 0.78), chest=(0.0, -0.18, 0.80),
    neck=(0.0, -0.34, 0.74), head=(0.0, -0.47, 0.66), snout=(0.0, -0.86, 0.54),
    tail=(0.0, 0.76, 0.70), tail_end=(0.0, 0.86, 0.70),
    shoulderL=(0.22, -0.17, 0.72), elbowL=(0.23, -0.15, 0.40), wristL=(0.23, -0.20, 0.10),
    fpawL=(0.23, -0.32, 0.03),
    hipL=(0.22, 0.47, 0.72), kneeL=(0.23, 0.42, 0.40), hockL=(0.23, 0.52, 0.11),
    hpawL=(0.23, 0.36, 0.03),
)

HZ = -0.09   # head drop: the head is carried low

# half rings, front (nose) to back (tail): (y, [top, upper, side, low, bottom] as (x, z))
RINGS = [
    (-0.85, [(0, 0.600), (0.070, 0.595), (0.085, 0.545), (0.065, 0.495), (0, 0.485)]),  # 0 nose pad
    (-0.79, [(0, 0.625), (0.085, 0.615), (0.100, 0.550), (0.080, 0.490), (0, 0.470)]),  # 1 muzzle
    (-0.71, [(0, 0.655), (0.100, 0.645), (0.120, 0.560), (0.095, 0.485), (0, 0.465)]),  # 2 stop
    (-0.64, [(0, 0.780), (0.140, 0.760), (0.195, 0.645), (0.130, 0.515), (0, 0.485)]),  # 3 brow / eye
    (-0.54, [(0, 0.820), (0.150, 0.800), (0.215, 0.670), (0.150, 0.525), (0, 0.495)]),  # 4 skull, cheek
    (-0.45, [(0, 0.800), (0.150, 0.790), (0.205, 0.650), (0.160, 0.495), (0, 0.465)]),  # 5 back of skull
    (-0.36, [(0, 0.790), (0.200, 0.775), (0.270, 0.66), (0.210, 0.490), (0, 0.435)]),  # 6 neck / chest
    (-0.28, [(0, 0.945), (0.210, 0.915), (0.300, 0.72), (0.240, 0.480), (0, 0.380)]),  # 7 foreleg front
    (-0.18, [(0, 1.000), (0.225, 0.960), (0.340, 0.72), (0.250, 0.470), (0, 0.365)]),  # 8 hump
    (-0.08, [(0, 0.965), (0.230, 0.920), (0.330, 0.71), (0.250, 0.470), (0, 0.385)]),  # 9 foreleg back
    (0.12, [(0, 0.865), (0.230, 0.842), (0.315, 0.69), (0.250, 0.535), (0, 0.490)]),   # 10 belly
    (0.34, [(0, 0.845), (0.230, 0.830), (0.320, 0.70), (0.240, 0.505), (0, 0.470)]),   # 11 hindleg front
    (0.48, [(0, 0.865), (0.225, 0.845), (0.335, 0.69), (0.240, 0.490), (0, 0.440)]),   # 12 hip
    (0.62, [(0, 0.845), (0.200, 0.825), (0.280, 0.69), (0.220, 0.500), (0, 0.460)]),   # 13 hindleg back
    (0.76, [(0, 0.790), (0.140, 0.770), (0.190, 0.67), (0.140, 0.560), (0, 0.520)]),   # 14 rump
    (0.84, [(0, 0.750), (0.050, 0.745), (0.065, 0.70), (0.050, 0.650), (0, 0.640)]),   # 15 tail stub
]

# leg sections: (z, cx, cy, half-width x, half-depth y, side bulge, tilt)
FORE = [
    (0.40, 0.225, -0.170, 0.100, 0.115, 1.12, 0.00),
    (0.24, 0.228, -0.185, 0.090, 0.100, 1.12, 0.00),
    (0.11, 0.230, -0.205, 0.075, 0.080, 1.10, 0.00),
    (0.06, 0.232, -0.245, 0.095, 0.125, 1.08, 0.015),
    (0.00, 0.232, -0.245, 0.097, 0.128, 1.08, 0.00),
]
HIND = [
    (0.42, 0.228, 0.455, 0.105, 0.150, 1.12, 0.00),
    (0.25, 0.230, 0.515, 0.090, 0.100, 1.12, 0.00),
    (0.11, 0.232, 0.550, 0.075, 0.080, 1.10, 0.00),
    (0.06, 0.234, 0.475, 0.093, 0.155, 1.08, 0.015),
    (0.00, 0.234, 0.475, 0.095, 0.158, 1.08, 0.00),
]


def _section(vs, z, cx, cy, w, d, bul, tilt):
    c = centre(vs)
    for v in vs:
        ox = 1 if v.co.x > c.x else -1
        dy = v.co.y - c.y
        oy = 0 if abs(dy) < 0.02 else (1 if dy > 0 else -1)
        v.co = V(cx + ox * w * (bul if oy == 0 else 1.0), cy + oy * d, z + oy * tilt)


def leg(bm, faces, steps):
    reg = faces
    for s in steps:
        r = extrude(bm, reg)
        _section(r['verts'], *s)
        reg = r['faces']
    return reg


def ear(bm, face):
    r = extrude(bm, [face])
    vs = r['verts']
    c = centre(vs)
    for v in vs:     # one round ear on the skull corner, facing forward
        outer, front = v.co.x > c.x, v.co.y < c.y
        v.co = V(0.236 if outer else 0.140, (-0.538 if front else -0.455) + (0.004 if outer else 0.0),
                 (0.735 if outer else 0.765) + HZ + 0.09)
    r2 = extrude(bm, r['faces'])
    vs = r2['verts']
    c = centre(vs)
    for v in vs:
        v.co = c + (v.co - c) * V(0.70, 0.82, 0.50) + V(0.006, 0.004, 0.030)


def stage1(k):
    bm = bmesh.new()
    R = []
    for i, (y, pts) in enumerate(RINGS):
        dz = HZ if i <= 5 else 0.0
        R.append(ring(bm, [(x, y, z + dz) for x, z in pts]))
    F = [bridge(bm, R[i], R[i + 1]) for i in range(len(R) - 1)]
    cap(bm, R[0]); cap(bm, R[-1])
    leg(bm, [F[7][2], F[8][2]], FORE)
    leg(bm, [F[11][2], F[12][2]], HIND)
    ear(bm, F[4][1])
    snap_seam(bm)
    return object_from_bm('body', bm)


EYE_FACE = (0.175, -0.59, 0.629)      # centre of the upper-side face between R3 and R4 (brow to cheek)


def stage2(k, body):
    bm = edit(body)
    f = face_near(bm, EYE_FACE, n=(1, 0, 0.2))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the brow-cheek face'):
        inner = inset(bm, [f], 0.42, 0.0)
    n = inner[0].normal.copy()
    move(inner[0].verts, -n * 0.014)
    # brow ridge: the R3 top and upper verts overhang the socket
    for v in verts_where(bm, lambda c: abs(c.y + 0.64) < 0.005 and c.z > 0.64 and c.x < 0.16):
        v.co += V(0, -0.018, 0.012)
    commit(body, bm)


PAL = {'fur': '#6b4a33', 'dark': '#4a3222', 'muzzle': '#c9a57d', 'nose': '#1e1714',
       'claw': '#2a221e', 'eye': '#151010', 'chest': '#8a6243'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.845:
        return 'nose'
    if y < -0.70:
        return 'muzzle'
    if z < 0.24:
        return 'dark'
    if -0.47 < y < -0.24 and n.y < -0.1 and z < 0.66 and x < 0.22:
        return 'chest'
    return 'fur'


def _box_half(bm, x1, y0, y1, z0, z1, taper=0.0):
    """A half box from the seam (x = 0) to x1: no face on the seam plane (the mirror closes it)."""
    a = ring(bm, [(0, y0, z0), (x1, y0 + taper, z0), (x1, y0 + taper, z1), (0, y0, z1)])
    b = ring(bm, [(0, y1, z0), (x1, y1, z0), (x1, y1, z1), (0, y1, z1)])
    bm.faces.new([a[0], a[1], a[2], a[3]][::-1]); bm.faces.new([b[0], b[1], b[2], b[3]])
    bm.faces.new([a[1], b[1], b[2], a[2]]); bm.faces.new([a[0], b[0], b[1], a[1]]); bm.faces.new([a[3], a[2], b[2], b[3]])


def _claw(bm, x, y, z, fwd):
    w, h = 0.018, 0.015
    base = ring(bm, [(x - w, y, z), (x + w, y, z), (x + w * 0.8, y, z + h * 2), (x - w * 0.8, y, z + h * 2)])
    back = ring(bm, [(v.co.x, y - fwd * 0.012, v.co.z) for v in base])
    tip = bm.verts.new((x, y + fwd * 0.060, z - 0.006))
    bridge(bm, back, base, closed=True)
    cap(bm, back[::-1])
    for i in range(4):
        bm.faces.new([base[i], base[(i + 1) % 4], tip])


def stage3(k, body):
    paint(body, PAL, body_rule)
    pieces = []
    # eyes: a low hexagonal lens proud of the socket floor
    bm0 = edit(body)
    f = face_near(bm0, EYE_FACE, n=(1, 0, 0.2))
    c, n = f.calc_center_median(), f.normal.copy()
    bm0.free()
    u = n.cross(V(0, 0, 1)).normalized(); w = n.cross(u).normalized()
    bm = bmesh.new()
    rim = ring(bm, [c + (u * math.cos(a) * 0.024 + w * math.sin(a) * 0.020) + n * 0.004
                    for a in [i * math.pi / 3 for i in range(6)]])
    front = bm.verts.new(c + n * 0.014); backv = bm.verts.new(c - n * 0.010)
    for i in range(6):
        bm.faces.new([rim[i], rim[(i + 1) % 6], front]); bm.faces.new([rim[(i + 1) % 6], rim[i], backv])
    eye = object_from_bm('eye', bm, mirror=True); paint(eye, {'eye': PAL['eye']}, lambda *a: 'eye')
    pieces.append(eye)
    # nose pad: a block on the muzzle front
    bm = bmesh.new()
    _box_half(bm, 0.052, -0.878, -0.842, 0.438, 0.508)
    nose = object_from_bm('nose', bm, mirror=True); paint(nose, {'nose': PAL['nose']}, lambda *a: 'nose')
    pieces.append(nose)
    # claws: four bold claws on each paw front
    bm = bmesh.new()
    for cx, fy in ((0.232, -0.362), (0.234, 0.325)):
        for dx in (-0.060, 0.0, 0.060):
            _claw(bm, cx + dx, fy, 0.009, -1)
    claws = object_from_bm('claws', bm, mirror=True); paint(claws, {'claw': PAL['claw']}, lambda *a: 'claw')
    pieces.append(claws)
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hip'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['snout'], 'neck', True),
        ('tail', J['tail'], J['tail_end'], 'hips'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hand.L', J['wristL'], J['fpawL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L', True),
        ('foot.L', J['hockL'], J['hpawL'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    A, H = 12, 10
    clip(rig, 'idle', {1: {}, 12: {'spine': (1.5, 0, 0), 'head': (-5, 0, 3)}, 24: {'spine': (2.5, 0, 0), 'neck': (3, 0, 0)},
                       36: {'spine': (1.5, 0, 0), 'head': (-5, 0, -3)}, 48: {}})
    st = lambda s: {'upperarm.L': (A * s, 0, 0), 'upperarm.R': (-A * s, 0, 0), 'thigh.L': (-H * s, 0, 0),
                    'thigh.R': (H * s, 0, 0), 'hips': (0, 0, 2 * s), 'head': (2 * s, 0, 0)}
    mid = lambda s: {'forearm.L': (-18 if s > 0 else 0, 0, 0), 'forearm.R': (-18 if s < 0 else 0, 0, 0),
                     'shin.L': (12 if s < 0 else 0, 0, 0), 'shin.R': (12 if s > 0 else 0, 0, 0)}
    clip(rig, 'move', {1: st(1), 9: mid(1), 17: st(-1), 25: mid(-1), 33: st(1)},
         loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0, 0.012)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0, 0.012)},
              33: {'hips': (0, 0, 0)}})
    clip(rig, 'attack', {1: {}, 12: {'chest': (-10, 0, 0), 'upperarm.L': (50, 0, -10), 'forearm.L': (15, 0, 0), 'head': (-8, 0, 0)},
                         20: {'chest': (4, 0, 0), 'upperarm.L': (-10, 0, 18), 'forearm.L': (-10, 0, 0), 'head': (6, 0, 0)},
                         28: {'upperarm.L': (-4, 0, 4)}, 40: {}},
         loc={1: {'hips': (0, 0, 0)}, 12: {'hips': (0, -0.02, 0)}, 20: {'hips': (0, 0.06, -0.02)}, 40: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
