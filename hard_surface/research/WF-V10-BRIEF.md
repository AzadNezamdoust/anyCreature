# WF v10 — consolidate the workflow and open it to a second class (FPS weapons) — engineer brief

Owner 2026-10-04: "consolidate the workflow with other 10 models — in this case FPS game weapons: grenade launcher,
gatling gun, rifle and so on — 10 of them." Work dir `D:\Git\checkout\tools\LLMModeling`.

## What "consolidated" means
Today a subject passes through three generations of machinery: gold setup (concept, turnaround, auditor, owner
gate) → gold rounds (JS-kernel model.mjs, 2 critics, ≤ 3 rounds) → HS look stage (Blender build, Fable review,
polish) → function stage (rig). The 10-unit A/B (research/WF-V9-HS.md) showed the look is decided in the HS stage by
`scripts/hs/method.md`; the gold rounds only supply metres and a silhouette baseline. v10 is ONE direct pipeline:

| stage | does | tools |
|---|---|---|
| S1 setup | description → concept image → 4-view turnaround → registration (px ↔ metres) + concept camera | `gold.mjs new`, `imagegen.mjs --gen gpt`, `turnaround.mjs`, `dump_frame.mjs`, `dump_concept_cam.mjs` |
| S2 look | Blender build straight from the sources by `scripts/hs/method.md` (block-out from the stated size → major masses → feature inventory → details) | `run_pass.py`, `closeups.py`, agent gold-hs-modeller |
| S3 review | blind Fable detail review + ONE polish | gold-hs-reviewer-fable, gold-hs-modeller polish |
| S4 function | rig.json + tests + rigged glb | `rig_pass.py` |

No JS-kernel rounds, no critics, no auditor agent for a `pipeline: "direct"` subject. The existing vehicles keep
working unchanged (their gold state stays; nothing of theirs is deleted or rewritten).

## Your job (engineering, then prove it on ONE weapon)
A. **Class `weapon`.** `scripts/v7/newsubject.mjs` CLASSES accepts only `vehicle`. Add `weapon` with the minimum the
   setup chain, `scripts/v6/ortho.mjs loadTurnaround`, `scripts/hs/judge_mesh.mjs`, `dump_frame.mjs` and
   `dump_concept_cam.mjs` need (class manifest under `classes/`, subject.json template with `"pipeline": "direct"`,
   facts with L / W / H in metres, colour families). A weapon has no hull quad on the ground: the concept camera is
   the style's fixed isometric (30° elevation, 45° azimuth) with scale / offset fitted to the concept's foreground
   box — find the smallest honest way to produce `concept_cam.json` for it. Views: side (the gun's left flank,
   muzzle to the left as the existing convention puts the nose), front (muzzle on), rear, top.
B. **Style `fps`** — a NEW key in `scripts/v7/styles.json` (never edit a used one; the text must start with the exact
   isometric camera sentence the others start with and keep the white-background sentence): stylised first-person-
   shooter weapon, chunky readable low-poly forms, crisp facets and chamfers, flat cel shading, one flat colour per
   surface, thin dark outlines, gunmetal / black polymer / one accent colour as described, no textures, decals,
   text, hands or people.
C. **No Gemini** (owner 2026-10-04: "stop trying to use gemini"). Make `gpt` the default generator wherever a default
   exists (`gold.mjs new`, `turnaround.mjs gen` / `repair`, `imagegen.mjs`), leave the gemini code path present but
   refuse it with a message naming the owner ruling unless `--allow-gemini` is passed. GPT is used ONLY through
   `scripts/v7/imagegen.mjs --gen gpt` (image generation) — never as a modelling, coding or review seat.
D. **HS stage without a gold model.** `run_pass.py` reads the gold baseline (`current_scores`, model-view tiles in
   the compare sheet), `gold.mjs hs` says "gold rounds first" unless build.py exists, BRIEF.md tells the builder to
   start from model.mjs. For a `pipeline: "direct"` subject: the pass must run and compose its sheet with no gold
   row; the gate is tris ≤ budget, topology 0, and ortho agree reported with the block-out's first full pass as the
   reference (no view more than .04 below the best earlier pass — a sanity check, see method.md); `gold.mjs hs`
   shows stages setup → build → review → polish → function → owner for it. Write `out/blender-hs/BUILD-DIRECT.md`
   (the builder brief for a direct subject: sources, method.md, block-out from facts, commands, limits, riggable
   rules for the class) and point the gold-hs-modeller agent file at it for direct subjects.
