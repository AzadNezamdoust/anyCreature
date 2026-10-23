import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# mantis (t7x zoo, workflow v2): ONE spine loft of 10-vertex half rings runs from the triangular face (eye bulbs on
# the top corners) through the neck pinch, down the long prothorax, over the pterothorax and along the deep leaf
# abdomen to its tip; every ring sits on the centre line's normal plane. The raptorial forelegs grow as octagon tubes
# from 2x2 face blocks under the prothorax front (coxa down, femur folded up-forward, tibia folded back down); the
# four walking legs grow from 2x2 blocks on the pterothorax lower flank (coxa down, femur up to a high knee, tibia
# down to the ground). Joints turn on fillet arcs (three rings) so no ring crosses its neighbour inside a bend.
# Identity cue (NOTES): raised folded spiked forelegs in front of a long upright neck + a triangular head with corner
# eyes + a long leaf abdomen under folded wings on four stilt legs.
META = dict(creature='mantis', model='opus', engine_glb='', stage1_tris=(1500, 6500), total_tris=(2500, 7500),
            closeups=[('raptorial foreleg', (0.07, -0.29, 0.28), 0.14, 'hero'),
                      ('face and eyes', (0.0, -0.28, 0.43), 0.09, 'hero'),
                      ('leg roots', (0.05, -0.04, 0.24), 0.12, 'hero_low'),
                      ('wings', (0.0, 0.17, 0.2), 0.24, 'az090')])

# ------------------------------------------------------------------------------------------------ the spine
# centre line z(y), read off the side view (head level, prothorax down at ~40 deg, abdomen sloping to the tip)
CL = [(-0.345, 0.425), (-0.300, 0.425), (-0.250, 0.426), (-0.222, 0.425), (-0.212, 0.420), (-0.198, 0.409),
      (-0.150, 0.369), (-0.110, 0.335), (-0.085, 0.313), (-0.060, 0.295), (-0.030, 0.277), (0.000, 0.262),
      (0.040, 0.243), (0.090, 0.218), (0.150, 0.188), (0.210, 0.162), (0.270, 0.139), (0.330, 0.119), (0.400, 0.098)]


def zc(y):
    """Catmull-Rom through CL (monotone in y), and the tangent angle (deg, from +Y toward +Z)."""
    P = CL
    i = 0
    while i < len(P) - 2 and P[i + 1][0] < y:
        i += 1
    p0 = P[i - 1] if i > 0 else (2 * P[0][0] - P[1][0], 2 * P[0][1] - P[1][1])
    p1, p2 = P[i], P[i + 1]
    p3 = P[i + 2] if i + 2 < len(P) else (2 * P[-1][0] - P[-2][0], 2 * P[-1][1] - P[-2][1])
    # solve t for y on the segment (y is monotone): a few Newton steps on the cubic in y
    def cr(t, k):
        a, b, c, d = p0[k], p1[k], p2[k], p3[k]
        return 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
    def dcr(t, k):
        a, b, c, d = p0[k], p1[k], p2[k], p3[k]
        return 0.5 * ((-a + c) + 2 * (2 * a - 5 * b + 4 * c - d) * t + 3 * (-a + 3 * b - 3 * c + d) * t * t)
    t = (y - p1[0]) / max(p2[0] - p1[0], 1e-9)
    for _ in range(8):
        t -= (cr(t, 0) - y) / max(dcr(t, 0), 1e-9)
    return cr(t, 1), math.degrees(math.atan2(dcr(t, 1), dcr(t, 0)))


# half-ring profiles (top seam -> bottom seam), (fx, fh): x = fx * W, h = fh * (T if fh >= 0 else B)
# s1 r2: the head ring is built per station: the face triangle (top centre, cheek, mouth) with the eye bulb on its
# top corner, sliced from a sphere (centre y -0.256, r 0.03): round in the front AND the side view (r00/r01 lofted
# one profile at constant height: a flat T-bar box). (zt top centre, zb mouth/bottom seam, bulb cx, cz, slice e)
# s1 r5: the vertex between the eyes sits 1.2 cm under the bulb tops (r04's flat top bar read as an anvil in az000)
HEADS = {'H0': (0.432, 0.392, 0.022, 0.430, 0.008), 'H1': (0.443, 0.376, 0.031, 0.441, 0.010),
         'H2': (0.450, 0.372, 0.040, 0.444, 0.016), 'H3': (0.454, 0.376, 0.045, 0.444, 0.023),
         'H4': (0.456, 0.384, 0.047, 0.443, 0.027), 'H5': (0.456, 0.392, 0.048, 0.443, 0.028),
         'H6': (0.453, 0.400, 0.046, 0.443, 0.024), 'H7': (0.446, 0.404, 0.040, 0.441, 0.015)}
BULB_A = (120, 55, -5, -65)        # bulb vertices 2-5: angles on the slice circle (deg from +X toward +Z)


def head_pts(nm, y):
    zt, zb, cx, cz, e = HEADS[nm]
    out = [Vector((0, y, zt)), Vector((cx * 0.45, y, zt - 0.002))]
    for a in BULB_A:
        t = math.radians(a)
        out.append(Vector((cx + e * math.cos(t), y, cz + e * math.sin(t))))
    z6 = cz - max(e, 0.012) - 0.01
    out += [Vector((0.62 * cx, y, z6)), Vector((0.42 * cx, y, z6 + (zb - z6) * 0.45)),
            Vector((0.22 * cx, y, z6 + (zb - z6) * 0.85)), Vector((0, y, zb))]
    return out


# thorax + abdomen: domed back (the wing seat, vertices 0-4), widest at vertex 4 (the wing edge), a flat lower
# flank (vertices 5-7: the leg-root band) and a narrower keel belly
BODYP = [(0, 1), (0.45, 0.96), (0.8, 0.78), (0.98, 0.45), (1.0, 0.1), (0.94, -0.25), (0.8, -0.55), (0.58, -0.8),
         (0.3, -0.95), (0, -1)]
