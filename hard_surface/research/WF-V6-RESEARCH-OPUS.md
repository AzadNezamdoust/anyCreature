# How low-poly hard-surface is really modelled, and what works with LLMs — Opus 5.5 research (2026-09-26)
Owner: "Bus is a disaster. Truck much better but not perfect. Research how humans model low-poly hard-surface/props
and the best ways that work with LLMs. Tool-agnostic."

Root cause (diagnosed on out/v56/loop-school_bus/build/module.mjs): ONE VIEW LEAVES ONE FREE DIRECTION PER PART
(the camera ray ≈ (0.62, 0.48, 0.62)); silhouette FIT, residuals and "N of M exact" are blind to it; contact gates only
ask "touches something". Mirrors: arm 0.04 m → head hugs the flank, slides back along the ray onto the stop arm. Stop
arm rc_stop1 pinned at its range bound. Bumper: thin plate low + forward (lower ≡ forward in this view). Stubby van: L
locked 4.8 m, L/W 2.25 (real Type C bus ≈ 4:1 at W 2.44 m); nothing decides stylisation vs foreshortening; capR 0.5
rounds the flat bus front into a van nose; hidden sides from template defaults. V5 "100 % exact" was defined on the
single view that cannot see these failures.

Artists: reference board with front/side/top/rear blueprints as locked planes; blockout from primitives checked from
every angle; primary → secondary → tertiary; proportions from real-world dimensions; with one concept they get a
turnaround or make a throwaway blockout and paint over / render orthos; hidden sides from real references. No artist
commits part positions from one view.
LLM evidence: code-as-geometry (LL3M, BlenderRAG, 3DCodeBench: spatial placement is the main failure); visual feedback
helps structure modestly (CADCodeVerify ~7 %); accuracy jumps with 3D evidence (CAD-Recode, MeshCoder, MeshLLM) → LLM
chooses structure, numbers from 3D evidence; multi-view generation (Zero123++, MV-Adapter orthographic, Drive-1-to-3)
holds silhouettes/proportions, drifts in details; image-to-3D (Hunyuan3D, TRELLIS, Rodin, Tripo) = strong proportion/
depth prior, poor final asset.

Keep: manifold kernel, KNOBS+FIT, short structural LLM loop, K.assemble library, validators, solved camera, inventory,
feature measurement (concept view). Replace/add: multi-view objective, free-direction accounting, placement rules for
attached parts, class dimension prior + explicit stylisation knob, multi-view verification incl. behind/below; retire
single-view "N of M exact" as the stop criterion.
Pipeline (ranked value/effort): P3 placement rules + class proportion priors with a stylisation knob (nearly free) ·
P4 6-view verification gate (geometric checks + VLM check questions) · P1 generate orthographic turnaround from the
concept, cross-check shared dimensions, FIT on 4 views (concept weighted highest) + visual-hull blockout
(K.intersect of extruded side/front/top silhouettes) · P2 image-to-3D proxy as a depth oracle only (ray-cast free
directions), never shipped · P5 keep single-view exactness as the concept-side detail pass.
Experiment on the bus: A current v56; B + 3 generated orthos (±3 % agreement, ≤ 2 regenerations) + P3 + 4-view FIT;
C = B + image-to-3D proxy. Pass: concept IoU ≥ 0.96, P4 checks pass for B / fail for A, held-out view IoU ≥ A + 0.05,
owner blind A/B/C pick on a 6-view sheet.
Sources: see the agent report (LL3M 2508.08228, BlenderRAG 2605.00632, 3DCodeBench 2606.01057, CADCodeVerify 2410.05340,
CAD-Recode 2412.14042, MeshCoder 2508.14879, MeshLLM 2508.01242, Zero123++ 2310.15110, MV-Adapter 2412.03632,
Drive-1-to-3 2412.14494, Hunyuan3D-2, polycount/Sunstrike/Propgon workflow threads, Blue Bird Vision dimensions).
