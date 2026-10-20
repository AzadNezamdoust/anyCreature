# TARGET provenance — forklift

- date: 2026-09-27
- generator: GPT image generation (built-in `image_gen`, model gpt-6-astra session) through Codex CLI
  (`faa963e871dd422c/codex.exe`, codex-cli 0.158.0-alpha.2.1), `codex exec --ephemeral --skip-git-repo-check -s workspace-write -C <scratch>`;
  GPT is used only to generate the image
- raw output: 1448 x 1086 px, 1019253 bytes, sha256 68a09b47a11a7a938e84c9ce585ef5afa30f3c81ce432ef9be13246805ea82bf
- image: refs/forklift.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 674087
- sha256: bff3af5559a3922a59ab9c25c494af424918b838c942b94174c689d34334cacc
- style: frozen STYLE of refs/pickup_truck.README.md (chunky cartoon city-builder asset, front-left orthographic isometric 30 deg / 45 deg, flat cel colours, thin dark outlines, white background, stated real size)

## Full prompt (image prompt; the Codex wrapper only asked to generate it with the built-in tool and save it as forklift.png)

```
A chunky cartoon warehouse forklift parked on the ground, the same city-builder game style as a Simpsons Tapped Out asset, seen from the front-left. At the front a tall upright mast of two vertical rails with cross bars, a carriage plate on the mast and two long flat forks pointing forward at ground level; a compact body behind the mast with a driver seat and a steering wheel, an open overhead guard above the seat made of four thin posts and a slatted roof grid you can see through, a big rounded counterweight block at the rear, two large front wheels under the mast end and two smaller rear wheels under the counterweight. Body, counterweight and overhead guard posts painted a bright yellow, mast, carriage and forks dark charcoal grey, seat black, steering wheel black, hubs light grey, tyres dark charcoal, one small orange beacon on the guard roof. About 3.2 m long including the forks, 1.2 m wide and 2.2 m tall; the wheels clearly visible. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Cartoon low-poly game asset: flat cel shading, one solid colour per surface, no textures, no gradients, thin dark outlines. Every surface is one uniform flat colour edge to edge: no panel lines, no surface detail of any kind beyond the parts described. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No people, no animals, no other vehicles, no props beyond those described, no text, no logos, no lettering. Solid white background, whole object in frame with margin, centred.
```
