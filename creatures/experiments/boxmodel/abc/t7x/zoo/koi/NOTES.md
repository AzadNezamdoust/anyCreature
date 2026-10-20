# koi (t7x zoo) — NOTES

t7's technique adapted to a fish: the spine loft of 6-vertex half rings (caudal peduncle -> snout, 15 rings) is the whole body; every fin is a face region extruded off it. Dorsal, anal and both caudal lobes grow from seam faces (the wall left on x = 0 is removed, the mirror closes the fin); the caudal plate grows from the tail end cap to the fork notch and the lobes grow from its top and bottom walls; pectoral and pelvic fins grow from a lower-flank quad.

Stage 0: reference/sheet_1.png traced with kit/refs.py (height 0.28 m, length 0.70 m). The default threshold (40) dropped the white body (the side outline hugged the black patch); re-traced at --thresh 6, which follows the white flank. The sheet's top view draws the caudal as a horizontal fan, while its side and rear views show it vertical; the model follows side and rear, so the top IoU pays for it.

## Stage 1
- r1: first fit, gates PASS, 544 tris, IoU side/front/top 0.876/0.551/0.686. Critique: az000 — the pectorals are thin blades seen edge-on; the ref front shows broad paddles. Diagnosis: each pectoral level had one z for lead and trail (a flat blade). Fix: the chord drops from lead to trail (lead z 0.072, trail 0.036), blade normal tilted.
- r2: better — front IoU 0.641; 544 tris. Critique: top — the pectoral is a swept spike; the ref paddle has a ~9 cm chord. Fix: lead/trail spread wider at both levels.
- r3: better — rounded paddle in top view; IoU 0.875/0.645/0.654. r4: LOCK (544 tris).
- s2 r1 then FAILED the sliver gate (112 = 18%): 1.5-4.5 mm fins make every rim and edge wall a needle. Lock deleted and stage 1 rebuilt (r5): three levels for dorsal, lobes and pectoral; 4-6 mm half thickness so each fin face's width/length clears tan 6 deg; caudal plate vertices spread by rank, notch end 3.5 cm tall; pectoral rim a short rounded end, uniform thickness.
- r5 (LOCK): gates PASS, 312 verts, 620 tris, edge sha256 d9beb3ccb2e45b82; IoU 0.853/0.654/0.661.

## Stage 2
- r2: joint rings (peduncle tail joint, mid-body flex, gill line), eye-socket inset between H1 and H2 pushed 4 mm in, flat crown over the eyes, slanted mouth pad, snout rings widened (blunt koi snout). Gates PASS: 696 tris, slivers 2 = 0.3%, min IoU vs s1 0.996.

## Stage 3
- r1: colours along existing loops (white ground, orange head cap / shoulder / rear patches, one black patch, orange fin roots), small brown lens eyes with black pupils, one pair of barbels. Gates PASS, 784 tris, 4 colours.
- r2: Critique: az090 — orange reaches the belly, the ref is white below the lateral line. Fix: shoulder patch h > 0.1, rear patch h > 0. Result: better, white lower flank. Gates PASS.

## Stage 4
- r1: rig spine/chest/head + tail1-3 + pec.L/.R (roll Z up: rot Z = yaw); clips idle (hover, tail sway, pectoral paddle), move (swim wave head -> caudal), attack (C-coil, dart forward, head snap). All gates PASS: hit/float/zfight 0, slivers 0.3%, fold-overs 0, drift 0, lock OK, glbcheck OK; clip warning only (22 tris, 0.12% of surface).
- Checks (checks.py on the GLB): orbit18_sheet.jpg — every view reads, no collapse or hole. Separation on the rest mesh: pelvic L-R 9.8 cm, pectoral L-R 18.6 cm, caudal upper-lower lobe 13.3 cm (past the notch): PASS. side_by_side.jpg: sheet views next to the model.

