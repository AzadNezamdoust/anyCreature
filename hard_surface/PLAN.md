# LLMModeling — merged plan (Fable final, 2026-09-10)

Merge of `research/06-arch-opus.md` + `07-arch-fable.md` after exchange `08-opus-revision.md`.
Evidence: `research/01..05`. **OWNER** = owner-ratified, never self-ratified. **RULING** = Fable
call on a contested point, with the reason. Implementer-ready; each milestone is one session.

## 0. Shape

The LLM never writes geometry or a world coordinate. It emits an **attachment program**
(`spec.json`, schema `pg/1`): primitives in metres, every non-root part attached to a parent
*face* at *(u,v)* with a *contact mode*; facades are CGA-lite splits; repetition/symmetry are
macros. A deterministic JS compiler resolves transforms, builds one merged flat-shaded
vertex-coloured mesh (fork of `CharacterStudioV2/src/geom.js`), and runs numeric validators
V0–V7 + V10 in Node before any pixel exists. V8 (screen-space visibility) runs in the capture
page. Only PASSing candidates reach the BlindLoop judge. Generation is tiered (massing →
facades → props), each tier validated and repaired (≤2 re-prompts) before the next. Determinism
lives in the spec cache and compiler seed, never in the model call (03:D). Blender never in the
loop (03:D). Why this route: ranked #1 of ten on correctness/style/speed/determinism (03:ranked);
the only one where all four owner failure modes are impossible by construction, not by critique.

## 1. Data contracts

### 1.1 `subjects/<name>/spec.json` (LLM-authored; metres, y-up)
```jsonc
{ "schema":"pg/1", "subject":"tenement_block", "seed":1, "class":"building",
  "unit":{"part":"door_l","m":2.0},
  "palette":{"mint":"#9fd3b8","brick":"#c9573f","tan":"#c9b391","iron":"#3b3f4a","stone":"#b9b3a8"},
  "parts":[
    {"id":"mass_l","prim":"box","dims":[6.0,9.6,8.0],"ground":true,"role":"massing","zone":"mint"},
    {"id":"mass_m","prim":"box","dims":[5.2,10.4,8.0],"role":"massing","zone":"brick",
     "attach":{"to":"mass_l","face":"+X","uv":[0.5,0.0],"contact":"flush","align":"bottom"}},
    {"id":"mass_r","prim":"box","dims":[5.6,9.6,8.0],"role":"massing","zone":"tan",
     "attach":{"to":"mass_m","face":"+X","uv":[0.5,0.0],"contact":"flush","align":"bottom"}},
    {"id":"parapet_l","prim":"plate","dims":[6.2,0.3,8.2],"role":"parapet","zone":"stone",
     "attach":{"to":"mass_l","face":"+Y","uv":[0.5,0.5],"contact":"rests-on-top"}},
    {"id":"door_l","prim":"box","dims":[1.0,2.0,0.1],"role":"door","zone":"iron",
     "attach":{"to":"mass_l","face":"+Z","uv":[0.7,0.0],"contact":"socket","embed":0.08,"align":"bottom"}},
    {"id":"balcony_r","prim":"bevelBox","dims":[2.4,0.14,1.0],"role":"balcony","zone":"iron",
     "attach":{"to":"mass_r","face":"+Z","uv":[0.5,0.60],"contact":"flush","embed":0.05},
     "repeat":{"axis":"+Y","count":2,"pitch":3.2}},
    {"id":"rail_r","prim":"railing","dims":[2.4,0.95,0.05],"role":"railing","zone":"iron",
     "attach":{"to":"balcony_r","face":"+Y","uv":[0.5,0.97],"contact":"rests-on-top"}}
  ],
  "facades":[
    {"id":"fac_m_front","on":"mass_m","face":"+Z","occlude":true,
     "split":{"axis":"Y","rule":[["base",3.4],["floor",3.2,"*2"],["cornice",0.6]]},
     "tile":{"floor":{"axis":"X","rule":[["pier",0.4],["bay",1.4,"*3"],["pier",0.4]]}},
     "elements":{"bay":{"window":{"dims":[0.9,1.4],"inset":0.12,"zone":"glass"}},
                 "base":{"storefront":{"awning":[4.0,0.25,1.2],"zone":"awning"}}}}
  ]
}
```
Rules: every `attach.to` names an **earlier** part (DAG). Exactly the `ground:true` parts have
no `attach`. `zone` indexes `palette`; per-facet `paint()` keeps one material (05:§2). No
`budgetTris` in the spec — budgets live in `limits.json` (08:D5). `prim` is a closed
vocabulary: box, bevelBox, taperBox, prism, wedge, plate, stepStack, ring, tube, lathe,
extrudeProfile(+holes) from `geom.js`, plus **composite prims** (railing, stairFlight,
landing, vent, awning, pipe, trashcan, crate) = spec fragments in `src/parts/lib/`,
authored once, versioned, library-learned (03:T5). `rot` = one angle about the attach
normal only in v0 (08:A7); composites own their internal inclines (stairs).
`contact` ∈ {rests-on-top, flush, socket, embedded, hangs-below}; `embed` (m) = intended
penetration for flush/socket so union connectivity is guaranteed.

