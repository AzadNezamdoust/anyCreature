# textured.obj (+ _metallic/_roughness jpg) -> PBR textured.glb via trimesh, and a 4-view albedo preview using custom_rasterizer
import os, sys, numpy as np, trimesh, torch
from PIL import Image
os.add_dll_directory(r'E:\gen3d\cuda134\nvidia\cu13\bin\x86_64')
import custom_rasterizer as cr
d = sys.argv[1]; obj = os.path.join(d, 'textured.obj')
m = trimesh.load(obj, process=False, force='mesh')
alb = Image.open(os.path.join(d, 'textured.jpg')).convert('RGB')
met = np.array(Image.open(os.path.join(d, 'textured_metallic.jpg')).convert('L').resize(alb.size))
rou = np.array(Image.open(os.path.join(d, 'textured_roughness.jpg')).convert('L').resize(alb.size))
mr = np.stack([np.zeros_like(met), rou, met], -1)        # glTF: G=roughness, B=metallic
mat = trimesh.visual.material.PBRMaterial(baseColorTexture=alb, metallicRoughnessTexture=Image.fromarray(mr),
                                           metallicFactor=1.0, roughnessFactor=1.0)
uv = m.visual.uv
m.visual = trimesh.visual.TextureVisuals(uv=uv, material=mat)
m.export(os.path.join(d, 'textured.glb'))
print('glb', os.path.getsize(os.path.join(d, 'textured.glb')), 'V', len(m.vertices), 'F', len(m.faces))
# preview
v = torch.tensor(m.vertices, dtype=torch.float32, device='cuda'); v = (v - v.mean(0)) / (v - v.mean(0)).abs().max()
f = torch.tensor(m.faces, dtype=torch.int32, device='cuda'); uvt = torch.tensor(uv, dtype=torch.float32, device='cuda')
tex = torch.tensor(np.array(alb), dtype=torch.float32, device='cuda') / 255; H, W = tex.shape[:2]
R = 768; tiles = []
for az in [0, 90, 180, 270]:
    a = np.radians(az); rot = torch.tensor([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]], dtype=torch.float32, device='cuda')
    p = v @ rot.T * 0.9; clip = torch.cat([p[:, :1], p[:, 1:2], p[:, 2:3] * 0.5 + 0.5, torch.ones_like(p[:, :1])], 1)
    fi, bary = cr.rasterize(clip[None], f, (R, R))
    img = torch.ones(R, R, 3, device='cuda'); mask = fi > 0
    tri = f[(fi[mask] - 1).long()].long(); b = bary[mask]
    t = (uvt[tri] * b[..., None]).sum(1)
    px = (t[:, 0] * (W - 1)).clamp(0, W - 1).long(); py = ((1 - t[:, 1]) * (H - 1)).clamp(0, H - 1).long()
    img[mask] = tex[py, px]; tiles.append(img.flip(0).cpu().numpy())
Image.fromarray((np.concatenate(tiles, 1) * 255).astype(np.uint8)).save(os.path.join(d, 'preview.png'))
print('preview ok')
