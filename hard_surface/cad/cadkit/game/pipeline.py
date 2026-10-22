"""Host orchestration: model.py -> out/game/<name>/ {meshes.npz, game.blend, maps/LOD*/..., *.glb, *.fbx, preview/, report.json}."""
from __future__ import annotations

import json
import os
import shutil
import subprocess

_NOWIN_KW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}  # no stray console windows (Windows)
import threading
import time

import numpy as np

from cadkit.runner import BLENDER
from .tess import build_meshes
from .uvstats import curvature_from_normal

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(os.path.dirname(HERE))
MAPS = [["n_tan", "NORMAL", 1], ["ao", "AO", 64], ["id_face", "EMIT", 1], ["id_mat", "EMIT", 1], ["pos_grad", "EMIT", 1]]


class VramPeak:
    """Polls nvidia-smi used memory; peak minus baseline approximates the bake process footprint."""

    def __init__(self, dt=0.25):
        self.dt, self.base, self.peak, self._stop = dt, None, 0, False

    @staticmethod
    def used():
        try:
            o = subprocess.run(**_NOWIN_KW, args=["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=5).stdout
            return int(o.split()[0])
        except Exception:  # noqa: BLE001
            return None

    def __enter__(self):
        self.base = self.used()
        self.peak = self.base or 0
        self._t = threading.Thread(target=self._run, daemon=True); self._t.start()
        return self

    def _run(self):
        while not self._stop:
            u = self.used()
            if u is not None:
                self.peak = max(self.peak, u)
            time.sleep(self.dt)

    def __exit__(self, *a):
        self._stop = True; self._t.join()

    @property
    def delta_mb(self):
        return None if self.base is None else self.peak - self.base


def blender(mode, args, out, timeout=1800):
    ap = os.path.join(out, f"args_{mode}.json")
    json.dump(args, open(ap, "w"), indent=1)
    cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "--python",
           os.path.join(HERE, "bl_game.py"), "--", mode, ap]
    p = subprocess.run(**_NOWIN_KW, args=cmd, capture_output=True, text=True, timeout=timeout)
    open(os.path.join(out, f"log_{mode}.txt"), "w", encoding="utf-8").write(p.stdout + "\n---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"blender {mode} failed:\n{p.stdout[-2500:]}\n{p.stderr[-1500:]}")
    return json.load(open(os.path.join(out, f"{mode}_report.json")))


def curvature_maps(out):
    from PIL import Image
    for d in sorted(os.listdir(os.path.join(out, "maps"))):
        f = os.path.join(out, "maps", d, "n_tan.png")
        if os.path.exists(f):
            n = np.asarray(Image.open(f).convert("RGB"), "f4") / 255
            Image.fromarray((curvature_from_normal(n) * 255).astype(np.uint8)).save(os.path.join(out, "maps", d, "curvature.png"))


def sheet(out, name, rep, dst, tile=480):
    """2 rows lit EEVEE (hero, rear) x [HI, LOD0, LODn, QUAD] + row of LOD0 maps. Labels with tri counts."""
    from PIL import Image, ImageDraw
    fr = rep["final"]; shown = fr["shown"]; b = rep["build"]
    tri = {"HI": b["hi"]["tris"], **{k: v["tris"] for k, v in b["lods"].items()}, "QUAD": b.get("quad", {}).get("tris")}
    lab = {"HI": "HI (CAD)", "QUAD": "QUAD remesh, no bake"}
    cols = max(len(shown), 6)
    W = Image.new("RGB", (cols * tile, 3 * tile + 30), (24, 24, 26)); dr = ImageDraw.Draw(W)
    dr.text((8, 8), f"{name}: high vs low+bake  (EEVEE)  bake {rep['bake'].get('total_s')}s  vram +{rep['vram_mb']} MB",
            fill=(230, 230, 230))
    for r, vn in enumerate(("hero", "rear")):
        for c, s in enumerate(shown):
            im = Image.open(fr["preview_tiles"][f"{vn}_{s}"]).convert("RGB").resize((tile, tile))
            W.paste(im, (c * tile, 30 + r * tile))
            if r == 0:
                dr.text((c * tile + 8, 36), f"{lab.get(s, s + ' + bake')}  {tri.get(s)} tris", fill=(255, 220, 120))
    md = os.path.join(out, "maps", "LOD0")
    for c, k in enumerate(["n_tan", "ao", "curvature", "id_face", "id_mat", "pos_grad"]):
        f = os.path.join(md, f"{k}.png")
        if os.path.exists(f):
            W.paste(Image.open(f).convert("RGB").resize((tile, tile)), (c * tile, 30 + 2 * tile))
            dr.text((c * tile + 8, 36 + 2 * tile), f"LOD0 {k}", fill=(120, 220, 255))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    W.save(dst, quality=85)
    return dst


def _save(rp, rep):
    json.dump(rep, open(rp, "w"), indent=1, default=str)


def run(model_py, out, name=None, res=2048, lod_fracs=(1.0, 0.5, 0.25), lod0_budget=None, sharp_deg=30.0,
        quad=True, preview_res=640, previews_dir=None, stages=("tess", "build", "bake", "final")):
    name = name or os.path.basename(os.path.dirname(os.path.abspath(model_py)))
    os.makedirs(out, exist_ok=True)
    rp = os.path.join(out, "report.json")
    rep = json.load(open(rp)) if os.path.exists(rp) else {"name": name}
    npz = os.path.join(out, "meshes.npz")
    if "tess" in stages:
        rep["tess"] = build_meshes(model_py, npz, lod_fracs, lod0_budget); _save(rp, rep)
    base = {"out": out, "cad_dir": CAD, "npz": npz, "res": res, "sharp_deg": sharp_deg, "margin": 8 / res,
            "margin_px": 8, "stretch_fallback": 1.6, "quad": quad, "diag": rep["tess"]["diag_m"], "maps": MAPS,
            "name": name, "preview_res": preview_res}
    if "build" in stages:
        t = time.time(); rep["build"] = blender("build", base, out); rep["build"]["s"] = round(time.time() - t, 1); _save(rp, rep)
    if "bake" in stages:
        t = time.time()
        with VramPeak() as vp:
            rep["bake"] = blender("bake", base, out)
        rep["bake"]["total_s"] = round(time.time() - t, 1); rep["vram_mb"] = vp.delta_mb
        rep["vram_note"] = ("nvidia-smi whole-GPU peak-minus-baseline during the bake process (WDDM gives no per-process "
                            "numbers; includes CUDA/OptiX context + other apps\u0027 churn)")
        rep["vram_payload_est_mb"] = round((rep["build"]["hi"]["tris"] * 200 + res * res * 16 * 2) / 1e6, 1)
        curvature_maps(out); _save(rp, rep)
    if "final" in stages:
        rep["final"] = blender("final", base, out)
        rep["sheet"] = sheet(out, name, rep, os.path.join(out, "preview_sheet.jpg"))
        if previews_dir:
            os.makedirs(previews_dir, exist_ok=True)
            from PIL import Image
            im = Image.open(rep["sheet"]); im.thumbnail((1600, 1600))
            dst = os.path.join(previews_dir, f"{name}_game.jpg"); im.save(dst, quality=80); rep["preview_small"] = dst
    json.dump(rep, open(rp, "w"), indent=1, default=str)
    return rep
