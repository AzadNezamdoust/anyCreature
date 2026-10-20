import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# emperor penguin, t7 hand box-model (owl / imp line). ONE spine loft of 17-vertex half rings runs bottom -> crown
# (front seam down the belly, back seam down the back; the head rings tilt so the front seam rides the chin and
# the beak root). The flippers are 2-span x 3-face regions of the shoulder side (the shoulder ring carries the
# flipper top), the legs 1-span x 4-face regions of the flat bottom seat ending in a webbed foot block, the slim
# beak a 2-face region of the face on the front seam (its seam walls removed: the mirror closes it), the stiff tail
# a 2-face region of the rump on the back seam. Colour borders run along PLACED loops: vertex column NB of every
# ring sits at the black/white border angle TB(z) (front of it white/yellow, behind it black), level rings carry
# the yellow-chest and hood borders, flipper inner faces (role a = -1) are white. Lens eyes, toes and claws are S3.
# Coordinates from blueprint.json (refs.py --height 1.1 --thresh 14: the cream belly needs the low threshold).
META = dict(creature='penguin', model='opus', stage1_tris=(1500, 3600), total_tris=(2000, 5000),
            closeups=[('head', (0.0, -0.12, 0.99), 0.17, 'hero'),
                      ('flipper root', (0.19, 0.0, 0.80), 0.16, 'hero'),
                      ('foot', (0.13, -0.03, 0.04), 0.13, 'hero'),
                      ('tail', (0.0, 0.31, 0.12), 0.13, 'back34')])

J = dict(
    hips=(0.0, 0.09, 0.22), spine=(0.0, 0.06, 0.48), chest=(0.0, 0.02, 0.74), neck=(0.0, -0.01, 0.88),
    head=(0.0, -0.04, 0.965), crown=(0.0, -0.13, 1.06),
    wing=(0.185, 0.0, 0.815), wing1=(0.275, 0.085, 0.52), wing2=(0.305, 0.165, 0.245),
    thigh=(0.125, 0.07, 0.10), ankle=(0.13, 0.05, 0.035), toe=(0.13, -0.15, 0.01),
    tail0=(0.0, 0.29, 0.175), tail1=(0.0, 0.32, 0.12), tail2=(0.0, 0.35, 0.03),
)

NV = 17          # vertices per half ring, front seam (0) -> back seam (16)
NB = 9           # the black/white border column


def TB(z):
    """Border angle (deg from the front seam) of column NB at height z: the white front wraps far back low on the
    body, comes forward to the front edge of the flipper at the shoulder, and goes back on the neck to the ear patch."""
    pts = [(0.0, 125), (0.30, 122), (0.45, 117), (0.60, 104), (0.72, 88), (0.80, 78), (0.86, 77), (0.90, 84),
           (0.95, 92), (1.00, 96), (1.05, 100), (1.2, 100)]
    for (z0, a0), (z1, a1) in zip(pts, pts[1:]):
        if z <= z1:
            return a0 + (a1 - a0) * max(0.0, (z - z0)) / (z1 - z0)
    return pts[-1][1]


def prof(tb, e=0.85, back=0.0):
    """Half-ring profile (fx share of W, fh +1 front .. -1 back) with vertex NB at angle tb."""
    out = []
    for i in range(NV):
        if i <= NB:
            t = math.radians(tb) * i / NB
        else:
            t = math.radians(tb) + (math.pi - math.radians(tb)) * (i - NB) / (NV - 1 - NB)
        c = math.cos(t)
        fx = 0.0 if i in (0, NV - 1) else math.sin(t) ** e * (1.0 + back * (-c))
        out.append((fx, c))
    return out


