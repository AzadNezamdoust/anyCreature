import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# setting c1 "carve + detail": stage 1 carved from reference/ (a visual hull) plus hand edits; detail in stages 2-4
META = dict(creature='owl', model='opus', engine_glb='')

J = dict(
    root=(0.0, 0.02, 0.10), spine=(0.0, -0.02, 0.25), chest=(0.0, -0.04, 0.39),
    head=(0.0, -0.07, 0.43), crown=(0.0, -0.08, 0.61),
    tail0=(0.0, 0.12, 0.17), tail1=(0.0, 0.20, 0.08),
    hipL=(0.067, -0.045, 0.10), ankleL=(0.067, -0.045, 0.035), toeL=(0.067, -0.13, 0.01),
    shoulderL=(0.13, -0.06, 0.37), wingtipL=(0.12, 0.125, 0.18),
)


def V_(bm, p, tol=0.004):
    """The base vertex at a carved position (from carve_base.json); asserts it is there."""
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < tol, ('no vertex at', p, tuple(v.co))
    return v


# ear tufts: the hull truncates the thin tuft blade (voxel 7 mm); pull its top verts into a point (front view tip
# x .117 z .642, side view tip y -.059 z .640), the outer edge under it, and the inner slope down into the V
TUFT = [((0.097443, -0.070911, 0.620358), (0.118, -0.064, 0.648)),
        ((0.110047, -0.063938, 0.618871), (0.126, -0.056, 0.628)),
        ((0.086113, -0.04819, 0.612133), (0.090, -0.050, 0.604))]


def stage1(k):
    body = carve_base(k, mask_blur=1, blur=0)
    bm = edit(body)
    for p, q in TUFT:
        V_(bm, p).co = Vector(q)
    commit(body, bm)
    return body


# colour borders, cut into the triangulated carve as planar loops (bisect_plane inside k.topo 'loop')
WING = ((0.0, -0.039, 0.264), (0.0, 0.894, 0.447))   # side view: the folded wing's front edge, shoulder -> tail root
WING_X = ((0.135, 0.0, 0.0), (1.0, 0.0, 0.0))         # front view: the wing's inner edge on the chest
BIB = ((0.0, 0.0, 0.345), (0.0, 0.0, 1.0))            # front: brown upper chest over the cream belly
BAND_SNAP = 0.006
CHEST = ((0.0, 0.0, 0.400), (0.0, 0.0, 1.0))          # team M5: brown upper chest over the mid-tan band
LEG = ((0.0, 0.0, 0.036), (0.0, 0.0, 1.0))            # team M3: ankle loop; cream leg above, tan toes below
in_flank = lambda c: c.x > 0.05 and 0.09 < c.z < 0.44
in_chest = lambda c: c.y < -0.04 and 0.28 < c.z < 0.42
in_front = lambda c: c.y < 0.06 and 0.12 < c.z < 0.42
CUTS = {
    'wing front edge (side view), shoulder to tail root': (*WING, in_flank),
    'wing inner edge (front view) on the chest': (*WING_X, in_front),
    'bib: mid-tan band over the cream belly': (*BIB, in_chest),
    'chest: brown upper chest over the mid-tan band (team M5)': (*CHEST, in_chest),
    'ankle: border loop round each leg, cream leg over tan toes': (*LEG, lambda c: c.z < 0.11),
}


def side_of(c, plane):
    co, no = plane
    return (Vector(c) - Vector(co)).dot(Vector(no))


def cut(k, bm, co, no, box, reason, dist=0.012):
    """A planar loop through the faces whose vertices all satisfy box(co) (the bear's helper)."""
    faces = [f for f in bm.faces if all(box(v.co) for v in f.verts)]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    with k.topo(bm, 'loop', reason):
        bmesh.ops.bisect_plane(bm, geom=geom, dist=dist, plane_co=Vector(co), plane_no=Vector(no).normalized())


# face: the hull's face is a prow (seam 3 cm ahead of the eye column); an owl's face is a flat dish with the rim forward
FACE = [((0.0, -0.192534, 0.511825), (0.0, 0.012, 0.0)),
        ((0.0, -0.197218, 0.503506), (0.0, 0.010, 0.0)),
        ((0.014849, -0.197553, 0.502408), (0.0, 0.014, 0.0)),
        ((0.0, -0.180986, 0.530513), (0.0, 0.006, 0.0)),
        ((0.051133, -0.184629, 0.508279), (0.0, 0.006, 0.0)),
        ((0.083323, -0.163119, 0.492306), (0.0, -0.008, 0.0)),
        ((0.084885, -0.168115, 0.476698), (0.0, -0.005, 0.0)),
        ((0.082018, -0.151202, 0.49941), (0.0, -0.010, 0.0)),
        # the side view's beak carved as a seam bump: back into the face, the beak piece replaces it
        ((0.0, -0.214875, 0.443979), (0.0, 0.020, 0.0)),
        ((0.0, -0.211917, 0.432066), (0.0, 0.018, 0.0)),
        ((0.0, -0.206877, 0.424975), (0.0, 0.012, 0.0))]


