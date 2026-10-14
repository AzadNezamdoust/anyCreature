# character (w4) - NOTES

Reference sheet read before stage 0: bald toon mannequin, ball head ~1/4 height, thin neck, slim straight torso, T-pose. Blueprint is the traced one (not replaced).

## Stage 1
- r1 Critique: first render had blade feet (flat vertical shards, front + side). Diagnosis: `face_near(..., n=-Y)` ran before normals were recalculated, so it picked an inverted back face of the ankle block. Fix: `recalc_normals(bm)` before the foot and thumb lookups. Result: better; feet are blocks, gates PASS, 830 tris, IoU side/front/top 0.863/0.809/0.808.
- r2 Critique: front view, the pelvis flares into a wide "shorts" trapezoid (hip ring rx 0.150) and the leg outline steps in at the crotch; the reference hips are barely wider than the waist. Diagnosis: hip ring (z 0.76) rx 0.150 and thigh station rx 0.064. Fix: hip rx 0.150 -> 0.126, thigh ring rx 0.064 -> 0.056 (centre 0.098).
  Result: better; hips no longer a skirt, but the overlay still shows grey outside the red at hip/crotch height (the crotch hex outer vertex at x 0.160 is now the widest point). 830 tris, IoU 0.863/0.818/0.808.
- r3 Critique: front overlay, hips/upper thighs bulge past the traced outline and the crotch gap opens too wide (inner thigh x 0.044 vs traced ~0.02). Diagnosis: leg-root hex centre 0.100 / half-width 0.060 and the z 0.60 station. Fix: root hex centre 0.093, half-width 0.052; thigh station centre 0.092, rx 0.052.
  Result: better; hip line now inside the trace, crotch gap narrow like the reference. 830 tris, IoU 0.862/0.826/0.808.
- r4 Critique: side and hero views, the foot is two stacked slabs with a hard step at the instep (top 0.075 -> 0.050 -> 0.030) and points straight ahead; the reference foot slopes smoothly from the ankle to rounded toes that turn slightly out. Diagnosis: the two foot extrusions' `ztop` and centre x. Fix: instep top 0.062 at y -0.115, toe top 0.038 at y -0.19, toe centre stepping out 0.118 -> 0.124 -> 0.134, half-width 0.048.
  Result: better; one sloping foot turned slightly out, no instep step. 830 tris, IoU 0.868/0.830/0.823.
- r5 Critique: front and hero views, the shoulder is a flat shelf meeting the arm root at a right angle (a coat hanger); the reference shoulder slopes from the neck into a rounded cap. Diagnosis: shoulder-top ring (z 1.15) sits out at rx 0.138, level with the arm's top. Fix: that ring rx 0.138 -> 0.124 and z 1.15 -> 1.157 so neck -> shoulder -> arm top is one falling slope.
  Note: arm span is 1.68 m (hand tip x 0.84) to match the traced front/top views; the brief says 1.5 m. Sheet wins on shape (BUILD.md).
  Result: better; neck -> shoulder -> arm reads as one slope, rounder cap. 830 tris, IoU 0.868/0.829/0.822.
- r6 LOCK: reads as the toon mannequin from every view (ball head ~1/4 height on a thin neck, slim straight torso, long thin limbs, T-pose). Locked with orbit.

Stage 1: 6 rounds (5 fixes + lock), 830 tris, lock edge sha256 2df2fd913009e92b..., min blueprint IoU 0.822 (top).

## Stage 2
- r1 Critique: az000/hero, the head is a blank ball - no socket, no nose; the face carries the character. Diagnosis: the eye face (seam..first column, rings 1.40-1.50) is one flat quad and the seam vertex at 1.40 sits on the sphere. Fix: `inset` the eye face (0.28, -0.012) for a socket and pull the seam vertex at 1.40 out 0.024 as a tiny nose; socket valleys kept via META keep_valleys.
  Result: better; two readable sockets and a small nose ridge between them, gates PASS, 846 tris, IoU vs s1 min 0.987.
- r2 Critique: hero/az090, the foot is one smooth wedge with no toe block (brief: bare feet with toe blocks). Diagnosis: the toe segment (y -0.115..-0.19) is a single quad ring. Fix: `loopcut` round the toe segment at t 0.45 and press its top verts down 0.009 so the toes read as a block.
  Result: better; a toe block reads at the ball of the foot, gates PASS, 862 tris, IoU vs s1 min 0.987. Stage 2: 2 rounds.

## Stage 3
- r1 Critique: the face is still blank sockets - no eyes, brows or mouth; identity needs the big cartoon eyes. Diagnosis: no pieces yet. Fix: raycast-seated pieces: 10-gon black rim + domed white sclera + 8-gon pupil lens per eye (mirrored), arched brow bars, a straight mouth bar; body painted peach. 4 colours.
  Result: better; the face reads (eyes, brows, mouth), gates PASS, 1166 tris, 4 colours. (Colour renders read the peach as tan under the workbench key light; the white reads light grey too, so it is the light, not the palette.)
- r2 Critique: az000 face crop, the eyes are smaller than the reference's and the square socket rim shows as a dark frame round each eye. Diagnosis: rim r 0.047 / sclera r 0.042 do not cover the inset square. Fix: rim 0.053, sclera 0.048, pupil 0.015; brows lifted to z 1.536 to clear the bigger eyes.
  Result: better; big eyes cover the sockets like the reference, brows clear them, gates PASS, 1166 tris. Stage 3: 2 rounds.

## Stage 4
- r1: rig on J (roll auto), skin, eye.L/.R bones (skin weight they took handed back to head), eye pieces rigid per side, brows/mouth bind(body=). Clips idle (breathe + blink f40-44), move (4-key walk, arm swing), attack (guard, wind-up, left jab).
  Result: FAIL posed fold-overs 31 tris (2.66% / 0.83% area); every other gate PASS. Heatmap: purple at the top of the shoulder / arm root.
- r2 Critique: posed hero wire + tech, the shoulder cap folds over when the arm drops 56-70 degrees from T-pose. Diagnosis: nearly all of the drop is on upperarm, whose root ring sits right against the shoulder-top faces; heat weights pinch them. Fix: move ~20 degrees of every drop onto clav (the whole shoulder mass turns) and keep upperarm at 30-44.
  Result: better but FAIL: 19 tris (1.63% / 0.22% area); the shoulder is clean now, the heatmap has moved to the inside of both elbows.
- r3 Critique: tech heatmap, the inner elbow folds over in the attack guard/wind-up. Diagnosis: forearm bends of 105-120 degrees across only three elbow rings 0.04 m apart. Fix: guard elbow 105 -> 70, wind-up 120 -> 85 (the jab still extends to 6).
  Result: better but FAIL by one triangle: 6 tris (0.51% / 0.10% area); drift 0, glbcheck OK.
- r4 Critique: the last folds are still at the inner elbow in the attack guard. Diagnosis: 70/85-degree elbow bends on the same three rings. Fix: guard elbow 55, wind-up 65 (a tighter-armed, more boxer-like guard is still readable).
  Result: PASS; fold-overs 1 tri (0.09% / 0.05% area), drift 0, glbcheck OK. Posed wires: neck, shoulders, knees bend without collapse; the jab reads, the guard is loose rather than a tight boxer guard.
  Note: the idle blink (eye bones rotate 80 deg, f40-44) falls between the drift sampler's frames (10/19/29/38); the eye pieces swing about their own centre inside the socket during those 4 frames.

Triangles: stage 1 830, stage 2 862, stage 3/4 1166 total. Rounds: s1 6 (incl. lock), s2 2, s3 2, s4 4.
