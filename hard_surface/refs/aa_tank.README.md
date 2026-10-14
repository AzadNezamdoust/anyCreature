# TARGET provenance — aa_tank

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1326717 bytes, sha256 d0b40642b0110b1219aacb660385ec3b88e9a51b714400b9259cb7f010d35c18 (out/concept/aa_tank/raw.png)
- image: refs/aa_tank.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 568141
- sha256: 5e2423b3dbd3b0f03f872458d18b72d0481131d3b62623fab97b968f3216a698
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly tracked anti-aircraft tank parked on the ground, seen from the front-left. A tank hull with a sloped front plate and a flat engine deck at the rear; on top a tall boxy angular turret set in the middle of the hull with one long slim autocannon barrel mounted on each side of the turret, both barrels parallel, raised at about 30 degrees and pointing forward and up; on the turret roof at the rear a flat rectangular radar dish on a short post, facing forward, and a small square tracking radar box on the turret front between the guns. Along each side a track loop over five road wheels with a drive sprocket at the front end and an idler at the rear end, a flat track guard over each track. Hull, turret, track guards and radar post painted one dark grey; both gun barrels, tracks, road wheels, sprocket and idler dark gunmetal; radar dish and tracking box a lighter mid grey. The engine grille on the rear face faces away and is hidden; the right-hand track is hidden behind the hull. About 7.7 m long, 3.4 m wide and 3.4 m tall including the raised barrels and the radar; the tracks, road wheels and both gun barrels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- deviation kept for the owner: six road wheels per side (the prompt says five); the radar dish is a flat slab on a post.
