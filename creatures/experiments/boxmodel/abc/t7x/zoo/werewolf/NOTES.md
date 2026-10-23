# werewolf — t7 box model, zoo workflow v2

Sheet: refs/gpt/v3/werewolf/sheet_1.png (side TL, front TR, rear BL, top BR). refs.py --height 2.2 (ear tip).
- The sheet's top view is a 3/4 overhead (1.62x the side length), not a plan: dropped from blueprint.json; side +
  front only (as minotaur). Marks added by hand (eye, snout, chin, shoulder, elbow, wrist, hip, knee, hock).
- Identity cue (werewolf, not bear/minotaur/dog): a long tapered WOLF MUZZLE with a black nose and tall pointed ears
  on a skull sitting low in a huge neck ruff / trapezius; inverted-triangle torso (deltoids 1.08 m across, waist
  0.55 m) leaning forward; long arms hanging past the hips with big clawed hands; DIGITIGRADE legs (knee forward,
  hock back high, long paw); a huge bushy tail (0.4 m deep) hanging to the ground. Grey back, cream chest/belly.
- Plan: minotaur loft (13-vertex half rings from 5 control points), arms from a 2x3 region whose top edge is the
  widest ring C2 (hug ring = root loop pushed out unshrunk), legs 2x4 pelvis underside through a 45 % transition ring
  (rhino), ears 2 faces of the skull top, tail a 3x2-face region of the rump back seam (14-sided brush).
  hand_three_finger (4 clawed fingers) and paw_canine welded before the lock.

## Stage 1
- r01 First fit: 2796 tris, IoU side/front 0.873/0.813. FAIL self-intersection 10 pairs at (0.03, 0.20, 0.8): the
  tail's first ring bottom (centre z 0.86, rh 0.10) dips into the buttock under the region. Fix: tail ring 0 up/back
  (0.29, 0.93) rh 0.09, ring 1 (0.37, 0.79).
- r02 Result: tail root clear; 4 pairs left at the ear root (0.12-0.16, -0.32, 2.04). Diagnosis: the ear region
  (F1->F2 cols 4-5) is centred at y -0.40 but the ear rings sit at y -0.335: the first rings lean back through the
  skull top. Fix: region cols 5-6 (centre (0.165, -0.34, 2.02)), ear rings at x 0.16-0.165.
- r03 Result: all S1 gates PASS, 2796 tris, IoU 0.875/0.811. Critique (az000/az045/hero): the head reads as a hood /
  beak: the muzzle side runs as one diagonal plane from the nose corner straight out to the cheek (a wedge), so from
  the front there is no muzzle block in front of the face. Diagnosis: ring13 puts vertices 4-5 on the fc -> side
  chord. Fix: muzzle rings J0/M0/M1/S0 take hand-placed vertices 4-5 running back along the muzzle side (x 0.075-0.10
  to y -0.55) before turning out to the cheek: a box muzzle with a cheek step.
- r04 Result: the muzzle reads as a box with a cheek step from az045/az090; PASS, 2796 tris. Critique (az000/hero):
  the ears are thin spikes; the sheet's wolf ears are broad triangles (base 0.14 across, 0.18 long, 0.2 tall).
  Diagnosis: 2-face base (0.06 x 0.07) and rings r 0.06/0.05 -> 0.04. Fix: 3-face base (F1->F2 cols 4-6), pyramid
  rings 0.06 x 0.085 -> 0.045 x 0.062 -> 0.022 x 0.03 -> tip at z 2.215.
- r05 Result: ears broader at the base, 2860 tris, IoU 0.88/0.813 (still slim from the front: revisit). Critique
  (az000 + blueprint front): the paws are small (ground x 0.20-0.33 vs the sheet's 0.13-0.45, big long wolf paws).
  Fix: paw_canine width 0.25 -> 0.31 (root 0.14 x 0.16).
- r06 Result: paws now span the sheet's foot width; PASS, 2860 tris, IoU 0.886/0.814. Critique (az000/az090 vs sheet):
  the thighs are columns; the sheet's thighs bulge to x 0.37 and are 0.42 m deep at z 0.65 (the lesson: builders
  drift thin). Fix: thigh rings 0-2 centre x 0.235-0.25, r 0.135 x 0.21 -> 0.12 x 0.185 -> knee 0.10 x 0.155.
