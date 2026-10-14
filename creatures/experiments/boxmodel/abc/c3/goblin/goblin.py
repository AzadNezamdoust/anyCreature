import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import part_guide, part_rings, hull_sections, fit_to_guide, _plane_axes

# goblin, stage-1 cage on the PART GUIDE (c3). Grey form and topology only.
# One closed quad shell, modelled on the left half:
#   torso   6 rings x 12 sides (a hip loop, belly, waist, chest, shoulder ring), closed top and bottom by a 2 x 2 grid
#   legs    extruded from the outer column of the bottom grid: the root loop runs crotch -> groin -> iliac side (hip loop)
#   arms    extruded from two side faces under the shoulder ring: the root loop runs over the shoulder
#   neck    the inner column of the top grid carried up by two loops into a hole in the head's underside
#   head    its own mass: 5 rings front -> back (12 sides), a face ring + 2 x 2 face grid, the nose out of the grid's
#           centre face, the ear out of the temple face, a 2 x 2 grid on the back of the skull
# Every limb ring is sized from the guide's part stations (stn()), never a constant radius.

J = dict(
    pelvis=(0.0, 0.05, 0.42), spine=(0.0, 0.045, 0.56), chest=(0.0, 0.05, 0.675), neck=(0.0, -0.02, 0.775),
    head=(0.0, -0.07, 0.93), snout=(0.0, -0.29, 0.735),
    shoulderL=(0.172, 0.05, 0.660), elbowL=(0.261, 0.072, 0.492), wristL=(0.299, -0.004, 0.364), handL=(0.305, -0.10, 0.12),
    hipL=(0.108, 0.035, 0.39), kneeL=(0.098, -0.017, 0.253), ankleL=(0.080, 0.043, 0.131), toeL=(0.135, -0.09, 0.03),
    earL=(0.17, 0.02, 0.92), earTipL=(0.555, 0.29, 0.94),
    clothF=(0.0, -0.03, 0.29), clothB=(0.0, 0.165, 0.37),     # the loincloth's flaps (a stage-3 piece): only META['later'] reads them
)
PLAN = dict(spine=['pelvis', 'spine', 'chest', 'neck', 'head', 'snout'],
            limbs=dict(arm=['shoulderL', 'elbowL', 'wristL', 'handL'], leg=['hipL', 'kneeL', 'ankleL', 'toeL']),
            extra=[['earL', 'earTipL']])
INTENDED = {
    'leg limb thickness / length': "the sheet's side run at mid shin is the shin plus the hanging hand in front of it (0.17 m; the "
                                   "leg's own section there is 0.06 - 0.08 in the guide and in part_profiles). The model's hand "
                                   "hangs 1 - 2 cm clear of the shin in that view, so its run is the shin alone",
    'leg length / body height': "the sheet's centre-line clearance is the loincloth's tip (z 0.20); the loincloth is a stage-3 "
                                "piece (brief). The body's crotch is at 0.33, where the sheet's inner thigh ends (0.31)",
    'head profile': "the head stations on the neck > head bone cut through both ears (width = ear span; the reference there is "
                    "the plan view's straight ears or the guide's cone ear, and BRIEF 3 lets the side view's swept ears win), "
                    "and the first head > snout plane runs on into the shoulders. The stations that do measure the head "
                    "(neck, nose) are within 3 cm"}
META = dict(creature='goblin', model='opus', cage=True, J=J, plan=PLAN, iou_floor={'top': 0.45}, intended=INTENDED,
            landmarks={'eye': (0.108, -0.180, 0.890), 'mouth': (0.030, -0.180, 0.772)},
            later={'loincloth': dict(chain=['clothF', 'clothB'], radius=0.06)})

P_T = 2.4                                    # the torso's section exponent (the guide's torso_p)
ANG = (0, 20, 42, 66, 90, 114, 138, 160, 180)   # a torso half ring of 9 (16 sides): 3 = front corner, 4 = side, 5 = back corner


