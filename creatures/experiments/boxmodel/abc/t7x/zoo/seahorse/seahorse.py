import os, sys, math, json, bisect
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# seahorse (t7x zoo, workflow v2): no legs, so ONE spine loft of 10-vertex half rings IS the body: tube snout tip ->
# head -> arched neck -> ridged trunk -> tail -> a logarithmic curl ending in the tip. Each half ring is a RUNG in the
# side plane: a dorsal point D and a ventral point V (both read off reference/side.png) and a half width W (front.png).
# The ring plane holds X and the rung, so the side outline is matched by construction; at the head-neck bend the
# dorsal ends sweep round the occiput while the ventral ends crawl along the jaw and throat (no crossing rings).
# Armour ridges are ring STEPS (a groove ring 7% in, then the crest ring), never noise. Fins are face regions of the
# loft extruded as closed slabs: the dorsal fin from the back-seam faces (koi grow_seam), a pectoral fin per side from
# a 1 x 4 face window of the trunk side, the coronet spike from the crown seam faces.
META = dict(creature='seahorse', model='opus', stage1_tris=(1500, 6000), total_tris=(1700, 6500),
            closeups=[('head', (0.0, -0.04, 0.42), 0.13, 'hero'),
                      ('fins', (0.03, 0.08, 0.255), 0.12, 'back34'),
                      ('tail curl', (0.0, 0.03, 0.07), 0.14, 'az090')])


def resample(prof, splits):
    out = [prof[0]]
    for (a, b), n in zip(zip(prof, prof[1:]), splits):
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return out


# half-ring profiles, dorsal seam -> ventral seam: (fx of W, fh of the half rung)
SNOUT = [(0, 1), (0.4, 0.92), (0.72, 0.72), (0.93, 0.4), (1.0, 0.04), (0.96, -0.3), (0.82, -0.6), (0.58, -0.84),
         (0.3, -0.96), (0, -1)]
HEADP = [(0, 1), (0.42, 0.93), (0.76, 0.72), (0.95, 0.4), (1.0, 0.08), (0.97, -0.22), (0.86, -0.5), (0.64, -0.76),
         (0.33, -0.94), (0, -1)]
TRUNK = [(0, 1), (0.38, 0.86), (0.72, 0.6), (0.93, 0.27), (1.0, -0.04), (0.95, -0.35), (0.8, -0.62), (0.55, -0.83),
         (0.27, -0.96), (0, -1)]
TAILP = [(0, 1), (0.42, 0.88), (0.77, 0.6), (0.96, 0.26), (1.0, -0.06), (0.95, -0.38), (0.8, -0.64), (0.55, -0.85),
         (0.27, -0.97), (0, -1)]


def mixp(a, b, t):
    return [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t) for p, q in zip(a, b)]


