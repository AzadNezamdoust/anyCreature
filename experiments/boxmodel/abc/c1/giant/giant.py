import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_base, colour_from_sheet

# prototype: stage 1 carved from reference/ (a visual hull), stage 3 coloured from the same sheet;
# the skeleton and clips are abc/k3/giant's
META = dict(creature='giant', model='opus', engine_glb='')

J = dict(   # re-fitted to the carved base (the arm hangs forward of the torso, legs centred under the hips)
    pelvis=(0.0, 0.30, 1.05), spine=(0.0, 0.25, 1.85), chest=(0.0, 0.15, 2.70), neck=(0.0, -0.20, 3.15),
    head=(0.0, -0.62, 2.95), snout=(0.0, -1.15, 2.90),
    hipL=(0.55, 0.20, 1.05), kneeL=(0.58, 0.05, 0.55), ankleL=(0.62, 0.15, 0.20), toeL=(0.68, -0.55, 0.06),
    neckbase=(0.0, -0.20, 2.95), clavL=(0.30, 0.05, 2.95), clavtipL=(1.05, -0.05, 2.85), shoulderL=(1.20, -0.15, 2.75),
    elbowL=(1.45, -0.35, 1.95), wristL=(1.52, -0.45, 1.15), fistL=(1.52, -0.45, 0.35),
)


# ---------------------------------------------------------------- stage 1: carve + a designed head
# the hull keeps the masses; the face is the hull's blind spot (a cube), so a box-modelled head is
# unioned onto it. Head rings stacked in z; each half ring runs back centre -> side -> cheek ->
# socket -> inner -> front centre, (x, y) per point.
HEAD = [   # (z, half ring of (x, y[, dz])): 8 rings, the face planes are in the ring shapes
    (2.48, [(0, -0.55), (0.18, -0.58), (0.25, -0.80), (0.24, -0.95), (0.17, -1.02), (0.08, -1.05), (0, -1.05)]),   # chin
    (2.60, [(0, -0.50), (0.28, -0.55), (0.36, -0.80), (0.34, -0.98), (0.25, -1.09), (0.11, -1.12), (0, -1.12)]),   # wide jaw, underbite
    (2.70, [(0, -0.50), (0.28, -0.55), (0.35, -0.80), (0.31, -0.96), (0.22, -1.02), (0.10, -1.05), (0, -1.05)]),   # mouth crease
    (2.82, [(0, -0.50), (0.28, -0.55), (0.35, -0.80), (0.31, -0.95), (0.20, -1.02), (0.12, -1.13), (0, -1.16)]),   # nose wings
    (2.98, [(0, -0.50), (0.29, -0.55), (0.37, -0.78), (0.35, -0.90), (0.19, -0.92), (0.07, -1.06, -0.03), (0, -1.08, -0.04)]),  # sockets, bridge
    (3.10, [(0, -0.50), (0.30, -0.55), (0.40, -0.78), (0.38, -0.97, -0.02), (0.23, -1.10, 0.02), (0.09, -1.10, -0.05), (0, -1.07, -0.07)]),  # angry brow
    (3.22, [(0, -0.50), (0.27, -0.55), (0.33, -0.74), (0.30, -0.90), (0.20, -0.98), (0.08, -0.99), (0, -0.99)]),   # forehead
    (3.32, [(0, -0.50), (0.17, -0.55), (0.21, -0.68), (0.19, -0.80), (0.12, -0.86), (0.05, -0.88), (0, -0.88)]),   # skull top
]


def head_bm():
    bm = bmesh.new()
    rings = []
    for z, half in HEAD:
        P = [(p[0], p[1], z + (p[2] if len(p) > 2 else 0.0)) for p in half]
        pts = P + [(-x, y, zz) for x, y, zz in reversed(P[1:-1])]
        rings.append(ring(bm, pts))
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rings[0]))); cap(bm, rings[-1])
    recalc_normals(bm)
    return bm


GAP = [(0.50, 0.88, 1.12), (0.80, 0.88, 1.14), (1.00, 0.85, 1.16), (1.20, 0.85, 1.26), (1.40, 0.88, 1.24),
       (1.60, 0.86, 1.16), (1.80, 0.85, 1.11), (2.00, 0.81, 1.08), (2.20, 0.82, 1.02)]   # (z, torso edge, arm edge):
# the reference front mask's edges widened ~0.05 each way, so the gap still reads in perspective


