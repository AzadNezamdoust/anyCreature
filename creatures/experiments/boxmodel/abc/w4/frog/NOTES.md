# frog (w4) build notes

Reference sheet present: blueprint.json traced from it (not redrawn; marks eye/shoulder/knee/heel added).
Conflict: brief says length 0.5 m, width 0.8 m with feet; the sheet (scaled to 0.3 m height) gives ~0.36 m long,
~0.39 m wide. Sheet wins on shape (BUILD.md), so the build follows the blueprint scale. Brief wins on palette/clips.

## Stage 1
- r01 Critique: gate FAIL, 4 self-intersecting face pairs. Diagnosis: debug overlap print -> all at the hind heel fold
  (y 0.15-0.16, z 0.01-0.02). Fix: move heel ring back (y 0.176) and first foot ring forward (y 0.138). Result: still 4 hits. 484 tris.
- r02 Critique: same hits at the heel. Diagnosis: the foot rings used u=z, nearly parallel to the heel ring's normal, so the
  corner matching rotated the foot 180 deg (a twisted tube). Fix: foot rings use u=x (a=width, b=height). Result: 0 hits, all gates PASS. 484 tris.
- r03 Critique: top view (ortho_top) hind legs run parallel to the body as two planks; the reference folds them in a V
  (thigh out-forward from the rear, shin back in, foot out-forward). Diagnosis: thigh rings stacked at x~0.14-0.15 along y.
  Fix: splay knee out, shin back inward, foot out-forward. Result: foot splays; thigh still parallel (top IoU 0.754). 484 tris.
- r04 Critique: thigh still hugs the flank in plan. Diagnosis: thigh rooted mid-flank (segment 7). Fix: root the thigh on the
  rear face (segment 8), run it diagonally out to the knee. Result: 2 hits thigh root vs flank. 484 tris.
- r05 Critique: gate FAIL, thigh root inner face inside the flank at y 0.12-0.13. Fix: root ring pushed out/back
  (0.095, 0.165), thigh mid out to x 0.135. Result: 4 new hits thigh bottom vs shin/ankle.
- r06 Critique: gate FAIL, thigh underside cuts the shin. Diagnosis: thigh bottom z 0.054 = shin top. Fix: thigh raised/thinned
  (bottom ~0.068), shin lowered 4 mm. Result: 0 hits, V fold reads in top view (top IoU 0.755). 484 tris.
- r07 Critique: eye bumps are small square posts; the bulging eyes are the identity cue (front/hero). Diagnosis: eye turret
  rings 0.024x0.020 then 0.016x0.013. Fix: bigger, more outward turret (0.028x0.024 -> 0.020x0.017, top z 0.296). Result: better; front IoU 0.708. 484 tris.
- r08 Critique: front view is a barrel; the head should be the widest mass with the shoulders narrower. Diagnosis: S4/S5
  dorsal+side x 0.066-0.108. Fix: head mouth line x 0.106, S4/S5 narrowed, snout tip narrowed. Result: head reads wider. 484 tris.
- r09 Critique: a crate sticks out of the rear (side + top): the thigh root ring 0.031x0.022. Fix: smaller root ring
  (0.026x0.017), meatier mid-thigh (0.035x0.027). Result: rear rounder, side IoU 0.838. 484 tris.
- r10 Critique: rear view is a wide box; the reference is a pear (narrow back, wide hips/thighs). Diagnosis: dorsal verts v1
  S5-S8 at x 0.058-0.076, chest v3/v4 wide. Fix: dorsal v1 narrowed, chest lower sides narrowed. Result: pear reads from az180. 484 tris.
- r11 Reads as a frog from every view (V-folded hind legs, eye bumps, tilted-up head). Lock.
- r12 LOCK: 244 verts, 238 faces, 484 tris, edge sha256 5516ad30fb97742d. Min blueprint IoU 0.709 (front; side 0.838, top 0.756).
  Orbit rc=0 (advise: no head chain in a grey base, expected).

## Stage 2
- r01 Ops: eye socket inset, second elbow loop, extra knee loop; snout pulled into a V, skull plane flattened, throat keel,
  spine crest. Critique: gate FAIL slivers 16 (3.0%), all yellow on the eye turret. Diagnosis: the socket inset at 0.22 leaves
  a rim ~4 mm wide on a 24 mm face -> needle triangles. Fix: inset 0.36 (wider rim). IoU vs s1 min 0.986. 532 tris.
- r02 Result: all stage-2 gates PASS (slivers under 2%), IoU vs s1 min 0.986, orbit rc=0. 532 tris.

## Stage 3
- r01 Pieces: gold eye domes + black pupil bars, black mouth line, 12 draped spots (mirror off), toes with pads + 4 webs per
  hind foot, hidden tongue; 6 colours. Critique: gate FAIL slivers 68 (4.3%): mouth 28, toes 32, body 8. Diagnosis: the mouth
  strip spans 40 mm per section on a 5 mm diamond; web side faces 22 x 2.2 mm (5.7 deg). Fix: 3 sections per mouth span;
  webs 3.4 mm thick, 19 mm long. 1580 tris.
- r02 Result: all gates PASS, 1708 tris. Critique (hero/az000 colour): cream leaks onto the front forearms and hands; the gold
  eye is a small dot next to the reference's big eye; spots too small to read. Diagnosis: jaw rule (y<-0.055, z<mouth) also
  catches the front legs; eye dome r 17 mm. Fix (budget-merged, one colour/face pass): jaw rule limited to z>0.12, chest rule to
  x<0.07; eye dome r 21 mm, pupil 19 mm; spots x1.4.
- r03 Result: all gates PASS, orbit rc=0, 1708 tris, 6 colours. Cream now only on jaw/throat/chest/belly. Eye still reads
  smaller than the reference and spots are faint on the shaded flank; accepted for budget.

## Stage 4
- r01 Rig (12 bones + .R mirrors, roll auto; tongue bone non-deforming during skin, then the tongue tip ring only), clips idle
  (throat pulse x2, eye-retract blink), move (hop in place), attack (rear up, tongue lash 13 cm). All gates PASS, glbcheck OK.
  Posed wires: neck/shoulder and knees bend without collapse; tongue reads. Critique: hop apex (move f016) hind legs barely
  extend, reads as floating. Fix: thigh/shin -38, foot -25 at launch.
- r02 (final, with orbit): all gates PASS; hit 0, float 0, z-fight 1, slivers 8 (0.5%), flips 0 / 0% area, drift 0,
  lock PASS, glbcheck OK. Hop apex now shows the hind legs extended (thigh+shin straightened, feet trailing). 1708 tris.

Triangles: stage 1 484, stage 2 532 (body), stage 3/4 1708 total. Rounds: s1 12 (lock r12), s2 2, s3 3, s4 2.
- r03 Critique (review 1_beauty az000): a cream patch on the snout top above the lip. Diagnosis: the snout cap is one n-gon
  spanning the mouth line; the jaw rule painted all of it. Fix: faces facing straight forward (n.y < -0.9) stay green; the black
  lip piece covers the border.
- r03 Result: all gates PASS (same QA totals), orbit rc=0, glbcheck OK; review packet rebuilt. Rounds: s1 12, s2 2, s3 3, s4 3.
