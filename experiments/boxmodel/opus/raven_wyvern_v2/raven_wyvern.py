"""Raven-wyvern v2: a raven-headed wyvern, box-modelled from a new stage 1.

The identity is in the base (the v1 base read as a parrot):
  - one trunk of half-rings from the tail tip to the bill tip: a long tapering
    reptile tail (longer than the body), a deep keeled body, a thick S-neck that
    rises forward then back under the skull, a raven skull and a long raven bill;
  - bird legs extruded from the lower flank at the hips (drumstick, reversed
    heel, scaled shank, foot box, four toes);
  - wing forelimbs extruded from the upper flank at the shoulder: a thick upper
    arm back and down to the elbow, an elbow knuckle, the forearm extruded from
    the knuckle's upper faces forward and up to a high wrist knuckle, and the
    long finger with the folded membrane (a sail section) extruded from the
    wrist knuckle's back faces, sweeping back to a free tip above the tail root.
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *
from bmkit import _bone_segments, _seg_dist

META = dict(creature='raven_wyvern', model='opus', engine_glb='example/gallery/raven_wyvern.glb')

# ----------------------------------------------------------------------------- skeleton
J = dict(
    hips=(0.0, 0.14, 0.74), chest=(0.0, -0.14, 0.82),
    neck0=(0.0, -0.33, 0.93), neck1=(0.0, -0.44, 1.10), neck2=(0.0, -0.44, 1.27),
    head=(0.0, -0.47, 1.35), beak=(0.0, -0.93, 1.31),
    tail0=(0.0, 0.34, 0.74), tail1=(0.0, 0.58, 0.65), tail2=(0.0, 0.84, 0.60), tailtip=(0.0, 1.18, 0.58),
    hipL=(0.13, 0.13, 0.60), kneeL=(0.20, 0.23, 0.22), ankleL=(0.19, 0.07, 0.065), toeL=(0.19, -0.11, 0.02),
    shoulderL=(0.21, -0.17, 0.86), elbowL=(0.35, 0.04, 0.74), wristL=(0.235, -0.18, 1.30),
    fingerL=(0.29, 0.10, 1.21), tipL=(0.245, 0.68, 0.945),
)

# ----------------------------------------------------------------------------- trunk rings
# half-ring = [T top seam, s1, s2, s3, s4, B bottom seam]; shape = four (fraction of W, s along T->B)
TAIL = ((0.80, 0.14), (1.00, 0.42), (0.88, 0.70), (0.50, 0.92))
BODY = ((0.74, 0.10), (1.00, 0.36), (0.88, 0.64), (0.46, 0.90))
HIPS = ((0.76, 0.10), (1.00, 0.38), (0.92, 0.66), (0.55, 0.90))
NECK = ((0.78, 0.14), (1.00, 0.42), (0.90, 0.70), (0.55, 0.92))
HEAD = ((0.80, 0.10), (1.00, 0.34), (0.92, 0.62), (0.58, 0.88))
BILL = ((0.55, 0.12), (0.95, 0.40), (1.00, 0.62), (0.60, 0.90))

RINGS = [  # name, T (y, z), B (y, z), W, shape
    ('t0', (1.18, 0.60), (1.17, 0.555), 0.022, TAIL),
    ('t1', (1.00, 0.625), (0.99, 0.54), 0.045, TAIL),
    ('t2', (0.83, 0.67), (0.81, 0.54), 0.072, TAIL),
    ('t3', (0.66, 0.745), (0.63, 0.545), 0.105, TAIL),
    ('t4', (0.49, 0.835), (0.45, 0.55), 0.150, TAIL),
    ('h0', (0.33, 0.915), (0.29, 0.52), 0.190, HIPS),
    ('h1', (0.17, 0.965), (0.14, 0.47), 0.222, HIPS),
    ('h2', (0.02, 0.99), (0.00, 0.47), 0.232, BODY),
    ('c0', (-0.12, 1.02), (-0.13, 0.50), 0.240, BODY),
    ('c1', (-0.23, 1.045), (-0.33, 0.62), 0.220, BODY),
    ('n0', (-0.28, 1.085), (-0.40, 0.86), 0.125, NECK),    # neck base: narrower than the chest
    ('n1', (-0.37, 1.145), (-0.545, 1.01), 0.100, NECK),   # lower neck bows forward ...
    ('n2', (-0.42, 1.245), (-0.585, 1.155), 0.090, NECK),
    ('n3', (-0.37, 1.345), (-0.52, 1.28), 0.088, NECK),    # ... the upper neck bows back under the skull
    ('k0', (-0.34, 1.53), (-0.575, 1.315), 0.120, HEAD),     # occiput: juts back over the nape
    ('k1', (-0.47, 1.545), (-0.625, 1.315), 0.140, HEAD),    # skull, eye
    ('k2', (-0.58, 1.535), (-0.665, 1.325), 0.120, HEAD),    # brow, face: a stop above the bill
    ('b0', (-0.655, 1.465), (-0.695, 1.33), 0.068, BILL),    # bill root, 0.135 deep, narrower than the face
    ('b1', (-0.75, 1.435), (-0.765, 1.35), 0.052, BILL),
    ('b2', (-0.84, 1.40), (-0.835, 1.36), 0.036, BILL),
    ('b3', (-0.905, 1.36), (-0.89, 1.345), 0.020, BILL),
]


def ring_pts(T, B, W, shape):
    T = Vector((0.0, T[0], T[1])); B = Vector((0.0, B[0], B[1]))
    pts = [T]
    for fx, s in shape:
        p = T.lerp(B, s)
        pts.append(Vector((fx * W, p.y, p.z)))
    pts.append(B)
    return pts


def rp(name, i):
    """The stage-1 position of vertex i (0 top .. 5 bottom) of trunk ring `name`."""
    n, T, B, W, shape = next(r for r in RINGS if r[0] == name)
    return ring_pts(T, B, W, shape)[i]


def vn(bm, name, i):
    return vert_near(bm, rp(name, i))


def face_of(vs):
    s = set(vs)
    return next(f for f in vs[0].link_faces if set(f.verts) == s)


def boundary_loop(faces):
    fs = set(faces)
    edges = [e for f in faces for e in f.edges if sum(1 for g in e.link_faces if g in fs) == 1]
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    start = edges[0].verts[0]
    loop, prev, cur = [start], None, start
    while True:
        if prev is None:
            nxt = adj[cur][0]
        else:
            nxt = next(v for v in adj[cur] if v is not prev)
        if nxt is start:
            break
        loop.append(nxt)
        prev, cur = cur, nxt
    return loop


def ext_to(bm, faces, pts):
    """E then place: extrude a face region and put its new boundary on the closed
    polygon pts (the cyclic order / direction with the least travel). Returns
    (new boundary verts in pts order, new end faces, side faces)."""
    old = boundary_loop(faces)
    n = len(old)
    assert n == len(pts), 'ext_to: %d boundary verts for %d points' % (n, len(pts))
    pos = [v.co.copy() for v in old]
    P = [Vector(p) for p in pts]
    best = None
    for d in (1, -1):
        for s in range(n):
            idx = [(s + d * i) % n for i in range(n)]
            cost = sum((pos[i] - P[idx[i]]).length_squared for i in range(n))
            if best is None or cost < best[0]:
                best = (cost, idx)
    r = extrude(bm, faces)
    new = [min(r['verts'], key=lambda v: (v.co - p).length) for p in pos]
    assert len(set(new)) == n, 'ext_to: ambiguous vertex match'
    if os.environ.get('RW_DEBUG') and n == 6:
        say('EXT', [tuple(round(x, 3) for x in pos[i]) + ('->',) + tuple(round(x, 3) for x in P[best[1][i]]) for i in range(n)])
    out = [None] * n
    for i, v in enumerate(new):
        v.co = P[best[1][i]].copy()
        out[best[1][i]] = v
    return out, r['faces'], r['sides']


def frame(axis, up):
    a = Vector(axis).normalized()
    u = Vector(up)
    u = (u - a * u.dot(a)).normalized()
    f = a.cross(u).normalized()
    return a, u, f


def hexsec(c, axis, up, rf, ru, n=6):
    """An n-sided section round the axis: rf across (side to side), ru along `up`."""
    a, u, f = frame(axis, up)
    c = Vector(c)
    return [c + f * rf * math.cos(2 * math.pi * i / n) + u * ru * math.sin(2 * math.pi * i / n) for i in range(n)]


def pick_pair(sides, d):
    """The two adjacent side faces (of a knuckle) that best face direction d, judged
    from the knuckle's centre (face normals of fresh extrusions are not trusted)."""
    d = Vector(d).normalized()
    # sort by position: extrude's side list is ordered by stale face indices (not deterministic)
    sides = sorted(sides, key=lambda f: tuple(round(x, 5) for x in f.calc_center_median()))
    c = sum((f.calc_center_median() for f in sides), Vector()) / len(sides)
    best = None
    for f in sides:
        for g in sides:
            if f is g or not (set(f.edges) & set(g.edges)):
                continue
            m = (f.calc_center_median() + g.calc_center_median()) / 2 - c
            s = m.normalized().dot(d)
            if best is None or s > best[0] + 1e-9:
                best = (s, [f, g])
    return best[1]


