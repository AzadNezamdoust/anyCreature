import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet
from mathutils.bvhtree import BVHTree

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull) plus hand edits; detail in stages 2-4
META = dict(creature='goblin', model='opus', engine_glb='')

J = dict(
    hips=(0, 0.10, 0.40), spine=(0, 0.09, 0.52), chest=(0, 0.07, 0.63), neck=(0, 0.03, 0.72),
    head=(0, -0.04, 0.82), crown=(0, -0.08, 1.06),
    hipL=(0.115, 0.06, 0.38), kneeL=(0.19, -0.07, 0.25), ankleL=(0.20, 0.06, 0.09), toeL=(0.20, -0.12, 0.03),
    shoulderL=(0.18, 0.05, 0.63), elbowL=(0.245, 0.03, 0.45), wristL=(0.29, -0.04, 0.27), handL=(0.30, -0.08, 0.13),
    earL=(0.16, -0.05, 0.91), earTipL=(0.45, 0.09, 0.955),
)


# the head the hull cannot see (it fuses the long ear blade with the skull into a shelf over the shoulders, and
# reads the face as a hood): hand-built half rings P0 (front seam) .. P7 (back seam), throat -> crown.
# P1-P3 carry the face (nose side, eye, cheek corner), P4-P5 the side of the skull (ear root), P6 the rear.
EAR_SECTIONS = [((0.21, -0.045, 0.905), 0.13, 0.026), ((0.30, 0.0, 0.925), 0.095, 0.02),
                ((0.385, 0.05, 0.942), 0.05, 0.012), ((0.45, 0.09, 0.955), 0.012, 0.005)]
BACK = (0.06, 0.56, 0.20, 0.20)    # the hunch: corner centre y, z and radii
TRAP = (0.72, 1.0)         # the trapezius slope: z at x = 0.08, drop per metre of x
ARM_SQUEEZE = 0.5
ARM_Y = [(0.10, -0.09), (0.25, -0.07), (0.35, -0.03), (0.45, 0.02), (0.55, 0.045), (0.66, 0.06)]   # (z, y) of the arm's centre


def interp(tab, z):
    if z <= tab[0][0]:
        return tab[0][1]
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z <= z1:
            return a + (b - a) * (z - z0) / (z1 - z0)
    return tab[-1][1]


NECK = [(0, -0.075, 0.69), (0.04, -0.072, 0.695), (0.07, -0.055, 0.705), (0.085, -0.02, 0.72), (0.088, 0.02, 0.74),
        (0.075, 0.055, 0.76), (0.045, 0.08, 0.775), (0, 0.085, 0.78)]
HEAD = [
    # H1 throat / jaw underside
    [(0, -0.235, 0.645), (0.05, -0.225, 0.648), (0.095, -0.185, 0.67), (0.12, -0.13, 0.715), (0.125, -0.06, 0.755), (0.105, 0.0, 0.785), (0.06, 0.04, 0.805), (0, 0.05, 0.81)],
    # H2 chin / lower lip
    [(0, -0.275, 0.685), (0.055, -0.262, 0.69), (0.10, -0.225, 0.71), (0.135, -0.16, 0.745), (0.145, -0.07, 0.79), (0.125, 0.01, 0.83), (0.075, 0.06, 0.85), (0, 0.07, 0.855)],
    # H3 mouth line
    [(0, -0.282, 0.718), (0.06, -0.268, 0.726), (0.105, -0.232, 0.75), (0.142, -0.17, 0.785), (0.152, -0.075, 0.82), (0.132, 0.015, 0.855), (0.08, 0.065, 0.875), (0, 0.078, 0.88)],
    # H4 upper lip / nose base
    [(0, -0.29, 0.745), (0.04, -0.283, 0.75), (0.10, -0.245, 0.775), (0.145, -0.18, 0.805), (0.158, -0.08, 0.84), (0.137, 0.018, 0.875), (0.085, 0.07, 0.895), (0, 0.083, 0.90)],
    # H5 nose underside (the hook tip) / cheek
    [(0, -0.395, 0.705), (0.028, -0.305, 0.765), (0.085, -0.262, 0.80), (0.145, -0.195, 0.825), (0.162, -0.085, 0.855), (0.14, 0.02, 0.89), (0.088, 0.073, 0.91), (0, 0.087, 0.915)],
    # H6 nose top / cheekbone under the eye
    [(0, -0.405, 0.76), (0.03, -0.315, 0.80), (0.06, -0.28, 0.835), (0.118, -0.245, 0.84), (0.165, -0.12, 0.865), (0.15, 0.0, 0.90), (0.092, 0.075, 0.925), (0, 0.09, 0.93)],
    # H7 nose bridge / lower eye
    [(0, -0.33, 0.835), (0.03, -0.305, 0.85), (0.055, -0.285, 0.862), (0.115, -0.25, 0.868), (0.165, -0.13, 0.89), (0.152, 0.0, 0.925), (0.092, 0.075, 0.95), (0, 0.09, 0.955)],
    # H8 brow ridge
    [(0, -0.31, 0.89), (0.035, -0.31, 0.905), (0.06, -0.305, 0.915), (0.12, -0.265, 0.925), (0.165, -0.135, 0.93), (0.15, -0.005, 0.96), (0.09, 0.07, 0.98), (0, 0.085, 0.985)],
    # H9 forehead
    [(0, -0.27, 0.97), (0.04, -0.267, 0.973), (0.08, -0.255, 0.978), (0.13, -0.205, 0.985), (0.155, -0.11, 0.99), (0.135, 0.0, 1.01), (0.085, 0.06, 1.02), (0, 0.07, 1.025)],
    # H10 dome
    [(0, -0.21, 1.05), (0.04, -0.207, 1.05), (0.08, -0.19, 1.05), (0.11, -0.145, 1.05), (0.122, -0.08, 1.05), (0.105, -0.01, 1.055), (0.065, 0.035, 1.06), (0, 0.045, 1.065)],
    # H11 crown
    [(0, -0.14, 1.088), (0.03, -0.137, 1.09), (0.055, -0.123, 1.092), (0.07, -0.095, 1.094), (0.072, -0.06, 1.095), (0.06, -0.03, 1.095), (0.035, -0.008, 1.095), (0, 0.0, 1.095)],
]
# the side-view cut line (y, z): everything of the hull above it goes (the chin under the jaw, the head, the ear shelf
# over the shoulders); the hunched shoulder line behind the neck descends as the reference side view shows it
CUT = [(-0.60, 0.60), (-0.11, 0.60), (-0.10, 0.66), (0.05, 0.765), (0.16, 0.745), (0.60, 0.55)]


def fcut(y):
    for (y0, z0), (y1, z1) in zip(CUT, CUT[1:]):
        if y <= y1:
            return z0 + (z1 - z0) * max(0.0, (y - y0)) / (y1 - y0)
    return CUT[-1][1]


