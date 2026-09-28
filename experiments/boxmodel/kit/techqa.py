"""techqa — the technical errors an art director sees up close, computed on the
exported triangulation, painted onto a heatmap, and counted for the gates.

Why it exists: batch 2 passed every structural gate and the owner still found
"a bunch of technical errors" in two close crops — an antler beam through an
ear, paper-thin cape and ruff plates showing as shards, and pinched folds at
the bear's shoulder. None of that was measured. Now it is.

Classes (heatmap colour):
  valley  red      a non-planar face whose triangulation folds INTO the form (a pinch)
  fold    orange   a non-planar face folded more than FOLD_WARN degrees
  sliver  yellow   a needle triangle (min angle < SLIVER_DEG, not a tiny one)
  hit     magenta  a part that passes through something a second time: a shell of a piece
                   entering the body (or another shell) in more than one place, e.g. an
                   antler rooted in the skull that also cuts through the ear
  open    cyan     a piece with open edges (a single-sided plate: a shard edge-on)
  float   blue     a piece shell that touches nothing (a visible gap)
  zfight  green    a piece face lying ON another surface, facing the same way (flicker);
                   faces pressed face-to-face are a hidden contact and do not count
  flip    purple   a triangle that folds over or collapses in a posed frame
  drift   brown    (posed) a piece that sits on the body at rest but comes off it in a
                   pose — rigid to one bone while the skin under it follows others; gated
"""
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def _zero_pose(rig):
    """Every pose bone to identity, without changing its rotation mode. Bones a clip does not
    key otherwise keep whatever the previous clip left them at, and the fold-over and drift
    counts depended on the order the clips were sampled in (8 or 16 flips on identical input)."""
    for b in rig.pose.bones:
        b.location = (0, 0, 0); b.scale = (1, 1, 1)
        b.rotation_quaternion = (1, 0, 0, 0); b.rotation_euler = (0, 0, 0)
        b.rotation_axis_angle = (0, 0, 1, 0)


FOLD_WARN = 25.0
VALLEY_WARN = 10.0
SLIVER_DEG = 6.0
COL = {'ok': (0.80, 0.80, 0.78), 'valley': (0.92, 0.10, 0.10), 'fold': (1.0, 0.55, 0.10),
       'sliver': (1.0, 0.90, 0.15), 'hit': (0.92, 0.10, 0.85), 'open': (0.10, 0.80, 0.95),
       'float': (0.15, 0.30, 1.0), 'zfight': (0.10, 0.85, 0.30), 'flip': (0.55, 0.15, 0.85),
       'drift': (0.60, 0.38, 0.15), 'clip': (1.0, 0.55, 0.70)}
PRIORITY = ['flip', 'hit', 'clip', 'float', 'drift', 'zfight', 'open', 'valley', 'sliver', 'fold']
MAX_SAMPLES = 40          # posed frames per clip


def _key_frames(act):
    """Every keyed frame of an action (legacy fcurves or Blender 5 layered channelbags)."""
    curves = list(getattr(act, 'fcurves', None) or [])
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for cb in getattr(strip, 'channelbags', []):
                curves += list(cb.fcurves)
    return {int(round(k.co.x)) for fc in curves for k in fc.keyframe_points}


def sample_frames(act):
    """The frames a clip is checked at: every keyed frame (a blink keyed 40-44 is a pose the old
    4-point sampler at 20/40/60/80 % never saw) plus the in-betweens at 20/40/60/80 %."""
    a, b = act.frame_range
    fs = {int(a + (b - a) * s) for s in (0.2, 0.4, 0.6, 0.8)}
    fs |= {f for f in _key_frames(act) if a <= f <= b}
    fs = sorted(fs)
    if len(fs) > MAX_SAMPLES:
        fs = [fs[round(i * (len(fs) - 1) / (MAX_SAMPLES - 1))] for i in range(MAX_SAMPLES)]
    return fs


