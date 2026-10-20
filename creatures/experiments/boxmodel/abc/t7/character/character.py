import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from bmkit import _fill_unweighted
from mathutils import Vector
from mathutils.bvhtree import BVHTree

META = dict(creature='character', model='opus', engine_glb='')

# the skeleton the model is built on (metres, -Y forward, left = +X, feet on z = 0)
J = dict(hip=(0, 0.0, 0.80), spine=(0, 0.0, 0.93), chest=(0, 0.0, 1.06), neck=(0, 0.0, 1.15),
         head=(0, -0.005, 1.225), head_top=(0, -0.005, 1.58),
         hipL=(0.085, 0.0, 0.72), kneeL=(0.09, -0.008, 0.40), ankleL=(0.10, 0.0, 0.085),
         toeL=(0.10, -0.16, 0.025),
         clavL=(0.035, 0.0, 1.12), shoulderL=(0.19, 0.0, 1.07), elbowL=(0.425, 0.004, 1.07),
         wristL=(0.605, 0.0, 1.068), handL=(0.735, 0.0, 1.055))

HEX_LEG = (240, 300, 0, 60, 120, 180)              # Fi F1 S B1 Bi Mi around a leg (xy plane)
ARM_DIRS = ((-0.87, 0.5), (0, 1), (0.87, 0.5), (0.87, -0.5), (0, -1), (-0.87, -0.5))  # ft t bt bb b fb


def legsec(cx, cy, z, rx, ry):
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)), z) for a in HEX_LEG]


def armsec(x, cy, cz, ry, rz):
    return [(x, cy + dy * ry, cz + dz * rz) for dy, dz in ARM_DIRS]


def hring(z, f0, f1, s, b1, b0, yc=0.0):
    """Half ring front seam -> back seam: F0, F1, S, B1, B0 (an 8-sided section)."""
    return [(0.0, yc + f0, z), (f1[0], yc + f1[1], z), (s[0], yc + s[1], z), (b1[0], yc + b1[1], z), (0.0, yc + b0, z)]


def grow(bm, faces, order, rows):
    """Extrude the region again and again; place each new ring (mapped to `order`)."""
    rings = [order]
    for pts in rows:
        base = [v.co.copy() for v in order]
        r = extrude(bm, faces)
        nv = r['verts']
        order = [min(nv, key=lambda w: (w.co - b).length) for b in base]
        place(order, pts)
        faces = r['faces']
        rings.append(order)
    return faces, rings


def face_of(vs):
    return next(f for f in vs[0].link_faces if set(f.verts) == set(vs))


