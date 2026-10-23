import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *

# giant spider (t7x zoo): the spine loft of 6-vertex half rings runs abdomen tip -> big round abdomen -> pedicel
# waist -> cephalothorax -> head front. The eight legs are swept hexagon tubes, each grown from its own 2-face
# region (columns 2-3 of one cephalothorax span), so every leg has its own root; the chelicerae (mandibles) are
# 1-face extrusions from the head underside. Leg placement read off the front and top views (the sheet's side is 3/4).
META = dict(creature='spider', detail_tier=1, model='opus', stage1_tris=(1000, 4000), total_tris=(2000, 6000),
            closeups=[('head and chelicerae', (0.07, -0.50, 0.32), 0.2, 'hero'),
                      ('front legs', (0.3, -0.45, 0.3), 0.4, 'hero'),
                      ('abdomen', (0.0, 0.45, 0.5), 0.45, 'az090'),
                      ('leg underside', (0.35, 0.0, 0.25), 0.4, 'hero_low')])

# poly pass 3: 10-vertex half rings (were 6) so the round masses read round
ABD = [(0, 1), (0.36, 0.94), (0.68, 0.76), (0.89, 0.47), (0.995, 0.13), (0.98, -0.2), (0.87, -0.5), (0.68, -0.75),
       (0.4, -0.93), (0, -1)]
CEPH = [(0, 1), (0.4, 0.96), (0.7, 0.85), (0.88, 0.64), (0.97, 0.4), (1.0, 0.13), (0.99, -0.13), (0.92, -0.4),
        (0.6, -0.85), (0, -1)]
HEAD = [(0, 1), (0.4, 0.96), (0.7, 0.85), (0.88, 0.62), (0.97, 0.35), (0.98, 0.03), (0.95, -0.3), (0.8, -0.6),
        (0.55, -0.85), (0, -1)]


def _abd():
    """poly pass 3: abdomen stations re-fitted to the sheet's full round abdomen (blunt rear dome in the top view):
    a superellipse along y, stations denser where the outline turns (the rear dome and the front neck)."""
    out = []
    for n, th in enumerate((8, 20, 33, 47, 62, 77, 92, 107, 122, 136, 150)):
        c = math.cos(math.radians(th))
        R = 0.345 * math.sin(math.radians(th)) ** 0.8
        z = 0.53 - 0.10 * max(0.0, -c - 0.35) / 0.65
        out.append(('AT' if n == 0 else 'A%d' % n, round(0.47 + 0.37 * c, 4), round(z, 4), R, R * 0.96, R * 0.985, ABD))
    return out


# the loft, abdomen tip -> head front: (name, centre (y, z), T, B, W, profile); seam A on top
_S = _abd() + [
      ('Wa', .11, .405, .11, .105, .11, ABD),     # poly pass 3: abdomen neck into the pedicel
      ('W', .075, .39, .075, .075, .075, CEPH),
      ('Wb', .04, .39, .10, .09, .135, CEPH),     # poly pass 3: the carapace shoulder
      ('C0', .00, .39, .13, .11, .19, CEPH), ('C1', -.09, .39, .17, .12, .25, CEPH), ('C2', -.18, .39, .185, .125, .28, CEPH),
      ('C3', -.27, .39, .18, .12, .27, CEPH), ('C4', -.36, .39, .16, .115, .245, CEPH),
      ('Hm', -.405, .39, .14, .116, .216, HEAD),   # poly pass 3: carapace -> head transition
      ('H0', -.445, .39, .125, .115, .205, HEAD), ('H1', -.52, .38, .105, .105, .175, HEAD), ('H2', -.55, .38, .055, .06, .085, HEAD)]
CZ = 0.03   # fix pass 2: cephalothorax, head, waist raised 3 cm (opus: hidden by the legs)
SECS = [(n, (y, z + (0 if n[0] == 'A' else CZ)), 0.0, T, B, W, p) for (n, y, z, T, B, W, p) in _S]
RC = (4, 5, 6, 7)   # poly pass 3: the leg root region, ring vertices 4-7 (3 faces) -> octagon tube

