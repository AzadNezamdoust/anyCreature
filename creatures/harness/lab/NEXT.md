# Paused milestone — 2026-10-14

## State
- Workflow works end to end (harness/lab/pipeline/run_inbox.py, INBOX.md):
  inbox images -> Hunyuan3D-2.1 (or 2mv) candidates + contact sheet -> pick ->
  clean8 -> Hunyuan Paint 2.1 + RealESRGAN texture -> QuadriFlow LODs -> auto-rig -> GLBs.
- --lowvram verified under a 7.5 GiB cap (shape 7.1/7.4 GiB, paint 6.5/7.3 GiB), same
  judged quality as free mode (wolf 6/6, horse 5/5).
- Best blind-judged quality ~6/10 vs AAA (see RESULTS.md). Main limit: reference images.

## In progress when paused (work-in-progress, untested or partly tested)
- run_inbox.py: multi-view path now maps back.png; --all batch and --pick-file added
  (horse multi-view phase 1 ran; phase 2 batch was mid-run when stopped).
- validate.py: GLB checks (mesh, UV+baseColor, skin, weights, idle/walk anims) -> report.json.
- rig_robust.py: leg detection when tail touches hind legs; biped/no-leg paths unfinished.
- WORKFLOW.md (full doc) not written yet.

## Next steps
1. Finish/verify the four items above; re-run horse multi-view phase 2 + validate.
2. Write harness/lab/WORKFLOW.md.
3. User makes Nano Banana / GPT Image refs with PROMPTS_reference_images.md ->
   E:\gen3d\inbox\<animal>\ ; run run_inbox.py --all, critic picks, phase 2, blind-judge vs round 9.
4. Confirm texture stage on a real 8 GB card (7.3 GiB reserved is tight).
5. Optional: TRELLIS.2 needs the user's DINOv3 HF login.

Machine-side assets live in E:\gen3d (venvs, ~40 GB weights, outputs); not in git.

## Pause 2026-10-20 (evening)

Done today: repo split creatures/ + hard_surface/; boxmodel kit on Blender 5.2.2
(E:\gen3d\blender, portable) + census gate + PARAMS/patch prompt; 20 new box-model
creatures (r20, gallery_r20.jpg; blind judging leaked titles - rerun with
judge_pack.py blanking titles); rounds 16-19 + part-aware test in RESULTS.md;
RTX 2070M mode (pipeline/RTX2070M.md, --turing, sm_75 rasterizer, low-RAM load);
--bake-normals (adopt, make default on).

Decisions (Azad): Hunyuan3D-2.1 = shape; Hunyuan Paint 2.1 = texture (only one
with unlit albedo); MV-Adapter = commercial-safe fallback needing delight.
No Fable unless Azad asks.

Stopped mid-run (resume these):
- Pixal3D test (TencentARC, MIT) -> E:\gen3d\pixal\ (was in setup/download).
- Direct3D-S2 test -> E:\gen3d\d3ds2\ (setup done, first runs).
Then: blind Opus judge vs Hunyuan r9pick; if one wins, mesh refinement vs refs
(needs non-nvdiffrast renderer). Item 7 needs Azad's multi-view refs in
E:\gen3d\inbox\<animal>\.

## 2026-10-21
Shape challengers all lose to Hunyuan3D-2.1 (rounds 16, 20, 21: TRELLIS.2,
Pixal3D, Direct3D-S2). Azad: D3D-S2 more detailed but more artifacts -> tuning
lane (E:\gen3d\d3ds2_tuned). Roach in bake pose lane (E:\gen3d\assets\roach,
out/roach_summary.jpg). Normal-map bake now default on.
