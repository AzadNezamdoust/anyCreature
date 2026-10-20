# S1 brief — kernel + smoke (Opus implementer, 2026-09-12)

Authority: `V2-TEST-PLAN.md` §2, §3, §6 row S1 (read it first, whole file). Owner said go.
Working dir: `D:\Git\checkout\tools\LLMModeling` (Windows, Node 24.11.1, PowerShell or bash).
Never touch `tools/CharacterStudioV2`, `refs/**`, `src/validate/limits.json`, `tools/BlindLoop/config*.json`,
or any existing v1 file except the two edits named below. New files only otherwise. No commits.

## Deliverables

1. `package.json`: add exact pins `"manifold-3d": "3.5.3"`, `"three-mesh-bvd"` NOT yet (S2). Run `npm install`.
   Keep `npm run check` green (v1 suite must still pass; run it at the end and report).
2. `src/kernel/index.mjs` — closed API over manifold-3d, exported as named functions so an author
   writes `import * as K from "../../src/kernel/index.mjs"`:
   - `await K.init()` (loads the WASM once; every other call throws if not initialised).
   - `box([w,h,d])` — local frame identical to `src/prims.js:5-8`: x and z centred, y from 0 to h.
   - `extrude(profile, depth, {holes?: profile[]})` — profile is a 2D polygon in XY (metres),
     extruded along +Z from z=0 to z=depth. Holes subtract.
   - `revolve(profile, segs)` — profile in XY, revolved around local Y.
   - `cut(a, b)`, `union(a, b)`, `intersect(a, b)` — return new solids; inputs unchanged.
   - `cut` throws `KernelError("V5_THIN ...")` if the result's min wall thickness under the cut
     region falls below MIN_FEAT = 0.06 m. Cheap check acceptable for S1: compare bounding-box
     depth of `a` minus depth of `b` overlap; document the limit in README. Exact check is S2.
   - Solid wrapper methods: `.at([x,y,z])`, `.rotY(deg)`, `.rotX(deg)`, `.rotZ(deg)`, `.mirrorX()`,
     `.volume()`, `.aabb()` → `{min:[..],max:[..]}`, `.status()` (manifold status string),
     `.genus()`, `.decompose()` → solid[], `.mesh()` → manifold MeshGL.
     Every transform returns a NEW solid (immutable style), so an author can reuse a tool solid.
   - `repeat(n, pitch, fn)` → array of whatever `fn(i, offset)` returns; pure helper.
   - `profile.rect({w,h})`, `profile.arch({w,h,rise,segs})` (rect + half-round/segmental head,
     `segs` even-numbered facets, base at y=0, centred on x=0), `profile.offset(profile, d)`
     (outward offset by d, mitred corners, for reveals), `profile.stepped(steps:[{w,h}...])`
     (cornice: stacked rects, each centred, from y=0 up), `profile.wedge({w,h,run})`
     (awning section, right triangle + rect), `profile.poly(points)` (raw, validated: ≥3 points,
     non-self-intersecting via simple check, CCW).
   - Deterministic: no `Math.random`, `Date`, `performance`. Same input → same MeshGL.
3. `src/kernel/toThree.mjs` — `solidToGeometry(solid)` → non-indexed THREE.BufferGeometry with
   flat normals (each triangle its own 3 verts), so `paint()` from `src/geom.js:116` works
   unchanged. `partsToGeometry(parts, palette, seed)` → for each `{id, solid, zone}`: geometry,
   `paint(geo, palette[zone] ?? "#ff00ff", {seed: `${seed}:${id}`})`, then
   `mergeGeometries` (`src/geom.js:520`). Return `{geometry, parts (with aabb + triCount per
   part), bounds}` in the SAME shape `compile()` returns (`src/compile/build.js:164-200`), so
   `app.js` can render it without a new code path.
4. `src/kernel/README.md` — the author-facing API doc, ≤120 lines, with the V2-TEST-PLAN §2
   mini-example verbatim. This text is inlined into every Astra prompt; write it for a model
   that sees nothing else: every function, its frame, units, what throws.
5. `scripts/check-module.mjs <file.mjs>` — static gate: reject any import other than the kernel
   path (`../../src/kernel/index.mjs` or absolute equivalent), any `Math.random`, `Date`,
   `fetch`, `performance`, `require`, `process`, `import(`, `eval`, `new Function`. Then dynamic:
   `await import(file)`, check `meta` (class, seed, palette object) and `build` is a function,
   run `build()` after `K.init()`, check every part has `id` (unique), `solid`, `zone` (key of
   palette). Exit 0/1 with ≤8 lines of text.
6. `subjects/facade_brick/facade.mjs` — SMOKE only (Astra replaces it in S4): one 8×11×0.35 wall
   box with one arched door cut + stepped reveal exactly as the §2 example, plus one iron bar
   `box([0.06, 3, 0.06])` at x=3.5 touching the wall face. Three parts. `meta.palette` with
   brick/trim/glass/iron.
7. `src/app.js:31` `SUBJECT_SPECS`: add `facade_brick: "./subjects/facade_brick/facade.mjs"`.
   In `loadSpec()`/compile site (`app.js:191-320`) branch on `.mjs` extension: dynamic-import
   the module, `await K.init()`, run `check-module`-equivalent runtime checks, call
   `partsToGeometry`, and use `hash32` of the module SOURCE TEXT (fetch it) in place of
   `specHash` (plan §2). Keep the capture URL contract `(subject, view, seed, size)` untouched.
   Minimal diff; every added line commented `// V2:`.
8. `scripts/bench-kernel.mjs` — node: init, build smoke, time (a) build ms, (b) 20 sequential
   `cut`s of small boxes from the wall, (c) one `cut(wall, union(20 tools))`. Print ms + tris.
9. `vite.config.*` if needed for the WASM (`optimizeDeps.exclude: ["manifold-3d"]` is the
   documented workaround). Prove `npm run build` and `npm run dev` both serve `facade_brick`.

## Stop point (report these numbers, PASS/FAIL each, no prose beyond one failing excerpt)
- `node scripts/check-module.mjs subjects/facade_brick/facade.mjs` exit 0.
- `node scripts/bench-kernel.mjs` numbers.
- `npm run check` green (v1 suite).
- `npm run build` green.
- Dev server on port 4210 serves `http://127.0.0.1:4210/?capture=1&subject=facade_brick&seed=1&view=target&size=900`
  with a visible wall + arch + bar (leave the server running; report its PID).
- Do NOT run the 3× capture yourself; the reviewer does.
