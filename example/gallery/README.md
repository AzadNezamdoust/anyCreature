# Gallery: creatures that are not the wolf

`example/wolf.json` is one light quadruped. The creatures here exist to show that
the same engine builds a different body plan, and `tools/test.sh` rebuilds each
spec in this folder on every run and fails on any `BLOCK`. Like the wolf, they
are syntax references. Don't use them as a starting skeleton: `example_copy`
only guards the wolf and the calibration samples, so nothing will stop you, but
the design cards ask for a skeleton built from your own brief.

## raven_wyvern: a crested raven-wyvern

![beauty](raven_wyvern_beauty.png)

A bipedal wyvern with a raven's head. Its forelimbs are membrane wings, raised
in a swept-back mantle. It has a heavy hooked bill with a hinged lower mandible,
a fan of violet crest blades, a pale shaggy throat bib, feathered thighs over
scaled shanks, and four-toed talons with hooked claws (three toes forward and a
hallux back). A long whip tail ends in a violet feather fan.

| | |
|---|---|
| build | 61 joints, 6,622 vertices, 8,520 triangles (claims band 4,000-9,000), all green |
| clips | `idle` (breath, head tilt, wing settle), `move` (bipedal stride, balance flutter), `attack` (neck and wings wind back with the bill open, then the root lunges and the neck throws the bill forward) |
| declared | named parts, `function` (head = effector, legs, wings and toes = locomotion), `joint_range` for every animated joint |
| colour | hero view saturated area 25.6%, median albedo luminance 71.4. Near-neutral slate masses with a dark saddle and a pale breast, dusky violet wings, magenta crest and tail fan (the spotlight), gold bill |

What it exercises that the wolf does not:

- **`membrane` wings.** Each wing has four ribs: the arm as the leading edge,
  two fingers, and a trail chain that brings the sheet back to the flank. The
  arm and the fingers are thin volumes, so the bones show through the skin.
- **Toes as chains.** Each talon toe is its own three-joint chain with a volume.
  The claw is a `curve` inserted into that toe's dome. A claw can't be seated in
  a `curve` toe (see below), and `paw` only builds a mammal pad.
- **A loose joint** (`Jaw`, attached to `Skull`) that carries the lower bill, so
  the attack opens the beak.
- **`tufts` used as feathers**: the throat bib, the feathered thighs and the
  tail fan. **`curve` blades** make the crest.

