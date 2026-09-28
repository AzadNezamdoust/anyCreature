"""bmkit — the hands, the stage lock and the camera for the staged box-model experiment.

A creature program imports this module, defines stage1 … stage4 and calls run():

    py -3.11 experiments/boxmodel/kit/run.py <creature>.py --stage N [--round R] [--lock]

(run.py launches headless Blender on the program, then composes the round sheet,
the harness orbit and, at stage 4, glbcheck). BRIEF.md in the parent folder is
the protocol; this file is its enforcement.

CONVENTIONS. Blender units are metres, Z is up, the creature faces -Y and its
LEFT flank is +X (the glTF export turns that into the harness convention: +Y
up, facing +Z, left flank +X). The base mesh is modelled as its left half
(x >= 0) under a live Mirror modifier (X, clipping, merge); seam vertices sit
exactly on x = 0.

WHAT IS ENFORCED.
  stage 1  one connected, closed, self-intersection-free mirrored mesh, 400-1,500
           triangles. --lock writes stage1_lock.json: vertex/face/triangle
           counts, the sha256 of the sorted canonical edge list, a hash of the
           vertex positions and the camera frame. Once the lock exists, every
           later run rebuilds stage 1 and must reproduce it EXACTLY — stage 1 is
           frozen; later shape changes live in stage 2 where they are visible.
  stage 2  vertex moves are free. Connectivity changes only inside
           `with k.topo(bm, kind, reason):` blocks, which mark the new vertices,
           classify the new edges and log the operation with its reason to
           stage2_log.json. The lock assertion then dissolves every logged
           insertion and requires the remainder to hash to the lock.
  stage 3  may not touch the base mesh at all (geometry hash before == after);
           details are separate objects; 4-8 region colours.
  stage 4  armature from the build skeleton, automatic weights, idle/move/attack.
"""
import bpy, bmesh, json, hashlib, math, os, sys, time, contextlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import numpy as np

SEAM = 1e-5                     # |x| below this is on the mirror seam
ORBIT = [f'az{d:03d}' for d in range(0, 360, 45)] + ['top', 'bottom']
ROUND_VIEWS = ['az000', 'az045', 'az090', 'az135', 'az180', 'top', 'hero']
WIRE_VIEWS = ['hero', 'az090', 'az000']
FOV = math.radians(30.0)        # outline.py's pinhole
FILL = 1.15                     # round renders sit this much closer than the outline camera
CLAY_MATCAP = os.environ.get('BMK_MATCAP') or None   # e.g. 'clay_studio.exr'; None = studio light
DIST = 2.4                      # distance = longest frame dimension x DIST (outline.py's rule)


def say(*a):
    print('BMK', *a, flush=True)


def V(x, y=None, z=None):
    return Vector(x) if y is None else Vector((x, y, z))


# =============================================================================
# 1. THE HANDS — box-modelling verbs on a bmesh
# =============================================================================
def ring(bm, pts):
    """New vertices at pts (a list of xyz). Returns the list of BMVerts."""
    return [bm.verts.new(Vector(p)) for p in pts]


def bridge(bm, a, b, closed=False):
    """Quads between two vertex rows of equal length (a[i] -> b[i])."""
    assert len(a) == len(b), 'bridge: rows differ in length'
    n = len(a) if closed else len(a) - 1
    return [bm.faces.new([a[i], a[(i + 1) % len(a)], b[(i + 1) % len(b)], b[i]]) for i in range(n)]


def cap(bm, verts):
    """One face on a row of vertices (an n-gon; export triangulates it)."""
    return bm.faces.new(verts)


def extrude(bm, faces, offset=None):
    """Extrude a face region (E). The original faces are replaced by the new
    region: nothing is left inside. Returns {'faces', 'verts', 'sides'}.
    offset: optional Vector to move the new region by (the G after the E)."""
    faces = list(faces)
    r = bmesh.ops.extrude_face_region(bm, geom=faces, use_keep_orig=False)
    newf = [g for g in r['geom'] if isinstance(g, bmesh.types.BMFace)]
    newv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    # FACES (not FACES_ONLY): a region's interior edges and vertices go with its faces;
    # its boundary stays, shared with the new side faces
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    if offset is not None:
        for v in newv:
            v.co += Vector(offset)
    # new faces carry index -1 and no normal until updated: sorting a set by a stale index kept the
    # per-run set order, and picking a side by its normal read garbage (stage 1 varied run to run)
    bm.faces.index_update()
    sides = sorted({f for v in newv for f in v.link_faces if f not in newf}, key=lambda f: f.index)
    _fresh(newv)
    return {'faces': newf, 'verts': newv, 'sides': sides}


def inset(bm, faces, amount, depth=0.0):
    """Inset (I), each face on its own: a new ring of vertices inside the face at
    `amount` (0..1) of the way to its centre, pushed `depth` along the normal
    (negative = in). The face's own corners and edges stay where they are, so in
    stage 2 this is a loop in the face that dissolves back out. Returns the inner faces."""
    inner = []
    for f in list(faces):
        c, n = f.calc_center_median(), f.normal.copy()
        vs = list(f.verts)
        ws = [bm.verts.new(v.co.lerp(c, amount) + n * depth) for v in vs]
        bm.faces.remove(f)
        for i in range(len(vs)):
            bm.faces.new([vs[i], vs[(i + 1) % len(vs)], ws[(i + 1) % len(vs)], ws[i]])
        inner.append(bm.faces.new(ws))
    return inner


def _fresh(verts):
    """Recompute the normals of every face on these vertices. bmesh does not update normals when a
    vertex moves, so a face picked by its normal after a move (face_near, max over sides) was
    picked by where it pointed before."""
    for f in {f for v in verts for f in v.link_faces}:
        f.normal_update()


def centre(verts):
    return sum((v.co for v in verts), Vector()) / max(1, len(verts))


def move(verts, d):
    d = Vector(d)
    for v in verts:
        v.co += d
    _fresh(verts)


def scale(verts, s, pivot=None):
    """Scale about pivot (default: their centre). s = number or (sx, sy, sz)."""
    p = Vector(pivot) if pivot is not None else centre(verts)
    s = (s, s, s) if isinstance(s, (int, float)) else s
    for v in verts:
        d = v.co - p
        v.co = p + Vector((d.x * s[0], d.y * s[1], d.z * s[2]))
    _fresh(verts)


def rotate(verts, axis, deg, pivot=None):
    p = Vector(pivot) if pivot is not None else centre(verts)
    R = Matrix.Rotation(math.radians(deg), 3, Vector(axis).normalized() if not isinstance(axis, str) else axis)
    for v in verts:
        v.co = p + R @ (v.co - p)
    _fresh(verts)


def place(verts, pts):
    for v, p in zip(verts, pts):
        v.co = Vector(p)
    _fresh(verts)


def flatten(verts, keep_seam=True):
    """Project the vertices onto their best-fit plane (a deliberate facet).
    keep_seam: vertices on the mirror seam stay on x = 0 (the mirror must close)."""
    P = np.array([v.co[:] for v in verts])
    c = P.mean(axis=0)
    n = np.linalg.svd(P - c)[2][-1]
    for v in verts:
        seam = abs(v.co.x) < SEAM
        q = np.array(v.co[:])
        v.co = Vector(q - np.dot(q - c, n) * n)
        if keep_seam and seam:
            v.co.x = 0.0
    _fresh(verts)


