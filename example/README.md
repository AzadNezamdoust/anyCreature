# Example: the reference light quadruped (wolf)

`wolf.json` is the reference example — a stylised timber wolf, re-authored
against the 1.4 engine: one body volume from rump to neck with a deep keeled
chest, tucked loin, broad haunch and a thick neck; a broad skull with a real
stop (`sharp` row between skull and muzzle) and a heavy muzzle; jointed legs
with a real thigh and upper arm (the leg ellipse is deep fore-aft, narrow
side-to-side — a haunch, not a post), a narrow cannon and a hock; four-toed
paws with claws (`"toes": 4, "claws": true`); broad-based elliptical `curve`
ears with a pale inside (`colors.arcs` on a curve); an eye with an engine-placed
pupil; a bushy tail. The wolf signature — the neck ruff — is a `tufts` part:
six-sided fur CLUMPS with a root-to-tip colour ramp (grey roots, cream tips),
cheek tufts on the head, a brush along the tail in its own `fur_brush` and
three dark tufts extending the tip. The palette is a wolf value plan written
with t-ranged, feathered `colors.arcs`, every feather at 2-3x its ring step so
it is a gradient and not a hard band: a cool charcoal saddle over the top
third melting into a tawny lower flank, cream chest / belly / muzzle, a soft
pale inner leg, a light cheek mask under a dark crown, a nose bridge and lower
lip a step darker, a dark (not black) tail tip. Spec-level `shading` at the
defaults (junction normals hide the limb / torso seams), no faceted masses:
every volume keeps the default `smooth_angle` 50. Its `_template` and
`_anchor_numbers` fields are an ANCHOR to deviate from, not a target to
converge on; there is no `templates/` library any more (removed in 1.2.0).

Files: `wolf.glb` — skinned (32 joints, 5,691 vertices, 7,688 triangles),
three clips (idle / move / attack), vertex-coloured, AO baked into COLOR_0,
UV off (`"keep_uv": true` is opt-in, and this spec does not set it) —
`wolf_beauty.png` (the projected hero shot over a studio card),
`wolf_silhouette.png` (side view), `wolf_thumb24.png` (the blind-read image).

Measured (hero view): high-saturation area **20.1%**, median luminance 90.7;
shares fur_leg 33% · fur_body 29% · fur_head 14% · fur_tail 7% · fur_ruff 7%.
Side W/H 1.79, hero W/H 1.36.

```bash
# rebuild
node engine/cli.js example/wolf.json example/wolf.glb
# silhouettes + thumbs + every measure (layout, boldness, part shares, colour)
python3 harness/outline.py example/wolf.glb out/r1
# the hero shot, projected not rendered
python3 harness/outline.py example/wolf.glb out/r1 --hero out/r1/hero.png
# claims judged over those numbers (add --spec <claims.json> to check claims)
node harness/judge.mjs example/wolf.glb out/j wolf
```