# ----------------------------------------------------------------------------- legs (from v1)
def hexs(c, d, hf, ho, wf=0.72):
    """A 6-sided limb section at centre c, perpendicular to the (y, z) direction d:
    [FO, O, BO, BI, I, FI] (front-outer ... front-inner)."""
    c = Vector(c)
    d = Vector((0.0, d[0], d[1])).normalized()
    f = Vector((0.0, d.z, -d.y))
    if f.y > 0:
        f = -f
    o = Vector((1.0, 0.0, 0.0))
    return [c + f * hf + o * ho * wf, c + o * ho, c - f * hf + o * ho * wf,
            c - f * hf - o * ho * wf, c - o * ho, c + f * hf - o * ho * wf]


LEG = [hexs((0.170, 0.10, 0.40), (0.15, -1.0), 0.140, 0.112),     # drumstick
       hexs(J['kneeL'], (-0.25, -1.0), 0.066, 0.058),             # reversed heel
       hexs((0.19, 0.07, 0.065), (-0.3, -1.0), 0.056, 0.052),     # ankle / foot top
       hexs((0.19, 0.07, 0.0), (0.0, -1.0), 0.070, 0.062)]        # sole

TOES = [  # foot-box wall (hex indices), direction, length, knuckle w/h, tip w/h
    (5, 0, (0.0, -1.0), 0.17, 0.024, 0.045, 0.012, 0.022),
    (0, 1, (math.sin(math.radians(35)), -math.cos(math.radians(35))), 0.14, 0.022, 0.042, 0.011, 0.02),
    (4, 5, (-math.sin(math.radians(30)), -math.cos(math.radians(30))), 0.13, 0.022, 0.042, 0.011, 0.02),
    (2, 3, (0.0, 1.0), 0.09, 0.02, 0.04, 0.011, 0.02)]


