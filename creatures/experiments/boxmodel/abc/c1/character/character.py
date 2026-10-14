import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet
from mathutils.bvhtree import BVHTree

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull) plus hand edits; detail in stages 2-4
META = dict(creature='character', model='opus', engine_glb='')

# the skeleton (abc/k3/character's, moved onto the carved arm axis and the hand-built hand / foot)
J = dict(
    hips=(0.0, -0.01, 0.70), spine=(0.0, -0.012, 0.88), chest=(0.0, -0.01, 1.04),
    neck=(0.0, -0.005, 1.15), head=(0.0, 0.0, 1.235), top=(0.0, 0.0, 1.58),
    clav=(0.03, 0.0, 1.12), shoulder=(0.15, 0.020, 1.080), elbow=(0.350, 0.030, 1.098),
    wrist=(0.560, 0.028, 1.095), fingers=(0.695, 0.028, 1.07),
    hip=(0.080, -0.006, 0.66), knee=(0.108, -0.004, 0.35), ankle=(0.120, 0.004, 0.10),
    toe=(0.135, -0.16, 0.02),
)

HEAD_C = Vector((0.0, 0.005, 1.398))
HEAD_R = 0.198
HEAD_TH = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180]      # half 16-gon: front seam .. back seam
HEAD_PHI = (-66, -46, -24, -2, 20, 40, 58, 74)
NECK_Z = 1.185                     # the hull is cut here; everything above is the hand-built head
NECK = (0.060, -0.004, 0.057)      # the neck ellipse at the cut: half width, centre y, half depth (reference front/side)


def head_ring(phi):
    p = math.radians(phi)
    r, z = HEAD_R * math.cos(p), HEAD_C.z + HEAD_R * math.sin(p)
    return [(r * math.sin(math.radians(t)), HEAD_C.y - r * math.cos(math.radians(t)), z) for t in HEAD_TH]


def zip_rows(bm, A, B):
    """Triangles between two seam-to-seam rows of different lengths, advancing by arc-length parameter (goblin)."""
    def par(R):
        L = [0.0]
        for p, q in zip(R, R[1:]):
            L.append(L[-1] + (q.co - p.co).length)
        return [l / L[-1] for l in L]
    ta, tb = par(A), par(B)
    i = j = 0
    while i < len(A) - 1 or j < len(B) - 1:
        if j == len(B) - 1 or (i < len(A) - 1 and ta[i + 1] <= tb[j + 1]):
            bm.faces.new([A[i], A[i + 1], B[j]]); i += 1
        else:
            bm.faces.new([A[i], B[j + 1], B[j]]); j += 1


def open_rim(bm):
    """The non-seam boundary edges as one row, front seam vertex first."""
    bnd = [e for e in bm.edges if len(e.link_faces) == 1 and not (abs(e.verts[0].co.x) < 1e-5 and abs(e.verts[1].co.x) < 1e-5)]
    adj = {}
    for e in bnd:
        for v in e.verts:
            adj.setdefault(v, []).append(e.other_vert(v))
    ends = [v for v, l in adj.items() if len(l) == 1]
    assert len(ends) == 2 and max(len(l) for l in adj.values()) == 2, ('rim', len(ends))
    A, prev = [min(ends, key=lambda v: v.co.y)], None
    while True:
        nx = [w for w in adj[A[-1]] if w is not prev]
        if not nx:
            return A
        prev = A[-1]; A.append(nx[0])


