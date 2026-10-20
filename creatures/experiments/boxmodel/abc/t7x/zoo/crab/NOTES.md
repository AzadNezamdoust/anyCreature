# crab (t7x zoo) — NOTES

t7's technique adapted to a crab. The spine loft of 6-vertex half rings (9 rings, rear edge to front edge) IS the carapace: a flat dome with a sharp rim at ring vertex 2. Four walking legs per side grow from 2-face regions under the rim (one span each; neighbouring roots share an edge). The claw grows from its own span at the front corner, with one empty span between it and leg 1. The eye stalks are 1-face extrusions of the front-edge top face. Every limb is a hexagon tube swept along a path with a parallel-transported frame, so it does not twist.

Stage 0: reference/sheet.png traced with kit/refs.py (height 0.30 m). The sheet's side tile is a 3/4 view, and its top view has a different pose (top width 0.64x the front width), so the blueprint IoU is only a loose guide.

## Stage 1
- r1: first fit. FAIL: 26 self-intersecting pairs at the rear legs, 1168 tris. Diagnosis: legs 3 and 4 head 34/60 deg back and rise over the narrow rear dome. Fix: headings 30/50 deg, first two path points lower.
- r2: FAIL: 8 pairs at leg 1. Diagnosis: the first section is only 3 cm out from the root centre, still inside the rim, so the upper wall folds under the rim. Fix: first section 4.8 cm out.
- r3: PASS, IoU 0.572/0.598/0.484. Critique: az000. The legs are pencils; the ref legs keep their thickness down to the propodus. Fix: rw 0.018/0.016/0.015/0.013 down the leg.
- r4: PASS. Critique: az090/hero. The palm is a lumpy club; the ref palm is a big round mitten. Fix: palm sections 0.054/0.05 wide, one more section.
- r5: PASS. Critique: az000. The eye stalks are flat tabs at the shell corners. Diagnosis: the F2 ring is too wide, so the root face spans x 0.06-0.12. Fix: F2 W 0.108, stalks 8.5 mm square, centred at x 0.066.
- r6: PASS. Critique: az000. The legs fall nearly straight down from the knee; the ref legs splay out to the tip. Fix: the lower leg reaches 2.4 cm further out.
- r7: PASS, IoU 0.585/0.574/0.457. The crab reads in every view.
- r8 (LOCK): 598 verts, 1192 tris, edge sha256 2a6de94038d19d62.

## Stage 2
- r1: joint rings (loop cut, pinched to 0.86) at each leg's knee and wrist and at the claw's carpus and wrist; the front plate flattened. FAIL: slivers 3.4%, at the needle leg tips.
- r2: Fix: tip rings x1.9 (blunt). PASS: 1432 tris, slivers 0, min IoU vs s1 0.975.

## Stage 3
- r1: 6 colours painted along existing loops: red shell above the rim, cream underside, orange limbs, red palm, cream fingers, dark brown lens eye with a black pupil. The movable finger was a separate piece at this round. PASS, 1592 tris.
- r2: the eye lens grows a little (r 1.35 cm) and sits on top of the stalk.

## Stage 4
- r1: rig: body; 3 bones per leg; claw arm/carpus/palm/finger plus a dactyl bone; eye stalks. Clips: idle, sideways walk (alternating tetrapods), attack (claws rise and open, strike and snap). FAIL: drift 2 shells. A rigid hinged finger always opens a gap to the palm skin.
- r2: palm and fixed finger weighted rigidly to palm. Still drift: the drift gate flags any hinged piece by design.
- r3: Fix: the movable finger becomes part of the body, a quad tube extruded in stage 2 from the palm's upper front face (logged topo op) and weighted rigidly to the dactyl bone, whose local Z is set to the claw's side axis (+Z closes). The finger piece is dropped. All gates PASS.
- r4: Critique: the attack's strike swings the palm over the face. Fix: smaller arm/carpus strike angles. All gates PASS: hit/float/zfight/drift/fold 0, slivers 0, lock OK; clip warning only (52 tris, legs crossing in the walk).

Checks (checks.py on the stage-4 GLB): orbit18_sheet.jpg shows every view reading, with no collapse or hole. Separation on the rest mesh (distal bones per limb): claw to leg 1 is 8.9 cm, legs 1-2/2-3/3-4 are 5.2/4.8/4.3 cm, claw L to R is 19.2 cm, and the movable to fixed finger gap is 1.15 cm, so PASS. side_by_side.jpg: sheet next to model.

Triangles: stage 1 1192 · stage 2 1432 · total 1544.
Weaknesses: the ref's segmented leg look is only hinted at by the joint rings. The rear shell shows cream under-rim faces from behind. The shell is a tent of planes (no dome bulge, no rim teeth). The claws sit slightly high and wide against the 3/4 side tile.

