# 07 — Architecture proposal (Fable seat, independent; pre-exchange)

Inputs: 01–05. Citations `NN:§` = research file + section. **RULING** = Fable design call;
**OWNER** = owner-ratified number/decision, never self-ratified.

## 0. One-paragraph shape

The LLM never emits geometry or world coordinates. It emits an **attachment program**
(`spec.json`): primitives in metres, each non-root part attached to a parent *face* at
*(u,v)* with a *contact mode*; facades are a split grammar; repetition and symmetry are
macros. A deterministic JS compiler resolves transforms, builds one merged flat-shaded
vertex-coloured mesh (CharacterStudioV2 `geom.js` fork), and runs ten numeric validators
before any pixel exists. Only PASSing candidates reach the BlindLoop judge. Generation is
tiered (massing → facades → props), each tier validated and repaired (≤2 re-prompts) before
the next. Everything downstream of the spec text is deterministic and cached; LLM
non-determinism is contained to spec authoring (03:D). Blender never sits in the loop (03:D).

## 1. Pipeline + data contracts

```
TARGET.png ──(once per target, frozen)──► refs/<t>.camera.json   (two-slope solve, 04:D)
                                          refs/<t>.parts.json    (VLM inventory + measured boxes, 04:A)
                                          refs/<t>.mask.png      (silhouette)
parts.json + prompts ──► LLM builder ──► assets/<t>/spec.json   (tier 1..3 fragments merged)
spec.json ──► compile.js ──► parts[] {mesh, xform, role, color} ──► validate/* ──► report.json
                          └─► merge → one BufferGeometry → studio (capture) / GLB export
```

### 1.1 spec.json (v0 schema; JSON, metres, y-up, no world coords)
```jsonc
{ "asset":"tenement_iso", "seed":1, "budgetTris":8000, "class":"building",
  "unit":{"part":"door_L","m":2.0},
  "parts":[
   {"id":"mass_L","prim":"box","dims":[6.0,9.6,8.0],"ground":true,"role":"massing","paint":"mint"},
   {"id":"mass_M","prim":"box","dims":[5.2,10.4,8.0],
    "attach":{"to":"mass_L","face":"+X","uv":[0,0],"contact":"flush","align":"bottom"},"role":"massing","paint":"brick"},
   {"id":"parapet_L","prim":"plate","dims":[6.2,0.3,8.2],
    "attach":{"to":"mass_L","face":"+Y","uv":[0.5,0.5],"contact":"rests-on-top"},"role":"parapet","paint":"stone"},
   {"id":"balcony_R2","prim":"bevelBox","dims":[2.4,0.14,1.0],
    "attach":{"to":"mass_R","face":"+Z","uv":[0.5,0.62],"contact":"flush"},
    "repeat":{"axis":"Y","count":2,"pitch":3.0},"role":"balcony","paint":"iron"},
   {"id":"rail_R2","prim":"railing","dims":[2.4,0.95,0.04],
    "attach":{"to":"balcony_R2","face":"+Y","uv":[0.5,0.95],"contact":"rests-on-top"},"role":"railing","paint":"iron"}
  ],
  "facades":[
   {"on":"mass_M","face":"+Z","floors":3,"floorH":3.2,"bays":3,
    "tile":{"window":[0.9,1.4],"sill":0.08,"lintel":"arch"},
    "ground":{"kind":"storefront","awning":[4.0,0.25,1.2],"door":"door_M"}}
  ],
  "paint":{"mint":"#9fd3b8","brick":"#c9573f","iron":"#3b3f4a","stone":"#b9b3a8"}
}
```
- `prim` ∈ closed vocabulary compiled from `geom.js`: box, bevelBox, taperBox, prism,
  wedge, plate, stepStack, ring, tube, lathe, extrudeProfile(+holes), plus **composite
  prims** (railing, stairFlight, fireEscapeLanding, vent, awning) that are themselves
  spec fragments authored once and library-learned (03:T5; 02:T1).
- `attach.face` ∈ ±X/±Y/±Z of the parent's *local* box frame; `uv` ∈ [0,1]² on that face;
  `contact` ∈ {rests-on-top, flush, socket(d), embedded, hangs-below} (02:T1; 05:§3).
  `align` ∈ {bottom, center, top} for side attachments. Rotated prims (stairs, pipes)
  carry `rot` about the attach normal only; local frame = parent face frame
  (**RULING** on 02:OQ5 — no free rotations in v0).
