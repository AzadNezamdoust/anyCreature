import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
import bmkit as BK

# Raven-wyvern, t7 hand box-model: one spine loft of 6-vertex half rings (tail fan tip -> beak tip), the two hind
# legs extruded as 2-face regions from the lower flank; stage 2 knee ring, neck and tail loops, eye socket, flat
# beak planes; stage 3 lens eyes, folded wing-arms (a lofted slab with primary feathers and a wrist claw), tail
# and nape feathers, toes and talons, colour along the loops; stage 4 rig (wing, leg, neck, tail chains) and clips.
# The sheet reads as a big raven; the wyvern proportions are put in on purpose: the head sits 0.10 m further
# forward and 0.15 m higher than the sheet's (a longer neck), the beak is longer and deeper.
META = dict(creature='raven_wyvern', model='opus', stage1_tris=(1200, 2400), total_tris=(2600, 3600),
            closeups=[('head', (0.0, -0.94, 1.10), 0.28, 'hero'),
                      ('foot', (0.16, -0.62, 0.05), 0.20, 'hero'),
                      ('wing', (0.27, -0.25, 0.55), 0.70, 'hero'),
                      ('tail fan', (0.0, 0.85, 0.10), 0.45, 'hero')])

J = dict(
    hips=(0.0, -0.25, 0.50), spine=(0.0, -0.50, 0.62), chest=(0.0, -0.70, 0.76),
    neck1=(0.0, -0.79, 0.91), neck2=(0.0, -0.77, 1.00), head=(0.0, -0.76, 1.08), beak=(0.0, -1.16, 1.04),
    tail0=(0.0, -0.05, 0.44), tail1=(0.0, 0.25, 0.30), tail2=(0.0, 0.50, 0.20), tail3=(0.0, 0.75, 0.13),
    tailtip=(0.0, 1.08, 0.06),
    hipL=(0.12, -0.38, 0.42), knee=(0.15, -0.50, 0.30), hock=(0.15, -0.43, 0.21), foot=(0.16, -0.56, 0.03),
    toe=(0.16, -0.78, 0.02),
    shoulder=(0.19, -0.66, 0.78), elbow=(0.27, -0.45, 0.60), wrist=(0.27, -0.72, 0.72), wingtip=(0.17, 0.45, 0.28),
)

BODY = [(0, 1), (0.6, 0.92), (1, 0.3), (0.88, -0.35), (0.5, -0.8), (0, -1)]
CHEST = [(0, 1), (0.65, 0.9), (1, 0.3), (0.95, -0.4), (0.5, -0.8), (0, -1)]
NECK = [(0, 1), (0.65, 0.9), (1, 0.2), (0.85, -0.45), (0.45, -0.85), (0, -1)]
HEAD = [(0, 1), (0.75, 0.93), (1, 0.3), (0.85, -0.4), (0.5, -0.85), (0, -1)]
BEAK = [(0, 1), (0.55, 0.85), (1, 0.2), (0.95, -0.35), (0.55, -0.85), (0, -1)]
TAILF = [(0, 1), (0.6, 0.8), (1, 0.1), (0.8, -0.4), (0.4, -0.8), (0, -1)]


