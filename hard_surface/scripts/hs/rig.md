# Function (rig) stage — the rig contract

The look stage (`run_pass.py`) makes a model that looks right. The function stage makes it WORK as a game asset:
turrets turn, weapons elevate, wheels roll and steer, suspensions travel, rotors spin, and the vehicle behaves sanely
in a simple physics simulation. Per subject one file, `out/blender-hs/<s>/rig.json`, next to `build.py`.

```powershell
# from D:\Git\anyCreature\hard_surface, after the look stage's --final
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python-exit-code 1 `
    --python scripts/hs/rig_pass.py -- --subject <s>      # [--rig <json>] [--build <py>] [--out-dir <dir>] [--no-render] [--no-judge]
python scripts/hs/rig_sim.py out/blender-hs/<s>/rig_stats.json   # re-run only the physics (pure Python, no Blender)
```

Outputs in `out/blender-hs/<s>/`: `rig_stats.json` (PASS / FAIL + numbers per test, `sim_input`, `sim_frames`),
`rig_sheet.png` (posed contact sheet + the test table), `rig_pose_manifest.json` (each rendered pose's label, joint
values and view; written when rendering), `<s>_rigged.glb` (node hierarchy with pivots, named joints,
baked clips), `<s>_rig.json` (rig.json + `derived`: mass, COM, inertia, colliders, measured clear ranges, static wheel
loads). stdout: one `TEST PASS|FAIL <name> {numbers}` per test, `SUMMARY` lines, `RIG PASS|FAIL n/m`. Exit code 1 only
when it cannot run (bad rig.json, build raised); failed tests are in `rig_stats.json` (`failed`).

Vehicle door/hatch/hinge limits appear in side and rear-quarter views, with framing that includes both extremes.
Open the sheet and check the actual moving parts; a pose manifest proves requested coverage, not visual clearance.

`rig_pass.py` never edits `run_pass.py`; it executes its source minus the trailing `main()` and reuses its build
loader, topology report, judge call, cameras, cel materials and font. ~20 s without renders, ~80 s with (apc_8x8).

## Frame and conventions

Author frame = the glb's glTF frame: **x left (near flank), y up, z nose**, metres, ground `y = 0`. Angles in degrees,
positive = right-hand about `axis`: yaw about `[0,1,0]` turns left; a weapon pitches UP about `[-1,0,0]`; a wheel rolls
forward about `[1,0,0]` (both sides); steer about `[0,1,0]` is left. Suspension is prismatic along `axis`
(`[0,1,0]`), metres, positive = compression (wheel up into the body), 0 = the modelled pose. Pivots are absolute rest
positions (not relative to the parent). The rest pose (all joints 0) is the look-stage model, unchanged.

## rig.json

```jsonc
{
 "subject": "<s>", "version": 1, "class": "wheeled_apc",
 "joints": [
  {"id": "turret_yaw", "type": "turret_yaw", "parent": null, "pivot": [x, y, z], "axis": [0, 1, 0],
   "limits": null, "continuous": true,            // or "limits": [-120, 120]
   "parts": ["turret", "cupola", "smoke_launchers"]},
  {"id": "gun_pitch", "type": "weapon_pitch", "parent": "turret_yaw", "pivot": [..], "axis": [-1, 0, 0],
   "limits": [-8, 60], "probe": [-20, 85], "parts": ["gun"]},
  {"id": "susp_L1", "type": "suspension", "parent": null, "pivot": [wheel centre], "axis": [0, 1, 0],
   "limits": [-0.10, 0.07],
   "parts": [{"part": "axle_housings", "box": [[x0, y0, z0], [x1, y1, z1]], "name": "axle_L1"}]},
  {"id": "steer_L1", "type": "wheel_steer", "parent": "susp_L1", "pivot": [..], "axis": [0, 1, 0], "limits": [-25, 25], "parts": []},
  {"id": "wheel_L1", "type": "wheel_spin", "parent": "steer_L1", "pivot": [..], "axis": [1, 0, 0], "limits": null,
   "parts": [{"part": "tyres", "box": [..], "name": "tyre_L1"}, {"part": "hubs", "box": [..], "name": "hub_L1"}]}
 ],
 "contacts": [{"a": "turret", "b": "turret_ring"},
              {"a": "gun", "b": "turret", "seat": {"centre": [..], "r": 0.26}}],
 "tolerances": {"collide_m": 0.002, "pivot_m": 0.001, "ground_m": 0.005, "ring_m": 0.005, "bore_m": 0.03},
 "physics": { ... }
}
```

**Joint** fields: `id` (unique, and NOT a part name — it becomes the glb node name), `type`, `parent` (joint id or
null = the root), `pivot`, `axis`, `limits` (`[lo, hi]` deg or m; null for a continuous joint), `parts`. Optional:
`continuous` (turret), `bore_parts` (weapon_pitch: fit the bore line to these parts only, when a shield /
ammo box pitches with the gun), `probe` (`[lo, hi]` range the sweep explores past the limits; default limits ± 10° /
−0.05..+0.10 m), `step`, `yaw_samples` (weapon_pitch, default 12), `flap_deg` (rotor_spin: the disc is also swept
tilted ± this about both in-plane axes), `clip` (animation name override), `speed_param` (track_scroll). Continuous joints also take
`run_pose` (`{joint id: value}`: the pose the group spins in — a parked rotor's drooped blade raised by its flap
joint; the pivot test and the sweep use it) and `sync` (`{"joint", "ratio", "phase_deg"}`: a geared partner that turns
with it, partner value = ratio × value + phase_deg — tandem rotors; each flap tilt is swept on this disc alone and on
both discs together).

| type | motion | notes |
|---|---|---|
| `turret_yaw` | rotary | continuous or limited; pivot = centre of the turret's base ring |
| `weapon_pitch` | rotary | pivot = trunnion, on the bore axis; swept at 12 yaws of its turret ancestor |
| `wheel_spin` | rotary, continuous | pivot = wheel centre, axis = axle |
| `wheel_steer` | rotary | kingpin; swept at suspension droop / rest / bump |
| `suspension` | prismatic | limits `[-droop, +bump]` m |
| `suspension_arm` | rotary | swing / trailing arm (bike rear): pivot = the arm's axle, limits deg, + = wheel up; the harness converts to vertical wheel travel for the sim. A raked prismatic `suspension` (bike fork, child of its `wheel_steer`) is converted by `axis.y` the same way |
| `rotor_spin` | rotary, continuous | `flap_deg` for blade flap / teeter clearance |
| `track_scroll` | none | a marked part + `speed_param` (UV / offset proxy; no per-link animation). Exported as a node with extras |
| `door` / `hatch` | rotary | optional; clip `Open_<id>` |
| `fixed` | none | a named static group |

**Parts** are the build's object names (`hs.finish(bm, name, ...)`). A part that holds several joints' geometry can
be split without touching build.py by a **selector**: `{"part": <object>, "box": [[min], [max]], "name": <new>}` moves
the mesh islands whose bbox centre lies in the author-frame box into a new object (tris unchanged). Unclaimed parts
stay static under the root. A joint's moving group = its parts + all descendant joints.

**Contacts** declare intended interpenetration (a bearing, a seat): `{"a", "b"}` exempts the whole part pair;
with `"seat": {"centre", "r"}` only the triangles of `a` that lie entirely inside that rest-pose sphere are exempt
(so a barrel hitting the turret roof is still caught while the mantlet sits in its embrasure). Everything else that
interpenetrates deeper than `collide_m` (2 mm) is a collision.

### physics

```jsonc
"physics": {
 "ground_y": 0.0, "drive": true, "mu": 0.9, "lock_roll": false,          // lock_roll: two-wheelers (planar sim)
 "mass": {"density": {"hull": "armour_light", "tyres": "wheel", "default": "detail"},   // by part name / source part / role
          "mass_kg": null, "range_kg": [12000, 26000]},                   // mass_kg overrides the volume estimate
 "com": null,                                                              // optional authored COM (checked within 0.15 m of the computed one, then used)
 "wheels": [{"id": "L1", "centre": [x, y, z], "radius": 0.502, "width": 0.47, "steerable": true, "driven": true,
             "joint_spin": "wheel_L1", "joint_steer": "steer_L1", "joint_suspension": "susp_L1"}],
 "tracks": [{"id": "track_L", "parts": ["track_l"], "width": 0.5, "speed_param": "track_speed_l",
             "contacts": [{"centre": [x, r, z], "radius": r, "bump": 0.12, "droop": 0.10}]}],   // one per road wheel
 "skids": [{"id": "skid_L", "parts": ["skids"], "flex": 0.05, "contacts": [[x, 0, z], [x, 0, z]]}],
 "suspension": {"travel_bump": 0.07, "travel_droop": 0.10, "frequency_hz": 1.6, "damping_ratio": 0.6, "bump_stop_ratio": 60},
 "colliders": [{"id": "hull", "type": "convex", "joint": null, "parts": ["hull"], "chassis": true},
               {"id": "turret", "type": "box", "joint": "turret_yaw", "parts": ["turret", "cupola"]}],
 "sim": {"drop_m": 0.30, "bump_m": 0.15, "bump_len_m": 0.80, "speed_mps": 5.0, "accel_mps2": 2.5, "brake_mps2": 6.0,
         "brake_from_mps": 10.0, "lateral_g": 0.4},
 "limits": {"tip_side_min_deg": 30, "tip_pitch_min_deg": 30, "settle_s": 3.0, "ride_err_m": 0.010,
            "bump_pitch_deg": 10, "accel_pitch_deg": 3, "brake_pitch_deg": 5, "lateral_roll_deg": 6}
}
```

- **Mass** = Σ part mesh volume × effective density (hollow-shell classes, kg/m³): `armour_light` 1150,
  `armour_heavy` 1900, `turret_light` 1500, `turret_heavy` 2600, `soft_skin` 300, `cargo` 150, `wheel` 600,
  `track` 1500, `gun` 4000, `airframe` 110, `rotor` 300, `detail` 1500, `none` 0 (or a number). COM = mass-weighted
  volume centroids; inertia = per-part bbox boxes + parallel axis (diagonal).
- **Colliders**: `box` (AABB of the parts, or authored `centre` / `size`) or `convex` (hull vertices, author frame),
  each bound to a joint (null = chassis). The `chassis` collider's underside is what must never touch the ground.
- Wheel `radius` is the rolling radius = `centre.y − ground_y`. Spring rate per wheel is derived, not authored:
  `k = N / (g / (2π f)²)` from the static load N, damper `2 ζ √(k N / g)`; `<s>_rig.json derived` lists the loads.

## Tests (rig_stats.json `tests`)

| test | PASS when |
|---|---|
| `pivot:<wheel_spin / rotor_spin>` | radial + axial run-out about the axis ≤ 1 mm (least-squares circle / plane through the rim vertices: exact for any n-fold symmetric wheel) and the bbox centre is on the pivot ≤ 1 mm. The n-gon's facet ripple over a turn is reported, not judged |
| `pivot:<turret_yaw>` | pivot within 5 mm of the base ring's centre (lowest 30 mm slab of the joint's parts); reports ring + swept radius |
| `pivot:<weapon_pitch>` | trunnion ≤ 30 mm off the bore line (principal axis of the group), bore ⟂ pitch axis within 2° |
| `pivot:<wheel_steer>` | scrub radius (kingpin to wheel centre) ≤ half the wheel width |
| `pivot:<suspension>` | axis within 40° of vertical |
| `sweep:<joint>` | limited joints: walk out from 0 in both directions (1° / 5 mm) to the probe range; `clear` = range with no interpenetration > 2 mm of the moving group against everything else; PASS = limits ⊂ clear and no collision at rest. `first_hit_lo/hi` = first colliding value, the part pair, depth. weapon_pitch: per turret yaw; wheel_steer: per suspension state. Continuous joints: a full turn (turret 5°, wheel 15°), 0 colliding steps |
| `ground` | every wheel / track / skid bottom on `ground_y` ± 5 mm, nothing below it, wheel `centre` = spin pivot, `radius` = centre height |
| `mass` | total in `range_kg` (or in `mass.reference.kg` when a reference is given: "Mass: the honest rule"); authored COM (if any) within 0.15 m; outside a reference = FAIL + `owner_item` |
| `colliders` | a chassis collider exists, its bottom > 20 mm above ground |
| `stability` | COM inside the support polygon; static tip-over `atan(reach / COM height)` ≥ 30° sideways and fore / aft (`lock_roll` skips sideways) |
| `sim:drop_settle` | dropped 0.3 m: settles ≤ 3 s, ride height within 10 mm of the modelled pose, chassis never touches the ground, peak compression ≤ the suspension's measured clear travel (no tyre in the arch) |
| `sim:bump` | 0.15 m × 0.8 m sin² bump at 5 m/s: compression ≤ clear travel, chassis clear, &#124;pitch&#124; ≤ 10°, re-settles ≤ 3 s |
| `sim:accelerate` / `sim:brake` | 2.5 m/s² squat ≤ 3°, 6 m/s² dive ≤ 5°, no wheel lift, compression ≤ clear travel |
| `sim:lateral` | 0.4 g side load: roll ≤ 6°, no wheel lift |
| `regroup` | the joint hierarchy reproduces every vertex at rest (≤ 0.01 mm) and in a test pose (numpy pose = Blender pose) |
| `look` | tris = the look stage's `stats.json`, topology 0, ≤ budget, build.py = the look stage's final snapshot, the judge's iou / agree identical to `stats.json` (≤ 1e-4) and no view > .01 below gold |
| `export` | glb: tris unchanged, every joint a node under the right parent with its world pivot exact, all clips present |
| `pose:<joint>` | (only when the joint has `expect`, 2026-10-11) at the stated end pose the named point lies within `tol_m` of `near`, and the optional panel normal within `tol_deg`: "Pose expectations" below |

Helicopters (`drive: false`): only `sim:drop_settle` on the skids / wheels; rotor clearance is the `rotor_spin` sweep.

The sim (`rig_sim.py`) is a raycast vehicle: one rigid body, a spring-damper per contact along body-up, the ground's
rolling-circle envelope under each wheel, bump stops, load-shared drive / brake force and lateral slip friction
clamped to μN, semi-implicit Euler at 2 ms. It is a sanity check of the rig DATA (travel, COM, wheel layout), not an
engine: no tyre compliance, friction is regularised (a parked vehicle under side load creeps a few cm, `slide_m`).

## glb

`<s>` root → joint nodes (translation = pivot relative to the parent joint, identity rotation) → the part meshes
(mesh origin at the joint pivot). Joint nodes carry extras `joint_type`, `joint_axis`, `joint_limits`. Clips (NLA
tracks, sampled): `TurretYaw` (full turn or 0 → hi → 0 → lo → 0), `WeaponPitch`, `WheelsRoll` (one turn), `Steer`,
`Suspension`, `RotorSpin`, `Open_<id>`; joints of one type share one clip. Geometry is the look stage's, regrouped.
Unity 6: import with glTFast / UnityGLTF; drive the joint nodes from code with `<s>_rig.json`, the clips are previews.

## What the modeller must do (riggable build.py)

1. **Separate geometry per joint**: every moving group is its own object, or at least its own mesh islands (a
   selector can split islands, never a welded mesh). A base that must not turn (turret ring / plinth) is a separate
   static part.
2. **Closed geometry under moving parts**: every part is a closed solid, and whatever a motion uncovers is modelled —
   the roof / ring under a turret, a rotation-symmetric trunnion drum behind the mantlet, the wheel well behind a
   steered tyre.
3. **Pivots on axes**: a wheel is a body of revolution about its axle through its centre; the turret's base ring is
   centred on the yaw axis; the trunnion lies on the bore.
4. **Clearance**: steered tyres need well depth (inner sweep = `hw cosθ + R sinθ`), bump travel needs arch height,
   gun depression is limited by the highest roof fitting under the barrel, a turret base wider than its neighbours'
   gap must be round or static.
5. **Ground**: tyre / track / skid bottoms at `y = 0` (lug tips, not the carcass radius).
6. Keep the look gate: function edits go where no scored view sees them, or re-run the look stage `--final`
   BEFORE `rig_pass.py` (the `look` test compares against its `stats.json`).

Not covered (2026-10-03): tracks and skids / rotors are implemented but only the wheeled pilot (apc_8x8) has run;
a moving part fully inside another (no surface crossing) is not detected; the sim treats suspension axes as body-up.

## Handheld weapons (WF v10, 2026-10-04) — `physics.mode: "handheld"`

A weapon is held, not driven: with `"physics": {"mode": "handheld", "mass": {...}}` the harness runs NO `ground`,
`colliders`, `stability` or `sim:*` test (physics.wheels / tracks / skids / suspension / sim are ignored). Mass, COM and
inertia are still estimated from the part volumes and reported (`mass`: total in `range_kg` / `reference.kg` per "Mass:
the honest rule" below, authored COM within 0.05 m;
kg to 3 decimals, `volume_l`, `com_ahead_of_grip_m` when a `grip_r` socket exists). Density classes for weapons
(effective, kg per m³ of the closed mesh): `weapon_steel` 5000 (bored barrel, bolt, sights), `weapon_alloy` 1300 (hollow
receiver; the handheld default), `polymer` 450 (hollow furniture), `magazine_loaded` 1400, `optic` 900.
Frame: muzzle +z, the weapon's left flank +x, y up, y = 0 at its lowest point (classes/weapon.md).

### Mass: the honest rule (2026-10-10; required for new and re-rigged handheld subjects)

Builders were inventing `range_kg` to make `mass` pass (rocket_launcher 8–18, it_rotary_drill 25–75 for a 60 kg
solid-steel drill, it_gatling 30–75 for 55 kg). A range chosen after seeing the estimate tests nothing. Instead:

1. **Estimate from volume with real materials.** Each part: mesh volume × density × fill. Use the bulk material
   classes `steel` 7850, `aluminium` 2700, `polymer_solid` 1300, `rubber` 1150, `brass` 8500, `glass` 2500 kg/m³ for
   parts whose material is known, or the older effective classes (`weapon_alloy` 1300 = a hollow receiver *with* its
   mechanism, `polymer` 450 = hollow furniture, `magazine_loaded` 1400, `optic` 900, `weapon_steel` 5000) where the part
   stands for a whole assembly.
2. **Shell factor for parts drawn solid that are hollow in reality** (barrels, tubes, housings, drill cones):
   `"shell": {"<part>": f | {"wall_m": t} | {"bore_d_m": d}, "_why": "<one line per real-world reason>"}`.
   `f` = material fraction of the drawn volume (0 < f ≤ 1); `wall_m` = a closed shell of wall t over the part's own mesh
   (fill = min(1, area × t / volume), any shape); `bore_d_m` = a tube along the part's longest bbox axis with that bore.
   The wall / bore is the real object's (a barrel's bore, a housing's sheet thickness), never a number fitted to a range.
   `rig_stats.json` reports each `shell_fill` and the `_why`.
3. **The range comes from a stated real-world reference per item class**, recorded with its source:
   `"reference": {"item": "<real item(s) and configuration>", "kg": [lo, hi], "source": "<url / datasheet>",
   "exclude_parts": ["ammo_box"]}`. `kg` spans the real items of that class as published (no stylisation margin).
   `exclude_parts` removes parts the reference configuration does not include (ammo, a battery); they still count
   for total mass, COM and inertia. With a reference, the harness uses `reference.kg` as the range and ignores (and
   reports, `range_kg_ignored`) any `range_kg`.
4. **Outside the reference = owner item, never widened.** `mass` FAILs with `owner_item` (also listed under
   `owner_items` in rig_stats.json). The builder does not touch the range, the densities or the shells to make it pass;
   the owner decides: accept the stylised mass, set a game `mass_kg`, or change the model. A rig without `reference`
   still runs (`range_source: "builder (unreferenced)"` in its stats) but is not done under this rule.
5. **Game mass (optional, 2026-10-11): `"mass_game_kg": <kg>`** in `physics.mass`. The mass the game will use for a
   chunky prop (the set's props are drawn 1.5-2x a realistic prop, so the honest estimate lands 2-4x the reference:
   thumper 180 kg vs 64-72, glide pack 27 vs 2.4-6.9). It is REPORTED next to the estimate (`mass_game_kg`,
   `game_over_estimate`, `game_in_reference`; `derived.mass_game_kg` in `<s>_rig.json`) and never changes the test,
   the COM or the inertia: `mass` still compares the honest estimate with the reference and still FAILs as an owner
   item when outside it. (`mass_kg` is different: it rescales the estimate and the inertia to that total.)

   **Open owner question (not decided):** which number gates the set — (a) the honest estimate vs the reference, the
   game mass a separate column; (b) the game mass vs the reference, the estimate information only; or (c) one set-wide
   rule such as "game mass within 2x of the reference" (Opus plan) or a filled `MASS-GAME` table (Fable plan). Until
   the owner rules, write `mass_game_kg` only when the owner has given a number, and report every `mass` FAIL as an
   owner item.

Class references used so far (published figures, 2026-10-10):

| item class | kg | source |
|---|---|---|
| light rotary gun with motor + feeder, less ammo container / power (M134D) | 24–30 | modernfirearms.net/machine/usa/m134-minigun-e.html (XM214 bare gun ≈ 10–12 kg, en.wikipedia.org/wiki/XM214_Microgun) |
| two-hand electric breaker / heavy rotary hammer, no bit | 12.5–27.1 | hilti.com: TE 1000-AVR 12.5 kg, TE 3000-AVR 27.1 kg (EPTA 01/2003) |
| shoulder-fired launcher, loaded | 6.7–14.3 | en.wikipedia.org/wiki/AT4 (6.7 kg), en.wikipedia.org/wiki/Panzerfaust_3 (12.9, IT600 14.3 kg) |

Example (dry run of it_gatling, not applied):
`"mass": {"density": {"barrel_cluster": "steel", "ammo_box": "magazine_loaded", ..., "default": "weapon_alloy"},
"shell": {"barrel_cluster": {"wall_m": 0.006}, "_why": "barrels drawn solid; real barrels are bored tubes, ~6 mm wall"},
"reference": {"item": "M134D ...", "kg": [24, 30], "source": "...", "exclude_parts": ["ammo_box"]}}` → 52.7 kg total,
43.1 kg in reference scope → `mass` FAIL, owner item (the prop is drawn larger and chunkier than an M134).

```jsonc
{
 "subject": "<s>", "version": 1, "class": "handheld_rifle",
 "bore": {"parts": ["barrel"]},                      // default: parts named / with role "barrel"; or {"point", "dir"}
 "joints": [
  {"id": "trigger_pull", "type": "trigger", "parent": null, "pivot": [0, 0.166, -0.104], "axis": [1, 0, 0], "limits": [0, 12], "parts": ["trigger"]},
  {"id": "bolt_cycle", "type": "slide", "parent": null, "pivot": [..], "axis": [0, 0, -1], "limits": [0, 0.09], "parts": ["bolt"]},
  {"id": "magazine_release", "type": "magazine", "parent": null, "pivot": [..], "axis": [0, -1, 0], "limits": [0, 0.10], "parts": ["magazine"]},
  {"id": "barrels", "type": "barrel_spin", "parent": null, "pivot": [..], "axis": [0, 0, 1], "limits": null, "chambers": 6, "parts": ["barrel_cluster"]},
  {"id": "cylinder_index", "type": "cylinder", "parent": null, "pivot": [..], "axis": [0, 0, 1], "limits": null, "chambers": 6, "parts": ["cylinder"]},
  {"id": "bipod_leg_l", "type": "hinge", "parent": null, "pivot": [..], "axis": [1, 0, 0], "limits": [0, 90], "parts": ["bipod_leg_l"], "clip": "Open_bipod"},
  {"id": "selector_turn", "type": "selector", "parent": null, "pivot": [..], "axis": [1, 0, 0], "limits": [0, 90], "parts": ["selector"]}
 ],
 "sockets": [
  {"id": "muzzle", "pos": [0, 0.2265, 0.450], "axis": [0, 0, 1]},
  {"id": "sight_rear", "pos": [..], "axis": [0, 0, 1], "parts": ["rear_sight"]},
  {"id": "grip_r", "pos": [..], "axis": [0, -1, 0], "parts": ["grip"], "parent": null, "tol_m": 0.035}
 ],
 "contacts": [],
 "physics": {"mode": "handheld", "mass": {"density": {"barrel": "weapon_steel", "stock": "polymer", "default": "weapon_alloy"}, "mass_kg": null, "range_kg": [3.0, 6.0]}}
}
```

| type | motion | pivot test (`pivot:<id>`) | sweep (`sweep:<id>`) | clip |
|---|---|---|---|---|
| `trigger` | rotary, small arc; + = pull about `[1,0,0]` (the tip moves toward the grip) | the pin within 10 mm (`pin_m`) of the part's bbox, axis = the cross axis x within 5° (`free_axis` to skip), the tip's arc over the limits 2–25 mm | limits ⊂ clear (1° steps, probed one step past the limits) | `Fire` |
| `slide` | prismatic: bolt, charging handle, pistol slide, pump fore-end | axis along the bore (z) within 2° (`free_axis`), travel ≥ 5 mm | limits ⊂ clear (2 mm steps) | `Fire` |
| `magazine` | prismatic detach along the well axis | axis in the bore plane (abs(axis.x) ≤ 0.05), travel ≥ half the magazine's length along the axis | limits ⊂ clear AND `detached_at_limit`: at full travel, with every declared seat contact switched off, the magazine touches nothing (it is out of the well) | `Reload` |
| `barrel_spin` | rotary, continuous (gatling cluster) | the wheel test (radial / axial run-out ≤ 1 mm, bbox centre on the pivot), axis along the bore within 2°; with `chambers: n` the n-fold symmetry error ≤ 1 mm | a full turn at 5°, 0 colliding steps | `SpinUp` |
| `cylinder` | rotary, indexed `chambers: n` (revolver, revolver launcher) | as barrel_spin; `chambers` ≥ 2 required: the vertex set turned by 360 / n lands on itself ≤ 1 mm | a full turn at 5°, 0 colliding steps | `CylinderIndex` (one index step, 12 frames) |
| `hinge` | rotary: break-action, folding stock, bipod leg, feed cover | the hinge line within 20 mm (`pin_m`) of the part's bbox, limits given | limits ⊂ clear | `Open` (or `clip`) |
| `selector` | rotary, small lever | as trigger without the arc band | limits ⊂ clear | `Selector` |

Clips: `Fire` = trigger pull (frames 0–4–8) + slide / bolt cycle (4–10–16) in one clip; `Reload` = magazine out (12) and
in (24); `SpinUp` = one barrel turn (24 frames); `Open` = hinge out and back; joints of one clip name share it.

**Sockets** — named points with an axis: exported as empties `socket_<id>` (under their `parent` joint, else the root;
identity rotation, the axis as the extra `socket_axis`) and tested as stated (`socket:<id>`):

| socket | PASS when |
|---|---|
| `muzzle` | ≤ 3 mm off the bore line (`bore_socket_m`), axis along the bore (≤ 2°, pointing out), within −5 … +30 mm of the front of its declared `parts` (muzzle assembly), or all geometry when no parts are declared. This keeps a loaded projectile's tip distinct from the tube mouth. Unknown part selections fail; the distance to all geometry is still reported. |
| `sight_rear`, `sight_front` | each within 20 mm of its `parts`; plus `socket:sight_line`: the segment rear → front is not blocked by any part except the sockets' own `parts` (the line clears the receiver), ≤ 3° to the bore, above it |
| `ejection_port`, `optic_mount` | within `socket_m` (20 mm; `tol_m` per socket) of the surface of its `parts` (any part when none are named) |
| `grip_r`, `grip_l`, `magazine_well` | the same with 35 mm (they sit at the centre of a handle / a mouth); `magazine_well`'s axis within 5° of the magazine joint's |

The `export` test also demands every `socket_<id>` node at its position (`socket_max_err_mm`).

`look` for a direct subject: tris / topology / build snapshot / identical judge numbers as before; the reference is the
look stage's own best earlier pass (gate .04 on the orthos), not gold. **Hero-led rule (2026-10-11):** a direct subject
with `subjects/<s>/parts.json` whose final `stats.json` carries a `hero` verdict (built with `--hero report|gate`) is
gated on that verdict instead: `look` PASS = tris / topology / build snapshot identical, judge numbers identical to the
final `stats.json` (≤ 1e-4) and `stats.json` `hero.verdict` = PASS. Ortho views below the best earlier pass are
reported (`below_best_earlier_info`), not gated: a hero-led polish drops them on purpose (POLISH.md "Hero-led
views"); `sigma_in_band_0.98_1.03` is reported too. Subjects without parts.json / hero keep the rule above. The sheet shows REST, FIRE, RELOAD, OPEN, SPIN,
CYLINDER and SELECTOR poses instead of the drive frames. The SPIN tile renders from the muzzle-end three-quarter (`front_q`, 2026-10-10) so the
spinning cluster is in view; the plain `front` camera looks from −z, i.e. at the rear of a weapon.
Handheld hinge and trigger / slide limit tiles (`OPEN <hinge>`, `TRIGGER+SLIDE LIMITS`) render from whichever of side / front / top / quarter shows the moving group's rest-to-limit displacement largest in projected pixels, and the title ends with the view (`[SIDE]`); vehicle sheets are unchanged (2026-10-10).

### Non-firearm items (placed, worn, tools) — `class: weapon`, `physics.mode: "handheld"`

A deployable pad, carry rack, worn pack or thrown charge is not a gun but runs the same handheld harness, so record
`"physics": {"mode": "handheld", "mass": {...}}` (no wheels / contacts / colliders / sim sections) and the same mass rule.

- **Checks that apply**: `look`, `export` (every socket node), `mass` (+ `reference`), every joint you declare
  (`pivot:` / `sweep:` / clip), every socket you declare (`socket:<id>`), `topology`, the closed-solid and
  coincident-face checks. **Checks that need a firearm part**: `bore` / `socket:muzzle`, `socket:sight_line`, the
  `trigger` / `magazine` joints, and `com_ahead_of_grip_m` (needs a `grip_r`). Declare them only where the item has the
  part; a missing `muzzle` / `grip_r` / sights is NOT a failure for such an item (state "no bore" in the report).
- **Sockets are item-specific.** Replace `muzzle`, `grip_r`, `sight_*` by one socket per way the engine attaches,
  places or holds the item. Rule: the id is a lowercase `snake_case` noun for the *role* (where / what attaches),
  never a firearm word; `<role>_<n>` (1-based, in x, then z order) for repeated ones; `pos` = the centre of the
  attachment point on the part's surface, `axis` = the outward direction the attached thing points, `parts` = the
  part(s) it sits on. Tested like `ejection_port`: within `socket_m` (20 mm; `tol_m` per socket) of the surface of
  `parts`. Examples: a placed pad `top_centre` (axis +y, the face a thing stands on); a carry handle `carry` (axis +y,
  the middle of the grip bar); a worn pack `back_mount` (axis -z, the face against the wearer's back); thrown charges
  `charge_1` ... `charge_N` (axis out along the throw / release direction, on each charge body).
- **Joints** only for what really moves; a static item has `"joints": []` and is tested through sockets and mass alone.
  A `slide` must run along z (the bore) unless the joint says `"free_axis": true` (a charge that detaches sideways); a
  `magazine` joint needs its axis in the bore plane (abs(x) <= 0.05), so use `slide` + `free_axis` for other releases.
  No bore is needed unless you declare a `muzzle` socket or a joint that names the bore (`bore.parts`).
- **Chained joints** (e.g. a parentless `lift` slide carrying a child `slide` that owns the geometry; proof:
  `out/blender-hs/it_breach_charges/`): a joint with `"parts": []` is valid when a child joint carries the geometry.
  `Rig.__init__` only builds each joint's own list; a joint's moving group is its parts plus all descendant joints.
  `test_pivots` judges `slide`, `hinge`, `trigger`, `selector` and `magazine` on that whole group
  (`joint_verts(own_only=False)`), so the empty parent passes and reports "no parts" only when the group is empty too.
  `turret_yaw` (own parts only) and `scale` (`_setup_scale` raises) do need parts of their own.
- **`free_axis` on every slide off the bore.** `test_pivots` requires each `slide` axis within 2 deg of z unless that
  joint sets `"free_axis": true`. The flag is per joint, not inherited: set it on every slide in the chain whose axis is
  not z, parentless lift steps included (a vertical lift without it FAILS `pivot:<id>`, even if its child has it).
- **Chained sweeps.** `test_sweeps` poses only the joint under test (ancestors, and every other joint, at value 0 = rest);
  `Rig.collide` moves that joint's group (itself plus descendants, at their own rest) against all other parts,
  ancestors' own parts included. PASS needs `limits` inside the clear range. The combined pose (parent extended while
  the child extends) is never swept, so the child must clear on its own with its parent at rest; a clearance that
  exists only while the parent is displaced is not verified, and a child that needs it fails its own sweep.
- **Clip timing.** `clip_curves` / `clip_keys` key each joint independently from frame 0 by its type: `slide` 0-16
  (out by frame 10, home by 16), `trigger` 0-16, `magazine` / `selector` / `hinge` 0-24, other limited joints 0-64.
  Joints sharing a clip name therefore move together; there is no per-joint delay or start-offset field, and a limited
  joint's clip returns it to rest at its end. The `clip` field only names the clip. For a deploy "one after another" give each joint (or
  chain) its own clip name (`Deploy_1`, `Deploy_2`, ...); each exports as a separate action starting at frame 0 and the
  engine starts them one after another. A chain's lift and slide in one clip start together, not lift first.
- **Mass for placed / non-firearm items.** Parts are solid (fill 1) unless `mass.shell` names them (`shell_of`), so
  decide per part from the real object: a hollow moulded shell, case, tank or tube drawn as a closed solid gets
  `mass.shell` (`f`, `{"wall_m": t}` or `{"bore_d_m": d}`) with the real wall or bore; a genuinely solid moulded disc,
  end block or bar gets no shell entry. Reason: the mesh volume is the drawn outer volume, so a hollow part left solid
  overstates mass by the empty volume, and a solid part shelled would understate it. Record the reason for each
  shelled part in `mass.shell._why` (reported as `shell_why`); for solid parts record it in a `_`-prefixed comment such as
  `mass._density`, never inside `mass.density` (`mass_props` validates every value there as a density class).

Proof: `out/blender-hs/assault_rifle/` (trigger + magazine + charging handle + selector, 8 sockets): 21 / 21 PASS.
Not covered: recoil / spring dynamics, a belt or a round as animated parts, a hinge that carries other joints through
its sweep cases (it is swept at its children's rest pose), IK hand poses (the grip sockets are points, not poses).
`barrel_spin`, `cylinder` and `hinge` are implemented but have not run on a subject yet.

## Scale joints (2026-10-10) — `type: "scale"`

Parts that compress, extend or inflate (coil springs, a rubber bellows, an inflating bladder) scale along ONE principal
axis about the pivot plane. Additive: a rig without a `scale` joint is unchanged.

```jsonc
{"id": "springs_compress", "type": "scale", "parent": null, "pivot": [0, 0.1245, 0], "axis": [0, 1, 0],
 "follow": {"joint": "plate_bounce", "ratio": 1.0},      // or "follow": "plate_bounce"; or no follow + "limits": [lo, hi]
 "length": null,                                         // optional; null or absent = the parts' extent from the pivot plane (null crashed before 2026-10-11)
 "parts": ["spring_fl", "spring_fr", "spring_rl", "spring_rr"]}
