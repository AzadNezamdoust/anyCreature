# Octopus (r20) — round notes

Design: a friendly stylised reef octopus sitting on the ground — a big round head with two large eyes and a heavy
brow, a tall bulbous mantle tilted back, eight thick arms (four a side) fanned out on the ground with tips that
curl up; coral red with darker spots, cream suckers on the arm undersides. No reference sheet / blueprint.

## Stage 1
**r01** 484 tris, gates PASS. Critique: worst = the face is a narrow snout poking forward from a thin sock-like
mantle (az090, hero); an octopus is a big round bulb. Diagnosis: CH rings 0-1 at y -0.24 / -0.20 with half widths
0.08 / 0.165; mantle half widths 0.25-0.27. Fix: front rings pulled back and widened, mantle 10-15 % fuller.
**r02** 484 tris: mantle fuller, but the face still ends in a nub (az045, top): the chain's first ring is small,
so the front tapers to a point. Fix: rings 0-1 as big as the head (a blunt flat face plane for the eyes).
**r03** 484 tris: blunt face plane. Critique: worst = the arms are eight thin straight spikes (top view reads a
starfish / sun). Diagnosis: ARM_W 0.027-0.062, sections on straight rays. Fix: arms ~40 % thicker and each sweeps
sideways along its length, alternating (ARM_BEND), so they read as soft curling arms.
**r04** FAIL self-intersection (26 pairs): alternating sweeps drove arms 2 and 3 into each other. Fix: all arms sweep the same way (pinwheel), bend 1.2.
**r05** FAIL: 2 pairs where the back arm's thick root section touches the mantle (0.22, 0.21, 0.19). Fix: root section 0.075 and 3 cm further out.
**r06** FAIL 2 pairs: the back arm's first band (root on rings 4-5, already rising into the mantle) cuts the mantle's lower back. Fix: all arm roots one ring forward (rings 0-3), under the head.
**r07** 484 tris, gates PASS: bulb head + tall tilted mantle + eight curving arms read as an octopus from every view. Locked (r08).

## Stage 2
Three loops per arm (curl), head/mantle junction loop, mantle mid loop, brow pushed out. IoU PASS (in r09).

## Stage 3 / 4
**r09** 1630 tris, all gates PASS: toon kit eyes (parts.eye_set style='toon'), mantle warts, suckers; coral /
spot / cream / white / black, 5 colours. Rig 27 bones; idle + move = travelling arm ripple with mantle sway and
bob, attack = front arms rear up and lash. Clip warnings (pink) on the front arms in poses: warning only.
Critique: worst = the eyes are small for the character (az000). Fix: eye radius 0.055 -> 0.072.
**r10** final (orbit + review).

Final: all stage-4 gates PASS. Remaining weakness: the face is a flat-fronted cylinder (pug read), suckers barely visible.
