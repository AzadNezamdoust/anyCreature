import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# crab (t7x zoo): the spine loft of 6-vertex half rings runs from the shell's rear edge to its front edge and IS the
# carapace (wide, flat, a sharp rim at ring vertex 2); the four walking legs per side grow from 2-face regions under
# the rim (one span each, neighbouring roots share an edge), the claw from its own span at the front corner (one
# empty span between it and the first leg), the eye stalks as 1-face extrusions of the front-edge top face.
# Every limb is a hexagon tube swept along a path with a parallel-transported frame. The movable claw finger is a
# stage-3 piece on its own bone (the snap). Rig: idle, sideways walk, claw-snap attack.
META = dict(creature='crab', model='opus', stage1_tris=(1000, 4500), total_tris=(2500, 6000),
            closeups=[('claw', (0.2, -0.2, 0.22), 0.13, 'hero'),
                      ('eyes and front', (0.0, -0.1, 0.17), 0.12, 'hero'),
                      ('legs side', (0.2, 0.06, 0.09), 0.2, 'az090'),
                      ('underside', (0.08, -0.02, 0.07), 0.2, 'hero_low')])

ZC = 0.115   # fix pass: was 0.14 (carapace lowered)
# shell half ring, top seam -> bottom seam: dome shoulder, sharp rim (vertex 2), under-rim, belly side
SHELL = [(0, 1), (0.68, 0.82), (1, 0.0), (0.84, -0.42), (0.5, -0.88), (0, -1)]
# density pass 3: 10-vertex half rings, a rounded dome (two shoulder vertices) down to the sharp rim (vertex 4), then a
# 3-face under-rim root band (vertices 4-7) and the belly
SHELL = [(0, 1), (0.38, 0.95), (0.67, 0.8), (0.88, 0.52), (1, 0.0), (0.92, -0.24), (0.8, -0.46), (0.6, -0.7),
         (0.32, -0.92), (0, -1)]
RIM, ROOT = 4, (4, 5, 6, 7)

# (name, y, T, B, W) rear -> front
_S = [('R0', 0.165, 0.03, 0.035, 0.05),
      ('R1', 0.14, 0.055, 0.055, 0.095),
      ('R2', 0.105, 0.068, 0.07, 0.125),
      ('R3', 0.065, 0.075, 0.075, 0.142),
      ('M0', 0.025, 0.078, 0.078, 0.15),
      ('F0', -0.015, 0.078, 0.078, 0.15),
      ('F1', -0.055, 0.07, 0.07, 0.14),
      ('F2', -0.088, 0.055, 0.055, 0.104),
      ('F3', -0.11, 0.035, 0.04, 0.088)]
# fix pass: a wide flat shield (width 1.5x depth, height -15%, body lower), straighter front edge (F2/F3 wider)
_S = [(n, y * 0.88, T * 0.85, B * 0.85, W * 1.2) for n, y, T, B, W in _S]
# density pass 3: new stations where the top outline curves: RT (the pointed rear of the sheet's shield), R0a (rear
# taper), F0a (front shoulder, the widest part of the sheet's shield sits ahead of the middle)
_S = ([('RT', 0.158, 0.012, 0.014, 0.026)] + _S[:1] + [('R0a', 0.135, 0.039, 0.043, 0.09)] + _S[1:6]
      + [('F0a', -0.031, 0.064, 0.065, 0.177)] + _S[6:])
# r14: the rear tapers to the sheet's shield point (top view): RT further back, R0/R0a/R1 narrower
_S = [(n, y, T, B, {'R0': 0.052, 'R0a': 0.08, 'R1': 0.106}.get(n, W)) if n != 'RT' else (n, 0.166, T, B, 0.02)
      for n, y, T, B, W in _S]
SECS = [(n, (y, ZC), 0.0, T, B, W, SHELL) for n, y, T, B, W in _S]

