# threejs-procedural-animals vs our box-model path: independent judgement (Fable 5.1)

Date 2026-10-03. Clone of majidmanzarpour/threejs-procedural-animals at c95ae49
(committed 2026-10-01), read-only. Paths below are relative to the clone root.
Evidence: README.md, llms.txt, docs/AUTHORING.md, core + bear/cheetah/wolf
sources, and the live showcase (bear and wolf, Orbit camera) viewed in the
browser; no image or GIF ships in the clone (a find over png/gif/jpg/mp4 returns
nothing; README.md:3 has a `<!-- demo video link -->` placeholder). Our side:
`experiments/boxmodel/k3_repair_r2.jpg` and `abc/k3/{bear,boar,wolf}/review/1_beauty.jpg`.

## 1. What it is

A runtime three.js library, 24 real-world species in 6 body plans, ~55k lines of
JS (`src/`), MIT, zero deps beyond three (package.json:78). Nothing is a mesh file:

- Body = hand-authored SDF primitives per species, placed relative to a
  hand-authored skeleton (docs/AUTHORING.md:72-99; bear: src/species/bear/sculpt.js,
  272 lines, ~110 primitives; wolf sculpt 339 lines, cheetah 158).
- Meshed by narrow-band surface nets at mm cell sizes (src/core/sdf/mesher.js:1-10),
  per-region jobs in Web Workers, 65-80k verts at the default tier
  (README.md:162-168; src/core/build/pipeline.js:20-26).
- Skinned with dual-quaternion skinning in a custom shader (src/core/render/dqs.js:1-13),
  weights computed from the SDF (src/core/build/weights.js).
- Coat = per-vertex colour/pattern/fur-length/flow painted in code
  (docs/AUTHORING.md:114-165; bear coat.js is 726 lines), rendered by a 1300-line
  custom GLSL material with instanced fur shells, silhouette fins, Kajiya-Kay
  hair lighting (src/core/render/coatMaterial.js:1-30; animalObject.js:4-9).
- Motion = procedural IK gait engines per body plan, 2.9k lines for quadrupeds
  alone (src/core/motion/quadruped.js:1-16), with actions, body language,
  events. No animation clips exist anywhere.
- Quality discipline is strong: numeric thresholds for joint pops, foot slide,
  pattern stretch, exposed holes (tools/thresholds.json:5-40), and a render-vs-photo
  silhouette overlay tool (tools/compare.mjs:1-15; docs/AUTHORING.md:344-348).

## 2. Is its output visually better than ours?

Yes, and by a lot, on its own terms. The live bear is a convincing
semi-realistic grizzly: correct proportions (hump, low head, flat plantigrade
feet, claws), shaggy coat with silhouette fins, dark paws, countershading. It
reads as an animal at once. The wolf likewise. Our k3 bear (`abc/k3/bear/review/1_beauty.jpg`)
is a brown wedge with a lighter muzzle plate, a two-plane face, boot paws, no
brow or eye socket; the boar's tusks and crest are stuck on; the wolf's ruff is
a collar. On a blind "does this look like a bear" test the library wins about
9/10 to our 6/10.

But the two are not in the same category, and this is the whole point:

- It is **not stylised low-poly**. The base skin is a smooth iso-surface at
  mm resolution; the look comes from 28-40 fur shells plus hair lighting
  (pipeline.js:21-25). Turn the shells off (crowd tier, or `setDebug('bare')`,
  README.md:150) and you get a smooth, untextured 6-8k-vertex blob, which is
  exactly the "lofted tube" look the owner rejected in our BRIEF.md section 1.
  Nothing in it has a designed plane, a crease, or a flat colour border on an
  edge loop.
