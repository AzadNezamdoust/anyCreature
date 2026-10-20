# Zoo review, round 2 (Fable seat, blind)

Judged from `stage4/s4_hero_colour.png`, `orbit18_sheet.jpg`, `side_by_side.jpg` and `reference/sheet.png` only; `before/` and `review_*.md` not read.
Rubric: t7 hand box model (crisp flat planes, flat colour), simple face (small round lens eye, no masks or liners), shape before colour, species read from every angle.
Fixes name the table or function in `<creature>/<creature>.py` and the direction of the edit; numbers are starting points, re-lock stage 1 after a loft edit.

## Scores

| creature | score | one-line read |
|---|---|---|
| stag | 8 | best of the set; reads from every angle, antlers and rump patch sell it |
| dragon | 7.5 | good silhouette; head small, wings too far back |
| spider | 7.5 | reads instantly; legs too straight, abdomen a bit flat |
| raven_wyvern | 7.5 | clean raven; tail over-long, head narrow |
| owl | 7.5 | reads well; body loafs backward, tail too long |
| fox | 7 | good; tail hangs straight down, muzzle short |
| bear | 7 | reads; no shoulder hump, head and neck under-scaled |
| golem | 7 | close to sheet; head perched, arms thin vs sheet |
| octopus | 7 | reads; arms are straight sticks, mantle tipped back |
| chameleon | 6.5 | reads; legs straight stilts, head too long |
| koi | 6.5 | reads as fish; body too deep and short, patches read as stripes |
| knight | 6.5 | reads; shield painted flat on the cape, sword a stick |
| boar | 6.5 | reads; tusks tiny, head small, rear thin |
| crocodile | 6 | reads from top; snout too short, body a flat slab |
| shark | 6 | reads from side; pectorals hang down like legs |
| tiger | 6 | reads; face is a white mask/ruff (owner rule), shoulders over-high |
| ogre | 6 | reads as humanoid brute; belly weak, arms thin tubes |
| goblin | 6 | reads; nose block reads as a trunk from the side |
| crab | 6 | reads; claws held up like boxing gloves, carapace too tall |
| snake | 5 | reads from top only; from the side the body is a flat ribbon, head a box |

Broken outright: none (all 20 load, render, mirror, and stand on the ground plane). Packaging flags below.

## Packaging flags (not model defects)

- `shark/side_by_side.jpg`, `chameleon/side_by_side.jpg`, `golem/side_by_side.jpg`, `owl/side_by_side.jpg` compare stage 1 vs stage 4, not reference vs model; the sheet is only in `reference/sheet.png`. Regenerate with the reference columns like the other 16.
- `snake` and `crocodile` renders are tiny in frame (orbit and side_by_side); the camera is framed on the bounding sphere of a long flat creature. Frame on the bbox, not the sphere, for low-aspect creatures.
- `ogre/side_by_side.jpg` is a 6-up strip, no top row.

## Per creature

### fox (7)
1. Tail hangs straight down from the rump (T0-T4 in `SECS`): the sheet tail trails back and level, the tip past the hocks. Fix: `SECS` T1-T4 move y back (+0.15 .. +0.30) and raise z so the tail axis sits ~20 deg below horizontal; keep T0 tip at z ~0.12.
2. Muzzle short and blunt, head small for the body. Fix: `SECS` H2-H4 push y forward by ~0.06 and lower `MUZ` top edge (0.62, 0.95) -> (0.62, 0.9); scale H0-H1 W by 1.1.
3. Belly line is one flat orange plane; the sheet's dark underbelly and white chest are the only shape cue from below. Fix: `body_rule` in stage 3, cream band on the three lower faces of C0-M0 (colour, lowest priority).

### bear (7)
1. No shoulder hump, back a flat ridge: the sheet peaks over the shoulders and slopes to the rump. Fix: `SECS` C0-C1 top z +0.08 (1.205 -> 1.28, 1.245 -> 1.32), R1-R2 top z -0.04.
2. Head and neck under-scaled (sheet: skull wide as the chest in front view). Fix: `SECS` H0-H1 W x1.2 (0.20 -> 0.24, 0.155 -> 0.19), N0 W 0.23 -> 0.27.
3. Legs are straight pillars, rear legs splay apart in the rear view. Fix: `HIND` first two rings x 0.20 -> 0.16, `FORE` rings keep x but ry +0.02 so the leg reads as a wedge, not a tube.

### boar (6.5)
1. Tusks barely visible (sheet: tusks curl up past the snout). Fix: `tusk` in stage 3, length x2 and curl +30 deg, root one ring back (H3 instead of H4).
2. Head small and low, rear hips too narrow (sheet is a wedge, deep at the shoulder). Fix: `SECS` N0-H1 W x1.15; R0-R1 W 0.14/0.22 -> 0.17/0.24.
3. Pink snout patch on the front face reads as a cartoon nose (owner rule: no face patches). Fix: `body_rule` stage 3, drop the pink disc, keep the snout as the same brown, dark-only nostrils.

