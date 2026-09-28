# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 6.5 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the wedge head with tall pointed ears, amber eyes under a brow, black nose pad over a cream lip, dark saddle, deep chest with a tuck-up, long tan legs, the low bushy tail, and the diagonal-pair trot. Both reviewers call the identity the strongest; do not regress it.

Kit gates: none failing. clip_area_pct 0.79 (14 triangles), below the 1.0 threshold: no item. There is no item 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

1. **The ruff is a spray of thin triangle plates, some detached on the shoulder (F major, O major).**
   - Where: 1_beauty hero and az000; 2_closeups front limb and ruff colour/wire: many narrow triangular plates stand out from the neck and shoulder, several floating clear of the shoulder as shards, and some crossing the shoulder and the foreleg line. 5_reference: the ruff is two or three rows of wide overlapping shingles round the neck only, ending at the withers and the chest.
   - Fix: Stage 3: rebuild piece_ruff and the bib clumps as 8-10 wide shingle plates (width 2x the current clump, thickness at least 25% of the width, lengths varied +-25%) in two rows around the neck, laid down along the surface (keep the s3 r02 sweep), sunk 20% of their thickness into the skin, and rooted only on neck rings in front of the withers and above z 0.64 (the s4 r01 drift lesson: nothing on the upper-arm band or the shoulder). Paint the throat and chest row cream, the nape row grey; the cream bib under them stays painted on the chest faces.
   - Check: 2_closeups front limb: no plate on the shoulder or across the foreleg; 1_beauty hero: no detached shard; ruff float/drift 0; az000 shows the cream bib.

2. **Hackles along the spine are a row of identical spikes (F major, O major).**
   - Where: 1_beauty az090 and back34; 3_tech az090: a comb of identical small triangles down the saddle from the withers to the hip. 5_reference: no spikes; the saddle is a smooth dark mantle.
   - Fix: Stage 3: delete piece_hackles. If a withers tuft is wanted, keep at most three clumps at the withers only, unequal (+-30%), laid flat along the back, none behind the shoulder loop.
   - Check: 1_beauty az090: no comb along the spine; the saddle reads as one dark mantle.

3. **Posed fold-over on the chest and a dark pendant between the forelegs (F major, O major).**
   - Where: 3_tech hero and az000: a purple patch on the chest under the ruff (2 faces, 0.20%, under the limit but visible in two views and as a dark collapsed facet in 1_beauty az000). 1_beauty az000: a dark grey pointed wedge hangs below the cream bib between the forelegs.
   - Fix: Stage 2 (vertex moves): raise the lowest sternum vertex to its neighbours' level and spread the drop over the 2-3 bottom chest verts each side so the brisket is a rounded curve, not a point; add one logged loop across the chest between the foreleg tops so the chest skin has a row to bend on when the legs swing. Stage 4: check that the chest faces between the forelegs carry chest weight, not upper-arm weight. Stage 3: paint the sternum faces cream on the existing loop so the bib closes at the leg line.
   - Check: 1_beauty az000: no dark point below the bib; 3_tech az000 and hero: no purple on the chest; flips 0; IoU > 0.9.

4. **The tail is dark along its whole underside, not just the tip (O minor).**
   - Where: 1_beauty az090, back34 and az180 (5_reference): the tail's underside and rear read fully dark; the reference tail is grey with a dark tip only.
   - Fix: Stage 3 (paint): paint the tail body and its brush clumps `grey fur`, and the `dark saddle` colour only on the last 30% of the tail (the tip clump and the base faces under it); keep the saddle running onto the tail root from the back.
   - Check: 1_beauty az090: a grey brush with a dark tip.

5. **Paws are blocks with claws stuck on (F minor).**
   - Where: 2_closeups front and hind limb: each paw is a box the width of the cannon with four claws on its front face; the brief asks for oval paws with the middle toes leading.
   - Fix: Stage 2 (vertex moves): on each paw, pull the side and back verts of the bottom ring in to about 1.15x the pastern width and push the front verts forward about 10% so the paw becomes an oval pad. Stage 3: make the two middle claws about 20% longer and splay the outer claws +-8 deg, rooted 30% into the toe end.
   - Check: 2_closeups front limb: an oval paw with the middle claws leading; claw float 0; IoU > 0.9.

## Should-fix

- AD: the amber eye is a small diamond (2_closeups head). Stage 3: scale the lens 1.4x, keep it under the brow and proud by half its thickness.
- F: the 2 slivers and 2 flipped faces logged pass the gates; recheck after item 3, which touches the chest faces.

## Dropped

- None. Every item is reachable in stages 2-4.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6.5
- top_issues:
  - Tech heatmap flags a posed fold-over (purple) on the chest under the ruff, seen in the idle first frame as a dark collapsed facet between the front legs in az000 and hero
  - Hackles along the spine are a row of identical repeated spikes (az090, back34), and some ruff triangles float off the shoulder as detached shards (hero, front-limb close-up)
  - 2 flipped body faces and 2 slivers logged; paws are blocky with claws stuck on rather than oval toe-led paws
- brief_fit / keep: Strongest identity: long wedge muzzle, tall ears, amber eyes under a brow, clumped ruff over a cream bib, dark saddle, tuck-up and a low bushy dark-tipped tail all read at a glance.

### Opus 5.5: FIX 6
- top_issues:
  - The ruff is built from many thin triangle plates, and the hackles are a row of identical spikes along the spine (machine tell, paper-thin edge-on)
  - Two flipped faces fold over at the throat when posed (purple in tech hero/az000). A dark spike pendant hangs under the chest between the forelegs (az000)
  - The tail is dark along its whole underside rather than a dark tip. Some ruff plates cross the shoulder and forelimb line
- brief_fit / keep: Closest overall: wedge head, tall pointed ears, strong amber eyes, dark saddle, deep chest with tuck-up, long legs, low bushy tail

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 14 triangles (0.79% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 14, clip_area_pct 0.79
