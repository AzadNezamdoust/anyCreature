# raven_wyvern (t7) build notes

## Stage 1
- r01 Critique: the wing arms rise straight up beside the head (az000 reads as raised arms, a T-pose cue) and the finger bundle is a thin plank that does not read as a folded wing. Diagnosis: J wristL at z 1.19 (0.3 above the shoulder), fingerL/tipL hf 0.04/0.016. Fix: wrist lowered to z 1.10 and forward over the shoulder, finger bundle deepened to a vertical blade (hf 0.085). Result (r02): see below. 460 tris.
- r02 Result: better; the folded wing now reads as a wing blade along the back, not raised arms. 460 tris.
- r02 Critique: stilt legs; from az000 the legs are skinny planks and the body rides high (hip-to-ground ~1.3x torso depth). Diagnosis: LEG hs/hf (thigh 0.08/0.11, hock 0.042) and every station/joint z. Fix: legs ~20% thicker and the whole upper body (stations, hip, wing, knee half) lowered 0.06 m.
- r03 Result: better; legs read sturdy, body lower. 460 tris. (Blueprint IoU fell because the design moved down 0.06; blueprint redrawn at r04 to the new height.)
- r03 Critique: head and neck read as a slender crow (az090): a long thin conical bill and a neck much thinner than the skull. Diagnosis: ST[0..7] bill w/up (0.045/0.058 at the culmen) and neck w 0.125-0.135. Fix: bill shorter (tip y -1.05), deeper and hooked; skull slightly bigger; neck stations 6-7 thickened to w 0.14-0.15.
- r04 Result: better; heavy hooked bill with a stop, neck as thick as the skull is wide. 460 tris.
- r04 Critique: az000/az180 still read as two arms held up beside the body (the wing bars splay out to x 0.36). Diagnosis: J armL/wristL/fingerL/tipL x 0.30-0.345, outboard of the shoulder. Fix: fold the wing in against the body: wrist x 0.275, finger blade x 0.30.
- r05 Result: better; from front/back the folded wings hug the flanks. 460 tris.
- r06 lock: the base reads as a biped wyvern from every view (two legs, wing-forelimbs folded back along the back, tail longer than the body ending in a thin fin blade). Remaining base weakness (tail tip a thin rod from the top) is left to the stage-3 fin.

## Stage 2
- r01: 7 logged ops (knee x2, hock, wrist, shoulder, mid-neck loops; eye-socket inset), brow corners pushed out 18 mm, knee/hock rings pinched. Gates PASS, min IoU 0.991, 628 tris.
- r01 Critique: the eye socket landed on the lower cheek face (below the side crease), not under the brow. Diagnosis: EYE z 1.135 was nearer the b->c face centre than the a->b face. Fix: EYE z 1.196 (the a->b face, right under the pushed-out brow corners).
- r02 Result: better; the socket now sits under the brow corners (hero). Gates PASS, IoU 0.991, 628 tris. Stage 2 done.

## Stage 3
- r01: 13 pieces (eye/pupil/glint, brow, horns, hackles, graded spines, tail fin, sail, spars, thumb claw, toes with talons), 8 colours, 1240 tris. FAIL hit 4 (sail) and slivers 6.1%.
- r01 Critique: the wing sail fails tech QA and barely shows (a purple strip under the finger blade). Diagnosis: one 'spars' object crosses the sail in two places per side (hit); 16 mm slab side walls and 0.5 m spar quads are needles (spars 48, sail 16 slivers). Fix: sail rebuilt as a lens (single rim, bulging centre), each spar its own object in ~9 cm segments, trailing finger tip lowered to show more sail.
- r02 Result: better; slivers 20 (1.5%) PASS, spars clean; sail still hit 2 (one per side), 1356 tris.
- r02 Critique: the sail rim leaves and re-enters the finger blade and the arm (straight rim chords W->T and W->Sh graze their undersides), so it crosses the body in several patches. Diagnosis: OL has no points inside the blade/arm between the wrist and the tip/shoulder. Fix: rim points added inside the finger blade (y 0.12) and the forearm (z 0.95); the S1 scallop raised less deep so no fan triangle is a needle.
- r03 Result: better; all stage-3 gates PASS (hit 0, float 0, z-fight 0, slivers 12 = 0.9%, all on the base), 8 colours, 1364 tris. The sail now reads purple under the folded wing from the side.

## Stage 4
- r01: rig (13 bones + mirrors, roll auto), skin, all pieces bound with body= weights, clips idle 48f / move 33f / attack 40f. FAIL posed fold-overs 12 (0.88% tris, 0.10% area), all on spar1.
- r01 Critique: the long trailing spar folds over itself when the wing mantles. Diagnosis: its vertices borrow skin weights from whatever body surface is nearest (flank, hips, hand), so the bar is sheared between bones. Fix: the spars take their weights from the sail they lie on (bind body=membrane), which deforms cleanly.
- r02 Result: fold-overs 0 PASS, but drift 4 shells (the spar roots slide off the wrist: the sail's fan interpolates the wrist with its centre vertex). 
- r02 Critique: spar roots leave the wrist knuckle in attack. Diagnosis: sail weights at the root are not the wrist skin's. Fix: spar weights blend from the body skin at the root to the sail's weights over 0.3 m along the spar.
- r03 Result: better; drift 2 shells, only the right-side spars. 
- r03 Critique: right-side spar roots still slide. Diagnosis: the blend distance used the +X root only, so every .R vertex got pure sail weights. Fix: measure the distance with |x| (the mirror is applied by then). Final round with orbit and glbcheck.
- r04 Result: all stage-4 gates PASS (hit 0, float 0, z-fight 0, slivers 0.9%, flips 0.00% tris / 0.00% area, drift 0, lock PASS, glbcheck OK). Posed wires: the neck lunges and the wings mantle without collapse.

## Triangles
stage 1: 460; stage 2: 628; stage 3/4: 1364 total (base 628 + pieces 736).
Rounds: s1 6 (lock at r06), s2 2, s3 3, s4 4. Blueprint IoU at lock: side 0.774, front 0.768, top 0.847.
