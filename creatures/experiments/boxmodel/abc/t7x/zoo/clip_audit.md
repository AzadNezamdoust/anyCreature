# Clip audit: zoo S4 clips (kit/clip_gate.py + kit/clipkit.py), 2026-10-23

Gate: penetration <= 0.5 % H, planted-foot slide std <= 0.3 % H/frame, idle/attack plant speed <= 0.3, loop gap <= 0.5 % H, no NaN, no quat flips.
Fix = animation only, spliced onto the current stage4 GLB (meshes/skin/nodes byte-kept; identity check PASS on all). Originals: `<c>/stage4/before_clips/<c>.glb`. Re-run: `run.py <c>/<c>.py --clips --fix-clips` (reads clips from the backup, keeps current weights). Per-creature sheet + json: `<c>/stage4/clips/`.
gorilla, yeti stage4 were newer than this run's start (another agent re-weighted): clips applied on top of their GLB, weights untouched.
crab: fix REVERTED (idle/attack penetration got worse, 8-leg rig, no gait table) -> original clips.

Result: 29/40 PASS (crab reverted counted FAIL). Columns: pen/slide % H, before -> after.

| creature | gate | feet | gait | idle | move | attack | mesh same | residual fails |
|---|---|---|---|---|---|---|---|---|
| bear | PASS | 4 | quad_trot | 0.25/0.08 -> 0.03/0.04 | 14.68/1.29 -> 0.00/0.06 | 10.18/2.55 -> 0.00/0.14 | True |  |
| beetle | PASS | 6 | None | 0.00/0.05 -> 0.00/0.00 | 8.42/0.80 -> 0.00/0.12 | 7.91/0.81 -> 0.00/0.02 | True |  |
| boar | PASS | 4 | quad_trot | 0.03/0.10 -> 0.00/0.00 | 3.68/1.10 -> 0.00/0.04 | 1.04/1.06 -> 0.00/0.10 | True |  |
| chameleon | PASS | 4 | quad_trot | 0.49/0.06 -> 0.01/0.00 | 6.83/1.03 -> 0.01/0.00 | 0.50/0.19 -> 0.01/0.00 | True |  |
| crab | FAIL | 8 | None | -0.00/0.10 -> 1.57/0.05 | 3.25/2.20 -> 2.35/0.26 | -0.00/0.00 -> 1.02/0.00 | True | pen 1.017  slide 0.000  plant 0.000  loop 0.000  penetration_pctH 1.017 > 0.5; pen 1.569  slide 0.048  plant 0.035  loop |
| crocodile | PASS | 4 | quad_trot | 0.00/0.03 -> 0.01/0.00 | 4.07/2.16 -> 0.00/0.00 | 3.81/0.00 -> 0.01/0.00 | True |  |
| dragon | PASS | 4 | quad_trot | 0.00/0.04 -> 0.00/0.19 | 8.85/1.07 -> 0.00/0.14 | 4.00/0.73 -> 0.00/0.08 | True |  |
| eagle | PASS | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 5.75/0.20 -> 0.00/0.00 | 3.19/0.57 -> -0.00/0.07 | True |  |
| elephant | PASS | 4 | quad_trot | 0.08/0.08 -> 0.01/0.01 | 2.62/0.95 -> 0.00/0.04 | 1.01/0.33 -> 0.01/0.02 | True |  |
| fox | PASS | 4 | quad_trot | -0.00/0.08 -> -0.00/0.00 | 3.24/2.70 -> 0.00/0.25 | 1.16/0.22 -> 0.00/0.02 | True |  |
| frog | FAIL | 4 | quad_trot | -0.00/0.06 -> 0.00/0.00 | 2.98/0.73 -> 0.00/0.00 | 2.38/0.41 -> 0.00/0.62 | True | pen 0.000  slide 0.623  plant 0.791  loop 0.000  foot_slide_std_pctH 0.623 > 0.3; plant speed 0.791 > 0.3 |
| goblin | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 3.06/0.75 -> 0.00/0.05 | -0.00/0.00 -> 0.00/0.00 | True |  |
| golem | PASS | 2 | biped_walk | 0.00/0.00 -> 0.00/0.00 | 9.91/1.08 -> -0.00/0.00 | 2.49/0.14 -> -0.00/0.04 | True |  |
| gorilla | PASS | 4 | quad_trot | 0.00/0.08 -> 0.00/0.00 | 6.64/1.40 -> 0.00/0.25 | 4.45/2.40 -> 0.00/0.09 | True |  |
| griffin | FAIL | 4 | quad_trot | 0.00/0.05 -> -0.00/0.08 | 8.97/2.38 -> 0.00/0.53 | 3.60/1.06 -> 0.00/0.04 | True | pen 0.000  slide 0.527  plant 0.538  loop 0.000  foot_slide_std_pctH 0.527 > 0.3 |
| hippo | PASS | 4 | quad_trot | 0.14/0.07 -> 0.03/0.00 | 5.16/1.19 -> 0.01/0.05 | 1.07/0.73 -> 0.02/0.01 | True |  |
| imp | FAIL | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 3.23/0.35 -> 0.00/0.33 | -0.00/0.00 -> -0.00/0.00 | True | pen 0.000  slide 0.327  plant 0.401  loop 0.000  foot_slide_std_pctH 0.327 > 0.3 |
| knight | FAIL | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 2.11/0.86 -> 0.00/0.66 | -0.00/0.00 -> 0.00/0.00 | True | pen 0.000  slide 0.657  plant 1.665  loop 0.000  foot_slide_std_pctH 0.657 > 0.3 |
| koi | PASS | 0 | None | 6.99/0.00 -> 0.00/0.00 | 12.82/0.00 -> 0.00/0.00 | 16.71/0.00 -> 0.00/0.00 | True |  |
| lizardman | PASS | 2 | biped_walk | 0.00/0.00 -> 0.00/0.00 | 1.68/0.59 -> -0.00/0.04 | 0.00/0.00 -> 0.00/0.00 | True |  |
| manta_ray | FAIL | 2 | biped_walk | 2.30/0.19 -> 0.00/0.19 | 28.05/0.01 -> 0.00/0.01 | 35.13/2.58 -> 0.00/0.49 | True | pen 0.000  slide 0.493  plant 1.123  loop 0.000  foot_slide_std_pctH 0.493 > 0.3; plant speed 1.123 > 0.3 |
| mantis | PASS | 4 | quad_trot | -0.00/0.03 -> 0.00/0.00 | 6.82/0.89 -> 0.00/0.00 | 1.16/0.25 -> 0.00/0.00 | True |  |
| minotaur | PASS | 2 | biped_walk | 0.00/0.00 -> 0.00/0.00 | 1.92/0.53 -> -0.00/0.00 | 0.00/0.00 -> 0.00/0.00 | True |  |
| octopus | FAIL | 4 | quad_trot | 11.51/0.25 -> 2.54/0.13 | 19.51/1.03 -> 9.83/0.58 | 44.85/3.54 -> 36.42/3.23 | True | pen 36.425  slide 3.230  plant 2.230  loop 0.000  penetration_pctH 36.425 > 0.5; foot_slide_std_pctH 3.23 > 0.3; plant s |
| ogre | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 2.20/0.44 -> 0.00/0.02 | -0.00/0.00 -> 0.00/0.00 | True |  |
| owl | FAIL | 2 | biped_walk | 0.00/0.00 -> -0.00/0.00 | 4.65/0.92 -> -0.00/0.07 | 4.57/0.64 -> 0.00/0.59 | True | pen 0.004  slide 0.591  plant 0.362  loop 0.000  foot_slide_std_pctH 0.591 > 0.3; plant speed 0.362 > 0.3 |
| penguin | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 2.31/0.13 -> 0.00/0.11 | -0.00/0.00 -> 0.00/0.00 | True |  |
| raven_wyvern | PASS | 2 | biped_walk | 0.00/0.00 -> -0.00/0.00 | 18.15/1.36 -> -0.00/0.00 | 2.10/0.00 -> 0.00/0.00 | True |  |
| rhino | PASS | 4 | quad_trot | 0.17/0.08 -> 0.00/0.03 | 3.65/1.47 -> 0.00/0.29 | 0.76/0.70 -> 0.00/0.26 | True |  |
| scorpion | PASS | 8 | None | 1.96/0.11 -> 0.00/0.05 | 0.23/0.22 -> 0.00/0.00 | 0.00/0.34 -> 0.00/0.00 | True |  |
| seahorse | PASS | 0 | None | 0.53/0.00 -> 0.00/0.00 | 1.24/0.00 -> 0.00/0.00 | 0.00/0.00 -> 0.00/0.00 | True |  |
| shark | PASS | 0 | None | 0.00/0.00 -> 0.00/0.00 | -0.00/0.00 -> -0.00/0.00 | 2.44/0.00 -> 0.00/0.00 | True |  |
| snake | PASS | 0 | None | 0.04/0.00 -> 0.00/0.00 | 1.84/0.00 -> 0.00/0.00 | 1.41/0.00 -> -0.00/0.00 | True |  |
| spider | PASS | 8 | None | 5.03/0.25 -> 0.01/0.09 | 0.34/0.46 -> 0.00/0.00 | 10.72/1.42 -> 0.01/0.11 | True |  |
| stag | FAIL | 4 | quad_trot | 0.04/0.06 -> 0.01/0.00 | 1.78/1.87 -> 0.00/1.82 | 0.31/0.26 -> 0.25/0.01 | True | pen 0.000  slide 1.821  plant 2.990  loop 0.000  foot_slide_std_pctH 1.821 > 0.3 |
| tiger | FAIL | 4 | quad_trot | 0.00/0.09 -> 0.00/0.06 | 8.30/1.15 -> 0.00/0.25 | 4.34/1.31 -> 0.00/0.88 | True | pen 0.000  slide 0.877  plant 0.624  loop 0.000  foot_slide_std_pctH 0.877 > 0.3; plant speed 0.624 > 0.3 |
| troll | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 3.19/0.46 -> 0.00/0.29 | -0.00/0.00 -> 0.00/0.00 | True |  |
| turtle | FAIL | 4 | quad_trot | 0.00/0.00 -> 0.00/0.00 | 3.25/0.45 -> 0.00/0.39 | 1.42/0.20 -> 0.00/0.20 | True | pen 0.000  slide 0.386  plant 0.654  loop 0.000  foot_slide_std_pctH 0.386 > 0.3 |
| werewolf | PASS | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 0.94/1.02 -> 0.00/0.00 | -0.00/0.00 -> -0.00/0.00 | True |  |
| yeti | PASS | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 3.46/0.39 -> 0.00/0.22 | -0.00/0.00 -> -0.00/0.00 | True |  |

Residual causes (honest): limb reach limit at full extension (tiger/owl/frog attack swipes, stag/knight move strides) -> IK clamps and the foot skims; octopus tentacles treated as feet (huge authored penetration, improved but far over gate); manta_ray wingtips detected as feet. Next: toe-roll / end-bone rotation when out of reach, per-creature foot exclusion list.
