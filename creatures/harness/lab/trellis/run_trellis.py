"""TRELLIS v1 (microsoft/TRELLIS-image-large) runner for Windows/sm_120.
Patches (runtime only, repo untouched): xformers.ops shim -> torch SDPA; rembg/open3d stubs (inputs have alpha).
usage: python run_trellis.py  (does the 10 critic-picked refs, seeds 0,1)"""
import os, sys, types, time, json
os.environ['ATTN_BACKEND'] = 'xformers'; os.environ['SPARSE_ATTN_BACKEND'] = 'xformers'
os.environ['SPCONV_ALGO'] = 'native'; os.environ.setdefault('HF_HOME', 'E:/gen3d/hf')
import torch, torch.nn.functional as F, numpy as np

# ---- xformers.ops shim on torch SDPA (xformers 0.0.35 win wheel has no sm_120 kernels)
class _BDM:
    def __init__(s, q, kv): s.q, s.kv = list(q), list(kv)
    @staticmethod
    def from_seqlens(q, kv=None): return _BDM(q, kv if kv is not None else q)
def _sdpa(q, k, v):  # [B,N,H,C]
    return F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)).transpose(1, 2)
def memory_efficient_attention(q, k, v, attn_bias=None):
    if attn_bias is None: return _sdpa(q, k, v)
    outs, qi, ki = [], 0, 0
    for lq, lk in zip(attn_bias.q, attn_bias.kv):
        outs.append(_sdpa(q[:, qi:qi+lq], k[:, ki:ki+lk], v[:, ki:ki+lk])); qi += lq; ki += lk
    return torch.cat(outs, 1)
xo = types.ModuleType('xformers.ops'); xo.memory_efficient_attention = memory_efficient_attention
xo.fmha = types.SimpleNamespace(BlockDiagonalMask=_BDM)
xf = types.ModuleType('xformers'); xf.ops = xo
sys.modules['xformers'] = xf; sys.modules['xformers.ops'] = xo
for m in ('rembg', 'open3d'): sys.modules[m] = types.ModuleType(m)
for m in ('kaolin', 'kaolin.utils', 'kaolin.utils.testing'): sys.modules[m] = types.ModuleType(m)
sys.modules['kaolin.utils.testing'].check_tensor = lambda *a, **k: True  # flexicubes only uses it for asserts
sys.modules['open3d'].geometry = types.SimpleNamespace(TriangleMesh=object)

sys.path.insert(0, 'E:/gen3d/TRELLIS')
from PIL import Image
import trimesh
from trellis.pipelines import TrellisImageTo3DPipeline

JOBS = [('wolf', 'r8/wolf/ref_rgba.png'), ('crocodile', 'r8/crocodile/ref_rgba.png'), ('eagle', 'r8/eagle/ref_rgba.png'),
        ('frog', 'r8/frog/ref_rgba.png'), ('horse', 'r9/horse/ref_c5.png'), ('elephant', 'r9/elephant/ref_c9.png'),
        ('giraffe', 'r9/giraffe/ref_c3.png'), ('shark', 'r9/shark/ref_c3.png'), ('tortoise', 'r9/tortoise/ref_c3.png'),
        ('kangaroo', 'r9/kangaroo/ref_c4.png')]
only = sys.argv[1:]
t0 = time.time()
pipe = TrellisImageTo3DPipeline.from_pretrained('microsoft/TRELLIS-image-large'); pipe.cuda()
print('load s', round(time.time() - t0, 1), flush=True)
log = {}
for name, ref in JOBS:
    if only and name not in only: continue
    od = f'E:/gen3d/trellis/{name}'; os.makedirs(od, exist_ok=True)
    img = Image.open(f'E:/gen3d/{ref}')
    for seed in (0, 1):
        torch.cuda.reset_peak_memory_stats(); t = time.time()
        out = pipe.run(img, seed=seed, formats=['mesh'])
        m = out['mesh'][0]
        v = m.vertices.detach().cpu().numpy(); f = m.faces.detach().cpu().numpy()
        v = np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)  # z-up -> y-up
        col = None
        if m.vertex_attrs is not None:
            col = (m.vertex_attrs[:, :3].detach().clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
        tm = trimesh.Trimesh(v, f, vertex_colors=col, process=False)
        tm.export(f'{od}/raw_s{seed}.obj'); tm.export(f'{od}/raw_s{seed}.glb')
        dt = time.time() - t; pk = torch.cuda.max_memory_allocated() / 2**30
        log[f'{name}_s{seed}'] = dict(sec=round(dt, 1), peak_gib=round(pk, 2), V=len(v), F=len(f))
        print(name, seed, log[f'{name}_s{seed}'], flush=True)
        del out, m; torch.cuda.empty_cache()
json.dump(log, open('E:/gen3d/trellis/gen_log.json' if not only else f'E:/gen3d/trellis/gen_log_{"_".join(only)}.json', 'w'), indent=1)


