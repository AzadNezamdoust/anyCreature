"""Blender step (run inside Blender 5.2 headless): mesh.npz (B-rep face-id tessellation) -> game mesh.

blender -b --factory-startup --python-exit-code 1 --python blender_mesh.py -- <run_dir> [--lods 0.5,0.25] [--smart-uv]
          [--sharp-angle 30]
Writes <run_dir>/model.glb (LOD0), model_lod<N>.glb, model.blend, mesh_report.json.
Per part: verts welded across B-rep faces; UV seams = every B-rep face boundary (incl. periodic seams);
sharp edges = face boundaries with dihedral > sharp-angle; smooth shading elsewhere; UVs unwrapped per B-rep
face island (angle based, packed) or smart project with --smart-uv.
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
run = argv[0]
lods = [float(x) for x in argv[argv.index("--lods") + 1].split(",")] if "--lods" in argv else [0.5, 0.25]
sharp_deg = float(argv[argv.index("--sharp-angle") + 1]) if "--sharp-angle" in argv else 30.0
smart = "--smart-uv" in argv

d = np.load(os.path.join(run, "mesh.npz"))
names = [str(n) for n in d["names"]]
cols = d["colours"]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
report = {"parts": {}, "lods": lods, "sharp_angle": sharp_deg, "uv": "smart" if smart else "brep_islands"}


def weld(V, T, tol):
    q = np.round(V / tol).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    return V[first], inv[T], inv


def boundary_edges(T, F):
    """Edges used once within their own B-rep face's (unwelded) triangulation -> face boundary incl. periodic seam."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    fid = np.concatenate([F, F, F])
    key = np.sort(e, axis=1)
    rows = np.column_stack([fid, key])
    u, cnt = np.unique(rows, axis=0, return_counts=True)
    return u[cnt == 1][:, 1:]


for i, name in enumerate(names):
    V, T, F = d[f"v_{i}"], d[f"t_{i}"], d[f"f_{i}"]
    if len(T) == 0:
        continue
    diag = float(np.linalg.norm(V.max(0) - V.min(0))) or 1.0
    bnd = boundary_edges(T, F)
    Vw, Tw, inv = weld(V, T, diag * 1e-6)
    seam_set = {tuple(sorted((int(inv[a]), int(inv[b])))) for a, b in bnd}
    me = bpy.data.meshes.new(name)
    me.from_pydata(Vw.tolist(), [], Tw.tolist())
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    fid_layer = bm.faces.layers.int.new("brep_face")
    for f, fid in zip(bm.faces, F):
        f[fid_layer] = int(fid)
    n_seam = n_sharp = 0
    cos_t = math.cos(math.radians(sharp_deg))
    for e in bm.edges:
        k = tuple(sorted((e.verts[0].index, e.verts[1].index)))
        if k in seam_set:
            e.seam = True
            n_seam += 1
            if len(e.link_faces) == 2:
                a, b = e.link_faces
                if a.normal.dot(b.normal) < cos_t:
                    e.smooth = False
                    n_sharp += 1
        elif len(e.link_faces) == 2 and e.link_faces[0].normal.dot(e.link_faces[1].normal) < math.cos(math.radians(60)):
            e.smooth = False
            n_sharp += 1
    for f in bm.faces:
        f.smooth = True
    # drop degenerate tris (zero-area slivers from tiny B-rep faces); flags already set
    bmesh.ops.dissolve_degenerate(bm, dist=diag * 1e-7, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    c = [float(x) for x in cols[i]]
    bsdf.inputs["Base Color"].default_value = (*[x ** 2.2 for x in c], 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    mat.diffuse_color = (*[x ** 2.2 for x in c], 1)
    me.materials.append(mat)
    # UVs
    bpy.context.view_layer.objects.active = ob
    for o in scene.objects:
        o.select_set(o == ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    if smart:
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
    else:
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.003)
        bpy.ops.uv.pack_islands(margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    report["parts"][name] = {"tris": len(me.polygons), "verts": len(me.vertices), "seam_edges": n_seam,
                             "sharp_edges": n_sharp, "brep_faces": int(F.max()) + 1}

report["tris"] = sum(p["tris"] for p in report["parts"].values())


def export(path):
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True)


objs = [o for o in scene.objects if o.type == "MESH"]
for o in objs:
    o.select_set(True)
export(os.path.join(run, "model.glb"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(run, "model.blend"))
report["lod_tris"] = {}
for li, ratio in enumerate(lods, start=1):
    for o in objs:
        for m in list(o.modifiers):
            o.modifiers.remove(m)
        m = o.modifiers.new("lod", "DECIMATE")
        m.ratio = ratio
        m.use_collapse_triangulate = True
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    report["lod_tris"][f"lod{li}"] = sum(len(o.evaluated_get(dg).to_mesh().loop_triangles) for o in objs)
    for o in scene.objects:
        o.select_set(o in objs)
    export(os.path.join(run, f"model_lod{li}.glb"))
with open(os.path.join(run, "mesh_report.json"), "w") as f:
    json.dump(report, f, indent=1)
print("MESH_REPORT", json.dumps({"tris": report["tris"], "lod_tris": report["lod_tris"]}))
