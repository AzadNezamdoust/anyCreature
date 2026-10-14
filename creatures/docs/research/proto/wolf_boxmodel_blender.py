"""Proof: model a low-poly wolf in headless Blender (bpy) the way a human box-modeller would.

Human steps reproduced (each is a bmesh op a person would do with E / S / G / Ctrl-R):
  1. rump cap polygon → extrude forward in segments, scale/move each ring where the form changes
     (hip, waist, chest, shoulder, neck, skull, brow, muzzle, nose)
  2. legs: EXTRUDE a face of the torso downward (thigh → shank → paw); the leg shares the
     body's vertices, so there is no intersecting shell
  3. tail: extrude the rump cap; ears: extrude a face of the skull
  4. Mirror modifier on X with clipping (model only the left half), apply
  5. break the symmetry by hand: tilt one ear, curl the tail off-axis, drop one shoulder
  6. flat shading, one material per region (body / belly / paws / nose / eye)
  7. armature + automatic weights, a tiny idle clip, export GLB, render.
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

S = "/tmp/claude-0/-home-user-anyCreature/33ef5e48-0bfe-5281-b1b6-0e2d9698737c/scratchpad/research_fable"
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

me = bpy.data.meshes.new("wolf"); ob = bpy.data.objects.new("wolf", me)
sc.collection.objects.link(ob)
bm = bmesh.new()

# ---------- helpers = the artist's hands -------------------------------------------------
def half_ring(y, cz, rx, rz, boxy=0.72, top=1.0, bot=1.0):
    """5 verts of the LEFT half of a boxy octagon section (top and bottom verts on the seam x=0)."""
    pts = [(0, y, cz + rz * top), (boxy * rx, y, cz + 0.78 * rz * top), (rx, y, cz),
           (boxy * rx, y, cz - 0.78 * rz * bot), (0, y, cz - rz * bot)]
    return [bm.verts.new(p) for p in pts]

def bridge(a, b):
    """quads between two consecutive rings (front ring b, back ring a)."""
    return [bm.faces.new([a[i], a[i + 1], b[i + 1], b[i]]) for i in range(4)]

def extrude_face(face):
    r = bmesh.ops.extrude_face_region(bm, geom=[face])
    newf = [g for g in r["geom"] if isinstance(g, bmesh.types.BMFace)][0]
    return newf

def place_quad(face, xc, w, yc, l, z):
    """after an extrude: grab/scale the 4 new verts onto a rectangle (the human's S and G)."""
    vs = list(face.verts)
    xm = sum(v.co.x for v in vs) / 4; ym = sum(v.co.y for v in vs) / 4
    for v in vs:
        v.co = Vector((xc + (w / 2 if v.co.x >= xm else -w / 2), yc + (l / 2 if v.co.y >= ym else -l / 2), z))

def place_ring(face, y, cz, rx, rz, boxy=0.72):
    """extruded half-ring cap: move its 5 verts onto a new half ring (keeps seam verts on x=0)."""
    vs = sorted(face.verts, key=lambda v: (-v.co.z if v.co.x < 1e-6 else 0, v.co.x))
    # order: identify by original layout: top(x=0,high) upper corner, side, lower corner, bottom(x=0,low)
    seam = sorted([v for v in face.verts if abs(v.co.x) < 1e-6], key=lambda v: -v.co.z)
    others = sorted([v for v in face.verts if abs(v.co.x) >= 1e-6], key=lambda v: -v.co.z)
    order = [seam[0], others[0], others[1], others[2], seam[1]]
    tgt = [(0, y, cz + rz), (boxy * rx, y, cz + 0.78 * rz), (rx, y, cz), (boxy * rx, y, cz - 0.78 * rz), (0, y, cz - rz)]
    for v, p in zip(order, tgt): v.co = Vector(p)
    return order

# ---------- 1. torso + neck + head: a chain of extrusions, rings only where the form changes ----
# name: (y, cz, rx, rz, boxy)   y negative = forward
R = {}
spec = [("rump",     0.45, 0.62, 0.16, 0.19, 0.75),
        ("hip",      0.18, 0.64, 0.21, 0.23, 0.72),
        ("waist",   -0.06, 0.62, 0.17, 0.19, 0.70),
        ("chest",   -0.30, 0.60, 0.21, 0.26, 0.78),
        ("shoulder",-0.52, 0.68, 0.19, 0.21, 0.72),
        ("neck0",   -0.70, 0.80, 0.12, 0.14, 0.70),
        ("neck1",   -0.84, 0.90, 0.13, 0.13, 0.70),
        ("skull",   -0.98, 0.95, 0.155, 0.15, 0.80),
        ("brow",    -1.10, 0.92, 0.13, 0.12, 0.85),
        ("muzzle",  -1.24, 0.86, 0.075, 0.075, 0.85),
        ("nose",    -1.31, 0.85, 0.045, 0.04, 0.9)]
prev = None
for name, y, cz, rx, rz, bx in spec:
    R[name] = half_ring(y, cz, rx, rz, bx)
    if prev: bridge(R[prev], R[name])
    prev = name
cap_rump = bm.faces.new(R["rump"])          # half n-gon caps on the seam
cap_nose = bm.faces.new(list(reversed(R["nose"])))
# a drooping belly and a keel: pull the bottom verts of chest/waist down a touch
R["chest"][4].co.z -= 0.03; R["chest"][3].co.z -= 0.02; R["waist"][4].co.z -= 0.01
# brow: lift the brow ring's upper corner (a brow ridge) and pull the muzzle's lower seam up (jaw line)
R["brow"][1].co.z += 0.02; R["muzzle"][4].co.z += 0.01
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()

def seg_face(a, b, idx):
    """the face between rings a and b at slot idx (0 top,1 upper side,2 lower side,3 bottom)."""
    va, vb = {R[a][idx], R[a][idx + 1]}, {R[b][idx], R[b][idx + 1]}
    for f in bm.faces:
        if va | vb == set(f.verts): return f
    raise RuntimeError("no face " + a + b + str(idx))

# ---------- 2. legs: extrude torso faces downward ------------------------------------------
# hind leg from the lower-side face of the hip..rump segment
f = extrude_face(seg_face("hip", "rump", 2));  place_quad(f, 0.14, 0.13, 0.30, 0.20, 0.42)  # thigh -> knee (knee forward)
f = extrude_face(f);                             place_quad(f, 0.13, 0.10, 0.40, 0.13, 0.22)  # shank -> hock (set back)
f = extrude_face(f);                             place_quad(f, 0.13, 0.10, 0.34, 0.12, 0.08)  # cannon -> ankle
f = extrude_face(f);                             place_quad(f, 0.13, 0.11, 0.27, 0.18, 0.0)   # paw on the ground
hind_paw = f
# front leg from the lower-side face of the shoulder..chest segment
f = extrude_face(seg_face("shoulder", "chest", 2)); place_quad(f, 0.13, 0.12, -0.41, 0.17, 0.42) # upper arm -> elbow
f = extrude_face(f);                                place_quad(f, 0.12, 0.09, -0.42, 0.10, 0.20) # forearm -> wrist
f = extrude_face(f);                                place_quad(f, 0.12, 0.10, -0.44, 0.12, 0.08)
f = extrude_face(f);                                place_quad(f, 0.12, 0.11, -0.50, 0.18, 0.0)  # paw, a bit forward
front_paw = f

# ---------- 3. tail from the rump cap, ear from the skull ---------------------------------
def extrude_cap(face):
    nf = extrude_face(face)
    # delete the side face the extrusion made on the mirror plane
    for g in [x for x in bm.faces if all(abs(v.co.x) < 1e-6 for v in x.verts) and x is not nf]:
        bm.faces.remove(g)
    return nf
t = extrude_cap(cap_rump); place_ring(t, 0.58, 0.60, 0.075, 0.075)
t = extrude_cap(t);        place_ring(t, 0.72, 0.52, 0.10, 0.11)    # bushy middle
t = extrude_cap(t);        place_ring(t, 0.84, 0.38, 0.07, 0.07)
t = extrude_cap(t);        place_ring(t, 0.92, 0.26, 0.02, 0.02)
tail_tip = t
e = extrude_face(seg_face("neck1", "skull", 1)); place_quad(e, 0.10, 0.09, -0.90, 0.12, 1.06)   # ear base up
e = extrude_face(e);                              place_quad(e, 0.095, 0.025, -0.905, 0.035, 1.20) # ear tip
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()

# ---------- 4. mirror modifier with clipping, then apply ----------------------------------
mod = ob.modifiers.new("mirror", "MIRROR"); mod.use_axis[0] = True; mod.use_clip = True; mod.use_mirror_merge = True; mod.merge_threshold = 1e-4
bpy.context.view_layer.objects.active = ob
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
    bpy.ops.object.modifier_apply(modifier="mirror")

# ---------- 5. eyes (small spheres, the classic cheap way), asymmetry by hand -------------
def sphere(name, loc, r, segs=6, rings=4):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = bpy.context.object; o.name = name; return o
eyes = []
for sx in (1, -1):
    eyes.append(sphere("eye", (sx * 0.105, -1.10, 0.95), 0.042))
    eyes.append(sphere("pupil", (sx * 0.125, -1.125, 0.95), 0.022, 6, 3))

# asymmetry: tilt the right ear back a little, sway the tail to one side, no two paws exactly alike
import random; random.seed(7)
for v in me.vertices:
    if v.co.z > 1.0 and v.co.x < 0:                # right ear
        v.co.y += 0.02 * (v.co.z - 1.0) / 0.16; v.co.x -= 0.015 * (v.co.z - 1.0) / 0.16
    if v.co.y > 0.5:                                # tail sways left and curls
        v.co.x += 0.10 * (v.co.y - 0.5) / 0.36
    # tiny hand-made jitter (1 cm) everywhere but the seam
    if abs(v.co.x) > 1e-4: v.co += Vector((random.uniform(-.006, .006), random.uniform(-.006, .006), random.uniform(-.006, .006)))

# ---------- 6. flat shading + materials per region ---------------------------------------
def mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    return m
M = {"fur": mat("fur_body", (0.42, 0.31, 0.20)), "belly": mat("fur_belly", (0.86, 0.78, 0.60)),
     "paw": mat("fur_paw", (0.16, 0.12, 0.09)), "nose": mat("nose", (0.03, 0.03, 0.03)),
     "eye": mat("eye", (0.95, 0.75, 0.15)), "pupil": mat("pupil", (0.02, 0.02, 0.02)), "back": mat("fur_back", (0.20, 0.17, 0.16))}
for k in ("fur", "back", "belly", "paw", "nose"): me.materials.append(M[k])
mi = {"fur": 0, "back": 1, "belly": 2, "paw": 3, "nose": 4}
for p in me.polygons:
    c = p.center; n = p.normal
    p.use_smooth = False
    if c.y < -1.28: p.material_index = mi["nose"]
    elif c.z < 0.10 and abs(c.x) > 0.05: p.material_index = mi["paw"]
    elif c.z > 0.40 and n.z < -0.35 and abs(c.x) < 0.16 and -0.9 < c.y < 0.5: p.material_index = mi["belly"]   # belly + throat
    elif c.y < -1.12 and c.z < 0.87 and n.z < 0.3: p.material_index = mi["belly"]      # lower jaw
    elif n.z > 0.6 and c.z > 0.72 and -0.55 < c.y < 0.5: p.material_index = mi["back"]   # saddle
    else: p.material_index = mi["fur"]
for o in eyes:
    o.data.materials.append(M["eye" if o.name.startswith("eye") else "pupil"])
    for p in o.data.polygons: p.use_smooth = True
# join eyes into the wolf
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob] + eyes, selected_editable_objects=[ob] + eyes):
    bpy.ops.object.join()
