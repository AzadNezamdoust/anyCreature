# 05 — Local reuse audit (Opus seat, repo-only, no web)

What `tools/LLMModeling` can take from this repo, what interface it must expose,
and what it must not break. All citations are `file:line` in `D:\Git\checkout`.

---

## Findings

### A. The BlindLoop web lane is generic already — it is not CharacterStudioV2-specific

- There are **two** BlindLoop capture lanes, not one. The **web lane**
  (`tools/BlindLoop/config.json:3-22`, `capture.mjs`) drives a Playwright headless
  Chromium against a vite dev server. The **Unity lane**
  (`tools/BlindLoop/capture-settings.json:7-22`, `RUNBOOK.md:19-27`) drives a PlayMode
  test. LLMModeling belongs on the **web lane**; ignore `capture-settings.json` and
  `orchestrate.ps1` entirely (those are the Unity lane).
- The only project-specific coupling in the web lane is
  `config.json:4-6` (`project.root`, `devServerUrl`, `devServerCmd`) plus the URL
  template at `config.json:9`. Everything else — worktrees, anonymise, judging,
  ledger, gate — is project-agnostic (`orchestrator.mjs:214`, `:233-243`, `:307-330`).
- **`config.json` is frozen** (`BLIND_LOOP.md:106-110`, `config.json:32-42`, enforced by
  `preflight.mjs:128-138` and by the diff guard `orchestrator.mjs:257-260`). It points at
  `../CharacterStudioV2` and hardcodes port 4193. LLMModeling therefore **must not edit
  it** — it needs its **own config file**. `capture.mjs:175` already accepts
  `--config <path>`, so a sibling `tools/BlindLoop/config.llmmodeling.json` is the clean
  move. `orchestrator.mjs:20` does **not** take a config override — it hardcodes
  `path.join(HERE, 'config.json')`. That is the one real blocker (see Open questions).
- `orchestrator.mjs:308` derives the candidate's serve directory as
  `worktree + relative(REPO_ROOT, config.project.root)`, and `linkNodeModules`
  (`orchestrator.mjs:232-243`) junctions the main install into the worktree. So a
  worktree candidate is served from `<worktree>/tools/LLMModeling` with `node_modules`
  symlinked — no `npm install` per candidate.
- `captureWorktree` uses `BLINDLOOP_SERVE_CMD` (default
  `npm run dev -- --host 127.0.0.1 --port {port} --strictPort`,
  `orchestrator.mjs:309-311`), so the project's `dev` script **must accept `--port` and
  `--strictPort` passthrough**. The alternative path `capture-candidate.mjs:15-19` does
  `npm run build` then `npm run preview -- --port N --strictPort` — build-then-preview,
  which fails loudly on a broken module graph. Both require `dev`, `build` and `preview`
  scripts.
