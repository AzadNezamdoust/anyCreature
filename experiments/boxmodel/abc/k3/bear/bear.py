import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='bear', model='opus')

# the skeleton the model is built on (metres, faces -Y, left flank +X, feet on z = 0)
J = dict(
    pelvis=(0.0, 0.60, 0.66), spine=(0.0, 0.18, 0.72), neck=(0.0, -0.28, 0.76),
    head=(0.0, -0.50, 0.63), snout=(0.0, -0.80, 0.47),
    tail0=(0.0, 0.70, 0.60), tail1=(0.0, 0.80, 0.56),
    shoulderL=(0.195, -0.11, 0.56), elbowL=(0.195, -0.12, 0.29), wristL=(0.195, -0.15, 0.10),
    pawL=(0.20, -0.36, 0.03),
    hipL=(0.20, 0.52, 0.58), kneeL=(0.20, 0.54, 0.28), hockL=(0.205, 0.62, 0.09),
    toeL=(0.21, 0.35, 0.03),
)


def sec(y, zt, zb, w, zw=None, t1=0.55, t5=0.45, d1=0.22, w2=0.9, w4=0.88):
    """A half section, top seam -> bottom seam: 7 verts, a keel below and a back plane above."""
    zw = zw if zw is not None else zb + 0.45 * (zt - zb)
    return [(0.0, y, zt),
            (t1 * w, y, zt - d1 * (zt - zw)),
            (w2 * w, y, zw + 0.5 * (zt - zw)),
            (w, y, zw),
            (w4 * w, y, zw - 0.5 * (zw - zb)),
            (t5 * w, y, zb + 0.12 * (zw - zb)),
            (0.0, y, zb)]


# nose -> tail. (y, zt, zb, w, extra)
STATIONS = [
    ('H0', sec(-0.815, 0.50, 0.425, 0.055, t1=0.8, d1=0.1, t5=0.75, w4=0.95)),            # nose pad
    ('H1', sec(-0.790, 0.545, 0.39, 0.085, t1=0.8, d1=0.1, t5=0.7, w4=0.95)),           # muzzle front
    ('H2', sec(-0.720, 0.585, 0.38, 0.098, t1=0.8, d1=0.1, t5=0.7, w4=0.95)),           # muzzle at the stop
    ('H3', sec(-0.685, 0.69, 0.38, 0.125, t1=0.6, t5=0.65)),                    # brow / dished face
    ('H4', sec(-0.600, 0.75, 0.38, 0.180, t5=0.6)),                            # skull, ears
    ('H5', sec(-0.500, 0.79, 0.40, 0.175)),                            # back of skull
    ('T0', sec(-0.360, 0.87, 0.41, 0.235, w4=0.95)),                            # neck
    ('T1', sec(-0.220, 0.955, 0.36, 0.300, w4=0.97)),                           # shoulder front
    ('T2', sec(-0.100, 1.000, 0.33, 0.300, w4=1.0)),                           # hump
    ('T3', sec(0.020, 0.975, 0.32, 0.290, w4=0.97)),                            # behind the shoulder
    ('T4', sec(0.200, 0.875, 0.31, 0.270)),                            # belly
    ('T5', sec(0.360, 0.860, 0.31, 0.270)),                            # flank / stifle
    ('T6', sec(0.520, 0.830, 0.33, 0.270)),                            # hip
    ('T7', sec(0.660, 0.760, 0.38, 0.240)),                            # haunch
    ('T8', sec(0.745, 0.690, 0.45, 0.185, w4=0.85)),                            # rump rear plane
    ('T9', sec(0.775, 0.640, 0.53, 0.060, t1=0.7)),                    # tail root
    ('T10', sec(0.810, 0.610, 0.550, 0.038, t1=0.7)),                  # tail tip
]


def hexring(cx, cy, z, rx, ry, tilt=0.0):
    return dict(OF=(cx + 0.8 * rx, cy - ry, z + tilt), OM=(cx + rx, cy, z), OB=(cx + 0.8 * rx, cy + ry, z - tilt),
                IB=(cx - 0.8 * rx, cy + ry, z - tilt), IM=(cx - rx, cy, z), IF=(cx - 0.8 * rx, cy - ry, z + tilt))


