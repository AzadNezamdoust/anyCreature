# shape.py <ref.png> <out.obj> <octree> <num_chunks> <offload 0|1> [steps] [seed]
import sys; sys.path.insert(0, 'E:/gen3d/lowvram'); import cap, time, torch
sys.path.insert(0, r"E:\gen3d\Hunyuan3D-2.1\hy3dshape")
from PIL import Image
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from hy3dshape.postprocessors import FloaterRemover, DegenerateFaceRemover
ref, out, octree, chunks, off = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5] == '1'
steps = int(sys.argv[6]) if len(sys.argv) > 6 else 50; seed = int(sys.argv[7]) if len(sys.argv) > 7 else 0
t = time.time()
shp = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1", device='cpu' if off else 'cuda')
if off:
    from accelerate import cpu_offload_with_hook
    h = None
    for n in ('conditioner', 'model', 'vae'):
        _, h = cpu_offload_with_hook(getattr(shp, n), 'cuda', prev_module_hook=h)
    shp.device = torch.device('cuda')
if len(sys.argv) > 8 and sys.argv[8] == 'vdm': shp.enable_flashvdm(mc_algo='mc')
print('params M', {n: round(sum(p.numel() for p in getattr(shp, n).parameters())/1e6) for n in ('conditioner','model','vae')})
print('load', round(time.time()-t), flush=True); t = time.time()
m = shp(image=Image.open(ref), num_inference_steps=steps, octree_resolution=octree, num_chunks=chunks,
        generator=torch.manual_seed(seed))[0]
print('gen', round(time.time()-t), flush=True); cap.peak('gen')
m = DegenerateFaceRemover()(FloaterRemover()(m)); m.export(out); print('faces', len(m.faces))
