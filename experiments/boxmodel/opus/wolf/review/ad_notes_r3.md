# Art-direction notes, round 3 (reconciled, K=3 pass)

Round-3 scores (Fable 5.1 / Opus 5.5): 6 FIX / 6 FIX.

**The owner authorised a stage-1 unlock for this pass, for these items only: the chest keel, the legs and the paws.** Follow the unlock procedure in `REPAIR.md`, and change nothing else in stage 1. Every other rule holds: stage-2 IoU > 0.9 against the new stage 1, stage 3 never edits the base, all gates pass.

Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both reviewers' keep lists (appendix). Check every item in your own `--review` packet, which shows the idle pose, before you call it done.

## Must-fix, in order

1. **Keel wedge under the bib (F major, O major).**
   - Fix: Stage 1 (unlock) or stage 2: raise the lowest centre chest vertex to its neighbours' level and lower those neighbours about 3% of the chest depth, so the brisket is flat-bottomed with no point. Stage 3: paint the sternum faces cream down to the brisket.
   - Check: az000: the cream bib meets the leg line with no dark shape below it; 3_tech az000: no V point between the forelegs.
2. **Legs under a hem, boot paws (O major, F minor).**
   - Fix: Stage 1 (unlock):
     - Make each paw an oval pad about 1.15x the pastern width: pull the side and back verts of the bottom ring in, and push the front verts forward about 10%.
     - Taper the wrist to about 70% of the elbow width, and narrow the hind cannons to about 75% of their current width.
     - Bring the upper arm's lowest loop flush into the forearm with no crease, and do the same at the stifle.
   - Check: front and hind limb close-ups: no dark horizontal line across any leg and no bell flare; az090: the legs taper from elbow to wrist.
3. **Ruff still a torus (F major, O minor).**
   - Fix: Stage 3: break the throat part into 2-3 downward clumps of unequal length (+-25%), with the top edge sunk into the jaw and neck so no ledge shows. Taper the top-rear edge to zero along the spine. Paint the top faces the saddle dark where they meet the saddle.
   - Check: 3_tech az000: no unbroken ring; head close-up: a clumped fur edge under the jaw.
4. **Eye reads as a cube in a slot (F minor, O minor).**
   - Fix: Stage 3: flatten piece_eye to a lens no deeper than 1/3 of its width, seated flush with the socket rim, and fill at least 2/3 of the socket. Make the catchlight a small quad on the front face, and paint the socket dark grey (about 25% value).
   - Check: head close-up: a flat amber eye with a dot highlight and no white sliver; float 0.
5. **Toes form a comb (F minor, O minor).**
   - Fix: Stage 3: make the two middle toes about 20% longer and splay the outer toes +-8 deg along an arc.
   - Check: toes close-up: the middle toes lead; zfight 0.

## Should-fix

- F: push the 2-3 verts of the flank pocket in front of the thigh outward 3-4% of the body width (stage 2).

## Appendix: both round-3 reviews verbatim

### Fable 5.1: FIX 6
- round-2 item "1 ruff reads as a collar": **not**. 3_tech az000 shows piece_ruff as one uniform ring with a flat top rim round the whole neck; back34 and hero show that rim as a lighter band behind the ears; no clumps of unequal length.
- round-2 item "2 chest keel and underline": **partly**. az090 chest is ~1.3x the waist and the underline curves into the tuck-up, but az000 still has a dark grey pointed wedge hanging below the cream bib between the forelegs; the keel was neither rounded nor painted cream.
- round-2 item "3 legs under a body hem": **partly**. forearm tapers a little (wrist ~85% of elbow) but the tan paws still flare as boots with a ledge at the top rim, and the body's lowest loop still steps over the near foreleg with a shadow line in the front-limb close-up.
- round-2 item "4 move clip reads as idle": **done**. move_f007 and f013 show a diagonal-pair stride with ~25 deg swing; both frames differ clearly from idle.
- round-2 item "should-fix F3 eye socket": **partly**. socket is still a black hollow ~1.4x the eye; the amber reads as a bead in a hole.
- round-2 item "should-fix O3 toe lengths": **partly**. toes are tan with black tips now, but four equal nubs in a straight comb.
- round-2 item "should-fix O5 nose pad": **done**. black on the top-front pad only, cream lip below (hero, az000, head close-up).
- round-2 item "should-fix O7 tail carriage": **done**. tail hangs straight/low in idle and stays below the withers in attack_f015.
- **F1** [major/pieces] where: 3_tech az000 neck ring; 1_beauty back34 and hero nape; 2_closeups head colour, top-right ruff edge
  - what: piece_ruff is still one uniform ring: a flat top rim runs right round the neck as a shelf, painted body grey against the dark saddle so it shows as a lighter band behind the ears; it reads as a collar, not a mane.
  - fix: Stage 3: rebuild piece_ruff as 3-4 overlapping clumps of unequal length (+-25%); taper the top-rear edge to zero thickness along the spine and sink it 20% of neck width into the nape; keep full thickness (>= 25% neck width) only at the sides and the chest bib; paint the top faces the saddle dark grey where they meet the saddle.
  - check: 3_tech az000 shows no horizontal rim across the nape; back34 nape is one skull-to-withers line at 128 px; ruff hit/float/zfight 0.
