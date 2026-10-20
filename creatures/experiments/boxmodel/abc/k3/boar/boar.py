import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EYE = (0.118, -0.470, 0.500)
META = dict(creature='boar', model='opus',
            keep_valleys=lambda c: (Vector(c) - Vector((abs(c[0]), c[1], c[2]))).length < 1 and
            (Vector((abs(c[0]), c[1], c[2])) - Vector(EYE)).length < 0.05)

# the skeleton the model is built on (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.46, 0.56), spine=(0.0, 0.10, 0.60), chest=(0.0, -0.20, 0.62),
    neck=(0.0, -0.33, 0.47), head=(0.0, -0.40, 0.52), snout=(0.0, -0.66, 0.28),
    shoulderL=(0.13, -0.15, 0.46), elbowL=(0.13, -0.155, 0.21), wristL=(0.13, -0.155, 0.12),
    hoofL=(0.13, -0.17, 0.0),
    hipL=(0.13, 0.46, 0.46), stifleL=(0.13, 0.465, 0.25), hockL=(0.13, 0.535, 0.155),
    fhoofL=(0.13, 0.492, 0.0),
    tail0=(0.0, 0.56, 0.52), tail1=(0.0, 0.64, 0.33),
    earL=(0.15, -0.39, 0.64), earTipL=(0.20, -0.40, 0.78),
)

# half sections snout -> rump: (y, [v0 top seam, v1 back, v2 upper flank, v3 lower flank, v4 belly side, v5 bottom seam])
SECT = [
    (-0.665, [(0, .345), (.058, .334), (.084, .292), (.080, .245), (.052, .215), (0, .210)]),   # snout disc
    (-0.638, [(0, .345), (.058, .334), (.084, .292), (.080, .245), (.052, .215), (0, .210)]),   # disc rim
    (-0.610, [(0, .385), (.058, .374), (.080, .330), (.078, .262), (.052, .222), (0, .218)]),   # muzzle behind disc
    (-0.520, [(0, .495), (.090, .478), (.132, .405), (.135, .300), (.078, .240), (0, .232)]),   # face / jowl
    (-0.430, [(0, .625), (.095, .600), (.150, .505), (.165, .350), (.085, .268), (0, .258)]),   # brow / eye
    (-0.330, [(0, .745), (.110, .680), (.190, .545), (.195, .390), (.100, .305), (0, .298)]),   # back of head
    (-0.210, [(0, .880), (.135, .775), (.238, .570), (.205, .360), (.095, .285), (0, .280)]),   # shoulder hump
    (-0.080, [(0, .860), (.145, .765), (.243, .555), (.205, .355), (.095, .282), (0, .278)]),
    (0.080,  [(0, .800), (.135, .720), (.222, .535), (.190, .365), (.090, .295), (0, .295)]),
    (0.250,  [(0, .735), (.120, .665), (.200, .530), (.180, .375), (.080, .310), (0, .310)]),
    (0.400,  [(0, .670), (.115, .640), (.200, .520), (.190, .370), (.085, .320), (0, .320)]),   # hams / hind leg front
    (0.520,  [(0, .630), (.100, .600), (.170, .520), (.170, .380), (.080, .335), (0, .335)]),   # rump
    (0.555,  [(0, .585, -.018), (.080, .568, -.010), (.125, .505, .004), (.112, .420, -.006), (.055, .385, -.022), (0, .378, -.028)]),   # rump rounding: top and bottom recede
]
FRONT_LEG = [(0.13, -0.150, 0.22, 0.058, 0.074), (0.13, -0.150, 0.115, 0.036, 0.040),
             (0.13, -0.158, 0.060, 0.042, 0.050), (0.13, -0.165, 0.0, 0.050, 0.066)]
HIND_LEG = [(0.13, 0.465, 0.25, 0.056, 0.080), (0.13, 0.535, 0.155, 0.036, 0.042),
            (0.13, 0.500, 0.058, 0.040, 0.046), (0.13, 0.492, 0.0, 0.050, 0.060)]


