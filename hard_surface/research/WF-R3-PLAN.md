# Round 3 — reviews + baseline blind runs → plan (Opus 5.5, 2026-09-25)

Owner 2026-09-25: reviews by Opus 5.5 + Fable 5.1 subagents; plan + implementation on Opus 5.5; TEST seats are now
GPT 6 Luna (`--seat luna`) and Gemini 3.8 Flash Medium (`--seat gmed`); Opus 5.5 is the REFERENCE bar (`--seat opus`,
relay answered by a fresh Opus agent). The workflow passes when Luna and Gemini Medium build technically correct models.

## Baseline (current HEAD 00b179a + seat aliases), from the frozen starts
| run | harness | what the stills show |
|---|---|---|
| Luna pickup P1 | FAIL: attempt-1 V3_FLOAT (mirror heads 0.5 mm off arms); after repair only LK_AREA glass 0.61×, LK_VISIBLE wheel | windshield + side panes are slabs standing above the roof / out of the side (anchor error); boxy template cab |
| Gemini-M pickup P1 | FAIL: attempt-1 gate FAIL, glass 0.01×, headlights 0/2 visible; after repair only LK_VISIBLE wheel | — |
| Luna facade P2 | "PASS / ACCEPTED_WITH_RESIDUALS" | **not technically correct**: flight hangs in FRONT of both decks (z −1.25…−1.97 while decks are −1.25…0), `gateFor` then cut gates across most of each front rail (landings read railless), drop ladder runs to the ground THROUGH the awning, roof ladder ground-to-roof |
| Gemini-M facade P2 | PASS after repair (attempt-1 threw `BAD_ARG: ladder width … undefined`) | same three defects as Luna |

Harness defects found by the baseline (not model defects):
- **H1 stale review.** Luna's P2 verdict row 3 came from run 4's `out/facade/P2/review.md`, restored by the blind snapshot and
  archived with the seat's result → automatic ACCEPTED on a model nobody reviewed.
- **H2 own-hub occlusion.** Both pickup seats end on the identical row `LK_VISIBLE wheel … covered by part "hub_rl" (role hub)`,
  2 of 3, same px box; `hub_rl` is template geometry both kept. A wheel's own hub is counted as its occluder.
- **H3 template fails its own likeness.** `--prep-previous` P1 gate-only of start-P2 fails LK_AREA glass 0.44×, grey 1.52×.
- **H4 gates pass wrong ironwork.** No rule requires a flight's ends to land ON a deck; `gateFor` opens a gate wherever a
  flight's bbox crosses the rail line, even when the flight never arrives on the deck; the ladder-through-awning clash is
  not reported.

Reviews (both converge; `out/blind/exam/r3-*` not kept — summarised here):
- Opus 5.5: biggest weakness = fractions converted to metres by hand; only building ironwork is correct by construction.
- Fable 5.1: same, plus no row measures SHAPE (vertical template windshield passes everything) and prompts are 25–42 kB.
- Job-4 rows: C13 → one bounds constructor + harness-printed metre bounds (no boxAtCentre, no per-key prose);
  C15 → data (measure roofLadder.bottom, window.front.top) not prose; C16 → mostly done by gateFor, remove `gateAt`
  from author docs; C18 → defer (lamp LK_AREA is UNVERIFIED, remove it from ACCEPTANCE); G1 → never written, dropped.

## Job R3-A (building + harness truth) — one Opus implementer
1. **H1** `scripts/pass.mjs` verdict: `review.md` counts only when it records the module hash it reviewed (write
   `module: <hash>` into review headers the harness scaffolds; a review without a matching hash → `PREVIOUS REVIEW:
   UNREVIEWED`, verdict REVIEW_PENDING). `scripts/blind-test.mjs`: delete `review.md` from the pass folder before the seat
   runs. Test: a stale review.md with a different module hash never yields ACCEPTED*.
2. **H4 by construction** `src/kernel/assemblies.mjs`: new `K.assemble.fireEscape({wall, centreX, span, depth, levels:[y…],
   flightWidth?, dropLadder:{bottom}|null, railHeight?, idPrefix})` building the landings, one flight between each pair
   of levels whose treads start and end ON the decks (inside deck x and z), gates computed from the helper's own flights
   and ladder, drop ladder hung under the lowest deck and ending at `dropLadder.bottom`. The building P2 item becomes one
   call fed by measured keys. Keep `landing/flight/ladder` for other subjects but make `flight` refuse (BAD_ARG) endpoints
   outside any `wall`-attached deck when given `decks`, and `gateFor` refuse an element that does not arrive on the deck.
3. **H4 rules** `src/validate/rules/building.mjs`: `V11_FLIGHT_ON_DECK` (each flight's bottom and top tread lie within a
   landing deck footprint ± one tread, at deck y ± maxRise) and `V11_RAIL_COVERAGE` (gate openings ≤ element width + 0.2 m
   each; front rail coverage ≥ 50 % of span). Find why ladder-through-awning is not a V6 clash and fix it (iron vs any
   non-iron role overlap = clash). Tests: Luna's and Gemini-M's archived P2 modules (`out/blind/facade_brick/{luna,gmed}/P2/
   module.*.mjs` → copy into `test/fixtures/building/`) FAIL with these rows; run-4 geometry and a fireEscape-built module PASS.