# the spine loft, bottom -> crown: (name, front seam (y, z), back seam (y, z), W, e, back)
SECS = [
    ('R0', (0.020, 0.080), (0.160, 0.080), 0.125, 0.85, 0.0),     # the bottom seat (the legs drop from it)
    ('R1', (-0.035, 0.095), (0.225, 0.100), 0.172, 0.85, 0.0),
    ('R2', (-0.070, 0.140), (0.282, 0.145), 0.197, 0.85, 0.0),
    ('R3', (-0.100, 0.195), (0.304, 0.195), 0.214, 0.85, 0.0),    # rump (the tail root)
    ('R4', (-0.128, 0.250), (0.312, 0.250), 0.229, 0.85, 0.0),
    ('R5', (-0.151, 0.300), (0.317, 0.300), 0.240, 0.85, 0.0),
    ('R6', (-0.173, 0.350), (0.321, 0.350), 0.247, 0.85, 0.0),
    ('R7', (-0.187, 0.400), (0.321, 0.400), 0.249, 0.85, 0.0),    # widest
    ('R8', (-0.200, 0.450), (0.318, 0.450), 0.248, 0.85, 0.0),
    ('R9', (-0.211, 0.500), (0.310, 0.500), 0.244, 0.85, 0.0),
    ('R10', (-0.218, 0.550), (0.300, 0.550), 0.237, 0.85, 0.0),
    ('R11', (-0.221, 0.600), (0.287, 0.600), 0.228, 0.85, 0.0),   # belly front
    ('R12', (-0.220, 0.650), (0.272, 0.650), 0.215, 0.85, 0.0),
    ('R13', (-0.215, 0.700), (0.252, 0.700), 0.193, 0.85, 0.0),
    ('R14', (-0.206, 0.750), (0.230, 0.750), 0.173, 0.85, 0.0),
    ('C0', (-0.194, 0.800), (0.205, 0.800), 0.156, 0.85, 0.0),    # shoulder (flipper root bottom)
    ('C1', (-0.180, 0.840), (0.183, 0.840), 0.146, 0.85, 0.0),
    ('N0', (-0.165, 0.870), (0.163, 0.870), 0.138, 0.85, 0.0),    # flipper root top
    ('N1', (-0.155, 0.900), (0.140, 0.895), 0.131, 0.85, 0.05),   # throat
    ('H0', (-0.187, 0.946), (0.118, 0.925), 0.122, 0.9, 0.15),    # chin
    ('H1', (-0.219, 0.968), (0.100, 0.955), 0.112, 0.9, 0.25),    # beak root bottom
    ('H2', (-0.222, 1.016), (0.075, 0.990), 0.103, 0.9, 0.25),    # beak root top
    ('H3', (-0.200, 1.046), (0.055, 1.035), 0.095, 0.9, 0.25),    # brow
    ('H4', (-0.164, 1.075), (0.025, 1.070), 0.077, 0.9, 0.2),
    ('H5', (-0.120, 1.093), (-0.020, 1.093), 0.046, 0.9, 0.1),    # crown
]


def sec_pts(F, B, W, e, bk):
    F, B = Vector((0.0,) + tuple(F)), Vector((0.0,) + tuple(B))
    m, u = (F + B) / 2, (B - F) / 2
    tb = TB(m.z)
    return [(fx * W, (m - u * fh).y, (m - u * fh).z) for fx, fh in prof(tb, e, bk)]


def P(nm):
    for (n, F, B, W, e, bk) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(F, B, W, e, bk)]


IDX = {s[0]: i for i, s in enumerate(SECS)}


def kx(b, corner=0.55):
    return corner if abs(b) > 0.99 else math.sqrt(max(0.0, 1.0 - 0.75 * b * b))


def lpos(sec, a, b):
    """Leg ring point (a -1 inner .. +1 outer, b -1 front .. +1 back), a horizontal rounded box."""
    c, rx, ry = sec[:3]
    tp = sec[3] if len(sec) > 3 else 0.0        # webbed foot: wider at the front (b = -1)
    return (c[0] + a * rx * kx(b) * (1.0 - tp * b), c[1] + b * ry, c[2])


# flipper: horizontal sections down the flipper: (centre, half thickness (a), half width (b), dz); the flat plane
# turned FLIP_ROT deg about z (front edge out: the white inner face shows from the front, as on the sheet)
FLIP_ROT = 15.0
FLIP = [((0.200, 0.030, 0.778), 0.021, 0.066, -0.012, 0.85),    # shoulder cap: hugs the shoulder, outer side high
        ((0.219, 0.040, 0.722), 0.022, 0.062, -0.006, 0.7),
        ((0.243, 0.052, 0.645), 0.018, 0.068, 0.0),
        ((0.264, 0.074, 0.565), 0.015, 0.074, 0.0),
        ((0.281, 0.096, 0.485), 0.013, 0.075, 0.0),
        ((0.294, 0.117, 0.405), 0.012, 0.071, 0.0),
        ((0.301, 0.136, 0.330), 0.011, 0.059, 0.0),
        ((0.303, 0.151, 0.275), 0.009, 0.041, 0.0),
        ((0.301, 0.160, 0.243), 0.006, 0.020, 0.0)]


