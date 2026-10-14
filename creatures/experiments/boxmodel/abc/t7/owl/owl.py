import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
import math

META = dict(creature='owl', model='opus',
            keep_valleys=lambda c: c.y < -0.10 and 0.43 < c.z < 0.57 and abs(c.x) < 0.13)   # sockets dent in

# skeleton the model is built on (metres, faces -Y, left flank +X)
J = dict(root=(0.0, 0.0, 0.10), spine=(0.0, 0.0, 0.24), chest=(0.0, -0.005, 0.36),
         neck=(0.0, -0.01, 0.41), head=(0.0, -0.01, 0.47), crown=(0.0, -0.01, 0.62),
         hipL=(0.07, -0.05, 0.11), ankleL=(0.075, -0.06, 0.03), toeL=(0.075, -0.13, 0.0),
         shoulderL=(0.14, 0.0, 0.34), wtipL=(0.12, 0.14, 0.08),
         tail=(0.0, 0.11, 0.13), tailtip=(0.0, 0.20, 0.06),
         eyeL=(0.075, -0.14, 0.50))

TH = [0, 30, 68, 98, 128, 157, 180]          # half-section angles from the front (non-uniform)
# rings: z, half-width, front depth, back depth
RINGS = [(0.060, 0.060, -0.068, 0.060),      # 0 belly bottom
         (0.100, 0.100, -0.108, 0.092),      # 1 belly underside
         (0.130, 0.128, -0.130, 0.108),      # 2 lower belly
         (0.165, 0.144, -0.145, 0.120),      # 3 wing tip row
         (0.230, 0.150, -0.152, 0.125),      # 4 widest belly
         (0.300, 0.146, -0.148, 0.120),      # 5 upper belly
         (0.360, 0.140, -0.136, 0.108),      # 6 shoulder
         (0.405, 0.140, -0.130, 0.102),      # 7 neck (barely a notch)
         (0.445, 0.150, -0.140, 0.104),      # 8 face bottom
         (0.550, 0.152, -0.140, 0.104),      # 9 brow
         (0.590, 0.130, -0.120, 0.088),      # 10 crown shoulder
         (0.613, 0.072, -0.068, 0.048)]      # 11 crown


def sec(z, w, yf, yb):
    out = []
    for t in TH:
        a = math.radians(t)
        c = math.cos(a)
        x = 0.0 if t in (0, 180) else w * math.sin(a)
        out.append([x, c * (yf if c > 0 else -yb), z])
    return out


def reshape(new, fn):
    for v in new:
        v.co = Vector(fn(v.co.copy()))


