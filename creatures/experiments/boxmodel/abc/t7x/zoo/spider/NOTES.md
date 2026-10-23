# giant spider (t7x zoo) — NOTES

t7's technique adapted to a spider: the spine loft of 6-vertex half rings runs abdomen tip -> big round abdomen (9 rings) -> pedicel waist -> cephalothorax (C0-C4) -> head (H0-H2). The eight legs are swept hexagon tubes, each grown from its own 2-face region (columns 2-3 of one cephalothorax span, C0..C3), straight in plan along a heading, knee high, foot on the ground. The chelicerae are 1-face extrusions from the head underside. Stage 0: reference/sheet.png traced with kit/refs.py (height 0.9 m). The sheet's side tile is a 3/4 view, so leg headings and reach come from the front and top views; the blueprint IoU is a loose guide.

## Stage 1
- r1: first fit. PASS, 1268 tris, IoU 0.602/0.588/0.508. Critique: az000/hero — the legs are pencils tapering to needles; the ref legs stay thick to the foot. Fix: leg half widths 0.056-0.062 to 0.026 at the foot, hexagon corners 0.55 -> 0.7.
- r2: FAIL, 14 self-intersecting pairs at the leg roots. Diagnosis: the first two sections (0.058 wide across) are wider than the 8 cm root span, so neighbouring roots cross. Fix: first sections 0.04 / 0.05.
- r3: PASS, IoU 0.600/0.609/0.484. Critique: az000 — the chelicerae are two thin sticks under a small head; the ref has two bulbous chelicerae under a broad face. Fix: fang sections wider (rx 0.054, ry 0.06), H0/H1 W 0.17/0.145.
- r4: better, PASS. Critique: top — the carapace is narrow next to the ref's round one. Fix: C rings W 0.16-0.23, T +0.02.
- r5: PASS, IoU 0.603/0.618/0.480; every view reads as the ref spider. Lock.
- r6 (LOCK): gates PASS, 636 verts, 1268 tris, edge sha256 25eacb7edc1171f0.

## Stage 2
- r1: joint rings on every leg (patella after the knee, metatarsus joint), pedicel ring, eye socket inset in the top-outer head front face (6 mm in), flat carapace top. PASS, 1496 tris, min IoU vs s1 1.0.
- r2 (run with stage 4 r4): Critique: az180 — the abdomen end is a big flat octagon. Fix: AT and A1 rings pushed back 7 / 4 cm. PASS, min IoU vs s1 0.975; the rear now domes.

