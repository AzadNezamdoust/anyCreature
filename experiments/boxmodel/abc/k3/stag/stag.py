import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
import math

EYE = (0.093, -0.485, 1.222)
META = dict(creature='stag', model='opus',
            keep_valleys=lambda c: (Vector(c) - Vector(EYE)).length < 0.045)

# skeleton the model is built on (x, y, z); left side only, .R mirrored
J = dict(
    hip=(0.0, 0.52, 0.86), spine=(0.0, 0.15, 0.88), chest=(0.0, -0.14, 0.86),
    neck0=(0.0, -0.33, 0.90), neck1=(0.0, -0.38, 1.16), head0=(0.0, -0.42, 1.22), nose=(0.0, -0.70, 1.15),
    tail0=(0.0, 0.64, 0.80), tail1=(0.0, 0.70, 0.60),
    # fore leg
    fsh=(0.10, -0.12, 0.72), felb=(0.095, -0.13, 0.50), fknee=(0.09, -0.17, 0.30),
    ffet=(0.09, -0.18, 0.10), fhoof=(0.09, -0.21, 0.01),
    # hind leg
    hhip=(0.11, 0.50, 0.74), hstf=(0.10, 0.45, 0.46), hhock=(0.09, 0.62, 0.28),
    hfet=(0.09, 0.59, 0.10), hhoof=(0.09, 0.565, 0.01),
    # ear / antler roots and tips
    ear0=(0.085, -0.41, 1.22), ear1=(0.21, -0.31, 1.35),
    ant0=(0.06, -0.45, 1.30), ant1=(0.27, -0.06, 1.70),
)

# half rings, rear -> front: top seam (y, z), bottom seam (y, z), 4 side points (s along T->B, x)
TORSO = [(0.03, 0.08), (0.25, 0.15), (0.55, 0.16), (0.85, 0.11)]
RINGS = [
    ((0.675, 0.81), (0.655, 0.63), [(0.05, 0.04), (0.3, 0.075), (0.6, 0.08), (0.88, 0.05)]),   # R0 rear cap
    ((0.58, 0.885), (0.60, 0.55), [(0.03, 0.08), (0.25, 0.16), (0.55, 0.18), (0.85, 0.14)]),  # R1 rump + thigh
    ((0.38, 0.895), (0.40, 0.57), [(0.03, 0.09), (0.25, 0.17), (0.55, 0.17), (0.85, 0.11)]),  # R2 hip front
    ((0.15, 0.905), (0.15, 0.60), [(0.03, 0.08), (0.25, 0.15), (0.55, 0.165), (0.85, 0.10)]),   # R3 waist
    ((-0.04, 0.965), (-0.05, 0.53), [(0.03, 0.08), (0.25, 0.16), (0.55, 0.19), (0.85, 0.12)]), # R4 ribs
    ((-0.17, 1.02), (-0.25, 0.52), [(0.03, 0.07), (0.25, 0.17), (0.55, 0.185), (0.85, 0.11)]),# R5 shoulder
    ((-0.22, 1.04), (-0.44, 0.72), [(0.03, 0.06), (0.25, 0.14), (0.55, 0.155), (0.85, 0.09)]), # R6 neck base
    ((-0.25, 1.12), (-0.49, 0.99), [(0.03, 0.05), (0.25, 0.10), (0.55, 0.11), (0.85, 0.08)]), # R7 neck mid
    ((-0.32, 1.25), (-0.47, 1.09), [(0.03, 0.04), (0.25, 0.075), (0.55, 0.085), (0.85, 0.06)]),# R8 poll
    ((-0.39, 1.32), (-0.49, 1.08), [(0.03, 0.045), (0.25, 0.085), (0.55, 0.10), (0.85, 0.07)]), # R9 skull
    ((-0.50, 1.30), (-0.54, 1.09), [(0.03, 0.045), (0.25, 0.09), (0.50, 0.095), (0.85, 0.06)]), # R10 brow
    ((-0.62, 1.22), (-0.63, 1.09), [(0.03, 0.035), (0.30, 0.062), (0.60, 0.062), (0.85, 0.045)]),# R11 muzzle
    ((-0.712, 1.19), (-0.705, 1.11), [(0.05, 0.025), (0.30, 0.042), (0.60, 0.042), (0.85, 0.032)]),# R12 nose
]

