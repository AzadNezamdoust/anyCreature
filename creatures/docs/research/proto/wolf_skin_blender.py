# Proof A: "armature sketch -> Skin modifier -> subsurf 1 -> shape tweaks -> flat low-poly"
# Written the way a human Blender user would block out a quadruped: a stick figure of
# vertices with radii (the Skin modifier's intended use), one connected quad mesh out.
import bpy, bmesh, math, sys, os
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
TAG = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'skin'
SUBD = int(os.environ.get('SUBD', '1'))

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------- skeleton graph (x right, y back, z up; head at -y) ----------------
# name: (pos, (radius_x, radius_y))
V = {}
E = []
def v(name, p, r):
    V[name] = (Vector(p), r)
def chain(*names):
    for a, b in zip(names, names[1:]):
        E.append((a, b))

# spine: nose -> tail tip
v('nose',  (0, -0.89, 0.82), (0.045, 0.04))
v('muzz',  (0, -0.80, 0.85), (0.085, 0.075))
v('head',  (0, -0.62, 0.92), (0.15, 0.14))
v('neck',  (0, -0.46, 0.82), (0.16, 0.18))
v('chest', (0, -0.26, 0.66), (0.20, 0.23))
v('belly', (0,  0.02, 0.67), (0.16, 0.17))
v('hips',  (0,  0.26, 0.69), (0.16, 0.16))
v('t0',    (0,  0.42, 0.72), (0.07, 0.07))
v('t1',    (0,  0.60, 0.64), (0.11, 0.11))
v('t2',    (0,  0.76, 0.50), (0.11, 0.10))
v('t3',    (0,  0.88, 0.38), (0.035, 0.035))
chain('nose', 'muzz', 'head', 'neck', 'chest', 'belly', 'hips', 't0', 't1', 't2', 't3')
if os.environ.get('STYL'):
    # stylised pass: bigger head, chunkier limbs, ruff and cheek tufts as short skin stubs
    for k, f in (('head', 1.18), ('muzz', 1.1), ('neck', 1.1), ('t1', 1.2), ('t2', 1.3)):
        p, r = V[k]; V[k] = (p, (r[0]*f, r[1]*f))
    for s_, sx in (('L', 1), ('R', -1)):
        v(s_+'ch', (sx*0.19, -0.56, 0.84), (0.03, 0.03)); chain('head', s_+'ch')      # cheek tuft
        v(s_+'r1', (sx*0.24, -0.40, 0.70), (0.035, 0.035)); chain('neck', s_+'r1')    # ruff
    v('r0', (0, -0.52, 0.60), (0.04, 0.04)); chain('neck', 'r0')                       # chest ruff tip


FT = 1.25 if os.environ.get('STYL') else 1.0
for s, sx in (('L', 1), ('R', -1)):
    # front leg: shoulder hangs off chest
    v(s+'sh',  (sx*0.13, -0.28, 0.50), (0.09, 0.10))
    v(s+'el',  (sx*0.13, -0.26, 0.30), (0.062*FT, 0.062*FT))
    v(s+'wr',  (sx*0.13, -0.29, 0.10), (0.05*FT, 0.05*FT))
    v(s+'fp',  (sx*0.13, -0.37, 0.035), (0.06*FT, 0.035))
    chain('chest', s+'sh', s+'el', s+'wr', s+'fp')
    # hind leg: thigh, stifle forward, hock back
    v(s+'th',  (sx*0.13, 0.28, 0.52), (0.11, 0.12))
    v(s+'kn',  (sx*0.13, 0.20, 0.34), (0.07*FT, 0.07*FT))
    v(s+'hk',  (sx*0.13, 0.33, 0.15), (0.05*FT, 0.05*FT))
    v(s+'hp',  (sx*0.13, 0.26, 0.035), (0.06*FT, 0.035))
    chain('hips', s+'th', s+'kn', s+'hk', s+'hp')
    # ears grow straight out of the skull
    v(s+'e0',  (sx*0.08, -0.60, 1.03), (0.055, 0.035))
    v(s+'e1',  (sx*0.10, -0.58, 1.17), (0.012, 0.01))
    chain('head', s+'e0', s+'e1')

names = list(V)
idx = {n: i for i, n in enumerate(names)}
me = bpy.data.meshes.new('wolf')
me.from_pydata([V[n][0] for n in names], [(idx[a], idx[b]) for a, b in E], [])
ob = bpy.data.objects.new('wolf', me)
bpy.context.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
sk = ob.modifiers.new('Skin', 'SKIN')
sk.branch_smoothing = 0.6
for n in names:
    d = me.skin_vertices[0].data[idx[n]]
    d.radius = V[n][1]
    d.use_root = (n == 'chest')
bpy.ops.object.modifier_apply(modifier='Skin')

