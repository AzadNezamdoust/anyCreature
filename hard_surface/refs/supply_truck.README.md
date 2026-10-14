# TARGET provenance — supply_truck

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1309175 bytes, sha256 bbb2b711d4e700d9c5c7250363ea2743e7f154c3cdbfb3d855871c53e99b5ccf (out/concept/supply_truck/raw.png)
- image: refs/supply_truck.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 621236
- sha256: b39b2461116b417b0dc44ee7d989e2b6e1aa0b370a209c83ad390e1851bd23b3
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly six-wheeled military cargo truck parked on the ground, seen from the front-left. A boxy flat-fronted cab at the front with a flat slatted grille, two square flat headlights, a flat two-pane windscreen and a flat roof; behind the cab a long flat cargo bed with low flat side boards, covered by a tall canvas tilt: a boxy cover with a gently rounded top and flat sides stretched over hoops, the hoops showing as slight vertical ridges along the side. Six large chunky wheels of the same size: one axle under the cab and two close-set axles under the rear of the cargo bed. Cab and cargo bed side boards painted one desert tan; canvas cover a slightly darker sand khaki; bumper, grille slats and fuel tank under the cab door dark gunmetal grey; windscreen and cab side windows a single flat dark blue-grey; tyres dark charcoal, hubs dark tan; headlights pale grey. The open rear end of the canvas cover and the tailgate on the rear face face away and are hidden; the right-hand wheels are hidden behind the truck. About 8.0 m long, 2.5 m wide and 3.3 m tall; the six wheels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- notes: side mirrors and a fuel tank under the cab drawn (mirrors not described).