def half_ring(c, r, d, n=6):
    """n points from the top seam round the +X side to the bottom seam, in the plane normal to d."""
    d = Vector(d).normalized()
    u = Vector((0, -d.z, d.y)) if d.z < 0 else Vector((0, d.z, -d.y))
    if u.z < 0:
        u = -u
    X = Vector((1, 0, 0))
    out = []
    for i in range(n):
        a = math.pi * i / (n - 1)
        p = Vector(c) + r * (math.sin(a) * X + math.cos(a) * u)
        out.append((0.0 if i in (0, n - 1) else p.x, p.y, p.z))
    return out


def grow(bm, face, corners, rings):
    """Extrude `face` once per ring. corners: the face's 4 corner positions in the order
    front-out, back-out, back-in, front-in; rings: (cx, cy, z, hx, hy) boxes, same order."""
    order = [min(face.verts, key=lambda v: (v.co - Vector(p)).length) for p in corners]
    for cx, cy, z, hx, hy in rings:
        pos = [v.co.copy() for v in order]
        r = extrude(bm, [face])
        face = r['faces'][0]
        order = [min(r['verts'], key=lambda v: (v.co - p).length) for p in pos]
        pts = [(cx + hx, cy - hy, z), (cx + hx, cy + hy, z), (cx - hx, cy + hy, z), (cx - hx, cy - hy, z)]
        for v, p in zip(order, pts):
            v.co = Vector(p)
    return face, order


