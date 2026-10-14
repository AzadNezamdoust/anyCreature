# Blender hard-surface harness (per subject) — scripts/hs

Generalised from the one-off pilot `out/blender-pilot/apc_8x8/` (read-only reference). A modeller writes ONE file,
`out/blender-hs/<s>/build.py`; the harness builds it in Blender 5.1, checks topology and the tri budget, exports a
glb, renders the four turnaround orthos in the gold judge's exact framing plus the judge's registered concept
camera, scores the model EXACTLY as the gold judge scores `model.mjs` (`judge_mesh.mjs`: same sigma fit, same
iou / agree), and composes a sheet: reference | current gold `model.mjs` | Blender.

## Files

| file | what |
|---|---|
| `scripts/hs/dump_frame.mjs` | `--subject <s>[,<s2>...]` -> `<s>/frame.json`: px/m `s`, per-view `ox oy kr ku w h spec` (scripts/v6/ortho.mjs `loadTurnaround`) + `crops` (judge.mjs `cropOf`, used to cut the current model's tiles) |
| `scripts/hs/dump_concept_cam.mjs` | `--subject <s>[,...]` -> `<s>/concept_cam.json`: the registered concept camera (scripts/registered.mjs) with the gold model's `frameScale/frameX/frameY` knobs from `out/ref/gold/<s>/model.mjs` |
| `scripts/hs/run_pass.py` | the pass (Blender, background) |
| `scripts/hs/judge_mesh.mjs` | the scorer: scripts/v6/judge.mjs's sigma fit + ortho / concept iou / agree on a triangle mesh (`--mesh`), or on a model.mjs (`--module`, `--export` its geometry as mesh.json) |
| `scripts/hs/build_from_mesh.py` | a build file that loads a mesh.json as-is (`$env:HS_MESH`), for the round-trip check |
| `scripts/hs/hs.py` | generic helpers imported by every `build.py` |
| `scripts/hs/imgio.py` | PNG <-> numpy through `bpy.data.images` (no PIL in Blender) |
| `scripts/hs/build_template.py` | starting point for a new subject's `build.py` (v10 / vehicles; a WF v11 subject starts from `spec_blockout.py`) |

**WF v11 (2026-10-12, research/WORKFLOW-V11.md; any subject with `subjects/<s>/spec.json`):**

| file | what |
|---|---|
| `scripts/hs/spec_build.mjs` | `--subject <s>`: `subjects/<s>/spec.in.json` (orchestrator's px rects on the registered views + hero ellipse reads) -> `spec.json` (metres, anchor ratios, view medians, `contested`, `cam_hints`, `const`); `--resolve hero [--cam]`: contested dims through the frozen camera's free hero edges. Test: `node --test scripts/hs/spec_build.test.mjs` |
| `scripts/hs/spec_proxy.py` | the spec boxes as Blender objects (one rule for the camera proxy and the block-out) |
| `scripts/hs/solve_persp_cam.py --proxy spec` | the FROZEN concept camera from the spec proxy (`--fov-min/--fov-max`, ellipse hold / soft terms, `frozen` block, `free_edges`, `camera_contested`, `hero_gate`); `--build` refused with `--proxy` |
| `scripts/hs/spec_blockout.py` | `--subject <s>`: the generated pass-1 `build.py` (`SPEC = hs.load_spec`, `C = hs.consts`, one primitive per part) |
| `scripts/hs/spec_lint.py` | builder-contract lint (advisory): literals >= 0.02 m in `part_*` without `# local:`, unused spec keys, unnamed parts |
| `scripts/hs/v11gate.py` | the v11 gate inside `run_pass.py`: frozen-camera / spec-hash / camera-change refusals, `--fix` latch, SPEC + BANDS + HERO + SIGMA + topo + tris, SCORE / ROLLBACK, `passN_spec.json` |
| `scripts/hs/score/specgate.mjs` | SPEC table (per-part per-axis, embedded ends clipped, ratios to the anchor). Test: `score/specgate.test.mjs` |
| `scripts/hs/score/bands.mjs` | BANDS (20 silhouette bands per view vs the turnaround; side / top hard). Test: `score/bands.test.mjs` |
| `scripts/hs/tests/mutants.py`, `test_camera_v11.ps1`, `test_run_pass_v11.ps1`, `fuzz/test_spec_consts.py` | v11 acceptance: §3 camera checks + §5.3 mutants, run_pass refusals, hs.load_spec / consts |

`hs.py` v11 additions: `SPEC = hs.load_spec(SUBJECT)` (`SPEC.part("<id>").L / .H / .W / .D / .pos / .size_author`),
`C = hs.consts(SPEC, overrides=os.environ.get("HS_CONST_JSON"))` (unknown override keys refused; `"<id>.<dim>"` keys
move a part dim in `load_spec`), `hs.SPEC_USED`, `cylinder(..., n=None)` = 16 segments for r >= 0.02 (else 12).
v11 pass: `run_pass.py -- --subject <s> --pass N [--fix <key[,key]> | --fix detail] [--accept-camera] [--final]`
(`--v10` = the pre-v11 gate on a subject that has a spec).

`frame.json` / `concept_cam.json` already exist for apc_8x8, main_battle_tank, light_tank, aa_tank, attack_heli,
transport_heli, combat_bike, jeep_gun, rocket_truck, supply_truck. Re-run `dump_concept_cam.mjs` whenever the gold
model's frame knobs change.

## How a modeller uses it

All commands from `D:\Git\anyCreature\hard_surface`.

```powershell
# once per subject (already done for the ten above)
node scripts/hs/dump_frame.mjs --subject <s>
node scripts/hs/dump_concept_cam.mjs --subject <s>
Copy-Item scripts/hs/build_template.py out/blender-hs/<s>/build.py   # then model

# every pass
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 `
    --python scripts/hs/run_pass.py -- --subject <s> --pass N            # add --final for the keeper
```

Options: `--build <py>` scores another build file, `--out-dir <dir>` writes the pass outputs there (frame.json /
concept_cam.json are still read from `out/blender-hs/<s>/`). Direct subjects: `--gate-ref mature|all` (see "Direct
subjects and handheld weapons" below).

**A pass takes 2-4 minutes** (build, glb, judge sigma fit, five renders, sheet). Run it in the FOREGROUND and give the
agent shell its maximum timeout (Bash / PowerShell tool `timeout: 600000` ms); never `run_in_background`, never `&` /
`Start-Job`. A backgrounded pass is read before it has finished (stale `passN_stats.json` or none), and the default
2-minute tool timeout kills it half-written. Several independent passes (separate `--out-dir`s) may run in parallel
inside ONE foreground command (`a & b & wait` in bash); never two passes into the same out dir.

Outputs in `out/blender-hs/<s>/`: `passN_{side,front,rear,top,concept}.png`, `passN_compare.png`,
`passN_stats.json`, `passN_<s>.glb`, `passN_build.py` (snapshot of the build that made the pass). `--final` copies
them to `side.png … concept.png`, `compare.png`, `stats.json`, `<s>.glb`.

stdout: `TRIS n / budget TOPO {...}`, `SIGMA <this model> (gold <gold model>)`, one
`VIEW <v> {iou, agree, drift, ref_only_px, model_only_px} | gold {iou, agree}` per view (orthos + concept),
`DELTA agree vs current {...}`, `DELTA iou vs current {...}`, `WARN` lines (over budget, non-clean topology per
object, a pre-scaled root). Exit code 1 = the build raised or the scorer failed (traceback / node stderr in the log).

What it measures:
- **Topology** per object and total: non-manifold edges, boundary edges, zero-area tris (< 1e-8 m²), duplicate
  faces, loose verts/edges, faces coincident across objects (centroids within 1 mm, parallel normals = z-fight).
  Target: all zero (`stats.json topology_clean`).
- **Tris** (triangulated) against `subjects/<s>/subject.json ruleOverrides.tris.value`, else 8000.
- **Scores = the gold judge's, computed by the judge's own code** (2026-10-03 fix; before, the harness scored its
  renders at scale 1 and the concept as plain IoU, so "agree vs gold" compared unlike things). run_pass dumps the
  built parts' triangles (author frame, one pseudo-part per object x material, zone = material) and runs
  `judge_mesh.mjs` on them, which imports scripts/v6/ortho.mjs / registered.mjs / project.mjs and does what
  `judge.mjs judge()` does for a `model.mjs`:
  - **sigma**: `fitSigma` (a verbatim copy; judge.mjs does not export it; since 2026-10-10 kept unless a dense scan beats it clearly, see "Sigma fit") — ONE uniform model scale about the
    origin shared by all orthos, golden section on the mean ortho silhouette IoU at 256 px in 0.6..1.8. So the
    absolute metric size is not scored, proportions are. Gold's sigma is in `out/ref/gold/<s>/view/model-view.json`.
  - **orthos**: `rasterOrtho` at k·sigma, `JUDGE_SIZE` 512 px, views.json `scale.right/up` via `basisOf`;
    `viewScore`: iou = plain, agree = with the view's drift rects don't-care; `drift` = their foreground share.
  - **concept**: `project(frame "target")` with the GOLD module's `meta.front` + KNOBS frame (sigma is NOT applied —
    the judge does not apply it there), target = `subject.json paths.target`, `targetState` with the subject mask
    rule (fgMax, enclosedFg, measured subject polygon / occlusion hull); iou = plain registered IoU, agree = with the
    concept drift rects don't-care.
  - `ref_only_px` / `model_only_px` count the judge's rasters (512 px orthos, the target's own px for the concept).
- **Renders / sheet**: the Blender orthos are drawn with the root scaled by the fitted sigma (x the view squeeze), the
  concept unscaled, so the sheet shows what was scored. They are not scored.
- **Current**: the gold model's iou / agree (every view, concept included) from `out/ref/gold/<s>/state.json`
  `baseline.views` (the gate's numbers; fallbacks `view/model-view.json`, then `gold.mjs status`), its sigma from
  `view/model-view.json`; its tiles are cut from row 2 of `out/ref/gold/<s>/view/model-view.png` (`frame.json crops`).

**build.py must NOT pre-scale.** Build in the gold model's metres (reuse `model.mjs` numbers as they are); the harness
fits sigma itself exactly like the judge, and the concept framing (`concept_cam.json`, unscaled like the judge) is then
right as dumped. A root scale is reset to 1 with a WARN. A pre-scale factor K (transport_heli's K = 1.119, and its hand
rescale of `concept_cam.json` s by 1/sigma) is no longer needed: drop K and re-run `dump_concept_cam.mjs`.

The cel renders are for comparison only: they replace each material's node tree with
Normal·L -> 6-band constant ramp -> × base colour -> emission (+ Freestyle ink). The glb is exported first and keeps
plain Principled base colours.

## build.py contract

```python
import hs                      # scripts/hs/hs.py (run_pass puts scripts/hs on sys.path)
PALETTE = {"body": "#737750", ...}          # sRGB hex per material name
def build():
    root = hs.begin("<s>", PALETTE, guards=True)   # wipes the scene, flat materials, root empty; guards: see below
    parts = [part_hull(), *part_wheels(), ...]   # each: hs.finish(bm, name, [material names], role)
    hs.end(parts)                           # remove_doubles + dissolve_degenerate, flat shading
    return root, parts                      # root: the empty every part is parented to
```

- **Frame**: metres in the subject's AUTHOR frame (`subjects/<s>/turnaround/views.json`): near flank **+x**,
  **y up**, nose **+z**, ground y = 0, x and z centred. `hs.A(x, y, z)` maps to Blender **Z-up** as
  `(x, -z, y)`: nose **−Y**, near flank **+X**. The glTF exporter's +Y-up conversion maps it back, so the glb is in
  the author frame (the same frame as `model.mjs` and the turnaround). Use A() / hs primitives; never type Blender
  coordinates by hand. On a mesh in Blender coordinates: author x = `co.x`, author y = `co.z`, author z = `-co.y`.
- Every part is a separate mesh object with `ob["part"] = <role>` (the roles of subject.json `ruleOverrides.roles`
  where they exist), parented to root via `hs.finish`. Root stays at the origin with identity transform (the
  harness scales it per view).
- Symmetric parts: build the +x side, `hs.mirror_x(ob)` (or `add_mirror_x` + one `apply_modifiers`).
- Measure numbers on the registered turnaround (frame.json `s` px/m, `ox oy`: author point p lands on
  `px = ox + s (p·right)`, `py = oy − s (p·up)`) and the concept; write the source of each in the docstring.
- `out/blender-hs/apc_8x8/build.py` is the worked example (7644 tris, clean topology).

### hs.py helpers

All points are AUTHOR-frame metres (x flank, y up, z nose); `bm` is a `bmesh.new()` you later pass to `finish`.
Signatures and return values as in `hs.py` (2026-10-10):

| helper (signature) | returns | use / notes |
|---|---|---|
| `A(x, y, z)` | Blender `Vector` (x, -z, y) | author -> Blender; only for hand-made bmesh verts |
| `begin(name, palette, guards=False)` | root empty | wipe scene, palette materials (`{name: "#hex"}`), root; new builds `guards=True` |
| `finish(bm, name, mats, part)` | mesh object (parented to root) | bmesh -> object; `mats` = material names (face `material_index` indexes them), `part` = role -> `ob["part"]`; frees `bm` |
| `end(parts, weld=1e-5)` | `parts` | weld + dissolve degenerates, flat shading; call once at the end of `build()` |
| `loft(bm, rings, cap0=True, cap1=True, mat=0)` | `(verts per ring, faces)`; `faces[-1]` = last cap | rings of Blender vectors (`hs.circle`, `[A(...)...]`), equal length |
| `prism(bm, poly, axis, a0, a1, mat=0)` | like `loft` | 2D polygon extruded along author `axis` from a0 to a1; 'x': poly (z, y), 'z': (x, y), 'y': (x, z) |
| `mirror_profile(half)` | closed loop `[(x, y)...]` | half profile from bottom centre up -> full symmetric loop |
| `profile_object(name, poly, axis, a0, a1, mats, part, bevel=0.0, angle_deg=30.0, mat=0)` | object | prism -> object (+ applied angle-limited chamfer) |
| `box(bm, c, size, mat=0, chamfer=0.0)` | faces (list) | axis-aligned box, centre `c`, FULL size `(sx, sy, sz)`; chamfer <= 0.4 x thinnest side |
| `oriented_box(bm, centre, axes, size, mat=0)` | like `loft` | box on orthonormal author axes `(u, v, w)`, full size `(su, sv, sw)` |
| `circle(centre, axis_u, axis_v, r, n, phase=0.0)` | list of Blender vectors | one ring for `loft` |
| `cylinder(bm, c0, c1, r, n, mat=0, r1=None, phase=None)` | like `loft`; `faces[-1]` = the c1 cap | cylinder / frustum (r -> r1) from c0 to c1, n sides |
| `tube_path(bm, points, r, n=8, mat=0)` | like `loft` (`[], []` if guarded away) | round tube swept along a polyline (hose, cable, handle), capped; r well under the bend radius |
| `pyramid(bm, base_c, base_hw, base_hd, tip, mat=0, axis="y")` | `([base verts + tip], faces)`; `faces[0]` = base | 4-sided point; base normal to `axis` ('y': hw = x, hd = z; 'z': hw = x, hd = y; 'x': hw = z, hd = y) |
| `ring_stack(bm, axis_c0, axis_c1, radii, n, mat=0)` | like `loft`; `faces[-1]` = the c1 cap | rings of `radii` equally spaced c0 -> c1: ribbed grip / bellows / hose, or a taper |
| `torus(bm, centre, axis, R, r, nu=16, nv=8, mat=0)` | `(verts per ring, faces)` (`[], []` if guarded away) | closed ring in ANY plane: `axis` = author vector or 'x' / 'y' / 'z'; R = centre-line radius, r = tube radius (< R) |
| `torus_x_y(bm, centre, R, r, nu=6, nv=4, mat=0)` | faces | the old ring, x-y plane only (axis z); kept for finished builds |
| `octagon(cx, cz, y, hf, hr, hx, ch=0.38)` | ring of 8 Blender vectors | chamfered octagon ring at height y (loft several: turrets) |
| `bore(bm, cap_face, wall=0.015, depth=0.06, mat=None)` (= `pit`) | wall faces | hollow muzzle / tube end / pit in a cap face: `vs, f = hs.cylinder(...); hs.bore(bm, f[-1], ...)`; wall + depth < the radius / length |
| `plane_cutter(bm, p0, p1, p2, out, half=0.9, depth=2.0)` | like `loft` | slab cutter through 3 points on the `out` side (corner facets with `cut`) |
| `cut(ob, cutter_bm, op="DIFFERENCE", name="cutter")` | `ob` | one-shot MANIFOLD boolean ('DIFFERENCE' / 'UNION' / 'INTERSECT'); applies `ob`'s modifiers too |
| `boolean(ob, cutter, op)` / `temp_object(bm, name)` / `kill(ob)` | modifier / object / - | stacked booleans: add several, then one `apply_modifiers`, then `kill` the cutters |
| `bevel_mod(ob, width, angle_deg=30.0, segments=1)` | modifier | angle-limited chamfer; width <= 0.1 x thinnest dimension; apply with `apply_modifiers` |
| `apply_modifiers(ob)` | `ob` | bake the modifier stack |
| `add_mirror_x(ob)` / `mirror_x(ob, tol=2e-5)` | modifier / `ob` | mirror about x = 0 (mirror_x applies it); inner face >= 1 mm off x = 0 or crossing it |
| `cleanup(ob, dist=1e-5)` | - | remove_doubles + dissolve_degenerate + recalc normals |
| `mark_edges(target, edges)` | number marked | Freestyle ink marks (attribute `freestyle_edge`); target = object or bmesh; edges = indices / BMEdges or `f(a, b) -> bool` on the AUTHOR-frame end points; mark last (cuts / welds renumber edges) |
| `wire_cage(ob, thickness=0.026)` | modifier | open lofted frame -> bars (Wireframe, replace); thickness <= 0.1 x width |
| `tyre(bm, centre, r, hw, tread_h=0.042, nseg=16, section=None, lug_len=0.8, lug_drop=0.03, side=1)` | tread block faces | tyre, axle along author x; hw >= 0.05 |
| `hub(bm, centre, hw, rings=None, n=10, recess=0.06, bolts=8, bolt_r=0.195, bolt_size=(0.024, 0.015), bolt_dx=(0.02, 0.05), scale=1.0, side=1)` | - | recessed rim, boss, bolt studs (`scale = r / 0.468`) |
| `wheel(bm_tyre, bm_hub, centre, r, hw, **kw)` | - | `tyre` + `hub`, kwargs split by name |
| `tyre_section(r, hw)` | `[(radius, u)...]` | the default tyre cross-section |

**Touching / overlapping primitives in ONE bmesh.** `loft` / `box` / `cylinder` ... each add a separate closed shell to
`bm`; nothing merges them except the weld in `finish` (guards) / `end`, which fuses coincident vertices. Measured
(`out/score/gate2/overlap_test.py` -> `overlap_test.txt`, guards off and on alike):
- boxes stacked FLUSH (a shared face: a block on a block, a plate on a hull face): the weld joins them along the shared
  face -> **4 non-manifold edges**, and a later DIFFERENCE cut keeps them;
- boxes sharing only an EDGE: **1 non-manifold edge**, which a UNION cannot fix (edge contact is not a solid);
- INTERPENETRATING shells (a box through a box, a rib ring sunk into a hose): topology 0, but the part is two
  self-intersecting shells (hidden internal faces, stray ink lines where they cross, method.md "Render aids").
Fix: (a) join with a boolean: build the second piece in its own bmesh, `ob = hs.finish(bm1, ...); hs.cut(ob, bm2,
"UNION")` (flush-stacked and interpenetrating both come out clean), with the pieces overlapping by >= 1 mm (never edge
or point contact); or (b) make it its own part object (`hs.finish(bm2, ...)`): parts may overlap each other, but keep
parallel faces of different objects >= 1-2 mm apart (`coincident_faces_across_objects`). Pieces with a gap between them
(separate bolt heads, a row of slats) may share one bmesh.

**Guards (2026-10-10).** `hs.begin(name, PALETTE, guards=True)` turns on the fixes from the helper stress test
(`fuzz/FINDINGS.md`): weld at `finish` and on cutters, cutters carry the target's material slots + empty slots dropped
after apply, `mirror_x` heals a part touching x = 0, `bevel_mod` / `box(chamfer=)` clamped to 0.45 x the thinnest
dimension, `tyre_section` chamfers scaled with hw; clamps and out-of-range calls go to `hs.GUARD_WARN`. **New builds:
always on.** Default off: with guards off every helper runs its original code, so finished builds are unchanged
(proof: `fuzz/matfix_all.py`, all 30 finished builds identical to the pre-guard hs.py; `fuzz/regress.py`, 6 builds'
`stats.json` reproduced exactly). `HS_GUARDS=1` in the environment forces guards on for any build without editing it
(what-if runs). Safe input ranges: `out/blender-hs/BUILD-DIRECT.md` "Helper safe ranges".
Finished builds are not face-ORDER deterministic run to run (same hs.py, same build: ~1 part in 30 comes out with
another face / vertex order, identical coordinates and materials); compare builds with `fuzz/matfix_probe.py`'s
order-invariant `canon`, not raw mesh bytes.

| fuzz file | what |
|---|---|
| `fuzz/fuzz_helpers.py` + `fuzz/run_fuzz.py` | seeded random-composition stress test (`--guards` = guards on) |
| `fuzz/report.py`, `fuzz/compare.py`, `fuzz/guards_report.py` | tally a run; compare two runs; per-guard paired off / on table |
| `fuzz/matfix_probe.py`, `fuzz/matfix_all.py` | order-invariant signature of every finished build; pre-guard vs patched hs.py |
| `fuzz/regress.py` | run_pass pass 99 of finished builds into `out/fuzz/regress*/` vs their `stats.json` |

## Blender 5.1 pitfalls (all hit in the pilot)

1. **EEVEE is the only engine listed** in a `--factory-startup` background run: `scene.render.engine = "BLENDER_EEVEE"`.
2. **Set `view_settings.view_transform = "Standard"`** (and `look = "None"`); the default AgX/Filmic shifts every
   flat colour.
3. **`Material.use_nodes` is deprecated** in 5.x: a new material always has a node tree; only set `use_nodes` when
   `node_tree is None` (older Blender).
4. **Always absolute paths.** A relative output path in background mode resolves against the (unsaved) blend file
   and lands in `D:/`. The harness builds every path from `__file__`.
5. **No PIL inside Blender.** Read / write PNGs through `bpy.data.images` + numpy `pixels.foreach_get/foreach_set`
   (`imgio.py`; rows are bottom-up, flip them).
6. **Cel ramp on Normal·L, not Shader-to-RGB.** Diffuse -> Shader to RGB under a sun picks up ~0.3 of ambient and
   the bands drift; dot the geometry normal with a fixed light vector and feed a CONSTANT ramp -> emission.
7. **Boolean solver `"MANIFOLD"`** (4.5+/5.x): manifold in, manifold out, fast. Inputs must be closed meshes;
   keep cutters past the surface (never coplanar with the face they cut).
8. **Bevel and inset leave zero-area faces / coincident verts**: run `remove_doubles` + `dissolve_degenerate`
   (`hs.cleanup`, done for every part by `hs.end`).
9. **`inset_individual` with depth makes funnels** (the walls slant). Do a lip inset (thickness, depth 0), then a
   zero-thickness inset with depth for straight walls (`hs.bore`).
10. **Apply modifiers via `bpy.data.meshes.new_from_object(ob.evaluated_get(depsgraph))`**, not `bpy.ops.object.
    modifier_apply` (context / selection dependent in background mode) — `hs.apply_modifiers`.
11. **Keep cutters local**: cutter objects are not parented to root and both they and the target have identity
    transforms, so the boolean sees both in the same space (`hs.temp_object`). Delete them after applying.
12. **Offset coplanar parts 1–5 mm** (a plate on the hull, an arch lip on the well edge): coplanar faces z-fight in
    the renders and show up as `coincident_faces_across_objects`.

## Verification (2026-10-03)

Build port (numbers from the OLD render-at-scale-1 scoring, kept for the record): apc_8x8 through the harness (`out/blender-hs/apc_8x8/build.py` = the pilot's `build_apc.py` on hs.py) reproduces the
pilot's final pass: tris 7644 (per object identical), topology all zero, side IoU .9664 / agree .9706, front .9553 /
.9600, rear .9512 / .9512 (pilot .9513), top .9331 / .9541, concept .9500. Renders differ from the pilot's by
< 60 px per view (wheel float noise); the compare sheet differs only in the row-3 label text.

### Scoring round-trip (2026-10-03, after the sigma fix)

Gold `model.mjs` geometry exported (`judge_mesh.mjs --module out/ref/gold/<s>/model.mjs --export mesh.json`), loaded
into Blender by `build_from_mesh.py` (`$env:HS_MESH`) and scored through `run_pass.py --build
scripts/hs/build_from_mesh.py --out-dir <scratch>` reproduces the judge (`view/model-view.json`) exactly:

| subject | sigma | side iou/agree | front | rear | top | concept iou/agree |
|---|---|---|---|---|---|---|
| main_battle_tank judge | 1.0255 | .9530/.9530 | .9610/.9610 | .9384/.9527 | .9701/.9817 | .9338/.9559 |
| main_battle_tank harness | 1.0255 | .9530/.9530 | .9610/.9610 | .9384/.9527 | .9701/.9817 | .9338/.9559 |
| apc_8x8 judge | 0.9922 | .9713/.9741 | .9535/.9607 | .9591/.9591 | .9375/.9579 | .9619/.9657 |
| apc_8x8 harness | 0.9922 | .9713/.9741 | .9535/.9607 | .9591/.9591 | .9375/.9579 | .9619/.9657 |

(The old harness gave MBT gold side .913 / front .947 / rear .932 / top .965 / concept .933.) Repeat:

```powershell
node scripts/hs/judge_mesh.mjs --subject <s> --module out/ref/gold/<s>/model.mjs --export $env:TEMP\<s>.mesh.json
$env:HS_MESH = "$env:TEMP\<s>.mesh.json"
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 `
    --python scripts/hs/run_pass.py -- --subject <s> --pass 0 `
    --build scripts/hs/build_from_mesh.py --out-dir $env:TEMP\hs-<s>
```

### Sigma fit (2026-10-10)

The sigma objective (mean ortho IoU at 256 px) is not unimodal: on a flat subject it swings 0.01–0.03 per 0.25 % of
scale (it_bounce_pad's side strip is a few px tall), and judge.mjs's golden section can stop in a side lobe. Bounce pad
pass 11 → 12 (only hidden side counts changed): golden sigma 1.0030 → 1.0153, objective .9595 → .9469, while 1.003
still scores .9596 on pass 12. `judge_mesh.mjs` now keeps the golden-section answer and adds a dense scan (0.6..1.8
step 0.005, top 5 refined at 0.0005, best at 0.0001); the scan answer replaces golden section only when it beats it by
more than `keep` in the objective: 0.001 for a direct subject, 0.005 for a vehicle (judge consistency first: of the 20
gold model.mjs only ambulance, +.0028, and attack_heli, +.0012, gain anything over 4e-4; both keep the judge's sigma).
`judge.sigmaFit` in stats.json records `method` (golden / scan), both sigmas and objectives.

Before / after (`out/score/sigma/compare.txt`, re-run `node out/score/sigma/compare.mjs`): bounce pad pass 11 1.003 /
1.003 (unchanged), pass 12 1.0153 → 1.003 (agree side .9264 → .9437, front .9266 → .9438, rear .9375 → .9495, top
.9398 → .9590), pass 14 (final) 1.0153 → 1.003; apc_8x8, pistol, it_gatling HS finals and all 20 gold model.mjs
(`--module`, vs view/model-view.json): sigma and every iou / agree identical (max delta 0.0000). `--sigma-fit golden`
(judge_mesh.mjs and run_pass.py) gives the old fit; rig_pass.py's `look` test uses it automatically for a look stage
scored before this change (no `sigmaFit` in its stats.json), so finished subjects' rigs keep reproducing their
stats.json until their look stage is re-run.

### Promotion to scripts/hs (2026-10-03, WF v9)

The harness moved from the gitignored `out/blender-hs/_harness/` to tracked `scripts/hs/` (paths: ROOTDIR =
`scripts/hs/../..`, the node scripts import `../v6/...`, `dump_*.mjs` still write `out/blender-hs/<s>/`). Check: apc_8x8's
final pass re-run from here (`--pass 16 --build out/blender-hs/apc_8x8/pass16_build.py --out-dir <scratch>`) reproduces
`out/blender-hs/apc_8x8/stats.json` exactly (every field; only `judge.source`, the mesh path, differs): tris 7868,
topology 0, sigma 1.0019, agree side .9691 / front .9619 / rear .9568 / top .9524 / concept .9583.

## Direct pipeline (WF v10) -- reading order for a `"pipeline": "direct"` subject
Worked example: `scripts/hs/examples/direct_example.py` (7 parts, 642 tris, topology 0, SIGMA 0.998; reads `frame.json`,
`hs.begin(guards=True)`, concept palette, `ob["part"]` roles, chamfered box with a slot cut, round barrel with a real
bore, `ring_stack` grip, `pyramid` point, `tube_path` hose, a separate trigger with 1.5 mm slot clearance). Run it:
`blender -b --factory-startup --python-exit-code 1 --python scripts/hs/run_pass.py -- --subject it_pneumatic_pick --pass 1 --build scripts/hs/examples/direct_example.py --out-dir out/score/example`.

Which sections of this README apply:
- **Apply**: "How a modeller uses it" (`dump_frame` / `run_pass`, `--build`, `--out-dir`), "build.py contract", "hs.py helpers"
  incl. Guards (always `guards=True`), "Blender 5.1 pitfalls", "Look method and close-ups", "Function stage (rig)" and the
  "Direct subjects and handheld weapons" block below (two-row sheet, `GATE` line, best-earlier reference).
- **Do not apply**: everything about a gold `model.mjs` -- the gold tiles / "current" column, `build_from_mesh.py` and the
  scoring round-trip, the "Verification" and "Promotion" history, `dump_concept_cam.mjs`'s model knobs, the vehicle-only
  sigma-keep rule. There is no gold to beat: later passes must not drop > .04 per view below the best earlier
  non-block-out pass (`--gate-ref mature`, below).
- Not in this README: the look method (`method.md`), the builder brief (`out/blender-hs/BUILD-DIRECT.md`), the part split
  and roles (`classes/weapon.md`).

### Reading sizes off the drawings: `scripts/v7/measure.mjs` (run from hard_surface)
All coordinates in the output are METRES along the view's own axes (side: right = -z, up = y; front: right = +x; top:
right = -z, up = -x -- see `frame.json views.<v>.spec`), so they convert straight to author numbers.
```powershell
# silhouette runs of the registered view. --axis row (default): one line per height  `up 0.440  ref -0.239..0.107 0.132..0.257`
#   = the foreground spans (right m) at that height.  --axis col: one line per right position -> the up spans.
node scripts/v7/measure.mjs profile --subject <s> --view side --axis row --from 0.40 --to 0.56 --step 0.02
node scripts/v7/measure.mjs profile --subject <s> --view side --axis col --from -0.10 --to 0.10 --step 0.01   # [--min-run 2 px]
node scripts/v7/measure.mjs profile --subject <s> --view concept --axis row --from 0 --to 1000 --step 20      # concept: PIXELS
# median colour of pixel rects x,y,w,h (view = concept | side | front | rear | top; concept = refs/<s>.png px) -> palette
node scripts/v7/measure.mjs sample --subject <s> --view concept 560,230,12,12 250,270,12,12
# connected colour components per view with bboxes in metres (finds the separate parts: lamp, hose, hook ...)
node scripts/v7/measure.mjs comps --subject <s> --view side --top 20
# zoomed crop with a 10 / 50 px grid;  runs = colour runs along one image row / column
node scripts/v7/measure.mjs grid --subject <s> --view side 300,100,500,300 --out $env:TEMP\g.png --scale 3
```
Read a profile at 5-10 steps along a part (collars, taper, rib pitch), not one value: a diameter from the front / rear
view, a length from the side, a half-width from the top, then cross-check the same dimension in a second view.

### Which dimensions a build aims at
1. **Registered frame wins**: `node scripts/v7/hull.mjs --subject <s> --no-concept` prints `dims W H L` (L = the anchor,
   the stated length). This is what the four drawings agree on, including hoses, straps, lamps and hooks the hull saw
   (it_pneumatic_pick: H 0.570 with the hose; facts.json said 0.52). Copy W H L into the head of `build.py`.
2. **`frame.json`** (`out/blender-hs/<s>/frame.json`, from `dump_frame.mjs`): `s` px/m and per view `ox oy` -- pixel <->
   metre for anything the profile tool does not give (`px = ox + s (p . right)`, `py = oy - s (p . up)`; the example's
   `side_px`).
3. **`subjects/<s>/turnaround/facts.json`** (`dims`, counts, decided facts) and the description in `refs/<s>.README.md`
   are estimates for sizes: use them for what the drawings cannot show (counts, the hidden flank, materials), never over
   the registered numbers. SIGMA far from 1.00 (0.84 for a build from facts) means the build used the wrong size.

### A drawing that sits off-centre against the registration (bore plane, frame shifts)
How a view is placed: the registration puts each view's origin at the centre of its foreground span (`frame.json` `ox
oy`); y = 0 is the lowest point and z is centred on L, so in y and z the origin follows the drawing itself. A drawing
can only sit "off-centre" in two ways:
1. **x in front / rear / top, a part protruding from one flank** (`facts.json asymmetric[].protrudes`: belt hook, drum,
   side magazine, sling loop): the span centre is pulled toward that flank and the bore plane lands at x != 0 (pistol
   2-3 mm, harpoon 8, flare pistol 10, line gun 18.5 mm). Check: `node scripts/v7/boreplane.mjs --subject <s>`
   (read-only) prints the bore-plane x in the span-centred frame and the views' spread. `views.json` with `_boreplane`
   (it_pneumatic_pick 2.4 mm, it_slinger -12.7 mm) = already fixed: its per-view `shift {right | up}` (metres) moved each
   x-seeing view's origin onto the mirror-symmetry axis (dims and `s` unchanged; judge, hull, `frame.json` and the renders
   all follow after `hull.mjs --write-frame`, `dump_frame.mjs`, `dump_concept_cam.mjs`).
2. **One drawing disagrees with the others** (a part a few px elsewhere in one view): method.md step 3, choose what most
   views show.

What the builder does:
- **Always build on x = 0 = the bore plane** (classes/weapon.md). Never shift the model, the root or a part sideways to
  chase the drawing's offset: the gate pays a little agree for it, and the rig (bore line, magazine axis in the bore
  plane) needs x = 0.
- **Ignore it** when the offset is <= ~3 mm (pistol: decided, do not flag), or `_boreplane` is already present: 1 px of
  the 1024 px drawing is 1 / `s` m (`frame.json s` ~1350-2850 px/m on the weapons, i.e. 0.35-0.75 mm), and likeness /
  part scores search a +-12 px registration shift anyway.
- **Report it** when the offset is larger, facts.json lists a protruding part and views.json has no `_boreplane`: write
  the `boreplane.mjs` line into `FEATURES.md` and the report. Writing the shift is a SETUP step (it edits
  `subjects/<s>/turnaround/views.json` and `frame.json`; the builder writes only under `out/blender-hs/<s>/`). After a
  registration change every earlier `passK_stats.json` was scored in the old frame, so the gate's best-earlier reference
  is stale: the orchestrator restarts the reference (a fresh `--out-dir` or a note in the report), never the builder.
- **Measure from the bore plane**, not from the drawing's centre line: a front-view bore centre at px `cx` is at
  `x = (cx - ox) / s`; a reviewer's or your own number read from an off-centre drawing is converted before use
  (it_grenade_launcher #5: the reviewer's gate face x .0985 came from the drawing's offset centre line; measured from
  the bore plane it is .093).

## Function stage (rig) — 2026-10-03

After the look stage's `--final`, a subject gets a rig: `out/blender-hs/<s>/rig.json` (joints, contacts, physics;
contract + test table: `scripts/hs/rig.md`) and one command:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 `
    --python scripts/hs/rig_pass.py -- --subject <s>        # [--no-render] [--no-judge] [--rig <json>] [--out-dir <dir>]
```

| file | what |
|---|---|
| `scripts/hs/rig.md` | the rig contract (rig.json schema, conventions, tests, what a riggable build needs) |
| `scripts/hs/rig_pass.py` | regroups the build under joint nodes, tests pivots / clearance sweeps / ground + stability / physics, re-scores the look, exports `<s>_rigged.glb` (+ clips), `<s>_rig.json`, `rig_stats.json`, `rig_sheet.png` |
| `scripts/hs/rig_sim.py` | the pure-Python raycast-vehicle sim (`python scripts/hs/rig_sim.py <rig_stats.json>`) |

`rig_pass.py` reuses `run_pass.py` unedited (it executes the source minus the final `main()`), so `run_pass.py` must
keep ending with a bare `main()`. What the modeller must provide: separate parts (or islands) per joint, closed
geometry under moving parts (turret ring, trunnion drum, wheel wells), pivots on the axes, clearance for the declared
limits, contact bottoms on y = 0 — see rig.md. If build.py changes for function, re-run the look stage `--final`
first: the `look` test demands identical tris and judge numbers.

Pilot apc_8x8 (pass 17): 22 joints (turret yaw 360, gun −8..+60, 8 suspensions −100..+70 mm, axles 1–2 steer ±25 /
±14, 8 wheels), 56/56 tests PASS, tris 7966, agree side .9717 / front .9631 / rear .9580 / top .9525 / concept .9583.

## Look method and close-ups (2026-10-04)
- `method.md` — the look method (owner decision): major masses first, feature inventory (`FEATURES.md`), view
  disagreements resolved by sense, gate = no ortho view more than .04 below gold, concept not gated.
- `closeups.py` — per part: SOURCE crop | BUILD crop | BUILD + source ink in red, at 2-3x, on the judge's registration.
  `blender -b --factory-startup --python-exit-code 1 --python scripts/hs/closeups.py -- --subject <s> [--k 2] [--parts a,b] [--build <py>] [--out-dir <dir>]`
  Needs one pass first (sigma). A magnifier for reading the source, not a ruler.
- `run_pass.py` inks Freestyle-MARKED edges (shallow facet lines the crease rule skips, panel seams). Mark them with
  `hs.mark_edges(ob, edges)`. Blender 5.1 has NO `MeshEdge.use_freestyle_mark` (AttributeError); the mark is the BOOLEAN
  EDGE attribute `freestyle_edge` (`me.attributes.new("freestyle_edge", "BOOLEAN", "EDGE")`, what aa_tank / apc_8x8 fall
  back to), verified to ink in 5.1.2 (`out/score/gate2/freestyle_test.py` -> `freestyle_test.txt`).

## Direct subjects and handheld weapons (WF v10, 2026-10-04) — the one page: `WORKFLOW-V10.md`
A subject with `subjects/<s>/subject.json "pipeline": "direct"` (class `weapon`, `classes/weapon.md`) has no gold model:
- `run_pass.py`: the sheet is two rows (reference | Blender), no gold tiles; the reference numbers of pass N are the BEST
  agree per view of the earlier passes (`passK_stats.json`, K < N, in the out dir and the subject's dir) that are not
  block-outs; stdout `VIEW <v> {...} | best earlier {...}` and one `GATE pass|FAIL {...}` line; `stats.json` gets
  `pipeline: "direct"` and `gate` {rule, ref_rule, ref_source, tris_ok, topology_clean, below_best_earlier (ortho views
  more than .04 below), pass}. `SIGMA` ~1.00 = built at the registered size.
- **Gate reference `--gate-ref mature` (default for direct subjects since 2026-10-10; vehicles unaffected, they gate on
  gold).** Block-outs are never a reference: the folder's FIRST pass (BUILD-DIRECT pass 1, "block-out from the size")
  and any pass with tris < 5 % of the budget (`BLOCKOUT_SHARE`, 400 of 8000). While only block-outs exist there is no
  reference (`ref_source` says "only block-outs so far"). `--gate-ref all` = the old rule (every earlier pass).
  Why: a block-out can fill a hollow / see-through part and outscore the correct model in that view for the rest of the
  build (it_tow_scooter Haiku: solid-disc shroud front .791 at pass 1, the hollow ring .678-.728 failed passes 3-6;
  it_pneumatic_pick: round pass-1 housing front .925, the ribbed hose at pass 4 / 5 failed front -.042 / rear -.044;
  it_grenade_launcher: a 188-tri pass 1 held rear at .790 for 16 passes). Replay of the 25 direct pass histories
  (`out/score/gate2/replay.py` -> `replay.txt`, rules R0-R9): this rule fixes those 6 false FAILs, frees the 4 grenade
  launcher passes (3, 4, 9, 10) whose only failing reference was its block-out (21 -> 11 failing passes) and still
  stops every regression measured against a mature pass (breach charges pass 5 / 10 / 11 / 14, jetpack pass 9 / 14 /
  15 / 18-20). Honest cost: grenade launcher pass 9 / 10 (the reviewer's gate radius R .096, which the builder rejected
  by measurement) are only -.019 / -.014 below the best mature pass, so they pass now. Rejected: previous pass or
  previous keeper only (let jetpack's narrow-strap drift pass 15 / 18-20 through: each step < .04), a likeness-interior
  excuse (detail always raises the interior over a block-out: it excused jetpack pass 10 / 15 / 18), a tris share
  relative to the current pass (a pass that doubles its tris escapes). Measured on scratch re-runs: it_pneumatic_pick
  pass 4 GATE pass under `mature` / FAIL front -.0421 rear -.0442 under `all`; it_tow_scooter Haiku pass 3 GATE pass
  (`out/score/gate2/{pick_mature,pick_all,tow_h}/pass*.log`).
  Not caught by any rule: a drop inside the .04 band (breach charges pass 13, side -.032 while likeness fell .597 ->
  .566): look at the sheet, the gate is a sanity check.
- `judge_mesh.mjs` / `dump_concept_cam.mjs`: the concept registration comes from `scripts/v7/conceptreg.mjs` (the camera
  of `subjects/<s>/camera.json` — the fixed style isometric, then `scripts/v7/solve-camera-hull.mjs` — with
  `layout.measured.json _frame.fit`); identity frame knobs (no model.mjs). For a vehicle both are unchanged.
- `closeups.py` works as it is. Builder brief: `out/blender-hs/BUILD-DIRECT.md`.
- `rig_pass.py`: `physics.mode: "handheld"`, the joint types `trigger` / `slide` / `magazine` / `barrel_spin` /
  `cylinder` / `hinge` / `selector` and `sockets` — `rig.md` "Handheld weapons"; brief `RIG-BRIEF.md` "Handheld weapons".
- `node scripts/v7/gold.mjs hs [--subject <s>]` shows a direct subject's stage: setup → build → review → polish →
  function → owner.
Regression after these edits (2026-10-04): `run_pass.py -- --subject apc_8x8 --pass 99 --build <snapshot> --out-dir <scratch>`
= identical stats.json (all but the mesh path), compare sheet, renders and glb byte for byte;
`rig_pass.py -- --subject jeep_gun --no-render` = the same summary lines, failed list and test numbers.