FOOT_X = 0.067
FOOT_W, FOOT_TOP, FOOT_FWD = 0.30, 0.030, 0.015     # second pass M3: 50% -> 30%, the plate is now the middle
                                                     # + rear toe only; the side toes are stage-3 pieces


def stage2(k, body):
    bm = edit(body)
    for p, d in FACE:
        move([V_(bm, p)], d)
    # feet: the hull of the sheet's spread talons is a 10 cm slab; narrow it about the leg (x .067) and pull the
    # outer front corners back so the middle toe leads (a toe fan, the talons do the rest)
    # team M3: narrowed further to 50% (r04 72%), the foot squashed to toe height (top .045 -> .030), the front
    # verts pushed 15 mm forward so the toes lead out from under a feathered leg
    for v in verts_where(bm, lambda c: c.z < 0.045 and c.y < 0.045 and c.x > 0.0):
        v.co.x = FOOT_X + (v.co.x - FOOT_X) * FOOT_W
        if v.co.y < -0.09:
            v.co.x = FOOT_X + (v.co.x - FOOT_X) * 0.7               # second pass M3: the middle toe tapers
            v.co.y += 0.35 * abs(v.co.x - FOOT_X) - FOOT_FWD
        v.co.z *= FOOT_TOP / 0.045
    for name, (co, no, box) in CUTS.items():
        cut(k, bm, co, no, box, name, dist=BAND_SNAP if name.startswith(('bib', 'chest')) else 0.012)
    commit(body, bm)


BRIEF = {'brown': '#7a5a3c', 'dark': '#4a3424', 'cream': '#efe3c6', 'tan': '#b08a64',
         'orange': '#f08a1c', 'black': '#111111', 'beak': '#2e2b2a', 'primary': '#35251a'}


def _rgb(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def sheet_palette(k, body):
    """colour_from_sheet's clusters, each brief role taking its nearest sheet colour where one is near (the bear's
    rule); the paint itself is by rules on the stage-2 loops, so the borders are clean."""
    sheet = colour_from_sheet(k, [body], chroma=1.2)
    say(f'sheet clusters: {sheet}')
    pal = {}
    for role, h in BRIEF.items():
        best = min(sheet.values(), key=lambda s: sum((p - q) ** 2 for p, q in zip(_rgb(s), _rgb(h))))
        d = sum((p - q) ** 2 for p, q in zip(_rgb(best), _rgb(h))) ** 0.5
        pal[role] = best if d < 16 and best not in pal.values() else h
    say(f'palette (sheet where near, else brief): {pal}')
    return pal


def body_rule(body, tol=0.013):
    """Region by the face's VERTICES (all on the region's side of its loop), so borders run along stage-2 loops."""
    me = body.data
    fv = [[Vector((abs(me.vertices[j].co.x), me.vertices[j].co.y, me.vertices[j].co.z)) for j in p.vertices]
          for p in me.polygons]
    def rule(c, n, i):
        vs = fv[i]
        if all(v.z > 0.575 and v.x > 0.065 for v in vs):
            return 'dark'                                            # ear tufts
        if all(v.y > 0.115 for v in vs):
            return 'dark'                                            # tail wedge (team M4: no tan behind the legs)
        if all(v.z < LEG[0][2] + 0.003 for v in vs):
            return 'tan'                                             # toes (under the ankle loop)
        if all(v.y > 0.115 and v.z < 0.24 for v in vs):
            return 'dark'                                            # tail
        if all(side_of(v, WING) > -tol and v.x > 0.05 and v.z < 0.45 for v in vs):
            return 'brown'                                           # flank under the wing plate
        if all(v.x > WING_X[0][0] - tol and v.y < 0.06 and 0.11 < v.z < 0.43 for v in vs):
            return 'brown'                                           # wing edge seen from the front
        if all(v.z < BIB[0][2] + 0.004 and v.y < 0.02 for v in vs):
            return 'cream'                                           # lower belly, border on the bib loop
        if all(v.z < CHEST[0][2] + 0.004 and v.y < -0.03 for v in vs):
            return 'tan'                                             # mid-tan chevron band between the loops
        return 'brown'
    return rule


# ------------------------------------------------------------------ face pieces (k3's, re-seated on the carve)
EYE_C0 = Vector((0.066, -0.17, 0.502))
EYE_N = Vector((0.258, -0.966, 0.0)).normalized()
EYE_C = EYE_C0.copy()                    # set in stage3 from the skin
DISC_R = (0.034, 0.055, 0.063)


def basis(n):
    n = Vector(n).normalized(); u = n.cross(Vector((0, 0, 1))).normalized(); w = u.cross(n)
    return n, u, w


def dome(bm, c, n, rings, apex, sides=12, rot=15.0):
    n, u, w = basis(n)
    dirs = [u * math.cos(math.radians(rot + 360 * i / sides)) + w * math.sin(math.radians(rot + 360 * i / sides))
            for i in range(sides)]
    rs = [ring(bm, [c + n * d + q * r for q in dirs]) for r, d in rings]
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, rs[0])
    top = ring(bm, [c + n * apex])[0]
    last = rs[-1]
    for i in range(sides):
        bm.faces.new([last[i], last[(i + 1) % sides], top])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def lens(bm, c, n, rim, back, back_apex, front, front_apex, sides=12, rot=15.0):
    n, u, w = basis(n)
    dirs = [u * math.cos(math.radians(rot + 360 * i / sides)) + w * math.sin(math.radians(rot + 360 * i / sides))
            for i in range(sides)]
    rr = ring(bm, [c + n * rim[1] + q * rim[0] for q in dirs])
    for rows, apex in ((back, back_apex), (front, front_apex)):
        prev = rr
        for r, d in rows:
            cur = ring(bm, [c + n * d + q * r for q in dirs]); bridge(bm, prev, cur, closed=True); prev = cur
        top = ring(bm, [c + n * apex])[0]
        for i in range(sides):
            bm.faces.new([prev[i], prev[(i + 1) % sides], top])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def skin_trees(me):
    """Both triangulations of each quad (the export folds quads out): a skin depth takes the front one."""
    vs = [v.co.copy() for v in me.vertices]
    trees = []
    for alt in (0, 1):
        tris = []
        for pg in me.polygons:
            ids = list(pg.vertices)
            if len(ids) == 4 and alt:
                ids = ids[1:] + ids[:1]
            tris += [(ids[0], ids[j], ids[j + 1]) for j in range(1, len(ids) - 1)]
        trees.append(BVHTree.FromPolygons(vs, tris))
    return trees


