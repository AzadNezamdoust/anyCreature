# boar, setting c1 (carve + detail)

Pattern: abc/c1/wolf (quadruped, staggered legs). Hand-built comparison: abc/k3/boar.

## Stage 1
- r01: carve_base voxel_div 120, target 850-1200, side mask legs redrawn as ONE leg per pair (the sheet's near/far legs stagger 5 cm fore, 15 cm hind). 1064 tris, IoU s/f/t .866/.974/.972. Critique: hindquarters a thin blade (az135, az180). Diagnosis: the plan view is 11% shorter than the side (its tail lies flat, so its rump ends at y 0.48 vs the side's 0.62; refs.py did not warn because both bboxes incl. the tail are 1.33 m). Fix: plan mask resampled along y so snout and rump match the side, plus a thin tail strip.
- r02: 1074 tris; hindquarters full. Critique: stacked terraces along the spine (top, az180). Diagnosis: the side crest's saw-tooth. Fix: side mask cleared above a smooth mane line (peak 0.858 at the withers); crest spikes become stage-3 clumps.
- r03: 1050 tris; terraces remain. Diagnosis: the front view's crest is also a saw-tooth (half-width 0.20 -> 0.12 -> 0.05 in 10 cm, ears beside it). Fix: front mask above z 0.62 clipped to a smooth roof; ears become stage-3 pieces.
- r04: 1062 tris (a first run carved with a reversed interp table: cache deleted, recarved). Terraces fewer but still at mid-back (top). Diagnosis: the narrow ridge descends through voxel layers. Fix: hand edit, 6 z-only smoothing passes on back verts (z > 0.62).
- r05: 1062 tris, IoU .867/.905/.816 (front/top lower by design: crest and ears left for pieces; the plan remap). Reads as a boar base: high withers hump with a mane ridge, long low head, deep chest, tucked belly, round hams, four legs with a hock. Head is blunt/round: stage-2 planes.
- r06: lock (with orbit, rc 0). Edge hash 600856eb... One lock, no re-locks.

## Stage 2 (lock edge hash 600856eb...)
- r01: Critique: the snout end is a rounded blob, no eye socket (hero, az090). Fix: verts in front of y -0.635 flattened onto the disc plane y -0.664; eye socket inset (35%, 8 mm deep) in the face at the reference eye (0.123, -0.471, 0.532). Result: PASS, 1074 tris, IoU min .995.
- r02: Critique: a decimated hull has no edge along any colour border (rule paint would saw-tooth). Fix: four planar bisect cuts logged as loops: snout-disc rim (y -0.648), hoof line (z 0.045), mantle front (behind the ear) and mantle lower edge (withers -> mid-back), read off the reference side. Result: PASS, 1274 tris, slivers 0.5%.
- r03 (driven from s3 r07, az000): no brow; the socket's upper rim vert pushed out/forward/up 10/10/4 mm. PASS.

## Stage 3
- r01: paint by the stage-2 cuts (brown, dark mantle, pink-grey disc, black hoof) with colour_from_sheet's clusters mapped to the brief roles; pieces: almond eye lens, two hex nostrils on the disc, curved 5-sided tusks from the lower-jaw corner, cupped pointed ears, ONE connected crest strip of 7 combed clumps (nape -> mid-back, tallest at the withers), dark tail tuft. 1856 tris, 6 colours, PASS. Critique: the sheet's lit brown #635149 renders near black (hero, az000).
- r02: brown #7d5843, dark #46322a (brief hues, mid values). Reads as the reference's warm brown with a dark mantle.
- r03-r06: Critique: ears read as thin dark horns (az090, az000). r03 plate turned 40 deg to the flank (no visible change), r04 broader leaf (still buried), r05 base printed: the ray hit the cheek slope at z 0.603, so the wide base sat inside the head; r06 seated at x 0.092 on the skull top: broader triangles, FAIL float 2; r07 sunk 4 mm: PASS.
- r08: eye lens 1.4x, tusks 1.3x thicker, brow (stage 2 r03). Eye still a pin-prick: lens buried under the socket rim.
- r09: lens 20 mm proud of the socket floor (12 mm over the rim): small dark eye reads in az000/az090. PASS, 1856 tris.