- **F2** [major/form] where: 1_beauty az000 between the forelegs below the cream bib; hero under the bib
  - what: a dark grey pointed wedge hangs below the V of the bib and reads as a dangling flap or a third leg at thumbnail size.
  - fix: Stage 2: raise the single dropped sternum vertex back to the brisket line and spread the drop over the 2-3 bottom chest verts each side so the keel is a rounded curve. Stage 3: paint the sternum faces cream on the existing loop so the bib closes at the leg line.
  - check: az000 at 128 px shows no dark point below the bib; az090 chest depth stays >= 1.3x waist; IoU > 0.9.
- **F3** [minor/form] where: 2_closeups front limb and hind limb colour; 1_beauty hero forelegs
  - what: the tan paw is wider than the cannon with a ledge at its top rim (a boot), and the body's lowest loop still steps over the near foreleg with a shadow line.
  - fix: Stage 2: scale each paw's top ring down to the cannon width and widen the pastern 10% so paw and cannon blend; slide the body's lowest loop up and in over each foreleg top by ~5% of chest depth.
  - check: front-limb close-up shows no ledge at the paw top and no horizontal shadow at the leg top; IoU > 0.9.
- **F4** [minor/face] where: 2_closeups head colour, eye
  - what: the socket is a black hollow ~1.4x the eye; the amber reads as a bead in a hole, with a stray white sliver at its front edge.
  - fix: Stage 3: scale piece_eye 1.2x and move it outward by half its thickness; paint the socket inset ~25% value dark grey, not black.
  - check: head close-up: amber fills >= 2/3 of the socket and no white sliver; az000 still shows two eyes; eye float 0.
- **F5** [minor/pieces] where: 2_closeups front limb and toes colour
  - what: four equal tan nubs with black tips, each ~1/6 of the paw width, in a straight row: a comb.
  - fix: Stage 3: make the two middle toes 15-20% longer, splay the outer toes +-8 deg, widen each pad to ~1/5 of the paw width.
  - check: toe close-up: the middle toes lead; toes zfight 0.
- **F6** [minor/form] where: 2_closeups hind limb colour, flank above the near hind leg
  - what: a concave pocket of dark facets sits on the flank in front of the thigh and reads as a dent.
  - fix: Stage 2: move the 2-3 pocket verts outward 3-4% of body width so the flank is convex from the rib cage to the hip.
  - check: hind-limb close-up shows the flank as one lit plane; valley 0; IoU > 0.9.
- keep: az090 silhouette: wedge head, pointed ears, deep chest with tuck-up, brush tail with a dark tip carried low | palette: grey, dark saddle, cream bib, tan legs from wrist/hock down, amber eyes, black nose pad over a cream lip | tech-clean mesh (hit/float/zfight/flip 0) and the diagonal-pair trot

