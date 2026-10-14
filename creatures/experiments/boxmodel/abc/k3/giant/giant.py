"""Hunched mountain troll (giant), staged box model. Faces -Y, left flank +X, feet on z = 0."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='giant', model='opus')

# the skeleton the model is built on (left side; x >= 0)
J = dict(
    pelvis=(0.0, 0.45, 1.05), spine=(0.0, 0.38, 1.85), chest=(0.0, 0.25, 2.70), neck=(0.0, -0.20, 3.15),
    head=(0.0, -0.62, 2.95), snout=(0.0, -1.15, 2.90),
    hipL=(0.62, 0.52, 1.05), kneeL=(0.64, 0.42, 0.50), ankleL=(0.66, 0.60, 0.22), toeL=(0.72, -0.05, 0.06),
    neckbase=(0.0, -0.30, 3.00), clavL=(0.30, 0.15, 2.95), clavtipL=(1.05, 0.05, 2.90), shoulderL=(1.15, 0.02, 2.85), elbowL=(1.44, -0.25, 2.00),
    wristL=(1.56, -0.42, 1.20), fistL=(1.52, -0.42, 0.35),
)

# torso half-ring profile: (x factor of w, along-u factor; + = back of db, - = front of df)
PROF = [(0.0, 1.0), (0.62, 0.85), (1.0, 0.35), (1.0, -0.30), (0.60, -0.85), (0.0, -1.0)]


def hring(bm, cy, cz, a, w, db, df, xf=None):
    """Half ring p0 (back/top seam) .. p5 (front/bottom seam); ring plane tilted a degrees
    (a = 0: horizontal torso ring, u = +Y; a = 90: vertical head ring, u = +Z)."""
    u = Vector((0.0, math.cos(math.radians(a)), math.sin(math.radians(a))))
    c = Vector((0.0, cy, cz))
    pts = []
    for i, (fx, fs) in enumerate(PROF):
        x = (xf[i] if xf else fx) * w
        s = fs * (db if fs > 0 else df)
        p = c + u * s
        pts.append((x, p.y, p.z))
    return ring(bm, pts)


def face_of(bm, vs):
    s = set(vs)
    for f in vs[0].link_faces:
        if set(f.verts) == s:
            return f
    raise RuntimeError('face_of: no face')


def ext_place(bm, faces, order, targets, seam=False):
    """Extrude a region, move each copy of order[i] to targets[i]; seam=True drops the
    side faces that would lie in the x = 0 plane (a midline extrusion)."""
    pos = [v.co.copy() for v in order]
    r = extrude(bm, faces)
    newv = r['verts']
    new = [min(newv, key=lambda w: (w.co - p).length) for p in pos]
    if seam:
        dead = [f for f in r['sides'] if all(abs(v.co.x) < 1e-6 for v in f.verts)]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
    for v, t in zip(new, targets):
        v.co = Vector(t)
    return r['faces'], new


def frame(d):
    d = Vector(d).normalized()
    L = Vector((0, -1, 0)).cross(d).normalized()
    F = d.cross(L).normalized()
    return L, F


ARM_HEX = [(-1, -0.5), (-1, 0.5), (0, 1), (1, 0.5), (1, -0.5), (0, -1)]      # (lateral, forward)
LEG_HEX = [(-0.85, 0.7), (0.3, 1.0), (1.0, 0.35), (1.0, -0.35), (0.3, -1.0), (-0.85, -0.7)]  # (x, y back)


def arm_sec(c, d, rl, rf, hexp=ARM_HEX):
    L, F = frame(d)
    c = Vector(c)
    return [tuple(c + L * (l * rl) + F * (f * rf)) for l, f in hexp]


def leg_sec(cx, cy, z, rx, ry):
    return [(cx + a * rx, cy + b * ry, z) for a, b in LEG_HEX]


def head_sec(y, zb, zbs, xbs, xs, zs, xts, zts, zt, zm):
    """bottom seam, bottom-side, side, top-side, top seam, mid seam (front centre)."""
    return [(0, y, zb), (xbs, y, zbs), (xs, y, zs), (xts, y, zts), (0, y, zt), (0, y, zm)]


def stage1(k):
    bm = bmesh.new()
    R = [
        hring(bm, 0.47, 0.95, 0, 0.78, 0.40, 0.38, xf=[0, 0.36, 1, 1, 0.36, 0]),   # R0 crotch
        hring(bm, 0.42, 1.38, 0, 0.90, 0.62, 0.55),                                # R1 hips
        hring(bm, 0.35, 1.88, 0, 0.96, 0.70, 0.95, xf=[0, 0.62, 1, 1, 0.72, 0]),   # R2 pot belly
        hring(bm, 0.30, 2.42, 0, 0.92, 0.78, 0.64),                                # R3 chest (tucked under the pecs)
        hring(bm, 0.25, 2.85, 10, 1.00, 0.80, 0.68),                               # R4 shoulders
        hring(bm, 0.05, 3.20, 35, 1.05, 0.85, 0.45),                               # R5 hump
        hring(bm, -0.33, 3.66, 43, 0.70, 0.50, 0.31),                              # R6 hump crest, slope over the head
    ]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    r0, r1 = R[0], R[1]
    cap(bm, [r0[0], r0[1], r0[4], r0[5]])                 # crotch
    cap(bm, [r0[1], r0[2], r0[3], r0[4]])                 # leg root
    cap(bm, list(R[6]))                                   # hump top
    recalc_normals(bm)

    # regions (faces found by their vertices, before any extrusion)
    leg_f = [face_of(bm, [r0[1], r0[2], r0[3], r0[4]]), face_of(bm, [r0[2], r0[3], r1[3], r1[2]])]
    leg_o = [r0[1], r0[2], r1[2], r1[3], r0[3], r0[4]]
    R3, R4, R5, R6 = R[3], R[4], R[5], R[6]
    arm_f = [face_of(bm, [R3[2], R3[3], R4[3], R4[2]]), face_of(bm, [R4[2], R4[3], R5[3], R5[2]])]
    arm_o = [R3[2], R3[3], R4[3], R5[3], R5[2], R4[2]]
    head_f = [face_of(bm, [R4[4], R4[5], R5[5], R5[4]]), face_of(bm, [R5[4], R5[5], R6[5], R6[4]])]
    head_o = [R4[5], R4[4], R5[4], R6[4], R6[5], R5[5]]

    # legs: short, thick, big flat feet
    f, o = leg_f, leg_o
    for sec in (leg_sec(0.63, 0.55, 0.78, 0.33, 0.44),    # thigh (bulk)
                leg_sec(0.64, 0.42, 0.50, 0.27, 0.34),    # knee, forward
                leg_sec(0.66, 0.62, 0.24, 0.23, 0.27),    # ankle, narrow and back
                leg_sec(0.72, 0.45, 0.12, 0.38, 0.47),    # foot top: toes slope down to the front
                leg_sec(0.72, 0.38, 0.00, 0.40, 0.58)):   # sole
        f, o = ext_place(bm, f, o, sec)

    # arms: very long, hanging to the knees, huge fists
    f, o = arm_f, arm_o
    for c, d, rl, rf in (((1.18, 0.02, 2.85), (1, 0, -0.6), 0.40, 0.42),     # deltoid
                         ((1.30, -0.10, 2.45), (0.20, -0.2, -1), 0.30, 0.36), # upper arm
                         ((1.44, -0.25, 2.00), (0.25, -0.25, -1), 0.30, 0.33), # elbow
                         ((1.56, -0.38, 1.60), (0.12, -0.15, -1), 0.40, 0.40), # forearm
                         ((1.56, -0.42, 1.20), (-0.05, -0.05, -1), 0.28, 0.30),   # wrist
                         ((1.52, -0.42, 0.95), (0, 0, -1), 0.36, 0.44),       # fist top
                         ((1.52, -0.42, 0.30), (0, 0, -1), 0.34, 0.42)):      # fist bottom
        f, o = ext_place(bm, f, o, arm_sec(c, d, rl, rf))

    # head: small, set low and forward under the hump
    f, o = head_f, head_o
    for sec in (head_sec(-0.64, 2.55, 2.60, 0.30, 0.38, 2.95, 0.26, 3.30, 3.40, 2.95),   # neck (sunk)
                head_sec(-0.80, 2.42, 2.48, 0.38, 0.38, 2.92, 0.24, 3.28, 3.34, 2.92),   # cheek / eye, wide jaw
                head_sec(-1.00, 2.42, 2.46, 0.32, 0.30, 2.95, 0.18, 3.18, 3.20, 2.95),   # brow front
                head_sec(-1.12, 2.48, 2.52, 0.26, 0.22, 2.88, 0.12, 3.02, 3.06, 2.80)):  # snout
        f, o = ext_place(bm, f, o, sec, seam=True)

    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


def mid(a, b):
    return tuple((Vector(a) + Vector(b)) / 2)


# sections as built in stage 1 (to find edges again; stage1() is locked)
A2 = arm_sec((1.30, -0.10, 2.45), (0.20, -0.2, -1), 0.30, 0.36)
A3 = arm_sec((1.44, -0.25, 2.00), (0.25, -0.25, -1), 0.30, 0.33)
A4 = arm_sec((1.56, -0.38, 1.60), (0.12, -0.15, -1), 0.40, 0.40)
A1 = arm_sec((1.18, 0.02, 2.85), (1, 0, -0.6), 0.40, 0.42)
A6 = arm_sec((1.52, -0.42, 0.95), (0, 0, -1), 0.36, 0.44)
A7 = arm_sec((1.52, -0.42, 0.30), (0, 0, -1), 0.34, 0.42)
S1 = leg_sec(0.63, 0.55, 0.78, 0.33, 0.44)
S2 = leg_sec(0.64, 0.42, 0.50, 0.27, 0.34)
S3 = leg_sec(0.66, 0.62, 0.24, 0.23, 0.27)
H0 = head_sec(-0.64, 2.55, 2.60, 0.30, 0.38, 2.95, 0.26, 3.30, 3.40, 2.95)
H2 = head_sec(-1.00, 2.42, 2.46, 0.32, 0.30, 2.95, 0.18, 3.18, 3.20, 2.95)
H3 = head_sec(-1.12, 2.48, 2.52, 0.26, 0.22, 2.88, 0.12, 3.02, 3.06, 2.80)
R5P4 = (0.63, 0.05 - 0.85 * 0.45 * math.cos(math.radians(35)), 3.20 - 0.85 * 0.45 * math.sin(math.radians(35)))


def near_ring(bm, pts, tol=0.03):
    return [v for v in bm.verts if min((v.co - Vector(p)).length for p in pts) < tol]


def stage2(k, body):
    bm = edit(body)
    cut = lambda a, b, t: loopcut(bm, edge_near(bm, mid(a, b)), t=t, near=vert_near(bm, a))
    with k.topo(bm, 'loop', 'neck ring between the hump and the skull: the neck must bend without collapsing'):
        neck = cut(R5P4, H0[2], 0.55)
    with k.topo(bm, 'loop', 'shoulder loop in the deltoid band: the arm swings from here'):
        sh = cut(A1[2], A2[2], 0.5)
    with k.topo(bm, 'loop', 'elbow loop above the elbow ring: the bend'):
        e1 = cut(A2[2], A3[2], 0.6)
    with k.topo(bm, 'loop', 'elbow loop below the elbow ring: the bend'):
        e2 = cut(A3[2], A4[2], 0.35)
    with k.topo(bm, 'loop', 'knuckle row across the fist'):
        kn = cut(A6[2], A7[2], 0.42)
    with k.topo(bm, 'loop', 'knee loop above the knee ring'):
        k1 = cut(S1[1], S2[1], 0.6)
    with k.topo(bm, 'loop', 'knee loop below the knee ring'):
        k2 = cut(S2[1], S3[1], 0.4)
    with k.topo(bm, 'loop', 'brow ring on the face: the brow ridge overhangs the eyes'):
        brow = cut(H2[2], H3[2], 0.5)

    # --- vertex moves: planes where anatomy turns ---
    for v in brow:                              # brow ridge juts forward over the eyes
        if v.co.z > 3.0:
            v.co.y -= 0.10; v.co.z += 0.05
        elif v.co.x > 0.2:
            v.co.x += 0.04                      # cheekbone
    for v in near_ring(bm, [H3[3], H3[4]]):     # under the brow: sockets set back
        v.co.y += 0.06; v.co.z -= 0.05
    nose = vert_near(bm, H3[5])                 # nose block on the seam
    nose.co.y -= 0.10; nose.co.z += 0.02
    for v in near_ring(bm, [H2[3], H2[4]]):     # low forehead sloping back to the hump
        v.co.z += 0.02
    for v in kn:                                # knuckle ridge forward
        if v.co.y < -0.6:
            v.co.y -= 0.06
    for v in e1 + e2:                           # elbow point back
        if v.co.y > -0.1:
            v.co.y += 0.04
    for v in k1 + k2:                           # kneecap forward
        if v.co.y < 0.2:
            v.co.y -= 0.04
    for v in neck:                              # neck sinks into the shoulders
        v.co.z -= 0.03

    # jaw: underbite, a heavy lower jaw the tusks rise from, with a mouth corner on the muzzle side
    e0 = edge_near(bm, mid(H3[0], H3[5]))
    e2 = edge_near(bm, mid((0.26, -1.06, 2.49), (0.26, -1.06, 2.915)))
    with k.topo(bm, 'partial_loop', 'mouth corner on the muzzle side, terminated on the muzzle (no bend there)'):
        mc = partial_loop(bm, e0, e2, t=0.45, terminate='fan')
    for v in mc:
        v.co.y += 0.05; v.co.x -= 0.02
    for v in near_ring(bm, [H3[0], H3[1]]):     # chin and jaw corner jut forward
        v.co.y -= 0.08; v.co.z -= 0.02
    for v in near_ring(bm, [H2[0], H2[1]]):
        v.co.y -= 0.04
    # hump crest: the R6 lid was one flat plane; lift its midline (and the lip over the head) into a ridge
    nl = Vector((0, -math.sin(math.radians(43)), math.cos(math.radians(43))))
    for p, d in (((0.0, 0.035, 4.0), 0.10), ((0.0, -0.556, 3.449), 0.12),
                 ((0.434, -0.019, 3.95), 0.05), ((0.42, -0.523, 3.48), 0.06)):
        vert_near(bm, p).co += nl * d
    # AD item 2: the brow overhangs the eyes more; the lower jaw front is one plane
    for v in brow:
        if v.co.z > 3.0:
            v.co.y -= 0.03; v.co.z -= 0.012
    # (the lower jaw front is already one plane: chin, jaw corner and mouth corner form one fan triangle)
    # eye sockets, cut after the brow moved
    hm_ts = min(brow, key=lambda v: (v.co - Vector((0.16, -1.16, 3.15))).length)
    with k.topo(bm, 'inset', 'eye socket under the brow: a loop inside one face'):
        fe = face_near(bm, (0.17, -1.10, 3.00), n=(0.3, -1, 0))
        inset(bm, [fe], 0.35, depth=-0.03)
    # pot belly: the R2 ring's front half forward and a little out (AD item 4)
    for p, dy, dx in (((0.0, -0.60, 1.88), -0.08, 0.0), ((0.6912, -0.4575, 1.88), -0.08, 0.02),
                      ((0.96, 0.065, 1.88), -0.03, 0.02)):
        v = vert_near(bm, p)
        v.co.y += dy; v.co.x += dx
    # AD item 1: the fist. A knuckle ridge loop round the fist top, then three finger grooves down the front.
    kn_mid = min(kn, key=lambda v: (v.co - Vector(A6[2]) + Vector((0, 0, 0.27))).length)   # kn vert under A6 h2
    with k.topo(bm, 'loop', 'knuckle ridge round the top of the fist (between the fist top and the finger row)'):
        kr = loopcut(bm, edge_near(bm, mid(A6[2], tuple(kn_mid.co))), t=0.5, near=vert_near(bm, A6[2]))
    fc = Vector((1.52, -0.42, 0.0))
    for v in kr:                                 # ridge out 4% of the fist width, the front a little more
        r = Vector((v.co.x - fc.x, v.co.y - fc.y, 0)).normalized()
        v.co += r * 0.03
        if v.co.y < -0.6:
            v.co.y -= 0.02
    grooves = []
    for a, b, c, d, t in ((1, 2, 5, 0, 0.42), (2, 3, 4, 5, 0.58)):
        va = min(kr, key=lambda v: (Vector((v.co.x, v.co.y)) - Vector(A6[a][:2])).length)
        vb = min(kr, key=lambda v: (Vector((v.co.x, v.co.y)) - Vector(A6[b][:2])).length)
        s_e = next(e for e in va.link_edges if vb in e.verts)
        e_e = edge_near(bm, mid(A7[c], A7[d]))
        with k.topo(bm, 'partial_loop', 'finger groove down the front of the fist, fan-terminated in the knuckle band and under the fist'):
            grooves += partial_loop(bm, s_e, e_e, t=t, terminate='fan')
    for v in grooves + [vert_near(bm, (A7[2][0], A7[2][1] + 0.0, A7[2][2]))] + \
            [min(kn, key=lambda v: (Vector((v.co.x, v.co.y)) - Vector(A6[2][:2])).length)]:
        v.co.y += 0.035                          # grooves cut in about 5% of the fist width
    # ankles narrower than the calves: the S3 ring to 85% about its centre
    anc = Vector((0.66, 0.62, 0.24))
    for v in near_ring(bm, S3):
        v.co.x = anc.x + (v.co.x - anc.x) * 0.85
        v.co.y = anc.y + (v.co.y - anc.y) * 0.85
    # AD r2 item 2: the mid-face sat 0.13-0.16 behind the brow and the nose tip (a recessed mask in shadow).
    # Pull the nose bridge and ridge forward, the cheek tops forward and up, and flatten one cheek plane a side.
    for p, dy, dz in (((0.0, -1.06, 3.01), -0.03, 0.0),
                      ((0.0, -1.22, 2.82), -0.02, 0.006), ((0.22, -1.12, 2.88), -0.03, 0.01),
                      ((0.30, -1.06, 2.915), -0.03, 0.01)):
        v = vert_near(bm, p)
        v.co.y += dy; v.co.z += dz
    flatten([vert_near(bm, p) for p in ((0.22, -1.15, 2.89), (0.30, -1.09, 2.925), (0.222, -1.07, 2.682), (0.26, -1.2, 2.5))])
    commit(body, bm)


PAL ={'hide': '#66727f', 'dark': '#343b46', 'stone': '#8b867c', 'moss': '#6f8f3a',
       'leather': '#a58c67', 'cloth': '#6e5236', 'tusk': '#d6c9a6', 'eye': '#ffcc3a'}


def prism(bm, base, axis, rx, ry, h, n=6, top=0.8, start=0.0, jit=None):
    """A closed low-poly slab/rock/box: an n-gon ring at base, a smaller one h along axis, both capped."""
    a = Vector(axis).normalized()
    ref = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((0, 1, 0))
    e1 = ref.cross(a).normalized()
    e2 = a.cross(e1).normalized()
    b = Vector(base)
    lo, hi = [], []
    for i in range(n):
        th = math.radians(start) + i * 2 * math.pi / n
        j = jit[i % len(jit)] if jit else 1.0
        off = e1 * (math.cos(th) * rx * j) + e2 * (math.sin(th) * ry * j)
        lo.append(b + off)
        hi.append(b + a * h + off * top)
    L, H = ring(bm, lo), ring(bm, hi)
    bridge(bm, L, H, closed=True)
    cap(bm, list(reversed(L))); cap(bm, H)


def piece(name, build, pal_rule, mirror=True):
    bm = bmesh.new()
    build(bm)
    recalc_normals(bm)
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, PAL, pal_rule)
    return ob


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    def body_rule(c, n, i):
        if c.z < 0.2:
            return 'dark'                        # soles and feet (the fists take the skin colour, AD r2 item 1)
        if c.y < -1.0 and 2.58 < c.z < 2.75 and abs(c.x) < 0.3 and n.y < -0.4:
            return 'dark'                        # mouth band on the top of the lower jaw
        return 'hide'
    paint(body, PAL, body_rule)
    tree = BVHTree.FromBMesh(evaluated_bm(body))

    def seat(p):
        loc, nrm, _, _ = tree.find_nearest(Vector(p))
        return loc, nrm

    def hit(o, d):
        loc, nrm, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
        return loc

    out = []
    # eyes: amber lenses proud of the sockets under the brow
    def eyes(bm):
        loc, n = seat((0.175, -1.14, 3.0))
        n = (n + Vector((0.15, -1, 0))).normalized()          # face the front, a touch outward
        prism(bm, loc - n * 0.02, n, 0.11, 0.06, 0.04, n=5, top=0.7, start=90)   # AD r2: 1.4x wider again
    out.append(piece('eyes', eyes, lambda c, n, i: 'eye'))
    # tusks rising from the lower jaw: base ring, bent mid ring, a single tip (no needle quads)
    def tusks(bm):
        # short thick tusks (AD item 2): base 1.6x, tip at the nose line below the eyes, curving outward
        base = [(0.19 + dx, -1.10 + dy, 2.54) for dx, dy in ((0.088, 0), (0, -0.08), (-0.088, 0), (0, 0.08))]
        midr = [(0.235 + dx * 0.7, -1.19 + dy * 0.7, 2.67) for dx, dy in ((0.088, 0), (0, -0.08), (-0.088, 0), (0, 0.08))]
        B, M = ring(bm, base), ring(bm, midr)
        tip = bm.verts.new((0.29, -1.25, 2.79))
        bridge(bm, B, M, closed=True)
        for i in range(4):
            bm.faces.new([M[i], M[(i + 1) % 4], tip])
        cap(bm, list(reversed(B)))
    out.append(piece('tusks', tusks, lambda c, n, i: 'tusk'))
    # AD item 3: a moss mantle of three irregular draped plates per side (7-9 sided, no two alike) that follow the
    # hump, sunk ~40% of their thickness with tapered edges, and big rocks bedded half into it
    def drape(bm, p, rx, ry, jit, t=0.11, spin=0.0):
        loc, N = seat(p)
        e1 = (Vector((1, 0, 0)) - N * N.x).normalized()
        e2 = N.cross(e1).normalized()
        nn = len(jit)
        def on_skin(q, lift):
            l, nr = seat(q)
            return l + nr * lift
        outer, midt, midb = [], [], []
        for i in range(nn):
            th = math.radians(spin) + i * 2 * math.pi / nn
            d = e1 * (math.cos(th) * rx * jit[i]) + e2 * (math.sin(th) * ry * jit[i])
            outer.append(on_skin(loc + d, -0.008))                  # the edge tucks under the skin: tapered
            midt.append(on_skin(loc + d * 0.75, t * 0.6))          # sunk 40% of the thickness
            midb.append(on_skin(loc + d * 0.75, -t * 0.4))
        O = ring(bm, [tuple(q) for q in outer])
        MT = ring(bm, [tuple(q) for q in midt])
        MB = ring(bm, [tuple(q) for q in midb])
        ct = bm.verts.new(tuple(loc + N * t * 0.65))
        cb = bm.verts.new(tuple(loc - N * t * 0.4))
        bridge(bm, O, MT, closed=True)
        bridge(bm, MB, O, closed=True)
        for i in range(nn):
            j = (i + 1) % nn
            bm.faces.new([MT[i], MT[j], ct])
            bm.faces.new([MB[j], MB[i], cb])
    def moss(bm):
        drape(bm, (0.36, 0.10, 3.98), 0.40, 0.62, [1, 0.8, 1.1, 0.95, 0.75, 1.05, 0.9, 1.15, 0.85], spin=10)     # crest
        drape(bm, (0.80, 0.35, 3.50), 0.30, 0.50, [0.9, 1.1, 0.8, 1.05, 1.0, 0.7, 1.1, 0.95], spin=35)           # shoulder
        drape(bm, (0.46, -0.40, 3.62), 0.36, 0.30, [1.1, 0.8, 1.0, 0.75, 1.15, 0.9, 1.0], spin=5)                # front lip
    out.append(piece('moss', moss, lambda c, n, i: 'moss'))
    def rocks(bm):
        for p, r, h in (((0.62, -0.30, 3.62), 0.22, 0.20), ((0.30, 0.45, 3.92), 0.28, 0.24), ((0.62, 0.95, 3.25), 0.24, 0.22)):
            loc, n = seat(p)
            prism(bm, loc - n * h * 0.5, n, r, r * 0.78, h, n=6, top=0.66, start=15, jit=[1, 0.8, 1.1, 0.9, 1.0, 0.85])
    out.append(piece('rocks', rocks, lambda c, n, i: 'stone'))
    # belt: follows the body section under the belly, sunk into it (one band)
    def belt(bm):
        rows = [[], [], [], []]
        N = 16
        for i in range(N):
            th = i * 2 * math.pi / N
            d = Vector((math.sin(th), -math.cos(th), 0))
            z = 1.56 - 0.06 * math.cos(th)
            loc = hit((0, 0.40, z), d)
            for r, (dz, dd) in zip(rows, ((-0.07, -0.04), (-0.07, 0.05), (0.07, 0.05), (0.07, -0.04))):
                r.append(loc + d * dd + Vector((0, 0, dz)))
        R = [ring(bm, [tuple(p) for p in r]) for r in rows]
        for a, b in zip(R, R[1:] + R[:1]):
            bridge(bm, a, b, closed=True)
    out.append(piece('belt', belt, lambda c, n, i: 'leather', mirror=False))
    # loincloth flaps, front and back, hanging clear of the body: quad-strip plates with real thickness
    def plate(rows, t):
        def build(bm):
            F = [ring(bm, [(-w, y, z), (0, y - bow, z), (w, y, z)]) for w, y, z, bow in rows]
            B = [ring(bm, [(-w, y + t, z), (0, y + t - bow, z), (w, y + t, z)]) for w, y, z, bow in rows]
            for r in range(len(rows) - 1):
                bridge(bm, F[r], F[r + 1]); bridge(bm, B[r + 1], B[r])
                for c in (0, 2):
                    bm.faces.new([F[r][c], F[r + 1][c], B[r + 1][c], B[r][c]])
            bridge(bm, F[0], B[0]); bridge(bm, B[-1], F[-1])
        return build
    # AD r2 item 3: wide cloth slabs front and back (closed shells, ~5% of their width thick), wrapping round the
    # hips, to mid-thigh, with a jagged hem of three uneven points; a darker brown than the belt
    def cloth(rows, t, hem):
        U = [-1, -0.66, -0.33, 0, 0.33, 0.66, 1]
        def build(bm):
            F, B = [], []
            for r, (w, y, z, bow, wrap) in enumerate(rows):
                last = r == len(rows) - 1
                pts = [(u * w, y - bow * (1 - u * u) + wrap * u * u, z + (hem[k] if last else 0)) for k, u in enumerate(U)]
                F.append(ring(bm, pts))
                B.append(ring(bm, [(px, py + t, pz) for px, py, pz in pts]))
            for r in range(len(rows) - 1):
                bridge(bm, F[r], F[r + 1]); bridge(bm, B[r + 1], B[r])
                bm.faces.new([F[r][0], F[r + 1][0], B[r + 1][0], B[r][0]])
                bm.faces.new([F[r][-1], B[r][-1], B[r + 1][-1], F[r + 1][-1]])
            bridge(bm, F[0], B[0]); bridge(bm, B[-1], F[-1])
        return build
    out.append(piece('loin_front', cloth([(0.58, -0.40, 1.56, 0.02, 0.10), (0.56, -0.35, 1.30, 0.02, 0.12),
                                          (0.52, -0.25, 1.06, 0.02, 0.12), (0.48, -0.16, 0.90, 0.02, 0.10)], 0.06,
                                         [0.0, -0.10, 0.02, -0.16, 0.0, -0.08, 0.03]),
                     lambda c, n, i: 'cloth', mirror=False))
    out.append(piece('loin_back', cloth([(0.60, 1.10, 1.64, -0.02, -0.08), (0.58, 1.16, 1.36, -0.02, -0.08),
                                         (0.54, 1.21, 1.10, -0.02, -0.07), (0.50, 1.25, 0.92, -0.02, -0.06)], -0.06,
                                        [0.02, -0.12, 0.0, -0.09, 0.03, -0.15, 0.0]),
                     lambda c, n, i: 'cloth', mirror=False))
    nails = lambda c, n, i: 'stone' if n.y < -0.7 else 'dark'
    # AD r2 item 1: four skin-coloured fingers, 2-segment curled boxes rooted ~30% into the lower front of the
    # fist below the knuckle ridge, curling back toward the fist bottom, a small raised stone nail on each tip
    nail_c = []
    def fingers(bm):
        up = Vector((0, 0, 1))
        for x, hw in ((1.25, 0.066), (1.425, 0.080), (1.615, 0.078), (1.79, 0.062)):
            def front(z):
                loc, nrm, _, _ = tree.ray_cast(Vector((x, -0.42, z)), Vector((0, -1, 0)))
                nh = Vector((nrm.x, nrm.y, 0)).normalized()
                return loc, nh
            p0, n0 = front(0.68)
            p1, n1 = front(0.52)
            p2, n2 = front(0.40)
            nh = (n0 + n1 + n2).normalized()
            Lh = up.cross(nh).normalized()
            cs = [p0 - nh * 0.06, p1 + nh * 0.12, p2 + nh * 0.11 + Vector((0, 0, -0.02)), p2 + nh * 0.07 + Vector((0, 0, -0.12))]
            ws = [hw, hw * 1.08, hw * 0.96, hw * 0.86]
            hs = [0.075, 0.08, 0.072, 0.06]
            rings = []
            for i, (c, w, h) in enumerate(zip(cs, ws, hs)):
                t = (cs[min(i + 1, 3)] - cs[max(i - 1, 0)]).normalized()
                T = Lh.cross(t).normalized()
                if T.dot(nh) < 0:
                    T = -T
                rings.append(ring(bm, [tuple(c + Lh * (w * a) + T * (h * b)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]))
            segs = [bridge(bm, a, b, closed=True) for a, b in zip(rings, rings[1:])]
            cap(bm, list(reversed(rings[0]))); cap(bm, rings[-1])
            recalc_normals(bm)
            tipf = max(segs[2], key=lambda f: f.normal.dot(nh))
            r = bmesh.ops.inset_individual(bm, faces=[tipf], thickness=0.022, depth=0.012)
            nail_c.append(tipf.calc_center_median().copy())
    out.append(piece('fingers', fingers, lambda c, n, i: 'stone' if min((c - q).length for q in nail_c) < 0.02 else 'hide'))
    def thumbs(bm):
        loc = hit((1.52, -0.52, 0.72), (-1, 0, 0))
        ax = Vector((-0.45, -1.0, -0.35)).normalized()
        prism(bm, loc + Vector((0.08, 0.05, 0.02)), ax, 0.095, 0.10, 0.34, n=5, top=0.72, start=90)
    out.append(piece('thumbs', thumbs, lambda c, n, i: 'stone' if n.dot(Vector((-0.45, -1.0, -0.35)).normalized()) > 0.8 else 'hide'))
    def toes(bm):
        for x, rx in ((0.52, 0.13), (0.70, 0.095), (0.85, 0.075)):
            ys = hit((x, 0.40, 0.07), (0, -1, 0)).y
            prism(bm, (x, ys + 0.05, 0.07), (0, -1, 0), rx, 0.07 if rx > 0.1 else 0.06, 0.15, n=4, top=0.85, start=45)
    out.append(piece('toes', toes, nails))
    return out


def stage4(k, body, pieces):
    rig = armature([
        ('hips', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neckbase'], J['head'], 'chest'),
        ('head', J['head'], J['snout'], 'neck', True),
        ('clav.L', J['clavL'], J['clavtipL'], 'chest'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'clav.L'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L', True),
        ('hand.L', J['wristL'], J['fistL'], 'forearm.L', True),
        ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)

    def both(d):          # mirror a left-side key onto the right (bone-local X pitch is shared; Y/Z flip)
        out = dict(d)
        for b, (x, y, z) in d.items():
            if b.endswith('.L'):
                out[b[:-2] + '.R'] = (x, -y, -z)
        return out
    clip(rig, 'idle', {1: {}, 24: both({'spine': (2, 0, 0), 'chest': (3, 0, 0), 'neck': (-3, 0, 0), 'head': (-2, 0, 0),
                                        'upperarm.L': (3, 0, 0), 'forearm.L': (4, 0, 0), 'clav.L': (0, 0, 3)}), 48: {}})
    stepL = {'hips': (0, 4, 0), 'chest': (0, -4, 0), 'thigh.L': (22, 0, 0), 'shin.L': (-8, 0, 0), 'foot.L': (-8, 0, 0),
             'thigh.R': (-16, 0, 0), 'shin.R': (-22, 0, 0), 'upperarm.L': (-14, 0, 0), 'upperarm.R': (14, 0, 0),
             'forearm.L': (6, 0, 0), 'forearm.R': (14, 0, 0)}
    passL = {'hips': (0, 0, 0), 'spine': (3, 0, 0), 'thigh.L': (0, 0, 0), 'shin.L': (-4, 0, 0),
             'thigh.R': (12, 0, 0), 'shin.R': (-40, 0, 0), 'foot.R': (10, 0, 0)}
    def swap(d):
        out = {}
        for b, (x, y, z) in d.items():
            nb = b[:-2] + ('.R' if b.endswith('.L') else '.L') if b[-2:] in ('.L', '.R') else b
            out[nb] = (x, -y, -z) if nb == b else (x, y, z)
        return out
    clip(rig, 'move', {1: stepL, 9: passL, 17: swap(stepL), 25: swap(passL), 33: stepL})
    wind = both({'spine': (-3, 0, 0), 'chest': (-30, 0, 0), 'neck': (14, 0, 0), 'clav.L': (0, 0, 8),
                 'upperarm.L': (85, 0, -27), 'forearm.L': (75, 0, 0)})   # AD r2 item 4: wider, higher
    slam = both({'spine': (4, 0, 0), 'chest': (26, 0, 0), 'neck': (-10, 0, 0), 'clav.L': (0, 0, -4),
                 'upperarm.L': (42, 0, -12), 'forearm.L': (10, 0, 0), 'thigh.L': (8, 0, 0), 'shin.L': (-12, 0, 0)})
    hold = both({'spine': (3, 0, 0), 'chest': (17, 0, 0), 'upperarm.L': (28, 0, 0), 'forearm.L': (8, 0, 0)})
    clip(rig, 'attack', {1: {}, 14: wind, 22: slam, 30: hold, 40: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
