# WORKFLOW v10 — the consolidated direct pipeline (2026-10-04)

One pipeline for a `pipeline: "direct"` subject (class `weapon`; `subjects/<s>/subject.json`): description → concept →
turnaround → registration → Blender build → blind review + one polish → function (rig). No JS-kernel model, no critics,
no auditor agent, no gold state. The vehicle subjects keep the v8 gold rounds + v9 HS stage unchanged
(`.claude/skills/gold-model/SKILL.md`). Why: research/WF-V9-HS.md — the look is decided in the HS stage by
`scripts/hs/method.md`; the gold rounds only supplied metres and a silhouette baseline, which a direct subject takes
from its stated size and its own block-out pass. Engineer brief + what is still weaker: research/WF-V10-BRIEF.md,
"Limits" below.

All commands from `D:\Git\anyCreature\hard_surface`. `node scripts/v7/gold.mjs hs --subject <s>` prints the stage and
the NEXT step at any time (setup → build → review → polish → function → owner).

## Agent routing (owner 2026-10-09: restored after the GPT R4 detour)

Claude Code seats, as in the original v10: builds, polishes and rigs: Opus 5.5 for production quality (`gold-hs-modeller`, owner 2026-10-10); while the workflow itself is being developed, test runs build / polish / rig on Haiku 5.5 (general-purpose + model haiku, body of gold-hs-modeller.md) so workflow weaknesses show up cheaply; the blind review runs on Opus 5.5 (general-purpose + model opus, prompt = the body of `.claude/agents/gold-hs-reviewer-fable.md`); Fable only with the owner's explicit yes (owner 2026-10-09: credits). GPT only generates images through `scripts/v7/imagegen.mjs --gen gpt`. Between 2026-10-05 and 10-09 a GPT session ran this workflow with GPT seats (the 20 weapons in `out/blender-hs/` come from that and are good), then left it for a single-image route (`out/weapon-grounded-r4-2026-10-07/`, `WORKFLOW-V11.md`, `RUN-30-MODELS.md`); the owner judged those models bad (2026-10-09). Those files are history, not authority. At most 5 agents at once.

## Stages

| stage | does | tools | who |
|---|---|---|---|
| S1 setup | description → concept → facts → 2 × 2 turnaround sheet → camera + frame → registration; **WF v11:** + `spec.in.json` rects → `spec.json` → frozen spec-proxy camera → `--resolve hero` → re-freeze → generated block-out | `gold.mjs new`, `turnaround.mjs`, `solve-camera-hull.mjs`, `hull.mjs`, `dump_frame.mjs`, `dump_concept_cam.mjs`; v11: `spec_build.mjs`, `solve_persp_cam.py --proxy spec`, `spec_blockout.py` | orchestrator (looks at every image) |
| S2 look | Blender build from the sources by `scripts/hs/method.md`: block-out from the size → major masses → feature inventory → details; **WF v11:** pass 1 = the generated block-out, masses to SPEC / BANDS green with the `--fix` latch and rollback, then detail | `run_pass.py`, `closeups.py`; v11 adds `score/specgate.mjs`, `score/bands.mjs`, `spec_lint.py` | Agent `gold-hs-modeller`, brief `out/blender-hs/BUILD-DIRECT.md` |
| S3 review | blind detail review, then ONE polish (K = 1) | — | Opus reviewer (body of `gold-hs-reviewer-fable.md`), then `gold-hs-modeller` mode polish |
| S4 function | `rig.json` (handheld) + tests + rigged glb with sockets and clips | `rig_pass.py` | Agent `gold-hs-modeller`, brief `out/blender-hs/RIG-BRIEF.md` "Handheld weapons" |
| owner | `compare.png` + `rig_sheet.png` (+ `POLISH.md` owner items) | — | the owner |

## Commands in order (one weapon; `<s>` = the id, description in `subjects/_weapons/<s>.txt`)

