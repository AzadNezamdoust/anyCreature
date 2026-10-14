# giant (k3) build notes

Reference present: sheet wins on shape, brief on identity/palette/clips. Top trace in blueprint.json is degenerate
(two identical points), so top IoU reads 0.0 throughout; side and front are the working targets. Not redrawn.

## Stage 1
- r01: 488 tris, gates PASS, IoU side 0.853 / front 0.873. Critique: side view, the hump stops short above the head:
  a notch between the head top (-0.5, 3.4) and the hump peak, where the reference slopes straight down from the
  peak into the brow. Diagnosis: R6 (a=62) puts its front seam at (-0.41, 3.14), below the head top. Fix: R6 tilted
  43 deg with its front seam at (-0.55, 3.45) so the crest slopes over the head; neck section H0 moved to y -0.64.
- r02: 488 tris, IoU side 0.872 / front 0.872. Better: crest now slopes into the head. Critique: front view, the
  arm is a straight column: too wide at the upper arm (grey past the red at x 1.5, z 2.4-3.0) and too narrow at
  the elbow/forearm (red reaches x 1.8 at z 1.7). Diagnosis: arm sections A2-A5 centred on a straight line x 1.35-1.52.
  Fix: bow the arm out at the elbow (A2 x 1.30, A3 1.44, A4 1.56 with lateral radius 0.40, A5 1.56).
- r03: 488 tris, IoU side 0.872 / front 0.866. Better: the arm bows out at the elbow like the sheet. Critique:
  front and hero views, the head reads as a bucket: a flat lid as wide as the jaw, square in front view.
  Diagnosis: head sections H0-H2 keep top-side x 0.30 and bottom-side x 0.30-0.36 (a box). Fix: narrow the
  cranium (top-side x 0.26/0.24/0.18), widen the jaw corner at H1 (x 0.38), drop the brow to z 3.18-3.20.
- r04: 488 tris, IoU side 0.869 / front 0.866. Better: head is now a narrow cranium over a wide jaw. Critique:
  hero/front, the torso front is one flat vertical panel from throat to crotch; no pot belly, no chest shelf.
  Diagnosis: front depths R1 0.62 / R2 0.80 / R3 0.72 are nearly equal. Fix: belly R2 df 0.95 (front-mid x 0.72,
  z 1.88), chest R3 df 0.64 (tuck under the pecs), hips R1 df 0.55.
- r05: 488 tris, IoU side 0.868 / front 0.867. Better: a pot belly with an under-plane now reads in front/hero.
  Critique: az045/hero, the legs are straight plank columns ending in a slab foot. Diagnosis: leg sections S1-S3
  nearly equal and stacked on one axis; S4 = S5 footprint. Fix: bulkier thigh, knee forward (y 0.42), narrow ankle
  set back (0.23 x 0.27 at y 0.62), foot top smaller than the sole so the toes slope down.
- r06: 488 tris, IoU side 0.859 / front 0.862. Better: thigh bulk, forward knee, narrow ankle, toes slope; legs
  no longer planks. Reads as a hunched troll from every view (small sunk head, hump, long arms, huge fists,
  short legs). Remaining faults are secondary (flat face, box fists, no knuckles) and belong to stages 2-3. Lock.

## Stage 2
- r01: 680 tris, gates PASS, min IoU vs s1 0.986. Loops: neck, shoulder, 2 elbow, knuckle row, 2 knee, brow ring;
  eye socket inset. Better: brow ridge and deep sockets read in front. Critique: hero, the face below the brow is a
  pig-snout tube; no jaw or mouth, so it reads "boar" not "troll". Diagnosis: the front cap is two quads with the
  chin H3[0] behind the nose. Fix: partial loop (fan-terminated on the muzzle) for a mouth corner pulled in, chin and
  jaw corner pushed forward 0.08 (underbite for the tusks).
- r02: 684 tris, PASS, min IoU 0.982. Better: jaw juts under the nose, a mouth corner reads. Critique: hero/top,
  the hump crest is one flat octagonal lid (the R6 cap n-gon), a crate lid on the dome. Diagnosis: all six R6 cap
  verts lie in one plane. Fix: lift the cap midline (p0 +0.10, p5 +0.12 along the lid normal, which also pushes the
  lip over the head) and p1/p4 +0.05, so the lid folds into a ridge.
