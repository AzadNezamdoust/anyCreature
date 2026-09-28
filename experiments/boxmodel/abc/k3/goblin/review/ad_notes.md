# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 5.5 FIX / 5 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the crouched body with arms to the knees, the belt with the chunky gold buckle, the tattered loincloth, three-fingered clawed hands and three-toed feet, long ears, fangs, and the clean rig (0 flips, 0 drift). Both reviewers agree the body is right and the head is the problem.

Kit gates: none failing. clip_area_pct 0.66 (4 triangles), below the 1.0 threshold: no item. There is no item 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

1. **The head is a dog muzzle with side eyes: no dome, no brow, no hooked nose, no grin (F major, O major).**
   - Where: 1_beauty hero, az090, az000; 2_closeups head: a long boxy snout, eyes set on the sides of the wedge, a thin dark mouth slot with fangs poking up from an underbite. 5_reference: a domed skull, heavy brow overhanging forward-facing eyes, a long nose hooking down, and a wide fanged grin curving up into the cheeks.
   - Fix, in three stages:
     - Stage 2 (vertex moves): pull the muzzle tip ring down by about 10% of head height and narrow it to 60% of its width so the snout ends in a hook, not a box; pull the brow verts above each socket forward 4% of head depth and down 2% so they overhang; move each eye socket's verts forward 5% of head length and inward 3% of head width so both eyes show from az000 under the brow; raise the crown verts 3% of head height for a dome. Keep every move inside the IoU floor and log the item partly done if it blocks.
     - Stage 3 (pieces): add piece_nose, a downward-hooking wedge rooted 30% into the muzzle tip, length about 25% of head length, tip below the mouth line; scale the eye lenses 1.3x and seat them under the new brow (float 0).
     - Stage 3 (paint): repaint the mouth as a wide dark band (`dark brown belt` colour) along the jaw edge loop that curves up at the corners into the cheek faces, two face rows wide at the corners, so it reads as a grin; scale the fangs 1.4x and seat them on the upper lip pointing down (a grin, not an underbite), the outer pair longer.
   - Check: 1_beauty az000 at thumbnail size: brow, two forward eyes, a hooked nose and a wide grin read; 1_beauty az090: the profile shows a hook at the nose tip and the mouth corner rises; nose and fang hit/float 0; IoU > 0.9.

2. **Recessed groove down the back of the skull, and a sliver seam along the jaw and throat (O major, F major).**
   - Where: 1_beauty back34: a vertical crease runs down the centre of the back of the head. 3_tech hero, az090, az000 and back34: yellow sliver lines from the ear base down the cheek to the throat, and at the jaw hinge.
   - Fix: Stage 2 (vertex moves): move the centre-line verts on the back of the skull outward to the level of their neighbours so the rear of the head is convex (`flatten` the two rear planes if needed). For the seam, slide the jaw-hinge loop so the long thin cheek triangles are split evenly (the sliver runs from the ear root to the throat: move its middle vert onto the line's midpoint and out 2% of head width).
   - Check: 1_beauty back34: no vertical crease on the skull; 3_tech: no yellow on the cheek or throat; slivers under 1%.

3. **Ears are oversized, swept back and blade-thin (F major, O major).**
   - Where: 1_beauty hero, az090; 5_reference top: the reference ears stand straight out sideways; ours sweep back at about 45 deg and read as thin blades edge-on; the far ear in hero is longer than the head.
   - Fix: Stage 2 (vertex moves): move each ear's tip verts forward by about 20% of the ear length (keeping x), so the ears point sideways as in 5_reference top; move the ear's rear-face verts back by 3% of head width at the base tapering to 1% at the tip so the ear has a thickness edge-on; do not shorten them (the brief asks for 0.8 m across the ears). If the top-view IoU blocks the full rotation, do what fits and log partly done.
   - Check: 5_reference top vs model top: the ears point sideways; 1_beauty az090: the ear has a visible thickness at the base.

4. **Loincloth side plates are slivers (O minor).**
   - Where: 3_tech az090 and back34: yellow lines along the side edges of both loincloth pieces; 1_beauty az090: the flaps read as paper.
   - Fix: Stage 3: rebuild cloth_front and cloth_back as quad-strip plates at least 0.02 m thick with the long side walls split once mid-height (the s3 lesson from giant), keeping the tattered bottom edge; tuck each inside the belt as now.
   - Check: 3_tech az090: no yellow on the loincloth; slivers lower than now; belt hit 0.

5. **No pot belly over the belt (O minor).**
   - Where: 1_beauty az090 and 5_reference side: the reference belly bulges forward over the belt; ours is a flat, light-green chest panel.
   - Fix: Stage 2 (vertex moves): push the belly ring verts between the chest and the belt forward by about 6% of body depth and out 3% each side, with the largest move just above the belt so the belt bites in.
   - Check: 1_beauty az090: a belly curve over the belt; IoU > 0.9.

## Should-fix

- F: the eyes still read small at thumbnail size after r01's r 0.03; item 1 scales them 1.3x. Check az000 before you go further.
- AD: the 4 pink triangles (0.66%) are probably the claws through the thigh in move_f009; drop the swing foot's forward reach 10% if the next run shows them.

## Dropped

- None. The nose and brow, which usually need stage 1, are reachable here with vertex moves on the muzzle and a rooted nose piece (item 1).

## Appendix: both reviews verbatim

### Fable 5.1: FIX 5.5
- top_issues:
  - head is a long dog/lizard muzzle with lateral eyes and no dome or heavy brow; the hooked nose is absent so it reads kobold, not goblin
  - ears are oversized swept-back blades out of scale with the head, and a sliver seam runs along the jaw/neck (yellow in hero and az000 heatmap)
  - mouth is a thin line with fangs poking from an underbite; the face has no expression at thumbnail size
- brief_fit / keep: Body, belt with gold buckle, three-fingered hands and three-toed feet are right; the head misses the brief (no dome, no hooked nose, no wide grin).

### Opus 5.5: FIX 5
- top_issues:
  - The head is a boxy dog-like muzzle, not a hooked nose, and the back of the skull (back34) has a recessed vertical groove that reads as a modelling error
  - The mouth seam is a dark crease wrapping the jaw, with a sliver line flagged at the jaw hinge; the far ear is extremely long and blade-thin in hero and az090
  - The side loincloth panels are thin plates (slivers in az090 and back34); the belly is a shaded chest panel with no pot over the belt
- brief_fit / keep: Has the right parts (arms to the knees, chunky gold buckle, long ears, fangs), but the head reads as a snouted dog-goblin and the face lacks a heavy brow.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 4 triangles (0.66% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 4, clip_area_pct 0.66
