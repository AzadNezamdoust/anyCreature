"""Close-up comparison per part: the source region next to the same region of the build, at 3x.

The pass sheet (run_pass.py compare.png) shows whole views at 1024 px, where a hatch or a grille is a handful of
pixels. This renders every view at K x 1024 on the judge's own registration (frame.json + the pass's sigma, concept
camera for the concept view: its `persp` pinhole when concept_cam.json has one, concept_camera.py) and cuts, per
semantic part (ob["part"]), the part's projected box out of the reference
and out of the render:

    REFERENCE crop | BUILD crop | BUILD + reference ink (red)

The third tile paints the reference's dark lines and silhouette edge over the build, so an offset hatch, a missing
slat or a wrong angle shows as red that does not sit on a model edge.

    blender -b --factory-startup --python-exit-code 1 --python scripts/hs/closeups.py -- --subject <s>
        [--build <py>] [--out-dir <dir>] [--k 3] [--views 2] [--parts a,b,c]

Writes <out-dir>/closeups/<part>.png and closeups/index.json. Needs stats.json (or the newest passN_stats.json) in
the subject folder for sigma: run a pass first. Read-only for everything else.
"""
import glob
import json
import os
import sys
import types

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True


def _load_run_pass():
    path = os.path.join(HERE, "run_pass.py")
    with open(path, encoding="utf-8") as f:
        src = f.read().rstrip()
    if not src.endswith("\nmain()"):
        raise SystemExit("closeups.py: run_pass.py no longer ends with a bare main() call; update _load_run_pass")
    mod = types.ModuleType("hs_run_pass")
    mod.__file__ = path
    exec(compile(src[:-len("main()")], path, "exec"), mod.__dict__)
    return mod


rp = _load_run_pass()
import concept_camera as CCAM  # noqa: E402  (scripts/hs: the `persp` block of concept_cam.json, when present)
imgio = rp.imgio
SUBJECT, SDIR, ODIR, ROOTDIR, TURN = rp.SUBJECT, rp.SDIR, rp.ODIR, rp.ROOTDIR, rp.TURN
K = int(rp._arg("--k", "3"))
NVIEWS = int(rp._arg("--views", "2"))
ONLY = [p for p in (rp._arg("--parts") or "").split(",") if p]
MIN_PX, PAD, TILE_MAX = 90, 0.22, 600


def pass_sigma():
    cands = [os.path.join(SDIR, "stats.json")] + sorted(
        glob.glob(os.path.join(SDIR, "pass*_stats.json")), key=os.path.getmtime, reverse=True)
    if ODIR != SDIR:
        cands = sorted(glob.glob(os.path.join(ODIR, "pass*_stats.json")), key=os.path.getmtime, reverse=True) + \
            [os.path.join(ODIR, "stats.json")] + cands
    for p in cands:
        if os.path.exists(p):
            st = rp._json(p)
            return float((st.get("judge") or {}).get("sigmaRaw") or st["sigma"]), p
    raise SystemExit("closeups.py: no stats.json / passN_stats.json — run scripts/hs/run_pass.py first (sigma)")


def author_points(ob):
    """World-space vertices in the author frame (x = Blender X, y = Blender Z, z = -Blender Y)."""
    n = len(ob.data.vertices)
    co = np.empty(n * 3, np.float32)
    ob.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    M = np.array(ob.matrix_world)
    w = co @ M[:3, :3].T + M[:3, 3]
    return np.stack([w[:, 0], w[:, 2], -w[:, 1]], axis=1)


def upscale(arr, k):
    """Bilinear x k."""
    H, W = arr.shape[:2]
    ys = (np.arange(H * k) + 0.5) / k - 0.5
    xs = (np.arange(W * k) + 0.5) / k - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, H - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 1)
    y1, x1 = np.minimum(y0 + 1, H - 1), np.minimum(x0 + 1, W - 1)
    fy = np.clip(ys - y0, 0, 1)[:, None, None]
    fx = np.clip(xs - x0, 0, 1)[None, :, None]
    a = arr[y0][:, x0] * (1 - fx) + arr[y0][:, x1] * fx
    b = arr[y1][:, x0] * (1 - fx) + arr[y1][:, x1] * fx
    return a * (1 - fy) + b * fy


