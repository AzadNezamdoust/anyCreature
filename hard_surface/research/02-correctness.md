# 02 — Geometric correctness for LLM-generated hard-surface assets

Seat: Fable 5.1 analysis. Scope: failure modes (a) placement/scale logic, (b) too-small/too-thin,
(c) floating/disconnected. Conclusion first, evidence after.

## Verdict

**Representation:** an attachment program (ShapeAssembly-style), not free-coordinate code.
Parts are primitives with real-unit dimensions; every non-root part declares *what* it attaches to,
*which face*, *where on that face* (u,v), and a *contact mode*. Facades are grammar splits, not
hand-placed windows. Symmetry and repetition are macros (`reflect`, `repeat`), never copied
coordinates. The LLM never emits a world coordinate.

**Validators:** ten headless numeric checks (V0–V9 below) run on the compiled part list before any
image exists. All three target failure modes are fully decidable numerically; a VLM is only kept
for taste (the BlindLoop judge). Violations go back to the LLM as one-line, part-named text.

**Repair:** auto-repair only where the fix is deterministic and intent-preserving (snap a declared
attachment closed, grow a thin axis, union at export). Never auto-drop a floating part: floating is
a *logic* error, so it is re-prompted with the specific violation.

## Findings

### Representations
- ShapeAssembly (Jones et al. 2020): `Cuboid(l,w,h,aligned)`, `attach(c1,c2,x1,y1,z1,x2,y2,z2)`
  aligns a point in c1's local frame to a point in c2's; a second attach on an already-attached
  cuboid translates/rotates/resizes it to satisfy both, so attachment is enforced by the
  interpreter, not trusted. `reflect(c,axis)`, `translate(c,axis,m,d)`, `squeeze(c,a,b,face,u,v)`.
  Root is a mandatory bbox cuboid; non-leaf cuboids expand into sub-programs whose bbox is the
  parent. Physical-validity metrics: rootedness (ground-to-every-leaf path) 94.5/96.2/95.3 % vs
  StructureNet 89.7/94.4/96.2 (chair/table/storage); stability under gravity sim 84.7/85.9/83.7 %
  vs 74.9/76.8/75.0 %. Admitted gap: strongly non-axis-aligned structures can still leave
  disconnected leaves. https://arxiv.org/abs/2009.08026
- L3GO (2024): builds objects part-by-part (pivotal part first), a Spatial Critic checks
  continuity (disconnected components), overlap (part entirely inside another) and gaps; a
  Coordinate Calculator writes code run 3x with majority vote; attachment is phrased as
  "attach the wing to the middle of the fuselage's left side" (face + position on face).
  Ablation: spatial critic and program-based coordinates each contribute measurably.
  https://arxiv.org/html/2402.09052
- ShapeCraft (2025): flat graph, each node = text + 6-DoF bounding volume + code snippet;
  Evaluator inspects rendered *bounding-box* images first (structure before detail); 100 %
  compile rate but only 0.44 VQA structural pass rate — bounding boxes alone do not fix
  attachment. https://arxiv.org/html/2510.17603v1
- Text2CAD-Bench (2026): free-form CadQuery invalid rates rise steeply with complexity
  (GPT-5.2: 11.1 % L1, 20.0 % L2, 68.0 % L3; Claude-4.5-Sonnet 20.3/43.7/70.0 %). Switching
  to DeepCAD-style command sequences made it worse (DeepSeek-V3.2 L1 invalid 13.3 → 67.3 %).
  Executability, geometric similarity and design understanding are three independent axes.
  https://arxiv.org/html/2605.18430
- CAD-Recode / Text2CAD: sketch-extrude as Python code; validity = "code executes"; neither
  exposes attachment semantics, both are engineering-part shaped (single body), so they do not
  address (a)/(c). https://arxiv.org/abs/2412.14042 https://arxiv.org/abs/2409.17106
- CADPrompt (200 objects, expert CadQuery) and LLM4CAD: metrics are Chamfer/point-cloud
  distance + invalid rate; LLM4CAD found text-only beats image/multimodal input for CadQuery
  generation. https://arxiv.org/pdf/2410.05340 https://asmedigitalcollection.asme.org/computingengineering/article/25/2/021005/1208543
- Zoo KCL: `startSketchOn(face)` + `extrude(method = MERGE)` merges into the parent solid by
  default; edge/face tags (`$side`, `END`/`START`) let later features reference earlier geometry.
  Attachment is structural in the language. Zookeeper agent runs "inspect/snapshot/debug"
  engine tools during generation (details UNVERIFIED — marketing page).
  https://zoo.dev/docs/kcl-book/sketch_on_face.html https://zoo.dev/docs/kcl-book/tags.html
  https://zoo.dev/research/zookeeper
