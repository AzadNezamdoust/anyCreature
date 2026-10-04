# bear c3: stage-1 cage on the part guide

Why c2 failed the new gates: torso 56 huge faces (density 0.29) against 220-face legs; 11-ring stacks on each
leg; library paws with toes (fans, triangles, poles in the wrist / hock bands); limb root loops below the joint
(t 0.4-0.5); head designed wider than the sheet (width taper -51%, RMS 18.6%).

Plan (c3): 12-sided torso tube of near-square quads; 8-sided limbs out of a 2 x 2 flank patch whose boundary is
the shoulder / hip loop (top edge above the joint, inner edge on the armpit line); muzzle out of the cranium's
face plane; sole closed with 4 quads. Rings sized by part_rings, slid onto the guide (fit_to_guide).
J: elbow / knee z 0.25, wrist / hock z 0.12, so their bands lie below the armpit and groin (the four patch
corners are the only poles of the limb root; they must stay out of the bands).

- **r1** 736 tris. Topology gates all pass first time (edge ratio torso 1.98, head 2.6, fore 2.57, hind 2.61).
  Critique: fails self-intersection (fore ring 1 reaches behind torso ring C), neck loops 1, neck width / head
  width +33.6%, head RMS 7.98%: the neck follows the guide, which is fat there (0.53 at y -0.52; the sheet's
  plan says 0.38), and the rump ring F took an over-the-end station (0.26 wide: a pinched rump).
  Fix: neck joint to y -0.43; three neck rings read off the sheet (shoulder wall 0.65 at y -0.447, neck 0.40 at
  -0.48, 0.385 at -0.53), not slid onto the guide; ring C back to y 0.165, D to 0.385; F explicit 0.50 wide.
  Result: better. 760 tris; intersection gone, proportions pass (max 7.9%), head RMS 3.4% (still over).
- **r2** Critique: neck counts 1 loop: the shoulder wall's radial edges tie rings N2 and K into one loop for the
  counter; head RMS 3.4% (neck depth at y -0.53 2.7 cm shallow, skull depth 2 cm deep).
  Fix: ring N1 moved to y -0.375 (a second loop inside the neck band, joined to N2 by lengthwise edges); K2
  depth 0.39, width 0.378; H0 depth x 0.95.
  Result: neck 2 loops; head RMS 3.19%; a new intersection under the throat (vertical ring K2 crosses the
  tilted skull ring H0). 760 tris. ROM 3.93% of area folds.
