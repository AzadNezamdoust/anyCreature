# Crocodile sheet_1.png — measured once (PIL, 1536x1024)

Segmentation: fg = (max-min > 25) | (max < 150) on white bg. L = side-view length.

## Side view (top-left, faces left) bbox x31-1042, y164-394 -> L = 1011 px, H = 230 px (0.23 L incl. scute bumps)
Fractions are of L from snout tip (0) to tail tip (1). Ground y = 394.

| zone | x frac | measure |
|---|---|---|
| snout tip | 0.00 | snout height 0.05-0.06 L (y 202-261 at 0.025-0.075) |
| snout -> head | 0.00-0.22 | head length 0.22 L; head depth 0.09 L at 0.15, 0.13 L at 0.20 (jaw cheek) |
| eye | 0.174-0.188 (centre 0.181), y 181-195 | eye dia 14 px = 0.014 L = 6.3 % of head length; sits on top bump (dorsal peak at 0.188, y164) |
| neck | 0.22-0.26 | top dip y175 at 0.225 |
| trunk | 0.24-0.63 | top y 175-190 (0.35-0.5), belly bottom y 360 -> trunk depth 0.18 L, belly clearance 0.034 L |
| front leg | 0.21-0.35 | foot on ground y385-394; leg + foot length 0.14 L, leg height ~0.09 L |
| rear leg | 0.50-0.63 | same; thigh larger |
| tail | 0.63-1.00 | 0.37 L; height 0.12 L at 0.65, 0.08 at 0.80, 0.05 at 0.90, 0.006 at tip; top line drops y226->331 |
| dorsal top | | y166 at 0.25, 180 at 0.42, 195 at 0.53, 225 at 0.63, 264 at 0.74, 311 at 0.94 |

Dorsal scute bumps (side profile local maxima): 17 bumps from 0.24 to 0.96, spacing 0.04-0.06 L, bump height ~0.012-0.02 L, shrinking tailward.

## Top view (bottom-right, snout left) bbox x660-1503 -> length 843 px
Widths (fraction of top length): snout 0.07-0.08 (0.05-0.10), head 0.10-0.15 (0.15-0.20), neck 0.165 (0.25), shoulders 0.19 (0.30), trunk 0.21 (0.50-0.55), hips 0.19 (0.60), tail 0.10 (0.75), 0.07 (0.85), 0.03 (0.95).
Leg span (feet splayed): front 0.37 at 0.40, rear 0.35 at 0.65. Eyes at 0.185-0.205, wide-set on top of head (y spread 84 px = 0.10).
Dorsal scutes, top: one central row of ~14 fat rounded oval scutes, largest ~0.055 L long x 0.04 L wide over the trunk, shrinking to ~0.02 L at the tail tip.

## Front view (top-right) bbox w 385 h 233 (same scale as side)
Head width 0.11-0.16 of side L; body width 0.30 L (cheeks/flank bulge), feet span 0.38 L. Splayed sprawl stance, elbows out.

## Feet
4 thick toes with dark rounded claws per foot (3-4 visible), claw length ~0.012 L; toes fan forward-outward.

## Teeth
5-6 visible per side, small conical, cream; we make 3-4 bigger blunt ones per side (lesson).

## Colour zones (sampled RGB)
| zone | hex |
|---|---|
| dorsal olive (back, head top, tail top, scutes) | #736d50 |
| snout top | #797051 |
| leg lit olive | #92845b |
| belly / flank lower sand | #dcc083 |
| jaw / throat cream | #fae8bd |
| eye iris amber | #cc9223 |
| pupil / claws dark | ~#2e2a26 |
Split line: olive above, sand below at ~55 % of trunk depth; jaw underside cream.