### 1.2 Attach solver (08:G4) — `src/compile/resolve.js`
Parent local box frame, half-extents (hx,hy,hz). Face frames (origin on face centre; u,v
tangent; n outward):

| face | n | u | v |
|---|---|---|---|
| +X | +X | +Z | +Y |
| −X | −X | −Z | +Y |
| +Y | +Y | +X | +Z |
| −Y | −Y | +X | −Z |
| +Z | +Z | −X | +Y |
| −Z | −Z | +X | +Y |

Order of operations per child: (1) build child geometry at origin, dims = `dims`;
(2) `rot` about n; (3) pick child contact face = the child face whose outward normal is −n
(`hangs-below`: +n; `embedded`: child centre); (4) `align` picks which child extreme along v
is anchored: `bottom` → child −v extreme at parent point, `top` → +v extreme, `center` (default)
→ child centre; along u always centre; (5) parent point = origin + (uv.u−0.5)·2·U·u +
(uv.v−0.5)·2·V·v where U,V are the face half-extents; (6) translate child so its anchored
point sits there, then shift along −n by `embed` (flush/socket/rests) so surfaces overlap by
`embed`; (7) multiply by parent world matrix. `repeat.axis` is parent-local; the compiler
writes resolved **world** directions into `solved.json` (08:G5). Compile order (08:G6):
resolve attach → expand repeat/mirror → build contact table → run facade grammar with
occlusion on the *expanded* contact set → merge → paint.

### 1.3 `solved.json` / `report.json`
`solved.json = {parts:[{id, prim, dims, matrix, zone, parentId, contact, genus, triCount,
aabb, worldRepeatAxis, provenance:{repairs:[]}}], contacts:[[a,b,dist]], bounds, triangles}`.
`report.json = {pass, violations:[{v, part, measured, limit, hint}]}` + ≤8-line text whose
hints state the **move in metres** (01:T). This text is the only thing REPAIR sees.

## 2. Validators (run order; first failing blocking class stops)

Constants in `src/validate/limits.json` (**OWNER**, frozen per run): `EPS = max(0.01,
0.005·bboxDiag)`; `PX = orthoHeight/900`; `MIN_FEAT = max(styleFloor[class], 3·PX)`;
styleFloor prop 0.04 / trim 0.06 (proposed); tri budget prop 2000 / building 8000 / vehicle
4000 (proposed); V7 role table; V8 6 px.

