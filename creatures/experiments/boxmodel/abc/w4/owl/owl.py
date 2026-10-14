import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='owl', model='opus',
            keep_valleys=lambda c: c.y < -0.15 and 0.48 < c.z < 0.56 and 0.02 < abs(c.x) < 0.10)

# the skeleton the model is built on (metres, faces -Y, left flank +X)
J = dict(
    hips=(0.0, 0.02, 0.12), chest=(0.0, 0.0, 0.30), neck=(0.0, -0.02, 0.43),
    head=(0.0, -0.03, 0.48), crown=(0.0, -0.04, 0.62),
    hipL=(0.080, 0.005, 0.11), kneeL=(0.082, 0.004, 0.045), ankleL=(0.085, -0.005, 0.02),
    toeL=(0.088, -0.095, 0.01),
    shoulderL=(0.165, 0.0, 0.40), wingtipL=(0.175, 0.12, 0.14),
    tail=(0.0, 0.09, 0.11), tailtip=(0.0, 0.205, 0.025),
)

TH_BODY = [0, 22, 45, 75, 100, 125, 152, 180]
TH_HEAD = [0, 12, 38, 62, 88, 115, 148, 180]
TH_MID = [(a + b) / 2 for a, b in zip(TH_BODY, TH_HEAD)]


def half(z, yf, yb, yc, rx, th, p=0.85):
    """A half section from the front seam (theta 0) to the back seam (180):
    ellipse-ish with a boxier exponent p, separate front and back depths."""
    pts = []
    for t in th:
        r = math.radians(t)
        s, c = math.sin(r), math.cos(r)
        x = 0.0 if t in (0, 180) else rx * abs(s) ** p
        d = (yc - yf) if c > 0 else (yb - yc)
        y = yc - math.copysign(abs(c) ** p, c) * d
        pts.append((x, y, z))
    return pts


def face_of(vs):
    s = set(vs)
    for f in vs[0].link_faces:
        if s <= set(f.verts):
            return f
    raise RuntimeError('no face on those verts')


def rect(vs, x0, x1, y0, y1, z):
    xs = sorted(vs, key=lambda v: v.co.x)
    for v in xs[:2]: v.co.x = x0
    for v in xs[2:]: v.co.x = x1
    ys = sorted(vs, key=lambda v: v.co.y)
    for v in ys[:2]: v.co.y = y0
    for v in ys[2:]: v.co.y = y1
    for v in vs: v.co.z = z