def leg(bm, faces, cur, rings):
    """Extrude a 2-quad region down ring by ring; cur maps role -> boundary vert."""
    for rg in rings:
        r = extrude(bm, faces)
        nv = r['verts']
        m = {role: min(nv, key=lambda q: (q.co - v.co).length) for role, v in cur.items()}
        for role, p in hexring(*rg).items():
            m[role].co = Vector(p)
        faces, cur = r['faces'], m
    return faces


def stage1(k):
    bm = bmesh.new()
    idx = {}
    rings = []
    for i, (nm, pts) in enumerate(STATIONS):
        idx[nm] = i
        rings.append(ring(bm, pts))
    bands = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, list(reversed(rings[0])))
    cap(bm, rings[-1])
    R = lambda nm, j: rings[idx[nm]][j]

    # forelegs: out of the lower flank between T1..T3
    ex, ey = J['elbowL'][0], J['elbowL'][1]
    wx, wy = J['wristL'][0], J['wristL'][1]
    fore = [(ex + 0.015, ey, 0.29, 0.120, 0.150),
            (ex + 0.01, ey - 0.01, 0.21, 0.108, 0.135),
            (wx, wy, 0.10, 0.085, 0.115),
            (wx + 0.005, -0.205, 0.045, 0.100, 0.155, -0.004),
            (wx + 0.005, -0.220, 0.0, 0.100, 0.160)]
    leg(bm, [bands[idx['T1']][4], bands[idx['T2']][4]],
        dict(OF=R('T1', 4), OM=R('T2', 4), OB=R('T3', 4), IB=R('T3', 5), IM=R('T2', 5), IF=R('T1', 5)), fore)

    # hind legs: out of the lower flank between T5..T7; stifle forward, hock back
    kx, ky = J['kneeL'][0], J['kneeL'][1]
    hx, hy = J['hockL'][0], J['hockL'][1]
    hind = [(kx, ky, 0.28, 0.110, 0.180),
            (kx, 0.60, 0.17, 0.100, 0.165),
            (hx, hy, 0.09, 0.090, 0.140),
            (hx + 0.005, 0.565, 0.04, 0.100, 0.205, -0.004),
            (hx + 0.005, 0.555, 0.0, 0.100, 0.215)]
    leg(bm, [bands[idx['T5']][4], bands[idx['T6']][4]],
        dict(OF=R('T5', 4), OM=R('T6', 4), OB=R('T7', 4), IB=R('T7', 5), IM=R('T6', 5), IF=R('T5', 5)), hind)

    # round ears out of the skull top between H4 and H5
    f = bands[idx['H4']][1]
    e1 = extrude(bm, [f])
    scale(e1['verts'], (1.25, 0.5, 1.0))
    move(e1['verts'], (0.03, 0.01, 0.045))
    e2 = extrude(bm, e1['faces'])
    scale(e2['verts'], (0.7, 0.75, 1.0))
    move(e2['verts'], (0.012, 0.0, 0.028))

    snap_seam(bm)
    return object_from_bm('body', bm)


META['keep_valleys'] = lambda c: abs(c[0]) > 0.06 and -0.68 < c[1] < -0.60 and 0.57 < c[2] < 0.70


