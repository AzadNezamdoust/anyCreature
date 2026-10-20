# great horned owl (t7 hand box-model) - NOTES

Technique from wolf_base (t7r line, no subdivision). One spine loft of 6-vertex half rings runs from the tail tip to the face disc. It leans as the sheet's side view does. The legs are 2-face belly regions extruded as horizontal hexagons, and the ear tufts are 1-face extrusions of the skull top. The folded wings, hooked beak, lens eyes, talons and breast feathers are separate pieces. Stage 0: blueprint.json was traced from reference/sheet.png with kit/refs.py (height 0.55 m). The sheet's top view traces 1.26x longer than the side, so it is not used for the fit.

## Stage 1
- r0: first fit (12 sections, legs from the M0-C0 span). FAIL: 4 self-intersecting pairs at the inner leg root (z 0.076). Diagnosis: the first leg section (z 0.08) sits at the height of the ring's lower vertex, so the extrusion folds. Fix: leg sections lowered (thigh 0.058, shank 0.036, ankle 0.016).
- r2: Result: PASS, 364 tris, IoU side/front/top 0.878/0.864/0.722. Critique: az000. The tufts are square blocks, but the ref tufts are flaring triangles. Fix: the tuft mid section was made shallower, with the tip out to x 0.106.
- r3 (LOCK): 184 verts, 364 tris, edge sha256 fe3d7429829d570a. IoU 0.878/0.860/0.722 (the low top IoU comes from the unreliable plan view).

## Stage 2
- r1: knee, ankle, neck-skull, belly and tail-root rings; an eye socket inset in the face disc where a frontal ray hits the ref eye position; a flat face disc; the brow corner moved forward. Gates PASS, 496 tris, min IoU vs s1 0.997.

## Stage 3
- r1: 6 colours, plus pieces: lens eyes, beak, folded wings, 3 talons per foot. Gates FAIL: total 790 tris, under the floor. Critique: the colours read near black next to the ref's mid brown.
- r2: Fix: palette lifted, the eye lens enlarged to r 2 cm (still small, simple), and blunt breast/thigh feather clumps added (6 per side). Gates PASS, 1030 tris.

## Stage 4
- Rig: hips/spine/chest/neck/head, tuft, tail, wing + wingtip, thigh/shin/foot (.L/.R). Clips: idle 48 (breathing, owl head turn, tuft twitch), move 24 (a hop: crouch, push-off with the wings half open, landing), attack 32 (mantle the wings, then a talon strike and head lunge).
- r1-r12: the drift gate failed on the wings. A wing bound to its own bones came off the flank. Moving the root to body weights did not help, and neither did removing the head weights. Diagnosis: the drift came from the attack's 35-degree thigh.L swing. The wing copies the flank's leg weights but sits 2-5 cm off the surface, so the lever arm opens a gap. Removing leg weights from the wing made both wings drift in the hop. Fix: the wing is bound with the body's weights (minus head/neck), the primaries past y 0.2 follow the wingtip bones, and the strike comes from the shin and foot (thigh 12 degrees).
- r13: all gates PASS (hit/float/zfight 0, slivers 1.7%, fold-overs 0.39% of tris / 0.15% of area, drift 0, lock OK, glbcheck OK). Clip warning only: 0.33% of the surface.

Checks: orbit18_sheet.jpg has 18 views, and every view reads with no hole or collapse. Fusion check on the rest mesh (checks/separation.json): leg L to R gap 2.8 cm; each wing is a separate shell, 74% of its vertices outside the body, standing off up to 5.5 cm (median 2.7 cm); wing L to R gap 11 cm. Verdict PASS. side_by_side.jpg is built.

Triangles: stage 1 364, stage 2 496, total 1030.
Weaknesses: the total is under the ~1.5k target. The wing flex is small (only the primaries move), so the hop reads mostly through the legs. The face disc is a flat tan panel. The front width under the wings is narrower than the ref.

## Pass 2 (review fix, both reviews merged)
- Fix list (shape first): body 8 degrees more upright about the leg root (Opus; the sheet still leans, so not fully vertical); tail 45% shorter, carried higher, a wider flat fan with a dark tip band (Opus shorten / Fable fan); paw-pad foot replaced by a small sole plus 3 thin toes forward and 1 back, each with a separate dark talon (Fable); ear tufts thinned to narrow points, smaller, tips angled outward (Opus); breast shard clumps removed, the bib is one cream region (Opus merge); wing gets a tip step and reaches over the shorter tail (Fable); eye lens r 2.0 -> 2.3 cm, 8 sides, pushed out of the tilted disc (simple lens kept; not 2x, owner rule).
- Base change: stage 1 re-locked (r4): 184 verts, 364 tris, edge sha256 1513daa3c3e8bcc3; blueprint side IoU 0.878 -> 0.742 (intended, the lean change). Old lock kept in before/.
- r15: tris 878 under the 900 floor -> wing tip section and 8-sided lens added: 918. r16: eye pupil hidden by the tilted face -> lens moved out. All gates PASS (lock, drift 0, fold-overs 0.23%, glbcheck OK). Separation PASS (legs 2.7 cm, wings separate shells).
- Not fixed: face disc stays flat (no concave plane), tufts still rise from a wide skull face, total tris near the floor.

