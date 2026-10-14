# threejs-procedural-animals: what to take (Opus seat, transfer angle)

Source: github.com/majidmanzarpour/threejs-procedural-animals at c95ae49 (shallow clone, read only).
Citations are `path:line` inside the clone. The licence is MIT (`LICENSE:1-3`), so we can port code
if we add a notice to our `THIRD-PARTY-NOTICES.md`.

## 1. What it is

The repo builds 24 animals at runtime in three.js. Each species is a folder of data and code:

- **Skeleton:** named joints, every number cited to a measurement (`src/species/bear/rig.js:1-60`).
- **Body:** about 100 signed-distance-field (SDF) primitives attached to bones (ellipsoids, round
  cones, lenses), joined by a smooth minimum (`src/core/sdf/sdf.js:10-15`,
  `src/species/bear/sculpt.js:44-260`).
- **Mesh:** narrow-band Surface Nets turn the field into a smooth skin of 6k to 130k vertices
  (`src/core/sdf/mesher.js:1-4`).
- **Surface:** colour per vertex, plus fur shells.
- **Motion:** data tables drive an IK gait engine (`src/core/motion/quadruped.js:1-90`,
  `src/species/bear/motion.js:39-74`).

The shared core is about 18.5k lines. One species is about 2k lines (the bear). The result looks
smooth, realistic and furred, which is the opposite of our faceted, flat-coloured low poly. What
transfers is the method around the mesh, not the mesh itself.

## 2. Our weaknesses mapped to their techniques

| our weakness | their technique | transfers? |
|---|---|---|
| base proportions miss the reference | They place the skeleton first and check it against the side photo before sculpting (`docs/AUTHORING.md:68-70`). Every primitive is placed relative to joints (`AUTHORING.md:87-88`). Proportions change through smooth spatial warps of the finished mesh and skeleton (`src/core/build/warp.js:1-17`, `:27-60`). | **Yes.** A warp only moves vertices, which our stage 2 already allows. |
| crude claws, paws, hands | Each claw is a generated tube along an arc: an elliptical section that tapers to a point, with the root buried in the toe (`src/species/bear/claws.js:10-11`, `:32-80`, `:82-147`). A paw is a pad plus toe spheres on an arc (`sculpt.js:228-240`). | **Yes**, as stage-3 piece generators. |
| crude faces | The head is built in its own local frame from named landmarks checked on profile and front photos: nose tip, eyes, stop, chin, skull top, occiput (`sculpt.js:93-100`, `AUTHORING.md:94-97`). An eye spec sets the almond opening (R, d), tilt, yaw and depth. A hard rule keeps the eyeball's front within 1.3 r of the skin (`src/core/sdf/eyeSocket.js:3-8`, `AUTHORING.md:179-190`). | **Yes** for the landmarks and the eye spec. No for the SDF eyelids. |
| joins between parts | Wide blend regions ("webs") at the shoulders and hips (`AUTHORING.md:92-93`). Limb weights are smooth (harmonic) fields, so the whole hip blends (`src/core/build/weights.js:1-11`). | Partly: the weighting idea, not the mesh. |
| colour | Hex values sampled from photos in neutral light, then desaturated. Countershading: dark back, light belly (`AUTHORING.md:148-151`). | A little. Our colour-from-sheet prototype already covers most of it. |
| animation | Gait tables: per speed, the stride frequency, duty factor, footfall offsets, foot lift and body bob. Feet plant on the ground and IK solves the legs (`quadruped.js:23-35`, `bear/motion.js:39-74`). An action is a set of overlapping smooth phase windows: crouch, then lunge, then recover, with the jaw opening inside the lunge (`src/core/motion/actions.js:410-421`, `:446-451`). | **Yes.** This is our biggest gap (see 3.1). |
| clipping, slivers, technical defects | One thresholds file covers foot slide, ground penetration, pops, jitter and skin stretch at joints. The rule is to fix the cause and never loosen a limit (`tools/thresholds.json:1-30`, `AUTHORING.md:340-343`). | **Yes.** We should add the motion checks we lack. |

Our current move clip shows the gap. `abc/k3/bear/bear.py:348-358` swings the thighs and upper
arms by 14-16 degrees each way, with no foot contact. The feet slide and float, but
ART_DIRECTOR.md:58 asks for "planted feet that don't slide".

## 3. Candidates, ranked by value for effort

### 3.1 Gait and attack clip generator (stage 4): do this first

**What it does.** A kit function writes the `move` clip from a gait row instead of hand keys:

