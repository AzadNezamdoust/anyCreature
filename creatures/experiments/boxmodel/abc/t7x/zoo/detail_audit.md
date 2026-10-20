# Detail audit: chunky details at game distance (2026-10-21)

Owner, 2026-10-21: the creatures are for GAMES. Fingers, toes and small details must be chunky, visible and understandable at game camera distance. Bigger creatures are seen bigger on screen, so they carry more details (tiers).

- **What ran:** `kit/detail_gate.py` on every zoo `stage4/*.glb`, **no fixes applied**.
  - Single-GLB command: `py -3.11 creatures/experiments/boxmodel/kit/detail_gate.py <glb> <outdir> [--tier N]`.
  - Inside a round: `run.py <prog> --details`.
- **floor:** the minimum section thickness, `max(1.2% H, 3 px at a 256 px creature height)`.
  - Tier 1 doubles the 1.2% part (2.4% H): small creatures need exaggerated details.
  - Fingers and toes also need length >= 4% H, and length / thickness (L/t) <= 4.5 (tier 1) or 6 (tiers 2-3). Above that limit a digit reads as a stick.
- **features:** distinct readable feature groups, counted once per mirrored pair. A group can be a piece, a body appendage kind, the eye, or a body paint region.
  - Needed: tier 1 3-8, tier 2 6-16, tier 3 12-30.
- **tier:** from the body's mass size `cbrt(volume)`: under 0.45 m is tier 1, over 1.0 m is tier 3.
  - `*` marks an owner-list override, set as `META detail_tier=N` in goblin, eagle and yeti (2), chameleon and spider (1), and dragon (3).
  - Octopus stays tier 1 (auto): the owner listed "octopus-large", and ours is 0.49 m tall.
- **Worst details:** the worst FAIL per piece/kind, with how many items of that kind fail (xN).
  - "t" is the p10 minimum section thickness, with its pixel width at a 256 px creature height.
  - "L" is the visible length.

Result: **10 of 40 PASS** (boar, crab, gorilla, minotaur, octopus, scorpion, seahorse, shark, tiger, yeti). Every tier-3 creature FAILS the count: they have 4-8 feature groups and need 12. The commonest thin details are:
- claws: fox, penguin, owl talons, spider, imp, beetle, griffin;
- rest-pose hands/feet: lizardman, werewolf;
- spines and antennae: mantis;
- teeth: croc;
- barbels: koi;
- tongue: snake;
- antler tines: stag;
- stick toes: frog, penguin, eagle, raven_wyvern, chameleon.

## Table

