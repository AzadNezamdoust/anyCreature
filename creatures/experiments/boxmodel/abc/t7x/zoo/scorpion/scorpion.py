import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# scorpion (t7x zoo, workflow v2): ONE spine loft of 10-vertex half rings runs from the carapace front through the
# seven mesosoma tergites (groove / crest station pairs: the segmented back) and on up the curled metasoma (five
# barrel segments with pinched joint rings) to the telson bulb and the sting tip; the tail rings tilt with the
# centre-line tangent. The eight walking legs and the two pedipalps grow as octagon tubes from 2x2 face blocks of
# the loft (legs on the lower flank, palps on the carapace side): each root is a broad region with a hug ring
# first. The pincer's two fingers grow as hexagon tubes from the two halves of the palm's end cap.
# Identity cue (NOTES): the tail curled up and forward over the back + two big forward pincers + 4 legs a side.
META = dict(creature='scorpion', model='opus', engine_glb='', stage1_tris=(1500, 6500), total_tris=(2500, 7000),
            closeups=[('pincer', (0.15, -0.26, 0.1), 0.15, 'hero'),
                      ('face and eyes', (0.0, -0.15, 0.18), 0.09, 'hero'),
                      ('leg roots', (0.12, 0.02, 0.13), 0.16, 'hero_low'),
                      ('tail and sting', (0.0, 0.31, 0.36), 0.18, 'az090')])

# ------------------------------------------------------------------------------------------------ profiles
# body half ring (top seam -> bottom seam): domed tergite top, the plate rim at vertex 4, a flat lower flank
# (vertices 5-7, the leg-root band), the sternite belly
BODYP = [(0, 1), (0.4, 0.97), (0.72, 0.85), (0.93, 0.6), (1.0, 0.25), (0.97, -0.12), (0.88, -0.45), (0.68, -0.75),
         (0.36, -0.95), (0, -1)]


def _se(n=10, e=2.5):
    out = []
    for k in range(n):
        th = math.pi * k / (n - 1)
        s, c = math.sin(th), math.cos(th)
        out.append((0.0 if k in (0, n - 1) else round(abs(s) ** (2 / e), 4), round(math.copysign(abs(c) ** (2 / e), c), 4)))
    return out


TAILP = _se(10, 2.5)          # tail barrels: a squarish round section
LEG_FACES, CLAW_FACES = (4, 5), (3, 4)    # S1 re-lock (s4 r01 probe): legs from faces 4-5 (normal ~level), were 5-6 (normal 33 deg down)    # ring faces of the root blocks (face j: vertex j -> j+1)

# carapace + mesosoma stations: (name, y, zc, T, B, W, groove)
_B0 = [('H0', -0.163, 0.166, 0.026, 0.030, 0.038, 0),
      ('H1', -0.156, 0.169, 0.040, 0.043, 0.057, 0),
      ('H2', -0.138, 0.171, 0.047, 0.049, 0.067, 0),
      ('H3', -0.115, 0.172, 0.049, 0.051, 0.073, 0),
      ('H4', -0.092, 0.172, 0.050, 0.052, 0.078, 0),
      ('C0', -0.069, 0.171, 0.051, 0.053, 0.082, 0),
      ('C1', -0.046, 0.170, 0.051, 0.053, 0.085, 0),
      ('C2', -0.023, 0.170, 0.051, 0.053, 0.087, 0),
      ('M0', 0.000, 0.170, 0.050, 0.052, 0.088, 1),
      ('M1', 0.023, 0.170, 0.051, 0.052, 0.091, 0),
      ('M2', 0.046, 0.170, 0.050, 0.051, 0.093, 1),
      ('M3', 0.069, 0.170, 0.051, 0.051, 0.095, 0),
      ('M4', 0.092, 0.171, 0.050, 0.050, 0.096, 1),
      ('M5', 0.115, 0.171, 0.050, 0.050, 0.096, 0),
      ('M6', 0.138, 0.172, 0.049, 0.049, 0.095, 1),
      ('M7', 0.161, 0.172, 0.049, 0.048, 0.093, 0),
      ('M8', 0.184, 0.173, 0.048, 0.046, 0.089, 1),
      ('M9', 0.207, 0.174, 0.047, 0.044, 0.083, 0),
      ('M10', 0.230, 0.175, 0.045, 0.042, 0.076, 1),
      ('M11', 0.252, 0.176, 0.044, 0.040, 0.068, 0)]

