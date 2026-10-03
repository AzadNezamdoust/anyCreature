import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet
import math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# prototype: stage 1 carved from reference/ (a visual hull), stage 3 coloured from the same sheet
META = dict(creature='bear', model='opus', engine_glb='')

# the skeleton (metres, faces -Y, left flank +X, feet on z = 0), read off the reference side and front views
J = dict(
    pelvis=(0.0, 0.55, 0.64), spine=(0.0, 0.05, 0.72), neck=(0.0, -0.33, 0.74),
    head=(0.0, -0.53, 0.63), snout=(0.0, -0.80, 0.47),
    tail0=(0.0, 0.70, 0.62), tail1=(0.0, 0.80, 0.60),
    shoulderL=(0.20, -0.16, 0.62), elbowL=(0.21, -0.16, 0.32), wristL=(0.21, -0.18, 0.10),
    pawL=(0.21, -0.33, 0.03),
    hipL=(0.21, 0.58, 0.62), kneeL=(0.21, 0.52, 0.34), hockL=(0.21, 0.66, 0.12),
    toeL=(0.21, 0.45, 0.03),
)


def stage1(k):
    return carve_base(k)


LEG_Z = 0.30                                  # dark lower legs below this loop
MUZ = ((0.0, -0.675, 0.555), (0.0, 0.20, 0.075))   # pale muzzle in front of this plane (side view: under the eye to behind the jaw)
BIB_V = ((0.0, -0.4, 0.27), (1.0, 0.0, -0.75))   # front view: the bib's V edge, x 0 at z 0.27 -> x 0.13 at z 0.44
BIB_Y = ((0.0, -0.22, 0.4), (0.0, 1.0, 0.0))     # side view: the bib's back edge
BIB_T = ((0.0, -0.4, 0.45), (0.0, 0.0, 1.0))     # the bib's top edge under the jaw
in_head = lambda c: c.y < -0.50 and c.z < 0.75
in_chest = lambda c: -0.62 < c.y < -0.12 and 0.22 < c.z < 0.60 and c.x < 0.30
CUTS = {
    'dark lower legs: border loop round each leg at z 0.30': ((0, 0, LEG_Z), (0, 0, 1),
        lambda c: c.z < LEG_Z + 0.08 and not (c.x < 0.10 and -0.36 < c.y < -0.18)),   # not the raised chest floor (slivers)
    'pale muzzle: border loop from under the eye to behind the jaw': (*MUZ, in_head),
    'pale bib: V edge seen from the front': (*BIB_V, in_chest),
    'pale bib: back edge seen from the side': (*BIB_Y, in_chest),
    'pale bib: top edge under the jaw': (*BIB_T, in_chest),
}


def side_of(c, plane):
    co, no = plane
    return (Vector(c) - Vector(co)).dot(Vector(no))


def V_(bm, p, tol=0.004):
    """The base vertex at a carved position (from carve_base.json); asserts it is there."""
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < tol, ('no vertex at', p, tuple(v.co))
    return v