def toe(bm, wall, dirn, L, w1, h1, w2, h2):
    P, Q, Qs, Ps = wall
    f = face_of(wall)
    t = Vector((dirn[0], dirn[1], 0.0)).normalized()
    s = Vector((-t.y, t.x, 0.0))
    if s.dot(Q.co - P.co) < 0:
        s = -s
    c0 = (P.co + Q.co + Qs.co + Ps.co) / 4
    c0.z = 0.0
    faces = [f]
    for frac, w, h in ((0.5, w1, h1), (1.0, w2, h2)):
        c = c0 + t * L * frac
        pts = [c - s * w + Vector((0, 0, h)), c + s * w + Vector((0, 0, h)), c + s * w, c - s * w]
        _, faces, _ = ext_to(bm, faces, pts)


def toe_tip(i):
    a_, b_, dirn, L = TOES[i][:4]
    c0 = (LEG[2][a_] + LEG[2][b_] + LEG[3][a_] + LEG[3][b_]) / 4
    c0.z = 0.0
    t = Vector((dirn[0], dirn[1], 0.0)).normalized()
    return c0 + t * L, t


# ----------------------------------------------------------------------------- wing
def sail(y, zle, zte, xle, xte, t, bone=0.06):
    """A folded-wing section in the plane y = const: LE-in, bone-in, TE-in, TE-out,
    bone-out, LE-out. The finger bone is the thick top; the membrane below it
    thins to the trailing edge and leans out over the flank."""
    return [(xle - t, y, zle - 0.012), (xle - t - 0.004, y, zle - bone), (xte - 0.5 * t, y, zte),
            (xte, y, zte), (xle + 0.012, y, zle - bone), (xle, y, zle)]


E = Vector(J['elbowL']); WR = Vector(J['wristL'])
FORE = (WR - E).normalized()
SH = Vector((0.29, -0.15, 0.83))
ARM = [hexsec(SH, (1.0, 0.6, -0.3), (0, 0, 1), 0.065, 0.095),                            # shoulder
       hexsec(E, E - SH, (0, -0.4, 1), 0.058, 0.062),                                      # elbow
       hexsec(E + Vector((0.005, 0.05, -0.025)), E - SH, (0, -0.4, 1), 0.045, 0.048)]      # elbow knuckle
FOREARM = [hexsec(E.lerp(WR, 0.45) + Vector((0.02, 0, 0)), FORE, (0, 1, 0.3), 0.046, 0.050),
           hexsec(E.lerp(WR, 0.85), FORE, (0, 1, 0.3), 0.040, 0.042),
           hexsec(WR, FORE, (0, 1, 0.3), 0.055, 0.055),                               # wrist
           hexsec(WR + FORE * 0.055, FORE, (0, 1, 0.3), 0.036, 0.038)]                  # wrist knuckle
# the sail: the finger bone on top, the membrane below it with a scalloped trailing edge
# (two finger points at y 0.10 and 0.38, scallops between them)
SAILS = [sail(-0.05, 1.29, 1.03, 0.225, 0.235, 0.040, bone=0.045),
         sail(0.10, 1.22, 0.74, 0.245, 0.285, 0.045, bone=0.055),     # finger-1 point
         sail(0.24, 1.15, 0.90, 0.255, 0.285, 0.040, bone=0.05),    # scallop
         sail(0.38, 1.08, 0.72, 0.25, 0.28, 0.040, bone=0.05),      # finger-2 point
         sail(0.52, 1.01, 0.92, 0.245, 0.26, 0.030, bone=0.035),    # scallop
         sail(0.68, 0.955, 0.935, 0.245, 0.25, 0.012, bone=0.012)]   # wing tip


def stage1(k):
    bm = bmesh.new()
    R, rows = {}, []
    for name, T, B, W, shape in RINGS:
        R[name] = ring(bm, ring_pts(T, B, W, shape))
        rows.append(R[name])
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)

    # ---- legs: 2-face patch on the lower flank at the hips (rings h0 h1 h2, verts 3-4)
    h0, h1, h2 = R['h0'], R['h1'], R['h2']
    faces = [face_of([h1[3], h2[3], h2[4], h1[4]]), face_of([h0[3], h1[3], h1[4], h0[4]])]
    secs = []
    for pts in LEG:
        v, faces, _ = ext_to(bm, faces, pts)
        secs.append(v)
    ftop, fbot = secs[-2], secs[-1]
    for a_, b_, dirn, L, tw1, th1, tw2, th2 in TOES:
        toe(bm, [ftop[a_], ftop[b_], fbot[b_], fbot[a_]], dirn, L, tw1, th1, tw2, th2)

    # ---- wing: 2-face patch on the upper flank at the shoulder (rings c1 c0, verts 1-3)
    c0, c1 = R['c0'], R['c1']
    faces = [face_of([c1[1], c0[1], c0[2], c1[2]]), face_of([c1[2], c0[2], c0[3], c1[3]])]
    for pts in ARM:
        _, faces, sides = ext_to(bm, faces, pts)
    faces = pick_pair(sides, FORE)
    for pts in FOREARM:
        _, faces, sides = ext_to(bm, faces, pts)
    faces = pick_pair(sides, (-0.4, 1.0, 0.2))
    for pts in SAILS:
        _, faces, _ = ext_to(bm, faces, pts)

    recalc_normals(bm)
    bm = canonical(bm)
    ob = object_from_bm('body', bm)
    debug_hits(ob)
    if os.environ.get("RW_DEBUG2"):
        from bmkit import lock_record
        r_ = lock_record(ob); say("LOCKDBG", r_["edge_hash"][:16], r_["pos_hash"][:16], r_["half_verts"], r_["verts"])
    return ob


