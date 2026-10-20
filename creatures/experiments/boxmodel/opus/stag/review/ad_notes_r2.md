# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 FIX / 7 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Mane rim outline (F1 major, O2 minor).**
   - Fix: Stage 3: sink the border vertices of the mane shell 0.5-1 cm under the skin so no light rim catches, or paint the rim faces the mane colour.
   - Check: head close-up: no thin light outline around the mane.
2. **Mane bib hides the throat (F2 minor, O2 minor).**
   - Fix: Stage 3: narrow the front of the mane to about 60% of the chest width, with a V hem.
   - Check: az000: the throat shows.
3. **Lowest tines cross the ears (O1 major; the orchestrator checked the head close-up).**
   - Fix: The lowest tines sprout in a bunch at the ears and cross the left one. This is the error the owner found in the original crop. Stage 3: move the brow-tine root about 15% of the beam length up the beam, and point it forward over the face, not sideways. Stagger the lower tines along the beam so they do not fan out of one point. Optional, stage 2: rotate the ears about 15 deg back.
   - Check: hero/az000: background visible between every tine and the ear; hit 0.
4. **Tail tab (O4 minor, F3 minor).**
   - Fix: Stage 3: seat the tail into the rump with the root sunk, so no pale tab stands proud in az090, and remove the slivers at its root.
   - Check: az090: no tab; no slivers at the tail root.

## Should-fix (a minor from one reviewer)

- O3: stop the pale jaw paint at the lower jaw line, so there are no stripes up the muzzle.
- F4: loop-slide the lower-leg rings to uneven spacing.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- **F1** [major/pieces] where: 1_beauty hero (mane top border on the neck) and az000 (light line under the hem across the chest); 2_closeups head colour (whole mane border)
  - what: The mane shell's attachment rim sits at the surface and catches light: a thin pale outline traces the entire mane border, reading as a sticker edge.
  - fix: Stage 3: sink the rim a further 2-3% of neck width so the rim's side faces are inside the neck, and paint the rim faces the mane colour.
  - check: Head close-up: no pale line anywhere on the mane border; hero shows the mane as a colour region only.
- **F2** [minor/pieces] where: 1_beauty az000, neck
  - what: From the front the mane is still a full-width bib over the neck and chest with a near-straight hem; the throat line does not show.
  - fix: Stage 3: narrow the mane front 20% and raise the hem 10% at the centre, keeping 3 unequal clumps.
  - check: az000: body brown visible either side of the mane on the neck.
- **F3** [minor/technical] where: 3_tech back34, tail root (yellow)
  - what: One sliver at the tail root; 4 slivers total on the body.
  - fix: Stage 2: merge the tail-root sliver into the rump loop.
  - check: sliver 0 at the tail in 3_tech.
- **F4** [minor/form] where: 2_closeups front limb wire, cannons
  - what: Each lower leg carries 5-6 evenly spaced ring loops (uniform ring-band tell); not visible in colour but it is in the wire.
  - fix: Stage 2: remove every other cannon loop (logged), keep the knee and fetlock loops.
  - check: Front limb wire: ≤ 3 loops per cannon; IoU > 0.9.
- keep: side silhouette: rack, deep chest, slender legs with knees and hocks, small solid black hooves | the rebuilt antlers: swept beam, forward brow tine, varied tines, crown cups, a lyre in az000, ear clear | rump patch with the hanging tail, the palette, and the head-down charge (flip 0)

### Opus 5.5: FIX 7
- **O1** [major/pieces] where: 1_beauty hero and az000, antler base; 2_closeups head colour and antlers colour
  - what: The rebuilt rack still fails in three ways. (1) In hero, the base tines fan out of one point over the ears, and the lowest tine crosses the ear (clearest on the image-left ear). (2) In az000, the brow tines stick out sideways just above the ears and read as a second, pale pair of ears. The bez and trez stand as a parallel pair of upright spikes, a comb. (3) At close range every tine is a dark cone stuck onto the beam, with no node.
  - fix: Stage 3, piece_antlers: rotate the brow tines ~35° about the vertical toward the face so they point forward over the brow. Move the bez up to ~25% of beam length and the trez to ~50%, pointing ≥ 20° apart. Flare each tine root 1.3× and sink it 30–40% into the beam. Bend the upper beams 10–15° inward for a lyre. Keep the overall height and spread.
  - check: hero: ≥ 1 tine width of daylight between every tine and the ears; az000: no horizontal pale spike above the ears, and a lyre outline; antlers close-up: the tine roots blend into the beam with no dark break; hit 0.
- **O2** [minor/form] where: 1_beauty az000, neck; 2_closeups head colour and antlers colour, the mane border
  - what: The mane is still a dark bib as wide as the chest in az000, and it hides the throat. At close range its top rim shows as a thin light outline around the collar, so it reads as a separate shell.
  - fix: Stage 3, piece_mane: narrow the front 20% and lift the front hem ~5% of neck length so the throat shows between the sides. Sink the top rim another 1–2% under the skin. Cut the lower edge into 3–5 unequal clumps.
  - check: az000: brown throat visible between the mane sides; head close-up: no light line along the mane border; zfight and sliver stay 0.
- **O3** [minor/face] where: 1_beauty az000, muzzle
  - what: The pale jaw paint wraps up the muzzle sides. From the front it shows as two pale diagonal strokes flanking the nose, like fangs.
  - fix: Stage 3 repaint: move the pale border down one loop so it stays under the jaw, or join it into one pale chin band below the nose.
  - check: az000: no separate pale strokes beside the nose; az090 still shows the pale jaw line.
- **O4** [minor/pieces] where: 1_beauty az090, tail; 2_closeups hind limb colour, top right; 3_tech az090 and back34, yellow at the tail root
  - what: The tail still stands proud of the rump as a pale tab in az090. At close range it is a grey curled shell stuck on the rump, and it carries slivers at the root.
  - fix: Stage 3: pull the tail in 50% so its back face follows the rump curve. Make it a short hanging wedge in the rump-patch colour, with no curl. Merge the root slivers.
  - check: az090: the rump outline is unbroken; hind close-up: the tail reads as part of the patch; no yellow at the tail in 3_tech.
- keep: side silhouette: deep chest, slender legs with knees and hocks, small solid black hooves | a tall rack with crowned tips, the pale jaw line, the rump patch and the warm red-brown palette | the head-down antler charge in attack, with flip 0