def ring_pts(i):
    y, xz = SECT[i]
    return [(p[0], y + (p[2] if len(p) > 2 else 0.0), p[1]) for p in xz]


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, ring_pts(i)) for i in range(len(SECT))]
    # tail: grows out of the top of the rump, hanging down and back
    t0, t1 = Vector(J['tail0']), Vector(J['tail1'])
    d = t1 - t0
    rows.append(ring(bm, half_ring(t0 + Vector((0, -0.01, 0)), 0.028, d)))
    rows.append(ring(bm, half_ring(t0.lerp(t1, 0.5), 0.018, d)))
    rows.append(ring(bm, half_ring(t1, 0.012, d)))
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)

    def lower_flank(i):   # the v3-v4 face between sections i and i+1
        return [f for f in bm.faces if len(f.verts) == 4 and set(f.verts) == {rows[i][3], rows[i + 1][3], rows[i][4], rows[i + 1][4]}][0]

    def corners(i):
        return [rows[i][3].co.copy(), rows[i + 1][3].co.copy(), rows[i + 1][4].co.copy(), rows[i][4].co.copy()]

    # legs from the lower flank
    grow(bm, lower_flank(6), corners(6), FRONT_LEG)
    grow(bm, lower_flank(10), corners(10), HIND_LEG)

    # ears: from the v1-v2 face between brow (4) and back of head (5)
    ef = [f for f in bm.faces if len(f.verts) == 4 and set(f.verts) == {rows[4][1], rows[5][1], rows[4][2], rows[5][2]}][0]
    ec = [rows[4][1].co.copy(), rows[5][1].co.copy(), rows[5][2].co.copy(), rows[4][2].co.copy()]
    order = [min(ef.verts, key=lambda v: (v.co - p).length) for p in ec]
    pos = [v.co.copy() for v in order]
    r = extrude(bm, [ef])
    order = [min(r['verts'], key=lambda v: (v.co - p).length) for p in pos]
    place(order, [(0.110, -0.405, 0.690), (0.120, -0.365, 0.715), (0.195, -0.365, 0.630), (0.190, -0.405, 0.615)])
    pos = [v.co.copy() for v in order]
    r = extrude(bm, [r['faces'][0]])
    bmesh.ops.pointmerge(bm, verts=r['verts'], merge_co=Vector(J['earTipL']))

    snap_seam(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'neck loop between nape and shoulder hump: the head-to-body bend'):
        loopcut(bm, edge_near(bm, (0.214, -0.27, 0.557)), t=0.5)
    with k.topo(bm, 'loop', 'barrel loop behind the elbow: belly skin between fore- and mid-body stops folding in the trot'):
        loopcut(bm, edge_near(bm, (0.2325, 0.0, 0.545)), t=0.35)
    with k.topo(bm, 'loop', 'mid-back loop: the spine flex for the trot and the charge'):
        loopcut(bm, edge_near(bm, (0.211, 0.165, 0.532)), t=0.5)
    for mid, why in (((0.575, 0.47), 'tail root bend: splits the long thin tail quads'),
                     ((0.620, 0.38), 'tail mid bend: splits the long thin tail quads')):
        e = min([e for e in bm.edges if (e.verts[0].co - e.verts[1].co).length > 0.07 and
                 all(v.co.y > 0.53 and v.co.x > 1e-5 for v in e.verts)],
                key=lambda e: abs((e.verts[0].co.y + e.verts[1].co.y) / 2 - mid[0]) +
                abs((e.verts[0].co.z + e.verts[1].co.z) / 2 - mid[1]))
        with k.topo(bm, 'loop', why):
            loopcut(bm, e, t=0.5)
    with k.topo(bm, 'inset', 'eye socket under the brow'):
        f = face_near(bm, EYE, n=(1, 0, 0.3))
        inner = inset(bm, [f], 0.40, -0.012)
    # brow ridge overhangs the socket; cheek plane flattened
    move([vert_near(bm, (0.095, -0.43, 0.60))], (0.012, -0.006, 0.004))
    move([vert_near(bm, (0.150, -0.43, 0.505))], (0.006, 0.0, 0.0))
    # ears: the 2 back-face verts of the ear base ring rearward 2% of head length, so the ear has thickness edge-on
    move([vert_near(bm, (0.120, -0.365, 0.715)), vert_near(bm, (0.195, -0.365, 0.630))], (0.0, 0.007, 0.0))
    # brow ridge: the 2 verts on the socket face's top edge out 3% and forward 2% of the head width (0.30)
    move([vert_near(bm, (0.107, -0.436, 0.604)), vert_near(bm, (0.090, -0.52, 0.478))], (0.009, -0.006, 0.0))
    # neck loop pulled up into the crest line so the nape reads as one thick wedge
    for v in verts_where(bm, lambda c: abs(c.y + 0.27) < 0.02 and c.x < 1e-5 and c.z > 0.7):
        v.co.z += 0.02
    # mantle border (stage-3 paint follows it): the v1-v2 edge of the -0.08 row slants back and up,
    # so the dark shoulder ends on a raked loop edge, not a vertical one on the flank
    place([vert_near(bm, (0.243, -0.08, 0.555)), vert_near(bm, (0.145, -0.08, 0.765))],
          [(0.240, -0.150, 0.563), (0.1440, -0.062, 0.764)])
    # tail: rings widened about the tail axis, 1.5x at the root tapering to 1.2x at the tip,
    # so it has a section from every angle (not a plate edge-on)
    ta = Vector(J['tail0']) + Vector((0, -0.01, 0))
    td = Vector(J['tail1']) - ta
    for v in bm.verts:
        sv = (v.co - ta).dot(td) / td.length_squared
        c = ta + td * max(0.0, min(1.0, sv))
        if v.co.y > 0.53 and -0.02 < sv < 1.02 and (v.co - c).length < 0.035:
            v.co = c + (v.co - c) * (1.5 - 0.3 * max(0.0, min(1.0, sv)))
    # r31 legs: the wrist ring was the waist of an hourglass. Widen it to ~85% of the forearm ring and push
    # its front verts forward 1 cm (knee bump); the ring above the hoof to ~80% of the new wrist (a slim
    # straight pastern); the hind hock ring 1.2x so the cannon does not pinch. Hooves unchanged.
    for z, cy, sx, sy, fwd in ((0.115, -0.150, 1.36, 1.57, 0.010), (0.060, -0.158, 0.93, 1.0, 0.0),
                               (0.155, 0.535, 1.20, 1.25, 0.0)):
        vs = verts_where(bm, lambda c: abs(c.z - z) < 0.006 and abs(c.x - 0.13) < 0.07 and abs(c.y - cy) < 0.07)
        assert len(vs) == 4, (z, len(vs))
        for v in vs:
            v.co.x = 0.13 + (v.co.x - 0.13) * sx
            v.co.y = cy + (v.co.y - cy) * sy - (fwd if v.co.y < cy else 0.0)
    commit(body, bm)