def tring(z, a, yf, yb, dz=None, p=P_T, bulge=0.0):
    """A torso half ring of 9: front seam .. side (4) .. back seam. a: half width, yf / yb: front and back, a
    superellipse of exponent p; dz: per-vertex z offsets; bulge: the front-centre vertices pushed forward (belly dome)."""
    cy, b = (yf + yb) / 2, (yb - yf) / 2
    out = []
    for i, deg in enumerate(ANG):
        th = math.radians(deg)
        s, c = math.sin(th), math.cos(th)
        x = a * abs(s) ** (2 / p)
        y = cy - b * math.copysign(abs(c) ** (2 / p), c) - (bulge if i < 2 else bulge * 0.4 if i == 2 else 0.0)
        out.append((0.0 if i in (0, 8) else x, y, z + (dz[i] if dz else 0.0)))
    return out


# torso rings, bottom -> top (sizes: the guide's torso stations, part_rings 'torso': pelvis 0.31 wide, belly 0.31 x 0.21,
# waist 0.27, under the chest 0.23 x 0.16, shoulders 0.34)
R0 = [(0, -0.052, 0.358), (0.030, -0.052, 0.355), (0.060, -0.050, 0.354), (0.126, -0.036, 0.378), (0.166, 0.045, 0.398),
      (0.126, 0.126, 0.378), (0.060, 0.140, 0.354), (0.030, 0.143, 0.355), (0, 0.144, 0.357)]      # the hip loop: crotch low, iliac side high
RB = [(0, 0.045, 0.336), (0.030, 0.045, 0.335), (0.060, 0.045, 0.336)]                             # bottom grid: seam mid, two interior (crotch)
SH = [(0, -0.070, 0.700), (0.070, -0.060, 0.693), (0.118, -0.040, 0.734), (0.148, -0.008, 0.724), (0.162, 0.036, 0.722),
      (0.146, 0.076, 0.722), (0.116, 0.094, 0.746), (0.068, 0.094, 0.756), (0, 0.094, 0.760)]      # shoulder ring (3..5: the arm root's top)
RT = [(0.078, 0.022, 0.736), (0.122, 0.030, 0.776)]                                               # top grid interior: neck base side, shoulder top
TORSO = [
    R0,
    tring(0.435, 0.167, -0.060, 0.166),                                                            # hips / haunch
    tring(0.500, 0.163, -0.066, 0.158, bulge=0.004),                                               # pot belly
    tring(0.562, 0.144, -0.053, 0.146),                                                            # waist
    tring(0.626, 0.124, -0.041, 0.110, dz=(0, 0, 0, 0, 0, 0.004, 0.010, 0.014, 0.016)),            # under the chest, armpit; upper back higher
    SH,
]