- CGA shape grammar (Müller, Wonka et al. 2006): mass model → facade `split`/`repeat` → tiles →
  windows; context-sensitive rules. CityEngine occlusion queries `inside/overlaps/touches
  (intra|inter|all)` test watertight volumes; canonical rule `WindowOpening --> case
  touches(intra): Wall else: ... Window` suppresses windows where another shape touches.
  https://dl.acm.org/doi/10.1145/1141911.1141931
  https://esri.github.io/cityengine-sdk/html/cgaref/cgareference/func_occlusion.html
- Our own CharacterStudioV2 blockout already carries the vocabulary: every part has `parent`
  and `attach_to: {part, contact: "rests-on-top" | "socket" | "embedded"}`, plus
  `anchor_size_m` and measured proportion ratios
  (D:\Git\checkout\tools\CharacterStudioV2\blockout-spec.json:31-45, :10).
- cad-khana (build123d wrapper): "constraints are enforced, not hoped for" — interference,
  clearance and assertion results in `mechanism.json`, violations fail the run; HLR ortho/iso
  line drawings for shape-level questions numbers don't express. https://github.com/cyberchitta/cad-khana

### Validators computable headlessly
- Connected components: `trimesh.split()` by face adjacency; watertight/winding checks built
  in. https://trimesh.org/trimesh.graph.html
- Guaranteed-manifold boolean union/intersection with volume readback: manifold3d (C++, Python,
  JS/WASM). Requires manifold inputs. https://github.com/elalish/manifold
- Thickness: `trimesh.proximity.thickness(mesh, points, method='max_sphere'|'ray')` casts
  inward from surface samples; `signed_distance`, `closest_point` for part-to-part gaps.
  https://trimesh.org/trimesh.proximity.html
- Thin-feature theory: local feature size = distance from surface to medial axis; 3D-print
  prep flags regions where that distance < half the printable resolution and thickens by
  advecting a velocity field. https://dl.acm.org/doi/10.1145/3450626.3459827
- Symmetry: declared `reflect` needs no detection; for undeclared, Mitra/Guibas/Pauly 2006
  transformation-space voting. https://dl.acm.org/doi/10.1145/1141911.1141924
- Layout solvers treat "no collision" and "no floating" as *hard* constraints: Holodeck (DFS
  over grid; edge/middle/near/far/in-front/side/above/on-top/center-aligned/face-to)
  https://ar5iv.labs.arxiv.org/html/2312.09067 ; LayoutGPT without a solver "frequently suffers
  from collisions, out-of-bound placements, and floating objects" (NaLA paper)
  https://arxiv.org/html/2606.29395 ; Infinigen Indoors DSL + simulated annealing
  https://arxiv.org/abs/2406.11824

### VLM critics — what they catch, what they miss
- CADCodeVerify: VLM writes 2–5 yes/no validation questions, answers them from multi-angle
  renders. Point-cloud distance 0.155 → 0.127 (GPT-4), 7 % better than 3D-PreMise-style raw
  visual feedback, which *degraded* hard cases by 20 %. But question-answer accuracy was only
  64.6–68.2 %; humans still beat it (0.120); "metrics cannot distinguish … gaps between
  components". https://arxiv.org/html/2410.05340
- 3D-PreMise: best prompting (one-shot CoT) 17.5 % Pass@1; self-correction from renders fixes
  obvious parametric mistakes but is "insensitive to commonsense errors visible in rendered
  output"; dominant failure = spatial precision (position/scale/rotation).
  https://arxiv.org/html/2401.06437
- BlenderGym: best VLM verifier alignment 0.66 vs human 0.79; some verifiers favour the second
  candidate regardless of order; verification only pays once compute is large (optimal
  verify-ratio 0.33–0.73). https://arxiv.org/html/2504.01786
- Cross-model VLM-judge protocol for meshes: agreement 0.95–0.97 on *visible* defects, 0.53
  (chance) on ambiguous pairs; geometry-validity proxies alone reached 0.62; a learned
  combiner collapsed onto manifoldness; thin structures listed as unsolved. No human check.
  https://arxiv.org/html/2606.18451
- BlenderAlchemy: pairwise tournament over b hypotheses (O(log b) queries), depth×breadth
  4×8 vs 8×4, and "hypothesis reversion" (previous best is always a candidate) — the same
  rule as BlindLoop's BASELINE-always-competes. https://arxiv.org/html/2404.17672
- General VLM spatial limits: patch encoders discard fine 3D cues; single-view judging
  suffers Janus artefacts; multi-view input needed. https://arxiv.org/html/2505.20279v5

## Techniques worth stealing (concrete)

