"""Side-view silhouette IoU: model mesh (out/.../mesh or hq glb) projected on XZ vs ref mask, registered by S."""
import sys, numpy as np, trimesh
from PIL import Image, ImageDraw
glb, mask_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
S = 191.0 / (1521 - 144)
ref = np.array(Image.open(mask_p)) > 128
H, W = ref.shape
sc = trimesh.load(glb, force="scene")
m = sc.to_geometry() if hasattr(sc, "to_geometry") else sc.dump(concatenate=True)
v = m.vertices.copy()
# glTF is Y-up: cadkit Z-up model -> glb (x, z, -y). detect: use axis with largest extent as height candidate
P = np.c_[v[:, 0], v[:, 1]] if np.ptp(v[:, 1]) > np.ptp(v[:, 2]) else np.c_[v[:, 0], v[:, 2]]
P = P * (1000.0 if np.ptp(P[:, 0]) < 5 else 1.0)  # m -> mm
px = P[:, 0] / S + 1521; py = 259 - P[:, 1] / S
img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
for f in m.faces:
    d.polygon([(px[i], py[i]) for i in f], fill=255)
mod = np.array(img) > 128
iou = (ref & mod).sum() / (ref | mod).sum()
ov = np.full((H, W, 3), 255, np.uint8); ov[ref] = (120, 170, 255); ov[mod] = (255, 200, 60); ov[ref & mod] = (90, 90, 90)
Image.fromarray(ov).resize((840, 840)).save(out)
ys, xs = np.nonzero(mod)
print(f"IoU_side={iou:.4f} model_L={(xs.max()-xs.min())*S:.1f}mm H={(ys.max()-ys.min())*S:.1f}mm  ref_only={(ref&~mod).sum()*S*S/100:.1f}cm2 model_only={(mod&~ref).sum()*S*S/100:.1f}cm2")
