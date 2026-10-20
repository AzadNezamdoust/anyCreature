#!/usr/bin/env python3
"""score.py — one continuous score (0..100) per stage-1 cage build, so a script can rank many variants.

    py -3.11 kit/score.py <build_dir> [<build_dir> ...] [--out table.json]
    py -3.11 kit/score.py --calib       # re-score the ten blind-ranked calibration builds; PASS when the order agrees with the owner

A build dir holds stage1/s1.glb and blockout/blockout.json. The mesh metrics are measured in headless
Blender on the imported glb (this same file runs inside Blender for that part); the rest is read from
blockout.json. Every metric is mapped linearly to 0..1 and clamped: the value at `zero` maps to 0, the
value at `one` maps to 1. score = 100 x the weighted mean of the mapped values. Self-intersection is a gate, not a
weight: any intersecting pair multiplies the score by GATE_FACTOR and lists 'self_intersection' in gate_fail.

The glb stores triangles, so the modeller's quads are rebuilt by pairing the two consecutive triangles
that share an edge (the exporter writes a quad's two triangles together), then joining each pair.
"""
import json, math, os, subprocess, sys, time

# ---------------------------------------------------------------------------- tuning: weights and ranges
WEIGHTS = dict(warp=2.0, poles=2.0, rom=1.5, quad_share=1.0, edge_spread=1.0, iou=1.0, proportion=0.5,
               long_faces=0.5, concave=0.0, banding=0.0)   # recorded, not weighted: they did not separate the owner picks
RANGES = {                      # metric: (value that maps to 0, value that maps to 1)
    'iou':               (0.75, 0.95),
    'proportion':        (20.0, 0.0),        # median |diff_pct|
    'quad_share':        (0.80, 1.00),
    'warp':              (0.25, 0.00),
    'long_faces':        (0.30, 0.00),
    'edge_spread':       (6.0,  2.0),
    'poles':             (0.20, 0.05),
    'rom':               (5.0,  0.0),        # flip_area_pct
    'concave':           (0.15, 0.02),       # share of interior edges folding inward beyond CONCAVE_DEG
    'banding':           (0.10, 0.00),       # share of vertices that are a concave crease along both edge directions
}
GATE_FACTOR = 0.9               # score multiplier when a gate fails (self_intersection > 0)
WARP_DEG = 12.0                 # a quad is warped when its two triangles' normals differ by more than this
LONG_RATIO = 3.0                # a face is long when longest / shortest edge exceeds this
CONCAVE_DEG = 8.0               # an interior edge is concave when its faces fold inward by more than this
PROPORTION_BROKEN_PCT = 50.0    # a proportion row beyond this is a broken measure, skipped

BLENDER = 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe'


def lin(x, zero, one):
    return max(0.0, min(1.0, (x - zero) / (one - zero)))