```powershell
# S1 — setup
node scripts/v7/gold.mjs new --subject <s> --class weapon --style fps --gen gpt --noun "<noun>" --desc-file subjects/_weapons/<s>.txt
#   LOOK at refs/<s>.png (the weapon described, whole, one object, no text / hands). Wrong -> move refs/<s>.png,
#   refs/<s>.README.md, subjects/<s>, out/concept/<s> aside and run `new` again.
#   EDIT subjects/<s>/turnaround/facts.json: sides / asymmetric / faces (per view: what the muzzle-on, butt-on and top
#   views show). Add an accent colour under 2 % to views.json families.table.body (measure.mjs sample --image refs/<s>.png x,y,w,h).
node scripts/v7/hull.mjs --subject <s> --write-frame --from facts
node scripts/v7/turnaround.mjs gen --subject <s> --out out/turnaround/<s> --gen gpt
#   LOOK at out/turnaround/<s>/current/*.png (four views of THIS weapon, right flank / hidden parts where facts say)
node scripts/v7/turnaround.mjs status --subject <s> --dir out/turnaround/<s>
node scripts/v7/turnaround.mjs repair --subject <s> --dir out/turnaround/<s> --view <v> --gen gpt      # only while a target is missed; the stop rule: 3 sets / 3 repairs per view
node scripts/v7/turnaround.mjs install --subject <s> --dir out/turnaround/<s>
node scripts/v7/boreplane.mjs --subject <s> [--write]          # S1 fix 2026-10-10: x = 0 on the bore plane (views.json per-view shift) when facts.asymmetric has a protruding part; read-only without --write
node scripts/v7/solve-camera-hull.mjs --subject <s>            # the concept camera (theta, phi) from the installed views' hull
node scripts/v7/hull.mjs --subject <s> --write-frame --frame-refine off   # scale / offset: the hull bbox fitted to the concept box (default "iou" = the old IoU refine: 2.8..9.3 % box error on 6 weapons, out/score/s1fix/box_stored.json)
node scripts/v7/conceptbox.mjs --subject <s>                   # after a build: model box vs concept fg box through the frame (> 2 % = flagged)
node scripts/v7/hull.mjs --subject <s> --aniso                 # read: residuals, viewOnly, concept IoU, aspect
node scripts/hs/dump_frame.mjs --subject <s>; node scripts/hs/dump_concept_cam.mjs --subject <s>
#   PRECISION (2026-10-10, research/PRECISION-VEHICLE-VS-DIRECT.md): order hero -> parts.json -> turnaround -> doctor
#   --direct -> camera --from-parts -> block-out -> HERO gate -> build. The orchestrator writes subjects/<s>/parts.json
#   from the hero (BUILD-DIRECT.md "Measured part list") before the build.
node scripts/v7/doctor.mjs --subject <s> --direct               # hull + hero-size rows; BLOCK -> turnaround.mjs repair (stop rule), never a build; an uncleared BLOCK goes to the owner as one line
#   after the pass-1 block-out (run with --dump-part-boxes): replace a hand-set camera with the part-centre fit
node scripts/v7/solve-camera-hull.mjs --subject <s> --from-parts --boxes out/blender-hs/<s>/pass1_parts.json [--write]
node scripts/v7/gold.mjs hs --subject <s>                      # -> stage build

# S1 (WF v11, research/WORKFLOW-V11.md; after registration): the measured spec + the frozen camera + the block-out
node scripts/hs/spec_build.mjs --subject <s>                                 # subjects/<s>/spec.in.json (orchestrator's rects) -> spec.json
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 --python scripts/hs/solve_persp_cam.py -- --subject <s> --proxy spec --cam out/blender-hs/<s>/concept_cam.ortho-v4.json
node scripts/hs/spec_build.mjs --subject <s> --resolve hero                  # contested dims through the frozen camera; then re-run the solve (re-freeze)
python scripts/hs/spec_blockout.py --subject <s>                             # pass-1 build.py (one primitive per spec part)

# S2 — look (the builder agent; brief out/blender-hs/BUILD-DIRECT.md). WF v11: pass 2+ needs --fix <failing keys> (--fix detail after 0)
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 --python scripts/hs/run_pass.py -- --subject <s> --pass N      # --final on the keeper; --hero gate when parts.json exists
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 --python scripts/hs/closeups.py -- --subject <s>

# S3 — review + polish: Opus reviewer (general-purpose, model opus, body of gold-hs-reviewer-fable.md) "subject: <s>" -> review_fable.md; Agent gold-hs-modeller
#   "subject: <s>, mode: polish, pipeline: direct" -> POLISH.md + a new --final

# S4 — function (brief out/blender-hs/RIG-BRIEF.md "Handheld weapons"; contract scripts/hs/rig.md)
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 --python scripts/hs/rig_pass.py -- --subject <s>
```

