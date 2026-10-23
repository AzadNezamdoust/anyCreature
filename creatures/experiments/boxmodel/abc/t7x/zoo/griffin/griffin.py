import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
from smooth_borders import smooth_borders

# Griffin, t7 hand box-model: one spine loft of 13-point half rings (tail stem -> hooked beak tip), the four legs
# extruded from broad 3 x 3 face regions of the lower flank (eagle forelegs, lion hind legs), the folded wings,
# eagle feet, lion claws, tail tuft and neck-ruff feathers as stage-3 pieces; stage 2 joint loops and the eye
# socket; stage 4 rig with idle / move / attack.
META = dict(creature='griffin', model='opus', stage1_tris=(1800, 3800), total_tris=(3000, 6500),
            closeups=[('head', (0.0, -0.88, 1.34), 0.26, 'hero'),
                      ('front foot', (0.19, -0.70, 0.10), 0.20, 'hero'),
                      ('hind paw', (0.24, 0.48, 0.10), 0.18, 'hero'),
                      ('wing', (0.30, 0.05, 0.95), 0.75, 'hero')])

# the skeleton (x >= 0 half; .L on +X), read off reference/side.png, front.png, rear.png (head at -Y)
J = dict(
    hips=(0.0, 0.36, 0.78), spine=(0.0, -0.02, 0.80), chest=(0.0, -0.42, 0.82),
    neck=(0.0, -0.70, 0.98), head=(0.0, -0.80, 1.32), nose=(0.0, -1.10, 1.22),
    tail0=(0.0, 0.60, 0.665), tail1=(0.0, 0.72, 0.53), tail2=(0.0, 0.86, 0.40), tail3=(0.0, 1.12, 0.10),
    shoulder=(0.20, -0.56, 0.80), elbow=(0.20, -0.61, 0.46), wrist=(0.19, -0.63, 0.30),
    fpaw=(0.19, -0.665, 0.10), ftoe=(0.19, -0.95, 0.02),
    hipL=(0.23, 0.41, 0.76), knee=(0.24, 0.43, 0.42), hock=(0.24, 0.54, 0.24),
    hpaw=(0.24, 0.49, 0.05), htoe=(0.24, 0.36, 0.02),
    wing=(0.13, -0.47, 1.08), wingtip=(0.30, 0.84, 0.50),
)


def dens(p):
    """The 2x density rule: a point on the straight midpoint of every span of the 7-point profile (13 points),
    so the added rings of vertices lie on the flat planes of the base section."""
    out = []
    for a, b in zip(p, p[1:]):
        out += [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)]
    return out + [p[-1]]


# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = dens([(0, 1), (0.55, 0.95), (0.9, 0.62), (1, 0.12), (0.94, -0.38), (0.62, -0.82), (0, -1)])
HAUNCH = dens([(0, 1), (0.5, 0.95), (0.84, 0.66), (0.98, 0.18), (1.04, -0.32), (0.76, -0.8), (0, -1)])   # r10: low wide haunch
CHEST = dens([(0, 1), (0.55, 0.95), (0.9, 0.62), (1, 0.1), (0.95, -0.4), (0.6, -0.85), (0, -1)])
NECK = dens([(0, 1), (0.6, 0.93), (0.93, 0.55), (1, 0.0), (0.93, -0.5), (0.6, -0.88), (0, -1)])
HEAD = dens([(0, 1), (0.45, 0.96), (0.82, 0.76), (1, 0.32), (1, -0.15), (0.78, -0.66), (0, -1)])   # r8: flat cheek plane, domed crown
BEAK = dens([(0, 1), (0.6, 0.86), (0.95, 0.42), (1, -0.08), (0.82, -0.55), (0.45, -0.9), (0, -1)])
TAIL = dens([(0, 1), (0.6, 0.85), (0.95, 0.4), (1, -0.05), (0.92, -0.45), (0.55, -0.85), (0, -1)])


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


