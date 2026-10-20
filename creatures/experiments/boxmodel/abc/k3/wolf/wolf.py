import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='wolf', model='opus')
EYE = (0.098, -0.608, 0.888)                       # eye centre (in the socket), stage 2/3
META['keep_valleys'] = lambda c: c[0] > 0.05 and -0.64 < c[1] < -0.575 and 0.84 < c[2] < 0.96

# the skeleton the model is built on (metres, faces -Y, left flank +X)
J = dict(
    pelvis=(0.0, 0.40, 0.66), spine=(0.0, 0.05, 0.70), chest=(0.0, -0.22, 0.72),
    neck=(0.0, -0.36, 0.80), head=(0.0, -0.50, 0.88), snout=(0.0, -0.80, 0.80),
    tail0=(0.0, 0.58, 0.63), tail1=(0.0, 0.64, 0.50), tail2=(0.0, 0.725, 0.35), tail3=(0.0, 0.795, 0.17),
    shoulderL=(0.135, -0.29, 0.56), elbowL=(0.125, -0.27, 0.36), wristL=(0.11, -0.31, 0.10),
    fpawL=(0.11, -0.35, 0.0),
    hipL=(0.12, 0.37, 0.57), kneeL=(0.13, 0.30, 0.39), hockL=(0.12, 0.505, 0.235),
    hpawL=(0.115, 0.455, 0.0),
    earL=(0.10, -0.54, 0.99), eartipL=(0.10, -0.555, 1.10),
)


def sec(c, up, prof):
    """A half ring in a plane containing X: c = (y, z) centre, up = tilt in degrees
    (positive leans the section's up axis back, +Y), prof = [(x, s)] with s along up."""
    t = math.radians(up)
    uy, uz = math.sin(t), math.cos(t)
    return [(x, c[0] + s * uy, c[1] + s * uz) for x, s in prof]


def torso(y, top, bot, w, tilt=0.0, up=0.8, side=0.45, under=0.45):
    """An 8-sided torso section (half: top, upper, side, under, bottom).
    A deep keel: the under vertex sits well in from the side."""
    h = top - bot
    zc = (top + bot) / 2
    return sec((y, zc), tilt, [(0.0, h / 2), (up * w, h / 2 - 0.10 * h), (w, h * (side - 0.5)),
                               (under * w, -h / 2 + 0.03 * h), (0.0, -h / 2)])


def corners(face):
    """The 4 corners of a quad as fi, fo, bi, bo (front = -Y, outer = +X)."""
    vs = sorted(face.verts, key=lambda v: v.co.y)
    f = sorted(vs[:2], key=lambda v: v.co.x)
    b = sorted(vs[2:], key=lambda v: v.co.x)
    return dict(fi=f[0], fo=f[1], bi=b[0], bo=b[1])


def limb(bm, face, rings):
    """Extrude a quad through a list of rings; each ring = dict(fi, fo, bi, bo) of xyz.
    Returns the last face and the list of vertex rows."""
    rows = []
    for r in rings:
        cs = corners(face)
        key = {v: n for n, v in cs.items()}
        pos = {n: v.co.copy() for n, v in cs.items()}
        e = extrude(bm, [face])
        face = e['faces'][0]
        row = {}
        for v in e['verts']:
            n = min(pos, key=lambda n: (pos[n] - v.co).length)
            v.co = Vector(r[n]); row[n] = v
        rows.append(row)
    return face, rows


def paw(c, ax, ay):
    """An oval paw: a domed top ring (toes lower and leading) and a sole ring on z = 0.
    Returns two rings: the knuckle line and the sole."""
    x, y, z = c
    top = dict(fi=(x - ax * 0.72, y - ay * 1.05, 0.030), fo=(x + ax * 0.80, y - ay * 1.0, 0.030),
               bi=(x - ax * 0.80, y + ay * 0.55, 0.042), bo=(x + ax * 0.85, y + ay * 0.55, 0.042))
    sole = dict(fi=(x - ax * 0.75, y - ay * 1.15, 0.0), fo=(x + ax * 0.85, y - ay * 1.1, 0.0),
                bi=(x - ax * 0.80, y + ay * 0.60, 0.0), bo=(x + ax * 0.85, y + ay * 0.60, 0.0))
    return top, sole


