import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit'))
sys.path.insert(0, KIT)
from bmkit import *
import parts as PT

# minotaur (biped, bull head), t7 hand box model. ONE upright spine loft of 13-vertex half rings (front seam ->
# back seam), crotch -> poll, each ring drawn from 5 control points (front seam, front corner, side, back corner,
# back seam) so the sections have planes. The bull muzzle, the jaw step and the trapezius hump are in the loft.
# Arms are extruded from a 2 x 3 face region of the shoulder side (C0-C2: the deltoid cap is the torso's own
# shoulder line), legs from a 2 x 4 region of the pelvis underside, ears from 2 faces of the skull side, the tail
# from the rump's back seam face (its seam walls removed: the mirror closes it). Hands and hooves are parts-library
# pieces (hand_three_finger, hoof_cloven) welded onto the wrist and ankle rings before the lock.
META = dict(creature='minotaur', model='opus', stage1_tris=(1800, 4800), total_tris=(2600, 6500),
            closeups=[('head', (0.0, -0.22, 2.06), 0.34, 'hero'),
                      ('shoulder', (0.52, -0.02, 1.48), 0.30, 'hero'),
                      ('hand', (0.78, -0.12, 0.78), 0.20, 'hero'),
                      ('hoof', (0.25, -0.02, 0.12), 0.24, 'hero')])

# the skeleton (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.03, 0.92), spine=(0.0, 0.0, 1.18), chest=(0.0, 0.02, 1.45), neck=(0.0, 0.10, 1.70),
    head=(0.0, 0.02, 1.90), top=(0.0, -0.12, 2.26),
    shoulder=(0.47, 0.03, 1.52), elbow=(0.655, 0.035, 1.10), wrist=(0.765, -0.07, 0.86), hand=(0.80, -0.15, 0.70),
    hipL=(0.20, 0.03, 0.86), knee=(0.215, -0.03, 0.48), ankle=(0.25, 0.05, 0.20), toe=(0.25, -0.22, 0.03),
    ear=(0.18, -0.06, 2.165), eartip=(0.31, -0.04, 2.10),
    tail0=(0.0, 0.34, 1.00), tail1=(0.0, 0.43, 0.86), tail2=(0.0, 0.45, 0.70), tail3=(0.0, 0.45, 0.50),
)


# ---------------------------------------------------------------- the loft
def torso5(yf, yb, W, fx=0.62, fy=0.10, sy=0.45, bx=0.72, by=0.14):
    D = yb - yf
    return [(0.0, yf), (W * fx, yf + D * fy), (W, yf + D * sy), (W * bx, yb - D * by), (0.0, yb)]


def ring13(c5, z, rnd=0.45):
    """13 points front seam -> back seam: 3 steps per control segment, a blend of the straight chord (planes) and
    a Catmull-Rom curve (round-over), the seam ends mirrored for the tangent (the mirror stays smooth)."""
    P = [Vector((x, y)) for x, y in c5]
    G = [Vector((-P[1].x, P[1].y))] + P + [Vector((-P[3].x, P[3].y))]
    out = []
    for s in range(4):
        p0, p1, p2, p3 = G[s], G[s + 1], G[s + 2], G[s + 3]
        for u in (0.0, 1 / 3, 2 / 3):
            lin = p1.lerp(p2, u)
            cr = 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                        + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
            q = lin.lerp(cr, rnd)
            out.append((max(q.x, 0.0) if s or u else 0.0, q.y, z))
    out.append((0.0, P[4].y, z))
    return out


