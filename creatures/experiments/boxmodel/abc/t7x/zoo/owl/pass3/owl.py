import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
import bmkit as BK

# pass 2 (review fix): the body stands 8 degrees more upright about the leg root; every hand-placed point of the
# body, head, wings and beak goes through X(); colour rules read the inverse (XI) so they keep their sheet frame.
TH, PIV = math.radians(8.0), (-0.05, 0.08)


def X(y, z):
    dy, dz = y - PIV[0], z - PIV[1]
    return (PIV[0] + dy * math.cos(TH) + dz * math.sin(TH), PIV[1] - dy * math.sin(TH) + dz * math.cos(TH))


def X3(p):
    return (p[0], *X(p[1], p[2]))


def XI(c, n=None):
    """World point (and normal) back into the sheet frame."""
    dy, dz = c[1] - PIV[0], c[2] - PIV[1]
    co, si = math.cos(TH), math.sin(TH)
    cc = Vector((c[0], PIV[0] + dy * co - dz * si, PIV[1] + dy * si + dz * co))
    if n is None:
        return cc
    return cc, Vector((n[0], n[1] * co - n[2] * si, n[1] * si + n[2] * co))

# great horned owl, t7 hand box-model: one spine loft of 6-vertex half rings runs tail tip -> face, leaning as the
# sheet's side view does (tail low at the back, the round head high at the front). The legs are 2-face regions
# of the belly extruded down as horizontal hexagons, the ear tufts 1-face extrusions of the skull top. The folded
# wings, the hooked beak, the lens eyes and the talons are separate pieces. Coordinates from blueprint.json
# (refs.py, height 0.55 m); the sheet's top view is 1.26x too long and is not used.
META = dict(creature='owl', model='opus', stage1_tris=(1000, 2600), total_tris=(1600, 4500),
            closeups=[('head', (0.0, -0.24, 0.43), 0.13, 'hero'),
                      ('foot', (0.06, -0.09, 0.03), 0.07, 'hero'),
                      ('wing', (0.14, 0.06, 0.25), 0.2, 'hero')])

J = dict(
    hips=(0.0, 0.10, 0.18), spine=(0.0, -0.02, 0.24), chest=(0.0, -0.12, 0.31), neck=(0.0, -0.17, 0.38),
    head=(0.0, -0.20, 0.42), beak=(0.0, -0.31, 0.39),
    tuft=(0.085, -0.19, 0.50), tufttip=(0.10, -0.165, 0.555),
    tail0=(0.0, 0.15, 0.14), tail1=(0.0, 0.31, 0.04),
    wing=(0.125, -0.08, 0.33), wing1=(0.135, 0.08, 0.25), wing2=(0.075, 0.26, 0.15),
    thigh=(0.06, -0.05, 0.14), knee=(0.06, -0.065, 0.065), ankle=(0.06, -0.072, 0.016), toe=(0.06, -0.14, 0.008),
)
J = {k_: (v if k_ in ('thigh', 'knee', 'ankle', 'toe') else X3(v)) for k_, v in J.items()}
J['tail1'] = X3((0.0, 0.25, 0.08))

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODYP = [(0, 1), (0.7, 0.9), (1, 0.15), (0.88, -0.5), (0.5, -0.88), (0, -1)]
BELLY = [(0, 1), (0.72, 0.88), (1, 0.05), (0.88, -0.58), (0.48, -0.92), (0, -1)]
HEADB = [(0, 1), (0.55, 0.99), (0.95, 0.65), (1, 0.0), (0.7, -0.75), (0, -1)]     # skull back: tuft face high
HEAD = [(0, 1), (0.75, 0.93), (1, 0.3), (0.92, -0.45), (0.55, -0.88), (0, -1)]
FACE = [(0, 1), (0.85, 0.95), (1, 0.2), (0.9, -0.5), (0.5, -0.9), (0, -1)]
TAIL = [(0, 1), (0.85, 0.6), (1, 0.0), (0.85, -0.6), (0.45, -0.9), (0, -1)]


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = X(*top), X(*bot)
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