# s1 r5: the sheet's carapace is a broad blunt trapezoid (~0.12 wide at the front edge, face broad between the
# pincers); r04 narrowed to a point (H0 0.038). Front stations widened, the claw root block moves out with them.
_WF = {'H0': 0.050, 'H1': 0.068, 'H2': 0.076, 'H3': 0.080, 'H4': 0.083, 'C0': 0.085, 'C1': 0.087}
_TF = {'H0': (0.030, 0.034), 'H1': (0.042, 0.045)}
_B = [(n, y, z, _TF.get(n, (T, B))[0], _TF.get(n, (T, B))[1], _WF.get(n, W), g) for n, y, z, T, B, W, g in _B0]

# the rear centre line: from M11 over the rump, up the curled tail to the sting tip (y, z), read off the side view
CURVE = [(0.230, 0.175), (0.252, 0.176), (0.275, 0.179), (0.300, 0.187), (0.330, 0.203), (0.358, 0.228),
         (0.378, 0.262), (0.390, 0.300), (0.392, 0.345), (0.382, 0.390), (0.360, 0.430), (0.325, 0.460),
         (0.285, 0.470), (0.247, 0.455), (0.217, 0.430), (0.198, 0.400), (0.188, 0.365), (0.185, 0.335), (0.187, 0.310)]


def _curve():
    P = [Vector((0.0, y, z)) for y, z in CURVE]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    pts = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(24):
            t = k / 24
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    pts.append(P[-2])
    S = [0.0]
    for a, b in zip(pts, pts[1:]):
        S.append(S[-1] + (b - a).length)
    return pts, S


CP, CS = _curve()
S_M11 = min(range(len(CP)), key=lambda i: (CP[i] - Vector((0, 0.252, 0.176))).length)
S_M11 = CS[S_M11]


def cat(s):
    """Point and tangent angle (deg, from +Y toward +Z) on the rear centre line at arc length s."""
    s = max(0.0, min(CS[-1], s))
    i = max(1, next((j for j, v in enumerate(CS) if v >= s), len(CS) - 1))
    t = (s - CS[i - 1]) / max(CS[i] - CS[i - 1], 1e-9)
    p = CP[i - 1].lerp(CP[i], t)
    d = CP[min(i + 1, len(CP) - 1)] - CP[max(i - 2, 0)]
    return p, math.degrees(math.atan2(d.z, d.y))


S_END = CS[-1]
S0 = S_M11 + 0.064                      # the first tail joint
TELSON = 0.205                          # telson bulb + sting length along the curve
LS = (S_END - TELSON - S0) / 5          # metasoma segment length
S_T = S0 + 5 * LS                       # telson neck
TAIL_W, TAIL_T = 0.040, 0.045
SEG_K = (1.0, 1.03, 1.02, 0.98, 0.93)


def _rear():
    """Rear stations from the centre line: the tapering 7th tergite, the five tail barrels, the telson and sting."""
    out = []
    for nm, ds, T, B, W, g in (('M12', 0.021, 0.041, 0.038, 0.058, 1), ('M13', 0.042, 0.040, 0.037, 0.050, 0)):
        p, ph = cat(S_M11 + ds)
        out.append((nm, p.y, p.z, ph, T, B, W, BODYP, g))
    for k in range(5):
        for j, (f, sc) in enumerate(((0.0, 0.92 if k == 0 else 0.76), (0.32, 1.0), (0.72, 0.97))):
            p, ph = cat(S0 + (k + f) * LS)
            q = SEG_K[k] * sc
            out.append(('T%d%s' % (k, 'jab'[j]), p.y, p.z, ph, TAIL_T * q, TAIL_T * q, TAIL_W * q, TAILP, 0))
    for nm, ds, r in (('Tn', 0.0, 0.026), ('Tb0', 0.03, 0.037), ('Tb1', 0.06, 0.044), ('Tb2', 0.09, 0.043),
                      ('Tb3', 0.116, 0.034), ('Tb4', 0.137, 0.021), ('St0', 0.157, 0.012), ('St1', 0.176, 0.008),
                      ('St2', 0.192, 0.005), ('St3', TELSON, 0.0025)):
        p, ph = cat(S_T + ds)
        out.append((nm, p.y, p.z, ph, r * 1.08, r * 1.08, r, TAILP, 0))
    return out


SECS = [(n, y, z, 0.0, T, B, W, BODYP, g) for n, y, z, T, B, W, g in _B] + _rear()
IDX = {s[0]: i for i, s in enumerate(SECS)}


