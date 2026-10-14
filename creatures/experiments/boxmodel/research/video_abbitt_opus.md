# Video review: Grant Abbitt, "Blender Low Poly Character: PS1 Style Modeling for Beginners"

Seat: Opus 5.5, read as a senior 3D character artist. Source: https://youtu.be/uIHuqFLa_X0 (19 min).
Worked from the auto-caption transcript only (not watched). The captions come in 2-minute blocks, so
timestamps are approximate (±1 min). Counts marked "derived" are worked out from the operations he names,
not stated by him.

**Not in the video:** the description promises "an easy UV map and texture"; the transcript ends at the
grey model (18:23 "Final Assembly"). There is no UV, texture, rigging or vertex-count discussion to take.

## 1. What the tutorial teaches

| time | step | what he does |
|---|---|---|
| 00:30–02:50 | reference | One drawing, used twice: front (rotated X 90) and a duplicate turned Z 90 for the side. Opacity lowered, both pushed behind/beside the work space, X-ray on. Centre line of the drawing on the world centre. |
| 02:50 | order | Starts with the head, and says in passing "often it's actually better to start with the chest". |
| 03:20–04:00 | mirror | Cube, one loop cut down the middle, delete half, Mirror modifier with clipping and on-cage. Repeated for every centre part. He forgets clipping twice and repairs it with scale-X-0. |
| 04:00–06:00 | head | Fit the **front** view first: box-select (through, in X-ray) and move whole rows; add horizontal loops one at a time where the outline turns (chin, jaw, cheekbone): about 3. Then fit the **side** view: move rows, rotate a whole ring. Then one extra vertical loop on the side, and the rounding trick: select a row, `GG` edge-slide out and back, so the section stops being square. |
| 06:00–06:40 | neck | Extrude the head's bottom face straight down and **into** where the torso will be. One optional loop; he cancels a second ("keep it simple"). |
| 06:40–08:30 | nose, eyes, ear | Nose: one loop round the head, extrude ONE face, scale it down. Eyes: shows inset + loops, then **undoes it** ("more complicated than we need"). Ear: inset two side faces, extrude, pull verts. |
| 09:15–10:40 | torso | New cube at the 3D cursor, mirror. Loops: one mid, one at the arm socket height, one at the waist; then loops in the side view "to make this a little more circular" with `GG`. |
| 10:40–12:10 | pelvis | A **separate** cube, not an extrusion: "PlayStation one graphics tended to have big blocky pieces". Optional loops for the bum and hips. Adds one loop only because the pelvis outline did not match the torso above it. |
| 12:16–14:10 | arms | One cube per segment (upper arm, forearm), scaled long, rotated to the reference in front and side view. Shoulder end scaled **up** so it buries in the torso; far end face scaled **down** (taper). Forearm: one mid loop scaled up (the forearm swell), wrist scaled thin in one axis only. Mentions an icosphere at the shoulder as the nicer option. Arms drawn held back "so it's easy to model and easy to rig". |
| 14:10–15:40 | hand | Thin cube, one loop, end face extruded twice with a rotate (a curved mitten), thumb extruded twice from a side face. |
| 15:46–16:50 | legs | Duplicate the arm segment, rescale; one loop + `GG`; duplicate again for the shin. Checks each overlap. |
| 16:50–17:40 | feet | Cube, front face extruded twice, one loop, toes pulled down, slight curve in top view. |
| 17:40–18:20 | overlap | Goes back and deepens the overlaps: "The overlap is there for the rigging. So when we move this arm around, it won't separate." |
| 18:20 | assembly | Mirror modifier on one limb part using the centre part as mirror object, copied to the other limb parts with Ctrl+L. |

Counts (derived):

- Limb segments are **4-sided** boxes, 2 end rings plus 0–1 mid ring, capped at both ends.
- Head: about 8 verts round a horizontal section (4 from the cube, +2 on the centre line, +2 from the side
  loop), about 5–6 rings in height. Torso the same, 4–5 rings. Pelvis 6 round, 2–3 rings.