## Gates
- **S1** (turnaround.mjs status; gold.config.json setupHull): every viewOnly ≤ 3 %, residuals within ± 3 %, |aspect| ≤ 3 %,
  conceptOnlyBlob ≤ 2.5 %. For a weapon the two concept numbers depend on the fitted camera: read them AFTER
  `solve-camera-hull.mjs` + `--write-frame` (`hull.mjs --aniso`), not from the first `gen` table (fixed isometric). The
  stop rule (3 failed sets / 3 failed repairs per view) ends regeneration; what remains is recorded in the install note.
  A first subject can now diagnose camera fit before install with `solve-camera-hull.mjs --subject <s>
  --views-dir out/turnaround/<s>/current --dry`; it uses the candidate table without requiring installed images.
  This diagnostic does not update camera/frame or reset the regeneration cap; the installed-set chain still follows.
  The image check is the orchestrator's eyes: a concept or a view that is not the weapon described is regenerated.
- **S2** (`stats.json gate`): tris ≤ 8000, topology 0, no ortho view more than .04 below the best earlier non-block-out pass (`run_pass.py --gate-ref mature`, the default for direct subjects: the first pass and passes under 5 % of the tri budget are never a reference; see BUILD-DIRECT.md). The
  concept view is a look reference, not gated. With `subjects/<s>/parts.json`: `--hero gate` adds HERO PASS
  (`scripts/hs/score/heroratio.mjs`: every hull-relative part ratio within 10 % of the hero, counts equal); pass 2 must
  pass it before any detail. The owner gate stays ONE (compare.png + showcase at the end).
- **S3**: the review is blind (no modeller report); every review item fixed or answered in `POLISH.md`; one polish round.
  Direct-subject status requires that response file. Newer passes alone mean the polish started; resume the same K = 1
  round after interruption instead of declaring it complete or starting another.
- **S4** (`rig_stats.json`): every `pivot:` / `sweep:` / `socket:` test, `mass` in the stated range, `regroup`, `look`
  (identical to the final look pass), `export` (joint + socket nodes, clips).
  Rig sheet (2026-10-10): a handheld rotary joint about the bore axis (cylinder, head index) picks its tile view by
  projected motion x visible share (`rig_pose_manifest.json bore_axis_views`); the muzzle-end ortho `[MUZZLE]` is a candidate.
  Missing, failed, malformed or older-than-input rig evidence stays at function. Open `rig_sheet.png` and inspect
  `rig_pose_manifest.json`: vehicle hinge limits have side/rear-quarter views; handheld framing includes the union
  of requested poses. Manual trigger/slide limits are diagnostic poses, separate from actual Fire clips.
  Running angular clips must pass actual BIN winding/phase/run_pose validation, not only node/name checks.
  Verify actual handheld clip key, midpoint and combined poses against collision checks and visible motion.
  `muzzle.parts`, when declared, selects the muzzle assembly for the front check; unknown names fail.
  Hierarchy construction preserves original world transforms/local origins and isolates shared meshes.

## Who decides what
- The owner: the list of subjects and their descriptions, the style, budgets and gate numbers, the generator
  (2026-10-04: GPT only — `--gen gemini` is refused without `--allow-gemini`), the final accept.
- The orchestrator: runs S1 itself, looks at every generated image, launches the seats `gold.mjs hs` names, relays
  reports and spot-checks independent findings against source/render images. It owns shared harness fixes and final
  evidence receipts, while the assigned builder owns build changes and the owner retains final taste decisions.
- The builder: the model (method.md: what makes sense, not line-to-line; decided facts hold).
- The reviewer (Opus 5.5, blind): the likeness verdict and the item list.

## Limits
- Image generation uses `scripts/v7/imagegen.mjs --gen gpt`, at most two generations at a time. Modeling and review
  use the Claude seats above; GPT is never a modelling, coding or review seat.
- The image generator's safety system can reject a weapon TURNAROUND prompt (assault_rifle attempt-0: http 400,
  `safety_violations=[illicit]`, on the concept paragraph verbatim; the concept itself passed). What worked once:
  `facts.json` noun / description / faces written as a fictional low-poly game prop described by shapes and colours
  (no mechanism names). A rejection counts as a failed set under the stop rule. If the reworded sheet is rejected too,
  stop and hand to the owner — do not keep rephrasing.
