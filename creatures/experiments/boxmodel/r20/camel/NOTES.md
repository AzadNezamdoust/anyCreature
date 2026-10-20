# Camel (r20) - structure copied from opus/stag, differences in the PARAMS block

Design: one-humped dromedary - tall thin legs, a big single hump mid-back, a long forward-reaching neck and a long narrow head with small ears.
Sandy body, darker neck fur collar, pale belly/rump, dark pads; no antlers; 7 colours.

## Stage 1 (2 rounds)
- r01 PARAMS: HEAD_SHIFT forward 0.30 (+NECK_SHIFT on ring 7), HEAD_SCALE long head, HUMP dz on rings 11-16. PASS 736 tris; reads camel. Critique: ears flat sideways cards (az000).
- r02 EAR_TIP_S up and in. LOCK, edge sha f51080964d269365.
## Stage 2 (1 round): stag ops as-is (nose block, mouth line, neck loops, eye socket, rump chamfer). IoU min 0.977.
## Stage 3/4 (1 round): antlers off (ANTLERS=False), sandy palette; stag mane/eye/hooves/tail pieces kept. 1532 tris, all gates PASS, glbcheck OK.
Weakness: the stag's neck-mane piece sits at the neck base like a scarf; hump top is a single large facet; hooves are cloven-deer not camel pads.
