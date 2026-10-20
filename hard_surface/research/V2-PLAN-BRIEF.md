# V2 test-project plan brief (two seats: GPT Astra high, Fable 5.1; Fable merges)

Owner: "then do test project plan together." Input: `research/10-postmortem.md` (merged
verdict) plus the two seat post-mortems `10-postmortem-fable.md`, `10-postmortem-astra.md`.
Read those first; skim `PLAN.md`, `WORKFLOW.md`, `dsl/SPEC.md`, `src/prims.js`,
`src/compile/grammar.js`, `src/validate/index.js`, `research/03-landscape.md` §A/§D,
`research/02-correctness.md` §T2 for what exists. Target image: `refs/tenement-iso.png`.
Owner constraints that still hold: cartoon low-poly, flat vertex colours, one material, no
outlines on the asset, glTF out, tri budgets, determinism from the artifact, TARGET = style
and model not a trace, GPT Astra authors geometry, Fable judges/reviews, Opus implements.
Machine facts: Node 24, three ^0.185.1, vite, Playwright in tools/BlindLoop, Codex CLI
(`gpt-6-astra`, reasoning high, shell in workspace-write; read-only blocks shell reads),
Antigravity `agy` for image generation, no API keys. No Blender in the loop.

Plan a **test project** — not a rewrite — that proves the v2 route on ONE façade before
anything else is touched. Deliverable ≤170 lines, implementer-ready:

1. **Scope statement.** One building face (the mint corner façade from the target, or the
   brick middle one — pick and say why): arched doorway cut into the mass, recessed
   windows with real reveals, shaped cornice, open balcony/fire-escape ironwork, parapet as
   a perimeter wall. Nothing else. Acceptance = one still at the solved camera plus one
   three-quarter, validators PASS, tri ≤ budget, and owner sentence.
2. **Representation.** Exactly what the author writes: a procedural JS module? a CSG
   program (manifold-3d union/difference over prims)? extrude-with-holes profiles? Choose
   ONE primary with a concrete mini-example (≤25 lines) for the arched doorway + reveal.
   State how it stays deterministic and how it exports (glTF with COLOR_0).
3. **What to keep, change, delete** from `tools/LLMModeling` for this test, by file.
   Which validators survive unchanged, which must measure real surfaces (contact,
   penetration) and how (manifold-3d intersect volume? three-mesh-bvh?), which are dropped.
4. **Authoring protocol.** Astra sees the target image and the current render every turn.
   One author, batched passes (massing → openings → trims → ironwork → palette), each
   pass validated; K = 1 repair; Fable reviews with one sentence; owner sees a still per
   pass. No Blind Loop until the façade reads right. Exact Codex invocation and prompt
   skeleton (what files/images it gets, what it must return).
5. **Measurement.** What is timed and counted (edit-to-preview seconds, tokens per pass,
   validator ms, boolean ms), thresholds that mean "v2 works", and the one comparison
   against the v1 tenement façade.
6. **Work plan.** Ordered steps with owner of each (Opus implementer / Astra author / Fable
   review / owner gate), each one session or less, with the stop points. Risks with the
   single check that retires each.

Rules: cite file:line for every claim about the current code; UNVERIFIED where you cannot;
no praise; do not edit any repo file; output only your plan.
