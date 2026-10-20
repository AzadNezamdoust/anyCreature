# Post-mortem brief (two independent seats: GPT Astra high, Fable 5.1)

Owner question, verbatim: "almost everything is additive, no boolean or poly modelling, why?
just process what went wrong, try not to fix the model."

You are auditing `D:\Git\checkout\tools\LLMModeling` (read-only; change nothing). Evidence:
`PLAN.md`, `WORKFLOW.md`, `README.md` (Status section = chronological log), `research/01..09`,
`dsl/SPEC.md`, `src/compile/*.js`, `src/prims.js`, `src/parts/lib/*.json`,
`subjects/tenement_block_llm/spec.json`, `tools/BlindLoop/runs/m4-tenement-r*/log.md` and
`ledger.md`, `refs/tenement-iso.png` (the target), `out/m4/final-target.png` (the result),
`out/targets/tenement_block-v1.png`. The owner's original brief: `research/BRIEF.md`.

Answer these, ranked by impact, with file:line or run-log citations for every claim:
1. Why is the geometry purely additive primitives (box/plate/wedge/ring) with no boolean
   subtraction (window reveals, arches, door openings) and no polygon modelling (extruded
   profiles, bevelled cornices, lofted awnings)? Was that a research conclusion, a plan
   ruling, an implementation shortcut, or drift? Quote the decision point.
2. Was additive-only the right call for the stated goals (correctness, style, speed)?
   Where did it cap visual quality? Which parts of the target are impossible to express
   in the current DSL?
3. Process: over ~2 days, where did time and tokens go? Estimate from README status entries,
   run logs and research files: research vs harness vs validators vs the model itself.
   Which harness incidents (junction deletion, adapter paths, scope gaming, occlusion,
   stacked merges, node_modules/.bin) were avoidable and how?
4. The loop: one item per ~10 min, three judges per round. Did the Blind Loop earn its cost
   for THIS stage (first 90% of the look) or was it applied too early? What should the
   first-90% path have been?
5. Model choices: Astra authored geometry via a constrained DSL. Did the constraints waste
   the model's strength? What would you let the model write instead (CSG program, mesh
   ops, procedural code with a validator after)?
6. What a v2 should be, concretely: representation (CSG via manifold-3d? extrude-with-holes?
   OpenSCAD-like program? hybrid?), what the validators keep, what the loop is for, and
   what to delete. One page max.

Format: ≤180 lines, headings 1–6, conclusions first, no praise, no hedging, UNVERIFIED
where you cannot cite. Do NOT edit any repo file; write only your own output file.
