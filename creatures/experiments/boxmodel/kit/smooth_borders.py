"""Smooth colour borders on a flat-colour box model (a stage-3 step for every creature).

A box model paints one flat colour per face, so a colour border runs along the quad grid and stair-steps wherever the
painted region does not follow a loop (frog belly / thigh underneath, werewolf bib). This pass, in the spirit of
Houdini Labs "smooth edges" but for material borders, fixes it inside the dense mesh without changing the shape:

  1. despeckle: a quad with 3+ border edges whose neighbours all share one other colour takes that colour;
  2. anti-stair cut: a quad at a 3-to-1 colour corner (two adjacent border edges, the same colour across both) is split
     on the diagonal that cuts the corner and its corner triangle takes the other colour. Cuts never share a border
     edge (that would zig-zag), and they are picked walking each border path, so a stair becomes a straight diagonal;
  3. relax: every border vertex inside a path (two border edges, not a 3-colour junction, not on the mirror seam or an
     open edge, not on a sharp crease, not pinned) slides TANGENTIALLY toward the middle of its path neighbours
     (Taubin lambda/mu, so curves do not shrink), is re-projected onto the ORIGINAL surface (BVH closest point: the
     silhouette and the planes stay), and never ends further than `max_slide` x its shortest edge from where it was.
     A move that flips or squashes a face is undone.

Density never decreases: cuts only add triangles (each one is a quad the exporter would triangulate anyway; the cut
just picks the diagonal), relax only moves vertices. Connectivity changes go through bmkit.topo() so the lock assertion
stays PASS (a diagonal dissolves back into its quad). The runner's "s3 base mesh untouched" gate accepts exactly the
geometry this pass leaves (ob['bmk_borders'] records the hash before and after).

    from smooth_borders import smooth_borders
    paint(body, PAL, body_rule)
    smooth_borders(body, k=k)                                    # every border
    smooth_borders(body, k=k, pairs=[('skin', 'belly')], iters=8, pin=lambda c: c.z > 0.25)

Returns a summary dict (also printed as 'BMK borders ...'); border_stats(ob) measures stair corners for before/after.
"""
import math
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bmkit import say, edit, commit, white, geometry_hash, topo

SEAM_EPS = 1e-4          # |x| below this: a mirror-seam vertex (pinned)
CREASE_DEG = 40.0        # a border vertex on a fold sharper than this stays put (the border follows the form there)


def _names(ob):
    return [m.name if m else '' for m in ob.data.materials]


def _allowed(pairs, names):
    if not pairs:
        return lambda a, b: a != b
    P = {frozenset(p) for p in pairs}
    return lambda a, b: a != b and frozenset((names[a], names[b])) in P


def _border_edges(bm, ok):
    out = set()
    for e in bm.edges:
        if len(e.link_faces) == 2:
            a, b = e.link_faces
            if ok(a.material_index, b.material_index):
                out.add(e)
    return out


def _other(e, f):
    a, b = e.link_faces
    return b if a == f else a


def _chains(border):
    """Border edges -> ordered vertex paths (open paths run junction to junction; loops are closed)."""
    adj = {}
    for e in border:
        for v in e.verts:
            adj.setdefault(v, []).append(e)
    seen, paths = set(), []
    starts = [v for v, es in adj.items() if len(es) != 2] + [v for v, es in adj.items() if len(es) == 2]
    for s in starts:
        for e0 in adj[s]:
            if e0 in seen:
                continue
            path, v, e = [s], s, e0
            while True:
                seen.add(e)
                w = e.other_vert(v)
                path.append(w)
                if w == s or len(adj[w]) != 2:
                    break
                e = adj[w][0] if adj[w][1] == e else adj[w][1]
                if e in seen:
                    break
                v = w
            paths.append(path)
    return paths, adj


def border_stats(ob, pairs=None, turn_deg=50.0):
    """Stair measure: border length, path vertices that turn more than turn_deg (stair corners), 3-to-1 corner quads."""
    bm = edit(ob)
    names = _names(ob)
    ok = _allowed(pairs, names)
    border = _border_edges(bm, ok)
    paths, adj = _chains(border)
    corners = 0
    for p in paths:
        for i in range(1, len(p) - 1):
            a, v, b = p[i - 1].co, p[i].co, p[i + 1].co
            d1, d2 = v - a, b - v
            if d1.length > 1e-9 and d2.length > 1e-9 and math.degrees(d1.angle(d2)) > turn_deg:
                corners += 1
    q31 = len(_candidates(bm, border, ok))
    L = sum(e.calc_length() for e in border)
    bm.free()
    return dict(border_edges=len(border), length=round(L, 4), paths=len(paths), corners=corners, corner_quads=q31,
                corners_per_m=round(corners / max(L, 1e-9), 1))


