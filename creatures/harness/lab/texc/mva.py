# Method A: MV-Adapter ig2mv (Apache-2.0) on SDXL base 1.0 (OpenRAIL++-M) + sdxl-vae-fp16-fix (MIT).
# Geometry control maps rendered + views baked with our own moderngl rasterizer (common.py) -> no nvdiffrast/cvcuda.
# usage: python mva.py [--cap] [--lowvram] [--tag NAME] animal [animal ...]
import os, sys, time, json
os.environ.setdefault('HF_HOME', r'E:\gen3d\hf'); os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, r'E:\gen3d\texc'); sys.path.insert(0, r'E:\gen3d\texc\src\MV-Adapter')
import torch, numpy as np, cv2
from PIL import Image
from common import *
MD = 'E:/gen3d/texc/models/'
args = [a for a in sys.argv[1:] if not a.startswith('--')]; flags = [a for a in sys.argv[1:] if a.startswith('--')]
tag = 'mvadapter'
for fl in flags:
    if fl.startswith('--tag='): tag = fl[6:]
if '--cap' in flags: torch.cuda.set_per_process_memory_fraction(7.5 / 95.6)
from diffusers import AutoencoderKL
from mvadapter.models.attention_processor import DecoupledMVRowColSelfAttnProcessor2_0
from mvadapter.pipelines.pipeline_mvadapter_i2mv_sdxl import MVAdapterI2MVSDXLPipeline
from mvadapter.schedulers.scheduling_shift_snr import ShiftSNRScheduler
from huggingface_hub import hf_hub_download
t0 = time.time()
pipe = MVAdapterI2MVSDXLPipeline.from_pretrained(MD+'stabilityai--stable-diffusion-xl-base-1.0', variant='fp16', torch_dtype=torch.float16,
        vae=AutoencoderKL.from_pretrained(MD+'madebyollin--sdxl-vae-fp16-fix', torch_dtype=torch.float16))
pipe.scheduler = ShiftSNRScheduler.from_scheduler(pipe.scheduler, shift_mode='interpolated', shift_scale=8.0)
pipe.init_custom_adapter(num_views=6, self_attn_processor=DecoupledMVRowColSelfAttnProcessor2_0)
pipe.load_custom_adapter(MD+'huanngzh--mv-adapter',
                         weight_name='mvadapter_ig2mv_sdxl.safetensors')
pipe.cond_encoder.to(dtype=torch.float16)
PROMPT = lambda a: f'a {a}, realistic animal, high quality, detailed natural texture'
NEG = 'watermark, ugly, deformed, noisy, blurry, low contrast'
EMB = {}
if '--lowvram' in flags:   # text encoders run once on GPU then go back to CPU; unet/vae/adapter stay on GPU
    pipe.to(torch.float16)
    pipe.text_encoder.to('cuda'); pipe.text_encoder_2.to('cuda')
    with torch.no_grad():
        for a in args:
            e = pipe.encode_prompt(prompt=PROMPT(a), device='cuda', num_images_per_prompt=1, do_classifier_free_guidance=True, negative_prompt=NEG)
            EMB[a] = dict(prompt_embeds=e[0], negative_prompt_embeds=e[1], pooled_prompt_embeds=e[2], negative_pooled_prompt_embeds=e[3])
    pipe.text_encoder.to('cpu'); pipe.text_encoder_2.to('cpu'); torch.cuda.empty_cache()
    pipe.unet.enable_layerwise_casting(storage_dtype=torch.float8_e4m3fn, compute_dtype=torch.float16)
    pipe.unet.to('cuda'); pipe.vae.to('cuda'); pipe.cond_encoder.to('cuda')
    type(pipe)._execution_device = property(lambda self: torch.device('cuda'))
    pipe.enable_vae_tiling(); pipe.vae.tile_sample_min_size = 384; pipe.vae.tile_latent_min_size = 48
else:
    pipe.to('cuda', torch.float16); pipe.cond_encoder.to('cuda', torch.float16)
