# crab (k3) build notes

Reference sheet present: 2x2 (side/front/rear/top). blueprint.json kept as traced (no edits).

## Stage 1
- r01: first blockout. 7-vert half-ring carapace x 8 Y-sections (T,D,R rim,U under-rim,L,B,S); 4 legs and
  the cheliped extruded from the U-L side faces; fixed finger from the palm end face, dactyl from the palm top face.
  Gates PASS, 772 tris. IoU side/front/top 0.663/0.643/0.566.
  Critique: top view, legs fan evenly at -20..57 deg; reference fan is forward/back (-22..70) so tips miss the traced legs.
  Diagnosis: LEGS yaw values. Fix (r02): yaw -22/16/44/68.
- r02: better, 772 tris, IoU 0.650/0.708/0.634 (top +0.07, front +0.07).
  Critique: front/side, the claw palm is a thin upright slab (0.12 x 0.20) pointing 45 deg inward; the reference palm is a
  chunky block held low, fingers pointing mostly forward. Diagnosis: CLAW_ARM palm dims, U axis, palm z.
  Fix (r03): palm 0.155 wide, axis 30 deg inward (U), claw lowered 0.01-0.015.
- r03: palm reads chunkier and lower; 772 tris, IoU 0.659/0.707/0.607.
  Critique: top view, the carapace is a rounded rectangle (flat 0.30-wide front and rear caps, square corners); the
  reference carapace is a near-round disc. Diagnosis: SECT half-widths at the end sections (0.15/0.23 front, 0.25/0.16 rear).
  Fix (r04): SECT widths follow a circle of r 0.32 (front 0.12/0.205, rear 0.225/0.10, rear cap pushed to y 0.33).
- r04: carapace now a round disc in top view; 772 tris, IoU 0.659/0.706/0.615.
  Critique: front (az000) and top, the fingers run straight on along the palm axis so the claw reads as a box on a stick;
  reference fingers curl inward across the front (70 deg) and are thick with a clear gap.
  Diagnosis: FINGER/DACTYL points lie on U. Fix (r05): second finger segments follow U2 (-0.87,-0.49), thicker sections.
- r05: fingers now curl inward, gap reads in top/hero; 772 tris, IoU 0.662/0.718/0.619.
  Critique: az000/az090, walking legs are thin spikes with a weak second bend; reference legs are chunky segmented
  tubes with a clear knee and an outward-kinked lower leg. Diagnosis: LEGP widths 0.06->0.04 and bend at s 0.37 z 0.15.
  Fix (r06): LEGP 20 % thicker, second bend pushed out to s 0.38 z 0.165 so the tip drops steeply from it.
- r06: legs read as chunky segmented limbs with a knee and a kinked lower leg; 772 tris, IoU 0.662/0.690/0.623
  (front dips: thicker legs cover the traced gaps). Reads as a crab from every view: wide low disc, two big claws with
  a finger gap held in front, eight splayed two-bend legs. Remaining (stage 2): flat-sided palm, belly plane, rim crease.
  Fix (r07): none; lock.
- r07: LOCKED (788? see lock) 772 tris, edge sha256 7ab508142516973d. Orbit holds (advisory: no head chain; a crab has none).

## Stage 2
- r01 plan: rim-band loop along the carapace slope (dark-ridge border, crowned), eye-socket insets on the front slope,
  seam crown +0.016, flat belly plate.
- r01 FAILED to run: kit assert_lock crashed (bmkit.py:626 vert_collapse_edge arg order) on a 2-valent leftover: the full
  band loop ended on the n-gon caps and the eye inset shared its end vertex. Kit not edited.
  Fix (r01b): band becomes a partial_loop from section 1 to 6 (fan terminators on the flat front/rear slope), the eye
  inset uses the untouched front D-R face.
- r01b: PASS. 804 tris, min IoU vs stage 1 0.975; 0 hits/floats/z-fight, slivers 0.5 %. Band crease and socket read in wire.
  Critique: palm still a plain box (no chamfer possible without a ring that runs into the body); accepted for the budget.
  Stage 2 closed after one round (budget).

## Stage 3
- r01 plan: paint shell / ridge band / cream underside / dark tips; pieces: eye stalks + bulbs (in the sockets),
  5 rim teeth per side, pincer teeth on both fingers, 4 barnacles on the rear rim (one side).
- r01: PASS, 1096 tris, 6 colours, 0 hit/float/z-fight. Critique (hero colour): the walking legs have no dark tips at
  all; the tip rule tested face centres below z 0.055 but the last segment's triangles centre at ~0.09. Secondary: bulb
  eyes read as tiny black diamonds. Fix (r02): tip rule z < 0.10 on limb faces; bulb r 0.032, 8 sides.
