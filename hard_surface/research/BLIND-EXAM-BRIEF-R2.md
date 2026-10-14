# Examiner audit, blind round 2 (GPT Astra high, examiner seat)

Owner rule: the WORKFLOW passes only if blind TEST models (Gemini 3.8 Flash High, GPT 5.6 Terra) build good models
through it. You examine the workflow; propose changes that help ANY model; never tune for one model.

Four blind runs, all FAIL. Read the archived artifacts (they are frozen; the harness source is being edited by
another job right now, so prefer the archived prompt.md files over live src files):
- Gemini, building P2 fire escape: out/blind/facade_brick/agy/P2/{prompt.md, attempt-1/report.json, attempt-1/likeness.json, report.json, likeness.json, repair.md, module.agy.mjs, compare.png}
- Terra, building P2 (gated, no repair): out/blind/facade_brick/terra/P2-diag/{module.terra.mjs, gate.log, report.json, likeness.json, compare.png}; its prompt is the same as Gemini's prompt.md above
- Gemini, pickup P1 details: out/blind/pickup/agy/P1/{prompt.md, report.json, likeness.json, repair.md, module.agy.mjs, compare.png}
- Terra, pickup P1: out/blind/pickup/terra/P1/{prompt.md, attempt-1/report.json, attempt-2/report.json, last.md, repair.md, module.terra.mjs}
Targets: refs/tenement-iso.png (building), refs/pickup_truck.png (truck).

ALREADY FOUND (research/WF-BLIND-R2.md C1–C11) — do not repeat: repair guard on introduced codes; helper-built
landing fails V11_LANDING_GUARD (rule/helper disagree); absolute metres + wall planes in the prompt; closed palette
zones (iron/lamps calibrated to wrong regions); template-owned likeness rows; lower-landing iron value patch; Terra
transport drops; stale NO_RESULT archive; groove rule vs V5_THIN cut contradiction + kernel throw kills the module;
detail parts hiding an already-built wheel.

Answer, ranked by impact, <= 60 lines, file:line or image evidence for every claim, UNVERIFIED where you cannot:
1. NEW workflow gaps these four runs expose that C1–C11 do not cover (quote the prompt line or artifact).
2. Where the two models behaved DIFFERENTLY on the same prompt, and what that says about ambiguity in the prompt.
3. What both models got right that the workflow should protect.
4. Concrete changes, implementer-ready.
Do not edit any file. Your final message is the audit.
