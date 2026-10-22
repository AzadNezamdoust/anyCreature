"""Blender 5.2 headless side of cadkit.game.  blender -b --factory-startup --python-exit-code 1 --python bl_game.py -- <mode> <args.json>
modes:
  build   meshes.npz -> game.blend: HI (fine), LOD0..n (B-rep retess), DEC1..n (collapse decimate of HI, B-rep boundary
          verts protected), QUAD (QuadriFlow of HI). Seams/sharp/weighted normals/UVs on LODs; report (tris, deviation, UV).
  bake    game.blend -> maps per LOD (Cycles GPU, selected-to-active, auto cage): n_tan, ao, id_face, id_mat, pos_grad.
  final   game.blend + maps -> glb per LOD, fbx (all LODs), EEVEE preview tiles.
"""
import json
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
MODE, A = argv[0], json.load(open(argv[1]))
OUT = A["out"]
import importlib.util as _ilu  # noqa: E402  load uvstats by path (cadkit/__init__ imports build123d)
_sp = _ilu.spec_from_file_location("uvstats", os.path.join(os.path.dirname(os.path.abspath(__file__)), "uvstats.py"))
_uv = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_uv)
uv_report = _uv.uv_report


_T0 = time.time()


def log(*a):
    print(f"[{time.time() - _T0:7.1f}s]", *a, flush=True)


# ---------------------------------------------------------------- helpers
def weld(V, T, tol):
    q = np.round(V / tol).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    return V[first], inv[T]


