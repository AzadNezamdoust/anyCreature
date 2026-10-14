# paint.py <mesh.obj> <ref.png> <outdir> v=9 r=512 off=0|1 tile=0 tex=4096 dil=1
import sys; sys.path.insert(0, 'E:/gen3d/lowvram'); import cap
import os, time, runpy, traceback, numpy as np
mesh, ref, d = [os.path.abspath(x) for x in sys.argv[1:4]]
o = dict(v='9', r='512', off='0', tile='0', tex='4096', dil='1', ds='0')
for t in sys.argv[4:]: k, v = t.split('='); o[k] = v
src = open(r'E:\gen3d\paint21.py').read(); head = src.split("conf = tgp")[0]
sys.argv = ['paint21.py', 'x', 'x', 'x']; g = {'__name__': '__main__'}
exec(compile(head, 'paint21_head', 'exec'), g)
tgp, torch = g['tgp'], g['torch']
import importlib, utils.image_super_utils as isu; importlib.reload(isu); tgp.imageSuperNet = isu.imageSuperNet
import utils.multiview_utils as mvu
off = o['off'] == '1'
if off:  # keep multiview UNet/VAE/text-enc + DINO on CPU; move to GPU only for the diffusion call
    _init, _call = mvu.multiviewDiffusionNet.__init__, mvu.multiviewDiffusionNet.__call__
    from accelerate import cpu_offload_with_hook
    def init(self, cfg):
        _init(self, cfg); self.pipeline.to('cpu'); self.dino_v2.to('cpu'); torch.cuda.empty_cache()
        if o.get('ffc', '1') != '0':   # feed-forward chunking over the batch dim
            n = 0
            for m in self.pipeline.unet.modules():
                if hasattr(m, 'set_chunk_feed_forward'): m.set_chunk_feed_forward(int(o.get('ffc', '1')), 0); n += 1
            print('ff-chunked blocks', n, flush=True)
        if o.get('vt') == '1': self.pipeline.vae.enable_tiling(); self.pipeline.vae.enable_slicing()
        dino = self.dino_v2
        class DinoOff:   # DINOv2-giant only on GPU for its single forward
            def __call__(s, *a, **k):
                dino.to('cuda')
                try: return dino(*a, **k)
                finally: dino.to('cpu'); torch.cuda.empty_cache()
        self.dino_v2 = DinoOff()
        te = self.pipeline.text_encoder; _f = te.forward
        def te_fwd(*a, **k):   # CLIP text encoder: GPU only for the one prompt encode
            te.to('cuda')
            try:
                a = [x.to('cuda') if torch.is_tensor(x) else x for x in a]
                k = {kk: (v.to('cuda') if torch.is_tensor(v) else v) for kk, v in k.items()}
                return _f(*a, **k)
            finally: te.to('cpu'); torch.cuda.empty_cache()
        te.forward = te_fwd
        type(self.pipeline)._execution_device = property(lambda s: torch.device('cuda'))
    def call(self, *a, **k):
        print('pre-mv alloc GiB', torch.cuda.memory_allocated()/2**30, flush=True)
        self.pipeline.unet.to('cuda'); self.pipeline.vae.to('cuda')   # text encoder stays on CPU (staged below)
        try: return _call(self, *a, **k)
        finally: self.pipeline.to('cpu'); torch.cuda.empty_cache()
    mvu.multiviewDiffusionNet.__init__, mvu.multiviewDiffusionNet.__call__ = init, call
    tgp.multiviewDiffusionNet = mvu.multiviewDiffusionNet
cfg = tgp.Hunyuan3DPaintConfig(int(o['v']), int(o['r'])); cfg.realesrgan_ckpt_path = r'E:\gen3d\dl_esrgan\RealESRGAN_x4plus.pth'
cfg.texture_size = int(o['tex'])
t = time.time(); pipe = tgp.Hunyuan3DPaintPipeline(cfg); print('load', round(time.time() - t), flush=True)
up = pipe.models['super_model'].upsampler; up.tile_size = int(o['tile'])
if off:  # RealESRGAN is small; leave it on GPU
    pass
sm = type(pipe.render).save_mesh; pipe.render.save_mesh = lambda p, downsample=True: sm(pipe.render, p, downsample=o['ds'] == '1')
os.makedirs(d, exist_ok=True); torch.cuda.reset_peak_memory_stats(); t = time.time()
pipe(mesh_path=mesh, image_path=ref, output_mesh_path=os.path.join(d, 'textured.obj'), use_remesh=False)
print('paint', round(time.time() - t), flush=True); cap.peak('paint')
if o['dil'] == '1':
    p13 = open(r'E:\gen3d\tex13\paint13.py').read(); s = p13.index('def dilate'); e = p13.index('for job in jobs')
    from PIL import Image, ImageDraw; import cv2, trimesh
    gg = dict(os=os, np=np, Image=Image, ImageDraw=ImageDraw, cv2=cv2, trimesh=trimesh); exec(p13[s:e], gg); gg['dilate'](d)
sys.argv = ['g', d]; runpy.run_path(r'E:\gen3d\glb_preview21.py', run_name='__main__')