def box(c, ax, ay, dz=(0, 0, 0, 0), dy=(0, 0, 0, 0)):
    """A limb ring around centre c: half width ax (X), half depth ay (Y).
    dz / dy: per-corner offsets in the order fi, fo, bi, bo."""
    x, y, z = c
    pts = dict(fi=(x - ax, y - ay, z), fo=(x + ax, y - ay, z), bi=(x - ax, y + ay, z), bo=(x + ax, y + ay, z))
    return {n: (p[0], p[1] + dy[i], p[2] + dz[i]) for i, (n, p) in enumerate(pts.items())}


def stage1(k):
    bm = bmesh.new()
    # ---- head -> neck -> torso -> tail: one chain of half rings -------------
    R = [
        # muzzle: a tapered box, nose pad at the tip
        [(0.0, -0.805, 0.815), (0.022, -0.803, 0.812), (0.034, -0.798, 0.776), (0.018, -0.79, 0.748), (0.0, -0.788, 0.744)],
        [(0.0, -0.715, 0.850), (0.040, -0.715, 0.846), (0.058, -0.712, 0.790), (0.036, -0.705, 0.738), (0.0, -0.702, 0.733)],
        # stop: the step between muzzle and skull
        [(0.0, -0.640, 0.895), (0.055, -0.640, 0.890), (0.080, -0.638, 0.815), (0.048, -0.625, 0.742), (0.0, -0.620, 0.736)],
        # brow / eye ring
        [(0.0, -0.595, 0.972), (0.076, -0.590, 0.962), (0.146, -0.575, 0.865), (0.072, -0.565, 0.752), (0.0, -0.560, 0.746)],
        # back of skull (ears sit on the upper-outer faces between these two)
        [(0.0, -0.500, 1.000), (0.074, -0.500, 0.990), (0.152, -0.500, 0.875), (0.085, -0.525, 0.755), (0.0, -0.530, 0.745)],
        # nape / throat: the thick neck (ruff mass)
        [(0.0, -0.420, 0.985), (0.095, -0.420, 0.955), (0.165, -0.440, 0.830), (0.110, -0.520, 0.670), (0.0, -0.548, 0.640)],
        [(0.0, -0.300, 0.945), (0.120, -0.305, 0.915), (0.195, -0.390, 0.760), (0.140, -0.500, 0.575), (0.0, -0.538, 0.545)],
        # chest front / shoulders (front leg face: side-under of this and the next)
        [(0.0, -0.180, 0.875), (0.135, -0.190, 0.840), (0.190, -0.300, 0.660), (0.105, -0.440, 0.480), (0.0, -0.470, 0.460)],
        [(0.0, -0.080, 0.855), (0.132, -0.085, 0.820), (0.178, -0.200, 0.620), (0.088, -0.220, 0.432), (0.0, -0.225, 0.412)],
        # ribs, waist (tuck-up), hips
        torso(0.030, 0.835, 0.445, 0.162, up=0.80, side=0.45, under=0.48),
        torso(0.170, 0.812, 0.535, 0.125, up=0.82, side=0.48, under=0.45),
        torso(0.280, 0.800, 0.520, 0.160, up=0.78, side=0.45, under=0.50),
        torso(0.440, 0.770, 0.500, 0.160, up=0.76, side=0.40, under=0.50),
        # rump
        [(0.0, 0.525, 0.720), (0.092, 0.530, 0.690), (0.112, 0.550, 0.600), (0.060, 0.535, 0.550), (0.0, 0.530, 0.540)],
    ]
    # tail: carried low, bushy in the middle
    tprof = lambda r, w: [(0.0, r), (0.75 * w, 0.55 * r), (w, -0.1 * r), (0.6 * w, -0.8 * r), (0.0, -r)]
    for (y, z), tilt, r, w in [(J['tail0'][1:], 50, 0.055, 0.055), (J['tail1'][1:], 57, 0.090, 0.085),
                               (J['tail2'][1:], 63, 0.095, 0.088), (J['tail3'][1:], 67, 0.050, 0.045)]:
        R.append(sec((y, z), tilt, tprof(r, w)))
    rows = [ring(bm, r) for r in R]
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, list(reversed(rows[0])))
    cap(bm, rows[-1])
    recalc_normals(bm)

    # ---- front leg: from the lower flank face behind the chest ------------
    ff = face_near(bm, (0.135, -0.28, 0.545), n=(1, 0, -1))
    ex, ey, ez = J['elbowL']; wx, wy, wz = J['wristL']; px, py, pz = J['fpawL']
    limb(bm, ff, [
        box((ex, ey, ez), 0.046, 0.066),
        box((0.117, -0.295, 0.24), 0.040, 0.052),
        box((wx, wy, wz), 0.031, 0.036),
        box((px, py + 0.010, 0.060), 0.033, 0.038),
        *paw((px, py, 0.0), 0.046, 0.064),
    ])
    # ---- hind leg: thigh, stifle forward, hock back ------------------------
    hf = face_near(bm, (0.12, 0.36, 0.565), n=(1, 0, -1))
    kx, ky, kz = J['kneeL']; hx, hy, hz = J['hockL']; qx, qy, qz = J['hpawL']
    limb(bm, hf, [
        box((kx, ky, kz), 0.052, 0.080, dz=(0, 0, 0.04, 0.04)),
        box((0.125, 0.405, 0.325), 0.041, 0.052),
        box((hx, hy, hz), 0.033, 0.046),
        box((qx, qy + 0.010, 0.060), 0.031, 0.036),
        *paw((qx, qy, 0.0), 0.045, 0.062),
    ])
    # ---- ear: tall and pointed, off the upper-outer skull face -------------
    ef = face_near(bm, (0.10, -0.545, 0.92), n=(1, 0, 1))
    tx, ty, tz = J['eartipL']
    limb(bm, ef, [
        dict(fi=(0.060, -0.572, 1.005), fo=(0.146, -0.566, 0.958), bi=(0.062, -0.515, 1.010), bo=(0.146, -0.510, 0.963)),
        dict(fi=(0.082, -0.566, 1.055), fo=(0.122, -0.563, 1.035), bi=(0.084, -0.528, 1.058), bo=(0.122, -0.527, 1.038)),
        dict(fi=(tx - 0.006, ty - 0.004, tz), fo=(tx + 0.006, ty - 0.004, tz - 0.004),
             bi=(tx - 0.006, ty + 0.004, tz), bo=(tx + 0.006, ty + 0.004, tz - 0.004)),
    ])
    snap_seam(bm, 1e-6)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    # ---- joint loops: a second ring where the limbs, neck and hips bend ----
    for p, t, why in [
        ((0.1075, -0.3625, 0.935), 0.5, 'neck: second ring between nape and mid-neck so the head nods without collapsing'),
        ((0.180, -0.318, 0.510), 0.5, 'shoulder: ring half way down the upper arm so the leg swings off the chest cleanly'),
        ((0.164, -0.340, 0.300), 0.35, 'elbow: second ring just below the elbow ring for the bend'),
        ((0.171, 0.250, 0.515), 0.5, 'hip: ring half way down the thigh so the hind leg swings without tearing the flank'),
        ((0.174, 0.286, 0.357), 0.4, 'stifle: second ring just below the knee for the bend'),
    ]:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p), t=t)
    # ---- face: eye socket under an overhanging brow ------------------------
    eye_f = face_near(bm, (0.089, -0.611, 0.883), n=(1, -0.3, 0.3))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the brow-cheek face; the eye piece sits in it'):
        sock = inset(bm, [eye_f], 0.32, -0.010)
    brow = vert_near(bm, (0.076, -0.590, 0.962))
    brow.co += Vector((0.019, -0.020, 0.004))          # the brow overhangs the socket (r30: +3% out, +2% fwd)
    cheek = vert_near(bm, (0.146, -0.575, 0.865))
    cheek.co += Vector((0.006, 0.0, -0.006))           # cheekbone plane under the eye
    # ---- planes: one deliberate rib-cage facet and one muzzle side plane ---
    rib = [vert_near(bm, p) for p in [(0.178, -0.200, 0.620), (0.1296, 0.030, 0.796),
                                      (0.162, 0.030, 0.6155), (0.1025, 0.170, 0.7844), (0.125, 0.170, 0.6735)]]
    flatten(rib)
    muz = [vert_near(bm, p) for p in [(0.040, -0.715, 0.846), (0.058, -0.712, 0.790),
                                      (0.055, -0.640, 0.890), (0.080, -0.638, 0.815)]]
    flatten(muz)
    # ---- throat: no forward bulge at the jaw-throat ring, so the head-down lunge
    # folds the throat skin as a smooth crease instead of turning a face over (repair r14)
    thr = vert_near(bm, (0.0, -0.548, 0.640))
    thr.co += Vector((0.0, 0.014, 0.008))
    # ---- tuck-up (repair r32): the waist underline rises from the chest to the flank,
    # most at the ring in front of the thigh; the low sides pulled in. Brisket untouched.
    for (y, zb, zu, xu), dz in [((0.170, 0.535, 0.5433, 0.05625), 0.030), ((0.280, 0.520, 0.5284, 0.080), 0.060)]:
        vert_near(bm, (0.0, y, zb)).co.z += dz
        vu = vert_near(bm, (xu, y, zu))
        vu.co.z += dz; vu.co.x -= 0.011
    # ---- pasterns (repair r35): the ring above the paw slimmed to ~80% so the leg tapers
    # into the foot instead of reading as a box tube
    for (px, py), ax, ay in [((J['fpawL'][0], J['fpawL'][1]), 0.033, 0.038),
                             ((J['hpawL'][0], J['hpawL'][1]), 0.031, 0.036)]:
        cc = Vector((px, py + 0.010, 0.060))
        for p in box(tuple(cc), ax, ay).values():
            v = vert_near(bm, p)
            v.co = cc + (v.co - cc) * Vector((0.82, 0.85, 1.0))
    # ---- paws: oval pads, the toe leading (repair r16): the sole's heel and toe
    # pulled in, the toe pushed forward, the knuckle heel narrowed
    for (px, py), ax, ay in [((J['fpawL'][0], J['fpawL'][1]), 0.046, 0.064),
                             ((J['hpawL'][0], J['hpawL'][1]), 0.045, 0.062)]:
        top, sole = paw((px, py, 0.0), ax, ay)
        for key, (dx, dy) in {'fi': (-0.026, -0.012), 'fo': (0.026, -0.012), 'bi': (-0.030, 0.0), 'bo': (0.030, 0.0)}.items():
            v = vert_near(bm, sole[key])
            v.co = Vector((px + dx, v.co.y + dy, v.co.z))
        for key, dx in {'bi': -0.036, 'bo': 0.036}.items():
            v = vert_near(bm, top[key])
            v.co.x = px + dx
    commit(body, bm)


