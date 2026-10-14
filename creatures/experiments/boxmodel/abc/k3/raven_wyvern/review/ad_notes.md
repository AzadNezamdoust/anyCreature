# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 6.5 FIX / 4 REBUILD.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Reconciled verdict: FIX, not REBUILD. Opus's rebuild call rests on the wings, which are base geometry; a rebuild is not on the table this pass, so the wing identity is recovered with paint, spar pieces and edge moves (item 1). If item 1 lands, the wyvern read is there from az090 and hero.

Keep what works: the silhouette (tail longer than the body with a fin tip, graded dorsal spines, swept horns, raven bill with a pale tip, bird legs with a reversed hock), the palette, and the clean rig (0 flips, 0 drift). Fable calls this the best silhouette match; do not regress it.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Posed clipping warning at 3.56% of surface (kit warning).**
   - `WARN s4 qa: 8 triangles (3.56% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek`
   - No gate fails, but 3.56% is above the 1.0 threshold. Eight triangles covering 3.56% of the surface means big faces: the wing blades. Likely cause: the mantle (4_posed attack_f020) or the stalking walk (move_f009/f017) swings a blade through the flank or the thigh.
   - Fix: Stage 4: in the mantle, rotate each wing arm outward (away from the body) by 20 deg before lifting it, so the blade clears the flank; in the walk, keep the blades still (no arm key) or weight the blade's lower verts to the wing hand bone rather than the spine so the hip sway does not drag them through the thigh. Rerun and read where the pink sits in 3_tech.
   - Check: stage-4 run: clip warning under 1.0% or none; 4_posed attack_f020: both blades outside the body.

1. **The folded wing is one flat purple cape with no arm, spars or thumb (O blocker, F major).**
   - Where: 1_beauty az090 and hero: a single saturated purple polygon hangs on each flank; 2_closeups hind limb: a flat slab edge-on with sliver edges (yellow in 3_tech az000). The one dark spar from s3 r02 barely reads. 5_reference side: a dark feathered wing arm running from the shoulder to a wrist knuckle at the top, with a purple membrane hanging under it, broken by dark finger spars and scalloped between them; a thumb claw at the wrist.
   - Fix, in three parts, all inside stages 2-3:
     - Stage 3 (paint): paint the top band of each blade (the faces along the leading/upper edge, about the top 35% of the blade height from shoulder to wrist) `blue-black plumage`, so the arm reads dark and only the hanging membrane is purple; keep the border on the blade's loops.
     - Stage 3 (pieces): rebuild the spar as three dark finger spars fanning from the wrist knuckle (front-top corner of the blade) back and down across the membrane to its trailing edge, each a 4-ring tapered tube rooted 30% into the blade face (radii like the s3 r03 spar so no slivers); rebuild the thumb claw 2x its size as a hook at the wrist, pointing forward-down, `black bill` colour.
     - Stage 2 (vertex moves): scallop the trailing/lower edge of each blade by pulling the 2-3 edge verts between the spar tips inward by 6-8% of the blade height, so the membrane hangs in bays between the spars; thicken the blade's top edge by moving its outer verts out 3% of body width so the arm has a section edge-on. The blade is a small part of every silhouette; IoU holds.
   - Check: 1_beauty az090 at thumbnail size: a dark arm over a purple membrane with three spars and a scalloped edge, not a cape; 2_closeups hind limb: the blade has a visible edge thickness; spar hit/float/z-fight 0; slivers under 2%.

