# owl (abc/c1): art-director notes, team round

Reviewer: art director (Fable 5.1). Packet: review/1_beauty.jpg, 2_closeups.jpg, 3_tech.jpg, 4_posed.jpg,
5_reference.jpg, techqa.json. All six images looked at; crops of the hero head, az090 head, az000 feet and the
az090 tail root zoomed.

## Score: 6 / 10. Verdict: FIX.

Reads as a horned owl in one glance from every view (tufts, orange eyes, hooked beak, cream belly, dark folded wing
over a brown flank). Tech is clean (hit 0, float 0, z-fight 0, slivers 0.5%, fold-overs under both limits, drift 0).
What keeps it off 7: the face is two goggles instead of a facial disc, the brows are dark planks floating off the
skull, the feet are tan bricks, and the tail is a lump, not a fan. These are the four things a buyer zooms on.

## Keep (must not regress)

- Stage-1 silhouette: egg body, pointed ear tufts, the folded-wing step on the flank (5_reference side/front/rear
  match the sheet in outline).
- The colour read of the wing: dark coverts + darker primaries on a brown flank, cream belly (az090, az135). Round
  s3 r05 fixed skin poking through the plate; keep the plate clearance.
- The clean tech sheet: 0 hit / 0 float / 0 z-fight, fold-overs 9 under limit, blink closes (idle f024).

## Must-fix (ordered by visual damage; max 5)

### M1. Brows float off the skull as dark planks
- Stage: 3.
- What I see: hero crop and az090: the V brow is a thin dark slab hovering above the eye ring with daylight under
  it; az000: both brow tips jut sideways past the head outline at eye level like a second pair of ears; the
  brow carries all 8 slivers in techqa.json (piece_brow). The heatmap reads it as "clean" because nothing passes
  through; my eye says it is a floating piece in the beauty views, which is a blocker by ART_DIRECTOR.md §1.
- Fix: rebuild the brow as a wedge seated in the skin: inner end at the beak root (on the disc rim), outer end
  running up into the tuft base; thickness 20-25 mm (~6% of head width, the current slab is ~5 mm); sink the
  underside 8-10 mm into the skin (raycast seat like the disc) so there is no gap; keep the outer tip inside the
  head outline in the front view (pull it in ~10% of head width). Remove the slivers by giving the wedge 3 faces
  per side, not a fan.
- Check: 1_beauty hero and az000: no gap between brow and eye ring, no brow tip outside the head silhouette;
  2_closeups head wire: brow reads as a wedge; techqa.json piece_brow sliver 0.

### M2. Face is two goggle rings, not a facial disc
- Stage: 3.
- What I see: az000 and hero: two separate cream rings with dark rims, a brown wedge between them, and the eye
  domes bulge beyond the head width (az000) and in front of the brow line (az090 crop). Reference front: one cream
  heart-shaped disc from the brow line to the beak tip, dark rim only on its outer edge, eyes sitting inside it
  with the beak between them.
- Fix: replace the two discs with one cream disc piece shaped as a heart/figure-8: width 90% of head width, top at
  the brow line, bottom at the beak tip, dark rim 10 mm wide on the outer edge only (none between the eyes).
  Eye domes: radius -15% (currently ~22% of head width each; target ~18%), sink the dome centre 30% of its radius
  into the head so the dome does not pass the head outline in az000 or the face plane in az090. Beak: move its root
  up to sit between the eyes (currently it hangs below the eye line), length unchanged.
- Check: 5_reference front vs az000: one cream disc, eyes inside the head outline; 1_beauty az090: no dome in
  front of the brow line; 2_closeups head colour.

### M3. Feet are tan bricks
- Stage: 2.
- What I see: az000 feet crop and hero: each foot is a square tan block as wide as the leg (~9 cm) with three
  talons glued to its front edge; the cream leg ends in a flat tan "boot". Reference: a feathered cream leg down to
  the ankle, then three narrow toes with talons, foot width under half the leg's.
- Fix (stage-2 vertex moves on the carve, r04 narrowed it to 72%; go further): foot verts (z < 0.045) narrowed
  to 50% about the leg line x 0.067; foot top lowered to z 0.03 (toe height ~5% of body height); push the front
  foot verts forward 15 mm so the toes lead and the talons sit at the toe tips, not under a block. Keep the cream
  leg paint down to z 0.045 (ankle), tan only on the toes.
- Check: 1_beauty az000 and hero: feet read as toes under a feathered leg; the stage-2 IoU gate (> 0.9, front and
  side) still passes; 3_tech feet grey.

### M4. Tail is a lump, no fan
- Stage: 3.
- What I see: az090 tail crop and 2_closeups hind limb: the carved tail is a short wedge under the primaries, half
  of it painted tan so it reads as a flesh lump sticking out behind the foot; top view (5_reference) shows no fan
  at all against the reference's wide dark fan.
- Fix: add a tail fan piece: 5 flat dark (#4a3424) feathers, 9 mm thick like the wing plate, fanned 60 degrees in
  the top view, length ~25% of body length (10 cm) from the tail root, pitched down 20 degrees; bind body=tail
  bone. Paint the carved tail wedge dark brown so no tan shows behind the legs (tan only on toes and beak).
- Check: 1_beauty az090 and back34: a dark fan behind the body, no tan under the primaries; 5_reference top: a
  fan silhouette; techqa float 0 and hit 0 on piece_tail.

### M5. Belly cream is one blob with a saw-tooth border
- Stage: 3.
- What I see: az000 and hero: the cream covers the whole chest from under the beak to the legs in one block
  with a coarse triangle saw edge. Reference front: brown upper chest, a chevron band of mid tan (#b08a64) at
  mid-body, cream only on the lower belly; the cream never reaches the face.
- Fix: repaint by loops: chest above z 0.40 brown; a mid-tan band z 0.33-0.40 (the existing bib loop at z 0.345 is
  the border; add one logged loop at z 0.40 if needed); cream below. Snap the cream border to the loop so the edge
  is a clean line, and let the tan band carry the chevron read.
- Check: 1_beauty az000 next to 5_reference front: three value bands on the chest, straight loop borders; colour
  count stays <= 8.

No STAGE-1 UNLOCK requested. The base carries the identity (tufts, egg, wing step) and every item above sits in
stages 2 and 3.

## Should-fix (short)

- Stage 4: the attack is a forward lunge with the wings only lifting (NOTES.md "remaining"). Bind the wing plate to
  the wing bone (bone=, not body=) and swing it 45-60 degrees out in the attack's spread frame; the fused carve
  wing can stay. Check 4_posed attack_f016: the plate leaves the flank.
- Stage 2: head is narrower than the body in az000; the reference head is as wide as the body. Widen the head
  6-8% (inside the IoU gate) at the eye line. Helps M2.
- Stage 3: the beak is a flat dark blade in az090; give it a 15 mm root width so it reads hooked, not knife-thin.
- Stage 3: the head "cap" in back34 is a flat lid; a slight dark crown patch (brief dark brown) would separate
  head from body in the rear view.
