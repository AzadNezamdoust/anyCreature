# mantis (t7x zoo, workflow v2)

Sheet: refs/gpt/v3/mantis/sheet_1.png (2x2), refs.py --height 0.55 -> length 0.807 m (antenna tip to wing tip).
refs warning: top-view width 0.32 vs front 0.47 (the plan view draws the legs tucked); the side wins for
proportions, front/rear for widths (wing leaf half-width 0.075-0.08 over a 0.05 belly), top for the leg plan.

**Identity cue:** raised folded raptorial forelegs (long coxa down, big blade femur up-forward, tibia folded back
down) in front of a long sloping prothorax "neck", a triangular head with round eye bulbs on its top corners, and
a long leaf abdomen under folded wings on four thin stilt legs with high knees. All in the S1 loft except the wing
slabs (S3 pieces, membrane gate) and antennae/spines.

Build: one loft of 10-vertex half rings, 41 stations, rings on the centre line's normal plane (Catmull-Rom centre
line through side-view points; sizes per station, straight lerps). Head rings are built per station (face triangle
+ a bulb sliced from a sphere). Legs: octagon tubes from 2x2 face blocks (hug ring 8 mm out at 0.88), joints turn
on fillet arcs (3 rings) so no ring crosses its neighbour inside a bend.

## Stage 1
- r00: PASS, 3008 tris, IoU 0.586/0.622/0.571. Reads as a mantis from every view. Critique: the head is a flat
  T-bar box (az000, az090 groove), the sheet's is a triangle with round corner eyes. Diagnosis: one HEADP profile
  lofted at constant height. Fix: per-station head profile.
- r01: PASS, IoU 0.586/0.625/0.577. Head bulb profile on the corners; still a box in az090 (constant top height).
- r02: PASS, IoU 0.588/0.627/0.577. Head rings built per station: face triangle + bulb sliced from a sphere: round
  bulb in az090. Critique: the femur reads as a thin tube rising only to z 0.31 (az090), the sheet's femur is a
  0.05-deep blade up to z 0.33. Diagnosis: 2.6 cm fillets cut 5 cm off each femur end. Fix: narrow joints in the
  bend plane (rw 0.012, R 1.5 cm), femur swell x2.3.
- r03: PASS, IoU 0.603/0.65/0.58. The blade femur reads in az090. Critique: az000 shows two thin bars by the neck,
  the sheet's folded forelegs fill x 0.035-0.095. Fix: femur at x 0.08, tibia folded inward to x 0.046.
