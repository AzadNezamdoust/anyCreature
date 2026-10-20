# raven_wyvern (c1): art-director notes, team pass (Fable 5.1)

Packet: `review/1_beauty.jpg`, `2_closeups.jpg`, `3_tech.jpg`, `4_posed.jpg`, `5_reference.jpg`, `techqa.json`
(all gates pass: hit 0, float 0, z-fight 2 at the limit, slivers 1.4%, flips 0.27%/0.14%, drift 0, clip WARN 0.96% on the hackles).

**Score: 5.5 / 10. Verdict: FIX.**

It reads as a two-legged bird-dragon with folded wings, a long tail and a fin from every view, and the horns, pale bill tip,
amber eye and grey shank are the right colours. But it is a squat hen with two purple boards bolted to its flanks, and its
eyes sit on top of its skull. The reference is a tall stalking raven with the wings folded tight along the body; the model is
not that yet.

## Keep (must not regress)

- The tail: ring chain plus spade fin, long and readable from the side and the 3/4 back view (hero, back34).
- The bill tip and shank colour borders sit on loops (head close-up, front-limb close-up); the 7-colour palette works.
- Stage-4 gates: drift 0, spar z-fight at the limit, the mantle on the arm bone (attack_f020 shows the wing turning as one).

## Must-fix (ordered by visual damage)

### 1. The wing is a flat purple rectangle standing off the flank (Stage 2 + Stage 3)
- Where: hero and az090 (the wing is a slab from shoulder to past the hip, same height front and back); az000 and model-top
  in `5_reference.jpg` (the two blades stand ~5 cm off the body as vertical boards with a gap between wing and flank; the
  reference folds them tight with the thumb hook at shoulder height above the back line).
- Fix, Stage 2 (vertex moves on the blade, no new loops needed): taper the blade. Keep the leading edge at the shoulder, bring
  the lower-rear corner up and back so the trailing edge is a diagonal from under the shoulder to a point behind the hip
  (the reference's wing tip lands near the base of the tail, at belly height). Lower-rear corner: raise ~35% of the blade
  height, move back ~15% of body length. Tilt the blade's top edge inward until it touches the flank (move the top-edge
  verts ~5 cm = 25% of the torso half-width toward x=0; the bottom edge can stay out ~2 cm). The side-view IoU is safe:
  most of the blade overlaps the torso in projection.
- Fix, Stage 3 (repaint + spars): paint the top third of the blade (the folded arm and finger ridge) plumage #424653 so
  the purple is only the lower membrane bays, as the reference does; make the 3 spars radiate from the wrist (front-top
  corner of the blade) down and back across the purple, not parallel lines down the middle, and make them read: thicker
  (section 2.5 cm) and the darker plumage colour, not the near-purple black.
- Check: `1_beauty.jpg` az090: a tapered wing, dark on top, purple bays below with three radiating spars; az000: no
  daylight between the wing top edge and the flank. `5_reference.jpg` side pair.

### 2. STAGE-1 UNLOCK: the legs are too short; the creature squats like a hen (Stage 1)
- Where: `5_reference.jpg` side pair: ground-to-belly is ~35% of height in the reference and ~22% in the model; az000
  pair: the reference's shank is a tall column with a visible hock, the model's leg is a stump under a low belly. The
  hero view shows the belly almost on the feet.
- Why stages 2-4 cannot: lengthening the shank and raising the torso moves the whole body silhouette in every view; IoU
  against stage 1 would fall below 0.9.
- Fix, Stage 1: raise the torso (belly bottom) from ~0.31 to ~0.48 m (+17% of the 1.4 m height); lengthen the shank to
  match, with a reversed hock bend (hock knuckle ~0.40 m, shank leaning back 15 deg below it, foot forward of the hock as
  the reference side view shows). Keep head height, tail and wing socket where they are; keep the foot size (it is right).
  Re-lock, then re-run stages 2-4 (the stage-2 throat/face moves must still apply; the rig's leg bones need the new hock).
- Check: `5_reference.jpg` side and front pairs: belly line at a third of the height, a visible hock angle; `4_posed.jpg`
  move_f009/f017: the feet still plant, no knee pop.

### 3. The eyes sit on top of the skull, not in the face (Stage 3, plus Stage 2 brow)
- Where: head colour close-up and az000: the amber hexes are on the crown's front edge, in front of the horns, facing up;
  from the hero they read as two orange studs on a helmet. The reference eye is on the side of the head, under a frowning
  brow, just behind the bill base.
- Fix, Stage 3: reposition the eye lens to the side of the skull: ~40% of the head length behind the bill tip, at the level
  of the bill's top line, facing out and slightly forward (normal ~30 deg forward of +X), and ~25% larger. Stage 2: pull
  the brow verts above it out 1 cm and forward so there is a ledge over the eye (the angry raven look).
- Check: `2_closeups.jpg` head colour: an amber eye under a brow on the side of the head; `1_beauty.jpg` hero and az000:
  the eye visible from the 3/4 front, not from the top.

### 4. The hackles turn the chest into a bag of rocks (Stage 3)
- Where: hero and front-limb close-up: 10 big dark wedges on the throat and nape, the same colour as the body, so the whole
  chest reads as lumpy noise and the neck disappears; they are also every tech warning left (20 clip faces, 6 flips).
- Fix, Stage 3: fewer and placed, not scattered: 3 wedges per side at the throat only (under the jaw, hanging down and back
  along the stage-2 throat hollow), 10-12 cm long, 6-8 cm wide, rooted in the surface; remove the nape ones and let the
  dorsal spines carry the nape. Paint them one step lighter than the body (the bill-black #1c1c22 is wrong; use #4e5262 or
  the plumage with a 10% lift) so they read as a ruff, not as shadow.
- Check: `2_closeups.jpg` head colour: a ruff under the bill with the neck visible behind it; `3_tech.jpg`: no purple or
  pink on the throat; techqa hackles clip < 10, flip 0.

### 5. The bill is a short fat wedge; the raven bill is long and hooked (Stage 2)
- Where: head colour close-up and `5_reference.jpg` side pair: the reference bill is ~45% of the head length with a hooked
  tip; the model's is ~30%, blunt, with the pale tip covering the whole lower front.
- Fix, Stage 2: move the bill-tip ring forward ~4 cm (15% of head length) and down 1 cm, narrow the tip ring to half its
  width, drop the upper-tip verts 1 cm below the ridge line to hook it; slide the pale/black loop back so the pale region is
  the front 30% of the bill only (it is the front 50% now).
- Check: `2_closeups.jpg` head colour and wire: a long hooked bill with a small pale tip; `5_reference.jpg` side pair.

## Should-fix (short)

- Tail fin: it is a plain paddle. Stage 2: notch the trailing edge into 3 rays (the reference's fan); Stage 3: a thin
  plumage-coloured stripe along each ray (the ribs were dropped for slivers; paint them instead).
- Dorsal spines: 13 identical cones in a row (machine tell). Stage 3: grade them harder (largest over the shoulders,
  smallest at mid-tail), and lean them back 20 deg.
- Hero wire shows unstructured carve triangulation on the chest and skull; a `flatten` on the cheek and the chest front
  (Stage 2) would give two clean planes where the light catches.
- Attack clip: the lunge is barely a head nod (attack_f020). Stage 4: 20 cm more neck reach and a 10 deg body pitch.
