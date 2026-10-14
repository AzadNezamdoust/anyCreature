# WF v8 — the reusable gold workflow (reconciled plan, orchestrator Opus 5.5, 2026-09-27)

Owner: "we will reuse it a lot in medium and high effort to generate stuff". Inputs: two blind reviews,
research/v7/WF-REVIEW-fable.md (F1–F10, C1–C12) and research/v7/WF-REVIEW-opus.md (F1–F10, C1–C12). Both found the same
core: v7 makes good models but quality and cost depend on the orchestrator's hand work (merges, rulings, ledger prose,
verification), the bar is not computable, reference disagreements surface one round at a time, eyes changed mid-run,
seats were not pinned, rounds ran on the cap, critics were slow and sometimes wrong. v8 moves judgment into pinned seats
and deterministic scripts so a MEDIUM-effort orchestrator gets the same result. References below: "F:C3" = Fable review
change C3, "O:C2" = Opus review change C2 — the implementer reads those sections for detail; this file decides conflicts.

## Decisions (where the reviews differ)
- Names: agents `gold-modeller`, `gold-critic-fable`, `gold-critic-opus`, `gold-auditor`; scripts `scripts/v7/gold.mjs`
  (orchestrator), `step.mjs` (modeller loop), `doctor.mjs` (setup), `merge.mjs`, `scaffold.mjs`.
- Seats (O:C1 / F:C2): project agents in D:\Git\checkout\.claude\agents\. gold-modeller claude-opus-5-5 effort high
  maxTurns 120; critics claude-fable-5-1 / claude-opus-5-5 effort high maxTurns 40, no Edit tool; gold-auditor
  claude-fable-5-1 effort high maxTurns 60. (Modeller high not max: the owner runs at medium/high; the acceptance A/B below
  decides whether max is worth it — one frontmatter line.)
