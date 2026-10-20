# Hand-off — WF v10 weapons (paused 2026-10-05)

Owner asked: commit and push, pause, hand-off notes. All agents were stopped mid-run; files on disk are as they left them.

## The set (owner 2026-10-04 / 05)
- 10 war vehicles — DONE (look + function, all 10 rigs pass). `out/blender-hs/<vehicle>/`.
- 10 normal guns, style `fps`, descriptions `subjects/_weapons/<id>.txt`.
- 10 futuristic cartoon guns, style `scifi_toon`, descriptions `subjects/_scifi/<id>.txt`. Owner: must NOT copy any prop
  of the two adult-animation shows he named; original designs that feel like they belong there. Regenerate any concept
  that resembles a known prop.

Pipeline per weapon (`WORKFLOW-V10.md`): S1 setup → S2 look build (`out/blender-hs/BUILD-DIRECT.md`, `scripts/hs/method.md`)
→ S3 blind Fable review (`gold-hs-reviewer-fable`) → ONE polish → S4 function (`out/blender-hs/RIG-BRIEF.md`
"Handheld weapons"). Polish + function run as one `gold-hs-modeller` agent. `node scripts/v7/gold.mjs hs --subject <s>`
prints the stage and the next step.

## State when paused
| weapon | setup | look build | review | polish | function |
|---|---|---|---|---|---|
| assault_rifle | done | done (13 passes) | 6.0 | done | RIG PASS 21/21 — FINISHED |
| gatling_gun | done | done | 6.5 | STOPPED mid-run (passes 9–13 exist, a rig_stats exists, no POLISH.md) | redo check |
| grenade_launcher | done | done (8) | 6.5 | STOPPED early (nothing new on disk) | — |
| pump_shotgun | done | done (10) | 6 | STOPPED early | — |
| pistol | done | done (8) | STOPPED (no review file) | — | — |
| rocket_launcher | done | STOPPED at pass 7, no `--final` | — | — | — |
| sniper_rifle, smg, light_machine_gun, revolver | done | not started | — | — | — |
| ray_pistol … bubble_cannon (8 sci-fi) | files complete (concept, sheet, frame, concept camera) | not started | — | — | — |
| laser_smg | concept + sheet, registration unfinished | — | — | — | — |
| disintegrator | not started | — | — | — | — |

Sci-fi: only `refs/ray_pistol.png` was opened by the orchestrator. The other concepts and ALL sci-fi sheets have not
been looked at — open each before building (right gadget, one object, four consistent views, not a show prop).

## Resume
1. Stopped polish agents: re-launch with the same prompt, adding "continue from the files already in the folder; check
   build.py still runs and the last pass's gate before going on". For gatling_gun verify `stats.json` / `rig_stats.json`
   belong to the current build.py (`gold.mjs hs` shows STALE otherwise).
2. pistol: re-launch the Fable review. Decided: build stays centred on the bore plane (x = 0); do not flag the 2–3 mm
   registration offset.
3. rocket_launcher: re-launch the build ("continue from pass 7").
4. Builds for sniper_rifle (bolt + bipod legs separate), smg, light_machine_gun, revolver (cylinder indexed), then the
   sci-fi ten. Riggable parts per weapon: see the prompts' pattern in the finished subjects' FEATURES.md.
5. Finish sci-fi setup for laser_smg and disintegrator (GPT image generation only, one at a time).
6. At most 6 agents at once. Open every compare / rig sheet before sending it to the owner (SendUserFile).

## Rules that bit this session
- Commit with a narrow explicit path list: top-level key files only. `git add -f` of a whole `out/blender-hs/<s>/`
  folder pulls ~800 MB of per-pass scratch. Count the list before committing.
- A deletion of `out/ref/gold/jeep_gun/critique/r2-fable.json` is staged in the index: leave it, never commit it.
- No Gemini / agy. GPT only through `scripts/v7/imagegen.mjs --gen gpt` for images. Owner 2026-10-05 offered
  "GPT Sol 6.1 high" as a builder (`gpt-6.1-sol` via the Codex CLI `exec`), but the permission classifier blocks
  launching it; the owner must add a Bash permission rule first. Earlier GPT build test on vehicles went poorly.
- Image prompts: describe weapons as game props by shapes and colours; "rifle"-type wording was rejected once.
- Do not run `scripts/v7/gold.test.mjs`.

## Open owner calls
- assault_rifle: magazine straight (side drawing) vs curved (description); trigger-guard height; mass range 3–7 kg.
- gatling_gun: drum hung under a top bracket, flat faces front / rear (concept) vs side-facing with feed chute
  (description) — concept kept.
- Vehicles (older): jeep gun ring position, MBT front fenders, rocket truck 52° forward elevation, concept-camera
  misfit on bike and both helicopters (harness fix pending).
- 97+ local commits were ahead of `origin/main` when the push was requested — see the session's final message for
  whether the push happened.
