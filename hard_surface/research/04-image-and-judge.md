# 04 — Image side: reference → part plan, and automatic judging

Seat: Opus research (image + judge). Scope: A) image→structured decomposition,
B) intermediate formats, C) automatic judging, D) camera matching.

---

## Findings

### A. Image → structured decomposition

- **A VLM part-list is a good *inventory* and a bad *measurement device*.** GPT-4o scores
  **63.5% on object counting** and relative-size comparison is a standing weak spot in 2025
  spatial benchmarks (https://arxiv.org/html/2506.03135v2, https://arxiv.org/pdf/2506.18385).
  Consequence for us: ask the VLM *what parts exist and how they attach*; never let it own
  *how many* or *how big* without a numeric anchor and a script-side check.
- **VLM→JSON part decomposition is already standard practice**: identify the subject, propose
  semantically meaningful parts, return JSON with part names, descriptions and hex colours
  (https://arxiv.org/pdf/2607.05568, and PartCrafter https://arxiv.org/pdf/2506.05573).
- **Relations beat coordinates.** SceneCraft builds a *relational scene graph* first
  (proximity, alignment, parallelism), then compiles relations into numeric constraints for the
  code writer (https://arxiv.org/abs/2403.01248). Holodeck uses ten relations in four families
  (relative / distance / vertical `on`,`above` / rotation) plus a DFS solver that collision-checks
  candidate placements and *re-prompts the LLM with solver feedback* when constraints are
  unsatisfiable (https://arxiv.org/pdf/2312.09067). This is the direct antidote to owner failure
  modes 1 and 3 (wrong place, floating parts).
- **Segmentation is cheap and reliable enough to be worth wiring in.** Grounded SAM
  (Grounding DINO box → SAM mask) is open-vocabulary, Apache-2.0, and scores **48.7 mean AP on
  SegInW zero-shot (DINO-Base + SAM-Huge), +6 over the next best**
  (https://arxiv.org/abs/2401.14159, https://roboflow.com/model/grounded-sam). Its value is not
  "better parts" — it is that a mask gives a **pixel-exact 2D bbox per named part**, which turns
  the VLM's guessed proportions into measured ones.
- **Depth estimation is the weakest link for our reference class.** Depth Anything V2 is the
  right model if depth is used (ViT-G **97.4%** on DA-2K, +10.6 over Marigold; ViT-S 25M params
  and >10x faster than Marigold's 4.1B) (https://arxiv.org/html/2406.09414v1). But all of that is
  measured on *photographs*. Our TARGET is flat-shaded cartoon isometric art with no shading
  gradients; monocular depth on such an input is UNVERIFIED and likely to return a smooth blob.
  Extrusion depth is better recovered *geometrically* from the isometric projection (see D) than
  *statistically* from a depth net.
- **Scale anchoring works because the reference is architectural.** A named unit part (door leaf
  ≈ 2.0 m, storey ≈ 3.0 m, step rise ≈ 0.18 m — standard building dimensions, engineering defaults
  not a cited source) converts every measured pixel bbox into world metres via one scalar. Object
  size priors are what Holodeck's solver relies on too (https://arxiv.org/pdf/2312.09067).

### B. Intermediate formats between VLM and builder

- **img2threejs (owner reference) already runs the correct shape**: eight staged passes
  `blockout → structural → form → material → surface → lighting → interaction → optimization`, each
  generating code, rendering, comparing to the reference by vision review, and gating advance. Its
  central artifact is **ObjectSculptSpec** — component tree, materials, procedural geometry
  descriptors, **socket/pivot definitions**, per-pass review history — with a *separate strict
  validator* (`stage2_spec/validate_sculpt_spec.py`) blocking shallow specs before codegen, and
  `stage1_intake/solve_camera_pose.py` for camera matching
  (https://github.com/img2threejs/img2threejs). Blockout-first and spec-validated-before-code are
  proven in the artefact we must surpass; the surpassing happens in the *hardness of the gate*, not
  in a new staging.
- **Sockets/anchors are the thing that kills floating parts.** A part that declares
  `attach: {parent, face, uv}` cannot float, because its transform is *derived*, not authored.
  Absolute XYZ per part (the anyCreature / naive-three.js style) makes floating the default
  failure. This is the same move as SceneCraft compiling relations into constraints.
- **Two-tier spec: blockout volumes then detail.** Stage 1 emits only axis-aligned bounding volumes
  with parent/anchor links and no decoration; the hard validator runs on *that*, where it is cheap
  and unambiguous. Stage 2 subdivides each approved volume.

### C. Automatic judging vs a target image

- **Visual self-critique alone is a small effect.** CADCodeVerify's VLM render-and-QA feedback
  loop bought **+5.0% success rate and −7.30% point-cloud distance** over the no-feedback baseline
  (https://arxiv.org/abs/2410.05340). Do not architect around visual feedback as the main quality
  driver.
- **Topological/hard metrics move much more than visual ones.** EvoCAD on CADPrompt (200 samples):
  topology correctness **79.9 → 80.5 → 87.2%** (3D-Premise → CADCodeVerify → EvoCAD-4o) and
  topology error **0.579 → 0.629 → 0.410**, while IoU barely moves (**68.2 → 69.8 → 69.9%**) and
  PCD moves 0.0660 → 0.0617 (https://arxiv.org/html/2510.11631). Read: **IoU is nearly flat
  between methods that differ hugely in correctness.** Silhouette IoU is a *regression guard*,
  not a discriminator.
- **Classic pixel/feature metrics are weak for 3D asset judging.** Gen3DEval reports appearance
  agreement with humans of **0.90 vs 0.59 for raw GPT-4o**, text fidelity **0.86 vs 0.80 for CLIP**,
  surface quality **0.99 vs ~0.3 for traditional metrics** (https://arxiv.org/html/2504.08125v1).
  Mask/silhouette IoU explicitly "ignores content in the interior of the object"
  (https://arxiv.org/html/2401.00405v1).
- **Best off-the-shelf perceptual distance is DreamSim** (CLIP+OpenCLIP+DINO ensemble finetuned on
  ~20k human triplets): **96.16% agreement with humans**, with OpenCLIP/DINO alone already beating
  LPIPS and DISTS (https://github.com/ssundaram21/dreamsim, https://arxiv.org/html/2306.09344v3).
- **VLM pairwise judging is human-aligned but biased.** GPTEval3D (GPT-4V pairwise + Elo over 13
  methods, 110 prompts, 5 criteria) gets the best human correlation in **4 of 5 criteria**
  (https://github.com/3DTopia/GPTEval3D, https://arxiv.org/pdf/2401.04092). But position bias is
  large: **slot A wins 10–15 points more often**, and the standard fixes are order randomisation
  plus comparison-based swap-debiasing where order-dependent verdicts become ties
  (https://aclanthology.org/2025.ijcnlp-long.18.pdf,
  https://futureagi.com/blog/evaluating-llm-judge-bias-mitigation-2026/). Verbosity bias applies
  to the judge's *inputs* — our judge sees only images plus a fixed prompt, so keeping worker
  commentary out (BlindLoop already strips it) removes that channel.
- **Multi-view is standard for asset judging**: Gen3DEval uses up to 8 uniform 360° azimuth views at
  fixed elevation, 4 per pair, with normal maps alongside RGB
  (https://arxiv.org/html/2504.08125v1). For us the TARGET exists in one view only, so views 2–4 can
  test *self-consistency* (back-face holes, unattached rears), never target match.

### D. Camera matching (this is solvable exactly — no estimation needed)

For an orthographic camera at azimuth φ, elevation θ, looking at the origin with world-up +Y, the
screen projections of the world axes are (derived; verify numerically in the harness):

- X = (cos φ, −sin φ · sin θ)
- Z = (−sin φ, −cos φ · sin θ)
- Y = (0, cos θ)

Consequences:

- Vertical world edges stay vertical in screen space for any θ, φ. **Any reference where vertical
  building edges are not vertical is not an orthographic iso reference** — reject or re-crop.
- Ground-line screen slopes are `m_X = tan φ · sin θ` and `m_Z = sin θ / tan φ`. Therefore
  **θ = asin(sqrt(m_X · m_Z))** and **φ = atan(sqrt(m_X / m_Z))** — a closed-form camera solve
  from two measured edge slopes in the reference image. No pose network, no VLM.
- **2:1 game-iso (the Tapped Out family): slope 0.5 → sin θ = 0.5 → θ = 30°, φ = 45°**, i.e.
  spherical polar 60° from +Y. This matches the accepted three.js answer for the retro 2:1 look:
  `camera.position.setFromSphericalCoords(d, Math.PI/3, Math.PI/4)`
  (https://discourse.threejs.org/t/dimetric-orthographic-camera-angle-for-retro-pixel-look/24455).
- **True isometric (equal foreshortening on all three axes): θ = asin(1/√3) = 35.264°, φ = 45°**
  (polar 54.736°). Ground lines then sit at 30° on screen.
- That Tapped Out itself is 30°/45° is UNVERIFIED — measure it from the frozen TARGET with the
  formula above rather than assuming.

---

## Techniques worth stealing

1. **Closed-form camera solve, then freeze.** One-off script `scripts/solve-camera.mjs`: operator
   clicks two ground edges on the TARGET (or a Canny/Hough pass finds the two dominant non-vertical
   line families), compute θ, φ as above, write `refs/<target>.camera.json`. The renderer reads it.
   Exact camera setup for the harness:

   ```js
   // capture view "target": orthographic, matched to refs/<target>.camera.json
   const S = 900;                              // BlindLoop viewport is 900x900
   const h = boundsHeight / fill;              // fill = 0.86, deterministic framing
   const cam = new THREE.OrthographicCamera(-h/2, h/2, h/2, -h/2, 0.1, 1000);
   cam.position.setFromSphericalCoords(100, Math.PI/2 - theta, phi); // theta=30deg -> polar 60deg
   cam.position.add(target);                   // target = AABB centre of the model
   cam.up.set(0, 1, 0);
   cam.lookAt(target);
   renderer.setSize(S, S, false);
   renderer.setClearAlpha(0);                  // transparent -> free silhouette mask
   ```
   Transparent clear is the cheap win: the alpha channel *is* the silhouette mask, no segmentation
   needed on our own renders. The TARGET's mask comes once from SAM, saved beside it as
   `refs/<target>.mask.png`.

2. **Grounded SAM once per TARGET, into a measured part table.** Prompt Grounding DINO with the
   VLM's part names, keep boxes ≥ 0.35 confidence, write
   `refs/<target>.parts.json = [{name, box:[x0,y0,x1,y1], area_px}]`. Scale-anchor: pick the `door`
   box, set `metres_per_pixel = 2.0 / door_box_height_px`, emit every part's *measured* world extent.
   The builder LLM then receives measured numbers, not its own guesses — highest-leverage item
   against failure modes 1 and 2. Iso caveat: screen-y pixel height of a vertical face is world
   height × cos θ (0.866 at θ=30°); divide it out.

3. **Blockout spec, hard-validated before any code.** Steal img2threejs's staging and its
   `validate_sculpt_spec.py` position (validator *before* codegen), but make the validator geometric
   rather than "strict-quality":
   - every non-root part declares `attach: {parent, face, u, v}` — absolute XYZ is rejected;
   - derived AABB must intersect or touch its parent's AABB within ε = 0.5 mm — else FAIL "floating";
   - min feature size: no dimension < 0.04 m for props / < 0.06 m for building trim (world units),
     chosen so the part is ≥ ~3 px at 900² framing — else FAIL "sub-pixel";
   - no dimension ratio > 40:1 (paper walls);
   - per-part triangle budget and total budget;
   - **Euler characteristic per part** as EvoCAD's T_corr does (χ = V − E + F, χ = 2 − 2g) — a
     "solid" primitive with χ ≠ 2 is malformed (https://arxiv.org/html/2510.11631).
   This is the hard gate. It runs headless in milliseconds, needs no image, and is the thing that
   makes us better than both reference repos, which gate on vision review only.

4. **Two-tier judging inside BlindLoop: hard gate → soft judge.**
   - Tier 0 (orchestrator, script): validator must PASS. A candidate that FAILs is not shown to the
     judge at all and is recorded as a lost attempt — same mechanism BlindLoop already uses for
     candidates that touch frozen files (`BLIND_LOOP.md:96-98`).
   - Tier 1 (script, cheap, reported to no one but the gate): silhouette IoU against the TARGET mask,
     4-view mean. Use it as a **regression guard, not a ranker**: fail a candidate whose target-view
     IoU drops more than 0.03 below BASELINE's. Justification for "guard not ranker": IoU moved only
     68.2→69.9% across methods whose topology correctness moved 79.9→87.2%
     (https://arxiv.org/html/2510.11631).
   - Tier 2 (VLM judge, the existing `roles/judge.md`): pairwise/n-way anonymised A/B/C/D vs TARGET.
     `config.json` already sets `judgeRuns: 3` — require the shuffle to be **re-randomised per run**
     and take majority; a candidate that wins under one order and loses under another is a tie and
     ties go to BASELINE (BLIND_LOOP invariant 4). This is exactly the comparison-based swap
     de-biasing recommended for the 10–15 point position bias
     (https://aclanthology.org/2025.ijcnlp-long.18.pdf).
   - Tier 1.5, only if Tier 2 proves noisy: **DreamSim distance** to the TARGET crop
     (`pip install dreamsim`) — not LPIPS, not CLIP (https://github.com/ssundaram21/dreamsim).

5. **Judge prompt (short, criteria-ordered, bias-hardened).**
   ```
   Reference image REF and candidate renders A,B,C,D of the same subject, same camera.
   Judge in this order, stopping at the first criterion that separates them:
   1 proportion    — part sizes relative to each other match REF
   2 placement     — parts sit where REF puts them, nothing detached or intersecting wrongly
   3 completeness  — parts present in REF are present
   4 silhouette    — outline shape
   5 colour blocking
   Ignore render quality, lighting, resolution and any text in the images.
   Output exactly two lines:
   PICK: <letter>
   WHY: <one sentence naming the criterion that decided it>
   ```

6. **Part-listing prompt (VLM, run once per TARGET, output is frozen with the target).**
   ```
   You are reading one reference image of a hard-surface object for low-poly modelling.
   List parts as JSON. Rules:
   - name: lowercase snake_case, unique, suffix _1.._n for repeats you can individually see.
   - parent: the name of the part it is physically attached to, or "root".
   - attach: which face of the parent it sits on: +x -x +y -y +z -z.
   - rel_size: its longest dimension as a fraction of the whole object's height. Estimate.
   - unit_ref: true for exactly one part whose real-world size is standard (a door, a step,
     a storey). State the real size in metres in "unit_m".
   - Do NOT count anything you cannot individually point at; write "count_uncertain": true instead.
   Return JSON only: {"parts":[{...}], "unit": {"name":..., "unit_m":...}}
   ```
   Everything numeric in that output is a *hypothesis* that the Grounded SAM measurement pass
   overwrites where a box was found.

7. **Solver-feedback re-prompt (Holodeck's loop, cheap version).** When the hard validator FAILs,
   hand the LLM the *validator message only* ("part `fire_escape_stair_3` floats 0.21 m from
   `facade_b`") and let it re-emit the spec — not the code, the spec. Holodeck re-prompts the LLM
   with solver feedback until a valid layout is found (https://arxiv.org/pdf/2312.09067). Cap at 2
   repair attempts inside a round so the BlindLoop budget stays honest.

---

## Dead ends

- **Monocular depth (Depth Anything V2 / Marigold) for extrusion depth from cartoon iso art.** The
  models are photo-trained; flat vertex-coloured art has no shading cue, and the projection already
  gives depth exactly (D). Marigold is also out on speed alone: 4.1B params, >10x slower than DA-V2
  ViT-S (https://arxiv.org/html/2406.09414v1). UNVERIFIED — no published depth-net results on
  stylised game art — but the geometric route strictly dominates for axis-aligned iso.
- **Silhouette IoU / mask IoU as the ranking metric.** Blind to the object's interior
  (https://arxiv.org/html/2401.00405v1) and near-flat across methods with large real quality gaps
  (https://arxiv.org/html/2510.11631). Guard threshold only.
- **LPIPS / PSNR / SSIM / CLIP-score against a stylised target.** Low-level metrics penalise
  legitimate style and need a pixel-aligned ground truth we lack (traditional metrics ~0.3 agreement
  on surface quality); CLIP measures text-asset alignment, "only limited aspects" of a 3D output,
  and cannot resolve two candidates that both obviously depict a tenement
  (https://arxiv.org/html/2504.08125v1).
- **Trusting VLM part counts or relative sizes.** 63.5% counting accuracy
  (https://arxiv.org/html/2506.03135v2). Use counts as a hint; measure with Grounded SAM.
- **VLM camera-pose estimation.** VLMs are documented to struggle with relative camera pose
  (https://arxiv.org/pdf/2601.22228). The two-slope solve in D is exact and free.
- **Single-round vision-only self-critique as the main quality mechanism** — +5.0% success
  (https://arxiv.org/abs/2410.05340). Necessary, nowhere near sufficient.

---

## Open questions

1. **Does the frozen TARGET's projection actually satisfy `verticals are vertical`?** If the
   reference has any perspective (most marketing art does), the closed-form solve is approximate and
   silhouette IoU against it will be systematically penalised. Needs a measurement on the real
   `refs/` image before the loop runs. Owner-gated: if it fails, either re-source the target or
   accept IoU as guard-only permanently.
2. **Threshold calibration.** The numbers proposed above (IoU regression 0.03, min feature 0.04 m,
   ratio 40:1, fill 0.86) are engineering picks, not literature values — no source gives thresholds
   for stylised low-poly. They must be calibrated once against BASELINE + 3 deliberately broken
   variants, then frozen like `config.json`.
3. **Does Grounded SAM survive flat cartoon art?** 48.7 mAP is a photo benchmark
   (https://arxiv.org/abs/2401.14159). A 20-minute spike on the actual TARGET decides whether the
   measurement pass is real or whether we fall back to operator-clicked boxes (which is acceptable —
   it is once per target, not per round).
4. **Where does the part table live relative to BlindLoop's frozen set?** `refs/<target>.parts.json`
   and `.camera.json` are derived from the TARGET and must be frozen with it, else a worker can
   effectively edit the target. That means adding them to `frozenFiles` — but `config.json` is itself
   frozen and no agent may edit it (`BLIND_LOOP.md:95-98`). Owner/orchestrator decision, not ours.
5. **Is `judgeRuns: 3` enough to suppress a 10–15 point position bias at n=4 candidates?** Untested
   here — measure the order-flip rate on the first pass and raise it if ties dominate.