def new_head(bm):
    """The hull's head is a decimated blob (random triangles, no place for the face): cut at the neck, a faceted
    16-gon sphere of latitude rings (the reference's head) zipped onto the neck rim."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=0.004, plane_co=(0, 0, NECK_Z), plane_no=(0, 0, 1))
    dead = [f for f in bm.faces if f.calc_center_median().z > NECK_Z]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    A = open_rim(bm)
    for v in (A[0], A[-1]):
        v.co.x = 0.0
    # the neck: the rim and the band under it onto the reference's thin round neck
    hw, cy, hd = NECK
    for v in bm.verts:
        if v.co.z > 1.135 and v.co.x < 0.13:
            t = min(1.0, (v.co.z - 1.135) / (NECK_Z - 1.135))
            u, w = v.co.x / hw, (v.co.y - cy) / hd
            r = math.hypot(u, w)
            if r > 1.0:
                s = 1.0 + (1.0 / r - 1.0) * t
                v.co.x *= s
                v.co.y = cy + (v.co.y - cy) * s
    rows = [ring(bm, head_ring(p)) for p in HEAD_PHI]
    zip_rows(bm, A, rows[0])
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    pole = bm.verts.new((0.0, HEAD_C.y, HEAD_C.z + HEAD_R))
    top = rows[-1]
    for i in range(len(top) - 1):
        bm.faces.new([top[i], top[i + 1], pole])
    recalc_normals(bm)


WRIST_X = 0.552                    # the hull arm is cut here; outward is the hand-built mitten hand
# hand rings: x, dy, dz (from the wrist axis), half depth (y), half thickness (z). team pass (AD item 1): a mitten
# wider than the wrist, a knuckle ring at ~50% of the length, the finger block beyond it curling down; 8-gon rounded
# rectangles (the 6-gon stack read as a paddle)
HAND = [(0.568, 0.0, 0.000, 0.035, 0.023),
        (0.600, 0.0, 0.001, 0.048, 0.023),      # palm base (thumb root between this and the wrist ring)
        (0.632, 0.0, 0.001, 0.051, 0.024),      # knuckle ring: the hinge of the curl, a slight ridge
        (0.664, 0.0, -0.011, 0.049, 0.019),
        (0.688, 0.0, -0.029, 0.045, 0.015),
        (0.698, 0.0, -0.047, 0.037, 0.011)]     # fingertips
HAND_ANG = [22.5 + 45 * i for i in range(8)]
# thumb: two segments out of the palm's front (-Y) face, pointing forward and slightly out, a little down
# team pass 2 (verifier: "a small hook pointing down/back"): longer (~0.055 m), forward and out toward the fingers,
# barely down; each cap is turned about Z to face its direction (offset alone sheared it into a plank)
THUMB = [((0.018, -0.022, -0.002), 1.05, 30), ((0.020, -0.016, 0.0), 0.8, 12)]


def loop_of(bm, edges):
    adj = {}
    for e in edges:
        for v in e.verts:
            adj.setdefault(v, []).append(e.other_vert(v))
    assert all(len(l) == 2 for l in adj.values()), 'loop: not a single cycle'
    L, prev = [next(iter(adj))], None
    while True:
        nx = [w for w in adj[L[-1]] if w is not prev]
        if nx[0] is L[0]:
            return L
        prev = L[-1]; L.append(nx[0])


def zip_loops(bm, A, B, c, axis='x'):
    """Triangles between two closed loops around the axis (+X or +Z) through c, advancing by angle."""
    if axis == 'x':
        ang = lambda v: math.atan2(v.co.z - c.z, v.co.y - c.y)
    else:
        ang = lambda v: math.atan2(v.co.y - c.y, v.co.x - c.x)
    A = sorted(A, key=ang); B = sorted(B, key=ang)
    a = [ang(v) for v in A] + [ang(A[0]) + 2 * math.pi]
    b = [ang(v) for v in B] + [ang(B[0]) + 2 * math.pi]
    i = j = 0
    while i < len(A) or j < len(B):
        if j == len(B) or (i < len(A) and a[i + 1] <= b[j + 1]):
            bm.faces.new([A[i], A[(i + 1) % len(A)], B[j % len(B)]]); i += 1
        else:
            bm.faces.new([A[i % len(A)], B[(j + 1) % len(B)], B[j]]); j += 1


def new_hand(bm):
    """The hull hand is a flat paddle with a knob (the curled fingers and thumb are under the voxel size): cut at
    the wrist, the forearm tapered into it, a mitten of 6-gon rings (flat palm, fingers curling down) and a thumb."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=0.003, plane_co=(WRIST_X, 0, 0), plane_no=(1, 0, 0))
    dead = [f for f in bm.faces if f.calc_center_median().x > WRIST_X]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    rim = loop_of(bm, [e for e in bm.edges if len(e.link_faces) == 1 and min(v.co.x for v in e.verts) > 0.5])
    c = centre(rim)
    # forearm taper: from x 0.40 to the cut, the arm section shrinks toward the wrist size about the arm axis
    ry0 = max(abs(v.co.y - c.y) for v in rim); rz0 = max(abs(v.co.z - c.z) for v in rim)
    for v in bm.verts:
        if v.co.x > 0.40:
            t = min(1.0, (v.co.x - 0.40) / (WRIST_X - 0.40)) ** 1.5
            v.co.y = c.y + (v.co.y - c.y) * (1 - t * (1 - 0.031 / ry0))
            v.co.z = c.z + (v.co.z - c.z) * (1 - t * (1 - 0.025 / rz0))
    rows = []
    Y = Vector((0, 1, 0))
    cs = [Vector((x, c.y + dy, c.z + dz)) for x, dy, dz, _, _ in HAND]
    for i, (x, dy, dz, ry, rz) in enumerate(HAND):
        d = (cs[min(i + 1, len(cs) - 1)] - cs[max(i - 1, 0)]).normalized()
        w = d.cross(Y).normalized()
        if w.z < 0:
            w = -w
        se = lambda t: math.copysign(abs(t) ** 0.5, t)          # superellipse: a rounded rectangle section
        rows.append(ring(bm, [cs[i] + Y * (ry * se(math.cos(math.radians(a)))) + w * (rz * se(math.sin(math.radians(a))))
                              for a in HAND_ANG]))
    zip_loops(bm, rim, rows[0], c)
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, rows[-1])
    recalc_normals(bm)
    # thumb: the lower-front face of the wrist-to-palm segment, out forward and down
    root = {rows[0][3], rows[0][4], rows[1][3], rows[1][4]}          # the front (-Y) quad, wrist ring -> palm base
    th = next(f for f in rows[0][3].link_faces if set(f.verts) == root)
    for d, s, turn in THUMB:
        e = extrude(bm, [th], offset=d)
        rotate(e['verts'], (0, 0, 1), turn)
        scale(e['verts'], s)
        th = e['faces'][0]
    recalc_normals(bm)


