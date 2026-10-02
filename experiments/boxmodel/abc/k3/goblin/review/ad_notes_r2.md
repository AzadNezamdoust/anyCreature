# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (minimum is 0.916, top view: the ears own it, do not move them); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Hooked nose that drops below the mouth line (r11, r15); brow over two big forward yellow eyes (r12-r13).
- Wide fanged grin reads at az000 (r14).
- Pot belly over the belt in az090 (r24-r25).
- Clean tech: slivers 0, clip 0, drift 0, 3_tech clean grey (r19-r29).
- Long horizontal ears, big domed head, crouch: matches 5_reference front and rear.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit; clip_area_pct 0.0, stretch 0. Nothing to do; keep it that way.

1. **The mouth is a big flat dark box with fangs on its rim (F major).**
   - Where: 1_beauty hero and az090: the open mouth is a large flat dark-brown plane, deep in az090 like a slot cut into the head, with the fangs standing on its edge. 5_reference side and front: a grin with lips, a row of teeth seated in the gum, and only a thin dark gap.
   - Fix: Stage 2 (vertex moves): raise the lower-lip verts (the R7 grin-loop row at P0-P2) by about 25% of the current mouth height so the dark opening narrows to about half; keep R7 P3 where r29 put it (the sliver fix). Stage 3: add a row of 4-6 small upper teeth per side between the fangs (cream, 4-sided wedges, about 1/3 of the fang length, rooted 40% into the upper-lip edge), and 2-3 small lower teeth; keep the four fangs. Paint the upper lip quad (R8-R9 P1-P2) back to green so the lip reads as a lip, with dark only inside the mouth.
   - Check: 1_beauty az000 and hero: a toothy grin with green lips, not a dark box; az090: no deep dark slot; slivers 0, hit/float 0, IoU > 0.9.

2. **Loincloth is two flat boards hanging off the belt (O major, F major).**
   - Where: 1_beauty az090: a front and a back plate hanging straight down, standing off the hips edge-on; back34: a flat plate. 5_reference side and rear: a tattered skirt that wraps the hips all round under the belt.
   - Fix: Stage 3: add a side panel on each hip (plate3, same 0.012-0.021 thickness, tattered hem 2-3 points) that joins the front and back flaps under the belt, so the cloth wraps the hips; angle front and back flaps 8-10 deg outward at the hem so they follow the thigh, not a straight drop. Bind with `body=` and apply `even_through()` as in r22 so the cloth does not fold.
   - Check: 1_beauty az090 and back34: the cloth wraps the hips with visible thickness, no edge-on board; fold-overs <= 0.5%; drift 0; clip 0.

3. **Hands are pointed mitts with three tiny claw cones (F major).**
   - Where: 2_closeups front limb and fingers colour: each hand is a narrow pointed shape with three thin finger sticks and small claws; 1_beauty az000: the hands read as spikes. Brief: clawed three-fingered hands. 5_reference front: three long, knuckled fingers with cream claws, slightly curled.
   - Fix: Stage 3: rebuild the three finger pieces per hand 1.5x thicker (about 25% of the hand width each), two segments with a 20 deg curl at the middle knuckle, splayed 12 deg apart; claws 1.3x longer and rooted 30% into the finger tips. Stage 2: widen the hand's last ring by about 20% so the fingers root on a palm, not a point. Bind fingers to the hand bone.
   - Check: 2_closeups front limb colour: three separate curled fingers with claws; 1_beauty az000: hands read as claws at thumbnail size; hit/float 0; drift 0.

4. **Unrequested horn nub on the crown (O minor).**
   - Where: 2_closeups head colour and wire: a small spike on top of the skull; 4_posed attack_f012: the same nub stands up from the crown.
   - Fix: Stage 2 (vertex move): pull the crown pole vert (or the seam vert that forms the nub) down to the level of its ring neighbours plus about 1% of head height, so the dome is smooth. If it is a piece, delete it in stage 3.
   - Check: 2_closeups head colour: a smooth dome; IoU > 0.9 (the nub is tiny).

## Should-fix

- Paint the belly front faces (R3-R4 front) a lighter green as in 5_reference front, if not already the case (az000 shows a light chest panel; extend it down to the belt).

## Dropped

- O "a thin stray line runs from the ear tip back across the head (needle sliver)" in 4_posed idle_f012: the packet was rendered 2026-09-28, before the kit's wire overlay lost its even offset (2026-09-29); the colour views show nothing there, and stretch is 0. Re-check in the new packet; if it is still there, it is a stray ear weight and becomes should-fix.
- O "limbs are thin constant tubes": the brief asks for thin limbs, and 5_reference shows thin limbs with knobby joints; not worth the IoU budget this round.
- Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 1_beauty hero/az000: the open mouth is a large flat black cavity with fangs sitting on its rim; it needs a lip edge or teeth seated in the jaw.
  - 2_closeups front limb colour / fingers: hands are pointed mitts with three tiny claw cones; no separate fingers.
  - 1_beauty az090: loincloth is a thin flat plate hanging in front of the belt with no thickness.

### Opus 5.5: FIX 6
- top_issues:
  - 1_beauty az090/back34: loincloth front and back flaps are paper-thin plates edge-on
  - 4_posed idle_f012: a thin stray line runs from the ear tip back across the head (needle sliver)
  - 1_beauty hero/2_closeups head: small unrequested horn nub on the crown; limbs are thin constant tubes

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_area_pct 0.0, stretch 0
