import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='character', model='opus',
            keep_valleys=lambda c: 1.39 < c.z < 1.51 and c.y < -0.10 and abs(c.x) < 0.12)

# the skeleton the model is built on (metres, Z up, faces -Y, left = +X)
J = dict(
    pelvis=(0.0, 0.010, 0.72), spine=(0.0, 0.010, 0.86), chest=(0.0, 0.010, 1.02),
    neck=(0.0, 0.010, 1.17), head=(0.0, 0.010, 1.235), crown=(0.0, 0.010, 1.56),
    hipL=(0.100, 0.010, 0.70), kneeL=(0.105, 0.004, 0.43), ankleL=(0.117, 0.028, 0.075),
    toeL=(0.118, -0.150, 0.020),
    clavL=(0.040, 0.015, 1.12), shoulderL=(0.150, 0.015, 1.10), elbowL=(0.440, 0.018, 1.107),
    wristL=(0.680, 0.019, 1.107), handL=(0.835, 0.022, 1.075),
    eyeL=(0.058, -0.185, 1.450),
)

HEAD_C = (0.010, 1.405)       # head centre (y, z)
HEAD_R = 0.196


def torso_ring(z, rx, yf, yb):
    """half ring: front seam, front corner, side front, side back, back corner, back seam.
    Flat chest, flat side, flat back: a section of planes, not a circle."""
    ys, d = (yf + yb) / 2, yb - yf
    return [(0.0, yf, z), (0.66 * rx, yf + 0.10 * d, z), (rx, ys - 0.25 * d, z),
            (rx, ys + 0.25 * d, z), (0.66 * rx, yb - 0.10 * d, z), (0.0, yb, z)]


def ell_ring(z, cy, rx, ry):
    """half of a 10-gon, from the front seam (-Y) round the left flank to the back seam."""
    return [(rx * math.sin(math.radians(a)), cy - ry * math.cos(math.radians(a)), z)
            for a in (0, 36, 72, 108, 144, 180)]


def limb(bm, faces, axis, stations):
    """Extrude a face region station by station; each new ring is re-drawn as a
    planar (possibly elliptical) section at the station, each vertex keeping its
    angle about the limb axis. axis 'z': station = (z, cx, cy, rx, ry);
    axis 'x': station = (x, cy, cz, ry, rz)."""
    def split(p):
        return (p.z, p.x, p.y) if axis == 'z' else (p.x, p.y, p.z)

    def join(a, u, w):
        return V(u, w, a) if axis == 'z' else V(a, u, w)

    vs = {v for f in faces for v in f.verts}
    us = [split(v.co)[1] for v in vs]; ws = [split(v.co)[2] for v in vs]
    pc = ((max(us) + min(us)) / 2, (max(ws) + min(ws)) / 2)
    pr = (max(1e-4, (max(us) - min(us)) / 2), max(1e-4, (max(ws) - min(ws)) / 2))
    rings = []
    for a, cu, cw, ru, rw in stations:
        ex = extrude(bm, faces)
        for v in ex['verts']:
            _, u, w = split(v.co)
            th = math.atan2((w - pc[1]) / pr[1], (u - pc[0]) / pr[0])
            v.co = join(a, cu + ru * math.cos(th), cw + rw * math.sin(th))
        faces = ex['faces']
        rings.append(list(ex['verts']))
        pc, pr = (cu, cw), (ru, rw)
    return faces, rings