# head rings, front -> back. Half ring of 7: T top seam, A crown corner, B temple / outer brow, C cheekbone, D jaw, E under, U bottom seam
# widths from the guide's head stack (part_rings 'head': chin 0.21, jaw 0.25, cheek 0.29, cranium 0.34 at z 0.95, crown 0.25 at z 1.04)
HEAD = [
    ('F',  [(0, -0.210, 0.955), (0.070, -0.206, 0.958), (0.136, -0.182, 0.940), (0.158, -0.140, 0.852), (0.114, -0.160, 0.772), (0.050, -0.190, 0.716), (0, -0.198, 0.694)]),
    ('G',  [(0, -0.170, 1.022), (0.085, -0.162, 1.014), (0.152, -0.122, 0.975), (0.176, -0.088, 0.868), (0.140, -0.100, 0.754), (0.058, -0.140, 0.722), (0, -0.152, 0.708)]),
    ('G2', [(0, -0.122, 1.080), (0.108, -0.112, 1.058), (0.170, -0.072, 0.992), (0.180, -0.045, 0.878), (0.146, -0.060, 0.738), (0.072, -0.088, 0.804), (0, -0.100, 0.800)]),
    ('HD', [(0, -0.045, 1.100), (0.115, -0.040, 1.072), (0.172, -0.018, 0.980), (0.162, -0.012, 0.845), (0.134, -0.012, 0.836), (0.085, -0.015, 0.840)]),   # no U: the neck hole
    ('K',  [(0, 0.018, 1.070), (0.100, 0.026, 1.046), (0.148, 0.050, 0.968), (0.134, 0.056, 0.885), (0.105, 0.054, 0.880), (0.068, 0.052, 0.877), (0, 0.060, 0.878)]),
]
BACK = [(0, 0.074, 0.962), (0.075, 0.072, 0.958)]                                            # back-of-skull grid: seam mid, interior
# the face inside F: an inner ring (brow centre, nose bridge side, inner eye corners top and bottom, mouth side, upper lip)
FACE2 = [(0, -0.232, 0.922), (0.034, -0.232, 0.922), (0.066, -0.224, 0.916), (0.072, -0.198, 0.858), (0.108, -0.176, 0.810), (0.048, -0.204, 0.828), (0, -0.214, 0.824)]
N1 = (0.042, -0.212, 0.868)                                                                  # side of the nose root
EYE_IN, EYE_DEEP = 0.45, 0.016                                                               # the eye socket: a loop inside the eye plane, sunk
# the nose: out of the inner column (brow centre .. upper lip), 8-sided, hooked; the tip closes on a seam vertex
NOSE = [
    [(0, -0.258, 0.856), (0.030, -0.252, 0.860), (0.046, -0.236, 0.834), (0.040, -0.230, 0.800), (0, -0.236, 0.788)],
    [(0, -0.290, 0.796), (0.022, -0.284, 0.795), (0.030, -0.272, 0.772), (0.024, -0.264, 0.752), (0, -0.262, 0.750)],
    [(0, -0.300, 0.750), (0.020, -0.295, 0.745), (0.024, -0.286, 0.728), (0.020, -0.280, 0.712), (0, -0.280, 0.708)],
]
NOSE_TIP = (0, -0.293, 0.727)
# the mouth: a lip loop inside the two lower face quads, and a sunk loop inside it (the grin)
MOUTH = [(0, -0.222, 0.794), (0.046, -0.215, 0.798), (0.084, -0.190, 0.800), (0.086, -0.182, 0.774), (0.046, -0.206, 0.750), (0, -0.213, 0.746)]
MOUTH_IN, MOUTH_DEEP = 0.10, 0.026
# ear: a blade out of the temple face, swept back as the side view draws it (BRIEF 3: the side view wins). x stations;
# top and bottom edges on the front view's lines, thickness by eye (the guide's ear width is an aspect prior: a wing)
EAR = [(0.230, 0.056, 0.969, 0.810), (0.310, 0.050, 0.967, 0.852), (0.390, 0.042, 0.957, 0.892), (0.470, 0.036, 0.948, 0.918),
       (0.546, 0.022, 0.944, 0.924)]                                                         # (x, thickness, top z, bottom z)
# ring budget (part_rings 'arm' / 'leg', n=None): root, one mass ring per bone, 3 at the elbow / knee / wrist / ankle
ARM_T = [0.04, 0.16, 0.240, 0.315, 0.390, 0.47, 0.53, 0.572, 0.615, 0.73, 0.86, 0.99]
LEG_T = [0.17, 0.245, 0.324, 0.403, 0.49, 0.575]
NECK_S = (-0.021, 0.021)                     # the neck's loops inside the joint band, metres along the neck joint's bisector; with the base loop (-0.057)
                                             # and the head's hole (+0.055) four loops 0.037 apart (0.23 x the neck's width)
# foot: ankle base (level), heel ring (tilted: instep -> heel), mid foot, toe base, toe tip (guide 'leg_foot': 0.15 - 0.18 wide; soles on z = 0)
FOOT = [
    dict(OF=(0.120, -0.006, 0.108), IF=(0.066, -0.006, 0.108), OM=(0.134, 0.042, 0.100), IM=(0.048, 0.042, 0.100), OB=(0.114, 0.098, 0.096), IB=(0.066, 0.098, 0.096)),
    dict(OF=(0.134, -0.046, 0.100), IF=(0.062, -0.048, 0.100), OM=(0.178, 0.030, 0.066), IM=(0.030, 0.032, 0.066), OB=(0.140, 0.112, 0.0), IB=(0.060, 0.112, 0.0)),
    dict(OF=(0.152, -0.086, 0.096), IF=(0.074, -0.090, 0.096), OM=(0.236, -0.034, 0.048), IM=(0.020, -0.026, 0.040), OB=(0.214, -0.020, 0.0), IB=(0.030, -0.014, 0.0)),
    dict(OF=(0.178, -0.126, 0.082), IF=(0.084, -0.132, 0.082), OM=(0.224, -0.102, 0.034), IM=(0.024, -0.106, 0.034), OB=(0.214, -0.098, 0.0), IB=(0.036, -0.100, 0.0)),
    dict(OF=(0.185, -0.157, 0.060), IF=(0.092, -0.160, 0.060), OM=(0.206, -0.154, 0.028), IM=(0.070, -0.157, 0.028), OB=(0.185, -0.150, 0.0), IB=(0.092, -0.152, 0.0)),
]
NECK_IN = 0.88
FLAT = 0.55                                  # a limb ring's flat front / back, x its width (PART['limb_front'] 0.5)