def zip_rows(bm, A, B):
    """Triangles between two seam-to-seam rows of different lengths, advancing by arc-length parameter."""
    def par(R):
        L = [0.0]
        for p, q in zip(R, R[1:]):
            L.append(L[-1] + (q.co - p.co).length)
        return [l / L[-1] for l in L]
    ta, tb = par(A), par(B)
    i = j = 0
    out = []
    while i < len(A) - 1 or j < len(B) - 1:
        if j == len(B) - 1 or (i < len(A) - 1 and ta[i + 1] <= tb[j + 1]):
            out.append(bm.faces.new([A[i], A[i + 1], B[j]])); i += 1
        else:
            out.append(bm.faces.new([A[i], B[j + 1], B[j]])); j += 1
    return out


def stage1(k):
    ob = carve_base(k, mask_blur=1, blur=0)
    bm = edit(ob)
    # 1. the head off: faces above the side-view cut line go, the new rim is snapped onto the line
    bm.faces.ensure_lookup_table()
    dead = [f for f in bm.faces if f.calc_center_median().z > fcut(f.calc_center_median().y)]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bnd = [e for e in bm.edges if len(e.link_faces) == 1 and not (abs(e.verts[0].co.x) < 1e-5 and abs(e.verts[1].co.x) < 1e-5)]
    adj = {}
    for e in bnd:
        for v in e.verts:
            adj.setdefault(v, []).append(e.other_vert(v))
    ends = [v for v, l in adj.items() if len(l) == 1]
    say('neck cut: boundary edges', len(bnd), 'ends', len(ends), 'max valence', max(len(l) for l in adj.values()),
        [tuple(round(c, 3) for c in v.co) for v in ends])
    start = min(ends, key=lambda v: v.co.y)
    A, prev = [start], None
    while True:
        nx = [w for w in adj[A[-1]] if w is not prev]
        if not nx:
            break
        prev = A[-1]; A.append(nx[0])
    say('neck rim', [tuple(round(c, 3) for c in v.co) for v in A])
    up = V(0, -0.3, 1).normalized()
    for v in (A[0], A[-1]):
        v.co.x = 0.0
    # 2. the neck ring just above the cut, resampled to 8 points, then the hand-built head rings
    # 1b. the hunched back: the hull's flat shoulder table behind the neck becomes a quarter ellipse in side view
    #     (verts behind and above the corner centre, outside the ellipse, are pulled onto it)
    cy, cz, ry, rz = BACK
    for v in bm.verts:
        if v.co.y > cy and v.co.z > cz and v.co.x < 0.17:
            u, w = (v.co.y - cy) / ry, (v.co.z - cz) / rz
            r = math.hypot(u, w)
            if r > 1.0:
                v.co.y, v.co.z = cy + (v.co.y - cy) / r, cz + (v.co.z - cz) / r
    # 1c. the trapezius: the hull's shoulder tops (x > 0.09) sit as high as the neck (a flat collar under the head);
    #     everything above the slope z = 0.76 - 0.8 (x - 0.08) is pressed down onto it (75%)
    for v in bm.verts:
        zmax = TRAP[0] - TRAP[1] * (v.co.x - 0.08)
        if v.co.x > 0.09 and -0.16 < v.co.y < 0.22 and v.co.z > zmax:
            v.co.z = zmax + 0.25 * (v.co.z - zmax)
    # 1c'. a narrower chest and waist: torso vertices inside the arms (x < 0.175) between the hips and the armpit
    #      come in to 86% in x (more air between the arm and the flank in the front view)
    for v in bm.verts:
        if v.co.x < 0.175 and 0.36 < v.co.z < 0.70 and v.co.y < 0.2:
            f = min(1.0, (v.co.z - 0.36) / 0.08, (0.70 - v.co.z) / 0.06)
            v.co.x *= 1.0 - 0.14 * f
    # 1d. the arms: the hull gives them the torso's whole side-view depth (0.16 m deep, 0.06 wide: a cape, not an arm).
    #     Arm vertices (outside the torso and legs in the front view) are squeezed in y about the arm's centre line,
    #     to half depth, blending into the torso at the shoulder.
    for v in bm.verts:
        x, y, z = v.co
        if z > 0.66 or x < (0.26 if z < 0.32 else 0.19) or y > (0.15 if z > 0.48 else 0.12):
            continue
        s = 1.0 - (1.0 - ARM_SQUEEZE) * min(1.0, max(0.0, (0.66 - z) / 0.08))
        yc = interp(ARM_Y, z)
        v.co.y = yc + (y - yc) * s
    # 2. a narrow neck ring above the wide rim (the band between them is the trapezius slope), then the head rings
    h0 = NECK
    rows = [ring(bm, h0)] + [ring(bm, r) for r in HEAD]
    zip_rows(bm, A, rows[0])
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[-1])
    recalc_normals(bm)
    # 3. ears: the long horizontal blades, out of the two side faces H6-H8 at P4-P5, swept back, a thin lens section
    roles = {'bf': rows[6][4], 'bb': rows[6][5], 'mb': rows[7][5], 'tb': rows[8][5], 'tf': rows[8][4], 'mf': rows[7][4]}
    faces = [f for f in bm.faces if set(f.verts) in ({rows[6][4], rows[6][5], rows[7][5], rows[7][4]},
                                                    {rows[7][4], rows[7][5], rows[8][5], rows[8][4]})]
    assert len(faces) == 2
    d = (V(J['earTipL']) - V(J['earL'])).normalized()
    t = d.cross(V(0, 0, 1)).normalized()            # across the blade, toward the front
    if t.y > 0:
        t = -t
    for c, h, th in EAR_SECTIONS:
        old = {k: v.co.copy() for k, v in roles.items()}
        r = extrude(bm, faces)
        faces = r['faces']
        nv = {k: min(r['verts'], key=lambda v: (v.co - p).length) for k, p in old.items()}
        c = V(c)
        up = V(0, 0, 1)
        pos = {'bf': c - up * h / 2 + t * th * 0.4, 'bb': c - up * h / 2 - t * th * 0.4, 'mb': c - t * th,
               'tb': c + up * h / 2 - t * th * 0.4, 'tf': c + up * h / 2 + t * th * 0.4, 'mf': c + t * th}
        for k, v in nv.items():
            v.co = pos[k]
        roles = nv
    recalc_normals(bm)
    snap_seam(bm)
    commit(ob, bm)
    if os.environ.get('GOB_DBG'):
        from mathutils.bvhtree import BVHTree
        eb = evaluated_bm(ob); eb.faces.ensure_lookup_table(); t = BVHTree.FromBMesh(eb)
        for i, j in t.overlap(t):
            if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
                say('HIT', tuple(round(x, 3) for x in eb.faces[i].calc_center_median()), tuple(round(x, 3) for x in eb.faces[j].calc_center_median()))
    return ob


