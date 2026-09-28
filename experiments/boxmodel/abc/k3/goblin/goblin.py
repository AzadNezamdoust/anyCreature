import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='goblin', model='opus')
META['keep_valleys'] = lambda c: c.z > 0.62 and c.z < 0.93 and c.y < -0.17

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    hips=(0, 0.11, 0.44), spine=(0, 0.08, 0.60), chest=(0, 0.06, 0.72), neck=(0, 0.01, 0.80),
    head=(0, -0.04, 0.88), crown=(0, -0.07, 1.06),
    hipL=(0.11, 0.08, 0.39), kneeL=(0.192, -0.005, 0.265), ankleL=(0.20, 0.135, 0.10), toeL=(0.225, -0.10, 0.03),
    shoulderL=(0.165, 0.055, 0.70), elbowL=(0.275, 0.03, 0.465), wristL=(0.31, -0.055, 0.29), handL=(0.33, -0.14, 0.13),
    earL=(0.15, -0.02, 0.965), earTipL=(0.44, 0.32, 0.95),
)

# half rings P0 (front seam) .. P5 (back seam), bottom to top: pelvis -> belly -> chest -> neck -> head
RINGS = [
    # R0 crotch
    [(0, -0.01, 0.34), (0.05, -0.02, 0.34), (0.075, 0.04, 0.335), (0.075, 0.14, 0.34), (0.05, 0.19, 0.35), (0, 0.20, 0.35)],
    # R1 hip / belt bottom
    [(0, -0.08, 0.42), (0.08, -0.07, 0.42), (0.128, 0.01, 0.43), (0.128, 0.15, 0.45), (0.08, 0.22, 0.46), (0, 0.235, 0.47)],
    # R2 belt top
    [(0, -0.09, 0.49), (0.085, -0.08, 0.49), (0.14, 0.0, 0.50), (0.135, 0.14, 0.52), (0.08, 0.21, 0.53), (0, 0.22, 0.54)],
    # R3 pot belly
    [(0, -0.135, 0.56), (0.105, -0.11, 0.56), (0.148, -0.015, 0.57), (0.13, 0.12, 0.60), (0.075, 0.19, 0.61), (0, 0.20, 0.62)],
    # R4 chest
    [(0, -0.065, 0.665), (0.07, -0.055, 0.665), (0.115, 0.0, 0.67), (0.118, 0.11, 0.68), (0.075, 0.18, 0.69), (0, 0.19, 0.70)],
    # R5 shoulders (hunch)
    [(0, -0.05, 0.72), (0.065, -0.04, 0.73), (0.135, 0.01, 0.745), (0.135, 0.10, 0.765), (0.07, 0.155, 0.775), (0, 0.155, 0.78)],
    # R6 neck
    [(0, -0.10, 0.73), (0.05, -0.08, 0.76), (0.09, -0.02, 0.80), (0.088, 0.045, 0.815), (0.052, 0.08, 0.82), (0, 0.085, 0.825)],
    # R7 jaw / chin underside
    [(0, -0.255, 0.63), (0.09, -0.215, 0.645), (0.145, -0.12, 0.72), (0.14, -0.02, 0.80), (0.09, 0.07, 0.85), (0, 0.09, 0.86)],
    # R8 mouth line
    [(0, -0.275, 0.665), (0.095, -0.24, 0.68), (0.155, -0.13, 0.75), (0.15, -0.03, 0.82), (0.10, 0.06, 0.86), (0, 0.085, 0.875)],
    # R9 nose underside (hook)
    [(0, -0.39, 0.70), (0.028, -0.265, 0.715), (0.125, -0.215, 0.765), (0.16, -0.06, 0.84), (0.115, 0.05, 0.88), (0, 0.085, 0.89)],
    # R10 nose top
    [(0, -0.405, 0.785), (0.03, -0.27, 0.79), (0.13, -0.23, 0.81), (0.165, -0.07, 0.86), (0.125, 0.05, 0.90), (0, 0.09, 0.915)],
    # R11 nose bridge / under the eye
    [(0, -0.30, 0.855), (0.04, -0.27, 0.855), (0.135, -0.237, 0.845), (0.168, -0.08, 0.89), (0.13, 0.05, 0.93), (0, 0.095, 0.945)],
    # R12 brow
    [(0, -0.33, 0.91), (0.06, -0.32, 0.915), (0.14, -0.27, 0.91), (0.168, -0.09, 0.93), (0.13, 0.05, 0.965), (0, 0.095, 0.98)],
    # R13 forehead
    [(0, -0.27, 1.0), (0.065, -0.25, 1.0), (0.125, -0.18, 0.99), (0.155, -0.07, 1.0), (0.12, 0.04, 1.01), (0, 0.075, 1.02)],
    # R14 dome
    [(0, -0.19, 1.075), (0.055, -0.17, 1.075), (0.09, -0.12, 1.07), (0.10, -0.05, 1.065), (0.075, 0.0, 1.055), (0, 0.02, 1.06)],
]


