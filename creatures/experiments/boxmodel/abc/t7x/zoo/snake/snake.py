import os, sys, math, json, bisect
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
from mathutils.kdtree import KDTree

# python (t7x zoo): no legs, so the spine loft IS the whole body (6-vertex half rings, tail tip -> nose).
# The kit's base is a mirrored half, so stages 1-3 are built straight (the sheet's side view is nearly straight:
# head raised, body flat on the ground) and stage 4 lays the finished snake into the sheet's plan-view S-curve
# (a deterministic bend along the traced centreline, mirror applied first), then rigs it in that pose.
META = dict(creature='snake', model='opus', stage1_tris=(400, 3200), total_tris=(1200, 6000))   # density pass 3: ~2x

# ---- the loft: (name, y, z bottom, z top, half-width W), read off reference/side.png (W from top.png)
# density pass 3: 8-vertex half rings (was 6): a brow vertex and a second cheek vertex on the head (cheek = one plane
# of vertices 3-4), a back and a shoulder vertex on the body for a round back; the belly stays one flat face
HEAD = [(0, 1), (0.7, 0.85), (0.9, 0.62), (1, 0.25), (0.99, -0.12), (0.92, -0.45), (0.6, -0.92), (0, -1)]
BODY = [(0, 1), (0.42, 0.97), (0.75, 0.81), (0.95, 0.44), (1, 0.0), (0.85, -0.6), (0.62, -0.96), (0, -1)]
SIDE, LOWER = 4, 5                   # BODY ring vertices bounding the lower-flank face (lip / belly loop)
CROWN, CHEEK = (0, 1), (3, 4)        # HEAD ring vertices: crown plane, cheek plane
EYE_A, EYE_B = 2, 3                  # HEAD ring vertices bounding the eye-socket face
# fix pass 1 (reviews): head 1.6x the neck, flat crown, blunt snout, raised 3 cm; thin neck, thick mid body,
# tail taper from ~60% of the length to the tip
# fix pass 2: head a wedge (H1-H5 W -12..15 %), crown edge in (0.78 -> 0.7), head 2 cm lower
HEADK = [('H0', -1.49, 0.265, 0.330, 0.040), ('H1', -1.45, 0.250, 0.348, 0.064), ('H2', -1.40, 0.238, 0.360, 0.084),
         ('H3', -1.34, 0.222, 0.366, 0.094), ('H4', -1.28, 0.205, 0.364, 0.099), ('H5', -1.22, 0.180, 0.352, 0.090),
         ('N1', -1.15, 0.138, 0.313, 0.066), ('N2', -1.08, 0.095, 0.262, 0.058), ('N3', -1.00, 0.052, 0.224, 0.060)]
# body / tail key table (y, z bottom, z top, W); rings in between are linear
BKEY = [(-0.92, 0.022, 0.207, 0.064), (-0.84, 0.006, 0.204, 0.072), (-0.68, 0.0, 0.214, 0.084), (-0.54, 0.028, 0.270, 0.092),
        (-0.40, 0.055, 0.302, 0.098), (-0.257, 0.060, 0.310, 0.102), (-0.115, 0.050, 0.298, 0.104), (-0.02, 0.016, 0.280, 0.104),
        (0.12, 0.0, 0.242, 0.102), (0.26, 0.0, 0.214, 0.098), (0.50, 0.0, 0.185, 0.088), (0.80, 0.0, 0.135, 0.072),
        (1.00, 0.0, 0.112, 0.058), (1.20, 0.0, 0.086, 0.042), (1.30, 0.0, 0.070, 0.033), (1.40, 0.0, 0.053, 0.024),
        (1.47, 0.0, 0.040, 0.016), (1.525, 0.0, 0.028, 0.010)]     # r2 arch kept; fix pass widens mid, tapers tail
# density pass 3: ~1.5x stations, densest over the neck / fore-body arch and the belly drop, finer tail taper
def _stations():
    ys, y = [], -0.92
    while y < 1.10 - 1e-6:
        ys.append(round(y, 4))
        y += 0.030 if y < -0.30 else (0.032 if y < 0.30 else 0.036)
    return ys + [1.10, 1.135, 1.17, 1.205, 1.24, 1.27, 1.30, 1.33, 1.355, 1.38, 1.405, 1.425, 1.445, 1.48]