def H(r, i):
    """Head ring r (0 = the neck ring, 1..11 = HEAD), point i (0 front seam .. 7 back seam), as built in stage 1."""
    return V(NECK[i] if r == 0 else HEAD[r - 1][i])


MOUTH = []      # stage 2 -> 3: centres of the faces inside the mouth slot
TEETH = []      # stage 2 -> 3: the upper-lip and lower-lip edge rows (x >= 0, front first)
EARF = []       # stage 2 -> 3: the ear's front (cupped) face centres


def stage2(k, body):
    bm = edit(body)
    vn = lambda r, i: vert_near(bm, H(r, i))
    # -- the grin: a loop through the chin band H2-H3, its front half pushed in as the mouth slot; the corners rise
    with k.topo(bm, 'loop', 'grin: a loop in the chin band H2-H3 (lower lip edge), its front pushed in as the mouth slot'):
        ms = loopcut(bm, edge_near(bm, (H(2, 0) + H(3, 0)) / 2), t=0.45, near=vn(2, 0))
    for v in ms:
        if v.co.y < -0.12:
            f = min(1.0, (-0.12 - v.co.y) / 0.08)
            v.co.y += 0.028 * f
            v.co.z += 0.004 * f
    # the upper lip (H3 front) overhangs the slot a touch; the lip corners (P3) climb into the cheek: a grin
    for i, d in ((0, (0, -0.006, 0.0)), (1, (0, -0.006, 0.0)), (2, (0, -0.004, 0.006)), (3, (0.004, 0, 0.012))):
        vn(3, i).co += V(d)
    # -- the hooked nose: the tip hangs below the bridge, the nostril wing flares, the bridge dips at the stop
    for (r, i), d in {(5, 0): (0, 0.005, -0.018), (6, 0): (0, -0.006, -0.012), (5, 1): (0.012, 0.004, 0.004),
                      (4, 1): (0.006, -0.004, 0.0), (7, 0): (0, 0.012, 0.004), (7, 1): (0, 0.008, 0)}.items():
        vn(r, i).co += V(d)
    # -- heavy angry brow: the brow ring comes forward and the inner brow drops (a V over the nose)
    # team pass, must-fix 3: the brow came forward 12-22 mm and read as a cap brim; now 0-6 mm (the V stays), the
    # forehead front comes forward 10 mm so the dome flows into the brow, the cheekbone rises to frame the socket
    # second pass (verify_team item 3): the wire still showed a step: at P2/P3 the brow ring overhung the eye by 2-2.5 cm
    # and the forehead above it receded at 35-45 deg. The brow's outer half goes back 11-13 mm, the forehead's outer
    # half forward another 10-12 mm: one slope from the dome to the brow, a 1 cm bump over the eye.
    for i, d in ((0, (0, -0.002, -0.018)), (1, (0, -0.005, -0.016)), (2, (0, 0.007, -0.008)), (3, (0.004, 0.007, 0.002))):
        vn(8, i).co += V(d)
    for i, d in ((0, (0, -0.01, 0)), (1, (0, -0.012, 0)), (2, (0, -0.02, 0)), (3, (0, -0.02, 0))):
        vn(9, i).co += V(d)
    vn(6, 2).co += V(0, 0, 0.008)
    vn(6, 3).co += V(0, 0, 0.015)
    # -- cheekbone: the cheek corner under the eye out and forward; jaw corner out (the jaw line reads in front view)
    vn(6, 3).co += V(0.012, -0.01, 0.0)
    vn(5, 3).co += V(0.01, -0.006, 0.0)
    vn(2, 3).co += V(0.01, 0.0, -0.006)
    vn(2, 4).co += V(0.008, 0.0, -0.008)
    # -- eye sockets: a loop inside the eye quad (H7-H8, P2-P3), sunk under the brow
    with k.topo(bm, 'inset', 'eye socket under the brow (H7-H8, P2-P3)'):
        c = (H(7, 2) + H(7, 3) + H(8, 2) + H(8, 3)) / 4
        sk = inset(bm, [face_near(bm, c, n=(0, -1, 0))], 0.22, depth=-0.014)
    sk[0].normal_update()
    SOCKET[:] = [sk[0].calc_center_median().copy(), sk[0].normal.copy()]
    # -- pot belly: the lower torso front swells forward over the belt line
    for v in bm.verts:
        x, y, z = v.co
        if x < 0.13 and 0.40 < z < 0.64 and y < 0.0 and z < 0.66:
            f = max(0.0, 1.0 - ((z - 0.52) / 0.12) ** 2) * max(0.0, 1.0 - (x / 0.13) ** 2)
            v.co.y -= 0.025 * f
    legs(bm)
    MOUTH[:] = []
    msf = set(ms)
    r3 = {vn(3, i) for i in range(4)}
    for f in bm.faces:
        if len(set(f.verts) & msf) >= 2 and len(set(f.verts) & r3) >= 1 and f.calc_center_median().y < -0.165:
            MOUTH.append(f.calc_center_median().copy())
    TEETH[:] = [[vn(3, i).co.copy() for i in (0, 1, 2, 3)],
                sorted([v.co.copy() for v in ms if v.co.y < -0.12], key=lambda c: c.x)]
    recalc_normals(bm)
    if os.environ.get('GOB_DUMP'):
        import json
        bm.verts.index_update()
        bm.faces.ensure_lookup_table(); t = BVHTree.FromBMesh(bm)
        for i, j in t.overlap(t):
            if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
                say('HIT', [tuple(round(x, 3) for x in v.co) for v in bm.faces[i].verts], [tuple(round(x, 3) for x in v.co) for v in bm.faces[j].verts])
        json.dump({'v': [list(v.co) for v in bm.verts], 'f': [[v.index for v in f.verts] for f in bm.faces],
                   'leg': [v.index for v in LEGV]}, open(os.environ['GOB_DUMP'], 'w'))
    commit(body, bm)


SOCKET = []
LEGV = []
# (vertex after the first pass) -> (y, z)
KNEE_MOVES = [
    ((0.128, -0.077, 0.161), (-0.090, 0.185)), ((0.121, -0.023, 0.112), (-0.062, 0.170)),      # the phantom prong
    ((0.163, -0.029, 0.117), (-0.064, 0.172)), ((0.117, 0.004, 0.127), (-0.030, 0.165)),
    ((0.159, 0.007, 0.128), (-0.028, 0.167)), ((0.138, 0.017, 0.148), (-0.012, 0.178)),
    ((0.129, -0.024, 0.191), (-0.026, 0.195)), ((0.169, -0.028, 0.190), (-0.028, 0.195)),
    ((0.125, 0.005, 0.230), (-0.005, 0.230)), ((0.190, 0.002, 0.236), (-0.005, 0.236)),         # the slot's top
    ((0.126, 0.083, 0.242), (0.045, 0.240)), ((0.188, 0.080, 0.239), (0.043, 0.238)),           # the back of the knee
    ((0.130, 0.050, 0.176), (0.020, 0.176)), ((0.161, 0.057, 0.171), (0.024, 0.171)),           # the shin, mid
    ((0.128, 0.093, 0.176), (0.095, 0.176)), ((0.160, 0.097, 0.168), (0.097, 0.168))]
