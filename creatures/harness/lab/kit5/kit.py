"""SDF anatomy kit.  Frame: x forward (head), y up (ground y=0), z lateral (+z = left side).
Every part is a loft of super-elliptic sections along a smooth (Catmull-Rom) path, so
cross-sections are never round tubes unless asked. Parts register ops on a Body; Body.mesh()
evaluates only inside each op's bbox (fast) then marches, Taubin-smooths, decimates, writes OBJ.
"""
import numpy as np
from skimage.measure import marching_cubes
import sdf2

# ------------------------------------------------------------------ math
def V(*a): return np.array(a, float)
def nrm(v): v = np.asarray(v, float); return v / (np.linalg.norm(v) + 1e-12)
def lerp(a, b, t): return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t

def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
def smax(a, b, k): return -smin(-a, -b, k)

def frame(a, b, up):
    ax = nrm(np.subtract(b, a)); u = nrm(up)
    if abs(ax.dot(u)) > 0.97: u = nrm(np.cross(ax, (0, 0, 1.0))) if abs(ax[2]) < .9 else V(0, 1, 0)
    s = nrm(np.cross(ax, u)); t = np.cross(s, ax); return ax, t, s

def catmull(P, n):
    """densify control points P (k,dim) with n sub-steps per span (passes through all points)"""
    P = np.asarray(P, float)
    if len(P) < 3: return np.array([lerp(P[0], P[-1], t) for t in np.linspace(0, 1, n + 1)])
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]]); out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1:i + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1]); return np.array(out)

# ------------------------------------------------------------------ primitive fields (X,Y,Z broadcast)
def _local(X, Y, Z, a, ax, t, s):
    x, y, z = X - a[0], Y - a[1], Z - a[2]
    return (x * ax[0] + y * ax[1] + z * ax[2], x * t[0] + y * t[1] + z * t[2], x * s[0] + y * s[1] + z * s[2])

def f_seg(a, b, A, B, up, ext0=0.0, ext1=0.0):
    """tapered super-elliptic segment. A,B=(half_depth, half_width, depth_offset, exponent)"""
    a = np.asarray(a, float); b = np.asarray(b, float); L = np.linalg.norm(b - a) + 1e-9
    ax, t, s = frame(a, b, up)
    def fn(X, Y, Z):
        x, y, z = _local(X, Y, Z, a, ax, t, s)
        h = np.clip(x / L, 0, 1)
        ax_ = x - h * L
        # interior joints: squash the cap along the axis so a span never overhangs its neighbour
        ax_ = ax_ * np.where(ax_ < 0, 1 + 2 * ext0, 1 + 2 * ext1)
        d = A[0] + (B[0] - A[0]) * h; w = A[1] + (B[1] - A[1]) * h
        o = A[2] + (B[2] - A[2]) * h; p = A[3] + (B[3] - A[3]) * h
        d = np.maximum(d, 1e-3); w = np.maximum(w, 1e-3); r = np.minimum(d, w)
        e = (np.abs((y - o) / d) ** p + np.abs(z / w) ** p) ** (1 / p)
        return np.sqrt(ax_ ** 2 + (e * r) ** 2) - r
    rad = 1.3 * max(A[0], A[1], B[0], B[1]) + max(abs(A[2]), abs(B[2]))
    return fn, np.minimum(a, b) - rad, np.maximum(a, b) + rad

def f_ell(c, axis, up, r):
    """oriented ellipsoid: r=(along axis, along up, lateral)"""
    c = np.asarray(c, float); ax, t, s = frame(c, c + nrm(axis), up)
    def fn(X, Y, Z):
        x, y, z = _local(X, Y, Z, c, ax, t, s)
        k0 = np.sqrt((x / r[0]) ** 2 + (y / r[1]) ** 2 + (z / r[2]) ** 2)
        k1 = np.sqrt((x / r[0] ** 2) ** 2 + (y / r[1] ** 2) ** 2 + (z / r[2] ** 2) ** 2)
        return k0 * (k0 - 1) / (k1 + 1e-9)
    R = max(r); return fn, c - R, c + R

def f_plane_cut(p, n):
    p = np.asarray(p, float); n = nrm(n)
    return lambda X, Y, Z: (X - p[0]) * n[0] + (Y - p[1]) * n[1] + (Z - p[2]) * n[2]

def f_box(c, half, axis, up, r=0.0):
    c = np.asarray(c, float); ax, t, s = frame(c, c + nrm(axis), up)
    def fn(X, Y, Z):
        x, y, z = _local(X, Y, Z, c, ax, t, s)
        qx, qy, qz = np.abs(x) - half[0] + r, np.abs(y) - half[1] + r, np.abs(z) - half[2] + r
        o = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
        return o + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - r
    R = np.linalg.norm(half); return fn, c - R, c + R

# ------------------------------------------------------------------ body / assembly
class Body:
    def __init__(self, kin=0.03): self.ops = []; self.kin = kin
    def _op(self, kind, fn, lo, hi, k, mirror):
        lo = np.array(lo, float); hi = np.array(hi, float)
        if mirror: zm = max(abs(lo[2]), abs(hi[2])); lo[2], hi[2] = -zm, zm
        self.ops.append((kind, fn, lo, hi, k, mirror))
    def add(self, prim, k=0.02, mirror=False): self._op('add', prim[0], prim[1], prim[2], k, mirror)
    def sub(self, prim, k=0.005, mirror=False): self._op('sub', prim[0], prim[1], prim[2], k, mirror)
    def group(self, prims, k_in, k_out, mirror=False):
        """union prims internally with k_in, then blend whole group into body with k_out (per-joint k)"""
        fns = [p[0] for p in prims]; k_in = k_in or getattr(prims, 'kin', 0) or self.kin
        def fn(X, Y, Z):
            d = None
            for f in fns:
                e = f(X, Y, Z); d = e if d is None else smin(d, e, k_in)
            return d
        lo = np.min([p[1] for p in prims], 0); hi = np.max([p[2] for p in prims], 0)
        self._op('add', fn, lo, hi, k_out, mirror)

    def mesh(self, out, n=330, target=80000, smooth=10):
        lo = np.min([o[2] for o in self.ops if o[0] == 'add'], 0) - 0.03
        hi = np.max([o[3] for o in self.ops if o[0] == 'add'], 0) + 0.03
        lo[1] = max(lo[1], -0.01)
        h = (hi - lo).max() / n
        xs, ys, zs = [np.arange(lo[i], hi[i] + h, h, dtype=np.float32) for i in range(3)]
        D = np.full((len(xs), len(ys), len(zs)), 1.0, np.float32)
        for kind, fn, a, b, k, m in self.ops:
            pad = k * 2 + 2 * h
            sl = []
            for ax, arr in enumerate((xs, ys, zs)):
                i0 = max(0, int(np.searchsorted(arr, a[ax] - pad)) - 1); i1 = min(len(arr), int(np.searchsorted(arr, b[ax] + pad)) + 1)
                sl.append(slice(i0, i1))
            X = xs[sl[0]][:, None, None]; Y = ys[sl[1]][None, :, None]; Z = zs[sl[2]][None, None, :]
            if m: Z = np.abs(Z)
            e = fn(X, Y, Z).astype(np.float32)
            blk = D[sl[0], sl[1], sl[2]]
            D[sl[0], sl[1], sl[2]] = smin(blk, e, k) if kind == 'add' else smax(blk, -e, k)
        D = np.maximum(D, -ys[None, :, None])           # ground plane = flat soles
        D = np.pad(D, 1, constant_values=1.0)
        Vn, Fc, _, _ = marching_cubes(D, 0, spacing=(h, h, h))
        Vn = Vn - h + lo; Fc = Fc[:, [0, 2, 1]]
        Vn, Fc = sdf2.clean(Vn.astype(float), Fc)
        Vn = sdf2.taubin(Vn, Fc, smooth); n0 = len(Fc)
        if len(Fc) > target: Vn, Fc = sdf2.decimate(Vn, Fc, target); Vn = sdf2.taubin(Vn, Fc, 3)
        with open(out, 'w') as o:
            o.write(''.join('v %.4f %.4f %.4f\n' % tuple(p) for p in Vn))
            o.write(''.join('f %d %d %d\n' % (t[0] + 1, t[1] + 1, t[2] + 1) for t in Fc))
        print(out, 'grid', D.shape, n0, '->', len(Fc), 'tris'); return len(Fc)

