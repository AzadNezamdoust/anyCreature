# anyCreature

This repo has two sections.

## [creatures/](creatures/README.md)

Organic creature work: the anyCreature engine, harness, box-model experiments,
calibration, cards, example specs, docs and tools. Everything that used to sit
at the repo root now lives here; run its scripts from inside `creatures/`
(for example `bash creatures/setup.sh && bash creatures/tools/test.sh`).

## [hard_surface/](hard_surface/README.md)

Hard-surface modelling: a copy of the LLMModeling gold workflow (v7 `gold.mjs`
scripts, DSL, subjects, refs, prompts, tests) with its `gold-model` skill and
`gold-*` agents under `hard_surface/.claude/`. Renders and builds (`out/`) are
not tracked here.