# team pass, must-fix 1 (legs): (z, scale) of the leg's cross-section about its centre line, and (z, dy) of the bend
LEG_S = [(0.05, 1.0), (0.10, 0.72), (0.16, 0.62), (0.22, 0.74), (0.29, 0.64), (0.36, 0.80), (0.42, 1.0)]
LEG_CY = [(0.05, 0.03), (0.20, 0.0), (0.30, 0.03)]
LEG_DY = [(0.05, 0.0), (0.10, 0.015), (0.16, -0.01), (0.22, -0.042), (0.29, -0.02), (0.40, 0.0)]


def legs(bm):
    """The hull's legs are columns as deep as the torso. Leg vertices (the component of the region below z 0.42 that
    holds the foot, not the hand's) are scaled in x and y about the leg's per-band centre (LEG_S, the knee ring less
    than thigh and shin so it reads as a joint), and the knee pushed forward / the ankle back (LEG_DY)."""
    reg = {v for v in bm.verts if v.co.z < 0.42}
    foot = min(reg, key=lambda v: (v.co - V(0.20, 0.0, 0.0)).length)
    comp, st = {foot}, [foot]
    while st:
        v = st.pop()
        for e in v.link_edges:
            w = e.other_vert(v)
            if w in reg and w not in comp and not (w.co.x > 0.245 and w.co.z > 0.11):
                comp.add(w); st.append(w)
    lv = [v for v in comp if v.co.x > 0.03]
    say('legs: verts', len(lv))
    LEGV[:] = lv
    for v in lv:
        cx, cy = 0.145, interp(LEG_CY, v.co.z)
        s = interp(LEG_S, v.co.z)
        wseam = min(1.0, (v.co.x - 0.03) / 0.06)          # the crotch near the seam follows only partly
        wbutt = min(1.0, max(0.0, (0.22 - v.co.y) / 0.07)) if v.co.z > 0.22 else 1.0   # the buttock is torso
        s = 1.0 - (1.0 - s) * wseam * wbutt
        v.co.x = cx + (v.co.x - cx) * s
        v.co.y = cy + (v.co.y - cy) * s + interp(LEG_DY, v.co.z) * wseam * wbutt
    # second pass (verify_team item 1). Diagnosis (mesh walk): under the knee the hull has TWO prongs: the real shin
    # (y 0.05-0.10, down to the heel) and a phantom one in front of it (the hand's side silhouette x the leg's front
    # silhouette), closed 2 cm above the foot. Together they read as a column in the side view. The phantom prong is
    # lifted into the knee (its underside), the shin's top is sheared forward under the knee and the back of the knee
    # hollowed, so the shin runs diagonally from a forward knee to the heel.
    for src, (y, z) in KNEE_MOVES:
        v = min(lv, key=lambda u: (u.co - V(src)).length)
        assert (v.co - V(src)).length < 2e-3, src
        v.co.y, v.co.z = y, z


PAL = {'skin': '#6aa84f', 'belly': '#9ccc7a', 'belt': '#4a3222', 'cloth': '#7a5a3a',
       'fang': '#efe6cf', 'eye': '#f2d23c', 'pupil': '#2b1d14', 'brass': '#b8963c'}
BELT = (0.455, 0.08, 0.20, 0.056)     # belt centre z at y = -0.08, its rise per metre of y (lower in front), height
HAND = V(0.30, -0.068, 0.158)         # the hull hand's lower centre (stage-3 probe of the base)
EYE_R = 0.031
EYE_W, EYE_H, EYE_TILT = 0.052, 0.037, 14.0    # almond half-width / half-height (1.4:1), outer corner up (deg)
EYE_PW, EYE_PH = 0.0075, 0.0145                # the pupil: a small vertical disc
BELT_REAR = 0.016                              # the belt's outer offset at the back (22 mm at the front and sides)
BELT_TH = {19: 146.0}                           # column 19 sits on the rump's corner ridge (deg from the front)
NB = 25                                        # belt columns, seam to seam
FING_L, FING_SPREAD, CLAW = (0.058, 0.040), 24, (0.045, 0.0155)   # team pass, must-fix 4: longer fingers, bigger claws
FINGERS = []


def pal(*keys):
    return {kk: PAL[kk] for kk in keys}


def zbelt(y):
    return BELT[0] + (y + BELT[1]) * BELT[2]


def basis(a, hint=(0, 0, 1)):
    a = V(a).normalized()
    h = V(hint)
    if abs(h.dot(a)) > 0.95:
        h = V(1, 0, 0)
    u = (h - a * h.dot(a)).normalized()
    return a, u, a.cross(u)


def spike(bm, base, tip, r, knots=((0.55, 0.85),), sides=4, hint=(0, 0, 1)):
    """A closed tapering cone: base ring, optional rings (t, radius scale), apex."""
    base, tip = V(base), V(tip)
    a, u, w = basis(tip - base, hint)
    ang = [2 * math.pi * (i + 0.5) / sides for i in range(sides)]
    rows = []
    for t, sc in ((0.0, 1.0),) + tuple(knots):
        c = base.lerp(tip, t)
        rows.append(ring(bm, [c + (u * math.cos(q) + w * math.sin(q)) * r * sc for q in ang]))
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1, closed=True)
    ap = bm.verts.new(tip)
    last = rows[-1]
    for i in range(sides):
        bm.faces.new([last[i], last[(i + 1) % sides], ap])
    cap(bm, list(reversed(rows[0])))


def tube(bm, rows, sides=5, hint=(0, 0, 1)):
    """A closed tube through rows [(centre, axis, radius)], both ends capped."""
    rr = []
    for c, d, r in rows:
        _, u, w = basis(d, hint)
        rr.append(ring(bm, [c + (u * math.cos(q) + w * math.sin(q)) * r for q in [2 * math.pi * (i + 0.5) / sides for i in range(sides)]]))
    for r0, r1 in zip(rr, rr[1:]):
        bridge(bm, r0, r1, closed=True)
    cap(bm, list(reversed(rr[0])))
    cap(bm, rr[-1])


def plate3(bm, top, bot, nrm, dt, db):
    """A thick cloth strip (as in abc/k3/goblin): rows top/mid/bot (seam first), offsets dt at the top, db at the hem;
    open at the seam (the mirror closes it), capped at the outer column."""
    mid = [p.lerp(q, 0.5) for p, q in zip(top, bot)]
    dm = ((dt[0] + db[0]) / 2, (dt[1] + db[1]) / 2)
    rows = []
    for pts, (d0, d1) in ((top, dt), (mid, dm), (bot, db)):
        rows.append((ring(bm, [p + n * d0 for p, n in zip(pts, nrm)]), ring(bm, [p + n * d1 for p, n in zip(pts, nrm)])))
    (ti, to), (mi, mo), (bi, bo) = rows
    bridge(bm, to, mo); bridge(bm, mo, bo); bridge(bm, bi, mi); bridge(bm, mi, ti)
    bridge(bm, ti, to); bridge(bm, bo, bi)
    bm.faces.new([ti[-1], to[-1], mo[-1], mi[-1]])
    bm.faces.new([mi[-1], mo[-1], bo[-1], bi[-1]])
    recalc_normals(bm)


