import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
from smooth_borders import smooth_borders

# t7 hand box model (the base wolf's technique): one spine loft of half rings tail tip -> snout disc (12-vertex
# since poly pass 3), legs extruded as 2x2-face regions from the lower flank (octagon legs), ears as 1-face extrusions. keep_valleys is set in stage2.
META = dict(creature='boar', model='opus', stage1_tris=(1200, 2400), total_tris=(2200, 5200),
            closeups=[('head', (0.0, -0.56, 0.61), 0.2, 'hero'),
                      ('front hoof', (0.115, -0.17, 0.05), 0.08, 'hero'),
                      ('hind hoof', (0.115, 0.47, 0.05), 0.08, 'hero'),
                      ('crest', (0.0, -0.05, 0.84), 0.26, 'hero')])

# fix pass 1: legs read thin and long for a boar mass: leg sections radius +20 %, leg length -10 %
# (the trunk drops DZ, leg section heights scale LZ) — a base change, stage 1 re-locked
DZ, LZ, LR = -0.03, 0.9, 1.2


def dz(p):
    return (p[0], p[1], round(p[2] + DZ, 4))


def lz(p):
    return (p[0], p[1], round(p[2] * LZ, 4))


# the skeleton the model is built on (x >= 0 half; .L on +X), fitted to reference/side.png + front.png
J = dict(
    hips=(0.0, 0.42, 0.60), spine=(0.0, 0.15, 0.62), chest=(0.0, -0.12, 0.64),
    neck=(0.0, -0.27, 0.66), head=(0.0, -0.40, 0.67), nose=(0.0, -0.71, 0.55),
    tail0=(0.0, 0.60, 0.60), tail1=(0.0, 0.632, 0.53), tail2=(0.0, 0.665, 0.45), tail3=(0.0, 0.745, 0.27),
    shoulder=(0.13, -0.16, 0.50), elbow=(0.125, -0.165, 0.24), wrist=(0.115, -0.17, 0.10),
    fpaw=(0.115, -0.175, 0.03), ftoe=(0.115, -0.24, 0.01),
    hipL=(0.13, 0.45, 0.52), knee=(0.13, 0.45, 0.24), hock=(0.115, 0.485, 0.10),
    hpaw=(0.115, 0.475, 0.03), htoe=(0.115, 0.41, 0.01),
    ear=(0.15, -0.355, 0.86), eartip=(0.165, -0.335, 0.945),
)
LEGJ = ('elbow', 'wrist', 'fpaw', 'ftoe', 'knee', 'hock', 'hpaw', 'htoe')
J = {n: (lz(p) if n in LEGJ else dz(p)) for n, p in J.items()}

# poly pass 3 (base change, stage 1 re-locked): the half rings go 6 -> 12 vertices and the spine loft 18 -> 27
# stations, refitted to the traced sheet (reference/trace.png + blueprint.json): tops and bellies off the side
# outline, widths off the plan view (shoulder and ham bulges, a narrower waist, a rounder rump). Each half ring is a
# superellipse: the top half `nt`, the bottom half `nb`, the bottom narrowing to `taper` of W at the bottom seam.
NV = 12


def prof(nt, nb, taper=1.0):
    out = []
    for j in range(NV):
        t = math.pi * j / (NV - 1)
        c, s = math.cos(t), math.sin(t)
        n = nt if c >= 0 else nb
        fx = abs(s) ** (2 / n) if j not in (0, NV - 1) else 0.0
        fh = math.copysign(abs(c) ** (2 / n), c)
        if c < 0:
            fx *= 1 - (1 - taper) * abs(c)
        out.append((round(fx, 4), round(fh, 4)))
    return out




def resample(poly, ins):
    """The pass-2 6-vertex half ring as 12 vertices: `ins[k]` extra vertices evenly on segment k (collinear, so
    the old flat planes and the hard dorsal ridge stay)."""
    out = []
    for k in range(len(poly) - 1):
        (x0, h0), (x1, h1) = poly[k], poly[k + 1]
        for i in range(ins[k] + 1):
            t = i / (ins[k] + 1)
            out.append((round(x0 + (x1 - x0) * t, 4), round(h0 + (h1 - h0) * t, 4)))
    return out + [poly[-1]]


