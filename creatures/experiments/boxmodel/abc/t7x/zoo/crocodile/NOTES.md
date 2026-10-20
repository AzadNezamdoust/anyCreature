# crocodile (t7 hand box-model): NOTES

The technique follows wolf_base's t7r look, adapted to a long, low body. One spine loft of 6-vertex half rings runs from the tail tip to the snout and forms the whole body (19 sections: 5 tail, 7 trunk, neck, 6 head). Each sprawled leg is a 2-face region of the lower flank (spans C0 and R1). It is extruded OUT and then down. The leg section turns from a vertical hexagon (theta 0) to a horizontal one (theta 90), so the elbow and knee stand out from the body. The eye turrets are 1-face extrusions from the skull top (span H0). They take the place of the wolf's ears.

Stage 0: the sheet's side view and front view touched (the tail tip ran into the front figure), so refs.py could not split them. reference/sheet_3_gutter.png is the same sheet with the front figure moved 26 px right. refs.py traced that into blueprint.json (height 0.42 m, length 2.70 m). The section table was read per 7.5 cm column off the side and top masks.

## Stage 1
- r1: first fit. PASS, 696 tris, IoU side/front/top 0.883/0.744/0.779. Critique: az000 against the ref front. The trunk is a narrow ridge, while the ref is a broad mound. Diagnosis: the trunk W is 0.205, with the widest profile point high (0.25 T). Fix: W 0.215-0.23 over C0-R2, the widest point lowered to 0.12 T, and the leg roots moved out to match.
- r2: PASS, IoU 0.883/0.758/0.771. Critique: top overlay. The ref forelegs run from a root behind the foot, out and forward. The hind legs run from a root ahead of the foot, out and back. Ours stuck straight out. Diagnosis: the root spans sit at the feet. Fix: C0/C1 moved to -0.34/-0.55 and R1/R2 to 0.22/0.02, with the limb sections re-staggered.
- r3: PASS, IoU 0.869/0.758/0.782. The plan view now shows the ref's angled legs. Locked at r4 (696 tris).