# the pass-3 stations (sheet frame): name, top seam, bottom seam, W, profile
OLD = [('T0', (0.262, 0.10), (0.255, 0.078), 0.058, TAIL),
       ('T1', (0.215, 0.15), (0.195, 0.07), 0.07, TAIL),
       ('R0', (0.17, 0.24), (0.13, 0.07), 0.085, BODYP),
       ('R1', (0.09, 0.33), (0.04, 0.09), 0.12, BELLY),
       ('M0', (0.0, 0.38), (-0.03, 0.075), 0.135, BELLY),
       ('C0', (-0.06, 0.41), (-0.10, 0.085), 0.135, BELLY),
       ('C1', (-0.10, 0.45), (-0.17, 0.13), 0.125, BODYP),
       ('N0', (-0.13, 0.48), (-0.235, 0.21), 0.115, BODYP),
       ('H0', (-0.17, 0.50), (-0.27, 0.29), 0.115, HEADB),
       ('H1', (-0.225, 0.50), (-0.29, 0.33), 0.11, HEAD),
       ('H2', (-0.27, 0.475), (-0.30, 0.355), 0.095, FACE),
       ('H3', (-0.29, 0.445), (-0.302, 0.37), 0.08, FACE)]

# poly pass: 12 -> 22 stations (tail root, rump, belly, shoulder, neck curve, skull, brow, face rim), 6 -> 12 vertices
# per half ring. Stations sit at fractional old indices; the new ones are re-fitted to the sheet's side outline.
STATIONS = [0, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 6.5, 7, 7.33, 7.67, 8, 8.5, 9, 9.5, 10, 10.5, 11]
NV = 12


def _cr(p0, p1, p2, p3, t):
    return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def _along(vals, f):
    i = min(int(f), len(vals) - 2); t = f - i
    g = lambda k: vals[max(0, min(len(vals) - 1, k))]
    return _cr(g(i - 1), g(i), g(i + 1), g(i + 2), t)


def resample(prof, n=NV):
    """A half profile (top seam -> bottom seam) through a closed Catmull-Rom loop (the mirror half included),
    resampled at n points of equal arc length: the same shape, its facets rounded."""
    loop = list(prof) + [(-x, h) for x, h in reversed(prof[1:-1])]
    m = len(loop)
    dense = []
    for i in range(len(prof) - 1):
        for s in range(40):
            dense.append(_cr(loop[(i - 1) % m], loop[i], loop[(i + 1) % m], loop[(i + 2) % m], s / 40))
    dense.append(prof[-1])
    L = [0.0]
    for p, q in zip(dense, dense[1:]):
        L.append(L[-1] + math.dist(p, q))
    out = []
    for k in range(n):
        tgt = L[-1] * k / (n - 1)
        j = next(j for j in range(len(L)) if L[j] >= tgt - 1e-12)
        out.append((max(0.0, dense[j][0]), dense[j][1]))
    out[0], out[-1] = (0.0, out[0][1]), (0.0, out[-1][1])
    return out


SIDE_OUT = json.load(open(os.path.join(HERE, 'blueprint.json')))['side']['outline']