PAL = {'fur': '#9c978e', 'saddle': '#65636b', 'tan': '#b59d76', 'cream': '#efe6cf',
       'eye': '#e0a030', 'nose': '#1e1b1b'}
SWEEP = Vector((0.0, 0.70, -0.35))                  # fur lies back and down


def body_rule(c, n, i):
    x, y, z = c
    if y < -0.79:
        return 'nose'
    if (Vector((abs(x), y, z)) - Vector(EYE)).length < 0.030:
        return 'saddle'                              # dark rim round the eye socket (r30)
    if y > 0.58 and z < 0.66:                        # the tail: a grey brush, dark on the last 30%
        if z < 0.26:
            return 'saddle'
        if z > 0.50 and n.z > 0.25:
            return 'saddle'                          # the saddle runs onto the tail root
        return 'fur'
    if z < 0.045 and n.y < -0.35 and y < 0.5:
        return 'saddle'                              # dark toe fronts under the claws (r29)
    if z < 0.40:
        return 'tan'                                 # legs below elbow and stifle
    if y < -0.56 and z < 0.80:
        return 'cream'                               # lip and lower muzzle, under the mouth line
    if (y < -0.20 and z < 0.75 and (n.y < -0.35 or n.z < -0.3)) or (y < -0.25 and z < 0.78 and x < 0.13 and n.x < 0.8):
        return 'cream'                               # bib and throat
    if n.z < -0.55:
        return 'cream'                               # belly
    if z > 1.0 and n.y > 0.3:
        return 'saddle'                              # backs of the ears
    if (n.z > 0.45 and -0.25 < y < 0.62 and z > 0.72) or (y > 0.56 and n.z > 0.25):
        return 'saddle'                              # back saddle down the tail
    return 'fur'


