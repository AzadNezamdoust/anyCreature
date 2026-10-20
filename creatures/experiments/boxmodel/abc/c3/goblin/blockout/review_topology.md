# goblin c3 cage: form and topology review

Evidence: blockout/1_grey, 4_topology, 4_topology_table, 5_profiles, 5_rom, 3_proportions, topology.json; concept refs/gpt/goblin/concept_2.png; previous cage abc/c2/goblin/blockout (1_grey, 4_topology).

## Scores

| | form /10 | topology /10 |
|---|---|---|
| c3 (new) | 7.0 | 7.5 |
| c2 (previous) | 6.0 | 5.0 |

Verdict: **FIX** (one small round; no gate rebuild, all five are local).

## Form (head, arms, legs against the concept)

- **Arms: good.** Front view reads deltoid mass, pinched elbow, forearm swell, thin wrist, broad hand. Width profile RMS 2.61 %, tube score 0.78 vs 0.81. Clearly better than c2, whose arm was a near-even taper. The hand is now a mitten paddle and is about 25 % too wide at the last two stations (red over black in 5_profiles), so it reads as a club rather than the concept's long splayed hand.
- **Legs: acceptable.** Thigh, narrow knee, calf and a broad planted foot read in front view (RMS 2.09 %). From the side the thigh-to-shin bend is soft: the concept has a sharp bent knee over a thin shin, the cage has a gentle S. Ankle has 2 rings only, so the thin-ankle/broad-foot break is one edge.
- **Head: the weakest part.** Side view is right: cranium dome, brow shelf, hooked nose, chin. Front view is a tall egg: the cranium is narrow at the crown, and there is no cheek or jaw mass, where the concept has a wide bulbous skull, wide cheekbones and a wide grinning jaw narrowing to a pointed chin. The head gate FAIL (RMS 19.6 %) is mostly the declared ear-span artefact, but the first two width stations are really over (red above black) and the mid station is really under, which is the same egg-not-skull reading. Not a wedge any more, but brow/cheek/jaw are not three masses yet.
- Ears are flat untapered slabs with no cup; acceptable at blockout, noted only for density below.

## Topology (as judged in production)

Good:
- 478 quads, 0 triangles, 0 n-gons, 0 valence-6 poles (c2: magenta fans across both hands and feet, a triangle at the wrist, an n-gon under the foot, toe/finger clusters at 3-5x body density).
- Even density: body edge p90/p10 2.72; regions 0.92-1.17x; arms 0 % over 3:1.
- 3 rings at elbow, wrist and knee; closed loops over shoulder and hip; 0 of 60 poles in a joint band.
- ROM: swing and crouch bend cleanly, hip keeps volume. Fold-over 38/956 triangles (1.72 % of area).

Weak:
- Neck: 2 rings at 0.11 x width spacing, i.e. one crammed double edge under the jaw, not a neck loop set; head turn/nod will shear one band. Valence-5 poles sit on the neck/shoulder line right behind it (back 3/4 view).
- Face: no eye or mouth loops (table warn FAIL). Valence-5 poles sit on the cheek exactly where the grin corner will be cut; this character's defining feature is the mouth.
- Shoulder: arm flow 0.33, just over the 0.30 limit; a valence-5 pole on top of the arm root and one at the chest/armpit corner. In the fold pose the elbow inside collapses (side wire: forearm faces pinch against the upper arm).
- Ankle/foot: 2 ankle rings; the heel and sole are long faces fanning to the heel corner (side and under-belly views); worst aspect 7.6:1 is here and on the ears.
- Ears: 19 % of faces over 5:1, density 0.65x, edge ratio 3.84 (just inside 4). Straight strip loft; fine for a rigid ear, poor if the ear is to flop.

Table vs eye: I agree with the table everywhere except the neck, which it counts as "3 loops" and passes; by eye it is one tight double edge, so the eye is right.

## Against the previous cage

Topology is a clear step up (+2.5): c2 would have been rejected in production on the hand/foot fans alone; c3 is a clean all-quad cage a rigger could weight today. Form is a modest step up (+1.0): arms and legs gained real swell and taper, but the head front is barely changed and c3 gave up c2's fingers and toes, which carried a lot of the goblin read.

## Fixes (max 5, in order)

1. **Head front masses.** Widen the cranium at the crown ring by about 12 % and the cheekbone ring by about 10 %; pull the jaw ring in toward a pointed chin (chin width about 40 % of cheek width). Target: front view reads skull-cheek-chin, not an egg.
2. **Mouth and eye loops.** Declare META['landmarks'] and add one closed loop round the mouth (grin line, corner at the current cheek valence-5 pole, which moves 1 face outward onto the cheek flat) and one round each eye socket under the brow shelf. About +16 to +24 faces on the head.
3. **Neck loops.** Spread the two crammed rings into 3 rings at 0.25-0.35 x neck width spacing (now 0.11); move the two valence-5 poles off the neck/shoulder line 1 face down onto the upper back.
4. **Shoulder flow and elbow inside.** Route 2 more of the arm's lengthwise edges into the chest/back (flow 0.33 to at least 0.5) and move the arm-root-top pole 1 face inboard onto the trapezius flat; space the elbow rings from 0.36 to about 0.45 x width on the inside so the fold pose does not pinch.
5. **Ankle, heel and hand end.** Add a 3rd ankle ring (spacing about 0.3 x width); re-grid the heel/sole so no face exceeds 4:1 (now 7.6:1); narrow the hand paddle by about 20 % at the last two stations, and split its end into 3 finger stubs if the brief does not make fingers a stage-3 piece.

Not required: ear cup and ear density (leave unless the ear is to deform).
