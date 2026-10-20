"""partseg.py: hard per-part face ownership of a carve, for skinning (bmkit.skin_parts).

The one idea ported from PartLLM (research/partllm_opus.md, research/partllm_fable.md): every face is
claimed by exactly one part through a softmax over all parts, then the labels are cleaned (vote fill of
isolated faces, small regions merged into a neighbour, a boundary band re-decided on the dihedral angle so
the seam lands on the crease). Our parts are the rig's deform bones, so no learned model is needed.

    labels = part_labels(body, rig)            # body: the skinned mesh object (its Mirror is applied first)
    skin_parts(body, rig, labels)              # bmkit: weight 1 to the owner, a 2-bone blend in the seam band
    label_shots(path, body, labels, frame)     # <path>: colour by label (top row) and the seam bands (bottom)

Score of bone b for face f: -dist(f, segment b) / r_b(t), r_b(t) the local part radius at the face's station
t along the bone (perpendicular rays from the bone into the carve, median hit distance), minus a penalty when
the bone cannot see the face: the face's normal points at the bone (the torso side of the armpit, the inner
thigh against the pelvis) or the straight line from the face to its closest bone point leaves the body.
"""
import heapq, math, os
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


def mirror_name(n):
    return n[:-2] + '.R' if n.endswith('.L') else n[:-2] + '.L' if n.endswith('.R') else n


def _segments(rig_or_J):
    """{bone: (head, tail)} world points: from a rig's deform bones, or a dict given as such."""
    if isinstance(rig_or_J, dict):
        return {n: (Vector(v[0]), Vector(v[1])) for n, v in rig_or_J.items()}
    M = rig_or_J.matrix_world
    return {b.name: (M @ b.head_local, M @ b.tail_local) for b in rig_or_J.data.bones if b.use_deform}


def _chain_roots(rig_or_J):
    """Bones that start a chain off their parent (a parent, not connected): upper arm, thigh, tail root.
    From a dict: entries given as (head, tail, True)."""
    if isinstance(rig_or_J, dict):
        return {n for n, v in rig_or_J.items() if len(v) > 2 and v[2]}
    return {b.name for b in rig_or_J.data.bones if b.use_deform and b.parent is not None and not b.use_connect}


def _mesh(body):
    """World face centres, normals, areas, polygon vertex lists and the face adjacency of the body."""
    me = body.data
    mw = body.matrix_world
    n3 = mw.to_3x3().inverted().transposed()
    V = np.array([tuple(mw @ v.co) for v in me.vertices])
    C = np.array([tuple(mw @ p.center) for p in me.polygons])
    N = np.array([tuple((n3 @ p.normal).normalized()) for p in me.polygons])
    A = np.array([p.area for p in me.polygons])
    P = [tuple(p.vertices) for p in me.polygons]
    ef = {}
    for fi, poly in enumerate(P):
        for k in range(len(poly)):
            e = (min(poly[k], poly[k - 1]), max(poly[k], poly[k - 1]))
            ef.setdefault(e, []).append(fi)
    adj = [[] for _ in P]                    # (neighbour face, edge length, boundary cost weight)
    for (a, b), fs in ef.items():
        if len(fs) != 2:
            continue
        f, g = fs
        L = float(np.linalg.norm(V[a] - V[b]))
        ang = math.acos(max(-1.0, min(1.0, float(N[f] @ N[g]))))
        concave = float((C[g] - C[f]) @ N[f]) > 0.0
        # a cut is cheap along a concave crease (where a leg meets the body), full price on flat / convex skin
        w = max(0.1, 1.0 - 0.9 * min(1.0, ang / (math.pi / 2))) if concave else 1.0
        adj[f].append((g, L, w)); adj[g].append((f, L, w))
    tree = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(poly) for poly in P])
    return V, C, N, A, P, adj, tree


def _seg_proj(X, a, b):
    """Distance from points X (n, 3) to segment a-b, the station t in [0, 1] and the closest points."""
    d = b - a
    t = np.clip(((X - a) @ d) / max(float(d @ d), 1e-12), 0.0, 1.0)
    Q = a + t[:, None] * d
    return np.linalg.norm(X - Q, axis=1), t, Q


