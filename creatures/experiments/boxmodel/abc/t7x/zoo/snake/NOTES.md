# snake (python, t7x zoo) — NOTES

Technique: base wolf's t7r loft adapted for a body with no legs. One spine loft of 6-vertex half rings (64 rings, tail tip -> nose) is the whole body. Head rings use a flat-crown profile and body rings a round-back, flat-belly profile. There are no limb or ear extrusions. Stage 2 adds the eye socket and a lip/belly loop. Stage 3 adds the lens eye, the forked tongue and colour painted along loops. Stage 4 adds the rig and the idle/move/attack clips.

Stage 0: reference/ from sheet_4.png via kit/refs.py (side height 0.36 m, length 3.05 m). The sheet's views do not agree with each other: the side is nearly straight, the top is an S-curve and the front is a 3/4 coil. refs.py assumes a bilaterally symmetric plan, so it folds the S-curve onto itself and the traced front/top outlines are meaningless (blueprint IoU front/top ~0.17/0.09). Only the side outline is a valid stage-1 target. Unsymmetrised top and side masks were saved to reference/top_mask.npz and side_mask.npz for the posed check.

Pose: the kit's base is a mirrored half (gate "s1 mirrored"), and a plan-view S-curve cannot be mirrored. So stages 1-3 are built straight, matching the side view. At the start of stage 4 the mirror is applied and the finished snake is bent along the S-curve centreline traced from top.png (deterministic warp: straight y -> arc length, x -> curve normal, z kept). The rig is then built and skinned in that pose.

## Stage 1
- r1: first fit of the section table off side.png. Gates PASS, 1276 tris, side IoU 0.751. Critique: az090 overlay — the ref's fore body arches up (top z 0.27, belly lifted 5-6 cm at y -0.4..-0.1); ours lies flat at 0.19. Diagnosis: BKEY flat from -0.6 to 0. Fix: arch keys read off the ref top/bottom edges.
- r2: Result: better, side IoU 0.856. Head wedge, neck dip and tail taper read. Fix: lock.
- r3 (LOCK): 640 verts, 1276 tris, edge sha256 93769f35ab355bf1, side IoU 0.856.

## Stage 2
- r1: crown and cheek flattened into planes, brow ledge, slanted snout pad, tail tip ring x1.6 (no needles). Logged: eye-socket inset (H2-H3 upper-side face, 6 mm in) and one longitudinal loop through the lower-flank faces from nose to tail tip (the mouth line on the head, the belly-band border on the body). Gates PASS: 1548 tris, min IoU vs s1 0.994, slivers 0.

## Stage 3
- r1: 5 colours (tan, brown blotches, cream belly band and lips, amber eye, black pupil/tongue), a small amber lens eye (r 1.2 cm), and a mirrored forked tongue rooted in the snout. Gates PASS, 1652 tris. Critique: hero/top — the blotches read as a checkerboard (4 brown spans in 8). Fix: saddles on 2 of every 6 spans, side blotches offset by 3, palette lifted a step.
- r2: Result: better — tan ground with separate brown saddles and staggered side blotches, cream belly band on the loop. Gates PASS.

## Stage 4
- r1: bent into the sheet's S-curve (plan centreline 3.19 m vs straight 3.02 m, stretched to fit). Rig: a 14-bone spine chain on the bent centreline (root mid-body, forward to the head, back to the tail tip), roll Z-up. Bone-heat skin; eye and tongue bound to the head. Clips: idle 48 (breathing, head lift/turn, tail-tip sway), move 24 (lateral undulation wave), attack 32 (rear into an S, then strike forward). All gates PASS: hit/float/zfight 0, slivers 12 = 0.7%, posed fold-overs 0, drift 0, final lock OK, every vertex weighted.
- Posed checks (stage4/posed_checks.json): plan IoU vs top.png 0.811. Side IoU vs side.png is 0.666, because the bent snake is shorter in side projection than the sheet's straight side view. Self-contact: no two body parts more than 0.6 m apart along the spine come within 8 cm, so nothing is fused (no legs; the tail does not touch the body). PASS.
- orbit18_sheet.jpg (checks.py/checks_blender.py on the stage-4 GLB): all 18 views read, no collapse or hole. side_by_side.jpg: the sheet's side/top/front/rear next to the model's.

