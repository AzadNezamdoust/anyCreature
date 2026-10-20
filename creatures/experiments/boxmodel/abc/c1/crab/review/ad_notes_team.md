# crab (abc/c1): art-director notes, team round

Packet read: 1_beauty, 2_closeups, 3_tech, 4_posed, 5_reference, techqa.json, reference/sheet.png.

## Score: 6 / 10. Verdict: FIX.

Reads as a crab in one glance from every angle; the tech sheet is clean (0 hit / float / z-fight / flip / drift, 1.2% slivers, 2 clip tris on rim teeth, and my eye agrees with the heatmap). What holds it under 7 is the front: a striped cream wall between the claws, a belly bowl twice the reference's height, lollipop eye stalks, and claw tips painted as blocks. All of it is on the hero and the az000 view, which is where a buyer looks first.

## Keep (must not regress)

- Carapace: low dome with the dark-red rim band over an overhanging cream underside (az090, back34). Proportion vs the sheet is right (IoU .80/.80/.78).
- Claws: big carved palms held in front with a real finger gap (top, az090), and the claws' size relative to the carapace.
- Legs: eight two-bend legs with dark tips, no collapse at the roots in any posed frame (4_posed), and the clean tech sheet.
- Palette: six flat colours, borders on loops.

## Must-fix (ordered by visual damage)

### 1. Front wall under the rim is a fan of vertical stripes. STAGE-1 UNLOCK
- **Stage:** 1 (unlock). Stage 2 tried to flatten the fan (s2 r04) and the triangles overlapped: the fault is the triangulation, not the vertex positions, and stages 2-4 cannot retriangulate.
- **Where:** 1_beauty az000 and hero; 2_closeups "eyes" colour: the cream face between the claw arms is 8-10 needle triangles fanning from the rim lip to the belly, each shaded a different value, reading as corrugated card.
- **Fix:** in stage1(), after the carve and before the leg build, replace the carve faces of the front wall (verts with y < -0.14, z between the belly bottom and the rim lip, |x| < 0.14, i.e. the span the r09 attempt proved is clear of the claw palms) with a regular grid: 2 rows x 4 columns of quads on one plane or on a shallow convex arc (bulge <= 2 cm, radius about the body half-width). Keep the wall where it is (no recess: r08/r09 showed the hull fuses body and claw beyond x 0.14). Re-lock; stage 2 code must still run on the new base.
- **Check:** 1_beauty az000: the cream face shows at most 3-4 flat facets with no vertical stripes; 3_tech az000 shows no yellow on the wall; stage-1 gates pass and lock sha changes once only.

### 2. Belly bowl is twice as tall as the reference's cream strip
- **Stage:** 2 (loop slide) + 3 (repaint on the moved loop).
- **Where:** 5_reference side vs model az090; 1_beauty az090, back34. The cream band is about 45% of the body height (rim at z 0.272 down to the belly bottom near 0.12); on the sheet the cream is a thin strip, about 20-25% of body height, hidden under the rim overhang.
- **Fix:** slide the belly colour loop (stage-2 planar cut at z 0.235) down by about 6 cm to z ~0.175 (about 15% of body height, 0.4 m), and paint everything above it shell red with the rim band unchanged. Optionally pull the belly-bottom verts up 2 cm so the bowl is shallower (IoU stays well above 0.9: the belly is a thin band in side view).
- **Check:** 1_beauty az090: cream band height <= 1/3 of the carapace-plus-belly height; 5_reference side pair reads the same red/cream split as the sheet.

### 3. Eye stalks are lollipops
- **Stage:** 3 (rebuild piece).
- **Where:** 1_beauty hero, az000, az090; 2_closeups "eyes". The stalks are about 2.5x the sheet's height and thin, the ball sits far above the rim. On the sheet the ball sits just above the rim lip on a stalk about one ball-diameter tall, and the ball is about 1.4x the stalk width.
- **Fix:** stalk height to 40% of the current (about 2 cm above the rim; ball centre at about rim z + 1 ball radius), stalk width +30%, ball diameter +25%; root the stalk in a socket on the rim (base ring 1 cm below the rim surface so it sits in, not on). Keep the eye spacing.
- **Check:** 5_reference front pair: the eye balls sit at the same height relative to the rim as the sheet; 2_closeups "eyes" wire shows the stalk root buried, not resting on a facet.

### 4. Claw finger tips are dark blocks, and the near claw reads as a lump
- **Stage:** 2 (vertex moves on the finger gap) + 3 (repaint the tip loop).
- **Where:** 1_beauty az000: a large black wedge on the inner side of each claw; hero: the near claw's dark zone covers about 35% of the claw and the two fingers merge into one mass with the gap barely visible. The sheet's tips are the last ~20% of each finger and both fingers read separately from the front.
- **Fix:** move the claw-tip loop forward by about 5 cm (y -0.555 to -0.60, i.e. dark = last 20% of the finger length) so the dark zone is a tip cap only; stage 2: deepen the finger gap by moving the gap's inner verts 2 cm apart (about 15% of the palm height) and pull the dactyl's top edge 1-2 cm up so the movable finger reads as its own wedge from the hero angle.
- **Check:** 1_beauty az000 and hero: dark zone only at the finger ends, two fingers distinct; 2_closeups "front limb" colour vs wire.

### 5. Legs too short and too flat compared with the sheet
- **Stage:** 2 (vertex moves on the leg rings; IoU stays > 0.9 because the legs are thin in every view).
- **Where:** 5_reference top and front pairs: the sheet's legs reach about 0.75 of the carapace radius beyond the rim and the knees arch up near the rim height; the model's legs reach about 0.55 and slope straight down from the hips. The silhouette is narrower than the brief's 1.5 m width.
- **Fix:** move knee-a rings up by about 4 cm (10% of body height) and out by 3 cm; move the second-bend and tip rings outward along each leg's azimuth so the tips sit 10-12 cm further from the body centre (about 15% of the half-width) while keeping the tips on z = 0. Re-fit the rig (stage 4) to the moved rings.
- **Check:** 5_reference top pair: leg reach matches the sheet within 10%; az000 shows arched knees; posed frames show no leg-root collapse; drift stays 0.

## Should-fix (short)

- Rim teeth: too small to read beyond the top view; +50% size, 7 per side, tilted forward 15 deg (stage 3). Check az000 and hero.
- Barnacles: three bigger ones (x1.6) clustered on the rear rim, as on the sheet, instead of five small ones (stage 3). Check back34.
- Legs are constant-section boxes: taper the tibia and tarsus rings by 25% toward the tip, and slide the knee-a ring so the knee is a visible bend (stage 2). Check 2_closeups "hind limb" wire.
- The 2 clip tris on the rim teeth in the attack pose: bind the teeth with `body=` to the rim (stage 4).
- Idle "claw click" barely moves the dactyl (4_posed idle f012/f024): +50% on the dactyl key.
