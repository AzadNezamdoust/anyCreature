# TARGET provenance — transport_heli

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1158922 bytes, sha256 0919bf271c089e44eba8bc8a684ad3d9b50383c3fe9d67fbd15bf335633f0f8b (out/concept/transport_heli/raw.png)
- image: refs/transport_heli.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 454845
- sha256: d6981235b9acc70d18e2adbf5195594e8e600719d6153f2a61b86a6467d96c97
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly twin-rotor heavy transport helicopter parked on the ground on its wheels, rotors stopped, seen from the front-left. A long boxy fuselage with flat sides and a flat roof, a rounded blunt cockpit nose with a row of flat-panelled cockpit windows at the front, a small square cabin window row along the side; a tall rotor pylon at the front on top of the nose and a taller rotor pylon at the rear end, each carrying a three-blade rotor with long thin flat blades, the two rotors overlapping in the middle. A long fairing along each lower flank; four short landing gear legs, two at the front and two at the rear, each with one small wheel resting on the ground. Fuselage, pylons and fairings painted one olive drab green; cockpit and cabin windows a single flat dark blue-grey; rotor blades and rotor hubs dark gunmetal grey; tyres dark charcoal. The rear loading ramp on the rear face faces away and is hidden; the right-hand landing gear is hidden behind the fuselage. About 30 m long from the front rotor tip to the rear rotor tip, 18.3 m wide across the rotor blades and 5.7 m tall; the four wheels and both rotors clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — REJECTED, regenerated once with the same prompt: the rotor blade tips ran to 16 px / 9 px of the left / right frame edge (1024 px square; no margin: 'whole object in frame with margin'). refs sha256 prefix 3c9fe7e62fccfc53; files kept in the session scratchpad, not in the repo.
- attempt 2 (GPT) — kept (this image): margins 21 px left and right, still tight (the 30 m rotor span fills the frame width); otherwise right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