# antler main beam (centre, half size) and tines (beam segment index, path)
ANTLER = [((0.08, -0.43, 1.40), 0.026), ((0.13, -0.37, 1.48), 0.022), ((0.19, -0.28, 1.55), 0.019),
          ((0.24, -0.17, 1.60), 0.015), ((0.28, -0.05, 1.63), 0.005)]
TINES = [(1, [((0.12, -0.47, 1.47), 0.012), ((0.13, -0.60, 1.49), 0.003)]),   # brow tine, forward
         (2, [((0.18, -0.35, 1.58), 0.011), ((0.19, -0.42, 1.66), 0.003)]),   # bez tine, up-forward
         (3, [((0.23, -0.23, 1.63), 0.010), ((0.24, -0.27, 1.70), 0.003)]),   # trez tine, up
         (4, [((0.27, -0.10, 1.65), 0.008), ((0.28, -0.13, 1.70), 0.003)])]   # crown tine


def half_ring(bm, T, B, side):
    T, B = Vector((0, T[0], T[1])), Vector((0, B[0], B[1]))
    pts = [T] + [T.lerp(B, s) + Vector((x, 0, 0)) for s, x in side] + [B]
    return ring(bm, [tuple(p) for p in pts])


class Chain:
    """Successive extrusions of one face; each new section is placed as a rectangle
    (half sizes ra along a, rb along b) centred on c. horizontal=True keeps a = +X,
    b = -Y (legs); otherwise the frame is parallel-transported along the path."""

    def __init__(self, bm, face, ref=(1, 0, 0), horizontal=False):
        self.bm, self.face = bm, face
        self.c = face.calc_center_median().copy()
        self.a = Vector(ref).normalized()
        self.horizontal = horizontal

    def to(self, c, ra, rb, rot=0.0):
        c = Vector(c)
        d = (c - self.c).normalized()
        if self.horizontal:
            a, b = Vector((1, 0, 0)), Vector((0, -1, 0))
        else:
            a = (self.a - self.a.dot(d) * d).normalized()
            b = d.cross(a)
        if rot:
            a, b = a * math.cos(math.radians(rot)) + b * math.sin(math.radians(rot)), \
                   b * math.cos(math.radians(rot)) - a * math.sin(math.radians(rot))
        self.face.normal_update()
        n = self.face.normal.copy()
        if n.dot(d) < 0:
            n = -n
        pa = a - a.dot(n) * n
        if pa.length < 1e-4:
            pa = b - b.dot(n) * n
        pa.normalize()
        pb = n.cross(pa)
        r = extrude(self.bm, [self.face])
        vs = r['verts']
        m = centre(vs)
        # corners in angular order around the old face, matched to the target corners
        ang = [math.atan2((v.co - m).dot(pb), (v.co - m).dot(pa)) for v in vs]
        order = sorted(range(4), key=lambda i: ang[i])
        tgt = [(1, 1), (-1, 1), (-1, -1), (1, -1)]           # 45, 135, 225, 315 degrees
        tang = [math.atan2(j, i) for i, j in tgt]
        def cost(sh):
            return sum(abs(math.remainder(ang[order[q]] - tang[(q + sh) % 4], 2 * math.pi)) for q in range(4))
        sh = min(range(4), key=cost)
        for q in range(4):
            i, j = tgt[(q + sh) % 4]
            vs[order[q]].co = c + a * (i * ra) + b * (j * rb)
        self.face, self.c, self.a = r['faces'][0], c, a
        return r