def sect(c, axis, hint, w, h):
    """A quad section at c, perpendicular to axis; w along hint, h across."""
    a = V(axis).normalized()
    s = V(hint)
    u = (s - a * s.dot(a)).normalized()
    v = a.cross(u)
    c = V(c)
    return [c + u * w / 2 + v * h / 2, c - u * w / 2 + v * h / 2, c - u * w / 2 - v * h / 2, c + u * w / 2 - v * h / 2]


def put(face, pts):
    """Place a quad's corners on pts, matching corners so the tube does not twist."""
    vs = [l.vert for l in face.loops]
    cur = centre(vs)
    tc = sum(pts, Vector()) / len(pts)
    best, bc = None, 1e9
    for order in (pts, pts[::-1]):
        for r in range(len(pts)):
            cand = order[r:] + order[:r]
            cst = sum(((v.co - cur).normalized() - (p - tc).normalized()).length_squared for v, p in zip(vs, cand))
            if cst < bc:
                best, bc = cand, cst
    place(vs, best)


def chain(bm, face, secs):
    r = None
    for s in secs:
        r = extrude(bm, [face])
        face = r['faces'][0]
        put(face, s)
    return face, r


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, r) for r in RINGS]
    bands = [bridge(bm, a, b) for a, b in zip(rings, rings[1:])]
    cap(bm, rings[0])
    cap(bm, rings[-1])
    recalc_normals(bm)

    # legs: from the down-and-out hip quad; thigh forward, knee, shin back, ankle, foot
    thigh, shin = sub(J['kneeL'], J['hipL']), sub(J['ankleL'], J['kneeL'])
    knee_ax = tuple(a + b for a, b in zip(V(thigh).normalized(), V(shin).normalized()))
    f, r = chain(bm, bands[0][2], [
        sect((0.13, 0.07, 0.345), thigh, (1, 0, 0), 0.085, 0.10),
        sect((0.19, -0.005, 0.29), knee_ax, (1, 0, 0), 0.082, 0.092),
        sect((0.196, 0.01, 0.245), shin, (1, 0, 0), 0.072, 0.08),
        sect((0.20, 0.13, 0.105), shin, (1, 0, 0), 0.05, 0.055),
        [V(0.155, 0.08, 0.004), V(0.25, 0.08, 0.004), V(0.25, 0.24, 0.004), V(0.155, 0.24, 0.004)],
    ])
    front = min(r['sides'], key=lambda g: g.calc_center_median().y)
    chain(bm, front, [
        [V(0.14, -0.075, 0.004), V(0.305, -0.075, 0.004), V(0.29, -0.06, 0.062), V(0.155, -0.06, 0.062)],
        [V(0.16, -0.125, 0.004), V(0.295, -0.125, 0.004), V(0.285, -0.118, 0.03), V(0.17, -0.118, 0.03)],
    ])

    # arms: from the shoulder quad, out and down, elbow, forearm forward, hand paddle
    upper, fore = sub(J['elbowL'], J['shoulderL']), sub(J['wristL'], J['elbowL'])
    elb_ax = tuple(a + b for a, b in zip(V(upper).normalized(), V(fore).normalized()))
    chain(bm, bands[4][2], [
        sect((0.195, 0.04, 0.685), (1, 0, -0.8), (0, 1, 0), 0.085, 0.08),
        sect((0.268, 0.035, 0.49), elb_ax, (1, 0, 0), 0.062, 0.07),
        sect((0.279, 0.024, 0.447), fore, (1, 0, 0), 0.058, 0.064),
        sect((0.31, -0.055, 0.29), fore, (1, 0, 0), 0.042, 0.05),
        sect((0.323, -0.11, 0.185), (0.1, -0.5, -1), (1, 0, 0), 0.036, 0.10),
    ])

    # ears: long horizontal blades out of the side of the skull, swept back
    ear = sub(J['earTipL'], J['earL'])
    chain(bm, bands[12][3], [
        sect((0.235, 0.085, 0.905), ear, (0, 0, 1), 0.15, 0.032),
        sect((0.335, 0.20, 0.93), ear, (0, 0, 1), 0.075, 0.022),
        sect((0.44, 0.32, 0.95), ear, (0, 0, 1), 0.012, 0.008),
    ])
    recalc_normals(bm)
    snap_seam(bm)
    ob = object_from_bm('body', bm)
    if os.environ.get('GOB_DBG'):
        eb = evaluated_bm(ob); eb.faces.ensure_lookup_table(); t = BVHTree.FromBMesh(eb)
        for i, j in t.overlap(t):
            if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
                say('HIT', tuple(round(x, 3) for x in eb.faces[i].calc_center_median()), tuple(round(x, 3) for x in eb.faces[j].calc_center_median()))
    return ob


