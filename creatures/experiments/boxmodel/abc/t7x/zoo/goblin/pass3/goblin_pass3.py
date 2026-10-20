import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# goblin (biped), t7 hand box-model: one spine loft of 6-vertex half rings runs pelvis (crotch) -> crown, the
# rings lying flat (back seam -> front seam). Legs are 2-face regions of the crotch-hip span extruded down as
# horizontal hexagons, arms 2-face regions of the chest side extruded out-down, the ears 1-face extrusions of the
# skull side, the hooked nose a 1-face extrusion of the face front (its seam wall removed: the mirror closes it).
# Coordinates from blueprint.json (refs.py, height 1.0 m); the sheet's top view is unreliable and is not used.
META = dict(creature='goblin', model='opus', stage1_tris=(1200, 3000), total_tris=(2600, 4800),
            closeups=[('head', (0.0, -0.06, 0.86), 0.24, 'hero'),
                      ('hand', (0.27, -0.06, 0.26), 0.10, 'hero'),
                      ('foot', (0.14, -0.05, 0.04), 0.11, 'hero'),
                      ('vest and loincloth', (0.06, -0.06, 0.48), 0.24, 'hero')])

# skeleton (x >= 0 half; .L on +X), read off reference/side.png + front.png
J = dict(
    hips=(0.0, 0.0, 0.30), spine=(0.0, -0.01, 0.45), chest=(0.0, -0.005, 0.58), neck=(0.0, 0.0, 0.68),
    head=(0.0, -0.01, 0.76), crown=(0.0, -0.03, 0.98),
    ear=(0.13, 0.04, 0.86), eartip=(0.315, 0.11, 0.93),
    shoulder=(0.14, 0.0, 0.61), elbow=(0.215, 0.04, 0.47), wrist=(0.252, -0.035, 0.33), hand=(0.243, -0.08, 0.215),
    hipL=(0.075, 0.0, 0.29), knee=(0.105, 0.012, 0.165), ankle=(0.125, 0.055, 0.07), toe=(0.14, -0.13, 0.02),
)

# half-ring profiles, back seam -> front seam: (x as a fraction of W, h as a fraction of the half depth)
TORSO = [(0, 1), (0.7, 0.9), (1, 0.1), (0.85, -0.6), (0.45, -0.92), (0, -1)]
NECK = [(0, 1), (0.75, 0.75), (1, 0.0), (0.8, -0.65), (0.4, -0.95), (0, -1)]
HEADP = [(0, 1), (0.75, 0.85), (1, 0.15), (0.85, -0.55), (0.45, -0.9), (0, -1)]
CROWN = [(0, 1), (0.7, 0.8), (1, 0.1), (0.8, -0.6), (0.45, -0.9), (0, -1)]


def dense(prof, bulge=1.04):
    """Density pass 3: 6 -> 10 vertices per half ring. A rounding vertex goes into each of the first four spans
    (back seam -> lower front): the Catmull-Rom midpoint (the seam mirrored for the end tangent), pushed out a
    little so the masses read round. The front-most span (belly / chin plane) stays one flat face."""
    q = [(-prof[1][0], prof[1][1])] + list(prof)
    out = []
    for i in range(len(prof) - 1):
        out.append(prof[i])
        if i < 4:
            p0, p1, p2, p3 = q[i], q[i + 1], q[i + 2], q[min(i + 3, len(q) - 1)]
            m = [0.5625 * (p1[k] + p2[k]) - 0.0625 * (p0[k] + p3[k]) for k in range(2)]
            out.append((m[0] * bulge, m[1] * bulge))
    out.append(prof[-1])
    return out


TORSO, NECK, HEADP, CROWN = dense(TORSO), dense(NECK), dense(HEADP), dense(CROWN)


def tb(nm, back, front, W, prof):
    """A ring from its back and front seam points (y, z) read off reference/side.png, W from the front view."""
    (yt, zt), (yb, zb) = back, front
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


