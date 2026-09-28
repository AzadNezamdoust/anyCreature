# goblin (w4) build notes

Setting: reference sheet present (`reference/`), blueprint.json traced by refs.py (kept as is).
Reference views disagree: the top view has the hands curled forward and out, the side view has them
hanging beside the knees; the side view wins for proportions (BRIEF), so the hands hang.

## Stage 1
- r01. Critique: gate fails, 3 open edges (az000 looks fine). Diagnosis: the seam extrusion of the nose
  deletes the x=0 side face but leaves the old seam edge of each step loose (3 steps = 3 edges).
  Fix: remove face-less edges in seam_clean. Result: 708 tris; IoU side .843 front .799 top .684.
- r02. Critique: az000 reads as a coat hanger: the upper arm leaves the chest horizontally at z .6 then
  kinks down; the reference shoulder slopes from the neck straight into a hanging arm.
  Diagnosis: deltoid section A1 at (0.215, z .60) with axis (1, 0, -0.5) extrudes sideways out of the
  vertical R3-R4 side quad; R4 (w .17) squares the shoulder. Fix: A1 lower and inboard (0.205, z .575,
  axis (0.7, 0, -1)), R4 w .158 so the shoulder cap slopes into the arm.
  Result: better, the shoulder slopes into the arm (az000); 708 tris; IoU side .843 front .781.
- r03. Critique: az000 head is an egg that narrows to a small chin: no room for the wide fanged grin;
  the reference jaw is as wide as the cheeks and square at the front corners.
  Diagnosis: jaw/mouth rings R7/R8 use the skull profile H (front corner x = .62 w) at w .15/.175.
  Fix: a jaw profile HJ (front corner .80 w, at t .08) and R7 w .165, R8 w .19.
  Result: better, the head is a broad box with a jaw that can hold a grin; IoU front .784.
- r04. Critique: az000/az180 torso is a barrel as wide as the head (.165 vs .20); the reference has a
  narrow chest, a pot belly and clear air between the torso and the hanging arms.
  Diagnosis: torso ring widths R1-R4 (.155/.165/.155/.158). Fix: R1 .142, R2 .152 (belly stays
  widest), R3 .136 (narrow chest), R4 .148.
  Result: slightly better, the chest reads narrower under the head; IoU front .772 (the traced front
  outline bridges arm and body, so a narrower chest costs IoU; the reference wins on shape).
- r05. Critique: az000 legs are straight posts under the torso; the reference goblin is bow-legged,
  knees out at x ~.2, which opens the crouch and the gap between the legs.
  Diagnosis: leg sections knee x .16, shin .172, ankle .18. Fix: knee .195, shin .205, ankle .20,
  foot .21, toes +.015 (J updated to match).
  Result: better, bow-legged crouch with air between the knees (az000/az180); IoU front .758 side .845.
- r06. Critique: az000/hero hands are forks: a thin wrist fanning into three needle fingers, no palm;
  the reference hands are big, a palm and three thick curled fingers.
  Diagnosis: split3 knuckle row W .045 x D .018; finger sections .011/.012 and tips .005.
  Fix: palm W .05 x D .024; fingers .015 thick, tips .007, shorter and curled forward.
  Result: slightly better in az090 (a palm and fingers), but az000 still shows a blade: the palm faces
  sideways so the front view sees only its edge.
- r07. Critique: az000 hands read as thin blades; in the reference front and side views both show the
  three fingers because the palm is turned forward-in. Diagnosis: split3 uses r = -Y, so the knuckle
  row spreads purely along Y. Fix: hand and finger frame r = (0.5, -0.87, 0): the knuckle row spreads
  30 deg off the Y axis; finger offsets follow in x and y.
  Result: better, the three fingers read in az000 and az090; IoU side .844 front .756 top .689.
- r08. Critique: the base reads as the goblin from every view (big domed head, horizontal ears,
  hooked nose, hunch, pot belly, bow legs, hands at the knees). Remaining: flat heel, the brow does
  not overhang yet (stage 2 vertex moves). No topology change needed. Fix: none; lock (r09).
