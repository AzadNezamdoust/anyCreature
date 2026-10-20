# goblin (k3) build notes

Setting: reference/ present -> blueprint.json traced from the sheet (not redrawn). Sheet conflict: the top view shows the ears
straight out sideways, the side view shows them swept far back; front/side/rear agree on a diagonal ear, so the ear goes out AND back
(side view wins on proportions). Palette and clips follow the brief.

## Stage 1
- r01: Critique: 4 self-intersecting face pairs; limbs too narrow vs the front view (feet x 0.10-0.23, ref 0.10-0.31; hands x 0.29, ref 0.36).
  Diagnosis: the thigh tube's front faces cut the R0-R1 front-lower torso quad (debug HIT at (0.085,-0.01,0.38) x (0.137,-0.01,0.33)).
  Fix: move every leg section out ~0.03 (knee x 0.185, foot centred x 0.20) and splay the arms (elbow x 0.27, hand x 0.325, hand forward). 520 tris; IoU side/front/top 0.687/0.615/0.607.
  Result r02: gates PASS, 520 tris, IoU 0.694/0.651/0.586. Better stance; front now reads as spread limbs.
- r02: Critique: the ears (the goblin's main cue) read as thin planks in front/rear views; the sheet's ears are big flat triangles with a tall base.
  Diagnosis: the ear chain is one base quad (0.07 tall) tapering straight to the tip.
  Fix: ear chain flares to a 0.15-tall section at x 0.235, then 0.075, then the tip at (0.44, 0.32, 0.95), swept back.
  Result r03: PASS, 536 tris, IoU 0.726/0.703/0.575. Ears now read as big blades front and rear; the top view disagrees (logged).
- r03: Critique: the head reads as a bird skull / egg: in az090 the nose, bridge and forehead are one straight slope (a beak); in az000 the jaw tapers to a narrow chin, no face mass.
  Diagnosis: front seam P0 of R10-R12 lies on one line (no stop, no brow bulge); jaw/cheek P1-P2 of R7-R11 at x 0.07-0.11.
  Fix: R11 P0 pulled back to a nose-root notch (-0.30), R12 P0 brow bulged to -0.33, nose tip raised to a vertical front (0.70-0.785); jaw/cheek P1/P2 widened to x 0.09/0.135-0.155.
  Result r04: PASS, 536 tris, IoU 0.725/0.704/0.565. Side now shows brow, stop and a drooping nose; front jaw wider.
- r04: Critique: in az090 the arm hangs straight down the flank and hides the torso; the sheet's arms hang FORWARD, in front of the belly, hands ahead of the knees (the red side outline's front line is the arm, y -0.06, claws to y -0.14).
  Diagnosis: arm sections centred at y 0.07 (elbow) and -0.08 (hand).
  Fix: elbow to y 0.035, wrist -0.055, hand paddle -0.11 and tilted forward; J updated.
  Result r05: PASS, 536 tris, IoU 0.733/0.705/0.572. Arms now hang ahead of the flank in az090/hero.
- r05: Critique: the torso is a uniform column in az000/az180 (same width hip to shoulder); the sheet has a narrow chest, a round pot belly and a hollow behind the neck (red side dips to y 0.03 at z 0.83).
  Diagnosis: R1-R5 P2/P3 all at x 0.13-0.145; R6 back seam at y 0.11.
  Fix: chest R4 pinched to x 0.115, belly R3 swollen to x 0.148 / y -0.135, hips 0.128, neck back R6 P3-P5 pulled forward to y 0.085.
  Result r06: PASS, 536 tris, IoU 0.734/0.704/0.571. Front/rear now show a pinched chest over a round belly.
- r06: Critique: legs read as straight planks ending in small flat stubs (az000, hero); the sheet has knobby knees, thin ankles and big splayed feet (x 0.10-0.31).
  Diagnosis: knee sections no bigger than the thigh; ankle 0.058; foot toe section only 0.14 wide and straight ahead.
  Fix: knee sections 0.082x0.092, ankle 0.05x0.055, heel back to y 0.24, toe section 0.165 wide and splayed out (+0.02..0.035 in x).
  Result r07: PASS, 536 tris, IoU 0.737/0.698/0.582. Feet now broad and splayed; knees read as knobs.
