# golem (t7 hand box-model, biped) - NOTES

The technique follows wolf_base, adapted to a biped. One vertical spine loft of 6-vertex horizontal half rings runs from the crotch to the crown (front seam to back seam). The legs are extruded from the 3-face region of the crotch-hip span and the arms from the 3-face side region of the upper-chest span. Both are 8-sided limb rings, and each section is an ellipse across its own axis. Stage 0: the sheet's top view had its head at the bottom, so it was turned 90 deg CW into reference/sheet.png (the untouched sheet is reference/sheet_original.png) and traced with kit/refs.py (height 2.0 m). The side view is partly turned, so widths come from the front and depth from the side, roughly.

## Stage 1
- r1: first fit. Gates PASS, 716 tris, IoU side/front/top 0.743/0.746/0.700. Critique (az000): the shoulder boulders slope off the shoulder shelf; the ref boulder tops sit at z 1.97, above the head. Diagnosis: the first arm section is tilted and low. Fix: the first arm ring is vertical, centre z 1.72.
- r2: Result: barely changed (0.760/0.749/0.697). The boulder still reads as a sloped fin. Diagnosis: a single big ring straight off the torso gives one flat wall. Fix: a small root ring, then the big boulder ring, then a ring turning down.
- r3: Result: the boulder is now a mass, but the arms read as vertical pillars, and the head and torso are narrow against the front view. Fix: the arm path re-fitted to the front outline (upper arm out to x 0.79, forearm 0.89 with r 0.25, fist 0.87 with r 0.23); head W 0.18; chest W 0.54 and deeper back; legs set wider (feet to x 0.64).
- r4: Result: better (0.772/0.762/0.689). Critique: a vertex sits on the boulder top, which makes a peak. Fix: the limb ring angles are snapped so that an edge sits on top, front and sides.
- r5 (LOCK): 376 verts, 748 tris, edge sha256 256c9500dbc0d960. IoU 0.772/0.760/0.690. The front outline's leg gap is traced filled, and the turned side view caps the side IoU.

## Stage 2
- r1: loop cuts at the elbow, wrist, knee, ankle, waist and neck; an eye-socket inset under the brow, pushed in 15 mm; the brow ridge moved 25 mm forward. Gates PASS, 932 tris, min IoU vs s1 0.998.

## Stage 3
- r1: palette of stone, dark stone (legs/fists), pale belly plate, moss (boulder tops and outer upper arm) and glow. Pieces: glowing lens eyes; a continuous glowing chest-crack strip (mirrored into a V); 4 moss clumps per side; stone plates (knee caps, forearm guard, 3 knuckles, 3 toes). Gate FAIL: z-fight on 6 crack faces (the strip stood only 6 mm proud).
- r2: Fix: crack top 14 mm proud. Result: gates PASS, 1420 tris. Critique (hero colour): the whole golem reads near black, and moss covers the boulders' outer sides.
- r3: Fix: palette lifted one step; moss only on faces with n.z > 0.45 above z 1.66; the arm streak dropped. Result: gates PASS.

## Stage 4
- r1: rig of 12 bones plus .R mirrors (hips, spine, chest, neck, head, shoulder, upperarm, forearm, hand, thigh, shin, foot). Clips: idle 48 (breathing, head turn), move 33 (walk: thigh swing, shin flex on the passing leg, counter arm swing, hip bob), attack 36 (two-arm overhead smash with a chest lunge). Gate FAIL: drift on 2 moss shells.
- r2: Tried each moss shell rigid at its mean weights. Worse: 8 drifting shells. Reverted.
- r3: The outer-arm clump was dropped. Still 2 drifting shells. r4: the clumps were made smaller and the attack raise cut from 100 to 75 deg. Still 2. r5: the outer clump was moved inward. Still 2. r6: shell-rigid weights on moss only: 4. Diagnosis: the boulder skin stretches between the shoulder and upperarm bones in every arm swing, so anything seated there slides.
- r7: Fix: the moss clumps were removed; moss stays as the painted boulder-top zone. Result: all gates PASS (clip warning only, 16 triangles = 0.01% of the surface). 1260 tris total, 5 colours.

18-view check (orbit18_sheet.jpg): every view reads; no collapse or hole. Fused-parts check on the rest mesh (separation.json): leg L to leg R 28.6 cm, arm to torso 13.8 cm, arm to legs 11.2 cm. PASS.

Weaknesses: moss is a flat colour cap, not clumps; the chest crack reads as an outline strip; the boulders are still angular wedges next to the ref's round stones; the body has no stone-slab seams; the side IoU is limited by the turned side view.

