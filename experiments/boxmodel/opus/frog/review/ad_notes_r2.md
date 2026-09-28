# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Hip fold-over at the limit (F1 major, O2 minor).**
   - Fix: Stage 4: blend the pelvis and thigh weights on the hip ring (about 60/40), and reduce the hop's hip flexion by about 10-15 deg.
   - Check: flip <= 0.2% and no purple at the hips; 4_posed: the hop thigh has no neck.
2. **Mouth-groove slivers (F2 minor, O4 minor).**
   - Fix: Stage 2: slide the mouth-groove vertices to widen the needle triangles, and the needles on the back too.
   - Check: slivers <= 0.5%.
3. **Tongue (F4 minor, O5 minor).**
   - Fix: Stage 3: a thicker tongue with a rounded, sticky pad tip instead of a needle. The root stays inside the mouth at full extension (bind and keys).
   - Check: attack frame: reads as a sticky tongue with the root inside.
4. **Eye is a nut face-on (O1 major; the Fable keep list covers az090/hero, not az000).**
   - Fix: Stage 3: dome the gold face, raising its centre about 30% of the radius. Remove the darker bevel ring, painting it the same gold, and centre the pupil on the front.
   - Check: az000: the eyes read as domes, not nuts.

## Should-fix (a minor from one reviewer)

- O3: paint the light rim bands around the spots the base green.
- O6: a cream belly.
- F3: give the webbing a wedge section.
- F5: flatten the head into 4-6 facets per region.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- **F1** [major/animation] where: 3_tech az090 (purple wedge at the hip) and back34 (purple at both hips); 4_posed move_f012 near hind leg; techqa flip 10
  - what: The hip fold-over is only at the gate edge: flip 10 = 0.47% against the 0.5% limit, purple remains at both hips, and the near thigh narrows to a neck at the hip in the hop. The gate passes; my eye and the heatmap say the hip still folds.
  - fix: Stage 4: blend pelvis/thigh weights 80/20 on the second flank loop and cap the hip extension in the hop at 150°; if still purple, log a hip loop in stage 2.
  - check: flip ≤ 4, no purple at the hips in 3_tech, thigh keeps its section in move_f012.
- **F2** [minor/technical] where: 3_tech hero and az000 (yellow along the upper lip), az090/back34 (long thin yellow triangles on the back); sliver 34
  - what: The mouth-groove slivers from round 1 were not merged, and the back carries several needle triangles (1.6%, under the gate but visible).
  - fix: Stage 2: merge the lip slivers into the lip loop and collapse the long back triangles into the neighbouring facets.
  - check: sliver ≤ 10 with none on the lip in 3_tech.
- **F3** [minor/pieces] where: 2_closeups hind limb colour/wire (web between toes), 1_beauty back34 left hind foot
  - what: The webbing is closed now but is a thin sheet: its edge reads as a line, not a wedge.
  - fix: Stage 3: thicken the web to ≥ 30% of toe thickness at the toe roots, tapering to the free edge.
  - check: Hind limb close-up shows a visible thickness edge on the web; open 0 stays.
- **F4** [minor/pieces] where: 4_posed attack_f016 (tongue bar left of the mouth); techqa piece_tongue drift 1
  - what: The tongue leaves the body at full extension; in wire it is a thin flat bar. Drift is acceptable for a tongue lash only if the root stays inside the mouth.
  - fix: Stage 3/4: root the tongue ≥ 20% inside the mouth floor at full extension; thickness ≥ 0.3× its width.
  - check: Colour render of attack_f016 head: tongue root inside the mouth, no gap at the lip.
- **F5** [minor/form] where: 2_closeups head wire; triangles 2148
  - what: The head is still a dense triangulated shell; the round-1 flatten note (4-6 facets per brow/cheek/back, ~1600 tris) was not done.
  - fix: Stage 2: flatten brow, cheek and back into 4-6 big facets each.
  - check: triangle count ≤ 1700; head wire shows big planes.
