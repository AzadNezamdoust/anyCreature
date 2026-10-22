"""t2i_refs.py <outdir> <species> <n> <seed0> - HunyuanDiT reference candidates for ref_critic.py --regen (venv python).
Prompts: E:/gen3d/refs.py A[species] + STY + SUF when present. Model is cached when run inside model_server.py."""
import builtins, os, sys
sys.path.insert(0, 'E:/gen3d'); sys.path.insert(0, r'E:\gen3d\Hunyuan3D-2')
import refs   # prompt tables only (its __main__ block does not run on import)
d, sp, n, s0 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
key = next((k for k in refs.A if k.split(' ')[0] == sp.split(' ')[0]), None)
base = refs.A[key] if key else [f'a {sp}, full body, anatomically correct, all limbs visible']
def build():
    from hy3dgen.text2image import HunyuanDiTPipeline
    return HunyuanDiTPipeline('Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled')
t2i = builtins._cached_impl('t2i_hunyuandit', build) if hasattr(builtins, '_cached_impl') else build()
for k in range(n):
    p = f'{base[k % len(base)]}, {refs.STY[k % len(refs.STY)]}' + refs.SUF
    t2i(p, seed=s0 + k).save(f'{d}/t{s0}_{k}.png'); print('t2i', k, p, flush=True)
