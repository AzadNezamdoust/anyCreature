# exp game_pack: game pack emitter vs baseline (stage-4 glb as-is), 2026-10-22

Emitter: `kit/game_pack.py` (new file; zoo folders untouched). Outputs: `t8/game_pack/<name>/` (pack: `unity/*.glb|fbx`, `unreal/*.fbx`, `<name>_pack.blend`, `renders/`, `pack_report.json`; baseline: `<name>/baseline/`).
Run: `blender -b --factory-startup -P kit/game_pack.py -- --glb <stage4.glb> --out <dir> --name <n> [--baseline]`, about 90 s per creature.

| metric | hippo A / B | werewolf A / B | penguin A / B |
|---|---|---|---|
| round-trip core (bones, bind pose, unit scale, clip lengths) | PASS / PASS x3 (glb, Unity fbx, Unreal fbx) | PASS / PASS x3 | PASS / PASS x3 |
| round-trip full (+ sockets, LOD0-3, hurtboxes, UCX/CAP) | FAIL (none present) / PASS x3 | FAIL / PASS x3 | FAIL / PASS x3 |
| bones | 23 | 24 | 15 |
| Unreal scale check | n/a / 0.0100 (cm) exact, bind err 0.000 % H | same | same |
| LOD tris (0/1/2/3) | 3192 / 1596 / 804 / 332 | 3896 / 1944 / 978 / 426 | 2776 / 1392 / 714 / 326 |
| LOD min silhouette IoU, 8 views (1/2/3), gate 0.90 | .996 / .991 / .973 | .989 / .968 / .930 | .996 / .988 / .960 |
| hurtbox capsules / sockets | 23 / mouth, hand_L/R, back | 24 / same | 15 / same |
| clip QA: penetration % H (attack/idle/move) | 1.07 / 0.14 / **5.15** | 0.0 / 0.0 / 0.94 | 0.0 / 0.0 / 2.31 |
| clip QA: planted-foot slide std % H/frame (attack/idle/move) | 0.72 / 0.07 / 1.32 | 0.60 / 0.01 / 0.60 | 0.0 / 0.0 / 0.11 |
| clip QA: loop gap % H | 0.0 all | 0.0 all | 0.0 all |

Clip QA uses the same clips for A and B, so the numbers are identical (it only measures). It is new information that the baseline does not have: hippo `move` sinks 5.15 % H below the rest floor, and penguin `move` sinks 2.3 %.

## LOD readability judge (one Opus seat, both orders; images `judge_order1.png` and `judge_order2.png`)
- 128 px, baseline vs LOD1: tie on all 3 creatures, in both orders.
- 80 px, baseline vs LOD2: baseline wins hippo and penguin (body banding) in both orders; werewolf is a tie.
- 48 px, baseline vs LOD3: baseline wins all 3 in both orders.
- The order flip was consistent, so this is a real preference, not position bias.
- Every species still reads at every size.

My read agrees with the judge. LOD1 is invisible. LOD2 is fine at 80 px. LOD3 at 10 % is visibly blocky: hippo snout, werewolf ears and arms. A 15 % ratio is worth trying for LOD3.

## Verdict: ADOPT (additive)
- The pack passes full round-trip on all 9 exports, where the baseline passes 0/3.
- LOD silhouette IoU is at least 0.93 everywhere.
- Clip QA exposes the hippo and penguin move penetration.
- The cost is a readability loss at LOD3 (10 %) only. A loss against full detail is expected, but it is real.

Notes:
- Renders are Workbench grey: the material colours did not show. This is the same for A and B.
- UCX_ is the Unreal static-mesh convention. Skeletal meshes use the HB_ capsules (custom props `radius` and `height`) or a physics asset.
- Cost: about 25 turns, about 25 min wall (6 Blender runs of about 1.5 min, plus 3 reruns).

ab_compare.jpg: rows = per creature: 192 px, then game-distance size; columns = baseline, LOD0, LOD1, LOD2, LOD3.
