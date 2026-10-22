# Plasticity parity matrix (clean-room)

Source of "what Plasticity does": docs/plasticity_spec.md ONLY (public material). No Plasticity binaries/code.
Target: the modelling CAPABILITY, exposed so an LLM can drive it from text. Not a UI clone.
Status: **W** works (tested, product-usable) / **P** partial (works with limits, see note) / **M** missing.
Before = state at commit 3106957; After = this pass (2026-10-22). Tests = tests/test_tools_<file>.py::test.

## Summary

| | works | partial | missing | total |
|---|---|---|---|---|
| before | 61 | 20 | 70 | 151 |
| after  | 75 | 20 | 56 | 151 |

New this pass: push_pull (face move + auto re-fillet), boolean_fillet, symmetrize, curve_network,
offset_curve_on_face, draft_face, and read-only queries measure / curvature / draft_analysis / deviation /
compare_to_ref / suggest_refs / explain_failure, per-op state diff, per-op worked examples.

## 1. Interaction semantics -> deterministic ops (what matters for an LLM)

| Plasticity concept (spec 2) | What it does conceptually | How we expose it |
|---|---|---|
| Modal tool + gizmo drag + typed value | every parameter is a handle; you type the number | every op = `{op, params}` JSON with explicit numbers (metres/deg). No modal state. |
| "Hot" last command, Space repeat, re-open to adjust | tweak the last op before moving on | journal tree: `cad_set_param(node, key, value)` re-edits ANY past op and replays (more than Plasticity: full history). `cad_undo/redo/checkout` = branches. |
| Contextual verbs (region->extrude, face->offset, edge->fillet) | op chosen by selection type | explicit op names; refs say the entity kind (`faces`/`edges`). |
| Select-then-command / command-then-pick | clicks on screen | **ref specs** (semantic queries: normal, geom, pick extreme, near, within, loop, tangent_chain, tag), re-resolved every replay. `cad_suggest_refs(obj, near)` lists entities near a point with VERIFIED unique ref specs (`stable_refs` + `near_ref`). |
| Push/pull a face on a filleted body, blends rebuild (2.5) | Parasolid rebuilds blends live | `push_pull`: detect blends (cyl/torus/sphere r<=max_radius) -> delete+heal -> offset faces -> re-fillet healed edges at their old radii. |
| Fillet-on-edit / refillet | change radius after the fact | `refillet`, `remove_fillets`, or `cad_set_param` on the original fillet node (history replay). |
| Regions from overlapping curves (no solver) | any closed curves -> arrangement of faces | `regions(curves)` = BOP general fuse of the planar faces -> every fragment a region (overlaps split, nesting -> holes). |
| Cplanes / sketch on face | ortho views set plane; plane from face | `cplane(face=ref | points | origin+normal, offset)`; every curve/prim op takes `plane=` (cplane name or {origin,normal}). |
| Snaps (end/mid/center/on-edge/normal...) | points land on exact geometry | no cursor: give exact coordinates. Read them with `cad_select` (centres/normals/lengths), `cad_measure` (closest points), `cad_suggest_refs`. P: no "midpoint of edge X" ref token yet. |
| Auto-boolean while extruding | extrude adds/cuts on touch | `mode=new|union|cut|intersect` + `target` on extrude/revolve/sweep/loft/pipe/rail_loft. |
| Mirror with auto-union, symmetric modelling | edit one half | `mirror(union=true)`; `symmetrize(body, plane, keep)` re-establishes exact symmetry after any edit (half-model workflow). |
| Live preview / visual check | the artist looks | `cad_render` (sheet.png), `cad_compare_to_ref` (silhouette IoU vs a reference image, absolute scale or shape-only), `cad_deviation` (vs a mesh/body). |
| Error = op silently fails, try again | artist fiddles | `ToolError` with hint + `data.max_feasible`; `cad_explain_failure(op, params)` dry-runs and diagnoses (missing/unknown params, ref counts, shortest neighbour edge, overlap, profile closed). Crashes isolated (sandbox worker). |
| Seeing what changed | viewport | every op result has `diff`: added objects, removed, and only the changed fields (volume/faces/edges/bbox with delta). |

## 2. Command matrix