def sheet_hit(top, bot, tol=0.03):
    """Re-fit a station's seam points to the traced side outline along its own cut line; a hit further than tol
    from the guess (the ear tufts, the legs under the belly) keeps the guess."""
    c = ((top[0] + bot[0]) / 2, (top[1] + bot[1]) / 2)
    h = math.dist(top, bot) / 2
    d = ((top[0] - bot[0]) / 2 / h, (top[1] - bot[1]) / 2 / h)
    ts = []
    for i in range(len(SIDE_OUT)):
        p, q = SIDE_OUT[i], SIDE_OUT[(i + 1) % len(SIDE_OUT)]
        ey, ez = q[0] - p[0], q[1] - p[1]
        den = -d[0] * ez + d[1] * ey
        if abs(den) < 1e-12:
            continue
        ry, rz = p[0] - c[0], p[1] - c[1]
        t, s = (-ry * ez + rz * ey) / den, (d[0] * rz - d[1] * ry) / den
        if 0 <= s <= 1:
            ts.append(t)
    up = min([t for t in ts if t > 0], key=lambda t: abs(t - h), default=h)
    dn = min([-t for t in ts if t < 0], key=lambda t: abs(t - h), default=h)
    up, dn = (up if abs(up - h) < tol else h), (dn if abs(dn - h) < tol else h)
    return (c[0] + d[0] * up, c[1] + d[1] * up), (c[0] - d[0] * dn, c[1] - d[1] * dn)


def stations():
    tops, bots, Ws = [o[1] for o in OLD], [o[2] for o in OLD], [(o[3],) for o in OLD]
    profs = [resample(o[4]) for o in OLD]
    out, cnt = [], {}
    for f in STATIONS:
        i = int(f)
        if f == i:
            nm, top, bot, W, pr = OLD[i][0], tops[i], bots[i], Ws[i][0], profs[i]
        else:
            t = f - i
            top, bot = sheet_hit(_along(tops, f), _along(bots, f)) if f >= 1.5 else (_along(tops, f), _along(bots, f))
            W = _along(Ws, f)[0]
            pr = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(profs[i], profs[i + 1])]
            cnt[i] = cnt.get(i, 0) + 1
            nm = OLD[i][0] + 'abc'[cnt[i] - 1]
        out.append(tb(nm, top, bot, W, pr))
    return out


SECS = stations()

# limb sections: (centre xyz, rx, ry) - horizontal hexagons; feathered thigh, thin shank, broad foot
LEG = [((0.062, -0.062, 0.058), 0.04, 0.05), ((0.062, -0.064, 0.047), 0.036, 0.043),
       ((0.062, -0.066, 0.036), 0.03, 0.034), ((0.062, -0.072, 0.018), 0.03, 0.036),
       ((0.062, -0.076, 0.004), 0.024, 0.03)]
TUFT = [((0.092, *X(-0.19, 0.516)), 0.016, 0.014, 0.0), ((0.122, *X(-0.18, 0.546)), 0.004, 0.003, 0.0)]


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def role_pos(sec, u, s, corner=0.55):
    c, rx, ry = sec[0], sec[1], sec[2]
    if corner is None:                  # a round limb: the 3-face root region's 8 vertices on an octagon
        ph = s * (math.pi / 8 + (1 - u) / 2 * (3 * math.pi / 4))
        return (c[0] + rx * math.cos(ph), c[1] + ry * math.sin(ph), c[2])
    dz = sec[3] if len(sec) > 3 else 0.0
    k = 1.0 if u == 0 else corner
    return (c[0] + u * rx, c[1] + s * ry * k, c[2] - u * dz)


def grow(bm, faces, roles, secs, corner=0.55):
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (u, s) in new.items():
            v.co = Vector(role_pos(sec, u, s, corner))
        faces, roles = r['faces'], new
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    # legs: the 3-face lower-flank region of the M0-C0 span just above the belly-seam face (round 8-vertex
    # rings), down to the foot; a higher, taller root folded its side walls under the flank (trial r30)
    i = idx['M0']
    rr, rf = rings[i], rings[i + 1]
    j = NV - 5
    roles = {}
    for q in range(4):
        u = 1 - 2 * q / 3
        roles[rf[j + q]] = (u, -1); roles[rr[j + q]] = (u, 1)
    grow(bm, spans[i][j:j + 3], roles, LEG, corner=None)
    # ear tufts: the skull-top face of the H0-H1 span nearest the pass-3 tuft root
    i = idx['H0']
    rr, rf = rings[i], rings[i + 1]
    tr = Vector(X3((0.075, -0.2, 0.505)))
    j = min(range(NV - 1), key=lambda j: (spans[i][j].calc_center_median() - tr).length)
    grow(bm, [spans[i][j]], {rf[j]: (-1, -1), rf[j + 1]: (1, -1), rr[j]: (-1, 1), rr[j + 1]: (1, 1)}, TUFT, corner=1.0)
    snap_seam(bm)
    return object_from_bm('body', bm)


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


