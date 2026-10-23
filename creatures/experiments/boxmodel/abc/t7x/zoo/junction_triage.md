# Junction triage 2026-10-23 (owner rule: fix only flaws VISIBLE in zoomed crops or at 192 px game distance)

Source: each creature's latest champion S4 junction json + A/B/C beauty crops (native 480 px) + detail-gate 192 px thumbnails.
Fox uses s4_r11 (r12/r13 border pass reverted). Ogre skipped (owner-protected chin/eye).
Composite crops: scratchpad `tri/<creature>_<tag>.jpg`.

| creature | root | metric | VISIBLE/NOISE | why |
|---|---|---|---|---|
| tiger | thigh.L/R | knife 4 (1.98 r, 168 deg) | VISIBLE | crops A/B: thigh front is a flat skirt plate hanging over the belly, hard edge + dark slot behind it |
| tiger | ear.L/R | knife 3.2 r 119 deg, strip 2.41 r | NOISE | ear root reads clean in A/B/C; flags sit on the skull plane behind |
| tiger | upperarm.L/R | knife 1.32 r 156 deg, strip 1.16 r | NOISE | shoulder blends in A/B; flag only in the armpit (C) |
| dragon | upperarm.L/R | knife 2.84 r 145 deg, strip 2.55 r | VISIBLE | crop A: upper arm a tube butted on the chest, hard vertical crease/slot at the shoulder front |
| dragon | horn.L/R | knife 4.82 r 137 deg, strip 2.66 r | NOISE | horn rises from a boss on the skull; a plane step, no slit |
| dragon | thigh.L/R | knife 4.0 r 157 deg, strip 1.51 r | NOISE | rear thigh crease is under the wing; mild in A, hidden B/C and at 192 px |
| shark | fin.L/R (pectoral) | strip 2.6 r, 9.5 mm | VISIBLE | crops A/B: pec fin is a rectangular plank butted on the flank, dark groove along the root top |
| boar | tail0 | strip 1.85 r, 4.9 mm | VISIBLE | crops A/B/C: radial fan of needle triangles (pole) on the rump around the tail root, streak shading |
| boar | ear.L/R | knife 3.05 r 140 deg, strip 2.04 r | NOISE | ear plate sits clean on the skull in A/B/C |
| boar | upperarm.L/R | strip 1.04 r | NOISE | borderline number, nothing in the crops |
| raven_wyvern | upperarm.L/R | gap piece_wing 58-75 mm | VISIBLE | crop A: thin light slit (background line) along the wing leading edge beside the wrist claws |
| raven_wyvern | tail0 / piece_wing | gap/knife/slit 1.9% | NOISE | wing-on-body overlap; crops show seated feathers and spines |
| raven_wyvern | thigh.L/R | knife 2.74 r 132 deg | NOISE | under-belly only (C) |
| fox | thigh.L/R | knife 3.78 r 160 deg, strip 2.55 r | VISIBLE (deferred) | crop A: vertical crease where the thigh front wall meets the flank; owner pick pending to promote abc/t9/fox (junction 7/7 PASS), so not patched here |
| fox | ear / upperarm / tail0 | ear knife 1.69 r, strip 3.2 r, 1.06 r | NOISE | clean in the crops |
| rhino | ear.L/R | strip 1.54 r, 23.6 mm | NOISE | native crops: clean faceted ear root, no fold or slit |
| golem | shoulder.L/R | knife 5.15 r 118 deg | NOISE | rock-block design: shoulder block over chest reads intended in A/B/C and at 192 px |
| golem | thigh.L/R | strip 1.71 r | NOISE | groin flag only, crops clean |
| crocodile | upperarm / thigh | strip 1.6 r; knife 2.02 r 120 deg | NOISE | only a cream belly-colour wedge seen from below (C); invisible at 192 px |
| owl | tuft / thigh / wing | strip 1.53 r; talon "gaps" | NOISE | talons seated on toes; tuft roots clean |
| owl | tail0 | posed clip 7.67% vs wings (move@6) | NOISE | posed move f006 renders: same-colour wing tips over the tail, no visible poke |
| stag | thigh / upperarm / ear / tail0 | knife 3.29 r, strip 3.21 r, ear knife 3.71 r | NOISE | reads as low-poly muscle plane breaks; ears under antlers; nothing at 192 px |
| eagle | thigh.L/R | strip 1.02 r | NOISE | crops clean (borderline number; last fix attempt broke the knife rule) |
| koi | pec.L/R, tail1 | knife 2.22 r 119 deg, strip 1.45 r | NOISE | fin plates read clean; 1.4 mm tail strip invisible |
| spider | leg1a.L/R | strip 1.3 r | NOISE | crops clean |
| seahorse | fin_dorsal (residual) | probe PASS (strip 0.69 r) | NOISE | judge's "bright sliver" is one lit facet at the root end, not a gap; invisible at 192 px |

VISIBLE fix order (worst first): tiger thigh, dragon upperarm, shark pec fin, boar tail0 fan, raven_wyvern wing slit. Fox thigh waits for the owner's t9 pick.

## Outcomes (step 2)
| creature | fix | result |
|---|---|---|
| tiger | thigh: S1 re-lock, 3-span x 4-face flank window + 45 % transition ring, haunch stripes to the transition ring | ADOPT (A/B both orders); thigh knife 1.98 r/168 deg -> 0.47 r/100 deg |
| shark | pectoral root fillet (stage 2), 3 rounds | REVERT: S2 IoU az180 < 0.9 or new knife; the visible groove is the blade's own crease. Needs an S1 2-face root window (owner packet) |
| boar | rump ring in the tail-root span (2 variants) | REVERT: both flip (TIE) -> champion |
| raven_wyvern | wing-arm front section 22 mm in to the chest, claws follow | ADOPT (A/B both orders); slit gone |
| dragon | not attempted | fix = S1 fore window 2-3 spans + transition ring, +150-230 tris over the 6000 total cap (5980 now): owner pick (raise cap or trim details) |
| fox | not attempted | owner pick pending: promote abc/t9/fox (junction 7/7 PASS) |
