# round 12 texture runner: python paint12.py <outroot> animal:variant[,animal:variant...]
# variants: key=value tokens joined by '+': ref=orig|delit|new  v=<views>  r=<view res>  dil=0|1
import os, sys, time, runpy, traceback, numpy as np
outroot, jobs = sys.argv[1], sys.argv[2].split(',')
src = open(r'E:\gen3d\paint21.py').read(); head = src.split("conf = tgp")[0]
sys.argv = ['paint21.py', 'x', 'x', 'x']; g = {'__name__': '__main__'}
exec(compile(head, 'paint21_head', 'exec'), g)
tgp, torch = g['tgp'], g['torch']
from PIL import Image, ImageDraw
import cv2, trimesh
ORIG = dict(wolf=r'E:\gen3d\r8\wolf\ref_rgba.png', crocodile=r'E:\gen3d\r8\crocodile\ref_rgba.png',
            eagle=r'E:\gen3d\r8\eagle\ref_rgba.png', frog=r'E:\gen3d\r8\frog\ref_rgba.png')
for a, k in dict(horse=5, elephant=9, giraffe=3, shark=3, tortoise=3, kangaroo=4).items(): ORIG[a] = rf'E:\gen3d\r9\{a}\ref_c{k}.png'
import importlib, utils.image_super_utils as isu; importlib.reload(isu)
tgp.imageSuperNet = isu.imageSuperNet   # real RealESRGAN x4plus
_cfg = tgp.Hunyuan3DPaintConfig(6, 512); _cfg.realesrgan_ckpt_path = r'E:\gen3d\dl_esrgan\RealESRGAN_x4plus.pth'
pipe = tgp.Hunyuan3DPaintPipeline(_cfg)
def dilate(d, px=24):
    m = trimesh.load(os.path.join(d, 'textured.obj'), process=False, force='mesh')
    for fn in ['textured.jpg', 'textured_metallic.jpg', 'textured_roughness.jpg']:
        p = os.path.join(d, fn); im = np.array(Image.open(p).convert('RGB')); H, W = im.shape[:2]
        mk = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(mk)
        uv = m.visual.uv; pts = np.stack([uv[:, 0] * W, (1 - uv[:, 1]) * H], -1)
        for f in m.faces: dr.polygon([tuple(pts[i]) for i in f], fill=255)
        cov = np.array(mk) > 0; img = im.astype(np.float32); cur = cov.copy(); k = np.ones((3, 3), np.float32)
        for _ in range(px):
            s = cv2.filter2D(img * cur[..., None], -1, k, borderType=cv2.BORDER_CONSTANT)
            c = cv2.filter2D(cur.astype(np.float32), -1, k, borderType=cv2.BORDER_CONSTANT)
            new = (~cur) & (c > 0); img[new] = s[new] / c[new][:, None]; cur |= new
        Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(p, quality=95)
for job in jobs:
    a, var = job.split(':'); o = dict(ref='orig', v='6', r='512', dil='0', ds='1')
    for t in var.split('+'):
        if '=' in t: k, v = t.split('='); o[k] = v
    ref = ORIG[a] if o['ref'] == 'orig' else rf'E:\gen3d\tex12\_refs\{a}_{o["ref"]}.png'
    d = os.path.join(outroot, a, var) if outroot.endswith('ab') else os.path.join(outroot, a); os.makedirs(d, exist_ok=True)
    pipe.config.max_selected_view_num = int(o['v']); pipe.config.resolution = int(o['r'])
    _sm = type(pipe.render).save_mesh; pipe.render.save_mesh = (lambda p, downsample=True, _o=o: _sm(pipe.render, p, downsample=_o['ds'] == '1'))
    t = time.time(); torch.cuda.reset_peak_memory_stats()
    try:
        pipe(mesh_path=rf'E:\gen3d\r9pick\{a}.obj', image_path=ref, output_mesh_path=os.path.join(d, 'textured.obj'), use_remesh=False)
        tp = time.time() - t
        if o['dil'] == '1': dilate(d)
        sys.argv = ['g', d]; runpy.run_path(r'E:\gen3d\glb_preview21.py', run_name='__main__')
        print(f'RESULT {a} {var} ok paint {tp:.0f}s total {time.time()-t:.0f}s peak {torch.cuda.max_memory_allocated()/2**30:.1f}GiB ref {ref}', flush=True)
    except Exception:
        traceback.print_exc(); print(f'RESULT {a} {var} FAIL {time.time()-t:.0f}s', flush=True)
