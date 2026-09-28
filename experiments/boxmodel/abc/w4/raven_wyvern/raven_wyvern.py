import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='raven_wyvern', model='opus')

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    hips=(0.0, 0.20, 0.47), spine=(0.0, -0.14, 0.58), chest=(0.0, -0.40, 0.66),
    neck0=(0.0, -0.56, 0.76), neck1=(0.0, -0.62, 0.92), neck2=(0.0, -0.62, 1.05),
    head=(0.0, -0.62, 1.15), bill=(0.0, -1.015, 1.045),
    tail0=(0.0, 0.40, 0.33), tail1=(0.0, 0.60, 0.255), tail2=(0.0, 0.80, 0.225), tail3=(0.0, 1.00, 0.215),
    hipL=(0.155, -0.055, 0.49), kneeL=(0.19, -0.115, 0.29), hockL=(0.19, 0.00, 0.20),
    ankleL=(0.18, -0.10, 0.05), toeL=(0.18, -0.30, 0.01),
    shoulderL=(0.17, -0.42, 0.73), elbowL=(0.37, -0.47, 0.47), wristL=(0.44, -0.56, 0.14),
    fingerL=(0.47, -0.30, 0.36), finger2L=(0.44, 0.05, 0.66), tipL=(0.34, 0.42, 0.95),
)

# spine stations, tail tip -> bill tip: (y, z, halfwidth, top, bottom, mid, ku, kl[, tangent override])
ST = [
    (1.00, 0.215, .012, .014, .012, .0, .8, .7),     # T0 tail tip
    (0.80, 0.225, .032, .040, .030, .005, .8, .6),   # T1
    (0.60, 0.255, .055, .065, .050, .01, .8, .6),    # T2
    (0.40, 0.33, .095, .100, .080, .01, .8, .6),     # T3 tail root
    (0.20, 0.45, .150, .130, .120, .0, .8, .6),      # B0 rump
    (0.03, 0.53, .180, .190, .130, .0, .85, .6),     # Bm
    (-0.14, 0.58, .200, .230, .190, .0, .85, .55),   # B1 ribs
    (-0.36, 0.63, .190, .220, .270, .02, .85, .45),  # B2 chest keel
    (-0.55, 0.74, .150, .150, .200, .0, .85, .5),    # B3 neck base
    (-0.62, 0.90, .120, .100, .110, .0, .85, .75),   # N1
    (-0.62, 1.03, .125, .110, .100, .0, .85, .75),   # N2
    (-0.59, 1.15, .140, .160, .110, .0, .9, .75, (-0.8, 0.6)),   # H0 occiput / throat corner
    (-0.68, 1.19, .150, .125, .120, .0, .92, .7),    # H1 skull back
    (-0.78, 1.19, .140, .120, .110, .0, .92, .75),   # H1b skull front / brow (eye here)
    (-0.845, 1.14, .080, .078, .070, .0, .85, .7),   # H2 bill base: the stop
    (-0.94, 1.085, .050, .048, .040, .0, .8, .7),    # H3 bill
    (-1.015, 1.045, .010, .012, .012, .0, .8, .7),   # H4 bill tip
]


HU = {11: 0.8, 12: 0.85, 13: 0.85, 10: 0.75}   # square skull tops: the upper-side vertex sits high


def _tan(i):
    s = ST[i]
    if len(s) > 8:
        t = Vector((0, s[8][0], s[8][1]))
    else:
        a = ST[max(i - 1, 0)]; b = ST[min(i + 1, len(ST) - 1)]
        t = Vector((0, b[0] - a[0], b[1] - a[1]))
    return t.normalized()


def half_ring(i):
    y, z, w, T, B, m, ku, kl = ST[i][:8]
    t = _tan(i)
    N = Vector((0, t.z, -t.y))          # dorsal direction in the yz plane
    c = Vector((0, y, z))
    hu = HU.get(i, 0.6)
    prof = [(0, T), (ku * w, m + (T - m) * hu), (w, m), (kl * w, m - (m + B) * 0.6), (0, -B)]
    return [Vector((x, 0, 0)) + c + N * v for x, v in prof]


