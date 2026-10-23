# golem (t9 RECREATE, 2026-10-23) — NOTES

Rebuild from scratch of zoo/golem (zoo stays champion). Concept: refs/gpt/v3/golem/sheet_1.png; reference/ +
blueprint.json copied from zoo/golem (same sheet, kit/refs.py, height 2.0 m). Template code: zoo/minotaur
(ring13 torso, region windows), t9/bear (grow() with the 45 % transition ring).
Judge's reason the zoo model fails: boxy slab torso with a tiny head on top, moss as flat stripes, side view just
an arm block. Sheet: built from rounded boulder masses (big round chest, segmented arm stones, sunken head).
Identity cue (in S1): a huge ROUND chest boulder, a small head sunk at the FRONT of the dome between two giant
shoulder masses, massive segmented arm stones hanging to the knees, short stacked stone legs.
Sheet measurements (front/side crops at 0.0042 m/px): chest half-width 0.52-0.53 (z 1.0-1.5), front y -0.52;
head 0.33 x 0.33, z 1.60-1.93, front y -0.44; shoulder boulder top z 1.97 at x 0.43, outer 0.92 at z 1.58;
forearm half 0.29 at z 0.85, fist z 0.21-0.63; thigh x 0.16-0.51, feet x 0.16-0.66, y -0.34..+0.30.
Tools: ov.py (model ortho silhouette over the reference front/side at sheet scale), meas.py (widths per height).

## S1
- r1: loft 13-vertex half rings (ring13, 5 control points), arm 3 x 3 window C2-S1 + vertical boulder ring,
  legs 3 x 4 pelvis window + 45 % ring, head extruded forward from a 3 x 2 seam window (seam walls removed).
  FAIL self-intersection at the crotch back (leg's first section z 0.62 above the crotch ring 0.54). IoU
  0.834/0.833/0.762 (zoo lock 0.786/0.812/0.803). Critique az000: boxy barrel torso, shoulder a fin.
- r2: Fix: leg sections start at z 0.52; torso rounded (W 0.53 at the chest, 0.40 hips, narrowing to the top);
  arm window C3-T0 x 6 columns. FAIL self-intersection in the boulder turn (tilted rings crossed at the armpit).
  Critique az000: the shoulder a flat yoke.
- r3: Fix: the boulder turn as rings FANNED about one armpit pivot (fan(): no crossing). PASS, 2,476 tris, IoU
  0.846/0.849/0.773. Critique az000: the boulder top outboard and the crown a plateau beside the head.
- r4: Fix: dome top rings narrower (S1-T1 W 0.42/0.34/0.26/0.14) and the inner boulder ring at x 0.47, so the
  head sits sunk between the shoulder masses. PASS, IoU 0.848/0.844/0.789. ov.py: silhouette on the sheet's.
- r5 (LOCK 61ddbd3f1d8e8034): shoulder mass lowered 4-6 cm (the S3 boulder piece sits over it and rises above).
  PASS, 1,240 verts, 2,476 tris, IoU side/front/top 0.838/0.854/0.786. Residual: the shoulder base reads as an
  arch, not a ball; the S3 boulder piece gives the round stone.
- r6 (re-lock bbb05b85): head +15 % (sheet head reads bigger: the shoulders press on it). Lock r5 moved to scratch.
- r7-r10 (after the S4 r1 junction probe FAIL, upperarm knife 1.95 r / 168 deg, thigh 2.52 r / 130 deg; folds.py
  lists the concave folds > 60 deg): r7 head rings ahead of the window and the leg window 5 columns (thigh fold
  130 -> 85 deg); r8 head window back on S0, dome front S0 -0.37 (chin fold 168 -> 108 deg); r9 boulder inner ring
  bottom out-up of the window rim (still a V-notch apex 114 deg); r10 arc(): the shoulder-turn rings' inner ends
  step round the armpit (five folds < 60 deg): no fold > 90 deg at the shoulder.
- r11 (LOCK 70935df38c5b6d75): 1,272 verts, 2,540 tris, IoU 0.832/0.837/0.782.

## S2
- r1-r3: eye socket inset in the outer face column (turned out 23 deg: its outer edge 3.5 cm back), brow row 2 cm
  forward, jaw row 1.2 cm forward (chin step). PASS, min IoU vs s1 0.996.

## S3
- r1: palette stone/plate/seam/moss/glow/pupil; groove-ring seams painted on arms and legs, moss streaks on the outer
  upper arm, smooth_borders; pieces: glowing lens eyes, brow, shoulder boulders (rock(): diamond-faceted ellipsoid,
  moss top + drips), conform() stone plates (chest x2, back x2, belly, pelvis, low back, rump, forearm, knee, shin),
  knuckle blocks, toes. FAIL hit (chest plate into the head) + z-fight (toe bottoms on the sole); render too dark.
- r2: chest plate lower, toes 8 mm up, palette one step lighter, plates as quad grids (no centre-fan needles). PASS.
- r3: re-run on lock r11: FAIL hit (boulder contains the whole shoulder section: two crossings). r4: boulder lower
  half flattened (rb 0.13, underside 1.57 above the armpit arch): one crossing, PASS, 5,588 tris.
- r5: conform() edge samples that missed the curving dome stood as plane points (spikes on the back, orbit18 az270,
  top, bottom): cast far 2.0 + a retry toward the plate centre. PASS.

## S4
- r1: rig (hips, spine, chest, neck, head, upperarm, forearm, hand, thigh, shin, foot), idle/move/attack. Kit PASS,
  eyes PASS (0.88/1.0/0.65), detail PASS; junction FAIL (see S1 r7-r10). Brow plate wider than the face: its end
  samples missed and made a blade (eye side crop) -> b 0.13.
- r2 (lock r11, boulder 0.37/0.44/0.28): ALL kit gates PASS, junction PASS (upperarm knife 0.32 r/108 deg = chin,
  strip 0.36 r; thigh knife 0, strip 0.73 r), eyes PASS 0.82/0.86/0.51, detail PASS 14 groups.
- r3: attack bone sign (posed f009: arms swung BACK): +X raises the arms (roll auto). PASS; --clips --fix-clips:
  move pen 7.99 -> 0.045, attack 2.51 -> 0.0, clip gate PASS. orbit18: spikes on the back (fixed s3 r5); moss caps
  flat bright green.
