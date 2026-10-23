# ogre (t7 hand box-model, biped) - NOTES

Technique from wolf_base (t7r line). The spine loft stands upright: one loft of 6-vertex half rings from the crotch to the skull top (14 sections). The legs are 2-face regions of the crotch-hip span, extruded as horizontal hexagons. The arms are 2-face regions of the chest-shoulder span, with a tilted deltoid ring first. The ears are 1-face extrusions of the head side. Stage 0: blueprint.json was traced from reference/sheet.png with kit/refs.py (height 2.0 m). The sheet's top view is turned, so the top outline was removed and only side and front are used.

## Stage 1
- r1: first fit. Gates PASS, 620 tris, IoU side/front 0.863/0.823. Critique: az000. The torso reads as a box with a flat front. Diagnosis: the BODY front-side vertex at (0.7, 0.85) makes a broad flat belly face. Fix: the BODY profile is rounder (front-side vertex 0.62/0.78, widest vertex lower).
- r2: Result: FAIL, 4 self-intersecting pairs at the armpit. The torso's widest vertex had moved to the back-side position and bulged into the arm root. Fix: keep the widest vertex at index 2, with index 3 at 0.93 W.
- r3: Result: gates PASS, but little visible change. Critique: az000. The shoulders are square. Diagnosis: the trapezius ring is narrow (C2 W 0.38) and the deltoid top sits low. Fix: C2 W 0.44, N0 W 0.30, the deltoid ring tilted more (dz -0.10) and raised.
- r4: Result: slightly better (front 0.825). Critique: az000. The hands read as small stumps next to the ref's big fists. Fix: the hand sections were enlarged (rx/ry 0.16/0.19 and 0.14/0.16).
- r5: Result: gates PASS, IoU 0.863/0.822.
- r6 (LOCK): 312 verts, 620 tris, edge sha256 754bb4920c3b8a6c.

## Stage 2
- r1: Joint rings at the knee, ankle, elbow, shoulder, waist and neck. An eye socket was inset into the face between the nose and brow rings and pushed 12 mm in. The brow ridge was moved forward and out, the nose tip forward, and the jaw forward. Result: gates PASS, 772 tris, min IoU vs s1 0.997, slivers 0.5%.