# key rungs, snout tip -> tail start: (dorsal (y, z), ventral (y, z), half width W, profile)
KEYS = [
    ((-0.142, 0.367), (-0.142, 0.343), 0.0125, SNOUT),     # mouth flare
    ((-0.136, 0.366), (-0.136, 0.345), 0.0120, SNOUT),
    ((-0.128, 0.363), (-0.128, 0.347), 0.0085, SNOUT),     # behind the lip collar
    ((-0.112, 0.367), (-0.112, 0.350), 0.0090, SNOUT),
    ((-0.096, 0.373), (-0.096, 0.354), 0.0100, SNOUT),
    ((-0.082, 0.380), (-0.082, 0.358), 0.0110, SNOUT),
    ((-0.070, 0.389), (-0.070, 0.363), 0.0130, SNOUT),     # snout base
    ((-0.064, 0.405), (-0.064, 0.366), 0.0180, mixp(SNOUT, HEADP, 0.5)),   # the stop
    ((-0.058, 0.440), (-0.058, 0.368), 0.0270, HEADP),     # face front
    ((-0.046, 0.462), (-0.046, 0.370), 0.0330, HEADP),
    ((-0.030, 0.474), (-0.030, 0.372), 0.0360, HEADP),     # eye ring (eye at y -0.038, z 0.42)
    ((-0.012, 0.480), (-0.014, 0.374), 0.0370, HEADP),
    ((0.006, 0.481), (0.002, 0.376), 0.0360, HEADP),
    ((0.025, 0.476), (0.011, 0.377), 0.0340, HEADP),       # the bend: D round the occiput, V along the jaw
    ((0.045, 0.467), (0.016, 0.377), 0.0320, HEADP),
    ((0.064, 0.455), (0.019, 0.376), 0.0310, mixp(HEADP, TRUNK, 0.3)),
    ((0.080, 0.438), (0.021, 0.372), 0.0300, mixp(HEADP, TRUNK, 0.55)),
    ((0.092, 0.418), (0.020, 0.366), 0.0290, mixp(HEADP, TRUNK, 0.8)),     # R0: ridges start
    ((0.100, 0.397), (0.018, 0.358), 0.0290, TRUNK),
    ((0.103, 0.378), (0.014, 0.350), 0.0300, TRUNK),
    ((0.102, 0.360), (0.008, 0.343), 0.0320, TRUNK),       # neck
    ((0.099, 0.343), (-0.003, 0.333), 0.0360, TRUNK),
    ((0.096, 0.327), (-0.017, 0.320), 0.0420, TRUNK),
    ((0.092, 0.310), (-0.030, 0.306), 0.0470, TRUNK),
    ((0.088, 0.290), (-0.040, 0.288), 0.0500, TRUNK),      # trunk
    ((0.085, 0.270), (-0.045, 0.270), 0.0520, TRUNK),
    ((0.084, 0.250), (-0.046, 0.250), 0.0530, TRUNK),
    ((0.086, 0.230), (-0.044, 0.230), 0.0530, TRUNK),
    ((0.090, 0.210), (-0.038, 0.210), 0.0510, TRUNK),
    ((0.096, 0.190), (-0.029, 0.193), 0.0460, TRUNK),
    ((0.103, 0.172), (-0.016, 0.180), 0.0400, TRUNK),      # belly end
    ((0.110, 0.155), (0.002, 0.167), 0.0350, mixp(TRUNK, TAILP, 0.3)),
    ((0.116, 0.137), (0.028, 0.150), 0.0310, mixp(TRUNK, TAILP, 0.6)),
    ((0.120, 0.118), (0.050, 0.128), 0.0280, mixp(TRUNK, TAILP, 0.85)),
    ((0.122, 0.098), (0.066, 0.104), 0.0260, TAILP),
]
R0 = 17
# the curl: a logarithmic spiral round C0, theta clockwise from the +Y side (body side, going down then forward)
C0 = (0.012, 0.078)
R_0, R_K = 0.086, 0.71           # centreline radius at theta 0, ratio per 90 deg
D_0, D_K = 0.026, 0.75           # half rung
W_0, W_K = 0.024, 0.85           # half width
TH_END = 600.0
GROOVE = 0.93                    # a groove ring's scale
KNOB = 0.10                      # crest knob on the dorsal keel, x the half rung


def spiral(th):
    t = math.radians(th)
    r = R_0 * R_K ** (th / 90.0)
    return (C0[0] + r * math.cos(-t), C0[1] + r * math.sin(-t))


def spiral_key(th):
    a, b = spiral(th - 0.5), spiral(th + 0.5)
    ty, tz = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(ty, tz)
    ty, tz = ty / ln, tz / ln
    uy, uz = -tz, ty                                         # dorsal: the tangent turned +90 (the outside)
    c = spiral(th)
    d = D_0 * D_K ** (th / 90.0)
    w = W_0 * W_K ** (th / 90.0)
    return ((c[0] + uy * d, c[1] + uz * d), (c[0] - uy * d, c[1] - uz * d), w, TAILP)


ALLK = KEYS + [spiral_key(th) for th in range(0, int(TH_END) + 1, 15)]