# ---------------------------------------------------------------------------- inside Blender: mesh metrics
def mesh_metrics(glb):
    import bpy, bmesh
    from mathutils.bvhtree import BVHTree
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        oe.to_mesh_clear()
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    bm.faces.ensure_lookup_table()
    tris = list(bm.faces)

    # self-intersection on the triangles: pairs that overlap and share no vertex
    tree = BVHTree.FromBMesh(bm)
    hits = sum(1 for i, j in tree.overlap(tree)
               if i < j and not (set(tris[i].verts) & set(tris[j].verts)))

    # rebuild the quads: consecutive triangles sharing an edge
    shared, warped, i = [], 0, 0
    while i < len(tris):
        if i + 1 < len(tris):
            a, b = tris[i], tris[i + 1]
            e = [x for x in a.edges if b in x.link_faces]
            if len(e) == 1:
                shared.append(e[0])
                if math.degrees(a.normal.angle(b.normal, 0.0)) > WARP_DEG:
                    warped += 1
                i += 2
                continue
        i += 1
    nquads = len(shared)
    bmesh.ops.dissolve_edges(bm, edges=shared, use_verts=False, use_face_split=False)
    bm.faces.ensure_lookup_table()
    nfaces = len(bm.faces)

    long_faces = 0
    for f in bm.faces:
        ls = [e.calc_length() for e in f.edges]
        if min(ls) <= 0 or max(ls) / min(ls) > LONG_RATIO:
            long_faces += 1
    lens = sorted(e.calc_length() for e in bm.edges)
    p = lambda q: lens[min(len(lens) - 1, int(q * (len(lens) - 1) + 0.5))]
    spread = p(0.9) / max(p(0.1), 1e-9)
    poles = sum(1 for v in bm.verts if len(v.link_edges) != 4)

    # concave edges: each face's centre lies on the outer side of the other face's plane
    bm.normal_update()
    tan_t = math.tan(math.radians(CONCAVE_DEG))
    cen = {f.index: f.calc_center_median() for f in bm.faces}
    concave_e = set()
    interior = 0
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        interior += 1
        f1, f2 = e.link_faces
        d = cen[f2.index] - cen[f1.index]
        dl = d.length
        if dl > 0 and f1.normal.dot(d) > tan_t * dl and f2.normal.dot(-d) > tan_t * dl:
            concave_e.add(e.index)
    # banding: valence-4 vertex whose four edges are all concave (a crease along both edge directions)
    band = sum(1 for v in bm.verts
               if len(v.link_edges) == 4 and all(e.index in concave_e for e in v.link_edges))
    out = dict(quad_share=nquads / max(nfaces, 1),
               warp=warped / max(nquads, 1),
               long_faces=long_faces / max(nfaces, 1),
               edge_spread=spread,
               poles=poles / max(len(bm.verts), 1),
               concave=len(concave_e) / max(interior, 1),
               banding=band / max(len(bm.verts), 1),
               self_intersection=hits)
    bm.free()
    return out


