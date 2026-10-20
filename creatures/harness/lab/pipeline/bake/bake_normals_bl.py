# Blender 5.x headless: hi->LOD normal/albedo bake, detail views, tangent re-bake, lit comparison renders.
# blender -b -P bake_normals_bl.py -- <mode> <json args>
#   bake   {hi, lp, out, res}              -> out/{lod.obj(uv), n_tan.png, n_obj.exr, albedo.png, pos.exr}
#   views  {hi, out, n, res}               -> out/view_k.png, view_k_pos.exr, view_k_nrm.exr, cams.json
#   retan  {lod, nobj, out, res}           -> tangent-space PNG from object-space EXR (normal bake on LOD itself)
#   render {lod, albedo, normals:[..], out, labels} -> lit EEVEE frames (3/4 + head closeup) per normal variant
import bpy, sys, json, os, math, time
from mathutils import Vector, Matrix
mode = sys.argv[sys.argv.index('--') + 1]; A = json.loads(sys.argv[sys.argv.index('--') + 2])

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'
    p = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA'):
        try: p.compute_device_type = t; p.get_devices(); break
        except Exception: pass
    for d in p.devices: d.use = d.type != 'CPU'
    sc.cycles.device = 'GPU'; sc.cycles.samples = 1
    return sc

def imp(path):
    before = set(bpy.data.objects)
    if path.endswith('.glb'): bpy.ops.import_scene.gltf(filepath=path)
    else: bpy.ops.wm.obj_import(filepath=path, forward_axis='NEGATIVE_Z', up_axis='Y')
    o = [x for x in bpy.data.objects if x not in before and x.type == 'MESH'][0]
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o

def height(o): return max(v.co.z for v in o.data.vertices) - min(v.co.z for v in o.data.vertices)

def img(name, res, float_=False, noncolor=False):
    i = bpy.data.images.new(name, res, res, alpha=False, float_buffer=float_)
    if noncolor: i.colorspace_settings.name = 'Non-Color'
    return i

def mat_with(o, image):
    m = bpy.data.materials.new('bake'); m.use_nodes = True
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = image
    m.node_tree.nodes.active = n
    o.data.materials.clear(); o.data.materials.append(m); return m, n

def save(i, path, fmt):
    i.filepath_raw = path; i.file_format = fmt
    if fmt == 'OPEN_EXR': pass
    i.save()

def emit_mat(kind):   # emission material: position or world normal
    m = bpy.data.materials.new(kind); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    g = nt.nodes.new('ShaderNodeNewGeometry'); e = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    # emission colour is clamped >= 0 in a render: encode v*k+0.5 (pos k=0.25, normal k=0.5); decode in detail_normals.py
    mp = nt.nodes.new('ShaderNodeVectorMath'); mp.operation = 'MULTIPLY_ADD'
    mp.inputs[1].default_value = (0.25,) * 3 if kind == 'pos' else (0.5,) * 3; mp.inputs[2].default_value = (0.5,) * 3
    nt.links.new(g.outputs['Position' if kind == 'pos' else 'Normal'], mp.inputs[0]); nt.links.new(mp.outputs[0], e.inputs['Color'])
    nt.links.new(e.outputs[0], out.inputs[0])
    return m

def bake_one(lp, hi, image, typ, **kw):
    mat_with(lp, image)
    bpy.ops.object.select_all(action='DESELECT'); hi.select_set(True); lp.select_set(True); bpy.context.view_layer.objects.active = lp
    sc = bpy.context.scene; b = sc.render.bake
    b.use_selected_to_active = True; b.use_cage = False; b.cage_extrusion = A['ext']; b.max_ray_distance = A['ray']
    b.margin = 8; b.target = 'IMAGE_TEXTURES'
    t = time.time(); bpy.ops.object.bake(type=typ, **kw); return time.time() - t

