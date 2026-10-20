# wolf, setting c1 (carve + detail)

## Stage 1
- r01: carve_base defaults. Critique: 6 open edges (2 seam fins) fail "closed"; ears flat-topped stubs. Fix: voxel_div 120 (finer hull).
- r02: closed, 1176 tris, IoU side .93 / front .955 / top .973. Critique: ears are flat plateaus (az000, hero), not tall points. Diagnosis: the 4 plateau verts at z 1.07-1.08. Fix: pointmerge them into one tip at the outline's ear tip (0.097, -0.548, 1.10).
- r03: ears pointed, 1164 tris. Critique: any rule paint on a decimated hull will saw-tooth (triangles straddle every border). Fix: cut the colour borders into the base as plane bisects (nose, lip, bib, saddle, belly, fore/hind leg, tail tip) read off the reference side view on a 0.1 m grid; verts within 13 mm snap onto each plane first (no slivers).
- r04: 1396 tris (budget tight). Colour preview: borders are clean straight edge paths. Critique: hind legs tan up to the hip, belly band too thin to see. Fix: hind plane lowered (0.25,0.42)-(0.55,0.22), belly plane raised; carve target 850-1200 for headroom.
- r05: 1334 tris, IoU .927/.956/.974. Critique: ears read as fat pyramids in az090/hero (0.12 m deep base vs ~0.07 in the reference side). Fix: squeeze ear verts above z 0.985 toward the tip's y by up to 40%.
- r06: ears thinner blades, 1334 tris. Reads as a wolf from every view (head wedge, ears, ruff mass, deep chest + tuck, long legs, low brush tail). Remaining: blocky paws, soft face planes, ruff fin at the neck: all stage 2/3 work. Lock.
- r07 (first lock, WITHDRAWN): stage-2 vertex dump showed the hull has a 0.2 m fused forefoot and TWO hind legs per side (the side view's near and far legs are staggered; the hull keeps both) = six legs after the mirror. Visible in hero/az090 once looked for. Unlocked before any stage-2 work (lock file deleted).
- r08: Fix: hand edit of the carve input: in each leg zone the side mask is cleared and redrawn as ONE designed leg (foreleg column with tucked elbow and forward wrist; hind thigh-stifle-hock-cannon), polygons read off the reference grid. Cache deleted -> recarve.
- r09: four legs now (side IoU vs blueprint drops to .79: the blueprint traced both staggered legs; expected). Seam fin / intersection at voxel 124 and 112. Critique: legs are spindles (az090), the hind shin a plank. Fix: thicker leg polygons matching the near legs (fore 0.105 m deep, hind shin ~0.2), voxel_div back to 120.
- r10: carve leaves 4 seam fins (forelegs kissing x = 0 at z 0.32, tail tip) -> "closed" fails at every target tried (850-1250). Fix: split each fin edge, midpoint 2 mm off the seam (5 mm crossed a leg face).
- r11: PASS, 1328 tris. Critique: az090: the tail's front edge is fused to the back of the hind leg down to the paw (a 3.5 mm-voxel gap closed by the mask blur; the plan view overlaps them in x). Fix: hind leg back edge 2-3 cm forward, the clear zone reaches the tail's front line: 6 cm gap.
- r12: tail free of the leg, 1330 tris. Critique: az090 hind leg back edge is one vertical line (no hock) and the stifle sits too far forward (I had read the far leg). Fix: hind polygon redrawn on the near leg: stifle at y .385, a pointed hock at (.59, .205), shin .14 deep.
- r13: hock and stifle read in az090, 1270 tris, all gates PASS. Side IoU vs blueprint .77 (the blueprint carries the far legs; front .955, top .971). Remaining for stage 2: boxy muzzle front, no eye socket/brow, blocky paws, ruff fin. Lock (r14).

## Stage 2 (lock edge hash 6d83ddf5...)
- r01: Critique: hero/az000 face has no eye, no brow, no stop; front reads as a flat square muzzle (pig nose). Fix: eye socket inset (30%, 8 mm deep) on the face at the reference eye, outer/inner brow pushed out and forward, the stop vertex dropped 16 mm, chin pulled back 2.5 cm under the nose, lower jaw verts in 7-8 mm.
- r01 result: 1286 tris, IoU .997. Front view now has a brow line, a nose over a receding chin; socket reads. Sliver 8 (0.6%).
- r02: Critique: paws are boxes with a square toe line and full-width heel (close-up fore paw). Fix: toe corners pulled back/in, middle toe forward, heels narrowed (fore and hind).
- r02 result: 1286 tris, min IoU .98; paws taper to a leading middle toe. Stage 2 done (2 rounds): the rest of the detail is pieces.

## Stage 3
- r01: paint by the stage-1 plane cuts (every border an edge path: nose/chin, lip, bib, belly, saddle, fore/hind tan, tail tip) + ear backs dark. Pieces: almond amber eye lens + pupil set into it, black nose pad, cream inner ears, ruff (3 rows round the neck, 4 bib clumps, 2 cheek tufts), tail brush (4 clumps + dark tip), 16 claws.
- r01 result: 2010 tris, 6 colours; FAIL z-fighting 4 (inner ears 2: plate front only 3 mm off the ear; claws 2). Fix: inner-ear plate 7 mm proud.
- r02: PASS (z-fight 2 = limit, claws), 2010 tris. Critique: hero/az000: the ruff is a scatter of small flat shards hugging the neck; the reference ruff is the biggest secondary mass (layered spikes standing off the neck, a hanging cream bib). Fix: ruff rows moved up/out (3 rows of 4-5), clumps 40% longer and wider, thicker, lifted 0.55 off the skin; bib clumps bigger and higher.
- r03: PASS, 2094 tris. The ruff is now the big layered mass of the reference (hero, az000). Critique: the eyes are pin-pricks (az000/hero): lens 2.0 x 1.2 cm capped by the socket face size. Fix: almond lens 5.0 x 3.0 cm, pupil scaled with it.
- r04: PASS, 2094 tris. Critique (close-ups): eye lens sits level with the socket rim, so only a sliver shows; front view the muzzle tip is a flat box under a wide black plate (pig snout). Fix (face): lens raised to 13 mm proud; muzzle verts in front of y -0.715 tapered up to 30% in x (stage2), nose pad narrowed to match.
- r05: PASS (with orbit), 2094 tris, 6 colours. Eyes read as amber almonds with pupils; muzzle tip narrower. Remaining: socket normal tilts down (eye looks at the ground a little), hind paws small.

## Stage 4
- r01: k3's rig and clips (spine/chest/neck/head, ear, 3 tail bones, 3-bone legs, roll auto) on joints read off this base (J); every piece bound with the body's weights.
- r01 result: FAIL folds 30 (1.43%). Per-clip diagnosis (techqa.measure per action): attack folds the throat + bib clumps (neck -26 crushes the throat); move folds the back of the hock and the low tail brush (the tail hangs 3-6 cm behind the hock and shares its weights).
- r02: Fix: the lunge goes through the chest and head (neck -14 max, chest -10, head -22) and the hind trot swing is 10/20 deg (was 16/28). (A region split of tail/leg weights was tried in diagnosis and made it worse: reverted.) Diagnosis predicts 8 folds.
- r02 result: all gates PASS (folds under limit; WARN stretch 4 tris 2.81x, clip 16 tris). Orbit, --review, --compare done.

## Totals
- triangles: stage 1 1270 (lock 6d83ddf5...), stage 2 1286, stage 3/4 2094; 6 colours.
- rounds: s1 14 (first lock at r07 withdrawn: six legs), s2 2, s3 5, s4 2.
- vs abc/k3/wolf: richer silhouette (layered ruff, bib, cheek tufts, brush tail), the reference's colour map (saddle, cream belly band, tan legs, cream chin) on clean edge-path borders, almond eyes with pupils, inner ears, nose pad. Weaker: front view is a cream wall with a small head; forelegs tan from the chest down read as one block; hind paws small; eye socket normal tilts down.

## Team pass (builder, from review/ad_notes_team.md; rounds 15-29)
- r15 (s4 baseline): all gates PASS on the old lock (zfight 2, sliver 0.5%, flips 0.38%/0.45%, drift 0).
- r16-17 (s1, STAGE-1 UNLOCK, AD 1): Critique: forelegs one tan column, hind the same (az000/az180). Diagnosis: a visual hull has no view through the legs. Fix: `LEG_CHANNEL` clears the hull field between the legs in two y-bounded boxes (fore y -0.52..-0.16 below z 0.55, half gap 0.05; hind y 0.20..0.585 below z 0.45, half gap 0.04; the tail on x = 0 behind the hocks is outside both), wrapped round carve.hull_field from the program (kit not edited). Result: two columns from the chest floor, 1346 tris, s1 gates PASS, re-locked (old lock -> stage1_lock.pre_team.json, old carve -> carve_base.pre_team.json). Gap 0.10 m fore / 0.08 hind, not the asked 0.17: wider would thin the leg columns (the note also says keep their section).
- r18-19 (s2 on the new base): the exact-vertex nudges no longer matched: `nudge` takes the nearest vertex within 3 cm, paw nudges re-read off the new base. FAIL sliver 30 (2.2%), needles along the colour cuts. Fix: `unsliver` (tangential slide of needle verts; seam and cut-plane verts stay on their planes). Result: sliver 8 (0.6%), IoU .984.
- r20-23 (s4, item 0): FAIL drift 2 shells. Diagnosis (per-clip techqa, WOLF_DBG=1): the row-2 ruff clump at -12 deg, root (0.149, -0.47, 0.805) on the jaw/neck crease, comes off in the attack. Tries: low bib row dropped + bib -30% (AD 4, kept), cheek tufts 2 -> 1 (AD 4), row-3 clump -30 -> -18 (no effect, kept); fix: that clump to -20 deg (and -38 -> -42). Result: drift 0, all gates PASS.
- r24 (s2, AD 2): tail verts x -35%, root 25% thinner front-to-back, lower half swung back up to 0.15 m. Result: az090/back34 the tail angles back off the rump and the tip trails the hocks; IoU min .944.
- r25 (s2, AD 5): underside verts between the elbow line and the stifle raised up to 5.5 cm (cut-plane verts untouched). Result: a waist behind the ribs in az090; IoU .936.
- r26 (s3, AD 3): lens 7 x 4.2 cm, 17 mm proud, its top plane ~30 deg forward of the socket normal, pupil scaled up; a dark lip strip on the lip edge path (5 mm proud; 3 mm z-fought). Result: both eyes read in az000, mouth line in every view.
- r27 (s3/s4, AD 4 + tail follow-up): one cheek tuft per side behind the jaw (-0.545, 0.79); tail brush rows, brush axis and tail2/tail3 joints moved onto the swung tail. PASS, drift 0.
- r28 (should-fix): hind paws +20%, ear tips +12 mm, inner-ear plate 0.80 -> 0.92, ruff rows small/big/medium (0.085/0.118/0.095 wide). zfight 4 (hind inner claw on the wider paw) -> hind claw row moved out 1 cm: 2 (limit).
- r29 (final, orbit): hit 0, float 0, zfight 2, sliver 12 (0.6%), flips 2 (0.09% tris, 0.03% area), drift 0, lock PASS, s2 IoU min .934, glbcheck OK. 2170 tris (base 1346), 6 colours. WARN clip 9 tris (posed, tail brush). Orbit advise: az000 head_merged (the head still sits inside the ruff outline from the front).
- Not done: claw z-fight lift (still 2, at the limit). Partly: AD 1 gap width (0.10 vs 0.17), AD 4 (bib ends at the elbow and one tuft; the front is still a broad cream ruff round the head).

## Team pass, second pass (builder, from review/verify_team.json; rounds 30-38)
- r30 (s4 baseline): all gates PASS, unchanged from r29.
- r31-33 (s2, AD 2 PARTLY): Critique: tail still a deep slab fused into the thigh (back34, hind close-up). Diagnosis (vertex dump, WOLF_DBG=<file>): the hull filled a web between the back of the hind leg and the tail from z 0.29 to 0.53, and the tail left the body at z 0.45. Tries: front of the tail pulled to its back line (`TAIL_FRONT`, little effect alone); web verts snapped up to z 0.44 (10 then 4 self-intersections after `unsliver`). Fix: tail x -45%, rump back line leans out 4 cm, crotch vertex up 6 cm, leg-back verts between hock and z 0.46 slide up 60% graded by y (`WEB_Z`, `WEB_K`; the hock ring stays). Result: a notch under the tail above the hock in az090; IoU min .935. Still a wedge at ~45 deg from mid-thigh: a free-hanging brush needs the web cleared in the hull (stage 1, not unlocked for this item).
- r34 (s2, AD 5 PARTLY): `BELLY_TUCK` 5.5 -> 8.5 cm. Result: the underline rises clearly from the elbow to the stifle in az090; IoU az090 .926.
- r35 (s3/s4, AD 2 + AD 4): tail brush blades only on the tail (the two on the thigh/rump removed; lowest one moved up after FAIL hit 2 shells: it passed through the narrowed tail); cheek tuft removed; ruff row 1 narrower (0.085 -> 0.072), the sideways clumps (0, 16 deg) grey. PASS.
- r36 (s2, AD 4 PARTLY): skull and cheeks 14% wider (`HEAD_WIDE`; fades to the neck and below the ears, so EAR_TIP and the ear plates hold). IoU az000 .968, top .955.
- r37-38 (final, orbit): ruff clumps at -20 / -18 deg grey as well (grey flank, cream centre, as the reference front). hit 0, float 0, zfight 2, sliver 14 (0.7%), flips 2 (0.09% tris, 0.03% area), drift 0, lock PASS, s2 IoU min .926, glbcheck OK, 2130 tris. WARN clip 4 tris (posed). Orbit advise unchanged: az000 head_merged.
- Partly: AD 2 (notch and narrower brush, still a wedge off the thigh: stage 1), AD 4 (head wider, no tuft, grey flank clumps; the chest is still a cream block from chin to leg tops: the body's bib colour sits on an edge-path border that is on the keep list).
