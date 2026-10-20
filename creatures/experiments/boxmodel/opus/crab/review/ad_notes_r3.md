# Art-direction notes, round 3 (reconciled, K=3 pass)

Round-3 scores (Fable 5.1 / Opus 5.5): 6 FIX / 6 FIX.

**The owner authorised a stage-1 unlock for this pass, for these items only: the walking legs and the body height; the crown topology if turns allow.** Follow the unlock procedure in `REPAIR.md`, and change nothing else in stage 1. Every other rule holds: stage-2 IoU > 0.9 against the new stage 1, stage 3 never edits the base, all gates pass.

Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both reviewers' keep lists (appendix). Check every item in your own `--review` packet, which shows the idle pose, before you call it done.

## Must-fix, in order

1. **Spider legs (F major, O major).**
   - Fix: Stage 1 (unlock):
     - Shorten each below-knee segment 20-25%.
     - Add a second bend at about 65-70% of the leg, so the dactyl angles back in under the body. No knee may rise above the carapace top.
     - Splay the front pair about 20 deg forward and the rear pair about 25 deg back.
     - Lower the body so the underside is within about 20% of the body height of the ground.
     Keep the IK stance in the clips.
   - Check: az090: every leg shows two angles, no knee above the carapace, ground clearance 25% of the body height or less; hero: the four right legs are not parallel.
2. **Barnacles still read as pale nuts (F minor, O minor).**
   - Fix: Stage 3: 3-4 low truncated cones, sized 1-1.8x, tinted 20-40% toward the shell's shadow red, bases sunk 25-30%, all on the rear rim and none on top.
   - Check: back34: no pale nut and a clean top; float 0.
3. **The walk reads as idle (F minor, O minor).**
   - Fix: Stage 4: key an alternating tetrapod gait. Lift the swing tips 15% of the leg length, roll the body about 3 deg toward the stance side, and keep the planted tips fixed in world space.
   - Check: tip heights differ by at least 10% of the leg length between f006 and f012; planted tips do not move between consecutive frames.

## Should-fix

- F major, disputed (O: done in colour): the crown pole of about 30 spokes. If turns allow, rebuild it in stage 1 as 5-7 planes with no top vertex over 8 edges.
- F: merge the long pleat triangles of the side wall into 6-8 planes.

## Appendix: both round-3 reviews verbatim

### Fable 5.1: FIX 6
- round-2 item "Crown pie lid": **partly**. The shell's front and sides are big planes now, but the crown is untouched: the wire shows about 30 spokes on one pole with four concentric rings, and in colour the top reads as a smooth dome, not planes.
- round-2 item "Spidery legs": **not**. az090: four straight tapered stakes per side with one small bend at the top; the body still sits about a third of its height off the ground; no second bend, segments not shortened.
- round-2 item "Barnacles": **partly**. Dark holes on top and a rear-right cluster are in, but they are still pale grey hex prisms with visible base edges, and one sits on the top surface near the centre.
- round-2 item "F3 gait": **not**. move_f006/f012 read the same as idle_f012: no visible leg lift or body sway.
- **F1** [major/form] where: 1_beauty az090 and hero, all walking legs; 3_tech az090
  - what: The legs are long straight tapered spikes below a small top bend, standing as a row of near-vertical stakes; from the side the silhouette reads as a harvestman, and the body hangs a third of its height above the ground.
  - fix: Stage 2: shorten each below-knee segment 20-25% and add a second bend at ~70% of the leg so the dactyl angles back under the body; splay the front pair 20 deg forward and the rear pair 25 deg back. If IoU breaks, Stage 4: lower the stance in every clip with more knee bend, body 10% lower, and log it.
  - check: az090: every leg shows two angles and none is a stake; ground clearance 25% of body height or less; hero: the four right legs are not parallel.
- **F2** [major/form] where: 2_closeups front limb wire and barnacles wire (carapace top); the crown in every 4_posed frame; 1_beauty hero top of the shell
  - what: The carapace crown is still one pole vertex with about 30 radial spokes and four concentric rings; in colour it reads as a smooth plastic dome cap sitting over the faceted sides.
  - fix: Stage 2: flatten() the crown by sector into 5-7 big planes (front plateau, two front sides, two back sides, back, centre) and slide the ring vertices to uneven spacing so no top vertex has more than 8 edges; IoU > 0.9.
  - check: Wire: no pole fan and no concentric bands; hero/top colour: a few big planes with no ring or spoke shading.