def stn(parts, part, t):
    """The guide part's own station at t (0 = the chain's first joint, 1 = its last): centre, width, depth."""
    S = parts[part]['stations']
    s = [q['s'] for q in S]
    j = max(0, min(len(S) - 2, next((i for i in range(len(s)) if s[i] > t), len(s)) - 1))
    f = max(0.0, min(1.0, (t - s[j]) / max(1e-9, s[j + 1] - s[j])))
    a, b = S[j], S[j + 1]
    mix = lambda key: Vector(a[key]) * (1 - f) + Vector(b[key]) * f
    return dict(centre=mix('centre'), width=(1 - f) * a['width'] + f * b['width'], depth=(1 - f) * a['depth'] + f * b['depth'])


def tangent(names, t):
    """The limb's direction at t: each bone's own direction at its middle, the bisector at a joint."""
    P = [Vector(J[n]) for n in names]
    L = [(b - a).length for a, b in zip(P, P[1:])]
    D = [(b - a).normalized() for a, b in zip(P, P[1:])]
    tot = sum(L)
    cuts = [0.0]
    for l in L:
        cuts.append(cuts[-1] + l / tot)
    i = max(0, min(len(D) - 1, next((q for q in range(len(cuts)) if cuts[q] > t), len(cuts)) - 1))
    f = (t - cuts[i]) / (cuts[i + 1] - cuts[i])
    d0 = (D[i - 1] + D[i]).normalized() if i > 0 else D[i]
    d1 = (D[i] + D[i + 1]).normalized() if i + 1 < len(D) else D[i]
    f = max(0.0, min(1.0, f))
    w0, w1 = max(0.0, 1 - 2 * f), max(0.0, 2 * f - 1)                  # the joint's bisector fades out by mid bone
    return (d0 * w0 + d1 * w1 + D[i] * (1 - w0 - w1)).normalized()


def ring6(c, u, w, W, D):
    """A 6-sided limb section, a rounded box: O* outer (+u), I* inner, *F front (+w), *B back; W along u, D along w."""
    c, a, b = Vector(c), u * (W / 2), w * (D / 2)
    return dict(OF=c + a * FLAT + b, OM=c + a, OB=c + a * FLAT - b, IB=c - a * FLAT - b, IM=c - a, IF=c - a * FLAT + b)


def limb(bm, faces, cur, rings):
    """Extrude a 2-quad region ring by ring (a 6-sided limb); cur maps role -> boundary vert. Ends in two quads."""
    for rg in rings:
        r = extrude(bm, faces)
        m = {role: min(r['verts'], key=lambda q: (q.co - v.co).length) for role, v in cur.items()}
        for role, p in rg.items():
            m[role].co = Vector(p)
        faces, cur = r['faces'], m
    return faces, cur


def lerp_tab(tab, t):
    for (t0, v0), (t1, v1) in zip(tab, tab[1:]):
        if t <= t1:
            f = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
            return v0 + (v1 - v0) * f
    return tab[-1][1]


