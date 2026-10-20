# TARGET provenance — combat_bike

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1374 x 1145 px, 1194464 bytes, sha256 3d49411b34f52f77f70e6ed1f2995e093119502e46581cee4bae1b363b9c3ad6 (out/concept/combat_bike/raw.png)
- image: refs/combat_bike.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 801447
- sha256: c4efd38ef40f3e6ae8d6a46b643f48e94d59ecba23273ecb7a5320c0fdc2bb7c
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly military off-road motorbike parked upright on the ground on its two wheels, no rider, seen from the front-left. A slim boxy fuel tank and flat seat on a sturdy tubular frame, a small blocky engine block low in the middle, a tall front fork with wide flat handlebars and a small square headlight on the front of the fork, a short flat front mudguard over the front wheel and a flat rear mudguard, a boxy saddlebag hanging from the left side of the rear seat and an exhaust pipe running along the left side under the seat. Two large chunky knobbly wheels of the same size, front and rear. Fuel tank, mudguards and saddlebag painted one desert tan; frame, fork, handlebars, engine block and exhaust dark gunmetal grey; seat black; tyres dark charcoal, hubs dark grey; headlight lens pale grey. The tail light on the rear face faces away and is hidden; the right-hand side of the bike faces away and is hidden. About 2.2 m long, 0.9 m wide and 1.2 m tall; both wheels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- notes: no stand drawn (the bike stands upright on its wheels); the saddlebag and exhaust are on the visible left side as described.