def _candidates(bm, border, ok):
    """Quads at a 3-to-1 colour corner: (face, corner vert, other material, diagonal (p, q), border edges)."""
    out = []
    for f in bm.faces:
        if len(f.verts) != 4:
            continue
        loops = list(f.loops)
        be = [l.edge in border for l in loops]
        if sum(be) != 2:
            continue
        for i in range(4):
            j = (i + 1) % 4
            if be[i] and be[j]:                       # edges loops[i] (v_i -> v_i+1) and loops[j] (v_i+1 -> v_i+2)
                m1 = _other(loops[i].edge, f).material_index
                m2 = _other(loops[j].edge, f).material_index
                if m1 != m2:
                    break
                corner = loops[j].vert
                p, q = loops[i].vert, loops[(j + 1) % 4].vert
                out.append((f, corner, m1, (p, q), (loops[i].edge, loops[j].edge)))
                break
    return out


def _despeckle(bm, ok):
    n = 0
    for _ in range(3):
        border = _border_edges(bm, ok)
        ch = 0
        for f in bm.faces:
            es = [e for e in f.edges if e in border]
            if len(es) < 3 or len(es) < len(f.edges) - 1:
                continue
            ms = {_other(e, f).material_index for e in es}
            if len(ms) == 1:
                f.material_index = ms.pop()
                ch += 1
        n += ch
        if not ch:
            break
    return n


def _tri_w(a, b, c):
    L = max((a - b).length, (b - c).length, (c - a).length)
    return (b - a).cross(c - a).length / L if L > 1e-12 else 0.0


def _width(f):
    """A face's thinness: the smallest triangle height (2A / longest edge) of its best triangulation."""
    P = [v.co for v in f.verts]
    if len(P) == 3:
        return _tri_w(*P)
    if len(P) == 4:
        a, b, c, d = P
        return max(min(_tri_w(a, b, c), _tri_w(a, c, d)), min(_tri_w(a, b, d), _tri_w(b, c, d)))
    L = max(e.calc_length() for e in f.edges)
    return f.calc_area() / L if L > 1e-12 else 0.0