def ax(nm, c, d, h, W, prof=TAIL):
    """A tail section from its centre and the tail's direction (y, z) in the side view."""
    l = math.hypot(*d)
    py, pz = d[1] / l, -d[0] / l
    if pz < 0:
        py, pz = -py, -pz
    return tb(nm, (c[0] + py * h, c[1] + pz * h), (c[0] - py * h, c[1] - pz * h), W, prof)


# the tail stem (centre y, z, half size), tuft end -> root; the tuft piece hides the end
TAILC = [('T0', 0.885, 0.395, 0.034), ('T1', 0.835, 0.432, 0.038), ('T2', 0.785, 0.47, 0.042),
         ('T3', 0.735, 0.515, 0.047), ('T4', 0.69, 0.565, 0.053), ('T5', 0.65, 0.62, 0.062)]


def tail_secs():
    out = []
    for i, (nm, y, z, h) in enumerate(TAILC):
        p = TAILC[max(0, i - 1)]; q = TAILC[min(len(TAILC) - 1, i + 1)]
        out.append(ax(nm, (y, z), (p[1] - q[1], p[2] - q[2]), h, h * 1.05))
    return out


# r15: the nape's top seam bulges back (sheet ruff), its stations ~0.055 apart (thin quads at the back of the neck)
# the spine loft, tail stem -> beak tip. Torso stations 0.065-0.07 apart (about one face width: near-square quads);
# the neck stations fan from the back of the ruff to the chest front; the head stations fan over the crown
SECS = [
    *tail_secs()[:-1],
    tb('T5', (0.688, 0.668), (0.635, 0.556), 0.075, TAIL),            # r7: root ring tilted back (no fold under the root)
    tb('R0t', (0.615, 0.738), (0.605, 0.568), 0.13, BODY),           # r13: wider, underside on the stem's line (knife fold)
    tb('R0', (0.575, 0.81), (0.575, 0.562), 0.19, HAUNCH),
    tb('R0b', (0.52, 0.875), (0.52, 0.555), 0.24, HAUNCH),          # rump
    tb('R1', (0.45, 0.92), (0.45, 0.555), 0.265, HAUNCH),           # hind region rear ring
    tb('R1b', (0.38, 0.945), (0.38, 0.56), 0.27, HAUNCH),
    tb('R2', (0.31, 0.96), (0.31, 0.57), 0.262, HAUNCH),
    tb('R2b', (0.24, 0.968), (0.24, 0.585), 0.24, BODY),          # hind region front ring (groin)
    tb('W0', (0.17, 0.972), (0.17, 0.592), 0.224, BODY),
    tb('W0b', (0.10, 0.976), (0.10, 0.588), 0.218, BODY),
    tb('M0', (0.03, 0.98), (0.03, 0.578), 0.216, BODY),
    tb('M0b', (-0.04, 0.985), (-0.04, 0.566), 0.218, BODY),
    tb('M1', (-0.11, 0.992), (-0.11, 0.554), 0.222, BODY),
    tb('M1b', (-0.18, 1.0), (-0.18, 0.543), 0.228, BODY),
    tb('M2', (-0.25, 1.01), (-0.25, 0.535), 0.236, BODY),
    tb('M2b', (-0.32, 1.022), (-0.32, 0.529), 0.245, BODY),
    tb('C0', (-0.38, 1.036), (-0.38, 0.525), 0.252, CHEST),
    tb('C0b', (-0.44, 1.052), (-0.44, 0.522), 0.258, CHEST),       # fore region rear ring
    tb('C1', (-0.50, 1.07), (-0.505, 0.52), 0.262, CHEST),
    tb('C1b', (-0.52, 1.115), (-0.565, 0.522), 0.262, CHEST),
    tb('C2', (-0.535, 1.165), (-0.635, 0.53), 0.258, CHEST),       # fore region front ring
    tb('C3', (-0.545, 1.22), (-0.71, 0.55), 0.254, NECK),
    tb('N0', (-0.555, 1.275), (-0.785, 0.59), 0.25, NECK),          # the ruff: chest front up to the throat
    tb('N1', (-0.57, 1.33), (-0.85, 0.665), 0.25, NECK),
    tb('N2', (-0.595, 1.38), (-0.90, 0.77), 0.245, NECK),
    tb('N3', (-0.63, 1.42), (-0.935, 0.895), 0.232, NECK),
    tb('N4', (-0.675, 1.452), (-0.952, 1.02), 0.225, HEAD),
    tb('H0', (-0.73, 1.48), (-0.96, 1.115), 0.215, HEAD),          # the head fan over the crown
    tb('H1', (-0.785, 1.50), (-0.965, 1.175), 0.208, HEAD),
    tb('H2', (-0.855, 1.487), (-0.97, 1.212), 0.196, HEAD),
    tb('H3', (-0.915, 1.452), (-0.975, 1.232), 0.172, HEAD),
    tb('H4', (-0.962, 1.405), (-0.982, 1.243), 0.118, BEAK),        # cere: the beak's root
    tb('B0', (-1.0, 1.365), (-1.0, 1.235), 0.072, BEAK),
    tb('B1', (-1.04, 1.333), (-1.03, 1.222), 0.055, BEAK),
    tb('B2', (-1.075, 1.30), (-1.06, 1.203), 0.045, BEAK),
    tb('B3', (-1.103, 1.262), (-1.085, 1.18), 0.034, BEAK),
    tb('B4', (-1.12, 1.215), (-1.098, 1.155), 0.022, BEAK),         # the hook, tipped down
]