- Each leg gets a phase offset, a duty factor D, a stride length and a swing lift.
- During stance the foot is pinned to the ground and slides back linearly. During swing it follows
  an arc.
- The body bobs at twice the stride frequency.
- Blender IK constraints on target empties solve the leg chains. The result is baked to FK keys with
  visual keying, so the glTF export holds plain rotations.

Defaults come from their tables:

- walk: D 0.6-0.76, offsets [FL, FR, HL, HR] = [0.25, 0.75, 0, 0.5] (`bear/motion.js:46-48`);
- trot: the diagonal legs move as pairs;
- biped: two legs at [0, 0.5].

It adds `attack_clip(style)` too. The phase windows are copied from `actions.js:410-451` and turned
into key frames on our bones:

- bite-lunge: crouch 0-0.3, lunge 0.3-0.48, jaw open 0.25-0.52;
- charge and headbutt: head low 0-0.35, lunge 0.35-0.55.

**Where it goes.**

- New file `experiments/boxmodel/kit/gait.py`. `bmkit.py` re-exports `gait_clip` and
  `attack_clip`.
- `BRIEF.md` §3 (stage 4) and §4 ("Rig") say `move` comes from `gait_clip`. Hand keys stay only for
  creatures without legs. Builders still write `idle` by hand.

**New checks.** `kit/techqa.py` gains two measures, shown in the packet like `clip`:

- `foot_slide`: how far a stance foot travels, divided by leg length; warn above 2 %
  (`thresholds.json:12-13`).
- `ground_pen`: the lowest posed vertex below z = 0; warn above 1 % of the height
  (`thresholds.json:16-17`).

**Effort:** 2-3 days. Getting the IK pole and bone roll right for each body plan (quadruped, biped,
crab-like with 6+ legs) is the hard part.

**Expected gain:** high on the "poses and clips" axis and for the engine, which needs feet that
plant. Small on the still-image score, because the judge sees only posed stills.

**Risks:**

- Blender IK flips on nearly straight legs. Add pole targets placed from `J`.
- Our bone rolls are `roll='auto'` (`bear.py:340`), so the bake must use visual transforms.
- Clips must stay 16-48 frames and loop. Generate exactly one stride per clip.

### 3.2 Proportion warps in stage 2: fixes proportions without unlocking stage 1

**What it does.**

- Port their five warp types (`legs`, `length`, `scaleAbout`, `girth`, `shift`, `warp.js:27-75`).
  Each one moves the vertices of the body bmesh **and** the joints in `J`, as theirs moves the
  skeleton with the mesh (`warp.js:3-6`).
- Add `fit_warps(body, blueprint)`: a small coordinate-descent search over leg scale, body length,
  head scale, neck shift and girth. It maximises the side, front and top IoU against
  `blueprint.json`, using the existing `masks` and `iou` (`kit/bmkit.py:803-825`).

**Where it goes.**

- New file `kit/warp.py`, called from a builder's `stage2()`.
- Gate change in `kit/bmkit.py:1301-1303`: a stage-2 change passes when the IoU against stage 1 is
  above 0.9 **or** the blueprint IoU improves on every view. Log the list of warps in
  `stage2_log.json`.
- Build the stage-3 pieces and the stage-4 rig after the warp, from the warped `J`.

**Why the lock allows it.** `assert_lock` checks connectivity only, not positions
(`bmkit.py:609-640`). A warp changes positions only, so only the IoU gate needs to change.

**Effort:** 1-1.5 days.

**Expected gain:** high. The K=2 round concluded that the remaining flaws "need stage 1
(proportions, paw and claw bases)" (RESULTS.md, K=2 section). A smooth warp changes proportions
while keeping the locked topology.

**Risk:** a large warp (above 15 %) stretches facets unevenly and can soften designed planes. Cap
the factors to 0.85-1.15, as they do ("a few to ~15 %", `warp.js:6`).

### 3.3 Skeleton first, as a stage 0 step

**What it does.**

- Before stage 1, the builder writes `J` with a source note for each number, as in
  `bear/rig.js:24-55`.
- `run.py --joints` draws the joints and bones over `reference/side.png` and `front.png`. The
  builder fixes `J` until the joints sit inside the reference.
- Stage 1 places its rings from `J`, for example `lerp(J[a], J[b], t)` (`AUTHORING.md:87-88`).

**Where it goes:** `kit/run.py` (a new `--joints` flag that reuses the blueprint drawing code at
`run.py:194-215`), `kit/refs.py` for the view scale, and `BRIEF.md` §3 ("Stage 0").

**Effort:** 0.5 day.

**Expected gain:** medium on proportions. The rig also matches the mesh, so joints bend better.