def slide(pairs, t):
    """Loop slide: move each vertex toward its partner by fraction t. pairs = [(v, target_vert), ...]."""
    for v, w in pairs:
        v.co = v.co.lerp(w.co.copy(), t)
    _fresh([v for v, _ in pairs])


def faces_where(bm, pred):
    return [f for f in bm.faces if pred(f.calc_center_median(), f.normal)]


def verts_where(bm, pred):
    return [v for v in bm.verts if pred(v.co)]


def face_near(bm, p, n=None):
    """The face whose centre is nearest p (optionally among faces whose normal . n > 0.3)."""
    p = Vector(p)
    cand = [f for f in bm.faces if n is None or f.normal.dot(Vector(n)) > 0.3]
    return min(cand, key=lambda f: (f.calc_center_median() - p).length)


def edge_near(bm, p):
    p = Vector(p)
    return min(bm.edges, key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2 - p).length)


def vert_near(bm, p):
    p = Vector(p)
    return min(bm.verts, key=lambda v: (v.co - p).length)


def snap_seam(bm, eps=1e-3):
    """Vertices within eps of the mirror plane go onto it; nothing may cross it."""
    for v in bm.verts:
        if v.co.x < eps:
            v.co.x = 0.0


def recalc_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))


def edge_ring(edge, near=None, stop=None):
    """The edges a loop cut through `edge` would cross, walking quad to quad
    across opposite edges in both directions. Each entry is (edge, v0, v1) with
    v0 on the same side of the ring as `near` (default edge.verts[0]).
    stop: optional set of faces the walk may not enter."""
    v0 = near if near is not None else edge.verts[0]
    v1 = edge.other_vert(v0)
    out = [(edge, v0, v1)]
    seen = {edge}
    for di, f0 in enumerate(list(edge.link_faces)[:2]):
        e, a, f = edge, v0, f0
        chain = []
        while f is not None and len(f.verts) == 4 and (stop is None or f not in stop):
            ls = list(f.loops)
            i = next(k for k, l in enumerate(ls) if l.edge == e)
            opp = ls[(i + 2) % 4].edge
            if opp in seen:
                break
            # the vertex of opp joined to a by a side edge of f is on a's side of the ring
            side_e = next(ed for ed in f.edges if ed != e and ed != opp and a in ed.verts)
            na = side_e.other_vert(a)
            nb = opp.other_vert(na)
            seen.add(opp)
            chain.append((opp, na, nb))
            nxt = [g for g in opp.link_faces if g != f]
            e, a, f = opp, na, (nxt[0] if nxt else None)
        out = (list(reversed(chain)) + out) if di == 0 else (out + chain)
    return out


def _split(bm, rows, t):
    """Split each ring edge at fraction t from its v0 and join consecutive new
    vertices across the quad between them (and last to first on a closed ring)."""
    ms = []
    for e, a, b in rows:
        _, m = bmesh.utils.edge_split(e, a, t)
        ms.append(m)
    for m, n in zip(ms, ms[1:]):
        if set(m.link_faces) & set(n.link_faces):
            bmesh.ops.connect_verts(bm, verts=[m, n])
    if len(ms) > 2 and set(ms[-1].link_faces) & set(ms[0].link_faces) \
            and not any(ms[0] in e.verts for e in ms[-1].link_edges):
        bmesh.ops.connect_verts(bm, verts=[ms[-1], ms[0]])
    return ms


def loopcut(bm, edge, t=0.5, near=None):
    """Ctrl-R: one full edge loop through the quad ring that crosses `edge`.
    t: 0..1 from the `near` side (default edge.verts[0]). Returns the new verts."""
    return _split(bm, edge_ring(edge, near), t)


def partial_loop(bm, start, end, t=0.5, near=None, terminate='fan'):
    """A loop that does NOT run round the whole ring: it starts in the quad
    after edge `start` and stops in the quad before edge `end` (both edges of
    the same ring, walked from `start` toward `end`). The two end quads are
    closed with a terminator, so the extra density stays where it is needed
    (the topology cheat sheet: a 2-to-1 / 3-to-1 reduction; flat-shaded low
    poly may end it in triangles):
        'fan'  the end point joins both far corners (three triangles)
        'quad' the end point joins the nearer far corner (one triangle, one quad)
    Returns the new verts."""
    rows = edge_ring(start, near)
    idx = [r[0] for r in rows]
    i, j = idx.index(start), idx.index(end)
    if i > j:
        rows = list(reversed(rows)); idx = [r[0] for r in rows]; i, j = idx.index(start), idx.index(end)
    inner = rows[i + 1:j]
    assert inner, 'partial_loop: start and end must have at least one ring edge between them'
    ms = _split(bm, inner, t)
    for m, far in ((ms[0], rows[i]), (ms[-1], rows[j])):
        _, a, b = far
        corners = [a, b] if terminate == 'fan' else [min((a, b), key=lambda x: (x.co - m.co).length)]
        for c in corners:
            bmesh.ops.connect_verts(bm, verts=[m, c])
    return ms


def chamfer(bm, edge, frac=0.15):
    """A bevel that keeps the base: one loop on each side of the crease that
    `edge` lies on, at `frac` of the neighbouring faces' width from the crease.
    Returns the new verts."""
    new = []
    for f in list(edge.link_faces):
        if len(f.verts) != 4:
            continue
        side = next(e for e in f.edges if e != edge and edge.verts[0] in e.verts)
        new += loopcut(bm, side, t=frac, near=edge.verts[0])
    return new


# =============================================================================
# 2. MATERIALS AND COLOUR
# =============================================================================
def srgb(h):
    """'#8a7b6c' -> linear RGB tuple (Blender and glTF colours are linear)."""
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(name, rgb, rough=0.85):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    m.diffuse_color = (*rgb, 1)          # what the workbench shows
    m.roughness = rough
    return m


def paint(ob, palette, rule):
    """Region colours: palette = {'fur': '#7a6a5a', ...}; rule(centre, normal, face_index) -> a palette key.
    Faces are flat-shaded; COLOR_0 is written as a white shading multiplier (the hue lives in the material)."""
    me = ob.data
    me.materials.clear()
    keys = list(palette)
    for k in keys:
        me.materials.append(material(k, srgb(palette[k]) if isinstance(palette[k], str) else palette[k]))
    mw = ob.matrix_world
    for p in me.polygons:
        c = mw @ p.center
        n = (mw.to_3x3() @ p.normal).normalized()
        p.material_index = keys.index(rule(c, n, p.index))
        p.use_smooth = False
    white(ob)


def white(ob):
    me = ob.data
    col = me.color_attributes.get('Col') or me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    col.data.foreach_set('color', [1.0] * (4 * len(col.data)))
    me.color_attributes.active_color = col


