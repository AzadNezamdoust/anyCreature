# Lion (r20) - structure copied from opus/wolf, all differences in the PARAMS block

Design: tawny heavy cat, short broad blunt head with round-ish ears; a big dark-brown mane collar from behind the ears to the chest.
Thin rope tail ending in a dark tuft; heavy forelegs and broad paws; 8 colours.

## Stage 1 (6 rounds)
- r00 baseline: wolf copy, 728 tris, gates PASS.
- r01 PARAMS: head wider/shorter (HEAD_SCALE), thin rope tail (TAIL_R), heavier legs (LEG_K). Result: FAIL self-intersection, thigh vs waist.
- r02 hind LEG_K y -> 1.0. Still FAIL (thigh x widening). r03 HIND_FREE=2: thigh sections stay wolf size. PASS, 728.
- r04 critique: wolf-tall needle ears (az000). Fix: ear tip lowered (EAR_TIP_S1 z 0.985). Better.
- r05 critique: dog muzzle too long (az090). Fix: HEAD_SCALE y 0.86. Better, reads cat.
- r06 LOCK (orbit). edge sha 2361079b1682983a.
## Stage 2 (2 rounds)
- r01 wolf stage-2 ops as-is (logged loops, socket). IoU min 0.963.
- r02 critique (s3 sheet): chin was pulled to a point by the wolf's absolute nose coords. Fix: nose/chin through head_xf. IoU 0.97.
## Stage 3 (1 round)
- r01 ruff -> mane (MANE_U rows, MANE_T 2.3x), brush -> end tuft (TUFT). 1708 tris, 8 colours, all QA PASS.
## Stage 4 (1 round)
- r01 wolf rig/clips; mane and tuft bound with body=. All gates PASS, glbcheck OK. 1708 tris.
Weakness: ears still pointed (wolf pyramid ear), mane does not crown the top of the head; wolf-scale metres.