- **The worker adapter is hardcoded to CharacterStudioV2**:
  `adapters/worker-claude.mjs:55` tells the worker to run
  `npm --prefix tools/CharacterStudioV2 run check`. A new project needs either a forked
  adapter or that line parameterised. This is *not* a frozen file
  (`config.json:32-42` lists only BLIND_LOOP.md, config.json, capture.mjs,
  orchestrator.mjs, preflight.mjs, roles/*.md), so forking `adapters/worker-llm.mjs` is
  legal mid-run.
- The judge/worker contract is env-var only, fully documented at
  `adapters/README.md:14-40`. No code change needed to swap models.

### B. CharacterStudioV2's capture contract is the exact thing to copy

- Capture is a **mode inside the app**, not a separate entry point:
  `src/studio.js:6-12` (doc comment), `:70` (`URLSearchParams`), `:76`
  (`const CAPTURE = flag("capture")`), `:388-415` (`runCapture()`).
- The contract, verbatim: set `renderer.setPixelRatio(1)` (never `devicePixelRatio`,
  `studio.js:394`), `setSize(size,size,true)`, one `renderer.render`, then
  `window.__CAPTURE_MANIFEST__ = {...}` (`studio.js:404-413`) and
  `window.__CAPTURE_READY__ = true` (`studio.js:415`) plus
  `document.body.dataset.captureReady = "1"` (`studio.js:416`).
- The invariant that makes determinism provable: *nothing in the capture path may read
  the clock, devicePixelRatio, window size or `Math.random()`* (`studio.js:10-12`).
  Seeding is `rng(seed)` from `geom.js:56`, hashed per-part as
  `rng("${seed}:${partId}")` (`character.js:125`).
- Unknown `?preset=` **warns and falls back to knob defaults rather than silently
  picking preset[0]** (`studio.js:105-108`) — precisely so the manifest can never
  describe a different asset than the pixels. Copy this rule.
- `capture.mjs:95-119` asserts `innerWidth`, `innerHeight`, `devicePixelRatio` and the
  presence of the manifest, and **refuses to write the PNG** on any mismatch. The
  manifest is not judged in Phase 1 but is recorded in the sidecar
  (`capture.mjs:138-145`, `BLIND_LOOP.md:~200` Phase 1 note).
- `vite.config.js:2-9` uses `base: "./"` explicitly so the built page can be served from
  any path by the harness. Copy that too.

### C. TownhouseStudio is a prior attempt at *this exact target*

- `tools/TownhouseStudio/README.md:1-3`: built "strictly following the **img2threejs**
  methodology" — one of the two sources the brief says to surpass.
- Its subject is the brief's reference scene, item for item: mint/terracotta/tan
  facades, fire escape, awning, AC unit, clothesline, trash can, crates
  (`README.md:41-69`).
- **It is untracked.** `git status --porcelain -- tools/TownhouseStudio` → `?? `, and
  `git log -- tools/TownhouseStudio` is empty. A BlindLoop worktree is cut from `HEAD`
  (`orchestrator.mjs:214`), so **TownhouseStudio does not exist inside any candidate
  worktree**. Anything reused from it must be committed first.
- Its failure profile is the brief's failure list:
  - **Absolute magic coordinates, no anchors.** `TownhouseModel.js:220-224` —
    `const bX = -5.0; const bW = 5.2; const bD = 8.0; const frontZ = 2.7;` then every
    child placed by hand-computed literal (`:227`, `:249-250`). Nothing declares
    attachment; a scale change silently detaches children. This *is* failure mode 1 and 3.
  - **415 sub-meshes / ~40 materials.** `README.md:39`; `materials.js:7-30` builds a
    separate `MeshStandardMaterial` per surface. Against a one-material / one-draw-call
    target (`character.test.js:104-113`) that is a different architecture, not a tuning gap.
  - **9,020 triangles** (`README.md:39`) already exceeds the brief's <8k building budget,
    before any tri-budget test exists — there is none.
  - **No capture mode, no seed, no determinism, no tests.** `grep -n "capture\|seed\|
    Math.random" src/viewer.js src/model/*.js` → no hits. It cannot be looped as-is.
  - **Ink outlines as `LineSegments`** (`TownhouseModel.js:50-57`, `addInkEdges`) — extra
    draw calls and geometry that will not survive glTF→Unity as intended.

### D. ProceduralCharacterFoundry / SimHarness

- **ProceduralCharacterFoundry** (`README.md:1-5`): the pre-V2 character tool — three.js
  on one immutable T-pose skeleton, vite port 4190, plus `server.mjs` + `start.cmd` for a
  non-dev launch. Superseded by CharacterStudioV2 for every purpose here; only the
  `npm start` static-server pattern is transferable, and only if vite is ever dropped.
- **SimHarness** is C# (`SimHarness.csproj`, `ZoneSim.cs`) — a headless gameplay-sim
  harness for the Unity economy. **Not relevant** to this workstream.

---

## Techniques worth stealing

### 1. The exact interface `tools/LLMModeling` must expose to be looped

Deliverable 1. Required surface, in the order the harness touches it:

| # | Requirement | Contract source |
|---|---|---|
| 1 | `package.json` scripts `dev`, `build`, `preview`, `check` — `dev` and `preview` must accept `-- --host 127.0.0.1 --port <n> --strictPort` | `orchestrator.mjs:309-311`, `capture-candidate.mjs:15-19`; shape from `CharacterStudioV2/package.json:8-12` |
| 2 | `vite.config.js` with `base: "./"`, fixed `server.port`/`preview.port`, `strictPort: true` | `CharacterStudioV2/vite.config.js:2-9` |
| 3 | URL param `?capture=1` puts the page in a no-UI, no-rAF, no-damping, single-render mode | `studio.js:6-12`, `:76`, `:388-416` |
| 4 | URL params `seed`, `size`, plus project-specific selectors (CS2 uses `preset`, `view`; a building tool likely wants `subject`, `view`) — all parsed from `URLSearchParams` and reflected back into the manifest | `studio.js:70`, `:98-130`, `:404-413` |
| 5 | An unknown selector value must warn + use defaults, never silently substitute another | `studio.js:105-108` |
| 6 | `window.__CAPTURE_READY__ = true` set **after** the single `renderer.render` | `studio.js:415`; polled by `capture.mjs:83-92` |
| 7 | `window.__CAPTURE_MANIFEST__` = a non-null object; absence is capture drift and voids the round | `capture.mjs:99`, `:114-116` |
| 8 | `renderer.setPixelRatio(1)`, square `setSize(size,size,true)`, `camera.aspect = 1` | `studio.js:394-397` |
| 9 | Determinism: three captures of the same URL byte-identical | `preflight.mjs:69-91` |
| 10 | A sibling config `tools/BlindLoop/config.llmmodeling.json` — copy of `config.json` with `project.root: "../LLMModeling"`, a distinct port, and the project's own `urlTemplate` | `capture.mjs:18-20`, `:175` (`--config` supported) |
| 11 | A forked worker adapter `tools/BlindLoop/adapters/worker-llmmodeling.mjs` whose gate line runs `npm --prefix tools/LLMModeling run check` | `adapters/worker-claude.mjs:55` (hardcodes CharacterStudioV2) |

**Manifest schema to mirror** (`studio.js:404-413`) — keep the key names, swap the
domain fields:

```js
window.__CAPTURE_MANIFEST__ = {
  triangles,            // triangleCount(root)   — geom.js:550
  materials, drawCalls, // 1 / 1, as character.js:222-223 records
  boundsM: bounds,      // measure(): w/h/d/minY — character.js:232-244
  params: {...},        // every resolved knob, colors included
  view, subject, size,  // what the URL asked for, resolved
};
```

### 2. Modules reusable from CharacterStudioV2

Deliverable 2. `src/geom.js` is the prize: it is pure three.js + a seeded RNG,
imports nothing character-specific, and every one of these is **copy-importable as-is**
(no extraction needed) — CS2 must be treated as read-only, so **fork the file into
`tools/LLMModeling/src/geom.js` rather than importing across project roots** (a
cross-tool relative import would break the worktree/vite root assumption at
`orchestrator.mjs:308`).

| Module | `file:line` | Status for LLMModeling |
|---|---|---|
| Seeded RNG (`hash32`, `rng`) | `geom.js:45`, `:56` | as-is. Determinism spine. |
| `paint()` — per-**facet** vertex colour with AO ramp, up-tint, wrap term | `geom.js:116-178` | as-is. The facet-pairing at `geom.js:79-107` is the fix for quads shading as two triangles — do not re-derive it. |
| `characterMaterial()` — the single `MeshStandardMaterial({vertexColors, flatShading, roughness .92, metalness 0})` | `geom.js:181-189` | as-is, rename to `assetMaterial()`. This is the "one material" the whole style depends on. |
| `bevelBox` (chamfered box — "what stops them looking like Minecraft cubes") | `geom.js:201` | **highest-value primitive for hard-surface.** as-is. |
| `taperBox`, `prism`, `stepStack`, `plate`, `wedge` | `geom.js:228`, `:252`, `:268`, `:281`, `:300` | as-is. `stepStack` is literally stoop stairs; `plate` is parapet coping / sills. |
| `ring` / `wall` / `fan` / loft | `geom.js:330`, `:350`, `:372`, `:389` | as-is. Pipes, vents, trash cans. |
| `mergeGeometries`, `mirrorX` | used at `character.js:14` | as-is. One-draw-call merge. |
| `triangleCount()` (honours `userData.excludeFromExport`) | `geom.js:550-559` | as-is. The tri-budget probe. |
| Tri-budget + hygiene tests | `test/character.test.js:23-28` (budget), `:56-64` (seed determinism), `:78-84` (no NaN/Inf), `:87-90` (feet on y=0), `:104-113` (one mesh/one material/no texture) | **fork the harness, rewrite the assertions.** These five are exactly the guards the brief's failure modes need. Wire into `npm run check` like `package.json:11`. |
| GLB export, frozen options `{binary, trs, onlyVisible}` + `excludeFromExport` hide/restore | `exporters.js:22`, `:35-49`, `:69-77` | as-is minus the skeleton clause. **No FBX exporter exists anywhere in the repo** — glTF/GLB only, `three/addons/exporters/GLTFExporter.js` (`exporters.js:17`). FBX would be a new dependency; Unity ingests `.glb` natively. |
| `exportModuleSource()` — emits a self-contained `createAsset(overrides)` `.mjs`, byte-identical for identical params | `exporters.js:97-131` | as-is in spirit. This is the natural handoff format for an LLM-authored asset. |
| `capturePng(renderer, scene, camera)` | `exporters.js:189-224` | as-is for in-app stills; the loop uses Playwright instead. |

### 3. The `blockout-spec.json` attachment schema — steal this, it targets failure mode 3

`CharacterStudioV2/blockout-spec.json` declares each part as
`{name, primitive, parent, attach_to:{part, contact}, evidence}` with a closed
`contact` vocabulary — **`rests-on-top` (4), `socket` (3), `embedded` (3)** across 13
parts, plus `anchor_size_m` and an `anatomy` block of ratios in head-units.

- Nothing in the repo consumes it (`grep -rn "blockout-spec" tools/` → no code hits), so
  it is a **schema sketch, not a validated system**. That is the gap LLMModeling should
  close: make the spec the *authoritative input* and derive coordinates from it, so
  "floating part" becomes a **schema violation checkable at build time** rather than
  something only a judge can see.
- The `evidence` field per part ("hem at hip not mid-thigh") is a good discipline for an
  LLM-authored spec: it forces the model to justify each part against the reference
  before geometry exists.
- `TownhouseStudio/src/model/townhouse-spec.json:1-10` shows the img2threejs
  `ObjectSculptSpec` head (`object`, `version`, `generator`, `reference`,
  `anchor_size_m`, `materials`) — the same shape, minus any attachment vocabulary. That
  omission is why `TownhouseModel.js` fell back to magic literals.

### 4. Rules the new project must not break

- Never edit `BLIND_LOOP.md`, `config.json`, `capture.mjs`, `orchestrator.mjs`,
  `preflight.mjs`, `roles/*.md` (`config.json:32-42`). A candidate diff touching one is
  rejected pre-judging and logged as a loss (`BLIND_LOOP.md:110-113`, guard at
  `orchestrator.mjs:255-260`).
- Never special-case the capture URL, seed or ready flag to game the judge
  (`roles/worker.md:39-40`).
- Working tree must be **clean** before a run (`preflight.mjs:134-137`) — which means
  **TownhouseStudio's untracked tree must be committed or removed before the first
  LLMModeling round**, or preflight's frozen-file check passes but the dirty tree makes
  a merged winner's diff ambiguous (`RUNBOOK.md:~63`).
- CharacterStudioV2 is a *live* BlindLoop target (`config.json:4`). LLMModeling must not
  edit anything under `tools/CharacterStudioV2/` — copy, never import, never modify.

---

## Dead ends

- **Reusing `TownhouseModel.js` as a code base — no.** Verdict (deliverable 3):
  **fork the *content*, ignore the *code*.** Keep it as (a) a ready-made **subject
  inventory** for the item list (`README.md:41-69` enumerates every part the brief names)
  and (b) a calibrated **palette source** (`townhouse-spec.json` materials block,
  `materials.js:7-30` hexes, matched to the reference illustration). Discard the geometry
  layer: absolute literals with no anchors (`TownhouseModel.js:220-250`), 415 meshes /
  ~40 materials against a one-material target, 9,020 tris over budget, `LineSegments` ink
  outlines, no seed, no capture mode, no tests. Porting costs more than rebuilding on
  `geom.js` primitives, and it carries the exact defects the loop exists to remove.
- **Importing CS2 modules across project roots — no.** `orchestrator.mjs:308` serves the
  candidate from `<worktree>/tools/LLMModeling`, and `linkNodeModules`
  (`:232-243`) only links *that* project's `node_modules`. A relative import reaching
  into `../CharacterStudioV2/src/` would resolve in dev and be fragile-to-broken under
  `vite build` in a worktree. Copy the files.
- **Reusing `config.json` with extra params — no.** It is frozen and preflight fails on
  any uncommitted modification (`preflight.mjs:134-137`). Sibling config file only.
- **The Unity BlindLoop lane (`orchestrate.ps1`, `capture-settings.json`) — not
  applicable.** It serialises captures because one editor holds one project lock
  (`RUNBOOK.md:19-27`). The web lane runs candidates in parallel on separate ports; use it.
- **FBX export — not available locally.** Only `GLTFExporter` exists
  (`exporters.js:17`). Treat FBX as out of scope unless the owner rules otherwise.

---

## Node / tooling conventions to match (deliverable 4)

- **Node v24.11.1, npm 11.6.2** (measured on this machine, `node --version`).
  BlindLoop relies on Node ≥18 globals: top-level `await`
  (`capture-candidate.mjs:23`), global `fetch` (`preflight.mjs:59`), `node:test`
  (`CharacterStudioV2/package.json:11`).
- **`"type": "module"`, `private: true`** in every tool package
  (`CharacterStudioV2/package.json:3-5`, `TownhouseStudio/package.json:4-5`,
  `BlindLoop/package.json:4-5`).
- **three `^0.185.1`, vite `^8.1.5`** — identical across CharacterStudioV2, TownhouseStudio
  and ProceduralCharacterFoundry. Pin the same; a version split would change shading and
  void cross-project comparison.
- **`build.target: "es2022"`, `base: "./"`** (`CharacterStudioV2/vite.config.js:9`, `:6`).
- **Port convention, one per tool:** 4190 ProceduralCharacterFoundry, 4193
  CharacterStudioV2, 4200 TownhouseStudio. **Take 4210 for LLMModeling** — must not
  collide with 4193 while a CS2 loop is live.
- **`npm run check` = `node --check` every source file + `node --test`**
  (`CharacterStudioV2/package.json:11`); `npm run gate` = `check && build` (`:12`). The
  worker adapter calls `check` as its build gate (`worker-claude.mjs:55`). Mirror both
  script names exactly.
- **`.gitignore`**: `node_modules/`, `dist/`, `out/`, and third-party reference renders
  (`CharacterStudioV2/.gitignore:1-5`). LLMModeling currently ignores only `out/` —
  add the rest before the first `npm install`.

---

## Open questions

1. **`orchestrator.mjs` cannot take a config override.** It hardcodes
   `path.join(HERE, 'config.json')` (`orchestrator.mjs:20`) while `capture.mjs:175` and
   `preflight.mjs:17` both do too. Options, all needing an owner ruling because these are
   frozen files: (a) add a `BLINDLOOP_CONFIG` env var to all three — a one-line change
   each, but it edits three frozen files; (b) copy the whole harness to
   `tools/LLMModeling/loop/` — duplication, drift risk; (c) run LLMModeling rounds only
   while no CS2 run is active and temporarily repoint `config.json` — violates "frozen
   for the run" if the two overlap. **Recommend (a), owner-gated**, since the frozen
   guarantee is per-run and this is a pre-run structural change.
2. Does LLMModeling capture **one view or a view set**? CS2 captures a single
   `threeQuarter` frame (`config.json:17`). A building's fire escape is on the side wall
   (`TownhouseStudio/README.md:47`), invisible in one three-quarter frame — and
   `BLIND_LOOP.md:~148` requires every item be *observable in the frozen capture*. A
   multi-view contact sheet composited into one PNG would keep the single-artifact
   contract; a multi-image judge set would not. Unresolved.
3. **Tri budget per what?** The brief says props <2k / buildings <8k, but CS2's budget is
   a single constant (`studio.js:26`, `TRIANGLE_BUDGET = 4000`) and its test asserts one
   number for all presets (`character.test.js:23-28`). A per-subject budget table is
   needed before the test can be written.
4. Should the untracked `tools/TownhouseStudio/` be committed (as reference/palette
   provenance) or deleted? Preflight needs a clean tree either way; leaving it untracked
   also keeps it out of every candidate worktree.
5. Is Blender-Python generation still in scope? `LLMModeling/README.md:5,10` mentions
   "Blender Python / Three.js", but nothing in BlindLoop's web lane can capture a Blender
   render — that would need a third capture lane. Three.js-only keeps the existing
   harness intact.
