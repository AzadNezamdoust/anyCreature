import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit'))
sys.path.insert(0, KIT)
from bmkit import *
import parts as PT

# lizardman (upright reptile biped with a long thick ground tail), t7 hand box model, zoo workflow v2.
# Templates: zoo/minotaur (shoulder: deltoid = the torso's widest ring, arm from a 2 x 3 region with its top edge on
# it, unshrunk hug ring), zoo/werewolf (leg region up the flank to the widest hip ring, tail region on the rump).
# ONE upright spine loft of 13-vertex half rings (front seam -> back seam), crotch -> skull top, each ring drawn from
# 5 control points (front seam, front corner, side, back corner, back seam). The long lizard snout, the jaw step and
# the trapezius slope are horizontal slices of the loft.
# Groin / tail-root plan (werewolf failed here): the thigh region is the flank columns 2-7 from the crotch ring L0 up
# to the widest hip ring L1; the tail region is the back-seam columns 10-11 from the SAME crotch ring L0 up to L3, so
# the tail's lower wall leaves the crotch cap's back edge directly (no crotch-back band folding against it); columns
# 8-9 stay body faces: a clean two-face gap between thigh and tail.
META = dict(creature='lizardman', model='opus', stage1_tris=(1800, 5200), total_tris=(2600, 7000),
            closeups=[('head', (0.0, -0.85, 1.86), 0.32, 'hero'),
                      ('shoulder', (0.33, -0.68, 1.42), 0.30, 'hero'),
                      ('hip', (0.20, -0.55, 0.70), 0.32, 'back34'),
                      ('foot', (0.28, -0.70, 0.10), 0.26, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, -0.66, 0.84), spine=(0.0, -0.69, 1.12), chest=(0.0, -0.69, 1.38), neck=(0.0, -0.66, 1.62),
    head=(0.0, -0.68, 1.80), top=(0.0, -1.04, 1.86),
    shoulder=(0.30, -0.665, 1.44), elbow=(0.48, -0.635, 1.03), wrist=(0.55, -0.775, 0.81), hand=(0.575, -0.85, 0.68),
    hipL=(0.19, -0.69, 0.76), knee=(0.24, -0.67, 0.49), ankle=(0.27, -0.585, 0.18), toe=(0.31, -0.95, 0.03),
    tail0=(0.0, -0.50, 0.78), tail1=(0.0, -0.40, 0.66), tail2=(0.0, -0.13, 0.36), tail3=(0.0, 0.25, 0.15),
    tail4=(0.0, 0.72, 0.065), tail5=(0.0, 1.08, 0.035),
)


# ---------------------------------------------------------------- the loft
def torso5(yf, yb, W, fx=0.62, fy=0.10, sy=0.45, bx=0.72, by=0.14):
    D = yb - yf
    return [(0.0, yf), (W * fx, yf + D * fy), (W, yf + D * sy), (W * bx, yb - D * by), (0.0, yb)]


def ring13(c5, z, rnd=0.45):
    """13 points front seam -> back seam: 3 steps per control segment, a blend of the straight chord (planes) and
    a Catmull-Rom curve (round-over), the seam ends mirrored for the tangent (the mirror stays smooth)."""
    P = [Vector((x, y)) for x, y in c5]
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
    return out


KEY = [   # (name, z, 5 control points (x, y)) bottom -> top, read off reference/side.png + front.png (scratch meas.py)
    ('L0', 0.58, torso5(-0.80, -0.50, 0.17)),            # crotch (cap): thighs and tail root leave its edge
    ('L0b', 0.67, torso5(-0.83, -0.49, 0.26)),           # under the hips
    ('L1', 0.76, torso5(-0.845, -0.48, 0.31)),           # widest hip ring: the thigh region's top edge
    ('L2', 0.87, torso5(-0.85, -0.475, 0.29)),           # hips over the thigh
    ('L3', 0.97, torso5(-0.86, -0.47, 0.25)),            # belt bottom: the tail root's top edge
    ('B0', 1.07, torso5(-0.875, -0.485, 0.22)),          # belt
    ('B1', 1.17, torso5(-0.88, -0.53, 0.19)),            # waist
    ('B2', 1.26, torso5(-0.89, -0.535, 0.21)),           # ribs
    ('C0', 1.34, torso5(-0.905, -0.505, 0.24)),          # pec bottom / lats (s1 r05: 0.24, the armpit clears)
    ('C1', 1.41, torso5(-0.91, -0.48, 0.31)),            # pecs: the chest widens up and out ...
    ('C2', 1.48, torso5(-0.88, -0.466, 0.355, fx=0.6)),  # ... into the deltoid line (the widest ring)
    ('C3', 1.555, torso5(-0.84, -0.47, 0.32, fx=0.58)),  # shoulder top
    # T0 / T1 / N0 use the head rings' roles (front corner near the seam, side = jaw column) so the quads under the
    # jaw are not sheared (minotaur r15)
    ('T0', 1.60, [(0, -0.815), (0.15, -0.80), (0.235, -0.67), (0.20, -0.545), (0, -0.50)]),   # trapezius
    ('T1', 1.65, [(0, -0.815), (0.10, -0.80), (0.18, -0.685), (0.16, -0.57), (0, -0.525)]),   # trapezius / neck
    ('N0', 1.70, [(0, -0.833), (0.07, -0.82), (0.13, -0.70), (0.12, -0.59), (0, -0.556)]),    # neck / throat
    # s1 r03: the snout's front corner sits ~10 cm back from the tip (a rounded nose over 3 columns, not a duck bill
    # of tiny tip faces and one long flat side), and a crown ring F2 domes the skull (no flat lid)
    ('J0', 1.745, [(0, -0.96), (0.07, -0.89), (0.122, -0.71), (0.11, -0.60), (0, -0.566)]),     # jaw line / chin
    ('M0', 1.80, [(0, -1.10), (0.085, -1.00), (0.128, -0.73), (0.115, -0.615), (0, -0.577)]),   # mouth line
    ('M1', 1.85, [(0, -1.107), (0.09, -1.005), (0.14, -0.73), (0.12, -0.625), (0, -0.585)]),   # snout / cheeks
    ('E0', 1.90, [(0, -1.04), (0.085, -0.95), (0.128, -0.74), (0.115, -0.64), (0, -0.603)]),   # eye bottom
    ('F0', 1.945, [(0, -0.95), (0.075, -0.88), (0.118, -0.76), (0.10, -0.665), (0, -0.637)]),  # brow
    ('F1', 1.98, [(0, -0.84), (0.06, -0.80), (0.092, -0.74), (0.075, -0.685), (0, -0.665)]),   # skull
    ('F2', 2.00, [(0, -0.78), (0.03, -0.77), (0.05, -0.735), (0.04, -0.70), (0, -0.69)]),      # crown
]
# density: a straight in-between ring (pointwise lerp: every split face stays co-planar) where the outline bends
INSERT = ['L0b', 'L2', 'C1', 'C2']   # a ring inserted ABOVE each of these keys


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


# arm (A-pose, sheet front): deltoid -> biceps -> elbow (back, z 1.03) -> forearm forward -> wrist
# s1 r04: the upper arm hangs closer (sheet front: outer edge 0.40 at z 1.35, 0.44 at 1.25) and is 0.18-0.2 deep
ARM_C = [(0.355, -0.67, 1.36), (0.375, -0.665, 1.26), (0.41, -0.655, 1.17), (0.462, -0.64, 1.07),
         (0.50, -0.66, 0.98), (0.525, -0.715, 0.895), (0.55, -0.775, 0.81)]
ARM_R = [(0.09, 0.115), (0.085, 0.10), (0.078, 0.092), (0.068, 0.088), (0.072, 0.092), (0.065, 0.08),
         (0.05, 0.06)]
# leg (plantigrade, knees slightly bent): thigh under the crotch -> knee -> calf -> ankle
LEG_C = [(0.235, -0.705, 0.545), (0.24, -0.675, 0.48), (0.248, -0.63, 0.41), (0.255, -0.59, 0.33),
         (0.262, -0.575, 0.255), (0.27, -0.585, 0.18)]
LEG_R = [(0.10, 0.135), (0.095, 0.125),   # s1 r08: the thigh's back wall no deeper than its root (93 deg knife)
         (0.09, 0.12), (0.075, 0.10), (0.066, 0.088), (0.064, 0.078)]
T1_ARM = 0.45
T1_LEG = 0.50       # rhino / werewolf: the leg's first ring = the region rim pulled 60 % toward the first section
# the thick ground tail: each ring = (top point (y, z), bottom point (y, z), half-width x), read off the sheet's side
# contours (top and underside) perpendicular to the tail's axis, half-widths from the rear view. s1 r02: no hug ring
# (its pushed-back top made a shelf over the tail); ring 1's bottom leaves the crotch back 37 deg down (not straight
# down: a 90 deg concave crotch / tail-underside fold is the werewolf knife)
TAIL_KEY = [((-0.35, 0.84), (-0.475, 0.56), 0.145),     # s1 r08: a root ring (the 35 cm top wall made needles)
            ((-0.25, 0.695), (-0.44, 0.535), 0.135), ((-0.188, 0.588), (-0.40, 0.42), 0.125),
            ((-0.10, 0.46), (-0.30, 0.26), 0.115), ((0.025, 0.334), (-0.115, 0.12), 0.105),
            ((0.215, 0.24), (0.121, 0.026), 0.09), ((0.466, 0.169), (0.434, 0.017), 0.07),
            ((0.727, 0.113), (0.713, 0.011), 0.05), ((0.952, 0.07), (0.948, 0.014), 0.028),
            ((1.05, 0.048), (1.05, 0.016), 0.014), ((1.10, 0.036), (1.10, 0.024), 0.006)]
TAIL_STEP = 0.13    # s1 r08: straight in-between rings so no tail segment is longer than this (needle triangles)


def tail_rings():
    out = [TAIL_KEY[0]]
    for a, b in zip(TAIL_KEY, TAIL_KEY[1:]):
        ca = (Vector(a[0]) + Vector(a[1])) / 2
        cb = (Vector(b[0]) + Vector(b[1])) / 2
        n = max(1, math.ceil((cb - ca).length / TAIL_STEP))
        for i in range(1, n + 1):
            t = i / n
            out.append((tuple(Vector(a[0]).lerp(Vector(b[0]), t)), tuple(Vector(a[1]).lerp(Vector(b[1]), t)),
                        a[2] + (b[2] - a[2]) * t))
    return out


TAIL = tail_rings()


def corner(fr, ab):
    c, e1, e2, r1, r2 = fr
    return c + e1 * ab[0] * r1 + e2 * ab[1] * r2


def region_roles(faces, lo_ring, up_ring):
    """Roles (a, b) for a face region's vertices: the boundary loop spread evenly round the unit circle in the
    region's own frame (e1 lower ring -> upper ring = the limb's outer side, e2 = +y), interior vertices inside."""
    vs = sorted({v for f in faces for v in f.verts}, key=lambda v: tuple(v.co))   # deterministic (troll r15)
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
    return PT.hand_three_finger(origin=w + fwd * 0.02, width=0.13, forward=fwd, up=up, side=1, fingers=3, curl=0.35,
                                spread=12.0, finger_len=1.0, thumb=True, thumb_curl=0.3, knuckle=0.12,
                                claw_len=0.45, wrist=(0.11, 0.085), open_root=True, name='hand')


def foot_part():
    fwd = Vector((0.16, -1.0, 0.0)).normalized()          # toes turn out a little (sheet front: feet splay)
    return PT.foot_biped(origin=Vector(J['ankle']) + Vector((0.0, -0.01, -0.015)), width=0.21, forward=fwd,
                         side=1, height=0.165, length=0.46, toes=3, toe_segs=2, claws=True, claw_len=0.55,
                         root=(0.12, 0.14), open_root=True, name='foot')


def tail_region(rings, spans, i0, nsp, cols):
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


TAIL_COLS = (9, 10, 11)   # s1 r09: 3 columns (the 2-column root left needle wedges in the gap column 9)
TAIL_HALVE = (0.15, 0.62)
LEG_COLS = (2, 3, 4, 5, 6, 7)
LEG_COLS_NOTE = 'thigh cols 2-7, gap col 8, tail cols 9-11'
ARM_COLS = (4, 5, 6, 7)   # s1 r04: 2 x 4 faces = the deltoid's depth (y -0.80..-0.58), no notch at the arm front


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

    # tail first (its region indices refer to the untouched loft): columns 10-11 from the crotch ring L0 to L3
    i0 = idx['L0']
    nsp = idx['L3'] - i0
    faces, roles = tail_region(rings, spans, i0, nsp, TAIL_COLS)
    tail_rims = []
    for (ty, tz), (by_, bz), rx in TAIL:
        top, bot = Vector((0.0, ty, tz)), Vector((0.0, by_, bz))
        c, upv, rh = (top + bot) / 2, (top - bot).normalized(), (top - bot).length / 2
        keyed = [(o.co.copy(), ab) for o, ab in roles.items()]
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(keyed, key=lambda q: (q[0] - v.co).length)[1]
        for v, (ax, bh) in new.items():
            v.co = c + Vector((ax * rx, 0, 0)) + upv * bh * rh
        walls = [g for g in r['sides'] if all(abs(w.co.x) < 1e-6 for w in g.verts)]
        bmesh.ops.delete(bm, geom=walls, context='FACES')
        faces, roles = r['faces'], new
        rim = sorted([v for v, (ax, bh) in new.items() if ax * ax + bh * bh > 0.98], key=lambda v: new[v][1])
        tail_rims.append((c.y, rim))
    # s1 r09: 2-1 ring reductions down the thin tail (needle triangles: an 24-vertex ring on a 3 cm tail): from
    # TAIL_HALVE[0] on every rim keeps its seam ends and merges its inner vertices in pairs; from TAIL_HALVE[1] again
    for y0 in TAIL_HALVE:
        tm, kept = {}, []
        for k_, (cy, rim) in enumerate(tail_rims):
            if cy < y0:
                continue
            inner = rim[1:-1]
            out_ = [rim[0]]
            for a_ in range(0, len(inner) - 1, 2):
                va, vb = inner[a_], inner[a_ + 1]
                va.co = (va.co + vb.co) / 2
                tm[vb] = va
                out_.append(va)
            if len(inner) % 2:
                out_.append(inner[-1])
            out_.append(rim[-1])
            tail_rims[k_] = (cy, out_)
        bmesh.ops.weld_verts(bm, targetmap=tm)
    # arms: 2 x 3 faces of the shoulder side right under the shoulder line (C1 -> C1~ -> C2): the region's top edge
    # is the torso's widest ring, the first arm ring is the root loop pushed out unshrunk (minotaur r08)
    faces, lo, up = region('C1', 2, ARM_COLS)
    roles, info = region_roles(faces, lo, up)
    af = frame_chain(ARM_C, ARM_R)
    # s1 r05: the first arm ring is the root rim pulled 45 % toward the deltoid section (the pushed-out hug ring left
    # a collar band and a fin at its front corner over the arm)
    fr = [dict(kind='lerp', to=af[0], t=T1_ARM)] + af
    faces, roles = grow(bm, faces, roles, fr)
    rr = bridge_part(hand_part(), one_face(bm, faces), bm=bm)
    if rr is not None:
        rest.append(rr)
    # legs: 3 x 6 faces of the pelvis underside AND flank (L0 -> L0b -> L0b~ -> L1): the region's top edge is the
    # widest hip ring, so the thigh rises out of the flank with no pelvis shelf; a 60 % transition ring, level rings
    faces, lo, up = region('L0', idx['L1'] - idx['L0'], LEG_COLS)
    roles, info = region_roles(faces, lo, up)
    lf = level(LEG_C, LEG_R)
    # s1 r11: the transition ring is back (r06 removed it for a garter crease the crops never confirmed; without it
    # the thigh's front and back walls ran from the tall region edge to one ring: 21 mm needle strips, probe 1.42 r)
    fr = [dict(kind='lerp', to=lf[0], t=T1_LEG)] + lf
    faces, roles = grow(bm, faces, roles, fr)
    rr = bridge_part(foot_part(), one_face(bm, faces), bm=bm)
    if rr is not None:
        rest.append(rr)
    snap_seam(bm)
    recalc_normals(bm)
    k.meta['_rest'] = [o.name for o in rest]
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
EYE = Vector((0.10, -0.90, 1.92))     # sheet side: the eye under the brow, on the snout side


def eye_col():
    A, B_ = P('E0'), P('F0')
    return min(range(2, 7), key=lambda j: abs((A[j].y + A[j + 1].y + B_[j].y + B_[j + 1].y) / 4 - EYE.y))


def eye_face_centre():
    A, B_ = P('E0'), P('F0')
    j = eye_col()
    return (A[j] + A[j + 1] + B_[j] + B_[j + 1]) / 4


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.04 and abs(c.y - ec0.y) < 0.07 and abs(c.z - ec0.z) < 0.04


def limb_edge(bm, frames, i):
    """The edge running along a limb from ring i to ring i+1 on its outer side (a loop cut across it rings the limb)."""
    va = vert_near(bm, corner(frames[i], (1, 0)))
    tb = corner(frames[i + 1], (1, 0))
    return min(va.link_edges, key=lambda e: (e.other_vert(va).co - tb).length)


def stage2(k, body):
    """Joint loops (elbow, knee, waist), the eye socket, a brow over it."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table()
    af = frame_chain(ARM_C, ARM_R)
    lf = level(LEG_C, LEG_R)
    sp = lambda nm, j=0: P(nm)[j]
    cuts = [('elbow loop: the elbow bend', lambda: limb_edge(bm, af, 3)),
            ('knee loop: the knee bend', lambda: limb_edge(bm, lf, 1)),
            ('waist loop: the spine bend', lambda: edge_near(bm, tuple((sp('B0') + sp('B1')) / 2)))]
    for why, fe in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, fe(), t=0.5)
    # eye socket: an inset in the eye face (E0 -> F0, column 4), its floor a shallow 4 mm step (minotaur fix 1)
    ec0 = eye_face_centre()
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    A_E = P('E0')
    B_E = (A_E[eye_col()], A_E[eye_col() + 1])
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face, its floor pushed in'):
        inner = inset(bm, [f], 0.30, 0.0)
    # owner-review fix 1: the inset of the long sheared eye face was a diagonal slit with the lens at one end; its
    # floor is now a 3.8 x 3.4 cm square round the face centre (corners in angle order, minotaur r37), 4 mm deep
    iv = list(inner[0].verts)
    fc_ = sum((v.co for v in iv), Vector()) / 4
    u_ = (B_E[1] - B_E[0]).normalized()
    w_ = fn.cross(u_).normalized()
    ang_ = lambda v: math.atan2((v.co - fc_).dot(w_), (v.co - fc_).dot(u_))
    for v, (a_, b_) in zip(sorted(iv, key=ang_), ((-1, -1), (1, -1), (1, 1), (-1, 1))):
        v.co = fc_ + u_ * a_ * 0.019 + w_ * b_ * 0.017
    move(iv, -fn * 0.002)     # fix 1b: 2 mm (the 4 mm walls of the long face shaded as a dark wedge)
    F0 = P('F0')
    move([vert_near(bm, F0[j]) for j in (eye_col(), eye_col() + 1)], (0.006, 0.0, 0.004))   # brow ridge over the eye
    # mouth line: the M0 ring (the mouth) sunk 6 mm round the snout front and sides -> a groove between the jaws
    M0 = P('M0')
    for j in range(0, 7):
        v = vert_near(bm, M0[j])
        d = Vector((v.co.x, v.co.y - (-0.72), 0.0))
        if d.length > 1e-6:
            move([v], -d.normalized() * 0.006)
    # owner-review fix 2: the tail reads as a thin rope from the rear (+45 az180, az180); the sheet's rear view shows a
    # broad paddle (+-0.13 at z 0.5). Every tail vertex behind the legs is widened 18 % across, ramped in from y -0.42
    for v in bm.verts:
        q = v.co
        if q.y > -0.42 and abs(q.x) < 0.2 and q.z < 0.66 and not (q.z < 0.22 and abs(q.x) > 0.16):
            q.x *= 1.0 + 0.18 * min(1.0, (q.y + 0.42) / 0.15)
    C1, C0 = P('C1'), P('C0')
    move([vert_near(bm, C1[j]) for j in (0, 1, 2, 3)], (0.0, -0.018, 0.0))       # pec shelf (sheet: heavy pecs)
    move([vert_near(bm, C0[j]) for j in (0, 1, 2, 3)], (0.0, -0.010, 0.012))     # pec underside
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'skin': '#8ca25c', 'cream': '#e6dca8', 'dark': '#3c3b40', 'leather': '#6b4a2e', 'brass': '#a8874e',
       'eye': '#d9a531', 'pupil': '#1d1714'}


def _interp(nm_list, z, j):
    """x, y of vertex column j of the loft at height z (linear between stations)."""
    zs = [(SECS[i][1][0][2], i) for i in range(len(SECS))]
    for (za, ia), (zb, ib) in zip(zs, zs[1:]):
        if za <= z <= zb:
            t = (z - za) / max(zb - za, 1e-9)
            a, b = Vector(SECS[ia][1][j]), Vector(SECS[ib][1][j])
            return a.lerp(b, t)
    return Vector(SECS[0][1][j]) if z < zs[0][0] else Vector(SECS[-1][1][j])


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if 0.58 < z < 1.99 and x < 0.30 and y < -0.45:
        fc = _interp(None, z, 3)
        if z > 1.70:
            if n.z < -0.45 and z < 1.80:
                return 'cream'                                           # jaw underside / throat
            return 'skin'
        # owner-review fix 3: below the belt the cream narrows into the sheet's groin V (was a square apron)
        vx = fc.x if z > 1.0 else fc.x * max(0.3, (z - 0.58) / 0.42)
        if x < vx + 0.005 and y < fc.y + 0.06 and n.y < -0.2:
            return 'cream'                                               # throat, chest, belly, groin V
    if y > -0.47 and x < 0.17 and z < 0.75 and n.z < -0.05:
        return 'cream'                                                   # tail underside (the sheet's broad stripe)
    return 'skin'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A low-poly lens: ring R on the socket, inner ring I (the pupil's rim), apex A; returns the pupil faces."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 4 for k_ in range(8)]]
    R, I = ring_(r, 0.0), ring_(r * 0.4, h * 0.85)   # fix 1: a smaller pupil disc, the amber band shows
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.3)
    pup = []
    for j in range(8):
        a, b = j, (j + 1) % 8
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        pup.append(bm.faces.new([I[a], I[b], A]))
    return pup


def full_bvh(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def hit(tree, o, d, far=3.0):
    loc, nrm, _i, _d = tree.ray_cast(Vector(o), Vector(d).normalized(), far)
    return loc, nrm


def band(tree, centre, e1, e2, half_w, n_seg, sink=0.01, out=0.022, share=0.05):
    """A closed strap round the body (the ogre's crop-6 band): ray hits per angle, outer face evened and relaxed."""
    e1, e2 = Vector(e1).normalized(), Vector(e2).normalized()
    nrm = e1.cross(e2).normalized()
    bm = bmesh.new()
    ds, ts = [], []
    for s in range(n_seg):
        t = 2 * math.pi * s / n_seg
        d = e1 * math.cos(t) + e2 * math.sin(t)
        tt = []
        for side in (-1, 1):
            o = Vector(centre) + nrm * side * half_w
            loc, fn = hit(tree, o, d)
            tt.append((loc - o).length if loc is not None else 0.4)
        ds.append(d); ts.append(tt)
    tout = [[max(t[j], t[1 - j]) if abs(t[0] - t[1]) < share else t[j] for j in (0, 1)] for t in ts]
    tout = [[max(tout[s][j], 0.5 * (tout[s - 1][j] + tout[(s + 1) % n_seg][j]))
             if abs(tout[s - 1][j] - tout[(s + 1) % n_seg][j]) < 0.08 else tout[s][j] for j in (0, 1)]
            for s in range(n_seg)]
    rows = []
    for s in range(n_seg):
        d = ds[s]
        row = []
        for j, side in enumerate((-1, 1)):
            o = Vector(centre) + nrm * side * half_w
            sk = sink[j] if isinstance(sink, tuple) else sink
            row += [o + d * (ts[s][j] - sk), o + d * (tout[s][j] + out)]
        rows.append([bm.verts.new(p) for p in (row[0], row[1], row[3], row[2])])
    for s in range(n_seg):
        a, b = rows[s], rows[(s + 1) % n_seg]
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    return bm


def buckle_bm(c, w, h, y_front, y_back):
    """A square buckle plate (the sheet's belt buckle): a closed box, front face proud of the belt."""
    bm = bmesh.new()
    pts = []
    for y in (y_back, y_front):
        pts.append([bm.verts.new((c[0] + sx * w, y, c[2] + sz * h)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    b, f = pts
    bm.faces.new(b[::-1]); bm.faces.new(f)
    for j in range(4):
        bm.faces.new([b[j], b[(j + 1) % 4], f[(j + 1) % 4], f[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


BELT_Z = 1.065


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('skin', 'cream')}, body_rule)
    tree = full_bvh(body)
    pieces = []
    one = lambda key: (lambda c_, n_, i: key)
    # eye: an amber lens on the socket floor with a dark pupil disc (minotaur r36/r39: centre and normal from a ray
    # hit on the floor)
    ec = eye_face_centre()
    A_, B_ = P('E0'), P('F0')
    j = eye_col()
    n = (B_[j] - A_[j + 1]).cross(B_[j + 1] - A_[j]).normalized()
    n = n if n.x > 0 else -n
    c = ec - n * 0.004
    loc, fnn = hit(tree, ec + n * 0.05, -n)
    if loc is not None:
        c, n = loc, (fnn if fnn.dot(n) > 0 else -fnn)
    n = (n + Vector((0.0, -0.35, 0.08))).normalized()   # fix 1c: the lens looks a little forward (3/4 view 0.34)
    bm = bmesh.new()
    pup_c = [f.calc_center_median() for f in lens(bm, c - n * 0.003, n, 0.019, 0.019)]   # fix 1b: by face, not
                                                                                          # by the unset index
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if any((c_ - q).length < 1e-5 for q in pup_c) else 'eye')
    pieces.append(eye)
    # belt and buckle
    belt = object_from_bm('belt', band(tree, (0.0, -0.68, BELT_Z), (1, 0, 0), (0, 1, 0), 0.032, 32,
                                         sink=(0.01, 0.0), out=0.022, share=0.15), mirror=False)
    paint(belt, {'leather': PAL['leather']}, one('leather'))
    pieces.append(belt)
    loc, _n = hit(tree, (0, -1.6, BELT_Z), (0, 1, 0))
    buckle = object_from_bm('buckle', buckle_bm((0.0, 0.0, BELT_Z), 0.05, 0.04, loc.y - 0.035, loc.y + 0.005),
                            mirror=False)
    paint(buckle, {'brass': PAL['brass']}, one('brass'))
    pieces.append(buckle)
    # the welded parts' loose shells (hand and foot claws): mirrored, painted dark
    for nm in k.meta.get('_rest', []):
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        paint(o, {'dark': PAL['dark']}, one('dark'))
        if 'hand' in nm:
            # s3: the hand claws' top faces lay on the finger tops facing the same way (z-fight 6, werewolf s3 r17):
            # each claw shell moves 8 mm out along wrist -> claw
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
                d = (cen - Vector(J['wrist'])).normalized()
                for v in shell:
                    v.co += o.matrix_world.inverted().to_3x3() @ (d * 0.008)
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
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('tail3', J['tail3'], J['tail4'], 'tail2', True),
         ('tail4', J['tail4'], J['tail5'], 'tail3', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing through the chest, a head turn, the tail tip sweeps
    clip(rig, 'idle', {1: {},
                       12: {'chest': (2, 0, 0), 'head': (0, 0, 6), 'tail3': (0, 0, 6), 'tail4': (0, 0, 8),
                            'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       24: {'tail3': (0, 0, -2)},
                       36: {'chest': (2, 0, 0), 'head': (0, 0, -6), 'tail3': (0, 0, -6), 'tail4': (0, 0, -8),
                            'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       48: {}})
    # move: a heavy stride; the swinging leg folds at the knee, arms swing against the legs, the tail sways behind
    A, S = 12, 12
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
            'spine': (0, 0, 3), 'tail2': (0, 0, 4), 'tail3': (0, 0, 5)},
        9: {'shin.R': (-24, 0, 0), 'foot.R': (12, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0),
             'spine': (0, 0, -3), 'tail2': (0, 0, -4), 'tail3': (0, 0, -5)},
        25: {'shin.L': (-24, 0, 0), 'foot.L': (12, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
             'spine': (0, 0, 3), 'tail2': (0, 0, 4), 'tail3': (0, 0, 5)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.025, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.025, 0)},
             33: {'hips': (0, 0, 0)}})
    # attack: a claw swipe - wind the right arm up and back, rake it down and across, the head lunges, tail lashes
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (-5, 0, 3), 'neck': (-6, 0, 0), 'upperarm.R': (40, 0, -25), 'forearm.R': (30, 0, 0),
             'tail3': (0, 0, 8)},
        18: {'spine': (5, 0, -3), 'chest': (8, 0, -4), 'neck': (6, 0, 0), 'head': (8, 0, 0),
             'upperarm.R': (-30, 0, -10), 'forearm.R': (10, 0, 0), 'tail3': (0, 0, -8)},
        26: {'spine': (3, 0, -1), 'chest': (4, 0, -2)},
        36: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
