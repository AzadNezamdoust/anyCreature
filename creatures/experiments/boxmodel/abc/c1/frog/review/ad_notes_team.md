# frog (abc/c1): art-director notes, team round

Packet: review/1_beauty.jpg, 2_closeups.jpg, 3_tech.jpg, 4_posed.jpg, 5_reference.jpg, techqa.json.
Body dimensions used below: L = 0.5 m (length), W = 0.8 m (width with feet), H = 0.3 m (eye tops).

## Score: 6.5 / 10 -- Verdict: FIX

Reads as a frog in one glance from the front and the side; the tech sheet is clean (hit 0, float 0, z-fight 0,
fold-overs 0, drift 0; slivers 1.8% are hairline and invisible in beauty). What holds it under 7 is proportion
and surface, not technical errors: the rear half is a crate, the spots are random dark facets, and the eyes are
too small to be the silhouette cue the brief asks for.

## Keep (must not regress)

1. Side silhouette (1_beauty az090, 5_reference row 1): tilted-up sitting pose, round knee tucked at the flank,
   long foot lying forward on the ground, pear belly. This is the best match to the sheet.
2. Front face (1_beauty az000): continuous black mouth line across the cream jaw, cream throat/belly as one clean
   region, gold eyes with horizontal pupil bars. Colour borders already sit on edge paths.
3. Extremities: 4 splayed fingers with round pads, 5 long hind toes with pads and web slabs; planted, no drift in
   4_posed; gates all PASS.

## Must-fix (ordered by visual damage)

### 1. STAGE-1 UNLOCK -- rear half is a crate, not a dome with two thigh lobes
- Stage: 1 (unlock). Stage 2 cannot reach it: rounding the rear box into the sheet's dome removes well over 10%
  of the rear-view silhouette, which breaks the IoU > 0.9 rule; and the haunch/body groove needs occupancy
  removed from inside the hull, which vertex moves on a decimated surface cannot do (r02 of stage 1 already
  showed 86 self-hits from a vertex squeeze).
- What: 5_reference row 3 (rear vs az180) and 1_beauty back34: the model's rear is two square haunches with
  vertical outer walls, square floor corners and a flat vertical back wall, joined by a flat shelf; the
  reference rear is one round dome with the thighs as two smaller rounded lobes beside it, each narrower than
  the body. In 2_closeups "hind limb colour" the thigh is a flat-faced block as tall as the belly.
- Fix (carve input only, same pattern as stage-1 r03 BELLY cut): (a) top mask: round the rear plan outline into
  an egg; pull each rear corner in by ~8% W at the back and taper the thigh lobe so its outer edge is ~10% W
  inboard of the current wall at the hip, ~5% W at the knee; (b) front/rear mask below z = 0.15: cut the thigh
  lobe off the belly with a notch ~4% W wide and ~6% H deep between belly and thigh; (c) 3D cut of the occupancy
  behind the hips: nothing above a dome whose top is at the current back height and that falls ~25% H at the
  rear wall (kill the flat back face). Re-lock, then re-run stages 2-4; keep the side mask (the keep-list
  silhouette) untouched.
- Check: 5_reference row 3 -- az180 shows a round back and two lobes narrower than the body, with light between
  belly and thigh at the floor; 1_beauty back34 no longer shows a vertical outer thigh wall. Gates: one shell,
  no self-hits, 900-1400 tris.

### 2. Spots are random dark facets, not spots
- Stage: 3.
- What: 1_beauty back34, az090 and 5_reference row 4 (top): the dark green is scattered whole carve triangles
  of arbitrary shape and size; at thumbnail it reads as camouflage/dirt. The reference has round, evenly sized
  hexagonal spots in a loose row either side of the spine and down the flank.
- Fix: replace the painted-triangle spots with ~10 disc pieces (6-8 sided, radius ~3.5% L, 0.5 mm above the
  skin or half-sunk, bound with body=) placed on the dorsal surface: 2 rows of 3 either side of the spine
  between shoulder and hip, 2 on each flank behind the foreleg, 1 on each thigh top. Keep them off the head and
  belly. 6 colours still.
- Check: 1_beauty back34 and 5_reference row 4: spots read as round dots of one size at thumbnail; 3_tech shows
  no float/z-fight on the discs.

### 3. Eyes too small to be the bulging-eye cue
- Stage: 3.
- What: 5_reference rows 1-2: the reference eye is a ball ~20% L in diameter standing proud above the skull and
  outboard of the head; the model's eye is a cap ~12% L that sits inside the turret and barely tops the head
  line. In 1_beauty az000 the eyes read as small corner nubs; from az090 the eye does not break the skull
  silhouette.
- Fix: eye ball radius x1.5 (to ~9-10% L); raise the centre so the ball rises above the turret top by ~1/3 of
  its diameter and push it outboard ~2% W so it breaks the head outline in the front view. Keep the pupil bar
  horizontal and the same proportion of the ball. Re-check the cap rings do not float off the turret (bind body=).
- Check: 1_beauty az000 and az090: the gold ball breaks the skull silhouette top and side; 3_tech eyes grey.

### 4. Mouth line stops short, and the pink tongue tip shows at rest
- Stage: 3 (tongue tip rest position may also be a stage-4 key).
- What: 1_beauty az090 and 5_reference row 1: the black mouth tube ends at the snout corner; the reference
  mouth runs back to under the eye (~35% L from the snout). 1_beauty az000 and 2_closeups head colour: a pink
  rectangle shows in the middle of the mouth line at idle frame 1.
- Fix: extend the mouth tube along the jaw cut's edge path back to x under the eye centre (about +15% L per
  side), same section. Sink the tongue pad tip a further ~1.5% L (about 8 mm) inside the snout at rest, or key
  the tongue root 8 mm back at idle/move frames so no pink is visible until the attack lash.
- Check: 1_beauty az090 mouth line reaches under the eye; az000 shows no pink; 4_posed attack_f012 still shows
  the lash.

### 5. Ragged cream border on the flank
- Stage: 3 (repaint on an edge path; stage 2 loop slide if the path is missing).
- What: 1_beauty az090 and 5_reference row 1: between foreleg and thigh the cream patch has a jagged edge with a
  notch and a floating cream triangle up under the armpit; the reference has one clean convex cream belly edge
  from the throat down behind the foreleg to the thigh.
- Fix: repaint the flank border as a single edge path: from the throat seam down behind the foreleg (~2% L
  behind it) in a convex curve to the floor in front of the thigh; drop the isolated cream faces above that path.
  If no edge path exists there, slide one stage-2 loop onto it (IoU stays > 0.99).
- Check: 1_beauty az090: one continuous cream edge, no stray cream triangles; 5_reference row 1 side-by-side.

## Should-fix (short)

- Forelegs are thick columns (2_closeups front limb): taper the upper arm ~15% of its width at the elbow and
  lean the lower arm outward (stage 2 vertex moves, IoU safe). Reference arms are slender and angled.
- Flank and thigh facet noise (2_closeups hind limb wire, 3_tech slivers): a flatten pass on the flank verts
  between the cream border and the spine, and on the thigh outer face (stage 2).
- Shelf under the jaw still reads as a dark band in az090 (stage 2 r02 known): bring the throat-side verts
  forward another ~1% L.
- Tongue stretch warning (14 tris, stretch_max 5.55): add a mid ring to the tongue tube or scale the lash so
  the tube does not stretch past 3x (stage 4 keys).
- Toe pads are the right idea but small; +20% radius on the hind-toe pads so they read in 1_beauty hero.