ANKLE_Z = 0.125                    # the hull leg is cut here; below is the hand-built foot
# the sole outline (x, y), heel -> outer edge -> toes -> inner edge, and the top ring's height over each point
SOLE = [(0.120, 0.066), (0.154, 0.054), (0.168, -0.020), (0.182, -0.105), (0.188, -0.160), (0.170, -0.198),
        (0.122, -0.206), (0.090, -0.186), (0.082, -0.120), (0.082, -0.030), (0.088, 0.052)]
TOPZ = [0.074, 0.074, 0.064, 0.046, 0.036, 0.032, 0.032, 0.036, 0.046, 0.064, 0.074]


def new_foot(bm):
    """The hull foot is a short rounded club with no sole: cut at the ankle, a flat sole, a long low foot with a
    sloping instep (reference side view: toe y -0.20, heel 0.07), zipped onto the ankle rim."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=0.003, plane_co=(0, 0, ANKLE_Z), plane_no=(0, 0, 1))
    dead = [f for f in bm.faces if f.calc_center_median().z < ANKLE_Z]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    rim = loop_of(bm, [e for e in bm.edges if len(e.link_faces) == 1 and max(v.co.z for v in e.verts) < ANKLE_Z + 0.01])
    c = centre(rim)
    ax = max(abs(v.co.x - c.x) for v in rim); ay = max(abs(v.co.y - c.y) for v in rim)
    cx, cy = sum(p[0] for p in SOLE) / len(SOLE), sum(p[1] for p in SOLE) / len(SOLE)
    edge = [Vector((x, y, 0.016)) for x, y in SOLE]                                    # the widest ring, just above the sole
    sole = [Vector((cx + (x - cx) * 0.86, cy + (y - cy) * 0.95, 0.0)) for x, y in SOLE]   # the sole rolls under
    top = [Vector((cx + (x - cx) * 0.86, cy + (y - cy) * 0.94, z)) for (x, y), z in zip(SOLE, TOPZ)]
    mid = []
    for p in top:
        a = math.atan2(p.y - c.y, p.x - c.x)
        q = Vector((c.x + 0.8 * ax * math.cos(a), c.y + 0.8 * ay * math.sin(a), ANKLE_Z))
        m = q.lerp(p, 0.45)
        m.z = ANKLE_Z - 0.4 * (ANKLE_Z - p.z)
        mid.append(m)
    R = [ring(bm, pts) for pts in (mid, top, edge, sole)]
    zip_loops(bm, rim, R[0], c, axis='z')
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, R[-1])
    recalc_normals(bm)


def stage1(k):
    ob = carve_base(k)
    bm = edit(ob)
    new_head(bm)
    new_hand(bm)
    new_foot(bm)
    snap_seam(bm)
    commit(ob, bm)
    say('slivers (min angle < 6 deg, techqa rule):', slivers(ob))
    return ob


def slivers(ob, deg=6.0):
    eb = evaluated_bm(ob)
    bmesh.ops.triangulate(eb, faces=eb.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    L = 1.6
    bad = []
    for f in eb.faces:
        a, b, c = (v.co for v in f.verts)
        if max((a - b).length, (b - c).length, (c - a).length) < 0.01 * L:
            continue
        angs = [math.degrees((y - x).angle(z - x, 0)) for x, y, z in ((a, b, c), (b, c, a), (c, a, b))]
        if min(angs) < deg:
            bad.append(tuple(round(q, 3) for q in f.calc_center_median()))
    n = len(eb.faces)
    eb.free()
    return len(bad), n, bad[:40]


def cut(k, bm, co, no, box, reason, dist=0.006):
    """A planar loop through the faces whose vertices all satisfy box(c) (bisect_plane on the triangulated carve,
    logged as a loop; abc/c1/bear). Vertices within dist of the plane count as on it (no sliver cuts)."""
    faces = [f for f in bm.faces if all(box(v.co) for v in f.verts)]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    with k.topo(bm, 'loop', reason):
        r = bmesh.ops.bisect_plane(bm, geom=geom, dist=dist, plane_co=Vector(co), plane_no=Vector(no).normalized())
    return [v for v in r['geom_cut'] if isinstance(v, bmesh.types.BMVert)]


def stage2(k, body):
    bm = edit(body)
    # joints: the carve's triangles run across the knee and elbow at random; a loop on each joint plane gives the
    # bend a clean hinge line, and the knee cap / elbow point are pushed out on it
    kz = J['knee'][2]
    knee = cut(k, bm, (0, 0, kz), (0, 0, 1), lambda c: 0.04 < c.x < 0.2 and abs(c.z - kz) < 0.06,
               'knee loop: the hinge of the leg bend (z %.2f)' % kz)
    ex = J['elbow'][0]
    elbow = cut(k, bm, (ex, 0, 0), (1, 0, 0), lambda c: abs(c.x - ex) < 0.05 and c.z > 0.95,
                'elbow loop: the hinge of the arm bend (x %.2f)' % ex)
    for v in knee:
        if v.co.y < J['knee'][1] - 0.02:
            v.co.y -= 0.006                       # knee cap
        elif v.co.y > J['knee'][1] + 0.02:
            v.co.y += 0.003                       # back of the knee
    for v in elbow:
        if v.co.y > J['elbow'][1] + 0.015:
            v.co.y += 0.005                       # elbow point
    shoulders(bm)
    socket(bm)
    recalc_normals(bm)
    commit(body, bm)


def socket(bm):
    """team pass 2 (AD item 2, verifier: the eye still 1/3 of its diameter proud): the eye pieces sat on the smooth
    sphere, up to 7 mm over the 16-gon facets. The head vertices under each eye sink SOCKET m toward the head centre
    (vertex moves only), so the whole eye stack sits in a shallow socket instead of on the skull."""
    n = 0
    for v in bm.verts:
        d = v.co - HEAD_C
        if d.length > HEAD_R - 0.004 and d.normalized().dot(EYE_D) > 0 and d.cross(EYE_D).length < 0.05:
            v.co -= d.normalized() * SOCKET
            n += 1
    say('socket: head verts sunk', n)


def _smooth(vs, w, it, lam=0.5):
    """Laplacian relax of vs (weights w in 0..1), seam vertices kept on x = 0."""
    for _ in range(it):
        new = {}
        for v in vs:
            nb = [e.other_vert(v).co for e in v.link_edges]
            c = sum(nb, Vector()) / len(nb)
            new[v] = v.co + (c - v.co) * lam * w[v]
        for v, co in new.items():
            if abs(v.co.x) < 1e-6:
                co.x = 0.0
            v.co = co


RELAX = 8


def shoulders(bm):
    """team pass (AD item 4): the carve left the shoulder a flat-faced wedge with a knife ridge from the shoulder
    point down the chest and a crease down the sternum. Relax the upper torso and the arm root (falloff to the
    edges, the neck band untouched), then push the deltoid cap out ~8 mm and down ~4 mm so it is convex, and lift
    the armpit ~6 mm into the torso."""
    sh = Vector(J['shoulder'])
    def fall(t):
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)
    w = {}
    for v in bm.verts:
        c = v.co
        if c.x > 0.26 or c.z < 0.86 or c.z > 1.16:
            continue
        if c.z > 1.12 and c.x < 0.075:            # the neck band (shaped in stage 1) stays
            continue
        w[v] = fall((1.16 - c.z) / 0.04) * fall((c.z - 0.86) / 0.06) * fall((0.26 - c.x) / 0.05)
    _smooth(list(w), w, RELAX)
    # team pass 2 (verifier: a faint sternum crease in az000): the chest front between the seam and x 0.10 is eased
    # onto one plane per height: each vertex takes the seam profile's y at its z (falloff to the sides, top, bottom)
    prof = sorted((v.co.z, v.co.y) for v in bm.verts if abs(v.co.x) < 1e-6 and v.co.y < -0.02 and 0.84 < v.co.z < 1.16)
    def ys(z):
        for (z0, y0), (z1, y1) in zip(prof, prof[1:]):
            if z0 <= z <= z1:
                return y0 + (y1 - y0) * (z - z0) / max(z1 - z0, 1e-9)
        return None
    bm.normal_update()
    for v in bm.verts:
        c = v.co
        if 1e-6 < c.x < 0.10 and 0.88 < c.z < 1.12 and v.normal.y < -0.5:
            y = ys(c.z)
            if y is not None:
                t = fall((0.10 - c.x) / 0.10) * fall((1.12 - c.z) / 0.03) * fall((c.z - 0.88) / 0.04)
                c.y += (y - c.y) * t
    bm.normal_update()
    for v in bm.verts:
        d = v.co - sh
        cap = fall(1.0 - d.length / 0.075)       # the deltoid: the arm root around the shoulder joint
        if cap > 0 and v.co.z > sh.z - 0.05:
            out = Vector((d.x, d.y, max(d.z, 0.0)))
            out = out.normalized() if out.length > 1e-6 else Vector((1, 0, 0))
            v.co += out * 0.008 * cap + Vector((0, 0, -0.004)) * cap
        pit = fall(1.0 - (v.co - Vector((sh.x - 0.02, sh.y, sh.z - 0.075))).length / 0.04)
        if pit > 0:
            v.co.z += 0.006 * pit


EYE_D = Vector((0.09, -0.176, 0.028)).normalized()     # eye centre direction from the head centre
EYE_C = HEAD_C + EYE_D * HEAD_R * 0.97
SOCKET = 0.010
EYE_B = HEAD_C + EYE_D * HEAD_R * 0.88                 # the eye bone's head: under the sunk eye, so the blink sinks it
KEEP_VALLEYS = lambda c: (Vector((abs(c[0]), c[1], c[2])) - EYE_C).length < 0.045   # set in stage3 (a lambda in META breaks the lock's json)


PAL = {'skin': '#f0b477', 'eye_white': '#f7f7f5', 'black': '#151515', 'brow': '#3a2f2a'}


def frame_at(n):
    n = Vector(n).normalized()
    u = Vector((0, 0, 1)).cross(n).normalized()
    return n, u, n.cross(u).normalized()


def proj(tree, e):
    """The outer surface of tree along the ray from the head centre through e."""
    e = Vector(e).normalized()
    return tree.ray_cast(HEAD_C + e * 0.5, -e)[0]


def disc(name, tree, c0, n, u, w, r, h, rb, hb, dome, sides=12):
    """A lens: its rim follows the surface under it at +h, the back sits at hb (buried)."""
    bm = bmesh.new()
    A = [2 * math.pi * i / sides for i in range(sides)]

    def at(rr, hh):
        out = []
        for a in A:
            e = (c0 + (u * math.cos(a) + w * math.sin(a)) * rr - HEAD_C).normalized()
            out.append(proj(tree, e) + e * hh)
        return out
    F = ring(bm, at(r, h)); B = ring(bm, at(rb, hb))
    bridge(bm, F, B, closed=True)
    tip = bm.verts.new(centre(F) + n * dome)
    for i in range(sides):
        bm.faces.new([F[i], F[(i + 1) % sides], tip])
    bm.faces.new(list(reversed(B)))
    return object_from_bm(name, bm, mirror=False)


def _at(tree, c0, u, w, rr, hh, sides=12):
    out = []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        e = (c0 + (u * math.cos(a) + w * math.sin(a)) * rr - HEAD_C).normalized()
        out.append(proj(tree, e) + e * hh)            # team pass 2: on the real (socketed) skin, not the smooth sphere
    return out


def outline(name, tree, c0, u, w, sides=16):
    """The eye outline: a static torus band seated in the skin; the front annulus
    black, the outer side skin (a thin dark edge from the side, not a disc)."""
    bm = bmesh.new()
    # team pass (AD item 2): sunk ~8 mm and the band ~40% thinner, so it reads as a line, not a goggle rim
    # team pass 2: the rings follow the socketed skin and stand only 1-3 mm over it (nothing shows from behind)
    OB, OF = ring(bm, _at(tree, c0, u, w, 0.0578, -0.006, sides)), ring(bm, _at(tree, c0, u, w, 0.0600, 0.0008, sides))
    IF, IB = ring(bm, _at(tree, c0, u, w, 0.0569, 0.0028, sides)), ring(bm, _at(tree, c0, u, w, 0.0549, -0.004, sides))
    for a, b in ((OB, OF), (OF, IF), (IF, IB), (IB, OB)):
        bridge(bm, a, b, closed=True)
    recalc_normals(bm)
    ob = object_from_bm(name, bm, mirror=False)
    paint(ob, {'skin': PAL['skin'], 'black': PAL['black']}, lambda c, nn, i: 'black' if sides <= i < 3 * sides else 'skin')
    return ob


def sclera(name, tree, c0, n, u, w, sides=16):
    """The white dome inside the outline: its rim sits in the outline's inner wall and
    every vertex stays > 7 mm off the skin, so the blink can squash it without it
    riding over the skin (it hangs on the outline, not on the body)."""
    bm = bmesh.new()
    # team pass (AD item 2): the whole stack sunk ~8 mm, its back seated under the skin (it was raised in s3 r04
    # so the old squash blink was not drift; the blink now sinks the eye along its normal instead, see stage4)
    # team pass 2: the rim on the socketed skin inside the outline; the dome a shallow lens over the rim's plane
    # (5.5 mm at r 0.045, 7 mm at the centre: closer to the skin z-fights), not a dome over the smooth sphere
    R1 = ring(bm, _at(tree, c0, u, w, 0.0559, 0.0026, sides))
    p0 = centre(R1)
    circ = lambda rr, hh: [p0 + (u * math.cos(2 * math.pi * i / sides) + w * math.sin(2 * math.pi * i / sides)) * rr
                           + n * hh for i in range(sides)]
    R2 = ring(bm, circ(0.045, 0.0055))
    RB = ring(bm, circ(0.041, -0.007))
    bridge(bm, R1, R2, closed=True); bridge(bm, RB, R1, closed=True)
    tip = bm.verts.new(p0 + n * 0.0072)
    back = bm.verts.new(p0 - n * 0.009)
    for i in range(sides):
        bm.faces.new([R2[i], R2[(i + 1) % sides], tip])
        bm.faces.new([RB[(i + 1) % sides], RB[i], back])
    recalc_normals(bm)
    return solid(object_from_bm(name, bm, mirror=False), 'eye_white')


def strip(name, tree, dirs, out, inn, half, seam=False, mirror=False):
    """A thin bent bar laid on the surface along dirs (brow, mouth line): every corner of
    every column is projected onto the skin and offset along that facet's normal, so the
    bar follows the skull to its ends instead of standing off it as a straight chord."""
    bm = bmesh.new()
    hits = [proj(tree, d) for d in dirs]

    def on(q, h0, h1):
        e = (q - HEAD_C).normalized()
        loc, nrm = tree.ray_cast(HEAD_C + e * 0.5, -e)[:2]
        if nrm.dot(e) < 0:
            nrm = -nrm
        return loc + nrm * h0, loc + nrm * h1
    secs = []
    for i, (d, p) in enumerate(zip(dirs, hits)):
        e = Vector(d).normalized()
        t = hits[min(i + 1, len(hits) - 1)] - hits[max(i - 1, 0)]
        up = e.cross(t).normalized()
        if up.z < 0:
            up = -up
        to, ti = on(p + up * half, out, inn)
        bo, bi = on(p - up * half, out, inn)
        pts = [to, bo, bi, ti]
        if seam and i == 0:
            pts = [Vector((0.0, q.y, q.z)) for q in pts]
        secs.append(ring(bm, pts))
    for a, b in zip(secs, secs[1:]):
        bridge(bm, a, b, closed=True)
    if not seam:
        bm.faces.new(list(reversed(secs[0])))
    bm.faces.new(secs[-1])
    return object_from_bm(name, bm, mirror=seam or mirror)


def solid(ob, key):
    paint(ob, {key: PAL[key]}, lambda c, n, i: key)
    return ob


def sph(th, ph):
    t, p = math.radians(th), math.radians(ph)
    return Vector((math.sin(t) * math.cos(p), -math.cos(t) * math.cos(p), math.sin(p)))


def sheet_skin(k, body):
    """colour_from_sheet's clusters on the base; the skin is the sheet cluster nearest the brief's peach."""
    sheet = colour_from_sheet(k, [body])
    say('sheet clusters:', sheet)
    rgb = lambda h: [int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    best = min(sheet.values(), key=lambda h: sum((p - q) ** 2 for p, q in zip(rgb(h), rgb(PAL['skin']))))
    if sum((p - q) ** 2 for p, q in zip(rgb(best), rgb(PAL['skin']))) ** 0.5 < 45:
        PAL['skin'] = best
    say('palette:', PAL)


TOES = [  # centre x, y, half width, half length, half height (the big toe first)
    # team pass (should-fix): ~1.7x longer (roots unchanged, fronts further out), spread to the outer edge
    (0.101, -0.210, 0.017, 0.030, 0.015), (0.130, -0.208, 0.013, 0.027, 0.012),
    (0.153, -0.199, 0.012, 0.024, 0.011), (0.174, -0.186, 0.011, 0.020, 0.010)]


def toe_blocks():
    """Bare-foot toe blocks: small bevelled boxes rooted in the front of the sole, their fronts proud of it."""
    bm = bmesh.new()
    for x, y, hw, hl, hh in TOES:
        c = Vector((x, y, hh))
        pts = []
        for zz, sc in ((-hh + 0.003, 1.0), (hh * 0.55, 0.92), (hh, 0.6)):
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                pts.append(c + Vector((dx * hw * sc, dy * hl * sc, zz)))
        rows = [ring(bm, pts[i:i + 4]) for i in (0, 4, 8)]
        for r0, r1 in zip(rows, rows[1:]):
            bridge(bm, r0, r1, closed=True)
        cap(bm, list(reversed(rows[0])))
        cap(bm, rows[-1])
    recalc_normals(bm)
    return solid(object_from_bm('toes', bm, mirror=True), 'skin')


def stage3(k, body):
    META['keep_valleys'] = KEEP_VALLEYS
    # team pass: the skin is pinned to the sheet cluster s3 r01-r04 measured (#f5b06f); with the new hands the
    # clustering drifted to a duller #d8a475, and the flat palette is on the AD keep list
    PAL['skin'] = '#f5b06f'
    solid(body, 'skin')
    tb = BVHTree.FromBMesh(evaluated_bm(body))
    pieces = []
    for sgn, sd in ((1, 'L'), (-1, 'R')):
        d = Vector((sgn * EYE_D.x, EYE_D.y, EYE_D.z))
        n, u, w = frame_at(d)
        c0 = HEAD_C + d * HEAD_R
        rim = outline(f'outline.{sd}', tb, c0, u, w)
        white = sclera(f'eye.{sd}', tb, c0, n, u, w)
        bpy.context.view_layer.update()
        tw = BVHTree.FromBMesh(evaluated_bm(white))
        pc = c0 + u * (-sgn * 0.004) - w * 0.002
        pupil = solid(disc(f'pupil.{sd}', tw, pc, n, u, w, 0.022, 0.003, 0.019, -0.0012, 0.004, sides=10), 'black')
        pieces += [rim, white, pupil]
    brow = strip('brow', tb, [sph(t, p) for t, p in ((10, 34.3), (17.2, 36.0), (24.4, 37.05), (31.6, 36.8), (38.8, 35))],
                 0.0056, -0.008, 0.0045, mirror=True)   # team pass 2: 1.4 mm higher (z-fight on the socket slope)
    mouth = strip('mouth', tb, [sph(t, -24.5) for t in (0, 5.75, 11.5)], 0.0038, -0.008, 0.0035, seam=True)
    pieces += [solid(brow, 'brow'), solid(mouth, 'brow')]
    nc = proj(tb, sph(0, -10))
    bm = bmesh.new()
    # team pass (AD item 3): the nose 2.3x longer (0.058 m, ~0.3 head radius) with a ~0.035 m base pushed ~4 mm
    # into the skin, so it grows out of the head and reads as a point from the front, side and top
    top, s1, s2, bot = ring(bm, [nc + Vector(q) for q in ((0, 0.005, 0.018), (0.018, 0.005, 0.004),
                                                             (0.014, 0.005, -0.012), (0, 0.005, -0.016))])
    tip = bm.verts.new(nc + Vector((0, -0.058, -0.008)))
    for a, b in ((top, s1), (s1, s2), (s2, bot)):
        bm.faces.new([a, b, tip])
    bm.faces.new([top, bot, s2, s1])
    pieces.append(solid(object_from_bm('nose', bm, mirror=True), 'skin'))
    pieces.append(toe_blocks())
    return pieces


def clip_s(rig, name, keys, loc=None, scl=None):
    """kit clip() plus scale keys (the blink)."""
    act = clip(rig, name, keys, loc=loc)
    if scl:
        ad = rig.animation_data
        ad.action = act
        if hasattr(ad, 'action_slot') and len(getattr(act, 'slots', [])):
            ad.action_slot = act.slots[0]
        pb = rig.pose.bones
        for f in sorted(scl):
            for b, sv in scl[f].items():
                pb[b].scale = sv
                pb[b].keyframe_insert('scale', frame=f)
        rest(rig)
        ad.action = None
    return act


def P(**kw):
    """A full pose: arms dropped to a relaxed A, elbows soft; kw overrides (use _L/_R for .L/.R)."""
    d = {'upperarm.L': (0, 0, -38), 'upperarm.R': (0, 0, 38), 'forearm.L': (12, 0, 0), 'forearm.R': (12, 0, 0),
         'clav.L': (0, 0, -12), 'clav.R': (0, 0, 12), 'chest': (0, 0, 0), 'spine': (0, 0, 0), 'head': (0, 0, 0),
         'neck': (0, 0, 0), 'hips': (0, 0, 0), 'thigh.L': (0, 0, 0), 'thigh.R': (0, 0, 0),
         'shin.L': (0, 0, 0), 'shin.R': (0, 0, 0)}
    for kk, v in kw.items():
        d[kk.replace('_L', '.L').replace('_R', '.R')] = v
    return d


def stage4(k, body, pieces):
    eL = tuple(EYE_B)
    rig = armature([
        ('hips', J['hips'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['top'], 'neck', True),
        ('clav.L', J['clav'], J['shoulder'], 'chest'),
        ('upperarm.L', J['shoulder'], J['elbow'], 'clav.L', True),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('hand.L', J['wrist'], J['fingers'], 'forearm.L', True),
        ('thigh.L', J['hip'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
        ('foot.L', J['ankle'], J['toe'], 'shin.L', True),
        ('eye.L', eL, tuple(EYE_B + EYE_D * 0.04), 'head'),
    ], roll='auto')
    for b in ('eye.L', 'eye.R'):
        rig.data.bones[b].use_deform = False     # the skin never follows the blink
    skin(body, rig)
    for b in ('eye.L', 'eye.R'):
        rig.data.bones[b].use_deform = True
    for p in pieces:
        nm = p.name
        if nm.startswith('outline'):
            bind(p, rig, bone='head')              # static, seated in the skin
        elif 'eye' in nm or 'pupil' in nm:
            bind(p, rig, bone='eye.L' if nm.endswith('.L') else 'eye.R')   # blinks, hangs on the outline
        else:
            bind(p, rig, body=body)
    # blink: the eye sinks along its normal (bone Y) and narrows a little: the seated sclera moves < 1% of the
    # height (the drift limit); the old z squash to 0.35 moved its rim 36 mm
    one = (1, 1, 1); shut = (1, 0.2, 0.85)
    # team pass (AD item 5): idle arms hang by the thighs (they stood out 40 deg in an A), one gentle elbow bend
    # (8 deg), the hand in line with the forearm (no wrist key), both arms the same
    # team pass 2 (item 1, az000): the hanging hand showed only its thin edge from the front; a relaxed forearm
    # pronates, so the palm turns part-way back: the twist is shared by the forearm and the hand
    TW = 22
    hang = dict(upperarm_L=(0, 0, -60), upperarm_R=(0, 0, 60), forearm_L=(8, TW, 0), forearm_R=(8, -TW, 0),
                hand_L=(0, TW, 0), hand_R=(0, -TW, 0))
    clip_s(rig, 'idle', {
        1: P(**hang), 24: P(chest=(-2.5, 0, 0), spine=(-1, 0, 0), head=(3, 0, 0), neck=(-1, 0, 0),
                            **dict(hang, upperarm_L=(0, 0, -57), upperarm_R=(0, 0, 57))), 48: P(**hang)},
        scl={1: {'eye.L': one, 'eye.R': one}, 41: {'eye.L': one, 'eye.R': one},
             43: {'eye.L': shut, 'eye.R': shut}, 45: {'eye.L': one, 'eye.R': one},
             48: {'eye.L': one, 'eye.R': one}})
    sw, st = 20, 22
    walk = {
        1: P(thigh_L=(st, 0, 0), thigh_R=(-st, 0, 0), shin_L=(-5, 0, 0), shin_R=(-15, 0, 0),
             upperarm_L=(-sw, 0, -40), upperarm_R=(sw, 0, 40), hips=(0, 5, 0), chest=(0, -7, 0), spine=(3, 0, 0)),
        9: P(shin_L=(-8, 0, 0), shin_R=(-50, 0, 0), spine=(3, 0, 0), upperarm_L=(0, 0, -40), upperarm_R=(0, 0, 40)),
        17: P(thigh_L=(-st, 0, 0), thigh_R=(st, 0, 0), shin_L=(-15, 0, 0), shin_R=(-5, 0, 0),
              upperarm_L=(sw, 0, -40), upperarm_R=(-sw, 0, 40), hips=(0, -5, 0), chest=(0, 7, 0), spine=(3, 0, 0)),
        25: P(shin_L=(-50, 0, 0), shin_R=(-8, 0, 0), spine=(3, 0, 0), upperarm_L=(0, 0, -40), upperarm_R=(0, 0, 40)),
    }
    walk[33] = walk[1]
    bob = {f: {'hips': (0, z, 0)} for f, z in ((1, 0.0), (9, 0.014), (17, 0.0), (25, 0.014), (33, 0.0))}
    clip_s(rig, 'move', walk, loc=bob)
    guard = dict(forearm_L=(45, 0, 0), forearm_R=(45, 0, 0))
    clip_s(rig, 'attack', {
        1: P(**guard),
        7: P(forearm_L=(45, 0, 0), upperarm_R=(-25, 0, 36), forearm_R=(80, 0, 0), chest=(0, -12, 0)),
        11: P(forearm_L=(45, 0, 0), clav_R=(24, 0, 10), upperarm_R=(52, 0, 6), forearm_R=(4, 0, 0), chest=(3, 24, 0), spine=(0, 8, 0)),
        16: P(forearm_L=(45, 0, 0), clav_R=(18, 0, 10), upperarm_R=(46, 0, 12), forearm_R=(14, 0, 0), chest=(2, 18, 0), spine=(0, 6, 0)),
        25: P(**guard)})
    return rig





run(META, stage1, stage2, stage3, stage4)