## Stage 4
- r01: k3/boar's rig and clips on this base's joints (J); all pieces body= bound. FAIL flips 12 (0.65%): all on the ears (ear bone blended with head).
- r02/r03: ears rigid to head (r02 matched no piece: names are 'piece_ears'; fixed in r03): flips 0, drift 2 (skin under the ear part neck).
- r04: body= again, ear keys removed: flips 8 (0.43% tris, 0.56% area): FAIL on area.
- r05: ears rigid to head and the neck joint moved back 5 cm (-0.34 -> -0.29) so the skin under the ears is head: all PASS, flips 0, drift 0, clip 0.
- r06: final with orbit (rc 0; advisories az000 head_merged, az180 head_hidden: a head-low boar), glbcheck OK; --review, --compare.

## Totals
- triangles: stage 1 1062 (lock 600856eb...), stage 2 1274, stage 3/4 1856; 6 colours. Posed clip 0, flips 0.
- rounds: s1 6 (one lock), s2 3, s3 9, s4 6.
- Kit notes: refs.py did not warn that the plan view's body is 11% shorter than the side's (both bboxes include the tail, which lies flat in the plan); carve_base's cache key does not see mask edits (keyed here via carve_mask.key) or code bugs in them.
- vs abc/k3/boar: fuller carved mass (hump, hams, deep chest), the reference's dark mantle on clean edge borders, a flat pink-grey disc with nostrils, thick tusks framing the disc, brow + socketed eye, crest strip. Weaker: ears are narrow spikes from the side; crest clumps evenly spaced; mantle border is one straight diagonal.