def blade(bm, base, d, n, L, w, t):
    """One fur clump / claw: a 5-vert spike, its base buried along -n, tip along d."""
    d = d.normalized()
    u = d.cross(n)
    if u.length < 1e-4:
        u = d.orthogonal()
    u.normalize()
    v = u.cross(d).normalized()
    b = base - n * 0.012
    q = ring(bm, [b + u * w / 2 + v * t / 2, b - u * w / 2 + v * t / 2, b - u * w / 2 - v * t / 2, b + u * w / 2 - v * t / 2])
    tip = ring(bm, [base + d * L])[0]
    for i in range(4):
        bm.faces.new([q[i], q[(i + 1) % 4], tip])
    bm.faces.new(list(reversed(q)))


def shingle(bm, base, d, n, L, w, t, sink=0.2, sh=(0.55, 0.36)):
    """A wide fur shingle: a thick base plate (w x t) sunk `sink` of its thickness into the
    skin, a broad shoulder ring at 55% of the length, and a blunt point. Lies along d."""
    d = d.normalized()
    u = d.cross(n)
    if u.length < 1e-4:
        u = d.orthogonal()
    u.normalize()
    v = u.cross(d).normalized()
    if v.dot(n) < 0:
        v = -v
    sag = (w / 2) ** 2 / (2 * 0.20)                   # the neck curves away under a wide plate
    b = base + v * (t / 2 - sink * t) - v * sag
    q = ring(bm, [b + u * w / 2 + v * t / 2, b - u * w / 2 + v * t / 2, b - u * w / 2 - v * t / 2, b + u * w / 2 - v * t / 2])
    m = b + d * (sh[0] * L) + v * (0.35 * t)
    r = ring(bm, [m + u * sh[1] * w + v * 0.30 * t, m - u * sh[1] * w + v * 0.30 * t,
                  m - u * sh[1] * w - v * 0.30 * t, m + u * sh[1] * w - v * 0.30 * t])
    tip = ring(bm, [b + d * L + v * 0.25 * t])[0]
    bridge(bm, q, r, closed=True)
    for i in range(4):
        bm.faces.new([r[i], r[(i + 1) % 4], tip])
    bm.faces.new(list(reversed(q)))


