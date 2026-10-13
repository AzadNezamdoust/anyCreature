import os, sys, time
os.environ.setdefault("HF_HOME", r"E:\gen3d\hf")
sys.path.insert(0, r"E:\gen3d\Hunyuan3D-2")
import torch
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FloaterRemover, DegenerateFaceRemover
p = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2mv', subfolder='hunyuan3d-dit-v2-mv', variant='fp16')
D = "E:/gen3d/mv"
for job in sys.argv[1:]:          # animal:variant  variant a: left=side,right=mirror ; b: swapped ; +f adds front
    an, v = job.split(":")
    L = lambda n: Image.open(f"{D}/{an}/{n}.png").convert("RGBA")
    ims = {"left": L("side"), "right": L("side_mirror")} if v[0] == "a" else {"left": L("side_mirror"), "right": L("side")}
    if "f" in v: ims["front"] = L("front")
    for s in (0, 1):
        m = p(image=ims, num_inference_steps=50, octree_resolution=380, num_chunks=20000,
              generator=torch.manual_seed(s), output_type='trimesh')[0]
        m = DegenerateFaceRemover()(FloaterRemover()(m))
        m.export(f"{D}/{an}/raw_{v}_s{s}.obj"); print(time.strftime('%X'), an, v, s, len(m.faces), flush=True)