## Team repair pass (notes: review/ad_notes_team.md; R0 = 10)
- s4 r10 baseline: all gates PASS (hit/float/zfight 0, slivers 4 = 0.2%, flips 0, drift 0). No item 0.
- r11 (must-fix 1, ears): Critique: ears read as thin dark horns (az000, az090). Fix: piece_ears rebuilt as a lens-section leaf (no thin side walls), base 0.11 wide, 0.14 long, 30 deg forward / 35 deg out, base verts seated by a ray onto the skull and sunk 4 mm. Result: PASS, but still spikes: the tip only reaches z 0.75, against the dark hump (0.86) behind it.
- r12: 45 deg out, 0.16 long. Still spikes from the front. Diagnosis: the width ran along the outward lean, so the front view saw the leaf edge-on.
- r13: plate face (cup) set to open forward and out, width across it: az000 shows a leaf now, but all dark on the dark mantle.
- r14: 6-point section (rim, cup, rim): dark only on the inner cup, a brown rim and back. az000 reads as two leaf ears with a dark cup. Slivers 8 (0.4%).
- r15: cup turned 15 deg more toward the flank (az090 showed a spike): a narrow leaf from the side, tip ahead of its base. PASS. Ear base partly hidden by the hump in hero (base not touched).
- r16 (must-fix 2, crest): Critique: 7 identical teeth on a fixed pitch, bare nape (az090). Fix: 9 clumps with their own base length (0.09-0.15), half-width (0.03-0.05) and height (0.05 nape, 0.092 withers, 0.026-0.032 last two), each overlapping the next by a third, valleys at 35 % of the smaller neighbour, peak behind the centre (combed back), strip from y -0.397 (2 cm behind the ear seat). Result: PASS (hit 0, float 0); az090 reads dense and tapering, no two neighbours alike.
- r17 (must-fix 3, eye): Critique: the eye is a 2-3 px dot, no brow (az000). Fix: lens 1.4x (ha 0.040, hb 0.024; 1.8x would leave the socket face), its outer (rear) corner rotated 10 deg down; dark paint on the facets around the socket (BROW_C r 0.05) and the jowl beside the tusk root (JOWL_C r 0.04). Result: PASS; the eyes read, but the brow paint only hit 6 side facets.
- r18: the brow band over the eye (x > 0.06, y -0.54..-0.43, z 0.50..0.63, facing forward) painted dark: one large forehead facet per side, a dark V over the eyes in az000 (the reference's mean brow). PASS.
- r19 (stage 2): the brow rim verts a further 6 mm out along the socket normal: lens in shadow. IoU min 0.993, hit 0, z-fight 0. PASS.
- r20 (must-fix 4, stage 2): Critique: hind legs straight columns (az090). Fix: back-shear of the hind leg verts, 0 at the hoof ring, 6 cm at the hock band, 3 cm at z 0.42. FAIL: 2 self-hits (the shear reached the rump/thigh above z 0.38), IoU .957.
- r21: shear kept under the ham (z < 0.38, x > 0.04 so the tail is out): 0 at z 0.065, 5.5 cm at z 0.18 (the hock), 4.5 cm at z 0.27, 0 at z 0.38. PASS, IoU .97; az090 shows a hock angle and a cannon angled forward to the planted hoof. The cannon front not flattened (few verts on it).
- r22: forelegs 10 % narrower in x below the elbow (blended out at the elbow and hoof ring). PASS, IoU .967.
- r23 (must-fix 5): Critique: the mantle's lower edge was one straight diagonal; body brown read orange. Fix: the 'mlow' cut replaced by two logged planar cuts, a polyline (-0.28, 0.48) -> (-0.04, 0.46) -> (0.36, 0.75): the edge dips ~12 cm over the shoulder blade behind the foreleg, then rises to the back toward the hip; paint follows the polyline; brown #6f5040 (brief). PASS, IoU .967, slivers 12 (0.6 %). az090 shows the shoulder saddle.
- r24 (should-fix): tail base thinner (0.016 -> 0.011), tuft 30 % longer (to z 0.17), hanging; attack toss neck 10 -> 18, head 15 -> 20 (head lifts ~10 cm at f016). PASS (flips 0, drift 0).
- r25: full run with orbit: all gates PASS, but WARN clip 25 (body 20, tuft 3, crest 2; baseline 0): pink on the tail, tuft and the back of the hind legs (back34 tech).
- r26-r27: diagnosis runs: not the toss keys, not the idle tail flick; move tail swing 8 -> 3 deg cleared the tuft (3 -> 0); a smaller hock shear (4 cm) only halved the body clip (12), so the 5.5 cm hock was kept.
- r28-r29: Diagnosis: the hock, now 5.5 cm further back, swings through the hanging tail when the thighs go back (move, attack f008). Fix: the tail lifts 12 deg away from the hams in those keys (r28 +12 was the wrong sign: clip 52; r29 -12: body clip 0). WARN clip 2 (0.01 %, crest under the ear in the toss).
- r30: final with orbit, glbcheck, --review, --compare.
- Team pass totals: 1978 tris (stage 2 base + 2 mantle loops), 6 colours; hit/float/zfight/drift 0, slivers 12 (0.6 %), flips 0, clip 2 (warning), IoU min .967, lock PASS (no unlock), glbcheck OK. Rounds r10-r30. Not done: cannon-front flatten, hoof notch, snout-disc tilt, sliver merges.

## Team repair pass 2 (verifier: review/verify_team.json; items 1 and 5 PARTLY, clip regression; R0 = 31)
- r31 (item 1, ears): Critique: a thin spike in hero / az090. Diagnosis: the cup was 12 mm deep, so edge-on the leaf had no breadth. Fix: cup 45 mm at the widest row, lean 36 deg forward. Result: PASS, still a horn in hero (the far ear lies near horizontal at 45 deg out); clip 8.
- r32: lean 30 deg out / 25 forward, 0.18 long (upright leaf). az090: an upright triangle, tip ahead of the base. clip 5.
- r33: wider and deeper (half-width 0.058 / 0.072 / 0.054, cup 55 mm, 0.20 long): a broad leaf in az090 and az000, a blade with a visible cup in hero. PASS.
- r34 (item 5, mantle, stage 2): Critique: the lower edge still one diagonal. Fix: MLOW polyline (-0.28, 0.48) -> (-0.04, 0.45) -> (0.10, 0.66) -> (0.44, 0.69), three logged planar cuts: level over the shoulder, a 56 deg rise behind the shoulder blade, then a strip under the spine to a soft point at the hip. Result: PASS, IoU .967, slivers 6 (0.3 %), 1972 tris; az090 shows the reference's saddle.
- r35 (clip regression): own ear bones with a counter-rotation in the toss, crest front narrower, toss off: none cleared it (reverted). Not the toss alone.
- r36: crest end sections buried: no change. A temporary print of the clipped triangles (removed) showed: crest = the underside of the last clumps at y 0.24-0.28 (spine bend), ears = the right ear's cup back against the hump at attack f016-f019.
- r37: rear crest skirt 12 mm deep (y > 0.15), ear seat 15 mm forward (y -0.420): crest clip 0, ears 1.
- r38: toss head roll 10 -> 5 deg: clip 0. All gates PASS.
- r39: final with orbit, glbcheck, --review, --compare.
