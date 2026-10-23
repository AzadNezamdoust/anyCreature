# Kit bug audit (2026-10-23 night, kit agent)

Kit files changed: kit/junctions.py, kit/junction_gate.py, kit/techqa.py, kit/run.py (--compare only), new kit/techqa_glb.py. Creature folders read-only.
Before = kit as of 01:34 (copy), after = fixed kit; both on each creature's current stage4 GLB, posed clips on, no renders (scratch out dirs).

## Fixes and validation

| # | bug | fix | validation |
|---|---|---|---|
| 1 | eye gate head length = bbox incl. ears/horns | head length = body faces of the head bone and its centre-line children only (ears, horns, tufts, lobes, proboscis out) | 15 creatures change: fox 0.112->0.187, imp 0.066->0.118, manta 0.07->0.134, dragon 0.094->0.131, bear 0.062->0.081, goblin R 0.059 FAIL->0.096 PASS; no-ear heads unchanged within 0.001 (eagle, frog, gorilla) |
| 2 | mirrored root radius mismatch (eagle thigh 72.2/67.4) | mirrored pair (same kind, roots mirrored within 2% size) shares r = median of both sides' samples; json keeps r_side_mm | eagle thigh.L/R 68.6/68.6 (strip 1.02 r both, was 0.96 PASS / 1.03 FAIL); tiger upperarm 152.0/153.7 -> 152.6; elephant, wings: pairs equal |
| 3 | techqa drift anchors = first 12 vertex ids | anchors = shell vertices touching the skin (nearest-surface distance <= max(0.4% size, closest+0.2%)), up to 24 by farthest-point sampling; contact/float tests use all shell vertices, not the first 40 | techqa_glb.py before/after on 6 GLBs: troll drift 1 (piece_flap_back, a swinging hem anchor) -> 0; gorilla, minotaur, boar, dragon, knight 0 -> 0; all other counts identical |
| 4 | centre-line fin bones (seahorse fin_dorsal) classed trunk | trunk() excludes appendage words (fin, dorsal, sail, frill, crest, horn, antler, tusk, ear, lobe, tuft, wing...) | seahorse fin_dorsal now a junction + membrane target (p10 7.7 mm PASS; root knife 1.03 r / strip 1.11 r FAIL, crop confirms notches at the fin base); only zoo bone affected |
| 5 | no top-view shoulder-shelf check (troll T-bar) | shelf = largest patch of faces outboard of a hanging arm root (bone axis z < -0.5), normal within 20 deg of +z, unoccluded from the top; FAIL when area > 0.5 r^2 and width > 0.8 r | synthetic troll T-bar (shoulder top levelled, scratch GLB) 0.93 r^2 x 1.77 r FAIL; troll current 0.0 PASS; every other zoo arm 0.0-0.07 except ogre 3.45 r^2 (flat deltoid cap, visible in crop) |
| 6 | other appendage faces inside a root region (elephant ear rim as shoulder strip) | region keeps only trunk faces and the chain's own faces; json other_chain_tris | elephant upperarm strip 1.9 r -> 0.64 r (FAIL->PASS); tail roots lose thigh faces: dragon knife 1.79 r, tiger 3.3 r, ogre thigh 1.05 r -> 0 |
| 7 | run.py --compare overwrote side_by_side.jpg | writes compare_engine.jpg | troll scratch copy: compare_engine.jpg written, side_by_side.jpg untouched |

## Per creature (junction probe before -> after; eye diam/head L R, ! = eye FAIL)

