import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit'))
sys.path.insert(0, KIT)
from bmkit import *
import parts as PT

# werewolf (biped wolf), t7 hand box model, zoo workflow v2. Template: zoo/minotaur/minotaur.py.
# ONE upright spine loft of 13-vertex half rings (front seam -> back seam), crotch -> crown, each ring drawn from
# 5 control points (front seam, front corner, side, back corner, back seam). The long wolf muzzle, the jaw step
# and the trapezius / neck ruff are in the loft. Arms are extruded from a 2 x 3 face region of the shoulder side
# whose TOP edge is the torso's widest ring (C2 = the deltoid line), the first arm ring = the root loop pushed out
# unshrunk (minotaur trick). Legs from a 2 x 4 region of the pelvis underside through a 45 % transition ring
# (rhino trick), digitigrade: thigh -> knee forward -> hock back -> slanted metatarsus -> paw. Ears from 2 faces of
# the skull top, the bushy tail from a 3 x 2 face region on the rump's back seam (seam walls removed). Hands
# (hand_three_finger, 4 clawed fingers) and paws (paw_canine) are parts-library pieces welded before the lock.
META = dict(creature='werewolf', model='opus', stage1_tris=(1800, 4800), total_tris=(2600, 6500),
            closeups=[('head', (0.0, -0.50, 1.86), 0.34, 'hero'),
                      ('shoulder', (0.45, -0.05, 1.40), 0.32, 'hero'),
                      ('hand', (0.70, -0.20, 0.66), 0.22, 'hero'),
                      ('paw', (0.26, -0.08, 0.12), 0.26, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, -0.02, 0.86), spine=(0.0, -0.08, 1.12), chest=(0.0, -0.14, 1.38), neck=(0.0, -0.16, 1.62),
    head=(0.0, -0.30, 1.80), top=(0.0, -0.52, 1.92),
    shoulder=(0.44, -0.01, 1.42), elbow=(0.60, 0.06, 1.05), wrist=(0.685, -0.15, 0.79), hand=(0.70, -0.22, 0.60),
    hipL=(0.20, -0.04, 0.80), knee=(0.235, -0.10, 0.48), ankle=(0.25, 0.11, 0.31), ball=(0.26, -0.06, 0.13),
    toe=(0.26, -0.30, 0.03),
    ear=(0.13, -0.33, 2.03), eartip=(0.165, -0.34, 2.20),
    tail0=(0.0, 0.22, 0.95), tail1=(0.0, 0.42, 0.60), tail2=(0.0, 0.62, 0.32), tail3=(0.0, 0.75, 0.165),
)


# ---------------------------------------------------------------- the loft
def torso5(yf, yb, W, fx=0.62, fy=0.10, sy=0.45, bx=0.72, by=0.14):
    D = yb - yf
    return [(0.0, yf), (W * fx, yf + D * fy), (W, yf + D * sy), (W * bx, yb - D * by), (0.0, yb)]


def ring13(c5, z, rnd=0.45):
    """c5 = 5 control points, optionally followed by a dict {vertex index: (x, y)} of hand-placed vertices (the
    muzzle box: the two vertices between the muzzle corner and the cheek run back along the muzzle side).
    13 points front seam -> back seam: 3 steps per control segment, a blend of the straight chord (planes) and
    a Catmull-Rom curve (round-over), the seam ends mirrored for the tangent (the mirror stays smooth)."""
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
    for j, (x, y) in over.items():
        out[j] = (x, y, z)
    return out


KEY = [   # (name, z, 5 control points (x, y)) bottom -> top, read off reference/side.png + front.png (grid)
    ('L0', 0.70, torso5(-0.14, 0.10, 0.10)),             # crotch
    ('L0b', 0.78, torso5(-0.24, 0.20, 0.30)),            # under the hips
    ('L1', 0.88, torso5(-0.28, 0.22, 0.34, bx=0.78)),    # hips / buttocks, tail root
    ('L2', 0.98, torso5(-0.32, 0.20, 0.30)),             # lower belly
    ('B0', 1.06, torso5(-0.36, 0.16, 0.275)),            # waist
    ('B1', 1.15, torso5(-0.43, 0.15, 0.29)),             # abdomen / rib bottom
    ('B2', 1.25, torso5(-0.49, 0.15, 0.33)),             # ribs
    ('C0', 1.34, torso5(-0.53, 0.16, 0.38)),             # pec bottom / lats
    ('C1', 1.42, torso5(-0.535, 0.18, 0.45)),            # pecs: the chest widens up and out ...
    ('C2', 1.50, torso5(-0.52, 0.19, 0.54, fx=0.6)),     # ... into the deltoid cap (the shoulder line, widest)
    ('C3', 1.57, torso5(-0.50, 0.17, 0.50, fx=0.58)),    # shoulder top
    ('T0', 1.62, [(0, -0.48), (0.25, -0.45), (0.44, -0.15), (0.42, 0.06), (0, 0.16)]),    # trapezius / neck ruff
    # T1 uses the head rings' control-point roles (muzzle corner, cheek column, trapezius column) so the quads
    # under the jaw are not sheared (minotaur r15)
    ('T1', 1.655, [(0, -0.46), (0.10, -0.44), (0.33, -0.27), (0.39, 0.02), (0, 0.13)]),   # throat
    ('J0', 1.685, [(0, -0.68), (0.065, -0.64), (0.30, -0.33), (0.35, 0.0), (0, 0.10), {4: (0.08, -0.53), 5: (0.20, -0.40)}]),   # jaw underside / chin
    ('M0', 1.73, [(0, -0.775), (0.07, -0.70), (0.295, -0.36), (0.30, -0.03), (0, 0.07), {4: (0.085, -0.56), 5: (0.15, -0.46)}]),  # mouth / nose bottom
    ('M1', 1.78, [(0, -0.77), (0.075, -0.69), (0.28, -0.37), (0.26, -0.05), (0, 0.04), {4: (0.09, -0.56), 5: (0.16, -0.46)}]), # nose top / cheek ruff
    ('S0', 1.83, [(0, -0.67), (0.085, -0.61), (0.27, -0.37), (0.23, -0.08), (0, 0.01), {4: (0.10, -0.54), 5: (0.17, -0.45)}]), # snout top
    ('E0', 1.875, [(0, -0.59), (0.10, -0.55), (0.255, -0.36), (0.21, -0.10), (0, -0.02)]),  # stop / eye
    # repair 4 (r32): the sheet's front head is ~10 % broader than the model's at the brow .. jaw (0.51/0.54/0.56/0.59/
    # 0.63 m at z 1.875/1.83/1.78/1.73/1.685 vs 0.47/0.49/0.50/0.53/0.59): the cheek-ruff column x +1.5-3 cm, flaring
    # most at the mouth (a fluffier, wider cheek ruff); F1-F3 (the ear windows) untouched. T1 / J0 stay (0.33 / 0.30):
    # they lie in the upper-arm probe region, and a wider J0 (0.32) or T1 (0.36) made the 3 cm T1-J0 / T0-T1 bands seam
    # strips (1.40 / 1.29 r, r32a/b)
    ('F0', 1.93, [(0, -0.575), (0.115, -0.53), (0.23, -0.35), (0.185, -0.12), (0, -0.06)]),  # brow
    ('F1', 1.99, [(0, -0.53), (0.11, -0.49), (0.19, -0.35), (0.15, -0.15), (0, -0.12)]),    # forehead
    ('F2', 2.045, [(0, -0.46), (0.09, -0.43), (0.15, -0.34), (0.12, -0.23), (0, -0.21)]),   # skull top
    ('F3', 2.06, [(0, -0.44), (0.075, -0.415), (0.12, -0.34), (0.095, -0.255), (0, -0.235)]),   # crown bevel (s1 r11; s4 r22 lower + wider: no lid rim)
]
# density: a straight in-between ring (pointwise lerp: every split face stays co-planar) where the outline bends
INSERT = ['L0b', 'L1', 'L2', 'C1', 'C2']   # s4 r21: no C3 insert (its 2.5 cm band on the shoulder top was a seam strip)   # a ring inserted ABOVE each of these keys


def stations():
    out = []
    for i, (nm, z, c5) in enumerate(KEY):
        out.append((nm, ring13(c5, z)))
        if nm in INSERT and i + 1 < len(KEY):
            a, b = ring13(c5, z), ring13(KEY[i + 1][2], KEY[i + 1][1])
            out.append((nm + '~', [tuple((Vector(p) + Vector(q)) / 2) for p, q in zip(a, b)]))
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


# arm: deltoid -> biceps -> elbow -> forearm flare -> wrist (sheet front + side, forearm forward of the elbow)
ARM_C = [(0.53, -0.03, 1.36), (0.55, 0.01, 1.25), (0.575, 0.03, 1.14), (0.60, 0.06, 1.05), (0.64, 0.0, 0.96),
         (0.67, -0.08, 0.87), (0.685, -0.15, 0.79)]
ARM_R = [(0.13, 0.17), (0.14, 0.165), (0.12, 0.14), (0.115, 0.13), (0.12, 0.14), (0.11, 0.13), (0.075, 0.085)]
# leg (digitigrade): heavy thigh, knee forward, shin back to the hock, metatarsus slanting forward to the paw
LEG_C = [(0.235, -0.08, 0.63), (0.245, -0.10, 0.55), (0.25, -0.11, 0.48), (0.25, -0.05, 0.42), (0.25, 0.04, 0.37),
         (0.25, 0.10, 0.31), (0.255, 0.03, 0.22), (0.26, -0.05, 0.145)]
LEG_R = [(0.135, 0.21), (0.118, 0.172), (0.102, 0.15),   # s1 r14: thigh tapers into the knee (no bulge band)
         (0.088, 0.13), (0.08, 0.12), (0.07, 0.095), (0.065, 0.085),
         (0.07, 0.085)]
T1_LEG = 0.60       # rhino: the leg's first ring = the region rim pulled 45 % toward the first section
EAR_C = [(0.15, -0.36, 2.095), (0.168, -0.365, 2.13), (0.172, -0.37, 2.18), (0.175, -0.372, 2.22)]   # s4 r21: lean out
EAR_R = [(0.05, 0.08), (0.045, 0.062),   # r23: ring 0 no wider than the hug ring
         (0.022, 0.03), (0.004, 0.004)]   # a broad wolf ear: a 3-face base, pyramid
# bushy tail: (y, z) centre, half-width x, half-height in the side plane (sheet side: a huge brush 0.4 m deep)
# repair 3 (r31): the sheet's rear view shows a brush 0.43 m wide (as wide as 2/3 of the hips) and 0.4 m deep: the
# half-widths 0.10-0.14 read as a thin club from the front/rear. The (0.52, 0.45) station (lost in a comment at r23) is
# back, so the dark tip can start on a ring 62 % down the tail
TAIL = [((0.27, 0.86), 0.11, 0.115), ((0.36, 0.75), 0.16, 0.16),   # r23: a tall root over the rump
        ((0.44, 0.60), 0.20, 0.20), ((0.52, 0.45), 0.215, 0.205),
        ((0.62, 0.32), 0.19, 0.18), ((0.70, 0.22), 0.12, 0.115), ((0.75, 0.165), 0.04, 0.04)]
TAIL_DARK_RING = 3      # repair 2: the dark tip starts ON this tail ring (a ring border, not a z cut across tilted rings)


def _tail_s(i):
    pts = [(0.22, 0.95)] + [c for c, _a, _b in TAIL]
    return sum(math.dist(a, b) for a, b in zip(pts[:i + 1], pts[1:i + 2]))


TAIL_DARK = _tail_s(TAIL_DARK_RING) + 1e-4


def corner(fr, ab):
    c, e1, e2, r1, r2 = fr
    return c + e1 * ab[0] * r1 + e2 * ab[1] * r2


def region_roles(faces, lo_ring, up_ring):
    """Roles (a, b) for a face region's vertices: the boundary loop spread evenly round the unit circle in the
    region's own frame (e1 lower ring -> upper ring = the limb's outer side, e2 = +y), interior vertices inside."""
    vs = sorted({v for f in faces for v in f.verts}, key=lambda v: tuple(v.co))   # r29: set order is memory-layout
    # dependent (a file edit re-ordered it and moved the lock's vertices at 1e-5): sort by position
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
    order = sorted(bnd, key=lambda v: ang[v])
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


def hand_part():
    w = Vector(J['wrist'])
    fwd = (Vector(J['hand']) - w).normalized()
    up = Vector((1, 0, 0.0)); up = (up - fwd * up.dot(fwd)).normalized()
    return PT.hand_three_finger(origin=w + fwd * 0.03, width=0.23, forward=fwd, up=up, side=1, fingers=4, curl=0.35,
                                spread=10.0, finger_len=1.0, thumb=True, thumb_curl=0.3, knuckle=0.14,
                                claw_len=0.45, wrist=(0.16, 0.13), open_root=True, name='hand')


def paw_part():
    return PT.paw_canine(origin=Vector(J['ball']) + Vector((0, 0, -0.005)), width=0.31, height=0.125,
                         toes=4, toe_segs=2, claws=True, claw_len=0.75, pads=True, splay=12.0,
                         root=(0.14, 0.16), open_root=True, name='paw')


def tail_region(rings, spans, i0, nsp=3, cols=(10, 11)):
    """The rump's back-seam region: faces, and roles (ax >= 0 across, bh -1 bottom .. +1 top) for its vertices:
    the open boundary path (bottom seam -> outer side -> top seam) spread evenly over a half circle."""
    faces = [spans[i0 + s][c] for s in range(nsp) for c in cols]
    c0, c1 = cols[0], cols[-1] + 1        # vertex columns c0 .. c1 (c1 = 12 = the back seam)
    path = [rings[i0][j] for j in range(c1, c0 - 1, -1)]
    path += [rings[i0 + s][c0] for s in range(1, nsp)]
    path += [rings[i0 + nsp][j] for j in range(c0, c1 + 1)]
    n = len(path) - 1
    roles = {}
    for kk, v in enumerate(path):
        t = math.pi * (-0.5 + kk / n)
        roles[v] = (math.cos(t) if 0 < kk < n else 0.0, math.sin(t))
    for s in range(1, nsp):
        b = -1 + 2 * s / nsp
        for j in range(c0 + 1, c1 + 1):
            v = rings[i0 + s][j]
            if v not in roles:
                roles[v] = (0.0 if j == c1 else 0.55 * (c1 - j) / (c1 - c0), b * 0.8)
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, _p) in enumerate(SECS)}
    rings = [ring(bm, pts) for _n, pts in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    rest = []

    def region(lo, nsp, cols):
        i = idx[lo]
        faces = [spans[i + s][c] for s in range(nsp) for c in cols]
        return faces, rings[i], rings[i + nsp]

    # tail first (its region indices refer to the untouched loft): 3 x 2 faces of the rump's back seam
    i = idx['L0b']   # r23: 4 x 2 faces L0b -> L2 (z 0.78-0.98): the tail root is as tall as the sheet's
    faces, roles = tail_region(rings, spans, i, 4, (10, 11))
    prev = sum((v.co for v in faces[0].verts), Vector()) * 0.0
    prev = Vector((0.0, (rings[i][12].co.y + rings[i + 4][12].co.y) / 2, (rings[i][12].co.z + rings[i + 4][12].co.z) / 2))
    upv0 = Vector((0, 0, 1))
    for (cy, cz), rx, rh in TAIL:
        c = Vector((0.0, cy, cz))
        d = (c - prev).normalized()
        upv = Vector((0.0, -d.z, d.y))
        if upv.dot(upv0) < 0:
            upv = -upv
        upv0 = upv
        keyed = [(o.co.copy(), ab) for o, ab in roles.items()]   # by position: extrude removes interior verts
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(keyed, key=lambda q: (q[0] - v.co).length)[1]
        for v, (ax, bh) in new.items():
            v.co = c + Vector((ax * rx, 0, 0)) + upv * bh * rh
        walls = [g for g in r['sides'] if all(abs(w.co.x) < 1e-6 for w in g.verts)]
        bmesh.ops.delete(bm, geom=walls, context='FACES')
        faces, roles, prev = r['faces'], new, c
    # arms: 2 x 3 faces of the shoulder side right under the shoulder line (C1 -> C1~ -> C2): the region's top edge
    # is the torso's widest ring, the first arm ring is the root loop pushed out unshrunk (minotaur r08)
    faces, lo, up = region('C1', 2, (6, 7, 8))   # s1 r09: cols 6-8 (y -0.21..0.09) centred on the arm
    roles, info = region_roles(faces, lo, up)
    fr = [hug_frame(info, 0.025, 1.0)] + frame_chain(ARM_C, ARM_R)
    faces, roles = grow(bm, faces, roles, fr)
    rr = bridge_part(hand_part(), one_face(bm, faces), bm=bm)
    if rr is not None:
        rest.append(rr)
    # legs: 3 x 4 faces of the pelvis underside AND flank (L0 -> L0b -> L0b~ -> L1): the region's top edge is the
    # widest hip ring, so the thigh rises out of the flank with no pelvis shelf over it (s1 r08); a 45 % transition
    # ring (rhino), then level rings
    faces, lo, up = region('L0', 3, (3, 4, 5, 6, 7, 8))   # s4 r21: 6 wide = the thigh's depth
    roles, info = region_roles(faces, lo, up)
    lf = level(LEG_C, LEG_R)
    fr = [dict(kind='lerp', to=lf[0], t=T1_LEG)] + lf
    faces, roles = grow(bm, faces, roles, fr)
    rr = bridge_part(paw_part(), one_face(bm, faces), bm=bm)
    if rr is not None:
        rest.append(rr)
    # ears: 3 faces of the skull top (F1 -> F2, columns 4-6: a wolf ear's base is 0.18 m long on the sheet)
    faces, lo, up = region('F1', 2, (4, 5, 6))   # fix 2: F1 -> F3 (side + crown bevel)
    roles, info = region_roles(faces, lo, up)
    # lateral -x: the region's e1 runs F1 -> F2 (inward-up), so the outer (lower) row maps to the ear's +x side
    ef = frame_chain([info[0]] + EAR_C, [(0.06, 0.08)] + EAR_R, lateral=(-1, 0, 0))[1:]
    # s4 r20 (minotaur r29): the first ear ring is the root region itself pushed 2 cm out and shrunk to 0.85 (walls
    # lean in: no knife fold at the front/back corners of the root), the pyramid from the second ring on
    grow(bm, faces, roles, [hug_frame(info, 0.02, 0.85)] + ef)
    snap_seam(bm)
    recalc_normals(bm)
    k.meta['_rest'] = [o.name for o in rest]
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
def eye_face_centre():
    A, B_ = P('E0'), P('F0')
    return (A[3] + A[4] + B_[3] + B_[4]) / 4


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.045 and abs(c.y - ec0.y) < 0.05 and abs(c.z - ec0.z) < 0.045


def limb_edge(bm, frames, i):
    """The edge running along a limb from ring i to ring i+1 on its outer side (a loop cut across it rings the limb)."""
    va = vert_near(bm, corner(frames[i], (1, 0)))
    tb = corner(frames[i + 1], (1, 0))
    return min(va.link_edges, key=lambda e: (e.other_vert(va).co - tb).length)


def soften(bm, roots, soft=50.0, hot=72.0, cap=0.03, lam=2.0e6, iters=120):
    """Split hard concave folds near junction roots into two soft ones, by vertex moves only (stage 2).
    roots: (root, tip, r) like the junction probe (region = face centres within 2r of the root, at most 0.6 of the
    first bone down). The full mirrored surface is rebuilt in numpy; the cost is sum over region edges of
    length x (concave deg - soft)^2 + convex excess over 80 deg + lam |move|^2; the variables are the vertices of the
    faces on a concave fold over `hot` deg (and their one-ring), seam vertices keep x = 0, moves capped at `cap`."""
    import numpy as np
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    V0 = np.array([v.co[:] for v in bm.verts])
    n = len(V0)
    seam = np.abs(V0[:, 0]) < 1e-5
    mi = np.full(n, -1)
    nm = 0
    for i in range(n):
        if not seam[i]:
            mi[i] = n + nm; nm += 1
    full_idx = lambda i, side: i if side > 0 or seam[i] else mi[i]
    faces = []
    for f in bm.faces:
        ids = [v.index for v in f.verts]
        faces.append(ids)
        faces.append([full_idx(i, -1) for i in reversed(ids)])
    def full(V):
        return np.vstack([V, V[~seam] * np.array([-1.0, 1.0, 1.0])])
    F = full(V0)
    cen = np.array([F[f].mean(0) for f in faces])
    keep = np.zeros(len(faces), bool)
    for root, tip, r in roots:
        root, tip = np.array(root), np.array(tip)
        ax = (tip - root) / np.linalg.norm(tip - root)
        d = cen - root
        keep |= (np.linalg.norm(d, axis=1) < 2 * r) & (d @ ax < 0.6 * np.linalg.norm(tip - root))
        if abs(root[0]) > 1e-6:      # the mirrored root too
            rm = root * np.array([-1, 1, 1]); tm = tip * np.array([-1, 1, 1])
            axm = (tm - rm) / np.linalg.norm(tm - rm); dm = cen - rm
            keep |= (np.linalg.norm(dm, axis=1) < 2 * r) & (dm @ axm < 0.6 * np.linalg.norm(tm - rm))
    E = {}
    for fi, f in enumerate(faces):
        for si, (a, b) in enumerate(zip(f, f[1:] + f[:1])):
            E.setdefault((min(a, b), max(a, b)), []).append((fi, si))
    edges = [(e, fs) for e, fs in E.items() if len(fs) == 2 and (keep[fs[0][0]] or keep[fs[1][0]])]
    L = max(len(f) for f in faces)
    pad = np.array([f + [f[0]] * (L - len(f)) for f in faces])
    cnt = np.array([len(f) for f in faces])
    nxt = np.array([f[1:] + f[:1] + [f[0]] * (L - len(f)) for f in faces])
    EA = np.array([e[0] for e, _ in edges]); EB = np.array([e[1] for e, _ in edges])
    F1 = np.array([fs[0][0] for _, fs in edges]); F2 = np.array([fs[1][0] for _, fs in edges])
    S1 = np.array([fs[0][1] for _, fs in edges]); S2 = np.array([fs[1][1] for _, fs in edges])
    used = np.unique(np.concatenate([F1, F2]))
    uq = np.array([fi for fi in used if cnt[fi] == 4]); un = np.array([fi for fi in used if cnt[fi] != 4])
    QV = pad[uq][:, :4]
    unit = lambda x: x / np.maximum(np.linalg.norm(x, axis=-1), 1e-12)[..., None]
    def geom(Vf):
        """Per face and edge slot: the normal of the export triangle on that edge. A quad is split on the diagonal
        that folds OUT (techqa's export rule); other polygons use their Newell normal."""
        NS = np.zeros((len(faces), L, 3)); C = np.zeros((len(faces), 3))
        P, Q = Vf[pad[un]], Vf[nxt[un]]
        nn = np.stack([((P[..., 1] - Q[..., 1]) * (P[..., 2] + Q[..., 2])).sum(1),
                       ((P[..., 2] - Q[..., 2]) * (P[..., 0] + Q[..., 0])).sum(1),
                       ((P[..., 0] - Q[..., 0]) * (P[..., 1] + Q[..., 1])).sum(1)], 1)
        NS[un] = unit(nn)[:, None, :]
        msk = (np.arange(L)[None, :] < cnt[un][:, None])[..., None]
        C[un] = (P * msk).sum(1) / cnt[un][:, None]
        a, b, c, d = (Vf[QV[:, i]] for i in range(4))
        abc, acd = unit(np.cross(b - a, c - a)), unit(np.cross(c - a, d - a))
        abd, bcd = unit(np.cross(b - a, d - a)), unit(np.cross(c - b, d - b))
        s1 = (((d - a) * abc).sum(1) <= 0)[:, None]
        NS[uq, 0] = np.where(s1, abc, abd); NS[uq, 1] = np.where(s1, abc, bcd)
        NS[uq, 2] = np.where(s1, acd, bcd); NS[uq, 3] = np.where(s1, acd, abd)
        C[uq] = (a + b + c + d) / 4
        return NS, C
    def angles(Vf):
        NS, C = geom(Vf)
        n1, n2 = NS[F1, S1], NS[F2, S2]
        ang = np.degrees(np.arccos(np.clip((n1 * n2).sum(1), -1, 1)))
        mid = (Vf[EA] + Vf[EB]) / 2
        conc = ((C[F2] - mid) * n1).sum(1) > 1e-7
        ln = np.linalg.norm(Vf[EA] - Vf[EB], axis=1)
        return ang, conc, ln
    ang, conc, ln = angles(F)
    hotf = set(F1[conc & (ang > hot)]) | set(F2[conc & (ang > hot)])
    var = set()
    for fi in hotf:
        for i in faces[fi]:
            var.add(i if i < n else int(np.where(mi == i)[0][0]))
    ring1 = set()
    for f in bm.faces:
        ids = {v.index for v in f.verts}
        if ids & var:
            ring1 |= ids
    var = sorted(ring1)
    if not var:
        return
    def tri_w(Vf):
        """Widths (2 area / longest edge) of the two export triangles of every region quad (fold-out split)."""
        a, b, c, d = (Vf[QV[:, i]] for i in range(4))
        def w(p, q, r):
            ar = np.linalg.norm(np.cross(q - p, r - p), axis=1)
            lg = np.maximum(np.maximum(np.linalg.norm(q - p, axis=1), np.linalg.norm(r - q, axis=1)), np.linalg.norm(p - r, axis=1))
            return ar / np.maximum(lg, 1e-12)
        s1 = ((d - a) * np.cross(b - a, c - a)).sum(1) <= 0
        return np.concatenate([np.where(s1, w(a, b, c), w(a, b, d)), np.where(s1, w(a, c, d), w(b, c, d))])
    medw = float(np.median(tri_w(F)))
    def cost(D):
        V = V0.copy(); V[var] += D
        Vf = full(V)
        a, c, l = angles(Vf)
        # r31: + no thin triangles (the probe's seam strip: width < 0.4 x the median face) where the moves act
        thin = np.maximum(0.5 * medw - tri_w(Vf), 0)
        return float((l * np.where(c, np.maximum(a - soft, 0), np.maximum(a - 80.0, 0)) ** 2).sum() * 50
                     + lam * (D ** 2).sum() + 2.0e7 * (thin ** 2).sum())
    D = np.zeros((len(var), 3))
    mask = np.ones_like(D); mask[seam[var], 0] = 0
    lr, c0, h = 2e-7, cost(D), 1e-5
    a0 = angles(F)
    for it in range(iters):
        G = np.zeros_like(D)
        for i in range(len(var)):
            for k_ in range(3):
                if not mask[i, k_]:
                    continue
                D[i, k_] += h; cp = cost(D); D[i, k_] -= 2 * h; cm = cost(D); D[i, k_] += h
                G[i, k_] = (cp - cm) / (2 * h)
        while lr > 1e-12:
            Dn = np.clip(D - lr * G * mask, -cap, cap)
            cn = cost(Dn)
            if cn < c0:
                D, c0, lr = Dn, cn, lr * 1.5
                break
            lr *= 0.5
        else:
            break
    for i, vi in enumerate(var):
        bm.verts[vi].co += Vector(D[i])
    V = V0.copy(); V[var] += D
    a1 = angles(full(V))
    pr = lambda A: round(float(A[0][A[1]].max()), 1)
    print(f'BMK soften: {len(var)} verts, max move {1000 * np.abs(D).max():.1f} mm, region max concave {pr(a0)} -> {pr(a1)} deg, '
          f'concave>90 len {float(a0[2][a0[1] & (a0[0] > 90)].sum()):.3f} -> {float(a1[2][a1[1] & (a1[0] > 90)].sum()):.3f} m')


def stage2(k, body):
    """Joint loops (elbow, upper arm, knee, hock, hip, waist), the eye socket, a brow over it, broader ears."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table()
    af = frame_chain(ARM_C, ARM_R)
    lf = level(LEG_C, LEG_R)
    sp = lambda nm, j=0: P(nm)[j]
    cuts = [('elbow loop: the elbow bend', lambda: limb_edge(bm, af, 3)),
            ('upper-arm loop: the shoulder swing under the deltoid', lambda: limb_edge(bm, af, 0)),
            ('knee loop: the knee bend', lambda: limb_edge(bm, lf, 2)),
            ('hock loop: the digitigrade hock bend', lambda: limb_edge(bm, lf, 5)),
            ('hip loop: the thigh swing', lambda: limb_edge(bm, lf, 0)),
            ('waist loop: the spine bend', lambda: edge_near(bm, tuple((sp('B0') + sp('B1')) / 2)))]
    for why, fe in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, fe(), t=0.5)
    # eye socket: an inset in the eye face (E0 -> F0, columns 3-4), its floor 4 mm in (minotaur fix 1: a shallow step)
    ec0 = eye_face_centre()
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face, its floor pushed in'):
        inner = inset(bm, [f], 0.30, 0.0)
    move(list(inner[0].verts), -fn * 0.004)
    F0 = P('F0')
    move([vert_near(bm, F0[j]) for j in (3, 4)], (0.004, -0.012, 0.0))      # brow ridge over the eye
    # broader wolf ears: every ear vertex above the crown scaled 1.2 across / 1.15 deep about the ear axis
    ax = Vector(EAR_C[0])
    for v in bm.verts:
        q = v.co
        if q.z > 2.10 and q.x > 0.09 and (Vector((q.x, q.y)) - Vector((ax.x, ax.y))).length < 0.12:
            v.co.x = ax.x + (q.x - ax.x) * 1.2
            v.co.y = ax.y + (q.y - ax.y) * 1.15
    # owner fix 3: the groin. The crotch cap (L0, flat at z 0.70) met the thighs' inner walls at 97 deg and the tail
    # root's lower wall met the crotch back at 106 deg.
    L0 = P('L0')
    # fix 3b (r26): r25's V (down) and tail-back moves made the folds WORSE (158 / 137 deg in the fold dump): the
    # signs are inverted - the crotch cap domes UP toward the seam (the inner wall turns inward-up into it) and the
    # tail's lower root wall moves 1.5 cm FORWARD over the crotch back
    for j, dz in ((0, 0.03), (1, 0.025), (2, 0.018), (10, 0.018), (11, 0.025), (12, 0.03)):
        move([vert_near(bm, L0[j])], (0, 0, dz))
    tb = [v for v in bm.verts if v.co.x < 0.11 and 0.215 < v.co.y < 0.28 and 0.73 < v.co.z < 0.80]
    move(tb, (0, -0.03, 0))           # fix 3c: 3 cm (1.5 cm took the fold 106 -> 101 deg)
    # fix 3c: the thigh's inner transition verts 1.5 cm out, so the inner wall leans out under the crotch cap edge
    ti = [v for v in bm.verts if 0.07 < v.co.x < 0.14 and -0.2 < v.co.y < 0.08 and 0.62 < v.co.z < 0.69]
    move(ti, (0.015, 0, 0))
    recalc_normals(bm)
    # repair 1 (r29): the groin crease (belly underside vs thigh front, 94 deg) and the pocket under the tail root
    # (crotch back vs tail underside, 99 deg) each turn in ONE knife edge, because the 60 % lerp transition ring sits on
    # the straight line rim -> thigh ring 0. Two soft folds: the vertices one ring off each crease (the transition ring,
    # the tail's first ring underside, the crotch-cap row) slide so the turn splits over the rim and the next ring.
    soften(bm, [((0.2, -0.04, 0.8), (0.235, -0.10, 0.48), 0.183), ((0.0, 0.22, 0.95), (0.0, 0.42, 0.60), 0.098)])
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'fur': '#a0a0a3', 'back': '#727377', 'cream': '#efe5d1', 'tan': '#cfa572', 'dark': '#2c2b2e',
       'eye': '#2a1a10'}


COLS = {}     # face index -> (column from the front seam, column from the back seam), stage 3


def face_columns(body):
    """Walk every loft ring from the seam: a face on a seam edge is column 0, the face across its opposite edge
    column 1, ... (quads only, at most 6 steps). Colour borders then run along loft COLUMN lines (edge loops that
    flow from crotch to throat) and along level rings, never across faces (repair 2: no stair steps)."""
    bm = bmesh.new(); bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    front, back = {}, {}
    for e in bm.edges:
        if not all(abs(v.co.x) < 1e-5 for v in e.verts) or len(e.link_faces) != 1:
            continue
        f = e.link_faces[0]
        if len(f.verts) != 4:
            continue
        side = front if f.normal.y < 0 else back
        cur, ent = f, e
        for col in range(7):
            if cur.index in side:
                break
            side[cur.index] = col
            vs = set(ent.verts)
            opp = [g for g in cur.edges if not (set(g.verts) & vs)]
            if len(opp) != 1:
                break
            nf = [q for q in opp[0].link_faces if q is not cur]
            if not nf or len(nf[0].verts) != 4:
                break
            cur, ent = nf[0], opp[0]
    bm.free()
    COLS.clear()
    for i in set(front) | set(back):
        COLS[i] = (front.get(i, 99), back.get(i, 99))


def chain_s(p, pts):
    """Arc length of p projected on the polyline pts (and the polyline's total length)."""
    best, acc, out = 1e9, 0.0, 0.0
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b)
        d = b - a
        t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared))
        q = (a + d * t - p).length
        if q < best:
            best, out = q, acc + t * d.length
        acc += d.length
    return out, acc, best


