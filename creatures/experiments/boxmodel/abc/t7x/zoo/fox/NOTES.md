# fox (t7x zoo) — NOTES

Technique: the base wolf's t7r loft (one spine loft of 6-vertex half rings, tail tip -> nose; legs extruded from 2-face flank regions; ears 1-face extrusions), stage 2 joint rings + eye socket, stage 3 lens eyes, clumps, claws, colour by region rule, stage 4 rig + idle/move/attack. Built at the wolf's scale (1.1 m to the ear tips) so the wolf's piece sizes carry over.

Stage 0: reference/ from sheet_1.png via kit/refs.py (height 1.1, length 1.688). The plan trace cut a slit along the axis from mid-body to the nose (the dark ears split the head); the top head outline was re-drawn by hand from top.png.

## Stage 1
- r1: first fit of the section table read off side.png. Gates PASS, 692 tris, IoU side/front/top 0.734/0.828/0.735. Critique: az000/top — body a narrow plank. Diagnosis: W 0.12-0.15 against the ref's 0.19 half-width at the chest. Fix: W up (C0/C1 0.185, C2 0.17, M0 0.165, W0 0.15, R1 0.155).
- r2: Result: better, IoU 0.734/0.860/0.792. Critique: az090 overlay — empty wedge between the ear back and the neck line. Diagnosis: C1/C2/N0 tops 3-5 cm low and forward. Fix: neck top line raised to the ref's (C1 -0.36/0.89, C2 -0.40/0.95, N0 -0.45/1.0).
- r3: Result: better, IoU 0.746/0.870/0.789. Critique: az090 — hind leg stands between the ref's staggered pair. Diagnosis: hock/paw at the mean position. Fix: bias toward the rear ref leg (hock y 0.45, paw 0.415).
- r4: Result: better, side 0.759. Critique: top/az180 — tail thin next to the ref brush. Diagnosis: tail W 0.07-0.125. Fix: W 0.085-0.15.
- r5 (LOCK): gates PASS, 348 verts, 692 tris, edge sha256 08616e9be162f49c. IoU 0.759/0.870/0.792 (side pays for the staggered legs; front/top for cheek ruff and brush fluff, stage-3 pieces).

## Stage 2
The wolf's pass on the fox sections: elbow, stifle and neck rings, eye socket inset, brow/cheek moves, flat muzzle planes, slanted nose pad; tail tip ring widened x1.8. Gates PASS (run inside the stage-3 rounds), min IoU vs s1 > 0.9.

## Stage 3
- r1: Plan: 5 colours (orange coat, cream chin/cheek/throat/belly/tail tip, black-brown socks and ear backs, black nose, amber eye); small lens eye (r 1.6 cm, pupil by distance from the lens axis); cream cheek ruff + bib clumps, tail brush clumps, 3 claws per paw. Result: gates PASS, 1264 tris. Critique: az090 — tail tip barely cream, brush sparse. Diagnosis: cream rule starts at y 0.72; 9 brush clumps. Fix: cream from y 0.66; 5 more brush clumps; lower-flank cream underline.
- r2: Result: better, gates PASS, 1404 tris. Critique: hero — cream band on the foreleg above the sock. Diagnosis: throat rule had no lower z bound. Fix: throat z > 0.42; 2 more bib clumps.

## Stage 4
- r1: wolf rig on the fox skeleton (16 bones + mirrors), skin + body binds, idle/move/attack. All gates PASS: fold-overs 0, drift 0, lock OK, slivers under 2%; clip warning only (3.9% of surface, brush vs hind legs in the trot). 1460 tris total.
- 18-view orbit (orbit18_sheet.jpg): every view reads. Separation on the rest mesh: tail to hind legs 13.2 cm, fore L-R 13.0 cm, hind L-R 11.0 cm: PASS, nothing fused.

Weaknesses: one symmetric hind pair against the ref's staggered pair; cheek ruff reads as spiky clumps rather than the ref's smooth white cheeks; total tris (1460) at the low end of the range.

## Fix pass (reviews Fable + Opus)
- Merged list (shape first): tail too thin mid-length with a frayed tip; chest bib of many spiky shards jagging the rear/belly line; hind upper leg thin. Opus "legs 8-10% long" not applied: the concept sheet has the same leg length.
- Base change: tail W T1 0.12->0.15, T2 0.15->0.20, T3 0.13->0.17, T4 0.085->0.10; hind knee ring 0.06/0.10->0.072/0.115, gaskin 0.044/0.062->0.053/0.072. Stage 1 re-locked (r6): gates PASS, 692 tris, edge sha256 f2bc45b6ad5a8f89, IoU 0.765/0.847/0.775 (front/top lower: the wider brush sits outside the trace).
- Stage 3: bib 7 clumps -> 3 broad planes high on the throat; brush 14 slivers -> 7 broad clumps.
- Stage 4 r2: all gates PASS, 1152 tris (was 1460); clip warning 5.8% (brush vs hind legs in the trot). Separation PASS (tail-hind 14.7 cm, fore 13.0, hind 11.0). orbit18, side_by_side, before_after re-rendered.

## Fix pass 2 (reviews round 2, Fable + Opus; sheet as referee)
- Merged list: chest narrow at az0 (Opus) -> C0/C1 W 0.185->0.20, C2 0.17->0.18; muzzle short (Fable) -> H3 y -0.78, H4 nose -0.845 (sheet nose); shaggy bib (Opus) -> 2 flat planes laid down the throat; frayed brush -> 4 broad plates laid along the tail axis.
- Skipped: Fable "tail level ~20 deg" and Opus "tail 30% longer, arcs up": the sheet tail drops ~45 deg to a tip at y 0.84, which the loft already matches. Belly cream band (colour, lowest) not done.
- Stage 1 re-locked (r7): gates PASS, 692 tris, edge sha256 2453e3971ef6988d, IoU 0.765/0.851/0.784.
- Stage 4 r3: all gates PASS, 1040 tris; clip warning 5.6% (brush vs hind legs in trot). Separation PASS (tail-hind 14.7 cm, fore 13.0, hind 11.0). orbit18, side_by_side, before_after2 re-rendered.

