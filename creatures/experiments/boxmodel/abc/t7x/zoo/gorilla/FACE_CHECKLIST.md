# FROZEN gorilla FACE checklist (face pass 2026-10-22). Do not edit questions during the run.
Referee: reference/sheet.png (front TR, side TL). Views: versions/TAG/fc/f_front, f_3q, f_side (head close-ups) and g_front,
g_3q, g_side (whole creature at 192 px). Every NO maps to its edit target (gorilla.py); the critique IS that edit.
Champion loop: 2 variants per round, Opus pairwise vs champion in both orders, a variant must win both; regressions reverted.

| # | view | question (YES = good) | edit target if NO |
|---|---|---|---|
| Q1 | f_front | Brow ridge: a heavy shelf across both eyes (two arches, a shadowed underside), not a flat bar flush with the face? | stage2 H4 j0-j4 y/z, H5 j0-j3 |
| Q2 | f_side | Profile steps: brow > eye recess > nose > lips > chin (>= 4 visible changes)? | stage2 H0-H4 j0 y |
| Q3 | f_3q | Eyes sunken under the brow (brow and cheek forward of the lens), lens small, round, in a clean socket? | stage2 H3/H4 j1-j3, socket depth; stage3 lens offset |
| Q4 | f_front | A distinct nose: a broad pad between the eyes and the mouth, wider at the bottom, nostrils visible? | stage3 nose piece / stage2 H2-H3 j0-j1 |
| Q5 | f_3q, f_side | Muzzle/lip mass: a block stepping forward of the cheeks, its sides read as planes (not one centre ridge)? | stage2 H0-H2 j2-j3 |
| Q6 | f_3q | Cheek planes: a plane turn under the eye from the face front to the face side? | stage2 H2/H3 j2-j4 |
| Q7 | f_side, f_3q | Jaw and chin: chin step under the lower lip, jaw underside plane, step chin -> throat? | stage2 H0/H0u |
| Q8 | f_front, f_3q | NOT a visor: the skin outline follows the forms (brow top, cheeks, muzzle), eyes inside the face under the brow, no rectangular plate? | stage3 body_rule skin rows/cols, PAL skin |
| Q9 | f_front, f_side | Sagittal crest still a readable peak (B r18b)? | never regress: revert |
| Q10 | g_3q, g_side, g_front (192 px) | At game size the face reads as an ape face (brow shadow band, muzzle forward)? | any of the above |
| Q11 | all | Kit gates + junction probe + detail gate + eye gate PASS, S1 lock, IoU vs S1 > 0.9? | revert the variant |

Score = YES count (Q11 NO = variant rejected).