- Its quality comes from **months of hand-tuned numbers per species**, not from
  a generator. The bear sculpt is dense with photo-measured constants and
  revision notes ("at 0.043 / 0.0668 the brow... stood 5 mm in front of it...
  the lids were buried in a tunnel", sculpt.js:15-16; "a ball-shaped pad read
  as a clown's nose", sculpt.js:142). AUTHORING.md:68-69 and 147-149 require
  measuring photos and citing the source next to each number. Every species
  also has a bespoke coat.js (11k lines total across species) and motion
  tables from gait research. This is a hand-made asset library whose medium
  happens to be code: the same loop we run (reference sheet, place, render,
  critique, fix), done by one person with far more iterations per animal.
- It covers **real animals only**. No bipeds, no humanoid, no fantasy. Our
  goblin, giant, character, raven_wyvern, owl and crab have no counterpart
  (owl would need the bird plan, crab the spider plan, each with a new sculpt).

So "better" means: realistic furry animals at 65k+ verts in a WebGL runtime
look better than our 1-3k-vert flat-shaded game assets. For the owner's actual
target (a Quaternius/Synty creature, BRIEF.md section 1) its output is off-brief.

## 3. Would adopting it (library, or bake/export to glTF) get us to shippable creatures faster?

No, for an engine that ships glTF:

- **There is no exporter.** A grep for gltf / glb / AnimationClip over src,
  tools and showcase returns nothing. The bake format is proprietary PANM
  (src/bake.js:1-2, llms.txt:155) and stores exactly the attribute arrays the
  custom shader reads (`pos nrm index skinIndex skinWeight comb tint coat pat
  surf`, pipeline.js:271). A glTF would carry pos/nrm/index/skin and one
  colour; the coat, fur length, flow, pattern and material-id attributes have
  no glTF home.
- **The look does not survive export.** The fur is a shader (shells + fins +
  Kajiya-Kay), not geometry; a glTF of the base skin is the bare blob above.
  Reproducing the look in Unity means porting the 1300-line coatMaterial to
  URP, plus DQS (glTF/Unity skin with LBS; the author chose DQS because LBS
  pinches at the hips, dqs.js:3-7).
- **Animation is procedural at runtime.** Idle/walk/attack would have to be
  sampled from the JS engine into clips (a sampler against `animal.update(dt)`
  and the bone matrices it writes, llms.txt:47), losing IK foot planting,
  terrain adaptation, look-at and the action blending that make it good.
- **Budget mismatch.** 65-80k verts and 5 draw calls per animal at the default
  tier; the crowd tier (5-8k) is the one that fits our budget and is the one
  with no fur.
- **No new creature comes for free.** Adding a species is the same hand labour
  (AUTHORING.md sections 3-9): a rig, 100-300 primitives measured from photos,
  a coat painter, gait tables, then pass the metrics. The LLM-in-the-loop
  authoring cost is the same order as our stages 1-4, with a larger surface.

Adopting it would only make sense if anyCreature became a three.js game with
realistic animals and dropped stylised, fantasy and biped creatures. That is a
different product.

## 4. What is worth stealing (techniques, not the library)

These address our stated failure modes (proportions missed, crude paws and
faces, repair rounds that stopped paying), and all are cheap to port to bpy:

1. **Sculpt relative to joints, never absolute** (AUTHORING.md:87-88;
   sculpt.js:218-262 builds every leg mass from `lerp(J.shoulderL, J.elbowL, t)`).
   Our stage 1 places base boxes by hand in world space, so proportions drift
   from the reference. Lock the rig joints from the reference sheet first,
   then derive every block's centre and length from joint pairs. This is the
   single change most likely to fix "hand-placed base shapes miss the
   reference proportions".
2. **Reference-photo silhouette overlay with a numeric gate** (tools/compare.mjs;
   AUTHORING.md:344-348: "a 5 % error in leg length or head size is visible").
   We already print a stage-1 IoU against the drawn blueprint; extend it to
   IoU against the GPT reference sheet per view and make it a gate, not a
   printout.
3. **Head in head-local coordinates with named landmarks** (sculpt.js:90-94:
   nose tip, eye centres, stop, chin, skull top, occiput measured from profile
   and frontal; rig.js:15,20 for the frame and the muzzle-length morph). Our
   faces are a flat wedge because nothing forces a stop, a brow, a zygomatic
   width or a lip line. A landmark table per creature (6-8 points) in stage 2
   gives the LLM something checkable.
4. **Feet as explicit parts**: palm, carpal pad, paw, five toes in an arc,
   claws as separate surfaces (sculpt.js:228-239, claws.js); the toe joint at
   the claw tip so the paw rolls at push-off (sculpt.js:21-23). Our boot paws
   need a palm plane, a toe row and claw pieces in stage 3 with the same joint
   convention.
5. **Eye depth rule**: the eyeball front must sit at the skin, at most 1.3 r
   from the centre, or the lids bury (AUTHORING.md:181-185). Directly portable
   as a stage-3 check for our separate eye piece.
6. **Quantified motion gates** (thresholds.json: foot slide, joint pops,
   contact gap, penetration) rather than reviewer eyes. We have stretch
   gauges; we lack slide/pop/penetration on the move clip (RESULTS.md: the
   crab's legs snapping between frames was found by a reviewer, not a gate).
7. **Revision notes next to the number** (sculpt.js:97-99, 139, 142). Our
   repair rounds re-derive the same lessons; a per-creature "what read wrong
   and what fixed it" log inside the program would compound across rounds.

Not worth porting: SDF meshing (we want planes, not iso-surfaces), fur shells,
DQS, the runtime gait engines (our clips are baked).

## 5. What we would lose by adopting it

The stylised flat-shaded look (the brief), the glTF-native pipeline, the Unity
engine side, bipeds and fantasy, 1-3k vertex budgets, baked clips the engine
already plays, and the kit/techqa gates that are now tuned. We would gain a
WebGL-only dependency, a shader port, and the same per-species hand labour.

## 6. Recommendation

**Ignore the library; port techniques 1-3 (joint-relative placement, sheet
silhouette IoU as a gate, head landmark table) into the box-model kit, and
keep the carve prototype running as the competing bet.** The library's visual
lead comes from a person iterating on photo-measured numbers plus a fur
shader, not from a method we lack. The method it has that we lack is
"everything hangs off measured joints, and a photo overlay is the gate", and
that is the cheap part.

**First concrete step:** in `experiments/boxmodel/kit/bmkit.py`, add a
`joints` table loaded from the reference sheet (side and front: shoulder,
elbow, wrist, hip, knee, hock, toe, nose, eye, occiput, tail base) and a
`block_between(ja, jb, t0, t1, radii)` helper that places stage-1 blocks by
joint pair. Rebuild the k3 bear's stage 1 with it and report side/front IoU
against `abc/k3/bear/reference/{side,front}.png` before and after. If IoU
moves by more than 0.05, roll it into WORKFLOW.md stage 1 as a gate.
