# LLM CAD app — learnings (2026-10-21)

## Why we build our own
- Plasticity 26.2.1 (Windows, MSI install): no scripting API. The MIT
  plasticity-mcp (Mesteriis) drives it over Electron remote debugging, but the
  Windows build strips `--remote-debugging-port` and has the RunAsNode /
  NodeOptions / inspect fuses off. Only way in = patching the signed exe ->
  EULA breach. Rejected (Azad: "no, illegal"). Notes:
  plasticity_mcp_windows_blocked.md.
- Plasticity Blender bridge (ws://localhost:8980) is read-only mesh streaming
  (protocol verified in plasticity_spec.md) - no modelling commands.
- Plasticity has no editable history: our script-based model beats it there.

## Stack chosen (opensource_cad_survey.md, LLM_CAD_PLAN.md)
- build123d 0.13 on OCP/OpenCASCADE 8.0.1 (Apache + LGPL w/ exception ->
  closed product OK if dynamically linked). Manifold 3.5.4 fallback booleans.
- Blender 5.2 headless as external process for game meshing (sharp edges/UV
  seams from B-rep faces, LODs, glTF), bakes, renders.
- Own stdio MCP (mcp 2.x `MCPServer`): run_model, get_state, render, measure,
  export.

## What LLMs need from a CAD API (CAD-Recode, CADPrompt/CADCodeVerify)
- Whole model = one re-runnable script (undo/history free).
- Semantic refs (selectors, tags), never indices.
- JSON state query; errors that suggest the fix (max fillet radius).
- Render + measure after every step. Gains from verify loops are real but
  modest (~+5% success), so the kit must make failures rare by design.

## Phase 1 pilot results (rifle, turret, tenement)
- 2-4 rounds, ~3-4 min each, 1.1k-4.8k tris.
- Fillets 20 calls / 1 auto-reduced / 0 failed; booleans 57 / 0 failed.
- Bug found+fixed: boolean with a list of tools always failed.
- Owner verdict: promising but reads as polygonal box-modelling, not CAD.
  -> difficulty ladder L1-L5 (bracket, mouse/controller, drill/headphones,
  helmet/nozzle, sports car) with smooth tessellation + zebra renders.

## EULA (2026-10-21, docs/plasticity_eula_summary.md)
RE / source access / derivative works / circumvention banned (EULA 3.2-3.3).
Trial = evaluation only, commercial use prohibited. Output belongs to user.
Clean-room from public docs is our path; no hands-on trial mining for product.

## Robustness + surfacing pass (2026-10-22)
- Crash isolation must be process-level: OCCT segfaults (loft cap fillets) can't be caught in Python. MCP tools now
  run in a persistent worker; journal on disk (atomic write after success) is the source of truth; restart = replay.
  On Windows ctypes turns a null read into OSError, so the crash test uses faulthandler._sigsegv() and os.abort().
- OCP 8 binding moves: Array2 types live in OCP.collections (Array2_gp_Pnt); BRep_Tool.Curve_s returns only the
  curve (params via BRepAdaptor_Curve); build123d 0.13 has no Solid.make_solid (use BRepBuilderAPI_MakeSolid +
  ShapeFix_Solid).
- Shell openings after "offset + cut": punch with the INNER solid's matching face pushed out, not the outer face
  (outer face cutter eats the side walls).
- Loft cap rims: detect (closed edge of a one-edge planar face beside a B-spline face) and never call the OCCT
  fillet; trim r off and loft a quarter-round of inset sections instead.
- Fillet sets: per-edge staged radius ladder on the evolving body beats set-wide bisection.
- Multi-rail loft without a native OCCT op: blend neighbouring profiles, frame-fit contact points onto each rail
  (similarity for 2 rails, LSQ in-plane scale for 3+), loft the fitted stations.
- G2 bridge: quintic Bezier, P2 = 2P1 - P0 + kappa*N*(n d)^2/(n(n-1)) gives exact end curvature.