## Density pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- Body loft: half rings 6 -> 10 vertices (a Catmull-Rom rounding vertex between each pair from the top seam to the lower flank; the belly plane stays one flat face). Spine stations 20 -> 32: new T0x-T4x (tail curve), R0x (hip), R2x/W0x (loin, belly), M0x (behind the shoulder), C1x/C2x (chest-neck), H2x (muzzle); tops/bottoms Catmull-Rom between neighbours then snapped to the side trace, W interpolated (tail W kept above the trace per the earlier review).
- Legs: decagon rings grown from the 4-face flank region; fore 5 -> 7 stations (forearm taper), hind 6 -> 8 (gaskin -> hock -> cannon). Ears from 2 faces, base moved 1 cm up/out (cleared a self-intersection with the neck).
- Stage 2 follows: elbow/stifle loops on the decagon rings, neck loop unchanged, eye socket on the H0b-H1 quad above the cheek line, muzzle flats and nose pad on the 10-vertex rings. Details (eye, bib, brush, claws) unchanged; surf() walks the inserted stations. Budgets: stage1_tris 400-3000.
- Stage 1 re-locked (r8): gates PASS, 1796 tris, edge sha256 f78c8bb003db681b, IoU 0.775/0.840/0.775 (was 0.765/0.851/0.784).
- Stage 4 r4: all gates PASS, 2192 tris (was 1040): body 1928 (was 776), details 264 (unchanged); 100% of the increase in the body loft. Clip warning 4.7%. Separation PASS (tail-hind 4.6 cm, fore 13.4, hind 11.4). stage4, orbit18, side_by_side, before_after3 re-rendered.

## Poly-2x review apply (verdict MIX: keep head, ruff, tail; restore before3 torso loft)
- Torso R0..C2: before3 stations back (R0x, R2x, W0x, M0x, C1x removed); rings stay 10 vertices for the bridge, but the inserted vertices are straight midpoints of the before3 6-vertex sections (flat(), no Catmull-Rom bulge), so the shoulder/hip planes are flat again. Head, neck (C2x, N0), tail, legs, details unchanged. Lesson: density only where the outline bends.
- Stage 1 re-locked (r9): gates PASS, 1616 tris (was 1796), edge sha256 466d688c27e2678b, IoU 0.772/0.835/0.776.
- Stage 4 r5: all gates PASS, 2012 tris (was 2192); clip warning 4.7%. Separation PASS (tail-hind 4.6 cm, fore 13.4, hind 11.4). 2x-pass renders kept in pass3/; stage4, orbit18, side_by_side, before_after4 (before3 | 2x pass | now) re-rendered.

## Owner pass 5 (owner: fox too bad relative to the others)
- Diagnosis (shape and face first): (1) eye a 1.6 cm pinhole sunk under a heavy brow, no readable round lens; (2) ears small and thin next to the sheet's big triangular ears; (3) bib = floating cream slabs that jag the throat outline; (4) tail brush = loose plates, a frayed club, not one bushy mass with a clean cream tip; (5) colour blocking broken by those pieces (cream patches float off the planes).
- Base change: ears 3 stations (base 0.068/0.05, mid, tip z 1.15; eartip joint follows); tail W T1 0.15->0.19, T1x 0.184->0.22, T2 0.20->0.225, T2x 0.193->0.205. Stage 1 re-locked (r10): gates PASS, 1640 tris, edge sha256 999752f799f34ea1, IoU 0.770/0.802/0.761.
- Stage 2: eye socket inset 0.36->0.26, sink 0.012->0.008, brow overhang halved.
- Stage 3: lens eye r 1.6->2.6 cm, set proud of the socket, pupil r 1.0 cm; bib and brush pieces removed (cream chest and tail tip are flat colour on the body planes, tail cream from y 0.62); ear rule widened to the bigger ears.
- Stage 4 r6: all gates PASS, 1868 tris; clip warning 5.8%. Separation PASS (tail-hind 4.9 cm, fore 13.4, hind 11.4), no fused parts. stage4, orbit18, side_by_side, before_after5 re-rendered (before5/ holds the old renders).

## Density pass 9 (owner: keep the 2x mesh, fix its problems inside it)
- The poly-2x apply had removed the torso stations (a density revert). Restored R0x, R2x, W0x, M0x, C1x, but each is a straight in-between of its two neighbours (centre, tilt, T, B, W lerped; flat 10-vertex sections), so every split face stays co-planar: the shoulder (C0) and hip (R1) breaks stay crisp, no rib bands or lumps. Head, pass-5 eye (2.6 cm lens), ears, tail, legs, colour unchanged.
- Junctions checked in the orbit and close-ups: legs, ears, neck, tail meet clean; no holes, specks or slits.
- Stage 1 re-locked (r11): gates PASS, 1820 tris (2x level: r8 was 1796), edge sha256 5e21cb6412396b9d, IoU 0.770/0.802/0.761.
- Stage 4 r7: all gates PASS, 2048 tris; clip warning 5.8%. Separation PASS (tail-hind 4.9 cm, fore 13.4, hind 11.4), no fused parts. before9/ holds the old renders; stage4, orbit18, side_by_side, fix9 (before9 | after, hero + torso wire close-ups) re-rendered.