me = ob.data
# vertex colours baked from the material colours (so the GLB carries COLOR_0 like the harness expects)
col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for p in me.polygons:
    rgb = me.materials[p.material_index].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
    for li in p.loop_indices: col.data[li].color = rgb
print("mesh: verts", len(me.vertices), "faces", len(me.polygons), "tris", sum(len(p.vertices) - 2 for p in me.polygons))

# ---------- 7. armature, automatic weights, a small idle, export --------------------------
arm = bpy.data.armatures.new("rig"); rig = bpy.data.objects.new("wolf_rig", arm); sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
    bpy.ops.object.mode_set(mode="EDIT")
    def bone(name, h, t, parent=None, connect=False):
        b = arm.edit_bones.new(name); b.head = Vector(h); b.tail = Vector(t)
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = connect
        return b
    bone("Hips", (0, 0.30, 0.62), (0, 0.05, 0.62))
    bone("Spine", (0, 0.05, 0.62), (0, -0.30, 0.63), "Hips", True)
    bone("Chest", (0, -0.30, 0.63), (0, -0.55, 0.70), "Spine", True)
    bone("Neck", (0, -0.55, 0.70), (0, -0.84, 0.90), "Chest", True)
    bone("Head", (0, -0.84, 0.90), (0, -1.31, 0.85), "Neck", True)
    bone("Tail1", (0, 0.45, 0.62), (0, 0.65, 0.50), "Hips"); bone("Tail2", (0, 0.65, 0.50), (0.08, 0.86, 0.22), "Tail1", True)
    for sx, side in ((1, "L"), (-1, "R")):
        bone(side + "Thigh", (sx * 0.14, 0.30, 0.58), (sx * 0.14, 0.33, 0.40), "Hips")
        bone(side + "Shin", (sx * 0.14, 0.33, 0.40), (sx * 0.13, 0.40, 0.20), side + "Thigh", True)
        bone(side + "HFoot", (sx * 0.13, 0.40, 0.20), (sx * 0.13, 0.30, 0.06), side + "Shin", True)
        bone(side + "HToe", (sx * 0.13, 0.30, 0.06), (sx * 0.13, 0.16, 0.0), side + "HFoot", True)
        bone(side + "UpperArm", (sx * 0.13, -0.40, 0.62), (sx * 0.13, -0.41, 0.42), "Chest")
        bone(side + "Forearm", (sx * 0.13, -0.41, 0.42), (sx * 0.12, -0.42, 0.20), side + "UpperArm", True)
        bone(side + "FFoot", (sx * 0.12, -0.42, 0.20), (sx * 0.12, -0.46, 0.06), side + "Forearm", True)
        bone(side + "FToe", (sx * 0.12, -0.46, 0.06), (sx * 0.12, -0.58, 0.0), side + "FFoot", True)
        bone(side + "Ear", (sx * 0.09, -0.90, 1.0), (sx * 0.085, -0.905, 1.16), "Head")
    bpy.ops.object.mode_set(mode="OBJECT")