# fix pass 9 (owner: keep the 2x density, fix its faults): a hand-placed 12-vertex barrel, not a round
# superellipse. j0-j2 one flat back plane (mane plane) to a hard dorsal ridge at the midline; j2-j5 the shoulder
# bevel down to the widest flank; j5-j7 a near-flat flank plane; j7-j9 the leg-root bevel; j9-j11 a flat belly.
BODY = [(0, 1), (0.36, 0.93), (0.70, 0.86), (0.865, 0.64), (0.965, 0.36), (1.0, 0.05), (0.99, -0.27),
        (0.93, -0.56), (0.78, -0.74), (0.57, -0.88), (0.30, -0.955), (0, -1)]
HEADB = prof(3.0, 2.2, 0.75)     # skull back: broad brow, the jaw narrowing
HEAD = prof(2.8, 2.2, 0.7)
MUZ = prof(3.2, 2.6, 0.8)        # snout: boxier, for the flat side and bridge planes
TAIL = prof(2.2, 2.2, 0.8)
# the leg-root window on the lower flank: ring vertices j7 (outer), j8, j9 (inner) over three rings (2x2 faces)
LJ = (7, 8, 9)
EAR_J = (2, 3)                   # the ear face: j2 (inner) - j3 (outer) of the span N1 -> H0
EYE0 = (0.1487, -0.4447, 0.7159)  # the eye socket point of the pass-2 base (centre of its eye face)


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = (top[0], top[1] + DZ), (bot[0], bot[1] + DZ)
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


# the spine loft, tail tip -> snout: top and bottom of each section from the side outline, W from the plan view
SECS = [
    tb('T0', (0.752, 0.29), (0.735, 0.245), 0.022, TAIL),
    tb('T1', (0.725, 0.40), (0.665, 0.33), 0.032, TAIL),
    tb('Tm', (0.703, 0.45), (0.656, 0.40), 0.025, TAIL),
    tb('T2', (0.682, 0.50), (0.648, 0.47), 0.02, TAIL),
    tb('T3', (0.645, 0.585), (0.618, 0.535), 0.028, TAIL),
    # fix pass 9: the 2x-pass torso stations back (W1 / M1 return), widths smoothed into one monotone run per
    # mass (rump -> ham, waist plateau, shoulder) so neighbouring rings do not step in and out (the rib bands);
    # tops and bellies re-read as one smooth (monotone cubic) curve through the side-outline anchors
    tb('R0', (0.605, 0.64), (0.594, 0.4), 0.14, BODY),
    tb('R1', (0.565, 0.675), (0.56, 0.365), 0.20, BODY),
    tb('Rb', (0.465, 0.715), (0.465, 0.31), 0.238, BODY),
    tb('R2', (0.37, 0.744), (0.37, 0.303), 0.252, BODY),
    tb('R3', (0.29, 0.775), (0.29, 0.3), 0.248, BODY),
    tb('W0', (0.21, 0.808), (0.21, 0.299), 0.238, BODY),
    tb('W1', (0.13, 0.84), (0.13, 0.298), 0.234, BODY),
    tb('M0', (0.05, 0.868), (0.05, 0.298), 0.237, BODY),
    tb('M1', (-0.03, 0.896), (-0.03, 0.302), 0.246, BODY),
    tb('C0', (-0.075, 0.911), (-0.075, 0.307), 0.256, BODY),
    tb('Cb', (-0.165, 0.926), (-0.17, 0.32), 0.262, BODY),
    tb('C1', (-0.245, 0.915), (-0.265, 0.345), 0.245, BODY),
    tb('N0', (-0.305, 0.89), (-0.345, 0.39), 0.22, HEADB),
    tb('N1', (-0.33, 0.878), (-0.375, 0.42), 0.21, HEADB),
    tb('H0', (-0.395, 0.848), (-0.425, 0.45), 0.19, HEADB),
    tb('Hx', (-0.44, 0.815), (-0.465, 0.46), 0.172, HEADB),
    tb('H1', (-0.49, 0.775), (-0.505, 0.466), 0.145, HEAD),
    tb('Hy', (-0.54, 0.735), (-0.555, 0.47), 0.118, HEAD),
    tb('H2', (-0.59, 0.70), (-0.60, 0.475), 0.095, MUZ),
    tb('H3', (-0.65, 0.66), (-0.652, 0.49), 0.074, MUZ),
    tb('Hz', (-0.685, 0.638), (-0.685, 0.495), 0.068, MUZ),
    tb('H4', (-0.71, 0.62), (-0.708, 0.50), 0.064, MUZ),
]