4. **C15** measure `roofLadder.bottom` (measure-target.mjs, with evidence) or, if the target cannot support it, a labelled
   class default; print absolute datums (deck-top y per level, ladder bottom y) in MEASURED NUMBERS.
5. **H3** template-building: P1 output must pass its own P1 likeness (glass area, grey area). Fix the template (storefront /
   window pane sizes from measured keys, AC size) — not the bands. Test: template P1 gate-only likeness clean.
6. Remove `gateAt` from author-facing docs/items (`src/kernel/README.md`, facade P2 item); the kernel may keep it internally.
7. Author `file:line` in module throws (`scripts/check-module.mjs` from error.stack) — Gemini-M attempt-1 died on
   `ladder width undefined` with no line.
8. Regenerate `out/blind/facade_brick/start-P2.mjs` only if the template changes; keep run-4 facade byte-identical live.

## Job R3-B (vehicle + prompt) — after R3-A lands
1. **H2** likeness LK_VISIBLE: an instance's own assembly parts (same id suffix / assembly tag: wheel+tyre+hub) are never
   its occluders and count toward its visible px. Test: start-P1 gate-only at P1 → LK_VISIBLE wheel 3 of 3.
2. Vehicle helpers in assemblies.mjs: `K.assemble.pane({host, face, bounds, recess})`, `lamp({face, centre, diameter})`,
   `mirror({side, centreY, z, head, arm})` (pair, seated — no V3 float), `grille({face, bounds, slots})` (margins ≥
   MIN_FEAT, depth ≤ GROOVE_DEPTH_MAX, slot cuts counted by `grille.slots`), and `K.span({x,y,z})` bounds constructor.
   Nose parts refuse proud depth > bumper's (keeps the far wheel visible). `VEH_HANDBUILT` advisory. Test: a module built
   only from helpers + measured keys passes the full chain and V12 on every P1 key; helpers on every face pass V3/V5/V6.
3. Harness prints metre bounds per cited key (`inverse()` beside each `measure` in `layoutRules`) as ready `K.span`/helper
   arguments; round-trip test (inverse → measure = value; value ± 2×tol fails). H from the `lengthRoles` box (a detail above
   the roof cannot shift H); position tol = min(tol, 0.25 × feature extent).
4. Auto-fix deterministic rows before spending the repair: unique PALETTE_ZONE suggestion → rewrite + advisory; lateral
   V5_THIN only when penetration > GROOVE_DEPTH_MAX.
5. Shape: measure `window.front.top` (raked windshield) and make template-vehicle build the rake + hood step; add
   `LK_SILHOUETTE` (IoU of target foreground vs render mask inside the measured quad, band in classes/<class>.json) judged
   from P0. Test: raked template passes, box cab fails.
6. Prompt diet: P1 ≤ 12 kB, repair ≤ 0.6× first prompt (failing rows + diff + stills + local lines), items become helper
   calls, drop key restatements and the vehicle profile catalogue, drop LK_AREA lamp from ACCEPTANCE. Test asserts bytes.
7. Regenerate `out/blind/pickup/start-P1.mjs` from the new template.

## Then
Opus reference (`--seat opus`) + Luna + Gemini-M on pickup P1 and facade P2 from the regenerated starts; examiner = Opus
look at stills (technical correctness first: every part attached, stairs on decks, no clashes, panes inside hosts) + gate.
Pass = Luna and Gemini-M both reach the Opus reference's technical-correctness checklist.

## Round 4 result (after R3-A 230fc34 + R3-B 13bd49c), from the regenerated starts — `out/blind/r4-side-by-side.png`
| run | gate | likeness | layout | attempts | seat time | prompt |
|---|---|---|---|---|---|---|
| Opus 5.5 pickup P1 (reference) | PASS | PASS | PASS | 1 | — | 12.0 kB |
| GPT 6 Luna pickup P1 | PASS | PASS | PASS | 1 | 41 s | 12.0 kB |
| Gemini 3.8 Flash Medium pickup P1 | PASS | PASS | PASS | 1 | 87 s | 12.0 kB |
| Opus 5.5 facade P2 (reference) | PASS | PASS | PASS | 1 | — | 29.0 kB |
| GPT 6 Luna facade P2 | PASS | PASS | PASS | 1 | 70 s | 29.0 kB |
| Gemini 3.8 Flash Medium facade P2 | PASS | PASS | PASS | 1 | 83 s | 29.0 kB |
Stills: all three seats produce the same technically correct model per subject (panes inside hosts, mirrors seated,
flight on both decks, rails intact, drop ladder ends above the awning). Round 3 had 0 of 4 correct.
Residuals common to all seats (workflow-owned, not model-owned): grille slots do not read (one flat dark panel);
landing rails have no balusters (target is densely balustered); no door seams/handles or tail lamps; facade prompt 29 kB.
Caveat: the ready calls now carry the measured numbers, so these subjects no longer discriminate model skill — the
next test of the workflow is an UNSEEN subject (new target image, measure → template → passes) run blind.
