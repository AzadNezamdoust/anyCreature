# TARGET provenance — light_tank

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1327255 bytes, sha256 1c7deb58396c5d56c7887c95cb2851dbf3f3d48b4103801179212caed2c15169 (out/concept/light_tank/raw.png)
- image: refs/light_tank.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 582927
- sha256: 649392a914820e87ae5028a2c57ed7defec2e9500853e47bf6f0e68f02898f29
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly light tank parked on the ground, seen from the front-left. A short compact boxy hull with a steep sloped front plate and a flat rear engine deck; a small rounded angular turret set a little forward of the middle with a medium-length gun barrel pointing straight forward past the nose and a small square hatch on the turret roof. Along each side a track loop over four road wheels with a drive sprocket at the front end and an idler at the rear end, no side skirts, a thin flat track guard over each track. Hull, turret, hatch and track guards painted one desert tan; gun barrel, tracks, road wheels, sprocket and idler dark gunmetal grey; two small flat headlight blocks on the front plate pale tan. The engine grille on the rear face faces away and is hidden; the right-hand track is hidden behind the hull. About 6.5 m long including the gun, 2.9 m wide and 2.3 m tall; the tracks and road wheels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- deviation kept for the owner: five road wheels per side (the prompt says four).
