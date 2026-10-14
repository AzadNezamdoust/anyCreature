# Examiner audit of a BLIND test run (GPT Astra high, examiner seat)

Owner rule (2026-09-13): the modelling WORKFLOW passes only if blind TEST models (Gemini 3.8 High, GPT 5.6
Terra) produce good models through it. You are an EXAMINER: find what in the WORKFLOW made the test model fail
or fall short. Never propose tuning for one model; propose changes that would help ANY model.

Run under audit: subject `pickup`, pass P1 (details: windows, grille, headlights, mirrors, door lines), test seat
Gemini 3.8 Flash High, blind, text-only contract. Result FAIL. Artifacts (read them):
- out/blind/pickup/agy/P1-run1/prompt.md — EXACTLY what the test model received (with 3 images: target
  refs/pickup_truck.png, the P0 stills target.png and threeQuarter.png of the start module)
- out/blind/pickup/agy/P1-run1/module.start.mjs — the start module (a scripted P0 template)
- out/blind/pickup/agy/first-seat-P1.mjs — the test model's first module
- out/blind/pickup/agy/P1-run1/{run.log, report.json, likeness.json, repair-prompt.md, repair.md,
  module.after-repair.mjs, compare.png}
- the class rules classes/vehicle.md, classes/vehicle.json, src/kernel/README.md, subjects/pickup/passes.json,
  subjects/pickup/layout.json
Already found by the orchestrator (do not repeat, extend or contradict with evidence): door-line cuts through the
cab base split cab from chassis and the V3 hint named the wrong lump; the repair reply did not parse; the repair
guard let a non-loading module stand (fixed); the template hides the far front wheel.

Answer, ranked by impact, <= 80 lines, file:line or image evidence for every claim, UNVERIFIED where you cannot:
1. What in prompt.md is confusing, contradictory, missing or too long for a model that sees nothing else
   (quote the line). Estimate the prompt's size and what could be cut without losing a gate requirement.
2. Which gate/likeness rows would a careful author still fail because the prompt never states them.
3. What the test model got RIGHT that the workflow should protect.
4. Concrete workflow changes, implementer-ready (exact sentence, rule, token, or script change).
Do not edit any file. Your final message is the audit.