NECKP = [(0, 1), (0.42, 0.95), (0.78, 0.76), (0.97, 0.42), (1.0, 0.05), (0.95, -0.3), (0.8, -0.6), (0.56, -0.84),
         (0.28, -0.97), (0, -1)]

# stations: (name, y, T, B, W, profile)
SECS = [
    ('H0', -0.327, 0, 0, 0, 'HEAD'),
    ('H1', -0.318, 0, 0, 0, 'HEAD'),
    ('H2', -0.302, 0, 0, 0, 'HEAD'),
    ('H3', -0.286, 0, 0, 0, 'HEAD'),
    ('H4', -0.270, 0, 0, 0, 'HEAD'),
    ('H5', -0.254, 0, 0, 0, 'HEAD'),
    ('H6', -0.239, 0, 0, 0, 'HEAD'),
    ('H7', -0.229, 0, 0, 0, 'HEAD'),
    ('N0', -0.212, 0.021, 0.019, 0.026, NECKP),   # S1 re-lock 4: 1.7 cm behind H7 (was 1.2: 152 deg crease under the head)
    ('P0', -0.203, 0.023, 0.026, 0.030, NECKP),
    ('P1', -0.190, 0.024, 0.028, 0.033, NECKP),
    ('P2', -0.176, 0.024, 0.028, 0.033, NECKP),
    ('P3', -0.162, 0.022, 0.025, 0.030, NECKP),
    ('P4', -0.146, 0.020, 0.021, 0.027, NECKP),
    ('P5', -0.129, 0.019, 0.020, 0.026, NECKP),
    ('P6', -0.112, 0.020, 0.020, 0.026, NECKP),
    ('P7', -0.096, 0.022, 0.022, 0.028, BODYP),
    ('T0', -0.083, 0.027, 0.028, 0.031, BODYP),
    ('T1', -0.070, 0.032, 0.034, 0.035, BODYP),
    ('T2', -0.055, 0.034, 0.036, 0.037, BODYP),
    ('T3', -0.040, 0.034, 0.036, 0.037, BODYP),
    ('T4', -0.026, 0.034, 0.035, 0.037, BODYP),
    ('T5', -0.012, 0.034, 0.035, 0.038, BODYP),
    ('T6', 0.003, 0.035, 0.035, 0.040, BODYP),
    ('T7', 0.018, 0.037, 0.036, 0.043, BODYP),
    ('A0', 0.040, 0.042, 0.041, 0.051, BODYP),
    ('A1', 0.065, 0.048, 0.047, 0.059, BODYP),
    ('A2', 0.090, 0.053, 0.053, 0.065, BODYP),
    ('A3', 0.115, 0.056, 0.057, 0.069, BODYP),
    ('A4', 0.140, 0.057, 0.058, 0.070, BODYP),
    ('A5', 0.165, 0.056, 0.056, 0.069, BODYP),
    ('A6', 0.190, 0.053, 0.052, 0.066, BODYP),
    ('A7', 0.215, 0.049, 0.047, 0.062, BODYP),
    ('A8', 0.240, 0.044, 0.042, 0.056, BODYP),
    ('A9', 0.265, 0.039, 0.036, 0.049, BODYP),
    ('A10', 0.290, 0.033, 0.030, 0.041, BODYP),
    ('A11', 0.313, 0.027, 0.024, 0.033, BODYP),
    ('A12', 0.334, 0.021, 0.019, 0.025, BODYP),
    ('A13', 0.352, 0.015, 0.013, 0.017, BODYP),
    ('A14', 0.367, 0.009, 0.008, 0.010, BODYP),
    ('A15', 0.377, 0.004, 0.004, 0.0045, BODYP),
]
IDX = {s[0]: i for i, s in enumerate(SECS)}
NV = 10


def sec_pts(st):
    nm, y0, T, B, W, prof = st
    if prof == 'HEAD':
        return head_pts(nm, y0)
    z0, phi = zc(y0)
    a = math.radians(phi)
    uy, uz = -math.sin(a), math.cos(a)
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append(Vector((fx * W, y0 + h * uy, z0 + h * uz)))
    return out


def P(nm):
    return sec_pts(SECS[IDX[nm]])


# ------------------------------------------------------------------------------------------------ limbs
K_OCT = 0.75        # octagon corner factor


def block(rear, faces):
    """The 2x2 root block on the loft: 3 stations (rear, +1, +2) x 3 ring vertices. Returns the vertex grid
    pos[s][t] (s station, t ring step), its centre, outward normal, half extents and the ring-up direction."""
    i = IDX[rear]
    j0 = faces[0]
    G = [[sec_pts(SECS[i + s])[j0 + t] for t in range(3)] for s in range(3)]
    c = sum((G[s][t] for s in range(3) for t in range(3)), Vector()) / 9
    n = Vector()
    for s in range(2):
        for t in range(2):
            a, b, d = G[s][t], G[s + 1][t], G[s][t + 1]
            n += (d - a).cross(b - a)
    n.normalize()
    if n.dot(Vector((1, 0, 0))) < 0:
        n = -n
    bw = (G[0][1] - G[2][1]).length / 2
    bh = (G[1][0] - G[1][2]).length / 2
    up = (G[1][0] - G[1][2]).normalized()
    return G, c, n, bw, bh, up


def frames(pts, S0=None, roll=None, T0=None):
    """pts [(p, rw, rh)] -> [(p, U, S, T, rw, rh)]: S parallel-transported from S0 (no twist)."""
    out = []
    S = Vector(S0 or (0, 0, 1))
    P_ = [Vector(q[0]) for q in pts]
    for i, q in enumerate(pts):
        p, rw, rh = q[:3]
        kc = q[3] if len(q) > 3 else K_OCT
        a_ = P_[i - 1] if i > 0 else P_[i]
        b_ = P_[i + 1] if i + 1 < len(P_) else P_[i] + (P_[i] - P_[i - 1])
        T = (b_ - a_).normalized()
        if i == 0 and T0 is not None:
            T = Vector(T0).normalized()
        S = (S - T * S.dot(T)).normalized()
        if roll and i in roll:
            tgt, w = roll[i]
            tg = (Vector(tgt) - T * Vector(tgt).dot(T)).normalized()
            S = (S.lerp(tg, w)).normalized()
            S = (S - T * S.dot(T)).normalized()
        U = S.cross(T).normalized()
        out.append((Vector(p), U, S, T, rw, rh, kc))
    return out


