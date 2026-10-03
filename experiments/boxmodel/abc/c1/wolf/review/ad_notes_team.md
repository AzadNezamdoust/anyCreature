# wolf (abc/c1): art director notes, team round

Score: 6.5 / 10. Verdict: FIX.

Side view is a wolf at a glance and the colour map is the reference's. The front and the rear are not there yet: the forelegs are one tan column, the tail is a slab, the head is a small grey knob behind a cream wall. Tech gates all pass and the heatmap agrees with my eye (the purple on the bib clumps and the pink on the tail brush are posed only and not visible in the beauty views).

## Keep (must not regress)
- Side silhouette (az090): wedge head, pointed ears, ruff mass, deep chest, hock and stifle, low tail. Colour borders on clean edge paths: saddle, cream belly band, tan legs, cream chin, dark tail tip.
- The layered ruff and bib as the big secondary mass in hero/az090; inner-ear plates; nose pad.
- Paws with a leading middle toe and claws; rig and clips pass every gate (attack lunge reads in 4_posed f016).

## Must-fix (ordered by visual damage)

1. **STAGE-1 UNLOCK: forelegs fused into one tan column.** Stage 1.
   az000 and the front-limb close-up show one trouser block from the ruff to the paws with a shallow groove; the gap opens only at the feet (~15% of leg height). The reference front shows two separate columns from the chest floor down (gap from ~55% of shoulder height). Stage 2 cannot open a channel through a closed hull; the rear legs (az180) are the same.
   Fix: in the carve input, clear the zone between the forelegs in the front mask from the chest floor (z ~0.55, 50% of shoulder height) to the ground, gap ~0.17 m (35% of body width); same for the hind legs in the rear mask from the stifle (z ~0.45) down. Keep the leg columns at their current section. Re-lock, re-run stage 2-4 (IoU is measured against the new base).
   Check: 1_beauty az000 and 5_reference az000/az180: daylight between the legs from the chest floor; 2_closeups front limb: two columns.

2. **Tail is a slab hanging straight down off the rump.** Stage 2.
   back34 and 5_reference top/rear: the tail is wider than the hind leg and as deep as the thigh, fused into the hindquarters, carried vertical. The reference brush is a narrow ellipse that angles back off the rump and clears the hocks.
   Fix: narrow the tail verts in x by ~35% (from root to tip), thin the root front-to-back by ~25%, and swing the lower half back (+Y) by ~10% of body length (0.15-0.17 m) so the tip trails the hocks instead of hanging beside them. Keep the dark-tip border on its edge path. Top-view IoU stays well above 0.9 (the tail is <10% of the top area).
   Check: 1_beauty back34 and az090; 5_reference top and rear vs the reference.

3. **Eyes are pin-points and the face has no mouth.** Stage 3.
   az000 and the head close-up: the amber lens is a speck, the pupil is invisible at beauty size, and the socket normal tilts the eye at the ground. The reference has large amber almonds that look forward and a cream lip with a dark mouth line.
   Fix: lens +40% (to ~7 x 4 cm), pupil scaled with it, raise 15 mm proud, tilt the lens normal up ~10 deg and outward ~10 deg so both eyes read in az000; add a dark lip strip along the lip edge path (2-3 mm proud, nose to the corner of the mouth).
   Check: 2_closeups head colour (eye with pupil, mouth line), 1_beauty az000 (both eyes read at thumbnail size).

4. **Front view: a cream wall with a small head on top.** Stage 3.
   az000: the bib runs from the chin to the knees and the cheek tufts stack over the jaw; the head reads at ~60% of the reference's width relative to the ruff.
   Fix: bib clumps -30% and drop the lowest bib row so the bib ends at the elbow (z ~0.55), not the knee; cheek tufts from 2 to 1 per side, set behind the jaw line, not over it; keep the top ruff row as is.
   Check: 5_reference az000 vs reference front: head width to ruff width ratio close to the reference; 1_beauty hero: jaw line visible.

5. **Belly has no tuck-up.** Stage 2.
   az090: the belly line runs flat from the chest to the hind leg; the reference rises ~8% of body height behind the ribcage.
   Fix: raise the belly verts behind the ribcage (y from the elbow line back to the stifle) by 6-8% of body height (5-6 cm), keeping chest depth and the cream belly band border on its edge path.
   Check: 1_beauty az090 and 5_reference side: visible waist narrowing behind the ribs; stage-2 IoU side > 0.9.

## Should-fix
- Hind paws +20% (az090: smaller than the fore paws).
- Ears: tips 10% taller, the inner-ear plate a little bigger (reference ears are the tallest cue).
- Stage 4: bind the bib clumps with `body=` so they do not fold in the attack (purple in 3_tech az000); the claw z-fight (2, at the limit) lifted 2 mm.
- Hero: the ruff clumps over the shoulder are a scatter of same-size shards; vary clump sizes (one row of big, one of small).