- Drift (O:C2 over F's bar.json): drift = rects in views.json `drift: {<view>|concept: [{id, rect, decides, why}]}`,
  ≤ 5 % of a view's reference foreground, masked as don't-care → `agree` IoU per view; raw IoU still reported. Bar =
  agree ≥ 0.97 in every view. Rects change only via `gold.mjs drift add|rm` at a round boundary (re-baselines).
- Rounds (O:C8 + F:C6): setup (doctor → auditor → OWNER setup gate) → r1 build (≤ 100 calls) → review → r2 list (≤ 60)
  → review → r3 polish (≤ 40, A/B/C only) → OWNER. No critic review after the last round. STOP / OWNER / CONTINUE is
  printed by merge.mjs (O:C6 rule 9). A structural item still open after review 2 goes to the owner packet.
- MAJOR (F:C6): a measured discrepancy ≥ 0.05 m or ≥ 3 % of the view's dimension, or a missing / extra / wrong-count
  feature; a MAJOR without machine-checkable evidence is merged as MINOR.
- Critique (O:C5 + F:C5 + F:C8): JSON per schema (+ a short md), ≤ 10 items, keys from the packet's knob/part tables,
  written progressively (done:false → true), no crops in the repo (scratchpad).
- Merge (O:C6, F:C5): evidence check, drift reject, decided / tried / parked (K = 2), pairing A/B/C/CONFLICT/X,
  auto-variants with `variants.mjs --rule concept-first`, STOP line. The orchestrator writes nothing by hand.
- Gate (O:C10 over F:C7): `RULE_OVERRIDES` gains `wheels` {count, axles, diameters: equal|per-axle, diameterFrac?} and
  `paletteZones` {extra: [...]}, each {value, evidence} and printed as RULE_OVERRIDE advisories — an extension of the
  owner's 2026-09-26 "target wins via measured per-subject overrides" ruling (flagged to the owner).
- Starts (F:C10): `scaffold.mjs` starts a subject from the nearest gold of its class. The parts kit (O:C12) waits for
  the distillation phase.
- State (O:C7 / F:C1): out/ref/gold/<s>/state.json is the source of truth; LEDGER.md is generated from it.
- Eyes change control (O:C11): modellers never edit the eyes files; `close` refuses on changed eye hashes;
  `gold.mjs eyes-check` re-renders every subject and must show no change.
- Repo (F:C11): stop tracking crops, per-step snapshots, subject-local tools, scratch dirs (git rm --cached + .gitignore;
  nothing deleted from disk); one `model-rN.mjs` per round is kept.
- Deferred: the Workflow driver (O:C7 optional; needs the owner's opt-in), the parts kit (O:C12), viewRows removal from
  the v6 loop (only hidden from v7 seats).

## Work packages (implementation order; each ends in its gate)
WP1 eyes (O:C2, F:C4, O:C4 blob part, hide viewRows): scripts/v6/{ortho,judge,view}.mjs, scripts/registered.mjs,
  scripts/v7/variants.mjs (+ agree columns, `--rule concept-first`), unit tests. Blob table in the view JSON + printed
  lines (refOnly / modelOnly after a 1 px opening, top 5 per view outside drift, owning part, bbox in m / px).
  GATE: with no `drift` key every subject's outputs are byte-identical to before (all ten subjects); tests pass.
WP2 gate (O:C10): src/validate/kernel-chain.mjs RULE_OVERRIDES + PALETTE_ZONE keys, src/validate/rules/vehicle.mjs
  VEH_WHEELS (count / axles / per-axle diameters / band), tests. Subjects are NOT edited in WP2 (the orchestrator adds
  the overrides at a round boundary). GATE: existing tests pass; unknown zones still fail; override fixtures pass.
WP3 modeller loop + setup (O:C4, O:C3, F:C3, F:C10): scripts/v7/step.mjs (build, check-module, chain new rows, floats /
  clips, tris, frame refit, raw + agree IoU vs baseline, KEEP / REVERT line, blobs, probes, --save / --revert / --pages),
  scripts/v7/doctor.mjs (O:C3 table + F:C3 checks), scripts/v7/scaffold.mjs, research/v7/AUDITOR.md, optional per-view
  `scale`. GATE: step.mjs numbers equal view.mjs + chain + check-module on taxi model-v22; doctor at 0051e9c-era configs
  BLOCKs taxi / truck / tractor, WARNs the pickup, passes the bus.
WP4 critique + merge (O:C5, O:C6, F:C5): scripts/v7/critique.schema.json, scripts/v7/merge.mjs. GATE: replay on the
  converted round-3 critiques matches the hand merges on ≥ 80 % of items; the bus "near-black arch" is auto-REJECTED.
WP5 orchestration (O:C7, O:C9, O:C11, F:C1, F:C2, F:C12, F:C11): scripts/v7/gold.mjs (status, doctor, apply-audit,
  brief, close, merge, commit, drift add|rm, eyes-check), state.json + generated LEDGER.md, gold.config.json, the four
  agent definitions, D:\Git\checkout\.claude\skills\gold-model\SKILL.md (≤ 50 lines), MODELLER.md / CRITIC.md → role
  bodies in the agent files, RUNBOOK.md → pointer to the skill, WF-V7-GOLD.md → rationale only, .gitignore + untracking.
  GATE: one subject runs end to end from the skill at MEDIUM orchestrator effort with no hand-written merge or ledger line.

## Shared data (WP4 and WP5 both use these; do not change the shape without updating both)
- out/ref/gold/<s>/state.json — source of truth, LEDGER.md is generated from it:
  `{subject, round, phase: setup|model|review|owner|done, roundType: build|list|polish, baseline: {file, views:
  {<v>: {iou, agree}}}, modelHash, eyesHash, items: {decided: [{key, value, basis, round, evidence}], tried: [{key, dir,
  round, result}], parked: [{key, reason, round}], open: [{key, text, owner: bool}]}, runs: [{role, seat?, round, calls,
  minutes, ok}], ledger: [{round, role, text, iou?, tris?, gate?}]}`. Keys use the critique key grammar below.
- critique/rN-<seat>.json (scripts/v7/critique.schema.json, O:C5): `{subject, round, seat, done, items: [{sev: MAJOR|MINOR,
  key: "knob:<name>" | "def:<path>" | "part:<family>.<pos.x|pos.y|pos.z|size.x|size.y|size.z|rot|colour|shape|count|add|
  remove>" | "drift:<view>", now, want, unit, views, basis, at: {image, rect: [x0,y0,x1,y1] in that image's own px, claim:
  ref-only|model-only|colour|edge}, evidence: [commands], reopens, note}]}`, written after every item (done:false → true).
- critique/rN-merged.json + .md (merge.mjs, O:C6): first line `STOP: STOP|OWNER|CONTINUE — <reason>`; classes A, B, C,
  CONFLICT, X (structural experiment), REJECTED, REJECTED-DRIFT, DECIDED, TRIED, PARKED.
- WP5 additions (the shapes above unchanged): report/rN-modeller.json (gold-modeller → `gold.mjs close`) `{subject, round,
  done, items: [{id, key, status: done|partial|tried|skipped, from?, to?, dir?, why}], drift: [{image, rect, decides,
  why}], decided: [{key, value, basis, evidence}], open: [{key, text}], notes}` — `tried` becomes state tried (dir as
  merge.mjs dirOf), a drift proposal an owner open item; eyes.json (gold.mjs) = the eyes reference `{module,
  moduleSha256, eyesHash, render: {json, png, views}, files}` that close / merge / eyes-check compare against; state
  keys `fact:<name>` (auditor and owner facts) extend the key grammar for items no critique can raise.

## Acceptance (the next batch: ambulance, fire_truck, garbage_truck, forklift, icecream_van)
Per subject: doctor PASS after audit + owner setup approval; eyes-check clean at every close; no hand merge or ledger
line; chain PASS; every view agree ≥ 0.97 or the owner packet names the blob that explains the gap; ≤ 8 agent runs per
model; critics ≤ 40 turns. A/B: icecream_van twice from the same approved setup — orchestrator at MEDIUM vs HIGH; pass
when per-view agree matches within ±0.005 and both reach the same STOP / OWNER outcome.

## Owner stops (validation zone)
New override names (WP2) · round / review / budget numbers (defaults above) · per-subject setup approval, regenerated
views and drift rects · anything that deletes tracked history (not planned: untracking only).