# s1 r01: the rung ends are FITTED to the sheet's own side pixels (reference/side_mask.npz, opened 3 px so the knob
# tips do not count): along each hand rung line, D and V move to where the line leaves the sheet's silhouette
# (clamped to 0.75-1.35 of the hand length). Kept by hand: the mouth flare, the crown under the coronet spike and the
# back under the dorsal fin (the mask holds the fin and the spike there).
_SM = np.load(os.path.join(HERE, 'reference', 'side_mask.npz'))
_M, _Y0, _Z0, _PX = _SM['mask'], float(_SM['y0']), float(_SM['z0']), float(_SM['px'])


def _inside(y, z):
    c, r = int(round((y - _Y0) / _PX)), int(round((_Z0 - z) / _PX))
    return 0 <= r < _M.shape[0] and 0 <= c < _M.shape[1] and bool(_M[r, c])


def _exit(my, mz, uy, uz, t0):
    if not _inside(my, mz):
        return t0
    t = 0.0
    while t < 1.35 * t0 and _inside(my + uy * t, mz + uz * t):
        t += _PX * 0.25
    return min(max(t, 0.75 * t0), 1.35 * t0)


def fit(i, k):
    (dy, dz), (vy, vz), W, prof = k
    if i < 2:
        return k
    my, mz = (dy + vy) / 2, (dz + vz) / 2
    h = math.hypot(dy - vy, dz - vz) / 2
    uy, uz = (dy - vy) / (2 * h), (dz - vz) / (2 * h)
    keep_d = dz > 0.47 or (0.19 < dz < 0.32 and dy > 0.07)
    td = h if keep_d else _exit(my, mz, uy, uz, h)
    tv = _exit(my, mz, -uy, -uz, h)
    return ((my + uy * td, mz + uz * td), (my - uy * tv, mz - uz * tv), W, prof)


ALLK = [fit(i, k) for i, k in enumerate(ALLK)]


def _mid(k):
    return ((k[0][0] + k[1][0]) / 2, (k[0][1] + k[1][1]) / 2)


KS = [0.0]
for a, b in zip(ALLK, ALLK[1:]):
    ma, mb = _mid(a), _mid(b)
    KS.append(KS[-1] + math.hypot(mb[0] - ma[0], mb[1] - ma[1]))


def key_at(s):
    j = min(max(bisect.bisect_right(KS, s) - 1, 0), len(KS) - 2)
    t = (s - KS[j]) / (KS[j + 1] - KS[j])
    a, b = ALLK[j], ALLK[j + 1]
    L2 = lambda p, q: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    return (L2(a[0], b[0]), L2(a[1], b[1]), a[2] + (b[2] - a[2]) * t, mixp(a[3], b[3], t))


def half_rung(k):
    return math.hypot(k[0][0] - k[1][0], k[0][1] - k[1][1]) / 2


def seglen(h):
    xs, ys = [0.004, 0.015, 0.027, 0.065], [0.0075, 0.012, 0.017, 0.026]
    h = min(max(h, xs[0]), xs[-1])
    j = min(bisect.bisect_right(xs, h) - 1, len(xs) - 2)
    return ys[j] + (ys[j + 1] - ys[j]) * (h - xs[j]) / (xs[j + 1] - xs[j])


def no_knob(k):
    """The dorsal keel stays smooth under the dorsal fin."""
    return 0.19 < k[0][1] < 0.305 and k[0][0] > 0.06