BODY_Y = _stations()
HEAD_INS = [('H0a', -1.47), ('H1a', -1.425), ('H3a', -1.31), ('H4a', -1.25), ('H5a', -1.185),
            ('N1a', -1.115), ('N2a', -1.04), ('N3a', -0.96)]   # pass 9: neck inserts back (density kept), on the linear key lines
# mix pass 4 (review_poly2x): neck inserts N1a-N3a cut, head/neck/fore-neck rings linear between keys with no trace
# pull (before3 form) - the cubic + trace pull pinched and wobbled the neck behind the head
Y_LINEAR = -0.84


def _pchip(xs, ys, x):
    """Monotone cubic (Fritsch-Carlson) through the keys: smooth, no overshoot past the key values."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 3 * (h[i - 1] + h[i]) / ((2 * h[i] + h[i - 1]) / d[i - 1] + (h[i] + 2 * h[i - 1]) / d[i])
                  for i in range(1, n - 1)] + [d[-1]]
    i = min(max(bisect.bisect_right(xs, x) - 1, 0), n - 2)
    t = (x - xs[i]) / h[i]
    h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
    return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]


_SIDE = None


def _trace(y):
    """Top and bottom of the traced side outline (reference/side_mask.npz) at y, or None."""
    global _SIDE
    if _SIDE is None:
        s = np.load(os.path.join(HERE, 'reference', 'side_mask.npz'))
        _SIDE = (s['mask'], float(s['y0']), float(s['z0']), float(s['px']))
    m, y0, z0, px = _SIDE
    c = int(round((y - y0) / px))
    if not 0 <= c < m.shape[1]:
        return None
    r = np.where(m[:, c])[0]
    return (z0 - r.max() * px, z0 - r.min() * px) if len(r) else None


KEYS = [(y, zb, zt, W) for _, y, zb, zt, W in HEADK] + list(BKEY)
KEY_Y = {round(k[0], 4) for k in KEYS}


def _fit(y):
    """A station off the keys: exact on a key; between keys a monotone cubic through them, then pulled half way
    toward the traced side outline (at most 8 mm, so the review fixes - raised mid back, thin tail - survive)."""
    for k in KEYS:
        if abs(k[0] - y) < 1e-6:
            return list(k[1:])
    if y < Y_LINEAR:
        for a, b in zip(sorted(KEYS), sorted(KEYS)[1:]):
            if a[0] <= y <= b[0]:
                t = (y - a[0]) / (b[0] - a[0])
                return [p + (q - p) * t for p, q in zip(a[1:], b[1:])]
    xs = [k[0] for k in KEYS]
    zb, zt, W = (_pchip(xs, [k[j] for k in KEYS], y) for j in (1, 2, 3))
    tr = _trace(y)
    if tr is not None:
        zb += max(-0.008, min(0.008, (tr[0] - zb) * 0.5)) if y < 1.0 else 0.0
        zt += max(-0.008, min(0.008, (tr[1] - zt) * 0.5))
    zb = max(zb, 0.0)
    return [zb, zt, W]


def sections():
    out = []
    for i, y in enumerate(reversed(BODY_Y)):
        zb, zt, W = _fit(y)
        out.append(('B%02d' % (len(BODY_Y) - 1 - i), y, zb, zt, W, BODY))
    head = [(nm, y) for nm, y, *_ in HEADK] + HEAD_INS
    for nm, y in sorted(head, key=lambda s: -s[1]):
        zb, zt, W = _fit(y)
        out.append((nm, y, zb, zt, W, HEAD))
    return out                       # tail tip first, nose last


SECS = sections()
Y_NOSE, Y_TAIL = -1.49, 1.48


def sec_pts(y, zb, zt, W, prof):
    zc, T = (zb + zt) / 2, (zt - zb) / 2
    return [(fx * W, y, zc + fh * T) for fx, fh in prof]


def P(nm):
    for (n, y, zb, zt, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(y, zb, zt, W, p)]


SEC_Y = [s[1] for s in reversed(SECS)]             # nose -> tail, increasing y
SEC_ZC = [(s[2] + s[3]) / 2 for s in reversed(SECS)]
SEC_T = [(s[3] - s[2]) / 2 for s in reversed(SECS)]


def zc_t(y):
    """Section centre height and half height at y (between rings, linear)."""
    y = min(max(y, SEC_Y[0]), SEC_Y[-1])
    j = min(max(bisect.bisect_right(SEC_Y, y) - 1, 0), len(SEC_Y) - 2)
    t = (y - SEC_Y[j]) / (SEC_Y[j + 1] - SEC_Y[j])
    return SEC_ZC[j] + (SEC_ZC[j + 1] - SEC_ZC[j]) * t, SEC_T[j] + (SEC_T[j + 1] - SEC_T[j]) * t


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(y, zb, zt, W, p)) for (nm, y, zb, zt, W, p) in SECS]
    for i in range(len(rings) - 1):
        bridge(bm, rings[i], rings[i + 1])
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    """The upper-side face (ring vertices EYE_A-EYE_B) between H2 and H3: the eye socket."""
    H2, H3 = P('H2'), P('H3')
    return (H2[EYE_A] + H2[EYE_B] + H3[EYE_A] + H3[EYE_B]) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.035
                                        and abs(c.z - ec0.z) < 0.035)
    bm = edit(body)
    H0, H1, H2, H3, H4, H5 = (P(n) for n in ('H0', 'H1', 'H2', 'H3', 'H4', 'H5'))
    # deliberate head planes: one flat crown (from the snout to the back of the skull), one flat cheek per side
    # (density pass 3: the new head stations join both planes; the cheek plane is ring vertices 3-4)
    crown = [P(n) for n in ('H1', 'H1a', 'H2', 'H3', 'H3a', 'H4', 'H4a', 'H5')]
    flatten([vert_near(bm, H[j]) for H in crown for j in CROWN])
    flatten([vert_near(bm, H[j]) for H in [P(n) for n in ('H2', 'H3', 'H3a', 'H4', 'H4a', 'H5')] for j in CHEEK])
    # brow: the crown edge over the eye out a little, so the socket sits under a ledge
    move([vert_near(bm, H3[1]), vert_near(bm, H2[1])], (0.006, 0.0, 0.002))
    # snout: the flat end cap becomes a forward-down slanted pad (top edge forward, chin edge back)
    move([vert_near(bm, H0[0]), vert_near(bm, H0[1])], (0.0, -0.012, -0.004))
    move([vert_near(bm, H0[6]), vert_near(bm, H0[7])], (0.0, 0.010, 0.0))
    # tail tip (fix pass 2: rings cut at y 1.48): close the last ring to a 2 cm blunt tip
    T = P('B%02d' % (len(BODY_Y) - 1)); tc = sum(T, Vector()) / len(T)
    scale([vert_near(bm, q) for q in T], 0.7, pivot=(0.0, tc.y, tc.z))
    recalc_normals(bm)
    f = face_near(bm, ec0, n=(1, 0, 0.3))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the upper-side head face between H2 and H3'):
        inner = inset(bm, [f], 0.36, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.006)
    # the lip / belly line: one loop along the whole length through the lower-flank faces (ring vertices 2-3),
    # 60% of the way down; on the head it is the mouth line, on the body the border of the cream belly band
    Bm = P(min((s for s in SECS if s[5] is BODY), key=lambda s: abs(s[1] + 0.02))[0])
    e = edge_near(bm, (Bm[SIDE] + Bm[LOWER]) / 2)
    with k.topo(bm, 'loop', 'lip and belly line: a longitudinal loop through the lower-flank faces, nose to tail tip'):
        loopcut(bm, e, t=0.6, near=vert_near(bm, Bm[SIDE]))
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


# ---- colour: tan ground, dark-brown blotches staggered top / side, cream belly band and lips, dark crown
PAL = {'tan': '#b8975f', 'brown': '#6e5233', 'cream': '#e3d3a8', 'amber': '#e09a20', 'black': '#161210'}


def body_rule(c, n, i):
    y = c.y
    zc, T = zc_t(y)
    h = (c.z - zc) / max(T, 1e-4)
    if h < -0.2:
        return 'cream'                                     # below the lip / belly loop
    if y < -1.20:
        if h > 0.85 and y > -1.43:
            return 'brown'                                 # the dark crown, as in the ref's top view
        return 'tan'
    if y > 1.42:
        return 'brown'                                     # dark tail tip
    # fix pass 2: diamond saddles: wide on the crown row, a narrow point on the flank, side blotches between
    u = ((y + 1.20) / 0.30) % 1.0
    dc = abs(u - 0.5) * 2                                  # 0 at a saddle centre, 1 half way between saddles
    # pass 9: one continuous diamond per saddle (half width falls with height), so the denser rows step
    # the diamond edge instead of breaking it into square blocks
    if h > 0.0:
        if dc < 0.10 + 0.34 * min(1.0, h / 0.9):
            return 'brown'                                 # saddle: wide on the crown, a point low on the flank
        if h < 0.6 and dc > 0.86 - 0.3 * (0.6 - h):
            return 'brown'                                 # side blotch, staggered half a period
    return 'tan'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A low-poly eye: back cone, iris ring, pupil fan."""
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


