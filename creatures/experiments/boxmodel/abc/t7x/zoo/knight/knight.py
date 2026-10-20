import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# knight (biped), t7 hand box-model: one spine loft of 6-vertex half rings runs pelvis (crotch) -> helmet crown, the
# rings lying flat (back seam -> front seam). Legs are 2-face regions of the crotch-hip span extruded down as
# horizontal hexagons, arms 2-face regions of the chest side extruded out-down (the first arm section is the
# pauldron mass). Plate armour = chunky sections + colour zones; tabard, belt, cape, shield and sword are pieces.
# Coordinates from blueprint.json (refs.py, height 1.8 m); the sheet's top view is rotated/unreliable, not used.
META = dict(creature='knight', model='opus', stage1_tris=(1200, 3200), total_tris=(2600, 6000),
            closeups=[('helmet', (0.0, -0.05, 1.66), 0.40, 'hero'),
                      ('gauntlet', (0.47, -0.04, 0.74), 0.20, 'hero'),
                      ('sabaton', (0.25, -0.05, 0.08), 0.30, 'hero'),
                      ('belt and sword', (0.25, -0.15, 0.95), 0.40, 'hero')])

# skeleton (x >= 0 half; .L on +X, front = -Y)
J = dict(
    hips=(0.0, -0.02, 0.58), spine=(0.0, -0.03, 0.82), chest=(0.0, -0.05, 1.08), neck=(0.0, -0.05, 1.45),
    head=(0.0, -0.05, 1.53), crown=(0.0, -0.05, 1.83),
    shoulder=(0.27, -0.01, 1.30), elbow=(0.45, -0.02, 0.98), wrist=(0.47, -0.035, 0.76), hand=(0.47, -0.045, 0.62),
    hipL=(0.17, -0.01, 0.56), knee=(0.21, 0.0, 0.38), ankle=(0.24, 0.03, 0.11), toe=(0.25, -0.24, 0.03),
)
SH = -0.03          # s1 r4: the whole figure sits 3 cm forward of the first table (the trace's y origin)
J = {k_: (v[0], v[1] + SH, v[2]) for k_, v in J.items()}

# half-ring profiles, back seam -> front seam: (x as a fraction of W, h as a fraction of the half depth)
# poly pass 3: 10-vertex half rings (were 6); vertices 2..6 are the side band the limbs grow from (4 faces)
# dense fix pass 9: the 10-vertex torso ring lies ON the old 6-vertex plate polygon (corners kept as crisp ridges,
# the extra vertices on its edges), so the doubled faces stay co-planar plates instead of rounded bands
_T6 = [(0, 1), (0.75, 0.88), (1, 0.1), (0.88, -0.6), (0.5, -0.92), (0, -1)]
_m = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
TORSO = [_T6[0], _m(_T6[0], _T6[1]), _T6[1], _m(_T6[1], _T6[2]), _T6[2], _m(_T6[2], _T6[3]), _T6[3], _m(_T6[3], _T6[4]), _T6[4], _T6[5]]
TORSO6 = [(0, 1), (0.75, 0.88), (1, 0.1), (0.88, -0.6), (0.5, -0.92), (0, -1)]   # the old ring (belt path)
NECK = [(0, 1), (0.5, 0.92), (0.8, 0.72), (0.96, 0.4), (1, 0.0), (0.96, -0.38), (0.82, -0.7), (0.58, -0.88), (0.3, -0.97), (0, -1)]
HELM = [(0, 1), (0.5, 0.95), (0.8, 0.8), (0.97, 0.45), (1, 0.05), (0.95, -0.32), (0.86, -0.58), (0.5, -0.92), (0.24, -0.985), (0, -1)]


