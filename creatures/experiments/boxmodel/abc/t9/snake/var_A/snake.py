import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'kit')))
from bmkit import *
from smooth_borders import smooth_borders
sys.path.insert(0, HERE)
import snake_shape as SS

# t9 RECREATE of zoo/snake (2026-10-23) from refs/gpt/v3/snake/sheet_1.png: a CHUNKY python with a raised S-neck,
# an arched mid-body loop, a curled tail tip and big soft blotches. t7 hand box model: one spine loft of 12-vertex
# half rings (2x density), snout -> tail tip; no limbs. Stages 1-3 straight in plan (the kit's base is a mirrored
# half), carrying the sheet's vertical form; stage 4 lays the body into the sheet's plan-view S (snake_shape.bend).
# Shape tables + the posed-mass check vs the unsymmetrised sheet masks: snake_shape.py, tools/design.py.
VARIANT = os.environ.get('SNAKE_VARIANT', '')          # fix-loop variants (A / B); '' = champion
META = dict(creature='snake', model='opus', stage1_tris=(1500, 4500), total_tris=(2000, 6000), detail_tier=1)

NV = SS.NV
ST = SS.stations()
RING = [SS.ring_pts(s) for s in ST]
EYE_Y = -0.425                         # sheet side: the eye 12 cm behind the snout tip, high on the head side
EYE_J = (4, 5)                         # head ring vertices bounding the eye face (under the brow edge, vertex 3)


def st_index(y):
    return min(range(len(ST)), key=lambda i: abs(ST[i]['y'] - y) + (9 if ST[i]['blend'] < 0.99 else 0))


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, r) for r in RING]
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b)
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    i = st_index(EYE_Y)
    a, b = RING[i], RING[i + 1]
    return sum((Vector(p) for p in (a[EYE_J[0]], a[EYE_J[1]], b[EYE_J[0]], b[EYE_J[1]])), Vector()) / 4, i


def stage2(k, body):
    ec, ei = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec.x) < 0.03 and abs(c.y - ec.y) < 0.03 and abs(c.z - ec.z) < 0.03)
    bm = edit(body)
    heads = [i for i, s in enumerate(ST) if s['blend'] > 0.99]
    # head planes: one flat crown (vertices 0-2) snout -> back of the skull, one flat cheek per side (5-6)
    flatten([vert_near(bm, RING[i][j]) for i in heads[2:] for j in (0, 1, 2)])
    flatten([vert_near(bm, RING[i][j]) for i in heads[2:] for j in (5, 6)])
    # brow: the crown edge (vertex 3) over the eye out a little, so the socket sits under a ledge
    for i in (ei - 1, ei, ei + 1, ei + 2):
        move([vert_near(bm, RING[i][3])], (0.005, 0.0, 0.003))
    # mouth line: the lip vertex (7) in 3 mm along the head
    for i in heads[1:]:
        move([vert_near(bm, RING[i][7])], (-0.003, 0.0, 0.0))
    recalc_normals(bm)
    f = face_near(bm, ec, n=(1, 0, 0.3))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the head-side face under the brow (vertices 4-5)'):
        inner = inset(bm, [f], 0.30, 0.0)
    move(list(inner[0].verts), -fn * 0.004)
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


# ---- colour (sheet): khaki-tan ground, big soft dark-brown blotches, cream belly / throat / jaw, amber eye
PAL = {'tan': '#a08a62', 'brown': '#5c4b39', 'cream': '#e0cfa6', 'amber': '#d9962a', 'black': '#1c1612'}
CY = np.array([s['y'] for s in ST]); CZ = np.array([s['z'] for s in ST])


def local(c):
    """(station index, s, u, fh) of a straight-snake point: u = angle round the ring from the back (0) to the
    belly (pi), fh = the station-frame height share (-1 belly .. 1 back)."""
    i = SS.station_of(c.y, c.z)
    s = ST[i]
    ny, nz = -s['tz'], s['ty']
    off = (c.y - s['y']) * ny + (c.z - s['z']) * nz
    fh = off / (s['Tu'] if off > 0 else s['Td'])
    fx = abs(c.x) / max(s['W'], 1e-4)
    return i, s['s'], math.atan2(fx, fh), fh