- r07: Critique: in hero the lower face is a duck bill: the nose flanks and cheeks form one forward wedge, so the nose does not read as its own hooked block.
  Diagnosis: R9-R11 P1 (nose-root side) at y -0.28..-0.29 and x 0.035-0.045, P2 (cheek) receding to y -0.195..-0.225.
  Fix: nose base narrowed (P1 x 0.028-0.04) and set back to y -0.265..-0.27; cheeks P2 brought forward to -0.215..-0.237 so the face is a flatter plane with the nose standing off it.
  Result r08: PASS, 536 tris, IoU 0.737/0.698/0.581. The nose now stands off a flatter face in az000 and hero; reads as a goblin grey.
- r09: lock round (no geometry change): big head with hooked nose, swept blade ears, arms to the knees, pot belly, crouched legs all in the base.
  Result r09: LOCKED, 536 tris, 270 verts, edge sha256 89204defb40fb1ef. Stage 1 rounds: 9.

## Stage 2
- r01: Plan: neck loop (R5-R6) for the bend; grin loop in the chin band pushed in as a mouth slot; eye-socket inset under the brow; brow verts forward; belt band tucked under the belly.
  Result r01: gates PASS except slivers 26 (4.4%). Heatmap: the back of the skull (R7-R9 bands crowded 0.006-0.015 apart, the grin loop splitting them further) and the needle ear tip.
- r02: Critique: sliver gate FAIL. Diagnosis: back-seam/P4/P3 z of R6-R10 bunched; ear tip quad 0.012x0.008 at 0.16 from the last section.
  Fix: back verts of R6-R10 respaced evenly (vertex moves), grin loop recentred in its band and only its front (y < -0.15) pushed in; ear root/mid thickened x1.35-1.4, tip blunted x2.5.
  Result r02: all stage-2 gates PASS, 592 tris, min IoU vs s1 0.951. Front now shows eye sockets and a grin slot.
- r03: Fix: R10 back verts lowered (0.866/0.912/0.918) to clear the last slivers against R11; final stage-2 round with orbit.
  Result r03: stage-2 gates PASS with orbit, 592 tris, min IoU vs s1 0.951. Stage 2 rounds: 3.

## Stage 3
- r01: pieces: belt (R1-R2 band offset 5-24 mm), brass buckle frame (inset, centre bar from the mirror), tattered front/back loincloth
  plates tucked inside the belt, hex eye lens + pupil in the socket, 2 fangs/side, 3 clawed fingers/hand, 3 toe claws/foot; body painted
  skin / belly (border on the P1 column edges) / mouth slot. 8 colours, 1152 tris. FAIL hit: the belt is crossed by the loincloth in two
  separate patches (front and back flap in one object).
  Fix: the flaps become two pieces (cloth_front, cloth_back), each crossing the belt rim once.
  Result r02: all stage-3 gates PASS, 1152 tris, 8 colours. Critique: the belly colour does not show (torso front all skin green).
- r02: Diagnosis: the belly rule also required n.y < -0.45, which the R2-R4 front quads miss. Fix: belly = front faces (y < -0.04, |x| < 0.1) between z 0.435 and 0.665; final stage-3 round with orbit.
  Result r03: PASS with orbit, 1152 tris; belly reads light green over the belt. Stage 3 rounds: 3.

## Stage 4
- r01: rig (hips/spine/chest/neck/head, ears, 3-bone legs and arms, roll auto), heat skin, every piece bound with body weights (no drift);
  clips idle 48 (look left/right, ear twitch, fidget), move 33 (crouched sneak, knees lift in swing), attack 24 (right claw swipe).
  Also: eye lens enlarged to r 0.03 (hero showed a pin-point eye under the brow).
  Result r01: all gates PASS except posed flips 25 (2.17% tris, 0.06% area), all on piece_fingers: body-weight transfer mixes forearm/hand weights along the fingers.
- r02: Fix: fingers bound per vertex to the nearest bone (the hand bones), rigid; everything else keeps body weights.
  Result r02: all stage-4 gates PASS. Posed checks: move f009 lifts the swing foot back and up (knee flexes the right way), attack f006 raises the right claw forward-up, idle turns the head; no neck collapse in the wires.