## Pass 3 (round-2 reviews merged, concept sheet as referee)
- Fix list (shape first): facial dish (FACE profile 0.8/0.88 -> 0.85/0.95, H3 W 0.07 -> 0.08; Fable); eye lens r 2.3 -> 1.8 cm, pupil r 0.9 -> 0.75 cm, amber kept (Fable x0.8; Opus asked to drop the amber ring, but the sheet has amber eyes); upright body / shorter tail (Fable), shorter hidden legs (Opus), flatter wings (Opus) tried.
- Skipped against the sheet: the face disc toned to body colour (sheet disc is pale), wing contrast reduced (sheet wings are dark).
- Base change: stage 1 re-locked (r15), 184 verts, 364 tris, edge sha256 cc313785843bea77; side IoU 0.742. Old lock in before2/.
- r5-r9 (s1): lowered belly and a lower/fatter thigh self-intersected at the leg root (z 0.12); reverted. r16-r21 (s4): the R0 hump, T1 lift, wider R1, flatter wings and a wider shank each kept the wing drift gate failing; all reverted.
- r22: all gates PASS (lock, drift 0, fold-overs 0.11%, slivers 0.2%, glbcheck OK), 918 tris. Separation PASS (legs 2.65 cm, wings separate shells, 75% outside).
- Not fixed: posture/tail length and leg length (drift gate and leg-root fold block them in this rig), tris near floor.

## Poly pass 4 (denser main mesh)
Goal: about 2x triangles, mostly in the body loft, re-fitted to the traced sheet (no subdivision, no remesh).
Base change: loft 12 -> 22 stations (tail root, rump, belly, shoulder, neck curve, skull, brow, face rim); half rings 6 -> 12 vertices, each old profile rounded through a closed Catmull-Rom loop and resampled at equal arc length. New stations re-fitted along their cut line to the side outline of blueprint.json (hits more than 3 cm from the guess, the tufts and the legs under the belly, keep the guess). Legs: 3-face root region, 8-sided rings, 5 sections. Tufts re-seated on the nearest skull-top face.
Stage 1 re-locked as r33 (pass-3 lock kept in before3/): 580 verts, 1156 tris, edge sha256 468ebf4dab2eba72, IoU side/front/top 0.746/0.866/0.678 (pass 3: 0.742/0.860/0.722; the top view stays unreliable). Trial r30 FAIL: a 4-face leg root folded under the flank (12 pairs); fixed by the lower 3-face root.
Stage 2: the same 5 joint rings (now between adjacent new stations) and the eye socket; 1400 tris, min IoU vs s1 0.999.
Stage 3/4: details unchanged except the wing root row standing 1 cm further out (s4 r30 FAIL: 4 z-fighting wing faces on the rounder flank). r32: all gates PASS, glbcheck OK, separation PASS (legs 3.1 cm, wings separate shells, 73% outside). Total 1822 tris (was 918): body 496 -> 1400, details 422 -> 422.
Not fixed: QA warns only (8 stretched, 14 posed-clip triangles).

## Mix pass 5 (review verdict MIX)
Review: head, face disc and brow better after pass 4; the breast became a soft wobbly bib. Kept the pass-4 head, neck, tail and legs. Breast (R1..C1) restored to the pass-3 sections: the 6 old corners kept and the extra ring points placed on the flat facets (no Catmull-Rom rounding); breast in-betweens C0a/C1a dropped (22 -> 20 stations). Eyes, brow and head unchanged from pass 4.
Stage 1 re-locked as r40 (pass-4 lock kept in pass3/): 536 verts, 1068 tris, edge sha256 1cf720c7cfed860b, IoU side/front/top 0.746/0.860/0.676.
r41: all gates PASS, lock assert PASS, glbcheck OK, separation PASS (legs 2.9 cm, wings separate shells, 73% outside). Total 1734 tris (pass 4: 1822, pass 3: 918). QA warns only (8 stretched, 14 posed-clip triangles). Pass-4 renders kept in pass3/; before_after4.jpg = before3 | 2x pass | now.

## Fix pass 9 (owner: keep the 2x density, fix the problems inside it)
Mix pass 5 had dropped the breast in-betweens (22 -> 20 stations), a partial density revert. Restored all 22 stations and 12-vertex half rings; kept the pass-5 flat breast facets and the pass-4 head, eyes, brow, tufts, legs.
Breast fixes without losing rings: every breast ring (R1..C1) shares the same per-facet point counts, so corners line up ring to ring; the breast in-betweens R1a/C0a are straight blends of their neighbours (no outline re-fit, no spline), so ring sizes step evenly with no rib band; the breast quads are then pulled to their best-fit planes (40 averaged iterations, centre seam held on x 0) for co-planar chest facets.
Junctions checked in orbit18 (legs, tufts, neck, wing roots): no holes, specks or slits. Eye unchanged (pass-4 size).
Stage 1 re-locked as r51 (pass-5 lock in before9/): 580 verts, 1156 tris, edge sha256 3d4593a85727a5ac, IoU side/front/top 0.747/0.860/0.675. r50 = trial without the planarize step (blotchy lower chest).
r51: all gates PASS, lock assert PASS, glbcheck OK, separation PASS (legs 2.9 cm, wings separate shells, 73% outside). Total 1822 tris (pass 5: 1734). QA warns only (8 stretched, 14 posed-clip triangles). fix9.jpg = before9 | after, hero plus breast and chest close-ups.