| creature | probe | junction fails | eye/head | note |
|---|---|---|---|---|
| bear | FAIL -> FAIL | 6/7 -> 6/7 | L0.062 R0.062 -> L0.081 R0.081 |  |
| beetle | PASS -> PASS | 0/6 -> 0/6 | L0.083 R0.084 -> L0.083 R0.084 |  |
| boar | FAIL -> FAIL | 5/7 -> 5/7 | L0.062 R0.062 -> L0.077 R0.078 |  |
| chameleon | FAIL -> FAIL | 4/5 -> 4/5 | L0.143 R0.145 -> L0.143 R0.145 |  |
| crab | FAIL -> FAIL | 12/12 -> 12/12 | LNone! RNone! -> LNone! RNone! | arm shelf 0.91 fired before hang rule; removed |
| crocodile | FAIL -> FAIL | 4/5 -> 4/5 | L0.049! R0.047! -> L0.049! R0.047! | sprawl upperarm shelf 0.8 fired before hang rule; removed |
| dragon | FAIL -> FAIL | 7/9 -> 6/9 | L0.094 R0.094 -> L0.131 R0.131 | tail0 knife 1.79 r was thigh faces -> PASS; eye/head 0.094 -> 0.131 (horns out) |
| eagle | FAIL -> PASS | 1/5 -> 0/5 | L0.136 R0.137 -> L0.136 R0.137 | GLB rebuilt 03:33 by another agent mid-run; on the 01:3x GLB: thigh.L/R r 72.2/67.4 -> 68.6/68.6, strip 1.02 r both sides (symmetric verdict) |
| elephant | FAIL -> PASS | 2/7 -> 0/7 | L0.075 R0.072 -> L0.075 R0.072 | ear rim excluded from shoulder region (131-134 tris): upperarm strip 1.9 r -> 0.64 r, FAIL -> PASS |
| fox | FAIL -> FAIL | 7/7 -> 7/7 | L0.112 R0.113 -> L0.187 R0.189 | eye/head 0.112 -> 0.187 (ears out) |
| frog | PASS -> PASS | 0/4 -> 0/4 | L0.092 R0.092 -> L0.092 R0.092 |  |
| goblin | FAIL -> FAIL | 6/6 -> 6/6 | L0.06 R0.059! -> L0.097 R0.096 | eye R 0.059 FAIL (size) -> 0.096 PASS (ears out) |
| golem | FAIL -> FAIL | 4/4 -> 4/4 | L0.126! R0.124! -> L0.126! R0.124! | horizontal shoulder bone shelf 3.68 fired before hang rule; removed |
| gorilla | PASS -> PASS | 0/4 -> 0/4 | L0.068 R0.068 -> L0.069 R0.068 |  |
| griffin | PASS -> PASS | 0/7 -> 0/7 | L0.102 R0.102 -> L0.102 R0.102 |  |
| hippo | PASS -> PASS | 0/7 -> 0/7 | L0.068 R0.066 -> L0.078 R0.078 |  |
| imp | PASS -> PASS | 0/9 -> 0/9 | L0.066 R0.065 -> L0.118 R0.118 | eye/head 0.066 -> 0.118 (ears out) |
| knight | FAIL -> FAIL | 3/4 -> 3/4 | -None! -> -None! |  |
| koi | FAIL -> FAIL | 3/3 -> 3/3 | L0.119 R0.119 -> L0.119 R0.119 | pec fin shelf 1.12 fired before hang rule; removed |
| lizardman | PASS -> PASS | 0/5 -> 0/5 | L0.087 R0.087 -> L0.087 R0.087 |  |
| manta_ray | PASS -> PASS | 0/5 -> 0/5 | L0.07 R0.07 -> L0.133 R0.135 | eye/head 0.07 -> 0.134 (cephalic lobes out) |
| mantis | PASS -> PASS | 0/8 -> 0/8 | L0.129 R0.129 -> L0.129 R0.129 |  |
| minotaur | PASS -> PASS | 0/7 -> 0/7 | L0.066 R0.066 -> L0.068 R0.068 |  |
| octopus | FAIL -> FAIL | 8/8 -> 8/8 | LNone RNone -> LNone RNone | arm1a/arm2a shelf fired before hang rule; removed |
| ogre | FAIL -> FAIL | 4/4 -> 3/4 | L0.09! R0.088! -> L0.09! R0.088! | NEW shoulder shelf 3.45 r^2 x 2.55 r both arms (crop: flat level deltoid cap); thigh.L knife 1.05 r was arm faces -> PASS |
| owl | FAIL -> FAIL | 7/9 -> 7/9 | L0.137! R0.142! -> L0.147! R0.152! |  |
| penguin | PASS -> PASS | 0/5 -> 0/5 | L0.064 R0.065 -> L0.064 R0.065 |  |
| raven_wyvern | FAIL -> FAIL | 7/7 -> 7/7 | L0.065! R0.064 -> L0.065! R0.064 |  |
| rhino | FAIL -> FAIL | 2/7 -> 2/7 | L0.065 R0.067 -> L0.092 R0.094 |  |
| scorpion | PASS -> PASS | 0/11 -> 0/11 | L0.174 R0.174 -> L0.174 R0.174 | after = with hang rule: arm.L/R pincers no longer shelf (re-run PASS 0/11) |
| seahorse | PASS -> FAIL | 0/3 -> 1/4 | L0.069 R0.072 -> L0.069 R0.072 | fin_dorsal now probed: knife 1.03 r (126 deg) + strip 1.11 r at fin base (crop shows notches); membrane p10 7.7 mm PASS |
| shark | FAIL -> FAIL | 2/3 -> 2/3 | L0.076 R0.076 -> L0.076 R0.076 |  |
| snake | FAIL -> FAIL | 0/0 -> 0/0 | R0.075! -> R0.075! |  |
| spider | FAIL -> FAIL | 2/10 -> 2/10 | LNone! RNone! -> LNone! RNone! |  |
| stag | FAIL -> FAIL | 7/7 -> 7/7 | L0.036! R0.037! -> L0.036! R0.037! |  |
| tiger | FAIL -> FAIL | 7/7 -> 6/7 | L0.103! R0.102! -> L0.109! R0.108! | tail0 knife 3.3 r was thigh faces -> PASS |
| troll | PASS -> PASS | 0/6 -> 0/6 | L0.072 R0.071 -> L0.074 R0.074 |  |
| turtle | PASS -> FAIL | 0/5 -> 3/5 | L0.105 R0.105 -> L0.105 R0.105 | GLB rebuilt 03:18 by another agent mid-run: new posed clip tail0 vs thighs 3.3% is the new GLB, not a kit change |
| werewolf | PASS -> PASS | 0/7 -> 0/7 | L0.067 R0.066 -> L0.082 R0.081 |  |
| yeti | PASS -> PASS | 0/4 -> 0/4 | L0.068 R0.068 -> L0.068 R0.067 |  |

## Follow-ups
- ogre: shoulder shelf (new gate) joins its known shoulder issues; rebuild work (HANDOFF step 3).
- seahorse: fin_dorsal root knife/strip now visible to the gate.
- elephant trunk0-3 are still trunk bones (central, no tail word): the trunk root is not probed; decide if a proboscis is a junction.
- eagle/turtle GLBs were rebuilt by other agents during the run; re-run their gates on the final GLBs.
- Shelf limits calibrated on one synthetic + the zoo only; tune with an owner-named case.
