# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; the rear view (az180) sits ON the floor at 0.900, so no stage-2 move may widen or deepen anything seen from behind. Stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Clip cut from 3.56% to 0.08% (r08: blade 100% to the hand bone, wing-root flank off the thigh). Keep those weights.
- Folded wing reads as a dark arm over a purple membrane with three spars and a thumb hook (az090, r10-r12).
- Hackles are wedge clumps, not dozens of needles (r13); hooked talons, bigger eye lens (r18).
- Tail taper to 80% and a notched, ribbed fin (r16-r17); concave throat (r15).
- Wyvern-first silhouette: two legs, wings as forelimbs, tail longer than the body (5_reference side match).

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit. clip_area_pct 0.08 (2 hackle triangles), stretch 0. Item 3 rebuilds the hackles: keep their roots off the under-jaw (r13 lesson) so the warning does not grow.

1. **Attack wing swings back as a stretched flat plank (O major).**
   - Where: 4_posed attack_f020: the blade points straight back along the body as one long flat box, edge-up; the mantle reads as a plank, not a spread wing. 5_reference front: the wing opens with the membrane facing out and the spars fanned.
   - Fix: Stage 4 (clip keys): on the mantle keys (f17-23) change the hand bone pose: less sweep back, more lift and roll: X up 45 deg (from 22), Z outward 30 deg (from 45), and roll the hand about its long axis about 50 deg so the membrane's broad face turns outward and up toward the camera; keep the arm bone at X 22 (the r14 lesson: larger arm rotations collapse the shoulder). If the blade still reads edge-on, add 10 deg more roll rather than more arm.
   - Check: 4_posed attack_f020: the purple membrane is seen face-on, raised above the back, spars fanned; fold-overs <= 0.5%; clip <= 0.1%; drift 0.

2. **Neck is short and upright with no S-curve; the head sits on the chest (O major; round 1 item 3 partly done).**
   - Where: 1_beauty az090 and hero: the head rides directly on the chest with only a slight throat dip. 5_reference side: a long S-neck, the base forward and low, the head carried up and forward.
   - Fix: Stage 4 (clip keys): stage 2 cannot do more (az180 IoU 0.900). Add a base neck pose to every key of all three clips: neck base bone pitched forward/down about 15 deg, the mid/upper neck bone pitched back/up about 25 deg, the head pitched down about 10 deg so the bill stays level. The beauty views are posed at the idle's first frame, so this shows in the packet. Check the throat and nape for folds; if the fold gate fails, use 10/18/7 deg.
   - Check: 1_beauty az090: an S between chest and skull, the head clearly in front of and above the chest; fold-overs <= 0.5%; hackle clip does not grow.

3. **Hackles still read as dark needle slivers (F major).**
   - Where: 2_closeups head colour/wire and 1_beauty hero: the throat and chest hackles are thin dark spikes splaying out; az000: spikes along the chest edge. 5_reference front: overlapping shaggy feather clumps lying down the throat.
   - Fix: Stage 3: rebuild the hackles as 5 clumps per side, each a broad flat-backed wedge: width about 70% of its length (from 45%), thickness 40% of the width, length 0.08-0.14 (shorter than now), lying along the throat (tips pointing down and back, no more than 25 deg off the surface), overlapping like shingles, roots sunk 0.03. Grade them: biggest at mid-throat.
   - Check: 2_closeups head colour: layered clumps, no spikes off the silhouette; slivers <= 2%; clip <= 0.1%.

4. **Dorsal spines are identical cones at even spacing (F major).**
   - Where: 1_beauty az090 and back34: a row of the same cream cones from the shoulders to the tail tip, evenly spaced. 5_reference side and rear: spines largest over the shoulders and back, shrinking toward the tail, and dark plates rather than bright cones.
   - Fix: Stage 3: grade spine height along the row: 1.0 at the shoulders, 0.85 mid-back, then down linearly to 0.3 at the fin root; grade spacing with it (wider at the back, closer on the tail). Lean each spine back 25 deg and flatten it sideways (width across 60% of width along), so it is a plate, not a cone. Paint them a dark grey-blue (an existing body colour) with only the tips cream, or all dark if the colour count allows.
   - Check: 1_beauty az090: a spine row that shrinks toward the tail, no two neighbours alike; hit/float 0.

5. **Eye is a flat amber lozenge with no brow (O minor).**
   - Where: 2_closeups head colour: the amber lens sits on a flat side plane; 5_reference side and front: a dark brow ridge overhangs the eye.
   - Fix: Stage 2 (vertex moves): move the 2-3 skull verts above each eye outward by about 4% of head width and forward 2% to make a brow ridge (head-only, not visible from behind; check az180). Stage 3: tilt the lens 15 deg forward so it looks along the bill.
   - Check: 2_closeups head colour: a shadowed brow over the eye; az180 IoU >= 0.900; eye float/z-fight 0.

## Should-fix

- F: the folded membrane is a single flat plate with spar ridges on it. Stage 3: paint the membrane between spars in two purple values (alternating bays) so the spars separate panels; thickening needs stage 2 and the rear IoU is at the floor (r09).
- Toe split into three points (r18 not done): needs a loop through the foot; skip unless turns allow.

## Dropped

- F "the thumb claw is a small hook floating at the shoulder": the thumb hook is bound to the arm bone and touches the wrist knuckle (float 0, r12/r14); 5_reference front puts the thumb claw at the folded wrist at shoulder height, as ours.
- Nothing needs stage 1; the full neck length would, and item 2 does it by pose.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups head colour / hackles: throat hackles and neck feathers are a scatter of thin dark needle slivers rather than shaggy clumps.
  - 1_beauty az090: dorsal spines along the back and tail are identical repeated cones at even spacing, not graded.
  - 2_closeups hind limb wire: the folded wing membrane is a single flat plate with spar ridges drawn on; the thumb claw is a small hook floating at the shoulder.

### Opus 5.5: FIX 6
- top_issues:
  - 4_posed attack_f020: the wing swings straight back as a stretched flat box, so the mantle reads as a plank, not a spread wing
  - 1_beauty az090: neck is short and upright with no S-curve; the head sits on the chest
  - 2_closeups head: eye is a flat amber lozenge with no brow; hackles are a few spikes

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 2 triangles (0.08% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_area_pct 0.08, stretch 0
