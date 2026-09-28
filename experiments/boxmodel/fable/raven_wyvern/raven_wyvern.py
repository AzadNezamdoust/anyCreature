"""Raven-wyvern (fable): a raven-headed wyvern, box-modelled in four stages.

Stage 1: one trunk of 5-vert half-rings (tail tip -> bill tip) whose rings are
slices perpendicular to a hand-drawn centreline (a long reptile tail, a deep
keeled body, an S-neck, a raven skull and bill). Out of the trunk:
  - bird legs (drumstick, reversed hock, scaled shank, foot box, 3+1 toes) from
    a 2-face patch on the lower flank at the hips;
  - folded wing forelimbs from a 2-face patch on the upper flank at the shoulder:
    upper arm back along the flank to the elbow, forearm up and forward to a
    high wrist knob, one long finger back over the body to past the tail root.
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='raven_wyvern', model='fable', engine_glb='example/gallery/raven_wyvern.glb')

# ----------------------------------------------------------------------------- skeleton
J = dict(
    hips=(0.0, 0.20, 0.64), spine=(0.0, 0.02, 0.66), chest=(0.0, -0.22, 0.72), neck0=(0.0, -0.38, 0.88),
    neck1=(0.0, -0.50, 1.04), neck2=(0.0, -0.53, 1.20), head=(0.0, -0.66, 1.27), bill=(0.0, -1.17, 1.08),
    tail0=(0.0, 0.36, 0.58), tail1=(0.0, 0.55, 0.46), tail2=(0.0, 0.75, 0.35), tail3=(0.0, 0.94, 0.31),
    tailtip=(0.0, 1.12, 0.38),
    hipL=(0.16, 0.10, 0.52), hockL=(0.19, 0.24, 0.20), ankleL=(0.195, 0.08, 0.065), toeL=(0.20, -0.10, 0.02),
    shoulderL=(0.19, -0.16, 0.80), elbowL=(0.29, 0.18, 0.79), wristL=(0.25, -0.29, 1.21),
    finger0L=(0.255, -0.02, 1.13), finger1L=(0.255, 0.20, 1.11), fingertipL=(0.19, 0.98, 0.52),
)

# ----------------------------------------------------------------------------- trunk rings
# half-ring = [top seam, upper side, side, lower side, bottom seam]; shape = (x fraction of W, s along T->B)
TAIL = ((0.90, 0.22), (1.00, 0.52), (0.80, 0.82))
BODY = ((0.78, 0.14), (1.00, 0.45), (0.64, 0.83))
NECK = ((0.80, 0.18), (1.00, 0.50), (0.80, 0.82))
HEAD = ((0.92, 0.10), (1.00, 0.45), (0.72, 0.86))
BILL = ((0.60, 0.18), (1.00, 0.55), (0.75, 0.85))
HA = (-0.93, -0.36)                       # the head axis (y, z), occiput -> bill tip
TRUNK = [  # name, centre (y, z), tangent (y, z) head-ward, half-depth up, down, half-width W, shape
    ('t0', (1.12, 0.38), (-1, -0.35), .02, .02, .02, TAIL),
    ('t1', (0.94, 0.31), (-1, 0.0), .04, .035, .045, TAIL),
    ('t2', (0.75, 0.35), (-1, 0.35), .06, .055, .075, TAIL),
    ('t3', (0.55, 0.46), (-1, 0.50), .085, .08, .105, TAIL),
    ('t4', (0.36, 0.58), (-1, 0.42), .11, .10, .145, TAIL),
    ('h0', (0.22, 0.64), (-1, 0.20), .18, .18, .20, BODY),
    ('h1', (0.08, 0.65), (-1, 0.05), .24, .24, .225, BODY),
    ('h2', (-0.06, 0.66), (-1, 0.0), .26, .26, .235, BODY),
    ('c0', (-0.19, 0.69), (-1, 0.10), .27, .24, .225, BODY),
    ('c1', (-0.29, 0.76), (-1, 0.45), .24, .19, .20, BODY),
    ('c2', (-0.37, 0.90), (-0.6, 0.8), .17, .15, .16, NECK),
    ('n0', (-0.48, 1.00), (-0.6, 0.8), .125, .12, .13, NECK),
    ('n1', (-0.56, 1.11), (-0.3, 0.95), .11, .105, .12, NECK),
    ('n2', (-0.53, 1.22), (-0.2, 0.98), .105, .09, .115, NECK),
    ('n3', (-0.58, 1.30), (-0.85, 0.53), .10, .11, .115, NECK),
    ('k0', (-0.74, 1.24), HA, .115, .11, .15, HEAD),
    ('k1', (-0.83, 1.22), HA, .125, .12, .17, HEAD),
    ('k2', (-0.92, 1.19), HA, .115, .10, .14, HEAD),
    ('b0', (-0.96, 1.17), HA, .065, .055, .07, BILL),
    ('b1', (-1.05, 1.145), HA, .05, .04, .05, BILL),
    ('b2', (-1.13, 1.11), HA, .032, .022, .03, BILL),
    ('b3', (-1.185, 1.075), (-0.55, -0.85), .012, .008, .012, BILL),
]


def sec(c, t, du, dd, W, shape):
    """The 5 half-ring points of a trunk slice perpendicular to tangent t at centre c."""
    n = Vector((0.0, t[1], -t[0])).normalized()          # the slice's up direction
    c = Vector((0.0, c[0], c[1]))
    T, B = c + n * du, c - n * dd
    pts = [T]
    for fx, s in shape:
        p = T.lerp(B, s)
        pts.append(Vector((fx * W, p.y, p.z)))
    pts.append(B)
    return pts


def rp(name, i):
    """The stage-1 position of vertex i (0 top .. 4 bottom) of trunk ring `name`."""
    spec = next(r[1:] for r in TRUNK if r[0] == name)
    return sec(*spec)[i]


def face_of(vs):
    s = set(vs)
    return next(f for f in vs[0].link_faces if set(f.verts) == s)


def ext(bm, faces, old, new_pts):
    """E then G: extrude the region, place the copies of `old` (its boundary, in order) at new_pts."""
    pos = [v.co.copy() for v in old]
    r = extrude(bm, faces)
    nv = r['verts']
    new = [min(nv, key=lambda v: (v.co - p).length) for p in pos]
    assert len(set(new)) == len(new), 'ext: ambiguous vertex match'
    for v, p in zip(new, new_pts):
        v.co = Vector(p)
    return new, r['faces']


def chain(bm, faces, old, secs):
    rings = []
    for pts in secs:
        old, faces = ext(bm, faces, old, pts)
        rings.append(old)
    return rings, faces


# ----------------------------------------------------------------------------- legs
def hexs(c, d, hf, ho, wf=0.72):
    """A 6-sided limb section at centre c, perpendicular to the (y, z) direction d: [FO, O, BO, BI, I, FI]."""
    c = Vector(c)
    d = Vector((0.0, d[0], d[1])).normalized()
    f = Vector((0.0, d.z, -d.y))
    if f.y > 0:
        f = -f
    o = Vector((1.0, 0.0, 0.0))
    return [c + f * hf + o * ho * wf, c + o * ho, c - f * hf + o * ho * wf,
            c - f * hf - o * ho * wf, c - o * ho, c + f * hf - o * ho * wf]


LEG = [hexs((0.185, 0.11, 0.34), (0.15, -1.0), 0.130, 0.100),    # drumstick
       hexs(J['hockL'], (-0.25, -1.0), 0.056, 0.050),            # reversed hock
       hexs(J['ankleL'], (-0.3, -1.0), 0.050, 0.046),            # ankle / foot top
       hexs((0.20, 0.08, 0.0), (0.0, -1.0), 0.066, 0.058)]       # sole
TOES = [  # foot-box wall (hex indices), direction, length, knuckle w/h, tip w/h
    (5, 0, (0.0, -1.0), 0.17, 0.024, 0.045, 0.012, 0.022),
    (0, 1, (math.sin(math.radians(35)), -math.cos(math.radians(35))), 0.14, 0.022, 0.042, 0.011, 0.02),
    (4, 5, (-math.sin(math.radians(30)), -math.cos(math.radians(30))), 0.13, 0.022, 0.042, 0.011, 0.02),
    (2, 3, (0.0, 1.0), 0.09, 0.02, 0.04, 0.011, 0.02)]


def toe(bm, wall, dirn, L, w1, h1, w2, h2):
    """Extrude one toe out of a foot-box wall [P, Q, Q', P'] (top, top, sole, sole)."""
    P, Q, Qs, Ps = wall
    f = face_of(wall)
    t = Vector((dirn[0], dirn[1], 0.0)).normalized()
    s = Vector((-t.y, t.x, 0.0))
    if s.dot(Q.co - P.co) < 0:
        s = -s
    c0 = (P.co + Q.co + Qs.co + Ps.co) / 4
    c0.z = 0.0
    old, faces = [P, Q, Qs, Ps], [f]
    for frac, w, h in ((0.5, w1, h1), (1.0, w2, h2)):
        c = c0 + t * L * frac
        old, faces = ext(bm, faces, old, [c - s * w + Vector((0, 0, h)), c + s * w + Vector((0, 0, h)), c + s * w, c - s * w])
    return old


def toe_tip(i):
    a_, b_, dirn, L = TOES[i][:4]
    c0 = (LEG[2][a_] + LEG[2][b_] + LEG[3][a_] + LEG[3][b_]) / 4
    c0.z = 0.0
    t = Vector((dirn[0], dirn[1], 0.0)).normalized()
    return c0 + t * L, t


def build_leg(bm, R):
    h0, h1, h2 = R['h0'], R['h1'], R['h2']
    old = [h2[2], h1[2], h0[2], h0[3], h1[3], h2[3]]            # FO O BO BI I FI
    faces = [face_of([h1[2], h2[2], h2[3], h1[3]]), face_of([h0[2], h1[2], h1[3], h0[3]])]
    rings, _ = chain(bm, faces, old, LEG)
    ftop, fbot = rings[2], rings[3]
    wall = lambda a, b: [ftop[a], ftop[b], fbot[b], fbot[a]]
    for a_, b_, dirn, L, w1, h1, w2, h2 in TOES:
        toe(bm, wall(a_, b_), dirn, L, w1, h1, w2, h2)


# ----------------------------------------------------------------------------- wings
def bar(c, axis, rz, rx):
    """A keeled 6-sided bone section perpendicular to axis: [TI, T, TO, BO, B, BI] (inner = -x)."""
    c, a = Vector(c), Vector(axis).normalized()
    u = Vector((0, 0, 1)) - a * a.z
    u.normalize()
    o = a.cross(u).normalized()
    if o.x < 0:
        o = -o
    return [c + u * rz * 0.55 - o * rx, c + u * rz, c + u * rz * 0.55 + o * rx,
            c - u * rz * 0.55 + o * rx, c - u * rz, c - u * rz * 0.55 - o * rx]


def sail(c, axis, rz, rx, drop, t):
    """A folded-wing section: the finger bone on top (ridge T, bone bottom TI/TO), the membrane
    hanging `drop` below it, 2t thick at its lower edge. Same order as bar()."""
    c, a = Vector(c), Vector(axis).normalized()
    u = Vector((0, 0, 1)) - a * a.z
    u.normalize()
    o = a.cross(u).normalized()
    if o.x < 0:
        o = -o
    lean = o * drop * 0.2                                  # the membrane drapes inward over the flank
    return [c + u * rz * 0.2 - o * rx, c + u * rz, c + u * rz * 0.2 + o * rx,
            c - u * (rz + drop) + o * t - lean, c - u * (rz + drop + 0.01) - lean, c - u * (rz + drop) - o * t - lean]


ARM = [((0.275, -0.01, 0.81), (0.15, 1, -0.05), .050, .036), ((0.285, 0.09, 0.79), (0.05, 1, 0), .048, .034),
       (J['elbowL'], (0, 1, 0), .044, .032)]
FORE_AX = (0, -0.72, 0.69)
FORE = [((0.265, 0.03, 0.93), .048, .036), ((0.26, -0.10, 1.04), .045, .034), ((0.255, -0.22, 1.15), .042, .032),
        (J['wristL'], .042, .036)]
FINGER = [(J['finger0L'], (0, 1, -0.05), .040, .032, .04, .015),        # wrist end: membrane just begins
          (J['finger1L'], (0, 1, -0.25), .040, .030, .12, .015),        # concave
          ((0.245, 0.36, 1.05), (0, 1, -0.45), .036, .028, .28, .015),  # first hanging finger tip
          ((0.235, 0.50, 0.96), (-0.04, 1, -0.6), .032, .025, .14, .014),   # concave
          ((0.22, 0.64, 0.83), (-0.05, 1, -0.7), .028, .022, .26, .013),    # second finger tip
          ((0.205, 0.80, 0.66), (-0.06, 1, -0.7), .022, .017, .12, .012)]   # concave, to the tip
FINGER_TIP = (J['fingertipL'], (-0.06, 1, -0.7), .014, .010)


def build_wing(bm, R):
    h2, c0, c1 = R['h2'], R['c0'], R['c1']
    old = [c1[1], c0[1], h2[1], h2[2], c0[2], c1[2]]            # -> TI T TO BO B BI
    faces = [face_of([c0[1], c1[1], c1[2], c0[2]]), face_of([h2[1], c0[1], c0[2], h2[2]])]
    C = sum((v.co for v in old), Vector()) / 6
    nrm = (faces[0].normal + faces[1].normal).normalized()
    A0 = [C + (v.co - C) * 0.85 + nrm * 0.05 for v in old]         # the deltoid: the patch pushed out
    # the tube bends from "out" to "back" about Z: the patch's front verts go to the OUTER side
    # of the bend, so the bar order is [TO, T, TI, BI, B, BO]
    turn = lambda p: [p[2], p[1], p[0], p[5], p[4], p[3]]
    A, _ = chain(bm, faces, old, [A0] + [turn(bar(c, ax, rz, rx)) for c, ax, rz, rx in ARM])
    # forearm: out of the top faces of the upper arm between its 2nd and 3rd bar section
    a2, a3 = A[2], A[3]
    old = [a2[2], a2[1], a2[0], a3[0], a3[1], a3[2]]              # TI T TO TO T TI
    faces = [face_of([a2[2], a2[1], a3[1], a3[2]]), face_of([a2[1], a2[0], a3[0], a3[1]])]
    F, _ = chain(bm, faces, old, [list(reversed(bar(c, FORE_AX, rz, rx))) for c, rz, rx in FORE])
    # finger: out of the top faces of the forearm between its 2nd and 3rd section (F rings: BI B BO TO T TI)
    f2, f3 = F[1], F[2]
    old = [f2[5], f2[4], f2[3], f3[3], f3[4], f3[5]]
    faces = [face_of([f2[5], f2[4], f3[4], f3[5]]), face_of([f2[4], f2[3], f3[3], f3[4]])]
    secs = [list(reversed(sail(c, ax, rz, rx, drop, t))) for c, ax, rz, rx, drop, t in FINGER]
    secs.append(list(reversed(bar(*FINGER_TIP))))
    G, _ = chain(bm, faces, old, secs)
    return A, F, G


# ----------------------------------------------------------------------------- stage 1
def stage1(k):
    bm = bmesh.new()
    R = {name: ring(bm, sec(*spec)) for name, *spec in TRUNK}
    names = [r[0] for r in TRUNK]
    for a, b in zip(names, names[1:]):
        bridge(bm, R[a], R[b])
    cap(bm, R[names[0]])
    cap(bm, list(reversed(R[names[-1]])))
    recalc_normals(bm)
    build_leg(bm, R)
    build_wing(bm, R)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ----------------------------------------------------------------------------- stage 2
def vn(bm, name, i):
    return vert_near(bm, rp(name, i))


def stage2(k, body):
    bm = edit(body)
    bm.normal_update()
    # ---- the eye: a socket inset in the upper-side face between the skull ring k1 and the face ring k2
    eye_face = face_of([vn(bm, 'k1', 1), vn(bm, 'k2', 1), vn(bm, 'k2', 2), vn(bm, 'k1', 2)])
    n_out = eye_face.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the upper-side face between skull and face rings'):
        inner = inset(bm, [eye_face], 0.32, depth=0.0)
    for v in inner[0].verts:
        v.co -= n_out * 0.022
    # ---- the brow: the upper edge of the eye face overhangs the socket (out, forward, a touch down)
    for nm, d in (('k1', (0.022, -0.005, -0.012)), ('k2', (0.028, -0.01, -0.018))):
        vn(bm, nm, 1).co += Vector(d)
    # ---- the gape: the bill's side line pressed in, running back to a mouth corner under the eye
    for nm, d in (('b2', (-0.006, 0, 0.003)), ('b1', (-0.012, 0, 0.004)), ('b0', (-0.016, 0, 0.0)),
                  ('k2', (-0.012, 0.015, -0.02))):
        vn(bm, nm, 2).co += Vector(d)
    # ---- one deliberate cheek/jaw plane under the eye, occiput to mouth corner
    flatten([vn(bm, 'k0', 2), vn(bm, 'k0', 3), vn(bm, 'k1', 2), vn(bm, 'k1', 3), vn(bm, 'k2', 3)])
    # ---- hock: a supporting loop each side of the joint ring so the bend keeps its volume; the
    # thigh-side loop flares as the feather cuff ending the drumstick, the shank-side loop is slim
    dr, hk, an = ([vert_near(bm, p) for p in LEG[j]] for j in (0, 1, 2))
    for a_, b_, t, sc in ((0, 1, 0.80, 1.12), (1, 2, 0.25, 0.65)):
        pa, pb = LEG[a_][1], LEG[b_][1]
        e = edge_near(bm, (pa + pb) / 2)
        with k.topo(bm, 'loop', 'hock: a supporting loop %s the joint ring' % ('above' if a_ == 0 else 'below')):
            nv = loopcut(bm, e, t=t, near=vert_near(bm, pa))
        scale(nv, sc)
    # ---- legs (repair): a fuller drumstick tucked up under the belly, a slim shank below the hock (the
    # loop above at 0.65), a slimmer ankle, and a sharp heel: the hock's back verts out and pinched
    scale(dr, (1.15, 1.15, 1.0))
    move(dr, (0, 0, 0.015))
    scale(an, (0.82, 0.82, 1.0))
    move(hk[2:4], (0, 0.02, 0))
    hk[2].co.x -= 0.008
    hk[3].co.x += 0.008
    # ---- ventral line: the belly tucks up behind the keel
    for nm, d in (('h1', (0, 0, 0.025)), ('h0', (0, 0, 0.03)), ('t4', (0, 0, 0.02))):
        vn(bm, nm, 4).co += Vector(d)
    # ---- tech: the membrane's lower edge is keeled (its ridge 2.5 cm below the edge verts) so the
    # edge strips are not needle triangles; the finger-tip and tail-tip rings opened up for the same reason
    for i, (c, ax, rz, rx, drop, t) in enumerate(FINGER):
        pts = sail(c, ax, rz, rx, drop, t)
        u = (Vector(pts[1]) - Vector(pts[4])).normalized()
        low = [vert_near(bm, pts[j]) for j in (3, 4, 5)]
        if i > 0:                                   # not at the wrist: that edge sits over the forearm root
            low[1].co -= u * 0.035
        if i >= 4:                                  # the last two bone strips: a taller ridge
            vert_near(bm, pts[1]).co += u * 0.015
        if i in (2, 4):                             # the hanging tips lean in less: the spars must clear the flank
            move(low, (0.025 if i == 2 else 0.02, 0, 0))
    tip = [vert_near(bm, p) for p in bar(*FINGER_TIP)]
    scale(tip, 2.5)
    move(tip, (0.0, -0.05, 0.03))
    t0v = [vn(bm, 't0', i) for i in range(5)]
    scale(t0v, (1.0, 1.0, 1.7))
    for i in (1, 2, 3):
        t0v[i].co.x *= 1.8
    # ---- the wing root: the deltoid's upper-back vertex sat on the line between its neighbours (a needle
    # triangle that folds over in the attack); lifted so the stub's top is a convex ridge
    vert_near(bm, (0.233, -0.075, 0.858)).co += Vector((0.004, 0.0, 0.014))
    b3v = [vn(bm, 'b3', i) for i in range(5)]
    scale(b3v, 1.8, pivot=(0.0, rp('b3', 2).y, rp('b3', 2).z))
    commit(body, bm)


# ----------------------------------------------------------------------------- stage 3
PAL = {'plumage': '#4f546c', 'dark': '#383c4b', 'under': '#626890', 'membrane': '#7a5ab8', 'horn': '#2e2a2e',
       'bone': '#d9cfb5', 'amber': '#f0a020', 'shank': '#6e665e'}   # shank: grey-brown legs; the pupil is horn


def frame3(axis, up=(0, 0, 1)):
    a = Vector(axis).normalized()
    u = Vector(up) - a * a.dot(Vector(up))
    if u.length < 1e-6:
        u = Vector((1, 0, 0)) - a * a.x
    u.normalize()
    return a, u, a.cross(u).normalized()


def poly_ring(bm, p, d, r, sides, up=(0, 0, 1)):
    a, u, w = frame3(d, up)
    return ring(bm, [Vector(p) + (u * math.cos(t) + w * math.sin(t)) * r
                     for t in (math.radians(360.0 * j / sides + 180.0 / sides) for j in range(sides))])


def tube(bm, pts, radii, sides=6, up=(0, 0, 1)):
    """A closed faceted tube through pts, radius radii[i] at each point. Returns its faces."""
    rings = []
    for i, p in enumerate(pts):
        d = Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])
        rings.append(poly_ring(bm, p, d, radii[i], sides, up))
    fs = []
    for r0, r1 in zip(rings, rings[1:]):
        fs += bridge(bm, r0, r1, closed=True)
    fs.append(bm.faces.new(list(reversed(rings[0]))))
    fs.append(bm.faces.new(rings[-1]))
    return fs


def spike(bm, root, tip, r, sides=6, mid=0.45, midr=0.85, bend=(0, 0, 0), up=(0, 0, 1)):
    """A pointed faceted cone: base ring, a mid ring (pushed by bend), one tip vertex. Returns faces."""
    root, tip = Vector(root), Vector(tip)
    m = root.lerp(tip, mid) + Vector(bend)
    b = poly_ring(bm, root, m - root, r, sides, up)
    mm = poly_ring(bm, m, tip - root, r * midr, sides, up)
    tp = bm.verts.new(tip)
    fs = bridge(bm, b, mm, closed=True)
    fs += [bm.faces.new([mm[i], mm[(i + 1) % sides], tp]) for i in range(sides)]
    fs.append(bm.faces.new(list(reversed(b))))
    return fs


def blade(bm, root, tip, side, w, t, mid=0.4, midw=1.1, bend=(0, 0, 0)):
    """A thick faceted blade / feather clump: diamond section (w wide, t thick), wider at mid, a point."""
    root, tip = Vector(root), Vector(tip)
    ax = (tip - root).normalized()
    th = ax.cross(Vector(side)).normalized()
    sd = th.cross(ax).normalized()
    m = root.lerp(tip, mid) + Vector(bend)
    b = ring(bm, [root + sd * w, root + th * t, root - sd * w, root - th * t])
    mm = ring(bm, [m + sd * w * midw, m + th * t, m - sd * w * midw, m - th * t])
    tp = bm.verts.new(tip)
    fs = bridge(bm, b, mm, closed=True)
    fs += [bm.faces.new([mm[i], mm[(i + 1) % 4], tp]) for i in range(4)]
    fs.append(bm.faces.new(list(reversed(b))))
    return fs


def piece(name, bm, keymap, mirror=True):
    """keymap: [(faces, key)]. Object from bm, painted by face membership."""
    idx = {}
    bm.faces.index_update()
    for fs, key in keymap:
        for f in fs:
            idx[f.index] = key
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {k_: PAL[k_] for k_ in sorted(set(idx.values()))}, lambda c, n, i: idx[i])
    return ob


def flood(bm, seed, stop):
    """Faces connected to `seed` without crossing an edge whose two verts are both in `stop`."""
    out, todo = {seed}, [seed]
    while todo:
        f = todo.pop()
        for e in f.edges:
            if e.verts[0] in stop and e.verts[1] in stop:
                continue
            for g in e.link_faces:
                if g not in out:
                    out.add(g)
                    todo.append(g)
    return out


BONE = [(c[1], c[2], rz) for c, ax, rz, rx, drop, t in FINGER] + [(FINGER_TIP[0][1], FINGER_TIP[0][2], FINGER_TIP[2])]


def bone_z(y):
    """(centre z, half-height) of the finger bone at y, along the locked finger path."""
    for (y0, z0, r0), (y1, z1, r1) in zip(BONE, BONE[1:]):
        if y <= y1:
            t = max(0.0, (y - y0) / (y1 - y0))
            return z0 + (z1 - z0) * t, r0 + (r1 - r0) * t
    return BONE[-1][1], BONE[-1][2]


def socket_face(bm):
    cand = [f for f in bm.faces if len(f.verts) == 4 and all(v.co.x > 0.1 for v in f.verts)
            and -0.97 < f.calc_center_median().y < -0.76 and 1.12 < f.calc_center_median().z < 1.34
            and f.normal.x > 0.3]
    return min(cand, key=lambda f: f.calc_area())


def regions(bm):
    """Face-index -> palette key for the base, plus the wing / finger / leg face sets."""
    wing_stop = {vert_near(bm, rp(r, i)) for r in ('h2', 'c0', 'c1') for i in (1, 2)}
    leg_stop = {vert_near(bm, rp(r, i)) for r in ('h0', 'h1', 'h2') for i in (2, 3)}
    fb = [Vector(p) for p in bar(FORE[1][0], FORE_AX, FORE[1][1], FORE[1][2])[:3]] + \
         [Vector(p) for p in bar(FORE[2][0], FORE_AX, FORE[2][1], FORE[2][2])[:3]]
    finger_stop = {vert_near(bm, p) for p in fb}
    tipf = face_near(bm, Vector(FINGER_TIP[0]) + Vector((0, -0.05, 0.03)))
    wing = flood(bm, tipf, wing_stop)
    finger = flood(bm, tipf, finger_stop)
    leg = flood(bm, face_near(bm, (0.20, 0.08, 0.0), n=(0, 0, -1)), leg_stop)
    sock = socket_face(bm)
    key = {}
    for f in bm.faces:
        c, n = f.calc_center_median(), f.normal
        if f is sock:
            key[f.index] = 'horn'
        elif f in finger:
            zc, rz = bone_z(c.y)
            key[f.index] = 'membrane' if c.z < zc - rz * 0.3 - 0.004 else 'dark'
        elif f in wing:
            key[f.index] = 'plumage' if any(v in wing_stop for v in f.verts) else 'dark'
        elif f in leg:
            key[f.index] = 'plumage' if c.z > J['hockL'][2] + 0.03 else 'shank'   # slate thigh, lighter shank
        elif c.y < -1.10:
            key[f.index] = 'bone'                       # the bill's tip
        elif c.y < -0.93:
            key[f.index] = 'horn'                       # the bill
        elif n.z < -0.35 or (c.y < -0.33 and n.y < -0.55 and c.z < 1.15):
            key[f.index] = 'under'                      # belly, breast and throat
        elif n.z > 0.45 and c.z > 0.95 and c.y < -0.55:
            key[f.index] = 'dark'                       # crown and nape
        elif n.z > 0.55 and -0.4 < c.y < 0.9:
            key[f.index] = 'dark'                       # the saddle
        else:
            key[f.index] = 'plumage'
    return key, wing, finger, leg, sock


def hexprism(bm, c, nrm, r, depth, up=(0, 0, 1)):
    c, nrm = Vector(c), Vector(nrm).normalized()
    front = poly_ring(bm, c, nrm, r, 6, up)
    back = poly_ring(bm, c - nrm * depth, nrm, r * 0.9, 6, up)
    fs = bridge(bm, front, back, closed=True)
    fs.append(bm.faces.new(list(reversed(front))))
    fs.append(bm.faces.new(back))
    return fs


def sail_pt(i, f, out=0.008):
    """A point on the outer membrane surface of finger section i, f of the way from the bone bottom
    to the (keeled) lower edge, pushed `out` along +x."""
    c, ax, rz, rx, drop, t = FINGER[i]
    p = sail(c, ax, rz, rx, drop, t)
    u = (Vector(p[1]) - Vector(p[4])).normalized()
    lo = Vector(p[4]) - u * 0.035 + (Vector(p[3]) - Vector(p[4])) * 0.4
    return Vector(p[2]).lerp(lo, f) + Vector((out, 0, 0))


HACKLES = [  # root (on the throat, found by nearest-surface), tip, half-width, top thickness
    ((0.030, -0.655, 1.110), (0.045, -0.605, 0.905), 0.045, 0.032),   # medial, under the jaw
    ((0.085, -0.625, 1.120), (0.120, -0.570, 0.935), 0.040, 0.030),   # lateral, under the jaw corner
    ((0.050, -0.630, 1.020), (0.065, -0.555, 0.845), 0.038, 0.028)]   # lower, shingled under the first


def clump(bm, tree, root, tip, w, th):
    """A bold wedge feather clump: a roof-topped section (lit top faces, a keel under), widest at a
    third, one tip. Its root ring is sunk into the nearest body surface upstream of the root."""
    loc, N = tree.find_nearest(root)[:2]
    A = (tip - loc).normalized()
    U = (N - A * A.dot(N)).normalized()
    S = A.cross(U).normalized()
    p0 = loc - N * 0.006 - A * 0.03
    rings = []
    for f, sc in ((0.0, 0.55), (0.35, 1.0), (0.70, 0.62)):
        c = p0.lerp(tip, f)
        rings.append(ring(bm, [c + S * w * sc * (1.1 if f else 1), c + U * th * sc, c - S * w * sc * (1.1 if f else 1),
                               c - U * th * 0.8 * sc]))
    tp = bm.verts.new(tip)
    fs = []
    for r0, r1 in zip(rings, rings[1:]):
        fs += bridge(bm, r0, r1, closed=True)
    fs += [bm.faces.new([rings[-1][i], rings[-1][(i + 1) % 4], tp]) for i in range(4)]
    fs.append(bm.faces.new(list(reversed(rings[0]))))
    return fs


SPINE = [(-0.25, 0.34), (-0.12, 0.31), (0.03, 0.28), (0.19, 0.23), (0.36, 0.17)]   # (ridge y, height)


SPARS = [((0, 0.16), (2, 0.10), (2, 0.97)),        # root in the finger bone, bend (clear of the elbow),
         ((0, 0.05), (3, 0.12), (4, 0.97))]        # tip on the membrane edge


def bulb(bm, c, a, rings, sides=6):
    """A closed faceted knob along axis a: rings = [(offset along a, radius)]."""
    rs = [poly_ring(bm, Vector(c) + a * o, a, r, sides) for o, r in rings]
    fs = []
    for r0, r1 in zip(rs, rs[1:]):
        fs += bridge(bm, r0, r1, closed=True)
    fs.append(bm.faces.new(list(reversed(rs[0]))))
    fs.append(bm.faces.new(rs[-1]))
    return fs


def spar_curve(tree, p0, p1, p2, n=10):
    """Points on the body's outer (+x) surface along a quadratic curve p0 -> (p1) -> p2 in (y, z):
    one soft bend. Returns the surface points and their normals."""
    pts, nrms = [], []
    for j in range(n):
        t = j / (n - 1)
        q = p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t
        hit = tree.ray_cast(Vector((0.6, q.y, q.z)), Vector((-1, 0, 0)))
        if hit[0] is None:
            pts.append(Vector((0.25, q.y, q.z))); nrms.append(Vector((1, 0, 0)))
        else:
            pts.append(hit[0].copy()); nrms.append(hit[1].copy() if hit[1].x > 0 else Vector((1, 0, 0)))
    return pts, nrms


def spar3(bm, pts, nrms, r0, taper, sink0=0.02):
    """A 3-sided finger spar on the surface points: ridge out along the normal (it casts a shadow line
    on the membrane), base edge sunk; radius r0 tapering to taper*r0; the root ring sunk in the bone."""
    rings, m = [], len(pts)
    for j, (p, nv) in enumerate(zip(pts, nrms)):
        r = r0 * (1 - (1 - taper) * j / (m - 1))
        a = (pts[min(j + 1, m - 1)] - pts[max(j - 1, 0)]).normalized()
        u = (nv - a * a.dot(nv)).normalized()
        s = a.cross(u).normalized()
        c = p + u * (r * 0.25 if j else -sink0)
        rings.append(ring(bm, [c + u * r, c - u * r * 0.5 + s * r * 0.866, c - u * r * 0.5 - s * r * 0.866]))
    fs = []
    for q0, q1 in zip(rings, rings[1:]):
        fs += bridge(bm, q0, q1, closed=True)
    fs.append(bm.faces.new(list(reversed(rings[0]))))
    fs.append(bm.faces.new(rings[-1]))
    return fs


def spar_path(tree, samples, out=0.008, inside0=0.014):
    """Spar centre points that hug the membrane: each (y, z) sample (plus a midpoint between
    neighbours) is ray-cast onto the body's outer surface and pushed `out` along +x; the first
    point sits inside the finger bone so the spar grows out of it."""
    yz = []
    for a, b_ in zip(samples, samples[1:]):
        yz += [(a.y, a.z), ((a.y + b_.y) / 2, (a.z + b_.z) / 2)]
    yz.append((samples[-1].y, samples[-1].z))
    pts = []
    for j, (y, z) in enumerate(yz):
        hit = tree.ray_cast(Vector((0.6, y, z)), Vector((-1, 0, 0)))
        p = hit[0].copy() if hit[0] is not None else Vector((0.25, y, z))
        pts.append(p + Vector((-inside0 if j == 0 else out, 0, 0)))
    return pts


def stage3(k, body):
    bm = edit(body)
    bm.normal_update()
    key, wing, finger, leg, sock = regions(bm)
    sc, sn = sock.calc_center_median().copy(), sock.normal.copy()
    bm.free()
    paint(body, PAL, lambda c, n, i: key[i])
    pieces = []

    # ---- eye: an amber disc proud of the socket, an ink pupil ahead and a touch down, a bone glint
    b = bmesh.new()
    look = (sn + Vector((0, -0.45, -0.12))).normalized()
    iris = hexprism(b, sc + sn * 0.008, look, 0.050, 0.030)
    pup = hexprism(b, sc + sn * 0.017 + Vector((0, -0.008, -0.004)), look, 0.026, 0.012)
    glint = hexprism(b, sc + sn * 0.023 + Vector((0, -0.002, 0.012)), look, 0.008, 0.006)
    pieces.append(piece('eye', b, [(iris, 'amber'), (pup, 'horn'), (glint, 'bone')]))

    # ---- horns: two main horns swept back and up off the crown, two cheek horns behind the eye
    b = bmesh.new()
    main = spike(b, (0.10, -0.80, 1.28), (0.26, -0.415, 1.405), 0.055, mid=0.4, midr=0.8, bend=(0.03, 0, 0.035))  # raked back 15 deg more, tips out
    cheek = spike(b, (0.12, -0.76, 1.22), (0.185, -0.68, 1.265), 0.028, mid=0.4, midr=0.85, bend=(0.005, 0, 0.008))  # half length
    pieces.append(piece('horns', b, [(main, 'horn'), (cheek, 'horn')]))

    # ---- dorsal spines: five blades graded large to small along the ridge, neck base to tail root, spacing
    # varied, raked back 30 deg from vertical, bases sunk; wing-frame near-black
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    b = bmesh.new()
    ds = []
    for y, h in SPINE:
        hit = tree.ray_cast(Vector((0.001, y, 2.0)), Vector((0, 0, -1)))
        p0, n = hit[0], hit[1]
        up = Vector((0, 0, 1))                                  # raked 30 deg back from vertical
        ax = Vector((0, math.sin(math.radians(30)), math.cos(math.radians(30))))
        root = p0 - up * 0.035
        ds += blade(b, root, root + ax * (h + 0.035), (0, 1, 0), h * 0.25, 0.022, mid=0.35, midw=0.85)
    pieces.append(piece('spines', b, [(ds, 'horn')], mirror=False))

    # ---- hackles: the raven's throat ruff, three bold overlapping wedge clumps per side hanging from
    # the throat under the jaw, tips down and back, roots sunk into the neck (shingled: each root sits
    # under the clump above it, the top roots under the jaw)
    b = bmesh.new()
    hk = []
    for root, tip, w, th in HACKLES:
        hk += clump(b, tree, Vector(root), Vector(tip), w, th)
    pieces.append(piece('hackles', b, [(hk, 'under')]))

    # ---- wing: a solid knuckle capping the wrist knob with the thumb claw seated in it; two tapered
    # 3-sided finger spars, each with one soft bend, riding the membrane from the finger root to a
    # hanging tip on the membrane edge
    b = bmesh.new()
    wr = Vector(J['wristL'])
    fa = Vector(FORE_AX).normalized()
    knuckle = bulb(b, wr, fa, [(-0.05, 0.040), (0.0, 0.056), (0.035, 0.036)])
    thumb = spike(b, wr + fa * 0.01, wr + Vector((0.025, -0.14, 0.11)), 0.026, mid=0.45, bend=(0, 0, 0.02))
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    spars = []
    for (i0, f0), (i1, f1), (i2, f2) in SPARS:
        pts, nrms = spar_curve(tree, sail_pt(i0, f0), sail_pt(i1, f1), sail_pt(i2, f2))
        spars += spar3(b, pts, nrms, 0.022, 0.4)
    pieces.append(piece('wingbones', b, [(knuckle, 'horn'), (thumb, 'horn'), (spars, 'horn')]))

    # ---- talons: one hooked claw per toe
    b = bmesh.new()
    cl = []
    for i in range(4):
        tp, t = toe_tip(i)
        r0 = tp - t * 0.018 + Vector((0, 0, 0.011))
        cl += spike(b, r0, r0 + t * 0.075 + Vector((0, 0, -0.014)), 0.0095, mid=0.45, midr=0.85, bend=(0, 0, 0.012))
    pieces.append(piece('claws', b, [(cl, 'horn')]))

    # ---- tail fan: three thick vanes per side fanning back from the tail tip
    b = bmesh.new()
    fan = []
    for root, tip, w in (((0.012, 1.05, 0.38), (0.05, 1.34, 0.50), 0.045), ((0.02, 1.06, 0.37), (0.15, 1.29, 0.36), 0.04),
                         ((0.018, 1.04, 0.35), (0.12, 1.25, 0.22), 0.036)):
        fan += blade(b, root, tip, (0, 0, 1), w, 0.018, mid=0.45, midw=1.25)
    pieces.append(piece('tailfan', b, [(fan, 'membrane')]))
    return pieces


# ----------------------------------------------------------------------------- stage 4
BONES = [('hips', (0, 0.28, 0.62), (0, 0.08, 0.65), None),
         ('chest', (0, 0.08, 0.65), (0, -0.22, 0.72), 'hips', True),
         ('neck0', (0, -0.22, 0.72), (0, -0.46, 0.98), 'chest', True),
         ('neck1', (0, -0.46, 0.98), (0, -0.55, 1.16), 'neck0', True),
         ('neck2', (0, -0.55, 1.16), (0, -0.62, 1.29), 'neck1', True),
         ('head', (0, -0.62, 1.29), (0, -0.95, 1.17), 'neck2', True),
         ('bill', (0, -0.95, 1.17), (0, -1.18, 1.08), 'head', True),
         ('tail0', (0, 0.28, 0.62), (0, 0.55, 0.46), 'hips'),
         ('tail1', (0, 0.55, 0.46), (0, 0.75, 0.35), 'tail0', True),
         ('tail2', (0, 0.75, 0.35), (0, 0.94, 0.31), 'tail1', True),
         ('tail3', (0, 0.94, 0.31), (0, 1.12, 0.38), 'tail2', True),
         ('fan', (0, 1.12, 0.38), (0, 1.30, 0.46), 'tail3', True),
         ('thigh.L', J['hipL'], J['hockL'], 'hips'),
         ('shin.L', J['hockL'], J['ankleL'], 'thigh.L', True),
         ('foot.L', J['ankleL'], (0.20, -0.06, 0.02), 'shin.L', True),
         ('toes.L', (0.20, -0.06, 0.02), (0.20, -0.20, 0.02), 'foot.L', True),
         ('upperarm.L', (0.20, -0.17, 0.80), J['elbowL'], 'chest'),
         ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
         ('finger0.L', J['wristL'], (0.245, 0.36, 1.05), 'forearm.L', True),
         ('finger1.L', (0.245, 0.36, 1.05), (0.22, 0.64, 0.83), 'finger0.L', True),
         ('finger2.L', (0.22, 0.64, 0.83), J['fingertipL'], 'finger1.L', True)]
WING_B = {'upperarm', 'forearm', 'finger0', 'finger1', 'finger2'}
LEG_B = {'thigh', 'shin', 'foot', 'toes'}


def clean_weights(body, rig):
    """Bone heat bleeds the folded wing into the flank and the thighs into the belly: wing bones
    only on wing verts, leg bones only on leg verts (each side), fan off the body."""
    from bmkit import _bone_segments, _seg_dist
    bm = edit(body)
    sets = {}
    for sx, sd in ((1, 'L'), (-1, 'R')):
        m = lambda p: Vector((p[0] * sx, p[1], p[2]))
        wstop = {vert_near(bm, m(rp(r, i))) for r in ('h2', 'c0', 'c1') for i in (1, 2)}
        lstop = {vert_near(bm, m(rp(r, i))) for r in ('h0', 'h1', 'h2') for i in (2, 3)}
        wf = flood(bm, face_near(bm, m(Vector(FINGER_TIP[0]) + Vector((0, -0.05, 0.03)))), wstop)
        lf = flood(bm, face_near(bm, m((0.20, 0.08, 0.0)), n=(0, 0, -1)), lstop)
        sets['wing.' + sd] = {v.index for f in wf for v in f.verts} - {v.index for v in wstop}
        sets['leg.' + sd] = {v.index for f in lf for v in f.verts} - {v.index for v in lstop}
    bm.free()
    gname = {g.index: g.name for g in body.vertex_groups}
    segs = _bone_segments(rig)
    limb = {b + '.' + s for b in WING_B | LEG_B for s in 'LR'}
    for v in body.data.vertices:
        allowed = set(segs) - {'fan'} - limb
        for s in 'LR':
            if v.index in sets['wing.' + s]:
                allowed = {b + '.' + s for b in WING_B} | {'chest'}
                break
            if v.index in sets['leg.' + s]:
                allowed = {b + '.' + s for b in LEG_B} | {'hips'}
                break
        for g in list(v.groups):
            if gname[g.group] not in allowed and g.weight > 0:
                body.vertex_groups[gname[g.group]].remove([v.index])
        if sum(g.weight for g in v.groups if gname[g.group] in segs) <= 1e-4:
            p = body.matrix_world @ v.co
            nm = min(allowed & set(segs), key=lambda n: _seg_dist(p, *segs[n]))
            body.vertex_groups[nm].add([v.index], 1.0, 'REPLACE')
    # the deltoid ring: a chest / upper-arm blend, so a wing spread shears two face rings, not one
    P = [rp('c1', 1), rp('c0', 1), rp('h2', 1), rp('h2', 2), rp('c0', 2), rp('c1', 2)]
    C = sum(P, Vector()) / 6
    nrm = (P[2] - P[0]).cross(P[3] - P[0]).normalized()
    if nrm.x < 0:
        nrm = -nrm
    bm = edit(body)
    for sx, sd in ((1, 'L'), (-1, 'R')):
        for p in P:
            q = C + (p - C) * 0.85 + nrm * 0.05
            i = vert_near(bm, Vector((q.x * sx, q.y, q.z))).index
            for g in list(body.data.vertices[i].groups):
                body.vertex_groups[gname[g.group]].remove([i])
            body.vertex_groups['chest'].add([i], 0.6, 'REPLACE')
            body.vertex_groups['upperarm.' + sd].add([i], 0.4, 'REPLACE')
    bm.free()


def sym(keys):
    """Mirror every .L key onto .R (X kept, Y and Z negated) unless .R is given."""
    out = {}
    for f, d in keys.items():
        e = dict(d)
        for b, r in d.items():
            if b.endswith('.L') and b[:-2] + '.R' not in d:
                e[b[:-2] + '.R'] = (r[0], -r[1], -r[2])
        out[f] = e
    return out


def stage4(k, body, pieces):
    rig = armature(BONES, roll='auto')
    skin(body, rig)
    clean_weights(body, rig)
    P = {p.name.replace('piece_', ''): p for p in pieces}
    for nm in ('eye', 'horns'):
        bind(P[nm], rig, bone='head')
    bind(P['tailfan'], rig, bone='fan')
    for nm in ('hackles', 'spines', 'wingbones', 'claws'):
        bind(P[nm], rig, body=body)

    # idle: breathing, a slow head turn, the tail swaying, wings settling
    clip(rig, 'idle', sym({1: {}, 12: {'chest': (2, 0, 0), 'neck1': (0, 0, 6), 'head': (0, 0, 8), 'tail1': (0, 0, 6),
                                       'tail2': (0, 0, 6), 'upperarm.L': (0, 0, 3)},
                           24: {'chest': (3, 0, 0), 'neck1': (0, 0, 8), 'head': (-3, 0, 10), 'tail1': (0, 0, 3), 'tail2': (0, 0, 8)},
                           36: {'chest': (1, 0, 0), 'neck1': (0, 0, -5), 'head': (3, 0, -8), 'tail1': (0, 0, -6), 'tail2': (0, 0, -6),
                                'upperarm.L': (0, 0, -2)},
                           48: {}}))

    # move: a stalking stride, head bobbing like a raven's, tail swinging
    def step(th, sh, ft, thr, shr, ftr, bob, sway):
        return {'thigh.L': (th, 0, 0), 'shin.L': (sh, 0, 0), 'foot.L': (ft, 0, 0),
                'thigh.R': (thr, 0, 0), 'shin.R': (shr, 0, 0), 'foot.R': (ftr, 0, 0),
                'hips': (0, 0, sway), 'chest': (bob, 0, 0), 'neck0': (-bob * 2, 0, 0), 'neck2': (bob * 2, 0, 0),
                'tail1': (0, 0, -sway * 2), 'tail2': (0, 0, -sway * 2)}
    clip(rig, 'move', {1: step(25, -10, 8, -20, 15, -18, 2, 4), 7: step(5, 5, -4, -5, 30, -30, -2, 0),
                       13: step(-20, 15, -18, 25, -10, 8, 2, -4), 19: step(-5, 30, -30, 5, 5, -4, -2, 0),
                       25: step(25, -10, 8, -20, 15, -18, 2, 4)})

    # attack: a threat display, then the lunge: the neck coils back with the wings half-spread, then the
    # head drives forward and down with the wings flared and the tail whipping
    clip(rig, 'attack', sym({1: {},
                             8: {'chest': (-6, 0, 0), 'neck0': (-12, 0, 0), 'neck1': (-10, 0, 0), 'head': (8, 0, 0),
                                 'upperarm.L': (0, 0, 16), 'forearm.L': (0, 0, -22), 'finger0.L': (0, 0, -18), 'tail0': (-8, 0, 0)},
                             14: {'chest': (8, 0, 0), 'neck0': (14, 0, 0), 'neck1': (8, 0, 0), 'neck2': (4, 0, 0), 'head': (-8, 0, 0),
                                  'upperarm.L': (0, 0, 17), 'forearm.L': (0, 0, -38), 'finger0.L': (0, 0, -30), 'finger1.L': (0, 0, -20),
                                  'tail0': (10, 0, 0), 'tail1': (8, 0, 0), 'thigh.L': (-8, 0, 0)},
                             20: {'chest': (6, 0, 0), 'neck0': (10, 0, 0), 'neck1': (6, 0, 0), 'neck2': (3, 0, 0), 'head': (-6, 0, 0),
                                  'upperarm.L': (0, 0, 17), 'forearm.L': (0, 0, -31), 'finger0.L': (0, 0, -28), 'finger1.L': (0, 0, -14),
                                  'tail0': (6, 0, 0)},
                             32: {}}))
    return rig


run(META, stage1, stage2, stage3, stage4)
