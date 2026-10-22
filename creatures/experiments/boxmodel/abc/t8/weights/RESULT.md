# t8 / weights - werewolf A/B (2026-10-22)

A = zoo/werewolf S4 (bone heat). B = copy rebuilt at S4 with `BMKIT_WEIGHTS=v2` (kit/weights.py: half-rotation
helper bones at shoulder/elbow/wrist/hip/knee/ankle, COPY_ROTATION 0.5 baked by the glTF export; elbow/knee falloff
centre +0.7r, width 1.4r; smoothing at mid/distal; 4-influence cap; mirror-exact). Mesh identical (max vertex diff
0.1 mm = rounding). Kit gates S4: OK (1 WARN 3 tris pose clip). ROM = kit/rom_probe.py, t8/joint_graph/joints_werewolf.json.

| metric | A | B |
|---|---|---|
| ROM poses pass / 42 | 30 | 29 |
| min volume kept | 0.489 (elbow) | 0.814 (elbow) |
| vol fails (<0.70) | 2 (elbow 0.49, knee 0.70) | 0 |
| elbow flex 110 vol/stretch/inv/ovl | 0.49/1.58/4/111 | 0.81/1.63/5/115 |
| knee flex 90 | 0.70/1.26/1/79 | 0.83/1.32/0/73 |
| hip flex 70 (crouch) | 0.90/1.71/5/0 | 0.94/1.80/0/0 |
| max stretch | 1.712 | 2.000 (thigh side+) |
| inverted sum (poses) | 12 (4) | 11 (5) |
| new overlap sum (poses) | 600 (11) | 575 (12) |
| bones | 24 | 38 (+14 helpers) |
| judge J1 (A left) | **A** (6 vs 5): knee slit / pit above knee on B | |
| judge J2 (B left) | **A** (6.5 vs 6): crouch thigh-belly pit on B | |

Verdict: **REJECT for the zoo** (judge prefers baseline in both orders, weakly; ROM pass count 30 -> 29 even though
volume fails 2 -> 0). Zoo step 4 NOT run. Kit default stays `heat`; v2 is opt-in (`skin(body, rig, weights='v2')` or
env BMKIT_WEIGHTS=v2). Ablations (cfg sweep, rom_try/): parametric falloff at roots/spine and L/R seam split both
worse (stretch 2.4-3.3); helpers alone fix volume (elbow 0.49 -> 0.67, knee 0.70 -> 0.82).
Remaining fails on both = geometric contact (neck flex, arm adduction, elbow/knee self-contact), not weights.

Files: ab_compare.jpg, ab_joints.jpg, posed_AB/BA.jpg, joints_AB/BA.jpg, rom_A/A.json, rom_B/B.json, rom_try/*.json.

## Repair round r2 (coordinator go, 2026-10-22)
r2 = helpers mid+distal only (no root helpers: thigh-belly pit), elbow/knee centre +0.4r, 3 smoothing iters.
ROM (harness reweight on A): 29/42, min vol 0.761, elbow 0.76, knee 0.80, inv 18 (6), overlap 573 (11).
Judge (fresh Opus, both orders): r2_posed_AB/r2_joints_AB -> A (6 vs 5: elbow notch, knee slit, crouch curl on B);
r2_posed_BA/r2_joints_BA -> A (6 vs 5). Baseline wins both orders again -> **REJECT, no zoo rollout**; zoo/rom_audit.md
is the bone-heat audit.