def P(r, i):
    return V(RINGS[r][i])


def stage2(k, body):
    bm = edit(body)
    # neck: a second ring between the shoulders and the neck so the head can nod without collapsing
    vert_near(bm, P(7, 1)).co.z -= 0.012  # repair r20: the lower-lip corner quad is still a 5.6 deg needle: widen the band more
    vert_near(bm, P(7, 2)).co.z -= 0.04   # repair r19/r20: the mouth-corner band R7-R8 at P2 was 0.03 wide: the lower-lip corner quad is a needle
    with k.topo(bm, 'loop', 'neck bend: second loop between the shoulder ring R5 and the neck ring R6'):
        e = edge_near(bm, (P(5, 5) + P(6, 5)) / 2)
        loopcut(bm, e, t=0.5)
    # mouth: a loop across the chin band, pushed in to cut the grin line under the upper lip
    with k.topo(bm, 'loop', 'grin: a loop in the chin band R7-R8, its front pushed in as the mouth slot'):
        e = edge_near(bm, (P(7, 0) + P(8, 0)) / 2)
        ms = loopcut(bm, e, t=0.62, near=vert_near(bm, P(7, 0)))
    # the back of the skull: rings R6-R10 crowd together behind the jaw (slivers); spread them evenly
    ZB = {6: (0.79, 0.80, 0.805), 7: (0.782, 0.838, 0.843), 8: (0.83, 0.872, 0.877), 9: (0.852, 0.897, 0.90), 10: (0.877, 0.912, 0.918)}   # repair r19: R10 P3 0.866 -> 0.877
    vs = [(vert_near(bm, P(r, i)), z) for r, zs in ZB.items() for i, z in zip((3, 4, 5), zs)]
    for v, z in vs:
        v.co.z = z
    R6 = vert_near(bm, P(6, 3)); R6.co.x, R6.co.y = 0.079, 0.034   # repair r27: was (0.085, 0.04), on the line R6 P4 - R7 P3 (a 5.8 deg needle behind the jaw)
    # repair r19: the cheek quad R9-R10 P2-P3 was a 5.7 deg needle (P3 only 0.014 apart in z): R10 P3 up (above), out 0.006,
    # and R11 P3 up to 0.90 so the P3 column is evenly spaced from the jaw to the ear root
    vert_near(bm, P(10, 3)).co.x += 0.006
    vert_near(bm, P(11, 3)).co.z += 0.01
    # repair r16: the back of the skull reads as a groove: the seam ridge (P5 0.045 behind P4) meets two flat rear planes
    # at 38 deg. P4 comes back so the rear is one rounded convex shell, the turn shared between the seam and P4.
    for r, dy in ((8, 0.008), (9, 0.013), (10, 0.014), (11, 0.014), (12, 0.013), (13, 0.012), (14, 0.01)):
        vert_near(bm, P(r, 4)).co.y += dy
    for v in ms:                      # the grin loop sits midway in its band, then its front is pushed in
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in ms]
        if len(nb) == 2:
            v.co = (nb[0].co + nb[1].co) / 2
        if v.co.y < -0.15:
            f = max(0.0, min(1.0, (-0.15 - v.co.y) / 0.08))
            v.co.y += 0.03 * f
            v.co.z += 0.004 * f
    # ear: thicker root and a blunt (not needle) tip, so the blade has no sliver facets
    ear = V(sub(J['earTipL'], J['earL'])).normalized()
    t = ear.cross(V(0, 0, 1)).normalized()
    for c, s_t, s_h in (((0.235, 0.085, 0.905), 1.35, 1.0), ((0.335, 0.20, 0.93), 1.4, 1.0), ((0.44, 0.32, 0.95), 2.6, 2.4)):
        c = V(c)
        for v in verts_where(bm, lambda q: (q - c).length < (0.09 if s_h == 1.0 else 0.02) and abs((q - c).dot(ear)) < 0.02):
            d = v.co - c
            dt, dz = d.dot(t), d.z
            v.co = c + d + t * dt * (s_t - 1) + V(0, 0, dz * (s_h - 1))
    # repair r17: ears point out sideways (top view) and have thickness edge-on. The rear face of each section
    # moves back (0.010 at the base -> 0.003 at the tip), then the blade is sheared forward by up to 0.09 at the tip, x kept.
    for c, dd, rad in ((V(0.235, 0.085, 0.905), 0.010 * EAR_TH, 0.09), (V(0.335, 0.20, 0.93), 0.006 * EAR_TH, 0.09), (V(0.44, 0.32, 0.95), 0.003 * EAR_TH, 0.03)):
        for v in verts_where(bm, lambda q: (q - c).length < rad and abs((q - c).dot(ear)) < 0.02):
            if (v.co - c).dot(t) < 0:
                v.co.y += dd
    for v in verts_where(bm, lambda q: q.x > 0.2 and q.z > 0.85):
        v.co.y -= EAR_SHEAR * max(0.0, min(1.0, (v.co.x - 0.2) / 0.24))
    # repair r12: eyes face forward under a heavy brow, crown domed. The socket's outer corners come forward
    # (the eye quad turns from the side to the front), the brow ring overhangs forward and down, the dome rises.
    up = [(vert_near(bm, P(11, 2)), V(0, -0.04, 0)), (vert_near(bm, P(11, 1)), V(0, -0.02, 0)), (vert_near(bm, P(12, 2)), V(0, -0.03, -0.009)),
          (vert_near(bm, P(12, 1)), V(0, -0.02, -0.009)), (vert_near(bm, P(12, 0)), V(0, -0.015, -0.009))]
    up += [(vert_near(bm, P(14, i)), V(0, 0, 0.014)) for i in range(6)]
    up += [(vert_near(bm, P(13, i)), V(0, -0.006, 0.007)) for i in range(6)]
    for v, d in up:
        v.co += d
    # eye sockets: a loop inside the eye quad, sunk into the skull under the brow
    with k.topo(bm, 'inset', 'eye socket under the brow (R11-R12, P1-P2)'):
        c = (P(11, 1) + P(11, 2) + P(12, 2) + P(12, 1)) / 4
        sk = inset(bm, [face_near(bm, c, n=(0, -1, 0))], 0.28, depth=-0.012)
    for v in sk[0].verts:              # repair r20: the socket floor sinks 0.01 back, so its top wall is not a 1.7 deg needle
        v.co.y += 0.01
    # brow: push the brow ring's front forward so it overhangs the socket
    for i, d in ((1, 0.012), (2, 0.014)):
        vert_near(bm, P(12, i)).co.y -= d
    # cheekbone: lift and widen the cheek vertex under the eye into a plane change
    vert_near(bm, P(11, 2)).co.x += 0.008
    # repair r11: hooked nose, not a box snout: the nose top slopes down from the bridge and the tip drops below the mouth line
    NOSE = {(10, 0): (0, 0.006, -0.045), (9, 0): (0, 0.02, -0.05), (10, 1): (-0.008, 0, -0.02), (9, 1): (-0.008, 0, -0.02)}
    nv = [(vert_near(bm, P(r, i)), d) for (r, i), d in NOSE.items()]
    for v, d in nv:
        v.co += V(d)
    # knuckles of the spine: the belly's lowest front ring drops a touch so the belt band reads under the belly
    for v in verts_where(bm, lambda c: abs(c.z - 0.49) < 0.012 and c.y < -0.05):
        v.co.y += 0.012
    # repair r24: pot belly over the belt: the belly ring R3 comes forward (front 0.02) and out (sides 0.01), the chest R4 a touch
    for (r, i), d in {(3, 0): (0, -0.035, -0.005), (3, 1): (0.012, -0.032, -0.005), (3, 2): (0.012, -0.008, 0),
                      (4, 0): (0, -0.008, 0), (4, 1): (0.004, -0.008, 0)}.items():
        vert_near(bm, P(r, i)).co += V(d)
    r8 = {vert_near(bm, P(8, i)) for i in (0, 1, 2)}
    msf = set(ms)
    MOUTH[:] = [f.calc_center_median().copy() for f in bm.faces
                if len(set(f.verts) & msf) >= 2 and len(set(f.verts) & r8) >= 1 and f.calc_center_median().y < -0.12]
    # repair r14: the grin opens up into the cheek: the upper-lip quad R8-R9 P1-P2 is painted dark too,
    # so the mouth band rises from the nose root to the cheek corner (R9 P2 is 0.07 above R8 P0)
    r9p1, r9p2, r8p2 = nv[3][0], vert_near(bm, P(9, 2)), vert_near(bm, P(8, 2))
    lipf = [f for f in r9p1.link_faces if r8p2 in f.verts][0]
    lipf.normal_update()
    MOUTH.append(lipf.calc_center_median().copy())
    LIP[:] = [r9p1.co.copy(), r9p2.co.copy(), lipf.normal.copy()]
    if os.environ.get('GOB_DBG'):
        def mina(a, b, c):
            return min(math.degrees((y - x).angle(z - x, 0)) for x, y, z in ((a, b, c), (b, c, a), (c, a, b)))
        for f in bm.faces:
            q = [v.co for v in f.verts]
            if len(q) == 4:
                d1 = min(mina(q[0], q[1], q[2]), mina(q[0], q[2], q[3]))
                d2 = min(mina(q[1], q[2], q[3]), mina(q[1], q[3], q[0]))
                if min(d1, d2) < 6.5:
                    say('SLIV', tuple(round(x, 3) for x in f.calc_center_median()), round(d1, 1), round(d2, 1), [tuple(round(x, 3) for x in p) for p in q])
            elif len(q) > 4:
                say('NGON', len(q), tuple(round(x, 3) for x in f.calc_center_median()))
    recalc_normals(bm)
    if os.environ.get('GOB_VAL'):
        bm.normal_update()
        for e in bm.edges:
            if len(e.link_faces) == 2 and all(v.co.x >= 0 for v in e.verts) and min(v.co.z for v in e.verts) > 0.62:
                fa, fb = e.link_faces
                d = (fb.calc_center_median() - fa.calc_center_median()).dot(fa.normal)
                ang = math.degrees(fa.normal.angle(fb.normal, 0))
                if d > 0.002 and ang > 20:
                    say('VAL', round(ang), [tuple(round(x, 3) for x in v.co) for v in e.verts])
    commit(body, bm)