- Never edit: an existing `refs/**` file (a TARGET is frozen), `src/validate/limits.json`, the eyes files
  (`scripts/registered.mjs`, `scripts/project.mjs`, `scripts/v6/*.mjs`, `scripts/subject.mjs`: a round of a vehicle
  subject hashes them), a used key of `scripts/v7/styles.json`. Do not run `scripts/v7/gold.test.mjs` on a live tree.
- No gold commands for a direct subject (`status`, `doctor`, `brief`, `close`, `merge`, `commit`, `note` need a gold
  state it does not have). Provenance lives in `refs/<s>.README.md`, `out/turnaround/<s>/state.json`,
  `subjects/<s>/turnaround/README.md`, the `passN_*` files and `rig_stats.json`.
- Weaker than the vehicle path (2026-10-04): no setup auditor / doctor / drift rects (a view error is caught only by
  the orchestrator's look and the builder's method.md step 3); the concept camera is a 2-angle hull fit, not a solved
  one (assault_rifle hull IoU .80); ONE colour family (no per-colour zone scores); the gate has no independent
  baseline (the block-out is its own reference); `barrel_spin` has current Gatling15/15 evidence, and
  weapon hinges have sniper23/23 and launcher17/18 (mass fails) evidence. Revolver cylinder proof is pending.

## Proof
`assault_rifle` (freshly verified 2026-10-05): final pass 13, 6048 tris, original blind review plus completed one-polish
response, `closeups/`, and rig 21/21. Current files are under `out/blender-hs/assault_rifle/`. It is a complete technical
workflow example awaiting separate owner taste decisions; the old 756-triangle block-out is historical pass evidence.

## Campaign implementation notes (2026-10-05)

Call `bpy.context.view_layer.update()` before returning the build so topology checks see current transforms.
After Boolean material operations, resolve the actual material slot index and fill any empty slot with a valid base
material; a passing silhouette cannot reveal an inverted recess colour. Keep source-conflict decisions and mass
assumptions explicit. Campaign fix evidence and unresolved limitations: `out/campaign-30/WORKFLOW-FIXES.md`.

## Polygon surface requirement (owner 2026-10-05)

Body panels and shells must be filled polygon meshes; do not substitute tubes/bars for their surfaces. Actual
source-required barrels, rods, guards and window frames are separate modeled features. Standard comparison
renders add Freestyle silhouettes/creases/marked edges at1.5px; that ink is presentation and is not exported in GLB.
Inspect a no-outline colour/clay render of the actual exported GLB as additional evidence, using
`out/campaign-30/surface_preview.py`. Diagnostic outputs stay under surface-previews and never replace
registered source/compare images or change geometry, cameras used for scoring, or gates. The receipt hashes the
read-only input and counts exported faces; image/source inspection still decides whether bars are justified.

## Items-30 production additions (2026-10-11, research/PLAN-ITEMS30.md)
- Pass time is 13-67 s; run passes in the foreground. Owner pairs: #1 after the build and #2 after the polish
  (`py scripts/hs/pair.py --subject <s> --stage build|polish`: hero | lit hero-cam render, 2048x1024), #3 after the rig
  poses (`py scripts/hs/anim_gifs.py --subject <s>`).
- Build gate adds `node scripts/hs/score/chunky.mjs --subject <s>` (BUILD-DIRECT.md "Chunky detail"); reviewers get the heroratio
  table first, then chunky + FPS rows (agents `gold-hs-reviewer-fable` / `gold-hs-reviewer-opus`).
- Escalation triggers and the archive-old-builds rule: BUILD-DIRECT.md "Escalation and old builds". Builders:
  `gold-hs-modeller-sonnet` (class A), `gold-hs-modeller` (Opus, class B).
- Function stage: `research/FUNCTION-SPEC-BRIEF.md` (spec states the end pose first). rig_pass.py adds the `pose:<id>` expect
  test, the hero-led `look` rule for direct subjects with parts.json, and the optional `mass_game_kg` (reported next to the
  real mass; ranges never widened). `gold.mjs hs` prints the stage label per item.