def body_labels(bm):
    """Region labels for the base faces: rules, then a majority filter so no border runs saw-toothed across
    single triangles. Mouth, inner ear and head follow the hand-built head's loops and are not filtered."""
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    lab = {}
    fixed = set()
    for f in bm.faces:
        c, n = f.calc_center_median(), f.normal
        ax = V(abs(c.x), c.y, c.z)
        if any((ax - m).length < 2e-3 for m in MOUTH):
            lab[f.index] = 'belt'; fixed.add(f.index)
        elif c.x > 0.19 and c.z > 0.85 and n.y < -0.2:
            lab[f.index] = 'belly'; fixed.add(f.index)                    # the cupped front of the ear
        elif c.z > 0.64 and c.y < -0.12:
            lab[f.index] = 'skin'; fixed.add(f.index)                     # the head
        elif c.x < 0.105 and zbelt(c.y) < c.z < 0.655 and c.y < 0.0 and n.y < -0.25:
            lab[f.index] = 'belly'
        elif c.y > 0.12 and not (c.x < 0.10 and c.z > 0.42):
            lab[f.index] = 'skin'                                         # the rump beside and below the back flap
        elif c.x < 0.165 and 0.29 < c.z < zbelt(c.y) and (c.x < 0.09 or c.z > 0.33):
            lab[f.index] = 'cloth'
        else:
            lab[f.index] = 'skin'
    nb = {f.index: [g.index for e in f.edges for g in e.link_faces if g is not f] for f in bm.faces}
    for _ in range(3):
        new = dict(lab)
        for i, ns in nb.items():
            if i in fixed:
                continue
            cnt = {}
            for j in ns:
                cnt[lab[j]] = cnt.get(lab[j], 0) + 1
            best = max(cnt, key=cnt.get)
            if best != lab[i] and cnt[best] * 2 > len(ns):
                new[i] = best
        lab = new
    return lab