Stage 1 locked at r09: 708 tris, edge sha256 ee22cdff58e70676...

## Stage 2
- r01. Five logged ops: brow loop (R10-R11), mouth loop (R7-R8), second elbow and knee loops, eye
  socket inset; moves: brow forward, grin groove pushed in, chin/chest flattened, belly forward.
  Result: all gates pass, 796 tris, min IoU vs s1 .972, slivers 1.3%.
  Critique (az000 close crop): the nose is a flat plank as wide as the gap between the brows; the
  reference nose is a narrow-rooted wedge with a ridge and a drooping tip. Diagnosis: nose sections
  are flat quads 2w wide on a root quad of x .068. Fix: root verts R9P1/R10P1 inward; upper nose
  verts pulled to the middle (ridge), lower ones spread (nostril wings).
  Result: better, the nose reads as a narrow-rooted hooked wedge with a ridge (az000, az045); 796 tris,
  min IoU .970, slivers 1.3%. Stage 2 ends here (face reads; limbs have second joint loops).

## Stage 3
- r01. Paint 7 colours (skin; belly on the chest/belly ring faces; dark belt, also the mouth band and
  pupils; cloth; fang; eye; buckle). Pieces: belt band, buckle, front/back loincloth flaps with jagged
  hems, claws on finger and toe tip faces, two tusks + two upper teeth, eye lenses.
  Result: FAIL hit (belt) and float (both flaps); 1144 tris.
- r02. Critique: the belt cuts the belly in patches and the flaps hang 1.5 cm below the belt in air.
  Diagnosis: belt rows lerp the stage-1 rings, but stage 2 pushed the belly out, so the .004 inner row
  dips into the skin in spots; flap tops at z .322/.326 sit under the belt bottom (.337/.357).
  Fix: belt rows follow the stage-2 verts with a .003 inner gap (it rests on the buckle); flap tops
  raised into the belt band (.355/.375).
  Result: float fixed; the belt still counts one hit.
- r03. Critique: belt hit. Diagnosis: the flap tops poke out through the belt's outer face (front
  flap front at y -.066 vs belt outer -.065 at z .355; back flap face flush with the outer face .300),
  so the belt is crossed in two patches. Fix: flap tops centred inside the band (front -.063, back .295).
  Result: still one belt hit; the heatmap marks the body faces above AND below the belt (magenta).
- r04. Diagnosis: the waist is a concave crease at R1 (narrower than the belly and hips), so the belt's
  straight top-to-bottom faces cut the skin above and below R1: two contact patches. Fix: a middle
  belt row on R1 itself so the band folds with the crease, inner gap .006.
  Result: the hit moved: only the R0-R1 hip faces under the belt flag now.
- r05. Diagnosis: the R0-R1 strip is strongly twisted (pelvis profile), its folds bulge past the belt's
  lower chord. Fix: the belt rides only on the belly strip R1-R2 (rows at t .02 and .42, above the
  waist crease); buckle and flap tops moved up into the band.
  Result: all gates PASS; 1144 tris, 7 colours. Critique (for the record, stage-3 rounds used up): the
  eye lenses read as small beads under the brow; carried into stage 4 r01 as the one stage-3 change
  (lens 0.037 x 0.025, pupil 0.011 x 0.014).

## Stage 4
- r01. Rig from J (roll auto, 17 bones with mirrors), skin, every piece bound with body weights;
  clips idle (48), move (33), attack (24). Plus the eye lens enlargement above.
  Result: all gates PASS (hit 0, float 0, z-fight 0, slivers 1.6%, flips 0, drift 0); eyes read better.
  Critique (az090 posed attack f006): the wind-up is a flat forward reach at shoulder height, not a claw
  raised to strike. Diagnosis: attack key 8 upperarm.R X 60. Fix: wind-up X 105 with the forearm
  cocked 45 and the wrist back, swipe down-across to X 30 / Z -30. Final round with orbit (r02).
  Result: all gates PASS; attack f006 now raises the claw beside the face, f012 swipes down-across;
  1 posed fold (0.09% tris, 0.15% area). Orbit holds; glbcheck OK. Final: 1144 tris.
