# Rhino (r20) - structure copied from opus/boar, differences in the PARAMS block

Design: heavy grey barrel on thick pillar legs, low long head carrying a big cream front horn and a small rear horn.
Upright tube ears, short tail with dark tuft; no crest, no saddle; 8 colours.

## Stage 1 (4 rounds)
- r01 PARAMS: BODY_X 1.15, HEAD_X 1.05, LEG_W (1.30, 1.22). FAIL self-intersection (fore-leg back vs belly).
- r02 LEG_W depth 1.06. Still FAIL (root level too wide inside the belly).
- r03 LEG_FROM=1: the root level keeps boar size. PASS 716 tris. Critique: pig disc snout; accepted (horn carries identity).
- r04 LOCK. edge sha 50b9141cc0a51856. (DS() maps the boar design points through the PARAMS scales for stage 2.)
## Stage 2 (1 round): boar ops as-is (eye socket, nostrils, mouth line, saddle loop). IoU min 0.943.
## Stage 3/4 (4 stage-4 rounds)
- r01 crash: empty crest bmesh capped. Fix: caps only when CREST_ON.
- r02 tusk -> horns (HORNS), grey palette. FAIL drift 1 shell. r03 horn body=: still FAIL -> techqa: piece_eye.
- r04 eye bound with body=. All gates PASS, glbcheck OK.
Weakness: pig-style nostril disc and pointed boar ears; horns are 4-sided cones.