# limb sections: (centre xyz, rx, ry) — horizontal octagons (3x3 roles), deeper front-to-back. Pass 3: the pass-2
# radii kept (leg length x0.9, radii x1.2, upper legs x1.25, already baked in), with new stations where the leg
# outline curves: upper arm / ham under the body, lower forearm / gaskin taper, the narrow coronet above the hoof.
FORE = [((0.135, -0.163, 0.30), 0.085, 0.105), ((0.122, -0.165, 0.24), 0.1, 0.10),
        ((0.12, -0.168, 0.16), 0.088, 0.0966), ((0.117, -0.169, 0.13), 0.076, 0.08),
        ((0.115, -0.17, 0.10), 0.0624, 0.066), ((0.115, -0.172, 0.068), 0.06, 0.064),
        ((0.115, -0.175, 0.045), 0.066, 0.0744), ((0.115, -0.185, 0.0), 0.072, 0.084)]
HIND = [((0.14, 0.455, 0.30), 0.085, 0.112), ((0.127, 0.46, 0.24), 0.1, 0.11),
        ((0.12, 0.475, 0.16), 0.09, 0.1104), ((0.117, 0.48, 0.13), 0.078, 0.085),
        ((0.115, 0.485, 0.10), 0.0624, 0.066), ((0.115, 0.48, 0.068), 0.06, 0.064),
        ((0.115, 0.475, 0.045), 0.066, 0.0744), ((0.115, 0.465, 0.0), 0.072, 0.084)]
FORE = [(lz(c), rx, ry) for c, rx, ry in FORE]
HIND = [(lz(c), rx, ry) for c, rx, ry in HIND]
EAR = [(dz(c), rx, ry, d) for c, rx, ry, d in [((0.155, -0.35, 0.89), 0.05, 0.05, 0.025), ((0.17, -0.335, 0.955), 0.01, 0.008, 0.0)]]


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


def role_pos(sec, u, s, corner=0.72):
    """u across the ring (+1 outer), s front/back (+1 rear); a corner role (both non-zero) sits at `corner`."""
    c, rx, ry = sec[0], sec[1], sec[2]
    dz_ = sec[3] if len(sec) > 3 else 0.0
    k = corner if (u and s) else 1.0
    return (c[0] + u * rx * k, c[1] + s * ry * k, c[2] - u * dz_)


def grow(bm, faces, roles, secs, corner=0.72):
    """Extrude a face region section by section; each new vertex keeps the role (u across the ring, s front/back)
    of the vertex it was extruded from. roles: [(position, (u, s))] — positions, since a region's interior vertex
    is deleted by the extrude."""
    for sec in secs:
        r = extrude(bm, faces)
        new = []
        for v in r['verts']:
            ro = min(roles, key=lambda o: (o[0] - v.co).length)[1]
            new.append((v, ro))
        for v, (u, s) in new:
            v.co = Vector(role_pos(sec, u, s, corner))
        faces, roles = r['faces'], [(v.co.copy(), ro) for v, ro in new]
    return faces, roles


def stage1(k):
    bm = bmesh.new()
    idx = {nm: i for i, (nm, *_r) in enumerate(SECS)}
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)

    def limb(rear, secs):
        i = idx[rear]               # rings i (rear), i+1 (mid), i+2 (front): a 2x2 face window
        a, b, c = LJ
        roles = []
        for r_, s in ((rings[i], 1), (rings[i + 1], 0), (rings[i + 2], -1)):
            roles += [(r_[a].co.copy(), (1, s)), (r_[b].co.copy(), (0, s)), (r_[c].co.copy(), (-1, s))]
        grow(bm, [spans[i][a], spans[i][b], spans[i + 1][a], spans[i + 1][b]], roles, secs)

    limb('C0', FORE)
    limb('R1', HIND)
    i = idx['N1']
    rr, rf = rings[i], rings[i + 1]
    a, b = EAR_J
    grow(bm, [spans[i][a]], [(rf[a].co.copy(), (-1, -1)), (rf[b].co.copy(), (1, -1)),
                             (rr[a].co.copy(), (-1, 1)), (rr[b].co.copy(), (1, 1))], EAR, corner=1.0)
    snap_seam(bm)
    return object_from_bm('body', bm)


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