def stage1(k):
    bm = bmesh.new()
    rows = [half_ring(bm, *r) for r in RINGS]
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1)
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)

    def side_face(ra, rb, i):
        """The quad between rings ra and rb, side points i and i+1 (vertex indices in the half ring)."""
        want = {rows[ra][i], rows[ra][i + 1], rows[rb][i], rows[rb][i + 1]}
        return next(f for f in bm.faces if set(f.verts) == want)

    # fore leg: out of the lower flank between the rib and shoulder rings
    L = Chain(bm, side_face(4, 5, 3), horizontal=True)
    L.to((0.095, -0.135, 0.50), 0.046, 0.080)   # elbow
    L.to((0.09, -0.165, 0.31), 0.028, 0.036)   # above the knee
    L.to((0.09, -0.172, 0.27), 0.025, 0.031)    # below the knee
    L.to((0.09, -0.18, 0.11), 0.018, 0.022)    # fetlock
    L.to((0.09, -0.192, 0.05), 0.024, 0.030)   # hoof top
    L.to((0.09, -0.205, 0.0), 0.030, 0.045)    # hoof sole
    # hind leg: out of the lower flank between the rump and hip rings
    H = Chain(bm, side_face(1, 2, 3), horizontal=True)
    H.to((0.10, 0.465, 0.47), 0.056, 0.095)     # stifle / thigh
    H.to((0.095, 0.57, 0.36), 0.034, 0.050)   # gaskin
    H.to((0.09, 0.628, 0.28), 0.025, 0.036)    # hock
    H.to((0.09, 0.615, 0.23), 0.021, 0.026)    # below the hock
    H.to((0.09, 0.59, 0.11), 0.018, 0.022)     # fetlock
    H.to((0.09, 0.577, 0.05), 0.024, 0.030)    # hoof top
    H.to((0.09, 0.565, 0.0), 0.030, 0.045)     # hoof sole
    # ear: a leaf out of the side of the skull behind the eye
    E = Chain(bm, side_face(8, 9, 2), ref=(0, 1, 0))
    E.to((0.13, -0.38, 1.28), 0.014, 0.045)
    E.to((0.18, -0.34, 1.33), 0.012, 0.045)
    E.to((0.23, -0.30, 1.37), 0.004, 0.006)
    # antler main beam: up, out and back from the top of the skull
    A = Chain(bm, side_face(9, 10, 1), ref=(1, 0, 0))
    segs = [A.to(c, r, r) for c, r in ANTLER]
    # tines: each out of the beam side face that looks most toward the tine tip
    for si, path in TINES:
        c0 = centre(segs[si]['verts'])
        f = max(segs[si]['sides'], key=lambda f: (f.calc_center_median() - c0).normalized().dot((Vector(path[-1][0]) - c0).normalized()))
        T = Chain(bm, f, ref=(1, 0, 0))
        for c, r in path:
            T.to(c, r, r)
    recalc_normals(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)

    def leg_edge(zr, yr):
        """An edge running from the body down to the first leg section at height zr."""
        for e in bm.edges:
            lo, hi = sorted(e.verts, key=lambda v: v.co.z)
            if abs(lo.co.z - zr) < 0.004 and yr[0] < lo.co.y < yr[1] and lo.co.x > 0.03 and hi.co.z > zr + 0.05:
                return e
        raise RuntimeError('leg_edge: none at z %.2f' % zr)

    with k.topo(bm, 'loop', 'shoulder loop on the fore leg: the leg swings from here in the walk'):
        loopcut(bm, leg_edge(0.50, (-0.25, -0.02)), t=0.5)
    with k.topo(bm, 'loop', 'hip loop on the hind leg: the thigh swings from here'):
        loopcut(bm, leg_edge(0.47, (0.35, 0.58)), t=0.5)
    with k.topo(bm, 'loop', 'neck loop between the neck-base and mid-neck rings: the grazing bend'):
        loopcut(bm, edge_near(bm, (0.12, -0.2925, 1.024)), t=0.5)
    with k.topo(bm, 'inset', 'eye socket: a loop in the skull side face, dented for the eye piece'):
        inner = inset(bm, [face_near(bm, (0.093, -0.47, 1.22), n=(1, 0, 0))], 0.4, depth=-0.008)
    for v in inner[0].verts:
        v.co.y -= 0.012
    # blunt the needle tips (tines, beam, ear): their long side quads triangulate into slivers
    tips = [(path[-1][0], 0.009 / path[-1][1]) for _, path in TINES] + [(ANTLER[-1][0], 0.009 / ANTLER[-1][1]),
                                                                        ((0.23, -0.30, 1.37), 1.4)]
    for c, f in tips:
        vs = verts_where(bm, lambda co, c=c: (co - Vector(c)).length < 0.012)
        assert len(vs) == 4, (c, len(vs))
        scale(vs, f, pivot=Vector(c))
    # ear: give the leaf a section (rear face back, tapering to the tip) and turn it back 22 deg
    # about the vertical through its root so it stands beside the antler base, clear of the eye
    root = Vector(J['ear0'])
    secs = []
    for c, r in (((0.13, -0.38, 1.28), 0.047), ((0.18, -0.34, 1.33), 0.0466), ((0.23, -0.30, 1.37), 0.0101)):
        vs = [v for v in bm.verts if abs((v.co - Vector(c)).length - r) < 0.0015]
        assert len(vs) == 4, (c, len(vs))
        secs.append((Vector(c), vs))
    ax = (secs[-1][0] - root).normalized()
    ra = (Vector((0, 1, 0)) - ax * ax.y).normalized()          # the ear's rear direction
    for (c, vs), back in zip(secs, (0.012, 0.009, 0.003)):
        move([v for v in vs if (v.co - c).dot(ra) > 0], ra * back)
    rotate(secs[0][1], (0, 0, 1), 10, pivot=root)
    for _, vs in secs[1:]:
        rotate(vs, (0, 0, 1), 22, pivot=root)
    move(secs[2][1], (0, 0, 0.01))
    # brow ridge over the eye and a stop in front of it
    for p, d in (((0.09, -0.51, 1.2475), (0.012, -0.004, 0.012)), ((0.085, -0.415, 1.26), (0.008, 0, 0.006)),
                 ((0.035, -0.62, 1.2155), (0, 0, -0.012)), ((0.0, -0.62, 1.22), (0, 0, -0.014))):
        move([vert_near(bm, p)], d)
    # armpit: the waist ring's low side vertex behind the fore leg sat in a dent (a dark concave
    # facet in the front-limb close-up); push it out so the chest-to-belly faces are convex
    move([vert_near(bm, (0.10, 0.15, 0.646))], (0.015, 0, 0))
    # and turn the belly strip behind the fore leg toward the side (it faced down: a dark band in the
    # low front close-up) by dropping its outer edge
    move([vert_near(bm, (0.115, 0.15, 0.646))], (0, 0, -0.025))
    commit(body, bm)


