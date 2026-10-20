# TARGET provenance — jeep_gun

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1330605 bytes, sha256 0f91cd3e44d48c3cc4a7f217619ab388a6bea71e68560ee6996a2d88b78f372d (out/concept/jeep_gun/raw.png)
- image: refs/jeep_gun.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 622624
- sha256: 290efee01ed3876474bcb6d9660de52c69bb2b56ac3339e5417a5a5608ce4afd
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly four-by-four light military utility vehicle parked on the ground, no crew, seen from the front-left. A wide low boxy angular body with a flat bonnet, a flat vertical grille with a wide slatted front, square flat headlights at the corners, a short upright windscreen of two flat panes, four doors with small square flat windows and a flat hard roof; a round ring mount on the middle of the roof carrying a heavy machine gun on a short post with a small flat gun shield in front of it, the gun pointing forward. Four large chunky wheels of the same size on two axles under wide flared wheel arches. Body, doors, roof and wheel arches painted one desert tan; grille slats, bumper, gun, gun mount and gun shield dark gunmetal grey; windows a single flat dark blue-grey; tyres dark charcoal, hubs dark tan; headlights pale grey. The spare wheel on the rear face faces away and is hidden; the right-hand wheels are hidden behind the body. About 4.6 m long, 2.2 m wide and 2.6 m tall including the roof gun; the four wheels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
