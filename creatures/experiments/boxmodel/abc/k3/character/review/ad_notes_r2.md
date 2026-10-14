# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 6 FIX / 5 FIX. Opus's 5 leaned on the hand "needles", which were a wire-overlay artifact (fixed in the kit, packet re-rendered in r19); read it as about 6.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (the minimum is already 0.918, bottom view: keep stage-2 moves on the feet small); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Eyes stay in the sockets through the blink (split outline torus + sclera dome, r08-r09); flips 0.07%, drift 0.
- Hands read as a block with thickness, not a paddle (r10-r11).
- Short foot with an instep and a toe block (r12).
- No briefs line at the hips (r15-r16); brow and cheek facets on the head (r17).
- Big round head, thin neck, slim torso; 4 colours; the eye read (white sclera, black pupil, outline) at thumbnail size.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit; clip_area_pct 0.0, stretch 0. z-fight is at its limit (2): any face piece you move must not add a z-fight face.

1. **Brows and mouth are straight bars that lift off the curved skull at their ends (F major).**
   - Where: 2_closeups head colour: the far brow arcs off the side of the sphere with sky behind it; the mouth bar's ends stand off the cheek. outline.L wire: the near brow's ends sit above the facets while its middle is seated. r14 fixed the middle, not the ends.
   - Fix: Stage 3: rebuild each brow and the mouth as a bent strip of 4 segments (5 vertex columns) whose every column is placed by projecting onto the head surface along its normal, then offset out 4.2 mm (brow) / 3.8 mm (mouth) and in -8 mm, the r14 numbers, so the bar follows the sphere. Keep the brow's slight arch. Pull the far brow 10% of its length toward the face centre so it does not wrap past the silhouette edge in az000.
   - Check: 2_closeups head colour and outline.L wire: no gap under either end of either brow or the mouth; 1_beauty az090: no bar standing off the profile; float 0, z-fight <= 2.

2. **Thumb is a detached thin wedge under a flat mitt (F major, O major).**
   - Where: 2_closeups front limb colour and wire: the thumb is a small thin wedge hanging below the palm with a gap to the mitten; head colour (left edge): the hand is a flat hook. Brief: thumb plus a curled mitten of fingers. 5_reference front: the thumb sits on the inner front edge of the hand, as thick as a finger.
   - Fix: Stage 2 (vertex moves): thicken the thumb lobe to about 30% of the hand width (it is under 15% now) by pushing its top and bottom verts apart; move its tip verts in so the gap to the mitten is under 10% of the hand width and the thumb lies along the palm's front edge, pointing forward (-Y), not down. Bend the mitten's last finger ring down another 15 deg so the fingers read curled. Keep the r11 plan outline simple (no self-intersection: move the tip layer before the root layer, never past it).
   - Check: 2_closeups front limb colour: a thumb as thick as the mitten's edge, lying against it; 1_beauty hero: hands read as hands, not hooks; s2 self-intersection 0, IoU > 0.9.

3. **Eye outline ring is heavy; sclera shows its 12-gon corners (F minor).**
   - Where: 2_closeups outline.L colour: the black ring is about 15% of the eye radius thick and the white sclera dome shows corners at close range. Brief and 5_reference front: a thin black outline.
   - Fix: Stage 3: thin the outline torus's front annulus to about 8% of the eye radius (move the inner wall out; keep the outer edge, keep the r09 1.5 mm lift off the skin); raise the sclera dome and the outline to 16 sides. The pupil stays.
   - Check: 2_closeups outline.L colour: a thin ring, a round sclera; 4_posed idle frames: eyes in their sockets; drift 0, flips <= 0.5%, triangles stay inside the 3,000 budget.

## Should-fix

- Feet: Stage 3 (if turns allow): three toe blocks per foot rooted in the r12 toe block, big toe widest (5_reference front shows toes). Do not move foot verts in stage 2 (bottom IoU is 0.918).
- Head crown still bands (r17 residual): Stage 2, `flatten` one plane on each side of the crown above the brow plane; moves under 2% of head height.

## Dropped

- O "needle slivers shoot out of both hands in every posed frame": wire-overlay render artifact, fixed in the kit and re-rendered (orchestrator note, NOTES r19).
- O "rests in an A-pose, not the briefed T-pose": the rest pose is a T-pose (2_closeups head and front limb show the arms horizontal; 5_reference top shows them out). The beauty views are posed at the idle clip's first frame, and the idle relaxes the arms, which is what a game idle does. Keep it.
- O "eyes are flat discs stuck on the sphere; from az090 they stand proud like buttons": 5_reference side shows the eyes bulging proud of the head in the same way; the thinner ring in item 3 covers the heavy look.
- Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6
- top_issues:
  - 2_closeups head wire / front limb wire: brows and mouth line are separate bars floating a visible gap off the skull; they need to sit on the surface.
  - 2_closeups front limb colour: hands are flat paddle mitts with no thumb; brief asks for thumb plus a curled mitten of fingers.
  - 2_closeups outline.L colour: the eye outline ring is thick and heavy compared with the brief's thin black outline, and the sclera is a faceted 12-gon that shows corners at close range.

### Opus 5.5: FIX 5
- top_issues:
  - 4_posed attack_f007/idle_f012/idle_f024/move_f009/move_f017: long needle slivers shoot out of both hands in every posed frame (stray weighted verts / thumb stretch)
  - 1_beauty az000/hero: rests in an A-pose with arms at ~45 degrees, not the briefed T-pose; hands are small mitts with a detached-looking thumb wedge
  - 2_closeups outline.L: eyes are flat discs stuck on the sphere; from az090 they stand proud of the head like buttons

### Orchestrator note
- The posed "needle slivers" at the hands were a wire-overlay render artifact (even offset), fixed in the kit; the packet was re-rendered in r19. Drop every needle/sliver-from-the-hands item.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_area_pct 0.0, stretch 0