def mirror_z(p): p = np.array(p, float); p[2] = -p[2]; return p

# ------------------------------------------------------------------ loft: the workhorse
def loft(pts, secs, up=(0, 1, 0), sub=4, k=0.0):
    """pts: control points; secs: per point (half_depth, half_width[, depth_offset[, exponent]]).
    Returns list of segment prims (union them with group/blend)."""
    S = np.array([list(s) + [0.0, 2.0][len(s) - 2:] if len(s) < 4 else list(s) for s in secs], float)
    sub = max(sub * 3, 8); P = catmull(pts, sub); Q = catmull(S, sub)
    Q[:, 0:2] = np.maximum(Q[:, 0:2], 1e-3); Q[:, 3] = np.maximum(Q[:, 3], 1.2)
    ups = [up] * len(P) if np.ndim(up) == 1 else catmull(up, sub)
    m = len(P) - 1
    out = _Prims([_sweep(P, Q, ups)])
    out.kin = 1e-6
    return out

def _sweep(P, Q, ups):
    """single continuous swept field: per sample, pick the closest span and use the section
    interpolated there (no per-span caps -> no joint rings / seam bands)."""
    segs = [f_seg(P[i], P[i + 1], Q[i], Q[i + 1], ups[i], 0.0, 0.0) for i in range(len(P) - 1)]
    def fn(X, Y, Z):
        d = None
        for f, lo, hi in segs:
            e = f(X, Y, Z)
            d = e if d is None else smin(d, e, 0.0)
        return d
    lo = np.min([s_[1] for s_ in segs], 0); hi = np.max([s_[2] for s_ in segs], 0)
    return fn, lo, hi
    return out

class _Prims(list):
    kin = 0.0
    def __add__(self, o):
        r = _Prims(list(self) + list(o)); r.kin = max(self.kin, getattr(o, 'kin', 0)); return r

def strand(a, ctrl, b, r0, tip=0.004, flat=0.45, up=(0, 1, 0), sub=3):
    """hair clump / feather vane: flat tapered ribbon a->ctrl->b"""
    return loft([a, ctrl, b], [(r0 * flat, r0, 0, 2), (r0 * .8 * flat, r0 * .8, 0, 2), (tip, tip, 0, 2)], up=up, sub=sub)

# ------------------------------------------------------------------ TORSO
def torso(b, stations, scap=None, keel=None, ridge=0.012, k=0.04, box=2.15):
    """stations: list of (x, top_y, belly_y, half_width) front->back (chest..rump).
    scap: dict(top, point, width) scapula plates; keel: (front_point, depth) sternum keel."""
    st = sorted(stations, key=lambda s: -s[0])
    pts = [(x, (t + bo) / 2, 0) for x, t, bo, w in st]
    secs = [((t - bo) / 2, w, 0, box) for x, t, bo, w in st]   # box>2.4 -> tapered-box ribcage
    b.group(loft(pts, secs, sub=5), 0.0, 0.0)
    if ridge:   # dorsal spinous ridge (withers -> croup): narrow, low, blended
        rp = [(x, t - ridge * 1.5, 0) for x, t, bo, w in st[1:-1]]
        b.group(loft(rp, [(ridge * 2.2, ridge * 1.3)] * len(rp), sub=3), 0, ridge * 3)
    if scap:    # scapula: thin plate lying on ribcage, spine of scapula as low ridge
        top, pt, w = [np.asarray(scap[n], float) if n != 'width' else scap[n] for n in ('top', 'point', 'width')]
        b.add(f_seg(top, pt, (w, w * 0.22, 0, 2.2), (w * 0.7, w * 0.3, 0, 2.2), up=(1, 0, 0)), k=w * 1.2, mirror=True)
        if 0: cord(b, [lerp(top, pt, .1) + V(0, 0, w * .2), lerp(top, pt, .5) + V(0, 0, w * .3), lerp(top, pt, .85) + V(0, 0, w * .3)], w * .22, w * .12, up=(0, 0, 1))  # scapular spine
    if keel:    # sternum / chest keel: narrow deep blade under chest front
        fp, dep = keel[:2]; fp = np.asarray(fp, float); kl = keel[2] if len(keel) > 2 else dep * 4
        back = fp + V(-kl, -dep * 0.6, 0)
        b.group(loft([fp, back], [(dep * .9, dep * .55, 0, 2.2), (dep * .4, dep * .45, 0, 2.0)], up=(0, 1, 0)), 0, dep * 1.5)

def belly_tuck(b, x, y, w, k=0.06):
    """flank fold / stifle web: removes a soft wedge so the belly line tucks up at the loin"""
    b.sub(f_ell(V(x, y, 0), (1, 0, 0), (0, 1, 0), (w * 1.6, w * .55, w * 3)), k=k)

