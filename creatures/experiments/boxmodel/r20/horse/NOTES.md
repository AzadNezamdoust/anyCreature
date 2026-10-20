# Horse (r20) — round notes

Design: a stocky stylised bay horse — deep barrel, arched crested neck, long wedge head hung at ~55 deg, short
alert ears; black mane, forelock, full tail and black lower legs ("points"), pale muzzle, white blaze.
Identity cues in the base: long head on a long arched neck, tall slim legs ending in a flat hoof block.
No reference sheet / blueprint (no downloads or generation allowed in this batch): built from J and PARAMS.

## Stage 1
**r01** first build: 752 tris. Critique: self-intersection where the neck enters the chest (y -0.45, z 1.29),
neck a thin giraffe tube (az045). Diagnosis: NECK[3] ring at y -0.50 tilted into BODY[0]. Fix: neck rings 20-30 %
wider/deeper, last ring moved back to y -0.565 and turned flatter.
**r02** gates PASS, 752 tris. Critique: worst = ears are 0.20 m spikes (mule/donkey read, az090, hero).
Diagnosis: EAR_TIP (0.085, -0.86, 1.80). Fix: tip lower and forward-tilted.
**r03** 752 tris, ears read as horse now. Critique: worst = stilt legs, forearm and gaskin as thin as the cannon
(az090, az135). Diagnosis: FORE[1..4] / HIND[2..4] half widths 0.04-0.07. Fix: forearm / gaskin / hock / cannon
sections 12-25 % bigger (muscle above the knee and hock, cannon stays the narrowest).
**r04** 752 tris: legs now taper muscle -> cannon. Critique: worst = a flat plank topline (az090): no withers,
no dip behind them, no rounded croup. Diagnosis: BODY top half-heights flat 0.25-0.31. Fix: withers rings
0.34-0.35, back 0.265, croup 0.285 / 0.27, rump rounded (bottom 0.20).
**r05** 752 tris: withers, back dip and croup read in az090. Critique: worst = from the front (az000) the chest and
the leg stance are narrow (a deer's). Fix: barrel rings 10 % wider (BODY_SX) and the legs 2 cm out (LEG_DX).
**r06** 752 tris: stance and chest read from az000; the base reads as a horse from every view. Locked (r07).

## Stage 2
**r08** joint loops (elbow, knee x2, fetlocks, stifle, hock x2, throatlatch, neck base), nostril flare, jaw plate. 976 tris, IoU min 0.997, gates PASS.

## Stage 3 / 4
**r09** (stage 4, includes stage 3): mane blade, forelock, tail, kit eyes (parts.eye_set, brow wedge off); bay coat,
black points, blaze, pale muzzle; 6 colours, 1236 tris. Rig 22 bones, idle / trot / rear-and-strike. Every gate PASS.
Critique: eyes small, mane a thin blade (no hair clumps); accepted within budget.
**r10** final stage-4 run with orbit + glbcheck, then --review (beauty sheet review/1_beauty.jpg).

Final: all stage-4 gates PASS. Remaining weakness: long thin neck and a blade mane; small eyes.
