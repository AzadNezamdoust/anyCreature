"""
rig_sim.py -- the function stage's simple vehicle physics (pure Python stdlib: no Blender, no numpy, no engine).

A raycast-vehicle: ONE rigid body (mass, diagonal inertia about the centre of mass) on N spring-damper contacts (a
wheel, a track road wheel, a helicopter skid point). Each contact is a ray along the body's up axis from the contact's
rest centre: the rolling-circle envelope of the ground under it gives the compression c (m, + = wheel pushed up into
the body, 0 = the modelled rest pose), the suspension pushes with  F = N + k c + d c'  (N = the static load, so the
modelled pose IS the equilibrium), a bump stop (bump_stop_ratio x k, default 30) acts beyond the bump travel, the wheel hangs at -droop when the
ground is further away (airborne, F = 0). Tyre forces: a longitudinal drive / brake command spread over the wheels by
load and a lateral slip friction, both clamped to mu F. Semi-implicit Euler, dt 2 ms.

Frame = the rig contract's AUTHOR frame: x left (near flank), y up, z nose, metres; ground y = 0.

  python scripts/hs/rig_sim.py out/blender-hs/<s>/rig_stats.json     # re-runs the sim on the stats' "sim_input"

simulate(inp) -> {"tests": {name: {"pass": bool, ...numbers}}, "frames": [{label, t, pos, rot, comp}], "static": {...}}
inp (rig_pass.py builds it from rig.json + the measured geometry):
  mass, com [x,y,z], inertia [Ixx,Iyy,Izz], g
  contacts [{id, pos [x,y,z], radius, bump, droop, clear_bump (measured arch clearance), driven, braked}]
  frequency_hz, damping_ratio, mu
  chassis_points [[x,y,z], ...]      underside points of the chassis collider (must never touch the ground)
  drive (bool)                       False: only the drop test (helicopters)
  lock_roll (bool)                   two-wheelers: planar (pitch / heave) simulation
  sim {drop_m, bump_m, bump_len_m, speed_mps, accel_mps2, brake_mps2, brake_from_mps, lateral_g}
  limits {settle_s, ride_err_m, bump_pitch_deg, accel_pitch_deg, brake_pitch_deg, lateral_roll_deg}
"""
import json
import math
import sys

DT = 0.002
PHI = [math.radians(a) for a in range(-60, 61, 15)]
SINP = [math.sin(a) for a in PHI]
COSP = [math.cos(a) for a in PHI]

DEFAULT_SIM = {"drop_m": 0.30, "bump_m": 0.15, "bump_len_m": 0.80, "speed_mps": 5.0, "accel_mps2": 2.5,
               "brake_mps2": 6.0, "brake_from_mps": 10.0, "lateral_g": 0.4}
DEFAULT_LIMITS = {"settle_s": 3.0, "ride_err_m": 0.010, "bump_pitch_deg": 10.0, "accel_pitch_deg": 3.0,
                  "brake_pitch_deg": 5.0, "lateral_roll_deg": 6.0}


# ------------------------------------------------------------------------------------------------ small vector maths
def _add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _qrot(q):
    """unit quaternion (w, x, y, z) -> 3x3 rotation rows (body -> world)."""
    w, x, y, z = q
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
            (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
            (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)))


def _mv(R, v): return (_dot(R[0], v), _dot(R[1], v), _dot(R[2], v))
def _mtv(R, v): return (R[0][0] * v[0] + R[1][0] * v[1] + R[2][0] * v[2],
                        R[0][1] * v[0] + R[1][1] * v[1] + R[2][1] * v[2],
                        R[0][2] * v[0] + R[1][2] * v[1] + R[2][2] * v[2])


def _sat(x): return -1.0 if x < -1.0 else 1.0 if x > 1.0 else x


