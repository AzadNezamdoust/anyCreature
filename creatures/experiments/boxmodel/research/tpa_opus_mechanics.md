# threejs-procedural-animals: how it works (mechanics)

Source: https://github.com/majidmanzarpour/threejs-procedural-animals, commit c95ae49 (2026-10-01).
Citations are `path:line` in that clone. Read-only study; nothing was run.

## 0. One-paragraph answer

Each animal is a hand-written JS species module (570-2455 lines; wolf 1579) that declares a skeleton,
sculpts the body as a smooth union of 60-130 bone-tagged SDF primitives placed *relative to joints*,
and paints per-vertex coat fields. A generic core then meshes the SDF (narrow-band Surface Nets with
Newton projection onto the exact field), computes skin weights from the SDF and mesh topology
(harmonic limb fields, relaxed axial coordinate), applies seeded proportion warps to the finished
painted mesh, and renders it with dual-quaternion skinning plus instanced fur shells, silhouette
fin cards and a procedural eye shader. Motion is a data-table-driven per-body-plan engine
(gait tables, IK, springs, posture blending), not keyframes. Quality comes from the sculpt being
an implicit field (joins are free and smooth), from weights derived from that field, and from a
very large, heavily tuned shader + motion core (~37k lines). No glTF/FBX export exists.

## 1. The species "spec" (what an author writes)

There is no declarative schema file; a species is a JS module with a fixed shape
(`docs/AUTHORING.md:11-26`, worked example `src/species/wolf/index.js:10-92`):

| field | content | wolf example |
| --- | --- | --- |
| `id, name, latin, group, plan, covering, variants` | metadata; `plan` picks the motion engine (quadruped/bird/swimmer/snake/spider) | `index.js:11-24` |
| `variation(R, o)` | seeded RNG -> params: sex, age, size, morph, ~15 scalar knobs, plus a list of **warps** | `index.js:31-74` |
| `rig(params)` | joints (left side only, mirrored) + bone list + axial chain + limb blend fields | `rig.js`, contract `src/core/rig/rig.js:11-19` |
| `sculpt(m, rig, params)` | SDF primitives | `sculpt.js` (339 lines, 76 primitive call sites) |
| `regions(rig, params, Q)` | meshing jobs: cell sizes, overlapping head/body regions, eyelid patches, rigid jaw | `regions.js:28-57` |
| `coat(ctx)` | per-vertex tint/material id, pattern SDF, marks, fur length, comb direction, surface params | `coat.js` (749 lines) |
| `eyeSpecs`, `render` hints | eye geometry/look; shader knobs (strand density, clump, mark colour) | `index.js:79-107` |
| `motion` | gait table + feet/head/tail/ears/actions tuning + optional behaviour hooks | `motion.js:15-80`, schema `src/core/motion/quadruped.js:18-87` |
| `surfaces` (birds) | extra non-SDF geometry (feather cards) | `src/core/build/featherCards.js:11-13` |

`llms.txt` is the *consumer* API reference for agents (createAnimal/move/play/update contract,
`llms.txt:23-103`), not a species-authoring schema. Species registration: `registerSpecies` /
`addLoader` (`llms.txt:158`).

Units and frame: metres, bind pose on y = 0, facing +Z, left = +X; model one real-size reference
individual and let `variation()` warp it (`docs/AUTHORING.md:28-38`). `rig.unit` rescales every
internal distance relative to the cheetah so one core skins a rat and a horse (`AUTHORING.md:35-38`).

## 2. Build pipeline end to end

`src/core/build/pipeline.js` (header 1-2):

1. `prepare` (`pipeline.js:33-45`): seed -> `variation()` -> params (+ user `overrides`) ->
   `rig(params)` -> `SDFModel` -> `sculpt()` -> thin parts inflated at coarse tiers
   (`inflateThin`, 48-56) -> `regions()`.
2. Meshing jobs (`pipeline.js:58-60`, `mesh.js:13-33`), one Web Worker per job
   (`src/build.js:184-227`).