def stations():
    """(name, rung, scale, knob) snout tip -> tail tip. Head keys as they are; from R0 on, 2 rings per armour
    segment: a groove ring 30% down the segment, the crest ring at its end."""
    out = [('K%02d' % i, ALLK[i], 1.0, 0.0) for i in range(R0)]
    s, s_end = KS[R0], KS[-1]
    out.append(('K%02d' % R0, ALLK[R0], 1.0, 0.0))
    n = 0
    while True:
        L = seglen(half_rung(key_at(s)))
        if s + L > s_end - 0.25 * L:
            break
        g, c = key_at(s + 0.3 * L), key_at(s + L)
        out.append(('G%02d' % n, g, GROOVE, 0.0))
        out.append(('C%02d' % n, c, 1.0, 0.0 if no_knob(c) else KNOB))
        s += L
        n += 1
    out.append(('GT', key_at(s + 0.3 * (s_end - s)), GROOVE, 0.0))
    out.append(('TIP', ALLK[-1], 1.0, 0.0))
    return out


ST = stations()


def ring_pts(k, f=1.0, knob=0.0):
    (dy, dz), (vy, vz), W, prof = k
    my, mz = (dy + vy) / 2, (dz + vz) / 2
    h = math.hypot(dy - vy, dz - vz) / 2
    uy, uz = (dy - vy) / (2 * h), (dz - vz) / (2 * h)
    pts = []
    for i, (fx, fh) in enumerate(prof):
        e = fh * h * f + (knob * h if i == 0 else 0.0)
        pts.append(Vector((fx * W * f, my + uy * e, mz + uz * e)))
    return pts


def P(nm):
    for n, k, f, kn in ST:
        if n == nm:
            return ring_pts(k, f, kn)


def SI(nm):
    return [s[0] for s in ST].index(nm)


# ---- the skeleton (side plane; .L on +X)
J = dict(spine=(0.0, 0.025, 0.20), chest=(0.0, 0.03, 0.29), neck=(0.0, 0.05, 0.36), head=(0.0, 0.04, 0.425),
         snout=(0.0, -0.065, 0.385), nose=(0.0, -0.142, 0.355),
         tail0=(0.0, 0.050, 0.170), tail1=(0.0, 0.075, 0.150),
         finL=(0.044, 0.050, 0.26), finTipL=(0.078, 0.078, 0.26),
         dorsal=(0.0, 0.088, 0.25), dorsalTip=(0.0, 0.14, 0.26))

# dorsal fin outer edge (y, z), bottom -> top, sheet side view
# review fix 1: the arc ends no longer overhang the root (were z 0.198 / 0.312 against a root of 0.205-0.295): the fin's
# bottom and top walls folded back over the back at 147 / 133 deg (the red under the fin in the tail0 crops)
DORSAL_ARC = [(0.118, 0.213), (0.136, 0.232), (0.143, 0.258), (0.138, 0.284), (0.123, 0.299)]
# review fix 2-3: the first level is squeezed 22% toward the root's middle height: the end walls flare off the back
DORSAL_LV = [(0.4, 0.0048, 0.22), (0.75, 0.0042, 0.06), (1.0, 0.0037, 0.0)]
# pectoral fin sections: (distance out, chord low, chord high (along the loft, from the root centre), half thickness)
# s1 r02: a fan, not a board: the chord narrows a little past the hug section, then spreads, and the outer
# sections bow out at mid chord (round, x sin(pi a)) so the edge is an arc
# s4 r03 (S1 re-opened): the root is a FLARE, not a pillar: the first section 5 mm out is 27% shorter and 38% thinner
# than the 4-face root window, so the wall leaves the body at ~45 deg (s4 r02: 114 deg knife folds at the top and
# bottom of the root where the walls stood straight up off the trunk)
# s4 r05: the flare wall 8 mm wide (was 5): at 5 mm its faces were 4 mm x 16 mm strips on the ridge-step zigzag
PEC_LV = [(0.008, -0.019, 0.019, 0.0068, 0.0), (0.0145, -0.017, 0.017, 0.0045, 0.001),
          (0.024, -0.030, 0.030, 0.0039, 0.004), (0.034, -0.040, 0.037, 0.0036, 0.008),
          (0.039, -0.037, 0.033, 0.0035, 0.011)]
PEC_OUT = (0.8, 0.6, 0.0)
OUT_BLEND = [0.0, 0.45, 1.0]
CORONET_LV = [(0.55, 0.0075), (1.0, 0.0036)]