def smooth_borders(ob, pairs=None, iters=6, cut=True, max_slide=0.5, lam=0.5, mu=-0.53, pin=None, k=None, log=None,
                   crease_deg=CREASE_DEG, keep_width=0.8, cut_keep=0.6, guard=None, tag='borders'):
    """Smooth every colour border of `ob` (or only `pairs` of material names). See the module doc.
    pin(world_co) -> True keeps a vertex where it is (junction roots, a mouth line on purpose).
    keep_width: no face linked to a moved vertex may end thinner than this share of its own width (no slivers/strips).
    guard: [(centre, radius, factor)] scales max_slide by factor within radius (limb roots the junction probe reads).
    k (the stage's K) or log (bmkit Log): connectivity changes are logged so the lock assertion passes."""
    log = log if log is not None else (k.log if k is not None else None)
    h0 = geometry_hash(ob)
    prev = ob.get('bmk_borders')
    if prev is not None and list(prev)[1] == h0:      # a second pass on top of the first: keep the pre-pass hash
        h0 = list(prev)[0]
    before = border_stats(ob, pairs)
    names = _names(ob)
    ok = _allowed(pairs, names)
    bm = edit(ob)
    mw = ob.matrix_world
    n_speck = _despeckle(bm, ok)

    # ---- 2. anti-stair cuts, picked walking each border path (no two cuts share a border edge)
    n_cut = 0
    if cut:
        for _round in range(2):
            border = _border_edges(bm, ok)
            cand = {}
            for c in _candidates(bm, border, ok):
                cand.setdefault(c[1], []).append(c)
            paths, _ = _chains(border)
            used, taken, plan = set(), set(), []
            for p in paths:
                for v in p:
                    for c in cand.get(v, ()):
                        f, corner, m2, (a, b), es = c
                        if f in taken or any(e in used for e in es):
                            continue
                        opp = next(x for x in f.verts if x not in (a, b, corner))
                        if min(_tri_w(a.co, corner.co, b.co), _tri_w(a.co, b.co, opp.co)) < cut_keep * _width(f):
                            continue          # the forced diagonal would leave a sliver the exporter's would not
                        taken.add(f)
                        used.update(es)
                        plan.append(c)
            if not plan:
                break

            def do_cuts():
                n = 0
                for f, corner, m2, (a, b), es in plan:
                    if not f.is_valid:
                        continue
                    res = bmesh.utils.face_split(f, a, b)
                    nf = res[0]
                    if nf is None:
                        continue
                    tri = nf if corner in nf.verts else f
                    tri.material_index = m2
                    n += 1
                return n
            if log is not None:
                with topo(bm, log, 'border_cut', f'{tag}: split {len(plan)} 3-to-1 colour-corner quads on the '
                                                 f'diagonal that follows the border (anti-stair)'):
                    n_cut += do_cuts()
            else:
                n_cut += do_cuts()
        bm.normal_update()

    # ---- 3. tangential Taubin relax along the border paths, re-projected onto the original surface
    bm.verts.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    border = _border_edges(bm, ok)
    paths, adj = _chains(border)
    orig = {v: v.co.copy() for v in bm.verts}
    fn0 = {f: f.normal.copy() for f in bm.faces}
    fa0 = {f: f.calc_area() for f in bm.faces}
    fw0 = {f: _width(f) for f in bm.faces}
    nbr = {}
    for p in paths:
        for i, v in enumerate(p):
            if len(adj[v]) == 2:
                nbr.setdefault(v, set())
                if i > 0:
                    nbr[v].add(p[i - 1])
                if i < len(p) - 1:
                    nbr[v].add(p[i + 1])

    def pinned(v):
        if abs(v.co.x) < SEAM_EPS or any(not e.is_manifold for e in v.link_edges) or v.is_boundary:
            return True
        for e in adj.get(v, ()):
            if len(e.link_faces) == 2:
                a, b = e.link_faces
                if math.degrees(a.normal.angle(b.normal, 0.0)) > crease_deg:
                    return True
        return bool(pin and pin(mw @ v.co))

    mov = [v for v, ns in nbr.items() if len(ns) == 2 and not pinned(v)]
    lim = {}
    for v in mov:
        s = max_slide
        for c, rad, fac in guard or ():
            if (mw @ v.co - Vector(c)).length < rad:
                s = min(s, max_slide * fac)
        lim[v] = s * min(e.calc_length() for e in v.link_edges)
    for it in range(iters):
        for w in (lam, mu):
            new = {}
            for v in mov:
                a, b = nbr[v]
                d = (a.co + b.co) * 0.5 - v.co
                n = v.normal
                d = (d - n * d.dot(n)) * w
                q = tree.find_nearest(v.co + d)[0]
                if q is None:
                    continue
                off = q - orig[v]
                if off.length > lim[v]:
                    q = tree.find_nearest(orig[v] + off * (lim[v] / off.length))[0] or orig[v]
                if abs(orig[v].x) > SEAM_EPS and abs(q.x) < 10 * SEAM_EPS:
                    continue
                new[v] = q
            for v, q in new.items():
                v.co = q
    # undo (halve, then drop) moves that flip, squash or thin a face: a border vertex must never leave a sliver or a
    # narrow seam strip behind (the junction probe's strip rule: thin triangles on a crease at a limb root)
    n_undo = 0
    for it in range(10):
        bad = set()
        for v in mov:
            if (v.co - orig[v]).length < 1e-9:
                continue
            for f in v.link_faces:
                f.normal_update()
                if (f.calc_area() < 0.25 * fa0[f] or (fn0[f].length > 0 and f.normal.dot(fn0[f]) < math.cos(math.radians(45)))
                        or _width(f) < keep_width * fw0[f]):
                    bad.add(v)
        if not bad:
            break
        for v in bad:
            v.co = orig[v] if it >= 5 else orig[v].lerp(v.co, 0.5)
            n_undo += 1
    moved = [(v.co - orig[v]).length for v in mov]
    bm.normal_update()
    commit(ob, bm)
    bm.free()
    white(ob)
    after = border_stats(ob, pairs)
    ob['bmk_borders'] = [h0, geometry_hash(ob)]
    out = dict(tag=tag, despeckled=n_speck, cuts=n_cut, relaxed=len(mov), undone=n_undo,
               max_move=round(max(moved, default=0.0), 5), mean_move=round(sum(moved) / max(1, len(moved)), 5),
               before=before, after=after)
    say(f"borders {tag}: {n_speck} despeckled, {n_cut} anti-stair cuts, {len(mov)} border verts relaxed "
        f"(max {out['max_move'] * 1000:.1f} mm, {n_undo} undone); stair corners {before['corners']} -> {after['corners']}, "
        f"3-to-1 quads {before['corner_quads']} -> {after['corner_quads']}")
    if k is not None:
        k.meta.setdefault('_borders', []).append(out)
    return out
