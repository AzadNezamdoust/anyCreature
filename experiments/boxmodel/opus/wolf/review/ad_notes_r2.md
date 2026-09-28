# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Ruff reads as a collar (F1 major, O4 minor).**
   - Fix: Stage 3: break the nape ring into 3-4 overlapping clumps of unequal length. Sink the top rim into the neck so the ruff grows out of it with no shelf. Paint the top surface the neck grey, not lighter.
   - Check: back34/az090: no ring shelf at the nape; hero reads as a mane.
2. **Chest keel and underline (O2 major, F4 minor).**
   - Fix: Stage 2: spread the sternum drop over the 2-3 chest vertices on each side of the centre, so the keel is a rounded curve with no point between the forelegs. Deepen the chest toward 1.3x the waist depth within the IoU gate. Stage 3: paint the keel bib cream.
   - Check: az000: no dark wedge below the bib; az090: the underline curves up into the tuck-up.
3. **Legs hang under a body hem (O1 major).**
   - Fix: Stage 2: slide the lowest body loop up and in over each leg top, so no ledge or shadow line overhangs the leg. Taper the forearm and cannon, the wrist about 70% of the elbow width. Blend the paw into the pastern, with no boot flare.
   - Check: hero: no hem shadow line; az090: the legs taper. The IoU floor stays 0.9; if it blocks, log the item as partly done.
4. **The move clip reads as idle (F2 minor, O6 minor).**
   - Fix: Stage 4 keys: a diagonal-pair trot. At the quarter frames the front-left and hind-right legs swing forward about 25 deg while the other pair swings back about 20 deg, then they swap. Add a body bob of +-2% of the height with a head counter-bob.
   - Check: 4_posed: the move frames clearly differ from idle, and the feet pass under the body.

## Should-fix (a minor from one reviewer)

- F3: shrink the black socket to about 1.15x the eye.
- O3: vary the toe lengths (the two middle toes longer).
- O5: nose paint on the top-front pad only.
- O7: key the tail root about 20 deg down in every clip, so it is carried straight or low.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- **F1** [major/pieces] where: 1_beauty back34 and hero, neck behind the ears; az000 both sides of the neck; 2_closeups head colour, top edge of the ruff
  - what: The ruff is thick now but reads as a rolled collar: a uniform ring with a hard top ledge encircling the neck, lighter grey on its top surface, sitting proud of the nape like a scarf glued on rather than a mane in the form.
  - fix: Stage 3: taper piece_ruff to zero thickness along its top-rear edge and along the spine so the nape runs skull-to-withers in one line; keep the full thickness (>= 25% neck width) only at the sides of the neck and the chest bib; slide the top-rear edge down ~15% of neck length; paint the collar's top surface body grey so no lighter band shows from behind.
  - check: back34 shows no raised ring behind the ears; az090 nape silhouette is a single line from skull to withers; techqa piece_ruff flip 0 and sliver 0.
- **F2** [minor/animation] where: 4_posed move_f007 and move_f013
  - what: The move extremes are nearly identical to idle: a few degrees of leg swing, no diagonal-pair stride, no body bob (round-1 item 9 barely done).
  - fix: Stage 4: key shoulders and hips +/-20-25 deg in diagonal pairs, add a 3-5% height bob, keep paws planted through contact.
  - check: The two move frames differ visibly in leg spread at 128 px; no paw slides between contact frames.
- **F3** [minor/face] where: 2_closeups head colour and wire, eye
  - what: The socket is a black hollow about 1.5x the eye; at close range the amber eye reads as a bead in a hole.
  - fix: Stage 3: scale piece_eye 1.15x and paint the socket inset dark grey (~25% value) instead of black; or stage 2: shrink the socket inset to 1.2x the eye.
  - check: Head close-up shows the amber filling >= 2/3 of the socket; az000 still shows two eyes; float 0.
- **F4** [minor/colour] where: 1_beauty az000, chest between the forelegs
  - what: A dark grey chest keel pokes out below the V of the cream bib and reads as a dangling wedge.
  - fix: Stage 3: extend the ruff's centre clump down to the leg line, or paint the sternum tip cream on the existing loop.
  - check: az000: the cream bib reaches the line between the forelegs with no dark point below it.
- keep: az090 silhouette: wedge head, thick neck, deep chest with tuck-up, bushy brush tail with dark tip | palette: grey, dark saddle, cream bib, tan legs from wrist/hock down, amber eyes | tan toe wedges with black tips (zfight 0); body tech-clean (hit 0, float 0, flip 0.23%)