def seg(bm, face, c, axis, w, d):
    """Extrude one face and square its new end as a w x d rectangle at c, perpendicular to axis."""
    r = extrude(bm, [face])
    f = r['faces'][0]
    vs = list(f.verts)
    a = Vector(axis).normalized()
    U = Vector((1, 0, 0)) - a * a.x
    if U.length < 0.2:
        U = Vector((0, 0, 1)) - a * a.z
    U.normalize()
    W = a.cross(U).normalized()
    c = Vector(c)
    corners = [c + U * (su * w) + W * (sw * d) for su, sw in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    oc = centre(vs)
    offs = [(v.co - oc).normalized() for v in vs]
    best = None
    for order in (corners, corners[::-1]):
        for s in range(4):
            cs = order[s:] + order[:s]
            cost = sum(((q - c).normalized() - o).length for q, o in zip(cs, offs))
            if best is None or cost < best[0]:
                best = (cost, cs)
    place(vs, best[1])
    return f, r


def chain(bm, face, pts):
    """pts: [(centre, w, d)]; axis at each = direction prev -> next."""
    prev = face.calc_center_median()
    out = []
    for i, (p, w, d) in enumerate(pts):
        nxt = Vector(pts[i + 1][0]) if i + 1 < len(pts) else Vector(p) + (Vector(p) - prev)
        ax = (nxt - prev)
        face, r = seg(bm, face, p, ax, w, d)
        out.append(r)
        prev = Vector(p)
    return face, out


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, half_ring(i)) for i in range(len(ST))]
    bands = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    # leg: from the lower flank band between Bm (5) and B1 (6)
    legf = bands[5][2]
    chain(bm, legf, [
        ((0.215, -0.10, 0.35), .085, .120),
        ((0.21, -0.05, 0.255), .072, .090),
        ((0.195, 0.00, 0.205), .042, .046),
        ((0.19, -0.04, 0.14), .036, .040),
        ((0.18, -0.10, 0.05), .034, .034),
        ((0.18, -0.12, 0.00), .055, .120),
    ])
    # wing arm: from the upper flank band between B2 (7) and B3 (8)
    wf = bands[7][1]
    _, rs = chain(bm, wf, [
        ((0.24, -0.43, 0.70), .060, .065),
        ((0.37, -0.47, 0.47), .045, .055),
        ((0.43, -0.54, 0.20), .036, .045),
        ((0.44, -0.56, 0.13), .030, .040),
    ])
    tip = Vector(J['fingerL'])
    last = rs[-1]
    for f in last['sides']:
        f.normal_update()          # new side faces carry stale normals until updated
    side = max(last['sides'], key=lambda f: f.normal.dot((tip - f.calc_center_median()).normalized()))
    chain(bm, side, [
        ((0.47, -0.30, 0.36), .026, .032),
        ((0.44, 0.05, 0.66), .020, .025),
        ((0.34, 0.42, 0.95), .005, .007),
    ])
    snap_seam(bm, 1e-6)
    return object_from_bm('body', bm)


def P(i, j):
    """stage-1 position of spine ring i, vertex j (0 top seam .. 4 bottom seam)."""
    return half_ring(i)[j]