def grow_seam(bm, faces, tgt, levels):
    """koi: extrude a seam face region level by level; walls left on x = 0 are removed (the mirror closes it)."""
    base = {v: v.co.copy() for f in faces for v in f.verts}
    roles = {v: v for v in base}
    zs = [b.z for b in base.values()]
    zm = (min(zs) + max(zs)) / 2
    for lv in levels:
        k, th, sq = (lv + (0.0,))[:3]
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        wall = [f for f in r['sides'] if all(abs(v.co.x) < 1e-6 for v in f.verts)]
        if wall:
            bmesh.ops.delete(bm, geom=wall, context='FACES')
        for v, b in new.items():
            b0 = base[b]
            ty, tz = tgt(b0)
            z = b0.z + (tz - b0.z) * k
            v.co = Vector((0.0 if abs(b0.x) < 1e-6 else th, b0.y + (ty - b0.y) * k, zm + (z - zm) * (1 - sq)))
        faces, roles = r['faces'], new
    return faces


def grow_fin(bm, faces, out, levels):
    """A paired fin from a 1 x n face window: each boundary vertex keeps (a, side): a = its place along the chord
    (the loft direction), side = which long edge. Each level is a closed blade section."""
    vs = {v for f in faces for v in f.verts}
    O = sum((v.co for v in vs), Vector()) / len(vs)
    nrm = sum((f.normal for f in faces), Vector()).normalized()
    top = max(vs, key=lambda v: v.co.z).co
    bot = min(vs, key=lambda v: v.co.z).co
    c = (top - bot).normalized()
    o = Vector(out).normalized()
    o = (o - c * o.dot(c)).normalized()
    n = o.cross(c).normalized()
    ref = {v: v.co.copy() for v in vs}
    roles = {v: (((v.co - O).dot(c)), 1 if (v.co - O).dot(n) > 0 else -1) for v in vs}
    lo = min(r[0] for r in roles.values()); hi = max(r[0] for r in roles.values())
    roles = {v: ((a - lo) / (hi - lo), sd) for v, (a, sd) in roles.items()}
    nrm = (nrm - c * nrm.dot(c)).normalized()
    for li, (dist, clo, chi, ht, rnd) in enumerate(levels):
        # s4 r04: the first sections leave along the root's own normal, then turn to the fan direction, so neither
        # long wall of the flare is seen edge-on (r03: a 1.9 mm seam strip along the rear wall)
        b = OUT_BLEND[min(li, len(OUT_BLEND) - 1)]
        ol = (nrm * (1 - b) + o * b).normalized()
        o_, n_ = ol, ol.cross(c).normalized()
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda q: (q.co - v.co).length)
            new[v] = roles[ov]
        for v, (a, sd) in new.items():
            v.co = O + o_ * (dist + rnd * math.sin(math.pi * a)) + c * (clo + (chi - clo) * a) + n_ * (ht * sd)
        faces, roles = r['faces'], new
    return faces


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, ring_pts(kk, f, kn)) for nm, kk, f, kn in ST]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, list(reversed(rings[0]))); cap(bm, rings[-1])
    recalc_normals(bm)
    zc = lambda f: f.calc_center_median().z
    # coronet: the two crown seam faces K10-K12 up into a spike
    crown = [spans[SI('K10')][0], spans[SI('K11')][0]]
    grow_seam(bm, crown, lambda b: (-0.012 + (b.y + 0.012) * 0.3, 0.503), CORONET_LV)
    # dorsal fin: the back seam faces with centre z 0.205-0.295 (trunk), fanned back to the sheet's arc
    dfaces = [spans[i][0] for i in range(SI('K%02d' % R0), len(spans))
              if 0.205 < zc(spans[i][0]) < 0.295 and spans[i][0].calc_center_median().y > 0.06]
    zr = [v.co.z for f in dfaces for v in f.verts]
    z0, z1 = min(zr), max(zr)

    def darc(b):
        t = min(max((b.z - z0) / (z1 - z0), 0.0), 1.0) * (len(DORSAL_ARC) - 1)
        j = min(int(t), len(DORSAL_ARC) - 2)
        u = t - j
        (y0, zz0), (y1, zz1) = DORSAL_ARC[j], DORSAL_ARC[j + 1]
        return (y0 + (y1 - y0) * u, zz0 + (zz1 - zz0) * u)
    grow_seam(bm, dfaces, darc, DORSAL_LV)
    # pectoral: a 1 x 4 window of the dorsolateral faces (profile edge 2-3) round z 0.26
    trunk = [i for i in range(SI('K%02d' % R0), len(spans)) if spans[i][2].calc_center_median().y > 0.0]
    i0 = min(trunk, key=lambda i: abs(spans[i][2].calc_center_median().z - 0.272))
    pfaces = [spans[i][2] for i in range(i0, i0 + 4)]
    grow_fin(bm, pfaces, PEC_OUT, PEC_LV)
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    """The head side face between rungs K09 and K10, profile vertices 4-5 (the cheek at eye height)."""
    a, b = P('K09'), P('K10')
    return (a[4] + a[5] + b[4] + b[5]) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.014 and abs(c.y - ec0.y) < 0.014
                                        and abs(c.z - ec0.z) < 0.014) or c.y < -0.139
    bm = edit(body)
    K08, K09, K10, K11 = (P(n) for n in ('K08', 'K09', 'K10', 'K11'))
    # brow: the orbital rim over the eye stands out 2.5 mm (rung vertices 3 of K09-K10), the eye face sits under it
    move([vert_near(bm, K09[3]), vert_near(bm, K10[3])], (0.0025, 0.0, 0.0015))
    # cheek: one flat plane under the eye (rung vertices 5-6 of K10-K12)
    flatten([vert_near(bm, q) for R in (K10, K11, P('K12')) for q in (R[5], R[6])])
    recalc_normals(bm)
    f = face_near(bm, ec0, n=(1, 0, 0))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the head side face K09-K10 (rung edge 4-5) under the brow'):
        inner = inset(bm, [f], 0.25, 0.0)
    move(list(inner[0].verts), -fn * 0.003)
    # mouth: the snout tip cap gets a rim loop and the mouth sinks into the tube
    cap_f = face_near(bm, (0.004, -0.142, 0.355), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'mouth: a loop inside the snout tip cap, the opening of the tube mouth'):
        mo = inset(bm, [cap_f], 0.3, 0.0)
        seam = [v for v in mo[0].verts if v.co.x < 0.0012]
        for v in seam:
            v.co.x = 0.0                                   # the inner seam vertices stay on the mirror plane
        flat = [f_ for f_ in bm.faces if all(abs(v.co.x) < 1e-7 for v in f_.verts)]
        bmesh.ops.delete(bm, geom=flat, context='FACES_ONLY')   # no face in x = 0 (the mirror closes it)
    move(list(mo[0].verts), (0.0, 0.006, 0.0))
    recalc_normals(bm)
    if os.environ.get('SH_DEBUG'):
        res = []
        for e in bm.edges:
            if len(e.link_faces) != 2:
                continue
            f1, f2 = e.link_faces
            a = math.degrees(f1.normal.angle(f2.normal))
            d = (f2.calc_center_median() - f1.calc_center_median()).dot(f1.normal)
            if d > 0 and a > 80:
                c = (e.verts[0].co + e.verts[1].co) / 2
                near = min(ST, key=lambda st: (Vector((0, *[(st[1][0][i] + st[1][1][i]) / 2 for i in (0, 1)])) - Vector((0, c.y, c.z))).length)[0]
                res.append((round(a, 1), tuple(round(x, 3) for x in c), near))
        for r in sorted(res, reverse=True)[:12]:
            say('CONCAVE', r)
    commit(body, bm)
    bm.free()