SOCKET = []   # fix pass 5: socket floor centre and the eye face normal, set in stage 2 for the stage-3 lens


def stage2(k, body):
    ec0 = Vector(EYE0)
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.035 and abs(c.y - ec0.y) < 0.035
                                        and abs(c.z - ec0.z) < 0.05)
    bm = edit(body)
    mid = lambda a, b: tuple((Vector(a) + Vector(b)) / 2)
    with k.topo(bm, 'loop', 'elbow: a second ring between elbow and forearm so the elbow bends, not kinks'):
        loopcut(bm, edge_near(bm, mid(role_pos(FORE[1], 1, 0), role_pos(FORE[2], 1, 0))), t=0.5)
    with k.topo(bm, 'loop', 'stifle: a second ring between stifle and gaskin for the hind-leg bend'):
        loopcut(bm, edge_near(bm, mid(role_pos(HIND[1], 1, 0), role_pos(HIND[2], 1, 0))), t=0.5)
    with k.topo(bm, 'loop', 'neck: a ring between C1 and N0 so the head-down charge bends the short neck'):
        loopcut(bm, edge_near(bm, mid(P('C1')[0], P('N0')[0])), t=0.5)
    f = face_near(bm, ec0, n=(1, 0, 0))
    fn = f.normal.copy()
    brow = max(f.verts, key=lambda v: v.co.z - v.co.y)       # the eye face's front top corner
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face, under the brow'):
        inner = inset(bm, [f], 0.12, 0.0)
    ev = list(inner[0].verts)
    # fix pass 5: a shallow, open socket (was 0.3 inset, 1.2 cm deep, squashed: a narrow slot that swallowed the eye)
    move(ev, -fn * 0.004)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    # brow: the front top corner of the eye face forward and out (fix pass 1: the cheek push-out dropped)
    move([brow], (0.008, -0.012, 0.004))
    # deliberate planes on the snout: one flat side, one flat bridge
    MZ = ('H2', 'H3', 'Hz', 'H4')
    flatten([vert_near(bm, P(nm)[j]) for nm in MZ for j in (4, 5, 6)])
    flatten([vert_near(bm, P(nm)[j]) for nm in MZ for j in (0, 1, 2)])
    # s2 r2: the thin tail spans made needle triangles: tail rings 1.5x wider (a fuller stalk and tuft, as the ref rear)
    for nm in ('T0', 'T1', 'Tm', 'T2', 'T3'):
        scale([vert_near(bm, q) for q in P(nm)], (1.5, 1.0, 1.0), pivot=(0.0, 0.0, 0.0))
    # poly pass 3: the 12-vertex tail rings over the long tail spans made needle quads (slivers 3.8 %): one ring in
    # each long span (tuft and stalk), the tuft a little wider still
    scale([vert_near(bm, q) for nm in ('T0', 'T1') for q in P(nm)], (1.3, 1.0, 1.0), pivot=(0.0, 0.0, 0.0))
    for a_, b_, why in (('T0', 'T1', 'tuft'), ('T2', 'T3', 'stalk')):
        with k.topo(bm, 'loop', f'tail {why}: a ring in the long {a_}-{b_} span (no needle quads)'):
            loopcut(bm, edge_near(bm, mid(P(a_)[0], P(b_)[0])), t=0.5)
    # s2 r2: shoulder and ham bulge: the flank vertices just above each leg-root window out 2 cm (the ref plan
    # view's shoulder and hip width)
    move([vert_near(bm, P(nm)[j]) for nm in ('C0', 'Cb', 'C1', 'R1', 'Rb', 'R2') for j in (5, 6)], (0.02, 0.0, 0.0))
    # fix pass 6 (owner crops: leg-join speck, dark crease, ear join): the first ring of each leg and ear overhung
    # its 2x2 / 1-face root window (4 cm past the window front/back, the inner side 8 cm in under the belly), so the
    # root walls folded back up against the body (adjacent faces at -0.97): a knife crease that caught a white
    # glint. The root ring now sits inside its window footprint, the inner side lower, so the walls drop clean;
    # the outer side 1.5 cm out, flush under the flank (no dark overhang ledge). Fore: the mid
    # pair 1.5 cm out, else the rear wall's middle vertex lines up with C0 j8-j9 into a needle triangle.
    for sec, cy, ry, xin in ((FORE[0], -0.175, 0.085, 0.072), (HIND[0], 0.455, 0.076, 0.072)):
        (cx, _cy, cz), rx = sec[0], sec[1]
        for u in (-1, 0, 1):
            for s in (-1, 0, 1):
                if u == 0 and s == 0:
                    continue
                k_ = 0.72 if (u and s) else 1.0
                v = vert_near(bm, role_pos(sec, u, s))
                x = cx + u * k_ * (rx + 0.015 if u >= 0 else cx - xin) + (0.015 if (u == 0 and sec is FORE[0]) else 0.0)
                v.co = Vector((x, cy + s * ry * k_, cz - (0.03 if u < 0 else 0.0)))
    # the window's inner edge (j9 of its three rings) 2 cm in and 2.5 cm down, so the leg's inner wall drops
    # steeply from it instead of tucking flat under the belly
    move([vert_near(bm, P(nm)[9]) for nm in ('C0', 'Cb', 'C1', 'R1', 'Rb', 'R2')], (-0.02, 0.0, -0.025))
    e0 = EAR[0]
    for u in (-1, 1):
        for s in (-1, 1):
            v = vert_near(bm, role_pos(e0, u, s, 1.0))
            v.co = Vector(role_pos(((e0[0][0] + 0.005, -0.366, e0[0][2] - 0.03), 0.037, 0.033, 0.025), u, s, 1.0))
    # weakfix 2026-10-23: the hind legs stood 3-8 cm apart down their whole length (a narrow slit under the tail,
    # rear view); the sheet's hams meet, then the lower legs part with clear space. The hind leg below the stifle
    # moves out HSPREAD (ramped in from the stifle ring), the hams stay.
    for v in bm.verts:
        w = hspread_w(v.co)
        if w > 0:
            v.co.x += HSPREAD * w
    commit(body, bm)


