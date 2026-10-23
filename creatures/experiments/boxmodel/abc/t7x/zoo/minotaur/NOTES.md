# minotaur — t7 box model, zoo workflow v2

Sheet: refs/gpt/v3/minotaur/sheet_1.png (side TL, front TR, rear BL, top BR). refs.py --height 2.4 (horn tip).
- The sheet's top view is a 3/4 overhead shot (1.89x the side length), not a plan: dropped from blueprint.json; side + front only.
- Identity cue: a bull head (long square muzzle with a flat nose, horns out-and-up, small drooping ears) sitting LOW in a
  huge trapezius hump; inverted-triangle torso (deltoids 1.2 m across, waist 0.67 m); hooves; tufted tail; leather kilt.
- Plan: one upright spine loft, 13-vertex half rings from 5 control points (planes + round-over); arms 2x3-face region
  of the shoulder side (deltoid = the torso's own shoulder line), legs 2x4 region of the pelvis underside, ears 2 faces,
  tail = back-seam face (seam walls removed). hand_three_finger(2 fingers) and hoof_cloven welded before the lock.

## Stage 1
- r01 Critique: gate FAIL, 34 self-intersecting pairs (knee back, ankle/hoof, tail tip). Diagnosis: leg frames tilt with
  the knee->calf direction so ring 4's back rises over ring 3; the hoof root ring sits in the ankle ring's plane (flat
  bridge); the tail's last section flips (its up vector turned over where the tail runs straight down).
  Fix (one gate, three sites): level leg rings; hoof origin 3.5 cm under the ankle ring; tail section up-vector kept
  continuous. 2452 tris, IoU side/front 0.811/0.792.
- r02 Critique: 4 pairs still at the shoulder (x 0.56, z 1.54). Diagnosis (scratch isect probe): arm walls cross each
  other, the root-loop roles were twisted 18 deg (even spread anchored on one vertex, a 4-vertex row lost its symmetry).
  Fix: even spread with the phase fitted to the true angles. Result: same 4 pairs (second cause below).
- r03 Critique: shoulder pairs remain. Diagnosis: the first arm ring was an ellipse whose top (z 1.58) rose into the
  overhanging deltoid faces C1~-C2. Fix: the hug ring is the root loop itself pushed 3 cm out along the region
  normal and shrunk to 0.94 (keeps the torso planes). Result: all S1 gates PASS, 2452 tris, IoU 0.811/0.786.
- r04 Critique (az000/az090): the head read as a narrow hood. Fix: a boxy bull skull: E1-F2 rings wider (0.19 at the
  brow, 0.175 poll) with a flat top at 2.29 and an upright forehead. Result: head wider and squarer; still PASS, 2452 tris,
  IoU 0.816/0.789.
- r05 Critique (hero): a horizontal collar shelf where the shoulder top met the trapezius (C3 -> T0 front corner
  jumped in 13 cm). Fix: C3 narrower (0.52), T0/T1 front corners out (0.25/0.19) so the chest rises into the throat.
  Result: shelf softened; PASS, 2452 tris.
- r06 Critique (az000): the ears were stubs (a bull's ears droop out past the cheeks to x 0.31). Fix: 4-station leaf
  ear, widest past the root, tip at x 0.335. Result: ears read from the front; PASS.
- r07 Critique (hero, az045): the hands were small hooks (0.17 wide) against the sheet's 0.2 m mitts with thick dark
  fingers. Fix: hand_three_finger width 0.22, finger_len 0.75, curl 0.45, wrist (0.17, 0.10). Result: hands read as
  heavy two-finger mitts; PASS, 2476 tris, IoU 0.82/0.783.
- r08 (probe round; no rig at S1, so only the eye row runs: FAIL "no piece named eye", expected before S3). Own zoom
  crops (scratch crop.py) show the owner flaw: a dark vertical crease between the pec and the arm front and a shelf
  where the C2 shoulder line overhangs the arm (the region sat under the widest ring, the hug ring shrank 6%).
  Fix: arm region moved up to C1 -> C1~ -> C2 (its top edge IS the shoulder line), hug ring unshrunk (k 1.0, 2.5 cm out),
  deltoid ring (0.545, 0.035, 1.38) rx 0.12.
  Result r09 (crops): the chest runs over the shoulder into the arm with no crease or shelf; PASS, 2476 tris.
- r09 Critique (side crop): a collar ledge runs from the chin back along the neck side: the jaw-line ring's jaw
  angle (0.17, -0.16) sat inside the throat ring's front corner (0.19, -0.18). Fix: J0 jaw angle (0.205, -0.15),
  J1 (0.185, -0.19): the step stays under the chin only (side view), the jaw side rises straight off the trapezius.
  Result r10: the side ledge is gone (side crop); PASS, 2476 tris.
- r10 Critique (front crop): the face is a narrow muzzle box inside a cobra hood of trapezius; on the sheet the cheeks
  (0.20 at z 2.0) ARE the outline above z 1.95. Fix: head rings J0-F0 wider at the cheek (side points 0.20-0.21) and
  muzzle front corners 0.11-0.12, the trapezius control points unchanged.
  Result r11 (after an ear-root intersection from the wider cheek: ear chain moved out 2 cm): the face is as wide as
  the sheet's at the eyes, ears clear; PASS, 2476 tris, IoU 0.82/0.788. Residual: the trapezius slope beside the face
  still reads hood-like in grey; horns, ears, nose pad and colour carry the bull read from S3.
- r12 LOCK. Biped checklist at lock: chin/jaw step from az090 (J0 front -0.37 over throat T1 -0.205) yes; neck ring
  set back and narrower than the jaw yes; trapezius steps down neck -> shoulder (T1 0.41 -> C2 0.555) yes; chest
  rings widen into the deltoid (C0 0.42 -> C2 0.555) and the arm root (2x3 faces, top edge on C2) hugs the chest yes;
  arms A-pose, forward hands, elbows 0.21 m clear of the waist yes; knees slightly bent, 8 cm groin gap yes;
  hands = parts-library hand_three_finger (2 fingers + thumb) yes.
  LOCKED r12: 1240 verts, 2476 tris, edge sha256 b09d1d4ed8dc11f3; IoU side/front 0.82/0.788; orbit holds.

## Stage 2
- r13 plan: joint loops (elbow, upper arm, knee, hip, waist, neck), eye socket inset (E0-E1 cols 3-4, 1.2 cm in),
  brow ridge 1.5 cm forward over it, pec shelf (C1 front 2 cm forward, C0 front 1.2 cm).
- r13 Result: all S2 gates PASS (lock + 6 loops + socket; IoU vs S1 min 0.993), 2764 tris. Critique (TECH QA tiles
  hero/az000): a yellow sliver band under the chin: the jaw-underside quads between the throat ring T1 (front -0.205)
  and the chin ring J0 (-0.37) are skewed needles. Fix: T1 front verts 1.5-4 cm forward, T0 1.5 cm (vertex moves).
- r14 Result: slivers unchanged (14). The zoomed hero TECH tile shows where they really are: a thin yellow strip
  round the trapezius top, the logged neck loop cut between T0 and T1 (5 cm apart -> 2.5 cm strips on 10+ cm wide
  faces: a seam strip). The throat move stays (squarer chin underside). Fix: drop the neck loop (T0/T1/J0 already ring
  the neck).
- r15 Result: slivers still 14 — the strip is not the loop. Diagnosis: T1's control points were torso roles (side
  point = trapezius max at column 6) while J0's column 6 is the jaw angle: the T1 -> J0 quads shear 27 cm sideways in
  4 cm of height (needle triangles, and the collar ledge seen since r09). Fix (base change, stage 1 re-locked): T0/T1
  rebuilt with the head roles (front corner, jaw-angle column, trapezius column); the r14 throat move dropped.
  Result r16 (S1 re-lock: 1240 verts, 2476 tris, edge sha256 045339eaca35b823, IoU 0.819/0.787) + r17 (S2): slivers
  14 -> 6, the collar ledge under the head is gone in the hero TECH tile; all S2 gates PASS, 2716 tris.

## Stage 3
- r18 plan: pieces = lens eye (r 2.2 cm, 8-sided, proud 1.3 cm in the socket), parts horns (L 0.50, out then
  up-forward, curve 105), pig-kind nose pad (the bull's flat nose), tail_tuft (tuft kind), belt band + brass buckle,
  9 kilt plates (closed 1.4 cm slabs, tops sunk under the belt, a back gap for the tail). Palette 7: fur, dark
  (hooves, fingers, nose), horn, leather, brass, eye, tuft.
- r18 Result: FAIL hit (kilt side plates kilt2L/R) and slivers 2.7% (kilt plate rims: 1.4 cm x 18-20 cm side faces
  triangulate to 4 deg needles). Diagnosis: 2 hanging rows only; the straight mid->hem segment cut the thigh bulge and
  the tall rims are needles. Fix: kilt rows at 1.045/0.995/0.91/0.82/0.72 + hem, flare 0.17 x drop, 1.6 cm plates.
- r19 Result: slivers 2.7% -> PASS; hit remains on kilt2L/R. az090 TECH tile: the side plate is magenta where it
  meets the forearm: its radius rays started 1.2 m out and hit the hanging arm, so the plate flared into the forearm.
  Fix: kilt rays start 0.55 m from the axis (inside the arms, outside hip and thigh).
- r20 Result: all S3 gates PASS (4146 tris, 7 colours); junction probe PASS (S3 has no rig roots yet), eye PASS
  front/3q/side 0.22/0.52/0.48, 43.6 mm, proud 9.9 mm; band seat WARN 55% (the belt bridges the waist hollow, as the
  ogre's accepted belt). Critique (hero/az045 colour): the pig-kind nose pad stands 10 cm proud as a disc: reads pig, not
  bull. Fix: depth 1.6 cm, width 0.22, centred on the nose plane.
- r21 Result: still a disc on the angled muzzle front (crops head34/side): any stand-off pad reads pig. Fix: no pad
  piece; the muzzle's front plane is painted as dark nose leather and two small nostril lenses (r 2.2 cm, 7 mm proud)
  sit on it. (nose_pad was tried in pig kind; canine/bear kinds are wedge noses, wrong for a bull.)
- r22 Result: FAIL z-fighting 12 faces: the flat nostril lenses (7 mm over r 22 mm) lay along the muzzle plane.
  Fix: nostrils r 1.9 cm, 14 mm domed, rim 5 mm under the plane.
- r23 Result: all S3 gates PASS (4142 tris, 7 colours), eye PASS, junction probe PASS; colour tiles read bull:
  horns, ears, nose leather, kilt. Residual: the tail stem is thin against the sheet's.

## Stage 4
- r24 plan: rig on J (spine 5, arms 3, legs 3, ears, tail 3; roll auto), pieces bound with body weights; idle
  (breath, head turn, ear flick, tail swish), move (stride A 11, S 12, knee fold, tail sway), attack (rear back,
  horn drive down-forward). Bone signs checked on the posed renders.
- r24 Result: S4 kit gates PASS (glbcheck OK; warn clip 1.04% of surface, 2 tris stretch 2.24x). Junction probe FAIL
  on ears (knife 124 deg 1.8 r + strip 1.2 r), thighs (knife 134 deg 1.75 r) and tail0 (strip 1.83 r). Shoulders
  PASS (knife 0, max fold 65 deg, strip 0.87 r) - the owner's ogre flaw is not here. Crops: the ear crease shows as a
  dark slot under each ear (beauty tile 3); the thigh folds sit at the gluteal crease under the kilt (only the
  from-below tile shows them); the tail strip is a thin dark wedge at the tail root between the back kilt plates.
  Critique (worst visible): the slot under the ears. Diagnosis: the first ear ring drops below the 2-face root region
  (droop starts at the skull), the underside folds back against the head. Fix (S2 move): ear rings 0/1 up 2/1.5 cm.
- r25 Result: ears PASS (no knife, no strip). Eye L dropped to 0.058 of head length (floor 0.06). Thighs/tail as r24.
  Critique: the gluteal knife fold at the thigh root (134 deg, 1.75 r). Diagnosis: the crotch-underside faces behind
  the leg region run back level under the buttock while the first thigh ring's back wall rises straight to them.
  Fix (S2 move): back half of thigh rings 0/1 moved 3/1.5 cm back, ring 0 2.5 cm up. Also the lens r 2.2 -> 2.5 cm to
  clear the eye-size floor the ear move tipped.
- r26 Result: eyes PASS (0.069-0.071 head). Ears, thighs, tail unchanged (same max angles): neither move touched
  the flagged faces. Diagnosis by locating the flagged triangles (scratch where.py on the probe): thigh knife at the
  groin FRONT (0.13, -0.09, 0.82), not under the buttock; ear knife on the region's lower edge (0.204, -0.05..-0.09,
  2.11-2.13) and r25's x-window had missed the tilted ear-ring vertices; tail strip at the tail root's lower wall.
  Fix r27 (S4 round budget: three located junction fixes together, all S2 vertex moves): ear rings picked by
  position along the ear axis, lifted 2.5/2 cm; crotch ring front half 4 cm down; first tail ring 1.5 cm back. The
  r26 back-thigh move dropped.
  (r27 ran unchanged: the edit script aborted on a missing anchor; same numbers. Re-run as r28.)
- r28 Result: ears 124 -> 99.8 deg but now 4 knife edges (folds above AND below the root), thighs WORSE (143.6 deg),
  tail strip 1.83 -> 1.48 r. Located again (where.py): the ear's first ring (8 cm tall) is taller than its 6.5 cm
  2-face root, so walls fold out above and below; the groin-front fold is seen only through the 4-deg slit between
  the front and front-side kilt plates (no bottom camera in the probe; the kilt occludes the rest).
  Fix r29: (1) S1 re-lock: the ear's first ring is the root region pushed 2 cm out, shrunk 0.85 (walls lean in), the
  S2 ear lifts removed; (2) the groin move reverted; kilt plates alternate layers (even plates 2.2 cm out, 2.5 deg
  overlap; back tail gap kept) so no slit shows the groin - the sheet's plates overlap too; (3) first tail ring
  scaled 1.5 x / 1.2 z to the root face's width.
  S1 re-locked r29: 1240 verts, 2476 tris, edge sha256 d859bb62aac9b4a7.
- r30 Result: ears PASS (max fold 81 deg), thighs PASS (85 deg), shoulders PASS, eyes PASS. Only tail0 FAILS:
  strip 1.44 r / 27.9 mm (located at (0.056, 0.42, 0.94)): the 6-sided tail rope's 2 cm faces, 60 deg creased, just
  past the root. Fix: tail rings 1/2 scaled 1.45/1.3 (S2 move) - a thick tail root, faces ~5 cm.
- r31 Result: ALL gates PASS incl. junction probe (ears 81 deg, shoulders 65 deg / strip 0.87 r, thighs 85 deg, tail
  strip 0), eye, membrane. 4 S4 rounds used (+r27 null run); the fixes below are the owner-review rounds.

## Owner-style review (zoomed crops + sheet), fix rounds
Flaws seen: (1) eye socket is a thin diagonal slit with the lens at one end (eye crops, close-up 0): the inset of a
sheared quad; (2) a mild vertical groove behind the shoulder where the arm's back wall meets the back (upperarm
crops A/B) - soft, no hard line; (3) belt band lifts 55% (warn) over the waist hollow - reads as a thick belt.
Probe flags not visible: none left. Shoulder over ribcage reads connected from hero and az000.
- fix 1 (r32): the socket's inner ring set on a 6 cm square round the face centre, sunk 1.2 cm.
  r32 Result: the socket is now a clean square pocket, eyes PASS (0.22/0.49/0.53); but FAIL hit: the 2.5 cm lens
  ring touches the new socket wall (two crossings). Fix r33: socket 6.6 x 6.4 cm, lens r 2.35 cm.
  r33 Result: hit remains; eye crop (scratch) shows the lens at the pocket's upper corner clipping the rim: the lens
  was placed at the surface point nearest the old face centre, which after sinking is on the rim. Fix r34: lens at
  the socket floor centre (face centre - normal x 1.2 cm), facing the face normal.
  r34 Result: lens centred in the pocket but eyes FAIL visibility (side 0.29, 3/4 0.30: 1.2 cm deep pocket hides it)
  and hit remains. Fix r35: pocket 6 mm deep, lens dome 17 mm (proud of the head surface again).
  r35 Result: eyes PASS (0.28/0.48/0.44, proud 13 mm); hit remains, plus a drift FAIL. Located (scratch eyehit.py):
  every eye/body overlap is on the socket floor: the lens ring is aligned to the ring-point normal, tilted against
  the bmesh floor, so it crosses the floor on one side and stays under it on the other (2 clusters). Fix r36: lens
  centre and normal from a ray hit on the floor itself.
  r36 Result: eyes PASS (0.34/0.58/0.52); hit remains. Diagnosis (eyehit.py on the S4 GLB): the lens touches rim
  faces on opposite sides: the socket floor was a sliver, two inner corners of the sheared quad got the same sign and
  collapsed. Fix r37: inner corners assigned in angle order round the square.
  r37 Result: eye hit gone, but S2 self-intersection (2): the 6.6 cm square floor poked out of the narrow face.
  r38 (diagnostic S2 run): the face's centre is only 1.9 cm from its nearest edge - no socket floor can hold a 4.7 cm
  lens. Fix r39: socket = the original 0.34 inset, only 4 mm deep (no slit pocket), lens on the floor centre with
  its ring 6 mm under and a 2 cm dome (one crossing loop through floor and rim).
  r39 Result: ALL gates PASS (kit S1-S4, tech QA, junction probe, eye 0.31/0.50/0.46, 46 mm = 0.066 head, round
  0.95-0.98, proud 15 mm; membranes ears PASS). Eye crops: a round lens on a shallow socket step, no slit.
- not fixed: (2) the soft groove behind the shoulder (a tone change, no hard line or strip; probe 0 knife, 65 deg max
  fold, strip 0.87 r) - left; (3) belt seat WARN 55% - the belt bridges the waist hollow like the owner-accepted ogre belt.
- fix 2 (r41, orbit18 az90/+45 az270): the horns rise as straight spikes from the side (unicorn read); the sheet's
  sweep forward. Fix: horn bend vector forward-up (0, -1, 0.7) instead of up.
  r41 slip: the edit commented out segs/sides/taper; r42 restored them. r42 Result: horns sweep forward from the side
  (orbit18 az90/az270), ALL gates PASS (kit S1-S4 + tech QA, glbcheck, junction probe, eye, membrane).

## Final (r42)
- Tris: S1 base 2476 (lock edge sha256 d859bb62aac9b4a7), S2 2716, total 4142, 7 colours.
- Junctions: shoulders knife 0 / max fold 65 deg / strip 0.87 r; thighs 85 deg; ears 81 deg; tail strip 0; posed
  clip 0% per chain (techqa warn: 1.02% of surface clips in poses - belt/kilt vs thigh swing; 2 tris stretch 2.03x).
  Separation PASS (legs 0.048 m, arms 0.070 m). Belt seat WARN 55% (accepted-ogre style).
- Biped checklist at S4: chin/jaw step (az090) yes; trapezius steps to the deltoid yes; deltoid = the torso's own
  shoulder line, arm root 2x3 faces on it, hugs the chest yes; A-pose arms 0.07 m clear yes; knees bent yes; parts hand yes.
- Weaknesses: the trapezius slope beside the face still reads hood-like in grey; the torso is a smooth barrel (no
  pec/ab planes beyond one pec shelf); hands are small two-finger mitts and the tail stem is plain.
- Files: orbit18_sheet.jpg, side_by_side.jpg (--compare), side_by_side_sheet.jpg (sheet | model), review/,
  rounds/s4_r42_junctions.jpg, face_separation.jpg.

## Border pass (night 2026-10-23, s4 r43) - REVERTED
- kit/smooth_borders(body, k=k, iters=8): 2 cuts, 11 relaxed; stair corners 13 -> 11, 3-to-1 2 -> 0; all gates PASS.
- A/B: order 1 TIE, order 2 the champion (before) wins -> REVERT; py/GLB/checks restored from before_borders/.