ARM_S = None


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    cf, cb = COLS.get(i, (99, 99))
    if z > 2.07 and x > 0.09 and n.y < -0.45:
        return 'cream'                                                   # inner ear
    if y < -0.74 and 1.72 < z < 1.80 and n.y < -0.3:
        return 'dark'                                                    # nose leather (muzzle tip)
    if x > 0.45 and z < 1.40:                                            # arm: bands on the arm's own rings
        s, tot, d = chain_s(Vector((x, y, z)), ARM_C + [J['hand'], (0.71, -0.27, 0.42)])   # r31: + the hand
        if d < 0.25:
            return 'cream' if s >= ARM_S[6] - 1e-4 else ('tan' if s >= ARM_S[4] - 1e-4 else 'fur')
    if y > 0.21 and z < 0.95 and x < 0.25:                               # tail (r32: before the legs - the wider
        s, tot, d = chain_s(Vector((0.0, y, z)), [(0.0, 0.22, 0.95)] + [(0.0, cy, cz) for (cy, cz), _a, _b in TAIL])
        if d < 0.24:                                                     # brush entered the leg box), dark tip from
            return 'back' if s > TAIL_DARK else 'fur'                    # its TAIL_DARK_RING on
    if x > 0.12 and z < 0.66 and y < 0.45:                               # legs (level rings)
        return 'cream' if z < 0.40 else ('tan' if z < 0.50 else 'fur')
    if z < 0.75 and x < 0.11 and n.z < -0.5:
        return 'cream'                                                   # crotch cap
    if 0.69 < z < 1.665 and cf <= 2:
        return 'cream'                                                   # chest + belly bib: up to the v3 column
    if 1.665 < z < 1.80 and cf <= 5:
        return 'cream'                                                   # jaw, lower muzzle and the cheek front (sheet)
    if 1.105 < z < 1.665 and cb <= 2:
        return 'back'                                                    # saddle: the back-corner (v9) column line,
    if 0.975 < z < 1.105 and cb <= 1:                                    # wide over the trapezius, narrowing with
        return 'back'                                                    # the waist, a spine stripe into the tail
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