def stage2(k, body):
    bm = edit(body)
    V_ = lambda i, j: vert_near(bm, P(i, j))
    # --- vertex moves (free) ---
    move([V_(13, 1)], (0.018, -0.030, 0.012))      # brow: skull-front upper corner overhangs the eye
    move([V_(13, 0)], (0.0, -0.015, 0.0))          # brow ridge on the midline
    move([V_(14, 0)], (0.0, 0.0, -0.012))          # deepen the stop at the bill base
    move([V_(16, j) for j in range(5)], (0.0, 0.0, -0.020))       # hooked bill tip (whole tip ring drops)
    move([V_(15, 0)], (0.0, 0.0, 0.010))           # culmen: the bill's ridge arches
    move([V_(12, 2), V_(13, 2)], (0.012, 0.0, 0.0))   # cheek plane wider under the eye
    move([V_(7, 4)], (0.0, -0.035, -0.015))        # breastbone keel juts forward
    move([V_(8, 4)], (0.0, -0.025, 0.0))
    move([V_(4, 0), V_(5, 0)], (0.0, 0.0, 0.015))  # hip/rump top squarer
    flatten([V_(6, 2), V_(6, 3), V_(7, 2), V_(7, 3)])   # rib-cage side: one plane
    near = lambda p, r: verts_where(bm, lambda c: (c - Vector(p)).length < r)
    # needle faces (techqa slivers < 6 deg): fatten the spar rings and blunt the tips
    for key, sc in (('fingerL', 1.35), ('finger2L', 1.9), ('tipL', 3.2)):
        vs = near(J[key], 0.06 if key != 'tipL' else 0.02)
        scale(vs, sc, J[key])
    tail_tip = near((0, 1.0, 0.215), 0.03)
    scale(tail_tip, (2.2, 1.0, 2.2), (0, 1.0, 0.215))
    sh = sorted(bm.verts, key=lambda v: (v.co - Vector((0.24, -0.43, 0.70))).length)[:4]
    move(sh, (0.03, 0.0, 0.0))                     # shoulder ring out: its side faces were 1-degree needles
    bill_tip = near((0, -1.015, 1.03), 0.035)
    bc = centre(bill_tip); scale(bill_tip, (2.0, 1.0, 1.6), (0.0, bc.y, bc.z))   # pivot on the seam
    # --- connectivity (logged) ---
    with k.topo(bm, 'loop', 'neck: a second loop between N1 and N2 so the S-bend has three rings to deform'):
        loopcut(bm, edge_near(bm, (P(9, 2) + P(10, 2)) / 2), t=0.5)
    with k.topo(bm, 'loop', 'chest base of the neck: a loop between B3 and N1 so the neck root bends without collapsing'):
        loopcut(bm, edge_near(bm, (P(8, 2) + P(9, 2)) / 2), t=0.5)
    f1, f2, ft = (Vector(J[x]) for x in ('fingerL', 'finger2L', 'tipL'))
    with k.topo(bm, 'loop', 'wing finger: a knuckle loop halfway along the long spar (its quads were needles)'):
        loopcut(bm, edge_near(bm, (f1 + f2) / 2), t=0.5)
    with k.topo(bm, 'loop', 'wing finger tip: a loop halfway to the tip (needle quads, and the tip flexes)'):
        loopcut(bm, edge_near(bm, (f2 + ft) / 2), t=0.5)
    with k.topo(bm, 'loop', 'tail tip: a loop halfway along the last tail segment (needle quads; the tip flicks)'):
        loopcut(bm, edge_near(bm, (P(0, 2) + P(1, 2)) / 2), t=0.5)
    with k.topo(bm, 'inset', 'eye socket on the skull side under the brow'):
        f = face_near(bm, (P(12, 1) + P(12, 2) + P(13, 1) + P(13, 2)) / 4, n=(1, 0, 0))
        inset(bm, [f], 0.35, -0.010)
    commit(body, bm)
    if os.environ.get('RW_DEBUG'):
        t = bm.copy(); bmesh.ops.triangulate(t, faces=list(t.faces))
        for f in t.faces:
            vs = [v.co for v in f.verts]
            angs = [(vs[(i + 1) % 3] - vs[i]).angle(vs[(i + 2) % 3] - vs[i], 0) for i in range(3)]
            if min(angs) < math.radians(6):
                c = f.calc_center_median(); say('NEEDLE', tuple(round(x, 3) for x in c), round(math.degrees(min(angs)), 1))


META['keep_valleys'] = lambda c: abs(c[0]) > 0.08 and abs(c[1] + 0.73) < 0.07 and 1.13 < c[2] < 1.30