# =============================================================================
# 3. OBJECTS, MIRROR, REPORTS
# =============================================================================
def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def object_from_bm(name, bm, mirror=True):
    recalc_normals(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    me.update()
    ob = link(bpy.data.objects.new(name, me))
    for p in me.polygons:
        p.use_smooth = False
    if mirror:
        md = ob.modifiers.new('mirror', 'MIRROR')
        md.use_axis = (True, False, False)
        md.use_clip = True
        md.use_mirror_merge = True
        md.merge_threshold = 1e-4
    return ob


def has_mirror(ob):
    return any(m.type == 'MIRROR' for m in ob.modifiers)


def edit(ob):
    """A bmesh of the object's own mesh (the half, if the mirror is live)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    return bm


def commit(ob, bm):
    bm.to_mesh(ob.data)
    ob.data.update()
    for p in ob.data.polygons:
        p.use_smooth = False


def evaluated_bm(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    oe.to_mesh_clear()
    bm.transform(ob.matrix_world)
    return bm


def apply_mirror(ob):
    """Apply the Mirror (for asymmetric stage-2 moves or before rigging). Records
    which side each vertex came from, so the lock can still be checked."""
    if not has_mirror(ob):
        return
    bm = edit(ob)
    side = bm.verts.layers.int.get('bside') or bm.verts.layers.int.new('bside')
    for v in bm.verts:
        v[side] = 0 if abs(v.co.x) < SEAM else 1
    commit(ob, bm); bm.free()
    md = next(m for m in ob.modifiers if m.type == 'MIRROR')
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=md.name)
    bm = edit(ob)
    side = bm.verts.layers.int.get('bside')
    for v in bm.verts:                       # the mirrored copies carry +1; flip them
        if v[side] == 1 and v.co.x < 0:
            v[side] = -1
    commit(ob, bm); bm.free()


def report(ob, intersections=True):
    """Counts on the evaluated (mirrored, deformed) mesh."""
    bm = evaluated_bm(ob)
    bm.faces.ensure_lookup_table()
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    # connected components
    seen, comps = set(), 0
    for v in bm.verts:
        if v in seen:
            continue
        comps += 1
        stack = [v]; seen.add(v)
        while stack:
            x = stack.pop()
            for e in x.link_edges:
                w = e.other_vert(x)
                if w not in seen:
                    seen.add(w); stack.append(w)
    nonman = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    quads = sum(1 for f in bm.faces if len(f.verts) == 4)
    hits = None
    if intersections:
        t = BVHTree.FromBMesh(bm)
        hits = 0
        for i, j in t.overlap(t):
            if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
                hits += 1
    lo = Vector([min(v.co[k] for v in bm.verts) for k in range(3)])
    hi = Vector([max(v.co[k] for v in bm.verts) for k in range(3)])
    r = dict(verts=len(bm.verts), faces=len(bm.faces), tris=tris, quads=quads, ngons=ngons,
             components=comps, nonmanifold_edges=nonman, self_intersections=hits,
             bbox=[list(map(lambda x: round(x, 4), lo)), list(map(lambda x: round(x, 4), hi))])
    bm.free()
    return r


def geometry_hash(ob):
    """Positions + connectivity of the object's own mesh (not evaluated)."""
    me = ob.data
    h = hashlib.sha256()
    for v in me.vertices:
        h.update(('%.6f,%.6f,%.6f;' % tuple(v.co)).encode())
    for p in me.polygons:
        h.update((','.join(map(str, p.vertices)) + ';').encode())
    return h.hexdigest()


# =============================================================================
# 4. THE LOCK
# =============================================================================
def _layers(bm):
    L = bm.verts.layers.int
    bid = L.get('bid') or L.new('bid')
    bop = L.get('bop') or L.new('bop')
    borig = bm.edges.layers.int.get('borig') or bm.edges.layers.int.new('borig')
    side = L.get('bside')
    return bid, bop, borig, side


def _key(v, bid, side):
    s = (0 if v[side] == 0 else 1) if side is not None else (0 if abs(v.co.x) < SEAM else 1)
    return (int(v[bid]), s)


def _canon_edges(bm, only_orig=False):
    bid, bop, borig, side = _layers(bm)
    out = set()
    for e in bm.edges:
        if only_orig and not e[borig]:
            continue
        a, b = (_key(v, bid, side) for v in e.verts)
        out.add(tuple(sorted((a, b))))
    return out


def _edge_hash(edges):
    s = ';'.join('%d.%d-%d.%d' % (a[0], a[1], b[0], b[1]) for a, b in sorted(edges))
    return hashlib.sha256(s.encode()).hexdigest()


def _pos_hash(bm):
    bid = bm.verts.layers.int.get('bid')
    s = ';'.join('%d:%.5f,%.5f,%.5f' % (v[bid], *v.co) for v in sorted(bm.verts, key=lambda v: v[bid]))
    return hashlib.sha256(s.encode()).hexdigest()


def canonical_order(ob):
    """Put the stage-1 vertices and faces in position order. bmesh's multi-face
    region extrude creates vertices in a pointer-hash order that can change between
    runs, which made the frozen-lock gate fail with no code change (raven-wyvern v2).
    New locks record order='canonical' and every later run sorts the same way;
    locks made before this keep their legacy order."""
    bm = edit(ob)
    r = lambda c: (round(c.x, 5), round(c.y, 5), round(c.z, 5))
    vr = {v: i for i, v in enumerate(sorted(bm.verts, key=lambda v: r(v.co)))}
    bm.verts.sort(key=lambda v: vr[v])          # bmesh wants a numeric key: the rank
    bm.verts.index_update()
    fr = {f: i for i, f in enumerate(sorted(bm.faces, key=lambda f: r(f.calc_center_median())))}
    bm.faces.sort(key=lambda f: fr[f])
    bm.faces.index_update()
    commit(ob, bm)
    bm.free()


def stamp(ob):
    """Give every stage-1 vertex its base id (1..n) and every edge borig=1."""
    bm = edit(ob)
    bid, bop, borig, side = _layers(bm)
    for i, v in enumerate(bm.verts):
        v[bid] = i + 1
        v[bop] = 0
    for e in bm.edges:
        e[borig] = 1
    commit(ob, bm)
    return bm


def lock_record(ob):
    bm = stamp(ob)
    edges = _canon_edges(bm)
    rep = report(ob, intersections=False)
    lo, hi = Vector(rep['bbox'][0]), Vector(rep['bbox'][1])
    rec = dict(half_verts=len(bm.verts), half_faces=len(bm.faces), verts=rep['verts'], faces=rep['faces'],
               tris=rep['tris'], edges=len(edges), edge_hash=_edge_hash(edges), pos_hash=_pos_hash(bm),
               frame=dict(centre=[round(x, 5) for x in (lo + hi) / 2], size=[round(x, 5) for x in hi - lo]),
               canon_edges=[[list(a), list(b)] for a, b in sorted(edges)])
    bm.free()
    return rec


class Log:
    """stage2_log.json: every connectivity change, what it added, and why."""

    def __init__(self):
        self.ops = []


@contextlib.contextmanager
def topo(bm, log, kind, reason):
    """Wrap EVERY stage-2 connectivity change:
        with topo(bm, k.log, 'loop', 'second loop at the elbow: the bend'):
            loopcut(bm, edge_near(bm, (0.12, -0.4, 0.4)))
    Inside the block do connectivity only (a loop cut may slide along its own
    edges, as loopcut/partial_loop/chamfer do); move vertices after it."""
    bid, bop, borig, side = _layers(bm)
    vb, eb = set(bm.verts), set(bm.edges)
    segs = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in bm.edges if e[borig]]
    yield
    op = len(log.ops) + 1
    nv = [v for v in bm.verts if v not in vb]
    for v in nv:
        v[bid] = 0; v[bop] = op
        if side is not None:
            v[side] = 0 if abs(v.co.x) < SEAM else (1 if v.co.x > 0 else -1)
    extra = []
    for e in bm.edges:
        if e in eb:
            continue
        a, b = e.verts[0].co, e.verts[1].co
        on = False
        for p, q in segs:                      # a piece of an original edge?
            d = q - p
            L2 = d.length_squared
            if L2 < 1e-12:
                continue
            ok = True
            for x in (a, b):
                t = (x - p).dot(d) / L2
                if t < -1e-6 or t > 1 + 1e-6 or (p + d * t - x).length > 1e-6:
                    ok = False; break
            if ok:
                on = True; break
        e[borig] = 1 if on else 0
        if not on and e.verts[0][bid] > 0 and e.verts[1][bid] > 0:
            extra.append(sorted([list(_key(e.verts[0], bid, side)), list(_key(e.verts[1], bid, side))]))
    log.ops.append(dict(op=op, kind=kind, reason=reason, new_verts=len(nv), extra_base_edges=extra))
    say(f'topo #{op} {kind}: +{len(nv)} verts — {reason}')


