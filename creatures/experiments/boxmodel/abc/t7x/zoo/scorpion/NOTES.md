# scorpion (t7x zoo, workflow v2)

Sheet: refs/gpt/v3/scorpion/sheet_1.png (2x2), refs.py --height 0.5 -> length 0.857 m. Views disagree: the top view
draws the tail straight back (telson behind the body), the side view curls it up over the rump; the side wins
(proportions and the tail), the top view gives widths and the leg plan. Top-view width 0.50 vs front 0.66 (refs warning):
leg reach set between the two.

**Identity cue:** the segmented tail curled up and forward over the back ending in a dark bulb + sting, two big
forward pincers, four legs a side from under a flat segmented body. All of it is in the S1 loft (tail = part of the
spine loft; pincers and legs extruded), nothing waits for S3.

Build: one loft of 10-vertex half rings, 51 stations: carapace (8), mesosoma 7 tergites as groove/crest pairs
(grooves dip only the upper ring vertices, so the lower-flank leg-root band stays flat), the rear centre line
(Catmull-Rom on the CENTRE LINE only; rings are placed on it with straight per-station sizes), 5 tail barrels
(joint 0.76, bulge, bulge), telson bulb, sting. Legs and pedipalps: octagon tubes from 2x2 face blocks (4 faces,
broad root) with a hug ring 6 mm out at 0.86 of the block size; pincer fingers are hexagon tubes from the two halves
of the palm end cap.

## Stage 1
- r00: FAIL self-intersection 20 pairs near (0.088, 0.112-0.124, 0.152); 4312 tris; IoU 0.60/0.60/0.51.
  Critique: reads as a scorpion from every view (tail curl, pincers, 8 legs). Worst gate problem: the self-hit at
  leg 3's root (az090 hidden). Diagnosis: leg 3/4 swept straight back at 44/62 deg from the root, so the coxa's rear
  wall cuts back into the flank. Fix: coxa leaves along the flank normal for 3 cm, then turns to the heading.
- r01: PASS (0 self-hits), 4312 tris, IoU 0.61/0.61/0.51. Critique: the legs read as thin straight stilts (az000,
  az090: tips only 0.19-0.25 out, knee lost in the body side), the sheet's legs are chunky and sprawl wide with the knee
  up at 0.2. Diagnosis: LEG_T radii 0.017 and reach 0.185. Fix: LEG_T re-fitted (femur 0.022, knee 0.2 at 0.1 out,
  tip 0.215 out), headings -8/30/50/64 so the side-view tips spread back as the sheet's.
- r02: PASS, 4312 tris, IoU 0.61/0.67/0.49 (front up: the sprawl). Critique: legs still read as spikes in az090 and
  the top view (sheet legs are about 1.3-1.5x as thick, fat barrel segments). Diagnosis: LEG_T radii. Fix: femur on x1.3.
- r03: PASS, 4312 tris, IoU 0.61/0.66/0.48. Legs now chunky. Critique: the pincer (hero, top) is a pointed spindle on
  a thin arm with thin fingers; the sheet's chela is a big round bulb with thick dark fingers. Diagnosis: CLAW
  stations 7-11 (long wrist taper, palm 0.106 x 0.126) and MOV/FIX radii. Fix: one pincer re-fit: round palm
  0.128 x 0.15 with a short back shoulder, arm x1.15-1.3, fingers ~1.35x thicker and opened wider.
- r04: PASS, 4344 tris, IoU 0.63/0.68/0.51. The pincer now reads (round palm, thick open fingers). Critique: the
  carapace narrows to a point (top, az000: a small face between big pincers); the sheet's carapace is a broad blunt
  trapezoid. Diagnosis: H0-C1 widths 0.038-0.085. Fix: front widths 0.050/0.068/0.076/0.080/0.083 (H0-H4), taller
  front cap; claw femur stations 6 mm out with the root block.
- r05: PASS, 4344 tris, IoU 0.63/0.68/0.51. Critique: reads as the sheet's scorpion from every view: blunt carapace,
  segmented back, curled tail, round pincers, eight chunky legs. Weakest: the legs read straight in az090 (the
  sheet's knees are lower and more bent). Lock now (base read is right; junctions are only measurable with the rig,
  so the S1 lock is re-opened if the S4 probe finds a root fault, logged here).