3. `finish` (`pipeline.js:66-188`): merge regions; optional fin-edge sharpening (92);
   **skin weights** (94); region cross-fade values (97-98); **seam measurement** (101);
   **coat painter** (103); **fur-slope limiter** (108-113); crowd-tier pattern prefilter
   (114, 209-246); extra surfaces appended (118-135); **proportion warps + size** applied to the
   finished mesh, skeleton, eyes and coat lengths (138-155); packed typed arrays out (157-187).

Everything is deterministic in (species, seed, options) so workers recompute `prepare` from the id
(`pipeline.js:4-5`). Quality tiers only change cell size multiplier, shell count, fins and eyelid
patches (`pipeline.js:20-26`). Build cost: hero 5.6 s, crowd 0.4 s single-thread (`llms.txt:71`).

## 3. Body parts -> mesh

### 3.1 SDF primitives (`src/core/sdf/sdf.js`)
- Types: ellipsoid (any axis/up frame), round cone (tapered capsule), lens (almond eyelid
  aperture), fin slab (planar or quadric-curved polygon extruded, tapering thickness)
  (`sdf.js:5-8, 23-101`).
- Every primitive carries `bone`, `group`, `part` (body / jaw / tongue...), `tag`, `carve`, and
  its **own blend radius `k`** (default 0.02 m) (`sdf.js:103-117`).
- Combination: polynomial smooth-min for unions, `-smin(-d, di, k)` for carvers
  (`sdf.js:10-15`, `sdf.js:194-197`). Carvers cut nostrils, ear cups, mouth, palate.
- Culling per super-cell keeps evaluation cheap (`sdf.js` `cull`, ~208-230; used at
  `mesher.js:26-38`).

Authoring rules that produce the silhouette (`AUTHORING.md:86-99`): sculpt relative to joints
(`lerp(J.shoulderL, J.elbowL, 0.4)`); **separate muscle masses** (shoulder, triceps, thigh,
hamstring, flank fold) with generous `k` instead of one cone per bone ("looks like a mannequin");
wide **web** primitives (k 0.05-0.06) blending limbs into the body; head modelled in head-local
coordinates measured from profile + frontal photos; eyes in sockets with lids; separate jaw part;
separate toes/pads or hoof + coronet + dew claws. Cheetah uses 128 primitives. The wolf even
sculpts its winter coat volume (ruff, cape, breeches, tail brush) before shells add hair
(`src/species/wolf/sculpt.js:1-4`). Face detail is measured, commented geometry: nose leather as
two tilted ellipsoids, a nostril 2D SDF with an alar-groove tail that is both carved and painted
(`wolf/sculpt.js:10-63`).

### 3.2 Mesher (`src/core/sdf/mesher.js`)
Narrow-band Surface Nets: coarse grid finds the active band, only those cells are refined
(`mesher.js:1-4, 18-59`); each vertex is **Newton-projected onto the true zero set** using
tetrahedral finite-difference gradients (`mesher.js:135-140`), and normals come from the analytic
field gradient (`mesher.js:205-213`). Result: smooth, accurate surfaces at any resolution with no
manual topology.

### 3.3 Regions, patches, seams (`mesh.js`, `seams.js`, species `regions.js`)
- A species splits the surface into overlapping jobs: body at ~0.7 % of shoulder height (wolf 5.2 mm),
  head at ~half that (2.5 mm), eyelid patches at ~1 mm, jaw as a rigid region
  (`AUTHORING.md:101-112`, `wolf/regions.js:1-2, 35-44`). Patches are re-meshed balls clipped out of
  the parent (`mesh.js:17-30`).
- Overlaps cross-fade with a species `fade()` function (`wolf/regions.js:45-55`).
- `measureSeams` sizes a render-time "skirt": the handed-over surface sinks under the one taking
  over so no slit shows at grazing angles (`seams.js:1-15, 25-40`).
- Fin slabs tagged `sharpen` get sub-cell knife edges, with normals carried through the Jacobian
  (`finEdges.js:1-14`).