def stage3(k, body):
    bm = edit(body)
    lab = body_labels(bm)
    bm.free()
    paint(body, pal('skin', 'belly', 'belt', 'cloth'), lambda c, n, i: lab[i])
    pieces = []

    # belt: two rows ray-cast from the torso's axis onto the hull in the tilted belt plane, set out along the
    # surface's horizontal normal (inner 0.007, outer 0.026); open at the seam
    eb = evaluated_bm(body)
    tree = BVHTree.FromBMesh(eb)
    rows = {}
    for dz in (-BELT[3] / 2, BELT[3] / 2):
        pts, nrm = [], []
        for j in range(NB):
            th = math.radians(BELT_TH.get(j, 180.0 * j / (NB - 1)))
            d = V(math.sin(th), -math.cos(th), -math.cos(th) * BELT[2]).normalized()
            o = V(0, 0.07, zbelt(0.07) + dz)
            loc, n, _, _ = tree.ray_cast(o, d)
            hn = V(n.x, n.y, n.z * 0.7).normalized()     # the surface normal (the back of the skirt slopes)
            if j in (0, NB - 1):
                loc.x, hn.x = 0.0, 0.0
                hn.normalize()
            pts.append(loc); nrm.append(hn)
        rows[dz] = (pts, nrm)
    eb.free()
    (lo, ln), (hi, hn_) = rows[-BELT[3] / 2], rows[BELT[3] / 2]
    BELTROWS[:] = [lo, ln, hi, hn_]
    # the hull is lumpy between the columns: a column whose band cuts the skin steps out until none does (team pass,
    # must-fix 5: 25 columns and 2.5 mm steps, so the belt hugs the rump instead of standing off it as a shelf)
    # second pass (verify_team item 5): the hull's rump is a box, so columns 19 (facing +x) and 20 (facing +y) cut
    # the corner between them and stepped out 20 mm (the lump), and the 22 mm band stood off the receding back as a
    # shelf. The column normals are now averaged with their neighbours' (the band wraps the corner, offsets scaled by
    # 1/cos), and the band thins from 22 mm at the sides to BELT_REAR at the back.
    for nr in (ln, hn_):
        raw = [n.copy() for n in nr]
        for j in range(1, NB - 1):
            m = (raw[j - 1] + raw[j] * 2 + raw[j + 1]).normalized()
            nr[j] = m / max(0.7, m.dot(raw[j]))
    outer = [0.022 + (BELT_REAR - 0.022) * min(1.0, max(0.0, (j - 14) / 4)) for j in range(NB)]
    extra = [0.0] * NB
    eb2 = evaluated_bm(body); t2 = BVHTree.FromBMesh(eb2)
    for it in range(20):
        bm = bmesh.new()
        A = ring(bm, [p + n * (0.009 + e) for p, n, e in zip(lo, ln, extra)]); B = ring(bm, [p + n * (o + e) for p, n, e, o in zip(lo, ln, extra, outer)])
        C = ring(bm, [p + n * (o + e) for p, n, e, o in zip(hi, hn_, extra, outer)]); D = ring(bm, [p + n * (0.009 + e) for p, n, e in zip(hi, hn_, extra)])
        bridge(bm, A, B); bridge(bm, B, C); bridge(bm, C, D); bridge(bm, D, A)
        bm.faces.ensure_lookup_table()
        bad = {j for _, fi in t2.overlap(BVHTree.FromBMesh(bm)) for v in bm.faces[fi].verts for j in [v.index % NB]}
        if not bad:
            break
        for j in bad:
            extra[j] += 0.0025
        bm.free()
    say('belt extra offsets', [round(e, 3) for e in extra])
    if os.environ.get('GOB_DUMP'):
        for j in range(15, NB):
            say('BELT', j, tuple(round(c, 3) for c in lo[j]), tuple(round(c, 3) for c in ln[j]), tuple(round(c, 3) for c in hi[j]), tuple(round(c, 3) for c in hn_[j]))
        for v in eb2.verts:
            if v.co.x >= 0 and v.co.y > 0.1 and 0.42 < v.co.z < 0.62:
                say('BV', tuple(round(c, 3) for c in v.co))
    eb2.free()
    belt = object_from_bm('belt', bm)
    paint(belt, pal('belt'), lambda c, n, i: 'belt')
    pieces.append(belt)

    # buckle: a chunky brass frame on the belt front, its back sunk into the belt
    yo = (lo[0].y + hi[0].y) / 2 - 0.026
    zm = (lo[0].z + hi[0].z) / 2
    bm = bmesh.new()
    yi, yf, bx, z0, z1 = yo + 0.009, yo - 0.014, 0.044, zm - 0.036, zm + 0.036
    q = ring(bm, [(0, yi, z0), (bx, yi, z0), (bx, yf, z0), (0, yf, z0), (0, yi, z1), (bx, yi, z1), (bx, yf, z1), (0, yf, z1)])
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (3, 2, 6, 7), (1, 0, 4, 5), (2, 1, 5, 6)):
        bm.faces.new([q[j] for j in f])
    recalc_normals(bm)
    inner = inset(bm, [face_near(bm, (bx / 2, yf, zm), n=(0, -1, 0))], 0.45, depth=0.006)
    ctr = [f.calc_center_median().copy() for f in inner]
    buckle = object_from_bm('buckle', bm)
    paint(buckle, pal('brass', 'belt'), lambda c, n, i: 'belt' if any((V(abs(c.x), c.y, c.z) - m).length < 1e-3 for m in ctr) else 'brass')
    pieces.append(buckle)

    # loincloth: tattered front and back flaps tucked under the belt, the hem flared along the column normals
    # (second pass: the back flap's top tucks under the thinner rear belt and its hem flares less, so it hangs down
    # the rump instead of bulging off the belt)
    for nm, idx, drops, flare, dt, db in (('cloth_front', (0, 2, 4, 6), (0.15, 0.11, 0.16, 0.10), 0.14, (0.010, 0.021), (0.010, 0.030)),
                                          ('cloth_back', (24, 23, 21, 20), (0.115, 0.08, 0.12, 0.07), 0.10, (0.010, 0.015), (0.009, 0.023))):
        bm = bmesh.new()
        tops = [lo[j] + ln[j] * extra[j] + V(0, 0, 0.012) for j in idx]     # tucked under the belt where it steps out
        nn = [ln[j] for j in idx]
        bots = [t + n * flare * d + V(0, 0, -d) for t, n, d in zip(tops, nn, drops)]
        plate3(bm, tops, bots, nn, dt, db)
        cloth = object_from_bm(nm, bm)
        paint(cloth, pal('cloth'), lambda c, n, i: 'cloth')
        pieces.append(cloth)

    # eyes (team pass, must-fix 2): a big almond lens, outer corner up, its rim ray-cast onto the skin around the socket
    # (flush with the cheek plane, no dark gap), a bulged iris ring, a small vertical pupil (< 35% of the lens)
    sc, sn = SOCKET
    bm = bmesh.new()
    a, u, w = basis(V(sn.x * 0.6, sn.y, sn.z * 0.3), (0, 0, 1))
    if w.x < 0:
        w = -w                                       # w: toward the outer corner (+x)
    eb = evaluated_bm(body); tree = BVHTree.FromBMesh(eb)
    tilt = math.tan(math.radians(EYE_TILT))
    ang = [2 * math.pi * i / 8 for i in range(8)]

    def almond(sw, sh):
        pts = []
        for q in ang:
            c, s = math.cos(q), math.sin(q)
            ps, pt = c * sw * (1.06 if abs(s) < 0.1 else 1.0), s * sh * (0.85 + 0.15 * abs(s))
            pts.append((ps, pt + ps * tilt))
        return pts

    def depth(ps, pt):
        p = sc + w * ps + u * pt
        loc, *_ = tree.ray_cast(p + a * 0.1, -a, 0.2)
        return (loc - sc).dot(a) if loc else 0.0
    rim = almond(EYE_W, EYE_H)
    dr = [depth(*p) for p in rim]
    mid = almond(EYE_W * 0.6, EYE_H * 0.6)
    dr = [max(dr[i], (dr[i - 1] + 2 * dr[i] + dr[(i + 1) % 8]) / 4) for i in range(8)]   # no lumps, never under the skin
    mean = sum(dr) / 8
    dmi = [max(0.6 * d + 0.4 * mean + 0.009, depth(*p) + 0.005) for d, p in zip(dr, mid)]
    dm = sum(dmi) / 8
    pup = almond(EYE_PW, EYE_PH)
    ra = ring(bm, [sc + a * (d + 0.004) + w * ps + u * pt for (ps, pt), d in zip(rim, dr)])
    rb = ring(bm, [sc + a * d + w * ps + u * pt for (ps, pt), d in zip(mid, dmi)])
    rp = ring(bm, [sc + a * (dm + 0.0025) + w * ps + u * pt for ps, pt in pup])
    eb.free()
    ap = bm.verts.new(sc - a * 0.02)
    for i in range(8):
        bm.faces.new([ra[(i + 1) % 8], ra[i], ap])
    bridge(bm, ra, rb, closed=True); bridge(bm, rb, rp, closed=True)
    cap(bm, rp)
    pc = sc + a * (dm + 0.0025)
    eye = object_from_bm('eye', bm)
    paint(eye, pal('eye', 'pupil'), lambda c, n, i: 'pupil' if (V(abs(c.x), c.y, c.z) - pc).length < 0.005 else 'eye')
    pieces.append(eye)

    # teeth: upper teeth seated in the upper-lip edge, lower corner fangs rising past the lip, small lower teeth
    up, lw = TEETH

    def along(row, t):
        L = [(q - p).length for p, q in zip(row, row[1:])]
        d = t * sum(L)
        for (p, q), l in zip(zip(row, row[1:]), L):
            if d <= l:
                return p.lerp(q, d / l)
            d -= l
        return row[-1].copy()
    bm = bmesh.new()
    inward = V(0, 1, 0.3).normalized()
    for t, Lt in ((0.07, 0.026), (0.27, 0.03), (0.47, 0.03), (0.66, 0.026)):
        p = along(up, t)
        spike(bm, p + inward * 0.012, p + V(0, -0.004, -Lt), 0.009, knots=((0.5, 0.75),))
    for t in (0.18, 0.4):
        p = along(lw, t)
        spike(bm, p + V(0, 0.008, -0.006), p + V(0, -0.006, 0.012), 0.006, knots=((0.5, 0.75),))
    p = along(lw, 0.72)
    spike(bm, p + V(0, 0.01, -0.012), p + V(0.006, -0.012, 0.05), 0.012, knots=((0.45, 0.8),))
    fangs = object_from_bm('fangs', bm)
    paint(fangs, pal('fang'), lambda c, n, i: 'fang')
    pieces.append(fangs)

    # hands: three knuckled fingers out of the hull's paddle (rooted inside it), curled forward, cream claws
    # second pass (verify_team item 4): the three fingers fanned front-to-back (hv ~ -y), so the front view saw one
    # tapered paddle, and they pointed at the foot, so the drift gate capped their length. Now they fan across the hand
    # (x, with a little y so the side view sees them too), reach forward and hook down: the tips stay nearer the palm
    # than the foot, at the full +60% length.
    ha = V(0.36, -0.80, -0.42).normalized()
    fan = V(1.0, 0.25, 0.0).normalized()
    fan = (fan - ha * fan.dot(ha)).normalized()
    bmf, bmc = bmesh.new(), bmesh.new()

    def rot(d, toward, deg):
        t = (toward - d * toward.dot(d)).normalized()
        return (d * math.cos(math.radians(deg)) + t * math.sin(math.radians(deg))).normalized()
    curl = V(-0.1, 0.1, -1)
    FINGERS[:] = []
    for sgn in (-1, 0, 1):
        d0 = rot(ha, fan * sgn if sgn else ha, FING_SPREAD * abs(sgn))
        p0 = HAND + V(0, 0, 0.012) + fan * 0.019 * sgn - ha * 0.02
        ln_ = 0.85 if sgn else 1.0
        kn = p0 + d0 * FING_L[0] * ln_
        d1 = rot(d0, curl, 22)
        tp = kn + d1 * FING_L[1] * ln_
        FINGERS.append((p0.copy(), tp.copy()))
        tube(bmf, [(p0, d0, 0.013), (kn, (d0 + d1).normalized(), 0.013), (tp, d1, 0.009)], hint=tuple(fan))
        d2 = rot(d1, curl, 18)
        spike(bmc, tp - d1 * 0.012, tp + d2 * CLAW[0], CLAW[1], knots=((0.45, 0.8),), hint=tuple(fan))
        say('finger', sgn, 'root', tuple(round(c, 3) for c in p0), 'tip', tuple(round(c, 3) for c in tp))
    recalc_normals(bmf)
    fingers = object_from_bm('fingers', bmf)
    paint(fingers, pal('skin'), lambda c, n, i: 'skin')
    hclaws = object_from_bm('handclaws', bmc)
    paint(hclaws, pal('fang'), lambda c, n, i: 'fang')
    pieces += [fingers, hclaws]

    # feet: three toes out of the hull's foot front, each with a claw
    bmt, bmc = bmesh.new(), bmesh.new()
    for x, dx in ((0.135, -0.018), (0.20, 0.0), (0.265, 0.018)):
        p0, p1 = V(x, -0.07, 0.026), V(x + dx, -0.135, 0.02)
        tube(bmt, [(p0, p1 - p0, 0.022), (p0.lerp(p1, 0.6), p1 - p0, 0.021), (p1, p1 - p0, 0.016)], hint=(0, 0, 1))
        dd = (p1 - p0).normalized()
        spike(bmc, p1 - dd * 0.01, p1 + dd * 0.032 + V(0, 0, -0.014), 0.012, knots=((0.45, 0.8),))
    recalc_normals(bmt)
    toes = object_from_bm('toes', bmt)
    paint(toes, pal('skin'), lambda c, n, i: 'skin')
    claws = object_from_bm('claws', bmc)
    paint(claws, pal('fang'), lambda c, n, i: 'fang')
    pieces += [toes, claws]
    return pieces


