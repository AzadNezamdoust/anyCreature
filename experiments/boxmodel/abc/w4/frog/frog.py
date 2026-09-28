import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from mathutils import Vector
from mathutils.bvhtree import BVHTree

META = dict(creature='frog', model='opus')

# the skeleton the model is built on (metres, faces -Y, left flank +X, feet on z = 0)
J = dict(
    hip=(0.0, 0.130, 0.090), mid=(0.0, 0.020, 0.125), neck=(0.0, -0.055, 0.175), snout=(0.0, -0.170, 0.230),
    throat0=(0.0, -0.075, 0.130), throat1=(0.0, -0.135, 0.180),
    eyeL0=(0.075, -0.087, 0.250), eyeL1=(0.088, -0.088, 0.294),
    tongue0=(0.0, -0.120, 0.222), tongue1=(0.0, -0.170, 0.222),
    shoulderL=(0.072, -0.045, 0.110), elbowL=(0.094, -0.055, 0.050), wristL=(0.097, -0.062, 0.020),
    handL=(0.105, -0.112, 0.005),
    hipL=(0.085, 0.160, 0.098), kneeL=(0.152, 0.036, 0.075), ankleL=(0.104, 0.165, 0.032),
    footL=(0.172, 0.040, 0.005),
)
# stage 1 uses the same joints as literal ring centres: eye turret on eyeL, front leg rings on
# shoulderL/elbowL/wristL/handL, hind leg rings through hipL/kneeL/ankleL/footL

# body half-sections: y, then (x, z) from the top seam round to the bottom seam
#      v0 top     v1 dorsal      v2 upper side (mouth line on the head)  v3 lower side  v4 belly edge  v5 bottom
SECTIONS = [
    (-0.178, [(0, 0.243), (0.024, 0.240), (0.036, 0.222), (0.032, 0.208), (0.024, 0.200), (0, 0.198)]),
    (-0.145, [(0, 0.262), (0.052, 0.258), (0.085, 0.222), (0.080, 0.194), (0.050, 0.176), (0, 0.170)]),
    (-0.105, [(0, 0.272), (0.055, 0.272), (0.106, 0.215), (0.092, 0.168), (0.060, 0.140), (0, 0.133)]),
    (-0.065, [(0, 0.270), (0.060, 0.268), (0.106, 0.205), (0.090, 0.140), (0.060, 0.100), (0, 0.093)]),
    (-0.030, [(0, 0.260), (0.060, 0.254), (0.092, 0.190), (0.084, 0.112), (0.058, 0.064), (0, 0.054)]),
    (0.020, [(0, 0.243), (0.058, 0.236), (0.099, 0.170), (0.098, 0.092), (0.070, 0.048), (0, 0.042)]),
    (0.070, [(0, 0.220), (0.064, 0.212), (0.102, 0.150), (0.104, 0.078), (0.072, 0.042), (0, 0.037)]),
    (0.115, [(0, 0.188), (0.058, 0.180), (0.095, 0.126), (0.091, 0.068), (0.066, 0.042), (0, 0.037)]),
    (0.150, [(0, 0.150), (0.048, 0.144), (0.082, 0.106), (0.078, 0.064), (0.050, 0.046), (0, 0.043)]),
    (0.174, [(0, 0.112), (0.034, 0.106), (0.048, 0.088), (0.044, 0.066), (0.028, 0.056), (0, 0.053)]),
]


