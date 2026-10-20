> SUPERSEDED (owner 2026-10-09): written by a GPT session; its later single-image route produced models the owner rejected. Authority is WORKFLOW-V10.md + HANDOFF.md.

# 30-model workflow campaign — 2026-10-05

## Confirmed goal
Complete the three sets of ten (war vehicles, normal guns, original futuristic cartoon guns) through the existing coded Blender workflow. Examine every model visually, review its details, polish once after independent review, and validate its moving parts and exported clips. Use the evidence from all three sets to evaluate and improve the workflow. The owner confirmed this scope in the current chat; the app goal API cannot replace an unfinished goal text, so this is the authoritative task scope. Do not declare the goal complete before all 30 and the resulting workflow review are verified.

## Recovery
Original milestone: `llmmodeling-wf-v10-milestone-2026-10-05` → `586140e`. It predates the handoff-only commit. New resume checkpoint: `llmmodeling-wf-v10-resume-2026-10-05` → `161b60f`. Neither HEAD nor the shared index is moved. Current final build/rig artifacts are copied under `out/checkpoints/2026-10-05-wf-v10-pre-30/files/`; `manifest.json` lists 311 files (50,563,255 bytes), each SHA-256 verified against its source. The staged jeep critique deletion remains staged and must never enter a commit. Preserve all existing references, used style keys, gold models, and unrelated project work.

## Acceptance per model
1. Setup: the concept and installed four-view sheet are opened and examined; intended design and originality are checked. Frozen references stay unchanged. Record cross-view disagreements and prior owner decisions.
2. Look: registered metres, major masses first, complete feature inventory, one object per moving part, real openings and clearances. At least six substantive render-compare passes overall (resume previous passes). Open the concept and four-view comparisons each round and detail crops at the keeper. Do not add meaningless passes to meet a count.
3. Gates: ≤8000 triangles, all topology errors zero, no ortho agree drop beyond the existing .04 tolerance. Concept camera fit and outline scores are reported and cannot approve likeness.
4. Review: independent blind review without modeller reports; measure interior part shapes, counts, placement, colours, seams and thickness. Keep a score and prioritized findings. Apply one polish, with every finding fixed or answered. Taste decisions remain owner items. The owner replaced Claude seats on 2026-10-05: use pinned gpt-6.1-sol builders and gpt-6-astra blind reviewers. Prefer native collaboration; when native thread capacity is exhausted, use ephemeral Codex CLI workers with subject-only write sandboxes and fresh source/image-only read-only review intakes. Record the actual model header, process identity and intake hashes. The workflow contracts still apply; legacy model names and Claude launch requirements are superseded.
5. Function: fresh rig tests, pivots, sweep clearance, sockets, mass, unchanged look, exported joint hierarchy and clips. Open and examine the rig sheet, including moving-part extreme poses. Prior JSON pass flags are baseline evidence, not current completion.
6. Delivery: current build source, feature inventory, review, polish response, fresh stats, compare sheet, rig description, rig sheet, rig stats, and rigged GLB. Owner acceptance is separate from our verified-ready state.

## Campaign order
- Preserve/check the baseline; inspect all available sci-fi concepts and sheets before building. Finish laser_smg registration and disintegrator setup through GPT image generation.
- Resume interrupted normal guns, then four unbuilt normal guns, then ten sci-fi builds. The owner requested an army of 10+ workers: parallelize source/spec/code preparation and independent review while keeping subject writes isolated. Limit heavy Blender processes to three, with a root-owned per-subject render permit; worker count and rendering capacity are separate. Never assign two simultaneous writers to one subject.
- Re-examine and revalidate the ten existing vehicles; do not rebuild a finished vehicle gratuitously.
- Record per-subject actual time, passes, likeness findings, disagreements, rig failures, and harness issues as observed.
- After all 30: compare evidence across the three classes, distinguish setup/camera errors from modelling/detail/rig errors, prioritize recurring failures, implement justified workflow improvements additively, and validate them on the affected models plus vehicle and weapon regression pilots. Never promote unrelated deferred work.
- During the campaign, demonstrated local setup/status/motion-evidence defects may be repaired and verified against the existing models. These are interim fixes; final workflow conclusions and completion still require all 30.
- Produce a 30-model review matrix and contact sheets, an evidence-based workflow assessment, the updated workflow instructions, and reproducible validation receipts. No push without a new owner request.

## Baseline inventory (not completion)
| Set | Subject | Final look pass | Tris | Prior review | Prior rig | Next work |
|---|---|---:|---:|---|---|---|
| vehicles | aa_tank | 50 | 7924 | present | 58/58 | examine + fresh verification |
| vehicles | apc_8x8 | 20 | 7988 | present | 56/56 | examine + fresh verification |
| vehicles | attack_heli | 19 | 5680 | present | 16/16 | examine + fresh verification |
| vehicles | combat_bike | 28 | 7228 | present | 21/21 | examine + fresh verification |
| vehicles | jeep_gun | 25 | 7984 | present | 36/36 | examine + fresh verification |
| vehicles | light_tank | 23 | 7948 | present | 52/52 | examine + fresh verification |
| vehicles | main_battle_tank | 102 | 7780 | present | 68/68 | examine + fresh verification |
| vehicles | rocket_truck | 30 | 7978 | present | 44/44 | examine + fresh verification |
| vehicles | supply_truck | 20 | 7924 | present | 40/40 | examine + fresh verification |
| vehicles | transport_heli | 24 | 4680 | present | 34/34 | examine + fresh verification |
| weapons | assault_rifle | 13 | 6048 | present | 21/21 | fresh verification |
| weapons | gatling_gun | 13 | 5804 | present | 14/14 | resume polish + rig |
| weapons | grenade_launcher | 8 | 5696 | present | missing | resume polish + rig |
| weapons | light_machine_gun | — | — | missing | missing | build |
| weapons | pistol | 8 | 2734 | missing | missing | review |
| weapons | pump_shotgun | 10 | 2648 | present | missing | resume polish + rig |
| weapons | revolver | — | — | missing | missing | build |
| weapons | rocket_launcher | — | — | missing | missing | resume build |
| weapons | smg | — | — | missing | missing | build |
| weapons | sniper_rifle | — | — | missing | missing | build |
| scifi | bubble_cannon | — | — | missing | missing | build |
| scifi | disintegrator | — | — | missing | missing | setup |
| scifi | freeze_ray | — | — | missing | missing | build |
| scifi | goo_blaster | — | — | missing | missing | build |
| scifi | gravity_gun | — | — | missing | missing | build |
| scifi | laser_smg | — | — | missing | missing | build |
| scifi | plasma_rifle | — | — | missing | missing | build |
| scifi | ray_pistol | — | — | missing | missing | build |
| scifi | shrink_ray | — | — | missing | missing | build |
| scifi | tesla_blaster | — | — | missing | missing | build |