KEY = [   # (name, z, 5 control points (x, y)) bottom -> top, read off reference/side.png + front.png
    ('L0', 0.80, torso5(-0.10, 0.14, 0.10)),            # crotch
    ('L0b', 0.875, torso5(-0.22, 0.27, 0.29)),          # under the hips
    ('L1', 0.96, torso5(-0.27, 0.34, 0.37, bx=0.78)),   # hips / buttocks
    ('L2', 1.05, torso5(-0.31, 0.31, 0.365)),           # belt bottom
    ('B0', 1.13, torso5(-0.33, 0.27, 0.335)),           # waist (belt top)
    ('B1', 1.23, torso5(-0.34, 0.28, 0.34)),            # abdomen
    ('B2', 1.33, torso5(-0.36, 0.33, 0.37)),            # lower ribs
    ('C0', 1.43, torso5(-0.375, 0.38, 0.42)),           # pec bottom / lats
    ('C1', 1.52, torso5(-0.38, 0.41, 0.49)),            # pecs: the chest widens up and out ...
    ('C2', 1.61, torso5(-0.35, 0.43, 0.555, fx=0.6)),   # ... into the deltoid cap (the shoulder line)
    ('C3', 1.69, torso5(-0.30, 0.42, 0.52, fx=0.58)),   # shoulder top
    ('T0', 1.76, [(0, -0.265), (0.25, -0.235), (0.40, -0.05), (0.44, 0.13), (0, 0.39)]),   # trapezius slope
    # T0 / T1 use the head rings' control-point roles (front corner, jaw-angle column, trapezius column) so the
    # quads under the jaw are not sheared (r15: the old torso roles made a sliver collar under the head)
    ('T1', 1.81, [(0, -0.24), (0.17, -0.215), (0.27, -0.11), (0.41, 0.06), (0, 0.36)]),    # throat / trapezius
    ('J0', 1.85, [(0, -0.37), (0.10, -0.35), (0.21, -0.15), (0.38, 0.055), (0, 0.33)]),     # chin / jaw line
    ('J1', 1.895, [(0, -0.445), (0.11, -0.425), (0.20, -0.19), (0.34, 0.05), (0, 0.30)]),   # mouth
    ('M0', 1.95, [(0, -0.49), (0.115, -0.46), (0.20, -0.20), (0.29, 0.03), (0, 0.27)]),     # nose
    ('M1', 2.01, [(0, -0.475), (0.115, -0.445), (0.205, -0.18), (0.245, 0.02), (0, 0.235)]),  # nose top / cheeks
    ('E0', 2.07, [(0, -0.375), (0.12, -0.345), (0.205, -0.15), (0.205, 0.02), (0, 0.19)]),   # muzzle bridge
    ('E1', 2.135, [(0, -0.29), (0.135, -0.26), (0.20, -0.12), (0.185, 0.03), (0, 0.135)]),   # eyes / brow
    ('F0', 2.20, [(0, -0.25), (0.135, -0.225), (0.195, -0.10), (0.17, 0.01), (0, 0.08)]),    # forehead, horn base
    ('F1', 2.255, [(0, -0.21), (0.12, -0.19), (0.175, -0.09), (0.15, -0.01), (0, 0.035)]),   # poll ridge
    ('F2', 2.29, [(0, -0.16), (0.09, -0.15), (0.13, -0.08), (0.11, -0.03), (0, -0.01)]),     # flat skull top
]
# density: a straight in-between ring (pointwise lerp: every split face stays co-planar) where the outline bends
INSERT = ['L0b', 'L1', 'C1', 'C2', 'C3']   # a ring inserted ABOVE each of these keys


def stations():
    out = []
    for i, (nm, z, c5) in enumerate(KEY):
        out.append((nm, ring13(c5, z)))
        if nm in INSERT and i + 1 < len(KEY):
            a, b = ring13(c5, z), ring13(KEY[i + 1][2], KEY[i + 1][1])
            out.append((nm + '~', [tuple((Vector(p) + Vector(q)) / 2) for p, q in zip(a, b)]))
    return out


SECS = stations()


def P(nm):
    for n, pts in SECS:
        if n == nm:
            return [Vector(q) for q in pts]


# ---------------------------------------------------------------- limbs
def frame_chain(cs, rads, lateral=(1, 0, 0)):
    """(centre, e1, e2, r1, r2) per station: e1 the outward lateral axis across the limb, e2 front-back."""
    cs = [Vector(c) for c in cs]
    out = []
    for i, (c, (r1, r2)) in enumerate(zip(cs, rads)):
        d = (cs[min(i + 1, len(cs) - 1)] - cs[max(i - 1, 0)]).normalized()
        e2 = Vector((0, 1, 0)); e2 = (e2 - d * e2.dot(d)).normalized()
        e1 = e2.cross(d).normalized()
        if e1.dot(Vector(lateral)) < 0:
            e1 = -e1
        out.append((c, e1, e2, r1, r2))
    return out


ARM_C = [(0.545, 0.035, 1.38), (0.575, 0.04, 1.26), (0.61, 0.04, 1.17), (0.655, 0.035, 1.10),
         (0.70, 0.0, 1.01), (0.74, -0.04, 0.93), (0.765, -0.07, 0.86)]
