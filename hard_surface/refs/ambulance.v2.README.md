# TARGET provenance — ambulance v2 (semantic fix of refs/ambulance.png)

- date: 2026-09-27
- why: the concept drew the rear doors (two windows, two handles, a door frame, seams, a greyer header panel) on the
  NEAR FLANK of the patient box at its rear end; the prompt asked for "two rear doors on its back face", and
  turnaround/rear.png already shows them there (owner / orchestrator semantic check; a blind setup audit confirmed it)
- fix: the near flank from the rear wheel back to the box's rear edge is a plain white wall like the rest of the flank;
  the red stripe continues straight at the same height and thickness to the rear edge; the two red marker lamps stay
- base image: refs/ambulance.png, sha256 ccdf1d63ff9959e5ac258ddcc38b69b78b4ea2508c12f368109b0627e6ff73d7 (unchanged)
- generator: GPT image generation — the Codex CLI's built-in image_gen tool, codex-cli 0.158.0-alpha.2.1
  (`faa963e871dd422c/codex.exe`), `-m gpt-6-astra`, one attempt; GPT only generated the image. Exact command (work dir
  = a scratch folder holding input.png = refs/ambulance.png; stdin = the instruction below, fed and closed):
  `codex exec --ephemeral --skip-git-repo-check -c "mcp_servers={}" -s workspace-write -C <scratch>/gen/amb-concept-1 -m gpt-6-astra -i input.png -o answer.md "Follow the instructions below."`
- raw output: the image_gen file (session 01a0e3bc-6b21-7581-823a-b066fec60dc4), 1254 x 1254 px, sha256
  6bb7c5d7ff7e0548c36c11e2be4ffb212ae6efdbd6a407e54ff8989215b8878e (the Codex agent's own saved copy was resized by
  its script; the raw file was used)
- region (the only px that differ from the base): the near flank's rear panel between the roof outline, the box's rear
  outline and the sill outline, from x 755 (flat flank white, left of the old seam) — polygon (755, roof+0.9) (899,
  roof+0.9) (899, sill-1.4) (766, sill-1.4) (763.5, 621) (757.5, 609.5) (755, 602), roof y = -0.38869 x + 644.69, sill
  y = 621.34 - 0.381 (x - 770.5); bbox x 755-898, y 296-620, 39379 px; the two marker lamps (1967 px) inside it keep
  the base px
- compositing: raw resized to 1024 (lanczos3), registered on the stripe edges and flank left of the region (scale
  0.9982, shift -1.125 / -0.125 px; band mean abs diff 3.20 -> 2.06), per-channel linear colour correction; snapped
  to the flank's cel palette (#eeeeee wall, #d2271f stripe, #1c1c1d outline; 2-colour blends only at edges); the
  outlines' anti-alias ring inside the region re-derived from the base's own anti-alias (moved from the old grey
  header / door white onto the wall white); lamp rings from GPT locally re-registered on each lamp; the rear-edge
  columns x 895-898 across the stripe rows take the base's own white-row / red-row rendering of those columns
- result: the new stripe's edges lie 0.2-0.4 px (top) and <= 1.4 px (bottom, at the rear edge) from the straight
  continuation of the base stripe (thickness 47.2 -> 46.5 px at the rear edge; the base's old strip beside the doors
  sat 4 px below that line)
- checks: foreground mask (views.json fgMax 252, enclosedFg) unchanged (0 px inside and outside the region); camera
  re-solve (`node scripts/solve-camera.mjs ambulance --image refs/ambulance.v2.png --dry --x-edge left --threshold 1`)
  identical to camera.json (theta 23.666, phi 46.215, residual 0.332 px), so camera.json stays
- image: refs/ambulance.v2.png, 1024 x 1024 RGBA, sha256 3adb4fced2f579900002b6f6003e366b4ab8bef3751c5d4b1e5d8c3f07cd971b;
  outside the region byte-identical to refs/ambulance.png (decoded RGBA px)
- subjects/ambulance/subject.json `paths.target` -> refs/ambulance.v2.png

## Instruction (verbatim, the only prompt)

```
Edit the attached image input.png (a 1024 x 1024 cartoon ambulance, orthographic isometric view from the front-left) with your built-in image generation tool, using input.png as the input image to edit. Make exactly ONE change and keep everything else identical.

THE CHANGE: the rear part of the near (visible, left) side wall of the tall white patient box, from just behind the rear wheel back to the box's rear vertical edge (about x 758-900, y 300-620 px in input.png), wrongly shows a pair of double doors: a vertical seam line at the front of that area, a door frame, two pale blue-grey windows, two dark handles, the vertical seam between the two doors, and a slightly greyer header panel above the doors. Rear doors belong on the back face of the box, which this view does not show. Make that whole area a plain, flat white wall exactly like the rest of the box's side wall (the same white): no doors, no windows, no handles, no door frame, no seams, no panel lines, no grey header panel. The broad bright-red horizontal stripe on the box side must continue perfectly straight through that area all the way to the box's rear edge, at exactly the same height, slant and thickness as the stripe on the front part of the box side: one continuous straight band (the short red piece next to the rear edge is part of that same band and must line up with it). Keep the two small red marker lights near the top of that wall exactly where and how they are.

KEEP IDENTICAL: the thin dark outline style, the flat cel colours (white body, bright red, pale blue-grey windows, light grey bumpers and step, dark charcoal tyres, pale grey hubs), every other part of the ambulance (cab, windshield, side window, front door and its handle, mirrors, red light bar, grille, headlights, bumpers, the grey rear step under the box, the wheels, the box roof and all of its outlines, the box's rear edge line, the two red marker lights), the size, position and framing of the ambulance, the white background, and the 1024 x 1024 canvas size. Do not redraw, restyle, move, crop or resize anything else.

Save the edited image as a PNG file named ambulance-edit.png in the current working directory. Do not write any other file.
```
