# 06 — Architecture proposal: `tools/LLMModeling` (Opus seat, independent)

Citations `[Rnn:LL]` = `research/nn-*.md` line LL; repo citations are `file:line`.

**Route:** LLM emits a *relational part-graph DSL*; a JS compiler resolves every transform; ten
headless validators gate before any pixel exists; three.js renders that same compiler output
under BlindLoop's web lane. Ranked #1 of ten routes on correctness+style+speed [R03:189-217] and
the only one where all four owner failure modes are structurally impossible rather than
statistically unlikely [R03:206-212]. **JS-first, one runtime** for compile+validate+capture
[R02:223-225]: the web lane already drives a vite app through Playwright [R05:9-13],
`manifold-3d` ships WASM [R02:78], and a second (Python) runtime would double the determinism
surface for one library's convenience. `trimesh` stays an *offline* M0 cross-check only.

## 1. Pipeline stages and data contracts

| S | Stage | Runtime | In → Out | Frozen? |
|---|---|---|---|---|
| S0 | Target intake | node, once per TARGET | `refs/x.png` → `x.camera.json`, `x.parts.json`, `x.mask.png`, `x.palette.json` | yes, with the TARGET |
| S1 | Plan | VLM (LISTER) | TARGET + S0 measurements → part inventory JSON | yes |
| S2 | Build | LLM (BUILDER), 3 tiers | plan + DSL spec → `subjects/<n>/spec.json` | no |
| S3 | Compile | JS | `spec.json` → `solved.json` + `THREE.BufferGeometry` | — |
| S4 | Validate | JS | `solved.json` → `report.json` (+ auto-repairs) | — |
| S5 | Capture | vite app + Playwright | URL → `candidate.png` + `__CAPTURE_MANIFEST__` | — |
| S6 | Export | JS | `solved.json` → `.glb`, `createAsset()` `.mjs` | — |
| S7 | Judge | BlindLoop | PNG vs TARGET → ledger | — |

**Invariant: the LLM never writes a world coordinate.** `dims` in metres and relations only;
the compiler owns transforms [R02:8-11, R03:150-152, R04:59-63].

### DSL sketch (`spec.json`, schema id `pg/1`)

```jsonc
{ "schema":"pg/1", "subject":"tenement_block", "seed":1, "unit":"m",
  "palette": { "mint":"#9fd8bf", "brick":"#b4553f", "iron":"#3a3f46" },
  "parts": [
    { "id":"mass_left", "prim":"box", "dims":[6.0,9.0,8.0], "ground":true, "zone":"mint" },
    { "id":"parapet_left", "prim":"plate", "dims":[6.2,0.6,8.2], "zone":"mint_dark",
      "attach":{ "to":"mass_left","face":"+Y","uv":[0.5,0.5],"contact":"rests-on-top" } },
    { "id":"balcony", "prim":"bevelBox", "dims":[1.6,0.12,0.9], "zone":"iron", "role":"balcony",
      "attach":{ "to":"mass_right","face":"+Z","uv":[0.25,0.55],"contact":"flush","embed":0.06 },
      "repeat":{ "axis":"+Y","count":2,"pitch":3.0 }, "mirror":null } ],
  "facades": [
    { "id":"fac_left_front", "on":"mass_left", "face":"+Z", "occlude":true,
      "split":{ "axis":"Y","rule":[["base",1.2],["floor",3.0,"*3"],["cornice",0.4]] },
      "tile":{ "floor":{ "axis":"X","rule":[["pier",0.5],["bay",1.5,"*3"],["pier",0.5]] } },
      "elements":{ "bay":{ "window":{ "dims":[0.9,1.4],"inset":0.12,"zone":"glass" } } } } ] }
```

- `contact` ∈ `rests-on-top | flush | socket | embedded | hangs-below` — extends the repo's
  existing vocabulary at `CharacterStudioV2/blockout-spec.json:31-45` [R02:131, R05:169-175].
- `face`+`uv` is ShapeAssembly's `attach`; `repeat`/`mirror` are its `translate`/`reflect`
  [R02:20-27]. `attach.to` must name an **earlier** part (DAG, no cycles).
- `facades` are CGA splits, so window count/spacing/alignment cannot be wrong [R02:133-137,
  R03:117-120]. `occlude:true` turns a tile that `touches` another part into wall [R02:136].
- **Paint zones, not per-part hex:** `zone` indexes `palette`; the compiler calls the forked
  `paint()` per facet with its AO ramp (`CharacterStudioV2/src/geom.js:116`), so one material /
  one draw call survives [R05:159-163].
