# FROZEN yeti HEAD checklist (head rebuild pass 2026-10-22, after the face pass r31g). Do not edit during the run.
Problem (orchestrator): at 192 px the face still reads as a grey rectangle set into the head; the mouth is a dark slot
(robotic); the nose piece is beak-like in profile; grey jaw wings flare past the hood. Goal: the face is part of the
head LOFT (brow ring, muzzle rings, mouth ring step, cheek ring vertices, jaw/chin) sitting under the fur hood; the grey
skin follows the new loops with soft borders, no jaw wings.
Referee: reference/sheet.png (front TR, side TL). Views: versions/TAG/fc f_front, f_3q, f_side (head close-ups) and
g_front, g_3q, g_side (whole creature, 192 px native). Champion at start: r31g (face pass). Loop: WORKFLOW.md section 11.

| # | view | question (YES = good) | edit target if NO |
|---|---|---|---|
| Q1 | g_front, g_3q (192 px) | The face does NOT read as a grey rectangle / box: its outline follows brow arches, cheeks and a rounded muzzle? | stage3 body_rule skin (ring, vertex) set + smooth_borders; S1 FACE muzzle v2-v4 |
| Q2 | f_front, f_3q | No grey jaw wings: nothing grey flares out past the hood at the jaw; the muzzle sits under / inside the hood? | S1 FACE J0/M0 v3-v5; stage3 body_rule |
| Q3 | f_side | Profile steps: brow > eye recess > nose pad > upper lip > mouth step > chin (>= 5 visible steps), the muzzle a rounded block? | S1 FACE v0 y of J0..F0 rings |
| Q4 | f_front | The muzzle is wider than tall and rounded in plan (its sides turn back, no flat box front)? | S1 FACE M0/N0/N1 v1-v4 |
| Q5 | f_front, f_3q | The mouth reads as a lip line (a thin ring step), NOT a dark slot? | S1 FACE Mm v0-v3 |
| Q6 | f_side, f_3q | The nose is a broad flat pad flush on the muzzle top (nostrils readable), NOT a beak in profile? | stage3 nose_pad |
| Q7 | f_front | Brow: a heavy overhang with two arches and a shadowed underside over the eyes (not a straight bar)? | S1 FACE Eu/F0 v0-v4 |
| Q8 | f_3q | Eyes: small round lenses in clean sockets under the brow, clearly visible? | S1 FACE E0/Eu v1-v3; stage2 socket; stage3 lens |
| Q9 | f_3q | Cheek planes: a plane turn between the eye and the muzzle from the face front to the side (no 90 deg box wall)? | S1 FACE N1/E0 v3-v4 |
| Q10 | f_front, f_3q | The grey border is soft and follows the forms, blending into the white fur edge (hood frames the face on top and sides)? | stage3 body_rule + smooth_borders; hood tier |
| Q11 | g_front, g_3q, g_side | At game size it reads as an ape face under a fur hood (brow shadow, nose/muzzle); body and fur unchanged? | any of the above; revert |
| Q12 | all | Kit gates + junction probe + detail gate + eye gate PASS, S1 lock (re-lock logged), IoU vs S1 > 0.9, tris in META range? | revert the variant |

Score = YES count (Q12 NO = variant rejected).