HAND_W = [(0.615, 0.076), (0.68, 0.130), (0.73, 0.170), (0.86, 0.124), (0.99, 0.096)]     # by eye: the guide reads one finger row (0.083); the sheet's spread hand is 0.135
HAND_D = [(0.615, 0.060), (0.73, 0.054), (0.86, 0.064), (0.99, 0.042)]     # curled fingers are thicker than the palm
HAND_TWIST = [(0.0, 0.0), (0.60, 0.0), (0.70, 45.0), (0.86, 45.0), (0.99, 65.0)]                             # degrees about the arm: the palm turned in, so the side view sees the hand's width (sheet: 0.12 deep)
ramp = lambda t, a, b: max(0.0, min(1.0, (t - a) / (b - a)))
ARM_X = lambda t: -0.008 * ramp(t, 0.0, 0.16) + 0.022 * ramp(t, 0.3, 0.47) - 0.020 * ramp(t, 0.6, 0.73)
ARM_Z = lambda t: -0.008 * ramp(t, 0.86, 0.99)                       # finger tips down to the sheet's (z 0.10)   # front view: the sheet's arm line
ARM_Y = lambda t: lerp_tab([(0.0, 0.0), (0.35, 0.0), (0.6, -0.036), (0.73, -0.018), (0.86, 0.012), (0.99, 0.062)], t) # side view: the hand hangs in front of the knee, finger tips curl back


# arm widths: the sheet mask's runs (part_profiles: 0.068, 0.059, elbow 0.098, 0.081, forearm 0.055, wrist 0.063) on the guide's
# stations (0.074, 0.060, 0.080, 0.058, 0.055): a deltoid, a thin upper arm, a knobby elbow, a thin forearm, a broad hand
ARM_W = [(0.0, 0.080), (0.04, 0.080), (0.16, 0.068), (0.24, 0.078), (0.315, 0.100), (0.39, 0.090), (0.47, 0.070), (0.53, 0.066), (0.572, 0.068), (0.615, 0.076)]


def arm_size(t, W, D):
    """Arm section from the guide's stations (width seen in the front / rear view, depth its aspect prior)."""
    if t > 0.60:
        return lerp_tab(HAND_W, t), lerp_tab(HAND_D, t)
    W = lerp_tab(ARM_W, t)
    if t < 0.10:
        W = max(W, 0.090)                          # the deltoid: the shoulder mass stands proud of the upper arm
    return W, min(max(D, 0.9 * W), 1.0 * W)


def arm_off(t):
    return Vector((ARM_X(t), ARM_Y(t), ARM_Z(t)))


# leg sections: the guide's thigh is a prior (no view sees it): by eye from the concept (a meaty thigh, a knobby knee, a thin shin)
LEG_W = [(0.0, 0.086), (0.17, 0.086), (0.245, 0.072), (0.324, 0.082), (0.403, 0.072), (0.49, 0.054), (0.575, 0.058)]
LEG_D = [(0.0, 0.112), (0.17, 0.112), (0.245, 0.108), (0.324, 0.116), (0.403, 0.088), (0.49, 0.066), (0.575, 0.070)]


def leg_size(t, W, D):
    return lerp_tab(LEG_W, t), lerp_tab(LEG_D, t)


def leg_off(t):
    return Vector((0.010 * (1 - ramp(t, 0.16, 0.46)), 0.008 * ramp(t, 0.15, 0.25) + 0.008 * ramp(t, 0.28, 0.42), 0))   # the thigh clear of the crotch; the calf back (side view)


