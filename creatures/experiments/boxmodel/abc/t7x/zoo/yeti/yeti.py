import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit'))
sys.path.insert(0, KIT)
from bmkit import *
import parts as PT

# yeti (shaggy upright ape-biped), t7 hand box model, zoo workflow v2. Templates: zoo/troll (biped head, toes),
# zoo/werewolf (13-vertex control-point loft, minotaur arm trick, rhino leg transition ring, welded hands).
# ONE upright spine loft of 13-vertex half rings (front seam -> back seam), crotch -> crown, each ring drawn from
# 5 control points (front seam, front corner, side, back corner, back seam). The head sits low and forward in a
# hair hood that slopes straight down into a huge shoulder mantle: the head rings run back into the hump, so head,
# hood and hump are one mass (the sheet's silhouette). Arms from a 2 x 3 face region of the chest side whose TOP
# edge is the torso's widest ring (C2, the deltoid line), first arm ring = the root loop pushed out unshrunk.
# Legs from a 3 x 6 region of the pelvis underside and flank through a 45 % transition ring, straight to a big flat
# foot. Fur = big loft steps (the forearm cuff over the hand, the shin skirt over the foot) + a few big S3 clumps.
# Identity cue (yeti, not gorilla / troll): white shaggy fur over everything; a hooded head sunk forward in a fur
# mantle that slopes from the crown peak to the shoulders; barrel torso as deep as wide; massive arms widening
# downward into fur cuffs over big grey hands; grey face mask, hands and big flat feet; upright, not hunched.
META = dict(creature='yeti', detail_tier=2, model='opus', stage1_tris=(1800, 4400), total_tris=(2600, 6500),
            closeups=[('head', (0.0, -0.36, 2.12), 0.32, 'hero'),
                      ('shoulder', (0.62, 0.0, 1.62), 0.38, 'hero'),
                      ('hand', (0.83, -0.20, 0.70), 0.28, 'hero'),
                      ('foot', (0.38, -0.05, 0.12), 0.36, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.10, 0.90), spine=(0.0, 0.06, 1.20), chest=(0.0, 0.04, 1.50), neck=(0.0, 0.0, 1.84),
    head=(0.0, -0.18, 2.02), top=(0.0, -0.22, 2.38),
    shoulder=(0.64, 0.02, 1.62), elbow=(0.78, -0.03, 1.15), wrist=(0.82, -0.17, 0.87), hand=(0.83, -0.22, 0.52),
    hipL=(0.27, 0.16, 0.80), knee=(0.30, 0.18, 0.45), ankle=(0.33, 0.14, 0.14), toe=(0.40, -0.36, 0.04),
)


# ---------------------------------------------------------------- the loft
def torso5(yf, yb, W, fx=0.52, fy=0.13, sy=0.45, bx=0.70, by=0.15):   # r7: rounder barrel (was 0.62/0.10)
    D = yb - yf
    return [(0.0, yf), (W * fx, yf + D * fy), (W, yf + D * sy), (W * bx, yb - D * by), (0.0, yb)]


def ring13(c5, z, rnd=0.45):
    """5 control points -> 13 points front seam -> back seam: 3 steps per control segment, a blend of the straight
    chord (planes) and a Catmull-Rom curve (round-over), the seam ends mirrored for the tangent."""
    over = c5[5] if len(c5) > 5 else {}
    P = [Vector((x, y)) for x, y in c5[:5]]
    G = [Vector((-P[1].x, P[1].y))] + P + [Vector((-P[3].x, P[3].y))]
    out = []
    for s in range(4):
        p0, p1, p2, p3 = G[s], G[s + 1], G[s + 2], G[s + 3]
        for u in (0.0, 1 / 3, 2 / 3):
            lin = p1.lerp(p2, u)
            cr = 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                        + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
            q = lin.lerp(cr, rnd)
            out.append((max(q.x, 0.0) if s or u else 0.0, q.y, z))
    out.append((0.0, P[4].y, z))
    for j, (x, y) in over.items():          # hand-placed vertices: the face box inside the hair hood
        out[j] = (x, y, z)
    return out


KEY = [   # (name, z, 5 control points (x, y)) bottom -> top, read off reference side.png + front.png (metric grid)
    ('L0', 0.72, torso5(-0.20, 0.22, 0.13)),             # crotch
    ('L0b', 0.82, torso5(-0.29, 0.38, 0.38)),            # under the hips
    ('L1', 0.92, torso5(-0.31, 0.46, 0.47, bx=0.78)),    # hips / buttocks
    ('L2', 1.03, torso5(-0.34, 0.49, 0.47)),             # low belly
    ('B0', 1.14, torso5(-0.36, 0.48, 0.46)),             # waist
    ('B1', 1.26, torso5(-0.38, 0.44, 0.48)),             # belly top
    ('B2', 1.38, torso5(-0.40, 0.45, 0.51)),             # ribs
    ('C0', 1.49, torso5(-0.42, 0.48, 0.55)),             # pecs: the chest widens up and out ...
    ('C1', 1.59, torso5(-0.42, 0.50, 0.63)),             # ... (armpit -> deltoid) ...
    ('C2', 1.70, torso5(-0.40, 0.49, 0.73, fx=0.55)),     # ... into the deltoid line: the torso's WIDEST ring
    ('C3', 1.79, torso5(-0.37, 0.47, 0.70, fx=0.52)),    # shoulder top: the mantle slopes in
    ('T0', 1.86, [(0, -0.35), (0.20, -0.33), (0.66, -0.02), (0.46, 0.34), (0, 0.46)]),   # throat / trapezius mantle
    ('J0', 1.95, [(0, -0.47), (0.15, -0.43), (0.56, -0.06), (0.42, 0.30), (0, 0.43)]),   # chin / jaw underside
    ('M0', 2.03, [(0, -0.50), (0.15, -0.46), (0.44, -0.10), (0.34, 0.24), (0, 0.37), {4: (0.17, -0.38), 5: (0.30, -0.27)}]),   # mouth / muzzle
    ('N1', 2.11, [(0, -0.48), (0.16, -0.43), (0.35, -0.13), (0.27, 0.16), (0, 0.28), {4: (0.18, -0.36), 5: (0.28, -0.27)}]),   # nose
    ('E0', 2.18, [(0, -0.41), (0.16, -0.39), (0.29, -0.16), (0.22, 0.10), (0, 0.20), {4: (0.185, -0.33), 5: (0.265, -0.25)}]),   # eye / under the brow
    ('F0', 2.24, [(0, -0.45), (0.16, -0.41), (0.25, -0.18), (0.18, 0.05), (0, 0.12), {4: (0.19, -0.35), 5: (0.24, -0.26)}]),   # brow ridge
    ('F1', 2.31, [(0, -0.37), (0.14, -0.34), (0.21, -0.17), (0.14, 0.0), (0, 0.05)]),    # forehead / hood
    ('F2', 2.37, [(0, -0.26), (0.09, -0.25), (0.14, -0.16), (0.09, -0.06), (0, -0.03)]), # crown
]
# density: a straight in-between ring (pointwise lerp: every split face stays co-planar) where the outline bends
INSERT = ['L0b', 'C1']      # a ring inserted ABOVE each of these keys


# HEAD pass (2026-10-22): the face is built in the loft. Three new head rings, straight lerps of their neighbours
# (Mm the mouth line between the lower lip M0 and the upper lip N1, N2 the muzzle top / nose base between N1 and E0,
# Eu the upper lid between the eye ring E0 and the brow F0), and hand-placed face vertices v0-v5 (x, y, z: a face
# vertex may sit off its ring's height): a rounded muzzle wider than tall that juts 13 cm ahead of the eyes (the
# sheet's side view) and turns back into the cheeks, the mouth a thin ring step under the upper-lip overhang, the
# nose bridge (E0 v0) forward between the eyes, the eye band (E0/Eu v1-v3) sunk under a brow ring (F0) that
# overhangs it in two arches, cheekbone vertices (E0 v3-v4), the lower face narrowing to the chin, and the jaw (J0)
# tucked under the muzzle inside the hood: no grey jaw 'wings' (J0 v4 was x 0.29). The r31g S2 face moves are gone.
EXTRA = {'M0': ('Mm', 'N1', 0.45), 'N1': ('N2', 'E0', 0.5), 'E0': ('Eu', 'F0', 0.55)}   # lower key -> (name, upper key, t)
# r3b (Q1: 'the face sides are straight vertical walls'): the face side v4 follows a heart outline - widest at the
# cheekbones (E0/N2 0.194), narrowing to the brow (0.178) and down to the chin (0.14)
FACE = {
    'J0': {0: (0.0, -0.470, 1.950), 1: (0.050, -0.465, 1.950), 2: (0.095, -0.450, 1.950), 3: (0.130, -0.420, 1.950),
           4: (0.140, -0.370, 1.950), 5: (0.250, -0.290, 1.950)},
    'M0': {0: (0.0, -0.512, 2.000), 1: (0.050, -0.507, 2.002), 2: (0.098, -0.490, 2.008), 3: (0.136, -0.455, 2.018),
           4: (0.142, -0.390, 2.030), 5: (0.280, -0.275, 2.030)},
    'Mm': {0: (0.0, -0.517, 2.040), 1: (0.052, -0.512, 2.041), 2: (0.102, -0.495, 2.045), 3: (0.144, -0.462, 2.045),
           4: (0.160, -0.390, 2.050)},
    'N1': {0: (0.0, -0.538, 2.054), 1: (0.054, -0.533, 2.056), 2: (0.106, -0.513, 2.061), 3: (0.150, -0.474, 2.066),
           4: (0.182, -0.392, 2.082), 5: (0.280, -0.270, 2.110)},
    'N2': {0: (0.0, -0.512, 2.108), 1: (0.054, -0.506, 2.110), 2: (0.104, -0.488, 2.115), 3: (0.150, -0.452, 2.122),
           4: (0.194, -0.372, 2.138)},
    'E0': {0: (0.0, -0.445, 2.165), 1: (0.050, -0.425, 2.167), 2: (0.095, -0.406, 2.170), 3: (0.150, -0.386, 2.175),
           4: (0.194, -0.332, 2.180), 5: (0.265, -0.250, 2.180)},
    'Eu': {0: (0.0, -0.443, 2.206), 1: (0.050, -0.419, 2.208), 2: (0.095, -0.402, 2.210), 3: (0.150, -0.370, 2.214),
           4: (0.180, -0.324, 2.220)},
    'F0': {0: (0.0, -0.462, 2.240), 1: (0.050, -0.470, 2.255), 2: (0.100, -0.466, 2.260), 3: (0.152, -0.418, 2.256),
           4: (0.178, -0.356, 2.250), 5: (0.240, -0.260, 2.240)},
}


def _face(nm, pts):
    pts = list(pts)
    for j, q in FACE.get(nm, {}).items():
        pts[j] = q
    return pts


def stations():
    out = []
    for i, (nm, z, c5) in enumerate(KEY):
        out.append((nm, _face(nm, ring13(c5, z))))
        if nm in INSERT and i + 1 < len(KEY):
            a, b = ring13(c5, z), ring13(KEY[i + 1][2], KEY[i + 1][1])
            out.append((nm + '~', [tuple((Vector(p) + Vector(q)) / 2) for p, q in zip(a, b)]))
        if nm in EXTRA:
            en, up, t = EXTRA[nm]
            ku = next(q for q in KEY if q[0] == up)
            a, b = _face(nm, ring13(c5, z)), _face(up, ring13(ku[2], ku[1]))
            out.append((en, _face(en, [tuple(Vector(p).lerp(Vector(q), t)) for p, q in zip(a, b)])))
    return out


SECS = stations()


def P(nm):
    for n, pts in SECS:
        if n == nm:
            return [Vector(q) for q in pts]


# ---------------------------------------------------------------- limbs
def frame_chain(cs, rads, lateral=(1, 0, 0)):
    """(centre, e1, e2, r1, r2) per station: e1 the outward lateral axis across the limb, e2 front-back."""
    cs = [Vector(c) for c in cs]
    out = []
    for i, (c, (r1, r2)) in enumerate(zip(cs, rads)):
        d = (cs[min(i + 1, len(cs) - 1)] - cs[max(i - 1, 0)]).normalized()
        e2 = Vector((0, 1, 0)); e2 = (e2 - d * e2.dot(d)).normalized()
        e1 = e2.cross(d).normalized()
        if e1.dot(Vector(lateral)) < 0:
            e1 = -e1
        out.append((c, e1, e2, r1, r2))
    return out


def level(cs, rads):
    return [(Vector(c), Vector((1, 0, 0)), Vector((0, 1, 0)), r1, r2) for c, (r1, r2) in zip(cs, rads)]


# arm (sheet front: the arm WIDENS downward into a fur cuff; side: it hangs forward, wrist at y -0.17)
ARM_C = [(0.72, 0.02, 1.50), (0.755, 0.01, 1.38), (0.775, 0.0, 1.26), (0.79, -0.03, 1.15), (0.80, -0.08, 1.04),
         (0.81, -0.13, 0.95), (0.82, -0.17, 0.87)]
ARM_R = [(0.17, 0.21), (0.19, 0.22), (0.21, 0.23), (0.21, 0.22), (0.23, 0.23),
         (0.24, 0.24),       # the fur cuff: the widest ring, its underside a flat step in over the wrist
         (0.09, 0.13)]       # wrist: flat like the hand root (r2: the round 0.12 ring fought the flat hand)
ARM_ELBOW = 3


def arm_frames():
    """The arm's frames: rings across the arm path, but the fur cuff and the wrist LEVEL (r8: a cuff ring tilted
    with the forearm dropped its front 11 cm, under the wrist ring: a fold-over)"""
    return frame_chain(ARM_C, ARM_R)[:-3] + level(ARM_C[-3:], ARM_R[-3:])   # r9: the forearm ring too (its tilted front fell under the cuff)
# leg: a thick straight column (thigh, knee, shin), a fur skirt over the foot, then the big flat foot to the floor
LEG_C = [(0.295, 0.17, 0.66), (0.305, 0.18, 0.55), (0.31, 0.18, 0.45), (0.31, 0.185, 0.36), (0.315, 0.18, 0.27),
         (0.33, 0.15, 0.19), (0.38, 0.03, 0.08), (0.39, 0.02, 0.0)]
LEG_R = [(0.225, 0.26), (0.215, 0.255), (0.20, 0.245), (0.195, 0.24), (0.20, 0.245),   # r12: the sheet's massive legs
         (0.225, 0.28),      # the fur skirt over the foot
         (0.25, 0.37), (0.25, 0.375)]   # foot top, sole
LEG_KNEE = 2
T1_LEG = 0.45       # rhino: the leg's first ring = the region rim pulled 45 % toward the first section
ARM_REG, ARM_COLS = 'C1', (5, 6, 7)
LEG_REG, LEG_COLS = 'L0', (5, 6, 7, 8, 9, 10)


def corner(fr, ab):
    c, e1, e2, r1, r2 = fr
    return c + e1 * ab[0] * r1 + e2 * ab[1] * r2


def region_roles(faces, lo_ring, up_ring):
    """Roles (a, b) for a face region's vertices: the boundary loop spread evenly round the unit circle in the
    region's own frame (e1 lower ring -> upper ring = the limb's outer side, e2 = +y), interior vertices inside."""
    vs = sorted({v for f in faces for v in f.verts}, key=lambda v: tuple(v.co))
    fs = set(faces)
    bnd = [v for v in vs if any(f not in fs for f in v.link_faces)]
    inn = [v for v in vs if v not in bnd]
    lo = [v for v in vs if v in set(lo_ring)]
    up = [v for v in vs if v in set(up_ring)]
    cen = sum((v.co for v in vs), Vector()) / len(vs)
    e1 = (sum((v.co for v in up), Vector()) / len(up) - sum((v.co for v in lo), Vector()) / len(lo)).normalized()
    e2 = Vector((0, 1, 0)); e2 = (e2 - e1 * e2.dot(e1)).normalized()
    pr = {v: ((v.co - cen).dot(e1), (v.co - cen).dot(e2)) for v in vs}
    s1 = max(abs(pr[v][0]) for v in bnd) or 1
    s2 = max(abs(pr[v][1]) for v in bnd) or 1
    ang = {v: math.atan2(pr[v][1] / s2, pr[v][0] / s1) for v in bnd}
    # r10: the boundary in TOPOLOGICAL order (walk the region's rim edges): an angle sort mixed up the rim where the
    # widest ring bulges out along e1 (the C1 side vertex sorted to the front: a twisted arm)
    rim = {}
    for f in faces:
        for e in f.edges:
            if sum(1 for q in e.link_faces if q in fs) == 1:
                for v in e.verts:
                    rim.setdefault(v, []).append(e.other_vert(v))
    order = [min(bnd, key=lambda v: ang[v])]
    while len(order) < len(bnd):
        nxt = [w for w in rim[order[-1]] if w not in order]
        if not nxt:
            break
        order.append(nxt[0] if len(order) > 1 else max(nxt, key=lambda w: ang[w]))
    area = sum(pr[a_][0] * pr[b_][1] - pr[b_][0] * pr[a_][1] for a_, b_ in zip(order, order[1:] + order[:1]))
    if area < 0:
        order = [order[0]] + order[1:][::-1]
    n = len(order)
    sx = sum(math.cos(ang[v] - 2 * math.pi * rk / n) for rk, v in enumerate(order))
    sy = sum(math.sin(ang[v] - 2 * math.pi * rk / n) for rk, v in enumerate(order))
    ph = math.atan2(sy, sx)
    roles = {}
    for rk, v in enumerate(order):
        t = ph + 2 * math.pi * rk / n
        roles[v] = (math.cos(t), math.sin(t))
    for v in inn:
        roles[v] = (0.5 * pr[v][0] / s1, 0.5 * pr[v][1] / s2)
    nrm = e1.cross(e2).normalized()
    if nrm.dot(cen - Vector((0, cen.y, cen.z))) < 0 and abs(cen.x) > 0.01:
        nrm = -nrm
    return roles, (cen, e1, e2, s1, s2, nrm)


def grow(bm, faces, roles, frames):
    for fr in frames:
        keyed = [(o.co.copy(), ab) for o, ab in roles.items()]   # by position: extrude removes interior verts
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(keyed, key=lambda q: (q[0] - v.co).length)[1]
        if isinstance(fr, dict) and fr.get('kind') == 'lerp':    # a transition ring: rim pulled t toward a section
            for v, ab in new.items():
                v.co = v.co + (corner(fr['to'], ab) - v.co) * fr['t']
        elif isinstance(fr, dict):       # a hug ring: the root loop itself, pushed out (and maybe shrunk)
            c, n_, out, k_ = fr['c'], fr['n'], fr['out'], fr['k']
            for v in new:
                v.co = c + (v.co - c) * k_ + n_ * out
        else:
            for v, ab in new.items():
                v.co = corner(fr, ab)
        faces, roles = r['faces'], new
    return faces, roles


def hug_frame(info, out, k_=1.0):
    cen, e1, e2, s1, s2, nrm = info
    return dict(c=cen, n=nrm, out=out, k=k_)


def one_face(bm, faces):
    r = bmesh.ops.dissolve_faces(bm, faces=list(faces))
    return r['region'][0]


def hand_part(side=1):
    """The big grey ape hand hanging from the fur cuff: palm toward the thigh, fingers down and curled in."""
    w = Vector(J['wrist'])
    fwd = (Vector(J['hand']) - w).normalized()
    if side < 0:
        w, fwd = Vector((-w.x, w.y, w.z)), Vector((-fwd.x, fwd.y, fwd.z))
    up = Vector((side * 1.0, 0.0, 0.0)); up = (up - fwd * up.dot(fwd)).normalized()   # the back of the hand faces out (r3: the width axis on the wrist ring's long axis, y)
    return PT.hand_three_finger(origin=w + fwd * 0.02, width=0.30, forward=fwd, up=up, side=side, fingers=4, curl=0.62,
                                spread=8.0, finger_len=0.62, thumb=True, thumb_curl=0.45, knuckle=0.12,
                                wrist=(0.25, 0.16), open_root=True, name=f'hand_{"L" if side > 0 else "R"}')


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, _p) in enumerate(SECS)}
    rings = [ring(bm, pts) for _n, pts in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0])
    top = cap(bm, rings[-1])
    recalc_normals(bm)
    pk = bmesh.ops.poke(bm, faces=[top])                        # the crown: the hood's low peak, not a flat lid
    for v in pk['verts']:
        v.co.z += 0.03
    rest = []

    def region(lo, nsp, cols):
        i = idx[lo]
        faces = [spans[i + s][c] for s in range(nsp) for c in cols]
        return faces, rings[i], rings[i + nsp]

    # arms: 2 x 3 faces of the chest side right under the deltoid line (C1 -> C1~ -> C2): the region's top edge
    # is the torso's widest ring, the first arm ring is the root loop pushed out unshrunk (minotaur trick)
    faces, lo, up = region(ARM_REG, 2, ARM_COLS)
    roles, info = region_roles(faces, lo, up)
    fr = [hug_frame(info, 0.04, 1.0)] + arm_frames()
    grow(bm, faces, roles, fr)       # r4: the hand is an S3 piece rooted inside the cuff (the S1 weld self-crossed)
    # legs: 3 x 6 faces of the pelvis underside AND flank (L0 -> L0b -> L0b~ -> L1): the thigh rises out of the
    # flank, a 45 % transition ring (rhino), then level rings down to the flat foot
    faces, lo, up = region(LEG_REG, 3, LEG_COLS)
    roles, info = region_roles(faces, lo, up)
    lf = level(LEG_C, LEG_R)
    fr = [dict(kind='lerp', to=lf[0], t=T1_LEG)] + lf
    grow(bm, faces, roles, fr)
    snap_seam(bm)
    recalc_normals(bm)
    k.meta['_rest'] = [o.name for o in rest]
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
EYE_LO, EYE_HI, EYE_COL = 'E0', 'Eu', 2     # s4 r8: column 2, by the face corner: seen from the side (HEAD pass: under the new upper-lid ring)