# the spine loft, crotch -> crown
SECS = [
    tb('R0', (0.035, 0.25), (-0.06, 0.25), 0.045, TORSO),     # crotch
    tb('R1', (0.085, 0.33), (-0.10, 0.33), 0.12, TORSO),      # hips
    tb('R1b', (0.082, 0.375), (-0.12, 0.375), 0.122, TORSO),  # hip -> belly round-over (trace front -0.128)
    tb('R2', (0.075, 0.42), (-0.125, 0.42), 0.115, TORSO),    # pot belly
    tb('R2b', (0.072, 0.455), (-0.114, 0.455), 0.108, TORSO), # belly tuck (trace front -0.110)
    tb('R3', (0.07, 0.49), (-0.105, 0.49), 0.10, TORSO),      # waist
    tb('R3b', (0.072, 0.53), (-0.10, 0.53), 0.11, TORSO),     # ribs (trace front -0.105)
    tb('R4', (0.075, 0.565), (-0.095, 0.565), 0.12, TORSO),   # chest
    tb('R5', (0.07, 0.645), (-0.08, 0.645), 0.13, TORSO),     # shoulders
    tb('R5b', (0.064, 0.668), (-0.071, 0.66), 0.12, TORSO),   # shoulder round-over
    tb('R6', (0.055, 0.69), (-0.06, 0.675), 0.095, TORSO),    # shoulder top
    tb('R6b', (0.052, 0.725), (-0.056, 0.688), 0.075, NECK),  # neck base (trace front 0.066-0.087)
    tb('N0', (0.045, 0.76), (-0.05, 0.70), 0.055, NECK),      # neck
    tb('N0b', (0.058, 0.783), (-0.10, 0.699), 0.07, NECK),    # throat under the jaw
    tb('H0', (0.075, 0.80), (-0.17, 0.705), 0.085, HEADP),    # jaw / chin
    tb('H0b', (0.089, 0.815), (-0.197, 0.73), 0.10, HEADP),   # chin -> mouth (trace front -0.195)
    tb('H1', (0.10, 0.83), (-0.215, 0.76), 0.115, HEADP),     # mouth
    tb('H1a', (0.105, 0.84), (-0.218, 0.788), 0.121, HEADP),  # upper lip
    tb('H1b', (0.11, 0.85), (-0.215, 0.815), 0.125, HEADP),   # nose root
    tb('H2', (0.115, 0.895), (-0.20, 0.885), 0.13, HEADP),    # brow / eye line
    tb('H2b', (0.11, 0.925), (-0.172, 0.92), 0.124, CROWN),   # forehead (trace front -0.171)
    tb('H3', (0.095, 0.95), (-0.135, 0.95), 0.13, CROWN),    # skull
    tb('H3b', (0.078, 0.972), (-0.11, 0.972), 0.11, CROWN),   # dome round-over (trace -0.11 / 0.085)
    tb('H4', (0.05, 0.99), (-0.085, 0.99), 0.085, CROWN),    # crown
]

# limb sections: (centre, r1, r2); hexagon corners (a, b) at c + e1 a r1 + e2 b r2
HEX = {'um': (1, 0), 'ub': (0.5, 1), 'uf': (0.5, -1), 'lb': (-0.5, 1), 'lf': (-0.5, -1), 'lm': (-1, 0)}
# density pass 3: 10-vertex limb rings (a 4-face root strip) and 11-12 stations: thigh -> knee -> calf -> ankle ->
# heel -> ball, shoulder -> biceps -> elbow -> forearm swell -> wrist; new radii read off the front/side leg and arm widths
LEG = [((0.09, 0.0, 0.215), 0.05, 0.062), ((0.098, 0.006, 0.19), 0.046, 0.054), (J['knee'], 0.042, 0.046),
       ((0.11, 0.03, 0.142), 0.04, 0.046), ((0.115, 0.04, 0.12), 0.037, 0.041),
       ((0.12, 0.048, 0.097), 0.033, 0.037), ((0.125, 0.055, 0.075), 0.03, 0.034), ((0.133, 0.03, 0.052), 0.046, 0.066),
       ((0.14, -0.01, 0.035), 0.062, 0.098), ((0.14, -0.013, 0.017), 0.066, 0.104), ((0.14, -0.015, 0.0), 0.066, 0.105)]
