# Art-direction notes, round 3 (reconciled, K=3 pass)

Round-3 scores (Fable 5.1 / Opus 5.5): 6 FIX / 7 FIX.

**The owner authorised a stage-1 unlock for this pass, for these items only: the head (fewer, bigger planes) and the hip ring.** Follow the unlock procedure in `REPAIR.md`, and change nothing else in stage 1. Every other rule holds: stage-2 IoU > 0.9 against the new stage 1, stage 3 never edits the base, all gates pass.

Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both reviewers' keep lists (appendix). Check every item in your own `--review` packet, which shows the idle pose, before you call it done.

## Must-fix, in order

1. **Hop leg deforms (F major: the shank stretches into a rod; O major: the thigh hangs on a neck).**
   - Fix: Stage 4: strip any translation or scale from the ankle and foot keys in the move clip so the shank keeps its rest length, and weight the shank ring 100% to the shank bone. Spread the pelvis-to-thigh blend over the hip ring and one loop each side (70/30, 50/50, 30/70), and cut the thigh extension in f010-f014 by about 20 deg. If a neck remains, add a loop at the hip (logged in stage 2, or in stage 1 through the unlock) bound 50/50.
   - Check: move_f012 wire: both shanks keep their rest length and section; the hip section is at least 70% of the thigh's widest section; flip stays at 4 or below.
2. **Toe pads poke out through the toe walls (F major; the orchestrator confirmed it on the 2nd and 3rd front toes).**
   - Fix: Stage 3: scale piece_pads 0.8x and seat each pad 40% deeper along the toe axis, so every pad facet stays inside the toe tip.
   - Check: front limb close-up at 2x zoom: no cream outside any toe tip; hit 0, float 0.
3. **Pupils sit on the top rim face-on (F minor, O minor).**
   - Fix: Stage 3: rotate piece_pupil and piece_glint about 20-25 deg down and forward on each ball, so gold shows above and below the lozenge from the front.
   - Check: az000: gold above each pupil; hero: the pupil still on the face of the ball.
4. **Spots read as windows (F minor, O minor).**
   - Fix: Remove the spot insets from stage 2: they are your own logged ops. Stage 3: paint 5-7 spots directly on body faces, each spanning 2-4 faces so its outline has 5 or more sides, in mixed sizes and not in rows.
   - Check: back34: 5-7 irregular spots, none a parallelogram, no light rims; sliver does not rise.
5. **Dense head shell (F minor, O minor).**
   - Fix: flatten() the brow, cheeks and back of the head into 4-6 planes each: stage 2, or fewer head loops through the stage-1 unlock.
   - Check: head colour: big planes; triangles 1800 or fewer.

## Should-fix

- O: repaint the belly about 12% lighter toward a warm cream.
- F: thicken piece_web to about 30% of the toe thickness at the roots.

## Appendix: both round-3 reviews verbatim

### Fable 5.1: FIX 6
- round-2 item "Hip fold-over": **done**. flip 2 (0.09%), no purple at the hips in 3_tech; the hop thigh keeps its section.
- round-2 item "Mouth-groove slivers": **done**. sliver 6 (0.27%); no yellow along the mouth in 3_tech; one tiny yellow tick remains at the near eye-turret base in back34.
- round-2 item "Tongue": **done**. attack_f016: a flat bar about 0.35x as thick as wide with a rounded pad tip, root inside the mouth; piece_tongue drift 0.
- round-2 item "Eye nut face-on": **partly**. Bevel ring gone and the gold shades as a ball in hero and az000, but in az000 both pupils still sit on the top-outer rim of the ball so the frog looks up and away.
- round-2 item "O3 spot rims": **not**. Spots are still 4-sided insets whose lit rim walls show as light-green bands (hind limb close-up, az090).
- round-2 item "O6 cream belly": **done**. az000/az090: belly and jaw read cream, not khaki.
- round-2 item "F3 web wedge": **partly**. The foot shows a tan side wall, but the web's free edge between toes is still a line.
- round-2 item "F5 flatten head": **not**. Triangle count 2252 (was 2148); head wire still a dense even shell.
- **F1** [major/animation] where: 4_posed move_f012, near hind leg
  - what: In the hop's extreme frame the near leg's segment between the knee block and the foot is pulled into a thin tapered rod about 1.5x the thigh's length and a quarter of its width, while the far leg keeps its section. The gauge measures fold-over, not stretch, so it stays clean; the eye is right.
  - fix: Stage 4: weight the shank ring 100% to the shank bone (no thigh/foot blend across it) and strip any translation or scale from the ankle/foot keys in the move clip so the shank keeps rest length; mirror the far leg's keys.
  - check: move_f012: both shanks the same length and section as at rest; flip stays 2 or less.
- **F2** [major/technical] where: 2_closeups front limb colour, near front foot, second and third toes (visible at 2x zoom)
  - what: A cream wedge of each toe-pad piece exits the toe's outer side wall just behind the pad, a pale fin through the toe.
  - fix: Stage 3: scale piece_pads 0.8x and seat each pad 40% deeper along the toe axis so every pad facet stays inside the toe tip.
  - check: Front limb close-up at 2x: no cream outside the toe tips; hit 0, float 0.
- **F3** [minor/face] where: 1_beauty az000, both eyes
  - what: Pupils sit on the top-outer rim of each eyeball, so face-on the frog looks up and sideways.
  - fix: Stage 3: rotate piece_pupil and piece_glint about 25 deg down and forward on each ball so the lozenge sits on the front face.
  - check: az000: both pupils read as lozenges on the ball's front; hero and az090 unchanged.