def stage1(k):
    guide = part_guide(k)
    GP = k.guide_parts
    if os.environ.get('GOB_RINGS'):
        for nm in ('arm', 'leg', 'leg_foot', 'head', 'nose', 'neck', 'torso', 'extra0'):
            part_rings(GP, nm, label=nm)
    bm = bmesh.new()

    # ---- torso: 16-sided rings, strips; the bottom and top grids are 3 x 2 per half
    tr = [ring(bm, pts) for pts in TORSO]
    tb = [bridge(bm, tr[i], tr[i + 1]) for i in range(len(tr) - 1)]
    b0, top = tr[0], tr[-1]
    s_, c1, c2 = ring(bm, RB)
    bm.faces.new([b0[0], b0[1], c1, s_]); bm.faces.new([b0[1], b0[2], c2, c1])                # crotch, front
    bm.faces.new([s_, c1, b0[7], b0[8]]); bm.faces.new([c1, c2, b0[6], b0[7]])                # crotch, back
    leg_faces = [bm.faces.new([b0[2], b0[3], b0[4], c2]), bm.faces.new([c2, b0[4], b0[5], b0[6]])]
    g1, g2 = ring(bm, RT)
    bm.faces.new([top[1], top[2], g2, g1]); bm.faces.new([g1, g2, top[6], top[7]])            # trapezius, front and back
    bm.faces.new([top[2], top[3], top[4], g2]); bm.faces.new([g2, top[4], top[5], top[6]])    # shoulder top

    # ---- head: rings front -> back, the neck hole under G2..K
    hi, hr = {}, []
    for i, (nm, pts) in enumerate(HEAD):
        hi[nm] = i
        hr.append(ring(bm, pts))
    HR = lambda nm, j: hr[hi[nm]][j]
    hb = {}
    for i in range(len(hr) - 1):
        a, b = hr[i], hr[i + 1]
        for j in range(min(len(a), len(b)) - 1):
            hb[(HEAD[i][0], j)] = bm.faces.new([a[j], a[j + 1], b[j + 1], b[j]])
    kq = hr[hi['K']]
    m1, m2 = ring(bm, BACK)
    bm.faces.new([kq[0], kq[1], m2, m1]); bm.faces.new([kq[1], kq[2], kq[3], m2])
    bm.faces.new([m1, m2, kq[5], kq[6]]); bm.faces.new([m2, kq[3], kq[4], kq[5]])
    # face: the inner ring; brow and cheek strips to F
    f1 = hr[hi['F']]
    f2 = ring(bm, FACE2)
    bridge(bm, f2[:3], f1[:3])                                                               # forehead over the brow
    bm.faces.new([f2[3], f2[4], f1[4], f1[3]])                                               # cheek side
    n1 = ring(bm, [N1])[0]
    bm.faces.new([f2[1], f2[2], f2[3], n1])                                                  # between nose and eye (keeps the eye loop off the nose loop)
    # eye: a socket loop inside the eye plane (inner corners on the face ring, outer brow B and cheekbone C on F)
    eq = [f2[2], f1[2], f1[3], f2[3]]
    ec = sum((v.co for v in eq), Vector()) / 4
    ei = ring(bm, [v.co.lerp(ec, EYE_IN) + Vector((0, EYE_DEEP, -0.003)) for v in eq])
    bridge(bm, eq, ei, closed=True)
    bm.faces.new(ei)
    bm.faces.new([n1, f2[3], f2[4], f2[5]])                                                  # cheek, under the eye
    # nose: the inner column's loop (brow centre, brow mid, inner eye corner, upper lip) carried out to the hooked tip
    prev = [f2[0], f2[1], n1, f2[5], f2[6]]
    for pts in NOSE:
        nr = ring(bm, pts)
        bridge(bm, prev, nr)
        prev = nr
    nt = ring(bm, [NOSE_TIP])[0]
    bm.faces.new([prev[0], prev[1], prev[2], nt]); bm.faces.new([nt, prev[2], prev[3], prev[4]])
    # mouth: lip loop inside (upper lip, mouth side, jaw, chin), a sunk loop inside it, two quads across
    mo = [f2[6], f2[5], f2[4], f1[4], f1[5], f1[6]]
    ml = ring(bm, MOUTH)
    mc = sum((Vector(p) for p in MOUTH[1:5]), Vector()) / 4
    mi = ring(bm, [Vector((p[0] * (1 - MOUTH_IN) if p[0] else 0.0, p[1] + MOUTH_DEEP, p[2] + (mc.z - p[2]) * MOUTH_IN)) for p in MOUTH])
    bridge(bm, mo, ml)
    bridge(bm, ml, mi)
    bm.faces.new([mi[0], mi[1], mi[4], mi[5]]); bm.faces.new([mi[1], mi[2], mi[3], mi[4]])

    # ---- neck: three loops between the top grid's inner column (the neck base, on the shoulders) and the head's hole,
    #      spaced along the neck joint's bisector; the base loop's poles stay one face below the first neck loop
    N0 = [top[0], top[1], g1, top[7], top[8]]
    H = [HR('G2', 6), HR('G2', 5), HR('HD', 5), HR('K', 5), HR('K', 6)]
    jn = Vector(J['neck'])
    d1, d2 = (jn - Vector(J['chest'])).normalized(), (Vector(J['head']) - jn).normalized()
    bis = (d1 + d2).normalized()
    rows = [N0]
    for s in NECK_S:
        pts = []
        for a, b in zip(N0, H):
            sa, sb = (a.co - jn).dot(bis), (b.co - jn).dot(bis)
            pts.append(a.co.lerp(b.co, (s - sa) / (sb - sa)))
        cy = sum(p.y for p in pts) / len(pts)
        rows.append(ring(bm, [Vector((p.x * NECK_IN, cy + (p.y - cy) * NECK_IN, p.z)) for p in pts]))   # the neck is narrower than its base and the skull's hole
    rows.append(H)
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    recalc_normals(bm)

    # ---- arm: out of the two side faces under the shoulder ring; every ring from the guide's arm stations
    T = len(tr) - 1
    names = PLAN['limbs']['arm']
    rings = []
    for t in ARM_T:
        s = stn(GP, 'arm', t)
        u, w = _plane_axes(tangent(names, min(t, 0.999)))
        th = math.radians(lerp_tab(HAND_TWIST, t))
        u, w = u * math.cos(th) + w * math.sin(th), w * math.cos(th) - u * math.sin(th)
        W, D = arm_size(t, s['width'], s['depth'])
        rings.append(ring6(s['centre'] + arm_off(t), u, w, W, D))
    limb(bm, [tb[T - 1][3], tb[T - 1][4]],
         dict(OF=tr[T][3], OM=tr[T][4], OB=tr[T][5], IB=tr[T - 1][5], IM=tr[T - 1][4], IF=tr[T - 1][3]), rings)

    # ---- leg: out of the bottom grid's outer column; guide stations down to the ankle, then the foot
    names = PLAN['limbs']['leg']
    rings = []
    for t in LEG_T:
        s = stn(GP, 'leg', t)
        u, w = _plane_axes(tangent(names, t))
        W, D = leg_size(t, s['width'], s['depth'])
        rings.append(ring6(s['centre'] + leg_off(t), u, w, W, D))
    limb(bm, leg_faces, dict(OF=b0[3], OM=b0[4], OB=b0[5], IB=b0[6], IM=c2, IF=b0[2]), rings + FOOT)

    # ---- ear: a blade out of the temple face (B..C between HD and K)
    cur = dict(ft=HR('HD', 2), fb=HR('HD', 3), bb=HR('K', 3), bt=HR('K', 2))
    fq = hb[('HD', 2)]
    e0, e1 = Vector(J['earL']), Vector(J['earTipL'])
    fwd = Vector((0.573, -0.82, 0.0))                                                        # square to the ear, toward the face
    for x, th, zt, zb in EAR:
        f = (x - e0.x) / (e1.x - e0.x)
        y = e0.y + (e1.y - e0.y) * f
        c = Vector((x, y, 0.0))
        e = extrude(bm, [fq])
        cur = {r: min(e['verts'], key=lambda q: (q.co - v.co).length) for r, v in cur.items()}
        for r, off, z in (('ft', 0.5, zt), ('fb', 0.5, zb), ('bb', -0.5, zb), ('bt', -0.5, zt)):
            p = c + fwd * (off * th)
            cur[r].co = Vector((p.x, p.y, z))
        fq = e['faces'][0]

    for v in bm.verts:
        if v.co.z < 0.0:
            v.co.z = 0.0
    recalc_normals(bm)
    snap_seam(bm)
    if os.environ.get('GOB_POLES'):                                                          # poles near the neck band
        band = 0.4 * min((jn - Vector(J['chest'])).length, (Vector(J['head']) - jn).length)
        for v in bm.verts:
            n = len(v.link_edges) + (sum(1 for e in v.link_edges if e.other_vert(v).co.x > 1e-6) if v.co.x < 1e-6 else 0)
            pr = (v.co - jn).dot(bis)
            if n != 4 and abs(pr) < band + 0.012 and v.co.x < 0.3:
                print('BMK pole', n, tuple(round(q, 3) for q in v.co), 'proj %.3f band %.3f' % (pr, band))
        el = sorted((e.calc_length(), tuple(round(q, 3) for q in (e.verts[0].co + e.verts[1].co) / 2)) for e in bm.edges
                    if all((q.co - jn).dot(bis) > 0 and q.co.x < 0.2 for q in e.verts))
        print('BMK head edges', len(el), 'p10 %.4f p90 %.4f' % (el[len(el) // 10][0], el[len(el) * 9 // 10][0]), 'smallest', el[:26])
    return object_from_bm('body', bm)


run(META, stage1)