# legs (x >= 0 half): (span = rear ring of the root span, heading deg from -Y toward +X, reach of the tip from the root)
LEGS = [('C3', 24.0, 0.76), ('C2', 58.0, 0.80), ('C1', 122.0, 0.86), ('C0', 150.0, 0.92)]   # fix pass: front swept forward, rear back
# leg sections: (fraction of the reach, centre z, half width); knee high at 0.38, foot on the ground
# poly pass 3: 16 sections (were 9), denser round the knee arch and the joints; octagon tubes
LEG_T = [(0.065, 0.465, 0.040), (0.12, 0.53, 0.047), (0.17, 0.58, 0.052), (0.23, 0.63, 0.056), (0.30, 0.675, 0.060),
         (0.35, 0.70, 0.063), (0.40, 0.705, 0.063), (0.45, 0.675, 0.060), (0.52, 0.54, 0.057), (0.60, 0.38, 0.055),
         (0.66, 0.31, 0.053), (0.72, 0.25, 0.050), (0.79, 0.17, 0.047), (0.86, 0.10, 0.043), (0.93, 0.05, 0.036),
         (1.0, 0.016, 0.026)]
OCT = ((0.924, 0.383), (0.383, 0.924), (-0.383, 0.924), (-0.924, 0.383))   # (S, U) roles of ring vertices 4..7


def LI(f):
    """Index of the leg section nearest the reach fraction f."""
    return min(range(len(LEG_T)), key=lambda i: abs(LEG_T[i][0] - f))


BANDS = (0.235, 0.53, 0.785)     # orange leg bands: the spans whose centre sits at these fractions
# chelicerae: 1-face extrusion from the head underside (H0-H1 span, column 3), hanging forward and down
FANG = [((0.064, -0.53, 0.28), 0.058, 0.062, 0.0), ((0.06, -0.565, 0.23), 0.052, 0.05, 0.0), ((0.054, -0.56, 0.19), 0.03, 0.026, 0.0)]   # fix pass: short bulbous, tucked under the face


def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    return [(fx * W, y0 + fh * (T if fh >= 0 else B) * s, z0 + fh * (T if fh >= 0 else B) * co) for fx, fh in prof]


def P(nm):
    for (n, c, a, T, B, W, p) in SECS:
        if n == nm:
            return [Vector(q) for q in sec_pts(c, a, T, B, W, p)]


IDX = {s[0]: i for i, s in enumerate(SECS)}


def leg_root(spec):
    a, b = P(spec[0]), P(SECS[IDX[spec[0]] + 1][0])
    return (a[5] + a[6] + b[5] + b[6]) / 4


def leg_path(spec):
    """(p, U, S, rw, rh) per section: straight in plan along the heading, knee high, foot on the ground."""
    nm, ph, R = spec
    a = math.radians(ph)
    h = Vector((math.sin(a), -math.cos(a), 0.0))
    r0 = leg_root(spec)
    base = Vector((r0.x, r0.y, 0.0))
    pts = [base + h * (f * R) + Vector((0, 0, z)) for f, z, w in LEG_T]
    out = []
    for i, p in enumerate(pts):
        a_ = pts[i - 1] if i > 0 else r0 - h * 0.03
        b_ = pts[i + 1] if i + 1 < len(pts) else p + (p - pts[i - 1])
        T = (b_ - a_).normalized()
        S = (Vector((0, 0, 1)) - T * T.z).normalized()
        U = S.cross(T).normalized()
        w = LEG_T[i][2]
        out.append((p, U, S, w, w * 0.9))
    return out


def grow_leg(bm, faces, roles, secs):
    for p, U, S, rw, rh in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (a, b) in new.items():
            v.co = p + S * (a * rh) + U * (b * rw)
        faces, roles = r['faces'], new
    return faces


def role_pos(sec, u, s):
    c, rx, ry, dz = sec
    return (c[0] + u * rx, c[1] + s * ry, c[2] - u * dz)


def grow_fang(bm, faces, roles, secs):
    for sec in secs:
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (u, s) in new.items():
            v.co = Vector(role_pos(sec, u, s))
        faces, roles = r['faces'], new


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(c, a, T, B, W, p)) for (nm, c, a, T, B, W, p) in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, rings[0]); cap(bm, rings[-1])
    recalc_normals(bm)
    for spec in LEGS:
        i = IDX[spec[0]]
        rr, rf = rings[i], rings[i + 1]
        roles = {}
        for j, (a, b) in zip(RC, OCT):
            roles[rr[j]], roles[rf[j]] = (a, b), (a, -b)
        grow_leg(bm, [spans[i][j] for j in RC[:-1]], roles, leg_path(spec))
    i = IDX['H0']
    rr, rf = rings[i], rings[i + 1]
    grow_fang(bm, [spans[i][7]], {rr[7]: (1, 1), rf[7]: (1, -1), rr[8]: (-1, 1), rf[8]: (-1, -1)}, FANG)
    recalc_normals(bm)
    snap_seam(bm)
    return object_from_bm('body', bm)


