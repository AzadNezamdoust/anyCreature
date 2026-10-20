# TARGET provenance — rocket_truck

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1270552 bytes, sha256 ec77156545dcc3aa3a1d6cbe1ea63fd0c5e46c23ade48b0bd21211f413328611 (out/concept/rocket_truck/raw.png)
- image: refs/rocket_truck.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 579092
- sha256: c96550114cadfbb5a4683f8f7484f4ba42486110ae236e7579b024c818ecbe08
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly six-wheeled military rocket launcher truck parked on the ground, seen from the front-left. A boxy flat-fronted cab at the front with a flat slatted grille, two square flat headlights and a flat two-pane windscreen; behind the cab a flat chassis bed carrying a big rectangular rocket launcher box on a turntable, the box raised at the front end to about 20 degrees and pointing forward over the cab roof; the front face of the launcher box shows a grid of round tube openings, three rows of six. Six large chunky wheels of the same size: one axle under the cab and two close-set axles under the rear bed. Cab, launcher box and chassis bed sides painted one olive drab green; tube openings, turntable, bumper and grille slats dark gunmetal grey; windscreen and cab side windows a single flat dark blue-grey; tyres dark charcoal, hubs dark olive; headlights pale grey. The rear face of the launcher box and the stabiliser jacks on the rear face face away and are hidden; the right-hand wheels are hidden behind the truck. About 9.0 m long, 2.5 m wide and 3.4 m tall with the launcher raised; the six wheels clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- notes: the launcher box's tube face shows 3 x 6 openings as described; the box is raised at its front end over the cab.