# limb sections: (centre xyz, rx, ry); a rounded box (superellipse p 3), flat front, back and sides
FORE = [((0.20, -0.595, 0.55), 0.112, 0.09), ((0.20, -0.603, 0.465), 0.104, 0.094), ((0.20, -0.61, 0.395), 0.098, 0.094),
        ((0.198, -0.618, 0.35), 0.092, 0.09),                                       # feathered trouser
        ((0.192, -0.628, 0.295), 0.068, 0.062), ((0.19, -0.643, 0.215), 0.062, 0.056),   # scaled tarsus
        ((0.19, -0.66, 0.135), 0.064, 0.058)]
# r11: thigh centre in (x 0.20 -> 0.24 at the hock) under the wider haunch, so the thigh is the body's side
# r9: the lion hind leg read off the sheet's near leg: a deep thigh (buttock to stifle), stifle forward, hock back
HIND = [((0.225, 0.44, 0.49), 0.11, 0.135),        # r17-20: first ring low, inner side out (x 0.115), back in line with
        ((0.225, 0.455, 0.43), 0.102, 0.128),      # R0: the groin and buttock slope into the leg (no 140-150 deg crease)
        ((0.23, 0.475, 0.37), 0.092, 0.108), ((0.235, 0.50, 0.31), 0.082, 0.095),
        ((0.24, 0.525, 0.245), 0.072, 0.085), ((0.24, 0.515, 0.165), 0.064, 0.07),
        ((0.24, 0.50, 0.095), 0.072, 0.088), ((0.24, 0.48, 0.04), 0.088, 0.115), ((0.24, 0.47, 0.0), 0.088, 0.122)]
SUPER = 3.0
TRANS = 0.45          # the transition ring: this far from the flank region toward the first leg section


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def role_pos(sec, u, s):
    """(u, s) on the region grid (u +1 = the flank's upper edge = the leg's outer side, s +1 = rear) onto the
    section's rounded box."""
    c, rx, ry = sec[0], sec[1], sec[2]
    e = (abs(u) ** SUPER + abs(s) ** SUPER) ** (1.0 / SUPER) if (u or s) else 1.0
    m = max(abs(u), abs(s))
    f = m / e if e > 0 else 0.0
    return Vector((c[0] + u * f * rx, c[1] + s * f * ry, c[2]))