def tongue(bm):
    """One prong of the forked tongue (the mirror makes the fork): sunk in the snout, out past the nose pad."""
    rows = [(0.0045, -1.44, 0.282, 0.0025, 0.002), (0.0050, -1.475, 0.280, 0.0024, 0.0018),
            (0.0060, -1.51, 0.276, 0.0020, 0.0015), (0.0110, -1.53, 0.272, 0.0012, 0.001)]   # fix pass 2: head -2 cm   # fix pass: head +3 cm
    R = [[bm.verts.new((x + sx * hw, y, z + sz * hh)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
         for x, y, z, hw, hh in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def stage3(k, body):
    paint(body, PAL, body_rule)
    # eye: a small amber lens with a black pupil, proud of the socket floor
    ec = eye_face_centre()
    bmb = edit(body)
    f = face_near(bmb, ec + Vector((-0.006, 0, 0)), n=(1, 0, 0.3))
    c, n = f.calc_center_median().copy(), f.normal.copy()
    n = n if n.x > 0 else -n
    bmb.free()
    bm = bmesh.new()
    lens(bm, c, n, 0.012, 0.007)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'black': PAL['black']},
          lambda c_, n_, i: 'black' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.005 and n_.dot(n) > 0.5 else 'amber')
    bm = bmesh.new()
    tongue(bm)
    tg = object_from_bm('tongue', bm)
    paint(tg, {'black': PAL['black']}, lambda c_, n_, i: 'black')
    return [eye, tg]


# ---- stage 4: the sheet's plan-view S-curve (reference/top.png centreline, sheet pixels (column, row))
PLAN_PX = [(664, 608), (688, 609), (712, 608), (736, 608), (760, 608), (784, 611), (808, 612), (832, 610), (856, 607),
           (880, 606), (904, 607), (928, 611), (940, 616), (952, 623), (964, 633), (976, 644), (988, 660), (1000, 678),
           (1012, 695), (1024, 711), (1036, 728), (1048, 745), (1060, 762), (1072, 776), (1084, 788), (1096, 796),
           (1108, 803), (1120, 807), (1132, 809), (1144, 811), (1156, 810), (1168, 809), (1180, 808), (1192, 805),
           (1204, 800), (1216, 794), (1228, 787), (1240, 781), (1252, 775), (1264, 767), (1276, 759), (1288, 751),
           (1300, 744), (1312, 738), (1324, 731), (1336, 726), (1348, 721), (1360, 717), (1372, 716), (1384, 715),
           (1396, 715), (1408, 716), (1420, 719), (1432, 723), (1444, 728), (1456, 735), (1468, 746), (1480, 759),
           (1490, 776), (1497, 796), (1501, 815), (1503, 830)]
PX_M = 0.36 / 114                     # the sheet's metres per pixel (side figure height 0.36 m)


class Curve:
    """The plan centreline, nose -> tail, smoothed and resampled by arc length."""

    def __init__(self):
        P_ = np.array([((r - 707) * PX_M, (c - 1075) * PX_M) for c, r in PLAN_PX])      # (x, y)
        for _ in range(3):
            Q = P_.copy(); Q[1:-1] = (P_[:-2] + 2 * P_[1:-1] + P_[2:]) / 4; P_ = Q
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P_, axis=0), axis=1))]
        self.L = d[-1]
        s = np.linspace(0, self.L, 600)
        self.P = np.c_[np.interp(s, d, P_[:, 0]), np.interp(s, d, P_[:, 1])]
        T = np.gradient(self.P, axis=0)
        self.T = T / np.linalg.norm(T, axis=1)[:, None]
        self.s = s

    def at(self, s):
        """Point and unit tangent at arc s (extrapolated straight past either end)."""
        if s <= 0:
            return self.P[0] + self.T[0] * s, self.T[0]
        if s >= self.L:
            return self.P[-1] + self.T[-1] * (s - self.L), self.T[-1]
        i = min(int(s / self.L * (len(self.s) - 1)), len(self.s) - 2)
        t = (s - self.s[i]) / (self.s[i + 1] - self.s[i])
        p = self.P[i] * (1 - t) + self.P[i + 1] * t
        tg = self.T[i] * (1 - t) + self.T[i + 1] * t
        return p, tg / np.linalg.norm(tg)


