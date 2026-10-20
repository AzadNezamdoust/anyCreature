"""Raven-wyvern: a crested bird-dragon, box-modelled for the staged experiment.

Build plan (stage 1): one trunk of half-rings from the tail tip to the beak tip
(tail, rump/hips, chest, neck, skull, beak), each ring a slice between a dorsal
point T and a ventral point B of the side profile. Out of the trunk:
  - each leg is extruded from a 2-face patch on the lower flank at the hips
    (6-sided sections: thigh, reversed knee, scaled shank, foot box), and the
    4 toes are extruded from the foot box walls (3 forward, 1 back);
  - each folded wing is extruded from a 2-face patch on the upper flank at the
    shoulder (6-sided sections: arm up to the wrist above the shoulder, then the
    folded hand/membrane sail back and down past the tail root). The upper part
    of every sail section is the wing bone, the lower part the membrane.
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *
from bmkit import _bone_segments, _seg_dist

META = dict(creature='raven_wyvern', model='opus', engine_glb='example/gallery/raven_wyvern.glb')

# ----------------------------------------------------------------------------- skeleton
J = dict(
    hips=(0.0, 0.14, 0.72), chest=(0.0, -0.12, 0.84), neck=(0.0, -0.30, 0.98),
    head=(0.0, -0.41, 1.13), beak=(0.0, -0.99, 1.10),
    tail0=(0.0, 0.40, 0.68), tail1=(0.0, 0.66, 0.62), tail2=(0.0, 0.88, 0.56),
    hipL=(0.14, 0.13, 0.56), kneeL=(0.17, 0.22, 0.21), ankleL=(0.175, 0.07, 0.065), toeL=(0.18, -0.10, 0.02),
    shoulderL=(0.21, -0.12, 0.92), wristL=(0.285, -0.24, 1.10), handL=(0.27, 0.30, 0.86), tipL=(0.19, 0.72, 0.63),
)

# ----------------------------------------------------------------------------- trunk rings
# half-ring = [top seam, upper side, side, lower side, bottom seam]
# shape: three (fraction of W, s along T->B) for the side verts
TAIL = ((0.90, 0.22), (1.00, 0.52), (0.80, 0.82))
BODY = ((0.78, 0.14), (1.00, 0.45), (0.64, 0.83))
NECK = ((0.80, 0.18), (1.00, 0.50), (0.80, 0.82))
HEAD = ((0.78, 0.13), (1.00, 0.48), (0.78, 0.84))
BEAK = ((0.60, 0.18), (1.00, 0.55), (0.75, 0.85))

RINGS = [  # name, T (y, z), B (y, z), W, shape
    ('t0', (0.88, 0.60), (0.86, 0.52), 0.075, TAIL),
    ('t1', (0.68, 0.71), (0.64, 0.54), 0.115, TAIL),
    ('t2', (0.48, 0.82), (0.42, 0.53), 0.160, TAIL),
    ('h0', (0.32, 0.88), (0.26, 0.47), 0.200, BODY),
    ('h1', (0.16, 0.95), (0.12, 0.41), 0.230, BODY),
    ('h2', (0.00, 1.00), (-0.02, 0.40), 0.245, BODY),
    ('c0', (-0.14, 1.05), (-0.18, 0.46), 0.240, BODY),
    ('c1', (-0.24, 1.08), (-0.32, 0.62), 0.210, BODY),
    ('n0', (-0.26, 1.11), (-0.42, 0.80), 0.165, NECK),
    ('n1', (-0.265, 1.22), (-0.48, 0.98), 0.145, NECK),
    ('k0', (-0.28, 1.36), (-0.54, 1.07), 0.140, HEAD),
    ('k1', (-0.44, 1.42), (-0.62, 1.04), 0.170, HEAD),
    ('k2', (-0.58, 1.405), (-0.67, 1.04), 0.160, HEAD),
    ('b0', (-0.64, 1.37), (-0.69, 1.07), 0.090, BEAK),
    ('b1', (-0.76, 1.30), (-0.765, 1.115), 0.065, BEAK),
    ('b2', (-0.85, 1.235), (-0.835, 1.13), 0.042, BEAK),
    ('b3', (-0.88, 1.13), (-0.855, 1.085), 0.018, BEAK),
]


HEAD_SCALE, HEAD_PIVOT = 1.15, (-0.36, 1.42)      # the head rings, sized up about the skull top


def head_ring(name, T, B, W):
    if name[0] not in 'kb':
        return T, B, W
    f = lambda p: (HEAD_PIVOT[0] + (p[0] - HEAD_PIVOT[0]) * HEAD_SCALE, HEAD_PIVOT[1] + (p[1] - HEAD_PIVOT[1]) * HEAD_SCALE)
    return f(T), f(B), W * HEAD_SCALE


def ring_pts(T, B, W, shape):
    T = Vector((0.0, T[0], T[1])); B = Vector((0.0, B[0], B[1]))
    pts = [T]
    for fx, s in shape:
        p = T.lerp(B, s)
        pts.append(Vector((fx * W, p.y, p.z)))
    pts.append(B)
    return pts


def face_of(vs):
    s = set(vs)
    return next(f for f in vs[0].link_faces if set(f.verts) == s)


def ext(bm, faces, old, new_pts):
    """E then G/S/R: extrude the region, place the copies of `old` (its boundary,
    in my order) at new_pts. Returns (new boundary verts in the same order, new faces)."""
    pos = [v.co.copy() for v in old]
    r = extrude(bm, faces)
    nv = r['verts']
    new = [min(nv, key=lambda v: (v.co - p).length) for p in pos]
    assert len(set(new)) == len(new), 'ext: ambiguous vertex match'
    for v, p in zip(new, new_pts):
        v.co = Vector(p)
    return new, r['faces']


def hexs(c, d, hf, ho, wf=0.72):
    """A 6-sided limb section at centre c, perpendicular to the (y, z) direction d:
    [FO, O, BO, BI, I, FI] (front-outer ... front-inner)."""
    c = Vector(c)
    d = Vector((0.0, d[0], d[1])).normalized()
    f = Vector((0.0, d.z, -d.y))            # forward, perpendicular to the limb
    if f.y > 0:
        f = -f
    o = Vector((1.0, 0.0, 0.0))
    return [c + f * hf + o * ho * wf, c + o * ho, c - f * hf + o * ho * wf,
            c - f * hf - o * ho * wf, c - o * ho, c + f * hf - o * ho * wf]


def sail(y, zle, zte, xle, xte, t, bone=0.075):
    """A folded-wing section in the plane y = const: [P0..P5] =
    LE-in, bone-in, TE-in, TE-out, bone-out, LE-out. The bone (leading edge) is
    the thick top strip; the membrane below it thins to the trailing edge and
    leans out over the flank (xte)."""
    return [(xle - t, y, zle - 0.012), (xle - t - 0.004, y, zle - bone), (xte - 0.5 * t, y, zte),
            (xte, y, zte), (xle + 0.012, y, zle - bone), (xle, y, zle)]


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
    old = [P, Q, Qs, Ps]
    faces = [f]
    for frac, w, h in ((0.5, w1, h1), (1.0, w2, h2)):
        c = c0 + t * L * frac
        pts = [c - s * w + Vector((0, 0, h)), c + s * w + Vector((0, 0, h)), c + s * w, c - s * w]
        old, faces = ext(bm, faces, old, pts)
    return old


LEG = [hexs((0.165, 0.10, 0.38), (0.15, -1.0), 0.140, 0.108),     # thigh top (drumstick)
       hexs(J['kneeL'], (-0.25, -1.0), 0.058, 0.050),             # reversed knee
       hexs((0.175, 0.07, 0.065), (-0.3, -1.0), 0.050, 0.046),    # ankle / foot top
       hexs((0.18, 0.07, 0.0), (0.0, -1.0), 0.066, 0.058)]        # sole


TOES = [  # foot-box wall (hex indices), direction, length, knuckle w/h, tip w/h
    (5, 0, (0.0, -1.0), 0.17, 0.024, 0.045, 0.012, 0.022),                                             # middle
    (0, 1, (math.sin(math.radians(35)), -math.cos(math.radians(35))), 0.14, 0.022, 0.042, 0.011, 0.02),  # outer
    (4, 5, (-math.sin(math.radians(30)), -math.cos(math.radians(30))), 0.13, 0.022, 0.042, 0.011, 0.02), # inner
    (2, 3, (0.0, 1.0), 0.09, 0.02, 0.04, 0.011, 0.02)]                                                  # hind


def toe_tip(i):
    a_, b_, dirn, L = TOES[i][:4]
    c0 = (LEG[2][a_] + LEG[2][b_] + LEG[3][a_] + LEG[3][b_]) / 4
    c0.z = 0.0
    t = Vector((dirn[0], dirn[1], 0.0)).normalized()
    return c0 + t * L, t


SAILS = [sail(0.02, 1.08, 0.86, 0.215, 0.28, 0.060),
         sail(0.30, 0.96, 0.68, 0.20, 0.28, 0.055),
         sail(0.56, 0.80, 0.62, 0.175, 0.225, 0.045, bone=0.06),
         sail(0.72, 0.66, 0.60, 0.16, 0.19, 0.025, bone=0.03)]


def stage1(k):
    bm = bmesh.new()
    R = {}
    rows = []
    for name, T, B, W, shape in RINGS:
        T, B, W = head_ring(name, T, B, W)
        R[name] = ring(bm, ring_pts(T, B, W, shape))
        rows.append(R[name])
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)

    # ---- legs: 2-face patch on the lower flank at the hips (rings h0 h1 h2, faces s->l)
    h0, h1, h2 = R['h0'], R['h1'], R['h2']
    old = [h2[2], h1[2], h0[2], h0[3], h1[3], h2[3]]            # FO O BO BI I FI
    faces = [face_of([h1[2], h2[2], h2[3], h1[3]]), face_of([h0[2], h1[2], h1[3], h0[3]])]
    secs = LEG
    for pts in secs:
        top = old
        old, faces = ext(bm, faces, old, pts)
    ftop, fbot = top, old
    FO, O, BO, BI, I, FI = range(6)
    wall = lambda a, b: [ftop[a], ftop[b], fbot[b], fbot[a]]
    for a_, b_, dirn, L, tw1, th1, tw2, th2 in TOES:
        toe(bm, wall(a_, b_), dirn, L, tw1, th1, tw2, th2)

    # ---- wings: 2-face patch on the upper flank at the shoulder (rings h2 c0 c1, faces u->s)
    c0, c1 = R['c0'], R['c1']
    old = [c1[1], c0[1], h2[1], h2[2], c0[2], c1[2]]            # P0..P5 at the root
    faces = [face_of([c0[1], c1[1], c1[2], c0[2]]), face_of([h2[1], c0[1], c0[2], h2[2]])]
    wr = Vector(J['wristL'])
    up = Vector((0.0, -0.39, 0.92)).normalized()
    arm = [(0.245, -0.27, 0.97), (0.235, -0.21, 0.965), (0.245, -0.15, 0.96),
           (0.295, -0.15, 0.95), (0.305, -0.21, 0.955), (0.295, -0.27, 0.96)]
    wrist = [wr + Vector((-0.04, 0, 0)) + up * 0.04, wr + Vector((-0.05, 0, 0)), wr + Vector((-0.04, 0, 0)) - up * 0.045,
             wr + Vector((0.035, 0, 0)) - up * 0.045, wr + Vector((0.048, 0, 0)), wr + Vector((0.035, 0, 0)) + up * 0.04]
    secs = [arm, wrist,
            *SAILS]
    for pts in secs:
        old, faces = ext(bm, faces, old, pts)

    # the kit's extrude deletes the old region FACES_ONLY: a 2-face region leaves its
    # interior edge behind as a loose wire; remove those.
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
    recalc_normals(bm)
    return object_from_bm('body', bm)


def rp(name, i):
    """The stage-1 position of vertex i (0 top .. 4 bottom) of trunk ring `name`."""
    n, T, B, W, shape = next(r for r in RINGS if r[0] == name)
    T, B, W = head_ring(n, T, B, W)
    return ring_pts(T, B, W, shape)[i]


def vn(bm, name, i):
    return vert_near(bm, rp(name, i))


def stage2(k, body):
    bm = edit(body)
    # ---- face: eye socket in the upper-side face between the skull ring k1 and the face ring k2
    eye_face = face_of([vn(bm, 'k1', 1), vn(bm, 'k2', 1), vn(bm, 'k2', 2), vn(bm, 'k1', 2)])
    with k.topo(bm, 'inset', 'eye socket: a loop inside the upper face between skull and face rings'):
        inner = inset(bm, [eye_face], 0.30, depth=0.0)
    iv = list(inner[0].verts)
    # the socket: inner ring pushed into the skull, its top pulled under the brow
    n_out = Vector((0.9, -0.2, 0.25)).normalized()
    for v in iv:
        v.co -= n_out * 0.022
    # the brow: the upper edge of the eye face overhangs it (out, forward, a touch down)
    for nm, d in (('k1', (0.022, -0.01, -0.012)), ('k2', (0.03, -0.015, -0.02))):
        vn(bm, nm, 1).co += Vector(d)
    # ---- knee: a loop each side of the knee ring so the bend keeps its volume; the thigh-side
    # loop flares into the feather cuff that ends the drumstick, the shank-side loop is the slim
    # top of the scaled shank
    O = 1
    for a_, b_, t, sc in ((0, 1, 0.80, 1.18), (1, 2, 0.22, 0.88)):
        pa, pb = LEG[a_][O], LEG[b_][O]
        e = edge_near(bm, (pa + pb) / 2)
        with k.topo(bm, 'loop', 'knee: a supporting loop %s the knee ring' % ('above' if a_ == 0 else 'below')):
            nv = loopcut(bm, e, t=t, near=vert_near(bm, pa))
        scale(nv, sc)
    # ---- the gape: the bill's side line (55% height) pressed in, running back and down to a
    # mouth corner under the eye; the upper mandible now overhangs the lower
    for nm, d in (('b3', (-0.004, 0, 0)), ('b2', (-0.012, 0, 0.004)), ('b1', (-0.02, 0, 0.004)),
                  ('b0', (-0.022, 0.0, -0.01)), ('k2', (-0.01, 0.02, -0.025))):
        vn(bm, nm, 2).co += Vector(d)
    # ---- the wing bone: the leading-edge strip overhangs the membrane (P4 = bone-bottom outer)
    for sec, d in zip(SAILS[:3], ((0.024, 0, -0.012), (0.026, 0, -0.012), (0.018, 0, -0.008))):
        vert_near(bm, sec[4]).co += Vector(d)
    # ---- one deliberate cheek/jaw plane under the eye, from the occiput to the mouth corner
    flatten([vn(bm, 'k0', 2), vn(bm, 'k0', 3), vn(bm, 'k1', 2), vn(bm, 'k1', 3), vn(bm, 'k2', 3)])
    # ---- (orchestrator review: parrot read) a raven bill, not a parrot's: the culmen runs longer
    # and straighter to a small hook, the mandibles thinner (bottom verts up)
    for nm, dy, dz in (('b0', 0.0, (0, 0, 0, 0.015, 0.02)),
                       ('b1', -0.03, (0.02, 0.015, 0.01, 0.02, 0.03)),
                       ('b2', -0.06, (0.045, 0.035, 0.02, 0.02, 0.02)),
                       ('b3', -0.08, (0.06, 0.05, 0.03, 0.025, 0.02))):
        vs = [vn(bm, nm, i) for i in range(5)]
        for v, z in zip(vs, dz):
            v.co += Vector((0, dy, z))
    # ---- ventral profile: the breast swells forward, the belly tucks up behind it
    for nm, i, d in (('n0', 4, (0, -0.035, -0.01)), ('n0', 3, (0.01, -0.03, -0.01)),
                     ('c1', 4, (0, -0.04, -0.03)), ('c1', 3, (0.012, -0.035, -0.025)),
                     ('c0', 4, (0, -0.015, -0.03)), ('c0', 3, (0.01, -0.01, -0.02)),
                     ('h1', 4, (0, 0.0, 0.035)), ('h0', 4, (0, 0.0, 0.03)), ('t2', 4, (0, 0.0, 0.02))):
        vn(bm, nm, i).co += Vector(d)
    commit(body, bm)


PAL = {'plumage': '#454a59', 'dark': '#363a47', 'ink': '#2a2c34', 'beak': '#c89233', 'eye': '#ffb21e',
       'membrane': '#7a62a8', 'crest': '#b02cf0', 'scale': '#9a8458'}


def spike(bm, root, tip, side, w, t, mid=0.45, midw=1.1, bend=(0, 0, 0)):
    """A faceted blade / horn / claw: diamond section at the root, a wider diamond at `mid`
    (pushed by `bend` for a curve), one point at the tip. Returns its faces."""
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
    """keymap: list of (faces, key). Object from bm, painted by face membership."""
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


def front_of(name, c):
    T, B = rp(name, 0), rp(name, 4)
    d = B - T
    n = Vector((0.0, d.z, -d.y))
    return (Vector(c) - T).dot(n) > 0


def stage3(k, body):
    bm = edit(body)
    wing_stop = {vn(bm, r, i) for r in ('h2', 'c0', 'c1') for i in (1, 2)}
    leg_stop = {vn(bm, r, i) for r in ('h0', 'h1', 'h2') for i in (2, 3)}
    wing = flood(bm, face_near(bm, (0.17, 0.72, 0.63)), wing_stop)
    leg = flood(bm, face_near(bm, (0.18, 0.07, 0.0), n=(0, 0, -1)), leg_stop)
    root = {f for f in wing if any(v in wing_stop for v in f.verts)}
    # the socket: the inset's inner face, the smallest side-facing quad in the eye region
    cand = [f for f in bm.faces if len(f.verts) == 4 and all(v.co.x > 0.1 for v in f.verts)
            and -0.68 < f.calc_center_median().y < -0.48 and 1.18 < f.calc_center_median().z < 1.36
            and f.normal.x > 0.3]
    socket = min(cand, key=lambda f: f.calc_area())
    sc, sn = socket.calc_center_median(), socket.normal.copy()
    bone_line = [(-0.22, 1.055)] + [(s_[0][1], s_[1][2]) for s_ in SAILS]   # (y, z) of the bone bottom
    z_cuff = LEG[0][1].z + 0.80 * (LEG[1][1].z - LEG[0][1].z)

    def zb(y):
        for (y0, z0), (y1, z1) in zip(bone_line, bone_line[1:]):
            if y <= y1:
                return z0 + (z1 - z0) * max(0.0, (y - y0) / (y1 - y0))
        return bone_line[-1][1]

    key = {}
    for f in bm.faces:
        c = f.calc_center_median()
        if f in wing:
            key[f.index] = 'plumage' if f in root else ('membrane' if c.y > -0.2 and c.z < zb(c.y) - 0.004 else 'ink')
        elif f in leg:
            key[f.index] = 'scale' if c.z < z_cuff else 'plumage'
        elif f is socket:
            key[f.index] = 'ink'
        elif front_of('b0', c):
            key[f.index] = 'beak'
        elif front_of('n0', c) or not front_of('t2', c) or f.normal.z > 0.5:
            key[f.index] = 'dark'          # head and neck, the back saddle (top row of faces), the tail
        else:
            key[f.index] = 'plumage'
    bm.free()
    paint(body, {k_: PAL[k_] for k_ in sorted(set(key.values()))}, lambda c, n, i: key[i])
    pieces = []

    # ---- eye: gold iris, ink pupil (ahead and a touch down), pale glint
    b = bmesh.new()
    look = (sn + Vector((0, -0.45, -0.1))).normalized()
    ec = sc + sn * 0.012
    iris = hexprism(b, ec, look, 0.042, 0.03)
    pup = hexprism(b, ec + look * 0.006 + Vector((0, -0.006, -0.002)), look, 0.024, 0.012)
    glint = spike(b, ec + look * 0.012 + Vector((0, 0.008, 0.014)), ec + look * 0.02 + Vector((0, 0.004, 0.022)),
                  (0, 1, 0), 0.006, 0.004)
    pieces.append(piece('eye', b, [(iris, 'eye'), (pup, 'ink'), (glint, 'eye')]))

    # ---- brow: a dark wedge from behind the eye forward over it, front end low (determined)
    b = bmesh.new()
    br = spike(b, sc + Vector((0.0, 0.075, 0.062)), sc + Vector((0.022, -0.085, 0.022)), (0, 0, 1), 0.026, 0.02,
               mid=0.4, midw=1.2)
    pieces.append(piece('brow', b, [(br, 'ink')]))

    # ---- horns: three violet blades per side sweeping back from brow and skull (dragon read)
    b = bmesh.new()
    hs = []
    # swept back along the skull line (brow 1.40 -> occiput 1.35), rising only at the tips
    for root_, tip_, w, bend in (((0.07, -0.57, 1.385), (0.12, -0.02, 1.41), 0.046, (0, 0, 0.02)),     # main, over the brow
                                 ((0.14, -0.47, 1.30), (0.21, -0.06, 1.24), 0.036, (0.01, 0, 0.02)),   # cheek horn
                                 ((0.035, -0.46, 1.405), (0.06, -0.06, 1.455), 0.03, (0, 0, 0.015))): # crown
        hs += spike(b, root_, tip_, (1, 0, 0.3), w, w * 0.85, mid=0.3, midw=0.9, bend=bend)
    pieces.append(piece('horns', b, [(hs, 'crest')]))

    # ---- hackles: a pale ruff of feather shards round the neck (separate: never the neck base)
    b = bmesh.new()
    hk = []
    for i, (xo, L) in enumerate(((0.04, 0.17), (0.02, 0.19), (0.025, 0.2), (0.02, 0.18), (0.04, 0.16))):
        side_off = Vector((0.045, 0, 0)) if i in (0, 4) else Vector()
        r0, r1, r2 = rp('n1', i) + side_off, rp('n0', i) + side_off, rp('c1', i) + side_off
        out = Vector((1.0, 0, 0)) if i in (1, 2, 3) else Vector((0.3, 0, 0))
        root_ = r0.lerp(rp('k0', i) + side_off, 0.35) + out * xo * 0.5
        d = (r1.lerp(r2, 0.4) - root_).normalized()
        hk += spike(b, root_, root_ + d * L + out * xo, (0, 1, 0) if i in (1, 2, 3) else (1, 0, 0), 0.04, 0.012,
                    mid=0.3, midw=1.15)
    pieces.append(piece('hackles', b, [(hk, 'plumage')]))

    # ---- dorsal ridge: small violet spikes on the midline, nape to tail (one unmirrored piece)
    b = bmesh.new()
    ds = []
    pts = [('n1', 0.06), ('c1', 0.085), ('c0', 0.09), ('h2', 0.085), ('h1', 0.075), ('h0', 0.065), ('t2', 0.055),
           ('t1', 0.045)]
    for (nm, hgt), nxt in zip(pts, pts[1:] + [('t0', 0)]):
        p0, p1 = rp(nm, 0), rp(nxt[0], 0)
        base = p0.lerp(p1, 0.15) - Vector((0, 0, 0.012))
        back = (p1 - p0).normalized()
        upn = Vector((0, -back.z, back.y))
        if upn.z < 0:
            upn = -upn
        ds += spike(b, base, base + upn * hgt + back * hgt * 0.8, (0, 0, 1), hgt * 0.5, 0.016, mid=0.3, midw=1.0)
    pieces.append(piece('spines', b, [(ds, 'crest')], mirror=False))

    # ---- wing: thumb claw at the wrist, finger ribs on the membrane poking past the trailing edge
    b = bmesh.new()
    wr = Vector(J['wristL'])
    up = Vector((0.0, -0.39, 0.92)).normalized()
    thumb = spike(b, wr + up * 0.02 + Vector((0.01, -0.01, 0)), wr + Vector((0.03, -0.12, 0.09)), (1, 0, 0),
                  0.02, 0.018, mid=0.5, bend=(0, -0.01, 0.025))
    ribs, flaps = [], []
    for j, (sec, ext_) in enumerate(zip(SAILS[:3], (0.13, 0.12, 0.09))):
        p4, p3 = Vector(sec[4]) + Vector((0.026, 0, -0.012)), Vector(sec[3])
        d = (p3 - p4).normalized()
        tipp = p3 + d * ext_ + Vector((0.004, 0.05, 0))
        ribs += spike(b, p4 + Vector((0.006, 0, 0.01)), tipp + Vector((0.008, 0, 0)), (0, 1, 0), 0.02, 0.014,
                      mid=0.5, midw=0.85)
        # the membrane follows the finger to its tip: a flap from the trailing edge either side
        # of the rib down to the tip, so the edge scallops between fingers
        ya, yb = sec[3][1] - 0.10, sec[3][1] + 0.12
        def te(y):
            for s0, s1 in zip(SAILS, SAILS[1:]):
                if s0[3][1] <= y <= s1[3][1]:
                    t_ = (y - s0[3][1]) / (s1[3][1] - s0[3][1])
                    return Vector(s0[3]).lerp(Vector(s1[3]), t_)
            return Vector(SAILS[0][3]) + Vector((0, y - SAILS[0][3][1], 0.35 * (SAILS[0][3][1] - y)))
        A, C = te(ya) + Vector((0.004, 0, 0.03)), te(yb) + Vector((0.004, 0, 0.03))
        T_ = tipp + Vector((0.004, 0, 0.01))
        o = Vector((0.006, 0, 0))
        vv = ring(b, [A, T_, C, A - o * 2, T_ - o * 2, C - o * 2])
        flaps += [b.faces.new([vv[0], vv[1], vv[2]]), b.faces.new([vv[5], vv[4], vv[3]]),
                  b.faces.new([vv[0], vv[3], vv[4], vv[1]]), b.faces.new([vv[1], vv[4], vv[5], vv[2]]),
                  b.faces.new([vv[2], vv[5], vv[3], vv[0]])]
    pieces.append(piece('wingbones', b, [(thumb, 'ink'), (ribs, 'ink'), (flaps, 'membrane')]))

    # ---- claws: one hooked ink claw per toe
    b = bmesh.new()
    cl = []
    for i in range(4):
        tp, t = toe_tip(i)
        r0 = tp + Vector((0, 0, 0.013)) - t * 0.012
        L = 0.06 if i < 3 else 0.05
        cl += spike(b, r0, r0 + t * L + Vector((0, 0, -0.011)), (0, 0, 1), 0.014, 0.012, mid=0.45,
                    midw=0.9, bend=(0, 0, 0.012))
    pieces.append(piece('claws', b, [(cl, 'ink')]))

    # ---- tail fan: violet blades fanning back from the tail tip
    b = bmesh.new()
    fan = []
    base = rp('t0', 2)
    for x0, tip_, w in ((0.02, (0.06, 1.09, 0.63), 0.055), (0.045, (0.18, 1.04, 0.58), 0.05),
                        (0.06, (0.26, 0.95, 0.51), 0.042)):
        r0 = Vector((x0, base.y - 0.05, base.z + 0.01))
        fan += spike(b, r0, tip_, (0, 0, 1), w, 0.012, mid=0.45, midw=1.25)
    pieces.append(piece('tailfan', b, [(fan, 'crest')]))
    return pieces


BONES = [('hips', J['hips'], (0.0, -0.02, 0.78), None),
         ('chest', (0.0, -0.02, 0.78), J['neck'], 'hips', True),
         ('neck', J['neck'], (0.0, -0.40, 1.15), 'chest', True),
         ('head', (0.0, -0.40, 1.15), (0.0, -0.95, 1.12), 'neck', True),
         ('crest', (0.0, -0.52, 1.40), (0.0, -0.20, 1.48), 'head'),
         ('tail0', (0.0, 0.34, 0.70), J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('fan', J['tail2'], (0.0, 1.06, 0.60), 'tail1', True),
         ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
         ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
         ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
         ('arm.L', J['shoulderL'], J['wristL'], 'chest'),
         ('hand.L', J['wristL'], J['handL'], 'arm.L', True),
         ('tip.L', J['handL'], J['tipL'], 'hand.L', True)]


def _side_sets(body):
    """Vertex-index sets of the wing and leg of each side on the skinned (mirror-applied) body."""
    bm = edit(body)
    out = {}
    for sx, sd in ((1, 'L'), (-1, 'R')):
        m = lambda p: Vector((p[0] * sx, p[1], p[2]))
        wstop = {vert_near(bm, m(rp(r, i))) for r in ('h2', 'c0', 'c1') for i in (1, 2)}
        lstop = {vert_near(bm, m(rp(r, i))) for r in ('h0', 'h1', 'h2') for i in (2, 3)}
        wf = flood(bm, face_near(bm, m((0.17, 0.72, 0.63))), wstop)
        lf = flood(bm, face_near(bm, m((0.18, 0.07, 0.0)), n=(0, 0, -1)), lstop)
        out['wing.' + sd] = {v.index for f in wf for v in f.verts} - {v.index for v in wstop}
        out['leg.' + sd] = {v.index for f in lf for v in f.verts} - {v.index for v in lstop}
    bm.free()
    return out


def _clean_weights(body, rig):
    """Bone heat bleeds the folded wing into the flank (they sit 2-4 cm apart) and the thighs into
    the belly: keep wing bones on wing verts, leg bones below the hip on leg verts, and the crest
    and fan bones off the body entirely (they carry pieces)."""
    sets = _side_sets(body)
    wing_b = {s: {'arm.' + s, 'hand.' + s, 'tip.' + s} for s in 'LR'}
    leg_b = {s: {'shin.' + s, 'foot.' + s} for s in 'LR'}
    gname = {g.index: g.name for g in body.vertex_groups}
    segs = _bone_segments(rig)
    for v in body.data.vertices:
        allowed = set(segs) - {'crest', 'fan'}
        for s in 'LR':
            if v.index in sets['wing.' + s]:
                allowed = wing_b[s] | {'chest'}
                break
            if v.index in sets['leg.' + s]:
                allowed = leg_b[s] | {'thigh.' + s, 'hips'}
                break
        else:
            allowed -= wing_b['L'] | wing_b['R'] | leg_b['L'] | leg_b['R']
        for g in list(v.groups):
            if gname[g.group] not in allowed and g.weight > 0:
                body.vertex_groups[gname[g.group]].remove([v.index])
        if sum(g.weight for g in v.groups if gname[g.group] in segs) <= 1e-4:
            p = body.matrix_world @ v.co
            nm = min(allowed & set(segs), key=lambda n: _seg_dist(p, *segs[n]))
            vg = body.vertex_groups.get(nm) or body.vertex_groups.new(name=nm)
            vg.add([v.index], 1.0, 'REPLACE')


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
    rig = armature(BONES)
    skin(body, rig)
    _clean_weights(body, rig)
    P = {p.name.replace('piece_', ''): p for p in pieces}
    for nm in ('eye', 'brow'):
        bind(P[nm], rig, bone='head')
    bind(P['horns'], rig, bone='crest')
    bind(P['tailfan'], rig, bone='fan')
    for nm in ('hackles', 'spines', 'wingbones', 'claws'):
        bind(P[nm], rig, body=body)

    # idle: breathing, a head tilt, crest and fan twitch
    clip(rig, 'idle', {1: {}, 12: {'chest': (-2, 0, 0), 'head': (0, 10, 0), 'crest': (-6, 0, 0), 'fan': (0, 0, 8)},
                       24: {'chest': (-3, 0, 0), 'head': (0, 12, 0), 'crest': (4, 0, 0), 'tail0': (0, 0, 4)},
                       36: {'chest': (-1, 0, 0), 'head': (4, -4, 0), 'crest': (-3, 0, 0), 'fan': (0, 0, -6)},
                       48: {}})

    # move: a stalking walk, head low and level, wings tucked
    W = {'neck': (8, 0, 0), 'head': (-6, 0, 0)}
    def step(th, sh, ft, thr, shr, ftr, hips_z, tail_z, head_z):
        d = dict(W)
        d.update({'thigh.L': (th, 0, 0), 'shin.L': (sh, 0, 0), 'foot.L': (ft, 0, 0),
                  'thigh.R': (thr, 0, 0), 'shin.R': (shr, 0, 0), 'foot.R': (ftr, 0, 0),
                  'hips': (0, 0, hips_z), 'tail0': (0, 0, tail_z), 'head': (-6, 0, head_z)})
        return d
    clip(rig, 'move', {1: step(-24, 8, 10, 22, -6, -12, 3, -6, -3),
                       7: step(-4, 2, 0, 6, 26, -30, 0, 0, 0),
                       13: step(22, -6, -12, -24, 8, 10, -3, 6, 3),
                       19: step(6, 26, -30, -4, 2, 0, 0, 0, 0),
                       25: step(-24, 8, 10, 22, -6, -12, 3, -6, -3)})

    # attack: rear back, then a lunge-peck with the wings half-flaring
    clip(rig, 'attack', sym({1: {},
                             8: {'chest': (-6, 0, 0), 'neck': (-14, 0, 0), 'head': (-8, 0, 0), 'crest': (10, 0, 0),
                                 'arm.L': (0, 0, -20), 'hand.L': (0, 0, -14), 'tail0': (-8, 0, 0)},
                             14: {'chest': (10, 0, 0), 'neck': (24, 0, 0), 'head': (14, 0, 0), 'crest': (-4, 0, 0),
                                  'arm.L': (0, 0, -32), 'hand.L': (0, 0, -24), 'tail0': (10, 0, 0),
                                  'thigh.L': (-6, 0, 0)},
                             20: {'chest': (8, 0, 0), 'neck': (18, 0, 0), 'head': (10, 0, 0),
                                  'arm.L': (0, 0, -28), 'hand.L': (0, 0, -20), 'tail0': (8, 0, 0)},
                             32: {}}))
    return rig


run(META, stage1, stage2, stage3, stage4)