def sec_pts(st):
    nm, y0, z0, phi, T, B, W, prof, g = st
    a = math.radians(phi)
    uy, uz = -math.sin(a), math.cos(a)
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        w = fx * W
        if g and fh > 0.2:          # tergite groove: the upper ring dips and narrows a little
            h *= 1 - 0.09 * min(1.0, (fh - 0.2) / 0.5)
            w *= 0.97
        out.append(Vector((w, y0 + h * uy, z0 + h * uz)))
    return out


def P(nm):
    return sec_pts(SECS[IDX[nm]])


# ------------------------------------------------------------------------------------------------ limbs
K_OCT = 0.75        # octagon corner factor


def block(rear, faces):
    """The 2x2 root block on the loft: 3 stations (rear, +1, +2) x 3 ring vertices. Returns the vertex grid
    pos[s][t] (s station, t ring step), its centre, outward normal and half extents."""
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
    return G, c, n, bw, bh


def frames(pts, S0=None, roll=None):
    """pts [(p, rw, rh)] -> [(p, U, S, T, rw, rh)]: S parallel-transported from world up (no twist), optionally
    rolled toward a target per section: roll = {index: (target_S, weight)}."""
    out = []
    S = Vector(S0 or (0, 0, 1))
    P_ = [Vector(p) for p, _w, _h in pts]
    for i, (p, rw, rh) in enumerate(pts):
        a_ = P_[i - 1] if i > 0 else P_[i]
        b_ = P_[i + 1] if i + 1 < len(P_) else P_[i] + (P_[i] - P_[i - 1])
        T = (b_ - a_).normalized()
        S = (S - T * S.dot(T)).normalized()
        if roll and i in roll:
            tgt, w = roll[i]
            tg = (Vector(tgt) - T * Vector(tgt).dot(T)).normalized()
            S = (S.lerp(tg, w)).normalized()
            S = (S - T * S.dot(T)).normalized()
        U = S.cross(T).normalized()
        out.append((Vector(p), U, S, T, rw, rh))
    return out


# legs: (rear station of the root block, heading deg from +X toward +Y (+ = back), reach scale)
LEGS = [('C0', -8.0, 0.95), ('M0', 30.0, 1.05), ('M3', 50.0, 1.12), ('M6', 64.0, 1.2)]
# leg sections: (horizontal distance out, z, rw, rh): coxa out-down, femur up to the knee, patella, tibia down,
# tarsus, claw tip (the pinched joint rings: 4, 7, 10)
# s1 r2: chunkier (femur 0.022, sheet ~0.037 diameter) and sprawled like the sheet's front view (knee 0.2 high at
# ~0.1 out, tips 0.21-0.29 out): the r01 legs read as thin straight stilts
LEG_T = [(0.016, 0.140, 0.020, 0.018), (0.034, 0.146, 0.021, 0.019), (0.054, 0.165, 0.022, 0.020),
         (0.075, 0.185, 0.022, 0.020), (0.093, 0.198, 0.017, 0.016), (0.108, 0.202, 0.022, 0.020),
         (0.125, 0.192, 0.021, 0.019), (0.140, 0.172, 0.016, 0.015), (0.155, 0.145, 0.019, 0.018),
         (0.172, 0.108, 0.019, 0.017), (0.186, 0.074, 0.0145, 0.0135), (0.197, 0.050, 0.015, 0.014),
         (0.207, 0.027, 0.012, 0.011), (0.215, 0.010, 0.007, 0.007)]
# s1 r3: the segments x1.3 from the femur on (coxa stays at the root block's size): the sheet's legs are fat
# bulbous segments (tibia ~0.045 across in the side view), r02 still read as thin spikes
LEG_T = [(d, z, rw * (1.0 if i < 2 else 1.3), rh * (1.0 if i < 2 else 1.3)) for i, (d, z, rw, rh) in enumerate(LEG_T)]
# S1 re-lock (after s4 r01): the root block moved up to ring faces 4-5 (centre z ~0.165, normal near level), so the
# coxa leaves along the normal instead of 33 deg across it (knife folds 92-97 deg on the upper root side, legs 1-2);
# section heights re-based on the new root, knee 0.203
_LZ = (0.163, 0.170, 0.182, 0.194, 0.203, 0.206, 0.196, 0.176, 0.148, 0.110, 0.075, 0.050, 0.027, 0.010)
LEG_T = [(d, _LZ[i], rw, rh) for i, (d, z, rw, rh) in enumerate(LEG_T)]
KNEE, TIB, TAR = 5, 8, 11       # section indices (after the hug ring) where the bones start