# (z, y front, y back, y centre, half width, thetas)
SECTIONS = [
    (0.082, -0.035, 0.070, 0.010, 0.055, TH_BODY),   # I0 inner bottom
    (0.095, -0.075, 0.100, 0.010, 0.110, TH_BODY),   # R0 belly bottom / tail root
    (0.150, -0.140, 0.145, 0.000, 0.152, [0, 28, 58, 108, 125, 140, 158, 180]),   # R1 lower belly
    (0.250, -0.188, 0.130, -0.010, 0.170, [0, 24, 50, 92, 112, 132, 155, 180]),  # R2 belly
    (0.340, -0.195, 0.115, -0.020, 0.170, [0, 22, 45, 78, 102, 127, 152, 180]),  # R3 chest
    (0.410, -0.185, 0.090, -0.030, 0.160, [0, 22, 45, 68, 95, 122, 152, 180]),   # R4 shoulder
    (0.450, -0.190, 0.082, -0.040, 0.148, TH_MID),   # R5 neck / lower face
    (0.490, -0.198, 0.078, -0.045, 0.150, TH_HEAD),  # R6 cheek
    (0.545, -0.190, 0.062, -0.050, 0.138, TH_HEAD),  # R7 brow
    (0.590, -0.150, 0.032, -0.055, 0.110, TH_HEAD),  # R8 crown
    (0.615, -0.090, 0.000, -0.050, 0.060, TH_HEAD),  # R9 top
]


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, half(*s)) for s in SECTIONS]
    I0, R0, R1 = rows[0], rows[1], rows[2]
    # tail: the back of the lowest belly ring runs out and down into a fan wedge
    R0[7].co = Vector((0.0, 0.205, 0.022)); R0[6].co = Vector((0.062, 0.185, 0.032))
    R0[5].co = Vector((0.100, 0.100, 0.080))
    I0[7].co = Vector((0.0, 0.080, 0.078)); I0[6].co = Vector((0.030, 0.072, 0.080))
    R1[7].co = Vector((0.0, 0.160, 0.140)); R1[6].co = Vector((0.085, 0.150, 0.145))
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, list(reversed(I0)))
    cap(bm, rows[-1])
    recalc_normals(bm)

    # wings: the back-side panel from the lower belly to the shoulder steps out as a folded wing
    wf = [face_of([rows[r][c], rows[r][c + 1], rows[r + 1][c], rows[r + 1][c + 1]])
          for r in (2, 3, 4) for c in (3, 4, 5)]
    w = extrude(bm, wf, offset=(0.022, 0.006, -0.004))
    # the leading edge runs diagonally (per-ring thetas); the folded wing thickens and drops toward its tips
    WING_ROW = {0.150: (0.012, 0.015, -0.035), 0.250: (0.004, 0.005, 0.0), 0.340: (0.0, 0.0, 0.0), 0.410: (-0.012, 0.0, 0.0)}
    for v in w['verts']:
        zr = min(WING_ROW, key=lambda z: abs(z - (v.co.z + 0.004)))
        v.co += Vector(WING_ROW[zr])

    # legs: the bottom band quad under the hip drops as a feathered leg, then the foot
    f = face_of([I0[3], I0[4], R0[3], R0[4]])
    r = extrude(bm, [f])
    rect(r['verts'], 0.054, 0.114, -0.032, 0.040, 0.064)
    r = extrude(bm, [r['faces'][0]])
    rect(r['verts'], 0.064, 0.104, -0.016, 0.024, 0.030)
    r = extrude(bm, [r['faces'][0]])
    rect(r['verts'], 0.050, 0.128, -0.058, 0.036, 0.0)
    # toes: the front face of the foot pushes forward
    recalc_normals(bm)
    ff = max((g for g in bm.faces if g.calc_center_median().z < 0.035 and g.calc_center_median().x > 0.04),
             key=lambda g: -g.normal.y)
    r = extrude(bm, [ff], offset=(0.0, -0.035, 0.0))
    scale(r['verts'], (0.85, 1.0, 0.55), pivot=centre(r['verts']))
    for v in r['verts']:
        v.co.z = max(0.0, v.co.z - 0.004)

    # ear tufts: the crown band quad above the eye rises into a tuft
    f = face_of([rows[9][3], rows[9][4], rows[10][3], rows[10][4]])
    r = extrude(bm, [f], offset=(0.028, -0.004, 0.022))
    scale(r['verts'], 0.55)
    r = extrude(bm, [r['faces'][0]], offset=(0.016, 0.004, 0.018))
    scale(r['verts'], 0.35)
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


WING_OFF = (0.022, 0.006, -0.004)
WING_ROW = {0.150: (0.012, 0.015, -0.035), 0.250: (0.004, 0.005, 0.0), 0.340: (0.0, 0.0, 0.0), 0.410: (-0.012, 0.0, 0.0)}


def wing_verts(bm):
    """The extruded wing verts, found by their stage-1 positions: {(ring, column): vert}."""
    out = {}
    for ri in (2, 3, 4, 5):
        pts = half(*SECTIONS[ri])
        if ri == 2:
            pts[6] = (0.085, 0.150, 0.145)
        for c in (3, 4, 5, 6):
            p = Vector(pts[c]) + Vector(WING_OFF) + Vector(WING_ROW[SECTIONS[ri][0]])
            v = min(bm.verts, key=lambda q: (q.co - p).length)
            assert (v.co - p).length < 1e-4, ('wing vert not found', ri, c)
            out[(ri, c)] = v
    return out