def path(ctrl):
    """ctrl: [(point, rw, rh, fillet_R, n_between)] control polyline. Straight runs get n_between in-between
    stations (sizes lerped); every interior control point turns on a fillet arc of radius R (3 rings: arc start,
    the joint ring with the control size, arc end). Returns [(p, rw, rh)]."""
    C = [(Vector(c[0]), c[1], c[2], c[3], c[4], c[5] if len(c) > 5 else 0.0) for c in ctrl]
    out = [(C[0][0], C[0][1], C[0][2])]
    prev = C[0][0]
    for i in range(1, len(C)):
        p, rw, rh, R, nb, sw = C[i]
        q0, w0, h0 = C[i - 1][0], C[i - 1][1], C[i - 1][2]
        seg = p - q0
        L = seg.length
        d_in = seg / L
        if i < len(C) - 1 and R > 0:
            d_out = (C[i + 1][0] - p).normalized()
            th = math.acos(max(-1.0, min(1.0, d_in.dot(d_out))))
            t = min(R * math.tan(th / 2), 0.45 * L, 0.45 * (C[i + 1][0] - p).length)
            A = p - d_in * t
            B = p + d_out * t
        else:
            A = B = p
            t = 0.0
        # in-betweens on the straight run prev -> A
        run = A - prev
        for k in range(1, nb + 1):
            f = k / (nb + 1)
            q = prev + run * f
            g = ((q - q0).length) / L
            bump = 1.0 + sw * math.sin(math.pi * g)
            out.append((q, (w0 + (rw - w0) * g) * bump, (h0 + (rh - h0) * g) * (1.0 + 0.4 * sw * math.sin(math.pi * g))))
        if t > 0:
            g = (A - q0).length / L
            out.append((A, w0 + (rw - w0) * g, h0 + (rh - h0) * g))
            mid = (A + B) * 0.25 + p * 0.5
            out.append((mid, rw, rh))
            n_ = C[i + 1]
            g2 = t / (n_[0] - p).length
            out.append((B, rw + (n_[1] - rw) * g2, rh + (n_[2] - rh) * g2))
            prev = B
        else:
            out.append((p, rw, rh))
            prev = p
    return out


# raptorial foreleg: root block under the prothorax front; coxa hangs down, a fillet turns the femur up-forward,
# another folds the tibia back down; rh along S (~ world X: the thin side), rw in the bend plane (the blade).
FORE_REAR, FORE_FACES = 'P0', (5, 6)
# s1 r3: the sheet's femur is a big blade (0.05 deep) rising steeply to z 0.33 at y -0.37; r00-r02 had 2.6 cm
# fillets that cut 5 cm off each femur end (the femur rose only to 0.31 and read as a thin tube). Now the joints
# are narrow in the bend plane (trochanter rw 0.012, R 1.5 cm) and the blade swells x2.3 between them.
FORE = [((0.052, -0.196, 0.350), 0.019, 0.0115, 0.0, 1),     # S1 re-lock 4: rh (x) near the root ~ the block
        ((0.064, -0.202, 0.215), 0.012, 0.0125, 0.015, 2, 0.3),   # coxa (swells x1.3), the trochanter turn
        ((0.080, -0.370, 0.338), 0.010, 0.009, 0.012, 3, 1.3),   # femur blade (x2.3 mid), the tibia folds down
        ((0.046, -0.340, 0.145), 0.005, 0.005, 0.0, 4)]          # tibia hook tip (s2 r1: 4 in-betweens)
# s1 r4: front view: the sheet's folded forelegs fill x 0.035-0.095 (femur outer, tibia folded inward of it, the
# spines between); r03 had femur and tibia in one plane at x ~0.07 (two thin bars by the neck)


FILLET = [False]