- r06 LOCK: 2174 verts, 4344 tris, edge sha256 7847cf24e3fc9b98. --junctions at S1: body open 0 / non-manifold 0;
  no rig and no eye piece yet, so the probe has no roots and the eye check fails by construction (S3/S4 gate it).

## Stage 2
- r01: PASS (lock assert, IoU vs S1 1.0, tech QA hit/float/zfight 0, slivers 0.6%). One logged change: the eye socket
  inset in the carapace front-top corner face, sunk 4 mm. Tech heatmaps clean. Critique: nothing new at S2 scale; the
  socket is small at round-sheet size (checked in the S3 eye crops).

## Stage 3
- r01: PASS (5 colours, 4424 tris, hit/float/zfight 0). Critique: the telson bulb and sting are tail-tan, the sheet's
  telson is the darkest mass (hero, az090); the whole creature reads muddy brown against the sheet's light tan.
  Diagnosis: the telson rule gated on c.y > 0.27 but the bulb hangs at y 0.19-0.30; palette values one step dark.
  Fix: telson rule on arc length + z > 0.3, palette a step lighter.
- r02: PASS, 4424 tris (body 4344 + 2 lenses 80). Telson + sting now dark, palette lighter. --junctions: body open 0,
  eye L/R PASS visible front/3q/side 0.37/0.60/0.45, 17.9 mm, round 1.0, proud 7 mm (no head bone yet: size checked
  at S4). Eye crops: a small dark round lens in a clean socket on the carapace corner, not hidden by the pincer arm.

## Stage 4
- r01 (all S1-S3 gates + tech QA PASS; posed clip warn 5.7%): junction probe FAIL on 11/11 roots. Crops (C view, from
  below) show a visible crease on the upper side of the leg 1/2 roots (red knife 92-97 deg) where the coxa runs level
  out of a flank face block whose normal points 33 deg down. Posed clip leg3 vs leg2/leg4 7-10% in move@1/13 (pink
  shows the femurs crossing). tail0 r = 180 mm and arm r = 138 mm are probe artifacts: their subtree vertices behind the
  root (the sting under the curl, the palm forward of the arm root) project to t <= 0 on the first bone and dominate
  the median, so the probe region swallows half the body; tail0 slit 3.14% and arm knife 2.0 r are not visible in crops.
  Fix (this round): RE-OPEN THE S1 LOCK (old lock in before_relock/): leg root blocks to ring faces 4-5 (level normal),
  leg heights re-based. Next: short root bones (probe r), then a smaller gait swing.

## Stage 1 re-lock
- r07: PASS, 4344 tris, IoU 0.63/0.67/0.50; legs now leave the side at mid-flank (az090/hero read the same, legs a
  touch higher, body underside shows). Re-lock next round.
- r08 LOCK: 2174 verts, 4344 tris, edge sha256 e816f5d821fd0b0d. S2 r02 PASS (eye socket re-applied), S3 r03 PASS
  (4424 tris, 5 colours, tech QA 0); round sheets read as before.

## Stage 4 (after re-lock)
- r02: tail0 now PASS (r 42 mm, knife 0, slit 0) and the arm radius sane (33 mm): the short root bones fixed the
  probe artifact. Still FAIL: legs/arm knife 1.2-1.3 r at 91-101 deg and seam strips 1.6-2.0 r (3-5 mm wide); crops
  (B and C angles) show a thin dark crease ring at each coxa root = the hug-ring wall band. Posed clip leg3 vs leg2/4
  7-10% in move. Fix next: S2 root fillet (below), then the gait.

## Stage 2 (root fillet)
- r03 (S2, root fillet): PASS. S3 r04 PASS. S4 r03 probe: knife folds 0 on every root (max concave 77-86 deg),
  leg1, arm, tail0 PASS. Left: legs 3/4 strips 1.47/1.86 r (inner side of the coxa turn: the plan path kinks at 3 cm
  from the normal to a 50/64 deg heading, the inner wall faces crowd into a creased band), and posed clip 6.5-8.9%
  (legs 2-4 in move).
- r04 (S2): one fix: the coxa's plan path turns smoothly (smoothstep 1.2-7 cm) instead of the 3 cm kink; all leg
  sections moved in S2 (vertex moves only), paint and rig follow the same paths.
  r04 FAIL: S2 IoU vs S1 bottom 0.88 (the 1.2-7 cm turn swung every leg lateral). r05: turn over 0.8-5.2 cm, centred
  on the old kink.
