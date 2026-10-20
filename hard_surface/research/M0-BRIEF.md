# M0 brief — Loopable shell + massing (implementer seat, Opus 5)

Read first: `tools/LLMModeling/PLAN.md` (all of it), `research/05-local-reuse.md` §1–2 and
`research/08-opus-revision.md` §4 (gaps G4–G9). Then the CharacterStudioV2 files cited in
PLAN §6 (read the cited ranges, not whole files). Do NOT modify anything under
`tools/CharacterStudioV2/` or any BlindLoop frozen file (`tools/BlindLoop/config.json:32-42`).

## Scope (exactly this, nothing more)

Create `tools/LLMModeling/` as a vite + three.js project that compiles an attachment-program
spec to one merged flat-shaded vertex-coloured mesh, renders it deterministically in capture
mode, exports GLB, and captures byte-identically three times.

### Files to create
1. `package.json` — `"type":"module"`, `private:true`, scripts: `dev` (vite), `build`,
   `preview`, `check` (`node --check` every `src/**/*.js` + `node --test test/`), `gate`
   (`check && build`). Deps: `three ^0.185.1`, `vite ^8.1.5` (devDep). No other deps in M0.
2. `vite.config.js` — `base:"./"`, `server.port 4210`, `preview.port 4210`, `strictPort:true`,
   `build.target "es2022"`. Must accept `-- --host 127.0.0.1 --port N --strictPort` passthrough
   (vite does natively; verify).