- Rotated parts (stair flight, angled pipe) carry `rot:[rx,ry,rz]` applied **after** attachment
  resolution; `face`/`uv` evaluate in the *parent's* frame — spec'd, not inferred [R02:233-235].

`solved.json` (compiler output, the validators' only input): `{ parts:[{id, prim, dims, matrix,
zone, parentId, contact, triCount, aabb, provenance:{specPath, repairs:[]}}], contacts:[[a,b,d]],
bounds, triangles }`. `report.json`: `{ pass, violations:[{v, part, measured, limit, hint}] }` +
a ≤8-line text rendering fed verbatim to the repair prompt [R02:176-177].

## 2. Validators — run order, rule, repair policy

Constants (owner-gated, §8): `EPS = max(0.01 m, 0.005·bboxDiag)`; `PX` = ortho height/900; `MIN_FEAT = max(styleFloor, 3·PX)`.

| # | Check | PASS rule | On FAIL |
|---|---|---|---|
| V0 | Program | schema valid; `attach.to` earlier + acyclic; ≥1 `ground`; `repeat.count·pitch` fits parent face | re-prompt (no geometry exists) |
| V1 | Per-part manifold | each primitive watertight + consistently wound | abort: compiler bug, not the LLM's |
| V2 | Declared contact real | `flush`/`rests-on-top`: \|d\| ≤ EPS on ≥90% of face samples; `socket`: penetration ∈ [0.5,1.5]·`embed`; `embedded`: ∩ ≥50% of child vol [R02:148-152] | **auto**: gap ≤ 5·EPS or ≤10% child extent → translate along face normal. Else re-prompt with the metres [R02:183-185] |
| V3 | Connectivity + rootedness | contact graph connected; every part has a path to a `ground` part; cross-check `manifold3d` union `split()` == 1 component [R02:153-156] | **never auto** — floating is a logic error; re-prompt naming orphan + nearest candidate parent [R02:190, R02:216-218] |
| V4 | Ground + stability | ground parts min y == 0 ±EPS; union CoM projects inside ground-footprint hull | re-prompt |
| V5 | Minimum feature | min OBB extent ≥ MIN_FEAT; non-box prims 5th-pct thickness ≥ MIN_FEAT; any `repeat` with `pitch − width < 2·PX` is sub-pixel [R02:159-162] | **auto**: grow the thin axis, keep the attached face fixed; sub-pixel repeat → collapse to one block + stripe zone [R02:187-188] |
| V6 | Overlap / containment | pairwise ∩ ÷ smaller vol: >0.9 = duplicate; 0.2–0.9 without `socket`/`embedded` = accidental interpenetration [R02:163-166] | **auto** delete the ≥0.9 contained part (log); else re-prompt |
| V7 | Relative-scale logic | role-keyed table: door h ∈[2.0,2.4]; window h < floorH; step rise ∈[0.14,0.2]; railing top ∈[0.9,1.1] above its floor; awning bottom ≥ door top; parapet ∈[0.3,1.2] [R02:167-170] | **never auto** (numbers are owner-ratified) — re-prompt quoting rule + measured value |
| V8 | Visibility at capture | offscreen id-buffer at 900²: a part < 6 px is hidden (drop from export, keep in program) or must grow [R02:171-174] | auto-drop from export only |
| V9 | Symmetry (opt) | when `role` implies symmetry and `mirror` absent: 1k-sample chamfer of mirrored union ≤ 2·EPS | advise only |
| V10 | Export hygiene | one mesh, one material, no texture, no NaN/Inf, tri budget — port `test/character.test.js:23-28, :78-84, :104-113` [R05:164-166] | build fails `npm run check` |

Every auto-repair re-runs V0–V10; one that creates a new violation is reverted and the original
re-prompted [R02:191-193]. Zero LLM tokens are spent on V0–V10; repairs are logged to
`provenance.repairs`. Each check is tagged **block|advise** and its message states the **move in
metres**, not the gap (anyCreature) [R01:29-35,:191-194].

## 3. LLM seat design

| Seat | Model | Runs | Sees | Emits | Budget |
|---|---|---|---|---|---|
| LISTER | Fable 5.1 (vision) | **once per TARGET**, output frozen with it | TARGET + S0 measured boxes | part inventory + `unit_ref` [R04:202-217] | ≤4k out |
| BUILDER-A massing | Opus 5 | 1/subject | plan + DSL spec + palette | 3–8 mass parts | ≤3k out |
| BUILDER-B facades | Opus 5 | 1/subject | A's `solved.json` summary | `facades[]` | ≤4k out |
| BUILDER-C props | Opus 5 | 1/subject | A+B summary | attached props | ≤6k out |
| REPAIR | Opus 5 | ≤2 per tier | **only** `report.json` text | a spec *delta* | ≤1k out |
| JUDGE | Fable 5.1 | `judgeRuns` per round | anonymised PNGs + TARGET | `PICK:`/`WHY:` [R04:189-199] | — |

- **Tiered, not one shot:** V0–V3 after each tier beats whole-program emission above ~15 parts
  [R02:200-202]; free-form assembly is where models collapse (`PartMatchF1 ≈ 0.50`)
  [R03:34,:153-156].
- **Never a VLM structural critic** — V3 answers "is anything floating" exactly, while VLM QA
  accuracy is 64–68% and blind to thin defects [R02:195-198,:212-214, R03:243-245].
- **Ship the whole DSL spec in-context** (~200 lines): the LL3M RAG effect (5.86× ops, −26%
  errors) applies and is cheap for a small DSL [R03:170-172].
- **≤ 25k tokens/object** vs img2threejs's own 80k–180k estimate [R01:117-119]; ≤2 repair rounds
  per tier [R04:220-221]; hard cap 3 attempts per BlindLoop round, then BASELINE stands [R02:194].
- **Determinism lives in our code, never in the model call** — temperature 0 gave 80 distinct
  outputs from 1,000 samples [R03:138-143]. Cache key `sha256(promptTemplate + planHash +
  dslVersion + tier)` → `out/cache/specs/<key>.json`; a hit makes **zero** model calls. `seed`
  feeds only the compiler's `rng()` (`geom.js:56`), hashed per part as `rng("${seed}:${partId}")`
  [R05:110-113].

## 4. Capture + judge integration with BlindLoop

- **Own config, never edit the frozen one:** `tools/BlindLoop/config.llmmodeling.json`,
  `project.root: "../LLMModeling"`, port **4210** [R05:246]. `capture.mjs:175` accepts
  `--config`; `orchestrator.mjs:20` does not — see §8.
- **URL:** `http://127.0.0.1:4210/?capture=1&subject={subject}&view={view}&seed={seed}&size={size}`.
  An unknown `subject`/`view` warns and falls back to defaults, never silently substitutes
  (`studio.js:105-108`) [R05:53-56].
