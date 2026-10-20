# raven_wyvern (t7 hand box-model) — NOTES

Technique: wolf_base's t7 look. One spine loft of 6-vertex half rings from the tail-fan tip to the beak tip; the hind legs are 2-face extrusions from the lower flank (span R0-M0). Wing-arms, feathers, toes and eyes are stage-3 pieces. Stage 0: refs.py traced reference/sheet.png (height 1.2 m, length 2.19 m). The sheet reads as a raven; wyvern proportions were put in on purpose: head 0.10 m further forward and 0.15 m higher (longer neck, three neck sections), longer, deeper beak, a flat tail fan that widens to its end.

## Stage 1
- r1: first fit. PASS, 496 tris, IoU side/front/top 0.66/0.675/0.705 (the traced outline includes the wings and the sheet's shorter neck). Critique top: the tail tapers to a stick; the ref tail is a fan that widens toward its end.
- r2 (LOCK): tail widths T0 0.11, T1 0.185 (fan). PASS, locked 250 verts / 496 tris, IoU 0.66/0.677/0.70.

## Stage 2 (run with stage 4)
Knee and hock rings, three neck loops, three tail loops, eye socket inset, brow corner, flat beak sides and culmen planes.

## Stage 3 / 4
- s4 r1: pieces (lens eyes, folded wing-arm slabs with primaries and a wrist claw, tail and nape/throat feathers, 4 toes with talons), rig (hips, spine, 3 neck, head, 4 tail, upperarm/forearm/hand, thigh/shin/tarsus/toe + .R) and idle/move (biped walk)/attack (wing mantle, neck coil and strike). FAIL: 1,348 tris under budget, 2 floating feathers, 16 z-fighting toe faces; colour too dark to read the wing.
- s4 r2: feathers rooted on the nearest body point, toes lifted 1.4 cm, denser wing loft, covert row and 3 more primaries, lighter palette. FAIL: 4 floating coverts (buried inside the wing slab).
- s4 r3/r4: coverts straddle the wing's outer face, thicker. PASS.
- s4 r5: sheen toned down (was saturated blue under EEVEE). All gates PASS, glbcheck OK; warning only: 7 eye triangles clip in a pose.

Checks: orbit18_sheet.jpg (18 views): every view reads, no collapse. Separation (rest mesh): legs L-R 0.164 m, tail vs legs 0.498 m, free wing vs body 0.061 m: PASS. side_by_side.jpg built.

Triangles: s1 496, total 1,660.
Weaknesses: wings sit narrower than the ref's in front view; tail sheen bands read striped rather than iridescent; the body is plainer than the ref's shaggy plumage.

## Fix pass (reviews fable + opus merged)
Fix list, shape first: (1) neck too long / head small / chest thin (opus) -> neck shortened ~30 %, head lowered 0.12 m and widened 20 % (fable), chest deepened (C0 belly 0.47->0.40) and widened (0.20->0.23), throat hackles re-aimed forward-down; (2) wings narrow slabs with a gap and edge fringe (both) -> slab folded in 0.03 m against the flank (gap 0.061->0.028 m, still separate), 7 primaries + 5 coverts replaced by 3 large tip primaries + 3 broad coverts; (3) tail striped plank (both) -> thicker wedge fan widening to 0.22 m, one dark colour, 3 broad tip feathers. Base change: stage 1 re-locked (r4, 496 tris, IoU 0.713/0.747/0.702, was 0.66/0.677/0.70); old lock kept in before/.
- s1 r3 FAIL self-intersection (belly lowered into thigh) -> belly kept, r4 LOCK PASS.
- s4 r6-r8 FAIL floating shells (buried throat hackles, wrist claw inside slab, coverts off the face) -> re-seated. r9 PASS; warning: 24 tris clip in a pose.
Checks: 18 views read, separation PASS (legs 0.164, tail/legs 0.496, wing/body 0.028 m). Total 1,532 tris. before_after.jpg built.
Not fixed: body still plainer than the ref's shaggy plumage.

## Fix pass 2 (review2 fable + opus merged, concept sheet as referee)
Fix list, shape first: (1) head narrow (fable) -> H1/H2 widened ~15 % (0.108/0.095 -> 0.124/0.109); H0 kept at 0.10 (wider H0 made the N2-H0 neck loop self-intersect, s4 r10/r11 FAIL); (2) chest narrows to the legs (fable) -> CHEST profile (0.9,-0.3) -> (0.95,-0.4), C0 W 0.23 -> 0.25; (3) front view narrower than sheet -> folded wings moved out 0.02-0.05 m (r12 FAIL wing pierced the wider chest twice, r13 moved out further); (4) top-view tail fan narrower than sheet -> T1-T3 W 0.22/0.19/0.16 -> 0.26/0.22/0.17.
Skipped: tail shortening (fable) - model length/height 1.82 matches the sheet's 1.83; wyvern membrane wings, horns, tail spade (opus) - the concept sheet is a plain raven.
Base change: stage 1 re-locked (r7, 496 tris, IoU 0.713/0.755/0.695); old lock in before2/.
s4 r13 PASS (warning: 12 tris clip in a pose). Separation PASS (legs 0.164, tail/legs 0.496, wing/body 0.028 m). 18 views all colour and read. Total 1,532 tris. before_after2.jpg built.
Not fixed: body plainer than the sheet's shaggy plumage.

## Poly pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
Before renders, the pass-2 script and the r7 lock kept in before3/.
- Base change, stage 1 re-locked: half rings 6 -> 11 vertices (old vertices kept, each new one on the Catmull-Rom curve between them: rounder sections); spine loft 19 -> 31 stations (tail fan T15/T25/T35, tail root RT, back RR, flank RM, breast MC/MC2, crop CN, neck NN0/NN1/NN2, nape NH, crown HH, beak root HB, culmen B12). Back tops re-read off the traced side outline (R1 0.50 -> 0.47, T4/C0/M0 lowered to the sheet). Legs: 4x2-face flank root, 12-sided rings, 7 sections (upper-thigh bulk, shank added).
- s1 r8 script error (extrude freed the root interior verts); r9-r11 FAIL leg self-intersection (twisted ring order, interior cap verts, upper thigh into the belly) -> boundary walked in loop order, interior verts halfway to their neighbours, upper thigh lowered. r13 locked 1572 tris, then r15 RE-LOCK with 4 more stations: 1732 tris, 868 verts, edge sha256 0741eff919ca9e2f, IoU side/front/top 0.733/0.769/0.701 (r7: 0.713/0.755/0.695).
- Stage 2 on the new topology: knee and tarsus rings, neck loops CN-N0, N0-NN0, NH-H0, tail loops T4-RT, T35-T4, T2-T3, eye socket on the H1-H2 side quad (inset 0.3), brow, flat beak sides and culmen; 2204 tris, IoU vs s1 >= 0.998.
- Details unchanged (eye, wing, feathers, toes 852 tris; feathers and eye re-rooted on the new surface by nearest point). s4 r16: all gates PASS, glbcheck OK, warning: 12 tris clip in a pose. Separation PASS (legs 0.164, tail/legs 0.484, wing/body 0.028 m). 18 views read.
Triangles 1,532 -> 3,056: body 680 -> 2,204, details 852 -> 852 (the whole increase in the body loft). before_after3.jpg, side_by_side.jpg, orbit18_sheet.jpg rebuilt.