## Fix pass (merged review fixes)
Reviews disagreed on the head: one asked 1.4x and lower boulders, the other +15 % and a small raise. The concept sheet keeps a small head under high boulders, so the +15 % / raise path was taken and the boulders were kept.
- Stage 1 re-locked (base change): head sections +15 % and raised 6 cm so the eyes clear the pec line; foot sections lengthened forward into a flat slab (ry 0.32, centre y -0.10); fist end widened (0.20/0.21) so the fist is a blunt block. Gates PASS, 748 tris, IoU 0.760/0.759/0.700. Old lock kept in before/.
- Stage 2: the eye-socket inset dropped (it read as a visor mask); brow ridge kept. Gates PASS, 916 tris.
- Stage 3: chest crack strip dropped (a liner/decal); two plain small lens eyes on flat face planes; moss extended down the outer upper arm as a second painted patch; knuckle blocks enlarged (knuckle plane); 3 square dark stone toes per foot replace the light nubs; pec and belly stone slabs added. r10 still showed the crack (object built but unlisted) and the arm moss as a band; r11 removed the crack code and joined the arm patch to the boulder cap. Gates PASS, 1204 tris.
- Stage 4: same rig and clips. Gates PASS (clip warning only, 20 tris = 0.01 %). Separation PASS (legs 28.6 cm, arm-torso 13.8 cm, arm-legs 10.6 cm).
Not fixed: boulders still angular wedges; the belly slab is mostly hidden under the chest overhang; moss stays a flat colour zone.

## Fix pass 2 (merged round-2 reviews)
Reviews disagreed on the head (one: sink it, no neck; other: 1.4x and raise). The concept sheet has a small head sunk between the boulders, so the head was sunk and not scaled.
- Stage 1 re-locked (base change; old lock kept in before2/lock): neck and head sections 5 cm lower, shoulder shelf W 0.40 -> 0.44; torso depth +15..25 % (P2-P6 front/back); upper arm and elbow rings x1.2, forearm x1.15. Gates PASS, 748 tris, IoU 0.765/0.781/0.783 (was 0.760/0.759/0.700).
- Stage 3: plates painted body grey (shape only); three knuckle chips merged into one knuckle block; belly plate restored, upper and lower back plates added (sheet rear). First run FAIL on total tris 1132 < 1200; the back plates fixed it.
- Stage 4: rig joints follow the lower head. Gates PASS (clip warning only, 28 tris = 0.69 %). Separation PASS (legs 28.6 cm, arm-torso 12.3 cm, arm-legs 10.6 cm).
- side_by_side.jpg now shows reference views against the model (checks.py).
Not fixed: boulders still angular wedges; moss a flat colour zone; head still reads small (sheet-true).

## Density pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- Body loft: half rings 6 -> 10 vertices (rounded super-ellipse torso; head with one flat front plane for the lens eye and a tapering skull back). Spine stations 12 -> 18 (new P1a hip-waist, P2a belly swell, P3a chest overhang, P4a pec/back hump, H0a cheek, H1a brow-skull); torso W re-read from the front trace (z < 1.15), depths blended toward the side trace, head W toward the trace (0.235).
- Limbs: 12-sided rings (was 8) grown from 5 of 9 side faces; arm 9 -> 13 sections, leg 7 -> 11. Boulder rebuilt as a dome to the front trace (top over the shoulder at x 0.44 z 1.95, crown, outer shoulder, turn into the upper arm); elbow and forearm rings re-read from the trace. limb() now walks the region's boundary loop instead of an angle sort (a first trial failed self-intersection: the wide region mis-ordered by angle).
- Stage 1 re-locked (r24; old lock in before3/lock): 1796 tris, edge sha256 27b3a4323d5b148e, IoU side/front/top 0.786/0.812/0.803 (was 0.765/0.781/0.783). Budgets: stage1_tris 1200-3200, total 2000-5000.
- Stage 2 follows: elbow, wrist, knee, ankle, waist and neck loops on the new rings; eye on the H0a-H1 front plane; brow kept. 2060 tris, min IoU vs s1 0.999.
- Stage 3/4: details unchanged (eye lens, plates, toes re-cast onto the new surface). All gates PASS (clip warning only, 4 tris). Separation PASS (legs 27.2 cm, arm-torso 12.5 cm, arm-legs 10.2 cm). Total 2348 tris (was 1204): body 916 -> 2060, details 288 -> 288; 100 % of the increase in the body loft. stage4, orbit18_sheet.jpg, side_by_side.jpg, before_after3.jpg re-rendered.