def leg_secs(spec, fillet=True):
    rear, hd, sc = spec
    G, c, n, bw, bh = block(rear, LEG_FACES)
    a = math.radians(hd)
    h = Vector((math.cos(a), math.sin(a), 0.0))
    # review f2: hug ring 13 mm out at 0.88 (was 10 mm / 0.9): the hug wall's triangles were 5 mm wide seam strips
    pts = [(c + n * (0.013 if fillet else 0.006), bw * (0.88 if fillet else 0.86), bh * (0.88 if fillet else 0.86))]
    # s1 r1: the coxa leaves along the flank normal (plan) for D0, then turns to the heading (a rear leg swept
    # straight back from the root cut through the flank behind it)
    h0 = Vector((n.x, n.y, 0.0)).normalized()
    D0 = 0.03
    t0, t1 = math.atan2(h0.y, h0.x), math.atan2(h.y, h.x)
    for i, (d, z, rw, rh) in enumerate(LEG_T):
        if fillet and i < 3:
            d = (0.030, 0.046, 0.062)[i]   # review f2: first ring 3.0 cm (hug ring moved out)
        if fillet:
            # s2 r4: the plan path turns from the root normal to the heading smoothly over 0.8-5.2 cm (the kink at
            # 3 cm crowded the inner side of legs 3/4 into creased strips 1.5-1.9 r)
            q, s_, ds = Vector((c.x, c.y, 0.0)), 0.0, 0.0005
            while s_ < d - 1e-9:
                u = min(1.0, max(0.0, (s_ - 0.018) / 0.040))   # review f2: the turn starts past the first coxa ring   # centred on the old 3 cm kink: the plan stays put
                th = t0 + (t1 - t0) * u * u * (3 - 2 * u)
                q = q + Vector((math.cos(th), math.sin(th), 0.0)) * (ds * (1.0 if s_ < D0 else sc))
                s_ += ds
        else:
            q = Vector((c.x, c.y, 0.0)) + h0 * min(d, D0) + h * (max(0.0, d - D0) * sc)
        pts.append((Vector((q.x, q.y, z)), rw, rh))
    return frames(pts)


# pedipalp: hug ring, femur out, elbow, patella forward-down, wrist, the round palm (cap -> two fingers)
CLAW = [((0.095, -0.116, 0.182), 0.020, 0.019), ((0.118, -0.113, 0.175), 0.020, 0.019),
        ((0.140, -0.107, 0.166), 0.019, 0.018), ((0.158, -0.103, 0.155), 0.015, 0.014),
        ((0.172, -0.110, 0.143), 0.019, 0.018), ((0.178, -0.125, 0.130), 0.020, 0.019),
        ((0.176, -0.142, 0.118), 0.016, 0.015), ((0.170, -0.158, 0.108), 0.030, 0.034),
        ((0.163, -0.180, 0.100), 0.046, 0.055), ((0.156, -0.207, 0.096), 0.053, 0.063),
        ((0.150, -0.234, 0.094), 0.049, 0.058), ((0.145, -0.257, 0.093), 0.036, 0.044)]
# s1 r4: the sheet's chela is a big round bulb (0.15 tall, 0.13 wide) on a fat patella with thick dark fingers; r03's
# palm was a pointed spindle (long wrist taper) on a thin arm. Arm x1.15-1.3, a short palm back shoulder, a round
# palm 0.13 x 0.15, one more palm station.
CLAW = [((0.101, -0.116, 0.182), 0.021, 0.020), ((0.123, -0.113, 0.175), 0.022, 0.021),
        ((0.143, -0.107, 0.166), 0.022, 0.021), ((0.158, -0.103, 0.155), 0.018, 0.017),
        ((0.172, -0.110, 0.143), 0.025, 0.024), ((0.178, -0.125, 0.130), 0.026, 0.025),
        ((0.176, -0.141, 0.119), 0.019, 0.018), ((0.171, -0.151, 0.112), 0.038, 0.045),
        ((0.166, -0.168, 0.104), 0.056, 0.066), ((0.159, -0.195, 0.097), 0.064, 0.075),
        ((0.153, -0.225, 0.094), 0.062, 0.072), ((0.148, -0.250, 0.093), 0.050, 0.060),
        ((0.144, -0.268, 0.093), 0.038, 0.047)]
ELBOW, WRIST = 4, 7             # claw section indices (hug ring = 0)
PINCER_S = (-0.55, 0.0, 0.85)   # the pincer opens in this plane: movable finger upper-inner, fixed lower-outer


