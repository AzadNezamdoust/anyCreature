"""Stylised low-poly red deer stag, box-modelled in four stages (experiments/boxmodel/BRIEF.md).

One chain of 8-sided half rings (5 verts: dorsal seam, back corner, flank, keel/jaw corner,
ventral seam) runs nose -> skull -> upright neck (tilted rings) -> chest -> rump -> short tail.
Legs are 6-sided and extruded from two lower-flank quads each; the ears are leaf-shaped
(two extrusions) out of the skull's back-corner/flank quad. The antlers are stage-3 pieces
rigid to the head bone. Everything is placed from the joints in J.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='stag', model='opus', engine_glb='')

# the skeleton the model is built on (x, y, z); .L joints on +X
J = dict(
    hip=(0.0, 0.50, 1.08), spine=(0.0, 0.10, 1.06), chest=(0.0, -0.22, 1.08),
    neck=(0.0, -0.34, 1.16), neck1=(0.0, -0.45, 1.33), head=(0.0, -0.53, 1.50), snout=(0.0, -0.95, 1.28),
    tail0=(0.0, 0.76, 1.08), tail1=(0.0, 0.815, 1.02), tail2=(0.0, 0.83, 0.94),
    shoulderL=(0.185, -0.28, 1.00), elbowL=(0.180, -0.17, 0.62), kneeL=(0.170, -0.215, 0.40),
    ffetL=(0.165, -0.23, 0.11), fhoofL=(0.165, -0.26, 0.0),
    hipL=(0.185, 0.58, 1.02), stifleL=(0.190, 0.49, 0.69), hockL=(0.170, 0.655, 0.43),
    hfetL=(0.160, 0.605, 0.11), hhoofL=(0.160, 0.58, 0.0),
)

# ---------------------------------------------------------------- the head frame
# u runs from the nose tip back along the head axis, v is 'up' across it; the head is
# carried nose-down at HEAD_TILT degrees.
HEAD_N0 = (-0.90, 1.30)
HEAD_TILT = 30.0


def H(x, u, v):
    c, s = math.cos(math.radians(HEAD_TILT)), math.sin(math.radians(HEAD_TILT))
    return (x, HEAD_N0[0] + u * c - v * s, HEAD_N0[1] + u * s + v * c)


HEAD = [   # (u, [(x, v) x 5]): dorsal, back corner, flank, jaw corner, ventral
    (0.00, [(0, 0.030), (0.022, 0.026), (0.029, -0.004), (0.024, -0.032), (0, -0.040)]),    # nose pad
    (0.04, [(0, 0.042), (0.030, 0.037), (0.039, -0.004), (0.033, -0.043), (0, -0.052)]),
    (0.13, [(0, 0.058), (0.040, 0.053), (0.051, -0.004), (0.044, -0.056), (0, -0.066)]),    # muzzle
    (0.22, [(0, 0.086), (0.058, 0.080), (0.078, 0.006), (0.058, -0.072), (0, -0.084)]),     # eye front
    (0.29, [(0, 0.116), (0.074, 0.110), (0.124, 0.036), (0.080, -0.080), (0, -0.096)]),     # orbit / cheek
    (0.36, [(0, 0.122), (0.060, 0.120), (0.102, 0.038), (0.086, -0.098), (0, -0.112)]),     # skull, ear front
    (0.42, [(0, 0.090), (0.056, 0.090), (0.092, 0.025), (0.080, -0.128), (0, -0.138)]),     # poll, jaw angle
]


def tilt_ring(D, Vn, mids):
    """A tilted half ring from the dorsal point D=(y, z) to the ventral point Vn; mids = [(x, t)]."""
    pts = [(0.0, D[0], D[1])]
    for x, t in mids:
        pts.append((x, D[0] + (Vn[0] - D[0]) * t, D[1] + (Vn[1] - D[1]) * t))
    pts.append((0.0, Vn[0], Vn[1]))
    return pts


def tail_ring(c, d, rx, rz):
    dy, dz = d
    L = math.hypot(dy, dz); dy, dz = dy / L, dz / L
    uy, uz = -dz, dy
    if uz < 0:
        uy, uz = -uy, -uz
    y, z = c
    return [(0.0, y + uy * rz, z + uz * rz),
            (0.72 * rx, y + uy * 0.62 * rz, z + uz * 0.62 * rz),
            (rx, y - uy * 0.05 * rz, z - uz * 0.05 * rz),
            (0.72 * rx, y - uy * 0.66 * rz, z - uz * 0.66 * rz),
            (0.0, y - uy * rz, z - uz * rz)]


CHAIN = [[H(x, u, v) for x, v in ring_] for u, ring_ in HEAD] + [
    # upright neck: tilted rings, thick at the base
    tilt_ring((-0.470, 1.490), (-0.462, 1.265), [(0.075, 0.12), (0.118, 0.50), (0.088, 0.85)]),
    tilt_ring((-0.360, 1.370), (-0.490, 1.100), [(0.100, 0.12), (0.150, 0.50), (0.110, 0.85)]),
    # withers / point of the shoulder / breast
    tilt_ring((-0.230, 1.290), (-0.480, 0.930), [(0.130, 0.10), (0.185, 0.48), (0.120, 0.85)]),
    # chest: the foreleg comes out of rings 10-12 (flank -> keel corner); the keel is deepest at 11-12
    [(0, -0.12, 1.29), (0.140, -0.12, 1.25), (0.200, -0.20, 1.00), (0.130, -0.31, 0.74), (0, -0.36, 0.73)],
    [(0, -0.01, 1.27), (0.150, -0.01, 1.23), (0.205, -0.08, 0.98), (0.125, -0.17, 0.66), (0, -0.20, 0.64)],
    [(0, 0.10, 1.24), (0.155, 0.10, 1.20), (0.200, 0.05, 0.97), (0.115, -0.03, 0.65), (0, -0.05, 0.63)],
    [(0, 0.22, 1.21), (0.155, 0.22, 1.17), (0.195, 0.20, 0.97), (0.110, 0.13, 0.69), (0, 0.12, 0.67)],
    # ribs back, waist (tuck)
    [(0, 0.33, 1.18), (0.150, 0.33, 1.14), (0.185, 0.32, 0.98), (0.100, 0.29, 0.76), (0, 0.28, 0.75)],
    [(0, 0.42, 1.17), (0.135, 0.42, 1.13), (0.165, 0.42, 1.00), (0.090, 0.41, 0.88), (0, 0.41, 0.87)],
    # hip / haunch: the hind leg comes out of rings 16-18
    [(0, 0.50, 1.19), (0.140, 0.50, 1.15), (0.180, 0.49, 1.02), (0.100, 0.47, 0.88), (0, 0.47, 0.87)],
    [(0, 0.60, 1.19), (0.140, 0.60, 1.15), (0.180, 0.60, 1.00), (0.100, 0.59, 0.87), (0, 0.59, 0.86)],
    [(0, 0.69, 1.16), (0.120, 0.69, 1.12), (0.155, 0.70, 0.99), (0.085, 0.71, 0.88), (0, 0.71, 0.87)],
    # rump back (the pale patch plane)
    [(0, 0.75, 1.12), (0.080, 0.755, 1.09), (0.100, 0.765, 1.00), (0.050, 0.77, 0.92), (0, 0.77, 0.91)],
    # rump dome (stage-1 unlock, AD K=3 note 1): the old 3-ring tail curled into a shell with a
    # plate; the body now ends in a low rounded rump and the tail is a stage-3 wedge piece
    [(0, 0.775, 1.075), (0.075, 0.787, 1.052), (0.095, 0.797, 0.990), (0.048, 0.795, 0.928), (0, 0.788, 0.918)],
]

# chunky torso: widen the neck-base and body rings (front and top views read as a pencil otherwise)
for _i, _sx in zip(range(8, 20), (1.10, 1.18, 1.22, 1.22, 1.22, 1.22, 1.22, 1.22, 1.22, 1.22, 1.20, 1.15)):
    CHAIN[_i] = [(p[0] * _sx, p[1], p[2]) for p in CHAIN[_i]]

# stylised head (STYLE sec. 2: size it up): head rings 0-6 and the ear tip scale about the poll
HEAD_S, HEAD_P = (1.20, 1.20, 1.20), H(0.0, 0.42, -0.015)


def head_xf(p):
    return tuple(HEAD_P[i] + (p[i] - HEAD_P[i]) * HEAD_S[i] for i in range(3))


for _i in range(7):
    CHAIN[_i] = [head_xf(p) for p in CHAIN[_i]]

R_EAR = 5            # the ear comes out of head rings 5 -> 6, back corner -> flank
R_FORE = 10          # foreleg root: rings 10, 11, 12
R_HIND = 16          # hind leg root: rings 16, 17, 18
EAR_TIP = head_xf((0.255, -0.565, 1.665))


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def fore_sections():
    e, k, f, h = J['elbowL'], J['kneeL'], J['ffetL'], J['fhoofL']
    return [
        dict(c=(e[0], e[1], 0.60), w=0.055, d=0.085, ff=0.55, fb=0.25, mid=-0.2),   # elbow: point sticks back
        dict(c=(e[0] - 0.005, -0.200, 0.50), w=0.048, d=0.058, ff=0.60, fb=0.40),   # forearm
        dict(c=(k[0], k[1] + 0.003, 0.438), w=0.035, d=0.039, ff=0.60, fb=0.50),    # wrist above the knee
        dict(c=k, w=0.047, d=0.053, ff=0.60, fb=0.50),                              # knee (carpus): knobbly
        dict(c=(k[0] - 0.003, k[1] - 0.005, 0.34), w=0.030, d=0.032, ff=0.60, fb=0.45),  # cannon top
        dict(c=f, w=0.032, d=0.038, ff=0.60, fb=0.45),                              # fetlock
        dict(c=(h[0], h[1] + 0.005, 0.045), w=0.034, d=0.044, ff=0.65, fb=0.55, dir=(0, 0, -1)),  # hoof top
        dict(c=h, w=0.037, d=0.052, ff=0.65, fb=0.55, dir=(0, 0, -1)),              # sole
    ]


def hind_sections():
    s, hk, f, h = J['stifleL'], J['hockL'], J['hfetL'], J['hhoofL']
    return [
        dict(c=(0.180, 0.60, 0.82), w=0.078, d=0.155, ff=0.50, fb=0.70),          # haunch
        dict(c=(0.180, 0.575, 0.68), w=0.066, d=0.130, ff=0.55, fb=0.55),           # lower thigh: stifle in front, buttock behind
        dict(c=(0.172, 0.615, 0.55), w=0.045, d=0.060, ff=0.55, fb=0.45),    # gaskin
        dict(c=hk, w=0.036, d=0.056, ff=0.55, fb=0.30, mid=-0.3),                  # hock: point back
        dict(c=(hk[0] - 0.005, hk[1] - 0.01, 0.34), w=0.028, d=0.033, ff=0.60, fb=0.45),  # cannon top
        dict(c=f, w=0.030, d=0.036, ff=0.60, fb=0.45),                             # fetlock
        dict(c=(h[0], h[1] + 0.005, 0.045), w=0.033, d=0.042, ff=0.65, fb=0.55, dir=(0, 0, -1)),  # hoof top
        dict(c=h, w=0.036, d=0.050, ff=0.65, fb=0.55, dir=(0, 0, -1)),             # sole
    ]


# ---------------------------------------------------------------- helpers
def quad(*vs):
    s = set(vs[0].link_faces)
    for v in vs[1:]:
        s &= set(v.link_faces)
    assert len(s) == 1, 'quad lookup: %d faces' % len(s)
    return s.pop()


def hexagon(sec, bone_dir):
    """Six points of a limb section: rows o (outer) / i (inner), cols 0 front .. 2 back."""
    c = Vector(sec['c'])
    b = Vector(sec.get('dir', bone_dir)).normalized()
    f = Vector((0.0, b.z, -b.y))
    if f.y > 0:
        f = -f
    w, d = sec['w'], sec['d']
    ff, fb, mid = sec.get('ff', 0.55), sec.get('fb', 0.45), sec.get('mid', 0.0)
    X = Vector((1, 0, 0))
    return {('o', 0): c + X * (ff * w) + f * d, ('i', 0): c - X * (ff * w) + f * d,
            ('o', 1): c + X * w - f * (mid * d), ('i', 1): c - X * w - f * (mid * d),
            ('o', 2): c + X * (fb * w) - f * d, ('i', 2): c - X * (fb * w) - f * d}


def build_leg(bm, R, i0, secs):
    lab = {}
    for k in range(3):
        lab[('o', k)] = R[i0 + k][2]
        lab[('i', k)] = R[i0 + k][3]
    faces = [quad(R[i0 + k][2], R[i0 + k][3], R[i0 + k + 1][3], R[i0 + k + 1][2]) for k in range(2)]
    prev_c = centre(list(lab.values()))
    out = []
    for j, sec in enumerate(secs):
        pos = {k: v.co.copy() for k, v in lab.items()}
        r = extrude(bm, faces)
        lab = {}
        for v in r['verts']:
            k = min(pos, key=lambda q: (pos[q] - v.co).length)
            lab[k] = v
        faces = r['faces']
        assert not [e for e in bm.edges if not e.link_faces], 'extrude left loose edges'
        nxt = Vector(secs[j + 1]['c']) if j + 1 < len(secs) else Vector(sec['c']) + Vector((0, 0, -0.1))
        bone = (nxt - prev_c)
        bone.x = 0
        for k, p in hexagon(sec, bone).items():
            lab[k].co = p
        prev_c = Vector(sec['c'])
        out.append(dict(lab))
    return out


def build_ear(bm, R, i, tip, mid_t=0.42, widen=1.55, thin=0.45):
    """A leaf ear: the root quad is extruded to a wide, thin middle, then to a point."""
    f = quad(R[i][1], R[i][2], R[i + 1][2], R[i + 1][1])
    cb = f.calc_center_median()
    tip = Vector(tip)
    e = tip - cb
    L = e.length
    e.normalize()
    w = Vector((0, 1, 0)); w = (w - e * w.dot(e)).normalized()
    t = e.cross(w)
    r = extrude(bm, [f])
    for v in r['verts']:
        d = v.co - cb
        v.co = cb + e * (L * mid_t) + w * (d.dot(w) * widen) + t * (d.dot(t) * thin)
    r2 = extrude(bm, r['faces'])
    bmesh.ops.pointmerge(bm, verts=r2['verts'], merge_co=tip)


LEGS = {}      # stage-1 leg section positions, for finding edges in stage 2
EYE_SOCKET = []     # the stage-2 socket floor corners (the eye piece seats on them)
SOLE_LIFT = 0.006   # stage 2 lifts each leg's sole inside its hoof piece (no coplanar sole)


# ---------------------------------------------------------------- stage 1
def stage1(k):
    bm = bmesh.new()
    R = [ring(bm, pts) for pts in CHAIN]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    cap(bm, R[0])
    cap(bm, list(reversed(R[-1])))
    recalc_normals(bm)
    build_ear(bm, R, R_EAR, EAR_TIP)
    for name, i0, secs in (('fore', R_FORE, fore_sections()), ('hind', R_HIND, hind_sections())):
        labs = build_leg(bm, R, i0, secs)
        LEGS[name] = [{q: v.co.copy() for q, v in lab.items()} for lab in labs]
    recalc_normals(bm)
    return object_from_bm('body', bm)


def P(i, j):
    """Stage-1 position of chain ring i, vertex j."""
    return Vector(CHAIN[i][j])


def leg_loop(bm, leg, a, t):
    """A full loop round a leg segment between sections a and a+1, t from section a."""
    L = LEGS[leg]
    pa, pb = L[a][('o', 1)], L[a + 1][('o', 1)]
    return loopcut(bm, edge_near(bm, (pa + pb) / 2), t=t, near=vert_near(bm, pa))


def stage2(k, body):
    bm = edit(body)
    # ---- connectivity (each logged)
    with k.topo(bm, 'loop', 'nose block: a loop just behind the nose pad so the pad reads as its own block'):
        nose = loopcut(bm, edge_near(bm, (P(0, 0) + P(1, 0)) / 2), t=0.55, near=vert_near(bm, P(0, 0)))
    with k.topo(bm, 'partial_loop', 'mouth line along the muzzle side, fan terminators at the nose and on the cheek'):
        e0 = edge_near(bm, (P(0, 2) + P(0, 3)) / 2)
        e1 = edge_near(bm, (P(4, 2) + P(4, 3)) / 2)
        mouth = partial_loop(bm, e0, e1, t=0.40, near=vert_near(bm, P(0, 3)))
    with k.topo(bm, 'loop', 'neck base: loop between the neck and the withers for the head-down bend'):
        loopcut(bm, edge_near(bm, (P(8, 0) + P(9, 0)) / 2), t=0.5)
    with k.topo(bm, 'loop', 'mid neck: loop between the throat rings so the neck arcs instead of kinking'):
        loopcut(bm, edge_near(bm, (P(7, 0) + P(8, 0)) / 2), t=0.5)
    with k.topo(bm, 'loop', 'shoulder: loop round the foreleg root above the elbow'):
        loopcut(bm, edge_near(bm, (P(11, 2) + LEGS['fore'][0][('o', 1)]) / 2), t=0.55,
                near=vert_near(bm, P(11, 2)))
    joints = []
    for leg, a, t, why in (('fore', 0, 0.40, 'elbow: loop below the elbow for the bend'),
                           ('hind', 0, 0.55, 'stifle: loop in the thigh above the stifle'),
                           ('hind', 1, 0.45, 'stifle: loop below the stifle')):
        # (K=3: the two mid-cannon loops are gone: they made the even 'bamboo' ring bands; the
        # cannon now runs knee/hock -> cannon top -> fetlock, unevenly spaced)
        with k.topo(bm, 'loop', why):
            joints.append(leg_loop(bm, leg, a, t))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye plane under the brow'):
        eyef = quad(vert_near(bm, P(3, 1)), vert_near(bm, P(3, 2)), vert_near(bm, P(4, 2)), vert_near(bm, P(4, 1)))
        eye_in = inset(bm, [eyef], 0.42, depth=0.0)
    rump_top = [vert_near(bm, P(19, j)) for j in (0, 1)]
    with k.topo(bm, 'chamfer', 'rump: a crease hugging the top-back corner so the rump rounds off instead of a slab'):
        e = next(ed for ed in rump_top[0].link_edges if rump_top[1] in ed.verts)
        chamfer(bm, e, 0.30)
    # ---- vertex moves
    for v in eye_in[0].verts:                          # the socket sinks under the brow
        v.co += Vector((-0.012, 0.0, -0.004))
    EYE_SOCKET[:] = [tuple(v.co) for v in eye_in[0].verts]
    for i in (3, 4):                                   # brow ridge over the socket
        vert_near(bm, P(i, 1)).co += Vector((0.010, 0.0, 0.006))
    for v in nose:                                     # the bridge steps down behind the nose pad
        if v.co.z > P(1, 0).z - 0.02:
            v.co.z -= 0.006
    for v in mouth:                                    # a shallow lip groove
        v.co.x -= 0.006
        v.co.z -= 0.002
    # rump: the flat back plate becomes rounded buttocks (flank/keel corners of the rump rings back)
    for i, d in ((18, 0.015),):                        # (ring 19 stays: the rump dome rounds it off)
        for j in (2, 3):
            vert_near(bm, P(i, j)).co.y += d
    # flank planes: rib barrel out, waist in, the point of the shoulder and the hip bone proud
    for i, j, d in ((12, 2, (0.014, 0, 0)), (13, 2, (0.016, 0, 0)), (14, 2, (0.010, 0, 0)),
                    (13, 1, (0.006, 0, 0.004)), (15, 2, (-0.010, 0, 0)), (15, 3, (-0.006, 0, 0.006)),
                    (9, 2, (0.012, -0.006, 0)), (16, 1, (0.010, 0, 0.006)), (17, 1, (0.008, 0, 0.004))):
        vert_near(bm, P(i, j)).co += Vector(d)
    # rump (AD note 5): the top-back corner drops 2.5 cm (rounded by the chamfer) and the stifle
    # loops slide forward so the ham slopes (the tail is a stage-3 piece since the K=3 unlock)
    for v in rump_top:
        v.co.z -= 0.025
        v.co.y -= 0.005
    # rump dome (K=3): the centre line of the dome sat further forward than its sides, so the cap
    # read as a dish (a 'curl' round the tail); the centre goes back so the rump is convex
    for j, d in ((0, 0.018), (1, 0.010), (3, 0.010), (4, 0.020)):
        vert_near(bm, P(20, j)).co.y += d
    for vs, d in ((joints[1], 0.020), (joints[2], 0.025)):
        for v in vs:
            v.co.y -= d
    # knee (K=3 note 4): a flat-fronted block that bulges backward, not a bead ring
    kn = {q: vert_near(bm, p) for q, p in LEGS['fore'][3].items()}
    kc = J['kneeL'][0]
    for q in (('o', 0), ('i', 0)):                     # the front: back into line, spread flat
        v = kn[q]
        v.co.y += 0.014
        v.co.x = kc + (0.036 if q[0] == 'o' else -0.036)
    for q in (('o', 1), ('i', 1)):                     # the sides in
        kn[q].co.x = kc + (kn[q].co.x - kc) * 0.87
    for q in (('o', 2), ('i', 2)):                     # the back bulges
        kn[q].co.y += 0.006
    for v in bm.verts:                                 # soles up inside the hoof pieces
        if v.co.z < 0.002:
            v.co.z += SOLE_LIFT
    commit(body, bm)


# ---------------------------------------------------------------- stage 3
PALETTE = {'body': '#8a5a3a', 'mane': '#6a4630', 'pale': '#d9c3a0', 'legs': '#7a5238',
           'hoof': '#231a16', 'antler': '#d8c8a8', 'tip': '#efe6d2', 'eye': '#1a1410'}


def pal(*keys):
    return {q: PALETTE[q] for q in keys}


def head_uv(c):
    """World point -> (u, v) in the unscaled head frame (u from the nose tip back, v up)."""
    y = HEAD_P[1] + (c[1] - HEAD_P[1]) / HEAD_S[1]
    z = HEAD_P[2] + (c[2] - HEAD_P[2]) / HEAD_S[2]
    cs, sn = math.cos(math.radians(HEAD_TILT)), math.sin(math.radians(HEAD_TILT))
    dy, dz = y - HEAD_N0[0], z - HEAD_N0[1]
    return dy * cs + dz * sn, -dy * sn + dz * cs


def mouth_v(u):
    """v of the lip line (stage-2 partial loop, t 0.40 from the jaw corner) along the head."""
    pts = [(uu, r[3][1] + (r[2][1] - r[3][1]) * 0.40) for uu, r in HEAD[:5]]
    if u <= pts[0][0]:
        return pts[0][1]
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if u0 <= u <= u1:
            return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return pts[-1][1]


def neck_front_y(z):
    """y of the withers-to-brisket plane (ring 9) at height z; the neck is ahead of it."""
    return -0.23 - (1.29 - z) * (0.25 / 0.36)


def body_rule(c, n, i):
    x, y, z = c
    u, v = head_uv(c)
    if x > 0.15 and z > 1.45 and y < -0.40 and u > 0.30:          # ears: pale cup in front, body behind
        return 'pale' if n.y < -0.15 and x < 0.20 else 'body'  # pale only in the inner root half: a
                                                                  # pale ear tip reads as a tine from the front
    if u < 0.47 and v > -0.15 and z > 1.15:                         # the head
        if u < 0.030:
            return 'hoof'                                           # nose pad
        if v < mouth_v(u) + 0.002 and u < 0.20 and (n.z < -0.25 or abs(x) < 0.02):
            return 'pale'                                           # chin under the jaw line only
        return 'body'
    if z < 0.05:
        return 'hoof'
    if (y < 0.20 and z < 0.56) or (y > 0.30 and z < 0.58):
        return 'legs'
    if y > 0.66 and 0.70 < z < 1.10 and ((n.y > 0.35 and x < 0.09) or (y > 0.735 and x < 0.115 and n.y > 0.15 and z > 0.86)
                                         or (y > 0.72 and x < 0.075 and z < 0.97)):  # rump patch, down between the buttocks
        return 'pale'
    if n.z < -0.55 and -0.02 < y < 0.60 and x < 0.13:              # belly: starts at ring 12, behind the forelegs
        return 'pale'
    if z > 0.95 and y < neck_front_y(z) - 0.01:                     # the neck: dark mane colour,
        if n.y < -0.35 and n.z < 0.40:                              # but the neck front is brown: the
            return 'body'                                           # dark V bib is on the mane piece
        return 'mane'
    if n.z > 0.80 and z > 1.14 and y < 0.62:                        # dark line along the back
        return 'mane'
    return 'body'


def mk(name, bm, palette, rule, clip=True):
    ob = object_from_bm(name, bm, mirror=True)
    if not clip:
        ob.modifiers['mirror'].use_clip = False
    paint(ob, palette, rule)
    return ob


def frame_for(d, ref=None):
    d = d.normalized()
    ref = ref if ref is not None else (Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0)))
    a = (ref - d * ref.dot(d))
    if a.length < 1e-6:
        a = Vector((1, 0, 0)) - d * d.x
    a.normalize()
    b = d.cross(a).normalized()
    return a, b


def branch(bm, pts, rads, n=5, flat=1.0):
    """A tapered n-sided branch through pts (rings at all but the last point, which is the tip)."""
    pts = [Vector(p) for p in pts]
    rings_ = []
    a_prev = None
    for i, p in enumerate(pts[:-1]):
        d = (pts[i + 1] - pts[i - 1]) if i > 0 else (pts[1] - pts[0])
        a, b = frame_for(d, a_prev)
        a_prev = a
        r = rads[i]
        rings_.append(ring(bm, [p + a * (r * math.cos(2 * math.pi * q / n)) + b * (r * flat * math.sin(2 * math.pi * q / n))
                                for q in range(n)]))
    for r0, r1 in zip(rings_, rings_[1:]):
        bridge(bm, r0, r1, closed=True)
    cap(bm, list(reversed(rings_[0])))
    t = bm.verts.new(pts[-1])
    last = rings_[-1]
    for q in range(n):
        bm.faces.new([last[q], last[(q + 1) % n], t])
    return rings_


PED = None       # the antler pedicel (left), set in stage 3


def piece_antlers():
    """Red-deer antlers. The beam leaves the burr sweeping BACK and out, turns up, and curves in
    at the top into a crown cup. Brow (longest, low at the burr, forward over the face), bez just
    above it and trez at mid-beam: lengths 100/80/70%, splayed ~15 deg apart; a crown cup of the
    beam tip plus three points (40-60%). Every tine starts on the beam axis (its root cap hidden in
    the beam) and leaves the beam through a node flared 1.3x, sunk ~35% of its radius."""
    bm = bmesh.new()
    O = Vector(PED)

    def at(x, y, z):
        return O + Vector((x, y, z))
    beam = [at(-0.004, 0.0, -0.03), at(0.030, 0.030, 0.035), at(0.085, 0.115, 0.105), at(0.160, 0.185, 0.205),
            at(0.240, 0.205, 0.315), at(0.290, 0.180, 0.420), at(0.270, 0.130, 0.510)]
    brad = [0.050, 0.045, 0.040, 0.035, 0.031, 0.030]          # a steady taper, base -> crown (K=3)
    branch(bm, beam, brad)

    def on_beam(i, t):
        return beam[i].lerp(beam[i + 1], t), brad[i] + (brad[min(i + 1, len(brad) - 1)] - brad[i]) * t
    seg = [(b_ - a_).length for a_, b_ in zip(beam, beam[1:])]

    def at_frac(f):                                  # a point f of the way along the beam (arc length)
        s_ = f * sum(seg)
        for i, L_ in enumerate(seg):
            if s_ <= L_ or i == len(seg) - 1:
                return on_beam(i, min(1.0, s_ / L_))
            s_ -= L_
    LB = 0.21
    # the lower tines are STAGGERED up the beam (27/40/57% of its length) so they do not fan out of
    # one point at the burr; the brow rises forward over the face, well above the ear (repair K=2)
    # K=3: lengths 0.6-1.3x of the mean and directions >= 15 deg apart, so no two tines are parallel
    # or equal; the brow roots 5% of the beam higher (daylight over the ear)
    tines = [(at_frac(0.32), (0.10, -0.85, 0.48), LB, 0.024, 0.030),              # brow: 1.3x, low and forward
             (at_frac(0.42), (0.45, -0.55, 0.62), 0.48 * LB, 0.019, 0.012),     # bez: 0.6x, forward-out
             (at_frac(0.58), (0.72, -0.22, 0.66), 0.78 * LB, 0.020, 0.018),     # trez: 1.0x, out
             (on_beam(5, 0.0), (0.82, 0.22, 0.52), 0.62 * LB, 0.017, 0.010),     # crown: out and back
             (on_beam(5, 0.0), (-0.05, 0.74, 0.67), 0.46 * LB, 0.015, 0.008),    # crown: back
             (on_beam(5, 0.0), (0.22, -0.52, 0.82), 0.70 * LB, 0.016, 0.010)]    # crown: forward, steep
    tips = [(beam[-1], 0.12)]
    for (root, br), d, L, r, bend in tines:
        d = Vector(d).normalized()
        node = root + d * (br - 0.30 * 1.4 * r)          # the flared root, 30% of it sunk in the beam
        mid = root + d * (br + 0.45 * (L - br)) + Vector((0, 0, bend * 0.3))
        tip = root + d * L + Vector((0, 0, bend))
        branch(bm, [root, node, mid, tip], [r, 1.4 * r, 0.72 * r])
        tips.append((tip, L))

    def rule(c, n, i):
        c = Vector(c)
        return 'tip' if any((c - t).length < 0.32 * L for t, L in tips) else 'antler'
    return mk('antlers', bm, pal('antler', 'tip'), rule, clip=False)


MANE_CLUMPS = [(0.18, 0.030), (0.42, 0.048), (0.64, 0.062), (0.90, 0.026)]   # (tf crest->throat, hang)


def piece_mane(pos):
    """The shaggy neck mane: a CLOSED, thick collar over the lower neck (ring 7 to 8.85). Its top
    rim is sunk under the neck and steps out in a lip; the collar swells 3-5 cm off the neck and
    ends in a blunt hem (1.8 cm thick) broken into four unequal rounded clumps, short on the crest
    and longer on the throat. The throat side swells less, so the throat line shows from the front.
    Its underside stands 6-22 mm off the neck, so the shell enters the neck along ONE band (the rim)."""
    bm = bmesh.new()

    def at(t, j):                                   # a point on the neck surface, ring t (7..9), vertex j
        i = int(min(8, math.floor(t)))
        return pos(i, j).lerp(pos(i + 1, j), t - i)
    NC = 13                                         # columns per half: ring vertices and thirds between

    def band(t):
        r = [at(t, j) for j in range(5)]
        pts = []
        for j in range(4):
            pts += [r[j], r[j].lerp(r[j + 1], 1 / 3), r[j].lerp(r[j + 1], 2 / 3)]
        pts.append(r[4])
        return pts, (r[0] + r[4]) / 2
    down_neck = ((pos(9, 0) + pos(9, 4)) / 2 - (pos(7, 0) + pos(7, 4)) / 2).normalized()

    def out(p, c):
        d = p - c
        return (d - down_neck * d.dot(down_neck)).normalized()

    def hem(tf):
        h = 0.014
        for cc, amp in MANE_CLUMPS:
            h += amp * max(0.0, 1.0 - abs(tf - cc) / 0.13) ** 0.6
        return h
    bands = {}

    def col(t, q):                                  # (point, band centre) of column q at ring t
        t = round(t, 3)
        if t not in bands:
            bands[t] = band(t)
        return bands[t][0][q], bands[t][1]
    rows = [[] for _ in range(8)]
    for q in range(NC):
        tf = q / (NC - 1)                                  # 0 crest .. 1 throat
        sw = 1.0 - 0.50 * tf                               # the throat swells less (narrower front)
        # the hem (K=3): level on the crest, rising on the front sides (brown neck shows under it
        # from the front) and dropping again to a centred V point on the throat
        if tf <= 0.30:
            t_hem = 8.45
        elif tf <= 0.75:
            t_hem = 8.45 - 0.70 * (tf - 0.30) / 0.45
        else:
            t_hem = 7.75 + 0.40 * (tf - 0.75) / 0.25
        t_sw = min(7.8, t_hem - 0.18)
        p0, c0 = col(7.20, q); pl, cl = col(7.30, q); p1, c1 = col(t_sw, q)
        pj, cj = col(7.44, q); p2, c2 = col(t_hem, q)
        o2 = out(p2, c2)
        hang = (down_neck * (1 - tf) + Vector((0, 0, -1)) * tf * 0.8 + o2 * 0.55).normalized()   # flares off
        rows[0].append(p0 - out(p0, c0) * 0.028)                                        # sunk root, deep
        rows[1].append(pl + out(pl, cl) * 0.004)                                        # the rim: barely proud
        rows[2].append(p1 + out(p1, c1) * 0.034 * sw)                                   # the swell
        rows[3].append(p2 + o2 * 0.046 * sw)
        tip = p2 + o2 * 0.036 * sw + hang * hem(tf)
        rows[4].append(tip)                                                             # hem, outer
        rows[5].append(tip - o2 * 0.018 * sw - hang * 0.006)                            # hem, inner
        rows[6].append(p2 + o2 * 0.022 * sw)                                            # underside, standing off
        rows[7].append(pj + out(pj, cj) * 0.006)                                        # the neck: it enters the
    for row in rows:
        for qq in (row[0], row[-1]):
            qq.x = 0.0
    R = [ring(bm, [tuple(qq) for qq in row]) for row in rows]
    for a_, b_ in zip(R, R[1:] + R[:1]):
        bridge(bm, a_, b_)
    # paint (K=3): a centred V bib, ~60% of the neck width at the top, narrowing to the hem point;
    # the forward-facing collar outside the V is body brown, so the throat reads from the front
    z_top, z_bot = rows[1][-1].z, rows[4][-1].z
    w0 = 0.60 * max(p.x for p in rows[1])

    def rule(c, n, i):
        if n.y > -0.20 or c[1] > rows[1][-1].y + 0.06:
            return 'mane'
        f = max(0.0, min(1.0, (c[2] - z_bot) / max(1e-6, z_top - z_bot)))
        return 'mane' if abs(c[0]) < w0 * f else 'body'
    return mk('mane', bm, pal('mane', 'body'), rule)


def piece_eye(body):
    """A 6-sided lens seated in the stage-2 socket floor: a third of its depth sunk below the
    floor, the rim just proud of it (no flush face), and a small highlight set into the lens."""
    q = [Vector(p) for p in EYE_SOCKET]
    c = sum(q, Vector()) / len(q)
    nrm = (q[1] - q[0]).cross(q[2] - q[0]).normalized()
    if nrm.x < 0:
        nrm = -nrm
    up = Vector((0, 0, 1)); up = (up - nrm * up.dot(nrm)).normalized()
    fw = nrm.cross(up).normalized()
    if fw.y > 0:
        fw = -fw
    bm = bmesh.new()
    r = 0.030
    h_back, h_rim, h_apex = -0.007, 0.002, 0.014          # 1/3 of the depth below the floor

    def lens(cen, rad, sq):
        rim = [bm.verts.new(cen + nrm * h_rim + fw * (rad * 1.3 * math.cos(a)) + up * (rad * sq * math.sin(a)))
               for a in [math.radians(30 + 60 * i) for i in range(6)]]
        apex = bm.verts.new(cen + nrm * h_apex)
        back_ = bm.verts.new(cen + nrm * h_back)
        for i in range(6):
            bm.faces.new([rim[i], rim[(i + 1) % 6], apex])
            bm.faces.new([rim[(i + 1) % 6], rim[i], back_])
    lens(c + fw * 0.004, r, 0.82)
    hl = c + fw * (0.004 - 0.1 * r) + nrm * 0.0105 + up * (0.35 * r)
    tri = [bm.verts.new(hl + fw * 0.006), bm.verts.new(hl - fw * 0.004 + up * 0.004),
           bm.verts.new(hl - fw * 0.004 - up * 0.004)]
    bk = bm.verts.new(hl - nrm * 0.005)
    for i in range(3):
        bm.faces.new([tri[i], tri[(i + 1) % 3], bk])
    bm.faces.new(tri)
    return mk('eye', bm, pal('eye', 'tip'), lambda cc, n, i: 'tip' if (Vector(cc) - hl).length < 0.008 else 'eye',
              clip=False)


def piece_hooves(body):
    """Cloven hooves: one closed dark shell per foot that WRAPS the leg end (the leg's sole is
    lifted 6 mm inside it in stage 2), every wall 10% + 4 mm out from the leg so no wall is
    coplanar with it; a notch at the front reads as the cleft, the heel sits lower than the toe."""
    bmr = edit(body)
    order = [('o', 0), ('o', 1), ('o', 2), ('i', 2), ('i', 1), ('i', 0)]
    feet = []
    for leg in ('fore', 'hind'):
        sole = [vert_near(bmr, LEGS[leg][-1][q] + Vector((0, 0, SOLE_LIFT))).co.copy() for q in order]
        top = [vert_near(bmr, LEGS[leg][-2][q]).co.copy() for q in order]
        fet = [vert_near(bmr, LEGS[leg][-3][q]).co.copy() for q in order]
        feet.append((sole, top, fet))
    bmr.free()
    bm = bmesh.new()

    def grow(pts, z_of):
        c = sum(pts, Vector()) / len(pts)
        out = []
        for p in pts:
            d = Vector((p.x - c.x, p.y - c.y, 0.0))
            q = c + d * 1.10 + d.normalized() * 0.004
            out.append(Vector((q.x, q.y, z_of(p))))
        # the cleft: a notch in the middle of the front edge (between ('i', 0) and ('o', 0))
        f0, f1 = out[5], out[0]
        m = (f0 + f1) / 2
        m.y += 0.006
        return out + [m]
    for sole, top, fet in feet:
        ztop = [0.074, 0.066, 0.052, 0.052, 0.066, 0.074]             # toe high, heel low
        mid = [a.lerp(b, (zt - a.z) / (b.z - a.z)) for a, b, zt in zip(top, fet, ztop)]
        bot = ring(bm, [tuple(p) for p in grow([Vector((p.x, p.y, 0.0)) for p in sole], lambda p: 0.0)])
        tz = ztop + [0.074]
        rim = grow(mid, lambda p: 0.0)
        tp = ring(bm, [(p.x, p.y, tz[i]) for i, p in enumerate(rim)])
        bridge(bm, bot, tp, closed=True)
        cap(bm, list(reversed(bot))); cap(bm, tp)
    recalc_normals(bm)
    return mk('hooves', bm, pal('hoof'), lambda c, n, i: 'hoof', clip=False)


TAIL_PATH = [(0.765, 1.062, 0.028), (0.808, 1.042, 0.036), (0.831, 1.000, 0.035), (0.841, 0.955, 0.027), (0.845, 0.935, 0.017)]


def piece_tail():
    """The tail (AD K=3 note 1): one short hanging wedge on the centre line over the rump patch.
    It leaves the rump dome ~30% of its length from the buried root, hangs back-down clear of the
    patch, is 40% as thick as it is wide, and narrows to a blunt end. Brown on top (the back-facing
    side), patch cream underneath (the side against the rump)."""
    bm = bmesh.new()
    pts = [Vector((0.0, y, z)) for y, z, _ in TAIL_PATH]      # (y, z, half width) root -> blunt end
    R = []
    for n_, (p, (_, _, w)) in enumerate(zip(pts, TAIL_PATH)):
        d = (pts[min(n_ + 1, len(pts) - 1)] - pts[max(n_ - 1, 0)]).normalized()
        b = Vector((0.0, -d.z, d.y))                        # the tail's top: faces back (and up)
        if b.y < 0:
            b = -b
        t = 0.40 * w                                        # half thickness = 40% of the half width
        R.append(ring(bm, [tuple(p + b * t), tuple(p + Vector((0.75 * w, 0, 0)) + b * (0.6 * t)),
                           tuple(p + Vector((w, 0, 0))), tuple(p + Vector((0.75 * w, 0, 0)) - b * (0.6 * t)),
                           tuple(p - b * t)]))
    for a_, b_ in zip(R, R[1:]):
        bridge(bm, a_, b_)
    cap(bm, R[0]); cap(bm, list(reversed(R[-1])))
    recalc_normals(bm)
    return mk('tail', bm, pal('body', 'pale'), lambda c, n, i: 'pale' if n.y < -0.25 else 'body')


def stage3(k, body):
    global PED
    paint(body, pal('body', 'mane', 'pale', 'legs', 'hoof'), body_rule)
    bmr = edit(body)
    cache = {}

    def pos(i, j):
        if (i, j) not in cache:
            cache[(i, j)] = vert_near(bmr, P(i, j)).co.copy()
        return cache[(i, j)]
    PED = tuple(head_xf(H(0.052, 0.375, 0.112)))
    pieces = [piece_mane(pos)]
    bmr.free()
    pieces += [piece_antlers(), piece_eye(body), piece_hooves(body), piece_tail()]
    return pieces


# ---------------------------------------------------------------- stage 4
def bones():
    """The armature from the joints the model was built on (J); the ear bone from the ear root."""
    ear0 = tuple((P(R_EAR, 1) + P(R_EAR, 2) + P(R_EAR + 1, 1) + P(R_EAR + 1, 2)) / 4)
    fh = (J['fhoofL'][0], J['fhoofL'][1] - 0.03, 0.01)
    hh = (J['hhoofL'][0], J['hhoofL'][1] - 0.03, 0.01)
    return [('hips', J['hip'], J['spine'], None),
            ('chest', J['spine'], J['neck'], 'hips', True),
            ('neck0', J['neck'], J['neck1'], 'chest', True),
            ('neck1', J['neck1'], J['head'], 'neck0', True),
            ('head', J['head'], J['snout'], 'neck1', True),
            ('ear.L', ear0, EAR_TIP, 'head'),
            ('tail0', J['tail0'], J['tail1'], 'hips'),
            ('tail1', J['tail1'], J['tail2'], 'tail0', True),
            ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
            ('forearm.L', J['elbowL'], J['kneeL'], 'upperarm.L', True),
            ('cannon.L', J['kneeL'], J['ffetL'], 'forearm.L', True),
            ('fhoof.L', J['ffetL'], fh, 'cannon.L', True),
            ('thigh.L', J['hipL'], J['stifleL'], 'hips'),
            ('shin.L', J['stifleL'], J['hockL'], 'thigh.L', True),
            ('meta.L', J['hockL'], J['hfetL'], 'shin.L', True),
            ('hhoof.L', J['hfetL'], hh, 'meta.L', True)]


CENTRE = ('hips', 'chest', 'neck0', 'neck1', 'head', 'tail0', 'tail1')


def both(d):
    """{'upperarm': x} -> the same rotation on .L and .R."""
    out = {}
    for kk, v in d.items():
        if kk.endswith('.L') or kk.endswith('.R') or kk in CENTRE:
            out[kk] = v
        else:
            out[kk + '.L'] = v; out[kk + '.R'] = v
    return out


def compose(tracks, frames):
    """tracks = {bone: {frame: (rx, ry, rz)}} (rest outside the keys) -> clip keys at every frame,
    each bone linearly interpolated, so short flicks can overlap longer moves."""
    out = {}
    for f in frames:
        out[f] = {}
        for b, keys in tracks.items():
            ks = sorted(keys)
            if f <= ks[0] or f >= ks[-1]:
                v = keys[ks[0]] if f <= ks[0] else keys[ks[-1]]
            else:
                a_ = max(k_ for k_ in ks if k_ <= f); b_ = min(k_ for k_ in ks if k_ >= f)
                t = 0 if b_ == a_ else (f - a_) / (b_ - a_)
                v = tuple(keys[a_][i] + (keys[b_][i] - keys[a_][i]) * t for i in range(3))
            out[f][b] = v
    return out


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        nm = p.name
        if 'mane' in nm:
            bind(p, rig, body=body)            # borrows the neck weights: rides on the skin
        elif 'antlers' in nm or 'eye' in nm:
            bind(p, rig, bone='head')          # rigid to the skull
        else:
            bind(p, rig, body=body)            # hooves: the leg-end weights, so the leg never pokes out
    Z = (0, 0, 0)
    # idle: a head lift and a look to the side, an ear flick, a tail flick, breathing
    idle = compose({
        'chest': {1: Z, 24: (1.5, 0, 0), 48: Z},
        'neck0': {1: Z, 10: (-5, 0, 0), 30: (-5, 0, 0), 42: Z, 48: Z},
        'neck1': {1: Z, 10: (-4, 0, 0), 16: (-4, 16, 0), 28: (-4, 16, 0), 36: (-4, 0, 0), 42: Z, 48: Z},
        'head': {1: Z, 10: (-6, 0, 0), 16: (-6, 10, 0), 28: (-6, 10, 0), 36: (-4, 0, 0), 42: Z, 48: Z},
        'ear.L': {1: Z, 20: Z, 22: (-35, 0, 0), 24: (10, 0, 0), 26: Z, 48: Z},
        'ear.R': {1: Z, 30: Z, 32: (-35, 0, 0), 34: (10, 0, 0), 36: Z, 48: Z},
        'tail0': {1: Z, 36: Z, 38: (35, 0, 0), 40: (-5, 0, 0), 42: (25, 0, 0), 44: Z, 48: Z},
        'tail1': {1: Z, 36: Z, 38: (15, 0, 0), 42: (10, 0, 0), 44: Z, 48: Z},
    }, [1, 10, 16, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 48])
    clip(rig, 'idle', idle)

    # move: a trot, diagonal pairs A = fore.L + hind.R, B = fore.R + hind.L
    reach, back_ = -20, 18

    def trot(a_fore, a_hind, b_fore, b_hind, lift_a, lift_b):
        return {'upperarm.L': (a_fore, 0, 0), 'thigh.R': (a_hind, 0, 0),
                'upperarm.R': (b_fore, 0, 0), 'thigh.L': (b_hind, 0, 0),
                'forearm.L': (-10 * lift_a, 0, 0), 'forearm.R': (-10 * lift_b, 0, 0),
                'cannon.L': (55 * lift_a, 0, 0), 'cannon.R': (55 * lift_b, 0, 0),
                'fhoof.L': (30 * lift_a, 0, 0), 'fhoof.R': (30 * lift_b, 0, 0),
                'shin.R': (30 * lift_a, 0, 0), 'shin.L': (30 * lift_b, 0, 0),
                'meta.R': (-35 * lift_a, 0, 0), 'meta.L': (-35 * lift_b, 0, 0),
                'hhoof.R': (25 * lift_a, 0, 0), 'hhoof.L': (25 * lift_b, 0, 0),
                'neck0': (1.5 * (lift_a + lift_b), 0, 0), 'head': (-1.5 * (lift_a + lift_b), 0, 0),
                'tail0': (8, 0, 0)}
    clip(rig, 'move', {1: trot(reach, reach, back_, back_, 0, 0),
                       7: trot(0, 0, 0, 0, 0, 1),
                       13: trot(back_, back_, reach, reach, 0, 0),
                       19: trot(0, 0, 0, 0, 1, 0),
                       25: trot(reach, reach, back_, back_, 0, 0)},
         loc={1: {'hips': Z}, 7: {'hips': (0, 0, 0.02)}, 13: {'hips': Z}, 19: {'hips': (0, 0, 0.02)}, 25: {'hips': Z}})

    # attack: drop the head so the antlers point forward, charge, thrust the antlers up and through
    clip(rig, 'attack', {
        1: {},
        10: both({'neck0': (14, 0, 0), 'neck1': (8, 0, 0), 'head': (30, 0, 0), 'chest': (-3, 0, 0),
                  'upperarm': (-8, 0, 0), 'cannon': (4, 0, 0), 'thigh': (10, 0, 0), 'shin': (6, 0, 0),
                  'meta': (-6, 0, 0), 'tail0': (20, 0, 0)}),
        18: both({'neck0': (20, 0, 0), 'neck1': (6, 0, 0), 'head': (22, 0, 0), 'chest': (-5, 0, 0),
                  'upperarm': (-22, 0, 0), 'cannon': (6, 0, 0), 'thigh': (-14, 0, 0), 'shin': (10, 0, 0),
                  'meta': (-10, 0, 0), 'tail0': (30, 0, 0)}),
        24: both({'neck0': (12, 0, 0), 'neck1': (2, 0, 0), 'head': (-8, 0, 0), 'chest': (-3, 0, 0),
                  'upperarm': (-16, 0, 0), 'cannon': (4, 0, 0), 'thigh': (-8, 0, 0), 'shin': (6, 0, 0),
                  'meta': (-6, 0, 0), 'tail0': (25, 0, 0)}),
        36: {}},
        loc={1: {'hips': Z}, 10: {'hips': (0, -0.04, -0.03)}, 18: {'hips': (0, 0.06, -0.01)},
             24: {'hips': (0, 0.05, 0)}, 36: {'hips': Z}})
    return rig


run(META, stage1, stage2, stage3, stage4)
