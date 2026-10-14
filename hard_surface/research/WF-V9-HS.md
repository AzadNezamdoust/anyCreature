# WF v9 — the Blender hard-surface (HS) look stage (2026-10-03)

**Why.** Owner on the WF v8 gold models: "they do not look like the source; small differences, but those small things
are a lot". Gold matches silhouettes (agree .70–.98) but reads crude: no chamfers, insets, real slats or bolts. WF v9
keeps gold as the **measurement stage** and adds an HS **look stage** after a subject reaches phase owner / done.

## What changed
1. **Blender 5.1 hard-surface build** — Agent `gold-hs-modeller` (Opus 5.5, maxTurns 160) writes
   `out/blender-hs/<s>/build.py`: one function per semantic part on `scripts/hs/hs.py` (chamfered boxes, profile
   extrusions, MANIFOLD booleans, bores, tyres / hubs, wire cages), starting from the gold `model.mjs` metres; clean
   topology (0), tris ≤ budget, ≥ 4 render-compare passes, `--final`.
2. **Judge-consistent scoring** — `scripts/hs/run_pass.py` dumps the built triangles and scores them with
   `scripts/hs/judge_mesh.mjs`, i.e. the gold judge's own code (uniform sigma fit, 512 px orthos with drift rects,
   registered concept iou + drift-masked agree). Round-trip: gold `model.mjs` through Blender reproduces
   `view/model-view.json` to 4 decimals (apc_8x8, main_battle_tank). Gate: no view's agree more than .01 below gold.
3. **Blind Fable review + one Opus polish** — Agent `gold-hs-reviewer-fable` (Fable 5.1) writes `review_fable.md`:
   strict art director, every small difference vs concept + turnaround, measured, fixes keyed to build.py, likeness
   /10, top 10, never re-flags facts.json / drift rects. Then ONE `gold-hs-modeller` polish pass fixes every item,
   the turnaround winning over the reviewer (K = 1; residual → owner packet, POLISH.md `## Owner`).
4. Plumbing: harness promoted from gitignored `out/blender-hs/_harness/` to tracked `scripts/hs/`;
   `node scripts/v7/gold.mjs hs [--subject s]` prints each subject's stage (wait / build / review / polish / owner) and
   NEXT from the files present (read-only); skill `gold-model` gained the HS section.

## Evidence (out/blender-hs/<s>/stats.json, final pass after polish; agree gold / HS)

| subject | side | front | rear | top | concept | gate | tris | Fable likeness (before polish) |
|---|---|---|---|---|---|---|---|---|
| apc_8x8 | .974 / .969 | .961 / .962 | .959 / .957 | .958 / .952 | .966 / .958 | pass | 7868/8000 | — (pilot, not reviewed) |
| transport_heli | .904 / .901 | .768 / .760 | .822 / .835 | .699 / .703 | .782 / .774 | pass | 5390/8000 | 5.5 |
| attack_heli | .931 / .945 | .884 / .906 | .888 / .911 | .812 / .837 | .565 / .556 | pass | 4916/8000 | 6 |
| rocket_truck | .863 / .859 | .926 / .933 | .918 / .931 | .940 / .934 | .950 / .942 | pass | 7842/8000 | 6 |
| main_battle_tank | .953 / .944 | .961 / .965 | .953 / .952 | .982 / .972 | .956 / .932 | **FAIL** concept −.024 | 7894/8000 | 6 |
| combat_bike | .865 / .893 | .910 / .912 | .882 / .888 | .879 / .882 | .739 / .731 | pass | 7084/8000 | 6.0 |

