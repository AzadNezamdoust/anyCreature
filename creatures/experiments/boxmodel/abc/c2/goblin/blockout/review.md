# goblin blockout review

Verdict: **FIX**

Side view is the goblin of the sheet: hunch, forward-hung head, hook nose, long ear (side IoU 0.91, head / body height 0.363 vs 0.360). Head size and construction, neck, ear span, arm length and thickness are accepted, and so is the intended leg-length deviation (the loincloth is a stage-3 piece). The front, hero and back34 views lose the character: a constant-width box trunk with square shoulders on two parallel pillar legs and brick feet reads as a generic toy biped, not the concept's pot-bellied, sloped-shoulder, wide-planted crouching goblin. It is a designed cage (100 % quads, 2-3 loops per joint), not a scan. Range of motion: elbow, wrist and neck bend clean, 1.11 % fold-over; the leg is the weak spot (fix 3).

## Fixes (primary only, in priority order; % are of body height)

1. **Stance: parallel pillar legs under the hips** (stance). Where: az000, front silhouette diff (blue wedges outside both shins and feet, blue triangle at the crotch). Direction: open the legs into an A, knees turned out, feet planted wider than the hips and toed out. Amount: ankles outward 6-7 % each (ankle x 0.086 -> about 0.16), knees outward 3 %, toe-out about 20 degrees; hip sockets stay.

2. **Torso: box trunk and square shoulders, no belly mass** (mass). Where: az000, hero, back34; front diff shows red shoulder corners and blue at the neck-to-shoulder slope. Direction: slope the shoulders down from the neck (trapezius line), narrow the chest and sink it, push the belly ring forward and out so ribcage and pot belly are two masses with a pinch between them. Amount: shoulder corner down 4 % and in 3 %; chest ring back 2 %; belly ring forward 4 % and wider 3 % per side.

3. **Leg construction: no thigh / knee / shin read** (limbs). Where: az090, hero, and the fold and crouch poses of 5_rom, where the short straight leg collapses into the foot block and the fold-over sits. Direction: a clear Z in the side view with a thick thigh and a tapered shin: knee forward, ankle back. Amount: knee forward 3 %, shin girth at the ankle -20 % against the thigh; keep 2 knee loops but space them about 3 % apart so the 80 degree bend has material on the outside.

4. **Feet: short heel-heavy bricks** (limbs). Where: az090 and side diff (red behind the heel and under the sole, blue ahead of the toe), front diff (blue outside the feet). Direction: slide the foot forward under the shin and stretch it into a long low wedge that widens toward the toes, top plane sloping down from the ankle. Amount: heel forward 4 %, toe forward 5 %, toe width +30 % of the current foot width, foot height at the toe -40 %.

5. **Arms hang flat beside the body** (silhouette). Where: top silhouette (IoU 0.524, sheet hands sit ahead of the trunk, model hands beside it), az000 (forearm drops vertical from the elbow). Direction: elbows out and slightly back, forearms and hands forward and inward so the hands hang in front of the thighs, as in the concept's stalking pose. Amount: elbow out 3 %, wrist forward 5 % and in 2 %. Recheck the side IoU afterwards; it has 0.01 of margin over the floor.
