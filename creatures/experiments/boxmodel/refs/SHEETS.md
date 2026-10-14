# Reference sheets: how they were made, checked and corrected (2026-09-27/28)

Both providers ran on the owner's subscriptions, with no API keys:

- **Gemini:** the Antigravity CLI `agy --print`. Its agent, `gemini-3.8-flash-high`, calls `generate_image`.
- **GPT:** the Codex CLI `codex exec -m gpt-6-astra`, using the model's built-in `image_gen` tool.

The prompt is byte-identical for both, built by `gen_refs.py` from `briefs/`:
one 2 × 2 orthographic sheet (side, front, rear, top). That format was adopted
from the owner's other project, where one sheet beat one image per view for
both generators.

## The pipeline (per provider and creature, attempts in order)

1. **`gen_refs.py`:** generate a sheet. Up to 3 attempts; a fourth only where a
   check was added mid-way (the GPT raven-wyvern).
2. **Direction audit** (`audit.json`, a blind Fable 5.1 reader, plus the
   orchestrator's check for later attempts):
   - which way the head points in the side and top views;
   - whether the front and rear views are straight-on;
   - whether the layout is intact.
3. **`orient.py`** makes two corrections:
   - **Directions:** it flips a side view that faces right, and flips or
     rotates a plan view whose head does not point left. The creatures are
     left-right symmetric, so this changes nothing but the direction.
   - **`--fit`:** it makes the views agree as one orthographic set.
     - The side view is the master.
     - Front and rear are scaled evenly to the side height.
     - The plan view is scaled along each axis to the side length and the
       front width.
     - **Brief length (`--aspect`, since 2026-09-28):** the side and plan
       views are stretched along the body, so the side view has the brief's
       length-to-height ratio. Height is already the master, so the traced
       length now equals the brief's, within 1%. Width is not fitted: brief
       widths are pose extents ("with the feet", "across the arms").
     - The stretch counts toward the 35% limit. Before and after, side views
       at equal height: `lengthfit.jpg`.

   Nothing else is redrawn.
4. **Rejections.** A sheet is rejected when its layout is broken (duplicated
   or missing views), when its front is not straight-on, or when any view
   needs more than 35% correction.
5. **`accept.py`** checks the corrected sheet, and `select_sheets.py` keeps the
   first attempt that passes (`chosen.json`, `fitted_<n>.png`). If no attempt
   passes, the least-bad one is used and recorded.
6. **Previews:** `sheets_gemini.jpg` and `sheets_gpt.jpg`. Each sheet is fitted
   into its tile with its aspect ratio kept. The first preview squeezed GPT's
   3:2 sheets into squares and made them look stretched.

## Results

| | Gemini (agy) | GPT (Codex) |
|---|---|---|
| attempts generated | 19 | 19 |
| broken layout (views duplicated) | 1 | 0 |
| side view facing right (fixed by a flip) | 4 sheets | 0 |
| plan view turned (fixed by a rotation) | 2 sheets | 0 |
| labels or divider lines drawn | most sheets | none |
| **views disagree before the fit** (mean / max correction of the chosen sheets) | **10% / 17%** | **18% / 35%** |
| over the 35% limit on every attempt | none | crab (35, 43, 35%): the least-bad is used |
| time per sheet | about 45 s | about 75 s |

- **Gemini** breaks the prompt's layout and directions more often. Its views
  agree with each other better, once orientation is fixed.
- **GPT** follows the layout and directions exactly. Its views disagree more:
  its plan views are often a different width from its front views.
- The owner saw some GPT images as stretched. Two causes:
  - the preview bug, a 3:2 canvas squeezed into a square;
  - this real disagreement between views.

The fit removes the second before the builders see the sheets.

**The prompt changed once, before the final batch.** After the first wolf
smoke test, Gemini drew three-quarter front and rear views. The prompt gained
"straight-on elevation, left-right symmetric, never a three-quarter view" and
"no lines between the quarters", for both providers alike. The smoke-test
sheets are kept as `smoke_v1.*`.