# ---------------- "sculpt" pass: a few hand moves a modeller would do ----------------
bm = bmesh.new(); bm.from_mesh(me)
def soft(center, radius, fn):
    c = Vector(center)
    for vert in bm.verts:
        d = (vert.co - c).length
        if d < radius:
            w = (1 - d/radius)**2 * (3 - 2*(1 - d/radius)) if False else (1 - (d/radius)**2)**2
            vert.co = fn(vert.co, w)
# deep keeled chest: drag underside down, flatten sides a bit
soft((0, -0.28, 0.50), 0.22, lambda p, w: p + Vector((0, 0, -0.06*w)))
# tucked waist
soft((0, 0.05, 0.52), 0.18, lambda p, w: p + Vector((0, 0, 0.05*w)))
# ruff / mane: puff the neck-chest top and sides
soft((0, -0.42, 0.86), 0.18, lambda p, w: p + Vector((0, 0.02, 0.05*w)) + Vector((p.x*0.35*w, 0, 0)))
# skull: widen cheeks, flatten crown
soft((0, -0.62, 0.86), 0.12, lambda p, w: p + Vector((p.x*0.5*w, 0, 0)))
# muzzle: wedge (narrow + slightly lowered jaw line)
soft((0, -0.85, 0.80), 0.10, lambda p, w: p + Vector((-p.x*0.25*w, 0, -0.01*w)))
bm.to_mesh(me); bm.free()

if SUBD:
    m = ob.modifiers.new('Sub', 'SUBSURF'); m.levels = SUBD; m.render_levels = SUBD
    bpy.ops.object.modifier_apply(modifier='Sub')
DEC = float(os.environ.get('DEC', '0'))
if DEC:
    m = ob.modifiers.new('Dec', 'DECIMATE'); m.ratio = DEC; m.use_symmetry = True; m.symmetry_axis = 'X'
    bpy.ops.object.modifier_apply(modifier='Dec')

# ---------------- colour: face colours by region + vertical gradient ----------------
pal = {
    'back':  (0.33, 0.32, 0.31), 'side': (0.47, 0.45, 0.42), 'belly': (0.85, 0.80, 0.70),
    'leg':   (0.60, 0.50, 0.36), 'dark': (0.12, 0.12, 0.13), 'ear': (0.22, 0.20, 0.20),
    'muzz':  (0.85, 0.80, 0.70),
}
def srgb2lin(c): return tuple(((x+0.055)/1.055)**2.4 if x > 0.04045 else x/12.92 for x in c)
col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
for poly in me.polygons:
    c = poly.center; n = poly.normal
    if c.y < -0.86: k = 'dark'
    elif c.z > 0.97 and abs(c.x) > 0.03: k = 'ear'
    elif c.y < -0.72 and n.z < 0.3: k = 'muzz'
    elif c.z < 0.42: k = 'leg'
    elif n.z < -0.45: k = 'belly'
    elif c.y > 0.84: k = 'dark'
    elif n.z > 0.55: k = 'back'
    else: k = 'side'
    rgb = pal[k]
    for li in poly.loop_indices:
        col.data[li].color = (*srgb2lin(rgb), 1)
for p in me.polygons: p.use_smooth = False

mat = bpy.data.materials.new('fur'); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
attr = nt.nodes.new('ShaderNodeVertexColor'); attr.layer_name = 'Col'
nt.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.9
me.materials.append(mat)

# ---------------- eyes: snapped onto the skull surface by ray cast, half buried ----------------
bpy.context.view_layer.update()
em = bpy.data.materials.new('eye')
em.use_nodes = True; em.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.45, 0.02, 1)
pm = bpy.data.materials.new('pupil')
pm.use_nodes = True; pm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
for sx in (1, -1):
    origin = Vector((sx*0.5, -0.74, 0.97)); target = Vector((0, -0.70, 0.93))
    hit, loc, nrm, fi = ob.ray_cast(origin, (target-origin).normalized())
    for mat_, r, off in ((em, 0.03, 0.004), (pm, 0.016, 0.018)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=r, location=loc + nrm*off)
        e = bpy.context.active_object
        e.scale = (1, 1, 0.8)
        e.rotation_euler = nrm.to_track_quat('Z', 'Y').to_euler()
        e.data.materials.append(mat_)
        for p in e.data.polygons: p.use_smooth = False
        ca = e.data.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        cc = mat_.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
        for d in ca.data: d.color = tuple(cc)

print('tris', sum(len(p.vertices)-2 for p in me.polygons), 'verts', len(me.vertices), 'faces', len(me.polygons))
q = sum(1 for p in me.polygons if len(p.vertices) == 4)
print('quad share', q/len(me.polygons))


