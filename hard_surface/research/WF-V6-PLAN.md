# WORKFLOW v6 — multi-view, artist-order (Opus 5.5 + Fable 5.1 research merged, 2026-09-26)
Owner: "Bus is a disaster. Truck better, not perfect." Full reports: research/WF-V6-RESEARCH-OPUS.md + the Fable report
summarised below.

## Agreed diagnosis
Single-view fitting is the core mistake: every part keeps one free direction along the camera ray; silhouette FIT,
residuals and "N of M exact" are blind to it, so depth, hidden sides and attached-part placement come from template
defaults / knob bounds (bus: L locked 4.8 m, L/W 2.25 vs real 3.3–5 → stubby van; mirror arm 0.04 m slides onto the stop
arm; bumper low+forward = floating plate). The objective saturates (IoU 0.97–0.99) while the owner says "disaster".
Fable: 15.4 k LOC of harness for 157-line outputs; 86 knobs on the bus (49 machine-made rc_*); "N of M exact" rose 1 → 9
with no visible improvement.

## How artists do it (both reports)
Reference board with orthographic blueprints (front/side/top/rear) + real-object references; blockout from primitives
at real-world scale; check silhouettes from every angle before detail; primary → secondary → tertiary; symmetry;
hidden sides from real references; stylisation = deliberate deviation from real proportions.
Literature: code-geometry works when numbers come from 3D evidence (CAD-Recode, MeshCoder); agent-controlled viewing
is the biggest lever (3DHarnessBench: single image 0.740 → agent camera 0.871 → geometric access 0.927); multi-view
generators hold proportions, drift in details; image-to-3D = strong depth/proportion prior, poor final asset; VLM judge
works pairwise with a reference, order-swapped, ≤ 4 images per call, normal-map montages.

## v6 pipeline
A REFERENCES (tools): generate an orthographic turnaround (front, side, rear, top) from the concept (GPT image
  generation / multi-view model); cross-check shared dimensions with the concept (±3 %, ≤ 2 regenerations); class
  PRIOR CARD (real dimensions: e.g. Type C bus W 2.44 m, H 3.1–3.3 m, L 7.8–12.7 m, wheelbase, wheel D) + a measured
  STYLISATION ratio. Optional: image-to-3D proxy used ONLY as a depth oracle.
B BLOCKOUT (tools fit, LLM never sees numbers): ≤ ~15 body knobs; FIT on all views jointly (each ortho constrains its
  two axes; concept view weighted highest); ranges from the prior card; stop when every view ≥ 0.95 IoU. Visual-hull
  start (intersect extruded side/front/top silhouettes).
C FEATURES (LLM chooses structure): inventory from the concept; READY calls with constants measured on the orthos
  (two-axis measurements, not guesses); PLACEMENT RULES per helper (anchor face, offset range, clearances: mirror
  outboard on its arm, bumper flush on the nose face, stop arm clear of the mirror); no rc_* knob explosion.
D JUDGE: render 4 orthos + 2 three-quarter views (shaded + normal map); deterministic checks (per-view silhouette IoU,
  symmetry, ray-cast float/clip, contact to declared anchor); VLM pairwise A/B vs baseline with the concept as
  reference; view-tagged residual rows to the seat; owner sheet = the same 6 views.
V5 single-view exactness machinery: frozen as an optional concept-side detail pass, not a stop criterion; delete after
the experiment if it adds nothing (Fable: per-feature FIT, per-face palette, ABSORB, noise floor, rc_* knobs).

## Experiment (bus, before any broad rebuild)
A = v56 bus; B = turnaround + prior card + multi-view FIT + placement rules; control = B's FIT with only the concept
view (must reproduce the stubby van). Judge: 6-view sheet, geometric checks, VLM pairwise (order-swapped), owner.
Pass: B wins ≥ 5 of 6 views, no float/clip, concept IoU ≥ 0.96. Fail: the problem is the template/kernel, not the
objective.
