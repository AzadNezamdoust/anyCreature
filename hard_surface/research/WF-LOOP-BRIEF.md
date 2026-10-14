# Workflow-improvement loop brief (Fable 5.1 seat + GPT Astra seat, round R)

Owner, verbatim: "do a loop with astra and fable 5.1 to improve workflow since it did some logical
stuff wrong."

Subject: the V2 façade run in `tools/LLMModeling` (`V2-TEST-PLAN.md`, `out/facade/S9-REPORT.md`).
Author was GPT Astra writing `subjects/facade_brick/facade.mjs` against `src/kernel/README.md`
through `scripts/pass.mjs`, one pass per item in `subjects/facade_brick/passes.json`, with the
target image `refs/tenement-iso.png` and its own previous render attached each pass. Validators:
`src/validate/kernel-chain.mjs`. Stills: `out/facade/P{0..4}/target.png` and `threeQuarter.png`;
final module `out/facade/P4/facade.mjs`.

Your job in this round — audit, not fix:
1. List every LOGICAL error in the result (things a builder would call wrong, not style): parts
   floating or unsupported in reality even if the validator passed, parts through other parts,
   proportions or counts that contradict the target, things in the wrong place relative to each
   other, missing structure that the visible parts imply. One line each: `E<n>: <what> — <where
   seen: file/still> — <why wrong>`. Ranked by how much it hurts the read of the building.
2. For each error, the ROOT CAUSE in the workflow, one of: pass item wording, kernel README gap,
   missing kernel helper, missing validator rule, validator too weak, pass order, image/context
   given to the author, prompt rules. Cite the file and line of the workflow artifact at fault.
3. Concrete change per root cause, implementer-ready: exact new wording, new validator with its
   measurement and threshold, new kernel helper with signature, new pass order. Prefer changes
   that make the error impossible over changes that ask the author to be careful.
4. Anything that WORKED and must not be touched (one line each).

Rules: ≤120 lines; cite `file:line` or still name for every claim; UNVERIFIED where you cannot;
no praise; do not edit any repo file; output only your audit.