# ---------------- rig: armature straight from the same stick graph, heat-diffusion weights ----------------
RIG = os.environ.get('RIG')
if RIG:
    import collections
    adj = collections.defaultdict(list)
    for a, b in E: adj[a].append(b); adj[b].append(a)
    arm = bpy.data.armatures.new('rig'); ao = bpy.data.objects.new('rig', arm)
    bpy.context.collection.objects.link(ao)
    bpy.context.view_layer.objects.active = ao
    bpy.ops.object.mode_set(mode='EDIT')
    bones = {}
    root = arm.edit_bones.new('root'); root.head = V['chest'][0]; root.tail = V['chest'][0] + Vector((0, 0, 0.15))
    seen = {'chest'}; stack = [('chest', None)]
    while stack:
        n, parent = stack.pop()
        for m_ in adj[n]:
            if m_ in seen: continue
            seen.add(m_)
            b = arm.edit_bones.new(m_); b.head = V[n][0]; b.tail = V[m_][0]
            b.parent = bones.get(parent) or root
            b.use_connect = False
            bones[m_] = b
            stack.append((m_, m_))
    bpy.ops.object.mode_set(mode='OBJECT')
    eyes = [o for o in bpy.data.objects if o.name.startswith('Sphere')]
    for o in bpy.data.objects: o.select_set(False)
    ob.select_set(True); ao.select_set(True); bpy.context.view_layer.objects.active = ao
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    for e in eyes:
        e.parent = ao; e.parent_type = 'BONE'; e.parent_bone = 'head'
        e.matrix_parent_inverse = (ao.matrix_world @ ao.pose.bones['head'].matrix @ __import__('mathutils').Matrix.Translation((0, ao.pose.bones['head'].length, 0))).inverted()
    # empty vertex groups?
    vg_counts = collections.Counter()
    for vert in ob.data.vertices:
        for g in vert.groups:
            if g.weight > 0.05: vg_counts[ob.vertex_groups[g.group].name] += 1
    print('weighted verts per bone (sample):', dict(list(vg_counts.items())[:8]), 'unweighted:', sum(1 for vv in ob.data.vertices if not vv.groups))
    # trot cycle, 24 frames: diagonal pairs in phase
    sc0 = bpy.context.scene; sc0.frame_start = 1; sc0.frame_end = 24
    act = bpy.data.actions.new('trot'); ao.animation_data_create(); ao.animation_data.action = act
    phase = {'Lsh': 0, 'Rth': 0, 'Rsh': math.pi, 'Lth': math.pi}
    for f in range(1, 25, 3):
        t = (f-1)/24*2*math.pi
        for bn, ph in phase.items():
            pb = ao.pose.bones[bn]; pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (0.45*math.sin(t+ph), 0, 0); pb.keyframe_insert('rotation_euler', frame=f)
            lower = {'Lsh': 'Lel', 'Rsh': 'Rel', 'Lth': 'Lkn', 'Rth': 'Rkn'}[bn]
            pl = ao.pose.bones[lower]; pl.rotation_mode = 'XYZ'
            pl.rotation_euler = (-0.5*max(0, math.sin(t+ph+1.2)), 0, 0); pl.keyframe_insert('rotation_euler', frame=f)
        for bn, amp in (('t1', 0.25), ('head', 0.08)):
            pb = ao.pose.bones[bn]; pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (0, 0, amp*math.sin(2*t)); pb.keyframe_insert('rotation_euler', frame=f)
    sc0.frame_set(int(os.environ.get('POSEF', '4')))
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{TAG}.glb'), export_animations=True, export_vertex_color='ACTIVE')

# ---------------- render: 3/4 view like wolf_beauty ----------------
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.studio_light = 'paint.sl' if 'paint.sl' in [l.name for l in bpy.context.preferences.studio_lights] else sh.studio_light; sh.color_type = 'VERTEX' if os.environ.get('CT','V')=='V' else 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = False
sh.shadow_intensity = 0.3
sc.display.shadow_focus = 0.2
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.85, 0.83, 0.80)
sc.render.film_transparent = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.93, 0.92, 0.89)
sc.render.resolution_x = 800; sc.render.resolution_y = 800
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 60
def shoot(az_deg, el_deg, dist, name):
    tgt = Vector((0, -0.02, 0.55))
    az = math.radians(az_deg); el = math.radians(el_deg)
    d = Vector((math.sin(az)*math.cos(el), -math.cos(az)*math.cos(el), math.sin(el)))
    cam.location = tgt + d*dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f'{TAG}_{name}.png')
    bpy.ops.render.render(write_still=True)
shoot(50, 18, 3.3, 'q34')
shoot(90, 5, 3.3, 'side')
# wire overlay: render a flat-grey copy with wire via freestyle is heavy; instead export and let others inspect
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{TAG}.blend'))