### T1 — The DSL (what the LLM emits)
JSON, one object per part, metres, no world coordinates. Compiles deterministically (seeded
RNG only inside `jitter` fields) to a part list + union mesh, in JS so the BlindLoop capture URL
(`tools/BlindLoop/config.json:9`, 900×900) renders the same compiler output the validators saw.
```
{ "id":"balcony_2L", "prim":"box", "dims":[1.6,0.12,0.9],
  "attach":{"to":"facade_red","face":"+Z","uv":[0.25,0.55],"contact":"flush"},
  "repeat":{"axis":"Y","count":2,"pitch":3.0}, "mirror":null,
  "role":"balcony", "color":"iron" }
```
- `contact` ∈ {`rests-on-top`, `flush` (face-to-face), `socket` (penetrates depth d),
  `embedded`, `hangs-below`} — extends our blockout vocabulary (blockout-spec.json:32-45).
- `face` + `uv` is ShapeAssembly's attach point; `repeat`/`mirror` are its translate/reflect.
- Facades: `"grammar":{"floors":3,"floorH":3.0,"tile":{"w":1.5,"window":[0.9,1.4]}}` — a
  CGA split; windows are derived, so counts, spacing and alignment cannot be wrong.
- Root part must be `"ground":true`; the compiler places its bottom at y=0.
- Occlusion rule from CGA: a grammar window whose tile `touches` another part (balcony slab,
  fire-escape landing, adjoining facade) becomes wall. Computed with V4's contact table.

### T2 — Validator list (implementer-ready; run in this order, stop at first FAIL class)
Constants: `EPS_CONTACT` = max(1 cm, 0.5 % of asset bbox diagonal); `PX` = world size per
pixel of the frozen capture = ortho height / 900 (or bbox-diagonal-based for perspective);
`MIN_FEATURE` = max(style floor e.g. 4 cm, 3·PX).
- **V0 program-level (no mesh).** Schema; every `attach.to` names an *earlier* part (DAG, no
  cycles); exactly one `ground` part or every unattached part is `ground`; dims within class
  priors (table below); `repeat.count·pitch` fits inside the parent face. Cost: microseconds.
- **V1 per-part manifold.** Each compiled primitive is watertight + consistently wound
  (trimesh `is_watertight`, `is_winding_consistent`). Fail = compiler bug, not LLM's.
- **V2 declared contact is real.** For each `attach`: signed distance from the child's contact
  face samples to the parent surface. `flush`/`rests-on-top`: |d| ≤ EPS_CONTACT on ≥ 90 % of
  samples; `socket`: penetration ∈ [0.5d, 1.5d]; `embedded`: child volume ∩ parent ≥ 50 %.
  Message: `balcony_2L declared flush on facade_red +Z but gap = 0.12 m`.
- **V3 global connectivity + rootedness.** Contact graph: AABB-prefiltered part pairs with
  min surface distance ≤ EPS_CONTACT. Graph must be connected and every part must have a path
  to a `ground` part (ShapeAssembly rootedness). Cross-check with manifold3d union →
  `split()` component count == 1. Message names the orphan cluster and the nearest part.
- **V4 ground + stability.** Ground parts' min y == 0 (±EPS); projected centre of mass of the
  union inside the convex hull of the ground-contact footprint (cheap proxy for the gravity
  sim ShapeAssembly used).
- **V5 minimum feature size.** (i) min OBB extent of every part ≥ MIN_FEATURE; (ii) for
  non-box prims, 5th-percentile `trimesh.proximity.thickness` ≥ MIN_FEATURE; (iii) any
  `repeat` whose gap (pitch − width) < 2·PX is a sub-pixel pattern → must become one block
  with a colour stripe. Message: `rail_1 thickness 0.008 m < 0.04 m (3 px at capture)`.