2. **Hackles are dozens of needle shards (O major; F lists the shaggy hackles as a keep).**
   - Where: 2_closeups head and hackles colour: the chest and neck carry many thin spikes that splinter at close range; 1_beauty az000: a bristle of needles under the bill.
   - Fix: Stage 3: rebuild the hackles as 5-6 broad wedge tufts per side, base width at least 40% of the tuft length, thickness at least 25% of the width, lengths varied +-30%, sunk 20% into the throat and chest, overlapping like shingles. Keep them shaggy (Fable's keep) but bold, not needle-thin: no tuft with an apex angle under 30 deg.
   - Check: 2_closeups head: tufts read as clumps of plumage; 1_beauty az000: the throat outline is ragged but not spiky; hackle hit/float 0.

3. **No wing mantle in the attack, and the neck is a straight post (O major).**
   - Where: 4_posed attack_f020: the wings barely lift; 1_beauty az090 vs 5_reference side: the reference neck curves back then forward (S); ours runs straight from the chest to the skull.
   - Fix: Stage 4: at the lunge peak, key both wing arms up 35 deg and out 40 deg (after the outward rotation from item 0) so the blades spread behind the head; hold for 6 frames. Stage 2 (vertex moves): move the mid-neck ring back by 4% of body length and the throat ring forward by 3%, so the neck reads as a curve in az090; log partly done if the side IoU blocks it.
   - Check: 4_posed attack_f020: blades spread visibly wider than the body; 1_beauty az090: a visible S bend in the neck; IoU > 0.9.

4. **Tail is a constant tube ending in a solid spade (F major).**
   - Where: 1_beauty az090, back34; 2_closeups front limb: the tail keeps one section to the fin and the fin is a flat spade. 5_reference side: a tapering tail with a ribbed, scalloped fan.
   - Fix: Stage 2 (vertex moves): scale the tail rings from 100% at the root to 55% at the fin; pull the fin's trailing edge verts inward between three points by 10% of the fin length to scallop it. Stage 3: add three dark rib pieces on the fin (thin tapered tubes rooted in the fin face, like the wing spars), and paint the fin's front third `blue-black` so only the fan is purple.
   - Check: 1_beauty back34: a tapering tail with a ribbed fan; IoU > 0.9.

5. **Feet are flat paddles with serrated toes and tiny claws; the eye is a small diamond (F minor).**
   - Where: 2_closeups front limb: each foot is a wedge with a serrated flat edge and small talons; 2_closeups head: the eye is a small amber bicone.
   - Fix: Stage 3: rebuild the talons at 2x their size as curved hooks (3 rings, tip down), `black bill` colour, rooted 30% into the toe ends, plus the hallux talon at the heel; rebuild the eye as a lens 1.5x wider, no deeper than 1/3 of its width, seated in the socket with the socket painted `black bill`. Stage 2 (vertex moves): pull the toe-end verts apart by 3% of foot width at the tips so the paddle splits into three toe points.
   - Check: 2_closeups front limb: three toes with visible hooked talons; head close-up: an amber eye about 1/8 of the head length; talon and eye float 0.

## Should-fix

- AD: the dorsal spines are fine but identical in section; vary their lean +-10 deg (stage 3).

## Dropped (needs stage 1)

- F "the body squats low with short hidden legs, reading as a hunched vulture": leg length and body pitch are base geometry; not reachable within the IoU floor.
- O "a real wing arm with elbow and wrist geometry": the blade is base geometry; item 1 recovers the read with paint, spars and edge moves instead.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6.5
- top_issues:
  - folded wing is a single flat purple plate with no thickness, reads as a shard edge-on (hind-limb close-up, sliver edges in az000)
  - tail is a constant-section tube ending in a fan; feet are flat wedges with serrated flat toes and tiny claws
  - eye is a small diamond and the body squats low with short hidden legs, reading as a hunched vulture
- brief_fit / keep: Best silhouette match: tail longer than the body, graded dorsal spines, shaggy hackles, swept horns, raven bill; the wings and feet are the weak pieces.

### Opus 5.5: REBUILD 4
- top_issues:
  - The wings are a single purple cape plate hung on each flank, with no wing arm, spars or thumb claw, so the wyvern identity fails
  - The chest and neck are covered in dozens of needle-thin hackle shards that splinter at close range
  - The body is an upright raven with no neck S-curve and no wing mantle in the attack
- brief_fit / keep: Reads as a horned raven with a dragon tail; the brief's first requirement (a wyvern whose wings are the forelimbs) is not met.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 8 triangles (3.56% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 8, clip_area_pct 3.56