## Stage 3
- r1: colours along existing loops: brown; orange leg bands on three leg spans (femur, after the patella ring, metatarsus); three orange abdomen stripes on spans A2-A3, A4-A5, A6-A7. Small black lens eyes (one in the socket, a smaller one above); a dark claw spike under each foot. PASS, 1640 tris.
- r2: brown a step lighter (#5a3d2e), claws their own dark colour (4 colours).

## Stage 4
- r1: rig ceph, abdomen, fang.L/R, 8 leg chains x 3 bones (local Z up: rot X lifts, rot Z swings); idle (abdomen breathing, leg ripple, fangs), move (alternating tetrapod gait), attack (rear up, front legs raised, fangs open, forward strike). FAIL: 3 colours; clip warning 15% of surface.
- r2: abdomen pitch and knee bends smaller. Clip unchanged (15%): wrong diagnosis. A probe shows the neighbouring femurs crossing at their shared roots in the gait.
- r3: femur bones pivot from the coxa section, not the root; swing 14 -> 9 deg. All gates PASS; clip 0.03% (eye lens only).
- r4: final with stage-2 r2. All gates PASS: hit/float/zfight 0, slivers 0, fold-overs 0, drift 0, lock OK.

Checks (checks.py): orbit18_sheet.jpg — every view reads, no collapse or hole. Fused-parts check on the rest mesh (vertices dominated by each leg's tibia/metatarsus bones), every neighbouring pair: L1-L2 9.3 cm, L2-L3 25.6, L3-L4 14.8, L4-L4R 62.7, L1-L1R 64.1 (mirrored the same): PASS. side_by_side.jpg: sheet views next to the model.

Triangles: stage 1 1268 · stage 2 1496 · total 1640.
Weaknesses: legs are straight in plan (the ref's arch slightly at the knee); single eye pair, not the ref's eye cluster; the abdomen stripes are thinner than the ref's.

## Fix pass (reviews: fable + opus)
Merged list, shape first: (1) chelicerae read as a dog snout (opus: shorten, tuck; fable: lengthen) — the sheet has short bulbous chelicerae under the face, so: shortened and tucked under the head front; (2) carapace +20 % (C/H rings), head moved forward 4.5 cm so it reads from az0; (3) abdomen -10 % and round cross-section (W = T); A1/A2 rings widened for a rounder rear dome; (4) leg headings 35/63/117/148 -> 24/58/122/150 (front forward, rear back; rear at 158 crossed the abdomen, r7 FAIL 12 self-intersecting pairs); knees raised 0.51 -> 0.63, above the carapace line.
- Base change: stage 1 re-locked (old lock kept in before/). r7 FAIL (rear leg through abdomen), r8 PASS, r9 lock, r10 re-lock with the rounder rear. Same topology: 636 verts, 1268 tris. Stage-2 log and lock assertion PASS; stage 4 all gates PASS (clip warning 0.03 %, eye lens only). Separation PASS (closest pair L3-L4 16.4 cm). Total 1640 tris.
- Not fixed: the az180 view still shows the abdomen end as a faceted disc with the A2-A3 stripe as a rim.

## Fix pass 2 (round-2 reviews: fable 7.5, opus 8)
Merged list, concept sheet as referee, shape first: (1) legs too straight (fable): knee sections z 0.61/0.63/0.59 -> 0.67/0.71/0.66, mid-tibia 0.42 -> 0.37, so the knees arch above the carapace like the sheet; (2) cephalothorax low and hidden (opus): waist, carapace and head raised 3 cm (CZ), leg roots, fangs and rig follow; no extra scale (pass 1 already +20 %); (3) abdomen flat at the rear / egg-shaped (both): rear rings spread back (A4-AT y +0.015..0.07), ABD profile (1, 0.3) -> (1, 0.15), stage-2 tip push 0.07/0.04 -> 0.03/0.02; abdomen stripes follow.
- Skipped: pedipalps (fable; the sheet shows only the two chelicerae), one band per leg segment (opus; the sheet has three bands per leg).
- Base change: stage 1 re-locked (old lock in before2/). r11 lock FAIL (expected), r12 PASS IoU 0.618/0.632/0.500, r13 lock. Same topology, 1268 tris. Stage 4 r7 all gates PASS, lock assertion PASS, clip warning 0.02 %. Separation PASS (closest L3-L4 16.7 cm). Total 1640 tris.
- Not fixed: the az180 view still shows the abdomen end as a faceted disc (an orange ring around it, as the sheet rear).

## Poly pass 3 (owner: denser main mesh, same box-model technique)
- Loft: half rings 6 -> 10 vertices (ABD/CEPH/HEAD re-profiled round); spine stations 18 -> 23: the abdomen is re-fitted as a superellipse with 11 stations denser at the rear dome and front neck, plus Wa (abdomen neck), Wb (carapace shoulder), Hm (carapace -> head). C0-C4 spacing kept (leg roots).
- Legs: hexagon -> octagon tubes from a 3-face root region (ring vertices 4-7); sections 9 -> 16, denser round the knee arch and joints. Fang root moved to ring vertices 7-8; eye face to vertices 2-3.
- Budgets raised: stage 1 1000-4000, total 2000-6000.
- Base change: stage 1 re-locked (old lock in before3/). r14 FAIL (leg 1 root through the new Hm ring, 4 pairs): first leg section further out, Hm narrower. r15 PASS, r16 (abdomen narrower, top IoU dropped, reverted), r17 lock: 1462 verts, 2920 tris, IoU 0.626/0.651/0.503 (was 0.618/0.632/0.500).
- Stage 2 follows: joint rings now 8-vertex loops at the 0.52 and 0.79 leg spans, pedicel ring on A10-Wa, eye socket on the new head face. Lock assertion PASS.
- Stage 3: leg bands painted by the nearest 3D leg centre line (the plan projection checkered the bands on the steep tibia).
- Stage 4 r9: all gates PASS, clip warning 0.01 %. Separation PASS (closest L1-L2 16.6 cm). Tris 1640 -> 3372 (body 1496 -> 3228, details 144 unchanged).

## Weakfix 2026-10-23 (night, backup before_weakfix/)
- s4 r10. Critique: rear view — the abdomen end reads as a flat disc (the 14 cm AT cap n-gon facing straight back). Fix (stage 2 vertex moves, lock kept): AT ring x/z scaled 0.48 about its centre and 2.2 cm further back, A1 0.92 / +1 cm, A2 0.97 / +3 mm: the dome turns in to a small apex. Build includes the detail agent's pending claw-cap edit (spider.py 02:50).
- Result: kit gates PASS (clip warn 17 tris), detail PASS (4 groups, tier 1), clips PASS after --fix-clips; junction FAIL leg1a knife 0.94 r..., eye side 0.22 (untouched geometry).
- r10 A/B not run: the EEVEE rear views (checks/h180) barely differ: the disc read comes from the bands seen end-on as concentric rings (the abdomen axis is level and points at the rear camera), not from the cap alone.
- s4 r11. Fix: the abdomen rings (AT..A10, Wa) tilt 12 deg tail-down about the pedicel (sheet side: a raised egg whose rear dips), so from behind the bands read as arcs.
- r11 result: FAIL s2 silhouette IoU vs stage 1: az135/az180/az225 0.891/0.886/0.891 (< 0.9); detail PASS, clips PASS.
- s4 r12. Fix: tilt 7 deg.
- r12 result: kit gates PASS (s2 IoU min 0.932), detail PASS, clips PASS; but checks/h180 still reads as a disc and the y-ruled stripe paint turns jagged/checkered on the tilted abdomen (side view). No A/B run: a visible regression -> REVERTED (spider.py = before_weakfix copy, which keeps the detail agent's claw-cap edit; stage4/ and checks/ restored).
- Diagnosis for next time: the disc is the band paint seen end-on (rings round a level y axis); the fix is to paint the bands by station along the tilted abdomen axis (or tilt + re-rule the bands together), plus a darker spinneret nub at the rear apex.