- r02: PASS, 1104 tris. Dark leg tips now read; bulbs larger but still diamond-like (bicone). Closed stage 3 (budget).

## Stage 4
- r01 plan: 41 bones (body; 4 legs x coxa/femur/tibia/tarsus; claw arm/wrist/palm/pollex/dactyl), custom rolls so +Z
  swings every limb tip down on both sides; all pieces bind(body=) so they borrow the skin weights (no drift).
  Clips: idle 48f claw clicks, move 25f alternating-set sideways scuttle, attack 32f raise-open-lunge-snap.
- r01: all gates PASS (0 flips, 0 drift, glbcheck OK). Posed check: attack f8 claws rise with the dactyl opened wide,
  f16 snaps shut; move f7 the A-set legs lift at the coxa while the B-set plant; no collapse at the claw or leg roots.
  Fix (r02): none; final round with orbit + glbcheck.
- r02: final with orbit: all gates PASS; glbcheck OK (attack/idle/move). Then --review and --compare.

## Triangles per stage
stage 1: 772 (locked) | stage 2: 804 | stage 3 total: 1104 | stage 4: 1104

## Repair pass (K=1, 2026-09-28; notes review/ad_notes.md; stage 1 locked)
- r08 baseline (s4, current kit): all gates PASS; 1104 tris; slivers 0.4 %; 0 flips; 0 drift; clip warn 2 tris (0.04 %). No item 0.
- r09 (item 1, s3) Critique: rim teeth are 5 needles per side (closeups hind limb, back34). Diagnosis: piece_rim_teeth
  pyramids 0.03 wide x 0.012 thick x 0.05 long. Fix: 4 blunt pyramids per side (1 on the front edge between the eyes,
  3 on the anterolateral rim from section 1, spacing 0.073/0.092), h 0.034-0.038, base 0.056-0.06 wide, sunk 25 %.
  Result: PASS, 1092 tris; top view reads as bumps, but edge-on (close-up 1) they were still thin wedges (0.013 thick).
- r10 (item 1) Fix: base thickness 0.013 -> 0.032 (front 0.026) so the vertical apex angle is ~48 deg too. Result: PASS,
  1092 tris, hit/float/z-fight 0, slivers 0.4 % unchanged; close-up 1 shows blunt lobes on the rim, no needles.
- r11 (item 2, s3 paint) Critique: az000 a cream shield fills the front wall between the stalks. Diagnosis: belly rule
  `c.z < 0.25 and n.z < 0.4` catches the front cap n-gon (centre z ~0.22, n.y -1). Fix: belly only for faces wholly at
  or below the U (under-rim) loop. Result: front wall red, but the rim-lip underside went red too (side lost its cream).
- r12 (item 2) Fix: add the note's `n.z < -0.2` underside clause. Result: PASS; az000 front wall red with the teeth on
  its top edge, cream only on the lip undersides and a low band at the bottom. Borders sit on the U and R loops.
- r13 (item 3, s3) Critique: eyes are black bicone diamonds on stalks ~3 widths tall (az000). Diagnosis: `bicone` bulb,
  stalk 0.075 tall r 0.019/0.014. Fix: new `ball()` (8-sided equator + two 0.72 rings, flat octagon caps, r 0.029),
  stalk 60 % height, radii x1.2 (0.023/0.017); ball sunk 0.006 over the stalk top. Result: PASS, 1148 tris, eye
  hit/float 0, slivers 0.3 %; az000 shows two round black eyes on short stalks.
- r14 (item 4, s2) Critique: legs are constant-section tubes, the second bend a shallow kink (close-up hind limb).
  Diagnosis: LEGP rings 2/3 (knee) 0.064/0.060 wide vs femur 0.070; tarsus ring 5 0.046; bend 25 deg. Fix: vertex moves
  only: knee rings x1.3, ring 4 x0.92, ring 5 x0.9, rings 4+5 pushed out 0.016 along the leg's reach (the note said
  "lower" the joint; lowering it flattens the bend, pushing it out sharpens it 25 -> ~34 deg); J bend moved to match.
  Result: PASS, but slivers 0.4 -> 1.2 % (14): scaling the knee rings in the bend plane pinched the inside of each knee.
- r15 (item 4) Fix: knee rings swell across the leg plane only (x1.3) plus a 0.008 bump on their top verts. Result:
  PASS, slivers 0.3 %, min IoU 0.914 (az180); knee swell and taper read in close-up 1, second bend reads in az000.