- r03: 684 tris, PASS, min IoU 0.981. Better: the lid folds into a crest ridge; lip pushed over the head. Stage 2
  done (3 rounds); remaining face read depends on the stage-3 eyes and tusks.

## Stage 3
- r01: 1332 tris, FAIL hit (belt) + slivers 2.3%. Critique: the gates. Diagnosis: the one loincloth object's front
  and back flaps meet the belt in two separate patches (counted as a double pass); slivers are the loincloth's
  0.04-thick side walls and pentagon caps (20) and the tusks' tapered needle quads (8). Fix: two loincloth pieces
  built as quad-strip plates 0.07 thick (3 points per row, no n-gon caps); tusks as base ring, bent mid ring, one tip.
- r02: 1416 tris, all gates PASS. Critique: hero/az000 colour, the moss is three small green chips; the sheet shows a
  moss mantle over the hump and shoulders (the creature's mountain read). Diagnosis: moss slabs 0.28-0.30 radius,
  0.04 sunk. Fix: four larger clumps (0.28-0.40 radius, 0.11 thick, crest/shoulder/upper back/front lip), rocks
  moved clear of them.
- r03: 1464 tris, PASS. Better: moss mantle reads on the crest and shoulders from front/hero. Stage 3 done.

## Stage 4
- r01: body 1464 tris, FAIL posed fold-overs 4 tris (0.27% tris, 0.56% area) + drift 2 rock shells. Critique: TECH QA
  hero/az000, purple folds on the deltoid cap and brown rocks on the shoulders in the attack wind-up. Diagnosis:
  upperarm pitched 100 deg crushes the deltoid top faces, and the deltoid rock sits across the clav/upperarm weight
  seam. Fix (the shoulder joint): wind-up takes the height from the chest (-20) and the elbow (55) with the upper
  arm at 75; the shoulder rock moves to the upper back (0.90, 0.85, 3.00), off the joint.
- r02: all stage-4 gates PASS (flips 0, drift 0). Weakness kept: the wind-up raises the fists to chest/face height,
  not fully overhead; a higher raise folded the deltoid cap. Final round r03 with orbit + glbcheck.

Triangles: stage 1 488, stage 2 684 (base), stage 3 1464 total, stage 4 1464 total.

## Repair pass (NGO AD notes, K=1; kit of 2026-09-28)
- s4 r08 (baseline): all gates PASS; WARN clip 38 tris (2.46% of surface). No gate fails, so item 0 is the clip warning.
- s4 r09 (diagnosis, no model change): a temporary per-frame probe (GIANT_DIAG=1) of kit `_clipping` showed the pink is
  NOT the fists through the chest: (a) body 8 tris = the two fists crossing each other at the midline in front of the
  face at the wind-up peak (attack f14); (b) loin_back at the wind-up and loin_front + belt front at slam/hold: the
  spine bone (head at z 1.85) pitches the belly/back under the belt through the flap tops; (c) belt at the hip sides
  in the walk (thigh bulge, 2 tris).
- s4 r10: Fix (a): wind-up upperarm Z -15 (elbows out). Result: fists apart; clip 30 tris, 1.26%.
- s4 r11: Fix (b): take the attack's torso pitch from the chest, not the spine: wind spine -10/chest -20 -> -3/-30,
  slam 12/18 -> 4/26, hold 8/12 -> 3/17 (also the should-fix: 10 deg more chest pitch in the wind-up). Result: clip
  4 tris, 0.11% (belt at the hip sides in the walk); attack f020 shows the fists swinging in front of the body. Flips 0.
- s2 r12 (item 4): Critique: az090, flat belly plane from chest to belt; calves one width to the ankle. Diagnosis: the
  R2 ring's front verts; the S3 ankle ring at 85% of the knee. Fix: R2 front seam and front-side verts y -0.08, x +0.02,
  R2 side y -0.03; S3 ring scaled 0.85 about its centre; loin_front top rows 0.03 forward to stay on the belly.
  Result: min IoU 0.967; belly curve visible in hero/az090 but modest under the arm; clip rose to 12 tris 0.52%
  (loin_front inner face at z 1.37-1.56, 0.05 from the new belly, closed in slam and walk).
- s4 r13 (probe) / r14: Fix: loin_front plate hangs at a steeper angle (rows 1-2 y -0.26/-0.15 -> -0.33/-0.20).
  Result: clip 4 tris 0.11% (belt hip sides in the walk only).
- s2 r15 (item 2, stage-2 part): Critique: the brow does not overhang the eye chips. Diagnosis: brow ring verts z>3.0.
  Fix: those verts y -0.03, z -0.012. The lower-jaw front is already one plane (chin, jaw corner, mouth corner form
  one fan triangle), so no flatten was needed. Result: min IoU 0.967, gates PASS.
- s4 r16 (item 2, stage-3 part): Fix: tusks rebuilt at ~55% height (tip z 2.79 at the nose line, eyes at 3.0), base
  radius 0.055 -> 0.088, tip curving out (x 0.29); eyes 1.4x wider lenses (0.077 x 0.05), 0.04 deep, 0.02 proud;
  mouth band: body faces on the top of the lower jaw (y < -1.0, z 2.58-2.75, front-facing) painted 'dark'.
  Result: az000 close crop reads brow, two amber eyes, two short thick tusks and a dark mouth V; gates PASS.
- s4 r17 (item 1, stage-2 part): Critique: az000, the fist is a smooth mitt. Fix: a full knuckle-ridge loop between the
  fist top and the finger row (pushed out 0.03, front 0.05); two logged partial loops (fan-terminated in the knuckle
  band and under the fist) down the two front faces, their verts and the front-centre edge pulled in 0.035: three
  finger grooves, four fingers. Result: min IoU 0.961, 1504 tris, gates PASS; grooves are subtle under dark paint.
- s4 r18 / r19 (item 1, stage-3 part): Fix: the four equal finger boxes replaced by four stone knuckle caps on the
  ridge, unequal (half widths 0.075/0.092/0.088/0.07, middle two widest), staggered in height and depth, axis half
  along the surface normal; a stone-tipped thumb block on the inside of each fist rooted ~30% in the mitt; toes
  three of unequal width, big toe inside (0.13/0.095/0.075). Result: 1536 tris, gates PASS; the caps read as
  knuckles over a grooved mitt, but the row still reads regular from straight on.
- s4 r20 (item 3): Critique: hero/back34, the moss is flat prism chips sitting on the hump with an edge all round.
  Diagnosis: flat 7-gon prisms placed on one surface point cannot follow the dome. Fix: `drape()` plates: an
  irregular 7/8/9-gon outline projected onto the skin (edge tucked 0.008 under it), a mid ring at 75% lifted 0.066 /
  sunk 0.044 (40% of 0.11 thickness), centre peak; three per side (crest, shoulder, front lip). Rocks 2x
  (r 0.22-0.28), sunk 50%, all at x <= 0.62, off the clavicle/upper-arm seam. Result: FAIL drift 1 shell (moss).
- s4 r21: Diagnosis: the shoulder plate (centre x 0.92, 0.46 long) reached onto the deltoid over the clav/upperarm
  weight seam. Fix: centre moved to (0.80, 0.30, 3.50), 0.26 x 0.44. Result: all gates PASS; but the plates read as
  small sunk patches (only the inner half stood proud of the skin).
- s4 r22: Fix: mid ring at 75% of the outline, plates larger (crest 0.40 x 0.62, shoulder 0.30 x 0.50, lip 0.36 x
  0.30). Result: gates PASS, 1632 tris; top/back34 read as a mantle from the crest over both shoulders with rocks
  bedded in it; clip 14 tris 0.29% (moss 10 tris at the wind-up, belt 4).
- s4 r23 (probe, no model change): the moss clip comes only after the kit's edge turning (not in the raw mesh
  probe); left at 0.18% of surface. The GIANT_DIAG probe was then removed from the program.