T = {}
if mode == 'bake':
    sc = reset(); hi = imp(A['hi']); lp = imp(A['lp'])
    s = height(hi) / height(lp); lp.scale = (s, s, s)
    bpy.ops.object.select_all(action='DESELECT'); lp.select_set(True); bpy.context.view_layer.objects.active = lp
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004)
    bpy.ops.uv.pack_islands(margin=0.004); bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    o = A['out']; r = A['res']; sc.cycles.samples = 1
    i = img('ntan', r, noncolor=True); T['n_tan'] = bake_one(lp, hi, i, 'NORMAL', normal_space='TANGENT'); save(i, f'{o}/n_tan.png', 'PNG')
    i = img('nobj', r, True, True); T['n_obj'] = bake_one(lp, hi, i, 'NORMAL', normal_space='OBJECT'); save(i, f'{o}/n_obj.exr', 'OPEN_EXR')
    i = img('alb', r); T['albedo'] = bake_one(lp, hi, i, 'DIFFUSE', pass_filter={'COLOR'}); save(i, f'{o}/albedo.png', 'PNG')
    keep = list(hi.data.materials); hi.data.materials.clear(); hi.data.materials.append(emit_mat('pos'))
    i = img('pos', r, True, True); T['pos'] = bake_one(lp, hi, i, 'EMIT'); save(i, f'{o}/pos.exr', 'OPEN_EXR')
    lp.data.materials.clear()
    bpy.ops.object.select_all(action='DESELECT'); lp.select_set(True); bpy.context.view_layer.objects.active = lp
    bpy.ops.wm.obj_export(filepath=f'{o}/lod.obj', export_selected_objects=True, export_materials=False,
                          forward_axis='NEGATIVE_Z', up_axis='Y', export_triangulated_mesh=False)
    bpy.ops.wm.save_as_mainfile(filepath=f'{o}/lod.blend')
    json.dump(dict(times=T, scale=s, faces=len(lp.data.polygons)), open(f'{o}/bake_bl.json', 'w'), indent=1)

