# 09 — LiteReality-Agent (research note, 2026-09-12)

Repo: https://github.com/LiteReality/LiteReality-Agent (Apache-2.0, v0.0.1, created 2026-08-01,
pushed 2026-09-11, ~430 stars, 31 MB). Site: https://litereality.github.io/agent/ (blog-post URL
returned 404 at fetch time). "A technical report is coming" — NO paper for the Agent yet. The
parent LiteReality (NeurIPS 2025, https://arxiv.org/abs/2507.02861) is retrieval-based scene
reconstruction; the Agent repo does NOT do asset retrieval (see 1c).

## 1. What it does end to end

**Input → output.** RGB-D scan from the "LiteReality Scanner" iPhone app (ARKit frames +
RoomPlan `room.usdz`) → articulated, physics-tagged room: `Room.py` manifest, `Room.glb`
(baked textures), Blender scene, URDF/MJCF for MuJoCo, a three.js "walk" viewer
(`room_ops/walk/`). Target user is robotics sim, not games.
https://raw.githubusercontent.com/LiteReality/LiteReality-Agent/main/ARCHITECTURE.md

**Stages** (`pipeline/runner.py`, resumable via `run/<scene>/.litereality/pipeline.json`):
1. `scene_init` (deterministic): ingest RoomPlan boxes + walls → `layout/` repair → per-object
   reference-crop selection (GroundingDINO, DINOv2) → `reconstruct/` (per-object 3D) → seed room.
2. `realism_authoring` (agentic; Claude Code or Codex CLI as harness, `agent/providers/`):
   the agent edits `Room.py` and calls tools until renders match photos.
3. Optional polish (per-object refinement, materials), model-driven quality pass, simulate.

**Models/tools called.** TRELLIS.2 image→3D (Modal or ≥24 GB local GPU), GroundingDINO,
DINOv2, a VLM for `critic`/`completeness` (default `claude-opus-5`, env-overridable), Claude
sonnet via `claude` CLI subprocess for the optional layout agent, Blender 5.x for build +
bake + render, MuJoCo for physics gates, Poly Haven for PBR textures, OpenAI/Gemini image
API (~$1/scene). Python 3.10–3.12; deps: trimesh, open3d, python-fcl, coacd, mujoco,
networkx, opencv, fastapi, anthropic, openai, google-genai, claude-agent-sdk.

**Geometry representation — three routes, no retrieval:**
- (a) **Procedural, LLM-written Blender Python** for "box/slab/revolve" categories (tables,
  cabinets, appliances). An agent runs the `image-to-articulated-glb` skill: reference crop +
  hand-authored per-category spec (`category_specs.py`: geometry text, materials,
  REVOLUTE/PRISMATIC joints with axis/limits) + real dims from RoomPlan → writes
  `build_<stem>.py` against `blender_lib.py` (add_box/add_cylinder/add_lathe/add_arc_panel/
  add_rounded_box/build_carcass/build_drawer, `parent_keep_world`, `set_articulation`) →
  GLB → self-contained `object.py` + `object.md`.
  https://raw.githubusercontent.com/LiteReality/LiteReality-Agent/main/src/litereality_agent/models/object_generation/articulated-glb-agent/.claude/skills/image-to-articulated-glb/SKILL.md
- (b) **TRELLIS mesh gen** for organic categories (chairs, sofas, plants); a policy override
  forces chairs/sofas to TRELLIS regardless of the VLM router (`classify_complexity.py`,
  JSON `{route, complexity, is_organic, primitive_buildable, reason, primitive_plan}`).
- (c) Room shell (walls/floor/openings) built procedurally from RoomPlan polygons.
  Retrieval from an artist asset DB exists only in the parent LiteReality paper (UNVERIFIED
  for the Agent repo — no asset-library code found in the tree).

**Placement/arrangement.** Not generative: it starts from scanned oriented boxes and repairs
them. `layout/repair.py` = beam search (beam 3, ≤14 rounds) over ordered actions
drop→snap→dewrap→slide→separate→shrink, lexicographic score
`(violations, anchors_broken, penetration, displacement)`, strict-improvement acceptance,
"never worse than input"; `REVIEW_SHIFT=0.22 m` marks moves as claims-not-corrections;
`SHRINK_MAX=0.35`. Optional LLM layout agent answers `{action: resize|translate|attach|none,
size, center, walls, confidence, why}`, accepted only if bounded (±60 % dims, ±0.6 m) AND
violations drop AND no anchor breaks.
https://raw.githubusercontent.com/LiteReality/LiteReality-Agent/main/src/litereality_agent/pipeline/scene_init/layout/README.md

**Checks it runs.**
- Object level, `probe_glb.py` (hard): node connectivity from scene root; joint axis
  |a|<1e-6 fails; degenerate limits fail; moving part must open toward canonical front
  (`OPEN_TOL=0.02 m`). Soft: rest interpenetration >10 % of smaller part (hardware <3 % of
  max part exempt), open-pose clearance, isolated part (`TOL=0.005 m`, AABB gap).
- Object level, `mesh_qc/checks.py` (TRELLIS output): extreme plane (flat area ≥0.15 and
  footprint ≥0.46 → fail), low support band, ≥20 small components → fail (≥8 warn), bbox
  aspect ≥7.5 warn, squat blob (height/footprint <0.68 fail), origin grounding |min_y|>0.025.
- VLM `completeness_check.py`: reference vs 3 renders, "every SALIENT feature ... COUNT and
  rough placement ... IGNORE lighting, exact colour", JSON `{pass, missing[], notes}`.
- Physics gate `sim/checks.py`: drop (0.05 m, 3 s, rest speed 0.05, overlap ≤0.005, drift
  ≤0.02), per-joint release (self-collision 0.01 m, vel ≤25), tilt to 60° in 2° steps vs
  declared friction (±12°).
- Room level, `room_qc/checks.py` + `doc/QC/*`: contact from real triangles, penetration
  depth from CoACD convex decomposition, bbox only for chair/table pairs; `object_clash`
  (SAT, pen >0.08 m, z-overlap >0.05), `wall_clash` (thickness/2+0.02), `outside_room`
  (0.10 m), `FLOAT_TOL=0.08`, `SUNK_TOL=0.05`; support graph (highest top face under
  footprint, else floor, else wall anchor; snap in Z only, ≤0.15 m, propagates through
  stacks; `support_cycle`, `orphan_anchor`). Loop: detect→nudge→detect until clean or
  provably stuck.
- Authoring loop: `render` returns render|photo pairs from identical ARKit poses (+ ortho
  rectified wall stitches, `grid` metric ruler); `critic` VLM grades against ONE stated
  goal, "Be strict: near-misses fail", `{pass, score 0-10, issues[]}`, repeated verdicts
  merged conservatively (all must pass, min score). "render produces the pair; it doesn't
  judge it." Cost/time: "$1–3 and 3–8 minutes per image" per object (README claim,
  UNVERIFIED by us).