### Primitives
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Box | box | W | W | prims::test_box_cyl_cone_sphere_torus |
| Sphere | sphere | W | W | same |
| Cylinder | cylinder | W | W | same |
| Cone | cone | W | W | same |
| Torus | torus | W | W | same |
| Rectangle (corner/center, corner radius) | rectangle | W | W | curves::test_rect_polygon_circle_closed |
| Polygon | polygon | W | W | same |
| Slot | - | M | M | do with rectangle corner_radius=h/2 |
| Text -> curves | - | M | M | |

### Curves create
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Polyline | line | W | W | curves::test_line_arc_spline_lengths |
| NURBS/interp curve (+tangents) | spline | W | W | same |
| Circle center | circle | W | W | curves::test_rect_polygon_circle_closed |
| Circle 2-pt / 3-pt / tangent | - | P | P | 3-pt via arc pieces; tangent circle missing |
| Arc 3-pt | arc | W | W | |
| Arc center / tangent arc | - | P | P | tangent continuation via bridge_curve |
| Ellipse | - | M | M | |
| Helix / spiral | helix | W | W | surfacing::test_curve_trim_join_helix (no taper) |

### Curves edit
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Trim | trim_curve | P | P | param range only, no trim-at-intersection fragment pick |
| Join | join_curves | W | W | surfacing::test_curve_trim_join_helix |
| Unjoin | - | M | M | |
| Fillet curve vertex | fillet_curve | W | W | curves::test_offset_and_fillet_curve |
| Chamfer curve vertex | - | M | M | |
| Offset planar curve | offset_curve | W | W | curves::test_offset_and_fillet_curve |
| **Offset curve on surface** | offset_curve_on_face | M | W | parity::test_offset_curve_on_face_plane_and_cylinder |
| Bridge curves G1/G2 | bridge_curve | W | W | surfacing::test_bridge_curve_g2 |
| Extend endpoints | - | M | M | |
| Split segment | trim_curve | P | P | |
| Insert knot / raise degree / rebuild / subdivide | - | M | M | (4 rows) |
| Planarize | - | M | M | |
| Reverse | - | M | M | |
| Project curve onto body | project_curve | W | W | curves::test_project_curve |
| Project curve onto curve | - | M | M | |
| Body outline / silhouette curves | - | M | M | |
| Body-body intersection curve | - | M | M | used internally by boolean_fillet, no op yet |
| Extract edges as curves | - | M | M | |
| Isoparam curves | - | M | M | |
| Control-point move/scale/slide/delete | - | M | M | edit spline points + cad_set_param instead |
| Import SVG/DXF | - | M | M | |

(the "insert knot / raise / rebuild / subdivide" row counts as 4.)

### Regions
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Regions auto from overlapping closed curves | regions | W | W | curves::test_regions_overlap_and_nested |
| Boolean regions | regions + pick | P | P | union/diff by choosing fragments; no op |
| Offset region | offset_curve | P | P | via outline curve |
| Patch region -> sheet / extrude region | prism, extrude | W | W | prims::test_prism_from_region |
| Curves from regions | - | M | M | |

### Shape from profile / surfaces
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Extrude (2 sides, draft, thin, op type) | extrude | W | W | solids::test_extrude_both_sides_draft_thin, test_extrude_modes |
| Revolve | revolve | W | W | solids::test_revolve |
| Sweep | sweep | P | P | no twist/scale law |
| Loft (+guide) | loft | W | W | solids::test_loft_plain_and_guided |
| Multi-rail loft | rail_loft | W | W | surfacing::test_rail_loft_two_and_three_rails |
| Pipe | pipe | W | W | solids::test_sweep_and_pipe |
| Rib | - | M | M | |
| Bridge / blend surface G1/G2 | blend_surface | W | W | surfacing::test_blend_surface_tangent |
| Constrained / N-sided patch | patch, coons_patch | P | P | GeomPlate approximation |
| **Curve-network surface** | curve_network | M | P | parity::test_curve_network_follows_interior (GeomPlate free constraints, not exact Gordon) |
| Sew sheets -> solid | sew | W | W | surfacing::test_sew_sheets_to_solid |
| Cap sheet holes | patch | P | P | |
| Reverse / extend / insert sheet | - | M | M | (3 rows) |