MOUTH = []
EAR_SHEAR = 0.02    # r17: the top-view IoU floor (0.9) caps the ear tip's forward shear: 0.02 -> 0.909, 0.03 -> 0.895
EAR_TH = 1.0
LIP = []
PAL = {'skin': '#6aa84f', 'belly': '#9ccc7a', 'belt': '#4a3222', 'cloth': '#7a5a3a',
       'fang': '#efe6cf', 'eye': '#f2d23c', 'pupil': '#2b1d14', 'brass': '#b8963c'}


def pal(*keys):
    return {kk: PAL[kk] for kk in keys}


def hnorm(pts, i):
    """Outward horizontal normal at pts[i] of a half ring (front seam -> back seam)."""
    a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
    n = V(b.y - a.y, -(b.x - a.x), 0)
    if i in (0, len(pts) - 1):
        n.x = 0
    return n.normalized()


def basis(a, hint=(0, 0, 1)):
    a = V(a).normalized()
    h = V(hint)
    if abs(h.dot(a)) > 0.95:
        h = V(1, 0, 0)
    u = (h - a * h.dot(a)).normalized()
    return a, u, a.cross(u)


def spike(bm, base, tip, r, knots=((0.55, 0.85),), sides=4, hint=(0, 0, 1)):
    """A closed tapering cone: base ring, optional rings (t, radius scale), apex."""
    base, tip = V(base), V(tip)
    a, u, w = basis(tip - base, hint)
    ang = [2 * math.pi * (i + 0.5) / sides for i in range(sides)]
    rows = []
    for t, sc in ((0.0, 1.0),) + tuple(knots):
        c = base.lerp(tip, t)
        rows.append(ring(bm, [c + (u * math.cos(q) + w * math.sin(q)) * r * sc for q in ang]))
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1, closed=True)
    ap = bm.verts.new(tip)
    last = rows[-1]
    for i in range(sides):
        bm.faces.new([last[i], last[(i + 1) % sides], ap])
    cap(bm, list(reversed(rows[0])))