elif mode == 'views':   # orthographic ring of hi renders: colour (lit) + world position + world normal per pixel
    sc = reset(); hi = imp(A['hi']); o = A['out']; r = A['res']; os.makedirs(o, exist_ok=True)
    mn = Vector([min(v.co[k] for v in hi.data.vertices) for k in range(3)]); mx = Vector([max(v.co[k] for v in hi.data.vertices) for k in range(3)])
    c = (mn + mx) / 2; ext = (mx - mn).length * 0.55
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = ext * 2
    sc.render.resolution_x = sc.render.resolution_y = r; sc.render.film_transparent = True
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.0
    keep = list(hi.data.materials); cams = []
    dirs = [(math.radians(a), math.radians(e)) for e in (15, -20) for a in range(0, 360, 360 // (A['n'] // 2))]
    for k, (az, el) in enumerate(dirs):
        d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        cam.location = c + d * ext * 3; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sun.rotation_euler = (-(d + Vector((0, 0, 0.6)))).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        hi.data.materials.clear(); [hi.data.materials.append(m) for m in keep]
        sc.cycles.samples = 64; sc.view_settings.view_transform = 'Standard'
        sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
        sc.render.filepath = f'{o}/view_{k}.png'; bpy.ops.render.render(write_still=True)
        for kind in ('pos', 'nrm'):
            hi.data.materials.clear(); hi.data.materials.append(emit_mat('pos' if kind == 'pos' else 'nrm'))
            sc.cycles.samples = 1; sc.cycles.use_denoising = False; sc.cycles.filter_width = 0.01; sc.view_settings.view_transform = 'Raw'
            sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.color_depth = '32'
            sc.render.filepath = f'{o}/view_{k}_{kind}.exr'; bpy.ops.render.render(write_still=True)
        sc.cycles.filter_width = 1.5; sc.cycles.use_denoising = True
        cams.append(dict(k=k, mw=[list(rw) for rw in cam.matrix_world], ortho=cam.data.ortho_scale, res=r))
    json.dump(cams, open(f'{o}/cams.json', 'w'), indent=1)

elif mode == 'exr2npy':   # cv2 in the venv has no EXR codec: convert with Blender's numpy (top-down rows, RGBA float32)
    import numpy as np, glob
    for p in A['files']:
        i = bpy.data.images.load(p); i.colorspace_settings.name = 'Non-Color'; w, h = i.size; a = np.empty(w * h * 4, np.float32); i.pixels.foreach_get(a)
        np.save(p[:-4] + '.npy', a.reshape(h, w, 4)[::-1]); bpy.data.images.remove(i)

elif mode == 'npy2exr':
    import numpy as np
    a = np.load(A['npy']).astype(np.float32); h, w = a.shape[:2]
    i = bpy.data.images.new('x', w, h, alpha=True, float_buffer=True); i.colorspace_settings.name = 'Non-Color'
    i.pixels.foreach_set(a[::-1].ravel()); save(i, A['out'], 'OPEN_EXR')

elif mode == 'retan':   # object-space map -> tangent-space map on the LOD's own UVs/tangents
    bpy.ops.wm.open_mainfile(filepath=A['lod']); sc = bpy.context.scene; sc.render.engine = 'CYCLES'
    p = bpy.context.preferences.addons['cycles'].preferences
    try: p.compute_device_type = 'OPTIX'; p.get_devices(); [setattr(d, 'use', d.type != 'CPU') for d in p.devices]; sc.cycles.device = 'GPU'
    except Exception: pass
    sc.cycles.samples = 1
    lp = min([x for x in bpy.data.objects if x.type == 'MESH'], key=lambda x: len(x.data.polygons))   # LOD, not the hi mesh
    for x in bpy.data.objects:
        if x != lp: bpy.data.objects.remove(x)
    m = bpy.data.materials.new('n'); m.use_nodes = True; nt = m.node_tree
    src = nt.nodes.new('ShaderNodeTexImage'); src.image = bpy.data.images.load(A['nobj']); src.image.colorspace_settings.name = 'Non-Color'; src.interpolation = 'Closest'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.space = 'OBJECT'
    nt.links.new(src.outputs[0], nm.inputs['Color']); nt.links.new(nm.outputs[0], nt.nodes['Principled BSDF'].inputs['Normal'])
    tgt = nt.nodes.new('ShaderNodeTexImage'); tgt.image = img('t', A['res'], noncolor=True); nt.nodes.active = tgt
    lp.data.materials.clear(); lp.data.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT'); lp.select_set(True); bpy.context.view_layer.objects.active = lp
    b = sc.render.bake; b.use_selected_to_active = False; b.margin = 8
    bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT'); save(tgt.image, A['out'], 'PNG')

elif mode == 'render':  # EEVEE, single key light, same camera per variant
    bpy.ops.wm.open_mainfile(filepath=A['lod']); sc = bpy.context.scene
    for x in list(bpy.data.objects):
        if x.type != 'MESH': bpy.data.objects.remove(x)
    objs = [x for x in bpy.data.objects if x.type == 'MESH']; lp = min(objs, key=lambda x: len(x.data.polygons))
    for x in objs:
        if x != lp: bpy.data.objects.remove(x)
    sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in sc.render.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x = A.get('w', 900); sc.render.resolution_y = A.get('h', 700); sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.04, 0.045, 0.05, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    m = bpy.data.materials.new('v'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    bs.inputs['Roughness'].default_value = 0.75
    al = nt.nodes.new('ShaderNodeTexImage'); al.image = bpy.data.images.load(A['albedo']); nt.links.new(al.outputs[0], bs.inputs['Base Color'])
    nimg = nt.nodes.new('ShaderNodeTexImage'); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.space = 'TANGENT'
    nt.links.new(nimg.outputs[0], nm.inputs['Color'])
    lp.data.materials.clear(); lp.data.materials.append(m)
    mn = Vector([min(v.co[k] for v in lp.data.vertices) for k in range(3)]); mx = Vector([max(v.co[k] for v in lp.data.vertices) for k in range(3)])
    c = (mn + mx) / 2; L = (mx - mn).length
    head = Vector(A['head'])   # head centre (world), measured from the views
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 4.0
    sun.data.angle = math.radians(2)
    shots = {'full': (c, Vector(A['dir']).normalized() * L * 1.25, 40), 'head': (head, Vector(A['hdir']).normalized() * L * 0.42, 40)}
    for shot, (tgt, off, lens) in shots.items():
        cam.location = tgt + off; cam.rotation_euler = (-off).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
        kd = Vector(A['key']).normalized(); sun.rotation_euler = (-kd).to_track_quat('-Z', 'Y').to_euler()
        for lab, npth in zip(A['labels'], A['normals']):
            if npth:
                nimg.image = bpy.data.images.load(npth, check_existing=True); nimg.image.colorspace_settings.name = 'Non-Color'
                nt.links.new(nm.outputs[0], bs.inputs['Normal'])
            else:
                for l in list(bs.inputs['Normal'].links): nt.links.remove(l)
            sc.render.filepath = f"{A['out']}_{shot}_{lab}.png"; bpy.ops.render.render(write_still=True)
