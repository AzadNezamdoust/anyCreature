# Wyrm (r20, opus)
Design: a legless crimson serpent-dragon, neck reared like a cobra, body thrown into humps over the ground.
Identity cues: big dragon head with swept-back ivory horns, orange dorsal fin blades, tail blade, fangs, gold belly.

## Stage 1 (4 render rounds)
- r01 PASS 620. Critique: reads as a worm (thin, tiny head). Fix: THICK head 1.55 / body 1.45.
- r02 FAIL self-intersection at the hump underside, then body below ground. Fix: path raised, hump belly depth reduced. PASS.
- r03 Critique: snake head. Fix: head 1.85, snout 9 cm longer. r04 lock (edge 4a8165b0).
## Stage 2 (1): mouth loop, neck bend loop, brow, open jaw.
## Stage 3 (1): 7 colours, horns, 5 fins, tail blade, eyes, fangs. 1308 tris.
## Stage 4 (3): r01 FAIL floating fangs (head moved). Fix: fangs placed by ray on the jaw. r02 PASS; horns/fins too small -> r03 horns 0.42 m, fins x1.6, final PASS.
Weakness: the S lies in y-z (mirror), so it never coils sideways; humps shallow.
