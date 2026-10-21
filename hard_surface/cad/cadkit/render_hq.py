"""Surface-quality render (Blender 5.2 headless, Workbench) of a FINE B-rep tessellation glb (model_hq.glb).

blender -b --factory-startup --python-exit-code 1 --python render_hq.py -- <model_hq.glb> <out_dir> [--res 900]
Tiles: hero (part colours, studio light), hero_clay (matcap clay), hero_zebra (reflection-stripe matcap, shows G1/G2
continuity: stripes kink at G0 creases, bend smoothly across G2 blends), + 6 ortho clay views. sheet.png = 3x3.
Convention: Z up, front -X, left -Y.
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
res = int(argv[argv.index("--res") + 1]) if "--res" in argv else 900
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == "MESH"]
pts, tris = [], 0
for o in meshes:
    m = o.data
    m.calc_loop_triangles()
    tris += len(m.loop_triangles)
    mw = o.matrix_world
    vs = m.vertices
    pts += [mw @ vs[i].co for i in range(0, len(vs), max(1, len(vs) // 3000))]
P = np.array([p.to_tuple() for p in pts])
lo, hi = P.min(0), P.max(0)
ctr = Vector(((lo + hi) / 2).tolist())
size = hi - lo
R = float(np.linalg.norm(size)) / 2

scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.show_object_outline = False
sh.show_cavity = False
sh.show_specular_highlight = True
scene.display.render_aa = "16"
scene.render.resolution_x = scene.render.resolution_y = res
scene.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("w")
world.color = (0.93, 0.93, 0.94)
scene.world = world

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def look(d, ortho=True):
    d = d.normalized()
    cam_data.type = "ORTHO" if ortho else "PERSP"
    cam_data.lens = 70
    cam_data.clip_end = R * 40
    cam.location = ctr + d * (R * (4 if ortho else 3.7))
    cam.rotation_euler = (0, 0, -math.pi / 2) if d.z > 0.99 else (-d).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    if ortho:
        inv = cam.matrix_world.inverted()
        Q = np.array([(inv @ Vector(p)).to_tuple() for p in P])
        ext = max(np.ptp(Q[:, 0]), np.ptp(Q[:, 1]))
        cx, cy = (Q[:, 0].max() + Q[:, 0].min()) / 2, (Q[:, 1].max() + Q[:, 1].min()) / 2
        cam.location = cam.matrix_world @ Vector((cx, cy, 0))
        cam_data.ortho_scale = ext * 1.08


def style(kind):
    if kind == "colour":
        sh.light, sh.color_type = "STUDIO", "MATERIAL"
        pass
    elif kind == "clay":
        sh.light, sh.color_type = "MATCAP", "SINGLE"
        sh.studio_light = "clay_studio.exr"
        sh.single_color = (0.8, 0.78, 0.75)
    elif kind == "zebra":
        sh.light, sh.color_type = "MATCAP", "SINGLE"
        sh.studio_light = ZEBRA
        sh.single_color = (1, 1, 1)


# zebra matcap: 14 hard-ish stripes over asin(view-space normal.x) -> isophote bands (kink = G0, smooth = G1+)
_n = 512
_u = np.linspace(-1, 1, _n)
NX, NY = np.meshgrid(_u, _u)
_ang = np.arcsin(np.clip(NX * 0.999, -1, 1)) + 0.35 * np.arcsin(np.clip(NY * 0.999, -1, 1))
_st = 0.5 + 0.5 * np.tanh(6 * np.sin(_ang * 14))
_rim = np.clip(1 - (NX ** 2 + NY ** 2), 0, 1) ** 0.15
_rgb = (0.06 + 0.9 * _st) * _rim
_px = np.dstack([_rgb, _rgb, _rgb, np.ones_like(_rgb)]).astype(np.float32)
_zi = bpy.data.images.new("zebra", _n, _n, alpha=True)
_zi.pixels = _px.ravel()
_zf = os.path.join(out, "zebra_matcap.png")
_zi.filepath_raw, _zi.file_format = _zf, "PNG"
_zi.save()
bpy.ops.preferences.studiolight_install(files=[{"name": "zebra_matcap.png"}], directory=out, type="MATCAP")
ZEBRA = "zebra_matcap.png"

HERO = Vector((-1.0, -1.15, 0.55))
SHOTS = [("hero", HERO, False, "colour"), ("hero_clay", HERO, False, "clay"), ("hero_zebra", HERO, False, "zebra"),
         ("front", Vector((-1, 0, 0)), True, "clay"), ("left", Vector((0, -1, 0)), True, "clay"),
         ("top", Vector((0, 0, 1)), True, "clay"), ("back", Vector((1, 0, 0)), True, "clay"),
         ("rear34_zebra", Vector((1.0, 1.1, 0.6)), False, "zebra"), ("under", Vector((-0.6, 0.7, -0.8)), False, "clay")]
files = []
for name, d, ortho, kind in SHOTS:
    style(kind)
    look(d, ortho)
    f = os.path.join(out, f"view_{name}.png")
    scene.render.filepath = f
    bpy.ops.render.render(write_still=True)
    files.append(f)

imgs = [np.array(bpy.data.images.load(f).pixels[:], dtype=np.float32).reshape(res, res, 4) for f in files]
rows = [np.concatenate(imgs[i:i + 3], axis=1) for i in (6, 3, 0)]  # bottom-up pixel order
sheet = np.concatenate(rows, axis=0)
H, W = sheet.shape[:2]
img = bpy.data.images.new("sheet", W, H, alpha=True)
img.pixels = sheet.ravel()
img.filepath_raw = os.path.join(out, "sheet.png")
img.file_format = "PNG"
img.save()
rep = {"src": src, "tris": tris, "size": size.round(5).tolist(), "views": [s[0] for s in SHOTS]}
json.dump(rep, open(os.path.join(out, "render_report.json"), "w"), indent=1)
print("RENDER_REPORT", json.dumps(rep))
