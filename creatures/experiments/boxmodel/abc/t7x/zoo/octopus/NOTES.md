# octopus (t7x zoo) — NOTES

t7's technique adapted to an octopus: the spine loft of 6-vertex half rings runs mantle tip -> egg mantle -> neck -> head -> arm crown -> mouth cap (13 rings); the ring planes turn from across the tilted mantle axis to horizontal at the head, seam A staying on one side, so the loft never twists. The eight arms are swept tubes, each grown from its own 2-face region (one column of the two crown spans) as flat-topped, flat-bottomed hexagons along an S path (S in side view: drop then lift; a small S in plan) with a fast-then-long taper. Neighbouring roots share one edge, so the only web is the side walls between them. Suckers are separate stage-3 pieces.

Stage 0: reference/sheet_h2fix.png traced with kit/refs.py (height 0.45 m). The sheet's "side" tile is a 3/4 view and its top and front widths disagree (0.74x), so the blueprint IoU is a loose guide (side/front/top ~0.56/0.57/0.38).

## Stage 1
- r1: first fit. Gate FAIL — 28 self-intersecting pairs at the rear crown; 1216 tris. Critique: az000 — the arm crown sits low (z 0.14), the arms droop to the ground from the roots; the ref arms leave the crown near-level at z ~0.17-0.2. Diagnosis: crown rings low, arm z profile a single dip. Fix: crown up 2.3 cm, CROWN profile vertices every 38 deg (equal arm columns), arm z given at five points per arm read off the front view (front pair hangs, next pair level, third low, rear pair lifts).
- r2: PASS, IoU 0.536/0.597/0.437. Critique: az000 — the arms are pencils next to the ref's. Diagnosis: root half width 0.026, taper exponent 1.3. Fix: 0.032, exponent 1.1, height 0.95 of width.
- r3: FAIL, 22 pairs at the crown between arms 1/2 and 3/4. Diagnosis: the plan S swings of neighbouring arms point toward each other (opposite signs). Fix: all swings start toward the back.
- r4: PASS, IoU 0.554/0.584/0.367. Critique: az090/top — the mantle is a sausage; the ref mantle is a fat egg (length/diameter ~1.3). Fix: mantle radii +12%, W 0.97 r, axis 3 cm shorter.
- r5: PASS, IoU 0.561/0.568/0.375. Critique: top — the arms wiggle in plan; the ref arms radiate as a star with a gentle curve. Fix: plan swing halved.
- r6 (LOCK): gates PASS, 610 verts, 1216 tris, edge sha256 f1a36b46ca519d5f; IoU 0.564/0.569/0.381.

## Stage 2
- r1: neck ring (M6-N0), mid-mantle ring (M3-M4), eye socket inset in the side head face between H0 and H1 (5 mm in), brow corner out, flat mouth cap. Gates PASS: 1272 tris, slivers 0, min IoU vs s1 0.997.