def plate(bm, top, bot, nrm, d0, d1):
    """A thick cloth strip: rows top/bot (seam first), offset d0..d1 along per-column normals.
    Open at the seam (the mirror closes it), capped at the outer column."""
    ti = ring(bm, [p + n * d0 for p, n in zip(top, nrm)]); to = ring(bm, [p + n * d1 for p, n in zip(top, nrm)])
    bi = ring(bm, [p + n * d0 for p, n in zip(bot, nrm)]); bo = ring(bm, [p + n * d1 for p, n in zip(bot, nrm)])
    bridge(bm, to, bo); bridge(bm, bi, ti); bridge(bm, ti, to); bridge(bm, bo, bi)
    bm.faces.new([ti[-1], to[-1], bo[-1], bi[-1]])


def plate3(bm, top, bot, nrm, dt, db):
    """repair r21: a thick cloth quad strip with a mid-height row, so the long side wall is split once.
    Rows top/mid/bot (seam first); the top row sits at offsets dt (inside the belt), the bottom at db (thicker)."""
    mid = [a.lerp(b, 0.5) for a, b in zip(top, bot)]
    dm = ((dt[0] + db[0]) / 2, (dt[1] + db[1]) / 2)
    rows = []
    for pts, (d0, d1) in ((top, dt), (mid, dm), (bot, db)):
        rows.append((ring(bm, [p + n * d0 for p, n in zip(pts, nrm)]), ring(bm, [p + n * d1 for p, n in zip(pts, nrm)])))
    (ti, to), (mi, mo), (bi, bo) = rows
    bridge(bm, to, mo); bridge(bm, mo, bo); bridge(bm, bi, mi); bridge(bm, mi, ti)
    bridge(bm, ti, to); bridge(bm, bo, bi)
    bm.faces.new([ti[-1], to[-1], mo[-1], mi[-1]])
    bm.faces.new([mi[-1], mo[-1], bo[-1], bi[-1]])
    recalc_normals(bm)