def face_plane_y(z):
    # the facial disc: one flat plane, leaning back 0.3 m per m toward the crown (reference side view)
    return -0.192 + (z - 0.47) * 0.30


def stage2(k, body):
    bm = edit(body)
    # facial disc: the front verts of the head rings (theta 0-38) go onto one plane; the theta-62
    # column stays behind it, so the disc rim is a crease
    disc = verts_where(bm, lambda c: 0.47 < c.z < 0.60 and c.y < -0.12 and c.x < 0.105)
    for v in disc:
        v.co.y = face_plane_y(v.co.z)
    # a soft ridge down the middle of the disc, from the brow to the beak root
    for v in disc:
        if v.co.x < 1e-5 and 0.48 < v.co.z < 0.56:
            v.co.y -= 0.010
    # folded wing: the leading edge was a 1-2 cm step (needle triangles); it stands proud as a real edge
    W = wing_verts(bm)
    for (ri, c), v in W.items():
        if c == 3:
            v.co += Vector((0.014, 0.0, 0.0))
        elif ri == 5:
            v.co += Vector((0.008, 0.0, 0.0))
    with k.topo(bm, 'inset', 'eye socket: a loop in the disc quad between the theta-12/38 columns and the cheek/brow rings'):
        f = face_near(bm, (0.058, face_plane_y(0.517), 0.517), n=(0, -1, 0))
        inset(bm, [f], 0.28, depth=-0.006)
    commit(body, bm)


PAL = {'brown': '#7a5a3c', 'dark': '#4a3424', 'cream': '#efe3c6', 'eye': '#f08a1c',
       'pupil': '#111111', 'beak': '#d8b870'}
FACE_N = Vector((0.0, -1.0, 0.30)).normalized()      # the facial disc's outward normal
EYE = Vector((0.058, face_plane_y(0.517), 0.517))


def body_rule(c, n, i):
    x = abs(c.x)
    if 0.465 < c.z < 0.60 and n.y < -0.75 and x < 0.10:
        return 'cream'                                   # facial disc
    if 0.445 < c.z < 0.61 and n.y < -0.25 and x < 0.14:
        return 'dark'                                    # the disc rim
    if 0.11 < c.z < 0.41 and n.y < -0.45 and x < 0.115:
        return 'cream'                                   # belly
    if c.z < 0.028 and c.z < 0.06:
        return 'beak'                                    # bare foot pad
    if (x > 0.15 and c.z < 0.19 and c.y > -0.02) or (c.y > 0.15 and c.z < 0.075):
        return 'dark'                                    # wing and tail tips
    return 'brown'


def prism(bm, poly, depth_vec):
    """A closed prism: a polygon (list of xyz) and the same polygon moved by depth_vec."""
    a = ring(bm, poly)
    b = ring(bm, [Vector(p) + Vector(depth_vec) for p in poly])
    bridge(bm, a, b, closed=True)
    cap(bm, a); cap(bm, list(reversed(b)))
    return a, b


def disc_poly(c, r, n, sides=8, rot=22.5):
    """A polygon of radius r around c, in the plane with normal n."""
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1))).normalized()
    w = u.cross(n).normalized()
    return [c + (u * math.cos(math.radians(rot + 360 * i / sides)) + w * math.sin(math.radians(rot + 360 * i / sides))) * r
            for i in range(sides)]


def blade(bm, base, tip, w, t, up=(0, 0, 1)):
    """A tapered four-sided blade from a base centre to a tip point: w wide, t thick at the base."""
    base, tip = Vector(base), Vector(tip)
    d = (tip - base).normalized()
    s = d.cross(Vector(up)).normalized()
    q = s.cross(d).normalized()
    b = ring(bm, [base + s * w / 2 + q * t / 2, base - s * w / 2 + q * t / 2, base - s * w / 2 - q * t / 2, base + s * w / 2 - q * t / 2])
    a = bm.verts.new(tip)                      # one apex: no needle quads at the tip
    for i in range(4):
        bm.faces.new([b[i], b[(i + 1) % 4], a])
    cap(bm, list(reversed(b)))


