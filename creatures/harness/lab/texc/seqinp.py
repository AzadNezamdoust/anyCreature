# Method B: Text2Tex/TEXTure-style sequential depth-ControlNet inpainting with SDXL.
# Weights: SDXL base 1.0 (OpenRAIL++-M), sdxl-vae-fp16-fix (MIT), diffusers/controlnet-depth-sdxl-1.0 (OpenRAIL++-M),
# h94/IP-Adapter SDXL vit-h + image encoder (Apache-2.0). Rasterizer/bake: own moderngl code (common.py). No nvdiffrast.
# usage: python seqinp.py [--cap] [--lowvram] [--tag=NAME] animal [...]
import os, sys, time, json
os.environ.setdefault('HF_HOME', r'E:\gen3d\hf'); os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, r'E:\gen3d\texc')
import torch, numpy as np, cv2
from PIL import Image
from common import *
from common import _raster_uv_attr
MD = 'E:/gen3d/texc/models/'
args = [a for a in sys.argv[1:] if not a.startswith('--')]; flags = [a for a in sys.argv[1:] if a.startswith('--')]
tag = 'seqinpaint'
for fl in flags:
    if fl.startswith('--tag='): tag = fl[6:]
if '--cap' in flags: torch.cuda.set_per_process_memory_fraction(7.5 / 95.6)
from diffusers import StableDiffusionXLControlNetInpaintPipeline, ControlNetModel, AutoencoderKL
from transformers import CLIPVisionModelWithProjection
t0 = time.time(); dt = torch.float16
pipe = StableDiffusionXLControlNetInpaintPipeline.from_pretrained(MD+'stabilityai--stable-diffusion-xl-base-1.0', variant='fp16', torch_dtype=dt,
    controlnet=ControlNetModel.from_pretrained(MD+'diffusers--controlnet-depth-sdxl-1.0', variant='fp16', torch_dtype=dt),
    vae=AutoencoderKL.from_pretrained(MD+'madebyollin--sdxl-vae-fp16-fix', torch_dtype=dt),
    image_encoder=CLIPVisionModelWithProjection.from_pretrained(MD+'h94--IP-Adapter', subfolder='models/image_encoder', torch_dtype=dt))
pipe.load_ip_adapter(MD+'h94--IP-Adapter', subfolder='sdxl_models', weight_name='ip-adapter_sdxl_vit-h.safetensors')
pipe.set_ip_adapter_scale(0.6)
if '--lowvram' in flags:
    for mdl in (pipe.unet, pipe.controlnet): mdl.enable_layerwise_casting(storage_dtype=torch.float8_e4m3fn, compute_dtype=dt, skip_modules_pattern=("pos_embed", "patch_embed", "norm", "^proj_in$", "^proj_out$", "encoder_hid_proj"))
    pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
else: pipe.to('cuda')
pipe.set_progress_bar_config(disable=True)
load_t = time.time() - t0
RES = 1024; TEX = 2048
# (elev, az offset from the side view that shows the head on the right, view word)
SEQ = [(0, 0, 'side view'), (0, 180, 'side view'), (0, 90, 'front view'), (0, 270, 'back view'),
       (0, 45, 'three-quarter front view'), (0, 135, 'three-quarter front view'), (0, 225, 'three-quarter back view'), (0, 315, 'three-quarter back view'),
       (55, 0, 'view from above'), (55, 180, 'view from above'), (-55, 0, 'view from below'), (-55, 180, 'view from below')]

def ref_img(p):
    im = np.array(Image.open(p).convert('RGBA')).astype(np.float32) / 255
    return Image.fromarray(((im[..., :3] * im[..., 3:] + (1 - im[..., 3:])) * 255).astype(np.uint8))