def claw_secs(fillet=True):
    G, c, n, bw, bh = block('H2', CLAW_FACES)
    pts = [(c + n * (0.010 if fillet else 0.006), bw * (0.9 if fillet else 0.86), bh * (0.9 if fillet else 0.86))]
    pts += [(Vector(p), w, h) for p, w, h in CLAW]
    return frames(pts, roll={WRIST: (PINCER_S, 0.4), WRIST + 1: (PINCER_S, 0.7), WRIST + 2: (PINCER_S, 1.0),
                             WRIST + 3: (PINCER_S, 1.0), WRIST + 4: (PINCER_S, 1.0), WRIST + 5: (PINCER_S, 1.0)})


# fingers in the palm-end frame: (t along T, s along S, u along U, rw, rh)
MOV = [(0.016, 0.026, 0.0, 0.030, 0.019), (0.048, 0.034, -0.004, 0.026, 0.017), (0.082, 0.034, -0.010, 0.020, 0.014),
       (0.112, 0.028, -0.016, 0.014, 0.010), (0.137, 0.019, -0.020, 0.009, 0.006), (0.154, 0.012, -0.022, 0.003, 0.003)]
FIX = [(0.016, -0.026, 0.0, 0.032, 0.020), (0.050, -0.036, -0.003, 0.028, 0.018), (0.086, -0.037, -0.009, 0.022, 0.015),
       (0.118, -0.031, -0.015, 0.015, 0.011), (0.145, -0.021, -0.020, 0.009, 0.007), (0.164, -0.012, -0.023, 0.003, 0.003)]


def finger_secs(spec):
    p, U, S, T, rw, rh = claw_secs()[-1]
    pts = [(p + T * t + S * s + U * u, w, h) for t, s, u, w, h in spec]
    fr = frames(pts, S0=S)
    out = []
    for (q, U2, S2, T2, w, h) in fr:
        # keep U/S of the palm frame turned with the finger (S2 was transported from the palm S)
        out.append((q, U2, S2, T2, w, h))
    return out


def oct_pos(sec, a, b, tip=0.0):
    p, U, S, T, rw, rh = sec
    if a == 0 and b == 0:
        return p + T * tip
    k = K_OCT if (a and b) else 1.0
    return p + S * (a * rh * k) + U * (b * rw * k)


def hex_pos(sec, a2, b):
    p, U, S, T, rw, rh = sec
    return p + U * (b * 0.87 * rw) + S * (a2 * (0.5 if b else 1.0) * rh)


def grow(bm, faces, roles, secs, place):
    """Extrude the region section by section; every new vertex keeps the role of the vertex it came from
    (matched by position before the extrusion: the region's interior vertex is deleted with its faces)."""
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


def root_roles(rings, rear, faces, U0):
    i, j0 = IDX[rear], faces[0]
    V = [[rings[i + s][j0 + t] for t in range(3)] for s in range(3)]
    sg = 1 if (V[0][1].co - V[2][1].co).dot(U0) > 0 else -1
    roles = {V[s][t]: (1 - t, sg * (1 - s)) for s in range(3) for t in range(3)}
    region = [spans_of[i + s][j0 + t] for s in range(2) for t in range(2)]
    return region, roles


spans_of = []


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(st)) for st in SECS]
    spans_of.clear()
    spans_of.extend(bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1))
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    # legs
    for spec in LEGS:
        secs = leg_secs(spec, fillet=False)
        region, roles = root_roles(rings, spec[0], LEG_FACES, secs[0][1])
        grow(bm, region, roles, secs, lambda sec, rl, last: oct_pos(sec, rl[0], rl[1], 0.007 if last else 0.0))
    # pedipalp + pincer
    secs = claw_secs(fillet=False)
    region, roles = root_roles(rings, 'H2', CLAW_FACES, secs[0][1])
    cap_faces, roles = grow(bm, region, roles, secs, lambda sec, rl, last: oct_pos(sec, rl[0], rl[1], 0.004 if last else 0.0))
    top = [f for f in cap_faces if all(roles[v][0] >= 0 for v in f.verts)]
    bot = [f for f in cap_faces if all(roles[v][0] <= 0 for v in f.verts)]
    rt = {v: rl for v, rl in roles.items() if rl[0] >= 0}
    rb = {v: rl for v, rl in roles.items() if rl[0] <= 0}
    grow(bm, top, rt, finger_secs(MOV), lambda sec, rl, last: hex_pos(sec, 1 if rl[0] == 1 else -1, rl[1]))
    grow(bm, bot, rb, finger_secs(FIX), lambda sec, rl, last: hex_pos(sec, 1 if rl[0] == 0 else -1, rl[1]))
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