def tb(nm, back, front, W, prof):
    """A ring from its back and front seam points (y, z) read off reference/side.png, W from the front view."""
    (yt, zt), (yb, zb) = back, front
    c = ((yt + yb) / 2 + SH, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


# the spine loft, crotch -> crown
SECS = [
    tb('R0', (0.06, 0.50), (-0.10, 0.50), 0.06, TORSO),       # crotch
    tb('R0b', (0.11, 0.56), (-0.145, 0.56), 0.15, TORSO),     # * leg root mid (the leg grows from R0-R0b-R1)
    tb('R1', (0.14, 0.62), (-0.175, 0.62), 0.205, TORSO),     # hips (faulds)
    tb('R1b', (0.145, 0.70), (-0.195, 0.70), 0.228, TORSO),   # * fauld flare
    tb('R2', (0.13, 0.78), (-0.20, 0.78), 0.23, TORSO),       # belly
    tb('R2b', (0.115, 0.865), (-0.205, 0.865), 0.222, TORSO), # * belly into the belt
    tb('R3', (0.10, 0.95), (-0.21, 0.95), 0.225, TORSO),      # waist / belt
    tb('R3b', (0.10, 1.04), (-0.228, 1.04), 0.262, TORSO),    # * rib cage flare
    tb('R4', (0.11, 1.13), (-0.245, 1.13), 0.30, TORSO),      # breastplate
    tb('R4b', (0.115, 1.215), (-0.25, 1.215), 0.31, TORSO),   # * chest fullest (the arm grows from R4-R4b-R5)
    tb('R5', (0.105, 1.30), (-0.235, 1.30), 0.305, TORSO),    # shoulders
    tb('R5b', (0.09, 1.37), (-0.205, 1.365), 0.30, TORSO),    # * shoulder round-over
    tb('R6', (0.065, 1.43), (-0.17, 1.415), 0.27, TORSO),     # shoulder top / cowl
    tb('R6b', (0.05, 1.47), (-0.14, 1.46), 0.20, TORSO),      # * cowl slope neck -> shoulder (front trace line)
    tb('N0', (0.04, 1.50), (-0.12, 1.49), 0.135, NECK),       # gorget
    tb('H0', (0.08, 1.56), (-0.18, 1.55), 0.11, HELM),        # helmet rim
    tb('H0b', (0.088, 1.595), (-0.188, 1.592), 0.114, HELM),  # * cheek
    tb('H1', (0.09, 1.635), (-0.19, 1.635), 0.115, HELM),     # face plate
    tb('H2', (0.085, 1.705), (-0.175, 1.705), 0.108, HELM),   # visor line
    tb('H2b', (0.072, 1.74), (-0.148, 1.742), 0.096, HELM),   # * dome shoulder
    tb('H3', (0.05, 1.768), (-0.11, 1.772), 0.076, HELM),     # dome
    tb('H3b', (0.03, 1.79), (-0.075, 1.792), 0.052, HELM),    # * dome round-over
    tb('H4', (0.01, 1.803), (-0.04, 1.803), 0.026, HELM),     # crown
]
# fix pass 2 (base change, re-locked): the helm 1.12x about its rim centre, so it holds its own against the pauldrons
HS, HZ, HY = 1.12, 1.555, -0.05 + SH
SECS = [(n, ((c[0] - HY) * HS + HY, (c[1] - HZ) * HS + HZ), a, T * HS, B * HS, W * HS, p) if n[0] == 'H' else (n, c, a, T, B, W, p)
        for (n, c, a, T, B, W, p) in SECS]

# limb sections: (centre, r1, r2); ring points at c + e1 r1 cos(t) + e2 r2 sin(t)
# poly pass 3: 12-vertex round limb rings (were hexagons), 11 sections each (were 6 / 7), re-read off the traces
LEG = [((0.172, -0.01, 0.48), 0.105, 0.145),     # thigh top
       ((0.19, -0.005, 0.43), 0.11, 0.14),       # thigh
       ((0.208, 0.0, 0.375), 0.112, 0.132),      # knee (fix 9: radii smoothed, one straight greave taper)
       ((0.218, 0.012, 0.315), 0.106, 0.124),    # below the knee
       ((0.228, 0.03, 0.25), 0.099, 0.116),      # calf
       ((0.233, 0.03, 0.215), 0.095, 0.112),     # lower calf
       ((0.238, 0.03, 0.18), 0.091, 0.108),      # ankle (no pinch: a plate greave)
       ((0.245, 0.03, 0.12), 0.089, 0.108),      # ankle cuff
       ((0.25, -0.035, 0.065), 0.088, 0.185),    # sabaton top
       ((0.25, -0.048, 0.025), 0.092, 0.21),     # sabaton
       ((0.25, -0.045, 0.0), 0.09, 0.21)]        # sole
ARM = [((0.385, -0.035, 1.215), 0.085, 0.10),   # shoulder: grows out-down from the side band (no armpit fold)
       ((0.405, -0.025, 1.15), 0.09, 0.095),     # deltoid
       ((0.425, -0.018, 1.09), 0.086, 0.091),    # upper arm (fix 9: radii smoothed, straight rerebrace)
       ((0.44, -0.02, 1.03), 0.083, 0.088),      # above the elbow
       ((0.452, -0.022, 0.97), 0.083, 0.088),    # elbow
       ((0.46, -0.027, 0.90), 0.084, 0.089),     # vambrace
       ((0.463, -0.03, 0.865), 0.082, 0.087),    # forearm
       ((0.466, -0.032, 0.83), 0.078, 0.083),    # cuff
       ((0.47, -0.035, 0.77), 0.056, 0.06),      # wrist
       ((0.472, -0.04, 0.70), 0.048, 0.072),     # gauntlet
       ((0.465, -0.045, 0.635), 0.034, 0.055)]    # fingertips
LEG = [((c[0], c[1] + SH, c[2]), r1, r2) for c, r1, r2 in LEG]
ARM = [((c[0], c[1] + SH, c[2]), r1, r2) for c, r1, r2 in ARM]


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def leg_frames():
    return [(Vector(c), Vector((1, 0, 0)), Vector((0, 1, 0)), r1, r2) for c, r1, r2 in LEG]


def arm_frames():
    cs = [Vector(J['shoulder'])] + [Vector(c) for c, _, _ in ARM]
    out = []
    for i, (c, r1, r2) in enumerate(ARM):
        d = (cs[min(i + 2, len(cs) - 1)] - cs[i]).normalized()
        e2 = Vector((0, 1, 0)); e2 = (e2 - d * e2.dot(d)).normalized()
        out.append((Vector(c), d.cross(e2).normalized(), e2, r1, r2))
    return out


def lpos(fr, role):
    """A limb ring point: boundary role ('b', angle) on the section ellipse (angle 0 = +e1), interior ('i', f)."""
    c, e1, e2, r1, r2 = fr
    if role[0] == 'b':
        # dense fix pass 9: the 12 ring points sit on a hexagon (corners every 60 deg, the extra points on the edge
        # middles), so each limb is flat plate facets with crisp ridges, as before3, at twice the density
        t = round(role[1] / (math.pi / 6)) * (math.pi / 6)
        u = (t % (math.pi / 3)) - math.pi / 6
        r = math.cos(math.pi / 6) / math.cos(u)
        return c + e1 * r1 * r * math.cos(t) + e2 * r2 * r * math.sin(t)
    return c + e2 * r2 * role[1]


def region_roles(faces):
    """Poly pass 3: roles for a side-band face region (4 profile faces x 2 station spans, 12 boundary vertices).
    Upper station -> +e1, back (+y) -> +e2, as the hexagon roles were; even angles, best-fit rotation."""
    fs = set(faces)
    vs = {v for f in faces for v in f.verts}
    bnd = [v for v in vs if not all(f in fs for f in v.link_faces)]
    inn = [v for v in vs if v not in bnd]
    c = sum((v.co for v in bnd), Vector()) / len(bnd)
    ez = max(v.co.z for v in bnd) - min(v.co.z for v in bnd)
    ey = max(v.co.y for v in bnd) - min(v.co.y for v in bnd)
    ang = {v: math.atan2((v.co.y - c.y) / ey, (v.co.z - c.z) / ez) for v in bnd}
    order = sorted(bnd, key=lambda v: (ang[v], v.co.x, v.co.y, v.co.z))
    n = len(order); st = 2 * math.pi / n
    sx = sum(math.cos(ang[v] - i * st) for i, v in enumerate(order))
    sy = sum(math.sin(ang[v] - i * st) for i, v in enumerate(order))
    base = math.atan2(sy, sx)
    roles = [(v.co.copy(), ('b', base + i * st)) for i, v in enumerate(order)]
    roles += [(v.co.copy(), ('i', 0.8 * (v.co.y - c.y) / ey)) for v in inn]
    return roles


def grow(bm, faces, frames):
    """Extrude a face region frame by frame; each new vertex keeps the role of the vertex it came from."""
    roles = region_roles(faces)
    for fr in frames:
        r = extrude(bm, faces)
        new = [(v, min(roles, key=lambda o: (o[0] - v.co).length)[1]) for v in r['verts']]
        for v, role in new:
            v.co = lpos(fr, role)
        faces = r['faces']
        roles = [(v.co.copy(), role) for v, role in new]
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(nm, frames):
        i = idx[nm]                 # poly pass 3: spans i, i+1 (rings i -> i+2), side faces 2..5
        grow(bm, [spans[j][q] for j in (i, i + 1) for q in (2, 3, 4, 5)], frames)

    limb('R0', leg_frames())
    limb('R4', arm_frames())
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
def visor_face_centre():
    A, B_ = P('H1'), P('H2')
    return (A[6] + A[7] + B_[6] + B_[7]) / 4


VISOR = {}


def keep_visor(c):
    v0 = visor_face_centre()
    return abs(abs(c.x) - v0.x) < 0.04 and abs(c.y - v0.y) < 0.04 and abs(c.z - v0.z) < 0.04


def stage2(k, body):
    """Joint rings (shoulder, elbow, wrist, hip, knee, waist, neck) and the visor slit (the eye socket of a helm)."""
    k.meta['keep_valleys'] = keep_visor
    bm = edit(body)
    recalc_normals(bm)
    mid = lambda a, b: tuple((a + b) / 2)
    af, lf = arm_frames(), leg_frames()
    def lmid(fa, fb):               # poly pass 3: midpoint of a real longitudinal edge between two limb sections
        va = vert_near(bm, lpos(fa, ('b', 0.0)))
        vb = min((e.other_vert(va) for e in va.link_edges), key=lambda v: (v.co - lpos(fb, ('b', 0.0))).length)
        return tuple((va.co + vb.co) / 2)
    # poly pass 3: the joint rings re-aimed at the new sections
    cuts = [('elbow ring: the elbow bend', lambda: lmid(af[3], af[4])),
            ('shoulder ring: the arm swing', lambda: lmid(af[0], af[1])),
            ('wrist ring: the wrist bend', lambda: lmid(af[8], af[9])),
            ('knee ring: the knee bend', lambda: lmid(lf[2], lf[3])),
            ('hip ring: the leg swing', lambda: lmid(lf[0], lf[1])),
            ('waist ring: the spine bend', lambda: mid(P('R2b')[0], P('R3')[0])),
            ('neck ring: the head nod', lambda: mid(P('N0')[0], P('H0')[0]))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_()), t=0.5)
    v0 = visor_face_centre()
    f = face_near(bm, v0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'visor slit: a ring in the face-plate face, squeezed to a slot and pushed in'):
        inner = inset(bm, [f], 0.22, 0.0)
    vs = list(inner[0].verts)
    c = sum((v.co for v in vs), Vector()) / len(vs)
    for v in vs:
        v.co.z = c.z + (v.co.z - c.z) * 0.3
    move(vs, -fn * 0.014)
    VISOR['floor'] = c - fn * 0.014
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'steel': '#9aa1aa', 'mail': '#3a3e45', 'blue': '#2d4677', 'leather': '#6a4329', 'bright': '#cfd3d8',
       'brass': '#b9934a'}