def stage2(k, body):
    bm = edit(body)
    # --- face planes (round s2 r01): eye socket, brow ridge over it, a stop between skull and muzzle
    sock = face_near(bm, (0.114, -0.656, 0.560), n=(1, 0, 0))
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face, sunk'):
        inner = inset(bm, [sock], 0.42)
    move(inner[0].verts, (-0.010, 0.006, 0.0))
    brow = V_(bm, (0.112, -0.662, 0.606))                 # socket top corner -> brow ridge, forward and out
    move([brow], (0.012, -0.014, 0.010))
    move([V_(bm, (0.063, -0.680, 0.644))], (0.004, -0.016, 0.004))     # inner brow forward
    move([V_(bm, (0.0, -0.686, 0.634))], (0.0, -0.014, 0.0))           # forehead forward over the stop
    move([V_(bm, (0.0, -0.699, 0.605))], (0.0, 0.004, -0.018))          # the stop: a step down to the muzzle
    move([V_(bm, (0.065, -0.706, 0.589))], (0.0, 0.004, -0.020))
    move([V_(bm, (0.0, -0.714, 0.564))], (0.0, 0.0, -0.008))            # straight muzzle top
    # --- big planes on the torso (team pass, must-fix 1): the hull's speckle becomes a few large facets
    for _ in range(FACET_PASSES):                    # repeated: each pass refits the planes to the moved surface
        facet(bm, torso_face, K=FACET_K, lam=FACET_LAM, max_d=FACET_MAXD, fit=FACET_FIT)
    say('torso before denoise: ' + speckle(bm, torso_face))
    if DENOISE:                                      # second pass (verifier: still small light-catching facets)
        denoise(bm, torso_face, **DENOISE)
    say('torso after denoise: ' + speckle(bm, torso_face))
    # --- hind leg (team pass, must-fix 2): a hock bulge at the back, a narrower shin, a flat plantigrade foot
    hind = lambda c: c.y > 0.28 and c.z < 0.85
    cut(k, bm, (0, 0, HOCK_Z), (0, 0, 1), hind, 'hind leg: a loop at the hock, so the rear edge can bend')
    cut(k, bm, (0, 0, SHIN_Z), (0, 0, 1), hind, 'hind leg: a loop on the shin, under the hock')
    ring_at = lambda z, pred: [v for v in bm.verts if abs(v.co.z - z) < 0.004 and pred(v.co)]
    move(ring_at(HOCK_Z, lambda c: c.y > 0.60 and c.x > 0.07), (0, 0.065, 0))          # hock pulled back
    move(ring_at(SHIN_Z, lambda c: c.y > 0.60 and c.x > 0.07), (0, -0.05, 0))          # shin back edge in: the hock angle
    move(verts_where(bm, lambda c: c.y > 0.28 and c.y < 0.40 and c.z < 0.07), (0, -0.045, 0))   # toes forward
    flatten(verts_where(bm, lambda c: c.y > 0.28 and c.y < 0.45 and 0.055 < c.z < 0.13))     # foot top: one plane
    # second pass (verifier: no visible hock angle, shin a slab): the shin's FRONT edge goes back under the knee,
    # most at the ankle, so the leg tapers from thigh to ankle and the flat foot sticks out forward of it
    for v in verts_where(bm, lambda c: 0.28 < c.y < 0.47 and 0.135 < c.z < HOCK_Z - 0.005):
        t = min(1.0, (HOCK_Z - v.co.z) / (HOCK_Z - SHIN_Z - 0.02))
        move([v], (0, ANKLE_IN * t * min(1.0, (0.47 - v.co.y) / 0.05), 0))
    # --- front legs off the chest (team pass, must-fix 4): chest floor up, armpits in, brisket back, shoulder out
    move(verts_where(bm, lambda c: c.x < 0.05 and -0.32 < c.y < -0.20 and c.z < 0.30), (0, 0, FLOOR_UP))
    move(verts_where(bm, lambda c: 0.05 < c.x < 0.09 and -0.30 < c.y < -0.22 and c.z < 0.30), (0.02, 0, 0.01))
    move(verts_where(bm, lambda c: c.x < 0.12 and -0.42 < c.y < -0.28 and 0.30 < c.z < 0.42), (0, 0.035, 0))
    move(verts_where(bm, lambda c: c.x > 0.27 and -0.32 < c.y < 0.0 and 0.42 < c.z < 0.62), (0.012, 0, 0))
    # --- colour borders on edge loops (round s2 r02): a planar loop cut through the region, so the border is a straight run
    for name, (co, no, box) in CUTS.items():
        cut(k, bm, co, no, box, name)
    # second pass (verifier: legs still drop straight out of the chest): a loop where the leg leaves the body; above
    # it the shoulder ring goes out, below it the leg is narrowed about its own axis down to the wrist, so the
    # shoulder and chest overhang the leg (a shadow step) and the leg reads as a column under a mass
    # the hull's chest front and leg front are ONE sheet (triangles run from the breastbone to the outer leg), so a
    # vertical loop splits it where the leg meets the chest, and that line is sunk: a groove, the armpit shadow
    cut(k, bm, (CLEFT_X, 0, 0), (1, 0, 0), lambda c: c.y < -0.20 and 0.17 < c.z < 0.47 and c.x < 0.31,
        'chest front: a vertical loop between breastbone and leg, so the leg can separate from the chest')
    move(verts_where(bm, lambda c: abs(c.x - CLEFT_X) < 0.004 and c.y < -0.20 and 0.17 < c.z < 0.40), (0, CLEFT_D, 0))
    fleg = lambda c: -0.45 < c.y < 0.0 and c.z < 0.52 and c.x > 0.085
    cut(k, bm, (0, 0, ARM_Z), (0, 0, 1), fleg, 'front leg: a loop under the shoulder, where the leg leaves the body')
    ax = Vector((J['elbowL'][0], J['elbowL'][1], 0.0))
    for v in verts_where(bm, lambda c: fleg(c) and 0.115 < c.z < ARM_Z + 0.004):
        top = abs(v.co.z - ARM_Z) < 0.004
        f = ARM_OUT if top else ARM_IN + (1.0 - ARM_IN) * max(0.0, (0.20 - v.co.z) / 0.085)
        move([v], ((v.co.x - ax.x) * (f - 1.0), (v.co.y - ax.y) * (f - 1.0), 0))
    commit(body, bm)


