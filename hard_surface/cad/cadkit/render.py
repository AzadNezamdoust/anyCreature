"""6-view render + contact sheet (Blender 5.2 headless). Same style for any glb (cad build or bpy build).

blender -b --factory-startup --python-exit-code 1 --python render.py -- <model.glb> <out_dir> [--res 640]
          [--front -x]   (which axis the model's front/muzzle points to; default -x)
Views: iso (front-left 3/4, like the concepts), left, right, front, back, top.  Writes view_<name>.png,
sheet.png (3x2), render_report.json (bbox, tris).  Convention: Z up, length along X, left flank = -Y.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
res = int(argv[argv.index("--res") + 1]) if "--res" in argv else 640
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
if src.endswith(".blend"):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == "MESH"]
dg = bpy.context.evaluated_depsgraph_get()
pts, tris = [], 0
for o in meshes:
    m = o.evaluated_get(dg).to_mesh()
    m.calc_loop_triangles()
    tris += len(m.loop_triangles)
    mw = o.matrix_world
    pts += [mw @ v.co for v in m.vertices]
P = np.array([p.to_tuple() for p in pts])
lo, hi = P.min(0), P.max(0)
ctr = Vector(((lo + hi) / 2).tolist())
size = hi - lo
R = float(np.linalg.norm(size)) / 2

scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light = "STUDIO"
sh.color_type = "MATERIAL"
sh.show_cavity = True
sh.cavity_type = "BOTH"
sh.show_object_outline = True
sh.object_outline_color = (0.05, 0.05, 0.05)
sh.show_specular_highlight = False
scene.display.render_aa = "8"
scene.render.resolution_x = scene.render.resolution_y = res
scene.render.film_transparent = False
world = bpy.data.worlds.new("w")
scene.world = world
scene.view_settings.view_transform = "Standard"
sh.background_type = "VIEWPORT"
sh.background_color = (1, 1, 1)
# Workbench background = world colour in render
world.color = (1, 1, 1)

cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

VIEWS = {
    "iso": Vector((-1.0, -1.25, 0.85)),
    "left": Vector((0, -1, 0)), "right": Vector((0, 1, 0)),
    "front": Vector((-1, 0, 0)), "back": Vector((1, 0, 0)),
    "top": Vector((0, 0, 1)),
}
files = []
for name, d in VIEWS.items():
    d = d.normalized()
    cam.location = ctr + d * (R * 4)
    cam.rotation_euler = (0, 0, 0) if name == "top" else (-d).to_track_quat("-Z", "Y").to_euler()
    # ortho scale = projected extent
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    Q = np.array([(inv @ Vector(p)).to_tuple() for p in P[:: max(1, len(P) // 4000)]])
    ext = max(np.ptp(Q[:, 0]), np.ptp(Q[:, 1]))
    cx, cy = (Q[:, 0].max() + Q[:, 0].min()) / 2, (Q[:, 1].max() + Q[:, 1].min()) / 2
    cam.location = cam.matrix_world @ Vector((cx, cy, 0))
    cam_data.ortho_scale = ext * 1.12
    cam_data.clip_end = R * 10
    f = os.path.join(out, f"view_{name}.png")
    scene.render.filepath = f
    bpy.ops.render.render(write_still=True)
    files.append(f)

# contact sheet 3x2
imgs = []
for f in files:
    im = bpy.data.images.load(f)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(res, res, 4)
    imgs.append(a)
row0 = np.concatenate(imgs[3:6], axis=1)  # bottom row in Blender's bottom-up pixel order
row1 = np.concatenate(imgs[0:3], axis=1)
sheet = np.concatenate([row0, row1], axis=0)
H, W = sheet.shape[:2]
img = bpy.data.images.new("sheet", W, H, alpha=True)
img.pixels = sheet.ravel()
img.filepath_raw = os.path.join(out, "sheet.png")
img.file_format = "PNG"
img.save()
rep = {"src": src, "tris": tris, "bbox_min": lo.round(5).tolist(), "bbox_max": hi.round(5).tolist(),
       "size": size.round(5).tolist(), "views": list(VIEWS), "sheet_layout": "top row iso,left,right; bottom front,back,top"}
json.dump(rep, open(os.path.join(out, "render_report.json"), "w"), indent=1)
print("RENDER_REPORT", json.dumps(rep))
