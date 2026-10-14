# anyCreature — why it reads as "procedural tubes", and what to do about it

Independent review (Fable). Repo read-only; every prototype and image lives under
`$S` = `/tmp/claude-0/-home-user-anyCreature/33ef5e48-0bfe-5281-b1b6-0e2d9698737c/scratchpad/review_fable/`.

Renderer used for every sheet: `$S/render/view.html` + `$S/render/shoot.mjs` (three.js from the repo's node_modules,
Chromium 1194 via Playwright, orthographic; `grey` = neutral smooth-shaded, `flat` = flat-shaded, `wire` = authored faces
(quads stay quads), `color` = COLOR_0). `shoot_posed.mjs` poses a skinned GLB at `move` t=0.3 s on the CPU.

---

## 1. Diagnosis — what makes it read as procedural tubes

The owner's verdict is correct and the cause is structural, not a matter of spec tuning. Every lever in the spec
language (profile rows, `taper`, `cup`, `bias`, `sharp`, `tufts`, `junction_band`) is a lever **on a ring**, and the
engine has exactly one surface primitive: a ring loft closed by caps, one per chain, intersecting its neighbours.

Evidence images:
- `$S/wolf_current_closeup.png` — 900 px wire (left) and flat-shaded (right) of the shipped wolf, 3/4 and side.
- `$S/current_flesh_quads_sheet.png` — the five flesh volumes alone, with their **authored quads** (not the GLB triangulation).
- `$S/wolf_current_sheet.png`, `$S/giant_current_sheet.png`, `$S/raven_current_sheet.png` — grey / wire / colour.
- `$S/orbit_wolf/orbit_sheet.png`, `$S/orbit_giant/orbit_sheet.png` — the harness's own orbit sheets.

| # | Property visible in the renders | Where it comes from |
|---|---|---|
| 1 | **Parallel, planar edge loops at constant spacing** along every mass. In the flat close-up the body is a stack of frustum bands, one per ring pair. | `engine/core/compile.js:269-283` — `buildVolume` resamples every chain at a fixed arc step (`ring_step` or `total/36`, max 48 rings), one ring per sample; `engine/core/geometry.js:82-85` `partFromRings` joins ring s to s+1 with N quads: every edge loop is a ring, every other loop a straight generator. |
| 2 | **Constant side count and perfect radial regularity**: 16 generators on the body, 14 head, 12 legs/tail; every ring has the same angular layout, so the wireframe is a rolled-up grid. | `engine/core/section.js:64-69` puts vertex k at `2πk/N` on every ring; `compile.js:261` `sides` default 12. Superellipse/taper/cup (`section.js:17-29`) only slide the vertex along the same ray — a "boxy" section is still a 12-gon with 30° walls. |
| 3 | **Intersecting shells with hard seams instead of one surface.** Legs are tubes whose root ring is buried in the torso, the head is an open tube rammed into the neck, the tail into the rump (`current_flesh_quads_sheet.png` shows the head as a separate cylinder ending inside the neck; the flat close-up shows a lit crease where each leg enters the chest). | `compile.js:359-392` caps; `checks.js:365` `root_containment` *requires* the buried root ring. The whole junction machinery — `junction.js:246-309` skin blend, `glb.js:84-121` normal copy, `shade.js:221-251` seam-safe colour — exists to **hide** a seam the geometry still has. Under animation (`$S/compare_posed.png` left) the seam returns at shoulder and neck. |
| 4 | **No edge flow following anatomy.** No loops around shoulder, hip, eye, mouth or jaw; every feature is a separate mesh placed on the surface. | `buildEye` `compile.js:480`, `buildNose` `:662`, `buildTufts` `:1319`, `buildPaw` `:1225`, `buildFin` `:1447`. |
| 5 | **Uniform tessellation regardless of detail.** Muzzle tip, rump and mid-thigh get the same ring spacing and sides. | `compile.js:270` `M = max(joints, min(48, round(total/step)))`; meanwhile one eye costs 128 tris (`:503-504`) and a lid 84. |
| 6 | **Identical repeated tufts.** Every clump is the same 4-station loft; the only variation is a length jitter alternating by `(i+r)%2`; mirrored exactly. | `compile.js:1391`, `:1399-1404`, `mirrorMesh` `:1538`. |
| 7 | **Silhouette made of cylinders/ellipsoids with concave corners at every junction** (no fillets) — visible on every orbit sheet at az045/az135. | Union of frusta + dome caps, no blending anywhere in the geometry stage. |
| 8 | **Shading reveals rings.** Normals are angle-weighted and smooth, but the silhouette is still the ring polygon, the L8 bone-field blend pushes every flesh normal toward *a cylinder's* (the code documents "every flesh normal is a cylinder's… the blobby sausage look"), and AO bakes the intersection creases into COLOR_0 (dark ring at each leg root). | `normals.js:126-137,165`; `glb.js:44-60`, `cli.js:186-194`; `ao.js:23`. |
| 9 | **Perfect bilateral symmetry** of geometry and colour; the twin is forbidden from differing. | `mirrorMesh` `compile.js:1538`; `mirror_distortion` `checks.js:565`. |
| 10 | **Per-ring two-joint skinning** — a rigid ring stack bends like a straw. | `compile.js:279-283`, then `junction.js` blend. |

