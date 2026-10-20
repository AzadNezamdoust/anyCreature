# Penguin (r20) - structure copied from opus/owl, differences in the PARAMS block

Design: chubby cartoon penguin - big round black head and back, a white face mask and belly, small dark eyes, orange beak and feet.
Flat flipper paddles hang down each flank; a short stub tail; 5 colours.

## Stage 1 (4 rounds)
- r01 PARAMS: owl ear tufts shrunk (TUFT_TIP), facial-disc TWEAK off. PASS 580. Critique: the owl wings fold back into a long tail wedge (az090).
- r02 FLIPPER sections replace the folded wing: paddles hang down the flank. Better (az000).
- r03 critique: the owl's long tail (az090). Fix: TAIL_T0/T1 short stub. Better.
- r04 LOCK (J tail1 moved to match). edge sha cc33169eec3be66b.
## Stage 2 (1 round): owl ops as-is (disc rim loop, sockets). IoU min 0.945.
## Stage 3/4 (4 stage-4 rounds)
- r01 penguin palette (black/white/orange). All PASS; critique: owl-size eyes and brow wedges (az000).
- r02 EYE_R small, BROW off -> crash (stage4 bound 'brow'). r03 same crash (edit missed). r04 bind only present pieces: all gates PASS, 910 tris.
Weakness: feet keep the owl's talons (claws instead of webbed feet); head is owl-wide with two tuft nubs.
