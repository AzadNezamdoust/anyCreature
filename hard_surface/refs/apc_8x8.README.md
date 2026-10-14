# TARGET provenance — apc_8x8

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1282582 bytes, sha256 d611cd236be3d8fbaacec6c944958be58245cab61323146295b4e48d09c9069f (out/concept/apc_8x8/raw.png)
- image: refs/apc_8x8.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 561281
- sha256: bffa3d0d93bb1ac60c5b6f4c46fd3d70a54d509f1525933ba76546c201f865ac
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly eight-wheeled armoured personnel carrier parked on the ground, seen from the front-left. A long tall boxy armoured hull with a steeply sloped angular nose plate, flat vertical side walls angled slightly inward at the top and a flat roof; a small low one-man turret on the roof just behind the nose carrying a short thick autocannon pointing forward; a narrow driver's vision slit block at the front left of the roof. Eight large chunky wheels in four evenly spaced axles along the hull, all the same size, set under slightly flared wheel arches. Hull, wheel arches and turret painted one olive drab green; autocannon barrel dark gunmetal grey; tyres dark charcoal, hubs dark olive; the vision slit a single flat dark grey. The rear troop door ramp on the rear face faces away and is hidden; the right-hand wheels are hidden behind the hull. About 7.8 m long, 2.9 m wide and 2.8 m tall; the eight wheels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- deviation kept for the owner: the turret autocannon is traversed roughly 30 degrees off the nose toward the right (the prompt says forward).
