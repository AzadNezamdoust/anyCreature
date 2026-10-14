# M1 brief — Validators bite (implementer seat, Opus 5)

Read first: `tools/LLMModeling/PLAN.md` §1.3, §2 (validator table), §5, §7 M1; then the
existing code `src/compile/*.js`, `src/prims.js`, `src/validate/v0.js`, `src/geom.js`
(loft/bevelBox/plate/paint/triangleCount only), `src/app.js`, `test/*.test.js`,
`research/02-correctness.md` §T2–T3 (validator semantics), `research/08-opus-revision.md`
§4 G3/G7. M0 is done and green (16 tests); do not regress it. Do NOT touch
`tools/CharacterStudioV2/` or BlindLoop frozen files. Do not commit.

## Scope

Validators V1–V7 + V10 in Node, `limits.json`, report + repair, 20 broken fixtures, in-page
overlay. Nothing else (no facades, no composites, no LLM, no V8/V9, no SAM).

### Files
1. `src/validate/limits.json` — single owner-number file, every value flagged
   `"_ratified": false`: `epsAbs 0.01`, `epsRel 0.005`, `captureSize 900`, `fill 0.86`,
   `minFeaturePx 3`, `styleFloor {building: 0.06, prop: 0.04, vehicle: 0.04}`,
   `triBudget {building: 8000, prop: 2000, vehicle: 4000}`, `overlapDuplicate 0.9`,
   `overlapClash 0.2`, `contactSampleFrac 0.9`, `v7 {door_h:[2.0,2.4], step_rise:[0.14,0.20],
   railing_h:[0.9,1.1], parapet_h:[0.3,1.2], window_h_lt_floorH:true, awning_bottom_ge_door_top:true}`,
   `repairGapMaxEpsMult 5`, `repairGapMaxChildFrac 0.10`, `maxRepairPasses 2`.
2. `src/validate/index.js` — `validate(spec, solved, geometryInfo, limits) → report`. Runs
   V0 (existing) then V1, V2, V3, V4, V5, V6, V7, V10 in that order; stops at the first
   failing *blocking* class but still records advisories. `report = {pass, violations:[{v,
   part, measured, limit, hint, blocking:true}], advisories:[…], text}` where `text` is the
   ≤8-line rendering, hints state the move in metres (e.g. `move balcony_r 0.12 m along -Z
   to touch mass_r`). Also export `validateSpec(spec, limits)` that compiles internally.
3. `src/validate/v1.js` — per-prim: non-indexed tri count even, every edge shared by exactly
   2 triangles with opposite direction (watertight + consistent winding), χ = V−E+F ==
   2−2·genus using the prim's declared genus. Build a vertex map with 1e-6 quantisation.
4. `src/validate/v2.js` — declared contact real. For each attached part: sample the child's
   contact face (the face whose outward normal is −n, per `resolve.js`; 5×5 grid in
   world space) and measure signed distance to the parent's solid. For M0 prims all parts
   are boxes/bevelBoxes: implement signed distance to an oriented box (use part matrix
   inverse + AABB in part-local space; treat bevelBox/plate as their bounding box, note
   `// MVP-STUB`). Rules: flush / rests-on-top: |d| ≤ EPS on ≥ contactSampleFrac of samples
   (d measured from the child face *before* embed, i.e. expected penetration == embed ±
   EPS); socket: penetration ∈ [0.5, 1.5]·embed. EPS = max(epsAbs, epsRel·bboxDiag).
5. `src/validate/v3.js` — contact graph: AABB-prefiltered pairs, min distance between
   oriented boxes ≤ EPS (implement box–box distance via sampled faces or SAT gap; document
   choice). Graph must be connected and every part must reach a `ground` part. Violation
   names the orphan cluster and its nearest part with the gap in metres. No manifold union
   in M1 (flag only, `// DEFERRED: manifold-3d cross-check`).