def stage1(k):
    bm = bmesh.new()
    R = [hring(0.76, -0.075, (0.09, -0.075), (0.155, 0.005), (0.095, 0.085), 0.09),     # hips
         hring(0.90, -0.07, (0.075, -0.07), (0.125, 0.0), (0.075, 0.065), 0.06),       # waist
         hring(1.00, -0.09, (0.09, -0.085), (0.145, 0.0), (0.09, 0.075), 0.07),        # chest
         hring(1.13, -0.07, (0.10, -0.065), (0.165, 0.0), (0.10, 0.07), 0.075),        # shoulders
         hring(1.175, -0.042, (0.032, -0.032), (0.046, 0.0), (0.032, 0.034), 0.045),   # neck base
         hring(1.215, -0.040, (0.030, -0.030), (0.044, 0.0), (0.030, 0.032), 0.043),   # neck top
         hring(1.235, -0.10, (0.075, -0.075), (0.10, 0.0), (0.065, 0.055), 0.07, -0.005),   # jaw underside
         hring(1.275, -0.15, (0.115, -0.115), (0.152, 0.0), (0.105, 0.10), 0.125, -0.005),   # jaw
         hring(1.35, -0.178, (0.134, -0.13), (0.19, 0.0), (0.13, 0.122), 0.17, -0.005),     # cheek
         hring(1.46, -0.175, (0.134, -0.128), (0.19, 0.0), (0.13, 0.122), 0.17, -0.005),    # brow
         hring(1.548, -0.13, (0.105, -0.098), (0.145, 0.0), (0.103, 0.095), 0.128, -0.005), # crown
         hring(1.60, -0.06, (0.05, -0.045), (0.068, 0.0), (0.05, 0.044), 0.06, -0.005)]     # top
    rings = [ring(bm, r) for r in R]
    bands = [bridge(bm, a, b) for a, b in zip(rings, rings[1:])]
    cap(bm, rings[-1])
    # groin: seam strip + one hexagon per leg
    F0, F1, S, B1, B0 = rings[0]
    Cf, C, Cb, Fi, Mi, Bi = ring(bm, [(0, -0.055, 0.715), (0, 0.0, 0.70), (0, 0.06, 0.715),
                                      (0.032, -0.05, 0.712), (0.022, 0.002, 0.692), (0.032, 0.055, 0.712)])
    for q in ([F0, F1, Fi, Cf], [Cf, Fi, Mi, C], [C, Mi, Bi, Cb], [Cb, Bi, B1, B0]):
        bm.faces.new(q)
    legf = bm.faces.new([Fi, F1, S, B1, Bi, Mi])
    # leg: thigh, knee (3 loops), calf, ankle, sole
    lx = J['hipL'][0]
    _, L = grow(bm, [legf], [Fi, F1, S, B1, Bi, Mi], [
        legsec(lx, 0.0, 0.62, 0.062, 0.068),
        legsec(0.088, -0.004, 0.45, 0.047, 0.052),
        legsec(0.09, -0.008, 0.40, 0.045, 0.050),
        legsec(0.092, -0.004, 0.35, 0.044, 0.050),
        legsec(0.095, 0.004, 0.25, 0.045, 0.056),
        legsec(0.10, 0.0, 0.09, 0.034, 0.036),
        legsec(0.10, 0.005, 0.0, 0.045, 0.052)])
    A, So = L[-2], L[-1]
    ff = face_of([A[0], A[1], So[1], So[0]])
    grow(bm, [ff], [A[0], A[1], So[1], So[0]], [
        [(0.056, -0.11, 0.058), (0.146, -0.11, 0.054), (0.152, -0.11, 0.0), (0.052, -0.11, 0.0)],
        [(0.058, -0.14, 0.048), (0.144, -0.14, 0.045), (0.150, -0.14, 0.0), (0.054, -0.14, 0.0)],
        [(0.064, -0.198, 0.036), (0.138, -0.192, 0.032), (0.142, -0.198, 0.0), (0.060, -0.204, 0.0)]])
    # arm out of the two side faces of the chest band
    r2, r3 = rings[2], rings[3]
    armf = [bands[2][1], bands[2][2]]
    order = [r3[1], r3[2], r3[3], r2[3], r2[2], r2[1]]
    cz = J['shoulderL'][2]
    _, AR = grow(bm, armf, order, [
        armsec(0.20, 0.0, cz + 0.005, 0.055, 0.058),
        armsec(0.30, 0.0, cz, 0.045, 0.045),
        armsec(0.39, 0.002, cz, 0.038, 0.038),
        armsec(0.425, 0.004, cz, 0.037, 0.036),
        armsec(0.46, 0.003, cz, 0.038, 0.038),
        armsec(0.53, 0.0, cz, 0.040, 0.037),
        armsec(0.60, 0.0, cz - 0.002, 0.031, 0.026),
        armsec(0.635, 0.0, cz - 0.002, 0.052, 0.030),
        armsec(0.69, 0.0, cz - 0.004, 0.056, 0.028),
        armsec(0.725, 0.0, cz - 0.014, 0.053, 0.024),
        armsec(0.752, 0.0, cz - 0.03, 0.046, 0.017)])
    P, Kn = AR[8], AR[9]
    tf = face_of([P[0], P[5], Kn[5], Kn[0]])
    grow(bm, [tf], [P[0], P[5], Kn[5], Kn[0]], [
        [(0.640, -0.072, cz + 0.010), (0.640, -0.072, cz - 0.016), (0.670, -0.072, cz - 0.016), (0.670, -0.072, cz + 0.010)],
        [(0.668, -0.100, cz - 0.002), (0.668, -0.100, cz - 0.022), (0.694, -0.094, cz - 0.024), (0.694, -0.094, cz - 0.004)]])
    snap_seam(bm, 1e-6)
    return object_from_bm('body', bm)


EYE = (0.067, 1.405)          # eye centre (x, z) on the face plane between the cheek and brow rings
META['keep_valleys'] = lambda c: 1.35 < c.z < 1.465 and 0.004 < abs(c.x) < 0.135 and c.y < -0.1


def stage2(k, body):
    bm = edit(body)
    # the eye plane: one flat facet per eye, then a shallow socket inside it
    ef = face_near(bm, (EYE[0], -0.16, EYE[1]), n=(0.35, -0.94, 0))
    flatten(list(ef.verts))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye facet at 25%, floor 4 mm in'):
        inset(bm, [ef], 0.25, -0.004)
    commit(body, bm)


PAL = {'skin': '#f0b477', 'white': '#f7f7f5', 'black': '#151515', 'brow': '#3a2f2a'}


