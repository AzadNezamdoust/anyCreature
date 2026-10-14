# WORKFLOW v4 — Opus 5.5 design (2026-09-26, summary)
Why blind seats are plainer: Opus's 0.909→0.976 came from reshaping continuous geometry (roof inset, rake, bed
length, bumpers, arches); weak one-shot seats never reshape and cannot read the overlay.
Loop (scripts/loop.mjs replaces P0–P3): MEASURE (scripts, once) → START (template emits `export const KNOBS` —
every continuous size/position with range from its V12 tolerance) → FIT (no seat: coordinate descent over KNOBS on
silhouette IoU via a Node rasteriser, gate must hold, ~150 evals ~10 s) → BUILD (1 seat call, READY CALLS for every
inventory feature) → ITERATE (≤ 6 seat calls; accept only if not worse: loads; gate rows not more / no new code;
coverage not lower; IoU ≥ best − 0.002; rejected edit reverts and is reported). Stops: target (gate PASS, 100 %
coverage, IoU ≥ 0.97 whole / 0.95 per face) / plateau (2 accepted < 0.003 or 2 rejected) / budget (6 iter or 12 min).
Iteration prompt ≤ 12 kB: scoreboard, top-5 DIFFERENCES each naming the line/knob and allowed range, KNOBS +
numbered lines of named parts, READY CALLS for missing features; images: compare sheet + difference heat map.
Harness computes (scripts/diff.mjs): part-level id pass; XOR outline gaps per part and side in metres; per-feature
zone mask IoU + offsets; per-part colour delta (auto-fix unique); coverage MISSING rows; ranked by area × weight.
Layout floors that block a fit → MISSING KEY, not the seat's fault.
Delete: P0–P3 split + passes.json items, K=1 repair block, review/REVIEW_PENDING/look-checklist, compare-still,
staged due/owner logic, instructionCoverage. Keep kernel, helpers, gates, V12, measure, inventory, seats, line edits.
Registered render (drop bbox alignment — it hides scale/aspect errors). One-load capture. Vectorise compose.
Cost: ~5 seat calls, 5–7 min typical, ≤ 10 min, < 60 k tokens per subject per seat.
Test: pickup, facade, unseen (vending machine / school bus); Opus, Luna, Gemini-M blind, same loop; pass per weak
seat: gate PASS, 100 % coverage, registered IoU ≥ Opus-loop − 0.015 and ≥ 0.95, ≤ 6 iter, ≤ 12 kB, ≤ 10 min.
Steps: 1 registered render · 2 Node rasteriser · 3 idpass=part + diff.mjs · 4 KNOBS templates · 5 fit.mjs ·
6 sheet.mjs · 7 loop.mjs + guard + stops · 8 retire old passes/repair/review, rewire blind-test · 9 reference +
blind runs · 10 unseen subject.