def stage1(k):
    bm = bmesh.new()
    P = [sec(*r) for r in RINGS]
    # facial disc: flat, slightly dished, rim at idx2
    for r, ys in ((8, (-0.132, -0.14, -0.128)), (9, (-0.136, -0.145, -0.128))):
        P[r][0][1], P[r][1][1], P[r][2][1] = ys
        P[r][1][0], P[r][2][0] = 0.035, 0.122
    # round skull behind the disc: the side column forward, the back corners full
    for r, sc in ((8, 1.0), (9, 1.0), (10, 0.86)):
        P[r][3][:2] = [0.155 * sc, -0.055 * sc]
        P[r][4][:2] = [0.138 * sc, 0.045 * sc]
        P[r][5][:2] = [0.078 * sc, 0.096 * sc]
    # chin tucks under the disc
    P[7][0][1], P[7][1][1] = -0.12, -0.122
    # tail: the back-bottom of the egg pulled into a short wedge
    P[0][6] = [0.0, 0.195, 0.045]; P[0][5] = [0.035, 0.165, 0.05]
    P[1][6] = [0.0, 0.165, 0.09]; P[1][5] = [0.05, 0.14, 0.097]
    R = [ring(bm, p) for p in P]
    B = [bridge(bm, R[i], R[i + 1]) for i in range(len(R) - 1)]
    cap(bm, list(reversed(R[0])))
    cap(bm, R[-1])
    recalc_normals(bm)

    # legs: from the lower-front belly face, down to an ankle, then a spread foot
    f = B[0][1]
    fv = sorted(f.verts, key=lambda v: (v.co.z, v.co.y))     # low-front, low-back, high-front, high-back
    e = extrude(bm, [f])
    tgt = [(0.040, -0.076, 0.032), (0.089, -0.022, 0.032), (0.062, -0.099, 0.036), (0.110, -0.047, 0.036)]
    for v in e['verts']:
        i = min(range(4), key=lambda j: (fv[j].co - v.co).length)
        v.co = Vector(tgt[i])
    e2 = extrude(bm, e['faces'])
    for v in e2['verts']:
        i = min(range(4), key=lambda j: (Vector(tgt[j]) - v.co).length)
        v.co = Vector([(0.050, -0.077, 0.022), (0.083, -0.028, 0.022), (0.070, -0.096, 0.024), (0.107, -0.054, 0.024)][i])
    e3 = extrude(bm, e2['faces'])
    for v in e3['verts']:
        i = min(range(4), key=lambda j: (Vector([(0.050, -0.077, 0.022), (0.083, -0.028, 0.022), (0.070, -0.096, 0.024), (0.107, -0.054, 0.024)][j]) - v.co).length)
        v.co = Vector([(0.022, -0.08, 0.0), (0.08, 0.012, 0.0), (0.078, -0.148, 0.0), (0.138, -0.06, 0.0)][i])

    # folded wings: the back-side flank region (bands 1-3, idx 3-5) pushed out
    reg = [B[b][i] for b in (3, 4, 5, 6) for i in (2, 3, 4)]
    e3 = extrude(bm, reg)
    for v in e3['verts']:
        d = Vector((v.co.x, v.co.y * 0.4, 0.0)).normalized()
        v.co += d * 0.028
        back = max(0.0, min(1.0, (v.co.y + 0.04) / 0.14))
        if v.co.z < 0.17:                     # wing tip row sweeps down and back past the tail root
            v.co.z -= 0.02 + 0.055 * back; v.co.y += 0.06 * back; v.co.x = max(v.co.x, 0.088)
        elif v.co.z > 0.39:                   # shoulder row tucks under the head
            v.co.x -= 0.016; v.co.z -= 0.012
    # ear tufts: from the upper side-front of the head
    ft = B[9][2]
    e4 = extrude(bm, [ft])
    c0 = centre(e4['verts'])
    for v in e4['verts']:
        d = v.co - c0
        v.co = Vector((0.13, -0.058, 0.616)) + Vector((d.x * 0.5, d.y * 0.28, d.z * 0.4))
    e5 = extrude(bm, e4['faces'])
    c0 = centre(e5['verts'])
    for v in e5['verts']:
        d = v.co - c0
        v.co = Vector((0.158, -0.07, 0.646)) + Vector((d.x * 0.35, d.y * 0.6, d.z * 0.3))
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE = (0.079, -0.135, 0.497)          # centre of the eye quad (band 8, idx1-2)


def stage2(k, body):
    bm = edit(body)
    f = face_near(bm, EYE, n=(0, -1, 0))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye quad, pushed in'):
        inner = inset(bm, [f], 0.2, -0.014)
    # brow: the top edge of the eye quad overhangs the socket
    for v in verts_where(bm, lambda c: abs(c.z - 0.55) < 0.004 and c.y < -0.12 and c.x < 0.05):
        v.co.y -= 0.008
    # chin: the shelf under the disc softened, the throat fills forward
    for v in verts_where(bm, lambda c: abs(c.z - 0.405) < 0.004 and c.y < -0.1):
        v.co.y -= 0.008
    # beak root ridge between the eyes: the seam of the disc comes forward to the rim line
    for v in verts_where(bm, lambda c: c.x < 1e-4 and 0.44 < c.z < 0.46 and c.y < -0.12):
        v.co.y -= 0.004
    # crown: a low dome, the top plate lifted at the centre line
    for v in verts_where(bm, lambda c: c.z > 0.605 and c.x < 0.03):
        v.co.z += 0.006
    commit(body, bm)


PAL = {'brown': '#7a5a3c', 'dark': '#4a3424', 'cream': '#efe3c6', 'orange': '#f08a1c',
       'pupil': '#111111', 'beak': '#d8b870', 'white': '#fbf7ee'}


def body_rule(c, n, i):
    ax = abs(c.x)
    if c.z < 0.037:
        return 'beak'                                   # toes
    if c.z > 0.6 and ax > 0.1:
        return 'dark'                                   # tufts
    if 0.445 < c.z < 0.552 and c.y < -0.10 and ax < 0.124:
        return 'cream'                                  # facial disc and sockets
    if 0.44 < c.z < 0.555 and ax >= 0.12 and c.y < -0.03:
        return 'dark'                                   # disc rim
    if 0.40 < c.z < 0.447 and c.y < -0.09 and ax < 0.11:
        return 'cream'                                  # lower disc (chin)
    if 0.40 < c.z < 0.447 and c.y < -0.05:
        return 'dark'                                   # rim under the disc, at the sides
    if 0.55 < c.z < 0.595 and c.y < -0.07 and ax < 0.1:
        return 'cream'                                  # upper disc behind the brows
    if c.y > 0.12 and c.z < 0.12:
        return 'dark'                                   # tail
    if c.z < 0.085 and c.y < 0.03:
        return 'cream'                                  # feathered legs, belly underside
    if 0.07 < c.z < 0.405 and c.y < -0.05 and n.y < -0.45 and ax < 0.125:
        return 'cream'                                  # breast
    if 0.085 < c.z < 0.41 and ax > 0.08 and c.y > -0.10:
        return 'dark'                                   # folded wings
    return 'brown'