| creature | tier | H m | floor mm | features (need) | gated / FAIL | worst details (thickness p10, length, length/thickness) | verdict |
|---|---|---|---|---|---|---|---|
| bear | 2 | 1.29 | 15.48 | 4 (6-16) FAIL | 26 / 0 | - | FAIL |
| beetle | 1 | 0.619 | 14.85 | 5 (3-8) | 21 / 14 | claws/claw x12: t 6.6 mm (2.7 px), L 64.8 mm, L/t 9.8; mandible/horn x2: t 9.5 mm (3.9 px), L 35.8 mm, L/t 3.8 | FAIL |
| boar | 2 | 0.928 | 11.14 | 9 (6-16) | 17 / 0 | - | PASS |
| chameleon | 1* | 1.12 | 26.88 | 5 (3-8) | 19 / 14 | crest/horn x6: t 14.6 mm (3.3 px), L 68.5 mm, L/t 4.7; toes/toe x8: t 23.6 mm (5.4 px), L 160.7 mm, L/t 6.8 | FAIL |
| crab | 1 | 0.255 | 6.12 | 5 (3-8) | 14 / 0 | - | PASS |
| crocodile | 2 | 0.465 | 5.58 | 5 (6-16) FAIL | 31 / 10 | teeth/tooth x10: t 1.5 mm (0.9 px), L 18.1 mm, L/t 11.7 | FAIL |
| dragon | 3* | 1.81 | 21.72 | 7 (12-30) FAIL | 36 / 0 | - | FAIL |
| eagle | 2* | 0.854 | 10.24 | 8 (6-16) | 25 / 2 | footL/toe x1: t 14.5 mm (4.3 px), L 117.3 mm, L/t 8.1; footR/toe x1: t 15.1 mm (4.5 px), L 106.8 mm, L/t 7.1 | FAIL |
| elephant | 3 | 2.98 | 35.76 | 6 (12-30) FAIL | 20 / 0 | - | FAIL |
| fox | 2 | 1.15 | 13.8 | 5 (6-16) FAIL | 19 / 12 | claws/claw x12: t 6.3 mm (1.4 px), L 35.9 mm, L/t 5.7 | FAIL |
| frog | 1 | 0.307 | 7.38 | 2 (3-8) FAIL | 22 / 18 | feet/toe x10: t 5.5 mm (4.6 px), L 49.4 mm, L/t 9.0; fingers/finger x8: t 5.5 mm (4.6 px), L 15.3 mm, L/t 2.8 | FAIL |
| goblin | 2* | 0.99 | 11.88 | 5 (6-16) FAIL | 24 / 0 | - | FAIL |
| golem | 3 | 2.005 | 24.06 | 5 (12-30) FAIL | 10 / 2 | toes/toe x2: t 21.6 mm (2.8 px), L 157.9 mm, L/t 7.3 | FAIL |
| gorilla | 2 | 1.5 | 18.0 | 6 (6-16) | 24 / 0 | - | PASS |
| griffin | 2 | 1.514 | 18.17 | 9 (6-16) | 22 / 4 | claws/claw x4: t 17.0 mm (2.9 px), L 50.2 mm, L/t 3.0 | FAIL |
| hippo | 3 | 1.638 | 19.66 | 4 (12-30) FAIL | 19 / 0 | - | FAIL |
| imp | 1 | 0.806 | 19.34 | 6 (3-8) | 25 / 15 | claws_L/claw x3: t 6.2 mm (2.0 px), L 41.0 mm, L/t 6.7; claws_R/claw x3: t 6.2 mm (2.0 px), L 41.0 mm, L/t 6.7; hand_L/finger x4: t 10.3 mm (3.3 px), L 43.1 mm, L/t 4.2 | FAIL |
| knight | 2 | 1.884 | 22.61 | 9 (6-16) | 5 / 1 | crest/horn x1: t 18.0 mm (2.4 px), L 257.7 mm, L/t 14.3 | FAIL |
| koi | 1 | 0.247 | 5.93 | 5 (3-8) | 7 / 2 | barbels/antenna x2: t 2.2 mm (2.3 px), L 16.3 mm, L/t 7.4 | FAIL |
| lizardman | 2 | 2.0 | 24.0 | 5 (6-16) FAIL | 19 / 14 | _rest_hand/finger x8: t 5.4 mm (0.7 px), L 46.8 mm, L/t 8.7; _rest_foot/toe x6: t 10.8 mm (1.4 px), L 61.7 mm, L/t 5.7 | FAIL |
| manta_ray | 2 | 0.545 | 6.54 | 5 (6-16) FAIL | 5 / 0 | - | FAIL |
| mantis | 1 | 0.535 | 12.83 | 4 (3-8) | 21 / 14 | spines/horn x12: t 1.6 mm (0.8 px), L 16.2 mm, L/t 10.0; antenna/antenna x2: t 3.3 mm (1.6 px), L 192.0 mm, L/t 58.3 | FAIL |
| minotaur | 2 | 2.422 | 29.06 | 9 (6-16) | 8 / 0 | - | PASS |
| octopus | 1 | 0.485 | 11.64 | 3 (3-8) | 8 / 0 | - | PASS |
| ogre | 3 | 2.038 | 24.46 | 6 (12-30) FAIL | 14 / 0 | - | FAIL |
| owl | 1 | 0.559 | 13.41 | 7 (3-8) | 22 / 16 | talons/claw x8: t 1.5 mm (0.7 px), L 15.0 mm, L/t 10.0; toes/toe x8: t 7.3 mm (3.4 px), L 37.1 mm, L/t 5.1 | FAIL |
| penguin | 2 | 1.098 | 13.18 | 5 (6-16) FAIL | 16 / 12 | claws/claw x6: t 3.0 mm (0.7 px), L 20.9 mm, L/t 7.0; toes/toe x6: t 5.6 mm (1.3 px), L 74.6 mm, L/t 13.2 | FAIL |
| raven_wyvern | 2 | 1.236 | 14.83 | 7 (6-16) | 31 / 6 | toes/toe x6: t 27.1 mm (5.6 px), L 235.3 mm, L/t 8.7 | FAIL |
| rhino | 3 | 1.75 | 21.0 | 7 (12-30) FAIL | 21 / 0 | - | FAIL |
| scorpion | 1 | 0.504 | 12.11 | 6 (3-8) | 13 / 0 | - | PASS |
| seahorse | 1 | 0.505 | 12.11 | 5 (3-8) | 1 / 0 | - | PASS |
| shark | 2 | 0.95 | 11.4 | 6 (6-16) | 14 / 0 | - | PASS |
| snake | 1 | 0.36 | 8.64 | 4 (3-8) | 4 / 2 | tongue/antenna x2: t 2.7 mm (1.9 px), L 60.0 mm, L/t 22.6 | FAIL |
| spider | 1* | 0.878 | 21.07 | 3 (3-8) | 17 / 8 | claws/claw x8: t 8.3 mm (2.4 px), L 44.0 mm, L/t 5.3 | FAIL |
| stag | 2 | 2.026 | 24.31 | 8 (6-16) | 21 / 8 | tines/horn x8: t 16.9 mm (2.1 px), L 161.5 mm, L/t 9.6 | FAIL |
| tiger | 2 | 1.128 | 13.54 | 6 (6-16) | 22 / 0 | - | PASS |
| troll | 3 | 2.215 | 26.58 | 8 (12-30) FAIL | 24 / 2 | toes_L/toe x1: t 26.5 mm (3.1 px), L 178.1 mm, L/t 6.7; toes_R/toe x1: t 29.8 mm (3.4 px), L 200.2 mm, L/t 6.7 | FAIL |
| turtle | 2 | 0.904 | 10.85 | 5 (6-16) FAIL | 23 / 0 | - | FAIL |
| werewolf | 2 | 2.22 | 26.64 | 7 (6-16) | 32 / 10 | _rest_hand/finger x10: t 9.6 mm (1.1 px), L 132.4 mm, L/t 13.8 | FAIL |
| yeti | 2* | 2.4 | 28.8 | 6 (6-16) | 92 / 0 | - | PASS |
10 pass of 40