def body_rule(c, n, i):
    vf = visor_face_centre()
    fl = Vector((vf.x, vf.y, vf.z)) + (VISOR.get('floor', vf) - vf)
    if (Vector((abs(c.x), c.y, c.z)) - fl).length < 0.016:
        return 'mail'                                   # the visor slit
    if 1.47 < c.z < 1.56 and abs(c.x) < 0.16:
        return 'mail'                                   # gorget shadow under the helm
    if 1.38 < c.z < 1.50 and abs(c.x) < 0.27 and n.z > 0.15:
        return 'blue'                                   # the cowl of the cape over the shoulders
    return 'steel'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def box_chain(bm, rows):
    """A closed tube through rows of 4 points each: end caps + side quads."""
    R = [[bm.verts.new(Vector(p)) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def sq(c, u, w, su, sw):
    return [c - u * su - w * sw, c + u * su - w * sw, c + u * su + w * sw, c - u * su + w * sw]


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def ray_y(tree, x, z, from_front=True):
    o = Vector((x, -1.0 if from_front else 1.0, z))
    hit = tree.ray_cast(o, Vector((0, 1 if from_front else -1, 0)), 2.0)[0]
    return hit.y if hit is not None else None


def plate(bm, cols, th, front):
    """A solid cloth plate from columns of points (x >= 0, top -> hem), the second sheet th behind (toward the
    body); the x = 0 column is the seam (the mirror closes it). front: the plate faces -y."""
    sgn = 1 if front else -1
    O = [[bm.verts.new(Vector(p)) for p in c] for c in cols]
    I = [[bm.verts.new(Vector((p[0], p[1] + sgn * th, p[2]))) for p in c] for c in cols]
    nr = len(cols[0])
    for i in range(len(cols) - 1):
        for r in range(nr - 1):
            q = [O[i][r], O[i + 1][r], O[i + 1][r + 1], O[i][r + 1]]
            bm.faces.new(q)
            q = [I[i][r + 1], I[i + 1][r + 1], I[i + 1][r], I[i][r]]
            bm.faces.new(q)
    for r in range(nr - 1):                   # outer side edge
        bm.faces.new((O[-1][r], O[-1][r + 1], I[-1][r + 1], I[-1][r]))
    for i in range(len(cols) - 1):            # top and hem
        bm.faces.new((O[i + 1][0], O[i][0], I[i][0], I[i + 1][0]))
        bm.faces.new((O[i][-1], O[i + 1][-1], I[i + 1][-1], I[i][-1]))
    recalc_normals(bm)


def tabard(tree):
    """The blue tabard: rooted in the belly under the belt, hanging flat in front of the thighs to a pointed hem."""
    xs = [0.0, 0.065, 0.13]
    hem = [0.45, 0.48, 0.52]
    ymin = min(ray_y(tree, max(x, 0.002), z) or 0.0 for x in xs for z in (0.90, 0.80, 0.70, 0.62))
    yo = ymin - 0.02
    cols = []
    for x, zh in zip(xs, hem):
        yr = ray_y(tree, max(x, 0.002), 0.95)
        cols.append([(x, yr + 0.006, 0.95), (x, yo, 0.90), (x, yo, 0.70), (x, yo, zh)])
    bm = bmesh.new()
    plate(bm, cols, 0.026, True)
    return bm


def cape_y(x, z):
    """The cape's outer surface: hanging back off the shoulders, wrapping forward a little at its sides."""
    zs = [(1.36, 0.165), (1.10, 0.215), (0.85, 0.25), (0.62, 0.27)]
    if z >= zs[0][0]:
        y = zs[0][1]
    elif z <= zs[-1][0]:
        y = zs[-1][1]
    else:
        for (z0, y0), (z1, y1) in zip(zs, zs[1:]):
            if z1 <= z <= z0:
                y = y0 + (y1 - y0) * (z0 - z) / (z0 - z1)
    return y - 0.06 * (x / 0.32) ** 2


def cape(tree):
    rows = [1.45, 1.36, 1.10, 0.85, 0.62]
    xs_root = [0.0, 0.06, 0.12, 0.17, 0.20]
    xs = [0.0, 0.10, 0.19, 0.26, 0.31]
    xs_low = [0.0, 0.11, 0.21, 0.28, 0.33]
    cols = []
    for j in range(len(xs)):
        col = []
        yr = ray_y(tree, max(xs_root[j], 0.002), rows[0], from_front=False)
        col.append((xs_root[j], (yr if yr is not None else 0.0) - 0.008, rows[0]))
        for z in rows[1:]:
            x = xs[j] if z > 1.0 else xs_low[j]
            col.append((x, cape_y(x, z), z))
        cols.append(col)
    bm = bmesh.new()
    plate(bm, cols, 0.035, False)
    return bm


def shield(bm):
    """The round shield on the back: a 12-sided disc (half here, the mirror closes it) lying on the cape, with a
    steel rim ring and a domed boss."""
    zc, R = 1.10, 0.27
    yb = cape_y(0.0, zc) - 0.006                     # back plane inside the cape plate (rooted once)
    th = 0.09                                         # fix pass 2: a real board, standing off the cape
    tilt = (cape_y(0.0, zc - 0.2) - cape_y(0.0, zc + 0.2)) / 0.4     # dy/d(-z) of the cape

    def P3(x, z, off):
        return Vector((x, yb + off + tilt * (zc - z), z))
    angs = [math.radians(90 - 30 * j) for j in range(7)]             # top (seam) -> bottom (seam)
    rings = []
    for rr in (R, R * 0.86):
        rings.append([(rr * math.cos(a) if j not in (0, 6) else 0.0, zc + rr * math.sin(a)) for j, a in enumerate(angs)])
    RIM = 0.014                                                     # raised rim lip
    Fo = [bm.verts.new(P3(x, z, th + RIM)) for x, z in rings[0]]
    Fh = [bm.verts.new(P3(x, z, th + RIM)) for x, z in rings[1]]
    Fi = [bm.verts.new(P3(x, z, th)) for x, z in rings[1]]
    Bo = [bm.verts.new(P3(x, z, 0.0)) for x, z in rings[0]]
    cf, cb = bm.verts.new(P3(0.0, zc, th)), bm.verts.new(P3(0.0, zc, 0.0))
    for j in range(6):
        bm.faces.new([Fo[j], Fh[j], Fh[j + 1], Fo[j + 1]])          # rim ring (front, raised)
        bm.faces.new([Fh[j], Fi[j], Fi[j + 1], Fh[j + 1]])          # rim inner wall
        bm.faces.new([Fi[j], cf, Fi[j + 1]])                          # boards
        bm.faces.new([Bo[j + 1], cb, Bo[j]])                          # back
        bm.faces.new([Bo[j], Fo[j], Fo[j + 1], Bo[j + 1]])            # edge
    # boss: a hexagonal dome on the front
    bc = P3(0.0, zc, th - 0.01)
    n = Vector((0, 1, tilt)).normalized()
    up = Vector((0, -tilt, 1)).normalized()
    side = Vector((1, 0, 0))
    r0, r1 = 0.10, 0.06
    base = [bc + (side * math.cos(a) + up * math.sin(a)) * r0 for a in [math.radians(90 - 60 * j) for j in range(4)]]
    mid = [bc + n * 0.07 + (side * math.cos(a) + up * math.sin(a)) * r1 for a in [math.radians(90 - 60 * j) for j in range(4)]]
    for p in base + mid:
        if abs(p.x) < 1e-4:
            p.x = 0.0
    B_ = [bm.verts.new(p) for p in base]
    M_ = [bm.verts.new(p) for p in mid]
    top = bm.verts.new(bc + n * 0.095)
    bot = bm.verts.new(bc)
    for j in range(3):
        bm.faces.new([B_[j], B_[j + 1], M_[j + 1], M_[j]])
        bm.faces.new([M_[j], M_[j + 1], top])
        bm.faces.new([B_[j + 1], B_[j], bot])
    recalc_normals(bm)
    return (zc, R)


def belt(bm, tree):
    """The leather belt: a square tube round the waist ring (front seam -> back seam), its inner half sunk in the
    plate; it ends 4 mm off the seam so each side is one rooted piece."""
    # poly pass 3: the belt keeps its old path (the 6-point waist profile + midpoints), projected on the new surface
    n_, c_, a_, T_, B_, W_, _p = next(r for r in SECS if r[0] == 'R3')
    pts = [Vector(q) for q in sec_pts(c_, a_, T_, B_, W_, TORSO6)]
    cen = Vector((0.0, sum(p.y for p in pts) / len(pts), pts[0].z))
    path = []
    for j, p in enumerate(pts):
        p = p.copy()
        if j in (0, len(pts) - 1):
            p.x = 0.004
        path.append(p)
    dense = []
    for a, b in zip(path, path[1:]):
        dense += [a, a.lerp(b, 0.5)]
    dense.append(path[-1])
    rows = []
    for p in dense:
        n = Vector((p.x, p.y - cen.y, 0.0)).normalized()
        loc, fn, _i, _d = tree.find_nearest(p)
        rows.append(sq(loc + n * 0.006, n, Vector((0, 0, 1)), 0.013, 0.024))
    box_chain(bm, rows)


SWORD = dict(guard=Vector((0.29, -0.24, 0.96)), tip=Vector((0.375, 0.09, 0.42)))


def sword(bm):
    """The sheathed sword on the left hip: a scabbard hanging back-down from a strap on the belt, the crossguard,
    grip and pommel standing forward-up in front of the hip."""
    G, T = SWORD['guard'], SWORD['tip']
    d = (G - T).normalized()                         # tip -> guard
    X = Vector((1, 0, 0))
    u = d.cross(X).normalized()                      # the blade's broad side lies in the y-z plane
    w = u.cross(d).normalized()
    L = (G - T).length
    rows = [sq(G - d * 0.01, u, w, 0.036, 0.018)] + [sq(G - d * L * t, u, w, (0.038 if t < 0.3 else 0.05) - 0.012 * t, 0.021 - 0.003 * t)
            for t in (0.2, 0.4, 0.6, 0.8)] + [sq(T + d * 0.05, u, w, 0.034, 0.014), sq(T, u, w, 0.016, 0.009)]
    box_chain(bm, rows)
    # crossguard: a bar across the blade (along x), on the scabbard mouth
    gc = G + d * 0.004
    box_chain(bm, [sq(gc - X * 0.065, u, d, 0.014, 0.012), sq(gc + X * 0.065, u, d, 0.014, 0.012)])
    # grip and pommel
    box_chain(bm, [sq(G + d * 0.005, u, w, 0.012, 0.012), sq(G + d * 0.15, u, w, 0.011, 0.011)])
    pc = G + d * 0.165
    box_chain(bm, [sq(pc - d * 0.02, u, w, 0.018, 0.018), sq(pc + d * 0.02, u, w, 0.018, 0.018)])
    # strap: from the belt into the scabbard mouth
    b0 = Vector((0.205, -0.135, 0.95))
    b1 = G - d * 0.05
    e = (b1 - b0).normalized()
    s1 = Vector((0, 0, 1)); s1 = (s1 - e * s1.dot(e)).normalized(); s2 = e.cross(s1)
    box_chain(bm, [sq(b0, s1, s2, 0.016, 0.006), sq(b1, s1, s2, 0.016, 0.006)])


def pauldron(bm):
    """A flared shoulder plate: three rows across the shoulder, from the collar out over the arm top, flaring down."""
    yc = -0.005 + SH
    Y = Vector((0, 1, 0))
    rows = [sq(Vector((0.21, yc, 1.40)), Y, Vector((0, 0, 1)), 0.085, 0.028),
            sq(Vector((0.31, yc, 1.395)), Y, Vector((0.3, 0, 1)).normalized(), 0.12, 0.035),
            sq(Vector((0.40, yc, 1.33)), Y, Vector((0.8, 0, 1)).normalized(), 0.115, 0.03),
            sq(Vector((0.445, yc, 1.235)), Y, Vector((1, 0, 0.35)).normalized(), 0.085, 0.022)]
    box_chain(bm, rows)


def knee_cop(bm, tree):
    """A flared knee plate standing proud of the knee front."""
    x, z = 0.205, 0.37
    yf = ray_y(tree, x, z) or (-0.16 + SH)
    Y, Z, Xa = Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
    box_chain(bm, [sq(Vector((x, yf + 0.03, z)), Xa, Z, 0.06, 0.055),
                   sq(Vector((x, yf - 0.01, z)), Xa, Z, 0.058, 0.05),
                   sq(Vector((x, yf - 0.025, z + 0.005)), Xa, Z, 0.03, 0.03)])


def visor_ridge(bm, tree):
    """The visor's prow: a horizontal steel bar across the helm front, just under the slit."""
    z = visor_face_centre().z - 0.032
    xs = [0.004, 0.04, 0.075, 0.10]
    pts = [Vector((x, ray_y(tree, x, z), z)) for x in xs]
    rows = [sq(p + Vector((0, -0.006, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.014, 0.011) for p in pts]
    box_chain(bm, rows)


def crest(bm):
    """A thin crest fin along the helm crown, front to back (one unmirrored piece on the midline)."""
    c = Vector((0.0, HY, (1.66 - HZ) * HS + HZ))
    path = [(-0.20, 1.72), (-0.12, 1.79), (-0.03, 1.815), (0.05, 1.78), (0.09, 1.71)]
    rows = []
    for y, z in path:
        p = Vector((0.0, (y + SH - HY) * HS + HY, (z - HZ) * HS + HZ))
        n = (p - c).normalized()
        rows.append(sq(p + n * 0.012, Vector((1, 0, 0)), n, 0.009, 0.026))
    box_chain(bm, rows)


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('steel', 'mail', 'blue')}, body_rule)
    tree = body_bvh(body)
    to = object_from_bm('tabard', tabard(tree))
    paint(to, {'blue': PAL['blue'], 'bright': PAL['bright']},
          lambda c_, n_, i: 'blue')
    co = object_from_bm('cape', cape(tree))
    paint(co, {'blue': PAL['blue']}, lambda c_, n_, i: 'blue')
    bm = bmesh.new()
    zc, R = shield(bm)
    so = object_from_bm('shield', bm)
    paint(so, {'blue': PAL['blue'], 'bright': PAL['bright'], 'steel': PAL['steel']},
          lambda c_, n_, i: 'steel' if (Vector((c_.x, 0, c_.z - zc)).length > R * 0.84 or Vector((c_.x, 0, c_.z - zc)).length < 0.105)
          else ('blue' if n_.y > 0.3 else 'steel'))
    bm = bmesh.new()
    belt(bm, tree)
    bo = object_from_bm('belt', bm)
    paint(bo, {'leather': PAL['leather'], 'brass': PAL['brass']},
          lambda c_, n_, i: 'brass' if abs(c_.x) < 0.035 and c_.y < -0.1 else 'leather')
    bm = bmesh.new()
    sword(bm)
    wo = object_from_bm('sword', bm, mirror=False)
    G = SWORD['guard']
    paint(wo, {'leather': PAL['leather'], 'bright': PAL['bright'], 'brass': PAL['brass']},
          lambda c_, n_, i: 'brass' if (c_ - G).dot((G - SWORD['tip']).normalized()) > -0.002 else 'leather')
    bm = bmesh.new(); pauldron(bm)
    po = object_from_bm('pauldron', bm)
    bm = bmesh.new(); knee_cop(bm, tree)
    ko = object_from_bm('knee_cop', bm)
    bm = bmesh.new(); visor_ridge(bm, tree)
    vo = object_from_bm('visor_ridge', bm)
    bm = bmesh.new(); crest(bm)
    cro = object_from_bm('crest', bm, mirror=False)
    for o in (po, ko, vo, cro):
        paint(o, {'bright': PAL['bright']}, lambda c_, n_, i: 'bright')
    return [to, co, so, bo, wo, po, ko, vo, cro]


# ---------------------------------------------------------------- stage 4
def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['crown'], 'neck', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:                     # the sheathed sword hangs rigid from the belt (hips)
        bind(p, rig, bone='hips') if 'sword' in p.name else bind(p, rig, body=body)
    # idle: breathing, a slow look around, the arms sway a little
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, 6), 'upperarm.L': (2, 0, 0), 'upperarm.R': (-2, 0, 0)},
                       24: {}, 36: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, -6), 'upperarm.L': (-2, 0, 0), 'upperarm.R': (2, 0, 0)}, 48: {}})
    # move: a heavy armoured walk; legs swing in opposition, the knee folds on the swinging leg, arms counter-swing
    A, S = 20, 12
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 3, 0)},
        9: {'thigh.R': (5, 0, 0), 'shin.R': (-30, 0, 0), 'foot.R': (12, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0), 'spine': (0, -3, 0)},
        25: {'thigh.L': (5, 0, 0), 'shin.L': (-30, 0, 0), 'foot.L': (12, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 3, 0)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.015, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.015, 0)}, 33: {'hips': (0, 0, 0)}})
    # attack: wind the right gauntlet back, then a forward hammer blow with a lean into it
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (-5, 0, 0), 'upperarm.R': (-35, 0, 0), 'forearm.R': (30, 0, 0), 'head': (-4, 0, 0)},
        18: {'chest': (10, 0, 0), 'spine': (4, 0, 0), 'upperarm.R': (60, 0, 0), 'forearm.R': (10, 0, 0), 'head': (5, 0, 0),
             'upperarm.L': (-8, 0, 0)},
        24: {'chest': (7, 0, 0), 'upperarm.R': (40, 0, 0), 'head': (3, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