def stage2(k, body):
    bm = edit(body)
    P = {nm: pts for nm, pts in STATIONS}
    Vn = lambda nm, j: vert_near(bm, P[nm][j])
    mid = lambda a, b: tuple((a[i] + b[i]) / 2 for i in range(3))

    # a loop in the neck so the head can nod without the skull ring collapsing
    with k.topo(bm, 'loop', 'neck bend: a ring between the back of the skull (H5) and the neck (T0)'):
        loopcut(bm, edge_near(bm, mid(P['H5'][3], P['T0'][3])), t=0.5)
    # a loop at the shoulder blade / withers, where the chest bone meets the neck
    with k.topo(bm, 'loop', 'withers: ring between T0 and T1 for the neck-chest bend'):
        loopcut(bm, edge_near(bm, mid(P['T0'][2], P['T1'][2])), t=0.55)

    # brow overhangs the eye
    move([Vn('H3', 1)], (0.0, -0.012, 0.012))
    move([Vn('H3', 2)], (0.006, -0.010, 0.006))
    # eye socket: a loop inside the face under the brow, pushed in
    with k.topo(bm, 'inset', 'eye socket under the brow'):
        f = face_near(bm, (0.115, -0.640, 0.640), n=(0.7, -0.6, 0.3))
        inset(bm, [f], 0.32, -0.010)

    # planes: muzzle top, muzzle side, forehead
    flatten([Vn(n, j) for n in ('H0', 'H1', 'H2') for j in (0, 1)])
    flatten([Vn(n, j) for n in ('H1', 'H2') for j in (2, 3, 4)])
    flatten([Vn(n, j) for n in ('H3', 'H4') for j in (0, 1)])
    # cheekbone: push the widest head verts out a little, square jaw corner
    move([Vn('H4', 3)], (0.012, 0.0, 0.0))
    move([Vn('H4', 4)], (0.006, 0.0, -0.006))
    # shoulder blade out, waist in, hip bone out: the flank stops being a tube
    move([Vn('T2', 2)], (0.016, 0.0, 0.0))
    move([Vn('T1', 2)], (0.010, 0.0, 0.0))
    move([Vn('T4', 3), Vn('T4', 4)], (-0.014, 0.0, 0.0))
    move([Vn('T4', 2)], (-0.008, 0.0, 0.0))
    move([Vn('T6', 2)], (0.012, 0.0, 0.010))
    # a flat back plane over the hump and a flat flank plane behind the shoulder
    flatten([Vn(n, j) for n in ('T3', 'T4', 'T5') for j in (0, 1)])
    # hump: the back was one long arch; lift the withers, drop the back half so the line falls to the rump
    wt0, wt1 = vert_near(bm, (0.0, -0.29, 0.91)), vert_near(bm, (0.14, -0.29, 0.87))
    lift = [(Vn('T1', 0), 0.040), (Vn('T1', 1), 0.034), (wt0, 0.028), (wt1, 0.022), (Vn('T2', 0), 0.020),
            (Vn('T2', 1), 0.016), (Vn('T4', 0), -0.020), (Vn('T4', 1), -0.016), (Vn('T5', 0), -0.028),
            (Vn('T5', 1), -0.022), (Vn('T6', 0), -0.030), (Vn('T6', 1), -0.024), (Vn('T7', 0), -0.025),
            (Vn('T7', 1), -0.020)]
    for v, dz in lift:
        move([v], (0.0, 0.0, dz))
    # armpit: the elbow ring's inner verts sat inside the flank line, so the inner leg face tilted up (a dark fan).
    # slide the ring down, stand the inner face upright, and lift the pinched chest keel between the forelegs
    elb = [vert_near(bm, p) for p in ((0.114, -0.270, 0.29), (0.090, -0.120, 0.29), (0.114, 0.030, 0.29))]
    elo = [v for v in verts_where(bm, lambda c: c.x > 0.25 and -0.30 < c.y < 0.06 and 0.27 < c.z < 0.31)]
    move(elb + elo, (0.0, 0.0, -0.025))
    move(elb, (0.030, 0.0, 0.0))
    move([Vn('T1', 6)], (0.0, 0.0, -0.030))              # one slope from the brisket back to the chest, no step
    move([Vn('T1', 5)], (0.0, 0.0, -0.012))
    move([Vn('T2', 6)], (0.0, 0.0, 0.020))
    move([Vn('T3', 6)], (0.0, 0.0, 0.022))
    # legs taper to the wrist / cannon; the paw rings stay wide
    wr = verts_where(bm, lambda c: c.x > 0.05 and -0.35 < c.y < 0.05 and abs(c.z - 0.10) < 0.004)
    scale(wr, (0.82, 0.85, 1.0), Vector((J['wristL'][0], J['wristL'][1], 0.10)))
    hk = verts_where(bm, lambda c: c.x > 0.05 and 0.40 < c.y < 0.85 and abs(c.z - 0.09) < 0.004)
    scale(hk, (0.86, 0.88, 1.0), Vector((J['hockL'][0], J['hockL'][1], 0.09)))
    # round ear: the inner-top corner of the tilted ear slab made a point; level the top, push it out, flat front
    ti, tf = vert_near(bm, (0.142, -0.521, 0.816)), vert_near(bm, (0.145, -0.559, 0.778))
    to, tof = vert_near(bm, (0.196, -0.521, 0.756)), vert_near(bm, (0.200, -0.559, 0.721))
    move([ti, tf], (0.004, 0.0, -0.030))
    move([to, tof], (0.008, 0.0, 0.006))
    move([ti, to], (0.0, 0.004, -0.010))                 # side view: the back-top corner was the fin tip
    move([tf, tof], (0.0, -0.008, 0.018))                # front-top up and forward: a level, cupped top
    ef = [v for v in verts_where(bm, lambda c: 0.11 < c.x < 0.215 and -0.57 < c.y < -0.55 and c.z > 0.68)]
    flatten(ef + [tf, tof])
    # brisket: drop the T0 and withers keel so the throat turns into a forward-facing chest plane (the bib)
    wk6, wk5 = vert_near(bm, (0.0, -0.29, 0.38)), vert_near(bm, (0.14, -0.29, 0.41))
    for v, dz in ((Vn('T0', 6), -0.11), (Vn('T0', 5), -0.09), (wk6, -0.08), (wk5, -0.06)):
        move([v], (0.0, 0.0, dz))
    # muzzle stop: drop the H2 top back and down so the brow stands as a step; lift the H1 top (no droop); flat nose face
    hh = P['H4'][0][2] - P['H4'][6][2]
    move([Vn('H2', 0), Vn('H2', 1)], (0.0, 0.006, -0.04 * hh))
    move([Vn('H1', 0), Vn('H1', 1)], (0.0, 0.0, 0.02 * hh))
    flatten([Vn('H0', j) for j in range(7)])
    # tail: the T10 cap was a flat disc on the rump; pull the tip ring back and down into a small stub cone,
    # and the root ring back a little so the stub has a base
    t10 = [Vn('T10', j) for j in range(7)]
    t9 = [Vn('T9', j) for j in range(7)]
    tc = Vector((0.0, P['T10'][0][1], (P['T10'][0][2] + P['T10'][6][2]) / 2))
    scale(t10, (0.8, 1.0, 0.8), tc)
    move(t10, (0.0, 0.045, -0.030))
    move(t9, (0.0, 0.025, -0.008))
    # paws: the box paw had step sides; narrow the paw-top ring and drop its front verts so the paw slopes to the toes
    for cz, cy, cx in ((0.045, -0.205, J['wristL'][0] + 0.005), (0.04, 0.565, J['hockL'][0] + 0.005)):
        pr = verts_where(bm, lambda c: c.x > 0.05 and abs(c.y - cy) < 0.25 and abs(c.z - cz) < 0.008)
        scale(pr, (0.9, 0.9, 1.0), Vector((cx, cy, cz)))
        fr = [v for v in pr if v.co.y < cy]
        move(fr, (0.0, 0.0, -0.007))
    commit(body, bm)


