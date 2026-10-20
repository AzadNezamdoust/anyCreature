# lizardman — t7 box model, zoo workflow v2

Sheet: refs/gpt/v3/lizardman/sheet_1.png (side TL, front TR, rear BL, top BR). refs.py --height 2.0 (skull top).
- The sheet's top view is not a true plan (1.26x the side length): dropped from blueprint.json; side + front only.
  Side marks added by hand (eye, snout, chin, shoulder, elbow, wrist, hip, knee, ankle, tail root).
- Side IoU ceiling: the side trace fills the triangle under the tail (tail underside to the heel, ~10% of the
  silhouette) as body, so the side IoU stays near 0.82 even when the contours match.
- Identity cue (lizardman, not crocodile/dragon/werewolf): an UPRIGHT reptile biped - a long narrow lizard snout on a
  thick neck with no ears or horns, inverted-triangle torso with a cream throat-chest-belly panel, heavy thighs,
  long-toed clawed feet, and a massive tail whose root fills the whole rump (belt line to crotch) and lies on the
  ground behind.
- Plan: minotaur loft (13-vertex half rings from 5 control points), arms from a region of the shoulder side whose top
  edge is the widest ring C2, legs from a 3 x 6 flank region L0 -> L1 (top edge = widest hip ring), tail from back
  columns 10-11 L0 -> L3 (seam walls removed). Groin / tail-root plan: thigh cols 2-7 and tail cols 10-11 both leave
  the crotch ring L0; cols 8-9 stay body faces (a 2-face gap); the tail's bottom wall leaves the crotch cap's back edge
  going back-and-down (37 deg), never straight down (a 90 deg concave crotch/tail fold = the werewolf knife).
  hand_three_finger (3 clawed fingers + thumb) and foot_biped (3 clawed toes) welded before the lock.
- Measured early (lesson: builders drift thin): scratch slice script vs sheet widths: chest+deltoid 0.39-0.43 vs
  sheet 0.37-0.40 at z 1.40-1.45, hip 0.31 = sheet, leg 0.335 at z 0.5 = sheet, head 0.26 wide x 0.53 long = sheet.

## Stage 1
- r01 First fit: all S1 gates PASS, 2812 tris, IoU side/front 0.771/0.835. Critique (az090, az180): the tail root is
  a vertical plate stuck to the rump with a shelf on top; the tail drops off its lower half. Diagnosis: hug ring =
  root loop pushed 5 cm straight back (a vertical plane with a horizontal top band) and ring 1 centred 16 cm lower.
  Fix: no hug; each tail ring = (top, bottom, half-width) read off the sheet's top and underside contours
  perpendicular to the tail axis.
- r02 Result: the tail top runs straight out of the back line (crops), IoU side 0.815; PASS, 2812 tris. Critique
  (head crops): a flat-topped duck-bill wedge: the front corner sat 3 cm off the tip (tiny tip faces, one long flat
  side), F1 a flat lid. Fix: snout front corners 10 cm back from the tip (a rounded nose), crown ring F2.
- r03 Result: domed skull and a rounded snout (head crops); PASS, 2860 tris. Critique (shoulder crop 0): a fin and a
  dark vertical notch at the arm's front root; arm too far out (slice: 0.46 at z 1.35 vs sheet 0.40). Diagnosis:
  the 2 x 3 root (0.17 deep) was shallower than the 0.25-deep first arm ring. Fix: root 2 x 4 cols 4-7, arm 5 cm in.
- r04 Result: no notch, IoU front 0.85; a collar band + a corner fin at the hug ring remain (shoulder crop 0).
  Fix: first arm ring = root rim pulled 45 % toward the deltoid section (lerp) instead of the pushed-out hug.
- r05 Result: FAIL self-intersection 4 pairs (0.27, -0.70, 1.365): the lerp ring's inner side reached the lats.
  Same fix completed: C0 W 0.24, deltoid ring centre x 0.355. PASS, 2920 tris; shoulder crops: the chest runs over
  the shoulder into the arm, no fin, no notch; the armpit is a plain open gap.