- s4 r24 (final, orbit + glbcheck): all gates PASS; hit/float/z-fight 0; slivers 2 (0.1%); flips 0 (0.00% / 0.00%);
  drift 0; lock PASS; min IoU 0.961; glbcheck OK; clip warning 14 tris, 0.29% of surface (moss 10, belt 4).
  Review packet checked (idle frame 1): item 0 done; item 2 done; item 1 partly (knuckle caps unequal and staggered,
  but still a regular row from az000; the grooves are faint under the dark paint); item 3 partly (a mantle from
  top/back34, still separate patches from az000/hero); item 4 partly (ankles done; the belly curve is small and the
  arm hides it in az090). Should-fix done (wind-up chest pitch -30). Triangles: base 724, total 1632.

## Repair pass round 2 (AD notes r2, K=2; kit of 2026-09-29)
- s4 r25 (baseline): all gates PASS; WARN clip 14 tris 0.29% (moss 10, belt 4). Item 0: no FAIL.
- s4 r26 (item 1): Critique: az000, fists near-black boxes with stone dice across the front. Diagnosis: body_rule painted
  every face at x>1, z<1.12 'dark'; the stone knuckle caps sat on the surface. Fix: fists painted 'hide'; caps replaced by
  four skin fingers (2-segment curled boxes, half widths 0.066/0.080/0.078/0.062, rooted 0.06 in the lower front,
  ray-cast to the V front), thumb 'hide' with its stone nail. Result: gates PASS, 1824 tris; four fingers read, nails faint.
