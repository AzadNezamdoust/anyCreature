# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 FIX / 7 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Eye beads drift in the attack (F1 major, O1 major; now gated).**
   - Fix: Stage 4: bind the eye beads with body= (the face skin weights) so they ride the face.
   - Check: techqa drift 0; 4_posed attack frames show both eyes.

## Should-fix (a minor from one reviewer)

- F2: point each claw along its toe (the outer claw forward, not sideways) and vary the sizes.
- F3: taper the forelegs, the wrist about 75% of the shoulder width (stage 2).
- O2: a broader, lighter chest plane instead of a stripe.
- O3: paint the inner-ear face as a cupped plane, not a bar.
- O4: move the front paws back under the hump (stage 2, within IoU).

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- **F1** [major/technical] where: 3_tech hero/az000/az090: both eyes blue; techqa piece_eye drift 2
  - what: The eye beads sit at rest but come off the face in a pose (the attack head drop/lift, f011/f022): eyes will float or sink into the skull in the attack clip.
  - fix: Stage 4: bind piece_eye with body= the eye-socket vertices (or bone='head' with the same weights as the face) so the beads inherit the head transform exactly.
  - check: drift 0 on piece_eye, no blue on 3_tech; a colour render of attack_f022 head shows both beads in their sockets.
- **F2** [minor/pieces] where: 2_closeups hind limb colour (near hind paw front-left corner, far forepaw) and front limb colour (far paw)
  - what: Claws are four identical radial cones per paw; the outer claw of each paw pokes sideways past the paw's side silhouette instead of forward from a toe.
  - fix: Stage 3: angle all claws within ±10° of the paw axis, shorten the two outer claws 20%, root each in its toe bump.
  - check: az000 and back34: no claw outside the paw's side outline.
- **F3** [minor/form] where: 1_beauty az000, forelegs
  - what: Forelegs are still constant-section posts: the wrist is as wide as the shoulder (round-1 [O] note only partly done).
  - fix: Stage 2: narrow the wrist loop 15% and flatten the front of the forearm; IoU > 0.9.
  - check: az000: the leg visibly narrows below the elbow.
- keep: az090: shoulder hump is the highest point, head carried low, all in the base | broad dished face: pale muzzle block, black nose pad with a straight bottom edge, round half-disc ears | two-tone legs with plantigrade paws and toe bumps; clean base tech (hit/float/zfight/flip 0)

### Opus 5.5: FIX 7
- **O1** [major/technical] where: 4_posed attack_f011 and attack_f022, head; 3_tech, both eyes blue; techqa piece_eye drift 2
  - what: The eye beads do not ride with the head. In both attack frames the eye dots are gone (left inside the skull as the head drops and lifts), while every idle and move frame shows them. The bear attacks eyeless. The gauge and the eye agree.
  - fix: Stage 4: bind piece_eye with bone='head' (rigid, 100%) and weight the eye-socket ring verts 100% head, so the socket and bead share one transform. No body= transfer for the eyes.
  - check: techqa piece_eye drift 0; no blue in 3_tech; a dark eye dot on the near side in attack_f011 and attack_f022.
- **O2** [minor/colour] where: 1_beauty hero, front edge of the near shoulder; az090, the strip between cheek and shoulder
  - what: The lightened chest shows only as a narrow yellow-olive vertical stripe down the shoulder front. It reads as a hue seam, not a lighter chest.
  - fix: Stage 3 repaint: keep the light tone on the front-facing chest faces between the forelegs only, and take it off the side faces. Make it the body hue +8–10% value, with no shift toward yellow.
  - check: az090 reads one brown from cheek to elbow; the hero shoulder has no yellow strip; the az000 chest still reads lighter.
- **O3** [minor/face] where: 1_beauty az000 and 2_closeups head colour, ear fronts
  - what: The inner-ear marks are thin, tilted tan bars. They read as slots, not cupped ears.
  - fix: Stage 2: log an inset on each ear's front face at ~60% and push it back ~20% of ear depth. Stage 3: paint the inset light brown.
  - check: az000: each ear reads as a cupped half-disc with a rounded lighter centre.
- **O4** [minor/form] where: 1_beauty az090, forelegs
  - what: The forearms rake about 20° forward, so the front paws land well ahead of the hump peak. The bear looks braced backward instead of carrying its weight on the shoulders.
  - fix: Stage 2: slide the wrist and paw loops back ~8% of body length so the forearm stands near vertical. Leave the elbow where it is.
  - check: az090: the forearm is within 5° of vertical and the paw sits under the front half of the hump; IoU > 0.9.
- keep: az090: the shoulder hump is the highest point and the head is carried low, both in the base mesh | az000: broad face, round half-disc ears, pale muzzle with a black top-front nose pad | plantigrade paws with toe bumps, dark claws and the darker lower legs

