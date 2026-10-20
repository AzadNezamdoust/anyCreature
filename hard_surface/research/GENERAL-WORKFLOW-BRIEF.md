# Generalisation brief (two seats in parallel: GPT Astra high, Fable 5.1; Fable merges)

Owner, verbatim: "this is the best so far, small improvements can be done … using fable 5.1 and
astra high in parallel work on the workflow and setup in a way that will create great results on
any hard-surface modelling, analyze what we have done to get these relatively good results to
optimize workflow for any llm."

Subject of the analysis: `tools/LLMModeling`, the brick-façade test, runs 1–4 under the workflow
loop. Read in this order: `README.md` (Status), `V2-TEST-PLAN.md`, `research/WF-LOOP-R1.md`,
`WF-LOOP-R2.md`, `WF-LOOP-R3.md`, `out/facade/measurements.md`, `out/facade/run4/P*/review.md`,
`out/facade/run4/compare-final.png` (best result, vs target `refs/tenement-iso.png`), and the
pipeline as it stands: `src/kernel/README.md` (author API, inlined in every prompt),
`src/kernel/index.mjs`, `src/validate/kernel-chain.mjs`, `scripts/{pass,measure-target,likeness,
calibrate-palette,capture2,check-module}.mjs`, `subjects/facade_brick/{layout.json,
layout.measured.json,census.json,regions.json,passes.json}`, `out/facade/run4/P2/prompt.md` (what
the author actually sees), `out/facade/run4/P2/facade.mjs` (what it wrote). Earlier evidence:
`research/10-postmortem.md` (why v1 failed), `out/wf-loop/r1..r3/*-audit.md`.

Answer, ranked, ≤160 lines, file:line for every claim, UNVERIFIED where you cannot:

1. **What actually produced the improvement, in causal order.** Separate: representation (kernel
   with real booleans/profiles vs the v1 box DSL), the author seeing the target and its own render,
   the measured-not-guessed spec (census/layout/regions with evidence), the gates (logic validators,
   likeness rows, refusals), flat capture, the pass structure, the audit loop itself. For each:
   the evidence that it mattered (a run that failed without it), and what it cost.
2. **What is subject-specific and must be generated per subject vs what is generic.** Which files
   would change for a pickup truck, a vending machine, a robot, a mint corner building; which are
   fixed. Where hand work still exists (regions.json seeded from an audit, census counted at 2×
   zoom by a seat, the front-face contract, camera solve from ground edges) and how each becomes a
   script or a model call with evidence. Propose the per-subject "reference packet" schema:
   what `measure-target` must emit for a generic subject (landmarks, families, silhouette, faces),
   how a class prior (building / vehicle / prop / robot) sets its rules.
3. **Author-model agnosticism.** The author is GPT Astra through Codex today. What in the prompt,
   API, README and gate makes the result depend on that model, and what would let Claude, Gemini
   or a local model author with the same gates: prompt contract (inputs, images, one CHANGE line,
   MISSING KEY), kernel surface, tokens per pass (14–115 k now — what to cut), pass count, repair
   protocol (K=1, own render + table), refusals. Which measured rows would catch a weaker author.
4. **Where the seats still waste.** From `measurements.md` and the run-4 retries log: seats lost
   to workflow bugs, Codex drops, palette work, unverified keys; what a deterministic template
   could replace (P0 massing from the layout, palette, sills), what needs judgement.
5. **The next three subjects to prove generality**, in order, with the reference packet and the
   new rules each needs (e.g. vehicle: wheel census, ground clearance, symmetry; robot: joint
   frames, mirror; prop: single material zones), and the single check that retires each risk.
6. **A one-page target-state workflow** ("WORKFLOW v3"): stages, owner of each (script / author
   model / judge model / owner), inputs and outputs, gates, and the loop that improves the workflow
   itself (which audits, how often, what counts as done). Small, concrete, implementer-ready.

Rules: no praise; cite; do not edit any repo file; output only your analysis.
