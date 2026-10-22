# FROZEN yeti FACE checklist (face pass 2026-10-22). Do not edit questions during the run.
Referee: reference/sheet.png (front TR, side TL). Views: versions/TAG/fc/f_front, f_3q, f_side (head close-ups) and g_front,
g_3q, g_side (whole creature at 192 px). Every NO maps to its edit target (yeti.py); the critique IS that edit.
Champion loop: 2 variants per round, Opus pairwise vs champion in both orders, a variant must win both; regressions reverted.

| # | view | question (YES = good) | edit target if NO |
|---|---|---|---|
| Q1 | f_front | Brow ridge: a heavy shelf with two arches over the eyes (shadowed underside), not a straight bar? | stage2 F0 v0-v4 y/z, F1 v0-v3 |
| Q2 | f_side | Profile steps: brow > eye recess > nose > muzzle/lips > chin (>= 4 visible changes)? | stage2 J0-F0 v0 y |
| Q3 | f_3q | Eyes sunken under the brow, small round lens in a clean socket (not a slot)? | stage2 E0/F0 v1-v3, socket; stage3 lens |
| Q4 | f_front | A distinct broad flat nose with nostrils visible between the eyes and the mouth? | stage3 nose piece / stage2 N1-E0 v0-v1 |
| Q5 | f_3q, f_side | Muzzle mass: a rounded block stepping forward of the cheeks (not a flat box front)? | stage2 J0-N1 v1-v4 |
| Q6 | f_3q | Cheek planes: a plane turn from the face front to the face side under the eye (no 90 deg box wall)? | stage2 M0-E0 v3-v4 |
| Q7 | f_side, f_3q | Chin and jaw: a chin under the mouth, beard hanging from it (kept)? | stage2 J0/M0; stage3 beard tier |
| Q8 | f_front, f_3q | NOT a box/visor: the grey face area follows the forms (brow, cheeks, muzzle), no rectangular plate? | stage3 body_rule skin, PAL skin |
| Q9 | f_front, f_3q | The white fur hood frames the face on top and sides (the face sits inside the hood)? | stage1 lock (no edit) / stage3 hood tier; revert |
| Q10 | g_front, g_3q, g_side (192 px) | At game size it reads as an ape face (brow shadow, nose/muzzle) under a fur hood? | any of the above |
| Q11 | all | Kit gates + junction probe + detail gate + eye gate PASS, S1 lock, IoU vs S1 > 0.9? | revert the variant |

Score = YES count (Q11 NO = variant rejected).