def frame_of_face(f):
    n = f.normal.copy()
    u = Vector((0, 0, 1)).cross(n).normalized()
    if u.x < 0:
        u = -u
    v = n.cross(u).normalized()
    if v.z < 0:
        v = -v
    return f.calc_center_median(), u, v, n


def disc(bm, C, u, v, n, r, s0, s1, sides=8, sq=1.0):
    """A low-poly disc (prism) from s0 to s1 along n, radius r (sq squashes v)."""
    rows = []
    for s in (s0, s1):
        rows.append([bm.verts.new(C + n * s + u * (r * math.cos(2 * math.pi * (i + 0.5) / sides))
                                  + v * (r * sq * math.sin(2 * math.pi * (i + 0.5) / sides))) for i in range(sides)])
    bridge(bm, rows[0], rows[1], closed=True)
    cap(bm, list(reversed(rows[0]))); cap(bm, rows[1])


def strip(bm, pts, up, w, d, fwd):
    """A bar along a polyline: 4-sided sections (w tall along up, d deep along fwd)."""
    rows = []
    for p in pts:
        p = Vector(p)
        rows.append([bm.verts.new(p + up * a * w * 0.5 + fwd * b * d * 0.5) for a, b in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    for a_, b_ in zip(rows, rows[1:]):
        bridge(bm, a_, b_, closed=True)
    cap(bm, list(reversed(rows[0]))); cap(bm, rows[-1])


def claw(bm, base, tip, r):
    base, tip = Vector(base), Vector(tip)
    d = (tip - base).normalized()
    a = d.cross(Vector((0, 0, 1))).normalized()
    b = a.cross(d).normalized()
    ring_ = [bm.verts.new(base + (a * math.cos(t) + b * math.sin(t)) * r) for t in (0.0, 2.094, 4.189)]
    t_ = bm.verts.new(tip)
    for i in range(3):
        bm.faces.new([ring_[i], ring_[(i + 1) % 3], t_])
    bm.faces.new(list(reversed(ring_)))


def piece(name, build, colour):
    bm = bmesh.new()
    build(bm)
    ob = object_from_bm(name, bm, mirror=True)
    paint(ob, {colour: PAL[colour]}, lambda c, n, i: colour)
    return ob


def stage3(k, body):
    paint(body, PAL and {x: PAL[x] for x in ('brown', 'dark', 'cream', 'beak')}, body_rule)
    bm0 = edit(body)
    sock = min((f for f in bm0.faces if f.normal.y < -0.8 and 0.04 < f.calc_center_median().x < 0.115
                and 0.46 < f.calc_center_median().z < 0.535 and len(f.verts) == 4),
               key=lambda f: (f.calc_center_median() - Vector(EYE)).length)
    C, u, v, n = frame_of_face(sock)
    bm0.free()
    P = [piece('iris', lambda bm: disc(bm, C, u, v, n, 0.037, -0.004, 0.017), 'orange'),
         piece('pupil', lambda bm: disc(bm, C - v * 0.004, u, v, n, 0.02, 0.016, 0.021), 'pupil'),
         piece('glint', lambda bm: disc(bm, C + u * 0.008 + v * 0.006, u, v, n, 0.006, 0.020, 0.024, sides=4), 'white')]
    # V brows: inner end low (over the beak root), outer end high: a confident glare
    P.append(piece('brow', lambda bm: strip(bm, [(0.012, -0.150, 0.523), (0.066, -0.153, 0.545), (0.118, -0.124, 0.562)],
                                            Vector((0, 0.25, 1)).normalized(), 0.013, 0.014, Vector((0, -1, 0))), 'dark'))

    def beak(bm):
        rt0, rb0 = bm.verts.new((0, -0.125, 0.505)), bm.verts.new((0, -0.125, 0.468))
        rt1, rb1 = bm.verts.new((0.018, -0.125, 0.502)), bm.verts.new((0.018, -0.125, 0.471))
        mt0, mb0 = bm.verts.new((0, -0.160, 0.497)), bm.verts.new((0, -0.153, 0.467))
        mt1, mb1 = bm.verts.new((0.012, -0.156, 0.492)), bm.verts.new((0.012, -0.151, 0.469))
        tip = bm.verts.new((0, -0.176, 0.450))
        for q in ([rt0, rt1, mt1, mt0], [rb0, mb0, mb1, rb1], [rt1, rb1, mb1, mt1], [rt0, rb0, rb1, rt1],
                  [mt0, mt1, tip], [mt1, mb1, tip], [mb1, mb0, tip]):
            bm.faces.new(q)
    P.append(piece('beak', beak, 'beak'))

    def talons(bm):
        c0 = Vector((0.08, -0.068, 0.0))
        for t in ((0.078, -0.148), (0.022, -0.08), (0.138, -0.06), (0.08, 0.012)):
            p = Vector((t[0], t[1], 0.006))
            d = (p - c0); d.z = 0; d.normalize()
            claw(bm, p - d * 0.006, p + d * 0.02 - Vector((0, 0, 0.004)), 0.006)
    P.append(piece('talon', talons, 'dark'))

    def tuft(bm):
        claw(bm, (0.132, -0.056, 0.612), (0.172, -0.042, 0.634), 0.008)
    P.append(piece('tuft', tuft, 'dark'))
    return P


def force(ob, pred, bone_of):
    """Weight the skin where pred(world co) holds 100% to one bone (so rigid pieces on it cannot drift)."""
    for v in ob.data.vertices:
        co = ob.matrix_world @ v.co
        if pred(co):
            for g in list(v.groups):
                ob.vertex_groups[g.group].remove([v.index])
            nm = bone_of(co)
            vg = ob.vertex_groups.get(nm) or ob.vertex_groups.new(name=nm)
            vg.add([v.index], 1.0, 'REPLACE')


def stage4(k, body, pieces):
    rig = armature([('root', J['root'], J['spine'], None),
                    ('chest', J['spine'], J['chest'], 'root', True),
                    ('neck', J['chest'], (0.0, -0.01, 0.43), 'chest', True),
                    ('head', (0.0, -0.01, 0.43), J['crown'], 'neck', True),
                    ('thigh.L', J['hipL'], J['ankleL'], 'root'),
                    ('foot.L', J['ankleL'], J['toeL'], 'thigh.L', True),
                    ('wing.L', J['shoulderL'], J['wtipL'], 'chest'),
                    ('tail', J['tail'], J['tailtip'], 'root')], roll='auto')
    skin(body, rig)
    force(body, lambda c: c.z > 0.438, lambda c: 'head')
    force(body, lambda c: c.z < 0.03, lambda c: 'foot.L' if c.x > 0 else 'foot.R')
    for p in pieces:
        if p.name.startswith('piece_talon') or p.name == 'talon':
            bind(p, rig)
            p.vertex_groups.clear()
            force(p, lambda c: True, lambda c: 'foot.L' if c.x > 0 else 'foot.R')
        else:
            bind(p, rig, bone='head')
    W = lambda a: {'wing.L': (0, 0, a), 'wing.R': (0, 0, -a)}
    clip(rig, 'idle', {1: {}, 10: {'neck': (0, 15, 0), 'head': (0, 25, 0)}, 20: {'neck': (0, 15, 0), 'head': (0, 25, 0)},
                       30: {'neck': (0, -8, 0), 'head': (-6, -14, 0), 'chest': (2, 0, 0)},
                       40: {'chest': (3, 0, 0)}, 48: {}})
    clip(rig, 'move', {1: {}, 5: {'chest': (6, 0, 0), **W(8)}, 10: {'chest': (-4, 0, 0), **W(28)},
                       15: {**W(10)}, 20: {'chest': (4, 0, 0), **W(18)}, 24: {}},
         loc={1: {'root': (0, 0, 0)}, 5: {'root': (0, -0.008, 0)}, 10: {'root': (0, 0.05, 0)},
              15: {'root': (0, 0.06, 0)}, 20: {'root': (0, 0.0, 0)}, 24: {'root': (0, 0, 0)}})
    clip(rig, 'attack', {1: {}, 8: {'chest': (-8, 0, 0), 'head': (8, 0, 0), **W(30)},
                         16: {'chest': (-14, 0, 0), 'head': (12, 0, 0), 'thigh.L': (40, 0, 0), 'thigh.R': (40, 0, 0),
                              'foot.L': (25, 0, 0), 'foot.R': (25, 0, 0), 'tail': (-10, 0, 0), **W(36)},
                         24: {'chest': (-4, 0, 0), **W(15)}, 32: {}},
         loc={1: {'root': (0, 0, 0)}, 8: {'root': (0, 0.02, 0)}, 16: {'root': (0, 0.05, 0.02)},
              24: {'root': (0, 0.01, 0)}, 32: {'root': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
