# tiger (t7 hand box-model) — NOTES

Technique: wolf_base's t7r look. One spine loft of 6-vertex half rings from the tail tip to the nose. The legs are 2-face extrusions from the lower flank (spans C0 and R1), and the ears are 1-face extrusions from the H0 span. Stage 0: refs.py traced reference/sheet.png into blueprint.json (height 1.1 m, length 1.83 m). Sections were read off a 5 cm grid over side.png and the traced outline.

## Stage 1
- r1: first fit. FAIL: 4 self-intersecting pairs at the inner fore-leg root (x 0.05-0.07, z 0.354). Diagnosis: the elbow section (z 0.40) sat above the chest bottom (z 0.35-0.37), so the inner leg wall folded up. Blueprint IoU side/front/top 0.787/0.872/0.833.
- r2: elbow section lowered to z 0.32 and narrowed. PASS, 692 tris, IoU 0.789/0.866/0.833.
- r3: Critique (blueprint overlay): the tail sat above the ref tail and did not hang low enough; the back dipped at the neck; the head top and jaw were too low; the shoulders were too narrow in the top view. Fix: the tail re-fit to the traced edges, the C0-H0 tops raised 3 cm, the jaw lowered, C0/C1/R1/R2 widened, the forelegs made deeper and moved out. PASS, IoU 0.823/0.873/0.838.
- r4 (LOCK): Critique az000/hero: the head read as a wolf wedge, with the muzzle tapering to a point. Fix: muzzle widths H1-H4 0.16/0.125/0.105/0.08 (a broad cat muzzle). PASS, locked: 348 verts, 692 tris. IoU 0.823/0.873/0.829.

## Stage 2
- r1: elbow, stifle and neck-skull rings; 16 stripe loops (2 per band) in 8 spans (3 tail spans, 5 body spans that hold no leg); an eye socket inset in the H0b-H1 stop face; brow, cheekbone, flat muzzle planes, nose pad. FAIL: the changes were not logged.
- r2: each change wrapped in topo(). PASS, 1096 tris, min IoU vs s1 0.994.

## Stage 3
- r1: palette (orange, stripe, cream, nose, amber, pupil) painted along the loops. Stripe = the band faces between each pair of loops (an int face layer). Pieces: small lens eyes, 3 cream cheek-ruff clumps per side, 4 claws per paw. PASS, 1584 tris. Critique (hero): the nose colour covered the whole muzzle front, and the ruff clumps stood out as wings.
- r2: Fix: the ruff laid back (lay 0.08/0.9/-0.4, s 0.04) and the nose test narrowed. PASS. The ruff now hugs the jaw, but the nose test no longer caught any face.

## Stage 4
- r1: Fix: nose = the top faces of the muzzle near the seam, plus the cap tip. Rig: 16 bones + .R mirrors; clips idle 48, move 24 trot, attack 32 crouch-and-swipe. All gates PASS, glbcheck OK. Warning: 12 tris (1.16%) clip in poses.

Checks: orbit18_sheet.jpg (18 views, EEVEE) reads from every angle, with no collapse. Separation on the rest mesh: tail to hind legs 15.5 cm, fore L-R 10 cm, hind L-R 11.4 cm: PASS. side_by_side.jpg shows the reference views next to the model.

Triangles: s1 692, s2 1096, total 1584.
Weaknesses: the head is smaller and less round than the ref's ruffed head; the stripes are straight vertical bands (the ref's are slanted and forked); one symmetric leg pair stands in for the ref's staggered pairs.

## Fix pass (review_fable + review_opus merged)
Fix list, shape first: head small/narrow (wolf read), long neck, thin legs and paws, thin tail, shallow chest; ears pointed; face mask too pale.
- Base change, stage 1 re-locked (old lock kept in before/). r5: head H0-H4 widened ~20-30 %, raised, pulled back 3 cm (shorter neck and snout, deeper muzzle step); chest bottom 5-6 cm lower and wider; fore and hind legs radius ~+25 %, paws ~+30 %, legs moved out 2-3 cm; tail base radius +50 % with a smooth taper; ear tips blunter. FAIL: 4 self-intersecting pairs at the tail root. r6: T4 thinned and lifted, R0 bottom restored. PASS. r7 (LOCK): ear tips narrowed. PASS, 692 tris, IoU 0.827/0.756/0.812 (front IoU drops because the head is now wider than the traced outline, as on the sheet).
- Stage 2 r3, stage 3 r3, stage 4 r3: PASS. Critique: the nose colour covered the whole muzzle top. Stage 3/4 r4: nose limited to the centre tip, lips/chin cream raised; cheek mask shrunk, ear rule kept above the cranium. PASS, 1584 tris, posed clipping 0.13 %.
- Checks: separation tail-hind 13.8 cm, fore L-R 9 cm, hind L-R 10.5 cm: PASS. Orbit 18 all in colour.
Not fixed: stripes still straight vertical bands; ears read squarish rather than round.