- Whole figure: about 12 separate closed parts, roughly 350–450 triangles.
- Loops go only where an outline changes direction in one of the two views. He never adds a loop "for the joint":
  the joint is the gap between two parts.

Cross-section shaping, the whole of it: (1) non-uniform scale of a ring in one axis; (2) rotate a ring;
(3) slide a row out and back to bow a flat side. That is all.

## 2. What answers our problems, what does not

**Answers**

- **Junction topology, limb-to-torso flow (our hardest stage-1 problem).** Overlapping closed parts delete it.
  No bridge between a 4-sided limb and an 8-sided torso, no poles to place, no rule 4. Each part is a capped
  loft, which is exactly what `part_rings` already describes. This matches the owner's point: the implicit
  base is already a union of parts; welding them into one cage is the step that costs us and buys little.
- **Tube-like limbs, partly.** Not through his sections (a 4-sided box is cruder than ours) but through the
  structure: with separate parts the section may **jump** at a joint. Forearm wider than the elbow end of the
  upper arm, thigh mass sitting over the shin, shoulder knob over the arm. A welded loft must be continuous,
  which is why ours read as columns. `c2_wire.jpg` shows it: bear and wolf legs are one constant section with
  6–8 tight rings.
- **Ring bands / density.** His rule (a ring only where the outline turns) is the cure for our bear leg. With
  joints at part boundaries, the "2–3 loops per joint" rings disappear from the limbs.
- **Too much effort in eyes.** He blocks eyes out of the model entirely and takes nose and ear with one
  extrusion each. Supports the grey form-only cage and a hard cap on face budget.
- **Deformation.** Rigid parts cannot fold or stretch. Our open items (range-of-motion folding 3.4–4%, raised
  limbs stretching in the attack) are skinning artefacts of the welded cage and go away on rigid parts.
- **Fewer sides, oriented.** 4–5 sided limbs with a face (not a corner) toward the side and front cameras give
  bigger, cleaner flat-shaded planes than 6-sided tubes.

**Does not fit**

- **Flat shading without texture.** PS1 hid the intersection seam under a texture. On our untextured model
  the seam is a visible crease that slides in animation. Acceptable at shoulder, hip, neck base, wrist, ankle
  (real form breaks). Not acceptable mid-torso or mid-neck, so the spine stays one welded skinned part.
- **His shapes are below our bar.** Box limbs, mitten hands, ~400 triangles, human only. Nothing on quadruped
  haunch/scapula masses, muzzles or creature heads. Our `part_guide` masses are already richer.
- **Our gates.** "One closed shell, no self-intersection" and techqa pass-through/clipping fail by design on
  overlapping parts. They must be rewritten, not waived.
- **Manual GUI method.** Box-select-and-nudge against an image has no LLM equivalent; we already do it better
  with stations measured from masks.
- **UV/texture:** absent, and irrelevant to face-colour models.
- **Hidden triangles:** buried caps and root rings cost about 10–15% of the base budget. Fine inside 500–3,000.

## 3. Changes, ranked

**1. Stage 1 "parts mode": the base is N overlapping closed shells in one mesh object.**
- Kit: `part_shell(bm, k.guide_parts, part, sides, n, root_sink)` in `kit/bmkit.py`: lofts `part_rings`
  stations, caps both ends (root cap as a low dome: one extra ring at 0.6 scale, then a cap), returns the
  island. Parts: `torso` (+ neck + tail, welded, skinned as now), `head`, each limb chain (option
  `split='segments'` for one shell per bone on thick limbs: bear, giant, goblin).
- Gates in `cage_gates` / `report`: every island closed and manifold; island count == declared parts;
  self-intersection tested **within** an island only; new gate `overlap`: each child's root ring centre lies
  inside its parent by ≥ 0.3 × root width at rest and in the three ROM poses. `techqa` pass-through and
  clipping skip declared parent-child pairs. Lock hash unchanged (one object).
- Stage 4: limb and head islands bind rigid to their bone (or a single blended root ring); torso keeps `skin`.
- Gain: removes junction topology, poles, `bridge_uneven` at roots, the ears-in-the-IoU problem; ROM folding
  toward 0; lets sections jump at joints. Largest single win available from this video.