## Stage 3
- r1: Five colours: olive skin, a tan belly and chest along the existing loops, brown leather, cream tusks and nails, and dark eyes. Pieces: lens eyes, tusks, 4 toenails per foot, a belt band and a diagonal chest strap, both ray-cast onto the body (inner face sunk, outer face standing off), and front and back loincloth flaps with jagged hems. Result: FAIL, slivers 2.6% (the flaps' 1.2 cm layers). The skin read too dark.
- r2: Fix: the flap layers were moved 3 cm apart, the strap made 16 cm wide, the tusks moved forward and lengthened, and the palette lifted. Result: gates PASS, 1676 tris, 5 colours.

## Stage 4
- r1: Rig with 11 bones plus .R mirrors (roll auto). Clips: idle 48 (breathing, head turn), move 33 (heavy walk), attack 32 (right-arm hammer blow). Result: FAIL, drift 1 (the front flap).
- r2: Rigid hip binding for the cloth was tried. Result: worse (3 drift), and it was reverted.
- r3-r5: The flap top was sunk 4 cm, the belt raised to z 0.80, the flaps' top raised, and the thigh swing reduced. Result: still drift 1. A per-vertex probe on the GLB showed under 2 mm nearest-surface drift. The gate anchors on the piece's first 12 vertices, and those were the flap hem hanging in front of the thigh.
- r6: Fix: a short waddle step (thigh swing 8 deg).
- r7: Fix: the flap vertices are now built row by row from the sunk top row, so the seat is the belt line. Result: all gates PASS. Clip warning only (0.22% of surface).

Checks: orbit18_sheet.jpg (18 views) shows every view reading, with no collapse. Fusion on the rest mesh: legs L-R 0.26 m, each arm to the torso 0.125 m, so nothing is fused (separation.json). side_by_side.jpg pairs the sheet's side, front and rear with the model.

Triangles: stage 1 620, stage 2 772, total 1676. Rounds: s1 6, s2 1, s3 2, s4 7.
Weaknesses: the torso stays boxy at 6 vertices per half ring. The tusks are thin and hard to see. The hands are plain fists with no fingers. The walk step is short.

## Fix pass (zoo reviews, fable + opus merged)
Fix list, shape first: head small and sunk (both reviews); belly pale area wraps like a vest (fable); wrist has no taper, hands small (opus); loincloth bulky (opus); tusks thin (fable). Fable's leg +15% was not taken: the sheet's legs are short and thick.
- Base change, stage 1 re-locked: head rings H0-H4 scaled 1.2x about the neck (z 1.66), 1.15x deep, 2.5 cm forward; lower jaw a further 2.5 cm forward; N0 front 5 cm forward to carry the jaw; ears follow the head; wrist ring narrowed (0.10/0.115), fist rings enlarged. New lock 312 verts, 620 tris, edge sha256 dd89f81e709100ed. A first try (4 cm forward) failed fold-overs 0.60% area at the right shoulder in the attack.
- Stage 3: belly colour now a front patch (|x| < 0.31, n.y < -0.55); loincloth layers 3.0 -> 2.1 cm; tusks wider (3 cm root) and 17 cm long.
- Stage 4: attack wind-up 95 -> 80 deg upper arm (fold-overs). Result: all gates PASS, clip warning 0.29% of surface. Separation PASS (legs 0.26 m, arms 0.125 m). Total 1676 tris.
Not fixed: no fingers or toe blocks (fists and nails stay); torso still boxy.

## Fix pass 2 (review2 fable + opus merged, concept sheet as referee)
Fix list, shape first: belly weak, no hanging sphere (both); arms thin tubes, fists small (both); jaw weak, skull pointed (fable). Opus "raise the head and pull it back over the spine" was not taken: the sheet head sits low and forward of the shoulders.
- Base change, stage 1 re-locked: B0/B1 front 11-12 cm forward (yf -0.60/-0.64), W 0.55/0.54; B2 and L1 front follow. Arm rings 1-3 x1.2-1.3 thick and 3 cm out (forearm bulk), wrist kept narrow, fist ring 0.21/0.24, last ring tapers. Lower jaw a further 2.5 cm forward; H3-H4 W +3 cm (rounder skull). New lock 312 verts, 620 tris, edge hash ec78e52362781631. IoU side/front 0.837/0.804.
- Stage 3: belly patch follows the bulge (|x| < 0.38, n.y < -0.45).
- Result: all gates PASS first try, clip warning 0.32% of surface. Separation PASS (legs 0.26 m, arms 0.139 m).
Not fixed: no fingers; torso still 6 vertices per half ring.

## Poly pass 3 (denser main mesh)
Goal: about 2x triangles, mostly in the body loft, re-fitted to the traced sheet (no subdivision, no remesh).
- Base change: loft 14 -> 21 stations (added at the belly underside, belly widest/top, trapezius slope, mouth, forehead, skull dome); half rings 6 -> 14 vertices, round profiles with the widest point a little forward. Back of chest/shoulders pushed to the sheet's 0.50-0.52 m hump. Legs and arms: 10-sided rings on 4-face roots, legs 6 -> 12 sections (thigh, knee, calf), arms 7 -> 14 (deltoid, upper arm, elbow, forearm bulk); shoulder ring tilt eased (sloped shoulder of the sheet front). Ears and eye face re-indexed on the new rings.
- Stage 1 re-locked (pass-2 lock kept in before3/): r8 trial lock 1832 tris, then r9 final lock 1082 verts, 2160 tris, edge sha256 4410656561282016. IoU side/front 0.848/0.805 (was 0.837/0.804).
- Stage 2: the same 6 joint rings (knee, ankle, elbow, shoulder, waist, neck) and the eye socket on the new topology; brow/jaw moves cover the 3 front vertices. 2440 tris, min IoU vs s1 0.998.
- Stage 3: s4 r13-r15 FAIL hit: the back flap's outer columns passed through the rounder thigh roots (flap now x <= 0.30, hanging rows 7/5 cm off), and the belt's two edges crossed the rounder hips separately (belt 32 segments, lower edge sunk 1 cm, upper edge 4 mm off). Other details unchanged.
- Stage 4 r16: all gates PASS, glbcheck OK; clip warning 1.54% of surface. Separation PASS (legs L-R 0.22 m, arms vs torso 0.044 m).
- Total 3408 tris (was 1676): body 772 -> 2440, details 904 -> 968, so 96% of the increase is in the body. before_after3.jpg, orbit18_sheet.jpg, side_by_side.jpg refreshed.
- Not fixed: no fingers; arms still read as blocky boxes at the fists.

## Poly pass 3 review: REVERT
Review: eyes lost under a visor-like brow, belly and arms ring-banded, helmet-like head. Verdict REVERT.
- ogre.py and stage1_lock.json restored from before3/ (pass-2 loft: 14 stations, 6-vertex half rings, 6-section legs, 7-section arms). Stage 1 re-run to refresh the stage-1 masks (the pass-3 masks failed the s2 IoU gate on top/bottom); it matches the pass-2 lock (620 tris).
- Stage 4 r18: all gates PASS, clip warning 0.32% of surface. Separation PASS (legs 0.26 m, arms 0.139 m). Total 1676 tris.
- Pass-3 renders and script kept in pass3/. before_after4.jpg: before3 | 2x pass | now; now matches before3.

## Fix pass 5 (owner: "too bad relative to others")
Diagnosis vs the sheet and bear/golem/knight, shape and face first:
1. Head reads as a tall box helmet: big flat cranium cap rising to the back, skull deep into the hump; the sheet's skull is low and round over a wide jaw.
2. Flat face front (front-side vertex at 0.65 W): the face is a slab, not a muzzle.
3. Eye is a 1.5 cm dot under a visor brow: unreadable at hero distance.
4. Arms are straight columns of equal thickness (no elbow taper), so they read as pillars.
5. Belly colour is a rectangular block running up to the chest corners, not the sheet's oval.
Fixes (t7 box-model, same topology):
- Base change, stage 1 re-locked twice (r19 trial, r20 final): HEAD profile front-side vertex 0.58/0.78; H2 depth back 0.12 -> 0.09; H3 lower (1.925) and narrower (W 0.15), forehead forward; H4 3 cm lower, narrower, centred over the face. Elbow ring 0.17/0.20 -> 0.135/0.165, upper arm 0.16/0.20. Lock 312 verts, 620 tris, edge sha256 97106fc24b44be29. IoU side/front 0.837/0.805.
- Stage 2: brow forward move 2.5 -> 1.2 cm (no visor over the eye).
- Stage 3: lens eye r 1.5 -> 2.6 cm in the same socket; belly patch an oval (z 1.0 +- 0.30, |x| < 0.40).
- Result r20: all gates PASS, clip warning 0.27% of surface. Separation PASS (legs 0.26 m, arms 0.146 m). Total 1676 tris. before_after5.jpg, orbit18_sheet.jpg, side_by_side.jpg refreshed; old renders and lock in before5/.
Not fixed: hands are still plain fist blocks; torso 6-vertex half rings.

## Crop pass 6 (owner crops: strap at shoulder, belly/loincloth)
Probe on the stage-4 GLB and the hero view (both crops sit in s4_hero; before6/ holds the old renders).
1. Strap at the shoulder: each band segment took its own ray hit, so where the strap crosses the shoulder-arm crease the hits dived in and out; the outer face folded and skin showed through it as specks at the strap end.
2. Belly over the loincloth: the belt's upper edge hit the belly overhang far out and its lower edge the hips further in, so the belt top sat under the overhang as a dark slit between belly and belt.
Fix (band() in ogre.py, the t7 bridge): the hits come first, then the outer face is evened out. Each edge takes the other edge's larger radius when the two are close (5 cm on the strap, 15 cm on the belt), and one relax pass along the band bridges creases. The inner face keeps its own hit, sunk 1 cm, so nothing passes through the arm. A first try (shared inner radius, two relax passes) FAILED hit 4 and fold-overs 0.95%; it was replaced.
- Result r23: all gates PASS, clip warning 0.36% of surface (strap clip 6, was 3). Total 1676 tris. Stage 1 lock unchanged. crop_fix.jpg, orbit18_sheet.jpg, side_by_side.jpg refreshed.

## Fix pass 8 (owner: no shoulder, no chin; keep the dense mesh)
Owner update: the pass-3 revert made the ogre low-poly again; restart from the dense pass-3 script (pass3/), keep the later eye, belly, strap and belt fixes, then add shoulders and chin. Old renders, script and lock in before8/.
- Base: pass3/ogre.py (21-station loft, 14-vertex half rings, 12-section legs, 14-section arms). Ported: pass-5 low round dome (H2b-H4 lower and narrower, no helmet), brow move 1.2 cm (no visor), lens eye r 2.6 cm, oval belly patch, crop-6 band() (outer face evened, relaxed; belt keeps its lower/upper sink and share 0.15).
- Shoulders: trapezius rings narrowed (C1 W 0.47, C2a 0.39, C2 0.31) so the neck steps down to the shoulder. Deltoid cap: the first arm ring smaller and tilted outer side up (0.12/0.19, dz -0.07), the second a bulge wider than the upper arm (0.195/0.25 at z 1.40, x 0.71), then the upper arm narrower (0.18, 0.16). r29 FAIL: 4 self-intersecting pairs at the arm root (the bulge's inner side inside the torso); fixed by moving the bulge out to x 0.71.
- Chin: new jaw-line ring H0u under the lower jaw (front 2.5 cm ahead of the old jaw line), the neck ring N0 set back (front -0.08) and narrower (W 0.25), so a lower jaw plane with a visible underside separates head from neck and chest.
- Stage 1 re-locked (r25, r26, r30 trials; r32 final): 1108 verts, 2212 tris, edge sha256 0bdbb6f2319f87d2. IoU side/front 0.843/0.783.
- Stage 4 r33: all gates PASS; warnings: clip 1.54% of surface, 2 triangles stretch 2.04x. Separation PASS (legs L-R 0.224 m, arms vs torso 0.044 m). fix8.jpg (hero, shoulder, head side; before | after), orbit18_sheet.jpg, side_by_side.jpg refreshed.
- Not fixed: ring banding on the belly and arms is still visible in flat shading; hands are plain fists.

## Fix pass 8b (owner: "his shoulder is like not connected to the chest"; eyes lost)
- Shoulder: the torso carries the shoulder line. C0 W 0.50 -> 0.52, C1 0.47 -> 0.55, C2a 0.39 -> 0.47, C2 0.31 -> 0.34, so the chest planes run up and out into the deltoid. First arm ring moved out to the torso edge and barely tilted ((0.65, 0.20, 1.47), dz -0.03), so it no longer caps above the shoulder line; the deltoid bulge (0.19/0.25) then steps down into the upper arm. Shoulder width unchanged (about 0.91 m).
- Eye: the lens sits 8 mm out of the dense socket and reads again under the brow. Chin kept.
- Stage 1 re-locked r34: 1108 verts, 2212 tris, edge sha256 8c03805f26d213ca, IoU side/front 0.843/0.790.
- s4 r35 FAIL hit 1: the strap over the wider shoulder. Fix: strap plane steeper (e1 0.78/0.85) with share 0.10. r36: all gates PASS; warnings: clip 1.70% of surface, 2 triangles stretch 2.04x. Separation PASS (legs 0.224 m, arms 0.044 m). fix8.jpg, orbit18_sheet.jpg and side_by_side.jpg refreshed.

## Fix pass 8c (owner redline: narrow, hard crease at the shoulder join)
- The arm root now takes 5 faces of the C0-C1 span (was 4), starting one face further forward on the chest side (ARM_ROOT 6 -> 5); limb() takes a face count. The first arm ring is a broad, flat transition ring that hugs the chest side ((0.60, 0.19, 1.44), 0.09/0.27). The chest planes run across it over the deltoid bulge into the upper arm, with no thin strip or sharp fold. Shoulder width, eye, chin and strap are unchanged.
- Stage 1 re-locked r37: 1164 verts, 2324 tris, edge sha256 d564cbd67478aa02, IoU side/front 0.843/0.793.
- s4 r38: all gates PASS first try; warnings: clip 1.57% of surface, 2 triangles stretch 2.04x. fix8.jpg, orbit18_sheet.jpg and side_by_side.jpg refreshed.

## Detail pass (2026-10-23 night, tier 3: 6 -> 12+ groups; backup before_detail/)
- r39 (S4): seated chunky pieces (detail_pieces.py): brow ridges, nostril mounds (dark cap), navel, belly fold (broad
  STEP step over the belt), kneecaps, 3 knuckle bumps per fist, 2 shoulder warts, lower lip roll. Kit gates OK,
  detail PASS 13 groups. Junction/eye FAILs are the champion's own (WORKFLOW s9 calibration: shoulder strip/shelf
  1.13 r, attack arm-thigh posed clip 3.7-6.5 %, eye side 0.08 under the brow) - unchanged by this pass.
  A/B Opus both orders: variant won BOTH -> ADOPT. Residuals: knuckle dots + hex navel read slightly like bolts.

## Night fix 2026-10-23: deltoid shelf (kit shelf check; backup before_deltoid/, champion = r39 detail pass)
- r40. Critique: kit shoulder-shelf FAIL both arms 3.45 r^2 x 2.55 r; crops j0/j1 A/B show a flat level disc on top of each deltoid (T-bar), front view square shoulders vs the sheet's sloped ones. Diagnosis: ARM[0] (z 1.44, outer z 1.47) and ARM[1] (outer x 0.91 z 1.41) are horizontal rings, so C1 (0.545, 1.50) -> ARM[0] outer -> ARM[1] outer drops only 9 cm over 37 cm (12-15 deg). Fix (S1 positions, re-locked, edge sha256 06d2fd25add8d3fb): the outer line slopes from C1 over the arm and rolls into the outer wall: ARM[0] z 1.40, ARM[1] (0.72, 0.21, 1.30) rx 0.16, ARM[2] z 1.21 rx 0.17, ARM[3] 1.15, ARM[4] 1.085; 5-face root, broad first ring, chin, eye, strap untouched.
- r40 result: shelf 3.45 -> 0.28 r^2 x 0.8 r (PASS both), upperarm.L strip 1.13 -> 0.56 r PASS; upperarm.R still knife 0.44 r/148 deg + strip 1.14 r at the trapezius top (pre-existing, R only) + posed clip arm.R/thigh.R attack 3.8/6.2% (pre-existing); eyes side 0.08 FAIL (pre-existing); detail PASS 13 groups; kit gates PASS; clips PASS after --fix-clips. IoU front 0.793 -> 0.804. A/B fresh Opus seats: AB -> variant, BA -> champion (flip = tie -> champion). BA seat: deltoid top "a little boxier", back view squarer.
- r42. Critique (BA seat r40): the new deltoid top is still a flat-fronted box from the back 3/4 (square front/back corners). Diagnosis: ARM[0]/ARM[1] corners (b = +-1) stay at the ring's z. Fix: hexpos dome term, outer-side corners of ARM[0]/ARM[1] drop 3.5/5 cm x b^2 (S1 positions, re-locked; edge hash unchanged 06d2fd25add8d3fb).
- r42 result: shelf 0.0 r^2 both arms, upperarm.L knife 0 / strip 0.57 r PASS; upperarm.R knife 0.23 r/133 deg + strip 1.16 r (trapezius top, R side only, pre-existing) and posed clip 3.83/6.21% (pre-existing); eyes side 0.08 (pre-existing); kit gates PASS, detail PASS 13 groups, clips PASS after --fix-clips; 4380 tris. A/B fresh Opus seats vs champion r39: AB -> variant, BA -> variant: ADOPT (rounded cap flows from the trapezius into the arm, closer to the sheet).
- r43 (clip, stage 4 only): Critique: posed clip arm.R through thigh.R in attack@17-18 3.8/6.2% (junction rows j1/j3, pink on the thigh front). Fix: the blow ends higher (upperarm.R 35 -> 52 at f18, 25 -> 40 at f24). Result: 2.64% @17 / 4.16% @20, still FAIL. (Kit gotcha: --fix-clips takes authored clips from stage4/before_clips/ while the joint rest is unchanged, so the fresh build is copied there first.)
- r44: the arm also swings out through the blow (upperarm.R Z -14 at f18, -10 at f24; Z -15 moves the hand.R tail outward x -0.87 -> -1.14 in a rest-pose probe).
- r44 result: posed clip 0% both chains (arm.R / thigh.R), clips PASS after --fix-clips. Posed A/B at attack@18 (front + hero), fresh Opus seats: AB -> variant, BA -> variant: ADOPT (fist clear of the belly, the blow reads). Remaining junction FAILs: upperarm.R "strip 1.16 r / knife 0.23 r" = the N0 -> H0u chin/neck step at x 0.25, z 1.645-1.69 inside the shoulder's 2r region (R-side triangulation only; owner-accepted chin, not a shoulder seam); eyes side 0.08 (owner-accepted brow/eye, kept).