# ------------------------------------------------------------------ NECK + MANE
def neck(b, base, head, base_dw, head_dw, crest=0.0, sag=0.0, k=0.06, mane=None):
    """base/head points; *_dw=(half_depth, half_width). crest lifts topline (stallion crest).
    mane=dict(length, count, thick, fall) draws hanging hair clumps from the crest."""
    base = np.asarray(base, float); head = np.asarray(head, float)
    mid = lerp(base, head, .5) + V(0, -sag, 0)
    md = lerp(base_dw, head_dw, .55)
    secs = [(base_dw[0], base_dw[1], 0, 2.1), (md[0] + crest, md[1], crest * .6, 2.2), (head_dw[0], head_dw[1], 0, 2.1)]
    b.group(loft([base, mid, head], secs, up=(0, 1, 0), sub=6), 0, k)
    if mane and mane.get('style') == 'solid':
        # solid roached/lying mane: a crest cord sitting on the topline, falling slightly to +z
        P = catmull([base, mid, head], 3); pts = []
        for i in range(1, len(P) - 1):
            t = i / (len(P) - 1); ax = nrm(P[i + 1] - P[i - 1]); nup = nrm(np.cross(V(0, 0, 1), ax))
            dd = lerp(base_dw, head_dw, t)[0] + crest * np.sin(np.pi * t)
            pts.append(P[i] + nup * (dd - mane['thick'] * .6) + V(0, 0, mane['thick'] * .5))
        cord(b, pts, mane['length'], mane['thick'], up=(0, 0, 1), mirror=False)
    elif mane:
        P = catmull([base, mid, head], 6); n = mane['count']
        for i in range(n):
            t = (i + .5) / n; j = t * (len(P) - 1); i0 = int(j); f = j - i0
            p = lerp(P[i0], P[min(i0 + 1, len(P) - 1)], f)
            ax = nrm(P[min(i0 + 1, len(P) - 1)] - P[i0]); nup = nrm(np.cross(V(0, 0, 1), ax))
            dd = lerp(base_dw, head_dw, t)[0] + crest * np.sin(np.pi * t)
            root = p + nup * dd * 0.92
            L = mane['length'] * (0.75 + 0.35 * np.sin(i * 2.3) ** 2) * (0.7 + 0.3 * np.sin(np.pi * t))
            fall = mane.get('fall', 0.6); side = 1 if i % 2 == 0 else -1
            ctrl = root + nup * L * .25 + V(0, 0, side * L * .25 * fall) - ax * L * .1
            tip = root + nup * L * (0.3 - fall) + V(0, -L * fall * .6, side * L * .7 * fall) - ax * L * .2
            b.group(strand(root, ctrl, tip, mane['thick'], flat=0.5, up=ax), 0, mane['thick'] * 1.2)

# ------------------------------------------------------------------ SKULL
class Head:
    """local head frame: origin at poll, u forward along face, v up (dorsal), z lateral."""
    def __init__(self, poll, pitch_deg, length):
        a = np.radians(pitch_deg)   # pitch: 0 = horizontal, +ve nose down
        self.o = np.asarray(poll, float); self.L = length
        self.u = V(np.cos(a), -np.sin(a), 0); self.v = V(np.sin(a), np.cos(a), 0)
    def P(self, s, up=0.0, side=0.0):
        return self.o + self.u * s * self.L + self.v * up * self.L + V(0, 0, side * self.L)

def skull(b, H, cranium_w, cranium_h, muzzle_w, muzzle_h, jaw_depth, cheek=0.12, stop=0.03,
          brow=0.02, eye_r=0.035, eye_at=0.32, nose='horse', k=0.02, s0=0.0):
    """all sizes as fractions of head length.  nose: 'horse' (soft lips, comma nostrils) |
    'dog' (leathery nose pad, flews)."""
    L = H.L
    # dorsal skull: cranium -> forehead -> nasal bridge -> muzzle box
    s = [s0, 0.16, 0.34, 0.55, 0.80, 0.97]
    up = [-cranium_h * .2, -cranium_h * .25, -cranium_h * .35 - stop, -muzzle_h * .9 - stop * .5, -muzzle_h * 1.0, -muzzle_h * 1.05]
    hd = [cranium_h * .75, cranium_h * .8, cranium_h * .72, muzzle_h * 1.0, muzzle_h * .95, muzzle_h * .85]
    hw = [cranium_w * .8, cranium_w, cranium_w * .85, muzzle_w * 1.05, muzzle_w, muzzle_w * .9]
    pts = [H.P(si, ui) for si, ui in zip(s, up)]
    b.group(loft(pts, [(d * L, w * L, 0, 2.3) for d, w in zip(hd, hw)], up=H.v, sub=4), 0, k * L)
    # mandible: deep rami behind (jowls) narrowing to chin
    ja = [0.14, 0.32, 0.62, 0.93]
    jup = [-cranium_h * .9 - jaw_depth * .5, -cranium_h * .9 - jaw_depth * .55, -muzzle_h * 1.6 - jaw_depth * .2, -muzzle_h * 1.75]
    jd = [jaw_depth * .55, jaw_depth * .5, jaw_depth * .28, muzzle_h * .55]
    jw = [cranium_w * .95, cranium_w * .78, muzzle_w * .8, muzzle_w * .75]
    b.group(loft([H.P(si, ui) for si, ui in zip(ja, jup)], [(d * L, w * L, 0, 2.2) for d, w in zip(jd, jw)], up=H.v, sub=4), 0, k * 1.5 * L)
    # cheekbone (zygomatic arch / facial crest): low ridge from below eye forward
    for sgn in (1,):
        c0 = H.P(eye_at - .02, -cranium_h * .55, cranium_w * .78); c1 = H.P(eye_at + cheek * 2.2, -muzzle_h * 1.25, muzzle_w * 1.05)
        b.add(f_seg(c0, c1, (0.018 * L, 0.022 * L, 0, 2), (0.008 * L, 0.012 * L, 0, 2), up=H.v), k=0.02 * L, mirror=True)
    # brow ridge over eye
    bc = H.P(eye_at, -cranium_h * .05, cranium_w * .62)
    b.add(f_ell(bc, H.u, H.v, (eye_r * 1.6 * L, eye_r * .55 * L, eye_r * .9 * L)), k=brow * L, mirror=True)
    # eye socket + eyeball (slightly proud, lids from smooth blend)
    ec = H.P(eye_at, -cranium_h * .3, cranium_w * .83)
    b.sub(f_ell(ec + V(0, 0, eye_r * .5 * L), H.u, H.v, (eye_r * 1.3 * L, eye_r * L, eye_r * L)), k=0.012 * L, mirror=True)
    b.add(f_ell(ec + V(0, 0, -eye_r * .4 * L), H.u, H.v, (eye_r * L * .95, eye_r * L * .75, eye_r * L * .9)), k=0.004 * L, mirror=True)
    tip = H.P(1.0, -muzzle_h * 1.05)
    # straight nasal plane (dorsal face) and flat cheek plate / maxilla plane on each side
    flatten(b, H.P(.62, -muzzle_h * .05 - stop * .5), H.v - H.u * .08, (.32 * L, .2 * L, .05 * L), k=.012 * L, mirror=False, axis=H.u)
    flatten(b, H.P(eye_at + .12, -cranium_h * .7, cranium_w * .86), V(0, 0, 1) - H.v * .1, (.13 * L, .1 * L, .04 * L), k=.01 * L, axis=H.u)
    flatten(b, H.P(.72, -muzzle_h * 1.0, muzzle_w * .98), V(0, 0, 1) + H.v * .25, (.2 * L, .06 * L, .03 * L), k=.01 * L, axis=H.u)
    if nose == 'horse':
        # soft upper lip / lower lip pads, comma nostrils on muzzle sides-front
        b.add(f_ell(H.P(.93, -muzzle_h * 1.45), H.u, H.v, (.07 * L, muzzle_h * .55 * L, muzzle_w * .95 * L)), k=.02 * L)
        b.add(f_ell(H.P(.90, -muzzle_h * 1.9), H.u, H.v, (.06 * L, muzzle_h * .35 * L, muzzle_w * .7 * L)), k=.015 * L)
        nc = H.P(.92, -muzzle_h * .75, muzzle_w * .62)
        b.sub(f_ell(nc, H.u - H.v * .4 + V(0, 0, .5), H.v, (.035 * L, .016 * L, .03 * L)), k=.01 * L, mirror=True)
        b.add(f_ell(nc + H.v * .025 * L - H.u * .02 * L - V(0, 0, .008 * L), H.u, H.v, (.035 * L, .009 * L, .014 * L)), k=.008 * L, mirror=True)
        # mouth slit: thin wedge carved between lips, runs back to corner
        m0 = H.P(.98, -muzzle_h * 1.68); m1 = H.P(.80, -muzzle_h * 1.62)
        b.sub(f_seg(m1, m0, (0.004 * L, muzzle_w * .9 * L, 0, 3), (0.004 * L, muzzle_w * 1.2 * L, 0, 3), up=H.v), k=0.004 * L)
    else:
        # dog: nose pad (rhinarium) with philtrum, nostril commas; lips (flews) hang over jaw
        npad = H.P(1.0, -muzzle_h * .75)
        b.add(f_ell(npad, H.u + H.v * .3, H.v, (.055 * L, muzzle_h * .62 * L, muzzle_w * .92 * L)), k=.01 * L)
        groove(b, [H.P(.5, -muzzle_h * 1.75, muzzle_w * .95), H.P(.75, -muzzle_h * 1.6, muzzle_w * 1.0), H.P(.97, -muzzle_h * 1.45, muzzle_w * .7)], .006 * L, .012 * L)  # lip line
        b.sub(f_ell(H.P(1.045, -muzzle_h * .72, muzzle_w * .3), H.u, H.v, (.02 * L, .014 * L, .016 * L)), k=.005 * L, mirror=True)
        b.sub(f_box(H.P(1.03, -muzzle_h * 1.2), (.03 * L, muzzle_h * .3 * L, .003 * L), H.u, H.v), k=.004 * L)
        b.add(f_seg(H.P(.62, -muzzle_h * 1.55, muzzle_w * .55), H.P(.95, -muzzle_h * 1.6, muzzle_w * .5),
                    (.03 * L, .02 * L, 0, 2), (.035 * L, .022 * L, 0, 2), up=H.v), k=.02 * L, mirror=True)
        m0 = H.P(.99, -muzzle_h * 1.72); m1 = H.P(.48, -muzzle_h * 1.85)
        b.sub(f_seg(m1, m0, (0.004 * L, muzzle_w * 1.1 * L, 0, 3), (0.004 * L, muzzle_w * 1.0 * L, 0, 3), up=H.v), k=0.004 * L)