# ------------------------------------------------------------------------------------------------ stage 2
def eye_face_centre():
    """Carapace front-top corner face (ring vertices 2-3, H1 -> H2): the eye socket."""
    a, b = P('H1'), P('H2')
    return (a[2] + a[3] + b[2] + b[3]) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.02 and abs(c.y - ec0.y) < 0.02
                                        and abs(c.z - ec0.z) < 0.02)
    bm = edit(body)
    f = face_near(bm, ec0, n=(0.6, -0.4, 0.7))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the carapace front-top corner face'):
        inner = inset(bm, [f], 0.35, 0.0)
    move(list(inner[0].verts), -fn * 0.004)
    # s2 r3: root fillets (vertex moves only). s4 r02 probe + crops: the hug ring 6 mm out at 0.86 of the root block
    # made a ring of 3-5 mm wall faces (seam strips 1.6-2.0 r, a dark crease line in the B/C crops) and the first
    # coxa section 1 cm further on folded 91-101 deg. Hug ring 10 mm out at 0.9, the first three leg sections spread
    # to 2.6 / 4.3 / 6.0 cm (were 1.6 / 3.4 / 5.4): near-square wall faces, the turn split over three rings.
    OCTR = [(a, b) for a in (1, 0, -1) for b in (1, 0, -1) if a or b]
    moves = []
    for spec in LEGS:
        old_s, new_s = leg_secs(spec, fillet=False), leg_secs(spec, fillet=True)
        moves += [(old_s[i], new_s[i], i == len(old_s) - 1) for i in range(len(old_s))]
    cs_old, cs_new = claw_secs(fillet=False), claw_secs(fillet=True)
    moves.append((cs_old[0], cs_new[0], False))
    for so, sn, tip in moves:
        rl = OCTR + ([(0, 0)] if tip else [])
        vs = [(vert_near(bm, oct_pos(so, a, b, 0.007)), oct_pos(sn, a, b, 0.007)) for a, b in rl]
        for v, p in vs:
            v.co = p
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


# ------------------------------------------------------------------------------------------------ stage 3
PAL = {'tan': '#d2a467', 'pale': '#e3c28c', 'brown': '#9a6c42', 'dark': '#4a3124', 'eye': '#141011'}   # s3 r2: a step lighter (r1 read muddy brown)


def _seg_d(q, a, b):
    d = b - a
    t = max(0.0, min(1.0, (q - a).dot(d) / max(d.length_squared, 1e-12)))
    return (a + d * t - q).length, t


def _near_poly(q, pts):
    """(distance, fraction along) to a polyline of section centres."""
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
        _POLY['legs'] = [[s[0] for s in leg_secs(spec)] for spec in LEGS]
        _POLY['claw'] = [s[0] for s in claw_secs()]
        _POLY['mov'] = [s[0] for s in finger_secs(MOV)]
        _POLY['fix'] = [s[0] for s in finger_secs(FIX)]
    return _POLY


def tail_s(q):
    """Arc length of the nearest rear centre-line point and the distance to it."""
    i = min(range(len(CP)), key=lambda j: (CP[j].y - q.y) ** 2 + (CP[j].z - q.z) ** 2)
    return CS[i], math.hypot(CP[i].y - q.y, CP[i].z - q.z)


def body_rule(c, n, i):
    q = Vector((abs(c.x), c.y, c.z))
    pl = polys()
    for nm in ('mov', 'fix'):
        d, f = _near_poly(q, pl[nm])
        if d < 0.03:
            return 'dark'
    d, f = _near_poly(q, pl['claw'])
    if d < 0.07 and f > 0.55:
        return 'tan'
    for lp in pl['legs']:
        d, f = _near_poly(q, lp)
        if d < 0.03:
            return 'dark' if f > 0.9 else 'pale'
    if d < 0.03:
        return 'pale'
    s, dd = tail_s(q)
    if c.z > 0.3 and s >= S_T - 0.004 and dd < 0.07:   # s3 r2: was c.y > 0.27, which missed the bulb (y 0.19-0.3)
        return 'dark'                                   # telson and sting
    if -0.005 < c.y < 0.29 and n.z > 0.45 and c.z > 0.19:
        return 'brown'                                  # tergite plates
    return 'tan'


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