log = []
for a in args:
    d = os.path.join(ROOT, tag, a); os.makedirs(d, exist_ok=True)
    torch.cuda.reset_peak_memory_stats(); t = time.time()
    v, f, uv = load_uv_mesh(a); n = vnormals(v, f); vs, ns = to_std(v, n)
    uv3 = np.c_[uv, np.zeros(len(uv))].astype(np.float32)
    pos_uv, _ = _raster_uv_attr(vs, f, uv, vs, TEX); nrm_uv, _ = _raster_uv_attr(vs, f, uv, ns, TEX)
    cov = pos_uv[..., 3] > 0; P = pos_uv[cov][:, :3]; N = nrm_uv[cov][:, :3]; N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    col = np.zeros((len(P), 3), np.float32); best = np.zeros(len(P), np.float32)   # best cos so far (0 = unseen)
    ref = ref_img(ORIG[a]); sheet = []; tgen = 0
    for k, (el, az, word) in enumerate(SEQ):
        (M, cp), = ortho_cams([el], [az - 90])
        uvimg, dep = raster(vs, f, uv3, M=M, res=RES); m = uvimg[..., 3] > 0
        # current texture rendered into this view
        T = np.zeros((TEX, TEX, 3), np.float32); B = np.zeros((TEX, TEX), np.float32); T[cov] = col; B[cov] = best
        uvx = uvimg[..., 0][m] * TEX - 0.5; uvy = uvimg[..., 1][m] * TEX - 0.5
        cur = np.full((RES, RES, 3), 0.5, np.float32); cur[m] = bilerp(T, uvx, uvy)
        bv = np.zeros((RES, RES), np.float32); bv[m] = bilerp(B[..., None], uvx, uvy)[:, 0]
        nimg, _ = raster(vs, f, ns, M=M, res=RES); nn = nimg[..., :3] / (np.linalg.norm(nimg[..., :3], axis=-1, keepdims=True) + 1e-9)
        cosv = (nn @ (cp / np.linalg.norm(cp))).clip(0, 1)
        # regenerate where unseen, or where previously seen much more obliquely than now
        known = m & (bv > 0.05) & (bv > cosv - 0.35)
        ink = (m & ~known).astype(np.uint8); ink = cv2.dilate(ink, np.ones((9, 9), np.uint8))
        if ink.sum() < 200: continue
        dd = dep[m]; dn = np.zeros((RES, RES), np.float32); dn[m] = 1 - (dd - dd.min()) / (dd.max() - dd.min() + 1e-6) * 0.8
        ctrl = Image.fromarray((np.repeat(dn[..., None], 3, -1) * 255).astype(np.uint8))
        init = cur.copy(); init[~m] = 1.0
        # fill unknown pixels of init with a blurred version of known colours so the noise prior is plausible
        if known.any() and k > 0:
            tmp = cv2.inpaint((init * 255).astype(np.uint8), ((m & ~known) * 255).astype(np.uint8), 3, cv2.INPAINT_TELEA); init = tmp.astype(np.float32) / 255
        tg = time.time()
        out = pipe(prompt=f'{word} of a {a}, realistic animal, photographic, detailed natural texture, plain white background, even studio lighting',
                   negative_prompt='shadows, harsh lighting, text, watermark, blurry, deformed, low quality, cartoon',
                   image=Image.fromarray((init * 255).astype(np.uint8)), mask_image=Image.fromarray(ink * 255), control_image=ctrl,
                   ip_adapter_image=ref, strength=1.0 if k == 0 else 0.99, num_inference_steps=30, guidance_scale=6.0,
                   controlnet_conditioning_scale=0.8, height=RES, width=RES,
                   generator=torch.Generator('cuda').manual_seed(k)).images[0]
        tgen += time.time() - tg
        g = np.array(out).astype(np.float32) / 255; sheet.append(cv2.resize((g * 255).astype(np.uint8), (384, 384)))
        # bake: update texels visible here whose cos beats stored best (and inside regenerated region or unseen)
        clip = np.c_[P, np.ones(len(P))] @ M.T; ndc = clip[:, :3] / clip[:, 3:]
        px = (ndc[:, 0] + 1) / 2 * RES - 0.5; py = (ndc[:, 1] + 1) / 2 * RES - 0.5
        ix = np.clip(np.round(px).astype(int), 0, RES - 1); iy = np.clip(np.round(py).astype(int), 0, RES - 1)
        vis = (ndc[:, 2] * 0.5 + 0.5 <= dep[iy, ix] + 2e-3) & (cv2.erode(m.astype(np.uint8), np.ones((5, 5), np.uint8))[iy, ix] > 0)
        c = (N @ (cp / np.linalg.norm(cp))).clip(0, 1)
        upd = vis & (ink[iy, ix] > 0) & (c > best) & (c > 0.1)
        # soft blend at mask border: texels already known get 50/50
        newc = bilerp(g, px, py); w = np.where(best > 0.05, 0.5, 1.0)[:, None]
        col[upd] = (newc * w + col * (1 - w))[upd]; best[upd] = c[upd]
    Image.fromarray(np.concatenate(sheet, 1)).save(os.path.join(d, 'views.png'))
    tex = np.zeros((TEX, TEX, 3), np.float32); have = np.zeros((TEX, TEX), bool); tex[cov] = col; hv = np.zeros(len(P), bool); hv[best > 0] = True; have[cov] = hv
    t8 = fill_uv(tex, have, cov); export(d, v, f, uv, t8); preview(d, v, f, uv, t8)
    r = dict(animal=a, total_s=round(time.time() - t, 1), gen_s=round(tgen, 1), load_s=round(load_t, 1),
             peak_alloc_gib=round(torch.cuda.max_memory_allocated() / 2**30, 2), peak_reserved_gib=round(torch.cuda.max_memory_reserved() / 2**30, 2),
             coverage=round(float(have.sum() / cov.sum()), 3), flags=flags)
    print('RESULT', json.dumps(r), flush=True); log.append(r)
json.dump(log, open(os.path.join(ROOT, tag, 'timing.json'), 'w'), indent=1)