```

- **Value** = the far end's displacement along `axis` (m, 0 = rest); node scale along the axis = `1 + value / length`.
  `axis` must be ±x / ±y / ±z (glTF node scale is per local axis); the pivot's coordinate along the axis is the
  anchored end (the other two coordinates do not matter). A scale joint takes no child joints.
- **`follow`**: the value is driven by a limited prismatic joint with the same parent: value = ratio × (master axis ·
  this axis) × master value, so the far end tracks the master's slide. A follower has no clip of its own: it is keyed
  in its master's clip (bounce pad: `Bounce` carries the plate translation and both scale tracks). A free scale joint
  (no follow) takes `limits` in metres of far-end travel and gets clip `Scale` (or `clip`).
- Every pose (sweeps, sockets, regroup, sheet, clips) resolves followers from the master's value.

| test | PASS when |
|---|---|
| `pivot:<scale>` | the parts' near end lies on the pivot plane (≤ `pin_m`, 5 mm), scale ≥ `min_scale` (0.2) over the travel, and the far end tracks: `track_err_mm` = abs(1 − s) × abs(extent − length) ≤ 1 mm (a `length` other than the parts' extent makes the far end lag or lead the master) |
| `sweep:<scale>` | a follower: the master driven over its limits (+ one step past each), the scaled group against everything else with the master's group posed; a free joint: its own limits (2 mm steps). PASS = limits ⊂ clear, no rest collision |
| `sweep:<master>` | unchanged, but its followers move with it (the static-geometry cache is off for that sweep) |
| `regroup` | the test pose drives the master to 0.7 × its limit, so the Blender empties' scale = the numpy pose |
| `export` | `scale_tracks`: each scale joint has a glTF `scale` channel in its clip, sampled min / max = the rig's within 1e-4, off-axis components 1, rest node scale 1 |

The sheet adds `<MASTER> <mm> MM: SCALE s` tiles (side + quarter) at the master's far limit; a free joint gets
`SCALE <id> s`. `<s>_rig.json` lists `resolved_length_m`, `resolved_scale_range` and the `scale_rule` per scale joint.

Proof (scratch copy, `out/score/scalejoint/rig.json` on it_bounce_pad pass 14): springs + skirt follow `plate_bounce`,
all five contacts removed (the 0.081 m spring seats and the skirt / top_plate pair are no longer needed): scale 1 →
0.737 at 30 mm, sweeps clear −2..32 mm, export scale tracks 0.73684..1, 13 / 14 PASS (only `mass`, the existing
owner item). Negative controls (`out/score/scalejoint/neg/`): no scale joints → `top_plate > spring_rl` 2.5 mm at
4 mm; skirt not following → `top_plate > skirt` at 4 mm; springs `length` 0.13 → `track_err_mm` 3.69 and a 2.19 mm hit
at 30 mm. Existing rigs re-run unchanged (apc_8x8 57/57, it_gatling 15/15, pistol 20/20, it_bounce_pad 9/10).
Not covered: a follow on a rotary master, scaling about a non-principal axis, scale joints with children.

## Pose expectations (2026-10-11) — joint `expect`, test `pose:<joint>`

Sweeps prove a joint moves without collision; they do not prove it moves to the RIGHT place. The glide pack's
drum-axis wing hinge swept clear 0..80 deg and put the wing tips at hip height pointing down ("broken arms, not a
glider"); only the orchestrator's look at the sheet caught it. So the function spec states the END POSE first (tip
point, functional-surface normal at the limit; out/blender-hs/FUNCTION-SPEC-BRIEF.md), the joint is solved from it,
and rig.json carries the pose as numbers the harness checks. Additive: a joint without `expect` is untouched.

```jsonc
{"id": "wing_l", "type": "hinge", ..., "limits": [0, 93],
 "expect": {"at": "hi",                          // "hi" (default) / "max" / "lo" / "min" (the limits) or a value (deg / m)
            "point": "socket:wing_tip_2",        // or "<part>" / {"part": p} = posed bbox centre; {"part": p, "vertex": i};
                                                 //    {"part": p, "extreme": [dx, dy, dz]} = the part's REST vertex furthest
                                                 //    along the direction (a tip), posed; {"socket": id} = the socket's pos
                                                 //    carried by its parent joint
            "near": [1.06, 0.54, -0.10], "tol_m": 0.08,           // author metres; tol default 0.05
            "normal": [-0.40, 0.90, 0.16], "normal_of": "fabric_L", "tol_deg": 15,   // optional; tol default 15
            "pose": {"tab_pull": 0.05},          // optional: other joints' values (default all at rest)
            "_why": "FUNCTION.md sec. 0: open spar outboard, 25 deg dihedral, fabric a lifting surface"}}
```

- `expect` may be a list (tests `pose:<joint>.1`, `.2`, ... or each item's own `id`).
- **normal** = the posed part's thinnest principal axis (smallest-variance eigenvector of its vertices: a panel's
  normal), compared sign-free (`normal_off_deg` = acos |n · want|); `normal_of` defaults to the point's part and is
  required when the point is a socket. `normal_flatness` (smallest / middle eigenvalue) is reported: above ~0.5 the
  part is not a panel and the normal means little.
- The numbers come from the spec (the end pose designed first), never read back from a finished rig: a tolerance
  widened until it passes tests nothing.
- Proof (2026-10-11, scratch copies of out/blender-hs/it_glide_pack/rig.json): the solved skew hinge (axis
  [-0.5854, -0.6765, -0.4469], 93 deg) → `pose:wing_l` 0.003 m / 0.15 deg PASS; the old drum-axis hinge (axis
  [-0.8192, 0, -0.5736], 80 deg) sweeps clear but → tip [0.85, 0.29, -0.57], 0.57 m / 50 deg FAIL.