PAL = {'plumage': '#2c3346', 'membrane': '#6a3f9a', 'bill': '#1c1c22', 'billtip': '#d8cfb8',
       'eye': '#f0a020', 'shank': '#6e665e', 'horn': '#e4dcc8'}


def tube(name, pts, radii, n=4, flat=1.0, mirror=True, up=(0, 0, 1)):
    """A tapered closed tube along pts (last point = the tip). flat squashes the section across `up`."""
    bm = bmesh.new()
    pts = [Vector(p) for p in pts]
    rows = []
    for i, (p, r) in enumerate(zip(pts[:-1], radii)):
        a = (pts[i + 1] - pts[max(i - 1, 0)]).normalized()
        u = Vector(up) - a * a.dot(Vector(up))
        if u.length < 1e-3:
            u = Vector((1, 0, 0)) - a * a.x
        u.normalize(); w = a.cross(u).normalized()
        rows.append(ring(bm, [p + (u * math.cos(t) * r + w * math.sin(t) * r * flat)
                              for t in (2 * math.pi * (q + 0.5) / n for q in range(n))]))
    for a_, b_ in zip(rows, rows[1:]):
        bridge(bm, a_, b_, closed=True)
    tip = bm.verts.new(pts[-1])
    for q in range(n):
        bm.faces.new([rows[-1][q], rows[-1][(q + 1) % n], tip])
    cap(bm, list(reversed(rows[0])))
    return object_from_bm(name, bm, mirror=mirror)


def slab(name, pts, t, mirror=True, normal=None):
    """A thin closed plate on a polygon (pts), thickness t along its best-fit normal (or `normal`)."""
    A = np.array([list(p) for p in pts])
    n = Vector(normal) if normal else Vector(np.linalg.svd(A - A.mean(0))[2][-1])
    n.normalize()
    bm = bmesh.new()
    top = ring(bm, [Vector(p) + n * t / 2 for p in pts])
    bot = ring(bm, [Vector(p) - n * t / 2 for p in pts])
    cap(bm, top); cap(bm, list(reversed(bot)))
    bridge(bm, top, bot, closed=True)
    return object_from_bm(name, bm, mirror=mirror)


def lens(name, pts, t, mirror=True):
    """A closed sail with no thin side walls: the rim is shared, a centre vertex bulges t each way."""
    A = np.array([list(p) for p in pts])
    n = Vector(np.linalg.svd(A - A.mean(0))[2][-1]).normalized()
    c = Vector(A.mean(0))
    bm = bmesh.new()
    rim = ring(bm, pts)
    a, b = bm.verts.new(c + n * t), bm.verts.new(c - n * t)
    for i in range(len(rim)):
        bm.faces.new([rim[i], rim[(i + 1) % len(rim)], a])
        bm.faces.new([rim[(i + 1) % len(rim)], rim[i], b])
    return object_from_bm(name, bm, mirror=mirror)


def body_rule(c, n, i):
    if c.y < -0.965 and c.z > 0.95:
        return 'billtip'
    if c.y < -0.83 and c.z > 0.95:
        return 'bill'
    if c.z < 0.215 and 0.1 < abs(c.x) < 0.3:
        return 'shank'
    return 'plumage'


