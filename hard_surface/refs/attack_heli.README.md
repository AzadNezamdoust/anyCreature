# TARGET provenance — attack_heli

- date: 2026-09-28
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1536 x 1024 px, 1264137 bytes, sha256 edcb16bc6b0cfabe52c28160a43cb22df54c38aa941aecb061c9b10defb37707 (out/concept/attack_heli/raw.png)
- image: refs/attack_heli.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 517273
- sha256: 05f041c389e7f913330336359a9882b7a13d085b33d8575a97564b907ebc6f4a
- style: generals (scripts/v7/styles.json styles.generals.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style generals)

## Full prompt (image prompt, verbatim)

```
A chunky low-poly attack helicopter parked on the ground on its landing skids, rotors stopped, seen from the front-left. A slim angular fuselage with a narrow pointed nose; a tandem cockpit of two stepped flat-panelled canopies one behind the other, the rear seat higher than the front; a small chin turret under the nose with a short gun barrel pointing forward; a short stub wing on each side of the fuselage behind the cockpit, each wing carrying one fat cylindrical rocket pod under its tip; two boxy engine pods on the fuselage top above the wings; a long thin tail boom ending in an upright tail fin with a small two-blade tail rotor on its left side and a small flat horizontal stabiliser. A short rotor mast on top carrying a four-blade main rotor with long thin flat blades in an X shape. Two tubular landing skids under the fuselage, each a straight runner on two struts, both skid runners resting flat on the ground. Fuselage, tail boom, fin, stub wings and engine pods painted one dark olive green; canopy panels a single flat dark blue-grey; rotor blades, rotor mast, chin gun, rocket pods and skids dark gunmetal grey. The exhaust outlets on the rear face of the engine pods face away and are hidden; the right stub wing and its rocket pod are partly hidden behind the fuselage. About 15.5 m long from the nose to the tail rotor, 14.6 m wide across the main rotor blades and 4.6 m tall; the skids, stub wings, rocket pods and both rotors clearly visible. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Classic early-2000s real-time-strategy game unit look: chunky, slightly exaggerated proportions, visibly faceted low-poly shapes, flat cel shading, one solid flat colour per surface, thin dark outlines. Military paint in the single colour scheme described (olive drab, desert tan or dark grey), dark gunmetal for weapons and tracks. No textures, no gradients, no camouflage patterns, no decals, no panel lines, no text, no numbers, no insignia or markings. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No crew, no people, no animals, no other vehicles, no props beyond those described, no terrain, no ground shadow. Solid white background, whole object in frame with margin, centred.
```

## Attempts (gold.mjs new --style generals --gen gpt; checked by eye against the prompt, 2026-09-29)

- attempt 1 (GPT) — kept: right view (orthographic front-left isometric), no text / numbers / insignia, no crew, no hidden-face feature on a visible face, whole object in frame.
- notes: both skid runners, both stub-wing rocket pods, the tail rotor on the fin's left face visible.