def gap_bm():
    bm = bmesh.new()
    for sx in (1, -1):
        poly = [(xi, z) for z, xi, xo in GAP] + [(0.92, 2.36)] + [(xo, z) for z, xi, xo in reversed(GAP)]
        poly = [(sx * x, z) for x, z in poly]
        if sx < 0:
            poly = poly[::-1]
        A = ring(bm, [(x, -1.5, z) for x, z in poly])
        Bv = ring(bm, [(x, 1.5, z) for x, z in poly])
        bridge(bm, A, Bv, closed=True)
        cap(bm, list(reversed(A))); cap(bm, Bv)
    recalc_normals(bm)
    return bm


def moss_f(c):
    """> 0 on the moss mantle: the hump top and shoulders, lower down the back, a wavy organic edge."""
    ax = abs(c[0])
    zb = 3.42 - 0.55 * _smooth01((c[1] + 0.1) / 0.9) - 0.22 * _smooth01((ax - 0.6) / 0.6)
    zb += 0.07 * math.sin(7.0 * math.atan2(c[1], ax + 0.3) + 1.3) + 0.05 * math.sin(9.0 * c[1] + 4.0 * ax)
    if ax < 0.5 and c[1] < -0.3:
        zb += 0.6 * _smooth01((0.5 - ax) / 0.15) * _smooth01((-0.3 - c[1]) / 0.15)   # keep the head bare
    return c[2] - zb


def implicit_cut(bm, f, snap=0.03):
    """Cut the surface along f = 0: vertices within `snap` of it move onto it, crossing edges split at
    the root, faces split between their two cut points. Seam vertices stay on x = 0."""
    def grad(co):
        h = 1e-3
        return Vector(((f(co + Vector((h, 0, 0))) - f(co - Vector((h, 0, 0)))) / (2 * h),
                       (f(co + Vector((0, h, 0))) - f(co - Vector((0, h, 0)))) / (2 * h),
                       (f(co + Vector((0, 0, h))) - f(co - Vector((0, 0, h)))) / (2 * h)))
    on = set()
    for v in bm.verts:
        val = f(v.co)
        g = grad(v.co)
        if abs(v.co.x) < 1e-6:
            g.x = 0.0
        if g.length_squared < 1e-9:
            continue
        if abs(val) / g.length < snap:
            for _ in range(3):
                val = f(v.co); g = grad(v.co)
                if abs(v.co.x) < 1e-6:
                    g.x = 0.0
                v.co -= g * (val / g.length_squared)
            on.add(v)
    for e in list(bm.edges):
        a, b = e.verts
        if a in on or b in on:
            continue
        fa, fb = f(a.co), f(b.co)
        if fa * fb < 0:
            t = fa / (fa - fb)
            ne, nv = bmesh.utils.edge_split(e, a, t)
            on.add(nv)
    for fc in list(bm.faces):
        vs = [v for v in fc.verts if v in on]
        if len(vs) != 2:
            continue
        if any(vs[1] in (e.other_vert(vs[0]),) for e in vs[0].link_edges if fc in e.link_faces):
            continue
        bmesh.utils.face_split(fc, vs[0], vs[1])


ARMB = [(0.20, -0.12), (0.55, -0.12), (0.90, -0.08), (1.30, 0.06), (2.32, 0.12)]   # (z, arm back y), side view


def armback_bm(z0, z1, x0):
    bm = bmesh.new()
    if True:
        pts = [(y, z) for z, y in ARMB if z0 < z < z1]
        yb = lambda z: next(b0 + (b1 - b0) * (z - za) / (zb - za) for (za, b0), (zb, b1) in zip(ARMB, ARMB[1:]) if za <= z <= zb)
        poly = [(yb(z0), z0)] + pts + [(yb(z1), z1), (1.7, z1), (1.7, z0)]
        for sx in (1, -1):
            A = ring(bm, [(sx * x0, y, z) for y, z in poly])
            Bv = ring(bm, [(sx * 2.4, y, z) for y, z in poly])
            bridge(bm, A, Bv, closed=True)
            cap(bm, list(reversed(A))); cap(bm, Bv)
    recalc_normals(bm)
    return bm


def _in_head(f):
    return all(abs(v.co.x) < 0.42 and v.co.y < -0.47 and v.co.z > 2.42 for v in f.verts)


def _min_angle(f):
    return min(math.degrees(l.calc_angle()) for l in f.loops)


DEBUG_SLIVER = False