# ---- colour: warm orange armour, a pale-gold belly band below the ventrolateral loop (rung vertex 5), pale fins
# s3 r04: one step lighter and more saturated (the r03 renders read brown against the sheet's bright orange)
PAL = {'orange': '#f39a2e', 'belly': '#f9d47a', 'deep': '#e27c22', 'fin': '#fbdca2', 'iris': '#5a3418',
       'dark': '#1e140e'}
_MS = None


def _frame_of_faces():
    """Each station's centre M, dorsal unit u, half rung h and z, for the colour rule."""
    out = []
    for nm, kk, f, kn in ST:
        (dy, dz), (vy, vz), W, prof = kk
        h = math.hypot(dy - vy, dz - vz) / 2
        out.append((Vector((0, (dy + vy) / 2, (dz + vz) / 2)), Vector((0, (dy - vy) / (2 * h), (dz - vz) / (2 * h))),
                    h * f, nm))
    return out


def body_rule(c, n, i):
    global _MS
    if _MS is None:
        _MS = _frame_of_faces()
    x, y, z = abs(c.x), c.y, c.z
    if 0.19 < z < 0.33 and y > 0.097 and x < 0.006:
        return 'fin'                                                  # dorsal fin
    if 0.19 < z < 0.33 and y > 0.02 and x > 0.050:
        return 'fin'                                                  # pectoral fan
    cc = Vector((0, y, z))
    M, u, h, nm = min(_MS, key=lambda m: (m[0] - cc).length)
    fh = (cc - M).dot(u) / max(h, 1e-4)
    trunk = nm.startswith(('G', 'C')) and z > 0.16 and y < 0.11
    if trunk and fh < -0.33:
        return 'belly'
    if nm.startswith(('K0',)) and int(nm[1:]) < 7:
        return 'orange'                                               # snout
    if not trunk and (z < 0.16 or y > 0.11):
        return 'deep'                                                 # the tail and the curl: a step darker
    return 'orange'