def eye_face_centre():
    A, B_ = P(EYE_LO), P(EYE_HI)
    j = EYE_COL
    return (A[j] + A[j + 1] + B_[j] + B_[j + 1]) / 4


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.04 and abs(c.y - ec0.y) < 0.05 and abs(c.z - ec0.z) < 0.04


def limb_edge(bm, frames, i):
    """The edge running along a limb from ring i to ring i+1 on its outer side (a loop cut across it rings the limb)."""
    va = vert_near(bm, corner(frames[i], (1, 0)))
    tb = corner(frames[i + 1], (1, 0))
    return min(va.link_edges, key=lambda e: (e.other_vert(va).co - tb).length)


def stage2(k, body):
    """Joint loops (elbow, knee), the eye socket, a brow over it."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table()
    af = arm_frames()
    lf = level(LEG_C, LEG_R)
    cuts = [('elbow loop: the elbow bend', lambda: limb_edge(bm, af, ARM_ELBOW)),
            ('knee loop: the knee bend', lambda: limb_edge(bm, lf, LEG_KNEE))]
    for why, fe in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, fe(), t=0.5)
    # face pass: handles on the head-ring vertices at their S1 positions
    HV = {(nm, j): vert_near(bm, P(nm)[j]) for nm in ('T0', 'J0', 'M0', 'N1', 'E0', 'F0', 'F1', 'F2') for j in range(13)}
    hv = lambda nm, j: HV[(nm, j)]
    # HEAD pass: the face (brow, muzzle, mouth, cheeks, chin) is S1 ring vertices now (FACE); the r10 bevel and the
    # r29e / r30f face moves are gone
    ec0 = eye_face_centre()
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face under the brow, its floor pushed in'):
        inner = inset(bm, [f], 0.25, 0.0)
    move(list(inner[0].verts), -fn * 0.005)
    # s4 r2 (werewolf fix 3): the flat crotch cap met the thighs' inner walls at 115 deg (junction probe, groin crop):
    # the cap domes UP toward the seam, so the inner wall turns inward-up into it
    L0 = P('L0')
    for j, dz in ((0, 0.035), (1, 0.03), (2, 0.022), (3, 0.012), (12, 0.035)):   # r19: not v10-v11 (leg rim verts: lifting them left the transition faces a 14 mm seam strip)
        move([vert_near(bm, L0[j])], (0, 0, dz))
    # s4 r3: the folds sat on the cap's SIDE edge (L0 verts 4-8, x 0.11-0.13, z 0.72; dump of the s4 GLB): the thigh's
    # inner wall (x 0.07) runs back INWARD under the cap edge. The cap side drawn in to the wall's line.
    for j in range(3, 10):
        q = L0[j]
        move([vert_near(bm, q)], (-0.45 * q.x, 0, 0))
    # r4-r7, r13-r16 tried to soften the front groin fold (114 / 144 / 171 / 128 / 132 / 127 / 114 / 96). The fold
    # dump: the edge L0 v5 -> L0b v5 joins the triangle (L0 v4, L0 v5, L0b v5) = the belly underside, facing DOWN,
    # to the leg wall facing FORWARD: a 90 deg inside corner. r17: L0 v4 drops 6 cm (v3 3 cm), so that triangle
    # faces forward-down into the thigh front.
    for j, dz in ((3, 0.03), (4, 0.06)):     # r18: UP (r17 down turned it to face back: 150 deg)
        move([vert_near(bm, Vector((L0[j].x * 0.55, L0[j].y, L0[j].z + (0.012 if j == 3 else 0.0))))], (0, 0, dz))
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'skin2': '#b1b5bd', 'fur': '#e6e3dc', 'shade': '#c4bfb4', 'skin': '#7b8596', 'nail': '#a9b0bc', 'eye': '#3a281b',
       'inner': '#5f6878'}
# HEAD pass: the grey face follows the new head loops - each face of the head front is coloured by the loft span
# (lower ring) and column v it sits on: the chin front (J0 -> M0, v0-v1: the beard hides the rest), the lower lip,
# mouth step, muzzle front and top, eye band and brow underside out to the face side (v3 -> v4); the brow top (white
# eyebrows), the face side walls into the hood and the jaw stay fur (the r31g box rule painted the jaw 'wings' grey)
BLEND = False     # HEAD pass variant b: one face column of a mid tone between the grey skin and the white fur
SKIN_J = {'J0': 1, 'M0': 3, 'Mm': 3, 'N1': 3, 'N2': 3, 'E0': 3, 'Eu': 3}
_FQ = None


def face_span(c):
    """(lower ring, column, distance) of the nearest S1 head quad (J0 .. F1, columns 0-5), or (None, -1, 1e9)."""
    global _FQ
    if _FQ is None:
        _FQ = []
        names = [n for n, _p in SECS]
        for a, b in zip(names, names[1:]):
            if a in SKIN_J:
                A, B_ = P(a), P(b)
                for j in range(6):
                    _FQ.append((a, j, (A[j] + A[j + 1] + B_[j] + B_[j + 1]) / 4))
    q = Vector((abs(c.x), c.y, c.z))
    d, nm, j = min(((q - p).length, nm, j) for nm, j, p in _FQ)
    return nm, j, d


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if 1.9 < z < 2.3 and y < -0.3:
        nm, j, d = face_span(c)
        if d < 0.035 and j <= SKIN_J[nm]:
            return 'skin'                                                # the face
        if BLEND and d < 0.035 and j == SKIN_J[nm] + 1:
            return 'skin2'                                               # the blend band round the face
    if z < 0.10:
        return 'skin'                                                    # the big grey feet
    if x > 0.6 and z < 0.88:
        return 'skin'                                                    # hands
    return 'fur'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 4 for k_ in range(8)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.3)
    for j in range(8):
        a, b = j, (j + 1) % 8
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def full_bvh(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def hit(tree, o, d, far=3.0):
    loc, nrm, _i, _d = tree.ray_cast(Vector(o), Vector(d).normalized(), far)
    return loc, nrm


# fur TIERS (s3 r4): the stylised shag of the sheet as a few big jagged skirts, each a closed band: its top edge
# sunk 1.2 cm in the skin, hanging straight (it never dives: the radius is the max of the skin below it) out to a
# zig-zag hem of locks. (axis top, axis hem, angle range deg from +y (back) or None = full ring, flare, tooth, n,
# mirrored). The fur_clump locks (r1-r3) read as crystal spikes, not fur.
TIERS = [((0.0, 0.06, 2.00), (0.0, 0.06, 1.75), (-118, 118), 0.06, 0.10, 22, False, 0.04, 0.025),   # shoulder mantle
         ((0.0, -0.12, 2.37), (0.0, -0.12, 2.15), (-75, 75), 0.035, 0.07, 12, False, 0.012, 0.0),    # hood (back of head)
         ((0.0, -0.20, 1.995), (0.0, -0.20, 1.78), (138, 222), 0.03, 0.08, 8, False, 0.012, 0.0),    # beard, from the chin
         ((0.0, 0.0, 1.70), (0.0, 0.0, 1.44), (128, 232), 0.04, 0.10, 10, False, 0.012, 0.0),       # chest bib (review fix 2)
         ((0.0, 0.0, 1.42), (0.0, 0.0, 1.20), (140, 220), 0.035, 0.09, 8, False, 0.012, 0.0),       # belly bib (review fix 2)
         ((0.0, 0.08, 1.12), (0.0, 0.08, 0.95), None, 0.05, 0.09, 24, False, 0.012, 0.0),           # hip skirt
         ((0.752, 0.01, 1.47), (0.788, -0.025, 1.28), None, 0.05, 0.09, 12, True, 0.012, 0.0),      # upper arm
         ((0.795, -0.06, 1.17), (0.80, -0.085, 1.04), None, 0.04, 0.07, 12, True, 0.012, 0.0),      # elbow / forearm
         ((0.30, 0.175, 0.66), (0.305, 0.18, 0.48), None, 0.045, 0.09, 14, True, 0.012, 0.0)]       # thigh
# s3 r11: (..., sink, lift): only the mantle needs the deep sink + lifted first row (its z-fight on the hump); on the
# others the 4 cm ledge read as a belt. Teeth longer (0.07-0.10, notches 0.3 up): locks, not a band.


def tier(tree, top, hem, rng, flare, tooth, n, sink=0.012, lift=0.0, th=0.028):
    """A jagged fur skirt round an axis (top -> hem); a closed 5-vertex section per angle, end caps on a partial."""
    top, hem = Vector(top), Vector(hem)
    ax = (hem - top).normalized()
    e1 = Vector((0, 1, 0)); e1 = (e1 - ax * e1.dot(ax)).normalized()     # angle 0 = back (+y)
    e2 = ax.cross(e1).normalized()
    if e2.x < 0:
        e2 = -e2
    L = (hem - top).length
    rad = lambda c, d: ((lambda h: (h[0] - c).length if h[0] is not None else None)(hit(tree, c, d, 2.0)))
    full = rng is None
    a0, a1 = (0.0, 360.0) if full else rng
    m = n if full else n + 1
    secs = []
    for i in range(m):
        t = math.radians(a0 + (a1 - a0) * i / n)
        d = e1 * math.cos(t) + e2 * math.sin(t)
        # r6: each row follows the skin above it (max of the radii from the top down to the row), so a tier on a
        # skin sloping OUT hugs it (r4-r5 hung every row at the max of the whole run: a cone lid off the hood and the
        # mantle), and over a skin sloping IN (chin, belly) it hangs straight; the hem includes its tooth tips
        fs = (0.0, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0, 1.0 + tooth / L)
        rr = [rad(top + ax * L * f, d) for f in fs]
        rr = [r if r is not None else 0.2 for r in rr]
        r0 = rr[0]
        r1, r2, rmax = max(rr[:4]), max(rr[:6]), max(rr)   # r12: row 2 at 0.6 L (the 0.75 L row met the notches in slivers)
        tip = i % 2 == 0
        zt = L * (1.0 + (tooth if tip else -0.3 * tooth) / L)
        off = max(0.55 * flare, th + 0.012)          # r5: the inner face stays off the skin
        p_top = top + d * (r0 - sink)
        p_m1 = top + ax * (0.40 * L) + d * (r1 + off + lift)    # r8: the root face crosses the skin steeply (z-fight)
        p_m2 = top + ax * (0.60 * L) + d * (r2 + off + 0.3 * (flare - 0.55 * flare))   # r7: a third row (z-fight)
        p_hem = top + ax * zt + d * (rmax + max(flare, th + 0.015) + (0.03 if tip else 0.0))
        p_hin = p_hem - d * th - ax * 0.4 * th
        secs.append([p_top, p_m1, p_m2, p_hem, p_hin, p_m2 - d * th, p_m1 - d * th])
    bm = bmesh.new()
    V = [[bm.verts.new(q) for q in sec] for sec in secs]
    rng_ = range(m) if full else range(m - 1)
    for i in rng_:
        a_, b_ = V[i], V[(i + 1) % m]
        for j in range(7):
            bm.faces.new([a_[j], b_[j], b_[(j + 1) % 7], a_[(j + 1) % 7]])
    if not full:
        bm.faces.new(V[0]); bm.faces.new(list(reversed(V[-1])))
    recalc_normals(bm)
    return bm


def paint_slots(o, keymap, default):
    slots = [o.material_slots[p.material_index].name if o.material_slots else '' for p in o.data.polygons]
    keys = sorted(set(keymap.values()) | {default})
    paint(o, {kk: PAL[kk] for kk in keys},
          lambda c_, n_, i: next((v for kk, v in keymap.items() if kk in slots[i]), default))


def mirror_x(o):
    md = o.modifiers.new('mirror', 'MIRROR')
    md.use_axis = (True, False, False)


def box_chain(bm, rows):
    R = [[bm.verts.new(Vector(p)) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def toes(bm, tree, side):
    """Five big grey toes on the front of the flat foot (troll method), the big toe inside."""
    cx = LEG_C[-1][0]
    for o, w, L, hgt in ((-0.17, 0.052, 0.095, 0.095), (-0.085, 0.044, 0.088, 0.085), (0.0, 0.041, 0.082, 0.078),
                         (0.08, 0.038, 0.072, 0.07), (0.155, 0.034, 0.062, 0.06)):
        x = cx + o
        loc, _n = hit(tree, (x, -1.0, 0.035), (0, 1, 0))
        if loc is None:
            continue
        h = Vector((x, loc.y, 0.0))
        rows = [[h + Vector((-w, 0.035, 0.007)), h + Vector((w, 0.035, 0.007)), h + Vector((w, 0.035, hgt)), h + Vector((-w, 0.035, hgt))],
                [h + Vector((-w, -L * 0.5, 0.006)), h + Vector((w, -L * 0.5, 0.006)), h + Vector((w * 0.92, -L * 0.5, hgt * 0.85)), h + Vector((-w * 0.92, -L * 0.5, hgt * 0.85))],
                [h + Vector((-w * 0.8, -L, 0.006)), h + Vector((w * 0.8, -L, 0.006)), h + Vector((w * 0.7, -L, hgt * 0.55)), h + Vector((-w * 0.7, -L, hgt * 0.55))]]
        if side < 0:
            rows = [[Vector((-p.x, p.y, p.z)) for p in reversed(r)] for r in rows]
        box_chain(bm, rows)


def ring_chain(bm, rows):
    """Closed n-point sections bridged in order, both ends capped (a solid piece)."""
    R = [[bm.verts.new(Vector(q)) for q in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    n = len(R[0])
    for a, b in zip(R, R[1:]):
        for j in range(n):
            bm.faces.new([a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]])
    bm.faces.new(R[-1])
    recalc_normals(bm)


def nose_rows():
    """F r26b: the yeti nose - a broad, short, flat ape nose over the N1 -> E0 faces (columns 0-1): widest at the
    nostril line, narrowing up into the bridge between the eyes, its back buried. (z, half width, front y, back y);
    8-point sections: back, wing, nostril out, septum, septum, nostril out, wing, back."""
    out = []
    for z, w, f, b in ((2.088, 0.066, -0.497, -0.46), (2.115, 0.076, -0.518, -0.45), (2.178, 0.034, -0.442, -0.385)):
        dz = (0.0, 0.0, 0.003, -0.005, -0.005, 0.003, 0.0, 0.0) if z < 2.1 else (0,) * 8
        xs = (-0.8, -1.0, -0.74, -0.16, 0.16, 0.74, 1.0, 0.8)
        ys = (b, f + 0.016, f + 0.004, f, f, f + 0.004, f + 0.016, b)
        out.append([(xf * w, y_, z + d_) for xf, y_, d_ in zip(xs, ys, dz)])
    return out


# HEAD pass nose pad rows, bottom (nostril line, on the upper lip top) -> top (the bridge between the eyes):
# (z, half width, lift out of the surface)
# r4a = r3b + r3a's short broad nose bulb (lift along the surface normal, smaller nostrils)
NOSE_ROWS = ((2.096, 0.042, 0.010), (2.110, 0.058, 0.015), (2.126, 0.054, 0.014), (2.142, 0.036, 0.010))


def nose_pad(tree):
    """8-point closed sections (back, edge, four front points, edge, back) whose front points are the body surface
    (a ray from the front at that x, z) lifted out, the back points sunk 1.2 cm: a pad that follows the muzzle."""
    out = []
    for z, w, lift in NOSE_ROWS:
        sec = []
        for xf, kind in ((-0.45, 'b'), (-1.0, 'e'), (-0.6, 'f'), (-0.2, 'f'), (0.2, 'f'), (0.6, 'f'), (1.0, 'e'), (0.45, 'b')):
            x = xf * w
            loc, nr = hit(tree, (x, -1.5, z), (0, 1, 0))
            if loc is None:
                loc, nr = Vector((x, -0.5, z)), Vector((0, -1, 0))
            d_ = {'b': -0.016, 'e': max(0.4 * lift, 0.008), 'f': lift * (1.0 - 0.25 * abs(xf))}[kind]
            # r3a: the lift is measured along the surface normal (a y lift on the sloping muzzle top was half as thick:
            # z-fight), applied along y so the sections stay level
            sec.append((x, loc.y - d_ / max(abs(nr.y), 0.35), z))
        out.append(sec)
    return out


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('fur', 'skin') + (('skin2',) if BLEND else ())}, body_rule)
    from smooth_borders import smooth_borders
    smooth_borders(body, k=k, pairs=[('fur', 'skin'), ('fur', 'skin2'), ('skin', 'skin2')], pin=lambda c: c.z < 1.85)     # HEAD pass: the face border only
    tree = full_bvh(body)
    pieces = []
    one = lambda key: (lambda c_, n_, i: key)
    # eye: a small dark lens on the socket floor
    ec = eye_face_centre()
    A_, B_ = P(EYE_LO), P(EYE_HI)
    j = EYE_COL
    n = (B_[j + 1] - A_[j]).cross(B_[j] - A_[j + 1]).normalized()
    n = n if n.y < 0 else -n
    c = ec - n * 0.004
    loc, fnn = hit(tree, ec + n * 0.05, -n)
    if loc is not None:
        c, n = loc, (fnn if fnn.dot(n) > 0 else -fnn)
    n = (n + Vector((2.4, 0, 0.0))).normalized()      # s4 r8 (r9: 0.9 -> 1.8; HEAD pass 2.4): the lens looks forward-OUT (side view >= 0.40)
    bm = bmesh.new()
    lens(bm, c + n * 0.002, n, 0.024, 0.016)          # HEAD pass: 6 mm further out (side view margin)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, one('eye'))
    pieces.append(eye)
    # HEAD pass (Q6): the nose is a broad flat pad lying flush on the muzzle top (N2 -> E0), its lower band bevelled
    # forward-down with two dark nostrils (the eye colour: no new colour); the r26b wedge read as a beak in profile
    bm = bmesh.new()
    ring_chain(bm, nose_pad(tree))
    nose = object_from_bm('nose', bm, mirror=False)
    paint(nose, {'skin': PAL['skin'], 'eye': PAL['eye']},
          lambda c_, n_, i: 'eye' if (c_.z < (NOSE_ROWS[0][0] + NOSE_ROWS[1][0]) / 2 + 0.002 and (n_.y < -0.2 or n_.z < -0.2)
                                      and 0.3 * NOSE_ROWS[1][1] < abs(c_.x) < 0.7 * NOSE_ROWS[1][1]) else 'skin')
    pieces.append(nose)
    # hands: the parts-library four-finger hand, rooted in the wrist ring under the fur cuff
    wr = wrist_ring(body)
    for side in (1, -1):
        hand = hand_part(side)
        ring_pts = wr if side > 0 else [Vector((-p.x, p.y, p.z)) for p in reversed(wr)]
        k.bridge_part(hand, ring_pts, reason='parts-library 4-finger hand in the wrist ring under the fur cuff')
        paint(hand, {'skin': PAL['skin']}, one('skin'))
        pieces.append(hand)
    # toes: five per foot, pale nails on the tips
    cy = LEG_C[-1][1] - LEG_R[-1][1]
    for side in (1, -1):
        bm = bmesh.new()
        toes(bm, tree, side)
        to = object_from_bm(f'toes_{"L" if side > 0 else "R"}', bm, mirror=False)
        paint(to, {'skin': PAL['skin'], 'nail': PAL['nail']},
              lambda c_, n_, i: 'nail' if c_.y < cy - 0.05 and n_.z > 0.3 else 'skin')
        pieces.append(to)
    # ears: small round grey cups half sunk in the hood side
    # ear (s4 r12): a solid round ape-ear puck (ear_cup's thin rim failed the membrane floor at any thickness)
    loc, fnn = hit(tree, (0.6, -0.15, 2.19), (-1, 0, 0))
    ax_ = Vector((1, 0.15, 0.25)).normalized()
    u_ = Vector((0, 1, 0)); u_ = (u_ - ax_ * u_.dot(ax_)).normalized()
    w_ = ax_.cross(u_).normalized()
    bm = bmesh.new()
    rows = []
    for off, k_ in ((-0.03, 0.85), (0.012, 1.0), (0.03, 0.8)):      # review fix 1: sunk 2 cm, 15 % smaller (knobs)
        rows.append([bm.verts.new(loc + ax_ * off + (u_ * math.cos(t) * 0.036 + w_ * math.sin(t) * 0.045) * k_)
                     for t in [q * math.pi / 4 for q in range(8)]])
    for a_, b_ in zip(rows, rows[1:]):
        for j in range(8):
            bm.faces.new([a_[j], a_[(j + 1) % 8], b_[(j + 1) % 8], b_[j]])
    bm.faces.new(list(reversed(rows[0])))
    cc = bm.verts.new(loc + ax_ * 0.022)
    for j in range(8):
        bm.faces.new([rows[-1][j], rows[-1][(j + 1) % 8], cc])
    recalc_normals(bm)
    ear = object_from_bm('ear', bm, mirror=False)
    cen = loc + ax_ * 0.022
    paint(ear, {'skin': PAL['skin'], 'inner': PAL['inner']},
          lambda c_, n_, i: 'inner' if (Vector((abs(c_.x), c_.y, c_.z)) - cen).length < 0.03 else 'skin')
    mirror_x(ear)
    pieces.append(ear)
    # fur tiers
    for i, (tp, hm, rng, fl, too, nn, mir, sk, lf) in enumerate(TIERS):
        o = object_from_bm(f'fur_{i}', tier(tree, tp, hm, rng, fl, too, nn, sink=sk, lift=lf), mirror=False)
        paint(o, {'fur': PAL['fur'], 'shade': PAL['shade']},
              lambda c_, n_, i_: 'shade' if n_.z < -0.35 else 'fur')
        if mir:
            mirror_x(o)
        pieces.append(o)
    return pieces


def wrist_ring(body):
    """The wrist's open loop, in order: the arm end is the 2 x 3 root region carried down (6 faces, 2 inner
    vertices), not one n-gon (s3 r2: an n-gon search found the crotch cap and strung the hands across the groin)."""
    bm = edit(body)
    c = Vector(ARM_C[-1])
    z0 = c.z
    end = [f for f in bm.faces if all(abs(v.co.z - z0) < 0.004 and (v.co - c).length < 0.25 for v in f.verts)]
    fs = set(end)
    rim = {}
    for f in end:
        for e in f.edges:
            if sum(1 for q in e.link_faces if q in fs) == 1:
                for v in e.verts:
                    rim.setdefault(v, []).append(e.other_vert(v))
    order = [next(iter(rim))]
    while len(order) < len(rim):
        nxt = [w for w in rim[order[-1]] if w not in order]
        if not nxt:
            break
        order.append(nxt[0])
    pts = [v.co.copy() for v in order]
    bm.free()
    say(f'wrist ring: {len(end)} end faces, {len(pts)}-vertex rim')
    return pts


# ---------------------------------------------------------------- stage 4
def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['top'], 'neck', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_hand') or p.name.startswith('hand_'):
            bind(p, rig, bone='hand.L' if p.name.endswith('_L') else 'hand.R')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'head': (0, 0, 5), 'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       24: {}, 36: {'chest': (2, 0, 0), 'head': (0, 0, -5), 'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       48: {}})
    A, S = 10, 12
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 3)},
        9: {'shin.R': (-20, 0, 0), 'foot.R': (8, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0), 'spine': (0, 0, -3)},
        25: {'shin.L': (-20, 0, 0), 'foot.L': (8, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 3)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.025, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.025, 0)},
             33: {'hips': (0, 0, 0)}})
    clip(rig, 'attack', {
        1: {},
        10: {'upperarm.R': (55, 0, 0), 'forearm.R': (35, 0, 0), 'upperarm.L': (55, 0, 0), 'forearm.L': (35, 0, 0),
             'chest': (-6, 0, 0), 'head': (-4, 0, 0)},
        18: {'upperarm.R': (-25, 0, 0), 'forearm.R': (10, 0, 0), 'upperarm.L': (-25, 0, 0), 'forearm.L': (10, 0, 0),
             'chest': (10, 0, 0), 'spine': (4, 0, 0), 'head': (5, 0, 0)},
        26: {'chest': (5, 0, 0), 'spine': (2, 0, 0)},
        34: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