# legs: (rear ring of the root span, heading deg from +X toward +Y, length scale)
LEGS = [('M0', -24.0, 1.12), ('R3', 6.0, 1.15), ('R2', 32.0, 1.15), ('R1', 54.0, 1.1)]
# fix pass 2: legs a little shorter (less stilt splay)
LEGS = [(r, h, L * 0.94) for r, h, L in LEGS]
# density pass 3 r11: the rear leg 3 deg further back (its thicker merus touched leg 3 at the knee)
LEGS[3] = ('R1', 55.0, LEGS[3][2])
# leg path from the root: (distance out along the heading, z, rw, rh)
# fix pass: shorter (body lower), knee raised to the shell top, foot tip down, thicker lower segments
LEG_PTS = [(0.056, 0.098, 0.017, 0.015), (0.07, 0.14, 0.018, 0.016), (0.082, 0.165, 0.017, 0.016),
           (0.102, 0.135, 0.017, 0.016), (0.116, 0.09, 0.016, 0.015), (0.125, 0.046, 0.013, 0.013),
           (0.13, 0.006, 0.006, 0.006)]
# fix pass 2: knee lower (rim height, as the sheet side), legs taper to a point from the wrist down
LEG_PTS = [(0.056, 0.096, 0.017, 0.015), (0.07, 0.13, 0.018, 0.016), (0.084, 0.148, 0.017, 0.016),
           (0.104, 0.125, 0.016, 0.015), (0.117, 0.085, 0.013, 0.012), (0.126, 0.044, 0.009, 0.009),
           (0.131, 0.006, 0.004, 0.004)]
KNEE, WRIST = 2, 4
# density pass 3: 12 stations (was 7) re-fitted to the sheet's leg: a thick merus arching up to the knee, the carpus
# falling from it, the propodus to the wrist, then a tapered dactyl curving in to the tip (r11: knee stations 1.3 cm
# apart, closer ones folded the inner wall)
LEG_PTS = [(0.054, 0.092, 0.016, 0.015), (0.064, 0.12, 0.017, 0.016), (0.074, 0.14, 0.0175, 0.016),
           (0.09, 0.15, 0.017, 0.014), (0.108, 0.13, 0.017, 0.016), (0.113, 0.108, 0.016, 0.015),
           (0.119, 0.084, 0.014, 0.013), (0.124, 0.062, 0.012, 0.011), (0.126, 0.051, 0.0105, 0.010), (0.128, 0.04, 0.009, 0.009),
           (0.131, 0.02, 0.006, 0.006), (0.132, 0.006, 0.004, 0.004)]
KNEE, WRIST = 3, 6
# claw path (absolute): merus out and forward, carpus up, the big palm up and forward, the fixed finger inward
CLAW = [((0.165, -0.09, 0.092), 0.018, 0.016), ((0.198, -0.11, 0.102), 0.019, 0.017),
        ((0.212, -0.13, 0.118), 0.015, 0.014), ((0.218, -0.148, 0.14), 0.02, 0.018),
        ((0.22, -0.16, 0.16), 0.017, 0.016), ((0.22, -0.17, 0.177), 0.036, 0.033),
        ((0.22, -0.182, 0.204), 0.054, 0.048), ((0.214, -0.192, 0.234), 0.05, 0.045), ((0.202, -0.2, 0.258), 0.032, 0.028),
        ((0.182, -0.212, 0.272), 0.018, 0.015), ((0.16, -0.226, 0.276), 0.014, 0.012),
        ((0.141, -0.236, 0.268), 0.009, 0.008), ((0.128, -0.24, 0.254), 0.004, 0.004)]
PALM_FRONT = 8
# fix pass 2: the claw lower and further forward from the carpus on (palm out in front of the face, not a raised glove)
CLAW = [((x, y - 0.032 * min(1.0, max(0, i - 1) / 4), z - 0.035 * min(1.0, max(0, i - 1) / 4)), w, h)
        for i, ((x, y, z), w, h) in enumerate(CLAW)]
# density pass 3: 20 sections (was 13): two more along the merus, one at the merus-carpus bend, one in the carpus, one at the wrist flare and three more round
# the palm, so the palm reads as the sheet's round mitten (bulge 0.054 -> 0.056, smoother swell and front)
def _mid(a, b, w, h):
    return (tuple((p + q) / 2 for p, q in zip(a[0], b[0])), w, h)