# ---------------------------------------------------------------------------- outside: assemble the score
def blockout_metrics(path):
    d = json.load(open(path))
    iou = d['iou']
    raw = dict(iou=sum(iou[k] for k in ('side', 'front', 'top')) / 3.0)
    intended, skipped, diffs = d.get('intended') or {}, [], []
    for name, row in (d.get('proportions') or {}).items():
        if name in intended:
            continue
        v = abs(row['diff_pct'])
        if v > PROPORTION_BROKEN_PCT:
            skipped.append(name)
            continue
        diffs.append(v)
    diffs.sort()
    n = len(diffs)
    raw['proportion'] = 0.0 if not n else (diffs[n // 2] if n % 2 else (diffs[n // 2 - 1] + diffs[n // 2]) / 2)
    raw['rom'] = d['rom']['flip_area_pct']
    return raw, skipped


def run_blender(glb):
    out = os.path.join(os.path.dirname(os.path.abspath(glb)), '_score_mesh.json')
    cmd = [BLENDER, '--background', '--factory-startup', '-t', '2', '--python', os.path.abspath(__file__),
           '--', glb, out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.isfile(out):
        raise RuntimeError('blender failed:\n' + (r.stdout + r.stderr)[-1500:])
    try:
        return json.load(open(out))
    finally:
        os.remove(out)


def score_build(build):
    raw, skipped = blockout_metrics(os.path.join(build, 'blockout', 'blockout.json'))
    raw.update(run_blender(os.path.join(build, 'stage1', 's1.glb')))
    mapped = {k: lin(raw[k], *RANGES[k]) for k in RANGES}
    wsum = sum(WEIGHTS.values())
    score = 100.0 * sum(WEIGHTS[k] * mapped[k] for k in WEIGHTS) / wsum
    gate_fail = []
    if raw['self_intersection'] > 0:
        gate_fail.append('self_intersection')
        score *= GATE_FACTOR
    lost = {k: 100.0 * WEIGHTS[k] * (1 - mapped[k]) / wsum for k in WEIGHTS}
    top = sorted(lost.items(), key=lambda kv: -kv[1])[:3]
    return dict(build=build, score=round(score, 2), gate_fail=gate_fail,
                raw={k: round(v, 4) for k, v in raw.items()},
                mapped={k: round(v, 3) for k, v in mapped.items()},
                skipped=skipped,
                penalties=[dict(metric=k, points_lost=round(v, 2)) for k, v in top])


def calib_builds():
    """The ten builds of the blind calibration: {letter: (name, build dir)} from calib/key.json."""
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
    cal = os.path.join(root, 'out', 'boxmodel', 'calib')
    key = json.load(open(os.path.join(cal, 'key.json')))
    out = {}
    for letter, name in key.items():
        base = os.path.join(root, 'experiments', 'boxmodel', 'abc') if '/' in name             else os.path.join(cal, 'abc', 'c4')
        out[letter] = (name, os.path.join(base, name))
    return out


def calib():
    rows = {}
    todo = list(calib_builds().values())
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
    for g in ('c3/goblin', 'c4/goblin'):          # the goblin check: not in the blind key, ranked by eye
        todo.append((g, os.path.join(root, 'experiments', 'boxmodel', 'abc', g)))
    for name, path in todo:
        rows[name] = score_build(path)
        r = rows[name]
        print('%-10s %6.2f  %s' % (name, r['score'], ('gate: ' + ','.join(r['gate_fail'])) if r['gate_fail'] else ''))
    sc = {n: r['score'] for n, r in rows.items()}
    ok_w = sc['c4/wolf'] > sc['c2/wolf'] and sc['c4/wolf'] > sc['c3/wolf']
    ok_b = sc['c3/bear'] > sc['c2/bear'] and sc['c3/bear'] > sc['c4/bear']
    ok_g = sc['c3/goblin'] > sc['c4/goblin']
    msg = 'wolf %s (c4 %.2f, c2 %.2f, c3 %.2f);  bear %s (c3 %.2f, c2 %.2f, c4 %.2f);  goblin %s (c3 %.2f, c4 %.2f)' % (
        'ok' if ok_w else 'wrong', sc['c4/wolf'], sc['c2/wolf'], sc['c3/wolf'],
        'ok' if ok_b else 'wrong', sc['c3/bear'], sc['c2/bear'], sc['c4/bear'],
        'ok' if ok_g else 'wrong', sc['c3/goblin'], sc['c4/goblin'])
    print(('PASS  ' if ok_w and ok_b and ok_g else 'FAIL  ') + msg)
    return 0 if ok_w and ok_b and ok_g else 1


def main(argv):
    out, builds, i = None, [], 0
    while i < len(argv):
        if argv[i] == '--out':
            out = argv[i + 1]; i += 2
        elif argv[i] == '--calib':
            return calib()
        else:
            builds.append(argv[i]); i += 1
    if not builds:
        print(__doc__); return 2
    table = []
    for b in builds:
        t0 = time.time()
        r = score_build(b)
        r['build'] = b.replace(os.sep, '/')
        table.append(r)
        pen = ', '.join('%s -%.1f' % (p['metric'], p['points_lost']) for p in r['penalties'])
        print('%-28s %6.2f  | %s%s%s  concave %.4f banding %.4f  (%.1fs)' % (
            r['build'], r['score'], pen,
            ('  GATE: ' + ', '.join(r['gate_fail'])) if r['gate_fail'] else '',
            ('  skipped: ' + ', '.join(r['skipped'])) if r['skipped'] else '',
            r['raw']['concave'], r['raw']['banding'], time.time() - t0))
    if out:
        json.dump(table, open(out, 'w'), indent=1)
    return 0


def _in_blender():
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == '__main__':
    if _in_blender():
        glb, out = sys.argv[sys.argv.index('--') + 1:][:2]
        json.dump(mesh_metrics(glb), open(out, 'w'))
    else:
        sys.exit(main(sys.argv[1:]))
