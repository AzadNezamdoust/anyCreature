# knight (t7 box model) — NOTES

Biped: one spine loft of 6-vertex half rings, crotch -> helmet crown; legs = 2-face regions of the crotch-hip span extruded down as hexagons; arms = 2-face regions of the chest side, first section is the pauldron mass. Blueprint traced from reference/sheet.png with kit/refs.py (height 1.8 m); the sheet's top view is rotated, so top IoU is not used.

## Stage 1
- r1: first fit. Gates PASS, 568 tris, IoU side/front/top 0.661/0.752/0.321. Critique: az000 — no pauldron, the arm leaves the chest flat and thin at the shoulder. Fix: first arm section raised and bigger.
- r2: Result: shoulder corner now pokes out past the ref outline (x 0.44 at z 1.37). Diagnosis: pauldron centre x 0.345 too far out, R6 yoke too narrow (ref shoulder line runs straight neck -> x 0.39). Fix: pauldron (0.31, 1.30) r 0.10; R5/R6 W 0.30/0.28.
- r3: Result: better, shoulder line matches the front outline (front 0.776). Critique: overlay side — the whole figure sits ~3 cm behind the trace; egg-shaped belly. Fix: global y shift -0.03; waist narrowed (R2/R3 W 0.23/0.225), breastplate R4 W 0.30.
- r4: Result: better, side 0.679 (rest of the side gap is cape and shield, stage-3 pieces). Lock.
- r5 (LOCK): 286 verts, 568 tris.

## Stage 2
- r1: joint rings (shoulder, elbow, wrist, hip, knee, waist, neck); visor slit = inset of the face-plate face squeezed to a slot, pushed 14 mm in. Gates PASS, 744 tris, IoU vs s1 1.0.

## Stage 3
- r1: colours along existing loops (steel, mail visor + gorget, blue cowl); pieces: tabard, cape, round shield (rim + boss), belt with buckle, sheathed sword with crossguard/grip/pommel and belt strap (sword unmirrored, left hip). Result: FAIL slivers 2.7% (thin cape/tabard rims, long scabbard spans); cowl too low on the chest.
- r2: Fix: cape/tabard thickness 3.5/2.6 cm, scabbard split into 6 rows, cowl z > 1.38. Result: PASS, slivers 0.3%, 1360 tris, 6 colours, hit/float/zfight 0.

## Stage 4
- r1: rig 11 bones + .R mirrors; idle (breath, look), move (heavy walk), attack (right gauntlet hammer blow). All gates PASS: posed fold-overs 0.37%, drift 0, glbcheck OK; warnings only (5 stretch tris, 0.49% clip in poses).

Checks: orbit18_sheet.jpg (18 views) all read; separation on rest body: legs L-R 0.24 m, each arm vs torso 0.158 m: nothing fused. side_by_side.jpg built.
Weaknesses: face is just a slot in a plain helm (no lens eye — closed helm); pauldrons are part of the arm loft, not separate plates; no knee/elbow cops; low tri count (1360) leaves the limbs blocky.

## Fix pass (reviews fable 7 / opus 6)
Merged list (shape first): helm bucket -> visor ridge + crest fin; no pauldron/knee mass -> flared plates; sword thin and scabbard into the leg; cape flat with a painted shield ring. Stage 1 untouched (lock holds, no re-lock).
- r1: pieces pauldron (4 rows, flared down over the arm), knee cop, visor ridge under the slit, crest fin (unmirrored, midline); shield rim raised 14 mm as a steel lip, boss steel; cape hem 4 cm further back; scabbard +50 % wide, 3 cm out. FAIL: belt/sword hit (wider crossguard through the belt), posed folds 0.90 %.
- r2-r4: crossguard and guard back to original, only the lower scabbard widened (+38 %), tip 1.5 cm out; cape hang back to +1 cm. Folds 0.64 % (sword bent by thigh weights).
- r5: sword bound rigid to hips (a sheathed sword hangs from the belt). All gates PASS.
- r6: pauldron too deep (a slab in side view): depth -30 %, curved over 4 rows; knee cop smaller. PASS, 1572 tris, folds within limit, hit/float/zfight 0, separation PASS.
Not fixed: cape still one flat plate (no folds); helm front not flattened (base change avoided); face is the visor slit, no lens eye (closed helm).

## Fix pass 2 (round-2 reviews, Fable 6.5 / Opus 7)
Merged list, shape first, concept sheet as referee: (1) shield a flat disc on the cape (Fable) -> board 9 cm thick standing off the cape, steel edge and rim lip, boss +33 %; Opus "remove the ring" skipped (sheet shield has a steel rim); (2) helm small for the pauldrons (Opus) -> H rings 1.12x about the rim centre, crest follows; (3) thin shins (Fable) -> LEG rings 2-3 r 1.2x; (4) sword thin (Fable) -> scabbard ~+15-20 % wide/deep, angle kept (sheet hangs it near vertical).
Skipped: Opus legs +10 % (sheet is stumpy, short-legged).
Base change: stage 1 re-locked as r6 (r5 lock kept in before2/), 568 tris, IoU side/front 0.67/0.764. Stage 4 r7: all gates PASS, lock assert PASS, glbcheck OK, separation PASS (legs L-R 0.22 m, arm-torso 0.158 m). Warnings only: 8 stretch tris, 0.56 % posed clip. orbit18_sheet.jpg, side_by_side.jpg, before_after2.jpg rebuilt.
Not fixed: cape one flat plate; face stays the visor slit (closed helm, no lens eye); harness advises az45/az135 blob.