PAL =dict(body='#6f5040', bristle='#3e2c24', snout='#b88e7e', tusk='#efe3c8', hoof='#2a201c', eye='#1a1414')
TOP = [(-0.33, .745), (-0.27, .8325), (-0.21, .88), (-0.08, .86), (0.08, .80), (0.165, .7675), (0.25, .735)]


def top_z(y):
    if y <= TOP[0][0]:
        return TOP[0][1]
    for (a, za), (b, zb) in zip(TOP, TOP[1:]):
        if y <= b:
            return za + (zb - za) * (y - a) / (b - a)
    return TOP[-1][1]


def piece(name, verts, faces, key, mirror=True):
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(p)) for p in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: PAL[key]}, lambda c, n, i: key)
    return ob


def tube(rings, tip):
    """square-section tube: rings = [(centre, r)], closed at the base, fanned to a tip point"""
    V, F = [], []
    X = Vector((1, 0, 0))
    for i, (c, r) in enumerate(rings):
        c = Vector(c)
        d = (Vector(rings[min(i + 1, len(rings) - 1)][0]) - Vector(rings[max(i - 1, 0)][0])).normalized()
        a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else X).normalized()
        b = d.cross(a).normalized()
        V += [tuple(c + r * (a * sa + b * sb)) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    n = len(rings)
    F.append([3, 2, 1, 0])
    for i in range(n - 1):
        for j in range(4):
            F.append([i * 4 + j, i * 4 + (j + 1) % 4, (i + 1) * 4 + (j + 1) % 4, (i + 1) * 4 + j])
    V.append(tuple(tip))
    t = len(V) - 1
    for j in range(4):
        F.append([(n - 1) * 4 + j, (n - 1) * 4 + (j + 1) % 4, t])
    return V, F


def stage3(k, body):
    def body_rule(c, n, i):
        if c.z < 0.05:
            return 'hoof'
        if c.y < -0.632:
            return 'snout'
        # mantle: a wedge along the spine, per face against the local spine height. Depth below the
        # spine 30% of the hump height (0.6) at the nape, 20% at the withers, thinning to the spine
        # faces only from mid-back on, so the border steps back along existing edges.
        if -0.335 < c.y < 0.165:
            if c.y < -0.21:
                dep = 0.13 + (0.12 - 0.13) * (c.y + 0.335) / 0.125   # r33: 0.18 put the nape v1-v2 quad in, a vertical edge
            elif c.y < -0.08:
                dep = 0.12 + (0.04 - 0.12) * (c.y + 0.21) / 0.13
            else:
                dep = 0.0
            if c.z > top_z(c.y) - dep or (abs(n.x) < 0.35 and n.z > 0.6 and c.z > top_z(c.y) - 0.05):
                return 'bristle'
        return 'body'
    paint(body, {kk: PAL[kk] for kk in ('body', 'bristle', 'snout', 'hoof')}, body_rule)
    out = []
    # crest: 5 blunt bristle clumps nape -> mid-back, one connected strip. Unequal heights (tallest
    # at the nape), flat two-vert tops, each leaning back ~22 deg, bases sunk into the spine.
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)

    def surf(x, y):
        hit = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] is not None else top_z(y)
    # r27: uneven pitch (lengths vary +-35%), heights on a curve (nape .6, withers 1.0, then .8/.55/.35),
    # a small low clump between the ears starts the crest at the head; back three lean further back
    def strip(clumps, lean_from):
        st = []                                # (base y, top y, height above spine, top half-width, base half-width)
        for i, (y0, L, h) in enumerate(clumps):
            hv = 0.0 if i == 0 else 0.35 * min(h, clumps[i - 1][2])    # raised valleys: one ridge, clumps overlap
            f1, f2, fb, hb = (0.55, 0.86, 0.70, 0.70) if i < lean_from else (0.60, 0.90, 0.68, 0.65)
            w = 0.045 if h < 0.04 and i == 0 else 0.075
            st.append((y0, y0, hv, max(0.020, 0.25 * hv), 0.060 if w > 0.05 else 0.040))
            st.append((y0 + 0.40 * L, y0 + f1 * L, h, 0.30 * h, w))          # long front slope, flat top,
            st.append((y0 + fb * L, y0 + f2 * L, hb * h, 0.24 * h, w))       # tip combed back over the next valley
        y_end = clumps[-1][0] + clumps[-1][1]
        st.append((y_end, y_end, 0.0, 0.020, 0.060 if len(clumps) > 1 else 0.040))
        V, F = [], []
        for yb, yt, h, wt, w in st:
            if h > 0:
                top, side_top = surf(0, yt) + h, surf(0, yt) + 0.80 * h
            else:
                top, side_top = surf(0, yt) + 0.012, surf(wt, yt) - 0.004
            V += [(0, yt, top), (wt, yt, side_top), (w, yb, surf(w, yb) - 0.012),
                  (0, yb, surf(0, yb) - 0.05)]
        for i in range(len(st) - 1):
            a, b = 4 * i, 4 * i + 4
            F += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(3)]
        F += [[0, 1, 2, 3], [len(V) - 1, len(V) - 2, len(V) - 3, len(V) - 4]]
        return V, F
    # the small nape clump between the ears is its own piece: one strip across the head/neck bend drifted
    out.append(piece('crestnape', *strip([(-0.420, 0.060, 0.034)], 9), 'bristle'))
    out.append(piece('crest', *strip([(-0.350, 0.090, 0.063), (-0.260, 0.130, 0.105), (-0.130, 0.085, 0.084),
                                      (-0.045, 0.125, 0.058), (0.080, 0.075, 0.037)], 2), 'bristle'))
    # tusks: rooted at the lower-jaw corner just behind the disc (mouth line), root sunk ~25% into the
    # jaw; sweep out ~20 deg, then up, tip just above the snout top and a little forward. Thick base.
    V, F = tube([((0.055, -0.600, 0.232), 0.030), ((0.100, -0.612, 0.248), 0.027), ((0.150, -0.628, 0.282), 0.021),
                 ((0.176, -0.640, 0.330), 0.014)], (0.180, -0.656, 0.385))
    out.append(piece('tusk', V, F, 'tusk'))
    # eye: a low-poly lens sitting in the stage-2 socket, proud of it
    me = body.data
    pf = min(me.polygons, key=lambda p: (Vector(p.center) - Vector(EYE)).length)
    n = Vector(pf.normal).normalized()
    P = Vector(pf.center) + n * 0.002
    t1 = n.cross(Vector((0, 0, 1))).normalized()
    t2 = n.cross(t1).normalized()
    rim = [P + t1 * 0.0315, P + t2 * 0.0225, P - t1 * 0.0315, P - t2 * 0.0225]   # 1.5x: ~1/7 of the head width
    Q = P - n * 0.012
    back = [Q + (r - P) * 0.7 for r in rim]
    V = [tuple(v) for v in rim + back] + [tuple(P + n * 0.009)]
    F = [[0, 1, 8], [1, 2, 8], [2, 3, 8], [3, 0, 8], [7, 6, 5, 4]] +         [[(j + 1) % 4, j, 4 + j, 4 + (j + 1) % 4] for j in range(4)]
    out.append(piece('eye', V, F, 'eye'))
    # nostrils: round (6-sided) dark discs, diameter ~25% of the snout disc, set into the disc face
    # with the front face only 0.0035 proud (under 10% of its width)
    cx, cz, r, yf, yb = 0.037, 0.283, 0.021, -0.6685, -0.650
    V = [(cx + r * math.cos(math.pi * j / 3), yy, cz + r * math.sin(math.pi * j / 3)) for yy in (yf, yb) for j in range(6)]
    F = [[5, 4, 3, 2, 1, 0], [6, 7, 8, 9, 10, 11]] + [[j, (j + 1) % 6, 6 + (j + 1) % 6, 6 + j] for j in range(6)]
    out.append(piece('nostril', V, F, 'eye'))
    # tail tuft: one blunt chunky wedge (pentagon outline, flat two-vert tip, one side ridge vertex),
    # rooted 20% into the tail tip; 10 triangles after the mirror
    t1 = Vector(J['tail1'])
    a = (t1 - Vector(J['tail0'])).normalized()
    pp = Vector((0, -a.z, a.y)) if a.z < 0 else Vector((0, a.z, -a.y))
    L = 0.130
    R = t1 - a * 0.2 * L
    V = [R, R + a * 0.30 * L - pp * 0.038, R + a * 0.95 * L - pp * 0.014,
         R + a * 0.95 * L + pp * 0.014, R + a * 0.30 * L + pp * 0.038, R + a * 0.38 * L + Vector((0.030, 0, 0))]
    V = [tuple(v) for v in V]
    F = [[0, 1, 5], [1, 2, 5], [2, 3, 5], [3, 4, 5], [4, 0, 5]]
    out.append(piece('tuft', V, F, 'bristle'))
    return out


