# bear (t7 hand box-model) - NOTES

The technique comes from wolf_base (t7r line, no linear subdivision). One spine loft of 6-vertex half rings runs from the tail stub to the nose. The legs are 2-face lower-flank regions extruded as horizontal hexagons, and the ears are 1-face extrusions. Stage 0: blueprint.json was traced from reference/sheet.png with kit/refs.py (height 1.2 m, traced length 1.866 m). Each section is set by its top and bottom seam points read off the side view, with W from the front and top views.

## Stage 1
- r1: first fit (18 sections, legs from the C0-C1 and R1-R2 spans). Gates PASS, 628 tris, IoU side/front/top 0.876/0.892/0.869. Critique: az000. The flanks drop as vertical slabs, but the ref barrel is widest at z 0.69 (half-width 0.38) and narrows to 0.25 at the back. Diagnosis: the BODY profile's widest vertex sits at +0.15 h and W is only 0.33. Fix: BODY widest vertex moved to -0.05 h, top-outer vertex to 0.68 W, and W set to 0.34-0.355 from R2 to C0.
- r2: Result: slightly better (front 0.899). Critique: hero/az090. The legs read as stilts that pinch at the forearm and shin, while the ref legs are thick pillars. Diagnosis: the forearm and wrist ry is 0.12/0.115 and the shin and hock ry is 0.14/0.13. Fix: forearm 0.125/0.14, wrist 0.12/0.13, shin 0.13/0.16, hock 0.125/0.14.
- r3: Result: better (IoU 0.885/0.904/0.871). Critique: az000/top. The ears are square blocks, but the ref ears are round. Diagnosis: a single section goes straight to a small tip. Fix: three ear sections (base, wide middle, small top).
- r4: Result: better. The ears now read rounded; 644 tris, IoU 0.885/0.905/0.871.
- r5 (LOCK): 324 verts, 644 tris, edge sha256 76036f1505c429ae.

## Stage 2
- r1: Plan: joint rings at the elbow, knee, wrist, hock, neck-skull, lower neck, chest and belly; an eye socket inset into the brow face (H1-H2) and pushed 12 mm in; the brow corner moved out; a flat muzzle side and bridge; the nose pad slanted. Result: FAIL, because the inset was unlogged.
- r2: Result: FAIL, because the loop cuts were also outside topo blocks. Fix: each op wrapped in k.topo.
- r3: Result: gates PASS, 836 tris, min IoU vs s1 0.998.

## Stage 3
- r1: script encoding error (no build).
- r2: Plan: 6 colours (brown fur, dark brown legs/belly/ears below z 0.5, tan muzzle, black nose, dark lens eye with a pupil, cream claws). Pieces: 5 claws per paw, 3 cheek-ruff clumps per side and 3 shoulder-hump clumps per side. Result: gates PASS, 1524 tris. Critique: hero. The hump and cheek clumps stand off as scattered shards, and the whole bear reads near black-brown next to the ref's warm mid brown.
- r3: Diagnosis: the clumps are too large and laid sideways, and PAL is too dark. Fix: the shoulder clumps were dropped and the cheek clumps made smaller and laid back. Palette lifted to fur #9c6842, dark #5e3b27, muzzle #d2ab80. The total budget floor was set to 1300. Result: gates PASS, 1404 tris.

## Stage 4
- r1: Rig with 13 bones plus .R mirrors. Clips: idle 48 (breathing, head turn, ear flick), move 33 (diagonal walk), attack 32 (rear back, then a forepaw swipe and head lunge). Result: all gates PASS.

Checks: orbit18_sheet.jpg (18 views) shows every view reading, with no hole or collapse. Separation on the rest mesh: tail to hind legs 0.48 m, fore L-R 0.12 m, hind L-R 0.12 m, so the parts are not fused. side_by_side.jpg built.

Triangles: stage 1 644, stage 2 836, total 1404.
Weaknesses: the total is below the 1.5k target. The hind legs are one symmetric pair, while the ref shows a staggered pair. The back hump is mild, and the cheek ruff reads only as small facets.

