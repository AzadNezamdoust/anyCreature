# Zoo20 review (Fable 5.1, 2026-10-17)

Inputs: zoo20_sheet.jpg, per-creature orbit18_sheet.jpg, side_by_side.jpg, stage4/s4_hero_colour.png, reference/sheet.png (spot-checked owl, raven_wyvern, golem, crab, koi, dragon).
Rubric: t7 hand box model (crisp flat planes, flat colour), simple face (small round lens eye), shape over colour, species reads from all 18 views. Score 1-10. Defects ordered shape first; each with a concrete fix for `<creature>.py`.

Read scale: 8+ ship; 7 one fix pass; 6 two passes; <=5 rebuild a part.

---

## fox — 8
1. Tail in top/bottom view is a thin tube until the tip, then fans into a bushy white chunk: silhouette reads "brush on a stick". Fix: tail profile — widen mid-tail radius ~1.6x at 40-70% of length, taper the tip; drop the fringe spikes on the white tip (keep one plane split).
2. Rear view (az180): chest ruff spikes poke below the belly line and jag the outline. Fix: chest ruff piece — clamp lower extent to belly plane, reduce spike count to 3 flat wedges.
3. Hind legs too thin vs forelegs in -45 views. Fix: hind leg upper segment radius +20%, keep hock.

## bear — 8
1. Bottom view: belly is one flat dark slab with square-cornered legs; legs read as four boxes glued on. Fix: leg roots — blend upper leg into torso with one extra loop, round the inner corners.
2. Head is slightly small for a grizzly and muzzle is flat-topped; az0 front reads bear-cub. Fix: head scale +10%, muzzle top plane angled down 10 deg.
3. Claws are long light slivers that read as toes/fingers from -45. Fix: claw length -40%, 3 per paw.

## boar — 7
1. Orbit sheet is grey (stage-4 GLB rendered without material) — cannot judge colour from 18 views; zoo sheet colour is OK. Fix: rerun orbit18 with the colour material (pipeline, not .py).
2. Dorsal bristle crest: separate floating wedges along the spine, visible as a row of loose teeth in top/rear views (el+45_az180). Fix: crest — merge into one continuous serrated strip welded to the spine, 5-6 teeth max, zero gap.
3. Tusks: two thin white planes pointing forward from the cheeks, read as whiskers at az0. Fix: tusk — thicker triangular prism, rooted at the lower jaw, curving up and out.

## tiger — 7
1. Head is too small and boxy; from az0 the face is a pale flat mask with no muzzle break — reads "cat" not "tiger". Fix: head scale +12%, add muzzle block projecting 15% of head length, drop the pale face mask to a small chin/cheek wedge.
2. Tail too thin and stiff, kinks at the base in az180/az225. Fix: tail base radius +50%, taper smoothly, one gentle S-curve.
3. Legs too slender for a tiger; forelimbs read like a dog's. Fix: forearm and shoulder radius +25%, paws wider.

## stag — 7
1. Orbit sheet: bottom and all four el-45 views are blank (render failure, only hoof tips visible) — cannot verify underside/joins. Fix: rerun orbit18 (pipeline; check ground-plane clip or camera distance).
2. Antlers are flat planar blades with tines on one side only; from az0 they read as two combs. Fix: antler — give the beam a 3-sided cross-section and alternate tines left/right of the beam.
3. Neck mane is a dense shaggy ruff of many small spikes (noisy, off-style). Fix: mane — 4-5 large flat wedges along the throat, no small spikes.

## snake — 5
1. Body is a uniform thin tube; no neck taper, no mid-body thickening, no tail taper until the last 10%. Reads as a cord. Fix: body radius profile — head 1.0, neck 0.7, mid 1.4, tail taper from 60% to 0.
2. Head is a tiny wedge hardly wider than the body; from az0/az180 the snake has no head. Fix: head width 1.6x neck, flat top plane, blunt snout.
3. Sweep: S-curve is only in top view; side views show a flat line. Fix: add a slight vertical lift of the neck (head raised 1.5 body diameters) so the silhouette has a head end.