def stage4(k, body, pieces):
    tm = tuple((Vector(J['tail0']) + Vector(J['tail1'])) / 2)
    rig = armature([
        ('spine', J['spine'], J['chest'], None),
        ('hips', J['spine'], J['hips'], 'spine'),
        ('neck', J['chest'], J['neck'], 'spine', True),
        ('head', J['neck'], J['snout'], 'neck', True),
        ('ear.L', J['earL'], J['earTipL'], 'head'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'spine'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hoof.L', J['wristL'], J['hoofL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['stifleL'], 'hips'),
        ('shin.L', J['stifleL'], J['hockL'], 'thigh.L', True),
        ('foot.L', J['hockL'], J['fhoofL'], 'shin.L', True),
        ('tail', J['tail0'], tm, 'hips'),
        ('tail2', tm, J['tail1'], 'tail', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'neck': (-6, 0, 0), 'head': (-10, 0, 0), 'tail': (0, 0, 14), 'ear.L': (8, 0, 0)},
                       24: {'neck': (-2, 0, 0), 'head': (-5, 3, 0)},
                       36: {'neck': (-6, 0, 0), 'head': (-11, -3, 0), 'tail': (0, 0, -14), 'ear.R': (8, 0, 0)},
                       48: {}})

    def A(s):
        return {'upperarm.L': (14 * s, 0, 0), 'thigh.R': (14 * s, 0, 0), 'upperarm.R': (-14 * s, 0, 0),
                'thigh.L': (-14 * s, 0, 0), 'spine': (0, 2 * s, 0), 'head': (3, 0, 0), 'tail': (0, 0, 8 * s)}

    def mid(s):
        return {('forearm.L' if s > 0 else 'forearm.R'): (-22, 0, 0), ('shin.L' if s < 0 else 'shin.R'): (20, 0, 0),
                'head': (-2, 0, 0)}
    clip(rig, 'move', {1: A(1), 7: mid(-1), 13: A(-1), 19: mid(1), 25: A(1)})
    # r29 tusk toss: wind-up held over 25-30% (head+neck down 20, chest down, hinds gathered), lunge and
    # toss held over 50-56% (root forward ~10% of body length, head+neck up 25, head rolled 10: the hook)
    down = {'spine': (-5, 0, 0), 'neck': (-8, 0, 0), 'head': (-12, 0, 0), 'thigh.L': (-12, 0, 0), 'thigh.R': (-12, 0, 0)}
    toss = {'spine': (2, 0, 0), 'neck': (10, 0, 0), 'head': (15, 10, 0), 'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0),
            'ear.L': (-10, 0, 0), 'ear.R': (-10, 0, 0)}
    clip(rig, 'attack', {1: {}, 8: down, 10: down, 16: toss, 18: toss,
                         25: {'neck': (2, 0, 0), 'head': (4, 0, 0)}, 32: {}},
         loc={1: {}, 10: {}, 16: {'spine': (0, 0.06, 0)}, 18: {'spine': (0, 0.06, 0)},
              25: {'spine': (0, 0.015, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