def _solve3(M, b):
    """Gaussian elimination with partial pivoting; a (near) singular column is dropped (its unknown = 0)."""
    n = 3
    A = [list(M[i]) + [b[i]] for i in range(n)]
    used = []
    row = 0
    for col in range(n):
        piv = max(range(row, n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-9:
            continue
        A[row], A[piv] = A[piv], A[row]
        k = A[row][col]
        A[row] = [v / k for v in A[row]]
        for r in range(n):
            if r != row and A[r][col]:
                f = A[r][col]
                A[r] = [a - f * c for a, c in zip(A[r], A[row])]
        used.append((row, col))
        row += 1
    x = [0.0] * n
    for r, c in used:
        x[c] = A[r][n]
    return x


# ------------------------------------------------------------------------------------------------ statics
def static_loads(inp):
    """Rest loads N_i = a + b z_i + c x_i (plane distribution) with sum N = m g and zero moment about the COM."""
    g = inp.get("g", 9.81)
    com = inp["com"]
    pts = [(c["pos"][0] - com[0], c["pos"][2] - com[2]) for c in inp["contacts"]]
    n = len(pts)
    sx = sum(p[0] for p in pts)
    sz = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    szz = sum(p[1] * p[1] for p in pts)
    sxz = sum(p[0] * p[1] for p in pts)
    a, b, c = _solve3([[n, sz, sx], [sz, szz, sxz], [sx, sxz, sxx]], [inp["mass"] * g, 0.0, 0.0])
    return [a + b * p[1] + c * p[0] for p in pts]


def convex_hull_2d(pts):
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in pts))
    if len(pts) < 3:
        return pts
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(pts), half(reversed(pts))
    return lo[:-1] + up[:-1]


