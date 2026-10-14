# school_bus — owner packet (scripts/v7/gold.mjs, 2026-09-27T19:09:45Z)
Phase owner after round 5. Migrated from the v7 run (4-round cap + the owner's extra round 5): no v8 merge exists; the open items are the ledger's OWNER lines.

Model `out/ref/gold/school_bus/model-r5.mjs` · sheet `out/ref/gold/school_bus/view/model-view.png` · pages `out/ref/gold/school_bus/view/model-side.png` `out/ref/gold/school_bus/view/model-front.png` `out/ref/gold/school_bus/view/model-rear.png` `out/ref/gold/school_bus/view/model-top.png` `out/ref/gold/school_bus/view/model-concept.png`

| image | iou | agree | drift | vs the bar |
|---|---|---|---|---|
| side | 0.9643 | 0.9643 | 0.0 % | -0.0057 |
| front | 0.9687 | 0.9687 | 0.0 % | -0.0013 |
| rear | 0.9411 | 0.9411 | 0.0 % | -0.0289 |
| top | 0.9709 | 0.9709 | 0.0 % | ok |
| concept | 0.9638 | 0.9638 | 0.0 % | -0.0062 |

Below the bar (0.97): side, front, rear, concept — the blob table names what explains each gap (`node scripts/v7/step.mjs --subject school_bus`).
Gate: chain pass · tris 3742 / 4000

## For the owner to decide
- fact:owner-r5: overall length (concept ~0.15 m shorter: side -0.03 for concept +0.002) and the shell height over the wheels (concept +0.05: side -0.03 for concept +0.002) — both disqualified by the concept-first rule; the owner decides whether the bus follows the concept's proportions

## Runs (12)
r1 modeller ? calls ? min · r1 critic fable ? calls ? min · r2 modeller ? calls ? min · r2 critic fable ? calls ? min · r2 critic opus ? calls ? min · r3 modeller ? calls ? min · r3 critic fable ? calls ? min · r3 critic opus ? calls ? min · r4 modeller ? calls ? min · r4 critic fable ? calls ? min · r4 critic opus ? calls ? min · r5 modeller ? calls ? min

Ledger: `out/ref/gold/school_bus/LEDGER.md`. Decide: accept → `node scripts/v7/gold.mjs owner --subject school_bus --accept` · one more review → `--review` · one more modeller round → `--extra-round`.