def grow(bm, faces, roles, secs, trans=TRANS):
    first = True
    for sec in secs:
        keyed = [(o.co.copy(), rl) for o, rl in roles.items()]       # the region's interior verts go with extrude
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            new[v] = min(keyed, key=lambda q: (q[0] - v.co).length)[1]
        for v, (u, s) in new.items():
            tgt = role_pos(sec, u, s)
            v.co = v.co.lerp(tgt, trans) if first else tgt
        first = False
        faces, roles = r['faces'], new
    return faces, roles


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


def region(rings, spans, i0, S, j0, F):
    """The flank region of S spans (rings i0..i0+S) x F faces (points j0..j0+F) and its (u, s) roles."""
    faces = [spans[i0 + a][j0 + b] for a in range(S) for b in range(F)]
    roles = {}
    for a in range(S + 1):
        for b in range(F + 1):
            roles[rings[i0 + a][j0 + b]] = (1 - 2 * b / F, 1 - 2 * a / S)
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    ends = [cap(bm, rings[0]), cap(bm, rings[-1])]
    bmesh.ops.poke(bm, faces=ends)
    recalc_normals(bm)
    f, r = region(rings, spans, idx['C1'], 3, 8, 3)      # r2: C1..C3, centred over the foreleg top
    grow(bm, f, r, FORE)
    f, r = region(rings, spans, idx['R0'], 4, 8, 3)      # r22: R0..R2 (4 spans = the thigh's full depth, 14-vertex rings)
    grow(bm, f, r, HIND)
    snap_seam(bm)
    return object_from_bm('body', bm)


import parts as PT


def eye_face_centre():
    H2, H3 = P('H2'), P('H3')
    return (H2[6] + H2[7] + H3[6] + H3[7]) / 4


def stage2(k, body):
    bm = edit(body)
    recalc_normals(bm)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    H2, H3 = P('H2'), P('H3')
    # the eye face (H2-H3, points 6-7) opened up along the ring so a round lens fits one clean socket
    for R in (H2, H3):
        a, b = vert_near(bm, R[6]), vert_near(bm, R[7])
        d = (R[5] - R[6]) * 0.45
        e = (R[8] - R[7]) * 0.45
        a.co += d; b.co += e
    ec = sum((vert_near(bm, R[j]).co for R in (H2, H3) for j in (6, 7)), Vector()) / 4
    f = face_near(bm, ec)
    fn = f.normal.copy()
    with topo(bm, k.log, 'inset', 'eye socket: one inset in the opened cheek face under the brow'):
        inner = inset(bm, [f], 0.2, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.007)                    # s3 r2: shallower socket (lens hidden from the side)
    # brow: the ring point over the eye out and forward (the eagle's supraorbital ridge)
    for R in (H2, H3):
        move([vert_near(bm, R[5])], (0.012, -0.008, 0.004))
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'tan': '#d29e60', 'cream': '#e9d6b0', 'white': '#efeae0', 'yellow': '#e2ad38', 'brown': '#6a4a33',
       'dark': '#2c2420', 'amber': '#b8741f'}