E. **Function stage for a handheld weapon.** `rig_pass.py` assumes ground contacts, mass, stability, a drive sim. Add
   `physics.mode: "handheld"` (no ground / stability / sim tests; mass + COM still estimated and reported) and the
   joint types a weapon needs, each with pivot and sweep tests like the existing ones: `trigger` (rotary, small arc),
   `slide` (prismatic: bolt, charging handle, pistol slide, pump fore-end), `magazine` (prismatic detach along the
   mag well axis, must clear the well over its travel), `barrel_spin` (continuous; gatling cluster), `cylinder`
   (rotary, indexed n chambers; revolver / revolver launcher), `hinge` (break-action, folding stock, bipod leg,
   feed cover), `selector` (rotary, small). Add `sockets` (named points with an axis, exported as empties and tested
   as stated): `muzzle` on the bore line, `ejection_port`, `grip_r`, `grip_l`, `sight_rear` / `sight_front` (the
   sight line clears the receiver), `optic_mount`, `magazine_well`. Clips: Fire (slide / bolt cycle + trigger),
   Reload (magazine out / in), SpinUp (barrel_spin), Open (hinge). Document in `scripts/hs/rig.md`; write the weapon
   section of `out/blender-hs/RIG-BRIEF.md`.
F. **Prove it on `assault_rifle`** end to end as far as S2 pass 2 + a rig smoke test:
   write its description (one paragraph: parts, colours, real size in metres, what is on the hidden flank),
   `gold.mjs new --class weapon --style fps --gen gpt`, the turnaround sheet with `--gen gpt`, registration, frame,
   concept camera; then build a block-out + one masses pass yourself (enough to show the pass, the compare sheet,
   the close-ups and the gate work with no gold), and run `rig_pass.py` on it with a minimal handheld rig (trigger +
   magazine + charging handle + muzzle socket) to show the harness path works. Open the images you generate: a
   concept or a view that is not the weapon described (wrong weapon, cropped, two objects, text) is regenerated
   (the stop rule in turnaround.mjs applies).
G. **Write the 10 descriptions** to `subjects/_weapons/<id>.txt` for the fan-out (ids fixed): `assault_rifle`,
   `grenade_launcher` (6-shot revolver type), `gatling_gun` (hand-carried rotary minigun with an ammo drum),
   `pump_shotgun`, `sniper_rifle` (bolt action, scope, bipod), `smg`, `pistol`, `rocket_launcher` (shoulder tube
   with a loaded rocket), `light_machine_gun` (belt box, bipod), `revolver`. One coherent family: same style, the
   same gunmetal / black polymer palette with one accent colour, real sizes. Tri budget 8000 each.
H. **One page**: `WORKFLOW-V10.md` (the consolidated workflow: stages, commands in order, gates, who decides what,
   limits) and the pointer in `.claude/skills/gold-model/SKILL.md` + `scripts/hs/README.md` + `scripts/v7/README.md`
   (add the missing `hs` line there too).

## Rules
- Never edit: `tools/CharacterStudioV2`, existing files under `refs/**`, `src/validate/limits.json`,
  `tools/BlindLoop/config*.json`, any `out/ref/gold/<s>/model*.mjs`. Never delete anything permanently, never
  `git clean`, no commits, no pushes.
- Other agents are running HS passes on the vehicle subjects right now: do not touch `out/blender-hs/<vehicle>/`;
  keep harness edits additive (new branches for `direct` / `handheld`, vehicle behaviour byte-for-byte the same);
  re-read a shared file immediately before editing it. After harness edits prove no regression: one vehicle pass
  into a scratch out-dir (`run_pass.py -- --subject apc_8x8 --pass 99 --out-dir <scratchpad>`) and one
  `rig_pass.py -- --subject jeep_gun --no-render --out-dir <scratchpad>` give the same numbers as before.
- Tests: do NOT run `scripts/v7/gold.test.mjs` (it overwrites live state files). Run only tests that are pure
  (`styles`, `newsubject`, `imagegen`, `turnaround`, `normalize-views`) and say which you ran.
- Image generation takes minutes per call; run at most 2 at a time.

## Report
What you changed (file list with one line each), the exact command sequence for one new weapon from description to
function stage (copy-pasteable, for the fan-out), what `assault_rifle` looks like now (paths of the concept, the four
views, the compare sheet, the rig sheet), regression results, and every place where the consolidated path is still
weaker than the vehicle path. Be explicit about anything you could not make work.