| V | Check | FAIL | Auto-repair | Re-prompt | Where |
|---|---|---|---|---|---|
| V0 | schema; DAG; ground rule; dims within class priors; repeat fits parent face | any | — | yes | node |
| V1 | per-prim watertight + winding; χ = 2−2·genus with **per-prim declared genus** (ring/tube/lathe = 1) (08:E4) | any | abort round: compiler bug | — | node |
| V2 | declared contact real: SDF samples of child contact face vs parent; flush/rests |d|≤EPS on ≥90 %; socket pen ∈[0.5,1.5]·embed; embedded ∩≥50 % | gap>EPS | gap ≤ max(5·EPS, 10 % child extent): translate along −n | larger | node |
| V3 | contact graph connected; every part rooted to ground; manifold-3d union comp==1 as **flagged cross-check** until M1 fixtures promote it | orphan | never (logic error must reach ledger) | yes, orphan + nearest parent | node |
| V4 | ground min-y = 0 ± EPS; COM inside ground-footprint hull | any | — | yes | node |
| V5 | min OBB extent ≥ MIN_FEAT; non-box p5 thickness ≥ MIN_FEAT; repeat gap < 2·PX = sub-pixel | any | grow thin axis keeping attached face; collapse sub-pixel repeat to block + stripe zone | if repair breaks V6/V7 | node |
| V6 | pairwise ∩ ÷ smaller: >0.9 duplicate; 0.2–0.9 without socket/embedded = clash | clash | delete ≥0.9 duplicate (log) | clash | node |
| V7 | role-keyed scale table (door 2.0–2.4; step rise .14–.20; rail .9–1.1 above floor; window < floorH; awning ≥ door top; parapet .3–1.2) | any | never | yes, rule + measured | node |
| V10 | one mesh, one material, no texture, no NaN/Inf, tri ≤ budget[class] | any | — | budget → yes | node |
| V8 | id-buffer at frozen camera: part < 6 px hidden → drop from export (advisory, recorded in manifest) | — | drop from export | — | capture page |
| V9 | symmetry when role implies and `mirror` absent (vehicle/robot): mirrored-union chamfer ≤ 2·EPS | advise | — | — | node |

Every auto-repair re-runs the chain; a repair that creates a new violation is reverted and the
original re-prompted. Retry cap 2 per tier. Zero LLM tokens in V0–V10. V8 never gates a round
(08:G7).

## 3. LLM seats

| Seat | Model | Runs | Sees | Emits |
|---|---|---|---|---|
| LISTER | Fable 5.1 (vision) | once per TARGET, frozen | TARGET + measured boxes | `refs/<t>.parts.json` inventory (prompt 04:T6) |
| MEASURE | script | once per TARGET | parts names | Grounding DINO + SAM boxes → metres via door anchor; **spike ≤20 min; fallback operator-clicked boxes** |
| BUILDER-A/B/C | Opus 5 | 1 per tier | DSL doc + 2 valid examples + plan + previous tier's `solved.json` **summary** (08:D4) | spec fragment ≤6k tokens |
| REPAIR | Opus 5 | ≤2 per tier | report text only | spec delta ≤1k |
| JUDGE | Fable 5.1 via BlindLoop adapter | `judgeRuns` per round | TARGET + anonymised PNGs | frozen contract `PICK:` / `WORSE:` (08:G1) |

Budget ≤25k tokens/object (img2threejs own estimate 80k–180k, 01:B). Cache key
`sha256(promptTemplate + inputsHash + dslVersion + tier)` → `cache/specs/`; hit = zero calls.
Worked examples in `dsl/examples/` must each pass V0–V7 in `npm run check` (08:E1 — a broken
example teaches an invalid program).

## 4. BlindLoop integration (web lane; harness frozen files untouched)

- Sibling `tools/BlindLoop/config.llmmodeling.json`: `project.root ../LLMModeling`, port 4210
  for human dev only (candidates are captured serially on 4201–4203 by the orchestrator,
  08:G2), URL `?capture=1&subject={subject}&view={view}&seed={seed}&size={size}`, **its own
  path plus `refs/<t>.*` and `limits.json` in its `frozenFiles`** (08:G9). One run = one
  subject, one view.