def lens(bm, c, n, r, h, sides=8):
    """A small low-poly lens: back cone into the socket, iris ring, pupil fan (koi), 8 sided."""
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1))).normalized()
    w = n.cross(u)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * 2 * math.pi / sides for k_ in range(sides)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(sides):
        a, b = j, (j + 1) % sides
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


EYE_R, EYE_H = 0.008, 0.0062


def stage3(k, body):
    paint(body, PAL, body_rule)
    ec = eye_face_centre()
    bmb = edit(body)
    f = face_near(bmb, ec, n=(1, 0, 0))
    c, n = f.calc_center_median().copy(), f.normal.copy()
    n = n if n.x > 0 else -n
    bmb.free()
    n = (n + Vector((0, -0.6, 0.05))).normalized()                  # a little forward: the eye shows from the front
    bm = bmesh.new()
    lens(bm, c, n, EYE_R, EYE_H)
    eye = object_from_bm('eye', bm)
    paint(eye, {'iris': PAL['iris'], 'dark': PAL['dark']},
          lambda c_, n_, i: 'dark' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.0032 and n_.dot(n) > 0.5 else 'iris')
    return [eye]


# ---- stage 4: the seahorse floats (the whole model lifted LIFT off the floor), rigged in that pose
LIFT = 0.06


def _apply_mirror_piece(o):
    for m in list(o.modifiers):
        if m.type == 'MIRROR':
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
                bpy.ops.object.modifier_apply(modifier=m.name)


def _c(th):
    y, z = spiral(th)
    return (0.0, y, z + LIFT)