### Opus 5.5: FIX 6
- round-2 item "Ruff reads as a collar": **partly**. back34 and hero: the nape is now a stepped grey scruff with no ring shelf. The head close-up still shows the cream throat band as one smooth scarf with a hard top edge, and 3_tech az000 shows a full torus round the neck.
- round-2 item "Chest keel and underline": **partly**. az090: the underline now curves up into a clear tuck-up (chest about 1.4x waist). az000: a dark charcoal pointed wedge still hangs below the cream bib between the forelegs.
- round-2 item "Legs hang under a body hem": **not**. front limb close-up: a dark hem crease still crosses the near foreleg at the elbow, and the forearm keeps about 90% of its width down to the wrist. Every paw flares into a tan boot, the hind paws worst.
- round-2 item "Move clip reads as idle": **done**. move_f007 vs move_f013: the diagonal pairs swap, and the near foreleg reaches forward, then back. It no longer reads as idle.
- round-2 item "should: F3 socket about 1.15x eye": **partly**. The black socket is now about 1.3x the eye, but the eye is an amber cube standing proud of a slot.
- round-2 item "should: O3 toe lengths": **not**. Each paw still has four identical toes in a straight row.
- round-2 item "should: O5 nose paint": **done**. az000: a black nose pad over a pale lip.
- round-2 item "should: O7 tail carried low": **done**. All beauty views: the brush hangs low behind the hocks.
- **O1** [major/form] where: 2_closeups front limb colour/wire (near foreleg at the elbow), hind limb colour (all paws); 1_beauty az090 (hind paws)
  - what: The legs still hang under a hem. The upper-arm mass overhangs the forearm with a dark horizontal crease at the elbow, and the forearm keeps about 90% of its elbow width down to the wrist. Every paw flares into a tan bell-bottom boot about 1.4x the pastern width, and the tall hind cannon blocks read as hooves.
  - fix: Stage 2: (a) On every paw, pull the side and back verts of the bottom ring in to about 1.15x the pastern width and push the front verts forward about 10%, so the paw becomes an oval pad under the pastern, not a bell. (b) Scale the wrist ring to about 70% of the elbow ring, and scale the hind cannon rings to about 75% of their current width. (c) Slide the upper arm's lowest loop down and in by about 8% of leg length so it meets the forearm flush, and do the same at the stifle. If the 0.9 IoU floor blocks (c), log it as partly done.
  - check: Front and hind limb close-ups: no dark horizontal line across any leg, and no bell flare at the sides or back of a paw. az090: the legs taper from elbow to wrist. IoU > 0.9.
- **O2** [major/silhouette] where: 1_beauty az000, between the forelegs below the cream bib; 3_tech az000, same spot
  - what: The sternum keel still hangs below the bib between the forelegs as a dark charcoal pointed wedge. In the front view it reads as a dangling blade.
  - fix: Stage 2: raise the lowest centre vertex of the chest loop to the level of its two neighbours, and lower those neighbours by about 3% of chest depth, so the brisket is flat-bottomed. Stage 3: paint the sternum faces bib cream down to the brisket.
  - check: az000: the cream bib meets the leg line with no dark shape below it. 3_tech az000: no V point between the forelegs.
- **O3** [minor/face] where: 2_closeups head colour, eye
  - what: At close range the eye is an amber cube standing proud of a black slot. Its spiky white catchlight reads as a shard.
  - fix: Stage 3: flatten piece_eye to a lens no deeper than 1/3 of its width, seated flush with the socket rim. Make the catchlight a small square quad on the front face, and paint the socket dark grey (about 25% value).
  - check: Head close-up: a flat amber eye with a dot highlight and no block edges. float 0.
- **O4** [minor/pieces] where: 2_closeups head colour (cream band under the jaw); 3_tech az000 (ring round the neck)
  - what: The cream throat part of the ruff is one smooth band with a hard top edge, and it wraps the neck like a scarf. From the front the ruff is still a uniform torus.
  - fix: Stage 3: break the throat part of piece_ruff into 2-3 downward clumps of unequal length. Sink its top edge into the jaw and neck so no ledge shows. Keep the stepped nape.
  - check: Head close-up: a clumped fur edge under the jaw, with no continuous top edge. 3_tech az000: no unbroken ring. Ruff hit, float and zfight stay 0.
- **O5** [minor/pieces] where: 2_closeups toes colour, all paws
  - what: The toes are four identical tan keys with black tips in a straight row, like a comb.
  - fix: Stage 3: lengthen the two middle toes of each paw by about 20%, and splay the outer toes +-8 deg along a slight arc.
  - check: Toes close-up: the middle toes lead. piece_toes zfight stays 0.
- keep: az090 silhouette: a wedge head, tall ears, a deep chest with a clear tuck-up, and a low brush tail with a dark tip | Palette: grey with a dark saddle, a cream bib, tan legs from the wrist and hock down, amber eyes, and a black nose pad over a pale lip | The new diagonal-pair trot and the head-down attack lunge. Tech is clean: hit, float, flip, zfight and drift are all 0.