ARM = [((0.168, 0.01, 0.588), 0.048, 0.05), ((0.178, 0.018, 0.56), 0.048, 0.05), ((0.19, 0.026, 0.53), 0.046, 0.048), (J['elbow'], 0.042, 0.042),
       ((0.232, 0.014, 0.425), 0.05, 0.053), ((0.237, 0.005, 0.40), 0.052, 0.055), ((0.245, -0.015, 0.365), 0.047, 0.049),
       (J['wrist'], 0.04, 0.04), ((0.255, -0.044, 0.307), 0.044, 0.052), ((0.255, -0.055, 0.28), 0.046, 0.06), ((0.245, -0.08, 0.228), 0.037, 0.046)]
EAR_ROOT, EAR_TIP = Vector((0.125, 0.035, 0.85)), Vector(J['eartip'])
EAR = [(0.12, -0.015, 0.08, 0.02), (0.5, 0.0, 0.056, 0.018), (1.0, 0.0, 0.006, 0.004)]   # (t, dz, wide, thin)
NOSE = [((-0.24, 0.818), 0.032, 0.035), ((-0.254, 0.794), 0.024, 0.026), ((-0.258, 0.774), 0.012, 0.014)]


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


def leg_frames():
    return [(Vector(c), Vector((1, 0, 0)), Vector((0, 1, 0)), r1, r2) for c, r1, r2 in LEG]


def arm_frames():
    cs = [Vector(J['shoulder'])] + [Vector(c) for c, _, _ in ARM]
    out = []
    for i, (c, r1, r2) in enumerate(ARM):
        d = (cs[min(i + 2, len(cs) - 1)] - cs[i]).normalized()
        e2 = Vector((0, 1, 0)); e2 = (e2 - d * e2.dot(d)).normalized()
        out.append((Vector(c), d.cross(e2).normalized(), e2, r1, r2))
    return out


def ear_frames():
    d = (EAR_TIP - EAR_ROOT).normalized()
    e1 = Vector((0, 0, 1)); e1 = (e1 - d * e1.dot(d)).normalized()
    e2 = d.cross(e1).normalized()
    out = []
    for t, dz, wide, thin in EAR:
        c = EAR_ROOT.lerp(EAR_TIP, t) + Vector((0, 0, dz))
        out.append((c, e1, e2, wide, thin))
    return out


def ellipse_roles(verts, fr):
    """Roles (cos t, sin t) for a root loop of n vertices: their order round the frame axes, spread evenly, the vertex
    nearest +e1 at t = 0 (so HEX['um'] = (1, 0) is a real corner and the joint cuts find their edge)."""
    e1, e2 = fr[1], fr[2]
    cen = sum((v.co for v in verts), Vector()) / len(verts)
    pr = [((v.co - cen).dot(e1), (v.co - cen).dot(e2)) for v in verts]
    s1, s2 = max(abs(a) for a, _ in pr) or 1, max(abs(b) for _, b in pr) or 1
    ang = [math.atan2(b / s2, a / s1) for a, b in pr]
    order = sorted(range(len(verts)), key=lambda i: ang[i])
    r0 = order.index(min(range(len(verts)), key=lambda i: abs(ang[i])))
    n = len(verts)
    out = {}
    for rk, i in enumerate(order):
        t = 2 * math.pi * (rk - r0) / n
        out[verts[i]] = (round(math.cos(t), 6), round(math.sin(t), 6))
    return out


def corner(fr, ab):
    c, e1, e2, r1, r2 = fr
    return c + e1 * ab[0] * r1 + e2 * ab[1] * r2