with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[ob, rig], selected_editable_objects=[ob, rig]):
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
print("skin groups:", len(ob.vertex_groups))
# idle: breathe + look
sc.frame_start, sc.frame_end = 1, 48; sc.render.fps = 24
pb = rig.pose.bones
for frame, chest, head, tail in ((1, 0, 0, 0), (24, 3, -6, 12), (48, 0, 0, 0)):
    sc.frame_set(frame)
    pb["Chest"].rotation_mode = pb["Head"].rotation_mode = pb["Tail2"].rotation_mode = "XYZ"
    pb["Chest"].rotation_euler = (math.radians(chest), 0, 0); pb["Head"].rotation_euler = (math.radians(head), 0, 0)
    pb["Tail2"].rotation_euler = (0, 0, math.radians(tail))
    for b in ("Chest", "Head", "Tail2"): pb[b].keyframe_insert("rotation_euler", frame=frame)
rig.animation_data.action.name = "idle"
sc.frame_set(1)
bpy.ops.export_scene.gltf(filepath=os.path.join(S, "proof_wolf.glb"), export_format="GLB", export_animations=True, export_skins=True, export_yup=True, export_apply=True)

# ---------- 8. render: 3/4 front-left from above, like example/wolf_beauty.png ------------
cam_d = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
target = Vector((0, -0.25, 0.55))
def aim(campos):
    cam.location = campos; d = target - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cam_d.lens = 45
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 3.0; so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(-10), math.radians(-40))
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.75, 0.72, 1); sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
# ground plane for a contact shadow
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0)); gnd = bpy.context.object; gnd.data.materials.append(mat("ground", (0.85, 0.84, 0.80)))
sc.render.resolution_x = sc.render.resolution_y = 800
sc.render.film_transparent = False
views = {"beauty": (-1.9, -2.4, 1.5), "side": (-3.2, -0.3, 0.7), "front": (0, -3.4, 0.9), "top": (0, -0.3, 3.6), "back34": (1.9, 2.4, 1.4)}
sc.render.engine = "CYCLES"; sc.cycles.samples = 64; sc.cycles.device = "CPU"; sc.cycles.use_denoising = True
for name, pos in views.items():
    aim(Vector(pos)); sc.render.filepath = os.path.join(S, f"proof_wolf_{name}.png"); bpy.ops.render.render(write_still=True)
