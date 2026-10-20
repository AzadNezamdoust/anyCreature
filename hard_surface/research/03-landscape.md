# 03 — Landscape survey: LLM/AI routes to hard-surface low-poly assets

Scope: routes beyond `anyCreature` / `img2threejs`. Every non-obvious claim carries a URL.
Claims I could not verify from a primary source are marked **UNVERIFIED**.

---

## Findings

### A. Code-generation routes (LLM writes a program that builds geometry)

- **The benchmark that matches our exact failure list exists.** 3DCodeBench (arXiv 2606.01057)
  benchmarks VLM agents writing **Blender 5.0 Python** for procedural 3D. Its headline failure
  finding is verbatim our failure mode #3: models "frequently produce disconnected parts and
  incorrect structural alignments", and "disconnected or floating 3D geometric components" appear
  even in scripts that execute and render fine. https://arxiv.org/abs/2606.01057
- **3DCodeBench numbers** (Table A.1, SigLIP-2 conditional / executability): GPT-5.5 0.834 / 0.906;
  Gemini 3.1 Pro 0.824; Claude Opus 4.7 0.814 / **0.910** (best executability). Metrics =
  Executability, SigLIP-2 view similarity (their strongest human-preference predictor), DINOv3,
  Chamfer, Uni3D. **Multi-turn error feedback is worth +0.128 aggregate SigLIP-2** — i.e. a
  compile/execute/render feedback loop is the single largest cheap win. https://arxiv.org/html/2606.01057v1
- **P3D-Bench (arXiv 2606.11152) directly compares our candidate target languages** — JSON,
  OpenSCAD, CadQuery, Three.js — under one protocol that executes and renders every output.
  GPT-5.5, Image-to-3D (Geo / Topo / Judge / Valid%):
  | Format | Geo | **Topo** | Judge | Valid |
  |---|---|---|---|---|
  | OpenSCAD | 0.567 | **1.000** | 0.592 | 100% |
  | Three.js | 0.556 | **0.828** | 0.569 | 100% |
  | CadQuery | 0.524 | 0.914 | 0.526 | 93.7% |
  Conclusion quoted: "OpenSCAD is the strongest format… no clear weakness". Three.js is fine on
  validity but loses on topology ("triangulated mesh limitations"). https://arxiv.org/html/2606.11152v1
- **P3D-Bench also quantifies failure modes #1 and #2.** Semantic alignment J-Sem ≈ 0.80 but
  **geometric alignment J-Geo ≈ 0.35** — models know *what* the object is and get *dimensions*
  wrong. `PartMatchF1 ≈ 0.50`: only half the parts match at all. Assembly-3D (many parts, all
  authored by the model) is the hardest of the three tasks. Same source.
- **LL3M (arXiv 2508.08228) is the best-documented bpy agent.** 6 agents (planner/retrieval/coder/
  critic/verifier/user-proxy), readable `bpy`, critic renders **5 views** per pass. RAG over **1,729
  Blender 4.4 doc files** buys **5.86× more complex Blender operations** and **26% fewer execution
  errors** (2.43 vs 3.29). Wall-clock is fatal for us: **~4 min initial + ~6 min auto-refine per
  asset**, 38 s per user edit, only 59% of edits land in one prompt. Stated limits: "some geometry
  details remain disconnected after auto-refinement"; "VLMs may still struggle to accurately
  identify spatial artifacts." https://arxiv.org/html/2508.08228v1
