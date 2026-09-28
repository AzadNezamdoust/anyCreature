"""giant (w4): hunched mountain troll, staged box model.
Torso + head are ONE sweep of half-rings along a spine that stands up at the hips
and bends forward over the shoulders into the head (the outer side of the bend is
the hump, the inner side the throat). Legs come out of the crotch cap, arms out
of the shoulder side faces; both are hexagonal extrusions."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from mathutils import Vector

META = dict(creature='giant', model='opus')

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    pelvis=(0.0, 0.34, 1.00), spine=(0.0, 0.26, 1.70), chest=(0.0, 0.34, 2.45), neck=(0.0, 0.20, 3.05),
    head=(0.0, -0.62, 3.00), headtip=(0.0, -1.20, 3.00),
    clavL=(0.30, 0.30, 2.95), shoulderL=(1.18, 0.24, 2.80), elbowL=(1.40, 0.08, 2.00),
    wristL=(1.54, -0.26, 1.12), fistL=(1.53, -0.40, 0.30),
    hipL=(0.55, 0.34, 0.98), kneeL=(0.59, 0.22, 0.52), ankleL=(0.62, 0.32, 0.24), toeL=(0.64, -0.30, 0.06),
)

# torso sweep: (front point (y, z), bend angle phi deg, depth D, half width w)
TORSO = [
    ((-0.08, 0.88), 0, 0.88, 0.80),    # R0 crotch
    ((-0.40, 1.22), 0, 1.42, 0.90),    # R1 hip
    ((-0.60, 1.65), 0, 1.62, 0.88),    # R2 pot belly
    ((-0.47, 2.08), 5, 1.52, 0.84),    # R3 low chest
    ((-0.51, 2.36), 15, 1.85, 0.96),   # R4 chest
    ((-0.54, 2.50), 38, 1.80, 1.02),   # R5 shoulders
    ((-0.60, 2.58), 65, 1.55, 0.80),   # R6 hump / traps
    ((-0.70, 2.58), 85, 0.97, 0.44, 'head'),   # R7 back of head
    ((-0.97, 2.55), 90, 0.97, 0.45, 'head'),   # R8 head middle
    ((-1.22, 2.56), 90, 0.82, 0.38, 'head'),   # R9 face
]
# half profile: F0 front seam, F1 front corner, S1 side front, SM side, S2 side back, B1 back corner, B0 back seam
PROF = [(0.0, 1.0, 'f'), (0.62, 0.92, 'f'), (1.0, 0.40, 'f'), (1.0, 0.0, 'f'), (0.95, 0.45, 'b'), (0.60, 0.93, 'b'),
        (0.0, 1.0, 'b')]
# head: wide jaw corners, narrow cranium (a wedge, not a drum)
HPROF = [(0.0, 1.0, 'f'), (0.85, 0.95, 'f'), (1.0, 0.45, 'f'), (0.95, 0.0, 'f'), (0.78, 0.5, 'b'), (0.48, 0.95, 'b'),
         (0.0, 1.0, 'b')]
KEYS = ['F0', 'F1', 'S1', 'SM', 'S2', 'B1', 'B0']


def nvec(phi):
    p = math.radians(phi)
    return Vector((0.0, -math.cos(p), -math.sin(p)))


def torso_ring(Pf, phi, D, w, prof=None, fr=0.5):
    n = nvec(phi)
    prof = HPROF if prof == 'head' else PROF
    df, db = fr * D, (1 - fr) * D
    c = Vector((0.0, Pf[0], Pf[1])) - df * n
    return [c + Vector((x * w, 0, 0)) + ((s * df) if sd == 'f' else (-s * db)) * n for x, s, sd in prof]


def ext(bm, faces, names, offset):
    """extrude a region and return (result, {name: new vert}) by matching orig + offset."""
    off = Vector(offset)
    tgt = {nm: v.co + off for nm, v in names.items()}
    r = extrude(bm, faces, off)
    return r, {nm: min(r['verts'], key=lambda v: (v.co - t).length) for nm, t in tgt.items()}


def hexpts(c, t, hw, hd, shape):
    """ring positions in a limb frame: t along the limb, f forward, u outward."""
    c, t = Vector(c), Vector(t).normalized()
    f = Vector((0, -1, 0)); f = (f - f.dot(t) * t).normalized()
    u = f.cross(t).normalized()
    return {nm: c + a * hw * u + b * hd * f for nm, (a, b) in shape.items()}


ARM = dict(IF=(-0.75, 1.0), IM=(-1.0, 0.0), IB=(-0.75, -1.0), OB=(0.75, -1.0), OM=(1.0, 0.0), OF=(0.75, 1.0))
# leg rings are horizontal: u = +X, f = -Y
LEG = dict(F=(-0.15, 1.0), OF=(0.8, 0.5), O=(1.0, 0.0), OB=(0.8, -0.5), B=(-0.15, -1.0), I=(-1.0, 0.0))
FOOT = dict(F=(-0.05, 1.0), OF=(0.95, 0.75), O=(1.0, -0.05), OB=(0.6, -0.95), B=(-0.4, -1.0), I=(-1.0, 0.25))

ARM_RINGS = [  # centre, direction, hw, hd
    ((1.25, 0.22, 2.88), (0.80, 0.0, -0.60), 0.34, 0.40),   # deltoid
    ((1.32, 0.14, 2.40), (0.20, -0.05, -1.0), 0.30, 0.33),  # upper arm
    ((1.40, 0.06, 1.98), (0.15, -0.25, -1.0), 0.27, 0.29),  # elbow
    ((1.48, -0.10, 1.62), (0.10, -0.35, -1.0), 0.35, 0.33),  # forearm bulk
    ((1.54, -0.28, 1.14), (0.0, -0.15, -1.0), 0.23, 0.24),  # wrist
    ((1.54, -0.37, 0.88), (0.0, 0.0, -1.0), 0.34, 0.36),    # knuckle top of the fist
    ((1.52, -0.40, 0.22), (0.0, 0.0, -1.0), 0.31, 0.34),    # fist bottom
]
LEG_RINGS = [  # centre, hw, hd, shape
    ((0.58, 0.24, 0.63), 0.33, 0.42, LEG),   # above the knee
    ((0.60, 0.20, 0.45), 0.31, 0.40, LEG),   # knee
    ((0.62, 0.30, 0.26), 0.28, 0.34, LEG),   # ankle
    ((0.65, 0.16, 0.12), 0.36, 0.60, FOOT),  # top of the foot
    ((0.65, 0.16, 0.00), 0.36, 0.60, FOOT),  # sole
]


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, torso_ring(*r)) for r in TORSO]
    R = [dict(zip(KEYS, r)) for r in rings]
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b)
    # face cap: X = nose centre on the seam
    r9 = R[-1]
    X = bm.verts.new((0.0, -1.24, 2.97))
    cap(bm, [r9['F0'], r9['F1'], r9['S1'], X])
    cap(bm, [X, r9['S1'], r9['SM'], r9['S2']])
    cap(bm, [X, r9['S2'], r9['B1'], r9['B0']])
    # crotch cap: Xc on the seam, Mx the inner thigh
    r0 = R[0]
    Xc = bm.verts.new((0.0, 0.36, 0.86))
    Mx = bm.verts.new((0.24, 0.36, 0.87))
    cap(bm, [r0['F0'], r0['F1'], Mx, Xc])
    cap(bm, [Xc, Mx, r0['B1'], r0['B0']])
    legf = [cap(bm, [r0['F1'], r0['S1'], r0['SM'], Mx]), cap(bm, [r0['SM'], r0['S2'], r0['B1'], Mx])]
    recalc_normals(bm)

    # legs
    names = dict(F=r0['F1'], OF=r0['S1'], O=r0['SM'], OB=r0['S2'], B=r0['B1'], I=Mx)
    faces = legf
    for c, hw, hd, shape in LEG_RINGS:
        r, names = ext(bm, faces, names, (0, 0, -0.1))
        P = hexpts(c, (0, 0, -1), hw, hd, shape)
        for nm, v in names.items():
            v.co = P[nm]
        faces = r['faces']

    # arms from the two side faces of the shoulder band (R4-R5)
    r4, r5 = R[4], R[5]
    armf = [f for f in bm.faces if set(f.verts) in ({r4['S1'], r4['SM'], r5['SM'], r5['S1']},
                                                    {r4['SM'], r4['S2'], r5['S2'], r5['SM']})]
    assert len(armf) == 2
    names = dict(IF=r4['S1'], IM=r4['SM'], IB=r4['S2'], OF=r5['S1'], OM=r5['SM'], OB=r5['S2'])
    faces = armf
    for c, t, hw, hd in ARM_RINGS:
        r, names = ext(bm, faces, names, (0.1, 0, 0))
        P = hexpts(c, t, hw, hd, ARM)
        for nm, v in names.items():
            v.co = P[nm]
        faces = r['faces']
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    V = lambda p: vert_near(bm, p)
    # the stage-1 face ring R9, the nose point and the chest verts, looked up before anything moves
    f9 = dict(F0=V((0, -1.22, 2.56)), F1=V((0.323, -1.22, 2.58)), S1=V((0.38, -1.22, 2.786)),
              SM=V((0.361, -1.22, 2.97)), S2=V((0.296, -1.22, 3.175)), B1=V((0.182, -1.22, 3.36)),
              B0=V((0.0, -1.22, 3.38)))
    X = V((0.0, -1.24, 2.97))
    pec = [V((0.0, -0.51, 2.36)), V((0.595, -0.44, 2.38))]
    sub = V((0.0, -0.47, 2.08))
    crest = V((0.48, 0.033, 3.93))
    belly = [V((0.0, -0.60, 1.65)), V((0.546, -0.535, 1.65))]
    under = [V((0.0, -0.40, 1.22)), V((0.558, -0.343, 1.22))]
    taper = [(V((0.836, 0.5745, 1.65)), 0.78), (V((0.528, 0.963, 1.65)), 0.49), (V((0.798, 0.628, 2.176)), 0.76)]
    with k.topo(bm, 'loop', 'head loop behind the face: brow shelf, cheekbone and temple planes'):
        hl = loopcut(bm, edge_near(bm, (0.396, -1.095, 3.0)), t=0.5)
    # face: brow shelf overhangs, nose bridge forward, cheek recessed, underbite chin
    place([X], [(0.0, -1.37, 3.06)])
    place([f9['B0'], f9['B1'], f9['S2']], [(0.0, -1.31, 3.29), (0.20, -1.31, 3.30), (0.34, -1.25, 3.17)])
    place([f9['SM'], f9['S1'], f9['F1'], f9['F0']],
          [(0.36, -1.17, 2.97), (0.41, -1.21, 2.78), (0.35, -1.23, 2.56), (0.0, -1.31, 2.57)])
    for v in hl:
        if v.co.z > 3.25:              # the loop's top sits back and up: the forehead slopes off the brow
            v.co.y += 0.03
        elif 2.85 < v.co.z < 3.1:      # cheekbone out
            v.co.x += 0.04
    # chest: a pec shelf over a tucked sternum crease
    for v in pec:
        v.co.z -= 0.07; v.co.y -= 0.04
    sub.co.y += 0.04
    # pot belly hangs forward over a tucked underbelly; the back tapers under the hump
    for v in belly:
        v.co.y -= 0.07; v.co.z -= 0.05
    for v in under:
        v.co.y += 0.04
    for v, x in taper:
        v.co.x = x
    crest.co.z += 0.06                 # the hump peaks in a crest over the shoulder blades
    with k.topo(bm, 'inset', 'eye socket under the brow'):
        eye = inset(bm, [face_near(bm, (0.26, -1.24, 3.0), (0, -1, 0))], 0.4, -0.05)
    ev = list(eye[0].verts)
    move(ev, (0.02, 0, 0.05))
    commit(body, bm)


PAL = {'hide': '#66727f', 'dark': '#343b46', 'stone': '#8b867c', 'moss': '#6f8f3a', 'leather': '#a58c67',
       'tusk': '#d6c9a6', 'eye': '#f4b427'}


def prism(bm, c, n, r0, r1, h0, h1, k=6, rot=0.0, sq=1.0):
    """a k-sided cushion/slab on a surface: bottom ring h0 below c (radius r0), top ring h1 above (r1)."""
    c, n = Vector(c), Vector(n).normalized()
    a = n.orthogonal().normalized(); b = n.cross(a)
    def rr(h, r):
        return ring(bm, [c + n * h + (a * math.cos(rot + 2 * math.pi * i / k) + b * math.sin(rot + 2 * math.pi * i / k) * sq) * r
                         for i in range(k)])
    lo, hi = rr(-h0, r0), rr(h1, r1)
    bridge(bm, lo, hi, closed=True); cap(bm, list(reversed(lo))); cap(bm, hi)


def box(bm, c, ax, ay, az):
    c, ax, ay, az = Vector(c), Vector(ax), Vector(ay), Vector(az)
    v = {(i, j, l): bm.verts.new(c + ax * i + ay * j + az * l) for i in (-1, 1) for j in (-1, 1) for l in (-1, 1)}
    for f in ([(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)], [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
              [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)],
              [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]):
        bm.faces.new([v[q] for q in f])


def piece(name, bm, key, mirror=False):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, PAL, lambda c, n, i: key)
    return ob


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    def rule(c, n, i):
        if n.z < -0.55 or (n.y > 0.45 and c.z < 3.3):
            return 'dark'                       # the shadow side: back below the moss, undersides
        return 'hide'
    paint(body, PAL, rule)
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)
    near = lambda p: tree.find_nearest(Vector(p))[:2]
    out = []
    # moss clumps and rocks on the hump and shoulders
    spots = [((0.0, 0.35, 4.2), 0.42, 0.3, 1), ((0.0, 0.95, 3.8), 0.36, 1.1, 0), ((0.50, 0.20, 4.1), 0.38, 0.7, 0),
             ((0.85, 0.55, 3.7), 0.36, 0.2, 1), ((1.18, 0.22, 3.3), 0.32, 0.9, 1), ((0.60, 1.00, 3.4), 0.30, 0.5, 0),
             ((0.82, -0.10, 3.6), 0.28, 1.3, 0), ((0.0, 1.15, 3.2), 0.24, 0.1, 0), ((0.25, 1.15, 3.0), 0.18, 0.6, 1)]
    spots += [((-p[0], p[1], p[2]), r, -a, rk) for p, r, a, rk in spots if p[0] > 0]
    mb, rb = bmesh.new(), bmesh.new()
    for i, (p, r, a, rk) in enumerate(spots):
        loc, n = near(p)
        prism(mb, loc, n, r, r * 0.85, 0.07, 0.05, 7, a, 0.8)
        if rk:
            prism(rb, loc + n * 0.07, n + Vector((0.2 * math.cos(a), 0.1, 0)), r * 0.42, r * 0.34, 0.035, 0.035, 6, a + 0.4, 0.8)
    out += [piece('moss', mb, 'moss'), piece('rocks', rb, 'stone')]
    # belt: a wedge section, only its top inner edge sunk in the hide (one contact ring)
    yc, N = 0.30, 24
    def hit(z, t):
        d = Vector((math.sin(t), -math.cos(t), 0.0))
        return tree.ray_cast(Vector((0, yc, z)), d)[0], d
    bb, rows = bmesh.new(), [[], [], [], []]
    for i in range(N):
        t = 2 * math.pi * i / N
        (ht, d), (hb, _) = hit(1.40, t), hit(1.24, t)
        for row, pnt in zip(rows, (ht - d * 0.06, ht + d * 0.06, hb + d * 0.10, hb + d * 0.035)):
            row.append(bm_v(bb, pnt))
    for a_, b_ in zip(rows, rows[1:] + rows[:1]):
        bridge(bb, a_, b_, closed=True)
    out.append(piece('belt', bb, 'leather'))
    # loincloth flaps, front and back, hung from the belt
    yf = hit(1.32, 0.0)[0].y; yb = hit(1.32, math.pi)[0].y
    for nm, (y0, yb_, s_, zb) in (('loin_front', (yf - 0.05, yf + 0.15, -1, 0.55)), ('loin_back', (yb + 0.05, yb + 0.14, 1, 0.66))):
        lb = bmesh.new()
        ym, zm = (y0 + yb_) / 2, (1.33 + zb) / 2 + 0.05
        fr = [Vector(q) for q in ((-0.30, y0, 1.33), (0.30, y0, 1.33), (0.23, ym, zm), (0.12, yb_, zb + 0.10),
                                  (0.0, yb_, zb), (-0.12, yb_, zb + 0.10), (-0.23, ym, zm))]
        A = ring(lb, fr)
        B = ring(lb, [q + Vector((0, s_ * 0.06, 0)) for q in fr])
        bridge(lb, A, B, closed=True); cap(lb, list(reversed(A))); cap(lb, B)
        out.append(piece(nm, lb, 'stone'))
    # fingers: a knuckle row of four blocks on the front of each fist, stone nails at the tips
    fb, nb = bmesh.new(), bmesh.new()
    for sx in (1, -1):
        for j, dx in enumerate((-0.21, -0.07, 0.07, 0.21)):
            x = sx * (1.535 + dx)
            h = 0.30 if j else 0.24
            box(fb, (x, -0.75, 0.55 - h * 0.5), (0.062, 0, 0), (0, 0.075, 0), (0, 0, h * 0.5 + 0.05))
            box(nb, (x, -0.80, 0.55 - h - 0.02), (0.05, 0, 0), (0, 0.045, 0), (0, 0, 0.04))
        for q in ((0.49, -0.27), (0.64, -0.44), (0.84, -0.37)):
            box(nb, (sx * q[0], q[1] - 0.02, 0.05), (0.055, 0, 0), (0, 0.05, 0), (0, 0, 0.045))
    out += [piece('fingers', fb, 'hide'), piece('nails', nb, 'stone')]
    # eyes in the sockets, tusks from the lower jaw
    eb, tb = bmesh.new(), bmesh.new()
    sock = min((f for f in ebm.faces if f.calc_center_median().x > 0.1 and f.normal.y < -0.3),
               key=lambda f: (f.calc_center_median() - Vector((0.29, -1.22, 3.04))).length)
    c, n = sock.calc_center_median(), sock.normal
    prism(eb, c + n * 0.03, n, 0.065, 0.03, 0.035, 0.02, 5, 0.3, 0.7)
    loc, n = near((0.19, -1.40, 2.63))
    base = [loc - n * 0.05 + Vector(q) for q in ((0.07, 0.0, 0.05), (-0.06, 0.0, 0.05), (-0.06, 0.0, -0.05), (0.07, 0.0, -0.05))]
    tip = loc + n * 0.16 + Vector((0.07, 0, 0.32))
    bv = ring(tb, base); tv = tb.verts.new(tip)
    cap(tb, bv)
    for i in range(4):
        tb.faces.new([bv[i], bv[(i + 1) % 4], tv])
    out += [piece('eye', eb, 'eye', mirror=True), piece('tusk', tb, 'tusk', mirror=True)]
    ebm.free()
    return out


def bm_v(bm, p):
    return bm.verts.new(Vector(p))


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['headtip'], 'neck', True),
        ('clav.L', J['clavL'], J['shoulderL'], 'chest'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'clav.L', True),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hand.L', J['wristL'], J['fistL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: heavy breathing sway (48 f)
    clip(rig, 'idle', {1: {}, 16: {'chest': (4, 0, 0), 'spine': (0, 0, 2), 'head': (-3, 0, 0),
                                   'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0)},
                       32: {'chest': (-1, 0, 0), 'spine': (0, 0, -2), 'head': (1, 0, 0),
                            'upperarm.L': (-2, 0, 0), 'upperarm.R': (-2, 0, 0)}, 48: {}})
    # move: lumbering walk (32 f), arms swing against the legs, the torso rolls over the planted leg
    L = lambda th, sh, ua, sp: {'thigh.L': (th, 0, 0), 'thigh.R': (-th, 0, 0), 'shin.L': (sh[0], 0, 0),
                                'shin.R': (sh[1], 0, 0), 'upperarm.L': (-ua, 0, 0), 'upperarm.R': (ua, 0, 0),
                                'forearm.L': (8, 0, 0), 'forearm.R': (8, 0, 0), 'spine': (4, sp, 0), 'chest': (3, -sp, 0)}
    clip(rig, 'move', {1: L(16, (0, -8), 12, 4), 9: L(0, (0, -28), 0, 0), 17: L(-16, (-8, 0), -12, -4),
                       25: L(0, (-28, 0), 0, 0), 33: L(16, (0, -8), 12, 4)})
    # attack: two-handed overhead slam (40 f)
    up = {'upperarm.L': (95, 0, 0), 'upperarm.R': (95, 0, 0), 'clav.L': (0, 0, 20), 'clav.R': (0, 0, -20), 'forearm.L': (35, 0, 0), 'forearm.R': (35, 0, 0),
          'chest': (-10, 0, 0), 'spine': (-5, 0, 0), 'head': (8, 0, 0)}
    slam = {'upperarm.L': (45, 0, 0), 'upperarm.R': (45, 0, 0), 'forearm.L': (10, 0, 0), 'forearm.R': (10, 0, 0),
            'chest': (16, 0, 0), 'spine': (10, 0, 0), 'head': (-8, 0, 0)}
    clip(rig, 'attack', {1: {}, 14: up, 20: slam, 28: slam, 40: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