def repair_slivers(bm, border_f, min_deg=7.0, passes=12):
    """The booleans and the moss cut leave needle/cap triangles (techqa: min angle < 6 deg). Each is fixed
    one at a time (cap: flip its long edge; needle: collapse its short edge, trying both ends and the
    middle), and an attempt that pushes the surface through itself is undone. Seam vertices stay on
    x = 0 and moss-border vertices on the border, so the paint border stays an edge path."""
    def on_border(v):
        return abs(border_f(v.co)) < 1e-4
    def seam(v):
        return abs(v.co.x) < 1e-6
    def bad_faces(b):
        return [f for f in b.faces if len(f.verts) == 3 and _min_angle(f) < min_deg
                and max(e.calc_length() for e in f.edges) > 0.04]
    def attempts(g):
        es = list(g.edges)
        ls = [e.calc_length() for e in es]
        angs = [math.degrees(l.calc_angle()) for l in g.loops]
        emax, emin = es[ls.index(max(ls))], es[ls.index(min(ls))]
        out = []
        if max(angs) > 110.0 and len(emax.link_faces) == 2 and not all(seam(v) for v in emax.verts)                 and not all(on_border(v) for v in emax.verts):
            out.append(('flip', emax))
        a, b = emin.verts
        for keep, other in ((a, b), (b, a)):
            if (seam(other) and not seam(keep)) or (on_border(other) and not on_border(keep)):
                continue
            out.append(('merge', (keep, other)))
        if not (seam(a) or seam(b) or on_border(a) or on_border(b)):
            out.append(('mid', (a, b)))
        for v in g.verts:
            if not on_border(v):
                out.append(('relax', v))
        return out
    say('repair_slivers: start hits', _nhits(bm), 'bad', len(bad_faces(bm)))
    for _ in range(passes):
        cands = [tuple(sorted(v.index for v in f.verts)) for f in bad_faces(bm)]
        if not cands:
            break
        fixed = 0
        for key in cands:
            bm.verts.ensure_lookup_table()
            if max(key) >= len(bm.verts):
                continue
            vs = [bm.verts[i] for i in key]
            f = next((f for f in vs[0].link_faces if set(f.verts) == set(vs)), None)
            if f is None or _min_angle(f) >= min_deg:
                continue
            n_try = len(attempts(f))
            for t in range(n_try):
                trial = bm.copy()
                trial.verts.ensure_lookup_table()
                tv = [trial.verts[i] for i in key]
                g = next(g for g in tv[0].link_faces if set(g.verts) == set(tv))
                kind, arg = attempts(g)[t]
                if kind == 'flip':
                    bmesh.ops.rotate_edges(trial, edges=[arg], use_ccw=False)
                elif kind == 'relax':                    # tangential Laplacian step of one vertex
                    v = arg
                    nbr = [e.other_vert(v) for e in v.link_edges]
                    avg = sum((w.co for w in nbr), Vector()) / len(nbr)
                    d = avg - v.co
                    n = v.normal.copy()
                    d -= n * d.dot(n)
                    if seam(v):
                        d.x = 0.0
                    v.co += d * 0.6
                else:
                    p, q = arg
                    nb_p = {e.other_vert(p) for e in p.link_edges}
                    nb_q = {e.other_vert(q) for e in q.link_edges}
                    shared = [e for e in p.link_edges if e.other_vert(p) is q]
                    if not shared or len(nb_p & nb_q) != len(shared[0].link_faces):
                        DEBUG_SLIVER and say('   link fail', kind); trial.free(); continue
                    co = p.co.copy() if kind == 'merge' else (p.co + q.co) / 2
                    bmesh.ops.pointmerge(trial, verts=[p, q], merge_co=co)
                bmesh.ops.dissolve_degenerate(trial, edges=list(trial.edges), dist=1e-6)
                if _ == passes - 1 or (_ > 0 and not fixed and False):
                    pass
                if DEBUG_SLIVER:
                    say('   try', kind, 'manifold', all(len(e.link_faces) in (1, 2) for e in trial.edges), 'hits', _nhits(trial),
                        'bad', len(bad_faces(trial)), 'vs', len(bad_faces(bm)))
                if all(len(e.link_faces) in (1, 2) for e in trial.edges) and _nhits(trial) == 0                         and len(bad_faces(trial)) < len(bad_faces(bm)):
                    bm.free(); bm = trial; fixed += 1
                    break
                trial.free()
        if not fixed:
            break
    left = sum(1 for f in bm.faces if len(f.verts) == 3 and _min_angle(f) < 6.0 and max(e.calc_length() for e in f.edges) > 0.04)
    say('repair_slivers: left', left, 'of', len(bm.faces))
    return bm