def fpos(sec, a, b):
    c, rt, rw, dz = sec[:4]
    co = sec[4] if len(sec) > 4 else 0.75         # corner: the root sections keep round corners (no notch)
    r = math.radians(FLIP_ROT)
    ea, eb = Vector((math.cos(r), math.sin(r), 0.0)), Vector((-math.sin(r), math.cos(r), 0.0))
    p = Vector(c) + ea * (a * rt * kx(b, co)) + eb * (b * rw * (0.86 if abs(a) > 0.99 else 1.0))
    return (p.x, p.y, p.z - a * dz)


LEG = [((0.128, 0.060, 0.050), 0.050, 0.062),       # feathered 'pants'
       ((0.130, 0.045, 0.034), 0.042, 0.052),       # ankle
       ((0.130, -0.005, 0.018), 0.050, 0.100, 0.35),   # foot top: a flat webbed foot, wide at the toes
       ((0.130, -0.020, 0.006), 0.056, 0.125, 0.40),   # sole edge
       ((0.130, -0.020, 0.0), 0.053, 0.120, 0.40)]     # sole
LEG_HUG = (0.008, 0.92)
# tail: (centre (y, z), half width x, half height); a stiff wedge from the rump down to the ground
TAIL = [((0.290, 0.103), 0.054, 0.028),
        ((0.312, 0.070), 0.045, 0.021),
        ((0.330, 0.042), 0.030, 0.013),
        ((0.344, 0.020), 0.012, 0.006)]
# beak: (centre (y, z), half width x, half height); slim, the tip a little down
BEAK = [((-0.258, 0.994), 0.018, 0.023),
        ((-0.285, 0.988), 0.014, 0.015),
        ((-0.320, 0.983), 0.0095, 0.010),
        ((-0.352, 0.978), 0.0045, 0.0055)]


def root_patch(rings, spans, i0, nspan, j0, nf):
    """A limb root region: nspan spans x nf faces. Roles: ring i0 -> inner side (a = -1), ring i0+nspan -> outer
    (a = +1), the rings between -> their end vertices on the front / back edge (b = -1 / +1)."""
    roles = {}
    for c in range(nf + 1):
        b = -1 + 2.0 * c / nf
        roles[rings[i0][j0 + c]] = (-1, b); roles[rings[i0 + nspan][j0 + c]] = (1, b)
    for m in range(1, nspan):
        a = -1 + 2.0 * m / nspan
        roles[rings[i0 + m][j0]] = (a, -1); roles[rings[i0 + m][j0 + nf]] = (a, 1)
    faces = [spans[i0 + m][j0 + c] for m in range(nspan) for c in range(nf)]
    return faces, roles


FC = []           # (stage-1 face centre, tag): stage 3 tags each face from its nearest stage-1 face
TAG = {}          # BMFace -> part * 10000 + span * 100 + col (written to the face layer 'ptag' at the end of stage 1)
PART = dict(loft=1, flip=2, flipin=3, leg=4, beak=5, tail=6, cap=7)


def tag_sides(sides, roles, part, step, inner=None):
    for f in sides:
        p = part
        if inner is not None:
            rs = [roles.get(v) for v in f.verts]
            if all(r_ is not None and r_[0] < -0.99 for r_ in rs):
                p = inner
        TAG[f] = p * 10000 + step * 100


