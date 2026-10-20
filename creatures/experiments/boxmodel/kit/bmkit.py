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
           details are separate objects; 4-8 region colours (distinct COLOURS: two
           material names with one colour count once, so a library part's slots
           cost nothing when they map onto the palette).
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


def _loop_normal(P):
    c = sum(P, Vector()) / len(P)
    n = Vector()
    for i in range(len(P)):
        n += (P[i] - c).cross(P[(i + 1) % len(P)] - c)
    return c, (n.normalized() if n.length > 1e-12 else Vector((0, 0, 1)))


def bridge_uneven(bm, a, b):
    """Quads and triangles between two CLOSED vertex loops of DIFFERENT lengths (a limb's 6-ring
    onto a paw's 10-ring). Each loop is given in order; b is reversed and rotated to line up with
    a, the two are matched by angle round their own centres, a quad is made where both advance
    and a triangle where only one does. Returns the new faces. Equal lengths: use bridge()."""
    a, b = list(a), list(b)
    ca, na_ = _loop_normal([v.co for v in a])
    cb, nb_ = _loop_normal([v.co for v in b])
    if na_.dot(nb_) < 0:
        b.reverse()
    e1 = a[0].co - ca
    e1 -= na_ * e1.dot(na_)
    e1.normalize()
    e2 = na_.cross(e1)

    def angles(loop, c):
        out = []
        for v in loop:
            d = v.co - c
            out.append(math.atan2(d.dot(e2), d.dot(e1)))
        return out
    tb = angles(b, cb)
    j0 = min(range(len(b)), key=lambda j: abs(tb[j]))
    b = b[j0:] + b[:j0]

    def mono(loop, c):
        t = angles(loop, c)
        out = [t[0]]
        for x in t[1:]:
            while x < out[-1] - math.pi:
                x += 2 * math.pi
            out.append(max(x, out[-1]))
        return out + [out[0] + 2 * math.pi]
    ta, tb = mono(a, ca), mono(b, cb)
    na, nb = len(a), len(b)
    A, Bv = a + [a[0]], b + [b[0]]
    i = j = 0
    faces = []
    while i < na or j < nb:
        opts = []
        if i < na and j < nb:
            opts.append((0.75 * abs(ta[i + 1] - tb[j + 1]), 2))
        if i < na:
            opts.append((abs(ta[i + 1] - tb[j]) if j < nb else -1.0, 0))
        if j < nb:
            opts.append((abs(ta[i] - tb[j + 1]) if i < na else -1.0, 1))
        kind = min(opts)[1]
        if kind == 2:
            vs = [A[i], A[i + 1], Bv[j + 1], Bv[j]]; i += 1; j += 1
        elif kind == 0:
            vs = [A[i], A[i + 1], Bv[j]]; i += 1
        else:
            vs = [A[i], Bv[j + 1], Bv[j]]; j += 1
        faces.append(bm.faces.new(vs))
    return faces


def bridge_part(part, ring, bm=None, log=None, shrink=0.92, sink=0.25, reason=''):
    """Join a library part built with open_root=True (parts.paw_canine, hoof_cloven, hand ...) to a
    cage ring with a different vertex count.

    ring   the cage's limb-end loop in order: world points, BMVerts, or the end-cap BMFace
           (k.face_near(bm, p)).
    STAGE 3 (bm=None; the base may not change): the part stays a separate piece. A copy of the
           cage ring, shrunk to `shrink` and sunk `sink` x its radius into the limb, is added to the
           PART, stitched to the part's root ring (bridge_uneven) and capped: a closed shell whose
           root takes the limb's own section and is buried in it. Logged to stage3/stats.json
           ('attach') when called as k.bridge_part(part, ring, reason=...). Returns the part.
    STAGE 1 (bm = the body half being built, before the lock): the part's root shell is copied
           INTO bm and stitched to the ring's own vertices; a cap face on the ring is removed.
           The base stays one shell. A part's other shells (a canine paw's toe beans and claws,
           a fist's thumb) cannot join a one-shell base: they stay behind in an object renamed
           '_rest_<name>' (hidden from the stage-1 and stage-2 renders by the underscore), which
           is returned: keep it and return it from stage3 as a piece. Returns None when the part
           was one shell (the part object is then deleted)."""
    import parts as _P
    root_pts = _P.attach(part).get('root_ring')
    assert root_pts, f'bridge_part: {part.name} has no open root ring (build it with open_root=True)'
    cap_face = ring if isinstance(ring, bmesh.types.BMFace) else None
    rv = list(cap_face.verts) if cap_face else list(ring)
    is_bm = bool(rv) and isinstance(rv[0], bmesh.types.BMVert)
    rp = [v.co.copy() if is_bm else Vector(v) for v in rv]
    src = edit(part)
    src.transform(part.matrix_world)

    def root_of(verts):
        vs = list(verts)
        out = [min(vs, key=lambda v: (v.co - q).length_squared) for q in root_pts]
        assert len(set(out)) == len(out), 'bridge_part: root ring vertices not found on the part'
        return out
    if bm is None:
        c, _ = _loop_normal(rp)
        rad = sum((p - c).length for p in rp) / len(rp)
        into = c - sum((v.co for v in src.verts), Vector()) / len(src.verts)
        into = into.normalized() if into.length > 1e-9 else Vector((0, 0, 1))
        root = root_of(src.verts)
        mi = next((f.material_index for f in root[0].link_faces), 0)
        new = [src.verts.new(c + (q - c) * shrink + into * (sink * rad)) for q in rp]
        faces = bridge_uneven(src, root, new)
        faces.append(src.faces.new(new))
        for f in faces:
            f.material_index = mi
        bmesh.ops.recalc_face_normals(src, faces=src.faces)
        src.transform(part.matrix_world.inverted())
        commit(part, src); src.free()
        white(part)
        d = json.loads(part.get('attach', '{}'))
        d.pop('root_ring', None)
        part['attach'] = json.dumps(d)
        part['tris'] = sum(len(q.vertices) - 2 for q in part.data.polygons)
        rec = dict(kind='piece_attach', piece=part.name, cage_ring=len(rp), part_ring=len(root_pts),
                   new_faces=len(faces), reason=reason)
        if log is not None:
            log.attach.append(rec)
        say(f"attach {part.name}: {len(root_pts)}-ring root onto a {len(rp)}-ring limb end, +{len(faces)} faces"
            + (f' — {reason}' if reason else ''))
        return part
    assert is_bm, 'bridge_part: in stage 1 pass the ring as BMVerts (or the cap BMFace) of bm'
    if cap_face is None:
        cap_face = next((f for f in bm.faces if set(f.verts) == set(rv)), None)
    if cap_face is not None:
        bm.faces.remove(cap_face)
    shell, stack = set(), list(root_of(src.verts))           # the vertices of the shell that holds the root ring
    while stack:
        v = stack.pop()
        if v not in shell:
            shell.add(v)
            stack.extend(e.other_vert(v) for e in v.link_edges)
    vm = {v: bm.verts.new(v.co) for v in src.verts if v in shell}
    for f in src.faces:
        if f.verts[0] in shell:
            bm.faces.new([vm[v] for v in f.verts])
    bridge_uneven(bm, root_of(vm.values()), rv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    say(f"bridged a part into the base: {len(root_pts)}-ring root onto a {len(rp)}-ring limb end, +{len(vm)} verts")
    rest = None
    if len(shell) < len(src.verts):
        bmesh.ops.delete(src, geom=list(shell), context='VERTS')
        src.transform(part.matrix_world.inverted())
        commit(part, src)
        white(part)
        d = json.loads(part.get('attach', '{}'))
        d.pop('root_ring', None)
        part['attach'] = json.dumps(d)
        part.name = '_rest_' + part.name
        rest = part
    else:
        me = part.data
        bpy.data.objects.remove(part, do_unlink=True)
        bpy.data.meshes.remove(me)
    src.free()
    return rest


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
    hits, where = None, []
    if intersections:
        t = BVHTree.FromBMesh(bm)
        hits = 0
        for i, j in t.overlap(t):
            if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
                hits += 1
                if len(where) < 4:
                    where.append([round(x, 3) for x in (bm.faces[i].calc_center_median() + bm.faces[j].calc_center_median()) / 2])
    lo = Vector([min(v.co[k] for v in bm.verts) for k in range(3)])
    hi = Vector([max(v.co[k] for v in bm.verts) for k in range(3)])
    r = dict(verts=len(bm.verts), faces=len(bm.faces), tris=tris, quads=quads, ngons=ngons,
             components=comps, nonmanifold_edges=nonman, self_intersections=hits, intersections_at=where,
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
        self.attach = []            # stage 3: library parts bridged onto a cage ring (bridge_part)


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
VIEWS = {}                      # custom camera directions: name -> (direction to the camera, up)


def view(name, direction, up=(0, 0, 1)):
    """Register a camera direction (FROM the subject TO the camera) under a view name, usable
    wherever a view name is: shoot(views=[...]), camera(), masks(), closeups. Returns the name."""
    VIEWS[name] = (Vector(direction).normalized(), Vector(up).normalized())
    return name


def _view_dir(view):
    """Direction FROM the creature TO the camera, and the camera's up vector."""
    if view in VIEWS:
        return VIEWS[view]
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
    sh.light = 'FLAT' if mode == 'topo' else 'STUDIO'      # topo: flat face colours under the quad wire
    sh.show_cavity = mode in ('clay', 'wire', 'colour')
    sh.cavity_type = 'BOTH'
    sh.cavity_ridge_factor, sh.cavity_valley_factor = 0.6, 0.8
    # an outline round every separate object drew a dark 'sticker edge' round each piece in the
    # colour and tech renders (the art directors read it as glued-on); a game draws none
    sh.show_object_outline = mode in ('clay', 'wire', 'topo')
    sh.object_outline_color = (0.08, 0.08, 0.08)
    sh.show_shadows = mode == 'colour'
    sh.shadow_intensity = 0.35
    sh.color_type = {'colour': 'MATERIAL', 'tech': 'VERTEX', 'topo': 'VERTEX'}.get(mode, 'OBJECT')
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


_QUAD = {}                      # object name -> its mesh as modelled, kept by qa_step before the export triangulation


def _wire_dups(objs, frame):
    t = max(frame['size']) * 0.0032
    dups = []
    for o in objs:
        d = o.copy()                       # shares the mesh, keeps the modifier stack (mirror / armature)
        if o.name in _QUAD:                # a wire shows the modeller's faces (quads, n-gons), never the export triangles
            d.data = _QUAD[o.name]
        d.name = '_wire_' + o.name
        link(d)
        wm = d.modifiers.new('wf', 'WIREFRAME')
        wm.thickness = t
        wm.use_replace = True
        wm.use_even_offset = False         # even offset mitres sharp corners (a thumb tip) into long needle spikes
        d.color = (0.02, 0.02, 0.02, 1)
        dups.append(d)
    return dups


def shoot(outdir, tag, frame, views=ROUND_VIEWS, wire_views=WIRE_VIEWS, colour=False, res=512, objs=None, fill=None,
          modes_override=None, dirs=None):
    """Clay (flat grey) renders of every view, wire-over-clay of wire_views, and
    material-colour renders when colour=True. Files: <tag>_<view>_<mode>.png
    dirs: custom camera directions for this call, {name: direction} or {name: (direction, up)},
    direction = FROM the subject TO the camera, e.g. dirs={'under': (0.4, -0.6, -1)}. The names
    are then valid in views / wire_views; with views left at its default, the custom views are
    the ones rendered (view(name, direction) registers one for good).
    BMK_NORENDER=1 skips every picture (gates and QA still run): the regression sweep."""
    if dirs:
        for n, d in dirs.items():
            view(n, *((d,) if isinstance(d[0], (int, float)) else d))
        if views is ROUND_VIEWS:
            views = list(dirs)
            if wire_views is WIRE_VIEWS:
                wire_views = list(dirs)
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
            _QUAD[o.name] = o.data.copy()  # same vertices and weights: the wire renders keep showing these faces
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
        if tot.get('stretch', 0):
            say(f"WARN s{N} qa: {tot['stretch']} triangles stretch past {Q.STRETCH:g}x their rest length in a pose "
                f"(teal, worst {tot.get('stretch_max', 0):g}x): a stray weight, unless the part stretches by design (a tongue)")
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
        self.bridge_part = lambda part, ring, **kw: bridge_part(part, ring, log=self.log, **kw)

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
    ap.add_argument('--blockout', action='store_true', help='stage 1 plus the raw blockout sign-off packet')
    return ap.parse_args(argv)


def _json_safe(o):
    """json default: what META may hold that json cannot (a lambda, a numpy value, a Vector, a set) as a plain value."""
    if callable(o):
        return f"<callable {getattr(o, '__qualname__', type(o).__name__)}>"
    if hasattr(o, 'tolist'):
        return o.tolist()
    if isinstance(o, (set, frozenset)):
        return sorted(o, key=str)
    try:
        return list(o)
    except TypeError:
        return repr(o)


def _dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(obj, indent=1, default=_json_safe)                # serialise first: a failure leaves no half-written lock
    with open(path, 'w') as f:
        f.write(text)


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
    tri_lo, tri_hi = meta.get('stage1_tris', TOPO_LIMITS['template']['tris'] if meta.get('template') else (400, 1500))
    ok &= _gate('s1 one connected shell', r1['components'] == 1, f"{r1['components']} components")
    ok &= _gate('s1 closed (no open or non-manifold edges)', r1['nonmanifold_edges'] == 0, f"{r1['nonmanifold_edges']} edges")
    ok &= _gate('s1 no self-intersection', r1['self_intersections'] == 0, f"{r1['self_intersections']} face pairs" + (f" near {r1['intersections_at']}" if r1['self_intersections'] else ''))
    ok &= _gate('s1 triangles in budget', tri_lo <= r1['tris'] <= tri_hi, f"{r1['tris']} (budget {tri_lo}-{tri_hi})")
    ok &= _gate('s1 mirrored', has_mirror(body))
    cage = None
    if meta.get('cage') and N == 1:              # a cage build: joint loops, silhouette and proportion vs the sheet
        cok, cage = cage_gates(k, body, bpfile)
        ok &= cok
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
        if a.blockout and cage is not None:
            blockout_packet(k, body, cage, ok, r1)
        say('SUMMARY', json.dumps(dict(ok=bool(ok), stage=1, tris=r1['tris'], verts=r1['verts'])))
        return _finish(ok, t0)
    if stage2 is None:
        _gate(f'stage 2 is written before --stage {N}', False, 'this program stops at stage 1')
        return _finish(False, t0)

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
    cols = {}                 # the gate counts distinct COLOURS: a part slot sharing a palette colour is free
    for o in [body] + pieces:
        for m in o.data.materials:
            if m:
                cols.setdefault(tuple(round(c, 3) for c in m.diffuse_color[:3]), set()).add(m.name)
    ok &= _gate('s3 4-8 region colours', 4 <= len(cols) <= 8,
                f"{len(cols)}: {sorted('='.join(sorted(v)) for v in cols.values())}")
    tris = report(body, False)['tris'] + sum(report(p, False)['tris'] for p in pieces)
    t_lo, t_hi = meta.get('total_tris', (500, 3000))
    ok &= _gate('s3 total triangles in budget', t_lo <= tris <= t_hi, f'{tris} (budget {t_lo}-{t_hi})')
    _dump(k.path('stage3', 'stats.json'), dict(lock_assert=la3, colours=sorted(mats), colour_count=len(cols), tris=tris,
                                               attach=k.log.attach,
                                               pieces={p.name: report(p, False)['tris'] for p in pieces}))
    _dump(k.path('lock_assert.json'), dict(stage=3, **la3))
    if N == 3:
        vf = frame_of([body] + pieces, k.frame)
        if meta.get('cage'):
            topology_final(k, 3, body, pieces, vf)
        ok &= qa_step(k, 3, body, pieces, vf)
        shoot(k.path('stage3'), 's3', vf, colour=True)
        export_glb(k.path('stage3', 's3.glb'), [body] + pieces)
        say('SUMMARY', json.dumps(dict(ok=bool(ok), stage=3, tris=tris, colours=len(cols))))
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
    if meta.get('cage'):
        topology_final(k, 4, body, pieces, vf)
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


# =============================================================================
# 9. THE CAGE: stage-1 measures, the proxy rig and the blockout packet
# =============================================================================
# A program opts in with META['cage'] = True, META['J'] = J and META['plan'] (see cage_plan).
# IoU floors from the pilot bear (side 0.97, front 0.96, top 0.85): the side view is the proportion view and a cage
# that follows it clears 0.90 with room for a blocked-in ear or tail; the plan view of a generated sheet disagrees
# with its side view on where the paws are, so its floor sits lower. META['iou_floor'] = {'top': ...} overrides, logged.
CAGE_LIMITS = dict(joint_loops=2, quad_share=0.85, iou=dict(side=0.90, front=0.85, top=0.80), proportion_pct=10.0)


def planarize(faces, angle=8.0, iters=12, max_move=None):
    """Facet grouping: neighbouring faces whose normals lie within `angle` degrees of the group's first
    face become one group, and each group's vertices are projected onto its best-fit plane (repeated,
    because a vertex shared by two or three groups must settle on their crease). A lone non-planar quad
    is its own group, so its export diagonal stops showing under flat shading. Seam vertices stay on
    x = 0; max_move caps how far any vertex leaves where it started. Returns the groups (lists of faces)."""
    faces = list(faces)
    fs = set(faces)
    for f in faces:
        f.normal_update()
    cosang = math.cos(math.radians(angle))
    groups, seen = [], set()
    for f in faces:
        if f in seen:
            continue
        g, st = [f], [f]
        seen.add(f)
        while st:
            x = st.pop()
            for e in x.edges:
                for y in e.link_faces:
                    if y in fs and y not in seen and y.normal.dot(f.normal) >= cosang:
                        seen.add(y); g.append(y); st.append(y)
        groups.append(g)
    gv = [list({v for f in g for v in f.verts}) for g in groups]
    home = {v: v.co.copy() for vs in gv for v in vs}
    for _ in range(iters):
        for vs in gv:
            if len(vs) < 4:
                continue
            P = np.array([v.co[:] for v in vs])
            c = P.mean(axis=0)
            n = np.linalg.svd(P - c)[2][-1]
            for v in vs:
                q = np.array(v.co[:])
                v.co = Vector(q - np.dot(q - c, n) * n)
                if abs(home[v].x) < SEAM:
                    v.co.x = 0.0
                if max_move is not None:
                    d = v.co - home[v]
                    if d.length > max_move:
                        v.co = home[v] + d * (max_move / d.length)
    _fresh(list(home))
    return groups


def cage_plan(meta):
    """(J, plan). plan = META['plan']:
        spine   joint names from the root to the nose/head end: ['pelvis', 'spine', 'neck', 'head', 'snout']
        limbs   {'fore': ['shoulderL', 'elbowL', 'wristL', 'pawL'], 'hind': [...]}: root joint -> tip, left side
        extra   other chains (a tail): [['tail0', 'tail1']]
        neck, head, snout   the joint names the proportion table reads (defaults 'neck', 'head', 'snout')
        joints  where the >= 2 loops gate applies (default: every inner limb joint, and the neck)
    META['landmarks'] = {'eye': (x, y, z), 'mouth': (x, y, z)} (optional) lets topology() look for the face loops."""
    J = meta['J']
    plan = dict(meta.get('plan') or {})
    plan.setdefault('spine', [n for n in ('pelvis', 'spine', 'chest', 'neck', 'head', 'snout') if n in J])
    plan.setdefault('limbs', {})
    plan.setdefault('extra', [])
    for n in ('neck', 'head', 'snout'):
        plan.setdefault(n, n)
    plan.setdefault('landmarks', meta.get('landmarks') or {})          # optional {'eye': (x, y, z), 'mouth': (x, y, z)}
    if 'joints' not in plan:
        plan['joints'] = [n for c in plan['limbs'].values() for n in c[1:-1]]
        if plan['neck'] in plan['spine'][1:-1]:
            plan['joints'].append(plan['neck'])
    return J, plan


def _loops_at(bm, j, axis, band):
    """Closed edge loops that go round `axis` within `band` of the joint j (evaluated, mirrored mesh)."""
    ref = Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))
    u = (ref - axis * ref.dot(axis)).normalized()
    w = axis.cross(u)
    nb = {}
    for e in bm.edges:
        a, b = e.verts[0].co, e.verts[1].co
        d = b - a
        if d.length < 1e-9 or abs(d.dot(axis)) / d.length > 0.6:        # runs along the limb: not a ring edge
            continue
        if abs(((a + b) / 2 - j).dot(axis)) > 2 * band:
            continue
        nb.setdefault(e.verts[0], []).append(e.verts[1]); nb.setdefault(e.verts[1], []).append(e.verts[0])
    seen, n = set(), 0
    for v in nb:
        if v in seen:
            continue
        comp, st = [], [v]
        seen.add(v)
        while st:
            x = st.pop(); comp.append(x)
            for y in nb[x]:
                if y not in seen:
                    seen.add(y); st.append(y)
        if len(comp) < 4 or abs(sum((x.co - j).dot(axis) for x in comp) / len(comp)) > band:
            continue
        ang = sorted(math.atan2((x.co - j).dot(w), (x.co - j).dot(u)) for x in comp)
        gap = max(b - a for a, b in zip(ang, ang[1:] + [ang[0] + 2 * math.pi]))
        if gap < 0.75 * math.pi:                                         # it goes all the way round the bone
            n += 1
    return n