def root_pts(c, n, bw, bh, first, walking=False):
    """S1 re-lock 2 (s4 r02 probe: knife folds 152-170 deg and 3.9 mm seam strips on every coxa root): three
    root rings turn the tube from the block normal to the coxa direction and grow it from the block size (the
    block is ~1 cm in the ring direction, the coxa 1.5-1.7 cm) instead of one hug ring 8 mm out followed by a
    4-7 cm wall that doubled in one step and twisted."""
    p1, rw1, rh1 = Vector(first[0]), first[1], first[2]
    D = (p1 - c).normalized()
    out = []
    if FILLET[0]:
        # S2 r07 root fillet (vertex moves only): the three root rings 10 / 17 / 22 mm out (were 7 / 13 / 17): the
        # walls between them were 1.5-4 mm seam strips and a 98 deg fold at the walking-leg roots (s4 r06 probe)
        # s2 r08: straighter (the turn from the normal to the coxa moves past r2): r07's bend crowded the inner wall
        # of r1-r2 into 2.2-3 mm strips between the left and right coxae
        if walking:
            # s2 r10: the walking-leg root rings ride a quadratic Bezier from the block (tangent = the block normal)
            # to the first coxa ring (control point half-way out along the normal): the ~40 deg turn spreads evenly
            # over r0-r1-r2-coxa (r07/r08 turned it inside one wall: 1.5-5 mm seam strips on the inner side).
            # s2 r13: the ring-direction size (rh) stays at the block's through the root rings (r11: growing rh on
            # the inner side of the turn crowded the lower walls into 2.8-4.7 mm strips; r12's straight rings
            # folded 179 deg and self-intersected)
            # s2 r14: control point 0.7 out (was 0.5): the rings stay near the normal and the turn back (the block
            # normal leans 20 deg forward with the tilted rings) lands on the long last wall; r13's U+ (rear) walls
            # between r0-r1-r2 were 2.3-4.6 mm seam strips
            A, K = c + n * 0.008, c + n * (walking * (p1 - c).length)     # s2 r15: per leg (mid 0.8, hind 0.6)
            for t, g, k, kc in ((0.0, 0.0, 0.92, 0.95), (0.2, 0.3, 1.0, 0.88), (0.4, 0.6, 1.0, 0.81)):
                q = A * (1 - t) ** 2 + K * (2 * t * (1 - t)) + p1 * t * t
                rw = (bw * k) + (rw1 - bw * k) * g
                rh = bh * (0.92 if t == 0 else 0.95)
                out.append((q, rw, rh, kc))
            return out
        for off_n, off_d, g, k, kc in ((0.010, 0.0, 0.0, 0.92, 0.95), (0.016, 0.009, 0.3, 1.0, 0.88),
                                       (0.019, 0.021, 0.65, 1.0, 0.81)):
            rw = (bw * k) + (rw1 - bw * k) * g
            rh = (bh * k) + (rh1 - bh * k) * g
            out.append((c + n * off_n + D * off_d, rw, rh, kc))
        return out
    # S1 re-lock 3 (s4 r03 probe: knife + seam strip at the block corners, where the hug ring's corners were pulled
    # in to the octagon's 0.75 while the block corners stay square): the root rings keep square-ish corners
    # (0.95 / 0.88 / 0.81) and reach the octagon (0.75) on the first coxa ring
    for off_n, off_d, g, k, kc in ((0.007, 0.0, 0.0, 0.92, 0.95), (0.013, 0.006, 0.3, 1.0, 0.88),
                                   (0.017, 0.016, 0.65, 1.0, 0.81)):
        rw = (bw * k) + (rw1 - bw * k) * g
        rh = (bh * k) + (rh1 - bh * k) * g
        out.append((c + n * off_n + D * off_d, rw, rh, kc))
    return out


def fore_secs():
    G, c, n, bw, bh, up = block(FORE_REAR, FORE_FACES)
    pts = root_pts(c, n, bw, bh, FORE[0]) + path(FORE)
    return frames(pts, S0=up, T0=n if FILLET[0] else None)


# walking legs: (root block rear station, ring faces, control points after the root rings)
# S1 re-lock 5: blocks on ring faces 6-7 (normal ~55 deg down, along the coxa) instead of 5-6 (~30 deg down): the
# steep coxa undercut the block's lower edge (139-148 deg concave fold, s4 r03-r05 probe)
LEGS = {
    'mid': ('T1', (6, 7), [((0.050, -0.064, 0.205), 0.016, 0.0125, 0.0, 1),   # S1 re-lock 4: rh 0.0125 (was 0.015: the coxa's lower wall bulged under the block = 139-148 deg undercut)
                           ((0.060, -0.066, 0.168), 0.014, 0.0125, 0.018, 0),     # coxa end
                           ((0.135, -0.150, 0.228), 0.010, 0.010, 0.020, 2),     # knee (high)
                           ((0.200, -0.232, 0.026), 0.0065, 0.0065, 0.014, 5),   # ankle (s2 r1: 5 in-betweens, slivers)
                           ((0.215, -0.262, 0.006), 0.0055, 0.004, 0.0, 0)]),    # tarsus tip on the ground
    'hind': ('T5', (6, 7), [((0.052, 0.006, 0.188), 0.016, 0.0125, 0.0, 1),
                            ((0.066, 0.030, 0.150), 0.014, 0.0125, 0.018, 0),
                            ((0.150, 0.130, 0.238), 0.010, 0.010, 0.020, 2),
                            ((0.195, 0.248, 0.026), 0.0065, 0.0065, 0.014, 5),
                            ((0.205, 0.280, 0.006), 0.0055, 0.004, 0.0, 0)]),
}


ROOT_K = {'mid': 0.8, 'hind': 0.6}     # Bezier control point of the root rings (x the root -> coxa distance)


def leg_secs(name):
    rear, faces, ctrl = LEGS[name]
    G, c, n, bw, bh, up = block(rear, faces)
    pts = root_pts(c, n, bw, bh, ctrl[0], walking=ROOT_K[name]) + path(ctrl)
    if FILLET[0]:
        # s2 r16: the whole coxa rides one cubic Bezier from the first root ring (leaving along the block normal)
        # to the coxa-end arc (arriving along the coxa): the 34-40 deg turn back from the forward-leaning block
        # normal spreads over the four walls r0-r1-r2-coxa-arc instead of crowding one wall (r10-r15: the
        # octagon's corner faces on the short inner walls were 1-4.6 mm seam strips, or the turn folded 133-142 deg)
        P0, E = pts[0][0], pts[4][0]
        d_in = (Vector(ctrl[1][0]) - Vector(ctrl[0][0])).normalized()
        L = (E - P0).length
        B1, B2 = P0 + n * (0.4 * L), E - d_in * (0.35 * L)
        for i, t in ((1, 0.22), (2, 0.45), (3, 0.72)):
            q = P0 * (1 - t) ** 3 + B1 * (3 * t * (1 - t) ** 2) + B2 * (3 * t * t * (1 - t)) + E * t ** 3
            pts[i] = (q,) + tuple(pts[i][1:])
    # s2 r11: the first root ring lies parallel to its block (T = the block normal): r10's ring was skewed by the
    # Bezier tangent, 4 mm off the block on one side and 10 mm on the other (the 4.4 mm seam strips)
    return frames(pts, S0=up, T0=n if FILLET[0] else None)


def oct_pos(sec, a, b, tip=0.0):
    p, U, S, T, rw, rh = sec[:6]
    if a == 0 and b == 0:
        return p + T * tip
    k = (sec[6] if len(sec) > 6 else K_OCT) if (a and b) else 1.0
    return p + S * (a * rh * k) + U * (b * rw * k)