- r07 Result: thighs bulkier; PASS, 2860 tris, IoU 0.885/0.819. Own zoom crops (scratch crop.py, workbench, rest
  pose) of shoulder / hip / head / tail root show the owner flaws: (a) the pelvis is a box whose L0b..L1 rings
  overhang the thigh root as a SHELF (hip crops front+rear: a dark slot under the skirt); (b) a thin fin and slot
  where the C2 shoulder line meets the arm front; (c) skull top is a flat cap disc; (d) collar ledge under the jaw.
  Worst = (a). Diagnosis: the leg region is only the pelvis underside (L0 -> L0b~), the hip rings above it stick
  out 4-8 cm past the thigh wall. Fix: leg region 3 x 4 faces L0 -> L1, its top edge on the widest hip ring.
- r08 Result: the hip shelf is gone from the side and rear crops (the thigh's outer wall runs straight down from the
  hip ring); the groin V under the belly stays (sheet has it). PASS, 2920 tris, IoU 0.884/0.822. Critique (shoulder
  crop front): a thin fin and notch at the FRONT of the arm root. Diagnosis: region cols 5-7 span y -0.30..0.0 but
  the first arm ring spans y -0.17..0.17: the root's front wall steps back 13 cm. Fix: region cols 6-8
  (y -0.21..0.09), deltoid ring centre y -0.03.
- r09 Result: the fin at the arm front is gone (shoulder crop A); PASS, 2920 tris. Critique (shoulder crops A + side):
  a horizontal collar shelf on the shoulder top where C3 (x 0.50) steps in to T0 (x 0.40) in 5 cm; the sheet's
  trapezius is one 45 deg slope (x = 0.5 - 1.15 (z - 1.56)). Fix: T0 side/back corner 0.44/0.42, T1 back corner 0.39.
- r10 Result: PASS, 2920 tris, IoU 0.884/0.824; the shoulder-top step is softer. Re-reading the side crop: the ledge
  left at z 1.67 is the jaw underside over the throat (the intended chin step; the sheet has it). Critique (head crops
  A/B, hero): the skull top is a flat lid with a sharp rim, the ears read as cones stuck on a lid. Fix: a crown ring F3
  (z 2.07, W 0.10) so the lid is a two-bevel dome.
- r11 Result: crown is a low two-bevel dome (head crops), PASS, 2968 tris, IoU 0.885/0.827. Critique (az000/az045
  hand crops vs sheet): the hands are thin small claws (0.19 wide); the sheet's hands are big 0.22 m paws-hands with
  long fingers - the long-clawed-arm identity cue. Fix: hand_three_finger width 0.23, finger_len 1.0, knuckle 0.14,
  wrist 0.16 x 0.13.
- r12 Result: hands read as broad four-finger hands with claws; PASS, 2968 tris, IoU 0.873/0.827. Critique (wide
  hero-low crop): the werewolf reads as a man in a wolf mask: a dark collar groove runs all round under the head.
  Diagnosis: J0 (jaw line) is NARROWER than T1 under it (cheek 0.23 vs 0.27, jaw vertex 5 at 0.14 vs 0.21), so the
  T1->J0 quads are an upward shelf round the head, and the jaw underside spans the full cheek width. Fix: J0 cheek
  (0.265, -0.34), back corner 0.35, jaw vertices 4/5 (0.08, -0.53)/(0.20, -0.40): the cheek ruff runs straight down
  into the neck, the underside is a narrow wedge under the lower jaw only.
