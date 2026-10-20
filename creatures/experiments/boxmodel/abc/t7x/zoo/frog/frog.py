import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
import parts as PT
from smooth_borders import smooth_borders
from mathutils.kdtree import KDTree

# t7 hand box model (zoo workflow v2): a sitting bullfrog. One spine loft of 14-vertex half rings (snout tip -> rump
# cap), every ring a level-free vertical section placed by hand from reference/side.png + front.png. Limbs are extruded
# from BROAD loft windows through a sloped transition ring (the rhino/troll trick): the short front legs from 3 x 3
# lower-chest windows (level rings going down), the folded hind legs as one big drumstick mass from a 4 x 5 window on the
# rear lower flank (sections parallel to the flank, pushed out and forward: the haunch rises out of the flank, no
# knife fold), the raised eye domes from 2 x 2 windows on the flat skull top (level rings going up).
META = dict(creature='frog', model='opus', stage1_tris=(1500, 3600), total_tris=(2000, 6000),
            closeups=[('head', (0.0, -0.17, 0.25), 0.11, 'hero'),
                      ('front leg', (0.13, -0.08, 0.06), 0.07, 'hero'),
                      ('hind leg', (0.17, 0.12, 0.07), 0.10, 'az090'),
                      ('eye', (0.08, -0.16, 0.285), 0.05, 'az045')])

# the skeleton the model is built on (x >= 0 half; .L on +X)
J = dict(
    hips=(0.0, 0.13, 0.11), spine=(0.0, 0.03, 0.13), chest=(0.0, -0.07, 0.15),
    head=(0.0, -0.115, 0.20), nose=(0.0, -0.235, 0.232),
    shoulder=(0.115, -0.074, 0.105), elbow=(0.14, -0.066, 0.064), wrist=(0.134, -0.088, 0.026),
    hand=(0.132, -0.13, 0.004),
    hipL=(0.12, 0.13, 0.085), knee=(0.185, 0.05, 0.06), ankle=(0.175, 0.215, 0.03), toe=(0.18, 0.02, 0.004),
)

NV = 14
DEBUG = False


def tbz(nm, y, top, bot, W, f, pr, tuck=0.0):
    """A vertical section at y: top and bottom seam z, half width W at the widest level (f of the height up); tuck
    narrows the bottom half by tuck x |fh|."""
    return (nm, y, top, bot, W, f, pr, tuck)


# hand-placed half-ring profiles (fx across, fh: +1 top seam .. -1 bottom seam, 0 = the widest level)
HEAD = [(0, 1), (0.36, 0.99), (0.64, 0.95), (0.83, 0.84), (0.94, 0.64), (0.99, 0.37), (1.0, 0.08),
        (0.98, -0.16), (0.92, -0.40), (0.83, -0.61), (0.69, -0.78), (0.51, -0.91), (0.27, -0.985), (0, -1)]
BODY = [(0, 1), (0.31, 0.985), (0.58, 0.93), (0.78, 0.80), (0.91, 0.60), (0.98, 0.33), (1.0, 0.05),
        (0.985, -0.22), (0.94, -0.47), (0.86, -0.68), (0.73, -0.85), (0.54, -0.95), (0.28, -0.99), (0, -1)]

