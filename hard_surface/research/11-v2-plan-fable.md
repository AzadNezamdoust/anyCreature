# 11 — v2 test-project plan (Fable 5.1 seat, independent, 2026-09-12)

Inputs: `10-postmortem*.md`, PLAN/WORKFLOW/SPEC, `src/**`, `refs/tenement-iso.png`. Not a rewrite:
v1 (`pg/1` spec → compiler → V0–V10) stays runnable for the comparison. UNVERIFIED marks guesses.

## 1. Scope statement

**Façade: the brick middle building, front face + its roof.** Why brick, not mint corner:
(a) it carries the ironwork that cost v1 the most loop time — fire-escape-open (r8, 36.2 min, three
merges) and fire-escape-width (r10) — so the one v1 comparison (§5) is sharpest there; (b) a single
flat face isolates the boolean/reveal/profile operations from corner-mitre work (the mint corner is
the *second* test, after the operations are proven); (c) the storefront is the largest cut in the
target and the awning is a pure extruded profile — two representation tests the mint face lacks.
Deviation declared: the target's brick building has no arch (it is on the tan one). The shop
entrance (right of the shop window) is authored as an arched opening; the owner's sentence after P1
may square it — the reveal cut is the same operation either way.

In scope, nothing else: (1) wall slab + returns + roof slab with the **parapet as a perimeter
wall** (roof interior visible; vent box, two pipes as plain solids); (2) 3 × 2 **recessed windows
with real reveals** (frame + glass inside the reveal, not proud as `grammar.js:26` `GLASS_PROUD`);
(3) **arched shop-door opening** + storefront cut; (4) **shaped cornice** = stepped profile
extruded along the parapet, plus sills; (5) **open fire-escape ironwork**: two landings, one flight,
ladder, bars ≥ MIN_FEAT; (6) awning as an extruded wedge profile; (7) palette zones. No
clothesline, bench, AC, neighbours.

Acceptance (all five, or FAIL): one 900 px still at the solved camera (`refs/tenement_block.camera.json`
theta 29.20°, phi 43.09°, `provisional:false`) + one `threeQuarter` still (`app.js:48`); §3 validators
PASS; tris ≤ 3000 (a third of `limits.json:9` building 8000 — OWNER number, provisional); 3× capture
byte-identical (`preflight.mjs:89`); owner sentence "reads as the brick tenement".

## 2. Representation

**Primary: a procedural JS module written against a closed kernel API, solids by manifold-3d.**
The author writes `subjects/facade_brick/facade.mjs` exporting `meta` and `build()`; it imports
only `src/kernel/index.mjs` (`K`), metres, *local* frames. Not a JSON op list (no loops/derived
dimensions — v1's 17 hand-placed treads, `10-postmortem-fable.md:63-67`), not raw three.js (route
4, `03-landscape.md:190`, correctness 2). Solids via manifold-3d (`02-correctness.md:78-79`;
`manifold-3d@3.5.3` per `npm view`); ironwork bars are solids too but **never booleaned together**
— `build()` returns `parts[]` of `{id, solid, zone, role?, touches?:[ids]}`; union happens only
inside validators. Kernel surface (deterministic, no RNG, no clock):
`box(dims)` (same local frame as `prims.js:5-8`: x/z centred, y from 0), `extrude(profile, depth,
{holes})`, `revolve(profile, segs)` (finials), `cut(a,b)`, `union(a,b)`, `.at([x,y,z])`,
`.rotY(deg)`, `profile.{rect, arch, offset, stepped, wedge}`, `repeat(n, pitch, fn)`.

Mini-example (arched doorway + stepped reveal; what Astra actually writes):
```js
import * as K from "../../src/kernel/index.mjs";
export const meta = { class: "building", seed: 1,
  palette: { brick: "#b5412f", trim: "#5a2a22", glass: "#8fc1d6", iron: "#2b2e33" } };
export function build() {
  const W = 8.0, H = 11.0, T = 0.35;                       // wall width, height, thickness (m)
  const parts = [];
  let wall = K.box([W, H, T]);                             // local: x centred, y 0..H, z -T/2..T/2
  const door = K.profile.arch({ w: 1.2, h: 2.4, rise: 0.6, segs: 12 });   // rect + half-round head
  wall = K.cut(wall, K.extrude(door, T + 0.02).at([2.6, 0, -T / 2 - 0.01]));  // through opening
  const reveal = K.extrude(K.profile.offset(door, 0.12), 0.25).at([2.6, 0, T / 2 - 0.25]);
  wall = K.cut(wall, reveal);                              // 12 cm stepped reveal, 25 cm deep
  parts.push({ id: "wall_front", solid: wall, zone: "brick", role: "massing" });
  parts.push({ id: "door_leaf", solid: K.extrude(door, 0.05).at([2.6, 0, -T / 2 + 0.02]),
               zone: "trim", role: "door", touches: ["wall_front"] });
  return parts;
}
```
Determinism: manifold-3d is single-threaded WASM, same input → same mesh (vertex-order stability
UNVERIFIED until the 3× capture passes); colour jitter stays `rng("<seed>:<partId>")`
(`build.js:13`, `geom.js:116`); the module text is the seed artifact (its hash replaces `specHash`,
`spec.js:24`). `scripts/check-module.mjs` rejects any import other than `K` and any `Math.random`,
`Date`, `fetch`, `performance`. Export: solid → `getMesh()` → non-indexed `BufferGeometry` →
`paint()` → `mergeGeometries` (`geom.js:520`) → one `assetMaterial()` (`material.js:9-16`) →
`GLTFExporter` binary with COLOR_0 (`exporters.js:14,39-54`, unchanged).