def stage4(k, body, pieces):
    apply_mirror(body)
    for p in pieces:
        _apply_mirror_piece(p)
    for o in [body] + pieces:
        for v in o.data.vertices:
            v.co.z += LIFT
        o.data.update()
    ec = eye_face_centre() + Vector((0, 0, LIFT))
    ecm = ec * Vector((-1, 1, 1))
    k.meta['keep_valleys'] = lambda c: min((c - ec).length, (c - ecm).length) < 0.02 or c.y < -0.139
    k.meta['closeups'] = [(n, (x, y, z + LIFT), r, v) for n, (x, y, z), r, v in META['closeups']]
    L = lambda p: (p[0], p[1], p[2] + LIFT)
    B = [('spine', L((0, 0.020, 0.175)), L((0, 0.025, 0.270)), None),
         ('chest', L((0, 0.025, 0.270)), L((0, 0.045, 0.345)), 'spine', True),
         ('neck', L((0, 0.045, 0.345)), L((0, 0.052, 0.400)), 'chest', True),
         ('head', L((0, 0.052, 0.400)), L((0, -0.030, 0.425)), 'neck', True),
         ('head_snout', L((0, -0.062, 0.385)), L((0, -0.142, 0.355)), 'head'),
         # a SHORT root bone pointing DOWN the tail: the curl lies ahead of it, so the probe radius is the root's
         ('tail0', L((0, 0.050, 0.175)), L((0, 0.058, 0.150)), 'spine'),
         ('tail1', L((0, 0.058, 0.150)), _c(0), 'tail0', True),
         ('tail2', _c(0), _c(90), 'tail1', True), ('tail3', _c(90), _c(180), 'tail2', True),
         ('tail4', _c(180), _c(270), 'tail3', True), ('tail5', _c(270), _c(390), 'tail4', True),
         ('tail6', _c(390), _c(560), 'tail5', True),
         ('fin.L', L(J['finL']), L(J['finTipL']), 'spine'),
         ('fin_dorsal', L(J['dorsal']), L(J['dorsalTip']), 'spine')]
    rig = armature(B)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            eb.align_roll(Vector((1, 0, 0)))        # local Z = lateral: rot Z bends in the side plane
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    tails = ['tail1', 'tail2', 'tail3', 'tail4', 'tail5', 'tail6']
    fin = lambda a: {'fin.L': (0, 0, a), 'fin.R': (0, 0, -a), 'fin_dorsal': (0, a * 0.6, 0)}
    # idle: a slow hover bob, the curl breathing, the fins fanning, a small head nod
    clip(rig, 'idle', {1: {}, 12: dict(fin(14), **{t: (0, 0, 2.5) for t in tails[1:]}, head=(0, 0, -2)),
                       24: dict(fin(-10), neck=(0, 0, 1.5)),
                       36: dict(fin(14), **{t: (0, 0, -2.5) for t in tails[1:]}, head=(0, 0, 2)), 48: {}},
         loc={1: {'spine': (0, 0, 0)}, 24: {'spine': (0, 0.012, 0)}, 48: {'spine': (0, 0, 0)}})
    # move: swim upright, fins beating fast, a forward lean, the tail curl tightening and opening
    keys = {}
    for f in (1, 5, 9, 13, 17, 21, 25):
        ph = 2 * math.pi * (f - 1) / 24
        a = 22 * math.sin(ph * 3)
        d = fin(round(a, 2))
        d.update({t: (0, 0, round(4 * math.sin(ph - j * 0.6), 2)) for j, t in enumerate(tails)})
        d['spine'] = (0, 0, round(-4 + 2 * math.sin(ph), 2))
        keys[f] = d
    keys[25] = keys[1]
    clip(rig, 'move', keys, loc={1: {'spine': (0, 0, 0)}, 13: {'spine': (0, 0.01, 0)}, 25: {'spine': (0, 0, 0)}})
    # attack: the pivot strike: the head cocks down, then flicks up and forward to snap prey, and settles
    clip(rig, 'attack', {1: {}, 8: {'neck': (0, 0, -8), 'head': (0, 0, -6), 'chest': (0, 0, -3)},
                         13: {'neck': (0, 0, 12), 'head': (0, 0, 14), 'head_snout': (0, 0, 4), 'chest': (0, 0, 4)},
                         18: {'neck': (0, 0, 8), 'head': (0, 0, 8)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
