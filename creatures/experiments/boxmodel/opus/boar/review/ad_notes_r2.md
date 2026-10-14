# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 SHIP / 7 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Crest needles and fin (O1 major, F1 minor).**
   - Fix: Stage 3: blunt every clump tip into a small flat end instead of a needle. Vary the clump heights, and thicken the crest from the front to about half its height.
   - Check: az000: a mane strip, not a fin; az090: not a saw; no slivers on the crest.
2. **Saddle blanket (F2 minor, O2 minor).**
   - Fix: Stage 3: repaint the saddle border along staggered faces, feathered onto the neck and flank, instead of a straight-edged quadrilateral.
   - Check: hero/az090: no straight border.
3. **Ears (F3 minor: slivers; O4 minor: donkey cones).**
   - Fix: Stage 2: remove the ear-tip slivers by moving the tip vertices to widen the triangles. Shorten the ears about 15% and tilt them forward and out about 20 deg.
   - Check: no slivers on the ears; az090: the ears fold forward.
4. **Tusk hook inside the profile (F4 minor, O5 minor).**
   - Fix: Stage 3: lengthen the tusk and curve it up and back, so its tip breaks the snout profile by 3-4 cm in az090. Keep hit at 0.
   - Check: az090: a tusk hook visible above the snout line.

## Should-fix (a minor from one reviewer)

- O3: nostrils as tilted ovals, not rectangles.
- F5: a mouth line and a brow ridge.
- O6: leg stockings a step lighter.

## Appendix: both reviews verbatim

### Fable 5.1: SHIP 7
- **F1** [minor/pieces] where: 1_beauty az000 (crest head-on) and az090 (crest tips); 3_tech back34 and hero yellow on the crest; techqa piece_crest sliver 8
  - what: From the front the crest is a thin fin about 1/4 as wide as it is tall, and every clump still ends in a needle point (8 slivers).
  - fix: Stage 3: widen each clump base 1.5x and offset alternate clumps +/-1 cm sideways; blunt each tip to a >= 1.5 cm flat.
  - check: az000 crest width >= 40% of its height; crest sliver 0.
- **F2** [minor/colour] where: 1_beauty hero and az090, shoulder saddle
  - what: The dark saddle is still a hard-edged trapezoid with a straight vertical border at the neck; it reads as a blanket.
  - fix: Stage 3: move the border onto loops that run from the crest down the shoulder blade to the elbow point in a V, stepped on existing loops; no straight vertical border.
  - check: hero: no straight vertical colour edge on the shoulder at 128 px.
- **F3** [minor/technical] where: 3_tech az000 and hero: yellow lines along both ear inner edges; techqa body sliver 8
  - what: The ear tips are still sliver triangles (round-1 check 'ear slivers gone' not met).
  - fix: Stage 2: merge the ear-tip verts or widen each tip to a >= 1 cm flat; thicken the root.
  - check: No yellow on the ears in 3_tech; body sliver <= 4.
- **F4** [minor/pieces] where: 1_beauty az090, tusk
  - what: The tusk lies flat against the muzzle side; its tip does not break the profile silhouette (hit 0 is met, the silhouette check is not).
  - fix: Stage 3: rotate each tusk a further 10-15 deg outward and forward so the tip clears the muzzle by ~4 cm.
  - check: az090 silhouette shows the tusk tip; hit 0.
- **F5** [minor/face] where: 2_closeups head colour; 1_beauty hero
  - what: No mouth line behind the snout disc; the eye is a small dot with no brow ridge.
  - fix: Stage 2: inset a crease from the disc back 1/3 of the head length; pull 2-3 brow verts out ~1 cm. Stage 3: scale piece_eye 1.2x.
  - check: Head close-up shows a mouth line and a brow; the eye reads in hero at 128 px.
- keep: front-heavy hump in the base and the long wedge head (az090) | fused crest ridge of varied height, dusky snout disc, cream tusks clearing the lip (hit 0) | cloven hooves, hock angles, flip 0 in all poses

### Opus 5.5: FIX 7
- **O1** [major/silhouette] where: 1_beauty az000 (above and between the ears); az090, back34 and 2_closeups crest
  - what: The crest is now one strip, tallest over the hump and leaning back, but every clump still ends in a sharp triangular point. From the side it reads as a saw. From the front, which is the charge view, it shows as a single narrow spike above the ears that reads as a horn.
  - fix: Stage 3: blunt each clump by cutting its top ~20% to a short flat or split tip. Widen each clump sideways to ≥ 50% of its height and roll alternate clumps ±12° about the spine so the ridge fans out. Lower the tallest clump ~15%.
  - check: az000 shows at least 2 clumps side by side and no single point above the ear tips; az090 reads as a mane; crest sliver ≤ 2
- **O2** [minor/colour] where: 1_beauty az090, hero and back34, side of the shoulder hump
  - what: The dark shoulder saddle is still a hard quadrilateral patch with a straight horizontal bottom edge. Round-1 item 6 was not done.
  - fix: Stage 3: repaint the saddle on faces that taper down from the crest in a V ending near the elbow, with the border on existing diagonal loops.
  - check: in az090 the saddle border follows two diagonal loops and has no horizontal edge
- **O3** [minor/face] where: 1_beauty az000 and hero snout disc
  - what: The nostrils are two tall black rectangular slots, so the snout disc reads as a power socket.
  - fix: Stage 2 (logged): re-inset each nostril as a 5–6-sided teardrop about 60% of its current height, tilted 20° outward at the top. Stage 3: paint them near-black.
  - check: at az000 thumbnail size it reads as a snout, not an outlet
- **O4** [minor/form] where: 1_beauty az090 and hero ears; 3_tech az000 (yellow on the inner ear edges)
  - what: The ears are fixed from the front, but in profile they still stand as tall, narrow, upright cones (a donkey read), and the ear slivers remain.
  - fix: Stage 2: move the ear tips down ~20% and tilt them 15° back. Widen the base front-to-back ~20% and merge the thin inner-edge strip.
  - check: in az090 the ear tip sits below the front crest clump; no yellow on the ears in 3_tech
- **O5** [minor/silhouette] where: 1_beauty az090 tusk
  - what: The tusk reads against the cheek, but its tip stays inside the head outline, so the profile has no tusk hook. This was the round-1 check.
  - fix: Stage 3: rotate the tusk ~10° further out and forward and lengthen it ~15%, so in profile the tip clears the snout's top line by 2–3 cm. Keep the root inside the jaw.
  - check: in az090 the tusk tip shows against the background; techqa hit stays 0
- **O6** [minor/colour] where: 2_closeups front limb colour
  - what: The dark leg stockings go near-black in shadow, so the leg facets disappear in the close-up.
  - fix: Stage 3: raise the stocking colour's value by 10–15% and keep the hooves the darkest value.
  - check: the leg facets read in the front-limb close-up, and the hooves stay distinct from the legs
- keep: az090 silhouette: high shoulder hump, long wedge head, flat disc snout, thin tufted tail | upward tusks rooted in the jaw with hit 0; the far tusk tip clears the snout in hero | clean tech and deformation (flip 0, hit 0, zfight 0) with cloven hooves and hock angles