EYE = Vector(X3((0.045, -0.29, 0.425)))      # the ref eye (front view x 0.045, side view y -0.29, z 0.425)


def eye_hit(bm_or_tree):
    t = bm_or_tree if isinstance(bm_or_tree, BVHTree) else BVHTree.FromBMesh(bm_or_tree)
    loc, n, i, d = t.ray_cast(Vector((EYE.x, -0.6, EYE.z)), Vector((0, 1, 0)), 1.0)
    return loc, n


def keep_eye(c):
    return abs(abs(c.x) - EYE.x) < 0.035 and abs(c.y - EYE.y) < 0.04 and abs(c.z - EYE.z) < 0.04


def stage2(k, body):
    """Joint rings (knee, ankle, neck-skull, belly, tail root), the eye socket, a flat face disc."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    lp = lambda i: role_pos(LEG[i], 1, 1, None)
    cuts = [('knee ring: the leg bend under the thigh feathers', mid(lp(1), lp(2))),
            ('ankle ring: the foot bend', mid(lp(2), lp(3))),
            ('neck-skull ring: the head turn', mid(P('N0b')[0], P('H0')[0])),
            ('belly ring: the hop crouch', mid(P('R1a')[0], P('M0')[0])),
            ('tail root ring: the tail lift', mid(P('R0')[0], P('T1a')[0]))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_), t=0.5)
    loc, _n = eye_hit(bm)
    f = face_near(bm, loc)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the face disc, its floor pushed in'):
        inner = inset(bm, [f], 0.36, 0.0)
    move(list(inner[0].verts), -fn * 0.008)
    flatten([vert_near(bm, q) for q in P('H3')])                 # a flat face disc
    move([vert_near(bm, P('H2')[1])], (0.006, -0.006, 0.004))   # brow corner forward / out over the eye
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


PAL = {'brown': '#8a705a', 'dark': '#5a4839', 'tan': '#c9a57a', 'cream': '#efe3cb', 'beak': '#2b2828',
       'amber': '#d9891f'}


def body_rule(c, n, i):
    c, n = XI(c, n)
    x, y, z = abs(c.x), c.y, c.z
    if z > 0.505 and x > 0.05:
        return 'dark'                                   # ear tufts
    if y < -0.28 and n.y < -0.55:
        return 'tan'                                    # the flat face disc
    if z < 0.03:
        return 'tan'                                    # feet
    if y > 0.2:
        return 'dark' if y > 0.235 else 'tan'           # banded tail
    if y < -0.08 and z < 0.36 and n.y < -0.15:
        return 'cream' if z > 0.2 else 'tan'            # cream bib over a tan lower breast
    if z < 0.12:
        return 'tan'                                    # feathered legs and the belly
    return 'brown'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 4 for k_ in range(8)]]
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(8):
        a, b = j, (j + 1) % 8
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def toe(bm, bt, root, d, L):
    """A thin toe block from root along d (tapering, lying on the ground) and its hooked talon (separate piece bt)."""
    side = Vector((-d.y, d.x, 0.0))
    rows = []
    for t, w, h in ((0.0, 0.007, 0.013), (0.55, 0.006, 0.011), (1.0, 0.0045, 0.008)):
        c = root + d * (L * t)
        rows.append([bm.verts.new(c + side * su * w + Vector((0, 0, zz))) for su, zz in ((-1, 0.0015), (1, 0.0015), (1, h), (-1, h))])
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(rows[-1])
    tip = root + d * (L + 0.002)
    base = [bt.verts.new(tip + side * su * 0.004 + Vector((0, 0, zz))) for su, zz in ((-1, 0.002), (1, 0.002), (1, 0.009), (-1, 0.009))]
    pt = bt.verts.new(tip + d * 0.014 + Vector((0, 0, 0.0008)))
    bt.faces.new(list(reversed(base)))
    for j in range(4):
        bt.faces.new([base[j], base[(j + 1) % 4], pt])


# folded wing: sections root -> tip, (top (y, z), bottom (y, z), x inner, x outer); the inner face sinks in the flank
WING = [((-0.10, 0.39), (-0.15, 0.22), 0.09, 0.135),    # poly pass: root out 1 cm (the rounder flank z-fought it)
        ((-0.02, 0.385), (-0.07, 0.15), 0.105, 0.150),
        ((0.08, 0.33), (0.04, 0.12), 0.10, 0.152),
        ((0.17, 0.25), (0.13, 0.11), 0.075, 0.118),
        ((0.225, 0.205), (0.20, 0.112), 0.063, 0.095),
        ((0.28, 0.15), (0.27, 0.118), 0.05, 0.07)]


def wing_bm():
    bm = bmesh.new()
    rows = []
    for (yt, zt), (yb, zb), xi, xo in WING:
        xm = (xi + xo) / 2
        L = lambda t: (yt + (yb - yt) * t, zt + (zb - zt) * t)
        pts = [(xm, *L(0.0)), (xo, *L(0.28)), (xo, *L(0.72)), (xm, *L(1.0)), (xi, *L(0.72)), (xi, *L(0.28))]
        rows.append([bm.verts.new(X3(p)) for p in pts])
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b, closed=True)
    bm.faces.new(list(reversed(rows[0]))); bm.faces.new(rows[-1])
    return bm


def beak_bm():
    """The hooked beak, half: a ridge and a keel on the seam (the mirror closes it), a side, a down-hooked tip."""
    bm = bmesh.new()
    rt, rs, rb = [bm.verts.new(p) for p in ((0, -0.28, 0.418), (0.017, -0.28, 0.392), (0, -0.28, 0.365))]
    mt, ms, mb = [bm.verts.new(p) for p in ((0, -0.312, 0.398), (0.009, -0.307, 0.381), (0, -0.302, 0.367))]
    tip = bm.verts.new((0, -0.312, 0.35))
    for v in bm.verts:
        v.co = Vector(X3(v.co))
    bm.faces.new([rt, rs, rb])
    bm.faces.new([rt, mt, ms, rs]); bm.faces.new([rs, ms, mb, rb])
    bm.faces.new([mt, tip, ms]); bm.faces.new([ms, tip, mb])
    return bm


def clump(bm, a, n, lay, s, L):
    """A chunky fur clump: a square base sunk in the body, a thick mid section standing off the surface
    (sideways 0.8 s, 0.9 s deep), and a blunt narrow tip laid back along `lay` - a bold wedge, not a shard."""
    n, lay = Vector(n).normalized(), Vector(lay).normalized()
    u = n.cross(lay).normalized(); w = u.cross(n)
    b = a - n * 0.03
    base = [bm.verts.new(b + u * su * s + w * sw * s) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    sn = 0.45 * s
    m = a + n * (0.9 * sn) + lay * L * 0.4
    mid = [bm.verts.new(m + u * su * s * 0.8 + n * sv * sn) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    t = a + n * L * 0.32 + lay * L
    tip = [bm.verts.new(t + u * su * s * 0.14 + n * sv * s * 0.12) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    shell = base + mid + tip
    lo = min(v.co.x for v in shell)
    if lo < 0.003:                                  # never across the mirror plane
        for v in shell:
            v.co.x += 0.003 - lo
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip[(j + 1) % 4], tip[j]])
    bm.faces.new(tip)


def surf(a, b, t, jf):
    """A point on the coarse loft between sections a and b (t from a to b) at fractional ring index jf, and its
    outward normal (radial from the interpolated section centre)."""
    A, Bq = P(a), P(b)
    j0 = min(int(jf), 4); f = jf - j0
    pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
    p = pa.lerp(pb, t)
    ca = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == a][0]))
    cb = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == b][0]))
    c = ca.lerp(cb, t)
    return p, (p - c).normalized()


def clumps(spec, tree):
    """spec: [(a, b, t, jf, lay, s, L)] -> one mirrored piece of fur clumps, each rooted on the nearest point
    of the subdivided, fitted body (the coarse loft only says where)."""
    bm = bmesh.new()
    for a, b, t, jf, lay, s_, L_ in spec:
        p, n_ = surf(a, b, t, jf)
        loc, fn, _i, _d = tree.find_nearest(p)
        n2 = (fn + n_).normalized()
        clump(bm, loc, n2, Vector(lay), s_, L_)
    return bm


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('brown', 'dark', 'tan', 'cream')}, body_rule)
    tree = body_bvh(body)
    c, n = eye_hit(tree)
    n = (n.normalized() + Vector((0.35, -1.0, 0.0)).normalized()).normalized()
    c = c + n * 0.002
    bm = bmesh.new()
    lens(bm, c, n, 0.018, 0.008)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'beak': PAL['beak']},
          lambda c_, n_, i: 'beak' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.0075 and n_.dot(n) > 0.5 else 'amber')
    beak = object_from_bm('beak', beak_bm())
    paint(beak, {'beak': PAL['beak']}, lambda c_, n_, i: 'beak')
    wing = object_from_bm('wing', wing_bm())
    paint(wing, {'brown': PAL['brown'], 'dark': PAL['dark'], 'tan': PAL['tan']},
          lambda c_, n_, i: (lambda q: 'dark' if q.y > 0.11 else ('tan' if q.z < 0.2 and q.y < 0.0 else 'brown'))(XI(c_)))
    # feet: 3 thin toes forward, 1 back, each tipped with a separate dark talon (no paw pad)
    tb_, tl = bmesh.new(), bmesh.new()
    (cx, cy, _), rx, ry = LEG[3]
    for ang, L in ((-28, 0.046), (0, 0.052), (28, 0.046), (180, 0.03)):
        d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.0))
        toe(tb_, tl, Vector((cx, cy, 0.0)) + d * (ry * 0.55), d, L)
    toes = object_from_bm('toes', tb_)
    paint(toes, {'tan': PAL['tan']}, lambda c_, n_, i: 'tan')
    talons = object_from_bm('talons', tl)
    paint(talons, {'beak': PAL['beak']}, lambda c_, n_, i: 'beak')
    return [eye, beak, wing, toes, talons]


WING_FLEX_Y = 0.2


def bind_wing(piece, rig, body):
    """The wing rides the flank with the body's own weights (kit bind), except its primaries (the last ring
    pair, past y 0.2), which follow the wingtip bone of their side so the wing can flex open."""
    bind(piece, rig, body=body)
    tips = {s: piece.vertex_groups.get('wingtip' + s) or piece.vertex_groups.new(name='wingtip' + s) for s in ('.L', '.R')}
    gi = {g.index: g.name for g in piece.vertex_groups}
    chest = piece.vertex_groups.get('chest') or piece.vertex_groups.new(name='chest')
    for v in piece.data.vertices:
        p = piece.matrix_world @ v.co
        for g in list(v.groups):                       # the head turn never pulls the wing root
            if gi.get(g.group, '').split('.')[0] in ('head', 'neck', 'tuft'):
                w = g.weight
                piece.vertex_groups[g.group].remove([v.index])
                chest.add([v.index], w, 'ADD')
        if p.y > WING_FLEX_Y:
            for g in list(v.groups):
                piece.vertex_groups[g.group].remove([v.index])
            tips['.L' if p.x > 0 else '.R'].add([v.index], 1.0, 'REPLACE')


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['beak'], 'neck', True),
         ('tuft.L', J['tuft'], J['tufttip'], 'head'),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('wing.L', J['wing'], J['wing1'], 'chest'),
         ('wingtip.L', J['wing1'], J['wing2'], 'wing.L', True),
         ('thigh.L', J['thigh'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    # the wing bones never pull the flank: their body weights go to the chest
    gi = {g.index: g.name for g in body.vertex_groups}
    chest = body.vertex_groups['chest']
    for v in body.data.vertices:
        w = sum(g.weight for g in v.groups if gi[g.group].startswith('wing'))
        if w > 0:
            for g in list(v.groups):
                if gi[g.group].startswith('wing'):
                    body.vertex_groups[gi[g.group]].remove([v.index])
            chest.add([v.index], w, 'ADD')
    wing = next(p for p in pieces if 'wing' in p.name)
    for p in pieces:
        if p is wing:
            bind_wing(p, rig, body)
        elif 'talons' in p.name or 'toes' in p.name or 'eye' in p.name:
            bind(p, rig, body=body)
        else:
            bind(p, rig, bone='head')
    # idle: breathing, a slow owl head turn, a tuft twitch, a wing settle
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'head': (0, 0, 22), 'wing.L': (0, 0, -3), 'wing.R': (0, 0, 3)},
                       20: {'head': (0, 0, 22), 'tuft.L': (-12, 0, 0)}, 26: {},
                       36: {'chest': (1.5, 0, 0), 'head': (0, 0, -22)}, 48: {}})
    # move: a hop - crouch, push off with the wings half open, land
    clip(rig, 'move', {
        1: {},
        6: {'thigh.L': (20, 0, 0), 'thigh.R': (20, 0, 0), 'shin.L': (-25, 0, 0), 'shin.R': (-25, 0, 0), 'spine': (4, 0, 0)},
        12: {'thigh.L': (-10, 0, 0), 'thigh.R': (-10, 0, 0), 'foot.L': (15, 0, 0), 'foot.R': (15, 0, 0),
             'wing.L': (6, 0, -8), 'wing.R': (6, 0, 8), 'wingtip.L': (0, 0, -8), 'wingtip.R': (0, 0, 8),
             'tail0': (10, 0, 0)},
        18: {'thigh.L': (8, 0, 0), 'thigh.R': (8, 0, 0), 'wing.L': (-3, 0, -4), 'wing.R': (-3, 0, 4)},
        24: {}},
        loc={1: {'hips': (0, 0, 0)}, 6: {'hips': (0, 0, -0.012)}, 12: {'hips': (0, -0.03, 0.05)},
             18: {'hips': (0, -0.05, 0.01)}, 24: {'hips': (0, 0, 0)}})
    # attack: rear back with the wings mantled, then a talon strike forward and a head lunge
    clip(rig, 'attack', {
        1: {},
        10: {'spine': (-8, 0, 0), 'neck': (-6, 0, 0), 'wing.L': (8, 0, -10), 'wing.R': (8, 0, 10),
             'wingtip.L': (0, 0, -8), 'wingtip.R': (0, 0, 8), 'tuft.L': (-15, 0, 0)},
        18: {'spine': (8, 0, 0), 'neck': (10, 0, 0), 'head': (8, 0, 0), 'thigh.L': (12, 0, 0), 'shin.L': (25, 0, 0),
             'foot.L': (-35, 0, 0), 'wing.L': (5, 0, -6), 'wing.R': (5, 0, 6), 'tuft.L': (-15, 0, 0)},
        24: {'spine': (4, 0, 0), 'neck': (5, 0, 0), 'thigh.L': (5, 0, 0), 'shin.L': (10, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 10: {'hips': (0, 0.02, 0)}, 18: {'hips': (0, -0.04, 0.01)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