EYE_FACE = ('k1', 'k2', 1, 2)      # the upper-side face between skull and brow rings


def stage2(k, body):
    bm = edit(body)
    # ---- eye socket: a loop inside the upper-side face between the skull and brow rings
    ka, kb, i0, i1 = EYE_FACE
    eye_face = face_of([vn(bm, ka, i0), vn(bm, kb, i0), vn(bm, kb, i1), vn(bm, ka, i1)])
    with k.topo(bm, 'inset', 'eye socket: a loop inside the upper-side face between skull and brow rings'):
        inner = inset(bm, [eye_face], 0.28, depth=0.0)
    n_out = Vector((0.9, -0.25, 0.2)).normalized()
    for v in inner[0].verts:
        v.co -= n_out * 0.02
    # ---- brow: the top edge of the eye face overhangs it (out, forward, down)
    for nm, d in (('k1', (0.018, -0.01, -0.012)), ('k2', (0.026, -0.012, -0.018))):
        vn(bm, nm, 1).co += Vector(d)
    # ---- heel: a supporting loop each side of the reversed heel so the bend keeps its volume
    for a_, b_, t, sc in ((0, 1, 0.80, 1.12), (1, 2, 0.20, 0.92)):
        pa, pb = LEG[a_][1], LEG[b_][1]
        with k.topo(bm, 'loop', 'heel: a supporting loop %s the heel ring' % ('above' if a_ == 0 else 'below')):
            nv = loopcut(bm, edge_near(bm, (pa + pb) / 2), t=t, near=vert_near(bm, pa))
        scale(nv, sc)
    # ---- shoulder: a loop halfway down the upper arm so the wing can lift without shearing the flank
    with k.topo(bm, 'loop', 'upper arm: a loop between shoulder and elbow for the wing lift'):
        nv = loopcut(bm, edge_near(bm, (ARM[0][0] + ARM[1][0]) / 2), t=0.5)
    # ---- the gape: the bill's side line pressed in and run back to a mouth corner under the eye;
    # the upper mandible now overhangs the lower
    for nm, d in (('b3', (-0.004, 0, 0)), ('b2', (-0.01, 0, 0.003)), ('b1', (-0.016, 0, 0.004)),
                  ('b0', (-0.018, 0.0, -0.006)), ('k2', (-0.01, 0.015, -0.02))):
        vn(bm, nm, 3).co += Vector(d)
    # ---- the hook: only the last quarter of the culmen turns down over the lower mandible
    for nm, dz, dy in (('b3', -0.022, -0.012), ('b2', -0.006, 0.0)):
        for i in (0, 1):
            vn(bm, nm, i).co += Vector((0, dy, dz))
    # ---- one cheek/jaw plane under the eye, occiput to mouth corner
    flatten([vn(bm, 'k0', 3), vn(bm, 'k0', 4), vn(bm, 'k1', 3), vn(bm, 'k1', 4), vn(bm, 'k2', 4)])
    # ---- no needles (tech QA slivers): the thin ends get a little body
    # the tail tip and the bill tip rings open up (the fan and the hook cover them)
    for nm, sx, sz in (('t0', 1.9, 1.5), ('b3', 1.4, 1.0)):
        vs = [vn(bm, nm, i) for i in range(6)]
        c = sum((v.co for v in vs), Vector()) / 6
        for v in vs:
            v.co = Vector((v.co.x * sx, v.co.y, c.z + (v.co.z - c.z) * sz))
    # the membrane's trailing edge is 3.5 cm thick, not a 2 cm blade
    for sec in SAILS[:5]:
        vert_near(bm, sec[2]).co.x -= 0.014
    # the wing tip section: a blunt knuckle, not a needle
    tip = [vert_near(bm, p) for p in SAILS[5]]
    c = sum((v.co for v in tip), Vector()) / 6
    for v in tip:
        v.co = c + Vector(((v.co.x - c.x) * 2.6, 0.0, (v.co.z - c.z) * 1.6))
    debug_slivers(bm)
    commit(body, bm)


def debug_slivers(bm):
    if not os.environ.get('RW_DEBUG'):
        return
    def mina(a, b, c):
        out = []
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            u, w = y - x, z - x
            out.append(0 if u.length < 1e-9 or w.length < 1e-9 else math.degrees(u.angle(w)))
        return min(out)
    for f in bm.faces:
        P = [v.co for v in f.verts]
        if len(P) == 3:
            best = mina(*P)
        elif len(P) == 4:
            best = max(min(mina(P[0], P[1], P[2]), mina(P[0], P[2], P[3])), min(mina(P[1], P[2], P[3]), mina(P[1], P[3], P[0])))
        else:
            continue
        if best < 6.5:
            say('SLIVER %.1f' % best, tuple(round(x, 3) for x in f.calc_center_median()))


KEEP_VALLEYS = lambda c: c.z > 1.42 and -0.66 < c.y < -0.44 and abs(c.x) > 0.08   # the eye socket


# ============================================================================= stage 3
PAL = {'body': '#4a5167', 'dark': '#343949', 'bill': '#3b352f', 'bone': '#cfc3a3', 'scale': '#5f564d',
       'ink': '#1d1e24', 'membrane': '#6c4f98', 'eye': '#ffb21e'}