- **Capture contract, verbatim** from `studio.js:388-416`: `setPixelRatio(1)`,
  `setSize(size,size,true)`, `camera.aspect = 1`, one `renderer.render`, then
  `__CAPTURE_MANIFEST__`, then `__CAPTURE_READY__ = true`; nothing in that path reads the clock,
  `devicePixelRatio`, window size or `Math.random()` [R05:41-51].
- **Manifest:** `{ triangles, materials, drawCalls, boundsM, subject, view, seed, size,
  specHash, dslVersion, validatorPass, violationCount, repairCount, cameraId }` — the last five
  are new and make gate state auditable from the sidecar [R05:126-137].
- **Camera solve, closed form, no network.** `scripts/solve-camera.mjs`: operator clicks (or
  Hough finds) the two ground-edge families; θ = asin(√(m_X·m_Z)), φ = atan(√(m_X/m_Z))
  [R04:107-118] → `refs/<t>.camera.json`, read by the app. Framing = `fill` of the AABB;
  `setClearAlpha(0)` so the alpha channel **is** the silhouette mask [R04:120-146]. Verticals
  not vertical in the TARGET ⇒ not orthographic ⇒ stop and re-source [R04:110-112,:250-254].
- **Hard gate before the judge.** A candidate whose `report.json` fails is never shown to the
  judge and is logged as a lost attempt — the mechanism BlindLoop already uses for frozen-file
  violations (`BLIND_LOOP.md:110-113`, `orchestrator.mjs:255-260`) [R04:167-171, R05:189-192].
- **Tier 1 = regression guard, not ranker:** silhouette IoU vs `refs/<t>.mask.png`; fail a
  candidate whose target-view IoU drops >0.03 below BASELINE. IoU moved 68.2→69.9% across
  methods whose topology correctness moved 79.9→87.2% [R04:172-178,:69-76].
