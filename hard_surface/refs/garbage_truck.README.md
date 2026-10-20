# TARGET provenance — garbage_truck

- date: 2026-09-27
- generator: GPT image generation (built-in `image_gen`, model gpt-6-astra session) through Codex CLI
  (`faa963e871dd422c/codex.exe`, codex-cli 0.158.0-alpha.2.1), `codex exec --ephemeral --skip-git-repo-check -s workspace-write -C <scratch>`;
  GPT is used only to generate the image
- raw output: 1536 x 1024 px, 1275093 bytes, sha256 09766184fdb23e3080f8e92ddc538dad945ac05f47f6394887fbcb3e6e96ff31
- image: refs/garbage_truck.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed
- bytes: 581323
- sha256: 3065d921e3cdca8c99c4cc8f08fde11d0c9b4caa4a16f16bffb0a9ae49d7ed72
- style: frozen STYLE of refs/pickup_truck.README.md (chunky cartoon city-builder asset, front-left orthographic isometric 30 deg / 45 deg, flat cel colours, thin dark outlines, white background, stated real size)

## Full prompt (image prompt; the Codex wrapper only asked to generate it with the built-in tool and save it as garbage_truck.png)

```
A chunky cartoon garbage truck parked on the ground, the same city-builder game style as a Simpsons Tapped Out asset, seen from the front-left. A flat-fronted cab-over cab at the front with a large windshield, one side window per door and a side mirror on each door at window height, a simple grille and two square headlights low on the cab front; behind the cab a tall boxy refuse body with slightly rounded top edges, and at the very rear a rear-loader hopper: a tilted tailgate housing with a wide open loading mouth at the back, a step and grab bar below it. Full-width front bumper, a low side skirt between the wheels, one front axle and one rear axle with large wheels with dark tyres and pale grey hubs. Cab and refuse body painted a medium green, the hopper tailgate a darker green, windows pale blue-grey, bumpers, step and hubs light grey, tyres dark charcoal, headlights pale yellow. About 7.5 m long, 2.5 m wide and 3.4 m tall; the wheels clearly visible below the body. Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Cartoon low-poly game asset: flat cel shading, one solid colour per surface, no textures, no gradients, thin dark outlines. Every surface is one uniform flat colour edge to edge: no panel lines, no surface detail of any kind beyond the parts described. Windows are a single flat colour with no reflections, streaks, highlights or glass shine. No people, no animals, no other vehicles, no props beyond those described, no text, no logos, no lettering. Solid white background, whole object in frame with margin, centred.
```