Triangles: stage 1 1,276 · stage 2 1,548 · total 1,652.
Weaknesses: the blotches are rectangular span blocks, not the ref's rounded saddles; the sheet's front/rear 3/4 coil is not modelled (the S-curve follows the top view); the eye socket reads boxy in the head close-up; the head is narrower than the ref's broad triangular plan.

## Fix pass 1 (merged fable + opus reviews)
- Fix list (shape first): head barely wider than the neck; body a uniform cord (no thin neck, no thick mid body); tail taper too abrupt; head not raised enough. Not taken: extra lateral S-bends (the sheet's top view has the one S-curve the model already follows).
- Base change, stage 1 re-locked (old lock kept in before/): head keys widened to 1.6x the neck (W 0.116 vs 0.058), flat crown kept, blunt snout (nose ring W 0.028 -> 0.042), head raised 3 cm; neck W 0.058-0.064; mid body W 0.085 -> 0.104 with a slightly higher back; tail tapers in width and height from y 0.26 (~60% of length) to the tip. Tongue moved up 3 cm with the head. Same topology: 640 verts, 1276 tris, edge sha256 29044465541efa6c; side IoU 0.78 (was 0.856, thinner tail than the traced outline).
- Stage 4 r2: all gates PASS, 1652 tris, posed plan IoU 0.848 (was 0.811), self gap > 8 cm (nothing fused). Orbit18 and side_by_side re-rendered, all 18 views in colour. before_after.jpg: hero before | after.
- Not fixed: rectangular blotches (colour, minor); front/rear 3/4 coil of the sheet.

## Fix pass 2 (merged review2 fable + opus, sheet as referee)
- Fix list (shape first): body reads as a flat ribbon / boxy section; head a raised square box; tail ends in needle rings; square-tile pattern. Not taken: extra vertical S-bends (the sheet's side view is nearly straight with only the raised head/neck, which the model has).
- Base change, stage 1 re-locked (pass-1 lock kept in before2/): BODY profile side vertex (1, 0.12) -> (1, 0.0), belly (0.95, -0.55) -> (0.85, -0.6) for a rounder section; mid-body top +3 cm (y -0.54..0.50; fable asked +6 cm, halved to stay at the sheet's round section); HEAD crown edge (0.78, 0.96) -> (0.7, 0.85); head a wedge (H1-H5 W -12..15 %, still 1.6x the neck) and 2 cm lower, tongue follows; last two tail rings cut (tail ends y 1.48), tip ring closed to 2 cm. 620 verts, 1236 tris, edge sha256 e3b43b373f3d305f, side IoU 0.76.
- Stage 3: diamond saddles (wide on the crown row, a point on the flank, side blotches staggered half a period).
- Stage 4: all gates PASS, 1604 tris, lock assert PASS, every vertex weighted; posed plan IoU 0.84, side IoU 0.60 (posed bend shortens the side projection), self gap > 8 cm (nothing fused).
- checks_blender.py now frames each view on the model's projected extent (renders were tiny on the bounding sphere). Orbit18 (18 views, colour) and side_by_side (sheet views | model) re-rendered; before_after2.jpg: hero before | after.
- Not fixed: at 6-vertex rings the diamonds read as bars on the flank; the sheet's front/rear 3/4 coil.

## Density pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- Loft half rings 6 -> 8 vertices: body gains a back and a shoulder vertex (round back, belly still one flat face); head gains a brow vertex and a second cheek vertex (crown plane = vertices 0-1, cheek plane = 3-4). Stations 62 -> 92: body spacing 3.0 / 3.2 / 3.6 cm (densest over the neck arch and belly drop), finer tail taper, head/neck inserts H0a, H1a, H3a, H4a, H5a, N1a, N2a, N3a (H2-H3 kept adjacent for the socket).
- Re-fit: keys exact; stations between keys on a monotone cubic through the keys (was linear), then pulled half way to the traced side outline, max 8 mm (keeps the raised back and thin tail from the reviews).
- Stage 2 follows: crown/cheek flats take the new head stations, eye socket on the ring-vertex 2-3 face between H2 and H3, chin pad on vertices 6-7, lip/belly loop on the SIDE-LOWER face. Details (eye, tongue) unchanged. Budgets: stage1_tris 400-3200, total 1200-6000.
- Stage 1 re-locked (pass-2 lock kept in before3/): gates PASS, 1302 verts, 2600 tris, edge sha256 c5457e69ce58ac4a, side IoU 0.798 (was 0.76).
- Stage 4 r3: all gates PASS, 3092 tris (was 1604): body 2988 (was 1500), details 104 (unchanged); 100% of the increase in the body loft. Posed plan IoU 0.839 (was 0.84), side 0.621 (was 0.601), self gap > 8 cm (nothing fused). stage4, orbit18, side_by_side, before_after3 re-rendered.

## Mix pass 4 (review_poly2x: MIX - restore the before3 neck/head junction, keep the denser body curve)
- Neck inserts N1a, N2a, N3a cut; every ring in front of y -0.84 (head, neck, fore neck) back to linear between the keys with no trace pull (before3 form). The cubic + trace pull had pinched and wobbled the neck behind the head. Body stations, 8-vertex rings and head inserts H0a-H5a (on the linear key lines, so the crown/cheek planes stay flat) kept.
- Stage 1 re-locked (pass-3 lock and renders kept in pass3/): gates PASS, 1260 verts, 2516 tris, edge sha256 437f1565012275da, side IoU 0.794.
- Stage 4 r4: all gates PASS, 2996 tris (2x pass 3092), lock assert PASS, every vertex weighted; posed plan IoU 0.84, side 0.619, self gap > 8 cm (nothing fused). Neck reads smooth again, head and eye as in before3. stage4, orbit18, side_by_side re-rendered; before_after4.jpg: before3 | 2x pass | now.

## Fix pass 9 (owner: keep the 2x mesh, fix the problems inside it)
- Pass 4 had cut the neck inserts (density revert). Restored N1a, N2a, N3a (y -1.115, -1.04, -0.96) on the linear key lines in front of y -0.84, so the neck keeps the pass-3 density without the cubic + trace pull that pinched and wobbled it behind the head. Head planes, eye socket and lens (r 1.2 cm) unchanged from before3.
- Pattern: saddles were span blocks that broke into squares at the denser rows; now one continuous diamond per saddle (half width falls with height) plus a staggered side blotch, so the edge steps diagonally along the rings.
- Stage 1 re-locked (pass-4 lock, script and renders in before9/): gates PASS, 1302 verts, 2600 tris (pass 3 level), edge sha256 5e4de9c36c3515ec, side IoU 0.794.
- Stage 4: all gates PASS, lock assert PASS, every vertex weighted, glbcheck OK; posed plan IoU 0.84, side 0.619, self gap > 8 cm (nothing fused). stage4, orbit18_sheet, side_by_side re-rendered; fix9.jpg: hero before9 | after plus neck close-ups.

## Border pass (night 2026-10-23, s4 r05) - owner pick
- kit/smooth_borders(body, k=k, iters=8): 24 despeckled, 40 cuts, 149 relaxed; stair corners 99 -> 15, 3-to-1 62 -> 0.
- Blind A/B: after wins both orders, but the pattern changes (small side spots removed by despeckle) -> taste call, champion kept.
  Candidate: before_borders/snake_r05_borders_candidate.glb / .py, border_before_after_CANDIDATE.jpg.
