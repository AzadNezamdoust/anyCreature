# hard_surface/cad — resume here

State 2026-10-21:
- Phase 1 kit + MCP done (README.md, cadkit/, mcp_server.py, pilot/). Owner:
  "promising but looks polygonal" -> ladder L1-L5 in progress (ladder/,
  render_hq.py, kit fixes in ops.py/worker.py).
- Clean-room Plasticity-style toolset in progress: cadkit/tools/ + mcp_tools.py,
  spec = docs/plasticity_spec.md only (never Plasticity binaries/code).
- EULA: docs/plasticity_eula_summary.md — no RE/decompile; trial = evaluation
  only, no commercial use; hands-on trial testing for a commercial product is a
  grey area -> public docs only, or buy licence / ask vendor first.
- Learnings: docs/LEARNINGS.md.

Next after the two lanes report: review ladder summary (ladder_summary.jpg) +
toolset coverage table; blind Opus judge; Phase 2 hardening (LLM_CAD_PLAN.md).

## 2026-10-22 pause
- Kernel blockers fixed (d732880), fast Python loop (f85ad29), C++/GPU engine Phase 1 (this commit):
  cadengine.exe (OCCT 8.0.1 conda-forge SDK at E:\gen3d\occt), JSON-lines stdio, op cache,
  isolated risky ops, GL 4.5 sheets/IoU/deviation; 57/57 equivalence vs Python kit on 9 journals;
  cold start 41 ms, sheet 17 ms, IoU 0.14 ms. CADKIT_BACKEND=cpp.
- TODO next: independent Opus review of engine diff; port remaining ops (variable/refillet,
  push_pull, symmetrize, surfacing, queries); mcp_server.py still imports build123d at start;
  measure on a real 2070M; then ONE product (G502 or DCD777) to 7/10 via the composite gate.
- Python replicas L3/L4 now fail under the stricter kit (impossible radii no longer shrink
  silently) — expected; rebuild them through the gate.