ARM_Z, ARM_OUT, ARM_IN = 0.355, 1.06, 0.84
CLEFT_X, CLEFT_D = 0.10, 0.02
FLOOR_UP = 0.0
FACET_K, FACET_LAM, FACET_PASSES, FACET_MAXD, FACET_FIT = 14, 0.002, 12, 0.02, 1
DENOISE = None
HOCK_Z, SHIN_Z = 0.37, 0.19
ANKLE_IN = 0.06
ATK_REAR = 18
ATK_ROLL = 8          # chest roll at the strike: the right shoulder drops
torso_face = lambda f: all(v.co.z > 0.33 and v.co.y > -0.45 for v in f.verts)


def min_angle(f):
    vs = [v.co for v in f.verts]
    out = 180.0
    for i in range(len(vs)):
        a, b = vs[i - 1] - vs[i], vs[(i + 1) % len(vs)] - vs[i]
        if a.length > 1e-9 and b.length > 1e-9:
            out = min(out, math.degrees(a.angle(b)))
    return out


def facet(bm, mask, K=16, lam=0.08, iters=12, max_d=0.03, seed=3, fit=1):
    """Planar facets (a VSA-style fit): the masked faces are clustered by normal and position into K regions,
    each region gets one plane (area-weighted normal and centroid), and every vertex is moved to the least-squares
    meet of the planes of the regions around it (pulled back to where it was by lam, capped at max_d). Vertices
    that touch an unmasked face stay put, so the head, legs and borders do not move; seam vertices stay on x = 0."""
    F = sorted((f for f in bm.faces if mask(f)), key=lambda f: tuple(round(x, 5) for x in f.calc_center_median()))
    if not F:
        return
    orig = {v: v.co.copy() for f in F for v in f.verts}
    N = np.array([f.normal[:] for f in F]); C = np.array([f.calc_center_median()[:] for f in F])
    A = np.array([f.calc_area() for f in F])
    X = np.hstack([N, C / 0.35])
    rng = np.random.default_rng(seed)
    ctr = X[rng.choice(len(F), K, replace=False, p=A / A.sum())]
    for _ in range(iters):
        lab = np.argmin(((X[:, None, :] - ctr[None]) ** 2).sum(-1), axis=1)
        for j in range(K):
            m = lab == j
            if m.any():
                ctr[j] = (X[m] * A[m, None]).sum(0) / A[m].sum()
    fl = {f: lab[i] for i, f in enumerate(F)}
    for _fit in range(fit):                          # fixed regions: refit the planes, move, repeat (converges to planes)
        for f in F:
            f.normal_update()
        N = np.array([f.normal[:] for f in F]); C = np.array([f.calc_center_median()[:] for f in F])
        A = np.array([f.calc_area() for f in F])
        planes = {}
        for j in range(K):
            m = lab == j
            if not m.any():
                continue
            n = (N[m] * A[m, None]).sum(0); n /= np.linalg.norm(n)
            c = (C[m] * A[m, None]).sum(0) / A[m].sum()
            planes[j] = (n, float(n @ c))
        new = {}
        for v in {v for f in F for v in f.verts}:
            if any(f not in fl for f in v.link_faces):
                continue
            p0 = np.array(v.co[:]); seam = abs(p0[0]) < 1e-4
            ks = {fl[f] for f in v.link_faces}
            M = lam * np.eye(3); b = lam * p0
            for j in ks:
                n, d = planes[j]
                M += np.outer(n, n); b += n * d
            if seam:
                M2, b2 = M[1:, 1:], b[1:] - M[1:, 0] * 0.0
                q = np.concatenate([[0.0], np.linalg.solve(M2, b2)])
            else:
                q = np.linalg.solve(M, b)
            o = np.array(orig[v][:]); dv = q - o; L = np.linalg.norm(dv)      # capped from where the vertex started
            if L > max_d:
                dv *= max_d / L
            new[v] = Vector(o + dv)
        mx = max(((new[v] - v.co).length for v in new), default=0.0)
        back = 0  
        bm.verts.index_update()
        for v, q in sorted(new.items(), key=lambda t: t[0].index):   # a move that would make a needle triangle is shortened (fixed order)
            p0 = v.co.copy()
            before = min((min_angle(f) for f in v.link_faces), default=90.0)
            for t in (1.0, 0.6, 0.3, 0.0):
                v.co = p0.lerp(q, t)
                if t == 0.0 or min(min_angle(f) for f in v.link_faces) >= min(8.0, before):
                    break
            back += t < 1.0
    undone = 0
    for _ in range(6):                               # a move that makes two faces cross is undone
        tree = BVHTree.FromBMesh(bm)
        bm.faces.ensure_lookup_table()
        bad = set()
        for i, j in tree.overlap(tree):
            fi, fj = bm.faces[i], bm.faces[j]
            if i < j and not set(fi.verts) & set(fj.verts):
                bad |= set(fi.verts) | set(fj.verts)
        bad = {v for v in bad if v in orig and (v.co - orig[v]).length > 1e-7}
        if not bad:
            break
        for v in bad:
            v.co = orig[v]
        undone += len(bad)
    for f in bm.faces:
        f.normal_update()
    say(f'facet: {undone} moves undone (crossing faces); {len(F)} faces -> {len(planes)} planes, {len(new)} verts moved, max {mx:.3f}, {back} shortened')