HSPREAD = 0.024
SPREAD_DONE = []


def hspread_w(co):
    z0, z1 = HIND[1][0][2], HIND[2][0][2]
    if co.x <= 0.02 or not (0.33 < co.y < 0.60) or co.z >= z0:
        return 0.0
    return min(1.0, (z0 - co.z) / (z0 - z1))

# colours picked off the reference sheet: grey-brown flank, dark crest/saddle, pale jowl and snout, light-brown legs
PAL = {'fur': '#8a7b70', 'saddle': '#554b46', 'cream': '#bcb2a8', 'leg': '#9c8a7c', 'hoof': '#262321',
       'snout': '#b08c88', 'tusk': '#ece3cc', 'eye': '#a8702e'}


def body_rule(c, n, i):
    x, y, z = abs(c.x), c.y, c.z - DZ       # trunk thresholds in the pre-drop frame
    zl = c.z / LZ                            # leg thresholds in the pre-shortening frame
    if y < -0.695 and n.y < -0.6:
        return 'snout'                                  # the flat snout disc
    if z > 0.86 and -0.43 < y < -0.27 and x > 0.09:
        return 'saddle'                                 # ears
    if zl < 0.045 and x > 0.03:
        return 'hoof'                                   # hooves: the ring below the pastern
    if SOCKET and (Vector((x, c.y, c.z)) - SOCKET[0]).length < 0.028:
        return 'fur'                                    # fix pass 5: the socket in plain head fur, not cream
    if y > 0.66 and z < 0.43:
        return 'saddle'                                 # dark tail tuft
    if zl < 0.24 and x > 0.03:
        return 'leg'                                    # lower legs, light brown
    if -0.56 < y < -0.36 and z < 0.74 and not (n.z > 0.6 and y > -0.55):
        return 'cream'                                  # pale jowl, cheek and snout
    if n.z < -0.45 and z < 0.40 and -0.30 < y < 0.45:
        return 'leg'                                    # belly, lighter
    if z > 0.70 and n.z > 0.35 and -0.43 < y < 0.58:
        return 'saddle'                                 # dark crest and back
    return 'fur'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A low-poly eye: back cone, iris ring, pupil fan."""
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


def clump(bm, a, n, lay, s, L):
    """A bristle clump: a square base sunk in the body, a mid section standing off the surface, a blunt
    narrow tip laid back along `lay`."""
    n, lay = Vector(n).normalized(), Vector(lay).normalized()
    u = n.cross(lay).normalized(); w = u.cross(n)
    b = a - n * 0.03
    base = [bm.verts.new(b + u * su * s + w * sw * s) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    sn = 0.45 * s
    m = a + n * (0.9 * sn) + lay * L * 0.4
    mid = [bm.verts.new(m + u * su * s * 0.8 + n * sv * sn) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    t = a + n * L * 0.32 + lay * L
    tip = [bm.verts.new(t + u * su * s * 0.14 + n * sv * s * 0.12) for su, sv in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    shell = base + mid + tip
    lo = min(v.co.x for v in shell)
    if lo < 0.003:                                  # never across the mirror plane
        for v in shell:
            v.co.x += 0.003 - lo
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip[(j + 1) % 4], tip[j]])
    bm.faces.new(tip)


def surf(a, b, t, jf):
    """A point on the loft between sections a and b (t from a to b) at fractional ring index jf, and its
    outward normal (radial from the interpolated section centre)."""
    A, Bq = P(a), P(b)
    j0 = min(int(jf), 4); f = jf - j0
    pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
    p = pa.lerp(pb, t)
    ca = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == a][0]))
    cb = Vector((0.0, *[sc for (n_, sc, *_r) in SECS if n_ == b][0]))
    c = ca.lerp(cb, t)
    return p, (p - c).normalized()


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def clumps(spec, tree):
    """spec: [(a, b, t, jf, lay, s, L)] -> one mirrored piece, each clump rooted on the nearest body point."""
    bm = bmesh.new()
    for a, b, t, jf, lay, s_, L_ in spec:
        p, n_ = surf(a, b, t, jf)
        loc, fn, _i, _d = tree.find_nearest(p)
        clump(bm, loc, (fn + n_).normalized(), Vector(lay), s_, L_)
    return bm


def tusk(bm, root, pts, w):
    """A curved triangular-prism tusk: a root ring sunk in the lower jaw, rings along pts tapering to a blunt tip
    (fix pass 1: the thin square tusk read as a whisker at az0)."""
    rings_ = []
    allp = [root] + pts
    for i, p in enumerate(allp):
        p = Vector(p)
        d = (Vector(allp[min(i + 1, len(allp) - 1)]) - Vector(allp[max(i - 1, 0)])).normalized()
        u = d.cross(Vector((0, 1, 0))).normalized(); v = d.cross(u).normalized()
        r = w[i]
        rings_.append([bm.verts.new(p + (u * su + v * sv) * r) for su, sv in ((-1.0, -0.6), (1.0, -0.6), (0.0, 1.1))])
    bm.faces.new(list(reversed(rings_[0])))
    for a, b in zip(rings_, rings_[1:]):
        for j in range(3):
            bm.faces.new([a[j], a[(j + 1) % 3], b[(j + 1) % 3], b[j]])
    bm.faces.new(rings_[-1])


def crest_strip(tree, y0, y1, teeth, w, hi, lo):
    """fix pass 1: the dorsal crest as ONE continuous saw-tooth strip on the midline (the half; the mirror welds
    the x = 0 edge), its base sunk 2 cm into the spine, teeth laid back. Replaces the floating per-side clumps."""
    bm = bmesh.new()
    n = 4 * teeth + 1                                  # per tooth: valley, front slope, tip, back shoulder
    PH = [(lo, 0.0, 0.8), (0.55, 0.0, 0.6), (1.0, 0.02, 0.35), (0.45, 0.0, 0.6)]
    st = []
    for i in range(n):
        y = y0 + (y1 - y0) * i / (n - 1)
        hit = tree.ray_cast(Vector((0.001, y, 1.5)), Vector((0, 0, -1)), 2.0)[0]
        zs = hit.z if hit is not None else 0.8
        fh, back, fw = PH[i % 4]
        env = 1.0 - 0.4 * abs(i - n / 2) / (n / 2)     # tallest over the withers
        h = fh if i % 4 == 0 else fh * hi * env
        yt = y + back                                  # tips lean back
        st.append([bm.verts.new((0.0, y, zs - 0.02)), bm.verts.new((w, y, zs - 0.02)),
                   bm.verts.new((w * fw, yt, zs + h)), bm.verts.new((0.0, yt, zs + h))])
    for a, b in zip(st, st[1:]):
        for j in range(3):
            bm.faces.new([a[j], b[j], b[j + 1], a[j + 1]])
    bm.faces.new([st[0][0], st[0][1], st[0][2], st[0][3]])
    bm.faces.new([st[-1][3], st[-1][2], st[-1][1], st[-1][0]])
    recalc_normals(bm)
    return bm


def toe(bm, h, d):
    """One of the two hoof toes: a root sunk behind the hoof front, a mid ring and a blunt tip on the ground."""
    x0 = h.x + d
    yr, ym, yt = h.y + 0.014, h.y - 0.006, h.y - 0.018
    rows = [[(x0 - 0.02, yr, 0.004), (x0 + 0.02, yr, 0.004), (x0 + 0.02, yr, 0.045), (x0 - 0.02, yr, 0.045)],
            [(x0 - 0.019, ym, 0.002), (x0 + 0.019, ym, 0.002), (x0 + 0.016, ym, 0.034), (x0 - 0.016, ym, 0.034)],
            [(x0 - 0.012, yt, 0.001), (x0 + 0.012, yt, 0.001), (x0 + 0.009, yt, 0.012), (x0 - 0.009, yt, 0.012)]]
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
    tree = body_bvh(body)
    # eyes (fix pass 5, owner: eyes still bad): was a 1.4 cm dark-brown dot sunk in a narrow slot. Now a 1.7 cm
    # amber lens with a big black pupil, centred on the open socket floor, facing the eye face's own normal
    # (out, forward and up, so it reads in the hero and front views), its apex proud of the skin.
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    c.x = abs(c.x)
    n = (n + Vector((0.0, -0.25, 0.0))).normalized()     # a little more to the front for the az0 view
    bm = bmesh.new()
    lens(bm, c + n * 0.002, n, 0.017, 0.011)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'hoof': PAL['hoof']},
          lambda c_, n_, i: 'hoof' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.0095 and n_.dot(n) > 0.5 else 'eye')
    # tusks: curved ivory tusks from the snout side, up and out
    bm = bmesh.new()
    # fix pass 1: rooted low in the jaw, thicker, curving out then up ~20 deg more
    # fix pass 2: tusks x2 long, curling up past the snout top (sheet), root one ring back in the jaw
    tusk(bm, dz((0.05, -0.595, 0.47)), [dz(p) for p in ((0.095, -0.61, 0.49), (0.135, -0.62, 0.54), (0.155, -0.615, 0.61),
                                                        (0.155, -0.595, 0.68), (0.14, -0.57, 0.735))],
         [0.03, 0.029, 0.025, 0.019, 0.012, 0.004])
    tusks = object_from_bm('tusk', bm)
    paint(tusks, {'tusk': PAL['tusk']}, lambda c_, n_, i: 'tusk')
    # dorsal bristle crest: one continuous saw-tooth strip, poll -> mid back, rooted in the spine (fix pass 1)
    cr = object_from_bm('crest', crest_strip(tree, -0.30, 0.22, 6, 0.022, 0.042, 0.01))
    paint(cr, {'saddle': PAL['saddle']}, lambda c_, n_, i: 'saddle')
    # fix pass 1: the pale jowl tuft flared out like a cheek plate / face mask: removed, the cheek is painted cream
    # hoof toes: two per foot, rooted in the hoof front (found by a ray on the body)
    bm = bmesh.new()
    for sole in (FORE[-1], HIND[-1]):
        (cx, cy, _), rx, ry = sole
        if sole is HIND[-1]:
            cx += HSPREAD                       # weakfix: the hind feet moved out with the lower leg
        for d in (-0.022, 0.022):
            o = Vector((cx + d, cy - ry - 0.15, 0.02))
            hit = tree.ray_cast(o, Vector((0, 1, 0)), 0.3)[0]
            h = Vector((cx, hit.y if hit is not None else cy - ry * 0.8, 0.02))
            toe(bm, h, d)
    toes = object_from_bm('toes', bm)
    paint(toes, {'hoof': PAL['hoof']}, lambda c_, n_, i: 'hoof')
    return [eye, tusks, cr, toes]


def stage4(k, body, pieces):
    if not SPREAD_DONE:
        for nm in ('hock', 'hpaw', 'htoe'):
            p = J[nm]
            J[nm] = (p[0] + HSPREAD * hspread_w(Vector((p[0] + 0.001, p[1], p[2]))), p[1], p[2])
        SPREAD_DONE.append(1)
    B = [('hips', J['hips'], J['spine'], None),
         ('spine', J['spine'], J['chest'], 'hips', True),
         ('chest', J['chest'], J['neck'], 'spine', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['nose'], 'neck', True),
         ('ear.L', J['ear'], J['eartip'], 'head'),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('tail2', J['tail2'], J['tail3'], 'tail1', True),
         ('upperarm.L', J['shoulder'], J['elbow'], 'chest'),
         ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
         ('hoof.L', J['wrist'], J['ftoe'], 'forearm.L', True),
         ('thigh.L', J['hipL'], J['knee'], 'hips'),
         ('shin.L', J['knee'], J['hock'], 'thigh.L', True),
         ('foot.L', J['hock'], J['hpaw'], 'shin.L', True),
         ('toe.L', J['hpaw'], J['htoe'], 'foot.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: breathing, a tail flick, one ear twitch, a snout dip
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, 8)},
                       20: {'ear.L': (0, 0, -14), 'head': (4, 0, 0)}, 24: {'tail1': (0, 0, 0)}, 27: {},
                       36: {'chest': (1.5, 0, 0), 'neck': (-1.5, 0, 0), 'tail1': (0, 0, -8)}, 48: {}})
    # move: trot, diagonal pairs (LF + RH, then RF + LH); the swinging leg flexes
    A = 16
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 6)},
        7: {'forearm.R': (-30, 0, 0), 'hoof.R': (-25, 0, 0), 'shin.L': (-18, 0, 0), 'foot.L': (22, 0, 0), 'neck': (2, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0), 'tail1': (0, 0, -6)},
        19: {'forearm.L': (-30, 0, 0), 'hoof.L': (-25, 0, 0), 'shin.R': (-18, 0, 0), 'foot.R': (22, 0, 0), 'neck': (2, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0), 'tail1': (0, 0, 6)}})
    # attack: drop the head, charge forward, then toss the tusks up and to the side
    clip(rig, 'attack', {
        1: {},
        8: {'neck': (12, 0, 0), 'head': (8, 0, 0), 'chest': (-3, 0, 0), 'tail0': (10, 0, 0)},
        16: {'neck': (14, 0, 0), 'head': (10, 0, 0), 'upperarm.L': (12, 0, 0), 'upperarm.R': (12, 0, 0),
             'thigh.L': (-10, 0, 0), 'thigh.R': (-10, 0, 0)},
        20: {'neck': (-8, 0, 6), 'head': (-14, 0, 10), 'upperarm.L': (6, 0, 0), 'upperarm.R': (6, 0, 0)},
        24: {'neck': (-4, 0, 3), 'head': (-6, 0, 4)},
        32: {}},
        loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.03, 0)}, 16: {'hips': (0, -0.06, 0)}, 20: {'hips': (0, -0.07, 0)},
             24: {'hips': (0, -0.03, 0)}, 32: {'hips': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
