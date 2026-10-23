# Clip audit: zoo S4 clips (kit/clip_gate.py + kit/clipkit.py), 2026-10-23

Gate: penetration <= 0.5 % H, planted-foot slide std <= 0.3 % H/frame, idle/attack plant speed <= 0.3, loop gap <= 0.5 % H, no NaN, no quat flips.
Fix = animation only, spliced onto the current stage4 GLB (meshes/skin/nodes byte-kept; identity check PASS on all). Originals: `<c>/stage4/before_clips/<c>.glb`. Re-run: `run.py <c>/<c>.py --clips --fix-clips` (reads clips from the backup, keeps current weights). Per-creature sheet + json: `<c>/stage4/clips/`.
gorilla, yeti stage4 were newer than this run's start (another agent re-weighted): clips applied on top of their GLB, weights untouched.

Result: 40/40 PASS after round 2 (2026-10-23; gorilla, yeti untouched from round 1). Round 1 was 29/40. Columns: pen/slide % H, before -> after.

| creature | gate | feet | gait | idle | move | attack | mesh same | residual fails |
|---|---|---|---|---|---|---|---|---|
| bear | PASS | 4 | quad_trot | 0.25/0.08 -> 0.03/0.04 | 14.68/1.29 -> 0.00/0.06 | 10.18/2.55 -> 0.00/0.14 | True |  |
| beetle | PASS | 6 | None | 0.00/0.05 -> 0.00/0.00 | 8.42/0.80 -> 0.00/0.12 | 7.91/0.81 -> 0.00/0.02 | True |  |
| boar | PASS | 4 | quad_trot | 0.03/0.10 -> 0.00/0.00 | 3.68/1.10 -> 0.00/0.04 | 1.04/1.06 -> 0.00/0.10 | True |  |
| chameleon | PASS | 4 | quad_trot | 0.49/0.06 -> 0.01/0.00 | 6.83/1.03 -> 0.01/0.00 | 0.50/0.19 -> 0.01/0.00 | True |  |
| crab | PASS | 8 | octo_tetrapod | -0.00/0.10 -> 0.00/0.03 | 3.25/2.20 -> 0.00/0.00 | -0.00/0.00 -> 0.00/0.00 | True | round 2 |
| crocodile | PASS | 4 | quad_trot | 0.00/0.03 -> 0.01/0.00 | 4.07/2.16 -> 0.00/0.00 | 3.81/0.00 -> 0.01/0.00 | True |  |
| dragon | PASS | 4 | quad_trot | 0.00/0.04 -> 0.00/0.19 | 8.85/1.07 -> 0.00/0.14 | 4.00/0.73 -> 0.00/0.08 | True |  |
| eagle | PASS | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 5.75/0.20 -> 0.00/0.00 | 3.19/0.57 -> -0.00/0.07 | True |  |
| elephant | PASS | 4 | quad_trot | 0.08/0.08 -> 0.01/0.01 | 2.62/0.95 -> 0.00/0.04 | 1.01/0.33 -> 0.01/0.02 | True |  |
| fox | PASS | 4 | quad_trot | -0.00/0.08 -> -0.00/0.00 | 3.24/2.70 -> 0.00/0.25 | 1.16/0.22 -> 0.00/0.02 | True |  |
| frog | PASS | 4 | quad_trot | -0.00/0.06 -> 0.00/0.00 | 2.98/1.19 -> 0.00/0.00 | 2.38/0.41 -> 0.00/0.00 | True | round 2 |
| goblin | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 3.06/0.75 -> 0.00/0.05 | -0.00/0.00 -> 0.00/0.00 | True |  |
| golem | PASS | 2 | biped_walk | 0.00/0.00 -> 0.00/0.00 | 9.91/1.08 -> -0.00/0.00 | 2.49/0.14 -> -0.00/0.04 | True |  |
| gorilla | PASS | 4 | quad_trot | 0.00/0.08 -> 0.00/0.00 | 6.64/1.40 -> 0.00/0.25 | 4.45/2.40 -> 0.00/0.09 | True |  |
| griffin | PASS | 4 | quad_trot | 0.00/0.05 -> 0.00/0.00 | 8.97/2.38 -> 0.00/0.00 | 3.60/0.76 -> 0.00/0.07 | True | round 2 |
| hippo | PASS | 4 | quad_trot | 0.14/0.07 -> 0.03/0.00 | 5.16/1.19 -> 0.01/0.05 | 1.07/0.73 -> 0.02/0.01 | True |  |
| imp | PASS | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 3.23/0.35 -> 0.15/0.05 | -0.00/0.00 -> -0.00/0.00 | True | round 2 |
| knight | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 2.11/0.86 -> 0.01/0.00 | -0.00/0.00 -> 0.00/0.00 | True | round 2 |
| koi | PASS | 0 | None | 6.99/0.00 -> 0.00/0.00 | 12.82/0.00 -> 0.00/0.00 | 16.71/0.00 -> 0.00/0.00 | True |  |
| lizardman | PASS | 2 | biped_walk | 0.00/0.00 -> 0.00/0.00 | 1.68/0.59 -> -0.00/0.04 | 0.00/0.00 -> 0.00/0.00 | True |  |
| manta_ray | PASS | 0 | None | 2.30/0.00 -> 0.00/0.00 | 28.05/0.00 -> 0.00/0.00 | 35.13/0.00 -> 0.00/0.00 | True | round 2 |
| mantis | PASS | 4 | quad_trot | -0.00/0.03 -> 0.00/0.00 | 6.82/0.89 -> 0.00/0.00 | 1.16/0.25 -> 0.00/0.00 | True |  |
| minotaur | PASS | 2 | biped_walk | 0.00/0.00 -> 0.00/0.00 | 1.92/0.53 -> -0.00/0.00 | 0.00/0.00 -> 0.00/0.00 | True |  |
| octopus | PASS | 0 | None | 11.51/0.00 -> 0.00/0.00 | 19.51/0.00 -> 0.00/0.00 | 44.85/0.00 -> 0.00/0.00 | True | round 2 |
| ogre | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 2.20/0.44 -> 0.00/0.02 | -0.00/0.00 -> 0.00/0.00 | True |  |
| owl | PASS | 2 | biped_walk | 0.00/0.00 -> -0.00/0.00 | 4.65/0.92 -> -0.00/0.00 | 4.57/0.64 -> 0.01/0.11 | True | round 2 |
| penguin | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 2.31/0.13 -> 0.00/0.11 | -0.00/0.00 -> 0.00/0.00 | True |  |
| raven_wyvern | PASS | 2 | biped_walk | 0.00/0.00 -> -0.00/0.00 | 18.15/1.36 -> -0.00/0.00 | 2.10/0.00 -> 0.00/0.00 | True |  |
| rhino | PASS | 4 | quad_trot | 0.17/0.08 -> 0.00/0.03 | 3.65/1.47 -> 0.00/0.29 | 0.76/0.70 -> 0.00/0.26 | True |  |
| scorpion | PASS | 8 | None | 1.96/0.11 -> 0.00/0.05 | 0.23/0.22 -> 0.00/0.00 | 0.00/0.34 -> 0.00/0.00 | True |  |
| seahorse | PASS | 0 | None | 0.53/0.00 -> 0.00/0.00 | 1.24/0.00 -> 0.00/0.00 | 0.00/0.00 -> 0.00/0.00 | True |  |
| shark | PASS | 0 | None | 0.00/0.00 -> 0.00/0.00 | -0.00/0.00 -> -0.00/0.00 | 2.44/0.00 -> 0.00/0.00 | True |  |
| snake | PASS | 0 | None | 0.04/0.00 -> 0.00/0.00 | 1.84/0.00 -> 0.00/0.00 | 1.41/0.00 -> -0.00/0.00 | True |  |
| spider | PASS | 8 | None | 5.03/0.25 -> 0.01/0.09 | 0.34/0.46 -> 0.00/0.00 | 10.72/1.42 -> 0.01/0.11 | True |  |
| stag | PASS | 4 | quad_trot | 0.04/0.06 -> 0.01/0.00 | 1.78/1.87 -> 0.00/0.00 | 0.31/0.26 -> 0.00/0.00 | True | round 2 |
| tiger | PASS | 4 | quad_trot | 0.00/0.09 -> 0.00/0.00 | 8.30/1.15 -> 0.00/0.00 | 4.34/1.31 -> 0.00/0.02 | True | round 2 |
| troll | PASS | 2 | biped_walk | -0.00/0.00 -> 0.00/0.00 | 3.19/0.46 -> 0.00/0.29 | -0.00/0.00 -> 0.00/0.00 | True |  |
| turtle | PASS | 4 | quad_trot | 0.00/0.00 -> 0.00/0.00 | 3.25/0.45 -> 0.16/0.00 | 1.42/0.20 -> 0.00/0.20 | True | round 2 |
| werewolf | PASS | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 0.94/1.02 -> 0.00/0.00 | -0.00/0.00 -> -0.00/0.00 | True |  |
| yeti | PASS | 2 | biped_walk | -0.00/0.00 -> -0.00/0.00 | 3.46/0.39 -> 0.00/0.22 | -0.00/0.00 -> -0.00/0.00 | True |  |