- r03: final round with orbit + glbcheck (no change).

Triangles per stage: s1 536, s2 592, s3/s4 1152 total (8 colours). Rounds: s1 9, s2 3, s3 3, s4 3.

## Repair pass (K=1, from review/ad_notes.md; stage 1 locked)
- r10: baseline on the 2026-09-28 kit: every gate PASS (hit/float/zfight 0, slivers 14 = 1.2%, flips 0, drift 0), clip WARN 4 tris 0.66% (all on piece_belt, not the claws). No item 0.
- r11 (item 1, nose): Critique: az090 shows a horizontal box snout (nose top flat at z 0.785, vertical front, flat underside). Diagnosis: front-seam R10 P0 / R9 P0 sit level with the bridge. Fix: stage 2 moves R10 P0 down 0.045, R9 P0 down 0.05 and back 0.02, R9/R10 P1 in 0.008 and down 0.02, so the top slopes from the bridge and the tip drops below the mouth line. Result: better, the profile now slopes down to a tip; 1152 tris, IoU min 0.949, gates PASS.
- r12 (item 1, brow/dome): Critique: hero/az000 eyes sit on the sides of the wedge, no brow, flat crown. Diagnosis: eye quad R11-R12 P1-P2 faces sideways (P2 set back to y -0.24/-0.27); R12 level with the socket. Fix: R11 P2 forward 0.025, R12 P0-P2 forward 0.015-0.03 and down 0.009 (brow overhang), R13 forward/up, R14 dome up 0.014, socket inner verts in 0.008. Result: better, two eyes under a brow read from az000 and hero; IoU min 0.93, slivers 16 (1.4%), gates PASS.
- r13 (item 1 / should-fix eyes): Critique: the lenses look down at the floor (socket normal z -0.76) and read small. Diagnosis: the eye quad tilts because R11 sits behind R12. Fix: R11 P1/P2 forward 0.02/0.04 more; lens axis = socket normal with z x0.35; lens radii x1.3 (0.039). Result: better, big forward yellow eyes under the brow in az000 and hero; float/hit 0, gates PASS.
- r14 (item 1, grin): Critique: the mouth is a thin slot with fangs from an underbite (az000, az090). Diagnosis: only the two slot quads were painted; fangs rooted at the lower jaw. Fix: the upper-lip quad R8-R9 P1-P2 joins the dark mouth (the band rises from the nose root to the cheek corner), fangs x1.4 rooted in the R9 P1-P2 edge hanging down, outer pair longer. Result: much better, a wide fanged grin reads at az000 and hero; hit/float 0, gates PASS.
- r15 (item 1, nose piece): Critique: the nose still ends in a blunt wedge in az090. Diagnosis: the seam-tip wedge is 4 mm wide at the tip, nothing hooks. Fix: piece_nose (no mirror, 6-sided bent tube along the bridge line then down, tip z 0.612 below the mouth line), rooted 0.07 inside the nose, body weights. Result: better, a hooked nose in az090 and hero; 1186 tris, hit/float 0, gates PASS.
- r16 (item 2, skull groove): Critique: back34 shows a dark vertical strip down the back of the head. Diagnosis (first guess): the seam ridge P5 sits 0.045 behind P4, two flat rear planes. Fix: R8-R14 P4 back 0.008-0.014 (rounder rear). Result: no visible change; a valley scan (GOB_VAL) finds no concave edge on the rear skull. Re-diagnosis: in back34 the camera looks straight down the near ear (it sweeps back at ~50 deg toward the camera), so the tall thin blade seen end-on reads as a crease. The cure is item 3 (ear direction). The P4 move stays (harmless, IoU unchanged).
- r17 (item 3, ears): Fix: rear face of each ear section back 0.010 -> 0.003 (edge thickness) and the blade sheared forward up to 0.09 at the tip (x kept). Result: FAIL s2 IoU top 0.843. Sweep: thickness costs nothing; shear 0.03 -> 0.895, 0.02 -> 0.909 (the thin blade leaves its own top footprint).
- r18 (item 3): Fix: shear capped at 0.02. Result: gates PASS, IoU min 0.909 (top). Ears only ~5 deg more sideways; back34 still sees the near ear end-on. Items 2 (groove) and 3 are partly done: the IoU floor blocks the rotation.
- r19 (item 2, slivers): Critique: 3_tech hero/az090 yellow line from the ear base down the cheek to the throat, and at the jaw hinge. Diagnosis (GOB_DBG quad scan): cheek quad R9-R10 P2-P3 is a 5.7 deg needle (P3 only 0.014 apart in z); the lower-lip corner quad (R7 - grin loop, P1-P2) 4.8 deg; the eye-socket inner wall 3.1 deg after the r12 inward shift. Fix: R10 P3 up 0.011 and out 0.006, R11 P3 up 0.01, R7 P2 down 0.02, socket x-shift dropped. Result: cheek line gone; lip corner still 5.6 deg; socket top wall 1.7 deg. Slivers 16 (1.3%).
- r20 (item 2, slivers): Fix: R7 P1 down 0.012 and R7 P2 down 0.04 in all (the lip-corner band widens), socket floor 0.01 further back. Result: no yellow on the head in hero/az000 tech; body slivers 6 -> 2, total 12 (1.0%); IoU min 0.916; gates PASS.
- r21 (item 4, loincloth): Critique: 3_tech az090/back34 yellow along both flaps' side edges; flaps read as paper. Diagnosis: plate() is 9 mm thick with one long side cap (0.009 x 0.15-0.21, a 3 deg needle). Fix: plate3(), a quad strip with a mid-height row (side wall split once), 0.012 thick inside the belt and 0.021 thick at the tattered hem. Result: cloth slivers 10 -> 0, total slivers 2 (0.2%); but posed flips 4 (0.32%) appear on cloth_front (purple in az090 tech).
- r22 (item 4 follow-up): Diagnosis: the thicker plate's columns take different body weights (seam column hips, outer column thigh), so in move the sheet folds over. Fix: even_through(): after bind(body=), each cloth vertex takes the mean weights of the cloth vertices within 0.06. Result: flips 0 (0.00%/0.00%), drift 0.
- r23 (should-fix, clip): Critique: the pink clip warning (4 tris) is all on piece_belt (not the claws, as guessed). Tried the weight evening on the belt: worse (10). Fix instead: the belt stands off the skin 0.009-0.028 (was 0.005-0.024), buckle and the cloth's top row moved out with it (0.012-0.023, still inside the belt). Result: clip 0, hit/float/zfight 0, gates PASS.
- r24 (item 5, pot belly): Critique: az090 shows a flat chest panel, no belly over the belt. Diagnosis: R3 (belly ring) front at y -0.135, barely ahead of the belt band. Fix: R3 P0/P1 forward 0.02, P1/P2 out 0.008-0.01, R4 front forward 0.008. Result: slight curve only; IoU min 0.916.
- r25 (item 5): Fix: R3 P0/P1 forward 0.035/0.032 and down 0.005, sides out 0.012. Result: az090 and hero show a belly bulging over the belt; gates PASS, slivers 2 (0.2%), flips 0, clip 0.
- r26: final-candidate run with orbit + glbcheck, --review, --compare. Packet check: az000 brow, two forward eyes, hooked nose and wide grin read; az090 hooked profile, mouth corner rises; belly over belt. Remaining yellow in 3_tech: one needle behind the jaw at the neck (az090, back34).
- r27 (item 2, last sliver): Diagnosis: R6 P3 (0.085, 0.04, 0.79) sat on the line R6 P4 - R7 P3, so the neck quad split into a 5.8 deg needle. Fix: R6 P3 to (0.072, 0.03). Result: needle gone, but 4 body triangles clip in a pose (the jaw closes on the thinner neck).
- r28: Fix: R6 P3 to (0.079, 0.034). Result: clip 0; 2 slivers remain on the jaw side quad (R7 - grin loop, P2-P3; 5.7 deg).
- r29: Fix: R7 P3 z 0.795 -> 0.782 (the band at P3 widens). Result: slivers 0 (0.0%), clip 0, IoU min 0.916, gates PASS.
- r30: final with orbit + glbcheck, then --review and --compare. All gates PASS: hit/float/zfight 0, slivers 0 (0.0%), flips 2 (0.16% tris, 0.05% area; the R7 P3 move, posed only), drift 0, clip 0, lock PASS, IoU min 0.916 (top), glbcheck OK. 3_tech is clean grey. 1242 tris. Repair rounds r10-r30.

