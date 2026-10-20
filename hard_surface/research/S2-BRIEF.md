# S2 brief — kernel validators + pass runner (Opus implementer, 2026-09-12)

Authority: `V2-TEST-PLAN.md` §3, §4, §5, §6 row S2. S1 landed (see `research/S1-BRIEF.md`;
kernel at `src/kernel/`, README there is the author API; smoke `subjects/facade_brick/facade.mjs`;
`scripts/check-module.mjs`; `scripts/bench-kernel.mjs`; app serves `facade_brick` on port 4210,
capture URL `http://127.0.0.1:4210/?capture=1&subject=facade_brick&seed=1&view={target|threeQuarter}&size=900`).
Working dir `D:\Git\checkout\tools\LLMModeling`. Never touch `refs/**`, `src/validate/limits.json`,
`tools/BlindLoop/config*.json`, `tools/CharacterStudioV2`, or v1 validator files (`src/validate/v*.js`,
`index.js`, `obb.js`, `repair.js`). New sibling modules only. No commits. `npm run check` must
stay green; add the new files to the `check` script's `node --check` list and add tests to `test/`.

## Deliverables

1. `package.json`: exact pin `"three-mesh-bvh": "0.9.15"`, `npm install`.

2. `src/validate/kernel-chain.mjs` — `export async function validateParts(meta, parts, limits = DEFAULT_LIMITS)`
   returning `{pass, violations, advisories, text, measurements, timings}` with the same violation
   object shape as `src/validate/index.js` (`{v, part, measured, limit, hint, blocking}`) and the
   same ≤8-line `reportText` rule (`index.js:169-178`; reuse that function by import). Chain order,
   stop at first failing validator (as `index.js:135-141`):
   - **V1′ manifold**: every part `solid.status() === "NoError"`, `solid.genus()` finite. Merged
     mesh winding: reuse the check in `test/winding.test.js` (import its helper or copy the maths).
   - **V5 feature size**: per part, min AABB extent ≥ `limits.styleFloor[meta.class]` (0.06 for
     building). Report the part and the extent.
   - **V2′ contact (real surfaces)**: for each `touches` entry `[a, b]` (part a declares it
     touches b): penetration volume `K.intersect(a,b).volume()`. Zero volume → closest-point
     distance between the two meshes via `three-mesh-bvh` (`MeshBVH.closestPointToGeometry` or
     `bvhcast`) must be ≤ `limits.epsAbs` (0.01 m). Declared touch with gap > eps → `V2_GAP`.
     Penetration deeper than `limits.overlapClash` fraction of the smaller volume is NOT a V2
     failure here (V6 handles it).
   - **V3′ connectivity**: `union` of all parts with `role !== "prop"` → `decompose().length === 1`
     else `V3_FLOAT` naming the parts in the extra components (map components back to parts by
     AABB containment or by intersect volume > 0). Plus: every non-prop part must reach a ground
     part (AABB min y ≤ eps) through the measured contact graph (edges = pairs with intersect
     volume > 0 OR closest distance ≤ eps, tested for declared `touches` AND for all AABB-overlap
     pairs as broad phase). Unreachable → `V3_UNSUPPORTED`.
   - **V6′ clash**: for every AABB-overlapping pair, `intersect.volume() / min(volA, volB)`;
     > `limits.overlapDuplicate` (0.9) → `V6_DUPLICATE`; > `limits.overlapClash` (0.2) →
     `V6_CLASH`, unless the pair is a declared `touches` pair with `embed: true` on the part
     (explicit embedding allowed, e.g. a bar seated in a landing). Document that flag in
     `src/kernel/README.md` (one line, additive edit).
   - **V4 ground**: min y of the whole assembly within eps of 0; footprint COM inside the
     ground-contact convex hull — copy the maths from `src/validate/v4.js` onto part AABBs.
   - **V7 role table**: import `src/validate/v7.js` if its input is AABB+role based and can be fed
     from parts; else re-implement the rows in `limits.v7` for roles `door, step, railing,
     parapet, window, awning` on part AABBs. Rows that need a floor height use `meta.floorH`
     (author-declared, default 3.5).
   - **V10 budget**: tris ≤ `meta.triBudget ?? 3000` (owner provisional number, NOT limits.json's
     8000), one material, no NaN vertices.
   `timings` = ms per validator (timing is allowed here: validators are not the kernel).