## 3. Keep / change / delete (by file, test path only; v1 files untouched)

Keep unchanged: `src/geom.js`, `src/material.js`, `src/exporters.js`, `v4.js` (AABB min-y +
footprint COM, `v4.js:1-16`), `v7.js` (role table on part AABBs; author supplies `role`), `v10.js`,
`limits.json` (frozen, `config.llmmodeling.json:50`), `v9.js` (never fires for building),
`scripts/qa-sheet.mjs`, `scripts/solve-camera.mjs`, `refs/**`, `tools/BlindLoop/capture.mjs` +
`config.llmmodeling.json` (capture URL contract, line 9).
Change (new sibling modules, so `npm run check` for v1 still passes):
- `src/validate/index.js:123-133` chain → `src/validate/kernel-chain.mjs` taking `parts[]` of
  solids; same `{pass, violations, text}` contract and ≤8-line `reportText` (`index.js:168-178`).
- V1 (`v1.js` per-prim χ) → `solid.status() === NoError` per part, genus from `solid.genus()`;
  winding still checked on the merged mesh (`test/winding.test.js`).
- V2 (`v2.js` AABB samples via `obb.js:7-11`) → real surfaces: for each `touches` pair, penetration
  = `K.intersect(a,b).volume()`; flush contact (zero volume) = closest-point distance ≤ EPS via
  `three-mesh-bvh@0.9.15` (`npm view`, not yet installed — `package.json:14-19` has only three).
