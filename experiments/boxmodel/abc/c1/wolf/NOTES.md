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
