# Tortoise (r20) — round notes

Design: a stylised Galapagos-type tortoise — a tall domed shell (1.4x as long as wide) with an overhanging rim
and raised scute plates, a blunt beaked head on a short wrinkled neck, four elephant-column legs with toenails;
tan shell with ochre plates, grey-green skin, cream plastron. No reference sheet / blueprint in this batch.

## Stage 1
**r01** 428 tris, FAIL self-intersection at the fore legs (z 0.05). Critique: worst = the legs are crushed tents
(az000): the underside sits at z 0.10, so the first leg section is level with its root and folds through it.
Diagnosis: chain centre z 0.22, belly 0.10. Fix: whole chain up 8 cm (LIFT), legs as columns under the rim.
**r02** 428 tris, gates PASS. Critique: worst = stilts: the shell rides high on long legs that splay out (az000,
az090) - more a table than a tortoise. Diagnosis: LIFT 0.08, leg sections x 0.25-0.27. Fix: LIFT 0.05, legs 2 cm in.
**r03** 428 tris: legs read as short columns. Critique: worst = the shell is a flat-topped loaf (az090, az000);
the tortoise cue is a tall dome. Diagnosis: shell top half heights 0.19-0.34 on a 0.74 m wide shell. Fix: x1.22 (DOME).
**r04** 428 tris: dome reads. Critique: worst = the head is a thin tube level with the shell opening (hero, az090),
no character. Diagnosis: head rings 0-2 half width 0.05-0.09 at z 0.30. Fix: head ~20 % bigger and raised 6 cm on
an up-curving neck.
**r05** 428 tris: head reads as a blunt tortoise head on a rising neck. Locked (r06).

## Stage 2
Neck loop, knee / elbow loops, beak ridge dropped. **r07** IoU PASS.

## Stage 3 / 4
**r07** (stage 4): side + spine scute plates (hex knobs), toenails, kit eyes; shell / plates / skin / plastron /
nail, 5 colours, 1216 tris. FAIL: hit 2 (the eye pieces pass through the narrow head), slivers 3.0 % (36 on the
body: the mouth partial loop's fan ends on the thin beak). Fix (gate repair): mouth loop dropped, eyes r 0.018 with
no brow wedge.
**r08** hit fixed; slivers still 3.1 %. Located them on the GLB (min angle < 6 deg): the shell back -> tail ring
band (y 0.48-0.54) and the inner leg band under the knee loops (z 0.05-0.08). Fix: knee loops dropped, the tail root
ring scaled 1.8x in stage 2.
**r09** all gates PASS, 1200 tris. Critique: worst = the scutes read as small spikes (an ankylosaur, az090) and the
skin colour wraps the front of the shell; the beak cap is a big black disc. Fix (stage 3 only): plates 30 % wider and
flatter (taper 0.30), shell paint covers the front ring above the rim, beak cap only the upper tip.
**r10** final run with orbit + review.
**r10** PASS, 1200 tris. Critique: worst = skin colour on the front and back of the shell (az000, back34): the
bands between the neck / tail rings and the shell rings were painted skin. Fix: those annulus faces painted shell
away from the neck / tail axis.
**r11** final (orbit + review).

Final: all stage-4 gates PASS (incl. census, tech QA, glbcheck run). Remaining weakness: back of the shell still shows a skin wedge above the tail; scutes read as knobs rather than tiled plates.
