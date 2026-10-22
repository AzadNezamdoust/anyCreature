# Zoo ROM audit (2026-10-22, bone-heat weights, kit/rom_gate.py auto joints)

Gates per pose: volume kept >= 0.70, stretch <= 2.0, flipped tris 0, new self-overlap <= 5% of joint region tris.
Weights v2 (kit/weights.py) was REJECTED on the werewolf pilot (judge preferred baseline in both orders, 2 rounds;
see abc/t8/weights/RESULT.md), so this is the current-weights audit only; no S4 changed.

| creature | poses pass | min vol | max stretch | inverted (poses) | new overlap (poses) | first fails |
|---|---|---|---|---|---|---|
| bear | 40/48 | 0.805 (shin.L flex) | 2.38 | 8 (4) | 541 (7) | chest flex (overlap); head flex (overlap); upperarm.L flex (stretch,inverted) |
| beetle | 39/42 | 0.413 (tibia2.L flex) | 1.723 | 15 (2) | 120 (3) | tibia1.L flex (vol,overlap); tibia2.L flex (vol,inverted,overlap); tibia3.L flex (vol,inverted,overlap) |
| boar | 50/58 | 0.789 (shin.L flex) | 1.835 | 10 (4) | 430 (7) | upperarm.L flex (inverted); upperarm.L side- (overlap); forearm.L flex (inverted,overlap) |
| chameleon | 68/76 | 0.667 (forearm.L flex) | 1.617 | 6 (2) | 308 (8) | forearm.L flex (vol,inverted,overlap); tail3 flex (overlap); tail4 flex (overlap) |
| crab | 41/52 | 0.41 (leg2b.L flex) | 2.433 | 7 (4) | 926 (10) | leg1a.L flex (inverted,overlap); leg1b.L flex (vol,overlap); leg2a.L flex (overlap) |
| crocodile | 55/60 | 0.794 (shin.L flex) | 1.705 | 26 (4) | 126 (3) | forearm.L flex (inverted,overlap); thigh.L flex (overlap); thigh.L side+ (inverted) |
| dragon | 53/62 | 0.564 (shin.L flex) | 1.643 | 16 (2) | 381 (8) | upperarm.L ext (overlap); upperarm.L side- (overlap); forearm.L flex (vol,inverted,overlap) |
| eagle | 43/46 | 0.837 (shin.L flex) | 1.788 | 6 (2) | 121 (2) | wing1.L flex (inverted); thigh.L side- (overlap); shin.L flex (inverted,overlap) |
| elephant | 63/74 | 0.87 (shin.L flex) | 2.283 | 23 (4) | 527 (9) | neck flex (stretch,inverted); skull side+ (overlap); skull side- (overlap) |
| fox | 50/58 | 0.69 (shin.L flex) | 2.152 | 12 (2) | 588 (8) | upperarm.L side- (overlap); forearm.L flex (stretch,inverted,overlap); tail0 ext (overlap) |
| frog | 32/38 | 0.504 (shin.L flex) | 1.895 | 14 (3) | 244 (6) | chest flex (overlap); upperarm.L ext (overlap); upperarm.L side- (overlap) |
| goblin | 39/44 | 0.688 (forearm.L flex) | 1.637 | 7 (2) | 184 (5) | chest side+ (overlap); chest side- (overlap); upperarm.L side- (overlap) |
| golem | 35/46 | 0.515 (upperarm.L flex) | 1.889 | 12 (3) | 812 (10) | spine side+ (overlap); spine side- (overlap); chest side+ (overlap) |
| gorilla | 38/44 | 0.72 (shin.L flex) | 1.686 | 18 (3) | 235 (6) | upperarm.L flex (overlap); upperarm.L ext (overlap); upperarm.L side- (overlap) |
| griffin | 53/58 | 0.694 (shin.L flex) | 2.501 | 5 (1) | 168 (4) | upperarm.L ext (overlap); upperarm.L side- (overlap); thigh.L flex (stretch) |
| hippo | 44/52 | 0.856 (forearm.L flex) | 2.05 | 15 (3) | 226 (7) | upperarm.L flex (inverted); upperarm.L side- (overlap); forearm.L flex (stretch,inverted,overlap) |
| imp | 53/58 | 0.709 (shin.L flex) | 1.823 | 28 (2) | 278 (5) | upperarm.L flex (overlap); upperarm.L side- (overlap); forearm.L flex (inverted,overlap) |
| knight | 40/44 | 0.803 (shin.L flex) | 2.036 | 16 (3) | 151 (3) | upperarm.L flex (inverted); upperarm.L side- (overlap); forearm.L flex (inverted,overlap) |
| koi | 29/30 | 0.962 (pec.L ext) | 1.485 | 0 (0) | 16 (1) | tail2 ext (overlap) |
| lizardman | 60/64 | 0.707 (forearm.L flex) | 1.961 | 20 (2) | 212 (4) | upperarm.L side- (overlap); upperarm.L twist+ (overlap); forearm.L flex (inverted,overlap) |
| manta_ray | 34/40 | 0.576 (tail2 ext) | 1.948 | 19 (2) | 0 (0) | lobe1.L flex (inverted); tail2 flex (vol); tail2 ext (vol) |
| mantis | 46/58 | 0.353 (femur2.L flex) | 3.067 | 19 (5) | 547 (11) | coxa1.L side- (overlap); femur1.L flex (vol,inverted,overlap); tibia1.L flex (vol,overlap) |
| minotaur | 51/56 | 0.751 (shin.L flex) | 1.596 | 17 (3) | 365 (4) | upperarm.L side- (overlap); forearm.L flex (inverted,overlap); thigh.L flex (inverted) |
| octopus | 39/52 | 0.794 (arm2b.L flex) | 2.517 | 21 (7) | 653 (12) | arm1a.L flex (stretch,overlap); arm1a.L ext (overlap); arm1a.L twist- (overlap) |
| ogre | 34/44 | 0.809 (forearm.L flex) | 2.012 | 23 (5) | 488 (7) | chest side+ (overlap); chest side- (overlap); neck flex (overlap) |
| owl | 37/38 | 0.787 (shin.L flex) | 1.684 | 8 (1) | 29 (1) | shin.L flex (inverted,overlap) |
| penguin | 40/48 | 0.659 (foot.L flex) | 1.697 | 8 (2) | 334 (8) | chest ext (overlap); chest side+ (overlap); chest side- (overlap) |
| raven_wyvern | 52/58 | 0.521 (shin.L flex) | 1.965 | 4 (3) | 206 (5) | neck1 side+ (overlap); neck1 side- (overlap); neck2 flex (overlap) |
| rhino | 52/58 | 0.839 (forearm.L flex) | 2.129 | 22 (3) | 228 (5) | upperarm.L flex (stretch); upperarm.L side- (overlap); forearm.L flex (inverted,overlap) |
| scorpion | 76/100 | 0.667 (femur.L flex) | 1.626 | 15 (5) | 1337 (24) | abdomen side+ (overlap); abdomen side- (overlap); tail2 ext (overlap) |
| seahorse | 59/64 | 0.925 (tail2 flex) | 1.836 | 0 (0) | 604 (5) | tail2 flex (overlap); tail3 flex (overlap); tail4 ext (overlap) |
| shark | 33/34 | 0.913 (tail3 side+) | 1.487 | 1 (1) | 6 (1) | fin.L ext (inverted,overlap) |
| snake | 64/64 | 0.949 (neck1 twist-) | 1.497 | 0 (0) | 0 (0) |  |
| spider | 31/46 | 0.342 (leg1b.L flex) | 2.002 | 24 (4) | 843 (15) | abdomen side+ (overlap); abdomen side- (overlap); leg1a.L flex (overlap) |
| stag | 43/50 | 0.663 (shin.L flex) | 1.964 | 10 (4) | 352 (6) | upperarm.L ext (inverted); upperarm.L side- (inverted,overlap); forearm.L flex (inverted,overlap) |
| tiger | 45/58 | 0.653 (shin.L flex) | 2.303 | 12 (5) | 662 (7) | neck flex (inverted); neck ext (stretch); upperarm.L flex (stretch,inverted) |
| troll | 39/42 | 0.822 (shin.L flex) | 2.211 | 15 (2) | 168 (3) | upperarm.L side- (overlap); forearm.L flex (stretch,inverted,overlap); shin.L flex (inverted,overlap) |
| turtle | 42/44 | 0.72 (foot.L flex) | 1.613 | 28 (2) | 64 (2) | hand.L flex (inverted,overlap); foot.L flex (inverted,overlap) |
| werewolf | 50/58 | 0.653 (forearm.L flex) | 1.63 | 6 (3) | 349 (7) | neck flex (overlap); upperarm.L side- (overlap); forearm.L flex (vol,inverted,overlap) |
| yeti | 37/42 | 0.788 (forearm.L flex) | 1.869 | 19 (3) | 287 (4) | upperarm.L side- (overlap); forearm.L flex (inverted,overlap); thigh.L flex (inverted) |

Fail counts by gate (poses): inverted 112, overlap 243, stretch 25, vol 36
Creatures audited: 40