def speckle(bm, mask):
    """Share of the masked surface's edge length that is flat (< 4 deg), speckle (4-18 deg) or a crease (> 18 deg)."""
    fs = {f for f in bm.faces if mask(f)}
    b = [0.0, 0.0, 0.0]
    for e in {e for f in fs for e in f.edges}:
        lf = [f for f in e.link_faces if f in fs]
        if len(lf) == 2:
            a = math.degrees(lf[0].normal.angle(lf[1].normal, 0.0))
            b[0 if a < 4 else 1 if a < 18 else 2] += e.calc_length()
    t = sum(b) or 1.0
    return 'flat %.0f%% speckle %.0f%% crease %.0f%%' % tuple(100 * x / t for x in b)


def denoise(bm, mask, sigma=0.3, n_iters=6, v_iters=12, max_d=0.025):
    """Bilateral normal filtering (mesh denoising): each masked face's normal is averaged with its neighbours'
    (edge+vertex ring), weighted by area and by how close the normals already are (sigma, in |dn|), so near-equal
    neighbours merge into one plane and real creases stay; then vertices are moved to fit the filtered normals
    (Sun et al. 2007). Vertices touching an unmasked face stay; seam vertices stay on x = 0; moves capped at max_d."""
    F = [f for f in bm.faces if mask(f)]
    fset = set(F)
    free = [v for v in {v for f in F for v in f.verts} if all(f in fset for f in v.link_faces)]
    p0 = {v: v.co.copy() for v in free}
    nb = {f: {g for v in f.verts for g in v.link_faces if g in fset} for f in F}
    for f in F:
        f.normal_update()
    n = {f: f.normal.copy() for f in F}
    A = {f: f.calc_area() for f in F}
    for _ in range(n_iters):
        m = {}
        for f in F:
            acc = Vector((0, 0, 0))
            for g in nb[f]:
                w = A[g] * math.exp(-((n[f] - n[g]).length / sigma) ** 2)
                acc += n[g] * w
            m[f] = acc.normalized()
        n = m
    for _ in range(v_iters):
        C = {f: f.calc_center_median() for f in F}
        for v in free:
            d = Vector((0, 0, 0))
            fs = v.link_faces
            for f in fs:
                d += n[f] * n[f].dot(C[f] - v.co)
            q = v.co + d / len(fs)
            if abs(p0[v].x) < 1e-4:
                q.x = 0.0
            off = q - p0[v]
            if off.length > max_d:
                q = p0[v] + off * (max_d / off.length)
            v.co = q
    for f in bm.faces:
        f.normal_update()
    say(f'denoise: {len(F)} faces, {len(free)} verts, max move {max(((v.co - p0[v]).length for v in free), default=0):.3f}')


