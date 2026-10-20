"""render_glb.py — render any GLB the same way (the engine creature, a box-model
final, a CC0 reference), so comparisons and blind reads see identical cameras,
light and background. Run by run.py --compare and by the judging step:

    blender -b --factory-startup -P render_glb.py -- --jobs jobs.json

jobs.json: [{"glb": path, "out": dir, "prefix": "wolf_engine",
             "mode": "beauty" | "colour" | "clay", "views": ["hero", "az090"], "res": 768}]
Frames each model by its own bounding box; the skeleton is shown at rest.
beauty = EEVEE with the imported materials (baseColorFactor x COLOR_0 as glTF
defines it), a key light, a soft fill and a contact shadow.
"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmkit as K
from mathutils import Vector


def load(glb, pose=None):
    """pose: None = the rest pose; else a substring of an action name (e.g. 'Idle'):
    the model is shown at that clip's first frame (for references modelled in a T-pose)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    shapes = set()
    for o in bpy.context.scene.objects:
        if o.type == 'ARMATURE':
            act = next((a for a in bpy.data.actions if pose and pose.lower() in a.name.lower()), None)
            if act:
                o.data.pose_position = 'POSE'
                o.animation_data_create()
                o.animation_data.action = act
                bpy.context.scene.frame_set(int(act.frame_range[0]))
            else:
                o.data.pose_position = 'REST'
                if o.animation_data:
                    o.animation_data.action = None
            shapes |= {pb.custom_shape for pb in o.pose.bones if pb.custom_shape}
    # the importer's bone-display shape (an Icosphere) is a scene mesh: not part of the model
    for o in list(bpy.context.scene.objects):
        if o in shapes or (o.type == 'MESH' and (o.hide_render or o.hide_get())):
            bpy.data.objects.remove(o, do_unlink=True)
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree.nodes.get('Principled BSDF'):
            bc = m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
            m.diffuse_color = tuple(bc)
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    lo = Vector((1e9, 1e9, 1e9)); hi = -lo
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        for v in me.vertices:
            p = o.matrix_world @ v.co
            lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
        oe.to_mesh_clear()
    return meshes, dict(centre=list((lo + hi) / 2), size=list(hi - lo), floor=lo.z)


def beauty_setup(frame):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.film_transparent = False
    w = sc.world or bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (0.62, 0.64, 0.66, 1)
    bg.inputs[1].default_value = 0.9
    L = max(frame['size'])
    sun = K.link(bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(48), 0, math.radians(-35))
    fill = K.link(bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')))
    fill.data.energy = 0.8
    fill.data.use_shadow = False
    fill.rotation_euler = (math.radians(70), 0, math.radians(150))
    bpy.ops.mesh.primitive_plane_add(size=L * 12, location=(frame['centre'][0], frame['centre'][1], frame['floor']))
    g = bpy.context.object
    g.name = '_ground'
    g.data.materials.append(K.material('_ground', (0.55, 0.56, 0.57), rough=1.0))
    try:
        sc.eevee.use_shadows = True
    except AttributeError:
        pass
    sc.view_settings.view_transform = 'Standard'


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    jobs = json.load(open(argv[argv.index('--jobs') + 1]))
    for j in jobs:
        meshes, frame = load(j['glb'], j.get('pose'))
        os.makedirs(j['out'], exist_ok=True)
        mode = j.get('mode', 'beauty')
        if mode == 'beauty':
            beauty_setup(frame)
        for v in j.get('views', ['hero']):
            if mode == 'beauty':
                K.camera(frame, v, fill=j.get('fill', 1.1))
            else:
                K._workbench(mode)
                for o in meshes:
                    o.color = (0.78, 0.78, 0.76, 1)
                K.camera(frame, v, fill=j.get('fill', 1.1))
            p = os.path.join(j['out'], f"{j['prefix']}_{v}.png")
            K._render(p, j.get('res', 768))
            K.say('rendered', p)


main()
