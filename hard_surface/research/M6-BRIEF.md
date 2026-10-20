# M6 brief — DSL gaps surfaced by the blind seats (implementer seat, Opus 5)

Read: `PLAN.md` §1.1–1.2; `src/compile/{resolve,expand,composites,build}.js`; `src/parts/lib/railing.json`
(its DEVIATION note) and `wheel.json`; `dsl/examples/cart.json` (MVP-STUB note); `src/validate/v0.js`,
`v2.js`, `v3.js`; `test/{grammar,composites,m5}.test.js`. 89 tests green. No commits, no CS2/BlindLoop-
frozen edits, no skills. `subjects/tenement_block/spec.json` is the BASELINE: it must still compile to the
**same specHash + same capture sha** (`9166a66e…` is the M0 massing; the M2 full spec hash is
`h32:a7e21c69`, capture `out/m2/tenement-target.png`) unless a change below is opted into by a spec.

## Gaps (all three were reported by builder seats as blockers or forced workarounds)
1. **Composites as parents.** `attach.to` may name a composite part id (resolves to its *root*
   sub-part) or `composite.sub` (a named sub-part). V0 accepts both; `solve()` resolves after
   expansion; V2/V3 see ordinary parts. Test: railing on a `landing` composite by id, and a lamp
   on `landing.deck`.
2. **Per-instance children.** A part attached to a `repeat`ed or `mirror`ed parent is expanded
   once per parent instance (`child#k`, `child~m`) unless it sets `"instance": 0` (anchor only).
   The wheel composite's hub then rides every mirrored tyre, closing the cart.json MVP-STUB.
   V3 contact graph and V6 must handle the expanded set. Test: mirrored wheel pair with hubs on
   both; repeated balcony with a railing on each.
3. **`alignU`** ∈ {start, center, end} (default center) — anchors the child's extreme along the
   face's u axis, symmetric to `align` on v. With this, rewrite `railing.json` as **open bars**:
   bottom rail plate + top rail plate + N posts via `repeat` between them, no infill web; posts
   ≥ styleFloor. Keep the old version as `railing_web.json` so the BASELINE hash is unchanged
   (baseline keeps referencing `railing`? — NO: baseline references `railing`; to keep its hash,
   name the new one `railing_open` and leave `railing` = web. Document both in SPEC.md).
4. `dsl/SPEC.md`, `dsl/schema.json`, builder prompts' rule lists updated for 1–3 (the prompts
   embed SPEC.md, so mostly automatic; check `prompts/builder-c.md` for a hard-coded "composites
   cannot be parents" line and remove it).
5. New example `dsl/examples/balcony-open.json`: mass + repeated balcony ×2 + `railing_open` on
   each via per-instance children; passes V0–V7 + V10; wired into `npm run check`.

## Evidence
`npm run check` tail (count, green); `node scripts/check-spec.mjs dsl/examples/balcony-open.json`;
BASELINE unchanged: `node -e` print specHash of `subjects/tenement_block/spec.json` == `h32:a7e21c69`
and a fresh `capture.mjs` of `subject=tenement_block&view=target` sha == sha of `out/m2/tenement-target.png`
(dev server via preview tool only; stop it after). One capture of `balcony-open` (register it in
SUBJECT_SPECS as `balcony_open`) at `view=threeQuarter` to `out/m6/balcony-open.png`; view it and state
in one sentence whether the bars are open and every railing sits on its own balcony.
README Status → "M6 done <date> …". Report: PASS/FAIL per item, deviations, one failing excerpt.
