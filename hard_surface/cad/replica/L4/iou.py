"""Ortho silhouettes of out/replica/L4/r<N>/mesh.npz vs reference masks; IoU + dims. Writes overlay_<view>.png.
Registration: both silhouettes are scaled to the published overall width 153 mm (bbox), anchored at bbox min."""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
CAD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rnd = sys.argv[1]; out = os.path.join(CAD, "out", "replica", "L4", f"r{rnd}")
z = np.load(os.path.join(out, "mesh.npz")); n = len(z["names"])
V = [z[f"v_{i}"] * 1000 for i in range(n)]; T = [z[f"t_{i}"] for i in range(n)]
names = list(z["names"])
PX = 4.0  # px per mm
def sil(ax_u, ax_v, flip_u=False, skip=()):
    allv = np.vstack([v for v, nm in zip(V, names) if nm not in skip])
    lo = allv.min(0); hi = allv.max(0)
    w = int((hi[ax_u] - lo[ax_u]) * PX) + 1; h = int((hi[ax_v] - lo[ax_v]) * PX) + 1
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    for v, t, nm in zip(V, T, names):
        if nm in skip: continue
        u = (v[:, ax_u] - lo[ax_u]) * PX; vv = (hi[ax_v] - v[:, ax_v]) * PX
        if flip_u: u = w - 1 - u
        for a, b, c in t:
            d.polygon([(u[a], vv[a]), (u[b], vv[b]), (u[c], vv[c])], fill=255)
    return np.asarray(im) > 0, hi - lo
def iou(model, refname, width_mm, tag):
    ref = Image.open(os.path.join(CAD, "refs", "L4", refname)).convert("L")
    s = model.shape[1] / ref.size[0]   # register: same overall width (153 mm)
    ref = np.asarray(ref.resize((model.shape[1], max(1, int(ref.size[1] * s))), Image.NEAREST)) > 0
    Hh = max(ref.shape[0], model.shape[0]); a = np.zeros((Hh, model.shape[1]), bool); b = a.copy()
    a[Hh - model.shape[0]:] = model; b[Hh - ref.shape[0]:] = ref     # bottom-aligned (table)
    I = (a & b).sum(); U = (a | b).sum()
    rgb = np.full(a.shape + (3,), 255, np.uint8); rgb[b & ~a] = (220, 60, 60); rgb[a & ~b] = (60, 110, 230); rgb[a & b] = (90, 90, 90)
    Image.fromarray(rgb).save(os.path.join(out, f"overlay_{tag}.png"))
    return round(I / U, 4), round(ref.shape[0] / PX, 1), round(model.shape[0] / PX, 1)
res = {}
top, size = sil(1, 0)                 # plan: u = Y (width), v = -X (bumper edge at top of image)
top = top[::-1]                       # image top = bumper edge (-X)
res["top"] = iou(top, "mask_top_trace.png", 153, "top")
back, _ = sil(1, 2, flip_u=True)      # rear elevation, looking along +X from the bumper side
res["back"] = iou(back, "mask_back.png", 153, "back")
res["size_mm"] = [round(float(s), 1) for s in size]
print(json.dumps(res))
json.dump(res, open(os.path.join(out, "iou.json"), "w"))