def grow(bm, faces, roles, secs, pos, hug=None, part=None, inner=None):
    """Extrude a face region section by section; each new vertex keeps the role of the vertex it came from.
    A multi-face root region is first dissolved into one face, so each section is one ring."""
    if len(faces) > 1:
        mids = [v for f in faces for v in f.verts if all(g in faces for g in v.link_faces)]
        faces = bmesh.ops.dissolve_faces(bm, faces=list(faces), use_verts=False)['region']
        loose = [v for v in set(mids) if v.is_valid and not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    rings = []
    if hug is not None:
        bv = list({v for f in faces for v in f.verts})
        cen = sum((v.co for v in bv), Vector()) / len(bv)
        nrm = sum((f.normal * f.calc_area() for f in faces), Vector()).normalized()
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
            v.co = cen + (v.co - cen) * hug[1] + nrm * hug[0]
        if part:
            tag_sides(r['sides'], {**roles, **new}, part, 0, inner)
        faces, roles = r['faces'], new
        rings.append(dict(roles))
    for si, sec in enumerate(secs):
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, ab in new.items():
            v.co = Vector(pos(sec, *ab))
        if part:
            tag_sides(r['sides'], {**roles, **new}, part, si + 1, inner)
        faces, roles = r['faces'], new
        rings.append(dict(roles))
    if part:
        for f in faces:
            TAG[f] = part * 10000 + (len(secs) + 1) * 100
    return faces, roles, rings


def seam_grow(bm, faces, roles, frames, hug, part=0):
    """A seam-region extrusion (beak, tail): the region's seam walls are removed every step (the mirror closes
    them). roles: vertex -> (ax, bh) on the section ellipse; frames: (centre, half width, half height, up)."""
    faces = bmesh.ops.dissolve_faces(bm, faces=list(faces), use_verts=False)['region'] if len(faces) > 1 else faces
    cen = sum((v.co for f in faces for v in f.verts), Vector()) / sum(len(f.verts) for f in faces)
    nrm = sum((f.normal * f.calc_area() for f in faces), Vector()).normalized()
    r = extrude(bm, faces)
    new = {}
    for v in r['verts']:
        ov = min(roles, key=lambda o: (o.co - v.co).length)
        new[v] = roles[ov]
        v.co = cen + (v.co - cen) * hug[1] + nrm * hug[0]
        if new[v][0] == 0.0:
            v.co.x = 0.0
    bmesh.ops.delete(bm, geom=[g for g in r['sides'] if all(abs(w_.co.x) < 1e-6 for w_ in g.verts)], context='FACES')
    tag_sides([g for g in r['sides'] if g.is_valid], {}, part, 0)
    faces, roles = r['faces'], new
    for si, (c, w, h, up) in enumerate(frames):
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (ax, bh) in new.items():
            v.co = c + Vector((ax * w, 0, 0)) + up * bh * h
        bmesh.ops.delete(bm, geom=[g for g in r['sides'] if all(abs(w_.co.x) < 1e-6 for w_ in g.verts)], context='FACES')
        tag_sides([g for g in r['sides'] if g.is_valid], {}, part, si + 1)
        faces, roles = r['faces'], new
    for f in faces:
        TAG[f] = part * 10000 + (len(frames) + 1) * 100
    return faces


def path_frames(secs, flip=1.0):
    C = [Vector((0.0, y, z)) for (y, z), _w, _h in secs]
    out = []
    for i, ((y, z), w, h) in enumerate(secs):
        d = C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]
        d.normalize()
        up = Vector((0.0, -d.z, d.y)).normalized() * flip
        out.append((C[i], w, h, up))
    return out


