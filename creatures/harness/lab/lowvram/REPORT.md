# Creature workflow on 8 GB: feasibility (2026-10-14)

Emulation: every GPU test process called `torch.cuda.set_per_process_memory_fraction(7.5/95.6)` (`lowvram/cap.py`, CAP=1),
plus `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. A stage passes if it finishes without OOM under the cap.
Peaks are torch max_memory_allocated / max_memory_reserved. Times are noisy because the GPU was shared with
another lane at 99% util.

## Per stage (wolf)

| stage | baseline (96 GB config) peak alloc/res | best <7.5 GB config | capped peak alloc/res | time base -> capped | quality |
|---|---|---|---|---|---|
| T2I HunyuanDiT-v1.1 distilled, 1024², 25 steps | 8.38 / 9.13 GiB (all on GPU) | `enable_model_cpu_offload()` + VAE tiling/slicing, fp16 | 3.98 / 4.34 | gen 18 s -> 14-44 s | identical image (`t2i/cmp.png`) |
| Shape Hunyuan3D-2.1, octree 380, 50 steps | 7.63 / 8.51; **OOMs under cap** | load on CPU, accelerate `cpu_offload_with_hook` chain conditioner -> DiT -> VAE (repo's own `enable_model_cpu_offload` is broken: no `components`) | 6.45 / 6.75 | 31 s -> 27-31 s | bit-identical mesh (max vertex diff 0.0) |
| Remove BG (mask8), clean8, QuadriFlow (pyquadriflow), rig | CPU | CPU (run with CUDA_VISIBLE_DEVICES= ) | 0 | unchanged | unchanged |
| Texture Hunyuan Paint 2.1 + RealESRGAN, 9 views @512, 4K tex | 15.44 / 24.20; 9 views OOMs under cap even with all reductions | **6 views @512**; multiview UNet+VAE on GPU only for the diffusion call; DINOv2-giant and CLIP text encoder staged GPU<->CPU around their single forward; FF chunking (chunk 1, dim 0) on 64 UNet blocks; VAE slicing+tiling; RealESRGAN `tile_size=256`; forced `_execution_device=cuda` | 6.53-6.56 / 7.26-7.30 | paint 109 s -> 50-90 s | 6 vs 9 views: near-identical; slightly more blotchy patch on one neck side (`tex/base` vs `tex/v6off`) |

Weight sizes that set the floor: shape DiT 3.05 B params (5.7 GiB fp16); paint UNet 1.96 B + DINOv2-giant 1.1 B + CLIP 0.34 B.
Headroom left: shape ~1.0 GiB, paint ~0.2 GiB reserved (tight).

## Full chain (`chain.sh <animal> <prompt_idx> <seed>`), all GPU stages capped
| animal | T2I | shape | quad | paint | rig | total |
|---|---|---|---|---|---|---|
| wolf | pass 4.0 GiB | pass 6.45 | 5208 quads | pass 6.53 | pass (34 joints, idle/walk) | ~5 min |
| horse (new T2I) | pass | pass | 4839 quads | pass 6.55 | **FAIL** rig prototype: "expected 4 leg blobs, got 3" (low tail touches hind legs) - geometry, not VRAM |
| horse_r9ref (96 GB run's ref_c5) | n/a | pass | 5321 quads | pass 6.56 | pass after leak-proof voxel fill (TailRoot/TailTip flagged outside) |

Outputs per animal dir: ref.png, ref_rgba.png, raw.obj, final.obj(+png), lowpoly_quad.obj(+png), textured.glb (tex/preview.png), rigged.glb(+png).

## Not done
TRELLIS v1 fp16, Hunyuan3D-2mini/turbo, SDXL-Turbo: not tested - the default models already fit with offload, and
none of the smaller variants are cached (downloads). Real GTX 1050 (2-4 GB) would NOT fit shape (5.7 GiB weights) or paint.
Caveats: emulation caps torch allocations only (no CUDA context/driver overhead ~0.3-0.5 GB, no PCIe-bandwidth
cost of offload on a laptop); paint at 7.3 GiB reserved is marginal on a real 8 GB card driving a display.
rigrun.py adds a leak-proof voxel fill (binary closing) around rig.voxelize - rig.py itself unchanged.