## Poly pass 3 (owner: denser main mesh, same t7 technique)
- Spine loft: 13 -> 23 stations (new: leg-root mid, fauld flare, belly into belt, rib flare, chest fullest, shoulder round-over, cowl slope neck -> shoulder, cheek, dome shoulder, dome round-over), widths/depths re-read off the traces; half rings 6 -> 10 vertices. Limbs: root 4 profile faces x 2 spans -> 12-vertex round rings, 11 sections each (legs: thigh, knee, calf, lower calf, ankle pinch, cuff, sabaton; arms: shoulder, deltoid, upper arm, elbow, vambrace, forearm, cuff, wrist, gauntlet). Arm grows out-down from the side band (r07-r10 FAIL self-intersection: the old pauldron-mass first section folded into the armpit).
- Stage 1 re-locked (r12; r6 lock in before3/): 1880 tris, IoU side/front 0.67/0.755 (was 0.67/0.764). Budgets raised to s1 1200-3200, total 2600-6000.
- Stage 2: the 7 joint rings re-aimed at the new sections (12/10-vertex loops); visor slit in the matching face of the 10-vertex helm ring. Belt keeps its old path (FAIL r08: belt/sword hit with a 10-point path).
- Stage 4 r11: all gates PASS, lock OK, glbcheck OK, hit/float 0; stretch warning only. Separation PASS (legs 0.20 m, arm-torso 0.117 m).
- Tris 1572 -> 3036: body 744 -> 2208, details 828 unchanged (100% of the increase in the body). before3/, before_after3.jpg, orbit18_sheet.jpg, side_by_side.jpg rebuilt.

## Mix pass (review_poly2x: MIX, keep the helm, restore arms, legs, torso plates)
- Kept from poly pass 3: the 10-vertex HELM/NECK rings and stations N0, H0, H0b, H1, H2, H2b, H3, H3b, H4; visor slit on the 10-ring face.
- Restored to before3 (r6): torso stations R0-R6 (7, no 'b' stations) with the 6-vertex TORSO ring; hexagon limbs (LEG 6 / ARM 7 sections, first arm section the pauldron mass), 2-face limb roots, old joint-ring cuts (waist R2-R3).
- New: one step span R6 (6) -> N0 (10), quads + one triangle per doubled edge; the neck loop cut stays in the 10-10 span.
- Budgets back to before3 (s1 400-2600, total 1300-4500). Stage 1 re-locked r13 (r12 lock kept in pass3/, r6 in before3/): 772 tris, IoU side/front 0.668/0.764.
- Stage 4 r12: all gates PASS, lock assert PASS, glbcheck OK; warnings only (8 stretch tris, 0.56 % posed clip), same as before3. Total 1792 tris (before3 1572, pass 3 3036).
- pass3/ holds the 2x-pass script, lock and renders; before3/knight_before3.py is the recovered before3 script. before_after4.jpg = before3 | 2x pass | now.
- Separation PASS (legs 0.224 m, arm-torso 0.158 m).

## Dense fix pass 9 (owner: keep the 2x density, fix the review's WORSE parts inside it)
- Start: the 2x script (pass3/), with every earlier fix it already holds (helm 1.12x, visor slit + ridge, pauldron, knee cop, crest, shield board, scabbard, belt path). The mix-pass density revert dropped.
- Limbs ringed and wobbly -> the 12-vertex limb rings now sit on a hexagon (corners every 60 deg, extra points on the edge middles): flat plate facets with crisp ridges, as before3, at twice the density. Radii smoothed: leg one straight greave taper (no ankle pinch/cuff bulge), arm one straight rerebrace/vambrace run (no elbow dip/bulge).
- Torso planes: the 10-vertex torso ring lies on the old 6-vertex plate polygon (corners kept, 4 extra vertices on its edges), so the 23 stations make co-planar plates, not rounded bands. Helm/neck rings, eye (visor slit) unchanged from the best version.
- Stage 1 re-locked r14 (r13 lock in before9/): 1880 tris, IoU side/front 0.662/0.753.
- Stage 4 r13: all gates PASS, lock assert PASS, glbcheck OK; posed folds 0.16 %; warning only (4 stretch tris). Total 3036 tris. Separation PASS (legs 0.208 m, arm-torso 0.117 m). Junctions checked in the 18-view orbit: no holes, specks or slits.
- before9/ = the mix-pass renders; fix9.jpg = hero before9 | after + arm and leg close-ups. orbit18_sheet.jpg, side_by_side.jpg rebuilt.

## Border pass (night 2026-10-23, s4 r14) - REVERTED
- kit/smooth_borders(body, k=k, iters=8): 3 despeckled, 0 cuts, 23 relaxed; stair corners 13 -> 1. Gates as baseline.
- A/B: TIE both orders -> champion kept; py/GLB/checks restored from before_borders/.