### tiger (6)
1. Front view: white cheek ruff + white chest + pink nose bar read as a face mask (owner rule). Fix: `body_rule` stage 3, remove the white ruff faces on H0b-H1 sides and the pink bar; keep white only on the three lower muzzle faces and the belly.
2. Shoulders stand higher than the hips; the sheet back is level. Fix: `SECS` C1-C2 top z 0.97/1.02 -> 0.90/0.95, N0 0.05 lower.
3. Head block is as wide as the chest (H0 W 0.255 vs C0 0.24). Fix: `SECS` H0-H0b W x0.85, H1 x0.9.

### stag (8)
1. Neck mane is a dark blocky bib; the sheet mane is a soft lighter ruff. Fix: `clumps` / `body_rule` stage 3, reduce the mane clump depth by half and lift the colour to the body brown (colour after shape).
2. Head slightly small for the antler mass. Fix: `SECS` H0-H0b W 0.12 -> 0.135, H1 0.085 -> 0.095.
3. Legs very thin at the cannon (W 0.04). Fix: `FORE`/`HIND` ring 4 rx/ry +0.008.

### snake (5)
1. Body is a flat ribbon from the side: `BKEY` z-top ~0.21-0.28 with W ~0.10 gives a 2:1 flattened section, and the belly plates on `BODY` ((1, 0.12) -> (0.95, -0.55)) flatten it further. Fix: `BKEY` z top +0.06 across the mid body, `BODY` profile side vertex (1, 0.12) -> (1, 0.0), belly vertex (0.95, -0.55) -> (0.85, -0.6).
2. Head is a raised square box (`HEADK` H1-H4 W 0.074-0.116 with a flat crown). Fix: `HEAD` profile crown (0.78, 0.96) -> (0.7, 0.85) and narrow H3-H4 W by 15 %; drop the raise so the head sits 1 cm, not 3 cm, above the neck.
3. Plan S-curve is good; the tail taper ends in a needle (`BKEY` last 4 keys). Fix: cut the last two keys so the tip is 2 cm wide.

### crocodile (6)
1. Snout short and chunky for a crocodile (sheet: snout ~1/3 of the body). Fix: `SECS` H2-H5 y stretch x1.25 (H5 -1.434 -> -1.70), H3-H5 W -15 %.
2. Body is two stacked slabs (dark back plate over cream belly plate) with a visible step line in side view. Fix: `BODY` profile side vertex (1, 0.12) -> (1, -0.1) so the belly colour seam sits lower and the trunk reads round-backed.
3. Dorsal scutes too small to read from the side. Fix: `block` in stage 3, scute height x1.6 along R0-T3, two rows only.

### shark (6)
1. Pectoral fins hang down and forward and the shark stands on them (the `PECTORAL` normal (0.57, 0.82) points mostly up, so the blade lies near the ground). Fix: normal -> (0.85, 0.5), and raise the root level z 0.22 -> 0.30 so the fins stick out sideways and slightly down.
2. Head is blunt and the body deep: the sheet is a spindle. Fix: `SECS` head rings W -10 %, mid rings T/B -8 %.
3. White underside wraps up over the jaw and reads as a face pattern from the front (owner rule). Fix: `body_rule` stage 3, white only on faces whose normal z < -0.3.

### koi (6.5)
1. Body too deep and short (humpback). Fix: `SECS` mid-body z top -8 %, stretch y x1.1; `BODY` profile (0.78, 0.8) -> (0.7, 0.85).
2. Red patches are full vertical bands, reading as stripes, not koi patches. Fix: `body_rule` stage 3, patches limited to the upper two face rows, break the rear band.
3. Dorsal and caudal fins are needle-thin blades. Fix: `DORSAL_LV`/`LOBE_LV` thickness x1.6, caudal `UPPER`/`LOWER` reach +20 %.

### chameleon (6.5)
1. Legs are straight vertical stilts; the sheet legs crouch with a bent knee and elbow out. Fix: `FORE`/`HIND` ring 1 x 0.205 -> 0.26, z 0.18 -> 0.22 (elbow out), wrist/ankle rings x back to 0.21.
2. Head too long and low; the casque should rise above the back. Fix: `HEADS` H0 crown (0, 1.04) -> (0, 1.12), H2-H4 y compressed x0.85.
3. Mitten feet missing (two-lobe split foot is the species cue). Fix: `claw` in stage 3, split the foot into two lobes, drop the single claw.

### dragon (7.5)
1. Head small for the chest (H0 W 0.13 vs C0 0.34). Fix: `SECS` H0-H1 W x1.2, horn root follows.
2. Wings small and rooted too far back (`WING` root y -1.02 sits over the mid back). Fix: root y -1.02 -> -1.25, W tip (0.44, -0.80, 1.44) -> (0.55, -0.95, 1.70), F1 x 0.56 -> 0.70.
3. Legs thin under a heavy chest (`FORE` elbow 0.13 vs C0 0.34). Fix: `FORE` rings rx/ry x1.2, `HIND` thigh x1.15.

