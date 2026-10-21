# LLM-first hard-surface CAD — plan (2026-10-21)

Why: Plasticity 26.2.1 has no scripting API and blocks remote debugging on
Windows (Electron fuses off). Patching it is off the table (EULA). Build our own
LLM-drivable tool from open parts instead.

Inputs: `plasticity_spec.md` (what to match; items tagged (pub) unverified),
`opensource_cad_survey.md` (what to build on), existing `WORKFLOW-V10.md`
(Blender build.py + render-compare loop that already ships vehicles/guns).

## Stack (survey rank 2, growing into rank 1)

- Kernel: OpenCASCADE via build123d (Apache) / OCP. B-rep solids, booleans,
  fillets/chamfers, shell, loft/sweep/revolve, STEP. LGPL kernel linked
  dynamically = closed product OK.
- Fallback booleans: Manifold (Apache) on meshes when OCCT fails.
- Game end: Blender 5.2 headless as an external process (no GPL linking):
  tessellate, sharp edges / UV seams from B-rep face IDs, UVs, bakes, LODs,
  glTF/FBX, renders. Reuses WF v10 tooling (scripts/hs, rig_pass).
- MCP: own stdio server (start from MIT build123d-mcp / @casys/mcp-build123d).

## LLM-ideal design rules (CAD-Recode, CADPrompt, Text2CAD evidence)

1. Whole model = one re-runnable Python script (build123d). Undo = re-run.
   Beats Plasticity: real history.
2. Each op is pure `{op, refs, params} -> revision`; journal is a replayable tree.
3. Refs are semantic queries (selectors/tags: `edges().filter_by(Axis.Z).group_by(...)[-1]`,
   named faces), re-resolved on replay — never raw indices.
4. State queryable as JSON: bodies, volumes, bbox, face/edge counts, tagged
   features, manifold/validity flags.
5. Errors say what to try next (fillet radius too big for edge X -> max ~r;
   boolean failed -> retry with fuzzy tol / Manifold fallback).
6. Verify every step: render 6 views + measure against the spec table
   (render.py-style contact sheet, census asserts).

## Must-have ops (from spec, ranked for game hard-surface)

booleans; fillet/chamfer (variable) with retry; push/pull extrude; game meshing
(face IDs -> sharp edges/seams, LODs, tri budget); curves/imprint/split;
mirror/arrays/instances; shell/thicken; stable refs; loft/sweep/revolve;
deform/bend; editable history; glTF/FBX export.

## Human UI (later)

Plasticity's speed comes from keymap + gizmo-per-parameter + typed values.
Phase 3: thin viewport (Blender add-on or web OCCT viewer) that edits the same
script, so human and LLM share one source of truth.

## Phases

1. Prototype (S-M): build123d + MCP (exec, render, measure, export) + Blender
   meshing step; rebuild 3 WF v10 assets (rifle, vehicle part, prop); blind
   Opus judge vs current Blender-bpy builds; measure fillet failure rate.
2. Hardening (M): fillet/boolean retry layer, semantic ref helpers, JSON state,
   error hints, LOD + bake chain, RTX 2070M-friendly defaults.
3. UI (L): keyboard viewport sharing the script.

Open checks before Phase 1: verify (pub) items in plasticity_spec.md against
doc.plasticity.xyz + plasticity-blender-addon; verify licences/activity in the
survey (thin web pass).