def sweep(bm, face, c, n, u, a, b):
    """Extrude a quad and place the new ring as a rectangle: centre c, tube direction n,
    half-size a along u and b along n x u. Corners are matched by angle (no twist)."""
    n = V(n).normalized(); u0 = V(u); c = V(c)
    fn = face.normal.copy(); fc = face.calc_center_median()
    uo = (u0 - fn * u0.dot(fn)).normalized(); wo = fn.cross(uo)
    un = (u0 - n * u0.dot(n)).normalized(); wn = n.cross(un)
    r = extrude(bm, [face])
    vs = r['verts']
    old = sorted(vs, key=lambda v: math.atan2((v.co - fc).dot(wo), (v.co - fc).dot(uo)))
    oa = [math.atan2((v.co - fc).dot(wo), (v.co - fc).dot(uo)) for v in old]
    tg = sorted([(a, b), (-a, b), (-a, -b), (a, -b)], key=lambda p: math.atan2(p[1], p[0]))
    ta = [math.atan2(p[1], p[0]) for p in tg]

    def dang(x, y):
        d = abs(x - y) % (2 * math.pi)
        return min(d, 2 * math.pi - d)
    k = min(range(4), key=lambda s: sum(dang(oa[i], ta[(i + s) % 4]) for i in range(4)))
    for i, v in enumerate(old):
        p, q = tg[(i + k) % 4]
        v.co = c + un * p + wn * q
    f = r['faces'][0]
    f.normal_update()
    return f


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, [(x, y, z) for x, z in pts]) for y, pts in SECTIONS]
    F = {}
    for s in range(len(rows) - 1):
        for b, f in enumerate(bridge(bm, rows[s], rows[s + 1])):
            F[(s, b)] = f
    cap(bm, list(reversed(rows[0])))
    cap(bm, rows[-1])
    recalc_normals(bm)
    for f in bm.faces:            # outward check on the flank
        f.normal_update()

    # eyes: a turret out of the dorsal face over the cheek, two steps
    f = sweep(bm, F[(2, 1)], (0.082, -0.086, 0.272), (0.55, -0.15, 0.85), (0, 1, 0), 0.028, 0.024)
    f = sweep(bm, f, (0.090, -0.088, 0.296), (0.3, -0.1, 1.0), (0, 1, 0), 0.020, 0.017)

    # front leg: straight, from the lower side of the chest, then the hand forward
    f = sweep(bm, F[(3, 3)], (0.090, -0.048, 0.090), (0.1, -0.05, -1), (0, 1, 0), 0.017, 0.013)
    f = sweep(bm, f, (0.094, -0.055, 0.050), (0.05, -0.1, -1), (0, 1, 0), 0.014, 0.012)
    f = sweep(bm, f, (0.097, -0.062, 0.020), (0.05, -0.5, -1), (0, 1, 0), 0.011, 0.010)
    f = sweep(bm, f, (0.100, -0.082, 0.006), (0.1, -1, -0.1), (0, 0, 1), 0.006, 0.014)
    f = sweep(bm, f, (0.105, -0.112, 0.005), (0.1, -1, 0), (0, 0, 1), 0.005, 0.021)

    # hind leg: Z fold. Thigh forward along the flank, shin back under it, foot forward on the ground
    f = sweep(bm, F[(8, 2)], (0.095, 0.163, 0.098), (1, -0.3, 0), (0, 0, 1), 0.026, 0.017)
    f = sweep(bm, f, (0.135, 0.114, 0.106), (0.6, -1, 0), (0, 0, 1), 0.035, 0.027)
    f = sweep(bm, f, (0.147, 0.062, 0.100), (0.3, -1, -0.1), (0, 0, 1), 0.031, 0.023)
    f = sweep(bm, f, (0.155, 0.034, 0.082), (0.1, -0.6, -0.8), (1, 0, 0), 0.020, 0.020)
    f = sweep(bm, f, (0.150, 0.044, 0.052), (-0.2, 0.6, -0.8), (1, 0, 0), 0.018, 0.016)
    f = sweep(bm, f, (0.128, 0.100, 0.043), (-0.4, 1, -0.1), (1, 0, 0), 0.016, 0.014)
    f = sweep(bm, f, (0.106, 0.150, 0.037), (-0.4, 1, -0.2), (1, 0, 0), 0.014, 0.013)
    f = sweep(bm, f, (0.100, 0.178, 0.022), (0, 0.2, -1), (1, 0, 0), 0.013, 0.010)
    f = sweep(bm, f, (0.110, 0.140, 0.007), (0.4, -1, 0), (1, 0, 0), 0.013, 0.007)
    f = sweep(bm, f, (0.140, 0.090, 0.006), (0.55, -1, 0), (1, 0, 0), 0.016, 0.006)
    f = sweep(bm, f, (0.172, 0.040, 0.005), (0.6, -1, 0), (1, 0, 0), 0.028, 0.005)

    snap_seam(bm)
    if os.environ.get('FROG_DEBUG'):
        bm.faces.ensure_lookup_table()
        t = BVHTree.FromBMesh(bm)
        for i, j in t.overlap(t):
            if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
                say('HIT', [round(x, 3) for x in bm.faces[i].calc_center_median()],
                    [round(x, 3) for x in bm.faces[j].calc_center_median()])
    return object_from_bm('body', bm)



# ---------------------------------------------------------------- stage 2
from mathutils import Matrix
EYE_DIR = V((0.8, -0.35, 0.3)).normalized()


