"""techqa_glb.py — techqa.measure() on an exported GLB (read-only: nothing is written next to the GLB).

The stage runner (bmkit.qa_step) measures the scene objects before export. This re-measures a shipped
stage-4 GLB, e.g. to re-run tech QA over the zoo after a techqa change without rebuilding anything:

    blender -b --factory-startup -P techqa_glb.py -- <glb> <out.json> [--techqa-dir <dir>] [--no-posed]

The importer splits every flat-shaded vertex per face, so each mesh is welded by position first (the
shells, open edges and seats are then the authored ones). Prints 'BMK techqa <glb>: ...' with the totals
and writes them (and per-object counts) to out.json. --techqa-dir imports techqa.py from another folder
(a before/after comparison of a techqa change).
"""
import bpy, bmesh, json, os, sys

KIT = os.path.dirname(os.path.abspath(__file__))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(argv) < 2:
        print(__doc__); sys.exit(2)
    glb, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    qdir = argv[argv.index('--techqa-dir') + 1] if '--techqa-dir' in argv else KIT
    sys.path.insert(0, KIT)
    sys.path.insert(0, qdir)
    import techqa as Q
    src = open(os.path.join(KIT, 'render_glb.py'), encoding='utf-8').read().replace('\nmain()\n', '\n')
    RG = {'__file__': os.path.join(KIT, 'render_glb.py'), '__name__': 'render_glb'}
    exec(compile(src, 'render_glb', 'exec'), RG)
    meshes, frame = RG['load'](glb)
    for o in meshes:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    body = next((o for o in meshes if o.name.lower().startswith('body')), None) or max(meshes, key=lambda o: len(o.data.polygons))
    pieces = [o for o in meshes if o is not body]
    rig = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
    acts = None
    if rig is not None and bpy.data.actions and '--no-posed' not in argv:
        rig.data.pose_position = 'POSE'
        if rig.animation_data is None:
            rig.animation_data_create()
        acts = {a.name: a for a in sorted(bpy.data.actions, key=lambda a: a.name)}
    counts, flags, tris = Q.measure(body, pieces, frame['size'], rig if acts else None, acts)
    tot, ntris = Q.summary(counts, tris)
    rep = dict(glb=glb, techqa=os.path.join(qdir, 'techqa.py'), triangles=ntris, totals=tot, per_object=counts)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=1, default=float)
    keys = ['hit', 'float', 'zfight', 'sliver', 'open', 'flip', 'drift', 'clip', 'stretch']
    print('BMK techqa', os.path.basename(glb) + ':', ', '.join(f"{k} {tot.get(k, 0)}" for k in keys),
          '| drift shells:', {n: c.get('drift', 0) for n, c in counts.items() if c.get('drift', 0)}, flush=True)


main()
