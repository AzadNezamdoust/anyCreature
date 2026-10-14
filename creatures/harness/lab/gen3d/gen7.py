import os, sys, torch, trimesh
from PIL import Image
from make import remove_white_bg, log
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FloaterRemover, DegenerateFaceRemover
picks = dict(a.split(":") for a in sys.argv[1].split(","))
seeds = [0, 1]
shp = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2", subfolder="hunyuan3d-dit-v2-0")
for an, k in picks.items():
    d = f"r7/{an}"; rgba = remove_white_bg(Image.open(f"{d}/c{k}.png")); rgba.save(f"{d}/ref_rgba.png")
    for s in seeds:
        m = shp(image=rgba, num_inference_steps=60, octree_resolution=512, generator=torch.manual_seed(s))[0]
        m = DegenerateFaceRemover()(FloaterRemover()(m))
        m.export(f"{d}/raw_s{s}.obj"); log(an, s, len(m.faces))