def stage3(k, body):
    paint(body, PAL, body_rule)
    bm_ = edit(body)
    tree = BVHTree.FromBMesh(bm_)
    bm_.free()
    bm = bmesh.new()
    ec = eye_face_centre()
    c, n, _i, _d = tree.find_nearest(ec)
    if n.dot(Vector((0.6, -0.4, 0.7))) < 0:
        n = -n
    lens(bm, c + n * 0.001, n, 0.009, 0.006)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, lambda c_, n_, i: 'eye')
    return [eye]


# ------------------------------------------------------------------------------------------------ stage 4
def stage4(k, body, pieces):
    B = [('thorax', (0.0, 0.0, 0.17), (0.0, -0.12, 0.17), None),
         ('head', (0.0, -0.12, 0.17), (0.0, -0.165, 0.17), 'thorax', True),
         ('abdomen', (0.0, 0.0, 0.17), (0.0, 0.14, 0.172), 'thorax'),
         ('abdomen2', (0.0, 0.14, 0.172), (0.0, 0.27, 0.178), 'abdomen', True)]
    # s4 r2: a short tail0 root bone (5 cm) aimed up the curl: on a full-segment tail0 the sting under the curl
    # projected behind the root and the probe's root radius came out 180 mm (region = half the body)
    jp = [cat(S0)[0]]
    d0 = (cat(S0 + 2 * LS)[0] - jp[0]).normalized()
    jp.append(jp[0] + d0 * 0.05)
    jp += [cat(S0 + kk * LS)[0] for kk in (2, 3, 4, 5)] + [cat(S_T + 0.12)[0], cat(S_END)[0]]
    prev = 'abdomen2'
    for kk in range(7):
        a, b = jp[kk], jp[kk + 1]
        nm = 'tail%d' % kk
        B.append((nm, tuple(a), tuple(b), prev, kk > 0))
        prev = nm
    for n_, spec in enumerate(LEGS, 1):
        s = leg_secs(spec)
        G, c, nrm, bw, bh = block(spec[0], LEG_FACES)
        pts = [c, s[KNEE][0], s[TIB][0], s[-1][0]]
        par = 'thorax' if n_ <= 2 else 'abdomen'
        for t_, (p, q) in zip('abc', zip(pts, pts[1:])):
            nm = 'leg%d%s.L' % (n_, t_)
            B.append((nm, tuple(p), tuple(q), par if t_ == 'a' else 'leg%d%s.L' % (n_, 'ab'['bc'.index(t_)]), t_ != 'a'))
    cs = claw_secs()
    G, c, nrm, bw, bh = block('H2', CLAW_FACES)
    # s4 r2: a short trochanter root bone (4 cm out along the root normal), then the femur to the elbow: the palm
    # forward of a root->elbow bone projected behind its root and inflated the probe radius to 138 mm
    tro = c + nrm * 0.04
    B.append(('arm.L', tuple(c), tuple(tro), 'thorax'))
    B.append(('femur.L', tuple(tro), tuple(cs[ELBOW][0]), 'arm.L', True))
    B.append(('fore.L', tuple(cs[ELBOW][0]), tuple(cs[WRIST][0]), 'femur.L', True))
    B.append(('hand.L', tuple(cs[WRIST][0]), tuple(cs[-1][0]), 'fore.L', True))
    mv = finger_secs(MOV)
    B.append(('finger.L', tuple(cs[-1][0] + cs[-1][2] * 0.012), tuple(mv[-1][0]), 'hand.L'))
    rig = armature(B)
    Sp = cs[-1][2]
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            nm = eb.name
            if nm.startswith(('thorax', 'head', 'abdomen', 'tail')):
                eb.align_roll(Vector((1, 0, 0)))          # local Z = world X: rot Z bends in the body plane
            elif nm.startswith(('hand', 'finger')):
                sx = 1 if nm.endswith('.L') else -1
                eb.align_roll(Vector((Sp.x * sx, Sp.y, Sp.z)))   # local Z = the pincer axis: rot X opens/closes
            else:
                eb.align_roll(Vector((0, 0, 1)))          # local Z up: rot X lifts, rot Z swings
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    # the palm and fixed finger rigid on hand, the movable finger rigid on finger (heat bleeds across the crotch)
    pl = polys()
    for sd in 'LR':
        for nm in ('hand.' + sd, 'finger.' + sd):
            if body.vertex_groups.get(nm) is None:
                body.vertex_groups.new(name=nm)
    for v in body.data.vertices:
        p = body.matrix_world @ v.co
        q = Vector((abs(p.x), p.y, p.z))
        sd = 'L' if p.x > 0 else 'R'
        dm, fm = _near_poly(q, pl['mov'])
        df, ff = _near_poly(q, pl['fix'])
        dc, fc = _near_poly(q, pl['claw'])
        tgt = None
        if dm < 0.024 and dm < df and fm > 0.08:
            tgt = 'finger.' + sd
        elif df < 0.026 or (dc < 0.07 and fc > 0.72):
            tgt = 'hand.' + sd
        if tgt:
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            body.vertex_groups[tgt].add([v.index], 1.0, 'REPLACE')
    for p in pieces:
        bind(p, rig, body=body)

    T_ = ['tail%d' % i for i in range(7)]
    # idle: breathing, a slow tail sway, the pincers opening and closing, a leg shuffle
    keys = {}
    for f in (1, 13, 25, 37, 49):
        ph = 2 * math.pi * (f - 1) / 48
        d = {t: (0, 0, round(2.0 * math.sin(ph + i * 0.5), 2)) for i, t in enumerate(T_[:5])}
        d['tail0'] = (0, round(2.5 * math.sin(ph), 2), d['tail0'][2])
        for sd in 'LR':
            d['finger.' + sd] = (round(-10 * max(0.0, math.sin(ph)), 2), 0, 0)
            d['arm.' + sd] = (round(3 * math.sin(ph + 1.0), 2), 0, 0)
        for n_ in range(1, 5):
            for sd, o in (('L', 0.0), ('R', 1.1)):
                d['leg%da.%s' % (n_, sd)] = (round(2.5 * math.sin(ph + n_ * 1.3 + o), 2), 0, 0)
        keys[f] = d
    clip(rig, 'idle', keys, loc={1: {'thorax': (0, 0, 0)}, 25: {'thorax': (0, 0, 0.004)}, 49: {'thorax': (0, 0, 0)}})
    # move: s4 r4: a metachronal wave (each leg a quarter cycle behind the one in front, the right side half a cycle
    # off) with a 5 deg swing: the r01-r03 alternating tetrapod swung neighbours 2 x 9 deg against each other and
    # the femurs of legs 2-4 crossed (posed clip 6.5-10%)
    A, Lf = 5.0, 10.0
    LAG = {1: 0.0, 2: math.pi / 2, 3: math.pi, 4: math.pi}

    def gait(f):
        d = {}
        for n_ in range(1, 5):
            for sd, off in (('L', 0.0), ('R', math.pi)):
                ph = 2 * math.pi * (f - 1) / 24 - LAG[n_] + off   # s4 r5: legs 3 and 4 step together (lag 0)
                a_ = A if n_ <= 2 else 2.5      # review f3: the rear pair swings 2.5 deg (5 deg grazed leg3 on leg4)
                fwd = -a_ if sd == 'L' else a_
                d['leg%da.%s' % (n_, sd)] = (round(Lf * max(0.0, math.cos(ph)), 2), 0, round(fwd * math.sin(ph), 2))
                d['leg%db.%s' % (n_, sd)] = (round(-4.0 * max(0.0, math.cos(ph)), 2), 0, 0)
        ph = 2 * math.pi * (f - 1) / 24
        d['tail0'] = (0, round(3 * math.sin(ph), 2), 0)
        d['tail2'] = (0, round(-2 * math.sin(ph), 2), 0)
        return d
    clip(rig, 'move', {f: gait(f) for f in (1, 4, 7, 10, 13, 16, 19, 22, 25)},
         loc={1: {'thorax': (0, 0, 0)}, 7: {'thorax': (0, 0, 0.004)}, 13: {'thorax': (0, 0, 0)},
              19: {'thorax': (0, 0, 0.004)}, 25: {'thorax': (0, 0, 0)}})
    # attack: the pincers rise and open, the tail coils back, then the sting strikes forward and the pincers snap
    coil = {t: (0, 0, v) for t, v in zip(T_, (-6, -6, -5, -4, -3, 0, 0))}
    strike = {t: (0, 0, v) for t, v in zip(T_, (8, 9, 8, 6, 5, 4, 0))}
    for sd in 'LR':
        coil['arm.' + sd] = (-12, 0, 0); coil['finger.' + sd] = (-22, 0, 0)
        strike['arm.' + sd] = (-6, 0, 0); strike['finger.' + sd] = (6, 0, 0)
    clip(rig, 'attack', {1: {}, 10: coil, 16: strike, 20: strike, 26: {'tail0': (0, 0, 2)}, 32: {}},
         loc={1: {'thorax': (0, 0, 0)}, 10: {'thorax': (0, 0.01, 0.006)}, 16: {'thorax': (0, -0.012, 0)},
              32: {'thorax': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