- **V6 overlap / containment.** manifold3d intersection volume per pair ÷ smaller part volume:
  > 0.9 = invisible duplicate (L3GO's "entirely contained"); 0.2–0.9 without `socket`/
  `embedded` = accidental interpenetration.
- **V7 relative-scale logic.** Rule table keyed by `role`: window h < floorH; door h ∈
  [2.0, 2.4]; stoop step rise ∈ [0.14, 0.2]; railing top ∈ [0.9, 1.1] above its floor;
  awning bottom ≥ door top; parapet h ∈ [0.3, 1.2]; vehicle wheel radius vs wheelbase; prop
  bbox vs `anchor_size_m` (blockout-spec.json:10 pattern). Numbers are owner-ratified — start
  from building-code ranges and put them in a YAML the loop cannot edit.
- **V8 visibility at capture.** Offscreen id-buffer render at 900×900 from the frozen view;
  a part covering < 6 px is either hidden (drop from export, keep in program) or must grow.
  This is the only validator that needs the renderer; it also feeds the tri budget
  (props < 2k, buildings < 8k; degenerate/zero-area faces = 0).
- **V9 symmetry (optional).** Only when `mirror` is absent but `role` implies symmetry
  (vehicle, chair): mirror the union across the declared plane, 1k-sample chamfer distance
  ≤ 2·EPS_CONTACT.

Output contract: JSON `{pass:boolean, violations:[{validator, part, measured, limit, hint}]}`
plus a ≤ 8-line text rendering fed verbatim to the re-prompt. Zero LLM tokens spent on V0–V9.

### T3 — Repair policy
| Violation | Auto-repair | Re-prompt |
|---|---|---|
| V2 gap ≤ 5·EPS or ≤ 10 % of child extent | translate child along face normal to close it | — |
| V2 gap larger | — | yes, with measured gap and both part ids |
| V5 thin axis | scale that axis to MIN_FEATURE, keep the attached face fixed | if it breaks V6/V7 |
| V5 sub-pixel repeat | collapse to one block + stripe colour | — |
| V6 duplicate ≥ 0.9 | delete the contained part | log only |
| V3 orphan cluster | never (intent unknown) | yes, list orphan + nearest candidate parent |
| V7 scale rule | never (numbers are owner-gated) | yes, quote rule and measured value |
Each auto-repair re-runs V0–V9; a repair that creates a new violation is reverted and the
original violation re-prompted. Retry cap 3 per BlindLoop round; then BASELINE stands.

### T4 — Where the VLM stays
Only inside the BlindLoop judge, pairwise, BASELINE always a candidate, order permuted
(BlenderGym position bias), multi-view + a bounding-box-only render (ShapeCraft) so structure
is judged before colour. Never ask a VLM "is anything floating" — V3 answers that exactly.

### T5 — Generation order
Part-by-part with V0–V3 after every part (L3GO) beats whole-program emission for anything
over ~15 parts (Text2CAD-Bench L2→L3 collapse). Massing blocks → grammar facades → attached
props, one prompt per tier, each tier validated before the next is requested.

## Dead ends
- LLM writes three.js / bpy / CadQuery with world coordinates: 11–70 % invalid at scale,
  dominant residual error is spatial precision, no structural guarantees (Text2CAD-Bench,
  3D-PreMise, CADCodeVerify). Same root cause as the owner's three failure modes.
- Command-sequence tokens (DeepCAD style) for LLMs: strictly worse than Python (13 → 67 %).
- Chamfer / point-cloud / CLIP as correctness metrics: "noisy … cannot distinguish gaps";
  render-CLIP at chance (0.48) for defect judging. Use only as tie-breakers, never as gates.
- VLM as structural critic: 64–68 % QA accuracy, 0.66 vs human 0.79, blind to non-salient
  and thin defects — exactly failure mode (b). Learned combiners collapse onto manifoldness.
- Bounding-box-only structure (ShapeCraft flat graph): compiles 100 %, structurally valid 44 %.
- Auto-dropping floating parts: silently erases intent and hides the logic error from the
  loop; BlenderGym/BlindLoop need the failure to be visible to the ledger.
- Mesh-boolean union as the *only* connectivity check: a 2 mm gap is a separate component,
  but a part 1 mm inside another passes while being wrong — needs V6 alongside.
- Diffusion / Shap-E style generators for this class: no part semantics, no sockets, fail on
  counted structure ("chair with five legs", L3GO).

## Open questions
1. Compiler language: JS (three-mesh-bvh for closest-point, manifold-3d WASM for booleans)
   keeps one runtime for capture and validation; Python (trimesh + manifold3d) has richer
   thickness tooling. Recommendation JS-first with trimesh as an offline cross-check — owner call.
2. `MIN_FEATURE` px threshold (2 vs 3 px at 900²) and the style floor per asset class are
   owner-taste numbers; V7's range table likewise. Both need ratification before a run.
3. Perspective vs ortho for PX: BlindLoop capture for buildings is not yet frozen; V5/V8
   depend on it. Freeze the capture before the validator constants.
4. How much of CGA (splits/repeat/occlusion) to implement vs letting the LLM emit `repeat`
   counts: recommend implement splits; grammar is ~200 lines and removes a whole error class.
5. Non-axis-aligned parts (fire-escape diagonal stairs, chimney pipes at angles): ShapeAssembly
   admits rootedness loss there; V2 sample-based contact handles it, but `face`/`uv` on rotated
   prisms needs a defined local frame. Spec it before implementation.
6. Whether V4 stability should use a real gravity step (ShapeAssembly did) — proxy first.
