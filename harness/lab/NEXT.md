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