def eye_face(bm):
    cand = [f for f in bm.faces if f.calc_center_median().z > 0.265 and f.calc_center_median().x > 0.07]
    return max(cand, key=lambda f: f.normal.dot(EYE_DIR))


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'inset', 'eye socket: the gold eye piece sits in it, proud of the rim'):
        inset(bm, [eye_face(bm)], 0.36, 0.0)
    with k.topo(bm, 'loop', 'second elbow loop on the front leg: the bend of the straight arm'):
        loopcut(bm, edge_near(bm, (0.104, -0.058, 0.035)), t=0.5)
    with k.topo(bm, 'loop', 'extra knee loop on the hind leg: the thigh-shin fold'):
        loopcut(bm, edge_near(bm, (0.170, 0.040, 0.066)), t=0.5)
    bm.verts.ensure_lookup_table()
    f = eye_face(bm)                                   # the socket: inner face pushed in so the rim reads
    move(list(f.verts), f.normal * -0.0025)
    # snout: a V in plan like the reference top view; mouth corners stay wide
    for p, d in [((0.036, -0.178, 0.222), (-0.008, 0, 0)), ((0.032, -0.178, 0.208), (-0.007, 0, 0)),
                 ((0.085, -0.145, 0.222), (-0.010, 0, 0.002)), ((0.080, -0.145, 0.194), (-0.008, 0, 0))]:
        vert_near(bm, p).co += V(d)
    # a wide flat skull plane between the eyes
    flatten([vert_near(bm, p) for p in [(0, -0.145, 0.262), (0.052, -0.145, 0.258), (0, -0.105, 0.272),
                                         (0.055, -0.105, 0.272), (0, -0.065, 0.270), (0.060, -0.065, 0.268)]])
    # throat keel under the jaw
    for p, d in [((0, -0.105, 0.133), (0, 0, -0.004)), ((0, -0.065, 0.093), (0, -0.004, -0.002))]:
        vert_near(bm, p).co += V(d)
    # a slight crest down the spine so the back reads as two planes
    for p in [(0, 0.020, 0.243), (0, 0.070, 0.220), (0, 0.115, 0.188)]:
        vert_near(bm, p).co.z += 0.004
    commit(body, bm)


# ---------------------------------------------------------------- stage 3
PAL = {'skin': '#5fae3c', 'spot': '#2f6b2a', 'belly': '#efe0b0', 'gold': '#f2c230', 'black': '#151515',
       'tongue': '#d8646e'}


def mouth_z(y):
    if y < -0.145:
        return 0.222
    if y < -0.105:
        return 0.222 - (y + 0.145) / 0.04 * 0.007
    return 0.215 - (y + 0.105) / 0.04 * 0.010


def body_rule(c, n, i):
    x = abs(c.x)
    if c.y < -0.055 and 0.12 < c.z < mouth_z(c.y) - 0.002 and x < 0.11 and n.z < 0.6 and n.y > -0.9:
        return 'belly'                               # cream jaw and throat under the mouth line
    if x < 0.07 and 0.03 < c.z < 0.2 and (n.z < -0.3 or (c.y < 0.03 and n.y < -0.25 and n.z < 0.4)):
        return 'belly'                               # chest and belly
    return 'skin'


def solid(bm, rings):
    rs = [ring(bm, r) for r in rings]
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rs[0]))); cap(bm, rs[-1])
    return rs


def frame(d):
    d = V(d).normalized()
    t = V((0, 0, 1)).cross(d)
    t = t.normalized() if t.length > 1e-6 else V((1, 0, 0))
    return d, t, d.cross(t)


def rect(c, t, u, w, h):
    return [c + t * w + u * h, c - t * w + u * h, c - t * w - u * h, c + t * w - u * h]


def make_piece(name, bm, rule, mirror=True):
    recalc_normals(bm)
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, PAL, rule)
    return ob


