# FROZEN gorilla checklist (B arm). Do not edit questions during the run. Answer each YES/NO per variant, citing the image.
Referee: reference/sheet.png (side TL, front TR, rear BL, top BR). Views = stage4 renders / orbit18 / junction crops.
Every NO must map to the named edit target (file gorilla.py) - the critique IS that edit.

| # | view | question (YES = good) | edit target if NO |
|---|---|---|---|
| Q1 | az000 front | Does the face show a muzzle that juts forward of the eye plane (nose/lip planes), not one flat plate? | stage2: H0/H1/H2 j0-j2 y moves; H3 j0-j1 nose bridge |
| Q2 | az090 side | Does the muzzle profile step: brow > eye recess > nose > lip > chin (>=3 visible steps)? | stage2: H0-H4 j0-j2 y; brow H4 move |
| Q3 | hero/az045 | Does the head read as a skull with a brow ridge + cheek turn, not a helmet/bucket with a visor? | stage2: H3/H4 j3-j5 (cheek/temple) x,y; brow ridge vector |
| Q4 | az090 side | Is the sagittal crest a readable peak (ridge), not a smooth dome? | stage2: last head rings dorsal j11-j13 z/y |
| Q5 | az000/hero | Is the eye a small round lens in a socket under the brow, visible (eye gate PASS)? | stage2 socket depth / S3 lens(); do not regress |
| Q6 | az090 side | Is the saddle a soft-edged patch on the LOWER back + rump, NOT a rectangular blanket hanging down the flanks? | stage3 body_rule / SADDLE_BACK / HAUNCH_SIDE, j thresholds |
| Q7 | az180 rear | Does the saddle narrow upward toward the shoulders (V/taper like sheet rear), with dark fur on the shoulders? | stage3 body_rule per-ring j limit |
| Q8 | top | Top view: saddle starts behind the shoulder mass and covers the rump; border follows the form, no stair-steps? | stage3 body_rule + smooth_borders k |
| Q9 | az090 side | Does the forearm swell (thicker below the elbow than above the wrist), not a straight tube? | ARM_R forearm rings (rx, ry) / stage2 ring scale |
| Q10 | az000 front | Do arms show an elbow knob / shape change, upper arm bulging at the deltoid then tapering? | ARM_R upper rings, stage2 elbow loop verts |
| Q11 | az090 side | Do arms read massive and long like the sheet (forearm width >= ~0.8 of upper arm)? | ARM_R |
| Q12 | hero/az000 | Are knuckle hands chunky readable pads with fat fingers at 192px? | HAND_DIGITS / digits() |
| Q13 | hero + junction crops | Shoulder join: deltoid over ribcage, no slit/knife fold/seam strip (junction PASS)? | stage2 C2/T1 moves; never regress |
| Q14 | junction crops | Thigh/groin join: no slit, knife or pinch (junction PASS)? | stage2 knee/groin moves |
| Q15 | az090 side | Silhouette still matches sheet side (torso slopes up rump->shoulders, head low/forward)? | do not move S1 lock; revert edit |
| Q16 | all | All kit gates + junction + detail gate PASS, tris in META range? | revert the variant |

Score = number of YES (Q16 NO = variant rejected regardless).