3. `index.html` + `src/app.js` — studio: OrbitControls in normal mode; under `?capture=1`:
   no controls, no rAF loop, no damping, `renderer.setPixelRatio(1)`,
   `renderer.setSize(size,size,true)`, `camera.aspect=1`, ONE `renderer.render`, then set
   `window.__CAPTURE_MANIFEST__ = {triangles, materials:1, drawCalls:1, boundsM:{w,h,d,minY},
   subject, view, seed, size, specHash, dslVersion:"pg/1", validatorPass, violationCount,
   repairCount:0, v8Dropped:0, cameraId}` then `window.__CAPTURE_READY__ = true` and
   `document.body.dataset.captureReady="1"`. URL params: `capture, subject, view, seed, size`.
   Unknown `subject`/`view` → `console.warn` + defaults (never silently substitute). Nothing in
   the capture path reads clock, devicePixelRatio, window size or Math.random. Load specs with
   `fetch('./subjects/<subject>/spec.json')` in dev; for build, copy `subjects/` into `dist/`
   via vite `publicDir` or a static copy so `preview` serves it with no network dependency
   (PLAN §4, 08:G8). Overlay/UI is hard-off under `capture=1`.
   Views: `target` = OrthographicCamera, position `setFromSphericalCoords(100, PI/2 - theta,
   phi)` + AABB centre, `lookAt` centre, frustum = AABB height / 0.86 square, `up (0,1,0)`,
   `setClearAlpha(0)`; theta/phi read from `refs/<subject>.camera.json` if present else
   provisional `{theta_deg:30, phi_deg:45, provisional:true}` (write that file for the
   tenement now, flagged provisional). Also `threeQuarter` perspective view like CS2 for humans.
   Lighting: one directional + hemisphere, fixed positions (copy CS2's).
4. `src/geom.js` — verbatim copy of `tools/CharacterStudioV2/src/geom.js`. `src/material.js`
   — `assetMaterial()` = CS2 `characterMaterial()` (vertexColors, flatShading, roughness .92,
   metalness 0).
5. `src/compile/resolve.js` — attach solver exactly per PLAN §1.2 (face-frame table, operation
   order 1–7, `align`, `embed`). Support prims `box, bevelBox, plate` (from geom.js) and
   contacts `flush, rests-on-top, socket`. `src/compile/expand.js` — `repeat{axis,count,pitch}`
   (parent-local axis, writes world direction) and `mirror`. `src/compile/build.js` —
   spec → `solved` object `{parts:[{id,prim,dims,matrix,zone,parentId,contact,genus,triCount,
   aabb,worldRepeatAxis}], bounds, triangles}` + one merged BufferGeometry, painted per facet
   via geom.js `paint()` using `palette[zone]`. Seed → `rng("${seed}:${partId}")`.
6. `src/validate/v0.js` — schema + DAG (attach.to names an earlier id) + ground rule (parts
   without `attach` must be `ground:true`, ≥1 ground) + unknown prim/contact/zone. Returns
   `{pass, violations:[{v:"V0", part, measured, limit, hint}]}`. Only V0 in M0.
7. `src/exporters.js` — GLB export via `three/addons/exporters/GLTFExporter.js`, options
   `{binary:true, trs:false, onlyVisible:true}`, vertex colours as COLOR_0. Expose
   `window.__exportGLB()` in studio + a `scripts/export-glb.mjs` is NOT required in M0 (browser
   button is enough).
8. `dsl/SPEC.md` — the DSL doc for pg/1 as implemented in M0 (parts, attach, align, embed,
   repeat, mirror, palette/zone, ground, prim list, contact list, face-frame table). Keep it
   ≤150 lines; it ships in-context to the model later.
9. `dsl/schema.json` — JSON schema for pg/1 (hand-written, used by v0.js).
10. `subjects/tenement_block/spec.json` — hand-authored MASSING ONLY: three adjoining masses
    (mint 6.0×9.6×8.0 ground; brick 5.2×10.4×8.0 flush +X; tan 5.6×9.6×8.0 flush +X),
    parapet plates on each roof, a stoop `bevelBox` stack (two steps) socketed into the mint
    +Z face, one door box per building (socket, embed 0.08, align bottom), a roof stair
    bulkhead box on the mint roof, two chimney-pipe boxes on the brick roof. Palette from
    `refs/README.md` description: mint `#9fd3b8`, brick `#c9573f`, tan `#c9b391`, stone
    `#b9b3a8`, iron `#3b3f4a`, foundation `#8f7f8c`. Must pass V0. No facades in M0.
11. `dsl/examples/crate.json` (one bevelBox ground + a lid plate rests-on-top) and
    `dsl/examples/bench.json` (seat plate + 2 leg boxes hangs-below is NOT supported in M0 —
    use legs as ground parts and seat rests-on-top of leg_1 with the second leg flush… keep it
    valid under M0 contacts). Both must pass V0.
12. `test/determinism.test.js` — build the tenement spec twice with seed 1 → identical vertex
    buffers (byte compare of position + color arrays); seed 2 differs in colour jitter only if
    jitter exists. `test/v0.test.js` — each example + subject passes; three inline broken
    specs (cycle, missing ground, unknown prim) fail with exactly one V0 violation each.
    `test/budget.test.js` — tenement triangles < 8000 (provisional limit, note it is unratified).
13. `refs/tenement_block.camera.json` — `{theta_deg:30, phi_deg:45, provisional:true,
    note:"measure from refs/tenement-iso.png with scripts/solve-camera.mjs before M4"}`.
14. `tools/BlindLoop/config.llmmodeling.json` — copy of `config.json` with
    `project.root "../LLMModeling"`, `devServerUrl http://127.0.0.1:4210/`, urlTemplate
    `http://127.0.0.1:4210/?capture=1&subject={subject}&seed={seed}&view={view}&size={size}`,
    defaults `{subject:"tenement_block", seed:1, view:"target", size:900}`, and `frozenFiles`
    = the original list + `tools/BlindLoop/config.llmmodeling.json`,
    `tools/LLMModeling/refs/**`, `tools/LLMModeling/src/validate/limits.json`. Do NOT touch
    `config.json`. `tools/BlindLoop/adapters/worker-llmmodeling.mjs` — fork of
    `worker-claude.mjs` whose gate line runs `npm --prefix tools/LLMModeling run check` and,
    on non-zero exit, reverts the worktree (`git checkout -- . && git clean -fd` inside the
    worktree) then exits 0 so the orchestrator records an empty diff (08:G3). Read the
    original adapter fully before forking.
15. Update `tools/LLMModeling/README.md` Status line to "M0 in progress/done" as appropriate.

### Evidence required (write to `tools/LLMModeling/out/m0/` and summarise in your report)
- `npm install` then `npm run check` exit 0 (paste the last 10 lines).
- Start the dev server (use the Browser preview tool with a `.claude/launch.json` entry
  `llmmodeling` → `npm run dev -- --host 127.0.0.1 --port 4210 --strictPort` in
  `tools/LLMModeling`, or `capture.mjs`'s own path if it starts the server — read
  `tools/BlindLoop/capture.mjs` header to see what it expects). Then run
  `node tools/BlindLoop/capture.mjs --config tools/BlindLoop/config.llmmodeling.json --out
  tools/LLMModeling/out/m0/cap1.png` (check the real CLI flags in capture.mjs) three times
  → `cap1/2/3.png`; report `sha256` of all three (must be identical) and the manifest sidecar.
- Screenshot of the `threeQuarter` view for a human (any size) as `out/m0/human.png`.
- Timing: `console.time` around build+V0 in a node script `scripts/bench.mjs` (three.js works
  in node for geometry) — report ms for the tenement spec.
- Stop the dev server before finishing.

### Rules
- Never import from `../CharacterStudioV2`; copy files.
- Mark shortcuts `// MVP-STUB:`.
- Do not implement V1–V10, facades, composites, LLM scripts, SAM, or IoU. Those are M1–M3.
- If something in PLAN is impossible as written, implement the closest working thing, mark
  it `// DEVIATION:` with one line why, and list every deviation in your report.
- Report format: PASS/FAIL per acceptance item, deviations, files created, evidence paths,
  one failing excerpt max. No transcript.