- **Judge de-biasing:** re-randomise the shuffle **per** judge run (`judgeRuns: 3`,
  `config.json:29`), majority vote; an order-dependent verdict is a tie and ties go to BASELINE
  [R04:179-185] — position bias is 10–15 points [R04:87-90]. Add anyCreature's reader traps
  (canary image, binding question); a tripped trap voids the read [R01:200-202]. DreamSim only
  if Tier 2 proves noisy [R04:186-188].
- **Side views never reach the judge** — the TARGET exists in one view, so views 2–4 test
  self-consistency only [R04:97-100]. `npm run qa` writes a 3-view sheet to `out/qa/` for V8 and
  back-face checks; the judged PNG stays the single frozen view, so the harness is untouched
  [R05:268-273].

## 5. Iteration speed

Targets on the owner's Win 11 box, warm: **compile+validate ≤ 300 ms** at 8k tris,
**capture ≤ 1.5 s** on a reused page, **full candidate round ≤ 5 s with a spec-cache hit**,
≤ 60 s including three LLM tiers. Compare: LL3M ~4 min + ~6 min refine [R03:37-40].

- **Persistent Chromium, page per candidate,** launched `--use-gl=egl` — headless Chrome defaults
  to the SwiftShader software rasteriser [R03:129-131,:177-179]. **Parallel candidates** =
  BlindLoop worktrees on ports 4211–4213 (`workerCount: 3`, `config.json:24`); `linkNodeModules`
  junctions `node_modules`, so no per-candidate install [R05:33-38].
- **Incremental rebuild** (one-ITEM-per-round maps onto per-part regeneration [R03:174-176]):
  memo key `sha256(partSubtree + palette + seed + dslVersion)` → cached `BufferGeometry`; only
  the edited subtree recompiles. **Cached:** spec text (§3), per-part geometry, the manifold
  union keyed by contact-graph hash, `refs/*.mask.png|.camera.json`, the parts library — all in
  `out/cache/` (gitignored); a cold run must reproduce it byte-identically.
- **No Blender in the loop** — EEVEE cannot render headless on Windows and CLI startup dominates
  short renders [R03:132-137,:222-226]. **Library learning:** every winner promotes its part
  function into `src/parts/lib/` under a version, so stairs are never re-derived [R03:164-166].

## 6. File / folder layout, and what to copy

```
tools/LLMModeling/
  package.json      # dev|build|preview|check|gate|qa; ports pass through --port --strictPort [R05:100]
  vite.config.js    # base:"./", port 4210, strictPort  <- CharacterStudioV2/vite.config.js:1-10
  index.html
  dsl/              # SPEC.md (the in-context DSL doc), schema.json, examples/*.json
  src/  geom.js (FORK — copy, never import [R05:222-227]) · material.js · exporters.js (FORK)
        app.js (studio + capture, shape from studio.js:70,:76,:388-416)
        compile/ resolve.js (attach->matrix) · grammar.js (CGA split/tile/occlude) · build.js
        validate/ v0..v10.js · report.js · repair.js        parts/lib/ (promoted, versioned)
  scripts/          # solve-camera.mjs, intake.mjs (Grounded SAM / operator boxes), qa-sheet.mjs
  prompts/          # lister.md, builder-a|b|c.md, repair.md
  refs/             # TARGET + .camera.json .mask.png .parts.json .palette.json (frozen)
  subjects/<name>/  # spec.json, solved.json, report.json
  test/asset.test.js  # rewrite of test/character.test.js assertions      out/ (gitignored)
tools/BlindLoop/config.llmmodeling.json          # sibling config, NOT an edit of config.json
tools/BlindLoop/adapters/worker-llmmodeling.mjs  # fork of worker-claude.mjs:55 (gate line) [R05:39-44]
```

Copy list, all `tools/CharacterStudioV2/`, as-is unless noted [R05:150-168]: `src/geom.js:45`
`hash32`, `:56` `rng`, `:78-107` facet pairing, `:116` `paint`, `:181` `characterMaterial`
(rename), `:201` `bevelBox` (**highest-value hard-surface primitive**), `:228` `taperBox`,
`:252` `prism`, `:268` `stepStack` (= stoop stairs), `:281` `plate` (= parapet coping/sills),
`:300` `wedge`, `:330` `ring`, `:350` `wall`, `:372` `fan`, `:460` `loft`, `:502`
`mergeGeometries`, `:527` `mirrorX`, `:551` `triangleCount`; `src/exporters.js:22,:35-49,:69-77`
GLB export (glTF only — no FBX exporter exists in this repo [R05:167,:230-233]), `:97-131`
`exportModuleSource`; `src/studio.js:105-108`, `:388-416`; `vite.config.js:2-9`;
`package.json:8-12`; `blockout-spec.json:31-45` attach vocabulary. Pin `three ^0.185.1`,
`vite ^8.1.5`, `"type":"module"` [R05:239-243]. **Do not port `tools/TownhouseStudio/src/`** —
magic literals, 415 meshes, ~40 materials, 9,020 tris, no seed, no capture mode [R05:203-215];
take only its part inventory and palette.