PAL = {'body': '#8a5a3a', 'mane': '#6a4630', 'cream': '#d9c3a0', 'antler': '#d8c8a8',
       'hoof': '#231a16', 'eye': '#111111'}


def body_rule(c, n, i):
    ax = abs(c.x)
    ear = ax > 0.10 and 1.2 < c.z < 1.40 and c.y > -0.42
    if c.z < 0.05 and ax > 0.04 or c.y < -0.70:
        return 'hoof'                                    # hooves and the black nose
    if (c - Vector(EYE)).length < 0.035 and n.x > 0.3:
        return 'mane'                                    # the eye socket in shadow
    if ear:
        return 'cream' if n.y < -0.3 else 'body'         # pale inner ear
    if c.z > 1.33:
        return 'antler'
    if c.z < 0.30 and ax > 0.04:
        return 'mane'                                    # dark lower legs
    if c.y < -0.42 and c.z < 1.14 and n.z < -0.3:
        return 'cream'                                   # pale jaw line
    if c.y > 0.585 and c.z > 0.6 and n.y > 0.25:
        return 'cream'                                   # rump patch
    if -0.28 < c.y < 0.62 and c.z < 0.74 and n.z < -0.25 and abs(c.x) > 0.0 and not (ax < 0.13 and c.z < 0.55):
        return 'cream'                                   # belly
    if c.y < -0.30 and 0.6 < c.z < 0.86 and n.y < -0.3:
        return 'cream'                                   # chest bib under the mane V
    if -0.52 < c.y < -0.15 and 0.8 < c.z < 1.24:
        return 'mane'
    return 'body'