def _radii(C, segs, names, n=5, lim=(0.6, 1.6)):
    """Local part radius per bone and station: the median distance to the bone of the faces nearest to it
    (the carve's own cross-section round the bone, robust to a bone lying off-centre or poking through the
    skin), per station bin along the bone, clamped to lim x the bone's median (a limb root buried in the
    torso would otherwise read the torso's girth)."""
    D, T = [], []
    for nm in names:
        a, b = (np.array(tuple(x)) for x in segs[nm])
        d, t, _ = _seg_proj(C, a, b)
        D.append(d); T.append(t)
    D, T = np.array(D), np.array(T)
    near = np.argmin(D, axis=0)
    out = {}
    for j, nm in enumerate(names):
        m = near == j
        if m.sum() < 3:
            L = float(np.linalg.norm(np.array(tuple(segs[nm][1])) - np.array(tuple(segs[nm][0]))))
            out[nm] = (np.array([0.0, 1.0]), np.full(2, max(0.02, 0.25 * L)))
            continue
        med = float(np.median(D[j, m]))
        ts = (np.arange(n) + 0.5) / n
        rs = []
        for k in range(n):
            mk = m & (T[j] >= k / n) & (T[j] <= (k + 1) / n)
            rs.append(float(np.median(D[j, mk])) if mk.sum() >= 4 else med)
        out[nm] = (ts, np.clip(np.array(rs), lim[0] * med, lim[1] * med))
    return out


def _components(lab, adj, faces=None):
    seen, comps = set(), []
    for f in (range(len(lab)) if faces is None else faces):
        if f in seen:
            continue
        stack, comp = [f], []
        seen.add(f)
        while stack:
            x = stack.pop(); comp.append(x)
            for g, _, _ in adj[x]:
                if g not in seen and lab[g] == lab[f]:
                    seen.add(g); stack.append(g)
        comps.append(comp)
    return comps


def _vote_fill(lab, adj, A, passes=6):
    """A face no neighbour agrees with takes its neighbours' majority (by shared edge length)."""
    n = 0
    for _ in range(passes):
        ch = 0
        for f in range(len(lab)):
            if not adj[f] or any(lab[g] == lab[f] for g, _, _ in adj[f]):
                continue
            acc = {}
            for g, L, _ in adj[f]:
                acc[lab[g]] = acc.get(lab[g], 0.0) + L
            lab[f] = max(acc, key=acc.get); ch += 1
        n += ch
        if not ch:
            break
    return n


def _drop_small(lab, adj, A, min_area):
    """Regions under min_area (fraction of the total) and stray islands (a part's island under half its
    largest) go to the neighbour they share the longest border with, smallest first."""
    tot = float(A.sum())
    merged = 0
    for _ in range(50):
        comps = _components(lab, adj)
        big = {}
        for c in comps:
            big[lab[c[0]]] = max(big.get(lab[c[0]], 0.0), float(A[c].sum()))
        small = [c for c in comps if float(A[c].sum()) < min_area * tot
                 or float(A[c].sum()) < 0.5 * big[lab[c[0]]]]
        if not small:
            break
        c = min(small, key=lambda c_: float(A[c_].sum()))
        cs = set(c)
        acc = {}
        for f in c:
            for g, L, _ in adj[f]:
                if g not in cs:
                    acc[lab[g]] = acc.get(lab[g], 0.0) + L
        if not acc:
            break
        nl = max(acc, key=acc.get)
        for f in c:
            lab[f] = nl
        merged += 1
    return merged


def _ring_faces(lab, adj, rings, pair=None):
    """Faces within `rings` face rings of a label border (of one bone pair when given)."""
    seed = set()
    for f in range(len(lab)):
        for g, _, _ in adj[f]:
            if lab[g] != lab[f] and (pair is None or {lab[f], lab[g]} == set(pair)):
                seed.add(f)
    band, front = set(seed), set(seed)
    for _ in range(rings - 1):
        nxt = {g for f in front for g, _, _ in adj[f]} - band
        band |= nxt; front = nxt
    return band


def _symmetrise(lab, C, names):
    """Faces on -X take the label of their mirror face (L/R swapped): the labels are mirror-exact."""
    kd = KDTree(len(C))
    for i, c in enumerate(C):
        kd.insert(c, i)
    kd.balance()
    idx = {n: i for i, n in enumerate(names)}
    n = 0
    for f, c in enumerate(C):
        if c[0] < -1e-5:
            _, j, d = kd.find((-c[0], c[1], c[2]))
            if d < 1e-4:
                m = idx.get(mirror_name(names[lab[j]]), lab[j])
                if lab[f] != m:
                    lab[f] = m; n += 1
    return n


