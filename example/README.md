# Example: the reference light quadruped (wolf)

`wolf.json` is the reference example — a stylised timber wolf, re-authored
against the 1.4 engine: one body volume from rump to neck with a deep keeled
chest, tucked loin, broad haunch and a thick neck; a broad skull with a real
stop (`sharp` row between skull and muzzle) and a heavy muzzle; jointed legs
with a real thigh and upper arm (the leg ellipse is deep fore-aft, narrow
side-to-side — a haunch, not a post), a narrow cannon and a hock; four-toed
paws with claws (`"toes": 4, "claws": true`); broad-based elliptical `curve`
ears with a pale inside (`colors.arcs` on a curve); an eye with an engine-placed
pupil, seated under a `lid` in the head's own fur; a bushy tail. The wolf signature — the neck ruff — is a `tufts` part:
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

Files: `wolf.glb` — skinned (32 joints, 5,805 vertices, 7,936 triangles),
three clips (idle / move / attack), vertex-coloured, AO baked into COLOR_0,
UV off (`"keep_uv": true` is opt-in, and this spec does not set it) —
`wolf_beauty.png` (the projected hero shot over a studio card),
`wolf_silhouette.png` (side view), `wolf_thumb24.png` (the blind-read image).

Measured (hero view, on the palette): **28.5%** coloured (HSV S ≥ 0.30, the tawny
legs and paws), 0.1% loud (S ≥ 0.50 — a muted natural palette); median shipped
luminance 91.7;
shares fur_leg 33% · fur_body 29% · fur_head 15% · fur_tail 6% · fur_ruff 6%.
Side W/H 1.74, hero W/H 1.33. (Fourth pass: the tail's frame is `"up"` so its dark
top and pale underside sit where the arcs say, the hind thigh is deep fore-aft as the
profile intended, and the three tawny bands are feathered at half their width so
they reach their colour. Fifth pass: the head is built for the in-between views —
`taper` on the skull and muzzle rows gives it brow, cheek and jaw planes instead of
an ellipse, the muzzle is boxy (`exp` 3) with a flat bridge, the eyes are hooded
by a `lid`, the ears are cupped (`section.cup` on the curve) and the nose pad is a
boxy `section` — judged on an 8+2 orbit, eight azimuths at 45° plus top and bottom, with
head close-ups at the same eight.)

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