def _smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _to_object(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); me.update()
    return link(bpy.data.objects.new(name, me))


def _kill(ob):
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)


def stage1(k):
    import carve as C
    carved = carve_base(k, target_tris=(560, 960), plan_roundness=2.5)
    full = evaluated_bm(carved)
    _kill(carved)
    # shrink the hull's head cube into the designed head (smooth falloff behind it, so the neck is untouched)
    piv = Vector((0.0, -0.72, 2.86))
    for v in full.verts:
        c = v.co
        if c.z < 2.30 or abs(c.x) > 0.55:
            continue
        w = _smooth01((-0.52 - c.y) / 0.22) * _smooth01((c.z - 2.30) / 0.15) * _smooth01((0.55 - abs(c.x)) / 0.15)
        if w > 0:
            v.co = c.lerp(piv + (c - piv) * 0.45, w)
    # the plan view sees the fists far forward, so the hull's shoulders run forward to the face (a slab
    # in the side view): soft-clamp the shoulder front back to the side view's trapezius line
    for v in full.verts:
        c = v.co
        w = _smooth01((c.z - 2.20) / 0.30) * _smooth01((abs(c.x) - 0.40) / 0.20)
        if w <= 0:
            continue
        ylim, s = -0.55, 0.08
        if c.y < ylim + s:
            c.y += w * (ylim + s * math.exp((c.y - ylim - s) / s) - c.y)
    # the hull's back-outer hump corners stand up as fins (plan corner x side corner): soft-cap the
    # upper body under a dome so the hump rolls off into the deltoids
    for v in full.verts:
        c = v.co
        if c.z < 2.7:
            continue
        dome = 3.98 - 0.45 * c.x * c.x - 0.9 * max(0.0, c.y - 0.2) ** 2 - 0.6 * max(0.0, -0.2 - c.y) ** 2
        s = 0.05
        if c.z > dome - s:
            c.z = dome - s * math.exp(-(c.z - dome + s) / s)
    ob = _to_object('_full', full); full.free()
    hd = _to_object('_head', head_bm())
    md = ob.modifiers.new('u', 'BOOLEAN')
    md.operation = 'UNION'; md.solver = 'EXACT'; md.object = hd
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=md.name)
    _kill(hd)
    # the hull fills the narrow front-view gap between the hanging arm and the torso: cut it open
    # (a slab per side, from the reference front mask: torso edge -> arm inner edge, armpit down)
    ct = _to_object('_gap', gap_bm())
    md = ob.modifiers.new('d', 'BOOLEAN')
    md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = ct
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=md.name)
    _kill(ct)
    # the side view sees the torso behind the hanging arm, so the hull's arm is a 1.3 m deep slab:
    # cut its back off along the reference side view's arm back edge (the arm hangs forward)
    for z0, z1, x0 in ((0.44, 2.32, 0.95), (0.20, 0.50, 1.16)):     # forearm/upper arm, then the fist bottom
        ct = _to_object('_armback', armback_bm(z0, z1, x0))
        md = ob.modifiers.new('d2', 'BOOLEAN')
        md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = ct
        with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
            bpy.ops.object.modifier_apply(modifier=md.name)
        _kill(ct)
    bm = edit(ob); _kill(ob)
    for v in bm.verts:
        if abs(v.co.x) < 0.004:
            v.co.x = 0.0
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-6,
                           plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
    for v in bm.verts:
        if v.co.x < 1e-4:
            v.co.x = 0.0
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(abs(v.co.x) < 1e-6 for v in f.verts)], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    C._largest_shell(bm)
    # boolean cut faces are flat fans of needles: merge coplanar triangles and re-triangulate them (beauty)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(2.5), use_dissolve_boundaries=False,
                             verts=list(bm.verts), edges=list(bm.edges))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4 or (len(f.verts) == 4 and not _in_head(f))],
                          quad_method='BEAUTY', ngon_method='BEAUTY')   # the head keeps its designed quads
    trial = bm.copy()                          # the kit's sliver repair, kept only if it folds nothing through
    C._fix_slivers(trial, 4.0, 8.0)
    if _nhits(trial) == 0:
        bm.free(); bm = trial
    else:
        say('sliver repair folded the surface: skipped'); trial.free()
    implicit_cut(bm, moss_f, snap=0.035)        # the moss mantle border is an edge path (clean paint border)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4 or
                                     (len(f.verts) == 4 and any(abs(moss_f(v.co)) < 1e-4 for v in f.verts))],
                          quad_method='BEAUTY', ngon_method='BEAUTY')
    bm = repair_slivers(bm, moss_f)
    say('stage1 head union: half verts', len(bm.verts), 'faces', len(bm.faces), 'defects', C._defects(bm))
    out = object_from_bm('body', bm)
    _hits(out)
    return out


