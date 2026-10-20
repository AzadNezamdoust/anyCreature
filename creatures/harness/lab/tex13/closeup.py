# closeup.py <glb> <out.png> <tile 0-3> <x0> <y0> <x1> <y1>   (box in 768px preview-tile coords); renders that crop at 4x
import os, sys, numpy as np, trimesh, torch
from PIL import Image
os.add_dll_directory(r'E:\gen3d\cuda134\nvidia\cu13\bin\x86_64')
import custom_rasterizer as cr
glb, out, tile, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), *map(float, sys.argv[4:8])
sc = trimesh.load(glb, process=False); m = list(sc.geometry.values())[0]
uv = m.visual.uv; alb = m.visual.material.baseColorTexture.convert('RGB')
v = torch.tensor(m.vertices, dtype=torch.float32, device='cuda'); v = (v - v.mean(0)) / (v - v.mean(0)).abs().max()
f = torch.tensor(m.faces, dtype=torch.int32, device='cuda'); uvt = torch.tensor(uv, dtype=torch.float32, device='cuda')
tex = torch.tensor(np.array(alb), dtype=torch.float32, device='cuda') / 255; H, W = tex.shape[:2]
Z = 4; R = 768 * Z; a = np.radians(tile * 90)
rot = torch.tensor([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]], dtype=torch.float32, device='cuda')
p = v @ rot.T * 0.9; clip = torch.cat([p[:, :2], p[:, 2:3] * 0.5 + 0.5, torch.ones_like(p[:, :1])], 1)
fi, bary = cr.rasterize(clip[None], f, (R, R))
img = torch.ones(R, R, 3, device='cuda'); mask = fi > 0
tri = f[(fi[mask] - 1).long()].long(); t = (uvt[tri] * bary[mask][..., None]).sum(1)
# bilinear sample
tx = (t[:, 0] * (W - 1)).clamp(0, W - 1); ty = ((1 - t[:, 1]) * (H - 1)).clamp(0, H - 1)
ix, iy = tx.floor().long().clamp(0, W - 2), ty.floor().long().clamp(0, H - 2); fx, fy = (tx - ix)[:, None], (ty - iy)[:, None]
c = tex[iy, ix] * (1 - fx) * (1 - fy) + tex[iy, ix + 1] * fx * (1 - fy) + tex[iy + 1, ix] * (1 - fx) * fy + tex[iy + 1, ix + 1] * fx * fy
img[mask] = c
im = (img.flip(0).cpu().numpy() * 255).astype(np.uint8)
Image.fromarray(im[int(y0 * Z):int(y1 * Z), int(x0 * Z):int(x1 * Z)]).save(out)
