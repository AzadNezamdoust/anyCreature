# Scorpion (r20) — round notes

Design: a chunky stylised desert scorpion — flat segmented amber body, two big swollen pincers held forward, four
arched walking legs a side, a five-segment tail curling up and forward over the back to a bulbous dark stinger.
No reference sheet / blueprint in this batch.

## Stage 1
**r01** 572 tris, FAIL self-intersection in the tail at the top of the curl (0, 0.52, 0.36). Silhouette already
reads scorpion from top and side. Diagnosis: hring flips a ring whose tangent turns backwards (its 'up' keeps
z > 0), so the curl twists. Fix: tail rings take their dorsal side from the tangent (outside of the curl).
**r02** 572 tris, gates PASS; the curl is clean. Critique: worst = needle legs: 2-3 cm sections with a 12 cm spike
tip (az090 comb of pins, az000). Diagnosis: LEG_W 0.028/0.024/0.018, shin at z 0.12. Fix: sections ~50 % thicker,
shin lowered to z 0.08 and the tip pulled in (short pointed foot).
**r03** 572 tris. Legs now planks (8 cm deep boards, az090) - overshot. Critique also: the body is a 9 cm plank from
the side, the tail looks heavier than the body. Fix (r04, leg width settles between r02 and r03 as the same item):
LEG_W 0.032/0.028/0.021; body top half-heights x1.45 (BODY_H).
**r04** 572 tris: legs balanced, body reads as a segmented slab under the curl. Locked (r05); pincer fingers and stinger come as pieces.

## Stage 2
Arm elbow + wrist loops, knee loops, tergite steps, waist pinch. **r06** (stage 4 run): total 802 tris < 900.
Fix: joint loops where the creature bends: ankle loop per leg and one loop between every tail segment.

## Stage 3 / 4
**r07** 994 tris, all gates PASS: pincer fingers, stinger barb, four eye beads; amber / dark bands / pale / black,
4 colours. Rig 24 bones; idle sway, move = alternating leg swing, attack = tail strike + pincer snap.
Critique: worst = the pincer fingers are buried in the palm (close-up 2) - the claws read as clubs.
Fix: finger roots moved 3.5 cm forward to the palm tip, 30 % longer.
**r08** final (orbit + review).

Final: all stage-4 gates PASS. Remaining weakness: legs are straight posts (no visible arch), pincer fingers small.