SECS = [
    # snout tip -> skull (the eye-dome windows sit on H1-H3, j1-j3). s1 r8: a rounded wedge snout (top-view taper:
    # 0.32 / 0.56 / 0.72 of the body width at 4 / 8 / 10 cm behind the tip) and the throat bulging lower (side view)
    tbz('N0', -0.240, 0.236, 0.226, 0.010, 0.50, HEAD),
    tbz('N1', -0.236, 0.248, 0.212, 0.030, 0.45, HEAD),
    tbz('N2', -0.227, 0.258, 0.198, 0.050, 0.42, HEAD),
    tbz('N3', -0.213, 0.266, 0.182, 0.066, 0.42, HEAD),
    tbz('H0', -0.195, 0.273, 0.160, 0.080, 0.44, HEAD),
    tbz('H1', -0.175, 0.278, 0.134, 0.093, 0.46, HEAD),
    tbz('H2', -0.155, 0.281, 0.110, 0.105, 0.48, HEAD),
    tbz('H3', -0.135, 0.282, 0.088, 0.114, 0.50, HEAD),
    # chest (fore-leg windows C0-C3, j7-j10)
    tbz('C0', -0.112, 0.281, 0.066, 0.118, 0.50, BODY, 0.12),   # s1 r9: chest narrower below (the arms sit in front of it)
    tbz('C1', -0.084, 0.279, 0.048, 0.120, 0.46, BODY, 0.16),   # s1 r6: tuck the belly (front view +-0.12): the arm clears it
    tbz('C2', -0.064, 0.275, 0.032, 0.124, 0.42, BODY, 0.20),
    tbz('C3', -0.044, 0.270, 0.022, 0.130, 0.40, BODY, 0.20),
    # the belly sagging to the ground
    tbz('M0', -0.022, 0.263, 0.017, 0.138, 0.40, BODY, 0.15),
    tbz('M1', 0.000, 0.255, 0.015, 0.146, 0.40, BODY, 0.09),
    # s1 r4: from M2 back the widest level drops low (f 0.32): the body's lower rear flank stands out at x 0.14 and
    # carries the drumstick's inner half, so the leg window (B0-R1, j4-j10) is nearly the drumstick's own footprint
    tbz('M2', 0.022, 0.246, 0.015, 0.146, 0.36, BODY, 0.05),
    tbz('B0', 0.046, 0.236, 0.016, 0.145, 0.36, BODY, 0.08),   # s1 r11: tuck the rump's underside (rear view +-0.08)
    # hind-leg windows B0-R1, j4-j10
    tbz('B1', 0.074, 0.224, 0.018, 0.143, 0.38, BODY, 0.16),
    tbz('B2', 0.102, 0.210, 0.020, 0.140, 0.40, BODY, 0.24),
    tbz('B3', 0.130, 0.194, 0.022, 0.135, 0.42, BODY, 0.28),
    tbz('B4', 0.156, 0.176, 0.025, 0.126, 0.44, BODY, 0.30),
    tbz('R0', 0.178, 0.156, 0.029, 0.112, 0.45, BODY, 0.30),
    tbz('R1', 0.198, 0.134, 0.035, 0.102, 0.46, BODY, 0.16),   # s4 r2: fuller, in the hind window
    # rump closing
    tbz('R2', 0.213, 0.112, 0.045, 0.074, 0.48, BODY, 0.12),
    tbz('R3', 0.223, 0.094, 0.058, 0.032, 0.45, BODY),
]

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def sec_pts(y, top, bot, W, f, pr, tuck=0.0):
    zc = bot + f * (top - bot)
    out = []
    for fx, fh in pr:
        z = zc + fh * ((top - zc) if fh >= 0 else (zc - bot))
        out.append((fx * W * (1 - tuck * abs(fh) if fh < 0 else 1.0), y, z))
    return out


def S(c, f1, f2, r1, r2, n=2.4, dome=0.0):
    """A limb section: centre c, in-plane axes f1 (the window's along-spine axis maps here) and f2 (the window's
    second axis), radii r1/r2, superellipse exponent n; the extrusion runs along f1 x f2; dome lifts interior verts."""
    return dict(c=Vector(c), f1=Vector(f1).normalized(), f2=Vector(f2).normalized(), r1=r1, r2=r2, n=n, dome=dome)


def spow(c, n):
    return math.copysign(abs(c) ** (2 / n), c)