# a workbench flat/cavity render to show the facets honestly
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.show_shadows = True
aim(Vector(views["beauty"])); sc.render.filepath = os.path.join(S, "proof_wolf_workbench.png"); bpy.ops.render.render(write_still=True)
sh.show_object_outline = True; sh.color_type = "SINGLE"; sh.single_color = (0.8, 0.8, 0.8)
aim(Vector(views["beauty"])); sc.render.filepath = os.path.join(S, "proof_wolf_clay.png"); bpy.ops.render.render(write_still=True)
# wireframe over clay: duplicate with a Wireframe modifier (thin black), workbench, no shadows
wire = ob.copy(); wire.data = ob.data.copy(); sc.collection.objects.link(wire); wire.parent = None; wire.modifiers.clear()
wm = wire.modifiers.new("wire", "WIREFRAME"); wm.thickness = 0.006; wm.use_replace = True
wire.data.materials.clear(); wire.data.materials.append(mat("wire", (0, 0, 0)))
sh.color_type = "MATERIAL"; sh.show_shadows = False; sh.show_cavity = False
for name in ("beauty", "side"):
    aim(Vector(views[name])); sc.render.filepath = os.path.join(S, f"proof_wolf_wire_{name}.png"); bpy.ops.render.render(write_still=True)
wire.hide_render = True
# posed frame to prove the skin deforms
sc.frame_set(24); sc.render.filepath = os.path.join(S, "proof_wolf_posed_f24.png"); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(S, "proof_wolf.blend"))
print("done")