- Capture contract verbatim from `studio.js:388-416`: `setPixelRatio(1)`, square, one render,
  `__CAPTURE_MANIFEST__ = {triangles, materials, drawCalls, boundsM, subject, view, seed, size,
  specHash, dslVersion, validatorPass, violationCount, repairCount, v8Dropped, cameraId}`, then
  `__CAPTURE_READY__`. Unknown subject/view warns + defaults. Overlay hard-off under `?capture=1`
  (08:G8). Specs loaded by `fetch()` in dev with `import.meta.hot` handler; inlined at build so
  `preview` has no network dependency.
- **Judged view = single frozen target view** (RULING, 08:D1: a 2×2 sheet halves resolution and
  doubles MIN_FEAT; three quadrants have no TARGET counterpart). Orthographic camera from
  `refs/<t>.camera.json`, θ/φ **measured** from two ground-edge slopes (04:D), never assumed
  (08:E8); fill 0.86; `setClearAlpha(0)`. `npm run qa` writes a 3-view sheet to `out/qa/` for
  humans only.
- **Gate mechanism (08:G3):** forked `adapters/worker-llmmodeling.mjs` runs
  `npm --prefix tools/LLMModeling run check` after the worker; on FAIL it reverts the worktree
  (`git checkout -- . && git clean -fd`) so the orchestrator logs `no change produced - lost`.
  This is the only gate that works without a frozen-file edit.
- **IoU regression guard: deferred** (RULING on 08:D2). It cannot live in `check` (no BASELINE
  PNG in the worktree, and it would hand the worker a target proxy) and the orchestrator is
  frozen. Bundle it with the owner-gated orchestrator change below; until then the gate is
  validators + judge only.
- Judge de-biasing: shuffle re-randomised per run, majority; order-dependent verdict = tie →
  BASELINE. Criteria order (proportion → placement → completeness → silhouette → colour) enters
  through the **item brief**, not the frozen role prompt.
- **OWNER (pre-M4):** `BLINDLOOP_CONFIG` env override in `orchestrator.mjs:20`,
  `preflight.mjs:17`, `capture.mjs` (three frozen one-liners); optional IoU guard in the same
  change; commit-or-delete `tools/TownhouseStudio/` (untracked, preflight needs a clean tree).

## 5. Iteration speed

- Node compile + V0–V7 + V10 target ≤300 ms at 8k tris (three-mesh-bvh, AABB prefilter);
  **measure at M0**. Capture ≤1.5 s on a warm page.
- Human loop = deliverable (brief priority 3): edit `spec.json` → re-render ≤1 s; in-page
  overlay (orphans red, thin yellow, gap vectors, violation list); knob panel for palette +
  top-level dims.
- Round wall-clock is **serial** (08:G2): 3 × (worker + dev-server start + capture). Budget
  after M0 measurement; do not promise <90 s.
- Caches: prompt→spec, part-subtree→geometry (`sha256(subtree+palette+seed+dslVersion)`),
  union keyed by contact-graph hash, capture PNG by (specHash, view, seed, size). All under
  `cache/` (gitignored); a cold run must reproduce byte-identically.

## 6. Layout + copy list

```
tools/LLMModeling/
  package.json   dev|build|preview|check|gate|qa; --port --strictPort passthrough; three ^0.185.1, vite ^8.1.5,
                 three-mesh-bvh, manifold-3d (flag)                     <- CS2 package.json:8-12
  vite.config.js base "./", port 4210, strictPort                        <- CS2 vite.config.js:2-9
  index.html, src/app.js (studio + capture + overlay)                    <- CS2 studio.js:6-12,70-130,388-416
  src/geom.js (verbatim fork), src/material.js                           <- CS2 geom.js:45 hash32, :56 rng, :78-107 facet pairing,
                 :116 paint, :181 material, :201 bevelBox, :228 taperBox, :252 prism, :268 stepStack, :281 plate,
                 :300 wedge, :330 ring, :350 wall, :372 fan, :460 loft, :502 mergeGeometries, :527 mirrorX, :551 triangleCount
  src/compile/{resolve,expand,contacts,grammar,build}.js   src/parts/lib/*.json (composites, versioned)
  src/validate/{v0..v10}.js, limits.json, report.js, repair.js
  src/exporters.js (GLB, COLOR_0)                                        <- CS2 exporters.js:22,35-49,69-77,97-131
  dsl/SPEC.md, dsl/schema.json, dsl/examples/{crate,bench,tenement-massing}.json
  prompts/{lister,builder-a,builder-b,builder-c,repair}.md
  scripts/{solve-camera,intake,gen,check-spec,qa-sheet}.mjs
  refs/tenement-iso.png (+ .camera.json .parts.json .mask.png .palette.json)
  subjects/tenement_block/{spec,solved,report}.json
  test/{determinism,budget,fixtures}.test.js  (20 broken fixtures -> exact V-codes)
tools/BlindLoop/config.llmmodeling.json, tools/BlindLoop/adapters/worker-llmmodeling.mjs
```
Never import across project roots; never edit `tools/CharacterStudioV2` (live loop target).
TownhouseStudio: take palette hexes + part inventory into `refs/`, port no code.