def ear(b, base, tip, width, thick=0.01, cup=0.6, out=(0, 0, 1), k=0.015, rim=0.6):
    """leaf ear: thin shell with rolled rim and concave inner (cup 0..1). 'out' = direction the
    opening faces. Mirrored automatically."""
    base = np.asarray(base, float); tip = np.asarray(tip, float)
    mid = lerp(base, tip, .42)
    nf = nrm(out)
    # outer leaf: flattened (depth=thickness*shell) section that is wide at middle, pointed tip
    secs = [(width * .55, width * .45, 0, 2), (width * .5, width, 0, 2), (thick * 2, thick * 2, 0, 2)]
    b.group(loft([base, mid, tip], secs, up=nf, sub=5), 0, k, mirror=True)
    # concave inner: carve a scaled leaf offset toward the opening
    cut = [(width * .5, width * .3 * rim + .001, width * .5 * cup, 2), (width * .45, width * .7 * rim, width * .6 * cup, 2), (thick, thick, thick, 2)]
    for p in loft([base + nf * width * 0.05, mid, tip - nrm(tip - base) * thick * 3], cut, up=nf, sub=4):
        b.sub(p, k=thick * .6, mirror=True)

def horn(b, base, ctrl, tip, r0, ridges=0, k=0.02, mirror=True):
    """horn / ossicone: curved taper; ossicone if r tip large (rounded knob)"""
    b.group(loft([base, ctrl, tip], [(r0, r0, 0, 2), (r0 * .7, r0 * .7, 0, 2), (r0 * .15, r0 * .15, 0, 2)], up=(1, 0, 0), sub=6), 0, k, mirror=mirror)

# ------------------------------------------------------------------ LIMBS
def foreleg(b, J, g, foot='hoof', k_body=0.08, toe=None):
    """J: dict of landmarks (left side, z>0): scap_top, shoulder, elbow, carpus, fetlock, coronet, ground
    (digitigrade: carpus, paw(=metacarpo-phalangeal), ground). g = forearm half-girth (m).
    Sections are deeper fore-aft than wide on the forearm, flat-sided on cannon, tendon zone behind."""
    sh, el, ca, fe = [np.asarray(J[n], float) for n in ('shoulder', 'elbow', 'carpus', 'fetlock')]
    st = np.asarray(J['scap_top'], float)
    # arm (humerus + triceps mass behind): big, blends into body
    arm = loft([lerp(st, sh, .45), sh, el + V(-.15 * g, .3 * g, 0)],
               [(g * 1.5, g * 1.05, 0, 2.2), (g * 1.6, g * 1.1, 0, 2.2), (g * 1.25, g * 1.05, -.25 * g, 2.2)], up=(1, 0, 0))
    b.group(arm, 0, k_body, mirror=True)
    # forearm: muscle belly front/outside upper 2/3, narrowing to slim tendon zone above carpus
    f1 = lerp(el, ca, .35); f2 = lerp(el, ca, .78)
    fa = loft([el + V(0, .1 * g, 0), f1, f2, ca],
              [(g * 1.15, g * .95, .1 * g, 2.2), (g * 1.0, g * .82, .12 * g, 2.2), (g * .62, g * .52, .02 * g, 2.4), (g * .62, g * .58, 0, 2.6)],
              up=(1, 0, 0), sub=4)
    b.group(fa, 0, g * .6, mirror=True)
    bump(b, sh + V(g * .45, -g * .1, 0), (g * .7, g * .6, g * .6), k=g * .4)   # point of shoulder, forward
    # triceps: big wedge mass between scapula and elbow (behind); deltoid/brachiocephalic head over shoulder
    tc = lerp(lerp(st, sh, .6), el, .5) + V(-g * .7, 0, g * .25)
    b.add(f_ell(tc, el - lerp(st, sh, .6), (1, 0, 0), (np.linalg.norm(el - lerp(st, sh, .6)) * .55, g * 1.3, g * 1.0)), k=g * .9, mirror=True)
    b.add(f_ell(lerp(sh, el, .3) + V(g * .2, 0, g * .35), el - sh, (1, 0, 0), (np.linalg.norm(el - sh) * .45, g * .8, g * .7)), k=g * .8, mirror=True)
    # olecranon (point of elbow): bony knob protruding back/up
    b.add(f_ell(el + V(-g * .9, g * .45, 0), (-.3, 1, 0), (1, 0, 0), (g * .5, g * .38, g * .38)), k=g * .35, mirror=True)
    # carpus: flattened front, accessory carpal bone proud at back
    b.add(f_box(ca + V(.05 * g, 0, 0), (g * .42, g * .5, g * .6), (0, 1, 0), (1, 0, 0), r=g * .2), k=g * .18, mirror=True)  # knee flare: flat front, wide
    b.add(f_ell(ca + V(-g * .55, g * .15, 0), (0, 1, 0), (1, 0, 0), (g * .35, g * .22, g * .18)), k=g * .15, mirror=True)
    _lower(b, ca, fe, J, g, foot, toe)

