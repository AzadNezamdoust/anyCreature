# M2 brief — Full tenement by hand (two implementer seats, Opus 5)

Read first: `PLAN.md` §1.1 (facades, composite prims), §1.2 compile order, §7 M2;
`refs/README.md` (target inventory); `research/02-correctness.md` §CGA; `research/08-opus-revision.md`
G5/G6. Existing code: `src/compile/*.js`, `src/prims.js`, `src/validate/index.js` + `v2/v3/v5`,
`src/geom.js` (prism, wedge, ring, tube, stepStack, fan, loft, mirrorX), `src/app.js`.
M0+M1 green (46 tests). Do not regress. No CS2 edits, no BlindLoop frozen edits, no commits.

## Seat A — grammar + composites (mechanism)

1. **Facade grammar** `src/compile/grammar.js`. Input `spec.facades[]` per PLAN §1.1 (`on`,
   `face`, `occlude`, `split{axis,rule}`, `tile{<name>:{axis,rule}}`, `elements{<name>:{…}}`).
   Rule entries `[name, size]` or `[name, size, "*N"]` (repeat N) or `[name, "~"]` (fill
   remaining, split equally among `~` entries). Split runs on the parent face rectangle
   (u,v extents from `resolve.js` face frame). Output = derived parts appended to the solved
   list with ids `<facadeId>/<row>/<col>/<element>`, each with a real `attach`
   `{to: on, face, uv, contact: "socket"|"flush", embed}` so V2/V3 see them as ordinary parts.
   Elements supported: `window` (`dims:[w,h]`, `inset` → a box socketed `inset` deep, zone
   glass; plus `sill` plate under it if `sill` given; `lintel:"flat"|"arch"` — arch = prism
   half-round via geom `fan`/`ring` sized w×w/2, `// MVP-STUB` if approximated by a box),
   `door` (box socket, zone), `storefront` (big window box + `awning` composite), `pier`/
   `wall`/`base`/`cornice` = no geometry (empty regions), `cornice` may take `band` → plate.
   **Occlusion (08:G6):** grammar runs AFTER attach + expand; a tile whose face rectangle
   overlaps (in u,v) the contact footprint of any already-solved non-grammar part on that
   face (balcony, landing, stair, adjoining mass) becomes `wall` (no element). Record
   `occludedBy` on the tile in solved output.
2. **Composite prims** `src/parts/lib/*.json` + loader in `src/prims.js`: a composite is a
   spec fragment `{"schema":"pg/1-composite","params":{…defaults},"parts":[…]}` whose parts
   use `$w/$h/$d` and `$param` expressions (tiny evaluator: numbers, +,-,*,/, params). The
   compiler expands a composite part into its sub-parts (ids `<id>.<sub>`), first sub-part is
   `ground:false` root attached with the composite's `attach`; sub-parts attach to each other.
   Composites in this seat: `railing` (top rail plate + posts repeat + bottom rail; post pitch
   param; posts ≥ 0.05 thick), `stairFlight` (uses geom `stepStack` if it fits the bottom-
   centred contract, else N step boxes rests-on-top chain; params steps, rise, run, width),
   `landing` (plate + railing on 3 sides), `pipe` (box or `ring` tube, cap plate), `vent`
   (box + louvre stripes as zone-only, no geometry).
3. `dsl/SPEC.md` + `dsl/schema.json` updated for facades, composites, new prims (prism,
   wedge, ring, tube, stepStack) with genus declared in `PRIM_GENUS`; V1 must pass on all.
4. Tests: `test/grammar.test.js` (3 floors × 3 bays → 9 windows, all pass V2/V3; a balcony
   flush over row 2 col 2 → that tile occluded, 8 windows), `test/composites.test.js`
   (railing expands, all sub-parts pass V1–V7; stairFlight top step height = steps·rise),
   winding test extended to every prim in `PRIM_NAMES`. `npm run check` green.
5. Evidence: check output tail; `node scripts/check-spec.mjs dsl/examples/facade-demo.json`
   (new example: one mass + one 3×3 facade + one balcony occluding a tile) → PASS; one
   `capture.mjs --view threeQuarter` of facade-demo to `out/m2/facade-demo.png`; view it,
   one-sentence observation. Server via preview tool only; stop it after.

## Seat B — full tenement + props + qa sheet (runs after A is green)

1. `subjects/tenement_block/spec.json` → full per `refs/README.md`: three facades (mint 3×3
   front + 2-col side via a second facade on `-X`… only faces visible in the target view need
   windows: `+Z` fronts and mint `-X` side), basement half-window band on mint, fire escape
   on brick (two `landing` composites on `+Z` at floors 2/3 + `stairFlight` between, rot 0,
   `// MVP-STUB` if the diagonal flight is a wedge box), storefront on brick ground floor
   (awning composite `wedge`/box, big window, AC unit box above awning, bench box), tan:
   two balconies (bevelBox + railing) floors 2/3, arched door (lintel arch), stoop with
   railings, trash can (`ring` tube + lid), two crates (bevelBox stack), clothesline
   (`tube` thin from mint roof corner to tan balcony rail — must pass V5: ≥ styleFloor, so
   0.06 m rope, `// MVP-STUB` thickness), 4 shirts = plates hanging-below… hangs-below
   contact not in solver → use `flush` on rope `-Y` face with `align:"top"` and note.
   Roof: bulkhead + louvre, vent box on brick, pipes on tan too.
2. New composites needed: `awning`, `trashcan`, `crate`, `acUnit` — add to `src/parts/lib/`.
3. Must PASS `check-spec` (V0–V7 + V10) with ≤ 8000 tris. If V7 rejects an authored
   dimension, fix the dimension, never the limit.
4. `scripts/qa-sheet.mjs`: 3 captures (target, threeQuarter, back = azimuth+180°) composited
   into `out/qa/<subject>-sheet.png` (use `capture.mjs --url` with a `view=back` you add to
   app.js; compose with `sharp` if present in BlindLoop node_modules else write three PNGs
   side by side and skip compositing, note deviation).
5. Evidence: check tail; check-spec output; tri count; `out/m2/tenement-target.png` (target
   view) + qa sheet; view target still yourself and list which inventory items from
   `refs/README.md` are present/missing in one line each. Server stopped. README Status →
   "M2 done <date> … awaiting owner taste gate; next M3".

Report format both seats: PASS/FAIL per item, deviations, evidence paths, one failing excerpt.
