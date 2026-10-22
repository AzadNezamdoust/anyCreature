"""render_ab.py -- matched renders of A (baseline glb) and B (candidate glb): 6 views lit colour (EEVEE, same
camera/light), plus a close-up crop of receiver/charging handle and muzzle. blender -b -P render_ab.py -- A.glb B.glb outdir"""
import math
import os
import sys

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
GLBS, OUT = {"A": a[0], "B": a[1]}, a[2]
os.makedirs(OUT, exist_ok=True)
VIEWS = [("side_l", 90, 5), ("side_r", -90, 5), ("q_front", 40, 20), ("q_rear", 140, 25), ("top", 90, 85),
         ("low", -30, -20)]
CROPS = [("crop_receiver", (0.0, 0.05, 0.22), 0.16, 70, 10), ("crop_muzzle", (0.0, -0.40, 0.22), 0.11, 50, 15),
         ("crop_stock", (0.0, 0.40, 0.17), 0.16, 120, 15)]


def scene_reset():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for d in list(coll):
            coll.remove(d)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.82, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = w
    for rot, e in (((50, 0, 30), 3.0), ((60, 0, 210), 1.2)):
        L = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
        L.data.energy = e
        L.rotation_euler = [math.radians(r) for r in rot]
        sc.collection.objects.link(L)
    return sc


def cam(sc, target, dist, az, el, ortho):
    c = bpy.data.objects.get("cam")
    if c is None:
        c = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        sc.collection.objects.link(c)
        sc.camera = c
    c.data.type = "ORTHO"
    c.data.ortho_scale = ortho
    t = Vector(target)
    d = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)),
                -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
    # model frame: nose -Y (hs.A); az 90 = looking at the +x (left) flank
    d = Vector((math.cos(math.radians(el)) * math.cos(math.radians(az - 90)) * 0 + d.x, d.y, d.z))
    c.location = t + d * dist
    c.rotation_euler = (t - c.location).to_track_quat("-Z", "Y").to_euler()


for tag, glb in GLBS.items():
    sc = scene_reset()
    bpy.ops.import_scene.gltf(filepath=glb)
    mins = Vector((1e9,) * 3)
    maxs = Vector((-1e9,) * 3)
    for ob in sc.objects:
        if ob.type == "MESH":
            for v in ob.bound_box:
                w = ob.matrix_world @ Vector(v)
                mins = Vector(map(min, mins, w))
                maxs = Vector(map(max, maxs, w))
    ctr = (mins + maxs) / 2
    for name, az, el in VIEWS:
        sc.render.resolution_x, sc.render.resolution_y = 1200, 700
        cam(sc, ctr, 3.0, az, el, 1.05)
        sc.render.filepath = os.path.join(OUT, f"{tag}_{name}.png")
        bpy.ops.render.render(write_still=True)
        if name == "q_front":
            sc.render.resolution_x, sc.render.resolution_y = 192, 112
            sc.render.filepath = os.path.join(OUT, f"{tag}_thumb192.png")
            bpy.ops.render.render(write_still=True)
    for name, t, size, az, el in CROPS:
        sc.render.resolution_x, sc.render.resolution_y = 800, 600
        cam(sc, Vector((ctr.x, t[1], t[2])), 2.0, az, el, size * 1.6)
        sc.render.filepath = os.path.join(OUT, f"{tag}_{name}.png")
        bpy.ops.render.render(write_still=True)