def brep_boundary(T, F):
    """edges (welded idx) used once inside their own face = B-rep face boundaries + periodic seams."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    rows = np.column_stack([np.concatenate([F, F, F]), np.sort(e, axis=1)])
    u, c = np.unique(rows, axis=0, return_counts=True)
    return {tuple(r) for r in u[c == 1][:, 1:]}


def hash_col(i):
    h = (i * 2654435761) & 0xFFFFFFFF
    return ((h & 255) / 255, ((h >> 8) & 255) / 255, ((h >> 16) & 255) / 255, 1.0)


def select_only(objs, active=None):
    for o in bpy.context.scene.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = active or (objs[0] if objs else None)


def make_obj(name, d, prefix, cols):
    """Concatenate all parts of tessellation `prefix` into one mesh; material slot per part."""
    Vs, Ts, Fs, Ps, bset, off = [], [], [], [], set(), 0
    for i in range(len(cols)):
        V, T, F = d[f"{prefix}_v_{i}"], d[f"{prefix}_t_{i}"], d[f"{prefix}_f_{i}"]
        if len(T) == 0:
            continue
        diag = float(np.linalg.norm(V.max(0) - V.min(0))) or 1.0
        Vw, Tw = weld(V, T, diag * 1e-6)
        # drop degenerate / collapsed tris (tiny B-rep faces) - they crash custom-normal code in 5.2
        ar = np.linalg.norm(np.cross(Vw[Tw[:, 1]] - Vw[Tw[:, 0]], Vw[Tw[:, 2]] - Vw[Tw[:, 0]]), axis=1)
        keep = (ar > (diag * 1e-7) ** 2) & (Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])
        Tw, F = Tw[keep], F[keep]
        _, u = np.unique(np.sort(Tw, 1), axis=0, return_index=True)  # duplicate tris
        u = np.sort(u); Tw, F = Tw[u], F[u]
        bset |= {(a + off, b + off) for a, b in brep_boundary(Tw, F)}
        Vs.append(Vw); Ts.append(Tw + off); Fs.append(F); Ps.append(np.full(len(Tw), i))
        off += len(Vw)
    V, T, F, P = np.concatenate(Vs), np.concatenate(Ts), np.concatenate(Fs), np.concatenate(Ps)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], T.tolist())
    me.update()
    a = me.attributes.new("brep_face", "INT", "FACE"); a.data.foreach_set("value", (F + P * 100000).astype(np.int32))
    me.polygons.foreach_set("material_index", P.astype(np.int32))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for i, c in enumerate(cols):
        me.materials.append(part_mat(i, c))
    return ob, bset


_MATS = {}


def part_mat(i, c):
    if i in _MATS:
        return _MATS[i]
    m = bpy.data.materials.new(f"part{i}")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*[float(x) ** 2.2 for x in c], 1)
    b.inputs["Roughness"].default_value = 0.42
    _MATS[i] = m
    return m


def mark_edges(ob, bset, sharp_deg, seam_mode):
    """sharp = dihedral > sharp_deg on B-rep boundaries (or > 60 anywhere); seams = sharp + periodic/closed-face seams
    (seam_mode 'groups') or every B-rep boundary (seam_mode 'brep')."""
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    fl = bm.faces.layers.int.get("brep_face")
    cs, c60 = math.cos(math.radians(sharp_deg)), math.cos(math.radians(60))
    ns = nseam = 0
    for e in bm.edges:
        k = tuple(sorted((e.verts[0].index, e.verts[1].index)))
        lf = e.link_faces
        isb = k in bset if bset is not None else (len(lf) == 2 and lf[0][fl] != lf[1][fl])
        dot = lf[0].normal.dot(lf[1].normal) if len(lf) == 2 else -1
        sharp = (isb and dot < cs) or dot < c60
        e.smooth = not sharp
        periodic = isb and len(lf) == 2 and lf[0][fl] == lf[1][fl]
        e.seam = sharp or periodic or (seam_mode == "brep" and isb) or len(lf) != 2
        ns += sharp; nseam += e.seam
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me); bm.free()
    return {"sharp_edges": ns, "seam_edges": nseam}


def weighted_normals(ob):
    m = ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    m.mode, m.keep_sharp, m.weight = "FACE_AREA", True, 50
    select_only([ob]); bpy.ops.object.modifier_apply(modifier=m.name)


def islands(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    isl = np.full(len(bm.faces), -1); k = 0
    for f in bm.faces:
        if isl[f.index] >= 0:
            continue
        st = [f]; isl[f.index] = k
        while st:
            g = st.pop()
            for e in g.edges:
                if e.seam:
                    continue
                for h in e.link_faces:
                    if isl[h.index] < 0:
                        isl[h.index] = k; st.append(h)
        k += 1
    bm.free()
    return isl


def unwrap(ob, margin):
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    select_only([ob])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=margin)
    bpy.ops.uv.average_islands_scale()          # consistent texel density across islands
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def tri_arrays(ob):
    me = ob.data; me.calc_loop_triangles()
    lt = me.loop_triangles
    vi = np.zeros(len(lt) * 3, np.int32); lt.foreach_get("vertices", vi)
    li = np.zeros(len(lt) * 3, np.int32); lt.foreach_get("loops", li)
    pi = np.zeros(len(lt), np.int32); lt.foreach_get("polygon_index", pi)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    uv = None
    if me.uv_layers:
        uv = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)[li].reshape(-1, 3, 2)
    return co[vi].reshape(-1, 3, 3), uv, pi


def uv_stats(ob, res):
    P, UV, pi = tri_arrays(ob)
    return uv_report(P, UV, islands(ob)[pi], res=res)


def deviation(hi, lo, n=30000):
    """hi verts -> nearest on low: signed (+ = hi outside low) distances in m."""
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(lo, dg)
    vs = hi.data.vertices
    idx = range(0, len(vs), max(1, len(vs) // n))
    d = []
    for i in idx:
        p = vs[i].co
        q, nrm, _, dist = bvh.find_nearest(p)
        if q is not None:
            d.append(dist if (p - q).dot(nrm) >= 0 else -dist)
    d = np.array(d)
    return {"mean_mm": float(np.abs(d).mean() * 1e3), "p99_mm": float(np.percentile(np.abs(d), 99) * 1e3),
            "max_out_mm": float(max(d.max(), 0) * 1e3), "max_in_mm": float(max(-d.min(), 0) * 1e3)}


def tris_of(ob):
    ob.data.calc_loop_triangles(); return len(ob.data.loop_triangles)


def faces_kept(ob):
    a = ob.data.attributes.get("brep_face")
    if a is None:
        return None
    v = np.zeros(len(ob.data.polygons), np.int32); a.data.foreach_get("value", v)
    return int(len(np.unique(v)))


def transfer_face_ids(src, dst):
    dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(src, dg)
    sv = np.zeros(len(src.data.polygons), np.int32); src.data.attributes["brep_face"].data.foreach_get("value", sv)
    sm = np.zeros(len(src.data.polygons), np.int32); src.data.polygons.foreach_get("material_index", sm)
    ids, mi = [], []
    for p in dst.data.polygons:
        _, _, fi, _ = bvh.find_nearest(p.center)
        ids.append(sv[fi] if fi is not None else 0); mi.append(sm[fi] if fi is not None else 0)
    a = dst.data.attributes.get("brep_face") or dst.data.attributes.new("brep_face", "INT", "FACE")
    a.data.foreach_set("value", np.array(ids, np.int32)); dst.data.polygons.foreach_set("material_index", np.array(mi, np.int32))


def finish_low(ob, bset, A, rep):
    t = time.time(); log(" finish", ob.name, tris_of(ob))
    m = mark_edges(ob, bset, A["sharp_deg"], A.get("seam_mode", "brep"))
    unwrap(ob, A["margin"]); log("  unwrapped"); uv = uv_stats(ob, A["res"]); seam = A.get("seam_mode", "brep"); log("  uv", uv)
    if seam == "groups" and uv["stretch_p95"] > A["stretch_fallback"]:  # tangent-continuous closed groups unwrap badly -> per-B-rep-face islands
        m = mark_edges(ob, bset, A["sharp_deg"], "brep"); unwrap(ob, A["margin"]); uv2 = uv_stats(ob, A["res"])
        if uv2["stretch_p95"] < uv["stretch_p95"]:
            uv, seam = uv2, "brep"
        else:
            m = mark_edges(ob, bset, A["sharp_deg"], "groups"); unwrap(ob, A["margin"])
    log("  wn"); weighted_normals(ob); log("  wn done")
    rep.update(m, uv=uv, seams=seam, uv_s=round(time.time() - t, 2))


# ---------------------------------------------------------------- build
def build():
    d = np.load(A["npz"]); cols = d["colours"]; nl = len(d["lod_fracs"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    R = {"lods": {}, "decimate": {}, "quad": {}}
    hi, hb = make_obj("HI", d, "hi", cols)
    mark_edges(hi, hb, A["sharp_deg"], "brep")
    R["hi"] = {"tris": tris_of(hi), "brep_faces": faces_kept(hi)}
    for li in range(nl):
        ob, b = make_obj(f"LOD{li}", d, f"l{li}", cols)
        r = {"tris_raw": tris_of(ob)}; log("LOD", li)
        finish_low(ob, b, A, r)
        log(" dev"); r.update(tris=tris_of(ob), verts=len(ob.data.vertices), brep_faces=faces_kept(ob), dev=deviation(hi, ob))
        R["lods"][f"LOD{li}"] = r
    # (a2) generic collapse decimation of HI, B-rep boundary verts protected (vertex group, inverted)
    bverts = sorted({int(v) for e in hb for v in e})
    for li in range(1, nl):
        t = time.time()
        target = R["lods"][f"LOD{li}"]["tris"]; log("DEC", li)
        me = hi.data.copy(); ob = bpy.data.objects.new(f"DEC{li}", me); bpy.context.scene.collection.objects.link(ob)
        vg = ob.vertex_groups.new(name="brep_bnd"); vg.add(bverts, 1.0, "REPLACE")
        m = ob.modifiers.new("dec", "DECIMATE"); m.ratio = target / R["hi"]["tris"]
        m.use_collapse_triangulate = True; m.vertex_group = "brep_bnd"; m.invert_vertex_group = True
        dg = bpy.context.evaluated_depsgraph_get()
        for fac in (0.9, 0.6, 0.3, 0.0):  # strongest boundary protection that still reaches ~target
            m.vertex_group_factor = fac; bpy.context.view_layer.update()
            got = len(ob.evaluated_get(dg).data.polygons)
            if got <= target * 1.15:
                break
        select_only([ob]); bpy.ops.object.modifier_apply(modifier="dec")
        r = {"target": target, "protect_factor": fac}
        finish_low(ob, None, A, r)
        r.update(tris=tris_of(ob), brep_faces=faces_kept(ob), dev=deviation(hi, ob), s=round(time.time() - t, 2))
        R["decimate"][f"DEC{li}"] = r
    # (b) QuadriFlow of HI per part (needs manifold) at LOD1 budget (quads -> 2 tris)
    if A.get("quad", True):
        t = time.time(); log("QUAD")
        target = R["lods"][f"LOD{min(1, nl - 1)}"]["tris"]
        me = hi.data.copy(); q = bpy.data.objects.new("QUAD", me); bpy.context.scene.collection.objects.link(q)
        select_only([q])
        try:
            bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.separate(type="MATERIAL"); bpy.ops.object.mode_set(mode="OBJECT")
            pieces = [o for o in bpy.context.scene.objects if o.name.startswith("QUAD")]
            tot = sum(len(o.data.polygons) for o in pieces); ok = 0
            for o in pieces:
                select_only([o])
                n = max(60, int(target / 2 * len(o.data.polygons) / tot))
                bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.remove_doubles(threshold=A["diag"] * 2e-5); bpy.ops.mesh.delete_loose()
                bpy.ops.mesh.fill_holes(sides=0); bpy.ops.mesh.normals_make_consistent(inside=False)
                bpy.ops.object.mode_set(mode="OBJECT")
                # QuadriFlow silently CANCELs on metre-scale CAD (tiny edge lengths): work at x(10/diag) and
                # pre-decimate to ~8x target so it runs in seconds
                from mathutils import Matrix
                k = 10.0 / A["diag"]; o.data.transform(Matrix.Scale(k, 4))
                if len(o.data.polygons) > 16 * n:
                    pm = o.modifiers.new("pd", "DECIMATE"); pm.ratio = 16 * n / len(o.data.polygons)
                    bpy.ops.object.modifier_apply(modifier="pd")
                kw = dict(mode="FACES", target_faces=n, use_preserve_sharp=True, use_preserve_boundary=True,
                          use_mesh_symmetry=False, seed=1)
                res = bpy.ops.object.quadriflow_remesh(**kw)
                if len(o.data.polygons) > 4 * n:  # still not manifold -> voxel remesh first (standard fallback)
                    vr = o.modifiers.new("vx", "REMESH"); vr.mode = "VOXEL"; vr.voxel_size = 10.0 / 250
                    bpy.ops.object.modifier_apply(modifier="vx"); res = bpy.ops.object.quadriflow_remesh(**kw)
                ok += len(o.data.polygons) <= 4 * n
                o.data.transform(Matrix.Scale(1 / k, 4))
            select_only(pieces); bpy.ops.object.join(); q = bpy.context.view_layer.objects.active; q.name = "QUAD"
            q.data.materials.clear()
            for i, c in enumerate(cols):
                q.data.materials.append(part_mat(i, c))
            transfer_face_ids(hi, q)
            r = {"target_tris": target, "parts_ok": ok, "parts": len(pieces),
                 "quads": sum(len(p.vertices) == 4 for p in q.data.polygons)}
            finish_low(q, None, A, r)
            r.update(tris=tris_of(q), brep_faces=faces_kept(q), dev=deviation(hi, q), s=round(time.time() - t, 2))
            R["quad"] = r
        except Exception as e:  # noqa: BLE001
            R["quad"] = {"error": repr(e)}
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "game.blend"))
    json.dump(R, open(os.path.join(OUT, "build_report.json"), "w"), indent=1)


# ---------------------------------------------------------------- bake
def gpu_setup(scene):
    scene.render.engine = "CYCLES"
    pr = bpy.context.preferences.addons["cycles"].preferences
    for dt in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            pr.compute_device_type = dt; pr.get_devices()
            if any(dv.type == dt for dv in pr.devices):
                for dv in pr.devices:
                    dv.use = dv.type == dt
                scene.cycles.device = "GPU"
                return dt
        except TypeError:
            continue
    scene.cycles.device = "CPU"
    return "CPU"


def hi_bake_mat(hi):
    """single emission material for HI; per-mode link chooses id_face / id_mat / pos_grad."""
    me = hi.data
    fid = np.zeros(len(me.polygons), np.int32); me.attributes["brep_face"].data.foreach_get("value", fid)
    mid = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get("material_index", mid)
    nl = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get("loop_total", nl)
    for nm, vals in (("id_face", [hash_col(int(f)) for f in fid]), ("id_mat", [hash_col(int(m) + 7919) for m in mid])):
        ca = me.color_attributes.new(nm, "BYTE_COLOR", "CORNER")
        ca.data.foreach_set("color", np.repeat(np.array(vals, "f4"), nl, axis=0).ravel())
    co = np.array([v.co[:] for v in me.vertices]); lo, sz = co.min(0), np.maximum(np.ptp(co, 0), 1e-9)
    m = bpy.data.materials.new("hi_bake"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    src = {}
    for nm in ("id_face", "id_mat"):
        a = N.new("ShaderNodeVertexColor"); a.layer_name = nm; src[nm] = a.outputs["Color"]
    g = N.new("ShaderNodeNewGeometry"); mp = N.new("ShaderNodeMapping"); mp.vector_type = "POINT"
    mp.inputs["Location"].default_value = Vector(-lo / sz); mp.inputs["Scale"].default_value = Vector(1 / sz)
    nt.links.new(g.outputs["Position"], mp.inputs["Vector"]); src["pos_grad"] = mp.outputs[0]
    for i in range(len(me.materials)):
        me.materials[i] = m
    return lambda k: nt.links.new(src[k], em.inputs["Color"])


def bake():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "game.blend"))
    sc = bpy.context.scene; dev = gpu_setup(sc)
    sc.cycles.use_denoising = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("bake")
    sc.world.light_settings.distance = A["diag"] * 0.3  # AO reach ~ a third of the part
    hi = bpy.data.objects["HI"]; link = hi_bake_mat(hi)
    R = {"device": dev, "res": A["res"], "lods": {}}
    lods = sorted(o for o in bpy.data.objects.keys() if o.startswith("LOD"))
    bset = A.get("bake_lods") or lods
    for ln in lods:
        if ln not in bset:
            continue
        lo = bpy.data.objects[ln]; t0 = time.time()
        dv = deviation(hi, lo)
        ext = dv["max_out_mm"] * 1e-3 * 1.5 + A["diag"] * 2e-4
        ray = ext + dv["max_in_mm"] * 1e-3 * 1.5 + A["diag"] * 2e-4
        # bake-target mats on low (copy of part mats + image node active)
        res = A["res"]; d = os.path.join(OUT, "maps", ln); os.makedirs(d, exist_ok=True)
        timgs = {}
        for i, m0 in enumerate(list(lo.data.materials)):
            m = m0.copy(); lo.data.materials[i] = m
            n = m.node_tree.nodes.new("ShaderNodeTexImage"); n.name = "bake"; m.node_tree.nodes.active = n
        r = {"cage_extrusion_mm": ext * 1e3, "max_ray_mm": ray * 1e3, "dev": dv, "maps": {}}
        for kind, btype, spp in A["maps"]:
            img = bpy.data.images.new(f"{ln}_{kind}", res, res, alpha=False)
            if kind in ("n_tan", "pos_grad"):
                img.colorspace_settings.name = "Non-Color"
            for m in lo.data.materials:
                m.node_tree.nodes["bake"].image = img
            if btype == "EMIT":
                link(kind)
            sc.cycles.samples = spp
            for a in ("visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
                setattr(lo, a, False)  # low must not occlude the high during AO rays
            for o in bpy.data.objects:  # other LODs / variants overlap HI and would occlude AO rays
                if o.type == "MESH":
                    o.hide_render = o not in (hi, lo)
            select_only([hi, lo], lo)
            t = time.time()
            kw = dict(type=btype, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray,
                      margin=A["margin_px"], use_clear=True)
            if btype == "NORMAL":
                kw.update(normal_space="TANGENT")
            bpy.ops.object.bake(**kw)
            f = os.path.join(d, f"{kind}.png"); img.filepath_raw = f; img.file_format = "PNG"; img.save()
            r["maps"][kind] = round(time.time() - t, 2); timgs[kind] = img
        r["bake_s"] = round(time.time() - t0, 2)
        R["lods"][ln] = r
    json.dump(R, open(os.path.join(OUT, "bake_report.json"), "w"), indent=1)


# ---------------------------------------------------------------- final: export + preview
def game_mat(base, d, kind_ok, i):
    m = base.copy(); m.name = f"{base.name}_{os.path.basename(d)}"; nt = m.node_tree; N = nt.nodes
    b = N["Principled BSDF"]
    if os.path.exists(os.path.join(d, "n_tan.png")):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, "n_tan.png"), check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        nm = N.new("ShaderNodeNormalMap"); nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if os.path.exists(os.path.join(d, "ao.png")):  # glTF occlusion via the exporter's custom group
        g = bpy.data.node_groups.get("glTF Material Output")
        if g is None:
            g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
            g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
        gn = N.new("ShaderNodeGroup"); gn.node_tree = g
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, "ao.png"), check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        sp = N.new("ShaderNodeSeparateColor"); nt.links.new(t.outputs["Color"], sp.inputs[0])
        nt.links.new(sp.outputs[0], gn.inputs["Occlusion"])
    return m


def final():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "game.blend"))
    sc = bpy.context.scene
    lods = sorted(o for o in bpy.data.objects.keys() if o.startswith("LOD"))
    R = {"exports": []}
    for ln in lods:
        lo = bpy.data.objects[ln]; d = os.path.join(OUT, "maps", ln)
        for i, m in enumerate(list(lo.data.materials)):
            lo.data.materials[i] = game_mat(m, d, True, i)
        select_only([lo])
        f = os.path.join(OUT, f"{A['name']}_{ln}.glb")
        bpy.ops.export_scene.gltf(filepath=f, export_format="GLB", use_selection=True, export_yup=True,
                                  export_apply=True, export_tangents=True)
        R["exports"].append(f)
    select_only([bpy.data.objects[n] for n in lods])
    for n in lods:
        bpy.data.objects[n].name = f"{A['name']}_{n}"
    f = os.path.join(OUT, f"{A['name']}.fbx")
    bpy.ops.export_scene.fbx(filepath=f, use_selection=True, path_mode="COPY", embed_textures=True,
                             mesh_smooth_type="OFF", use_tspace=True, axis_forward="-Z", axis_up="Y")
    R["exports"].append(f)
    for n in lods:
        bpy.data.objects[f"{A['name']}_{n}"].name = n
    # preview (EEVEE): HI | LOD0+bake | LOD{last}+bake | QUAD (no bake)
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng; break
        except TypeError:
            continue
    hi = bpy.data.objects["HI"]
    shown = ["HI", "LOD0", lods[-1]] + (["QUAD"] if "QUAD" in bpy.data.objects else [])
    co = np.array([v.co[:] for v in hi.data.vertices]); lo_, hi_ = co.min(0), co.max(0)
    ctr = Vector(((lo_ + hi_) / 2).tolist()); Rr = float(np.linalg.norm(hi_ - lo_)) / 2
    res = A["preview_res"]
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.33, 0.35, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6; sc.world = w
    for nm, en, rot in (("key", 4.0, (0.9, 0.2, -0.9)), ("rim", 2.5, (-0.8, 0.1, 2.4))):
        L = bpy.data.lights.new(nm, "SUN"); L.energy = en; L.angle = 0.15
        lo2 = bpy.data.objects.new(nm, L); lo2.rotation_euler = rot; sc.collection.objects.link(lo2)
    cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.lens = 70; cd.clip_end = Rr * 50
    views = {"hero": Vector((-1.0, -1.15, 0.6)), "rear": Vector((1.0, 0.9, 0.45))}
    files = {}
    for vn, dvec in views.items():
        dvec = dvec.normalized(); cam.location = ctr + dvec * Rr * 3.6
        cam.rotation_euler = (-dvec).to_track_quat("-Z", "Y").to_euler()
        for s in shown:
            for o in bpy.data.objects:
                if o.type == "MESH":
                    o.hide_render = o.name != s
            if s == "HI":
                for i in range(len(hi.data.materials)):
                    hi.data.materials[i] = _part_mats()[i]
            f = os.path.join(OUT, "preview", f"{vn}_{s}.png"); sc.render.filepath = f
            bpy.ops.render.render(write_still=True); files[f"{vn}_{s}"] = f
    R["preview_tiles"] = files; R["shown"] = shown; R["engine"] = sc.render.engine
    json.dump(R, open(os.path.join(OUT, "final_report.json"), "w"), indent=1)


def _part_mats():
    return [m for m in bpy.data.materials if m.name.startswith("part") and "_" not in m.name and "." not in m.name]


{"build": build, "bake": bake, "final": final}[MODE]()