def part_labels(body, rig_or_J, plan=None, tau=0.35, penalty=3.0, face_cos=-0.2, lam=1.0, iters=8,
                band_rings=2, min_area=0.002, unary_w=1.0):
    """Per face of `body` (its Mirror applied first), the owning deform bone.
    rig_or_J: the rig, or {bone: (head, tail)}. plan: optional {bone: radius} overriding the measured radii.
    Returns dict(names, label (face -> bone index), prob (faces x bones softmax), bands {(a, b): faces},
    band (all faces in a seam band), stats)."""
    import bmkit
    bmkit.apply_mirror(body)
    segs = _segments(rig_or_J)
    names = sorted(segs)
    V, C, N, A, P, adj, tree = _mesh(body)
    F, B = len(C), len(names)
    S = np.zeros((F, B))
    occl = np.zeros((F, B), bool)
    # MVP-STUB: carve.parts_field radii are not wired in (v1 builds carve a visual hull, no part plan);
    # every bone measures its radius from the carve's own faces round it (_radii), `plan` can override per bone.
    RS = _radii(C, segs, names)
    roots = _chain_roots(rig_or_J)
    for j, n in enumerate(names):
        a, b = (np.array(tuple(x)) for x in segs[n])
        D, t, Q = _seg_proj(C, a, b)
        r = np.full(F, float(plan[n])) if plan and n in plan else np.interp(t, *RS[n])
        s = -D / r
        if n in roots:
            # a limb owns nothing behind its root joint (above the shoulder, the hip): the scapula / rump
            # skin there stays with the trunk, so a swinging limb does not drag it over the withers
            ax = b - a
            behind = -((C - a) @ ax) / max(float(np.linalg.norm(ax)), 1e-9)
            s = s - penalty * np.clip(behind / (0.5 * r), 0.0, 1.0)
        # visibility, tested only beyond one part radius (a bone near the skin sees its own faces from
        # either side): the face looks at the bone (normal toward it) -> it is skin of another part
        far = D > r
        dirn = (C - Q) / np.maximum(D, 1e-9)[:, None]
        cos = np.einsum('ij,ij->i', N, dirn)
        bad = far & (cos < face_cos)
        # the line from the face to its closest bone point leaves the body before it gets there
        cand = np.flatnonzero(far & ~bad & (s > -6.0))
        for f in cand:
            p = Vector(C[f]) - Vector(N[f]) * 1e-4
            q = Vector(Q[f])
            dv = q - p
            L = dv.length
            if L < 1e-6:
                continue
            loc, nrm, _, dist = tree.ray_cast(p, dv / L, L)
            # leaving the volume = hitting a face from inside (its normal along the ray)
            if loc is not None and dist > 1e-3 and nrm.dot(dv) > 0.0:
                occl[f, j] = True
        S[:, j] = s - penalty * (bad | occl[:, j])
    Z = S / tau
    Z -= Z.max(axis=1, keepdims=True)
    Pr = np.exp(Z); Pr /= Pr.sum(axis=1, keepdims=True)
    lab = list(np.argmax(Pr, axis=1))
    st = dict(faces=F, bones=B)
    st['vote'] = _vote_fill(lab, adj, A)
    st['small'] = _drop_small(lab, adj, A, min_area)
    # crease-aware relabel inside a two-ring band round every border (iterated conditional modes)
    U = -np.log(Pr + 1e-9) * unary_w
    Lm = float(np.mean([L for f in range(F) for _, L, _ in adj[f]])) or 1.0
    moved = 0
    for _ in range(iters):
        band = _ring_faces(lab, adj, band_rings)
        ch = 0
        for f in sorted(band):
            cands = {lab[f]} | {lab[g] for g, _, _ in adj[f]}
            def cost(l):
                return U[f, l] + lam * sum(L / Lm * w for g, L, w in adj[f] if lab[g] != l)
            best = min(cands, key=cost)
            if best != lab[f] and cost(best) < cost(lab[f]) - 1e-9:
                lab[f] = best; ch += 1
        moved += ch
        if not ch:
            break
    st['icm'] = moved
    st['vote2'] = _vote_fill(lab, adj, A)
    st['small2'] = _drop_small(lab, adj, A, min_area)
    st['mirror'] = _symmetrise(lab, C, names)
    lab = np.array(lab)
    pairs = set()
    for f in range(F):
        for g, _, _ in adj[f]:
            if lab[g] != lab[f]:
                pairs.add(tuple(sorted((names[lab[f]], names[lab[g]]))))
    bands = {pr: _ring_faces(list(lab), adj, band_rings, pair=tuple(names.index(x) for x in pr)) for pr in sorted(pairs)}
    allband = set().union(*bands.values()) if bands else set()
    st['pairs'] = len(pairs)
    st['band_faces'] = len(allband)
    st['per_bone_faces'] = {n: int((lab == j).sum()) for j, n in enumerate(names)}
    st['empty_bones'] = [n for j, n in enumerate(names) if not (lab == j).any()]
    st['occluded_pairs'] = int(occl.sum())
    print('PARTSEG labels', {k: v for k, v in st.items() if k != 'per_bone_faces'})
    return dict(names=names, label=lab, prob=Pr, bands=bands, band=allband, stats=st)