- **F4** [minor/colour] where: 2_closeups hind limb colour (back); 1_beauty az090 and back34
  - what: About nine 4-sided sunken panels whose inset walls catch light as light-green bands; they read as windows, not spots.
  - fix: Stage 2: dissolve the inset rings (logged). Stage 3: paint 5-7 irregular 5+-sided spots of mixed size directly on the body faces.
  - check: Hind close-up: no light rim on any spot; back34: no parallelogram spots; sliver does not rise.
- **F5** [minor/form] where: 2_closeups head wire and head colour
  - what: The head is a dense even shell (about 40 small facets visible) that reads as a smoothed procedural surface rather than planned low-poly planes.
  - fix: Stage 2: flatten brow, cheek and crown into 4-6 facets each; IoU > 0.9.
  - check: Head wire shows big planes; triangle count 1700 or less.
- **F6** [minor/pieces] where: 2_closeups hind limb colour, web between the toes
  - what: The web's free edge is a line; the sheet has no wedge section.
  - fix: Stage 3: thicken piece_web to at least 30% of toe thickness at the toe roots, tapering to the free edge.
  - check: Hind close-up: a visible thickness edge on the web; open 0.
- keep: az090: squat pear body tilted up, folded hind-leg Z, long webbed feet | Gold ball eyes with the horizontal lozenge pupil and glint; wide black mouth line over the cream jaw | Green/cream/gold palette with the cream belly; clean hips (flip 2) and tongue drift 0

### Opus 5.5: FIX 7
- round-2 item "Hip fold-over at the limit": **partly**. flip is 2 (0.09%) and there is no purple at the hips, but in move_f012 the hop thigh still hangs from a thin neck at the hip.
- round-2 item "Mouth-groove slivers": **done**. sliver is 6 (was 34), with no yellow along the mouth in 3_tech.
- round-2 item "Tongue": **done**. attack_f016: a flat bar ending in a rounded pad, rooted at the mouth.
- round-2 item "Eye is a nut face-on": **partly**. hero and the close-up: the gold now shades as a dome and the bevel ring is gone. az000: the pupils still sit on the top rim of each ball like black lids.
- round-2 item "(should) O3 spot rims": **partly**. The light rims are gone, but the spots are still about 9 dark 4-sided parallelograms (back34).
- round-2 item "(should) O6 cream belly": **partly**. The az000 belly reads light tan; the underside in the front-limb close-up is still brown.
- round-2 item "(should) F3 web wedge": **done**. back34 and the hind close-up: the web fills between the toes and no thin sheet edge shows.
- round-2 item "(should) F5 flatten the head": **not**. triangles 2252 (was 2148); the head wire is still a dense shell.
- **O1** [major/animation] where: 4_posed move_f012, near hind leg at the hip
  - what: At full hop extension the thigh hangs off the pelvis on a neck about 40% of the thigh's width, like a sausage on a string. The gauge passes (flip 2) because the faces thin without flipping; the eye is right.
  - fix: Stage 4: spread the pelvis-to-thigh blend over the hip ring and one loop each side (70/30, 50/50, 30/70). Cut the thigh extension in move f010-f014 by about 20° and let the shin and foot carry the reach. If a neck remains, stage 2: log one loop at the hip and bind it 50/50.
  - check: move_f012 wire: the hip section is at least 70% of the thigh's widest section; flip stays at 4 or below.
- **O2** [minor/face] where: 1_beauty az000, both eyes
  - what: The pupils sit on the top rim of each gold ball. Face-on they read as black lids or a scowl, not pupils.
  - fix: Stage 3: rotate piece_pupil and piece_glint about 20° down about each eye's lateral axis, so gold shows above and below each lozenge from the front. Keep them on the front half of the ball.
  - check: az000: gold is visible above each pupil; hero: the pupil is still on the face of the ball.
- **O3** [minor/colour] where: 1_beauty back34 and az090, back; 2_closeups hind limb colour
  - what: The spots are about 9 dark 4-sided parallelograms of similar size in rows, so they read as windows or panels.
  - fix: Stage 3: repaint 5-7 spots, each spanning 2-4 adjacent faces so its outline has 5 or more sides, in mixed sizes (1-2.5×) and not in rows.
  - check: back34: 5-7 irregular spots, none a parallelogram.
- **O4** [minor/form] where: 2_closeups head wire and head colour; techqa triangles 2252
  - what: The head is a dense triangulated shell, and its triangle count went up. The head top shows many small value shifts instead of big planes.
  - fix: Stage 2: flatten() the brow, cheeks and back into 4-6 planes each, and dissolve the extra edges (logged).
  - check: triangles 1800 or fewer; head colour shows big planes.
- **O5** [minor/colour] where: 1_beauty az000, belly; 2_closeups front limb colour, underside
  - what: The belly is khaki tan and turns brown in shadow instead of reading cream.
  - fix: Stage 3: repaint the belly +12% value toward a warm cream, halfway to the toe-pad colour.
  - check: az000: the belly reads cream; front-limb close-up: the underside is not brown.
- keep: az090: squat pear body tilted up with the folded hind-leg Z and long webbed feet | hero: gold dome eyes on turrets with the horizontal lozenge pupil and glint, and the wide black mouth line over the cream jaw | clean tech (hit, float, zfight and drift 0, slivers down to 6) and the sticky-pad tongue in the attack

