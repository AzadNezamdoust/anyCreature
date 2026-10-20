# Workflow loop — round 1 merge (Fable final, 2026-09-13)

Inputs: `out/wf-loop/r1/astra-audit.md` (GPT Astra high, 361 s, 81 927 tokens, 10 errors),
`out/wf-loop/r1/fable-audit.md` (Fable seat, 11 errors). Target re-read at 2× zoom
(`out/wf-loop/r1/target-brick-zoom.png`): brick front = 2 bays × 2 upper window rows, storefront +
RECTANGULAR glazed door, green sign box over the awning with an AC unit, roof-access ladder on the
left edge, drop ladder from the lower landing, full-depth block, roof with vent box + 2 pipes.
Fable's "3 rows" (E2) is wrong; Astra's "2 × 2 keep" stands. Everything else below is what both
seats said or one said and the other did not contradict.

## Errors accepted (ranked) → change
| # | Error | Fix class | Change |
|---|---|---|---|
| 1 | Populated face shows on the wrong side at the target camera (window heads fall to the right; target's rise) | by construction | `meta.front` contract: author builds the front on −Z (README unchanged); `toThree`/app rotate the assembly about Y so −Z → +X before framing. Documented in README "Frame" section. Validator none needed. |
| 2 | Roof + back parapet + vent cantilever 3.1 m past 1.1 m returns | wording + validator | P0 item: closed block, full-depth side walls + back wall, roof bears on all four. `V11_BEARING`: every part with role in {roof, cornice, sill, awning, landing, parapet} — sample bottom face on 0.1 m grid; each sample needs a part within 0.02 m below OR unsupported span along the part's long axis ≤ 1.0 m. |
| 3 | Arched door on the brick building | wording | P1 item: RECTANGULAR glazed door 2.1–2.4 m, same reveal recipe. Arch stays in the README example + `test/fixtures/kernel`. |
| 4 | Missing roof ladder, sign box, AC unit; census by vision | census | `subjects/facade_brick/census.json` {bays 2, windowRows 2, windows 4, storefront 1, doors 1, landings 2, flights 1, ladders 2, signbox 1, ac 1, vent 1, pipes 2}. `V12_CENSUS` counts by role (windows = role window frames; rows = y-bands clustered 0.5 m; ladders = role ladder assemblies = groups of ladder-role parts with overlapping x-range). Items cite census numbers, never "count them". |
| 5 | Role table bypassed (tread/massing instead of step/parapet); stair rise 0.27 m; parapet 0.28 m; no stair handrail | closed roles | README closed role list: massing, roof, parapet, cornice, sill, window, storefront, door, awning, signbox, ac, landing, support, stringer, step, railing, baluster, ladder, rung, roof_fixture, prop. `V7_ROLE` fails on unknown role. `step_rise` = y-pitch between consecutive role-step parts incl. landing tops, band 0.14–0.20, variation ≤ 0.01. `stair_rail_required`: each stringer needs ≥1 railing part overlapping its x-range, 0.9–1.1 m above the tread line. Parapet band applies to role parapet. |
| 6 | Undeclared penetrations pass V6 (brackets into brick + awning, treads through stringers) | validator | Pairs with no declared touch: any intersect volume > 1e-6 m³ fails `V6_CLASH_UNDECLARED`. Declared touch keeps 0.2; `embed:true` keeps 0.9. New default key `overlapClashUndeclared: 0` in kernel-chain (limits.json frozen → owner packet). |
| 7 | Landings 0.425 m off the wall, no rear guard; sills 0.38 m deep | validator + README | `V11_LANDING_GAP`: role landing rear face to nearest massing face ≤ 0.15 m. README: sills project 0.05–0.15 m, cornice 0.2–0.6 m, awning ≤ 1.5 m. |
| 8 | Drop ladder head blocked by continuous railing | validator | `V11_LADDER_ACCESS`: for each ladder assembly whose top is within 0.3 m of a landing top, no railing/baluster part may intersect the ladder's x-range ± 0.3 m in the band landing-top … +1.1 m. |
| 9 | Deck slots 0.21 m | validator | `V11_DECK_GAP`: landing-role parts in one y-band, sorted along their short axis: adjacent gap ≤ 0.10 m. |
| 10 | Storefront got a knee-height sill | wording + role | Role `storefront`; P2 item: sills under UPPER windows only, stall riser flush. |
| 11 | Freeze wording locked errors in; author saw its render one pass late | protocol | Every pass item ends: "You may reopen any earlier part if the LOOK checklist for it failed; the previous review lists the failed rows." Fable review = fixed 6 rows (orientation, bearing, census, door shape, landing gap, clashes) PASS/FAIL, written to `review.md`; a FAIL row goes into the next prompt. |
| 12 | Camera fallback silent | preflight | `pass.mjs` refuses to run unless `refs/<subject>.camera.json` exists with `provisional:false`. |
| 13 | Dashed line under right cornice | UNVERIFIED | Opus: raise the cornice bottom course 0.01 m in a scratch copy, re-render; if dashes vanish add advisory `V13_COPLANAR` (shared plane within 1e-4 m, overlap > 0.01 m²). |

Deferred (owner packet): drop-ladder deployed state (Astra E10), `K.stairFlight`/`K.bracket`
helpers (Astra E5, Fable C6 — validators first, helpers only if the author fails the rows twice).

## Keep (both seats): reveal recipe, `cut(wall, union(tools))`, stepped cornice along the run,
wedge awning + fascia, `K.repeat` ironwork as separate solids, Codex invocation hygiene, V2′/V3′
real-surface measurement, byte-stable capture, check-module gate, perimeter parapet.

## Round-1 run plan
Opus applies the table (S-WF1). Module reset to the S1 smoke; P0–P4 rerun with the new
`passes.json`; Fable 6-row review per pass; round-2 audits (both seats) on the new stills;
loop ends when both audits list zero errors of classes 1–12 or after round 3.
