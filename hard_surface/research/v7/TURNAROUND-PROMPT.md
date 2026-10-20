# Turnaround prompt — the template `scripts/v7/turnaround.mjs` fills (Opus 5.5, 2026-09-27)

The sheet prompt is the image-generator A/B's template (research/v7/IMAGEGEN-AB.md; the same text for GPT and Gemini)
plus the projection rules of RUNBOOK §0 and AUDITOR.md task 0, with two additions from the A/B's blind semantic check:
explicit image sides for every asymmetric part (the tractor's exhaust stack went to the wrong flank, the ice-cream van's
awning onto both flanks) and per-view face sentences for the features a face must NOT show (hidden faces). One image,
2 × 2 (side, front, rear, top), the concept as the only reference image. The repair prompt regenerates ONE view from two
references: image 1 = the current view, image 2 = a draft (a mirrored front / rear, or the view re-proportioned to the
measured dimensions).

`turnaround.mjs` reads the fenced `text` blocks under the headings below (the heading names are the keys — do not rename
them) and fills `{placeholders}` from `subjects/<s>/turnaround/facts.json`; a placeholder without a value is an error, and
no `{` survives the fill. `{style}` = the frozen STYLE of `scripts/make-target.mjs` with its isometric sentence replaced by
"True orthographic elevation, no perspective." (never copied here, so it cannot drift). `node scripts/v7/turnaround.mjs
prompt --subject <s> [--view <v> --draft mirror|proportion]` prints the filled text.

## Placeholders

| placeholder | from |
|---|---|
| `{noun}` | facts.json `noun` ("fire truck") |
| `{description}` | facts.json `description`: the concept's parts and colours (concept prompt + a look at the concept) |
| `{proportions}` | facts.json `proportions`: the concept's measured L : W : H, wheel size, wheelbase, heights |
| `{sides}` | facts.json `sides`: which flank every asymmetric part is on (or "symmetric left to right") |
| `{shape.side}` … `{shape.top}` | facts.json `shape.<view>`: that view's aspect ("in this view it is 3.05 times as long as it is wide") |
| `{extra.side}` … `{extra.top}` | generated: facts.json `faces.<view>` + one sentence per `asymmetric` entry naming the IMAGE side it shows on in that view (left flank → front view image RIGHT, rear view image LEFT, top view image BOTTOM; `along` front / rear → top view image LEFT / RIGHT) |
| `{view.side}` … `{view.top}` | the view conventions below, `{noun}` filled |
| `{projection}` | the projection rules below |
| `{style}` | scripts/make-target.mjs STYLE, isometric sentence replaced |
| repair only: `{VIEW}`, `{view}`, `{viewSentence}`, `{shape}`, `{extra}`, `{draft}` | the repaired view, its convention, its facts, the draft sentence below |

## Sheet template

```text
One image: a 2 x 2 orthographic turnaround sheet of the {noun} in the reference image, four views of the same {noun}: top-left the SIDE view, top-right the FRONT view, bottom-left the REAR view, bottom-right the TOP view. All four views at one common scale (the same number of pixels per metre in every view), each centred in its own quarter, separated by wide plain white gutters. No text, no labels, no numbers, no arrows, no dimension lines, no frames or borders.
The reference image is the concept drawing of this {noun}: an isometric view from its front-left, showing its front face and its left flank (the {noun}'s own left side). Keep its design exactly (the same parts, shapes, colours and proportions); only the viewing direction changes.
The {noun}: {description}
Proportions measured on the concept: {proportions}
Left and right: {sides}
The views:
- {view.side}; {shape.side}.{extra.side}
- {view.front}; {shape.front}.{extra.front}
- {view.rear}; {shape.rear}.{extra.rear}
- {view.top}; {shape.top}.{extra.top}
{projection}
{style}
```

## Repair template

```text
One image: the {VIEW} view of the {noun}, a single true orthographic view and the only drawing in the image, centred, on a plain white background. No text, no labels, no numbers, no arrows, no dimension lines, no frames or borders.
Image 1 is the current {VIEW} view of this {noun}. {draft}
The {noun}: {description}
Proportions measured on the concept: {proportions}
Left and right: {sides}
The view: {viewSentence}; {shape}.{extra}
{projection}
{style}
```

## View conventions

```text
side: SIDE view: looking straight at the left flank (the flank the concept shows), the front of the {noun} pointing to the LEFT of the image
front: FRONT view: looking straight at the front face; the {noun}'s left flank is on the RIGHT of the image
rear: REAR view: looking straight at the rear face; the {noun}'s left flank is on the LEFT of the image
top: TOP view: a plan view looking straight down on the {noun}; its front points to the LEFT of the image and its left flank (the flank the concept shows) is at the BOTTOM of the image
```

## Projection rules

The A/B's visibility sentence + the orchestrator's projection rule of 2026-09-27 (RUNBOOK §0), verbatim.

```text
Each feature appears only in the views that can see its face: anything on the rear face (for example rear doors, where the vehicle has them) only in the rear view, anything on the front face only in the front view, anything on the left flank only in the side view. Each view is a true orthographic projection: any part seen along an axis shows its cross-section along that axis, never its length (a ladder lying front-to-back is a thin strip in the front and rear views; an upright cone is a circle in the top view). A vertical part seen from above is its plan (an upright post is a small square). Parts that stick out from a flank (mirrors, awnings, shelves, steps) appear as profiles beyond the body outline in the front, rear and top views. Closed housings are drawn closed.
```

## Draft sentences

`{OTHER}` / `{other}` = the opposite end view (front ↔ rear). Mirror drafts exist only for front / rear.

```text
mirror: Image 2 is a draft made by mirroring the {OTHER} view of the same {noun} left to right: its OUTLINE is the outline this {VIEW} view must have, but its surface details belong to the {other} face. Keep image 1's own {view} face details (the parts and colours of the {view} face) and match image 2's mirrored OUTLINE exactly: the wheel, fender, post, cab and body widths and positions, the overall width and height. Do not copy any {other}-face part into this view.
proportion: Image 2 is a draft: image 1 re-proportioned to the measured dimensions of the concept (only stretched, nothing else changed). Keep image 1's own details and match image 2's overall width, height and part positions.
```

## facts.json (per subject, `subjects/<s>/turnaround/facts.json`)

```json
{
  "subject": "<s>", "noun": "...", "sources": "where each fact comes from",
  "description": "...", "proportions": "...", "sides": "...",
  "shape": { "side": "...", "front": "...", "rear": "...", "top": "..." },
  "faces": { "<view>": "extra sentence(s) for that view: hidden-face rules, known projection traps" },
  "asymmetric": [ { "part": "the striped awning and the counter shelf", "plural": true, "flank": "left | right", "along": "front | middle | rear | null", "protrudes": true } ],
  "dims": { "L": 4.7, "W": 2.0, "H": 4.7, "_": "registration measures: L / W = the body-family span (views.json families.body), H = the foreground bbox height" }
}
```

`dims` feeds the proportion draft only (front / rear: W / H, side: L / H, top: W / L on the registration's own spans);
the prompt's words come from `proportions` / `shape`.
