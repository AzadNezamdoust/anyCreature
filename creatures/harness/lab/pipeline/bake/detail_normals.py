"""Image -> fine normal detail -> LOD UV space.
Marigold normals LCM v0.1 (prs-eth, Apache-2.0 code+weights) on ortho renders of the textured hi mesh; the high-pass of the
estimated camera-space normal is rotated to world, projected onto each LOD texel (baked hi position, depth-tested against the
view's position pass, facing-weighted), added to the baked object-space normal and renormalised (world-space UDN; the LOD is
re-baked to tangent space in Blender afterwards).
usage: detail_normals.py marigold <views_dir> [--vram-cap 7.0]
       detail_normals.py project <views_dir> <lod_dir> [strength]
"""
import os, sys, json, time
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import numpy as np, cv2

def exr(p): return np.load(p[:-4] + '.npy')   # EXR pre-converted by bake_normals_bl.py exr2npy (venv cv2 lacks EXR)

def marigold(vd, cap):
    import torch
    from diffusers import MarigoldNormalsPipeline
    from PIL import Image
    if cap: torch.cuda.set_per_process_memory_fraction(cap * 2**30 / torch.cuda.get_device_properties(0).total_memory)
    t = time.time()
    pipe = MarigoldNormalsPipeline.from_pretrained('prs-eth/marigold-normals-lcm-v0-1', variant='fp16', torch_dtype=torch.float16).to('cuda')
    pipe.set_progress_bar_config(disable=True)
    cams = json.load(open(f'{vd}/cams.json')); stats = []
    for c in cams:
        k = c['k']; im = np.asarray(Image.open(f'{vd}/view_{k}.png').convert('RGBA')).astype(np.float32) / 255
        rgb = im[..., :3] * im[..., 3:] + 0.5 * (1 - im[..., 3:])
        out = pipe(Image.fromarray((rgb * 255).astype(np.uint8)), num_inference_steps=4, ensemble_size=3,
                   processing_resolution=768, match_input_resolution=True, generator=torch.Generator('cuda').manual_seed(0))
        n = np.asarray(out.prediction[0], np.float32)
        # convention check vs true geometry normal (camera space)
        R = np.array(c['mw'])[:3, :3]; g = (exr(f'{vd}/view_{k}_nrm.exr')[..., :3] * 2 - 1) @ R
        m = im[..., 3] > 0.99
        corr = [float(np.corrcoef(n[m][:, i], g[m][:, i])[0, 1]) for i in range(3)]
        np.save(f'{vd}/mari_{k}.npy', n); stats.append(corr)
        cv2.imwrite(f'{vd}/mari_{k}.png', ((n * 0.5 + 0.5)[..., ::-1] * 255).astype(np.uint8))
    peak = torch.cuda.max_memory_allocated() / 2**30; rpeak = torch.cuda.max_memory_reserved() / 2**30
    r = dict(model='prs-eth/marigold-normals-lcm-v0-1', views=len(cams), corr_xyz=np.mean(stats, 0).round(3).tolist(),
             vram_alloc_gib=round(peak, 2), vram_reserved_gib=round(rpeak, 2), cap=cap, sec=round(time.time() - t, 1))
    json.dump(r, open(f'{vd}/marigold.json', 'w'), indent=1); print(r)

def project(vd, ld, strength):
    t = time.time(); cams = json.load(open(f'{vd}/cams.json'))
    P = (exr(f'{ld}/pos.exr')[..., :3] - 0.5) * 4; Nraw = exr(f'{ld}/n_obj.exr')[..., :3]; No = Nraw * 2 - 1
    valid = Nraw.sum(-1) > 0.05; N = No / np.maximum(np.linalg.norm(No, axis=-1, keepdims=True), 1e-6)
    acc = np.zeros_like(P); wsum = np.zeros(P.shape[:2], np.float32)
    for c in cams:
        k = c['k']; M = np.array(c['mw']); R = M[:3, :3]; o = M[:3, 3]; res = c['res']; s = c['ortho']
        n = np.load(f'{vd}/mari_{k}.npy'); a = cv2.imread(f'{vd}/view_{k}.png', cv2.IMREAD_UNCHANGED)[..., 3] > 250
        a = cv2.erode(a.astype(np.uint8), np.ones((5, 5))) > 0
        hp = n - cv2.GaussianBlur(n, (0, 0), 3.0)                    # fine detail only (fur clumps, wrinkles)
        hp[..., 2] = 0; hp *= a[..., None]
        dw = hp @ R.T                                                # camera -> world
        pr = (exr(f'{vd}/view_{k}_pos.exr')[..., :3] - 0.5) * 4
        pc = (P - o) @ R
        u = ((pc[..., 0] / s + 0.5) * res).astype(np.int32); v = ((0.5 - pc[..., 1] / s) * res).astype(np.int32)
        inb = valid & (u >= 0) & (u < res) & (v >= 0) & (v < res)
        uu, vv = np.clip(u, 0, res - 1), np.clip(v, 0, res - 1)
        vis = inb & (np.linalg.norm(pr[vv, uu] - P, axis=-1) < 0.006) & a[vv, uu]
        w = np.clip(N @ R[:, 2], 0, 1) ** 4 * vis
        acc += dw[vv, uu] * w[..., None]; wsum += w
    D = acc / np.maximum(wsum, 1e-4)[..., None]
    D -= (D * N).sum(-1, keepdims=True) * N                          # keep it tangential
    Nc = N + strength * D; Nc /= np.maximum(np.linalg.norm(Nc, axis=-1, keepdims=True), 1e-6)
    Nc[~valid] = N[~valid]
    cov = float((wsum[valid] > 1e-3).mean())
    out = np.concatenate([Nc * 0.5 + 0.5, np.ones_like(Nc[..., :1])], -1).astype(np.float32)
    np.save(f'{ld}/n_obj_detail.npy', out)   # -> EXR via bake_normals_bl.py npy2exr
    r = dict(strength=strength, texel_coverage=round(cov, 3), mean_detail=float(np.linalg.norm(D[valid], axis=-1).mean()), sec=round(time.time() - t, 1))
    json.dump(r, open(f'{ld}/detail.json', 'w'), indent=1); print(r)

if __name__ == '__main__':
    if sys.argv[1] == 'marigold':
        cap = float(sys.argv[sys.argv.index('--vram-cap') + 1]) if '--vram-cap' in sys.argv else 0
        marigold(sys.argv[2], cap)
    else: project(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 1.5)