def spike(bm, root, tip, side, w, t, mid=0.45, midw=1.1, bend=(0, 0, 0)):
    """A faceted blade / claw: diamond section at the root, a wider diamond at `mid`
    (pushed by `bend`), one point at the tip. w runs across `side`-ish, t is the thickness."""
    root, tip = Vector(root), Vector(tip)
    ax = (tip - root).normalized()
    th = ax.cross(Vector(side)).normalized()
    sd = th.cross(ax).normalized()
    m = root.lerp(tip, mid) + Vector(bend)
    b = ring(bm, [root + sd * w, root + th * t, root - sd * w, root - th * t])
    mm = ring(bm, [m + sd * w * midw, m + th * t * midw, m - sd * w * midw, m - th * t * midw])
    tp = bm.verts.new(tip)
    fs = bridge(bm, b, mm, closed=True)
    fs += [bm.faces.new([mm[i], mm[(i + 1) % 4], tp]) for i in range(4)]
    fs.append(bm.faces.new(list(reversed(b))))
    return fs


def tube(bm, pts, radii, n=5, up=(0, 0, 1)):
    """A tapered n-sided tube along pts (radii for all but the last point, which is the tip)."""
    P = [Vector(p) for p in pts]
    rows = []
    for i, r in enumerate(radii):
        a = (P[i + 1] - P[max(i - 1, 0)]).normalized()
        rows.append(ring(bm, hexsec(P[i], a, up, r, r, n=n)))
    fs = []
    for a, b in zip(rows, rows[1:]):
        fs += bridge(bm, a, b, closed=True)
    fs.append(bm.faces.new(list(reversed(rows[0]))))
    tp = bm.verts.new(P[-1])
    last = rows[-1]
    fs += [bm.faces.new([last[i], last[(i + 1) % n], tp]) for i in range(n)]
    return fs


def hexprism(bm, c, nrm, r, depth, up=(0, 0, 1)):
    c, nrm = Vector(c), Vector(nrm).normalized()
    u = Vector(up) - nrm * Vector(up).dot(nrm)
    u.normalize()
    w = nrm.cross(u)
    ang = [math.radians(30 + 60 * i) for i in range(6)]
    front = ring(bm, [c + (u * math.sin(a) + w * math.cos(a)) * r for a in ang])
    back = ring(bm, [c - nrm * depth + (u * math.sin(a) + w * math.cos(a)) * r * 0.9 for a in ang])
    fs = bridge(bm, front, back, closed=True)
    fs.append(bm.faces.new(front))
    fs.append(bm.faces.new(list(reversed(back))))
    return fs


def piece(name, bm, keymap, mirror=True):
    """keymap: list of (faces, key). Object from bm (normals outward), painted by face membership."""
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    idx = {}
    bm.faces.index_update()
    for fs, key in keymap:
        for f in fs:
            idx[f.index] = key
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {k_: PAL[k_] for k_ in sorted(set(idx.values()))}, lambda c, n, i: idx[i])
    return ob


def front_of(name, c):
    T, B = rp(name, 0), rp(name, 5)
    d = B - T
    n = Vector((0.0, d.z, -d.y))
    return (Vector(c) - T).dot(n) > 0


def flood(bm, seed, stop):
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


def body_tree(body):
    from bmkit import evaluated_bm
    from mathutils.bvhtree import BVHTree
    b = evaluated_bm(body)
    t = BVHTree.FromBMesh(b)
    b.free()
    return t


def surface_x(tree, y, z, x0=0.305):
    hit = tree.ray_cast(Vector((x0, y, z)), Vector((-1.0, 0.0, 0.0)), 0.4)
    return hit[0].x if hit[0] is not None else None