def stage3(k, body):
    paint(body, PAL, body_rule)
    hb = evaluated_bm(body)
    tree = BVHTree.FromBMesh(hb)
    base = edit(body)
    ef = eye_face(base)
    ec, ed = ef.calc_center_median(), ef.normal.copy()
    mouth = [V((0, -0.178, 0.222))] + [vert_near(base, p).co.copy() for p in
                                        [(0.028, -0.178, 0.222), (0.075, -0.145, 0.224), (0.106, -0.105, 0.215),
                                         (0.106, -0.065, 0.205)]]
    base.free()
    pieces = []

    # eyes: a gold low-poly dome in the socket, a black horizontal pupil bar on its face
    bm = bmesh.new()
    d, t, u = frame(ed)
    r, h = 0.021, 0.015
    solid(bm, [[ec + d * off + (t * math.cos(a) + u * math.sin(a)) * r * rad for a in [j * math.pi / 4 for j in range(8)]]
               for off, rad in [(-0.004, 1.0), (0.45 * h, 0.95), (h, 0.58)]])
    pieces.append(make_piece('eye', bm, lambda c, n, i: 'gold'))
    bm = bmesh.new()
    pc = ec + d * h
    solid(bm, [rect(pc - d * 0.002, t, u, 0.0095, 0.0028), rect(pc + d * 0.0015, t, u, 0.0095, 0.0028)])
    pieces.append(make_piece('pupil', bm, lambda c, n, i: 'black'))

    # mouth: a bold black lip line wrapped round the mouth crease; the snout centre sits on the seam
    bm = bmesh.new()
    rs = []
    path = [mouth[0]]
    for p0, p1 in zip(mouth, mouth[1:]):                  # 3 sections per span: no needle quads
        path += [p0.lerp(p1, s_ / 3) for s_ in (1, 2, 3)]
    for p in path:
        o = V((p.x, p.y + 0.06, 0)).normalized()
        z = V((0, 0, 1))
        rs.append(ring(bm, [p + o * 0.004, p + z * 0.0035, p - o * 0.004, p - z * 0.0035]))
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, rs[-1])
    snap_seam(bm)
    pieces.append(make_piece('mouth', bm, lambda c, n, i: 'black'))

    # spots: irregular dark patches draped on the back (the two sides differ: mirror off)
    bm = bmesh.new()
    SP = [(0.030, -0.020, 0.013), (-0.035, 0.000, 0.011), (0.050, 0.040, 0.012), (-0.020, 0.050, 0.014),
          (0.015, 0.100, 0.012), (-0.050, 0.090, 0.011), (0.045, 0.125, 0.009), (-0.030, 0.135, 0.010),
          (0.000, -0.045, 0.009), (0.062, -0.012, 0.008), (-0.066, 0.030, 0.009), (0.022, 0.068, 0.008)]
    for si, (x, y, rr) in enumerate(SP):
        loc, nrm, _, _ = tree.ray_cast(V((x, y, 0.5)), V((0, 0, -1)))
        if loc is None:
            continue
        _, t1, t2 = frame(nrm)
        top, bot = [], []
        for j in range(6):
            a = j * math.pi / 3 + si * 0.7
            rad = 1.4 * rr * (0.75 + 0.4 * ((si * 7 + j * 3) % 5) / 4)
            q = loc + (t1 * math.cos(a) + t2 * math.sin(a)) * rad
            l2 = tree.ray_cast(q + nrm * 0.02, -nrm)[0]
            l2 = l2 if l2 is not None else q
            top.append(l2 + nrm * 0.0022); bot.append(l2 - nrm * 0.003)
        solid(bm, [bot, top])
    pieces.append(make_piece('spots', bm, lambda c, n, i: 'spot', mirror=False))

    # toes with round pads, and webbing plates between the hind toes: one piece, many shells
    bm = bmesh.new()
    up = V((0, 0, 1))

    def toe(root, dirn, L, w=0.0034):
        d_, t_, _ = frame(V((dirn.x, dirn.y, 0)))
        c0 = V((root.x, root.y, 0.0045)) - d_ * 0.004
        sec = lambda s_, ww, hh: rect(c0 + d_ * s_, t_, up, ww, hh)
        solid(bm, [sec(0, w, 0.0028), sec(L * 0.72, w * 0.72, 0.0024), sec(L * 0.80, w * 1.6, 0.0038), sec(L, w * 1.2, 0.003)])
        return c0, d_
    hc, hn, ht = V((0.105, -0.112, 0.005)), V((0.1, -1, 0)).normalized(), V((1, 0.1, 0)).normalized()
    for j, ang in enumerate([-40, -14, 14, 40]):
        toe(hc + ht * (-0.015 + j * 0.01), Matrix.Rotation(math.radians(ang), 3, 'Z') @ hn, 0.026)
    fc, fn, ft = V((0.172, 0.040, 0.005)), V((0.6, -1, 0)).normalized(), V((0.858, 0.514, 0)).normalized()
    roots = [toe(fc + ft * (-0.022 + j * 0.011), Matrix.Rotation(math.radians(ang), 3, 'Z') @ fn, 0.040)
             for j, ang in enumerate([-44, -22, 0, 22, 44])]
    for (c1, d1), (c2, d2) in zip(roots, roots[1:]):
        pts = [c1 + d1 * 0.005, c1 + d1 * 0.024, c2 + d2 * 0.024, c2 + d2 * 0.005]
        solid(bm, [[p_ + V((0, 0, -0.0017)) for p_ in pts], [p_ + V((0, 0, 0.0017)) for p_ in pts]])
    pieces.append(make_piece('toes', bm, lambda c, n, i: 'skin'))

    # tongue: hidden in the head at rest (tip just behind the snout); it lashes out in 'attack'
    bm = bmesh.new()
    tx, tz = V((1, 0, 0)), V((0, 0, 1))
    solid(bm, [rect(V((0, y, 0.222)), tx, tz, w, 0.003) for y, w in
               [(-0.118, 0.008), (-0.128, 0.009), (-0.140, 0.009), (-0.1768, 0.007)]])
    pieces.append(make_piece('tongue', bm, lambda c, n, i: 'tongue', mirror=False))
    hb.free()
    return pieces


