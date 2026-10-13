# Hunyuan3D-2.1 PBR texture paint runner (venv cu128 torch + CUDA-13.4 pip-built custom_rasterizer)
import os, sys, time, types
os.add_dll_directory(r'E:\gen3d\cuda134\nvidia\cu13\bin\x86_64')   # cudart64_13.dll for custom_rasterizer_kernel
sys.modules.setdefault('bpy', types.ModuleType('bpy'))              # bpy only used by an unused obj-import helper
ROOT = r'E:\gen3d\Hunyuan3D-2.1'
os.chdir(ROOT); sys.path[:0] = [ROOT, os.path.join(ROOT, 'hy3dpaint')]
mesh, ref, out = sys.argv[1], sys.argv[2], sys.argv[3]
views = int(sys.argv[4]) if len(sys.argv) > 4 else 6
res = int(sys.argv[5]) if len(sys.argv) > 5 else 512
try:
    from utils.torchvision_fix import apply_fix; apply_fix()
except Exception as e: print('tv fix:', e)
import torch, huggingface_hub.file_download as _fd
_fd.are_symlinks_supported = lambda *a, **k: False   # Win: no symlink privilege -> copy blobs
from PIL import Image
import utils.image_super_utils as isu
class LanczosSuper:   # RealESRGAN weights are GitHub-release only (non-approved source) -> plain x4 Lanczos
    def __init__(self, config): pass
    def __call__(self, im): return im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
isu.imageSuperNet = LanczosSuper
import textureGenPipeline as tgp
tgp.imageSuperNet = LanczosSuper
conf = tgp.Hunyuan3DPaintConfig(views, res)
t0 = time.time(); torch.cuda.reset_peak_memory_stats()
pipe = tgp.Hunyuan3DPaintPipeline(conf); t1 = time.time()
p = pipe(mesh_path=mesh, image_path=ref, output_mesh_path=out, use_remesh=False)  # input already a clean low-poly mesh; remesh decimation target > face count raises
t2 = time.time()
print(f'OUT {p} load {t1-t0:.1f}s paint {t2-t1:.1f}s peakVRAM {torch.cuda.max_memory_allocated()/2**30:.2f} GiB')
