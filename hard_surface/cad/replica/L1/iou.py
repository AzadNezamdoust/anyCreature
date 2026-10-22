"""Silhouette IoU: model ortho projections vs reference (bolt: ISO 4017 drawing side/end view; case: spec envelope).
python iou.py <model_hq.glb> <out_dir>"""
import json, sys, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageOps, ImageChops
REF = r"E:\Github\anyCreature\hard_surface\cad\refs\L1\iso4017_drawing.jpg"
glb, out = sys.argv[1], sys.argv[2]
sc = trimesh.load(glb, force="scene")
def part(name):
    ms = [g.copy().apply_transform(sc.graph.get(n)[0]) for n in sc.graph.nodes_geometry
          for g in [sc.geometry[sc.graph.get(n)[1]]] if name in n or name in sc.graph.get(n)[1]]
    m = trimesh.util.concatenate(ms); v = m.vertices.copy(); m.vertices = np.c_[v[:, 0], -v[:, 2], v[:, 1]]  # glTF Y-up -> CAD Z-up
    return m
def sil(m, ax, px, box):  # ax: (u,v) column idx; box (u0,u1,v0,v1) metres
    V = m.vertices * 1000; u0, u1, v0, v1 = box; W = int((u1 - u0) * px); H = int((v1 - v0) * px)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    P = np.c_[(V[:, ax[0]] - u0) * px, (v1 - V[:, ax[1]]) * px]
    for t in m.faces: d.polygon([tuple(P[i]) for i in t], fill=255)
    return im
def iou(a, b):
    A, B = np.array(a) > 127, np.array(b) > 127; return float((A & B).sum() / max(1, (A | B).sum()))
res = {}
# ---- bolt side view: drawing k+l spans x 30..390 px (=45.3 mm), axis y=167
ref = ImageOps.grayscale(Image.open(REF)).crop((20, 90, 400, 245))
bw = ref.point(lambda v: 0 if v < 160 else 255)
fill = bw.copy()
for sd in [(x, y) for x in range(0, 380, 6) for y in (0, 154)] + [(0, y) for y in range(0, 155, 6)] + [(379, y) for y in range(0, 155, 6)]:
    if fill.getpixel(sd) == 255: ImageDraw.floodfill(fill, sd, 128)
refsil = fill.point(lambda v: 0 if v == 128 else 255)
px_ref = (390 - 30) / 45.3
b = part("bolt"); V = b.vertices * 1000; c = (V.min(0) + V.max(0)) / 2
xlo = V[:, 0].min()
box = (xlo - 10 / px_ref, xlo - 10 / px_ref + 380 / px_ref, c[2] - 77 / px_ref, c[2] + 78 / px_ref)  # drawing head at left
m = b.copy(); m.vertices[:, 0] = 2 * c[0] - m.vertices[:, 0] if False else m.vertices[:, 0]
ms = sil(b, (0, 2), px_ref, box).resize(refsil.size)
# model head is at +X; mirror to drawing (head left)
ms = ImageOps.mirror(sil(b, (0, 2), px_ref, (V[:, 0].max() - 370 / px_ref, V[:, 0].max() + 10 / px_ref, box[2], box[3])))
ms = ms.resize(refsil.size)
res["bolt_side"] = iou(ms, refsil)
Image.merge("RGB", (refsil, ms, ImageChops.multiply(refsil, ms))).save(out + "/overlay_bolt_side.png")
# ---- bolt end view (hex): drawing hex centre (652,167), s = 597..709 px
ref2 = ImageOps.grayscale(Image.open(REF)).crop((582, 92, 722, 242)).point(lambda v: 0 if v < 160 else 255)
f2 = ref2.copy()
for sd in [(x, y) for x in range(0, 140, 4) for y in (0, 149)] + [(x, y) for y in range(0, 150, 4) for x in (0, 139)]:
    if f2.getpixel(sd) == 255: ImageDraw.floodfill(f2, sd, 128); refhex = f2.point(lambda v: 0 if v == 128 else 255)
p2 = (709 - 597) / 13.0
hb = (c[1] - 70 / p2, c[1] + 70 / p2, c[2] - 75 / p2, c[2] + 75 / p2)
mh = sil(b, (1, 2), p2, hb).resize(refhex.size)
res["bolt_end"] = iou(mh, refhex)
Image.merge("RGB", (refhex, mh, ImageChops.multiply(refhex, mh))).save(out + "/overlay_bolt_end.png")
# ---- case vs spec envelope (97x70 plan r6, 97x25 side, 70x25 end) [R1] — no true ortho ref available
cs = trimesh.util.concatenate([part("case_lid"), part("case_base")]); C = cs.vertices * 1000
def env(w, h, r, px=8):
    im = Image.new("L", (int(w * px) + 40, int(h * px) + 40), 0)
    ImageDraw.Draw(im).rounded_rectangle((20, 20, 20 + w * px, 20 + h * px), r * px, fill=255); return im
for nm, ax, (w, h, r) in [("case_top", (0, 1), (97, 70, 6)), ("case_side", (0, 2), (97, 25, 1.5)), ("case_end", (1, 2), (70, 25, 1.5))]:
    lo, hi = C[:, list(ax)].min(0), C[:, list(ax)].max(0); cx = (lo + hi) / 2
    bx = (cx[0] - w / 2 - 2.5, cx[0] + w / 2 + 2.5, cx[1] - h / 2 - 2.5, cx[1] + h / 2 + 2.5)
    e = env(w, h, r); res[nm] = iou(sil(cs, ax, 8, bx).resize(e.size), e)
    res[nm + "_dims_mm"] = [round(float(x), 2) for x in (hi - lo)]
print(json.dumps(res)); json.dump(res, open(out + "/iou.json", "w"), indent=1)