pipe.enable_vae_slicing()
load_t = time.time() - t0
RES = 768
ELEV = [0, 0, 0, 0, 89.99, -89.99]; AZ = [x - 90 for x in [0, 90, 180, 270, 180, 180]]

def prep_ref(p):
    im = np.array(Image.open(p).convert('RGBA')); al = im[..., 3] > 0; y, x = np.where(al)
    c = im[y.min():y.max() + 1, x.min():x.max() + 1]; H, W = c.shape[:2]; s = RES * 0.9 / max(H, W)
    c = np.array(Image.fromarray(c).resize((int(W * s), int(H * s)), Image.LANCZOS)); H, W = c.shape[:2]
    o = np.zeros((RES, RES, 4), np.uint8); o[(RES - H) // 2:(RES - H) // 2 + H, (RES - W) // 2:(RES - W) // 2 + W] = c
    o = o.astype(np.float32) / 255; return Image.fromarray(((o[..., :3] * o[..., 3:] + (1 - o[..., 3:]) * 0.5) * 255).astype(np.uint8))

log = []
for a in args:
    d = os.path.join(ROOT, tag, a); os.makedirs(d, exist_ok=True)
    torch.cuda.reset_peak_memory_stats(); t = time.time()
    v, f, uv = load_uv_mesh(a); n = vnormals(v, f); vs, ns = to_std(v, n)
    cams = ortho_cams(ELEV, AZ)
    pos, nrm, msk = [], [], []
    for M, _ in cams:
        pimg, _ = raster(vs, f, vs, M=M, res=RES); nimg, _ = raster(vs, f, ns, M=M, res=RES)
        m = pimg[..., 3] > 0
        pos.append(np.where(m[..., None], (pimg[..., :3] + 0.5).clip(0, 1), 0))
        nn = nimg[..., :3] / (np.linalg.norm(nimg[..., :3], axis=-1, keepdims=True) + 1e-9)
        nrm.append(np.where(m[..., None], nn / 2 + 0.5, 0.5)); msk.append(m)  # normal_background=0 -> 0.5 encoded
    ctrl = torch.tensor(np.concatenate([np.stack(pos), np.stack(nrm)], -1), dtype=torch.float32).permute(0, 3, 1, 2).cuda()
    ref = prep_ref(ORIG[a]); ref.save(os.path.join(d, 'ref_in.png'))
    tg = time.time()
    pk = dict(EMB[a]) if a in EMB else dict(prompt=PROMPT(a), negative_prompt=NEG)
    imgs = pipe(**pk, height=RES, width=RES, num_inference_steps=50,
                guidance_scale=3.0, num_images_per_prompt=6, control_image=ctrl, control_conditioning_scale=1.0,
                reference_image=ref, reference_conditioning_scale=1.0,
                generator=torch.Generator('cuda').manual_seed(0)).images
    tgen = time.time() - tg
    Image.fromarray(np.concatenate([np.array(i) for i in imgs], 1)).save(os.path.join(d, 'views.png'))
    views = [np.array(i).astype(np.float32) / 255 for i in imgs]
    er = [cv2.erode(m.astype(np.uint8), np.ones((5, 5), np.uint8)) for m in msk]
    tex, have, cov = bake(vs, ns, f, uv, views, cams, tex=2048, masks=er)
    t8 = fill_uv(tex, have, cov); export(d, v, f, uv, t8); preview(d, v, f, uv, t8)
    r = dict(animal=a, total_s=round(time.time() - t, 1), gen_s=round(tgen, 1), load_s=round(load_t, 1),
             peak_alloc_gib=round(torch.cuda.max_memory_allocated() / 2**30, 2), peak_reserved_gib=round(torch.cuda.max_memory_reserved() / 2**30, 2),
             coverage=round(float(have.sum() / cov.sum()), 3), flags=flags)
    print('RESULT', json.dumps(r), flush=True); log.append(r)
json.dump(log, open(os.path.join(ROOT, tag, 'timing.json'), 'w'), indent=1)