- **SceneCraft (ICML'24, arXiv 2403.01248)**: scene-graph blueprint → *numerical constraints* → bpy
  → GPT-V critique on renders → library learning that promotes recurring functions into a reusable
  library. Constraint-then-code ordering is the transferable idea. https://arxiv.org/abs/2403.01248
- **3D-GPT (arXiv 2310.12945)** writes no geometry code — three agents *extract parameter values*
  and drive **Infinigen** generators. The LLM never places a vertex. https://arxiv.org/abs/2310.12945
- **ShapeCraft (NeurIPS'25, arXiv 2510.17603)**: Graph-based Procedural Shape (GPS) — a graph of
  sub-shapes before any code. No public numbers. https://arxiv.org/pdf/2510.17603
- **blender-mcp (ahujasid)**: JSON-over-TCP into a live Blender (3.0+) with bridges to Poly Haven /
  Rodin / Hunyuan3D. A *transport*, not a modeling method. https://github.com/ahujasid/blender-mcp
- **LLaMA-Mesh (NVIDIA, arXiv 2411.09595)**: OBJ vertex/face lines as plain text, **no vocabulary
  expansion**. Quantised coords + sequence length cap face counts — fine for blob-scale objects,
  not a 3-storey facade with a fire escape. https://github.com/nv-tlabs/LLaMA-Mesh
- **MeshAnything / v2 (arXiv 2406.10163)**: VQ-VAE + shape-conditioned decoder-only transformer,
  converts *any* dense shape into an **artist-created mesh with "hundreds of times fewer faces"** —
  the only credible automatic dense→low-poly retopo in the literature.
  https://buaacyw.github.io/mesh-anything/
- **MeshFIM (arXiv 2605.08744)** adds *local* editing: fill-in-the-middle over 12-tokens-per-face
  quad blocks, target regions up to **1200 faces**, boundary vertex match **99.75%** — a per-part
  regeneration primitive, exactly BlindLoop's "one ITEM per round". https://arxiv.org/html/2605.08744
- **CAD-Recode (ICCV'25, arXiv 2412.14042)** is the mesh→code bridge: point cloud → **CadQuery
  Python** via Qwen2-1.5B + one linear point projector, **10× lower mean Chamfer** than prior SOTA
  on DeepCAD/Fusion360, output editable by an off-the-shelf LLM. https://github.com/filaPro/cad-recode
- **CAD export paths are real.** build123d `export_gltf(linear_deflection, angular_deflection)`;
  CadQuery `Assembly.export()` writes glTF with per-component `cq.Color` + transforms.
  https://build123d.readthedocs.io/en/latest/import_export.html ·
  https://cadquery.readthedocs.io/en/latest/importexport.html
- **OpenSCAD's colour story is the catch.** It wins P3D-Bench on topology but only got colour export
  (via 3MF) in 2025 dev snapshots and it is still buggy — colours land as separate grey objects
  (openscad#5849, #5994). Its Manifold backend does support glTF I/O.
  https://github.com/openscad/openscad/issues/5849 ·
  https://github.com/elalish/manifold/wiki/Manifold-Library
- **Zoo (ex-KittyCAD)**: `KCL` parametric DSL + closed ML-ephant text-to-CAD API; open-source UI
  only. Mechanical-CAD aesthetic, no vertex colours. https://docs.zoo.dev/blog/introducing-text-to-cad

### B. Generative models as **oracle / reference**, not final asset

- **TRELLIS (MIT licence)** — SLAT structured latents, decodes to Gaussians/RF/mesh. Permissive
  licence is the differentiator vs Hunyuan3D 2.0, which carries regional usage restrictions.
  https://github.com/microsoft/TRELLIS
- **TRELLIS.2** — "O-Voxel" field-free sparse voxels + Flexible Dual Grids, explicitly
  "**preserving sharp edges**", 4B params, PBR, **3 s @512³ → 60 s @1536³ on an H100**.
  Sharp-edge preservation is what makes it usable as a hard-surface silhouette oracle.
  https://microsoft.github.io/TRELLIS.2/
- **Hunyuan3D-2.1**: 10 GB VRAM shape, 21 GB texture, **29 GB combined** — above a consumer card
  for the full pipeline. https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- **Tripo / Meshy**: both **$0.01/credit**. Tripo Pro $19.9/mo ≈ 3,000 credits; Meshy Pro $20/mo
  ≈ 1,000 credits with full commercial rights. **Tripo's free tier output is CC BY 4.0 and
  non-commercial** — a licensing trap if a free-tier mesh ever ships. Tripo v3.0 ≈ 100 s/asset vs
  v2.5 ≈ 25–30 s. https://www.sloyd.ai/blog/3d-ai-price-comparison · https://tripo3ds.com/pricing/
- **Sloyd is the only genuinely parametric vendor**: handcrafted parametric templates with sliders,
  **target polycount + quad output**, "often under 5K triangles", API/SDK on the Pro tier, from
  $15/mo with commercial licence. Closest external analogue to what we want to build.
  https://www.sloyd.ai/
- **Kaedim is humans**: mandatory in-house artist QA on every asset, sales-only, ~$300/mo entry.
  Not automatable. https://knowara.com/ai-tools/image/kaedim-review/
- **Every neural quad-remesher gives evenly distributed quads**, not intentional loops — fine as a
  silhouette reference, wrong as a shipped flat-shaded asset.
  https://app.cinevva.com/guides/ai-3d-model-generators
- **Answer to "can we re-express an oracle mesh as code?"**: proven in the CAD domain (CAD-Recode,
  above). **No published equivalent for cartoon/game low-poly** — **UNVERIFIED** whether
  CAD-Recode-style program induction survives non-CSG shapes like a fire escape or an awning.

### C. Hybrid — LLM selects and parameterises procedural generators

- **Infinigen Indoors (arXiv 2406.11824, BSD)** is the strongest prior art for route C:
  **79 randomized procedural object generators**, a **constraint DSL + solver** for composition,
  human-overridable parameters, exports OBJ/FBX/USD. Generators are built "from functional
  requirements — such as the need for a chair to have a seat at an appropriate height" — i.e. the
  correctness we want is baked into the generator, not asked of the LLM.
  https://arxiv.org/abs/2406.11824
- **3D-GPT's whole result is that this works**: the LLM only fills parameters into Infinigen and
  gets reliable geometry — the strongest available evidence that parameterisation beats raw
  code-gen on correctness. Caveat: no head-to-head numeric ablation vs raw code-gen in that paper
  (**UNVERIFIED** as a *quantified* margin). https://arxiv.org/abs/2310.12945
- **CGA shape grammar (Müller et al., SIGGRAPH 2006)** is the canonical building/facade grammar —
  split rules over facades, repeat/subdivide, context-sensitive rules — "extensive architectural
  models for computer games… at low cost". Our reference target (3 adjoining tenement facades,
  parapets, fire escape, balconies) is a textbook CGA subject.
  https://dl.acm.org/doi/10.1145/1141911.1141931
- **Constraint-expressive IR (arXiv 2507.18625)** proposes an IR capturing **contact, alignment and
  containment** between objects, solved before code emission. Exact numbers not extractable from
  the PDF (**UNVERIFIED**), but the constraint vocabulary is directly reusable.
  https://arxiv.org/pdf/2507.18625

### D. Iteration-speed tooling

- **Headless Chrome uses a software rasteriser (SwiftShader) by default** — WebGL runs but slowly;
  `--use-gl=egl` / `--use-angle` restores GPU. Playwright tests are "much slower" without it.
  https://michelkraemer.com/enable-gpu-for-slow-playwright-tests-in-headless-mode/
- **Blender EEVEE does not render headless on Windows or macOS** (Linux only, and only since 3.4).
  On Windows `-b` is Cycles-or-nothing. This kills "fast flat render via EEVEE" on the owner's
  Win 11 box. https://medium.com/@jjziets/how-to-rendering-blender-eevee-on-a-headless-system-d3054ced8ec
- **Blender CLI startup dominates short renders** — for seconds-long frames the process
  startup/teardown costs more than the render; keeping one Blender process alive between frames is
  the documented fix. https://superlumin.al/eevee-render-farm
- **Determinism from an LLM seed does not exist by default.** 1,000 completions at temperature 0
  from Qwen3-235B produced **80 distinct outputs**, diverging at token 103, because kernels are not
  batch-invariant; bitwise repeatability needs batch-invariant RMSNorm/matmul/attention kernels —
  which no hosted API exposes. Determinism must therefore live in *our* code path (seeded
  generator + cached program text), never in the model call.
  https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/

---

## Techniques worth stealing (concrete, mapped to our pipeline)

1. **Constraint IR before code (SceneCraft + 2507.18625 + Infinigen's solver).** LLM emits a *part
   graph* first — parts with `contact`, `align`, `inside`, `on_top_of`, `flush_with` relations —
   and **our** deterministic solver computes transforms. The LLM never writes a world-space number.
   The only technique here that cures failure modes #1/#3 by construction, not by critique.
2. **Anchor/socket parts, not free primitives (Infinigen + CGA).** A small hard-surface library
   (wall panel, parapet, stair flight, railing, vent, pipe, awning, stoop) where each part declares
   named sockets and legal mates, so assembly becomes socket-matching — P3D-Bench shows free-form
   assembly is where models collapse (PartMatchF1 ≈ 0.50).
3. **Validator-in-the-loop with error text fed back (3DCodeBench: +0.128 SigLIP-2).** Assert before
   any render: every part touches ≥1 other (no floating), wall thickness ≥ t_min (no paper-thin),
   feature ≥ k px at the BlindLoop camera (no sub-pixel slats), bbox ratios in declared ranges.
   Reject and re-prompt with the failing assertion text.
4. **Minimum-feature test in *screen* space, not world space.** Failure mode #2 is a
   render-resolution property: project each feature under the frozen BlindLoop camera, reject below
   ~3 px. Cheap, deterministic, no VLM needed.
5. **Library learning (SceneCraft).** Every accepted BlindLoop winner promotes its part function
   into a versioned parts library, so the loop improves monotonically instead of re-deriving stairs.
6. **CSG solid as a correctness oracle even if we ship triangles (P3D-Bench Topo 1.000).** Emit the
   same part graph to OpenSCAD/Manifold as a boolean union; if the union is a single watertight
   manifold with the expected genus, no part is floating — by definition. Run it as a gate, keep
   three.js as the shipping/render path.
7. **RAG over the API surface (LL3M: 5.86× ops, −26% errors).** If we expose a custom DSL, ship its
   full spec + worked examples in-context; the same effect applies and is cheaper for a small DSL
   than for all of `bpy`.
8. **Per-part regeneration (MeshFIM).** BlindLoop's "one ITEM per round" maps onto regenerating one
   part with its neighbours frozen as context. Even without the MeshFIM model, adopt the *protocol*.
9. **Oracle-as-TARGET only (TRELLIS.2 sharp-edge preservation, 3 s @512³).** Use a generative model
   to produce the frozen reference render when a hand-drawn TARGET is missing. Never ship it.
10. **Persistent renderer process + parallel worktrees.** One long-lived headless Chromium with GPU
    flags, page-per-candidate; parallel candidate builds map onto BlindLoop's existing worktrees.
    Avoids the Blender-startup tax entirely by not using Blender in the loop.

---

## Ranked routes

Scores 1–5 (5 = best). Correctness = attachment/scale/min-feature. Style = flat-colour cartoon.

| # | Route | Correct | Style | Speed | Determ. | Cost |
|---|---|---|---|---|---|---|
| 1 | **LLM → constrained part-graph DSL → our solver → three.js + glTF** | 5 | 5 | 5 | 5 | 5 |
| 2 | **LLM → CSG/OpenSCAD-Manifold solid (gate) → tessellate** | 4 | 3 | 4 | 5 | 5 |
| 3 | **LLM parameterises a socketed part library / CGA facade grammar** | 5 | 4 | 5 | 5 | 4 |
| 4 | LLM → raw three.js (the two source repos) | 2 | 4 | 5 | 2 | 5 |
| 5 | LLM → CadQuery/build123d → glTF | 3 | 2 | 3 | 5 | 5 |
| 6 | bpy agent (LL3M / blender-mcp) | 3 | 4 | 1 | 2 | 4 |
| 7 | Generative oracle as **reference image** (TRELLIS.2/Tripo) | n/a | 4 | 3 | 3 | 3 |
| 8 | Mesh-token models (LLaMA-Mesh / MeshAnything / MeshFIM) | 2 | 3 | 2 | 2 | 3 |
| 9 | Generative model as **final asset** (Tripo/Meshy/Hunyuan/Rodin) | 2 | 2 | 2 | 1 | 2 |
| 10 | Kaedim (human QA) | 5 | 4 | 1 | 5 | 1 |

**Top 3, with reasons**

1. **Constrained part-graph DSL compiled to three.js.** It is the only route where all four owner
   failure modes are structurally impossible rather than statistically unlikely: the LLM emits
   relations, our solver emits transforms, a validator gates thickness/attachment/screen-size, and
   the DSL text is the deterministic seed artifact. Renders in a browser in ms, exports via
   `GLTFExporter`, plugs into BlindLoop as a URL + manifest with no new runtime. P3D-Bench's
   Three.js topo weakness (0.828) is a property of *free-form* three.js, not of a compiler that
   only ever emits closed boxes and extrusions.
2. **CSG solid as a correctness gate (OpenSCAD/Manifold), not as the shipping format.** Best
   topology score of any format measured (1.000, P3D-Bench) and a boolean union is a *proof* of
   attachment. Its weaknesses — colour export bugs, triangulation quality — do not matter if it
   only ever answers "is this one connected solid, and is everything thicker than t_min?".
3. **LLM-parameterised socketed part library / facade grammar.** The Infinigen + 3D-GPT result
   (LLM fills parameters, generator guarantees geometry) plus CGA's 20-year track record on exactly
   our subject (tenement facades) make this the highest-correctness route per unit of LLM
   competence. Ranked third only because it needs the most upfront authoring; it should be grown
   *inside* route 1 via SceneCraft-style library learning rather than built as a separate track.

---

## Dead ends (and why)

- **bpy agents in the inner loop (LL3M, blender-mcp, 3DCodeBench setups).** ~10 min per asset
  (LL3M) against a priority of "seconds, not minutes"; Blender's CLI startup tax; and **EEVEE
  cannot render headless on Windows**. Keep Blender as an offline export/bake tool only.
- **Mesh-token LLMs as our generator (LLaMA-Mesh, MeshAnything, MeshFIM).** Quantised coords and
  sequence-length caps (MeshFIM tops out at ~1200-face regions) cannot express an 8k-tri building,
  and the output is opaque triangle soup with no parameters to edit. Revisit MeshFIM only if we
  ever need automatic retopo of an oracle mesh.
- **Any hosted generative model as the shipped asset.** Dense non-planar topology, baked textures
  instead of flat vertex colours, evenly-distributed quads on remesh, per-asset cost, 25–100 s
  latency, a **CC BY 4.0 non-commercial trap on Tripo's free tier**, and no determinism.
- **Kaedim.** Human artists in the loop, sales-gated contracts. Cannot sit in an unattended loop.
- **Zoo / KCL and pure mechanical CAD (CadQuery alone).** Right for brackets, wrong for a cartoon
  tenement: no vertex-colour story, filleted mechanical aesthetic, and CadQuery scored lowest of
  the four formats on validity (93.7%), 55% of its failures at parameter specification.
- **Relying on temperature 0 for determinism.** Empirically false (80 distinct outputs from 1,000
  temp-0 samples). Determinism must come from caching the emitted program text and seeding our own
  generator.
- **VLM-only critique as the correctness gate.** LL3M: VLMs "struggle to accurately identify spatial
  artifacts", geometry stays disconnected after auto-refinement. VLM for style, assertions for
  geometry.

---

## Open questions

1. Does a boolean-union manifold check actually catch our floating-part cases, or do LLM outputs
   typically produce *touching-but-not-overlapping* parts that union into a valid-but-disconnected
   compound? Needs a 20-case empirical check against `manifold` — **UNVERIFIED**.
2. What is our real headless three.js capture latency on this Win 11 box with GPU flags, page
   reused across candidates? Assumed sub-second; **UNVERIFIED**, must be measured before the DSL
   design freezes on it.
3. Can CAD-Recode-style program induction be retrained/prompted to emit *our* part-graph DSL from a
   TRELLIS.2 oracle mesh, closing the loop oracle→code? No prior art outside CSG.
4. Is a Sloyd API subscription ($15/mo, <5k tris, quads, polycount targets) a cheaper source of
   baseline hard-surface parts than authoring our own library? Depends on whether its API exposes
   the parametric templates or only the generative endpoints.
5. Does 3DCodeBench's +0.128 error-feedback gain hold when the feedback is *geometric assertions*
   rather than Python tracebacks? Their gain is measured on execution errors only.
6. Licensing check needed before any TRELLIS.2 / Hunyuan3D-2.1 use: TRELLIS core is MIT, but the
   TRELLIS.2 weights licence and Hunyuan3D-2.1's territorial restrictions were not readable from
   the repo pages — **UNVERIFIED**.