## Fix pass (reviews fable 5 / opus 3)
Merged list, shape first: (1) claws jumbled, fingers stacked, palm near the body; (2) carapace a tall ball, the sheet is a wide flat shield; (3) legs long straight spikes lifting the body, no knee rise.
- Base change, stage 1 re-locked: shell rings y x0.88, height x0.85, width x1.2 (width about 1.5x depth), F2/F3 wider (straighter front edge), ZC 0.14 -> 0.115 (body lower). Legs: shorter path, knee raised to shell-top height, foot tip down, lower segments thicker (wrist 0.013 -> 0.016), headings spread to -24/6/32/54. Claw path moved out 3.5 cm and down, palm in front of the shell; fingers thicker.
- r0: FAIL, 16 self-intersecting pairs (legs 1-2 at the knee). Fix: headings spread. r1: FAIL, 8 pairs (leg 1's first section under the wider rim). Fix: first section 5.6 cm out. r2: PASS, IoU 0.56/0.528/0.402. LOCK: 598 verts, 1192 tris, edge sha256 5e5923f7adf171c9.
- Stage 3 paint rule rewritten by nearest claw section: palm red, both fingers cream (no more cream palm front / third tine).
- checks_blender.py: finger-gap y thresholds moved with the claw.
- Stage 4: all gates PASS (hit/float/zfight/drift/fold 0, slivers 1.0%, lock OK); clip warning 86 tris (legs crossing in the walk). Separation PASS: finger gap 1.7 cm, claw-leg1 7.3 cm, legs 6.2/5.7/5.0 cm.
- Triangles: stage 1 1192, total 1544.
Not fixed: the near claw still sits close to the shell in the tight hero camera; no rim teeth; legs keep joint rings only (no hard segment breaks).

## Fix pass 2 (reviews fable 6 / opus 8)
Merged list, sheet as referee: (1) claws held high like raised gloves (both reviews); (2) legs uniform stilts, knee too high (fable shorter/lower knee, opus taper; both match the sheet); (3) carapace: fable flatter, opus front rim. Skipped: the sheet's dome is as tall as the model's and the rim is already a sharp ring edge.
- Base change, stage 1 re-locked: claw sections from the carpus on lowered 3.5 cm and moved 3.2 cm forward; legs x0.94 length, knee 0.165 -> 0.148, taper from the wrist to a 4 mm tip. r9 PASS first try, IoU 0.46/0.535/0.406. LOCK: 598 verts, 1192 tris, edge sha256 6ed907c33d31fe70.
- checks_blender.py: finger-gap y thresholds moved with the claw (-0.215/-0.206 -> -0.247/-0.238).
- Stage 4: all gates PASS (hit/float/drift/fold 0, slivers 1.0%, lock OK); clip warning 40 tris. Separation PASS: finger gap 1.7 cm, claw-leg1 7.8 cm, legs 6.1/5.7/5.0 cm.
- Triangles: stage 1 1192, total 1544.
Not fixed: shell outline stays a rounded box from the top (sheet is a pointed-rear shield); legs keep joint rings only.

## Density pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- Shell loft: half rings 6 -> 10 vertices (two dome-shoulder vertices, so the dome is rounded instead of a tent; the sharp rim is now vertex 4; the under-rim root band is vertices 4-7). Stations 9 -> 12: RT (the pointed rear of the sheet's shield), R0a (rear taper), F0a (front shoulder). R0/R0a/R1 narrowed so the top view tapers to the sheet's point.
- Limbs: octagon tubes (was hexagon) grown from the 3-face under-rim region. Legs 7 -> 12 stations, re-fitted to the sheet: thick merus arching to the knee, carpus falling, propodus, tapered dactyl (KNEE 3, WRIST 6). Claw 13 -> 20 sections: merus x2, merus-carpus bend, carpus, wrist flare, three more round the palm (bulge 0.056, the round mitten).
- r10/r11 FAIL: 44/40 self-intersecting pairs at leg 4's knee (inner wall folded where the knee stations sat 1 cm apart). r13: knee stations spaced 1.6 cm, knee rh 0.014, leg 4 heading 55 -> PASS. r14: pointed rear. r16 LOCK: 1320 verts, 2636 tris, edge sha256 6e277fa8692ccc2a, IoU 0.465/0.525/0.397 (was 0.46/0.535/0.406).
- Stage 2 follows: knee/wrist and carpus/wrist joint rings on the octagon rings, tip blunting on all 8 tip vertices, dactyl from the palm-front top face (section 15), eye stalks from the dome-shoulder face (ring vertices 2-3). Details (lens eye, dactyl, stalks) unchanged. Budgets: stage1_tris 1000-4500, total 2500-6000.
- Stage 4 r7: all gates PASS (hit/float/zfight/drift/fold 0, slivers 0.7%, lock OK); clip warning 28 tris. Separation PASS (claw-leg1 8.7 cm, legs 5.8/5.4/5.2, finger gap 1.75 cm).
- Triangles: 1544 -> 3068 (body mesh 3020, eye 48); the whole increase is in the body loft. stage4, orbit18, side_by_side, before_after3 re-rendered.
