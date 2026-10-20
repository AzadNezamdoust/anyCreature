import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
import parts as PT

# gorilla (knuckle-walking silverback), t7 hand box model (zoo workflow v2). ONE spine loft of 14-vertex half rings
# runs rump -> crest: level-axis rings over the haunch and belly (ventral seam under the belly, dorsal seam along the
# back), then the rings TILT up through the chest (ventral seam up the chest front, dorsal seam up the back slope)
# into the low, jutting head, ending at the sagittal crest. Arms (minotaur/troll shoulder method): the deltoid is the
# torso's own widest ring (C2); each arm grows from a 2 x 3-face region whose top edge sits on C2, its first ring the
# root loop pushed out unshrunk, then frame rings down to a knuckle pad on the ground. Legs from 4 x 3-face windows
# on the haunch underside. Coordinates from blueprint.json (refs.py, height 1.5 m at the crest).
# Identity cue (gorilla, not bear/ape-man): knuckle-walk stance - the torso slopes UP from the rump to huge shoulders,
# very long massive arms planted on knuckles in front, short bent hind legs; a high sagittal crest on a head hung low
# and forward between the shoulders; a clear jaw and a protruding muzzle under a heavy brow; silver saddle.
META = dict(creature='gorilla', model='opus', stage1_tris=(1500, 3600), total_tris=(2600, 5800),
            closeups=[('head', (0.0, -0.66, 1.20), 0.30, 'hero'),
                      ('shoulder', (0.42, -0.36, 0.98), 0.34, 'hero'),
                      ('hand', (0.37, -0.64, 0.10), 0.24, 'hero'),
                      ('hind foot', (0.27, 0.58, 0.10), 0.30, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.52, 0.80), spine=(0.0, 0.12, 0.84), chest=(0.0, -0.28, 0.98), neck=(0.0, -0.44, 1.10),
    head=(0.0, -0.53, 1.16), top=(0.0, -0.74, 1.24),
    shoulder=(0.36, -0.36, 1.00), elbow=(0.36, -0.47, 0.58), wrist=(0.37, -0.64, 0.17), hand=(0.37, -0.66, 0.02),
    hipL=(0.24, 0.50, 0.62), knee=(0.26, 0.47, 0.38), ankle=(0.27, 0.61, 0.13), toe=(0.27, 0.36, 0.03),
)

NV = 14     # vertices per half ring (ventral seam -> dorsal seam): 13 faces per span


def prof(e=0.85, w=0.0, back=0.0, keel=0.0, n=NV):
    """Half-ring profile, ventral seam -> dorsal seam: (x as a share of W, fh: +1 ventral .. -1 dorsal).
    e: roundness (lower = boxier); w > 0 moves the widest point ventral; back > 0 widens the dorsal half;
    keel > 0 narrows the ventral half (a chest keel between the arms)."""
    out = []
    for i in range(n):
        t = math.pi * i / (n - 1)
        c = math.cos(t)
        fx = 0.0 if i in (0, n - 1) else math.sin(t) ** e * (1.0 + back * (-c)) * (1.0 - keel * max(c, 0.0))
        out.append((round(fx, 4), round(c + w * (1 - c * c), 4)))
    return out


BODY = prof(0.8, 0.0, 0.12)            # r11: the dorsal half broader (the sheet's flat, broad back)
HAUNCH = prof(0.7, 0.05, 0.05)
CHEST = prof(0.9, -0.05, 0.0, 0.55)
# the chest rings, hand placed: a narrow keel between the arms (j1-j4, x <= 0.4 W), the arm region's lower edge at j5,
# the widest point at j8 = the deltoid line (the region's top edge), the trapezius rounding over j9-j12 to the back
CH = [(0.0, 1.0), (0.18, 0.97), (0.30, 0.88), (0.36, 0.74), (0.33, 0.56), (0.40, 0.36), (0.68, 0.15), (0.86, -0.07),
      (0.98, -0.28), (0.90, -0.48), (0.74, -0.66), (0.52, -0.82), (0.27, -0.94), (0.0, -1.0)]
# r12: the trapezius slopes from the deltoid line up to the spine (r11's flat back made a level shelf with a vertical
# outer wall from +45 az180); T1, in front of the deltoid ring, continues the chest keel and the j8 shoulder line
# (the TRAPP T1 bulged out at j5 over the arm's front wall: a dark wedge at the front of the shoulder)
T1P = [(0.0, 1.0), (0.18, 0.97), (0.30, 0.88), (0.37, 0.74), (0.44, 0.56), (0.56, 0.36), (0.76, 0.15), (0.92, -0.07),
       (1.0, -0.28), (0.90, -0.48), (0.72, -0.66), (0.50, -0.82), (0.26, -0.94), (0.0, -1.0)]
TRAP = prof(0.9, -0.10, 0.15, 0.45)
NECK = prof(0.85, -0.05, 0.25, 0.35)
# head rings, hand placed (r05): pear sections - the face/cheek side (ventral) full, the skull tapering dorsally into
# the sagittal crest (the r01 HEAD/JAW were round: the head read as a tilted drum, a 'top hat')
JAW = [(0.0, 1.0), (0.38, 0.99), (0.68, 0.955), (0.88, 0.86), (0.97, 0.68), (1.0, 0.45), (1.0, 0.2), (0.97, -0.05),
       (0.90, -0.30), (0.80, -0.53), (0.65, -0.72), (0.46, -0.87), (0.24, -0.97), (0.0, -1.0)]
# r08: the face is a broad flat plane (j0-j2 within 2 % of the chord), a corner at j3 into the cheek, the skull
# tapering dorsally into the crest
HEAD = [(0.0, 1.0), (0.30, 0.99), (0.60, 0.955), (0.75, 0.87), (0.85, 0.70), (0.95, 0.47), (1.0, 0.22), (0.98, -0.04),
        (0.90, -0.30), (0.78, -0.53), (0.62, -0.72), (0.45, -0.87), (0.25, -0.97), (0.0, -1.0)]
# r09: the head and trapezius are ONE mass from the side (no neck): ring widths fall smoothly T1 -> crest, the ring's
# middle (temple / behind the ear) wider than the flat face front (j2-j3 at 0.6-0.75 W)


# r10: trapezius rings, hand placed: the dorsal half falls in a straight line to the dorsal seam (the sheet's front view
# runs straight from the shoulder (0.41, 1.15) to the crest; the round TRAP/NECK profiles bulged it into a dome)
TRAPP = [(0.0, 1.0), (0.20, 0.97), (0.36, 0.88), (0.52, 0.74), (0.70, 0.56), (0.86, 0.35), (0.97, 0.12), (1.0, -0.12),
         (0.92, -0.35), (0.78, -0.56), (0.60, -0.74), (0.42, -0.88), (0.22, -0.97), (0.0, -1.0)]


def tb(nm, F, B, W, p):
    """A ring from its ventral and dorsal seam points (y, z), half width W at the chord's middle."""
    return (nm, tuple(F), tuple(B), W, p)


# the spine loft, rump -> crest: (name, ventral seam (y, z), dorsal seam (y, z), W, profile)
SECS = [
    tb('R0', (0.735, 0.625), (0.745, 0.785), 0.15, HAUNCH),    # rump end (r06: a small ring, the cap poked out: a dome)
    tb('R1', (0.705, 0.53), (0.715, 0.885), 0.29, HAUNCH),
    tb('R2', (0.625, 0.47), (0.645, 0.97), 0.37, HAUNCH),
    tb('R3', (0.51, 0.45), (0.54, 1.025), 0.42, HAUNCH),       # haunch
    tb('R4', (0.41, 0.45), (0.43, 1.045), 0.44, HAUNCH),
    tb('R5', (0.31, 0.455), (0.32, 1.05), 0.43, HAUNCH),
    tb('R6', (0.20, 0.46), (0.21, 1.065), 0.40, BODY),        # loin
    tb('R7', (0.09, 0.455), (0.10, 1.113), 0.39, BODY),       # waist
    tb('R8', (-0.03, 0.455), (0.015, 1.176), 0.40, BODY),     # belly
    tb('R9', (-0.16, 0.48), (-0.04, 1.218), 0.42, BODY),
    tb('R10', (-0.29, 0.52), (-0.085, 1.252), 0.42, CH),   # ribs: the rings tilt up into the chest
    tb('C0', (-0.42, 0.58), (-0.125, 1.283), 0.46, CH),    # armpit
    tb('C1', (-0.53, 0.66), (-0.165, 1.315), 0.49, CH),
    tb('C2', (-0.60, 0.76), (-0.20, 1.345), 0.51, CH),     # the deltoid line: the torso's WIDEST ring
    tb('T1', (-0.64, 0.83), (-0.24, 1.37), 0.46, T1P),       # trapezius: a rounded mass from the shoulder to the crest
    tb('T2', (-0.675, 0.865), (-0.285, 1.40), 0.36, TRAPP),    # neck / throat under the jaw
    tb('H0u', (-0.725, 0.885), (-0.33, 1.425), 0.29, JAW),    # jaw line (the jaw underside, ahead of the throat)
    tb('H0', (-0.775, 0.925), (-0.375, 1.45), 0.255, JAW),    # chin
    tb('H1', (-0.81, 1.0), (-0.415, 1.47), 0.235, HEAD),       # mouth
    tb('H2', (-0.79, 1.09), (-0.45, 1.485), 0.225, HEAD),      # nose
    tb('H3', (-0.765, 1.165), (-0.48, 1.493), 0.215, HEAD),    # eye
    tb('H4', (-0.755, 1.225), (-0.505, 1.498), 0.2, HEAD),   # brow ridge
    tb('H5', (-0.70, 1.30), (-0.525, 1.50), 0.145, HEAD),      # forehead
    tb('H6', (-0.63, 1.39), (-0.54, 1.50), 0.07, HEAD),       # crest
]


def sec_pts(F, B, W, p):
    F, B = Vector((0.0,) + tuple(F)), Vector((0.0,) + tuple(B))
    m, u = (F + B) / 2, (B - F) / 2
    return [(fx * W, (m - u * fh).y, (m - u * fh).z) for fx, fh in p]


def P(nm):
    for (n, F, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(F, B, W, p)]


# ---- arm (minotaur/troll method): frame rings (centre, (r lateral, r front-back)) after the hug ring
ARM_C = [(0.39, -0.40, 0.80), (0.375, -0.44, 0.69), (0.36, -0.47, 0.58),                         # upper arm, elbow
         (0.37, -0.52, 0.47), (0.37, -0.57, 0.35), (0.37, -0.61, 0.25), (0.37, -0.64, 0.17),      # forearm, wrist
         (0.37, -0.645, 0.09), (0.37, -0.645, 0.03), (0.37, -0.645, 0.0)]                         # knuckle pad
ARM_R = [(0.15, 0.175), (0.15, 0.185), (0.14, 0.19),
         (0.17, 0.19), (0.165, 0.175), (0.14, 0.15), (0.12, 0.13),
         (0.145, 0.16), (0.15, 0.165), (0.15, 0.165)]
ARM_ELBOW = 2
ARM_SPAN, ARM_COLS = 'C0', (5, 6, 7)

# ---- hind leg: level rounded-box sections (cx, cy, z, rx, ry, exponent) under the haunch window
LEG = [(0.27, 0.50, 0.40, 0.17, 0.22, 2.6),     # knee / thigh under the haunch (r07: the sheet's legs are massive)
       (0.275, 0.54, 0.31, 0.16, 0.21, 2.6),    # calf
       (0.28, 0.58, 0.22, 0.145, 0.18, 2.6),
       (0.28, 0.61, 0.15, 0.13, 0.15, 2.6),     # ankle
       (0.28, 0.60, 0.08, 0.145, 0.20, 2.4),    # foot
       (0.28, 0.59, 0.03, 0.15, 0.22, 2.4),
       (0.28, 0.59, 0.0, 0.15, 0.22, 2.4)]
LEG_WIN, LEG_J0, LEG_A, LEG_B, T1_LEG = 'R1', 1, 4, 4, 0.45


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


def corner(fr, ab):
    c, e1, e2, r1, r2 = fr
    return c + e1 * ab[0] * r1 + e2 * ab[1] * r2


def region_roles(faces, lo_ring, up_ring):
    """(this creature: lo_ring / up_ring are the region's lower (inner) and upper (deltoid) COLUMN vertex sets)"""
    """Roles (a, b) for a face region's boundary: spread evenly round the unit circle in the region's own frame
    (e1 lower ring -> upper ring = the limb's outer side, e2 = +y), the phase fitted to the true angles."""
    vs = sorted({v for f in faces for v in f.verts}, key=lambda v: tuple(v.co))
    fs = set(faces)
    bnd = [v for v in vs if any(f not in fs for f in v.link_faces)]
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
    roles = {v: (math.cos(ph + 2 * math.pi * rk / n), math.sin(ph + 2 * math.pi * rk / n)) for rk, v in enumerate(order)}
    nrm = sum((f.normal * f.calc_area() for f in faces), Vector()).normalized()
    return roles, (cen, nrm)


def grow_frames(bm, faces, roles, frames):
    """Extrude a (dissolved, one-face) root region frame by frame; a dict frame is a hug ring: the root loop
    itself pushed `out` along the region normal and scaled k about its centre."""
    for fr in frames:
        keyed = [(o.co.copy(), ab) for o, ab in roles.items()]
        r = extrude(bm, faces)
        new = {v: min(keyed, key=lambda q: (q[0] - v.co).length)[1] for v in r['verts']}
        if isinstance(fr, dict):
            for v, ab in new.items():
                # r15: the inner (armpit) half of the hug ring is pushed straight out sideways (a level band facing
                # down), the deltoid half along the region normal: no 138 deg fold back under the region edge
                w = max(0.0, -ab[0])
                d = fr['n'].lerp(Vector((1.0, 0.0, 0.0)), w).normalized()
                v.co = fr['c'] + (v.co - fr['c']) * fr['k'] + d * fr['out']
        else:
            for v, ab in new.items():
                v.co = corner(fr, ab)
        faces, roles = r['faces'], new
    return faces, roles


def akey(t):
    return round(t if t < math.pi - 1e-6 else -math.pi, 4)


def role_pos(sec, u, s, amap=None):
    """u across (+1 = +x side), s front/back (+1 = rear). Boundary roles sit on the section's superellipse at the
    angle of (u, s) (amap: grid angle -> evenly spaced angle)."""
    cx, cy, z, rx, ry, n = sec[:6]
    if abs(u) > 0.999 or abs(s) > 0.999:
        th = math.atan2(s, u)
        if amap:
            th = amap[akey(th)]
        c, sn = math.cos(th), math.sin(th)
        return Vector((cx + rx * math.copysign(abs(c) ** (2 / n), c), cy + ry * math.copysign(abs(sn) ** (2 / n), sn), z))
    return Vector((cx + u * rx * 0.85, cy + s * ry * 0.85, z))


def grow_win(bm, rings, spans, i0, j0, A, B, secs, t1):
    """Extrude the A x B face window (rings i0..i0+A, ring vertices j0..j0+B) section by section (rhino method).
    The first new ring slopes from the window rim t1 of the way to secs[0] (the broad transition)."""
    faces = [spans[i0 + a][j0 + b] for a in range(A) for b in range(B)]
    G = [[rings[i0 + a][j0 + b] for b in range(B + 1)] for a in range(A + 1)]
    su = 1 if G[A // 2][0].co.x > G[A // 2][B].co.x else -1
    ss = 1 if G[0][B // 2].co.y > G[A][B // 2].co.y else -1
    roles = [(G[a][b].co.copy(), (su * (1 - 2 * b / B), ss * (1 - 2 * a / A))) for a in range(A + 1) for b in range(B + 1)]
    th = sorted({akey(math.atan2(s_, u_)) for _p, (u_, s_) in roles if abs(u_) > 0.999 or abs(s_) > 0.999})
    N = len(th)
    off = 0.0 if any(abs(t) < 1e-6 for t in th) else math.pi / N
    base = min(range(N), key=lambda i: abs(th[i] - (-math.pi + off)))
    amap = {th[(base + i) % N]: -math.pi + off + 2 * math.pi * i / N for i in range(N)}
    rp = lambda sec, u_, s_: role_pos(sec, u_, s_, amap)

    def step(faces, roles, place):
        r = extrude(bm, faces)
        new = []
        for v in r['verts']:
            o = min(roles, key=lambda o_: (o_[0] - v.co).length)
            new.append((v, o))
        for v, (p0, ro) in new:
            v.co = place(p0, ro)
        return r['faces'], [(v.co.copy(), ro) for v, (p0, ro) in new]

    def first(p0, ro):
        q = role_pos(secs[0], *ro)
        return p0 + (q - p0) * t1
    faces, roles = step(faces, roles, first)
    for sec in secs:
        faces, roles = step(faces, roles, lambda p0, ro, sec=sec: rp(sec, *ro))
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(F, B, W, p)) for (nm, F, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    rump = cap(bm, rings[0])
    top = cap(bm, rings[-1])
    recalc_normals(bm)
    pk = bmesh.ops.poke(bm, faces=[top])                        # the crest: a low ridge dome, not a flat lid
    for v in pk['verts']:
        v.co.z += 0.008
    pk = bmesh.ops.poke(bm, faces=[rump])                       # the rump: a low dome, not a flat oval lid
    for v in pk['verts']:
        v.co.y += 0.022

    # hind legs: a 4-span x 3-face window of the haunch underside (R1 -> R5, j1..j4): the leg rises out of the haunch
    grow_win(bm, rings, spans, idx[LEG_WIN], LEG_J0, LEG_A, LEG_B, LEG, T1_LEG)

    # arms: a 2 x 3 face region of the chest side right under the deltoid line (C0 -> C1 -> C2, columns 5-7): its top
    # edge IS the torso's widest ring; dissolved to one face, first ring = the root loop pushed out unshrunk
    i = idx[ARM_SPAN]
    faces = [spans[i + m][c] for m in range(2) for c in ARM_COLS]
    c0, c1 = ARM_COLS[0], ARM_COLS[-1] + 1
    roles, (cen, nrm) = region_roles(faces, [rings[i + m][c0] for m in range(3)], [rings[i + m][c1] for m in range(3)])
    inner = [v for f in faces for v in f.verts if all(g in faces for g in v.link_faces)]
    faces = bmesh.ops.dissolve_faces(bm, faces=faces, use_verts=False)['region']
    loose = [v for v in inner if v.is_valid and not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    roles = {v: ab for v, ab in roles.items() if v.is_valid}
    grow_frames(bm, faces, roles, [dict(c=cen, n=nrm, out=0.045, k=1.0)] + frame_chain(ARM_C, ARM_R))
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
def face_c(nm_lo, nm_up, j):
    A, B_ = P(nm_lo), P(nm_up)
    return (A[j] + A[j + 1] + B_[j] + B_[j + 1]) / 4


EYE_SPAN, EYE_COL = ('H3', 'H4'), 1
SOCKET = []


def keep_eye(c):
    e = SOCKET[0]
    return abs(abs(c.x) - e.x) < 0.04 and abs(c.y - e.y) < 0.04 and abs(c.z - e.z) < 0.05


def stage2(k, body):
    """The joint loops (elbow, knee), the eye socket (an inset in the eye face under the brow, its floor pushed in) and
    the brow ridge forward over it."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    af = frame_chain(ARM_C, ARM_R)

    def limb_edge(frames, i):
        va = vert_near(bm, corner(frames[i], (1, 0)))
        tb_ = corner(frames[i + 1], (1, 0))
        return min(va.link_edges, key=lambda e: (e.other_vert(va).co - tb_).length)

    def leg_edge(i):
        a, b = LEG[i], LEG[i + 1]
        va = vert_near(bm, (a[0] + a[3], a[1], a[2]))
        tb_ = Vector((b[0] + b[3], b[1], b[2]))
        return min(va.link_edges, key=lambda e: (e.other_vert(va).co - tb_).length)
    cuts = [('elbow loop: the elbow bend', lambda: limb_edge(af, ARM_ELBOW)),
            ('knee loop: the knee bend', lambda: leg_edge(0))]
    for why, fe in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, fe(), t=0.5)
    ec = face_c(*EYE_SPAN, EYE_COL)
    f = face_near(bm, ec)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face under the brow, its floor pushed in'):
        inner = inset(bm, [f], 0.22, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.003)                            # s2 r5: a shallow socket (the side view needs the lens clear)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    H4 = P('H4')
    move([vert_near(bm, H4[j]) for j in (0, 1, 2, 3)], (0.0, -0.013, 0.004))    # the heavy brow ridge over the eye (r5: 1.8 -> 1.3 cm)
    # s2 r2: the collar step C2 -> T1 -> T2 (W 0.51 / 0.46 / 0.36; a ledge round the neck seen from the top and az000):
    # the shoulder-to-crest rings relaxed along the loft (each vertex half way to the mean of its neighbours up and down
    # the column, twice), so the trapezius is one sloping mass from the deltoid line to the crest
    names = ['C2', 'T1', 'T2', 'H0u', 'H0']     # r4: from C2 (C1 j6/j7 are gone into the arm region; C2 stays put)
    col = {nm: [vert_near(bm, q) for q in P(nm)] for nm in names}
    for _it in range(2):
        new = {}
        for a_, b_, c_ in zip(names, names[1:], names[2:]):
            for j in range(5, 13):
                v = col[b_][j]
                new[v] = v.co.lerp((col[a_][j].co + col[c_][j].co) / 2, 0.5)
        for v, p in new.items():
            v.co = p
    # s2 r4: T1's lower side (j4-j5, x 0.23 / 0.26) stood out past the arm region's front-lower corner (C2 j5, x 0.20)
    # and overhung the arm's front wall: a 112 deg fold (probe s4 r02). Drawn in to the C2 keel line (-> 92 deg).
    col['T1'][4].co.x -= 0.03
    col['T1'][5].co.x -= 0.05
    # s2 r3: junction knife folds (probe s4 r01: groin 135 deg at x 0.12-0.15, thigh front 94 deg at y 0.31; the
    # armpit's 138 deg went to the S1 re-lock r16).
    # leg: the knee section's inner side out (the inner thigh wall slopes OUT going down, no overhang under the belly)
    # and its front back 2 cm (the thigh front slopes back from the groin like the sheet's); the transition ring half
    sec0 = [v for v in bm.verts if 0.385 < v.co.z < 0.415 and 0.05 < v.co.x < 0.5 and 0.2 < v.co.y < 0.8]
    for v in sec0:
        t_ = max((e.other_vert(v) for e in v.link_edges), key=lambda w: w.co.z)
        dx = 0.04 if v.co.x < 0.2 else 0.0
        dy = 0.02 if v.co.y < 0.40 else 0.0
        v.co += Vector((dx, dy, 0.0))
        t_.co += Vector((dx * 0.5, dy * 0.5, 0.0))
    # s2 r6: the face was a flat box plate under a brow shelf (hero close-up 0). The muzzle juts (mouth ring H1 2 cm,
    # chin H0 1.5 cm, nose H2 1 cm forward on the front columns j0-j2) and the face's side columns j3 of H0-H4 step
    # back 1.5 cm, so the face front rounds into the cheeks
    for nm, dy in (('H0', -0.015), ('H1', -0.02), ('H2', -0.01)):
        for jj in (0, 1, 2):
            vert_near(bm, P(nm)[jj]).co.y += dy * (1.0 if jj < 2 else 0.6)
    for nm in ('H0', 'H1', 'H2', 'H3', 'H4'):
        vert_near(bm, P(nm)[3]).co.y += 0.015
    # s2 r5: the groin (probe s4 r03: 96-98 deg where the level crotch strip met the thigh's vertical inner wall along
    # the window's inner edge, x 0.15): the ventral seam between the thighs dropped 3 cm (R1-R5, R6 1.5 cm) - a shallow
    # V, the crotch faces turn down-and-in into the inner thigh
    for nm, dz in (('R1', 0.03), ('R2', 0.03), ('R3', 0.03), ('R4', 0.03), ('R5', 0.03), ('R6', 0.015)):
        vert_near(bm, P(nm)[0]).co.z -= dz
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'fur': '#55545a', 'saddle': '#a9a9ae', 'skin': '#3d3a3b', 'eye': '#5b3a20', 'pupil': '#140f0c'}
# s3 r2: colour follows topology - each face is coloured by the loft ring and column (j) it sits on (the r1 rule cut
# across tilted rings by height: a stepped 'tetris' saddle border)
_RINGPTS = None


def ring_col(c):
    """(ring, column, distance) of the S1 loft quad whose centre is nearest: ring i -> i+1, column j -> j+1 (s3 r4:
    nearest VERTEX tied between two columns and stepped the saddle border face by face)"""
    global _RINGPTS
    if _RINGPTS is None:
        _RINGPTS = []
        for (a, *_r), (b, *_s) in zip(SECS, SECS[1:]):
            A, B_ = P(a), P(b)
            for j in range(NV - 1):
                _RINGPTS.append((a, j, (A[j] + A[j + 1] + B_[j] + B_[j + 1]) / 4))
    q = Vector((abs(c.x), c.y, c.z))
    d, nm, j = min(((q - p).length, nm, j) for nm, j, p in _RINGPTS)
    return nm, j, d


SADDLE_BACK = ('R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9')
HAUNCH_SIDE = ('R0', 'R1', 'R2', 'R3', 'R4')


def body_rule(c, n, i):
    nm, j, d = ring_col(c)
    if d < 0.07:
        if nm in ('H0', 'H1', 'H2', 'H3') and j <= 2:
            return 'skin'                               # the face: chin to brow, the front plane only (no wide mask)
        # review fix 1: ONE border column (j >= 6) along the whole back and haunch, the rump end (R0-R1) all silver;
        # the j9/j5/j2 mix stepped the border face by face on the haunch (thigh crops B)
        # review fix 2: no rump exception (R0-R1 j >= 1 made one big zigzag notch at the haunch, az135 / az225)
        if nm in SADDLE_BACK and j >= 5:
            return 'saddle'                             # the silver saddle: back, rump, haunch sides
        return 'fur'
    if c.y > 0.73 and c.z > 0.55:
        return 'saddle'                                 # the rump cap (s4 r8: it showed as a dark hole from behind)
    if c.z < 0.075:
        return 'skin'                                   # soles of the knuckle pads and feet
    return 'fur'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A low round lens: an 8-vertex rim, an inner ring and a crown; its back a cone sunk in the socket."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 4 for k_ in range(8)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.4)
    for j in range(8):
        a, b = j, (j + 1) % 8
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def box_chain(bm, rows):
    R = [[bm.verts.new(Vector(p)) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def full_bvh(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def hit(tree, o, d, far=3.0):
    loc, nrm, _i, _d = tree.ray_cast(Vector(o), Vector(d).normalized(), far)
    return loc, nrm


def digits(bm, tree, cx, cy, spec, side, back=0.03):
    """Rounded digit rolls on the front of a pad: (x offset, half width, length, height) each, rooted `back` inside
    the pad's front wall (found by a ray from the front at mid height)."""
    for o, w, L, hgt in spec:
        x = cx + o
        loc, _n = hit(tree, (x, cy - 1.0, hgt * 0.5), (0, 1, 0))
        if loc is None:
            continue
        h = Vector((x, loc.y, 0.0))
        rows = [[h + Vector((-w, back, 0.006)), h + Vector((w, back, 0.006)), h + Vector((w, back, hgt)), h + Vector((-w, back, hgt))],
                [h + Vector((-w, -L * 0.5, 0.005)), h + Vector((w, -L * 0.5, 0.005)), h + Vector((w * 0.92, -L * 0.5, hgt * 0.88)), h + Vector((-w * 0.92, -L * 0.5, hgt * 0.88))],
                [h + Vector((-w * 0.8, -L, 0.005)), h + Vector((w * 0.8, -L, 0.005)), h + Vector((w * 0.7, -L, hgt * 0.55)), h + Vector((-w * 0.7, -L, hgt * 0.55))]]
        if side < 0:
            rows = [[Vector((-p.x, p.y, p.z)) for p in reversed(r)] for r in rows]
        box_chain(bm, rows)


HAND_DIGITS = [(-0.105, 0.036, 0.06, 0.085), (-0.035, 0.036, 0.07, 0.09), (0.035, 0.036, 0.07, 0.09),
               (0.105, 0.034, 0.06, 0.08)]          # four curled finger rolls (knuckle-walk: middle phalanges down)
FOOT_DIGITS = [(-0.115, 0.042, 0.10, 0.07), (-0.03, 0.03, 0.07, 0.055), (0.03, 0.029, 0.065, 0.05),
               (0.08, 0.027, 0.06, 0.046), (0.125, 0.025, 0.05, 0.042)]   # the big toe medial and set apart


def ear_slab(c, nrm, up, w, h, th):
    """A small closed ear slab: two 8-gon outlines th apart (membrane check: a real thickness everywhere)."""
    n = Vector(nrm).normalized(); u = (Vector(up) - n * Vector(up).dot(n)).normalized(); s_ = n.cross(u)
    bm = bmesh.new()
    pts = [s_ * math.cos(t) * w + u * math.sin(t) * h for t in [k_ * math.pi / 4 for k_ in range(8)]]
    A = [bm.verts.new(c + p) for p in pts]
    B = [bm.verts.new(c + p * 0.85 + n * th) for p in pts]
    bm.faces.new(list(reversed(A)))
    bm.faces.new(B)
    for j in range(8):
        bm.faces.new([A[j], A[(j + 1) % 8], B[(j + 1) % 8], B[j]])
    recalc_normals(bm)
    return bm


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('fur', 'saddle', 'skin')}, body_rule)
    tree = full_bvh(body)
    pieces = []
    # eyes: small round lenses in the sockets, facing forward-out
    c0, n0 = SOCKET[0].copy(), SOCKET[1].normalized()
    if n0.x < 0:
        n0 = Vector((-n0.x, n0.y, n0.z))
    n = (n0 + Vector((1.9, -0.1, 0.0))).normalized()     # s3 r2-3: turned out (side view 0.03 / 0.13)
    bm = bmesh.new()
    lens(bm, c0 + n * 0.015, n, 0.023, 0.010)          # s3 r2/r4: 46 mm (0.054 of the head was < 0.06)
    eye = object_from_bm('eye', bm)
    tip = c0 + n * 0.025
    paint(eye, {'eye': PAL['eye'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if (Vector((abs(c_.x), c_.y, c_.z)) - tip).length < 0.010 else 'eye')
    pieces.append(eye)
    # ears (s3 r3): small closed slabs flat to the skull side, 1.3 cm thick (the ear_cup rim was 3-4 mm: membrane FAIL)
    for side in (1, -1):
        o = Vector((side * 0.30, -0.51, 1.23))
        loc, nr = hit(tree, o, (-side, 0, 0))
        nn = Vector((side * abs(nr.x), nr.y, nr.z)) if nr is not None else Vector((side, 0, 0))
        bm = ear_slab(loc - nn * 0.006, nn, (0, 0.2, 1), 0.032, 0.042, 0.013)
        ear = object_from_bm(f'ear_{"L" if side > 0 else "R"}', bm, mirror=False)
        paint(ear, {'fur': PAL['fur'], 'skin': PAL['skin']}, lambda c_, n_, i, nn=nn: 'skin' if n_.dot(nn) > 0.7 else 'fur')
        pieces.append(ear)
    # knuckle pads: four finger rolls on the front of each pad; hind feet: five toes
    for side in (1, -1):
        bm = bmesh.new()
        digits(bm, tree, ARM_C[-1][0], ARM_C[-1][1], HAND_DIGITS, side)
        hd = object_from_bm(f'fingers_{"L" if side > 0 else "R"}', bm, mirror=False)
        paint(hd, {'skin': PAL['skin']}, lambda c_, n_, i: 'skin')
        pieces.append(hd)
        bm = bmesh.new()
        digits(bm, tree, LEG[-1][0], LEG[-1][1], FOOT_DIGITS, side)
        to = object_from_bm(f'toes_{"L" if side > 0 else "R"}', bm, mirror=False)
        paint(to, {'skin': PAL['skin']}, lambda c_, n_, i: 'skin')
        pieces.append(to)
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
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_fingers'):
            bind(p, rig, bone='hand.L' if p.name.endswith('_L') else 'hand.R')
        elif p.name.startswith('piece_toes'):
            bind(p, rig, bone='foot.L' if p.name.endswith('_L') else 'foot.R')
        else:
            bind(p, rig, body=body)
    # idle: heavy breathing, the head looks round
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, 6)},
                       24: {}, 36: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, -6)}, 48: {}})
    # move: a knuckle walk - diagonal pairs (left arm with right leg), short swings, the body sways
    A, S = 14, 12
    clip(rig, 'move', {
        1: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (S, 0, 0), 'thigh.R': (-S, 0, 0), 'chest': (0, 0, 3)},
        9: {'forearm.R': (-18, 0, 0), 'hand.R': (10, 0, 0), 'shin.L': (-16, 0, 0)},
        17: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-S, 0, 0), 'thigh.R': (S, 0, 0), 'chest': (0, 0, -3)},
        25: {'forearm.L': (-18, 0, 0), 'hand.L': (10, 0, 0), 'shin.R': (-16, 0, 0)},
        33: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (S, 0, 0), 'thigh.R': (-S, 0, 0), 'chest': (0, 0, 3)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0, 0.02)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0, 0.02)},
             33: {'hips': (0, 0, 0)}})
    # attack: the chest rears back, the right arm swings up and forward, then slams down
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (-8, 0, 0), 'upperarm.R': (55, 0, 0), 'forearm.R': (25, 0, 0), 'head': (-6, 0, 0)},   # s4 r2: +X swings forward (roll auto)
        18: {'chest': (6, 0, 0), 'upperarm.R': (-12, 0, 0), 'forearm.R': (5, 0, 0), 'head': (6, 0, 0)},
        24: {'chest': (3, 0, 0), 'upperarm.R': (-5, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