PAL = {'fur': '#6b4a33', 'dark': '#4a3222', 'muzzle': '#c9a57d', 'nose': '#1e1714',
       'claw': '#2a221e', 'eye': '#151010'}


def body_rule(c, n, i):
    x = abs(c.x)
    if c.y < -0.705 and c.z < 0.60:
        return 'muzzle'                                  # pale muzzle block: in front of H2-H3, below the eye socket
    if -0.56 < c.y < -0.10 and 0.30 < c.z < 0.58 and x < 0.20 and n.y < -0.3 and abs(n.x) < 0.5:
        return 'muzzle'                                  # pale bib: front-facing chest between the forelegs
    if c.z < 0.235:
        return 'dark'                                    # darker lower legs, border on the 0.21/0.17 rings
    return 'fur'


def bipyramid(bm, c, nrm, r, up, back, sides=6):
    nrm = Vector(nrm).normalized()
    t = nrm.orthogonal().normalized()
    b = nrm.cross(t)
    rim = ring(bm, [c + (t * math.cos(2 * math.pi * i / sides) + b * math.sin(2 * math.pi * i / sides)) * r
                    for i in range(sides)])
    top = bm.verts.new(c + nrm * up)
    bot = bm.verts.new(c - nrm * back)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new([rim[i], rim[j], top])
        bm.faces.new([rim[j], rim[i], bot])