BELTROWS = []


def even_through(ob, rad=0.06):
    """repair r22: the thick cloth's inner and outer skins took different body weights (inner nearer the thigh),
    so the plate folded over in move. Each vertex takes the mean weights of the cloth vertices within rad
    (its partner through the thickness), so the plate bends as one sheet."""
    vs = ob.data.vertices
    W = [{g.group: g.weight for g in v.groups} for v in vs]
    new = []
    for v in vs:
        nb = [i for i, u in enumerate(vs) if (u.co - v.co).length < rad]
        acc = {}
        for i in nb:
            for g, w in W[i].items():
                acc[g] = acc.get(g, 0.0) + w / len(nb)
        new.append(acc)
    for vg in ob.vertex_groups:
        vg.remove(list(range(len(vs))))
    for i, acc in enumerate(new):
        for g, w in acc.items():
            if w > 1e-4:
                ob.vertex_groups[g].add([i], w, 'REPLACE')


def finger_rigid(pcs):
    """repair r109: rigid fingers (nearest bone) drifted off the heat-skinned palm; body weights folded them. Each finger
    and its claw now take one weight set: the mean body weights of that finger's root ring, so the finger follows the
    palm where it roots and stays straight."""
    segs = [(a, b) for a, b in FINGERS] + [(V(-a.x, a.y, a.z), V(-b.x, b.y, b.z)) for a, b in FINGERS]
    def sd(p, a, b):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        return (p - (a + ab * t)).length
    def which(p):
        return min(range(len(segs)), key=lambda i: sd(p, *segs[i]))
    fg = pcs[0]
    W = [{fg.vertex_groups[g.group].name: g.weight for g in v.groups} for v in fg.data.vertices]
    root = []
    for i, (a, b) in enumerate(segs):
        ids = [j for j, v in enumerate(fg.data.vertices) if (v.co - a).length < 0.02 and which(v.co) == i]
        acc = {}
        for j in ids:
            for g, w in W[j].items():
                acc[g] = acc.get(g, 0.0) + w / len(ids)
        root.append(acc)
    for ob in pcs:
        vs = ob.data.vertices
        for vg in ob.vertex_groups:
            vg.remove(list(range(len(vs))))
        for j, v in enumerate(vs):
            for g, w in root[which(v.co)].items():
                if w > 1e-4:
                    (ob.vertex_groups.get(g) or ob.vertex_groups.new(name=g)).add([j], w, 'REPLACE')




def smooth_weights(body, passes=10, rate=0.5):
    """The carved mesh is irregular: heat weights jump between neighbours of very different size, and the thin inner
    faces of the wrist folded over in a 7 deg forearm bend. Each pass moves every vertex's weights halfway to the mean
    of its edge neighbours', renormalised."""
    me = body.data
    nb = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nb[a].append(b); nb[b].append(a)
    W = [{g.group: g.weight for g in v.groups} for v in me.vertices]
    for _ in range(passes):
        new = []
        for i, w in enumerate(W):
            acc = {g: (1 - rate) * x for g, x in w.items()}
            for j in nb[i]:
                for g, x in W[j].items():
                    acc[g] = acc.get(g, 0.0) + rate * x / len(nb[i])
            s = sum(acc.values()) or 1.0
            new.append({g: x / s for g, x in acc.items() if x / s > 1e-3})
        W = new
    for vg in body.vertex_groups:
        vg.remove(list(range(len(me.vertices))))
    for i, w in enumerate(W):
        for g, x in w.items():
            body.vertex_groups[g].add([i], x, 'REPLACE')