(The frog row is the before state. The frog pass below fixes it.)

## Tier 3: missing details vs the concept sheet

These are concrete adds for the next pass. Each one is a geometry step: extrusions, insets, seated pieces, or a flat colour region. No noise, no sculpt. Every add stays chunky and must pass detail_gate.

**hippo** (4 groups, needs 12). It has an eye, 16 nails, ears, a tail and a pink belly paint.
1. Toenails per toe, 4 per foot, as separate chunky pale nail caps. The sheet shows 4 rounded nails on every foot; ours are dark and flat. Cream nails would read as a group.
2. Nostril mounds: two raised domes on top of the muzzle, each with a dark inset nostril.
3. Eye ridges: a raised brow knob over each eye. The eyes sit on bumps on the skull top.
4. Skin folds at the neck: 2-3 stepped ring planes behind the jaw.
5. Skin folds at the legs: a fold ring at each wrist/ankle above the foot.
6. Mouth line: a long inset groove from the muzzle front to under the eye, in a darker colour.
7. Tail bristle: a flat tuft fan at the tail tip.
8. Pink muzzle/cheek paint and pink inner ears: two paint regions.
9. A rump cleft (rear view): a vertical inset groove.
10. Lower-lip bulge plane.

**elephant** (6 groups: eye, nails, tusks, ears, tail, pale paint).
1. Tail tuft (the sheet has a dark brush): a flat fan piece.
2. Trunk rings: 4-6 stepped ring planes along the trunk.
3. Knee/ankle skin folds: a fold ring per leg.
4. Ear rim: a thickened edge loop plus an inner-ear colour.
5. Brow ridge over the eye.
6. Mouth / lower lip under the trunk root.
7. Toenails: already chunky (PASS); keep 3 per front foot.
8. Darker sole-pad paint.
9. Forehead dome step.

**rhino** (7 groups: eye, 2 horns, nails, ears, tail, leg paint).
1. Armour skin folds, the rhino signature on the sheet: a shoulder fold behind the neck, a flank fold in front of the thigh, and a neck fold. These are 3 stepped plane bands.
2. Tail-tip tuft.
3. Ear rims plus inner-ear paint.
4. Eye ridge/brow.
5. Mouth line plus a lip point.
6. Leg ankle folds.
7. Dark nails per toe: already PASS. Three per foot reads well.
8. Rump cleft.

**troll** (8 groups). The sheet shows a big long nose, toes and fingers already there, and a ragged loincloth.
1. Nose: a big separate seated piece with nostril insets.
2. Brow ridge.
3. Ear inner colour.
4. Toenails (5 per foot on the sheet; use 4 game toes) plus fingernails.
5. Knuckle bumps on the hands.
6. Loincloth jag teeth (the sheet's ragged hem): a zig-zag edge on the flap pieces.
7. Navel inset plus a belly paint region.
8. Kneecaps.
9. Chest/pec plane step.
10. 2-3 warts/bumps on the shoulders.
11. Fix the 2 stick toes: L/t 6.7.

**ogre** (6 groups: eye, flaps, nails, tusks, belly paint; the belt and strap are not counted, their stem is shared).
1. A brow ridge over the small eyes.
2. Ear pieces: pointed ears on the sheet.
3. A navel and belly fold under the strap.
4. Toenails per toe: the sheet shows 4-5 chunky toes. Use 4 fat toes plus nails.
5. Knuckles plus fingernails.
6. A loincloth jag hem.
7. Strap buckle/knot piece.
8. Kneecaps.
9. Nostrils.
10. Chin/jowl plane.
11. A lower-lip bulge behind the tusks.

**golem** (5 groups: eye, plates, toes FAIL, 2 paint regions).
1. Glowing crack lines (the sheet's blue chest crack): an inset groove in a glow colour.
2. Moss caps on the shoulders, head and forearms: seated flat-colour slab pieces.
3. Rock-block seams: inset grooves between the boulder masses, each limb segment a separate block.
4. Fist knuckle blocks.
5. Brow block over the glowing eyes.
6. Toe blocks: fix the 2 stick toes (L/t 7.3).
7. Chest plate seams.
8. Back plate seams.

**dragon** (7 groups, tier 3 by override).
1. Dorsal spike row: spine to tail, about 14 on the sheet; ours has 10 spikes. These are cream tooth-shaped pieces.
2. Belly scale plates: cream ventral band segments, as stepped inset bands.
3. Tail arrow-head spade.
4. Wing finger bones (cream struts) plus thumb claws.
5. Horn pair plus a cheek frill horn.
6. Brow ridge.
7. Nostrils.
8. Toe claws: already chunky (PASS).
9. Elbow spikes.
10. Mouth line.
11. Knee scales.