def stage1(k):
    bm = bmesh.new()
    # ---- pelvis floor: the hexagonal leg root plus three crotch quads ----------
    lc, lr = (0.093, 0.010), (0.052, 0.075)
    hx = lambda a, z: (lc[0] + lr[0] * math.cos(math.radians(a)), lc[1] + lr[1] * math.sin(math.radians(a)), z)
    p0 = ring(bm, [(0.0, -0.072, 0.705)])[0]
    h1, h2, h3, h4 = ring(bm, [hx(-60, 0.695), hx(0, 0.69), hx(60, 0.695), hx(120, 0.685)])
    m2, m1 = ring(bm, [(0.041, 0.010, 0.668), (0.066, -0.045, 0.672)])
    c1, c2 = ring(bm, [(0.0, -0.035, 0.66), (0.0, 0.060, 0.662)])
    p5 = ring(bm, [(0.0, 0.105, 0.712)])[0]
    hip_face = bm.faces.new([h1, h2, h3, h4, m2, m1])
    bm.faces.new([p0, h1, m1, c1]); bm.faces.new([c1, m1, m2, c2]); bm.faces.new([c2, m2, h4, p5])
    rows = [[p0, h1, h2, h3, h4, p5]]
    # ---- torso: planar sections, dense only at the shoulder --------------------
    for z, rx, yf, yb in [(0.76, 0.126, -0.080, 0.120), (0.86, 0.106, -0.088, 0.090),
                          (0.96, 0.116, -0.095, 0.108), (1.05, 0.135, -0.082, 0.105),
                          (1.10, 0.142, -0.070, 0.098), (1.157, 0.124, -0.052, 0.080)]:
        rows.append(ring(bm, torso_ring(z, rx, yf, yb)))
    # ---- neck (thin) and head (a faceted ball) --------------------------------
    rows.append(ring(bm, ell_ring(1.175, 0.010, 0.052, 0.050)))
    rows.append(ring(bm, ell_ring(1.215, 0.010, 0.047, 0.046)))
    for z in (1.235, 1.29, 1.345, 1.40, 1.50, 1.555):
        r = math.sqrt(max(HEAD_R ** 2 - (z - HEAD_C[1]) ** 2, 1e-6))
        rows.append(ring(bm, ell_ring(z, HEAD_C[0], r, r * 1.06)))
    gaps = [bridge(bm, a, b) for a, b in zip(rows, rows[1:])]
    pole = ring(bm, [(0.0, HEAD_C[0], 1.600)])[0]
    top = rows[-1]
    for i in range(5):
        bm.faces.new([pole, top[i], top[i + 1]])
    # ---- legs: out of the pelvis floor ---------------------------------------
    leg_st = [(0.60, 0.092, 0.012, 0.052, 0.078), (0.48, 0.103, 0.006, 0.052, 0.058),
              (0.43, 0.105, 0.004, 0.048, 0.054), (0.38, 0.107, 0.010, 0.046, 0.056),
              (0.30, 0.110, 0.020, 0.046, 0.064), (0.14, 0.116, 0.022, 0.033, 0.043),
              (0.075, 0.118, 0.028, 0.037, 0.055), (0.0, 0.118, 0.028, 0.042, 0.062)]
    limb(bm, [hip_face], 'z', leg_st)
    # foot: the front face of the heel block goes forward twice
    cx = 0.118
    recalc_normals(bm)
    ff = face_near(bm, (cx, -0.03, 0.037), n=(0, -1, 0))
    for y, fx, w, ztop in ((-0.115, 0.124, 0.048, 0.062), (-0.190, 0.134, 0.046, 0.038)):
        ex = extrude(bm, [ff])
        mid = centre(ex['verts']).x
        for v in ex['verts']:
            v.co = V(fx + (w if v.co.x > mid else -w), y, ztop if v.co.z > 0.02 else 0.0)
        ff = ex['faces'][0]
    # ---- arms: out of the two shoulder faces on the flat side --------------------
    arm_faces = [gaps[4][2], gaps[5][2]]
    arm_st = [(0.20, 0.020, 1.100, 0.046, 0.042), (0.33, 0.018, 1.104, 0.037, 0.035),
              (0.40, 0.018, 1.106, 0.033, 0.032), (0.44, 0.018, 1.107, 0.031, 0.030),
              (0.48, 0.018, 1.108, 0.032, 0.030), (0.57, 0.018, 1.108, 0.032, 0.029),
              (0.665, 0.018, 1.108, 0.024, 0.021), (0.70, 0.020, 1.106, 0.040, 0.019),
              (0.77, 0.022, 1.100, 0.046, 0.017), (0.815, 0.022, 1.086, 0.042, 0.014),
              (0.84, 0.022, 1.070, 0.034, 0.011)]
    limb(bm, arm_faces, 'x', arm_st)
    # thumb: from the front-lower face of the palm, forward and out
    recalc_normals(bm)
    tf = face_near(bm, (0.735, -0.012, 1.093), n=(0, -1, -0.4))
    for d, s in (((0.012, -0.030, -0.006), 0.8), ((0.020, -0.024, -0.004), 0.7)):
        ex = extrude(bm, [tf], offset=d)
        scale(ex['verts'], s)
        tf = ex['faces'][0]
    snap_seam(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    recalc_normals(bm)
    # face: an eye socket in the big face between the front seam and the first column,
    # rings 1.40-1.50; the nose is the seam vertex at 1.40 pulled out between the sockets
    ef = face_near(bm, (0.054, -0.163, 1.45), n=(0, -1, 0))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face, pushed in'):
        inset(bm, [ef], 0.28, -0.012)
    nose = vert_near(bm, (0.0, -0.197, 1.40))
    nose.co.y -= 0.024
    nose.co.z -= 0.008
    # toe block: a loop round the toe segment of the foot, its top pressed down into a crease
    with k.topo(bm, 'loop', 'toe crease: the ball of the foot / toe block'):
        nv = loopcut(bm, edge_near(bm, (0.178, -0.152, 0.0)), t=0.45)
    for v in nv:
        if v.co.z > 0.02:
            v.co.z -= 0.009
    commit(body, bm)


PAL = {'skin': '#f0b477', 'eye_white': '#f7f7f5', 'black': '#151515', 'brow': '#3a2f2a'}


def _surface(body):
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())

    def hit(p, d):
        d = V(d).normalized()
        loc, nrm, _, _ = tree.ray_cast(V(p) - d * 0.3, d)
        return loc, nrm
    return hit