def stage3(k, body):
    bm = edit(body)
    wing_stop = {vn(bm, r, i) for r in ('c1', 'c0') for i in (1, 2, 3)}
    leg_stop = {vn(bm, r, i) for r in ('h0', 'h1', 'h2') for i in (3, 4)}
    wing = flood(bm, face_near(bm, SAILS[-1][3]), wing_stop)
    leg = flood(bm, face_near(bm, (0.19, 0.07, 0.0), n=(0, 0, -1)), leg_stop)
    # sail vertices by their section slot: 0 LE-in 1 bone-in 2 TE-in 3 TE-out 4 bone-out 5 LE-out
    slot = {}
    for sec in SAILS:
        for j, p in enumerate(sec):
            slot[vert_near(bm, Vector(p) - Vector((0.014 if j == 2 else 0.0, 0, 0)))] = j
    cand = [f for f in bm.faces if len(f.verts) == 4 and all(v.co.x > 0.06 for v in f.verts)
            and -0.62 < f.calc_center_median().y < -0.42 and f.calc_center_median().z > 1.40]
    socket = min(cand, key=lambda f: f.calc_area())
    sc, sn = socket.calc_center_median(), socket.normal.copy()
    if sn.x < 0:
        sn = -sn
    z_cuff = LEG[0][1].z + 0.80 * (LEG[1][1].z - LEG[0][1].z)
    key = {}
    for f in bm.faces:
        c = f.calc_center_median()
        if f in wing:
            sl = [slot.get(v) for v in f.verts]
            key[f.index] = 'membrane' if all(s_ in (1, 2, 3, 4) for s_ in sl) else 'dark'
        elif f in leg:
            key[f.index] = 'scale' if c.z < z_cuff else 'body'
        elif f is socket:
            key[f.index] = 'ink'
        elif front_of('b2', c) and c.y < -0.87:
            key[f.index] = 'bone'
        elif front_of('b0', c):
            key[f.index] = 'bill'
        elif f.normal.z > 0.55 or (front_of('n1', c) and not front_of('k1', c) and f.normal.z > 0.2):
            key[f.index] = 'dark'           # the saddle, the skull cap and brow planes
        elif not front_of('t3', c):
            key[f.index] = 'dark'           # the tail darkens toward the tip
        else:
            key[f.index] = 'body'
    bm.free()
    paint(body, {k_: PAL[k_] for k_ in sorted(set(key.values()))}, lambda c, n, i: key[i])
    tree = body_tree(body)
    pieces = []

    # ---- eye: amber iris proud of the socket, ink pupil ahead and a touch down, bone glint
    b = bmesh.new()
    look = (sn + Vector((0, -0.5, -0.1))).normalized()
    ec = sc + sn * 0.004                          # a lens just proud of the socket, not a block
    iris = hexprism(b, ec, look, 0.038, 0.026)
    pup = hexprism(b, ec + look * 0.006 + Vector((0, -0.005, -0.003)), look, 0.021, 0.012)
    glint = spike(b, ec + look * 0.010 + Vector((0, 0.010, 0.012)), ec + look * 0.016 + Vector((0, 0.004, 0.021)),
                  (0, 1, 0), 0.007, 0.005)
    pieces.append(piece('eye', b, [(iris, 'eye'), (pup, 'ink'), (glint, 'bone')]))

    # ---- horns: two main swept-back cones off the skull top, two small ones off the cheek
    b = bmesh.new()
    hs = tube(b, [(0.062, -0.46, 1.49), (0.085, -0.37, 1.575), (0.11, -0.27, 1.655), (0.125, -0.17, 1.70),
                  (0.13, -0.09, 1.72)], [0.052, 0.042, 0.028, 0.014], n=6)
    hs += tube(b, [(0.095, -0.44, 1.44), (0.14, -0.36, 1.42), (0.175, -0.29, 1.39), (0.195, -0.23, 1.36)],
               [0.034, 0.026, 0.014], n=5)
    pieces.append(piece('horns', b, [(hs, 'bone')]))

    # ---- throat hackles: six raven-beard clumps, varied, pointing forward-down off the throat
    b = bmesh.new()
    hk = []
    for x, z0, L, w in ((0.028, 1.235, 0.17, 0.042), (0.062, 1.26, 0.14, 0.04), (0.085, 1.29, 0.11, 0.036)):
        y0 = -0.545 + 0.25 * (1.235 - z0)
        root = Vector((x, y0 + 0.03, z0))
        tip = root + Vector((x * 0.6, -0.075, -0.10)).normalized() * L
        hk += spike(b, root, tip, (1, 0, 0), w, 0.030, mid=0.35, midw=1.05)
    pieces.append(piece('hackles', b, [(hk, 'dark')]))

    # ---- dorsal ridge: nine graduated wedges, nape to tail, swept back ~32 deg; plus the fan's
    # centre vane (one unmirrored piece on the midline)
    b = bmesh.new()
    ds = []
    ridge = [('n2', 0.06), ('n0', 0.09), ('c1', 0.16), ('c0', 0.19), ('h2', 0.15), ('h1', 0.125),
             ('h0', 0.10), ('t4', 0.075), ('t3', 0.055)]
    names = [r[0] for r in RINGS]
    for nm, hgt in ridge:
        p0 = rp(nm, 0)
        nx = names[names.index(nm) - 1]
        back = (rp(nx, 0) - p0).normalized()
        if back.y < 0:
            back = -back
        upn = Vector((0, -back.z, back.y))
        if upn.z < 0:
            upn = -upn
        base = p0 - upn * 0.03
        tip = base + (upn * math.cos(math.radians(32)) + back * math.sin(math.radians(32))) * (hgt + 0.03)
        ds += spike(b, base, tip, (0, 0, 1), hgt * 0.42 + 0.02, 0.026, mid=0.3, midw=1.0)
    fanc = spike(b, (0.0, 1.10, 0.600), (0.0, 1.42, 0.625), (1, 0, 0), 0.03, 0.016, mid=0.40, midw=1.5)
    pieces.append(piece('spines', b, [(ds, 'membrane'), (fanc, 'membrane')], mirror=False))

    # ---- tail fan: two side vanes per side (varied length and angle), 3.4 cm thick
    b = bmesh.new()
    fan = []
    for root, tip, w in (((0.02, 1.12, 0.562), (0.12, 1.37, 0.56), 0.042),
                         ((0.025, 1.10, 0.558), (0.19, 1.26, 0.53), 0.038)):
        fan += spike(b, root, tip, (1, 0, 0), w, 0.014, mid=0.45, midw=1.2)
    pieces.append(piece('tailfan', b, [(fan, 'membrane')]))

    # ---- wing: thumb claw off the wrist knuckle; two finger spars seated in the membrane
    b = bmesh.new()
    spars = []
    for (ys, zs), (ye, ze) in (((-0.02, 1.16), (0.10, 0.74)), ((0.02, 1.19), (0.38, 0.72))):
        pts, rad = [], []
        for t in (0.0, 0.3, 0.6, 0.88):
            y, z = ys + (ye - ys) * t, zs + (ze - zs) * t
            x = surface_x(tree, y, z) or 0.27
            pts.append(Vector((x - 0.004, y, z)))
            rad.append(0.024 - 0.008 * t)
        d = pts[-1] - pts[-2]
        pts.append(pts[-1] + d.normalized() * 0.13)
        spars += tube(b, pts, rad, n=5, up=(1, 0, 0))
    pieces.append(piece('wingbones', b, [(spars, 'dark')]))
    b = bmesh.new()
    thumb = tube(b, [WR + FORE * 0.03, WR + FORE * 0.10 + Vector((0, -0.02, 0)),
                     WR + FORE * 0.16 + Vector((0, -0.06, 0.0)), WR + FORE * 0.17 + Vector((0, -0.11, -0.03))],
                 [0.03, 0.022, 0.012], n=5, up=(0, -1, 0))
    pieces.append(piece('thumb', b, [(thumb, 'bone')]))

    # ---- claws: one hooked ink claw per toe
    b = bmesh.new()
    cl = []
    for i in range(4):
        tp, t = toe_tip(i)
        r0 = tp + Vector((0, 0, 0.012)) - t * 0.015
        L = 0.065 if i < 3 else 0.05
        cl += spike(b, r0, r0 + t * L + Vector((0, 0, -0.010)), (0, 0, 1), 0.016, 0.014, mid=0.45,
                    midw=0.9, bend=(0, 0, 0.012))
    pieces.append(piece('claws', b, [(cl, 'ink')]))
    return pieces