def assert_lock(ob, lock, log):
    """The base connectivity == the lock + the logged stage-2 insertions."""
    bm = edit(ob)
    bid, bop, borig, side = _layers(bm)
    errs = []
    nops = len(log.ops)
    allowed = {tuple(tuple(k) for k in pair) for o in log.ops for pair in o['extra_base_edges']}
    for v in bm.verts:
        if v[bid] <= 0 and not (1 <= v[bop] <= nops):
            errs.append('unlogged vertex at (%.3f, %.3f, %.3f)' % tuple(v.co))
    seen = {}
    for v in bm.verts:
        if v[bid] > 0:
            s = v[side] if side is not None else (0 if abs(v.co.x) < SEAM else 1)
            seen[(v[bid], s)] = seen.get((v[bid], s), 0) + 1
    dups = [k for k, c in seen.items() if c > 1]
    if dups:
        errs.append(f'{len(dups)} base ids appear twice (geometry was split outside a topo block), e.g. {dups[:3]}')
    lock_keys = {tuple(k) for pair in lock['canon_edges'] for k in pair}
    have = {_key(v, bid, side) for v in bm.verts if v[bid] > 0}
    miss = lock_keys - have
    if miss:
        errs.append(f'{len(miss)} locked vertices are gone, e.g. {sorted(miss)[:3]}')
    for e in bm.edges:
        if not e[borig] and e.verts[0][bid] > 0 and e.verts[1][bid] > 0:
            k = tuple(sorted((_key(e.verts[0], bid, side), _key(e.verts[1], bid, side))))
            if k not in allowed:
                errs.append(f'unlogged edge between locked vertices {k}')
    # collapse: dissolve every non-original edge, then the 2-valent new vertices
    new_edges = [e for e in bm.edges if not e[borig]]
    if new_edges:
        bmesh.ops.dissolve_edges(bm, edges=new_edges, use_verts=True, use_face_split=False)
    left = [v for v in bm.verts if v[bid] <= 0]
    for v in left:
        if v.is_valid and len(v.link_edges) == 2:
            bmesh.utils.vert_collapse_edge(v, v.link_edges[0])
    iso = [v for v in bm.verts if v.is_valid and v[bid] <= 0 and not v.link_edges]
    if iso:                                  # interior vertices of an inset: nothing left to join
        bmesh.ops.delete(bm, geom=iso, context='VERTS')
    left = [v for v in bm.verts if v.is_valid and v[bid] <= 0]
    if left:
        errs.append(f'{len(left)} inserted vertices do not dissolve back out (not a loop / terminator)')
    edges = _canon_edges(bm)
    h = _edge_hash(edges)
    if h != lock['edge_hash']:
        want = {tuple(tuple(k) for k in p) for p in lock['canon_edges']}
        errs.append(f'collapsed edge hash differs from the lock: {len(edges - want)} extra, {len(want - edges)} missing '
                    f'(e.g. extra {sorted(edges - want)[:2]}, missing {sorted(want - edges)[:2]})')
    bm.free()
    res = dict(verdict='PASS' if not errs else 'FAIL', lock_edge_hash=lock['edge_hash'], collapsed_edge_hash=h,
               logged_ops=nops, logged_new_verts=sum(o['new_verts'] for o in log.ops), errors=errs[:20])
    return res


# =============================================================================
# 5. THE CAMERA
# =============================================================================
def _view_dir(view):
    """Direction FROM the creature TO the camera, and the camera's up vector."""
    if view.startswith('az'):
        t = math.radians(int(view[2:]))
        return Vector((math.sin(t), -math.cos(t), 0.0)), Vector((0, 0, 1))
    return {'top': (Vector((0, 0, 1)), Vector((0, -1, 0))),
            'bottom': (Vector((0, 0, -1)), Vector((0, -1, 0))),
            'hero': (Vector((1, -1, 0.5)).normalized(), Vector((0, 0, 1))),
            'hero_low': (Vector((1, -1.2, 0.15)).normalized(), Vector((0, 0, 1))),
            'back34': (Vector((1, 1, 0.45)).normalized(), Vector((0, 0, 1))),
            'front34r': (Vector((-1, -1, 0.35)).normalized(), Vector((0, 0, 1))),
            }[view]


def _aim(cam, pos, target, up):
    f = (target - pos).normalized()
    r = f.cross(up)
    if r.length < 1e-6:
        r = f.cross(Vector((0, 1, 0)))
    r.normalize()
    u = r.cross(f)
    M = Matrix((r, u, -f)).transposed()
    cam.matrix_world = Matrix.Translation(pos) @ M.to_4x4()


def camera(frame, view, ortho=False, fill=1.0):
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        cam = link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam')))
        sc.camera = cam
    c, s = Vector(frame['centre']), Vector(frame['size'])
    L = max(s)
    d, up = _view_dir(view)
    cam.data.clip_start, cam.data.clip_end = 0.01, 100
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = frame.get('ortho', L * 1.25) / fill
    else:
        cam.data.type = 'PERSP'
        cam.data.angle = FOV
    dist = L * DIST / fill
    _aim(cam, c + d * dist, c, up)
    return cam


def _workbench(mode):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.show_cavity = mode in ('clay', 'wire', 'colour')
    sh.cavity_type = 'BOTH'
    sh.cavity_ridge_factor, sh.cavity_valley_factor = 0.6, 0.8
    # an outline round every separate object drew a dark 'sticker edge' round each piece in the
    # colour and tech renders (the art directors read it as glued-on); a game draws none
    sh.show_object_outline = mode in ('clay', 'wire')
    sh.object_outline_color = (0.08, 0.08, 0.08)
    sh.show_shadows = mode == 'colour'
    sh.shadow_intensity = 0.35
    sh.color_type = {'colour': 'MATERIAL', 'tech': 'VERTEX'}.get(mode, 'OBJECT')
    if mode == 'tech':
        sh.show_cavity = False
    sh.show_specular_highlight = False
    sc.display.render_aa = '8' if mode != 'mask' else 'OFF'
    sc.render.film_transparent = mode == 'mask'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    if mode in ('clay', 'wire') and CLAY_MATCAP:
        sh.light = 'MATCAP'
        sh.studio_light = CLAY_MATCAP
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    sc.world.color = (0.72, 0.72, 0.70) if mode != 'mask' else (1, 1, 1)


def _render(path, res):
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA' if sc.render.film_transparent else 'RGB'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _meshes():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.name.startswith('_')]


def _wire_dups(objs, frame):
    t = max(frame['size']) * 0.0032
    dups = []
    for o in objs:
        d = o.copy()                       # shares the mesh, keeps the modifier stack (mirror / armature)
        d.name = '_wire_' + o.name
        link(d)
        wm = d.modifiers.new('wf', 'WIREFRAME')
        wm.thickness = t
        wm.use_replace = True
        wm.use_even_offset = True
        d.color = (0.02, 0.02, 0.02, 1)
        dups.append(d)
    return dups