- keep: squat pear body tilted up with the folded hind-leg Z and long webbed feet | gold dome eyes with the horizontal lozenge pupil and glint (no coin edge in az090/hero) | wide mouth line with the cream jaw; green/cream/gold palette with painted spots

### Opus 5.5: FIX 6
- **O1** [major/face] where: 1_beauty hero near eye and az000; 2_closeups head colour
  - what: The eyes are balls in profile, but face-on the near eye still reads as a flat octagonal nut: a uniform flat gold face, a darker bevel ring, and the pupil filling the middle. In az000 the pupils sit on the top-outer rim of each ball like black lids, so the eyes look up and away from the viewer.
  - fix: Stage 3, piece_eye: rebuild at 10 segments with 3 rings, the centre raised ≥ 35% of the radius (a true half-dome), seated 40% into the turret's top-front. Rotate the pupil and glint ~20° down and forward so they sit on the front face of the ball.
  - check: hero near eye: the shading falls off across the gold, with no flat octagon face or bevel ring; az000: the pupils read as lozenges on the face of the ball, not on its rim; az090 still reads as a ball.
- **O2** [minor/animation] where: 3_tech az090 and back34, purple at the rear hip and thigh; techqa flip 10
  - what: The hip fold-over is down from 32 to 10, but 10 is 0.47% against the 0.5% limit, and the purple is still there.
  - fix: Stage 4: extend the pelvis–thigh blend over one more flank loop (50/50, 80/20, 95/5) and cap the knee opening in the hop at ≤ 150°.
  - check: flip ≤ 5; no purple in 3_tech; the thigh keeps its section in move_f012.
- **O3** [minor/colour] where: 2_closeups hind limb colour, back; 1_beauty back34; 3_tech back34, yellow on the back
  - what: The spots are 4-sided insets framed by a light-green rim band. There are about 9 of them, they read as windows or panels, and the inset rims add slivers on the back.
  - fix: Stage 2: dissolve the inset rings. Stage 3: paint 5–7 irregular spots of mixed size, each 5+ sided, directly on the body faces.
  - check: hind close-up: no light frame around any spot; back34: 5–7 spots, none a parallelogram; no yellow on the back in 3_tech.
- **O4** [minor/technical] where: 3_tech hero and az000, along the mouth groove; techqa sliver 34 (1.6%)
  - what: Slivers still line the mouth groove. The black paint hides them, but the count sits near the 2% limit.
  - fix: Stage 2: collapse the short edges on the mouth-groove loop, merging the sliver verts into their neighbours.
  - check: no yellow along the mouth in 3_tech; sliver ≤ 1%.
- **O5** [minor/pieces] where: 4_posed attack_f016, tongue; techqa piece_tongue drift 1
  - what: The tongue shoots out as a thin pointed needle, so the attack reads as a sting rather than a sticky tongue.
  - fix: Stage 3: rebuild piece_tongue as a flat bar ≥ 0.3× its width, ending in a rounded pad 1.5× wide. Stage 4: root it on the jaw bone ≥ 20% inside the mouth.
  - check: attack_f016: the tongue ends in a rounded pad; its root stays inside the mouth in every attack frame.
- **O6** [minor/colour] where: 1_beauty az000, belly; 2_closeups front limb colour, underside
  - what: The belly is a khaki grey-tan that turns muddy brown in shadow instead of reading cream.
  - fix: Stage 3: repaint the belly a warm cream: +12% value, shifted toward yellow, about halfway to the toe-pad colour.
  - check: az000: the belly reads cream against the green; front-limb close-up: the underside is not brown.
- keep: az090: squat pear body tilted up, with the folded hind-leg Z | az000: wide black mouth line over the pale throat, with the eyes as the top of the silhouette | closed webbed feet with pale toe pads; the green/gold palette with the horizontal pupil

