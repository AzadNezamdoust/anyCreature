"""part_pass.py -- run_pass.py + a per-part ID pass in the same Blender process (for part_score.mjs).

    blender -b --factory-startup --python-exit-code 1 --python scripts/hs/score/part_pass.py -- --subject <s>
        --build <py> --out-dir <dir> [--pass N] [--ids-only]

1. Runs scripts/hs/run_pass.py's main() unchanged (same build, judge sigma fit, ortho renders passN_{view}.png,
   passN_stats.json in <dir>). --ids-only skips it and reuses <dir>/passN_stats.json for sigma.
2. Re-renders the four ortho views in the judge's framing (frame.json, kr/ku, the pass sigma) with Workbench, flat
   unlit object colours, no AA, no ink: every mesh gets a colour keyed to its semantic role ob["part"] (else its
   name). The visible (occlusion-aware) role per pixel is written as raw uint8 <dir>/passN_ids_<view>.bin
   (W*H, row 0 = top, 0 = background, k = index k-1 in passN_ids.json "parts").
3. When out/blender-hs/<s>/concept_cam.json exists, the same ID pass in the judge's concept camera (model unscaled, as
   run_pass.py's passN_concept.png; its `persp` pinhole when the file has one): passN_ids_concept.bin, "concept" in
   passN_ids.json "views". The concept render is
   NOT pixel-aligned with refs/<s>.png; part_score.mjs aligns it per part.

The ID maps are pixel-registered with passN_<view>.png and subjects/<s>/turnaround/<view>.png (same frame.json camera);
part_score.mjs applies the whole-view registration shift on top. Writes only into <dir>.
"""
import glob
import json
import os
import sys
import types

import bpy
import numpy as np
from mathutils import Vector

SCORE = os.path.dirname(os.path.abspath(__file__))
HS = os.path.dirname(SCORE)
sys.path.insert(0, HS)
sys.dont_write_bytecode = True


def _load_run_pass():
    path = os.path.join(HS, "run_pass.py")
    with open(path, encoding="utf-8") as f:
        src = f.read().rstrip()
    if not src.endswith("\nmain()"):
        raise SystemExit("part_pass.py: run_pass.py no longer ends with a bare main() call")
    mod = types.ModuleType("hs_run_pass")
    mod.__file__ = path
    exec(compile(src[:-len("main()")], path, "exec"), mod.__dict__)
    return mod