CURVE = None


def bend(co):
    """A point of the straight snake -> the posed snake: the straight y runs along the plan centreline
    (scaled to its length), x goes out along the curve's left normal, z stays."""
    s = (co.y - Y_NOSE) / (Y_TAIL - Y_NOSE) * CURVE.L
    p, t = CURVE.at(s)
    nx, ny = t[1], -t[0]                 # (x, y) left normal: the straight snake's +x
    return Vector((p[0] + co.x * nx, p[1] + co.x * ny, co.z))


def _apply_mirror_piece(o):
    for m in list(o.modifiers):
        if m.type == 'MIRROR':
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
                bpy.ops.object.modifier_apply(modifier=m.name)


def _raster_iou(tris2d, mask, u0, v0, px, vsign):
    """IoU of projected triangles against a reference mask whose pixel (r, c) centre is (u0 + c px, v0 + vsign r px)."""
    H, W = mask.shape
    m = np.zeros_like(mask)
    for a, b, c in tris2d:
        lo, hi = np.minimum(np.minimum(a, b), c), np.maximum(np.maximum(a, b), c)
        c0, c1 = int(max(0, (lo[0] - u0) / px)), int(min(W - 1, (hi[0] - u0) / px + 1))
        if vsign > 0:
            r0, r1 = int(max(0, (lo[1] - v0) / px)), int(min(H - 1, (hi[1] - v0) / px + 1))
        else:
            r0, r1 = int(max(0, (v0 - hi[1]) / px)), int(min(H - 1, (v0 - lo[1]) / px + 1))
        if c1 < c0 or r1 < r0:
            continue
        U, V = np.meshgrid(u0 + np.arange(c0, c1 + 1) * px, v0 + vsign * np.arange(r0, r1 + 1) * px)
        cr = lambda p, q: (q[0] - p[0]) * (V - p[1]) - (q[1] - p[1]) * (U - p[0])
        d1, d2, d3 = cr(a, b), cr(b, c), cr(c, a)
        m[r0:r1 + 1, c0:c1 + 1] |= ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | ((d1 <= 0) & (d2 <= 0) & (d3 <= 0))
    return float((m & mask).sum() / max(1, (m | mask).sum()))