_C = CLAW
CLAW = [_C[0], _mid(_C[0], _C[1], 0.0195, 0.0175), _C[1], _mid(_C[1], _C[2], 0.017, 0.016), _C[2], _C[3],
        _mid(_C[3], _C[4], 0.019, 0.017), _C[4], _mid(_C[4], _C[5], 0.025, 0.023),
        (_C[5][0], 0.038, 0.035), _mid(_C[5], _C[6], 0.048, 0.044), (_C[6][0], 0.055, 0.05),
        _mid(_C[6], _C[7], 0.056, 0.05), (_C[7][0], 0.05, 0.045), _mid(_C[7], _C[8], 0.043, 0.039),
        _C[8]] + _C[9:]
PALM_FRONT = 15
CARPUS_J, WRIST_J, PALM0 = 5, 8, 10         # joint-ring cuts (before section j), the rigid palm from section PALM0
B_CARPUS, B_PALM = 4, 7                     # bone heads: carpus, palm
PAINT_PALM = 9
# eye stalks: 1-face extrusion of span F2-F3's face 1 (ring vertices 1-2): (centre, rx, ry, dz)
EYE = [((0.088, -0.088, 0.175), 0.0085, 0.0085, 0.0), ((0.085, -0.091, 0.2), 0.0075, 0.0075, 0.0)]


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def nxt(nm):
    i = [s[0] for s in SECS].index(nm)
    return SECS[i + 1][0]


def root_centre(rear):
    pts = [P(rear)[j] for j in ROOT] + [P(nxt(rear))[j] for j in ROOT]
    return sum(pts, Vector()) / len(pts)


def frames(root, pts):
    """pts [(p, rw, rh)] -> [(p, U, S, rw, rh)]: S parallel-transported from world up (no twist along the limb)."""
    out, S = [], Vector((0, 0, 1))
    P_ = [root] + [Vector(p) for p, _w, _h in pts]
    for i, (p, rw, rh) in enumerate(pts):
        a_ = P_[i]
        b_ = P_[i + 2] if i + 2 < len(P_) else P_[i + 1] + (P_[i + 1] - P_[i])
        T = (b_ - a_).normalized()
        S = (S - T * S.dot(T)).normalized()
        U = S.cross(T).normalized()
        out.append((Vector(p), U, S, rw, rh))
    return out


def leg_secs(spec):
    rear, hd, L = spec
    rc = root_centre(rear)
    a = math.radians(hd)
    h = Vector((math.cos(a), math.sin(a), 0.0))
    pts = [(rc + h * d * L + Vector((0, 0, z - rc.z)), rw, rh) for d, z, rw, rh in LEG_PTS]
    return frames(rc, pts)


def claw_secs():
    return frames(root_centre('F1'), [(Vector(p), rw, rh) for p, rw, rh in CLAW])


def sec_pos(sec, a, b):
    p, U, S, rw, rh = sec
    return p + S * (a * rh) + U * (b * rw * (0.45 if abs(a) == 1 else 1.0))   # density pass 3: octagon (was hexagon)


OCT = (1, 0.41, -0.41, -1)


def grow_tube(bm, faces, roles, secs):
    """Extrude the root region section by section; each new vertex keeps the role (a: 1 upper, 0 side, -1 lower;
    b: side across) of the vertex it was extruded from: a hexagon tube."""
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (a, b) in new.items():
            v.co = sec_pos(sec, a, b)
        faces, roles = r['faces'], new
    return faces


def role_pos(sec, u, s):
    c, rx, ry, dz = sec
    return (c[0] + u * rx, c[1] + s * ry, c[2] - u * dz)