- r16 (item 5, s3) Critique: barnacles are 4 plain hex prisms in a row on one side of the rear rim (close-up 2).
  Diagnosis: frustum base 0.012 deep, height 0.9r, x 0.045..0.075 off-centre. Fix: 5 truncated 6-sided cones (top 0.6r,
  h 1.1r = 55 % of the base diameter, sunk 30 % of h, crater inset), r 0.016-0.028, astride the centre-line on the
  rear slope. Result: PASS, 1180 tris; barnacle float/z-fight 0; clip warning 2 tris (0.03 %) still on barnacles.
- r17 final (orbit + glbcheck) and --review. Packet check (idle f1): az000 still showed two tall cream stripes flanking
  the red front wall: the front-corner rim-lip faces (R-U, sections 0-1) caught by `n.z < -0.2`.
- r18 (item 2) Fix: the note's front clause: front-facing faces (n.y < -0.5) above the U loop stay shell. Result:
  PASS; az000 red down to a thin cream band at the bottom, the teeth line the front edge.
- r19 final (orbit + glbcheck OK), --review, --compare. All gates PASS; 1180 tris; slivers 0.3 %; flips 0; drift 0;
  min IoU 0.914; clip warn 2 barnacle tris (0.03 % of area). Packet (idle f1) checked for items 1-5.
Triangles this pass: stage 1 772 (locked) | stage 2 772+logged | stage 3/4 total 1180

## Repair pass (K=2, 2026-10-03; notes review/ad_notes_r2.md; stage 1 locked)
- r20 baseline (s4, current kit): all gates PASS; 1180 tris; slivers 0.3 %; flips 0; drift 0; clip warn 2 barnacle tris. No item 0.
- r21 (item 1, s2) Critique: claw = boxy palm with thin spike fingers and spurs (closeups front limb). Diagnosis: finger
  rings 0.04-0.06 vs palm 0.17-0.2; tips are bare points. Fix: `claw_pincer()` walks the finger rings back from each tip
  (distance matching failed: the rings are not rectangles), scales them 1.5-1.6x, curls the tips 15 deg toward each other,
  pulls them back 30 %, shaves the palm bottom 0.015. Result: FAIL IoU az090 0.899; fixed finger a stub; 24 stretched
  tris on the spur spikes (they span the gap and borrow both fingers' weights).
- r22 Fix: scales 1.15-1.45, pull 12 %, shave 0.006; spur spikes dropped (s3); dark only on the last segment of each finger
  (moved tips passed to stage 3). Result: PASS, IoU 0.906; stretch 0. Fixed finger still short.
- r23-r24 Fix: the fixed finger tip moves 30 % of its segment further out instead of back; dark-tip radius 0.72x each
  finger's last segment (the dactyl's tip was still red). Result: PASS; hero shows two thick fingers, a gap, dark tips.
- r25 (item 2, s2) Fix: knee rings -0.023 z, +0.02 along the reach; tip vertex +0.027. Result: FAIL IoU 0.891 in every
  view: lifting the tips shrinks the bbox. r26: no tip lift, knee drop 0.012, palm shave 0 (it cost side IoU).
  Result: PASS, min IoU 0.901 (az090); az090 knees at/below the carapace top, legs splay a little.
- r27 (item 3, s3) Fix: rim_teeth rebuilt: 6 pyramids/side, base depth 0.65 w, height 0.7 w, tip 15 deg down, sunk 35 %,
  graded 0.035-0.05, shell red. Result: FAIL hit 2 (the eye stalk passed through the tooth in front of it).
- r28 Fix: one tooth on the front edge, five past the stalk (arc 0.168-0.39). Result: PASS; close-up 0 saw-tooth rim with
  thickness, no dark wedges.
- r29 (item 4, s3) Fix: `ball()` 10-sided with rings at +-0.7r and +-0.95r (small caps); stalk 1.4x tall, 0.8x radius.
  Result: PASS; az000 round black balls on thin stalks.
- r30 (item 5, s2) Fix: extra across-plane taper rings 4/5 x0.86/0.80. Result: PASS, slivers 0.3 %, IoU unchanged 0.901;
  close-up 1 wire tapers knee to tip.
- r31 (should-fix, s3) Fix: barnacles 8-sided, cream, dark crater, two smallest sunk 45 %. Result: PASS; clip warning gone.
- r32 final (orbit + glbcheck OK), --review, --compare. All gates PASS; 1320 tris; slivers 0.3 %; flips 0; drift 0;
  z-fight 1 face (allowance); min IoU 0.901 (az090/270); clip 0. Packet (idle f1) checked for items 1-5 and the barnacles.
Triangles this pass: stage 1 772 (locked) | stage 3/4 total 1320