def _nhits(half):
    from mathutils.bvhtree import BVHTree
    bm = half.copy()
    bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
    bm.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(bm)
    n = sum(1 for i, j in t.overlap(t) if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)))
    bm.free()
    return n


def _hits(ob):
    from mathutils.bvhtree import BVHTree
    bm = evaluated_bm(ob); bm.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(bm)
    for i, j in t.overlap(t):
        if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
            say('hit', tuple(round(c, 3) for c in bm.faces[i].calc_center_median()), tuple(round(c, 3) for c in bm.faces[j].calc_center_median()))
    bm.free()


def stage2(k, body):
    bm = edit(body)
    # r1 the wrist break the hull smoothed away: pinch the forearm above the fist so the fist reads huge
    for v in bm.verts:
        c = v.co
        if c.x < 1.0 or not 0.85 < c.z < 1.40:
            continue
        w = max(0.0, 1.0 - abs(c.z - 1.10) / 0.28)
        w = w * w * (3 - 2 * w)
        s = 1.0 - 0.16 * w
        c.x = 1.52 + (c.x - 1.52) * s
        c.y = -0.44 + (c.y + 0.44) * s
    # r2 the pot belly and the pec shelf the hull rounded off: belly front forward, under-pec back
    for v in bm.verts:
        c = v.co
        if c.x > 0.80 or c.y > -0.25:
            continue
        wb = max(0.0, 1.0 - abs(c.z - 1.72) / 0.32)
        wp = max(0.0, 1.0 - abs(c.z - 2.22) / 0.10)
        c.y += -0.07 * wb * wb * (3 - 2 * wb) + 0.05 * wp
    commit(body, bm); bm.free()


BRIEF_PAL = {'hide': '#66727f', 'dark': '#343b46', 'stone': '#8b867c', 'moss': '#6f8f3a',
             'leather': '#a58c67', 'cloth': '#6e5236', 'tusk': '#d6c9a6', 'eye': '#f4b427'}
PAL = dict(BRIEF_PAL)


def _hex_rgb(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def sheet_palette(k, body):
    """colour_from_sheet's clusters; each brief role snaps to its nearest sheet colour when one is close
    (the sheet's hide, moss, stone, leather); eye, tusk and dark keep the brief value."""
    tmp = body.copy(); tmp.data = body.data.copy(); link(tmp)
    sheet = colour_from_sheet(k, [tmp])                    # on a copy: the body keeps no sheet state
    _kill(tmp)
    say('sheet palette', sheet)
    pal = dict(BRIEF_PAL)
    for role in ('hide', 'moss', 'cloth'):
        r = _hex_rgb(BRIEF_PAL[role])
        best = min(sheet.values(), key=lambda h: sum((p - q) ** 2 for p, q in zip(_hex_rgb(h), r)))
        d = sum((p - q) ** 2 for p, q in zip(_hex_rgb(best), r)) ** 0.5
        if d < 45:
            pal[role] = best
    say('palette used', pal)
    return pal


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


def horn(bm, rings, tip):
    """A tapered closed spike: rings of points (base first) and one tip vertex."""
    R = [ring(bm, [tuple(p) for p in r]) for r in rings]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b, closed=True)
    t = bm.verts.new(tuple(tip))
    n = len(R[-1])
    for i in range(n):
        bm.faces.new([R[-1][i], R[-1][(i + 1) % n], t])
    cap(bm, list(reversed(R[0])))


def section(c, d, rx, ry, n=4, spin=45):
    d = Vector(d).normalized()
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    e1 = ref.cross(d).normalized(); e2 = d.cross(e1).normalized()
    c = Vector(c)
    return [c + e1 * (math.cos(math.radians(spin + i * 360 / n)) * rx) + e2 * (math.sin(math.radians(spin + i * 360 / n)) * ry)
            for i in range(n)]