def ring_pt(u, s):
    """A point on the base surface: u = ring index (float), s = 0 top seam .. 1 bottom seam."""
    def pts(ri):
        T, B, side = RINGS[ri]
        T, B = Vector((0, T[0], T[1])), Vector((0, B[0], B[1]))
        return [T] + [T.lerp(B, q) + Vector((x, 0, 0)) for q, x in side] + [B], (T + B) / 2
    i = min(int(u), len(RINGS) - 2); f = u - i
    (a, ma), (b, mb) = pts(i), pts(i + 1)
    j = min(int(s * 5), 4); g = s * 5 - j
    p = a[j].lerp(a[j + 1], g).lerp(b[j].lerp(b[j + 1], g), f)
    m = ma.lerp(mb, f)
    return p, (p - m).normalized()


# mane shingles: (ring u, s round the ring 0 top..1 bottom, length, half width, hang direction)
BACK, DOWN = (0, 0.35, -1), (0, -0.1, -1)
MANE = [(6.3, 0.12, 0.19, 0.085, BACK), (7.3, 0.12, 0.17, 0.080, BACK),                      # nape
        (5.9, 0.42, 0.22, 0.100, BACK), (6.7, 0.45, 0.20, 0.100, BACK), (7.5, 0.45, 0.16, 0.085, BACK),  # sides
        (6.9, 0.80, 0.18, 0.080, DOWN), (7.6, 0.80, 0.15, 0.075, DOWN)]                       # throat, V


def centre_pts(ps):
    return sum(ps, Vector()) / len(ps)


