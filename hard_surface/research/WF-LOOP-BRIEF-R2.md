# Workflow-improvement loop brief — ROUND 2 (Fable 5.1 seat + GPT Astra seat)

Owner, verbatim, on the round-1 result: **"too far from the truth."** Owner goal, verbatim:
"we are trying to create workflow that can create accurate 3d models fast."

Round 1 (`research/WF-LOOP-R1.md`, `out/wf-loop/r1/*`) turned 13 LOGICAL errors into rules:
closed roles, census, bearing, landing gap, ladder access, deck gap, undeclared clash, handedness,
camera preflight. Run 2 (`out/facade/P0..P4`, stills `target.png`/`threeQuarter.png`, side-by-sides
`out/wf-loop/r1/compare-P*.png`, final module `out/facade/P4/facade.mjs`) passes every one of those
rules with 0 repairs — and still does not look like the brick building in `refs/tenement-iso.png`.
Round 2 is about LIKENESS: why a model that is logically right still reads wrong, and what rule,
measurement, prompt, or kernel helper closes each gap **without a human in the loop**.

Your job — audit, not fix:
1. List every LIKENESS gap between `out/facade/P4/target.png` and the brick building in image 1,
   ranked by how much it hurts the read at a glance. Think like an art director: proportion (opening
   size vs wall, frame thickness, sill depth, cornice depth, storey height), colour (hue/value of
   brick, frames, iron, awning), silhouette (what breaks the box outline), detail density (what the
   target has that we lack, what we have that the target lacks), style (flat cartoon vs shaded).
   One line each: `L<n>: <gap> — <where seen> — <what the target does instead>`. Measure where you
   can (pixel ratios in the stills, hex values sampled from image 1, metres in `facade.mjs`).
2. For each gap the ROOT CAUSE in the workflow: pass item wording, kernel README gap, missing kernel
   helper, missing measurement (nothing measured it so nobody noticed), review row missing, author
   never compared its render to the target, palette sampled by guess. Cite file:line.
3. Concrete change per cause, implementer-ready. Prefer MEASUREMENTS over instructions: a rule that
   samples the target image (e.g. mean colour of a region, opening-to-wall area ratio, frame width
   in px at the solved camera) and compares it to the render is worth ten adjectives in a prompt.
   Name the script, its inputs, the number it produces, the threshold. Where an instruction is the
   only option, give the exact sentence.
4. Speed: which of the five passes could merge, which could run without a seat (deterministic from
   the census + a palette sample), where the 2–5 min per pass goes (`out/facade/measurements.md`).
5. What WORKED in round 1 and must not be touched (one line each).

Rules: ≤130 lines; cite file:line or still name for every claim; UNVERIFIED where you cannot;
no praise; do not edit any repo file; output only your audit.