### Opus 5.5: FIX 6
- **O1** [major/form] where: 2_closeups front limb colour/wire and toes colour (leg tops); 1_beauty az090 and az000; 3_tech az000 (step and yellow slivers at the foreleg tops)
  - what: The legs are still stilts hung under a body hem. The body's lowest loop overhangs each leg top as a ledge with a dark shadow line. The forearm and cannon keep one width from elbow to paw, and the paw flares out as a separate boot. Only the repaint from round-1 item 5 was done, not the geometry.
  - fix: Stage 2: slide the body's lowest loop down and in so it meets each leg's top ring flush, with no ledge. Scale the foreleg ring at the elbow +25% and the hind gaskin +15%, tapering to the pastern. Flatten a back-of-elbow plane on each foreleg.
  - check: front-limb close-up shows no horizontal shadow line where the leg meets the body; no yellow at the foreleg tops in 3_tech; az000 foreleg width at the elbow ≥ 0.28× chest width; IoU > 0.9
- **O2** [major/silhouette] where: 1_beauty az090 underline; 1_beauty az000 and 3_tech az000 between the forelegs
  - what: The underline is still a straight box: in az090 the chest is only about 1.15× the waist depth. The sternum drop was made on one centre vertex, so a dark pointed keel now hangs between the forelegs in az000.
  - fix: Stage 2: undo the single-vertex drop. Lower the three bottom verts of the chest loop together by ~8% of body depth to make a flat brisket, and raise the belly loop in front of the stifle ~15% for the tuck-up.
  - check: az090 chest depth ≥ 1.3× waist depth; az000 brisket is flat-bottomed with no point between the forelegs; IoU > 0.9
- **O3** [minor/pieces] where: 2_closeups front limb and toes colour; 1_beauty az000 paws
  - what: The toes read as a comb of four identical tiny black spikes across the paw front, each about 1/8 of the paw width. The tan toe body barely shows.
  - fix: Stage 3: rebuild piece_toes as four pads per paw, each ~1/5 of the paw width, with the middle two 15–20% longer, splayed ±8°. Make each pad tan with black only on the last 30% (the claw), the tip angled down to the ground line.
  - check: toe close-up reads as tan toes with black claw tips; techqa zfight stays 0
- **O4** [minor/pieces] where: 1_beauty back34 nape; 2_closeups head colour/wire
  - what: The ruff is thick and correct in front, but at the nape it is one smooth ring with a hard shelf lip. It reads as a neck pillow or collar, not fur.
  - fix: Stage 3: break the ruff's top and back edge into 2–3 offset clumps (height ±20%) and chamfer the nape lip to ~45° so it runs into the neck. Keep the thickness and the chest clumps.
  - check: back34 shows a stepped mane at the nape with no single ring ledge; ruff stays hit/float/zfight 0
- **O5** [minor/face] where: 1_beauty az000 muzzle; 2_closeups head colour
  - what: The nose paint still covers the whole front face of the muzzle, so az000 shows a black muzzle end instead of a nose pad.
  - fix: Stage 3: keep black only on the upper half of the muzzle tip (the nose pad) and paint the lower half grey/cream as the upper lip, with the border on the existing mid loop.
  - check: az000 shows a black nose pad above a grey lip
- **O6** [minor/animation] where: 4_posed move_f007 vs move_f013
  - what: The move clip still has almost no stride. The legs stay under the body and both frames look like idle.
  - fix: Stage 4: key the shoulders and hips ±20–25° in diagonal pairs, add a 3–5% body bob, and lock the paws at contact.
  - check: between move_f007 and move_f013 the diagonal pairs swap front and back, and the gap between fore and hind paws changes by ≥ 30%
- **O7** [minor/animation] where: 4_posed attack_f015 and idle_f012, tail
  - what: The tail curls up over the rump like a husky or spitz. A wolf carries its tail straight out or low.
  - fix: Stage 4: cap tail-root pitch at ≤ +20° above horizontal and per-bone curl at ≤ 10° in the attack and idle clips.
  - check: in attack_f015 the tail tip stays below the withers line
- keep: az090 silhouette: wedge head, pointed ears, thick ruff and a brush tail with a dark tip read as a wolf | tech-clean mesh and pieces: hit, float and zfight are all 0, with only 4 flips on the ruff | palette: grey with a dark saddle, cream bib, tan paws, and amber eyes that now show in az000