## Repair pass K=2 (from review/ad_notes_r2.md; stage 1 locked)
- r100: baseline: every gate PASS (hit/float/zfight 0, slivers 0, flips 2 = 0.16%/0.05%, drift 0, clip 0). No item 0.
- r101: diagnostic (GOB_FACE dump of the mouth faces): the dark box is the upper-lip quad R8-R9 P1-P2 (face normal (0.72,-0.7), so it shows as a slot in az090); the real opening is the grin-loop band (ms-R8), a thin gap.
- r102 (item 1): Fix: upper-lip quad back to skin green (dropped from MOUTH); piece_fangs gains 5 upper teeth per side seated 40% into the R8 lip edge and 2 small lower teeth per side on the lower lip; fangs kept. Result: az000 reads as a toothy grin with green lips; az090 still a deep dark corner; clip WARN 6 tris on the teeth.
- r103 (item 1): Diagnosis: the ms-R8 gap at the mouth corner is 0.055 tall. Fix (stage 2): the grin-loop front verts rise 0.003 at the seam to 0.016 at the corner. Result: az090 now a thin dark line; clip 0; IoU min 0.916.
- r104 (item 1): upper teeth read as a stipple; length 0.02 -> 0.03, radius 0.008. Result: 3 flips + 2 clip on piece_fangs.
- r105: Diagnosis: a tooth took lip and jaw weights at either end. Fix: even_through(fangs, rad 0.03). Result: flips on fangs 0; clip 2 remains.
- r106: Fix: upper-tooth tips lean 0.003 forward and reach 0.52 L down, clear of the raised lower lip. Result: clip 0, flips 2 (body only).
- r107 (item 2): Fix: piece_cloth_hip, a plate3 panel (both ends capped) on each hip under the belt from the front flap's outer edge round to the back flap's, tattered 3-point hem flared ~0.03 out over the thigh; front/back flap hems flare 9 deg along the column normals. Bound body= + even_through. Result: az090/back34/az000 show a skirt wrapping the hips with thickness; hit/float/zfight/drift/clip 0.
- r108 (item 3): Fix: fingers rebuilt as 5-sided two-segment tubes (r 0.015, knuckle 0.0155), 12 deg splay, 20 deg curl at the middle knuckle; separate piece_handclaws (cream, rooted 30% in the tips); stage 2 widens the hand's last ring 20% across the fingers. Result: FAIL drift 2 on fingers (nearest-bone rigid binding vs heat-skinned palm). IoU min 0.915.
- r109: Fix: finger_rigid(): every finger + its claw takes the mean body weights of that finger's root ring. Result: drift still 2.
- r110: Diagnosis (GOB_FDBG nearest-skin dump): the rear (low) finger's tip verts sit nearer the foot top (0.05) than the palm, so the drift anchor is the foot. Fix: rear finger 0.72x length. Result: drift 0, all gates PASS.
- r111 (item 3): claws read as dark pin points in hero: claw r 0.0115, length 0.032. Result: three curled clawed fingers per hand read in hero and the front-limb close-up; gates PASS.
- Item 4 (crown nub), no change: the "nub" in the head close-up and attack_f012 is the far ear's blunt tip seen past the dome (the ear sweeps back and up; a camera above the head projects it over the crown). The dome has no spike; the ears own the top-view IoU (0.915), so they stay.
- Should-fix (belly): already light green from the chest to the belt in az000; no change. Dropped stray-line item: not present in the new 4_posed idle_f012.
- r112: final with orbit + glbcheck, --review, --compare. All gates PASS: hit/float/zfight 0, slivers 0 (0.0%), flips 2 (0.12% tris, 0.05% area), drift 0, clip 0, lock PASS, IoU min 0.915, glbcheck OK. 1706 tris. Repair rounds r100-r112.