def hindleg(b, J, g, foot='hoof', k_body=0.1, toe=None, tg=None):
    """J: hip (coxofemoral), stifle, hock, fetlock, coronet, ground (+ 'buttock', 'thigh_out').
    g = gaskin half-girth. Thigh is huge laterally flattened mass, gaskin muscle behind tibia,
    point of hock (calcaneus) protrudes, Achilles tendon a thin band to it."""
    hp, sf, hk, fe = [np.asarray(J[n], float) for n in ('hip', 'stifle', 'hock', 'fetlock')]
    bt = np.asarray(J.get('buttock', hp + V(-.25, -.05, 0)), float)
    # thigh: from hip & buttock down to stifle; deep fore-aft, flat laterally
    gt = tg or g
    th = loft([hp + V(.0, .05, 0), lerp(hp, sf, .5) + V(-gt * .6, 0, 0), sf + V(-gt * .4, gt * .6, 0)],
              [(gt * 3.0, gt * 1.7, -.9 * gt, 2.3), (gt * 2.7, gt * 1.55, -1.1 * gt, 2.3), (gt * 1.4, gt * 1.1, -.3 * gt, 2.2)], up=(1, 0, 0), sub=4)
    b.group(th, 0, k_body, mirror=True)
    # hamstring sweep from buttock down the back of the thigh into gaskin
    hs = loft([bt, lerp(bt, hk, .38) + V(-gt * .2, 0, 0), lerp(sf, hk, .62) + V(-gt * .55, 0, 0)],
              [(gt * 1.3, gt * 1.3, 0, 2.2), (gt * 1.25, gt * 1.15, .3 * gt, 2.2), (gt * .55, gt * .6, .15 * gt, 2.2)], up=(1, 0, 0), sub=4)
    b.group(hs, 0, gt * 1.2, mirror=True)
    # gaskin web: fills the triangle thigh / hamstring / tibia so the haunch reads as one mass
    b.group(loft([lerp(bt, sf, .45), lerp(sf, hk, .3) + V(-gt * .45, 0, 0), lerp(sf, hk, .55) + V(-gt * .4, 0, 0)],
                 [(gt * 1.8, gt * 1.25, 0, 2.2), (gt * 1.35, gt * .95, 0, 2.2), (gt * .8, gt * .65, 0, 2.2)], up=(1, 0, 0), sub=4), 0, gt * .9, mirror=True)
    # stifle patella knob (front)
    b.add(f_ell(sf + V(gt * .6, 0, gt * .25), (0, 1, 0), (1, 0, 0), (gt * .6, gt * .45, gt * .5)), k=gt * .3, mirror=True)
    # big haunch masses: gluteal over hip, biceps femoris sweeping down the side of the thigh
    b.add(f_ell(lerp(hp, bt, .4) + V(0, gt * .6, -gt * .2), (1, 0, 0), (0, 1, 0), (np.linalg.norm(bt - hp) * .7 + gt, gt * 1.3, gt * 1.4)), k=gt * 1.2, mirror=True)
    bf0 = lerp(bt, sf, .35); bf1 = lerp(sf, hk, .3) + V(-gt * .5, 0, 0)
    b.add(f_ell(lerp(bf0, bf1, .5) + V(0, 0, gt * .35), bf1 - bf0, (1, 0, 0), (np.linalg.norm(bf1 - bf0) * .6, gt * 1.5, gt * 1.1)), k=gt * 1.0, mirror=True)
    # fill mass sized from landmarks: closes thigh/gaskin/hamstring triangle (no holes)
    fc = (hp + sf + bt + lerp(sf, hk, .45)) / 4
    b.add(f_ell(fc, lerp(sf, hk, .45) - lerp(hp, bt, .5), (1, 0, 0), (np.linalg.norm(lerp(sf, hk, .45) - lerp(hp, bt, .5)) * .55, np.linalg.norm(bt - sf) * .45, gt * 1.3)), k=gt * 1.0, mirror=True)
    # tibia + gaskin: gaskin belly behind, thin front (tibia crest)
    tb = loft([sf, lerp(sf, hk, .4), lerp(sf, hk, .8), hk + V(g * .1, g * .2, 0)],
              [(g * 1.05, g * .85, -.15 * g, 2.2), (g * 1.15, g * .9, -.4 * g, 2.2), (g * .65, g * .5, -.15 * g, 2.4), (g * .55, g * .5, 0, 2.8)],
              up=(1, 0, 0), sub=4)
    b.group(tb, 0, g * .5, mirror=True)
    # calcaneus (point of hock) + Achilles (common calcanean) tendon band
    pc = hk + V(-g * .85, g * .45, 0)
    b.add(f_ell(pc, (0, 1, 0), (1, 0, 0), (g * .45, g * .3, g * .3)), k=g * .1, mirror=True)
    b.add(f_seg(lerp(sf, hk, .35) + V(-g * .9, 0, 0), pc, (g * .2, g * .18, 0, 2), (g * .2, g * .2, 0, 2), up=(1, 0, 0)), k=g * .35, mirror=True)
    b.add(f_box(hk + V(0, -g * .15, 0), (g * .32, g * .55, g * .45), (0, 1, 0), (1, 0, 0), r=g * .28), k=g * .3, mirror=True)
    _lower(b, hk, fe, J, g * .95, foot, toe)

def _lower(b, top, fe, J, g, foot, toe):
    """cannon (flat-sided, front bone + back tendon gutter) -> fetlock -> pastern -> hoof | paw"""
    # cannon: two lofts — bone in front (narrow), flexor tendons behind separated by shallow groove
    bone = loft([top + V(0, -g * .3, 0), fe + V(g * .05, g * .3, 0)], [(g * .32, g * .42, 0, 2.6), (g * .3, g * .4, 0, 2.6)], up=(1, 0, 0), sub=2)
    ten = loft([top + V(-g * .5, -g * .45, 0), fe + V(-g * .45, g * .3, 0)], [(g * .2, g * .22, 0, 2.2), (g * .22, g * .25, 0, 2.2)], up=(1, 0, 0), sub=2)
    b.group(bone + ten, g * .05, g * .15, mirror=True)
    if foot == 'hoof':
        co, gr = np.asarray(J['coronet'], float), np.asarray(J['ground'], float)
        # fetlock joint: rounded, with ergot bump behind
        b.add(f_ell(fe + V(-g * .06, 0, 0), (0, 1, 0), (1, 0, 0), (g * .44, g * .45, g * .44)), k=g * .12, mirror=True)
        b.add(f_ell(fe + V(-g * .5, -g * .25, 0), (1, -1, 0), (1, 0, 0), (g * .28, g * .2, g * .2)), k=g * .15, mirror=True)
        # pastern: sloping, slightly flattened front-back
        b.group(loft([fe + V(g * .05, -g * .2, 0), co + V(0, g * .1, 0)], [(g * .38, g * .4, 0, 2.2), (g * .4, g * .46, 0, 2.3)], up=(1, 0, 0), sub=2), 0, g * .2, mirror=True)
        # hoof capsule: frustum whose front wall follows pastern angle; flares to ground; heel bulbs
        fw = nrm(gr - co)  # front wall direction
        g = J.get('hoof_g', g)
        hc = co + V(0, 0, 0)
        wall = loft([hc + V(0, g * .05, 0), lerp(hc, gr, .5) + V(-g * .0, 0, 0), V(gr[0] - g * .2, -0.02, gr[2])],
                    [(g * .5, g * .55, 0, 2.6), (g * .66, g * .7, -.03 * g, 2.8), (g * .86, g * .86, -.05 * g, 3.0)], up=(1, 0, 0), sub=3)
        b.group(wall, 0, g * .025, mirror=True)   # small k -> crisp coronet band
        b.add(f_ell(V(co[0] - g * .55, co[1] - g * .2, co[2]), (1, 0, 0), (0, 1, 0), (g * .3, g * .3, g * .45)), k=g * .1, mirror=True)
    else:
        paw(b, fe, J['ground'], g, toe or {})

