# 01 — Source repo dissection: anyCreature and img2threejs

Fable analysis seat, 2026-09-10. Sources fetched from `raw.githubusercontent.com` at HEAD
(anyCreature v1.3.1, `VERSION`; img2threejs v2.0.0, `SKILL.md:5`). Neither repo is a fork
(GitHub API `fork:false` for both). `AC/` = `github.com/Ariescar/anyCreature`, `I2T/` =
`github.com/img2threejs/img2threejs`. Line numbers are from the fetched HEAD copies.

## Findings

### A. anyCreature — a compiled JSON DSL with an engine-side legality checker

- **Pipeline.** Text order → one clarifying question → nine-slot brief → LLM writes ONE JSON
  spec (joints/chains/volumes/parts/palette/animations) → `node engine/cli.js spec.json out.glb`
  compiles to a skinned, vertex-coloured, AO-baked GLB → `harness/round.py` builds + projects
  silhouettes from geometry + measures + preflights in one command → a *context-free reader
  subagent* answers "what is this?" on 24/48 px thumbnails → repair → MID (all parts) → HIGH
  (colour + 3 anims) → SHIP. `AC/README.md` "How it works" mermaid; `AC/cards/00_START.md:3-7`.
- **LLM output format is never three.js.** The model emits a *relational* skeleton
  (`"Chest": {"from":"Hips","fwd":0.1,"up":0.5}`, `AC/engine/core/relative.js:1-11`) plus tube
  volumes as profile rows `[t, half-width, half-height, {exp,bias,sharp}]` lofted along a chain
  (`AC/engine/core/compile.js:110 buildVolume`), and a closed part vocabulary: `curve`,
  `membrane`, `fin`, `eye`, `hand`, `paw`, `spike` (`AC/cards/SYNTAX.md`). Boxy masses come from
  superellipse exponent `exp 2.5-4 = boxy slab` on a tube row — there is no box/plane primitive.
- **Validation is real geometry, engine-side, and BLOCKs the build** (`AC/engine/core/checks.js`
  `runChecks`): `root_containment` (chain root ring ≥80% inside host, :383), `part_attachment`
  (nearest part vertex within `0.015 × modelH` of host surface, :435-470), `touch` (declared
  chain pairs must overlap or be within `0.01 × modelH`, :745-765), `part_seat` (declared join
  `insert` needs base ring ≥60% buried; `extrude` needs base centre inside a body, :795-845),
  `balance` (mass centre inside support footprint, :337), `size` (±15% of declared height, :243),
  `mesh_integrity` (flipped tris, :517), `limb_clearance`, `mirror_distortion`, `anim_integrity`,
  `attack_reach`. Every message states the corrective MOVE in metres, not just the gap
  (`checks.js:455-458` comment: "Say the MOVE, not just the gap").
- **Every check is tagged block/advise and allocate/verify** (`AC/harness/gates.json`, 35 checks;
  `AC/cards/00_START.md` "Every check is tagged twice"). Advisories (6:3:1 hierarchy, focal
  contrast, `thinnest_px48`, `tri_budget`) never stop a build.
- **Minimum feature size exists only as an advisory pixel ruler.** `thinnest_px48` = width of the
  thinnest protrusion on the 48 px thumbnail (`AC/harness/maskmetrics.py:63-64`,
  `gates.json` id `thinnest_px48`, `enforce: advise`). The engine ignores edges shorter than
  `1.5% of model height` when *voting* (`checks.js` `edgeFloor`) but never refuses thin geometry.
- **Silhouettes are computed, not photographed.** `AC/harness/outline.py` projects triangles
  under the same 30° perspective camera as the renderer and rasterises the masks in numpy;
  verified vs Chromium masks at IoU 0.980-0.989; a round dropped 9.0 s → 1.4 s, a 3-variant round
  11.0 s → 4.4 s (`AC/cards/00_START.md` "LOW no longer needs a browser at all"). Chromium
  (playwright, bundled three.js) is used only for colour judging, hero shots, viewer.
- **No VLM critic in the loop; a blind human-proxy reader instead.** Readers get shuffled
  neutral labels, a canary image with a known answer, and a bump-count binding question; a
  tripped trap voids the read (`AC/cards/01_LOW.md` §4, :218-276). Verdict is *scored*: "rank R
  passes if the noun reached R in at least R views" (`§4b`, `harness/identity.py`).
