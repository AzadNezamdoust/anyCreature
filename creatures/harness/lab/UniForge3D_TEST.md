# UniForge3D test (2026-10-20)

Repo cloned: E:\gen3d\UniForge3D (github.com/xibushu/UniForge3D, MIT code). No venv built, no weights downloaded.

## Result: BLOCKED (gated DINOv3), stopped at step 1

Checkpoints loaded (uniforge3d/configs/pipeline.json, models/loaders.py, models/dino.py):

| Checkpoint | Use | Gated? |
|---|---|---|
| xibushu/UniForge3D (stage1 structure joint model, shape512/1024 denoiser + VGGT adapter, texture1024 denoiser + adapter, VGGT condition) | all stages | No (public, CC BY-NC 4.0) |
| microsoft/TRELLIS-image-large | sparse-structure decoder | No |
| microsoft/TRELLIS.2-4B | shape/texture decoders etc. | No |
| facebook/dinov3-vitl16-pretrain-lvd1689m | image condition for structure, shape512, shape1024 and texture stages (`_encode_dino`) | **YES: HTTP 401, gated, no HF login** |
| briaai/RMBG-2.0 | background removal | YES, but skippable (our refs have alpha) |

DINOv3 is not optional: every stage takes DINOv3 features (`dino_features["sparse_structure"]`, `["shape512"]`, `["shape1024"]`), and the released checkpoints were trained on them, so swapping DINOv2 (which is cached locally) would not give valid results. This is the same blocker as TRELLIS.2.
No local DINOv3 copy exists (HF cache only has dinov2-giant).

## Not done
Steps 2-3 (horse multi-view / wolf single-view runs, VRAM peaks, 8 GB fitting) need DINOv3.
Notes for later: the pipeline already has `low_vram=True` by default (per-stage model swapping via `_use_models`), plus `--low_vram` in infer.py.
Setup translation for Windows: reuse venv_trellis2 wheels (cumesh/flex_gemm/nvdiffrast/o_voxel); upstream pins torch 2.6 cu124 + flash-attn 2.7.3 and TRELLIS.2 commit 75fbf01.

## Unblock
Azad requests access to facebook/dinov3-vitl16-pretrain-lvd1689m on Hugging Face and runs `hf auth login` himself; that also unblocks TRELLIS.2.

## Licences
Code MIT. UniForge3D weights CC BY-NC 4.0 (VGGT-1B derived), non-commercial. DINOv3 has its own licence (gated). RMBG-2.0 needs a commercial licence. TRELLIS.2 weights MIT.
