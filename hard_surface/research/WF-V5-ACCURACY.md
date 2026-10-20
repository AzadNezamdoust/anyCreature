# v5 — "100 % accurate" (owner 2026-09-26: stylized low-poly targets must be modelled exactly)

## Fable 5.1 discrepancy audit (summary; root causes M measure, H helper, K kernel, T template, C colour, S style, G gate-blind)
Bus (0.958): roof→nose cap and rear corner rounded (K), cap face (K+M), 4 marker lamps on the cap (H+G), windshield black
frame + mullion (H+M), brow line (H), window band wraps rear corner (H), passenger door (H + inventory gap), bumper wrap
(M), headlight rings (C/H), turn lamps rounded-rect (H), right mirror position (M), stop arm size −25 % / border / post
(M+C+H), roof lighter than flank (C).
Pickup (0.978): hood panel/crease helper exists but not called (G/inventory), windshield frame (H), door seam helper not
called, mirror z (M), grille slot height (M), bed end (M), hub cap/ring not passed (T), wheel centres (M); remaining rows
are 1–2 % of L that FIT should absorb (384 px raster, zone terms dominate).
Building: MASSING LOCKED AT WRONG SIZE (~1.4× too tall, front too wide) — pickFrame derives and locks W/H/D, FIT cannot
rescale → every feature inherits it (M, critical; supersedes the "fixed metric size" ruling: scale is free in ortho,
ASPECT must be fitted); roof fixtures/awning/sign from priors (M); storefront layout floor vs image (G/M).
Ranked fixes: 1 fit scale+aspect (similarity + W/H/D) before knobs · 2 inventory-driven BUILD, coverage 100 % blocks the
stop · 3 per-feature measurement (measure-feature.mjs: component segmentation → metres) · 4 kernel rounding
(profile.round) + cap face · 5 helpers: pane frame, roundRect lamps on any face, windowRow wrap, busDoor · 6 colour: one
body tone unless measured split, lamp rings, calibrate on flat render · 7 FIT on full-res per-feature masks + small-part
pass.
"100 %" metric: inventory coverage 100 %; per feature centre ≤ 1.5 % anchor, bbox w/h ≤ 2 %, ΔE ≤ 6 (flat), shape class
match; whole IoU ≥ 0.99, per-zone ≥ 0.95 at full res; no residual row ≥ 0.5 % anchor; gate PASS.
Inventory: segment target (subject mask) into colour components ≥ 0.02 % area → VLM labels each (round-trip: no
unlabelled component, no label without component) → measure-feature → match one-to-one after BUILD (MISSING/EXTRA → 0).

## Opus 5.5 machinery audit (summary)
1 three-state target mask (subject / background / OCCLUDED don't-care — the facade's left wall is behind the green
building and is charged as EXCESS today) + ONE IoU path (compare 0.403 vs residuals 0.703 disagree today).
2 coverage = every target blob owned: unowned-component census ≥ 60 px incl. ink-stripped zone pixels; measured-but-never-
built keys (bus markers) become READY calls; lamp on any face (cap) with housing + lenses; pane frame; hood crease; seams;
arch flare.
3 kernel: K.profile.fillet(points, r, segs) (segs 1 = chamfer), K.profile.roundRect, K.hull (Manifold.hull), K.beam,
K.taper (extrude scaleTop); avoid minkowski; vehicleBody roofR/capR/cornerR knobs; all within triBudget.
4 palette per zone per face {top, front, side} sampled via face-orientation id pass; ΔE2000 ≤ 2 on eroded interiors.
5 FIT per feature: ROI at 1 target px/px (project.mjs roi window), feature score = ROI IoU + edge chamfer + centroid/
diameter, whole IoU held; ~45 s for 15 features. Residual floors / INK_OPEN currently erase frames, muntins, balusters.
6 thin/repeated features: edge map + chamfer, projection-profile autocorrelation (pitch/count/phase), template match,
lens centroid/diameter.
"100 %" = every inventory item within the harness's own noise floor (render measured as target): count exact, position ≤
max(1.5 px, floor), size ≤ 3 % or 1.5 px, ROI IoU ≥ 0.90 (≥ 400 px items) else edge ≤ 1.5 px, ΔE ≤ 2; unowned[] empty;
occlusion-masked whole IoU ≥ noise ceiling (~0.985 on outlined targets). Report "N of M items exact".

## Merged v5 plan (Opus 5.5 orchestrator)
V5-1 truth: three-state mask + one IoU path (test: compare = fit = residuals IoU); facade scale/aspect fitted
  (similarity + W/H/D free, supersedes the fixed-metric ruling); unowned-blob census; accuracy.json ("N of M exact");
  noise-floor calibration (render-as-target).
V5-2 kernel shapes (worktree, additive): fillet/roundRect/hull/beam/taper + README + check-module allow-list; vehicleBody
  rounding knobs (roofR, capR, cornerR).
V5-3 helpers + READY: lamp on any face with housing/lenses (bus markers), pane frame + mullion, windowRow wrap, busDoor,
  roundRect turn lamps, stop arm border + post, hoodPanel crease + seams emitted, arch flare, mirror arm path, hub caps
  passed; building window frames/muntins/sills, baluster rails, AC fan.
V5-4 measurement + FIT per feature: ROI projection, per-feature measure (components, edges, autocorrelation), per-feature
  FIT stage, per-face palette with ΔE gate.
V5-5 runs: fake + blind Luna/Gemini-M on pickup, bus, facade; report "N of M items exact" + sheets.

## Exactness diagnosis (Fable 5.1, 2026-09-26) — "looks right, 1 of 25 exact"
Artefacts: noise floor degenerate (flat self-render has no ink/AA/cel → all zeros; code SPEC ~9× stricter than this
doc: 1.5 px vs 1.5 % anchor ≈ 13 px on vehicles); ROI pad leaks outline strokes + neighbouring same-family items into
the target item (target bbox == ROI in 11/25 bus rows → "render always smaller"); roiIoU too harsh on small items (1 px
costs ~17 % on a 22 px lamp); ΔE contaminated by AA on thin black parts and by cel-shaded tops calibrated from the wrong
face; count errors from classifier merge/split; per-feature FIT timed out and shared knobs undo each other.
Metric fixes alone (measured): bus 1 → 4–6/25, pickup 1–2 → 9–11/27, facade 0 → 1–2/45. The rest is real (lists in the
V5-5 job). Facade: sub-3-px features need a supersampled ROI or stroke/centreline measure.