## Fix pass 2 (review2_fable + review2_opus merged, sheet as referee)
Fix list, shape first: face reads as a mask (white cheek ruff flaps, pink nose bar, white chest); shoulders higher than hips; head as wide as the chest; muzzle short.
- Base change, stage 1 re-locked (old lock in before2/). r8 (LOCK): C1/C2 tops -4 cm, N0 -3 cm (sheet back near level, slight shoulder kept); head W H0/H0b/H1 -12 %/-12 %/-10 %; muzzle H3/H4 1.5-2.5 cm forward. PASS, 692 tris, IoU 0.823/0.768/0.819.
- Stage 3/4 r5-r6: cheek ruff pieces removed (both reviews flag them; owner no-mask rule); cheek cream rule removed; nose limited to a small tip; throat cream narrowed. PASS, 1464 tris, lock assert PASS, glbcheck OK; posed clipping warning 1.87 %.
- Checks: separation tail-hind 13.8 cm, fore L-R 9 cm, hind L-R 10.5 cm: PASS. Orbit 18 all in colour. side_by_side.jpg and before_after2.jpg rebuilt.
Skipped: Opus "lengthen torso 15 %" (side IoU already matches the sheet length). Not fixed: straight vertical stripes; lower muzzle cream block still broad.

## Density pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- Old lock, script and hero/orbit/side sheets kept in before3/.
- Base change, stage 1 re-locked. Half rings 6 -> 10 vertices: a rounded point goes into each of the first four spans of every profile (Catmull-Rom midpoint on the ring mirrored across the seam). Spine stations 20 -> 31: tail bend T2b, tail root T3b, rump R0b, belly tuck R2b, belly W0b, flat back to the shoulder M0b, chest front C1b, throat C2b, nape N0b, forehead H1b, muzzle bridge H2b; each fitted to the traced side top line and the old stations' offset from it, not interpolated. Legs: 4-face root strip, 10-vertex elliptical rings, plus forearm, ankle, thigh and gaskin stations (fore 7, hind 8). Ears from the new upper span face.
- r9: FAIL, 2 self-intersecting pairs under the tail root (T4 bottom sat behind R0 bottom). R0 bottom moved forward. PASS, LOCK: 874 verts, 1744 tris, IoU 0.827/0.772/0.815 (was 0.823/0.768/0.819).
- Stage 2-4 r7: neck-skull ring now N0b-H0; stripe loops moved into the new half spans; eye socket in the upper half of the split stop face (inset 0.25); muzzle flats over H2-H4 incl. H2b. FAIL: slivers 3.4 % (stripe loops too close to stations). r8: bands at 0.25-0.75 of each half span. All gates PASS, lock assert PASS, glbcheck OK, posed clip warning 0.54 %, s2 min IoU vs s1 0.994.
- Triangles: s1 692 -> 1744, body 1096 -> 2452, pieces 368 -> 368 (eye 48, claws 320), total 1464 -> 2820 (1.93x); all of the increase is in the body loft. Budgets: stage 1 1200-2600, total 2000-4600.
- Checks: separation tail-hind 12.7 cm, fore L-R 9 cm, hind L-R 10.4 cm: PASS. orbit18_sheet.jpg, side_by_side.jpg, before_after3.jpg rebuilt.

## Mix pass (review_poly2x: MIX, restore before3 chest/ruff and legs, keep new head and torso stripes)
- 2x-pass lock, script, hero, orbit and side sheets kept in pass3/.
- Base change, stage 1 re-locked. CHEST profile and the N0 neck/ruff ring keep 10 points but the added points sit on the straight before3 spans (flat planes back); M0b, C1b, C2b, N0b stations removed (31 -> 27). Legs: before3 stations (fore 5, hind 6); 10-vertex rings kept for the 4-face root, mid points on the before3 hexagon edges. Head (H0-H4, H1b, H2b), tail and torso stations unchanged from pass 3. Stripe spans M0-C0, C1-C2 and neck-skull ring N0-H0 back to before3.
- r10 (LOCK): PASS, 722 verts, 1440 tris, IoU 0.825/0.774/0.817. Stage 2-4 r9: all gates PASS, glbcheck OK, posed fold-overs 0 %, slivers 0.5 %.
- Triangles: s1 1744 -> 1440, total 2820 -> 2516.
- Checks: separation tail-hind 13.5 cm, fore L-R 9 cm, hind L-R 10.5 cm: PASS. orbit18_sheet.jpg, side_by_side.jpg rebuilt; before_after4.jpg = before3 | 2x pass | now.
Not fixed: the forearm cream patch from the 2x pass remains (paint rule, not ring density).