**Risk:** one extra round.

### 3.4 Generators for extremity and face pieces (stage 3)

**What it does.** A new `kit/parts.py` holds low-poly piece builders with parameters:

- `claw(root, dir, L, h0, w0, th0, th1, sides=4, segs=3)`: a tube along an arc, with a 4-sided
  section taller than it is wide, tapering to a point. The root is buried in the toe, and the arc
  is solved so the tip ends a set drop below the root (`claws.js:22-30`, `:44-80`, `:115-131`).
- `paw(wrist, mcp, toe, n_toes, spread, pad=True)`: a flat palm block plus toe blocks on an arc
  (`sculpt.js:228-240`; toe offsets at `claws.js:16-18`). It returns the claw roots for `claw()`.
- `eye(spec)`: their eye spec (`eyeSocket.js:3-8`: centre, r, yaw, pitch, almond R and d, tilt)
  built as a low-poly lens piece plus a pupil piece. `eye_check(body, spec)` enforces the depth
  rule: the front of the eyeball stays within 1.3 r of the skin (`AUTHORING.md:181-185`).
- `hand(wrist, n_fingers, ...)` for bipeds: the same idea, with finger boxes on an arc.

**Where it goes:** `kit/parts.py`, imported by `bmkit.py`. `BRIEF.md` §3 (stage 3) lists these as
the default for claws, paws, eyes and hands. Hand-built pieces stay allowed.

**Effort:** 2 days.

**Expected gain:** medium to high on crude extremities. It also removes a class of defects (needle
claws, sunk or floating eyes), because each generator is tested once.

**Risks:**

- Claws could look the same on every creature. Expose size, curve and count as parameters.
- Their claws are smooth tubes with 10+ sides. Ours must stay 3-5 sided to read as faceted.

### 3.5 Face landmarks in a head frame

**What it does.**

- Side marks in `blueprint.json` become required for the nose tip, stop, eye, brow, chin, skull
  top, occiput and ear base (their landmark set, `sculpt.js:93-96`).
- The run reports the mesh's distance to each mark in the side ortho view.
- It also checks that the brow overhangs the eye and that the profile has a step (the stop)
  between the skull and the muzzle.

**Where it goes:** `BRIEF.md` §3 (stage 0) and §2 rule 6; the blueprint overlay in `kit/run.py`
prints the error for each mark.

**Effort:** 1 day. **Expected gain:** medium on faces.

**Risk:** marks traced from a generated sheet can be wrong. The side view wins, as it does now.

### 3.6 Wider weight blending at shoulders and hips

**What it does.** After `skin()`, smooth the limb-root weights over a wider band, like their webs
(`AUTHORING.md:92-93`) and smooth limb fields (`weights.js:4-8`). In Blender this is a
vertex-group smooth limited to the root band (`bpy.ops.object.vertex_group_smooth`, or our own
Laplacian smoothing on the bmesh). The band width is a fraction of the upper-limb length, taken
from `J`.

**Where it goes:** `skin()` in `kit/bmkit.py:887`, with an optional `root_blend=0.3`.

**Effort:** 0.5 day. **Expected gain:** small to medium: fewer creased shoulders and hips in posed
frames.

**Risk:** softer creases also soften the planes we want. Apply it at the roots only.

### 3.7 One thresholds file for motion and deformation

**What it does.** Move the techqa limits, now scattered through the code, into
`kit/thresholds.json`, with a short note on each limit. Adopt their rule: fix the cause, and never
loosen a limit without a written reason (`AUTHORING.md:340-343`). Add the checks from 3.1.

**Where it goes:** `kit/techqa.py`, `kit/regress.py`, `WORKFLOW.md`.

**Effort:** 0.5 day. **Expected gain:** reliability, not score.

### 3.8 Colour: take the rules only

Take their rules: sample colours in neutral light, desaturate, and make the back darker than the
belly (`AUTHORING.md:148-151`), with the colour border on an edge loop (our rule 8). The
colour-from-sheet prototype already samples colours; add a desaturation clamp and a countershading
rule to the paint helper.

**Effort:** 0.25 day. **Expected gain:** small.

Their per-vertex gradients, fur shells and procedural patterns (`src/core/render/coatMaterial.js`)
do not fit 4-8 flat colours.

### Not recommended

- **The SDF sculpt and mesher as a stage-1 replacement.** Smooth-minimum unions are blobby by
  construction (`sdf.js:10-15`). A decimated SDF mesh gives the lofted tubes and blobby joins the
  owner already rejected in our engine creatures (BRIEF.md §1). Planar decimation of such a mesh
  gives random facets, not designed planes. The carve-from-sheet prototype is a better use of a 3D
  target. Effort 4-6 days, with low or negative expected gain.