def shoot(outdir, tag, frame, views=ROUND_VIEWS, wire_views=WIRE_VIEWS, colour=False, res=512, objs=None, fill=None,
          modes_override=None):
    """Clay (flat grey) renders of every view, wire-over-clay of wire_views, and
    material-colour renders when colour=True. Files: <tag>_<view>_<mode>.png
    BMK_NORENDER=1 skips every picture (gates and QA still run): the regression sweep."""
    if os.environ.get('BMK_NORENDER'):
        return []
    os.makedirs(outdir, exist_ok=True)
    objs = objs or _meshes()
    for o in objs:
        o.color = (0.78, 0.78, 0.76, 1)
    files = []
    modes = modes_override or (['clay'] + (['colour'] if colour else []))
    for mode in modes:
        _workbench(mode)
        for v in views:
            camera(frame, v, fill=fill or FILL)
            p = os.path.join(outdir, f'{tag}_{v}_{mode}.png')
            _render(p, res); files.append(p)
    if wire_views:
        _workbench('wire')
        dups = _wire_dups(objs, frame)
        for v in wire_views:
            camera(frame, v, fill=fill or FILL)
            p = os.path.join(outdir, f'{tag}_{v}_wire.png')
            _render(p, res); files.append(p)
        for d in dups:
            bpy.data.objects.remove(d, do_unlink=True)
    return files


def masks(frame, views=ORBIT, res=256, objs=None):
    """Silhouette masks under the fixed frame: {view: bool array}."""
    import tempfile
    objs = objs or _meshes()
    _workbench('mask')
    out = {}
    tmp = tempfile.mkdtemp()
    for v in views:
        camera(frame, v)
        p = os.path.join(tmp, f'm_{v}.png')
        _render(p, res)
        img = bpy.data.images.load(p)
        a = np.empty(res * res * 4, dtype=np.float32)
        img.pixels.foreach_get(a)
        out[v] = a.reshape(res, res, 4)[:, :, 3] > 0.5
        bpy.data.images.remove(img)
    return out


def iou(a, b):
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else 1.0


def ortho_views(outdir, blueprint, objs=None, res=640):
    """Orthographic silhouettes (side = the left flank, front, top) framed by the
    blueprint, for run.py to draw the blueprint over. Writes ortho.json with the mapping."""
    bp = json.load(open(blueprint))
    ys = [p[0] for p in bp['side']['outline']]; zs = [p[1] for p in bp['side']['outline']]
    xs = [abs(p[0]) for p in bp.get('front', {}).get('outline', [[0.3, 0]])]
    size = [2 * max(xs), max(ys) - min(ys), max(zs) - min(zs)]
    cen = [0.0, (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2]
    ortho = max(size) * 1.2
    frame = dict(centre=cen, size=size, ortho=ortho)
    _workbench('mask')
    maps = {}
    for name, view in (('side', 'az090'), ('front', 'az000'), ('top', 'top')):
        camera(frame, view, ortho=True)
        p = os.path.join(outdir, f'ortho_{name}.png')
        _render(p, res)
        maps[name] = os.path.basename(p)     # never an absolute path in a shipped file
    json.dump(dict(frame=frame, res=res, files=maps,
                   axes={'side': ['y', 'z'], 'front': ['x', 'z'], 'top': ['-x', '-y']}),
              open(os.path.join(outdir, 'ortho.json'), 'w'), indent=1)


# =============================================================================
# 6. RIG AND ANIMATION
# =============================================================================
def armature(bones, name='rig', roll=None):
    """bones: list of (name, head, tail, parent_or_None[, connect]). A name ending
    in '.L' (on +X) also creates its '.R' mirror, with parents mirrored too.
    roll='auto': every bone's local Z points forward (-Y), or up (+Z) for a bone
    lying along Y, so bone-local +X swings a hanging limb's tip FORWARD and
    pitches spine/neck bones the same way on both sides. None keeps Blender's
    default rolls (what batches 1-2 were animated with)."""
    full = []
    for b in bones:
        nm, h, t, par = b[:4]
        con = b[4] if len(b) > 4 else False
        full.append((nm, h, t, par, con))
        if nm.endswith('.L'):
            mp = par[:-2] + '.R' if par and par.endswith('.L') else par
            full.append((nm[:-2] + '.R', (-h[0], h[1], h[2]), (-t[0], t[1], t[2]), mp, con))
    arm = bpy.data.armatures.new(name)
    rig = link(bpy.data.objects.new(name, arm))
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for nm, h, t, par, con in full:
            eb = arm.edit_bones.new(nm)
            eb.head, eb.tail = Vector(h), Vector(t)
        for nm, h, t, par, con in full:
            if par:
                arm.edit_bones[nm].parent = arm.edit_bones[par]
                arm.edit_bones[nm].use_connect = con
        if roll == 'auto':
            for eb in arm.edit_bones:
                d = (eb.tail - eb.head).normalized()
                eb.align_roll(Vector((0, 0, 1)) if abs(d.y) > 0.7 else Vector((0, -1, 0)))
        bpy.ops.object.mode_set(mode='OBJECT')
    return rig


def skin(body, rig):
    """Automatic (bone heat) weights on the base mesh; the Mirror is applied first.
    Vertices heat leaves unweighted fall back to the nearest bone."""
    apply_mirror(body)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    body.select_set(True); rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[body, rig],
                                   selected_editable_objects=[body, rig]):
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    return _fill_unweighted(body, rig)


def _bone_segments(rig):
    M = rig.matrix_world
    return {b.name: (M @ b.head_local, M @ b.tail_local) for b in rig.data.bones if b.use_deform}


def _seg_dist(p, a, b):
    d = b - a
    t = max(0.0, min(1.0, (p - a).dot(d) / max(d.length_squared, 1e-12)))
    return (a + d * t - p).length


def _fill_unweighted(ob, rig):
    segs = _bone_segments(rig)
    groups = {g.index: g.name for g in ob.vertex_groups}
    fixed = 0
    for v in ob.data.vertices:
        if sum(g.weight for g in v.groups if groups.get(g.group) in segs) > 1e-4:
            continue
        p = ob.matrix_world @ v.co
        nm = min(segs, key=lambda n: _seg_dist(p, *segs[n]))
        vg = ob.vertex_groups.get(nm) or ob.vertex_groups.new(name=nm)
        vg.add([v.index], 1.0, 'REPLACE')
        fixed += 1
    return fixed