def piece(name, bm, colour):
    ob = object_from_bm(name, bm, mirror=True)
    paint(ob, PAL, colour if callable(colour) else (lambda c, n, i: colour))
    return ob


def stage3(k, body):
    paint(body, PAL, body_rule)
    out = []
    # eyes: octagonal orange lenses standing 6 mm proud of the disc, their backs sunk in the socket
    bm = bmesh.new(); prism(bm, disc_poly(EYE + FACE_N * 0.006, 0.024, FACE_N), -FACE_N * 0.016)
    out.append(piece('eye', bm, 'eye'))
    bm = bmesh.new(); prism(bm, disc_poly(EYE + FACE_N * 0.009, 0.0115, FACE_N), -FACE_N * 0.006)
    out.append(piece('pupil', bm, 'pupil'))
    # beak: a hooked wedge on the seam, its root sunk into the disc
    bm = bmesh.new()
    A, B, C, D, E, F = ring(bm, [(0, -0.176, 0.508), (0, -0.214, 0.486), (0, -0.224, 0.448),
                                 (0, -0.186, 0.456), (0.019, -0.178, 0.480), (0.009, -0.207, 0.470)])
    bm.faces.new([A, B, F, E]); bm.faces.new([B, C, F]); bm.faces.new([C, D, E, F]); bm.faces.new([A, E, D])
    out.append(piece('beak', bm, 'beak'))
    # V brows: dark blades from the ridge up and out over each eye, lying on the disc
    bm = bmesh.new()
    b0 = Vector((0.010, face_plane_y(0.540) - 0.004, 0.540)); b1 = Vector((0.104, face_plane_y(0.585) - 0.002, 0.585))
    blade(bm, b0, b1, 0.022, 0.017, up=FACE_N)
    out.append(piece('brow', bm, 'dark'))
    # ear tufts: dark blades rising out of the crown bumps
    bm = bmesh.new()
    blade(bm, (0.100, -0.075, 0.605), (0.150, -0.060, 0.690), 0.040, 0.016, up=(0, -1, 0))
    out.append(piece('tuft', bm, 'dark'))
    # toes: three forward and one back per foot, tan with dark talon tips
    bm = bmesh.new()
    for dx, tip in ((-0.026, (0.052, -0.125, 0.003)), (0.0, (0.090, -0.132, 0.003)), (0.026, (0.128, -0.122, 0.003)),
                    (0.0, (0.090, 0.075, 0.003))):
        base = (0.089 + dx * 0.6, -0.062 if tip[1] < 0 else 0.018, 0.017)
        blade(bm, base, tip, 0.017, 0.016)
    out.append(piece('toes', bm, lambda c, n, i: 'pupil' if (c.y < -0.112 or c.y > 0.062) else 'beak'))
    return out


def key_scale(rig, act, bone, keys):
    """Scale keys on one bone of an existing clip (the kit's clip() keys rotation/location only)."""
    ad = rig.animation_data
    ad.action = act
    pb = rig.pose.bones[bone]
    for f, sc in sorted(keys.items()):
        pb.scale = sc
        pb.keyframe_insert('scale', frame=f)
    ad.action = None
    rest(rig)


