# LLMModeling

LLM-driven hard-surface 3D modeling for Checkout: buildings, vehicles, props,
robots, furniture. Cartoon isometric low-poly, flat vertex colours, one
material, one draw call, glTF out. Goal: beat `anyCreature` and `img2threejs`
on geometric correctness (nothing floating, nothing paper-thin, logical
scale/placement) and on iteration speed, judged under `tools/BlindLoop`.

**Core rule: the LLM never writes geometry or a world coordinate.** It emits an
attachment program (`spec.json`); a deterministic JS compiler resolves every
transform; numeric validators gate before any pixel exists.

## Read order

1. `PLAN.md` — merged architecture + milestones (authoritative).
2. `research/` — evidence: 01 source repos, 02 correctness, 03 landscape,
   04 image + judge, 05 local reuse, 06/07 independent proposals, 08 exchange.
3. `refs/README.md` — frozen TARGET inventory.

## Layout (target state; see PLAN.md §6)

- `dsl/` — DSL spec doc, JSON schema, worked examples
- `src/` — geom fork, compiler, validators, studio/capture, exporters
- `prompts/` — lister, builder tiers, repair
- `scripts/` — camera solve, intake, gen, check-spec, qa-sheet
- `refs/` — frozen reference images + derived camera/parts/mask
- `subjects/<name>/` — spec.json, solved.json, report.json
- `test/` — determinism, budgets, broken-fixture validator tests
- `out/`, `cache/` — gitignored

## Rules

- Follows `tools/BlindLoop/BLIND_LOOP.md`. Never edit its frozen files.
- Copy from `tools/CharacterStudioV2`, never import across project roots,
  never modify it (it is a live loop target).
- Blender never in the inner loop. Three.js + Node only.
- Threshold numbers in `src/validate/limits.json` are owner-ratified.
- Port 4210.

## Status

Blind Loop passes 2026-09-12 (runs r7–r11b, three-model split live): merged sidewalk-apron, clothesline-shirts, fire-escape-open, storefront-awning, roof-bulkhead-tone, fire-escape-width, street-props-front, awning-shape. Winners: Astra 4, Opus 4. Post-merge repairs after stacked merges (props re-anchored, awning under the landing, occlusion by protrusion against element rects). Final `subjects/tenement_block_llm` 7644 tris, V0–V7+V10 clean; evidence out/m4/final-target.png. Rule: one item per orchestrator invocation, validate + commit after every merge (WORKFLOW §3b). Next items: fire escape belongs on the LEFT bay (judges chose the right half), mint side-face windows, window count per bay.


Target generation 2026-09-12: `scripts/make-target.mjs <subject>` generates a frozen-style reference through the owner's Google AI Ultra subscription via Antigravity CLI (`agy --print` + generate_image; no API key). v1 tenement frozen provisionally as `refs/tenement-iso.png` (= `refs/tenement_block.png` for gen.mjs), provenance in `refs/tenement-iso.prompt.md`. Owner may replace with the original. Camera solve (`scripts/solve-camera.mjs`) in progress.


M4 done 2026-09-12: first real Blind Loop round on `subjects/tenement_block_llm` (BASELINE) vs TARGET = M2 hand render (reference PNG still not on disk). Item `facade-palette`: 3 blind worker seats, 3 blind judge seats via relay adapters (`tools/BlindLoop/adapters/*-relay.mjs`, no CLI login needed), all candidates passed the validator gate, votes B,A,B, cand3 merged, BASELINE judged worst 3/3. Run log `tools/BlindLoop/runs/m4-tenement-r3/log.md`. Fixes on the way: adapters need absolute paths (worker cwd = worktree); `hard_surface/node_modules/.bin` was missing so candidate servers could not start (npm install). Remaining items `clothesline-shirts`, `fire-escape-open` unrun. Merged spec change is uncommitted (owner call).


