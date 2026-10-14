"""refs_standin.py — the refs.py self-test's Blender half (no image generator needed).

    blender -b --factory-startup -P refs_standin.py -- --glb <final.glb> --out <dir> --mode sheet
    blender -b --factory-startup -P refs_standin.py -- --glb <final.glb> --out <dir> --mode ortho --blueprint <bp.json>

sheet: the stand-in views for a turnaround sheet (front, side facing left, back, three-quarter, top;
       the caller composes the 1 x 4 row or the 2 x 2 grid, the top rotated 90 deg CCW so the head points left;
       flat workbench colours with faint shadows on white, one orthographic scale, one ground line)
       -> <dir>/standin_<view>.png and standin.json (the model's bounding box).
ortho: the kit's orthographic silhouettes (bmkit.ortho_views) of the model framed by a blueprint,
       for run.blueprint_overlay to score. The model is moved so its bounding box is centred on
       x = y = 0 (refs.py's convention for a traced blueprint).
Both use the rest pose.
"""
import bpy, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import bmkit as K
from mathutils import Vector


def load(glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    shapes = set()
    for o in bpy.context.scene.objects:
        if o.type == 'ARMATURE':
            o.data.pose_position = 'REST'
            shapes |= {pb.custom_shape for pb in o.pose.bones if pb.custom_shape}
    for o in list(bpy.context.scene.objects):
        if o in shapes or (o.type == 'MESH' and (o.hide_render or o.hide_get())):
            bpy.data.objects.remove(o, do_unlink=True)
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree.nodes.get('Principled BSDF'):
            m.diffuse_color = tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
    bpy.context.view_layer.update()


def bounds():
    lo = Vector((1e9, 1e9, 1e9)); hi = -lo
    dg = bpy.context.evaluated_depsgraph_get()
    for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        for v in me.vertices:
            p = o.matrix_world @ v.co
            lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
        oe.to_mesh_clear()
    return lo, hi


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    glb, out, mode = os.path.abspath(arg('--glb')), os.path.abspath(arg('--out')), arg('--mode', 'sheet')
    os.makedirs(out, exist_ok=True)
    load(glb)
    lo, hi = bounds()
    shift = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, 0))
    for o in bpy.context.scene.objects:
        if o.parent is None:
            o.location += shift
    bpy.context.view_layer.update()
    lo, hi = bounds()
    size = list(hi - lo)
    if mode == 'ortho':
        K.ortho_views(out, arg('--blueprint'))
        K.say('ortho written', out)
        return
    frame = dict(centre=list((lo + hi) / 2), size=size, ortho=max(size) * 1.12)
    K._workbench('colour')
    sc = bpy.context.scene
    sc.world.color = (1, 1, 1)
    sc.display.shading.shadow_intensity = 0.15
    res = 600
    files = []
    for tag, view in (('front', 'az000'), ('side', 'az090'), ('back', 'az180'), ('threeq', 'az045'), ('top', 'top')):
        K.camera(frame, view, ortho=True)
        p = os.path.join(out, f'standin_{tag}.png')
        K._render(p, res)
        files.append(p)
    json.dump(dict(glb=os.path.basename(glb), size=size, lo=list(lo), hi=list(hi), files=files, res=res,
                   ortho=frame['ortho']), open(os.path.join(out, 'standin.json'), 'w'), indent=1)
    K.say('standin views', files)


main()