# ============================================================================= stage 4
BONES = [('hips', (0.0, 0.22, 0.74), (0.0, -0.02, 0.79), None),
         ('chest', (0.0, -0.02, 0.79), (0.0, -0.31, 0.93), 'hips', True),
         ('neck', (0.0, -0.31, 0.93), (0.0, -0.46, 1.12), 'chest', True),
         ('neck2', (0.0, -0.46, 1.12), (0.0, -0.45, 1.34), 'neck', True),
         ('head', (0.0, -0.45, 1.34), (0.0, -0.90, 1.37), 'neck2', True),
         ('tail0', (0.0, 0.30, 0.74), (0.0, 0.57, 0.66), 'hips'),
         ('tail1', (0.0, 0.57, 0.66), (0.0, 0.85, 0.60), 'tail0', True),
         ('tail2', (0.0, 0.85, 0.60), (0.0, 1.20, 0.58), 'tail1', True),
         ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
         ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
         ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
         ('arm.L', J['shoulderL'], J['elbowL'], 'chest'),
         ('fore.L', J['elbowL'], J['wristL'], 'arm.L', True),
         ('finger.L', J['wristL'], J['fingerL'], 'fore.L', True),
         ('tip.L', J['fingerL'], J['tipL'], 'finger.L', True)]


def _side_sets(body):
    """Vertex-index sets of the wing and the leg of each side on the skinned body."""
    bm = edit(body)
    out = {}
    for sx, sd in ((1, 'L'), (-1, 'R')):
        m = lambda p: Vector((p[0] * sx, p[1], p[2]))
        wstop = {vert_near(bm, m(rp(r, i))) for r in ('c1', 'c0') for i in (1, 2, 3)}
        lstop = {vert_near(bm, m(rp(r, i))) for r in ('h0', 'h1', 'h2') for i in (3, 4)}
        wf = flood(bm, face_near(bm, m(SAILS[-1][3])), wstop)
        lf = flood(bm, face_near(bm, m((0.19, 0.07, 0.0)), n=(0, 0, -1)), lstop)
        out['wing.' + sd] = {v.index for f in wf for v in f.verts} - {v.index for v in wstop}
        out['leg.' + sd] = {v.index for f in lf for v in f.verts} - {v.index for v in lstop}
    bm.free()
    return out


def _clean_weights(body, rig):
    """Bone heat bleeds the folded wing into the flank and the thighs into the belly: wing bones
    stay on wing verts, shin/foot on leg verts."""
    sets = _side_sets(body)
    wing_b = {s: {'arm.' + s, 'fore.' + s, 'finger.' + s, 'tip.' + s} for s in 'LR'}
    leg_b = {s: {'shin.' + s, 'foot.' + s} for s in 'LR'}
    gname = {g.index: g.name for g in body.vertex_groups}
    segs = _bone_segments(rig)
    for v in body.data.vertices:
        allowed = set(segs)
        for s in 'LR':
            if v.index in sets['wing.' + s]:
                allowed = wing_b[s] | {'chest'}
                break
            if v.index in sets['leg.' + s]:
                allowed = leg_b[s] | {'thigh.' + s, 'hips'}
                break
        else:
            allowed -= wing_b['L'] | wing_b['R'] | leg_b['L'] | leg_b['R']
            if front_of('n3', body.matrix_world @ v.co):
                allowed = {'head'}                  # the skull is rigid: horns and eyes stay seated
        for g in list(v.groups):
            if gname[g.group] not in allowed and g.weight > 0:
                body.vertex_groups[gname[g.group]].remove([v.index])
        if allowed == {'head'}:
            body.vertex_groups['head'].add([v.index], 1.0, 'REPLACE')
        if sum(g.weight for g in v.groups if gname[g.group] in segs) <= 1e-4:
            p = body.matrix_world @ v.co
            nm = min(allowed & set(segs), key=lambda n: _seg_dist(p, *segs[n]))
            vg = body.vertex_groups.get(nm) or body.vertex_groups.new(name=nm)
            vg.add([v.index], 1.0, 'REPLACE')
    # the shoulder ring is shared half and half with the chest, so the wing lift rolls the root
    # instead of folding the flank under it
    bm = edit(body)
    for sx, sd in ((1, 'L'), (-1, 'R')):
        ids = [vert_near(bm, Vector((p.x * sx, p.y, p.z))).index for p in ARM[0]]
        for g in list(body.vertex_groups):
            if g.name not in ('arm.' + sd, 'chest'):
                g.remove(ids)
        body.vertex_groups['arm.' + sd].add(ids, 0.5, 'REPLACE')
        body.vertex_groups['chest'].add(ids, 0.5, 'REPLACE')
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


SPINE_SIGN = -1     # bone-local +X pitches the spine chain BACK/up on this rig (s4 r01 posed renders)