### 3.4 Warps (`src/core/build/warp.js`)
Per-individual proportion changes (legs, torso length, head scale, girth, shift, uniform size) are
C1-smooth spatial warps applied *after* meshing, weighting and painting, to mesh and skeleton
together, so one sculpt serves all individuals and patterns ride along (`warp.js:1-15`;
wolf uses legs/length/head/pup-paw warps, `wolf/index.js:62-68`).

## 4. Skeleton and skinning

- `buildRig` mirrors `...L` joints, expands `{S}` bones, bone frame = head joint origin, +Y along
  the bone (`src/core/rig/rig.js:1-40`). Quadrupeds must use the engine's fixed joint names
  (`AUTHORING.md:46-53`); other plans have helper builders (`core/rig/bird.js`, `snake.js`...).
- **Weights from the SDF, not painted** (`src/core/build/weights.js:1-12`):
  - axial skin (spine/neck/tail): soft arc-length projection onto the axial polyline, then 24
    relaxation iterations over the mesh (`weights.js:233-246`);
  - limbs: a **harmonic membership field** per limb solved by SOR (omega 1.85, 320 iterations)
    between a limb core (1) and body skin (0), so a whole hip/shoulder blends
    (`weights.js:260-299`); inside a limb, bones blend by SDF distance to their primitives,
    distal joints narrowly (`weights.js:225-229`); proximal bones only pull body skin in the
    blend zone (`weights.js:315-326`);
  - appendages (ears) blend by SDF distance; rigid parts (jaw) take one bone; tail skin guarded
    from body/limbs (`weights.js:248-258`); `webTags` keep web primitives from anchoring a limb
    (`AUTHORING.md:64-66`).
- **Dual-quaternion skinning** in the vertex shader with a bind-space scale pre-pass (for
  breathing/compression); avoids LBS candy-wrapper collapse at hips and shoulders
  (`src/core/render/dqs.js:1-13`).

## 5. Coat, materials, eyes

- The coat painter returns per-vertex fields (`AUTHORING.md:114-126`): `tint` (rgb + material id
  among 12 materials, `coatKit.js:14`), `pattern` SDF (<0 inside) + `patternColor`, `mark` (crisp
  lines), `furLen`, `comb` (hair flow), `surf` (gloss, feature size, agouti, undercoat).
  Helpers: `poissonFeatures` / `featureDistance` grow spots and rosettes on the real surface,
  `distPolyline` for tear lines and stripes, `smoothField`, `projectToSurface`
  (`coatKit.js:17-101`).
- Colour practice: hex values sampled from neutral-light reference photos and cited in comments;
  countershading blended by normal and height; fbm low-frequency noise; patterns kept as SDFs so
  edges stay crisp at any tier (`AUTHORING.md:147-157`). Wolf: four morph palettes plus agouti
  strengths per region (`wolf/coat.js:22-51`), saddle extent and fbm raggedness (`coat.js:224, 400-408`).
- Fur-wall limiter: a Dijkstra sweep caps how fast hair length may rise over skin, so shells
  never stand up as a pad with a hard rim (`furSlope.js:1-20`, applied `pipeline.js:108-113`).
- Shader (`src/core/render/coatMaterial.js:1-31`): opaque DQS base with per-material
  micro-detail; **one instanced draw of 8-40 fur shells**, strands hashed in bind space and
  converging into clumps toward the tips (tufts with dark gaps, ragged spot edges); **silhouette
  fin cards** per vertex so outlines are made of hairs; undercoat optical depth; Kajiya-Kay hair
  lighting; pattern SDFs antialiased with `fwidth` (`coatMaterial.js:468-484`); agouti banding
  (`coatMaterial.js:726-736`). Crowd tier has no shells and prefilters pattern coverage into vertex
  colour (`pipeline.js:201-246`). Draw calls: 5 at hero/high, 1 at crowd
  (`animalObject.js:4-8`).