## Stage 3
- r1: colours along existing loops (skin; pale arm undersides on the hexagon's lower corner loop and mouth cap; cream suckers; amber eye with black pupil); small lens eyes; 7 hex-cup suckers per arm sunk 3 mm into the flat underside. Gates PASS, 2440 tris, 5 colours. Critique: hero colour reads brick red against the ref's salmon orange, the eye a dot.
- r2: Fix: palette one step lighter (skin #ec7650, pale #f6b896), lens r 1.7 cm. Gates PASS.

## Stage 4
- r1: rig body + mantle1/2 + 4 arms x 3 bones per side (local Z up: rot X = curl up); clips idle (wave down every arm, mantle breathing), move (swim: arms open, jet stroke, tips trail), attack (front two pairs rear up and lash down). Gate FAIL: drift 2 shells — the eyes were rigid to `body` while the head skin blends into mantle1.
- r2: Fix: eyes bound with body weights. All gates PASS (clip warning only, 8 tris).
- r3: Critique: side_by_side rear — a pale band under the mantle. Diagnosis: the underside test (z < 0.27) caught the mantle underside. Fix: z < 0.235. All gates PASS: hit/float/zfight 0, slivers 0, fold-overs 0, drift 0, final lock OK, glbcheck OK; clip warning 0.17% of surface.

Checks (checks.py on the stage-4 GLB): orbit18_sheet.jpg — every view reads, no collapse or hole. Separation on the rest mesh (arm vertices past 17 cm from the crown, by azimuth): neighbour gaps 8.8-14.7 cm; the two rear arms 1.8 cm (their group also holds the mantle tip): PASS. side_by_side.jpg: sheet views next to the model.

Triangles: stage 1 1216 · stage 2 1272 · total 2440.
Weaknesses: no siphon and no spots (shape first); the ref arms are longer and finer at the tip; the head-to-crown column reads a little stalk-like from the front; the blueprint IoU is low because the sheet's side tile is a 3/4 view.

## Fix pass (reviews: fable 7, opus 5)
Merged list (shape first, sheet as tie-break): arms short/thick/some lifted -> long tapered low star; mantle -> longer egg tilted back, pinched tip; eyes buried -> turret bumps; suckers kept (sheet shows rows).
- Base change: stage-1 lock deleted (old lock kept in before/), re-locked.
- s1 r7: arm reach +35% (0.44/0.54/0.54/0.50), taper exponent 1.5, all arms end low (z 0.05-0.11; rear pair no longer lifts). PASS 1216 tris.
- s1 r8: mantle axis 35 deg, length +14%, radii +4-8%, tip pinched; head width +15-20% (eye level). PASS.
- s1 r9 lock; s2 r2 FAIL slivers 7.1% (needle tris at the whip tips). Fix: tip floor 6 mm. s1 r10 re-LOCK: 1216 tris, edge sha256 90d6bc41d255fdc1.
- s2 r3: eye socket face pushed out 9 mm (turret) instead of in. PASS 1272 tris.
- s3 r3 PASS 2440 tris, 5 colours. s4 r4 all gates PASS, glbcheck OK, clip warning 0.17%.
- Checks: separation PASS (neighbour gaps 7.9-11 cm, rear pair 1.3 cm); orbit18 all views read in colour. before_after.jpg added.
Not fixed: front view head column still a little tall; lens eye small; no siphon.

## Fix pass 2 (round-2 reviews: fable 7, opus 7)
Merged list (shape first, sheet as referee): mantle more upright and fuller; arms thicker at the root; arms curve in plan and lift at the tips; eyes on bumps. Before images in before2/.
- Base change: stage-1 lock re-made (old lock in before2/).
- s1 r11: mantle axis 50 deg, widths x1.08, root half width 0.042, plan curve one-way 0.035 growing to the tip, tips +0.04. FAIL 6 pairs at the front crown (arms 1/2 roots); mantle a tall stalk, tips hook.
- s1 r12: axis 44 deg, length -8%; root 0.039; tip lift spread over the last half. PASS.
- s1 r13 LOCK: 1216 tris, edge sha256 9807ec6db43fe62b. s2 eye turret 9 -> 13 mm.
- s4 r5: all gates PASS, lock assert PASS, glbcheck OK, clip warning 0.17%. Separation PASS (neighbour gaps 3.1-13.4 cm, rear pair 1.4 cm). orbit18 all 18 views in colour; before_after2.jpg added.
Not fixed: skipped fable's 50 deg mantle (a stalk against the sheet); no siphon; tip ends slightly blunt.

## Poly pass 3 (owner: about 2x tris, the new density in the main body)
Before images, old script and old lock in before3/. Same box-model technique (no subdivision, no remesh).
- Base change: stage-1 lock deleted and re-made. Loft 13 -> 22 stations (mantle 7 -> 12, close at the pinched tip and egg shoulders; neck N1, eye station Hm, crown shoulder H2, crown C1b added); half rings 6 -> 8 vertices. Profiles and the mantle radius list are run through smooth curves (Catmull-Rom / monotone cubic) and resampled, so the new vertices sit on the rounded form. Crown vertices by angle (0/36/45/77/94/130/139/180 deg): arms on columns 0/2/4/6, narrow web columns between them. Arms: octagons (were hexagons) from a 3-face root column, 22 sections (were 10), z a smooth curve through the five design heights.
- s1 r14: PASS 3428 tris, IoU 0.448/0.473/0.346 (before 0.447/0.478/0.342).
- s1 r15: neck station fuller (no stalk), egg +6% through its middle. PASS, IoU 0.452/0.463/0.349.
- s1 r16 LOCK: 3428 tris, edge sha256 7496fd470424c93b. Budgets raised: stage 1 1500-5200, total 3000-8000.
- s2: joint rings re-placed on the new loft (M11-N0 neck, M6-M7 mid-mantle); eye turret on the Hm-H1 side face. 3500 tris.
- s3/s4 r6: suckers and bones kept at their old arm positions, suckers re-seated on the new underside. All gates PASS, lock assert PASS, glbcheck OK; clip warning 2.53% of surface (was 0.17%).
- Checks: separation PASS (neighbour gaps 2.0-10.4 cm, rear pair 1.1 cm); orbit18 all 18 views read in colour. before_after3.jpg added.
Triangles: body 1272 -> 3500, details 1168 -> 1168, total 2440 -> 4668 (1.91x; 100% of the increase in the body).
Not fixed: eye reads smaller on the narrower turret face; posed clip warning higher.

## Eye pass (review_poly2x: MIX — keep mantle and arms, restore the before3 eye)
2x-pass renders, script and lock kept in pass3/.
- Base change: stage-1 lock deleted and re-made. Head station Hm dropped, so the eye face spans H0-H1 again as in before3; the head half ring is now a hand 8-vertex profile whose vertices 2-3 are exactly the old side-face vertices 1-2 (full-size turret face). Mantle (12 stations), crown and arms (22 octagon sections) unchanged.
- s1 r17: PASS 3400 tris, IoU 0.452/0.463/0.349. s1 r18 LOCK: 3400 tris, edge sha256 70df9f86ad63b947.
- s2/s3/s4 r9: eye turret and brow on H0-H1 as before3. All gates PASS, lock assert PASS, glbcheck OK; clip warning 1.67% (was 2.53%).
- Checks: separation PASS (neighbour gaps 2.0-10.4 cm, rear pair 1.1 cm); orbit18: yellow lens visible in front, side, 3/4 and +45 views. before_after4.jpg: before3 | 2x pass | now.
Triangles: total 4640 (body 3472, details 1168).

## Fix pass 9 (dense mesh kept, problems fixed inside it)
Owner: keep the 2x density and fix the problems within it. The octopus eye pass had already kept the dense loft (22 stations, 8-vertex half rings, 22-section octagon arms), so nothing is reverted; review_poly2x's one WORSE part was the eye. Renders, script and lock before this pass are in before9/.
- Eye: lens radius 0.017 -> 0.021 (pupil 7.5 -> 9.2 mm), turret inset 0.4 -> 0.3 so the turret face is wider and holds the bigger lens. Now larger than before3's eye.
- Junctions: arm roots, crown web and mouth cap checked in the hero, close-up and bottom views: no holes, specks, slits or folds.
- Base change: stage-1 lock deleted and re-made (stage 1 unchanged): 3400 tris, edge sha256 70df9f86ad63b947.
- s4 r10: all gates PASS, lock assert PASS, glbcheck OK; hit/float/drift/fold-overs 0; clip warning 1.69%. Separation PASS (neighbour gaps 2.0-10.4 cm, rear pair 1.1 cm). orbit18_sheet.jpg, side_by_side.jpg and fix9.jpg (before9 | after, eye and crown close-ups) rebuilt.
Triangles: total 4640 (body 3472, details 1168).