- r04: PASS, IoU 0.603/0.65/0.585. Forelegs read as paddles in az000. Critique: the head still reads as an anvil
  (az000: flat top bar level with the bulb tops; the sheet's eyes rise above the vertex). Fix: vertex between the
  eyes 1.2 cm under the bulb tops, bulb arc rotated up.
- r06 LOCK: 1506 verts, 3008 tris, sha 2032ed24. Head reads (heart-shaped eye corners in az000).
- Re-lock (S2 r01 FAIL slivers 8.5%: the long thin tibia quads, 7 cm segments on r 6 mm; old lock in
  before_relock/): tibia runs get 5 (walking) / 4 (foreleg) in-betweens.
- r07 LOCK: 1634 verts, 3264 tris, edge sha256 59b6291c2e12d3e0.

## Stage 2
- r02: PASS (slivers 0.5%, IoU vs S1 1.0, tech QA 0). One logged change: eye socket inset on the bulb's
  out-forward face (H3-H4, vertices 3-4), sunk 3 mm.

## Stage 3
- r01: FAIL slivers 2.9% (antenna 64: 3.5 cm segments on 2-3 mm radius; wing tip 48: two long converging rows).
  Fix: antenna resampled to 10 rings, wing tip as 5 short rows narrowing to a blunt point.
- r02: PASS (4588 tris, 6 colours, slivers 0.4%, hit/float/zfight 0). Critique: the colour views read dark
  bottle-green, the sheet is a bright leaf green; pale belly and lime bulbs hardly show. Fix: palette two steps
  lighter.
- r03: PASS (4588 tris). Lighter palette reads as the sheet's leaf green. Critique: the sheet's pale belly
  (az090 lower abdomen) and pale inner femur blade do not show (only steep undersides were pale). Fix: pale on
  every abdomen face turned down past level, the prothorax underside, the femur's inner face.
- r04: PASS. Pale belly and inner femur read. (Paint follow-up in r09: coxa roots green, were pale/green patches.)

## Stage 4 and the junction loop
- r01: S4 PASS (glbcheck OK, tech QA 0; posed clip warn 0.26%). Critique (posed az090): the strike swings the
  forelegs BACK into the body. Diagnosis: coxa bone (local Z forward) +X swings the tip back. Fix: strike -X.
- r02 --junctions: FAIL: coxa1 knife 2.55 r at 170 deg, coxa2/3 knife 1.2 r at 153 deg + 3.9 mm seam strips; wing
  junction knife (its region r = 211 mm swallows the whole body, so it sums every coxa fold). Eye L/R PASS
  (0.31/0.76/0.81, 19.5 mm = 0.13 head), membrane PASS (p10 9.3 mm). Crops B/C: thin red wedges down each coxa
  side from the root. Diagnosis: one hug ring 8 mm out at ~0.9 x a 1 x 1.8 cm block, then a 4-7 cm wall that
  doubled the ring-direction size in one step (the coxa undercut the block).
- S1 re-locks 2-5 (old locks in before_relock2..5/), one fix each, probed at S4 every time:
  2 (r03): three root rings (normal -> coxa direction, size blended): coxa1 knife 0.88 r; coxa2 117 deg.
  3 (r04): root ring corners square-ish (0.95/0.88/0.81 -> octagon 0.75 on the first coxa ring): no change.
  4 (r05): coxa rh (ring direction) near the root ~ the block (was 1.5x: the undercut), neck station 1.7 cm behind
     the head (a 152 deg crease under the head sat in the coxa1 region): coxa1 + wing PASS; coxa2 still 144 deg.
  5 (r06): walking-leg blocks on ring faces 6-7 (normal ~55 deg down, along the steep coxa) instead of 5-6:
     knives 98 deg / 0; only seam strips 1.1-1.2 r left. Lock r12: 1730 verts, 3456 tris, sha256 bd79e12d8e21dfcd.
- S2 root fillet (vertex moves only, rounds s2 r07-r16, S3/S4 re-run each time; one change per round):
  r07 root rings 10/16/19 mm out: knives 0, strips 1.1-1.25 r (2.2 mm). r08 straighter rings: foreleg 159 deg
  (reverted for the foreleg, kept r07 rings there). r10 Bezier root rings for the walking legs: strips 4.4 mm.
  r11 first root ring parallel to its block (T = block normal; it was 4 mm off one side, 10 mm the other).
  r12 straight rings: 179 deg fold + self-hits (reverted). r13 ring-direction size held: no change. r14/r15
  Bezier control 0.7 / per leg: strip passes, hind knife 133-142 deg. Diagnosis (labelled strip vertices): the
  thin faces are the octagon corner faces on the U+ (rear) walls between r0-r1-r2: the block normal leans 20 deg
  forward with the tilted body rings and the coxa runs back, so the 34-40 deg turn crowded the short root walls.
  r16 fix: the root rings AND the first coxa ring ride one cubic Bezier from the block normal to the coxa-end arc.
  Result s4 r16: junction probe PASS on every root (coxa1-3 L/R, wing L/R), eyes PASS, membrane PASS.

## Owner-style review (orbit18_sheet.jpg, side_by_side_sheet.jpg, rounds/s4_r16_junctions.jpg)
Looked at every junction row (A/B/C beauty crops first) and the 18-view orbit: no slit, speck, knife fold, seam
strip, pinch, poke-through or floating piece at the coxa roots, the wing seat or the eyes; the coxae rise out of
the thorax underside through the three root rings; the wing slab sits on the abdomen with a clean 7 mm step.
Visible flaws found:
1. A pale/green (neck, belly edge) and lime/green (eye bulbs) checkerboard: the paint keyed on facet normals.
2. The raptorial spines read as hairs (3 x 16 mm) at orbit size; the sheet's are bold dark spikes.
3. (checked, not a flaw) wing/abdomen width in plan: wing edge half-width 0.079 vs sheet 0.078.
- f1 (S3 r19): paint by position (lime on the bulb sphere, pale on the lower 35% of each ring, mouth underside,
  femur inner face). Result: clean pale belly band and prothorax underside, lime bulbs, no checkerboard.
- f2 (S3 r20 + S4): spines 4.5 x 23 mm (femur) and 3.6 x 16 mm (tibia).
  Spines first collided (S3 r20-r22 tech QA hit: 2 shells): 25 mm femur spikes reached the tibia/coxa and a
  4.5 mm base at 0.9 rw crossed both thin blade corner faces. Final: femur spikes 4 x 19 mm at 0.8 rw,
  positions 0.46-0.745 of the foreleg; tibia spikes 2.8 x 13 mm. hit 0.
- f3 (S4 r19): posed check on the GLB (bone tails): coxa +X swings the leg FORWARD; s4 r02's flip had sent the
  strike back to the mid legs (tibia tip at z 0.017). Strike coxa +22, femur -10, tibia -40 (opens), snap +18/-6/+4.
  Result: the tibia tip shoots to y -0.49 at the strike and folds back in the snap.
- s4 r20 FINAL (with orbit): ALL GATES PASS: S1-S3 gates, lock assert, glbcheck OK (idle/move/attack), tech QA
  hit/float/zfight/fold/drift 0, slivers 0.4%, posed clip warn 0.21%, stretch warn 6 tris (2.5x); junction probe
  PASS on all 8 roots (coxa1-3 L/R knife 0 r, max concave 70-85 deg, strips <= 0.87 r, slit 0, poke 0, gaps 0,
  clip 0; wing L/R knife 0.48 r, slit 0.35%), eyes PASS (0.31/0.76/0.81, 19.5 mm = 0.13 head, round 1.0, proud
  7 mm), membrane PASS (wing p10 9.3 mm >= 6.0). Tris: stage 1 3456, total 4780 (body 3472 + pieces 1308).
Residual (visible, not fixed: fix-round budget used):
1. The head is smaller and boxier than the sheet's (corner bulbs read as faceted bumps; by the owner rule the eye
   is a small lens, so the sheet's big round eye mass is only suggested).
2. The femur blade is shallower than the sheet's (about 0.05 deep at mid but thin in the front view) and the
   spines are fewer/smaller than the sheet's comb.
3. Legs are smooth octagon tubes with no knee knobs; the wings read as one slab with a faint midline groove.

## Border pass (night 2026-10-23, s4 r21-r22)
- kit/smooth_borders(body, k=k, iters=8) after the body paint: 5 despeckled, 18 cuts, 50 relaxed (max 7.0 mm, 12 undone);
  stair corners 38 -> 21, 3-to-1 quads 24 -> 0. Junction probe PASS, clips PASS (after --fix-clips).
- techqa hit 2 (piece_spines): r22 = the same mantis.py WITHOUT the border pass also hits -> caused by the 10-23 detail
  pass (3 fat frustum spines), which was not rebuilt before tonight. Needs that pass's owner. Detail gate FAIL.
- A/B vs r22 (fresh Opus seat per order, blind): after wins both orders (head-underside pale patch). ADOPT; stage4 holds
  the r21 (border) build; r22 GLB kept as before_borders/mantis_r22_noborders.glb.
