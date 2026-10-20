# Commercially-safe texture generators: round texc (2026-10-20)

Meshes: E:\gen3d\r9pick\<animal>.obj (98k faces, no UVs). Refs: same as paint13 (ORIG in common.py).
Outputs: E:\gen3d\texc\<method>\<animal>\{textured.glb, preview.png, albedo.png, views.png}.
Previews use the tex13 4-view layout. They are rendered with our own moderngl rasterizer, because
glb_preview21 uses Hunyuan's custom_rasterizer.
Montages: _cmpAB.png has, per animal, rows for tex13, then A, then B. _cmpcap.png shows the wolf for A,
A under the cap, B, and B under the cap.
Venv: E:\gen3d\venv_tex2 (torch 2.11.0+cu128, diffusers 0.33.1, transformers 4.48.3, moderngl, xatlas).
Weights: E:\gen3d\texc\models\ (local_dir downloads from the official HF repos).

## Shared clean stack (common.py)
- UV unwrap: xatlas (MIT), 2048, cached in _uv/.
- Rasterizer: moderngl (MIT). It renders the control maps, the depth/visibility, the UV-space position and
  normal maps, and the previews. NO nvdiffrast, custom_rasterizer, cvcuda, pytorch3d or kaolin.
- Bake: numpy projection with a depth-test visibility check and cos^4 weights. Unseen texels get OpenCV
  TELEA inpaint, then a 16 px chart dilation.

## Method A: MV-Adapter ig2mv + SDXL (mva.py), recommended
Image + geometry -> 6 orthographic views (768 px, 50 steps, CFG 3), then the bake above. The upstream
mesh_utils (nvdiffrast/cvcuda) is NOT imported; only the pipeline, attention processors and scheduler are used.
Patch in src/MV-Adapter, behind the env flag MVA_LEAN_REF=1 (default off): the reference-attention states
are kept at batch 1 and broadcast inside the processor. Upstream repeats them x6 views x2 for CFG and then
clones them, about 3 GB. The patched maths is the same, but I did not run a bit-exact check.
--lowvram: the text encoders run once and then move to CPU, the UNet weights are stored in fp8 (fp16
compute), and the VAE is tiled at 384.

## Method B: Sequential depth-ControlNet inpainting, Text2Tex/TEXTure style (seqinp.py)
SDXL ControlNet-inpaint (depth) with an IP-Adapter on the reference. 12 ortho views at 1024 px, 30 steps.
Each view regenerates only the unseen or grazing-angle texels and is baked straight away.
--lowvram: the UNet and ControlNet are stored in fp8, with model CPU offload and VAE tiling.

## Results (shared GPU box with concurrent jobs; times are upper bounds; pipeline load of 20-490 s not included)
| method | animal | per-animal | gen | peak alloc / reserved | coverage |
|---|---|---|---|---|---|
| A full | wolf (cold) | 263 s | 83 s | 15.1 / 18.4 GiB | 0.99 |
| A full | horse/elephant/eagle/kangaroo | 72/38/27/27 s | 59/26/18/17 s | 15.1 / 18.4 | 0.98/0.96/0.94/0.98 |
| A, 7.5 GiB cap | wolf/elephant | 136/115 s | 95/70 s | 5.24 / 6.54 GiB | 0.99/0.96 |
| B full | horse/eleph/eagle/kang/wolf | 382/225/226/129/138 s | 230/145/156/80/91 s | 13.3 / 14.5 GiB | ~1.0 |
| B, 7.5 GiB cap | wolf/elephant | 493/772 s | 442/651 s | 5.84 / 6.28 GiB | 1.0 |

## By-eye quality vs tex13 (Hunyuan3D-2.1 paint)
- A is roughly equal to tex13 and better on some animals. The elephant is grey with wrinkles and good tusks
  (tex13 is brown). The eagle head and feathers are sharper. The kangaroo is consistent. The wolf's right side
  and face are good; its left side is plausible but the eye is softer.
  Weaknesses: the horse tail and lower legs come out silvery-white (tex13 is cleaner there), there is mild
  baked-in specular, and there are small inpainted patches under the belly and between the legs.
- B is worse than A. The first side view is excellent, with the most detailed fur of any method. The later
  views drift: the opposite side is washed-out or pale (horse, elephant, eagle), the kangaroo darkens, and the
  seams between views are visible. It is a fallback or refinement pass, not the main generator.
- The 7.5 GiB cap does not visibly change quality for either method.

## Licence table (read 2026-10-20)
| component | used in | licence | evidence |
|---|---|---|---|
| MV-Adapter code (github huanngzh/MV-Adapter) | A | Apache-2.0 | LICENSE "Apache License Version 2.0, January 2004"; §2 grant "perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable" |
| MV-Adapter weights (HF huanngzh/mv-adapter, ig2mv_sdxl) | A | Apache-2.0 | card `license: apache-2.0` |
| SDXL base 1.0 | A, B | CreativeML OpenRAIL++-M | LICENSE.md §II "copyright license to reproduce, prepare, publicly display, publicly perform, sublicense, and distribute"; §III allows SaaS ("host for Third Party remote access"); only use-based restrictions (Attachment A, e.g. unlawful use), no non-commercial clause |
| sdxl-vae-fp16-fix | A, B | MIT | card `license: mit` |
| diffusers/controlnet-depth-sdxl-1.0 | B | OpenRAIL++-M | card `license: openrail++` |
| h94/IP-Adapter SDXL vit-h + image encoder | B | Apache-2.0 | card `license: apache-2.0` (encoder: OpenCLIP ViT-H-14) |
| diffusers / transformers / accelerate | A, B | Apache-2.0 | PyPI metadata |
| moderngl | raster | MIT | LICENSE "MIT License" |
| xatlas | UV | MIT | LICENSE "MIT License ... Permission is hereby granted, free of charge" |

Caveat: the OpenRAIL++-M use restrictions must be passed on when redistributing the weights; they do not
block commercial use of outputs. Not legal advice.

## Rejected candidates
- TEXGen: the repo has no licence (all rights reserved by default) and needs SD2-depth plus sd-image-variations.
- Paint3D: Apache code, but needs kaolin 0.13 and pytorch3d CUDA builds on Windows; the licence of the
  UV-position ControlNet weights is unclear.
- SyncMVD: MIT, and SD1.5 is OpenRAIL-M (OK), but pytorch3d needs a CUDA build; MV-Adapter covers the same idea better.
- TRELLIS.2 texturing: nvdiffrast plus gated DINOv3.
- Hunyuan3D-Paint: Tencent licence.
- Pure reference projection: the refs are 3/4 views with unknown poses and cover one side only.

## Repro
    set MVA_LEAN_REF=1
    E:\gen3d\venv_tex2\Scripts\python.exe E:\gen3d\texc\mva.py wolf horse elephant eagle kangaroo
    E:\gen3d\venv_tex2\Scripts\python.exe E:\gen3d\texc\mva.py --cap --lowvram --tag=mvadapter_cap7p5 wolf elephant
    E:\gen3d\venv_tex2\Scripts\python.exe E:\gen3d\texc\seqinp.py [--cap --lowvram --tag=X] wolf ...

Known gaps: the cap was tested on wolf and elephant only. The bake runs on CPU numpy. Albedo only:
metallic is 0 and roughness is 0.9, set as factors.