**Export consumer (08:G10):** Unity has `com.unity.formats.fbx` and **no glTF importer**. RULING:
export AC = "GLB opens in a glTF viewer with COLOR_0 intact" until the owner adds a Unity glTF
package (package-tree change = validation zone). Unity ingest + vertex-colour URP shader is a
separate owner-gated slice.

## 7. Milestones (one session each; done = capture evidence + dev server stopped)

- **M0 Loopable shell + massing.** Scaffold, geom fork, `resolve.js` for box/plate/bevelBox +
  flush/rests-on-top/socket + repeat, capture mode, GLB export, sibling config + adapter
  files written (not yet run). Hand-written `tenement-massing.json` (3 masses, parapets,
  stoop, door). Accept: 3 byte-identical captures at `view=target`; camera θ/φ measured from
  the frozen PNG and verticals-are-vertical confirmed; compile timing logged; worked examples
  pass V0.
- **M1 Validators bite.** V0–V7 + V10, `limits.json`, `report.js`, auto-repair, 20 broken
  fixtures each failing exactly its V-code; massing passes; in-page overlay. Accept: `check`
  red on every fixture, green on massing; 3 cm gap auto-closed, 1 cm rail auto-grown; union
  cross-check measured on fixtures → promote or keep flagged.
- **M2 Full tenement by hand.** Facade grammar with occlusion, composite prims (railing,
  stairFlight, landing, awning, vent, pipe, trashcan, crate, clothesline as tube), V8 in
  capture page, `qa` sheet. Accept: full hand spec passes; ≤8000 tris; one mesh/material.
  **Owner taste gate** on the still — stop, hand off.
- **M3 LLM authors it.** intake (SAM spike or clicked boxes) → LISTER → BUILDER A/B/C → REPAIR
  with cache. Accept: from `refs/tenement-iso.png` alone to PASS, ≤2 repairs/tier, ≤25k tokens,
  zero hand edits; cache re-run makes zero calls and reproduces the PNG byte-identically.
- **M4 First BlindLoop pass.** Owner applies `BLINDLOOP_CONFIG` change + TownhouseStudio
  decision; preflight green; items from the TARGET inventory; BASELINE = M3 output. Accept: one
  full pass inside `maxWallClockMinutes`; every gate FAIL logged as a loss without reaching the
  judge; ≥1 non-BASELINE win; serial round time recorded.
- **M5 Generality.** One vehicle or robot subject, V9 live, only new composites. Accept: M3
  criteria repeat.

## 8. Owner decisions (stop points)

1. `limits.json` numbers: MIN_FEAT px (2 vs 3), style floors, tri budgets per class, V7 table,
   V8 6 px, fill 0.86, EPS.
2. Three frozen one-liners for `BLINDLOOP_CONFIG` (+ optional IoU guard) before M4.
3. `tools/TownhouseStudio/`: commit as provenance or delete.
4. Unity glTF importer package vs FBX route (M2/M3 boundary).
5. Judge model + `judgeRuns` sufficiency after first pass flip-rate.
6. Save the reference image to `refs/tenement-iso.png` (could not be written from chat).