def stage4(k, body, pieces):
    e0 = EYE + FACE_N * 0.004
    rig = armature([
        ('hips', J['hips'], J['chest'], None),
        ('chest', J['chest'], J['neck'], 'hips', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['crown'], 'neck', True),
        ('eye.L', tuple(e0 + FACE_N * 0.02), tuple(e0 + FACE_N * 0.045), 'head'),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
        ('wing.L', J['shoulderL'], J['wingtipL'], 'chest'),
        ('tail', J['tail'], J['tailtip'], 'hips'),
    ], roll='auto')
    rig.data.bones['eye.L'].use_deform = True
    skin(body, rig)
    # the skull is rigid: every body vertex from the cheek ring up is 100% head, so the face
    # pieces (bound with these weights) and the eye lenses (on eye bones under head) stay seated
    hg = body.vertex_groups['head']
    for v in body.data.vertices:
        if (body.matrix_world @ v.co).z >= 0.44:
            for g in body.vertex_groups:
                g.remove([v.index])
            hg.add([v.index], 1.0, 'REPLACE')
    for p in pieces:
        if p.name in ('piece_eye', 'piece_pupil'):
            continue
        bind(p, rig, body=body)
    # the eye lens and pupil ride the eye bones (mirrored pieces: split by side)
    for p in pieces:
        if p.name in ('piece_eye', 'piece_pupil'):
            bind(p, rig, bone='head')
            p.vertex_groups.clear()
            gl, gr = p.vertex_groups.new(name='eye.L'), p.vertex_groups.new(name='eye.R')
            for v in p.data.vertices:
                (gl if (p.matrix_world @ v.co).x > 0 else gr).add([v.index], 1.0, 'REPLACE')
    # the skin under each eye follows the eye bone's parent (head) only: remove eye weights from the body
    for nm in ('eye.L', 'eye.R'):
        g = body.vertex_groups.get(nm)
        if g:
            body.vertex_groups.remove(g)
    from bmkit import _fill_unweighted
    _fill_unweighted(body, rig)

    W = ('wing.L', 'wing.R')
    idle = clip(rig, 'idle', {1: {}, 10: {'head': (0, 32, 0)}, 18: {'head': (0, 32, 0), 'chest': (2, 0, 0)},
                              28: {'head': (4, -26, 0)}, 36: {'head': (4, -26, 0)}, 48: {}})
    key_scale(rig, idle, 'eye.L', {1: (1, 1, 1), 40: (1, 1, 1), 42: (1, 1, 0.12), 44: (1, 1, 1), 48: (1, 1, 1)})
    key_scale(rig, idle, 'eye.R', {1: (1, 1, 1), 40: (1, 1, 1), 42: (1, 1, 0.12), 44: (1, 1, 1), 48: (1, 1, 1)})
    clip(rig, 'move', {1: {},
                       5: {'thigh.L': (18, 0, 0), 'thigh.R': (18, 0, 0), 'chest': (8, 0, 0)},
                       10: {W[0]: (0, 0, 28), W[1]: (0, 0, -28), 'thigh.L': (-8, 0, 0), 'thigh.R': (-8, 0, 0), 'tail': (-10, 0, 0)},
                       14: {W[0]: (0, 0, 6), W[1]: (0, 0, -6)},
                       18: {'thigh.L': (12, 0, 0), 'thigh.R': (12, 0, 0), 'chest': (5, 0, 0)},
                       24: {}},
         loc={1: {}, 5: {'hips': (0, -0.012, 0)}, 10: {'hips': (0, 0.05, 0)}, 14: {'hips': (0, 0.04, 0)},
              18: {'hips': (0, -0.008, 0)}, 24: {}})
    clip(rig, 'attack', {1: {},
                         8: {W[0]: (0, 0, 32), W[1]: (0, 0, -32), 'chest': (-8, 0, 0), 'head': (10, 0, 0), 'tail': (-12, 0, 0)},
                         14: {W[0]: (0, 0, 36), W[1]: (0, 0, -36), 'chest': (6, 0, 0), 'head': (8, 0, 0),
                              'thigh.L': (-35, 0, 0), 'thigh.R': (-35, 0, 0), 'foot.L': (20, 0, 0), 'foot.R': (20, 0, 0)},
                         20: {W[0]: (0, 0, 30), W[1]: (0, 0, -30), 'thigh.L': (-30, 0, 0), 'thigh.R': (-30, 0, 0)},
                         32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