def stage1(k):
    bm = bmesh.new()
    idx = {s[0]: i for i, s in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(rear, secs):
        i = idx[rear]
        rr, rf = rings[i], rings[i + 1]
        U0 = secs[0][1]
        sg = 1 if (sum((rr[j].co for j in ROOT), Vector()) - sum((rf[j].co for j in ROOT), Vector())).dot(U0) > 0 else -1
        roles = {}
        for j, a in zip(ROOT, OCT):
            roles[rr[j]] = (a, sg); roles[rf[j]] = (a, -sg)
        grow_tube(bm, [spans[i][j] for j in ROOT[:-1]], roles, secs)

    for spec in LEGS:
        limb(spec[0], leg_secs(spec))
    limb('F1', claw_secs())
    # eye stalks: one face, grown upward
    i = idx['F2']
    rr, rf = rings[i], rings[i + 1]
    faces = [spans[i][2]]
    roles = {rf[2]: (-1, -1), rf[3]: (1, -1), rr[2]: (-1, 1), rr[3]: (1, 1)}
    for sec in EYE:
        r = extrude(bm, faces)
        new = {v: roles[min(roles, key=lambda o: (o.co - v.co).length)] for v in r['verts']}
        for v, (u, s) in new.items():
            v.co = Vector(role_pos(sec, u, s))
        faces, roles = r['faces'], new
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    # joint rings: a pinched loop at every leg's knee and wrist, and at the claw's carpus and wrist
    cuts = []
    for n_, spec in enumerate(LEGS, 1):
        s = leg_secs(spec)
        for j, nm in ((KNEE, 'knee'), (WRIST, 'wrist')):
            cuts.append((s[j - 1], s[j], f'leg {n_} {nm}: a joint ring, the segment bend'))
    c = claw_secs()
    for j, nm in ((CARPUS_J, 'carpus'), (WRIST_J, 'wrist')):
        cuts.append((c[j - 1], c[j], f'claw {nm}: a joint ring, the claw bend'))
    for s0, s1, why in cuts:
        e = edge_near(bm, (sec_pos(s0, 1, 1) + sec_pos(s1, 1, 1)) / 2)
        with k.topo(bm, 'loop', why):
            nv = loopcut(bm, e, t=0.5)
        scale(nv, 0.86, pivot=centre(nv))
    # s2 r2: blunt the needle tips (leg dactyls and the fixed finger): the tip ring x1.9 about its centre
    tips = [leg_secs(spec)[-1] for spec in LEGS] + [claw_secs()[-1]]
    for t in tips:
        vs = [vert_near(bm, sec_pos(t, a, b)) for a in OCT for b in (1, -1)]
        scale(vs, 1.9, pivot=t[0])
        for v in vs:
            v.co.z = max(v.co.z, 0.0)
    # s4 r3: the movable finger (dactyl) grown from the palm's upper front face (sections 8-9, role a = 1), a quad
    # tube running 3 cm above the fixed finger, so the snap is a skin bend on its own bone (a rigid piece on a hinge
    # opens a gap to the palm skin in every pose: the drift gate)
    c = claw_secs()
    face = face_near(bm, sum((sec_pos(c[j], 1, b) for j in (PALM_FRONT, PALM_FRONT + 1) for b in (1, -1)), Vector()) / 4,
                     n=tuple(c[PALM_FRONT][2]))
    roles = {}
    for v in face.verts:
        j = min((PALM_FRONT, PALM_FRONT + 1), key=lambda j_: min((v.co - sec_pos(c[j_], 1, b)).length for b in (1, -1)))
        b = 1 if (v.co - c[j][0]).dot(c[j][1]) > 0 else -1
        roles[v] = (b, -1 if j == PALM_FRONT else 1)
    with k.topo(bm, 'extrude', 'claw dactyl: the movable finger, a quad tube grown from the palm front top face'):
        faces = [face]
        for p_, U, W, ru, rw in dactyl_path():
            r = extrude(bm, faces)
            new = {v: roles[min(roles, key=lambda o: (o.co - v.co).length)] for v in r['verts']}
            for v, (b, kk) in new.items():
                v.co = p_ + U * (b * ru) + W * (kk * rw)
            faces, roles = r['faces'], new
    # the front edge between the eye stalks a flat plate (the mouth plate)
    flatten([vert_near(bm, q) for q in P('F3')])
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'shell': '#d4512a', 'leg': '#e0662e', 'cream': '#ecd3a6', 'finger': '#f1e3c4', 'eye': '#3b2216',
       'pupil': '#140c08'}


