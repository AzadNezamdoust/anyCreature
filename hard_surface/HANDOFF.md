# LLMModeling — workflow hand-off (2026-10-05)

Recover point: tag `llmmodeling-wf-v10-milestone-2026-10-05` (commit 586140e + this file's commit).
Weapon-by-weapon state and resume steps: `HANDOFF-WEAPONS.md`. Commands: `WORKFLOW-V10.md`.

## Goal
One concept image → a stylised low-poly game asset with clean topology, built by an LLM writing code (no neural
image-to-3D; the owner rejected that route), that looks like its source in detail ("small differences matter") and has
working moving parts. Sets so far: 10 war vehicles, 10 normal guns, 10 futuristic cartoon guns.

## The workflow as it stands (WF v10, direct pipeline)
| stage | what happens | tools / briefs | who |
|---|---|---|---|
| S1 setup | description → concept image → 2×2 four-view sheet → registration (pixels ↔ metres), frame, concept camera | `gold.mjs new`, `imagegen.mjs --gen gpt`, `turnaround.mjs`, `hull.mjs`, `solve-camera-hull.mjs`, `scripts/hs/dump_frame.mjs`, `dump_concept_cam.mjs` | Opus agent; GPT for images only |
| S2 look | Blender 5.1 `build.py` on `scripts/hs/hs.py`, ≥ 6 render-compare passes, close-ups | `scripts/hs/run_pass.py`, `closeups.py`, `out/blender-hs/BUILD-DIRECT.md`, `scripts/hs/method.md` | `gold-hs-modeller` (Opus) |
| S3 review | blind strict art-director review, likeness /10, top-10 fixes; then ONE polish | `gold-hs-reviewer-fable`, then `gold-hs-modeller` mode polish | Fable, then Opus |
| S4 function | `rig.json`, pivot / sweep / socket tests, rigged glb with clips | `scripts/hs/rig_pass.py`, `rig_sim.py`, `scripts/hs/rig.md`, `out/blender-hs/RIG-BRIEF.md` | Opus (same agent as polish) |

`node scripts/v7/gold.mjs hs [--subject s]` prints each subject's stage and the next step (read-only).
The 10 vehicles went the older way (gold JS-kernel rounds first, then S2–S4); new subjects use `"pipeline": "direct"`.
Classes: `vehicle`, `weapon`. Styles (`scripts/v7/styles.json`): `cartoon`, `generals`, `fps`, `scifi_toon`.

## The look method (owner decision 2026-10-04, `scripts/hs/method.md`)
- The concept and the four views are generated drawings that contradict each other; do not force line-to-line
  alignment. Build what makes sense: major masses first, then a feature inventory (`FEATURES.md`: every drawn part,
  count, place), view disagreements resolved by sense and written down.
- Gate: tris ≤ 8000, topology 0, no ortho view more than .04 below the reference (gold for vehicles; best earlier pass
  for direct subjects). The concept view is reported, not gated. Never tune geometry to the judge's raster.
- Build riggable from the start: one object per moving part, real clearances, real bores / openings.
- Evidence behind it: 10-unit strict vs soft A/B in `research/WF-V9-HS.md`; owner preferred soft.

## What the numbers do and do not tell
- Agree / IoU measures the outline. Every Fable review so far scored 6–6.5 / 10 with the outline already right: the
  misses are inside it (part shapes, seams, groove forms, tone values, wall thickness). Likeness comes from S3 + polish
  and from the close-ups, not from pushing agree.
- The numeric rig tests can all pass while a part is drawn in the wrong place (tank gun, 2026-10-04). Open every
  compare sheet and rig sheet by eye before showing it to the owner.
- Blind AI A/B judges show row-position bias; judge twice with the order swapped, or let the owner decide.

## State
- Vehicles: 10 / 10 look + function done, all rigs pass on the rebuilt (major-masses) models.
- Normal guns: assault_rifle finished end to end; gatling_gun, grenade_launcher, pump_shotgun built + reviewed, polish
  interrupted; pistol built; rocket_launcher build interrupted at pass 7; four not built. All ten set up.
- Futuristic guns: 8 set up (unseen by the orchestrator except the ray pistol concept), laser_smg partly, disintegrator
  not started. Must be original designs, not copies of any show prop.

## Known weak points (not fixed)
- Concept camera registration is off on combat_bike and both helicopters (and scores .68–.88 on weapons): harness fix
  pending; this is why the concept view is not gated.
- S1 four-view sets often fail the cross-view width checks (bipods, butt pads, funnels); they are installed anyway
  after the stop rule and the builder resolves by sense.
- Harness ink is light grey: seams on dark parts do not read; builders model dark recess faces instead.
- `closeups.py` crops by part role and is slow (~6 min full).
- Tracked vehicles: road wheels spin but have no per-wheel suspension travel.
- Rig joint types `cylinder` and `hinge` are documented but untested on a finished subject; `barrel_spin` ran once on
  the interrupted gatling polish.
- Texture projection (an earlier improvement idea) not started.

## Standing rules
- Models: Opus 5.5 + Sonnet 5.5 for all work; Fable 5.1 only as the blind reviewer / rare tie-break. GPT only for image
  generation. No Gemini / agy. (Owner offered GPT Sol 6.1 high as a builder on 2026-10-05; launching it is blocked by
  the permission classifier until the owner adds a rule.)
- ≤ 6 agents at once. Agents write only inside their subject's folder; harness edits stay additive.
- Never edit: `tools/CharacterStudioV2`, existing `refs/**`, `src/validate/limits.json`, `tools/BlindLoop/config*.json`,
  any gold `model*.mjs`. Never delete permanently, never `git clean`, never run `scripts/v7/gold.test.mjs`.
- Commits: explicit narrow path list (top-level key files of a subject folder, never the whole folder — per-pass
  scratch is ~800 MB), count it first; a staged deletion of `out/ref/gold/jeep_gun/critique/r2-fable.json` stays staged
  and is never committed. Push only when the owner asks.
- Owner-taste calls are never self-ratified; list them and move on.
- Send images with SendUserFile, after opening them.

## Where things are
- `WORKFLOW-V10.md` commands and gates · `research/WF-V9-HS.md` history, A/B evidence, lessons · `research/WF-V10-BRIEF.md`
  the consolidation brief · `scripts/hs/` harness (README, method.md, rig.md) · `out/blender-hs/<s>/` builds
  (build.py, FEATURES.md, compare.png, review_fable.md, POLISH.md, rig.json, rig_sheet.png, `<s>_rigged.glb`) ·
  `subjects/<s>/` setup · `refs/<s>.png` concepts · `out/blender-hs-ab/` the strict vs soft test.
