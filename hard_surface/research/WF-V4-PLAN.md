# WORKFLOW v4 — merged plan (Opus 5.5 + Fable 5.1 designs, merged by Opus 5.5, 2026-09-26)
Owner: "reflect this quality to the workflow. consider overhauling the system."
Evidence: Opus-with-eyes lifted the pickup IoU 0.909 → 0.976; of ~25 numbers it changed, 18 were edges read off the
image that no layout key measured (roof front, cab-back lean, body bottom, windshield top, cab taper, arch shape,
cowl, handle, rear bumper); the rest was structure (wraps, liners, taper, seams). Eyes did two jobs: (a) measure
edges — numeric, must be the HARNESS's job; (b) choose structure — the only job an LLM needs.
Both designs agree: harness FIT for continuous shape (no seat), then a short seat loop on NAMED residuals with a
strict no-regression guard; delete the P0–P3 pass split, K=1 repair and review machinery; registered renders.

## Architecture (v4)
S0 MEASURE (existing scripts, once per subject) → S1 START: template emits a module whose continuous numbers are one
`export const KNOBS = { name: {v, min, max, key} }` block (ranges from V12 tolerances / class priors; knobs on unseen
edges locked to symmetry/prior) → S2 FIT (no seat): coordinate descent over KNOBS scored by a Node projector (kernel
mesh → solved camera → per-part/per-role masks, ms per eval): objective = whole silhouette IoU + Σ per-zone IoU −
gate penalty; ~150–300 evals → S3 BUILD (1 seat call): features from the inventory via READY CALLS (merges P1–P3) →
S4 LOOP (seat, K ≤ 4): residual rows → seat edits (`replace A-B`) → gate + project → accept only if strictly better
(lexicographic: loads; gate blocking rows ↓ and no new code; coverage ↑; min per-zone IoU ↑; whole IoU ↑; tris in
budget) else revert and re-send with the reason; stop at all rows under tol / K / 2 reverts / 2 gains < 0.003.
Residual rows (scripts/residuals.mjs): `RESIDUAL <part|zone> <EXCESS|DEFICIT|OFFSET|EXTENT|MISSING|EXTRA> <metres>
— part "<id>" side <top|bottom|front|rear> — proposal: <knob edit | helper call>`; pure knob residuals are absorbed by
FIT and never shown to a seat; a residual blocked by a layout floor becomes MISSING KEY (harness fault, not seat).
Prompt ≤ 8 kB (scoreboard, ≤ 8 rows, cited lines ±2, READY calls for missing features, edit contract). Images:
compare sheet with registered outlines + numbered callouts; the loop must also work with images off.
Final look sheet (browser, shaded) only for the owner/examiner.

## Keep / change / delete
Keep: kernel + helpers, check-module, V-rule gates, V12 layout (as constraints), measure scripts, inventory, seats,
line edits, syntax retry, palette auto-fix, LK_VISIBLE, LK_OVERLAP, blind-test snapshot/restore.
Change: render-module/compose-compare → registered (no bbox alignment; it hides scale/aspect error); captures in one
page load; blind-test runs loop.mjs.
Delete: passes.json prose items + P0–P3 staging (dueVisibleParts, familyOwners, instructionRows/Coverage,
resolveItem), K=1 repair block, review.md/REVIEW_PENDING/look-checklist/verdict review hashes, compare-still,
LK_VALUE/LK_HUE/LK_AREA/LK_SILHOUETTE-wedge (→ per-zone IoU + colour deltas), missing-keys refuse policy (FIT supplies
unmeasured numbers; true gaps logged as deferred).

## Stages (each its own implementer job, tests green at each)
V4-1 projector + registered render + residuals: scripts/project.mjs (IoU ≥ 0.99 vs browser idpass on
  out/ref/work/pickup.mjs and the facade), app registered framing, scripts/residuals.mjs (Opus work module → rows under
  tol; blind Luna r5 module → rows name roof front, cab-back lean, body bottom, rear bumper, arches).
V4-2 KNOBS + FIT: template-vehicle (then template-building) emit KNOBS; scripts/fit.mjs (from start-P1: FIT alone ≥
  0.95 whole IoU, gate PASS, deterministic, ≤ 30 s).
V4-3 LOOP: scripts/loop.mjs (BUILD + LOOP, guard, stops, prompt ≤ 8 kB; fake-seat tests: regression reverted,
  plateau stop, target stop), blind-test rewired, delete list applied, old tests converted.
V4-4 runs: Opus (reference, same loop), Luna, Gemini-M blind on pickup + facade; then an UNSEEN subject (GPT image,
  e.g. school bus) end to end. Pass per weak seat: gate PASS, coverage 100 %, registered IoU ≥ 0.96 and ≥ Opus-loop −
  0.015, ≤ 4 loop iterations, ≤ 8 kB prompts, ≤ 10 min, no harness edits mid-run; owner side-by-side sheet.
Outlines stay excluded (owner ruling 2026-09-12). Designs: research/WF-V4-OPUS.md + Fable section below.

## Fable 5.1 design (summary)
Picked "harness fits parameters; LLM only chooses structure" over "every seat iterates on pixels" (re-opens the
round-3 fractions-by-hand failure) and "strong builds, weak edits" (violates any-LLM). Projector in node through
refs/<s>.camera.json; FIT on layout._fit vertex/arch/bumper params; residual rows the seat reads instead of pixels;
lexicographic strictly-better guard; K ≤ 3; prompt ≤ 8 kB, images optional; unseen sides locked to symmetry/prior; a
GPT second view only as a topology hint, never in the objective; unabsorbable residuals → deferredByRuling = the next
helper to write.