def shell_w(y):
    ys = [s[1] for s in _S]
    if y >= ys[0] or y <= ys[-1]:
        return 0.0
    for (n0, y0, *_a, w0), (n1, y1, *_b, w1) in zip(_S, _S[1:]):
        if y1 <= y <= y0:
            return w0 + (w1 - w0) * (y0 - y) / (y0 - y1)


def body_rule(c, n, i):
    # fix pass: regions by the nearest claw section (palm red, both fingers cream) instead of fixed heights
    x, y, z = abs(c.x), c.y, c.z
    q = Vector((x, y, z))
    cs = claw_secs()
    j = min(range(len(cs)), key=lambda i_: (q - cs[i_][0]).length)
    near = (q - cs[j][0]).length < max(cs[j][3], cs[j][4]) * 1.6 + 0.006
    if any((q - p_).length < max(ru, rw) * 1.6 + 0.004 for p_, _u, _w, ru, rw in dactyl_path()[1:]):
        return 'finger'                                # movable finger, cream
    if near and j >= PALM_FRONT + 1:
        return 'finger'                                # fixed claw finger, cream
    if z > ZC + 0.03 and y < -0.07 and x < 0.11:
        return 'leg'                                   # eye stalks
    if x <= shell_w(y) * 1.01 + 1e-3 and 0.04 < z:
        return 'shell' if (z > ZC - 0.004 and n.z > -0.05) else 'cream'   # carapace / underside (border on the rim)
    if near and PAINT_PALM <= j <= PALM_FRONT:
        return 'shell'                                 # claw palm, shell red
    if n.z < -0.55:
        return 'cream'                                 # limb undersides
    return 'leg'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A small low-poly eye: back cone, iris ring, pupil fan."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 3 for k_ in range(6)]]
    R, I = ring_(r, 0.0), ring_(r * 0.6, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.1)
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def dactyl_pts(side=1):
    """The movable finger: from a hinge on the palm's upper front, along the fixed finger 3 cm above it (along S)."""
    cs = claw_secs()
    out = []
    for j, g, r in ((PALM_FRONT, 0.012, 0.02), (PALM_FRONT + 1, 0.03, 0.015), (PALM_FRONT + 2, 0.036, 0.012),
                    (PALM_FRONT + 3, 0.04, 0.008), (PALM_FRONT + 4, 0.042, 0.003)):
        p, U, S, _w, _h = cs[j]
        q = p + S * g + (cs[j][0] - cs[PALM_FRONT][0]) * 0.12
        out.append((Vector((q.x * side, q.y, q.z)), U, S, r))
    return out


def dactyl_path():
    """The dactyl's sections: (centre, U side, W across, ru, rw); W = U x tangent, so the root face's section-8 -> 9
    direction (along the claw) turns into -S as the finger bends forward."""
    c = claw_secs()
    fc = sum((sec_pos(c[j], 1, b) for j in (PALM_FRONT, PALM_FRONT + 1) for b in (1, -1)), Vector()) / 4
    S8 = c[PALM_FRONT][2]
    pts = [(fc + S8 * 0.014, 0.012, 0.01),
           (c[PALM_FRONT + 2][0] + c[PALM_FRONT + 2][2] * 0.03, 0.01, 0.009),
           (c[PALM_FRONT + 3][0] + c[PALM_FRONT + 3][2] * 0.032, 0.008, 0.007),
           (c[PALM_FRONT + 4][0] + c[PALM_FRONT + 4][2] * 0.03 + (c[-1][0] - c[-2][0]) * 0.5, 0.004, 0.004)]
    out, prev = [], fc
    for i, (p_, ru, rw) in enumerate(pts):
        nx = pts[i + 1][0] if i + 1 < len(pts) else p_ + (p_ - prev)
        Td = (nx - prev).normalized()
        U = c[min(PALM_FRONT + 1 + i, len(c) - 1)][1]
        U = (U - Td * U.dot(Td)).normalized()
        out.append((p_, U, U.cross(Td).normalized(), ru, rw))
        prev = p_
    return out