## Stage 2
- r1: elbow, knee, neck-skull and tail-root rings; an eye socket (an inset in the turret's outer wall); a flat muzzle top; the upper-jaw ridge; a raised nostril pad. FAIL: slivers 2.8%.
- r2: T0 ring scaled 1.7x (a blunt tip). Still FAIL, 2.5%. The diagnosis was only partly right.
- r3: one ring each in the T0-T1 and T1-T2 spans (20 cm spans on 2-3 cm seam edges). PASS, 840 tris, min IoU vs s1 0.993.

## Stage 3
- r1: palette (olive, scute, cream, amber, pupil, claw, tooth). Pieces: lens eyes; scutes (3 rows a side on the trunk, 2 on the neck, a paired crest down the tail); 5 teeth a side; 4 fanned claws per foot. FAIL: z-fight 31 (the claw roots sat 4 mm over the sole plane; the lens sat on the socket floor).
- r2: claw roots lifted and the lens raised 3 mm. PASS, 2520 tris.
- r3: Critique az090: the ref has a cream lower-flank band; ours read green. Fix: a band rule for z < 0.14. It came out patchy, because the leg test (|x| > 0.215) caught the trunk's lower flank.
- r4 (run with s4 r1): the leg test changed to |x| > 0.24. The band now runs the length of the body.

## Stage 4
- r1: rig with 15 bones plus .R mirrors and a 4-bone tail. Clips: idle 48 (breathing, tail sway), move 24 (diagonal high walk with a trunk and tail S-bend), attack 32 (pull back, then a sideways head snap). All gates PASS. Warning: 2 tris (0.08%) clip in a pose.

Checks: orbit18_sheet.jpg (18 EEVEE views) reads from every angle, with no collapse. Separation on the rest mesh: tail to hind legs 32 cm, fore L-R 53 cm, hind L-R 54 cm, fore to hind 46 cm: PASS. side_by_side.jpg shows the four reference views next to the model.

Triangles: s1 696, s2 840, total 2520.
Weaknesses: the head is thinner and less bulbous than the ref's cartoon head (the front view reads small); the legs are stiff hexagonal sticks next to the ref's rounded limbs; the body is less round than the ref's front mound.

## Fix pass (zoo reviews, Fable + Opus merged)
Fix list (shape first): 1 snout +25 % and a narrower, flatter tip (both reviews); 2 legs sprawled out (reviews disagreed: Fable asked for longer legs, Opus for a lower sprawl; the concept sheet's front view shows short, wide-splayed legs, so the sprawl was taken); 3 scutes as 2 rows of large flat wedges a side, half as many, and a coarser tail crest (both reviews).
- Base change: the snout sections H2-H5 were stretched from H1 (tip y -1.345 -> -1.434, tip half width 0.042 -> 0.032), and the limb sections moved out (feet x 0.345 -> 0.405 fore, 0.355 -> 0.42 hind; elbow and knee lowered 2 cm). Stage 1 was re-locked (r5): PASS, 696 tris, IoU side/front/top 0.855/0.679/0.752 (the front drop is the wider sprawl).
- Stage 2-4 re-run (r2): all gates PASS, 1824 tris total. Warning: 3 tris (0.15 %) clip in a pose. Separation PASS (tail-hind 33 cm, fore L-R 54 cm, hind L-R 55 cm).
- Not fixed: the body is not lowered (the belly already sits 4.5 cm off the ground); the head stays thinner than the ref's.

## Fix pass 2 (round-2 reviews, Fable + Opus merged, concept sheet as referee)
Fix list (shape first): 1 trunk a wider, rounder mound (Opus: body thin and low; Fable: flat slab with a seam step); 2 legs 1.25x thicker and moved out with the trunk (Opus); 3 scutes 1.6x taller, 2 rows, bigger tail crest (both). Skipped: Fable's snout +25 % (the sheet's snout is eye-to-tip ~13 % of the length; ours already matches, a stretch moves away from the sheet).
- Base change: BODY profile rounded and widest low ((1, 0.12) -> (1, -0.05)); trunk W R1-C1 +15-20 %, top z +1-2 cm; leg sections x +0.035-0.04, radii x1.25; joints follow. Stage 1 re-locked (r6): PASS, 696 tris, IoU side/front/top 0.874/0.607/0.703 (front drop: the blueprint's front trace is narrower than the sheet's front mound).
- Stage 2-4 re-run (s4 r3): all gates PASS, glbcheck OK, 1824 tris total. Warning: 9 tris (0.62 %) clip in a pose. Separation PASS (tail-hind 33 cm, fore L-R 62 cm, hind L-R 62 cm, fore-hind 43 cm).
- checks_blender.py: views framed on the bbox seen from each view (floor half the long side), so the front and rear views are no longer tiny.
- Not fixed: from az0 the head is small in front of the mound (the sheet's cartoon head is bigger); the legs are still straight hexagon sticks.

## Poly pass 3 (owner: denser main mesh, ~2x tris, the increase in the body loft)
- Base change: half rings 6 -> 11 vertices (BODY re-fit to the sheet's front mound, TAIL, HEAD/MUZ rounder cheeks); 19 -> 35 loft stations, added where the silhouette curves (tail tip, hip, belly, shoulder-neck, snout) and re-fit to the side/top traces (trunk top and belly, head bottom raised to the trace, H0/H1 wider); legs 6 -> 12 sections of 10-gon rings with a shoulder/thigh bulge and wrist taper (root region 4 faces); ladder quad end caps (the 11-gon fans were needles). Eye turret on skull face v2-v3.
- Stage 1 re-locked twice: r7 (1908 tris) superseded at once for budget and tail-tip slivers; r8 locked: PASS, 2388 tris, IoU side/front/top 0.891/0.605/0.701 (r6: 0.874/0.607/0.703). Old lock kept in before3/.
- Stage 2 follows: elbow/knee rings after section ELB, neck-skull and tail-root rings, eye socket inset; the s2 r3 tail sliver rings are now base stations. s2 2564 tris, min IoU vs s1 0.997.
- Details unchanged (eye 48, scutes 576, teeth 40, claws 320; scute/teeth surface indices remapped).
- s4 r5: all gates PASS, glbcheck OK, slivers 0.6 %, z-fight 1, no clip warning. Separation PASS (tail-hind 33 cm, fore L-R 60 cm, hind L-R 60 cm, fore-hind 42 cm). Total 1824 -> 3548 tris (+1724, 100 % body). orbit18_sheet.jpg, side_by_side.jpg, before_after3.jpg rebuilt.

## Poly pass 3 review: REVERT (review_poly2x.md)
Verdict: the 2x pass made the scutes smaller and flatter, softened the snout plane and added side-pattern noise; before3 has bolder scutes and a crisper snout.
- Reverted: crocodile.py restored from before3/crocodile_fix2.py (6-vertex half rings, 19 stations, 6-section hexagon legs, old budgets); stage1_lock.json restored from before3/stage1_lock_r6.json (696 tris). The 2x-pass script, lock and renders are kept in pass3/.
- s4 r6: all gates PASS, s1 matches the r6 lock, 1824 tris total, slivers 0.3 %, z-fight 0. Warning: 9 tris (0.62 %) clip in a pose (same as fix pass 2). Separation PASS (tail-hind 33 cm, fore L-R 62 cm, hind L-R 62 cm, fore-hind 43 cm).
- The hero render is pixel-identical to before3. orbit18_sheet.jpg, side_by_side.jpg rebuilt; before_after4.jpg = before3 | 2x pass | now.

## Pass 9 (owner: keep the 2x density, fix the review's WORSE parts inside it)
Started from the poly pass 3 script (pass3/); the REVERT is undone. Earlier renders kept in before9/.
- Half rings stay 11 vertices, but every extra vertex now sits on a before3 hexagon plane (the midpoint of each old edge): co-planar faces on the trunk, tail, skull and muzzle, crisp ridges at the old corners. Fixes the soft snout plane and the rounded, rib-banded flanks.
- Index remap: JAW 7 -> 6, leg ROOT (4-8), scute rows jf 0.5 / 1.5 (bold wedges on the flat back plane, as before3), tail crest 0.7.
- Cream band rule only on the down-facing lower-flank plane (n.z < -0.02): no side-pattern patches.
- s2: the vertices beside the upper-jaw ridge follow it half way, so the jaw planes stay flat (no cream slits).
- Stage 1 re-locked r9: PASS, 2388 tris, IoU side/front/top 0.891/0.609/0.701. s4 r8: all gates PASS, glbcheck OK, z-fight 0. Warning: 2 tris (0.10 %) clip in a pose. Separation PASS (tail-hind 33 cm, fore L-R 60 cm, hind L-R 60 cm). Leg, neck and tail junctions checked: no holes or slits. Eye unchanged (lens r 14 mm).
- fix9.jpg = before9 | after hero, plus head and leg close-ups. orbit18_sheet.jpg, side_by_side.jpg rebuilt.