def grow(bm, faces, roles, frames):
    """Extrude a face region frame by frame; each new vertex keeps the role (a, b) of the vertex it came from."""
    for fr in frames:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, ab in new.items():
            v.co = corner(fr, ab)
        faces, roles = r['faces'], new
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(nm, frames):
        i = idx[nm]                 # span between ring i (lower) and ring i+1 (upper)
        lo, up = rings[i], rings[i + 1]
        # old columns 1-2 = new columns 2-5; roles spread evenly round the root loop in its own order, the upper
        # middle vertex at (1, 0) (HEX 'um'), the back side (+e2) next
        seq = [up[4], up[3], up[2], lo[2], lo[3], lo[4], lo[5], lo[6], up[6], up[5]]
        roles = {v: (round(math.cos(2 * math.pi * k / 10), 6), round(math.sin(2 * math.pi * k / 10), 6))
                 for k, v in enumerate(seq)}
        grow(bm, spans[i][2:6], roles, frames)

    limb('R0', leg_frames())
    limb('R4', arm_frames())
    # ear: column 1 of the nose-root -> brow span; roles from its own frame
    i = idx['H1b']
    lo, up = rings[i], rings[i + 1]
    fr = ear_frames()
    roles = {v: (a * 0.95, b * 1.15) for v, (a, b) in ellipse_roles(lo[2:5] + up[2:5], fr[0]).items()}
    grow(bm, spans[i][2:4], roles, fr)
    # nose: column 8 (front, on the seam) of the same span, out and down to a hooked tip
    f = spans[i][8]
    roles = {up[9]: (0, 1), lo[9]: (0, -1), up[8]: (1, 0.4), lo[8]: (1, -0.4)}
    faces = [f]
    prev = Vector((0.0, (lo[5].co.y + up[5].co.y) / 2, (lo[5].co.z + up[5].co.z) / 2))
    for (cy, cz), hh, rx in NOSE:
        c = Vector((0.0, cy, cz))
        d = (c - prev).normalized()
        upv = Vector((0.0, -d.z, d.y))
        if upv.z < 0:
            upv = -upv
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (ax, bh) in new.items():
            v.co = c + Vector((ax * rx, 0, 0)) + upv * bh * hh
        seam_walls = [g for g in r['sides'] if all(abs(w.co.x) < 1e-6 for w in g.verts)]
        bmesh.ops.delete(bm, geom=seam_walls, context='FACES')
        faces, roles, prev = r['faces'], new, c
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
def eye_face_centre():
    A, B_ = P('H1b'), P('H2')
    return (A[7] + A[8] + B_[7] + B_[8]) / 4      # old column 3 -> its front half (column 7)


def keep_eye(c):
    ec0 = eye_face_centre()
    return abs(abs(c.x) - ec0.x) < 0.035 and abs(c.y - ec0.y) < 0.035 and abs(c.z - ec0.z) < 0.04


def stage2(k, body):
    """Joint rings (elbow, knee, wrist, ankle, waist, neck), the eye socket, the brow and the jaw plane."""
    k.meta['keep_valleys'] = keep_eye
    bm = edit(body)
    recalc_normals(bm)
    mid = lambda a, b: tuple((a + b) / 2)
    af, lf = arm_frames(), leg_frames()
    cuts = [('elbow ring: the elbow bend', mid(corner(af[3], HEX['um']), corner(af[4], HEX['um']))),
            ('shoulder ring: the arm swing', mid(corner(af[1], HEX['um']), corner(af[2], HEX['um']))),
            ('wrist ring: the wrist bend', mid(corner(af[7], HEX['um']), corner(af[8], HEX['um']))),
            ('knee ring: the knee bend', mid(corner(lf[2], HEX['um']), corner(lf[3], HEX['um']))),
            ('hip ring: the leg swing', mid(corner(lf[0], HEX['um']), corner(lf[1], HEX['um']))),
            ('waist ring: the spine bend', mid(P('R2b')[0], P('R3')[0])),
            ('neck ring: the head nod', mid(P('N0b')[0], P('H0')[0]))]
    for why, p_ in cuts:
        with k.topo(bm, 'loop', why):
            loopcut(bm, edge_near(bm, p_), t=0.5)
    ec0 = eye_face_centre()
    f = face_near(bm, ec0)
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a ring in the eye face, its floor pushed in'):
        inner = inset(bm, [f], 0.26, 0.0)
    move(list(inner[0].verts), -fn * 0.009)
    H2, H0 = P('H2'), P('H0')
    move([vert_near(bm, H2[6]), vert_near(bm, H2[7])], (0.006, -0.01, 0.004))   # brow corner forward / out over the eye
    move([vert_near(bm, H0[j]) for j in (6, 7, 8)], (0.0, -0.008, 0.0))         # a firmer jaw corner
    recalc_normals(bm)
    commit(body, bm)
    bm.free()
    ortho_views(k.path('stage2'), k.path('blueprint.json'), objs=[body])