def bind(piece, rig, bone=None, body=None):
    """A stage-3 piece follows the skeleton: rigidly to one bone, or with the
    weights of the nearest body surface (fur ruffs, crests) when body is given."""
    if has_mirror(piece):
        with bpy.context.temp_override(object=piece, active_object=piece, selected_objects=[piece]):
            bpy.ops.object.modifier_apply(modifier=next(m for m in piece.modifiers if m.type == 'MIRROR').name)
    piece.vertex_groups.clear()
    if bone:
        vg = piece.vertex_groups.new(name=bone)
        vg.add(list(range(len(piece.data.vertices))), 1.0, 'REPLACE')
    elif body is not None:
        for g in body.vertex_groups:
            piece.vertex_groups.new(name=g.name)
        dt = piece.modifiers.new('dt', 'DATA_TRANSFER')
        dt.object = body
        dt.use_vert_data = True
        dt.data_types_verts = {'VGROUP_WEIGHTS'}
        dt.vert_mapping = 'POLYINTERP_NEAREST'
        dt.layers_vgroup_select_src = 'ALL'
        dt.layers_vgroup_select_dst = 'NAME'
        with bpy.context.temp_override(object=piece, active_object=piece, selected_objects=[piece]):
            bpy.ops.object.modifier_apply(modifier=dt.name)
    else:
        segs = _bone_segments(rig)
        for v in piece.data.vertices:
            p = piece.matrix_world @ v.co
            nm = min(segs, key=lambda n: _seg_dist(p, *segs[n]))
            vg = piece.vertex_groups.get(nm) or piece.vertex_groups.new(name=nm)
            vg.add([v.index], 1.0, 'REPLACE')
    _fill_unweighted(piece, rig)
    mw = piece.matrix_world.copy()
    piece.parent = rig
    piece.matrix_world = mw
    am = piece.modifiers.new('armature', 'ARMATURE')
    am.object = rig


def clip(rig, name, keys, loc=None):
    """keys = {frame: {bone: (rx, ry, rz) degrees, bone-local XYZ}}; loc = {frame: {bone: (x, y, z)}}.
    Every bone named anywhere is keyed at every frame listed (missing -> rest).
    The action is stored on its own NLA track (muted) so each clip exports alone."""
    ad = rig.animation_data or rig.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ad.action = act
    pb = rig.pose.bones
    rb = sorted({b for f in keys.values() for b in f})
    lb = sorted({b for f in (loc or {}).values() for b in f})
    frames = sorted(set(keys) | set(loc or {}))
    for f in frames:
        for b in rb:
            pb[b].rotation_mode = 'XYZ'
            pb[b].rotation_euler = [math.radians(x) for x in keys.get(f, {}).get(b, (0, 0, 0))]
            pb[b].keyframe_insert('rotation_euler', frame=f)
        for b in lb:
            pb[b].location = (loc or {}).get(f, {}).get(b, (0, 0, 0))
            pb[b].keyframe_insert('location', frame=f)
    rest(rig)
    tr = ad.nla_tracks.new()
    tr.name = name
    tr.strips.new(name, int(frames[0]), act)
    tr.mute = True
    ad.action = None
    return act


def rest(rig):
    for b in rig.pose.bones:
        b.rotation_mode = 'XYZ'
        b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)


def pose(rig, act, frame):
    import techqa
    techqa._zero_pose(rig)      # bones this clip does not key sit at rest, not where the last clip left them
    rig.animation_data.action = act
    bpy.context.scene.frame_set(int(frame))


# =============================================================================
# 7. EXPORT
# =============================================================================
def export_glb(path, objs, anim=False):
    for o in objs:              # a grey stage has no palette yet; harness/outline.py draws nothing without one
        if o.type == 'MESH' and not o.data.materials:
            o.data.materials.append(material('clay', (0.6, 0.6, 0.6)))
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_animations=anim, export_skins=anim, export_vertex_color='ACTIVE',
              export_all_vertex_colors=False, export_materials='EXPORT', export_extras=False,
              export_attributes=False, export_image_format='NONE', export_morph=False)
    if anim:
        kw.update(export_animation_mode='ACTIONS', export_force_sampling=True, export_def_bones=True)
    bpy.ops.export_scene.gltf(**kw)


# =============================================================================
# 7b. VIEW FRAME, CLOSE-UPS, TECH QA
# =============================================================================
def frame_of(objs, base=None):
    """Bounding frame of the evaluated objects, grown to contain `base` (the locked
    stage-1 frame): stage 3/4 renders use it so antlers and crests are not cropped."""
    lo = Vector((1e9, 1e9, 1e9)); hi = -lo
    for o in objs:
        bm = evaluated_bm(o)
        for v in bm.verts:
            lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
        bm.free()
    if base:
        c, s = Vector(base['centre']), Vector(base['size'])
        lo = Vector(map(min, lo, c - s / 2)); hi = Vector(map(max, hi, c + s / 2))
    return dict(centre=[round(x, 5) for x in (lo + hi) / 2], size=[round(x, 5) for x in hi - lo])


def auto_closeups(rig, frame, pieces=()):
    """Close-up targets: the head (with everything parented under it), one front
    limb chain, one hind limb chain, and the biggest detail piece (antlers, ruff,
    crest: where pass-through and shard errors live). [(name, point, radius, view)].
    META['closeups'] overrides."""
    L = max(frame['size'])
    M = rig.matrix_world
    bones = list(rig.data.bones)

    def side_ok(b):
        n = b.name.lower()
        return not n.endswith(('.r', '_r')) and not n.startswith(('r_', 'right'))

    def pick(keys):
        for key in keys:
            for b in bones:
                if key in b.name.lower() and side_ok(b):
                    return b
        return None

    def extent(b, up=False):
        root = b
        if up:        # climb to the top of the limb chain (while the parent is still on this side)
            while root.parent and root.parent.name.lower()[-2:] == root.name.lower()[-2:] and \
                    root.name.lower()[-2:] in ('.l', '_l'):
                root = root.parent
        pts = []
        stack = [root]
        while stack:
            x = stack.pop()
            pts += [M @ x.head_local, M @ x.tail_local]
            stack += list(x.children)
        lo = Vector([min(q[k] for q in pts) for k in range(3)])
        hi = Vector([max(q[k] for q in pts) for k in range(3)])
        return (lo + hi) / 2, (hi - lo).length

    out = []
    h = pick(['head', 'skull'])
    if h:
        c, d = extent(h)
        out.append(('head', c, max(0.75 * d, 0.09 * L), 'hero'))
    fore = pick(['forearm', 'fore', 'lowerarm', 'hand', 'wrist', 'arm', 'wing', 'claw'])
    if fore:
        c, d = extent(fore, up=True)
        out.append(('front limb', c, max(0.6 * d, 0.09 * L), 'hero'))
    hind = pick(['shin', 'hock', 'calf', 'lowerleg', 'thigh', 'leg', 'foot'])
    if hind:
        c, d = extent(hind, up=True)
        out.append(('hind limb', c, max(0.6 * d, 0.09 * L), 'back34'))
    if pieces:
        big = max(pieces, key=lambda o: len(o.data.polygons))
        bm = evaluated_bm(big)
        lo = Vector([min(v.co[k] for v in bm.verts) for k in range(3)])
        hi = Vector([max(v.co[k] for v in bm.verts) for k in range(3)])
        bm.free()
        out.append((f'{big.name[6:] if big.name.startswith("piece_") else big.name} (largest piece)',
                    (lo + hi) / 2, max(0.65 * (hi - lo).length, 0.09 * L), 'hero'))
    else:
        out.append(('body side', Vector(frame['centre']), 0.36 * L, 'az090'))
    return out[:4]


def closeups(outdir, targets, res=640):
    """Colour and wire close-ups of each target: close_<i>_colour.png / close_<i>_wire.png."""
    if os.environ.get('BMK_NORENDER'):
        return []
    files = []
    objs = _meshes()
    for i, (name, p, r, view) in enumerate(targets):
        dist = r / math.tan(FOV / 2)
        fr = dict(centre=list(p), size=[dist / DIST] * 3)      # camera(): distance = max(size) * DIST
        _workbench('colour')
        camera(fr, view)
        a = os.path.join(outdir, f'close_{i}_colour.png'); _render(a, res)
        _workbench('wire')
        for o in objs:
            o.color = (0.78, 0.78, 0.76, 1)
        dups = _wire_dups(objs, dict(size=[r * 1.2] * 3))
        camera(fr, view)
        b = os.path.join(outdir, f'close_{i}_wire.png'); _render(b, res)
        for d in dups:
            bpy.data.objects.remove(d, do_unlink=True)
        files.append((name, a, b))
    _dump(os.path.join(outdir, 'closeups.json'),
          [dict(name=n, colour=os.path.basename(a), wire=os.path.basename(b)) for n, a, b in files])
    return files