def eye_face_centre():
    """The top-outer face of the head front (ring vertices 2-3, H1 -> H2): the eye."""
    H1, H2 = P('H1'), P('H2')
    return (H1[2] + H1[3] + H2[2] + H2[3]) / 4


def leg_edge_mid(spec, i):
    """Midpoint of the leg's side edge (role (0.383, +0.924)) between leg sections i and i+1."""
    s = leg_path(spec)
    (p0, U0, S0, w0, h0), (p1, U1, S1, w1, h1) = s[i], s[i + 1]
    return ((p0 + U0 * w0 * 0.924 + S0 * h0 * 0.383) + (p1 + U1 * w1 * 0.924 + S1 * h1 * 0.383)) / 2


def stage2(k, body):
    ec0 = eye_face_centre()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.03
                                        and abs(c.z - ec0.z) < 0.03)
    bm = edit(body)
    # joint rings on every leg: the patella (after the knee) and the metatarsus joint
    for n, spec in enumerate(LEGS, 1):
        for i, why in ((LI(0.52), 'patella joint ring (knee -> tibia), leg %d' % n), (LI(0.79), 'metatarsus joint ring, leg %d' % n)):
            e = edge_near(bm, leg_edge_mid(spec, i))
            with k.topo(bm, 'loop', why):
                loopcut(bm, e, t=0.5)
    # pedicel: a ring in the abdomen front span (A8 -> W), the abdomen's hinge
    e = edge_near(bm, (P('A10')[2] + P('Wa')[2]) / 2)
    with k.topo(bm, 'loop', 'pedicel ring: the abdomen hinge'):
        loopcut(bm, e, t=0.5)
    recalc_normals(bm)
    # eye socket: a loop inside the head front face, pushed 6 mm in
    f = face_near(bm, ec0, n=(0.5, -1, 0.3))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the top-outer head front face'):
        inner = inset(bm, [f], 0.35, 0.0)
    move(list(inner[0].verts), -fn * 0.006)
    # s2 r2: rounded abdomen end (the rear view showed a flat octagon): the tip and A1 rings pushed back
    move([vert_near(bm, q) for q in P('AT')], (0, 0.03, 0))   # fix pass 2: 0.07 -> 0.03 (stage-1 abdomen now longer)
    move([vert_near(bm, q) for q in P('A1')], (0, 0.02, 0))
    # weakfix 2026-10-23: the rear still read as a flat disc (rear view: the 14 cm AT cap n-gon facing back). The end
    # rings close in to a round bulb: AT shrinks to half its radius and moves 2 cm further back, A1 / A2 tighten a
    # little, so the rear view shows the dome turning in to a small apex.
    for nm, sc, dy in (('AT', 0.48, 0.022), ('A1', 0.92, 0.010), ('A2', 0.97, 0.003)):
        off = {'AT': 0.03, 'A1': 0.02}.get(nm, 0.0)
        vs = [vert_near(bm, q + Vector((0, off, 0))) for q in P(nm)]
        zc = (max(v.co.z for v in vs) + min(v.co.z for v in vs)) / 2
        for v in vs:
            v.co.x *= sc
            v.co.z = zc + (v.co.z - zc) * sc
            v.co.y += dy
    # flat carapace top: the C1-C3 top seam vertices level
    flatten([vert_near(bm, q) for nm in ('C1', 'C2', 'C3') for q in P(nm)[:3]])
    recalc_normals(bm)
    commit(body, bm)
    bm.free()


PAL = {'brown': '#5a3d2e', 'orange': '#d4702e', 'eye': '#121012', 'claw': '#2a1b15'}   # s3 r2: brown a step lighter
LEG_BANDS = ((0.17, 0.30), (0.46, 0.53), (0.72, 0.785))      # leg spans painted orange (borders on the section loops)
ABD_BANDS = ((0.64, 0.722), (0.457, 0.553), (0.274, 0.362))    # poly pass 3: one station span each