# ---------------------------------------------------------------- stage 3
PAL = {'skin': '#a3b56c', 'dark': '#4a6644', 'inner': '#c99a7c', 'leather': '#6b4a36', 'rope': '#b49a68',
       'eye': '#d9a62a', 'black': '#231c1a'}


def ear_t(c):
    d = EAR_TIP - EAR_ROOT
    return (Vector((abs(c.x), c.y, c.z)) - EAR_ROOT).dot(d) / d.length_squared


def body_rule(c, n, i):
    x = abs(c.x)
    if x > 0.135 and c.z > 0.76 and c.y > -0.05:
        t = ear_t(c)
        if t > 0.72:
            return 'dark'                                   # darker green ear tip
        e2 = ear_frames()[0][2]
        if t > 0.1 and Vector((abs(n.x), n.y, n.z)).dot(e2) > 0.5:
            return 'inner'                                  # warm inner ear on the forward wall
    return 'skin'


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


def box_chain(bm, rows):
    """A closed tube through rows of 4 points each (a finger, a toe, a rope segment): end caps + side quads."""
    R = [[bm.verts.new(Vector(p)) for p in r] for r in rows]
    bm.faces.new(list(reversed(R[0])))
    for a, b in zip(R, R[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(R[-1])


def sq(c, u, w, su, sw):
    return [c - u * su - w * sw, c + u * su - w * sw, c + u * su + w * sw, c - u * su + w * sw]


def shell_patch(bm, quads, drop=(), inner=0.006, outer=0.012):
    """A solid leather panel on a patch of loft quads (lists of 4 points, outward winding): every corner offset
    along its patch normal, -inner and +outer, so the panel is rooted in the skin along its whole rim (it crosses
    the surface once). Corners at x = 0 stay on the seam (the mirror closes the panel across the back)."""
    keyf = lambda p: (round(p.x, 5), round(p.y, 5), round(p.z, 5))
    nrm, pos = {}, {}
    for q in quads:
        fn = (q[1] - q[0]).cross(q[2] - q[0]) + (q[2] - q[0]).cross(q[3] - q[0])
        for p in q:
            kk = keyf(p)
            nrm[kk] = nrm.get(kk, Vector()) + fn
            pos[kk] = p.copy()
    for kk, d in drop:
        pos[kk] = pos[kk] + Vector(d)
    I, O = {}, {}
    for kk, p in pos.items():
        n = nrm[kk].normalized()
        if abs(p.x) < 1e-6:
            n.x = 0.0; n = n.normalized()
        I[kk] = bm.verts.new(p - n * inner); O[kk] = bm.verts.new(p + n * outer)
    edges = {}
    for q in quads:
        ks = [keyf(p) for p in q]
        bm.faces.new([O[kk] for kk in ks])
        bm.faces.new([I[kk] for kk in reversed(ks)])
        for j in range(4):
            e = (ks[j], ks[(j + 1) % 4])
            edges[e] = edges.get(e, 0) + 1
    for (a, b), cnt in edges.items():
        if (b, a) in edges:
            continue
        if abs(pos[a].x) < 1e-6 and abs(pos[b].x) < 1e-6:
            continue                                    # seam edge: the mirror closes it
        bm.faces.new([O[b], O[a], I[a], I[b]])


def vest(tree):
    """The ragged vest: a band round the waist-chest span (open at the front), a back strip and a front strip up
    over the shoulder spans (the arm comes out between them); its hem hangs in points."""
    R3, R3b, R4, R5, R5b, R6 = P('R3'), P('R3b'), P('R4'), P('R5'), P('R5b'), P('R6')
    quads = []
    band, strip = tuple(range(8)), (0, 1, 6, 7)     # old columns 0-3 and 0, 3 on the 10-vertex rings
    for lo, up, cols in ((R3, R3b, band), (R3b, R4, band), (R4, R5, strip), (R5, R5b, strip), (R5b, R6, strip)):
        for j in cols:
            quads.append([lo[j + 1], lo[j], up[j], up[j + 1]] if False else [lo[j], lo[j + 1], up[j + 1], up[j]])
    # outward winding check: the first quad's normal must point away from the spine
    q = quads[0]
    n = (q[1] - q[0]).cross(q[2] - q[0])
    c = sum(q, Vector()) / 4
    if n.dot(c - Vector((0, 0, c.z))) < 0:
        quads = [list(reversed(q)) for q in quads]
    keyf = lambda p: (round(p.x, 5), round(p.y, 5), round(p.z, 5))
    drop = [(keyf(R3[2]), (0, 0, -0.03)), (keyf(R3[6]), (0, 0, -0.028))]
    bm = bmesh.new()
    shell_patch(bm, quads, drop=drop)
    return bm


def ray_y(tree, x, z, from_front=True):
    o = Vector((x, -0.6 if from_front else 0.6, z))
    hit = tree.ray_cast(o, Vector((0, 1 if from_front else -1, 0)), 1.2)[0]
    return hit.y if hit is not None else None


def flap(bm, tree, front=True):
    """A loincloth flap: rooted in the belly (or rump) under the belt, hanging free over the thighs to a ragged
    hem; one solid plate, 1.2 cm thick."""
    sgn = -1 if front else 1
    xs = [0.0, 0.04, 0.075, 0.105]
    hem = [0.205, 0.255, 0.235, 0.27] if front else [0.19, 0.24, 0.255, 0.28]
    cols = []
    for x, zh in zip(xs, hem):
        y44 = ray_y(tree, max(x, 0.002), 0.445, front)
        y40 = ray_y(tree, max(x, 0.002), 0.40, front)
        y44 = y44 if y44 is not None else sgn * 0.10
        y40 = y40 if y40 is not None else sgn * 0.11
        y1 = y40 + sgn * 0.022
        cols.append([(x, y44 - sgn * 0.014, 0.445), (x, y1, 0.40), (x, y1 + sgn * 0.004, 0.31), (x, y1 + sgn * 0.008, zh)])
    # the outer sheet keeps the free rows at the outermost depth so the plate hangs straight
    out = min if front else max
    for r in (1, 2, 3):
        yy = out(c[r][1] for c in cols)
        for c in cols:
            c[r] = (c[r][0], yy, c[r][2])
    th = 0.012 * -sgn
    O = [[bm.verts.new(Vector(p)) for p in c] for c in cols]
    I = [[bm.verts.new(Vector((p[0], p[1] + th, p[2]))) for p in c] for c in cols]
    for i in range(len(xs) - 1):
        for r in range(3):
            q = [O[i][r], O[i + 1][r], O[i + 1][r + 1], O[i][r + 1]]
            bm.faces.new(q if front else list(reversed(q)))
            q = [I[i][r + 1], I[i + 1][r + 1], I[i + 1][r], I[i][r]]
            bm.faces.new(q if front else list(reversed(q)))
    rim = []
    for r in range(3):                      # outer side edge
        rim.append((O[-1][r], O[-1][r + 1], I[-1][r + 1], I[-1][r]))
    for i in range(len(xs) - 1):            # top and hem
        rim.append((O[i + 1][0], O[i][0], I[i][0], I[i + 1][0]))
        rim.append((O[i][3], O[i + 1][3], I[i + 1][3], I[i][3]))
    for q in rim:
        bm.faces.new(q)
    recalc_normals(bm)


def belt(bm, tree):
    """The rope belt: a square tube round the waist at z 0.43 per side (front seam -> back seam), its inner half
    sunk in the skin; it ends 4 mm off the seam so each side is one rooted piece."""
    z = 0.432
    t = (z - 0.42) / 0.035
    A, Bq = P('R2'), P('R2b')
    pts = [A[j].lerp(Bq[j], t) for j in range(10)]
    cen = Vector((0.0, sum(p.y for p in pts) / 10, z))
    rows = []
    path = []
    for j, p in enumerate(pts):
        p = p.copy()
        if j in (0, 9):
            p.x = 0.004
        path.append(p)
    # the 10-vertex ring keeps the rope round; one extra point in its flat front span
    for p in path[:9] + [path[8].lerp(path[9], 0.5), path[9]]:
        n = Vector((p.x, p.y - cen.y, 0.0)).normalized()
        loc, fn, _i, _d = tree.find_nearest(p)
        q = loc + n * 0.004
        rows.append(sq(q, n, Vector((0, 0, 1)), 0.011, 0.012))
    box_chain(bm, rows)


def fingers(bm):
    af = arm_frames()
    c, e1, e2, r1, r2 = af[-1]
    d = (c - af[-2][0]).normalized()
    for o, L in ((-0.03, 0.058), (-0.01, 0.064), (0.011, 0.06), (0.031, 0.052)):
        root = c + e2 * o + d * 0.004
        mid = root + d * L * 0.55 - e1 * 0.008
        tip = root + d * L - e1 * 0.02
        w = 0.0115 if abs(o) < 0.02 else 0.0105
        rows = [sq(root - d * 0.012, e1, e2, w, w), sq(mid, e1, e2, w * 0.95, w * 0.95), sq(tip, e1, e2, w * 0.7, w * 0.75)]
        box_chain(bm, rows)
    # thumb: from the front of the hand, down and forward
    hc = af[-2][0]
    root = hc + af[-2][2] * (-af[-2][4] * 0.6) + af[-2][1] * (-0.006)
    dd = (Vector((-0.01, -0.5, -1.0))).normalized()
    rows = [sq(root - dd * 0.012, Vector((1, 0, 0)), Vector((0, 1, 0)), 0.011, 0.011),
            sq(root + dd * 0.03, Vector((1, 0, 0)), Vector((0, 1, 0)), 0.01, 0.01),
            sq(root + dd * 0.05, Vector((1, 0, 0)), Vector((0, 1, 0)), 0.007, 0.007)]
    box_chain(bm, rows)


def toes(bm, tree):
    (cx, cy, _), r1, r2 = LEG[-1]
    for o, w, L in ((-0.036, 0.012, 0.034), (-0.016, 0.009, 0.03), (0.002, 0.0085, 0.028), (0.018, 0.008, 0.026), (0.032, 0.0075, 0.022)):
        x = cx + o
        hit = tree.ray_cast(Vector((x, -0.5, 0.014)), Vector((0, 1, 0)), 0.6)[0]
        if hit is None:
            continue
        h = Vector((x, hit.y, 0.0))
        X, Z = Vector((1, 0, 0)), Vector((0, 0, 1))
        rows = [[h + Vector((-w, 0.012, 0.002)), h + Vector((w, 0.012, 0.002)), h + Vector((w, 0.012, 0.028)), h + Vector((-w, 0.012, 0.028))],
                [h + Vector((-w, -L * 0.5, 0.001)), h + Vector((w, -L * 0.5, 0.001)), h + Vector((w * 0.9, -L * 0.5, 0.022)), h + Vector((-w * 0.9, -L * 0.5, 0.022))],
                [h + Vector((-w * 0.8, -L, 0.001)), h + Vector((w * 0.8, -L, 0.001)), h + Vector((w * 0.7, -L, 0.014)), h + Vector((-w * 0.7, -L, 0.014))]]
        box_chain(bm, rows)


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def stage3(k, body):
    paint(body, {'skin': PAL['skin']}, lambda c, n, i: 'skin')   # single flat skin colour: no two-tone ear mask
    tree = body_bvh(body)
    # eyes: small calm yellow lenses with a black pupil, in the sockets
    ec = eye_face_centre()
    c, n, _i, _d = tree.find_nearest(ec + Vector((0.0, -0.004, 0.0)) - Vector((0.006, 0, 0)))
    n = n if n.x > 0 else -n
    bm = bmesh.new()
    lens(bm, c, n, 0.015, 0.008)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'black': PAL['black']},
          lambda c_, n_, i: 'black' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.0065 and n_.dot(n) > 0.5 else 'eye')
    vo = object_from_bm('vest', vest(tree))
    paint(vo, {'leather': PAL['leather']}, lambda c_, n_, i: 'leather')
    bm = bmesh.new()
    flap(bm, tree, True)
    flap(bm, tree, False)
    belt(bm, tree)
    lo = object_from_bm('loincloth', bm)
    paint(lo, {'leather': PAL['leather'], 'rope': PAL['rope']},
          lambda c_, n_, i: 'rope' if 0.415 < c_.z < 0.45 and abs(c_.y) > 0.04 and not (abs(c_.x) < 0.11 and abs(abs(c_.y) - 0.12) < 0.006) else 'leather')
    bm = bmesh.new()
    fingers(bm)
    fo = object_from_bm('fingers', bm)
    paint(fo, {'skin': PAL['skin'], 'black': PAL['black']}, lambda c_, n_, i: 'skin')
    bm = bmesh.new()
    toes(bm, tree)
    to = object_from_bm('toes', bm)
    paint(to, {'skin': PAL['skin'], 'black': PAL['black']},
          lambda c_, n_, i: 'black' if c_.y < LEG[-1][0][1] - LEG[-1][2] - 0.012 and c_.z > 0.008 else 'skin')
    return [eye, vo, lo, fo, to]