S_HEAD = ST[[i for i, s in enumerate(ST) if s['blend'] > 0.99][-1]]['s']
S_END = ST[-1]['s']
# blotches: big soft rounded patches, each two overlapping discs in surface metres (s along the spine, a = arc
# round the ring from the backbone): a saddle over the back, a flank blotch staggered half a period (sheet)
BLOT = []
_s, _n = S_HEAD + 0.09, 0
while _s < S_END - 0.05:
    j = (_n * 7) % 3 - 1
    BLOT.append([(_s, 0.0, 0.066 + 0.006 * j), (_s + 0.028 * j, 0.040, 0.046)])                   # dorsal saddle
    BLOT.append([(_s + 0.108, 0.168 + 0.010 * j, 0.050), (_s + 0.130 + 0.01 * j, 0.142, 0.036)])   # flank blotch
    _s += 0.215 + 0.015 * ((_n * 3) % 3 - 1)
    _n += 1


_BC = {}


def blot_centre(sc, ac):
    """posed surface point of a blotch centre: spine arc sc, ac metres round the ring from the backbone (+x side)."""
    key = (round(sc, 4), round(ac, 4))
    if key not in _BC:
        S = [x['s'] for x in ST]
        i = min(range(len(ST)), key=lambda j: abs(S[j] - sc))
        st = ST[i]
        R = (st['W'] + 0.5 * (st['Tu'] + st['Td'])) / 2
        u = min(math.pi, ac / max(R, 1e-4))
        ny, nz = -st['tz'], st['ty']
        x, fh = st['W'] * math.sin(u), math.cos(u)
        off = fh * (st['Tu'] if fh > 0 else st['Td'])
        _BC[key] = Vector(SS.bend((x, st['y'] + ny * off, st['z'] + nz * off)))
    return _BC[key]