Summary: the model **is** a set of intersecting lofted tubes; nothing in the spec language can make it not one.

## 2. What a hand-made game model has that this lacks

- One watertight, manifold surface (per material island at most); limbs meet the torso through a shared edge loop, never an intersection.
- Quad-dominant topology, >90 % valence-4, poles only at branch points; loops that circle the shoulder, hip, neck, eye socket, mouth and jaw and flow between them (the wolf's flesh is 100 % quads and has 0 such loops).
- Density where detail is: 3–4x denser on the face and hands than the thigh; a game wolf at 8 k tris spends ~35 % on the head.
- Planar changes and secondary forms sculpted into the surface: brow / cheek / jaw planes, sternum, scapula, thigh mass.
- Fillets at every junction.
- Deliberate asymmetry and imperfection (masses, tuft sizes, a tilted ear).
- Features integrated in the mesh: eye sockets as recesses with a lid loop, a mouth line, nostrils, ears growing out of the skull loops.
- Weights painted across a continuous surface so a bend deforms a region, not a ring boundary.

## 3. Candidate techniques, ranked (quality gain x feasibility in zero-dependency JS, keeping skinning/checks)

### Rank 1 — Hybrid: skeleton-driven **quad cage → Catmull–Clark → shrink-wrap onto a smooth-min SDF** (b+a) [prototyped]
- The existing chains/profiles are used twice: (i) as SDF primitives (ring-exact swept sections, smooth-min union, later sculpt primitives) that define the *shape*; (ii) as a **coarse quad cage** (12 sides x ~7 cm rings on the body, 8-sided limbs) whose limbs are **bridged into 2x2 holes cut in the torso cage** and whose serial chains (head, tail) are joined ring-to-ring. Catmull–Clark x1 (x2 for hero LOD), then project every vertex onto the SDF iso-surface.
- Look: one continuous quad mesh with real loops around shoulders/hips/neck, fillets at every junction, 96–97 % valence-4 — the wireframe of a box-modelled base mesh; grey render is a clay blockout instead of glued tubes.
- Cost: prototype ~550 lines; production ~1.5 k lines (one new module + integration). Runtime on the wolf: 2.7 s (2.4 s of it the 3 cm SDF grid; bbox-culled sampling gets it under 1 s).
- Risks: hole placement on a very thin torso (fallback: serial join); two limbs sharing one host ring (pick the next ring); wrap folds if the cage is far from the field (project the cage before CC); fan caps leave a 12-pole at nose/tail tip (use a grid cap). Skinning: k-NN transfer from the source rings posed cleanly; better: CC-subdivided weights. Budget: cage 12/8 @7 cm → 4 944 flesh tris (8 710 with parts); @9 cm → 3 984 (7 750). Deterministic. Checks: everything walking `_rings/_ringIdx/_pts/_seatIdx` (14 sites in checks.js, 10 in uv.js, junction.js, buildTufts, surfacePoint) keeps working because **the loft is still built** — it becomes the SDF source and anchor surface, it just no longer ships. `part_spans` survive (per-vertex part id carried through transfer); materials survive (per-vertex material majority → per-material primitive); arc colours transfer per vertex; AO / L1–L8 / L8 run on the new mesh unchanged.
- Spec changes: none for milestone 1 (`"surface": "cage"` root flag). Later: `blend` per attach (fillet radius), `cage_step`, per-chain `cage_sides`, `masses`.

### Rank 2 — **SDF + surface nets** (a alone) [prototyped]
- Same SDF; iso-surface via surface nets on a uniform grid, tangential relax.
- Look: continuous, filleted, seam-free — but the wireframe is grid-crumpled (54 % valence-4, 25 % valence-3), density uniform, thin features vanish under ~1.5 cells. Reads as a voxel remesh. Budget: 4 cm → 6 624 flesh tris (10 390 total, over); 3 cm → 13 k; 2 cm → 31 k; needs a quad decimator (a real project) to reach 4–9 k with detail where it matters.
- Cost ~300 lines (done). Best use: milestone-1 fallback and the watertight reference surface for checks.

### Rank 3 — **Sculpt layer on the SDF** (d) — the essential second stage of Rank 1, not a competitor
- `masses: [{joint, offset, radii, rot, blend, mode: add|subtract}]` (scapula, deltoid, cheek, brow ridge, belly; subtract = eye socket, mouth line, flank hollow), crease terms for brow/jaw planes, low-amplitude deterministic noise for asymmetry. A few lines per primitive in an SDF; impossible on a loft. Only route to secondary forms and to eye/mouth loops living in the head mesh (cage side: a ring of faces around the eye becomes an eye loop after CC).

### Rank 4 — Keep lofts, boolean/merge + retopo + relax (c)
- No robust mesh boolean without a dependency; booleans on 16-gon tubes make slivers at every intersection, and a retopo good enough to fix them *is* Rank 1's cage/wrap. Skip.

### Rank 5 — Catmull–Clark on the existing loft rings
- Keeps every ring and every intersection (`$S/proto_sn060cc1_flesh.png` shows the flavour). Does not address the diagnosis.

### Also considered
- Field-aligned quad remeshing (instant-meshes style): best wireframe from the SDF alone but 3–5 k lines and iterative; not justified while the skeleton already gives the flow direction for free (Rank 1 exploits exactly that). Dual contouring adds sharp hardware edges, not topology quality.

## 4. Prototype (Ranks 1 and 2) on the wolf — results and honest judgement

Code (scratch only): `$S/proto/field.js` (compile via the real engine; ring-exact mitred-slab SDF per volume with 4x
Catmull-Rom section supersampling; smooth-min union with per-chain k (head/tail 2x); grid sampling; trilinear field;
k-NN attribute transfer; skinned GLB writer through the engine's own glb.js/anim.js), `$S/proto/nets.js` (surface nets),
`$S/proto/cage.js` (cage + hole bridging + Catmull–Clark + shrink-wrap). `$S/proto/sdf_nets.js` is the first iteration
(two bugs found and fixed on the way: `smin(Infinity, …)` → NaN, and a per-segment clamped distance that dug pits on the
outside of every chain bend — the mitred-slab formulation fixes it).

Timings (this container, Node 22, one thread), wolf spec, flesh = body + head + tail + 4 legs + 4 paws:

| Variant | verts | faces | flesh tris | total tris (+3 766 parts) | valence-4 | time |
|---|---|---|---|---|---|---|
| Current engine (`node engine/cli.js example/wolf.json`) | 6 074 (GLB) | 4 955 | 4 494 | 8 260 | all quads, 0 anatomy loops | 2.5 s full build |
| A: nets, 4 cm cells | 3 314 | 3 312 q | 6 624 | 10 390 | 54 % | 1.6 s |
| A: nets, 3 cm | 6 649 | 6 688 q | 13 376 | 17 142 | 55 % | 22 s (first field) |
| A: nets, 2 cm | 15 718 | 15 784 q | 31 568 | 35 334 | 58 % | 66 s (first field) |
| **B: cage 12/8, 7 cm, CC1, wrap** | 2 474 | 2 472 q | **4 944** | **8 710** | **96.9 %** | **2.7 s** (2.4 s grid) |
| B: cage 12/8, 9 cm, CC1 | 1 994 | 1 992 q | 3 984 | 7 750 | 96.2 % | 2.5 s |
| B raw cage (before CC) | 606 | 632 (91 % q) | 1 208 | — | 96.7 % | — |
| B: CC2 (hero LOD) | 12 066 | 12 064 q | 24 128 | 27 894 | 99.4 % | 3.2 s |

Images:
- `$S/compare_q.png`, `$S/compare_side.png` — **current loft vs A vs B**, grey + wire, flesh only (the key pair).
- `$S/proto_cage_raw.png` — the quad cage: body rings, limbs bridged into 2x2 holes, head/tail serial joins.
- `$S/proto_cage_cc1_flesh.png`, `$S/proto_cage09_cc1_flesh.png`, `$S/proto_cage_cc2_flesh.png` — B at three densities.
- `$S/proto_netsB040_flesh.png`, `$S/proto_sn020_flesh.png` — A.
- `$S/compare_full_q.png` — full creature: current GLB (whole shading stack + AO) vs B's GLB (raw arc colours, no AO/stack).
- `$S/compare_posed.png`, `$S/proto_cage_cc1_posed.png`, `$S/current_posed.png` — both skinned GLBs posed at `move` t=0.3 s.
- `$S/orbit_cage/orbit_sheet.png` — `harness/outline.py` on B's GLB: "orbit holds… the head reads"; `harness/glbcheck.mjs`: OK, 3 clips.
- GLBs: `$S/proto/wolf_cage_cc1.glb`, `$S/proto/wolf_cage09_cc1.glb`, `$S/proto/wolf_netsB040.glb`.

Judgement (honest):
- **B removes the tube read.** In `compare_q.png` the current loft is unmistakably five tubes with a cylinder head plugged into a neck; B is one continuous surface with fillets at chest/leg, belly/thigh and neck, and its wireframe has loops around the shoulders and hips like a box-modelled base mesh. It skins and poses without tearing on transferred weights; the harness's orbit and contract tools accept the GLB unchanged.
- **B is not yet "hand-crafted".** It is a clean *clay blockout*: smooth, anonymous, no scapula, no cheek plane, no brow, no eye socket; CC1 still shows the 12-gon a little at the neck and the muzzle tip carries a 12-pole. Honest score: from "obviously procedural tubes" to "smooth generic base mesh" — about half the distance. The other half is the sculpt layer (Rank 3) plus eye/mouth face groups in the cage, both cheap once SDF and cage exist. Without it a reviewer will say "blobby".
- **A alone is not it.** Same seam-free surface, but the wireframe screams voxel remesh and it is over budget at any resolution that keeps the muzzle; keep it as the watertight reference surface and milestone-1 fallback.
- Colour and material transfer worked (saddle, pale chest, dark tail tip, pale paws survive); AO and the L1–L8 stack were not run on the prototype, which is why the current GLB looks richer in `compare_full_q.png` — integration, not a limitation.
- Not solved in the prototype: paws are still bolted parts (their SDF flares the leg end but the cage has no paw block); tufts/ears/eyes/nose unchanged; no adaptive density; no sculpt primitives.

## 5. Staged implementation plan (Rank 1, in this engine)

Principle: **the loft keeps being built; it stops being shipped.** Every check, anchor, tuft, junction and UV routine that walks `_rings/_ringIdx/_pts/_seatIdx` keeps its input. A new stage after `compile()` + checks replaces the flesh meshes that go to AO / shading / GLB.

Files:
- `engine/core/field.js` (new): `volumeSDF(mesh)` (mitred-slab, supersampled section — port of `$S/proto/field.js volSDF`), `meshSDF(mesh)` for parts, `unionField(spec, meshes)` with per-attach `blend`, grid sampler with per-source bbox culling, `field/grad/project`.
- `engine/core/cage.js` (new): `cageFromChains(spec, meshes)` → rings per chain, serial joins, `cutHole/bridge` for `attach` limbs (2x2 hole ↔ 8-sided limb; 3x3 ↔ 12), grid caps, `catmullClark(V, F, attrs)` subdividing skin/colour/partId with the mesh, `shrinkWrap`.
- `engine/core/surface.js` (new): orchestrates `spec.surface` = `loft` (today) | `nets` | `cage`: field → cage → CC → wrap → transfer; returns shipped flesh meshes + `partOfVertex`; original volumes flagged `_ship=false`.
- `engine/cli.js`: after `blendJunctionSkin` and `runChecks` (they need the loft), call `surface.build()`; hand shipped meshes to `applyUVs / bakeAO / shadeStack / writeGLB`. `part_spans`: one row per source volume/part from `partOfVertex` (vertices sorted by part so rows stay contiguous).
- `engine/core/checks.js`: new `surface_integrity` (manifold, watertight, no flipped faces, valence histogram, fold count on every clip frame via the existing `foldCount`); `mesh_integrity` also on the shipped mesh. `soft_mass` (`checks.js:188`) stays on the loft.
- `engine/core/shade.js`: the L1 seam pass (`:221`) becomes part-only; `junction` normal/skin blends keep running for parts that stay bolted (ears, tufts).
- `cards/SYNTAX.md`: `"surface"` root flag, per-attach `blend`, later `masses`.

Milestones:
1. **M1 (one agent pass): field + surface nets behind a flag.** `field.js` + nets extractor + attribute transfer + `surface: "nets"`; shipped mesh = nets flesh + untouched parts; `part_spans` per part; AO/stack/UV run on it. Acceptance: wolf, giant, raven build green; `glbcheck` OK; `outline.py` orbit holds; zero folded triangles on all clip frames; triangle total printed. Gives seam-free creatures immediately and the field every later stage needs.
2. **M2 (2–3 days): quad cage + CC + wrap** (`cage.js`): serial joins, limb holes, twins by mirroring cage rings, grid caps, CC-subdivided weights, `surface: "cage"` default; `surface_integrity`; budget from `cage_step` / CC level chosen against `tri_budget`.
3. **M3 (2 days): sculpt layer.** `masses` add/subtract, crease planes for brow/jaw, deterministic asymmetry noise; cage face groups for eye socket and mouth so loops form there; density bias (smaller cage step on head chains).
4. **M4 (1–2 days): parts into the surface.** Paws/hands as cage blocks bridged to the limb; ears as extruded face groups; tufts remain cards; retire junction normal copying for anything now continuous.
5. **M5: gates.** Recalibrate `soft_mass`, `thinnest_px48` and `harness/claims.json` `tri_budget` on the new surface; update the calibration set.