def stage3(k, body):
    in_mouth = lambda c: any((c - m).length < 2e-3 for m in MOUTH)
    paint(body, pal('skin', 'belly', 'belt'),
          lambda c, n, i: 'belt' if in_mouth(V(abs(c.x), c.y, c.z)) else
          'belly' if (0.435 < c.z < 0.665 and abs(c.x) < 0.1 and c.y < -0.04) else 'skin')
    bm0 = edit(body); bm0.normal_update()
    r1 = [vert_near(bm0, P(1, i)).co.copy() for i in range(6)]
    r2 = [vert_near(bm0, P(2, i)).co.copy() for i in range(6)]
    sock = face_near(bm0, (P(11, 1) + P(11, 2) + P(12, 2) + P(12, 1)) / 4, n=(0, -1, 0))
    sc, sn = sock.calc_center_median().copy(), sock.normal.copy()
    if os.environ.get('GOB_FACE'):
        for f in bm0.faces:
            c = f.calc_center_median()
            if c.x >= 0 and c.y < -0.08 and 0.6 < c.z < 0.86:
                say('FACE', f.index, len(f.verts), tuple(round(x, 3) for x in c), tuple(round(x, 2) for x in f.normal),
                    'M' if any((c - m).length < 2e-3 for m in MOUTH) else '')
        say('SOCK', tuple(round(x, 3) for x in sc), tuple(round(x, 2) for x in sn))
    bm0.free()
    pieces = []

    # belt: a thick band hugging the R1-R2 band, open at the seam
    lo = [a.lerp(b, 0.12) for a, b in zip(r1, r2)]
    hi = [a.lerp(b, 0.92) for a, b in zip(r1, r2)]
    ns = [hnorm(r1, i) for i in range(6)]
    bm = bmesh.new()
    A = ring(bm, [p + n * 0.009 for p, n in zip(lo, ns)]); B = ring(bm, [p + n * 0.028 for p, n in zip(lo, ns)])
    C = ring(bm, [p + n * 0.028 for p, n in zip(hi, ns)]); D = ring(bm, [p + n * 0.009 for p, n in zip(hi, ns)])
    bridge(bm, A, B); bridge(bm, B, C); bridge(bm, C, D); bridge(bm, D, A)
    belt = object_from_bm('belt', bm)
    paint(belt, pal('belt'), lambda c, n, i: 'belt')
    pieces.append(belt)

    # buckle: a chunky brass frame on the belt front, its back sunk into the belt
    yo = (lo[0].y + hi[0].y) / 2 - 0.028
    zm = (lo[0].z + hi[0].z) / 2
    bm = bmesh.new()
    yi, yf, bx, z0, z1 = yo + 0.009, yo - 0.014, 0.042, zm - 0.034, zm + 0.034
    q = ring(bm, [(0, yi, z0), (bx, yi, z0), (bx, yf, z0), (0, yf, z0), (0, yi, z1), (bx, yi, z1), (bx, yf, z1), (0, yf, z1)])
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (3, 2, 6, 7), (1, 0, 4, 5), (2, 1, 5, 6)):
        bm.faces.new([q[j] for j in f])
    recalc_normals(bm)
    inner = inset(bm, [face_near(bm, (bx / 2, yf, zm), n=(0, -1, 0))], 0.45, depth=0.006)
    ctr = [f.calc_center_median().copy() for f in inner]
    buckle = object_from_bm('buckle', bm)
    paint(buckle, pal('brass', 'belt'), lambda c, n, i: 'belt' if any((V(abs(c.x), c.y, c.z) - m).length < 1e-3 for m in ctr) else 'brass')
    pieces.append(buckle)

    # loincloth: tattered front and back flaps tucked into the belt
    for nm, idx, drops, tilt in (('cloth_front', (0, 1), (0.19, 0.15, 0.2, 0.13), -0.012),
                                 ('cloth_back', (5, 4), (0.2, 0.15, 0.21, 0.14), 0.02)):
        bm = bmesh.new()
        s0, s1 = idx
        s2 = s1 + (1 if s1 > s0 else -1)
        tops = [lo[s0], lo[s0].lerp(lo[s1], 0.5), lo[s1], lo[s1].lerp(lo[s2], 0.3)]
        nn = [ns[s0], ns[s0].lerp(ns[s1], 0.5).normalized(), ns[s1], ns[s1].lerp(ns[s2], 0.3).normalized()]
        tops = [t + V(0, 0, 0.013) for t in tops]
        bots = [t + V(0, tilt, -d) for t, d in zip(tops, drops)]
        plate3(bm, tops, bots, nn, (0.012, 0.023), (0.007, 0.028))   # repair r21: >= 0.02 thick below the belt
        cloth = object_from_bm(nm, bm)
        paint(cloth, pal('cloth'), lambda c, n, i: 'cloth')
        pieces.append(cloth)

    # eyes: a low-poly lens sunk in the socket, iris ring and pupil proud of it
    bm = bmesh.new()
    a, u, w = basis(V(sn.x, sn.y, sn.z * 0.35), (0, 0, 1))   # repair r13: the lens looks forward, not down at the floor
    e = sc
    ang = [2 * math.pi * i / 6 for i in range(6)]

    def hexr(off, r):
        return ring(bm, [e + a * off + (w * math.cos(q) + u * math.sin(q) * 0.78) * r for q in ang])
    ra, rb, rp = hexr(0.007, 0.039), hexr(0.015, 0.027), hexr(0.019, 0.013)
    ap = bm.verts.new(e - a * 0.02)
    for i in range(6):
        bm.faces.new([ra[(i + 1) % 6], ra[i], ap])
    bridge(bm, ra, rb, closed=True); bridge(bm, rb, rp, closed=True)
    cap(bm, rp)
    pc = e + a * 0.019
    eye = object_from_bm('eye', bm)
    paint(eye, pal('eye', 'pupil'), lambda c, n, i: 'pupil' if (V(abs(c.x), c.y, c.z) - pc).length < 0.004 else 'eye')
    pieces.append(eye)

    # fangs: two per side
    bm = bmesh.new()
    # repair r14: fangs x1.4, rooted in the upper-lip edge (R9 P1-P2) and hanging down over the dark grin, outer pair longer
    la, lb, ln = LIP
    for t, L, r in ((0.3, 0.05, 0.017), (0.68, 0.064, 0.02)):
        p = la.lerp(lb, t)
        spike(bm, p - ln * 0.012 + V(0, 0, 0.012), p + ln * 0.012 + V(0, 0, -L), r, knots=((0.5, 0.8),))
    fangs = object_from_bm('fangs', bm)
    paint(fangs, pal('fang'), lambda c, n, i: 'fang')
    pieces.append(fangs)

    # repair r15: piece_nose, a hooked tip rooted in the nose wedge: forward along the bridge line, then down past the mouth line
    bm = bmesh.new()
    path = [(V(0, -0.30, 0.735), 0.012, 0.034), (V(0, -0.372, 0.718), 0.017, 0.03), (V(0, -0.405, 0.668), 0.014, 0.02)]
    tipn = V(0, -0.392, 0.612)
    rows = []
    for j, (c, rx, rz) in enumerate(path):
        nxt = path[j + 1][0] if j + 1 < len(path) else tipn
        prv = path[j - 1][0] if j else c
        ax = (nxt - prv).normalized()
        u = V(1, 0, 0); w = ax.cross(u).normalized()
        rows.append(ring(bm, [c + u * rx * math.cos(q) + w * rz * math.sin(q) for q in [2 * math.pi * (i + 0.5) / 6 for i in range(6)]]))
    for r0, r1 in zip(rows, rows[1:]):
        bridge(bm, r0, r1, closed=True)
    apx = bm.verts.new(tipn)
    for i in range(6):
        bm.faces.new([rows[-1][i], rows[-1][(i + 1) % 6], apx])
    cap(bm, list(reversed(rows[0])))
    recalc_normals(bm)
    nose = object_from_bm('nose', bm, mirror=False)
    paint(nose, pal('skin'), lambda c, n, i: 'skin')
    pieces.append(nose)

    # fingers: three long clawed fingers out of the hand paddle
    ha, hu, hv = basis((0.1, -0.5, -1), (1, 0, 0))
    hc = V(0.323, -0.11, 0.185)
    bm = bmesh.new()
    for sgn in (-1, 0, 1):
        b0 = hc + hv * 0.03 * sgn - ha * 0.02
        tip = hc + hv * 0.04 * sgn + ha * 0.085 + V(-0.012, 0.02, 0)
        spike(bm, b0, tip, 0.011, knots=((0.5, 0.9), (0.72, 0.8)), hint=(1, 0, 0))
    fingers = object_from_bm('fingers', bm)
    zc = hc.z + ha.z * 0.06
    paint(fingers, pal('skin', 'fang'), lambda c, n, i: 'fang' if c.z < zc else 'skin')
    pieces.append(fingers)

    # toe claws: three per foot
    bm = bmesh.new()
    for x, dx in ((0.18, -0.012), (0.228, 0.0), (0.276, 0.012)):
        spike(bm, (x, -0.10, 0.017), (x + dx, -0.168, 0.006), 0.011, knots=((0.5, 0.8),))
    claws = object_from_bm('claws', bm)
    paint(claws, pal('fang'), lambda c, n, i: 'fang')
    pieces.append(claws)
    return pieces


