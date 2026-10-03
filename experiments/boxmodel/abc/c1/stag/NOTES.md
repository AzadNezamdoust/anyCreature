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

## Team repair pass (ad_notes_team.md, Fable 6.5/10 FIX); R0 = 8
- r08 (s4 baseline): all gates PASS, clip WARN 14 tris (0.52%), slivers 0.9%, 2280 tris.
- r09: Critique (must-fix 1): cream belly paints both foreleg tops (az000, front limb close-up). Diagnosis: the belly cut's region spans the foreleg zone (y -0.30..-0.05), so the leg tops below the plane go cream. Fix: belly cream behind y -0.07 or between the legs (x < 0.04) only; stage-2 front-plane cuts `manev` (mane V, point z 0.74), `chestlo`/`chesthi` (a cream diamond 0.10 wide, z 0.60-0.74 under the point). Result: PASS, 2352 tris; az000 forelegs brown to the knee, one cream chest diamond. The V is still hidden by the locks (item 3).
- r10: Critique (must-fix 2): the eye is a slit (head close-up, az000). Diagnosis: lens 0.044 x 0.016 m almond with a 0.75-scaled frustum top. Fix: round-almond dome 0.032 x 0.030 m, 3 rings (socket -3 mm, +7 mm, crown +12 mm = ~4 mm proud of the face). Result: PASS, float 0, z-fight 0; two dark eyes read in az000, almond the size of the nostril block in the close-up.
- r11: Critique (must-fix 3): locks stand off as cards (hero plate, az000 vest bars, back34 throat shard). Diagnosis: straight shingles hang plumb while the shoulder falls away under the neck; the throat lock hangs free. Fix: `hug_lock`: root, shoulder ring and tip projected onto the skin (find_nearest) along a tangent direction; 3 locks per side; throat lock dropped. Result: PASS, plates still stood off across their width (close-up wire).
- r12: Fix: each section edge projected on its own (the plate bends round the neck). Result: PASS, 2332 tris; hero plate gone, az000 mane is a dark V over the cream diamond (the V paint from r09). Clip WARN 20 tris (mane 6, ears 8, body 6).
- r13 (s3 check): lock vertices max 15.6 mm off the skin (5 verts over 15 mm).
- r14: Critique (must-fix 4): antlers read as a rake (az000 spread ~2.2 head widths, tines near-horizontal, lower beam dark). Fix: beam x pulled in about the root (x 0.72), tines pitched 25 deg toward vertical and 20% shorter, beam base radius 0.032 -> 0.040, dark burr only below z 1.32 (bottom 10% of the beam). Result: PASS, 2212 tris, slivers 1.7%; az000 tines up-and-out, spread ~1.65 head widths; hero tan antlers with a small burr.
- r15: Critique (must-fix 5): the ears stand out sideways like wings (az000, hero). Fix: ear pitched up 32 deg, yawed 10 deg forward, 15% shorter. Result: PASS, but the ear tip runs through the (now thicker, narrower) beam (head close-up).
- r16: Diagnosis: a forward yaw crosses the beam axis (clearance search: forward yaw < 8 mm). Fix: ear up 28 deg, yawed 15 deg BACK, root 3 cm back (still sunk); clearance ~14 mm. Result: PASS; ear tips above the roots, inside the antler spread, behind the beams (az000 they sit close to the antler base, as the reference). Clip WARN 22 tris (ears 10, body 6, mane 6): the ear bone still pointed along the old ear.
- r17: Fix: ear bone joints moved onto the raised ear. Result: clip unchanged (22).
- r18: Fix tried: ears bound rigidly to the head bone. Result: clip unchanged (ears 10), the flick lost: reverted.
- r19: Diagnosis: mane clip 6 = lock inner faces 2 mm over the skin dip under it when the neck pitches. Fix: lock thinner (18 mm), shoulder ring 11 mm and tip 8 mm over the skin (outer face max 16.4 mm). Result: mane clip 2, total 18.
- r20: Diagnosis: ear clip = the blade's lower section grazing the skull as the skin slides round the sunk root. Fix: ear root 8 mm higher (still sunk: float 0). Result: PASS; ears clip 0, total clip 8 tris (0.38%; was 14 / 0.52% before the pass).
- r21: Should-fix (lower legs heavy): shin border z 0.31 -> 0.26. Result: FAIL slivers 2.1% (the cut 8 mm from leg rings).
- r22: Fix: shin cut snap 8 -> 14 mm. Result: PASS, slivers 1.7%; the dark cannon is the lower ~45% of the leg below the knee, hoof black.
- r23 (with orbit): Should-fix: tail 20% longer with a slight hang. PASS; packet check: the burr (z < 1.32) sat inside the skull, no dark burr visible.
- r24 (final, with orbit): Fix: burr line z 1.35 (the first ~3 cm of beam above the skull). All gates PASS: hit 0, float 0, z-fight 0, slivers 1.7%, flips 0%/0%, drift 0, lock PASS, min s2 IoU .963, clip WARN 8 tris (0.38%), glbcheck OK, 2140 tris. --review and --compare rebuilt.
- Must-fix: 1 done; 2 done; 3 done (3 skin-hugging locks per side, outer face max 16.4 mm; the V's point is shallow: the fringe locks carry the jag); 4 done (spread ~1.65 head widths by the AD's measure, burr ~15% of the beam so it shows above the skull); 5 done with one change: yawed 15 deg BACK not 10 deg forward (forward runs the ear through the thicker beam), so in az000 the ears sit behind the antler bases.
- Should-fix done: lower-leg border down (z 0.26), tail. Not done: croup rounding, walk-cycle evening.
- Rounds this pass: r08-r24 (17).

