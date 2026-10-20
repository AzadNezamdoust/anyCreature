import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# ogre (biped), t7 hand box-model: ONE spine loft of 6-vertex half rings standing upright (crotch -> skull top),
# legs extruded as 2-face regions from the crotch-hip span, arms as 2-face regions from the shoulder span,
# ears as 1-face extrusions. Coordinates from blueprint.json (refs.py, side and front views; the sheet's top is turned).
META = dict(creature='ogre', model='opus', stage1_tris=(1500, 3200), total_tris=(2800, 5000),
            closeups=[('head', (0.0, -0.25, 1.86), 0.30, 'hero'),
                      ('hand', (0.84, 0.05, 0.62), 0.22, 'hero'),
                      ('foot', (0.37, -0.05, 0.08), 0.24, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.07, 0.74), spine=(0.0, 0.05, 1.05), chest=(0.0, 0.07, 1.40), neck=(0.0, 0.06, 1.62),
    head=(0.0, -0.10, 1.73), top=(0.0, -0.13, 2.06),
    shoulder=(0.56, 0.20, 1.45), elbow=(0.79, 0.20, 1.02), wrist=(0.86, 0.08, 0.72), hand=(0.87, 0.03, 0.48),
    hipL=(0.30, 0.08, 0.66), knee=(0.33, 0.10, 0.40), ankle=(0.34, 0.12, 0.13), toe=(0.37, -0.27, 0.03),
)

# half-ring profiles, front seam -> back seam: (x as a fraction of W, position from the front (1) to the back (-1))
# poly pass 3: 14-vertex half rings (was 6), round sections with the widest point a little forward of centre
def _prof(e, w=0.25, n=14):
    out = []
    for i in range(n):
        t = math.pi * i / (n - 1)
        c = math.cos(t)
        out.append((0.0 if i in (0, n - 1) else round(math.sin(t) ** e, 4), round(c + w * (1 - c * c), 4)))
    return out
BODY = _prof(0.85)
HIP = _prof(0.75)
HEAD = _prof(0.9)

# the loft, bottom -> top: (name, z, front y, back y, half-width W, profile), read off reference/side.png + front.png
SECS = [
    ('L0', 0.60, -0.12, 0.28, 0.14, HIP),      # crotch
    ('L1', 0.72, -0.40, 0.47, 0.52, HIP),      # hips / belly underside
    ('B0a', 0.79, -0.53, 0.48, 0.545, BODY),   # poly pass 3: belly underside curve
    ('B0', 0.86, -0.61, 0.48, 0.56, BODY),
    ('B1', 0.95, -0.65, 0.46, 0.56, BODY),     # belly at its widest
    ('B1b', 1.04, -0.645, 0.44, 0.555, BODY),
    ('B2a', 1.12, -0.60, 0.445, 0.53, BODY),   # belly top rolling in
    ('B2', 1.20, -0.53, 0.46, 0.51, BODY),
    ('C0', 1.35, -0.37, 0.50, 0.50, BODY),     # chest; back toward the sheet's 0.52 hump
    ('C1', 1.50, -0.25, 0.515, 0.48, BODY),    # shoulders
    ('C2a', 1.56, -0.20, 0.50, 0.46, BODY),    # trapezius slope
    ('C2', 1.61, -0.16, 0.46, 0.42, BODY),     # trapezius
    ('N0', 1.66, -0.30, 0.38, 0.31, HEAD),     # under the jaw
    ('H0', 1.72, -0.32, 0.30, 0.21, HEAD),     # lower jaw
    ('H0b', 1.76, -0.335, 0.24, 0.205, HEAD),  # mouth
    ('H1', 1.80, -0.34, 0.17, 0.20, HEAD),     # nose / upper lip
    ('H2', 1.87, -0.31, 0.12, 0.18, HEAD),     # brow
    ('H2b', 1.905, -0.27, 0.09, 0.185, HEAD),  # forehead
    ('H3', 1.94, -0.22, 0.06, 0.18, HEAD),
    ('H3b', 1.97, -0.165, 0.03, 0.15, HEAD),   # skull dome
    ('H4', 1.99, -0.10, 0.00, 0.11, HEAD),     # skull top
]
# fix pass (zoo reviews): the head was small and sunk. Head rings scaled 1.2x about the neck (z 1.66), 1.15x deep,
# moved 2.5 cm forward; the lower jaw (H0) projects a further 2.5 cm forward. Stage 1 re-locked.
HS, HD, HF, HZ0, HY0 = 1.2, 1.15, -0.025, 1.66, -0.06
hz = lambda z: HZ0 + (z - HZ0) * HS
hy = lambda y: HY0 + (y - HY0) * HD + HF
SECS = [(n, hz(z), hy(yf) - (0.05 if n == 'H0' else 0.0), hy(yb), W * HS, p) if n[0] == 'H' else (n, z, yf, yb, W, p)
        for (n, z, yf, yb, W, p) in SECS]

# limb sections: (centre xyz, rx, ry[, dz]) - horizontal hexagons; dz tilts the ring (outer side up for dz < 0)
# poly pass 3: 10-sided rings (4-face roots), more stations at the thigh, knee, calf, deltoid, elbow and forearm
LEG = [((0.30, 0.06, 0.60), 0.22, 0.26, -0.04), ((0.315, 0.08, 0.51), 0.215, 0.265), ((0.322, 0.09, 0.465), 0.21, 0.26), ((0.33, 0.10, 0.42), 0.20, 0.25),
       ((0.335, 0.11, 0.35), 0.185, 0.24), ((0.34, 0.12, 0.28), 0.18, 0.235), ((0.34, 0.12, 0.24), 0.172, 0.226), ((0.34, 0.12, 0.20), 0.16, 0.215),
       ((0.34, 0.12, 0.14), 0.14, 0.20), ((0.355, 0.08, 0.10), 0.17, 0.25), ((0.37, 0.03, 0.06), 0.20, 0.30),
       ((0.38, 0.03, 0.0), 0.20, 0.32)]
ARM = [((0.61, 0.20, 1.45), 0.13, 0.20, -0.06), ((0.67, 0.21, 1.34), 0.165, 0.215, -0.02), ((0.70, 0.215, 1.28), 0.172, 0.215), ((0.73, 0.22, 1.22), 0.17, 0.21),
       ((0.765, 0.215, 1.11), 0.16, 0.20), ((0.79, 0.20, 1.02), 0.165, 0.195), ((0.825, 0.17, 0.93), 0.19, 0.215),
       ((0.84, 0.15, 0.89), 0.188, 0.21), ((0.85, 0.13, 0.85), 0.18, 0.20), ((0.86, 0.10, 0.77), 0.13, 0.15), ((0.86, 0.08, 0.72), 0.10, 0.115),
       ((0.865, 0.05, 0.67), 0.19, 0.22), ((0.87, 0.03, 0.60), 0.21, 0.24), ((0.88, 0.02, 0.49), 0.17, 0.20)]
LEG_ROOT, ARM_ROOT, EAR_FACE, EYE_J = 4, 6, 7, 1   # fix pass 2: arms x1.2-1.3 thick, forearm bulk, wrist taper, bigger fist   # fix pass: wrist tapered, fists bigger
# ear: flat plates in the y-z plane (centre, half-height, half-depth), pointing up and out
EAR = [((0.21 * HS, hy(0.025), hz(1.875)), 0.04, 0.04), ((0.24 * HS, hy(0.035), hz(1.96)), 0.007, 0.007)]


def sec_pts(z, yf, yb, W, prof):
    yc, h = (yf + yb) / 2, (yb - yf) / 2
    return [(fx * W, yc - fh * h, z) for fx, fh in prof]


def P(nm):
    for (n, z, yf, yb, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(z, yf, yb, W, p)]


def hexpos(sec, a, b, corner=0.55):
    """a: -1 inner (toward the body), +1 outer; b: -1 front, 0 middle, +1 back."""
    c, rx, ry = sec[0], sec[1], sec[2]
    dz = sec[3] if len(sec) > 3 else 0.0
    k = corner if abs(b) > 0.99 else (0.9 if abs(b) > 0.3 else 1.0)   # poly pass 3: 10-sided ring
    return (c[0] + a * rx * k, c[1] + b * ry, c[2] - a * dz)


def earpos(sec, a, b):
    c, hz, hy = sec
    return (c[0], c[1] + b * hy, c[2] + a * hz)


def grow(bm, faces, roles, secs, pos):
    """Extrude a face region section by section; each new vertex keeps the role of the vertex it came from."""
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (a, b) in new.items():
            v.co = Vector(pos(sec, a, b))
        faces, roles = r['faces'], new
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(z, yf, yb, W, p)) for (nm, z, yf, yb, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(span, j0, secs, pos):
        """Faces j0, j0+1 of the span above ring `span`: lower ring -> inner side, upper ring -> outer side."""
        i = idx[span]
        lo, up = rings[i], rings[i + 1]
        roles = {}
        for c in range(5):
            roles[lo[j0 + c]] = (-1, -1 + 0.5 * c); roles[up[j0 + c]] = (1, -1 + 0.5 * c)
        grow(bm, [spans[i][j0 + c] for c in range(4)], roles, secs, pos)

    limb('L0', LEG_ROOT, LEG, hexpos)
    limb('C0', ARM_ROOT, ARM, hexpos)
    i = idx['H1']
    lo, up = rings[i], rings[i + 1]
    e = EAR_FACE
    grow(bm, [spans[i][e]], {lo[e]: (-1, -1), lo[e + 1]: (-1, 1), up[e]: (1, -1), up[e + 1]: (1, 1)}, EAR, earpos)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    """Centre of the front face between H1 and H2 (seam to the front-side vertex): the eye socket."""
    A, B_ = P('H1'), P('H2')
    j = EYE_J
    return (A[j] + A[j + 1] + B_[j] + B_[j + 1]) / 4


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.045 and abs(c.y - ec0.y) < 0.04 and abs(c.z - ec0.z) < 0.05


def stage2(k, body):
    """Joint rings (knee, ankle, elbow, wrist, waist, neck), the eye socket, a heavy brow, nose and jaw planes."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ec0 = eye_face_centre()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    cuts = [('knee ring: the knee bend', mid(hexpos(LEG[3], 1, 0), hexpos(LEG[4], 1, 0))),
            ('ankle ring: the ankle bend', mid(hexpos(LEG[8], 1, 0), hexpos(LEG[9], 1, 0))),
            ('elbow ring: the elbow bend', mid(hexpos(ARM[5], 1, 0), hexpos(ARM[6], 1, 0))),
            ('shoulder ring: the arm swing', mid(hexpos(ARM[0], 1, 0), hexpos(ARM[1], 1, 0))),
            ('waist ring: the spine bend under the belly', mid(P('B1b')[0], P('B2a')[0])),
            ('neck ring: the head nod', mid(P('N0')[0], P('H0')[0]))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_), t=0.5)
    H0, H1, H2 = P('H0'), P('H1'), P('H2')
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the brow face, its floor pushed in'):
        inner = inset(bm, [f], 0.36, 0.0)
    move(list(inner[0].verts), -fn * 0.012)
    move([vert_near(bm, H2[j]) for j in range(3)], (0.0, -0.025, 0.0))        # heavy brow ridge forward
    move([vert_near(bm, H2[2])], (0.012, 0.0, 0.0))                            # brow corner out
    move([vert_near(bm, H1[0])], (0.0, -0.012, -0.01))                         # nose tip forward / down
    move([vert_near(bm, H0[j]) for j in range(3)], (0.0, -0.01, 0.0))          # under-bite jaw
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# colours read off the sheet: olive skin, tan belly and chest, brown leather, cream tusks and nails, dark eyes
PAL = {'skin': '#9aa07c', 'belly': '#d6c9a4', 'leather': '#6b5244', 'cream': '#e6dcc2', 'eye': '#1d1915',
       'mouth': '#4a4436'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if 0.74 < z < 1.30 and n.y < -0.45 and x < 0.38:   # fix pass 2: follows the bulged belly   # fix pass: a front patch, not a vest
        return 'belly'
    return 'skin'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 3 for k_ in range(6)]]
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def prism(bm, rows):
    """A closed tube through square rows (4 points each), capped at both ends."""
    R = [[bm.verts.new(Vector(p)) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R[:-1], R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def square(c, ax, s, up=Vector((0, 0, 1))):
    ax = Vector(ax).normalized()
    u = ax.cross(up)
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    w = u.cross(ax)
    su, sw = (s, s) if not isinstance(s, tuple) else s
    return [c + u * a * su + w * b * sw for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def full_bvh(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def hit(tree, o, d, far=3.0):
    loc, nrm, _i, _d = tree.ray_cast(Vector(o), Vector(d).normalized(), far)
    return loc, nrm


def band(tree, centre, e1, e2, half_w, n_seg, sink=0.01, out=0.022):
    """A closed strap around the body in the plane (e1, e2) through `centre`: for each angle, two rays (the strap's
    two edges, +-half_w along the plane normal) find the surface; the inner face is sunk, the outer face stands off."""
    e1, e2 = Vector(e1).normalized(), Vector(e2).normalized()
    nrm = e1.cross(e2).normalized()
    bm = bmesh.new()
    rows = []
    for s in range(n_seg):
        t = 2 * math.pi * s / n_seg
        d = e1 * math.cos(t) + e2 * math.sin(t)
        row = []
        for side in (-1, 1):
            o = Vector(centre) + nrm * side * half_w
            loc, fn = hit(tree, o, d)
            if loc is None:
                loc, fn = o + d * 0.4, d
            fn = (fn + d).normalized()
            sk = sink[side > 0] if isinstance(sink, tuple) else sink   # poly pass 3: (lower, upper) edge sink
            row += [loc - fn * sk, loc + fn * out]
        rows.append([bm.verts.new(p) for p in (row[0], row[1], row[3], row[2])])   # in-lo, out-lo, out-hi, in-hi
    for s in range(n_seg):
        a, b = rows[s], rows[(s + 1) % n_seg]
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    return bm


def flap(tree, cols, z_top, z_mid, bottoms, front):
    """A half loincloth flap (x >= 0, mirrored): the top row sunk in the body under the belt, then hanging,
    a jagged hem. Two layers 1.2 cm apart, closed on the hem and the outer side (the seam side meets its mirror)."""
    sgn = -1.0 if front else 1.0
    bm = bmesh.new()
    pts = []
    for x, zb in zip(cols, bottoms):
        loc, _n = hit(tree, (x, sgn * 1.5, z_top), (0, -sgn, 0))
        yt = (loc.y if loc is not None else sgn * 0.3) - sgn * 0.04   # s4 r3: sunk 4 cm, stays rooted when the thigh swings
        o1, o2 = (0.045, 0.02) if front else (0.07, 0.05)   # poly pass 3: back flap clears the rounder seat
        pts.append([(x, y_, z_) for y_, z_ in zip([yt, yt + sgn * o1, yt + sgn * o2], [z_top, z_mid, zb])])
    # s4 r7: vertices made row by row from the sunk top row down, so the seat (the first vertices) is the belt line
    F = [[None] * 3 for _ in cols]; Bk = [[None] * 3 for _ in cols]
    for r in range(3):
        for i, col in enumerate(pts):
            x, y_, z_ = col[r]
            F[i][r] = bm.verts.new((x, y_, z_))
            Bk[i][r] = bm.verts.new((x, y_ - sgn * 0.021, z_))   # fix pass: 30% thinner
    n = len(cols)
    for i in range(n - 1):
        for r in range(2):
            bm.faces.new([F[i][r], F[i + 1][r], F[i + 1][r + 1], F[i][r + 1]])
            bm.faces.new([Bk[i][r], Bk[i][r + 1], Bk[i + 1][r + 1], Bk[i + 1][r]])
        bm.faces.new([F[i][2], F[i + 1][2], Bk[i + 1][2], Bk[i][2]])     # hem
        bm.faces.new([F[i][0], Bk[i][0], Bk[i + 1][0], F[i + 1][0]])     # top (inside the body)
    for r in range(2):
        bm.faces.new([F[-1][r], F[-1][r + 1], Bk[-1][r + 1], Bk[-1][r]])  # outer side
    return bm


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('skin', 'belly')}, body_rule)
    tree = full_bvh(body)
    # eyes: small dark lenses on the socket floor
    ec = eye_face_centre()
    c, n, _i, _d = tree.find_nearest(ec + Vector((0, 0.012, 0)))
    n = n if n.y < 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.015, 0.008)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, lambda c_, n_, i: 'eye')
    # tusks: from inside the lower jaw, up and a little forward and out
    bm = bmesh.new()
    loc, _n = hit(tree, (0.135, -1.0, hz(1.70)), (0, 1, 0))
    b0 = loc + Vector((0, 0.012, -0.01))
    ax = Vector((0.12, -0.35, 1.0)).normalized()
    prism(bm, [square(b0, ax, 0.03, Vector((0, -1, 0))), square(b0 + ax * 0.07, ax, 0.025, Vector((0, -1, 0))),
               square(b0 + ax * 0.17, ax, 0.006, Vector((0, -1, 0)))])   # fix pass: thicker tusks
    tusks = object_from_bm('tusks', bm)
    paint(tusks, {'cream': PAL['cream']}, lambda c_, n_, i: 'cream')
    # toenails: four per foot on the foot front
    bm = bmesh.new()
    (cx, cy, _), rx, ry = LEG[5][:3]
    for d in (-0.085, -0.03, 0.025, 0.08):
        loc, _n = hit(tree, (cx + d, -1.0, 0.03), (0, 1, 0))
        if loc is None:
            continue
        x0, y0 = loc.x, loc.y
        prism(bm, [[(x0 - 0.022, y0 + 0.015, 0.004), (x0 + 0.022, y0 + 0.015, 0.004), (x0 + 0.022, y0 + 0.015, 0.042),
                    (x0 - 0.022, y0 + 0.015, 0.042)],
                   [(x0 - 0.02, y0 - 0.008, 0.004), (x0 + 0.02, y0 - 0.008, 0.004), (x0 + 0.018, y0 - 0.008, 0.034),
                    (x0 - 0.018, y0 - 0.008, 0.034)]])
    nails = object_from_bm('nails', bm)
    paint(nails, {'cream': PAL['cream']}, lambda c_, n_, i: 'cream')
    # belt: a band round the hips, just under the belly
    belt = object_from_bm('belt', band(tree, (0.0, 0.07, 0.80), (1, 0, 0), (0, 1, 0), 0.04, 32, sink=(0.01, -0.004), out=0.03), mirror=False)   # poly pass 3: 32 segments, stands off the rounder hips
    # chest strap: over the left shoulder, across the chest and back to the right hip
    e1 = Vector((0.85, 0.0, 0.78)).normalized()
    strap = object_from_bm('strap', band(tree, (-0.02, 0.06, 1.27), e1, (0, 1, 0), 0.08, 40), mirror=False)
    # loincloth: a front and a back flap hanging from under the belt, jagged hems
    lf = object_from_bm('flap_front', flap(tree, [0.0, 0.09, 0.18, 0.27, 0.36], 0.745, 0.55,
                                           [0.24, 0.33, 0.28, 0.37, 0.44], True))
    lb = object_from_bm('flap_back', flap(tree, [0.0, 0.075, 0.15, 0.225, 0.30], 0.745, 0.58,
                                          [0.36, 0.45, 0.40, 0.49, 0.55], False))
    for o in (belt, strap, lf, lb):
        paint(o, {'leather': PAL['leather']}, lambda c_, n_, i: 'leather')
    return [eye, tusks, nails, belt, strap, lf, lb]


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
        bind(p, rig, body=body)
    # idle: breathing through the chest, a slow head turn, the arms sway a little
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (-1.5, 0, 0), 'head': (0, 0, 5),
                                   'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0)},
                       24: {}, 36: {'chest': (2, 0, 0), 'neck': (-1.5, 0, 0), 'head': (0, 0, -5),
                                    'upperarm.L': (3, 0, 0), 'upperarm.R': (3, 0, 0)}, 48: {}})
    # move: a heavy walk; the swinging leg bends at the knee, the arms swing against the legs
    A, S = 8, 12     # s4 r6: a short waddle step (a longer swing levers the front flap off the thigh: drift)
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 3)},
        9: {'shin.R': (-25, 0, 0), 'foot.R': (10, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0), 'spine': (0, 0, -3)},
        25: {'shin.L': (-25, 0, 0), 'foot.L': (10, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 0, 3)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.03, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.03, 0)},
             33: {'hips': (0, 0, 0)}})
    # attack: the right arm rears up and back, then a downward hammer blow with a forward lean
    clip(rig, 'attack', {
        1: {},
        10: {'upperarm.R': (80, 0, 0), 'forearm.R': (55, 0, 0), 'chest': (-6, 0, 0), 'head': (-4, 0, 0)},
        18: {'upperarm.R': (35, 0, 0), 'forearm.R': (10, 0, 0), 'chest': (12, 0, 0), 'spine': (5, 0, 0), 'head': (6, 0, 0)},
        24: {'upperarm.R': (25, 0, 0), 'forearm.R': (8, 0, 0), 'chest': (8, 0, 0), 'spine': (3, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