# ---------------------------------------------------------------- stage 4
def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['hip'], J['mid'], None), ('chest', J['mid'], J['neck'], 'hips', True),
        ('head', J['neck'], J['snout'], 'chest', True), ('throat', J['throat0'], J['throat1'], 'chest'),
        ('tongue', J['tongue0'], J['tongue1'], 'head'), ('eye.L', J['eyeL0'], J['eyeL1'], 'head'),
        ('arm.L', J['shoulderL'], J['elbowL'], 'chest'), ('forearm.L', J['elbowL'], J['wristL'], 'arm.L', True),
        ('hand.L', J['wristL'], J['handL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'), ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['footL'], 'shin.L', True)], roll='auto')
    rig.data.bones['tongue'].use_deform = False      # the skin never follows the tongue
    skin(body, rig)
    rig.data.bones['tongue'].use_deform = True
    tongue = None
    for p in pieces:
        if p.name.endswith('tongue'):
            tongue = p
            continue
        bind(p, rig, body=body)
    bind(tongue, rig, bone='head')
    tip = list(range(12, 16))                          # the tip ring; rings 0-2 stay rigid in the head
    tongue.vertex_groups['head'].remove(tip)
    tongue.vertex_groups.new(name='tongue').add(tip, 1.0, 'REPLACE')

    # idle: throat pulse twice, then a blink (frogs pull the eyes down into the head)
    Z = (0, 0, 0)
    fr = [1, 7, 12, 18, 23, 30, 33, 40]
    thr = {7: (0, 0, -0.005), 18: (0, 0, -0.005)}
    eye = {30: (0, -0.007, 0)}
    clip(rig, 'idle', {f: {'chest': (1.5 if f in (12, 23) else 0, 0, 0)} for f in fr},
         loc={f: {'throat': thr.get(f, Z), 'eye.L': eye.get(f, Z), 'eye.R': eye.get(f, Z)} for f in fr})

    # move: a hop in place - crouch, launch (legs extend, arms back), land (arms forward), settle
    L = lambda a, b: {a + '.L': b, a + '.R': b}
    hop = {1: {},
           8: {'chest': (-6, 0, 0), **L('thigh', (6, 0, 0))},
           14: {'chest': (10, 0, 0), **L('thigh', (-38, 0, 0)), **L('shin', (-38, 0, 0)), **L('foot', (-25, 0, 0)),
                **L('arm', (-25, 0, 0))},
           20: {'chest': (2, 0, 0), **L('thigh', (-12, 0, 0)), **L('shin', (-10, 0, 0)), **L('arm', (22, 0, 0))},
           26: {'chest': (-4, 0, 0), **L('arm', (6, 0, 0))},
           32: {}}
    bones = ['chest', 'thigh.L', 'thigh.R', 'shin.L', 'shin.R', 'foot.L', 'foot.R', 'arm.L', 'arm.R']
    up = {8: -0.008, 14: 0.055, 20: 0.03, 26: -0.004}
    clip(rig, 'move', {f: {b: hop[f].get(b, Z) for b in bones} for f in hop},
         loc={f: {'hips': (0, 0, up.get(f, 0))} for f in hop})

    # attack: rear up and aim, the tongue lashes out and snaps back
    atk = {1: {}, 6: {'chest': (9, 0, 0), 'head': (6, 0, 0)}, 10: {'chest': (-5, 0, 0), 'head': (-4, 0, 0)},
           14: {'chest': (-5, 0, 0), 'head': (-4, 0, 0)}, 19: {'chest': (2, 0, 0)}, 24: {}}
    tl = {10: 0.13, 14: 0.12, 19: 0.01}
    clip(rig, 'attack', {f: {b: atk[f].get(b, Z) for b in ('chest', 'head')} for f in atk},
         loc={f: {'tongue': (0, tl.get(f, 0), 0)} for f in atk})
    return rig


run(META, stage1, stage2, stage3, stage4)