def grow(bm, faces, roles, secs, place):
    """Extrude the region section by section; every new vertex keeps the role of the vertex it came from."""
    for i, sec in enumerate(secs):
        snap = [(v.co.copy(), rl) for v, rl in roles.items()]
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(snap, key=lambda o: (o[0] - v.co).length)[1]
        last = i == len(secs) - 1
        for v, rl in new.items():
            v.co = place(sec, rl, last)
        faces, roles = r['faces'], new
    return faces, roles


spans_of = []


def root_roles(rings, rear, faces, U0):
    i, j0 = IDX[rear], faces[0]
    Vv = [[rings[i + s][j0 + t] for t in range(3)] for s in range(3)]
    sg = 1 if (Vv[0][1].co - Vv[2][1].co).dot(U0) > 0 else -1
    roles = {Vv[s][t]: (1 - t, sg * (1 - s)) for s in range(3) for t in range(3)}
    region = [spans_of[i + s][j0 + t] for s in range(2) for t in range(2)]
    return region, roles


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(st)) for st in SECS]
    spans_of.clear()
    spans_of.extend(bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1))
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    for nm in LEGS:
        secs = leg_secs(nm)
        region, roles = root_roles(rings, LEGS[nm][0], LEGS[nm][1], secs[0][1])
        grow(bm, region, roles, secs,
             lambda sec, rl, last: oct_pos(sec, rl[0], rl[1], 0.004 if last else 0.0))
    secs = fore_secs()
    region, roles = root_roles(rings, FORE_REAR, FORE_FACES, secs[0][1])
    grow(bm, region, roles, secs, lambda sec, rl, last: oct_pos(sec, rl[0], rl[1], 0.004 if last else 0.0))
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


# ------------------------------------------------------------------------------------------------ stage 2
EYE_ST, EYE_V = ('H3', 'H4'), (3, 4)       # the eye socket face: bulb vertices 3-4 (outer, facing out-forward)


def eye_face_centre():
    a, b = P(EYE_ST[0]), P(EYE_ST[1])
    return (a[EYE_V[0]] + a[EYE_V[1]] + b[EYE_V[0]] + b[EYE_V[1]]) / 4


def eye_face_normal():
    a, b = P(EYE_ST[0]), P(EYE_ST[1])
    n = (a[EYE_V[1]] - a[EYE_V[0]]).cross(b[EYE_V[0]] - a[EYE_V[0]])
    n.normalize()
    return n if n.x > 0 else -n


def stage2(k, body):
    ec0, en0 = eye_face_centre(), eye_face_normal()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.015 and abs(c.y - ec0.y) < 0.015
                                        and abs(c.z - ec0.z) < 0.015)
    bm = edit(body)
    old = [fore_secs()] + [leg_secs(nm) for nm in LEGS]
    FILLET[0] = True
    new = [fore_secs()] + [leg_secs(nm) for nm in LEGS]
    OCTR = [(a, b) for a in (1, 0, -1) for b in (1, 0, -1) if a or b]
    for so, sn in zip(old, new):
        for i in range(4):                       # the three root rings + the first coxa ring (s2 r16)
            vs = [(vert_near(bm, oct_pos(so[i], a, b)), oct_pos(sn[i], a, b)) for a, b in OCTR]
            for v, p in vs:
                v.co = p
    f = face_near(bm, ec0, n=tuple(en0))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye bulb face that faces out-forward'):
        inner = inset(bm, [f], 0.3, 0.0)
    move(list(inner[0].verts), -fn * 0.003)
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


# ------------------------------------------------------------------------------------------------ stage 3
# s3 r3: two steps lighter (r02 read dark bottle-green next to the sheet's bright leaf green; belly hidden)
PAL = {'green': '#9fcf55', 'pale': '#e4e9b2', 'lime': '#d2e676', 'wing': '#86bd47', 'dark': '#1d2116',
       'spine': '#3b2c1e'}


def _seg_d(q, a, b):
    d = b - a
    t = max(0.0, min(1.0, (q - a).dot(d) / max(d.length_squared, 1e-12)))
    return (a + d * t - q).length, t


def _near_poly(q, pts):
    best = (1e9, 0.0)
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d, t = _seg_d(q, a, b)
        if d < best[0]:
            best = (d, (L[i] + t * (L[i + 1] - L[i])) / L[-1])
    return best


_POLY = {}


def polys():
    if not _POLY:
        _POLY['fore'] = [s_[0] for s_ in fore_secs()]
        for nm in LEGS:
            _POLY[nm] = [s_[0] for s_ in leg_secs(nm)]
    return _POLY


def bulb_dist(q):
    """Distance from q to the eye-bulb surface slices (head stations H2-H7)."""
    best = 1e9
    for nm in ('H2', 'H3', 'H4', 'H5', 'H6', 'H7'):
        zt, zb, cx, cz, e = HEADS[nm]
        y = SECS[IDX[nm]][1]
        if e > 0.012:
            best = min(best, math.hypot(math.hypot(q.x - cx, q.z - cz) - e, q.y - y))
    return best


_BY = [(st[1], st[3]) for st in SECS if st[5] != 'HEAD']
BULB_C, BULB_R = Vector((0.047, -0.256, 0.443)), 0.028


def _B_at(y):
    """The ring's lower half-depth at y (lerped between stations)."""
    for (y0, b0), (y1, b1) in zip(_BY, _BY[1:]):
        if y0 <= y <= y1:
            return b0 + (b1 - b0) * (y - y0) / max(y1 - y0, 1e-9)
    return _BY[0][1] if y < _BY[0][0] else _BY[-1][1]