def dactyl(side):
    bm = bmesh.new()
    rows = []
    for p, U, S, r in dactyl_pts(side):
        U = Vector((U.x * side, U.y, U.z)); S = Vector((S.x * side, S.y, S.z))
        rows.append([bm.verts.new(p + (U * math.cos(t) + S * math.sin(t)) * r) for t in [k_ * math.pi / 3 for k_ in range(6)]])
    bm.faces.new(list(reversed(rows[0])) if side > 0 else rows[0])
    for a, b in zip(rows, rows[1:]):
        for j in range(6):
            f = [a[j], a[(j + 1) % 6], b[(j + 1) % 6], b[j]]
            bm.faces.new(f if side > 0 else list(reversed(f)))
    bm.faces.new(rows[-1] if side > 0 else list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = object_from_bm('dactyl_' + ('L' if side > 0 else 'R'), bm, mirror=False)
    paint(ob, {'finger': PAL['finger']}, lambda c_, n_, i: 'finger')
    return ob


def stage3(k, body):
    paint(body, PAL, body_rule)
    bm = bmesh.new()
    top = Vector(EYE[-1][0])
    c = top + Vector((0, -0.002, 0.006))
    n = Vector((0.15, -0.55, 1.0)).normalized()
    lens(bm, c, n, 0.0135, 0.011)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.006 and n_.dot(n) > 0.5 else 'eye')
    return [eye]


