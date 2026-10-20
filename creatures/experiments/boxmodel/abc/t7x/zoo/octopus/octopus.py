import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# octopus (t7x zoo): no legs, so the spine loft of 6-vertex half rings (mantle tip -> mantle -> neck -> head ->
# arm crown -> mouth) is the egg mantle and the head; the eight arms are swept tubes, each grown from its own
# 2-face region of the crown (one column of the two crown spans), so every arm has a separate root and the
# only web is the side walls between neighbouring roots. Suckers are separate stage-3 pieces. Rig: idle, swim, attack.
META = dict(creature='octopus', model='opus', stage1_tris=(1500, 5200), total_tris=(3000, 8000),
            closeups=[('head and eye', (0.07, -0.08, 0.25), 0.16, 'hero'),
                      ('arm crown', (0.08, -0.06, 0.13), 0.22, 'hero'),
                      ('mantle', (0.0, 0.10, 0.36), 0.26, 'az090'),
                      ('arm underside', (0.17, -0.12, 0.06), 0.18, 'hero_low')])

# poly pass 3: 8-vertex half rings (were 6), 22 loft stations (were 13), the arms octagons over 22 sections (were
# hexagons over 10). The old control shapes stay as the design: each profile / radius list is run through a smooth
# curve and resampled, so the new vertices sit on the rounded form instead of on the old straight edges.
def _pchip(xs, ys, x):
    """Monotone cubic through (xs, ys) (xs ascending), evaluated at x (clamped)."""
    n = len(xs)
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 2 / (1 / d[i - 1] + 1 / d[i]) for i in range(1, n - 1)] + [d[-1]]
    i = max(k for k in range(n - 1) if xs[k] <= x)
    h = xs[i + 1] - xs[i]
    t = (x - xs[i]) / h
    return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[i] + (t ** 3 - 2 * t ** 2 + t) * h * m[i]
            + (-2 * t ** 3 + 3 * t ** 2) * ys[i + 1] + (t ** 3 - t ** 2) * h * m[i + 1])