- `repeat`/`mirror` are macros expanded by the compiler; the LLM never copies coordinates.
- `facades[]` is CGA-lite: split(floors) → split(bays) → tile. Windows are derived; a tile
  whose area is touched by another part (balcony, landing, adjoining mass) becomes wall
  (02:§CGA occlusion). Implement splits + occlusion only (~200 lines).
- Root parts: `ground:true`, bottom snapped to y=0. Every other part has `attach`. A part
  with neither is a V0 FAIL, never a warning (01:C3 — the warning tier is where floating
  parts shipped).

### 1.2 report.json (validator output, fed verbatim to the repair prompt)
`{pass, tris, violations:[{v:"V3", part, measured, limit, hint:"move balcony_R2 0.12 m along -Z to touch mass_R"}]}`
Hints state the *move in metres* (01:T "say the move, not the gap"). ≤8-line text rendering.

## 2. Validators (run order; first failing class stops; zero LLM tokens) — from 02:T2

| V | Check | FAIL rule | Auto-repair | Re-prompt |
|---|---|---|---|---|
| V0 | schema, DAG, ground rule, dims within class priors, repeat fits parent face | any | — | yes |
| V1 | per-prim watertight + winding (χ=2) | any | compiler bug → abort round | — |
| V2 | declared contact is real: SDF samples of child contact face vs parent surface; flush/rests ≤EPS on ≥90 %; socket pen ∈[0.5d,1.5d]; embedded ∩≥50 % | gap>EPS | gap ≤ max(5·EPS, 10 % child extent): translate along normal | larger gap |
| V3 | contact graph connected + every part rooted to ground; manifold union comp==1 as flagged cross-check | orphan cluster | never | yes, name orphan + nearest parent |
| V4 | ground min-y=0; COM inside ground-footprint hull | any | — | yes |
| V5 | min feature: OBB min extent ≥ MIN_FEATURE; p5 thickness for non-box prims; repeat gap < 2·PX = sub-pixel | any | grow thin axis (attached face fixed); collapse sub-pixel repeat to block+stripe | if repair breaks V6/V7 |
| V6 | pairwise intersection vol ÷ smaller: >0.9 duplicate; 0.2–0.9 without socket/embedded = clash | clash | delete ≥0.9 duplicate | clash |
| V7 | role-keyed relative-scale table (door 2.0–2.4, step rise .14–.20, rail .9–1.1, window<floorH, awning≥door top, parapet .3–1.2, …) | any | never (OWNER numbers) | yes, quote rule + measured |
| V8 | id-buffer render at frozen camera: part <6 px → hidden-drop or grow; tri budget | budget | drop invisible from export | budget |
| V9 | symmetry when role implies it and `mirror` absent (vehicles/robots) | chamfer>2·EPS | — | yes |

Constants: EPS = max(1 cm, 0.5 % bbox diag); PX = ortho height/900; MIN_FEATURE =
max(style floor, 3·PX). **OWNER**: px threshold (2 vs 3), style floors (prop 4 cm, trim
6 cm), V7 table, tri budgets (prop 2k, building 8k, vehicle ?). Live in
`src/validate/limits.json`, added to the run's frozenFiles.

**RULING**: manifold-3d union is a V3 *cross-check* behind a flag, not a gate dependency —
03:OQ1 leaves it unverified whether touching-not-overlapping parts union cleanly. The
contact graph is authoritative; union is promoted only after the 20-fixture check (M1).

## 3. LLM seats, budgets, caching

| Seat | Model | When | Input | Output | Budget |
|---|---|---|---|---|---|
| LISTER (VLM) | Fable 5.1 | once per target, frozen | TARGET.png + lister prompt (04:T6) | parts.json: inventory, parent, face, rel_size, unit_ref | 1 call |
| MEASURE | script | once per target | parts.json names → Grounding DINO + SAM boxes; door anchor → metres | measured fields in parts.json | 0 tokens; spike-gated (04:OQ3), fallback = operator-clicked boxes |
| BUILDER | Opus 5 | per tier (massing, facades, props) | SCHEMA.md + 2 worked examples + parts.json + prior tiers + report | spec fragment | ≤6k out/tier |
| REPAIR | Opus 5 | on FAIL, ≤2 per tier | prior fragment + ≤8-line report | edited fragment | ≤3k out |
| JUDGE | BlindLoop adapter (existing) | per round | TARGET + A/B/C/D | PICK/WHY | 3 runs, re-shuffled |

