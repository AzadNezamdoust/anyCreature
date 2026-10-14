# LLMModeling research brief (shared by all seats, 2026-09-10)

## Project context
Repo D:\Git\checkout (Unity DOTS PoC "Checkout"). New workstream `tools/LLMModeling/`:
an LLM-driven 3D modeling pipeline for HARD-SURFACE assets — buildings, vehicles,
props, robots, furniture, street furniture. Not organic characters (that is
`tools/CharacterStudioV2`, already solved).

Target look: cartoon isometric low-poly, flat/vertex colours, chunky readable
silhouettes, clean planar faces, small tri budgets (props <2k, buildings <8k),
one material. Reference: a Simpsons-Tapped-Out-style 3-storey tenement block —
three adjoining facades (mint, red-brick, tan), flat roofs with parapets, vents,
chimney pipes, fire escape with stairs, balconies, awning, stoop stairs with
railings, arched door, trash can, crates, AC unit, clothesline. Every part
attached, proportions logical, nothing floating, nothing paper-thin.

Two starting sources the owner wants surpassed:
- https://github.com/Ariescar/anyCreature
- https://github.com/img2threejs/img2threejs

Observed failure modes of LLM-writes-three.js approaches (owner report):
1. Logical errors: parts in wrong place, wrong scale relative to each other.
2. Details too small or too thin (sub-pixel slats, paper walls, hairline rails).
3. Floating parts: sections not attached to anything, gaps between sections.
4. Poor iteration speed: slow regenerate/render/judge loop.

## Iteration harness we already own
`tools/BlindLoop/` — blind-judged improvement loop: frozen TARGET image, BASELINE
always a candidate, worker never sees target, judge never sees authorship,
one ITEM per round, isolated git worktree per candidate, hard budgets, stall
rule. Any solution must plug into this loop (headless capture URL + manifest).

## Priorities (in order)
1. Geometric correctness (attachment, scale logic, min feature size).
2. Quality above the two sources.
3. Speed + iteration for the human modeler (seconds, not minutes, per round).
4. Determinism from seed; exportable to glTF/FBX for Unity.

## Deliverable format for each seat
Write ONE markdown file at the path given in your task. Max ~250 lines.
Sections: Findings (bullets, each with a source URL or file:line), Techniques
worth stealing (concrete, with how they'd fit our pipeline), Dead ends (with
why), Open questions. Conclusions only — no transcript, no narration. Cite
every non-obvious claim. If you cannot verify a claim, mark it UNVERIFIED.
Do not edit anything outside `tools/LLMModeling/research/`.