All six: topology 0, under budget. The HS models hold the gold silhouette (29 of 30 views within .01, 14 above it)
while adding the part-level detail; the look verdict is compare.png in each folder (owner gate). Gold numbers are the
gold `state.json` baseline at the time of each final pass (apc_8x8's gold has since moved on in its r2).

## Lessons
- Harness numbers from before the judge fix (render at scale 1, concept plain IoU) are not comparable with gold —
  only post-fix `VIEW ... | gold ...` lines count.
- Never pre-scale (no K factor, no root scale, no hand-edited concept_cam.json): the judge fits sigma itself.
- `opus-worker` stops at 60 turns — builders need ≥ 150: use `gold-hs-modeller`, or general-purpose + model opus with
  its body as the prompt.
- Long concept-vs-turnaround conflicts (the reviewer reads one, the turnaround says another) are the owner's call, not
  another polish loop.
- The reviewer is blind: it gets images + build.py, never the modeller's report.

## Function stage (2026-10-04)
After polish each unit gets a rig: `out/blender-hs/<s>/rig.json` (contract `scripts/hs/rig.md`, brief
`out/blender-hs/RIG-BRIEF.md`) tested by `scripts/hs/rig_pass.py` + `rig_sim.py` and exported as `<s>_rigged.glb`
with animation clips. Final harness run, all 10 units (passed / total):

| unit | tests | note |
|---|---|---|
| apc_8x8 | 56/56 | |
| rocket_truck | 44/44 | launcher elevates 12 deg only (pivot mid-box); `bore_m` tolerance widened; ground_y 0.029 |
| supply_truck | 40/40 | bed wheel notch, taller fenders, flaps moved (tyres were inside them) |
| jeep_gun | 36/36 | |
| transport_heli | 34/34 | rotor phase 28 deg from the colliding window; cargo bay is a plate |
| combat_bike | 21/21 | ground_y 0.0136; roll locked |
| aa_tank | 18/18 | |
| light_tank | 16/16 | flat track run floats 34 mm |
| main_battle_tank | 19/20 | look gate (side -.015, concept -.020 vs gold) |
| attack_heli | 15/16 | parked tip-back 9.6 deg vs 30 |

Lessons:
- Look-stage builds were not riggable as built: tyres inside fenders / beds / jacks, turret bases sunk in decks, struts
  inside solid tyres. BRIEF.md now carries the "build it riggable" rules so the look stage leaves clearance.
- Tracked units: road wheels, sprockets and idlers are static meshes and the track is one scroll-speed parameter; no
  per-wheel travel. Open item.
- The sheet must be looked at, not only counted: the glTF exporter left a child joint's rest offset rotated (the tank's
  gun was drawn 1 m off its turret) while every numeric test passed; `set_pose` now restores rest offsets.
- Agents share `rig_pass.py`; edits stayed additive (suspension_arm, run_pose / sync, ground_y, bbox_centre_turn).

## Look method A/B: strict line matching vs "what makes sense" (2026-10-04)
Owner's premise: the concept and turnaround are generated drawings, not views of one 3D object, so forcing line-to-line
alignment is wrong. Test: 10 units x 2 arms, same starting build, same budget (4-8 passes, close-ups), briefs in
`out/blender-hs-ab/BRIEF-{COMMON,strict,soft}.md`, results in `out/blender-hs-ab/{strict,soft}/<s>/`.

| | strict (.01 gate, ink on edges) | soft (inventory + sense, .04 limit) |
|---|---|---|
| mean agree vs gold, all views | +.002 | -.003 |
| mean change vs start | +.001 | -.004 |
| units inside the old .01 gate | 9 / 10 | 2 / 10 |
| units inside .04 | 10 | 10 |
| effort (tokens per unit) | ~300-390k | ~175-290k |

- Strict builders' own reports: in 8 / 10 units half or more of the rounds failed the concept gate and were repaired
  or reverted; in 7 units a part ended away from where the drawings agree, to satisfy another drawing; attack_heli
  tuned rotor height 14 mm to the judge's raster.
- Measured source conflicts: jeep nose parts 0.10 m lower in front than side; light_tank roof parts 0.2 m further aft
  in top than side; apc turret yaw 9 deg (top) vs 33 deg (front); supply_truck orthos ~12 % taller than the frame;
  rocket_truck facts vs side up to 0.45 m.
- Blind judges (Opus + Sonnet, two rounds with X / Y swapped): 16 of 20 seat-unit picks flipped with row order or
  tied; consistent picks soft 3, strict 1. Opus chose the bottom row 10 / 10 then 8 / 10. Not conclusive.
- Owner (labelled sheets): "soft is better in most details; some details strict looks better; generally prefer soft."
  -> `scripts/hs/method.md` is the look method; gate = no ortho view more than .04 below gold, concept not gated.
  Soft builds promoted to `out/blender-hs/<s>/` (rigs stale until re-run: `gold.mjs hs` shows STALE).
- Neither arm changed base proportions (tank hull slab vs tall tracks, jeep gun height, transport_heli nose): one
  polish round does not; method.md step 1 "major masses first" is the rule that came out of it.
- New tool from this round: `scripts/hs/closeups.py` (per-part source | build | build + source ink at 2-3x).
