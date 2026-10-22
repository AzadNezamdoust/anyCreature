# t8 / joint_graph — werewolf A/B (2026-10-22)

Technique: joints declared in JOINTS (type, axis, ROM, pivot station) in werewolf/werewolf.py; stage-2 loops generated
from it (hinge = pivot ring + 1 loop each side: elbow, wrist, knee, hock; twist = 5 loops: shoulder, hip, neck; waist
ball loop). Replaces baseline's 6 hand-placed single loops. Stage 1 lock unchanged (reused). Skeleton = same J dict
(already joint-derived); skin = kit bone heat, unchanged.
New gate: rom_sweep.py + joints_werewolf.json (42 single-joint limit poses, .L + spine/neck/tail; volume kept in a
1.3r ball around pivot by ray parity >= 0.70, edge stretch <= 2.0, flipped tris vs dominant bone rotation = 0,
new BVH self-overlap pairs vs rest = 0) + 4 combined extreme-pose renders.

| metric | A baseline zoo/werewolf | B joint_graph |
|---|---|---|
| kit gates s1-s4 | PASS | PASS (1 WARN: 3 tris 0.02% pose clip) |
| body tris (GLB) / total | 3476 / 3896 | 3948 / 4368 |
| ROM poses pass (of 42) | 30 | 32 |
| min joint volume kept | 0.489 (elbow flex 110) | 0.513 (elbow flex 110) |
| fail vol (<0.70) | 2 (elbow, shin 0.698) | 2 (elbow, shin 0.693) |
| max stretch | 1.712 | 1.710 |
| inverted tris (sum) / poses failing | 12 / 4 | 21 / 4 (knee flex 1 -> 10) |
| new self-overlap pairs (sum) / poses failing | 600 / 11 | 625 / 9 (neck fixed: 38->22, twist 2->0) |
| judge J1 (A,B order) | TIE | |
| judge J2 (B,A order) | TIE | |
| own read | identical silhouettes in all 4 extreme poses | same; no visible joint improvement |
| cost | sweep 4 runs x ~20 s | 1 build round (2.5 min), ~25 turns total |

Not done: orbit18/192px sheets (rest pose geometry is the same as A; posed frames were the deciding comparison).

Common defects both (judge): elbow collapse at 110 flex, crouch thigh pinch into belly, raised-thigh knife fold at
groin, deltoid seam on arm raise, thin wrists. Root cause = bone-heat weights, not loop count.

Verdict: **REJECT** (keep the ROM sweep gate) — extra joint loops do not change deformation (judge tie both orders,
ROM numbers within noise, +472 tris, more knee inversions); weights dominate. The rom_sweep.py gate itself is useful
and exposes real baseline failures (elbow vol 0.49, shin 0.70, adduction/neck overlaps).

Files: ab_compare.jpg, posed_A.jpg, posed_B.jpg, baseline_rom/rom.json, candidate_rom/rom.json, rom_sweep.py.