- **r3** (first blockout look) Critique: (1) the shoulder wall reads as a collar / hood round the head; (2) the
  head is a lofted cone, round sections; (3) the rump is a chopped flat plane with a point; (4) paws are thin
  flippers (the guide's paw is a slanted swept ellipse).
  Fix (form pass, by region): N2 a trapezoid section, widest low; K, K2 lean with the head (no crossing);
  cranium rings boxier (corners out, extents kept); ring F and the rump cap placed by hand off the side and
  plan outlines; the last paw ring and the sole read off the sheet (blocky toe front), not slid onto the guide.
  Result: worse on the gates (760 tris): head RMS 11.4% (the vertical neck rings are cut obliquely by the
  profile stations, which are square to the neck bone: the low wide wall lands in the neck's station); fore
  width taper -54% (the blocky paw is no longer 'hidden' at the last station and the guide's paw is 0.097 wide
  there against the sheet's 0.237); 4 sole poles in the wrist band; hind root loop t 0.32 (F3 too low).
- **r4** Fix: neck rings K, K2, N2 square to the neck bone; paw / toe joints pulled back inside the paw
  (y -0.265 / 0.53, z 0.04) so the last profile station cuts the paw where the guide still has its width; round
  heel (sole back corners forward 3.5 cm: out of the band); hip loop top edge higher (D3, E3 at 68 deg, F3 z 0.66).
  Result: mixed (760 tris). Poles and root loops pass again. Head RMS 7.55%: the wall sat behind its station
  (0.51 against 0.62) and N2's low edge crossed N1 (intersection, neck 1 loop). Fore width taper still -51%:
  the guide's paw is 0.109 wide at the last station whatever the joint (part_guide takes the tighter of front
  and plan runs, and the plan run goes through the claws); the sheet's front view says 0.232. KIT PROBLEM.
- **r5** Fix: N2 and K 1.5 cm forward along the neck bone (N2 on its station), N1 leaning with them, N2's top
  corners in (plan width at the neck 0.40), K2 depth 0.42. Waiver logged: META['intended']['fore profile']
  (paw width: guide 0.11 against the sheet's 0.23; the cage follows the sheet).
  Result: better. Head RMS 2.51% (pass). Still: neck 1 loop, neck width / head width +20.9%. 760 tris.
- **r6** Critique: N2's upper corner (x 0.20 at y -0.507) sits in the plan row where the neck is measured and
  its edge to N1 is diagonal enough to tie N1 into the wall's loop.
  Fix: that corner back and out (0.24, h 0.10: y -0.492); N1 to y -0.385, lean -0.30.
  Result: neck 2 loops (pass). Neck width / head width unchanged +20.9%: the plan row at y -0.505 still crosses
  the wall's upper edge (x 0.219), the head row measures 0.44.
- **r7** Fix: wall corner to (0.225, y -0.488), K 0.38 wide, cheeks at H0 x 1.04 (0.47, the sheet's 0.46),
  N1 lean -0.20, N2's chest edge 3 cm forward (no sliver band under the chest).
  Result: +14.6% (the mesh measures 0.41 / 0.46 = 0.89 at the exact rows; the mask row sits ~1 cm further back,
  on the wall's slope). Head RMS 2.88%. 760 tris.
- **r8** Fix: wall corner to y -0.475 and K 6 mm back (y -0.480): the neck is clear of the wall from y -0.49.
  Result: better: ALL GATES PASS, 760 tris. Neck / head width +2.1%, head RMS 2.76%. Blockout: reads as the
  sheet's bear; ROM 3.31% of area folds (paws and elbows in the 80-degree fold pose).
- **r9** (blockout look) Critique: a nape bump (K2's top 6 cm over the skull's), no stop between brow and
  muzzle, no tail root on the rump outline.
  Fix (head form): K2 1.5 cm down its section; brow verts of H2 up 1.6 cm and the muzzle root down 1 cm;
  rump cap's top seam vertex out to y 0.795 (the tail root; the tail itself is a stage-3 piece).
  Result: better. ALL GATES PASS (full run with the orbit), 760 tris, head RMS 2.62%, side IoU 0.962.
  ROM 3.2% of area. Not locked (orchestrator's call).

Waiver: `fore profile` (paw width at the last station; see r4-r5). Without it: width taper -50.6%, RMS 4.78%
(max 15.9% at that one station); the other five fore stations are within 1.5 cm.
Kit problems (not edited): (1) part_guide sizes the paw from the tighter of the front and plan runs, and the
plan run passes through the claws, so the guide's paw closes to 0.11 m where the sheet's front view has 0.23 m;
part_profiles then takes the guide as reference there. (2) blockout/5_profiles.jpg prints the fore gates as FAIL:
it does not apply META['intended'] as cage_gates does. (3) joint_loops counts a steep wall between two rings
(radial edges) as one loop. (4) the neck-width proportion row sits ~1 cm off the mesh row (raster).

## Rebuild on the new part base (after review_topology.md), r11-r22

Plan: torso 14-sided (one more lengthwise loop each side of the spine), limbs 8-sided rounded boxes (p >= 2.6) out
of the 2 x 2 flank patch, root loop top ~0.10 m higher (64 / 59 deg), neck rings off the guide's neck part, 10-sided
muzzle ending in a blunt nose block (two quads, no tip point), paw block wider than the wrist, wrist rings x 0.93.

- **r11** old program on the new base: 760 tris, head RMS 5.46% FAIL (old hand-made neck against the new guide).
- **r12** the rebuild. 888 tris. Critique: rings A, B, E pinched (the torso part is 0.19 wide between the leg
  masses), neck fat (fit pulled K, K2 onto the blended guide), N2 crosses N1. Fails: intersection, edge ratio 4.12,
  5.4% long faces, neck width +23%, head RMS 17%, hind RMS 4.7%.
- **r13** Fix: A, B, E start at the body's width; K, K2 unfitted at the plan's width; N1 leans with the neck.
  Result: better; topology gates pass. Still: A / B hump a narrow ridge (the fit follows the guide's ridge), head
  height +10.4%, head RMS 20% (plan width 0.65 beside the neck), hind RMS 4.7% (toe too tall and long in the oblique cut).
- **r14** Fix: back columns of A, B, E keep the drawn dome (not slid on); N1 wide low; H0 depth x 0.94; paws
  tapered (narrow heel, broad toes), hind toe shorter. Result: better: front IoU 0.945; head RMS 17%, hind 3.4%.
- **r15** Fix: two neck rings (K t 0.68, N2 t 0.33) evenly ~0.07 apart; N2 narrow on top, wide low (the shoulder
  fronts beside the neck: half the old wall's step); hind knee rings depth x 1.08. Result: all profile gates
  pass (head 2.75%, hind 2.37%); neck width / head width +31.6%.
- **r16-r18** Fix: N2's upper side in (x 0.90) and less lean; K's side vertex 2.4 cm back (the rendered diagonal
  K3 -> N2_4 crossed the plan's neck row). Result: ALL GATES PASS, 860 tris, neck +6.6%. ROM 4.68%.
- **r19** Critique (blockout): kite quads at the limb roots (root loop 0.46 tall, first limb ring flat).
  Fix: the first two limb rings follow the root loop (outer high, armpit low), flank column 118 -> 108 deg.
  Result: intersection at the hind root's back (F5), ROM 4.81%: no gain.
- **r20** Fix: F5 / F6 back and up. Result: ALL GATES PASS; ROM 4.88% (folds listed by BEAR_ROM=1: the faces
  between the elbow / knee ring pair all round, the wrist faces, the root's front / back quads).
- **r21** Fix tried: three rings at elbow and knee. Result: worse: medial slivers cross the belly face
  (8 intersecting pairs, a 64:1 face), elbow counted 1 loop. ROM 4.08%. Reverted.
- **r22** Fix: tight elbow / knee pair (0.295 tilted, 0.215). Result: ALL GATES PASS, 860 tris, ROM 4.3%.
  Not locked: ROM is over the 2% aim and the root quads in front of and behind each limb root are still kites.

Review fixes: 1 done within the new reference (wrist x 0.93, paw 0.25 broad at the toes: fore width taper 1.25 =
reference 1.25; the review's 1.9 was against the old guide). 2 done (wrist pair 0.145 / 0.09). 3 partly: poles up
~0.10 m, limb ring follows the root loop, but no second flank loop (it would make the limbs 10-sided) and kites remain.
4 done (two even neck rings, no sliver ring). 5 done (extra back loop, torso density 0.70; blunt nose block).
No waivers (META['intended'] is empty).
Kit problems (not edited): (1) the torso part's width at the leg stations is ~0.19 (a ridge between the leg masses),
so fit_to_guide pinches the hump and croup; (2) limb station t 0.71 has centre z 0.002; (3) the head profile's two
neck stations take the plan's run across the shoulder fronts (0.65-0.70) as "head width", which forces a wide ring one
step behind the head against the neck-width proportion; (4) the neck-width row is cut by rendered quad diagonals;
(5) ROM does not say where it folds (bear.py has a BEAR_ROM=1 diagnostic hook, and BEAR_DIAG=1 prints the ring budgets).
