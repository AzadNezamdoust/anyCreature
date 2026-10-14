# goblin, setting c1 "carve + detail"

Stage 1 = carve_base (visual hull of reference/) for the body, legs and arms, plus hand edits: the hull's head is
replaced (the hull fused the long ear blade and the skull into a shelf over the shoulders and read the face as a hood).

## Stage 1
- r01: carve_base defaults. 1126 tris, IoU side/front/top 0.913/0.868/0.876. Critique: the head is a hood with a beak,
  the ears a flat shelf over the back (az090/az180); body, legs and arms read. Fix: replace the head.
- r02: Fix: bisect at a neck plane, hand-built 8-point head rings H1-H11 zipped to the cut rim. Result: FAIL 32
  intersections (the hull's chin below the plane survives; the zip folds).
- r03: Fix: delete hull faces above a side-view cut line (chin, head, ear shelf). Result: 18 hits: the rim spans the full
  shoulder width (x 0.2), the resampled neck ring folds against the jaw ring.
- r04: Fix: a narrow hand neck ring (half width 0.088) above the wide rim (the zip band is the trapezius slope), cut line
  lowered at the neck, jaw-side points of H1 raised. Result: PASS, 0 hits, 1128 tris. No ears yet.
- r05: Fix: ears extruded from the two side faces H6-H8 P4-P5, four lens sections to the tip. Result: PASS; front IoU
  0.796 -> 0.845; but top view: ears swept back ~55 deg (the side view's tip y 0.29) read as wings; top IoU 0.742.
- r06: Fix: ear tip to (0.44, 0.17, 0.955) (~35 deg back, the front and top views' sideways ear; side view loses
  length, noted: the generated sheet's side and top views disagree), mid section taller (0.095).
- r06 result: top view still reads the ears swept back ~50 deg (wings); top IoU 0.749.
- r07: knob plan_roundness=2.5 to round the box flank. Result: FAIL closed (a seam fin, 3 open edges) and the flank
  barely changes. Reverted.
- r08: Fix: ear tip to (0.45, 0.09, 0.955): sideways with a slight back sweep, as the front, rear and top views show.
- r08 result: ears read sideways in front/rear; PASS, 1214 tris, IoU 0.85/0.847/0.765.
- r09: Fix: the back-top corner pulled onto a quarter ellipse (hunch). Result: no visible change: the hull back is
  already round; the flat "table" in az090/az000 is the shoulder tops at neck height. Kept (harmless).
- r10: Fix: shoulder tops (x > 0.09) pressed onto a trapezius slope z = 0.76 - 0.8 (x - 0.08).
- r10 result: PASS; the collar shelf is lower, but hero shows the real problem: the arms are slabs 0.16 deep (the
  torso's side-view depth) and 0.06 wide, so they read as a cape.
- r11: Fix: arm vertices (x > 0.19, or > 0.26 below the knee) squeezed to half depth about the arm's centre line.
- r11 result: PASS; az090 now shows a thin arm hanging forward of the torso; hero still a wide sack torso and a
  T-shirt collar shelf around the jaw (az000).
- r12: Fix (upper-body proportion): trapezius slope lowered to z = 0.72 - (x - 0.08); torso between hips and armpit
  narrowed to 86% in x (more gap to the arm in front view).
Lock: r13, 1214 tris, edge sha256 70471d60241baeef, IoU vs blueprint 0.847/0.819/0.753 (ears turned sideways on purpose).

## Stage 2
- r01: grin loop in band H2-H3 (front pushed in 0.028, lip corners climb), hooked nose tip down + nostril flare,
  angry brow (inner brow down, ring forward), cheekbone and jaw corner out, eye-socket inset, pot belly forward.
  Result: PASS, min IoU 0.975, slivers 22 (1.7%), 1258 tris. Clay reads beak + brow; the face needs eyes/teeth/colour.

## Stage 3
- r01: paint by rules + 3-pass majority filter (mouth, inner ear, belly, cloth, skin); belt ray-cast onto the hull in
  the tilted belt plane; brass buckle; front/back tattered flaps; hex eye lens + pupil in the socket; upper teeth row,
  lower corner fangs; 3 curled fingers + claws per hand; 3 toes + claws per foot.
- r01 result: FAIL hit 1 (the belt cuts the lumpy hull at the back of the skirt), slivers 3.2% (the eye lens was
  degenerate: the inset face's normal was stale, zero).
- r02: Fix: belt columns step out 5 mm until no band face cuts the skin (two back columns +35 mm); socket normal
  refreshed. Result: PASS, slivers 28 (1.2%), 2390 tris. Critique: the eyes sit behind the socket rim, invisible at
  hero/az000 size (the reference's big yellow eyes carry the face).
- r03: Fix: lens 5 mm prouder (front of the pupil 23 mm off the socket floor), radius 0.027 -> 0.031.
- r03 result: PASS; az000 now reads goblin (yellow eyes under an angry brow, hooked nose, toothy grin, ears with a
  light inner face, belt + buckle, tattered cloth). Critique: hero shows the dark mouth band running back under the
  ear like a strap (MOUTH took every slot face with y < -0.10); the reference grin ends at the cheek.
- r04: Fix: mouth faces only where y < -0.165 (the lip corner), the rest of the slot stays skin as a crease.
- r04 result: PASS; the dark band left in hero is the slot's shading, not paint (acceptable: it reads as a wide grin).

## Stage 4
- r01: k3's rig and clips, joints moved onto the carved legs/arms (J). Result: FAIL flips 22 (0.92% tris, 1.2% area:
  body 19 at the arm/flank junction, belt 3), drift 2 (fingers); stretch 27 (forearm, teal), clip 56 (warn).
- r02: Fix: arm-bone rotations at 60% (the hull arm hangs 2-4 cm off the flank and shares its heat weights).
- r02 result: no change (21 flips). Diagnosis (GOB_DBG flip dump): every flip is on the hand's inner face
  (x 0.25-0.27, z 0.21-0.32), in move/attack frames where the thigh swings: the hand hangs beside the knee and took leg
  heat weights; the fingers' root weights (finger_rigid) inherit it -> drift.
- r03: Fix: arm_clean(): hand/forearm vertices (|x| > 0.25, z < 0.42) drop leg/hip weights, renormalised to arm bones.
- r03 result: worse (62 flips): the |x| > 0.25 box also caught the feet. Narrowed to the hand: still 30, so not leg
  weights. Dropped arm_clean.
- r04: Fix: smooth_weights(): 10 passes moving each vertex's weights halfway to its neighbours' mean (the carved
  mesh's irregular triangles gave weight jumps across the thin wrist faces). Result: flips 11 (0.46% tris, 0.54% area:
  still over on area), all in attack f006 (the chest twist swings both hands) plus one skirt face; drift 2 (fingers).
- r05: Fix: attack chest twist 18/16 -> 10 deg; fingers shortened (0.045+0.03 -> 0.036+0.026) so their tips are
  nearer the palm than the foot top (the drift anchor).
- r05 result: flips 10 (0.42% / 0.55% area), drift 1. r06 (hand.R counter-bend at attack f7 dropped): no change.
  Diagnosis (GOB_DBG weight dump): the right hand's verts carry thigh.R 0.18-0.28 + shin.R 0.1 (heat bleed from the
  knee beside it), so the chest twist pulls the hand against the leg.
- r07: Fix: arm_clean (hand/forearm |x| > 0.25, 0.11 < z < 0.42 drop leg/hip weights) BEFORE the weight smoothing.
- r07 result: drift 0, but flips 22. Diagnosis (mesh walk on carve_base.json): the carved hand/forearm is FUSED to the
  knee by a web of faces at z 0.2-0.3 (the occupancy blur closed the ~3 cm front-view gap between forearm and knee).
  No stage-2/4 weight trick can bend a web; it is a stage-1 defect.

## Stage 1 re-lock (logged: the r13 lock is deleted, backup kept outside the folder)
- r14: Fix: carve knobs mask_blur 3 -> 1, blur 1 -> 0: the hand walks up the arm without reaching the leg (mesh walk:
  the hand's component below z 0.6 never comes nearer than x 0.20). PASS, 1122 + head = 1122 tris (body),
  IoU 0.851/0.817/0.754; the silhouette is the same, slightly crisper. Over the 14-round stage-1 budget by one (the lock).
Lock: r15, 1122 tris, edge sha256 78576a9075a21571.
- stage 2 r02 (re-run on the new lock, same moves): PASS, min IoU 0.975, slivers 20 (1.7%), 1166 tris.
- stage 3 r05 (re-run): PASS, 2298 tris, slivers 32 (1.4%), hit/float/zfight 0, 8 colours.
- stage 4 r08 (re-run, arm_clean + smooth_weights kept): PASS: flips 3 (0.13% / 0.24% area), drift 0, hit 0;
  clip WARN 74 tris (4.2% area: the front flap against the thighs in move). Over budget: stage 4 took 8 rounds
  (the hull's hand-knee web cost 6).
- stage 4 r09: final with orbit + glbcheck, --review, --compare.

## Team pass (review/ad_notes_team.md), rounds 10-30
- r10: baseline, all gates PASS (flips 3, drift 0, clip 74 warn).
- s2 r11 (must-fix 1, legs): Critique: thigh/shin are one column as deep as the torso. Diagnosis: the hull leg (85
  vertices, no knee ring). Fix: legs(): scale leg vertices about per-band centroids. Result: PASS but jagged (the
  centroids of 4-10 vertices per band jump; the band at z 0.36 is the rump).
- s2 r12: Fix: a fixed centre line (x 0.145, LEG_CY), the buttock (y > 0.15-0.22) and the crotch near the seam excluded.
  Result: FAIL slivers 2.1%; shape smooth.
- s2 r13: Fix: LEG_S shin 0.62 / knee 0.74 / thigh 0.64, LEG_DY knee -42 mm, ankle +15 mm. PASS, IoU min 0.948,
  slivers 1.9%. s4 r14: PASS, flips 5 (0.22% / 0.35%), clip 74 -> 22.
- s4 r15 (must-fix 2, eyes): Fix: 8-point almond lens (EYE_W/EYE_H, outer corner up 14 deg), rim ray-cast onto the
  skin + 4 mm, bulged iris ring, small vertical pupil. Result: PASS; readable, but half under the brow, a flange at the
  outer corner.
- s4 r16 (must-fix 3, brow): Fix: brow ring forward push 12-22 mm -> 2-6 mm, forehead front +10 mm forward, cheekbone
  H6 P2/P3 up 8/15 mm. Result: PASS, IoU 0.949; no brim, the forehead runs into the brow.
- s3 r17 / s4 r18: rim depths smoothed, the iris ring follows the rim's tilt, corner elongation 1.12 -> 1.06: a clean
  almond. r19: size 0.052 x 0.037 (a yellow fleck: the smoothed rim dipped under the brow). r20: rim = max(raw,
  smoothed): clean. Eyes are the first read in hero and az000.
- s4 r21 (must-fix 4, hands): Fix: fingers 0.058+0.040, spread 20 deg, claws 0.045 x 0.0155. Result: FAIL drift 2
  (finger shells: the tips come nearer the foot top than the palm, so the kit anchors them to the foot).
- r22: fingers 0.048+0.034 (+33%): PASS drift 0. r23: 0.053+0.037: FAIL drift 2. Kept 0.048+0.034. Partly done: the
  drift gate caps the length; claws are +50%.
- s4 r24 (must-fix 5, belt): Fix: 25 belt columns, 2.5 mm steps (rear step 40 mm -> 18 mm). Result: FAIL hit 1 (belt).
  r25: inner offset 7 -> 9 mm: PASS.
- r26: Fix: belt rise 0.33 -> 0.20 per metre (the rear sat on the receding slope above the rump and stood off as a
  shelf; now on the near-vertical part). Result: FAIL hit 2 (the back flap no longer tucked under the stepped columns).
- r27: flap tops follow the belt's step-out: PASS (Blender crashed after the gates in the render, rerun fine).
- r28: back flap columns 24,23,21,20 (to 150 deg, ~70% of the old width), drops x 2/3, 4 tatters. PASS.
- r29: the rump beside/below the back flap painted skin (the painted "skirt" on the base was the bib). PASS.
- r30: belt outer 26 -> 22 mm; final with orbit + glbcheck OK, --review, --compare. 2514 tris, slivers 1.0%,
  flips 5 (0.20% / 0.36% area), hit/float/zfight/drift 0, clip 32 (warn), IoU min 0.949, lock PASS.
- Not done: should-fix list (skull nub, collar shelf, mouth crease, move stride, ear slivers). Rear belt columns 19-20
  still step out 20 mm (a lump of the hull at the hip).

## Team pass, second pass (review/verify_team.json: items 1, 3, 4, 5 PARTLY), rounds 31-43
- r31: baseline, all gates PASS (flips 5, drift 0, clip 32 warn).
- s2 r33 (item 1, legs): Critique: az090 the leg is still a column, no forward knee. Diagnosis (mesh dump, side plot): under
  the knee the hull has two prongs: the real shin (y 0.05-0.10) and a phantom one in front of it (hand side silhouette
  x leg front silhouette), closed 2 cm above the foot. A y-remap of the whole band: FAIL (34 hits). Fix: KNEE_MOVES,
  16 explicit vertex moves: the phantom prong lifted into the knee's underside, the back of the knee hollowed.
  Result: PASS, IoU min 0.933, slivers 1.9%: a forward knee, the shin runs diagonally back to the heel. s4 r34 PASS.
- s2 r35: Fix: shin mid ring 4 -> 7.5 cm deep (it read as a blade). PASS, IoU 0.937.
- s4 r36 (item 3, brow): Diagnosis: at P2/P3 the brow ring overhung the eye 2-2.5 cm and the forehead above receded
  at 35-45 deg (the step in the wire). Fix: brow P2/P3 back 11-13 mm, forehead P2/P3 forward 10-12 mm. PASS: one
  slope from dome to brow; the ring edge still shows as a line in the wire (partly).
- s4 r37 (item 4, hands): Diagnosis: the fingers fanned front-to-back (hv ~ -y), so az000 saw one paddle, and they
  pointed at the foot, so the drift gate capped the length. Fix: fan across the hand (x), fingers reach forward and
  hook down, length 0.058+0.040 (the full +60%), spread 24 deg. PASS drift 0; clip 46 (claws vs the foot in move).
- r38/r39: hand axis outward and less down (0.36, -0.80, -0.42), claw hook 30 -> 18 deg: clip 32 (claws 8).
- s4 r40 (item 5, belt): Diagnosis (column dump): the rump is a box; column 19 faced +x and column 20 +y, the band
  cut the corner ridge between them and stepped out 20 mm; the 22 mm band stood off the receding back. Fix: column
  normals averaged with their neighbours, column 19 moved onto the ridge (146 deg), outer offset 22 -> 16 mm at the
  back. Result: PASS, steps 3 mm, belt clip 15 -> 10.
- r41: back flap top (10, 15) mm under the thinner belt, hem (9, 23) mm, flare 0.14 -> 0.10: it hangs down the rump.
- r42: belt even_through radius 0.035: no change in clip, reverted.
- r43: final with orbit + glbcheck OK, --review, --compare. 2514 tris, slivers 1.4%, flips 5 (0.20% / 0.36% area),
  hit/float/zfight/drift 0, clip 27 (warn; was 32), IoU min 0.937, lock PASS.
- Not done: flips stay 5 (within limits, inner forearm faces); clip 27 remains (belt 10, claws 8, fangs 5, front flap 4).
