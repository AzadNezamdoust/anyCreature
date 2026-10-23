import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
from smooth_borders import smooth_borders
import parts as PT

# imp (small winged biped), t7 hand box-model. ONE spine loft of 14-vertex half rings runs crotch -> crown (the
# head rings tilt: front seam along the jaw underside and the face, back seam up the back of the skull). Legs are
# 2-span x 5-face regions of the crotch-hip underside, arms 2-span x 4-face regions of the chest side (chest ->
# shoulder line -> trapezius), ears 2-face regions of the skull side, the tail a 2-face region of the rump on the
# back seam (its seam wall removed: the mirror closes it) ending in a flat spade. Wings (closed slabs with spar
# ridges), horns, hands, claws and the lens eyes are stage-3 pieces.
# Coordinates from blueprint.json (refs.py, height 0.8 m; the sheet's plan view is not a true ortho, not used).
# Identity cue (imp, not goblin/gremlin): a big round head with two short dark horns and huge pointed ears on a
# small pot-bellied body, bat wings from the shoulder blades, a thin tail ending in a spade.
META = dict(creature='imp', model='opus', stage1_tris=(1500, 3600), total_tris=(2400, 5600),
            later={'wing': dict(chain=['wingroot', 'wingwrist', 'wingtip'], radius=0.09)},
            closeups=[('head', (0.0, -0.15, 0.60), 0.17, 'hero'),
                      ('shoulder', (0.12, -0.08, 0.38), 0.12, 'hero'),
                      ('wing', (0.17, 0.10, 0.42), 0.22, 'back34'),
                      ('foot', (0.07, -0.10, 0.06), 0.12, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, -0.09, 0.19), spine=(0.0, -0.09, 0.28), chest=(0.0, -0.09, 0.37), neck=(0.0, -0.09, 0.44),
    head=(0.0, -0.10, 0.49), top=(0.0, -0.13, 0.715),
    ear=(0.115, -0.075, 0.605), eartip=(0.245, 0.055, 0.672),
    shoulder=(0.115, -0.092, 0.395), elbow=(0.172, -0.088, 0.285), wrist=(0.195, -0.10, 0.19), hand=(0.2, -0.11, 0.13),
    hipL=(0.066, -0.095, 0.165), knee=(0.068, -0.11, 0.10), ankle=(0.071, -0.085, 0.04), toe=(0.075, -0.20, 0.01),
    tail0=(0.0, 0.012, 0.207), tail1=(0.0, 0.05, 0.193), tail2=(0.0, 0.12, 0.161), tail3=(0.0, 0.20, 0.152),
    tailtip=(0.0, 0.295, 0.182),
    wingroot=(0.05, -0.03, 0.42), wingwrist=(0.20, 0.09, 0.52), wingtip=(0.35, 0.30, 0.335),
)

NV = 14     # vertices per half ring (front seam -> back seam): 13 faces per span


def prof(e=0.85, w=0.0, back=0.0, n=NV):
    """Half-ring profile, front seam -> back seam: (x as a share of W, fh: +1 front .. -1 back).
    e: roundness (lower = boxier); w > 0 moves the widest point forward; back > 0 widens the back half."""
    out = []
    for i in range(n):
        t = math.pi * i / (n - 1)
        c = math.cos(t)
        fx = 0.0 if i in (0, n - 1) else math.sin(t) ** e * (1.0 + back * (-c))
        out.append((round(fx, 4), round(c + w * (1 - c * c), 4)))
    return out


BODY = prof(0.9, 0.0)
HIP = prof(0.85, 0.0)
TRAP = prof(0.9, -0.1, 0.15)
NECK = prof(0.85, -0.05)
JAW = prof(0.85, 0.0)
HEAD = prof(0.9, -0.05)
SNOUT = prof(1.05, -0.2)


def tb(nm, F, B, W, p):
    return (nm, tuple(F), tuple(B), W, p)


# the spine loft, crotch -> crown: (name, front seam (y, z), back seam (y, z), W, profile)
SECS = [
    tb('R0', (-0.135, 0.150), (-0.040, 0.152), 0.030, HIP),      # crotch
    tb('R1', (-0.170, 0.162), (-0.004, 0.160), 0.098, HIP),      # hip underside (a flat seat: the legs drop from it)
    tb('R2', (-0.190, 0.207), (0.012, 0.207), 0.104, HIP),       # hips / butt
    tb('R3', (-0.203, 0.262), (0.010, 0.262), 0.108, BODY),      # low belly
    tb('R4', (-0.205, 0.298), (0.003, 0.298), 0.107, BODY),      # belly (pot belly front)
    tb('R5', (-0.199, 0.332), (-0.004, 0.332), 0.102, BODY),     # waist
    tb('R6', (-0.190, 0.362), (-0.010, 0.362), 0.096, BODY),     # ribs
    tb('C0', (-0.181, 0.388), (-0.014, 0.390), 0.090, BODY),     # chest
    tb('C1', (-0.172, 0.412), (-0.018, 0.414), 0.086, BODY),     # shoulder line
    tb('C2', (-0.162, 0.432), (-0.026, 0.437), 0.076, TRAP),     # chest top / trapezius
    tb('N0', (-0.150, 0.447), (-0.038, 0.458), 0.062, NECK),     # neck
    tb('H0u', (-0.195, 0.463), (-0.033, 0.490), 0.058, JAW),     # jaw line (the jaw underside, ahead of the throat)
    tb('H0', (-0.243, 0.482), (-0.022, 0.525), 0.080, JAW),      # chin
    tb('H1', (-0.270, 0.506), (-0.016, 0.560), 0.103, SNOUT),    # mouth
    tb('H2', (-0.288, 0.536), (-0.013, 0.595), 0.120, SNOUT),    # nose
    tb('H3', (-0.272, 0.575), (-0.014, 0.626), 0.125, HEAD),     # eye / cheek
    tb('H4', (-0.258, 0.615), (-0.022, 0.653), 0.123, HEAD),     # brow
    tb('H5', (-0.240, 0.652), (-0.038, 0.678), 0.115, HEAD),     # forehead
    tb('H6', (-0.210, 0.684), (-0.060, 0.700), 0.095, HEAD),     # upper skull
    tb('H7', (-0.175, 0.706), (-0.090, 0.713), 0.058, HEAD),     # crown
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
LEG = [((0.063, -0.093, 0.125), 0.040, 0.062),          # thigh top, inside the hug ring
       ((0.065, -0.099, 0.112), 0.042, 0.064),
       ((0.068, -0.106, 0.098), 0.041, 0.060),              # knee
       ((0.069, -0.102, 0.080), 0.039, 0.056),
       ((0.070, -0.094, 0.060), 0.036, 0.050),              # ankle
       ((0.072, -0.100, 0.036), 0.050, 0.070),
       ((0.075, -0.115, 0.014), 0.058, 0.085), ((0.075, -0.115, 0.0), 0.058, 0.085)]   # foot: sole on the ground
ARM = [((0.126, -0.090, 0.384), 0.026, 0.029, -0.012),     # deltoid cap: outer side high, inner low (armpit)
       ((0.142, -0.089, 0.352), 0.025, 0.026, -0.006),
       ((0.154, -0.087, 0.318), 0.023, 0.024),
       ((0.165, -0.084, 0.292), 0.021, 0.023), ((0.172, -0.086, 0.268), 0.021, 0.023),   # elbow (a little back)
       ((0.181, -0.094, 0.236), 0.022, 0.024),              # forearm
       ((0.190, -0.104, 0.203), 0.017, 0.019)]              # wrist (forward of the elbow)


def tilt(secs, first):
    """Each ring perpendicular to the limb's path in the y-z plane: (centre, rx, ry, dz, ty), z -= ty * b * ry."""
    cs = [Vector(first)] + [Vector(s_[0]) for s_ in secs]
    out = []
    for i, s_ in enumerate(secs):
        d = cs[min(i + 2, len(cs) - 1)] - cs[i]
        ty = d.y / d.z if abs(d.z) > 1e-6 else 0.0
        out.append((s_[0], s_[1], s_[2], s_[3] if len(s_) > 3 else 0.0, 0.0 if i == 0 else max(-0.8, min(0.8, ty))))
    return out


LEG_SPAN, LEG_NS, LEG_J0, LEG_NF = 'R0', 1, 3, 7
LEG_HUG = (0.012, 0.92)     # first ring: the root loop pushed 1.2 cm along its normal, shrunk (walls lean in)
ARM_SPAN, ARM_J0, ARM_NF = 'C0', 5, 4
TAIL_SPAN = 'R1'
# tail: (centre (y, z), half width x, half height); the last five stations are the flat spade
TAIL = [((0.042, 0.188), 0.025, 0.019),      # first ring past the hug ring
        ((0.058, 0.186), 0.020, 0.019),
        ((0.086, 0.178), 0.015, 0.015),
        ((0.116, 0.164), 0.012, 0.012),
        ((0.146, 0.154), 0.0105, 0.0105),
        ((0.176, 0.150), 0.0095, 0.0095),
        ((0.198, 0.151), 0.009, 0.0095),     # spade neck
        ((0.207, 0.154), 0.010, 0.030),      # spade lobes
        ((0.222, 0.158), 0.010, 0.040),
        ((0.246, 0.165), 0.009, 0.031),
        ((0.271, 0.173), 0.007, 0.018),
        ((0.295, 0.182), 0.004, 0.005)]      # tip
EAR_TIP = Vector(J['eartip'])
EAR = [(0.22, 0.050, 0.016, 0.2), (0.38, 0.056, 0.022, 0.45), (0.55, 0.052, 0.018, 0.85), (0.72, 0.038, 0.012, 1.0),
       (0.88, 0.020, 0.007, 1.0), (1.0, 0.005, 0.004, 1.0)]   # (t, half width, half thickness, morph root -> leaf)
EAR_N = (0.30, -0.85, 0.43)


def kx(b, corner=0.55):
    return corner if abs(b) > 0.99 else math.sqrt(max(0.0, 1.0 - 0.75 * b * b))


def apos(sec, a, b):
    """Arm ring point: rounder corners than the leg."""
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


def grow(bm, faces, roles, secs, pos, rec=None, hug=None):
    """Extrude a face region section by section; each new vertex keeps the role of the vertex it came from.
    A multi-face root region is first dissolved into one face (its inner vertices go), so each section is one ring."""
    if len(faces) > 1:
        inner = [v for f in faces for v in f.verts if all(g in faces for g in v.link_faces)]
        faces = bmesh.ops.dissolve_faces(bm, faces=list(faces), use_verts=False)['region']
        loose = [v for v in set(inner) if v.is_valid and not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    r = None
    if rec is not None:
        rec.append([(v.co.copy(), ab) for v, ab in roles.items()])
    if hug is not None:                     # a first ring that is the root loop pushed out along its normal, shrunk
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
        if rec is not None:
            rec.append([(v.co.copy(), ab) for v, ab in roles.items()])
    for si, sec in enumerate(secs):
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, ab in new.items():
            v.co = Vector(pos(sec, *ab))
        faces, roles = r['faces'], new
        if rec is not None:
            rec.append([(v.co.copy(), ab) for v, ab in roles.items()])
    return faces, roles, r


def ellipse_roles(verts, e1, e2):
    cen = sum((v.co for v in verts), Vector()) / len(verts)
    pr = [((v.co - cen).dot(e1), (v.co - cen).dot(e2)) for v in verts]
    s1, s2 = max(abs(a) for a, _ in pr) or 1, max(abs(b) for _, b in pr) or 1
    ang = [math.atan2(b / s2, a / s1) for a, b in pr]
    order = sorted(range(len(verts)), key=lambda i: ang[i])
    n = len(verts)
    r0 = order.index(min(range(n), key=lambda i: abs(ang[i])))
    return {verts[i]: (math.cos(2 * math.pi * (rk - r0) / n), math.sin(2 * math.pi * (rk - r0) / n))
            for rk, i in enumerate(order)}


def ear_frame(root):
    d = (EAR_TIP - root).normalized()
    n = Vector(EAR_N); n = (n - d * n.dot(d)).normalized()                 # leaf normal: front-out-up (broad from front, rear, top)
    e1 = n.cross(d).normalized()                                           # leaf width
    if e1.z < 0:
        e1 = -e1
    return d, e1, n


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


def tail_frames():
    """Per tail station: centre, side (x) and up vectors; up is perpendicular to the path in the y-z plane."""
    C = [Vector((0.0, y, z)) for (y, z), _w, _h in TAIL]
    out = []
    for i, ((y, z), w, h) in enumerate(TAIL):
        d = C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]
        d.normalize()
        up = Vector((0.0, -d.z, d.y)).normalized()
        out.append((C[i], w, h, up))
    return out


EARF = {}
LEGREC = []          # per leg station (0 = the root loop): [(position, role (a, b))], for the S2 moves


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
        v.co.z += 0.004

    # legs: a 2-span x 5-face region (crotch -> hip underside -> hip side): the thigh rises out of the flank
    faces, roles = root_patch(rings, spans, idx[LEG_SPAN], LEG_NS, LEG_J0, LEG_NF)
    LEGREC.clear()
    grow(bm, faces, roles, LEG, lpos, rec=LEGREC, hug=LEG_HUG)

    # arms: a 2-span x 4-face region (chest -> shoulder line -> chest top): the chest ring -> the armpit (inner
    # side), the chest-top ring -> the top of the shoulder (outer side): the shoulder sits over the ribcage
    faces, roles = root_patch(rings, spans, idx[ARM_SPAN], 2, ARM_J0, ARM_NF)
    grow(bm, faces, roles, tilt(ARM, J['shoulder']), apos)

    # ears: 3 faces (one column, three spans: ~11 cm tall, the sheet's broad ear base) of the skull side; a hug ring
    # (root loop 1.5 cm out, shrunk 0.9: walls lean in), then the leaf, never wider than the root
    root = Vector(J['ear'])
    f0 = min((f for f in bm.faces if f.normal.x > 0.4 and len(f.verts) == 4),
             key=lambda f: (f.calc_center_median() - root).length)
    nb = [g for e in f0.edges for g in e.link_faces if g is not f0 and g.normal.x > 0.3]
    dz = lambda g: (g.calc_center_median() - f0.calc_center_median()).normalized().z
    ef = [f0, max(nb, key=dz), min(nb, key=dz)]            # the face and its neighbours above and below: a 3-span root
    bv = sorted({v for f in ef for v in f.verts}, key=lambda v: tuple(v.co))
    c0 = sum((v.co for v in bv), Vector()) / len(bv)
    d, e1, e2 = ear_frame(c0)
    pr = {v: ((v.co - c0).dot(e1), (v.co - c0).dot(e2)) for v in bv}
    s1, s2 = max(abs(p[0]) for p in pr.values()), max(abs(p[1]) for p in pr.values())
    # roles = the root vertex's own normalised position in the leaf frame (no re-spacing round the ellipse: the
    # rings morph without twisting; ellipse_roles' even re-spacing twisted ring 2 and made a 57 mm needle, s4 r26)
    roles = {}
    for v, p in pr.items():                              # on the leaf ellipse at the vertex's own angle: round corners
        th_ = math.atan2(p[1] / s2, p[0] / s1)
        roles[v] = (math.cos(th_), math.sin(th_), (v.co - c0) * 0.90)
    nrm0 = sum((f.normal * f.calc_area() for f in ef), Vector()).normalized()
    p1 = c0 + nrm0 * 0.06                                   # the leaf leaves along the root normal, then turns to the tip
    secs = [(c0 * (1 - t) ** 2 + p1 * (2 * t * (1 - t)) + EAR_TIP * t * t, wd, th, bl) for t, wd, th, bl in EAR]
    EARF.update(c0=c0.copy(), e1=e1.copy(), e2=e2.copy())
    # each ring morphs from the root loop's own shape (bl 0) to the leaf ellipse (bl 1): no step at the root
    grow(bm, ef, roles, secs, lambda s, a, b, rel: s[0] + rel.lerp(e1 * a * s[1] + e2 * b * s[2], s[3]))

    # tail: the two back-seam column faces of the groin -> hip span, out and back to a flat spade
    i = idx[TAIL_SPAN]
    lo, hi = rings[i], rings[i + 1]
    n = NV - 1
    roles = {lo[n]: (0.0, -1.0), lo[n - 1]: (math.cos(math.radians(-54)), math.sin(math.radians(-54))),
             lo[n - 2]: (math.cos(math.radians(-18)), math.sin(math.radians(-18))),
             hi[n - 2]: (math.cos(math.radians(18)), math.sin(math.radians(18))),
             hi[n - 1]: (math.cos(math.radians(54)), math.sin(math.radians(54))), hi[n]: (0.0, 1.0)}
    faces = bmesh.ops.dissolve_faces(bm, faces=[spans[i][n - 2], spans[i][n - 1]], use_verts=False)['region']
    # hug ring: the root loop 1.5 cm out along its normal, shrunk 0.85 (walls lean in: no fold over the rump)
    cen = sum((v.co for f in faces for v in f.verts), Vector()) / sum(len(f.verts) for f in faces)
    nrm = faces[0].normal.copy()
    r = extrude(bm, faces)
    new = {}
    for v in r['verts']:
        ov = min(roles, key=lambda o: (o.co - v.co).length)
        new[v] = roles[ov]
        v.co = cen + (v.co - cen) * 0.85 + nrm * 0.015
        if new[v][0] == 0.0:
            v.co.x = 0.0
    bmesh.ops.delete(bm, geom=[g for g in r['sides'] if all(abs(w_.co.x) < 1e-6 for w_ in g.verts)], context='FACES')
    faces, roles = r['faces'], new
    for c, w, h, up in tail_frames():
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (ax, bh) in new.items():
            v.co = c + Vector((ax * w, 0, 0)) + up * bh * h
        seam_walls = [g for g in r['sides'] if all(abs(w_.co.x) < 1e-6 for w_ in g.verts)]
        bmesh.ops.delete(bm, geom=seam_walls, context='FACES')
        faces, roles = r['faces'], new
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = Vector((0.068, -0.236, 0.590))     # the lens centre target (sheet eye, front-side corner of the face under the brow)


def eye_face(bm):
    return min((f for f in bm.faces if len(f.verts) == 4 and f.normal.y < -0.35 and f.calc_center_median().x > 0.02),
               key=lambda f: (f.calc_center_median() - EYE).length)


EYEF = {}
FILLETS = [('thigh root', (0.066, -0.10, 0.165), 0.065)]       # (name, centre, radius): S2 root fillets


def fillet(bm, centre, radius, iters=3, k=0.5):
    """An S2 root fillet (vertex moves only): Laplacian relax of the vertices within `radius` of a limb root, weighted
    by a smooth falloff, so the crease where the limb leaves the torso opens into a broad blend. Seam vertices stay on
    x = 0."""
    c = Vector(centre)
    vs = [v for v in bm.verts if (v.co - c).length < radius]
    for _ in range(iters):
        new = {}
        for v in vs:
            nb = [e.other_vert(v).co for e in v.link_edges]
            if not nb:
                continue
            avg = sum(nb, Vector()) / len(nb)
            w = k * (1.0 - ((v.co - c).length / radius) ** 2)
            new[v] = v.co.lerp(avg, w)
        for v, p in new.items():
            if abs(v.co.x) < 1e-6:
                p.x = 0.0
            v.co = p
    return len(vs)


def keep_eye(c):
    e = EYEF.get('c', EYE)
    return abs(abs(c.x) - e.x) < 0.025 and abs(c.y - e.y) < 0.025 and abs(c.z - e.z) < 0.025


def stage2(k, body):
    """The eye socket (an inset in the eye face under the brow, its floor pushed in), a brow ridge over it, the
    elbow and knee loops for the bend."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    tl, ta = LEG, tilt(ARM, J['shoulder'])
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    cuts = [('elbow loop: the elbow bend', mid(apos(ta[3], 1, -0.5), apos(ta[4], 1, -0.5))),
            ('knee loop: the knee bend', mid(lpos(tl[2], 1, -0.2), lpos(tl[3], 1, -0.2)))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_), t=0.5)
    for nm, cen, rad in FILLETS:
        n_ = fillet(bm, cen, rad)
        say(f'fillet {nm}: {n_} verts relaxed')
    f = eye_face(bm)
    fn, fc = f.normal.copy(), f.calc_center_median()
    EYEF.update(c=fc.copy(), n=fn.copy())
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face under the brow, its floor pushed in'):
        inner = inset(bm, [f], 0.20, 0.0)
    move(list(inner[0].verts), -fn * 0.006)
    H4 = P('H4')
    move([vert_near(bm, H4[j]) for j in (1, 2, 3, 4)], (0.0, -0.005, 0.002))     # brow ridge forward over the socket
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'skin': '#dc5a42', 'belly': '#f0977b', 'wing': '#8e3430', 'horn': '#4a2c22', 'nose': '#a8382f',
       'eye': '#3a2414', 'pupil': '#120c08'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if 0.17 < z < 0.405 and y < -0.12 and math.degrees(math.atan2(x, -0.09 - y)) < 38.0:   # the belly panel (front columns)
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


def wrist_ring(body):
    bm = edit(body)
    c = Vector(ARM[-1][0])
    f = min((f for f in bm.faces if len(f.verts) >= 10), key=lambda f: (f.calc_center_median() - c).length)
    pts = [v.co.copy() for v in f.verts]
    bm.free()
    return pts


def foot_claws(bm, tree, side):
    (cx, cy, _), rx, ry = LEG[-1][:3]
    for o in (-0.036, 0.0, 0.036):
        x = cx + o
        loc, _n = hit(tree, (x, -1.0, 0.016), (0, 1, 0))
        if loc is None:
            continue
        h = Vector((x, loc.y, 0.0))
        w, L, hg = 0.011, 0.026, 0.020
        rows = [[h + Vector((-w, 0.008, 0.004)), h + Vector((w, 0.008, 0.004)), h + Vector((w, 0.008, hg)), h + Vector((-w, 0.008, hg))],
                [h + Vector((-w * 0.8, -L * 0.5, 0.003)), h + Vector((w * 0.8, -L * 0.5, 0.003)),
                 h + Vector((w * 0.6, -L * 0.5, hg * 0.75)), h + Vector((-w * 0.6, -L * 0.5, hg * 0.75))],
                [h + Vector((-w * 0.25, -L, 0.003)), h + Vector((w * 0.25, -L, 0.003)),
                 h + Vector((w * 0.15, -L, hg * 0.3)), h + Vector((-w * 0.15, -L, hg * 0.3))]]
        if side < 0:
            rows = [[Vector((-p.x, p.y, p.z)) for p in reversed(r)] for r in rows]
        box_chain(bm, rows)


# the bat wing (x >= 0): hub at the wrist W, finger tips T1 (outer), T2, T3, the body attach A and root R (both sunk
# ~1 cm in the back), a scalloped trailing edge; a closed slab (membrane 10 mm, spar ridges 21 mm) fanned from W
WING = dict(R=(0.045, -0.048, 0.425), W=(0.20, 0.09, 0.52), T1=(0.35, 0.30, 0.335), T2=(0.215, 0.165, 0.30),
            T3=(0.12, 0.045, 0.315), A=(0.05, -0.032, 0.318))
WH, WS = 0.005, 0.0105          # half thickness: membrane, spar


def _seg_d(p, a, b):
    d = b - a
    t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared))
    return (a + d * t - p).length


def wing_bm(side):
    G = {k_: Vector(v) for k_, v in WING.items()}
    W = G['W']
    n = (G['R'] - W).cross(G['T1'] - W).normalized()
    B = []

    def scal(a, b, m, depth):
        for i in range(1, m + 1):
            t = i / (m + 1)
            p = a.lerp(b, t)
            B.append((p + (W - p).normalized() * depth * math.sin(math.pi * t), False))
    B.append((G['T1'], True)); scal(G['T1'], G['T2'], 3, 0.045)
    B.append((G['T2'], True)); scal(G['T2'], G['T3'], 3, 0.03)
    B.append((G['T3'], True)); scal(G['T3'], G['A'], 1, 0.012)
    B.append((G['A'], False)); scal(G['A'], G['R'], 4, 0.0)
    nsunk = 6                                                   # A, four points of the sunk attach line, R
    B.append((G['R'], True))
    S = 3
    bm = bmesh.new()

    def th(k, i):
        if B[k][1]:
            return WS if k == len(B) - 1 else WS * (1.0 - 0.45 * i / S)
        return WH
    T = [[None] * (S + 1) for _ in B]
    Bo = [[None] * (S + 1) for _ in B]
    # the 12 vertices of the sunk attach line are created first: techqa anchors a seated piece on its first 12
    # vertices, which must be the ones in the back (a wing vertex 11 cm off the skin 'drifts' when the head tilts)
    order = [(k, S) for k in range(len(B) - nsunk, len(B))]
    order += [(k, i) for k in reversed(range(len(B))) for i in range(S, 0, -1) if (k, i) not in order]
    for k, i in order:
        p = B[k][0]
        if True:
            q = W.lerp(p, i / S)
            h = th(k, i)
            T[k][i], Bo[k][i] = bm.verts.new(q + n * h), bm.verts.new(q - n * h)
    hubT, hubB = bm.verts.new(W + n * WS * 1.15), bm.verts.new(W - n * WS * 1.15)
    M = len(B)
    for k in range(M - 1):
        bm.faces.new([hubT, T[k][1], T[k + 1][1]]); bm.faces.new([hubB, Bo[k + 1][1], Bo[k][1]])
        for i in range(1, S):
            bm.faces.new([T[k][i], T[k][i + 1], T[k + 1][i + 1], T[k + 1][i]])
            bm.faces.new([Bo[k][i], Bo[k + 1][i], Bo[k + 1][i + 1], Bo[k][i + 1]])
        bm.faces.new([T[k][S], Bo[k][S], Bo[k + 1][S], T[k + 1][S]])          # trailing rim
    for k in (0, M - 1):                                                        # leading rims (W -> T1, W -> R)
        ch_t, ch_b = [hubT] + T[k][1:], [hubB] + Bo[k][1:]
        for i in range(S):
            bm.faces.new([ch_t[i], ch_t[i + 1], ch_b[i + 1], ch_b[i]])
    recalc_normals(bm)
    bm.faces.ensure_lookup_table()
    spar = {f.index for f in bm.faces
            if _seg_d(f.calc_center_median(), W, G['R']) < 0.012}      # only the arm bone in skin red
    if side < 0:
        for v in bm.verts:
            v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    return bm, spar


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('skin', 'belly')}, body_rule)
    # night 10-23 border pass (owner 10-21 approved kit/smooth_borders, as frog r17): anti-stair cuts + tangential relax
    smooth_borders(body, k=k, iters=8)
    tree = full_bvh(body)
    pieces = []
    # eyes: small round lenses in the sockets, looking forward-out
    fc, fn = EYEF['c'], EYEF['n']
    n = (fn + Vector((0.30, 0, 0.0))).normalized()
    c0 = fc - fn * 0.006
    bm = bmesh.new()
    lens(bm, c0 + n * 0.004, n, 0.0165, 0.0068)
    eye = object_from_bm('eye', bm)
    tip = c0 + n * 0.0105
    paint(eye, {'eye': PAL['eye'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if (Vector((abs(c_.x), c_.y, c_.z)) - tip).length < 0.0068 else 'eye')
    pieces.append(eye)
    # nose: a small button lens on the snout tip (on the seam, not mirrored)
    loc, _n = hit(tree, (0.0, -1.0, 0.537), (0, 1, 0))
    bm = bmesh.new()
    lens(bm, loc + Vector((0, 0.004, 0)), Vector((0, -1, 0.25)), 0.014, 0.008)
    nose = object_from_bm('nose', bm, mirror=False)
    paint(nose, {'nose': PAL['nose']}, lambda c_, n_, i: 'nose')
    pieces.append(nose)
    # horns: short dark cones on the skull top, curving a little back
    for side in (1, -1):
        loc, _n = hit(tree, (side * 0.075, -0.118, 1.0), (0, 0, -1))
        hn = PT.horn(loc, length=0.11, radius=0.029, forward=(side * 0.12, 0.02, 1), up=(0, 1, 0), side=side, curve=30, taper=1.5,
                     segs=4, sides=6, name=f'horn_{"L" if side > 0 else "R"}')
        paint(hn, {'horn': PAL['horn']}, lambda c_, n_, i: 'horn')
        pieces.append(hn)
    # hands: the parts-library three-finger hand with small dark claws on each wrist ring
    wr = wrist_ring(body)
    for side in (1, -1):
        o = Vector((side * 0.192, -0.104, 0.196))
        hand = PT.hand_three_finger(o, width=0.062, forward=(side * 0.2, -0.2, -1), up=(side * 1.0, 0.1, 0.2), side=side,
                                    fingers=3, curl=0.35, finger_len=0.85, thumb_curl=0.2, claw_len=0.22,
                                    wrist=(0.027, 0.023), open_root=True, mats={'skin': 'skin', 'claw': 'horn'}, name=f'hand_{"L" if side > 0 else "R"}')
        ring_pts = wr if side > 0 else [Vector((-p.x, p.y, p.z)) for p in reversed(wr)]
        k.bridge_part(hand, ring_pts, reason='parts-library 3-finger clawed hand on the wrist ring')
        pieces.append(hand)
    # toe claws: three per foot
    for side in (1, -1):
        bm = bmesh.new()
        foot_claws(bm, tree, side)
        to = object_from_bm(f'claws_{"L" if side > 0 else "R"}', bm, mirror=False)
        paint(to, {'horn': PAL['horn']}, lambda c_, n_, i: 'horn')
        pieces.append(to)
    # wings: closed slabs, membrane + spar ridges
    for side in (1, -1):
        bm, sp = wing_bm(side)
        wg = object_from_bm(f'wing_{"L" if side > 0 else "R"}', bm, mirror=False)
        paint(wg, {'skin': PAL['skin'], 'wing': PAL['wing']}, lambda c_, n_, i: 'skin' if i in sp else 'wing')
        pieces.append(wg)
    return pieces


# ---------------------------------------------------------------- stage 4
def bind_wing(p, rig, body, side):
    """Each wing vertex takes the skin weights of the body vertex nearest to its projection on the sunk attach line
    A-R: the root follows the back skin exactly (no drift) and the slab moves as a rigid sheet (no stretch toward the
    tail or the ear, which nearest-surface weights gave: 9x stretch, 1.7% folds in s4 r03)."""
    bind(p, rig, body=body)
    A = Vector((side * WING['A'][0], WING['A'][1], WING['A'][2]))
    R = Vector((side * WING['R'][0], WING['R'][1], WING['R'][2]))
    bv = [(body.matrix_world @ v.co, v) for v in body.data.vertices]
    bgn = {g.index: g.name for g in body.vertex_groups}
    cache = {}
    for g in list(p.vertex_groups):
        p.vertex_groups.remove(g)
    for v in p.data.vertices:
        q = p.matrix_world @ v.co
        t = max(0.0, min(1.0, (q - A).dot(R - A) / (R - A).length_squared))
        key = round(t * 20)
        if key not in cache:
            c = A.lerp(R, key / 20)
            cache[key] = min(bv, key=lambda e: (e[0] - c).length)[1]
        for g in cache[key].groups:
            if g.weight > 1e-4:
                nm = bgn[g.group]
                vg = p.vertex_groups.get(nm) or p.vertex_groups.new(name=nm)
                vg.add([v.index], g.weight, 'REPLACE')


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
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),                 # short root bone: the probe radius stays at the root
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('tail3', J['tail3'], J['tailtip'], 'tail2', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    # the shoulder-blade skin under the wing roots follows the trunk, not the arm swing (the wings ride it)
    gi = {g.name: g for g in body.vertex_groups}
    for v in body.data.vertices:
        c = body.matrix_world @ v.co
        if abs(c.x) < 0.085 and c.y > -0.075 and 0.28 < c.z < 0.47:
            for nm in ('upperarm.L', 'upperarm.R'):
                if nm in gi:
                    gi[nm].remove([v.index])
    for p in pieces:
        nm = p.name
        if nm.startswith('piece_hand'):
            bind(p, rig, bone='hand.L' if nm.endswith('_L') else 'hand.R')
        elif nm.startswith('piece_horn'):
            bind(p, rig, bone='head')
        elif nm.startswith('piece_wing'):
            bind_wing(p, rig, body, 1 if nm.endswith('_L') else -1)
        else:
            bind(p, rig, body=body)
    # idle: breathing, a head tilt, the ears and the tail sway, the wings ride the chest
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'head': (0, 0, 4), 'ear.L': (0, 0, 5), 'ear.R': (0, 0, -5),
                                   'tail1': (0, 0, 8), 'tail2': (0, 0, 8)},
                       24: {}, 36: {'chest': (2, 0, 0), 'head': (0, 0, -4), 'tail1': (0, 0, -8), 'tail2': (0, 0, -8)},
                       48: {}})
    # move: a quick waddle; short leg swing, knee bend on the passing leg, arm swing, tail sway, 
    A, S = 16, 14
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
            'spine': (0, 0, 3), 'tail1': (0, 0, 10)},
        9: {'shin.R': (-24, 0, 0), 'foot.R': (10, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0),
             'spine': (0, 0, -3), 'tail1': (0, 0, -10)},
        25: {'shin.L': (-24, 0, 0), 'foot.L': (10, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
             'spine': (0, 0, 3), 'tail1': (0, 0, 10)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.008, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.008, 0)},
             33: {'hips': (0, 0, 0)}})
    # attack: the right arm rears back then a clawing swipe, the tail lashes
    clip(rig, 'attack', {
        1: {},
        10: {'upperarm.R': (55, 0, 0), 'forearm.R': (35, 0, 0), 'chest': (-5, 0, 0), 'head': (-4, 0, 0),
             'tail1': (0, 0, -12), 'tail2': (0, 0, -10)},
        18: {'upperarm.R': (-35, 0, 0), 'forearm.R': (10, 0, 0), 'chest': (9, 0, 0), 'spine': (4, 0, 0), 'head': (5, 0, 0),
             'tail1': (0, 0, 12), 'tail2': (0, 0, 10)},
        24: {'upperarm.R': (-20, 0, 0), 'forearm.R': (8, 0, 0), 'chest': (5, 0, 0), 'spine': (2, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