QA_LIMITS = dict(sliver_pct=2.0, hit=0, float=0, zfight=2, flip_pct=0.5, flip_area_pct=0.5, drift=0)


def qa_step(k, N, body, pieces, frame, rig=None, acts=None):
    """Turn edges so folds follow the form, then measure, paint and gate."""
    import techqa as Q
    objs = [body] + list(pieces)
    turned = stuck = 0
    if (os.environ.get('BMK_TRI') or k.meta.get('triangulate', 'convex')) == 'convex':
        for o in objs:
            t_, s_ = Q.triangulate_convex(o, keep=k.meta.get('keep_valleys'))
            turned += t_; stuck += s_
    counts, flags, tris = Q.measure(body, pieces, frame['size'], rig, acts)
    tot, ntris = Q.summary(counts, tris)
    ok = True
    ok &= _gate(f's{N} qa: no piece passes through a surface twice (hit)', tot['hit'] <= QA_LIMITS['hit'], f"{tot['hit']} shells")
    ok &= _gate(f's{N} qa: no floating piece', tot['float'] <= QA_LIMITS['float'], f"{tot['float']} shells")
    ok &= _gate(f's{N} qa: no z-fighting', tot['zfight'] <= QA_LIMITS['zfight'], f"{tot['zfight']} faces")
    sl = 100.0 * tot['sliver'] / max(1, ntris)
    ok &= _gate(f's{N} qa: sliver triangles <= {QA_LIMITS["sliver_pct"]}%', sl <= QA_LIMITS['sliver_pct'],
                f"{tot['sliver']} ({sl:.1f}%)")
    if rig is not None:
        fp = 100.0 * tot['flip'] / max(1, ntris)
        fa = 100.0 * tot.get('flip_area', 0) / max(1e-12, tot.get('area', 0))
        ok &= _gate(f's{N} qa: posed fold-overs/collapses <= {QA_LIMITS["flip_pct"]}% of triangles and '
                    f'<= {QA_LIMITS["flip_area_pct"]}% of surface area',
                    fp <= QA_LIMITS['flip_pct'] and fa <= QA_LIMITS['flip_area_pct'],
                    f"{tot['flip']} ({fp:.2f}% of tris, {fa:.2f}% of area)")
        ok &= _gate(f's{N} qa: no piece comes off the body in a pose (drift)', tot.get('drift', 0) <= QA_LIMITS['drift'],
                    f"{tot.get('drift', 0)} shells — bind them with body= weights (or the bone under them)")
        ca = 100.0 * tot.get('clip_area', 0) / max(1e-12, tot.get('area', 0))
        if tot.get('clip', 0):
            say(f"WARN s{N} qa: {tot['clip']} triangles ({ca:.2f}% of surface) clip through the body in a pose that "
                f"did not at rest (pink): a limb through a flap, a paw through the cheek")
    if tot['open']:
        say(f"WARN s{N} qa: {tot['open']} open edges on pieces (single-sided plates read as shards edge-on)")

    if tot['valley'] or tot['fold']:
        say(f"WARN s{N} qa: {tot['valley']} valley-folded and {tot['fold']} hard-folded faces left")
    say(f's{N} qa: turned {turned} edges so folds follow the form ({stuck} pinched folds could not be turned)')
    Q.paint_heatmap(objs, flags)
    shoot(k.path(f'stage{N}'), f's{N}', frame, views=['hero', 'az090', 'az000', 'back34'], wire_views=[],
          res=640, fill=FILL, modes_override=['tech'])
    Q.clear_heatmap(objs)
    _dump(k.path(f'stage{N}', 'techqa.json'), dict(limits=QA_LIMITS, totals=tot, triangles=ntris, turned=turned, stuck=stuck,
                                                  per_object=counts, ok=bool(ok)))
    return ok


# =============================================================================
# 8. THE STAGE RUNNER
# =============================================================================
class K:
    """What a stage function receives: the log, the paths, and the frame."""

    def __init__(self, a, meta):
        self.a, self.meta = a, meta
        self.dir = a.out
        self.log = Log()
        self.frame = None
        self.topo = lambda bm, kind, reason: topo(bm, self.log, kind, reason)

    def path(self, *p):
        q = os.path.join(self.dir, *p)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        return q


def _args():
    import argparse
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--scratch', required=True)
    ap.add_argument('--stage', type=int, default=1)
    ap.add_argument('--round', type=int, default=0)
    ap.add_argument('--lock', action='store_true')
    ap.add_argument('--final', action='store_true', help='full render set for the requested stage')
    return ap.parse_args(argv)


def _dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=1)


def _gate(name, ok, detail=''):
    say(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail else ''))
    return ok