- r05 (S2): PASS, IoU vs S1 min 0.976. S3 re-run next.

## Stage 4 final round
- r04 fix: the move clip as a metachronal wave (quarter-cycle lag per leg, right side half a cycle off), swing 5 deg,
  lift 10 deg (was an alternating tetrapod at 9/14 deg that crossed neighbouring femurs).
- r04: S4 gates PASS (glbcheck OK, tech QA 0, clip warn 2.0%, was 5.7%); probe: tail0, legs 1-2, arm, eyes PASS.
  FAIL: legs 3/4 posed clip 3.4-4.6% (leg3 vs leg4 at move@11/22) and seam strips 1.58/1.81 r (5.0-5.6 mm wide vs
  18 mm median face). Crops: the leg 3/4 roots read clean from A/B/C (no crease line visible; the yellow flag is a
  sliver on the hug wall at the C-view edge) -> strip = noise by rule 6.3, clip is real. S4 round budget (4) used;
  continuing as review fix rounds (brief: up to 3).

## Review fix rounds
- f1 (S4 r05): legs 3 and 4 step in phase (wave lags 0 / 90 / 180 / 180 deg), so the two rear femurs never swing
  against each other.
  Result: posed clip 0.0% on every chain (tech QA clip warn 1.08%); only legs 3/4 seam strips remain.
- f2 (S2 r06 + S3 r06 + S4 r06): legs 3/4 strips (5.0-5.6 mm wide band on the hug wall, worst on the inner side of the
  coxa turn). Hug ring 13 mm out at 0.88, first coxa ring 3.0 cm, plan turn starts at 1.8 cm (past the first ring).
  Result: strips gone everywhere (max 0.95 r); knife 0; legs 1, 2, 4, arm, tail0, eyes PASS. New: leg3 vs leg4 posed
  clip 1.98% (leg4 0.74%) at move@6: the moved-out coxae put the in-phase rear femurs closer, and the 5 deg back-swing
  grazes them. Crops/pink: the femurs touch near the knees in the back-swing frame.
- f3 (S4 r07): rear pair (legs 3, 4) swing 2.5 deg instead of 5.
  Result (S4 r07, final): ALL GATES PASS: S1-S3 gates, lock assert, glbcheck OK (idle/move/attack), tech QA hit/float/
  zfight/drift/fold 0, slivers 0.6%, posed clip warn 1.08%; junction probe PASS on all 11 roots (tail0, legs 1-4 L/R,
  arm L/R: open 0, knife 0, strips <= 0.99 r, slit 0, poke 0, gaps 0, chain clip <= 1%), eyes PASS (0.36/0.59/0.45,
  18 mm = 0.174 head, round 1.0, proud 7 mm). Tris: stage 1 4344, total 4424 (body 4344 + eyes 80).

## Owner-style review (orbit18_sheet.jpg, side_by_side_sheet.jpg, junction crops s4_r07)
Looked at every junction row and the 18-view orbit: no slit, speck, knife fold, seam strip, pinch, poke-through or
floating piece is visible at the leg, pincer or tail roots; the coxae leave the flank through a broad fillet; the tail
root blends over the rump. The 3 fix rounds went to the gate flaws above (gait clip, hug-wall strips, rear-pair swing).
Residual (visible, not fixed: fix-round budget used):
1. The body is slimmer than the sheet's: next to the long legs the carapace/mesosoma read small in az000 and top.
2. The tergite segmentation is shape-only and faint (a 9% groove dip); the sheet's plates read as clear bands.
3. Legs are smooth tapered tubes: the joint pinch rings are too soft to read as the sheet's knobby segments.
Also: the pincer fingers graze each other in the snap (tech QA pink, warn only).
Outputs: orbit18_sheet.jpg and side_by_side_sheet.jpg (checks.py), side_by_side.jpg (run.py --compare), review/,
rounds/s4_r07_junctions.jpg.

## Border pass (night 2026-10-23, s4 r08) - REVERTED
- kit/smooth_borders(body, k=k, iters=8): 4 despeckled, 3 cuts, 64 relaxed; stair corners 49 -> 34, 3-to-1 8 -> 0; all gates PASS.
- A/B: TIE both orders -> champion kept; py/GLB/checks restored from before_borders/.