def stage3(k, body):
    paint(body, PAL, body_rule)
    pieces = []
    # eye: a low-poly lens standing proud in the socket
    bmb = edit(body)
    f = face_near(bmb, (EYE[0], EYE[1], EYE[2]), n=(1, 0, 0))
    fc, fn = f.calc_center_median().copy(), f.normal.copy()
    bmb.free()
    if fn.x < 0:
        fn = -fn
    u = (Vector((0, -1, 0)) - fn * fn.dot(Vector((0, -1, 0)))).normalized(); w = fn.cross(u)
    c = fc + fn * 0.002
    bm = bmesh.new()
    E_ = 1.6                                             # a bigger, readable eye (about 1/9 head length)
    vs = ring(bm, [c + u * 0.02 * E_, c + w * 0.014 * E_, c - u * 0.016 * E_, c - w * 0.013 * E_])
    fr, bk = ring(bm, [c + fn * 0.012, c - fn * 0.012])
    for q in range(4):
        bm.faces.new([vs[q], vs[(q + 1) % 4], fr]); bm.faces.new([vs[(q + 1) % 4], vs[q], bk])
    recalc_normals(bm)
    eye = object_from_bm('eye', bm, mirror=True); paint(eye, PAL, lambda c, n, i: 'eye'); pieces.append(eye)
    # tine points: one taper with the tine. Each point is rooted 40% of its length inside the blunt
    # tip, with a collar that matches the tine's last ring (no ledge), lengths varied (brow shortest,
    # crown longest) and leaning 7 deg outward along the tine
    bmb = edit(body)
    ends = []
    for (a, b), vis in zip([(path[-2][0], path[-1][0]) for _, path in TINES] + [(ANTLER[-2][0], ANTLER[-1][0])],
                           (0.034, 0.044, 0.05, 0.058, 0.066)):
        a, b = Vector(a), Vector(b)
        ring4 = [v.co.copy() for v in bmb.verts if (v.co - b).length < 0.02]
        assert len(ring4) == 4, (b, len(ring4), sorted((v.co - b).length for v in bmb.verts)[:6], len(bmb.verts))
        ends.append((a, b, ring4, vis))
    bmb.free()
    bm = bmesh.new()
    for a, b, ring4, vis in ends:
        m = centre_pts(ring4)
        d = (m - a).normalized()
        ring4 = [q - d * d.dot(q - m) for q in ring4]           # the ring's plane, square to the tine
        ring4.sort(key=lambda q: math.atan2((q - m).dot(d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < 0.95
                                                        else Vector((1, 0, 0))), (q - m).dot(d.orthogonal().normalized())))
        out = Vector((1, 0, 0)) - d * d.x
        dl = (d + out.normalized() * math.tan(math.radians(7))).normalized() if out.length > 1e-3 else d
        tot = vis / 0.6
        root = ring(bm, [m - d * min(0.4 * tot, 0.015)])[0]      # a short back point sunk in the tine (steep: no z-fight)
        collar = ring(bm, [m + d * 0.002 + (q - m) * 1.06 for q in ring4])
        tip = ring(bm, [m + dl * vis])[0]
        for q in range(4):
            bm.faces.new([collar[(q + 1) % 4], collar[q], root])
            bm.faces.new([collar[q], collar[(q + 1) % 4], tip])
    recalc_normals(bm)
    tines = object_from_bm('tines', bm, mirror=True); paint(tines, PAL, lambda c, n, i: 'antler'); pieces.append(tines)
    # mane: bold shingle plates in three rows around the neck (nape, sides, throat), hung down and
    # back like roof tiles, each rooted inside the neck; the long throat pair makes the V over the bib
    bm = bmesh.new()
    for u_, s_, L, w, g in MANE:
        p, n = ring_pt(u_, s_)
        assert p.z > 0.78, (u_, s_, p.z)                 # no roots over the fore-leg tops (drift)
        g = Vector(g).normalized()
        gt = (g - n * g.dot(n)).normalized()
        d = (gt + n * 0.2).normalized()
        t = n.cross(d).normalized()
        o = d.cross(t).normalized()
        secs = []
        for c, wi, ho, hi in ((p - n * 0.03, 0.6 * w, 0.012, 0.008), (p + d * 0.45 * L, w, 0.028, 0.008),
                              (p + d * L, 0.35 * w, 0.009, 0.005)):
            pts = [c + t * wi, c + o * ho, c - t * wi, c - o * hi]
            for q in pts:
                q.x = max(q.x, 0.004)
            secs.append(ring(bm, [tuple(q) for q in pts]))
        for r0, r1 in zip(secs, secs[1:]):
            bridge(bm, r0, r1, closed=True)
        cap(bm, secs[0]); cap(bm, list(reversed(secs[-1])))
    recalc_normals(bm)
    mane = object_from_bm('mane', bm, mirror=True); paint(mane, PAL, lambda c, n, i: 'mane'); pieces.append(mane)
    # tail: a short hanging wedge out of the rump patch
    bm = bmesh.new()
    rows = []
    for y, z, wd, h in ((0.635, 0.80, 0.035, 0.018), (0.695, 0.76, 0.05, 0.032), (0.72, 0.67, 0.042, 0.028),
                        (0.715, 0.60, 0.016, 0.012)):
        rows.append(ring(bm, [(0, y - h, z), (wd, y - h * 0.4, z), (wd * 0.8, y + h * 0.5, z), (0, y + h, z)]))
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1)
    cap(bm, rows[0]); cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)
    tail = object_from_bm('tail', bm, mirror=True)
    paint(tail, PAL, lambda c, n, i: 'mane' if n.y > -0.2 else 'cream'); pieces.append(tail)
    return pieces