def body_rule(c, n, idx):
    i, s, u, fh = local(c)
    st = ST[i]
    taper = min(1.0, st['W'] / 0.10)                 # blotches shrink with the tail
    if st['blend'] > 0.5:                            # head
        if fh < -0.42:
            return 'cream'                           # jaw and lips
        if u < 0.75 and -0.47 < c.y < -0.38:
            return 'brown'                           # crown patch behind the eyes (sheet top view)
        return 'tan'
    if fh < (-0.25 if s < S_HEAD + 0.40 else -0.42):
        return 'cream'                               # broad cream throat on the neck, belly band on the body
    arc = u * (st['W'] + 0.5 * (st['Tu'] + st['Td'])) / 2        # metres round the ring from the backbone
    k_ = 0.45 + 0.55 * taper
    if VARIANT == 'A':                                # discs measured on the POSED surface: round after the bend
        p = Vector(SS.bend((abs(c.x), c.y, c.z)))
        for discs in BLOT:
            for sc, ac, r in discs:
                if (p - blot_centre(sc, ac * k_)).length < r * k_:
                    return 'brown'
        return 'tan'
    f = 1.0
    if VARIANT == 'B':                                # s distances corrected for the plan bend's squeeze at this face
        q0, q1 = Vector(SS.bend((abs(c.x), c.y - 0.01, c.z))), Vector(SS.bend((abs(c.x), c.y + 0.01, c.z)))
        f = (q1 - q0).length / 0.02
    for discs in BLOT:
        for sc, ac, r in discs:
            if VARIANT == 'B':
                ac, r = ac * 0.9, r * 0.92            # flank blotches a little higher and smaller (off the inner flank)
            if ((s - sc) * f) ** 2 + (arc - ac * k_) ** 2 < (r * k_) ** 2:
                return 'brown'
    return 'tan'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h, sides=8):
    """A low-poly round lens: back cone, iris ring, pupil cap."""
    n, u, w = frame3(n)
    rg = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                           for t in [2 * math.pi * j / sides for j in range(sides)]]
    R, I = rg(r, 0.0), rg(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.3)
    for j in range(sides):
        a, b = j, (j + 1) % sides
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def tongue(bm):
    """One chunky prong of the forked tongue (the mirror makes the fork): buried in the mouth, out past the snout.
    Variants: A = round 6-sided prongs tapering to a blunt tip in a V; B = a shorter stubby round fork."""
    if VARIANT in ('A', 'B'):
        if VARIANT == 'A':
            rows = [(0.0080, -0.505, 0.404, 0.0074), (0.0085, -0.540, 0.401, 0.0074), (0.0120, -0.568, 0.398, 0.0072),
                    (0.0190, -0.590, 0.396, 0.0068), (0.0255, -0.604, 0.394, 0.0064)]
        else:
            rows = [(0.0080, -0.505, 0.404, 0.0078), (0.0090, -0.540, 0.401, 0.0078), (0.0140, -0.565, 0.398, 0.0075),
                    (0.0200, -0.582, 0.396, 0.0070)]
        n6 = 6
        R = [[bm.verts.new((x + r * math.cos(2 * math.pi * j / n6), y, z + r * math.sin(2 * math.pi * j / n6)))
              for j in range(n6)] for x, y, z, r in rows]
        bm.faces.new(list(reversed(R[0])))
        for a, b in zip(R, R[1:]):
            for j in range(n6):
                bm.faces.new([a[j], a[(j + 1) % n6], b[(j + 1) % n6], b[j]])
        x, y, z, r = rows[-1]
        tip = bm.verts.new((x + 0.002, y - 0.008, z))
        for j in range(n6):
            bm.faces.new([R[-1][j], R[-1][(j + 1) % n6], tip])
        return
    rows = [(0.0080, -0.505, 0.404, 0.0072), (0.0085, -0.540, 0.401, 0.0072), (0.0120, -0.570, 0.398, 0.0071),
            (0.0195, -0.592, 0.395, 0.0069), (0.0265, -0.606, 0.393, 0.0066)]
    R = [[bm.verts.new((x + sx * r, y, z + sz * r)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
         for x, y, z, r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def stage3(k, body):
    paint(body, PAL, body_rule)
    smooth_borders(body, k=k, iters=8, despeckle=(VARIANT == 'B'), keep=None if VARIANT == 'B' else ['brown'],
                   keep_area=0.0012 if VARIANT == 'B' else None)
    ec, _ = eye_face_centre()
    bmb = edit(body)
    f = face_near(bmb, ec + Vector((-0.004, 0, 0)), n=(1, 0, 0.3))
    c, n = f.calc_center_median().copy(), f.normal.copy()
    n = n if n.x > 0 else -n
    bmb.free()
    n = (n + Vector((0, -0.35, 0.10))).normalized()          # the lens looks a little forward (front visibility)
    bm = bmesh.new()
    lens(bm, c + n * 0.002, n, 0.0115, 0.0065)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'black': PAL['black']},
          lambda c_, n_, i: 'black' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.0055 and n_.dot(n) > 0.5 else 'amber')
    bm = bmesh.new()
    tongue(bm)
    tg = object_from_bm('tongue', bm)
    paint(tg, {'black': PAL['black']}, lambda c_, n_, i: 'black')
    return [eye, tg]


# ---- stage 4: bend into the plan S, rig along the posed centreline
def _apply_mirror_piece(o):
    for m in list(o.modifiers):
        if m.type == 'MIRROR':
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
                bpy.ops.object.modifier_apply(modifier=m.name)


def spine_at(s):
    """straight-snake spine centre and dorsal normal at arc s (between stations, linear)."""
    S = [x['s'] for x in ST]
    j = min(max(int(np.searchsorted(S, s)) - 1, 0), len(S) - 2)
    t = (s - S[j]) / (S[j + 1] - S[j])
    a, b = ST[j], ST[j + 1]
    y, z = a['y'] + (b['y'] - a['y']) * t, a['z'] + (b['z'] - a['z']) * t
    ty, tz = a['ty'] + (b['ty'] - a['ty']) * t, a['tz'] + (b['tz'] - a['tz']) * t
    return Vector((0.0, y, z)), Vector((0.0, -tz, ty)).normalized()


def bent(p):
    return Vector(SS.bend(tuple(p)))


S_NECK = SS._neck_path()[2][-1]                 # arc at the neck base
# chain joints (arc s): snout, head back, neck x3, body, the root at the arched loop, tail
SJ = [0.0, S_HEAD, S_HEAD + 0.12, S_HEAD + 0.24, S_NECK, S_NECK + 0.14, S_NECK + 0.30, S_NECK + 0.46,
      S_NECK + 0.62, S_NECK + 0.76, S_NECK + 0.88, S_NECK + 0.97, S_NECK + 1.04, S_NECK + 1.09, S_END]


def stage4(k, body, pieces):
    apply_mirror(body)
    for p in pieces:
        _apply_mirror_piece(p)
    for o in [body] + pieces:
        for v in o.data.vertices:
            v.co = bent(v.co)
        o.data.update()
    ec, _ = eye_face_centre()
    ecw, ecm = bent(ec), bent(ec * Vector((-1, 1, 1)))
    k.meta['keep_valleys'] = lambda c: min((c - ecw).length, (c - ecm).length) < 0.03
    J = [bent(spine_at(s)[0]) for s in SJ]
    D = [(bent(spine_at(s)[0] + spine_at(s)[1] * 0.05) - bent(spine_at(s)[0])).normalized() for s in SJ]
    k.meta['closeups'] = [('head', tuple((J[0] + J[1]) / 2), 0.16, 'hero'), ('neck', tuple(J[3]), 0.25, 'az045'),
                          ('arched loop', tuple(J[6]), 0.30, 'az090'), ('tail curl', tuple(J[13]), 0.16, 'hero')]
    #       name     head  tail parent   (root = spine at the arched loop, forward to the head, back to the tail tip)
    B = [('spine', J[7], J[6], None),
         ('chest', J[6], J[5], 'spine', True), ('neck2', J[5], J[4], 'chest', True), ('neck1', J[4], J[3], 'neck2', True),
         ('neck', J[3], J[1], 'neck1', True), ('head', J[1], J[0], 'neck', True),
         ('tail0', J[7], J[8], 'spine'), ('tail1', J[8], J[9], 'tail0', True), ('tail2', J[9], J[10], 'tail1', True),
         ('tail3', J[10], J[11], 'tail2', True), ('tail4', J[11], J[12], 'tail3', True),
         ('tail5', J[12], J[13], 'tail4', True), ('tail6', J[13], J[14], 'tail5', True)]
    rig = armature(B)
    names = [b[0] for b in B]
    dors = dict(zip(names, [D[6], D[5], D[4], D[3], D[2], D[0], D[7], D[8], D[9], D[10], D[11], D[12], D[13]]))
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            eb.align_roll(dors[eb.name])               # local Z = the dorsal side: rot X pitches, rot Z sways
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, bone='head')
    # idle: slow breathing in the loop, the raised head sways and tilts, a lazy tail-tip curl
    clip(rig, 'idle', {1: {}, 12: {'neck1': (0, 0, 3), 'neck': (-2, 0, 2), 'head': (2, 0, 0), 'tail6': (0, 0, 8)},
                       24: {'neck2': (2, 0, 0), 'neck': (2, 0, -3), 'head': (-2, 0, 0)},
                       36: {'neck1': (0, 0, -3), 'neck': (-2, 0, 2), 'head': (2, 0, 0), 'tail6': (0, 0, -8)}, 48: {}})
    # move: a sideways wave from the chest to the tail tip (local Z = dorsal, so rot Z is a lateral sway)
    chain = ['chest', 'tail0', 'tail1', 'tail2', 'tail3', 'tail4', 'tail5']
    keys = {}
    for f in (1, 7, 13, 19, 25):
        ph = 2 * math.pi * (f - 1) / 24
        keys[f] = {b: (0, 0, round(6.0 * math.sin(ph - j * 1.0), 2)) for j, b in enumerate(chain)}
        keys[f]['neck'] = (0, 0, round(-3.0 * math.sin(ph), 2))
    clip(rig, 'move', keys)
    # attack: draw the S-neck back, strike forward and down, recover
    clip(rig, 'attack', {1: {},
                         10: {'neck2': (8, 0, 0), 'neck1': (10, 0, 0), 'neck': (8, 0, 0), 'head': (-6, 0, 0)},
                         16: {'neck2': (-10, 0, 0), 'neck1': (-14, 0, 0), 'neck': (-10, 0, 0), 'head': (8, 0, 0)},
                         20: {'neck2': (-10, 0, 0), 'neck1': (-14, 0, 0), 'neck': (-10, 0, 0), 'head': (8, 0, 0)},
                         32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