## Owner fix pass 5 (owner: tiger too bad relative to others)
- Old hero, orbit, side sheets, lock and script kept in before5/.
- Diagnosis (zoomed vs sheet and bear/golem/crab): 1) head a flat-topped long dog/hippo box, narrower than the ref's round ruffed head; 2) eye a pin dot, unreadable at zoo scale; 3) lower muzzle a broad grey-cream block, no visible nose; 4) ears tall square posts; 5) few, sparse stripes, weak colour rhythm on the flank.
- Base change, stage 1 re-locked. r11 (LOCK): HEAD/HEADF profiles fuller in the cheek (lower side points out), H0-H1b widened ~5-12 % and the crown raised 1.5 cm (round cranium); H3/H4 1-2.5 cm back, H4 deeper and wider (short blunt cat muzzle); ears lower and broader, tip corner 0.7. PASS, 722 verts, 1440 tris.
- Stage 2-4 r10-r11: 3 extra stripe bands (R0b-R1, R2b-W0, W0-W0b); lens eye r 0.019 -> 0.027 with a larger round pupil in the same socket; nose pad on the muzzle front only; lip/chin cream limited to the lower jaw. All gates PASS, lock assert PASS, glbcheck OK, posed fold-overs 0 %, posed clip warning 0.03 %.
- Checks: separation tail-hind 13.5 cm, fore L-R 9 cm, hind L-R 10.5 cm: PASS (no fused parts). orbit18_sheet.jpg, side_by_side.jpg, before_after5.jpg rebuilt. Total 2732 tris.
Not fixed: throat/chest cream still reads grey in shadow; stripes still straight bands; ears still flat-faced.

## Owner crop pass 6 (1 crop: fore leg / chest join)
- Old stage4, orbit, side sheets, lock and script kept in before6/.
- Crop 1 (near fore leg front, under the grey chest): the leg root strip on C0-C1 went straight to the elbow ring, whose front sat 13 cm ahead of and 30 cm below the root's front edge on C1, so the leg front tucked under the chest's C1-C2 plane: a V slit at the C1 edge (probe: concave folds 117-169 deg along it, no open edges, no slivers).
- Fix (stage 1 re-locked, r12 FAIL 2 self-intersecting pairs at the inner rear root corner; r13 LOCK): shoulder station FSH between the root strip and the elbow, front on the C1-C2 chest plane, inner side tilted down below the root's inner corner. Leg top now fills out under the chest, no slit. 742 verts, 1480 tris, IoU 0.823/0.756/0.811.
- Stage 2-4 r12: all gates PASS, lock assert PASS, glbcheck OK, slivers 0.3 %, posed clip warning 0.03 %. Separation tail-hind 13.5 cm, fore L-R 9 cm, hind L-R 10.5 cm: PASS. orbit18_sheet.jpg, side_by_side.jpg, crop_fix.jpg (crop | before/after, hero and low close-ups, clay) rebuilt.

## Dense pass 9 (owner: keep the 2x density, fix its problems inside it)
- Old stage4, orbit, side sheets, lock and script kept in before9/. Started from the current script (all fix5/fix6 head, eye, ear, nose, stripe and shoulder-junction fixes kept) and put the 2x density back.
- review_poly2x WORSE parts and fixes: lumpy chest/ruff -> the 2x rings M0b, C1b, C2b, N0b return as rings exactly on the straight line between their neighbours (co-planar with the before3 chest/neck planes, no lumps); noisy leg banding -> the fore (forearm, pastern) and hind (thigh, gaskin, ankle) stations return as halfway rings on the flat hexagon leg planes (fore 8 incl. shoulder, hind 9; no radius wobble); torso less boxy -> the BODY profile's added points now sit on the straight spans (flat torso planes, crisp back edge). Head and eye unchanged (lens r 0.027).
- Stage 1 re-locked r14: PASS, 914 verts, 1824 tris, IoU 0.823/0.756/0.811. Stage 2-4 r14 FAIL (a C1-C1b stripe cut at t 1.0 landed on the C1b ring); r15 band 0.35/0.45: all gates PASS, lock assert PASS, glbcheck OK, slivers 0.4 %, posed clip warning 1.10 %.
- Junctions (orbit 18, low views): no holes, specks, slits or folds at the leg, ear, tail and neck joins. Separation tail-hind 13.5 cm, fore L-R 9 cm, hind L-R 10.5 cm: PASS (no fused parts).
- Triangles: s1 1480 -> 1824, total -> 3116 (2x pass was 2820). orbit18_sheet.jpg, side_by_side.jpg, fix9.jpg (hero before9 | after, chest/fore-leg and torso/hind-leg wire close-ups) rebuilt.
