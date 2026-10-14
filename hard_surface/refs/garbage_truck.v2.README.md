# TARGET provenance — garbage_truck v2 (semantic fix of refs/garbage_truck.png)

- date: 2026-09-27
- why: the concept drew the rear-loader hopper (the darker-green tailgate) OPEN on its near side: its dark interior
  was seen through a large side opening framed by the tailgate edges, like a dustpan; the prompt asked for "a tilted
  tailgate housing with a wide open loading mouth at the back" — a real rear loader has solid side walls and the mouth
  faces backward (turnaround/rear.png shows it). A blind setup audit confirmed it and added: remove the flank grab bar
  (the rear view has the grab bars at the back corners); keep the grey step
- fix: the tailgate's near side is ONE closed, flat, darker-green side wall filling the same outer outline (same
  silhouette); the grab bar is gone; the step, the refuse body's rear edge line, the tailgate's outer outline and the
  darker underside facet at its bottom-left stay. The front frame strip's edge line (it was the opening's left edge)
  went with the opening, so the closed wall runs from the refuse body's rear edge to the silhouette, and GPT's
  top-face edge line now spans the tailgate's full width (turnaround/side.png keeps its strip edge: see its README)
- base image: refs/garbage_truck.png, sha256 3065d921e3cdca8c99c4cc8f08fde11d0c9b4caa4a16f16bffb0a9ae49d7ed72 (unchanged)
- generator: GPT image generation — the Codex CLI's built-in image_gen tool, codex-cli 0.158.0-alpha.2.1
  (`faa963e871dd422c/codex.exe`), `-m gpt-6-astra`; attempt 1 used (attempt 2, asked to keep the strip edge full
  height, left junction artefacts at the top and bottom of that line). GPT only generated the image. Exact command
  (work dir = a scratch folder holding input.png = refs/garbage_truck.png; stdin = the instruction below):
  `codex exec --ephemeral --skip-git-repo-check -c "mcp_servers={}" -s workspace-write -C <scratch>/gen/gt-concept-1 -m gpt-6-astra -i input.png -o answer.md "Follow the instructions below."`
- raw output: the image_gen file (session 01a0e3bc-6b43-7c81-bcf0-7e04e1e2b05f), 1254 x 1254 px, sha256
  1b4c86e2654b127603dcbd26600704bc51bfccfd2c7f97f54a0c8a5bed4053c4 (the raw file was used, not the agent's resized copy)
- region (the only px that differ from the base): the tailgate's near side — its hopper-green / mouth / grab-bar px
  inside the box x 795-976, y 250-612, holes filled, minus the kept outline cores (dark px within 2 px of the refuse
  body green, the page white or the step grey) and minus the underside facet (#1b4326) with a 3 px margin; bbox x
  795-971, y 256-593, 35341 px
- compositing: raw resized to 1024 (lanczos3), registered on a 40 px band around the region (scale 1.0010, shift
  0.375 / 0.125 px; band mean abs diff 2.61 -> 2.39), per-channel linear colour correction, snapped to the cel
  palette of a 30 px band around the region (#2c5b34 wall, #43863b body, #b4b3b3 / #9b9a9a step, #fefefe page,
  #101e14 outline; 2-colour blends only at edges); the kept outlines' anti-alias ring re-derived from the base's own
- checks: foreground mask (views.json default fgMax 235) unchanged (0 px); camera re-solve (`node
  scripts/solve-camera.mjs garbage_truck --image refs/garbage_truck.v2.png --dry --x-edge left`) identical to
  camera.json (theta 25.021, phi 47.451, residual 0.394 px), so camera.json stays
- image: refs/garbage_truck.v2.png, 1024 x 1024 RGB, sha256 ab5a093e95bf9b4c0c6b1e3033fd8611efd2f51766dadb98a6998f60a297ede0;
  outside the region byte-identical to refs/garbage_truck.png (decoded RGB px)
- subjects/garbage_truck/subject.json `paths.target` -> refs/garbage_truck.v2.png

## Instruction (verbatim, attempt 1 — the one used)

```
Edit the attached image input.png (a 1024 x 1024 cartoon garbage truck, orthographic isometric view from the front-left) with your built-in image generation tool, using input.png as the input image to edit. Make exactly ONE change and keep everything else identical.

THE CHANGE: the rear-loader hopper (the darker-green tilted tailgate housing at the very rear of the truck, right of the medium-green refuse body) is wrongly drawn OPEN on its near (visible, left) side: its dark interior is seen through a large side opening framed by the tailgate's edges (the darkest green area with faint interior lines, about x 830-960, y 300-548 px), like a dustpan. A real rear loader has solid side walls; its loading mouth faces backward, on the back face, which this view does not show. Close it: the tailgate's near side becomes ONE closed, flat side wall in the same darker green as the tailgate frame around the opening, filling exactly the same outer outline. Remove the dark interior, the opening's inner outline, the interior lines, and the light grey grab bar on that side wall, so the whole near side of the tailgate is one plain darker-green panel and nothing of the inside is visible. The tailgate's outer silhouette and outer outline stay exactly the same, and the light grey step below the tailgate stays exactly as it is.

KEEP IDENTICAL: the thin dark outline style, the flat cel colours (medium green cab and refuse body, darker green tailgate, pale blue-grey windows, light grey bumper, side skirt, step and hubs, dark charcoal tyres, pale yellow headlights), every other part of the truck (cab, windshield, side window, mirrors, grille, headlights, bumper, refuse body, side skirt, wheels, the step), the size, position and framing of the truck, the white background, and the 1024 x 1024 canvas size. Do not redraw, restyle, move, crop or resize anything else.

Save the edited image as a PNG file named garbage-edit.png in the current working directory. Do not write any other file.
```