rp = _load_run_pass()


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def palette(n):
    """n well-separated sRGB byte colours (6 levels per channel = 215 usable, black excluded)."""
    lv = [0, 51, 102, 153, 204, 255]
    cols = [(r, g, b) for r in lv for g in lv for b in lv if (r, g, b) != (0, 0, 0)]
    step = max(1, len(cols) // max(1, n))
    out = cols[::step][:n]
    if len(out) < n:
        raise SystemExit(f"part_pass.py: {n} parts > {len(cols)} ID colours")
    return out


def main():
    tag = rp.TAG
    if "--ids-only" not in rp.argv:
        rp.main()
        objs = [o for o in bpy.data.objects if o.type == "MESH" and o.parent is not None]
    else:
        mod = rp.load_build()
        _root, parts = mod.build()
        objs = [o for o in parts if o.type == "MESH"]
    hsmod = sys.modules.get("hs")   # guard clamps of this build (HS_GUARDS=1 or begin(..., guards=True)); part_search reads them
    print("GUARDS", "on" if getattr(hsmod, "GUARDS", False) else "off")
    for w in list(getattr(hsmod, "GUARD_WARN", None) or []):
        print("GUARD_WARN", w)
    stats_path = os.path.join(rp.ODIR, f"{tag}_stats.json")
    st = rp._json(stats_path)
    sigma = float((st.get("judge") or {}).get("sigmaRaw") or st["sigma"])
    root = getattr(sys.modules.get("hs"), "ROOT", None)
    root = root or next(o for o in bpy.data.objects if o.type == "EMPTY" and o.parent is None and any(c in objs for c in o.children))
    root.scale = (1.0, 1.0, 1.0)

    roles = sorted({str(o.get("part") or o.name) for o in objs})
    cols = palette(len(roles))
    col_of = dict(zip(roles, cols))
    for o in objs:
        r, g, b = col_of[str(o.get("part") or o.name)]
        o.color = (srgb_to_lin(r / 255), srgb_to_lin(g / 255), srgb_to_lin(b / 255), 1.0)
    for o in bpy.data.objects:          # hide anything that is not a part mesh (cameras / lights are not rendered anyway)
        if o.type == "MESH" and o not in objs:
            o.hide_render = True

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.use_freestyle = False
    sc.render.film_transparent = True
    sc.render.dither_intensity = 0.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.display.render_aa = "OFF"
    sh = sc.display.shading
    sh.light = "FLAT"
    sh.color_type = "OBJECT"
    for k in ("show_object_outline", "show_cavity", "show_shadows", "show_specular_highlight", "show_xray",
              "use_dof", "show_backface_culling"):
        if hasattr(sh, k):
            setattr(sh, k, False)
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0

    frame = rp._json(os.path.join(rp.SDIR, "frame.json"))
    pal = np.array(cols, np.float32)
    tmp = os.path.join(rp.ODIR, f"{tag}_ids_tmp.png")
    meta = {"subject": rp.SUBJECT, "sigma": sigma, "parts": roles, "colours": cols, "views": {}}
    cc_path = os.path.join(rp.SDIR, "concept_cam.json")
    cc = rp._json(cc_path) if os.path.exists(cc_path) else None
    jobs = list(frame["names"]) + (["concept"] if cc else [])
    for v in jobs:
        if v == "concept":   # the judge's registered concept camera, model unscaled (as run_pass.py's concept render)
            W, H = cc.get("w", 1024), cc.get("h", 1024)
            root.scale = (1.0, 1.0, 1.0)
            bpy.context.view_layer.update()
            if isinstance(cc.get("persp"), dict):   # solve_persp_cam.py pinhole (concept_camera.py), as run_pass.py
                import concept_camera
                cam = concept_camera.blender_camera(cc)
            else:
                cam = rp.camera_for(cc["basis"]["right"], cc["basis"]["up"], cc["o"][0], cc["o"][1], cc["s"], W, H)
            V = {"w": W, "h": H}
        else:
            V = frame["views"][v]
            spec = V["spec"]
            rp.view_scale(root, V)
            root.scale = tuple(c * sigma for c in root.scale)
            bpy.context.view_layer.update()
            cam = rp.camera_for(spec["right"], spec["up"], V["ox"], V["oy"], frame["s"], V["w"], V["h"])
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = V["w"], V["h"]
        sc.render.resolution_percentage = 100
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        root.scale = (1.0, 1.0, 1.0)
        a = rp.imgio.load(tmp)                              # raw sRGB bytes / 255
        rgb = a[..., :3] * 255.0
        d = ((rgb[..., None, :] - pal[None, None, :, :]) ** 2).sum(-1)
        idx = d.argmin(-1).astype(np.uint8) + 1
        bad = d.min(-1) > 3 * 20.0 ** 2
        idx[(a[..., 3] < 0.5)] = 0
        ids = idx.astype(np.uint8)
        ids.tofile(os.path.join(rp.ODIR, f"{tag}_ids_{v}.bin"))
        counts = {roles[k - 1]: int((ids == k).sum()) for k in range(1, len(roles) + 1)}
        meta["views"][v] = {"w": V["w"], "h": V["h"], "file": f"{tag}_ids_{v}.bin", "px": counts,
                            "undecoded_px": int((bad & (a[..., 3] >= 0.5)).sum())}
        print("IDS", v, json.dumps(counts), "undecoded", meta["views"][v]["undecoded_px"])
    os.remove(tmp)
    with open(os.path.join(rp.ODIR, f"{tag}_ids.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print("IDS DONE", rp.ODIR)


main()