def body_rule(c, n, i):
    # review f1: colour by position in the form, not by the facet normal (r09's normal thresholds flipped on
    # alternate facets: a pale/green and lime/green checkerboard on the neck, the belly edge and the eye bulbs).
    # Lime: faces on the eye-bulb sphere; pale: the lower 35% of each body ring, the head's mouth underside, the
    # inner face of the femur blade; legs green.
    q = Vector((abs(c.x), c.y, c.z))
    nx = n.x if c.x >= 0 else -n.x
    nq = Vector((nx, n.y, n.z))
    if c.y < -0.222:
        d = q - BULB_C
        if d.length < BULB_R + 0.009 and nq.dot(d.normalized()) > 0.35:
            return 'lime'
    pl = polys()
    d, f = _near_poly(q, pl['fore'])
    if d < 0.022 or (d < 0.035 and f > 0.12):
        return 'pale' if (nx < -0.45 and 0.35 < f < 0.8) else 'green'
    for nm in LEGS:
        d, f = _near_poly(q, pl[nm])
        if d < 0.019:
            return 'green'
    if c.y < -0.222:
        return 'pale' if (c.z < 0.400 and c.y > -0.315) else 'green'
    z0, phi = zc(c.y)
    a = math.radians(phi)
    h = (c.z - z0) * math.cos(a) - 0.0 * math.sin(a)
    return 'pale' if h < -0.35 * _B_at(c.y) else 'green'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A small low-poly lens: back cone, ring, front fan (8 sides)."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 4 for k_ in range(8)]]
    R, I = ring_(r, 0.0), ring_(r * 0.6, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.3)
    for j in range(8):
        a, b = j, (j + 1) % 8
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def ring_normals(pts):
    """In-plane outward normals of a half ring (top seam -> bottom seam)."""
    out = []
    ax = (pts[0] - pts[-1]).normalized()
    pn = ax.cross(Vector((1, 0, 0))).normalized()        # the ring plane's normal
    c = (pts[0] + pts[-1]) / 2
    for j in range(len(pts)):
        a = pts[max(j - 1, 0)]
        b = pts[min(j + 1, len(pts) - 1)]
        t = (b - a).normalized()
        nn = t.cross(pn).normalized()
        if nn.dot(pts[j] - c) < 0:
            nn = -nn
        out.append(nn)
    return out


WING_ROWS = ['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
             'A9', 'A10', 'A11', 'A12', 'A13', 'A14']
WING_IN, WING_OUT = 0.002, 0.009          # the slab: 2 mm sunk into the abdomen, 9 mm proud (11 mm thick)
WING_TIP = (0.405, 0.106)


def wing_rows():
    """[(outer pts, inner pts)] per row: the wing covers the ring from the top seam to u_max (vertex 4 = the
    widest point), narrower at the front rows (the wing base on the pterothorax)."""
    rows = []
    for nm in WING_ROWS:
        pts = P(nm)
        nrm = ring_normals(pts)
        y = SECS[IDX[nm]][1]
        umax = 2.6 + 1.4 * min(1.0, max(0.0, (y + 0.083) / 0.06))
        o, i_ = [], []
        for j in range(5):
            u = umax * j / 4
            j0 = min(int(u), 8)
            f = u - j0
            p = pts[j0].lerp(pts[j0 + 1], f)
            n = nrm[j0].lerp(nrm[j0 + 1], f).normalized()
            if j == 0:
                p = Vector((0.0, p.y, p.z))
                n = Vector((0.0, n.y, n.z)).normalized()
            dip = 0.0025 if j == 0 else 0.0          # the midline groove between the two wings
            o.append(p + n * (WING_OUT - dip))
            i_.append(p - n * WING_IN)
        rows.append((o, i_))
    # s3 r2: the tip beyond the abdomen: five short rows (< 8 mm apart) narrowing to a blunt 3 mm point and thinning
    # to 6.5 mm, so no needle triangles (r01: two long converging rows made 48 slivers)
    lo, li = rows[-1]
    ty, tz = WING_TIP
    y0 = lo[0].y
    for yy in (0.377, 0.386, 0.394, 0.400, 0.405):
        f = (yy - y0) / (ty - y0)
        w = 1.0 - 0.85 * f
        th = 1.0 - 0.4 * f
        zc_o = lo[0].z + (tz + 0.0035 - lo[0].z) * f
        o2, i2 = [], []
        for po, pi in zip(lo, li):
            mo = Vector((po.x * w, yy, zc_o + (po.z - lo[0].z) * w))
            mi = Vector((pi.x * w, yy, zc_o + (pi.z - lo[0].z) * w - (lo[0].z - li[0].z) * th))
            o2.append(mo); i2.append(mi)
        rows.append((o2, i2))
    return rows


def build_wing():
    bm = bmesh.new()
    rows = wing_rows()
    O = [[bm.verts.new(p) for p in o] for o, _ in rows]
    I = [[bm.verts.new(p) for p in i_] for _, i_ in rows]
    for r in range(len(rows) - 1):
        for j in range(4):
            bm.faces.new([O[r][j], O[r][j + 1], O[r + 1][j + 1], O[r + 1][j]])
            bm.faces.new([I[r][j], I[r + 1][j], I[r + 1][j + 1], I[r][j + 1]])
        bm.faces.new([O[r][4], I[r][4], I[r + 1][4], O[r + 1][4]])       # the outer edge wall
    for j in range(4):                                                    # front wall and tip wall
        bm.faces.new([O[0][j], I[0][j], I[0][j + 1], O[0][j + 1]])
        bm.faces.new([O[-1][j], O[-1][j + 1], I[-1][j + 1], I[-1][j]])
    recalc_normals(bm)
    return object_from_bm('wing', bm)