def dome(bm, c, nrm, r, front, back, sides=8):
    """A low eye dome: a back ring sunk in the socket, a rim ring and a slightly domed front cap."""
    nrm = Vector(nrm).normalized()
    t = nrm.orthogonal().normalized()
    b = nrm.cross(t)
    rr = lambda o, rad: ring(bm, [c + nrm * o + (t * math.cos(2 * math.pi * i / sides) + b * math.sin(2 * math.pi * i / sides)) * rad
                                  for i in range(sides)])
    bk = rr(-back, r * 0.8)
    rim = rr(front * 0.4, r)
    bridge(bm, bk, rim, closed=True)
    cap(bm, list(reversed(bk)))
    top = bm.verts.new(c + nrm * front)
    for i in range(sides):
        bm.faces.new([rim[i], rim[(i + 1) % sides], top])


def claw(bm, base, tip, h):
    base, tip = Vector(base), Vector(tip)
    q = ring(bm, [base + Vector(d) for d in ((-h, 0, -h), (h, 0, -h), (h, 0, h), (-h, 0, h))])
    a = bm.verts.new(tip)
    bm.faces.new(q)
    for i in range(4):
        bm.faces.new([q[(i + 1) % 4], q[i], a])


def hook(bm, base, ang, L, hw, hh, sy):
    """A thick curved claw: base quad rooted 25% inside the toe, a smaller mid quad, the tip bent ~30 deg down."""
    a = math.radians(ang)
    d = Vector((math.sin(a), sy * math.cos(a), 0.0))
    s = Vector((math.cos(a), -sy * math.sin(a), 0.0))
    z = Vector((0.0, 0.0, 1.0))
    B = Vector(base)
    M = B + d * (0.6 * L) - z * (0.15 * L)
    T = B + d * L
    T.z = 0.002
    q0 = ring(bm, [B + s * u * hw + z * w * hh for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    q1 = ring(bm, [M + s * u * hw * 0.6 + z * w * hh * 0.6 for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bridge(bm, q0, q1, closed=True)
    bm.faces.new(list(reversed(q0)))
    tip = bm.verts.new(T)
    for i in range(4):
        bm.faces.new([q1[i], q1[(i + 1) % 4], tip])


def stage3(k, body):
    # eyes: a low-poly lens set proud in the stage-2 socket; the socket is painted dark fur so the eye reads as a dot in shadow
    hb = edit(body)
    cands = [f for f in hb.faces if (f.calc_center_median() - Vector((0.115, -0.640, 0.640))).length < 0.05
             and f.normal.x > 0.2]
    sock = min(cands, key=lambda f: f.calc_area())
    c, nr = sock.calc_center_median(), sock.normal.copy()
    sock_c = c.copy()
    hb.free()
    def rule(cc, n, i):
        if (Vector((abs(cc.x), cc.y, cc.z)) - sock_c).length < 0.028 and n.x > 0.1:
            return 'dark'
        return body_rule(cc, n, i)
    paint(body, PAL, rule)
    bm = bmesh.new()
    fwd = (nr + Vector((0.0, -0.5, 0.0))).normalized()   # face the lens more forward so it reads head-on too
    dome(bm, c, fwd, 0.021, 0.005, 0.010)          # depth 0.015 = 35% of the 0.042 width, front 0.005 proud
    eye = object_from_bm('eye', bm, mirror=True)
    paint(eye, {'eye': PAL['eye']}, lambda c, n, i: 'eye')
    # claws: five thick curved hooks per paw, graded (outer 80%), fanned out, tip bent down to the ground line
    bm = bmesh.new()
    fx = J['wristL'][0] + 0.005
    hx = J['hockL'][0] + 0.005
    for o, ang, g in ((-0.07, -12, 0.8), (-0.035, -6, 1.0), (0.0, 0, 1.0), (0.035, 6, 1.0), (0.07, 12, 0.8)):
        hook(bm, (fx + o, -0.362, 0.024), ang, 0.040 * g, 0.014, 0.011, -1)
        hook(bm, (hx + o * 0.9, 0.357, 0.017), ang, 0.028 * g, 0.010, 0.008, -1)
    claws = object_from_bm('claws', bm, mirror=True)
    paint(claws, {'claw': PAL['claw']}, lambda c, n, i: 'claw')
    # nose pad: a separate black block on the front-top of the muzzle (half, mirrored)
    bm = bmesh.new()
    bk = ring(bm, [(0, -0.792, 0.445), (0.032, -0.792, 0.450), (0.034, -0.792, 0.505), (0, -0.792, 0.512)])
    fr = ring(bm, [(0, -0.829, 0.452), (0.026, -0.829, 0.458), (0.030, -0.826, 0.498), (0, -0.826, 0.505)])
    bridge(bm, bk, fr)
    cap(bm, fr)
    cap(bm, list(reversed(bk)))
    nose = object_from_bm('nose', bm, mirror=True)
    paint(nose, {'nose': PAL['nose']}, lambda c, n, i: 'nose')
    return [eye, claws, nose]


def stage4(k, body, pieces):
    rig = armature([
        ('spine', J['pelvis'], J['spine'], None),
        ('chest', J['spine'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['snout'], 'neck', True),
        ('tail', J['tail0'], J['tail1'], 'spine'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'chest'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('paw.L', J['wristL'], J['pawL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'spine'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L', True),
        ('foot.L', J['hockL'], J['toeL'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-3, 0, 0), 'head': (-7, 0, 5)},
                       24: {'neck': (2, 0, 0), 'head': (6, 0, 0)},
                       36: {'chest': (1.5, 0, 0), 'neck': (-3, 0, 0), 'head': (-7, 0, -5)}, 48: {}})
    A, H = 16, 14
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-H, 0, 0), 'thigh.R': (H, 0, 0),
            'chest': (0, 0, 2), 'head': (-3, 0, 0)},
        9: {'forearm.R': (-25, 0, 0), 'paw.R': (-15, 0, 0), 'shin.L': (-15, 0, 0), 'foot.L': (12, 0, 0),
            'head': (2, 0, 0)},
        17: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (H, 0, 0), 'thigh.R': (-H, 0, 0),
             'chest': (0, 0, -2), 'head': (-3, 0, 0)},
        25: {'forearm.L': (-25, 0, 0), 'paw.L': (-15, 0, 0), 'shin.R': (-15, 0, 0), 'foot.R': (12, 0, 0),
             'head': (2, 0, 0)},
        33: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-H, 0, 0), 'thigh.R': (H, 0, 0),
             'chest': (0, 0, 2), 'head': (-3, 0, 0)}})
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (7, 0, 0), 'neck': (4, 0, 0), 'head': (6, 0, 0), 'upperarm.L': (35, 0, 0),
             'forearm.L': (-30, 0, 0), 'paw.L': (-10, 0, 0)},
        18: {'chest': (-4, 0, -6), 'neck': (-4, 0, 0), 'head': (-8, 0, 0), 'upperarm.L': (-12, 0, 0),
             'forearm.L': (-5, 0, 0), 'paw.L': (-12, 0, 0)},
        26: {'chest': (-2, 0, -3), 'head': (-4, 0, 0), 'upperarm.L': (-6, 0, 0)},
        40: {}},
        loc={1: {'spine': (0, 0, 0)}, 10: {'spine': (0, -0.02, 0)}, 18: {'spine': (0, 0.05, 0)},
             26: {'spine': (0, 0.02, 0)}, 40: {'spine': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