def cut(k, bm, co, no, box, reason, dist=0.012):
    """A planar loop through the faces whose vertices all satisfy box(co): bisect_plane, new verts on base edges only
    (a loop that dissolves back out). Vertices within dist of the plane count as on it (no sliver cuts)."""
    faces = [f for f in bm.faces if all(box(v.co) for v in f.verts)]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    with k.topo(bm, 'loop', reason):
        bmesh.ops.bisect_plane(bm, geom=geom, dist=dist, plane_co=Vector(co), plane_no=Vector(no).normalized())


BRIEF = {'fur': '#6b4a33', 'dark': '#4a3222', 'muzzle': '#c9a57d', 'nose': '#1e1714', 'claw': '#2a221e', 'eye': '#151010'}


def _rgb(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def sheet_palette(k, body):
    """colour_from_sheet's clusters, each brief role taking its nearest sheet colour (the sheet's own values);
    the paint itself is by rules on the stage-2 loops, so the borders are clean."""
    sheet = colour_from_sheet(k, [body], chroma=1.35)
    say(f'sheet clusters: {sheet}')
    pal = {}
    for role, h in BRIEF.items():
        best = min(sheet.values(), key=lambda s: sum((p - q) ** 2 for p, q in zip(_rgb(s), _rgb(h))))
        d = sum((p - q) ** 2 for p, q in zip(_rgb(best), _rgb(h))) ** 0.5
        pal[role] = best if d < 40 and best not in pal.values() else h
    say(f'palette (sheet where near, else brief): {pal}')
    return pal


def ray_hit(tree, o, d):
    hit = tree.ray_cast(Vector(o), Vector(d).normalized())
    assert hit[0] is not None, ('ray missed', o, d)
    return hit[0], hit[1]


def hook(bm, base, ang, L, hw, hh, sy):
    """k3's claw: a base quad rooted in the toe, a smaller mid quad, the tip bent down to the ground line."""
    a = math.radians(ang)
    d = Vector((math.sin(a), sy * math.cos(a), 0.0))
    s = Vector((math.cos(a), -sy * math.sin(a), 0.0))
    z = Vector((0.0, 0.0, 1.0))
    B = Vector(base)
    M = B + d * (0.6 * L) - z * (0.15 * L)
    T = B + d * L
    T.z = 0.003
    q0 = ring(bm, [B + s * u * hw + z * w * hh for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    q1 = ring(bm, [M + s * u * hw * 0.6 + z * w * hh * 0.6 for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bridge(bm, q0, q1, closed=True)
    bm.faces.new(list(reversed(q0)))
    tip = bm.verts.new(T)
    for i in range(4):
        bm.faces.new([q1[i], q1[(i + 1) % 4], tip])


def dome(bm, c, nrm, r, front, back, sides=8):
    """k3's eye: a back ring sunk in the socket, a rim ring and a low front cap."""
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


def ear(bm, c, facing, up, r, thick, cup):
    """A round cup ear: an 8-sided disc (front and back rings), the front cupped by a sunk inner ring."""
    f = Vector(facing).normalized()
    u = (Vector(up) - f * Vector(up).dot(f)).normalized()
    s = u.cross(f)
    pts = lambda rad, o: [Vector(c) + f * o + (s * math.cos(2 * math.pi * i / 8) + u * math.sin(2 * math.pi * i / 8)) * rad
                          for i in range(8)]
    fr = ring(bm, pts(r, thick * 0.5))
    bk = ring(bm, pts(r * 0.92, -thick * 0.5))
    inn = ring(bm, pts(r * 0.58, thick * 0.5 - cup))
    bridge(bm, bk, fr, closed=True)
    bridge(bm, fr, inn, closed=True)
    cap(bm, inn)
    cap(bm, list(reversed(bk)))
    return f


def body_rule(body, sock_c, tol=0.013):
    """Region by the face's VERTICES (all of them on the region's side of its loop, within the cut tolerance),
    so every border runs along a stage-2 loop, never across a triangle."""
    me = body.data
    fv = [[Vector((abs(me.vertices[j].co.x), me.vertices[j].co.y, me.vertices[j].co.z)) for j in p.vertices] for p in me.polygons]
    def inside(vs, box, *planes):
        return all(box(v) for v in vs) and all(side_of(v, pl) < tol for v in vs for pl in planes)
    def rule(c, n, i):
        c = Vector((abs(c.x), c.y, c.z))
        vs = fv[i]
        if (c - sock_c).length < 0.024 and n.x > 0.2:
            return 'dark'                                    # the eye socket: a shadow ring round the lens
        if inside(vs, in_head, MUZ):
            return 'muzzle'
        if inside(vs, in_chest, BIB_V, BIB_Y, BIB_T):
            return 'muzzle'                                  # the pale bib
        if all(v.z < LEG_Z + tol for v in vs):
            return 'dark'
        return 'fur'
    return rule


EAR_FACING = (0.45, -1.0, 0.1)


def stage3(k, body):
    pal = sheet_palette(k, body)
    pal['dark'] = BRIEF['dark']                      # team pass, must-fix 3: the sheet's dark (#403832) read grey; the brief's warm brown
    hb = edit(body)
    tree = BVHTree.FromBMesh(hb)
    cands = [f for f in hb.faces if (f.calc_center_median() - Vector((0.114, -0.656, 0.560))).length < 0.04 and f.normal.x > 0.2]
    sock = min(cands, key=lambda f: f.calc_area())
    sock_c, sock_n = sock.calc_center_median(), sock.normal.copy()
    paint(body, pal, body_rule(body, sock_c))
    pieces = []
    # eyes: a low dome in the socket, turned toward -Y so it reads head-on too
    bm = bmesh.new()
    en = (sock_n + Vector((0.0, -0.4, 0.0))).normalized()
    dome(bm, sock_c + sock_n * 0.009, en, 0.019, 0.006, 0.012)   # lens front ~0.005 proud of the socket rim
    eye = object_from_bm('eye', bm, mirror=True)
    paint(eye, {'eye': pal['eye']}, lambda c, n, i: 'eye')
    pieces.append(eye)
    # ears: round cups on the top-back corner of the skull, seated on the surface found by a ray
    hit, nrm = ray_hit(tree, (0.125, -0.50, 1.2), (0, 0, -1))
    bm = bmesh.new()
    f = ear(bm, hit + Vector((0.010, 0.0, 0.038)), EAR_FACING, (0.3, 0.0, 1.0), 0.056, 0.034, 0.014)
    ears = object_from_bm('ears', bm, mirror=True)
    paint(ears, {'fur': pal['fur']}, lambda c, n, i: 'fur')   # the cup reads by shading; a dark inner disc read as a goggle
    pieces.append(ears)
    # nose pad: a black block on the snout tip, its back half buried
    tip, _ = ray_hit(tree, (0.0001, -1.2, 0.462), (0, 1, 0))
    y0 = tip.y
    bm = bmesh.new()
    bk = ring(bm, [(0, y0 + 0.022, 0.432), (0.034, y0 + 0.022, 0.440), (0.038, y0 + 0.022, 0.488), (0, y0 + 0.022, 0.498)])
    fr = ring(bm, [(0, y0 - 0.012, 0.440), (0.026, y0 - 0.012, 0.446), (0.030, y0 - 0.008, 0.482), (0, y0 - 0.008, 0.490)])
    bridge(bm, bk, fr)
    cap(bm, fr)
    cap(bm, list(reversed(bk)))
    nose = object_from_bm('nose', bm, mirror=True)
    paint(nose, {'nose': pal['nose']}, lambda c, n, i: 'nose')
    pieces.append(nose)
    # claws: five graded hooks per paw, rooted where a ray from the front meets the toe
    bm = bmesh.new()
    for cx, y_from, L0, hw, hh, zb in ((0.212, -0.8, 0.044, 0.014, 0.011, 0.026), (0.200, 0.10, 0.034, 0.012, 0.009, 0.020)):
        for o, ang, g in ((-0.076, -14, 0.8), (-0.038, -7, 1.0), (0.0, 0, 1.0), (0.038, 7, 1.0), (0.076, 14, 0.8)):
            p, _ = ray_hit(tree, (cx + o, y_from, zb), (0, 1, 0))
            hook(bm, (p.x, p.y + 0.010, zb), ang, L0 * g, hw, hh, -1)
    claws = object_from_bm('claws', bm, mirror=True)
    paint(claws, {'claw': pal['claw']}, lambda c, n, i: 'claw')
    pieces.append(claws)
    # tail: a short stub off the rump, high, hanging back and down
    p, _ = ray_hit(tree, (0.0001, 1.5, 0.66), (0, -1, 0))
    bm = bmesh.new()
    b0 = Vector((0.0, p.y - 0.025, 0.66))
    rr = lambda o, r, dz: [b0 + Vector((r * math.sin(math.pi * i / 4), o, dz + r * 0.8 * math.cos(math.pi * i / 4))) for i in range(5)]
    r0, r1 = ring(bm, rr(0.0, 0.050, 0.0)), ring(bm, rr(0.055, 0.042, -0.018))
    bridge(bm, r0, r1)
    t = bm.verts.new(b0 + Vector((0.0, 0.085, -0.050)))
    for i in range(4):
        bm.faces.new([r1[i], r1[i + 1], t])
    cap(bm, list(reversed(r0)))
    tail = object_from_bm('tail', bm, mirror=True)
    paint(tail, {'fur': pal['fur']}, lambda c, n, i: 'fur')
    pieces.append(tail)
    hb.free()
    return pieces


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
        bind(p, rig, body=body)                    # every piece borrows the skin weights under it (no drift)
    clip(rig, 'idle', {1: {}, 12: {'chest': (1.5, 0, 0), 'neck': (-3, 0, 0), 'head': (-6, 0, 4)},
                       24: {'neck': (2, 0, 0), 'head': (5, 0, 0)},
                       36: {'chest': (1.5, 0, 0), 'neck': (-3, 0, 0), 'head': (-6, 0, -4)}, 48: {}})
    A, H = 14, 12
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-H, 0, 0), 'thigh.R': (H, 0, 0),
            'chest': (0, 0, 2), 'head': (-3, 0, 0)},
        9: {'forearm.R': (-20, 0, 0), 'paw.R': (-12, 0, 0), 'shin.L': (-12, 0, 0), 'foot.L': (10, 0, 0),
            'head': (2, 0, 0)},
        17: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (H, 0, 0), 'thigh.R': (-H, 0, 0),
             'chest': (0, 0, -2), 'head': (-3, 0, 0)},
        25: {'forearm.L': (-20, 0, 0), 'paw.L': (-12, 0, 0), 'shin.R': (-12, 0, 0), 'foot.R': (10, 0, 0),
             'head': (2, 0, 0)},
        33: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-H, 0, 0), 'thigh.R': (H, 0, 0),
             'chest': (0, 0, 2), 'head': (-3, 0, 0)}})
    # attack (team pass, must-fix 5): a lunge (body forward ~10% of length, down, head up) with the left paw
    # raised to chest height, then swept across toward the midline; the right shoulder drops; thighs and the
    # right arm swing back by the lunge's distance so the planted feet stay put
    S = ATK_REAR                                     # second pass: the body rears about the pelvis, so the paw gets high without folding the chest
    clip(rig, 'attack', {
        1: {},
        10: {'spine': (S, 0, 0), 'chest': (-4, 0, 0), 'neck': (6, 0, 0), 'head': (12, 0, 0),
             'upperarm.L': (40, 0, 10), 'forearm.L': (25, 0, 0), 'paw.L': (10, 0, 0),
             'upperarm.R': (-14, 0, 0), 'thigh.L': (-S, 0, 0), 'thigh.R': (-S, 0, 0)},
        20: {'spine': (S * 0.6, 0, 0), 'chest': (-6, ATK_ROLL, 0), 'neck': (2, 0, 0), 'head': (6, 0, -10),
             'upperarm.L': (38, 0, -16), 'forearm.L': (20, 0, 0), 'paw.L': (-10, 0, 0),
             'upperarm.R': (-17, 0, 0), 'thigh.L': (-S * 0.6, 0, 0), 'thigh.R': (-S * 0.6, 0, 0)},
        28: {'chest': (-2, 0, 0), 'head': (2, 0, -4), 'upperarm.L': (18, 0, -8), 'forearm.L': (-6, 0, 0),
             'upperarm.R': (-6, 0, 0)},
        40: {}},
        loc={1: {'spine': (0, 0, 0)}, 10: {'spine': (0, 0.04, 0.0)}, 20: {'spine': (0, 0.08, 0.0)},
             28: {'spine': (0, 0.03, 0.0)}, 40: {'spine': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