def spike(bm, base, d, side_hint, r=0.0032, ln=0.014, tip_r=None):
    """A 3-sided spine; with tip_r a blunt frustum (detail pass 10-23: chunky, >= the gate floor to its tip)."""
    d = d.normalized()
    u = d.cross(side_hint)
    u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0))
    w = d.cross(u).normalized()
    b0 = base - d * 0.003
    vs = [bm.verts.new(b0 + (u * math.cos(t) + w * math.sin(t)) * r) for t in (0, 2.0944, 4.1888)]
    bot = bm.verts.new(b0 - d * 0.002)
    if tip_r:
        ts = [bm.verts.new(base + d * ln + (u * math.cos(t) + w * math.sin(t)) * tip_r) for t in (0, 2.0944, 4.1888)]
        for a in range(3):
            bm.faces.new([vs[a], vs[(a + 1) % 3], ts[(a + 1) % 3], ts[a]])
            bm.faces.new([vs[(a + 1) % 3], vs[a], bot])
        bm.faces.new(ts)
        return
    tip = bm.verts.new(base + d * ln)
    for a in range(3):
        bm.faces.new([vs[a], vs[(a + 1) % 3], tip])
        bm.faces.new([vs[(a + 1) % 3], vs[a], bot])


FEMUR_SPIKES = (0.50, 0.62, 0.74)   # detail pass 10-23: 3 fat spines (were 4 thin)
FEMUR_SPIKES_OLD = (0.46, 0.555, 0.65, 0.745)  # review f2: off the trochanter (the 0.38 spike reached the coxa)      # fractions along the foreleg path (on the blade's grasping edge)
TIBIA_SPIKES = (0.82, 0.92)


def build_spines():
    bm = bmesh.new()
    secs = fore_secs()
    pts = [s_[0] for s_ in secs]
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)

    def at(fr):
        t = fr * L[-1]
        i = max(1, next((j for j, v in enumerate(L) if v >= t), len(L) - 1))
        g = (t - L[i - 1]) / max(L[i] - L[i - 1], 1e-9)
        a, b = secs[i - 1], secs[i]
        return a[0].lerp(b[0], g), a[1].lerp(b[1], g).normalized(), a[3].lerp(b[3], g).normalized(), a[4] + (b[4] - a[4]) * g
    for fr in FEMUR_SPIKES:
        p, U, T, rw = at(fr)
        spike(bm, p + U * rw * 0.8, U - T * 0.35, T, r=0.0105, ln=0.017, tip_r=0.0089)   # review f2: bolder (were 3.2 x 16 mm), seated at 0.8 rw (the blade edge is thin: at 0.9 the base crossed both corner faces)
    for fr in TIBIA_SPIKES:
        p, U, T, rw = at(fr)
        spike(bm, p + U * rw * 0.85, U + T * 0.3, T, r=0.0100, ln=0.015, tip_r=0.0088)
    return object_from_bm('spines', bm)


ANT = [(0.010, -0.300, 0.442), (0.026, -0.318, 0.466), (0.045, -0.338, 0.490), (0.064, -0.356, 0.508)]   # detail pass 10-23: short + chunky
ANT_OLD = [(0.010, -0.300, 0.442), (0.026, -0.318, 0.466), (0.045, -0.338, 0.490), (0.068, -0.360, 0.511),
       (0.094, -0.382, 0.526), (0.122, -0.402, 0.534)]
ANT_N = 5                               # s3 r2: resampled to 10 rings ~2 cm apart (r01: 3.5 cm segments = 64 slivers)


def _resample(pts, n):
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    out = []
    for k in range(n):
        t = L[-1] * k / (n - 1)
        i = max(1, next((j for j, v in enumerate(L) if v >= t - 1e-12), len(L) - 1))
        g = (t - L[i - 1]) / max(L[i] - L[i - 1], 1e-12)
        out.append(pts[i - 1].lerp(pts[i], g))
    return out