- s4 r27: Fix: tip segment lengthened (0.12 down) and the nail an inset (0.022, +0.012) on its front face, painted stone.
  Result: small pale nails at the finger tips in az000; gates PASS.
- s2 r28 (probe, item 2): the mid-face (nose bridge y -1.06) sat 0.13-0.16 behind the brow (-1.19) and nose tip (-1.22):
  up-facing planes in the brow's shadow. Probe removed afterwards.
- s4 r29-r30: nose bridge/ridge/cheek tops forward + flatten incl. a socket-edge vert: FAIL s2 self-intersection (4 hits).
  r31 bisect: the flatten set caused it.
- s2 r32 / s4 r33: Fix: flatten the cheek plane (cheek top, cheek side, cheek low, jaw corner) instead. PASS; but the
  bridge at -0.06 hid the inner half of the eyes in az000.
- s4 r34: Fix: bridge -0.03; eyes 0.11 x 0.06, seated at x 0.175 and turned to the front, brighter amber #ffcc3a.
  Result: two amber eyes read under the brow in az000; min IoU 0.961; gates PASS.
- s4 r35 (item 3): Fix: loin_front/back rebuilt as 7-column closed slabs 0.06 thick (5% of width), half width 0.58-0.60
  at the belt wrapping round the hips, to mid-thigh, jagged hem with 3 uneven points; new palette slot 'cloth' #6e5236
  (8 colours; no darker brown existed); back flap hangs ~10 deg off the buttocks; both body=. Result: gates PASS,
  1928 tris, clip 0.44% (loin_front 8 in the walk).
- s4 r36 (item 4): wind-up upperarm (75,0,-15)->(85,0,-27), slam (32,0,0)->(42,0,-12). Clip 0.61% (moss 16); the near
  forearm still sweeps across the face in hero. r37: Z -40 + head -8: clip 1.96% (body 10, moss 24) - rejected.
  r38: Z +10 sign test: arms inward, flips FAIL - rejected (negative Z = elbows out confirmed).
- s4 r39-r41: wind forearm 55->75 (fist higher in the wind-up); head -8 adds moss clip (24) -> dropped (r41). r40 X 80
  changed nothing. r42: shoulder moss moved inward: no change -> reverted.
- s4 r43 (final, orbit + glbcheck): all gates PASS; hit/float/z-fight 0; slivers 2 (0.1%); flips 0/0; drift 0; lock PASS;
  min IoU 0.961; glbcheck OK; clip warning 30 tris 0.61% (moss 16, loin_front 8, belt 4, rocks 2). 1928 tris.
  Packet checked: item 1 done; item 2 partly (eyes and nose read; mid-face still darker than the brow); item 3 done;
  item 4 partly (no body self-clip reported, but the near forearm still passes in front of the face in hero f010/f020;
  clip 0.61% > the 0.29% target). Should-fix not done (belly paint needs a 9th colour; moss bridge plates not tried).