M6 done 2026-09-12: the three DSL gaps the blind builder seats reported are closed. (1) Composites are parents — `attach.to` takes a composite id (resolves to its root sub-part) or `composite.sub`; expansion rewrites both, so V2/V3/V6 still only ever see ordinary parts. (2) Per-instance children are the DEFAULT: a child of a `repeat`ed/`mirror`ed parent is expanded once per parent instance (`child#k`, `child~m`), `attach.instance: 0` opts back out to the anchor of each group. That closed the cart.json MVP-STUB — the mirrored wheel now carries a hub on both tyres with no spec edit. (3) `alignU` (start/center/end) anchors the child along the face's u axis, the twin of `align` on v; with it the new `railing_open` composite is real open bars (bottom rail + N posts + top rail, no infill web) and `railing` stays the web version the frozen M2 baseline references. New example `dsl/examples/balcony-open.json` (subject `balcony_open`), in `npm run check`. BASELINE fence held: `subjects/tenement_block/spec.json` still hashes `h32:a7e21c69` and its fresh `view=target` capture is byte-identical to `out/m2/tenement-target.png` (sha256 650df10c…). 100 tests. Evidence out/m6/.

M5 done 2026-09-12: generality proven on a vehicle. New contacts hangs-below/embedded, V9 symmetry advisory, vehicle V7 rows (wheel DIAMETER/length 0.1–0.2, Fable ruling; class-scoped), `wheel` composite (axis-x ring), `gen.mjs --inventory`. Blind Opus seat authored `subjects/pickup_truck_llm` from `refs/pickup_truck.README.md`: 3 tiers, 0 repairs, FINAL PASS, 1180 tris. Evidence out/m5/. 89 tests. Look gap: wheels mostly hidden by the full-width chassis. M4 (first Blind Loop pass) still parked on owner gates: BLINDLOOP_CONFIG one-liners, clean committed tree, CLI /login, reference PNG, limits ratification.


M3 done 2026-09-11: LLM-authored tenement via `scripts/gen.mjs --runner file` (lister = Fable 5.1 on refs/README.md text, builders A/B/C = Opus 5 seat under a blindness rule; baseline hidden from the tree during the run). 3 builder calls, 0 repair prompts, FINAL PASS, 41 parts, 7860 tris. Evidence out/m3/llm-target.png. First attempt was VOIDED (seat copied the hand spec; byte-identical PNG) — M4 candidates must run in worktrees with no access to other specs. Unattended `--runner cli` still blocked on CLI login. Next: M4 first Blind Loop pass (owner: BLINDLOOP_CONFIG one-liners, TownhouseStudio, CLI login, reference PNG).



M3 pipeline built 2026-09-11; live run pending CLI login / file runner. `prompts/{lister,
builder-a,builder-b,builder-c,repair}.md` + `scripts/gen.mjs` (lister -> builder A/B/C ->
validate -> auto-repair -> REPAIR seat, <=2 per tier; V0-V3 gate after A and B, full
V0-V7 + V10 after C; `sha256(promptTemplate + inputs + dslVersion + seat + tier)` cache in
`cache/specs/`). The model call is pluggable because this machine has no API key and the
standalone CLI is not logged in: `--runner cli` (spawns `claude -p … --output-format json`),
`--runner file` (writes `cache/pending/<hash>.prompt.md` + `.meta.json`, exits 3, resumes when
a `.response.md` appears), `--runner fake` (canned, for the suite). `npm run check` 74/74.
Evidence: `node scripts/gen.mjs tenement_block --runner fake` -> `subjects/tenement_block_llm/`
5 calls, 1 repair prompt, FINAL PASS, 40 parts — those artefacts are the CANNED run, not a
model's work. Deviations: no `refs/tenement_block.png`, so the LISTER is fed `refs/README.md`'s
inventory text; MEASURE (Grounded SAM / clicked boxes) is not implemented, so every `rel_size`
stays a hypothesis. Next: owner `/login`, then M3 for real.


