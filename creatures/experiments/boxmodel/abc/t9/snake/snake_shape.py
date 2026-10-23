"""t9 snake: the shape tables (pure numpy; shared by snake.py in Blender and tools/design.py outside it).

The kit's base is a mirrored half, so stages 1-3 are built STRAIGHT in plan: a sagittal (YZ) spine that already
carries the sheet's vertical form (raised head, S-neck rising out of the body, the arched mid-body loop, the tail
tip curling up). Stage 4 lays the body (behind the neck base) into the sheet's plan-view S-curve with bend():
straight y -> arc length along the plan centreline, x -> along the curve's left normal, z kept.

Sheet: refs/gpt/v3/snake/sheet_1.png (kit/refs.py --height 0.5). The plan view is drawn ~10 % smaller than the
side (705 vs 771 px), so the plan centreline is scaled x1.10 about the snout to the side's length (side wins).
"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_SCALE = 1.10
PLAN_XSCALE = 1.2                         # lateral stretch of the plan S (the front and rear views are wider than the top)
SNOUT_Y = -0.542
NV = 12                                   # vertices per half ring (top seam -> bottom seam), 2x density

# ---------------------------------------------------------------- the sagittal spine (head + neck), snout -> neck base
# (y, z) of the spine centre, read off reference/side.png: level wedge head, a near-vertical neck at y -0.33,
# a 90 deg turn (radius ~0.11) into the body on the ground
NECK_KEYS = [(-0.566, 0.421), (-0.558, 0.424), (-0.546, 0.427), (-0.505, 0.431), (-0.455, 0.437), (-0.405, 0.441), (-0.365, 0.438),
             (-0.336, 0.420), (-0.316, 0.385), (-0.304, 0.335), (-0.300, 0.280), (-0.297, 0.225),
             (-0.288, 0.180), (-0.270, 0.142), (-0.244, 0.114), (-0.212, 0.099), (-0.180, 0.094)]
Y_BASE = -0.180                           # neck base: the plan bend starts here
XB, THETA, THETA_HEAD = 0.020, math.radians(-32.0), math.radians(6.0)    # plan start tangent (toward -x) / head yaw


def _resample(P, ds):
    P = np.asarray(P, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, d[-1], max(2, int(round(d[-1] / ds)) + 1))
    return np.c_[[np.interp(s, d, P[:, j]) for j in range(P.shape[1])]].T, s


def _smooth(P, it):
    P = np.asarray(P, float).copy()
    for _ in range(it):
        Q = P.copy(); Q[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4; P = Q
    return P


# ---------------------------------------------------------------- the plan centreline (body, neck base -> tail tip)
class Plan:
    def __init__(self, extra=0):
        d = json.load(open(os.path.join(HERE, 'reference', 'plan_centre.json')))
        xy = np.array(d['xy'], float)                       # (x, y), head first
        xy[:, 1] = SNOUT_Y + PLAN_SCALE * (xy[:, 1] - SNOUT_Y)
        xy[:, 0] *= PLAN_SCALE * PLAN_XSCALE
        keep = xy[:, 1] > Y_BASE + 0.06                        # behind the neck base (the head lies over it)
        P = xy[keep]
        st, sn = math.sin(THETA), math.cos(THETA)
        lead = [[XB + st * q, Y_BASE + sn * q] for q in (0.0, 0.02, 0.04)]   # start tangent = the head's yaw
        P = np.r_[lead, P]
        P, _ = _resample(P, 0.01)
        for _ in range(40):
            P = _smooth(P, 1)
            P[:5] = [[XB + st * q, Y_BASE + sn * q] for q in np.arange(5) * 0.01]
        if extra:                                              # pose curve only (S1 keeps PLAN): rounder tight bends
            for a, b in POSE_ZONES[:extra]:
                d0 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
                idx = np.nonzero((d0 > a) & (d0 < b))[0]
                for _ in range(POSE_ITERS):
                    Q = P.copy(); Q[idx] = (P[idx - 1] + 2 * P[idx] + P[idx + 1]) / 4; P = Q
            d0 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            P = P[0] + (P - P[0]) * (PLAN.L / d0[-1])         # same length as the plan: the loft maps 1:1
        self.P, self.s = _resample(P, 0.004)
        self.L = self.s[-1]
        T = np.gradient(self.P, axis=0)
        self.T = T / np.linalg.norm(T, axis=1)[:, None]

    def at(self, h):
        if h <= 0:
            t0 = np.array((math.sin(THETA), math.cos(THETA)))
            return np.array((XB, Y_BASE)) + t0 * h, t0
        if h >= self.L:
            return self.P[-1] + self.T[-1] * (h - self.L), self.T[-1]
        i = min(int(h / self.L * (len(self.s) - 1)), len(self.s) - 2)
        t = (h - self.s[i]) / (self.s[i + 1] - self.s[i])
        p = self.P[i] * (1 - t) + self.P[i + 1] * t
        g = self.T[i] * (1 - t) + self.T[i + 1] * t
        return p, g / np.linalg.norm(g)


PLAN = Plan()
POSE_SMOOTH = int(os.environ.get('SNAKE_POSE_SMOOTH', '0'))     # fix-loop variants: number of bend zones rounded
POSE_ZONES = [(0.04, 0.50), (0.62, 0.92)]                    # the first turn, the bottom arc (plan arc, m)
POSE_ITERS = int(os.environ.get('SNAKE_POSE_ITERS', '200'))
POSE = Plan(POSE_SMOOTH) if POSE_SMOOTH else PLAN
Y_TAIL = Y_BASE + PLAN.L
INNER_MIN = float(os.environ.get('SNAKE_INNER_MIN', '0'))      # fix-loop variants: min inner-bend squeeze (0 = off)
_ang = np.unwrap(np.arctan2(PLAN.T[:, 1], PLAN.T[:, 0]))
_KAP = np.convolve(np.pad(np.gradient(_ang, PLAN.s), 10, mode='edge'), np.ones(21) / 21, mode='valid')


def bend(co):
    """straight snake point (x, y, z) -> posed point. Head + neck rings (by the ring the point lies on) turn
    rigidly about the neck base, the yaw blending ring by ring from THETA_HEAD (skull) to THETA (neck base);
    the body runs along the plan S-curve."""
    x, y, z = co
    i = station_of(y, z)
    s = _SS[i]
    if s < S_NECK - 1e-6:
        u = min(1.0, max(0.0, (s - S_SKULL) / (S_NECK - S_SKULL)))
        u = u * u * (3 - 2 * u)
        a = THETA_HEAD + (THETA - THETA_HEAD) * u
        dy, c, sn = y - Y_BASE, math.cos(a), math.sin(a)
        return (XB + x * c + dy * sn, Y_BASE - x * sn + dy * c, z)
    h = y - Y_BASE
    p, t = POSE.at(h * POSE.L / PLAN.L)                        # the pose curve, re-scaled to the plan's length
    nx, ny = t[1], -t[0]                                       # left normal: the straight snake's +x
    if INNER_MIN > 0:                                          # inner side of a tight bend: soft-clamp the offset
        kap = float(np.interp(h, PLAN.s, _KAP))                # so the arc there squeezes to >= INNER_MIN, no pinch
        if kap * x < 0 and abs(kap) > 1e-3:
            m = (1.0 - INNER_MIN) / abs(kap)
            x = math.copysign(m * math.tanh(abs(x) / m), x)
    return (p[0] + x * nx, p[1] + x * ny, z)


def station_of(y, z):
    """the loft station whose ring plane the straight point lies on (nearest plane among nearby stations)."""
    d = (y - _SY) * _TY + (z - _SZ) * _TZ
    r2 = (y - _SY) ** 2 + (z - _SZ) ** 2
    return int(np.argmin(np.abs(d) + 1e3 * (r2 > 0.16 ** 2)))


# ---------------------------------------------------------------- body tables along h = y - Y_BASE (0 .. PLAN.L)
# full width (plan view x1.1), section height, belly lift (the arched loop), read off the sheet; linear between keys
BODY_KEYS = [  # h, full width, height, belly lift (plan L ~1.13 m)
    (0.00, 0.180, 0.172, 0.000),
    (0.10, 0.190, 0.180, 0.000),
    (0.18, 0.208, 0.200, 0.030),
    (0.26, 0.222, 0.224, 0.082),
    (0.34, 0.228, 0.232, 0.100),
    (0.42, 0.230, 0.230, 0.090),
    (0.50, 0.226, 0.212, 0.045),
    (0.58, 0.224, 0.212, 0.015),
    (0.66, 0.214, 0.200, 0.000),
    (0.74, 0.190, 0.168, 0.000),
    (0.82, 0.158, 0.142, 0.000),
    (0.90, 0.118, 0.108, 0.000),
    (0.96, 0.088, 0.082, 0.004),
    (1.02, 0.064, 0.060, 0.035),
    (1.07, 0.046, 0.044, 0.080),
    (1.10, 0.034, 0.034, 0.110),
    (1.14, 0.020, 0.020, 0.132)]
# head / neck tables along the sagittal keys: full width, dorsal half height (up / back), ventral half height
NECK_SEC = [
    (0.030, 0.011, 0.012), (0.066, 0.022, 0.024), (0.104, 0.032, 0.033), (0.150, 0.042, 0.043), (0.184, 0.052, 0.053),
    (0.204, 0.059, 0.061), (0.202, 0.062, 0.065),
    (0.168, 0.084, 0.072), (0.160, 0.090, 0.088), (0.160, 0.092, 0.100), (0.165, 0.102, 0.110), (0.170, 0.096, 0.118),
    (0.175, 0.088, 0.130), (0.178, 0.084, 0.124), (0.180, 0.084, 0.112), (0.180, 0.085, 0.099), (0.180, 0.086, 0.086)]
N_HEAD = 7                                 # NECK_KEYS[0:5] are head stations (wedge profile)


_HG = np.arange(-0.2, 1.4, 0.005)
_HB = np.array(BODY_KEYS)
_HB[:, 0] *= PLAN.L / 1.14                     # keys were read off a 1.14 m plan: stretch to the plan length
_TAB = np.c_[[np.interp(_HG, _HB[:, 0], _HB[:, j]) for j in (1, 2, 3)]].T
for _ in range(2):                                         # 8 cm box filter twice: no kinks in the loop's arch
    _k = np.ones(17) / 17
    _TAB = np.c_[[np.convolve(np.pad(_TAB[:, j], 8, mode='edge'), _k, mode='valid') for j in range(3)]].T


def body_at(h):
    W, T, lift = (float(np.interp(h, _HG, _TAB[:, j])) for j in range(3))
    return W, T, lift


def tail_z_top(h):
    W, T, lift = body_at(h)
    return lift + T


# ---------------------------------------------------------------- ring profiles (fx across, fh up; top seam -> bottom seam)
def prof_body(n=NV):
    """python body: a round back, slightly flat flanks, a broad flat belly (belly border = vertices 8-9)."""
    ang = [0, 16, 32, 48, 64, 80, 96, 112, 128, 146, 164, 180][:n]
    out = []
    for a in ang:
        t = math.radians(a)
        c, s = math.cos(t), math.sin(t)
        e = 2.4 if c >= 0 else 4.0
        fx = abs(s) ** (2 / e)
        fh = math.copysign(abs(c) ** (2 / e), c)
        if c < 0:
            fx *= 1.0 - 0.18 * abs(c)
        out.append((fx if a not in (0, 180) else 0.0, fh))
    return out


def prof_head(n=NV):
    """python head: a flat crown (0-2), the brow edge (3), eye face (3-4), cheek plane (4-6), lip line (7),
    jaw side (7-9), a flat jaw underside (9-11)."""
    return [(0.0, 1.0), (0.36, 1.0), (0.66, 0.96), (0.86, 0.80), (0.98, 0.50), (1.0, 0.16), (0.97, -0.18),
            (0.90, -0.46), (0.78, -0.74), (0.58, -0.94), (0.30, -1.0), (0.0, -1.0)][:n]


# ---------------------------------------------------------------- stations: (name, centre (y,z), tangent (ty,tz), W/2, Tup, Tdn, profile, blend)
def _neck_path():
    P = np.array(NECK_KEYS, float)
    S = np.array(NECK_SEC, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    return P, S, d


def stations(ds_body=0.030):
    """All loft stations snout -> tail tip. Each: dict(y, z, ty, tz, W, Tu, Td, kind, s)."""
    out = []
    P, S, d = _neck_path()
    # head + neck: station spacing ~ one face width (finer in the head and the turn)
    sp = []
    s = 0.0
    while True:
        sp.append(s)
        W = np.interp(s, d, S[:, 0])
        s += max(0.016, min(0.030, 0.17 * W)) if s > d[N_HEAD - 1] else max(0.012, min(0.026, 0.16 * W))
        if s > d[-1] - 0.020:                    # the body's first ring (h = 0) closes the neck: no near-duplicate
            break
    for s in sp:
        y, z = np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])
        e = 0.035                                   # ring tilt from a +-3.5 cm chord: rings turn gradually (no folds)
        y0, z0 = np.interp(max(0, s - e), d, P[:, 0]), np.interp(max(0, s - e), d, P[:, 1])
        y1, z1 = np.interp(min(d[-1], s + e), d, P[:, 0]), np.interp(min(d[-1], s + e), d, P[:, 1])
        t = np.array((y1 - y0, z1 - z0)); t /= np.linalg.norm(t)
        W, Tu, Td = (np.interp(s, d, S[:, j]) for j in range(3))
        head = s <= d[N_HEAD - 1] + 1e-6
        blend = 1.0 if head else max(0.0, 1.0 - (s - d[N_HEAD - 1]) / 0.06)   # head wedge -> round neck
        out.append(dict(y=y, z=z, ty=t[0], tz=t[1], W=W / 2, Tu=Tu, Td=Td, blend=blend, s=s))
    # body: on the ground, h = y - Y_BASE; spacing ~ one face width, finer on the tail taper
    h = 0.0
    hs = []
    while h < PLAN.L - 1e-6:
        hs.append(h)
        W, T, lift = body_at(h)
        h += max(0.012, min(ds_body, 0.15 * W))
    hs.append(PLAN.L)
    s0 = d[-1]
    for h in hs:
        W, T, lift = body_at(h)
        e = 0.04
        z = lambda q: body_at(q)[2] + body_at(q)[1] / 2
        t = np.array((2 * e, 0.5 * (z(min(PLAN.L, h + e)) - z(max(0, h - e))))); t /= np.linalg.norm(t)   # half tilt
        out.append(dict(y=Y_BASE + h, z=lift + T / 2, ty=t[0], tz=t[1], W=W / 2, Tu=T / 2, Td=T / 2, blend=0.0, s=s0 + h))
    return out


def ring_pts(st, n=NV):
    """the half-ring vertices of a station (straight snake), top seam first."""
    pb, ph = prof_body(n), prof_head(n)
    b = st['blend']
    ny, nz = -st['tz'], st['ty']                   # sagittal normal (dorsal side)
    pts = []
    for (bx, bh), (hx, hh) in zip(pb, ph):
        fx, fh = bx * (1 - b) + hx * b, bh * (1 - b) + hh * b
        off = fh * (st['Tu'] if fh > 0 else st['Td'])
        pts.append((fx * st['W'], st['y'] + ny * off, st['z'] + nz * off))
    return pts


# ---------------------------------------------------------------- numpy mesh (for the design tool)
def mesh_np(n=NV):
    ST = stations()
    R = [ring_pts(s, n) for s in ST]
    V = []
    for r in R:
        V += r
    F = []
    for i in range(len(R) - 1):
        for j in range(n - 1):
            a, b = i * n + j, i * n + j + 1
            F.append((a, b, b + n, a + n))
    V = np.array(V)
    VM = V * np.array((-1, 1, 1))                   # mirror
    nv = len(V)
    F2 = F + [tuple(i + nv for i in f[::-1]) for f in F]
    F2 += [tuple(range(n)), tuple(range(len(V) - n, len(V)))]
    F2 += [tuple(i + nv for i in range(n)), tuple(i + nv for i in range(len(V) - n, len(V)))]
    return np.r_[V, VM], F2, ST


STATIONS = stations()
_SY = np.array([s['y'] for s in STATIONS]); _SZ = np.array([s['z'] for s in STATIONS])
_TY = np.array([s['ty'] for s in STATIONS]); _TZ = np.array([s['tz'] for s in STATIONS])
_SS = np.array([s['s'] for s in STATIONS])
S_NECK = _neck_path()[2][-1]
S_SKULL = _neck_path()[2][N_HEAD - 1]