def ell(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


FLIPREC, LEGREC = [], []


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(F, B, W, e, bk)) for (nm, F, B, W, e, bk) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    TAG.clear()
    for i, row in enumerate(spans):
        for j, f in enumerate(row):
            TAG[f] = PART['loft'] * 10000 + i * 100 + j
    bot = cap(bm, rings[0])
    top = cap(bm, rings[-1])
    recalc_normals(bm)
    for f, dz in ((top, 0.005), (bot, -0.004)):
        pk = bmesh.ops.poke(bm, faces=[f])
        for v in pk['verts']:
            v.co.z += dz
        for g in pk['faces']:
            TAG[g] = PART['cap'] * 10000 + (0 if dz < 0 else 99) * 100

    # flippers: the shoulder side, rings C0 -> C1 -> N0 (2 spans) x columns NB .. NB+3: C0 -> the inner face,
    # N0 -> the outer face (the shoulder ring runs on into the flipper top)
    faces, roles = root_patch(rings, spans, IDX['C0'], 2, NB, 3)
    _f, _r, rec = grow(bm, faces, roles, FLIP, fpos, part=PART['flip'], inner=PART['flipin'])
    FLIPREC[:] = rec

    # legs: the bottom seat R0 -> R1 x 4 columns (R0 inner, R1 outer), a hug ring, the pants, the foot block
    faces, roles = root_patch(rings, spans, IDX['R0'], 1, 3, 4)
    _f, _r, rec = grow(bm, faces, roles, LEG, lpos, hug=LEG_HUG, part=PART['leg'])
    LEGREC[:] = rec

    # beak: the front-seam face of the H1 -> H2 span (one column: a slim hexagonal beak the width of its root) (lo = H1 the lower mandible, hi = H2 the culmen)
    i = IDX['H1']
    lo, hi = rings[i], rings[i + 1]
    roles = {lo[0]: (0.0, -1.0), lo[1]: ell(-40), hi[1]: ell(40), hi[0]: (0.0, 1.0)}
    seam_grow(bm, [spans[i][0]], roles, path_frames(BEAK, -1.0), (0.008, 0.97), PART['beak'])

    # tail: the two back-seam faces of the R1 -> R2 span (the rump bottom), down-back to the ground
    i = IDX['R1']
    lo, hi = rings[i], rings[i + 1]
    n = NV - 1
    roles = {lo[n]: (0.0, -1.0), lo[n - 1]: ell(-55), lo[n - 2]: ell(-18), hi[n - 2]: ell(18), hi[n - 1]: ell(55),
             hi[n]: (0.0, 1.0)}
    seam_grow(bm, [spans[i][n - 2], spans[i][n - 1]], roles, path_frames(TAIL), (0.012, 0.85), PART['tail'])
    snap_seam(bm)
    recalc_normals(bm)
    FC.clear()
    for f in bm.faces:
        FC.append((f.calc_center_median().copy(), TAG.get(f, 0)))
    say('stage-1 tags', len(TAG), 'faces', len(FC), 'tagged', sum(1 for _c, t in FC if t))
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
EYE = Vector((0.07, -0.114, 1.022))     # the sheet eye (side y -0.114, z 1.022; front x ~0.062)
EYEF = {}


def keep_eye(c):
    e = EYEF.get('c', EYE)
    return abs(abs(c.x) - e.x) < 0.03 and abs(c.y - e.y) < 0.03 and abs(c.z - e.z) < 0.03


def mid(a, b):
    return tuple((Vector(a) + Vector(b)) / 2)


FILLETS = []       # (name, centre, radius): S2 root fillets


def fillet(bm, centre, radius, iters=3, k=0.5):
    """An S2 root fillet (vertex moves only, imp's): Laplacian relax of the vertices within `radius` of a limb root,
    weighted by a smooth falloff, so the crease where the limb leaves the body opens into a broad blend."""
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


