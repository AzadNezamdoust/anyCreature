# v7 gold workflow — review (Opus 5.5 seat, blind; 2026-09-27)

This review covers the workflow, not any one model. I read research/WF-V7-GOLD.md and research/v7/{RUNBOOK,MODELLER,CRITIC,EYES-EXPERIMENT}.md. I also read scripts/v6/README.md, scripts/v7/README.md, scripts/v6/view.mjs, scripts/v7/*.mjs and the judge / ortho / registered code they call. The run itself I read from the five LEDGER.md files, every critique and merged list, and `git log e4055be..HEAD -- .`.

I also measured four things for this review (commands in the appendix):
- the registration residuals of all ten subjects;
- the validator chain on the five gold models;
- render, gate and variant timings;
- the size of the page images.

research/v7/WF-REVIEW-fable.md was not opened.

## Summary

The loop makes good models, but both their quality and the loop's cost depend on the orchestrator's judgment:
- the finish line cannot be measured;
- critics find reference disagreements one round at a time;
- merges and rulings are written by hand;
- the seats run at whatever effort the orchestrating session has.

A medium-effort orchestrator would break the loop at exactly these points. The fix moves judgment into pinned seats and deterministic scripts:
- **Agent definitions** that pin each seat's model, effort and turn cap.
- **Drift stored as bounded don't-care regions.** "IoU ≥ 0.97 where the references agree" then becomes a number.
- **A setup doctor that runs before round 1.** On the gold subjects it flags 4 of 5 exactly where the ledgers later logged drift or eye fixes. It blocks all 5 queued subjects today.
- **One tool call per modeller iteration.**
- **Structured critiques** whose evidence a script checks and merges.
- **A shorter run:** at most 3 modeller rounds and 2 reviews, with a mechanical stop.

Expected effect:
- about half the agent runs per model;
- tool calls per model capped at about 340 by the budgets (300–1 800 as run);
- no hand merges and no mid-project eye fixes;
- the same seats at the same effort, whatever effort the orchestrator runs at.

## 1. Failure modes and costs

**The run in numbers:**
- 5 models and 20 modeller rounds.
- 37 critic launches: 27 in rounds 1–3, and 10 after the last round, of which 9 were killed by the weekly limit.
- 12 hand merges and 5 mid-project eye or tool fixes.
- About 8 h of wall time (commit 5fca95b at 22:56 to 5a45518 at 07:08).

No subject stopped on the quality bar. All five stopped on the 4-round cap.

### F1. The finish line cannot be measured, and drift has no bound

This decides how many rounds run, so it is the largest cost.
- **The bar is not computable.** WF-V7-GOLD.md:78-81 sets per-view IoU ≥ 0.97, and MODELLER.md:4-6 drops "where the references agree" altogether. Which pixels agree exists only as prose `drift:` lines, so no seat and no script can say whether the bar is met.
- **No subject reached it.** The lowest raw IoU per subject at the end:
  - bus: .942 (rear);
  - pickup: .864 (front);
  - truck: .923 (front);
  - tractor: .766 (side);
  - taxi: .873 (top).

  Every run ended on the round cap: school_bus/LEDGER.md:12, pickup:14, delivery_truck:21, tractor:15, taxi:15.
- **The drift exception is open-ended.** The KEEP exception for drift regions (MODELLER.md:32-35) has no limit. Tractor round 4 kept a variant that cost the side view −.127 "in drift regions" (tractor/LEDGER.md:13). The run ended on an owner call about which proportions to follow (:15).

### F2. Reference disagreements surface late, one critic item at a time

This produces flip-flops.
- **Drift was found in every round.** `drift:` lines were added in every round: pickup LEDGER:5, 6, 9, 11; delivery_truck:4, 5, 9, 13, 15, 20; tractor:5, 8, 10, 14; taxi:3, 8, 11, 14. The setup audit exists only on paper: RUNBOOK.md:15-16 was committed in f996811, near the end of the run, and was never run on these five.
- **The setup residuals were already out of band** (measured now). The contract already computes registration residuals (scripts/v6/ortho.mjs:226-233) and states a ±3 % band (scripts/v6/README.md:22-24). Three subjects were outside it before round 1:
  - taxi: W front +6.8 %, top −9.3 %;
  - truck: W rear +7.4 %, fixed in round 3 as a `shift` (LEDGER:16);
  - tractor: W rear −6.8 %.

  The pickup's overall bbox, which is only reported, was off by up to 13 % (top +13.3 %, rear −9.0 %). The bus, the steadiest subject, is within ±0.5 %.
- **Flip-flops, each costing a modeller round-trip:**
  - pickup cab rake: 0.15 → 0.12 → 0 (pickup LEDGER:3, 4, 10);
  - bus tyres: "bigger" → R 0.53 → 0.46 (school_bus LEDGER:3, 4, 7);
  - bus marker lens: amber → orange (school_bus/critique/r2-merged.md:43-44);
  - taxi rear axle: moved to the concept's distorted flank in round 2 and moved back in round 3, together with paneZ (taxi LEDGER:6, 9, 10; taxi/critique/r2-merged.md:3-5);
  - taxi sign taper: widened in round 2, narrowed in round 3 (taxi/critique/r3-merged.md:9-15);
  - truck tandem: moved in all four rounds (delivery_truck LEDGER:7-8, 11, 14, 18-19).
- **The next batch is already out of band:**
  - forklift: W rear +9.6 %, front −6.0 %;
  - garbage_truck: W front −9.1 %, top +9.1 %; Wbbox −15.7 / +16.6 %;
  - ambulance: W top +5.9 %;
  - fire_truck: W top −5.0 %;
  - icecream_van: W top +4.8 %.

### F3. Judgment lives in the orchestrator

It cannot be reproduced at medium effort.
- **Merges are hand-applied rules** (WF-V7-GOLD.md:19-27): 12 lists, about 137 items (47 A, 10 B, 17 CONFLICT, 62 C, 1 rejected). Several merges are analyses in their own right:
  - delivery_truck/critique/r2-merged.md:26-37 is a joint cab solve;
  - tractor/critique/r3-merged.md:5-19;
  - school_bus/critique/r3-merged.md:5-9 is a rejection the orchestrator measured.
- **Open questions stayed open.** Questions the orchestrator owned were not acted on: delivery_truck LEDGER:10 and 17, tractor:11. The proportion question parked in round 3 became the round-4 fight.
- **Critic output passed through the orchestrator.** The orchestrator transcribed one critic's output (delivery_truck/critique/r1-fable.md:1).

### F4. The seats are not pinned

- **Effort follows the session.** The modeller is launched as `general-purpose` with the alias `opus` (RUNBOOK.md:5-6), and the critics the same way. An unpinned seat takes the session's effort: the workflow docs say that an omitted effort "inherits the session effort", and nothing in RUNBOOK sets it.
  - The session that produced gold ran at max (WF-V7-GOLD.md:3).
  - A medium-effort orchestrator would run the modeller and critics at medium without anyone noticing.
- **The one pinned type hit its cap.** opus-worker stopped at its 60-turn cap three times (WF-V7-GOLD.md:32-33). Each needed a SendMessage recovery (RUNBOOK.md:20).

### F5. Each KEEP decision costs 4–6 tool calls and about 9 k image tokens

- **The loop in MODELLER.md:29-38** is: render, look, check six KEEP conditions with three commands (view.mjs, check-module, `inspect chain`), then copy a snapshot.
- **Compute is not the cost.** view.mjs --zoom takes 4.8 s, check-module 0.6 s, the chain 1.9 s.
- **Agent turns and images are the cost.** The sheet and the five pages are 1.2–1.9 k tokens each, about 9 k per full look, and they stay in context. Modeller rounds took 30–235 calls.
- **Modellers wrote their own tools** before scripts/v7 existed: school_bus/tools has 23 files and delivery_truck/tools has 19.

### F6. Critics are expensive, repeat each other's measurements, and are sometimes wrong

- **Cost.** A run took 25–75 min and 60–115 calls before the ≈30-call budget (WF-V7-GOLD.md:34-35), and 25 or more after it. One run wrote 63 crop files (tractor/critique/r2-opus/).
- **Two wrong claims were caught only by orchestrator work:**
  - The bus "near-black arch" sampled the tyre (school_bus/critique/r3-fable.md:2 → r3-merged.md:5-9).
  - The "perspective" claim (taxi LEDGER:4, delivery_truck:10) needed an experiment to refute (EYES-EXPERIMENT.md:8-22). The refuted claim still sits in the taxi module header (out/ref/gold/taxi/model.mjs:16-18).
- **About 17 items were built, measured worse, and reverted:** school_bus LEDGER:4, 10; pickup:4, 10, 13; delivery_truck:8; tractor:4, 13; taxi:10. Most were a single knob. A 5-second variant run would have screened them before the round.
- **Mirror heads keep coming back.** They appear in 9 of the 12 merged lists and are still open at two ENDs (school_bus LEDGER:12, pickup:14).

### F7. The eyes and tools changed during the project

Each change re-baselined the IoU, so round-start numbers and earlier "tried" results stopped meaning anything.
- **The changes:**
  - enclosedFg arrived in round 2 (taxi LEDGER:7, delivery_truck:12), in commit 94b0bb6 together with a bus round;
  - the truck rear `shift` arrived in round 3 (LEDGER:16);
  - the FIT's concept target erased the truck's white body (EYES-EXPERIMENT.md:37-38);
  - a `comps --family` bug was fixed inside a taxi round (24104ad);
  - modellers added tools during rounds (scripts/v7/README.md:22-32).
- **The rules conflict.** RUNBOOK.md:33-35 allows eye changes only at round boundaries. MODELLER.md:25-26 tells modellers to "use and extend them", with five modellers working in parallel on the same code.

### F8. The gate is never green

- **All five fail.** `inspect.mjs chain` prints `pass false` on all five final models:
  - PALETTE_ZONE: school_bus ×3, pickup ×1, taxi ×10;
  - VEH_WHEELS: delivery_truck ×1, tractor ×2.
- **The modeller has to discount rows by hand.** MODELLER.md:39-41 asks the modeller to subtract "class-config rows" at every KEEP. Formally, "valid module" is unmet everywhere.
- **The triangle budget binds:**
  - pickup reached 3994/4000 and skipped items (pickup LEDGER:10);
  - tractor lugs were skipped (tractor LEDGER:9), then raised as a MAJOR by the post-final critic (tractor/critique/r4-opus.md:2).

### F9. Most of the spend goes into the tail of the run

- **Late rounds moved little where the setup was sound:**
  - bus rounds 1 → 4: within ±0.010 per view (LEDGER:2 vs :10);
  - taxi rounds 3 → 4: at most .004 (:10 vs :13);
  - pickup rounds 3 → 4: at most .001 (:10 vs :13).
- **The round-3 reviews found little that was real.** Four of five subjects had 0–1 MAJOR: one rejected claim, one real see-through slit, and two flip-flops.
- **The largest structural change went unreviewed.** The tractor proportions change landed in the last round with no review (tractor LEDGER:13, 15).
- **Critics ran after the last round.** Ten critic runs were launched afterwards (critique/r4-{fable,opus}/ in all five folders). Nine died with only crops written. No round used the one that finished.

### F10. Work is lost when agents die

Critics write their file only at the end (CRITIC.md:33). When 14 agents stopped at once, nine reviews were lost outright. Nothing caps concurrency.

## 2. Changes (ranked)

| # | Change | Quality | Cost / speed | Medium-effort robustness |
|---|---|---|---|---|
| 1 | Pinned role agents | same seats as in the gold run | no turn-cap restarts | seats do not depend on the orchestrator's effort |
| 2 | Drift as bounded don't-care regions; agree-IoU | bar measurable; escape hatch bounded | the stop rule can fire | KEEP, stop and variant rules become numbers |
| 3 | Setup doctor + one audit + owner setup gate | no mid-run eye fixes; owner calls before round 1 | removes flip-flop rounds | checks are commands |
| 4 | `step.mjs`: one call per iteration | the KEEP rule cannot be skipped | about 1/3 of the modeller's calls; images on demand | the loop is one command |
| 5 | Structured critiques that carry evidence | claims can be checked | partial work survives | no transcription |
| 6 | `merge.mjs` worksheet | flip-flops stopped; tried items screened | no hand merges | the orchestrator writes nothing |
| 7 | `gold.mjs` + `state.json` + skill (+ Workflow driver) | — | resumable after a rate-limit stop | orchestration = follow `status` |
| 8 | Rounds, budgets, mechanical stop | structural changes reviewed or owned by the owner | ≤ 8 runs per model | caps are config |
| 9 | Critic packet | both seats see the same measured evidence | ≤ 25 calls per critic | — |
| 10 | Close the class-config gate gap | "valid module" becomes true or false | no mental subtraction | PASS means PASS |
| 11 | Change control for eyes and tools + `eyes-check` | metrics stay stable within a run | no re-baselines | enforced by `close` |
| 12 | Gold parts kit | recurring parts right the first time | shorter build rounds | fewer choices |

### C1. Package the seats as pinned agent definitions

**Files to add:** four agent definitions in D:\Git\checkout\.claude\agents\ (the repo's agent directory, next to grunt46.md). Each has this frontmatter; the body is the role text from C4, C5 and C3.

```
---
name: gold-modeller
description: LLMModeling v7 gold modeller — edits out/ref/gold/<subject>/model.mjs against refs/<s>.png + subjects/<s>/turnaround. Launch only with a `gold.mjs brief modeller` prompt.
model: claude-opus-5-5
effort: max
maxTurns: 150
tools: Read, Edit, Write, Bash, Glob, Grep
---
```

| Seat | model | effort | maxTurns | tools |
|---|---|---|---|---|
| `gold-critic-fable` | `claude-fable-5-1` | high | 40 | Read, Write, Bash, Glob, Grep (no Edit) |
| `gold-critic-opus` | `claude-opus-5-5` | high | 40 | same, body identical |
| `gold-auditor` | `claude-fable-5-1` | high | 60 | Read, Write, Bash, Glob, Grep |

The auditor is a single seat, per the global rule of one Fable judge seat per visual gate.

**Effort choice.** The modeller stays at max, the condition that produced gold (WF-V7-GOLD.md:3). Stepping it down to high is an A/B test (§4), not a default. The critics run at high: their known errors were caught by measurement, not by effort, and C6 makes that measurement automatic.

**Files to change:**
- **MODELLER.md and CRITIC.md** become one-line pointers to the agent files, so the role text has one home.
- **RUNBOOK.md:5-6 and :19-20:** launch by `subagent_type`, with no model alias and no paraphrase.
- **WF-V7-GOLD.md:32-33:** delete the `general-purpose` / opus-worker advice.

**Effect.**
- The seats keep their model and effort whatever effort the orchestrator runs at. This is the direct answer to "same quality at medium".
- The turn caps fit the work.
- Critics cannot Edit, and C7 checks the module hash anyway.

**Verify.**
- `/agents` in a session started in tools/LLMModeling lists the four agents. If not, start the orchestrator at the repo root.
- One critic launched from a medium-effort session reports `claude-fable-5-1`.

### C2. Drift as bounded don't-care regions; agree-IoU

**views.json contract** (add a bullet to scripts/v6/README.md:6-35). Rects use the image's own pixels, the same coordinates the pages and measure.mjs use.

```json
"drift": {
  "audited": "2026-09-28 gold-auditor, owner-approved",
  "side":    [{ "id": "D1", "rect": [610, 420, 700, 520], "decides": "concept", "why": "turnaround draws a bumper apron; the concept has none" }],
  "concept": [{ "id": "D2", "rect": [520, 380, 760, 560], "decides": "side", "why": "near flank aft of the far flank by ~0.1 m" }]
}
```

**Code:**
- **scripts/v6/ortho.mjs:79-83 and :259.**
  - `loadTurnaround` passes `{...spec.families, drift: spec.drift}` into `familyTable` (:259).
  - `maskRule` (:79) and `subjectMaskRule` (:81) also carry `drift`.
  - `maskOptions(rule, view)` (:83) also returns `dontCare: rule.drift?.[view]?.map(d => d.rect) ?? null`.
  - `readImage` (:149) ignores it.
- **scripts/v6/ortho.mjs:383-403 `viewTarget`.** Add a `care` raster: 0 inside that view's rects, mapped from reference pixels to the judge raster.
- **scripts/v6/ortho.mjs:406-427 `viewScore`.** Also return `agree`: the same IoU with care = 0 pixels excluded from both I and U.
- **scripts/registered.mjs:334-339 `targetState`.** Set `opts.dontCare` pixels to `OCCLUDED`. `iou` (:367-378) already excludes state 2 from both I and U.
- **scripts/v6/judge.mjs:293-294, 317, 320-323.** Write `views[v].agree` and `views[v].drift` (the masked share), plus `minAgree`. `iou` stays as it is.
- **scripts/v6/view.mjs:117-124, 135, 159.** Hatch the rects on the overlay and diff tiles. The notes read `IoU .918 · agree .962 · drift 3.1 %`.
- **scripts/v7/variants.mjs:53-59.** Add agree columns.

**Bound.** In each view, the drift rects may cover at most 5 % of the reference foreground. This makes RUNBOOK.md:15-16's 5 % rule executable. Above it, the view is regenerated.
- Only `gold.mjs drift add|rm` edits the rects, and only at a round boundary; that command re-baselines and writes an `eyes:` line.
- A drift rect cannot cover a whole-view proportion disagreement. That case goes to setup (C3).

**Docs:**
- The bar in WF-V7-GOLD.md:78-81 and the goal in MODELLER.md:4-6 become "agree-IoU ≥ 0.97 on every view". Raw IoU is still reported.
- WF-V7-GOLD.md:48-59 shrinks to "drift is a rect with `decides`". This also removes the ambiguity between the two drift flavours, turnaround drift and concept drift.

**Effect.**
- The bar, KEEP, stop and variant rules become arithmetic.
- The tractor round-4 side loss (−.127) could no longer hide inside prose drift.
- Items whose evidence lies where the other image decides can be rejected by the merge (C6).

**Verify.**
- With no `drift` key, the existing metric fields of all ten subjects are unchanged and `agree == iou` (`gold.mjs eyes-check`).
- Unit tests cover `viewScore` with a care mask and `targetState` with dontCare.
- On the pickup, rects for its logged drifts raise agree above raw, and the drift share prints ≤ 5 %.

### C3. Setup doctor, one audit, and an owner setup gate

**Files to add:**
- `scripts/v7/doctor.mjs`, run as `gold.mjs doctor <s>`. It exits 1 on any BLOCK.
- `subjects/<s>/probes.json`, written by the auditor. It defines 6–15 named scan lines through landmarks such as tyre bottoms, hub rows, roof apex, bumper edges and lamp rows. `step.mjs` prints reference vs model run ends along each line.
- `subjects/<s>/audit.json`, applied by `gold.mjs apply-audit <s>` after the owner approves.
- Optionally, a measured per-view `scale: {right}` next to `shift` (scripts/v6/ortho.mjs:236-241, about a 2-line change). A drawing whose width is off by a uniform few percent can then be corrected with evidence instead of regenerated.

**Doctor checks:**

| Check | BLOCK / WARN rule | Would have caught |
|---|---|---|
| Files; check-module on start.mjs | missing or failing → BLOCK | — |
| Registration residuals W / L / H (ortho.mjs:226-233) | any view > ±3 % → BLOCK: regenerate with measured proportions, add a measured `shift` / `scale`, or an owner ruling | taxi, truck, tractor; all 5 queued subjects |
| Wbbox / Lbbox residuals | > 5 % → WARN | pickup top +13.3 %, rear −9.0 % |
| Enclosed near-white (not border-connected, min channel ≥ fgMax) per view and concept | each component ≥ 0.1 % of fg listed with bbox and crop; enclosedFg unset and total ≥ 0.5 % → BLOCK (white part vs see-through → enclosedFg / holes) | taxi sign and headlights (front .866 → .937), tractor canopy (see-through) |
| Body family vs fgMax | a body colour's min channel ≥ fgMax − 8 → BLOCK | truck white body; EYES-EXPERIMENT.md:37-38 |
| Symmetric-axis centring | fg bbox centre vs origin > 0.03 m → WARN (measure a `shift`) | truck rear +0.11 |
| Concept camera | projected world-up > 0.5° off vertical → WARN | EYES-EXPERIMENT A |
| Gate | chain on start.mjs shows a class-config row with no override (C10) → BLOCK | all 5 golds (F8) |
| Tools | every measure / inspect / frame / variants subcommand runs once on the subject; lib.test passes → else BLOCK | `comps --family` (24104ad) |
| Audit present | views.json `drift` (may be empty) with `audited`, probes.json ≥ 6 lines → BLOCK / WARN | — |

The residual check catches global drift in a view (taxi, truck, tractor). It does not catch local drift (the pickup's bumper, lamp and mirror heights): that is the audit's job.

**Audit** (`gold-auditor`, one Fable seat, ≤ 40 calls). Input: the doctor report plus the start sheet. Its tasks:
- Decide every BLOCK.
- Classify each white candidate.
- Compare each turnaround view with the concept and write drift rects (≤ 5 % per view), each with `decides`.
- Check the concept's self-consistency and write concept-drift rects. The checks are near vs far flank, fanning edges, and hub vs tyre ellipse (WF-V7-GOLD.md:55-58).
- Write probes.json.
- Record the initial decided facts in audit.json, for example which view decides the wheel radius.

**Owner gate.** The owner sees the doctor report, the sheet with hatched rects, and the regenerate list. The owner approves, or has views regenerated with GPT image generation, before round 1. The tractor's "which proportions" call (LEDGER:15) belongs here.

**Effect.**
- The round-2 and round-3 eye fixes and most flip-flops disappear.
- Owner calls move before the spend.
- The cost is about 1 minute of compute plus one Fable run per subject.

**Verify.**
- Run the doctor in a worktree at 0051e9c (the gold setup commit). It must BLOCK taxi, truck and tractor on W, WARN the pickup's bbox, list taxi and truck white candidates, and pass the bus.
- Re-introduce the `comps --family` bug in a scratch worktree: the tools check must BLOCK.

### C4. `step.mjs`: one call per modeller iteration

**Files:**
- Add `scripts/v7/step.mjs`.
- Refactor `scripts/check-module.mjs` to export `checkModule(file)`; the CLI stays unchanged.
- Add `measure.mjs batch`, which runs N queries from a file or stdin in one process.
- Add `variants.mjs --rule concept-first`.

```
node scripts/v7/step.mjs --subject <s> [--save] [--revert] [--pages side,concept]
```

**What one call does**, printing ≤ 40 lines in ≤ 15 s. The module is always out/ref/gold/<s>/model.mjs.
- Build the module and run check-module.
- Run the chain under the subject's gate (C10) and list only rows that are new against the baseline.
- Run the placement checks (floats and clips) and count tris against the budget.
- Refit the concept frame (lib.mjs `fitFrame`, no grid) and print the frame change. WARN when scale moves more than 1 % or a shift exceeds 6 px.
- Print raw and agree IoU per view against the round baseline in state.json.
- Print a verdict line: `KEEP`, or `REVERT: <reasons>`. The reasons are:
  - agree drops by more than 0.01 in any view;
  - a new float or clip;
  - a gate or check-module fail;
  - tris over budget.
- **Blobs:** the top 5 per view of reference-only and model-only components, outside drift and ≥ 20 px, after a 1 px opening (judge.mjs:96 `openMask`) so outlines drop out. Each blob shows its share of the view, its bbox in metres for orthos (ortho.mjs:271 `pxToView`) or px for the concept, and the owning part:
  - model-only blobs take the mode of partId;
  - reference-only blobs take the nearest part on the blob's border.

  This prints the "3 biggest differences" that MODELLER.md:29 asks for.
- **Probes:** reference vs model edge for each probe line, with the Δ in px.

**Flags:**
- `--save` saves only on KEEP. It writes `steps/model-vNN.mjs` (untracked), the fitted frame knobs, and a line in `steps.jsonl`.
- `--revert` restores the last saved step.
- `--pages` renders only the view.mjs pages named.

**Variant rule** (`variants.mjs --rule concept-first`):
- Disqualify any variant that drops an ortho agree-IoU by more than 0.01 against BASE.
- The best concept agree-IoU wins.
- Variants within 0.002 of each other are tied; the higher minimum ortho agree breaks the tie.
- BASE wins ties, as in the repo's Blind Loop rule.
- The script prints `WINNER #n`.

**Effect.**
- An iteration drops from 4–6 calls to 1–2, and from about 9 k image tokens to about 0.5 k of text. Pages are read only for visual items.
- The KEEP rule cannot be skipped or misread.
- Experiment tables decide themselves.

**Verify.**
- On taxi model-v22 against its round-3 baseline, the numbers equal view.mjs + chain + check-module.
- A planted float (mirror moved 0.2 m out) gives `REVERT` naming the part.
- Timing ≤ 15 s.
- Record the next build round's calls against the budget in C8.

### C5. Structured critiques that carry evidence

**Files:**
- Add `scripts/v7/critique.schema.json`, a JSON Schema that is also usable as a Workflow `schema`.
- The critic agent bodies replace CRITIC.md:33-45.

```json
{ "subject": "taxi", "round": 3, "seat": "opus", "done": false,
  "items": [{ "sev": "MAJOR",
    "key": "knob:signT | def:zR1 | def:stripeY | part:mirror_head.size.z | drift:front",
    "now": 0.391, "want": 0.345, "unit": "m|deg|hex|count|text",
    "views": ["front", "rear", "concept"], "basis": "concept|side|front|rear|top",
    "at": { "image": "front", "rect": [410, 120, 470, 160], "claim": "ref-only|model-only|colour|edge" },
    "evidence": ["node scripts/v7/measure.mjs profile --subject taxi --view front --module ..."],
    "reopens": null, "note": "<= 200 chars" }] }
```

`part:<family>.<param>` takes a param from a closed list: `pos.x`, `pos.y`, `pos.z`, `size.x`, `size.y`, `size.z`, `rot`, `colour`, `shape`, `count`, `add`, `remove`.

**Rules in the critic body:**
- At most 12 items.
- Keys come from the packet's knob and part tables.
- `at` is required for MAJOR.
- `reopens` needs verified evidence on the decided item's basis image. The existing rule at CRITIC.md:6-9, made checkable.
- Drift is proposed as `drift:<view>` with a rect.
- No verdict line: C6 computes it.
- Rewrite the file after every item; set `done:true` at the end.
- At most 25 calls.

**Effect.**
- The merge becomes mechanical and claims become checkable.
- A killed critic leaves its items on disk.
- Nobody transcribes critic output.

**Verify.**
- A grunt converts the ten round-3 critiques to the schema; all validate.
- The first live critic output validates on the first try.

### C6. `merge.mjs`: the worksheet, a mechanical merge

**File to add:** `scripts/v7/merge.mjs`, run as `gold.mjs merge <s>`. It writes `critique/rN-merged.md` and `critique/rN-merged.json`.

**Rules, applied in order:**
1. **Schema.** A missing file or `done:false` stops the merge and prints the resume brief.
2. **Evidence.** Rebuild the model's raster for `at.image` (reuse `modelRGB` in measure.mjs:116-138) and test the claim inside the rect:
   - `ref-only` / `model-only`: at least 15 % of the rect's pixels are that kind of difference;
   - `colour`: the reference's family ≠ the model's family;
   - `edge`: at least one pixel differs.

   A failed test → REJECTED, with the numbers. The bus round-3 arch claim at side (244, 566) is the tyre family in both images, so it is rejected automatically.
3. **Drift.** An `at` inside a drift rect whose `decides` differs from the item's `basis` → REJECTED-DRIFT. Taxi round-2 C6, the rear axle read off the distorted concept flank, fails here once the flank rect exists.
4. **Decided.** An item on a key that state.json lists as decided, without a verified `reopens`, → DECIDED: dropped, but listed.
5. **Tried.** Same key and same direction as an earlier attempt → TRIED, with the old numbers. Tried twice → PARKED and sent to the owner packet. This is the Blind Loop stall rule with K = 2; it ends the mirror-head loop.
6. **Pairing.** Match on the exact key first. Then match `part:` items to a knob whose comment names that part family on the same axis. Classes:
   - **A:** both seats, same sign, amounts within 2×. The target is the mean; both amounts are shown.
   - **CONFLICT:** opposite signs, amounts more than 2× apart, or different non-numeric wants.
   - **B:** one seat, MAJOR.
   - **C:** one seat, MINOR or unverified.
7. **Auto-variants.** Every A, B or CONFLICT item with a knob/def key gets a `variants.mjs --rule concept-first` run of each want against BASE, and its per-view agree deltas are attached. An item that loses more than 0.01 agree on its own basis view is marked "verify visually". CONFLICTs are settled by the WINNER.
8. **Experiments.** A structural CONFLICT with no key becomes an `X` line: the modeller builds both versions and applies the C4 rule.
9. **STOP line** (first line of the file):
   - `STOP` when no MAJOR stands (A-MAJOR, B, or an unsettled CONFLICT with a MAJOR side), every view's agree ≥ 0.97, and the chain PASSes;
   - `OWNER` at the round cap or when a PARKED or structural item needs an owner call;
   - otherwise `CONTINUE`.

**Worksheet example:**

```
STOP: CONTINUE — 1 MAJOR standing (B1); min agree .962 (front) < .97
| id | class | key            | views        | fable       | opus              | evidence | variant (agree Δ)        |
| A1 | A     | def:rearWin    | rear         | 1.80→1.835  | 1.79→1.825        | ✓        | rear +.004               |
| B1 | B     | knob:signT     | front,concept| —           | .391→.345 MAJOR   | ✓        | front +.0014, concept +.0004 |
| X1 | REJ   | part:arch.colour| side        | #2a2a20 MAJ | —                 | ✗ both "tyre" at 244,566 | — |
| T1 | TRIED | def:mh         | concept,front| —           | .39→.45           | r3: concept −.001, front −.004 | PARKED (2nd) |
```

**Effect.**
- The orchestrator writes nothing.
- Wrong claims, drift misreads and flip-flops are stopped before a modeller round.
- About 17 tried-and-reverted items (F6) are screened in about 5 s each.

**Verify.**
- Replay on the 12 existing merges, using the converted critiques. The classes must match the hand merges on at least 80 % of items, and every difference is listed.
- The bus X1 is auto-rejected.
- The run takes under 3 min.

### C7. Orchestrator: `gold.mjs`, `state.json` and a skill, plus a Workflow driver

**File to add:** `scripts/v7/gold.mjs`, with these subcommands:

| Subcommand | Does |
|---|---|
| `status [<s>] [--json] [--cost]` | For every subject: round, phase, raw/agree IoU, standing MAJOR, next action |
| `doctor <s>`, `apply-audit <s>` | C3 |
| `brief <modeller\|critic\|auditor> <s> [--seat] [--resume]` | Prints the exact Agent call (subagent_type, description, prompt). The prompt fills subject, round, round type, budget, dims (prior.json), baseline, worksheet path and resume state. Pass it verbatim. |
| `close <s>` | Validates the modeller's `report.json`; checks that the eyes-file hashes did not change (C11); records the model hash (`merge` refuses if the model changed during review); renders `--zoom`; builds the packet (C9); writes the ledger line; moves the phase to review |
| `merge <s>` | C6 |
| `commit <s>` | `git add -f` explicit pathspecs (model.mjs, model-rN.mjs, LEDGER.md, state.json, critique/*.json and .md, review/rN sheet); the message is the ledger line. Workstream commits are in scope per the LLMModeling autonomy ruling. |
| `drift <s> add\|rm`, `eyes-check` | C2, C11 |

**State.** `out/ref/gold/<s>/state.json` holds:
- round, phase, roundType, baseline, modelHash and eyesHash;
- decided, tried, parked and open items, each as `{key, value, basis, round, evidence}`;
- runs, each as `{role, round, calls, minutes}`, copied from the Agent result.

LEDGER.md is generated from state.json. That replaces the 300–1 100-character hand-written lines, for example delivery_truck LEDGER:14.

**Modeller report.** The modeller writes `report.json` with:
- items, each `{id, key, status: done|partial|tried|skipped, value, why, delta}`;
- drift proposals;
- decided facts (with the WINNER table);
- open items.

Its final text is 10 lines or fewer, so evidence flows up compressed.

**Skill.** Add `D:\Git\checkout\.claude\skills\gold-model\SKILL.md`, 50 lines or fewer:
- the status → action table;
- at most 6 agents at once;
- merges and ledger lines are never written by hand;
- the owner gates are setup approval and the final sheets;
- an agent stopped at its cap → `brief <role> <s> --resume`.

**Workflow driver** (preferred when the Workflow tool is enabled; the workflow-authoring skill is installed). Add `research/v7/gold.workflow.js`: the same loop, deterministic and resumable with `resumeFromRunId` after a rate-limit stop. Mechanical steps run through a `grunt` agent at `effort: 'low'`, because workflow scripts have no filesystem access.

```js
export const meta = { name: 'gold-subject', description: 'v7 gold loop for one subject until STOP or OWNER', phases: [{ title: 'Model' }, { title: 'Review' }] }
const S = args.subject
const OUT = { type: 'object', properties: { out: { type: 'string' } }, required: ['out'] }
const sh = async (cmd) => JSON.parse((await agent(`From tools/LLMModeling run exactly: ${cmd} — return its last stdout line verbatim as "out".`, { agentType: 'grunt', effort: 'low', schema: OUT })).out)
let st = await sh(`node scripts/v7/gold.mjs status ${S} --json`)
for (let i = 0; i < 12 && (st.next === 'model' || st.next === 'review'); i += 1) {
  if (st.next === 'model') {
    phase('Model')
    const b = await sh(`node scripts/v7/gold.mjs brief modeller ${S} --json`)
    await agent(b.prompt, { agentType: 'gold-modeller', label: `${S} r${st.round} modeller` })
    await sh(`node scripts/v7/gold.mjs close ${S} --json`)
  } else {
    await parallel(['fable', 'opus'].map((seat) => async () => {
      const b = await sh(`node scripts/v7/gold.mjs brief critic ${S} --seat ${seat} --json`)
      return agent(b.prompt, { agentType: `gold-critic-${seat}`, phase: 'Review', label: `${S} r${st.round} ${seat}` })
    }))
    await sh(`node scripts/v7/gold.mjs merge ${S} --json`)
  }
  st = await sh(`node scripts/v7/gold.mjs status ${S} --json`)
}
return st   // next = 'owner': setup gate or final sheet
```

A batch is `pipeline(args.subjects, (s) => workflow('gold-subject', { subject: s }))`. One nesting level is allowed, the concurrency cap is shared, and `budget` gives a hard token ceiling.

**Effect.**
- A medium-effort orchestrator only follows `status`.
- Its context stays small.
- A rate-limit kill costs one relaunch instead of the lost reviews.

**Verify.**
- Run one subject end to end with the orchestrator at medium effort: no hand-written merge or ledger line, and `status` names the right next action in every phase.
- Kill a critic mid-run: `--resume` finishes from its partial JSON.

### C8. Rounds, budgets and stop rules

**File to add:** `scripts/v7/gold.config.json`, holding the caps and thresholds. It replaces WF-V7-GOLD.md:69-75 and RUNBOOK.md:18-31.

**Sequence:**
1. Setup: doctor, audit, owner gate.
2. **Round 1, build:** modeller, ≤ 100 calls. It stops at a plateau (3 consecutive REVERTs on the top blob) or at the budget.
3. **Review 1:** two critics, ≤ 25 calls each, then merge. STOP / OWNER / CONTINUE.
4. **Round 2, list:** ≤ 60 calls.
5. **Review 2**, then merge. STOP / OWNER / CONTINUE.
6. **Round 3, polish, the last:** ≤ 40 calls. A, B and C items only. A structural item still open after review 2 goes to the owner packet, not into the last round.
7. Owner.

No critic review runs after the last round. The owner packet `OWNER.md` holds:
- the final sheet with raw and agree IoU;
- the drift share;
- the open worksheet items, PARKED items, and items blocked by the budget;
- the gate state;
- the cost per run.

**Resilience:**
- At most 6 agents run concurrently; subjects go in waves.
- Writes are progressive: critic JSON after each item, and `steps.jsonl` plus snapshots for the modeller.
- `calls` and `minutes` are recorded for every run.

**Cost:**

| | As run | Planned |
|---|---|---|
| Agent runs per model | about 11.4: 20 modeller + 37 critic launches over 5 models | at most 8: 1 auditor + 3 modeller + 4 critic. 4–6 when the STOP fires early. |
| Tool calls per model | 300–1 800: 4 modeller rounds × 30–235, plus about 7.4 critic runs × 25–115 | at most 340 by budget |

**Effect.** The largest direct cut in cost and time per model. Structural changes are always reviewed or go to the owner.

**Verify.** The next batch (§4).

**Owner gate.** The round cap, the review count and the call budgets are process numbers the owner ratifies. The two-critic rule (owner, 2026-09-27) is kept.

### C9. Critic packet

**File:** `gold.mjs close` writes `out/ref/gold/<s>/review/rN/` containing:
- the sheet and pages;
- `blobs.txt` and `probes.txt` (from C4);
- `grid --module --diff` crops of the top 8 blobs at native resolution;
- `parts.txt` (`inspect.mjs parts`);
- `knobs.txt`, from a new `inspect.mjs knobs`: KNOBS plus flattened DEFAULTS paths, with values and comments. This covers both styles in use: taxi has 47 KNOBS, the other four have DEFAULTS + buildWith;
- `facts.md`: decided, tried, parked and drift entries with their ids;
- `palette.txt`: model zone colours against the family table.

**Effect.**
- Critics read instead of computing: ≤ 25 calls, against 25–115 as run, with up to 63 crops per run.
- Both seats see the same measured evidence.
- Their keys come from the tables, so C6 can pair them.

**Verify.** Next-batch critic runs stay at ≤ 25 calls and ≤ 25 min each.

### C10. Close the class-config gate gap

**Code:**
- **src/validate/kernel-chain.mjs:117.** Add `"wheels"` and `"paletteZones"` to `RULE_OVERRIDES`.
- **kernel-chain.mjs:124-141.** Two new overrides, each `{value, evidence}` and each printing a `RULE_OVERRIDE` advisory as the existing ones do:
  - `wheels`: `{count, axles, diameters: "equal"|"per-axle", diameterFrac?: [lo, hi]}`;
  - `paletteZones`: `{extra: [...]}`.
- **kernel-chain.mjs:454-457.** PALETTE_ZONE keys become the author keys plus `extra`.
- **src/validate/rules/vehicle.mjs:127, :136-144, :153-162.** Take `want` from the override; with `per-axle`, compare diameters within each axle cluster only; take the band from the override.

**Subject files:**
- school_bus, pickup and taxi `subject.json` get `paletteZones` with the concept sample as evidence.
- delivery_truck and tractor get `wheels`. The tandem 6/3; the tractor 0.81 / 1.40 m (LEDGER:6).

A class variant in classes/vehicle.json, for example `tandem`, is the alternative for the truck.

**Triangle budget.** The budget stays owner-owned. step.mjs prints tris per part family, and the owner packet lists items blocked by the budget (pickup LEDGER:10, tractor LEDGER:9 / r4-opus.md:2).

**Effect.** `pass true` means valid. KEEP has nothing to discount, and "valid module" becomes a fact.

**Verify.**
- The chain on the five golds prints `pass true` plus advisories.
- An undeclared zone still fails.
- Tests under test/ cover the new overrides.

**Validation zone.** New override names are an owner ratification. They extend the "TARGET WINS" ruling of 2026-09-26.

### C11. Change control for eyes and tools

**Agent body rule.** Modellers may add flags or subcommands to scripts/v7/{measure,inspect,variants,frame}.mjs and lib.mjs, each with a test in lib.test.mjs. They never touch the eyes files:
- scripts/v6/{judge,ortho,view}.mjs;
- scripts/registered.mjs and scripts/project.mjs;
- subjects/<s>/{turnaround/views.json, camera.json}.

**Enforcement:**
- `brief` stores the eyes files' hashes, and `close` refuses if any hash changed.
- `gold.mjs eyes-check` re-renders every subject's model.mjs, compares the numbers with state.json, and exits 1 on any change. This is RUNBOOK.md:33-35's "byte-identical" check as a command, run after every orchestrator-side eye change.

**Effect.** Metrics stay fixed within a round. Five parallel modellers cannot race on the judge.

**Verify.**
- Edit ortho.mjs in a scratch worktree: `close` refuses.
- `eyes-check` on the current tree reports no change for all subjects.

### C12. Gold parts kit

**Code:**
- **Update to the gold forms:** src/kernel/assemblies.mjs `handle` (:1311), `lamp` (:1351) and `mirror` (:1555).
- **New helpers extracted from the gold modules:**
  - `wheel({R, width, hubR, capR, inset, shoulders, duals})` — square shoulders and a recessed hub (taxi round 3 B2), plus the truck's duals;
  - `archLiner({R, gap, fill})` — fill down to the tyre (pickup round 4 A1);
  - `bumper({w, h, depth, wrap})`.

**Modeller body.** Build recurring parts with the kit and change their parameters; change their shapes only when a worksheet item says so. New start.mjs files use the kit, while the body stays a blockout.

**Evidence.** The gold modules call `K.assemble` 0–1 times each. Mirror heads, lamps and wheels are the items that recur across worksheets (F6).

**Effect.**
- Shorter build rounds and fewer recurring-part items.
- It is the first real step of the after-gold distillation (WF-V7-GOLD.md:87-90).

**Verify.**
- Swapping each gold part for its helper keeps that subject's per-view agree within 0.002 and its tris within ±5 %.
- Build rounds of the next batch use fewer calls than today's round 1.

### Implementation order, gates and validation-zone stops

**Order of changes** (dependencies):
1. C1
2. C2 — gate: `eyes-check` identical with no drift.
3. C10 — gate: 5 golds `pass true`.
4. C4 — gate: numbers equal to the three tools.
5. C3
6. C11
7. C5
8. C9
9. C6 — gate: replay on the 12 merges ≥ 80 % and bus X1 rejected.
10. C7
11. C8
12. C12

The last gate is the acceptance test in §4.

**Validation-zone stops (owner):**
- new override names (C10);
- round, review and budget numbers (C8);
- per-subject setup approval, regenerated views and drift rects (C3);
- deleting tracked files (§3).

Commits of workstream pathspecs are in scope.

## 3. Delete or simplify

**Delete:**
- `out/ref/gold/school_bus/tools/` (23 files) and `out/ref/gold/delivery_truck/tools/` (19 files). scripts/v7 supersedes them: commit 6fcc9b0 says it was "verified equal".
- The ad-hoc folders `*/view0/`, `*/snap/` and `tractor/k1/`.
- The nine orphan round-4 crop directories.

**Stop tracking:**
- Per-step snapshots: 22–47 `model-vNN.mjs` per subject, all added with `git add -f`. Keep `model.mjs` and `model-rN.mjs`; `steps/` stays untracked.
- Critic crop directories `critique/r*-<seat>/`, which can be regenerated.

**Remove from the protocol:**
- The ACCEPT / NOT YET line (CRITIC.md:35): computed by C6.
- The "at least 8 iterations" floor (MODELLER.md:28, WF-V7-GOLD.md:70): replaced by the plateau rule.
- The FIT option for the modeller (WF-V7-GOLD.md:10-11): no ledger shows it used.
- The `cmp` verification step (RUNBOOK.md:21-22): now `close`.
- Critics that see the sheet only (truck round 1): `close` always renders pages.
- Post-final critic reviews.
- The "one cheap orchestrator measurement" rule (WF-V7-GOLD.md:38-40): C6's evidence check replaces it.

**One home per rule:**
- The role text lives in the agent definitions. MODELLER.md and CRITIC.md shrink to pointers.
- The rules live in scripts/v7: `step`, `merge`, `doctor`, `gold.config.json`.
- The procedure lives in the skill (or Workflow).
- WF-V7-GOLD.md keeps the rationale and evidence under a banner saying it is not instructions. Its Merge (:19-27), Orchestrator notes (:29-46) and Round protocol (:69-75) are removed or pointed elsewhere.

**Stale text:**
- WF-V7-GOLD.md:83-85, Starts.
- RUNBOOK.md:5 (`general-purpose`, `model opus`).
- The perspective claim in out/ref/gold/taxi/model.mjs:16-18. Decided facts belong in state.json, not in module headers.

**Simplify:**
- The merge classes become one printed set: A, B, C, X, REJECTED, DECIDED, TRIED, PARKED. The ad-hoc K1/K2 labels go.
- The two drift flavours become one record with `decides`.
- `open (orchestrator)` lines become state.json `open` entries. A structural open item blocks the next round until the owner or the auditor decides it.

**Keep, but out of the gold path:**
- scripts/v6/loop6.mjs and mvfit.mjs, and the family-matched `viewRows` in the judge JSON. On the final taxi those rows are noisy, for example "stripe_l (dark) 0.49 m too far forward, 3.02 m too wide". Leave them for the after-gold ablation and do not show them to seats.

**What works and should stay:**
- the concept-wins rule;
- the blind dual critics;
- the build-both variant tables (the truck and tractor tables settled real disagreements);
- view.mjs `--zoom` pages;
- hand-built modules measured on the references.

## 4. Acceptance test for the change set

Run the next batch (forklift, garbage_truck, icecream_van, ambulance, fire_truck) with the orchestrator at medium effort.

**Pass criteria, per subject:**
- The doctor PASSes before round 1, after audit and owner approval.
- `eyes-check` is clean at every `close`.
- No merge or ledger line is written by hand.
- `chain` PASSes.
- Every view's agree-IoU is ≥ 0.97, or the owner packet names the blob that explains the gap.
- The owner accepts the sheet.

**Cost criteria:**
- at most 8 agent runs per model;
- each modeller round within its budget;
- critics at ≤ 25 calls and ≤ 25 min;
- no post-final reviews;
- `status --cost` shows per-model calls at least 50 % below the gold run's.

**Medium-vs-high A/B.** Use icecream_van, the smallest residual of the batch at 4.8 %. Run it twice from the same approved setup in two worktrees: once with the orchestrator at medium effort and once at high. Pass when:
- per-view agree-IoU matches within ±0.005;
- both runs reach the same STOP / OWNER outcome;
- the owner, blind, does not prefer either sheet.

**Optional second A/B:** the modeller seat at high instead of max, with the same pass rule. If it passes, it saves the most expensive seat's premium.

## Appendix: measurements made for this review

```
# registration residuals (band ±3 %, scripts/v6/README.md:22-24)
node -e "import('./scripts/v6/ortho.mjs').then(async ({loadTurnaround}) => { for (const s of process.argv.slice(1)) { const {reg} = await loadTurnaround(s); console.log(s, JSON.stringify(reg.residuals)); } })" school_bus pickup delivery_truck tractor taxi forklift garbage_truck icecream_van ambulance fire_truck
# gate on the gold models (all five print "pass false")
for s in school_bus pickup delivery_truck tractor taxi; do node scripts/v7/inspect.mjs chain --module out/ref/gold/$s/model.mjs --subject $s | head -1; done
# timings on the gold taxi: view --zoom 4.8 s · check-module 0.6 s · chain 1.9 s · variants with 2 rows + BASE 13 s
```

W residual per view (%), with the bbox residual where it is out of band:

| Subject | W front | W rear | W top | Wbbox or other | Doctor verdict |
|---|---|---|---|---|---|
| school_bus | −0.1 | +0.5 | −0.4 | Wbbox top −4.4 | pass |
| pickup | −1.7 | +0.4 | +1.3 | Wbbox top +13.3, rear −9.0 | WARN |
| delivery_truck | −3.5 | +7.4 | −3.8 | — | BLOCK |
| tractor | +3.4 | −6.8 | +3.4 | — | BLOCK |
| taxi | +6.8 | +2.5 | −9.3 | — | BLOCK |
| forklift | −6.0 | +9.6 | −3.6 | Wbbox rear −5.8 | BLOCK |
| garbage_truck | −9.1 | 0.0 | +9.1 | H side +3.2; Wbbox rear −15.7, top +16.6 | BLOCK |
| icecream_van | −3.1 | −1.7 | +4.8 | — | BLOCK |
| ambulance | −4.7 | −1.2 | +5.9 | — | BLOCK |
| fire_truck | +3.3 | +1.7 | −5.0 | Wbbox front +4.2 | BLOCK |

The L and H residuals are within ±1.5 % everywhere except garbage_truck H. Page sizes on the gold taxi: sheet 1728×858; pages 1549×566 to 958×1678, about 1.2–1.9 k tokens each.