def stage3(k, body):
    global ARM_S
    face_columns(body)
    ARM_S = [chain_s(Vector(q), ARM_C)[0] for q in ARM_C]
    paint(body, {kk: PAL[kk] for kk in ('fur', 'back', 'cream', 'tan', 'dark')}, body_rule)
    tree = full_bvh(body)
    pieces = []
    one = lambda key: (lambda c_, n_, i: key)
    # eye: a dark lens on the socket floor (minotaur r36/r39: centre and normal from a ray hit on the floor)
    ec = eye_face_centre()
    A_, B_ = P('E0'), P('F0')
    n = (B_[3] - A_[4]).cross(B_[4] - A_[3]).normalized()
    n = n if n.y < 0 else -n
    c = ec - n * 0.004
    loc, fnn = hit(tree, ec + n * 0.05, -n)
    if loc is not None:
        c, n = loc, (fnn if fnn.dot(n) > 0 else -fnn)
    bm = bmesh.new()
    lens(bm, c - n * 0.006, n, 0.021, 0.018)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, one('eye'))
    pieces.append(eye)
    # the welded parts' loose shells (hand claws, paw toe beans and claws): mirrored, painted by their part slot
    for nm in k.meta.get('_rest', []):
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        slots = [o.material_slots[p.material_index].name if o.material_slots else 'skin' for p in o.data.polygons]
        key = lambda c_, n_, i, slots=slots: ('dark' if ('claw' in slots[i] or 'pad' in slots[i]) else 'cream')
        paint(o, {'cream': PAL['cream'], 'dark': PAL['dark']}, key)
        if 'hand' in nm:
            # s3 r17: the hand claws' top faces lay 1-3 mm over the finger tops, facing the same way (z-fight 8):
            # each claw shell moves 8 mm out along the finger (wrist -> claw)
            bmo = bmesh.new(); bmo.from_mesh(o.data)
            seen = set()
            for v0 in bmo.verts:
                if v0 in seen:
                    continue
                shell, stack = set(), [v0]
                while stack:
                    v = stack.pop()
                    if v not in shell:
                        shell.add(v); stack.extend(e.other_vert(v) for e in v.link_edges)
                seen |= shell
                cen = sum((o.matrix_world @ v.co for v in shell), Vector()) / len(shell)
                d = (cen - Vector(J['wrist'])).normalized()        # r18: out along the finger (the claw centroid
                for v in shell:                                     # is inside the fingertip: a nearest-point
                    v.co += o.matrix_world.inverted().to_3x3() @ (d * 0.008)   # push pointed inward)
            bmo.to_mesh(o.data); bmo.free(); o.data.update()
        md = o.modifiers.new('mirror', 'MIRROR')
        md.use_axis = (True, False, False)
        pieces.append(o)
    return pieces


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
         ('foot.L', J['ankle'], J['ball'], 'shin.L', True),
         ('toe.L', J['ball'], J['toe'], 'foot.L', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing through the chest, a head turn, the ears flick, the big tail swishes
    clip(rig, 'idle', {1: {},
                       12: {'chest': (2, 0, 0), 'head': (0, 0, 6), 'ear.L': (0, 0, 8), 'tail1': (0, 0, 8),
                            'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       24: {'tail1': (0, 0, -3)},
                       36: {'chest': (2, 0, 0), 'head': (0, 0, -6), 'ear.R': (0, 0, -8), 'tail1': (0, 0, -8),
                            'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       48: {}})
    # move: a loping stride; the swinging leg folds at the knee and hock, the arms swing against the legs
    A, S = 12, 14
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
            'spine': (0, 0, 3), 'tail1': (0, 0, 5)},
        9: {'shin.R': (-24, 0, 0), 'foot.R': (14, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0),
             'spine': (0, 0, -3), 'tail1': (0, 0, -5)},
        25: {'shin.L': (-24, 0, 0), 'foot.L': (14, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
             'spine': (0, 0, 3), 'tail1': (0, 0, 5)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.03, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.03, 0)},
             33: {'hips': (0, 0, 0)}})
    # attack: a claw swipe - wind the right arm up and back, then rake it down and across, the head lunging in
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (-5, 0, 6), 'neck': (-6, 0, 0), 'upperarm.R': (40, 0, -25), 'forearm.R': (30, 0, 0),
             'tail1': (0, 0, 8)},
        18: {'spine': (5, 0, -6), 'chest': (8, 0, -8), 'neck': (6, 0, 0), 'head': (8, 0, 0),
             'upperarm.R': (-30, 0, -10), 'forearm.R': (10, 0, 0), 'tail1': (0, 0, -8)},
        26: {'spine': (3, 0, -3), 'chest': (4, 0, -4)},
        36: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