def stage2(k, body):
    """Joint loops (flipper shoulder and wrist, ankle, neck), the eye socket."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    cuts = [('flipper shoulder loop: the flipper swings at the shoulder', mid(fpos(FLIP[0], 1, 1 / 3), fpos(FLIP[1], 1, 1 / 3))),
            ('flipper wrist loop: the flipper bends at wing1', mid(fpos(FLIP[3], 1, 1 / 3), fpos(FLIP[4], 1, 1 / 3))),
            ('ankle loop: the foot bend', mid(lpos(LEG[1], 1, 0), lpos(LEG[2], 1, 0))),
            ('neck loop: the head turn and the throat curve', mid(P('N1')[4], P('H0')[4]))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_), t=0.5)
    for nm, cen, rad in FILLETS:
        say(f'fillet {nm}: {fillet(bm, cen, rad)} verts relaxed')
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    loc, nrm, fi, _d = tree.ray_cast(Vector((0.4, EYE.y, EYE.z)), Vector((-1, 0, 0)), 1.0)
    f = bm.faces[fi]
    fn, fc = f.normal.copy(), f.calc_center_median()
    say('eye face', [round(x, 3) for x in fc], 'normal', [round(x, 2) for x in fn],
        'edges mm', [round(1000 * e.calc_length()) for e in f.edges])
    EYEF.update(c=fc.copy(), n=fn.copy())
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face behind the beak root, its floor pushed in'):
        inner = inset(bm, [f], 0.22, 0.0)
    move(list(inner[0].verts), -fn * 0.005)
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'black': '#383b42', 'white': '#ebe7dd', 'yellow': '#f4e1ad', 'orange': '#eda33c', 'iris': '#6e4a30',
       'pupil': '#141210', 'claw': '#55585e'}
TAGS = []


def body_tags(body):
    """Tag per polygon from the nearest stage-1 face centre (a loop-cut half or a socket face finds its parent)."""
    from mathutils.kdtree import KDTree
    kd = KDTree(len(FC))
    for i, (c, _t) in enumerate(FC):
        kd.insert(c, i)
    kd.balance()
    out = [FC[kd.find(body.matrix_world @ p.center)[1]][1] for p in body.data.polygons]
    say('tags: faces', len(out), 'untagged', out.count(0))
    return out


def beak_axis_z(y):
    pts = [(-0.222, 0.992)] + [(yy, zz) for (yy, zz), _w, _h in BEAK]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y1 <= y <= y0:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[-1][1]


def body_rule(c, n, i):
    t = TAGS[i] if i < len(TAGS) else 0
    part, span, col = t // 10000, (t // 100) % 100, t % 100
    x, y, z = abs(c.x), c.y, c.z
    if part == PART['beak']:
        return 'orange' if z < beak_axis_z(y) - 0.002 else 'black'       # the lower-mandible stripe
    if part in (PART['flip'], PART['flipin']):
        # the inner (body-side) face is white below the shoulder band; judged from the face normal, so a loop-cut
        # half that inherited a rim tag cannot leave a black speck in the white (s4 r04 az000 crop)
        r = math.radians(FLIP_ROT)
        inward = -(n.x if c.x >= 0 else -n.x) * math.cos(r) - n.y * math.sin(r)
        return 'white' if (z < 0.70 and inward > 0.35) else 'black'
    if part == PART['tail']:
        return 'black'
    if part == PART['leg']:
        return 'black' if z < 0.024 else 'white'                         # white pants, black webbed feet
    if part == PART['cap']:
        return 'white' if span == 0 else 'black'
    if part == PART['loft']:
        patch = NB <= col <= NB + 2                                      # ear patch: 3 columns behind the eye
        if span < IDX['C0']:
            return 'white' if col < NB else 'black'
        if span <= IDX['N1']:
            if col < NB:
                return 'yellow'                                          # upper chest and throat
            return 'orange' if (span == IDX['N1'] and NB <= col <= NB + 1) else 'black'   # its narrow tail
        if span <= IDX['H2']:
            return 'orange' if patch else 'black'                        # the ear patch behind the eye
        return 'black'
    return 'black'


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


def full_bvh(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def toe(bm, bc, root, d, L, w0, h0):
    """A flat webbed toe from root along d (tapering, on the ground, its root sunk in the foot block) and its claw
    (separate piece bc)."""
    side = Vector((-d.y, d.x, 0.0))
    rows = []
    for t, w, h in ((0.0, w0, h0), (0.55, w0 * 0.8, h0 * 0.75), (1.0, w0 * 0.55, h0 * 0.5)):
        c = root + d * (L * t)
        rows.append([bm.verts.new(c + side * su * w + Vector((0, 0, zz))) for su, zz in ((-1, 0.005), (1, 0.005), (1, h), (-1, h))])
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(rows[-1])
    tip = root + d * (L - 0.004)
    base = [bc.verts.new(tip + side * su * w0 * 0.45 + Vector((0, 0, zz))) for su, zz in ((-1, 0.002), (1, 0.002), (1, h0 * 0.5), (-1, h0 * 0.5))]
    pt = bc.verts.new(tip + d * 0.018 + Vector((0, 0, 0.0015)))
    bc.faces.new(list(reversed(base)))
    for j in range(4):
        bc.faces.new([base[j], base[(j + 1) % 4], pt])


def stage3(k, body):
    TAGS[:] = body_tags(body)
    paint(body, {kk: PAL[kk] for kk in ('black', 'white', 'yellow', 'orange')}, body_rule)
    pieces = []
    # eyes: small round dark-brown lenses in the sockets, looking out and a little forward
    fc, fn = EYEF['c'], EYEF['n']
    n = (fn + Vector((0.0, -0.55, 0.05))).normalized()
    c0 = fc - fn * 0.005
    bm = bmesh.new()
    lens(bm, c0 + n * 0.003, n, 0.0135, 0.0065)
    eye = object_from_bm('eye', bm)
    tip = c0 + n * 0.0095
    paint(eye, {'iris': PAL['iris'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if (Vector((abs(c_.x), c_.y, c_.z)) - tip).length < 0.0062 else 'iris')
    pieces.append(eye)
    # webbed feet: three flat toes fanned forward from the foot block's front, each with a dark claw
    tb_, tc = bmesh.new(), bmesh.new()
    (cx, cy, _), rx, ry = LEG[3][:3]
    for ang, dx, L in ((-24, -0.034, 0.066), (0, 0.0, 0.074), (24, 0.034, 0.066)):
        d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.0))
        root = Vector((cx + dx, cy - ry + 0.03, 0.0))
        toe(tb_, tc, root, d, L, 0.018, 0.017)
    toes = object_from_bm('toes', tb_)
    paint(toes, {'black': PAL['black']}, lambda c_, n_, i: 'black')
    claws = object_from_bm('claws', tc)
    paint(claws, {'claw': PAL['claw']}, lambda c_, n_, i: 'claw')
    pieces += [toes, claws]
    return pieces


# ---------------------------------------------------------------- stage 4
def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['crown'], 'neck', True),
         ('wing.L', J['wing'], J['wing1'], 'chest'),
         ('wingtip.L', J['wing1'], J['wing2'], 'wing.L', True),
         ('thigh.L', J['thigh'], J['ankle'], 'hips'),
         ('foot.L', J['ankle'], J['toe'], 'thigh.L', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),               # short root bone: the probe radius stays at the root
         ('tail1', J['tail1'], J['tail2'], 'tail0', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing, a slow head turn, a small flipper settle
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (0, 14, 0), 'wing.L': (0, 0, 4), 'wing.R': (0, 0, -4)},
                       24: {}, 36: {'chest': (2, 0, 0), 'neck': (0, -14, 0)}, 48: {}})
    # move: the waddle - the body rocks side to side over each foot, the feet shuffle, flippers held out
    clip(rig, 'move', {
        1: {'hips': (0, 0, 6), 'thigh.L': (-8, 0, 0), 'thigh.R': (6, 0, 0), 'wing.L': (0, 0, 12), 'wing.R': (0, 0, -12),
            'neck': (0, 0, -4)},
        9: {'hips': (0, 0, 0), 'wing.L': (0, 0, 16), 'wing.R': (0, 0, -16)},
        17: {'hips': (0, 0, -6), 'thigh.L': (6, 0, 0), 'thigh.R': (-8, 0, 0), 'wing.L': (0, 0, 12), 'wing.R': (0, 0, -12),
             'neck': (0, 0, 4)},
        25: {'hips': (0, 0, 0), 'wing.L': (0, 0, 16), 'wing.R': (0, 0, -16)},
        33: {'hips': (0, 0, 6), 'thigh.L': (-8, 0, 0), 'thigh.R': (6, 0, 0), 'wing.L': (0, 0, 12), 'wing.R': (0, 0, -12),
             'neck': (0, 0, -4)}})
    # attack: rear up with the flippers raised, then a beak jab forward and down
    clip(rig, 'attack', {
        1: {},
        10: {'spine': (-6, 0, 0), 'neck': (-10, 0, 0), 'wing.L': (0, 0, 30), 'wing.R': (0, 0, -30),
             'wingtip.L': (0, 0, 8), 'wingtip.R': (0, 0, -8)},
        16: {'spine': (8, 0, 0), 'chest': (6, 0, 0), 'neck': (18, 0, 0), 'head': (10, 0, 0), 'wing.L': (0, 0, 20),
             'wing.R': (0, 0, -20)},
        24: {'spine': (3, 0, 0), 'neck': (6, 0, 0), 'wing.L': (0, 0, 8), 'wing.R': (0, 0, -8)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