def grow(bm, rings, spans, i0, j0, A, B, secs, t1=(0.45, 0.45), tag='', rec=None):
    """Extrude the A x B face window (rings i0..i0+A, ring vertices j0..j0+B) section by section. Boundary vertices
    keep their angular ORDER round the window and are spread at even angles round each section; the first new ring is
    the transition ring: t1[0] of the way to secs[0] in the window plane, t1[1] along the window normal."""
    faces = [spans[i0 + a][j0 + b] for a in range(A) for b in range(B)]
    G = [[rings[i0 + a][j0 + b] for b in range(B + 1)] for a in range(A + 1)]
    P = np.array([v.co[:] for row in G for v in row])
    C = Vector(P.mean(0))
    nrm = Vector(np.linalg.svd(P - P.mean(0))[2][2])
    fn = sum((f.normal for f in faces), Vector())
    if nrm.dot(fn) < 0:
        nrm = -nrm
    e1 = (Y - nrm * Y.dot(nrm)).normalized()
    e2 = nrm.cross(e1)
    loc = {}
    for row in G:
        for v in row:
            d = v.co - C
            loc[v] = (d.dot(e1), d.dot(e2))
    h1 = max(abs(p[0]) for p in loc.values()) or 1.0
    h2 = max(abs(p[1]) for p in loc.values()) or 1.0
    bnd = [G[a][b] for a in range(A + 1) for b in range(B + 1) if a in (0, A) or b in (0, B)]
    ang = {v: math.atan2(loc[v][1] / h2, loc[v][0] / h1) for v in bnd}
    order = sorted(bnd, key=lambda v: ang[v])
    N = len(order)
    # the even-angle offset: the CIRCULAR mean of (actual - even) angles (s1 r5: an arithmetic mean of wrapped values
    # averaged -pi and +pi to 0 and turned every limb section 180 deg against its window: r1-r4's 'wheels')
    dd = [ang[v] - 2 * math.pi * i / N for i, v in enumerate(order)]
    off = math.atan2(sum(math.sin(d) for d in dd), sum(math.cos(d) for d in dd))
    roles = {}
    for i, v in enumerate(order):
        roles[v] = ('b', off + 2 * math.pi * i / N)
    # s1 r2: interior (cap) vertices by transfinite (Coons) interpolation of the boundary in grid index space, so the
    # cap grid can never fold over the evenly re-spaced boundary (r1: flipped cap faces = self-intersections)
    for a in range(1, A):
        for b in range(1, B):
            roles[G[a][b]] = ('i', a / A, b / B)
    gidx = {G[a][b]: (a, b) for a in range(A + 1) for b in range(B + 1)}

    def bpos(sec, ro):
        c, f1, f2, r1, r2, n = sec['c'], sec['f1'], sec['f2'], sec['r1'], sec['r2'], sec['n']
        return c + f1 * (r1 * spow(math.cos(ro[1]), n)) + f2 * (r2 * spow(math.sin(ro[1]), n))

    def rpos(sec, ro):
        if ro[0] == 'b':
            return bpos(sec, ro)
        u, w = ro[1], ro[2]
        Pb = lambda a, b: bpos(sec, roles[G[a][b]])
        a_, b_ = round(u * A), round(w * B)
        L0, L1 = Pb(0, b_), Pb(A, b_)
        M0, M1 = Pb(a_, 0), Pb(a_, B)
        C00, C10, C01, C11 = Pb(0, 0), Pb(A, 0), Pb(0, B), Pb(A, B)
        p = ((1 - u) * L0 + u * L1 + (1 - w) * M0 + w * M1
             - ((1 - u) * (1 - w) * C00 + u * (1 - w) * C10 + (1 - u) * w * C01 + u * w * C11))
        r = 1 - (2 * u - 1) ** 2 * 0.5 - (2 * w - 1) ** 2 * 0.5
        return p + sec['f1'].cross(sec['f2']) * (sec['dome'] * r)

    cur = {v: (v.co.copy(), roles[v]) for v in roles}

    def step(faces, place):
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            o = min(cur, key=lambda o_: (cur[o_][0] - v.co).length)
            new[v] = cur[o]
        for v, (p0, ro) in new.items():
            v.co = place(p0, ro)
        if rec is not None:          # s4 r17: the new ring's positions (stage 2 finds the arm's rings by them)
            rec.append([v.co.copy() for v in new])
        if DEBUG:
            Pn = np.array([v.co[:] for v in new])
            say('  ring', len(new), 'min', Pn.min(0).round(3).tolist(), 'max', Pn.max(0).round(3).tolist())
        return r['faces'], {v: (v.co.copy(), ro) for v, (p0, ro) in new.items()}

    def first(p0, ro):
        q = rpos(secs[0], ro)
        d = q - p0
        dn = nrm * d.dot(nrm)
        if DEBUG and ro[0] == 'b':
            say('   first', tuple(round(x, 3) for x in p0), ro, tuple(round(x, 3) for x in q))
        return p0 + (d - dn) * t1[0] + dn * t1[1]

    faces, cur = step(faces, first)
    for sec in secs:
        faces, cur = step(faces, lambda p0, ro, sec=sec: rpos(sec, ro))
    say(f'grow {tag}: window centre {tuple(round(x, 3) for x in C)} normal {tuple(round(x, 2) for x in nrm)} '
        f'ring {N} verts, {len(secs) + 1} rings')
    return faces


