# Example: the reference light quadruped (wolf)

`wolf.json` is the reference example — a stylised timber wolf, re-authored
against the 1.4 engine: one body volume from rump to neck with a deep keeled
chest, tucked loin and broad haunch; a head with a real stop (`sharp` row
between skull and muzzle); jointed legs with shoulder/thigh mass, a narrow
cannon and a hock; four-toed paws with claws (`"toes": 4, "claws": true`);
elliptical `curve` ears; an eye with an engine-placed pupil; a bushy dome-capped
tail. Spec-level `shading` at the defaults, `colors.arcs` per volume (dark
saddle, cream belly and muzzle), no faceted masses. Its `_template` and
`_anchor_numbers` fields are an ANCHOR to deviate from, not a target to
converge on; there is no `templates/` library any more (removed in 1.2.0).

Files: `wolf.glb` — skinned (32 joints, 3,970 vertices, 5,484 triangles),
three clips (idle / move / attack), vertex-coloured, AO baked into COLOR_0,
UV off (`"keep_uv": true` is opt-in, and this spec does not set it) —
`wolf_beauty.png` (the projected hero shot over a studio card),
`wolf_silhouette.png` (side view), `wolf_thumb24.png` (the blind-read image).

Measured (hero view): high-saturation area **17.9%**, median luminance 86.7;
shares fur_body 37% · fur_leg 33% · fur_head 16%. Side W/H 1.73, hero W/H 1.32.

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