## 2. Usable for us

- **Category spec injected into the builder prompt** (`category_specs.py`): per-category
  part vocabulary + canonical frame (Z-up, front −Y, base at Z=0, centred). Analogue: a
  `specs/<class>.md` per hard-surface class (tenement, vehicle, street prop) handed to
  BUILDER A/B/C with the DSL doc. Cheap; targets failure mode 1 (wrong place/scale).
- **Probe hard/soft split with numeric constants** maps onto V0–V10: connectivity from
  root, isolated-part AABB gap 0.005 m, rest-overlap >10 % with a small-hardware exemption
  (<3 % of max part volume). The exemption is the useful bit: our min-feature-size and
  overlap validators need the same carve-out or they reject bolts, rails, vents.
- **Repair as bounded beam search, lexicographic score, "never worse than input"** — the
  BASELINE-always-competes contract at validator level. A mechanical REPAIR pass
  (snap-to-support, separate along MTV, shrink ≤35 %) before any Astra REPAIR seat; Astra
  only sees what arithmetic could not fix.
- **Support graph** (highest top face under footprint → floor → wall anchor; Z-only snap
  ≤0.15 m; cycle detection) is a ready algorithm for "nothing floating" when a DSL
  attachment is missing or wrong; `support_cycle` is a bug class we do not test.
- **Completeness prompt** as JUDGE/LISTER template: count + placement of salient parts,
  ignore lighting/colour/resolution — matches the owner ruling that TARGET is style, not
  tracing. Its `missing[]` is an items.json seed.
- **Critic contract**: one goal per grade, strict, min-merge across repeats. Our 3 judge
  runs majority-vote; min-merge is a stricter alternative worth one ledger trial.
- **Render staleness invariant**: "any `object.py` newer than its packed GLB is rebuilt"
  before render — add the same mtime guard to our capture so a stale build is never judged.
- **Self-contained `object.py`** (helpers inlined by `make_selfcontained.py`) = portable
  rebuild recipe; ours is spec.json + pinned compiler hash in the manifest.
- **Materials**: LAB-space recolour keeping each pixel's offset from the texture mean
  (`doc/Tools/fetch_material.md`), and "a procedural material with the correct colour and
  roughness beats a confidently wrong texture". We are flat vertex colour, but LAB shift is
  the right way to move a palette family without flattening shading later.
- **Orientation gate**: front-view render must show FRONT, else rotate 180° about Z — a
  trivial capture check (our isometric camera hides back/front swaps otherwise).
- Datasets: https://github.com/LiteReality/example-scans.git (indoor rooms, robotics). No
  hard-surface exterior/vehicle data. No benchmark numbers anywhere in the repo.

## 3. Not applicable, and why

- Input is a metric RGB-D scan with RoomPlan boxes; we start from a style image with no
  metres. Their layout solver repairs measured boxes, it never invents a layout.
- LLM emits free-form Blender Python and runs Blender per iteration (minutes, $1–3 per
  object) — the slow loop the brief rejects. Our DSL + JS compiler stays.
- TRELLIS route (organic, uneditable, "at whatever dimensions it felt like") contradicts
  low-poly flat-colour, seed-deterministic, tri-budgeted output.
- Articulation, mass/inertia, MuJoCo drop/tilt gates, URDF/MJCF export: robotics-only.
- Photo-matched render|photo pairs need camera poses; we have one reference image.
- Poly Haven PBR textures vs our one-material vertex colour.
- No tri-budget, min-thickness, or silhouette-readability checks in the tree — their
  "paper-thin" failure mode is unaddressed (no such constant surfaced in probe/validate/
  mesh_qc; `blender_lib` internals UNVERIFIED).
- Determinism: pipeline is "resumable", not seed-deterministic; agent output varies per run.

## 4. Licence and dependency weight

Apache-2.0 (LICENSE + pyproject). Heavy: Blender 5.x, MuJoCo, open3d, CoACD, python-fcl,
torch extras, Modal or a 24 GB GPU for TRELLIS/DINO, paid VLM + image API, Claude/Codex
CLI on PATH. Nothing imports into a Node pipeline as-is; lift algorithms and constants
(probe thresholds, support-graph rules, repair action order/score), not code. Only
`validate_glb.py` is pure-stdlib and trivially portable.
