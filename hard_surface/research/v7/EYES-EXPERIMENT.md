# v7 eyes experiment — concept perspective and white parts (Opus 5.5, 2026-09-27)

Evidence: scratchpad eyes-exp/ (A/*.json, A/control-*.json, B/*.json, gate.json; edge and mask PNGs). Gate: the
experiment's raster matched project.mjs frame "target" pixel for pixel on all 5 subjects and the judge's sigma / ortho IoU
to 4 dp; its pinhole camera matched THREE.PerspectiveCamera to 5e-13 px. Positive control: gold models rendered through a
known pinhole camera (D/L 5–10) — the fitter recovered D/L exactly and perspective beat ortho by +0.017..+0.035 IoU.

## A — perspective in the concept drawings: DO NOT ADOPT
| subject | concept IoU pipeline | best ortho (6-DOF) | best perspective | fitted D/L | verticals (plumb = 90°) |
|---|---|---|---|---|---|
| taxi | .9397 | .9405 | .9405 | ∞ | not traced |
| bus | .9611 | .9690 | .9699 | 20 (3.0°) | 89.99° |
| pickup | .9845 | .9882 | .9882 | ∞ | 89.76° (short line) |
| truck | .9610 | .9625 | .9626 | ∞ | 90.00°, 89.99° |
| tractor | .8479 | .8575 | .8684 | 7 (model errors, not camera) | 90.00°, 89.99° |
The GPT concepts are orthographic: vertical strokes plumb within 0.01°, parallel edges at the front and rear at equal
height do not converge (3 of 5 lean the wrong way for perspective). What the modellers saw is LOCAL DRAWING DISTORTION:
on the taxi and bus the nose's horizontal edges fan 1.2–3.0° with height while the roof's front and rear edges stay
parallel (no camera does that). Rule: keep the orthographic concept camera; measurements inside a distorted region of the
concept (so far: the taxi and bus nose) become `drift:` lines and the orthographic turnaround decides there. Freeing the
ortho angles gains +0.001..+0.010 only by rolling the camera against plumb strokes (it compensates model errors) — keep
camera.json.

## B — white parts in the reference masks: ADOPT as a per-subject opt-in (default off)
Background = the near-white region connected to the image border (flood fill, 4-connected, min channel ≥ fgMax);
enclosed near-white regions become foreground. Old → new gold IoU at the judge's registration:
| subject | side | front | rear | top | concept | became foreground |
|---|---|---|---|---|---|---|
| taxi | .965→.972 | .866→.937 | .877→.929 | .862→.878 | .940→.971 | roof sign, headlights (right) |
| truck | .964→.971 | .929→.943 | .855→.868 | .964→.970 | .961→.963 | 1–2 px seams inside the white body (right) |
| bus | .967→.968 | .970→.964 | .943→.939 | = | .961→.963 | stop-sign rim (right); mirror-bracket loops (wrong: see-through) |
| pickup | = | = | = | = | = | nothing |
| tractor | .930→.812 | .839→.787 | .790→.749 | = | .848→.856 | canopy openings, ladder gaps (wrong: see-through) |
No leaks (closing ≤ 2 px outline gaps adds ≤ 56 px per view). No colour rule can separate a white part from a see-through
hole (both are page white), so it is opt-in per subject (+ optional hole seeds later). On for taxi and delivery_truck;
off for tractor, bus (keeps the bus reproduction), pickup (no effect), buildings (untested). Pre-existing bug found:
scripts/residuals.mjs targetFamilies calls targetState at the default 235 even for the truck (fgMax 252), so the FIT's
concept target erases the white body.