def build_antennae():
    bm = bmesh.new()
    pts = [Vector(p) for p in ANT]
    pts[0] = pts[0] - (pts[1] - pts[0]).normalized() * 0.006         # sunk into the head
    pts = _resample(pts, ANT_N)
    rings_ = []
    S = Vector((0, 0, 1))
    for i, p in enumerate(pts):
        T = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        S = (S - T * S.dot(T)).normalized()
        U = S.cross(T)
        r = 0.0098 - 0.0004 * i / (len(pts) - 1)         # detail pass: >= 13 mm across (tier-1 floor 12.8 mm)
        rings_.append([bm.verts.new(p + (S * math.cos(t) + U * math.sin(t)) * r) for t in (0.0, 1.5708, 3.1416, 4.7124)])
    for a, b in zip(rings_, rings_[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(list(reversed(rings_[0])))
    tip = bm.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.005)
    for j in range(4):
        bm.faces.new([rings_[-1][j], rings_[-1][(j + 1) % 4], tip])
    recalc_normals(bm)
    return object_from_bm('antenna', bm)


def stage3(k, body):
    paint(body, PAL, body_rule)
    bm_ = edit(body)
    tree = BVHTree.FromBMesh(bm_)
    bm_.free()
    bm = bmesh.new()
    ec, en = eye_face_centre(), eye_face_normal()
    c, n, _i, _d = tree.find_nearest(ec)
    if n.dot(en) < 0:
        n = -n
    lens(bm, c + n * 0.001, n, 0.0105, 0.006)
    eye = object_from_bm('eye', bm)
    paint(eye, {'dark': PAL['dark']}, lambda c_, n_, i: 'dark')
    wing = build_wing()
    paint(wing, {'wing': PAL['wing']}, lambda c_, n_, i: 'wing')
    sp = build_spines()
    paint(sp, {'spine': PAL['spine']}, lambda c_, n_, i: 'spine')
    an = build_antennae()
    paint(an, {'green': PAL['green']}, lambda c_, n_, i: 'green')
    return [eye, wing, sp, an]


# ------------------------------------------------------------------------------------------------ stage 4
def chain_joints(name):
    """Root (block centre) and the control joints of a walking leg."""
    rear, faces, ctrl = LEGS[name]
    G, c, n, bw, bh, up = block(rear, faces)
    return [c] + [Vector(p[0]) for p in ctrl[1:]]


def stage4(k, body, pieces):
    B = [('thorax', (0.0, 0.0, 0.262), (0.0, -0.085, 0.313), None),
         ('neck', (0.0, -0.085, 0.313), (0.0, -0.212, 0.421), 'thorax', True),
         ('head', (0.0, -0.212, 0.421), (0.0, -0.327, 0.420), 'neck', True),
         ('abdomen', (0.0, 0.0, 0.262), (0.0, 0.165, 0.185), 'thorax'),
         ('abdomen2', (0.0, 0.165, 0.185), (0.0, 0.38, 0.10), 'abdomen', True)]
    G, c, n, bw, bh, up = block(FORE_REAR, FORE_FACES)
    fj = [c] + [Vector(p[0]) for p in FORE[1:]]
    B += [('coxa1.L', tuple(fj[0]), tuple(fj[1]), 'neck'),
          ('femur1.L', tuple(fj[1]), tuple(fj[2]), 'coxa1.L', True),
          ('tibia1.L', tuple(fj[2]), tuple(fj[3]), 'femur1.L', True)]
    for idx, nm in ((2, 'mid'), (3, 'hind')):
        j = chain_joints(nm)
        B += [('coxa%d.L' % idx, tuple(j[0]), tuple(j[1]), 'thorax'),
              ('femur%d.L' % idx, tuple(j[1]), tuple(j[2]), 'coxa%d.L' % idx, True),
              ('tibia%d.L' % idx, tuple(j[2]), tuple(j[3]), 'femur%d.L' % idx, True),
              ('tarsus%d.L' % idx, tuple(j[3]), tuple(j[4]), 'tibia%d.L' % idx, True)]
    rig = armature(B)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            nm = eb.name
            if nm.startswith(('thorax', 'neck', 'head', 'abdomen')):
                eb.align_roll(Vector((1, 0, 0)))          # local Z = world X: rot Z pitches in the body plane
            elif nm.startswith('coxa'):
                eb.align_roll(Vector((0, -1, 0)))         # local Z forward: rot X swings the leg fore/aft
            else:
                eb.align_roll(Vector((0, 0, 1)))          # local Z up: rot X lifts / folds
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: the head turns and tilts (the mantis look-around), the abdomen breathes, the forelegs sway a little
    keys = {}
    for f in (1, 13, 25, 37, 49):
        ph = 2 * math.pi * (f - 1) / 48
        d = {'head': (round(7 * math.sin(ph), 2), 0, round(3 * math.sin(2 * ph), 2)),
             'neck': (0, 0, round(1.5 * math.sin(ph + 0.6), 2)),
             'abdomen': (0, 0, round(1.5 * math.sin(ph), 2)),
             'abdomen2': (0, 0, round(1.0 * math.sin(ph - 0.5), 2))}
        for sd in 'LR':
            d['coxa1.' + sd] = (round(3 * math.sin(ph + 1.0), 2), 0, 0)
            d['tibia1.' + sd] = (round(-3 * max(0.0, math.sin(ph)), 2), 0, 0)
        keys[f] = d
    clip(rig, 'idle', keys, loc={1: {'thorax': (0, 0, 0)}, 25: {'thorax': (0, 0, 0.003)}, 49: {'thorax': (0, 0, 0)}})
    # move: the four walking legs step in diagonal pairs (mid.L + hind.R, then mid.R + hind.L): the coxa swings
    # fore/aft, the femur lifts during the swing; the forelegs stay folded, the head steadies
    A, Lf = 9.0, 10.0

    def gait(f):
        d = {}
        for idx, off in ((2, 0.0), (3, math.pi)):
            for sd, o2 in (('L', 0.0), ('R', math.pi)):
                ph = 2 * math.pi * (f - 1) / 24 + off + o2
                d['coxa%d.%s' % (idx, sd)] = (round(A * math.sin(ph), 2), 0, 0)
                d['femur%d.%s' % (idx, sd)] = (round(Lf * max(0.0, math.cos(ph)), 2), 0, 0)
        ph = 2 * math.pi * (f - 1) / 24
        d['head'] = (round(-2 * math.sin(ph), 2), 0, 0)
        d['abdomen'] = (0, 0, round(1.0 * math.sin(2 * ph), 2))
        return d
    clip(rig, 'move', {f: gait(f) for f in (1, 4, 7, 10, 13, 16, 19, 22, 25)},
         loc={1: {'thorax': (0, 0, 0)}, 7: {'thorax': (0, 0, 0.004)}, 13: {'thorax': (0, 0, 0)},
              19: {'thorax': (0, 0, 0.004)}, 25: {'thorax': (0, 0, 0)}})
    # review f3: measured on the GLB (posed bone tails): coxa +X swings the leg FORWARD (s4 r02's flip to -X sent
    # the strike back toward the mid legs, tibia tip at z 0.017); femur -X reaches forward, tibia -X opens it
    # attack: the raptorial strike: cock back, shoot the forelegs forward with the tibiae open, snap shut, recover
    cock, strike, snap = {}, {}, {}
    for sd in 'LR':
        cock['coxa1.' + sd] = (-8, 0, 0); cock['femur1.' + sd] = (10, 0, 0)
        strike['coxa1.' + sd] = (22, 0, 0); strike['femur1.' + sd] = (-10, 0, 0); strike['tibia1.' + sd] = (-40, 0, 0)
        snap['coxa1.' + sd] = (18, 0, 0); snap['femur1.' + sd] = (-6, 0, 0); snap['tibia1.' + sd] = (4, 0, 0)
    cock['neck'] = (0, 0, -4); strike['neck'] = (0, 0, 6); snap['neck'] = (0, 0, 5)
    clip(rig, 'attack', {1: {}, 9: cock, 14: strike, 18: snap, 24: snap, 33: {}},
         loc={1: {'thorax': (0, 0, 0)}, 9: {'thorax': (0, 0.01, 0)}, 14: {'thorax': (0, -0.012, 0)},
              24: {'thorax': (0, -0.008, 0)}, 33: {'thorax': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
