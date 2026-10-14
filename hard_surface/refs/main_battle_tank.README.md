# TARGET provenance — main_battle_tank

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1266992 bytes, sha256 8146235d6383f1150c35827654d5748fc0e0dcf63eb17d72d2b0c4f8d2bfce88 (out/concept/main_battle_tank/raw.png)
- image: refs/main_battle_tank.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 533125
- sha256: 4d9a1dde219003fdc06244e112d5d34747723d66e22c61041bb65ce3f87c8d28
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly main battle tank parked on the ground, seen from the front-left. A long low angular hull with a sloped front glacis plate, a flat track guard shelf over each track and a flat engine deck at the rear; a wide flat-sided angular turret sitting slightly behind the middle of the hull with a sloped front face, a long thick main gun barrel pointing straight forward over the nose with a short fume-extractor bulge halfway along it, a small commander's hatch cupola on the turret roof and a short machine gun beside it. Along each side a full-length track loop running over six large road wheels, a drive sprocket at the rear end and an idler wheel at the front end; a flat side skirt panel covering the upper half of the road wheels. Hull, turret, track guards and side skirts painted one olive drab green; gun barrel, machine gun, tracks, road wheels, sprockets and idlers dark gunmetal grey; hatch cupola olive drab. The engine exhaust grille on the rear face and the stowage basket on the back of the turret face away and are hidden; the right-hand track is hidden behind the hull. About 9.5 m long including the gun, 3.6 m wide and 2.5 m tall; the tracks and road wheels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- deviation kept for the owner: seven road wheels per side (the prompt says six); the side skirt reads as a track guard shelf.