# ---------------------------------------------------------------- stage 4
def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['crown'], 'neck', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing, a slow head turn, an ear twitch, the arms sway
    clip(rig, 'idle', {1: {}, 12: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, 4, 0), 'upperarm.L': (3, 0, 0), 'upperarm.R': (-3, 0, 0)},
                       20: {'ear.L': (0, 0, -10)}, 24: {'head': (0, 0, 0)}, 27: {},
                       36: {'chest': (2, 0, 0), 'neck': (-2, 0, 0), 'head': (0, -4, 0), 'upperarm.L': (-3, 0, 0), 'upperarm.R': (3, 0, 0)}, 48: {}})
    # move: a walk; legs swing in opposition, the knee folds on the swinging leg, the arms counter-swing
    A, S = 22, 14
    clip(rig, 'move', {
        1: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 4, 0)},
        9: {'thigh.R': (5, 0, 0), 'shin.R': (-35, 0, 0), 'foot.R': (15, 0, 0)},
        17: {'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'upperarm.L': (S, 0, 0), 'upperarm.R': (-S, 0, 0), 'spine': (0, -4, 0)},
        25: {'thigh.L': (5, 0, 0), 'shin.L': (-35, 0, 0), 'foot.L': (15, 0, 0)},
        33: {'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'upperarm.L': (-S, 0, 0), 'upperarm.R': (S, 0, 0), 'spine': (0, 4, 0)}},
        loc={1: {'hips': (0, 0, 0)}, 9: {'hips': (0, 0.012, 0)}, 17: {'hips': (0, 0, 0)}, 25: {'hips': (0, 0.012, 0)}, 33: {'hips': (0, 0, 0)}})
    # attack: wind up the left arm back, then a forward clawing swipe with a lean and a head jut
    clip(rig, 'attack', {
        1: {},
        10: {'chest': (-6, 0, 0), 'upperarm.L': (-40, 0, 0), 'forearm.L': (25, 0, 0), 'head': (-5, 0, 0)},
        18: {'chest': (12, 0, 0), 'spine': (4, 0, 0), 'upperarm.L': (55, 0, 0), 'forearm.L': (10, 0, 0), 'head': (6, 0, 0),
             'neck': (5, 0, 0), 'upperarm.R': (-10, 0, 0)},
        24: {'chest': (8, 0, 0), 'upperarm.L': (35, 0, 0), 'head': (3, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