## crocodile — 6
1. Model is very small/flat in all orbit frames; body is a slab with a jaw that doesn't read as a long snout at az0/az180. Fix: snout — lengthen 25%, narrow the tip, add a visible upper/lower jaw split plane.
2. Scutes: a grid of small bumps across the back — texture noise, not shape. Fix: replace the grid with two rows of 6-8 large flat ridge wedges along the spine and tail.
3. Legs splay as four short pegs; top view shows them as stubs. Fix: leg length +30%, elbow out, foot flat with 3 toes.

## shark — 7
1. Pectoral fins are thin flat blades mounted mid-body with a visible gap at the root; from az180 they stick out like wings. Fix: pectoral — root thickened and welded into the flank, sweep back 30 deg.
2. Gill slits are painted lines (five dark bars) on a flat plane: off-style decal. Fix: gills — 3 shallow cut planes, or drop them.
3. Tail fin: lower lobe too short and the tail base kinks. Fix: caudal — lower lobe 60% of upper, tail peduncle smooth.

## koi — 6
1. Fins are rigid flat paddles at right angles to the body (pectorals stick straight out, pelvic and anal fins hang down like legs) — the fish reads as standing on fins. Fix: pectorals swept back 40 deg and angled down 15; pelvic/anal fins shortened 40% and laid flat to the belly.
2. Body cross-section is too round/short; koi is a long torpedo. Fix: body length +20%, depth -10%.
3. Markings: hard rectangular stripe blocks; the black spot is a square. Fix: colour islands follow mesh planes with irregular 3-5 sided patches (colour only, minor).

## chameleon — 7
1. Casque is a tall flat triangle on top of the head; from az0 it is a spike. Fix: casque — 3-sided ridge, leaning back 20 deg, base blended to the skull.
2. Dorsal spines: tiny individual nubs along the spine (noise). Fix: 6 larger wedges or none.
3. Feet are flat mittens with pin claws. Fix: foot — split into two opposed pads (zygodactyl), drop the pin claws.

## dragon — 6
1. Wings are flat kite membranes with one spar; from az0/az180 they read as paper triangles stuck to the shoulders, no fold/elbow. Fix: wing — add elbow joint (finger root) so the wing has two panels, root thickened and welded to the shoulder block.
2. Neck is short and head sits directly on the chest; sheet has a long neck. Fix: neck +50% length, two segments, head raised above the shoulder line.
3. Dorsal spines: many tiny white triangles down the spine and tail (noise, visible in top view as a dotted line). Fix: spines — 8-10 larger wedges, spacing 1.5x.

## goblin — 6
1. Ears are enormous flat blades (span wider than the shoulders), green tip + pink inner mask reads as a face mask from az0. Fix: ear length -40%, thickness +, single flat colour with a thin inner wedge.
2. Arms hang to the knees and are tube-straight, no elbow; feet are long flat boards. Fix: arm length -15%, add elbow bend; foot length -30%.
3. Loincloth and back strap are thin dark paper planes that intersect the body in az90. Fix: loincloth — thickened block, offset from the pelvis by 2% of height.

## golem — 6
1. Feet: hands and feet are rounded blobs with light nub toes; from -45 views the feet are the same shape as the fists. Fix: foot — flat slab with 3 square toes; fist — cube with knuckle plane.
2. Head is a small dome sunk between the shoulders; sheet has a visible neck-less head slab. Fix: head scale +15%, raise 5% of height so the eyes clear the pec line.
3. Moss is only on the shoulders as a flat green cap; cyan crack is a painted zigzag line. Fix: moss — extend down the upper arm as a second patch; crack — cut as a thin recessed plane strip or drop (decal is off-style).

## ogre — 7
1. Belly plate: a beige slab that wraps 180 deg and reads as a vest; the strap crosses it as a flat decal. Fix: belly — reduce the pale area to a front patch 60% of chest width; strap — thin extruded block, not painted.
2. Head is small and sunk; from az90 the brow and jaw are one wedge. Fix: head +10%, jaw block projecting forward 10% of head depth, tusks thicker.
3. Legs are short stumps with no knee; feet are flat ovals with painted toes. Fix: leg +15% length, knee loop, 3 block toes.