## Team repair, second pass (verify_team.json: items 3 and 4 PARTLY); R0 = 25
- r25: Critique (item 4): az000 spread ~1.9 head widths, tines thin. Fix: ANT_SPREAD 0.72 -> 0.50, tine radius x1.5 / tip 9 mm. Result: PASS, spread ~1.48, but beams and tines bunch into two upright spikes (az000); slivers 1.9%.
- r26: Diagnosis: a linear pull-in makes a narrow V. Fix: lyre beam: x swings out early to ANT_XMAX 0.18 (quadratic ease), then rises; tine x scale 0.6. Result: FAIL slivers 2.1% (antlers 24); spread ~1.68.
- r27: Fix: ANT_XMAX 0.165, beam rings closer (seg_k 3.5). Result: PASS, slivers 1.9% (antlers 20: the tines' last ring gap).
- r28: Fix: tine rings closer (seg_k 3.2). Result: PASS, slivers 0.9% (antlers 0), 2160 tris; az000 spread ~1.57 head widths, chunky tan tines up-and-in on a lyre beam (hero).
- r29: Critique (item 3): az000 mane is a trapezoid with a shallow notch. Diagnosis: the `manev` plane has slope 0.6 and only front-facing faces use it; the front lock sits on the side. Fix: `manev` slope 1.5 (point z 0.74 -> neck edge at z 0.98), used by every face ahead of y -0.33; front lock moved onto the V's arm, hanging toward the point. Result: FAIL 3 open edges (the cut's snap pushed a near-seam vertex across x = 0).
- r30: Fix: the snap skips a vertex it would move within 4 mm of the seam. Result: PASS; the V is there but the shoulder locks (tips at z ~0.76) keep the mane's corners low and wide; clip 12.
- r31: Fix: V rule/cut from y -0.28; the two shoulder locks shorter (0.10) and swept back, rooted higher. Result: PASS; az000: a dark V tapering from the neck to a point at mid-chest over the cream diamond, small jags at the shoulder; clip 6 (mane 0).
- r32 (final, with orbit): all gates PASS: hit 0, float 0, z-fight 0, slivers 1.0%, flips 0%/0%, drift 0, lock PASS, min s2 IoU .963, clip WARN 6 tris (0.36%), glbcheck OK, 2164 tris. --review and --compare rebuilt.
- Packet check: item 3 done (az000 tapered V, hero no stand-off plate: lock outer face max 16.4 mm, 3_tech no blue); item 4 done (az000 spread ~1.55 head widths, tines 1.5x thicker). Items 1, 2, 5 unchanged (ear tips above the roots, inside the spread; float 0).
