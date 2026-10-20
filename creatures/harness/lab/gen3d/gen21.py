import os, sys, time, torch
sys.path.insert(0, r"E:\gen3d\Hunyuan3D-2.1\hy3dshape")
from PIL import Image
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from hy3dshape.postprocessors import FloaterRemover, DegenerateFaceRemover
ans = sys.argv[1].split(","); seeds = [0, 1]
shp = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1")
for an in ans:
    rgba = Image.open(f"r8/{an}/ref_rgba.png")
    for s in seeds:
        m = shp(image=rgba, num_inference_steps=50, octree_resolution=380, generator=torch.manual_seed(s))[0]
        m = DegenerateFaceRemover()(FloaterRemover()(m))
        m.export(f"r8/{an}/raw21_s{s}.obj"); print(time.strftime('%X'), an, s, len(m.faces), flush=True)