3. `test/fixtures/kernel/{gap,floating,thin-bar,clash}.mjs` — four author-style modules, each
   breaking exactly one validator: `gap` (bar declares `touches` wall but sits 0.05 m off →
   V2_GAP), `floating` (a box in mid-air, no touches → V3_FLOAT/V3_UNSUPPORTED), `thin-bar`
   (bar 0.03 m section → V5), `clash` (two overlapping bars 60 % → V6_CLASH).
   `test/kernel-chain.test.js`: each fixture FAILs with its own V-code as the FIRST violation;
   the smoke `subjects/facade_brick/facade.mjs` PASSes. Also a determinism test: validate twice,
   identical report JSON.

4. `scripts/pass.mjs <P> [--dry] [--item "<text>"] [--no-repair]` — the authoring runner from
   plan §4, in order:
   a. Assemble prompt: `src/kernel/README.md` verbatim; current `subjects/facade_brick/facade.mjs`
      verbatim; the pass item (from `--item` or `subjects/facade_brick/passes.json`, an array of
      five `{id, title, item}` objects you write from plan §1/§6: P0 massing + parapet perimeter +
      roof solids; P1 openings: 3×2 recessed windows with reveals, storefront cut, arched shop
      door; P2 trims: cornice profile, sills, awning; P3 ironwork; P4 palette); previous Fable
      sentence from `out/facade/P<N-1>/review.md` if present; the rules block (copy the wording
      from plan §4 "rules:" — TARGET = style and model not a trace; images 2–3 are your current
      render; edit ONLY `subjects/facade_brick/facade.mjs`; only `K.*`; metres; every part names
      `touches`; run `node scripts/check-module.mjs subjects/facade_brick/facade.mjs` before
      finishing; end with one `CHANGE:` line; no self-rating).
   b. Spawn Codex exactly as `tools/BlindLoop/adapters/worker-codex.mjs` does (copy its
      invocation and its stdin/stdout/stderr handling and comments — read that file), with
      `-C <LLMModeling dir>`, `-i refs/tenement-iso.png` always, plus
      `-i out/facade/P<N-1>/target.png -i out/facade/P<N-1>/threeQuarter.png` when they exist,
      `-o out/facade/P<N>/last.md`. Assert header `model: gpt-6-astra` and `reasoning effort:
      high` with `parseCodexTranscript` from `scripts/gen.mjs` (import it). Timeout 15 min.
      Record wall-clock and `tokens used`.
   c. Gate: `check-module` then `validateParts`. On FAIL and not `--no-repair`: ONE repair spawn,
      same prompt + the ≤8-line report text + "fix only this". Re-gate. Still FAIL → stop, exit 1,
      write everything below anyway.
   d. Capture `target` and `threeQuarter` via
      `BLINDLOOP_CONFIG=tools/BlindLoop/config.llmmodeling.json node tools/BlindLoop/capture.mjs --url <capture url> --out out/facade/P<N>/<view>.png`
      (run from repo root `D:\Git\checkout`; server must already be on 4210 — check with a GET,
      fail fast with a clear message if not).
   e. Write `out/facade/P<N>/`: `facade.mjs` (copy of the module after the pass), `report.json`
      (validator result), `timings.json`, `prompt.md` (what was sent), `last.md`, `repair.md` if
      any, stills. Then call `measure.mjs`.
   `--dry`: run a–e with `--item` text but with the prompt telling the model NOT to edit and to
   answer one question in its final message; skip the repair; still capture (unchanged module).
   The dry pass is used in S3 to prove images reach the model.

5. `scripts/measure.mjs <P>` — append one markdown row to `out/facade/measurements.md` (create
   with header if absent): pass, codex s, tokens, repairs, kernel build ms, booleans count,
   toThree ms, validator ms total, capture ms, edit-to-preview s (build+validate+capture), tris,
   parts, V-codes hit. Sources: `timings.json`, `report.json`, kernel counters (`K` exposes a
   boolean count per S1 — read `src/kernel/index.mjs`).

6. `src/app.js`: the `.mjs` branch must run `validateParts` (async) and put `validatorPass`,
   `violations` text into the capture manifest it already writes (S1 wrote `validatorPass: true`
   as a placeholder — find it and wire it). Lines commented `// V2:`.

## Stop point (report PASS/FAIL per line, one failing excerpt max, no transcript)
- `node --test test/kernel-chain.test.js`: 4 fixtures fail on their own code, smoke passes, determinism passes.
- `npm run check` green (v1 + new).
- `node scripts/pass.mjs 0 --dry --item "Do not edit any file. Answer: what colour is the awning in image 1?" --no-repair`
  runs end to end: Codex header asserted, answer captured in `out/facade/P0/last.md`, both
  stills written, `measurements.md` has one row. Report the answer text verbatim, wall-clock
  seconds and tokens. (If Codex is unreachable, report the exact error and finish everything else.)
- Server on 4210 still up.