Residual causes (honest): limb reach limit at full extension (tiger/owl/frog attack swipes, stag/knight move strides) -> IK clamps and the foot skims; octopus tentacles treated as feet (huge authored penetration, improved but far over gate); manta_ray wingtips detected as feet. Next: toe-roll / end-bone rotation when out of reach, per-creature foot exclusion list.


## Round 2 (11 fixed: tiger stag knight frog owl griffin turtle imp manta_ray octopus crab)
kit/clipkit.py: pelvis drop (<= 3 % H) for over-extended stance legs, held back if it drags a reaching swing foot; end-bone (toe) roll at full stretch (<= 35 deg, reverted if it digs in); final IK re-solve after the last root lift (was the main tiger/griffin miss); pass 2 turns plants the leg still cannot hold into a quick lifted step; swing frames lift >= 2.5 % H at once; move clips: 1-2 frame lift flickers closed, one plant per cycle; idle/attack plants no longer travel inside a window; `octo_tetrapod` gait (8 legs auto).
kit/clip_gate.py: splice / same_rest prefer the joint when a bone and a mesh share a name (octopus `body`: root anim was landing on the mesh node); per-creature `<c>/clips.json` passed as `--cfg`. run.py: clips read from current GLB if its rest differs from the backup.
clips.json: manta_ray, octopus `feet: []` (penetration + loop gates only; octopus attack now lifts the mantle instead of sinking tentacles); crab gait octo_tetrapod; frog `world_plants` (attack root sway is not root motion); turtle `aim_ik: [move]`.
Sheets of all 11 opened: poses/clip read kept, no frozen limbs. Note: earlier-passing creatures were not re-run on the new kit.