def disc(c, a, r, back, front, dome, n=10):
    """a closed low-poly lens: n-gon back cap inside, a short wall, a domed front fan."""
    bm = bmesh.new()
    a = V(a).normalized()
    u = a.cross(V(0, 0, 1)).normalized(); w = u.cross(a).normalized()
    ang = [2 * math.pi * i / n + math.pi / n for i in range(n)]
    rim = [(u * math.cos(t) + w * math.sin(t)) * r for t in ang]
    b = ring(bm, [c + a * back + q for q in rim])
    f = ring(bm, [c + a * front + q for q in rim])
    bridge(bm, b, f, closed=True)
    cap(bm, list(reversed(b)))
    tip = ring(bm, [c + a * (front + dome)])[0]
    for i in range(n):
        bm.faces.new([tip, f[i], f[(i + 1) % n]])
    return bm


def bar(hit, pts, aim, half_h, depth_in, depth_out):
    """a thin closed bar laid on the surface through pts (raycast along aim)."""
    bm = bmesh.new()
    secs = []
    for p in pts:
        s, n = hit(p, aim)
        up = V(0, 0, 1) - n * n.dot(V(0, 0, 1)); up.normalize()
        secs.append(ring(bm, [s - n * depth_in - up * half_h, s + n * depth_out - up * half_h,
                              s + n * depth_out + up * half_h, s - n * depth_in + up * half_h]))
    for x, y in zip(secs, secs[1:]):
        bridge(bm, x, y, closed=True)
    cap(bm, secs[0]); cap(bm, list(reversed(secs[-1])))
    return bm