- **Their skinning and rendering** (dual-quaternion skinning, seam skirts, fur). These are three.js
  runtime features. glTF uses linear skinning, and we export flat-shaded meshes.
- **Their engine as our runtime.** The style is different, it outputs its own `.animal` bake files
  rather than glTF (README, "Baking"), and its quality depends on 18k lines of tuned core.

## 4. Spec-driven generator vs LLM-written bpy

**Verdict: a hybrid.** Use spec-driven code for the technical, repeated parts. Keep LLM-written bpy
for the silhouette and the planes.

- **Their quality does not come from "spec in, animal out".** Each species is hand-tuned code. The
  bear sculpt is 272 lines of primitives. Many of them carry a comment that records a failed
  earlier value and the photo that corrected it (for example `sculpt.js:53-56`, `:66-69`,
  `:118-121`). Its 112 lines of gait data carry similar notes (`bear/motion.js:39-74`). The spec
  works because an 18k-line core turns each number into something that functions: IK, weights,
  eyes, claws.
- **Our engine is already spec-driven, and the owner rejected its look.** The repo README says each
  creature is "compiled from one JSON spec". The owner judged those creatures as lofted tubes
  (BRIEF.md §1). A spec gives reliability and consistency, but only the look its primitives
  allow, and smooth primitives cannot give designed planes.
- **Where a spec beats free bpy for us:** every part that has a right answer and recurs on every
  creature. That means skeleton placement, extremity pieces, eyes, gait and attack clips, and
  proportion warps. These are where our builds show defects (needle claws, sunk eyes, sliding
  feet), and where repair rounds stalled. RESULTS.md (K=2) found that small-part fixes "trade one
  flaw for another".
- **Where free bpy wins:** the torso, head and limb planes, which carry the hand-made look the
  judges score. Keep writing them by hand, but on a cited skeleton (3.3), with a warp fitter (3.2)
  to correct proportions after the lock.

## 5. Implementation order

1. **Warps.**
   - New `experiments/boxmodel/kit/warp.py` with `warp_legs`, `warp_length`, `warp_scale_about`,
     `warp_girth` and `warp_shift`, each acting on the bmesh vertices and on `J`. Add
     `fit_warps(body, J, blueprint, k_range=(0.85, 1.15))`.
   - In `kit/bmkit.py:1301-1303`, let the stage-2 IoU gate accept a blueprint-IoU improvement.
   - In `BRIEF.md` §3 (stage 2), allow warps and require them to be logged.
   - Validate on the bear, wolf and boar, which have the worst proportion notes.
2. **Gait and attack clips.**
   - New `experiments/boxmodel/kit/gait.py` with `gait_clip(rig, J, legs, row, frames=32)` and
     `attack_clip(rig, J, style, frames=32)`: IK solve, then bake to FK. Re-export from
     `kit/bmkit.py`.
   - In `kit/techqa.py`, add the `foot_slide` and `ground_pen` measures to `measure()`
     (`techqa.py:223`), with heat-map colours.
   - Update `BRIEF.md` §3 (stage 4) and §4 ("Rig").
   - Validate on the wolf (on its toes), the bear (flat-footed), the giant (biped) and the crab
     (6+ legs; it may need only the offsets table).
3. **Joint overlay.** `kit/run.py` gets the `--joints` overlay on the reference views, and
   `BRIEF.md` stage 0 requires a cited `J`.
4. **Piece generators.** New `experiments/boxmodel/kit/parts.py` with `claw`, `paw`, `hand`, `eye`
   and `eye_check`. `BRIEF.md` §3 (stage 3) lists them. Add a unit render in `kit/selftest/`.
5. **Face marks.** `BRIEF.md` and `kit/run.py`: required face marks, with the error printed for
   each mark.
6. **Root weights.** `kit/bmkit.py` `skin()`: optional root weight smoothing.
7. **Thresholds file.** New `kit/thresholds.json`, read by `techqa.py` and `regress.py`. Add the
   "fix the cause" rule to `WORKFLOW.md`.
8. **Licence.** Add the MIT notice to `THIRD-PARTY-NOTICES.md` for any ported code (warp formulas,
   claw arc solver, gait table defaults).

Measure each change with the existing blind A/B (round packets, shuffled key), one change at a
time. Items 3.2 and 3.4 are the two most likely to break the 6/10 plateau. Item 3.1 is what the
engine needs most. Do not touch `abc/c1` or `kit/carve.py`.
