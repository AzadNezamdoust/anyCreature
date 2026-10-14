# Art-direction notes, round 3 (reconciled, K=3 pass)

Round-3 scores (Fable 5.1 / Opus 5.5): 8 SHIP / 7 FIX.

**The owner authorised a stage-1 unlock for this pass, for these items only: the tail, if the curl is body geometry, and the cannon ring loops.** Follow the unlock procedure in `REPAIR.md`, and change nothing else in stage 1. Every other rule holds: stage-2 IoU > 0.9 against the new stage 1, stage 3 never edits the base, all gates pass.

Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both reviewers' keep lists (appendix). Check every item in your own `--review` packet, which shows the idle pose, before you call it done.

## Must-fix, in order

1. **Tail tab (O major, F minor x2).**
   - Fix: Delete the curled shell and the side flap. Build the tail as one short hanging wedge: about 8% of the body length, its thickness about 40% of its width, centred over the rump patch, root sunk 30%, cream underneath and brown on top. If the curl is body geometry, move it onto the rump curve: in stage 2, or through the stage-1 unlock.
   - Check: az090: the rump outline is unbroken except a short hanging wedge; back34: one continuous cream patch with the tail on the centre line; hind close-up: no curl; hit 0, sliver 0.
2. **Mane bib hides the throat (F minor, O minor).**
   - Fix: Stage 3, piece_mane: scale the front 40% of the mane to about 60% of the neck width about the centre line. Lift the front hem into a centred, symmetric V.
   - Check: az000: body brown on both sides of a centred V bib, and the throat reads.
3. **Tines read as a pinned-on comb (F minor, O minor).**
   - Fix: Stage 3, piece_antlers: vary the tine lengths 0.6-1.3x and their angles at least 15 deg from each other. Flare each root 1.3x and sink it 30% into the beam, and taper the beam 30% from base to crown. Move the near beam's lowest tine 5% of the beam length further up.
   - Check: attack_f009: no two tines parallel or equal; head close-up: roots blend into the beam; hero: at least one tine width of daylight between the lowest tine and the ear; hit 0.
4. **Even ring bands on the lower legs (F minor, O minor).**
   - Fix: Stage 2: slide the cannon loops to uneven spacing, or use the stage-1 unlock to remove every other cannon loop. Flatten the knee ring into a flat-fronted block.
   - Check: front limb wire: no even banding; colour: no bead ring at the knee; IoU > 0.9.

## Appendix: both round-3 reviews verbatim

### Fable 5.1: SHIP 8
- round-2 item "Mane rim outline": **done**. Head close-up and hero show the mane as a colour region only; no pale rim anywhere on the border.
- round-2 item "Mane bib hides the throat": **partly**. The hem is scalloped now, but in az000 the mane still spans about 80% of the neck width; only slivers of body brown show at the sides and the throat does not read.
- round-2 item "Lowest tines cross the ears": **done**. hero/az000/head close-up: brow tines point up and forward from above the ears with background between every tine and both ears; hit 0. The near beam's lowest tine still roots within ~5 px of the ear's top edge in the hero.
- round-2 item "Tail tab": **partly**. Root slivers are gone (sliver 0), but the tail still stands proud of the rump as a cream-faced tab in az090 and reads as a curled grey shell in the hind limb close-up.
- round-2 item "O3 pale jaw strokes": **done**. az000: no separate pale strokes beside the nose; az090 keeps the pale jaw line.
- round-2 item "F4 leg ring loops": **not**. Front limb wire: about 10 evenly spaced rings per cannon; only faint banding in colour.
- **F1** [minor/pieces] where: 1_beauty az090 tail behind the rump; 2_closeups hind limb colour, top right
  - what: The tail still stands off the rump outline as a flat cream-faced tab with a brown cap; at close range it is a curled shell with a concave inner face, not a hanging tail.
  - fix: Stage 3: rebuild piece_tail as a short hanging wedge (length ~8% of body, root sunk 50% into the rump, back face following the rump curve), cream underneath and body brown on top.
  - check: az090: rump outline unbroken except a short hanging wedge; hind close-up: no concave curl; sliver stays 0.
- **F2** [minor/pieces] where: 1_beauty az000 neck; hero neck front
  - what: The mane is still a near full-width dark bib down the front of the neck, so the throat line does not read.
  - fix: Stage 3: narrow the mane front 25% (to ~60% of neck width) and lift the hem centre 8% into a V, keeping three unequal clumps.
  - check: az000: body brown visible either side of the mane on the neck; the throat reads.
- **F3** [minor/pieces] where: 2_closeups head colour and antlers colour, every tine
  - what: Tines are 4-sided cones seated on the beam surface with a hard base edge and no node; at close range they read as pinned on (darker than the beam in the close-up light).
  - fix: Stage 3: flare each tine root 1.3x and sink it 30% into the beam; move the near beam's lowest tine root 5% of beam length further up from the ear.
  - check: Antlers close-up: no hard base ring at any tine root; hero: at least one tine width of daylight between the lowest tine and the ear; hit 0.
