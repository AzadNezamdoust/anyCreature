# Creature-method lab — results log

LLM (Opus) builds 10 animals per method from memory, no references, isolated
folder. Sheets rendered by `render.py`, shuffled by `blind.py`, judged blind by
Opus and Fable: open-answer animal ID + quality 1-10 vs AAA creature form.

Animals: wolf, horse, elephant, giraffe, crocodile, eagle, shark, frog, tortoise, kangaroo.

## Round 1 — five methods (2026-10-12)

| method | recognised O / F | quality O / F |
|---|---|---|
| SDF + smooth-min, marching cubes | 9 / 9 | **3.6 / 4.9** |
| engine skeleton spec (anyCreature) | **10 / 10** | 2.7 / 3.9 |
| mesh-as-text (raw OBJ numbers) | 9 / 8 | 2.9 / 4.5 |
| Fourier tubes (`fourier3d.py`) | 9 / 9 | 2.7 / 3.9 |
| primitive code (ellipsoids/capsules) | 8 / 8 | 2.0 / 2.8 |

(Round-1 sheets used a flat-shaded painter renderer; "surface noise" notes on SDF
were partly renderer artifacts. GPU renderer from round 2 on.)

## Round 2 — the two leaders, with judge notes + anatomy brief

| method | recognised O / F | quality O / F |
|---|---|---|
| **SDF v2** (bone landmarks, muscle masses, carved heads, flat fins) | 10 / 10 | **5.9 / 5.9** |
| SDF v1 (baseline, same renderer) | 10 / 10 | 4.2 / 4.2 |
| engine spec v2 | 9 / 10 | 3.0 / 3.0 |
| engine spec v1 | 10 / 10 | 2.1 / 2.7 |

Best single models (7/10): SDF v2 frog, eagle, horse, tortoise, elephant.
Recurring defects on SDF v2: tube limbs / balloon joints, blobby bodies,
detached flat ears, soft heads and hooves, tube tails.

Takeaway so far: implicit SDF with smooth blending is the only method that
climbs with iteration; the engine's ring-section spec plateaus at ~3.

## Round 3 — SDF v3, self-critique only

| | recognised O / F | quality O / F |
|---|---|---|
| SDF v3 | 9 / 10 | 4.8 / 5.2 |
| SDF v2 (same session baseline) | 10 / 10 | 4.6 / 5.1 |

Plateau: one artist critiquing itself stops improving around 5/10. Same defects
persist (tube limbs, lumpy muscles, crude heads/feet). Judges' absolute scale
drifts between sessions — compare only within a round.

Next: reusable SDF anatomy kit (parts built once and iterated), animals as
parameters on it, and an independent Fable critic per animal.

## Round 4a — SDF anatomy kit v3 (horse, wolf) vs freehand SDF v3

| model | Opus | Fable |
|---|---|---|
| kit3 horse | 4 | 5 |
| r3 horse | 4 | 6 |
| kit3 wolf | 3 | 4 |
| r3 wolf | 4 | 5 |

Kit removed artifacts but did not raise scores. Defects shifted to PROPORTION:
barrel/sagging belly, stick legs, hollow back, hind leg too straight/small.
Next: proportion canon (measurements from memory, written by a separate lane)
+ numeric landmark check before any visual judging.