def white(arr):
    rgb = arr[..., :3]
    if arr.shape[2] == 4:
        rgb = rgb * arr[..., 3:4] + (1 - arr[..., 3:4])
    return rgb.astype(np.float32)


def ink_overlay(build, ref):
    """Build crop + the reference's dark lines and silhouette edge in red."""
    dark = ref.max(axis=2) < 0.30
    fg = ref.min(axis=2) < rp.FG_MAX
    edge = np.zeros_like(fg)
    edge[1:-1, 1:-1] = fg[1:-1, 1:-1] & ~(fg[:-2, 1:-1] & fg[2:, 1:-1] & fg[1:-1, :-2] & fg[1:-1, 2:])
    for _ in range(max(1, K // 2)):                      # thicken the silhouette edge a little
        e = edge.copy()
        e[1:] |= edge[:-1]
        e[:, 1:] |= edge[:, :-1]
        edge = e
    out = build * 0.75 + 0.25
    out[dark] = out[dark] * 0.35 + np.array([0.9, 0.05, 0.05], np.float32) * 0.65
    out[edge] = np.array([1.0, 0.0, 0.0], np.float32)
    return out


def fit(img, wmax):
    h, w = img.shape[:2]
    if w <= wmax and h <= wmax:
        return img
    f = wmax / max(w, h)
    return imgio.resize_area(img, max(1, int(w * f)), max(1, int(h * f)))


def main():
    sigma, src = pass_sigma()
    mod = rp.load_build()
    root, parts = mod.build()
    objs = [o for o in parts if o.type == "MESH"]
    root.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    groups = {}
    for o in objs:
        groups.setdefault(str(o.get("part") or o.name), []).append(author_points(o))
    groups = {g: np.concatenate(v) for g, v in groups.items() if not ONLY or g in ONLY}
    rp.toon_materials()
    sc = rp.setup_scene()
    sc.render.line_thickness = 1.0 * K
    for ls in sc.view_layers[0].freestyle_settings.linesets:
        ls.linestyle.thickness = 1.0 * K
    frame = rp._json(os.path.join(SDIR, "frame.json"))
    cc = rp._json(os.path.join(SDIR, "concept_cam.json"))
    cstats = rp._json(src)
    cref = os.path.join(ROOTDIR, cstats.get("concept_ref") or cc.get("target"))
    views = {}                                           # name -> (right, up, ox, oy, s_eff, w, h, ref, render)
    os.makedirs(os.path.join(ODIR, "closeups"), exist_ok=True)
    tmp = os.path.join(ODIR, "closeups", "_view.png")
    for v in frame["names"]:
        V = frame["views"][v]
        spec = V["spec"]
        rp.view_scale(root, V)
        root.scale = tuple(c * sigma for c in root.scale)
        bpy.context.view_layer.update()
        cam = rp.camera_for(spec["right"], spec["up"], V["ox"] * K, V["oy"] * K, frame["s"] * K, V["w"] * K, V["h"] * K)
        back = Vector(spec["right"]).cross(Vector(spec["up"]))
        rp.set_light(tuple(back + Vector((0, 0.8, 0)) + Vector(spec["right"]) * -0.15))
        rp.render_to(tmp, cam, V["w"] * K, V["h"] * K)
        root.scale = (1.0, 1.0, 1.0)
        r, u = np.array(spec["right"], float), np.array(spec["up"], float)
        kr, ku = V.get("kr", 1), V.get("ku", 1)
        views[v] = (r * kr * sigma, u * ku * sigma, V["ox"], V["oy"], frame["s"], V["w"], V["h"],
                    white(imgio.load(os.path.join(TURN, spec.get("file", f"{v}.png")))), white(rp.render_to.last))
    bpy.context.view_layer.update()
    cw, ch = cc.get("w", 1024), cc.get("h", 1024)
    if CCAM.is_persp(cc):   # solve_persp_cam.py pinhole (concept_camera.py): FOV / shift are resolution-free
        cam = CCAM.blender_camera(cc)
    else:
        cam = rp.camera_for(cc["basis"]["right"], cc["basis"]["up"], cc["o"][0] * K, cc["o"][1] * K, cc["s"] * K, cw * K, ch * K)
    rp.set_light((0.15, 1.0, 0.2))
    rp.render_to(tmp, cam, cw * K, ch * K)
    views["concept"] = (np.array(cc["basis"]["right"], float), np.array(cc["basis"]["up"], float), cc["o"][0], cc["o"][1],
                        cc["s"], cw, ch, white(imgio.load(cref)), white(rp.render_to.last))
    os.remove(tmp)

    index = {}
    for g, P in sorted(groups.items()):
        boxes = {}
        for v, (r, u, ox, oy, s, w, h, _ref, _new) in views.items():
            if v == "concept" and CCAM.is_persp(cc):   # pinhole: project through the persp block's P
                Pm = np.array(cc["persp"]["P"], float)
                hw = P @ Pm[:, :3].T + Pm[:, 3]
                px, py = hw[:, 0] / hw[:, 2], hw[:, 1] / hw[:, 2]
            else:
                px, py = ox + s * (P @ r), oy - s * (P @ u)
            x0, x1, y0, y1 = px.min(), px.max(), py.min(), py.max()
            pw, ph = max(x1 - x0, MIN_PX), max(y1 - y0, MIN_PX)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            pw, ph = pw * (1 + 2 * PAD) + 16, ph * (1 + 2 * PAD) + 16
            bx0, bx1 = int(max(0, cx - pw / 2)), int(min(w, cx + pw / 2))
            by0, by1 = int(max(0, cy - ph / 2)), int(min(h, cy + ph / 2))
            if bx1 - bx0 > 8 and by1 - by0 > 8:
                boxes[v] = (bx0, by0, bx1, by1, (x1 - x0) * (y1 - y0))
        ortho = sorted([v for v in boxes if v != "concept"], key=lambda v: -boxes[v][4])[:NVIEWS]
        chosen = ortho + (["concept"] if "concept" in boxes else [])
        rows = []
        for v in chosen:
            x0, y0, x1, y1, _ = boxes[v]
            ref = upscale(views[v][7][y0:y1, x0:x1], K)
            new = views[v][8][y0 * K:y1 * K, x0 * K:x1 * K]
            hh, ww = min(ref.shape[0], new.shape[0]), min(ref.shape[1], new.shape[1])
            ref, new = ref[:hh, :ww], new[:hh, :ww]
            tiles = [fit(t, TILE_MAX) for t in (ref, new, ink_overlay(new, ref))]
            th, tw = tiles[0].shape[:2]
            row = np.ones((th + 26, tw * 3 + 20, 3), np.float32)
            rp.draw_text(row, 4, 4, f"{v}  SOURCE | BUILD | BUILD + SOURCE INK   px {x0},{y0}-{x1},{y1}", 2)
            for i, t in enumerate(tiles):
                row[26:26 + th, i * (tw + 10):i * (tw + 10) + tw] = t[:th, :tw]
            rows.append(row)
        if not rows:
            continue
        W = max(r.shape[1] for r in rows)
        H = sum(r.shape[0] for r in rows) + 28 + 8 * len(rows)
        sheet = np.ones((H, W, 3), np.float32)
        rp.draw_text(sheet, 4, 4, f"{SUBJECT} / {g}", 2)
        y = 28
        for r in rows:
            sheet[y:y + r.shape[0], :r.shape[1]] = r
            y += r.shape[0] + 8
        path = os.path.join(ODIR, "closeups", f"{g}.png")
        imgio.save(path, sheet)
        index[g] = {"file": f"closeups/{g}.png", "views": chosen}
        print("CLOSEUP", g, chosen)
    with open(os.path.join(ODIR, "closeups", "index.json"), "w", encoding="utf-8") as f:
        json.dump({"subject": SUBJECT, "sigma": sigma, "sigma_from": os.path.basename(src), "k": K, "parts": index}, f, indent=1)
    print("DONE", os.path.join(ODIR, "closeups"), len(index), "parts")


main()