def posed_checks(k, objs, body, straight_y):
    """Plan-view and side-view IoU of the posed snake against the unsymmetrised reference masks, and the
    self-contact check (no two body parts more than 0.6 m apart along the spine come within 1 cm)."""
    tris = []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        V_ = [o.matrix_world @ v.co for v in me.vertices]
        tris += [[V_[i] for i in t.vertices] for t in me.loop_triangles]
    top = np.load(k.path('reference', 'top_mask.npz'))
    side = np.load(k.path('reference', 'side_mask.npz'))
    t_top = [[np.array((p.y, p.x)) for p in t] for t in tris]
    t_side = [[np.array((p.y, p.z)) for p in t] for t in tris]
    iou_top = _raster_iou(t_top, top['mask'], float(top['y0']), float(top['x0']), float(top['px']), 1)
    iou_side = _raster_iou(t_side, side['mask'], float(side['y0']), float(side['z0']), float(side['px']), -1)
    me = body.data
    kd = KDTree(len(me.vertices))
    for v in me.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    gap = 9.0
    for v in me.vertices:
        for co, j, d in kd.find_range(v.co, 0.08):
            if abs(straight_y[j] - straight_y[v.index]) > 0.6:
                gap = min(gap, d)
    res = dict(plan_iou_vs_top_png=round(iou_top, 3), side_iou_vs_side_png=round(iou_side, 3),
               self_gap_m=round(gap, 4) if gap < 9 else '> 0.08', verdict='PASS' if gap > 0.01 else 'FAIL')
    json.dump(res, open(k.path('stage4', 'posed_checks.json'), 'w'), indent=1)
    say('POSED', json.dumps(res))


