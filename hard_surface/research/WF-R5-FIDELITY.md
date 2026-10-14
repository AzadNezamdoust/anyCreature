# Round 5 — fidelity (accuracy) design (Fable 5.1 review, merged by Opus 5.5, 2026-09-25)

Owner: "the whole idea is to create the ideal workflow" — accurate + technically correct + fast, any subject, any LLM.
Round 4 made every seat technically correct (same model); accuracy is capped by the workflow.

Principle: extend what made round 4 work (harness-computed numbers, correct-by-construction helpers) to SHAPE and to
EVERY feature; do not give weak authors more freedom.

Ranked (accuracy gain per effort):
1. Profile-derived body + wheel arches — scripts/measure-profile.mjs: rectified foreground masks per face (side/front/
   plan) → simplified profiles snapped to measured keys → layout._profile.*; shared scripts/template-profile.mjs:
   body = extrude(side) ∩ extrude(front) ∩ extrude(plan), arch cuts per wheel, role slicing at cab.start/end;
   classes/<class>.json profileFaces (vehicle, building massing, prop, robot limbs).
2. Feature inventory + V13_COVERAGE — scripts/inventory.mjs: strong-model vision pass with per-instance boxes, script
   verification (colour component or ink chain), rectified into keys with evidence; subjects/<s>/inventory.json
   generates census + requiredLayoutKeys; features without a helper → deferredByRuling (never silent). Gate: every
   item present by helper tag, count, position min(tol, 0.25 extent), extent ±15 %; row prints the READY call.
3. Helpers with inlay contrast — seam, handle, lamp tail, balustrade (pitch), acUnit fan, stoop, lintel; recess helpers
   place an inlay part in a closure zone sampled from target slot/seam pixels (flat unlit capture hides grooves);
   classes/<class>.json features{} = {helper, keys, tag}; a feature without a helper is inadmissible.
4. Tighter bands calibrated on the Opus reference — LK_AREA ±15 %, silhouette IoU ≥ 0.97 whole / 0.95 per face;
   scripts/calibrate-bands.mjs (reference value ± 1.5 × residual); round-4 modules become FAIL fixtures.
5. Passes P0 body (template) / P1 large features / P2 small features / P3 verify; --seat-mode append (seat returns only
   inserted lines; module shown collapsed) → every pass ≤ 12 kB (facade is 29 kB today from echoing the module).
6. Unseen-subject protocol — GPT image targets (school bus, corner bakery, vending machine, boxy biped mech), full
   measure → inventory → template → blind Luna + Gemini-M, vs an UNCONSTRAINED Opus reference; pass = 100 % coverage,
   IoU ≥ 0.9 × reference, ≤ 1 repair, ≤ 12 kB per pass.
Outlines stay excluded (owner ruling 2026-09-12).

## Unconstrained Opus reference (out/ref/pickup-free.mjs, out/ref/pickup-accuracy.png)
45 parts, 3684 tris; check-module PASS; harness gate PASS, layout PASS; likeness FAIL: body side/front value ratio 0.81
(target 1.0 ± 0.05), dark area 0.67×, LK_VISIBLE wheel 2/3. Better than the workflow model (grille with bar, wheel
arches, open bed with liners, tapered cab, door seams/handles, wrapped bumpers) but still short of the target.
Gaps Opus hit (all workflow gaps): no measured keys for sill, arch radius/height, bed floor, hood notches, door/handle
positions, rear bumper top (read off by eye); no helper for angled pane edges, flared arches, two-tone grille; window
instance grouping merges a tapered side pane with the windshield (bbox grouping); a recess cut flush with the face
leaves a zero-thickness skin over the glass (cut tool must start outside the face — kernel should do this); no
offline render for authors. Seams and arch liners barely read in the flat unlit capture (→ inlay contrast, item 3).

## 2026-09-26 — Opus with eyes (owner: "I want better 3d models from opus 5.5")
New tool `scripts/render-module.mjs` (+ `scripts/compose-compare.py`, app `?module=out/ref/...`): renders any work
module at the target's solved camera (flat + shaded) and a shaded three-quarter, overlays outlines on the target,
prints silhouette IoU. Shaded look stills (`shade=1`, camera-relative key) now also saved every pass.
Opus 5.5 iterating with it (8 iterations, render → 3 biggest differences → fix → re-render, revert regressions):
IoU 0.909 → 0.976, full chain PASS, 45 parts / 3844 tris (out/ref/work/pickup.mjs, out/ref/work/view/compare.png).
Remaining: rear bumper height held by the bumper.rear.h layout floor; 24-segment near wheels (tri budget); door seam
/ cab-back lip weak (no rounded-corner helper, no ink); helpers too coarse for rounded mirror heads / flush lamps
(so VEH_HANDBUILT advisory). Lesson: the render→compare→fix loop is the biggest single lever — next, give it to
every seat as a pass mode (K iterations of look-and-fix, not one-shot + one repair).
