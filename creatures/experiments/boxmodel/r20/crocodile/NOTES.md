# Crocodile (r20) — round notes

Design: a chunky stylised Nile crocodile — long flat snout with a toothy smile, eye turrets on a flat skull,
broad flat body on four sprawling bent legs, a thick tail as long as the body with a double row of scutes
that merges into one; olive back, pale yellow belly. No reference sheet / blueprint in this batch.

## Stage 1
**r01** 464 tris, gates PASS. Critique: worst = spider legs: long thin limbs reaching 0.39 m out, the feet
turned on edge (az000, top). Diagnosis: FORE/HIND sections x 0.36-0.42, half widths 0.035-0.05; the sole
section follows the bone, so it tilts. Fix: legs 6 cm in, 15-20 % thicker, wrist and sole sections forced
level (dir (0,0,-1)).
**r02** 464 tris: legs now short, bent and planted. Critique: worst = the body is a pencil (top, az000): a
crocodile reads by its broad flat back and wide skull. Diagnosis: CH half widths 0.10-0.21. Fix: width x1.3-1.4,
height x1.2-1.3 (SX / SZ per ring), legs 7 cm out (LEG_DX), eye turret tip moved up with the skull.
**r03** 464 tris: broad flat back and skull read. Critique: worst = it stands tall on posts (az090, az135); a
croc's belly nearly drags. Diagnosis: chain centre z 0.19-0.24, elbow/knee 0.14. Fix: body 4.5 cm lower (DROP),
leg sections down with it.
**r04** 464 tris: low sprawl reads. Critique: worst = the eye turrets are two horns (az000, az045) - a goat.
Diagnosis: EYE_TURRET tip 8 cm over its quad. Fix: tip down to 0.262 and out, a low dome-like knob.
**r05** 464 tris: knobs read as eye turrets, the silhouette says crocodile from top, side and 3/4. Locked (r06). Mouth line and density go to stage 2.

## Stage 2
Mouth partial loop (snout tip -> behind the hinge) sunk 1 cm as a lip groove, elbow / knee / forearm / shin loops,
neck loop, two tail loops, flattened snout top. Run inside r07: IoU min PASS (> 0.9), gates PASS.

## Stage 3 / 4
**r07** (stage 4): scute rows (two rows on the back, one on the tail), 3 claws per foot, two kit tooth rows
(parts.tooth_row, gum off), kit eyes (slit pupil) on the turrets; olive / dark bands / pale belly; 6 colours,
1474 tris. Rig 19 bones; idle tail sway, move = lateral undulation with diagonal limb swing, attack = lift and snap
lunge. All gates PASS. Critique: values too dark (the bands nearly black in hero); idle was 64 frames (> 48).
Fix: palette lifted (olive #7d8f46, bands #55652f), idle cut to 48 frames.
**r08** final run with orbit + review.

Final: all stage-4 gates PASS. Remaining weakness: the move clip's sprawl swing axis is unverified by eye (subtle in renders); head lacks a jaw step.
