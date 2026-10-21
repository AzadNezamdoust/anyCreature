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