def hit(tree, o, d):
    loc, nor, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
    assert loc is not None, f'no surface from {o}'
    return loc, nor


def stage3(k, body):
    paint(body, PAL, body_rule)
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)
    pieces = []
    # ---- eye: an amber lens standing proud in the socket -------------------
    bm0 = edit(body)
    sf = face_near(bm0, EYE, n=(1, -0.3, 0.3))
    c, n = sf.calc_center_median(), sf.normal.copy()
    vs = [v.co.copy() for v in sf.verts]
    bm0.free()
    bm = bmesh.new()
    # almond lens (repair r30): 6 points, sharp front and back corners, flatter top and
    # bottom; long axis along the head (-Y projected in the socket plane); r18 size kept
    fa = Vector((0, -1, 0)); fa = (fa - n * fa.dot(n)).normalized(); fb = n.cross(fa).normalized()
    if fb.z < 0:
        fb = -fb
    ha = 0.95 * max(abs((v - c).dot(fa)) for v in vs); hb = 0.55 * max(abs((v - c).dot(fb)) for v in vs)
    alm = [(-1.0, 0.0), (-0.38, 0.62), (0.40, 0.55), (1.0, 0.0), (0.40, -0.55), (-0.38, -0.62)]
    lo = ring(bm, [c + fa * (a * ha) + fb * (b * hb) - n * 0.004 for a, b in alm])
    hi = ring(bm, [c + fa * (a * ha * 0.68) + fb * (b * hb * 0.68) + n * 0.008 for a, b in alm])
    bridge(bm, lo, hi, closed=True); cap(bm, list(reversed(lo))); cap(bm, hi)
    eye = object_from_bm('eyes', bm); paint(eye, {'eye': PAL['eye']}, lambda c, n, i: 'eye'); pieces.append(eye)
    # ---- neck ruff and cream bib: clumps swept back and down ----------------
    # three rows of small pointed shingles round the neck only (repair r21): cheek row 3,
    # mid row 4, rear row 3 per side, ~60% of the r12 plate, roots sunk 30%; rays from the
    # neck axis, perpendicular to it; roots in front of the withers and above z 0.64
    bm = bmesh.new(); roots = []
    NA = Vector((0, -0.78, 0.62)); NU = Vector((0, 0.62, 0.78))     # neck axis, its up
    for P, row in [((0, -0.48, 0.845), [(55, 0.080, 'fur'), (15, 0.085, 'cream'), (-25, 0.080, 'cream')]),
                   ((0, -0.43, 0.80), [(62, 0.085, 'fur'), (32, 0.085, 'fur'), (2, 0.085, 'fur'), (-22, 0.065, 'cream')]),
                   ((0, -0.36, 0.76), [(52, 0.085, 'fur'), (20, 0.080, 'fur'), (-10, 0.075, 'fur')])]:
        for a, L, col in row:
            ar = math.radians(a)
            dr = Vector((math.cos(ar), 0, 0)) + NU * math.sin(ar)
            loc, nor = hit(tree, Vector(P) + dr * 0.8, -dr)
            print(f'WOLF ruff root a={a} P={P} loc=({loc.x:.3f},{loc.y:.3f},{loc.z:.3f})')
            assert loc.z > 0.64 and (loc.y < -0.33 or loc.z > 0.80), f'ruff root off the neck: {loc}'
            lift = 0.25 if a > 25 and P[1] > -0.47 else 0.42                 # low clumps ride out over the throat crease (r22)
            shingle(bm, loc, nor * lift + SWEEP * 0.90, nor, L, 0.090, 0.024, sink=0.3, sh=(0.35, 0.30))
            roots.append((loc.copy(), col))
    ruff = object_from_bm('ruff', bm)
    paint(ruff, {'fur': PAL['fur'], 'cream': PAL['cream']},
          lambda c, n, i: min(roots, key=lambda r: (r[0] - c).length)[1])
    pieces.append(ruff)
    # (repair r13: the withers hackles are gone; the saddle is one smooth painted mantle)
    # ---- tail brush: side clumps and a dark tip ------------------------------
    bm = bmesh.new()
    ax = Vector((0, 0.38, -0.92))
    for (y, z), a, L in [((0.64, 0.50), 10, 0.07), ((0.72, 0.35), -10, 0.07), ((0.70, 0.42), 45, 0.06)]:
        ar = math.radians(a)
        loc, nor = hit(tree, (0.8 * math.cos(ar), y, z + 0.8 * math.sin(ar)), (-math.cos(ar), 0, -math.sin(ar)))
        blade(bm, loc, nor * 0.40 + ax * 0.9, nor, L, 0.070, 0.026)
    for x in (0.022,):
        loc, nor = hit(tree, (x, 0.795 + 0.38 * 0.6, 0.17 - 0.92 * 0.6), (0, -0.38, 0.92))
        blade(bm, loc, ax, nor, 0.09, 0.04, 0.03)
    tail = object_from_bm('tailbrush', bm)
    paint(tail, {'fur': PAL['fur'], 'saddle': PAL['saddle']}, lambda c, n, i: 'saddle' if c.z < 0.27 else 'fur')
    pieces.append(tail)
    # ---- claws: four per paw, the middle toes leading -----------------------
    bm = bmesh.new()
    for (px, py) in [(J['fpawL'][0], J['fpawL'][1]), (J['hpawL'][0], J['hpawL'][1])]:
        # short thick claws (repair r29): 2x the root thickness, 70% length, pitched down
        # so the tips reach the ground line; middle pair leading, outer pair splayed
        for dx, L, sp, pz in [(-0.020, 0.024, -8, -0.62), (-0.007, 0.030, 0, -0.50), (0.007, 0.030, 0, -0.50), (0.020, 0.024, 8, -0.62)]:
            loc, nor = hit(tree, (px + dx, py - 0.2, 0.019), (0, 1, 0))
            s = math.radians(sp)
            d = Vector((0.85 * math.sin(s), -0.85 * math.cos(s), pz))
            blade(bm, loc, d, nor, L, 0.012, 0.020)   # blade() sinks the root 0.012
    claws = object_from_bm('claws', bm); paint(claws, {'nose': PAL['nose']}, lambda c, n, i: 'nose')
    pieces.append(claws)
    ebm.free()
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('spine', J['pelvis'], J['spine'], None),
        ('chest', J['spine'], J['chest'], 'spine', True),
        ('neck', J['chest'], J['head'], 'chest', True),
        ('head', J['head'], J['snout'], 'neck', True),
        ('ear.L', J['earL'], J['eartipL'], 'head'),
        ('tail0', J['tail0'], J['tail1'], 'spine'),
        ('tail1', J['tail1'], J['tail2'], 'tail0', True),
        ('tail2', J['tail2'], J['tail3'], 'tail1', True),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('fpaw.L', J['wristL'], (J['fpawL'][0], J['fpawL'][1] - 0.05, 0.012), 'forearm.L', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'spine'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L', True),
        ('hpaw.L', J['hockL'], (J['hpawL'][0], J['hpawL'][1] - 0.05, 0.012), 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing through the chest, a quick ear twitch, a lazy tail
    TS = 20                                          # and carried a little to one side, so the dark tip
                                                     # sits behind a hind leg in the front view (r37)
    TP = -12                                         # tail root pitched back on every idle key (r33)
    br = lambda a: {'chest': (a, 0, 0), 'neck': (-a * 0.5, 0, 0), 'tail0': (TP, 0, TS)}
    clip(rig, 'idle', {1: br(0), 12: br(2.5), 20: br(3), 22: {**br(3), 'ear.L': (-14, 0, 6)},
                       24: {**br(3), 'ear.L': (0, 0, 0)}, 26: {**br(3), 'ear.L': (-10, 0, 4)},
                       28: br(2.5), 36: {**br(1.5), 'tail0': (TP, 0, TS + 5)}, 48: br(0)})
    # move: trot, diagonal pairs (left fore + right hind together)
    def trot(s, flexR, flexL):
        return {'upperarm.L': (18 * s, 0, 0), 'upperarm.R': (-18 * s, 0, 0),
                'thigh.R': (16 * s, 0, 0), 'thigh.L': (-16 * s, 0, 0),
                'forearm.R': (-38 * flexR, 0, 0), 'forearm.L': (-38 * flexL, 0, 0),
                'fpaw.R': (-20 * flexR, 0, 0), 'fpaw.L': (-20 * flexL, 0, 0),
                'shin.L': (-28 * flexR, 0, 0), 'shin.R': (-28 * flexL, 0, 0),
                'hpaw.L': (24 * flexR, 0, 0), 'hpaw.R': (24 * flexL, 0, 0),
                'neck': (3 * abs(s), 0, 0), 'tail0': (0, 0, 6 * s)}
    clip(rig, 'move', {1: trot(1, 0, 0), 7: trot(0, 1, 0), 13: trot(-1, 0, 0), 19: trot(0, 0, 1), 25: trot(1, 0, 0)})
    # attack: rear back, head-down lunge, snap, recover
    clip(rig, 'attack', {1: {}, 8: {'neck': (12, 0, 0), 'head': (6, 0, 0), 'chest': (4, 0, 0), 'thigh.L': (-8, 0, 0), 'thigh.R': (-8, 0, 0)},
                         14: {'neck': (-24, 0, 0), 'head': (-12, 0, 0), 'chest': (-5, 0, 0), 'upperarm.L': (16, 0, 0), 'upperarm.R': (16, 0, 0),
                              'thigh.L': (10, 0, 0), 'thigh.R': (10, 0, 0)},
                         17: {'neck': (-28, 0, 0), 'head': (-22, 0, 0), 'chest': (-5, 0, 0), 'upperarm.L': (16, 0, 0), 'upperarm.R': (16, 0, 0),
                              'thigh.L': (10, 0, 0), 'thigh.R': (10, 0, 0)},
                         20: {'neck': (-24, 0, 0), 'head': (-8, 0, 0), 'chest': (-4, 0, 0), 'upperarm.L': (12, 0, 0), 'upperarm.R': (12, 0, 0),
                              'thigh.L': (6, 0, 0), 'thigh.R': (6, 0, 0)},
                         26: {'neck': (-6, 0, 0), 'head': (-2, 0, 0)}, 32: {}},
         loc={1: {'spine': (0, 0, 0)}, 8: {'spine': (0, -0.03, -0.02)}, 14: {'spine': (0, 0.07, -0.03)},
              20: {'spine': (0, 0.06, -0.02)}, 32: {'spine': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