- Eyes are separate meshes with their own shader: refracted iris through a clear-coat cornea,
  round/slit/bar pupils reacting to light, blinking mammal lids or bird nictitating membrane
  (`src/core/render/eyes.js:1-12`); geometry shared with the sculpt's socket/almond aperture
  (`src/core/sdf/eyeSocket.js:1-8`). The guide calls wrong eyes the fastest way to kill a face and
  gives depth/roll/patch rules (`AUTHORING.md:179-192`).
- Feathers: real two-sided vane cards, one bone per flight feather, so wings fan and fold
  (`featherCards.js:1-13`). Fins: translucent membrane pass (`coatMaterial.js:1-3`).

## 6. Procedural motion (`src/core/motion/*`)

Five engines, one per body plan: quadruped 2868 lines, bird 3063, spider 1810, snake 1594,
swimmer 1047, plus action layers (`actions.js` 800, `birdActions.js`, `swimmerActions.js`).

Quadruped (`quadruped.js:1-16`):
- **Gait table** rows `{v, f, D, off[FL,FR,HL,HR], lift, bob, flex, lat, fold, heel, tail, drop,
  width}` blended by speed (`quadruped.js:25-36`, lookup `gaitAt` 792); wolf has 7 rows with cited
  research numbers (`wolf/motion.js:5-10, 27-35`).
- Dynamic similarity: tables at reference size, speeds indexed by v/sqrt(size), frequencies
  divided by sqrt(size) (`quadruped.js:13-16`; `AUTHORING.md:226-236`).
- Foot planting with terrain-aware swing paths, reach-limited stance, pantograph hind IK
  (`solveHind` 2002), foreleg IK with best-fit sliding scapula (`scapBestFit` 491, `solveFront`
  2079), digit roll / toe-off (2335), hoof sink and flip (`FOOT_DEFAULTS` 93-97).
- Secondary motion via critically damped `Spring`s for bank, pitch, height, girdles, spine flex,
  head and ears (`quadruped.js:621-628`); spring-chain tail (`integrateTail` 531); one-arc neck
  with head stabilisation rising with speed (`solveHead` 2510); breathing and panting.
- Actions (`actions.js:1-30`): a posture-parameter layer blended over locomotion every frame;
  postures (sit/lie/sleep/death) cross-fade, one-shots (jump/attack/hit/eat/drink) layer and
  interrupt by fixed arbitration rules; automatic idle (weight shifts, look-around, ear twitch).
  Species add behaviour through `hooks: { actions, update(P), pose }` (`AUTHORING.md:238-260`;
  wolf body language `wolf/motion.js:16-17`).
- Gameplay API is steering only: `move/moveTo/follow/lookAt/play`, events `footstep`, `attackHit`
  (`llms.txt:82-107`).

## 7. Baking / export (`src/bake.js`)

`.animal` = "PANM" magic, u32 version, JSON header, 8-aligned typed-array blobs of the packed build
(pos, nrm, index, skinIndex, skinWeight, comb, tint, coat, pat, surf) (`bake.js:1-48`,
`pipeline.js:271`). It caches the expensive build; the runtime (shaders, motion engine) is still
required. High-tier cheetah ~9 MB (4.4 MB gzip), loads in 10-25 ms (`llms.txt:155`). **No glTF,
FBX or baked animation clips**: grep for gltf/glb/fbx in `src` and `tools` finds nothing. All
appearance beyond vertex colour lives in custom GLSL.

## 8. What produces the visual quality