def stage4(k, body, pieces):
    rig = armature(BONES, roll='auto')
    skin(body, rig)
    _clean_weights(body, rig)
    P = {p.name.replace('piece_', ''): p for p in pieces}
    for nm in ('eye', 'horns'):
        bind(P[nm], rig, bone='head')
    for nm in ('hackles', 'spines', 'tailfan', 'wingbones', 'claws'):
        bind(P[nm], rig, body=body)
    bind(P['thumb'], rig)                      # rigid, per vertex to the nearest bone (the wrist)
    s = SPINE_SIGN

    # idle: breathing, a slow head turn, the tail swaying, the wings settling
    clip(rig, 'idle', sym({1: {},
                           12: {'chest': (-2 * s, 0, 0), 'head': (0, 0, 8), 'tail1': (0, 0, 6), 'arm.L': (0, 3, 0)},
                           24: {'chest': (-3 * s, 0, 0), 'neck2': (3 * s, 0, 0), 'head': (0, 0, 12), 'tail1': (0, 0, -4),
                                'tail2': (0, 0, -8)},
                           36: {'chest': (-1 * s, 0, 0), 'head': (-4 * s, 0, 4), 'tail1': (0, 0, -6), 'arm.L': (0, 2, 0)},
                           48: {}}))

    # move: a stalking stride, head level, tail swinging against the hips
    def step(th, sh, ft, thr, shr, ftr, hz, tz):
        return {'thigh.L': (th, 0, 0), 'shin.L': (sh, 0, 0), 'foot.L': (ft, 0, 0),
                'thigh.R': (thr, 0, 0), 'shin.R': (shr, 0, 0), 'foot.R': (ftr, 0, 0),
                'hips': (0, 0, hz), 'tail0': (0, 0, tz), 'tail1': (0, 0, tz), 'neck': (4 * s, 0, 0),
                'head': (-4 * s, 0, -hz)}
    clip(rig, 'move', {1: step(17, -4, -12, -16, 8, 10, 4, -7),
                       7: step(3, -24, 26, -4, -2, 0, 0, 0),
                       13: step(-16, 8, 10, 17, -4, -12, -4, 7),
                       19: step(-4, -2, 0, 3, -24, 26, 0, 0),
                       25: step(17, -4, -12, -16, 8, 10, 4, -7)})

    # attack: rear up with the head drawn back and the wings half-spread (threat display), then a
    # lunge that drives the bill forward and down
    clip(rig, 'attack', sym({1: {},
                             9: {'chest': (-8 * s, 0, 0), 'neck': (-16 * s, 0, 0), 'neck2': (-10 * s, 0, 0),
                                 'head': (-10 * s, 0, 0), 'arm.L': (0, 40, 0),
                                 'tail0': (6 * s, 0, 0), 'tail1': (6 * s, 0, 0)},
                             15: {'chest': (-8 * s, 0, 0), 'neck': (-18 * s, 0, 0), 'neck2': (-12 * s, 0, 0),
                                  'head': (-12 * s, 0, 0), 'arm.L': (0, 48, 0),
                                  'tail0': (8 * s, 0, 0), 'tail1': (8 * s, 0, 0)},
                             21: {'chest': (8 * s, 0, 0), 'neck': (18 * s, 0, 0), 'neck2': (8 * s, 0, 0),
                                  'head': (10 * s, 0, 0), 'arm.L': (0, 30, 0),
                                  'tail0': (-6 * s, 0, 0), 'thigh.L': (8, 0, 0)},
                             26: {'chest': (5 * s, 0, 0), 'neck': (12 * s, 0, 0), 'neck2': (5 * s, 0, 0),
                                  'head': (6 * s, 0, 0), 'arm.L': (0, 15, 0), 'tail0': (-3 * s, 0, 0)},
                             32: {}}))
    debug_flips(body, rig)
    return rig


def debug_flips(body, rig):
    if not os.environ.get('RW_DEBUG'):
        return
    import techqa as Q
    for act in bpy.data.actions:
        counts, flags, tris = Q.measure(body, [], [0.8, 2.1, 1.55], rig, {act.name: act})
        fl = [p for p, c in flags.get(body.name, {}).items() if c == 'flip']
        me = body.data
        say('FLIPS', act.name, len(fl), [tuple(round(x, 2) for x in me.polygons[p].center) for p in fl[:8]])


def canonical(bm):
    """The same mesh with its vertices and faces in a position-sorted order: bmesh's region
    extrude orders new vertices by pointer hash, so the lock's vertex ids varied run to run."""
    key = lambda co: tuple(round(x, 5) for x in co)
    vs = sorted(bm.verts, key=lambda v: key(v.co))
    out = bmesh.new()
    nv = [out.verts.new(v.co) for v in vs]
    idx = {v: i for i, v in enumerate(vs)}
    fl = []
    for f in bm.faces:
        ids = [idx[v] for v in f.verts]
        m = ids.index(min(ids))
        fl.append(ids[m:] + ids[:m])
    for ids in sorted(fl):
        out.faces.new([nv[i] for i in ids])
    bm.free()
    recalc_normals(out)
    return out


def debug_hits(ob):
    """Print where the self-intersections are (RW_DEBUG=1)."""
    if not os.environ.get('RW_DEBUG'):
        return
    from bmkit import evaluated_bm
    from mathutils.bvhtree import BVHTree
    b = evaluated_bm(ob)
    b.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(b)
    for i, j in t.overlap(t):
        if i < j and not (set(b.faces[i].verts) & set(b.faces[j].verts)):
            ci, cj = b.faces[i].calc_center_median(), b.faces[j].calc_center_median()
            say('HIT', tuple(round(x, 3) for x in ci), tuple(round(x, 3) for x in cj))
    b.free()


META['keep_valleys'] = KEEP_VALLEYS
run(META, stage1, stage2, stage3, stage4)