def dens(prof):
    """Poly pass 3: a 6-vertex half ring -> 11 vertices. The old vertices stay (even indices); each new odd vertex
    sits on the Catmull-Rom curve through its neighbours, so the cross-section rounds out between the old planes."""
    e = [(-prof[1][0], prof[1][1])] + list(prof) + [(-prof[-2][0], prof[-2][1])]
    out = []
    for i in range(len(prof) - 1):
        p0, p1, p2, p3 = e[i], e[i + 1], e[i + 2], e[i + 3]
        out.append(p1)
        out.append(tuple(round((-a + 9 * b + 9 * c - d) / 16, 4) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(prof[-1])
    out[0] = (0.0, out[0][1]); out[-1] = (0.0, out[-1][1])
    return out


BODY, CHEST, NECK, HEAD, BEAK, TAILF = map(dens, (BODY, CHEST, NECK, HEAD, BEAK, TAILF))
NR = len(BODY)            # 11 vertices per half ring


def tb(nm, top, bot, W, prof):
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


def ax(nm, c, d, h, W, prof=TAILF):
    l = math.hypot(*d)
    py, pz = d[1] / l, -d[0] / l
    if pz < 0:
        py, pz = -py, -pz
    return tb(nm, (c[0] + py * h, c[1] + pz * h), (c[0] - py * h, c[1] - pz * h), W, prof)


# the spine loft, tail fan tip -> beak tip (head at -Y)
SECS = [
    ax('T0', (1.085, 0.06), (1.0, -0.1), 0.02, 0.15),
    ax('T1', (0.95, 0.08), (1.0, -0.12), 0.035, 0.26),
    ax('T15', (0.85, 0.105), (1.0, -0.18), 0.042, 0.24),          # pass 3: fan spread (sheet top 0.144)
    ax('T2', (0.75, 0.13), (1.0, -0.25), 0.048, 0.22),
    ax('T25', (0.625, 0.165), (1.0, -0.29), 0.054, 0.195),        # pass 3: (sheet top 0.21)
    ax('T3', (0.50, 0.20), (1.0, -0.33), 0.06, 0.17),
    ax('T35', (0.375, 0.245), (1.0, -0.38), 0.07, 0.155),        # pass 3: tail mid, sheet top 0.30
    ax('T4', (0.25, 0.29), (1.0, -0.42), 0.083, 0.15),
    tb('RT', (0.17, 0.405), (0.12, 0.185), 0.16, BODY),           # pass 3: rump into the tail root (sheet 0.40)
    tb('R1', (0.08, 0.47), (-0.04, 0.195), 0.175, BODY),          # top on the sheet (was 0.50)
    tb('RR', (0.0, 0.53), (-0.14, 0.215), 0.19, BODY),            # pass 3: the back rises (sheet 0.52)
    tb('R0', (-0.08, 0.60), (-0.25, 0.24), 0.205, BODY),
    tb('RM', (-0.175, 0.69), (-0.375, 0.27), 0.218, BODY),        # pass 3: mid flank over the thigh (sheet 0.685)
    tb('M0', (-0.27, 0.775), (-0.50, 0.31), 0.228, BODY),
    tb('MC', (-0.36, 0.835), (-0.655, 0.345), 0.242, CHEST),      # pass 3: the breast swell (sheet 0.83)
    tb('MC2', (-0.405, 0.862), (-0.73, 0.372), 0.247, CHEST),     # pass 3: breast at its widest
    tb('C0', (-0.45, 0.885), (-0.80, 0.40), 0.25, CHEST),
    tb('CN', (-0.515, 0.935), (-0.875, 0.53), 0.225, CHEST),      # pass 3: the round crop under the throat
    tb('N0', (-0.57, 0.97), (-0.92, 0.66), 0.19, NECK),
    tb('NN0', (-0.597, 1.01), (-0.918, 0.755), 0.174, NECK),      # pass 3
    tb('N1', (-0.62, 1.05), (-0.90, 0.84), 0.16, NECK),
    tb('NN1', (-0.637, 1.09), (-0.872, 0.902), 0.145, NECK),      # pass 3
    tb('N2', (-0.65, 1.13), (-0.84, 0.96), 0.13, NECK),
    tb('NN2', (-0.656, 1.152), (-0.815, 0.957), 0.121, NECK),     # pass 3
    tb('NH', (-0.662, 1.172), (-0.787, 0.955), 0.114, HEAD),      # pass 3: the nape into the skull
    tb('H0', (-0.69, 1.21), (-0.73, 0.96), 0.10, HEAD),
    tb('HH', (-0.735, 1.228), (-0.775, 0.968), 0.115, HEAD),      # pass 3: the round crown
    tb('H1', (-0.78, 1.235), (-0.82, 0.98), 0.124, HEAD),
    tb('H2', (-0.90, 1.21), (-0.91, 1.00), 0.109, HEAD),
    tb('HB', (-0.94, 1.19), (-0.945, 1.005), 0.08, BEAK),         # pass 3: the beak root steps down
    tb('B0', (-0.98, 1.17), (-0.98, 1.01), 0.055, BEAK),
    tb('B1', (-1.06, 1.13), (-1.06, 1.025), 0.04, BEAK),
    tb('B12', (-1.095, 1.105), (-1.093, 1.026), 0.032, BEAK),     # pass 3: the culmen curve
    tb('B2', (-1.13, 1.08), (-1.125, 1.025), 0.024, BEAK),
    tb('B3', (-1.175, 1.04), (-1.165, 1.005), 0.011, BEAK),
]

# hind leg sections: (centre xyz, rx, ry): feathered thigh, the knee, hock, tarsus, sole
# pass 3: 12-sided, 7 sections (upper thigh bulk and a shank added)
HIND = [((0.16, -0.465, 0.305), 0.076, 0.094), ((0.15, -0.47, 0.265), 0.072, 0.086), ((0.15, -0.445, 0.22), 0.044, 0.05),
        ((0.152, -0.47, 0.168), 0.034, 0.037), ((0.155, -0.50, 0.12), 0.03, 0.032),
        ((0.16, -0.555, 0.045), 0.034, 0.036), ((0.16, -0.565, 0.0), 0.05, 0.06)]


def leg_pt(sec, a):
    c, rx, ry = sec
    return (c[0] + rx * math.cos(a), c[1] + ry * math.sin(a), c[2])


def grow_ell(bm, faces, secs):
    """Extrude the root region down the leg sections; each boundary vertex keeps its angle around the root centre
    (in plan) and lands on that angle of every section's ellipse."""
    fs = set(faces)
    allv = {v for f in faces for v in f.verts}
    bnd = {v for f in faces for e in f.edges if sum(1 for g in e.link_faces if g in fs) == 1 for v in e.verts}
    cx = sum(v.co.x for v in bnd) / len(bnd); cy = sum(v.co.y for v in bnd) / len(bnd)
    sx = max(abs(v.co.x - cx) for v in bnd); sy = max(abs(v.co.y - cy) for v in bnd)
    raw = {v: math.atan2((v.co.y - cy) / sy, (v.co.x - cx) / sx) for v in allv}
    bedges = [e for f in faces for e in f.edges if sum(1 for g in e.link_faces if g in fs) == 1]
    order = [max(bnd, key=lambda v: v.co.x)]           # walk the boundary loop (topological order, no twist)
    while len(order) < len(bnd):
        nxt = [e.other_vert(order[-1]) for e in bedges if order[-1] in e.verts]
        nxt = [n for n in nxt if n not in order]
        if len(order) == 1:
            nxt.sort(key=lambda n: (raw[n] - raw[order[0]]) % (2 * math.pi))
        order.append(nxt[0])
    a0 = raw[order[0]]
    ang = {v: (a0 + 2 * math.pi * j / len(order), 1.0) for j, v in enumerate(order)}
    ang.update({v: (raw[v], 0.5) for v in allv - bnd})
    for sec in secs:
        old = [(v.co.copy(), val) for v, val in ang.items()]      # interior verts die in the extrude: keep positions
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(old, key=lambda o: (o[0] - v.co).length)[1]
        c, rx, ry = sec
        for v, (a, f) in new.items():
            if f == 1.0:
                v.co = Vector(leg_pt((c, rx, ry), a))
        cen = Vector(c)
        for v, (a, f) in new.items():                    # interior verts: halfway to their boundary neighbours
            if f != 1.0:
                nb = [e.other_vert(v) for e in v.link_edges if new.get(e.other_vert(v), (0, 0))[1] == 1.0]
                v.co = cen + (sum((n.co - cen for n in nb), Vector()) / len(nb) * 0.5 if nb else Vector())
        faces, ang = r['faces'], new
    return faces


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    return [(fx * W, y0 + fh * (T if fh >= 0 else B) * s, z0 + fh * (T if fh >= 0 else B) * co) for fx, fh in prof]


def role_pos(sec, u, s, corner=0.55):
    c, rx, ry = sec[0], sec[1], sec[2]
    k = 1.0 if u == 0 else corner
    return (c[0] + u * rx, c[1] + s * ry * k, c[2])


def grow(bm, faces, roles, secs, corner=0.55):
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (u, s) in new.items():
            v.co = Vector(role_pos(sec, u, s, corner))
        faces, roles = r['faces'], new
    return faces, roles


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    i = idx['R0']                      # pass 3: the leg root is a 4 x 2 face region (R0-RM-M0, old vertices 2-4)
    grow_ell(bm, [spans[j][q] for j in (i, i + 1) for q in (4, 5, 6, 7)], HIND)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    H1, H2 = P('H1'), P('H2')
    return (H1[3] + H1[4] + H2[3] + H2[4]) / 4      # pass 3: the side quad under the old eye plane


def stage2(k, body):
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ec0 = eye_face_centre()
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    with topo(bm, k.log, 'loop', 'knee ring: the bend under the thigh feathers'):
        loopcut(bm, edge_near(bm, mid(leg_pt(HIND[1], 0.0), leg_pt(HIND[2], 0.0))), t=0.5)
    with topo(bm, k.log, 'loop', 'tarsus ring: the hock bend'):
        loopcut(bm, edge_near(bm, mid(leg_pt(HIND[3], 0.0), leg_pt(HIND[4], 0.0))), t=0.5)
    for a_, b_ in (('CN', 'N0'), ('N0', 'NN0'), ('NH', 'H0')):
        with topo(bm, k.log, 'loop', f'neck loop in {a_}-{b_}: the long neck bends'):
            loopcut(bm, edge_near(bm, mid(P(a_)[0], P(b_)[0])), t=0.5)
    for a_, b_ in (('T4', 'RT'), ('T35', 'T4'), ('T2', 'T3')):
        with topo(bm, k.log, 'loop', f'tail loop in {a_}-{b_}: shorter spans, a bend'):
            loopcut(bm, edge_near(bm, mid(P(a_)[0], P(b_)[0])), t=0.5)
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with topo(bm, k.log, 'inset', 'eye socket'):
        inner = inset(bm, [f], 0.3, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.01)
    H1, H2, B0, B1, B2 = P('H1'), P('H2'), P('B0'), P('B1'), P('B2')
    move([vert_near(bm, H2[2])], (0.008, -0.01, 0.006))            # brow ridge over the eye
    flatten([vert_near(bm, q) for B_ in (B0, B1, B2) for q in (B_[4], B_[5], B_[6])])   # flat beak sides
    move([vert_near(bm, B0[2]), vert_near(bm, B1[2])], (0.004, 0.0, 0.006))          # culmen ridge planes
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'black': '#2e313d', 'sheen': '#323a58', 'beak': '#4a4d55', 'leg': '#55565c', 'talon': '#17181c',
       'iris': '#6a4420', 'pupil': '#0c0c0e'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.96 and z > 0.99:
        return 'beak'
    if y < -0.3 and z < 0.24 and x > 0.08:
        return 'leg'
    if -0.6 < y < 0.15 and n.z > 0.55 and x < 0.12:
        return 'sheen'                                   # back mantle
    return 'black'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
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


def _orient(fs, centre):
    for f in fs:
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - centre) < 0:
            f.normal_flip()


ROOT_TREE = [None]


def leaf(bm, root, d, nrm, L, w, t, sink=False):
    """A flat feather: a closed diamond (8 triangles) from root along d, w wide, t thick along nrm."""
    root, d, nrm = Vector(root), Vector(d).normalized(), Vector(nrm).normalized()
    if sink and ROOT_TREE[0]:
        c_, n_, _i, _d = ROOT_TREE[0].find_nearest(root)
        root = c_ - n_ * 0.02
    s = d.cross(nrm).normalized()
    m = root + d * L * 0.42
    vs = [bm.verts.new(p) for p in (root, root + d * L, m + s * w / 2, m - s * w / 2, m + nrm * t / 2, m - nrm * t / 2)]
    R, T, A, B, U, D = vs
    fs = [bm.faces.new(q) for q in ((R, A, U), (A, T, U), (T, B, U), (B, R, U), (A, R, D), (T, A, D), (B, T, D), (R, B, D))]
    _orient(fs, m)
    return fs


def cone(bm, a, b, r, up=(0, 0, 1)):
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    u = d.cross(Vector(up))
    u = u.normalized() if u.length > 1e-4 else d.orthogonal().normalized()
    w = d.cross(u).normalized()
    A = [bm.verts.new(a + (u * cu + w * cw) * r) for cu, cw in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    T = bm.verts.new(b)
    fs = [bm.faces.new(list(reversed(A)))] + [bm.faces.new([A[j], A[(j + 1) % 4], T]) for j in range(4)]
    _orient(fs, a * 0.7 + b * 0.3)
    return fs


def toe(bm, a, b, ra, rb, talon):
    """A 4-sided toe from a to b, a curved talon past b; returns (toe faces, talon faces)."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    u = d.cross(Vector((0, 0, 1))).normalized()
    w = d.cross(u).normalized()
    if w.z < 0:
        w = -w
    q = lambda c, r: [bm.verts.new(c + (u * cu + w * cw) * r) for cu, cw in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    nseg = max(1, math.ceil((b - a).length / 0.07))
    rings_ = [q(a.lerp(b, j / nseg), ra + (rb - ra) * j / nseg) for j in range(nseg + 1)]
    fs = [bm.faces.new(list(reversed(rings_[0]))), bm.faces.new(rings_[-1])]
    for R0, R1 in zip(rings_, rings_[1:]):
        for j in range(4):
            fs.append(bm.faces.new([R0[j], R0[(j + 1) % 4], R1[(j + 1) % 4], R1[j]]))
    for f in fs:
        f.normal_update()
        fc = f.calc_center_median()
        ax_ = a + d * max(0.0, min((b - a).length, (fc - a).dot(d)))
        if f.normal.dot(fc - ax_) < 0:
            f.normal_flip()
    tip = b + d * talon * 0.8 - Vector((0, 0, b.z - 0.002))
    cl = cone(bm, b - d * 0.01, tip, rb * 1.05)
    return fs, cl


# the folded wing-arm (x >= 0 half): (y, z top, z bottom, x, thickness) from the shoulder root to the tip
WSEC = [(-0.66, 0.85, 0.71, 0.17, 0.03), (-0.72, 0.89, 0.56, 0.285, 0.05), (-0.52, 0.84, 0.38, 0.295, 0.06),
        (-0.27, 0.72, 0.31, 0.285, 0.055), (-0.02, 0.57, 0.28, 0.24, 0.045), (0.24, 0.43, 0.27, 0.20, 0.03),
        (0.47, 0.32, 0.27, 0.17, 0.014)]


def wing_x(y, centre=False):
    """Outer face x of the folded wing slab at y (linear between WSEC sections)."""
    S = sorted(WSEC[1:])
    for a, b in zip(S, S[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return a[3] + (b[3] - a[3]) * t + (0 if centre else (a[4] + (b[4] - a[4]) * t) / 2)
    return S[-1][3]


def wing_bm():
    bm = bmesh.new()
    rings_ = []
    WS = [WSEC[0]]
    for a_, b_ in zip(WSEC, WSEC[1:]):
        WS += [tuple(p + (q - p) * 0.5 for p, q in zip(a_, b_)), b_] if a_ is not WSEC[0] else [b_]
    for (y, zt, zb, x, t) in WS:
        d = zt - zb
        pts = [(x, y, zt), (x + t / 2, y, zt - 0.25 * d), (x + t / 2, y, zb + 0.25 * d), (x, y - 0.01, zb),
               (x - t / 2, y, zb + 0.25 * d), (x - t / 2, y, zt - 0.25 * d)]
        rings_.append([bm.verts.new(p) for p in pts])
    for a, b in zip(rings_, rings_[1:]):
        for j in range(6):
            bm.faces.new([a[j], a[(j + 1) % 6], b[(j + 1) % 6], b[j]])
    bm.faces.new(list(reversed(rings_[0]))); bm.faces.new(rings_[-1])
    recalc_normals(bm)
    nw = len(bm.faces)
    # primary feathers: flat leaves off the lower back edge, laid along the wing face
    # three large primary steps at the tip only (no edge fringe)
    for (y, z, L) in ((-0.02, 0.31, 0.26), (0.14, 0.30, 0.26), (0.30, 0.29, 0.22)):
        leaf(bm, (wing_x(y, True), y, z + 0.03), (0.0, 0.85, -0.42), (1, 0, 0), L, 0.10, 0.018)
    # three broad covert plates straddling the outer face
    for (y, z) in ((-0.45, 0.58), (-0.18, 0.48), (0.08, 0.40)):
        leaf(bm, (wing_x(y) - 0.008, y, z), (0.0, 0.9, -0.38), (1, 0, 0), 0.26, 0.13, 0.03)
    nf = len(bm.faces)
    cone(bm, (0.303, -0.70, 0.84), (0.33, -0.81, 0.82), 0.014)      # the wyvern wrist claw
    bm.faces.index_update()
    return bm, nw, nf


def stage3(k, body):
    paint(body, PAL, body_rule)
    bm0 = edit(body); tree = BVHTree.FromBMesh(bm0); bm0.free()
    ROOT_TREE[0] = tree
    H1, H2 = P('H1'), P('H2')
    fn = (H2[3] - H1[3]).cross(H1[4] - H1[3]).normalized()
    fn = fn if fn.x > 0 else -fn
    c, n, _i, _d = tree.find_nearest(eye_face_centre() - fn * 0.01)
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.017, 0.009)
    eye = object_from_bm('eye', bm)
    paint(eye, {'iris': PAL['iris'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.007 and n_.dot(n) > 0.5 else 'iris')
    bm, nw, nf = wing_bm()
    wing = object_from_bm('wing', bm)
    paint(wing, {'black': PAL['black'], 'sheen': PAL['sheen'], 'talon': PAL['talon']},
          lambda c_, n_, i: 'black' if i < nw and c_.z > 0.62 else ('sheen' if i < nf else 'talon'))
    # feathers: the long tail fan's trailing tips and the shaggy nape and throat hackles
    bm = bmesh.new()
    for (x, y, sx, L) in ((0.04, 0.90, 0.08, 0.26), (0.11, 0.84, 0.30, 0.25), (0.17, 0.76, 0.55, 0.22)):
        z = 0.06 + (1.0 - y) * 0.25
        leaf(bm, (x, y, z), (sx, 1.0, -0.12), (0, 0.1, 1), L, 0.10, 0.016, sink=True)
    # nape and shaggy throat hackles (the heavy raven chest)
    for (x, y, z, d, L) in ((0.04, -0.66, 1.16, (0.3, 1.0, -0.5), 0.13), (0.07, -0.62, 1.07, (0.4, 1.0, -0.6), 0.12),
                            (0.05, -0.86, 0.92, (0.25, -0.6, -0.8), 0.15), (0.09, -0.84, 0.82, (0.35, -0.6, -0.8), 0.15),
                            (0.10, -0.80, 1.00, (0.5, 0.6, -0.8), 0.12), (0.07, -0.88, 0.72, (0.3, -0.6, -0.8), 0.14)):
        dd = Vector(d).normalized()
        leaf(bm, (x, y, z), dd, dd.cross(Vector((1, 0, 0))).normalized(), L, 0.06, 0.014, sink=True)
    feathers = object_from_bm('feathers', bm)
    paint(feathers, {'black': PAL['black'], 'sheen': PAL['sheen']}, lambda c_, n_, i: 'black')
    # toes and talons: three forward, one back
    bm = bmesh.new()
    F = Vector((0.16, -0.565, 0.032))
    tf, cf = [], []
    # detail pass 10-23: shorter, fatter toes (L/t 8.7 sticks -> <= 6): 3/4 length, radius 0.018/0.012 -> 0.022/0.016
    for tipv, talon in (((0.164, -0.74, 0.026), 0.05), ((0.112, -0.693, 0.026), 0.045), ((0.224, -0.689, 0.026), 0.045),
                        ((0.152, -0.465, 0.026), 0.045)):
        a_, b_ = toe(bm, F, tipv, 0.022, 0.016, talon)
        tf += a_; cf += b_
    bm.faces.index_update()
    talon_idx = {f.index for f in cf}
    toes = object_from_bm('toes', bm)
    paint(toes, {'leg': PAL['leg'], 'talon': PAL['talon']}, lambda c_, n_, i: 'talon' if i in talon_idx else 'leg')
    return [eye, wing, feathers, toes]


def bind_chain(piece, rig, names, pick=None):
    """Rigid per-vertex weights to the nearest bone of one chain (both sides; .L/.R by the vertex side)."""
    BK.apply_mirror(piece)
    piece.vertex_groups.clear()
    segs = BK._bone_segments(rig)
    for v in piece.data.vertices:
        p = piece.matrix_world @ v.co
        side = '.L' if p.x >= 0 else '.R'
        cand = [nm + side for nm in names]
        nm = pick(p, side) if pick else min(cand, key=lambda n_: BK._seg_dist(p, *segs[n_]))
        vg = piece.vertex_groups.get(nm) or piece.vertex_groups.new(name=nm)
        vg.add([v.index], 1.0, 'REPLACE')
    mw = piece.matrix_world.copy()
    piece.parent = rig
    piece.matrix_world = mw
    am = piece.modifiers.new('armature', 'ARMATURE')
    am.object = rig


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('neck0', J['chest'], J['neck1'], 'spine', True),
         ('neck1', J['neck1'], J['neck2'], 'neck0', True),
         ('neck2', J['neck2'], J['head'], 'neck1', True),
         ('head', J['head'], J['beak'], 'neck2', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('tail3', J['tail3'], J['tailtip'], 'tail2', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'spine'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['wingtip'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
         ('tarsus.L', J['hock'], J['foot'], 'shin.L', True),
         ('toe.L', J['foot'], J['toe'], 'tarsus.L', True)]
    rig = armature(B, roll='auto')
    for nm in ('upperarm', 'forearm', 'hand'):
        for s in ('.L', '.R'):
            rig.data.bones[nm + s].use_deform = False      # the body skin ignores the wing chain
    skin(body, rig)
    for nm in ('upperarm', 'forearm', 'hand'):
        for s in ('.L', '.R'):
            rig.data.bones[nm + s].use_deform = True
    for p in pieces:
        if p.name.startswith('wing'):
            bind_chain(p, rig, ['upperarm', 'forearm', 'hand'],
                       pick=lambda p_, s: ('hand' if p_.y > -0.45 else ('forearm' if p_.y < -0.62 else 'upperarm')) + s)
        elif p.name.startswith('toes'):
            bind_chain(p, rig, ['toe'], pick=lambda p_, s: 'toe' + s)
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'spine': (1.5, 0, 0), 'neck0': (-3, 0, 0), 'neck2': (4, 0, 0), 'tail1': (0, 0, 3),
                                   'forearm.L': (0, 0, 2), 'forearm.R': (0, 0, -2)},
                       24: {'head': (0, 0, 8), 'neck1': (2, 0, 0)},
                       36: {'spine': (1.5, 0, 0), 'neck0': (-3, 0, 0), 'neck2': (4, 0, 0), 'tail1': (0, 0, -3)},
                       48: {}})
    A = 24
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tarsus.R': (-20, 0, 0), 'neck0': (4, 0, 0), 'neck2': (-6, 0, 0), 'tail1': (0, 0, 4)},
        7: {'shin.L': (-10, 0, 0), 'shin.R': (25, 0, 0), 'tarsus.R': (-35, 0, 0), 'toe.R': (30, 0, 0), 'neck0': (-2, 0, 0), 'neck2': (5, 0, 0)},
        13: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tarsus.L': (-20, 0, 0), 'neck0': (4, 0, 0), 'neck2': (-6, 0, 0), 'tail1': (0, 0, -4)},
        19: {'shin.R': (-10, 0, 0), 'shin.L': (25, 0, 0), 'tarsus.L': (-35, 0, 0), 'toe.L': (30, 0, 0), 'neck0': (-2, 0, 0), 'neck2': (5, 0, 0)},
        25: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tarsus.R': (-20, 0, 0), 'neck0': (4, 0, 0), 'neck2': (-6, 0, 0), 'tail1': (0, 0, 4)}},
        loc={1: {'hips': (0, 0, 0)}, 7: {'hips': (0, 0, 0.03)}, 13: {'hips': (0, 0, 0)}, 19: {'hips': (0, 0, 0.03)}, 25: {'hips': (0, 0, 0)}})
    # attack: the wing-arms mantle out, the neck coils back, then a downward beak strike
    W = {'upperarm.L': (0, 0, -18), 'upperarm.R': (0, 0, 18), 'hand.L': (0, 0, -12), 'hand.R': (0, 0, 12)}
    clip(rig, 'attack', {
        1: {},
        8: dict(W, **{'neck0': (-14, 0, 0), 'neck1': (-10, 0, 0), 'neck2': (12, 0, 0), 'head': (-8, 0, 0), 'tail1': (6, 0, 0)}),
        16: dict(W, **{'neck0': (22, 0, 0), 'neck1': (12, 0, 0), 'neck2': (-6, 0, 0), 'head': (18, 0, 0), 'spine': (-6, 0, 0)}),
        20: dict(W, **{'neck0': (20, 0, 0), 'neck1': (12, 0, 0), 'neck2': (-4, 0, 0), 'head': (24, 0, 0), 'spine': (-6, 0, 0)}),
        26: {'neck0': (8, 0, 0), 'head': (6, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.04, 0)}, 16: {'hips': (0, -0.06, 0)}, 20: {'hips': (0, -0.06, 0)},
             26: {'hips': (0, -0.02, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
