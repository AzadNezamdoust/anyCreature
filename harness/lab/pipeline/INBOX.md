# run_inbox.py - reference images -> creature asset

Input: `E:\gen3d\inbox\<animal>\hero.png` (required, 3/4 view) + optional `side.png` (left-facing), `front.png`, `back.png`.
See `E:\Github\anyCreature\harness\lab\PROMPTS_reference_images.md` for how to make them.

## Usage (system python)

    python E:\gen3d\run_inbox.py <animal> [--seeds 0,1] [--lowvram] [--vram-cap 7.5]       # phase 1: candidates
    python E:\gen3d\run_inbox.py <animal> --pick <candidate>              # phase 2: finish chosen one
    python E:\gen3d\run_inbox.py --all [--lowvram --vram-cap 7.5]          # phase 1 for every inbox\<animal>\hero.png
    python E:\gen3d\run_inbox.py --pick-file picks.txt [--lowvram ...]     # phase 2 batch; lines "<animal> <candidate>", # comments
    python E:\gen3d\validate.py E:\gen3d\assets\<animal>                  # re-check finished assets (also runs at end of phase 2)

Batch mode runs each animal in its own subprocess (one failure does not stop the others), prints a summary and writes
`inbox/batch_all.json` / `inbox/batch_pick.json` (rc + seconds per animal); exit 1 if any animal failed.

Phase 1: mask all views (mask8; images with real alpha are kept as is) -> shape generation
(side.png present: Hunyuan3D-2mv AND 2.1-on-hero; else 2.1 only). 2mv slots: side -> left, front -> front,
back -> back; mirrored side -> right only when there is neither front nor back -> clean8 -> render.py
sheet per candidate -> `work/contact_sheet.png` + `work/candidates.json`. Nothing is auto-picked.
Candidate names: `h21_s<seed>`, `mv<slots>_s<seed>` with slots from l/f/b/r, e.g. `mvlfb_s0` (side+front+back), `mvlf_s1`, `mvlr_s0` (side + mirror).

Phase 2 (`--pick`): hi.obj -> sheet.png -> Paint 2.1 + RealESRGAN (tex13/paint13.py, masked hero as reference)
-> textured.glb -> QuadriFlow 1500 and 5000 (lowpoly/run_classic.py) -> wire.png -> rig (rig/rig_robust.py + export_glb.js)
-> validate (validate.py -> assets/<animal>/report.json; phase 2 exits non-zero if invalid).

Other flags: `--force` regenerate, `--no-rig`. Rig body-plan gate: rig_robust.py finds feet from ground contacts; if they are not a
2x2 quadruped stance (biped/kangaroo, perched bird, legless shark, sprawled crocodile/frog) the rig is skipped and
`assets/<animal>/rig_skip.json` says why (exit 3, not an error; validate.py then only warns).
Phase 1 is skipped on `--pick` if `work/candidates.json` exists.

## Output
`E:\gen3d\assets\<animal>\` : hi.obj, textured.glb, textured_preview.png, lp_1500.obj, lp_5000.obj, rigged.glb,
sheet.png, wire.png, manifest.json (with timings), report.json (validation), rig_skip.json (if rig skipped).
Work dir `E:\gen3d\inbox\<animal>\work\` : masks (ref_rgba.png, side.png...), raw*/cand/, sheets/, logs/<stage>.log, timings.json,
`_stage/` (generated copies of the stage scripts, see below).

## How stages are called
Existing scripts are not edited. Where they hardcode paths/seeds (gen21.py, mv/gen_mv.py, tex13/paint13.py, rig/rig.py),
run_inbox.py writes a copy into `work/_stage/` with those literals substituted (fails loudly if the source drifts) and
runs it. Venvs: `venv` (gen, clean8, paint, rig), `venv_lp` (QuadriFlow), system python (render.py, wire.py), node (GLB).
Do NOT put the CUDA-13 dir on PATH (torch fails to load); paint21 does `add_dll_directory` itself.

## Notes / TODO
- `--lowvram` (8 GB-class; measured in `lowvram/REPORT.md`): shape (2.1 and 2mv) loads on CPU and runs an accelerate
  `cpu_offload_with_hook` chain conditioner->DiT->VAE (mesh bit-identical); paint = `lowvram/tests/paint.py` (6 views, UNet/VAE on GPU only
  during diffusion, DINOv2/CLIP staged, FF chunking, VAE tiling, ESRGAN tile 256; ds=1 dil=0 like normal mode); mask/clean8/QuadriFlow/rig run with
  CUDA_VISIBLE_DEVICES= (CPU only). Implemented as substitutions/copies in `work/_stage/` (originals untouched). 2mv offload path verified on horse (raw meshes byte-identical to normal mode; peak 3.19 GiB alloc / 3.60 reserved).
- `--vram-cap <GiB>` (default off): every GPU stage gets a prepended `torch.cuda.set_per_process_memory_fraction` and prints a `PEAK` line;
  peaks are saved in timings.json (`peak_<stage>`) and printed at the end. Works with or without --lowvram (normal mode will OOM under 7.5).
  Caps torch allocations only (no CUDA context overhead). Verified: `run_inbox.py wolf --lowvram --vram-cap 7.5 --pick h21_s1 --force` passes all stages
  (shape 7.06 GiB alloc / 7.38 reserved, paint 6.54 / 7.27; raw meshes byte-identical to normal run, texture visually equal).
- Rig (both modes) uses `rig/rig_robust.py`: rig.py untouched; leak-proof voxel fill (as rigrun.py); legs = foot-contact blobs of the lowest
  3 cm (merged pair split by 2-means), slab voxels assigned to the nearest foot within 9 cm, the rest (low tail touching hocks) dropped.
  Fixes "expected 4 leg blobs, got 3". Gate tested: horse, wolf, elephant, giraffe -> quadruped; kangaroo, eagle, shark, frog,
  crocodile -> skip. There is no biped/bird/fish skeleton yet (rig.py spec is the wolf quadruped).
- validate.py checks: mesh, UV, baseColor texture+image, skin, joints, inverse binds == joints, JOINTS_0/WEIGHTS_0, weight sums within
  0.01 of 1, animations idle+walk, triangle ranges (textured 1k-2M, rigged 500-100k), file sizes (80 / 40 MB).
