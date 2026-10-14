"""Mountain giant: a hunched stylised brute, box-modelled in four stages.

Built as the left half (x >= 0) under the live mirror. The trunk is a chain of
five-vertex half rings (eight-sided sections) that bends from the pelvis up
over the hump and forward into the low-set head; the legs and arms are
extruded out of the pelvis underside and the rib-cage side, the fists and feet
are built as boxes on the limb ends with the fingers, thumb and toes extruded
from their faces.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *
from mathutils import Euler, Matrix

META = dict(creature='giant', model='opus', engine_glb='example/gallery/giant.glb',
            closeups=[('head', (0.0, -1.30, 3.38), 0.62, 'hero'), ('fist', (1.45, -0.62, 1.12), 0.62, 'hero'),
                      ('moss and rocks', (0.0, 0.15, 3.85), 1.05, 'back34'), ('belt and loincloth', (0.0, -0.3, 1.35), 0.85, 'hero')])

# the skeleton the model is built on (left side; the rig mirrors .L to .R)
J = dict(
    root=(0.0, 0.05, 1.50), spine=(0.0, 0.00, 2.25), chest=(0.0, 0.02, 2.95),
    neck=(0.0, -0.58, 3.36), head=(0.0, -0.96, 3.34), head_end=(0.0, -1.55, 3.34),
    clav=(0.30, -0.15, 3.25), shoulder=(1.12, -0.06, 3.10), elbow=(1.47, -0.05, 2.20),
    wrist=(1.50, -0.46, 1.50), hand_end=(1.50, -0.50, 1.00),
    hip=(0.48, 0.05, 1.40), knee=(0.54, -0.13, 0.92), ankle=(0.56, 0.06, 0.38), toe=(0.58, -0.52, 0.10),
)


# ----------------------------------------------------------------------------- helpers
def ext_place(bm, faces, order, pts, seam=False):
    """Extrude a face region (E) and place its new boundary vertices (G).
    order: the region's boundary verts in template order; pts: their new positions.
    seam=True: the region touches the mirror plane; the side wall that the
    extrusion puts IN the plane is removed (the mirror closes it)."""
    pos = [v.co.copy() for v in order]
    r = extrude(bm, faces)
    nv = r['verts']
    new = [min(nv, key=lambda w: (w.co - p).length) for p in pos]
    if seam:
        bad = [f for f in r['sides'] if f.is_valid and all(abs(v.co.x) < 1e-6 for v in f.verts)]
        if bad:
            bmesh.ops.delete(bm, geom=bad, context='FACES_ONLY')
        wires = [e for e in bm.edges if not e.link_faces]
        if wires:
            bmesh.ops.delete(bm, geom=wires, context='EDGES')
    for w, p in zip(new, pts):
        w.co = Vector(p)
    return r['faces'], new


def frame_of(d, front=(0, -1, 0)):
    """Section axes for a limb running along d: F (front) and L (lateral, +x side)."""
    d = Vector(d).normalized()
    F = Vector(front)
    F = (F - d * F.dot(d)).normalized()
    L = F.cross(d).normalized()
    return F, L


def dirs(root, cs):
    """Bisector direction at each section centre along root -> cs."""
    pts = [Vector(root)] + [Vector(c) for c in cs]
    out = []
    for i in range(1, len(pts)):
        din = (pts[i] - pts[i - 1]).normalized()
        if i + 1 < len(pts):
            out.append((din + (pts[i + 1] - pts[i]).normalized()).normalized())
        else:
            out.append(din)
    return out


def limb(bm, faces, order, root, secs, front=(0, -1, 0)):
    """secs: [(centre, half_depth, half_width, template[(f, l), ...]), ...]."""
    ds = dirs(root, [s[0] for s in secs])
    for (c, hd, hw, tm), d in zip(secs, ds):
        F, L = frame_of(d, front)
        pts = [Vector(c) + F * (f * hd) + L * (l * hw) for f, l in tm]
        faces, order = ext_place(bm, faces, order, pts)
    return faces, order


def sweep(bm, faces, order, n0, e1, path, scl, zmin=None):
    """Extrude the root region along path, carrying its own shape (parallel
    transport from the root normal n0) and scaling it by (s1 along e1, s2 across)."""
    n0 = Vector(n0).normalized()
    e1 = Vector(e1); e1 = (e1 - n0 * e1.dot(n0)).normalized()
    e2 = n0.cross(e1)
    c0 = centre(order)
    ab = [((v.co - c0).dot(e1), (v.co - c0).dot(e2)) for v in order]
    ds = dirs(c0, path)
    for p, d, (s1, s2) in zip(path, ds, scl):
        R = n0.rotation_difference(d).to_matrix()
        pts = [Vector(p) + R @ (e1 * a * s1 + e2 * b * s2) for a, b in ab]
        if zmin is not None:
            for q in pts:
                q.z = max(q.z, zmin)
        faces, order = ext_place(bm, faces, order, pts)
    return faces, order


def quad(bm, *vs):
    return bm.faces.new(vs)


# ----------------------------------------------------------------------------- the fist (K=3 unlock)
# Separate finger roots with 5 cm gaps on the palm bottom, a knuckle row (each knuckle its own bump),
# varied finger lengths (middle longest, little ~25 % shorter), fingertips curled 20 deg further in.
HX, FS = 1.50, 1.38                          # fist centre x, fist scale (the signature: huge)
YF, YB = -0.52 - 0.14 * FS, -0.52 + 0.14 * FS
ZW, ZM, ZK = 1.44, 1.44 - 0.235 * FS, 1.44 - 0.30 * FS    # wrist end, knuckle ridge line, palm bottom
XL, XM = HX + 0.28 * FS, HX - 0.28 * FS      # lateral (little) / medial (index) edge of the fist
FW = [0.130, 0.155, 0.170, 0.167]            # finger widths: little, ring, middle, index
GAP = 0.04
YP = YF + 0.62 * (YB - YF)                  # finger roots end here; the palm heel is behind
FL = [0.76, 1.0, 1.13, 0.97]                 # finger length factors
KN_PROUD = [0.035, 0.045, 0.050, 0.045]      # knuckle bump: front verts forward (m)
CURL = [40, 58, 62, 58]                      # tip segment angle up-back (deg; was 45 on all)
KN_DROP = [-0.045, 0.0, 0.035, 0.012]        # knuckle hangs lower on the longer fingers (m)
FIST_TIPS = []                               # (tip centre, finger dir, dorsal dir, width, half depth) per finger


def _finger_edges():
    s = (XL - XM) / (sum(FW) + 3 * GAP)      # fit exactly between the fist edges
    xs, x = [], XL
    for i, w in enumerate(FW):
        xs += [x, x - w * s]
        x -= (w + GAP) * s
    return xs                                 # 8 x values, lateral -> medial


def fist_ring(z, grow, xf=None, dy=0.0):
    """12-vert hand ring: front 5 (lateral -> medial), MM, back 5 (medial -> lateral), LM."""
    xf = xf or [HX + d * FS for d in (0.28, 0.14, 0.0, -0.14, -0.28)]
    X = [HX + (x - HX) * grow for x in xf]
    return ([(x, YF + dy, z) for x in X] + [(HX - 0.32 * FS * grow, (YF + YB) / 2, z)] +
            [(x, YB, z) for x in reversed(X)] + [(HX + 0.32 * FS * grow, (YF + YB) / 2, z)])


def build_fist(bm, W6):
    hFM, hMM, hBM, hBL, hLM, hFL = W6
    E = _finger_edges()
    s = (XL - XM) / (sum(FW) + 3 * GAP)
    gaps = [(E[2 * i + 1] + E[2 * i + 2]) / 2 for i in range(3)]
    W = ring(bm, fist_ring(ZW, 0.79))
    M = ring(bm, fist_ring(ZM, 0.98, [E[0]] + gaps + [E[7]], dy=0.015))   # the knuckle ridge line: sunk behind the bumps
    # palm bottom: per finger a front row of 4 (corner, chamfer, chamfer, corner), a row behind the finger
    # roots (YP) and the back row; the palm heel between YP and the back is not a finger
    fx = []
    for i in range(4):
        ch = 0.24 * FW[i] * s
        fx += [E[2 * i], E[2 * i] - ch, E[2 * i + 1] + ch, E[2 * i + 1]]
    kf = ring(bm, [(x, YF + (0.012 if j % 4 in (0, 3) else 0.0), ZK) for j, x in enumerate(fx)])
    kp = ring(bm, [(x, YP, ZK) for x in E])
    kb = ring(bm, [(x, YB, ZK) for x in reversed(E)])                        # medial -> lateral
    kMM, kLM = ring(bm, [(HX - 0.32 * FS, (YF + YB) / 2, ZK), (HX + 0.32 * FS, (YF + YB) / 2, ZK)])
    # wrist -> back of the hand: explicit fans (no long n-gon fans)
    for t in ((hFL, W[0], W[1]), (hFL, W[1], W[2]), (hFL, W[2], hFM), (hFM, W[2], W[3]), (hFM, W[3], W[4]),
              (hBM, W[6], W[7]), (hBM, W[7], W[8]), (hBM, W[8], hBL), (hBL, W[8], W[9]), (hBL, W[9], W[10])):
        bm.faces.new(t)
    quad(bm, hFM, hMM, W[5], W[4]); quad(bm, hMM, hBM, W[6], W[5])
    quad(bm, hBL, hLM, W[11], W[10]); quad(bm, hLM, hFL, W[0], W[11])
    bridge(bm, W, M, closed=True)
    # knuckle ridge -> palm bottom
    for i in range(4):
        F = kf[4 * i:4 * i + 4]
        bm.faces.new([M[i], F[1], F[0]]); quad(bm, M[i], M[i + 1], F[2], F[1]); bm.faces.new([M[i + 1], F[3], F[2]])
        quad(bm, M[6 + i], M[7 + i], kb[2 * i + 1], kb[2 * i])
    for i in range(3):
        bm.faces.new([M[i + 1], kf[4 * i + 3], kf[4 * i + 4]])
        bm.faces.new([M[7 + i], kb[2 * i + 1], kb[2 * i + 2]])
    quad(bm, M[4], M[5], kMM, kf[15]); quad(bm, M[5], M[6], kb[0], kMM)
    quad(bm, M[10], M[11], kLM, kb[7]); quad(bm, M[11], M[0], kf[0], kLM)
    # palm bottom: gap floors, the palm heel strip and the end triangles; the finger roots are extruded
    for i in range(3):
        quad(bm, kf[4 * i + 3], kf[4 * i + 4], kp[2 * i + 2], kp[2 * i + 1])
    for j in range(7):
        quad(bm, kp[j], kp[j + 1], kb[6 - j], kb[7 - j])
    bm.faces.new([kf[15], kMM, kp[7]]); bm.faces.new([kp[7], kMM, kb[0]])
    bm.faces.new([kLM, kf[0], kp[0]]); bm.faces.new([kLM, kp[0], kb[7]])
    FIST_TIPS.clear()
    for i in range(4):
        q = kf[4 * i:4 * i + 4] + [kp[2 * i + 1], kp[2 * i]]
        f = bm.faces.new(q)
        c = centre(q)
        sp = (c.x - HX) * 0.12
        L = FL[i]
        curl = math.radians(CURL[i])
        kn = c + Vector((sp * 0.5, -0.05, -0.09)) * FS + Vector((0, 0, -KN_DROP[i]))
        p1 = c + Vector((sp * 1.3, 0.15 * L, -0.18 * L)) * FS
        ln = min(0.17 * FS * L, (ZK - 0.10 - p1.z) / math.sin(curl))   # the tip stays clear of the palm heel
        tip = p1 + Vector((sp * 0.1, math.cos(curl), math.sin(curl))) * ln
        secs = _sweep_pts([v.co.copy() for v in q], (0, 0, -1), (1, 0, 0), [kn, p1, tip],
                          [(1.0, 0.86), (0.86, 0.70), (0.78, 0.60)])
        for si, sec in enumerate(secs):
            sc = sum(sec, Vector()) / len(sec)
            fwd = ((sec[1] + sec[2]) / 2 - sc).normalized()
            bump = Vector((0, -1.0, 0.3)) * KN_PROUD[i] if si == 0 else Vector()
            for j in (0, 3):                 # chamfered front corners: the gaps open as V grooves
                sec[j] = sec[j] - fwd * 0.035 + bump * 0.5
            for j in (1, 2):                 # the knuckle's front stands proud: a bump per finger
                sec[j] = sec[j] + bump
        faces, order = [f], q
        for sec in secs:
            faces, order = ext_place(bm, faces, order, sec)
        tc = centre(order)
        fr = (order[1].co + order[2].co) / 2
        FIST_TIPS.append((tc.copy(), (tip - p1).normalized(), (fr - tc).normalized(),
                          (order[0].co - order[3].co).length, (fr - tc).length))
    # thumb: from the medial face of the hand; its tip section swings rigidly forward-down in front of
    # the index knuckle
    q = [W[4], W[5], M[5], M[4]]
    f = next(f for f in bm.faces if set(f.verts) == set(q))
    c = centre(q)
    secs = _sweep_pts([v.co.copy() for v in q], (-1, -0.2, 0), (0, 0, 1),
                      [c + Vector((-0.10, -0.02, -0.08)) * FS, c + Vector((-0.10, -0.06, -0.22)) * FS],
                      [(0.50, 0.95), (0.42, 0.80)])
    s1 = sum(secs[0], Vector()) / 4
    tcn = sum(secs[1], Vector()) / 4
    S = Vector(THUMB_TIP)
    Rt = (tcn - s1).normalized().rotation_difference((S - s1).normalized()).to_matrix()
    secs[1] = [S + Rt @ (p - tcn) for p in secs[1]]
    faces, order = [f], q
    for sec in secs:
        faces, order = ext_place(bm, faces, order, sec)


THUMB_TIP = (1.00, -0.92, 0.95)


# ----------------------------------------------------------------------------- stage 1
# trunk half rings: 0 front/bottom seam, 1 front corner, 2 side, 3 back corner, 4 back/top seam
TRUNK = dict(
    R0=[(0, -0.60, 1.42), (0.50, -0.50, 1.44), (0.84, 0.05, 1.52), (0.50, 0.60, 1.52), (0, 0.66, 1.55)],   # hips
    R1=[(0, -0.95, 1.98), (0.62, -0.80, 1.98), (0.93, 0.02, 2.05), (0.56, 0.68, 2.10), (0, 0.74, 2.10)],   # gut
    R2=[(0, -0.88, 2.62), (0.62, -0.78, 2.65), (0.98, -0.02, 2.70), (0.62, 0.72, 2.80), (0, 0.80, 2.85)],  # ribs / armpit
    R3=[(0, -0.90, 2.98), (0.64, -0.80, 3.08), (1.20, -0.04, 3.34), (0.80, 0.56, 3.58), (0, 0.66, 3.68)],  # shoulder
    R4=[(0, -0.96, 2.95), (0.52, -0.87, 3.06), (1.02, -0.12, 3.62), (0.70, 0.16, 3.84), (0, 0.14, 3.97)],  # hump / traps
    R5=[(0, -1.00, 2.90), (0.30, -0.97, 2.95), (0.46, -0.76, 3.25), (0.36, -0.52, 3.52), (0, -0.46, 3.55)],  # neck
    H0=[(0, -1.12, 2.80), (0.40, -1.07, 2.84), (0.47, -0.92, 3.16), (0.34, -0.80, 3.52), (0, -0.76, 3.63)],  # jaw hinge
    H1=[(0, -1.30, 2.78), (0.45, -1.26, 2.84), (0.47, -1.10, 3.10), (0.33, -1.02, 3.50), (0, -1.00, 3.61)],  # cheekbone
    H2=[(0, -1.50, 2.80), (0.41, -1.48, 2.85), (0.43, -1.28, 3.08), (0.36, -1.28, 3.38), (0, -1.18, 3.50)],  # face ring
)
ORDER = ['R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'H0', 'H1', 'H2']
HEAD_OFF = Vector((0.0, -0.08, 0.16))    # the head block as a whole (rings, face grid, nose)
NECK_OFF = Vector((0.0, -0.04, 0.09))


def hp(p):
    return Vector(p) + HEAD_OFF

# limb section templates in (front, lateral) units
LEG_T = [(1.0, 0.15), (0.15, 1.0), (-1.0, 0.35), (-0.65, -0.70), (0.0, -1.0), (0.62, -0.72)]
ARM_T = [(0.85, -0.55), (0.0, -1.0), (-0.85, -0.55), (-0.85, 0.55), (0.0, 1.0), (0.85, 0.55)]


def stage1(k):
    bm = bmesh.new()
    R = {n: ring(bm, [Vector(p) + (HEAD_OFF if n[0] == 'H' else NECK_OFF if n == 'R5' else Vector()) for p in TRUNK[n]])
         for n in ORDER}
    for a, b in zip(ORDER, ORDER[1:]):
        bridge(bm, R[a], R[b])
    v0, v1, v2, v3, v4 = R['R0']

    # --- pelvis underside: the crotch strip on the seam and the leg root (a hexagon of two quads)
    lf, lm, lb = ring(bm, [(0.22, -0.30, 1.30), (0.16, 0.05, 1.26), (0.22, 0.36, 1.32)])
    sa, sb = ring(bm, [(0, -0.34, 1.30), (0, 0.30, 1.30)])
    quad(bm, v0, v1, lf, sa); quad(bm, sa, lf, lm, sb); quad(bm, sb, lm, lb, v4); quad(bm, lb, v3, v4)
    legf = [quad(bm, v1, v2, v3, lb), quad(bm, lb, lm, lf, v1)]
    order = [v1, v2, v3, lb, lm, lf]
    root = centre(order)
    secs = [((0.50, 0.04, 1.20), 0.46, 0.40, LEG_T),     # thigh
            ((0.54, -0.10, 0.99), 0.36, 0.32, LEG_T),    # above the knee
            ((0.55, -0.13, 0.84), 0.33, 0.30, LEG_T),    # below the knee
            ((0.56, 0.00, 0.62), 0.33, 0.29, LEG_T),     # calf
            ((0.56, 0.06, 0.38), 0.24, 0.24, LEG_T)]     # ankle
    legf, A = limb(bm, legf, order, root, secs)
    # heel / sole ring on the ground
    S = [(0.56, -0.18, 0.0), (0.86, 0.08, 0.0), (0.56, 0.42, 0.0), (0.36, 0.36, 0.0), (0.28, 0.10, 0.0), (0.32, -0.12, 0.0)]
    legf, S = ext_place(bm, legf, A, S)
    # --- forefoot: replace the two front faces of the ankle band with the toe box
    fr = [f for f in bm.faces if set(f.verts) in ({A[5], A[0], S[0], S[5]}, {A[0], A[1], S[1], S[0]})]
    bmesh.ops.delete(bm, geom=fr, context='FACES_ONLY')
    tx = [0.26, 0.46, 0.67, 0.90]
    t = ring(bm, [(x, -0.44, 0.27 - 0.02 * i) for i, x in enumerate(tx)])
    u = ring(bm, [(x, -0.47, 0.0) for x in tx])
    bm.faces.new([A[5], A[0], A[1], t[3], t[2], t[1], t[0]])
    bm.faces.new([S[5], S[0], S[1], u[3], u[2], u[1], u[0]])
    quad(bm, A[5], t[0], u[0], S[5]); quad(bm, A[1], S[1], u[3], t[3])
    for i in range(3):
        f = quad(bm, t[i], t[i + 1], u[i + 1], u[i])
        c = centre([t[i], t[i + 1], u[i + 1], u[i]])
        spread = (c.x - 0.58) * 0.25
        sweep(bm, [f], [t[i], t[i + 1], u[i + 1], u[i]], (0, -1, 0), (1, 0, 0),
              [c + Vector((spread, -0.14, -0.03))], [(0.80, 0.78)], zmin=0.0)

    # --- arm: extruded from the two side faces between the rib ring and the shoulder ring
    a, b = R['R2'], R['R3']
    armf = [f for f in bm.faces if set(f.verts) in ({a[1], a[2], b[2], b[1]}, {a[2], a[3], b[3], b[2]})]
    order = [a[1], a[2], a[3], b[3], b[2], b[1]]
    root = centre(order)
    secs = [((1.36, -0.08, 3.08), 0.44, 0.40, ARM_T),    # deltoid
            ((1.42, -0.04, 2.62), 0.32, 0.30, ARM_T),    # upper arm
            ((1.46, -0.02, 2.28), 0.28, 0.26, ARM_T),    # above the elbow
            ((1.49, -0.08, 2.12), 0.30, 0.28, ARM_T),    # below the elbow
            ((1.52, -0.24, 1.86), 0.42, 0.37, ARM_T),    # forearm: heavier than the upper arm
            ((1.50, -0.44, 1.56), 0.26, 0.26, ARM_T)]    # wrist
    armf, W6 = limb(bm, armf, order, root, secs)
    # --- fist: a box under the wrist, back of the hand forward, knuckles down
    bmesh.ops.delete(bm, geom=armf, context='FACES_ONLY')
    build_fist(bm, W6)

    # --- face: a grid in front of the face ring. Rows: brow top, brow underside (nose root),
    # nose bottom, lower-jaw top (underbite), chin. The nose is extruded from the centre column.
    h0, h1, h2, h3, h4 = R['H2']
    b_, sb_, e_, se_, n_, sn_, j_, sj_ = ring(bm, [hp(p) for p in [
        (0.17, -1.46, 3.40), (0, -1.44, 3.41),       # brow bar top edge
        (0.14, -1.37, 3.29), (0, -1.36, 3.29),       # brow underside / nose root
        (0.17, -1.39, 3.03), (0, -1.41, 3.01),       # nose bottom / upper lip
        (0.21, -1.53, 2.98), (0, -1.55, 2.98)]])     # lower-jaw top edge, in front of the upper lip
    quad(bm, h4, h3, b_, sb_)            # forehead
    bm.faces.new([h3, e_, b_])           # outer end of the brow bar
    quad(bm, b_, e_, se_, sb_)           # brow bar front
    quad(bm, h3, h2, n_, e_)             # eye / cheek plane under the brow
    nose = quad(bm, e_, n_, sn_, se_)    # nose column
    quad(bm, h2, h1, j_, n_)             # jaw side
    quad(bm, n_, j_, sj_, sn_)           # lower-jaw ledge (underbite)
    quad(bm, h1, h0, sj_, j_)            # chin
    ext_place(bm, [nose], [e_, n_, sn_, se_],
              [hp(p) for p in [(0.09, -1.45, 3.26), (0.17, -1.60, 3.00), (0, -1.63, 2.99), (0, -1.45, 3.27)]], seam=True)
    # --- ear: a small blade from the side of the skull
    q = [R['H0'][2], R['H0'][3], R['H1'][3], R['H1'][2]]
    f = next(f for f in bm.faces if set(f.verts) == set(q))
    c = centre(q)
    sweep(bm, [f], q, (1, 0.1, 0), (0, 0, 1), [c + Vector((0.09, 0.05, 0.02)), c + Vector((0.16, 0.14, 0.07))],
          [(0.55, 0.55), (0.18, 0.22)])

    snap_seam(bm, 1e-4)
    recalc_normals(bm)
    ob = object_from_bm('body', bm)
    if os.environ.get('GIANT_DBG'):
        debug_hits(ob)
    if os.environ.get('GIANT_CLOSE'):
        close_ups(k, ob)
    return ob


def close_ups(k, ob):
    """Debug only: close clay/wire renders of the head and the fist (scratch folder)."""
    d = os.path.join(k.a.scratch, 'close')
    for tag, c, sz in (('head', (0.0, -1.25, 3.2), 1.5), ('fist', (1.5, -0.45, 1.2), 1.4)):
        fr = dict(centre=list(c), size=[sz, sz, sz])
        shoot(d, tag, fr, views=['az000', 'az045', 'az090', 'front34r', 'hero_low'], wire_views=['az045'], res=420, objs=[ob])


def debug_hits(ob):
    """Print the centres of self-intersecting face pairs (evaluated mesh)."""
    eb = evaluated_bm(ob)
    eb.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(eb)
    for i, j in t.overlap(t):
        if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
            ci, cj = eb.faces[i].calc_center_median(), eb.faces[j].calc_center_median()
            say('HIT', tuple(round(x, 2) for x in ci), tuple(round(x, 2) for x in cj))


def base(name, i):
    """Locked position of trunk/head ring vertex i."""
    off = HEAD_OFF if name[0] == 'H' else NECK_OFF if name == 'R5' else Vector()
    return Vector(TRUNK[name][i]) + off


def nudge(bm, p, d, r=1e-3):
    """Move the base vertex at locked position p by d."""
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < r, ('no vertex at', p, v.co)
    v.co += Vector(d)
    return v


def _sweep_pts(q, n0, e1, path, scl):
    """The stage-1 sweep() section positions (same maths), one list of len(q) points per section."""
    n0 = Vector(n0).normalized()
    e1 = Vector(e1); e1 = (e1 - n0 * e1.dot(n0)).normalized()
    e2 = n0.cross(e1)
    c0 = sum(q, Vector()) / len(q)
    ab = [((v - c0).dot(e1), (v - c0).dot(e2)) for v in q]
    out = []
    for p, d, (s1, s2) in zip(path, dirs(c0, path), scl):
        R = n0.rotation_difference(d).to_matrix()
        out.append([Vector(p) + R @ (e1 * a * s1 + e2 * b * s2) for a, b in ab])
    return out


def stage2(k, body):
    bm = edit(body)
    # ---------------------------------------------------------------- face
    # locked face-grid positions (stage 1)
    h3, h2 = base('H2', 3), base('H2', 2)
    F = {n: hp(p) for n, p in dict(b=(0.17, -1.46, 3.40), sb=(0, -1.44, 3.41), e=(0.14, -1.37, 3.29),
                                   se=(0, -1.36, 3.29), n=(0.17, -1.39, 3.03), sn=(0, -1.41, 3.01),
                                   j=(0.21, -1.53, 2.98), sj=(0, -1.55, 2.98)).items()}
    NT = {n: hp(p) for n, p in dict(e=(0.09, -1.45, 3.26), n=(0.17, -1.60, 3.00), sn=(0, -1.63, 2.99),
                                    se=(0, -1.45, 3.27)).items()}
    eye_face = next(f for f in bm.faces if {vert_near(bm, p) for p in (h3, h2, F['n'], F['e'])} == set(f.verts))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye/cheek plane under the brow'):
        inner = inset(bm, [eye_face], 0.30, 0.0)[0]
    # socket: the inner quad sits high under the brow bar and is pushed into the skull
    iv = sorted(inner.verts, key=lambda v: -v.co.z)
    top, bot = sorted(iv[:2], key=lambda v: v.co.x), sorted(iv[2:], key=lambda v: v.co.x)
    place([top[0], top[1], bot[0], bot[1]],
          [hp((0.195, -1.31, 3.25)), hp((0.315, -1.28, 3.27)), hp((0.20, -1.32, 3.15)), hp((0.32, -1.29, 3.16))])
    # heavy brow: the bar comes forward and down over the socket; its outer end reaches the temple
    brow = [nudge(bm, F['b'], (0.02, -0.04, -0.03)), nudge(bm, F['sb'], (0, -0.03, -0.05)),
            nudge(bm, h3, (0.03, -0.08, -0.06)),
            nudge(bm, F['e'], (0.0, -0.10, -0.01)), nudge(bm, F['se'], (0, -0.10, -0.01))]   # K=3: brow front faces forward
    # broad nose: flared bottom, blunt tip
    nose = {nudge(bm, NT['n'], (0.04, 0.0, 0.01)), nudge(bm, NT['sn'], (0, 0.0, 0.0)),
            nudge(bm, NT['e'], (-0.01, 0.0, 0.0)), vert_near(bm, NT['se'])}
    # mouth: upper lip recessed under the nose, lower jaw (underbite) juts forward and up
    lip = nudge(bm, F['n'], (0.0, 0.03, 0.0)); lip_s = nudge(bm, F['sn'], (0, 0.03, 0.0))
    jaw = nudge(bm, F['j'], (0.03, -0.05, -0.03)); jaw_s = nudge(bm, F['sj'], (0, -0.05, -0.03))
    # cheekbones out, jaw corners wide and low
    nudge(bm, h2, (0.04, -0.02, 0.0))
    nudge(bm, base('H2', 1), (0.05, -0.02, -0.03)); nudge(bm, base('H1', 1), (0.04, 0.0, -0.03))
    nudge(bm, base('H2', 0), (0, -0.04, -0.02))
    # ---------------------------------------------------------------- torso
    P = {n: [base(n, i) for i in range(5)] for n in ('R0', 'R1', 'R2', 'R3')}
    with k.topo(bm, 'loop', 'gut: a ring between the belly (R1) and the ribs (R2) for the upper curve of the gut'):
        e = next(e for e in bm.edges if {v.co.to_tuple(4) for v in e.verts} == {P['R1'][2].to_tuple(4), P['R2'][2].to_tuple(4)})
        gut = loopcut(bm, e, t=0.38, near=vert_near(bm, P['R1'][2]))
    for v in gut:                                   # round the belly forward under the rib line
        if v.co.y < -0.5:
            v.co.y -= 0.05 if v.co.x < 0.3 else 0.03
    nudge(bm, P['R1'][0], (0, -0.04, -0.08)); nudge(bm, P['R1'][1], (-0.04, -0.02, -0.07))   # gut sags
    nudge(bm, P['R0'][0], (0, -0.08, 0.0)); nudge(bm, P['R0'][1], (-0.02, -0.05, 0.0))
    nudge(bm, P['R2'][0], (0, 0.03, 0.0)); nudge(bm, P['R2'][1], (-0.03, 0.0, 0.0))        # crease under the pecs
    nudge(bm, P['R3'][0], (0, -0.03, 0.0)); nudge(bm, P['R3'][1], (0.0, -0.01, -0.02))       # pec shelf
    # K=3 jaw-chest seam: the R4 front row sat on the pec-shelf line (needle triangles). The trapezius front
    # corner rises onto the neck, and the seam row spreads forward between the pec shelf and the neck
    nudge(bm, base('R4', 1), (0.0, -0.01, 0.09)); nudge(bm, base('R4', 0), (0, -0.05, 0.02))
    nudge(bm, base('R5', 0), (0, -0.05, 0.0))
    for n in ('R1', 'R2', 'R3'):                    # spine groove between the lats
        nudge(bm, P[n][4], (0, -0.05, 0.0))
    # back: shoulder-blade planes stand out either side of the groove, the lumbar dips in, a trapezius hump
    nudge(bm, P['R3'][3], (0.03, 0.07, 0.0)); nudge(bm, P['R2'][3], (0.02, 0.05, 0.0))
    nudge(bm, P['R1'][3], (0.0, -0.04, 0.0)); nudge(bm, P['R1'][4] + Vector((0, -0.05, 0)), (0.0, -0.03, 0.0))
    nudge(bm, base('R4', 3), (0.0, 0.02, 0.05))
    # ---------------------------------------------------------------- humanoid face, head up
    # the face grid protruded 0.3 m in front of the face ring like an ape muzzle: compress it toward a
    # flatter face plane (the nose and the underbite jaw stay proud), and lift the head out of the shoulders
    for v in bm.verts:
        c = v.co
        if c.x > 0.7 or c.z < 2.85 or c.y > -0.78:
            continue
        if c.y < -1.34:
            c.y = -1.34 + (c.y + 1.34) * (0.80 if v in nose else 0.62)
        w = max(0.0, min(1.0, (-c.y - 0.80) / 0.30))
        c.z += 0.09 * w
        c.y += 0.04 * w
    for v in nose:                                  # the nose plane stands 3 cm prouder of the face
        v.co.y -= 0.03
    # knees forward, calves back
    for v in bm.verts:
        c = v.co
        if 0.25 < c.x < 0.95 and 0.75 < c.z < 1.05 and -0.7 < c.y < -0.3:   # not the thumb tip
            c.y -= 0.04
        elif 0.25 < c.x < 1.0 and 0.5 < c.z < 0.75 and c.y > 0.1:
            c.y += 0.04
    # shoulders: a rounded deltoid cap instead of a flat plate (top view read as a disc)
    for p, d in (((1.608, -0.08, 3.394), (-0.07, 0, 0.05)), ((1.507, -0.454, 3.244), (-0.03, 0.02, 0.06)),
                 ((1.486, 0.294, 3.261), (-0.03, -0.02, 0.06)), (tuple(base('R3', 2)), (0, 0, 0.09))):
        nudge(bm, p, d, r=2e-3)
    # armpit / pec-deltoid: the quad from the chest corner to the deltoid front was split on the diagonal
    # chest-bottom -> deltoid-top, and that triangle folds over in the overhead raise. The front deltoid
    # head bulges 6.5 cm (along the quad normal), so the fold-out diagonal becomes chest-top -> deltoid-low.
    nudge(bm, (1.234, -0.454, 2.899), Vector((0.434, -0.894, -0.115)) * 0.065, r=3e-3)
    k.g = dict(brow=[v.co.copy() for v in brow], lip=lip.co.copy(), jaw=jaw.co.copy(),
               mouth=[v.co.copy() for v in (lip, lip_s, jaw, jaw_s)])
    commit(body, bm)
    if os.environ.get('GIANT_DBG'):
        debug_hits(body)
    if os.environ.get('GIANT_QA2'):
        qa_debug(k, body, [])
    if os.environ.get('GIANT_CLOSE'):
        close_ups(k, body)


PALETTE = {'hide': '#66727f', 'jaw': '#55606c', 'stone': '#8b867c', 'fist': '#a58c67',
           'tusk': '#d6c9a6', 'eye': '#f4b427', 'black': '#343b46', 'moss': '#7f9f3a'}


def piece(name, bm, key, mirror=True):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: PALETTE[key]}, lambda c, n, i: key)
    return ob


def prism(bm, c, u, w, n, rad, depth, sides=6, rot=0.0):
    """A flat low-poly disc (eye, pupil): a `sides`-gon in the (u, w) plane, extruded along n."""
    c, u, w, n = Vector(c), Vector(u).normalized(), Vector(w).normalized(), Vector(n).normalized()
    pts = [c + (u * math.cos(rot + 2 * math.pi * i / sides) + w * math.sin(rot + 2 * math.pi * i / sides)) * rad
           for i in range(sides)]
    a = ring(bm, pts)
    b = ring(bm, [p + n * depth for p in pts])
    bridge(bm, a, b, closed=True)
    cap(bm, a); cap(bm, list(reversed(b)))


def nail(bm, o, X, Y, Z, w, l, s=0.010, t=0.014):
    """A nail wedge in the frame (X across, Y toward the tip, Z out of the digit) centred at o on the
    digit surface: flat bottom s below, the top slopes from the buried back edge up to t at the front.
    Returns the front face."""
    P = lambda x, y, z: bm.verts.new(o + X * x + Y * y + Z * z)
    B0, B1 = P(-w / 2, -l / 2, -s), P(w / 2, -l / 2, -s)
    F0, F1 = P(-w / 2, l / 2, -s), P(w / 2, l / 2, -s)
    T0, T1 = P(-w / 2 * 0.8, l / 2, t), P(w / 2 * 0.8, l / 2, t)
    bm.faces.new([B0, B1, F1, F0]); fr = bm.faces.new([F0, F1, T1, T0])
    bm.faces.new([B0, T0, T1, B1]); bm.faces.new([B0, F0, T0]); bm.faces.new([B1, T1, F1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return fr


def horn(bm, base, segs):
    """A tapered 4-sided horn: segs = [(offset, half_size), ...] from the base; the last one is the tip."""
    rows = []
    for off, h in segs[:-1]:
        c = Vector(base) + Vector(off)
        rows.append(ring(bm, [c + Vector((h, h, 0)), c + Vector((-h, h, 0)), c + Vector((-h, -h, 0)), c + Vector((h, -h, 0))]))
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1, closed=True)
    cap(bm, list(reversed(rows[0])))
    tip = bm.verts.new(Vector(base) + Vector(segs[-1][0]))
    r = rows[-1]
    for i in range(4):
        bm.faces.new([r[i], r[(i + 1) % 4], tip])


def _frame(n):
    n = Vector(n).normalized()
    t1 = Vector((0, 1, 0)).cross(n)
    t1 = t1.normalized() if t1.length > 1e-3 else Vector((1, 0, 0))
    return n, t1, n.cross(t1).normalized()


def clump(bm, bvh, hit, R, H, seed):
    """A moss clump: a 7-sided mound whose base ring is projected onto the body and sunk 4 cm
    (it drapes over the form), a shoulder ring and a lumpy top ring (three high lumps)."""
    c, n = hit
    n, t1, t2 = _frame(n)
    jit = [0.95, 1.08, 0.88, 1.02, 1.12, 0.9, 1.0]
    hB = [0.55, 0.75, 0.6, 0.8, 0.5, 0.72, 0.62]
    hC = [1.0, 0.72, 1.12, 0.8, 0.95, 0.7, 1.05]
    A, B, C = [], [], []
    for i in range(7):
        k_ = (i + seed * 3) % 7
        ph = 2 * math.pi * i / 7 + 0.3 * seed
        d = t1 * math.cos(ph) + t2 * math.sin(ph)
        q = c + d * R * jit[k_]
        loc, nrm, _, _ = bvh.ray_cast(q + n * 0.6, -n)
        if loc is None:
            loc, nrm = q, n
        A.append(loc - n * 0.045)
        B.append(loc.lerp(c, 0.16) + n * H * hB[k_])
        C.append(loc.lerp(c, 0.52) + n * H * hC[k_])
    a, b, cc = ring(bm, A), ring(bm, B), ring(bm, C)
    bridge(bm, a, b, closed=True); bridge(bm, b, cc, closed=True)
    cap(bm, list(reversed(a))); cap(bm, cc)
    recalc_normals(bm)


def rock(bm, c, n, r, sc, yaw, tilt, seed):
    """A chipped low-poly stone, its local Z on the surface normal, sunk ~30 % of its height."""
    g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    vs = g['verts']
    for i, v in enumerate(vs):
        if (i + seed) % 3 == 0:
            v.co *= 0.80
        elif (i + 2 * seed) % 5 == 0:
            v.co *= 1.08
        v.co = Vector((v.co.x * sc[0], v.co.y * sc[1], v.co.z * sc[2]))
    n, t1, t2 = _frame(n)
    M = Matrix((t1, t2, n)).transposed() @ Euler((math.radians(tilt), 0, math.radians(yaw))).to_matrix()
    h = 2 * r * sc[2]
    o = Vector(c) + n * (0.5 - 0.30) * h
    for v in vs:
        v.co = M @ v.co + o


def body_eval(body):
    """The body as exported: convex-triangulated and mirrored (a bmesh in world space)."""
    import bpy, techqa as Q
    c = body.copy(); c.data = body.data.copy()
    bpy.context.scene.collection.objects.link(c)
    Q.triangulate_convex(c)
    eb = evaluated_bm(c)
    bpy.data.objects.remove(c, do_unlink=True)
    return eb


def body_section(body, zs, xmax=1.05):
    """Horizontal sections of the body as it is exported (convex-triangulated, mirrored), at
    heights zs that all cross the same band of edges: [[p(z0), p(z1), ...] per crossed edge],
    ordered round the waist. Each consecutive pair spans one planar triangle strip."""
    eb = body_eval(body)
    lo, hi = min(zs), max(zs)
    out = []
    for e in eb.edges:
        a_, b_ = e.verts[0].co, e.verts[1].co
        if max(abs(a_.x), abs(b_.x)) > xmax or not (min(a_.z, b_.z) < lo and max(a_.z, b_.z) > hi):
            continue
        out.append([a_.lerp(b_, (z - a_.z) / (b_.z - a_.z)) for z in zs])
    eb.free()
    yc = sum(q[0].y for q in out) / len(out)
    out.sort(key=lambda q: math.atan2(q[0].x, -(q[0].y - yc)) % (2 * math.pi))
    return out


def loop_normals(pts):
    """Outward horizontal normals of a closed loop (bisector of the two edge normals)."""
    n = len(pts)
    cx = sum(p.x for p in pts) / n; cy = sum(p.y for p in pts) / n
    res = []
    for i in range(n):
        a_, b_, c_ = pts[i - 1], pts[i], pts[(i + 1) % n]
        m = Vector((0, 0, 0))
        for p, q in ((a_, b_), (b_, c_)):
            d = Vector((q.x - p.x, q.y - p.y, 0))
            if d.length > 1e-9:
                nn = Vector((d.y, -d.x, 0)).normalized()
                if nn.dot(Vector((b_.x - cx, b_.y - cy, 0))) < 0:
                    nn = -nn
                m += nn
        res.append(m.normalized() if m.length > 1e-9 else Vector((b_.x - cx, b_.y - cy, 0)).normalized())
    return res


def stage3(k, body):
    g = k.g
    bm = edit(body)                                 # read only: never committed
    bop = bm.verts.layers.int.get('bop')
    sock = [v for v in bm.verts if v[bop] == 1]
    sock_c = centre(sock)
    sock_f = next(f for f in bm.faces if set(f.verts) == set(sock))
    sock_n = sock_f.normal.copy()
    if sock_n.y > 0:
        sock_n = -sock_n
    near = lambda p, q: (p - q).length < 1e-4
    faces = {}
    for f in bm.faces:
        c = f.calc_center_median()
        key = 'hide'
        if c.z < 0.34:
            key = 'jaw'                                                # feet: the darker hide
        elif c.x > 0.95 and c.z < 1.50:
            key = 'hide'                                               # hands: the body's blue-grey
        elif all(v[bop] == 1 for v in f.verts):
            key = 'black'                                              # the socket's back: dark blue-grey
        elif all(any(near(v.co, p) for p in g['mouth']) for v in f.verts):
            key = 'black'                                              # the mouth line between the tusks
        elif any(v[bop] == 1 for v in f.verts):
            key = 'jaw'                                                # socket walls: shadowed hide
        elif all(any(near(v.co, p) for p in g['brow']) for v in f.verts):
            key = 'jaw'                                                # brow bar: the darker hide
        elif c.y < -1.0 and 2.8 < c.z and all(v.co.z <= g['lip'].z + 0.01 for v in f.verts):
            key = 'jaw'                                                # lower jaw, chin, under-jaw
        faces[f.index] = key
    # candidate faces for moss and rocks: up-facing shoulder / trap / hump planes, biggest first
    tops = sorted([f for f in bm.faces if f.normal.z > 0.35 and f.calc_center_median().z > 3.3
                   and f.calc_center_median().y > -0.75 and f.calc_center_median().x > 0.2],
                  key=lambda f: -f.calc_area())
    top_polys = [([v.co.copy() for v in f.verts], f.normal.copy(), f.calc_center_median()) for f in tops]
    toes = [(f.calc_center_median(), max(v.co.z for v in f.verts), max(v.co.x for v in f.verts) - min(v.co.x for v in f.verts))
            for f in bm.faces
            if f.normal.y < -0.8 and f.calc_center_median().z < 0.35 and f.calc_center_median().y < -0.55]
    bm.free()
    paint(body, {k_: PALETTE[k_] for k_ in ('hide', 'jaw', 'black', 'stone')}, lambda c, n, i: faces[i])

    pieces = []
    # eyes: a small gold iris in the socket and a dark pupil looking ahead and slightly down
    u = Vector((1, 0, 0)); w = sock_n.cross(u).normalized()
    if w.z < 0:
        w = -w
    ec = sock_c - w * 0.012
    bmE = bmesh.new(); prism(bmE, ec - sock_n * 0.02, u, w, sock_n, 0.044, 0.035, 8, math.radians(22.5))
    pieces.append(piece('eye', bmE, 'eye'))
    bmP = bmesh.new(); prism(bmP, ec + sock_n * 0.013 - w * 0.004, u, w, sock_n, 0.029, 0.010, 8, math.radians(22.5))
    pieces.append(piece('pupil', bmP, 'black'))
    # tusks: from the lower-jaw ledge, up past the upper lip, flaring out
    j = g['jaw']
    bmT = bmesh.new()
    horn(bmT, j + Vector((-0.01, 0.03, -0.05)), [((0, 0, 0), 0.045), ((0.02, -0.01, 0.10), 0.040),
                                                  ((0.05, 0.0, 0.19), 0.028), ((0.08, 0.03, 0.27), 0)])
    pieces.append(piece('tusk', bmT, 'tusk'))
    # nails (K=3): a wedge per toe and finger, 1/3 of the digit wide, its back sunk 1 cm into the digit, its
    # front 1.2 cm proud of the tip; mid blue-grey with only the front face dark
    bmN = bmesh.new()
    fronts = []
    for c, zt, wd in toes:
        fronts.append(nail(bmN, Vector((c.x, c.y + 0.035 - 0.012, zt - 0.012)), Vector((1, 0, 0)), Vector((0, -1, 0)),
                           Vector((0, 0, 1)), wd / 3, 0.07))
    for tc, d, f, wd, hd in FIST_TIPS:
        fronts.append(nail(bmN, tc + f * hd - d * (0.035 - 0.012), d.cross(f).normalized(), d, f, wd / 3, 0.07))
    bmN.faces.index_update()
    fi = {f_.index for f_ in fronts}
    nails = object_from_bm('nails', bmN)
    paint(nails, {'jaw': PALETTE['jaw'], 'black': PALETTE['black']}, lambda c, n, i: 'black' if i in fi else 'jaw')
    pieces.append(nails)
    # moss: four lumpy clumps draped over the traps, hump and one shoulder edge, a third sunk in;
    # rocks: three different stones (a chunky boulder bedded in the hump clump, a spire, a slab)
    ebB = body_eval(body)
    bvh = BVHTree.FromBMesh(ebB)
    ebB.free()

    def hit_down(x, y):
        loc, nrm, _, _ = bvh.ray_cast(Vector((x, y, 6.0)), Vector((0, 0, -1)))
        return loc, nrm
    bmM = bmesh.new()
    CLUMPS = [((0.92, -0.08), 0.32, 0.18, 0), ((-0.25, 0.18), 0.30, 0.20, 1),
              ((-0.90, -0.05), 0.26, 0.16, 2), ((0.45, 0.50), 0.25, 0.16, 3)]
    for (x, y), R, H, seed in CLUMPS:
        clump(bmM, bvh, hit_down(x, y), R, H, seed)
    pieces.append(piece('moss', bmM, 'moss', mirror=False))
    bmR = bmesh.new()
    # each stone beds into exactly one clump: boulder -> hump clump, spire -> back clump, slab -> right shoulder
    # K=3: non-uniform (about 1.0 / 0.7 / 0.5), each turned differently; the back spire lies ~30 deg flatter
    for (x, y), r, sc, yaw, tilt, seed in (((-0.20, 0.28), 0.29, (1.15, 0.80, 0.60), 20, 8, 0),
                                           ((0.36, 0.60), 0.25, (1.05, 0.72, 0.62), 55, 14, 1),
                                           ((-0.95, 0.12), 0.22, (1.30, 0.90, 0.50), -30, 12, 2)):
        loc, nrm = hit_down(x, y)
        rock(bmR, loc, nrm, r, sc, yaw, tilt, seed)
    pieces.append(piece('rocks', bmR, 'stone', mirror=False))
    # leather belt and loincloth: the humanoid read (a giant, not an ape). The belt follows the
    # body's own (triangulated) section 1 cm off the skin; the flaps are solid tapered wedges
    # whose tops tuck into the belt.
    ZB, ZT = 1.58, 1.72
    sec = body_section(body, [ZB, 0.5 * (ZB + ZT), ZT])
    keep = []
    for q in sec:                                  # drop crossings bunched within 7 cm (keep seam points)
        if keep and min((q[i_] - keep[-1][i_]).length for i_ in range(3)) < 0.07:
            if abs(q[0].x) < 1e-4:
                keep[-1] = q
            continue
        keep.append(q)
    if len(keep) > 2 and (keep[0][0] - keep[-1][0]).length < 0.07:
        keep.pop()
    sec = keep
    bmL = bmesh.new()
    rows = []
    for zi in (0, 2):
        pts = [q[zi] for q in sec]
        n2 = loop_normals(pts)
        dense, dn = [], []
        for a_ in range(len(pts)):
            b_ = (a_ + 1) % len(pts)
            nseg = max(1, math.ceil((sec[b_][0] - sec[a_][0]).length / 0.16))
            for t_ in range(nseg):
                f_ = t_ / nseg
                dense.append(pts[a_].lerp(pts[b_], f_))
                m = n2[a_].lerp(n2[b_], f_); dn.append(m.normalized() if m.length > 1e-6 else n2[a_])
        rows.append((dense, dn))
    (pb, nb), (pt, nt) = rows
    ib = ring(bmL, [p + n * 0.010 for p, n in zip(pb, nb)]); ob_ = ring(bmL, [p + n * 0.040 for p, n in zip(pb, nb)])
    it = ring(bmL, [p + n * 0.010 for p, n in zip(pt, nt)]); ot = ring(bmL, [p + n * 0.040 for p, n in zip(pt, nt)])
    bridge(bmL, ob_, ot, closed=True); bridge(bmL, ot, it, closed=True)
    bridge(bmL, it, ib, closed=True); bridge(bmL, ib, ob_, closed=True)

    def surf_y(x, z, front):
        """The body surface y at (x, z) on the front (or back) of the waist section."""
        zi = 0 if z <= ZB else (2 if z >= ZT else 1)
        pts = [q[zi] for q in sec]
        yc = sum(p_.y for p_ in pts) / len(pts)
        side = [p_ for p_ in pts if (p_.y < yc) == front]
        side.sort(key=lambda p_: p_.x)
        for a_, b_ in zip(side, side[1:]):
            if a_.x <= x <= b_.x and b_.x - a_.x > 1e-6:
                return a_.y + (b_.y - a_.y) * (x - a_.x) / (b_.x - a_.x)
        return min(side, key=lambda p_: abs(p_.x - x)).y
    # flaps (K=3): each a 3-segment plate, 2 quads across. The top row is tucked under the belt, every
    # vertex lies 6 mm off the skin it covers (ray cast along y: belly and thighs in front, buttocks
    # behind); where there is no skin (between the legs) the row runs straight across from its sides.
    # Thin toward the hem, the hem 15 % wider, its corners lifted and pulled in (rounded).
    def skin_y(x, z, front):
        sg_ = -1 if front else 1
        loc, _, _, _ = bvh.ray_cast(Vector((x, sg_ * 3.0, z)), Vector((0, -sg_, 0)))
        return loc.y if loc is not None and abs(loc.y) < 1.3 else None
    for front, HW in ((True, (0.28, 0.30, 0.32, 0.34, 0.39)), (False, (0.23, 0.25, 0.265, 0.28, 0.32))):
        sg = -1 if front else 1
        inner, outer = [], []
        prev = None
        for r, (z, th) in enumerate(FLAP_ROWS):
            w = HW[r]
            hem = r == len(FLAP_ROWS) - 1
            xs = [u * w * (0.90 if hem else 1.0) for u in (-1.0, -1 / 3, 1 / 3, 1.0)]
            zs = [z + (0.06 if hem and abs(u) > 0.5 else 0.0) for u in (-1.0, -1 / 3, 1 / 3, 1.0)]
            ys = [skin_y(x_, z_, front) for x_, z_ in zip(xs, zs)]
            ref = prev if prev is not None else next(y_ for y_ in ys if y_ is not None)
            ys = [y_ if y_ is not None and abs(y_ - ref) < (0.45 if front else 0.25) and not (abs(x_) < 0.2 and z_ < 1.36)
                  else None for y_, x_, z_ in zip(ys, xs, zs)]   # thighs yes, the crotch no
            for j in (1, 2):                       # between the legs: straight across from the sides
                if ys[j] is None:
                    sides = [y_ for y_ in (ys[0], ys[3]) if y_ is not None]
                    ys[j] = (sum(sides) / len(sides)) if sides else ref
            for j in (0, 3):
                if ys[j] is None:
                    ys[j] = ys[1 if j == 0 else 2]
            ys = [y_ + sg * 0.006 for y_ in ys]
            for _ in range(3):                     # the straight faces between columns stay outside the skin
                for a_, b_ in ((0, 1), (1, 2), (2, 3)):
                    for t_ in (0.25, 0.5, 0.75):
                        xm = xs[a_] + (xs[b_] - xs[a_]) * t_
                        zm = zs[a_] + (zs[b_] - zs[a_]) * t_
                        sy = skin_y(xm, zm, front)
                        ym = ys[a_] + (ys[b_] - ys[a_]) * t_
                        if sy is not None and abs(sy - ym) < 0.25 and sg * (sy + sg * 0.006 - ym) > 0:
                            push = sy + sg * 0.006 - ym
                            ys[a_] += push; ys[b_] += push
            if prev is not None and front:         # in front it follows the belly, then slants toward the thighs (<= 7 cm a row)
                ys = [prev_ys[j] + min(y_ - prev_ys[j], 0.07) for j, y_ in enumerate(ys)]
            if prev is not None and not front:     # behind, the cloth hangs from the buttocks: it recedes <= 3 cm a row
                ys = [prev_ys[j] + max(y_ - prev_ys[j], -0.03) for j, y_ in enumerate(ys)]
            if prev is not None and hem and not front:   # the hem hangs: it never tucks back under the row above
                ys = [y_ if sg * (y_ - prev_ys[j]) >= -0.03 else prev_ys[j] - sg * 0.03 for j, y_ in enumerate(ys)]
            prev, prev_ys = (ys[1] + ys[2]) / 2, ys
            if os.environ.get('GIANT_FLAP'):
                say('FLAP', front, z, [round(x_, 2) for x_ in xs], [round(y_, 3) for y_ in ys],
                    [None if y_ is None else round(y_, 3) for y_ in (skin_y(x_, z_, front) for x_, z_ in zip(xs, zs))])
            inner.append(ring(bmL, [Vector((x_, y_, z_)) for x_, y_, z_ in zip(xs, ys, zs)]))
            outer.append(ring(bmL, [Vector((x_, y_ + sg * th, z_)) for x_, y_, z_ in zip(xs, ys, zs)]))
        for r in range(len(FLAP_ROWS) - 1):
            bridge(bmL, outer[r], outer[r + 1]); bridge(bmL, inner[r + 1], inner[r])
            bmL.faces.new([outer[r][0], inner[r][0], inner[r + 1][0], outer[r + 1][0]])
            bmL.faces.new([outer[r + 1][-1], inner[r + 1][-1], inner[r][-1], outer[r][-1]])
        bridge(bmL, inner[0], outer[0]); bridge(bmL, outer[-1], inner[-1])
    recalc_normals(bmL)
    pieces.append(piece('loincloth', bmL, 'fist', mirror=False))
    return pieces


def stage4(k, body, pieces):
    Jh = dict(J, neck=(0.0, -0.40, 3.36), head=(0.0, -0.94, 3.42), head_end=(0.0, -1.55, 3.42))   # head lifted in stage 2
    rig = armature([
        ('hips', J['root'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], Jh['neck'], 'spine', True),
        ('neck', Jh['neck'], Jh['head'], 'chest', True),
        ('head', Jh['head'], Jh['head_end'], 'neck', True),
        ('clav.L', J['clav'], J['shoulder'], 'chest'),
        ('arm.L', J['shoulder'], J['elbow'], 'clav.L', True),
        ('fore.L', J['elbow'], J['wrist'], 'arm.L', True),
        ('hand.L', J['wrist'], J['hand_end'], 'fore.L', True),
        ('thigh.L', J['hip'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
        ('foot.L', J['ankle'], J['toe'], 'shin.L', True),
    ])
    skin(body, rig)
    blend_shoulders(body)
    cap_deltoid(body, 0.3)
    for p in pieces:
        nm = p.name.replace('piece_', '')
        if nm in ('eye', 'pupil', 'tusk'):
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)            # moss, rocks, belt, loincloth, toenails ride the skin under them
            if nm in ('moss', 'rocks', 'loincloth', 'nails'):
                seat_weights(p, body)                      # exactly the weights of the exported skin point below
            if nm == 'loincloth':                          # the hem hangs: half its own seat, half its row's
                blend_rows(p, 1.40, 0.5)

    def sym(d):
        """Mirror a pose dict: .L keys also drive .R (same bone-local angles, Z/Y flipped)."""
        out = dict(d)
        for b_, (x, y, z) in d.items():
            if b_.endswith('.L') and b_[:-2] + '.R' not in d:
                out[b_[:-2] + '.R'] = (x, -y, -z)
        return out

    # idle: heavy breathing (chest and shoulders rise), the head sways
    # idle: heavy breathing (chest and shoulders rise), the head sways; the spine pitches ~12 deg
    # forward (the hunch) and the neck/head counter-rotate so the gaze stays level
    def hunch(d, sp=7, ch=5, nk=-6, hd=-6):
        o = dict(d)
        for b_, add in (('spine', sp), ('chest', ch), ('neck', nk), ('head', hd)):
            x, y, z = o.get(b_, (0, 0, 0))
            o[b_] = (x + add, y, z)
        return o
    clip(rig, 'idle', {
        1: hunch(sym({'spine': (0, 0, 0), 'chest': (0, 0, 0), 'clav.L': (0, 0, 0), 'neck': (0, 0, 0), 'head': (0, 0, 0)})),
        13: hunch(sym({'spine': (-2, 0, 0), 'chest': (-4, 0, 0), 'clav.L': (0, 0, 5), 'neck': (3, 0, 0), 'head': (0, 4, -3)})),
        25: hunch(sym({'spine': (-1, 0, 0), 'chest': (-2, 0, 0), 'clav.L': (0, 0, 2), 'neck': (1, 0, 0), 'head': (0, 0, 0)})),
        37: hunch(sym({'spine': (1, 0, 0), 'chest': (1, 0, 0), 'clav.L': (0, 0, -1), 'neck': (-1, 0, 0), 'head': (0, -4, 3)})),
        48: hunch(sym({'spine': (0, 0, 0), 'chest': (0, 0, 0), 'clav.L': (0, 0, 0), 'neck': (0, 0, 0), 'head': (0, 0, 0)})),
    })
    # move: a lumbering walk; legs and arms in opposition, the chest rolls with the stride
    A = dict(STEP=24, ARM=20)
    def walk(ph):
        s_ = 1 if ph == 0 else -1
        return {'thigh.L': (s_ * A['STEP'], 0, 0), 'thigh.R': (-s_ * A['STEP'], 0, 0),
                'shin.L': (-10 if s_ > 0 else -30, 0, 0), 'shin.R': (-30 if s_ > 0 else -10, 0, 0),
                'foot.L': (-8 * s_, 0, 0), 'foot.R': (8 * s_, 0, 0),
                'arm.L': (-s_ * A['ARM'], 0, 0), 'arm.R': (s_ * A['ARM'], 0, 0),
                'fore.L': (-10, 0, 0), 'fore.R': (-10, 0, 0),
                'chest': (4, 6 * s_, 0), 'spine': (3, 0, 3 * s_), 'head': (0, -4 * s_, 0)}
    def mid(s_):
        return {'thigh.L': (0, 0, 0), 'thigh.R': (0, 0, 0), 'shin.L': (-25 if s_ > 0 else -5, 0, 0),
                'shin.R': (-5 if s_ > 0 else -25, 0, 0), 'foot.L': (0, 0, 0), 'foot.R': (0, 0, 0),
                'arm.L': (0, 0, 0), 'arm.R': (0, 0, 0), 'fore.L': (-14, 0, 0), 'fore.R': (-14, 0, 0),
                'chest': (5, 0, 0), 'spine': (3, 0, 0), 'head': (0, 0, 0)}
    clip(rig, 'move', {f: hunch(p, 5, 3, -4, -4) for f, p in ((1, walk(0)), (9, mid(1)), (17, walk(1)), (25, mid(-1)),
                                                              (33, walk(0)))},
         loc={1: {'hips': (0, -0.05, 0)}, 9: {'hips': (0, 0.03, 0)}, 17: {'hips': (0, -0.05, 0)},
              25: {'hips': (0, 0.03, 0)}, 33: {'hips': (0, -0.05, 0)}})
    # attack: an overhead double-fist slam — wind up (arms up, torso back), then down hard
    rest0 = sym({'arm.L': (0, 0, 0), 'fore.L': (0, 0, 0), 'clav.L': (0, 0, 0), 'spine': (0, 0, 0),
                 'chest': (0, 0, 0), 'neck': (0, 0, 0), 'head': (0, 0, 0), 'thigh.L': (0, 0, 0), 'shin.L': (0, 0, 0)})
    up = sym({'arm.L': (-85, 0, 18), 'fore.L': (-35, 0, 0), 'clav.L': (0, 0, 20), 'spine': (-10, 0, 0),
              'chest': (-14, 0, 0), 'neck': (-8, 0, 0), 'head': (-6, 0, 0), 'thigh.L': (0, 0, 0), 'shin.L': (0, 0, 0)})
    slam = sym({'arm.L': (-40, 0, 15), 'fore.L': (-10, 0, 0), 'clav.L': (0, 0, -6), 'spine': (14, 0, 0),
                'chest': (20, 0, 0), 'neck': (-10, 0, 0), 'head': (-8, 0, 0), 'thigh.L': (18, 0, 0), 'shin.L': (-28, 0, 0)})
    clip(rig, 'attack', {1: rest0, 12: up, 18: up, 23: slam, 30: slam, 40: rest0},
         loc={1: {'hips': (0, 0, 0)}, 12: {'hips': (0, 0.03, 0)}, 23: {'hips': (0, -0.12, 0)},
              30: {'hips': (0, -0.12, 0)}, 40: {'hips': (0, 0, 0)}})
    if os.environ.get('GIANT_FLIP'):
        gn = {g.index: g.name for g in body.vertex_groups}
        for v in body.data.vertices:
            if v.co.x > 0 and (v.co - Vector((1.1, -0.56, 2.95))).length < 0.55:
                say('VW', v.index, tuple(round(c, 3) for c in v.co),
                    {gn[g.group]: round(g.weight, 2) for g in v.groups if g.weight > 0.02})
        for p in body.data.polygons:
            if p.center.x > 0 and (p.center - Vector((1.1, -0.56, 2.95))).length < 0.35:
                say('VF', p.index, list(p.vertices), tuple(round(c, 3) for c in p.center))
    if os.environ.get('GIANT_QA'):
        qa_debug(k, body, pieces, rig, {a.name: a for a in bpy.data.actions})
    return rig


FLAP_ROWS = [(1.68, 0.036), (1.52, 0.034), (1.42, 0.033), (1.30, 0.032), (1.08, 0.030)]   # loincloth rows: z, thickness


def seat_weights(ob, body):
    """Give each piece vertex the skin weights of its nearest point on the body as it is
    exported (convex-triangulated): barycentric over that triangle, so the piece moves
    with its seat (the drift gate measures against the same triangles)."""
    import techqa as Q
    c = body.copy(); c.data = body.data.copy()
    bpy.context.scene.collection.objects.link(c)
    Q.triangulate_convex(c)
    me = c.data
    M = c.matrix_world
    bV = [M @ v.co for v in me.vertices]
    tris = [tuple(p.vertices) for p in me.polygons]
    bw = [{body.vertex_groups[g.group].name: g.weight for g in v.groups} for v in me.vertices]
    bpy.data.objects.remove(c, do_unlink=True)
    bt = BVHTree.FromPolygons(bV, tris, all_triangles=True)
    for vg in list(ob.vertex_groups):
        ob.vertex_groups.remove(vg)
    for v in ob.data.vertices:
        loc, _, ti, _ = bt.find_nearest(ob.matrix_world @ v.co)
        t = tris[ti]
        bc = Q._bary(loc, *(bV[j] for j in t))
        acc = {}
        for j, u in zip(t, bc):
            for n_, w in bw[j].items():
                acc[n_] = acc.get(n_, 0.0) + w * u
        s = sum(acc.values()) or 1.0
        for n_, w in acc.items():
            if w / s > 1e-4:
                (ob.vertex_groups.get(n_) or ob.vertex_groups.new(name=n_)).add([v.index], w / s, 'REPLACE')


def blend_rows(ob, zmax, a):
    """Flap vertices below zmax: blend (1-a) of their own weights with a of the average over their
    row (same z within 2 cm, same side of the body), so the hem does not shear between the thighs."""
    me = ob.data
    gi = {g.index: g.name for g in ob.vertex_groups}
    W = {v.index: {gi[g.group]: g.weight for g in v.groups} for v in me.vertices}
    rows = {}
    for v in me.vertices:
        co = ob.matrix_world @ v.co
        if co.z < zmax and abs(co.x) < 0.5:
            rows.setdefault((round(co.z / 0.02), co.y > 0), []).append(v.index)
    for ids in rows.values():
        avg = {}
        for i in ids:
            for n_, w in W[i].items():
                avg[n_] = avg.get(n_, 0.0) + w / len(ids)
        for i in ids:
            out = {n_: (1 - a) * W[i].get(n_, 0.0) + a * avg.get(n_, 0.0) for n_ in set(W[i]) | set(avg)}
            t = sum(out.values()) or 1.0
            for vg in ob.vertex_groups:
                vg.remove([i])
            for n_, w in out.items():
                if w / t > 0.005:
                    ob.vertex_groups[n_].add([i], w / t, 'REPLACE')


def even_weights(ob, key):
    """Average the transferred skin weights over groups of a piece's vertices.
    key(shell, co) -> a group id (None: keep the vertex's own weights); shell is
    'belt' for a shell that wraps the waist, else the shell's index."""
    me = ob.data
    gi = {g.index: g.name for g in ob.vertex_groups}
    nbr = {v.index: set() for v in me.vertices}
    for e in me.edges:
        i, j = e.vertices
        nbr[i].add(j); nbr[j].add(i)
    shell, sid = {}, 0
    for v in me.vertices:
        if v.index in shell:
            continue
        stack = [v.index]; shell[v.index] = sid
        while stack:
            for j in nbr[stack.pop()]:
                if j not in shell:
                    shell[j] = sid; stack.append(j)
        sid += 1
    wraps = {s for s in range(sid) if {me.vertices[i].co.y > 0 for i in shell if shell[i] == s} == {True, False}
             and max(abs(me.vertices[i].co.x) for i in shell if shell[i] == s) > 0.5}
    groups = {}
    for v in me.vertices:
        s = shell[v.index]
        g = key('belt' if s in wraps else s, ob.matrix_world @ v.co)
        if g is not None:
            groups.setdefault((s, g), []).append(v.index)
    for ids in groups.values():
        acc = {}
        for i in ids:
            for g in me.vertices[i].groups:
                acc[gi[g.group]] = acc.get(gi[g.group], 0.0) + g.weight / len(ids)
        t = sum(acc.values()) or 1.0
        for vg in ob.vertex_groups:
            vg.remove(ids)
        for n_, w in acc.items():
            if w / t > 0.005:
                ob.vertex_groups[n_].add(ids, w / t, 'REPLACE')


def cap_deltoid(body, keep=0.3, dz=0.12):
    """Verts of the deltoid cap that sit ABOVE the shoulder joint's front swing backward over the
    joint in the overhead raise and fold the pec-deltoid plane over; they keep only `keep` of
    their upper-arm weight and hand the rest to the clavicle (the joint bends below them)."""
    for v in body.data.vertices:
        p = v.co
        s = 'L' if p.x >= 0 else 'R'
        if not (1.0 < abs(p.x) < 1.75 and p.z > J['shoulder'][2] + dz and p.y < -0.2):
            continue
        ga, gc = body.vertex_groups.get('arm.' + s), body.vertex_groups.get('clav.' + s)
        wa = next((g.weight for g in v.groups if g.group == ga.index), 0.0)
        wc = next((g.weight for g in v.groups if g.group == gc.index), 0.0)
        if wa > 0:
            ga.add([v.index], wa * keep, 'REPLACE')
            gc.add([v.index], wc + wa * (1 - keep), 'REPLACE')


def blend_shoulders(body, reps=8, a=0.5):
    """Widen the heat-weight seam between the chest/clavicle and the upper arm: a few
    Laplacian passes over every bone's weight, only on the shoulder region (deltoid,
    trapezius, armpit), so the seam loop ends up ~50/50 instead of a hard step."""
    me = body.data
    gi = {g.index: g.name for g in body.vertex_groups}
    nbr = {v.index: set() for v in me.vertices}
    for e in me.edges:
        i, j = e.vertices
        nbr[i].add(j); nbr[j].add(i)
    reg = []
    for v in me.vertices:
        p = v.co
        S = Vector((J['shoulder'][0] * (1 if p.x >= 0 else -1), J['shoulder'][1], J['shoulder'][2]))
        if abs(p.x) > 0.45 and p.z > 2.55 and (p - S).length < 0.85:
            reg.append(v.index)
    W = {v.index: {gi[g.group]: g.weight for g in v.groups} for v in me.vertices}
    for _ in range(reps):
        new = {}
        for i in reg:
            acc = {}
            for j in nbr[i]:
                for n_, w in W[j].items():
                    acc[n_] = acc.get(n_, 0.0) + w / len(nbr[i])
            out = {n_: (1 - a) * W[i].get(n_, 0.0) + a * acc.get(n_, 0.0) for n_ in set(W[i]) | set(acc)}
            t = sum(out.values()) or 1.0
            new[i] = {n_: w / t for n_, w in out.items() if w / t > 0.01}
        W.update(new)
    for i in reg:
        for g in body.vertex_groups:
            g.remove([i])
        for n_, w in W[i].items():
            (body.vertex_groups.get(n_) or body.vertex_groups.new(name=n_)).add([i], w, 'REPLACE')


def qa_debug(k, body, pieces, rig=None, acts=None):
    """Debug only (GIANT_QA=1): where the tech-QA flags sit, per class, on copies."""
    import bpy, techqa as Q
    tmp = []
    for o in [body] + list(pieces):
        c = o.copy(); c.data = o.data.copy(); c.name = 'dbg_' + o.name
        bpy.context.scene.collection.objects.link(c); tmp.append(c)
        Q.triangulate_convex(c, keep=k.meta.get('keep_valleys'))
    size = k.frame['size']
    if os.environ.get('GIANT_DRIFT') and acts:          # per-vertex seat gap growth (the drift measure)
        bV, bT, _ = Q._evaluated(tmp[0])
        bt = BVHTree.FromPolygons(bV, [t for _, t in bT], all_triangles=True)
        seats = {}
        for o in tmp[1:]:
            V, _, _ = Q._evaluated(o)
            for i, p in enumerate(V):
                loc, _, ti, d = bt.find_nearest(p)
                a_, b_, c_ = (bV[j] for j in bT[ti][1])
                seats[(o.name, i)] = (p.copy(), ti, Q._bary(loc, a_, b_, c_), d)
        worst = {}
        for n, a in acts.items():
            rig.animation_data.action = a
            fr = a.frame_range
            for f in [fr[0] + (fr[1] - fr[0]) * s for s in (0.2, 0.4, 0.6, 0.8)]:
                bpy.context.scene.frame_set(int(f))
                bVp, bTp, _ = Q._evaluated(tmp[0])
                for o in tmp[1:]:
                    Vp, _, _ = Q._evaluated(o)
                    for i, p in enumerate(Vp):
                        p0, ti, (u, w, x), d0 = seats[(o.name, i)]
                        if d0 > 0.03:
                            continue
                        a_, b_, c_ = (bVp[j] for j in bTp[ti][1])
                        g = (p - (a_ * u + b_ * w + c_ * x)).length - d0
                        key = (o.name, i)
                        if g > worst.get(key, (0,))[0]:
                            worst[key] = (g, n, int(f), tuple(round(c, 2) for c in p0))
        for o in tmp[1:]:
            ws = sorted([v for (on, _), v in worst.items() if on == o.name], reverse=True)[:6]
            say('DRIFT', o.name[4:], [(round(g, 3), n, f, p) for g, n, f, p in ws])
        rig.animation_data.action = None
        bpy.context.scene.frame_set(1)
    if os.environ.get('GIANT_FLIPF') and acts:          # fold-over per frame (techqa's criterion), body only
        o = tmp[0]
        V, T, P = Q._evaluated(o)
        rn = [Q._tri_normal(V, t) for _, t in T]
        nbr = {}
        for ti, (_, t) in enumerate(T):
            for v in t:
                nbr.setdefault(v, []).append(ti)
        for n, a in acts.items():
            rig.animation_data.action = a
            fr = a.frame_range
            for f in range(int(fr[0]), int(fr[1]) + 1, 2):
                bpy.context.scene.frame_set(f)
                Vp, Tp, _ = Q._evaluated(o)
                pn = [Q._tri_normal(Vp, t) for _, t in Tp]
                bad = []
                for ti, (_, t) in enumerate(Tp):
                    ring_ = {x for v in t for x in nbr[v] if x != ti}
                    avg = sum((pn[x][0] for x in ring_), Vector()); avg0 = sum((rn[x][0] for x in ring_), Vector())
                    if (avg.length > 1e-9 and pn[ti][0].dot(avg.normalized()) < -0.2 and rn[ti][0].dot(avg0.normalized()) > 0.3) \
                            or pn[ti][1] < 0.2 * rn[ti][1]:
                        c_ = sum((V[i] for i in t), Vector()) / 3
                        if c_.x > 0:
                            bad.append((tuple(round(x, 2) for x in c_), t, round(rn[ti][1], 3)))
                if bad:
                    say('FLIPF', n, f, bad)
                if n == 'attack' and f == 15:
                    say('POS15', [(i, tuple(round(c, 2) for c in Vp[i])) for i in (11, 16, 106, 109, 107, 12)])
        rig.animation_data.action = None
        bpy.context.scene.frame_set(1)
        return
    runs = [('rest', None)] + ([(n, {n: a}) for n, a in acts.items()] if acts else [])
    for lab, a in runs:
        counts, flags, tris = Q.measure(tmp[0], tmp[1:], size, rig if a else None, a)
        for o in tmp:
            by = {}
            for pi, cls in flags[o.name].items():
                if a is not None and cls not in ('flip', 'drift'):
                    continue
                c_ = o.matrix_world @ o.data.polygons[pi].center
                by.setdefault(cls, []).append(tuple(round(x, 2) for x in c_))
            for cls, cs in by.items():
                say('QA', lab, o.name[4:], cls, len(cs), sorted(cs)[:40])
    for c in tmp:
        bpy.data.objects.remove(c, do_unlink=True)


run(META, stage1, stage2, stage3, stage4)