# facial disc (team M2): ONE cream heart over both eyes, top at the brow line, bottom at the beak tip; the half
# outline in the front view (x, z), closed by the seam x = 0; dark rim 10 mm on the outer edge only
DISC_OUT = [(0.0, 0.532), (0.030, 0.546), (0.060, 0.566), (0.088, 0.576), (0.108, 0.560), (0.119, 0.530),
            (0.121, 0.500), (0.114, 0.470), (0.097, 0.452), (0.070, 0.443), (0.038, 0.440), (0.0, 0.442)]
BEAK_UP = 0.020
DISC_HOLE, DISC_RIM, DISC_SIDES = 0.020, 0.010, 16


def outline_hit(ex, ez, th):
    """Distance from the eye (ex, ez) along th to the half outline (closed by the seam); and whether it is the seam."""
    dx, dz = math.cos(th), math.sin(th)
    best = (1e9, False)
    poly = DISC_OUT + [DISC_OUT[0]]
    for i, ((x0, z0), (x1, z1)) in enumerate(zip(poly, poly[1:])):
        ex_, ez_ = x1 - x0, z1 - z0
        den = dx * ez_ - dz * ex_
        if abs(den) < 1e-12:
            continue
        t = ((x0 - ex) * ez_ - (z0 - ez) * ex_) / den
        u = ((x0 - ex) * dz - (z0 - ez) * dx) / den
        if t > 0 and -1e-9 <= u <= 1 + 1e-9 and t < best[0]:
            best = (t, i == len(DISC_OUT) - 1)
    return best