Triangles: stage 1 620 · stage 2 696 · total 784 (under the ~1.5k target; the fish needs few rings).
Weaknesses: fins are ~1 cm thick (the sliver gate's price); the caudal fork notch is a flat 3.5 cm end, not a V; patch borders are blocky (span-sized); black patch wraps the whole back; pelvic fins sit 5 cm ahead of the sheet's top view (side and top views disagree).

## Fix pass (zoo reviews, fable + opus merged)
- Fix list (shape first): (1) broken — pelvic and anal fins hung below the belly like legs; (2) body slender with a flat top (opus) vs long torpedo (fable): the sheet's front/rear views show a plump round koi, so opus wins; (3) pectorals stuck straight out; (4) barbels long tusks; (5) blocky markings (colour, minor).
- Base change, stage 1 re-locked (r6 check, r7 LOCK): mid-body half-width +30% (B2-B5, graded 15-25% at B0/B1/H0/H1), BODY profile shoulder rounded (0.78, 0.8); pectorals swept back ~4 cm and lowered at the tip; pelvics shortened and laid flat along the belly (z 0.033-0.05, was 0.003); anal fin swept back to z 0.062-0.07. Gates PASS, 620 tris, edge sha256 663b9dd48ee63edc; IoU 0.825/0.539/0.646 (lower: the sheet draws hanging fins).
- s2 r3 PASS 696 tris (min IoU vs s1 0.997); s3 r3 PASS 768 tris, 4 colours: barbels halved, thinner, angled forward; fin colour bands re-thresholded for the new fin positions. s4 r2 all gates PASS (clip warning 24 tris, 0.12%).
- checks_blender.py pelvic selector moved to the new fin height. Separation PASS: pelvic L-R 10.8 cm, pectoral 22.6 cm, caudal lobes 13.3 cm.
- Not fixed: patch borders still span-sized blocks.

## Fix pass 2 (round-2 reviews, fable + opus merged; concept sheet as referee)
- Fix list (shape first): (1) broken — pectorals/pelvics splayed to the floor like legs (opus); (2) stepped flat back (opus) / humpback (fable): shoulder profile softened; fable's "deeper -8 %, y x1.1" skipped, the sheet's side is as deep as the model; (3) dorsal and caudal lobes needle-thin from front/rear (both); fable's caudal reach +20 % skipped, the model already matches the sheet's caudal size; (4) patches read as vertical bands (fable, colour).
- Base change, stage 1 lock deleted and re-locked (r8 check: pectorals fully flat read edge-on against the sheet's drooping paddles; r9 LOCK): BODY shoulder (0.78, 0.8) -> (0.72, 0.85); pectorals broader, tip at z 0.040-0.046 (was 0.026), lead raised; pelvics lifted to z 0.046-0.056; dorsal half thickness x1.6, lobes 5 -> 6.5-7.5 mm. Gates PASS, 620 tris, edge sha256 0bfb4e421f646a91; IoU 0.816/0.458/0.638.
- s3: shoulder and rear patches limited to the upper rows (h > 0.3), rear patch ends before the peduncle (a first try with a white break added more stripes, reverted); pelvic band re-thresholded. s4 r4 all gates PASS (clip warning 24 tris, 0.12 %), lock assert PASS, 768 tris.
- checks_blender.py pelvic selector z < 0.058. Separation PASS: pelvic 10.8 cm, pectoral 23.2 cm, caudal lobes 13.3 cm.
- Not fixed: pectoral tips still near the ground plane in the front view (the sheet's paddles droop too); patch borders stay span-sized.

## Poly pass 3 (owner: denser main mesh, same t7 technique)
- Body loft: 15 -> 23 stations (new: peduncle Pa/Pc, rear taper Pb/Ba, belly Bb, shoulder Bc, pectoral girdle Bd, forehead Ha), zb/zt re-read off the side trace columns and W off the top trace rows (sheet half-width x1.05; the mid body is 0.074, was 0.088, as the sheet's front and top); half rings 6 -> 10 vertices, BODY profile re-cut from the sheet's front view (egg widest a little below the middle, rounded back and belly), KEEL and HEAD likewise.
- Fins and pieces unchanged in their tables; they follow the new faces: dorsal on 9 seam faces (P2..Bc), anal on P2+Pb bottom seam faces, pectoral/pelvic on lower-flank face 6, caudal plate on the 10-vertex tail cap.
- Stage 1 re-locked (r10 check, r11 LOCK; old lock and script in before3/): 620 verts, 1236 tris, edge sha256 dcd3b2da4891d8a5; IoU 0.824/0.515/0.663 (was 0.816/0.458/0.638). Budgets: stage 1 900-2200, total 1100-3000.
- Stage 2: tail-joint ring moved to the P1-Pc span; flex and gill rings unchanged spans; eye socket on the head face of ring vertices 3-4 between H1 and H2; crown flat over vertices 0-2 of H2/Ha/H3/H4; snout moves on H5 top 3 / bottom 3 vertices. Gates PASS, min IoU vs s1 0.996.
- Stage 4 r5: all gates PASS (hit/float/zfight 0, slivers 1.6 %, fold-overs 0, drift 0, lock PASS, glbcheck OK); clip warning only (2 tris). Separation PASS: pelvic 10.8 cm, pectoral 23.2 cm, caudal lobes 13.5 cm.
- Tris 768 -> 1432: body loft 348 -> 916, fins and pieces 420 -> 516 (86 % of the increase in the loft). before3/, before_after3.jpg, orbit18_sheet.jpg, side_by_side.jpg rebuilt.
- Not fixed: 1.86x, a little under 2x; patch borders still follow ring faces.

## Mix pass (review_poly2x: MIX)
- Kept the 2x body and tail (P2..H0 stations, 10-vertex BODY profile, fins as before).
- Peduncle: Pa and Pc dropped (5 -> 3 KEEL rings); KEEL back to the before3 6-vertex section, resampled collinear to 10 vertices so it bridges to the body with its flat planes intact. Tail-joint loop back in the P1-P2 span.
- Head: Ha dropped; H1-H5 back to the before3 stations and the before3 HEAD section (resampled collinear, the eye face left unsplit = the before3 eye face, ring vertices 2-3). Eye lens size unchanged from before3. Crown flatten on vertices 0-2 of H2-H4; snout moves on H5 0-2 / 7-9.
- Stage 1 re-locked (r12 check, r13 LOCK; 2x-pass lock and script kept in pass3/): 566 verts, 1128 tris, edge sha256 60b412f9f23e068c; IoU 0.819/0.515/0.655.
- s2 r6 PASS 1252 tris (min IoU 0.996); s3 r6 PASS 1324 tris, 4 colours; s4 r6 all gates PASS, lock assert PASS (clip warning 24 tris, 0.13 %).
- 2x-pass renders kept in pass3/; before_after4.jpg = before3 | 2x pass | now; orbit18_sheet.jpg, side_by_side.jpg rebuilt.
- Lesson applied: density only where the outline bends (body taper), not on the flat-planed head or peduncle.

## Fix pass 9 (owner: keep the 2x density, fix the problems inside it)
- Start: the pass3 2x script (23 stations, 10-vertex rings). The mix pass's density revert undone; its head, eye and peduncle section fixes kept.
- Peduncle ribbed tube: Pa and Pc kept, moved onto the straight P0-P1-P2 lines (z and W linear), KEEL = the before3 6-vertex section resampled collinear to 10, so the extra rings lie in flat planes, no rib bands.
- Head planes: Ha kept, on the H2-H3 line; H1-H5 the before3 stations and the before3 HEAD section resampled collinear (bold flat planes back). Eye face = before3 face (ring vertices 2-3), lens unchanged: as big as before3.
- Junctions (fins, caudal plate, peduncle) checked in close-ups and the orbit: no holes, specks, slits or folds.
- Stage 1 re-locked (r14 LOCK; mix-pass lock and script in before9/): 620 verts, 1236 tris, edge sha256 be20c8d60d58480a; IoU 0.819/0.515/0.655.
- s4 r14: all gates PASS, lock assert PASS, fold-overs 0 (clip warning 24 tris, 0.13 %). Separation PASS: pelvic 10.8 cm, pectoral 23.2 cm, caudal lobes 13.5 cm. Total 1432 tris (mix pass 1324, pass3 1432).
- before9/ = the mix-pass renders; fix9.jpg = hero before9 | after + head and peduncle close-ups; orbit18_sheet.jpg, side_by_side.jpg rebuilt.