def _hit(tree, x, z):
    loc, nrm, _, _ = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
    if nrm.y > 0:
        nrm = -nrm
    return loc, nrm.normalized()


def _frame(n):
    u = (Vector((1, 0, 0)) - n * n.x).normalized()
    v = n.cross(u).normalized()
    return u, (v if v.z > 0 else -v)


def prism(bm, c, n, u, v, rx, ry, back, front, sides=10):
    rows = []
    for d in (back, front):
        rows.append(ring(bm, [c + n * d + u * (rx * math.cos(2 * math.pi * i / sides)) +
                              v * (ry * math.sin(2 * math.pi * i / sides)) for i in range(sides)]))
    fs = [cap(bm, rows[0][::-1]), cap(bm, rows[1])] + bridge(bm, rows[0], rows[1], closed=True)
    return len(fs)


def strip(tree, pts, h, emb, out, seam_start=False):
    """A thin bar laid on the face through sample points (x, z): embedded `emb`, proud `out`."""
    bm = bmesh.new()
    secs = []
    for x, z in pts:
        p, n = _hit(tree, x, z)
        u = Vector((0, 0, 1)) - n * n.z
        u.normalize()
        sec = [p + n * out + u * h / 2, p + n * out - u * h / 2, p - n * emb - u * h / 2, p - n * emb + u * h / 2]
        if seam_start and x == 0.0:
            for q in sec:
                q.x = 0.0
        secs.append(ring(bm, sec))
    for a, b in zip(secs, secs[1:]):
        bridge(bm, a, b, closed=True)
    if not seam_start:
        cap(bm, secs[0][::-1])
    cap(bm, secs[-1])
    return bm


def stage3(k, body):
    paint(body, {'skin': PAL['skin']}, lambda c, n, i: 'skin')
    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)
    pieces = []
    # eyes: outline disc, white sclera, black pupil; rooted in the socket floor, proud of the rim
    c, n = _hit(tree, EYE[0], EYE[1])
    k.eye_c = c.copy()
    u, v = _frame(n)
    for side in ('L', 'R'):
        bm = bmesh.new()
        keys = ['black'] * prism(bm, c, n, u, v, 0.052, 0.055, -0.003, 0.0075)
        keys += ['white'] * prism(bm, c, n, u, v, 0.046, 0.049, -0.002, 0.0095)
        pc = c - u * 0.015 - v * 0.008
        keys += ['black'] * prism(bm, pc, n, u, v, 0.021, 0.024, 0.006, 0.0115, sides=8)
        if side == 'R':
            for w in bm.verts:
                w.co.x = -w.co.x
        ob = object_from_bm('eye_' + side, bm, mirror=False)
        paint(ob, {'white': PAL['white'], 'black': PAL['black']}, lambda c_, n_, i: keys[i])
        pieces.append(ob)
    # brows: thin dark arches over the eyes
    ob = object_from_bm('brows', strip(tree, [(0.03, 1.476), (0.07, 1.488), (0.112, 1.479)], 0.011, 0.003, 0.004))
    paint(ob, {'brow': PAL['brow']}, lambda c_, n_, i: 'brow'); pieces.append(ob)
    # mouth: a short straight line across the seam
    ob = object_from_bm('mouth', strip(tree, [(0.0, 1.292), (0.017, 1.292), (0.032, 1.294)], 0.008, 0.003, 0.004, seam_start=True))
    paint(ob, {'brow': PAL['brow']}, lambda c_, n_, i: 'brow'); pieces.append(ob)
    # nose: a tiny skin pyramid on the seam
    bm = bmesh.new()
    t, tn = _hit(tree, 0.0, 1.354); b, bn = _hit(tree, 0.0, 1.318); sd, sn = _hit(tree, 0.02, 1.332)
    t = t - tn * 0.004; b = b - bn * 0.004; sd = sd - sn * 0.004
    t.x = b.x = 0.0
    tip = Vector((0.0, min(t.y, b.y) - 0.022, 1.328))
    top, bot, sid, tp = ring(bm, [t, b, sd, tip])
    for f in ([top, sid, tp], [sid, bot, tp], [bot, top, sid]):
        bm.faces.new(f)
    ob = object_from_bm('nose', bm)
    paint(ob, {'skin': PAL['skin']}, lambda c_, n_, i: 'skin'); pieces.append(ob)
    ebm.free()
    return pieces