# ------------------------------------------------------------------ debug render
def _palette(names):
    """One colour per bone; a .R bone a darker shade of its .L."""
    base = sorted({n[:-2] if n.endswith(('.L', '.R')) else n for n in names})
    col = {}
    for i, b in enumerate(base):
        h = (i * 0.618034) % 1.0
        r, g, bl = (int(255 * (0.5 + 0.45 * math.cos(2 * math.pi * (h + o)))) for o in (0.0, 1 / 3, 2 / 3))
        col[b] = (r, g, bl)
    out = {}
    for n in names:
        c = col[n[:-2] if n.endswith(('.L', '.R')) else n]
        out[n] = tuple(int(x * 0.6) for x in c) if n.endswith('.R') else c
    return out


def label_shots(path, body, labels, frame, views=('hero', 'az090', 'az000', 'under'), res=512):
    """<path> (png): top row colour by owning bone, bottom row the seam bands (one colour per bone pair,
    grey outside). Rendered flat, the body alone (pieces hidden). BMK_NORENDER=1 skips it."""
    if os.environ.get('BMK_NORENDER'):
        return None
    import bmkit as K
    names, lab = labels['names'], labels['label']
    pal = _palette(names)
    hidden = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    base = K._baked(body, '_label_body')
    base.modifiers.clear()
    K.view('under', (0.35, -0.45, -1.0))
    band_of = {}
    pcols = {}
    for i, (pr, fs) in enumerate(sorted(labels['bands'].items())):
        h = (i * 0.381966) % 1.0
        pcols[pr] = tuple(int(255 * (0.5 + 0.45 * math.cos(2 * math.pi * (h + o)))) for o in (0.0, 1 / 3, 2 / 3))
        for f in fs:
            band_of.setdefault(f, pr)
    rows = []
    d = os.path.dirname(path) or '.'
    os.makedirs(d, exist_ok=True)
    K._workbench('topo')
    for row, cols in (('labels', [pal[names[l]] for l in lab]),
                      ('band', [pcols[band_of[f]] if f in band_of else (150, 150, 150) for f in range(len(lab))])):
        K._face_paint(base, cols)
        tiles = []
        for v in views:
            K.camera(frame, v, fill=K.FILL)
            p = os.path.join(d, f'_{row}_{v}.png')
            K._render(p, res)
            im = bpy.data.images.load(p)
            a = np.array(im.pixels[:]).reshape(res, res, 4)
            bpy.data.images.remove(im); os.remove(p)
            tiles.append(a)
        rows.append(np.concatenate(tiles, axis=1))
    full = np.concatenate(rows[::-1], axis=0)          # image rows run bottom-up: labels end on top
    h, w = full.shape[:2]
    im = bpy.data.images.new('_labels', w, h, alpha=True)
    im.pixels = full.ravel().tolist()
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    m = base.data
    bpy.data.objects.remove(base, do_unlink=True)
    bpy.data.meshes.remove(m)
    for o in hidden:
        o.hide_render = False
    return path
