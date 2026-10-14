# run_inbox.py - reference images -> creature asset

Input: `E:\gen3d\inbox\<animal>\hero.png` (required, 3/4 view) + optional `side.png` (left-facing), `front.png`, `back.png`.
See `E:\Github\anyCreature\harness\lab\PROMPTS_reference_images.md` for how to make them.

## Usage (system python)

    python E:\gen3d\run_inbox.py <animal> [--seeds 0,1] [--lowvram]       # phase 1: candidates
    python E:\gen3d\run_inbox.py <animal> --pick <candidate>              # phase 2: finish chosen one

Phase 1: mask all views (mask8; images with real alpha are kept as is) -> shape generation
(side.png present: Hunyuan3D-2mv variants `a`/`b` [+front] AND 2.1-on-hero; else 2.1 only) -> clean8 -> render.py
sheet per candidate -> `work/contact_sheet.png` + `work/candidates.json`. Nothing is auto-picked.
Candidate names: `h21_s<seed>`, `mv<af|bf|a|b>_s<seed>`.

Phase 2 (`--pick`): hi.obj -> sheet.png -> Paint 2.1 + RealESRGAN (tex13/paint13.py, masked hero as reference)
-> textured.glb -> QuadriFlow 1500 and 5000 (lowpoly/run_classic.py) -> wire.png -> rig (rig.py + export_glb.js).

Other flags: `--force` regenerate, `--no-rig`. Rig is skipped for eagle, shark, frog, kangaroo (quadruped-only skeleton).
Phase 1 is skipped on `--pick` if `work/candidates.json` exists.

## Output
`E:\gen3d\assets\<animal>\` : hi.obj, textured.glb, textured_preview.png, lp_1500.obj, lp_5000.obj, rigged.glb,
sheet.png, wire.png, manifest.json (with timings).
Work dir `E:\gen3d\inbox\<animal>\work\` : masks (ref_rgba.png, side.png...), raw*/cand/, sheets/, logs/<stage>.log, timings.json,
`_stage/` (generated copies of the stage scripts, see below).

## How stages are called
Existing scripts are not edited. Where they hardcode paths/seeds (gen21.py, mv/gen_mv.py, tex13/paint13.py, rig/rig.py),
run_inbox.py writes a copy into `work/_stage/` with those literals substituted (fails loudly if the source drifts) and
runs it. Venvs: `venv` (gen, clean8, paint, rig), `venv_lp` (QuadriFlow), system python (render.py, wire.py), node (GLB).
Do NOT put the CUDA-13 dir on PATH (torch fails to load); paint21 does `add_dll_directory` itself.

## Notes / TODO
- `--lowvram`: no stage script takes low-VRAM options yet; hook is marked TODO in `stage_generate` (lowvram lane results:
  octree/num_chunks/cpu offload in `E:\gen3d\lowvram\tests\shape.py`).
- `back.png` is masked but unused (gen_mv.py has no back slot).
- Rig state of the art is wolf/horse-tested only; other quadrupeds may need rig.py fixes.