Files: `raven_wyvern.json` (the spec), `raven_wyvern.glb` (built from it, skinned,
three clips, AO baked), `raven_wyvern.checks.json` (the engine's gate stamp),
`raven_wyvern_beauty.png` (the `outline.py --hero` shot) and
`raven_wyvern_silhouette.png` (side view).

Rebuild and measure:

```bash
node engine/cli.js example/gallery/raven_wyvern.json example/gallery/raven_wyvern.glb
python3 harness/outline.py example/gallery/raven_wyvern.glb out/rw --hero out/rw/hero.png
node harness/judge.mjs example/gallery/raven_wyvern.glb out/rw raven_wyvern
```

### Where the engine got in the way

These are engine limits, not choices made for this design:

- **A part cannot host a part.** `part_seat` and `part_attachment` measure only
  against volumes, so a claw on a `curve` toe is refused as floating. The
  workaround here was to turn every toe into a chain.
- **A membrane is one flat colour.** `colors.arcs` works on volumes and curves but
  not on membranes, so the wing has no darker leading edge or vein pattern.
- **With membrane wings, colour budget and spotlight pull against each other.**
  The spread membrane is about 30% of the hero view on its own, so a saturated
  membrane lands at 48-55% saturated area, far over the card's 34% ceiling. The
  wings are dusky violet (just under HSV S 0.5), and the vivid colour moved to
  the crest and tail fan.
- **An open volume end shows the background.** A body left with `"none"` at
  the chest end passed every check. In a real renderer, the gap between that
  open ring and the neck showed as a white crescent (backface culling). The
  body is domed at both ends here, but nothing checks for this.

The build warns that `lower_bill` sits 63% inside `upper_bill`. That one is
real and intended: the closed bill halves overlap at rest, and the `Jaw` hinge
opens them in the attack.

## giant: a menacing mountain giant

![beauty](giant_beauty.png)

The README's canonical order, "make me a menacing mountain giant", at 4 m. A
heavy, hunched biped whose signature is its fists: each one is about a metre
across, built from a palm, four folded fingers and a wrapped thumb, with the
back of the hand facing forward and the knuckle row as the striking face. The
shoulders rise above a small, low head with a heavy brow, amber eyes and an
underbite with two tusks. Granite-grey hide with a mottled pattern, a moss
mantle and rock crags on the hump, and sandstone fists behind a dark crust at
each wrist.

| | |
|---|---|
| build | 71 joints, 5,349 vertices, 8,814 triangles (claims band 4,000-9,000), all green |
| clips | `idle` (breath, head sway, arm settle), `move` (heavy bipedal walk with pelvis bob and sway, arms swinging opposite the legs), `attack` (both fists pull back, rise overhead, then the body pitches forward and the fists come down together in front, jaw open) |
| declared | named parts, `function` (arms, palms, fingers and thumbs = effector, legs = locomotion), `joint_range` for every animated joint |
| colour | hero view saturated area 19.1%, median albedo luminance 73.9. The fists are the brightest large mass (ochre, OKLab L 0.66); the hide is a cool slate (L 0.51) with a darker back and a pale chest; moss and rock sit on the hump; the eyes are the accent |

What it exercises that the wolf and the raven do not:

- **Fists as chains.** The stock `hand` part at `"fist": true` came out as a
  flat palm slab with thin hooked fingers, which read as a paddle at this size
  (its finger radius is fixed at 0.088 x `size`, and every vertex rides one
  joint). Each fist here is a palm chain (`LHand`) plus five chains for the
  fingers and thumb, each with its own volume, so there are real knuckles and
  the fingers could be animated.
- **`shade: "hard"` on flesh-coloured volumes.** The palm, fingers and thumb
  are declared hard. See the L1 note below.
- **A two-fisted strike.** The shoulders' `ry`/`rz` bring the fists together
  at impact. `attack_windup` and `effector_leads` both pass.

Files: `giant.json` (the spec), `giant.glb`, `giant.checks.json`,
`giant_beauty.png` (the `outline.py --hero` shot) and `giant_silhouette.png`
(front view, where the fists read).

```bash
node engine/cli.js example/gallery/giant.json example/gallery/giant.glb
python3 harness/outline.py example/gallery/giant.glb out/giant --hero out/giant/hero.png
node harness/judge.mjs example/gallery/giant.glb out/giant giant
```

### Where the engine got in the way

- **`effector_leads` does not count a mirrored part's twin.** SYNTAX.md says a
  chain listed in `mirror` covers its twin. That holds for a twin volume,
  which keeps its source's chain name. A twin part (the right `hand`) finds its
  chain through its skin, which gives `RArm`, so it counts as "something else".
  A two-fisted slam with `"LArm": "effector"` was blocked because the right fist
  tied the left one: "frontmost part is fist@fist.R at z=2.68, ahead of the
  declared effector at z=2.68". The workaround is to name the R chains in
  `function` as well, which this spec does.
- **The L1 seam blend reaches across gaps and smears detail.** Its radius is
  `max(3% of the diagonal, 3 x the median edge)`. On a 4 m body that is about
  20-25 cm, wider than a finger. The flesh fists hanging beside the thighs
  painted the knees ochre. The pale knuckle arcs were averaged into the
  neighbouring fingers. Raising an arm shows the torso's moss tint on its
  inner side, because the blend is baked at the bind pose. Declaring the fist
  pieces `shade: "hard"` takes them out of L1, and moving the knees in keeps the
  legs clear of the rest.
- **`joint_range` is swept from the bind pose only.** `LShoulder.rz` is capped
  at -15 degrees because a finger reaches the foot at rest. In the attack the
  arm is forward, where nothing is in the way.
- **Bevel-skip thins the rings on sharply bent chains.** A finger with two
  90-degree bends keeps rings about a sixth of its length apart, so a
  `feather_t` has to be about 0.34 before it does anything (the compiler says
  so).

The build warns about a steep profile slope on the torso (1.15 at t=0.92, where
the hump turns into its dome) and on the palm (0.91, where the wrist flares).
The anim_integrity check measures no folds in any clip, so both warnings are
left as they are.