### Booleans / cutting
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Union / difference / intersect, keepTools | boolean | W | W | booleans::test_boolean, test_boolean_multi_tool_coplanar |
| **Boolean with fillet propagation** (round the seam) | boolean_fillet | M | W | parity::test_boolean_fillet_rounds_seam |
| Auto-boolean while extruding | mode/target | W | W | solids::test_extrude_modes |
| Auto-boolean while moving | - | M | M | move then boolean |
| Cut/split by plane | split | W | W | split::test_split_plane_both_and_keep |
| Cut/split by curve | split(curve) | W | W | split::test_split_by_curve |
| Cut/split by face/sheet | - | M | M | |
| Imprint curves | imprint | W | W | split::test_imprint_keeps_volume |
| Imprint bodies | - | M | M | |

### Fillet / chamfer
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Constant fillet (+auto-reduce, staged) | fillet | W | W | fillet::test_constant_fillet_and_chamfer, surfacing::test_staged_fillet_keeps_good_radius |
| Variable radius | variable_fillet | P | P | fillet::test_variable_fillet; OCCT law, fails at complex corners |
| Conic / curvature-continuous (G2) | fillet shape=smooth | P | P | polynomial ~G2 approx; true conic profile M (OCCT has none) |
| Chamfer 1 dist / 2 dist / dist+angle | chamfer | W | W | fillet::test_chamfer_two_dist_angle |
| Face-face fillet | - | M | M | |
| Refillet | refillet | P | P | direct::test_remove_fillets_and_refillet (bbox heuristic) |
| Remove fillets | remove_fillets | W | W | same |
| Tangent-chain fillet | fillet tangent_chain ref | W | W | fillet::test_tangent_chain_fillet |
| Loft cap round | cap_round | W | W | surfacing::test_cap_round_smooth_join |

### Shell / thicken / offset
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Shell / hollow | shell | W | W | shell::test_shell_open_top, surfacing::test_shell_strategies_box |
| Thicken sheet | thicken | W | W | shell::test_thicken |
| Offset face (push/pull) | offset_face | W | W | shell::test_offset_face, surfacing::test_offset_face_curved |
| Offset face loop / edge / vertex | - | M | M | (3 rows) |

### Direct face / edge editing
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| **Move face with re-fillet** (spec 2.5) | push_pull | P | W | parity::test_push_pull_refillets, test_push_pull_all_edges_filleted (before: manual remove+offset+fillet) |
| Move face by arbitrary vector | - | M | M | along normal only |
| Rotate / scale faces | - | M | M | (2 rows) |
| **Draft face** | draft_face | M | W | parity::test_draft_face_and_analysis |
| Match faces | - | M | M | |
| Delete face + heal | delete_face | W | W | direct::test_delete_face_heals_boss |
| Dissolve faces / delete edges | - | M | M | (2 rows) |
| Move / slide edges | - | M | M | (2 rows) |
| Unjoin / extract faces | - | M | M | (2 rows) |
| Rebuild face / raise degree / untrim / isoparam edges / unwrap | - | M | M | (5 rows) |
| Deform (bend/twist/taper) | - | M | M | |

### Mirror / patterns / symmetry
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Mirror (keep/replace/auto-union) | mirror | W | W | pattern::test_mirror_union_and_copy |
| **Symmetry-aware half model** | symmetrize | P | W | parity::test_symmetrize (before: mirror only, no cut-at-plane) |
| Radial array | radial_array | W | W | pattern::test_linear_radial_arrays |
| Rectangular array | linear_array | W | W | same, test_union_array |
| Curve pattern along path | - | M | M | |
| Arrays of faces | - | M | M | |
| Linked instance / realize | instance, realize | W | W | pattern::test_instances_follow_source |
| Duplicate | duplicate | W | W | |

### Transforms / align
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Move | move | W | W | pattern::test_transforms |
| Rotate (pivot) | rotate | W | W | same |
| Scale | scale | P | P | uniform only |
| Align faces/edges/vertices | - | M | M | (use measure + move) |