def stage4(k, body, pieces):
    e = k.eye_c
    B = [('hips', J['hip'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['head_top'], 'neck', True),
         ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
         ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
         ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
         ('clavicle.L', J['clavL'], J['shoulderL'], 'chest'),
         ('upper_arm.L', J['shoulderL'], J['elbowL'], 'clavicle.L', True),
         ('forearm.L', J['elbowL'], J['wristL'], 'upper_arm.L', True),
         ('hand.L', J['wristL'], J['handL'], 'forearm.L', True),
         ('eye.L', tuple(e), (e.x, e.y, e.z + 0.03), 'head')]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for nm in ('eye.L', 'eye.R'):              # the eyes blink by scale: keep their bones off the skin
        g = body.vertex_groups.get(nm)
        if g:
            body.vertex_groups.remove(g)
    hg = body.vertex_groups['head']
    for vx in body.data.vertices:
        if sum(g.weight for g in vx.groups) < 1e-4:
            hg.add([vx.index], 1.0, 'REPLACE')
    for p in pieces:
        if p.name.endswith('eye_L'):
            bind(p, rig, bone='eye.L')
        elif p.name.endswith('eye_R'):
            bind(p, rig, bone='eye.R')
        else:
            bind(p, rig, body=body)

    def arms(lx, rx, lz=-68, fl=12, fr=12):
        return {'upper_arm.L': (lx, 0, lz), 'upper_arm.R': (rx, 0, -lz), 'forearm.L': (fl, 0, 0), 'forearm.R': (fr, 0, 0)}

    rest_ = arms(5, 5)
    breathe = dict(arms(5, 5, -66), chest=(-2.5, 0, 0), head=(-2, 0, 0), **{'clavicle.L': (0, 0, 3), 'clavicle.R': (0, 0, -3)})
    act = clip(rig, 'idle', {1: rest_, 25: breathe, 49: rest_})
    ad = rig.animation_data
    ad.action = act
    for f, sc in ((1, 1.0), (40, 1.0), (42, 0.12), (44, 1.0), (49, 1.0)):
        for nm in ('eye.L', 'eye.R'):
            pb = rig.pose.bones[nm]
            pb.scale = (1.0, sc, 1.0)
            pb.keyframe_insert('scale', frame=f)
    ad.action = None
    rest(rig)
    # walk: contact, passing, contact (mirrored), passing
    m1 = dict(arms(-18, 18), spine=(3, 4, 0), **{'thigh.L': (22, 0, 0), 'shin.L': (-4, 0, 0), 'foot.L': (8, 0, 0),
                                                 'thigh.R': (-20, 0, 0), 'shin.R': (-12, 0, 0), 'foot.R': (-10, 0, 0)})
    m17 = dict(arms(18, -18), spine=(3, -4, 0), **{'thigh.R': (22, 0, 0), 'shin.R': (-4, 0, 0), 'foot.R': (8, 0, 0),
                                                   'thigh.L': (-20, 0, 0), 'shin.L': (-12, 0, 0), 'foot.L': (-10, 0, 0)})
    m9 = dict(arms(0, 0), spine=(3, 0, 0), **{'thigh.L': (2, 0, 0), 'shin.L': (-2, 0, 0), 'thigh.R': (14, 0, 0), 'shin.R': (-42, 0, 0)})
    m25 = dict(arms(0, 0), spine=(3, 0, 0), **{'thigh.R': (2, 0, 0), 'shin.R': (-2, 0, 0), 'thigh.L': (14, 0, 0), 'shin.L': (-42, 0, 0)})
    up = {'hips': (0, 0.012, 0)}; zero = {'hips': (0, 0, 0)}
    clip(rig, 'move', {1: m1, 9: m9, 17: m17, 25: m25, 33: m1}, loc={1: zero, 9: up, 17: zero, 25: up, 33: zero})
    # punch with the right fist
    guard = {'upper_arm.L': (35, 0, -60), 'forearm.L': (70, 0, 0), 'upper_arm.R': (35, 0, 60), 'forearm.R': (70, 0, 0)}
    wind = dict(guard, chest=(0, -12, 0), **{'upper_arm.R': (-15, 0, 55), 'forearm.R': (95, 0, 0),
                                             'thigh.L': (12, 0, 0), 'shin.L': (-10, 0, 0), 'thigh.R': (-8, 0, 0)})
    hit = dict(guard, chest=(4, 16, 0), **{'upper_arm.R': (82, 0, 4), 'forearm.R': (4, 0, 0),
                                           'thigh.L': (16, 0, 0), 'shin.L': (-14, 0, 0), 'thigh.R': (-12, 0, 0)})
    clip(rig, 'attack', {1: guard, 10: wind, 17: hit, 22: hit, 33: guard})
    return rig


run(META, stage1, stage2, stage3, stage4)