- r06 Critique (hip crops): a garter crease round the thigh top. Fix: the leg's 60 % transition ring removed (the
  region rim goes straight to the first thigh ring). Result: PASS, 2848 tris; crops (wire) show the thigh's outer
  wall running straight down from the widest hip ring, no shelf; the groin panel (cols 0-1) is the sheet's groin V.
- r07 LOCK (first, with orbit; orbit holds). Then S2-S4 run straight through to get the junction probe early.
  Probe (s4 r10): thighs + tail0 knife 93.2 deg (located, scratch where.py: the thigh's back wall at y -0.567 bulged
  past its root region edge into the gap columns) + seam strip 1.44 r; arm-vs-thigh posed clip 1.8 % (attack@18 side
  bend); S2 slivers 4.9 % (tail tip: 24-vertex rings on a 3 cm tail, and a 35 cm top wall at the root).
- r08 RE-LOCK (old lock in old_locks/lock_r07): thigh ring 0 r2 0.15 -> 0.135 centred y -0.705 (back wall no deeper
  than its root), tail resampled every 13 cm plus a root ring; attack side bend halved. Result: knives 0, clip 0,
  slivers 3.2 %; strip 1.42 r remains.
- r09/r10 RE-LOCK: tail region 3 columns (9-11, gap col 8), 2-1 ring reductions at y 0.15 and 0.62 (24 -> 14 -> 8
  vertices round the thin tail). Result: slivers PASS; strip unchanged 1.42 r / 21 mm (located: thigh front/back
  walls at the region's side edges, from the tall region edge to one ring).
- r11 RE-LOCK: the 50 % transition ring back on the leg (r06 dropped it for a crease the crops never confirmed).
  Result: junction probe PASS (thigh strip 0.87 r, tail 0.84 r, knife 0, max concave 74.8 deg).
- r12 RE-LOCK (determinism): stage 3 failed the lock hash although stage 1 was untouched: region_roles summed a set
  of BMVerts (order by memory address -> last-bit float differences); vertices now sorted by position (troll r15).
  3 runs reproduce it. LOCKED r12: 1592 verts, 3180 tris, edge sha256 b0057f1bf4567783, IoU side/front 0.814/0.849.
- Biped checklist at lock: chin/jaw step from az090 (J0 front -0.96 over the throat N0 -0.833) yes; neck ring set back
  and narrower than the jaw (N0 0.13 vs M1 0.14) yes; trapezius steps down neck -> shoulder (N0 0.13 -> T0 0.235 ->
  C2 0.355) yes; chest widens into the deltoid (C0 0.24 -> C2 0.355) and the arm root (2 x 4 faces, top edge on C2,
  lerp first ring) hugs the chest yes; A-pose arms, elbows 0.16 m clear of the waist yes; knees slightly bent, legs
  0.29 m apart, the tail between them yes; hands = parts-library hand_three_finger (3 clawed fingers + thumb) yes.

## Stage 2
- r13 plan: elbow / knee / waist loops, eye socket (inset in the E0 -> F0 face nearest the sheet eye), brow 6 mm out,
  mouth line (M0 sunk 6 mm round the snout), pec shelf (C1 front 1.8 cm forward, C0 underside). Result: all S2 gates
  PASS (lock + 3 loops + socket, IoU vs S1 min 0.996), 3364 tris.

## Stage 3
- r09/r10/r15 (before the final lock): z-fighting 6 faces on _rest_hand: claw tops on the finger tops. Fix (werewolf
  s3 r17): each claw shell 8 mm out along wrist -> claw. Result: PASS.
- r14 Result: all S3 gates PASS, 3836 tris, 7 colours. Critique (colour tiles): dark saturated green, a thin cream
  line under the tail (sheet: a broad cream underside). Fix: skin/cream lifted, tail underside = every tail face
  facing down. r16/r18 Result: PASS; the beauty orbit reads lime -> skin settled at #8ca25c (sheet olive).

## Stage 4
- r17 plan: rig on J (spine 5, arms 3, legs 3, tail 5 with a SHORT root bone tail0 -> tail1 = 0.16 m, roll auto),
  pieces bound with body weights; idle (breath, head turn, tail tip sweep), move (heavy stride, knee fold, arm swing,
  tail sway from tail2 on so the root stays between the legs), attack (right-arm claw rake, chest twist, tail lash).
- r17/r19 Result: kit S4 gates PASS (glbcheck OK; warn posed clip 0.81 % of surface), junction probe PASS, eyes PASS
  (0.19/0.46/0.50), separation PASS (legs 0.29 m, arms 0.16 m).

## Owner-style review (orbit18, zoomed junction crops, side_by_side_sheet), fix rounds
Flaws seen: (1) eye: the inset of the long sheared eye face is a diagonal slit with the lens at one end, and the
whole lens painted black (pupil faces matched by an unset index -1); (2) tail a thin rope from the rear (+45 az180,
az180) vs the sheet's broad paddle; (3) cream belly panel ends in a square apron below the belt (sheet: a groin V);
(4) feet are short blocky boots (foot_biped toes = 0.2 of the length; sheet: long splayed toes); (5) a soft dark
armpit wedge at the arm front (probe 0 knife, max fold 84.5 deg) - an armpit, left. No slits, folds, strips,
poke-through or floating pieces in the crops; shoulders round from top and +45 rear (no shelf); tail root and groin
broad and blended (thigh / tail-root crops).
- fix 1 (r20-r29): socket floor a 3.8 x 3.4 cm square round the face centre, 2 mm deep; pupil faces by face (amber
  lens + dark pupil disc, pupil ring 0.4 r); lens 3 mm under the floor with a 19 mm dome, turned a little forward
  (3/4 view had dropped to 0.31-0.34). Result: eyes PASS 0.24/0.42/0.49, 0.087 head, proud 14.8 mm; crops read a
  round amber eye with a pupil; the long face still shades as a faint wedge behind the lens.
- fix 2 (r30-r32): tail vertices behind the legs widened 18 % across (S2 move, ramped from y -0.42). Result: all
  gates + probe PASS (IoU vs S1 min 0.946), the tail broader from the rear; still narrower than the sheet's paddle.
- fix 3 (r33-r34): below the belt the cream narrows into the groin V. Result: all gates PASS.
- not fixed: (4) feet (no foot part with open_root has long toes; bird_foot cannot be welded) - residual;
  (5) armpit wedge - anatomy, no hard line.

## Final (s4 r34)
- Kit gates S1-S4 PASS (lock edge sha256 b0057f1bf4567783, glbcheck OK, tech QA PASS; warn posed clip 0.80 % of
  surface). Junction probe PASS: upper arms knife 0 / max 84.5 deg / slit 0.38 %; thighs knife 0 / 74.8 deg / strip
  0.87 r; tail0 knife 0 / strip 0.84 r; posed clip 0 % per chain. Eyes PASS 0.24/0.42/0.49. No membranes. Belt seat
  WARN 48.5 % (bridges the lower-back hollow, like the accepted ogre belt). Separation PASS (legs 0.29 m, arms 0.16 m).
- Tris: S1 base 3180, S2 3364, total 3836; 7 colours.
- Weaknesses: bulk still under the sheet's muscular build (arms, thighs, chest planes read as a smooth tube); feet are
  stubby blocks; the head from the front reads as a narrow hood (snout hides the face, no cheek/jaw planes).
- Files: orbit18_sheet.jpg, side_by_side.jpg (--compare), side_by_side_sheet.jpg, review/, stage4/lizardman.glb,
  rounds/s4_r34_junctions.jpg, checks/face_separation.jpg.