### Selection / refs
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Face/edge/vertex/body modes | ref kinds | W | W | select::test_by_normal_geom_pick |
| Box select | within | W | W | |
| Loop select | loop outer/inner | P | P | select::test_loops (face loops, not edge rings) |
| Tangent chain | tangent_chain | W | W | select::test_tangent_chain |
| Select by type | geom | W | W | |
| Select adjacent | - | M | M | |
| Stable geometry refs / tags | ref specs, tag | W | W | select::test_tags_reresolve_after_edit |
| **Suggest refs near a point** | cad_suggest_refs | M | W | parity::test_suggest_refs_are_verified |

### Snaps / cplanes / datums
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Snaps (vertex/mid/center/edge/face) | exact coords + select/measure | P | P | no snap-token refs |
| Cplane from face / 3 pts / origin+normal | cplane | W | W | prims::test_cplane_from_face |
| Sketch on face (curves on cplane) | plane=<cplane> | W | W | prims::test_box_align_and_cplane |
| Datum point/axis | cplane | P | P | |

### Analysis / inspection
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| **Measure distance / angle / radius / props** | cad_measure | M | W | parity::test_measure_and_curvature |
| **Curvature at point** | cad_curvature | M | W | same |
| Validate bodies | state.valid | W | W | |
| Interference check | measure / explain_failure overlap | M | P | |
| Section analysis | split | M | M | |
| Continuity (zebra) analysis | cad_render zebra | P | P | visual only |
| **Draft analysis** | cad_draft_analysis | M | W | parity::test_draft_face_and_analysis |
| **Deviation to reference** | cad_deviation | M | W | parity::test_deviation |
| **Silhouette vs reference image** | cad_compare_to_ref | M | W | parity::test_compare_to_ref |

### Data / IO / history
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Export STEP / OBJ / STL / glTF | cad_export | W | W | export::test_export |
| Export 3MF / SVG / hidden-line | - | M | M | (2 rows) |
| Import STEP / IGES / x_t | - | M | M | |
| Facet settings / tri budget, LODs, seams | cad_game_mesh | W | W | export::test_game_mesh_blender, test_game |
| Live DCC bridge | game_mesh (batch) | P | P | not live |
| Undo / redo / branches | journal | W | W | journal::test_undo_redo_branch |
| Parametric history (beyond Plasticity) | cad_set_param | W | W | journal::test_set_param_replays_and_rolls_back |
| Groups / visibility | - | M | M | |
| Crash isolation | sandbox | W | W | crash::* |

### LLM ergonomics (not in Plasticity; counted)
| capability | our op | before | after | test / note |
|---|---|---|---|---|
| Worked example per op in tool description | EXAMPLES -> op_<name>, cad_help | M | W | parity::test_examples_match_signatures, test_mcp_query_tools |
| explain_failure | cad_explain_failure | M | W | parity::test_explain_failure |
| Concise state diff per op | info.diff | M | W | parity::test_state_diff_concise |
| Error hints + max_feasible | ToolError | W | W | fillet::test_fillet_auto_reduce_and_hint |

## 3. LLM text-only walkthrough (can each step be done without seeing the screen?)
1. Block out: prims / curves with explicit numbers - yes.
2. Pick geometry: semantic refs; unsure -> `cad_suggest_refs(obj, near=[x,y,z])` returns verified refs - yes.
3. Know what happened: `diff` in every result - yes.
4. Fix a failure: hint + `cad_explain_failure` - yes.
5. Edit after fillets: `push_pull` or `cad_set_param` on the old node - yes.
6. Check against the brief: `cad_measure`, `cad_draft_analysis`, `cad_deviation`, `cad_compare_to_ref` (numbers),
   `cad_render` (needs an image-capable model to look) - yes, numerically.
Remaining text-only gaps: no snap tokens like `{"edge_mid": ref}` in point params; no curve-curve intersection
point query; trim needs params not "the piece between X and Y".

## 4. Next gaps by priority (product modelling)
1. Snap-token points in params (mid/end/center of a ref) + curve intersection trim.
2. Exact Gordon network surface; true conic fillet profile (custom blend via blend_surface along edge).
3. Move/rotate face by vector (BRepOffsetAPI_MakeDraft / local ops), face-face fillet.
4. Section analysis curves, body-body intersection curve op, silhouette curves.
5. STEP import (reference CAD), non-uniform scale, sweep twist/scale law.