_LP = None


def leg_of3(c):
    """poly pass 3: (leg, fraction) from the nearest point on the leg centre line in 3D (the plan projection
    smeared the bands across the steep tibia once the tubes got denser), or None off the legs."""
    global _LP
    if _LP is None:
        _LP = []
        for spec in LEGS:
            s = leg_path(spec)
            _LP.append([(leg_root(spec), 0.0)] + [(s[j][0], LEG_T[j][0]) for j in range(len(s))])
    q = Vector((abs(c.x), c.y, c.z))
    best = None
    for n, pts in enumerate(_LP):
        for (p0, f0), (p1, f1) in zip(pts, pts[1:]):
            d = p1 - p0
            t = max(0.0, min(1.0, (q - p0).dot(d) / d.length_squared))
            dist = (p0 + d * t - q).length
            if best is None or dist < best[2]:
                best = (n, f0 + (f1 - f0) * t, dist)
    if best is None or best[2] > 0.09 or best[1] < 0.03:
        return None
    return best


def body_rule(c, n, i):
    lg = leg_of3(c)
    if lg is not None:
        f = lg[1]
        return 'orange' if any(a < f < b for a, b in LEG_BANDS) else 'brown'
    if c.y > 0.1 and any(a < c.y < b for a, b in ABD_BANDS):
        return 'orange'
    return 'brown'


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """A small low-poly lens eye: back cone, ring, front fan."""
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