SJ = [0.0, 0.29, 0.45, 0.62, 0.82, 1.05, 1.30, 1.55, 1.80, 2.05, 2.30, 2.52, 2.70, 2.84, 2.96]


def stage4(k, body, pieces):
    global CURVE
    CURVE = Curve()
    say('plan centreline %.3f m, straight snake %.3f m' % (CURVE.L, Y_TAIL - Y_NOSE))
    apply_mirror(body)
    for p in pieces:
        _apply_mirror_piece(p)
    straight_y = [v.co.y for v in body.data.vertices]
    for o in [body] + pieces:
        for v in o.data.vertices:
            v.co = bend(v.co)
        o.data.update()
    ec = bend(eye_face_centre())
    ecm = bend(eye_face_centre() * Vector((-1, 1, 1)))
    k.meta['keep_valleys'] = lambda c: min((c - ec).length, (c - ecm).length) < 0.035
    jp = lambda s: tuple(bend(Vector((0.0, Y_NOSE + s, zc_t(Y_NOSE + s)[0]))))
    k.meta['closeups'] = [('head', jp(0.13), 0.17, 'hero'), ('neck and front coil', jp(0.75), 0.4, 'hero'),
                          ('tail tip', jp(2.85), 0.2, 'hero'), ('belly band', jp(1.5), 0.3, 'az090')]
    J = {i: jp(s) for i, s in enumerate(SJ)}
    B = [('spine', J[7], J[6], None),
         ('body3', J[6], J[5], 'spine', True), ('body2', J[5], J[4], 'body3', True), ('body1', J[4], J[3], 'body2', True),
         ('neck1', J[3], J[2], 'body1', True), ('neck', J[2], J[1], 'neck1', True), ('head', J[1], J[0], 'neck', True),
         ('tail0', J[7], J[8], 'spine'), ('tail1', J[8], J[9], 'tail0', True), ('tail2', J[9], J[10], 'tail1', True),
         ('tail3', J[10], J[11], 'tail2', True), ('tail4', J[11], J[12], 'tail3', True),
         ('tail5', J[12], J[13], 'tail4', True), ('tail6', J[13], J[14], 'tail5', True)]
    rig = armature(B)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            eb.align_roll(Vector((0, 0, 1)))        # local Z up on every bone: rot Z = sideways, rot X = pitch
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, bone='head')
    posed_checks(k, [body] + pieces, body, straight_y)
    # idle: slow breathing in the fore body, a head lift and turn, a lazy tail-tip sway
    clip(rig, 'idle', {1: {}, 12: {'body1': (2, 0, 0), 'neck': (-2, 0, 3), 'tail5': (0, 0, 6)},
                       24: {'neck1': (4, 0, 0), 'neck': (-3, 0, -3), 'head': (-1, 0, 0)},
                       36: {'body1': (2, 0, 0), 'neck': (-2, 0, 3), 'tail5': (0, 0, -6)}, 48: {}})
    # move: lateral undulation, a sideways wave running from the neck to the tail tip
    chain = ['neck1', 'body1', 'body2', 'body3', 'tail0', 'tail1', 'tail2', 'tail3', 'tail4', 'tail5']
    A = 9.0
    keys = {}
    for f in (1, 7, 13, 19, 25):
        ph = 2 * math.pi * (f - 1) / 24
        keys[f] = {b: (0, 0, round(A * math.sin(ph - j * 0.9) * (-1 if j < 4 else 1), 2)) for j, b in enumerate(chain)}
    clip(rig, 'move', keys)
    # attack: rear the fore body into an S, then strike forward and down, then settle
    clip(rig, 'attack', {
        1: {},
        10: {'body1': (10, 0, 8), 'neck1': (16, 0, -14), 'neck': (-14, 0, 8), 'head': (-10, 0, 0)},
        16: {'body1': (4, 0, 0), 'neck1': (-6, 0, 0), 'neck': (-4, 0, 0), 'head': (4, 0, 0)},
        20: {'body1': (4, 0, 0), 'neck1': (-6, 0, 0), 'neck': (-4, 0, 0), 'head': (4, 0, 0)},
        32: {}},
        loc={1: {'spine': (0, 0, 0)}, 10: {'spine': (0, -0.03, 0)}, 16: {'spine': (0, 0.10, 0)},
             20: {'spine': (0, 0.10, 0)}, 32: {'spine': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