def run(meta, stage1, stage2=None, stage3=None, stage4=None):
    t0 = time.time()
    a = _args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    k = K(a, meta)
    N = a.stage
    ok = True
    lockp = k.path('stage1_lock.json')
    bpfile = k.path('blueprint.json')

    # ---- stage 1 --------------------------------------------------------------
    body = stage1(k)
    body.name = 'body'
    body.data.name = 'body'
    _L0 = json.load(open(lockp)) if os.path.exists(lockp) else None
    if _L0 is None or _L0.get('order') == 'canonical':
        canonical_order(body)
    r1 = report(body)
    tri_lo, tri_hi = meta.get('stage1_tris', (400, 1500))
    ok &= _gate('s1 one connected shell', r1['components'] == 1, f"{r1['components']} components")
    ok &= _gate('s1 closed (no open or non-manifold edges)', r1['nonmanifold_edges'] == 0, f"{r1['nonmanifold_edges']} edges")
    ok &= _gate('s1 no self-intersection', r1['self_intersections'] == 0, f"{r1['self_intersections']} face pairs")
    ok &= _gate('s1 triangles in budget', tri_lo <= r1['tris'] <= tri_hi, f"{r1['tris']} (budget {tri_lo}-{tri_hi})")
    ok &= _gate('s1 mirrored', has_mirror(body))
    rec = lock_record(body)
    k.frame = rec['frame']
    if os.path.exists(lockp):
        L = json.load(open(lockp))
        same = L['edge_hash'] == rec['edge_hash'] and L['pos_hash'] == rec['pos_hash']
        ok &= _gate('s1 matches stage1_lock.json (stage 1 is frozen)', same,
                    '' if same else 'stage1() changed after the lock — put the change in stage2(), '
                    'or delete the lock and log why in NOTES.md')
        k.frame = L['frame']
        if not same:
            say('SUMMARY', json.dumps(dict(ok=False, stage=1)))
            return _finish(ok, t0)
    elif a.lock:
        if not ok:
            say('refusing to lock: stage 1 gates fail')
        else:
            rec['locked_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            rec['order'] = 'canonical'
            rec['meta'] = meta
            _dump(lockp, rec)
            say(f"LOCKED stage 1: {rec['verts']} verts, {rec['faces']} faces, {rec['tris']} tris, edge sha256 {rec['edge_hash'][:16]}")
    elif N > 1:
        _gate('s1 is locked before stage 2 starts', False, 'run --stage 1 --lock first')
        return _finish(False, t0)
    s1stats = dict(report=r1, lock=os.path.exists(lockp))
    _dump(k.path('stage1', 'stats.json'), s1stats)
    if N == 1 or not os.path.exists(k.path('stage1', 'masks.npz')):
        m1 = masks(k.frame)
        np.savez_compressed(k.path('stage1', 'masks.npz'), **m1)
    if N == 1:
        shoot(k.path('stage1'), 's1', k.frame)
        if os.path.exists(bpfile):
            ortho_views(k.path('stage1'), bpfile, objs=[body])
        export_glb(k.path('stage1', 's1.glb'), [body])
        say('SUMMARY', json.dumps(dict(ok=bool(ok), stage=1, tris=r1['tris'], verts=r1['verts'])))
        return _finish(ok, t0)

    # ---- stage 2 --------------------------------------------------------------
    lock = json.load(open(lockp))
    stage2(k, body)
    _dump(k.path('stage2_log.json'), dict(ops=k.log.ops))
    la = assert_lock(body, lock, k.log)
    ok &= _gate('s2 base connectivity = lock + logged loops', la['verdict'] == 'PASS', '; '.join(la['errors'][:3]))
    r2 = report(body)
    ok &= _gate('s2 one closed shell, no self-intersection',
                r2['components'] == 1 and r2['nonmanifold_edges'] == 0 and r2['self_intersections'] == 0,
                f"{r2['components']} comp, {r2['nonmanifold_edges']} open edges, {r2['self_intersections']} hits")
    m1 = dict(np.load(k.path('stage1', 'masks.npz')))
    m2 = masks(k.frame, objs=[body])
    ious = {v: round(iou(m1[v], m2[v]), 3) for v in ORBIT}
    low = {v: x for v, x in ious.items() if x < 0.9}
    ok &= _gate('s2 silhouette IoU vs stage 1 > 0.9 per view', not low, f'low: {low}' if low else f'min {min(ious.values())}')
    _dump(k.path('stage2', 'stats.json'), dict(report=r2, lock_assert=la, iou_vs_stage1=ious))
    if N == 2:
        ok &= qa_step(k, 2, body, [], k.frame)
        shoot(k.path('stage2'), 's2', k.frame)
        export_glb(k.path('stage2', 's2.glb'), [body])
        say('SUMMARY', json.dumps(dict(ok=bool(ok), stage=2, tris=r2['tris'], min_iou=min(ious.values()))))
        return _finish(ok, t0)

    # ---- stage 3 --------------------------------------------------------------
    g0 = geometry_hash(body)
    pieces = stage3(k, body) or []
    for p in pieces:
        if not p.name.startswith('piece_'):
            p.name = 'piece_' + p.name
    ok &= _gate('s3 base mesh untouched by stage 3', geometry_hash(body) == g0)
    la3 = assert_lock(body, lock, k.log)
    ok &= _gate('s3 lock assertion', la3['verdict'] == 'PASS', '; '.join(la3['errors'][:3]))
    mats = {m.name for o in [body] + pieces for m in o.data.materials if m}
    ok &= _gate('s3 4-8 region colours', 4 <= len(mats) <= 8, f'{len(mats)}: {sorted(mats)}')
    tris = report(body, False)['tris'] + sum(report(p, False)['tris'] for p in pieces)
    t_lo, t_hi = meta.get('total_tris', (500, 3000))
    ok &= _gate('s3 total triangles in budget', t_lo <= tris <= t_hi, f'{tris} (budget {t_lo}-{t_hi})')
    _dump(k.path('stage3', 'stats.json'), dict(lock_assert=la3, colours=sorted(mats), tris=tris,
                                               pieces={p.name: report(p, False)['tris'] for p in pieces}))
    _dump(k.path('lock_assert.json'), dict(stage=3, **la3))
    if N == 3:
        vf = frame_of([body] + pieces, k.frame)
        ok &= qa_step(k, 3, body, pieces, vf)
        shoot(k.path('stage3'), 's3', vf, colour=True)
        export_glb(k.path('stage3', 's3.glb'), [body] + pieces)
        say('SUMMARY', json.dumps(dict(ok=bool(ok), stage=3, tris=tris, colours=len(mats))))
        return _finish(ok, t0)

    # ---- stage 4 --------------------------------------------------------------
    rig = stage4(k, body, pieces)
    acts = {a_.name: a_ for a_ in bpy.data.actions}
    need = {'idle', 'move', 'attack'}
    ok &= _gate('s4 clips idle / move / attack', need <= set(acts), f'have {sorted(acts)}')
    unweighted = 0
    for o in [body] + pieces:
        segs = {b.name for b in rig.data.bones if b.use_deform}
        gi = {g.index: g.name for g in o.vertex_groups}
        unweighted += sum(1 for v in o.data.vertices if sum(g.weight for g in v.groups if gi.get(g.group) in segs) <= 1e-4)
    ok &= _gate('s4 every vertex weighted', unweighted == 0, f'{unweighted} unweighted')
    la4 = assert_lock(body, lock, k.log)
    ok &= _gate('s4 final lock assertion', la4['verdict'] == 'PASS', '; '.join(la4['errors'][:3]))
    _dump(k.path('lock_assert.json'), dict(stage=4, **la4))
    name = meta['creature']
    glb = k.path('stage4', f'{name}.glb')
    if rig.animation_data:
        rig.animation_data.action = None
    rest(rig)
    bpy.context.scene.frame_set(1)
    vf = frame_of([body] + pieces, k.frame)
    ok &= qa_step(k, 4, body, pieces, vf, rig, {n: acts[n] for n in sorted(need) if n in acts})  # need is a set of str: its order changes per process
    export_glb(glb, [body] + pieces + [rig], anim=True)
    shoot(k.path('stage4'), 's4', vf, views=['hero', 'az090', 'az000', 'back34', 'top', 'hero_low'],
          wire_views=['hero', 'az090'], colour=True, res=768)
    closeups(k.path('stage4'), k.meta.get('closeups') or auto_closeups(rig, vf, pieces))
    # posed: two frames from each clip, clay + wire, to see the skin deform (the neck!)
    posed = []
    for cn in ('idle', 'move', 'attack'):
        if cn not in acts:
            continue
        fr = acts[cn].frame_range
        for f in (int(fr[0] + (fr[1] - fr[0]) * 0.25), int(fr[0] + (fr[1] - fr[0]) * 0.5)):
            pose(rig, acts[cn], f)
            posed += shoot(k.path('stage4', 'posed'), f'{cn}_f{f:03d}', vf, views=['hero', 'az090'],
                           wire_views=['hero'], colour=True, res=512)
    rig.animation_data.action = None
    rest(rig)
    bpy.context.scene.frame_set(1)
    _dump(k.path('stage4', 'stats.json'), dict(clips={n: list(a_.frame_range) for n, a_ in acts.items()},
                                               bones=len(rig.data.bones), unweighted=unweighted, lock_assert=la4))
    say('SUMMARY', json.dumps(dict(ok=bool(ok), stage=4, glb=glb)))
    return _finish(ok, t0)


def _finish(ok, t0):
    say(f'{"OK" if ok else "NOT OK"} in {time.time() - t0:.1f}s')
    sys.stdout.flush()
    return ok