def _cr(p0, p1, p2, p3, t):
    return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def resample(prof, n=8):
    """The half-ring polygon as a smooth Catmull-Rom curve (mirrored ghosts at the seams, so the curve meets the
    seam square), resampled at n points equally spaced along it."""
    P = [(-prof[1][0], prof[1][1])] + list(prof) + [(-prof[-2][0], prof[-2][1])]
    dense = []
    for i in range(1, len(P) - 2):
        for k in range(40):
            dense.append(_cr(P[i - 1], P[i], P[i + 1], P[i + 2], k / 40))
    dense.append(prof[-1])
    L = [0.0]
    for a, b in zip(dense, dense[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out = []
    for k in range(n):
        s = L[-1] * k / (n - 1)
        j = min(max(i for i in range(len(L)) if L[i] <= s + 1e-12), len(dense) - 2)
        f = (s - L[j]) / max(L[j + 1] - L[j], 1e-12)
        out.append((round(dense[j][0] + (dense[j + 1][0] - dense[j][0]) * f, 4),
                    round(dense[j][1] + (dense[j + 1][1] - dense[j][1]) * f, 4)))
    out[0], out[-1] = (0, out[0][1]), (0, out[-1][1])
    return out


# half-ring design profiles, seam A -> seam B: (x as a fraction of W, h as a fraction of T / B)
EGG6 = [(0, 1), (0.7, 0.85), (1, 0.25), (0.95, -0.35), (0.6, -0.85), (0, -1)]
HEAD6 = [(0, 1), (0.72, 0.8), (1, 0.2), (0.95, -0.4), (0.6, -0.85), (0, -1)]
EGG = resample(EGG6)
# eye pass: the head ring keeps the before3 side face exactly (old vertices 1-2 -> 2-3), so the eye turret is full size
HEAD = [(0, 1), (0.38, 0.95), (0.72, 0.8), (1, 0.2), (0.99, -0.12), (0.95, -0.4), (0.6, -0.85), (0, -1)]
# the crown: vertices by angle from the front; arm columns 0, 2, 4, 6 (centres 18, 61, 112, 159 deg), narrow web
# columns 1, 3, 5 between them, so neighbouring arms no longer share an edge
CROWN_ANG = (0, 36, 45, 77, 94, 130, 139, 180)
CROWN = [(round(0.97 * math.sin(math.radians(a)), 4), round(math.cos(math.radians(a)), 4)) for a in CROWN_ANG]

# the mantle: an egg along an axis from the neck (A) up and back to the tip; s = 0 at A, 1 at the tip
MA, MTIP = (-0.03, 0.285), (0.175, 0.483)   # fix pass 2: axis 44 deg (more upright egg), length -8%
_ML = math.hypot(MTIP[0] - MA[0], MTIP[1] - MA[1])
_MU = ((MTIP[0] - MA[0]) / _ML, (MTIP[1] - MA[1]) / _ML)
_MANG = math.degrees(math.atan2(-_MU[1], _MU[0]))          # dorsal d = (-u_z, u_y): up and a little forward
MANTLE6 = [(1.0, 0.024), (0.93, 0.06), (0.82, 0.095), (0.66, 0.117), (0.48, 0.121), (0.30, 0.112), (0.14, 0.086)]   # the design egg
# poly pass 3: 12 stations, close at the pinched tip and the shoulders of the egg; radius on the smooth curve
MANTLE_S = (1.0, 0.975, 0.94, 0.89, 0.82, 0.74, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15)
_MS = sorted(MANTLE6)
MANTLE = [(s_, round(_pchip([a for a, _ in _MS], [b for _, b in _MS], s_) * (1 + 0.06 * math.sin(math.pi * s_)), 4))
          for s_ in MANTLE_S]   # s1 r15: the egg rounder through its middle (+6% at mid-length, 0 at the ends)


def msec(nm, s, r):
    c = (MA[0] + _MU[0] * _ML * s, MA[1] + _MU[1] * _ML * s)
    return (nm, c, _MANG, r, r, r * 0.97, EGG)


# the head and crown design stations (u = station number): (u, centre (y, z), seam-A angle, T, B, W)
HEAD_KEYS = [(0, (-0.04, 0.282), -50.0, 0.07, 0.068, 0.088),     # s1 r15: neck fuller (the sheet has no stalk)
             (1, (-0.055, 0.255), -70.0, 0.066, 0.06, 0.092),
             (2, (-0.06, 0.222), -85.0, 0.07, 0.066, 0.094),
             (3, (-0.055, 0.194), -90.0, 0.084, 0.08, 0.088),
             (4, (-0.05, 0.165), -90.0, 0.09, 0.086, 0.092),
             (5, (-0.045, 0.137), -90.0, 0.07, 0.066, 0.072)]


def hsec(nm, u, prof):
    us = [k[0] for k in HEAD_KEYS]
    col = lambda i: round(_pchip(us, [k[i] for k in HEAD_KEYS], u), 5)
    yz = lambda j: round(_pchip(us, [k[1][j] for k in HEAD_KEYS], u), 5)
    return (nm, (yz(0), yz(1)), col(2), col(3), col(4), col(5), prof)


# the loft, mantle tip -> mouth: (name, centre (y, z), angle of the seam-A direction from +Z toward +Y, T, B, W, profile).
# The ring planes turn from across the tilted mantle axis to horizontal at the head; seam A stays on the same
# side (mantle top -> head front), so the loft never twists. Poly pass 3: neck, eye and crown-shoulder stations added.
SECS = [msec('M%d' % i, s, r) for i, (s, r) in enumerate(MANTLE)] + [
    hsec('N0', 0.0, HEAD), hsec('N1', 0.5, HEAD), hsec('H0', 1.0, HEAD), hsec('H1', 2.0, HEAD),   # eye pass: Hm dropped (eye face H0-H1 as before3)
    hsec('H2', 2.5, HEAD), hsec('C0', 3.0, CROWN), hsec('C1', 3.67, CROWN), hsec('C1b', 4.33, CROWN), hsec('C2', 5.0, CROWN)]

HUB = Vector((0.0, -0.05, 0.165))       # the arm crown centre (C1)

# arms (x >= 0 half): (crown column j, heading deg from -Y toward +X, tip reach r, centre z at t = 0, .25, .5, .75, 1,
# plan S amplitude, root half width). Read off the front view: the front pair hangs to the ground, the next pair
# reaches out level, the third runs low, the rear pair lifts behind the head.
ARMS = [(0, 20.0, 0.44, (0.165, 0.125, 0.07, 0.05, 0.075), 0.035, 0.039),     # fix pass 2: root 0.039, plan curve 0.035, tip lifts gently
        (2, 57.0, 0.54, (0.168, 0.16, 0.12, 0.10, 0.135), 0.035, 0.039),
        (4, 112.0, 0.54, (0.162, 0.115, 0.06, 0.05, 0.085), 0.035, 0.039),
        (6, 155.0, 0.50, (0.166, 0.15, 0.11, 0.09, 0.125), 0.03, 0.038)]
ARM_T6 = [0.07, 0.17, 0.28, 0.39, 0.50, 0.61, 0.72, 0.82, 0.91, 1.0]   # the old sections: suckers and bones keep these places
ARM_T = [round(0.07 + 0.93 * i / 21, 4) for i in range(22)]          # poly pass 3: 22 sections


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


def _smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def arm_centre(spec, t):
    """The arm's centre line: in the vertical plane of the heading it drops from the crown to its low point and lifts
    again to the tip (the S in side view; z a smooth curve through the five design heights); in plan one swing."""
    j, ph, R, zs, amp, w0 = spec
    a = math.radians(ph)
    h, t_ = Vector((math.sin(a), -math.cos(a), 0.0)), Vector((math.cos(a), math.sin(a), 0.0))
    r0 = 0.095
    r = r0 + (R - r0) * t
    z = _pchip([0, 0.25, 0.5, 0.75, 1.0], list(zs), t)       # poly pass 3: one smooth curve (was a smoothstep per quarter)
    lat = amp * math.sin(math.pi * min(t / 0.95, 1.0)) * (1 + t)   # fix pass 2: one-way curve, growing to the tip
    return h * r + t_ * lat + Vector((0.0, HUB.y, z))


def arm_frame(spec, t):
    """(p, U, S, rw, rh) at t: U = across (toward the back), S = up across the arm."""
    p = arm_centre(spec, t)
    T = (arm_centre(spec, min(t + 0.01, 1.0)) - arm_centre(spec, max(t - 0.01, 0.0))).normalized()
    S = (Vector((0, 0, 1)) - T * T.z).normalized()
    U = S.cross(T).normalized()
    rw = spec[5] * (1 - t) ** 1.5 + 0.006   # fix pass: whip taper (tip floor 6 mm: no needle tris)
    return (p, U, S, rw, rw * 0.95)


def arm_path(spec, ts=None):
    return [arm_frame(spec, t) for t in (ts or ARM_T)]


def grow_arm(bm, faces, roles, secs):
    """Extrude the root region section by section; every new vertex keeps the role (a = level: 1 top, 0 side,
    -1 underside; b = side across) of the vertex it was extruded from: an octagon
    (poly pass 3; was a hexagon), flat on top and underneath."""
    for p, U, S, rw, rh in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (a, b) in new.items():
            v.co = p + S * (a * rh) + U * (b * rw * (1.0 if abs(a) < 0.9 else 0.55))
        faces, roles = r['faces'], new
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {s[0]: i for i, s in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    cr = [rings[idx[n]] for n in ('C0', 'C1', 'C1b', 'C2')]
    for spec in ARMS:
        j = spec[0]
        faces = [spans[idx[n]][j] for n in ('C0', 'C1', 'C1b')]   # poly pass 3: a 3-face root column, 4 levels
        roles = {}
        for rr, a in zip(cr, (1.0, 0.4, -0.4, -1.0)):
            roles[rr[j]], roles[rr[j + 1]] = (a, -1), (a, 1)
        grow_arm(bm, faces, roles, arm_path(spec))
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    """The side head face (ring vertices 2-3, the old 1-2) between H0 and H1: the eye (eye pass: as before3)."""
    H0, H1 = P('H0'), P('H1')
    return (H0[2] + H0[3] + H1[2] + H1[3]) / 4


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.025 and abs(c.y - ec0.y) < 0.03
                                        and abs(c.z - ec0.z) < 0.03)
    bm = edit(body)
    mid = lambda a, b: (a + b) / 2
    # joint rings: where the mantle meets the head (the neck bend), mid-mantle (the breathing squeeze)
    for a, b, why in (('M11', 'N0', 'neck: a ring where the mantle meets the head, the mantle1 joint'),
                      ('M6', 'M7', 'mantle: a ring at the widest egg span, the mantle1-mantle2 joint')):
        e = edge_near(bm, mid(P(a)[3], P(b)[3]))
        with k.topo(bm, 'loop', why):
            loopcut(bm, e, t=0.5)
    recalc_normals(bm)
    # eye socket: a loop inside the side head face between H0 and H1, pushed 5 mm in; the brow corner out
    f = face_near(bm, ec0, n=(1, -0.3, 0))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye turret: a loop inside the side head face between H0 and H1'):
        inner = inset(bm, [f], 0.3, 0.0)   # fix pass 9: thinner inset, a wider turret face for the bigger lens
    move(list(inner[0].verts), fn * 0.013)          # fix pass: the socket face pushed OUT, a turret bump for the eye
    move([vert_near(bm, P('H0')[2])], (0.006, -0.004, 0.003))
    # the mouth cap a flat plane under the crown
    flatten([vert_near(bm, q) for q in P('C2')])
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'skin': '#ec7650', 'pale': '#f6b896', 'sucker': '#f3cfae', 'amber': '#d99a1c', 'pupil': '#1b1515'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    r = math.hypot(x, y - HUB.y)
    if z < 0.15 and r < 0.075:
        return 'pale'                                   # mouth cap under the crown
    if r > 0.1 and z < 0.235 and n.z < -0.45:   # s4 r3: z < 0.235 keeps the mantle underside skin
        return 'pale'                                   # arm undersides (the sucker side), border on the hexagon's lower corners
    return 'skin'


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
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def sucker(bm, q, n, rad):
    """A chunky sucker: a hexagonal cup, its base ring sunk 3 mm into the arm's flat underside, the rim
    standing out and a little narrower."""
    n, u, w = frame3(n)
    hx = lambda c, rr: [bm.verts.new(c + (u * math.cos(t) + w * math.sin(t)) * rr) for t in [k_ * math.pi / 3 for k_ in range(6)]]
    B = hx(q - n * 0.003, rad)
    T = hx(q + n * (0.004 + rad * 0.25), rad * 0.8)
    bm.faces.new(list(reversed(B)))
    for j in range(6):
        bm.faces.new([B[j], B[(j + 1) % 6], T[(j + 1) % 6], T[j]])
    bm.faces.new(T)


def stage3(k, body):
    paint(body, PAL, body_rule)
    ec = eye_face_centre()
    bmb = edit(body)
    f = face_near(bmb, ec + Vector((-0.004, 0, 0)), n=(1, -0.3, 0))
    c, n = f.calc_center_median().copy(), f.normal.copy()
    n = n if n.x > 0 else -n
    bmb.free()
    bm = bmesh.new()
    lens(bm, c, n, 0.021, 0.010)          # fix pass 9: lens r 0.017 -> 0.021, a clearer eye
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.0092 and n_.dot(n) > 0.5 else 'amber')
    # suckers: one per arm span on the flat underside, from the root to two thirds out
    bm = bmesh.new()
    for spec in ARMS:
        secs = arm_path(spec, ARM_T6)
        for i in range(0, 7):
            (p0, U0, S0, w0, h0), (p1, U1, S1, w1, h1) = secs[i], secs[i + 1]
            pm, Um, Sm, wm, hm = arm_frame(spec, (ARM_T6[i] + ARM_T6[i + 1]) / 2)   # poly pass 3: on the new surface
            q = pm - Sm * hm
            nn = -Sm
            rad = min(0.4 * (w0 + w1) / 2, 0.38 * (p1 - p0).length)
            sucker(bm, q, nn, rad)
    suck = object_from_bm('suckers', bm)
    paint(suck, {'sucker': PAL['sucker']}, lambda c_, n_, i: 'sucker')
    return [eye, suck]


def stage4(k, body, pieces):
    A = Vector((0.0, MA[0], MA[1]))
    Mtip = Vector((0.0, MTIP[0], MTIP[1]))
    Mmid = A.lerp(Mtip, 0.5)
    B = [('body', (0.0, -0.05, 0.14), (0.0, -0.055, 0.26), None),
         ('mantle1', tuple(A), tuple(Mmid), 'body'),
         ('mantle2', tuple(Mmid), tuple(Mtip), 'mantle1', True)]
    for n_, spec in enumerate(ARMS, 1):
        secs = arm_path(spec, ARM_T6)
        a = math.radians(spec[1])
        h = Vector((math.sin(a), -math.cos(a), 0.0))
        root = HUB + h * 0.06
        pts = [root, secs[2][0], secs[5][0], secs[9][0]]
        for s_, (p, q) in zip('abc', zip(pts, pts[1:])):
            par = 'body' if s_ == 'a' else 'arm%d%s.L' % (n_, 'ab'['bc'.index(s_)])
            B.append(('arm%d%s.L' % (n_, s_), tuple(p), tuple(q), par, s_ != 'a'))
    rig = armature(B)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            d = (eb.tail - eb.head).normalized()
            eb.align_roll(Vector((0, -1, 0)) if abs(d.z) > 0.7 else Vector((0, 0, 1)))   # arms: local Z up, rot X = curl up
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    for p in pieces:   # s4 r2: the eyes too follow the head skin (rigid to body they drifted)
        bind(p, rig, body=body)
    arms = [(n_, s_) for n_ in range(1, 5) for s_ in 'abc']
    amp = {'a': 5.0, 'b': 8.0, 'c': 12.0}
    lag = {'a': 0.0, 'b': 0.8, 'c': 1.6}
    # idle: a slow wave down every arm (each arm a quarter cycle behind the last), the mantle breathing
    keys = {}
    for f in (1, 13, 25, 37, 49):
        ph = 2 * math.pi * (f - 1) / 48
        d = {}
        for n_, s_ in arms:
            d['arm%d%s.L' % (n_, s_)] = (round(amp[s_] * math.sin(ph + n_ * 1.57 - lag[s_]), 2), 0, 0)
            d['arm%d%s.R' % (n_, s_)] = (round(amp[s_] * math.sin(ph + n_ * 1.57 + 1.0 - lag[s_]), 2), 0, 0)
        d['mantle1'] = (round(3 * math.sin(ph), 2), 0, 0)
        d['mantle2'] = (round(-2 * math.sin(ph), 2), 0, 0)
        keys[f] = d
    clip(rig, 'idle', keys)
    # move (swim): arms open up and out, then a jet stroke pulls them down and in, the tips trailing; the mantle squeezes
    sides = ('L', 'R')
    op = {f'arm{n_}{s_}.{sd}': {'a': (16, 0, 0), 'b': (8, 0, 0), 'c': (-6, 0, 0)}[s_] for n_, s_ in arms for sd in sides}
    cl = {f'arm{n_}{s_}.{sd}': {'a': (-14, 0, 0), 'b': (-8, 0, 0), 'c': (14, 0, 0)}[s_] for n_, s_ in arms for sd in sides}
    clip(rig, 'move', {1: dict(op, mantle1=(4, 0, 0)), 9: dict(cl, mantle1=(-4, 0, 0), mantle2=(-4, 0, 0)),
                       17: {'mantle1': (0, 0, 0)}, 25: dict(op, mantle1=(4, 0, 0))})
    # attack: the front two arm pairs rear up and curl, the body leans back, then they lash down and forward
    up = {f'arm{n_}{s_}.{sd}': {'a': (30, 0, 0), 'b': (18, 0, 0), 'c': (24, 0, 0)}[s_] for n_ in (1, 2) for s_ in 'abc' for sd in sides}
    hit = {f'arm{n_}{s_}.{sd}': {'a': (-22, 0, 0), 'b': (-12, 0, 0), 'c': (-16, 0, 0)}[s_] for n_ in (1, 2) for s_ in 'abc' for sd in sides}
    clip(rig, 'attack', {1: {}, 10: dict(up, body=(-8, 0, 0)), 16: dict(hit, body=(10, 0, 0)),
                         20: dict(hit, body=(10, 0, 0)), 26: {'body': (3, 0, 0)}, 32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