### goblin (6)
1. From the side the nose cone (`NOSE` 3 rings on H1b) reads as an elephant trunk. Fix: `NOSE` shorten to two rings, root higher (H2 brow), tip turned down 10 deg; H1-H1b y front -0.215 -> -0.19.
2. Legs thick and short (LEG rings 0.055-0.066 vs the sheet's thin shanks). Fix: `LEG` rings 1-3 r x0.8, ring 0 z 0.215 -> 0.25.
3. Vest reads as a dark bib on the chest. Fix: `vest` stage 3, open the front (two straps), keep the back panel.

### golem (7)
1. Head perched on top; the sheet head is sunk into the chest with no neck. Fix: `SECS` N0 z 1.71 -> 1.66, H0-H3 z -0.06, P6 shelf W 0.38 -> 0.44.
2. Arms thinner than the sheet boulder arms. Fix: `ARM` rings 3-5 r x1.2.
3. Chest slabs are white squares, not sheet plates. Fix: `slab` stage 3, same grey as the body, inset only (shape stays, colour matches).

### ogre (6)
1. Belly weak; the sheet is a sphere hanging below the chest. Fix: `SECS` B0-B1 W 0.47/0.43 -> 0.55/0.52, yf -0.49/-0.52 -> -0.60/-0.64.
2. Arms thin tubes ending in cube fists. Fix: `ARM` rings 1-3 rx/ry x1.3, fist ring 5 rx 0.17 -> 0.2, ring 6 taper off.
3. Head slopes to a point, no jaw. Fix: `SECS` H0 yf -0.32 -> -0.38 (jaw forward), H3-H4 W +0.03 (rounder skull).

### knight (6.5)
1. Shield is a flat disc drawn on the cape (`shield` th 0.035 on the cape plane). Fix: `shield` th 0.035 -> 0.09, boss +0.03, rim ring as a real lip; or hang it on the back as its own box clear of the cape.
2. Sword is a thin stick dangling at the hip. Fix: `sword` blade half-width x2, scabbard box, angle 25 deg back.
3. Legs thin at the shin (LEG rings 2-3 0.08/0.075). Fix: rings 2-3 r x1.2, add the greave edge via `knee_cop` offset.

### octopus (7)
1. Arms are straight tapering sticks; the sheet arms curl at the tips. Fix: `ARMS` plan S amplitude 0.01 -> 0.04, last two `ARM_T` z lifted 0.04 so the tip curls up.
2. Mantle tipped back 35 deg and pinched; the sheet egg is rounder and more upright. Fix: `MA`/`MTIP` axis 35 -> 50 deg, `MANTLE` widths x1.1.
3. Arms uniform in thickness. Fix: root half width 0.032 -> 0.042, keep the tip.

### spider (7.5)
1. Legs too straight; the sheet knees arch high above the carapace. Fix: `LEG_T` ring 3 z 0.63 -> 0.72, ring 5 z 0.42 -> 0.35.
2. Abdomen faceted and flat at the rear (A1-A3). Fix: `ABD` profile (1, 0.3) -> (1, 0.15), A1 T/B +0.03.
3. Pedipalps missing beside the fangs. Fix: `grow_fang` second pair on column 2, half length.

### crab (6)
1. Claws raised above the carapace like boxing gloves; the sheet claws point forward and level, palm out. Fix: `CLAW` rings 5-12 z -0.08 (palm top 0.276 -> 0.20), y -0.03 further forward; dactyl pointing inward-forward.
2. Carapace too tall and boxy (T/B 0.078 after x0.85). Fix: `_S` T/B x0.8, W x1.1; `SHELL` (1, 0.0) -> (1, -0.15).
3. Legs splay too wide and long. Fix: `LEGS` scale 1.12-1.15 -> 1.0, `LEG_PTS` knee z 0.165 -> 0.14.

### owl (7.5)
1. Body loafs backward into a long horizontal tail; the sheet owl is an upright drop. Fix: `SECS` T0-T1 y 0.262/0.215 -> 0.20/0.17, R0 z top 0.24 -> 0.30.
2. Face disc flat; a shallow facial dish helps the owl read from 3/4. Fix: `FACE` profile (0.8, 0.88) -> (0.85, 0.95), H3 W 0.07 -> 0.08.
3. Eyes orange rings with dark centres are fine as lenses; the orange ring is large. Fix: `lens` radius x0.8.

### raven_wyvern (7.5)
1. Tail too long and thin (T0 at y 1.085 vs body 0.6). Fix: `SECS` T0-T1 y 1.085/0.95 -> 0.95/0.85, T0 ry 0.15 -> 0.18.
2. Head narrow and small. Fix: `SECS` H0-H2 W x1.15.
3. Chest narrows to the legs; the sheet raven is a round chest. Fix: `CHEST` profile (0.9, -0.3) -> (0.95, -0.4), C0 W 0.23 -> 0.25.

## Five worst

snake 5, crab 6, goblin 6, ogre 6, tiger 6 (shark and crocodile also at 6; the tiger ranks among the worst because of the owner face rule, the crab because of the claw pose).
