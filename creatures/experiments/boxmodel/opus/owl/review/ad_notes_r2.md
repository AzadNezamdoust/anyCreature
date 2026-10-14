# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 FIX / 7 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Face pieces drift (F1 major, O1 major; now gated).**
   - Fix: Stage 4: bind the eyes, brows and beak with body= (the disc weights), or weight the disc 100% to the head bone to match the rigid pieces.
   - Check: techqa drift 0.
2. **Fold-over at the neck and head-back (F2 minor, O6 minor).**
   - Fix: Stage 4: blend the weights on the neck ring.
   - Check: heatmap: no purple there.
3. **Brow (F3 minor, O4 minor).**
   - Fix: Stage 3: seat the brow into the disc so it does not stand off the face, blunt its outer end, and keep the tip inside the head silhouette.
   - Check: az000/hero: no blade tip outside the head.
4. **Tail brick (F4 minor, O5 minor).**
   - Fix: Stage 3: rebuild the tail as a tapered fan, thinner toward the tip, with 3 feather-group facets and smaller than the wingtips.
   - Check: az090/back34: a fan, not a brick.

## Should-fix (a minor from one reviewer)

- O2: a rounded disc border and no throat band.
- O3: tilt the tufts apart so they separate in profile.
- O7: flatten the radial fan on the leg into 2-3 planes.
- F3: blunt the two spikes at the wing trailing edge.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- **F1** [major/technical] where: 3_tech hero/az000/az090: eyes, brows and beak all blue; techqa piece_eye drift 4, piece_brow drift 2, piece_beak drift 1
  - what: Every face piece sits at rest but comes off the disc in a pose (the attack head tilt): eyes, brows and beak detach from the face in the attack clip.
  - fix: Stage 4: bind piece_eye, piece_brow and piece_beak with body= the disc vertices (same weights as the face) so they inherit the head transform exactly.
  - check: drift 0 on all three, no blue on 3_tech; a colour render of attack_f016 head shows rings, brows and beak on the disc.
- **F2** [minor/animation] where: 3_tech az090 (purple at the head/body seam, back) and back34 (purple along the neck seam); techqa flip 3
  - what: A residual fold-over moved from the wing root to the neck seam.
  - fix: Stage 4: blend the neck seam loop 50/50 head/body.
  - check: flip 0, no purple in 3_tech.
- **F3** [minor/pieces] where: 2_closeups head colour (near brow outer tip); 1_beauty az090 (wing trailing edge, two short spikes)
  - what: The brow's outer end is a thin blade point, and the wing's trailing edge ends in two short thin spikes.
  - fix: Stage 2/3: chamfer the brow tip to 20% of its width; merge the two trailing spikes into one blunt feather point.
  - check: Head close-up: no needle tip on the brow; sliver ≤ 4.
- **F4** [minor/form] where: 1_beauty az090 and back34, tail
  - what: The tail is one flat plank with a single top plane.
  - fix: Stage 2: split the top plane on the centre line and drop the outer feathers 5%.
  - check: az090: the tail shows two planes; IoU > 0.9.
- keep: front read: big orange eyes with glints, V brows, hooked beak, pale disc framed by the dark hood | brown/cream value split with the split, tilted tufts in the base and the rounded head | the talon strike with spread wings (wing root clean)

### Opus 5.5: FIX 7
- **O1** [major/technical] where: 3_tech, every face piece blue in all four views; techqa drift: eye 4, brow 2, beak 1
  - what: The eyes, brows and beak sit on the face at rest but come off it in poses, because they ride a different transform from the face surface. The gap is too small to see at 4_posed scale, but the gauge is right, and the idle head turn is where it will show.
  - fix: Stage 4: bind piece_eye, piece_brow and piece_beak with bone='head' (rigid, 100%). Weight every facial-disc vert above the throat band 100% head, with no neck blend.
  - check: drift 0 on all three pieces; no blue in 3_tech; the pieces sit flush in idle_f012 and attack_f016.
- **O2** [minor/form] where: 1_beauty az000, face and throat
  - what: The facial disc is a cream rectangle with straight vertical brown sides, cut off by a straight, full-width pale band across the throat. It reads as a box face with a collar, not a round disc with a rim. Round-1 item 7 was not done.
  - fix: Stage 2: slide the disc-border verts inward on the two lower cheek loops (~8% of head width) so the disc narrows to a rounded bottom. Stage 3: paint the dark rim along those loops, and replace the straight band with a V bib that points down below the beak.
  - check: az000: a rounded disc outline with a dark rim, and no band across the full head width; IoU > 0.9.
- **O3** [minor/silhouette] where: 1_beauty az090, top of the head
  - what: From the side, the two tufts overlap into one tall, narrow, vertical dark spike that reads as a horn.
  - fix: Stage 2: tilt each tuft 15° back and 10° out, and shorten it 15%, so the two tips separate in profile.
  - check: az090: two tuft tips angled back, neither vertical; the az000 tufts are unchanged.
- **O4** [minor/pieces] where: 2_closeups head colour, near brow
  - what: The brow is still a dark plank standing off the face, and its outer tip pokes past the side of the head.
  - fix: Stage 3: sink piece_brow 40% into the face and shorten the outer tip 20% so it ends inside the disc edge.
  - check: head close-up: the brow tip is inside the face outline; az090: the brow projects less than the beak.
- **O5** [minor/form] where: 1_beauty back34 and az090, tail
  - what: The tail is a thick, square-ended brick, heavier than the wing tips above it.
  - fix: Stage 2: taper the tail 30% in thickness toward the tip and chamfer the end into a blunt point.
  - check: back34: the tail ends in a taper, not a square cap; sliver ≤ 1%.
- **O6** [minor/animation] where: 3_tech az090 and back34, back of the neck (purple); techqa flip 3
  - what: A small posed fold-over sits where the head meets the back.
  - fix: Stage 4: blend the head and neck weights 50/50 on the neck loop and 80/20 on the next loop down.
  - check: no purple at the neck in 3_tech; flip 0.
- **O7** [minor/form] where: 2_closeups hind limb colour and wire, where the leg meets the belly
  - what: A radial fan of about 8 triangles meets at one vertex and shows as a star of facets on the feathered leg.
  - fix: Stage 2: dissolve alternate spokes into 4–5 bigger planes, or log a small inset at the pole.
  - check: hind close-up: no star of facets, and no vertex there with more than 6 edges.
- keep: front read: big orange eyes with black pupils and glints, V brows, beak, pale face on a brown head | back34: rounded head dome; the split-tip tufts from the front | feathered cream legs with tapered toes and dark talons, the talon strike, and clean wing roots (no purple at the shoulders)

