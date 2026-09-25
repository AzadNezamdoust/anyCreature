# Example: the reference light quadruped (wolf)

`wolf.json` is the reference example — a stylised timber wolf, re-authored
against the 1.4 engine: one body volume from rump to neck with a deep keeled
chest, tucked loin, broad haunch and a thick neck; a broad skull with a real
stop (`sharp` row between skull and muzzle) and a heavy muzzle; jointed legs
with shoulder/thigh mass, a narrow cannon and a hock; four-toed paws with claws
(`"toes": 4, "claws": true`); broad-based elliptical `curve` ears; an eye with
an engine-placed pupil; a bushy tail. The wolf signature — the neck ruff — is a
`tufts` part, with cheek tufts on the head and a fringe under the tail. The
palette is a wolf value plan written with t-ranged, feathered `colors.arcs`:
charcoal saddle melting into a tawny flank, cream chest / belly / muzzle /
inner leg, a light cheek mask under a dark crown, a dark tail tip. Spec-level
`shading` at the defaults (junction normals hide the limb / torso seams), no
faceted masses: every volume keeps the default `smooth_angle` 50. Its
`_template` and `_anchor_numbers` fields are an ANCHOR to deviate from, not a
target to converge on; there is no `templates/` library any more (removed in
1.2.0).

Files: `wolf.glb` — skinned (32 joints, 4,562 vertices, 6,260 triangles),
three clips (idle / move / attack), vertex-coloured, AO baked into COLOR_0,
UV off (`"keep_uv": true` is opt-in, and this spec does not set it) —
`wolf_beauty.png` (the projected hero shot over a studio card),
`wolf_silhouette.png` (side view), `wolf_thumb24.png` (the blind-read image).

Measured (hero view): high-saturation area **18.2%**, median luminance 92.9;
shares fur_leg 31% · fur_body 30% · fur_head 14% · fur_tail 8% · fur_ruff 7%.
Side W/H 1.78, hero W/H 1.35.

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
