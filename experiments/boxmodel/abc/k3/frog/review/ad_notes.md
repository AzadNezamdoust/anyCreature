# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the big gold eyes on top of a wide flat head, the cream jaw and belly, the wide mouth line, the folded Z hind legs, the front legs with pad toes, the dark back spots, and the tongue lash in the attack. Both reviewers call this the closest to its brief; do not regress it.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Posed clipping warning at 4.32% of surface, and the hip fold-over (kit warning; F major, O major).**
   - `WARN s4 qa: 80 triangles (4.32% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek`
   - No gate fails. But 4.32% is far above the 1.0 threshold, so it is item 0. Likely cause: the idle blink is an eye retract (NOTES s4 r01), which pushes both gold lenses into the head turrets on the blink frames: two lenses are about 80 triangles. A second source is the hop (4_posed move_f012), where the extended thighs pass through the belly flank.
   - Fix: Stage 4 first: change the blink from a retract to a downward scale of the eye bone in z to no less than 0.4 (the lens stays in front of the turret) and cut the hop's thigh extension until the thigh stays outside the flank in move_f012. If the scaled blink still clips or folds, Stage 3: add a green lid piece (a half-dome cap over the top half of each lens, bound `bone=head`) and blink by rotating it down 70 deg on the blink frames, with the lens static.
   - Also: 3_tech hero shows a purple posed fold-over patch at the thigh/body junction (2 triangles, 0.41% of area, just under the 0.5% limit; both reviewers saw it). Stage 2: add one logged partial loop around the thigh root where it leaves the flank, so the hip has a vertex row to bend on; Stage 4: check the thigh weights fall off inside that loop, not across the belly.
   - Check: stage-4 run prints no pink warning above 1.0% and 0 fold-overs; 4_posed idle blink frame and move_f012 show no lens or thigh inside the body.

1. **Mouth line is a proud ribbon that pokes past the head corners (F major, O major).**
   - Where: 2_closeups head wire: a dense strip of tiny triangles stands off the jaw along the lip; 1_beauty az000 and the head close-up: the black bar ends stick out past the cheek silhouette at both corners.
   - Fix: Stage 2: add one logged loop along the lip ridge, offset about 1.5% of head length above the ridge edge, so a thin strip of faces runs the mouth's length. Stage 3: paint that strip black (`pupil and mouth`) and delete piece_mouth_bar. The strip ends where the ridge ends, so nothing can poke out.
   - Check: 2_closeups head wire: no floating strip along the lip; 1_beauty az000: the black line stops inside the cheek silhouette; slivers drop (the bar was the sliver source in s3 r01).

2. **Pupil wraps round the eye as a goggle stripe, and a green dome sits behind each eye (O major).**
   - Where: 1_beauty hero, az090, back34: the black band runs all the way round each gold ball, and a green turret dome shows behind and under each eye as a second dome. 5_reference: a black bar on the front of the eye only; the eye sits on a low rim.
   - Fix: Stage 3: paint the pupil band only on the faces whose normal points forward (n.y < -0.3), gold everywhere else on the lens. Stage 2 (vertex moves): lower the top verts of each eye turret by about 30% of the turret height so the gold ball dominates the top of the head; then Stage 3: move the lens down by the same amount so it stays seated and proud (float 0). The turrets are small; IoU holds.
   - Check: 1_beauty back34: no black band on the rear of the eye; 1_beauty hero: no green dome behind the gold ball; eye hit/float 0.

3. **Black arrow marks on the snout read as stray decals (F major).**
   - Where: 2_closeups head colour; 1_beauty hero and az000: two black chevrons on the snout top, one per side, larger than the reference's dot nostrils.
   - Fix: Stage 3 (paint only): remove the arrow paint; if nostrils are kept, paint one small face each at the snout tip (under 1.5% of head width, like 5_reference front), no larger.
   - Check: 1_beauty hero: no black marks on the snout above the mouth line except two dots at most.

4. **Hind feet show no webbing (O major).**
   - Where: 1_beauty hero and back34; 2_closeups hind limb: five separate toes with pad tips; the 3 mm web slabs from NOTES do not read.
   - Fix: Stage 3: widen each web slab so it spans from toe to neighbouring toe along 60% of the toe length (from the foot to 60% out), thickness 5 mm, and paint it green; keep the per-vertex rigid bind to foot.L/R (the s4 r02 fix) so it does not fold.
   - Check: 1_beauty back34 and 2_closeups hind limb: a green web fills between the hind toes; fold-overs stay 0 on the toes.

5. **Body reads as a box from the front and hangs with a gap under it (F minor, O major).**
   - Where: 1_beauty az000: the cream belly is a flat-fronted box with vertical sides; 1_beauty az090 and 5_reference side: a gap shows under the body between the hind legs where the reference belly sits on the ground.
   - Fix: Stage 2 (vertex moves): push the lower corner verts of the chest and belly rings outward and down by about 4% of body width so the belly is rounded in az000; lower the belly's centre-line verts between the hind legs by about 5% of body height to close the gap. Keep every move under the IoU floor; log the item partly done if the floor blocks it.
   - Check: 1_beauty az000: a rounded belly outline; az090: the gap under the body is at most a sliver of light.

## Should-fix

- F/O: the spots are small (NOTES s3 r03). Stage 3: scale the dome spots 1.6x and drop to 6 spots, sizes varied +-30%, as in 5_reference top.
- O: front toes are pad tipped but thin. Stage 3: thicken each front toe to 1.3x.

## Dropped (needs stage 1)

- O "stands too tall on long straight front legs, alert-upright rather than squat": the front-leg length and the body height are stage-1 base geometry, and lowering the body would break the 0.9 IoU floor. Item 5 recovers part of the squat by closing the gap under the belly; the leg length stays.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - Black arrow-shaped nostril marks on the snout read as stray decals at thumbnail size (2_closeups head)
  - Mouth line is a thin ribbon plate that stands proud of the jaw in wire (2_closeups head wire)
  - Posed fold-over patch at the hip in the hero heatmap; body reads as a box from the front (az000)
- brief_fit / keep: Closest to brief: big gold eyes with horizontal pupil band, wide mouth line, cream jaw and belly, straight front legs with pad toes, folded Z hind legs with long webbed feet, spots

### Opus 5.5: FIX 6
- top_issues:
  - Stands too tall on long straight front legs, so it reads alert-upright rather than squat, and the hind legs leave a big gap under the body (az090)
  - The pupil is a black band wrapped right round each eye (goggle stripe), and a green lid bump sits behind each eye as a second dome; the mouth-line bar pokes past the head at the corners (az000)
  - Hind feet have separate thin toes with no webbing; posed fold-over at the thigh-body junction (tech hero purple, move_f012)
- brief_fit / keep: Good: big gold bulging eyes on top of a wide head, cream jaw, black mouth line, dark back spots, folded Z hind legs; webbing is missing.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 80 triangles (4.32% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 80, clip_area_pct 4.32