def paw(b, fe, ground, g, o):
    """digitigrade paw: 4 weight-bearing toes in a tight arch (3,4 lead), digital pads under each
    toe, heart-shaped metacarpal pad, short claws. fe = metacarpophalangeal point."""
    ground = np.asarray(ground, float); fe = np.asarray(fe, float)
    pw = o.get('width', g * 2.3); tl = o.get('toe_len', g * 2.2); claw = o.get('claw', g * .5)
    # metacarpal pad (palm) behind/under the toes
    mc = V(ground[0] - tl * .05, g * .35, ground[2])
    b.add(f_ell(mc, (1, 0, 0), (0, 1, 0), (g * .7, g * .45, pw * .6)), k=g * .25, mirror=True)
    b.group(loft([fe + V(0, g * .1, 0), mc + V(0, g * .3, 0)], [(g * .4, g * .48, 0, 2.3), (g * .45, pw * .55, 0, 2.3)], up=(1, 0, 0), sub=2), 0, g * .2, mirror=True)
    toes = [(-.62, .82, .55), (-.2, 1.0, .7), (.2, 1.0, .7), (.62, .82, .55)]  # lateral pos, length, height
    for zf, lf, hf in toes:
        zc = ground[2] + zf * pw * .62
        root = V(mc[0] + g * .25, g * .55 * hf + g * .15, zc)
        knuckle = V(mc[0] + tl * .65 * lf, g * .55 * hf, zc + zf * g * .05)
        tipp = V(mc[0] + tl * lf, g * .22, zc + zf * g * .06)
        b.group(loft([root, knuckle, tipp], [(g * .36, g * .32, 0, 2.2), (g * .38, g * .32, 0, 2.2), (g * .28, g * .26, -.03 * g, 2.2)], up=(0, 1, 0), sub=3), 0, g * .12)
        # digital pad under toe
        b.add(f_ell(V(tipp[0] - g * .15, g * .2, zc), (1, 0, 0), (0, 1, 0), (g * .34, g * .22, g * .28)), k=g * .08)
        # claw: short downward-curving cone from toe tip
        c0 = tipp + V(g * .05, g * .03, 0); c1 = c0 + V(claw * .8, -claw * .55, 0)
        b.add(f_seg(c0, c1, (g * .1, g * .08, 0, 2), (g * .012, g * .012, 0, 2), up=(0, 1, 0)), k=g * .04)
    # the 4 toes were placed for the LEFT foot centre only (unmirrored); mirror copy for the right foot
    _mirror_last(b, 4 * 3)

def _mirror_last(b, n):
    for kind, fn, lo, hi, k, m in b.ops[-n:]:
        lo2 = lo.copy(); hi2 = hi.copy(); lo2[2], hi2[2] = -hi[2], -lo[2]
        b.ops.append((kind, (lambda f: (lambda X, Y, Z: f(X, Y, -Z)))(fn), lo2, hi2, k, False))

# ------------------------------------------------------------------ TAIL / WING / FIN / SHELL
def tail(b, pts, r0, r1=None, k=0.04, plume=None, mirror_plume=True):
    """tapered dock along pts; plume=dict(length,count,thick,spread) adds fur/hair clumps
    streaming from the dock (horse tail / wolf brush)."""
    r1 = r0 * .3 if r1 is None else r1
    rs = np.linspace(r0, r1, len(pts))
    b.group(loft(pts, [(r, r * .9, 0, 2) for r in rs], up=(0, 1, 0), sub=4), 0, k)
    if plume:
        P = catmull(pts, 4); n = plume['count']; rng = np.random.RandomState(plume.get('seed', 3))
        for i in range(n):
            t = plume.get('start', .15) + (1 - plume.get('start', .15)) * i / max(n - 1, 1)
            j = t * (len(P) - 1); i0 = min(int(j), len(P) - 2); p = lerp(P[i0], P[i0 + 1], j - i0)
            ax = nrm(P[i0 + 1] - P[i0]); a = rng.uniform(0, 2 * np.pi)
            rad = r0 + (r1 - r0) * t
            off = V(0, np.cos(a), np.sin(a)) * rad * .6
            L = plume['length'] * (0.7 + 0.5 * rng.rand()) * plume.get('taper', lambda t: 1)(t)
            g = plume.get('gravity', 0.6); sp = plume.get('spread', .25)
            dirn = nrm(ax * (1 - g) + V(0, -1, 0) * g + off / (rad + 1e-9) * sp)
            ctrl = p + off + nrm(ax + off / (rad + 1e-9) * sp) * L * .4
            tip = p + off + dirn * L
            b.group(strand(p + off, ctrl, tip, plume['thick'], flat=.6, up=ax), 0, plume['thick'] * 1.5)

def wing(b, shoulder, span, chord, sweep=10, n_prim=10, n_sec=12, thick=0.012, k=0.02):
    """layered feathered wing (mirrored): bony leading edge + coverts + overlapping blades."""
    sh = np.asarray(shoulder, float); sw = np.radians(sweep)
    el = sh + V(-span * .05, span * .03, span * .3); wr = el + V(span * .05, -span * .02, span * .3); tp = wr + V(-span * .1, -span * .05, span * .38)
    b.group(loft([sh, el, wr, tp], [(thick * 3, thick * 4, 0, 2), (thick * 2.5, thick * 3, 0, 2), (thick * 2, thick * 2, 0, 2), (thick, thick, 0, 2)], up=(0, 1, 0)), 0, k, mirror=True)
    for i in range(n_sec + n_prim):
        t = i / (n_sec + n_prim - 1); root = catmull([sh, el, wr, tp], 6)[int(t * 18)]
        L = chord * (0.8 + 0.6 * t)
        tip = root + V(-L * np.cos(sw + t * .9), -thick * 2, L * np.sin(sw + t * .9) * .5)
        b.group(loft([root, lerp(root, tip, .5) + V(0, thick, 0), tip], [(thick * .5, chord * .1, 0, 2), (thick * .4, chord * .12, 0, 2), (thick * .2, chord * .03, 0, 2)], up=(0, 1, 0), sub=3), 0, thick, mirror=True)

