# TARGET provenance — pistol

- date: 2026-10-04
- generator: GPT image generation through scripts/v7/imagegen.mjs --gen gpt (text to image, no reference; agent gpt-6-astra); GPT / Gemini are used only to generate the image
- raw output: 1312 x 1199 px, 950863 bytes, sha256 20177fa5fc8005379555aa12d8eeca5e3043ec3d9f9d636f209c7f21e249066d (out/concept/pistol/raw.png)
- image: refs/pistol.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 653596
- sha256: 06a00cd48e70bc6259f2db99711dec4e9747eb62ba42fac613162519fdb3d6a1
- style: fps (scripts/v7/styles.json styles.fps.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style fps)

## Full prompt (image prompt, verbatim)

```
A stylised semi-automatic pistol, one game weapon model. A long slab-sided dark gunmetal slide with a flat top, six slanted grip serrations at its rear end on the side, a blocky rear sight and a small blade front sight on top, and the round muzzle of the barrel showing in its front face above a recoil spring plug. Under the slide a matte black polymer frame with a short accessory rail under the muzzle end, a squared trigger guard with a gunmetal trigger inside it, and a thick grip raked backward with a stippled panel on its side and a flared base. The magazine's floor plate closes the bottom of the grip. Safety-orange accents: the magazine's floor plate, the front sight blade, and the round magazine release button on the left flank behind the trigger guard. A small gunmetal slide stop lever and a thumb safety lever on the left flank of the frame. The ejection port is on the right flank and top of the slide, hidden in this view. About 0.21 m long, 0.035 m wide and 0.15 m tall. Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Stylised first-person-shooter weapon model: one single handheld weapon held level in the air, its barrel horizontal, the muzzle end being its front. Chunky, readable low-poly forms with slightly exaggerated proportions, crisp facets and chamfers, flat cel shading, one solid flat colour per surface, thin dark outlines. Dark gunmetal for the metal parts, matte black polymer for the furniture, and the one accent colour described. No textures, no gradients, no wear, no scratches, no decals, no text, no numbers, no logos or markings. Lenses are a single flat colour with no reflections, streaks, highlights or glass shine. No hands, no people, no animals, no stand, no table, no other weapons, no props beyond those described, no ground shadow. Solid white background, whole object in frame with margin, centred.
```
