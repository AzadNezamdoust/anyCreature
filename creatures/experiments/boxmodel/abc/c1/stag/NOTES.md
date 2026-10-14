# stag, setting c1 (carve + detail)

Reference conflicts: the sheet's body is 1.42 m long (brief 1.8 m); the side view wins (as k3).
Antlers: a visual hull of thin branching tines is a blob, so the carve input is cleared above the
skull and the antlers are rooted stage-3 pieces bound to the head (BRIEF §7: "antlers can wait,
the body plan cannot"); the stage-1 base carries the deer body plan (long neck, deep chest, slim legs).

## Stage 1
- r01: carve with side-mask edits (antlers cleared above the skull; fore/hind leg zones redrawn as one leg each, read off the near legs), voxel_div 120. PASS, 1070 tris, IoU side .70 / front .68 / top .87 (the blueprint carries antlers + staggered legs). Critique: legs are needles (az000, az090): the 0.05 m cannons lose to section rounding + decimation; the head is a hammer (ears + top-view antler spread fused). Fix (legs): voxel_div 150, leg polygons ~25% deeper (stylised).
- r02: 1114 tris; legs have mass in az000. Critique: the hind leg ends at the hock (az090): no cannon or hoof. Diagnosis: the plan view tapers at the rump (x < 0.08 at y 0.68) and hides the legs, so the hull cut the hind cannon (x 0.06-0.14). Fix: leg footprints added to the plan mask (generic mask editor for side/front/top).
- r03: four legs, 1128 tris (a 4 mm triangle lying in the seam plane was dropped by the mirror merge -> 3 open edges; such faces are now point-merged). Critique: the head is a hammer (az000, az045, top): ears and the plan view's antler spread fuse into a slab over the skull. Fix: ears + antlers cleared from all three masks (side: above the poll/mane line; front: |x| > 0.085 above z 1.17 and all above 1.335; plan: |x| > 0.085 ahead of y -0.36). Ears become stage-3 leaf pieces.
- r04: 1116 tris; clean narrow skull. Critique: hero/az000: the head pokes straight out of a neck column as wide as the chest (no jaw/throat separation; reads sheep-like). Diagnosis: the front view's shaggy mane (+-0.17 at z 0.9) sets the hull's neck width. Fix: front mask neck redrawn slim (+-0.085 at the jaw to +-0.16 at the shoulders); the mane goes to stage 3.
- r05: 1122 tris; head and jaw now stand off a slim front-view neck. Critique: the rump is a square box end (top, az090, az135) where the reference rump rounds into the tail. Diagnosis: the plan's hind-leg footprint rectangle (to y 0.72, x 0.15) overrides the plan's rump taper. Fix: the footprint's back-outer corner is cut (x 0.15 at y 0.60 -> 0.115 at y 0.715).
- r06: 1126 tris; rump rounds again (top, az135). Reads as a deer body plan from every view: long slim legs with knee/hock, deep chest, upright thick maned neck, long head. The neck is kept as the sheet's maned mass (painted dark in s3); the poll dome is broken by the stage-3 ears + antlers. Lock (r07, with orbit).
- r07: LOCKED, 1126 tris, edge hash 6d2d546c...; orbit run. IoU vs blueprint .72/.66/.75 (blueprint carries antlers, mane spread, staggered legs).

## Stage 2
- r01: Critique: the face is a 0.10 m blade (az000) with no eye. Fix: head x widened 30% (10% at the nose), eye socket inset (30%, 8 mm) at the reference eye. Result: PASS, 1138 tris, IoU .963; head wider, socket small.
- r02: Critique: no edge runs along any colour border (a decimated hull paints saw-tooth). Fix: 9 planar border cuts (bisect, logged loops): nose, jaw, mane front/back, bib V (front plane), belly, rump patch, shin, hoof.
- r02 result: PASS, 1458 tris, min IoU .963, slivers 1.4% (snap 18 mm; 8 mm on the thin legs and the rump, where a snap folded the rump/thigh crease: 22 hits).

## Stage 3
- r01: paint by the s2 cuts with colour_from_sheet's clusters mapped to the brief roles; pieces: almond eye lenses, cupped leaf ears (cream inside a rim), antlers (beam + brow, bez, trez, 2 crown tines, 5-sided, rooted in the poll, dark base), 8 large mane locks per side on the mane border + throat, a short tail wedge.
- r01 result: FAIL float 2 (the ears' root ring stood 1-2 mm off the skull), slivers 3.3% (the long 3-ring tines and tips: 6-deg needles). Reads as a stag at last (antlers, ears, dark mane, cream rump/belly/jaw). Fix: tines/beam built by taper(): rings spaced <= 7.5 edges, a blunt 4-radius tip; ear root sunk into the skull.
- r02: PASS, 2544 tris, 7 colours (slivers fixed: rings <= 4.5 edges apart; a floating tine fixed by starting each tine 12 mm inside the beam).
- r02 critique: the mane does not read (hero, az090): the neck is painted body-brown (the mane rule needed both cut regions, which only overlap in a strip) and the 8 locks stand off the neck as dark shard cards (the wolf's lost-review look). Fix: mane = behind the front plane and above the lower plane on the whole neck; locks cut to 5 per side, broad (0.12) and lying on the skin as a jagged fringe on the border.
- r03: PASS, 2460 tris. The dark maned neck with a jagged fringe now reads as the reference (az090, hero). Critique: the antlers are needle-thin grey spikes (hero, az000) where the reference's are chunky tan tines. Fix: beam 0.032->0.011 m radius (was .024->.008), tines 35% thicker with blunter tips, a darker burr only at the base.
- r04: PASS, 2280 tris, 7 colours. Antlers read as chunky tan tines (az090, hero). Stage 3 done.

## Stage 4
- r01: k3's rig on joints read off this base (spine/neck/head, ear, tail, 4-bone legs, roll auto), every piece bound with the body's weights; idle graze + ear flick, diagonal walk (swing 12 deg), head-down antler charge.
- r01 result: all gates PASS; WARN clip 14 tris (0.52% area): the throat lock under the jaw (pink, az000) meets the jaw when the neck pitches down to graze/charge. Neck bends without collapse in all posed frames.
- r02: Fix: the throat lock rooted 6 cm lower (z 0.84), off the jaw's path. Final round with orbit.
- r02 result: PASS, clip still 14 tris: per object it is the ears (8) and the skin under them (6), not the lock: the ear flick (24 deg) swings the leaf root through the skull.
- r03: Fix: ear flick halved (12 / -5 / 9 deg). Final round with orbit.
- r03 result: PASS, clip unchanged (14 tris, 0.52% area: ears + the skin under them), so it is the neck/head pitch bending the skin round the ear roots, not the flick. Left as is (stage-4 cap; low vs giant 8.4%, goblin 4.2%).
- --review and --compare run (review/, side_by_side.jpg).

## Totals
- triangles: stage 1 1126 (lock 6d2d546c...), stage 2 1458, stage 3/4 2280; 7 colours (body, mane, cream, antler, antler burr, hoof, eye).
- rounds: s1 7, s2 2, s3 4, s4 3.
- vs abc/k3/stag: carved deep-chested body with real rump/thigh/shoulder mass, a dark maned neck with a jagged fringe (reads like the sheet), cream rump patch, belly band, jaw and bib V on clean edge-path borders, cupped leaf ears, branching antlers with a dark burr. Weaker: the belly band paints the fore-leg tops cream (az000 triangles), eyes small, the lower legs dark from the knee read heavy, antlers a little thin vs k3's.
- restored to the solo carve + detail version (orchestrator, 2026-10-05): both blind reviewers preferred it over the team pass. The team version is commit 923ec33.