def fin(b, root_a, root_b, tip, thick, k=0.02, mirror=False):
    """tapered foil: thick rounded leading edge root_a, thin trailing edge root_b, pointed tip"""
    ra, rb, tp = [np.asarray(p, float) for p in (root_a, root_b, tip)]
    n = 6
    for i in range(n):
        t = i / (n - 1); a = lerp(ra, tp, t); c = lerp(rb, tp, t ** .7)
        th = thick * (1 - t * .85)
        b.group(loft([a, lerp(a, c, .3), c], [(th, th, 0, 2), (th * .8, th, 0, 2), (th * .1, th * .1, 0, 2)], up=(0, 1, 0), sub=2), 0, th, mirror=mirror)

def shell(b, c, L, W, H, scutes=(5, 4), groove=0.006, k=0.02):
    """domed carapace with marginal rim and shallow seam grooves between scutes"""
    c = np.asarray(c, float)
    b.add(f_ell(c, (1, 0, 0), (0, 1, 0), (L, H, W)), k=k)
    b.add(f_ell(c + V(0, -H * .1, 0), (1, 0, 0), (0, 1, 0), (L * 1.04, H * .2, W * 1.04)), k=k * 2)
    nx, nz = scutes
    for i in range(1, nx):
        x = c[0] - L + 2 * L * i / nx
        b.sub(f_box(V(x, c[1] + H * .5, 0), (groove, H, W * 1.1), (1, 0, 0), (0, 1, 0)), k=groove)
    for j in range(1, nz):
        z = -W + 2 * W * j / nz
        b.sub(f_box(V(c[0], c[1] + H * .5, z), (L * 1.1, H, groove), (1, 0, 0), (0, 1, 0)), k=groove)


# ------------------------------------------------------------------ SURFACE TOOLS (iteration 2)
def groove(b, pts, depth, width, normal=(0, 0, 1), k=None, mirror=True):
    """soft muscle-separation / jugular groove along a curve lying on the surface.
    The cutter is a flat lens (depth x width) tapering to nothing at both ends, so even if the
    curve is off the surface the cut can never go deeper than ~depth; blended wide for softness."""
    nrm_ = nrm(normal); P = [np.asarray(p, float) for p in pts]; n = len(P)
    secs = [(depth * (.25 + .75 * np.sin(np.pi * (i + .5) / n)), width * (.3 + .7 * np.sin(np.pi * (i + .5) / n)), 0, 2) for i in range(n)]
    secs[0] = (1e-3, 1e-3, 0, 2); secs[-1] = (1e-3, 1e-3, 0, 2)
    for pr in loft(P, secs, up=nrm_, sub=3):
        b.sub(pr, k=max(k or 0, width * 1.2), mirror=mirror)   # wide, shallow, soft

def cord(b, pts, height, width, k=None, mirror=True, up=(0, 0, 1)):
    """raised muscle cord / tendon ridge along a curve (trapezius, sternocephalic, flexor tendon)"""
    P = [np.asarray(p, float) for p in pts]; n = len(P)
    secs = [(height * np.sin(np.pi * (i + .5) / n) + 1e-3, width, 0, 2) for i in range(n)]
    b.group(loft(P, secs, up=up, sub=3), 0, k or width * .8, mirror=mirror)

def flatten(b, p0, normal, radius, k=0.01, mirror=True, axis=(1, 0, 0)):
    """hard plane: shave everything beyond the plane (p0, outward normal) inside an ellipsoid of
    radius=(along axis, along up, along normal) - cheek plates, nasal plane, hoof wall facets"""
    p0 = np.asarray(p0, float); n = nrm(normal); pl = f_plane_cut(p0, n)
    ax = nrm(np.asarray(axis, float) - n * np.dot(axis, n)); up = np.cross(n, ax); ra, ru = radius[0], radius[1]
    def fn(X, Y, Z):   # beyond plane AND inside elliptic cylinder around the normal (whole cap removed)
        x, y = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1] + (Z - p0[2]) * ax[2], (X - p0[0]) * up[0] + (Y - p0[1]) * up[1] + (Z - p0[2]) * up[2]
        e = (np.sqrt((x / ra) ** 2 + (y / ru) ** 2) - 1) * min(ra, ru)
        return np.maximum(-pl(X, Y, Z), e)
    R = max(ra, ru) + 3 * radius[2] + 0.1
    b.sub((fn, p0 - R, p0 + R), k=max(k, radius[2] * .8), mirror=mirror)

def bump(b, c, r, axis=(1, 0, 0), up=(0, 1, 0), k=None, mirror=True):
    """bony landmark / muscle head: oriented ellipsoid blended tight (point of shoulder, stifle)"""
    b.add(f_ell(c, axis, up, r), k=k or min(r) * .6, mirror=mirror)

def ruff(b, base, head, radius, count=14, length=None, k=None, seed=5):
    """neck ruff: solid fur collar (thick loft) with short downward-back tufts blended in heavily
    so it reads as a volume, not strands"""
    base = np.asarray(base, float); head = np.asarray(head, float); length = length or radius * .6
    b.group(loft([base, lerp(base, head, .55), head], [(radius, radius * .9, -radius * .1, 2.2), (radius * .95, radius * .85, -radius * .15, 2.2), (radius * .6, radius * .6, 0, 2.2)], up=(0, 1, 0), sub=4), 0, k or radius * .3)
    rng = np.random.RandomState(seed)
    for i in range(count):
        t = rng.uniform(.1, .8); a = rng.uniform(-2.4, 2.4)
        c = lerp(base, head, t); o = V(0, -np.cos(a), np.sin(a)) * radius * .8
        tip = c + o * 1.0 + nrm(o) * length + V(-length * .6, -length * .3, 0)
        b.add(f_ell(lerp(c + o * .6, tip, .45), tip - c - o * .6, (1, 0, 0), (np.linalg.norm(tip - c - o * .6) * .55, radius * .3, radius * .22)), k=radius * .35)


# ------------------------------------------------------------------ SCULPT MASSES (iteration 4)
def tail_locks(b, pts, r0, length, n=4, spread=0.35, k=None, seed=2):
    """volumetric horse tail: thick dock + n thick tapering locks hanging from it, merged with
    generous smooth-min so the tail reads as one hair mass with soft separations."""
    P = [np.asarray(p, float) for p in pts]
    b.group(loft(P, [(r0, r0 * .9), (r0 * .85, r0 * .8), (r0 * .7, r0 * .65)][:len(P)] + [(r0 * .6, r0 * .55)] * max(0, len(P) - 3), sub=4), 0, r0 * .6)
    rng = np.random.RandomState(seed); root = P[-1]; ax = nrm(P[-1] - P[-2]); locks = []
    for i in range(n):
        zf = (i - (n - 1) / 2) / max(n - 1, 1)
        top = lerp(P[-2], P[-1], .3 + .2 * rng.rand()) + V(-r0 * .2, 0, zf * r0 * 1.0)
        L = length * (0.85 + 0.25 * rng.rand())
        mid = top + V(-L * (.12 + .05 * rng.rand()), -L * .5, zf * r0 * spread * 3)
        tip = top + V(-L * (.10 + .1 * rng.rand()), -L, zf * r0 * spread * 4.5)
        rr = r0 * (1.05 - .15 * abs(zf))
        locks += loft([top, mid, tip], [(rr * 1.0, rr * .8), (rr * .9, rr * .75), (rr * .25, rr * .2)], up=(1, 0, 0), sub=4)
    b.group(_Prims(locks), k or r0 * .55, r0 * .8)