Per object worst case: 3 tiers × 3 calls ≈ 9 calls, ~40k tokens — vs img2threejs's own
80k–180k (01:B). Tier split per 02:T5 (whole-program emission collapses past ~15 parts).
Caching: `cache/<sha256(prompt+inputs)>.json`; identical inputs never re-call. The spec text
is the determinism artifact; compile is pure `f(spec, seed)`. Prompts include `SCHEMA.md`
in full (small-DSL RAG, 03:T7). One builder seat, never split across subagents (01:dead).

## 4. Capture + judge integration (BlindLoop web lane, 05:§1)

- Project exposes `dev/build/preview/check` with `--port --strictPort` passthrough; vite
  `base:"./"`, port **4210**; `?capture=1&subject=<asset>&seed=&view=&size=`; unknown
  subject warns + defaults; `setPixelRatio(1)`, square canvas; `__CAPTURE_MANIFEST__` =
  {triangles, materials:1, drawCalls:1, boundsM, validators:{pass, counts}, camera,
  subject, view, size}; `__CAPTURE_READY__` after the single render. Nothing in the capture
  path reads clock/DPR/random (05:§B).
- `view=target` = orthographic from `refs/<t>.camera.json` (θ, φ from two ground-edge
  slopes; 2:1 iso ⇒ θ 30°, φ 45°), fill 0.86, `setClearAlpha(0)` so alpha = silhouette
  (04:T1). `view=sheet` = 2×2 contact sheet in ONE 900² PNG: target view, back
  three-quarter, front ortho, top — keeps the single-artifact contract while exposing
  unattached rears. **RULING** on 05:OQ2: `sheet` is the judged view; `target` is the
  IoU-guard view.
- Hard gate before judge: `npm run check` = node --check + node --test + `check-spec.mjs`
  (V0–V9 over every `assets/*/spec.json`) + IoU-vs-BASELINE guard on the target view
  (drop >0.03 = FAIL; guard, not ranker — 04:C). The worker adapter's gate line runs it, so
  a FAIL candidate is a lost attempt and never reaches the judge — same path BlindLoop
  already uses for frozen-file violations.
- Judge: existing `roles/judge.md` + criteria-ordered prompt from 04:T5 (proportion →
  placement → completeness → silhouette → colour), 3 runs re-shuffled, order-dependent
  verdict = tie → BASELINE. Add anyCreature reader traps (canary, binding question) only
  if the flip rate is high (01:T).
- BlindLoop wiring: sibling `config.llmmodeling.json` + `adapters/worker-llmmodeling.mjs`.
  **OWNER**: `BLINDLOOP_CONFIG` env override in orchestrator/preflight/capture (three
  frozen one-liners, 05:OQ1 option a) — needed before M4, not earlier.
- `refs/<t>.{camera,parts,mask}.*` and `limits.json` join the run's frozenFiles.

## 5. Iteration speed

- Node path (compile + V0–V7): target <300 ms at 8k tris (three-mesh-bvh closest-point,
  AABB prefilter). V8 needs WebGL → runs inside the capture page; `check` without a
  browser reports `v8:skipped` in the manifest. **Measure at M0** (03:OQ2 unverified).
- Human modeler loop: `npm run dev` studio watches `assets/*/spec.json` (vite HMR on JSON
  import) → re-render <100 ms; in-page violation overlay (orphans red, thin parts yellow,
  gap vectors drawn) + knob panel for `paint` and top-level dims. Edit-to-pixels in about a
  second is the modeler-speed deliverable; LLM calls are optional accelerants.
- Round wall-clock target: 3 candidates in parallel worktrees, node_modules junctioned
  (05:§A), one Chromium with GPU flags (`--use-angle`, 03:D) → <90 s including two Opus
  calls per candidate. **Measure at M4.**
- Cache layers: prompt→spec, spec→compiled parts (sha), capture PNG keyed by (spec sha,
  view, seed, size).

## 6. Layout (copy from CharacterStudioV2, never import across roots — 05:dead)