- Cost: medium-high (gates, techqa whitelist, bind path). Visual risk: sliding crease at shoulder/hip.
- Judgement (a): **yes for limb roots and the head; no for the spine, neck and tail.** It removes the hard
  problems at a visual cost that flat shading mostly hides, and it improves deformation at this triangle
  count rather than hurting it.

**2. Section step at every part boundary (BRIEF stage 1 rule + `PART` knob).**
- `PART['root_over'] = 1.2`: a child part's root section is ≥ 1.15–1.3 × its parent's section at that point
  (shoulder over arm, thigh over shin, forearm over wrist), sunk in. BRIEF: "a limb is 2–3 masses that
  overlap, never one loft".
- Gain: the direct fix for tube limbs. Cost: small. Needs change 1.

**3. Ring placement by profile, not by spacing (replaces Topology rule 2 for limbs).**
- BRIEF: a ring exists only where width, depth or centre offset changes by > 8% from the line between its
  neighbours. Default per limb segment: root, one belly ring at t ≈ 0.35–0.4, tip. No joint loops inside a
  rigid part. `topology()` gets a `ring_bands` measure: fail on 3+ consecutive rings within 8% of each other.
- Gain: kills the banded columns on bear and wolf legs; frees about 150–300 triangles. Cost: small.

**4. Side-count defaults for `part_rings` consumers (judgement (b)).**
- Take his counts as the floor, not the default: limb 4 sides when thinner than 8% of height (wolf lower
  leg, goblin forearm), 5 otherwise, 6 only for bear/giant thighs; head 8 round × 5–6 rings; torso 8;
  hands and feet 4. Always a face toward side and front (`u`, `w` are face normals, not corner directions),
  superellipse `p` from the station.
- His ring count (2–3 per segment) is right for rigid parts and too low for a welded bending limb.
- Gain: larger readable planes. Cost: small (a `sides=` default table in BRIEF and `part_shell`).

**5. Off-axis ring centres and ring tilt (`bow` on `part_shell`).**
- His only form tools are scale-one-axis, rotate-a-ring, slide-a-row. We have the first; add the other two:
  the belly ring's centre offset from the bone line (calf back, forearm out) and end rings tilted to the
  bisector of the joint. Read the offset from the station `centre`, never snap it to the bone.
- Gain: profile asymmetry, the other half of "not a tube". Cost: small.

**6. Order of work and detail freeze (judgement (c)).**
- Keep ours, not his: torso/pelvis first (he admits chest-first is better), then head mass, limbs,
  hand/foot blocks. Per part: fit side view, then front view, then round. Adopt his restraint: no eye, mouth
  or claw geometry before blockout sign-off; nose and ears are one extrusion each in the grey cage; the face
  gets ≤ 10% of triangles (tightens rule 7).
- Gain: stops the eye/detail overspend. Cost: BRIEF text only.

Validation-zone stops: the sliding-crease look and the clipping allowance are owner-taste gates; do not
self-ratify. Run changes 1–5 as a grey A/B and hand the gallery to the owner.

## 4. Verdict

**Partly useful.** As modelling instruction it is a beginner's GUI walkthrough well below our bar: box limbs,
no creature anatomy, no topology theory, and the promised UV/texture part is not in it. But its one structural
idea is the right one for an LLM-driven pipeline with an implicit, part-by-part base: build the creature as
overlapping closed parts, joined by burial instead of by topology. That removes our hardest automated problem
(limb-to-torso junctions), fixes posed folding, and makes non-tube limbs possible because sections may step at
joints. **First thing to try:** goblin and wolf in grey, `abc/c3/`, stage 1 in parts mode (torso+neck+tail
welded; head and limbs as rigid overlapping shells with changes 2–4), compared blind against the c2 cages on
`part_profiles` RMS, ROM fold %, and one Opus + one Sonnet looks-first review. PASS if profiles and fold both
improve and neither reviewer prefers c2; otherwise FAIL and keep the welded cage.