- **F3** [minor/pieces] where: 1_beauty back34 and 3_tech back34, rear carapace; 2_closeups barnacles colour
  - what: Five pale grey hex prisms with visible base edges read as nuts against the red shell; one sits on the top surface near the centre-right.
  - fix: Stage 3: rebuild as 3-4 low truncated cones in mixed sizes (1-1.8x), tinted 20% toward the shell red and darker, bases sunk 30%, all on the rear rim.
  - check: back34: no pale nut and a clean top centre; float 0.
- **F4** [minor/animation] where: 4_posed move_f006/f007/f012/f013
  - what: The move frames read as idle; no leg lift or body shift is visible.
  - fix: Stage 4: key a tetrapod gait with tips lifted 15% of leg length and a body sway; planted tips fixed in world space.
  - check: Tip heights differ by 10% of leg length or more between f006 and f012; planted tips do not move between consecutive frames.
- **F5** [minor/form] where: 2_closeups barnacles wire, carapace side wall; 1_beauty hero, shell side
  - what: The side wall is a skirt of long thin triangles that show as dark pleat wedges in colour.
  - fix: Stage 2: merge the pleats into 6-8 wide planes (logged); IoU > 0.9.
  - check: Hero: the side wall reads as a few planes; sliver 6 or less.
- keep: Chunky claws with a real gap between the fingers that snap in the attack | az000/back34: the wide low shell with the claws in front and eye stalks with bulb eyes reads as a crab | Clean tech: hit, float, zfight, flip and drift all 0

### Opus 5.5: FIX 6
- round-2 item "Crown pie lid": **done**. hero and back34 colour: the crown shows a few big shell planes with no spoke or ring shading. The pole is still in the wire, but that check is waived.
- round-2 item "Spidery legs": **not**. az090: the lower segments are still long straight spikes standing as vertical stakes, with no second bend. The knees rise above the carapace and the body is about a third of its height off the ground.
- round-2 item "Barnacles": **partly**. back34: 5 cones with dark holes cluster on the rear edge and none sit on top, but they are still pale grey rings with visible bases.
- round-2 item "(should) F3 alternating gait": **not**. move_f006 and move_f012 are near-identical, with no visible leg lift.
- **O1** [major/silhouette] where: 1_beauty az090, all walking legs; 1_beauty hero, right side; 1_beauty back34
  - what: The walking legs are unchanged: long, straight, two-tone blades below a high knee, with no second bend. In az090 they stand as a row of vertical stakes with the knees above the carapace, holding the body a third of its height off the ground. In hero the four right legs are parallel spikes. From the side it reads as a harvestman.
  - fix: Stage 2: slide the lower-segment loops to shorten each below-knee segment 25%, and move the verts at 65% of the segment outward about 10% of its length to make a second bend so the tip angles back in. Splay the front pair 20° forward and the rear pair 25° back. Stage 4: in every clip, lower the root 12% of body height and flex the knees outward. If the IoU floor blocks the stage-2 part, unlock stage 1 for leg length only and log it in NOTES.md: stage 4 alone keeps the stake shape, and leg length is what makes the side read as a spider.
  - check: az090: every leg shows two angles, no knee is above the carapace top, and the underside is within 15% of body height of the ground. hero: the four right legs are not parallel.
- **O2** [minor/pieces] where: 1_beauty back34, rear edge of the carapace
  - what: The barnacles now cluster and have holes, but they are pale grey rings with hard base edges, the highest-contrast detail on the crab after the claws.
  - fix: Stage 3, piece_barnacles: tint 40% toward the shell's shadow red-grey, sink the bases a further 25%, and vary sizes 1-1.8×.
  - check: back34: the cluster still reads, does not outcontrast the claws, and shows no base edge; float 0.
- **O3** [minor/animation] where: 4_posed move_f006, f007, f012 and f013
  - what: The move frames are near-identical, with no leg lift or body sway, so the walk will read as a slide.
  - fix: Stage 4: key an alternating tetrapod gait, lifting the swing-set tips 15% of leg length, with a 3° body roll toward the stance side. Keep planted tips fixed in world space.
  - check: Tip heights differ by at least 10% of leg length between f006 and f012, and planted tips do not move between consecutive frames.
- keep: az000: the wide low shell with the dark claws held in front and eye stalks with bulb eyes reads as a crab | chunky claws with a real gap between the fingers that snap in the attack | the carapace colour now reads as a few big shell planes, and tech stays clean (hit, float, zfight, flip and drift all 0)