def stage4(k, body, pieces):
    B = [('body', (0.0, 0.07, ZC), (0.0, -0.07, ZC), None)]
    for n_, spec in enumerate(LEGS, 1):
        s = leg_secs(spec)
        rc = root_centre(spec[0])
        pts = [rc, s[KNEE][0], s[WRIST][0], s[-1][0]]
        for t_, (p, q) in zip('abc', zip(pts, pts[1:])):
            par = 'body' if t_ == 'a' else 'leg%d%s.L' % (n_, 'ab'['bc'.index(t_)])
            B.append(('leg%d%s.L' % (n_, t_), tuple(p), tuple(q), par, t_ != 'a'))
    c = claw_secs()
    pts = [root_centre('F1'), c[B_CARPUS][0], c[B_PALM][0], c[PALM_FRONT][0], c[-1][0]]
    for nm, (p, q), par in zip(('arm', 'carpus', 'palm', 'finger'), zip(pts, pts[1:]), ('body', 'arm.L', 'carpus.L', 'palm.L')):
        B.append((nm + '.L', tuple(p), tuple(q), par, par != 'body'))
    d = dactyl_path()
    B.append(('dactyl.L', tuple(d[0][0]), tuple(d[-1][0]), 'palm.L'))
    B.append(('eye.L', (0.087, -0.088, 0.165), tuple(EYE[-1][0]), 'body'))
    rig = armature(B, roll='auto')
    # the dactyl's local Z = the claw's side axis U: +Z closes it toward the fixed finger on both sides
    Ud = d[1][1]
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        rig.data.edit_bones['dactyl.L'].align_roll(Ud)
        rig.data.edit_bones['dactyl.R'].align_roll(Vector((Ud.x, -Ud.y, -Ud.z)))
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    # s4 r2: the palm and fixed finger are one rigid shell on palm (heat spread carpus/arm into it, and the
    # rigid movable finger drifted off the palm in the attack)
    cs = claw_secs()
    vg = {sd: body.vertex_groups[f'palm.{sd}'] for sd in 'LR'}
    for v in body.data.vertices:
        p = body.matrix_world @ v.co
        q = Vector((abs(p.x), p.y, p.z))
        j = min(range(len(cs)), key=lambda i: (q - cs[i][0]).length)
        if j >= PALM0 and (q - cs[j][0]).length < max(cs[j][3], cs[j][4]) * 1.4 + 0.004:
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            vg['L' if p.x > 0 else 'R'].add([v.index], 1.0, 'REPLACE')
    # the dactyl tube (stage 2) rigid on its bone, its root ring on the palm
    dp = dactyl_path()
    fc = sum((sec_pos(cs[j], 1, b) for j in (PALM_FRONT, PALM_FRONT + 1) for b in (1, -1)), Vector()) / 4
    S8 = cs[PALM_FRONT][2]
    vd = {sd: body.vertex_groups.get(f'dactyl.{sd}') or body.vertex_groups.new(name=f'dactyl.{sd}') for sd in 'LR'}
    for v in body.data.vertices:
        p = body.matrix_world @ v.co
        q = Vector((abs(p.x), p.y, p.z))
        if (q - fc).dot(S8) > 0.007 and any((q - c_).length < max(ru, rw) * 1.35 + 0.002 for c_, _u, _w, ru, rw in dp):
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            vd['L' if p.x > 0 else 'R'].add([v.index], 1.0, 'REPLACE')
    bind(pieces[0], rig, body=body)
    # local Z of a sideways bone points forward (-Y): +Z lifts a .L leg, -Z lifts a .R leg
    def lift(sd, a):
        return a if sd == 'L' else -a
    # idle: the body breathes, the claws bob, the eye stalks twitch, a leg taps
    clip(rig, 'idle', {1: {}, 12: {'arm.L': (0, 0, 4), 'arm.R': (0, 0, -4), 'leg1a.L': (0, 0, 3)},
                       20: {'eye.L': (8, 0, 0), 'eye.R': (8, 0, 0)}, 24: {'arm.L': (0, 0, 0), 'leg1a.L': (0, 0, 0)},
                       36: {'arm.L': (0, 0, 4), 'arm.R': (0, 0, -4), 'leg3a.R': (0, 0, -3)}, 48: {}},
         loc={1: {'body': (0, 0, 0)}, 24: {'body': (0, 0, 0.004)}, 48: {'body': (0, 0, 0)}})
    # move: sideways walk (+X), alternating tetrapods A = L1 L3 R2 R4, B = L2 L4 R1 R3; the lifted leg folds its tip
    A_ = [('1', 'L'), ('3', 'L'), ('2', 'R'), ('4', 'R')]
    B_ = [('2', 'L'), ('4', 'L'), ('1', 'R'), ('3', 'R')]

    def up(group, amt):
        d = {}
        for n_, sd in group:
            d[f'leg{n_}a.{sd}'] = (0, 0, lift(sd, amt))
            d[f'leg{n_}b.{sd}'] = (0, 0, lift(sd, -amt * 0.8))
        return d
    clip(rig, 'move', {1: up(A_, 18), 7: {}, 13: up(B_, 18), 19: {}, 25: up(A_, 18)},
         loc={1: {'body': (0, 0, 0)}, 7: {'body': (0, 0.0, 0.006)}, 13: {'body': (0, 0, 0)}, 19: {'body': (0, 0, 0.006)},
              25: {'body': (0, 0, 0)}})
    # attack: both claws rise and open, then strike forward and snap shut
    raise_ = {'arm.L': (0, 0, 22), 'arm.R': (0, 0, -22), 'carpus.L': (-15, 0, 0), 'carpus.R': (-15, 0, 0),
              'dactyl.L': (0, 0, -12), 'dactyl.R': (0, 0, -12)}
    strike = {'arm.L': (10, 0, 4), 'arm.R': (10, 0, -4), 'carpus.L': (4, 0, 0), 'carpus.R': (4, 0, 0),  # s4 r4: was 14/6 and carpus 18, the palm swung over the face
              'dactyl.L': (0, 0, 15), 'dactyl.R': (0, 0, 15)}
    clip(rig, 'attack', {1: {}, 10: raise_, 16: strike, 20: strike, 26: {'dactyl.L': (0, 0, 0)}, 32: {}},
         loc={1: {'body': (0, 0, 0)}, 10: {'body': (0, 0.01, 0.01)}, 16: {'body': (0, -0.015, 0)}, 32: {'body': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