## Revert of density pass 3 (review_poly2x: REVERT)
- Review: rock planes rounded off, blocks banded into rings, head bulb-like, shoulder moss lumpy; no part clearly better.
- golem.py restored to the before3 version (6-vertex half rings, 12 spine stations, 8-sided limb rings, arm 9 / leg 7 sections; budgets stage1 400-2200, total 1200-4500). Stage 1 lock restored from before3/lock. 2x-pass script, lock and renders kept in pass3/.
- Rebuilt stages 1-4: all gates PASS (s1 matches lock; posed fold-overs 0.17 %). Separation PASS (legs 28.6 cm, arm-torso 12.3 cm, arm-legs 10.6 cm). 1204 tris. Hero render pixel-identical to before3.
- stage4, orbit18_sheet.jpg, side_by_side.jpg re-rendered; before_after4.jpg = before3 | 2x pass | now.

## Fix pass 9 (owner: keep the 2x density, fix the review's WORSE parts within it)
- Restarted from the pass3 2x script (10-vertex half rings, 18 spine stations, 12-sided limb rings, arm 13 / leg 10 sections). Previous state kept in before9/.
- Rib bands / rounded planes: every half-ring vertex now sits on the before3 6-vertex flat outline (extra vertices split the front, side and back planes), so faces stay co-planar and ridges crisp. The 12 before3 stations are restored; the 6 extra stations are exact interpolations of their neighbours (no bands, no lumps), except P3a, pulled in 4 % under the chest so the overhang reads as one ridge at P4.
- Limbs: the 12-sided ring keeps the before3 octagon (8 corners, 4 extra vertices on the side midpoints), so each limb side is one flat plane. Before3 sections restored with interpolated extras; the two boulder extras swelled 5 % / 3 % for a faceted stone instead of a fin; shoulder moss now sits on clean planes.
- Head bulb: before3 head widths restored (extra stations interpolated); eye back on the H0-H1 front plane; brow ridge moves the whole front plane; lens r 0.022 -> 0.027 (brow overhang).
- Stage 1 re-locked (r31; old lock in before9/lock): 1748 tris, edge sha256 280e2315811c7a8d, IoU side/front/top 0.775/0.801/0.779. Stage 2 cuts re-indexed to the new sections.
- All gates PASS (clip warning only, 6 tris = 0.69 %), lock assert PASS. Separation PASS (legs 26.0 cm, arm-torso 10.2 cm, arm-legs 8.5 cm). Junctions checked in the 18-view orbit: no holes, specks or slits. Total 2300 tris.
- stage4, orbit18_sheet.jpg, side_by_side.jpg re-rendered; fix9.jpg = before9 | after (hero, head/eye close-up, wire).

## Detail pass (2026-10-23 night, tier 3: 5 -> 12+ groups; backup before_detail/)
- r13 (S4): plates split into named pieces (kneecap, bracer, knuckle, plate_chest/_belly/_back/_lowback) + new
  plate_thigh, brow blocks, rock lumps; stone toes taller. Kit: z-fight 4 (toes dip below the ground); detail FAIL:
  all 6 toes 'sticks' (L 172 mm: the taller toe top runs back over the foot top, as troll r33). Junction (shoulder
  knife 5.2 r, thigh strip 1.7 r) and eye side 0.19 FAILs come from the unchanged body (not run on the champion).
  Critique (az000): brow blocks meet at the seam as a dark slit; rock lumps too small to read.
- r14 Fix: toes 56 mm tall centred at z 0.032 (under the foot top, off the ground); one brow block per eye clear of
  the seam; rock lumps 7-9 cm.
- r14 Result: kit gates OK (z-fight fixed), detail FAIL only the middle toe each foot (L/t 7.5; crop dcrop_0: it
  stands proud of the sloped foot front). Fix r15: toes seated deeper (middle 3 cm, outer 1.2 cm).
- r14 A/B (Opus, both orders): champion won BOTH: the shoulder rock nubs read as fussy cubes poking out of the
  moss boulders, the thigh slabs as stuck-on tiles. -> r15 also drops rock lumps and the thigh plate (keeps the named
  plates, brow blocks and the toe fix).
- r15 Result: kit OK; detail FAIL only the middle toe (unchanged L 156 mm, t 20.9 mm, tip off to the side: the hit
  normal of the sloped foot front tilts the block sideways). Fix r16: toe blocks square to the front (n = -Y), 2 cm in.
- r15 A/B (Opus, both orders): variant won BOTH (brow slab over the eyes, blockier toes) -> adopt once r16 passes the detail gate.
- r16 Result: kit gates OK, detail PASS 12 groups (was 5 FAIL; toe sticks fixed). Junction shoulder knife 5.2 r /
  thigh strip 1.7 r and eye side 0.19 come from the unchanged body (not part of this pass). ADOPT (r15 judge won
  both orders; r16 only squares the toe blocks). Residuals: toe blocks small; forearm bracer slab sticks out (both
  judges); the sheet's chest crack and boulder shoulders not done.