def piece(name, build, pal_rule, mirror=True):
    bm = bmesh.new()
    build(bm)
    recalc_normals(bm)
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, PAL, pal_rule)
    return ob


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    global PAL
    PAL = sheet_palette(k, body)

    def body_rule(c, n, i):
        if moss_f(c) > 0:
            return 'moss'                                   # the mantle: its border is the stage-1 cut path
        if abs(c.x) < 0.30 and c.y < -0.95 and 2.60 < c.z < 2.70:
            return 'dark'                                   # the mouth crease between the jaw and lip rings
        if c.z < 0.06:
            return 'dark'                                   # soles
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
    # eyes: amber lens set in the socket under the brow (proud of it), a dark slit pupil proud of the lens
    eye_c = hit((0.19, -1.6, 2.985), (0, 1, 0))
    eye_n = Vector((0.18, -1, 0.05)).normalized()

    def eyes(bm):
        prism(bm, eye_c - eye_n * 0.03, eye_n, 0.085, 0.050, 0.06, n=6, top=0.75, start=0)
    out.append(piece('eyes', eyes, lambda c, n, i: 'eye'))

    def pupils(bm):
        prism(bm, eye_c + eye_n * 0.022, eye_n, 0.018, 0.040, 0.02, n=4, top=0.6, start=0)
    out.append(piece('pupils', pupils, lambda c, n, i: 'dark'))

    # tusks: from the underbite jaw, rising past the lip, curving out
    def tusks(bm):
        base = hit((0.22, -1.6, 2.58), (0, 1, 0)) + Vector((0, 0.05, 0))
        horn(bm, [section(base, (0.2, -0.45, 1), 0.065, 0.06),
                  section(base + Vector((0.035, -0.10, 0.14)), (0.3, -0.25, 1), 0.05, 0.045)],
             base + Vector((0.085, -0.13, 0.30)))
    out.append(piece('tusks', tusks, lambda c, n, i: 'tusk'))

    # ears: short pointed troll ears out of the skull sides, swept back and up
    def ears(bm):
        root = Vector((0.33, -0.74, 3.05))
        horn(bm, [section(root, (1, 0.35, 0.25), 0.10, 0.055, n=4, spin=0),
                  section(root + Vector((0.13, 0.05, 0.05)), (1, 0.5, 0.35), 0.075, 0.035, n=4, spin=0)],
             root + Vector((0.27, 0.14, 0.15)))
    out.append(piece('ears', ears, lambda c, n, i: 'hide'))

    # nose: a broad bulb over the nose base with dark nostrils underneath
    def nose(bm):
        c = hit((0.0, -1.6, 2.86), (0, 1, 0))
        prism(bm, c + Vector((0, 0.05, 0)), (0, -1, -0.15), 0.115, 0.085, 0.10, n=6, top=0.7, start=0)
    out.append(piece('nose', nose, lambda c, n, i: 'dark' if n.z < -0.6 else 'hide', mirror=False))

    # moss mantle clumps over the painted mantle, rocks bedded into them (as the sheet shows)
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
            outer.append(on_skin(loc + d, -0.008))
            midt.append(on_skin(loc + d * 0.75, t * 0.6))
            midb.append(on_skin(loc + d * 0.75, -t * 0.4))
        O = ring(bm, [tuple(q) for q in outer]); MT = ring(bm, [tuple(q) for q in midt]); MB = ring(bm, [tuple(q) for q in midb])
        ct = bm.verts.new(tuple(loc + N * t * 0.65)); cb = bm.verts.new(tuple(loc - N * t * 0.4))
        bridge(bm, O, MT, closed=True); bridge(bm, MB, O, closed=True)
        for i in range(nn):
            j = (i + 1) % nn
            bm.faces.new([MT[i], MT[j], ct]); bm.faces.new([MB[j], MB[i], cb])

    def moss(bm):
        drape(bm, (0.40, 0.05, 3.90), 0.36, 0.55, [1, 0.8, 1.1, 0.95, 0.75, 1.05, 0.9, 1.15, 0.85], spin=10)
        drape(bm, (1.00, 0.10, 3.30), 0.28, 0.42, [0.9, 1.1, 0.8, 1.05, 1.0, 0.7, 1.1, 0.95], spin=35)
        drape(bm, (0.62, -0.42, 3.55), 0.30, 0.24, [1.1, 0.8, 1.0, 0.75, 1.15, 0.9, 1.0], spin=5)
        drape(bm, (0.55, 0.80, 3.25), 0.32, 0.30, [1.0, 0.85, 1.1, 0.8, 1.05, 0.9, 0.95], spin=20)
    out.append(piece('moss', moss, lambda c, n, i: 'moss'))

    def rocks(bm):
        for p, r, h in (((0.80, -0.40, 3.42), 0.20, 0.18), ((0.22, 0.40, 3.93), 0.24, 0.20),
                        ((1.18, 0.30, 3.05), 0.20, 0.18), ((0.75, 0.45, 3.62), 0.17, 0.15)):
            loc, n = seat(p)
            prism(bm, loc - n * h * 0.5, n, r, r * 0.78, h, n=6, top=0.66, start=15, jit=[1, 0.8, 1.1, 0.9, 1.0, 0.85])
    out.append(piece('rocks', rocks, lambda c, n, i: 'stone'))

    # belt: a band round the waist, sunk into the belly, sagging at the front; a stone buckle
    BELT_Z = lambda th: 1.66 - 0.08 * math.cos(th)

    def belt(bm):
        rows = [[], [], [], []]
        N = 32
        for i in range(N):
            th = i * 2 * math.pi / N
            d = Vector((math.sin(th), -math.cos(th), 0))
            z = BELT_Z(th)
            loc = hit((0, 0.20, z), d)
            for r, (dz, dd) in zip(rows, ((-0.06, 0.03), (-0.06, 0.10), (0.06, 0.10), (0.06, 0.03))):
                r.append(loc + d * dd + Vector((0, 0, dz)))
        R = [ring(bm, [tuple(p) for p in r]) for r in rows]
        for a, b in zip(R, R[1:] + R[:1]):
            bridge(bm, a, b, closed=True)
    out.append(piece('belt', belt, lambda c, n, i: 'leather', mirror=False))

    def toggles(bm):                                         # stone toggles on the belt at the hips (the sheet's)
        for th in (math.radians(66),):
            d = Vector((math.sin(th), -math.cos(th), 0))
            c = hit((0, 0.20, BELT_Z(th)), d)
            prism(bm, c + d * 0.065, d, 0.085, 0.07, 0.07, n=6, top=0.75, start=0)
    out.append(piece('toggles', toggles, lambda c, n, i: 'stone'))
    # loincloth flaps front and back: thick plates hanging flat in front of the body, a jagged hem
    U = [-1, -0.66, -0.33, 0, 0.33, 0.66, 1]

    def cloth(rows, side, hem, t=0.05):
        def build(bm):
            F, Bk = [], []
            for r, (w, z) in enumerate(rows):
                last = r == len(rows) - 1
                pts = []
                for kk, u in enumerate(U):
                    zz = z + (hem[kk] if last else 0.0)
                    ys = [h.y for h in (hit((u * w, -2.5 * side, zz - dz), (0, side, 0)) for dz in ((0.0, 0.08, 0.16) if r == 0 else (0.0,))) if h]
                    hy = max(y * -side for y in ys) * -side if ys else -0.7 * side   # the most outward point below the belt
                    pts.append([u * w, hy, zz])
                if r == 0:                                   # the top row sits inside the belt band only
                    for p in pts:
                        p[1] -= side * 0.065
                else:                                        # lower rows hang flat in front of the most forward point
                    lim = min(h.y * side for zz in [rows[-1][1] + 0.1 * q for q in range(9)] for u in U
                              for h in [hit((u * rows[r][0], -2.5 * side, zz), (0, side, 0))] if h) * side   # hang clear of everything below
                    for p, u in zip(pts, U):
                        p[1] = lim - side * 0.10 + side * 0.03 * u * u     # side: the ray direction (inward)
                F.append(ring(bm, [tuple(p) for p in pts]))
                Bk.append(ring(bm, [(px, py + side * t, pz) for px, py, pz in pts]))
            for r in range(len(rows) - 1):
                bridge(bm, F[r], F[r + 1]); bridge(bm, Bk[r + 1], Bk[r])
                bm.faces.new([F[r][0], F[r + 1][0], Bk[r + 1][0], Bk[r][0]])
                bm.faces.new([F[r][-1], Bk[r][-1], Bk[r + 1][-1], F[r + 1][-1]])
            bridge(bm, F[0], Bk[0]); bridge(bm, Bk[-1], F[-1])
        return build
    out.append(piece('loin_front', cloth([(0.40, 1.58), (0.36, 1.30), (0.31, 1.02), (0.26, 0.74)], 1,
                                         [0.0, -0.10, 0.02, -0.18, 0.0, -0.08, 0.03]),
                     lambda c, n, i: 'cloth', mirror=False))
    out.append(piece('loin_back', cloth([(0.50, 1.74), (0.47, 1.48), (0.43, 1.24), (0.38, 1.04)], -1,
                                        [0.02, -0.12, 0.0, -0.09, 0.03, -0.15, 0.0]),
                     lambda c, n, i: 'cloth', mirror=False))

    # fingers: four curled two-segment boxes on the fist front under the knuckle row, stone nails
    nail_c = []

    def fingers(bm):
        up = Vector((0, 0, 1))
        for x, hw in ((1.27, 0.068), (1.44, 0.080), (1.61, 0.078), (1.77, 0.064)):
            def front(z):
                loc, nrm, _, _ = tree.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
                return loc, Vector((nrm.x, nrm.y, 0)).normalized()
            p0, n0 = front(0.70)
            p1, n1 = front(0.54)
            p2, n2 = front(0.42)
            nh = (n0 + n1 + n2).normalized()
            if nh.y > -0.3:
                nh = Vector((0, -1, 0))
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
            bmesh.ops.inset_individual(bm, faces=[tipf], thickness=0.022, depth=0.012)
            nail_c.append(tipf.calc_center_median().copy())
    out.append(piece('fingers', fingers, lambda c, n, i: 'stone' if min((c - q).length for q in nail_c) < 0.02 else 'hide'))

    def thumbs(bm):
        loc = hit((1.52, -0.60, 0.72), (-1, 0, 0))
        ax = Vector((-0.45, -1.0, -0.35)).normalized()
        prism(bm, loc + Vector((0.08, 0.05, 0.02)), ax, 0.095, 0.10, 0.32, n=5, top=0.72, start=90)
    out.append(piece('thumbs', thumbs, lambda c, n, i: 'stone' if n.dot(Vector((-0.45, -1.0, -0.35)).normalized()) > 0.8 else 'hide'))

    # toes: three blunt toes with big stone nails on each foot front
    def toes(bm):
        for x, rx in ((0.48, 0.12), (0.68, 0.10), (0.87, 0.08)):
            h = hit((x, -2.0, 0.08), (0, 1, 0))
            prism(bm, (x, h.y + 0.06, 0.08), (0, -1, 0), rx, 0.075 if rx > 0.1 else 0.065, 0.15, n=4, top=0.85, start=45)
    out.append(piece('toes', toes, lambda c, n, i: 'stone' if n.y < -0.7 or (n.z > 0.7 and c.y < -0.7) else 'hide'))
    return out