def stage3(k, body):
    paint(body, PAL, lambda c, n, i: 'skin')
    hit = _surface(body)
    hc = V(0.0, 0.010, 1.405)
    e = V(0.062, -0.180, 1.455)
    a = (e - hc).normalized()
    s, _ = hit(e + a * 0.1, -a)
    pieces = []
    for name, r, back, front, dome, n, col, off in (
            ('eye_rim', 0.053, -0.016, 0.010, 0.000, 10, 'black', 0.0),
            ('eye_white', 0.048, -0.012, 0.017, 0.006, 10, 'eye_white', 0.0),
            ('pupil', 0.015, 0.013, 0.028, 0.003, 8, 'black', -0.007)):
        o = V(off, 0, 0); o -= a * a.dot(o)
        ob = object_from_bm(name, disc(s + o, a, r, back, front, dome, n), mirror=True)
        paint(ob, {col: PAL[col]}, lambda c, n_, i, col=col: col)
        pieces.append(ob)
    brow_pts = [(0.022 + 0.085 * t, -0.3, 1.536 + 0.012 * math.sin(math.pi * t) - 0.006 * t) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    brow = object_from_bm('brows', bar(hit, brow_pts, (0, 1, 0), 0.0045, 0.004, 0.005), mirror=True)
    mouth = object_from_bm('mouth', bar(hit, [(-0.03, -0.3, 1.338), (0.0, -0.3, 1.336), (0.03, -0.3, 1.338)],
                                        (0, 1, 0), 0.0028, 0.004, 0.004), mirror=False)
    for ob in (brow, mouth):
        paint(ob, {'brow': PAL['brow']}, lambda c, n_, i: 'brow')
        pieces.append(ob)
    return pieces


def _keys(base, frames):
    """every frame gets the base pose, overridden per frame (clip() keys missing bones at rest)."""
    return {f: {**base, **d} for f, d in frames.items()}


def stage4(k, body, pieces):
    hc = V(0.0, 0.010, 1.405)
    eye = V(J['eyeL']); ea = (eye - hc).normalized()
    rig = armature([
        ('hips', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['crown'], 'neck', True),
        ('eye.L', tuple(eye), tuple(eye + ea * 0.03), 'head'),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
        ('clav.L', J['clavL'], J['shoulderL'], 'chest'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'clav.L', True),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hand.L', J['wristL'], J['handL'], 'forearm.L', True),
    ], roll='auto')
    skin(body, rig)
    # the eye bones carry only the eye pieces: hand any skin weight they took back to the head
    hg = body.vertex_groups.get('head') or body.vertex_groups.new(name='head')
    for nm in ('eye.L', 'eye.R'):
        g = body.vertex_groups.get(nm)
        if g is None:
            continue
        for v in body.data.vertices:
            for ge in v.groups:
                if ge.group == g.index and ge.weight > 0:
                    hg.add([v.index], ge.weight, 'ADD')
        body.vertex_groups.remove(g)
    for p in pieces:
        if p.name.split('_', 1)[-1] in ('eye_rim', 'eye_white', 'pupil'):
            bind(p, rig, bone='head')
            p.vertex_groups.clear()
            gl, gr = p.vertex_groups.new(name='eye.L'), p.vertex_groups.new(name='eye.R')
            for v in p.data.vertices:
                (gl if v.co.x > 0 else gr).add([v.index], 1.0, 'REPLACE')
        else:
            bind(p, rig, body=body)
    # idle: arms relaxed down, breathing in the chest, a blink late in the loop
    rel = {'clav.L': (0, 0, -18), 'clav.R': (0, 0, 18), 'upperarm.L': (0, 0, -32), 'upperarm.R': (0, 0, 32),
           'forearm.L': (15, 0, 0), 'forearm.R': (15, 0, 0), 'eye.L': (0, 0, 0), 'eye.R': (0, 0, 0),
           'chest': (0, 0, 0), 'head': (0, 0, 0)}
    clip(rig, 'idle', _keys(rel, {1: {}, 24: {'chest': (-3, 0, 0), 'head': (2, 0, 0),
                                               'upperarm.L': (0, 0, -30), 'upperarm.R': (0, 0, 30)},
                                  40: {}, 42: {'eye.L': (80, 0, 0), 'eye.R': (80, 0, 0)}, 44: {}, 48: {}}))
    # move: a relaxed walk, arms swing against the legs
    def walk(tl, sl, tr, sr, al, ar, tw):
        return {'thigh.L': (tl, 0, 0), 'shin.L': (sl, 0, 0), 'thigh.R': (tr, 0, 0), 'shin.R': (sr, 0, 0),
                'upperarm.L': (al, 0, -40), 'upperarm.R': (ar, 0, 40), 'chest': (0, tw, 0)}
    wb = {'clav.L': (0, 0, -22), 'clav.R': (0, 0, 22), 'forearm.L': (12, 0, 0), 'forearm.R': (12, 0, 0)}
    clip(rig, 'move', _keys(wb, {1: walk(24, -6, -20, -14, -22, 22, 5), 9: walk(0, -6, 8, -48, 0, 0, 0),
                                 17: walk(-20, -14, 24, -6, 22, -22, -5), 25: walk(8, -48, 0, -6, 0, 0, 0),
                                 33: walk(24, -6, -20, -14, -22, 22, 5)}))
    # attack: guard, wind-up, left jab, recover
    g = {'clav.L': (0, 0, -20), 'clav.R': (0, 0, 20), 'upperarm.L': (30, 0, -42), 'forearm.L': (55, 0, 0),
         'upperarm.R': (30, 0, 42), 'forearm.R': (55, 0, 0), 'chest': (0, 0, 0), 'spine': (0, 0, 0)}
    clip(rig, 'attack', _keys(g, {1: {}, 10: {'chest': (0, 14, 0), 'upperarm.L': (15, 0, -44), 'forearm.L': (65, 0, 0)},
                                  16: {'chest': (4, -18, 0), 'spine': (4, 0, 0), 'upperarm.L': (82, 0, -4), 'forearm.L': (6, 0, 0)},
                                  24: {}, 32: {}}))
    return rig


run(META, stage1, stage2, stage3, stage4)