## 7. Milestones (one session each)

- **M0 — Loopable shell.** package/vite/app/capture mode, `config.llmmodeling.json`, forked
  worker adapter, one hand-written `spec.json` = three boxes. **AC:** `npm run check` and
  `npm run build` green; three captures of one URL byte-identical [R05:120-121]; `preflight.mjs`
  passes on a clean tree (TownhouseStudio resolved first, §8).
- **M1 — Compiler + V0–V4, hand-authored massing.** Three masses + parapets + roof boxes for
  the tenement block, no facades. **AC:** `report.json.pass == true` with zero auto-repairs;
  `manifold3d` union = 1 component; GLB exports and opens; tri count recorded in the manifest.
- **M2 — Facade grammar, paint zones, V5–V10.** CGA split/tile/occlude; windows derived. **AC:**
  window rows aligned by construction; no sub-pixel repeat survives V5; ≤ building tri budget;
  one mesh / one material asserted by `test/asset.test.js`.
- **M3 — LLM seats end to end.** S0 intake → LISTER → BUILDER A/B/C → REPAIR. **AC:** from
  `refs/tenement-iso.png` alone, a spec passing all blocking validators within ≤2 repairs per
  tier and ≤25k tokens with **no hand edits**; a cache re-run makes zero model calls and
  reproduces the PNG byte-identically.
- **M4 — First BlindLoop round.** Items from the TARGET inventory, BASELINE = M3 output. **AC:**
  a full round inside `maxWallClockMinutes`; every gate rejection logged as a loss without
  reaching the judge; ledger records `attempt 1: <change> — lost|won`.

## 8. Risks and owner-gated numbers (never self-ratified)

**Blocking decisions (validation zone — stop at the boundary).** (1) `orchestrator.mjs:20`
hardcodes `config.json`, so a second project cannot be looped without editing a **frozen** file
[R05:24-31,:258-265]; recommend a `BLINDLOOP_CONFIG` env var in `orchestrator`+`capture`+
`preflight` as a **pre-run** structural change — owner ruling required, touch nothing otherwise.
(2) `tools/TownhouseStudio/` is untracked and preflight demands a clean tree — commit or delete
[R05:196-200,:279-281]. (3) Whether `refs/*.camera.json|parts.json|mask.png` join `frozenFiles`
— `config.json` is itself frozen, so adding them is an owner action [R04:265-270].
(4) Judge model + `judgeRuns` sufficiency at n=4 candidates [R04:271-272].

**Numbers requiring ratification before the first run** — engineering picks; no literature value
exists for stylised low-poly [R04:255-258]: `MIN_FEAT` px floor (2 vs 3 px @900²) and per-class
world floor (props 0.04 m / trim 0.06 m); tri budgets (props <2k, buildings <8k — CS2 has one
`TRIANGLE_BUDGET = 4000` for all presets, so a per-subject table is new [R05:274-277]);
`EPS_CONTACT`; the V7 role table; IoU guard 0.03; `fill` 0.86; V8's 6-px floor; port 4210.

**Risks.** (a) The TARGET may be perspective, not orthographic — invalidates the closed-form
solve and biases IoU permanently [R04:250-254]; measure before M0 freezes the camera.
(b) Grounded SAM is a photo benchmark and may fail on flat cartoon art — fallback is
operator-clicked boxes, acceptable at once per target [R04:263-266]. (c) Touching-but-not-
overlapping parts may union into a valid-but-disconnected compound; V3 keeps the contact-graph
check *alongside* the boolean, and the 20-case empirical check is M1 work [R03:249-252].
(d) Headless WebGL latency here is unmeasured — M0 must record it before the DSL freezes on a
per-round budget [R03:253-256]. (e) `manifold-3d` needs manifold inputs [R02:78]; V1 guarantees
that, and a V1 failure halts the run rather than being re-prompted. (f) Model non-determinism is
permanent [R03:138-143] — every determinism claim is about the *cache*, never the model.
