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
| build | 61 joints, 6,190 vertices, 7,944 triangles (claims band 4,000-9,000), all green |
| clips | `idle` (breath, head tilt, wing settle), `move` (bipedal stride, balance flutter), `attack` (neck and wings wind back with the bill open, then the root lunges and the neck throws the bill forward) |
| declared | named parts, `function` (head = effector, legs, wings and toes = locomotion), `joint_range` for every animated joint |
| colour | hero view saturated area 26.1%, median albedo luminance 69.6. Near-neutral slate masses with a dark saddle and a pale breast, dusky violet wings, magenta crest and tail fan (the spotlight), gold bill |

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
- **`part_seat` under-reads burial in thin volumes.** It tests a sphere around
  the nearest ring centre, not the surface. A claw seated 12 mm deep inside a
  22 mm toe reads "0% inside a body", so the claws here start at the toe-tip
  ring centre.
- **A membrane is one flat colour.** `colors.arcs` exists only on volumes, so
  the wing has no darker leading edge or vein pattern.
- **With membrane wings, colour budget and spotlight pull against each other.**
  The spread membrane is about 30% of the hero view on its own, so a saturated
  membrane lands at 48-55% saturated area, far over the card's 34% ceiling. The
  wings are dusky violet (just under HSV S 0.5), and the vivid colour moved to
  the crest and tail fan.
- **An open volume end shows the background.** A body left with `"none"` at
  the chest end passed every check. In a real renderer, the gap between that
  open ring and the neck showed as a white crescent (backface culling). The
  body is domed at both ends here, but nothing checks for this.
- **False `part_overlap` warnings on tufts.** The build warns that `wing_skin`
  sits 96% inside `hackles`. It doesn't: `signedDistance` takes its sign from
  whichever face happens to be nearest at a tuft's tip, so points well clear of
  the tuft read as inside it.