def _edge_loops_at(bm, j, axis, band):
    """Closed TOPOLOGICAL edge loops round `axis` within `band` of the joint j: from an edge, on through each
    valence-4 vertex to the edge opposite (no shared face). A steep wall between two rings (its radial edges are
    not lengthwise by angle) or one short slanted edge does not tie two such loops into one, as it does for
    _loops_at's connected components."""
    ref = Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))
    u = (ref - axis * ref.dot(axis)).normalized()
    w = axis.cross(u)
    seen, n = set(), 0
    for e0 in bm.edges:
        if e0 in seen or abs(((e0.verts[0].co + e0.verts[1].co) / 2 - j).dot(axis)) > 2 * band:
            continue
        loop, closed = [e0], False
        e, v = e0, e0.verts[1]
        while len(loop) < 400:
            if len(v.link_edges) != 4:
                break
            fs = set(e.link_faces)
            nx = [x for x in v.link_edges if x is not e and not (fs & set(x.link_faces))]
            if len(nx) != 1:
                break
            e = nx[0]
            if e is e0:
                closed = True
                break
            loop.append(e)
            v = e.other_vert(v)
        seen.update(loop)
        if not closed or len(loop) < 4:
            continue
        vs = {x for e in loop for x in e.verts}
        if abs(sum((x.co - j).dot(axis) for x in vs) / len(vs)) > band:
            continue
        ang = sorted(math.atan2((x.co - j).dot(w), (x.co - j).dot(u)) for x in vs)
        gap = max(b - a for a, b in zip(ang, ang[1:] + [ang[0] + 2 * math.pi]))
        if gap < 0.75 * math.pi:
            n += 1
    return n


def joint_loops(body, J, plan):
    """{joint: edge loops round the limb at that joint}. A loop counts when its ring of edges encircles
    the bone and sits within 0.4 of the shorter neighbouring bone of the joint. Two counts, the larger wins: rings
    as connected sets of non-lengthwise edges (_loops_at), and closed topological edge loops (_edge_loops_at)."""
    bm = evaluated_bm(body)
    chains = [plan['spine']] + list(plan['limbs'].values()) + list(plan['extra'])
    out = {}
    for name in plan['joints']:
        c = next((c for c in chains if name in c), None)
        if c is None:
            out[name] = 0
            continue
        i, j = c.index(name), Vector(J[name])
        ds = [d for d in ((j - Vector(J[c[i - 1]])) if i > 0 else None,
                          (Vector(J[c[i + 1]]) - j) if i + 1 < len(c) else None) if d is not None and d.length > 1e-6]
        axes = [d.normalized() for d in ds] + [sum((d.normalized() for d in ds), Vector()).normalized()]
        band = 0.4 * min(d.length for d in ds)
        out[name] = max(max(_loops_at(bm, j, ax, band), _edge_loops_at(bm, j, ax, band)) for ax in axes)   # rings square to either bone, or mitred
    bm.free()
    return out