- **Isolated-part reads were deleted as a failed technique** — "a crown reads as 'a blob', a face
  as 'a stone'"; colour reads replaced by palette arithmetic (`value_order`, `contrast_adjacent`
  in OKLab) (`AC/cards/02_MID.md:25-64`).
- **Round economics doctrine:** cost = conversation round-trips, not compute ("a compile is
  1.4 seconds, a silhouette view half a second", `00_START.md` "The thing that actually costs
  money: TURNS"); one command per phase; build two opposite poles per round, not one attempt
  (`01_LOW.md:354-400`); "same symptom failed twice = no third tweak", enforced by
  `roundcheck.py` reading `iou_vs_prev` (iron law 3).
- **Output contract:** GLB, two chunks, no textures, colour + AO baked into `COLOR_0`, primitives
  merged per material, convention bone names, the source spec embedded in `asset.extras`
  (`AC/docs/OUTPUT_CONTRACT.md`, `AC/engine/core/glb.js:1-4`). Example wolf: 23 joints,
  5 volumes, 5 parts, 8 materials, 2,211 verts (`example/wolf.json`, README).
- **Hard-surface is an escape hatch, not a mode.** `"build":"rigid"` only lifts the
  `faceted_body` and `soft_mass` blocks ("robots/constructs/golems/vehicles ONLY",
  `SYNTAX.md`); everything else (balance, root containment, chains, mirror) is creature-shaped.

### B. img2threejs — an image-to-spec-to-TypeScript skill with a deterministic pixel judge

- **Pipeline.** Reference image → agent vision "layered observation" → `new_pre_spec_assessment`
  (class, 8 complexity scores, `qualityContract`, `detailInventory`) → LLM authors an
  `ObjectSculptSpec` JSON (component tree with `primitive`, `dimensions`, `parent`,
  `attachment`, `topologyClass`, materials, sockets) → `validate_sculpt_spec.py --strict-quality`
  → `generate_threejs_factory.py` emits a TypeScript `createXModel()` for the *current pass only*
  → browser render (agent's own screenshot tool, or optional Playwright adapter) → one
  side-by-side sheet → deterministic "Divine Eye" → optional VLM → one of
  `continue|refine-spec|refine-code|request-input|stop` → next pass. Eight locked passes:
  `blockout → structural-pass → form-refinement → material-pass → surface-pass → lighting-pass →
  interaction-pass → optimization-pass` (`I2T/forge/stage3_build/orchestrate_passes.py:18-27`;
  `I2T/docs/ARCHITECTURE.md` mermaid).
- **LLM output format is a spec JSON plus hand-edited TS.** The generator maps `primitive` to
  `THREE.BoxGeometry/SphereGeometry/CylinderGeometry/ConeGeometry/TorusGeometry`, a lathe, an
  extrude profile, a tube path, a `ringStack`, an SDF polygoniser or a visual hull
  (`I2T/forge/stage3_build/generate_threejs_factory.py:1811-1843, 856, 413`). `refine-code`
  edits the emitted TS directly; the showcase demos are 4k-line hand-written factories
  (README "Live demos" source links).
- **Prompt engineering is a router + gate contract, not a modelling recipe.** `SKILL.md` is
  447 lines of ordered commands; the copy-paste prompt (`I2T/docs/standard-prompts/build.md`)
  says: "the forge scripts *scaffold*, they do not *assess*… `--strict-quality` fails it with
  around 89 causes. Those are not defects to report; they are your fields to fill." and
  "Never say 'done' when it is 'improved'." Modelling guidance is in `grimoire/` prose read
  lazily ("read the named file at the moment you reach that stage", `SKILL.md:19-21`).
- **Geometry gates exist but most are post-hoc mesh analysers, not constraints.**
  `self_intersection.py` (ray-parity on a closed mesh, deterministic, EPSILON = 1e-3 × bbox
  diagonal), `pairwise_penetration.py` (odd crossings of A's vertices through B, `allowedPairs`
  for intentional contact), `geometry_integrity.py` (boundary/non-manifold edge counts,
  `SEAM_MIN_OVERLAP = 0.02`, `SEAM_MAX_OVERLAP = 0.05`, :13-14), `attachment_anchor.py`
  (worn/held items must name a non-root anchor and, with measured positions, sit within
  `0.25 × anchor extent` or `0.3`, :56-63), `turntable_gate.py` (4-azimuth captures),
  `check_part_coverage.py` (spec component built, none fused). All need an exported mesh JSON
  from the browser (`node runtime/scripts/export_mesh_geometry.mjs`, `SKILL.md` step 7a).
- **The "attachment" spec contract is declarative.** `validate_attachment` only checks that
  `parentSocket/localStart/localEnd/contactType/embedDepth|overlap/gapTolerance` *are present*
  and numeric — and emits a **warning**, not an error (`I2T/forge/stage2_spec/validate_sculpt_spec.py:1332-1372`).
  The generator consumes `localStart/localEnd` to orient a tube endpoint only for
  `ATTACHMENT_PRIMITIVES`; the comment records a head being emitted "at y -0.195, inside the
  body, and the model rendered with no head at all" from that branch
  (`generate_threejs_factory.py:3605-3618`). No script measures `embedDepth` against geometry.
- **Divine Eye is a 2-D pixel judge.** HARD: silhouette IoU < 0.85, scale delta > 0.08. SOFT:
  aspect, symmetry, pHash, SSIM on a 64×64 luma grid, Sobel edge overlap on 96×96, tonal parity
  (`I2T/forge/stage4_review/divine_eye.py:9-24, 59-75`). The repo itself documents its blind
  spots: "Silhouette IoU reads ~11% of figure cells: a model with its face deleted scored the
  same 0.8803 as the finished face" (`SKILL.md` Gates; `gates_reference.md` Interior
  difference); "a detail a few pixels wide is absent before any comparison happens"
  (`SKILL.md` Self-Correction); "A strict-PASS at fidelity 0.83 can still read as a flat toy in a
  three-quarter render" (`grimoire/review/self_correction.md:113`).
- **VLM critic is gated and subordinate:** never runs after a hard-gate failure, N-sample
  median vote, spread > 0.20 → `probe`, can rescue a soft reject but never a hard one
  (`I2T/forge/stage4_review/vlm_gate.py:7-21, 34-36`). The sampler is injected; no real VLM call
  ships in the repo.
- **Loop bounds:** 3 corrections per pass, 6 total (`SKILL.md` Mandatory Local State Gate);
  `correction_loop.py` `decide()` stops on repeated defect / oscillation / plateau
  (`min_delta 0.02`) / hard ceiling. Repo's own cost estimate: 5-8 render-review cycles at
  ~5k-12k tokens each, ~80k-180k tokens per object, characters ~150k-350k
  (`I2T/docs/TOKEN_COST.md`), all "engineering estimates, not a measured benchmark".
- **Capture path:** agent screenshot tool by default; `scripts/capture_threejs_playwright.py`
  requires the page to expose `window.__IMG2THREEJS_READY__` and `__IMG2THREEJS_CAPTURE__.setCamera`
  and waits for `requestAnimationFrame` before `page.screenshot` (:75-168). Deterministic-viewer
  rules (disable OrbitControls, fixed 1600×900 viewport, "match" view to ~98% of reference
  width) are prose in `grimoire/feedback/render_capture.md`.
- **Export to GLB is a plugin socket run after all gates** (`I2T/forge/stage3_build/emit_target.py`,
  `docs/EMISSION_TARGET_SOCKET.md`); the core ships TypeScript only. `flatShading` and
  `vertexColors` are supported on emitted materials (`generate_threejs_factory.py:3373, 3689`).
- **Scope:** image-first (`--image` on every intake script); no text-only object route except
  canon-table humanoids. Buildings/rooms/streets are roadmap "v2.2 — The Environment Update"
  (`README.md:347`), i.e. NOT shipped. Hard-surface guidance comes from knife/gun/bike
  failure records (`grimoire/build/geometry_patterns.md:132-330`).

### C. Why the owner's four failure modes arise structurally

1. **Logical placement / relative scale.** I2T: every component carries absolute
   `dimensions` + `transform.position` in world units authored by the LLM from a photo; nothing
   ties a child's size to its parent except prose ("Root/container transform.scale MUST be
   [1,1,1]", `geometry_patterns.md:138`). Placement errors are found only after render by a 2-D
   IoU that "is blind to the other 89%" of cells. The hat-at-hip and charm-4-units-away defects
   (`attachment_anchor.py:4-9`) shipped precisely because parts were parented to root with free
   world transforms. AC avoids this for skeletons (relational joints resolve to a fixed point,
   `relative.js:15-35`) but parts still take free `offset`/`dir` vectors and a `size` in metres.
2. **Too-small / too-thin details.** Neither repo has a minimum-feature-size *constraint*.
   AC's `thinnest_px48` is advisory. I2T's judge runs SSIM on 64 px luma and Sobel on 96 px, so
   thin rails are invisible to the very signal the loop optimises, and the fix is a separate
   "four-tier microscope" the agent must remember to run (`SKILL.md` Self-Correction). I2T's
   `open-shell` topology class *deliberately* permits zero-thickness two-sided surfaces
   (`validate_sculpt_spec.py:76-81, 258-280`) — paper walls are a supported output.
3. **Floating parts / gaps.** I2T: attachment is a spec-presence *warning*; seam overlap
   `0.02-0.05` is enforced only in `geometry_integrity.py` on exported meshes, only for pairs the
   mesh JSON declares adjacent; `pairwise_penetration` catches the opposite defect. The guard/
   handle gap example ("guard ended at X=-0.20, handle started at X=-0.42",
   `geometry_patterns.md:180`) is the canonical symptom. AC solved this for its DSL —
   `part_attachment`, `touch`, `part_seat`, `root_containment` are engine-side BLOCKs — but only
   between a *tube volume* host and a *part*; there is no general solid-solid contact check, and
   `join:"place"` opts out.
4. **Slow iteration.** I2T: 8 sequential passes, each = codegen → browser render → screenshot →
   sheet → agent vision → review JSON → state sync; the repo's own numbers are 5-8 cycles per
   object at 5k-12k tokens each, and the transcript-resident agent is the judge, so every
   cycle re-reads a growing context. AC diagnosed exactly this ("an identical command costs
   several times more at round 20", `00_START.md`) and collapsed a round to one command and a
   1.4 s geometric silhouette — but the *reader* is still a spawned subagent per gate, and the
   builder is an LLM writing JSON by hand with no parametric knobs a human can sweep.

## Techniques worth stealing

- **Compile a closed DSL; never let the LLM emit three.js.** AC's spec → engine → GLB with
  engine-side BLOCK/warn/info registers (`checks.js`, `gates.json`). For us: a hard-surface DSL
  (box/slab/prism/lathe/extrude-with-holes + `attach`, `stack`, `inset`, `array`) compiled by a
  Node engine to glTF; the same compiler runs headless under `tools/BlindLoop`.
- **Relational placement with fixed-point resolution** (`relative.js`): express every part as
  `{from, side/up/fwd | dir+len, ground}` so scale logic is inherited. Extend to hard surface:
  `{on: "roof", face: "+y", inset: 0.1}` snapping to a host face — a direct answer to failure 1.
- **Declared joins that the engine verifies** (`part_seat` insert/extrude/snap/place,
  `checks.js:795-845`; `touch` pairs, :745). Port as `attach: {host, mode: embed|flush|rest,
  minOverlap}` and make undeclared free-floating a BLOCK, not a warn (I2T's warning tier is
  where the floating charm slipped through).
- **Corrective messages that state the move in units** ("Move joint X about 0.032 m toward
  [0.1,-0.9,0]", `checks.js:376-389`). Cheapest possible repair loop: the LLM applies a delta
  instead of re-deriving geometry.
- **Geometry-side silhouette and metrics, no browser** (`outline.py`: same camera math as the
  renderer, IoU-verified). For our loop: rasterise our own iso camera in numpy for IoU-vs-prev,
  thinnest-feature, protrusion count; use the GPU only for the judged image.
- **`thinnest_px48` promoted to a BLOCK.** Compute min feature width in *target-render pixels*
  at the BlindLoop capture resolution and refuse below N px; also a world-space floor per
  category (rail ≥ 3 cm, wall ≥ 15 cm at 1 unit = 1 m). Neither repo does this; it is the
  highest-value gap.
- **Ray-parity penetration + seam overlap band on the compiled mesh** (`pairwise_penetration.py`,
  `geometry_integrity.py` 0.02-0.05). Run inside the compiler on every adjacent pair, with
  `allowedPairs` for intended contact, deterministic fixed directions.
- **Block/advise × allocate/verify tagging** (`gates.json`) and the rule "advice never stops a
  build". Keeps the loop from rebuilding over taste.
- **Two opposite poles per round, promote the winner** (`01_LOW.md:354-400`, `round.py`
  `--promote`). Maps directly onto BlindLoop's "BASELINE is a candidate" with two candidates.
- **Stall detection by measurement** (`roundcheck.py` reading `iou_vs_prev` to tell a restart
  from a nudge) — matches our stall rule K=2 but adds a metric that proves the retry differed.
- **Judge hygiene from AC's reader traps**: shuffled labels, a canary with a known answer,
  a binding question the judge must answer from the image. Fold into BlindLoop's judge prompt.
- **From I2T:** `attachment_anchor`'s ANCHOR_NOT_ROOT rule; `check_part_coverage` ("proves you
  built what you specified") as a structure gate; interior-difference banding — never let a
  silhouette metric be the loop's objective; turntable capture at 0/90/180/270 as a regression
  check; the `unmeasuredAttachments`/`sampledVertexCount` habit (a gate reports what it did not
  look at).
- **Embed the source spec in the GLB** (`asset.extras.source_spec`, AC CHANGELOG) so any
  round can re-open and re-compile; supports determinism-from-seed auditing.

## Dead ends

- **Pixel-similarity judges as the primary loop signal** (I2T Divine Eye). Repo's own evidence:
  face deleted scored identically; thin details vanish at 64 px; 2-D pass reads as a toy in 3/4
  view. Use pixels only for the blind visual verdict, geometry for correctness.
- **Attachment as spec metadata** (I2T `validate_attachment`, warning-only). Fields that are not
  measured against geometry do not prevent floating parts; two shipped defects prove it.
- **Isolated-part blind reads** (AC deleted them: "a crown reads as 'a blob'", `02_MID.md:29`).
- **VLM colour/eye-flow reads** — AC replaced with OKLab arithmetic (`value_order`,
  `contrast_adjacent`); numbers you already have should not cost a model call.
- **Free-transform component trees with absolute world dimensions** (I2T `dimensions` +
  `transform.position`): the source of scale-logic errors; nothing inherits.
- **Eight serial locked passes with an in-transcript judge** (I2T): 80k-180k tokens/object by
  the repo's estimate; the human modeller waits minutes per round. Passes should be data
  (the DSL) not conversation turns.
- **Splitting the builder across subagents** (AC README "Honesty about limits": costs more on
  tokens, wall clock and turns; re-derivation is the cause). One builder, many cheap readers.
- **Zero-thickness `open-shell` surfaces and plane cards** (I2T) — incompatible with our
  "nothing paper-thin" priority; I2T itself rejects plane cards for hair because it emits no
  alpha textures.
- **Creature-shaped legality for buildings.** AC's `balance`, `root_containment`, chains and
  mirror twins do not map to facades; `"build":"rigid"` only disables two style blocks. The
  *checker pattern* transfers; the check set does not.

## Open questions

- Does a hard-surface DSL need CSG (window holes, arched door) or is "extrude profile with
  holes + inset boxes" enough for the target look? I2T has `buildExtrudeGeometry(... holes)`
  (`generate_threejs_factory.py:2657`); AC has none. UNVERIFIED which wins on tri budget.
- Minimum feature floor: in render pixels at BlindLoop capture size, in world cm, or both?
  Owner-ratified number needed (validation-zone gate).
- Is a blind *LLM* reader (AC) or a deterministic silhouette IoU (I2T) the right BlindLoop judge
  for buildings, where identity is "reads as a tenement" rather than "matches this photo"?
  AC's scored-rank rule is text-target friendly; I2T's judge needs a reference image.
- Can AC's `outline.py` camera math be reused verbatim for an isometric orthographic capture, or
  does BlindLoop's fixed camera require a new projection (AC is 30° perspective)?
- I2T's Playwright adapter contract (`__IMG2THREEJS_READY__` + `setCamera`) vs our BlindLoop
  capture URL + manifest — worth adopting the ready-flag/rAF-settle pattern; unverified whether
  BlindLoop's current capture already waits for a settle frame.
- Neither repo measures wall-clock per round for hard-surface objects; AC's 1.4 s is a creature
  LOW round without colour. UNVERIFIED that a box/extrude compiler + numpy silhouette stays
  under ~2 s at 8k tris.