# ---- limb sections ------------------------------------------------------------------------------------------------
# front legs: level rings going down (f1 = y, f2 = +x: the window's upper edge maps to the leg's outer side)
# s1 r9: thick short arms set in (x 0.13, front view: they overlap the chest), the elbow back, the hand forward
# s4 r2 (re-lock): the first arm ring at the window's own height (z 0.115): r1's ring sat 1.5 cm under the window
# centre and the arm's front/rear walls folded back on themselves (knife 2.35 r, 172 deg at y -0.046, z 0.10)
# s4 r3 (re-lock): the first two arm rings TILTED (outer side up 42 / 19 deg), so the ring plane turns from the
# window's (a near-vertical flank patch) to level over two steps; r2's level first ring folded the armpit wall back up
# (knife 2.23 r, 159 deg under the shoulder)
FORE = [S((0.130, -0.067, 0.092), Y, Vector((1, 0, 0.6)), 0.034, 0.030, 2.4),    # upper arm (s4 r8: rear wall drops from the rim)
        S((0.135, -0.066, 0.068), Y, Vector((1, 0, 0.25)), 0.030, 0.027, 2.4),   # elbow
        S((0.134, -0.080, 0.050), Y, X, 0.023, 0.023, 2.4),    # forearm
        S((0.131, -0.092, 0.035), Y, X, 0.020, 0.020, 2.4),    # wrist
        S((0.130, -0.104, 0.016), Y, X, 0.028, 0.026, 2.4),    # hand
        S((0.130, -0.110, 0.003), Y, X, 0.031, 0.028, 2.4)]    # sole
# hind legs: the folded drumstick, sections parallel to the flank, pushed out (+x).
# s1 r7: the drumstick as a rounded egg, not a cylinder: five sections that swell (widest 4.5 cm out) and then round
# off over three shrinking rings into a domed outer end; the axis pitched 10 deg (rising to the rear, side view) and
# yawed 14 deg (the knee end further out than the heel end, plan view)
_p, _w = 0.17, 0.14       # s1 r12: yaw 0.24 -> 0.14 rad and fuller, deeper sections: from behind it reads as a lump
HY = Vector((-math.sin(_w), math.cos(_w) * math.cos(_p), math.cos(_w) * math.sin(_p)))
HZ = Vector((0, -math.sin(_p), math.cos(_p)))
HIND = [S((0.140, 0.136, 0.082), HY, HZ, 0.094, 0.066, 2.1),
        S((0.165, 0.140, 0.082), HY, HZ, 0.100, 0.070, 2.1),
        S((0.186, 0.138, 0.081), HY, HZ, 0.094, 0.064, 2.1),
        S((0.200, 0.134, 0.080), HY, HZ, 0.074, 0.050, 2.0),
        S((0.208, 0.130, 0.079), HY, HZ, 0.044, 0.030, 2.0, dome=0.005)]
# eye domes: level rings going up (f1 = y, f2 = -x: the window's second axis runs inward)
# s1 r10: round domes from a 3 x 3 window (H0-H3, j1-j4: x 0.04-0.10 like the sheet's front view), 12-vertex
# elliptical rings swelling past the window and closing over four rings into a small cap
DOME = [S((0.071, -0.163, 0.284), Y, -X, 0.033, 0.032, 2.0),
        S((0.072, -0.161, 0.296), Y, -X, 0.029, 0.028, 2.0),
        S((0.072, -0.159, 0.304), Y, -X, 0.019, 0.019, 2.0),
        S((0.072, -0.158, 0.308), Y, -X, 0.009, 0.009, 2.0)]


