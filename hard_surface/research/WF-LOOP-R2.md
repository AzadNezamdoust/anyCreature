# Workflow loop — round 2 merge (Fable final, 2026-09-13)

Inputs: `out/wf-loop/r2/fable-audit.md` (12 gaps, 7 changes), `out/wf-loop/r2/astra-audit.md`
(GPT Astra high, 408 s, 88 187 tokens, 18 gaps; two earlier seat attempts died mid-read). Owner:
"too far from the truth"; goal "accurate 3d models fast". Target stays `refs/tenement-iso.png`
(owner: "keep it").

Both seats, independently: (a) the RENDERER darkens the populated face (key light placed for the
character studio, front brick renders at 0.51× its palette value) — the P4 palette seat was blamed
for a capture fault; (b) NOTHING MEASURES LIKENESS — six logic rows, zero proportion/colour rows;
(c) every metre was invented by the author because the census counts but has no dimensions;
(d) the author never sees its own render; (e) 4 of 5 seats can go. Astra adds: compare only
mutually visible surfaces (the target's neighbours hide the side wall), keep geometry/appearance/
visibility failures separate. Fable adds: the "real recess, nothing proud" rule was ours, not the
target's — frames are proud in the image.

Deferred by owner ruling (assets outline-free, 2026-09-12): ink strokes (Fable M5, Astra L3) and
brick-accent decals (Astra L8, Fable L11). Deferred as second-order: glass reflection strokes,
door sash, roof-fixture shapes, bench prop, `K.fireEscape` helper (validators + layout first).

## Changes (two Opus jobs, file ownership disjoint; both must keep `npm run check` green)

### Job A — capture, measurement, speed (owns: src/app.js, src/material.js, src/kernel/toThree.mjs, src/geom.js, scripts/pass.mjs, scripts/likeness.mjs, scripts/capture2.mjs, subjects/facade_brick/regions.json, scripts/measure.mjs)
| # | Change | Number / gate |
|---|---|---|
| A1 | **Flat capture.** In the `?capture=1` path use `MeshBasicMaterial({vertexColors:true})`, no lights; `paint()` gains `sideTint` (default −0.12) on facets whose normal is the non-front horizontal axis so the side reads darker than the front like the target (front V .65, side V .52). Studio (non-capture) view unchanged. README:45 sentence becomes "palette hex = what the capture shows on the front face; side −12 %". | likeness front-brick value ratio render/palette 0.90–1.05; side/front 0.80–0.92 |
| A2 | **`?idpass=1` capture mode**: every part painted one flat unique colour per ROLE (lookup table in app.js), no shading; same camera. Gives a role mask of the render. | byte-stable like the main capture |
| A3 | **`subjects/facade_brick/regions.json`** (FROZEN once written): target px rects per zone on `refs/tenement-iso.png` for the brick building only: brick_front, brick_side_strip, roof, coping, glass (one rect per window pane row), frame, sill, iron_landing_upper, iron_landing_lower, awning, signbox, ac, door, storefront. Seed from the Fable audit (front face x 503–764, wall y 345–897; samples brick (650,380), glass (715,330), awning (680,710), frame (610,391), sill (610,442)). Derive by pixel sampling with a scratch script; commit the rects, not the script's guesses. | ≥ 25 interior px per rect |
| A4 | **`scripts/likeness.mjs <P>`**: inputs regions.json, target, `P<N>/target.png`, `P<N>/idpass.png`. Per zone: median target colour vs median render colour inside the role mask → value ratio, Δhue (deg); on-screen area share of each role vs the target rect area share (both normalised by the brick-building bbox). Also screen-space checks from the mask: `SCREEN_OVERLAP` ladder/iron pixels inside a window's projected rect = 0; `VISIBLE` every census role ≥ 50 mask px. Output `P<N>/likeness.json` + ≤ 8-line text in the SAME violation format as the V-codes (`LK_VALUE`, `LK_HUE`, `LK_AREA`, `LK_OVERLAP`, `LK_VISIBLE`). | ΔV 0.85–1.15, Δhue ≤ 12°, area share ±30 % |
| A5 | **pass.mjs**: after gate + capture run likeness; a likeness FAIL enters the SAME K=1 repair slot as a V-code, and the repair prompt attaches BOTH current stills + the likeness table (the author finally sees its own render). Write `P<N>/compare.png` (target | render) with `scripts/compare-still.mjs`. Drop the blank look-checklist rows that are now measured (bearing, census, clashes, landing gap stay measured; the LOOK table keeps only rows a script cannot do: orientation, door side, "reads as the target"). | — |
| A6 | **`scripts/capture2.mjs`**: one Playwright browser, one page, both views + idpass in sequence; same PNG bytes as `tools/BlindLoop/capture.mjs` (prove with sha on the smoke). pass.mjs uses it. | capture total ≤ 4 s warm |
| A7 | **measure.mjs**: run/attempt id column, separate seat / gate / capture / likeness / manual columns; fix the "## Run 2" header landing after the rows. | — |

### Job B — measured layout, layout validator, pass restructure (owns: src/validate/kernel-chain.mjs, subjects/facade_brick/layout.json, subjects/facade_brick/passes.json, subjects/facade_brick/census.json, src/kernel/README.md, scripts/calibrate-palette.mjs, test/**)
| # | Change | Number / gate |
|---|---|---|
| B1 | **`subjects/facade_brick/layout.json`** (FROZEN once written, fractions of face W and wall H so it is camera-free): from the Fable audit — window w 0.16 W, h 0.12 H, centres x 0.35 / 0.82 W, top row head 0.04 H below the coping, row pitch 0.28 H, frame width 0.25 × glass width, frame proud 0.05–0.08 m, cornice projection ≤ 0.02 W, coping+cornice height ≤ 0.05 H, landing depth 0.15 W (UNVERIFIED), landings at the window-row heights, sign box 0.12 H tall with top at 0.50 H, awning span ≥ 0.9 W below the sign box, storefront h ≈ 0.15 H over a stall riser, door h 0.22 H, AC on the sign box left, roof ladder stiles end ≤ 0.02 H below the coping top (no handholds above). Every entry carries `source: "audit r2 Fable Lx / Astra Ly"`. | — |
| B2 | **`V12_LAYOUT`** in kernel-chain after V12_CENSUS: for each layout key, measure on part AABBs by role (window assemblies: centre x/W, top/H, w/W, h/H; frame proud = frame z − wall face z; cornice projection; landing depth = landing z extent; signbox h/H and top/H; awning span/W; ladder top vs coping top). Fail text names the key, measured, expected ± tolerance. | ±0.05 of W or H per key; proud 0.05–0.08 m |
| B3 | **passes.json → 3 passes**: P0 massing (unchanged wording + "dimensions from layout.json: W, H, depth"), P1 "openings + trims" (merged; frames PROUD per layout, no reveal rule; cornice/coping per layout; sills; awning + sign box + AC per layout), P2 ironwork (landing depth 0.6–0.9 m and inside the landing x-range, ladder ends below coping). Each item cites the layout keys it must satisfy and ends with the reopen sentence. P4 palette is GONE (B4). Update `census._pass` accordingly. | — |
| B4 | **`scripts/calibrate-palette.mjs`**: reads regions.json (Job A) + target, writes `meta.palette` hex per zone = median target colour of that zone (frame, sill, coping, iron, glass, awning, signbox, ac, brick, roof), rewriting ONLY the palette block of `facade.mjs` (regex on `palette: {…}`), deterministic. No seat. | — |
| B5 | README: replace the cornice 0.2–0.6 / parapet 0.3–1.2 bands with "per layout.json"; delete "nothing sits proud"; add the 3-pass order and the sentence "After capture the harness compares your render with the target; a failed likeness row comes back to you with both images — reopen the responsible parameter, palette work included." | ≤ 140 lines |
| B6 | tests: fixture per V12_LAYOUT key class (window off-centre, frame recessed, cornice too deep, landing too deep, ladder above coping) each failing on its own code; smoke fixture stays green (layout skipped when `meta.layout === false`). | — |

## Run-3 plan
Reset module to smoke → P0 → P1 → P2 seats (Astra) with likeness in the repair slot → calibrate-palette
(script) → final capture + compare → round-3 audits (both seats) → stop when both audits report no
gap above "minor" or after round 3. Report: seats used, tokens, wall time, likeness table, owner still.