def even_through(ob, rad=0.06):
    """repair r22: the thick cloth's inner and outer skins took different body weights (inner nearer the thigh),
    so the plate folded over in move. Each vertex takes the mean weights of the cloth vertices within rad
    (its partner through the thickness), so the plate bends as one sheet."""
    vs = ob.data.vertices
    W = [{g.group: g.weight for g in v.groups} for v in vs]
    new = []
    for v in vs:
        nb = [i for i, u in enumerate(vs) if (u.co - v.co).length < rad]
        acc = {}
        for i in nb:
            for g, w in W[i].items():
                acc[g] = acc.get(g, 0.0) + w / len(nb)
        new.append(acc)
    for vg in ob.vertex_groups:
        vg.remove(list(range(len(vs))))
    for i, acc in enumerate(new):
        for g, w in acc.items():
            if w > 1e-4:
                ob.vertex_groups[g].add([i], w, 'REPLACE')


def stage4(k, body, pieces):
    rig = armature([
        ('hips', (0, 0.11, 0.40), (0, 0.09, 0.54), None),
        ('spine', (0, 0.09, 0.54), (0, 0.07, 0.66), 'hips', True),
        ('chest', (0, 0.07, 0.66), (0, 0.04, 0.77), 'spine', True),
        ('neck', (0, 0.04, 0.77), (0, -0.02, 0.85), 'chest', True),
        ('head', (0, -0.02, 0.85), J['crown'], 'neck', True),
        ('ear.L', J['earL'], J['earTipL'], 'head'),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hand.L', J['wristL'], J['handL'], 'forearm.L', True),
    ], roll='auto')
    skin(body, rig)
    for pc in pieces:
        if pc.name == 'piece_fingers':
            bind(pc, rig)            # nearest bone per vertex: each finger rides its hand bone rigidly
        else:
            bind(pc, rig, body=body)
        if pc.name.startswith('piece_cloth'):
            even_through(pc)
    both = lambda b, v: {b + '.L': v, b + '.R': v}
    clip(rig, 'idle', {
        1: {},
        12: {'head': (0, 22, 0), 'neck': (3, 8, 0), 'chest': (2, 0, 0), **both('ear', (6, 0, 0)), **both('forearm', (8, 0, 0))},
        24: {'head': (-6, 0, 0), 'neck': (0, 0, 0), 'chest': (0, 0, 0), **both('ear', (-4, 0, 0)), **both('forearm', (0, 0, 0))},
        36: {'head': (0, -22, 0), 'neck': (3, -8, 0), 'chest': (2, 0, 0), 'ear.L': (8, 0, 0), 'ear.R': (-2, 0, 0), **both('forearm', (8, 0, 0))},
        48: {}})
    W = {1: (-18, 18, 0, -10), 9: (0, 0, -30, 0), 17: (18, -18, -10, 0), 25: (0, 0, 0, -30), 33: (-18, 18, 0, -10)}
    mv = {}
    for f, (tl, tr, sl, sr) in W.items():
        mv[f] = {'thigh.L': (tl, 0, 0), 'thigh.R': (tr, 0, 0), 'shin.L': (sl, 0, 0), 'shin.R': (sr, 0, 0),
                 'upperarm.L': (-0.6 * tl, 0, 0), 'upperarm.R': (-0.6 * tr, 0, 0),
                 'forearm.L': (12, 0, 0), 'forearm.R': (12, 0, 0),
                 'hips': (0, 5 if tl < 0 else -5 if tl > 0 else 0, 0), 'chest': (10, 0, 0), 'head': (-10, 0, 0)}
    clip(rig, 'move', mv)
    clip(rig, 'attack', {
        1: {},
        7: {'upperarm.R': (70, 0, 0), 'forearm.R': (35, 0, 0), 'hand.R': (-20, 0, 0), 'chest': (-6, -18, 0), 'head': (-6, 8, 0),
            'upperarm.L': (-10, 0, 0)},
        12: {'upperarm.R': (-25, 0, 0), 'forearm.R': (10, 0, 0), 'hand.R': (25, 0, 0), 'chest': (14, 16, 0), 'head': (4, -6, 0),
             'upperarm.L': (15, 0, 0)},
        18: {'upperarm.R': (5, 0, 0), 'forearm.R': (8, 0, 0), 'hand.R': (5, 0, 0), 'chest': (6, 6, 0), 'head': (0, 0, 0),
             'upperarm.L': (5, 0, 0)},
        24: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
