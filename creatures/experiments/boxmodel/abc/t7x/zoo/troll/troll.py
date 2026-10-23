import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
sys.path.insert(0, HERE)
import parts as PT

# troll (hunched biped), t7 hand box-model. ONE spine loft of 14-vertex half rings runs crotch -> crown. The torso
# rings lie flat; from the shoulder line up the rings TILT (back seam high on the hump, front seam low on the throat)
# so the loft bends forward over the hump into the low, jutting head. Legs are 5-face regions of the crotch-hip
# underside, arms 2 x 4-face regions of the chest side (chest -> shoulder -> trapezius), ears 2-face regions of the
# skull side, the big nose a 2-face region of the face front (its seam walls removed: the mirror closes it).
# Coordinates from blueprint.json (refs.py, height 2.2 m; the sheet's plan view is not used).
# Identity cue (troll, not ogre): the hunch - the head hangs FORWARD and LOW in front of a trapezius hump nearly
# as high as the crown; a huge drooping nose; very long arms whose hands hang below the knees; short bowed legs on
# big flat feet; no tusks, no strap.
META = dict(creature='troll', model='opus', stage1_tris=(1500, 3600), total_tris=(2800, 5600),
            closeups=[('head', (0.0, -0.40, 1.88), 0.34, 'hero'),
                      ('shoulder', (0.58, 0.20, 1.45), 0.36, 'hero'),
                      ('hand', (0.90, 0.02, 0.50), 0.26, 'hero'),
                      ('foot', (0.41, 0.10, 0.10), 0.36, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.22, 0.82), spine=(0.0, 0.20, 1.10), chest=(0.0, 0.20, 1.40), neck=(0.0, 0.14, 1.66),
    head=(0.0, -0.14, 1.82), top=(0.0, -0.27, 2.19),
    ear=(0.17, -0.16, 2.04), eartip=(0.357, -0.119, 2.113),
    shoulder=(0.60, 0.19, 1.45), elbow=(0.75, 0.06, 1.01), wrist=(0.88, -0.05, 0.68), hand=(0.89, -0.03, 0.34),
    hipL=(0.27, 0.24, 0.72), knee=(0.36, 0.27, 0.45), ankle=(0.40, 0.31, 0.15), toe=(0.41, -0.18, 0.04),
)

NV = 14     # vertices per half ring (front seam -> back seam): 13 faces per span


def prof(e=0.85, w=0.0, back=0.0, n=NV):
    """Half-ring profile, front seam -> back seam: (x as a share of W, fh: +1 front .. -1 back).
    e: roundness (lower = boxier); w > 0 moves the widest point forward; back > 0 widens the back half (traps)."""
    out = []
    for i in range(n):
        t = math.pi * i / (n - 1)
        c = math.cos(t)
        fx = 0.0 if i in (0, n - 1) else math.sin(t) ** e * (1.0 + back * (-c))
        out.append((round(fx, 4), round(c + w * (1 - c * c), 4)))
    return out


BODY = prof(1.0, 0.0)
HIP = prof(0.9, 0.05)
TRAP = prof(0.95, -0.15, 0.35)
TRAP2 = prof(0.9, -0.10, 0.12)      # the trapezius slope ring: round, its widest at the side (no back-heavy shelf)
NECK = prof(0.85, -0.10, 0.45)
JAW = prof(0.75, 0.10)
HEAD = prof(1.0, 0.0)


def tb(nm, F, B, W, p):
    """A ring from its front and back seam points (y, z), half width W at the chord's middle."""
    return (nm, tuple(F), tuple(B), W, p)


# the spine loft, crotch -> crown: (name, front seam (y, z), back seam (y, z), W, profile)
SECS = [
    tb('R0', (0.10, 0.60), (0.34, 0.61), 0.09, HIP),        # crotch
    tb('R1', (-0.06, 0.72), (0.48, 0.72), 0.40, HIP),       # groin / buttock crease
    tb('R2', (-0.17, 0.86), (0.56, 0.86), 0.47, HIP),       # hips
    tb('R3', (-0.222, 0.98), (0.562, 0.99), 0.462, BODY),   # low belly   (smoothed: no rib bands)
    tb('R4', (-0.246, 1.09), (0.556, 1.10), 0.45, BODY),    # belly
    tb('R5', (-0.252, 1.20), (0.551, 1.21), 0.44, BODY),    # waist / belly top
    tb('R6', (-0.246, 1.30), (0.556, 1.31), 0.448, BODY),   # ribs
    tb('C0', (-0.24, 1.40), (0.572, 1.40), 0.53, BODY),     # chest (pecs): the chest widens up and out ...
    tb('C1', (-0.237, 1.48), (0.59, 1.50), 0.62, BODY),     # ... (armpit -> deltoid) ...
    tb('C2', (-0.215, 1.545), (0.585, 1.63), 0.645, BODY),   # ... into the deltoid line: the torso's WIDEST ring (owner fix)
    tb('T1', (-0.20, 1.585), (0.53, 1.77), 0.58, TRAP2),     # trapezius: a rounded mass sloping from the neck to the deltoid
    tb('T2', (-0.225, 1.60), (0.44, 1.88), 0.45, TRAP),     # hump top / neck base
    tb('N0', (-0.25, 1.595), (0.33, 1.98), 0.31, NECK),     # neck: narrow throat in front, trapezius behind
    tb('H0u', (-0.34, 1.585), (0.20, 2.05), 0.195, JAW),     # jaw line (the jaw underside, ahead of the throat)
    tb('H0', (-0.46, 1.615), (0.09, 2.10), 0.185, JAW),     # chin
    tb('H1', (-0.475, 1.72), (0.0, 2.13), 0.20, HEAD),      # mouth
    tb('H2', (-0.48, 1.80), (-0.06, 2.16), 0.215, HEAD),    # upper lip / nose base
    tb('H3', (-0.47, 1.92), (-0.12, 2.19), 0.21, HEAD),     # cheek / eye / nose root
    tb('H4', (-0.485, 2.03), (-0.17, 2.205), 0.175, HEAD),  # brow
    tb('H5', (-0.42, 2.13), (-0.21, 2.212), 0.125, HEAD),   # forehead
    tb('H6', (-0.33, 2.19), (-0.24, 2.215), 0.06, HEAD),    # crown
]


def sec_pts(F, B, W, p):
    F, B = Vector((0.0,) + tuple(F)), Vector((0.0,) + tuple(B))
    m, u = (F + B) / 2, (B - F) / 2
    return [(fx * W, (m - u * fh).y, (m - u * fh).z) for fx, fh in p]


def P(nm):
    for (n, F, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(F, B, W, p)]


# limb sections: (centre xyz, rx, ry[, dz]); dz < 0 lifts the outer side
LEG = [((0.305, 0.245, 0.58), 0.195, 0.235, -0.08),    # thigh: under the hug ring, outer side up toward the hip
       ((0.32, 0.255, 0.51), 0.185, 0.215, -0.02),
       ((0.35, 0.265, 0.45), 0.16, 0.19), ((0.365, 0.27, 0.40), 0.152, 0.18),     # knee
       ((0.38, 0.285, 0.33), 0.155, 0.18), ((0.39, 0.30, 0.25), 0.14, 0.165),     # calf
       ((0.40, 0.31, 0.17), 0.12, 0.145),                                         # ankle
       ((0.405, 0.24, 0.11), 0.19, 0.25), ((0.41, 0.14, 0.06), 0.235, 0.34), ((0.41, 0.13, 0.0), 0.235, 0.35)]
# arm (owner fix, minotaur method): the deltoid is the torso's own widest ring (C2); the arm grows from a 2 x 3 face
# region right under it (C0 -> C1 -> C2, columns 5-7), its first ring the root loop pushed out unshrunk, then these
# rings (centre, rx lateral, ry front-back). Side reference: the arm hangs FORWARD (elbow y 0.07, wrist -0.05).
ARM_C = [(0.645, 0.19, 1.32), (0.675, 0.16, 1.24), (0.70, 0.12, 1.16), (0.74, 0.07, 1.04), (0.77, 0.05, 0.97),
         (0.82, 0.02, 0.87), (0.86, -0.02, 0.77), (0.88, -0.05, 0.68)]
ARM_R = [(0.15, 0.21), (0.15, 0.20), (0.145, 0.19), (0.13, 0.17), (0.135, 0.17), (0.15, 0.18), (0.135, 0.16),
         (0.10, 0.115)]                        # deltoid/upper arm, elbow, forearm swell (massive), wrist
# density (r40): the 10-vertex arm rings cost 72 tris against the old 14-vertex arm, so two straight in-between rings
# (pointwise lerp: their faces stay co-planar) go where the outline bends: upper arm -> elbow, and the wrist taper
ARM_C.insert(3, tuple((Vector(ARM_C[2]) + Vector(ARM_C[3])) / 2)); ARM_R.insert(3, tuple((Vector(ARM_R[2]) + Vector(ARM_R[3])) / 2))
ARM_C.insert(-1, tuple((Vector(ARM_C[-2]) + Vector(ARM_C[-1])) / 2)); ARM_R.insert(-1, tuple((Vector(ARM_R[-2]) + Vector(ARM_R[-1])) / 2))
ARM_ELBOW = 4                                  # frame index of the elbow ring (ring 4 -> 5 carries the elbow loop)
ARM_SPAN, ARM_COLS = 'C0', (5, 6, 7)


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
    nrm = e1.cross(e2).normalized()
    if nrm.x < 0:
        nrm = -nrm
    return roles, (cen, nrm)


def grow_frames(bm, faces, roles, frames):
    """Extrude a (dissolved, one-face) root region frame by frame; a dict frame is a hug ring: the root loop
    itself pushed `out` along the region normal and scaled k about its centre."""
    for fr in frames:
        keyed = [(o.co.copy(), ab) for o, ab in roles.items()]
        r = extrude(bm, faces)
        new = {v: min(keyed, key=lambda q: (q[0] - v.co).length)[1] for v in r['verts']}
        if isinstance(fr, dict):
            for v in new:
                v.co = fr['c'] + (v.co - fr['c']) * fr['k'] + fr['n'] * fr['out']
        else:
            for v, ab in new.items():
                v.co = corner(fr, ab)
        faces, roles = r['faces'], new
    return faces, roles


def tilt(secs, first):
    """Each ring perpendicular to the limb's path in the y-z plane: (centre, rx, ry, dz, ty), z -= ty * b * ry."""
    cs = [Vector(first)] + [Vector(s_[0]) for s_ in secs]
    out = []
    for i, s_ in enumerate(secs):
        d = cs[min(i + 2, len(cs) - 1)] - cs[i]
        ty = d.y / d.z if abs(d.z) > 1e-6 else 0.0
        out.append((s_[0], s_[1], s_[2], s_[3] if len(s_) > 3 else 0.0, 0.0 if i == 0 else max(-0.8, min(0.8, ty))))   # the cap ring stays level
    return out
LEG_SPAN, LEG_J0, LEG_NF = 'R0', 4, 5
NOSE_SPAN = 'H2'
NOSE = [((-0.53, 1.99), (-0.52, 1.79), 0.065), ((-0.57, 1.95), (-0.56, 1.765), 0.085),
        ((-0.61, 1.91), (-0.595, 1.76), 0.10), ((-0.635, 1.87), (-0.625, 1.775), 0.085),
        ((-0.648, 1.84), (-0.642, 1.80), 0.045)]   # (top, bottom (y, z), half width): the sheet's potato nose
EAR_TIP = Vector(J['eartip'])
EAR = [(0.38, 0.064, 0.03), (0.85, 0.055, 0.018), (1.0, 0.012, 0.008)]   # (t, wide, thin): a cone base inside the 2-face root, then a broad pointed leaf


def kx(b, corner=0.55):
    return corner if abs(b) > 0.99 else math.sqrt(max(0.0, 1.0 - 0.75 * b * b))


def apos(sec, a, b):
    """Arm ring point: rounder corners than the leg (a deltoid and a forearm are round, a shin is boxy)."""
    c, rx, ry = sec[0], sec[1], sec[2]
    dz = sec[3] if len(sec) > 3 else 0.0
    ty = sec[4] if len(sec) > 4 else 0.0
    return (c[0] + a * rx * kx(b, 0.78), c[1] + b * ry * (0.92 if abs(a) > 0.99 else 1.0), c[2] - a * dz - ty * b * ry)


def lpos(sec, a, b):
    """Limb ring point: a -1 inner .. +1 outer, b -1 front .. +1 back."""
    c, rx, ry = sec[0], sec[1], sec[2]
    dz = sec[3] if len(sec) > 3 else 0.0
    ty = sec[4] if len(sec) > 4 else 0.0
    return (c[0] + a * rx * kx(b), c[1] + b * ry, c[2] - a * dz - ty * b * ry)


def grow(bm, faces, roles, secs, pos, hug=None, mid=False):
    """hug = (offset, shrink): a first ring that is the root loop itself pushed `offset` out along the region's
    normal and shrunk toward its centre - the broad transition ring that blends the limb into the torso."""
    """Extrude a face region section by section; each new vertex keeps the role of the vertex it came from.
    A multi-face root region is first dissolved into one face (its inner vertices go), so each section is one ring."""
    if len(faces) > 1:
        inner = [v for f in faces for v in f.verts if all(g in faces for g in v.link_faces)]
        faces = bmesh.ops.dissolve_faces(bm, faces=list(faces), use_verts=False)['region']
        loose = [v for v in set(inner) if v.is_valid and not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    if hug is not None:
        bv = sorted({v for f in faces for v in f.verts}, key=lambda v: tuple(v.co))
        cen = sum((v.co for v in bv), Vector()) / len(bv)
        nrm = sum((f.normal * f.calc_area() for f in faces), Vector()).normalized()
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
            v.co = cen + (v.co - cen) * hug[1] + nrm * hug[0]
        faces, roles = r['faces'], new
        if mid:                                 # a ring halfway from the hug ring to the first section: no sheared quads
            r = extrude(bm, faces)
            new = {}
            for v in r['verts']:
                ov = min(roles, key=lambda o: (o.co - v.co).length)
                new[v] = roles[ov]
                v.co = v.co.lerp(Vector(pos(secs[0], *new[v])), 0.5)
            faces, roles = r['faces'], new
    for si, sec in enumerate(secs):
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, ab in new.items():
            q = Vector(pos(sec, *ab))
            v.co = q
        faces, roles = r['faces'], new
    return faces, roles, r


def root_roles(verts, e1, e2):
    """Roles that keep the root loop's own layout (its offsets on e1 / e2, scaled to +-1): the leaf rings repeat
    the root's shape, so no ring is sheared against the next (even-angle roles made thin triangles)."""
    cen = sum((v.co for v in verts), Vector()) / len(verts)
    pr = [((v.co - cen).dot(e1), (v.co - cen).dot(e2)) for v in verts]
    s1, s2 = max(abs(a) for a, _ in pr) or 1, max(abs(b) for _, b in pr) or 1
    # the leaf rim stays thick: no root vertex closer than 0.85 to the leaf's mid plane (thin rim faces = seam strips)
    return {v: (a / s1, math.copysign(max(abs(b / s2), 0.85), b)) for v, (a, b) in zip(verts, pr)}


def ear_frame(root):
    d = (EAR_TIP - root).normalized()
    e1 = Vector((0, -1, 0.15)); e1 = (e1 - d * e1.dot(d)).normalized()     # broad side faces forward
    e2 = d.cross(e1).normalized()
    return d, e1, e2


def root_patch(rings, spans, i0, nspan, j0, nf):
    """A limb root region: nspan spans (rings i0 .. i0+nspan) x nf faces (columns j0 .. j0+nf-1). Roles: the lowest
    ring -> inner side (a = -1), the highest -> outer side (a = +1), the rings between -> their two end vertices on
    the front / back edge (b = -1 / +1) at a evenly between."""
    roles = {}
    for c in range(nf + 1):
        b = -1 + 2.0 * c / nf
        roles[rings[i0][j0 + c]] = (-1, b); roles[rings[i0 + nspan][j0 + c]] = (1, b)
    for m in range(1, nspan):
        a = -1 + 2.0 * m / nspan
        roles[rings[i0 + m][j0]] = (a, -1); roles[rings[i0 + m][j0 + nf]] = (a, 1)
    faces = [spans[i0 + m][j0 + c] for m in range(nspan) for c in range(nf)]
    return faces, roles




def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(F, B, W, p)) for (nm, F, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0])
    top = cap(bm, rings[-1])
    recalc_normals(bm)
    pk = bmesh.ops.poke(bm, faces=[top])                        # the crown: a low dome, not a flat lid
    for v in pk['verts']:
        v.co.z += 0.005

    # legs: a 2-span x 5-face region (crotch -> hip underside -> hip side): the thigh rises out of the flank
    faces, roles = root_patch(rings, spans, idx[LEG_SPAN], 2, LEG_J0, LEG_NF)
    grow(bm, faces, roles, LEG, lpos)

    # arms (owner fix, minotaur method): a 2 x 3 face region of the chest side right under the deltoid line (C0 -> C1
    # -> C2): its top edge IS the torso's widest ring, so the arm's outer wall carries the deltoid down (no shelf).
    # The region is dissolved to one face (its 2 inner verts go); the first ring is the root loop pushed out unshrunk.
    i = idx[ARM_SPAN]
    faces = [spans[i + m][c] for m in range(2) for c in ARM_COLS]
    roles, (cen, nrm) = region_roles(faces, rings[i], rings[i + 2])
    inner = [v for f in faces for v in f.verts if all(g in faces for g in v.link_faces)]
    faces = bmesh.ops.dissolve_faces(bm, faces=faces, use_verts=False)['region']
    loose = [v for v in inner if v.is_valid and not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    roles = {v: ab for v, ab in roles.items() if v.is_valid}
    grow_frames(bm, faces, roles, [dict(c=cen, n=nrm, out=0.045, k=1.0)] + frame_chain(ARM_C, ARM_R))

    # ears: 2 faces of the skull side, out to a pointed leaf
    root = Vector(J['ear'])
    f0 = min((f for f in bm.faces if f.normal.x > 0.35), key=lambda f: (f.calc_center_median() - root).length)
    nb = [g for e in f0.edges for g in e.link_faces if g is not f0 and g.normal.x > 0.3]
    f1 = max(nb, key=lambda g: abs((g.calc_center_median() - f0.calc_center_median()).normalized().y))   # the neighbour along y (ear width)
    ef = [f0, f1]
    bv = sorted({v for f in ef for v in f.verts}, key=lambda v: tuple(v.co))   # sorted: a set's order changed c0 in the last bits
    c0 = sum((v.co for v in bv), Vector()) / len(bv)
    d, e1, e2 = ear_frame(c0)
    roles = root_roles(bv, e1, e2)
    nrm0 = sum((f.normal * f.calc_area() for f in ef), Vector()).normalized()
    P1 = c0 + nrm0 * 0.5 * (EAR_TIP - c0).length          # the leaf leaves the skull along the root's normal, then
    bez = lambda t: c0 * (1 - t) ** 2 + P1 * 2 * t * (1 - t) + EAR_TIP * t * t   # turns to the tip (no overhang)
    secs = [(bez(t), wd, th) for t, wd, th in EAR]
    grow(bm, ef, roles, secs, lambda s, a, b: s[0] + e1 * a * s[1] + e2 * b * s[2], hug=(0.045, 0.74))   # hug: the root loop itself, out 4.5 cm and drawn in: a short cone base

    # nose: the two seam-column faces of the nose-base -> eye -> brow spans, out and down to a bulb
    i = idx[NOSE_SPAN]
    A_, B_, C_ = rings[i], rings[i + 1], rings[i + 2]
    roles = {A_[0]: (0, -1), B_[0]: (0, 0), C_[0]: (0, 1), A_[1]: (1, -1), B_[1]: (1, 0), C_[1]: (1, 1)}
    faces = [spans[i][0], spans[i + 1][0]]
    for top, bot, rx in NOSE:
        top, bot = Vector((0.0,) + top), Vector((0.0,) + bot)
        c, hh, upv = (top + bot) / 2, (top - bot).length / 2, (top - bot).normalized()
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (ax, bh) in new.items():
            v.co = c + Vector((ax * rx * (0.45 if bh > 0.99 else 0.8 if bh < -0.99 else 1.0), 0, 0)) + upv * bh * hh   # narrow bridge
        seam_walls = [g for g in r['sides'] if all(abs(w.co.x) < 1e-6 for w in g.verts)]
        bmesh.ops.delete(bm, geom=seam_walls, context='FACES')
        faces, roles = r['faces'], new
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
def face_c(nm_lo, nm_up, j):
    A, B_ = P(nm_lo), P(nm_up)
    return (A[j] + A[j + 1] + B_[j] + B_[j + 1]) / 4


EYE_SPAN, EYE_COL = ('H3', 'H4'), 2


def keep_eye(c):
    e = face_c(*EYE_SPAN, EYE_COL)
    return abs(abs(c.x) - e.x) < 0.04 and abs(c.y - e.y) < 0.04 and abs(c.z - e.z) < 0.06


def stage2(k, body):
    """The eye socket (an inset in the eye face under the brow, its floor pushed in), a brow ridge over it, the
    elbow and knee loops for the bend."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    tl, af = LEG, frame_chain(ARM_C, ARM_R)
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)

    def limb_edge(frames, i):
        va = vert_near(bm, corner(frames[i], (1, 0)))
        tb_ = corner(frames[i + 1], (1, 0))
        return min(va.link_edges, key=lambda e: (e.other_vert(va).co - tb_).length)
    cuts = [('elbow loop: the elbow bend', lambda: limb_edge(af, ARM_ELBOW)),
            ('knee loop: the knee bend', lambda: edge_near(bm, mid(lpos(tl[2], 1, -0.2), lpos(tl[3], 1, -0.2))))]
    for why, fe in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, fe(), t=0.5)
    ec = face_c(*EYE_SPAN, EYE_COL)
    f = face_near(bm, ec)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face under the brow, its floor pushed in'):
        inner = inset(bm, [f], 0.22, 0.0)
    move(list(inner[0].verts), -fn * 0.006)          # review fix 2: a shallow socket (14 mm read as a dark slot)
    H4 = P('H4')
    move([vert_near(bm, H4[j]) for j in (1, 2, 3, 4)], (0.0, -0.010, 0.004))    # brow ridge forward over the eye (review fix 2: 16 -> 10 mm)
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'skin': '#a2a283', 'belly': '#b9b493', 'nose': '#c4876f', 'leather': '#6c4a36', 'rope': '#9c7a52',
       'nail': '#d8cba8', 'eye': '#4a3420', 'pupil': '#17120e'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if x < 0.11 and y < -0.50 and 1.74 < z < 2.0:
        return 'nose'
    if 0.98 < z < 1.42 and y < 0.0 and math.degrees(math.atan2(x, 0.16 - y)) < 40.0:   # chest-belly: front columns 0-2
        return 'belly'
    return 'skin'


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


def band(tree, centre, e1, e2, half_w, n_seg, sink=(0.012, -0.004), out=0.026):
    """The rope belt: a closed strap round the body in the plane (e1, e2) through centre; per angle two rays (its two
    edges) find the skin; the inner face is sunk, the outer face evened out over neighbours (no dive into creases)."""
    e1, e2 = Vector(e1).normalized(), Vector(e2).normalized()
    nrm = e1.cross(e2).normalized()
    bm = bmesh.new()
    ds, ts = [], []
    for s_ in range(n_seg):
        t = 2 * math.pi * s_ / n_seg
        d = e1 * math.cos(t) + e2 * math.sin(t)
        tt = []
        for side in (-1, 1):
            o = Vector(centre) + nrm * side * half_w
            loc, _fn = hit(tree, o, d)
            tt.append((loc - o).length if loc is not None else 0.4)
        ds.append(d); ts.append(tt)
    tout = [[max(t) for _ in (0, 1)] for t in ts]
    tout = [[max(tout[i][j], 0.5 * (tout[i - 1][j] + tout[(i + 1) % n_seg][j])) for j in (0, 1)] for i in range(n_seg)]
    rows = []
    for i in range(n_seg):
        d = ds[i]
        row = []
        for j, side in enumerate((-1, 1)):
            o = Vector(centre) + nrm * side * half_w
            row += [o + d * (ts[i][j] - sink[j]), o + d * (tout[i][j] + out)]   # lower edge sunk, upper edge proud: one crossing
        rows.append([bm.verts.new(p) for p in (row[0], row[1], row[3], row[2])])
    for i in range(n_seg):
        a, b = rows[i], rows[(i + 1) % n_seg]
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    return bm


def flap(tree, xs, z_top, hems, front, th=0.018):
    """A loincloth panel (x >= 0 half, mirrored): rooted under the belt, hanging clear of the belly and thighs to
    a jagged hem. Each column follows the skin (ray from outside) at the top, then hangs straight. A closed slab th
    thick (membrane check: >= 9 mm)."""
    sgn = -1.0 if front else 1.0
    rows_z = [z_top, z_top - 0.07, z_top - 0.17, z_top - 0.29, None]
    cols = []
    for x, zh in zip(xs, hems):
        col = []
        for r, z in enumerate(rows_z):
            z = zh if z is None else max(z, zh + 0.02 * (len(rows_z) - 1 - r))
            loc, _n = hit(tree, (max(x, 0.004), sgn * 1.5, z), (0, -sgn, 0))
            y = loc.y if loc is not None else sgn * 0.2
            y = y - sgn * 0.03 if r == 0 else y + sgn * 0.022          # top row sunk 3 cm, the rest stand off
            col.append(Vector((x, y, z)))
        cols.append(col)
    for c in cols:                              # each column hangs at the outermost depth of its rows above
        for r in range(2, len(rows_z)):
            c[r].y = (min if front else max)(c[r].y, c[r - 1].y)
    bm = bmesh.new()
    O = [[bm.verts.new(p) for p in c] for c in cols]
    I = [[bm.verts.new(p + Vector((0, -sgn * th, 0))) for p in c] for c in cols]
    n, m = len(cols), len(rows_z)
    for i in range(n - 1):
        for r in range(m - 1):
            bm.faces.new([O[i][r], O[i + 1][r], O[i + 1][r + 1], O[i][r + 1]])
            bm.faces.new([I[i][r + 1], I[i + 1][r + 1], I[i + 1][r], I[i][r]])
        bm.faces.new([O[i + 1][m - 1], O[i][m - 1], I[i][m - 1], I[i + 1][m - 1]])    # hem
        bm.faces.new([O[i][0], O[i + 1][0], I[i + 1][0], I[i][0]])                    # top (in the body)
    for r in range(m - 1):
        bm.faces.new([O[-1][r + 1], O[-1][r], I[-1][r], I[-1][r + 1]])                # outer side
    recalc_normals(bm)
    return bm


def wrist_ring(body):
    bm = edit(body)
    c = Vector(ARM_C[-1])
    f = min((f for f in bm.faces if len(f.verts) >= 10), key=lambda f: (f.calc_center_median() - c).length)
    pts = [v.co.copy() for v in f.verts]
    bm.free()
    return pts


def toes(bm, tree, side):
    (cx, cy, _), rx, ry = LEG[-1][:3]
    for o, w, L, hgt in ((-0.136, 0.042, 0.066, 0.088),   # detail pass r34: big toe apart from toe 2 (r33: the overlap read as one 18 cm stick), taller, shorter
                         (-0.055, 0.034, 0.068, 0.062), (0.0, 0.031, 0.062, 0.056),
                         (0.05, 0.029, 0.055, 0.05), (0.095, 0.027, 0.046, 0.044)):
        x = cx + o
        loc, _n = hit(tree, (x, -1.0, 0.03), (0, 1, 0))
        if loc is None:
            continue
        h = Vector((x, loc.y, 0.0))
        rows = [[h + Vector((-w, 0.03, 0.007)), h + Vector((w, 0.03, 0.007)), h + Vector((w, 0.03, hgt)), h + Vector((-w, 0.03, hgt))],
                [h + Vector((-w, -L * 0.5, 0.006)), h + Vector((w, -L * 0.5, 0.006)), h + Vector((w * 0.92, -L * 0.5, hgt * 0.85)), h + Vector((-w * 0.92, -L * 0.5, hgt * 0.85))],
                [h + Vector((-w * 0.8, -L, 0.006)), h + Vector((w * 0.8, -L, 0.006)), h + Vector((w * 0.7, -L, hgt * 0.55)), h + Vector((-w * 0.7, -L, hgt * 0.55))]]
        if side < 0:
            rows = [[Vector((-p.x, p.y, p.z)) for p in reversed(r)] for r in rows]
        box_chain(bm, rows)


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('skin', 'belly', 'nose')}, body_rule)
    tree = full_bvh(body)
    pieces = []
    # eyes: small round lenses in the sockets, facing forward-out
    bm = edit(body)
    ec = face_c(*EYE_SPAN, EYE_COL)
    f = min((g for g in bm.faces if len(g.verts) == 4), key=lambda g: (g.calc_center_median() - ec).length)
    c0, n0 = f.calc_center_median(), f.normal.copy()
    bm.free()
    if n0.y > 0:
        n0 = -n0
    n = (n0 + Vector((1.1, 0, 0.05))).normalized()        # the lens looks forward-out (side view >= 0.40)
    bm = bmesh.new()
    lens(bm, c0 + n * 0.006, n, 0.026, 0.012)
    eye = object_from_bm('eye', bm)
    tip = c0 + n * 0.018
    paint(eye, {'eye': PAL['eye'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if (Vector((abs(c_.x), c_.y, c_.z)) - tip).length < 0.011 else 'eye')
    pieces.append(eye)
    # hands: the parts-library four-finger hand on each wrist ring
    wr = wrist_ring(body)
    for side in (1, -1):
        o = Vector((side * 0.885, -0.052, 0.66))
        hand = PT.hand_three_finger(o, width=0.27, forward=(side * 0.04, 0.03, -1), up=(side * 0.75, -0.66, 0), side=side,
                                    fingers=4, curl=0.38, finger_len=0.82, thumb_curl=0.25, knuckle=0.12,
                                    wrist=(0.16, 0.10), open_root=True, name=f'hand_{"L" if side > 0 else "R"}')
        ring_pts = wr if side > 0 else [Vector((-p.x, p.y, p.z)) for p in reversed(wr)]
        k.bridge_part(hand, ring_pts, reason='parts-library 4-finger hand on the wrist ring')
        paint(hand, {'skin': PAL['skin']}, lambda c_, n_, i: 'skin')
        pieces.append(hand)
    # toes: five per foot, nails on their tips
    for side in (1, -1):
        bm = bmesh.new()
        toes(bm, tree, side)
        to = object_from_bm(f'toes_{"L" if side > 0 else "R"}', bm, mirror=False)
        cy = LEG[-1][0][1] - LEG[-1][2]
        paint(to, {'skin': PAL['skin'], 'nail': PAL['nail']},
              lambda c_, n_, i: 'nail' if c_.y < cy - 0.045 and n_.z > 0.3 else 'skin')
        pieces.append(to)
    # loincloth: a rope belt round the hips and a front and a back leather flap with jagged hems
    belt = object_from_bm('belt', band(tree, (0.0, 0.17, 0.99), (1, 0, 0), (0, 1, 0.12), 0.022, 36), mirror=False)
    paint(belt, {'rope': PAL['rope']}, lambda c_, n_, i: 'rope')
    lf = object_from_bm('flap_front', flap(tree, [0.0, 0.1, 0.2, 0.3, 0.4], 0.925, [0.40, 0.52, 0.47, 0.57, 0.60], True))
    lb = object_from_bm('flap_back', flap(tree, [0.0, 0.1, 0.2, 0.3, 0.42], 0.995, [0.50, 0.60, 0.54, 0.63, 0.66], False))
    for o_ in (lf, lb):
        paint(o_, {'leather': PAL['leather']}, lambda c_, n_, i: 'leather')
    pieces += [belt, lf, lb]
    pieces += detail_pass(body, tree)
    return pieces


def detail_pass(body, tree):
    """Tier-3 detail pass (2026-10-23, zoo/detail_audit.md troll list): chunky seated pieces in the existing 8
    colours (the colour gate is full), box-model geometry only."""
    import detail_pieces as D
    out = []

    def piece(name, bm, col, mirror=True, rule=None):
        ob = object_from_bm(name, bm, mirror=mirror)
        cols = col if isinstance(col, dict) else {col: PAL[col]}     # palette KEY: materials are shared by name
        paint(ob, cols, rule or (lambda c_, n_, i: next(iter(cols))))
        out.append(ob)
        return ob
    sk = 'skin'
    # 1. brow ridge: a heavy arc over each eye (front view)
    e = face_c(*EYE_SPAN, EYE_COL)
    pts = [(e.x + 0.05 * t, -2.0, e.z + 0.055 - 0.018 * t * t) for t in (-0.9, -0.45, 0.0, 0.45, 0.9)]
    bm = bmesh.new()
    D.band(bm, D.stations_from_hits(D.path_stations(tree, pts, (0, 1, 0)), side_hint=(0, 0, 1)), 0.045, 0.028,
           prof=D.FOLD)
    piece('brow', bm, sk)
    # 2. nostrils: a flared mound under each side of the nose bulb with a dark nostril cap
    h_ = D.cast_in(tree, (0.052, -0.585, 1.3), (0, 0, 1))
    nn = (h_[1] + Vector((0.25, -0.45, 0))).normalized()
    bm = bmesh.new()
    D.knob(bm, h_[0], nn, 0.03, 0.018, top=0.6)
    piece('nostril', bm, {'nose': PAL['nose'], 'pupil': PAL['pupil']},
          rule=lambda c_, n_, i: 'pupil' if n_.dot(nn) > 0.9 else 'nose')
    # 3. kneecaps
    h_ = D.cast_in(tree, (0.355, -2.0, 0.44), (0, 1, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.075, 0.035, sides=7, sq=(1.15, 1.0), top=0.5)
    piece('kneecap', bm, sk)
    # 4. warts: three chunky bumps on the shoulder hump / trapezius
    bm = bmesh.new()
    for (x, y, r) in ((0.40, 0.26, 0.04), (0.52, 0.12, 0.033), (0.24, 0.36, 0.036)):
        h_ = D.cast_in(tree, (x, y, 3.0), (0, 0, -1))
        D.knob(bm, h_[0], h_[1], r, 0.8 * r, sides=6, top=0.5)
    piece('wart', bm, sk)
    # 5. navel: a belly-coloured rim with a dark centre (one midline piece)
    h_ = D.cast_in(tree, (0.0, -2.0, 1.105), (0, 1, 0))
    bm = bmesh.new()
    D.knob(bm, h_[0], h_[1], 0.04, 0.014, sides=6, top=0.55)
    nv = h_[1]
    piece('navel', bm, {'belly': PAL['belly'], 'leather': PAL['leather']}, mirror=False,
          rule=lambda c_, n_, i: 'leather' if n_.dot(nv) > 0.9 else 'belly')
    # 7. mouth line: a dark lip line across the mouth (open on the seam)
    pts = [(x, -2.0, 1.752 - 0.012 * (x / 0.11) ** 2) for x in (0.0, 0.03, 0.06, 0.085, 0.11)]
    bm = bmesh.new()
    D.band(bm, D.stations_from_hits(D.path_stations(tree, pts, (0, 1, 0)), side_hint=(0, 0, 1)), 0.026, 0.016,
           prof=D.ROUND, open_start=True)
    piece('mouth', bm, 'pupil')
    return out


# ---------------------------------------------------------------- stage 4
def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['top'], 'neck', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_hand'):
            bind(p, rig, bone='hand.L' if p.name.endswith('_L') else 'hand.R')
        else:
            bind(p, rig, body=body)
    # idle: slow heavy breathing, the head sways, the long arms swing a little
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, 4),
                                   'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0), 'ear.L': (0, 0, 6)},
                       24: {}, 36: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, -4),
                                    'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0)}, 48: {}})
    # move: a heavy lumbering walk; short leg swing, knee bend on the passing leg, long arm swing against the legs
    A, S = 10, 14
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 3)},
        9: {'shin.R': (-22, 0, 0), 'foot.R': (8, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0), 'spine': (0, 0, -3)},
        25: {'shin.L': (-22, 0, 0), 'foot.L': (8, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 3)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.025, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.025, 0)},
             33: {'hips': (0, 0, 0)}})
    # attack: the right arm rears up and back, then a downward clubbing swipe with a forward lean
    clip(rig, 'attack', {
        1: {},
        10: {'upperarm.R': (60, 0, 0), 'forearm.R': (40, 0, 0), 'chest': (-5, 0, 0), 'head': (-3, 0, 0)},
        18: {'upperarm.R': (-30, 0, 0), 'forearm.R': (10, 0, 0), 'chest': (10, 0, 0), 'spine': (4, 0, 0), 'head': (5, 0, 0)},
        24: {'upperarm.R': (-20, 0, 0), 'forearm.R': (8, 0, 0), 'chest': (6, 0, 0), 'spine': (2, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
