"""Stylised low-poly wolf, box-modelled in four stages (experiments/boxmodel/BRIEF.md).

The body is one chain of 8-sided half rings (5 verts: spine seam, back corner,
flank, keel corner, belly seam) from the nose block to the tail brush; legs are
6-sided and extruded from two lower-flank quads each, ears are pyramids pulled
out of the skull's top-side quad. Everything is placed from the joints in J.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='wolf', model='opus', engine_glb='example/wolf.glb')

# the skeleton the model is built on (x, y, z); .L joints on +X
J = dict(
    hip=(0.0, 0.30, 0.60), spine=(0.0, 0.02, 0.60), chest=(0.0, -0.20, 0.60),
    neck=(0.0, -0.22, 0.63), head=(0.0, -0.40, 0.80), snout=(0.0, -0.83, 0.76),
    tail0=(0.0, 0.46, 0.61), tail1=(0.0, 0.57, 0.575), tail2=(0.0, 0.665, 0.50), tail3=(0.0, 0.735, 0.39),
    tail4=(0.0, 0.775, 0.235),
    shoulderL=(0.145, -0.16, 0.52), elbowL=(0.138, -0.12, 0.25), wristL=(0.132, -0.185, 0.095),
    pawL=(0.132, -0.225, 0.02),
    hipL=(0.155, 0.30, 0.54), stifleL=(0.155, 0.235, 0.28), hockL=(0.142, 0.385, 0.15),
    hpawL=(0.138, 0.35, 0.02),
)


# ---------------------------------------------------------------- helpers
def quad(*vs):
    s = set(vs[0].link_faces)
    for v in vs[1:]:
        s &= set(v.link_faces)
    assert len(s) == 1, 'quad lookup: %d faces' % len(s)
    return s.pop()


def tail_ring(c, d, rx, rz):
    """A tail section perpendicular to the direction d (in y-z), centre c=(y, z)."""
    dy, dz = d
    L = math.hypot(dy, dz); dy, dz = dy / L, dz / L
    uy, uz = -dz, dy                       # 'up' across the tail
    if uz < 0:
        uy, uz = -uy, -uz
    y, z = c
    return [(0.0, y + uy * rz, z + uz * rz),
            (0.72 * rx, y + uy * 0.62 * rz, z + uz * 0.62 * rz),
            (rx, y - uy * 0.05 * rz, z - uz * 0.05 * rz),
            (0.72 * rx, y - uy * 0.66 * rz, z - uz * 0.66 * rz),
            (0.0, y - uy * rz, z - uz * rz)]


# The chain, nose -> tail tip. Each ring: spine seam, back corner, flank, keel corner, belly seam.
CHAIN = [
    # nose block (front face is the cap)
    [(0, -0.805, 0.770), (0.026, -0.805, 0.767), (0.034, -0.803, 0.735), (0.030, -0.797, 0.703), (0, -0.794, 0.697)],
    [(0, -0.770, 0.782), (0.036, -0.770, 0.777), (0.046, -0.772, 0.728), (0.043, -0.772, 0.682), (0, -0.770, 0.670)],
    # muzzle: a tapered box (flat bridge, near-vertical sides); the keel corner is the jaw line
    [(0, -0.700, 0.790), (0.047, -0.700, 0.786), (0.058, -0.700, 0.732), (0.056, -0.700, 0.672), (0, -0.700, 0.657)],
    [(0, -0.636, 0.806), (0.058, -0.636, 0.802), (0.076, -0.636, 0.742), (0.072, -0.640, 0.672), (0, -0.640, 0.650)],
    # brow (the stop is the step from the ring above)
    [(0, -0.596, 0.868), (0.078, -0.591, 0.872), (0.100, -0.600, 0.765), (0.088, -0.600, 0.672), (0, -0.600, 0.645)],
    # skull front (cheekbone)
    [(0, -0.535, 0.915), (0.070, -0.535, 0.910), (0.122, -0.540, 0.800), (0.104, -0.540, 0.675), (0, -0.540, 0.642)],
    # skull (ear front)
    [(0, -0.480, 0.930), (0.042, -0.480, 0.930), (0.125, -0.480, 0.820), (0.105, -0.470, 0.672), (0, -0.470, 0.640)],
    # skull back (ear back) / jaw angle
    [(0, -0.400, 0.915), (0.042, -0.400, 0.915), (0.118, -0.405, 0.810), (0.100, -0.420, 0.672), (0, -0.430, 0.638)],
    # neck: thick, tilted rings
    [(0, -0.340, 0.885), (0.068, -0.345, 0.875), (0.118, -0.370, 0.780), (0.100, -0.400, 0.650), (0, -0.425, 0.598)],
    [(0, -0.265, 0.815), (0.078, -0.270, 0.800), (0.128, -0.300, 0.690), (0.105, -0.360, 0.570), (0, -0.400, 0.530)],
    # shoulder front / breastbone
    [(0, -0.190, 0.765), (0.095, -0.190, 0.748), (0.155, -0.215, 0.610), (0.110, -0.285, 0.440), (0, -0.395, 0.440)],
    # chest (the foreleg comes out of this ring's lower flank); the keel is the lowest point
    # (r3 unlock, note 1: a flat-bottomed brisket: the seam 0.4 cm up, the keel corners 3.3 cm down)
    [(0, -0.090, 0.755), (0.112, -0.090, 0.735), (0.175, -0.100, 0.575), (0.095, -0.140, 0.312), (0, -0.200, 0.296)],
    # chest back, behind the elbow
    [(0, 0.010, 0.728), (0.117, 0.010, 0.712), (0.170, 0.000, 0.550), (0.088, -0.020, 0.318), (0, -0.040, 0.300)],
    # ribs back: the belly line starts to rise
    [(0, 0.110, 0.705), (0.115, 0.110, 0.690), (0.158, 0.110, 0.540), (0.085, 0.105, 0.410), (0, 0.095, 0.385)],
    # waist (tuck)
    [(0, 0.210, 0.700), (0.105, 0.210, 0.685), (0.138, 0.210, 0.565), (0.080, 0.212, 0.475), (0, 0.205, 0.458)],
    # hip
    [(0, 0.310, 0.695), (0.115, 0.310, 0.680), (0.155, 0.310, 0.575), (0.090, 0.320, 0.475), (0, 0.320, 0.458)],
    # rump
    [(0, 0.400, 0.670), (0.105, 0.400, 0.650), (0.140, 0.420, 0.560), (0.080, 0.440, 0.462), (0, 0.450, 0.462)],
    # tail
    tail_ring((0.470, 0.605), (1, -0.2), 0.058, 0.060),
    tail_ring((0.570, 0.570), (1, -0.5), 0.076, 0.082),
    tail_ring((0.665, 0.492), (0.6, -0.8), 0.086, 0.092),
    tail_ring((0.735, 0.388), (0.4, -0.92), 0.080, 0.086),
    tail_ring((0.772, 0.292), (0.2, -1.0), 0.060, 0.064),
    tail_ring((0.782, 0.222), (0.1, -1.0), 0.022, 0.024),
]
# stylised head: rings 0-7 (and the ear tip) are scaled up about the occiput
HEAD_S, HEAD_P = (1.18, 1.12, 1.18), (0.0, -0.40, 0.78)


def head_xf(p):
    return tuple(HEAD_P[i] + (p[i] - HEAD_P[i]) * HEAD_S[i] for i in range(3))


for _i in range(8):
    CHAIN[_i] = [head_xf(p) for p in CHAIN[_i]]
# chunky torso: widen the neck and body rings
for _i, _sx in zip(range(8, 17), (1.10, 1.15, 1.18, 1.18, 1.18, 1.18, 1.18, 1.18, 1.18)):
    CHAIN[_i] = [(p[0] * _sx, p[1], p[2]) for p in CHAIN[_i]]

EAR_TIP = head_xf((0.122, -0.448, 1.085))
R_EAR = 6            # the ear comes out of ring 6 -> 7, back corner -> flank
R_FORE = 10          # foreleg root: rings 10, 11, 12 (flank -> keel corner)
R_HIND = 14          # hind leg root: rings 14, 15, 16


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def chunky(secs, fw, fd, paw=1.12):
    """Stylised limbs: scale the section widths / depths (paws less)."""
    out = []
    for q in secs:
        q = dict(q)
        isp = q.get('dir') == (0, 0, -1)
        q['w'] *= paw if isp else fw
        q['d'] *= paw if isp else fd
        out.append(q)
    return out


def fore_sections():
    s, e, w, p = J['shoulderL'], J['elbowL'], J['wristL'], J['pawL']
    x = s[0]
    return [
        dict(c=(x + 0.005, -0.160, 0.290), w=0.055, d=0.085, ff=0.55, fb=0.50),   # upper arm under the chest (r3: under the lower brisket)
        dict(c=(e[0], -0.145, e[2]), w=0.046, d=0.075, ff=0.55, fb=0.25, mid=-0.2),  # elbow: the point sticks back
        dict(c=(e[0] - 0.003, -0.172, 0.170), w=0.038, d=0.046, ff=0.60, fb=0.35),  # forearm: front line straight
        dict(c=w, w=0.034, d=0.037, ff=0.60, fb=0.45),                            # wrist
        dict(c=(w[0], w[1] - 0.018, 0.055), w=0.040, d=0.042, ff=0.60, fb=0.45, dir=(0, -0.3, -1)),  # pastern
        dict(c=(p[0], p[1], 0.032), w=0.052, d=0.062, ff=0.70, fb=0.55, dir=(0, 0, -1)),   # paw top
        dict(c=(p[0], p[1], 0.000), w=0.055, d=0.068, ff=0.70, fb=0.55, dir=(0, 0, -1)),   # sole
    ]


def hind_sections():
    h, k, hk, p = J['hipL'], J['stifleL'], J['hockL'], J['hpawL']
    return [
        dict(c=(h[0] + 0.008, 0.325, 0.430), w=0.070, d=0.130, ff=0.50, fb=0.60),  # thigh: the big haunch
        dict(c=(h[0] + 0.006, 0.270, 0.350), w=0.060, d=0.095, ff=0.55, fb=0.50),  # lower thigh
        dict(c=k, w=0.046, d=0.062, ff=0.55, fb=0.45),                            # stifle
        dict(c=lerp3(k, hk, 0.5), w=0.038, d=0.052, ff=0.55, fb=0.40),            # gaskin
        dict(c=hk, w=0.032, d=0.042, ff=0.55, fb=0.40),                           # hock
        dict(c=(p[0], p[1] + 0.018, 0.075), w=0.032, d=0.036, ff=0.60, fb=0.45),  # metatarsus
        dict(c=(p[0], p[1], 0.032), w=0.050, d=0.060, ff=0.70, fb=0.55, dir=(0, 0, -1)),   # paw top
        dict(c=(p[0], p[1], 0.000), w=0.053, d=0.066, ff=0.70, fb=0.55, dir=(0, 0, -1)),   # sole
    ]


def hexagon(sec, bone_dir):
    """Six points of a limb section: rows o (outer) / i (inner), cols 0 front .. 2 back."""
    c = Vector(sec['c'])
    b = Vector(sec.get('dir', bone_dir)).normalized()
    f = Vector((0.0, b.z, -b.y))            # forward, perpendicular to the bone, in y-z
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
        wire = [e for e in bm.edges if not e.link_faces]      # the kit's extrude leaves the region's inner edge loose
        if wire:
            bmesh.ops.delete(bm, geom=wire, context='EDGES')
        nxt = Vector(secs[j + 1]['c']) if j + 1 < len(secs) else Vector(sec['c']) + Vector((0, 0, -0.1))
        bone = (nxt - prev_c)
        bone.x = 0
        pts = hexagon(sec, bone)
        for k, p in pts.items():
            lab[k].co = p
        prev_c = Vector(sec['c'])
        out.append(dict(lab))
    return out


def build_ear(bm, R, i, tip):
    f = quad(R[i][1], R[i][2], R[i + 1][2], R[i + 1][1])
    r = extrude(bm, [f])
    bmesh.ops.pointmerge(bm, verts=r['verts'], merge_co=Vector(tip))


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
    for name, i0, secs in (('fore', R_FORE, chunky(fore_sections(), 1.30, 1.25)),
                           ('hind', R_HIND, chunky(hind_sections(), 1.25, 1.20))):
        labs = build_leg(bm, R, i0, secs)
        for si, lab in enumerate(labs):                 # r3 unlock (note 2): the final leg widths live here
            hx, hy, push = LEG_S1[name][si]
            vs = list(lab.values())
            c = sum((v.co for v in vs), Vector()) / 6
            ex_, ey_ = max(abs(v.co.x - c.x) for v in vs), max(abs(v.co.y - c.y) for v in vs)
            for v in vs:
                v.co.x = c.x + (v.co.x - c.x) * hx / ex_
                v.co.y = c.y + (v.co.y - c.y) * hy / ey_
            for q in (('o', 0), ('i', 0)):              # paws: the front verts forward, an oval pad
                lab[q].co.y -= push
        LEGS[name] = [{q: v.co.copy() for q, v in lab.items()} for lab in labs]
    recalc_normals(bm)
    return object_from_bm('body', bm)


# r3 unlock (note 2): stage-1 half-extents (x, y) of every leg section and the paw front push. One
# smooth taper chest -> elbow -> wrist (wrist ~0.7 x the elbow), the pastern no wider than the wrist,
# the paw an oval pad ~1.15x the pastern with its front pushed forward; hind cannons ~0.75x (r2 final)
LEG_S1 = {'fore': [(0.064, 0.108, 0), (0.068, 0.095, 0), (0.056, 0.064, 0), (0.047, 0.050, 0),
                   (0.048, 0.050, 0), (0.052, 0.058, 0.007), (0.056, 0.064, 0.013)],
          'hind': [(0.088, 0.159, 0), (0.075, 0.096, 0), (0.062, 0.078, 0), (0.056, 0.054, 0),
                   (0.040, 0.046, 0), (0.034, 0.036, 0), (0.038, 0.044, 0.006), (0.040, 0.050, 0.010)]}
LEGS = {}      # stage-1 leg section positions, for finding edges in stage 2
EYE, EYE_N = [], []   # the stage-2 eye socket (for seating the eye piece)
EYE_OUT = []          # r3: the socket's outer rim (the faces inside it are painted dark grey)


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
    with k.topo(bm, 'loop', 'nose block: a loop just behind the nose pad so the pad reads as a separate block'):
        nose = loopcut(bm, edge_near(bm, (P(1, 0) + P(2, 0)) / 2), t=0.22, near=vert_near(bm, P(1, 0)))
    with k.topo(bm, 'partial_loop', 'mouth line along the muzzle side, ends on the cheek (nothing bends there)'):
        e0 = edge_near(bm, (P(0, 2) + P(0, 3)) / 2)
        e1 = edge_near(bm, (P(5, 2) + P(5, 3)) / 2)
        mouth = partial_loop(bm, e0, e1, t=0.38, near=vert_near(bm, P(0, 3)))
    with k.topo(bm, 'loop', 'neck base: third loop between the neck and the withers for the head-down bend'):
        loopcut(bm, edge_near(bm, (P(9, 0) + P(10, 0)) / 2), t=0.5)
    joints = []
    for leg, a, t, why in (('fore', 0, 0.62, 'elbow: loop above the elbow for the bend'),
                           ('fore', 1, 0.35, 'elbow: loop below the elbow for the bend'),
                           ('hind', 1, 0.60, 'stifle: loop above the knee'),
                           ('hind', 2, 0.40, 'stifle: loop below the knee'),
                           ('hind', 3, 0.62, 'hock: loop above the hock'),
                           ('hind', 4, 0.38, 'hock: loop below the hock')):
        with k.topo(bm, 'loop', why):
            joints.append(leg_loop(bm, leg, a, t))
    SECV = {(leg, si): [vert_near(bm, p) for p in LEGS[leg][si].values()]
            for leg in LEGS for si in range(len(LEGS[leg]))}          # section rings (before any move)
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye plane under the brow'):
        eyef = quad(vert_near(bm, P(4, 1)), vert_near(bm, P(4, 2)), vert_near(bm, P(5, 2)), vert_near(bm, P(5, 1)))
        eye_out = list(eyef.verts)
        eye_in = inset(bm, [eyef], 0.42, depth=0.0)
    # ---- vertex moves
    for v in eye_in[0].verts:                          # the socket sinks under the brow
        v.co += Vector((-0.007, 0.004, -0.004))
    vert_near(bm, P(4, 2)).co.x -= 0.016               # the cheek in front of the eye turns in: the eye reads from az000
    # the eye plane turns 26 deg toward the front (about Z) so both eyes read from az000
    rotate(list(eye_in[0].verts), (0, 0, 1), -26)
    flatten(list(eye_in[0].verts))
    EYE[:] = [v.co.copy() for v in eye_in[0].verts]
    EYE_N[:] = [eye_in[0].normal.copy() if eye_in[0].normal.length > 0 else Vector((1, 0, 0))]
    for j in (1,):
        for i in (4, 5):
            vert_near(bm, P(i, j)).co.x += 0.010      # brow ridge overhangs the socket
    for j, dz in ((0, -0.010), (1, -0.008)):         # the stop: bridge down at the muzzle root ...
        vert_near(bm, P(3, j)).co.z += dz
    for j, d in ((0, (0, -0.006, 0.014)), (1, (0.004, -0.008, 0.012))):   # ... forehead up and forward
        vert_near(bm, P(4, j)).co += Vector(d)
    # jaw angle vs throat: the jaw corner drops and flares, the throat behind it rises
    vert_near(bm, P(6, 3)).co += Vector((0.008, 0.0, -0.010))
    vert_near(bm, P(7, 3)).co += Vector((0.006, -0.006, -0.004))
    vert_near(bm, P(7, 4)).co += Vector((0.0, 0.010, 0.022))
    vert_near(bm, P(8, 4)).co += Vector((0.0, 0.004, 0.010))
    # ears: shorter, broader at the base, tipped outward
    tip = vert_near(bm, EAR_TIP)
    tip.co = Vector((0.146, -0.452, 1.090))            # note 8: 0.8x the height, no outward tilt
    for i in (6, 7):
        vert_near(bm, P(i, 1)).co.x -= 0.008           # base inner corner in
        vert_near(bm, P(i, 2)).co += Vector((0.010, 0.0, 0.006))   # base outer corner out
    for v in nose:                                   # the bridge steps down behind the pad
        if v.co.z > 0.76:
            v.co.z -= 0.007
    for v in mouth:                                  # the lip line: a real groove
        v.co.x -= 0.010
        v.co.z -= 0.004
    # (r3 unlock: the leg widths, the paws and the smooth taper moved into stage 1 (LEG_S1); the joint
    # loops interpolate between the stage-1 sections, so every ring tapers chest -> wrist with no step)
    def ext(vs):
        c = sum((v.co for v in vs), Vector()) / len(vs)
        return c, max(abs(v.co.x - c.x) for v in vs), max(abs(v.co.y - c.y) for v in vs)
    if os.environ.get('WOLF_RINGS'):
        for nm_, vs_ in [('f%d' % i_, SECV[('fore', i_)]) for i_ in range(7)] + [('j%d' % i_, joints[i_]) for i_ in range(6)] + [('h%d' % i_, SECV[('hind', i_)]) for i_ in range(8)]:
            c_, ex_, ey_ = ext(vs_)
            print('BMK RING', nm_, 'c=(%.3f %.3f %.3f) hx=%.3f hy=%.3f' % (c_.x, c_.y, c_.z, ex_, ey_), 'zr=%.3f..%.3f' % (min(v.co.z for v in vs_), max(v.co.z for v in vs_)))
    # r3 note 2 (no crease): the front of the upper arm ran forward of the forearm's front line, so the
    # f0 -> f1 band faced down (the dark line across the leg); its front verts now sit on one straight
    # line from the brisket's keel corner (ring 10) to the forearm front (f2)
    top = vert_near(bm, P(10, 3)).co.copy()
    f2f = sorted(SECV[('fore', 2)], key=lambda v: v.co.y)[:2]
    bot = Vector((0, sum(v.co.y for v in f2f) / 2, sum(v.co.z for v in f2f) / 2))
    for vs in (SECV[('fore', 0)], joints[0], SECV[('fore', 1)], joints[1]):
        for v in sorted(vs, key=lambda v: v.co.y)[:2]:
            t = (top.z - v.co.z) / (top.z - bot.z)
            v.co.y = top.y + (bot.y - top.y) * t
    # ... and the outer side: f0 / j0 bulged 0.8 cm past the line chest flank -> elbow, so the band
    # under them faced down; their outer rows come in onto that line
    fl = vert_near(bm, P(11, 2)).co.copy()
    e1 = max(SECV[('fore', 1)], key=lambda v: v.co.x).co.copy()
    for vs in (SECV[('fore', 0)], joints[0]):
        c = sum((v.co for v in vs), Vector()) / len(vs)
        mx = max(v.co.x for v in vs)
        zc = sum(v.co.z for v in vs) / len(vs)
        d = fl.x + (e1.x - fl.x) * (fl.z - zc) / (fl.z - e1.z) - mx
        for v in vs:
            if v.co.x > c.x:
                v.co.x += d * (v.co.x - c.x) / (mx - c.x)
    # a flat elbow plane at the back of each foreleg (the two rear verts of three rings)
    back = []
    for vs in (joints[0], SECV[('fore', 1)], joints[1]):
        back += sorted(vs, key=lambda v: -v.co.y)[:2]
    flatten(back)
    # underline (note 6): the sternum drops ~10 % of body depth, the belly in front of the stifle tucks up ~15 %
    # r2 note 2: the drop is spread over the seam AND the keel corners of rings 10-12 so the brisket is a
    # rounded curve, not one pointed vertex; the tuck-up in front of the stifle eases in (ring 13 less)
    # r3 unlock: the ring 11/12 brisket (flat-bottomed) is in stage 1 now; only the ring-10 front rounds here
    for i, j, dz in ((10, 4, -0.020), (13, 4, 0.022), (13, 3, 0.012), (14, 4, 0.036)):
        vert_near(bm, P(i, j)).co.z += dz
    # nose (note 7): the chin corners of the nose ring go up and back, so the black cap is only the
    # upper half of the muzzle tip and the ring-0/1 band below it becomes the chin front
    vert_near(bm, P(0, 3)).co = Vector((P(0, 3).x, -0.838, 0.712))
    vert_near(bm, P(0, 4)).co = Vector((0.0, -0.836, 0.708))
    # r3 note 1: the dark 'keel wedge' under the bib was the hanging tail tip seen through the gap between
    # the forelegs (az000 render with the brush hidden). The last two tail rings swing back and up (a soft
    # J at the tip) so the tip clears the sight line under the brisket; the tail still hangs low
    for i, d in ((21, (0.0, 0.012, 0.012)), (22, (0.0, 0.026, 0.030))):
        for j in range(5):
            vert_near(bm, P(i, j)).co += Vector(d)
    # tail root: the root ring 30 % wider (15 % deeper), the next ring 15 % / 8 %
    for i, sx, sr in ((17, 1.30, 1.15), (18, 1.15, 1.08)):
        vs = [vert_near(bm, P(i, j)) for j in range(5)]
        c = (vs[0].co + vs[4].co) / 2
        for v in vs:
            d = v.co - c
            v.co = Vector((d.x * sx, c.y + d.y * sr, c.z + d.z * sr))
    EYE_OUT[:] = [v.co.copy() for v in eye_out]
    commit(body, bm)
    if os.environ.get('WOLF_DBG'):                     # debug: where the az000 silhouette differs from stage 1
        m1 = np.load(k.path('stage1', 'masks.npz'))['az000']
        m2 = masks(k.frame, views=['az000'], objs=[body])['az000']
        img = np.zeros(m1.shape + (3,), dtype=np.uint8) + 255
        img[m1 & m2] = (160, 160, 160); img[m2 & ~m1] = (220, 30, 30); img[m1 & ~m2] = (30, 30, 220)
        np.save(os.environ['WOLF_DBG'], img)


PALETTE = {'fur_body': '#9c978e', 'fur_dark': '#65636b', 'fur_leg': '#b59d76', 'fur_paw': '#cbb58d',
           'cream': '#efe6cf', 'ear_in': '#d3bfa6', 'nose': '#1b1b1e', 'eye': '#f4b427'}


def pal(*keys):
    return {q: PALETTE[q] for q in keys}


def mouth_z(y):
    """z of the lip line (stage-2 partial loop, t 0.38 from the keel corner) along the muzzle."""
    pts = sorted((CHAIN[i][3][1], CHAIN[i][3][2] + (CHAIN[i][2][2] - CHAIN[i][3][2]) * 0.38) for i in range(5))
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[-1][1]


def in_socket(c):
    """r3 note 4: is a face centre inside the eye socket (its floor and walls)?"""
    if not EYE_OUT or c[0] < 0.05:
        return False
    p = Vector(c)
    o = sum(EYE_OUT, Vector()) / 4
    nn = EYE_N[0] if EYE_N[0].x > 0 else -EYE_N[0]
    if abs((p - o).dot(nn)) > 0.02:
        return False
    q = [v - nn * (v - o).dot(nn) for v in EYE_OUT]
    pp = p - nn * (p - o).dot(nn)
    sg = [((q[(k + 1) % 4] - q[k]).cross(pp - q[k])).dot(nn) for k in range(4)]
    return all(g > 0 for g in sg) or all(g < 0 for g in sg)


def body_rule(c, n, i):
    x, y, z = c
    if in_socket(c):                                           # r3: the socket dark grey, not black
        return 'fur_dark'
    if z > 0.975 and -0.52 < y < -0.38:                        # ears: pale inside, dark behind
        return 'ear_in' if n.y < -0.25 and n.z < 0.9 else 'fur_dark'
    if y < -0.838:
        return 'nose'
    if -0.32 < y < 0.06 and x < 0.08 and z < 0.46 and n.z < 0.3:     # the keel between the forelegs: cream bib
        return 'cream'
    fore, hind = y < 0.07 and z < 0.31, 0.12 < y < 0.52 and z < 0.30
    if fore or hind:                                           # legs: grey down to the wrist / hock, tan
        if z < 0.05:                                           # below it and on the inner side
            return 'fur_paw'
        if z < (0.098 if fore else 0.15) or n.x < -0.3:
            return 'fur_leg'
        return 'fur_body'
    # (r2 O5: the dark lip strip is gone; black only on the nose pad)
    if y < -0.60 and z < mouth_z(y) + 0.002:                  # lower jaw and lip
        return 'cream'
    if -0.62 < y < -0.36 and n.z < -0.35:                     # under the jaw
        return 'cream'
    if -0.46 < y < -0.12 and x < 0.10 and z < 0.64 and n.y < -0.25:   # throat and chest front
        return 'cream'
    if -0.36 < y < 0.47 and n.z < -0.45 and x < 0.11:         # keel and belly
        return 'cream'
    if y > 0.70 and z < 0.36:                                  # tail tip
        return 'fur_dark'
    if -0.40 < y < 0.80 and n.z > 0.70 and z > 0.55:          # saddle along the back and tail top
        return 'fur_dark'
    return 'fur_body'


def mk(name, bm, palette, rule):
    ob = object_from_bm(name, bm, mirror=True)
    paint(ob, palette, rule)
    return ob


def surface(bmr):
    from mathutils.bvhtree import BVHTree
    return BVHTree.FromBMesh(bmr)


def ring_at(pos, u, t):
    """A point on the (stage-2) chain at fractional ring u and fractional corner t (0 spine .. 4 belly)."""
    i = int(math.floor(u)); fu = u - i
    j = min(int(math.floor(t)), 3); ft = t - j

    def on(ii):
        return pos(ii, j).lerp(pos(ii, j + 1), ft)
    return on(i).lerp(on(i + 1), fu)


def ring_centre(pos, u):
    i = int(math.floor(u)); fu = u - i
    c = [(pos(ii, 0) + pos(ii, 4)) / 2 for ii in (i, i + 1)]
    return c[0].lerp(c[1], fu)


def piece_ruff(pos, tree):
    """The ruff: a THICK collar (a closed 5-sided section swept round the neck between rings
    8.55 and 9.55) that wraps the sides of the neck, thin on the nape (no hood behind the ears),
    thickest on the cheeks and throat, and ends on the chest in four blunt clumps (two a side).
    Its inner rows are sunk 7 mm into the neck; where the clumps lie on the chest they ride 3 mm
    off it. Separate object: the neck keeps its clean loops."""
    bm = bmesh.new()
    axis = (ring_centre(pos, 9.9) - ring_centre(pos, 8.3)).normalized()
    TS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.8, 3.05, 3.28, 3.5, 3.75, 4.0]
    # r3 note 3 (no torus): the throat breaks into three downward clumps of unequal length: one on the
    # centre seam (the longest) and one a side 24 % shorter, a valley between; the side of the neck fades
    EXT = [0, 0, 0, 0, 0, 0, 0.012, 0.080, 0.040, 0.008, 0.068, 0.105]

    def T(t):                                   # collar thickness round the neck
        tab = [(0, 0.004), (1, 0.040), (2, 0.085), (3, 0.090), (4, 0.085)]   # r3: tapers to ~0 on the spine
        for (a, x0), (b, x1) in zip(tab, tab[1:]):
            if a <= t <= b:
                return x0 + (x1 - x0) * (t - a) / (b - a)
        return tab[-1][1]

    def radial(p, u):
        r = p - ring_centre(pos, u)
        r = r - axis * r.dot(axis)
        return r.normalized()

    def pt(u, t, h, ext=0.0):
        p = ring_at(pos, u, t)
        rd = radial(p, u)
        if ext:
            p = p + Vector((0, 0, -ext))
        loc = tree.find_nearest(p)[0]
        q = loc + rd * h
        if t in (0.0, 4.0):
            q.x = 0.0
        return q
    # r2 note 1 (no collar): on the top half the front rim is sunk into the neck (the ruff grows
    # out of it, no shelf), and the back edge breaks into clumps of unequal length at the nape:
    # t -> (extra length in rings, thickness factor at the clump); valleys between them are short
    CLUMP = {0.0: (0.34, 1.15), 0.5: (-0.05, 0.85), 1.0: (0.24, 1.20), 1.5: (-0.08, 0.85),
             2.0: (0.14, 1.10), 2.5: (0.0, 0.80), 2.8: (0.0, 0.85), 3.05: (0.0, 1.15), 3.28: (0.0, 0.90),
             3.5: (0.0, 0.70), 3.75: (0.0, 1.05), 4.0: (0.0, 1.15)}      # r3: scalloped thickness round the throat

    def rim(t):                                 # front-rim height factor: sunk on top, full at the sides
        return 0.06 + 0.16 * min(t, 2.5) / 2.5    # r3: the front rim is sunk everywhere (no ledge under the jaw)
    rows = {'IF': [], 'OF': [], 'OM': [], 'OB': [], 'IB': []}
    for t, e in zip(TS, EXT):
        du, fk = CLUMP.get(t, (0.0, 1.0))
        rows['IF'].append(pt(8.30, t, -0.010 if t < 2.5 else -0.007))
        rows['OF'].append(pt(8.62 if t < 2.5 else 8.55, t, rim(t) * T(t)))
        rows['OM'].append(pt(9.10, t, T(t) * fk))
        rows['OB'].append(pt(9.75 + 0.6 * du, t, (0.40 if e or du > 0 else 0.65) * T(t) * fk, e))
        rows['IB'].append(pt(9.90 + du, t, 0.003 if e else -0.007, e))
    order = ['IF', 'OF', 'OM', 'OB', 'IB', 'IF']
    R = {kk: ring(bm, [tuple(q) for q in rows[kk]]) for kk in rows}
    keys = []
    for a_, b_ in zip(order, order[1:]):
        for fi, f in enumerate(bridge(bm, R[a_], R[b_])):
            tm = (TS[fi] + TS[fi + 1]) / 2
            keys.append('cream' if tm > 2.3 else 'fur_body')
    # the top surface carries the neck's own paint (the saddle rule of the body), never lighter
    return mk('ruff', bm, pal('fur_body', 'fur_dark', 'cream'),
              lambda c, n, i: 'fur_dark' if keys[i] == 'fur_body' and n.z > 0.55 and abs(c[0]) < 0.09 else keys[i])


def piece_tail_brush(pos):
    """The brush: a sleeve over the tail from 22 % of its length to past the tip. It swells to
    about 2x the root width at 55-65 %, ends in a blunt capped taper, and carries three offset
    clumps underneath (belly-seam and keel-corner rows pushed out on alternate rings). The last
    20 % is dark, the top strip carries the saddle, the underside is cream."""
    bm = bmesh.new()
    C = [(pos(i, 0) + pos(i, 4)) / 2 for i in range(17, 23)]
    last = (C[-1] - C[-2]).normalized()
    C.append(C[-1] + last * 0.075)
    seg = [(b - a).length for a, b in zip(C, C[1:])]
    Lt = sum(seg[:-1])                                  # the body tail's own length

    def at(s):                                         # centre and direction at fraction s of Lt
        d = s * Lt
        for k, l in enumerate(seg):
            if d <= l or k == len(seg) - 1:
                return C[k].lerp(C[k + 1], d / l), (C[k + 1] - C[k]).normalized()
            d -= l
    # s, rx, rz, belly (j4) push, keel-corner (j3) push
    SEC = [(0.22, 0.060, 0.066, 1.00, 1.00), (0.32, 0.092, 0.100, 1.00, 1.00), (0.42, 0.108, 0.118, 1.20, 0.98),
           (0.52, 0.116, 0.128, 0.96, 1.14), (0.62, 0.120, 0.132, 1.20, 0.98), (0.72, 0.113, 0.124, 0.96, 1.12),
           (0.82, 0.100, 0.110, 1.16, 1.00), (0.90, 0.086, 0.094, 1.00, 1.00), (1.00, 0.066, 0.072, 1.00, 1.00),
           (1.05, 0.046, 0.050, 1.00, 1.00)]      # r3: a short blunt end (was 1.10: it hung into the leg gap)
    R = []
    for s, rx, rz, pb, pk in SEC:
        c, d = at(s)
        pts = [Vector(p) for p in tail_ring((c.y, c.z), (d.y, d.z), rx, rz)]
        cy, cz = c.y, c.z
        for j, f in ((4, pb), (3, pk)):
            q = pts[j]
            pts[j] = Vector((q.x * f, cy + (q.y - cy) * f, cz + (q.z - cz) * f))
        R.append(ring(bm, [tuple(p) for p in pts]))
    keys = []
    DARK = 0.84
    for k, (a_, b_) in enumerate(zip(R, R[1:])):
        for q, f in enumerate(bridge(bm, a_, b_)):
            if SEC[k][0] >= DARK - 0.03:
                keys.append('fur_dark')
            else:
                keys.append({0: 'fur_dark', 3: 'cream'}.get(q, 'fur_body'))
    cap(bm, list(reversed(R[0]))); keys.append('fur_body')
    cap(bm, R[-1]); keys.append('fur_dark')
    return mk('tail_brush', bm, pal('fur_body', 'fur_dark', 'cream'), lambda c, n, i: keys[i])


def piece_eye(body):
    c = sum(EYE, Vector()) / len(EYE)
    nrm = (EYE[1] - EYE[0]).cross(EYE[2] - EYE[0]).normalized()
    if nrm.x < 0:
        nrm = -nrm
    up = Vector((0, 0, 1)); up = (up - nrm * up.dot(nrm)).normalized()
    fw = nrm.cross(up).normalized()
    if fw.y > 0:
        fw = -fw
    bm = bmesh.new()
    # r3 note 4: a flat lens cut from the socket floor itself (8-vert rim at 0.95 of the floor, filling the socket; see
    # its area, 1.5 mm proud), a black pupil cap, dome 6.5 mm (< 1/3 of the width), a small square
    # catchlight on the pupil's upper front; the back cone is buried in the head (no float)
    Q = [c + (p_ - c) - nrm * (p_ - c).dot(nrm) for p_ in EYE]
    rim_p = []
    for k in range(4):
        rim_p += [Q[k], (Q[k] + Q[(k + 1) % 4]) / 2]
    keys = []

    def ringv(sc, h, shift=Vector()):
        return [bm.verts.new(c + shift + (p_ - c) * sc + nrm * h) for p_ in rim_p]
    shift = fw * 0.004
    rim = ringv(0.95, 0.0015)
    pup = ringv(0.30, 0.0056, shift)
    apex = bm.verts.new(c + shift + nrm * 0.0065)
    back_ = bm.verts.new(c - nrm * 0.004)
    n8 = len(rim)
    for q in range(n8):
        bm.faces.new([rim[q], rim[(q + 1) % n8], pup[(q + 1) % n8], pup[q]]); keys.append('eye')
        bm.faces.new([pup[q], pup[(q + 1) % n8], apex]); keys.append('nose')
        bm.faces.new([rim[(q + 1) % n8], rim[q], back_]); keys.append('eye')
    span = max((p_ - c).dot(up) for p_ in rim_p)
    hc = c + shift + up * (0.22 * span) + fw * 0.004
    s_ = 0.0024
    box = [bm.verts.new(hc + fw * a * s_ + up * b * s_ + nrm * h) for h in (0.003, 0.0085)
           for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for f in ([0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]):
        bm.faces.new([box[q] for q in f]); keys.append('cream')
    ob = object_from_bm('eye', bm, mirror=True)
    ob.modifiers['mirror'].use_clip = False
    paint(ob, pal('eye', 'nose', 'cream'), lambda cc, n, i: keys[i])
    return ob


def piece_toes(body):
    """Four separate low toes and a dark claw each on every paw (the base paw stays a clean block)."""
    bmr = edit(body)
    feet = []
    for leg in ('fore', 'hind'):
        sole = LEGS[leg][-1]
        c0 = sum(sole.values(), Vector()) / 6
        vs = [v.co.copy() for v in bmr.verts if v.co.z < 0.002 and (v.co - c0).length < 0.14]
        feet.append((min(q.x for q in vs), max(q.x for q in vs), min(q.y for q in vs), max(q.y for q in vs)))
    bmr.free()
    bm = bmesh.new()
    keys = []
    Z0 = 0.0035                                     # every toe floor rides 3.5 mm over the sole plane
    for x0, x1, y0, y1 in feet:
        xc, hw = (x0 + x1) / 2, (x1 - x0) / 2 * 0.70   # the sole's front edge spans ff = 0.7 of its width
        for q, u in enumerate((-0.72, -0.24, 0.24, 0.72)):
            tx = xc + u * hw
            mid = q in (1, 2)
            # r3 note 5 (no comb): the middle pair leads (~20 % longer than r2's outer + 50 %), the outer
            # toes splay +-8 deg and sit 0.6 cm back, so the four tips lie on an arc
            L = 0.045 if mid else 0.029
            yb = y0 + (0.010 if mid else 0.016)
            a8 = math.radians(0 if mid else 8) * (1 if u > 0 else -1)
            dv = Vector((math.sin(a8), -math.cos(a8), 0.0))
            sv = Vector((math.cos(a8), math.sin(a8), 0.0))
            b0 = Vector((tx, yb, 0.0))
            ws = min(1.0, hw / 0.052)                        # toes narrower than their share of the paw (gaps: no z-fight)
            secs = [(0.0, 0.0100 * ws, 0.026), (0.40, 0.0108 * ws, 0.022), (0.66, 0.0080 * ws, 0.015)]

            def P3(s, w_, h_):
                p_ = b0 + dv * s + sv * w_
                return (p_.x, p_.y, Z0 + h_)
            R = []
            for s, w_, h_ in secs:
                R.append(ring(bm, [P3(L * s, -w_, 0), P3(L * s, w_, 0), P3(L * s, w_ * 0.8, h_), P3(L * s, -w_ * 0.8, h_)]))
            tip = ring(bm, [P3(L, -0.0032, 0.0012), P3(L, 0.0032, 0.0012)])
            f = cap(bm, list(reversed(R[0]))); keys.append('fur_paw')
            for a_, b_ in zip(R, R[1:]):
                for f in bridge(bm, a_, b_, closed=True):
                    keys.append('fur_paw')
            c = R[2]                                # the claw: black on the front 40 %
            for vs in ([c[0], c[1], tip[1], tip[0]], [c[3], tip[0], tip[1], c[2]], [c[0], tip[0], c[3]], [c[1], c[2], tip[1]]):
                bm.faces.new(vs); keys.append('nose')
    ob = object_from_bm('toes', bm, mirror=True)
    ob.modifiers['mirror'].use_clip = False
    paint(ob, pal('fur_paw', 'nose'), lambda cc, n, i: keys[i])
    return ob


def stage3(k, body):
    paint(body, pal('fur_body', 'fur_dark', 'fur_leg', 'fur_paw', 'cream', 'ear_in', 'nose'), body_rule)
    bmr = edit(body)
    cache = {}

    def pos(i, j):
        if (i, j) not in cache:
            cache[(i, j)] = vert_near(bmr, P(i, j)).co.copy()
        return cache[(i, j)]
    tree = surface(bmr)
    pieces = [piece_ruff(pos, tree), piece_tail_brush(pos)]
    bmr.free()
    pieces += [piece_eye(body), piece_toes(body)]
    return pieces


def bones():
    """The armature from the joints the model was built on (J)."""
    fp = (J['pawL'][0], J['pawL'][1] - 0.03, 0.02)
    hp0 = (J['hpawL'][0], J['hpawL'][1] + 0.01, 0.045)
    hp1 = (J['hpawL'][0], J['hpawL'][1] - 0.07, 0.01)
    return [('hips', J['hip'], J['spine'], None),
            ('chest', J['spine'], J['neck'], 'hips', True),
            ('neck', J['neck'], J['head'], 'chest', True),
            ('head', J['head'], J['snout'], 'neck', True),
            ('tail0', J['tail0'], J['tail1'], 'hips'),
            ('tail1', J['tail1'], J['tail2'], 'tail0', True),
            ('tail2', J['tail2'], J['tail3'], 'tail1', True),
            ('tail3', J['tail3'], J['tail4'], 'tail2', True),
            ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
            ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
            ('paw.L', J['wristL'], fp, 'forearm.L', True),
            ('thigh.L', J['hipL'], J['stifleL'], 'hips'),
            ('shin.L', J['stifleL'], J['hockL'], 'thigh.L', True),
            ('meta.L', J['hockL'], hp0, 'shin.L', True),
            ('hpaw.L', hp0, hp1, 'meta.L', True)]


def both(d):
    """{'upperarm': x} -> same rotation on .L and .R."""
    out = {}
    for kk, v in d.items():
        if kk.endswith('.L') or kk.endswith('.R') or kk in ('hips', 'chest', 'neck', 'head') or kk.startswith('tail'):
            out[kk] = v
        else:
            out[kk + '.L'] = v; out[kk + '.R'] = v
    return out


def stage4(k, body, pieces):
    rig = armature(bones())
    skin(body, rig)
    for p in pieces:
        nm = p.name
        if 'ruff' in nm:
            bind(p, rig, body=body)            # borrows the neck/chest weights: moves with the skin
        elif 'eye' in nm:
            bind(p, rig, bone='head')
        elif 'tail_brush' in nm:
            bind(p, rig, body=body)            # r3: follows the tail's skin through the idle curl (no drift)
        else:
            bind(p, rig)                       # toes and claws: nearest bone (the paws)
    # idle: breathing chest, a slow look left and right, a lazy tail sway
    clip(rig, 'idle', {
        1: {'tail0': (-4, 0, 0), 'tail2': (10, 0, 0), 'tail3': (12, 0, 0)},
        12: {'chest': (1.5, 0, 0), 'neck': (0, 0, 7), 'head': (2, 0, 6), 'tail0': (-4, 0, 8), 'tail1': (0, 0, 6), 'tail2': (10, 0, 0), 'tail3': (12, 0, 0)},
        24: {'chest': (0, 0, 0), 'neck': (-3, 0, 0), 'head': (3, 0, 0), 'tail0': (-4, 0, 0), 'tail1': (0, 0, 0), 'tail2': (10, 0, 0), 'tail3': (12, 0, 0)},
        36: {'chest': (1.5, 0, 0), 'neck': (0, 0, -7), 'head': (2, 0, -6), 'tail0': (-4, 0, -8), 'tail1': (0, 0, -6), 'tail2': (10, 0, 0), 'tail3': (12, 0, 0)},
        48: {'tail0': (-4, 0, 0), 'tail2': (10, 0, 0), 'tail3': (12, 0, 0)}})
    # move (r2 note 4): a real trot, diagonal pairs A = fore.L + hind.R, B = fore.R + hind.L. The pairs hit
    # their extremes every 6 frames (f1 B forward, f7 A forward, f13 B, f19 A, f25 B), so the quarter and
    # half frames are opposite extremes; the swing leg folds at the passing frames in between. Shoulders
    # and hips reach 25 deg forward / 20 back; the stance paws counter-rotate so the soles stay flat.
    # Body bob: the hips drop 3.6 cm at the extremes (the legs' own shortening, L (1 - cos 25)) and rise
    # 1 cm at passing (~ +-2 % of the height); the neck counter-bobs so the head stays level.
    reach, back_ = -25, 20

    def trot(a_fore, a_hind, b_fore, b_hind, lift_a, lift_b):
        ext_ = not (lift_a or lift_b)
        d = {'upperarm.L': (a_fore, 0, 0), 'thigh.R': (a_hind, 0, 0),
             'upperarm.R': (b_fore, 0, 0), 'thigh.L': (b_hind, 0, 0),
             'forearm.L': (52 * lift_a, 0, 0), 'shin.R': (34 * lift_a, 0, 0), 'meta.R': (-22 * lift_a, 0, 0),
             'forearm.R': (52 * lift_b, 0, 0), 'shin.L': (34 * lift_b, 0, 0), 'meta.L': (-22 * lift_b, 0, 0),
             'paw.L': (25 * lift_a - (a_fore if not lift_a else 0), 0, 0),
             'paw.R': (25 * lift_b - (b_fore if not lift_b else 0), 0, 0),
             'hpaw.R': (-(a_hind if not lift_a else 0), 0, 0), 'hpaw.L': (-(b_hind if not lift_b else 0), 0, 0),
             'chest': (0, 0, 3 * (lift_a - lift_b)), 'neck': (-4 if ext_ else 2, 0, 0), 'head': (2 if ext_ else -1, 0, 0),
             'tail0': (-8, 0, 6 * (lift_a - lift_b)), 'tail1': (-3, 0, 3 * (lift_a - lift_b))}
        return d
    A_fwd = trot(reach, reach, back_, back_, 0, 0)
    B_fwd = trot(back_, back_, reach, reach, 0, 0)
    A_swing, B_swing = trot(0, 0, 0, 0, 1, 0), trot(0, 0, 0, 0, 0, 1)
    down, up = -0.036, 0.010
    clip(rig, 'move', {1: B_fwd, 4: A_swing, 7: A_fwd, 10: B_swing, 13: B_fwd, 16: A_swing, 19: A_fwd,
                       22: B_swing, 25: B_fwd},
         loc={f: {'hips': (0, 0, down if f in (1, 7, 13, 19, 25) else up)} for f in (1, 4, 7, 10, 13, 16, 19, 22, 25)})
    # attack: wind up, then a lunge-bite - neck out and down, forelegs brace, tail up
    clip(rig, 'attack', {
        1: {},
        8: both({'neck': (-12, 0, 0), 'head': (-6, 0, 0), 'chest': (-4, 0, 0), 'upperarm': (8, 0, 0),
                 'thigh': (-10, 0, 0), 'tail0': (-6, 0, 0)}),
        15: both({'neck': (28, 0, 0), 'head': (-10, 0, 0), 'chest': (4, 0, 0), 'upperarm': (-26, 0, 0),
                  'forearm': (6, 0, 0), 'thigh': (18, 0, 0), 'shin': (-8, 0, 0), 'tail0': (4, 0, 0), 'tail1': (-4, 0, 0)}),
        21: both({'neck': (22, 0, 0), 'head': (-4, 0, 0), 'chest': (3, 0, 0), 'upperarm': (-20, 0, 0),
                  'forearm': (4, 0, 0), 'thigh': (14, 0, 0), 'shin': (-6, 0, 0), 'tail0': (2, 0, 0), 'tail1': (-4, 0, 0)}),
        30: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, -0.03, 0)}, 15: {'hips': (0, 0.08, 0)},
             21: {'hips': (0, 0.06, 0)}, 30: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
