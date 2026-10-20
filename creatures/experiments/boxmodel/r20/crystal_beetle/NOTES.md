# Crystal beetle (r20, opus)
Design: a pony-sized rhinoceros beetle, dark teal domed shell, six black jointed legs, bone mandibles.
Identity cues: violet crystal spikes bristling along the back and a big crystal rhino horn.

## Stage 1 (7 render rounds)
- r01 FAIL tris 380 < 400; legs thin 4-sided ribbons. Fix: REFINE_FROM=3 (mid rings), legs from two bands (6-sided), thicker.
- r02 PASS 604. Critique: spidery long legs. Fix: LEG_SPREAD 0.8, LEG_THICK 1.25.
- r03 PASS. r04 lock. r05/r06 re-lock after the r20lib determinism fix (lock had failed on rerun with no change).
- r07 re-lock (unlock logged: stage-4 sliver gate failed 4% on the leg sides; the limb rings now use even angles, `even=True`; same silhouette). Edge b31af19b.
## Stage 2 (1): knee + mid-femur loops per leg, shell rim loop, pronotum lip.
## Stage 3 (1): 8 colours, crystal horn, 8 crystals, eyes, mandibles. 1190 tris.
## Stage 4 (4)
- r01 FAIL slivers 4.7% (legs). r02 stage-2 femur loops: still 4.0% -> stage-1 unlock above. r03 PASS. r04 final orbit+glbcheck PASS.
Weakness: the thorax/legs read as one dark mass; the tripod gait is subtle.
