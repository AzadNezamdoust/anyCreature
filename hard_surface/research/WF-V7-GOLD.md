# The gold workflow — RATIONALE ONLY (v7 2026-09-26 → v8 2026-09-27; not instructions)

The procedure is the skill `D:\Git\checkout\.claude\skills\gold-model\SKILL.md`; the seats are `.claude/agents/gold-*.md`;
the rules are scripts — `scripts/v7/step.mjs` (KEEP / REVERT), `merge.mjs` (classes, evidence, STOP line), `doctor.mjs`
(the setup gate), `gold.mjs` (phases, briefs, ledger), `gold.config.json` (the numbers). This file keeps WHY the workflow
looks the way it does. The v8 decisions and their evidence: research/v7/WF-V8-PLAN.md, research/v7/WF-REVIEW-fable.md,
research/v7/WF-REVIEW-opus.md. The v7 text of this file is in git history (`git show 713c79f:tools/LLMModeling/research/WF-V7-GOLD.md`).

## Why gold models first (owner, 2026-09-26)
After the v6 bus experiment the owner said "I set effort to max, do your best" — meaning the result shown was NOT
acceptable: a sharp-edged box without the bus's rounded roof, dull mustard colour, stick mirrors, a small borderless stop
sign, thin frames. The best model at that point was the pickup Opus built by hand while LOOKING at renders (IoU 0.976);
every template + FIT model since scored well on numbers and looked worse. Quality first; the workflow is distilled from
models that look right.

## Why these seats
- The MODELLER builds directly in the kernel and decides shape and structure (the FIT only ever refined numbers; no v7
  ledger shows it used). v7 ran it as an unpinned general-purpose agent: its effort followed the session and the
  60-turn opus-worker cap was hit three times. v8 pins it (gold-modeller: Opus 5.5, high, 120 turns) and gives it one
  command per iteration (step.mjs), so the five-condition KEEP rule cannot be half-applied at any orchestrator effort.
- Two CRITICS, blind, Fable 5.1 + Opus 5.5 (owner 2026-09-27): single critics flip-flop between rounds (pickup cab rake
  0.15 → 0.12 → plumb; bus tyres "bigger" → R 0.53 → 0.46) and the two seats caught each other's wrong MAJORs. They took
  25–75 min at 25–115 calls when they wrote their own measuring scripts and crops; v8 pins them (40 turns), hands them the
  numbers in the brief and makes their output JSON whose evidence the merge checks.
- The ORCHESTRATOR did judgment by hand in v7 — 15 merges of 25–57 lines, lone-MAJOR measurements, ledger prose, commit
  selection — exactly what degrades first at medium effort. v8 moves all of it into gold.mjs + merge.mjs: a MEDIUM
  orchestrator gets the HIGH result because it only runs commands.
- The AUDITOR exists because reference disagreements surfaced one critic item per round (3–8 `drift:` lines per ledger,
  the tractor's four rounds ending on "which proportions") and three eye fixes (enclosedFg, a rear `shift`, fgMax) were
  detectable before round 1. The owner still caught what the numbers cannot (the ambulance's rear doors on its flank, the
  garbage truck's open hopper side) → the semantic check is the auditor's task 0.

## Why the merge classes
A = both seats flagged it, B = one seat MAJOR, C = one seat MINOR, CONFLICT = opposite directions or amounts > 2× apart
(settled by a variants table: the numbers decide, not the louder critic), X = a structural conflict without a knob (build
both), TRIED / PARKED = the ledger's attempts (twice in one direction → the owner: the Blind Loop stall rule, K = 2),
DECIDED = settled facts reopened only with a new measurement. A MAJOR without machine-checkable evidence merges as
MINOR: the bus's "near-black arch" MAJOR sampled the tyre, and the "perspective" MAJORs were refuted by
research/v7/EYES-EXPERIMENT.md (the concepts are orthographic: verticals plumb within 0.01°, a perspective camera gains
≤ 0.001 IoU on 4 of 5 subjects). The truck-tandem and tractor-proportion tables of v7 round 4 settled real disagreements —
v8 runs such tables in the merge of the round where the CONFLICT first appears.

## Why drift is a rect with `decides`
A generated turnaround can disagree with the concept (pickup front / rear, tractor fenders, truck cab gap, taxi
proportions); the concept wins by default, so the ortho IoU there can only fall. The concept is a drawing too: where its
own reading is inconsistent (near vs far flank, fanning parallel edges, a tandem drawn overlapping, hub centres vs tyre
ellipses, a nose shifted sideways) the orthographic turnaround decides — taxi round 2 moved its rear axle to the
concept's distorted flank and both round-2 critics reversed it. v7 kept these as prose `drift:` lines with an open-ended
KEEP exception (tractor round 4 kept a −.127 side loss "in drift regions"). v8: a rect in the image's own px, `decides`
naming the image that is right there, ≤ 5 % of a view's foreground (a bigger disagreement is a setup ruling: regenerate),
masked as don't-care in the agree IoU; changed only at a round boundary and only owner-approved.

## Why these eyes, and why they are frozen during a round
One sheet (references / the model in the same views in true cel colours / outline overlays with IoU and float-clip
checks) plus one native-resolution page per view — the sheet alone is too small for lamps, mirrors, seams. v8 adds the
blob table (the biggest silhouette differences as numbers, with the owning part) so an iteration reads five lines instead
of six images. In v7 the eyes changed under the modellers three times (enclosedFg at round 2, the truck's rear `shift` at
round 3, a fgMax bug that erased the truck's white body), each a re-baseline and a round aimed at a registration
artefact: hence the eyes hash (close refuses a round whose eyes changed) and eyes-check.

## Why the bar is a number and the run has a cap
"Every view reads as the concept at a glance" was a critic sentence and "≥ 0.97" was global although four of five
subjects could not reach it on drifted views; nothing computed whether a round was done. v8: agree ≥ 0.97 in every view
(the drift rects masked), checked by the merge's STOP line with the gate. All five v7 subjects ended on the 4-round cap;
round 4 moved ≤ .004 on the polish subjects → cap 3 (build ≤ 100 calls, list ≤ 60, polish ≤ 40, defaults pending the
owner), no critic review after the last round, a structural item still open after review 2 goes to the owner packet.

## After gold (not done yet)
Distil each gold module's structure into its class template / helpers (the parameters become KNOBS), rerun the v6 loop
with the fake seat → it must reproduce gold within the bar; then blind Luna + Gemini Medium runs; then delete machinery
the distilled pipeline no longer uses (ablation first).