## knight — 7
1. Cape is a flat blue sheet welded flat to the back with a painted white ring; from az90 it is a 2 mm plane. Fix: cape — thickness 3% of width, hang 10 deg off the back; replace the painted ring with a small raised rim or drop it.
2. Helmet is a round bucket with a dark slot — reads as a face mask. Fix: helmet — flat front plate with a thin horizontal visor slit cut as a plane.
3. Sword is a thin stick with a cross; scabbard intersects the leg in -45 views. Fix: sword — blade width +50%; scabbard moved 3% outward on the hip.

## octopus — 7
1. Arms are eight tapered tubes radiating in a flat star; in side views the arms lie in one plane and the mantle floats above them. Fix: arm roots — drop 4 arms 10 deg below the others, add one bend per arm.
2. Mantle is a smooth sphere; sheet has an elongated sac. Fix: mantle length +25%, tip slightly pinched.
3. Suckers: rows of small painted dots on the underside (decal). Fix: suckers — drop, or 3-4 raised flat discs per arm.

## spider — 8
1. Cephalothorax is a small box behind a huge abdomen; from az0 the head is hard to find. Fix: cephalothorax +20%, abdomen -10%.
2. Legs: all eight leave the body at the same angle, so the top view is a symmetric star. Fix: front pair swept forward 30 deg, rear pair back 30 deg.
3. Stripes: orange bands are mesh-plane bands (fine) but the fangs/chelicerae are two tiny nubs. Fix: chelicerae — one wedge each, 2x length.

## crab — 5
1. Claws: in the hero (and zoo sheet) the posed left claw's pincer fingers jut forward as three stacked white tines and intersect the carapace; right claw points at camera as a blob. Jumbled, flag as broken. Fix: pincer — two opposed fingers only (fixed + movable), rigid, rooted on the propodus; hero pose — raise claws up and out, no body intersection.
2. Carapace is a round ball; sheet is a wide flat shield. Fix: carapace width 1.5x depth, height -30%, straight front edge.
3. Legs are thin L-sticks with no segment breaks; walking legs splay below the body like a spider. Fix: legs — 3 segments with knee up, foot tip down; leg thickness +40%.

## owl — 5
1. Reads as a bear cub / cat from most angles: body is a wide furry lump with "paws", wings are side flaps with fringed edges, no tail. Fix: body — upright egg, narrower at the base; wings — two flat folded planes lying on the back, tip past the tail; add a short flat tail fan.
2. Face: flat pale disc with tiny dots for eyes and a fur fringe; sheet has large forward eyes in a facial disc. Keep eyes simple but give the face a shape. Fix: facial disc — single shallow concave plane, eye lenses 2x size, beak a small downward wedge.
3. Feet are big pale paw pads with dark claws; owl has thin talons. Fix: foot — 3 thin toe blocks forward, 1 back, no pad.

## raven_wyvern — 6
1. Wings/tail: fringed spikes along every edge (feather noise), the folded wings are thin planes that float off the body in az180. Fix: wings — solid folded wedges welded to the flank, 3 large feather steps at the tip only.
2. Head/beak: beak is correct in profile but from az0 the head is a narrow slot with no eye visible. Fix: head width +20%, eye lens on the cheek plane.
3. Tail is a long flat plank; sheet tail is a wedge fan. Fix: tail — 3-step fan widening to the tip, thickness +.

---

## Summary
| creature | score |
|---|---|
| fox | 8 |
| bear | 8 |
| spider | 8 |
| boar | 7 |
| tiger | 7 |
| stag | 7 |
| shark | 7 |
| chameleon | 7 |
| ogre | 7 |
| knight | 7 |
| octopus | 7 |
| crocodile | 6 |
| koi | 6 |
| dragon | 6 |
| goblin | 6 |
| golem | 6 |
| raven_wyvern | 6 |
| snake | 5 |
| crab | 5 |
| owl | 5 |

Worst 5: owl, crab, snake, dragon, koi.

Broken outright: crab pincer fingers (jumbled, intersect body); stag orbit sheet missing bottom + el-45 renders; boar orbit sheet rendered grey (no colour).