FORE_RINGS = []     # stage-1 positions of the arm rings: transition, upper arm, elbow, forearm, wrist, hand, sole


def stage1(k):
    bm = bmesh.new()
    idx = {s[0]: i for i, s in enumerate(SECS)}
    rings = [ring(bm, sec_pts(*s[1:])) for s in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    grow(bm, rings, spans, idx['B0'], 4, 6, 6, HIND, (0.45, 0.45), 'hind')
    FORE_RINGS.clear()
    grow(bm, rings, spans, idx['C0'], 6, 4, 3, FORE, (0.6, 0.5), 'fore', rec=FORE_RINGS)   # s4 r7: 4 x 3 window C0-M0 j6-j9 (the proven leg root)
    grow(bm, rings, spans, idx['H0'], 1, 3, 3, DOME, (0.5, 0.3), 'dome')
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ---- stage 2: eye sockets on the domes ---------------------------------------------------------------------------------
EYE_DIR = Vector((0.78, -0.50, 0.30)).normalized()     # the lens looks out, forward and a little up (sheet front/side)
EYE_AT = Vector((0.082, -0.163, 0.282))                 # the dome's centre the ray aims at
SOCKET = []


# s4 r17: the front legs thicker, toward the sheet (front view: the forearm ~0.19 of the body width, ours ~0.15; the
# wrist the thinnest point read as a stilt). Each arm ring is scaled in its own section plane about its centre (axial
# offsets kept, so ring spacing and the sole's ground contact stay); the transition ring swells a little so the root
# band rounds into the upper arm instead of folding at the window (vertex moves only, no re-lock).
# ring:          transition upper  elbow  forearm wrist  hand  sole
ARM_SCALE = [1.08, 1.12, 1.24, 1.36, 1.36, 1.12, 1.08]
ARM_OUT = [0.0, 0.002, 0.004, 0.006, 0.006, 0.004, 0.004]    # + x: the thicker arm's inner wall keeps off the chest


ROOT_SOFT = (2, 0.3)       # root-band relax: iterations, lerp toward the neighbour mean


def thicken_arms(bm):
    kd = KDTree(len(bm.verts))
    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)
    kd.balance()
    bm.verts.ensure_lookup_table()
    n = 0
    for r, pts in enumerate(FORE_RINGS):
        vs = []
        for p in pts:
            co, i, d = kd.find(p)
            if d is not None and d < 1e-5:
                vs.append(bm.verts[i])
        if not vs:
            continue
        if r == 0:
            c = sum((v.co for v in vs), Vector()) / len(vs)
            P = np.array([v.co[:] for v in vs])
            ax = Vector(np.linalg.svd(P - P.mean(0))[2][2])
        else:
            c, ax = FORE[r - 1]['c'], FORE[r - 1]['f1'].cross(FORE[r - 1]['f2']).normalized()
        s = ARM_SCALE[r]
        for v in vs:
            d = v.co - c
            da = ax * d.dot(ax)
            v.co = c + da + (d - da) * s + Vector((ARM_OUT[r], 0, 0))
            n += 1
    say(f'arms thickened: {n} verts over {len(FORE_RINGS)} rings (scale {ARM_SCALE})')
    # the root blend softened: the transition ring and the window rim (the loft vertices round it) relaxed toward
    # their neighbours' mean, so the concave turn from the chest into the arm spreads over the band
    r0 = set()
    for p in FORE_RINGS[0]:
        co, i, d = kd.find(p)
        if d is not None and d < 1e-5:
            r0.add(bm.verts[i])
    rim = {e.other_vert(v) for v in r0 for e in v.link_edges} - r0      # window rim + first arm ring
    r1 = {bm.verts[kd.find(p)[1]] for p in FORE_RINGS[1]}   # (all band moves are on x > 0, no seam verts)
    band = [v for v in (r0 | (rim - r1)) if abs(v.co.x) > 1e-4]   # s4 r18: with the first arm ring too: seam strip 1.07 r
    for _ in range(ROOT_SOFT[0]):
        tgt = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in band}
        for v in band:
            v.co = v.co.lerp(tgt[v], ROOT_SOFT[1])
    say(f'arm root softened: {len(band)} verts ({len(r0)} transition ring + {len(band) - len(r0)} rim), {ROOT_SOFT}')