- V3 (`v3.js:7-9` DEFERRED manifold cross-check) → promoted: union of all parts →
  `decompose().length === 1`, plus every part reaches a ground part through the measured contact
  graph. Props excluded by `role: "prop"` (not in this test's scope anyway).
- V5 (`v5.js`) → keep per-part min AABB extent ≥ MIN_FEAT (bars, treads; `limits.json:8`
  styleFloor building 0.06); thickness of remaining wall behind a cut asserted **in the kernel**
  (`K.cut` throws if a reveal leaves < MIN_FEAT) — sampled thickness deferred.
- V6 (`v6.js:3-7` AABB) → `K.intersect` volume ÷ smaller volume, same thresholds
  (`limits.json:12-13`), AABB as broad-phase only.
- `src/app.js:31-42` `SUBJECT_SPECS` → add `facade_brick` pointing at the module; the capture URL
  stays `(subject, view, seed, size)` (`app.js:27-30`).
- `package.json`: add `manifold-3d` and `three-mesh-bvh`, exact pins; vite may need
  `optimizeDeps.exclude: ["manifold-3d"]` for the WASM (UNVERIFIED).
Delete from the test path (files stay for v1): `v0.js` schema, `v2/v3/v6` AABB maths, `obb.js`
contact helpers, `repair.js` nudges (meaningless on a booleaned solid), `resolve/expand/grammar/
composites/prims` + `parts/lib` (not called), `embed`/`uv` (`SPEC.md:42-44`'s premise is gone).
New: `src/kernel/{index,profile,toThree}.mjs`, `scripts/{check-module,pass,measure}.mjs`,
`subjects/facade_brick/facade.mjs`, `test/fixtures/kernel/{gap,floating,thin-bar,clash}.mjs`.

## 4. Authoring protocol

One author (Astra), one seat per pass, target-aware. `scripts/pass.mjs <P>`: (1) spawn Codex with
the images attached; (2) `check-module` + kernel-chain gate; (3) on FAIL, ONE repair spawn with the
≤8-line report (K = 1); (4) capture `target` + `threeQuarter` via `tools/BlindLoop/capture.mjs`
(`capture.mjs:11`); (5) write `out/facade/P<N>/` {stills, report.json, timings.json, tokens}; stop.
Fable writes one PASS/FAIL sentence to `out/facade/P<N>/review.md`; the owner sees the `target`
still. No Blind Loop, judges or worktrees until the §1 owner sentence lands.

Codex invocation (flags verified from `codex exec --help`; `-i` attaches images):
```
codex.exe exec -c mcp_servers={} --skip-git-repo-check -s workspace-write -C tools/LLMModeling
  -m gpt-6-astra -c model_reasoning_effort="high"
  -i refs/tenement-iso.png -i out/facade/P<N-1>/target.png -i out/facade/P<N-1>/threeQuarter.png
  -o out/facade/P<N>/last.md "Follow the instructions below."   (prompt via stdin, closed —
  `worker-codex.mjs:22-25`; header assertion model/effort as `gen.mjs:181-192`)
```
Prompt skeleton (inlined, in order): `src/kernel/README.md` (API ≤120 lines, with the §2 example);
current `facade.mjs`; the pass item (one paragraph: which of massing → openings → trims → ironwork
→ palette, what "done" looks like in the target); previous Fable sentence; rules: image 1 is TARGET
= style and model, not a trace (`WORKFLOW.md:20-27`); images 2–3 are your current render; edit
ONLY `facade.mjs`; only `K.*`; metres; every part names what it `touches`; run `check-module`
before finishing; end with one `CHANGE:` line, no self-rating (`worker-codex.mjs:97-103`). Repair
prompt = same skeleton + report text. P0 gets the target image only (no render exists yet).

## 5. Measurement

`scripts/measure.mjs` appends one row per pass to `out/facade/measurements.md`: codex wall-clock s
and `tokens used` (parser `gen.mjs:181-207`), repairs, kernel build ms, boolean count + ms (kernel
counters), validator ms, capture ms, edit-to-preview s (build + validate + capture), tris, parts,
V-codes hit. "v2 works" (none ratified): all five §1 features after P4 with ≤ 2 repairs total;
edit-to-preview ≤ 5 s and build + validate ≤ 1 s at ≤ 3000 tris (v1 line was 300 ms at 8k,
`bench.mjs:3`; booleans cost more, 1 s is the line); tokens ≤ 15k per pass, ≤ 75k total (PLAN.md:130
budgeted 25k per object; the image in context earns 3×, no more); P0–P4 wall-clock ≤ 90 min with
reviews. The one v1 comparison: v1's brick façade took three loop runs (r8 36.2 + r10 12.2 + r11b
10.5 = 58.9 recorded min, `10-postmortem-astra.md` run table) for open fire escape, its width and
the awning — still no reveals, arch or cornice profile. Side-by-side `out/facade/compare.html`
(`qa-sheet.mjs` pattern): v1 `tenement_block_llm` still cropped to the middle building vs v2 P4;
v1 middle-building tris = sum of `solved.json` `triCount` under `mass_m` (UNVERIFIED until run).

## 6. Work plan

| # | Owner | Step (≤ 1 session) | Stop point |
|---|---|---|---|
| S1 | Opus | Install pins; `src/kernel/*` + `toThree`; `check-module`; register `facade_brick` in `app.js:31`; hand smoke module (box + one arch cut + one bar) | Fable: node AND vite both build the smoke; 3× capture byte-identical; bench numbers |
| S2 | Opus | `kernel-chain.mjs` (V1′ V2′ V3′ V5 V6′ V7 V10), K=1 repair path, `pass.mjs`, `measure.mjs`, 4 broken fixtures | Fable: each fixture FAILs on its own V-code, smoke PASSes |
| S3 | Fable | Dry pass: `pass.mjs 0 --dry` with a no-op item; Astra asked to name the awning colour in the target | Owner: cost of one pass (s, tokens); images provably reached the model |
| S4 | Astra / Fable / owner | P0 massing + parapet perimeter + roof solids | owner still |
| S5 | Astra / Fable / owner | P1 openings: reveals, storefront cut, arched door | owner sentence on the arch deviation |
| S6 | Astra / Fable / owner | P2 trims: cornice profile, sills, awning | owner still |
| S7 | Astra / Fable / owner | P3 ironwork: landings, flight, ladder, bars | owner still; V5/tri numbers |
| S8 | Astra / Fable / owner | P4 palette | owner sentence (§1 acceptance) |
| S9 | Fable | Measurement report + compare.html + this plan's thresholds PASS/FAIL | Owner: proceed to mint corner (mitre test) or stop |

Owner gates never self-ratified: tri cap 3000, the arch deviation, §5 thresholds, go/no-go at S9.
Commits only when the owner asks; pathspecs = the new files above. Risks, one retiring check each:
- manifold-3d WASM fails under vite or Node 24 → S1 smoke in both runtimes.
- Boolean output not byte-stable → S1 3× capture (`preflight.mjs:89-91`).
- ~20 cuts blow the 1 s line → S1 bench, smoke ×20 cuts; fix = one `cut(wall, union(tools))`.
- `-i` images not seen by the model → S3 colour question.
- Astra routes around the kernel (raw three, `Math.random`, literal mesh arrays) → `check-module`
  on the S3 dry-pass output.
- Thin ironwork trips V5 or the tri cap → S7 numbers; fix = bar section = MIN_FEAT, 4-sided bars.
- Arched door reads wrong to the owner → S5 sentence; fallback = square opening, same reveal op.
- Kernel too poor for the cornice/awning profile → P2 report names the op; adding a profile helper
  is an Opus edit, never an Astra workaround (ruling logged in `docs/questions.md`).