def crest_mane(b, base, head, base_dw, head_dw, crest, thick, width, k=None):
    """solid mane: broad crest mass riding the neck topline (sits ON the surface, blends wide)"""
    base = np.asarray(base, float); head = np.asarray(head, float)
    P = catmull([base, lerp(base, head, .5), head], 4); pts = []; secs = []
    for i in range(1, len(P) - 1):
        t = i / (len(P) - 1); ax = nrm(P[i + 1] - P[i - 1]); nup = nrm(np.cross(V(0, 0, 1), ax))
        dd = lerp(base_dw, head_dw, t)[0] + crest * np.sin(np.pi * t)
        env = np.sin(np.pi * min(1, t * 1.15)) ** .5
        pts.append(P[i] + nup * (dd - thick * .3)); secs.append((thick * env + 1e-3, width * (.6 + .4 * env)))
    b.group(loft(pts, secs, up=(0, 1, 0), sub=3), 0, k or width * .7)

def mass(b, c, axis, r, k=None, up=(0, 1, 0), mirror=True):
    """generic soft muscle mass (sculpt clay blob)"""
    b.add(f_ell(c, axis, up, r), k=k or min(r) * .9, mirror=mirror)


# ------------------------------------------------------------------ ROUND 5: landmark export
import json as _json, os as _os
def export(b, name, pts, values=None, n=330, target=78000, smooth=10, bl_len=None):
    """mesh to C:/lab5/<name>.obj and write <name>_landmarks.json.  Built with head toward +x; the
    exported mesh + landmarks are mirrored to the delivery convention (head toward -x)."""
    here = _os.path.dirname(_os.path.abspath(__file__)); path = _os.path.join(here, name + '.obj')
    nt = b.mesh(path, n=n, target=target, smooth=smooth)
    out = []
    for line in open(path):
        p = line.split()
        if p and p[0] == 'v': out.append('v %.4f %s %s\n' % (-float(p[1]), p[2], p[3]))
        elif p and p[0] == 'f': out.append('f %s %s %s\n' % (p[1], p[3], p[2]))
    open(path, 'w').write(''.join(out))
    P = {k: [-float(v[0])] + [float(x) for x in np.asarray(v, float)[1:]] for k, v in pts.items()}
    d = {'animal': name, 'points': P, 'values': values or {}}
    if bl_len: d['bl_len'] = bl_len
    _json.dump(d, open(_os.path.join(here, name + '_landmarks.json'), 'w'), indent=1)
    return nt


# ------------------------------------------------------------------ ROUND 5: generic parts for non-quadruped / pillar builds
def limb(b, pts, rs, k=0.03, mirror=True, flat=1.0, up=(1, 0, 0), sub=4, ex=2.0):
    """tube along pts with radius list rs (depth=r along 'up', width=r*flat)"""
    b.group(loft(pts, [(r, r * flat, 0, ex) for r in rs], up=up, sub=sub), 0, k, mirror=mirror)

def blob(b, c, r, axis=(1, 0, 0), up=(0, 1, 0), k=0.02, mirror=False, sub=False):
    (b.sub if sub else b.add)(f_ell(np.asarray(c, float), axis, up, r), k=k, mirror=mirror)

def plate(b, c, half, axis, up, r=0.004, k=0.01, mirror=False):
    b.add(f_box(np.asarray(c, float), half, axis, up, r=r), k=k, mirror=mirror)

def pillar_foot(b, c, rx, rz, h, nails=5, k=0.02, mirror=True):
    """elephant / tortoise column foot: slightly flared cylinder with toenails along the front rim"""
    c = np.asarray(c, float)
    b.group(loft([c + V(0, -0.02, 0), c + V(0, h * .5, 0), c + V(0, h, 0)], [(rx * 1.05, rz * 1.05, 0, 2.6), (rx, rz, 0, 2.3), (rx * .92, rz * .92, 0, 2.0)], up=(1, 0, 0), sub=2), 0, k, mirror=mirror)
    for i in range(nails):
        a = np.radians(-60 + 120 * i / max(nails - 1, 1))
        p = c + V(rx * np.cos(a) * 1.0, h * .22, rz * np.sin(a) * 1.0)
        b.add(f_ell(p, (1, 0, 0), (0, 1, 0), (rx * .14, h * .2, rz * .16)), k=0.004, mirror=mirror)

def f_tri(a, bpt, tip, thick, edge=0.15):
    """thin triangular slab (fin / feather blade): exact 2D triangle distance in its plane, thickness
    tapering from 'thick' at the root edge (a-bpt) to thick*edge at the tip and along the trailing edge"""
    a, bpt, tip = [np.asarray(p, float) for p in (a, bpt, tip)]
    e1 = nrm(bpt - a); n = nrm(np.cross(bpt - a, tip - a)); e2 = np.cross(n, e1)
    P2 = [np.array([np.dot(q - a, e1), np.dot(q - a, e2)]) for q in (a, bpt, tip)]
    def fn(X, Y, Z):
        x, y, z = X - a[0], Y - a[1], Z - a[2]
        u = x * e1[0] + y * e1[1] + z * e1[2]; v = x * e2[0] + y * e2[1] + z * e2[2]; h = x * n[0] + y * n[1] + z * n[2]
        d2 = None; sgn = None
        for i in range(3):
            p0, p1 = P2[i], P2[(i + 1) % 3]; ex, ey = p1 - p0
            wx, wy = u - p0[0], v - p0[1]
            t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
            dd = (wx - ex * t) ** 2 + (wy - ey * t) ** 2
            cr = ex * wy - ey * wx
            d2 = dd if d2 is None else np.minimum(d2, dd)
            s_ = cr > 0; sgn = s_ if sgn is None else (sgn & s_) if True else None
        # inside if all cross products have the same sign as the triangle orientation
        orient = (P2[1][0] - P2[0][0]) * (P2[2][1] - P2[0][1]) - (P2[1][1] - P2[0][1]) * (P2[2][0] - P2[0][0]) > 0
        inside = sgn if orient else None
        if inside is None:
            inside = np.ones_like(d2, bool)
            for i in range(3):
                p0, p1 = P2[i], P2[(i + 1) % 3]; inside &= ((p1[0] - p0[0]) * (v - p0[1]) - (p1[1] - p0[1]) * (u - p0[0])) < 0
        dtri = np.sqrt(d2) * np.where(inside, -1, 1)
        tv = np.clip(v / (P2[2][1] + 1e-9), 0, 1)
        th = thick * (1 - (1 - edge) * tv)
        dh = np.abs(h) - th
        return np.minimum(np.maximum(dtri, dh), 0) + np.sqrt(np.maximum(dtri, 0) ** 2 + np.maximum(dh, 0) ** 2)
    lo = np.min([a, bpt, tip], 0) - thick * 2; hi = np.max([a, bpt, tip], 0) + thick * 2
    return fn, lo, hi

def foil(b, a, bpt, tip, thick, k=None, mirror=False, n=None):
    b.add(f_tri(a, bpt, tip, thick), k=k if k is not None else thick * 2, mirror=mirror)