ARM_R = [(0.12, 0.18), (0.14, 0.17), (0.12, 0.15), (0.11, 0.14), (0.125, 0.14), (0.11, 0.12), (0.085, 0.095)]
LEG_C = [(0.20, 0.03, 0.75), (0.205, 0.02, 0.66), (0.21, 0.0, 0.57), (0.215, -0.03, 0.48), (0.22, -0.01, 0.42),
         (0.225, 0.05, 0.34), (0.235, 0.06, 0.26), (0.25, 0.05, 0.20)]
LEG_R = [(0.16, 0.225), (0.16, 0.225), (0.15, 0.21), (0.125, 0.17), (0.12, 0.16), (0.125, 0.165), (0.10, 0.12),
         (0.085, 0.09)]
EAR_C = [(0.232, -0.055, 2.165), (0.27, -0.05, 2.145), (0.31, -0.045, 2.12), (0.345, -0.04, 2.10)]
EAR_R = [(0.04, 0.02), (0.042, 0.018), (0.04, 0.014), (0.008, 0.006)]   # a drooping leaf, widest past its root
TAIL = [((0.39, 0.975), 0.045, 0.042), ((0.43, 0.87), 0.033, 0.033), ((0.45, 0.72), 0.028, 0.028),
        ((0.45, 0.58), 0.026, 0.026), ((0.448, 0.50), 0.024, 0.024)]


def corner(fr, ab):
    c, e1, e2, r1, r2 = fr
    return c + e1 * ab[0] * r1 + e2 * ab[1] * r2


def region_roles(faces, lo_ring, up_ring):
    """Roles (a, b) for a face region's vertices: the boundary loop spread evenly round the unit circle in the
    region's own frame (e1 lower ring -> upper ring = the limb's outer side, e2 = +y), interior vertices inside."""
    vs = list({v for f in faces for v in f.verts})
    fs = set(faces)
    bnd = [v for v in vs if any(f not in fs for f in v.link_faces)]
    inn = [v for v in vs if v not in bnd]
    lo = [v for v in vs if v in set(lo_ring)]
    up = [v for v in vs if v in set(up_ring)]
    cen = sum((v.co for v in vs), Vector()) / len(vs)
    e1 = (sum((v.co for v in up), Vector()) / len(up) - sum((v.co for v in lo), Vector()) / len(lo)).normalized()
    e2 = Vector((0, 1, 0)); e2 = (e2 - e1 * e2.dot(e1)).normalized()
    pr = {v: ((v.co - cen).dot(e1), (v.co - cen).dot(e2)) for v in vs}
    s1 = max(abs(pr[v][0]) for v in bnd) or 1
    s2 = max(abs(pr[v][1]) for v in bnd) or 1
    ang = {v: math.atan2(pr[v][1] / s2, pr[v][0] / s1) for v in bnd}
    order = sorted(bnd, key=lambda v: ang[v])
    n = len(order)
    # even spread round the circle, its phase the best fit to the true angles (no twist: a 4-vertex row stays
    # symmetric about the region's middle)
    sx = sum(math.cos(ang[v] - 2 * math.pi * rk / n) for rk, v in enumerate(order))
    sy = sum(math.sin(ang[v] - 2 * math.pi * rk / n) for rk, v in enumerate(order))
    ph = math.atan2(sy, sx)
    roles = {}
    for rk, v in enumerate(order):
        t = ph + 2 * math.pi * rk / n
        roles[v] = (math.cos(t), math.sin(t))
    for v in inn:
        roles[v] = (0.5 * pr[v][0] / s1, 0.5 * pr[v][1] / s2)
    nrm = e1.cross(e2).normalized()
    if nrm.dot(cen - Vector((0, cen.y, cen.z))) < 0 and abs(cen.x) > 0.01:
        nrm = -nrm
    return roles, (cen, e1, e2, s1, s2, nrm)


def grow(bm, faces, roles, frames):
    for fr in frames:
        keyed = [(o.co.copy(), ab) for o, ab in roles.items()]   # by position: extrude removes interior verts
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(keyed, key=lambda q: (q[0] - v.co).length)[1]
        if isinstance(fr, dict):       # a hug ring: the root loop itself, pushed out and shrunk a little
            c, n_, out, k_ = fr['c'], fr['n'], fr['out'], fr['k']
            for v in new:
                v.co = c + (v.co - c) * k_ + n_ * out
            move(list(new), (0, 0, 0))
        else:
            for v, ab in new.items():
                v.co = corner(fr, ab)
        faces, roles = r['faces'], new
    return faces, roles


def hug_frame(info, out, k_=0.94):
    """The first limb ring: the root region's own loop pushed `out` along its normal and shrunk to k_ about its
    centre (a broad transition ring that keeps the torso's planes)."""
    cen, e1, e2, s1, s2, nrm = info
    return dict(c=cen, n=nrm, out=out, k=k_)