def stage4(k, body, pieces):
    fe, fk, ff, fh = J['felb'], J['fknee'], J['ffet'], J['fhoof']
    hs, hk, hf, hh = J['hstf'], J['hhock'], J['hfet'], J['hhoof']
    rig = armature([
        ('hips', (0, 0.55, 0.80), (0, 0.15, 0.83), None),
        ('spine', (0, 0.15, 0.83), (0, -0.20, 0.85), 'hips', True),
        ('neck', (0, -0.30, 0.90), J['neck1'], 'spine'),
        ('head', J['neck1'], (0, -0.68, 1.16), 'neck', True),
        ('ear.L', J['ear0'], J['ear1'], 'head'),
        ('antler.L', J['ant0'], (0.22, -0.22, 1.60), 'head'),
        ('upper.L', J['fsh'], fe, 'spine'),
        ('fore.L', fe, fk, 'upper.L', True),
        ('cannon.L', fk, ff, 'fore.L', True),
        ('pastern.L', ff, fh, 'cannon.L', True),
        ('thigh.L', J['hhip'], hs, 'hips'),
        ('shin.L', hs, hk, 'thigh.L', True),
        ('hcannon.L', hk, hf, 'shin.L', True),
        ('hpastern.L', hf, hh, 'hcannon.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: lower the head to graze, chew, lift, flick an ear
    clip(rig, 'idle', {1: {}, 10: {'neck': (22, 0, 0), 'head': (-10, 0, 0)},
                       20: {'neck': (34, 0, 0), 'head': (-18, 0, 0)}, 26: {'neck': (34, 0, 0), 'head': (-14, 0, 0)},
                       34: {'neck': (15, 0, 0), 'head': (-4, 0, 0)}, 40: {'ear.L': (30, 0, 0)},
                       43: {'ear.L': (-12, 0, 0), 'ear.R': (20, 0, 0)}, 48: {}})
    # move: a diagonal-pair walk; the swinging leg folds at the knee / hock
    A, B = 16, -16
    clip(rig, 'move', {
        1: {'upper.L': (A, 0, 0), 'upper.R': (B, 0, 0), 'thigh.R': (A, 0, 0), 'thigh.L': (B, 0, 0)},
        7: {'fore.R': (-40, 0, 0), 'cannon.R': (-15, 0, 0), 'shin.L': (15, 0, 0), 'hcannon.L': (-30, 0, 0),
            'neck': (3, 0, 0)},
        13: {'upper.L': (B, 0, 0), 'upper.R': (A, 0, 0), 'thigh.R': (B, 0, 0), 'thigh.L': (A, 0, 0)},
        19: {'fore.L': (-40, 0, 0), 'cannon.L': (-15, 0, 0), 'shin.R': (15, 0, 0), 'hcannon.R': (-30, 0, 0),
             'neck': (3, 0, 0)},
        25: {'upper.L': (A, 0, 0), 'upper.R': (B, 0, 0), 'thigh.R': (A, 0, 0), 'thigh.L': (B, 0, 0)}})
    # attack: rear back, then drop the head and drive the antlers forward
    charge = {'neck': (30, 0, 0), 'head': (-22, 0, 0), 'upper.L': (-10, 0, 0), 'upper.R': (-10, 0, 0),
              'thigh.L': (-8, 0, 0), 'thigh.R': (-8, 0, 0)}
    clip(rig, 'attack', {1: {}, 8: {'neck': (-12, 0, 0), 'head': (10, 0, 0)}, 14: charge,
                         20: dict(charge, head=(-25, 0, 0)), 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
