# M5 brief — Generality: vehicle subject (implementer seat, Opus 5)

Read: `PLAN.md` §2 (V9), §7 M5; `src/compile/resolve.js` (contacts), `src/validate/index.js`,
`v3.js`, `v7.js`, `limits.json`; `src/parts/lib/railing.json` (composite shape); `refs/README.md`;
`scripts/gen.mjs` (subject discovery, prompts), `src/app.js` SUBJECT_SPECS. M0–M3 green (74 tests).
No commits, no CS2/BlindLoop-frozen edits, no skills. Do NOT touch `subjects/tenement_block*`.

## Scope
1. **Contacts** `hangs-below` (child's +Y-most face touches parent's −Y face; child hangs under,
   `embed` as usual) and `embedded` (child centre placed at the parent point, at depth
   `embed` inside along −n; V2 rule: child volume ∩ parent ≥ 50 %). Add to `resolve.js`,
   `v2.js`, `dsl/SPEC.md`, `dsl/schema.json`. Tests for each (pass + one broken fixture each).
2. **V9 symmetry** `src/validate/v9.js`: when `spec.class` ∈ limits.symmetricClasses
   (`["vehicle","robot"]`) and a part has `role` in limits.v9.roles (`wheel`, `headlight`,
   `mirror`, `door`, `leg`, `arm`) without `mirror:true` and without a twin (another part of
   the same role whose world AABB is its X-mirror within 2·EPS), emit an **advisory** (never
   blocking, PLAN §2). Test: pickup with one wheel → advisory; mirrored → none.
3. **Vehicle limits**: `limits.v7` add `wheel_radius_frac_of_length:[0.1,0.2]`,
   `ground_clearance:[0.15,0.5]` (wheel role bottom = 0, chassis bottom within range),
   `cab_h_le_total_h:true`. Flag `_ratified:false`. V7 skips rules whose roles are absent.
4. **Composite** `src/parts/lib/wheel.json` (ring tyre + box hub, dims [diameter, width,
   diameter], attaches via its hub; note that `ring` axis must be X for a side-mounted wheel —
   if `ring` only builds around Y, add a `axis:"x"` param to the ring prim path in
   `prims.js`, genus 1 preserved, winding test must pass).
5. **Target inventory** `refs/pickup_truck.README.md` (text, no image): cartoon low-poly
   pickup, ~4.8 m long, 1.9 wide, 1.8 tall; chassis slab, cab with windshield + two side
   windows as inset boxes, hood, open bed with three low walls, tailgate, four wheels (mirror
   pairs, radius 0.38), two headlights, two mirrors, front bumper, rear bumper, roof rack
   optional. All parts touch chassis/cab/bed. Register `pickup_truck` in `app.js`
   SUBJECT_SPECS pointing at `subjects/pickup_truck_llm/spec.json` (will not exist until the
   LLM run; loader must warn-and-default if missing, not crash) and make `gen.mjs` accept
   `--inventory refs/pickup_truck.README.md` for the lister text fallback.
6. **Hand smoke spec** `dsl/examples/cart.json` (prop: box body + 2 mirrored wheels via
   `hangs-below`) passing V0–V7 + V10 + no V9 advisory; wire into `npm run check`.
7. Camera for `view=target` is fine as-is (provisional 30/45) — `refs/pickup_truck.camera.json`
   copied from the tenement one with `provisional:true`.

## Evidence
`npm run check` tail (all green, count); `node scripts/check-spec.mjs dsl/examples/cart.json`;
V9 advisory text from the one-wheel fixture; `node scripts/gen.mjs pickup_truck --runner file
--inventory refs/pickup_truck.README.md` run once → show the pending lister prompt path.
No dev server needed. README Status → "M5 mechanism done <date>; blind LLM run pending".
Report: PASS/FAIL per item, deviations, evidence paths, one failing excerpt.