def one_face(bm, faces):
    """Dissolve a limb's end cap region into one n-gon (the ring a part is welded on)."""
    r = bmesh.ops.dissolve_faces(bm, faces=list(faces))
    return r['region'][0]


def hand_part():
    w = Vector(J['wrist'])
    fwd = (Vector(J['hand']) - w).normalized()
    up = Vector((1, 0, 0.0)); up = (up - fwd * up.dot(fwd)).normalized()
    return PT.hand_three_finger(origin=w + fwd * 0.03, width=0.22, forward=fwd, up=up, side=1, fingers=2, curl=0.45,
                                spread=8.0, finger_len=0.75, thumb=True, thumb_curl=0.3, knuckle=0.15,
                                wrist=(0.17, 0.10), open_root=True, name='hand')


def hoof_part():
    return PT.hoof_cloven(origin=Vector(J['ankle']) - Vector((0, 0, 0.035)), radius=0.085, height=0.165, width=0.30, length=0.37,
                          cleft=0.22, dewclaws=False, open_root=True, name='hoof')


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, _p) in enumerate(SECS)}
    rings = [ring(bm, pts) for _n, pts in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    rest = []

    def region(lo, nsp, cols):
        i = idx[lo]
        faces = [spans[i + s][c] for s in range(nsp) for c in cols]
        return faces, rings[i], rings[i + nsp]

    # arms: 2 x 3 faces of the shoulder side right under the shoulder line (C1 -> C1~ -> C2): the region's top edge
    # is the torso's widest ring, so the arm's outer wall carries the deltoid line straight down (no shelf)
    faces, lo, up = region('C1', 2, (5, 6, 7))
    roles, info = region_roles(faces, lo, up)
    fr = [hug_frame(info, 0.025, 1.0)] + frame_chain(ARM_C, ARM_R)
    faces, roles = grow(bm, faces, roles, fr)
    rr = bridge_part(hand_part(), one_face(bm, faces), bm=bm)
    if rr is not None:
        rest.append(rr)
    # legs: 2 x 4 faces of the pelvis underside (L0 -> L0b -> L0b~)
    faces, lo, up = region('L0', 2, (4, 5, 6, 7))
    roles, info = region_roles(faces, lo, up)
    fr = [(Vector(c), Vector((1, 0, 0)), Vector((0, 1, 0)), r1, r2) for c, (r1, r2) in zip(LEG_C, LEG_R)]   # level rings
    faces, roles = grow(bm, faces, roles, fr)
    rr = bridge_part(hoof_part(), one_face(bm, faces), bm=bm)
    if rr is not None:
        rest.append(rr)
    # ears: 2 faces of the skull side behind the eye (E1 -> F0, columns 6-7)
    faces, lo, up = region('E1', 1, (6, 7))
    roles, info = region_roles(faces, lo, up)
    # s4 r29: the first ear ring is the root region itself pushed 2 cm out and shrunk to 0.85 (walls lean in: no
    # knife fold above or below the ear root); the leaf widens from the second ring on
    grow(bm, faces, roles, [hug_frame(info, 0.02, 0.85)] + frame_chain(EAR_C, EAR_R, lateral=(1, 0, 0))[1:])
    # tail: the back seam face of the rump (L1 -> L1~, column 11), seam walls removed (the mirror closes it)
    i = idx['L1']
    f = spans[i][11]
    lo, up = rings[i], rings[i + 1]
    roles = {lo[12]: (0, -1), up[12]: (0, 1), lo[11]: (1, -0.6), up[11]: (1, 0.6)}
    faces = [f]
    prev = Vector((0.0, (lo[12].co.y + up[12].co.y) / 2, (lo[12].co.z + up[12].co.z) / 2))
    upv0 = Vector((0, 0, 1))
    for (cy, cz), rx, rh in TAIL:
        c = Vector((0.0, cy, cz))
        d = (c - prev).normalized()
        upv = Vector((0.0, -d.z, d.y))
        if upv.dot(upv0) < 0:          # continuity: the section never flips where the tail turns straight down
            upv = -upv
        upv0 = upv
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (ax, bh) in new.items():
            v.co = c + Vector((ax * rx, 0, 0)) + upv * bh * rh
        walls = [g for g in r['sides'] if all(abs(w.co.x) < 1e-6 for w in g.verts)]
        bmesh.ops.delete(bm, geom=walls, context='FACES')
        faces, roles, prev = r['faces'], new, c
    snap_seam(bm)
    recalc_normals(bm)
    k.meta['_rest'] = [o.name for o in rest]
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
def eye_face_centre():
    A, B_ = P('E0'), P('E1')
    return (A[3] + A[4] + B_[3] + B_[4]) / 4


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.04 and abs(c.y - ec0.y) < 0.045 and abs(c.z - ec0.z) < 0.045


def limb_edge(bm, frames, i):
    """The edge running along a limb from ring i to ring i+1 on its outer side (a loop cut across it rings the limb)."""
    va = vert_near(bm, corner(frames[i], (1, 0)))
    tb = corner(frames[i + 1], (1, 0))
    return min(va.link_edges, key=lambda e: (e.other_vert(va).co - tb).length)


def stage2(k, body):
    """Joint loops (hip, knee, elbow, shoulder, waist, neck), the eye socket, a brow over it, pec and nose planes."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table()
    af = frame_chain(ARM_C, ARM_R)
    lf = [(Vector(c), Vector((1, 0, 0)), Vector((0, 1, 0)), r1, r2) for c, (r1, r2) in zip(LEG_C, LEG_R)]
    sp = lambda nm, j=0: P(nm)[j]
    cuts = [('elbow loop: the elbow bend', lambda: limb_edge(bm, af, 3)),
            ('upper-arm loop: the shoulder swing under the deltoid', lambda: limb_edge(bm, af, 0)),
            ('knee loop: the knee bend', lambda: limb_edge(bm, lf, 2)),
            ('hip loop: the thigh swing under the kilt', lambda: limb_edge(bm, lf, 0)),
            ('waist loop: the spine bend', lambda: edge_near(bm, tuple((sp('B0') + sp('B1')) / 2)))]
    # no extra neck loop: T0 / T1 / J0 already ring the neck 4-5 cm apart (a loop between them made a sliver strip)
    for why, fe in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, fe(), t=0.5)
    # eye socket: an inset in the eye face (E0 -> E1, columns 3-4), its floor pushed in
    ec0 = eye_face_centre()
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face, its floor pushed in'):
        inner = inset(bm, [f], 0.34, 0.0)
    # owner-review fix 1 (r39): the 1.2 cm deep inset of this sheared, narrow face read as a slit pocket. A square
    # floor does not fit (the face is 3.8 cm across at its narrow side; r37/r38 tried it), so the socket is a shallow
    # 4 mm step and the lens (wider than the floor) sits on it, its ring below the surface all round.
    iv = list(inner[0].verts)
    move(iv, -fn * 0.004)
    F0, C1, C0 = P('F0'), P('C1'), P('C0')
    move([vert_near(bm, F0[j]) for j in (3, 4)], (0.006, -0.015, -0.004))     # brow ridge over the eye
    move([vert_near(bm, C1[j]) for j in (1, 2, 3)], (0.0, -0.02, 0.0))         # pec shelf
    move([vert_near(bm, C0[j]) for j in (1, 2, 3)], (0.0, -0.012, 0.012))      # pec underside
    # (s4 r25/r27 ear lifts removed in r29: the ear root is now built right in stage 1)
    # s4 r27: tail root strip: the first tail ring 1.5 cm further back so the root wall faces are not a thin band
    t0 = [v for v in bm.verts if v.co.x < 0.06 and abs(v.co.y - TAIL[0][0][0]) < 0.02 and abs(v.co.z - TAIL[0][0][1]) < 0.05]
    move(t0, (0, 0.015, 0))
    scale(t0, (1.5, 1.0, 1.2), pivot=(0.0, TAIL[0][0][0] + 0.015, TAIL[0][0][1]))   # s4 r29: as broad as the root face
    # s4 r31: the tail's next two rings thicker (1.45 / 1.3): a hexagonal rope 6 cm thick has 2 cm faces creased 60 deg,
    # read as a seam strip at the root; the root third of a bull's tail is thick anyway
    for ti, sc in ((1, 1.45), (2, 1.3)):
        (ty, tz) = TAIL[ti][0]
        tv = [v for v in bm.verts if v.co.x < 0.06 and abs(v.co.y - ty) < 0.03 and abs(v.co.z - tz) < 0.045]
        scale(tv, (sc, sc, sc), pivot=(0.0, ty, tz))
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


PAL = {'fur': '#6b4636', 'dark': '#3a2e2a', 'horn': '#e2d4b6', 'leather': '#7c5134', 'brass': '#b38b45',
       'eye': '#1a1311', 'tuft': '#4a3026'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if z < 0.075 and x > 0.06:
        return 'dark'                                                    # hooves
    if 1.875 < z < 2.03 and y < -0.40 and n.y < -0.55:
        return 'dark'                                                    # nose leather: the muzzle's front plane
    w = Vector(J['wrist']); fwd = (Vector(J['hand']) - w).normalized()
    if x > 0.6 and (Vector((x, y, z)) - w).dot(fwd) > 0.17:
        return 'dark'                                                    # the two hoof-fingers
    return 'fur'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 4 for k_ in range(8)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.3)
    for j in range(8):
        a, b = j, (j + 1) % 8
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def full_bvh(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def hit(tree, o, d, far=3.0):
    loc, nrm, _i, _d = tree.ray_cast(Vector(o), Vector(d).normalized(), far)
    return loc, nrm


def band(tree, centre, e1, e2, half_w, n_seg, sink=0.01, out=0.022, share=0.05):
    """A closed strap round the body (the ogre's crop-6 band): ray hits per angle, outer face evened and relaxed."""
    e1, e2 = Vector(e1).normalized(), Vector(e2).normalized()
    nrm = e1.cross(e2).normalized()
    bm = bmesh.new()
    ds, ts = [], []
    for s in range(n_seg):
        t = 2 * math.pi * s / n_seg
        d = e1 * math.cos(t) + e2 * math.sin(t)
        tt = []
        for side in (-1, 1):
            o = Vector(centre) + nrm * side * half_w
            loc, fn = hit(tree, o, d)
            tt.append((loc - o).length if loc is not None else 0.4)
        ds.append(d); ts.append(tt)
    tout = [[max(t[j], t[1 - j]) if abs(t[0] - t[1]) < share else t[j] for j in (0, 1)] for t in ts]
    tout = [[max(tout[s][j], 0.5 * (tout[s - 1][j] + tout[(s + 1) % n_seg][j]))
             if abs(tout[s - 1][j] - tout[(s + 1) % n_seg][j]) < 0.08 else tout[s][j] for j in (0, 1)]
            for s in range(n_seg)]
    rows = []
    for s in range(n_seg):
        d = ds[s]
        row = []
        for j, side in enumerate((-1, 1)):
            o = Vector(centre) + nrm * side * half_w
            sk = sink[j] if isinstance(sink, tuple) else sink
            row += [o + d * (ts[s][j] - sk), o + d * (tout[s][j] + out)]
        rows.append([bm.verts.new(p) for p in (row[0], row[1], row[3], row[2])])
    for s in range(n_seg):
        a, b = rows[s], rows[(s + 1) % n_seg]
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    return bm


KILT_C = Vector((0.0, 0.02, 0.0))
KILT_Z = (1.045, 0.995, 0.91, 0.82, 0.72)   # top row (sunk under the belt), belt bottom, rows ~9 cm apart (no needle
                                           # side faces), then the hem
KILT = [(-21, 21, 0.555, 0.60), (25, 61, 0.60, 0.615), (65, 101, 0.615, 0.62), (105, 141, 0.62, 0.62),
        (145, 171, 0.62, 0.625)]        # (deg from the front toward +x) and hem z at its two edges; back gap = tail


def kilt_panel(tree, a0, a1, h0, h1, side=1, ncol=4, thick=0.016, lay=0.0):
    """One leather plate of the kilt: a closed slab hanging from under the belt, clear of the hips and thighs (ray
    hits at each row + 3 cm), flaring to the hem; the top row sunk 2 cm under the belt."""
    bm = bmesh.new()
    cols = []
    for ci in range(ncol):
        th = math.radians(a0 + (a1 - a0) * ci / (ncol - 1))
        d = Vector((side * math.sin(th), -math.cos(th), 0.0))
        hem = h0 + (h1 - h0) * ci / (ncol - 1)
        if a0 < 0 < a1:
            hem = h0 + (h1 - h0) * abs(2 * ci / (ncol - 1) - 1)   # the front plate's point
        rs = []
        for zi, z in enumerate(KILT_Z + (hem,)):
            o = KILT_C + Vector((0, 0, z)) + d * 0.55     # inside the hanging arms: the rays find hip and thigh
            loc, _n = hit(tree, o, -d)
            rr = ((loc - KILT_C - Vector((0, 0, z))).length if loc is not None else 0.0)
            if zi == 0:
                r = rr - 0.02
            else:
                zp = (KILT_Z + (hem,))[zi - 1]
                r = max(rr + 0.03, rs[-1] + (0.0 if zi == 1 else 0.17 * (zp - z)))
            rs.append(r)
        rs = [rs[0]] + [r + lay for r in rs[1:]]
        out_ = [KILT_C + Vector((0, 0, z)) + d * r for z, r in zip(KILT_Z + (hem,), rs)]
        in_ = [p - d * thick for p in out_]
        cols.append(([bm.verts.new(p) for p in out_], [bm.verts.new(p) for p in in_]))
    nr = len(KILT_Z) + 1
    for ci in range(ncol - 1):
        (oa, ia), (ob, ib) = cols[ci], cols[ci + 1]
        for r in range(nr - 1):
            bm.faces.new([oa[r], oa[r + 1], ob[r + 1], ob[r]])
            bm.faces.new([ia[r], ib[r], ib[r + 1], ia[r + 1]])
        bm.faces.new([oa[-1], ia[-1], ib[-1], ob[-1]])      # hem
        bm.faces.new([oa[0], ob[0], ib[0], ia[0]])          # top (inside the body)
    for (o_, i_), flip in ((cols[0], False), (cols[-1], True)):
        for r in range(nr - 1):
            q = [o_[r], i_[r], i_[r + 1], o_[r + 1]]
            bm.faces.new(q[::-1] if flip else q)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def disc(bm, c, r, y_front, y_back, n=8):
    R0 = [bm.verts.new((c[0] + r * math.cos(t), y_back, c[2] + r * math.sin(t))) for t in [j * 2 * math.pi / n for j in range(n)]]
    R1 = [bm.verts.new((c[0] + 0.85 * r * math.cos(t), y_front, c[2] + 0.85 * r * math.sin(t))) for t in [j * 2 * math.pi / n for j in range(n)]]
    bm.faces.new(R0); bm.faces.new(R1[::-1])
    for j in range(n):
        bm.faces.new([R0[j], R0[(j + 1) % n], R1[(j + 1) % n], R1[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def stage3(k, body):
    paint(body, {kk: PAL[kk] for kk in ('fur', 'dark')}, body_rule)
    tree = full_bvh(body)
    pieces = []
    one = lambda key: (lambda c_, n_, i: key)
    # eye: a dark lens on the socket floor, proud of it
    ec = eye_face_centre()
    A_, B_ = P('E0'), P('E1')
    n = (B_[3] - A_[4]).cross(B_[4] - A_[3]).normalized()     # the eye face's own normal (outward, front-side)
    n = n if n.y < 0 else -n
    c = ec - n * 0.004                                        # owner fix 1: the socket floor's centre (was the
                                                              # nearest surface point, which fell on the rim)
    loc, fnn = hit(tree, ec + n * 0.05, -n)                   # r36: the floor's own point and normal, so the lens
    if loc is not None:                                       # ring lies parallel to the floor (a tilted ring crossed
        c, n = loc, (fnn if fnn.dot(n) > 0 else -fnn)         # it on one side and sat under it on the other)
    bm = bmesh.new()
    lens(bm, c - n * 0.006, n, 0.0235, 0.02)   # s4 r26: 2.2 -> 2.5 cm (eye L read 0.058 head); r33 2.35 in the square socket
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, one('eye'))
    pieces.append(eye)
    # horns: out from the skull's top corners, then up and forward, the tips turning in (sheet front + side)
    for sd in (1, -1):
        h = PT.horn(base=(sd * 0.15, -0.12, 2.24), length=0.50, radius=0.055, forward=(sd * 1.0, -0.15, -0.05),
                    up=(sd * -0.2, -1.0, 0.7), side=sd, curve=105.0, segs=5, sides=6, taper=1.3,   # fix 2: bends forward-up
                    name='horn' + ('L' if sd > 0 else 'R'))
        paint(h, {'horn': PAL['horn']}, one('horn'))
        pieces.append(h)
    # nose: the muzzle's front plane is the dark nose leather (painted on the base); two nostril lenses sit on it
    bm = bmesh.new()
    for sd in (1, -1):
        o = Vector((sd * 0.055, -0.3, 1.935))
        loc, nn = hit(tree, o, (0, -1, 0))
        loc, nn = hit(tree, o + Vector((0, -0.4, 0)), (0, 1, 0))
        nn = nn if nn.y < 0 else -nn
        lens(bm, loc - nn * 0.005, nn, 0.019, 0.014)   # r23: domed, its rim below the plane (no z-fight)
    nose = object_from_bm('nostrils', bm, mirror=False)
    paint(nose, {'eye': PAL['eye']}, one('eye'))
    pieces.append(nose)
    # tail tuft on the tail's end
    tuft = PT.tail_tuft(base=(0.0, 0.448, 0.52), length=0.24, radius=0.07, forward=(0, 0.05, -1), up=(0, 1, 0),
                        kind='tuft', tiers=2, sides=6, name='tuft')
    paint(tuft, {'tuft': PAL['tuft']}, one('tuft'))
    pieces.append(tuft)
    # belt and buckle
    belt = object_from_bm('belt', band(tree, (0.0, 0.0, 1.075), (1, 0, 0), (0, 1, 0), 0.045, 32,
                                         sink=(0.01, 0.0), out=0.03, share=0.15), mirror=False)
    paint(belt, {'leather': PAL['leather']}, one('leather'))
    pieces.append(belt)
    loc, _n = hit(tree, (0, -1.0, 1.075), (0, 1, 0))
    bm = bmesh.new()
    disc(bm, (0.0, 0.0, 1.075), 0.07, loc.y - 0.045, loc.y + 0.01)
    buckle = object_from_bm('buckle', bm, mirror=False)
    paint(buckle, {'brass': PAL['brass']}, one('brass'))
    pieces.append(buckle)
    # kilt plates
    for pi_, (a0, a1, h0, h1) in enumerate(KILT):
        lay = 0.022 if pi_ % 2 == 0 else 0.0     # s4 r29: alternate plates ride 2.2 cm out and overlap their
        for sd in ((1,) if a0 < 0 else (1, -1)):  # neighbours by 2.5 deg: no see-through slits between plates
            ob = object_from_bm('kilt%d%s' % (pi_, 'L' if sd > 0 else 'R'),
                                kilt_panel(tree, a0 - (2.5 if lay else 0), a1 + (2.5 if lay and a1 < 170 else 0),
                                           h0, h1, sd, lay=lay), mirror=False)
            paint(ob, {'leather': PAL['leather']}, one('leather'))
            pieces.append(ob)
    for nm in k.meta.get('_rest', []):
        o = bpy.data.objects.get(nm)
        if o is not None:
            paint(o, {'fur': PAL['fur']}, one('fur'))
            pieces.append(o)
    return pieces


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['top'], 'neck', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: slow breathing through the chest, a head turn, the ears flick, the tail swishes
    clip(rig, 'idle', {1: {},
                       12: {'chest': (2, 0, 0), 'head': (0, 0, 6), 'ear.L': (0, 0, 8), 'tail1': (0, 0, 10),
                            'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       24: {'tail1': (0, 0, -4)},
                       36: {'chest': (2, 0, 0), 'head': (0, 0, -6), 'ear.R': (0, 0, -8), 'tail1': (0, 0, -10),
                            'upperarm.L': (2, 0, 0), 'upperarm.R': (2, 0, 0)},
                       48: {}})
    # move: a heavy stride; the swinging leg folds at the knee, arms swing against the legs, the tail sways
    A, S = 11, 12
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
            'spine': (0, 0, 3), 'tail1': (0, 0, 6)},
        9: {'shin.R': (-28, 0, 0), 'foot.R': (12, 0, 0), 'thigh.R': (6, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0),
             'spine': (0, 0, -3), 'tail1': (0, 0, -6)},
        25: {'shin.L': (-28, 0, 0), 'foot.L': (12, 0, 0), 'thigh.L': (6, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0),
             'spine': (0, 0, 3), 'tail1': (0, 0, 6)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.03, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.03, 0)},
             33: {'hips': (0, 0, 0)}})
    # attack: a horn charge - rear back with the head up, then drive the horns down and forward, arms swinging back
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (-6, 0, 0), 'neck': (-8, 0, 0), 'head': (-10, 0, 0), 'upperarm.L': (10, 0, 0),
             'upperarm.R': (10, 0, 0), 'tail1': (0, 0, 10)},
        18: {'spine': (6, 0, 0), 'chest': (12, 0, 0), 'neck': (12, 0, 0), 'head': (18, 0, 0),
             'upperarm.L': (-14, 0, 0), 'upperarm.R': (-14, 0, 0), 'forearm.L': (-10, 0, 0), 'forearm.R': (-10, 0, 0)},
        26: {'spine': (4, 0, 0), 'chest': (8, 0, 0), 'neck': (8, 0, 0), 'head': (12, 0, 0)},
        36: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