def stage3(k, body):
    paint(body, PAL, body_rule)
    out = []

    def add(ob, key):
        paint(ob, PAL, lambda c, n, i: key); out.append(ob)

    # wing membrane: a sail from the arm and finger to the flank, scalloped trailing edge
    add(lens('membrane', [(0.36, -0.46, 0.50), (0.43, -0.53, 0.21), (0.465, -0.30, 0.36), (0.44, 0.05, 0.66),
                          (0.35, 0.40, 0.92), (0.36, 0.25, 0.72), (0.38, 0.29, 0.60), (0.34, 0.15, 0.55),
                          (0.345, 0.14, 0.49), (0.21, 0.00, 0.62), (0.18, -0.38, 0.70)], 0.03), 'membrane')
    w0 = Vector((0.44, -0.55, 0.17))
    for nm, e in (('spar2', (0.38, 0.29, 0.60)), ('spar3', (0.345, 0.14, 0.49))):
        pts = [w0.lerp(Vector(e), f) for f in (0.0, 0.3, 0.6, 0.88, 1.0)]
        add(tube(nm, pts, [.036, .032, .027, .021], n=3), 'plumage')
    add(tube('thumb', [(0.445, -0.56, 0.13), (0.45, -0.60, 0.08), (0.44, -0.65, 0.03)], [.022, .014]), 'horn')
    # talons: three forward toes and a hind toe
    for nm, a, b, r in (('toe_mid', (0.18, -0.17, 0.03), (0.18, -0.40, 0.012), .022),
                        ('toe_in', (0.15, -0.14, 0.03), (0.10, -0.35, 0.012), .021),
                        ('toe_out', (0.21, -0.14, 0.03), (0.27, -0.34, 0.012), .021),
                        ('toe_back', (0.18, -0.07, 0.025), (0.18, 0.12, 0.012), .021)):
        m = Vector(a).lerp(Vector(b), 0.6) + Vector((0, 0, 0.012))
        add(tube(nm, [a, m, b], [r, r * 0.7], flat=0.7), 'shank')
    # horns: swept back and up from the skull top
    add(tube('horn', [(0.07, -0.64, 1.25), (0.12, -0.54, 1.33), (0.17, -0.43, 1.37), (0.21, -0.33, 1.44)],
             [.038, .026, .015], n=5), 'horn')
    # eye: a low diamond proud of the socket
    bm = edit(body)
    ef = max((f for f in bm.faces if abs(f.calc_center_median().y + 0.73) < 0.06 and f.calc_center_median().z > 1.15
              and f.normal.x > 0.5), key=lambda f: f.normal.x)
    c, nn = ef.calc_center_median(), ef.normal.copy()
    bm.free()
    add(tube('eye', [c - nn * 0.012, c + nn * 0.004, c + nn * 0.018], [.034, .024], n=6, up=(0, -1, 0)), 'eye')
    # hackles: shaggy blades off the throat and nape
    hk = [(P(10, 3), (0.05, -0.3, -1)), (P(9, 3), (0.05, -0.4, -1)), (P(11, 3), (0.1, -0.3, -1)),
          (P(10, 2), (0.4, -0.1, -1)), (P(11, 2), (0.4, 0.2, -1)), (P(11, 1), (0.2, 1.0, -0.6)),
          (P(12, 1), (0.3, 1.0, -0.3))]
    for i, (b, d) in enumerate(hk):
        b = Vector(b); d = Vector(d).normalized()
        inward = Vector((-b.x * 0.35, 0, 0))
        add(tube(f'hackle{i}', [b + inward - d * 0.03, b + d * 0.05, b + d * 0.13], [.03, .018], n=3, flat=0.45), 'bill')
    # dorsal spines (midline, no mirror): graded blades from the neck base to the tail
    for i, (st, h) in enumerate(((8, .09), (7, .10), (6, .085), (5, .07), (4, .055), (3, .04), (2, .03))):
        b = P(st, 0); t_ = _tan(st); N = Vector((0, t_.z, -t_.y))
        tipp = b + N * h + Vector((0, 0.5 * h, 0))
        add(tube(f'spine{i}', [b - N * 0.02, b + N * h * 0.4, tipp], [.035, .024], flat=0.5,
                 mirror=False, up=(0, 1, 0)), 'membrane')
    # tail fin: an upper and a lower lobe, each rooted in the tail
    add(slab('fin_up', [(0, 0.80, 0.225), (0, 0.92, 0.31), (0, 1.05, 0.45), (0, 1.00, 0.29), (0, 1.08, 0.22),
                        (0, 0.98, 0.215)], 0.02, mirror=False, normal=(1, 0, 0)), 'membrane')
    add(slab('fin_lo', [(0, 0.86, 0.205), (0, 0.97, 0.205), (0, 1.03, 0.10), (0, 0.93, 0.165)], 0.02,
             mirror=False, normal=(1, 0, 0)), 'membrane')
    return out