def stage2(k, body):
    bm = edit(body)
    thicken_arms(bm)
    # s4 r16: the head 14 % wider (side_by_side: the sheet's head is ~0.75 of the body width at the mouth, ours read
    # ~0.6 with the domes standing up like ears): x scaled 1.14 ahead of y -0.15, easing to 1.0 at the chest (y -0.112)
    for v in bm.verts:
        y = v.co.y
        if y < -0.112:
            t = min(1.0, (-0.112 - y) / 0.038)
            v.co.x *= 1.0 + 0.14 * (t * t * (3 - 2 * t))
    tree = BVHTree.FromBMesh(bm)
    hit = tree.ray_cast(EYE_AT + EYE_DIR * 0.12, -EYE_DIR, 0.3)[0]
    f = face_near(bm, hit, n=tuple(EYE_DIR))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the dome face that looks out-forward'):
        inner = inset(bm, [f], 0.22, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.0015)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [sc.copy(), fn.copy()]
    ec0 = sc.copy()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.012 and abs(c.y - ec0.y) < 0.012 and abs(c.z - ec0.z) < 0.012)
    say(f'eye socket at {tuple(round(x, 3) for x in sc)} normal {tuple(round(x, 2) for x in fn)}')
    # s4 r14: the drumstick's outer end reads as a flat disc (orbit az135/az225: concentric rings on a flat face): dome
    # it out, up to 9 mm at the centre falling off to 0 at 7.5 cm round it (vertex moves only)
    n_dome = 0
    for v in bm.verts:
        c = v.co
        if c.x > 0.192 and 0.03 < c.y < 0.25 and c.z < 0.17:
            d = math.hypot(c.y - 0.130, (c.z - 0.079) * 1.4)
            v.co.x += 0.009 * max(0.0, 1 - (d / 0.075) ** 2)
            n_dome += 1
    say(f'eye socket at {tuple(round(x, 3) for x in sc)}; drumstick end domed: {n_dome} verts')
    commit(body, bm)


# ---- stage 3: colour, lens eyes, fingers and hind feet ------------------------------------------------------------------
# s4 r13: olive (sheet) not lime; the darker 'back' patches dropped (they read as rectangular blocks on the back)
FINGER_LEN = (0.028, 0.034, 0.033, 0.027)     # s4 r19: four fat fingers (detail gate: L/t <= 4.5 on tier 1)
FINGER_SPREAD = 80.0                           # s4 r20: 90 -> 80, the outer finger ran into the hand
TOE_LEN = (0.027, 0.034, 0.034, 0.028)        # s4 r19: four fat webbed toes (was five 50-78 mm sticks)
PAL = {'skin': '#76884a', 'belly': '#ddd3a6', 'tip': '#8d7a68', 'iris': '#b9893a', 'dark': '#16130f'}


def zline(pts, y):
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[0][1] if y < pts[0][0] else pts[-1][1]