## Fix pass 1 (zoo reviews, Fable + Opus)
Merged list, shape first: (1) shoulder hump weak (Opus) -> M1-C2 tops raised, C1 top now ~22 % above the hip ring, N0 top lowered for a neck break; (2) head small, sinks into chest (both) -> head sections, ears and head joints scaled 1.10 about the neck-skull pivot and moved 3 cm forward; muzzle top tipped down (H3/H4 tops -13/-20 mm, matches ref bridge); colour rule maps back through the head transform; (3) claws: reviews disagree (3 shorter vs 4 longer) -> ref shows 4-5 visible claws: 4 per paw, 1.4x thicker, 1.3x longer.
Base change: stage 1 re-locked as r6 (old lock kept in before/), 644 tris, IoU 0.865/0.882/0.847. Stage 4 r2: all gates PASS, lock assert PASS, glbcheck OK, separation PASS (tail-hind 0.48 m, fore/hind L-R 0.12 m). Total 1324 tris.
Not fixed: leg-root blend / rounded inner corners in bottom view (Fable 1); harness advises head merged at az000 (front view, head over chest).

## Fix pass 2 (round-2 reviews, Fable + Opus)
Merged list, shape first, concept sheet as referee: (1) body narrow at az0 (Opus asks +35 %): sheet front half-width peaks at 0.38 m, so torso W raised to 0.37-0.38 (R2-C0), C1 0.36, C2 0.30, N0 0.25 (about +7-12 %, not +35 %, which overshot the sheet in trial r7: front IoU 0.77); legs moved out 0.20 -> 0.22 m; (2) shoulder hump (both): C0/C1 tops +45 mm, M1/M0 small rise, R1/R2 tops -20/-30 mm so the back slopes to the rump; rump rounder: R0 W 0.17 -> 0.22, R1 0.29 -> 0.33; (3) head under-scaled (both): H0-H1 W about +8-10 %, muzzle tip blunted (H2-H4 W +10-24 %), ears moved out with the skull.
Skipped: Fable's hind ring narrowing and leg wedge (sheet rear shows the hind legs wide apart, pillar-like).
Base change: stage 1 re-locked as r8 (r6 lock kept in before2/), 644 tris, IoU 0.853/0.859/0.833. Stage 4 r3: all gates PASS, lock assert PASS, glbcheck OK, separation PASS (tail-hind 0.49 m, fore/hind L-R 0.16 m). Total 1324 tris. orbit18_sheet.jpg, side_by_side.jpg and before_after2.jpg rebuilt.
Not fixed: harness advises head merged at az000 and hidden at az180 (true to the sheet's front and rear); 5 posed triangles clip (QA warn).

## Poly pass 3 (denser main mesh)
Goal: about 2x triangles, mostly in the body loft, re-fitted to the traced sheet (no subdivision, no remesh).
Base change: loft 18 -> 27 stations (added at the rump, hind root, belly, shoulder hump, neck, skull and muzzle), half rings 6 -> 10 vertices with rounder profiles (narrower barrel top, as the sheet front view). All stations re-read from blueprint.json in world coordinates (hump top now on the sheet's 1.20 m, not above it; waist W 0.305, hips/shoulders 0.345/0.385). Legs: roots are 3x3-face flank regions, 12-sided rings, 7 sections each, thicker in side view (sheet pillars). Ears re-seated on the new skull face.
Stage 1 re-locked as r9 (r8 lock kept in before3/): 1688 tris, edge sha256 c845230f9d13da41, IoU side/front/top 0.926/0.943/0.874 (r8: 0.853/0.859/0.833). Two trial builds failed first (bmesh refs after extrude; hind root self-intersection fixed by lifting the hind belly seam).
Stage 2: the same 8 joint rings and the eye socket on the new topology; 2040 tris, min IoU vs s1 0.999.
Stage 3/4: details unchanged (claws, eye lens, cheek clumps re-rooted on the new surface); all gates PASS, glbcheck OK, separation PASS (tail-hind 0.49 m, fore L-R 0.12 m, hind L-R 0.14 m). Total 2528 tris (was 1324): body 836 -> 2040, details 488 -> 488, so the whole increase is in the body.
Not fixed: posed clip QA warn rose to 43 triangles; harness advises head merged at az000 and hidden at az180 (true to the sheet).

## Poly pass 3 review: MIX
Verdict (review_poly2x.md): keep the new head and legs; restore the before3 torso and hump (flat planes, a clear shoulder hump), since the 2x torso read as a ribbed barrel.
Change: the torso loft is back to the r8 stations R0, R1, R2, W0, M0, M1, C0, C1, C2, N0 and their r8 sizes. The BODY/REAR profiles are the r8 6-vertex sections with the 4 extra ring vertices placed on the old edges, so the faces stay flat. Three linear in-between stations (R1a, M1a at 0.25, C0a) lie on the old faces, so the 12-sided leg roots still have 3 spans (hind root R1 to W0, fore root M1a to C1). Head (N1 to H4), eyes, brow, ears and legs are unchanged from pass 3.
Rounds: s1 r10 failed self-intersection (fore root back edge behind the first leg ring), so M1a moved from 0.5 to 0.25 toward M1; r11 gates PASS.
Base change: stage 1 re-locked as r12 (the r9 lock and the pass-3 renders are kept in pass3/). 1544 tris, edge sha256 6db511459fe530c0, IoU side/front/top 0.897/0.881/0.860. Stage 2 1896 tris. Stage 4 r5: all gates PASS, lock assert PASS, glbcheck OK, separation PASS (tail-hind 0.49 m, fore L-R 0.12 m, hind L-R 0.14 m). Total 2384 tris. orbit18_sheet.jpg, side_by_side.jpg and before_after4.jpg (before3 | 2x pass | now) rebuilt.
Not fixed: 37 posed triangles clip (QA warn); harness advises head merged at az000 and hidden at az180 (true to the sheet).

## Fix pass 9 (dense mesh kept, problems fixed inside it)
Owner: the MIX pass made the bear low poly again. This pass restores the 2x station count and fixes the review's WORSE parts within it.
Change: the torso is 17 stations again (the pass-3 count), but each is sampled on a Catmull-Rom curve through the before3 (r8) sections as keys (R0, R1, R2, W0, M0, M1, C0, C1, C2, N0). Ring sizes now change smoothly, so there are no rib bands. Collinear keys (W0 to M1) give co-planar stations, so the flank keeps its big flat planes, and the shoulder hump and rump bend take the extra rings. The 10-vertex BODY/REAR rings keep the r8 6-plane cross-section, so the long facets stay crisp. Head, eye, brow, ears, legs, claws and cheek clumps are unchanged from pass 3.
Leg hole (owner crop: a white gap at the fore-leg root in the hero view): the brisket keys are deeper (M1/C0/C1 bottoms 0.34/0.365/0.39, C2 0.58 -> 0.48), and an extra station (C2a) sits between C2 and N0. The chest now closes the see-through gap in front of the fore leg.
Rounds: s1 r13 failed self-intersection (C0 bottom 0.335 cut the fore-root inner edge), r14 PASS; r16/r17 failed (a C1a station behind the moved-forward fore-root front ring folded), so C1a was dropped for C2a; r18 PASS. A stage-2 brisket keel failed (the belly midline crossed the fore-root inner walls), and so did trials that moved the fore root forward (5.55-7.5, 5.25-7.3, 5.25-7.15), so the root stays M1a..C1 (key index 5.25 to 7).
Base change: stage 1 re-locked in the stage-4 r12 run (the pass-8 r12 lock is kept in before9/): 1688 tris, edge sha256 fe20f810fe416841, IoU side/front/top 0.898/0.879/0.861. Stage 4 r12: all gates PASS, lock assert PASS, glbcheck OK, separation PASS (tail-hind 0.49 m, fore L-R 0.12 m, hind L-R 0.14 m). Total 2528 tris (was 2384). orbit18_sheet.jpg, side_by_side.jpg and fix9.jpg (before9 | after, with fore-leg root and torso close-ups) rebuilt.
Not fixed: 46 posed triangles clip (QA warn); the torso flank still shows mild vertical shading steps where the hump curve bends; harness advises head merged at az000 and hidden at az180 (true to the sheet).