def _near_ring(T):
    """For each triangle, the triangles within two vertex rings of it: their crossings are a
    crease folding on itself (the fold-over check's job), not one body part clipping another."""
    by_v = {}
    for ti, (_, t) in enumerate(T):
        for v in t:
            by_v.setdefault(v, set()).add(ti)
    r1 = [set().union(*(by_v[v] for v in t)) for _, t in T]
    return [set().union(*(r1[x] for x in r1[ti])) for ti in range(len(T))]


def _clipping(bV, bT, near, pieces):
    """Triangles that cross another part: body against body (not near each other) and each piece
    against the body. Returns {'body': set(body tris), piece_name: set(piece tris)}."""
    bt = BVHTree.FromPolygons(bV, [t for _, t in bT], all_triangles=True)
    out = {'body': set()}
    for i, j in bt.overlap(bt):
        if i != j and j not in near[i]:
            out['body'].add(i); out['body'].add(j)
    for name, (V, T) in pieces.items():
        pt = BVHTree.FromPolygons(V, [t for _, t in T], all_triangles=True)
        out[name] = {i for i, _ in pt.overlap(bt)}
    return out


# ---------------------------------------------------------------- the fix a modeller makes by hand
def triangulate_convex(ob, keep=None):
    """Triangulate the object's own mesh and TURN EDGES so every non-planar
    quad/ngon folds OUT with the form (a ridge), not into it (a pinch) — what a
    low-poly artist does by hand before export. keep(centre) -> True leaves a
    face's valley alone (a socket or a mouth corner that should dent in).
    Returns (edges turned, pinched folds that could not be turned)."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    big = [f for f in bm.faces if len(f.verts) > 3]
    if not big:
        bm.free()
        return 0, 0
    old = set(bm.edges)
    keep_faces = {f.index for f in big if keep and keep(ob.matrix_world @ f.calc_center_median())}
    bmesh.ops.triangulate(bm, faces=big, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.normal_update()
    turned = stuck = 0
    for e in [e for e in bm.edges if e not in old]:
        if not e.is_valid or len(e.link_faces) != 2:
            continue
        f1, f2 = e.link_faces
        a = e.verts[0]
        r = next(v for v in f2.verts if v not in e.verts)
        if (r.co - a.co).dot(f1.normal) <= 1e-7 or f1.normal.angle(f2.normal, 0) < math.radians(2):
            continue                                  # already a ridge, or flat
        if keep_faces:
            c = (f1.calc_center_median() + f2.calc_center_median()) / 2
            if keep and keep(ob.matrix_world @ c):
                continue
        ne = bmesh.utils.edge_rotate(e, True)
        if ne is None:
            stuck += 1
            continue
        bm.normal_update()
        ok = all(f.calc_area() > 1e-10 for f in ne.link_faces) and len(ne.link_faces) == 2
        if ok:
            g1, g2 = ne.link_faces
            rr = next(v for v in g2.verts if v not in ne.verts)
            ok = (rr.co - ne.verts[0].co).dot(g1.normal) <= 1e-7    # now a ridge
        if not ok:
            bmesh.utils.edge_rotate(ne, False)
            bm.normal_update()
            stuck += 1
        else:
            turned += 1
    bm.to_mesh(me)
    me.update()
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    return turned, stuck


# ---------------------------------------------------------------- measuring
def _evaluated(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    me.calc_loop_triangles()
    M = ob.matrix_world
    V = [M @ v.co for v in me.vertices]
    T = [(t.polygon_index, tuple(t.vertices)) for t in me.loop_triangles]
    P = [tuple(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    return V, T, P


def _tri_normal(V, t):
    a, b, c = (V[i] for i in t)
    n = (b - a).cross(c - a)
    return n.normalized() if n.length > 1e-12 else Vector((0, 0, 0)), n.length / 2


def _orig_poly(ob, P, p):
    n = len(ob.data.polygons)
    return p % n if n and len(P) % n == 0 else min(p, n - 1)


def _shells(P):
    """Connected components of polygons (by shared vertices): list of sets of poly indices."""
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for p in P:
        for v in p[1:]:
            ra, rb = find(p[0]), find(v)
            if ra != rb:
                parent[ra] = rb
    groups = {}
    for i, p in enumerate(P):
        groups.setdefault(find(p[0]), set()).add(i)
    return list(groups.values())


def _bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-18:
        return (1.0, 0.0, 0.0)
    w = (d11 * d20 - d01 * d21) / den
    x = (d00 * d21 - d01 * d20) / den
    return (1.0 - w - x, w, x)


def _clusters(polys, P):
    """How many separate patches a set of polygons forms (sharing a vertex joins them)."""
    polys = list(polys)
    if not polys:
        return 0
    sub = [P[i] for i in polys]
    return len(_shells(sub))


def measure(body, pieces, size, rig=None, acts=None):
    """Counts per class and per-object face flags {ob.name: {orig_poly: class}}."""
    L = max(size)
    objs = [body] + list(pieces)
    data = {o.name: _evaluated(o) for o in objs}
    flags = {o.name: {} for o in objs}
    counts = {o.name: {k: 0 for k in COL if k != 'ok'} for o in objs}

    def flag(o, p, cls):
        op = _orig_poly(o, data[o.name][2], p)
        cur = flags[o.name].get(op)
        if cur is None or PRIORITY.index(cls) < PRIORITY.index(cur):
            flags[o.name][op] = cls

    # folds and slivers, on the export triangulation
    for o in objs:
        V, T, P = data[o.name]
        by_poly = {}
        for p, t in T:
            by_poly.setdefault(p, []).append(t)
        for p, ts in by_poly.items():
            if len(ts) > 1:
                worst, valley = 0.0, False
                for i in range(len(ts)):
                    for j in range(i + 1, len(ts)):
                        sh = set(ts[i]) & set(ts[j])
                        if len(sh) != 2:
                            continue
                        n1, _ = _tri_normal(V, ts[i])
                        n2, _ = _tri_normal(V, ts[j])
                        if n1.length == 0 or n2.length == 0:
                            continue
                        ang = math.degrees(n1.angle(n2, 0))
                        r = next(v for v in ts[j] if v not in sh)
                        a = next(iter(sh))
                        is_valley = (V[r] - V[a]).dot(n1) > 1e-6 * L
                        if is_valley and ang > VALLEY_WARN:
                            valley = True
                        worst = max(worst, ang)
                if valley:
                    counts[o.name]['valley'] += 1; flag(o, p, 'valley')
                elif worst > FOLD_WARN:
                    counts[o.name]['fold'] += 1; flag(o, p, 'fold')
            for t in ts:
                a, b, c = (V[i] for i in t)
                ea, eb, ec = (b - c).length, (c - a).length, (a - b).length
                if max(ea, eb, ec) < 0.01 * L:
                    continue
                angs = []
                for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
                    u, w = y - x, z - x
                    if u.length < 1e-12 or w.length < 1e-12:
                        angs.append(0.0)
                    else:
                        angs.append(math.degrees(u.angle(w, 0)))
                if min(angs) < SLIVER_DEG:
                    counts[o.name]['sliver'] += 1; flag(o, p, 'sliver')
                    break

    # pieces: open edges, roots, floating, z-fight
    trees = {}
    for o in objs:
        V, T, P = data[o.name]
        trees[o.name] = BVHTree.FromPolygons(V, [t for _, t in T], all_triangles=True)
    bV, bT, bP = data[body.name]
    seated = []                       # piece shells that sit on/in the body at rest
    for o in pieces:
        V, T, P = data[o.name]
        edge_faces = {}
        for pi, poly in enumerate(P):
            for k in range(len(poly)):
                e = tuple(sorted((poly[k], poly[(k + 1) % len(poly)])))
                edge_faces.setdefault(e, []).append(pi)
        for e, fs in edge_faces.items():
            if len(fs) != 2:
                for pi in fs:
                    flag(o, pi, 'open')
                counts[o.name]['open'] += 1
        tri_poly = [p for p, _ in T]
        shells = _shells(P)
        # every other surface this piece can touch
        others = [x for x in objs if x is not o]
        for sh in shells:
            sh_tris = [ti for ti, (p, _) in enumerate(T) if p in sh]
            sh_tree = BVHTree.FromPolygons(V, [T[ti][1] for ti in sh_tris], all_triangles=True)
            touched = False
            for x in others:
                xV, xT, xP = data[x.name]
                pairs = sh_tree.overlap(trees[x.name])
                if not pairs:
                    continue
                touched = True
                hit_polys = {xT[j][0] for _, j in pairs}
                own_polys = {T[sh_tris[i]][0] for i, _ in pairs}
                # a mirrored piece enters once per side; a rooted piece crosses the surface
                # along ONE ring on each side of the contact (own faces) and ONE patch (theirs)
                for side in (1, -1):
                    side_polys = {p for p in hit_polys if side * sum(xV[v].x for v in xP[p]) >= 0}
                    own_side = {p for p in own_polys if side * sum(V[v].x for v in P[p]) >= 0}
                    if _clusters(side_polys, xP) > 1 or _clusters(own_side, P) > 1:
                        counts[o.name]['hit'] += 1
                        for i, j in pairs:
                            flag(o, T[sh_tris[i]][0], 'hit'); flag(x, xT[j][0], 'hit')
                        break
            # other shells of the same piece
            for sh2 in shells:
                if sh2 is sh:
                    continue
                tris2 = [ti for ti, (p, _) in enumerate(T) if p in sh2]
                t2 = BVHTree.FromPolygons(V, [T[ti][1] for ti in tris2], all_triangles=True)
                if sh_tree.overlap(t2):
                    touched = True
            body_contact = bool(sh_tree.overlap(trees[body.name])) or min(
                ((trees[body.name].find_nearest(V[v])[3] or 1e9) for v in list({v for p in sh for v in P[p]})[:40]),
                default=1e9) <= 0.004 * L
            if body_contact:
                anchors = []
                for v in list({v for p in sh for v in P[p]})[:12]:
                    loc, _, ti, d = trees[body.name].find_nearest(V[v])
                    if loc is None:
                        continue
                    a, b, c = (bV[i] for i in bT[ti][1])
                    anchors.append((v, ti, _bary(loc, a, b, c), d))
                seated.append((o, sh, anchors))
            if not touched:
                # a shell may rest on a surface without cutting it: distance test
                near = min(((trees[x.name].find_nearest(V[v])[3] or 1e9) for x in others
                            for v in list({v for p in sh for v in P[p]})[:40]), default=1e9)
                if near > 0.004 * L:
                    counts[o.name]['float'] += 1
                    for p in sh:
                        flag(o, p, 'float')
        # z-fight against the body
        for p, t in T:
            n, area = _tri_normal(V, t)
            if area < 1e-10:
                continue
            c = (V[t[0]] + V[t[1]] + V[t[2]]) / 3
            loc, nrm, idx, dist = trees[body.name].find_nearest(c)
            # same-facing coplanar faces flicker; faces pressed face-to-face (a hoof cap on a
            # leg end, opposite normals) are a hidden contact, not a z-fight
            if loc is not None and dist < 0.0015 * L and n.dot(nrm) > 0.985:
                counts[o.name]['zfight'] += 1; flag(o, p, 'zfight')

    # posed: a triangle that folds over against its neighbours, or collapses
    flipped = {}
    if rig is not None and acts:
        rest_n = {}
        for o in objs:
            V, T, P = data[o.name]
            rest_n[o.name] = [_tri_normal(V, t) for _, t in T]
        drifted = set()
        near = _near_ring(bT)
        clip0 = _clipping(bV, bT, near, {o.name: data[o.name][:2] for o in pieces})   # what already crosses at rest
        clipped = {}
        for name, act in acts.items():
            _zero_pose(rig)         # each clip plays alone, as exported: bones it does not key sit at rest
            for f in sample_frames(act):
                rig.animation_data.action = act
                bpy.context.scene.frame_set(f)
                bVp, bTp, _ = _evaluated(body)
                btree = BVHTree.FromPolygons(bVp, [t for _, t in bTp], all_triangles=True)
                cl = _clipping(bVp, bTp, near, {o.name: _evaluated(o)[:2] for o in pieces})
                for on, ts in cl.items():
                    oname = body.name if on == 'body' else on
                    for ti in ts - clip0[on]:
                        clipped.setdefault(oname, set()).add(ti)
                for pi, (o, sh, anchors) in enumerate(seated):
                    if pi in drifted:
                        continue
                    Vp, Tp, Pp = _evaluated(o)
                    # the gap between each sample vertex and the exact skin point it rested on:
                    # a piece that slides over or lifts off its seat opens that gap
                    grow = 0.0
                    for v, ti, (u, w, x), d0 in anchors:
                        a, b, c = (bVp[i] for i in bTp[ti][1])
                        grow = max(grow, (Vp[v] - (a * u + b * w + c * x)).length - d0)
                    if grow > 0.01 * L:
                        drifted.add(pi)
                        counts[o.name]['drift'] = counts[o.name].get('drift', 0) + 1
                        for p_ in sh:
                            flag(o, p_, 'drift')
                for o in objs:
                    V, T, P = _evaluated(o)
                    nbr = {}
                    for ti, (_, t) in enumerate(T):
                        for v in t:
                            nbr.setdefault(v, []).append(ti)
                    pn = [_tri_normal(V, t) for _, t in T]
                    for ti, (p, t) in enumerate(T):
                        n0, a0 = rest_n[o.name][ti]
                        n1, a1 = pn[ti]
                        if a0 < 1e-10:
                            continue
                        ring = {x for v in t for x in nbr[v] if x != ti}
                        avg = sum((pn[x][0] for x in ring), Vector())
                        avg0 = sum((rest_n[o.name][x][0] for x in ring), Vector())
                        folded = avg.length > 1e-9 and n1.dot(avg.normalized()) < -0.2 \
                            and avg0.length > 1e-9 and n0.dot(avg0.normalized()) > 0.3
                        if folded or a1 < 0.2 * a0:
                            flag(o, p, 'flip')
                            flipped.setdefault(o.name, {})[ti] = a0     # each triangle counts once, however many frames
        for o in objs:
            counts[o.name]['flip'] = len(flipped.get(o.name, {}))
            T = data[o.name][1]
            for ti in clipped.get(o.name, ()):
                flag(o, T[ti][0], 'clip')
            counts[o.name]['clip'] = len(clipped.get(o.name, ()))
            counts[o.name]['clip_area'] = sum(_tri_normal(data[o.name][0], T[ti][1])[1] for ti in clipped.get(o.name, ()))
        rig.animation_data.action = None
        for b in rig.pose.bones:
            b.rotation_mode = 'XYZ'
            b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)
            b.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
    tris = {o.name: len(data[o.name][1]) for o in objs}
    # surface areas, so a few huge flipped triangles cannot hide under a triangle count
    for o in objs:
        V, T, P = data[o.name]
        counts[o.name]['area'] = sum(_tri_normal(V, t)[1] for _, t in T)
        counts[o.name]['flip_area'] = sum(flipped.get(o.name, {}).values())
    return counts, flags, tris


def paint_heatmap(objs, flags):
    """A temporary colour attribute per object showing the flags (for the tech render)."""
    for o in objs:
        me = o.data
        at = me.color_attributes.get('_qa') or me.color_attributes.new('_qa', 'BYTE_COLOR', 'CORNER')
        fl = flags.get(o.name, {})
        cols = []
        for p in me.polygons:
            c = COL[fl.get(p.index, 'ok')]
            cols += [c[0], c[1], c[2], 1.0] * p.loop_total
        at.data.foreach_set('color', cols)
        me.color_attributes.active_color = at


def clear_heatmap(objs):
    for o in objs:
        me = o.data
        at = me.color_attributes.get('_qa')
        if at:
            me.color_attributes.remove(at)
        col = me.color_attributes.get('Col')
        if col:
            me.color_attributes.active_color = col


def summary(counts, tris):
    keys = set().union(*[c.keys() for c in counts.values()])
    tot = {k: sum(c.get(k, 0) for c in counts.values()) for k in keys}
    return tot, sum(tris.values())