def stage4(k, body, pieces):
    rig = armature([
        ('hips', (0, 0.20, 0.47), (0, -0.14, 0.58), None),
        ('chest', (0, -0.14, 0.58), (0, -0.48, 0.71), 'hips'),
        ('neck1', (0, -0.48, 0.71), (0, -0.62, 0.92), 'chest'),
        ('neck2', (0, -0.62, 0.92), (0, -0.62, 1.08), 'neck1'),
        ('head', (0, -0.62, 1.08), (0, -0.92, 1.12), 'neck2'),
        ('tail1', (0, 0.20, 0.47), (0, 0.42, 0.33), 'hips'),
        ('tail2', (0, 0.42, 0.33), (0, 0.62, 0.255), 'tail1'),
        ('tail3', (0, 0.62, 0.255), (0, 0.82, 0.225), 'tail2'),
        ('tail4', (0, 0.82, 0.225), (0, 1.0, 0.215), 'tail3'),
        ('thigh.L', (0.16, -0.05, 0.49), (0.21, -0.08, 0.30), 'hips'),
        ('shin.L', (0.21, -0.08, 0.30), (0.195, 0.0, 0.205), 'thigh.L'),
        ('tarsus.L', (0.195, 0.0, 0.205), (0.18, -0.10, 0.05), 'shin.L'),
        ('foot.L', (0.18, -0.10, 0.05), (0.18, -0.30, 0.01), 'tarsus.L'),
        ('arm.L', (0.17, -0.42, 0.73), (0.37, -0.47, 0.47), 'chest'),
        ('fore.L', (0.37, -0.47, 0.47), (0.44, -0.56, 0.14), 'arm.L'),
        ('finger.L', (0.44, -0.56, 0.14), (0.44, 0.05, 0.66), 'fore.L'),
        ('fingertip.L', (0.44, 0.05, 0.66), (0.34, 0.42, 0.95), 'finger.L'),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 24: {'chest': (2, 0, 0), 'neck1': (-3, 0, 0), 'head': (3, 8, 0), 'tail2': (0, 0, 3)},
                       48: {}})
    stepL = {'thigh.L': (14, 0, 0), 'thigh.R': (-12, 0, 0), 'tarsus.R': (-10, 0, 0), 'neck1': (4, 0, 0),
             'head': (-4, 0, 0), 'tail2': (0, 0, 4)}
    liftR = {'tarsus.R': (-25, 0, 0), 'shin.R': (15, 0, 0), 'neck1': (-3, 0, 0), 'head': (3, 0, 0)}
    stepR = {'thigh.R': (14, 0, 0), 'thigh.L': (-12, 0, 0), 'tarsus.L': (-10, 0, 0), 'neck1': (4, 0, 0),
             'head': (-4, 0, 0), 'tail2': (0, 0, -4)}
    liftL = {'tarsus.L': (-25, 0, 0), 'shin.L': (15, 0, 0), 'neck1': (-3, 0, 0), 'head': (3, 0, 0)}
    clip(rig, 'move', {1: stepL, 9: liftR, 17: stepR, 25: liftL, 32: stepL})
    clip(rig, 'attack', {
        1: {},
        12: {'neck1': (-14, 0, 0), 'neck2': (-8, 0, 0), 'head': (8, 0, 0), 'arm.L': (0, 0, 14), 'arm.R': (0, 0, -14),
             'chest': (-4, 0, 0)},
        20: {'neck1': (22, 0, 0), 'neck2': (12, 0, 0), 'head': (-10, 0, 0), 'arm.L': (0, 0, 18), 'arm.R': (0, 0, -18),
             'chest': (6, 0, 0)},
        30: {'neck1': (6, 0, 0), 'neck2': (3, 0, 0), 'arm.L': (0, 0, 8), 'arm.R': (0, 0, -8)},
        40: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)