- r13 Result: the cheeks run down into the neck; PASS, 2968 tris, IoU 0.873/0.827. A thin shadow line under the
  jaw remains (the intended chin step). Critique (wide hero-low crop): black rings round each leg under the thigh and
  round the elbow. Diagnosis: the thigh's second ring (0.12 x 0.185) bulges over the knee ring (0.10 x 0.155) - a
  downward-facing band all round; the elbow ring pinches (0.11 x 0.12) between biceps and forearm. Fix (one cause:
  masses bulge over the joint): thigh ring 1 0.118 x 0.172, knee 0.102 x 0.15; elbow 0.115 x 0.13. LOCK if PASS.
- r14 Result: thigh-to-knee and elbow bands softer; all S1 gates PASS. LOCKED r14: 1486 verts, 2968 tris, edge sha256
  b362f7db42c64a4f; IoU side/front 0.873/0.827; orbit holds. Biped checklist at lock: chin/jaw step from az090 (J0
  front -0.68 over throat T1 -0.46) yes; neck ring set back and narrower than the jaw yes; trapezius slopes neck ->
  shoulder (T1 0.39 -> T0 0.44 -> C2 0.54) yes; chest widens into the deltoid (C0 0.38 -> C2 0.54) and the arm root
  (2x3 faces, top edge on C2, hug ring unshrunk) hugs the chest yes; arms A-pose, hands forward, elbows 0.38 m clear
  of the waist yes; knees bent (digitigrade), groin V yes; hands = parts-library hand_three_finger (4 clawed) yes.
  Carried to S2: ears still slim; jaw underside shadow line.

## Stage 2
- r15 plan: joint loops (elbow, upper arm, knee, hock, hip, waist), eye socket inset (E0->F0 cols 3-4, 4 mm step),
  brow 1.2 cm forward, ears scaled 1.2 x / 1.15 y about their axis (vertex moves).
- r15 Result: all S2 gates PASS (lock + 6 loops + socket, IoU vs S1 min 0.997, slivers 0.9 %), 3280 tris; ears
  broader from the front; tech tiles show a few yellow slivers under the chin only (warn level). Next: stage 3.

## Stage 3
- r16 plan: palette 6 (fur grey, back dark grey, cream, tan, dark, eye); cream muzzle/jaw, chest/belly, hands, lower
  legs, inner ears; tan bands on forearm and shin; dark nose leather, back saddle + tail tip; lens eye r 2.1 cm on
  the socket floor; the welded parts' loose shells (hand claws, paw toe beans/claws) mirrored and painted by slot.