M2 done 2026-09-11 — facade grammar + composite library + the full tenement. Nine composites
(`railing`, `stairFlight`, `landing`, `pipe`, `vent`, `awning`, `trashcan`, `crate`, `acUnit`),
eight prims, six facades on the subject (two of them sharing a face so a ground floor can run
`occlude:false` under an `occlude:true` upper). `subjects/tenement_block/spec.json` PASSES
V0-V7 + V10 at 7612 / 8000 tris, 188 solved parts. `npm run check` 66/66. Evidence:
`out/m2/tenement-target.png`, `out/m2/facade-demo.png`, `out/qa/tenement_block-{target,
threeQuarter,back}.png` + `-sheet.html` (`scripts/qa-sheet.mjs`, `?view=back` added to app.js).
Camera still provisional (theta 30, phi 45) until `refs/tenement-iso.png` lands, so the target
still is NOT the judged framing yet. Awaiting owner taste gate; next M3.

M1 done 2026-09-11 — validators V0-V7 + V10, limits.json (every number `_ratified:
false`), repair, check-spec, 20 broken fixtures, studio overlay. `npm run check` 46/46.
build+V0-V7+V10 on the tenement 28 ms (budget 300 ms). Target capture sha unchanged from
M0 (`9166a66e…`, out/m1/cap-m1-target.png == out/m0/cap4.png) — validators change no
pixels. Overlay evidence out/m1/overlay-v{2,3,5}-*.png. Camera still provisional
(theta 30, phi 45) until refs/tenement-iso.png lands. Next: M2 (PLAN §7).

M0 done 2026-09-10 (evidence in out/m0/cap4.png, byte-identical x2, 428 tris, build+V0 2.3 ms). FORK-FIX in src/geom.js loft(): caps were inside-out for bevelBox/plate.

### V2 test project (2026-09-12) — `V2-TEST-PLAN.md`
- S1 PASS: `src/kernel/*` (manifold-3d 3.5.3), `check-module`, `bench-kernel`, `facade_brick`
  subject; smoke 200 tris, edit-to-preview 100 ms in node, 3× capture byte-identical.
- S2 PASS: `src/validate/kernel-chain.mjs` (V1′ V5 V2′ V3′ V6′ V4 V7 V10 on real surfaces via
  manifold intersect + three-mesh-bvh), 4 fixtures each fail on own code, `pass.mjs`, `measure.mjs`.
- S3 PASS: dry pass — Astra named the awning green from `-i refs/tenement-iso.png`; 19.5 s,
  10 009 tokens. Ruling: MIN_FEAT 0.06 applies to every part incl. door leaf (§2 example restated).
- S4–S8 PASS (P0–P4, Astra gpt-6-astra high via `scripts/pass.mjs`, target image in context every
  pass): massing 204 tris → openings 966 (real reveals, storefront cut, arched door) → trims 1258
  (stepped cornice, sills, wedge awning) → ironwork 2554 (147 parts, open fire escape) → palette.
  0 repairs in 5 passes; 1057 s Codex wall-clock, 218 602 tokens total (over the unratified
  15k/pass line every pass); build+validate ≤ 2.4 s; 3× final capture byte-identical
  (`out/facade/final/`). Stills `out/facade/P*/target.png`, GLB `out/glb/facade_brick.glb`.
  Owner gates still open: arch on brick, ironwork palette (P4 lighter than target), §1 sentence.
- Owner 2026-09-12: "v2 is significant improvements" — v2 route ratified; v1 DSL path retired for new subjects.

### Workflow loop (Astra + Fable audits → merge → Opus → rerun), 2026-09-13
- r1 `research/WF-LOOP-R1.md`: 13 logic errors → closed roles, staged census, bearing, landing gap,
  ladder access, deck gap, undeclared clash, handedness, camera preflight. Run 2: all rules PASS.
- r2 `WF-LOOP-R2.md`: renderer key light darkened the front (0.51×) → flat capture; likeness never
  measured → `likeness.mjs` + `regions.json`; metres invented → `layout.json` + V12_LAYOUT; author
  sees own render in the repair prompt; seats 5→3; palette by `calibrate-palette.mjs`. Run 3: PASS.
