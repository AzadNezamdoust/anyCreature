# WF-v7 workflow review — Fable 5.1 seat (2026-09-27, blind to the other reviewer)

Scope: the workflow, not a model. Read: research/WF-V7-GOLD.md, research/v7/{RUNBOOK,MODELLER,CRITIC,EYES-EXPERIMENT}.md,
scripts/v6/README.md, scripts/v7/README.md, scripts/v6/view.mjs + judge.mjs (blobs / viewRows / orthoTiles), scripts/v7/*.mjs,
the five LEDGER.md files, the 36 critique/*.md files, `git log e4055be..HEAD -- .` (36 commits, 09-26 22:56 → 09-27 07:08),
`git ls-files out/ref/gold`, and one timing pass on the taxi gold (view --zoom 3.3 s, view 2.6 s, inspect chain 1.25 s,
check-module 0.34 s, variants BASE+2 7.8 s, frame fit 10.5 s). Owner requirement: the same bar at MEDIUM orchestrator effort,
cheaper and faster per model, roles pinned as agent definitions.

Verdict in one paragraph: v7 produced five usable models, but as an expert-operated process. Every judgment-heavy step
sits with the orchestrator by hand (the merge, the lone-MAJOR check, drift classification, ledger prose, commit
selection); the role prompts assume a max-effort reader; the eyes changed under the modellers three times; the
"≥ 0.97 where the references agree" bar is not computed anywhere, so the stop rule rests on one critic seat's taste.
Machine time is irrelevant (≈ 5 s per iteration); the cost is agent turns, image reads and hand-written artefacts:
≈ 8–9 agent-hours per model plus ≈ 30 orchestrator artefacts (15 merges of 25–57 lines, 36 commits, 5 ledgers). The fix
is not a new loop: script the mechanics, make the critique machine-mergeable, decide reference agreement before round 1,
and give the modeller a one-command KEEP. The bar then becomes a per-view number the scripts can check.

## 1. Failure modes and costs (ranked by cost × medium-effort risk)

F1. The orchestrator does judgment work by hand. The merge (WF-V7-GOLD.md:19–27, RUNBOOK.md:29–31) matches items across
two free-text lists by part + view + direction and writes A/B/C/CONFLICT/TRIED plus experiments — 15 files of 25–57 lines
(delivery_truck r2-merged.md: 54 lines, its K1 at lines 26–37 is a hand-written joint solve). The lone-MAJOR check is a
hand measurement (WF-V7-GOLD.md:38–40; school_bus LEDGER:9). Verification is manual (`cmp`, "only class-config rows",
"the sheet exists": RUNBOOK.md:21–22). This was done at max effort by Opus 5.5; at medium effort it is exactly what
degrades first (mismatched items, a missed CONFLICT, a MAJOR taken on faith).

F2. Critics are expensive and unstable. 25–115 calls and 25–75 min per seat-round (WF-V7-GOLD.md:34–35); each item is a
300–1200-character paragraph of pixel measurements (delivery_truck r2-fable.md item 1 is 2.1 kB). 314 critic crop PNGs are
committed (pickup r2-fable/: 49 files, tractor r2-opus/: 63). Flip-flops: pickup cab rake (LEDGER:3 "rake 0.15" → :8 both
"plumb"), bus tyre R (LEDGER:3 "bigger" → :6 Opus "0.53 → 0.48" → :7 0.46), taxi sign (r1-merged C4 widen 0.35 → 0.40; r3
Opus MAJOR narrow to 0.345; r4 measured 0.365, taxi LEDGER:12–13). Two wrong MAJORs: "perspective" (taxi LEDGER:4,
taxi r1-merged.md:3–5, truck LEDGER:10 — refuted by EYES-EXPERIMENT.md A) and "arch near-black" (bus LEDGER:9, sampled the
tyre). Severity taste differs by seat: Fable ACCEPT / Opus NOT YET on taxi r1 and bus r2 (taxi LEDGER:5, bus LEDGER:6), so
"stop when both ACCEPT" (WF-V7-GOLD.md:74) hands the round decision to whichever seat is stricter.

F3. Reference agreement is discovered during rounds, not at setup. Every ledger carries 3–8 `drift:` lines found by
modellers and critics mid-round; the RUNBOOK's setup audit (RUNBOOK.md:15–16) was committed at 06:55 (f996811), seven hours
after the last subject setup (0051e9c, 23:21) and during the final rounds, and has never been executed. Costs: tractor burned four rounds and ends in "owner call which one the
model should follow" (tractor LEDGER:15; side .933 → .766 while concept .853 → .925); truck r2 lost side −0.047 / top −0.022
following the concept (truck LEDGER:8); pickup front/rear/side are capped at .86–.92 by drift (pickup LEDGER:14); the taxi
top view is 12 % narrower than the concept (taxi LEDGER:3) although ortho.mjs:226–243 computes the residual (README target
±3 %, scripts/v6/README.md:24) and nothing gates on it. The forklift prior written today already says "the turnaround draws
the machine ~20–25 % wider than the concept" — the same failure is queued for the next subject. Consequence: the KEEP rule's
drift exception (MODELLER.md:33–34) depends on a drift list that is never complete, and "≥ 0.97 where the references agree"
is not computable.

F4. Eyes changed under the modellers. enclosedFg (taxi and truck re-baselined at r2: taxi LEDGER:7, truck LEDGER:12), the
truck rear `shift` +0.11 found at r3 (rear .867 → .935 = 0.07 IoU of "model error" that was registration, truck LEDGER:16),
the residuals.mjs fgMax bug that erased the truck's white body in FIT (EYES-EXPERIMENT.md:36–38), `comps --family` fixed at
r3 (24104ad), `grid --diff` / `project --frame` added r3, `profile` added r4. Three of these are detectable at setup with
no model (enclosed near-white regions, body-span asymmetry, fgMax mismatch). Each cost a re-baseline and a round of
modeller effort aimed at a registration artefact.

F5. The modeller loop is turn-hungry by design. ≥ 8 iterations (MODELLER.md:28), each = render + read up to 6 images +
chain + check-module + edit + snapshot, with a five-condition KEEP rule (MODELLER.md:33–36) the agent applies by hand.
Rounds took 30–235 calls; the opus-worker 60-turn cap was hit three times and the workaround was "run as general-purpose"
(no cap) + SendMessage (WF-V7-GOLD.md:32–33, RUNBOOK.md:20). Modellers also wrote their own tools despite the rule
(scripts/v7/README.md:5–6): 42 files (≈ 865 lines of .mjs) under school_bus/tools and delivery_truck/tools are committed.

F6. Class-config noise in every gate. PALETTE_ZONE (kernel-chain.mjs:442–468, closed list classes/vehicle.json:88) and
VEH_WHEELS fire on every subject in every round; every ledger, merge and prompt repeats "leave them" (MODELLER.md:40–41,
all five LEDGERs, every merged GATE block). The final taxi chain prints `pass false` with 10 PALETTE_ZONE violations. A
medium-effort modeller either spends turns on them or renames zones into the closed list and loses colours; `pass` cannot
be used as a boolean.

F7. The workflow has no convergence rule of its own. Every subject ended on the 4-round cap (each ledger's END line;
WF-V7-GOLD.md:74–75). Round 4 was a polish round on three subjects — bus .967/.970/.943/.973/.961 → .970/.968/.942/.974/.961,
pickup r3 → r4 identical to 3 dp, taxi side +.004 — with bus r4 "measured worse" on three of six items (bus LEDGER:10). On
the other two it was a structural round decided by a variant table (truck top +.016 / rear +.009 from the tandem table,
truck LEDGER:19; tractor concept +.057 from the proportion table, tractor LEDGER:13) — experiments that belonged in the
round where the CONFLICT first appeared (truck r1-merged.md K3; tractor LEDGER:11 "not re-proportioned").

F8. Prompts and runbook assume a max-effort reader, and contradict each other. RUNBOOK.md:19 launches the modeller with
"Nothing else" but :27–28 launches critics "+ the subject's known facts"; CRITIC.md:12 names the view `side_right` while every
views.json names it `side` (CRITIC.md:24 uses `side`); the round-start IoU, dims, drift and tried lists are pasted by hand;
WF-V7-GOLD.md:83–84 "Starts" is stale; research/ holds 45 files a wandering agent can read instead of the rules. The
protocol lives in three places (WF-V7-GOLD "Round protocol", RUNBOOK §1, MODELLER "Loop").

F9. Repo bloat via `git add -f out/ref/gold/<s>` (RUNBOOK.md:26; .gitignore ignores `out/`). 851 tracked files under
out/ref/gold: 530 PNGs = 171 MB (314 critic crops, 210 view PNGs — nearly all of intermediate snapshots), 159
model-vNN.mjs snapshots, 42 subject-local tool files, view0/, snap/, k1/ scratch dirs. ≈ 35 MB per subject.

F10. The quality bar is asserted, not checked. "Every view reads as the concept" is a critic sentence; "≥ 0.97" is global
although four of five subjects cannot reach it on drifted views; "valid module" = check-module + chain minus a hand filter.
No single command answers "is this round done".

## 2. Changes (ranked; each implementer-ready)

### C1. `scripts/v7/round.mjs` — every mechanical orchestrator and modeller step as one command
Files: add `scripts/v7/round.mjs`; refactor `scripts/v7/inspect.mjs:104–131` so `chainCmd` is an exported
`runChain(modulePath, subjectId) → {pass, violations, advisories, tris, budget}`; reuse `viewSheet` (view.mjs:80) and
`buildVariant`/`fitFrame` (lib.mjs). Ledger becomes `out/ref/gold/<s>/LEDGER.json` (append-only, shape borrowed from
tools/BlindLoop/ledger.mjs: `{setup, rounds:[{n, role, snapshot, iou:{...}, tris, gate, text}], drift:[{views, region, text}],
tried:[{part, axis, text}], eyes:[...]}`); `LEDGER.md` is rendered from it, never hand-edited.
Subcommands:
- `iter --subject s --module m.mjs [--keep]` (the modeller's only loop command): view --zoom into `view/`, check-module,
  runChain, per-view IoU vs `view/rN-start.json`, drift exceptions from LEDGER.json, the blob table (C4); prints ONE line
  `KEEP` or `REVERT: <first failing reason>` (e.g. `front -0.013 not in drift`, `new clip a×b`, `V5_THIN grille_slat`);
  `--keep` on KEEP copies m.mjs → next `model-vNN.mjs` and `model.mjs`.
- `verify --subject s --round N` (the orchestrator gate): model.mjs byte-equals the newest snapshot; check-module PASS;
  `pass === true` after C7; no file changed under the gold dir outside {model.mjs, model-v*.mjs, view/} (fails on subject-local
  tools and crops); per-view IoU vs round start and vs `bar.json` (C3); writes `view/rN.json`; prints `PASS`/`FAIL` + `STOP`/
  `CONTINUE` (C6); exit code.
- `ledger --subject s --round N --role modeller|critic|merge|eyes|drift|setup --text "…"`: appends with IoU/tris/gate filled
  from the latest view JSON; regenerates LEDGER.md.
- `brief --subject s --round N --role modeller|critic|auditor [--seat fable|opus]`: fills every `{…}` of the role file from
  subject.json / prior.json / views.json / LEDGER.json / bar.json — dims, start snapshot, round-start IoU per view, bar per
  view, drift + tried lines, view names, the module's KNOBS list with comments and the `inspect parts` id list (so critics
  name real parts and knobs: C5), the fixed facts block (concept orthographic, cel shading, enclosedFg state), and the exact
  commands with paths filled; writes `out/ref/gold/<s>/brief/rN-<role>[-<seat>].md`. Refuses when LEDGER.json has no
  `setup.ok` (C3).
- `commit --subject s --round N --role …`: explicit pathspecs only (model.mjs, the round-end snapshot `model-rN.mjs`,
  LEDGER.json/.md, critique/rN-*.md|json, view/model-view.png + the 5 final pages + rN.json); templated message. Never `-f` a
  directory.
Effect: the orchestrator's round = brief → Agent → verify → ledger → commit → brief×2 → Agent×2 → merge (C5) → ledger →
commit: ≈ 12 tool calls, none of them judgment except reading the CONFLICT block. A medium-effort session cannot skip a
check because the check is the command. Modeller bookkeeping (snapshots, five-condition KEEP) disappears.
Verify: on the taxi gold at HEAD, `verify --round 4` prints PASS with the LEDGER:13 numbers; `iter` on model-v24 with
`view/r4-start.json` = model-v22's JSON reproduces the r4 KEEP; `brief --role modeller --round 4` diffed against the r4
prompt the orchestrator actually sent contains every value it contained.

### C2. Agent definitions + one skill; role prompts become the agent bodies' only instruction
Files (project-level, same frontmatter as C:\Users\AZAD\.claude\agents\opus-worker.md):
- `D:\Git\checkout\.claude\agents\llmm-modeller.md` — model claude-opus-5-5, effort high, maxTurns 90 (after C1/C9 an
  iteration is 2–3 calls; 8 iterations + reads + measurements + report ≈ 45; the cap is a budget, not a wall).
- `D:\Git\checkout\.claude\agents\llmm-critic-fable.md` — claude-fable-5-1, effort medium, maxTurns 30.
- `D:\Git\checkout\.claude\agents\llmm-critic-opus.md` — claude-opus-5-5, effort medium, maxTurns 30.
- `D:\Git\checkout\.claude\agents\llmm-auditor.md` — claude-fable-5-1, effort high, maxTurns 40 (C3 setup audit only).
Body of each: "Your whole task is the brief at the path in your prompt. Do not read research/ or docs the brief does not
name. Write your output to the path the brief names and return the same text. End with PASS/FAIL against the brief's
acceptance line." (The retry cap / one-excerpt rule from opus-worker.md carries over.)
- `D:\Git\checkout\.claude\skills\llmm-gold\SKILL.md` — the orchestrator procedure as a numbered command list: setup
  (C3 commands) → per round: `round.mjs brief` → `Agent(llmm-modeller, "Read <brief>")` → `verify` → `ledger` → `commit` →
  two `brief --role critic` → two Agents in parallel → `merge.mjs` → `ledger` → `commit` → read the STOP/CONTINUE line. Stop
  rules (C6) verbatim. Nothing else; WF-V7-GOLD.md stays as rationale, referenced once.
Effect: seats are pinned (no "run as general-purpose to escape the cap"), effort is pinned per role, and a medium-effort
orchestrator follows commands instead of re-deriving the protocol from three documents. Critic cost is bounded by
maxTurns, not by a sentence.
Verify: run one taxi round at medium orchestrator effort from the skill alone; count orchestrator tool calls (target ≤ 15)
and confirm no agent exceeded its maxTurns.

### C3. Setup gate before round 1: `scripts/v7/setup-check.mjs` + auditor pass + per-view `bar.json`
Files: add `scripts/v7/setup-check.mjs`; add `research/v7/AUDITOR.md` (role prompt); add `subjects/<s>/bar.json` and
`subjects/<s>/agree.json` (written by the auditor); RUNBOOK §0 becomes these commands.
setup-check (no model needed, exit 1 on any FAIL):
(a) `reg.residuals[D].maxAbs > 0.03` → FAIL naming the view (ortho.mjs:226–232 already computes it; taxi top −12 % fails);
(b) per ortho view: body-family span centre vs foreground bbox centre along `right`; |Δ| > 0.03 m without a `shift` in
views.json → WARN "shift candidate ±x m" (catches the truck rear +0.11);
(c) enclosedFg trial: under `enclosedFg: true`, list every enclosed near-white component ≥ 60 px per view + concept with
bbox/area → the auditor classifies "part" (keep on) or "hole" (add a `holes` seed or keep off); the current per-subject
guess (RUNBOOK.md:12) becomes a decision with a printed list;
(d) camera.json `provisional === false` and `residual_px < 1.0`;
(e) fgMax consistency: the value views.json declares must be the one targetState/residuals use (regression for the
EYES-EXPERIMENT.md:36–38 bug);
(f) start.mjs passes check-module and runChain (`pass === true` after C7);
(g) view names in views.json ⊆ the set the brief generator maps (side/front/rear/top; C8 fixes CRITIC.md).
Auditor pass (one Fable seat; the owner's one-judge-per-gate rule): compare each turnaround view with the concept on ≤ 8
named landmarks per view (wheel centres, roof top, nose/tail faces, flank width, ground line) with `measure.mjs comps` /
`unproject`, write `agree.json` `{view: {landmark: {turnaround_m, concept_m, delta_m}}}`, `drift:` lines into LEDGER.json,
and `bar.json` `{view: {bar: 0.97 | lower, why}}` (bar lowered only where a drift line caps it, with the reason). Rule,
mechanical: any landmark Δ > 5 % of that view's dimension → the view is regenerated (GPT, measured proportions in the
prompt) and the audit re-runs; otherwise round 1 starts. `round.mjs brief` refuses until LEDGER.json has `setup.ok`.
Effect: three of the five mid-project eye fixes (enclosedFg, shift, fgMax) become setup findings; the tractor's four
rounds become one setup decision; "≥ 0.97 where the references agree" is a per-view number the stop rule can use (C6);
modellers stop discovering drift with IoU losses of 0.05–0.13.
Verify: run setup-check on the five gold subjects: it must FAIL taxi (top residual), WARN delivery_truck rear (shift),
list the taxi sign / headlights and the truck seams under (c), and pass school_bus; run it on forklift and garbage_truck
before their round 1 (the forklift prior already reports a 20–25 % width drift — the gate must catch it).

### C4. Eyes: a silhouette-diff blob table in the view JSON, and the KEEP verdict from it
Files: `scripts/v6/view.mjs` (after line 116, where `masks[v]` exist): for each view run `blobs()` (judge.mjs:99–121,
already exported-able) on refOnly (`refFg && !modelFg`) and modelOnly masks with `idOf = partId` (extend
`orthoTiles`, judge.mjs:258–268, to keep `partId` per tile; the concept has `proj.partId`); emit `metrics.blobs[v] =
[{kind: "missing"|"extra", px, m2, bbox_m|bbox_px, centroid, part}]`, top 6 by area, and print them as `[view]` lines.
Do NOT feed the existing `metrics.viewRows` (judge.mjs:130–200, family-component matching) to agents: on the final taxi
they say `mirror_head_l 1.81 m too narrow along z` and `stripe_l 3.02 m too wide along z` — family rasters merge parts;
hide them from the v7 JSON.
Effect: the modeller's "name the 3 biggest differences" (MODELLER.md:29) becomes reading five text lines; image reads drop
from six per iteration to the one page that matters; critics get their silhouette items pre-anchored (C8). Numbers instead
of eyeballing is the single largest medium-effort equaliser.
Verify: on taxi model.mjs the top blob per view must coincide with the r4 critique items (front/rear: sign end faces;
side: tyre crescents; top: mirror heads at z .875–1.025 vs .68–.84); on delivery_truck model-v24 the side blob must be the
cab/box gap (r2 A1).

### C5. Structured critique + `scripts/v7/merge.mjs` — the merge becomes a script
Files: `research/v7/CRITIC.md` (output section); add `scripts/v7/merge.mjs`; `scripts/v7/lib.mjs` gets a part-id normaliser
(strip `_l/_r/_fl/_rr/\d+` suffixes as inspect.mjs:50 does).
Critic writes `critique/rN-<seat>.md` (unchanged format, shorter: C8) AND `critique/rN-<seat>.json`:
`[{n, severity, views[], part (a module part id or family from the brief's list), knob (a KNOBS name or null), axis
(x|y|z|r|colour|shape|count), dir (+|-|0), current, target, amount_m, reference (side|front|rear|top|concept), evidence
(the measure command + numbers, required for MAJOR), text}]`.
merge.mjs rules (deterministic; prints rN-merged.md in today's A/B/K/C format + a `stop:` line for C6):
key = (normalised part, axis). Both seats, same dir, amounts within 2× → A (both amounts kept). Both seats, opposite dir or
> 2× → CONFLICT; a CONFLICT whose part is a body/proportion family (from the class `lengthRoles`) → the EXPERIMENT block.
One seat MAJOR with `evidence` → B; MAJOR without evidence → C flagged `unmeasured` (this alone would have demoted the
"arch near-black" and "perspective" MAJORs). One seat MINOR → C. Key present in LEDGER.json `tried[]` → TRIED with the
ledger text. Any item with `knob` set and two numbers → a ready command
`node scripts/v7/variants.mjs --subject s --module … '{"<knob>":a}' '{"<knob>":b}' '{"<knob>":(a+b)/2}'` in a VARIANTS block
(the truck r4 tandem and tractor r4 proportion tables were exactly this, built by hand). Unmatched items are listed under
their seat, never silently merged.
Effect: the 15 hand merges become 15 script runs; the orchestrator reads only CONFLICT/EXPERIMENT; matching errors at
medium effort vanish; numeric items reach the modeller as a one-command table.
Verify: transcribe the committed pickup r2 and delivery_truck r2 critiques into the JSON once; merge.mjs must reproduce
the committed rN-merged.md partition (A/B/K/C membership; the demotion rule is the only allowed difference).

### C6. Stop rules and budgets that converge on numbers
Files: `research/v7/RUNBOOK.md` §1 (rewrite the stop rule), `round.mjs verify` (STOP/CONTINUE), `merge.mjs` (`stop:` line),
the agent definitions (maxTurns), `research/v7/CRITIC.md` (MAJOR definition).
Rules: STOP when (the merged list has no A and no B) OR (every view's Δ IoU over the last round < 0.003 and no A) OR
(round = 3). Cap 3, not 4 (F7). A single seat's ACCEPT is not a stop and both ACCEPTs are not required. MAJOR is
operational, not "at a glance": a measured discrepancy ≥ 0.05 m or ≥ 3 % of the view's dimension, or a missing / extra /
wrong-count feature — else MINOR; a MAJOR without `evidence` is MINOR (C5). Per-view bars from bar.json replace the global
0.97 in `verify`. Budgets: critic maxTurns 30, modeller maxTurns 90 with ≥ 5 iterations (C9), one experiment table per
CONFLICT (no re-runs), and `round.mjs` logs wall-clock per step. Drop the orchestrator's "one cheap measurement first"
(WF-V7-GOLD.md:38–40) — the evidence field replaces it.
Effect: one round less per subject at a cost of ≤ 0.004 IoU on the polish subjects (bus, pickup, taxi); the truck and
tractor round-4 gains were experiment tables, which C5 issues in the round the CONFLICT first appears; no round is driven
by one seat's severity taste; no unmeasured MAJOR reaches the modeller.
Verify: replay on the five ledgers — the cap is the binding rule on all five (the Δ rule is forward-looking: it refuses a
round after a no-change round, which never occurred because the cap struck first); record the round-4 IoU given up per
subject (bus ≤ .003, pickup ≤ .001, taxi ≤ .004) and confirm the truck/tractor tables are what C5 would have emitted at r2.

### C7. Close the class-config gaps so the gate is a boolean
Files: `src/validate/kernel-chain.mjs:442–468` (`validatePaletteZone`: accept, in addition to the class list, the keys of the
subject's `views.json families.table` and an optional `subjects/<s>/palette.json` list when the chain runs with a subject);
`src/validate/rules/vehicle.mjs` VEH_WHEELS (read `prior.json` `wheels: {count, axles, radii: [...]}` when present — truck
6/3, tractor two radii); `scripts/v7/inspect.mjs chain` and `round.mjs` pass the subject's extension in `opts`;
`classes/vehicle.json:87–88` documents the extension; MODELLER.md:40–41 and every GATE paragraph are deleted.
Effect: `pass` means pass; every prompt, ledger line and merge loses a paragraph; a medium-effort modeller cannot mistake
10 PALETTE_ZONE rows for work or rename zones into the closed list.
Verify: runChain on the five gold model.mjs → `pass true`, 0 violations; a module with a genuinely unknown zone still
fails; the taxi's `sign` resolves from its families.table and `well`, `trim`, `handle`, `panel` from a new
subjects/taxi/palette.json.

### C8. Critic prompt for a medium-effort seat
Files: `research/v7/CRITIC.md` rewrite. Inputs: the sheet, the five pages, the blob table (C4), the part-id and KNOBS
lists, bar.json, drift + tried lines — all in the brief (C1), view names filled from views.json (fixes CRITIC.md:12).
Output: ≤ 8 items, each ≤ 2 lines in the .md plus the JSON record (C5); a MAJOR carries an `evidence` line; items anchored
on the blob table first, then what the diff cannot show (colour, missing features, shape inside the silhouette, counts).
No crops in the repo: measurement images go to the agent's scratchpad; the `critique/rN-<seat>/` directory is gone. Drop
"about 30 tool calls" (the agent definition enforces it) and the "art director" framing; add the facts block ("the concept
is orthographic — do not raise perspective; the concept wins except inside a drift line; the model is cel shaded").
Effect: critic 25–75 min → 10–20 min, 25–115 calls → ≤ 30, 49–63 crops → 0 committed; the lists become mergeable.
Verify: one critic round on the taxi final at medium effort: ≤ 30 calls, ≤ 8 items, every MAJOR with evidence, and it
finds the two open r4 items (sign end faces, mirror head height).

### C9. Modeller prompt for a medium-effort seat
Files: `research/v7/MODELLER.md` rewrite. Loop = edit → `node scripts/v7/round.mjs iter --keep` (one command, one verdict
line, snapshot on KEEP); ≥ 5 iterations (the "8" at MODELLER.md:28 is arbitrary; r4 rounds had < 5 useful changes); the
three biggest differences = the blob table; measure before a B/C/K item stays (measure.mjs); knob-level items run the
VARIANTS command from the merge instead of hand edits; write nothing outside model.mjs / model-vNN.mjs (verify fails the
round otherwise — this ends subject-local tools); report ≤ 10 lines (the iter JSON already holds the numbers); the drift
exception prose goes (the script applies LEDGER.json drift); kernel import path and tool list stay.
Effect: 30–235 calls → 40–90 within maxTurns 90; the KEEP rule cannot be half-applied.
Verify: rerun the taxi r4 item list with the new prompt at medium effort: the round ends inside maxTurns with `verify`
PASS and no view below its bar by more than 0.01.

### C10. Start from the nearest gold, not a blockout
Files: add `scripts/v7/scaffold.mjs --subject s --from out/ref/gold/<g>/model.mjs` → copies the module to
`out/ref/gold/<s>/start.mjs`, sets L/W/H/wheelR KNOB values from `reg.dims` / prior.json, remaps the palette from the
subject's `families.table`, rewrites the header, runs `frame.mjs --write` and `round.mjs iter`; RUNBOOK §0 rule: the start is
the nearest gold of the class (sedan → taxi, box truck → delivery_truck, cab-over → school_bus, machine → tractor), a
blockout only when nothing is close. Delete WF-V7-GOLD.md:83–84 "Starts".
Evidence: the one hand-built start (pickup) opened at concept .979 in r1 (pickup LEDGER:2); blockout starts opened at .853
(tractor), .874 (taxi, 19 iterations to .940), .961 (truck).
Effect: round 1 spends its iterations on the subject's features instead of rediscovering a vehicle body; on close subjects
one round is saved.
Verify: scaffold forklift from tractor and garbage_truck from delivery_truck; `iter` on each scaffold must beat the
existing `out/ref/gold/<s>/start.mjs` on the concept IoU.

### C11. Stop committing crops, scratch dirs and intermediate snapshots
Files: `tools/LLMModeling/.gitignore` add `out/ref/gold/*/critique/r*-*/`, `out/ref/gold/*/tools/`,
`out/ref/gold/*/view/model-v*`, `out/ref/gold/*/view0/`, `out/ref/gold/*/snap/`, `out/ref/gold/*/k1/`,
`out/ref/gold/*/brief/`; `git rm -r --cached` the 314 crops, the 42 tool files, the intermediate view PNGs (210 tracked; keep the
final `model-view.png` + 5 pages per subject) and the mid-round `model-vNN.mjs` (keep one `model-rN.mjs` per round, copied by
`verify`); `round.mjs commit` is the only commit path (explicit pathspecs; RUNBOOK.md:26 `git add -f out/ref/gold/<s>` is
deleted).
Effect: ≈ 1 MB per subject instead of ≈ 35 MB; the history stays in git; commits need no judgment.
Verify: `git ls-files out/ref/gold | wc -l` ≈ 100 (from 851); tracked PNG bytes under gold < 10 MB.

### C12. One procedure, one place; remove the contradictions
Files: `research/v7/RUNBOOK.md` = the procedure (or the SKILL.md, with the RUNBOOK a pointer); `research/WF-V7-GOLD.md`
keeps rationale + rules only — delete "Orchestrator notes" lines 29–46 once C1/C3/C5 enforce them, delete "Starts";
fix RUNBOOK.md:19 vs :27–28 (the brief carries the facts for both roles), CRITIC.md:12 (`side`), MODELLER.md/CRITIC.md
class-config paragraphs (after C7); role files contain only what the brief generator fills; the KEEP rule and the round
protocol appear once (in MODELLER.md as "run iter", in the skill as the sequence).
Effect: a medium-effort orchestrator reads one file plus generated briefs; no rule is stated twice with different words.
Verify: `grep -n "{" research/v7/*.md` shows placeholders only in MODELLER/CRITIC/AUDITOR and every one is filled by
`round.mjs brief`; no sentence of the protocol exists in two files.

## 3. Delete or simplify
- Delete `out/ref/gold/school_bus/tools/` (24 files) and `out/ref/gold/delivery_truck/tools/` (19 files): superseded by
  scripts/v7 (6fcc9b0 "verified equal to the subject-local tools").
- Untrack the 314 critic crop PNGs, `view0/`, `snap/`, `k1/`, intermediate `view/model-vNN-*.png`, mid-round `model-vNN.mjs`
  (C11). The .md/.json critique and the round-end snapshot are the deliverables.
- Delete the "both critics ACCEPT" stop, the 4-round cap, the orchestrator's "one cheap measurement first", the hand merge,
  the hand `cmp`/chain verification and `git add -f` (C1/C5/C6/C11 replace each).
- Hide `metrics.viewRows` from the v7 JSON (C4): family-matching rows with wrong part-level numbers; keep the code for the
  v6 loop only.
- MODELLER.md "≥ 8 iterations" → "≥ 5 with `iter`"; the five-condition KEEP paragraph → one command; the drift-exception
  prose → LEDGER.json.
- CRITIC.md "≤ 12 items, ~30 tool calls, crops under critique/…" → "≤ 8 items, JSON + md, no repo crops"; maxTurns does the
  budgeting.
- Keep two critic seats (owner 2026-09-27; single seats flip-flop, and the two seats caught each other's wrong MAJORs) but at
  medium effort and 30 turns; they run in parallel, so wall-clock is unchanged.
- Do not port v7 onto tools/BlindLoop/orchestrator.mjs: its worker is target-blind (roles/worker.md), v7's modeller must see
  the references. Borrow only ledger.mjs (append-only factual JSON, `workerHistory`) and the preflight pattern (frozen files,
  exists checks) for C1/C3.
- Keep scripts/v7 measure/frame/variants/inspect as they are (cheap, used every round); keep EYES-EXPERIMENT.md as evidence,
  referenced from the facts block only.

## 4. Cost model (per model, estimate with the assumptions shown)
| | today (5 subjects, 09-26 22:56 → 09-27 07:08) | after C1–C12 |
|---|---|---|
| modeller | 4 rounds × 15–85 min, 30–235 calls, uncapped seat | 3 rounds × ≤ 90 turns (≈ 30–40 min), image reads ≈ 1 per iteration |
| critics | 6–8 seat-runs × 25–75 min, 25–115 calls, 49–63 crops | 6 seat-runs × ≤ 30 turns (≈ 10–20 min), 0 crops |
| orchestrator | 3 hand merges (25–57 lines), 7 commits, ledger prose, 1–2 hand measurements, max effort | ≈ 12 calls per round, reads one CONFLICT block, medium effort |
| eyes | 3 re-baselines mid-project, 2 tool bugs found by agents | setup-check + auditor before round 1 |
| repo | ≈ 35 MB and ≈ 170 files per subject | ≈ 1 MB, ≈ 20 files |
| agent time | ≈ 8.5 h | ≈ 3–3.5 h (3 × 40 + 6 × 15 min + orchestrator) |
Quality: unchanged bar, now checked per view against bar.json by `verify`; the parts of the bar that rounds 4 bought
(≤ 0.008 IoU) are given up by the cap of 3.
