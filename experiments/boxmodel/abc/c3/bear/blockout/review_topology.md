# bear c3 cage: form and topology review

Packet: `abc/c3/bear/blockout/` against `refs/gpt/bear/concept_2.png`; previous cage `abc/c2/bear/blockout/`.

| | form /10 | topology /10 |
|---|---|---|
| c3 (new) | 6.5 | 7.0 |
| c2 (previous) | 5.5 | 3.0 |

**Verdict: FIX** (one round, stage 1; four of the five fixes are local).

## Form (medium forms against the concept)

- **Head: good, no longer a wedge or a box.** Depth and width profiles sit on the reference (taper 3.14 vs 3.15, 4.39 vs 4.40; tube 0.67/0.67, 0.58/0.59; RMS 2.6%). Cranium, cheek step and muzzle read as three masses in hero and top. c2's head was a single box (width tube 0.77 vs 0.59). Two faults remain: the muzzle tip closes to a point where the concept has a blunt, boxy nose block, and the head/neck join is a hard collar ledge (a step ring, see topology 2) where the concept has a soft ruff.
- **Fore limb: FAILS, and my eye agrees with the gate.** Side depth is right (RMS 1.5%), with a shoulder mass and an elbow break. From the front the limb is a straight column: width tube 0.94 against 0.76, taper 1.19 against 2.41, last station 15.9% off. The "intended" note explains the last station only; the concept's fore limb narrows at the wrist and spreads into a broad paw, and the cage does neither. The paw itself is a sloped wedge with no distinct paw mass.
- **Hind limb: passes** (RMS 2.3%, tube 0.91/0.92, 0.95/0.92). Thigh mass and hock read in side and back 3/4. The reference hind is itself near-columnar below the knee, so the high tube score is correct, not a tube fault. Paw is the same wedge as the fore.
- **Body:** hump, shoulder and haunch masses separated; silhouette IoU 0.962 / 0.896 / 0.855, proportions all within 8%. Front view is ~8% too wide at shoulder height (red both sides), which also hides the limb's shoulder swell. Tail stub is absent from the cage (acceptable only if it comes as a piece).

## Topology (as production)

Measured table is right on every gate; my eye disagrees with it on two warnings it does not raise (items 2 and 3).

1. **Density: acceptable, torso at the floor.** All quads (c2: 32 tris, 4 n-gons). Edge ratio 2.67 body-wide; over-5:1 faces 4.2% (c2 19.1%). But torso density 0.53 against head 1.75: the hump is four quads across while the muzzle carries 96 faces. Passes the limit by 0.03.
2. **Neck collar sliver ring.** Neck rings spaced 0.085 and 0.041 on a 0.51-wide neck (0.12 x width); the last ring is the 9.4:1 red band in `4_aspect.jpg`. It is a crease ring, not a bend loop, and it is where the head will pinch on a nod.
3. **Limb-root slivers.** Root loops exist and pass over the joint (c2: below the joint); no fans, no caps, flow 0.50 / 0.62. But each root is closed by long kite quads that converge on the valence-5 pole above the shoulder and hip (5:1 to 7:1, red/orange in `4_aspect.jpg`). In the swing pose these stretch into a fan across the flank (`5_rom.jpg`, swing az090 wire); most of the 37 folded triangles (3.2% of area) are there and in the armpit.
4. **Joints.** Elbow, knee, hock: 2 rings at 0.23 to 0.28 x width, clean bends in fold and crouch. Wrist has ONE ring: the paw hinges on a single edge loop and collapses in the fold pose.
5. **Poles.** 44 (26 x 3, 18 x 5, no 6+), none in a joint band (c2: 176 poles, 44 fans, 22 in joints). Sole corners and the belly line are fine. The shoulder and hip valence-5 poles sit on the scapula and the haunch crest: flat in rest pose but inside the moving mass; better one ring up onto the back.
6. **No lofting.** 0 ring stacks (c2: 11 rings per limb at 0.14 x width). Eye and mouth loops not declared; acceptable at blockout, needed before stage 2 detail on the face.

## Against the previous cage

Topology: a large step, 3 to 7. c2 failed 5 of 6 gates (ring-stacked limbs, 44 fan poles on the paws, 22 poles in joints, root loops below the joint, 19% slivers); c3 passes all six at 36% fewer faces. Form: a modest step, 5.5 to 6.5. The head is clearly better and is the main gain; the fore limb in front view is no better than c2 (width tube 0.94 in both), and c2's paws were broader and read more as paws.

## Fixes (max 5)

1. **Fore limb front-view taper and paw spread** (form, limbs). Narrow the wrist ring ~15% in width and widen the two paw rings ~25 to 30% so the paw is broader than the wrist; target width tube <= 0.82 and taper >= 1.9. Apply the same paw spread (~15%) to the hind.
2. **Second wrist ring** (topology). Add one ring at the wrist, 0.20 to 0.25 x limb width from the existing one, matching elbow and hock.
3. **Limb-root slivers and pole position** (topology). Add one lengthwise loop through the flank between fore and hind roots, and one ring around each root so the closing quads are under 3:1; move the shoulder and hip valence-5 poles ~0.10 m up onto the back. Target: 0 faces over 5:1 at the roots, ROM fold-over under 2% of area.
4. **Neck collar** (topology, head). Respace the three neck rings evenly (~0.06 each, 0.12 x width apart or more) and cut the collar step by about half so it reads as a ruff, not a ledge; removes the 9.4:1 ring.
5. **Torso density and muzzle tip** (topology, head). One extra lengthwise loop each side of the spine over the hump and back (torso density from 0.53 to >= 0.7); blunt the nose: widen and deepen the last muzzle ring ~30% so the tip is a block, not a point.