6. `src/validate/v4.js` — ground parts min-y == 0 ± EPS; projected centre of mass (volume-
   weighted box centres) inside convex hull of ground-contact footprint (2D hull of ground
   parts' xz AABBs).
7. `src/validate/v5.js` — min feature: every part's min dim ≥ MIN_FEAT where MIN_FEAT =
   max(styleFloor[class], minFeaturePx·PX), PX = (bounds.h / fill) / captureSize
   (orthographic frustum from app.js frameTarget — read it and match exactly). Any `repeat`
   with pitch − extent-along-axis < 2·PX = sub-pixel.
8. `src/validate/v6.js` — pairwise box intersection volume ÷ smaller volume (oriented boxes:
   for M1 compute in world AABB space and mark `// MVP-STUB: AABB not OBB`). > overlapDuplicate
   → duplicate; between overlapClash and overlapDuplicate without contact socket/embedded and
   not a declared parent–child pair → clash.
9. `src/validate/v7.js` — role table from limits.v7. Roles present in M0 spec: door, step,
   parapet, massing, bulkhead, pipe; add railing/window/awning rules as data, skipped when no
   part has the role.
10. `src/validate/v10.js` — triangles ≤ triBudget[class]; no NaN/Inf in positions/colours;
    exactly one geometry (the compile output) — move the assertions from test/budget.test.js
    into this validator and keep the tests calling it.
11. `src/validate/repair.js` — `repair(spec, report, limits) → {spec, applied:[…]}` for:
    V2 gap ≤ max(repairGapMaxEpsMult·EPS, repairGapMaxChildFrac·childExtent): adjust the
    child's `embed` (or add `embed`) so the contact closes; V5 thin axis: scale that dim up to
    MIN_FEAT (keep attach face fixed — dims change only, solver re-places); V5 sub-pixel
    repeat: set count 1 and widen dim to cover the run, record `stripe:true`; V6 duplicate:
    delete the contained part. Never V3, V4, V7. After each pass re-validate; revert a pass
    that adds a new violation. Cap `maxRepairPasses`.
12. `scripts/check-spec.mjs <spec.json…>` — validates (with repair off), prints `report.text`,
    exit 1 on FAIL. Wire into `npm run check` for `subjects/**/spec.json` and
    `dsl/examples/*.json`.
13. `test/fixtures/broken/*.json` — 20 fixtures, each derived from the tenement massing or
    crate, each failing exactly one V-code (name files `v2-gap-large.json`, `v3-orphan.json`,
    `v5-thin-rail.json`, …). Minimum: V1×1 (hand-broken geometry via a test-only prim option
    if needed), V2×4 (gap small-repairable, gap large, socket too shallow, socket too deep),
    V3×3 (orphan single, orphan cluster, chain not rooted), V4×2 (floating ground, COM
    outside footprint), V5×4 (thin dim, sub-pixel repeat, below style floor, exactly at
    floor passes → this one is a PASS fixture), V6×3 (duplicate, clash, allowed socket
    overlap passes), V7×2 (door too tall, step rise too high), V10×1 (over budget via
    repeat count 2000). `test/validate.test.js` asserts each fixture → exactly its code
    (and the PASS fixtures pass), massing + examples pass with zero violations, repair
    closes the 3 cm gap fixture and grows a 1 cm rail fixture to MIN_FEAT, and repair
    refuses V3.
14. `src/app.js` — studio overlay (NOT under `?capture=1`): run validate on load and on spec
    reload; draw orphans in red tint, thin parts yellow, gap vectors as line segments
    between contact face centre and parent surface point; violation list panel with
    `report.text`. Overlay geometry must be a separate `THREE.Group` removed entirely in
    capture mode; manifest `validatorPass`/`violationCount` come from the real report.
15. `scripts/bench.mjs` — extend to time compile + full validate; report ms.

### Evidence
- `npm run check` output tail (all tests, count).
- `node scripts/check-spec.mjs subjects/tenement_block/spec.json` output.
- `node scripts/check-spec.mjs test/fixtures/broken/v3-orphan.json` output (the ≤8-line text).
- bench ms for compile + validate on the tenement.
- Dev server via preview tool (launch.json `llmmodeling`), load
  `?subject=tenement_block&view=threeQuarter` and a broken fixture via
  `?subject=…` if the loader supports paths (else add `?spec=<relative path>` param, dev
  only, ignored in capture) — screenshot the overlay showing red/yellow; save via
  `capture.mjs --view threeQuarter` if the screenshot tool cannot write. Then one capture
  `--view target` and confirm sha unchanged from `out/m0/cap4.png`
  (`9166a66e97dd6da5356475cffeadc82a7583877d4d748ce24ad55e72f3b47a9e`) — validators must
  not change pixels. Stop the server.
- README Status line → "M1 done <date> …; next M2".

Report: PASS/FAIL per acceptance item, deviations (`// DEVIATION:`), evidence paths,
one failing excerpt max. No transcript.