# the pale throat/belly border (side view): the mouth line from the snout to its corner, then down behind the arm
MOUTH = [(-0.26, 0.228), (-0.20, 0.219), (-0.14, 0.206), (-0.12, 0.196), (-0.09, 0.15), (-0.05, 0.11), (0.02, 0.085),
         (0.10, 0.07), (0.30, 0.06)]


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z
    arm = -0.15 < y < -0.03 and x > 0.10 and z < 0.115
    leg = y > 0.03 and x > 0.125 and z < 0.165
    if not arm and not leg and z < zline(MOUTH, y) and (n.z < 0.3 or y < -0.12) and x < 0.125:
        return 'belly'
    return 'skin'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h, sides=10):
    """A low-poly eye lens: back cone, iris ring, pupil cap."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * 2 * math.pi / sides for k_ in range(sides)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, Bv = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.4)
    for j in range(sides):
        a, b = j, (j + 1) % sides
        bm.faces.new([Bv, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def digit(bm, root, tip, w, h, bulb):
    """A finger/toe: a 4-sided tapered box from root to tip (flat sole), then a round low-poly bulb at the tip."""
    d = (tip - root).normalized()
    side = d.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(d).normalized()
    rows = []
    for t, sw, sh in ((0.0, 1.0, 1.0), (0.55, 0.85, 0.85), (1.0, 0.75, 0.75)):
        c = root.lerp(tip, t)
        rows.append([bm.verts.new(c + side * (su * w * sw / 2) + up * (sz * h * sh / 2)) for su, sz in
                     ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new([a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]])
    bm.faces.new(rows[-1])
    # the bulb: an 8-sided bicone (a flattened ball) centred just past the tip
    bc = tip + d * bulb * 0.4
    ring_ = [bm.verts.new(bc + (d * math.cos(t) + side * math.sin(t)) * bulb) for t in [k_ * math.pi / 4 for k_ in range(8)]]
    top, bot = bm.verts.new(bc + up * bulb * 0.8), bm.verts.new(bc - up * bulb * 0.8)
    for j in range(8):
        a, b = ring_[j], ring_[(j + 1) % 8]
        bm.faces.new([a, b, top])
        bm.faces.new([b, a, bot])


def ground_hit(tree, x, y, z0=0.3):
    return tree.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 1.0)[0]


def mirror_x(v):
    return Vector((-v.x, v.y, v.z))


def stage3(k, body):
    paint(body, PAL, body_rule)
    # s4 r17: owner redline (bottom / -45 views): the cream belly / green thigh and forelimb borders stair-step along
    # the quad grid. kit/smooth_borders: anti-stair diagonal cuts at 3-to-1 colour corners + a tangential relax of the
    # border vertices re-projected onto the original surface (shape kept, density only up)
    smooth_borders(body, k=k, iters=8)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    pieces = []
    # eyes: a round lens in each dome's socket, an iris ring and a black pupil
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.0012, n, 0.0115, 0.0055)
    lens(bm, mirror_x(c) + mirror_x(n) * 0.0012, mirror_x(n), 0.0115, 0.0055)
    eye = object_from_bm('eye', bm, mirror=False)

    def eye_rule(c_, n_, i):
        cc, nn = (c, n) if c_.x > 0 else (mirror_x(c), mirror_x(n))
        d = c_ - cc
        rad = (d - nn * d.dot(nn)).length
        return 'dark' if rad < 0.0058 and n_.dot(nn) > 0.5 else 'iris'
    paint(eye, {'iris': PAL['iris'], 'dark': PAL['dark']}, eye_rule)
    pieces.append(eye)
    # s4 r19 (owner 2026-10-21, game distance): fingers and toes were thin sticks (detail gate: 5.5 mm = 1.8% H,
    # length/thickness 7-13). Now kit parts in the chunky-first style: four FAT splayed fingers with knob tips
    # (parts.digits_splayed: 12 x 10.5 mm sections, 28-36 mm long) and a thick webbed hind foot with four fat knobbed
    # toes (parts.foot_webbed: 11 mm toes on a web plate), both built on +x and mirrored
    def mirrored(ob):
        md = ob.modifiers.new('mirror', 'MIRROR')
        md.use_axis = (True, False, False)
        md.use_mirror_merge = False
        return ob
    hc = Vector((0.130, -0.114, 0.0))             # s4 r20: 4 mm forward (outer finger 11 mm visible at r19)
    hands = mirrored(PT.digits_splayed(hc, lengths=FINGER_LEN, width=0.012, height=0.0105, spread=FINGER_SPREAD,
                                       r0=0.012, forward=(0, -1, 0), up=(0, 0, 1), lift=0.0045, name='fingers',
                                       style='game'))
    # s4 r20: green digits with tan knob tips (the sheet); the part slots came out tan all over
    def finger_tip(c_, n_, i):                    # s4 r21: only each finger's knob is tan (its own length)
        dx, dy = abs(c_.x) - hc.x, c_.y - hc.y
        a = math.degrees(math.atan2(-dx, -dy))
        k_ = min(len(FINGER_LEN) - 1, max(0, round((a / FINGER_SPREAD + 0.5) * (len(FINGER_LEN) - 1))))
        return 'tip' if math.hypot(dx, dy) > 0.012 + 0.86 * FINGER_LEN[k_] else 'skin'
    paint(hands, {'skin': PAL['skin'], 'tip': PAL['tip']}, finger_tip)
    pieces.append(hands)
    # hind feet: the heel embedded in the drumstick's underside, the toes forward on the ground
    fx = 0.178
    zt = []
    for yy in (0.19, 0.15, 0.11, 0.08):
        h = ground_hit(tree, fx, yy, 0.05)
        zt.append(h.z if h is not None else 0.0)
    top = max(0.014, min(zt) + 0.006)
    feet = mirrored(PT.foot_webbed((fx, 0.200, 0.0), length=0.118, width=0.040, forward=(0, -1, 0), up=(0, 0, 1),
                                   heel_h=top, heel_w=0.020, web=0.026, toes=4, toe_len=TOE_LEN, toe_h=0.011,
                                   splay=16.0, lift=0.0015, name='feet', style='game'))
    ball_y = 0.200 - 0.118

    def toe_tip(c_, n_, i):                       # s4 r21: only each toe's knob is tan
        dx, dy = abs(c_.x) - fx, c_.y - ball_y
        a = math.degrees(math.atan2(-dx, -dy))
        k_ = min(len(TOE_LEN) - 1, max(0, round(a / 16.0 + len(TOE_LEN) / 2 - 0.5)))
        return 'tip' if dy < 0 and math.hypot(dx, dy) > 0.026 + 0.80 * TOE_LEN[k_] else 'skin'
    paint(feet, {'skin': PAL['skin'], 'tip': PAL['tip']}, toe_tip)
    pieces.append(feet)
    say(f'foot sole top {top:.3f} (drumstick underside z {[round(z, 3) for z in zt]})')
    return pieces


# ---- stage 4: rig and clips --------------------------------------------------------------------------------------------
def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['head'], 'spine', True),
         ('head', J['head'], J['nose'], 'chest', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hand.L', J['wrist'], J['hand'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
         ('foot.L', J['ankle'], J['toe'], 'shin.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        if 'feet' in p.name:
            bind(p, rig)            # s4 r9: per vertex to the nearest bone (foot/shin): body weights stretched the toes 7x
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'chest': (-2.0, 0, 0), 'head': (2.0, 0, 0)}, 24: {},
                       36: {'chest': (-1.5, 0, 0), 'head': (-2.5, 0, 0)}, 48: {}})
    clip(rig, 'move', {
        1: {},
        6: {'chest': (4, 0, 0), 'head': (-3, 0, 0), 'thigh.L': (4, 0, 0), 'thigh.R': (4, 0, 0)},
        12: {'chest': (-6, 0, 0), 'head': (4, 0, 0), 'thigh.L': (-16, 0, 0), 'thigh.R': (-16, 0, 0),
             'shin.L': (14, 0, 0), 'shin.R': (14, 0, 0), 'upperarm.L': (-14, 0, 0), 'upperarm.R': (-14, 0, 0)},
        18: {'chest': (-3, 0, 0), 'thigh.L': (-8, 0, 0), 'thigh.R': (-8, 0, 0), 'shin.L': (6, 0, 0), 'shin.R': (6, 0, 0),
             'upperarm.L': (10, 0, 0), 'upperarm.R': (10, 0, 0)},
        24: {'chest': (3, 0, 0), 'head': (-2, 0, 0)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 6: {'hips': (0, 0, -0.006)}, 12: {'hips': (0, 0.03, 0.03)},
             18: {'hips': (0, 0.02, 0.025)}, 24: {'hips': (0, 0, -0.004)}, 32: {'hips': (0, 0, 0)}})
    clip(rig, 'attack', {
        1: {},
        6: {'chest': (5, 0, 0), 'head': (-4, 0, 0)},
        12: {'chest': (-10, 0, 0), 'head': (8, 0, 0), 'upperarm.L': (-10, 0, 0), 'upperarm.R': (-10, 0, 0)},
        16: {'chest': (-8, 0, 0), 'head': (6, 0, 0)},
        24: {}},
        loc={1: {'hips': (0, 0, 0)}, 6: {'hips': (0, 0.005, -0.004)}, 12: {'hips': (0, -0.02, 0.008)},
             16: {'hips': (0, -0.015, 0.006)}, 24: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