def disc_piece(me, pal):
    trees = skin_trees(me)
    ex, ez = EYE_C.x, EYE_C.z
    def skin_y(x, z):
        ys = [t.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))[0] for t in trees]
        ys = [h.y for h in ys if h is not None]
        return min(ys) if ys else -0.12
    def pt(x, z, front):
        if front:   # clear the skin's frontmost point around it (the carve bulges between samples)
            y = min(skin_y(x + dx, z + dz) for dx in (-0.006, 0.0, 0.006) for dz in (-0.006, 0.0, 0.006)
                    if x + dx >= 0) - 0.004
        else:
            y = skin_y(x, z) + 0.004
        return Vector((x, y, z))
    ths = [math.radians(360.0 * i / DISC_SIDES) for i in range(DISC_SIDES)]
    hits = [outline_hit(ex, ez, t) for t in ths]
    def ringpts(fr, front):
        pts = []
        for t, (R, seam) in zip(ths, hits):
            r = fr(R)
            x = ex + math.cos(t) * r
            z = ez + math.sin(t) * r
            if seam and r >= R - 1e-6 or x < 0.0005:
                x = 0.0
            pts.append(pt(x, z, front))
        return pts
    bm = bmesh.new()
    f_hole = ring(bm, ringpts(lambda R: DISC_HOLE, True))
    f_mid = ring(bm, ringpts(lambda R: DISC_HOLE + 0.55 * (R - DISC_RIM - DISC_HOLE), True))
    f_rim = ring(bm, ringpts(lambda R: R - DISC_RIM, True))
    f_out = ring(bm, ringpts(lambda R: R, True))
    b_out = ring(bm, ringpts(lambda R: R, False))
    b_hole = ring(bm, ringpts(lambda R: DISC_HOLE, False))
    for a, b in ((f_hole, f_mid), (f_mid, f_rim), (f_rim, f_out), (b_out, b_hole), (b_hole, f_hole)):
        bridge(bm, a, b, closed=True)
    n = DISC_SIDES
    for i in range(n):   # outer wall, open along the seam (the mirror closes it)
        j = (i + 1) % n
        if f_out[i].co.x == 0.0 and f_out[j].co.x == 0.0:
            continue
        bm.faces.new([f_out[i], f_out[j], b_out[j], b_out[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = object_from_bm('disc', bm)
    def rule(c, nn, i):
        dx, dz = abs(c.x) - ex, c.z - ez
        R, seam = outline_hit(ex, ez, math.atan2(dz, dx))
        return 'dark' if (not seam and math.hypot(dx, dz) > R - DISC_RIM * 0.6) else 'cream'
    paint(ob, {'cream': pal['cream'], 'dark': pal['dark']}, rule)
    return ob



def hook(bm, base, ang, L, hw, hh, sy):
    """A talon: a base quad rooted in the toe, a smaller mid quad arching up, the tip bent down to the ground."""
    a = math.radians(ang)
    d = Vector((math.sin(a), sy * math.cos(a), 0.0))
    s = Vector((math.cos(a), -sy * math.sin(a), 0.0))
    z = Vector((0.0, 0.0, 1.0))
    B = Vector(base)
    M = B + d * (0.6 * L) + z * (0.05 * L)
    T = B + d * L
    T.z = 0.002
    q0 = ring(bm, [B + s * u * hw + z * w * hh for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    q1 = ring(bm, [M + s * u * hw * 0.6 + z * w * hh * 0.6 for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bridge(bm, q0, q1, closed=True)
    bm.faces.new(list(reversed(q0)))
    tip = bm.verts.new(T)
    for i in range(4):
        bm.faces.new([q1[i], q1[(i + 1) % 4], tip])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


TOE_ANG, TOE_L, TOE_Y = (-30.0, 30.0), 0.075, -0.075


def toe(bm, root, ang, L):
    """A side toe: three 4-vert sections (root 10x12 mm inside the plate, knuckle, 10x6 mm tip), capped; returns
    the tip centre (the talon root)."""
    a = math.radians(ang)
    d = Vector((math.sin(a), -math.cos(a), 0.0)); s_ = Vector((math.cos(a), math.sin(a), 0.0)); z = Vector((0, 0, 1))
    secs = [(0.0, 0.005, 0.006, 0.008), (0.55, 0.0045, 0.005, 0.009), (1.0, 0.005, 0.003, 0.004)]
    rings = [ring(bm, [root + d * (f * L) + z * zc + s_ * (u * hw) + z * (w * hh)
                       for u, w in ((-1, -1), (1, -1), (1, 1), (-1, 1))]) for f, hw, hh, zc in secs]
    for A, B in zip(rings, rings[1:]):
        bridge(bm, A, B, closed=True)
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return root + d * (L - 0.004) + z * 0.004


# ------------------------------------------------------------------ folded wing plate
BACK = [(0.078, 0.218), (0.145, 0.157), (0.204, 0.132), (0.237, 0.131), (0.37, 0.09), (0.41, 0.065), (0.45, 0.04)]
WROWS = [0.405, 0.35, 0.29, 0.23, 0.17, 0.12]
WCOLS = 4


def interp(tab, z):
    if z <= tab[0][0]:
        return tab[0][1]
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z <= z1:
            return a + (b - a) * (z - z0) / (z1 - z0)
    return tab[-1][1]


def wing_piece(tree, pal):
    """A feather plate lying on the flank: a grid in the side view between the wing's front edge (the WING loop,
    6 mm ahead of it) and the back outline, raycast onto the skin from +X; front 6 mm proud, back 3 mm sunk;
    the bottom row is the primaries, scalloped and running back over the tail root."""
    def yf(z):
        return -0.114 + (0.414 - z) / 2.0 - 0.006
    def yb(z):
        return interp(BACK, z) - 0.022
    grid = []
    for z in WROWS:
        row = []
        for j in range(WCOLS + 1):
            y = yf(z) + (yb(z) - yf(z)) * j / WCOLS
            row.append((y, z))
        grid.append(row)
    # tips: the primaries run back and down past the tail root, every other point longer (feather ends)
    tips = []
    for j in range(WCOLS + 1):
        t = j / WCOLS
        tips.append((0.075 + 0.135 * t + (0.010 if j % 2 else 0.0), 0.085 - 0.012 * t - (0.016 if j % 2 else 0.0)))
    grid.append(tips)
    F, Bk = [], []
    lastx = None
    for i, row in enumerate(grid):
        fr, br = [], []
        for j, (y, z) in enumerate(row):
            loc, nrm, _, _ = tree.ray_cast(Vector((0.5, y, z)), Vector((-1, 0, 0)))
            if loc is not None and loc.x > 0.02:
                x = loc.x
            else:
                x = (lastx[j] if lastx else 0.08) - 0.008
            # the front clears the skin's highest point across the cell around it (the skin bulges between samples)
            xm = x
            for dy in (-0.02, 0.0, 0.02):
                for dz in (-0.025, 0.0, 0.025):
                    h = tree.ray_cast(Vector((0.5, y + dy, z + dz)), Vector((-1, 0, 0)))[0]
                    if h is not None and abs(h.x - x) < 0.03:
                        xm = max(xm, h.x)
            fr.append((xm + 0.005, y, z))
            br.append((x - 0.003, y, z))
        lastx = [b[0] + 0.003 for b in br]
        F.append(fr); Bk.append(br)
    # the tip row has no skin under it: give it thickness from the row above
    F[-1] = [(max(f[0], b[0] + 0.006), f[1], f[2]) for f, b in zip(F[-1], Bk[-1])]
    bm = bmesh.new()
    Fv = [[bm.verts.new(p) for p in r] for r in F]
    Bv = [[bm.verts.new(p) for p in r] for r in Bk]
    R, C = len(F), WCOLS + 1
    for i in range(R - 1):
        for j in range(C - 1):
            bm.faces.new([Fv[i][j], Fv[i + 1][j], Fv[i + 1][j + 1], Fv[i][j + 1]])
            bm.faces.new([Bv[i][j], Bv[i][j + 1], Bv[i + 1][j + 1], Bv[i + 1][j]])
    rim = [(i, 0) for i in range(R)] + [(R - 1, j) for j in range(1, C)] + \
          [(i, C - 1) for i in range(R - 2, -1, -1)] + [(0, j) for j in range(C - 2, 0, -1)]
    for a, b in zip(rim, rim[1:] + rim[:1]):
        bm.faces.new([Fv[a[0]][a[1]], Fv[b[0]][b[1]], Bv[b[0]][b[1]], Bv[a[0]][a[1]]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.calc_center_median().x < 0.02:
            pass
    ob = object_from_bm('wing', bm)
    zc = (WROWS[2] + WROWS[3]) / 2
    paint(ob, {'dark': pal['dark'], 'primary': pal['primary']}, lambda c, n, i: 'dark' if c.z > zc else 'primary')
    return ob


# brow: a wedge seated in the skull (team M1): inner end at the beak root on the disc rim, outer end up into the
# tuft base, kept inside the head outline; 4-vert section (sunk base pair, proud front pair) = 3 faces per side
BROW_PATH = [(0.012 + 0.080 * f, 0.528 + 0.057 * f) for f in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
BROW_H = (0.024, 0.016)        # section height inner -> outer (A direction)
BROW_PROUD = (0.010, 0.006)    # front face over the skin (clears the disc)
BROW_SINK = 0.009              # base under the skin


def brow_piece(tree, pal):
    S, N = [], []
    for x, z in BROW_PATH:
        hit, nrm, _, _ = tree.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))
        S.append(hit); N.append(nrm.normalized())
    bm = bmesh.new()
    secs = []
    for i in range(len(S)):
        f = i / (len(S) - 1)
        h = BROW_H[0] + (BROW_H[1] - BROW_H[0]) * f
        pr = BROW_PROUD[0] + (BROW_PROUD[1] - BROW_PROUD[0]) * f
        T = (S[min(i + 1, len(S) - 1)] - S[max(i - 1, 0)]).normalized()
        A = N[i].cross(T).normalized()
        if A.z < 0:
            A = -A
        p = S[i]
        sec = [p - A * h / 2 - N[i] * BROW_SINK, p - A * h * 0.25 + N[i] * pr,
               p + A * h * 0.30 + N[i] * pr, p + A * h / 2 - N[i] * BROW_SINK]
        for q in sec:
            q.x = max(q.x, 0.004)
        secs.append(ring(bm, sec))
    for a, b in zip(secs, secs[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, secs[0]); cap(bm, list(reversed(secs[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = object_from_bm('brow', bm)
    paint(ob, {'dark': pal['dark']}, lambda c, n, i: 'dark')
    return ob



# tail fan (team M4): a 9 mm plate fanned 60 deg in the top view (the +X half: 0..30 deg, open on the seam), pitched
# down 20 deg, root sunk in the rump; scalloped tip = 5 feathers (centre on the seam, 2 per side)
FAN_ROOT = Vector((0.0, 0.118, 0.150))
FAN_L, FAN_PITCH, FAN_T = 0.165, 20.0, 0.009          # second pass M4: .145 -> .165, spread 60 -> 80 deg,
FAN_WING = 0.85
FAN_DIH = 0.20                                          # outer feathers drop .35 x |x| (a roof, reads from the side)


def fan_piece(pal):
    pc = math.radians(FAN_PITCH)
    nrm = Vector((0.0, math.sin(pc), math.cos(pc)))          # plate normal (up, tilted back)
    def pt(a, r, side):
        a = math.radians(a)
        d = Vector((math.sin(a), math.cos(a) * math.cos(pc), -math.cos(a) * math.sin(pc)))
        p = FAN_ROOT + d * r + nrm * (side * FAN_T / 2)
        if abs(p.x) < 1e-6:
            p.x = 0.0
        return p
    angs = [0.0, 10.0, 20.0, 30.0, 40.0]
    tipr = [FAN_L, FAN_L * 0.86, FAN_L * 0.98, FAN_L * 0.84, FAN_L * 0.92]
    bm = bmesh.new()
    FR = (0.0, 0.4, 0.75, 1.0)            # rows root -> tip; the root is a 40 mm line, not a point (no needles)
    def at(j, f, side):
        r0 = FAN_ROOT + Vector((0.010 * j, 0.0, 0.0)) + nrm * (side * FAN_T / 2)
        p = r0 * (1 - f) + pt(angs[j], tipr[j], side) * f
        if j == 0:
            p.x = 0.0
        p.z -= FAN_DIH * abs(p.x)
        return p
    rows = {side: [[bm.verts.new(at(j, f, side)) for j in range(len(angs))] for f in FR] for side in (1, -1)}
    n = len(angs)
    for side in (1, -1):
        for A, Bq in zip(rows[side], rows[side][1:]):
            for j in range(n - 1):
                q = [A[j], Bq[j], Bq[j + 1], A[j + 1]]
                bm.faces.new(q if side > 0 else list(reversed(q)))
    T, U = rows[1], rows[-1]
    for j in range(n - 1):                               # tip wall and root wall
        bm.faces.new([T[-1][j], U[-1][j], U[-1][j + 1], T[-1][j + 1]])
        bm.faces.new([T[0][j], T[0][j + 1], U[0][j + 1], U[0][j]])
    for i in range(len(FR) - 1):                         # outer wall at 30 deg (the seam side stays open)
        bm.faces.new([T[i][n - 1], U[i][n - 1], U[i + 1][n - 1], T[i + 1][n - 1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = object_from_bm('tailfan', bm)
    paint(ob, {'dark': pal['dark']}, lambda c, n, i: 'dark')
    return ob



def stage3(k, body):
    global EYE_C
    pal = sheet_palette(k, body)
    paint(body, pal, body_rule(body))
    me = body.data
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    trees = skin_trees(me)
    ds = [t.ray_cast(EYE_C0 + EYE_N * 0.1, -EYE_N) for t in trees]
    d = max(0.1 - h[3] for h in ds if h[0] is not None)
    EYE_C = EYE_C0 + EYE_N * (d + 0.003)                      # eye rim 6 mm proud of the skin, 2 mm over the disc
    say(f'OWL eye centre {tuple(round(c, 4) for c in EYE_C)}')
    out = []
    bm = bmesh.new(); dome(bm, EYE_C, EYE_N, [(0.027, -0.008), (0.027, 0.0015), (0.0153, 0.0051)], 0.006)  # team M2: r -15%, flatter
    out.append(object_from_bm('eye', bm)); paint(out[-1], {'orange': pal['orange']}, lambda c, n, i: 'orange')
    bm = bmesh.new(); dome(bm, EYE_C, EYE_N, [(0.0123, 0.0048), (0.0123, 0.0059)], 0.0069)
    out.append(object_from_bm('pupil', bm)); paint(out[-1], {'black': pal['black']}, lambda c, n, i: 'black')
    bm = bmesh.new(); lens(bm, EYE_C, EYE_N, (0.0164, 0.0016), [(0.0092, 0.0035)], 0.0041, [(0.0098, 0.0041)], 0.0046)
    out.append(object_from_bm('lid', bm)); paint(out[-1], {'brown': pal['brown']}, lambda c, n, i: 'brown')
    # beak: a short hooked wedge on the seam, root sunk in the face, tip hooked down
    # team M2: root raised between the eyes (+20 mm), seated only 1 mm into the skin so it crosses the disc's
    # front face once (a root sunk 12 mm crossed the disc's front and back: a hit)
    sk = tree.ray_cast(Vector((0.0001, -0.5, 0.49)), Vector((0, 1, 0)))[0]
    y0 = sk.y - 0.011
    BZ = BEAK_UP
    say(f'OWL beak root skin y {sk.y:.4f}')
    bm = bmesh.new()
    r0 = ring(bm, [(0, y0 + 0.012, 0.506 + BZ), (0.020, y0 + 0.012, 0.470 + BZ), (0, y0 + 0.012, 0.436 + BZ)])
    r1 = ring(bm, [(0, y0 - 0.027, 0.500 + BZ), (0.014, y0 - 0.027, 0.472 + BZ), (0, y0 - 0.027, 0.448 + BZ)])
    r2 = ring(bm, [(0, y0 - 0.045, 0.486 + BZ), (0.008, y0 - 0.045, 0.466 + BZ), (0, y0 - 0.045, 0.452 + BZ)])
    tip = ring(bm, [(0, y0 - 0.057, 0.430 + BZ)])[0]
    bridge(bm, r0, r1); bridge(bm, r1, r2)
    bm.faces.new([r2[0], r2[1], tip]); bm.faces.new([r2[1], r2[2], tip]); cap(bm, r0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    out.append(object_from_bm('beak', bm)); paint(out[-1], {'beak': pal['beak']}, lambda c, n, i: 'beak')
    # facial disc
    disc = disc_piece(me, pal)
    out.append(brow_piece(tree, pal))
    # second pass M3: the carved plate is the middle + rear toe; two side toes (tan pieces, root inside the plate)
    # splay 30 deg out from the ankle; talons sit at the three toe tips and the rear toe
    bm = bmesh.new(); tbm = bmesh.new()
    p = tree.ray_cast(Vector((FOOT_X, -0.5, 0.010)), Vector((0, 1, 0)))[0]
    hook(bm, (p.x, p.y + 0.008, 0.010), 0, 0.034, 0.0055, 0.0055, -1)
    for ang in TOE_ANG:
        tip = toe(tbm, Vector((FOOT_X, TOE_Y, 0.0)), ang, TOE_L)
        hook(bm, (tip.x, tip.y, 0.008), ang, 0.030, 0.0045, 0.0045, -1)
    p = tree.ray_cast(Vector((FOOT_X, 0.5, 0.012)), Vector((0, -1, 0)))[0]
    hook(bm, (p.x, p.y - 0.010, 0.010), 0, 0.030, 0.006, 0.006, 1)
    out.append(object_from_bm('talons', bm)); paint(out[-1], {'black': pal['black']}, lambda c, n, i: 'black')
    out.append(object_from_bm('toes', tbm)); paint(out[-1], {'tan': pal['tan']}, lambda c, n, i: 'tan')
    out.append(disc)
    out.append(wing_piece(tree, pal))
    out.append(fan_piece(pal))
    return out


# ------------------------------------------------------------------ rig (k3's approach, joints on the carve)
def add_eye_bones(rig):
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        eb = rig.data.edit_bones
        for sx, nm in ((1, 'eye.L'), (-1, 'eye.R')):
            b = eb.new(nm)
            b.head = Vector((EYE_C.x * sx, EYE_C.y, EYE_C.z))
            b.tail = b.head + Vector((EYE_N.x * sx, EYE_N.y, EYE_N.z)) * 0.03
            b.parent = eb['head']
        bpy.ops.object.mode_set(mode='OBJECT')


def blink(rig, act, keys):
    ad = rig.animation_data
    ad.action = act
    for f, sc in keys.items():
        for nm in ('eye.L', 'eye.R'):
            rig.pose.bones[nm].scale = (sc, sc, sc)
            rig.pose.bones[nm].keyframe_insert('scale', frame=f)
    ad.action = None
    rest(rig)


def stage4(k, body, pieces):
    hx, hy = J['hipL'][0], J['hipL'][1]
    rig = armature([
        ('root', J['root'][:2] + (0.05,), (0.0, 0.0, 0.20), None),
        ('spine', (0.0, 0.0, 0.20), J['chest'], 'root', True),
        ('head', (0.0, -0.05, 0.41), J['crown'], 'spine'),
        ('tail', J['tail0'], J['tail1'], 'root'),
        ('thigh.L', (hx, hy, 0.11), (hx, hy, 0.035), 'root'),
        ('foot.L', (hx, hy, 0.035), J['toeL'], 'thigh.L', True),
        ('wing.L', J['shoulderL'], J['wingtipL'], 'spine'),
    ], roll='auto')
    skin(body, rig)
    add_eye_bones(rig)
    P = dict(zip(['eye', 'pupil', 'lid', 'beak', 'brow', 'talons', 'toes', 'disc', 'wing', 'tailfan'], pieces))
    for nm in ('eye', 'pupil', 'beak', 'brow', 'talons', 'toes', 'disc', 'wing'):
        bind(P[nm], rig, body=body)
    # second pass M4: body= weights stretched the fan (teal at the tail root: limb weights on its outer
    # verts) and a rigid tail bone drifted it; the fused wing's weights reach the
    # rump (wing .1-.47 on the fan's outer verts), so the two halves are pulled apart; the wing share is damped
    fan = P['tailfan']; bind(fan, rig, body=body)
    for v in fan.data.vertices:                # the wing share scaled by FAN_WING, the rest renormalised
        ws = {fan.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0}
        ws = {n: w * (FAN_WING if n.startswith('wing') else 1.0) for n, w in ws.items()}
        tot = sum(ws.values())
        for g in fan.vertex_groups:
            g.remove([v.index])
            if g.name in ws:
                g.add([v.index], ws[g.name] / tot, 'REPLACE')
    bind(P['lid'], rig, body=body)
    lid = P['lid']; hg = lid.vertex_groups.get('head')
    eg = {1: lid.vertex_groups.new(name='eye.L'), -1: lid.vertex_groups.new(name='eye.R')}
    for v in lid.data.vertices:
        w = next((g.weight for g in v.groups if g.group == hg.index), 0.0)
        if w > 0:
            hg.remove([v.index]); eg[1 if (lid.matrix_world @ v.co).x > 0 else -1].add([v.index], w, 'REPLACE')
    H = lambda a: {'head': (0, a, 0)}
    act_idle = clip(rig, 'idle', {1: H(0), 10: H(HT), 22: H(HT), 24: H(HT), 26: H(HT),
                                  32: H(-HT2), 40: H(-HT2), 48: H(0)})
    blink(rig, act_idle, {1: 1.0, 22: 1.0, 24: 1.8, 26: 1.0, 48: 1.0})
    W = lambda a: {'wing.L': (0, 0, a), 'wing.R': (0, 0, -a)}
    clip(rig, 'move', {1: {}, 6: {**W(WFLAP), 'thigh.L': (-15, 0, 0), 'thigh.R': (-15, 0, 0)},
                       12: {**W(3), 'thigh.L': (-20, 0, 0), 'thigh.R': (-20, 0, 0), 'tail': (-10, 0, 0)},
                       18: {**W(WFLAP)}, 24: {}},
         loc={1: {}, 6: {'root': (0, 0.03, 0)}, 12: {'root': (0, 0.06, 0)}, 18: {'root': (0, 0.02, 0)}, 24: {}})
    WR = lambda up, a: {'wing.L': (-up, 0, a), 'wing.R': (-up, 0, -a)}
    clip(rig, 'attack', {1: {}, 8: {**WR(WUP / 2, WSPREAD * 0.7), 'spine': (-10, 0, 0), 'head': (-8, 0, 0)},
                         16: {**WR(WUP, WSPREAD), 'spine': (12, 0, 0), 'head': (-10, 0, 0),
                              'thigh.L': (45, 0, 0), 'thigh.R': (45, 0, 0), 'foot.L': (-25, 0, 0), 'foot.R': (-25, 0, 0)},
                         24: {**W(WFLAP / 2), 'spine': (4, 0, 0)}, 32: {}})
    return rig


WFLAP, WUP, WSPREAD = 12, 14, 18
HT, HT2 = 25, 18


run(META, stage1, stage2, stage3, stage4)