| quality | technique | where |
| --- | --- | --- |
| silhouette / proportions | joint-relative primitives, separate muscle masses, photo-measured head, sculpted fur volume; `compare.mjs` red silhouette overlay vs reference photos, "5 % leg/head error is visible" | `AUTHORING.md:86-99, 344-348` |
| smooth joins between parts | per-primitive smooth-min `k`, wide web primitives, Newton-projected Surface Nets, analytic normals | `sdf.js:10-15`, `mesher.js:135-213` |
| joins that stay smooth in motion | harmonic limb weights + DQS | `weights.js:260-299`, `dqs.js:1-13` |
| face / eyes | finer head region, 1 mm eyelid patches, carved nostrils painted as marks, dedicated eye shader | `wolf/regions.js`, `eyes.js:1-12` |
| coat / fur | instanced shells with clumping, silhouette fins, fur-slope limiter, agouti, Kajiya-Kay | `coatMaterial.js:1-31`, `furSlope.js` |
| colour patterns | pattern/mark as per-vertex SDFs, Poisson features on the surface, fbm noise, photo-sampled palettes | `coatKit.js:34-101`, `AUTHORING.md:147-157` |
| animation feel | research gait tables, dynamic similarity, IK with scapula slide, springs everywhere, posture blending, species hooks | `quadruped.js`, `actions.js` |
| gates | metrics: pops, jitter, foot slide, pattern stretch, eyes, fur walls, perf; "never loosen a threshold" | `tools/thresholds.json`, `AUTHORING.md:329-357` |

## 9. How an author (or LLM) adds an animal

- Files: `index.js, rig.js, sculpt.js, regions.js, coat.js, motion.js` (+ optional `behaviour.js`),
  plus one line in `src/registry.js` and one in `src/index.d.ts` (`AUTHORING.md:11-26`).
- Size: 570 (crow) to 2455 (lion) lines per species; wolf 1579 (sculpt 339, coat 749, behaviour
  160, motion 80, rig 87, regions 57, index 107). The core they plug into is ~37k lines.
- Parameters: ~15 seeded scalar knobs + warp list in `variation`; ~60-130 primitives each with
  centre/radii/axis/bone/group/part/k/tag; region cell sizes and fade; coat palettes per morph;
  motion: maxSpeed, accel, turnRate, gears, 4-8 gait rows of ~14 numbers, feet/head/tail/ears/body
  sections/actions tuning.
- Process prescribed: measure proportions from cited sources, check bind pose against a side
  photo **before** sculpting, then iterate `metrics.mjs` (PASS/FAIL), `render.mjs` contact sheets,
  and `compare.mjs` photo overlays, plus 6-seed variety checks (`AUTHORING.md:68-70, 329-378`).
  Reference photos live outside the repo with framing metadata (`AUTHORING.md:359-378`).
- Comments read as long iterative tuning against photos (e.g. nose tilt 24 -> 14 deg because a
  viewer above lost the nostrils, `wolf/sculpt.js:18-22`). It is expert hand authoring, not a
  generator from a short spec. An LLM could follow the same contract, but the guide expects
  photo-measured numbers and many render/compare iterations.

## 10. Licence and maturity

- MIT, (c) 2026 Majid Manzarpour and contributors (`LICENSE:1-5`, `package.json`). Reference photos
  are deliberately kept out of the repo (`AUTHORING.md:361-374`).
- `package.json` version 0.1.0, not yet on npm ("until it is published", `README.md` install
  section). Peer dep three >= 0.160, no other runtime deps. Latest commit 2026-10-01 by the author;
  the clone is shallow, so history depth is unknown.
- Breadth is real: 24 species, 6 body plans, variants, sexes, juveniles, 5 quality tiers, workers,
  baking, a test suite (`tools/test.mjs`), metrics with thresholds, render/compare tools and a
  showcase. Effectively single-author; three.js/WebGL only.

## 11. Relevance to experiments/boxmodel (brief)

- Their "hand-placed base shapes" are the same failure mode we have, solved by (a) placing every
  primitive relative to measured joints, (b) separate muscle and web masses with large blend radii,
  (c) a silhouette-overlay compare loop against photos. Points (a)-(c) transfer to bpy directly
  (metaballs or a voxel-remeshed union of ellipsoids/round cones reproduces smooth-min joins).
- Their face quality comes from a finer head region, carved plus *painted* nostrils/lips/eye rims,
  and a real eye model; paws come from separate toes and pads. Low-poly box modelling cannot copy
  the shader stack (shells, fins, Kajiya-Kay, pattern SDF AA), which is where much of their look lives.
- Their weights (harmonic limb fields, relaxed axial coordinate) and gait-table + IK motion are
  algorithms we could port to bpy as automatic weighting and clip generation; no exportable assets
  exist to reuse.
