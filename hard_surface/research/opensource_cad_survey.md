# Open-source base for an LLM-drivable hard-surface CAD modeller (survey, 2026-10-21)

Scope: a Plasticity-like tool (NURBS/B-rep solids, booleans, fillets/chamfers, fast keyboard UI) for game hard-surface assets. Windows, target RTX 2070M.
Method: read-only web check plus prior knowledge. **Verified this pass:** build123d-mcp is on PyPI (v0.3.5x; exec, render and measure tools, sandboxed), and an MIT `@casys/mcp-build123d` exports STEP/STL/GLB. Check pass 2026-10-21: licences + latest releases verified via GitHub API (api.github.com/repos/<owner>/<repo>); paper numbers from arXiv abstracts. CADmium, Mayo, Bitbybit, Zoo, CGAL, libfive rows unverified.

## 1. Kernels

| Kernel | Licence / can ship closed? | Booleans | Fillet/chamfer | Notes |
|---|---|---|---|---|
| **OpenCASCADE (OCCT 8.0.1, 2026-07-30)** | LGPL-2.1 + exception. Yes, if OCCT is dynamically linked and its changes are published | Good. Fuzzy/glue options; fails on tangent/coplanar edge cases | The best open option. Still fails on vertex blends, variable-radius and fillet-over-fillet (Plasticity's Parasolid hits these far less often) | The only mature open B-rep. Exports STEP/IGES/glTF (RWGltf). C++; Python via OCP/pythonocc |
| **Manifold** | Apache-2.0 (v3.5.4, 2026-09-25). Yes | Excellent, guaranteed manifold, fast (in Blender 4.5+ and OpenSCAD) | None (mesh only) | Mesh-stage boolean or fallback. Not B-rep |
| **Truck (Rust)** | Apache-2.0 (no GH releases; active Oct 2026). Yes | Early, fragile | Minimal | Research grade |
| **Fornjot** | 0BSD (GH shows NOASSERTION; unverified). Last release v0.49.0 2024-03. Yes | Not usable yet | No | Not production |
| **SolveSpace kernel** | GPL-3. No | NURBS booleans, often flaky | No fillets | Its constraint solver (libslvs) is the valuable part |
| **CGAL** | GPL or commercial. No (unless you buy a licence) | Exact Nef polyhedra: robust but slow, mesh only | No | |
| **libfive** | MPL-2.0 (lib) / GPL (studio). Lib yes | SDF: always succeeds | Smooth blends, but no exact edges or B-rep | Greebles/detail only |
| **Parasolid / ACIS / C3D** | Commercial (C3D has cheaper tiers) | Best | Best (Plasticity = Parasolid) | Paid upgrade path |

## 2. Code-CAD layers

| Layer | Licence | LLM fitness | MCP | Notes |
|---|---|---|---|---|
| **build123d** (OCP/OCCT) | Apache-2.0 (v0.13.0, 2026-09-21) | **Best.** Pythonic builder/algebra modes. Selectors (`edges().filter_by(Axis.Z)`, `group_by`, `sort_by`) give text-addressable topology. Clear exceptions | **Yes** (build123d-mcp: exec + render + measure; @casys/mcp-build123d) | Exports STEP/STL/glTF/3MF/SVG. Windows pip wheels. Active |
| **CadQuery 2.x** | Apache-2.0 (GH NOASSERTION; v2.8.0, 2026-06-20) | Very good. The most LLM training data; most text-to-CAD papers use it. String selectors (`">Z"`, `"|Z"`) | Community servers | Same kernel |
| **OCP** | Apache-2.0 (8.0.1.1, 2026-09-24 = OCCT 8) | Too low-level for an LLM directly | - | Foundation under both |
| **Zoo / KittyCAD KCL** | App/KCL open (MIT, per the modeling-app repo; verify), but **the geometry engine is proprietary and cloud-hosted** (paid API) | Language designed for LLMs | Zoo API | Can't ship offline/closed for free. Design reference only |
| **OpenSCAD** | GPL-2 (running it as an external CLI is OK) | CSG only, no fillets. Manifold backend is fast | Several | Wrong primitives for hard surface |
| **ImplicitCAD** | AGPL | Niche | - | Skip |

## 3. Full apps

| App | Licence | Kernel | Scripting / LLM | MCP | Headless / render | Verdict |
|---|---|---|---|---|---|---|
| **FreeCAD 1.1.x (1.1.4, 2026-09-28)** | LGPL-2.1 | OCCT | Full Python API, but toponaming is only partly fixed, the doc model is heavy and the API is GUI-coupled and noisy | **Yes** (neka-nat/freecad-mcp MIT, active Oct 2026) | FreeCADCmd headless. Offscreen rendering is awkward | Usable but heavy. UX is the opposite of Plasticity |
| **Blender + CAD Sketcher / OCCT add-ons** | GPL (distributed add-ons inherit it) | Mesh + Manifold booleans; CAD Sketcher uses the solvespace solver | bpy is excellent and the LLM knows it well | **Yes** (ahujasid/blender-mcp, now mcp-for-blender, MIT, active) | Best: headless EEVEE/Cycles, FBX/glTF | Ideal render/bake/export end; weak as a B-rep modeller |
| **SolveSpace** | GPL-3 (v3.3, 2026-10-21) | own | Weak | - | - | No |
| **Dune 3D** | GPL-3 (v1.4.0, 2026-01-28) | OCCT + solvespace solver | Little | - | - | UX reference; GPL |
| **Mayo** | BSD-2 | OCCT viewer | CLI convert | - | Yes | Converter only |
| **CADmium** | verify | Truck, web | - | - | - | Stalled (2024) |
| **Chili3D** | AGPL-3.0 (0.7.1, 2026-09-19) | OCCT-wasm, web | TS | - | Browser | AGPL is a problem for closed ship. UI reference |
| **Bitbybit** | MIT core, paid cloud parts | OCCT/Manifold wasm | TS + nodes | - | Browser | Web option; wasm OCCT is slower |
| **"Plasmic"** | - | - | - | - | - | A web page builder, not CAD (probably meant Plasticity: closed, Parasolid) |
| **Onshape / Fusion** | Closed SaaS | Parasolid/ASM | FeatureScript/API | Community MCPs | Cloud | UX benchmarks only |

## 4. What makes an API "ideal for LLMs" (evidence)
- **Text parametric code beats GUI op streams.** CAD-Recode (arXiv 2412.14042): point cloud to CadQuery Python, SOTA on DeepCAD/Fusion360/CC3D, invalidity <1%. CADPrompt (200 prompts) / CADCodeVerify (Alrashedy et al., ICLR 2025, arXiv 2410.05340): **VLM render-then-self-critique** with GPT-4 gave -7.30% point-cloud distance, +5.0% success rate (modest, not "clear"). Text2CAD (NeurIPS 2024; numbers unverified) and DeepCAD use custom sketch/extrude tokens and need training; general LLMs do better in Python dialects they already know. Newer: CAD-Coder (2505.19713, CoT + geometric reward), CADReview (2505.22304), CADFS (2605.01925), CADFit (2605.01171), MIRAGE-CAD (2608.28669); headline numbers unverified. CAD-Coder and Zoo KCL agree: **code + execution errors + renders + measurements = the loop.**
- **Named / selector topology refs, not indices.** Edge #17 breaks after an upstream edit (FreeCAD toponaming). Semantic selectors and tags/labels survive edits and are readable by an LLM.
- **Deterministic and re-executable.** The model is one script rebuilt from scratch, so undo/history come free (git), the state can be diffed, and nothing hidden lives in GUI state.
- **Inspectable state** as JSON: volume, bounding box, face/edge counts, `BRepCheck` validity, min wall thickness.
- **Actionable errors:** "fillet r=3 failed on edges [..]: radius > adjacent face width 2.4" beats `StdFail_NotDone`. Wrap OCCT failures and suggest fallbacks (smaller radius, chamfer, reordering).
- **Cheap multi-view renders** per step (4 ortho + iso PNG) for VLM self-check.

## 5. Ranked recommendation
1. **build123d (OCCT) core + own MCP/verification layer + own fast viewport.** Apache + LGPL means a closed ship is possible. Best LLM ergonomics, selector topology, MCP precedent with render and measure, Windows pip, STEP/glTF export. Build: a tagged-face feature-tree DSL, a fillet wrapper with retry/fallback, Manifold as the mesh-boolean fallback, and an OCCT AIS or wgpu/three.js tessellation viewport for Plasticity-style keyboard UI. Fillet robustness is the known ceiling, so keep a C3D/Parasolid upgrade path behind a kernel interface.
2. **build123d/CadQuery B-rep + Blender (bpy + Blender MCP) game end.** B-rep is tessellated and passed to Blender for weighted normals, UVs, bakes, FBX/glTF and headless renders. The fastest path to a working pipeline, it reuses the anyCreature Blender tooling, and GPL is avoided if Blender stays an external process rather than part of the product.
3. **FreeCAD 1.x + FreeCAD MCP.** The most features out of the box and LGPL, but the API is heavy and noisy, toponaming is only partly fixed and the UX is non-Plasticity. Use as a prototyping fallback, not the product base.

Avoid as the base: CGAL/SolveSpace/Dune3D (GPL), Zoo KCL (proprietary cloud engine), OpenSCAD/libfive (no B-rep fillets), and Truck/Fornjot/CADmium (immature).

Sources: https://pypi.org/project/build123d-mcp/ , https://jsr.io/@casys/mcp-build123d , https://docs.zoo.dev/modeling-app/download
 , https://arxiv.org/abs/2412.14042 , https://arxiv.org/abs/2410.05340 , GitHub API repo/release endpoints for each repo named above