- r3 `WF-LOOP-R3.md`: frozen layout numbers were unmeasured (front+side px; my 1.8 W depth) →
  `measure-target.mjs` derives every key with evidence, `--check` + refusal on unverified keys,
  front-quad LK_AREA, per-instance visibility, visual authority over numeric PASS. Run 4: PASS,
  2980 tris, 3× capture identical (`out/facade/run4/`), residual: lower-landing iron value, AC hue/size.
- Standing rules learned: no hand-typed number in a frozen file; colour is never the seat's job;
  a numeric PASS never overrules a visible mismatch; Codex drops ~1 in 5 seats (retry loops).
- WORKFLOW-V3 §7 items 1–4 landed (Opus 5, 2026-09-13): `measure-target` emits the measured
  front-face quad (`_frame.quadPx`) and likeness uses it (no fallback); pass items cite `{MIN_FEAT}`
  from the gate config and the mangled P1 sentence is fixed; `calibrate-palette` solves
  `meta.shade.sideTint` in linear light from the target (−0.411) and runs after every author
  mutation; `pass.mjs` exits 3 on deterministic refusals (never retried), writes `verdict.json`
  (FAIL | REVIEW_PENDING | ACCEPTED_WITH_RESIDUALS | PASS, hash-bound). Run-4 final pass
  re-gated: ACCEPTED_WITH_RESIDUALS (LK_VALUE lower landing, LK_HUE ac, LK_AREA grey).
  Routing from here: Opus 5 + GPT Astra high only.
- WORKFLOW-V3 items 5–7 landed (Opus 5 jobs, 2026-09-13): subject manifest (`subjects/<s>/subject.json`,
  `scripts/subject.mjs`) + class prior (`classes/building.json`, `classes/building.md`,
  `src/validate/rules/building.mjs`) replace the per-script constants; harness-inferred contact
  (authors no longer declare every `touches`); seat adapters `scripts/seats/{codex,relay,fake}.mjs`
  with `pass.mjs --seat … --seat-mode text|agent` (default text: the prompt carries API, class rules,
  module, item and the cited layout numbers; the model replies with the whole module in one fence);
  MISSING KEY backlog. Proof: live Astra text-mode P0 PASS, 0 repairs, 85 s, 13 669 tokens (agent-mode
  P0 in run 4: 382 s, 96 k). Run 4 re-gates unchanged (ACCEPTED_WITH_RESIDUALS). 207 tests.
- WORKFLOW-V3 items 8–10 landed (Opus 5 jobs, 2026-09-13):
  - item 8 `scripts/template-building.mjs` — P0 massing + P1 openings/trims built from layout + census with
    no seat (P1 gate + likeness PASS, 42 parts, 928 tris); W/H rule documented in the script.
  - item 9 `K.assemble.{grate,landing,ladder,flight,frame}` (`src/kernel/assemblies.mjs`) — ironwork and
    frames that pass the buildability gates by construction, no `touches`.
  - item 10 vehicle class (`classes/vehicle.*`, `src/validate/rules/vehicle.mjs`: ground, wheels, mirror),
    `scripts/measure-vehicle.mjs`, subject `pickup` (target `refs/pickup_truck.png`, camera θ 29.34 φ 44.81).
  229 tests. Live proofs running: pickup P0 Astra text seat; building template + one Astra P2 seat.
- Live proofs (2026-09-13): building v3 = template P0+P1 + one Astra text P2 seat reaches near run-4 likeness
  at 54.5 k tokens / 348 s (run 4: 350 k / 1571 s), gate FAIL by 4 tris + 3 LK_AREA rows
  (`out/wf-loop/v3-proof/`); pickup P0 first Astra text seat FAIL (smoke anchoring, uncalibrated tread zone,
  repair broke V3). Harness fixes pushed: a repair that leaves the pass worse is reverted
  (`repair-reverted.md`), and every author prompt shows the triangle budget left. In progress: vehicle
  template + palette closure; building backlog keys (sign box, AC, storefront, door, landing sizes), template
  embeds, landing guard-rail rule.