```
tools/LLMModeling/
  package.json (type:module, three ^0.185.1, vite ^8.1.5, three-mesh-bvh, manifold-3d [flag])
  vite.config.js (base "./", port 4210, strictPort)        <- CS2 vite.config.js:2-9
  index.html, src/studio.js (capture mode)                  <- CS2 studio.js:6-12,70-130,388-416
  src/geom.js (verbatim fork), src/material.js               <- CS2 geom.js:45-559
      (paint 116-178, characterMaterial 181-189, bevelBox 201, stepStack 268, plate 281,
       ring 330, triangleCount 550)
  src/compile.js   spec -> parts[] (attach solver, repeat/mirror), src/grammar.js (facades)
  src/prims/*.js   composite prims (railing, stairFlight, landing, vent, awning, pipe)
  src/validate/{v0..v9}.js, limits.json, report.js
  src/exporters.js (GLB only; FBX out of scope, 05:§2)        <- CS2 exporters.js:22-77
  spec/SCHEMA.md, spec/examples/{crate,bench,tenement-massing}.json
  prompts/{lister,builder,repair}.md
  scripts/{solve-camera,measure-parts,gen,check-spec}.mjs
  refs/tenement-iso.png (+ .camera.json, .parts.json, .mask.png)
  assets/tenement/spec.json
  test/*.test.js  (determinism x3, tri budget, one mesh/one material, 20 broken fixtures -> expected V-codes)
tools/BlindLoop/config.llmmodeling.json, tools/BlindLoop/adapters/worker-llmmodeling.mjs
```
TownhouseStudio: **RULING** copy its palette hexes + part inventory into `refs/` notes, then
delete the folder (untracked, fails every invariant — 05:§C). **OWNER** confirms delete.

## 7. Milestones (one session each; done = live capture evidence + Play/dev stopped)

- **M0 Skeleton renders.** Scaffold, geom fork, compile.js for box/plate/bevelBox +
  attach{flush, rests-on-top} + repeat, studio capture mode, GLB export. Hand-written
  `tenement-massing.json` (3 masses, parapets, stoop). Accept: 3 byte-identical captures
  at `view=target`; manifest triangles < 8k; compile + V0–V2 timings logged.
- **M1 Validators bite.** V0–V7 + limits.json + 20 broken fixtures (each fails exactly its
  V-code; massing passes); in-page overlay. Accept: `npm run check` red on every fixture,
  green on massing; auto-repair closes a 3 cm gap and grows a 1 cm rail; union cross-check
  measured on fixtures (promote or keep flagged).
- **M2 Full tenement by hand.** Facade grammar + composite prims (railing, stairFlight,
  landing, awning, vent, pipe, trashcan, crates) → hand-authored full spec passes V0–V8,
  < 8k tris, `view=sheet` capture. Owner taste gate on the still (stop, hand off).
- **M3 LLM authors it.** lister → measure (spike or clicked boxes) → builder × 3 tiers →
  repair; from TARGET.png to PASS with zero human spec edits. Accept: ≤2 repairs/tier,
  tokens + seconds logged, spec cached, second run byte-identical from cache.
- **M4 Blind Loop pass.** Sibling config, worker adapter, BLINDLOOP_CONFIG (owner-gated),
  preflight green, one full pass over the tenement item list. Accept: ledger shows ≥1
  non-BASELINE win with validator PASS; round wall-clock recorded.
- **M5 Generality.** One vehicle or robot subject (V9 live), no compiler changes beyond new
  composite prims. Accept: same M3 criteria.

## 8. Risks + owner gates

- Grounded SAM on flat cartoon art unverified (04:OQ3) → ≤20 min spike at M3, fallback clicked boxes.
- TARGET may carry perspective → verticals test before the M0 camera freeze (04:OQ1).
- Union-as-proof unverified (03:OQ1) → flagged cross-check until fixtures prove it.
- Headless capture latency unverified (03:OQ2) → M0 measurement.
- Non-axis parts (stairs, angled pipes) limited to one rotation axis — may pinch vehicles; revisit at M5.
- **OWNER list:** MIN_FEATURE px + style floors; tri budgets per class; V7 table; IoU guard
  0.03; judgeRuns; port 4210; three frozen-file one-liners for BLINDLOOP_CONFIG;
  TownhouseStudio delete; sheet as judged view; FBX out of scope; Blender never in loop.