AMP = 0.8      # k3's clip amplitudes, a little softer: the carved shoulder is one mass with the hump


def softclip(rig, name, keys, loc=None):
    return clip(rig, name, {f: {b: tuple(AMP * a for a in r) for b, r in d.items()} for f, d in keys.items()}, loc)


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
        if p.name.split('piece_')[-1] == 'toggles':
            bind(p, rig, bone='hips')        # the waist gear rides the pelvis (nearest-skin weights reached the arms)
        else:
            bind(p, rig, body=body)

    def both(d):          # mirror a left-side key onto the right (bone-local X pitch is shared; Y/Z flip)
        out = dict(d)
        for b, (x, y, z) in d.items():
            if b.endswith('.L'):
                out[b[:-2] + '.R'] = (x, -y, -z)
        return out
    softclip(rig, 'idle', {1: {}, 24: both({'spine': (2, 0, 0), 'chest': (3, 0, 0), 'neck': (-3, 0, 0), 'head': (-2, 0, 0),
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
    softclip(rig, 'move', {1: stepL, 9: passL, 17: swap(stepL), 25: swap(passL), 33: stepL})
    wind = both({'spine': (-3, 0, 0), 'chest': (-30, 0, 0), 'neck': (14, 0, 0), 'clav.L': (0, 0, 8),
                 'upperarm.L': (85, 0, -27), 'forearm.L': (75, 0, 0)})   # AD r2 item 4: wider, higher
    slam = both({'spine': (4, 0, 0), 'chest': (26, 0, 0), 'neck': (-10, 0, 0), 'clav.L': (0, 0, -4),
                 'upperarm.L': (42, 0, -12), 'forearm.L': (10, 0, 0), 'thigh.L': (8, 0, 0), 'shin.L': (-12, 0, 0)})
    hold = both({'spine': (3, 0, 0), 'chest': (17, 0, 0), 'upperarm.L': (28, 0, 0), 'forearm.L': (8, 0, 0)})
    softclip(rig, 'attack', {1: {}, 14: wind, 22: slam, 30: hold, 40: {}})
    return rig



run(META, stage1, stage2, stage3, stage4)
