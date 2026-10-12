# LLM-authored 3D geometry: methods, representations, evaluation, failure modes

Note: search-snippet based (about 9 searches, few full-page fetches). Items marked "secondary" were not verified against the primary paper.

## Which methods exist where an LLM writes geometry itself?

### Takeaway
Three families: (1) mesh as text or tokens (LLaMA-Mesh, MeshGPT), (2) code that builds geometry (Blender bpy, CadQuery, three.js, SVG/TikZ), (3) parametric or procedural parameter extraction (3D-GPT). Code-based approaches dominate for general-purpose LLMs.

### Cited Findings
- LLaMA-Mesh fine-tunes a text LLM to emit OBJ text (v/f lines) with vertex coordinates quantized to integers to cut token count, trained on Objaverse text-3D pairs plus interleaved dialogue. It claims quality on par with from-scratch mesh models while keeping text ability. Pretrained LLMs could already emit crude OBJ with no examples. — [arXiv 2411.09595](https://arxiv.org/html/2411.09595v1); [NVIDIA page](https://research.nvidia.com/labs/toronto-ai/LLaMA-Mesh)
- MeshGPT treats a mesh as a triangle sequence, with a VQ-VAE learned geometric vocabulary and a decoder-only transformer. It reports a 9% shape-coverage gain and a 30-point FID gain on ShapeNet. It is a custom token model, not a general LLM. — [MeshGPT](https://arxiv.org/pdf/2311.15475)
- LL3M (UChicago, Aug 2025) uses multiple LLM agents (planner, retrieval over Blender docs "BlenderRAG", coder, debugger, critic) to write Blender Python. It has initial generation, automatic visual self-critique, and user-guided phases. The output code is editable. The paper used Claude Sonnet 3.7, which has since been retired. — [arXiv 2508.08228](https://arxiv.org/abs/2508.08228); [GitHub](https://github.com/threedle/ll3m)
- 3D-GPT uses a task-dispatch agent, a conceptualization agent and a modeling agent. They expand text and extract parameters that drive a procedural generator (Blender/Infinigen). — [arXiv 2310.12945](https://arxiv.org/html/2310.12945v2)
- SceneCraft (ICML 2024) builds a scene graph, turns relations into numerical layout constraints in Blender scripts, refines with a VLM looking at renders, and learns a reusable code library. It handles scenes of up to about 100 assets. — [PMLR](https://proceedings.mlr.press/v235/hu24g.html)
- CAD-Recode (ICCV 2025) maps point clouds to CadQuery Python with a Qwen2-1.5B decoder. It trained on 1M procedurally generated CAD programs and samples 10 candidates, keeping the one with the best Chamfer distance (secondary). Reported DeepCAD IoU is 92.0% versus 77.6% (secondary). It is point-cloud conditioned, not text-only. — [arXiv 2412.14042](https://arxiv.org/abs/2412.14042v2); [secondary review](https://www.themoonlight.io/tw/review/cad-recode-reverse-engineering-cad-code-from-point-clouds)
- BlenderLLM fine-tunes on BlendNet (about 8k instruction-bpy pairs, secondary) with self-improvement, evaluated on CADBench. A later paper says its outputs lack geometric constraints. — [arXiv 2412.14203](https://arxiv.org/pdf/2412.14203); [2505.19490](https://arxiv.org/html/2505.19490v1)
- Text2CAD-Bench (2026) benchmarks LLM text-to-CadQuery, with an error-message retry protocol. — [arXiv 2605.18430](https://arxiv.org/pdf/2605.18430)
- Sparks of AGI: GPT-4 "Draw a unicorn in TikZ" was queried over a month and shows clear improvement. This is the original from-memory geometry probe. — [arXiv 2303.12712](https://arxiv.org/pdf/2303.12712)
- Simon Willison's pelican-on-a-bicycle SVG test is judged by eye, with no formal score. Robert Glaser added an agentic render-and-revise loop. In Aug 2026 Karpathy reportedly had Claude Opus 5 write a three.js Lord of the Rings world (about 5500 lines, about 2 hours), per a GIGAZINE secondary report. — [Willison/Glaser](https://simonwillison.net/2025/Nov/11/agentic-pelican-on-a-bicycle/); [Glaser](https://www.robert-glaser.de/agentic-pelican-on-a-bicycle/); [GIGAZINE](https://gigazine.net/gsc_news/en/20260804-ai-test-cg/)

### Inferences
- For a general frontier LLM with no fine-tuning (the "from memory" case), code that builds primitives or SDF/parametric surfaces is the practical path. Raw OBJ needs fine-tuning to be good.

### Gaps
- MeshXL, Text2CAD (the original paper), and OpenSCAD-specific LLM studies were not retrieved.
- No head-to-head of raw-vertex vs code on the same frontier model was found.

## Which representation works best?

### Takeaway
Structured or code representations (construction trees, parametric primitives, procedural code) beat raw coordinates. Evidence for this comes from adjacent assembly work, not a single 3D-shape benchmark.

### Cited Findings
- In LLM machine-design synthesis, construction-tree representations outperformed coordinate-only descriptions, and adding parsed spatial information helped further. — [arXiv 2510.14980](https://arxiv.org/pdf/2510.14980)
- A shape-program benchmark found parse failures were mostly out-of-range values, so models don't absorb range constraints from a short prompt. — [ShapeCodeBench](https://arxiv.org/pdf/2605.11680)
- Craft-assembly work found hallucinated cuboid dimensions and missing alignment fields. — [Prompt2Craft](https://arxiv.org/pdf/2512.04568)
- SceneCraft converts spatial relations into numeric constraints, which supports scene-graph or constraint intermediates. — [PMLR](https://proceedings.mlr.press/v235/hu24g.html)
- LL3M claims that code is a readable, editable high-level representation that can use modifiers and B-meshes. — [arXiv](https://arxiv.org/abs/2508.08228)

### Inferences
- Likely best for text-only creature or shape work is a skeleton plus parts, with parametric primitives and explicit symmetry handled in code (build one side and mirror), and numeric constraints instead of free coordinates. This is inference, not directly benchmarked.

### Gaps
- No ShapeAssembly-with-LLM results were found. A direct representation ablation on a frontier LLM was not found.

## Does iterative self-correction with rendered feedback help?

### Takeaway
Yes for gross and execution errors, but with limits. Visual feedback misses precise dimensions, and the VLM critic is a weak point. Programmatic geometric checks add value.

### Cited Findings
- CADSmith (2026): nested loops (execution errors, then OpenCASCADE measurements plus a VLM judge). Execution rate went from 95% to 100%, median IoU from 0.8085 to 0.9629, and mean Chamfer from 28.37 to 0.74 on 100 prompts. The authors argue that visual-only feedback misses dimensional errors. — [arXiv 2603.26512](https://arxiv.org/abs/2603.26512)
- CADCodeVerify (ICLR 2025): the VLM asks and answers validation questions about its render. With GPT-4 this gave a 7.3% point-cloud-distance reduction and a 5.5% compile-rate gain. It introduces CADPrompt (200 prompts). — [ICLR 2025 paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/81a934cd364e18ea6fdeaf57a93c17d4-Paper-Conference.pdf)
- 3D-PreMise (2024): GPT-4 fixed clear parametric mistakes from renders but lacked sensitivity to common-sense visual errors. Self-correction was limited in complex geometric math. — [arXiv 2401.06437](https://arxiv.org/pdf/2401.06437)
- Pelican loop: letting vision models render and retry gave better SVGs (qualitative). — [Willison](https://simonwillison.net/2025/Nov/11/agentic-pelican-on-a-bicycle/)
- Multi-agent Blender coding (LL3M, SceneCraft) uses VLM render critique as a core loop (reported qualitatively and via human studies). — [LL3M](https://arxiv.org/abs/2508.08228); [SceneCraft](https://proceedings.mlr.press/v235/hu24g.html)

### Inferences
- A good loop: execute, run numeric checks (bbox, symmetry, volume, part counts), then do multi-view VLM critique. Multi-view critique per se was not tested against single-view in the sources found.

### Gaps
- No ablation of 1-view vs multi-view critique. No quantified results for TikZ or SVG loops.

## Evaluation methods

### Takeaway
Mixed: geometric metrics (Chamfer, IoU, compile rate) when ground truth exists, VLM or CLIP judging and human studies for open-ended text prompts. Blind-recognition protocols were not found.

### Cited Findings
- CADBench, CADPrompt, Text2CAD-Bench and CADSmith's 100-prompt set use IoU, Chamfer, point-cloud distance and execution rate. — sources above
- SceneCraft used constraint adherence plus human assessment. — [PMLR](https://proceedings.mlr.press/v235/hu24g.html)
- Pelican test is informal visual judging, with tiers set by the evaluator. A secondary July 2026 study claims no evidence labs specifically optimize for it (unverified). — [GIGAZINE/summary](https://gigazine.net/gsc_news/en/20250609-llms-pelicans-on-bicycles/)

### Gaps
- No blind-recognition human study of LLM-written shapes was found. CLIP/VLM multi-view scoring protocols were not found in detail.

## Known failure modes

### Takeaway
Spatial construction fails more often than planning: orientation, attachment, collisions, hallucinated dimensions. Symmetry and perspective specifics are inferred, not directly measured.

### Cited Findings
- Models give plausible plans but fail on part orientation, wrong parent attachment and blueprint adherence. — [arXiv 2510.14980](https://arxiv.org/pdf/2510.14980)
- Collisions were 69.1% of craft-assembly failures, and misplacement and wrong orientation were common. — [Prompt2Craft](https://arxiv.org/pdf/2512.04568)
- LEGO assembly: overlaps and misapplied interlocking even when the rules can be recited. — [LegoGPT summary](https://www.emergentmind.com/topics/legogpt)
- Tangram benchmark: models match silhouettes at the expense of geometric constraints. — [arXiv 2601.16520](https://arxiv.org/pdf/2601.16520)
- GPT-4o struggles with spatial reasoning and precise replication in visual programming (secondary summary). — same search result set
- Visual feedback is insensitive to dimension errors. — [CADSmith](https://arxiv.org/abs/2603.26512); [3D-PreMise](https://arxiv.org/pdf/2401.06437)

### Inferences
- Left/right pair and symmetry errors, perspective confusion and proportion drift are expected from raw coordinates and are mitigated by mirroring in code and numeric checks. No source here measured them directly.

### Gaps
- No direct citation for symmetry/pair errors, perspective confusion or proportions specifically in LLM-written shapes.