def arm_clean(body):
    """The carved hand hangs beside the knee and the forearm beside the hip: heat weighting bled thigh/shin weight into
    them (0.2-0.3), so a leg swing or a chest twist folded the hand. Every vertex whose nearest skeleton segment is an
    arm bone (|x| > 0.17, z > 0.11, i.e. not the foot) drops its leg and hip weights, renormalised."""
    names = {g.index: g.name for g in body.vertex_groups}
    leg = ('thigh', 'shin', 'foot', 'hips')
    segs = []
    for s in ('.L', '.R'):
        sx = 1 if s == '.L' else -1
        m = lambda p: V(sx * p[0], p[1], p[2])
        segs += [('arm', m(J['shoulderL']), m(J['elbowL'])), ('arm', m(J['elbowL']), m(J['wristL'])), ('arm', m(J['wristL']), m(J['handL'])),
                 ('leg', m(J['hipL']), m(J['kneeL'])), ('leg', m(J['kneeL']), m(J['ankleL'])), ('leg', m(J['ankleL']), m(J['toeL'])),
                 ('leg', V(J['hips']), V(J['spine']))]
    def sd(p, a, b):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        return (p - (a + ab * t)).length
    if os.environ.get('GOB_DBG'):
        cls = {v.index: min(segs, key=lambda s: sd(v.co, s[1], s[2]))[0] for v in body.data.vertices if v.co.x > 0.17 and v.co.z > 0.11}
        for e in body.data.edges:
            a, b = e.vertices
            if a in cls and b in cls and cls[a] != cls[b]:
                say('ARMLEG', tuple(round(x, 3) for x in body.data.vertices[a].co), cls[a], tuple(round(x, 3) for x in body.data.vertices[b].co), cls[b])
    for v in body.data.vertices:
        if abs(v.co.x) > 0.17 and v.co.z > 0.11:
            kind = min(segs, key=lambda s: sd(v.co, s[1], s[2]))[0]
            if kind != 'arm':
                continue
            keep = {names[g.group]: g.weight for g in v.groups if not names[g.group].startswith(leg)}
            side = '.L' if v.co.x > 0 else '.R'
            if sum(keep.values()) < 1e-3:
                keep = {'forearm' + side: 1.0}
            s = sum(keep.values())
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            for nm, w in keep.items():
                body.vertex_groups[nm].add([v.index], w / s, 'REPLACE')


def stage4(k, body, pieces):
    # abc/k3/goblin's rig and clips, the joints moved onto this mesh (J: the hull's legs and arms, the hand-built head)
    rig = armature([
        ('hips', J['hips'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['crown'], 'neck', True),
        ('ear.L', J['earL'], J['earTipL'], 'head'),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hand.L', J['wristL'], J['handL'], 'forearm.L', True),
    ], roll='auto')
    skin(body, rig)
    arm_clean(body)
    smooth_weights(body)
    arm_clean(body)
    for pc in pieces:
        bind(pc, rig, body=body)
        if pc.name.startswith('piece_cloth') or pc.name == 'piece_belt':
            even_through(pc)
        if pc.name in ('piece_fangs', 'piece_eye', 'piece_toes', 'piece_claws'):
            even_through(pc, rad=0.03)
    finger_rigid([pc for nm in ('piece_fingers', 'piece_handclaws') for pc in pieces if pc.name == nm])
    both = lambda b, v: {b + '.L': v, b + '.R': v}

    def soft(keys):
        # the carved arm hangs 2-4 cm off a flank it shares heat weights with: arm swings at 60% of k3's
        return {f: {b: (tuple(ARM_AMP * a for a in r) if b.split('.')[0] in ('upperarm', 'forearm', 'hand') else r)
                    for b, r in d.items()} for f, d in keys.items()}
    clip(rig, 'idle', {
        1: {},
        12: {'head': (0, 22, 0), 'neck': (3, 8, 0), 'chest': (2, 0, 0), **both('ear', (6, 0, 0)), **both('forearm', (8, 0, 0))},
        24: {'head': (-6, 0, 0), 'neck': (0, 0, 0), 'chest': (0, 0, 0), **both('ear', (-4, 0, 0)), **both('forearm', (0, 0, 0))},
        36: {'head': (0, -22, 0), 'neck': (3, -8, 0), 'chest': (2, 0, 0), 'ear.L': (8, 0, 0), 'ear.R': (-2, 0, 0), **both('forearm', (8, 0, 0))},
        48: {}})
    W = {1: (-18, 18, 0, -10), 9: (0, 0, -30, 0), 17: (18, -18, -10, 0), 25: (0, 0, 0, -30), 33: (-18, 18, 0, -10)}
    mv = {}
    for f, (tl, tr, sl, sr) in W.items():
        mv[f] = {'thigh.L': (tl, 0, 0), 'thigh.R': (tr, 0, 0), 'shin.L': (sl, 0, 0), 'shin.R': (sr, 0, 0),
                 'upperarm.L': (-0.6 * tl, 0, 0), 'upperarm.R': (-0.6 * tr, 0, 0),
                 'forearm.L': (12, 0, 0), 'forearm.R': (12, 0, 0),
                 'hips': (0, 5 if tl < 0 else -5 if tl > 0 else 0, 0), 'chest': (10, 0, 0), 'head': (-10, 0, 0)}
    clip(rig, 'move', soft(mv))
    clip(rig, 'attack', soft({
        1: {},
        7: {'upperarm.R': (70, 0, 0), 'forearm.R': (35, 0, 0), 'hand.R': (0, 0, 0), 'chest': (-6, -10, 0), 'head': (-6, 8, 0),
            'upperarm.L': (-10, 0, 0)},
        12: {'upperarm.R': (-25, 0, 0), 'forearm.R': (10, 0, 0), 'hand.R': (25, 0, 0), 'chest': (14, 10, 0), 'head': (4, -6, 0),
             'upperarm.L': (15, 0, 0)},
        18: {'upperarm.R': (5, 0, 0), 'forearm.R': (8, 0, 0), 'hand.R': (5, 0, 0), 'chest': (6, 6, 0), 'head': (0, 0, 0),
             'upperarm.L': (5, 0, 0)},
        24: {}}))
    if os.environ.get('GOB_DBG'):
        def tris(ob):
            eb = evaluated_bm(ob); bmesh.ops.triangulate(eb, faces=eb.faces[:]); eb.normal_update()
            return [(f.calc_center_median().copy(), f.normal.copy()) for f in eb.faces]
        rest(rig); bpy.context.view_layer.update()
        nm = {g.index: g.name for g in body.vertex_groups}
        for v in body.data.vertices:
            if (v.co - V(-0.287, -0.07, 0.27)).length < 0.05:
                say('WT', tuple(round(x, 3) for x in v.co), {nm[g.group]: round(g.weight, 2) for g in v.groups if g.weight > 0.05})
        r0 = tris(body)
        for act in bpy.data.actions:
            for fr in (6, 9, 12, 17, 18, 24, 25, 33, 36):
                pose(rig, act, fr)
                p = tris(body)
                bad = [tuple(round(x, 3) for x in c) for (c, n), (_, m) in zip(r0, p) if n.dot(m) < -0.2]
                if bad:
                    say('FLIP', act.name, fr, len(bad), bad[:6])
        rest(rig)
    return rig


ARM_AMP = 0.6


run(META, stage1, stage2, stage3, stage4)