def body_bvh(body):
    bm = edit(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def stage3(k, body):
    paint(body, PAL, body_rule)
    tree = body_bvh(body)
    bm = bmesh.new()
    # main eye in the socket, a small one above it nearer the midline (the ref's front eye row)
    ec = eye_face_centre()
    c, n, _i, _d = tree.find_nearest(ec + Vector((0, 0.006, 0)))
    n = n if n.y < 0 else -n
    lens(bm, c, n, 0.017, 0.009)
    H1, H2 = P('H1'), P('H2')
    c2 = (H1[0] + H1[2] + H2[0] + H2[2]) / 4 + Vector((0.012, 0, 0))
    c2, n2, _i, _d = tree.find_nearest(c2)
    n2 = n2 if n2.y < 0 else -n2
    lens(bm, c2, n2, 0.011, 0.006)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye']}, lambda c_, n_, i: 'eye')
    # leg tip claws: a small dark 4-sided spike under each foot pointing out and down
    bm = bmesh.new()
    for spec in LEGS:
        s = leg_path(spec)
        p, U, S, w, h = s[-1]
        T = (s[-1][0] - s[-2][0]).normalized()
        base = p - T * 0.02 + S * 0.004
        # detail pass 2026-10-23: a chunky blunt claw cap (a frustum >= 22 mm thick to its tip; tier-1 floor 21 mm),
        # was a 4-sided spike (t 8.3 mm)
        q = [bm.verts.new(base + U * su * 0.0165 + S * ss * 0.0145) for su, ss in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        tc = p + T * 0.024 - S * 0.007
        r_ = [bm.verts.new(tc + U * su * 0.0122 + S * ss * 0.0115) for su, ss in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        bm.faces.new(list(reversed(q))); bm.faces.new(r_)
        for j in range(4):
            bm.faces.new([q[j], q[(j + 1) % 4], r_[(j + 1) % 4], r_[j]])
    claws = object_from_bm('claws', bm)
    paint(claws, {'claw': PAL['claw']}, lambda c_, n_, i: 'claw')
    return [eye, claws]


def stage4(k, body, pieces):
    B = [('ceph', (0.0, 0.04, 0.45), (0.0, -0.40, 0.45), None),
         ('abdomen', (0.0, 0.075, 0.45), (0.0, 0.80, 0.53), 'ceph'),
         ('fang.L', (0.064, -0.50, 0.33), (0.056, -0.56, 0.19), 'ceph')]
    for n_, spec in enumerate(LEGS, 1):
        s = leg_path(spec)
        r0 = leg_root(spec)
        pts = [s[LI(0.17)][0], s[LI(0.40)][0], s[LI(0.72)][0], s[-1][0]]   # s4 r3: the femur pivots past the coxa, so neighbouring roots stay with the body
        for j, (a, b) in enumerate(zip(pts, pts[1:])):
            nm = 'leg%d%s.L' % (n_, 'abc'[j])
            par = 'ceph' if j == 0 else 'leg%d%s.L' % (n_, 'abc'[j - 1])
            B.append((nm, tuple(a), tuple(b), par, j > 0))
    rig = armature(B)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            d = (eb.tail - eb.head).normalized()
            eb.align_roll(Vector((0, -1, 0)) if abs(d.z) > 0.9 else Vector((0, 0, 1)))   # local Z up: rot X lifts, rot Z swings
        bpy.ops.object.mode_set(mode='OBJECT')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    L = ['leg%d%s.%s' % (n_, s_, sd) for n_ in range(1, 5) for s_ in 'abc' for sd in 'LR']
    # idle: abdomen breathing, a slow ripple of small leg lifts, the fangs working
    keys = {}
    for f in (1, 13, 25, 37, 49):
        ph = 2 * math.pi * (f - 1) / 48
        d = {'abdomen': (round(1.5 * math.sin(ph), 2), 0, 0), 'ceph': (round(-1.0 * math.sin(ph), 2), 0, 0),
             'fang.L': (round(6 * max(0.0, math.sin(2 * ph)), 2), 0, 0)}
        d['fang.R'] = d['fang.L']
        for n_ in range(1, 5):
            for sd, o in (('L', 0.0), ('R', 0.9)):
                d['leg%da.%s' % (n_, sd)] = (round(3 * math.sin(ph + n_ * 1.2 + o), 2), 0, 0)
        keys[f] = d
    clip(rig, 'idle', keys)
    # move: alternating tetrapod gait (L1 R2 L3 R4 | R1 L2 R3 L4): the swing set lifts and reaches forward
    A, Lf = 9.0, 18.0   # s4 r3: swing 14 -> 9
    setA = {('L', 1), ('R', 2), ('L', 3), ('R', 4)}
    def gait(phase):
        d = {}
        for n_ in range(1, 5):
            for sd in 'LR':
                inA = (sd, n_) in setA
                sw = (1 if inA else -1) * phase           # +1: this set swings forward, -1: it pushes back
                fwd = -A if sd == 'L' else A               # rot Z on .L: + turns the tip back; .R mirrored
                d['leg%da.%s' % (n_, sd)] = (Lf if sw > 0 else 0.0, 0, fwd * sw)
                d['leg%db.%s' % (n_, sd)] = (-4.0 if sw > 0 else 0.0, 0, 0)
        return d
    clip(rig, 'move', {1: gait(1), 7: gait(0), 13: gait(-1), 19: gait(0), 25: gait(1)},
         loc={1: {'ceph': (0, 0, 0)}, 7: {'ceph': (0, 0, 0.012)}, 13: {'ceph': (0, 0, 0)}, 19: {'ceph': (0, 0, 0.012)},
              25: {'ceph': (0, 0, 0)}})
    # attack: rear up, front legs raised high and the fangs open, then a forward strike and the fangs close
    up = {'ceph': (-10, 0, 0), 'abdomen': (3, 0, 0), 'fang.L': (25, 0, 0)}   # s4 r2: abdomen 8 -> 3
    up['fang.R'] = up['fang.L']
    for sd in 'LR':
        up['leg1a.' + sd] = (38, 0, 0); up['leg1b.' + sd] = (10, 0, 0)
        up['leg2a.' + sd] = (18, 0, 0)
    hit = {'ceph': (8, 0, 0), 'abdomen': (-2, 0, 0), 'fang.L': (-12, 0, 0)}
    hit['fang.R'] = hit['fang.L']
    for sd in 'LR':
        hit['leg1a.' + sd] = (8, 0, 0); hit['leg1b.' + sd] = (-6, 0, 0)
    clip(rig, 'attack', {1: {}, 10: up, 16: hit, 20: hit, 26: {'ceph': (2, 0, 0)}, 32: {}},
         loc={1: {'ceph': (0, 0, 0)}, 10: {'ceph': (0, -0.03, 0.03)}, 16: {'ceph': (0, 0.06, 0)}, 20: {'ceph': (0, 0.06, 0)},
              32: {'ceph': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