def stability(inp, half_width=None):
    """Support polygon (convex hull of the contact points, plan x-z; half_width widens each point to a patch +-x),
    COM inside?, static tip-over angles: atan(distance from the COM's plan point to the polygon edge / COM height)
    to each side (roll) and to the front / rear (pitch)."""
    com = inp["com"]
    pts = []
    for c in inp["contacts"]:
        w = (c.get("width", 0.0) / 2) if half_width is None else half_width
        pts += [(c["pos"][0] - w, c["pos"][2]), (c["pos"][0] + w, c["pos"][2])] if w else [(c["pos"][0], c["pos"][2])]
    hull = convex_hull_2d(pts)
    out = {"support_polygon": [[round(x, 4), round(z, 4)] for x, z in hull], "com": [round(v, 4) for v in com]}
    if len(hull) < 3:
        zs = [p[1] for p in hull] or [0.0]
        xs = [p[0] for p in hull] or [0.0]
        out.update({"com_inside": min(zs) <= com[2] <= max(zs), "degenerate": True,
                    "tip_left_deg": 0.0, "tip_right_deg": 0.0,
                    "tip_front_deg": round(math.degrees(math.atan2(max(zs) - com[2], com[1])), 2),
                    "tip_rear_deg": round(math.degrees(math.atan2(com[2] - min(zs), com[1])), 2),
                    "lateral_offset_m": round(com[0] - sum(xs) / len(xs), 4)})
        return out

    def reach(dx, dz):
        """distance from the COM plan point to the hull boundary along (dx, dz); negative = COM outside."""
        best = None
        for i in range(len(hull)):
            a, b = hull[i], hull[(i + 1) % len(hull)]
            ex, ez = b[0] - a[0], b[1] - a[1]
            den = dx * ez - dz * ex
            if abs(den) < 1e-12:
                continue
            t = ((a[0] - com[0]) * ez - (a[1] - com[2]) * ex) / den
            s = ((a[0] - com[0]) * dz - (a[1] - com[2]) * dx) / den
            if -1e-9 <= s <= 1 + 1e-9:
                if t >= 0 and (best is None or t < best):
                    best = t
        return best

    inside = all(reach(dx, dz) is not None for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    out["com_inside"] = inside
    for name, d in (("tip_left_deg", (1, 0)), ("tip_right_deg", (-1, 0)), ("tip_front_deg", (0, 1)),
                    ("tip_rear_deg", (0, -1))):
        r = reach(*d)
        out[name] = round(math.degrees(math.atan2(r, com[1])), 2) if (inside and r is not None) else 0.0
    return out


# ------------------------------------------------------------------------------------------------ the body
class Body:
    def __init__(self, inp, loads):
        self.inp = inp
        self.g = inp.get("g", 9.81)
        self.m = inp["mass"]
        self.I = inp["inertia"]
        self.com = tuple(inp["com"])
        self.mu = inp.get("mu", 0.9)
        self.lock_roll = bool(inp.get("lock_roll"))
        self.stop = float(inp.get("bump_stop_ratio", 30.0))
        f = inp.get("frequency_hz", 1.6)
        zeta = inp.get("damping_ratio", 0.6)
        delta = self.g / (2 * math.pi * f) ** 2
        self.con = []
        for c, N in zip(inp["contacts"], loads):
            k = N / delta
            self.con.append({"id": c["id"], "r": _sub(tuple(c["pos"]), self.com), "R": c.get("radius", 0.0), "N": N,
                             "k": k, "d": 2 * zeta * math.sqrt(k * N / self.g), "bump": c["bump"], "droop": c["droop"],
                             "driven": c.get("driven", True), "braked": c.get("braked", True)})
        self.chassis = [_sub(tuple(p), self.com) for p in inp.get("chassis_points", [])]
        self.reset()

    def reset(self, lift=0.0, speed=0.0):
        self.p = (self.com[0], self.com[1] + lift, self.com[2])
        self.q = (1.0, 0.0, 0.0, 0.0)
        self.v = (0.0, 0.0, speed)
        self.w = (0.0, 0.0, 0.0)        # body frame
        self.t = 0.0
        self.c = [(-c["droop"] if lift > c["droop"] else 0.0) for c in self.con]
        self.incontact = [lift <= c["droop"] for c in self.con]
        self.F = [0.0] * len(self.con)

    def angles(self, R):
        """(pitch nose-up, roll left-side-up) in degrees."""
        return math.degrees(math.asin(_sat(R[1][2]))), math.degrees(math.asin(_sat(R[1][0])))

    def step(self, ground, mode, cmd=0.0, ext=(0.0, 0.0, 0.0)):
        """ground(x, z) -> height (None = flat 0). mode 'park' | 'drive' (cmd = total longitudinal force, N; + =
        forward, - = brake). ext = an extra world force at the COM."""
        R = _qrot(self.q)
        up = (R[0][1], R[1][1], R[2][1])
        fw = (R[0][2], 0.0, R[2][2])
        n = math.hypot(fw[0], fw[2]) or 1.0
        fw = (fw[0] / n, 0.0, fw[2] / n)
        side = (fw[2], 0.0, -fw[0])
        wv = _mv(R, self.w)
        force = [ext[0], ext[1] - self.m * self.g, ext[2]]
        torque = [0.0, 0.0, 0.0]
        loads = []
        for i, c in enumerate(self.con):
            rw = _mv(R, c["r"])
            P = _add(self.p, rw)
            if ground is None:
                yt = c["R"]
            elif c["R"] > 0:
                yt = max(ground(P[0] + fw[0] * c["R"] * s, P[2] + fw[2] * c["R"] * s) + c["R"] * co
                         for s, co in zip(SINP, COSP))
            else:
                yt = ground(P[0], P[2])
            comp = (yt - P[1]) / max(up[1], 0.2)
            if comp < -c["droop"]:
                self.c[i], self.incontact[i], self.F[i] = -c["droop"], False, 0.0
                loads.append(None)
                continue
            cd = (comp - self.c[i]) / DT if self.incontact[i] else 0.0
            F = c["N"] + c["k"] * comp + c["d"] * cd
            if comp > c["bump"]:
                F += self.stop * c["k"] * (comp - c["bump"]) + c["d"] * cd
            F = max(F, 0.0)
            self.c[i], self.incontact[i], self.F[i] = comp, True, F
            arm = _add(rw, _mul(up, comp))
            arm = (arm[0], arm[1] - c["R"], arm[2])
            loads.append((F, arm, _add(self.v, _cross(wv, arm))))
        tot_d = sum(l[0] for l, c in zip(loads, self.con) if l and (c["driven"] if cmd >= 0 else c["braked"])) or 1.0
        for l, c in zip(loads, self.con):
            if not l:
                continue
            F, arm, vel = l
            vl, vs = _dot(vel, fw), _dot(vel, side)
            if mode == "park":
                fx = -self.mu * F * _sat(vl / 0.02)
            else:
                share = F / tot_d if (c["driven"] if cmd >= 0 else c["braked"]) else 0.0
                fx = max(-self.mu * F, min(self.mu * F, cmd * share))
            fy = -self.mu * F * _sat(vs / 0.02)
            f = (fw[0] * fx + side[0] * fy, F, fw[2] * fx + side[2] * fy)
            force[0] += f[0]
            force[1] += f[1]
            force[2] += f[2]
            tq = _cross(arm, f)
            torque[0] += tq[0]
            torque[1] += tq[1]
            torque[2] += tq[2]
        acc = (force[0] / self.m, force[1] / self.m, force[2] / self.m)
        self.v = _add(self.v, _mul(acc, DT))
        tb = _mtv(R, torque)
        Iw = (self.I[0] * self.w[0], self.I[1] * self.w[1], self.I[2] * self.w[2])
        gy = _cross(self.w, Iw)
        self.w = (self.w[0] + (tb[0] - gy[0]) / self.I[0] * DT, self.w[1] + (tb[1] - gy[1]) / self.I[1] * DT,
                  self.w[2] + (tb[2] - gy[2]) / self.I[2] * DT)
        if self.lock_roll:
            self.w = (self.w[0], 0.0, 0.0)
            self.v = (0.0, self.v[1], self.v[2])
        w, x, y, z = self.q
        ox, oy, oz = self.w
        dq = (-x * ox - y * oy - z * oz, w * ox + y * oz - z * oy, w * oy - x * oz + z * ox, w * oz + x * oy - y * ox)
        q = (w + 0.5 * dq[0] * DT, x + 0.5 * dq[1] * DT, y + 0.5 * dq[2] * DT, z + 0.5 * dq[3] * DT)
        n = math.sqrt(sum(a * a for a in q))
        self.q = tuple(a / n for a in q)
        self.p = _add(self.p, _mul(self.v, DT))
        self.t += DT
        return acc

    def clearance(self, ground):
        """lowest chassis collider point above the ground (m)."""
        if not self.chassis:
            return 9.0
        R = _qrot(self.q)
        best = 9.0
        for r in self.chassis:
            P = _add(self.p, _mv(R, r))
            best = min(best, P[1] - (ground(P[0], P[2]) if ground else 0.0))
        return best

    def frame(self, label):
        R = _qrot(self.q)
        return {"label": label, "t": round(self.t, 3), "pos": [round(a, 5) for a in self.p],
                "rot": [[round(a, 6) for a in row] for row in R], "comp": [round(a, 5) for a in self.c]}


class Track:
    """Running extremes of one scenario."""
    def __init__(self, body):
        n = len(body.con)
        self.cmax = [-9.0] * n
        self.cmin = [9.0] * n
        self.air = [0.0] * n
        self.clear = 9.0
        self.pitch = [0.0, 0.0]
        self.roll = [0.0, 0.0]
        self.gmax = 0.0
        self.last_unsettled = 0.0

    def see(self, b, ground, acc, settle_from=0.0):
        for i, c in enumerate(b.c):
            if c > self.cmax[i]:
                self.cmax[i] = c
            if c < self.cmin[i]:
                self.cmin[i] = c
            if not b.incontact[i]:
                self.air[i] += DT
        cl = b.clearance(ground)
        if cl < self.clear:
            self.clear = cl
        p, r = b.angles(_qrot(b.q))
        self.pitch = [min(self.pitch[0], p), max(self.pitch[1], p)]
        self.roll = [min(self.roll[0], r), max(self.roll[1], r)]
        self.gmax = max(self.gmax, abs(acc[1]) / b.g)
        if b.t >= settle_from and (abs(b.v[1]) > 0.02 or abs(b.w[0]) > 0.02 or abs(b.w[2]) > 0.02):
            self.last_unsettled = b.t


def _r(x, n=4):
    return round(x, n)


def _comp_report(b, tr):
    worst = max(range(len(b.con)), key=lambda i: tr.cmax[i] - b.inp["contacts"][i].get("clear_bump", b.con[i]["bump"]))
    c = b.inp["contacts"][worst]
    clear = c.get("clear_bump", b.con[worst]["bump"])
    return {"max_compression_m": _r(max(tr.cmax)), "max_droop_m": _r(-min(tr.cmin)),
            "worst_wheel": b.con[worst]["id"], "worst_compression_m": _r(tr.cmax[worst]),
            "arch_clear_m": _r(clear), "margin_to_arch_m": _r(clear - tr.cmax[worst]),
            "bump_stop_hit": any(tr.cmax[i] > b.con[i]["bump"] + 1e-4 for i in range(len(b.con))),
            "airborne_s": _r(max(tr.air), 3)}


def simulate(inp):
    sim = {**DEFAULT_SIM, **(inp.get("sim") or {})}
    lim = {**DEFAULT_LIMITS, **(inp.get("limits") or {})}
    loads = static_loads(inp)
    out = {"static": {"loads_N": {c["id"]: _r(N, 1) for c, N in zip(inp["contacts"], loads)},
                      "min_load_N": _r(min(loads), 1)}, "tests": {}, "frames": []}
    if min(loads) <= 0:
        out["tests"]["static_loads"] = {"pass": False, "why": "a contact carries no load at rest (COM outside the support)"}
        return out
    b = Body(inp, loads)
    T = out["tests"]
    F = out["frames"]

    # ---- 1. drop and settle
    b.reset(lift=sim["drop_m"])
    tr = Track(b)
    F.append(b.frame("DROP T 0.00"))
    tmax = lim["settle_s"] + 2.0
    peak, peak_frame = -9.0, None
    while b.t < tmax:
        acc = b.step(None, "park")
        tr.see(b, None, acc)
        if max(b.c) > peak:
            peak, peak_frame = max(b.c), b.frame(f"DROP MAX COMPRESSION T {b.t:.2f}")
    F.append(peak_frame)
    F.append(b.frame(f"DROP SETTLED T {b.t:.2f}"))
    p, r = b.angles(_qrot(b.q))
    ride = b.p[1] - b.com[1]
    rep = _comp_report(b, tr)
    T["drop_settle"] = {"drop_m": sim["drop_m"], "settle_s": _r(tr.last_unsettled, 2), "limit_s": lim["settle_s"],
                        "ride_height_err_m": _r(ride), "final_pitch_deg": _r(p, 3), "final_roll_deg": _r(r, 3),
                        "min_chassis_clearance_m": _r(tr.clear), "peak_g": _r(tr.gmax, 2), **rep}
    T["drop_settle"]["pass"] = bool(tr.last_unsettled <= lim["settle_s"] and abs(ride) <= lim["ride_err_m"]
                                    and tr.clear > 0 and rep["margin_to_arch_m"] >= 0 and abs(p) < 1 and abs(r) < 1)
    if not inp.get("drive", True):
        return out

    zs = [c["pos"][2] for c in inp["contacts"]]
    zf, zr = max(zs), min(zs)
    rmax = max(c.get("radius", 0.0) for c in inp["contacts"])
    v0 = sim["speed_mps"]

    # ---- 2. bump at speed (full width, sin^2 profile)
    zb = zf + rmax + 1.0
    H, L = sim["bump_m"], sim["bump_len_m"]

    def ground(x, z):
        s = (z - zb) / L
        return H * math.sin(math.pi * s) ** 2 if 0.0 < s < 1.0 else 0.0

    b.reset(speed=v0)
    tr = Track(b)
    t_clear = (zb + L + rmax - zr) / v0          # the last axle is off the bump
    shots = {"BUMP FRONT AXLE": (zb + L / 2 - zf) / v0, "BUMP MID": (zb + L / 2 - (zf + zr) / 2) / v0,
             "BUMP REAR AXLE": (zb + L / 2 - zr) / v0}
    tmax = t_clear + lim["settle_s"] + 1.0
    while b.t < tmax:
        cmd = b.m * max(-3.0, min(3.0, 4.0 * (v0 - b.v[2])))
        acc = b.step(ground, "drive", cmd)
        tr.see(b, ground, acc, settle_from=t_clear)
        for k in [k for k, ts in shots.items() if b.t >= ts]:
            F.append({**b.frame(f"{k} T {b.t:.2f}"), "bump": {"z": zb, "len": L, "h": H}})
            del shots[k]
    rep = _comp_report(b, tr)
    T["bump"] = {"bump_m": H, "bump_len_m": L, "speed_mps": v0, "pitch_deg": [_r(tr.pitch[0], 2), _r(tr.pitch[1], 2)],
                 "roll_deg": [_r(tr.roll[0], 2), _r(tr.roll[1], 2)], "limit_pitch_deg": lim["bump_pitch_deg"],
                 "min_chassis_clearance_m": _r(tr.clear), "peak_g": _r(tr.gmax, 2),
                 "resettle_s": _r(max(0.0, tr.last_unsettled - t_clear), 2), "limit_s": lim["settle_s"],
                 "exit_speed_mps": _r(b.v[2], 2), **rep}
    T["bump"]["pass"] = bool(tr.clear > 0 and rep["margin_to_arch_m"] >= 0
                             and max(abs(tr.pitch[0]), abs(tr.pitch[1])) <= lim["bump_pitch_deg"]
                             and tr.last_unsettled - t_clear <= lim["settle_s"])

    # ---- 3. accelerate from rest
    b.reset()
    tr = Track(b)
    acc_p = []
    while b.t < 2.5:
        acc = b.step(None, "drive", b.m * sim["accel_mps2"])
        tr.see(b, None, acc)
        if b.t > 1.8:
            acc_p.append(b.angles(_qrot(b.q))[0])
    F.append(b.frame(f"ACCEL {sim['accel_mps2']:.1f} M/S2"))
    steady = sum(acc_p) / len(acc_p)
    rep = _comp_report(b, tr)
    T["accelerate"] = {"accel_mps2": sim["accel_mps2"], "reached_mps": _r(b.v[2], 2), "steady_pitch_deg": _r(steady, 2),
                       "peak_pitch_deg": _r(tr.pitch[1], 2), "limit_pitch_deg": lim["accel_pitch_deg"], **rep}
    T["accelerate"]["pass"] = bool(abs(steady) <= lim["accel_pitch_deg"] and rep["airborne_s"] == 0
                                   and rep["margin_to_arch_m"] >= 0 and b.v[2] > 0.8 * sim["accel_mps2"] * 2.5)

    # ---- 4. brake to a stop
    vb = sim["brake_from_mps"]
    b.reset(speed=vb)
    tr = Track(b)
    z_start, t_stop, shot = b.p[2], None, False
    while b.t < vb / sim["brake_mps2"] + 2.5:
        moving = b.v[2] > 0.15
        acc = b.step(None, "drive" if moving else "park", -b.m * sim["brake_mps2"] if moving else 0.0)
        if not moving and t_stop is None:
            t_stop = b.t
            dist = b.p[2] - z_start
        if t_stop is None:
            tr.see(b, None, acc)
            if not shot and b.t > 0.6:
                F.append(b.frame(f"BRAKE {sim['brake_mps2']:.1f} M/S2"))
                shot = True
    rep = _comp_report(b, tr)
    T["brake"] = {"brake_mps2": sim["brake_mps2"], "from_mps": vb, "stop_s": _r(t_stop or -1, 2),
                  "stop_dist_m": _r(dist if t_stop else -1, 2), "dive_pitch_deg": _r(tr.pitch[0], 2),
                  "limit_pitch_deg": lim["brake_pitch_deg"], **rep}
    T["brake"]["pass"] = bool(t_stop is not None and abs(tr.pitch[0]) <= lim["brake_pitch_deg"]
                              and rep["airborne_s"] == 0 and rep["margin_to_arch_m"] >= 0)

    # ---- 5. steady lateral load (cornering / side slope)
    if not b.lock_roll:
        b.reset()
        tr = Track(b)
        rolls = []
        while b.t < 3.0:
            acc = b.step(None, "park", ext=(b.m * b.g * sim["lateral_g"] * min(1.0, b.t / 0.5), 0.0, 0.0))
            tr.see(b, None, acc)
            if b.t > 2.4:
                rolls.append(b.angles(_qrot(b.q))[1])
        F.append(b.frame(f"LATERAL {sim['lateral_g']:.1f} G"))
        steady = sum(rolls) / len(rolls)
        rep = _comp_report(b, tr)
        T["lateral"] = {"lateral_g": sim["lateral_g"], "steady_roll_deg": _r(steady, 2),
                        "limit_roll_deg": lim["lateral_roll_deg"], "slide_m": _r(b.p[0] - b.com[0], 3), **rep}
        T["lateral"]["pass"] = bool(abs(steady) <= lim["lateral_roll_deg"] and rep["airborne_s"] == 0
                                    and rep["margin_to_arch_m"] >= 0)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    inp = data.get("sim_input", data)
    res = simulate(inp)
    print("STATIC", json.dumps(res["static"]))
    print("STABILITY", json.dumps(stability(inp)))
    for k, v in res["tests"].items():
        print("PASS" if v["pass"] else "FAIL", k, json.dumps({a: b for a, b in v.items() if a != "pass"}))