def white_zone(c):
    if abs(c.x) > 0.17 and c.z < 0.82:
        return False                                      # s3 r4: the bib stays on the chest, the leg tops tan
    return c.z > 0.5 and (c.y + 0.62) < (c.z - 0.6) * 0.3


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    if y < -0.975 or (y < -0.955 and z > 1.25 and x < 0.1):
        return 'yellow'                                   # beak and cere
    if white_zone(c):
        return 'white'                                    # head, ruff and bib
    if y < -0.45 and z < 0.31:
        return 'yellow'                                   # scaled tarsus
    if y > 0.2 and z < 0.115 and x > 0.1:
        return 'cream'                                    # lion paws
    if -0.5 < y < 0.3 and n.z < -0.55 and z < 0.66 and x < 0.17:
        return 'cream'                                    # belly
    return 'tan'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 5 for k_ in range(10)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, B = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    for j in range(10):
        a, b = j, (j + 1) % 10
        bm.faces.new([B, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


# the folded wing, x >= 0: key stations along the wing (y, inner-top edge E0 (x, z), bulge E2, lower edge E4);
# the root station sits inside the shoulder, the rest rides over the back and flank, the tip hangs past the rump
WINGK = [(-0.60, (0.10, 1.07), (0.19, 1.02), (0.21, 0.93)),          # s3 r3: root deep in the ruff (no box end showing)
         (-0.44, (0.14, 1.18), (0.30, 1.12), (0.32, 0.93)),
         (-0.25, (0.09, 1.14), (0.33, 1.08), (0.35, 0.85)),
         (0.00, (0.06, 1.07), (0.335, 1.02), (0.355, 0.79)),
         (0.25, (0.07, 1.025), (0.325, 0.95), (0.345, 0.72)),
         (0.48, (0.10, 0.99), (0.305, 0.88), (0.325, 0.65)),
         (0.68, (0.15, 0.86), (0.28, 0.75), (0.295, 0.58)),
         (0.86, (0.235, 0.60), (0.255, 0.54), (0.262, 0.48))]
WT = 0.042            # slab thickness (membrane check: >= max(6 mm, 0.4 % of 2.25 m) = 9 mm)
WN = 15               # stations along the wing


def wing_bm():
    """A closed feathered slab: per station a 5-point arc (inner-top edge -> bulge -> lower edge) offset +-WT/2 along
    the outward direction; the lower edge zig-zags (every other station 3.5 cm lower: the primary tips).
    Returns the bmesh and, per face, 'cov' (upper-front coverts) or 'prim' (flight feathers)."""
    bm = bmesh.new()
    ys = [q[0] for q in WINGK]

    def key(y):
        for a, b in zip(WINGK, WINGK[1:]):
            if a[0] <= y <= b[0]:
                t = (y - a[0]) / (b[0] - a[0])
                return [tuple(a[i][j] + (b[i][j] - a[i][j]) * t for j in range(2)) for i in (1, 2, 3)]
        return [WINGK[-1][i] for i in (1, 2, 3)]
    rings_, labs = [], []
    for i in range(WN):
        t = i / (WN - 1)
        y = ys[0] + (ys[-1] - ys[0]) * t
        e0, e2, e4 = key(y)
        drop = 0.035 if (i % 2 == 1 and 2 <= i <= WN - 2) else 0.0
        e4 = (e4[0] + drop * 0.15, e4[1] - drop)
        e1 = ((e0[0] + e2[0]) / 2 + 0.03, (e0[1] + e2[1]) / 2 + 0.03)
        e3 = ((e2[0] + e4[0]) / 2 + 0.015, (e2[1] + e4[1]) / 2)
        arc = [e0, e1, e2, e3, e4]
        th = WT * (1.0 - 0.45 * t)
        pts_o, pts_i = [], []
        for (x, z) in arc:
            d = Vector((x, 0.0, z - 0.80)).normalized()
            p = Vector((x, y, z))
            pts_o.append(p + d * th / 2)
            pts_i.append(p - d * th / 2)
        rings_.append([bm.verts.new(p) for p in pts_o + list(reversed(pts_i))])
    for a, b in zip(rings_, rings_[1:]):
        bridge(bm, a, b, closed=True)
    c0 = bm.faces.new(list(reversed(rings_[0])))
    c1 = bm.faces.new(rings_[-1])
    bmesh.ops.poke(bm, faces=[c0, c1])
    # s4 r6: the covert layer, a second closed slab laid 6 mm over the upper-front of the wing (tan), its lower edge
    # zig-zagging station to station (covert tips) and tapering out at the 9th station; root inside the ruff too.
    # Replaces the stepped colour border on the single slab (the orbit read it as a tetris pattern).
    nf = len(bm.faces)
    crings = []
    NC = 9
    for i in range(NC):
        t = i / (WN - 1)
        y = ys[0] + (ys[-1] - ys[0]) * t
        e0, e2, e4 = key(y)
        e1 = ((e0[0] + e2[0]) / 2 + 0.03, (e0[1] + e2[1]) / 2 + 0.03)
        e3 = ((e2[0] + e4[0]) / 2 + 0.015, (e2[1] + e4[1]) / 2)
        f_ = 0.85 if i % 2 == 0 else 0.3
        ec = (e2[0] + (e3[0] - e2[0]) * f_, e2[1] + (e3[1] - e2[1]) * f_)
        arc = [e0, e1, e2, ec]
        if i == NC - 1:                                   # the last station closes onto the upper span
            arc = [e0, (e0[0] * 0.6 + e1[0] * 0.4, e0[1] * 0.6 + e1[1] * 0.4), (e0[0] * 0.3 + e1[0] * 0.7, e0[1] * 0.3 + e1[1] * 0.7), e1]
        th = WT * (1.0 - 0.45 * t)
        lo, hi = [], []
        for (x, z) in arc:
            d = Vector((x, 0.0, z - 0.80)).normalized()
            p = Vector((x, y, z)) + d * (th / 2 + 0.006)
            lo.append(p); hi.append(p + d * 0.022)
        crings.append([bm.verts.new(p) for p in hi + list(reversed(lo))])
    for a, b in zip(crings, crings[1:]):
        bridge(bm, a, b, closed=True)
    c2 = bm.faces.new(list(reversed(crings[0])))
    c3 = bm.faces.new(crings[-1])
    bmesh.ops.poke(bm, faces=[c2, c3])
    bm.faces.ensure_lookup_table()
    cov = {bm.faces[q] for q in range(nf, len(bm.faces))}
    recalc_normals(bm)
    bm.faces.index_update()
    return bm, {f.index for f in cov if f.is_valid}


def claw(bm, h, d, lead):
    x0 = h.x
    yr, ym, yt = h.y + 0.014, h.y - 0.01 - lead * 0.5, h.y - 0.03 - lead
    xm, xt = x0 + d * 0.1, x0 + d * 0.2
    rows = [[(x0 - 0.014, yr, 0.008), (x0 + 0.014, yr, 0.008), (x0 + 0.014, yr, 0.038), (x0 - 0.014, yr, 0.038)],
            [(xm - 0.0125, ym, 0.005), (xm + 0.0125, ym, 0.005), (xm + 0.0115, ym, 0.031), (xm - 0.0115, ym, 0.031)],
            [(xt - 0.0098, yt, 0.003), (xt + 0.0098, yt, 0.003), (xt + 0.0098, yt, 0.0225), (xt - 0.0098, yt, 0.0225)]]
    # detail pass 10-23: a blunt chunky tip (>= 19.5 mm; floor 18.2 mm), the tip ring was 10 x 7 mm (t 17.0 mm)
    R = [[bm.verts.new(p) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in ((R[0], R[1]), (R[1], R[2])):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[2])


def stage3(k, body):
    paint(body, PAL, body_rule)
    # night 10-23 border pass (owner 10-21 approved kit/smooth_borders, as frog r17): anti-stair cuts + tangential relax
    smooth_borders(body, k=k, iters=8)
    bm0 = edit(body); tree = BVHTree.FromBMesh(bm0); bm0.free()
    pieces = []
    # eye: a round amber lens with a dark pupil, part in the socket, part proud
    ec = eye_face_centre()
    c, n, _i, _d = tree.find_nearest(ec)
    n = n if n.x > 0 else -n
    look = (n + Vector((0.0, -0.15, 0.0))).normalized()      # s3 r1: less forward (side 0.29)
    bm = bmesh.new()
    lens(bm, c + n * 0.003, look, 0.022, 0.012)
    eye = object_from_bm('eye', bm)
    paint(eye, {'amber': PAL['amber'], 'dark': PAL['dark']},
          lambda c_, n_, i: 'dark' if ((c_ - c) - look * (c_ - c).dot(look)).length < 0.0095 and n_.dot(look) > 0.5 else 'amber')
    pieces.append(eye)
    # wings
    wbm, wcov = wing_bm()
    wing = object_from_bm('wing', wbm)
    paint(wing, {'tan': PAL['tan'], 'brown': PAL['brown']}, lambda c_, n_, i: 'tan' if i in wcov else 'brown')
    pieces.append(wing)
    # eagle feet on the tarsus ends (left, right)
    for sd in (1, -1):
        (cx, cy, cz), rx, ry = FORE[-1]
        ft = PT.bird_foot((cx * sd, cy, cz), toe_length=0.2, forward=(0, -1, 0), up=(0, 0, 1), side=sd, height=cz,
                          radius=0.052, spread=24.0, hallux=0.6, talon_len=0.55, name='foot' + ('L' if sd > 0 else 'R'),
                          mats={'scale': 'yellow', 'claw': 'dark'})
        pieces.append(ft)
    # lion claws on the hind paw fronts
    bm = bmesh.new()
    (cx, cy, _), rx, ry = HIND[-1]
    for d in (-0.055, -0.018, 0.018, 0.055):
        o = Vector((cx + d, cy - ry - 0.2, 0.02))
        hit = tree.ray_cast(o, Vector((0, 1, 0)), 0.4)[0]
        h = hit if hit is not None else Vector((cx + d, cy - ry * 0.8, 0.02))
        claw(bm, h, d, 0.004 if abs(d) < 0.03 else 0.0)
    claws = object_from_bm('claws', bm)
    paint(claws, {'dark': PAL['dark']}, lambda c_, n_, i: 'dark')
    pieces.append(claws)
    # the lion tail tuft over the stem end
    y0, z0 = TAILC[2][1], TAILC[2][2]          # s3 r5: the sheet's big brush (0.45 m, 0.24 wide), not a small knob
    tuft = PT.tail_tuft((0.0, y0, z0), length=0.46, radius=0.12, forward=(0, 0.68, -0.73), up=(0, 0.73, 0.68),
                        kind='brush', tiers=3, sides=6, name='tuft', mats={'fur': 'brown', 'fur_under': 'brown', 'fur_tip': 'brown'})
    pieces.append(tuft)
    return pieces


def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('foot.L', J['wrist'], J['fpaw'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
         ('hfoot.L', J['hock'], J['hpaw'], 'shin.L', True),
         ('toe.L', J['hpaw'], J['htoe'], 'hfoot.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_foot'):
            bind(p, rig, bone='foot.' + p.name[-1])
        elif 'tuft' in p.name:
            bind(p, rig, bone='tail2')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, 6), 'tail1': (0, 0, 5)},
                       24: {'head': (0, 0, -4), 'tail1': (0, 0, 0)},
                       36: {'chest': (1.5, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 0, -6), 'tail1': (0, 0, -5)}, 48: {}})
    A = 14
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 4)},
        7: {'forearm.R': (-24, 0, 0), 'foot.R': (-18, 0, 0), 'shin.L': (-16, 0, 0), 'hfoot.L': (20, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -4)},
        19: {'forearm.L': (-24, 0, 0), 'foot.L': (-18, 0, 0), 'shin.R': (-16, 0, 0), 'hfoot.R': (20, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 4)}})
    # attack: rear back, then a lunging beak strike with one talon raised
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (-10, 0, 0), 'chest': (4, 0, 0), 'head': (-8, 0, 0), 'tail1': (0, 0, 6)},
        16: {'neck': (14, 0, 0), 'chest': (-6, 0, 0), 'head': (12, 0, 0), 'upperarm.L': (-22, 0, 0), 'forearm.L': (30, 0, 0),
             'tail1': (0, 0, -6)},
        20: {'neck': (12, 0, 0), 'chest': (-6, 0, 0), 'head': (16, 0, 0), 'upperarm.L': (-12, 0, 0), 'forearm.L': (16, 0, 0)},
        24: {'neck': (8, 0, 0), 'chest': (-3, 0, 0), 'head': (5, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.03, 0)}, 16: {'hips': (0, -0.05, 0)}, 20: {'hips': (0, -0.05, 0)},
             24: {'hips': (0, -0.02, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
