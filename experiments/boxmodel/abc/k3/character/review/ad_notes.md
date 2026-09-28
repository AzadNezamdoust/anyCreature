# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 6 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the big-head, thin-neck, slim-torso silhouette that matches 5_reference in every view; the eyes (round sclera, black pupil, thin outline flush on the front face); the palette at 4 colours; the clean rest-pose tech sheet.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gate FAILs (current kit, every keyed frame sampled).**
   - `FAIL s4 qa: posed fold-overs/collapses <= 0.5% of triangles and <= 0.5% of surface area — 95 (8.02% of tris, 1.75% of area)`
   - `FAIL s4 qa: no piece comes off the body in a pose (drift) — 2 shells — bind them with body= weights (or the bone under them)`
   - Likely cause: both come from the blink (idle frames 41-45, the eye-bone scale). 95 triangles is about the size of the two eye lenses plus pupils, and 2 shells are the two eye pieces driven by bones outside the skin. The packet's 3_tech shows no purple or brown at rest and the r04 notes had 0 folds at the old 20/40/60/80% samples, which skip frames 41-45.
   - Fix: Stage 4. Bind eye.L/eye.R and the pupils with `body=` weights (or `bone=head`) so they never leave the socket, and rebuild the blink so it cannot collapse the lens: scale the eye bone in z only, to no less than 0.35 of the lens height about the lens centre, with the same key on the pupil, so no lens triangle flips or goes degenerate. If any fold-over remains after that, it is the T-pose arm drop at the front armpit: Stage 2, add one logged loop across the shoulder between the clavicle ring and the upper-arm ring, and check that the armpit triangle sits below J['shoulder'].
   - Fallback if the scaled blink still drifts or folds: Stage 3, drop the eye scale and blink with a skin-coloured lid piece (a half-dome over the top of each lens, bound `bone=head`) rotated down 60 deg on frames 41-45; the eye pieces then keep a single static bind.
   - Check: stage-4 run: flips 0% / 0% area, drift 0, glbcheck OK; 4_posed idle_f024 shows both eyes in the sockets.

1. **Hands are paper paddles with a detached hook thumb (F major, O major).**
   - Where: 1_beauty hero and back34: the far hand is a flat blade edge-on. 2_closeups front limb colour and wire: the hand is a thin slab with a thin hook standing away from the palm. 5_reference side: the hand is a curled mitten with a visible thickness and the thumb lying against it.
   - Fix: Stage 2 (vertex moves): push the palm-side and back-side verts of each hand apart until the hand depth is about 40% of its width (it is under 20% now); pull the thumb's tip verts in against the palm edge so the gap between thumb and mitten is under 20% of the hand width, and move the thumb base verts down so the thumb starts at the wrist, not mid-hand; rotate the mitten's outer finger ring down about 20 deg so the fingers read slightly curled. The hand is tiny in every silhouette; IoU will hold.
   - Check: 1_beauty hero: the far hand reads as a block, not a line; 2_closeups front limb: thumb lies against a mitten with visible thickness; hit/float 0.

2. **Feet are flat flippers (F major, O minor).**
   - Where: 1_beauty hero, az090 and back34; 2_closeups hind limb: each foot is a long flat slab with a step, about 2.5x the ankle width long, no instep and no toe block. 5_reference side: a short foot with a rising instep and a toe end.
   - Fix: Stage 2: pull the toe-end verts back so the foot is about 1.8x the ankle width long; raise the foot's top verts at the ankle to make an instep that rises about 60% of the foot length behind the toes; add one logged partial loop across the foot at 30% of its length from the front and drop the toe end below it by about 25% of the foot height so a toe block reads. Stage 3 (optional if turns allow): three toe blocks per foot, rooted in the toe end, the big toe widest.
   - Check: 1_beauty az090: the foot has an instep and a toe step, no flipper; 4_posed move_f017: the feet stay planted.

3. **Brows and mouth float off the skull; the eye rim reads as a black disc edge-on (F major, O none).**
   - Where: 2_closeups head wire, top-left: the near brow bar sits above the sphere with a visible gap; the mouth line stands proud of the face. 1_beauty az090 and 2_closeups head colour: the far eye shows as a thick black rim disc stuck on the sphere.
   - Fix: Stage 3: sink each brow and the mouth piece so half its thickness is inside the head surface (move each piece along the local normal by -50% of its thickness); keep the front faces flush. On the eye lens, halve the depth of the black outline band (the side of the lens): paint the side faces skin and keep black only on the front annulus, so from the side the eye is a white dome with a thin dark edge as in 5_reference side.
   - Check: 2_closeups head wire: no gap under either brow or under the mouth; 1_beauty az090: no thick black disc on the far eye; float and z-fight 0.

4. **Hip seam reads as a briefs line (O minor).**
   - Where: 1_beauty az000 and hero: a horizontal crease at the hip ring where the legs meet the torso; the ring is narrower than the torso ring above.
   - Fix: Stage 2 (vertex moves): move the hip ring verts outward to the torso ring's width so the torso runs into the legs without a shelf; keep the crotch split.
   - Check: 1_beauty az000: no horizontal line across the hips at thumbnail size.

5. **Head is a uniform UV-sphere ring band (O minor, F minor).**
   - Where: 2_closeups head wire and 3_tech: evenly spaced ring bands from pole to pole.
   - Fix: Stage 2: `flatten` a brow plane above the eyes and a cheek plane each side; slide the lowest two head rings down 3% of head height and pull the chin ring forward 2% so the jaw is a slight plane; leave the crown alone. IoU > 0.9 (the head is the biggest silhouette mass; keep the moves under 3%).
   - Check: 2_closeups head wire: brow and cheek read as planes, not bands.

## Should-fix

- O: torso and limbs are constant-section tubes. Stage 2: scale the wrist rings to about 80% of the elbow rings and the ankle rings to about 80% of the knee rings.
- The punch reads mild (NOTES r04). Stage 4: add 10 deg more chest twist in attack f010 if the fold gate holds.

## Dropped

- None. Every item is reachable in stages 2-4.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6
- top_issues:
  - Hands are paper-thin paddles with a notch for a thumb; the far hand in hero and back34 is a flat blade edge-on
  - Brow and mouth pieces float off the skull as dark bars (head close-up, left brow and mouth); the far eye is seen as a dark rim disc stuck on the sphere
  - Feet are flat flipper slabs with a step, no toe block; head is a uniform ring-band sphere
- brief_fit / keep: Big round head, thin neck, slim torso, big rimmed eyes, brows, nose and mouth are all present; hands and feet miss the brief.

### Opus 5.5: FIX 6
- top_issues:
  - the thumb is a thin detached hook and the hand reads as a claw rather than a curled mitten (2_closeups front limb)
  - the head is a plain UV sphere with uniform ring bands, a machine tell; the feet are long flat flippers
  - the hard hip seam band reads as a briefs line despite 'no clothing detail'; torso and limbs are constant-section tubes
- brief_fit / keep: Clean tech and the best eyes (round sclera, black pupil, thin outline flush on the sphere), with a correct big-head, thin-neck silhouette. The hands and feet are weak.

### Kit gates (this build, current kit)
- kit_gate_fails:
  - FAIL s4 qa: posed fold-overs/collapses <= 0.5% of triangles and <= 0.5% of surface area — 95 (8.02% of tris, 1.75% of area)
  - FAIL s4 qa: no piece comes off the body in a pose (drift) — 2 shells — bind them with body= weights (or the bone under them)
- kit_warnings: none
- clip_triangles 0, clip_area_pct 0.0
