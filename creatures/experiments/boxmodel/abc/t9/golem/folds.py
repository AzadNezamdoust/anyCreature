"""blender -b -P folds.py -- <glb> : list concave body folds > 90 deg (position, angle, edge length)."""
import bpy, bmesh, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
ob = next(o for o in bpy.data.objects if o.type == 'MESH' and 'body' in o.name)
bm = bmesh.new(); bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.normal_update()
M = ob.matrix_world
out = []
for e in bm.edges:
    if len(e.link_faces) != 2:
        continue
    f1, f2 = e.link_faces
    a = math.degrees(f1.normal.angle(f2.normal))
    if a < 60:
        continue
    if (f2.calc_center_median() - f1.calc_center_median()).dot(f1.normal) > 0:   # concave
        c = M @ ((e.verts[0].co + e.verts[1].co) / 2)
        out.append((a, tuple(round(q, 3) for q in c), round(e.calc_length(), 3)))
out.sort(reverse=True)
for o in out[:40]:
    print('FOLD', round(o[0], 1), o[1], o[2])
