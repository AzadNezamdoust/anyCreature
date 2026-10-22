# FROZEN gorilla HEAD checklist (head rebuild pass 2026-10-22, after the face pass r24e). Do not edit during the run.
Problem (orchestrator): at 192 px the face still reads as a dark rectangle set into the head; the mouth is a dark slot
(robotic); the nose piece is beak-like in profile. Goal: the face is part of the head LOFT (brow ring, muzzle rings,
mouth ring step, cheek ring vertices, jaw/chin), skin colour follows the new loops with soft borders.
Referee: reference/sheet.png (front TR, side TL). Views: versions/TAG/fc f_front, f_3q, f_side (head close-ups) and
g_front, g_3q, g_side (whole creature, 192 px native). Champion at start: r24e (face pass). Loop: WORKFLOW.md section 11.

| # | view | question (YES = good) | edit target if NO |
|---|---|---|---|
| Q1 | g_front, g_3q (192 px) | The face does NOT read as a dark rectangle / plate: its outline follows brow arches, cheeks and a rounded muzzle? | stage3 body_rule skin (ring, col) set + smooth_borders; S1 FACE muzzle j2-j4 |
| Q2 | f_side | The muzzle is a protruding rounded block under the brow (brow > eye recess > nose pad > upper lip > mouth step > chin > jaw: >= 5 visible steps)? | S1 FACE j0 y of H0..H4, Hm, He |
| Q3 | f_front | The muzzle is wider than tall and rounded in plan (its sides turn back, no flat front plate edge)? | S1 FACE H1/H2 j1-j4 |
| Q4 | f_front, f_3q | The mouth reads as a lip line (a thin ring step), NOT a dark slot or robot grille? | S1 FACE Hm j0-j3 (step depth, z gap to H1) |
| Q5 | f_side, f_3q | The nose is a broad flat pad flush on the muzzle top (nostrils readable), NOT a beak / wedge in profile? | stage3 nose_pad (lift, rows) |
| Q6 | f_front | The brow is a heavy overhang with two arches and a shadowed underside over the eyes (not one straight visor bar)? | S1 FACE He/H4 j0-j4 |
| Q7 | f_3q | Eyes: small round lenses in clean sockets under the brow, clearly visible (not slots, not big)? | S1 FACE H3/He j1-j3; stage2 socket; stage3 lens |
| Q8 | f_3q | Cheek planes: a plane turn between the eye socket and the muzzle, from the face front to the face side? | S1 FACE H2/H3 j3-j4 |
| Q9 | f_side, f_3q | Jaw and chin under the muzzle: a chin step, a jaw underside plane, a step chin -> throat? | S1 FACE H0 / H0u |
| Q10 | f_front, f_3q | The skin border is soft and follows the forms (no stair steps), blending into the fur edge? | stage3 body_rule + smooth_borders pairs |
| Q11 | g_3q, g_side | At game size it reads as a gorilla face (brow shadow band, muzzle forward); body, crest and silhouette unchanged? | any of the above; revert |
| Q12 | all | Kit gates + junction probe + detail gate + eye gate PASS, S1 lock (re-lock logged), IoU vs S1 > 0.9, tris in META range? | revert the variant |

Score = YES count (Q12 NO = variant rejected).