- r16 Result: FAIL z-fighting 8 faces, all on piece__rest_hand (techqa per_object): the hand claws' top faces lie
  within 1-3 mm of the finger tops facing the same way. Junction probe PASS (S3, no rig roots), eye PASS
  0.35/0.53/0.43, 42 mm, proud 9.7 mm. Colour tiles read near-black/navy (fur #7c7e86 under the key light) and the
  'back' rule paints every back-facing face. Fix (the gate): each claw shell 5 mm out of its finger (away from the
  nearest body point). Palette lifted (fur #9c9ea6, back #6f7179) and the saddle limited to the torso back, in the same
  run (colour only).
- r17 Result: z-fight still 8 (located with a scratch zf.py on s3.glb: 4 claw faces per hand at the finger tips,
  1.1-1.7 mm over the finger top, ~9 cm2 each). Diagnosis: the claw centroid sits inside the fingertip, so "away from
  the nearest body point" pushed the claws IN. Fix: claws 8 mm out along wrist -> claw. Colours now mid grey/cream.
- r18 Result: ALL S3 gates PASS (3700 tris, 6 colours), junction probe PASS, eye PASS (0.35/0.53/0.43, 42 mm,
  proud 9.7 mm). Colour hero reads as a werewolf: grey back, cream chest/hands/shins, tan bands, dark claws/nose.
  The grey reads blue-ish: fur/back made neutral (#a0a0a3 / #727377) for S4 (colour only).

## Stage 4
- r19 plan: rig on J (spine 5, arms 3, legs 4 digitigrade: thigh/shin/foot/toe, ears, tail 3 with a short root bone;
  roll auto), all pieces bound with body weights; idle (breath, head turn, ear flick, tail swish), move (loping stride,
  knee + hock fold), attack (right-arm claw rake with a chest twist).
- r19 Result: kit S4 gates PASS (glbcheck OK, posed fold 0, clip warn 0.08 %), eye PASS 0.36/0.55/0.45 (0.066 head),
  membranes PASS. Junction probe FAIL: ears knife 158 deg 2.6 r + strip 1.09 r; upper arms knife 106 deg 1.16 r + strip
  1.45 r (yellow band on the shoulder top); thighs knife 133 deg 5.9 r (groin front); tail0 knife 121 deg 3.1 r + strip
  1.59 r. Crops: the ears show worst (beauty tiles: a cone on a lid with notches at the root corners).
  Critique: ear root notches. Diagnosis: the 45 % lerp transition ring sits inside the root region, its walls fold
  back down onto the skull at the front/back corners. Fix (S1 re-lock): first ear ring = root region pushed 2 cm out,
  shrunk 0.85 (minotaur r29).
- r20 S1 re-locked (edge sha256 771b06807d22d3b8). Result: ears knife 158 -> 123 deg, 2.6 -> 1.15 r (strip 1.09 r);
  others unchanged. Located every flag (scratch where.py = junctions.probe on the S4 GLB, flagged poly centres):
  thigh knives all round the root (groin front y -0.17..-0.19, gluteal back y 0.09-0.10, under the tail root): the
  thigh rings are 0.42 m deep but the 3 x 4 root window only 0.26 m (L1 verts 4-8), so the tube walls bulge past
  the window front and back; upper-arm strips at z 1.58-1.61 = the C3~ inserted band (2.5 cm on 10 cm faces); ear knife
  at the INNER front corner of the root against the crown.
  Fix r21 (S4 round budget: three located fixes, one S1 re-lock, as minotaur r27): leg window 3 x 6 (cols 3-8,
  y -0.23..0.15); no C3 insert; ears lean out (tip x 0.18).
- r21 S1 re-locked (545c9aa9dbf05951, 3048 tris, IoU 0.874/0.824). Result: upper-arm strip 1.45 -> 0.84 r (PASS part),
  thigh knife 5.9 -> 3.2 r; ears 1.85 r (worse); tail unchanged. Located (where.py) + crops: (1) the ear's inner
  corner folds against the crown F3 band, which rises 2.5 cm nearly vertical into a flat cap: the crop reads as a lid
  with a rim; (2) the tail underside drops straight back from the root (121 deg crease against the buttock; crop C
  from below shows a bright slit line); all the remaining thigh knives are this same tail-root crease plus the groin V;
  (3) the arm's knife length includes the neck side at (0.29-0.34, 1.64-1.67): the side column steps in from T0 0.44
  to T1 0.27 in 3.5 cm (shoulder-top shelf, then a wall).
  Fix r22 (last S4 round, three located fixes, one re-lock): F3 a low wide bevel (2.06, W 0.12); tail ring 0 rises
  (0.30, 0.97) before the drop; T1 cheek column 0.33, J0 0.295, M0 0.265 (one cheek-ruff slope into the trapezius).
- r22 S1 re-locked (5d194527a54e6aec). Result: upper arms PASS (strip 0.84 r, knife <= 1 r); ears 2.67 r / 135 deg
  (worse), tail 1.32 r / 152 deg + a 5.8 mm strip, thighs 2.66 r (their max = the tail-root crease again).
  S4 round budget used (r19-r22): the rest are the owner-review fix rounds.

## Owner-style review (zoomed crops + where.py + sheet), fix rounds
- fix 1 (r23). Located: (a) ear knives all on the INNER root wall (x 0.13-0.17, z 2.03-2.06): the hug ring's inner
  side is at x 0.137 but ring 0 (rx 0.06 x S2 1.2 = 0.072) reaches in to x 0.088, so the wall goes out-up then
  straight inward: a 135 deg fold (beauty crop A shows a notch); (b) tail: ring 1 (rh 0.145, tilted) puts its
  underside FORWARD of ring 0's, folding back on the root (152 deg); the sheet's lower tail contour leaves the
  buttock at z 0.75, not at the 0.88 root edge. Fix (S1 re-lock): ear ring 0 rx 0.05 centred x 0.165, the S2 ear
  scale only above z 2.10; tail window 4 x 2 faces L0b -> L2 (z 0.78-0.98), rings 0/1 (0.27, 0.86) rh 0.115 /
  (0.36, 0.75) rh 0.155: a tall root over the rump.
  fix 1 Result (r23, S1 re-lock 39d0d6897e4c065d): tail0 PASS; ears 135 -> 119 deg (1.5 r); thighs max 152 -> 106 deg
  but 2.7 r long. Located: ear knives still on the inner root wall where the crown bevel F3 rises inward from the
  F2 row; thigh knives at the groin front (0.10, -0.03..-0.16, 0.69-0.73) and under the new tail root (0.05-0.10,
  0.22-0.26, 0.73-0.79), strips on the 45 % transition band at the inner front. Crops: the groin is hidden behind the
  hands in the beauty tiles; the ear notch shows faintly in A.
- fix 2 (r24): ear window spans F1 -> F3 (2 x 3 faces, side + crown bevel; ear ring 0 at x 0.15) so the inner wall
  rises from the cap rim; leg transition ring 60 % (a narrower, steeper band). S1 re-lock.
  fix 2 Result (r24, S1 re-lock 919f5fc5f273d7de, 3084 tris): ears PASS (no knife), thigh strip 0.98 r PASS; only the
  thighs fail: knife 2.7 r, max 106 deg. Fold dump (where.py): 106/93 deg on the tail root's lower wall against the
  crotch back (0.04-0.09, 0.24-0.26, 0.76-0.82); 100 deg on the leg window's front-inner edge (L0 v3 -> L0b v3);
  97 deg where the flat crotch cap meets the thigh's inner wall (L0 v6-v7).
- fix 3 (r25, S2 vertex moves, no re-lock): crotch cap drops into a shallow V (seam 3.5 cm, v1-3 / v9-11 1.5-3 cm);
  the tail root's lower wall 2 cm back.
  fix 3 Result (r25): WORSE - thigh knife 4.5 r, max 137 deg; the fold dump shows the V made 124-159 deg folds all
  along the L0 edge and the tail move raised its fold 106 -> 137 deg: both signs were wrong.
- fix 3b (r26, over the 3-round budget: the same diagnosis with the signs corrected, S2 moves only): the crotch cap
  domes UP toward the seam (3 / 2.5 / 1.8 cm), the tail root's lower wall 1.5 cm forward.
  fix 3b Result (r26): thigh knife 4.5 -> 2.43 r, max 137 -> 101 deg (fold dump: tail wall 101, window front edge 94,
  crotch-cap edge 97 deg; all else PASS). Still FAIL.
- fix 3c (r27, last; same diagnosis, larger step): tail lower root wall 3 cm forward; thigh inner transition verts
  1.5 cm out (the inner wall leans out under the cap edge).
  fix 3c Result (r27): thigh knife 2.43 -> 2.06 r, max 101 -> 98.8 deg, 3 edges (tail-root lower wall vs crotch back,
  window front-inner edge, crotch-cap edge). Still FAIL; fix budget spent - stopped (same gate, same cause, 3+ rounds).

## Final (r28)
- Kit gates S1-S4 PASS (lock 919f5fc5f273d7de, glbcheck OK, tech QA PASS: 0 hit/float/zfight, slivers 0.8 %, posed
  folds 0, clip warn 0.02 %); eye PASS (0.36/0.55/0.45, 0.066 head, proud 9.7 mm); membranes (ears) PASS;
  separation PASS (legs 0.22 m, arms 0.06 m). Junction probe FAIL on thigh.L/R only: knife 2.06 r (3 edges, max
  98.8 deg) at the groin / tail-root underside, hidden behind the hands and tail in the beauty crops. Ears, upper
  arms, tail0 PASS.
- Residual (orbit18 + side_by_side_sheet): head narrower and longer than the sheet's fluffy wolf head from the front;
  tail thinner than the sheet's brush from the front/rear and its dark half too long; colour borders stair-step
  (painted by face centre, not on placed loops) and the back saddle reads as a rectangle.
- Files: orbit18_sheet.jpg, side_by_side.jpg (--compare), side_by_side_sheet.jpg, review/, stage4/werewolf.glb,
  rounds/s4_r28_junctions.jpg, face_separation.jpg.

## Repair pass (art-director notes, 2026-10-18)
- repair 1 (r29). Critique: thigh.L/R junction FAIL, knife 2.06 r / max 98.8 deg: the groin crease (belly underside
  vs the thigh's front transition wall, 93.9 deg x 0.92 r per side) and the pocket under the tail root (crotch back vs
  the tail's lower wall, 98.8 deg). Diagnosis: the 60 % transition ring is a straight lerp rim -> thigh ring 0, so the
  rim -> transition -> ring 0 walls are one plane and the whole turn is ONE knife edge at the rim; earlier hand moves
  (r25-r27) shifted the fold instead of splitting it. Fix: `soften()` in stage 2 (vertex moves only): the vertices on
  and one ring off each concave fold > 72 deg in the thigh / tail-root probe regions slide (<= 17 mm, mirrored, seam
  x kept) so the turn splits over two edges, cost = exposed-style triangle fold angle (export fold-out split) over
  50 deg. Also: region_roles now sorts its vertex set by position (set order is memory-layout dependent: an
  unrelated file edit moved stage-1 vertices by 1e-5 and broke the lock); re-locked, pos hash = the old one (4f80a31c),
  edge hash 919f5fc5 unchanged. Tail root keeps its one-face column gap (col 9) to the thigh window.
  Result: junction probe PASS on every root: thighs knife 0, max concave 98.8 -> 62.5 deg; tail0 max 58.6 deg; ears /
  upper arms unchanged PASS; all S4 gates PASS, clip warn 0.02 %; crops: no red at the groin or under the tail.
- repair 2 (r30). Critique (orbit18 az000/az045/az180): colour borders stair-step: the chest patch was painted by
  face normal (n.y < -0.35) and the back by n.y > 0.35, so the border zig-zags across the faces; the arm and tail
  bands were z cuts across tilted rings; the back saddle read as a rectangle. Diagnosis: no rule followed a placed
  loop. Fix: `face_columns()` walks every loft ring from the front and back seam (column index per face); the bib is
  cols 0-2 = the front-corner (v3) column line from the crotch to the throat (wide at the pecs, narrow at the waist,
  one flowing edge loop), jaw/cheek cols 0-5 between the T1 and M1 rings; the saddle is cols 9-11 = the back-corner
  (v9) column from T1 down to the waist loop (wide over the trapezius, narrowing with the waist) and a cols 10-11
  spine stripe on to the tail root; arm bands by arc length on the arm's own rings; the tail tip from a tail ring.
  Result: all gates + junction probe PASS (unchanged numbers); the bib border is one smooth curve (hero/az000), the
  cheeks cream like the sheet, the saddle an inverted shield + stripe. Left: the hand back reads grey/tan (the hand
  faces lie > 0.25 m from the arm polyline and fall to the leg rule) - fixed in the next run.
- repair 3 (r31). Critique (orbit18 az000/az180 vs sheet rear/front): the tail is a thin club from the front and rear
  (0.28 m wide vs the sheet's 0.43 m brush, 2/3 of the hip width) and its dark half too long (from 44 % down).
  Diagnosis: TAIL half-widths 0.10-0.14; the (0.52, 0.45) station had been lost in a comment at r23. Fix (S1 re-lock
  af5149a3, +32 tris = 3116): half-widths 0.11 / 0.16 / 0.20 / 0.215 / 0.19 / 0.12 / 0.04, the lost station back,
  the dark tip from that ring on (62 % down, last 38 %, a ring border). The tail change pushed a groin transition
  triangle thin (seam strip 1.04 r, located at (0.06-0.17, -0.26..-0.12, 0.63-0.70)): soften() now also penalises
  export triangles narrower than 0.5 x the region median.
  Result: junction probe PASS (thighs strip 0.87 r, knife 0, max 73 deg; tail0 max 58.6 deg); all S4 gates PASS;
  hands now cream. Left: the wider brush's front faces fell into the leg rule (tan/fur patches on the tail side,
  az090): the tail rule now runs before the legs (y > 0.21; the hock back is at y 0.195).
- repair 4 (r32). Critique (orbit18 az000 vs sheet front): the head is narrow and long from the front; the sheet's head
  is ~10 % broader at the brow .. mouth (0.51-0.59 m vs 0.47-0.53 m at z 1.875-1.73) with a fluffy cheek ruff.
  Diagnosis: the cheek (side) control column of E0..M0. Fix (S1 re-lock): F0 0.215 -> 0.23, E0 0.235 -> 0.255,
  S0 0.245 -> 0.27, M1 0.25 -> 0.28, M0 0.265 -> 0.295, J0 0.295 -> 0.30 (+ the r32 tail paint order fix). Tried
  and reverted inside the round: J0 0.32 (T1-J0 band seam strip 1.40 r in the upper-arm region), then T1 0.36
  (T0-T1 band strip 1.29 r): T1/J0 lie in the upper-arm probe region, so the flare stops at M0.
  Result: lock b49ce906736316a6, 3116 S1 / 3896 total tris (density kept: +32 over r28), all S1-S4 gates PASS
  (techqa: 0 hit/float/zfight, slivers 0.9 %, posed folds 0, clip warn 0.02 %), junction probe PASS on all 7 roots
  (ears 0.66 r, upper arms 0.56 r / strip 0.90 r, thighs knife 0 / max 73 deg / strip 0.87 r, tail0 max 59 deg),
  eye PASS 0.37/0.54/0.42, separation PASS. Crops: broader cheeks, cream cheek/jaw like the sheet, smooth bib border,
  shield saddle, the wide brush with a 38 % dark tip.
- Final (r32): orbit18_sheet.jpg (before: orbit18_sheet_before.jpg), side_by_side.jpg, side_by_side_sheet.jpg,
  review/, rounds/s4_r32*.jpg. Residual: the head is still narrower above the jaw than the sheet's fluffy head
  (T1/J0 boxed in by the arm probe region); the saddle's lower end steps once (col 9 stops at the waist loop) and its
  top is a level nape line; the tail's dark border is a straight ring, not the sheet's flame shape.

## Border pass (night 2026-10-23, s4 r33)
- kit/smooth_borders(body, k=k, iters=8) right after the body paint (as frog r17). 5 despeckled, 14 anti-stair cuts,
  87 border verts relaxed (max 18.6 mm, 6 undone); stair corners 33 -> 13, 3-to-1 quads 22 -> 0.
- Gates: kit S1-S4 PASS, junction probe PASS (numbers unchanged), eyes PASS; clips: move FAIL (pen 0.94 %H) on the
  rebuild -> --clips --fix-clips -> all PASS. Detail gate FAIL (finger tips 9.6 mm thick < 26.6 mm, sticks): pre-existing,
  the border pass does not touch the hand pieces -> owner/next fix pass.
- A/B (fresh Opus seat per order, blind): after wins both orders (rear saddle V without the waist notch). ADOPT.
- Files: border_before_after.jpg, before_borders/ (old py, GLB, checks).