def bp_frame(bp):
    """The orthographic frame of a blueprint (run.py draws with the same one)."""
    ys = [p[0] for p in bp['side']['outline']]; zs = [p[1] for p in bp['side']['outline']]
    xs = [abs(p[0]) for p in bp.get('front', {}).get('outline', [[0.3, 0]])]
    size = [2 * max(xs), max(ys) - min(ys), max(zs) - min(zs)]
    cen = [0.0, (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2]
    return dict(centre=cen, size=size, ortho=max(size) * 1.2)


class _Ortho:
    """World <-> pixel for one orthographic view of a blueprint frame (row 0 at the top)."""

    def __init__(self, view, frame, res):
        self.view, self.res, self.ppm = view, res, res / frame['ortho']
        cx, cy, cz = frame['centre']
        self.c = {'side': (cy, cz), 'front': (cx, cz), 'top': (-cx, -cy)}[view]

    def uv(self, p):
        return {'side': (p[1], p[2]), 'front': (p[0], p[2]), 'top': (-p[0], -p[1])}[self.view]

    def px(self, uv):
        return self.res / 2 + (uv[0] - self.c[0]) * self.ppm, self.res / 2 - (uv[1] - self.c[1]) * self.ppm


def ortho_masks(frame, res=512):
    """The scene's orthographic silhouettes in a blueprint frame: {'side', 'front', 'top': bool (res, res)}."""
    import tempfile, shutil
    _workbench('mask')
    tmp = tempfile.mkdtemp()
    out = {}
    for name, view in (('side', 'az090'), ('front', 'az000'), ('top', 'top')):
        camera(frame, view, ortho=True)
        p = os.path.join(tmp, f'o_{name}.png')
        _render(p, res)
        img = bpy.data.images.load(p)
        a = np.empty(res * res * 4, dtype=np.float32)
        img.pixels.foreach_get(a)
        out[name] = a.reshape(res, res, 4)[::-1, :, 3] > 0.5
        bpy.data.images.remove(img)
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def ref_masks(bp, frame, res=512):
    """The blueprint's outlines (traced from the reference sheet) filled, in the same frame and layout."""
    out = {}
    for view in ('side', 'front', 'top'):
        part = bp.get(view)
        if not part:
            continue
        pts = [list(p) for p in part['outline']]
        if view != 'side' and all(p[0] >= -1e-9 for p in pts):          # a half outline: mirror it
            pts = pts + [[-p[0], p[1]] for p in reversed(pts)]
        o = _Ortho(view, frame, res)
        P = [o.px((p[0], p[1]) if view != 'top' else (-p[0], -p[1])) for p in pts]
        M = np.zeros((res, res), bool)
        n = len(P)
        for r in range(res):
            y = r + 0.5
            xs = []
            for i in range(n):
                (x0, y0), (x1, y1) = P[i], P[(i + 1) % n]
                if (y0 <= y) != (y1 <= y):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                M[r, max(0, int(math.ceil(a - 0.5))):max(0, int(math.floor(b - 0.5)) + 1)] = True
        out[view] = M
    return out


def _run_len(M, o, uv, duv, sub=False):
    """Length (metres) of the mask's run through the world point uv along the unit direction duv. sub: the run
    is read on the two pixel lines either side of the point and interpolated between their centres (a nearest-pixel
    row sits up to half a pixel, about 0.5 cm on a 2 m creature, off the row the mesh is measured at)."""
    res = o.res
    x0, y0 = o.px(uv)
    if sub:
        nx, ny = -duv[1], duv[0]                                        # across the run, in world (u, v)
        t = (x0 * nx - y0 * ny) - 0.5                                   # pixel-centre coordinate across the run
        f = t - math.floor(t)
        back = lambda k: (uv[0] + nx * k / o.ppm, uv[1] + ny * k / o.ppm)
        a, b = _run_len(M, o, back(-f), duv), _run_len(M, o, back(1 - f), duv)
        return (1 - f) * a + f * b if a and b else (a or b)
    dx, dy = duv[0], -duv[1]
    inside = lambda s: (0 <= int(y0 + dy * s) < res and 0 <= int(x0 + dx * s) < res
                        and bool(M[int(y0 + dy * s), int(x0 + dx * s)]))
    s0 = next((s for k in range(int(0.06 * res)) for s in (k * 0.5, -k * 0.5) if inside(s)), None)
    if s0 is None:
        return 0.0
    a = b = s0
    while inside(a - 0.5):
        a -= 0.5
    while inside(b + 0.5):
        b += 0.5
    return (b - a + 0.5) / o.ppm


def _measures(M, J, plan, frame, res):
    """The proportion ratios of one set of orthographic masks. Joints say WHERE to measure; the masks
    say how big the thing is there, so the same code reads the model and the sheet."""
    sd, o = M['side'], _Ortho('side', frame, res)
    rows, cols = np.nonzero(sd)
    H = (rows.max() - rows.min() + 1) / o.ppm
    L = (cols.max() - cols.min() + 1) / o.ppm
    zg = o.c[1] + (res / 2 - (rows.max() + 1)) / o.ppm                  # the ground under the figure
    out = {'body length / height': L / H}
    hj, nj = Vector(J[plan['head']]), Vector(J[plan['neck']])
    sj = Vector(J[plan['snout']]) if plan['snout'] in J else None
    if sj is not None and (sj - hj).length > 1e-6:                      # skull height, square to the muzzle line
        ax = Vector((sj.y - hj.y, sj.z - hj.z)).normalized()
        head = _run_len(sd, o, (hj.y, hj.z), (-ax.y, ax.x))
    else:                                                               # an upright head: its top down to the neck joint
        cx = int(o.px((hj.y, hj.z))[0])
        col = np.nonzero(sd[:, min(max(cx, 0), res - 1)])[0]
        head = (o.c[1] + (res / 2 - col.min()) / o.ppm - nj.z) if len(col) else 0.0
    out['head height / body height'] = head / H
    limbs = plan['limbs']
    roots = [J[c[0]][1] for c in limbs.values()]
    if roots and max(roots) - min(roots) > 0.15 * L:                    # quadruped: the belly's clearance between the legs
        ys = sorted(J[n][1] for c in limbs.values() for n in c)
        fore = [J[n][1] for c in limbs.values() if J[c[0]][1] == min(roots) for n in c]
        hind = [J[n][1] for c in limbs.values() if J[c[0]][1] == max(roots) for n in c]
        ym = (max(fore) + min(hind)) / 2
        cx = int(o.px((ym, 0))[0])
        col = np.nonzero(sd[:, min(max(cx, 0), res - 1)])[0]
        leg = (o.c[1] + (res / 2 - (col.max() + 1)) / o.ppm - zg) if len(col) else 0.0
    elif 'front' in M:                                                  # biped: the crotch height on the centre line
        of = _Ortho('front', frame, res)
        col = np.nonzero(M['front'][:, int(of.px((0, 0))[0])])[0]
        leg = (of.c[1] + (res / 2 - (col.max() + 1)) / of.ppm - zg) if len(col) else 0.0
    else:
        leg = 0.0
    out['leg length / body height'] = leg / H
    mid = (hj + nj) / 2
    if abs(hj.z - nj.z) > abs(hj.y - nj.y) and 'front' in M:            # upright neck: widths in the front view
        of = _Ortho('front', frame, res)
        nw, hw = _run_len(M['front'], of, (0, mid.z), (1, 0), True), _run_len(M['front'], of, (0, hj.z), (1, 0), True)
    elif 'top' in M:                                                    # level neck: widths in the plan view
        ot = _Ortho('top', frame, res)
        nw, hw = _run_len(M['top'], ot, (0, -mid.y), (1, 0), True), _run_len(M['top'], ot, (0, -hj.y), (1, 0), True)
    else:
        nw = hw = 0.0
    out['neck width / head width'] = nw / hw if hw else 0.0
    for name, c in limbs.items():
        a, b = (Vector(J[c[1]]), Vector(J[c[2]])) if len(c) > 2 else (Vector(J[c[0]]), Vector(J[c[1]]))
        m = (a + b) / 2
        ax = Vector((b.y - a.y, b.z - a.z))
        ax = ax.normalized() if ax.length > 1e-6 else Vector((0, -1))
        thick = _run_len(sd, o, (m.y, m.z), (-ax.y, ax.x))
        length = sum((Vector(J[q]) - Vector(J[p])).length for p, q in zip(c, c[1:]))
        out[f'{name} limb thickness / length'] = thick / length if length else 0.0
    return out


def proportions(body, J, blueprint, plan=None, res=512, masks_=None):
    """The proportion table: {ratio name: {'model', 'sheet', 'diff_pct'}} for head height / body height,
    leg length / body height (the under-body clearance), neck width / head width, each limb's
    thickness / length, and body length / height. Both columns are measured the same way from
    orthographic silhouettes in the blueprint's frame: the model's renders and the blueprint's outlines
    (the reference sheet's masks, traced by refs.py). blueprint: a path or the loaded dict."""
    bp = json.load(open(blueprint)) if isinstance(blueprint, str) else blueprint
    J, plan = cage_plan(dict(J=J, plan=plan))
    fr = bp_frame(bp)
    mm, rm = masks_ or (ortho_masks(fr, res), ref_masks(bp, fr, res))
    a, b = _measures(mm, J, plan, fr, res), _measures(rm, J, plan, fr, res)
    return {n: dict(model=round(a[n], 3), sheet=round(b[n], 3),
                    diff_pct=round(100.0 * (a[n] - b[n]) / b[n], 1) if b[n] else 0.0) for n in a}


def _later(meta, J):
    """META['later'] = {name: [joint names] or dict(chain=[joint names], radius=metres)}: thin parts the stage-1
    cage leaves out because they come later as library / extra pieces (big ears, a tail fan, horns).
    -> [(name, chain, radius)]; the default radius is 0.35 x the chain's length."""
    out = []
    for name, d in (meta.get('later') or {}).items():
        c = list(d['chain'] if isinstance(d, dict) else d)
        if len(c) < 2 or any(n not in J for n in c):
            say(f"WARN META['later'][{name!r}]: needs two or more joint names of J; ignored")
            continue
        L = sum((Vector(J[b]) - Vector(J[a])).length for a, b in zip(c, c[1:]))
        out.append((name, c, float(d['radius']) if isinstance(d, dict) and d.get('radius') else 0.35 * L))
    return out


def later_masks(meta, J, frame, res=512):
    """{view: bool (res, res)}: the pixels within `radius` of the META['later'] chains (and their mirror), in
    the blueprint frame; {} when META names none. The stage-1 silhouette IoU is measured outside them, on the
    model and on the reference alike, so a declared stage-3 part is neither missed nor rewarded in stage 1."""
    L = _later(meta, J)
    if not L:
        return {}
    out = {}
    R, C = np.mgrid[0:res, 0:res]
    for view in ('side', 'front', 'top'):
        o = _Ortho(view, frame, res)
        X = np.zeros((res, res), bool)
        for _, c, r in L:
            for sx in (1.0, -1.0):
                P = [o.px(o.uv((sx * J[n][0], J[n][1], J[n][2]))) for n in c]
                for (x0, y0), (x1, y1) in zip(P, P[1:]):
                    ex, ey = x1 - x0, y1 - y0
                    t = np.clip(((C + 0.5 - x0) * ex + (R + 0.5 - y0) * ey) / max(1e-9, ex * ex + ey * ey), 0, 1)
                    X |= np.hypot(C + 0.5 - x0 - t * ex, R + 0.5 - y0 - t * ey) <= r * o.ppm
        out[view] = X
    return out


def cage_gates(k, body, bpfile):
    """The stage-1 gates of a cage build (META['cage']). Returns (ok, info); info goes to stage1/cage.json."""
    J, plan = cage_plan(k.meta)
    ok = True
    loops = joint_loops(body, J, plan)
    low = {n: c for n, c in loops.items() if c < CAGE_LIMITS['joint_loops']}
    ok &= _gate(f"s1 cage: >= {CAGE_LIMITS['joint_loops']} edge loops at every joint", not low,
                (f'low: {low}; ' if low else '') + ', '.join(f'{n} {c}' for n, c in loops.items()))
    me = body.data
    q = sum(1 for p in me.polygons if len(p.vertices) == 4) / max(1, len(me.polygons))
    say(('' if q >= CAGE_LIMITS['quad_share'] else 'WARN ') + f's1 cage: quad share {100 * q:.0f}% of {len(me.polygons)} '
        f"half faces (report; a designed cage sits above {100 * CAGE_LIMITS['quad_share']:.0f}%)")
    info = dict(loops=loops, quad_share=round(q, 3), limits=CAGE_LIMITS)
    tm = getattr(k, 'template', None)                                   # a template build (kit/template.py): gates on its named sets
    k.cage_topo = T = topology(body, J, plan, tm)
    for c in T['checks']:                                               # gates block the lock; warnings are printed
        if c['kind'] == 'gate':
            ok &= _gate('s1 topology: ' + c['name'], c['ok'], c['detail'])
        elif not c['ok']:
            say(f"WARN s1 topology: {c['name']} — {c['detail']}")
    if tm is not None:
        lim = TOPO_LIMITS['template']['rom_fold_pct']
        info['rom_fold_pct'] = rf = rom_fold(body, J, plan)
        c = dict(kind='gate', name=f'template: range of motion folds at most {lim:g}% of the area in every pose',
                 ok=all(x <= lim for x in rf.values()), detail=', '.join(f'{n} {x:g}%' for n, x in rf.items()))
        T['checks'].append(c)
        ok &= _gate('s1 topology: ' + c['name'], c['ok'], c['detail'])
    info['topology_checks'] = T['checks']
    _dump(k.path('stage1', 'topology.json'), T)
    k.cage_masks = None
    if os.path.exists(bpfile):
        bp = json.load(open(bpfile))
        fr = bp_frame(bp)
        mm, rm = ortho_masks(fr), ref_masks(bp, fr)
        X = later_masks(k.meta, J, fr, mm['side'].shape[0])               # META['later']: thin parts that come as stage-3 pieces
        ious = {v: round(iou(mm[v] & ~X[v], rm[v] & ~X[v]) if X else iou(mm[v], rm[v]), 3) for v in rm}
        if X:
            say('s1 cage: silhouette IoU measured without the parts counted later: ' + ', '.join(
                f"{n} ({' > '.join(c)})" for n, c, _ in _later(k.meta, J)))
        floor = dict(CAGE_LIMITS['iou'], **k.meta.get('iou_floor', {}))
        low = {v: x for v, x in ious.items() if x < floor[v]}
        ok &= _gate('s1 cage: silhouette IoU vs the reference views (floor side %g, front %g, top %g)'
                    % (floor['side'], floor['front'], floor['top']), not low,
                    (f'low: {low}; ' if low else '') + ', '.join(f'{v} {x}' for v, x in ious.items()))
        prop = proportions(body, J, bp, plan, masks_=(mm, rm))
        intended = k.meta.get('intended', {})
        lim = CAGE_LIMITS['proportion_pct']
        off = {n: r['diff_pct'] for n, r in prop.items() if abs(r['diff_pct']) > lim and n not in intended}
        ok &= _gate(f"s1 cage: proportions within {lim:g}% of the sheet (or listed in META['intended'] with a reason)",
                    not off, f'off: {off}' if off else f"max {max(abs(r['diff_pct']) for r in prop.values()):g}%")
        for n, r in prop.items():
            say(f"  {n}: model {r['model']:.3f}  sheet {r['sheet']:.3f}  {r['diff_pct']:+.1f}%"
                + (f"  (intended: {intended[n]})" if n in intended and abs(r['diff_pct']) > lim else ''))
        info.update(iou=ious, iou_floor=floor, proportions=prop, intended=intended, frame=fr,
                    later=[dict(name=n, chain=c, radius=round(r, 4)) for n, c, r in _later(k.meta, J)])
        k.cage_masks = (mm, rm)
    else:
        ok &= _gate('s1 cage: blueprint.json present (the silhouette and proportion target)', False)
    # the medium forms: head, arms and legs against the reference, station by station
    k.cage_profiles = PP = part_profiles(body, J, plan, k.dir, getattr(k, 'guide', None),
                                         masks_=(k.cage_masks[0], info['frame']) if k.cage_masks else None)
    intended = k.meta.get('intended', {})
    for c in PP['checks']:
        why = intended.get(f"{c['part']} profile")                      # META['intended']['head profile'] = reason
        if why and not c['ok']:
            c['intended'] = why                                         # profiles.json and 5_profiles.jpg show the waiver
        if c['kind'] == 'gate':
            ok &= _gate('s1 form: ' + c['name'], c['ok'] or bool(why), c['detail'] + (f' (intended: {why})' if why and not c['ok'] else ''))
        elif not c['ok']:
            say(f"WARN s1 form: {c['name']} — {c['detail']}")
    info['profile_checks'] = PP['checks']
    _dump(k.path('stage1', 'profiles.json'), PP)
    _dump(k.path('stage1', 'cage.json'), info)
    return ok, info


def rom_fold(body, J, plan):
    """{pose: % of the surface that folds over or collapses} for the three range-of-motion poses (rom_poses), on a
    skinned COPY of the body with a proxy rig: the body itself keeps its mirror and stays unrigged."""
    import techqa as Q
    cp = body.copy()
    cp.data = body.data.copy()
    cp.name = 'body_rom'
    link(cp)
    rig = proxy_rig(J, plan, name='proxy_rom')
    skin(cp, rig)
    size = frame_of([cp])['size']
    out = {}
    for pn, keys in rom_poses(J, plan).items():
        act = clip(rig, 'romfold_' + pn, {1: keys, 2: keys})
        counts, flags, tris = Q.measure(cp, [], size, rig, {pn: act})
        tot, _ = Q.summary(counts, tris)
        out[pn] = round(100.0 * tot.get('flip_area', 0) / max(1e-12, tot.get('area', 0)), 2)
    bpy.data.objects.remove(rig, do_unlink=True)
    bpy.data.objects.remove(cp, do_unlink=True)
    return out


def proxy_rig(J, plan, name='proxy'):
    """A quick armature straight from J: one bone per joint-to-joint step of the spine, limb and extra
    chains, each named after the joint it turns about ('elbowL' -> 'elbow.L', mirrored to '.R'). Limb
    and extra chains hang off the nearest spine bone. For the blockout's range-of-motion poses."""
    bones = []
    bn = lambda a: (a[:-1] + '.L') if a.endswith('L') and J[a][0] > SEAM else a

    def chain(c, parent):
        for a, b in zip(c, c[1:]):
            bones.append((bn(a), J[a], J[b], parent))
            parent = bn(a)

    chain(plan['spine'], None)
    trunk = list(bones)
    for c in list(plan['limbs'].values()) + list(plan['extra']):
        p = Vector(J[c[0]])
        par = min(trunk, key=lambda b: _seg_dist(p, Vector(b[1]), Vector(b[2])))[0] if trunk else None
        chain(c, par)
    return armature(bones, name, roll='auto')


def rom_poses(J, plan, bend=80.0, swing=60.0):
    """Three range-of-motion poses for the proxy rig: {pose: {bone: (rx, 0, 0)}}.
      fold    every inner limb joint bent `bend` degrees, alternating down the limb (elbow, wrist, knee, hock)
      swing   every limb swung `swing` degrees from its root (fore limbs forward, hind limbs back), the
              first inner joint bent back so the lower limb hangs
      crouch  roots swung the other way, inner joints at 90, neck and head pitched down"""
    bn = lambda a: (a[:-1] + '.L') if a.endswith('L') and J[a][0] > SEAM else a
    fold, sw, crouch = {}, {}, {}
    for name, c in plan['limbs'].items():
        s = -1.0 if name.lower().startswith(('hind', 'leg', 'rear', 'back')) else 1.0
        for i, jn in enumerate(c[1:-1]):
            sg = s * (1 if i % 2 == 0 else -1)
            fold[bn(jn)] = (sg * bend, 0, 0)
            crouch[bn(jn)] = (sg * 90.0, 0, 0)
        sw[bn(c[0])] = (s * swing, 0, 0)
        crouch[bn(c[0])] = (-s * 0.5 * swing, 0, 0)
        if len(c) > 2:
            sw[bn(c[1])] = (-s * swing, 0, 0)
    sp = plan['spine']
    if plan['neck'] in sp[:-1]:
        crouch[plan['neck']] = (-35.0, 0, 0)
        if plan['head'] in sp[:-1]:
            crouch[plan['head']] = (-25.0, 0, 0)
    out = {}
    for pn, keys in (('fold', fold), ('swing', sw), ('crouch', crouch)):
        out[pn] = dict(keys, **{b[:-2] + '.R': r for b, r in keys.items() if b.endswith('.L')})
    return out


def blockout_packet(k, body, info, ok, report_):
    """The raw pictures and numbers of the blockout sign-off (run.py --blockout composes blockout/):
    grey views, wire views, the silhouettes, and three range-of-motion poses on a proxy rig."""
    import techqa as Q
    raw = os.path.join(k.a.scratch, 'blockout')
    os.makedirs(raw, exist_ok=True)
    J, plan = cage_plan(k.meta)
    shoot(raw, 'grey', k.frame, views=['hero', 'az090', 'az000', 'back34'], wire_views=['hero', 'back34'], res=768)
    fr = info.get('frame')
    if fr and not os.environ.get('BMK_NORENDER'):
        mm, rm = k.cage_masks
        np.savez_compressed(os.path.join(raw, 'sil.npz'), **{f'model_{v}': m for v, m in mm.items()},
                            **{f'ref_{v}': m for v, m in rm.items()})
        _workbench('wire')
        body.color = (0.78, 0.78, 0.76, 1)
        dups = _wire_dups([body], k.frame)
        camera(fr, 'az090', ortho=True)
        _render(os.path.join(raw, 'wire_side_ortho.png'), 1024)
        for d in dups:
            bpy.data.objects.remove(d, do_unlink=True)
        _workbench('clay')                                              # the model's side of 5_profiles.jpg
        camera(fr, 'az090', ortho=True)
        _render(os.path.join(raw, 'grey_side_ortho.png'), 1024)
    g = getattr(k, 'guide', None)
    if g is not None and getattr(k, 'cage_profiles', None):            # the base form on its own: 0_guide.jpg, 'guide' block
        guide_views(raw, g, k.frame)
        if not os.environ.get('BMK_NORENDER'):
            k.cage_profiles['guide'] = guide_profiles(g, J, plan, k.dir, fr)
            body.color = (0.78, 0.78, 0.76, 1)
    if getattr(k, 'cage_profiles', None):
        _dump(k.path('blockout', 'profiles.json'), k.cage_profiles)
    T = getattr(k, 'cage_topo', None) or topology(body, J, plan)
    _dump(k.path('blockout', 'topology.json'), T)
    topology_shots(raw, body, T, k.frame, J, plan)
    rig = proxy_rig(J, plan)
    skin(body, rig)
    poses = rom_poses(J, plan)
    acts = {pn: clip(rig, 'rom_' + pn, {1: keys, 2: keys}) for pn, keys in poses.items()}
    counts, flags, tris = Q.measure(body, [], k.frame['size'], rig, acts)
    tot, ntris = Q.summary(counts, tris)
    rom = dict(flip_tris=tot.get('flip', 0), triangles=ntris,
               flip_area_pct=round(100.0 * tot.get('flip_area', 0) / max(1e-12, tot.get('area', 0)), 2),
               stretch_tris=tot.get('stretch', 0))
    say(f"blockout rom: {rom['flip_tris']} of {ntris} triangles fold over or collapse in the three poses "
        f"({rom['flip_area_pct']}% of area), {rom['stretch_tris']} stretch")
    for pn, act in acts.items():
        pose(rig, act, 1)
        bpy.context.view_layer.update()
        shoot(raw, f'rom_{pn}', frame_of([body], k.frame), views=['hero', 'az090'], wire_views=['hero', 'az090'],
              res=640, objs=[body])
    rig.animation_data.action = None
    rest(rig)
    _dump(k.path('blockout', 'blockout.json'),
          dict(creature=k.meta.get('creature'), gates_ok=bool(ok), tris=report_['tris'], verts=report_['verts'],
               joints={n: list(J[n]) for n in plan['joints']}, poses=poses, rom=rom,
               **{a: b for a, b in info.items() if a != 'limits'}, limits=CAGE_LIMITS))


# =============================================================================
# 10. TOPOLOGY: the cage's own faces (quads and n-gons as modelled), measured before any triangulation
# =============================================================================
# Gates (block the stage-1 lock of a cage build) and warnings (printed, drawn in the table). The numbers come from
# what hand-made low-poly cages look like (near-square quads of one size per region, 2-3 loops per joint, poles on
# the flat of a form) and from what the three c2 cages measured (blockout/topology.json).
TOPO_LIMITS = dict(
    edge_ratio=4.0,          # gate: edge length p90 / p10 inside any one region
    aspect5_pct=5.0,         # gate: % of faces longer than 5:1
    joint_poles=0,           # gate: poles (valence != 4) inside a joint band
    root_loop=True,          # gate: a closed loop round every limb root that passes over the root joint
    fans=0, caps=0,          # gate: valence >= 6 vertices / non-quad faces where a limb joins the torso
    ring_stacks=0,           # gate: runs of 3+ parallel rings closer than stack_gap x the limb width, outside a joint band
    stack_gap=0.5,
    aspect3_pct=20.0,        # warn: % of faces longer than 3:1
    density=(0.5, 2.0),      # warn: a region's triangle share / its surface-area share
    body_edge_ratio=6.0,     # warn: edge length p90 / p10 over the whole body
    flow=0.3,                # warn: share of a limb's lengthwise edges that run on into the torso
    piece_share=0.5,         # warn (stage 3/4): pieces take more than this share of the triangles
    # a template build (kit/template.py, META['template']): gates read off the template's named sets, on top of the above
    template=dict(
        socket_verts=8,          # a limb's socket loop: this many vertices, every one of valence 4
        socket_flow=0.9,         # share of the limb's lengthwise lines that run on through the socket into the trunk
        pole_share=0.15,         # poles (valence != 4) / vertices; their count is the template signature's, no more
        warp_deg=12.0,           # a quad is non-planar when its two triangles (on the rendered diagonal) differ by more
        warp_pct=5.0,            # non-planar quads, % of the faces outside the hinges
        hinge_ratio=(0.4, 0.7),  # a 3-ring hinge: ring spacing on the flexion side / on the extension side
        edge_ratio=2.5,          # edge length p90 / p10 inside any one region
        density=(0.7, 1.6),      # a region's triangle share / its surface-area share
        corner_share=0.6,        # share of section-placed ring vertices that sit on a corner of the guide's section
        corner_tol=0.02,         # ... within this x the ring's size
        rom_fold_pct=1.0,        # folded area, % of the surface, in each range-of-motion pose
        tris=(1200, 2200),       # stage-1 triangles
    ),
)
TOPO_COL = dict(quad=(200, 200, 196), tri=(245, 185, 110), ngon=(185, 150, 235), piece=(170, 182, 198),
                pole3=(20, 110, 255), pole5=(255, 110, 0), pole6=(215, 0, 190),
                dense=(30, 70, 220), sparse=(220, 40, 30), a3=(240, 220, 60), a5=(215, 25, 25))


def _spread(a, nd=4):
    a = np.asarray(a, float)
    if not len(a):
        return dict(p10=0.0, p50=0.0, p90=0.0, ratio=0.0)
    p10, p50, p90 = (float(np.percentile(a, q)) for q in (10, 50, 90))
    return dict(p10=round(p10, nd), p50=round(p50, nd), p90=round(p90, nd), ratio=round(p90 / p10, 2) if p10 > 0 else 0.0)


def _face_loops(bm):
    """Closed quad strips (face loops): [(face indices, rail edge indices)]. A strip leaves a quad by the
    edge opposite the one it entered by; the rails are the edges it runs along."""
    seen, out = set(), []
    for f in bm.faces:
        if len(f.verts) != 4:
            continue
        for k in (0, 1):
            if (f.index, k) in seen:
                continue
            strip, rails, closed = [], set(), False
            cur, ein = f, f.edges[k]
            while len(strip) <= len(bm.faces):
                es = list(cur.edges)
                i = es.index(ein)
                seen.add((cur.index, i % 2))
                strip.append(cur.index)
                rails.update((es[(i + 1) % 4].index, es[(i + 3) % 4].index))
                eout = es[(i + 2) % 4]
                nx = [g for g in eout.link_faces if g is not cur]
                if len(nx) != 1 or len(nx[0].verts) != 4:
                    break
                cur, ein = nx[0], eout
                if cur is f and ein is f.edges[k]:
                    closed = True
                    break
            if closed and len(set(strip)) == len(strip):
                out.append((strip, rails))
    return out


def _edge_groups(bm, eidx):
    """Edge indices grouped by shared vertices (the two rails of a strip come apart)."""
    byv = {}
    for ei in eidx:
        for v in bm.edges[ei].verts:
            byv.setdefault(v.index, []).append(ei)
    left, out = set(eidx), []
    while left:
        st = [left.pop()]
        g = set(st)
        while st:
            for v in bm.edges[st.pop()].verts:
                for ej in byv[v.index]:
                    if ej in left:
                        left.discard(ej); g.add(ej); st.append(ej)
        out.append(g)
    return out


def _topo_chains(J, plan):
    """[(region name, joint names)]: the head (from the neck joint on), each limb, each extra chain."""
    sp = plan['spine']
    i = sp.index(plan['neck']) if plan['neck'] in sp[:-1] else max(0, len(sp) - 2)
    out = [('head', sp[i:])]
    out += [(n, list(c)) for n, c in plan['limbs'].items()]
    for c in plan['extra']:
        n = ''.join(ch for ch in c[0] if not ch.isdigit())
        n = n[:-1] if n.endswith('L') and len(n) > 1 else n
        while n in [x[0] for x in out] + ['torso']:
            n += '_'
        out.append((n, list(c)))
    return out


def _template_checks(bm, T, tm, val, add):
    """The gates of a template build, on the template's named vertices (found in the evaluated mesh by position)."""
    from mathutils.kdtree import KDTree
    L = TOPO_LIMITS['template']
    half = [v for v in bm.verts if v.co.x > -1e-5]
    kd = KDTree(len(half))
    for i, v in enumerate(half):
        kd.insert(v.co, i)
    kd.balance()

    def at(i):
        co, j, d = kd.find(tm.co[tm.names[i]])
        return half[j] if d < 1e-4 else None

    linked = lambda a, b: a is not None and b is not None and any(e.other_vert(a) is b for e in a.link_edges)
    info = dict(kind=tm.kind, counts=tm.counts, sockets={}, hinges={})
    for limb in tm.limbs:
        so, bd = [at(i) for i in tm.loops[limb + '.socket']], [at(i) for i in tm.loops[limb + '.border']]
        ring = {v for v in so + bd if v is not None}
        closed = all(linked(a, b) for a, b in zip(so, so[1:] + so[:1]))
        flow = sum(1 for a, b in zip(so, bd) if linked(a, b) and any(e.other_vert(b) not in ring for e in b.link_edges))
        info['sockets'][limb] = dict(verts=sum(v is not None for v in so), closed=closed, valence=[val[v.index] if v else 0 for v in so],
                                     flow=round(flow / max(1, len(so)), 2))
    sk = info['sockets']
    add('gate', f"template: every limb socket is a closed loop of {L['socket_verts']} vertices, all valence 4, flow >= {L['socket_flow']:g}",
        all(r['verts'] == L['socket_verts'] and r['closed'] and set(r['valence']) == {4} and r['flow'] >= L['socket_flow'] for r in sk.values()),
        ', '.join(f"{n} {r['verts']} verts, valence {sorted(set(r['valence']))}, flow {r['flow']:g}" for n, r in sk.items()))
    npoles = sum(1 for x in val if x != 4)
    info['pole_share'] = round(npoles / max(1, len(val)), 3)
    tv = tm.valence()
    sig_poles = sum((1 if i in tm.seam else 2) for i, x in enumerate(tv) if x != 4)
    info['poles'], info['signature_poles'] = npoles, sig_poles
    add('gate', f"template: poles at most {L['pole_share']:g} x the vertices, and exactly the template signature's count",
        info['pole_share'] <= L['pole_share'] and npoles == sig_poles, f"{npoles} of {len(val)} = {info['pole_share']:g} (signature: {sig_poles})")
    from template import quad_warp
    hp_ = [tm.co[tm.names[i]] for keys in tm.joint_rings.values() for key in keys if key[0] in tm.limbs for i in tm.rings[key]]
    hk = KDTree(max(1, len(hp_)))
    for i, c_ in enumerate(hp_):
        hk.insert(c_, i)
    hk.balance()
    is_h = lambda v: bool(hp_) and hk.find((abs(v.co.x), v.co.y, v.co.z))[2] < 1e-4
    out = [f for f in bm.faces if len(f.verts) == 4 and not all(is_h(v) for v in f.verts)]
    bad = sum(1 for f in out if quad_warp(*[v.co for v in f.verts]) > L['warp_deg'])
    info['warp_pct'] = round(100.0 * bad / max(1, len(out)), 2)
    add('gate', f"template: non-planar quads (warp over {L['warp_deg']:g} degrees) at most {L['warp_pct']:g}% of the faces outside the hinges",
        info['warp_pct'] <= L['warp_pct'], f"{info['warp_pct']:g}% ({bad} of {len(out)})")
    jp = {jn: sum(1 for key in keys for i in tm.rings[key] if at(i) is not None and val[at(i).index] != 4) for jn, keys in tm.joint_rings.items()}
    info['joint_ring_poles'] = jp
    add('gate', 'template: no pole on a joint ring (the hinge rings of every limb joint, the neck rings)', not any(jp.values()),
        ', '.join(f'{n} {x}' for n, x in jp.items()))
    for jn, h in tm.hinges.items():
        R3 = [[at(i) for i in tm.rings[(h['limb'], r)]] for r in h['rings']]
        gap = lambda ks: float(np.mean([(R3[q][k_].co - R3[q + 1][k_].co).length for q in range(len(R3) - 1) for k_ in ks]))
        f, e = gap(h['flex']), gap(h['ext'])
        info['hinges'][jn] = dict(rings=len(R3), flex=round(f, 4), ext=round(e, 4), ratio=round(f / e, 2) if e else 0.0)
    lo, hi = L['hinge_ratio']
    add('gate', f'template: 3 converging rings at every hinge, flexion / extension spacing {lo:g}-{hi:g}',
        all(r['rings'] == 3 and lo <= r['ratio'] <= hi for r in info['hinges'].values()),
        ', '.join(f"{n} {r['ratio']:g}" for n, r in info['hinges'].items()))
    er = {n: r['edge']['ratio'] for n, r in T['regions'].items()}
    add('gate', f"template: edge length p90/p10 <= {L['edge_ratio']:g} in every region", all(x <= L['edge_ratio'] for x in er.values()),
        ', '.join(f'{n} {x:g}' for n, x in er.items()))
    lo, hi = L['density']
    dn = {n: r['density'] for n, r in T['regions'].items()}
    add('gate', f'template: density between regions {lo:g}-{hi:g} (triangle share / area share)', all(lo <= x <= hi for x in dn.values()),
        ', '.join(f'{n} {x:g}' for n, x in dn.items()))
    on = tot = 0
    by = {}
    for key, c in tm.corners.items():
        C = [Vector(q) for q in c['corners']]
        for nm in c['names']:
            hit = min((Vector(getattr(tm, 'co0', tm.co)[nm]) - q).length for q in C) <= L['corner_tol'] * c['width']
            on += hit; tot += 1
            b = by.setdefault(str(key[0]), [0, 0]); b[0] += hit; b[1] += 1
    info['corner_share'] = round(on / max(1, tot), 3)
    info['corner_share_by_part'] = {n: round(a / max(1, b), 2) for n, (a, b) in by.items()}
    add('gate', f"template: section corner share >= {L['corner_share']:g} (ring vertices on a corner of the guide's section, as the sections placed them)",
        info['corner_share'] >= L['corner_share'], f"{info['corner_share']:g} of {tot} ({', '.join(f'{n} {x:g}' for n, x in info['corner_share_by_part'].items())})")
    lo, hi = L['tris']
    add('gate', f'template: stage-1 triangles {lo}-{hi}', lo <= T['tris'] <= hi, str(T['tris']))
    d, hsh = tm.signature()
    st = tm.stored_signature()
    info['signature'] = dict(d, hash=hsh, stored=st)
    add('gate', 'template: the topology signature is the stored one (template_signatures.json)', st == hsh,
        f"{hsh}" + ('' if st == hsh else f' (stored: {st})'))
    T['template'] = info


def topology(body, J, plan, template=None):
    """With template (the kit/template.py Topo that built the body): the template gates of TOPO_LIMITS['template'] are added.
    The topology measures of a cage, on its own faces (the evaluated, mirrored mesh; quads and n-gons as
    modelled, never the export triangles). Returns a JSON-safe dict:
      size       edge-length and face-area spread over the body: p10, p50, p90, ratio = p90 / p10
      regions    per region (torso, head = neck joint on, each limb, each extra chain): faces, tris, tri and area
                 share, density (tri share / area share: > 1 is denser than the body's average), the edge spread,
                 the share of faces longer than 3:1 and 5:1, triangles and n-gons
      aspect     longest / shortest edge per face: % over 3:1 and 5:1, the worst
      nonquad    triangles, n-gons, their share
      poles      vertices of valence 3, 5, 6+; how many sit in a joint band, at a limb root, elsewhere; `at` for the dots
      joints     per joint: `loops` (joint_loops, the stage-1 gate), `rings` (closed face-loop rails in the band),
                 their spacing and spacing / ring width
      roots      per limb: the closed loop round the limb where it leaves the torso (`loop`), whether it passes over
                 the root joint (`over_joint`: the shoulder / hip loop), `flow` (share of the limb's lengthwise edges
                 that run on into the torso), `fans` (valence >= 6) and `caps` (non-quad faces) at the junction
      face_loops eye / mouth: 'present' | 'absent' | 'not declared' (META['landmarks'])
      ring_stacks  runs of 3+ near-parallel rings closer than 0.5 x the limb width outside a joint band
      checks     [{kind: 'gate' | 'warn', name, ok, detail}] against TOPO_LIMITS
    A limb's rings are found without any reference to a bone axis: every closed quad strip gives two rails,
    and a rail is a ring of a limb when it cuts the limb's tip off from every other tip."""
    J, plan = cage_plan(dict(J=J, plan=plan))
    LIM = TOPO_LIMITS
    bm = evaluated_bm(body)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    bm.verts.index_update(); bm.edges.index_update(); bm.faces.index_update()
    nF = len(bm.faces)
    cen = [f.calc_center_median() for f in bm.faces]
    area = np.array([f.calc_area() for f in bm.faces])
    elen = np.array([e.calc_length() for e in bm.edges])
    asp = np.array([max(elen[e.index] for e in f.edges) / max(1e-9, min(elen[e.index] for e in f.edges)) for f in bm.faces])
    sides = np.array([len(f.verts) for f in bm.faces])
    val = [len(v.link_edges) for v in bm.verts]
    adj = [[(e.index, g.index) for e in f.edges for g in e.link_faces if g is not f] for f in bm.faces]
    everyone = set(range(nF))

    def side(cut, seed):
        seen, st = {seed}, [seed]
        while st:
            for ei, g in adj[st.pop()]:
                if ei not in cut and g not in seen:
                    seen.add(g); st.append(g)
        return seen

    tree = BVHTree.FromBMesh(bm)
    near = lambda p: tree.find_nearest(p)[2]                            # the face under the surface point nearest p

    def pt(n, s=1):
        p = Vector(J[n])
        p.x *= s
        return p

    cuts = {}                                                           # rail (edge set) -> the faces on one side of it
    for strip, rails in _face_loops(bm):
        for g in _edge_groups(bm, rails):
            cut = frozenset(g)
            if cut not in cuts:
                A = side(cut, bm.edges[next(iter(cut))].link_faces[0].index)
                if len(A) < nF:
                    cuts[cut] = A
    geo = {}

    def ring(cut):
        if cut not in geo:
            vs = {v for ei in cut for v in bm.edges[ei].verts}
            P = np.array([v.co[:] for v in vs])
            c = P.mean(axis=0)
            geo[cut] = (vs, Vector(c), float(np.linalg.norm(P - c, axis=1).mean()), Vector(np.linalg.svd(P - c)[2][-1]))
        return geo[cut]

    chains = _topo_chains(J, plan)
    entries = [(n, c, s) for n, c in chains for s in ((1, -1) if abs(J[c[-1]][0]) > SEAM or abs(J[c[0]][0]) > SEAM else (1,))]
    tipface = {(n, s): near(pt(c[-1], s)) for n, c, s in entries}
    guard = {}                                                          # (chain, side) -> per joint, the faces round it

    def around(p):
        d = tree.find_nearest(p)[3]
        return frozenset(i for i in range(nF) if (cen[i] - p).length <= 1.5 * d + 1e-6) | {near(p)}

    for n, c, s in entries:
        guard[(n, s)] = [around(pt(a, s).lerp(pt(b, s), t)) for a, b in zip(c, c[1:]) for t in (0.5, 1.0)]
    limbish = {n for n, _ in chains[:1 + len(plan['limbs'])]}             # the head and the limbs: never inside another region

    def rings_for(name, c, s):
        """Every rail that cuts this chain's tip off from all other tips, most proximal first: [(size, cut, faces)]."""
        tip = pt(c[-1], s)
        r = 0.35 * (tip - pt(c[-2], s)).length
        seeds = {i for i in range(nF) if (cen[i] - tip).length <= r} | {tipface[(name, s)]}
        others = {f for key, f in tipface.items() if key != (name, s) and key[0] in limbish}
        out = []
        for cut, A in cuts.items():
            if seeds <= A:
                R = A
            elif not (seeds & A):
                R = everyone - A
            else:
                continue
            if R & others or len(R) > 0.5 * nF:
                continue
            if any(0 < len(R & g) < len(g) for key, gs in guard.items() if key != (name, s) for g in gs):
                continue                                                # it cuts through another limb: a slab, not a ring
            out.append((len(R), cut, R))
        out.sort(key=lambda x: -x[0])
        return out

    region = ['torso'] * nF
    RG = {}                                                             # (name, side) -> (all rings, the root ring)
    for name, c, s in entries:
        rs = rings_for(name, c, s)
        root = rs[0] if rs else None
        if name == 'head' and rs:                                       # the head starts at the ring nearest the neck joint
            root = min(rs, key=lambda x: (ring(x[1])[1] - pt(plan['neck'])).length)
        RG[(name, s)] = (rs, root)
    for name, c, s in entries:                                          # head first, then limbs and extras over it
        rs, root = RG[(name, s)]
        if root:
            for i in root[2]:
                region[i] = name
        else:                                                           # MVP-STUB: no closed ring at all: nearest bone decides
            segs = [(pt(a, s), pt(b, s)) for a, b in zip(c[1:], c[2:])] or [(pt(c[0], s), pt(c[1], s))]
            sp = [(pt(a), pt(b)) for a, b in zip(plan['spine'], plan['spine'][1:])]
            for i in range(nF):
                if min(_seg_dist(cen[i], a, b) for a, b in segs) < min(_seg_dist(cen[i], a, b) for a, b in sp):
                    region[i] = name
    names = ['torso'] + [n for n, _ in chains]
    vreg = [{region[f.index] for f in v.link_faces} for v in bm.verts]

    # ---- sizes, aspect, non-quads, per region ----
    ftris = sides - 2
    T = dict(faces=nF, tris=int(ftris.sum()), verts=len(bm.verts), limits=dict(LIM))
    T['size'] = dict(edge=_spread(elen), area=_spread(area, 6))
    T['aspect'] = dict(gt3_pct=round(100.0 * float((asp > 3).mean()), 1), gt5_pct=round(100.0 * float((asp > 5).mean()), 1),
                       worst=round(float(asp.max()), 1))
    T['nonquad'] = dict(tris=int((sides == 3).sum()), ngons=int((sides > 4).sum()), share=round(float((sides != 4).mean()), 3))
    rarr = np.array(region)
    ereg = [{region[f.index] for f in e.link_faces} for e in bm.edges]
    T['regions'] = {}
    for n in names:
        m = rarr == n
        if not m.any():
            continue
        es = _spread([elen[i] for i, r in enumerate(ereg) if n in r])
        ts, ar = float(ftris[m].sum()) / ftris.sum(), float(area[m].sum()) / area.sum()
        T['regions'][n] = dict(faces=int(m.sum()), tris=int(ftris[m].sum()), tri_share=round(ts, 3), area_share=round(ar, 3),
                               density=round(ts / ar, 2) if ar else 0.0, edge=es, area_ratio=_spread(area[m], 6)['ratio'],
                               gt3_pct=round(100.0 * float((asp[m] > 3).mean()), 1),
                               gt5_pct=round(100.0 * float((asp[m] > 5).mean()), 1),
                               tris_n=int((sides[m] == 3).sum()), ngons=int((sides[m] > 4).sum()))

    # ---- joints: bands, rings, spacing ----
    cname = {id(c): n for (n, _), c in zip(chains[1:], list(plan['limbs'].values()) + list(plan['extra']))}
    all_chains = [plan['spine']] + list(plan['limbs'].values()) + list(plan['extra'])
    loops = joint_loops(body, J, plan)
    bands = {}                                                          # joint -> (point, bisector, band, regions, off-seam, chain)
    for jn in plan['joints']:
        c = next((c for c in all_chains if jn in c), None)
        if c is None:
            continue
        i, j = c.index(jn), pt(jn)
        ds = [d for d in ((j - pt(c[i - 1])) if i > 0 else None, (pt(c[i + 1]) - j) if i + 1 < len(c) else None)
              if d is not None and d.length > 1e-6]
        bis = sum((d.normalized() for d in ds), Vector()).normalized()
        spine = c is plan['spine']
        bands[jn] = (j, bis, 0.4 * min(d.length for d in ds), {'torso', 'head'} if spine else {cname[id(c)]},
                     abs(j.x) > SEAM, 'head' if spine else cname[id(c)])
    T['joints'] = {}
    for jn, (j, bis, band, own, off, ch) in bands.items():
        rs = RG.get((ch, 1), ([], None))[0]
        g = sorted(((ring(cut)[1] - j).dot(bis), ring(cut)[1], ring(cut)[2]) for _, cut, _ in rs
                   if abs((ring(cut)[1] - j).dot(bis)) <= band)
        gap = [round((b[1] - a[1]).length, 4) for a, b in zip(g, g[1:])]
        w = 2 * float(np.mean([x[2] for x in g])) if g else 0.0
        T['joints'][jn] = dict(loops=loops.get(jn, 0), rings=len(g), spacing=gap, width=round(w, 4),
                               spacing_over_width=round(float(np.mean(gap)) / w, 2) if gap and w else None)

    # ---- poles ----
    def in_band(v):
        for jn, (j, bis, band, own, off, ch) in bands.items():
            p = Vector((abs(v.co.x), v.co.y, v.co.z)) if off else v.co
            if own & vreg[v.index] and abs((p - j).dot(bis)) <= band:
                return jn
        return None

    junction = {}                                                       # (limb, side) -> junction verts, faces, root verts
    for name, c, s in entries:
        rs, root = RG[(name, s)]
        if root and name in plan['limbs']:
            rv = ring(root[1])[0]
            jf = {f for v in rv for f in v.link_faces if f.index not in root[2]}
            junction[(name, s)] = (rv | {v for f in jf for v in f.verts}, jf, rv)
    at_root = {v.index for jv, _, _ in junction.values() for v in jv}
    pj, pin, proot, P = {}, 0, 0, []
    for v in bm.verts:
        if val[v.index] == 4:
            continue
        jn = in_band(v)
        if jn:
            pin += 1
            pj[jn] = pj.get(jn, 0) + 1
        elif v.index in at_root:
            proot += 1
        P.append([round(x, 4) for x in v.co] + [val[v.index], jn or ''])
    T['poles'] = dict(n3=sum(1 for x in val if x == 3), n5=sum(1 for x in val if x == 5), n6=sum(1 for x in val if x >= 6),
                      in_joint=pin, by_joint=pj, at_roots=proot, elsewhere=len(P) - pin - proot, at=P)

    # ---- limb roots: the shoulder / hip loop and how the limb runs into the torso ----
    T['roots'] = {}
    for name, c in plan['limbs'].items():
        rs, root = RG[(name, 1)]
        if not root:
            T['roots'][name] = dict(loop=False, over_joint=False, t=None, rings=0, flow=0.0, fans=0, caps=0, poles=0)
            continue
        vs, cc, rad, nor = ring(root[1])
        a, b = pt(c[0]), pt(c[1])
        t = (cc - a).dot(b - a) / (b - a).length_squared
        over = near(a) in root[2] or t <= 0.25
        jv, jf, rv = junction[(name, 1)]
        flows = 0
        for v in rv:
            if val[v.index] != 4:
                continue
            outw = [e for e in v.link_edges if e.index not in root[1] and not any(f.index in root[2] for f in e.link_faces)]
            if len(outw) == 1 and val[outw[0].other_vert(v).index] == 4:
                flows += 1
        T['roots'][name] = dict(loop=True, over_joint=bool(over), t=round(t, 2), verts=len(rv), rings=len(rs),
                                centre=[round(x, 4) for x in cc], flow=round(flows / len(rv), 2),
                                fans=sum(1 for v in jv if val[v.index] >= 6), caps=sum(1 for f in jf if len(f.verts) != 4),
                                poles=sum(1 for v in jv if val[v.index] != 4))

    # ---- ring-band stacks ----
    T['ring_stacks'] = []
    T['chains'] = {}
    cosp = math.cos(math.radians(25))
    for name, c in chains[1:]:
        G = [ring(cut) for _, cut, _ in RG[(name, 1)][0]]
        T['chains'][name] = dict(rings=len(G))
        isj = [any(ch == name and abs((g[1] - j).dot(bis)) <= band for j, bis, band, own, off, ch in bands.values()) for g in G]
        if template is not None:                                        # a template limb or tail: the socket, cap and mass rings
            a, b = pt(c[0]), pt(c[1])                                    # fan round the root (ball) joint by design, as a hinge's do
            isj = [x or (g[1] - a).length <= 0.6 * (b - a).length for x, g in zip(isj, G)]
        close = [(G[i + 1][1] - G[i][1]).length < LIM['stack_gap'] * (G[i][2] + G[i + 1][2])
                 and abs(G[i][3].dot(G[i + 1][3])) > cosp for i in range(len(G) - 1)]
        i = 0
        while i < len(close):
            if not close[i]:
                i += 1
                continue
            k = i
            while k < len(close) and close[k]:
                k += 1
            run = list(range(i, k + 1))
            free = [q for q in run if not isj[q]]
            if len(free) >= 3:
                gaps = [(G[q + 1][1] - G[q][1]).length / (G[q][2] + G[q + 1][2]) for q in run[:-1]]
                T['ring_stacks'].append(dict(chain=name, rings=len(run), outside_joints=len(free),
                                             at=[round(x, 3) for x in G[run[len(run) // 2]][1]],
                                             spacing_over_width=round(float(np.mean(gaps)), 2)))
            i = k

    # ---- face loops (optional landmarks) ----
    LM = plan.get('landmarks') or {}
    T['face_loops'] = {}
    tips = set(tipface.values())
    harea = float(area[rarr == 'head'].sum()) or float(area.sum())
    lf = {n: near(Vector(LM[n])) for n in ('eye', 'mouth') if n in LM}
    for n in ('eye', 'mouth'):
        if n not in lf:
            T['face_loops'][n] = 'not declared'
            continue
        found = False
        for cut, A in cuts.items():
            R = A if lf[n] in A else everyone - A
            if len(R) > 0.5 * nF or float(area[list(R)].sum()) > (0.2 if n == 'eye' else 0.5) * harea:
                continue
            if R & (tips if n == 'eye' else tips - {tipface[('head', 1)]}):
                continue
            if any(lf[o] in R for o in lf if o != n):
                continue
            found = True
            break
        T['face_loops'][n] = 'present' if found else 'absent'

    # ---- checks ----
    ck = []
    add = lambda kind, name, ok, detail: ck.append(dict(kind=kind, name=name, ok=bool(ok), detail=detail))
    er = {n: r['edge']['ratio'] for n, r in T['regions'].items()}
    add('gate', f"even face size: edge length p90/p10 <= {LIM['edge_ratio']:g} in every region",
        all(x <= LIM['edge_ratio'] for x in er.values()), ', '.join(f'{n} {x:g}' for n, x in er.items()))
    add('gate', f"long faces: at most {LIM['aspect5_pct']:g}% of faces over 5:1", T['aspect']['gt5_pct'] <= LIM['aspect5_pct'],
        f"{T['aspect']['gt5_pct']:g}% (worst {T['aspect']['worst']:g}:1)")
    add('gate' if template is None else 'warn', 'no pole (valence 3 or 5+) inside a joint band', pin <= LIM['joint_poles'],
        f'{pin}' + (f' {pj}' if pj else '') + f' of {len(P)} poles')
    bad = [n for n, r in T['roots'].items() if not (r['loop'] and r['over_joint'])]
    add('gate', 'a closed loop round every limb root, over its joint (shoulder / hip loop)', not bad,
        ', '.join(f"{n}: {'no loop' if not r['loop'] else ('over the joint' if r['over_joint'] else 'below the joint, t ' + str(r['t']))}"
                  for n, r in T['roots'].items()))
    fc = {n: (r['fans'], r['caps']) for n, r in T['roots'].items()}
    add('gate', 'limbs join the torso by edge flow: no fan (valence >= 6) and no non-quad face at the junction',
        all(a <= LIM['fans'] and b <= LIM['caps'] for a, b in fc.values()),
        ', '.join(f'{n} {a} fans {b} non-quads' for n, (a, b) in fc.items()))
    add('gate', f"no ring-band stack (3+ parallel rings closer than {LIM['stack_gap']:g} x the limb width outside a joint band)",
        len(T['ring_stacks']) <= LIM['ring_stacks'],
        ', '.join(f"{s['chain']} {s['rings']} rings at {s['spacing_over_width']:g} x width" for s in T['ring_stacks']) or '0')
    add('warn', f"faces over 3:1 at most {LIM['aspect3_pct']:g}%", T['aspect']['gt3_pct'] <= LIM['aspect3_pct'], f"{T['aspect']['gt3_pct']:g}%")
    lo, hi = LIM['density']
    dn = {n: r['density'] for n, r in T['regions'].items()}
    add('warn', f'density per region within {lo:g}-{hi:g} x the body average (triangle share / area share)',
        all(lo <= x <= hi for x in dn.values()), ', '.join(f'{n} {x:g}' for n, x in dn.items()))
    add('warn', f"edge length p90/p10 over the whole body <= {LIM['body_edge_ratio']:g}",
        T['size']['edge']['ratio'] <= LIM['body_edge_ratio'], f"{T['size']['edge']['ratio']:g}")
    fl = {n: r['flow'] for n, r in T['roots'].items()}
    add('warn', f"limb edges run on into the torso (flow >= {LIM['flow']:g})", all(x >= LIM['flow'] for x in fl.values()),
        ', '.join(f'{n} {x:g}' for n, x in fl.items()))
    add('warn', "face loops round the eye and the mouth (META['landmarks'])",
        all(x == 'present' for x in T['face_loops'].values()), ', '.join(f'{n} {x}' for n, x in T['face_loops'].items()))
    if template is not None:
        _template_checks(bm, T, template, val, add)
    T['checks'] = ck
    bm.free()
    return T


def _lin(c):
    """sRGB 0..255 -> linear 0..1 (a colour attribute is stored linear)."""
    return tuple(((x / 255 + 0.055) / 1.055) ** 2.4 if x / 255 > 0.04045 else x / 255 / 12.92 for x in c)


def _mix(a, b, t):
    t = min(1.0, max(0.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _baked(o, name, wire=0.0):
    """The evaluated object (mirror, armature) as a new plain mesh object; wire > 0: its wireframe."""
    d = o.copy()
    link(d)
    if wire:
        wm = d.modifiers.new('wf', 'WIREFRAME')
        wm.thickness, wm.use_replace, wm.use_even_offset = wire, True, False
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(d.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(d, do_unlink=True)
    ob = link(bpy.data.objects.new(name, me))
    ob.matrix_world = o.matrix_world.copy()
    return ob


def _face_paint(ob, cols):
    """cols: one sRGB 0..255 colour (a tuple), or a list with one per polygon."""
    me = ob.data
    at = me.color_attributes.get('_qa') or me.color_attributes.new('_qa', 'BYTE_COLOR', 'CORNER')
    one = _lin(cols) if isinstance(cols, tuple) else None
    buf = []
    for p in me.polygons:
        c = one or _lin(cols[p.index])
        buf += [c[0], c[1], c[2], 1.0] * p.loop_total
    at.data.foreach_set('color', buf)
    me.color_attributes.active_color = at


def _dots(name, pts, radius, rgb):
    bm = bmesh.new()
    for p in pts:
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius, matrix=Matrix.Translation(p[:3]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    _face_paint(ob, rgb)
    return ob


def topology_targets(T, J, plan, L):
    """Close views of the topology sheet: [(label, point, radius, direction to the camera)]: shoulder, hip,
    the neck / head join and one limb end."""
    out = []
    limbs = list(plan['limbs'].items())
    for (name, c), d, lab in zip(limbs[:2], ((1, -0.35, 0.3), (1, 0.35, 0.3)), ('shoulder', 'hip')):
        a, b = Vector(J[c[0]]), Vector(J[c[1]])
        rc = T['roots'].get(name, {}).get('centre')
        out.append((f'{lab}: {name} root ({c[0]})', (a + Vector(rc)) / 2 if rc else a, max(1.3 * (b - a).length, 0.2 * L), d))
    n, h = Vector(J[plan['neck']]), Vector(J[plan['head']])
    out.append(('neck / head join', (n + h) / 2, max(1.5 * (h - n).length, 0.2 * L), (1, -0.7, 0.35)))
    if limbs:
        name, c = limbs[0]
        a, b = Vector(J[c[-2]]), Vector(J[c[-1]])
        out.append((f'limb end: {name} ({c[-1]})', (a + b) / 2, max(0.9 * (b - a).length, 0.1 * L), (1, -1, 0.7)))
    return out


def topology_shots(outdir, body, T, frame, J, plan, pieces=(), tag='topo'):
    """The topology pictures, every one a quad wire over FLAT colour (no shading, no triangulation):
      <tag>_wire_<view>.png     hero, az090, az000, top, back34, under: quads grey, triangles orange, n-gons violet,
                                poles as dots (valence 3 blue, 5 orange, 6+ magenta); pieces blue-grey
      <tag>_close_<i>.png       shoulder, hip, neck / head join, one limb end (<tag>_shots.json has the labels)
      <tag>_density_<view>.png  face area against the body's median: blue = smaller (denser), red = larger
      <tag>_aspect_<view>.png   longest / shortest edge: grey <= 2, yellow 3, red >= 5"""
    if os.environ.get('BMK_NORENDER'):
        return
    os.makedirs(outdir, exist_ok=True)
    C = TOPO_COL
    L = max(frame['size'])
    hidden = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    base = _baked(body, '_topo_body')
    me = base.data
    med = T['size']['area']['p50'] or 1e-9
    kind, dens, aspc = [], [], []
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        ls = [(vs[i] - vs[i - 1]).length for i in range(len(vs))]
        a = max(ls) / max(1e-9, min(ls))
        kind.append(C['quad'] if len(vs) == 4 else C['tri'] if len(vs) == 3 else C['ngon'])
        x = math.log2(max(p.area, 1e-12) / med) / 3.0
        dens.append(_mix(C['quad'], C['dense'], -x) if x < 0 else _mix(C['quad'], C['sparse'], x))
        aspc.append(_mix(C['quad'], C['a3'], a - 2) if a < 3 else _mix(C['a3'], C['a5'], (a - 3) / 2))
    solid = [base] + [_baked(p, '_topo_p') for p in pieces]
    for o in solid[1:]:
        _face_paint(o, C['piece'])
    wires, dots = {}, {}
    for key, t, r in (('full', L * 0.0032, L * 0.011), ('thin', L * 0.0014, L * 0.0055)):
        wires[key] = [_baked(o, '_topo_w', t) for o in [body] + list(pieces)]
        for o in wires[key]:
            _face_paint(o, (5, 5, 5))
        dots[key] = [_dots('_topo_d', [p for p in T['poles']['at'] if lo <= p[3] <= hi], r, C[c])
                     for c, lo, hi in (('pole3', 3, 3), ('pole5', 5, 5), ('pole6', 6, 99))]

    def show(wk, dk):
        for key in wires:
            for o in wires[key]:
                o.hide_render = key != wk
            for o in dots[key]:
                o.hide_render = key != dk

    _workbench('topo')
    view('under', (0.35, -0.45, -1.0))
    _face_paint(base, kind)
    show('full', 'full')
    for v in ('hero', 'az090', 'az000', 'top', 'back34', 'under'):
        camera(frame, v, fill=FILL)
        _render(os.path.join(outdir, f'{tag}_wire_{v}.png'), 900)
    show('thin', 'thin')
    labels = []
    for i, (lab, p, r, d) in enumerate(topology_targets(T, J, plan, L)):
        dist = r / math.tan(FOV / 2)
        camera(dict(centre=list(p), size=[dist / DIST] * 3), view(f'_topo{i}', d))
        _render(os.path.join(outdir, f'{tag}_close_{i}.png'), 800)
        labels.append(lab)
    show('full', None)
    for nm, cols in (('density', dens), ('aspect', aspc)):
        _face_paint(base, cols)
        for v in ('hero', 'az090', 'top'):
            camera(frame, v, fill=FILL)
            _render(os.path.join(outdir, f'{tag}_{nm}_{v}.png'), 700)
    for o in solid + [x for key in wires for x in wires[key] + dots[key]]:
        m = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(m)
    for o in hidden:
        o.hide_render = False
    _dump(os.path.join(outdir, f'{tag}_shots.json'), dict(close=labels))


def tri_budget(T, pieces):
    """Where the triangles of the final model went: every body region and every piece group (eye_L and eye_R
    are one group), each {tris, share}; plus the pieces' total share."""
    rows = {f'body: {n}': r['tris'] for n, r in T['regions'].items()}
    for p in pieces:
        n = p.name[6:] if p.name.startswith('piece_') else p.name
        n = n.split('.')[0].rstrip('0123456789_')
        n = n[:-2] if n.endswith(('_L', '_R', '_l', '_r')) else n
        n = 'piece: ' + n.rstrip('0123456789_')
        rows[n] = rows.get(n, 0) + report(p, False)['tris']
    tot = max(1, sum(rows.values()))
    pc = sum(v for n, v in rows.items() if n.startswith('piece'))
    return dict(total=tot, pieces_share=round(pc / tot, 3),
                rows={n: dict(tris=v, share=round(v / tot, 3)) for n, v in sorted(rows.items(), key=lambda x: -x[1])})


def topology_final(k, N, body, pieces, frame):
    """Stage 3 / 4 of a cage build: the base's topology as modelled (before the export triangulation) and the
    triangle budget per body region and piece group, to stage<N>/topology.json; at stage 4 the pictures too."""
    J, plan = cage_plan(k.meta)
    T = topology(body, J, plan)
    T['budget'] = B = tri_budget(T, pieces)
    say(f"s{N} topology: triangles by region: " + ', '.join(f"{n} {100 * r['share']:.0f}%" for n, r in list(B['rows'].items())[:6]))
    torso = B['rows'].get('body: torso', dict(tris=0))['tris']
    big = [n for n, r in B['rows'].items() if n.startswith('piece') and r['tris'] > torso]
    if big or B['pieces_share'] > TOPO_LIMITS['piece_share']:
        say(f"WARN s{N} topology: pieces take {100 * B['pieces_share']:.0f}% of the triangles"
            + (f"; more triangles than the whole torso ({torso}): {', '.join(big)}" if big else ''))
    _dump(k.path(f'stage{N}', 'topology.json'), T)
    if N == 4:
        topology_shots(k.path('stage4'), body, T, frame, J, plan, pieces)
    return T


# =============================================================================
# 11. PART PROFILES: the medium forms (head, arms, legs) against the reference, station by station
# =============================================================================
# A limb of the reference swells and tapers (shoulder, elbow, forearm, wrist); a lofted limb is a tube. Both are
# measured the same way: cross-sections square to the bone chain. The limits are set from the three c2 cages
# (wolf legs 1.6 and 2.4% RMS and tapers within 19%: the cage that follows its sheet; goblin arm and leg 6-15%).
PROFILE_LIMITS = dict(
    taper_pct=20.0,          # gate: a part's taper ratio (max / min along the part) within this % of the reference's
    rms_pct=3.0,             # gate: RMS of (model - reference) over the width and depth curves, % of the part's length
    per_bone=3,              # stations per bone
    hidden=1.25,             # a view cannot see a dimension where the model's own silhouette run exceeds its section by this
    sheet_band=(0.6, 1.2),   # a sheet-mask run is used when it is within this ratio of the guide's section; else the guide
    min_stations=3,
)


def _section_fill(ob, p, d):
    """Area of the section outline round p (cut square to d) over its bounding box: 0.785 is an ellipse, 1.0 a box."""
    from carve import _plane_axes
    u, w = _plane_axes(d)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    r = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-7,
                               plane_co=p, plane_no=d, clear_inner=False, clear_outer=False)
    nb = {}
    for e in (g for g in r['geom_cut'] if isinstance(g, bmesh.types.BMEdge)):
        nb.setdefault(e.verts[0], []).append(e.verts[1]); nb.setdefault(e.verts[1], []).append(e.verts[0])
    seen, best = set(), None
    for v in nb:
        if v in seen:
            continue
        comp, st = [], [v]
        seen.add(v)
        while st:
            x = st.pop(); comp.append(x)
            for y in nb[x]:
                if y not in seen:
                    seen.add(y); st.append(y)
        P = np.array([((q.co - p).dot(u), (q.co - p).dot(w)) for q in comp])
        ang = np.sort(np.arctan2(P[:, 1], P[:, 0]))
        gap = np.max(np.diff(np.concatenate([ang, ang[:1] + 2 * math.pi]))) if len(ang) > 2 else 7.0
        score = (0 if gap < math.pi else 1, float(np.min(np.hypot(P[:, 0], P[:, 1]))))
        if best is None or score < best[0]:
            best = (score, P)
    bm.free()
    if best is None or len(best[1]) < 3:
        return None
    P = best[1]
    c = (P.min(0) + P.max(0)) / 2
    Q = P[np.argsort(np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0]))]
    a = 0.5 * abs(float(np.dot(Q[:, 0], np.roll(Q[:, 1], -1)) - np.dot(Q[:, 1], np.roll(Q[:, 0], -1))))
    box = float(np.prod(P.max(0) - P.min(0)))
    return round(a / box, 3) if box > 0 else None


def _mask_run(view, xyz, dxyz):
    """Length (metres) of a reference view's mask run through the world point xyz along the world direction
    dxyz (both projected into the view); None when the direction points at the camera."""
    s = view.s
    r0, c0 = view.pix(*xyz)
    r1, c1 = view.pix(*(Vector(xyz) + Vector(dxyz)))
    dr, dc = r1 - r0, c1 - c0
    n = math.hypot(dr, dc) * s
    if n < 0.7:
        return None
    dr, dc = dr * s / n, dc * s / n
    M = view.mask
    H, W = M.shape
    inside = lambda t: 0 <= int(r0 + dr * t) < H and 0 <= int(c0 + dc * t) < W and bool(M[int(r0 + dr * t), int(c0 + dc * t)])
    t0 = next((t for k in range(int(0.03 / s) * 2) for t in (k * 0.5, -k * 0.5) if inside(t)), None)
    if t0 is None:
        return None
    a = b = t0
    while inside(a - 0.5):
        a -= 0.5
    while inside(b + 0.5):
        b += 0.5
    return (b - a + 0.5) * s


def part_profiles(body, J, plan, ref, guide=None, masks_=None):
    """The medium forms of the cage against the reference: for the head (neck -> head -> snout) and every limb
    chain, stations along the bones (PROFILE_LIMITS['per_bone'] per bone), and at each the section's `depth`
    (its extent in the side view, square to the bone; the head's height) and `width` (its extent in the front
    or the plan view), for the model and for the reference.
      ref     the creature folder: its reference/ sheet gives the side, front and top masks (carve.load_ref)
      guide   the carve guide (carve_guide(k)); carve.hull_sections cuts it and the model the same way
      masks_  (the model's orthographic masks, their frame), as cage_gates has them; rendered here when absent
    Source of the reference value, per station and dimension (`src`):
      'sheet'   the sheet mask's run through the section centre (the tighter of front and top for the width),
                when it agrees with the guide's section (0.6-1.2 x), or there is no guide section and it is
                within 0.5-1.5 x the model's
      'guide'   the guide's section (hull_sections), where the mask's run does not separate the part
      'hidden'  no view can see this dimension here: the model's own silhouette run is over 1.25 x its section
                (an arm in front of the torso in the side view). A three-view hull is blind there too, so the
                station is left out for that dimension and counted.
    A station whose model section reaches the body's midline (a leg still inside the flank) is `fused` and
    left out. Per part: `stations`; per dimension the taper ratio (max / min along the part) and the tube score
    (1 - coefficient of variation: 1.00 is a constant tube) of model and reference; `rms_pct` and `max_pct`
    (model - reference over both curves, % of the part's length); and the guide's own numbers (`guide`: valid
    stations, taper, tube, `fill` = section area / bounding box, 0.79 an ellipse and 1.00 a box, width / depth
    `aspect`, distance from the sheet's masks). `checks` as in topology()."""
    import carve
    J, plan = cage_plan(dict(J=J, plan=plan))
    LIM = PROFILE_LIMITS
    views = None
    if isinstance(ref, str) and os.path.exists(os.path.join(ref, 'reference', 'refs.json')):
        try:
            views = carve.load_ref(ref)
        except Exception as e:                                          # MVP-STUB: only 2 x 2 sheets have masks here
            say('part_profiles: no sheet masks:', e)
    try:
        guide = guide if guide is not None and guide.data else None
    except ReferenceError:
        guide = None
    if masks_ is None:
        fr = frame_of([body])
        fr['ortho'] = 1.2 * max(fr['size'])
        masks_ = (ortho_masks(fr), fr)
    mm, fr = masks_
    res = mm['side'].shape[0]
    orth = {v: _Ortho(v, fr, res) for v in mm}
    bm = evaluated_bm(body)
    me = bpy.data.meshes.new('_prof')
    bm.to_mesh(me)
    bm.free()
    mob = bpy.data.objects.new('_prof', me)
    out = dict(limits=dict(LIM), parts={}, source=dict(sheet=bool(views), guide=bool(guide)))
    if views:
        sd = views['side']
        out['sheet_map'] = dict(side=dict(s=sd.s, ground=sd.ground, cmid=sd.cmid))
    m = LIM['per_bone']
    DV = dict(depth=('side',), width=('front', 'top'))

    def model_run(v, c, d):                                             # the model's silhouette run in view v
        o = orth[v]
        duv = Vector(o.uv(d))
        if duv.length < 0.7:
            return None
        return _run_len(mm[v], o, o.uv(c), tuple(duv.normalized()))

    for name, c in _topo_chains(J, plan)[:1 + len(plan['limbs'])]:
        P = [Vector(J[n]) for n in c]
        total = sum((b - a).length for a, b in zip(P, P[1:]))
        off = abs(P[0].x) > SEAM or abs(P[-1].x) > SEAM
        st, done = [], 0.0
        for bi, (a, b) in enumerate(zip(P, P[1:])):
            d = (b - a).normalized()
            u, w = carve._plane_axes(d)
            ax = dict(depth=w, width=u)
            ms = carve.hull_sections(mob, a, b, m + 1)
            gs = carve.hull_sections(guide, a, b, m + 1) if guide else [None] * (m + 1)

            def good(S, p):
                if S is None or S.get('centre') is None or not S['inside']:
                    return False
                return not (off and min(p.x + S['lo'][0] * u.x, p.x + S['hi'][0] * u.x) < 0.15 * abs(p.x))

            for i in range(m + 1):
                if (i == 0 and bi > 0) or (i == m and bi == len(P) - 2):
                    continue                                            # a joint is cut once; the tip is not a station
                M_, G_ = ms[i], gs[i]
                p = a.lerp(b, i / m)
                row = dict(s=round((done + (b - a).length * i / m) / total, 3), at=[round(x, 4) for x in p], bone=c[bi],
                           w=[round(x, 3) for x in w], fused=not good(M_, p), src={})
                st.append(row)
                if row['fused']:
                    continue
                row['model'] = dict(width=M_['width'], depth=M_['depth'], centre=list(M_['centre']), fill=_section_fill(mob, p, d))
                if good(G_, p):
                    row['guide'] = dict(width=G_['width'], depth=G_['depth'], centre=list(G_['centre']), fill=_section_fill(guide, p, d))
                mc = Vector(M_['centre'])
                rc = Vector(row['guide']['centre']) if 'guide' in row else mc
                row['ref'], row['sheet'] = {}, {}
                for key in ('depth', 'width'):
                    mv, g = row['model'][key], row.get('guide', {}).get(key)
                    seen_in = [v for v in DV[key] if v in mm and (model_run(v, mc, ax[key]) or 9e9) <= LIM['hidden'] * mv]
                    if not seen_in:
                        row['src'][key] = 'hidden'
                        continue
                    runs = [r for r in (_mask_run(views[v], rc, ax[key]) for v in seen_in)] if views else []
                    sh = min([r for r in runs if r], default=None)
                    if sh:
                        row['sheet'][key] = round(sh, 4)
                    lo, hi = LIM['sheet_band']
                    if sh and ((g and lo * g <= sh <= hi * g) or (not g and 0.5 * mv <= sh <= 1.5 * mv)):
                        row['ref'][key], row['src'][key] = round(sh, 4), 'sheet'
                    elif g:
                        row['ref'][key], row['src'][key] = g, 'guide'
                    else:
                        row['src'][key] = 'hidden'
            done += (b - a).length
        part = dict(joints=c, length=round(total, 4), stations=st, dims={})
        diffs = []
        for key in ('depth', 'width'):
            ok = [r for r in st if key in r.get('ref', {})]
            D = dict(stations=len(ok), hidden=sum(1 for r in st if r['src'].get(key) == 'hidden'),
                     sources={s_: sum(1 for r in ok if r['src'][key] == s_) for s_ in ('sheet', 'guide')})
            if len(ok) >= LIM['min_stations']:
                A, B = np.array([r['model'][key] for r in ok]), np.array([r['ref'][key] for r in ok])
                diffs.append(A - B)
                ta, tb = float(A.max() / max(1e-9, A.min())), float(B.max() / max(1e-9, B.min()))
                D.update(taper_model=round(ta, 2), taper_ref=round(tb, 2), taper_diff_pct=round(100 * (ta - tb) / tb, 1),
                         tube_model=round(1 - float(A.std() / A.mean()), 2), tube_ref=round(1 - float(B.std() / B.mean()), 2),
                         rms_pct=round(100 * float(np.sqrt(((A - B) ** 2).mean())) / total, 2))
            part['dims'][key] = D
        if diffs:
            df = np.concatenate(diffs)
            part.update(rms_pct=round(100 * float(np.sqrt((df ** 2).mean())) / total, 2),
                        max_pct=round(100 * float(np.abs(df).max()) / total, 2))
        fl = [r['model']['fill'] for r in st if r.get('model', {}).get('fill')]
        part['model_fill'] = round(float(np.mean(fl)), 2) if fl else None
        gk = [r for r in st if 'guide' in r]
        G = dict(stations=len(gk), of=len(st), fused=sum(1 for r in st if r['fused']))
        if len(gk) >= LIM['min_stations']:                              # the guide on its own: a tube or a box here?
            gw, gd = np.array([r['guide']['width'] for r in gk]), np.array([r['guide']['depth'] for r in gk])
            dia = np.sqrt(gw * gd)
            vs = {k_: [abs(r['guide'][k_] - r['sheet'][k_]) / r['sheet'][k_] for r in gk if k_ in r['sheet']] for k_ in ('depth', 'width')}
            G.update(taper=round(float(dia.max() / dia.min()), 2), tube=round(1 - float(dia.std() / dia.mean()), 2),
                     fill=round(float(np.mean([r['guide']['fill'] or 0 for r in gk])), 2), aspect=round(float(np.mean(gw / gd)), 2),
                     vs_sheet_pct={k_: (round(100 * float(np.mean(v)), 1) if v else None) for k_, v in vs.items()})
        part['guide'] = G
        out['parts'][name] = part
    bpy.data.objects.remove(mob)
    bpy.data.meshes.remove(me)
    ck = []
    for name, p in out['parts'].items():
        have = {k_: D for k_, D in p['dims'].items() if 'taper_model' in D}
        hid = ', '.join(f"{k_} hidden at {D['hidden']}" for k_, D in p['dims'].items() if D['hidden'])
        if not have:
            ck.append(dict(kind='warn', part=name, name=f'{name}: profile measured', ok=False,
                           detail=f"under {LIM['min_stations']} comparable stations" + (f' ({hid})' if hid else '')))
            continue
        ck.append(dict(kind='gate', part=name, name=f"{name}: taper ratio within {LIM['taper_pct']:g}% of the reference's",
                       ok=all(abs(D['taper_diff_pct']) <= LIM['taper_pct'] for D in have.values()),
                       detail='; '.join(f"{k_} model {D['taper_model']:g} reference {D['taper_ref']:g} ({D['taper_diff_pct']:+g}%), "
                                        f"tube score {D['tube_model']:g} vs {D['tube_ref']:g}" for k_, D in have.items())))
        ck.append(dict(kind='gate', part=name, name=f"{name}: profile RMS <= {LIM['rms_pct']:g}% of the part's length",
                       ok=p['rms_pct'] <= LIM['rms_pct'],
                       detail=f"RMS {p['rms_pct']:g}%, max {p['max_pct']:g}% (" + ', '.join(
                           f"{k_} {D['stations']} stations: {D['sources']['sheet']} sheet {D['sources']['guide']} guide"
                           for k_, D in have.items()) + ')' + (f'; {hid}' if hid else '')))
    out['checks'] = ck
    return out


# The guide on its own: the base form is judged (pictures and profiles) before any cage exists.
GUIDE_VIEWS = ['hero', 'az090', 'az000', 'top', 'back34']


def _solo(guide):
    """Show the hidden guide alone to the renderer; returns the undo."""
    others = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o is not guide and not o.hide_render]
    for o in others:
        o.hide_render = True
    was = guide.hide_render, guide.display_type
    guide.hide_render, guide.display_type = False, 'SOLID'

    def undo():
        guide.hide_render, guide.display_type = was
        for o in others:
            o.hide_render = False
    return undo


def guide_views(outdir, guide, frame=None, res=768, tag='guide'):
    """Grey renders of the guide alone (GUIDE_VIEWS), smooth shaded: <tag>_<view>_clay.png."""
    undo = _solo(guide)
    try:
        guide.data.polygons.foreach_set('use_smooth', [True] * len(guide.data.polygons))
        return shoot(outdir, tag, frame or frame_of([guide]), views=GUIDE_VIEWS, wire_views=[], res=res, objs=[guide])
    finally:
        undo()


def guide_profiles(guide, J, plan, ref, frame=None):
    """part_profiles of the GUIDE itself against the sheet's masks (the 'guide' block of profiles.json): per part
    the RMS and max distance (% of the part's length), per dimension the taper of the guide and of the sheet, the
    section fill (0.79 an ellipse, 1.00 a box), and how many stations are fused with the body or hidden."""
    undo = _solo(guide)
    try:
        fr = dict(frame) if frame else frame_of([guide])
        fr.setdefault('ortho', 1.2 * max(fr['size']))
        PP = part_profiles(guide, J, plan, ref, None, masks_=(ortho_masks(fr), fr))
    finally:
        undo()
    out = {}
    for name, p in PP['parts'].items():
        out[name] = dict(rms_pct=p.get('rms_pct'), max_pct=p.get('max_pct'), fill=p['model_fill'], stations=len(p['stations']),
                         fused=sum(1 for r in p['stations'] if r['fused']),
                         rows=[dict(s=r['s'], fused=r['fused'], guide=[r.get('model', {}).get(k_) for k_ in ('width', 'depth')],
                                    sheet=[r.get('ref', {}).get(k_) for k_ in ('width', 'depth')]) for r in p['stations']],
                         dims={k_: {a: D.get(b) for a, b in (('stations', 'stations'), ('hidden', 'hidden'), ('taper_guide', 'taper_model'),
                                                             ('taper_sheet', 'taper_ref'), ('taper_diff_pct', 'taper_diff_pct'),
                                                             ('rms_pct', 'rms_pct'))} for k_, D in p['dims'].items()})
    return out
