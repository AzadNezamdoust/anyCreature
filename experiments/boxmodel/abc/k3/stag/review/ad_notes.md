# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 6 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the tall, properly branching antlers with forward brow tines and crowned tips, the dark mane over a cream V bib, the cream belly line and rump patch, hocks and small black hooves, the short tail, and the graze and charge clips. Both reviewers call this the closest to its brief; do not regress it.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Posed clipping warning at 1.17% of surface, and the throat fold-over (kit warning; F major, O major).**
   - `WARN s4 qa: 16 triangles (1.17% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek`
   - No gate fails, but 1.17% is above the 1.0 threshold. Likely cause: the charge (4_posed attack_f016) swings the antlers down until the rear tines and the ear pass into the mane and the shoulder; the graze (idle_f024) does the same with the brow tines against the neck.
   - Also: 3_tech hero, az000 and az090 show purple posed fold-overs on the mane tufts at the throat (2 triangles, 0.17%, under the limit but visible in three views; both reviewers saw it).
   - Fix: Stage 4: cut the charge's head pitch until the rear tines clear the shoulder line in attack_f016 (about -25 deg head instead of -32..-38; give the difference to the neck only if the mane tufts stay bound), and check the graze frame the same way. For the throat fold: the tufts there ride the neck/head weight seam; after item 1 rebuilds the mane, bind the throat shingles `bone=neck` (rigid) rather than `body=` so they cannot fold, and keep the s4 r03 rule of no tuft rooted below z 0.78.
   - Check: stage-4 run: clip warning under 1.0% or none, flips 0; 3_tech az000: no purple at the throat.

1. **The mane and bib are a pile of thin shards (F major, O major).**
   - Where: 1_beauty hero, az000; 2_closeups head and mane colour/wire: 36 narrow blade tufts overlapping in a dense pile that goes spiky and procedural at close range; 4_posed attack_f016 shows the pile as a mess of wire. 5_reference: the mane is a few bold shingle rows hanging down the neck, with the cream V a single clean shape.
   - Fix: Stage 3: rebuild the mane as 10-14 bold shingle plates in three rows down the neck (nape, sides, throat), each about 3x the width and 2x the thickness of the current tufts, lengths varied +-25%, hung down with the slight back lean from s3 r02, overlapping like roof tiles and sunk 20% into the neck; keep the mane colour. Rebuild the V bib as paint on the chest faces (cream, border on the existing loops) plus at most three longer shingles hanging over its top edge. Keep every root above z 0.78 (the drift lesson).
   - Check: 2_closeups mane colour: no more than 14 mane pieces, no needle tips; 1_beauty az000 at thumbnail size: a dark mane and one clean cream V; mane hit/float/drift 0.

2. **Tine tips are identical darker cone caps that read as glued-on pencil tips (O major, F minor).**
   - Where: 1_beauty hero, az000; 2_closeups head: every tine ends in a separate darker cone standing on a ledge; all tips the same length.
   - Fix: Stage 3: rebuild each tip cap in the `antler` colour exactly (no darker tint), rooted 40% of its length into the tine so no ledge shows, base radius matching the tine's last ring, lengths varied +-30% with the crown tips the longest and the brow tines the shortest, and each leaning 5-10 deg outward along the tine's own axis.
   - Check: 2_closeups head: tine and tip read as one taper with no colour step or ledge; tip hit/float 0.

3. **The ear is a thin flat cream plate in front of the antler base and eye (O major).**
   - Where: 2_closeups head colour and wire; 1_beauty hero: the ear is a flat cream slab with no thickness, sitting forward of the antler base and partly over the eye.
   - Fix: Stage 2 (vertex moves): move the ear's rear-face verts back by 2% of head length at the base tapering to 0.5% at the tip so the ear has a section; rotate the ear tip verts back by about 15 deg (tip moves rearward and up 3% of head length) so the ear stands beside the antler base and clears the eye. Stage 3 (paint): inner face cream, outer face `red-brown body`, border on the ear's edge loop.
   - Check: 2_closeups head: the ear has a visible thickness and sits behind the eye; IoU > 0.9.

4. **The eye is a tiny dot on a long head (F minor).**
   - Where: 1_beauty hero, az090; 2_closeups head: the eye is a black chip about 1/15 of the head length.
   - Fix: Stage 3: scale piece_eye 1.6x (target about 1/9 of the head length), keep it a lens seated in the socket with the front proud by half its thickness; paint the socket inset `dark mane` so the eye reads in a shadow.
   - Check: 1_beauty az090 at thumbnail size: the eye is visible; eye float 0.

5. **Dark inset facet at the armpit (F minor).**
   - Where: 2_closeups front limb colour: a dark concave facet on the chest behind the near foreleg's top.
   - Fix: Stage 2 (vertex moves): move the 1-2 verts of that facet outward by 3% of body width so the chest-to-leg faces are convex; check the 2 flipped faces logged near the shoulder (s4 r04) at the same spot after the move.
   - Check: 2_closeups front limb: the armpit is one lit plane; valley 0; flips 0.

## Should-fix

- AD: the rump patch border runs across faces on the flank in 1_beauty back34; move the cream rule's edge to the nearest loop (stage 3 paint).

## Dropped

- O "the lower legs add an off-palette dark stocking colour": NOTES s3 r01 paints the lower legs with the `dark mane` colour, which is on the palette, and 5_reference side shows the same dark lower legs. Keep them.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6
- top_issues:
  - Tech heatmap flags posed fold-over (purple) at the mane/neck junction in hero and az000; the mane is a dense pile of overlapping thin shards that gets messy at close range (mane close-up, attack_f016)
  - Antler tine tips are identical needle spikes (piece_tines) and 2 flipped body faces are logged near the shoulder; a dark inset facet at the armpit in the front-limb close-up
  - Eye is a tiny dot on a long head, so the face has little appeal at thumbnail size
- brief_fit / keep: Closest to the brief: tall crowned antlers with forward brow tines, leaf ears, dark mane over a cream V bib, cream belly and rump, hocks and small black hooves all read.

### Opus 5.5: FIX 6
- top_issues:
  - The mane and bib are built from many thin shard plates, not a few bold clumps, so they read spiky and procedural in the close-ups
  - The ear is a thin flat cream plate that sits in front of the antler base and eye (head close-up). Two flipped faces at the throat fold when posed (purple in tech az000)
  - The tines have separate darker cone caps that read as glued-on pencil tips. The lower legs add an off-palette dark stocking colour
- brief_fit / keep: Best fit: tall, properly branching antlers with forward brow tines and crowned tips, a dark mane with a cream V bib, rump patch and short tail

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 16 triangles (1.17% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 16, clip_area_pct 1.17