- **F4** [minor/form] where: 2_closeups front limb wire, cannons; faint banding on the az000 lower legs
  - what: Each lower leg carries about 10 evenly spaced ring loops (uniform ring-band tell).
  - fix: Stage 2: remove every other cannon loop (logged), keep the knee and fetlock loops; IoU > 0.9.
  - check: Front limb wire: 4 or fewer loops per cannon; IoU > 0.9.
- **F5** [minor/colour] where: 1_beauty back34, below-left of the rump patch
  - what: A second small pale quad (the tail underside) sits detached below the rump patch with a dark gap, reading as a floating pale chip.
  - fix: Stage 3: with the tail rebuild, centre the tail under the patch and paint its underside the patch cream so the two join.
  - check: back34: one continuous pale shape on the rump.
- keep: Side silhouette: rack, deep chest, slender legs with knees and hocks, small solid black hooves | The rack: swept beams, lyre in az000, forward brow tines clear of the ears, crown cups, hit 0 | Warm red-brown palette with the pale jaw line and cream rump patch; the head-down charge with flip 0

### Opus 5.5: FIX 7
- round-2 item "Mane rim outline": **done**. No light outline along the mane border in the head close-up or the hero view; zfight and sliver 0.
- round-2 item "Mane bib hides the throat": **not**. az000: the mane still covers the whole neck. Its hem is near-straight with one notch on the image-left side, and no throat shows.
- round-2 item "Lowest tines cross the ears": **done**. hero and az000: daylight between every tine and both ears; hit 0. The lowest tine now sits about 30% up the beam and points forward and up.
- round-2 item "Tail tab": **not**. az090: a pale tab still breaks the rump outline. Hind close-up: a grey curled shell with a plate stands on the rump. back34: a disc plus a separate flap.
- round-2 item "(should) O3 jaw paint": **done**. az000: no pale strokes beside the nose; az090 keeps the pale jaw line.
- round-2 item "(should) F4 uneven lower-leg rings": **not**. Front limb wire: still 5-6 evenly spaced loops per cannon, and the knee reads as a bead ring in colour.
- **O1** [major/pieces] where: 2_closeups hind limb colour, top right (rump); 1_beauty az090, rump edge; 1_beauty back34, rump patch
  - what: The tail still stands proud of the rump. At close range it is a grey curled scroll, with a flat plate sticking out at an angle. In az090 it breaks the rump outline as a pale tab. In back34 it is a cream flap beside the rump disc, with a dark notch between them. The heatmap is clean here because the tail neither floats nor intersects; the eye is right.
  - fix: Stage 3: delete the curled shell and the side flap. Build the tail as one short flat wedge: about 8% of body length, thickness about 40% of its width, hanging on the centre line over the rump patch, root sunk 30%, cream underneath and brown on top. If the curl is body geometry, use stage 2 instead: move its verts onto the rump curve and flatten them into the patch, IoU > 0.9.
  - check: az090: the rump outline is unbroken. back34: one cream patch with the tail hanging on the centre line. Hind close-up: no curled shell. hit 0, sliver 0.
- **O2** [minor/pieces] where: 1_beauty az000, neck; 1_beauty hero, throat
  - what: From the front the mane covers the full neck width with a straight hem and a notch on one side only. In hero its front lip overlaps the throat as a flap.
  - fix: Stage 3, piece_mane: scale the front 40% of the mane to 60% width about the centre line. Lift the front hem 10% of neck length into a centred V, and make the hem clumps symmetric about the centre.
  - check: az000: body brown shows on both sides of a centred V bib, with no one-sided notch.
- **O3** [minor/pieces] where: 4_posed attack_f009 and f018, rack; 1_beauty hero; 2_closeups antlers colour
  - what: The tines are identical straight cones at the same angle and even spacing along each beam, so the charging rack reads as a fishbone comb. Each tine root is a hard cone set on the beam with no node, and the beam keeps one section from base to crown.
  - fix: Stage 3, piece_antlers: vary tine lengths 0.6-1.3× and angles by at least 15° from each other. Flare each root 1.3× and sink it 30% into the beam. Taper the beam 30% from base to crown.
  - check: attack_f009: no two tines are parallel or equal in length. Head close-up: the tine roots blend into the beam. hit 0.
- **O4** [minor/form] where: 2_closeups front limb colour and wire; 1_beauty az000, legs
  - what: 5-6 evenly spaced loops per cannon, and a bead ring at each knee and fetlock, read as bamboo segments.
  - fix: Stage 2: dissolve every other cannon loop (logged). Flatten the knee ring so the knee is a flat-fronted block that bulges backward, not a ring.
  - check: Front limb wire: at most 3 loops per cannon. Colour: no bead ring at the knee. IoU > 0.9.
- keep: side silhouette: tall rack, deep chest, slender legs with knees and hocks, small solid black hooves | ears clear of the rack in hero and az000 (hit 0), with a lyre spread of the beams in az000 | the long tapered head with black nose and pale jaw line in profile, the warm red-brown palette and the dark mane collar with no rim outline

