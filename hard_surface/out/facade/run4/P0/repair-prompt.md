# Pass P0 — facade_brick

You are authoring one procedural module that builds a building through a closed kernel API.
Everything you are allowed to use is documented below. Read it before you write anything.

---

# KERNEL API

# Kernel API — everything an authored module may use

You write ONE file, `subjects/<subject>/<name>.mjs`. It imports the kernel and nothing else:

```js
import * as K from "../../src/kernel/index.mjs";
```

It exports `meta` and `build()`. `build()` returns `parts[]`; each part is
`{ id, solid, zone, role, touches: [ids], embed?: true }`. `id` is unique, `zone` is a key of
`meta.palette`, `role` comes from the closed table below, and `touches` names the parts this
one physically rests on or against. A part that penetrates anything it has NOT named in
`touches` fails `V6_CLASH_UNDECLARED` at ANY depth, so declare every contact you build.
Add `embed: true` only when this part is MEANT to be seated deep inside something it `touches` (a bar socketed into a
landing); it lifts the V6 clash band for those declared pairs alone, and a part may not be 90 % swallowed. Parts are
NEVER booleaned together — one solid per part; the validators union them.

Units are **metres**. `scripts/check-module.mjs <file>` is the gate; run it before you finish.

## Frame

Solid frames are **local**: build each solid at the origin, then place it with `.at([x, y, z])`.
The ASSEMBLY frame is fixed and you do not choose it. **+Y is up, y = 0 is the ground, and the
populated face — windows, door, ironwork — is built facing −Z** (declare `meta.front: "-Z"`).
Depth runs into +Z, so "along the façade" always means x and "off the wall" always means z.
**Handedness: stand on the street looking at the −Z front — YOUR RIGHT IS −x, your left is +x.**
"The door right of the shop window" therefore means door.x < storefront.x.

Never rotate the assembly to frame it: the renderer turns your −Z face onto +X before the camera sees it, because that is
the only side of the solved camera whose horizontals rise toward screen-right the way the target's do. The validators
measure your parts unrotated — build the front on −Z and the picture comes out right.

## Roles — a CLOSED list

Every part carries exactly one `role` from this list; an unknown role fails `V7_ROLE` — a part with an invented role
is a part no rule measures.
`massing`, `roof`, `parapet`, `cornice`, `sill`, `window`, `storefront`, `door`, `awning`,
`signbox`, `ac`, `landing`, `support`, `stringer`, `step`, `railing`, `baluster`, `ladder`,
`rung`, `roof_fixture`, `prop`.
A stair board is a `step`, its string a `stringer`, a handrail a `railing`, an upright a `baluster`, a ladder side a
`ladder`, its bars `rung`s. Window frame AND glass are both `window`; the shop window is `storefront`, not `window`.
Shading is flat cartoon: `meta.shade = { ao: 0.08, upTint: 0.12 }` is the default; palette hex = what the capture shows on the front face; side −12 %.

## What the rules expect of each role
- **Projection off the wall:** sills 0.05–0.15 m, cornice per `layout.json`, awning ≤ 1.5 m.
- **Frames:** a window frame stands **proud** of the brick, glass just behind its front face. There is no reveal rule and no “nothing sits proud” rule — that one was ours.
- **Bearing:** `roof`, `cornice`, `sill`, `awning`, `landing` and `parapet` carry load. No point on their underside
  may be more than **1.0 m** from something beneath it: a roof over a full-depth block is fine, on 1.1 m returns is not.
- **Stairs:** consecutive `step` tops (and the landing tops at each end) rise 0.14–0.20 m, within 0.01 m of each
  other; every `stringer` needs a `railing` over its run, 0.9–1.1 m above the treads.
- **Landings:** the back of a `landing` sits within 0.15 m of the massing; adjacent deck members
  leave no clear slot wider than 0.20 m — a deck is an open grate, not a plate.
- **Ladders:** where a `ladder` reaches a landing, leave a gate-width gap — no `railing` or
  `baluster` within 0.3 m either side of it, from the deck top up to 1.1 m.
- **Bands:** `door` 2.0–2.4 m tall, `railing` 0.9–1.1 m, `parapet` per `layout.json` (`crown.height`,
  inside the 0.3–1.2 m V7 band), a `window` shorter than one storey, an `awning` above the door head.

## Layout, and the three passes
`subjects/<subject>/layout.json` dimensions what `census.json` only counts: every window, trim, deck and ladder as a
**fraction of the face width W and the wall height H** you build in P0. Fractions along W are measured from the
**street-right** edge, which is your massing's **min x**. `V12_LAYOUT` measures it off part AABBs by role, within each
key's own `tol`; a key whose role is not built yet stands down, and a key marked `unverified` is reported but **never
enforced** — nothing gates it, so build what reads and do not read a number into the silence.
**A layout key is a measurement with evidence** (`scripts/measure-target.mjs` writes the file): if a key you need is
missing, say `MISSING KEY <name>` in your CHANGE line — do not guess. Read the number and multiply by your W or H —
never invent a metre. **P0 massing** → **P1 openings + trims** → **P2 ironwork**; the palette is a script
(`scripts/calibrate-palette.mjs`), not a pass. After capture the harness compares your render with the target; a failed
likeness row comes back to you with both images — reopen the responsible parameter, palette work included.

Banned: any other `import`, `Math.random`, `Date`, `fetch`, `performance`, `require`, `process`, `import(`, `eval`, `new Function`. Same text must always give the same mesh — no host state.

## Mini-example (arched doorway + stepped reveal — the arch is a KERNEL demo, not a house style)
```js
import * as K from "../../src/kernel/index.mjs";
export const meta = { class: "building", seed: 1,
  palette: { brick: "#b5412f", trim: "#5a2a22", glass: "#8fc1d6", iron: "#2b2e33" } };
export function build() {
  const W = 8.0, H = 11.0, T = 0.35;                       // wall width, height, thickness (m)
  const parts = [];
  let wall = K.box([W, H, T]);                             // local: x centred, y 0..H, z -T/2..T/2
  const door = K.profile.arch({ w: 1.2, h: 2.4, rise: 0.6, segs: 12 });   // rect + half-round head
  wall = K.cut(wall, K.extrude(door, T + 0.02).at([2.6, 0, -T / 2 - 0.01]));  // through opening
  const reveal = K.extrude(K.profile.offset(door, 0.12), 0.25).at([2.6, 0, T / 2 - 0.25]);
  wall = K.cut(wall, reveal);                              // 12 cm stepped reveal, 25 cm deep
  parts.push({ id: "wall_front", solid: wall, zone: "brick", role: "massing" });
  parts.push({ id: "door_leaf", solid: K.extrude(door, 0.06).at([2.6, 0, -T / 2 + 0.02]),
               zone: "trim", role: "door", touches: ["wall_front"] });
  return parts;
}
```

## Solid constructors
- `K.box([w, h, d])` → solid. x and z **centred** on the origin, y from **0 (bottom) to h**.
- `K.extrude(profile, depth, { holes })` → solid. The 2D profile lies in XY and is pushed along
  **+Z, from z = 0 to z = depth**. `holes` = profiles in the same frame, subtracted. `depth > 0`.
- `K.revolve(profile, segs)` → solid. The profile sweeps around the **local +Y axis**: x is the radius (keep it >= 0),
  y the height, so a profile based at y = 0 gives a solid based at y = 0. `segs` = facets round the full turn,
  integer >= 3.

## Booleans (inputs are never modified; the result is a new solid)
- `K.cut(a, b)` — a minus b.
- `K.union(a, b, ...)` / `K.intersect(a, b, ...)` — arrays are flattened, so
  `K.cut(wall, K.union(tools))` is one call and ~3x faster than twenty sequential cuts.
- `K.cut` throws `V5_THIN` when the cut would leave a wall thinner than **MIN_FEAT = 0.06 m** standing (a 0.32 m
  reveal in a 0.35 m wall throws; a 0.25 m one leaves 0.10 m and passes). It compares bounding boxes, so it is a
  floor, not a guarantee — cut clean through, or leave at least 6 cm of material.

## Solid methods (all transforms return a NEW solid, so a tool can be reused)
- `.at([x, y, z])` — translate, metres. `.mirrorX()` — mirror across the x = 0 plane.
- `.rotY(deg)`, `.rotX(deg)`, `.rotZ(deg)` — rotate about the local axis, degrees, about the
  origin (rotate first, place second).
- `.volume()` → m³. `.aabb()` → `{ min: [x,y,z], max: [x,y,z] }`. `.triCount()` → triangles.
- `.status()` → manifold status; `"NoError"` is the only healthy value. `.genus()` → 0 for a ball,
  1 per through-hole. `.decompose()` → solid[]; length 1 means one connected lump.

## Profiles (2D, metres, returned as `[[x, y], ...]` wound CCW, base at y = 0)

Feed any of these to `K.extrude` / `K.revolve`, or to `K.profile.offset`.
- `K.profile.rect({ w, h })` — centred on x = 0, base at y = 0.
- `K.profile.arch({ w, h, rise, segs })` — rectangle with a segmental head. `h` is the **total** height
  to the crown, `rise` the curved part above the springing line, so the jambs are `h - rise` tall.
  `rise = w / 2` is a semicircle; `rise < h` and `rise <= w / 2`. `segs` = facets across the arc,
  **even integer >= 2**.
- `K.profile.offset(profile, d)` — outward offset by `d` m, **mitred** corners (negative insets).
  This is how a reveal is made: offset the opening profile, extrude it shallower than the wall,
  cut. Deep offsets of concave corners self-intersect and throw `BAD_PROFILE`.
- `K.profile.stepped([{ w, h }, ...])` — stacked centred rectangles from y = 0 up, bottom course
  first. The cornice/plinth section: extrude it ALONG the run of the wall.
- `K.profile.wedge({ w, h, run })` — awning section: a right triangle (legs `run`, `h`) then a
  rectangle out to total width `w`; base at y = 0, left edge sloping (0, 0) → (run, h).
- `K.profile.poly(points)` — raw `[[x, y], ...]`: >= 3 points, simple, non-zero area; CCW out.

## Helper
- `K.repeat(n, pitch, fn)` → `[fn(0, 0), fn(1, pitch), ... fn(n-1, (n-1)*pitch)]`. `fn` returns a
  solid, a part or an array. This is how you write a bay of windows or a run of balusters.

## Failure messages
Every kernel throw is a `KernelError` whose message starts with its code: `KERNEL_UNINIT`,
`BAD_ARG`, `BAD_PROFILE`, `V5_THIN`. Read the code, fix the call, re-run `check-module`.
(`await K.init()` loads the WASM; the harness calls it before `build()` — you never do.)


---

# CURRENT MODULE — subjects/facade_brick/facade.mjs

```js
import * as K from "../../src/kernel/index.mjs";

export const meta = {
  front: "-Z",
  class: "building",
  seed: 1,
  shade: { ao: 0.08, upTint: 0.12 },
  palette: {
    brick: "#b5412f", trim: "#5a2a22", glass: "#8fc1d6", iron: "#2b2e33",
    roof: "#88817c", fixture: "#999f9d",
  },
};

export function build() {
  // Door anchor: 0.127 H is approximately 2.1 m. The solved target face
  // (208 px wide, 550 px high) gives W/H approximately 0.454.
  const W = 7.5, H = 16.5;
  const D = 0.874 * W;                  // layout: massing.depthOverW
  const crownH = 0.031 * H;            // layout: crown.height
  // Missing layout keys: massing.wallThickness, roof.thickness,
  // crown.thickness, roof_fixture.size, roof_fixture.position.
  // These construction dimensions and fixture placements are provisional.
  const T = 0.04 * W, slabH = 0.006 * H;
  const parts = [];
  const add = (id, solid, zone, role, touches) =>
    parts.push({ id, solid, zone, role, touches });

  // Four enclosing walls, with side walls running the entire depth.
  // A separate solid core supplies continuous bearing below the roof.
  const walls = ["wall_front", "wall_back", "wall_left", "wall_right"];
  add("wall_front", K.box([W - 2 * T, H, T]).at([0, 0, T / 2]),
    "brick", "massing", ["wall_left", "wall_right", "block_core", "roof_slab"]);
  add("wall_back", K.box([W - 2 * T, H, T]).at([0, 0, D - T / 2]),
    "brick", "massing", ["wall_left", "wall_right", "block_core", "roof_slab"]);
  add("wall_left", K.box([T, H, D]).at([(W - T) / 2, 0, D / 2]),
    "brick", "massing", ["wall_front", "wall_back", "block_core", "roof_slab"]);
  add("wall_right", K.box([T, H, D]).at([-(W - T) / 2, 0, D / 2]),
    "brick", "massing", ["wall_front", "wall_back", "block_core", "roof_slab"]);
  add("block_core", K.box([W - 2 * T, H, D - 2 * T]).at([0, 0, D / 2]),
    "brick", "massing", [...walls, "roof_slab"]);
  add("roof_slab", K.box([W, slabH, D]).at([0, H, D / 2]),
    "roof", "roof", [...walls, "block_core", "parapet", "vent_box", "pipe_0", "pipe_1"]);

  // Crown height includes the thin slab edge; the parapet is an open ring.
  const parapetH = crownH - slabH;
  const ring = K.cut(
    K.box([W, parapetH, D]),
    K.box([W - 2 * T, parapetH * 3, D - 2 * T]).at([0, -parapetH, 0]),
  );
  add("parapet", ring.at([0, H + slabH, D / 2]),
    "brick", "parapet", ["roof_slab"]);

  const roofY = H + slabH;
  add("vent_box", K.box([0.20 * W, 0.055 * H, 0.20 * W])
    .at([-0.25 * W, roofY, 0.70 * D]), "fixture", "roof_fixture", ["roof_slab"]);
  const pipe = (radius, height) => {
    const section = K.profile.rect({ w: radius, h: height });
    // Move the kernel rectangle onto the nonnegative radial half-plane.
    for (const point of section) point[0] += radius / 2;
    return K.revolve(section, 16);
  };
  add("pipe_0", pipe(0.016 * W, 0.045 * H).at([0.31 * W, roofY, 0.37 * D]),
    "fixture", "roof_fixture", ["roof_slab"]);
  add("pipe_1", pipe(0.015 * W, 0.037 * H).at([0.31 * W, roofY, 0.24 * D]),
    "fixture", "roof_fixture", ["roof_slab"]);
  return parts;
}

```

---

# THIS PASS — P0: massing: closed block, roof, perimeter parapet, roof fixtures

Build the massing only, as a CLOSED BLOCK. The brick middle building is a full-depth box: a front wall, two side walls that run the WHOLE depth, and a back wall. The roof slab bears on all four of them - nothing may overhang more than 1.0 m past something that carries it. The parapet is a PERIMETER WALL standing on the roof slab, not a solid cap: the roof interior stays visible over it from the solved camera, and it is 0.3-1.2 m tall (role parapet). Add the three plain roof solids the target shows - one vent box and two pipes, 3 roof fixtures in total - as simple boxes and a revolve, nothing shaped. No openings, no trims, no ironwork, no colour work beyond putting each part in the right palette zone. Roles for this pass: massing for the walls, roof for the slab, parapet for the perimeter wall, roof_fixture for the vent and the pipes. Dimensions from subjects/facade_brick/layout.json: the W (your massing's x extent) and H (its y extent) you fix here are what the whole building is measured against, and the block's depth is the key massing.depthOverW - read it and multiply, do not invent a metre. Layout keys this pass must satisfy: massing.depthOverW, crown.height. Done looks like: the silhouette of the middle building in image 1, in the right proportions, standing on the ground, closed on every side, with a parapet you can see over. You may reopen any earlier part if the LOOK checklist for it failed; the previous review lists the failed rows.

---

# LIKENESS OF WHAT YOU JUST WROTE, MEASURED AGAINST IMAGE 1

Images 2 and 3 are YOUR render of the module above, at the judged camera and
at three-quarter. Every number below is a script comparing those pixels with
the target's; a FAIL row is as blocking as a validator row.

```
FAIL: 2 likeness row(s) [LK_VALUE].
- LK_VALUE brick_side/front: the return must read exactly as much darker than the front as the target's does (measured 0.886x, limit 0.736-0.836 (target 0.786 +-0.05, measured at runtime))
- LK_VALUE brick_side_strip: zone brick_side_strip renders at the wrong value (measured 1.17x (#9b3727 vs #843b2e), limit 0.85-1.15)
(partial pass: colour rows only — LK_AREA / LK_OVERLAP / LK_VISIBLE are judged on the finished assembly)
```

| zone | role | target | render | value ratio | d hue | whole-picture share r/t (informational) |
|---|---|---|---|---|---|---|
| brick_front | massing | #a85643 V0.659 | #af3f2d V0.686 | 1.04 | 3° | 83.8% / 28.9% |
| brick_side_strip | massing | #843b2e V0.518 | #9b3727 V0.608 | 1.17 | 1° | 83.8% / 13.8% |
| roof | roof | #918680 V0.569 | #8f8883 V0.561 | 0.99 | 4° | 8.6% / 20.2% |
| coping | parapet | #a77b6f V0.655 | #af3f2d V0.686 | 1.05 | 5° | 5.8% / 5.5% |
| glass | window | #80a9ac V0.675 | — | — | — | 0.0% / 1.6% |
| frame | window | #8b7e73 V0.545 | — | — | — | 0.0% / 3.6% |
| sill | sill | #be9589 V0.745 | — | — | — | 0.0% / 5.1% |
| iron_landing_upper | landing | #887768 V0.533 | — | — | — | 0.0% / 1.5% |
| iron_landing_lower | landing | #887568 V0.533 | — | — | — | 0.0% / 4.7% |
| awning | awning | #538c54 V0.549 | — | — | — | 0.0% / 6.1% |
| signbox | signbox | #668865 V0.533 | — | — | — | 0.0% / 3.7% |
| ac | ac | #c0c0bf V0.753 | — | — | — | 0.0% / 0.8% |
| door | door | #81acaf V0.686 | — | — | — | 0.0% / 1.6% |
| storefront | storefront | #85adb2 V0.698 | — | — | — | 0.0% / 3.0% |

front brick #af3f2d vs palette: 0.967x (limit 0.90–1.05); side #9b3727 / front: 0.886x (band 0.736–0.836, = target 0.786 ± 0.05)

LK_AREA — share of the FRONT FACE quad, same classifier both sides:
| family | target share | render share | ratio | verdict |
|---|---|---|---|---|
| brick | 55.8% | 100.0% | 1.79x | FAIL |
| glass | 11.5% | 0.0% | 0.00x | FAIL |
| iron | 12.3% | 0.0% | 0.00x | FAIL |
| green | 19.4% | 0.0% | 0.00x | FAIL |
| grey | 1.0% | 0.0% | 0.00x | FAIL |

target quad: FALLBACK — no measured face quad in subjects/facade_brick/layout.measured.json; Fable r3 audit x 556-764, wall top y 345, ground y 895 at x 556; parallelogram, face slope 0.521 px/px taken from the render's own front quad

LK_VISIBLE — separate blobs of ≥ 50 id-pass px, against the frozen census:
| role | instances seen | census | verdict |
|---|---|---|---|
| window | 0 | 4 | FAIL |
| storefront | 0 | 1 | FAIL |
| door | 0 | 1 | FAIL |
| landing | 0 | 2 | FAIL |
| stringer | 0 | 1 | FAIL |
| ladder | 0 | 2 | FAIL |
| signbox | 0 | 1 | FAIL |
| ac | 0 | 1 | FAIL |
| roof_fixture | 3 | 3 | PASS |

Reopen whichever parameter is responsible — palette hex, a dimension, a
position — and change nothing else.

---

## Rules

- Image 1 is the TARGET: it is the STYLE and the MODEL, not a trace. You are never copying pixels —
  you are building the same building, in the same idiom, at the same proportions.
- Images 2 and 3, when present, are the current render of the module above (target view, three-quarter view).
- Edit ONLY `subjects/facade_brick/facade.mjs`. No other file may change, for any reason.
- Use ONLY `K.*` from the kernel API above. No other import, no raw geometry, no literal vertex arrays,
  no `Math.random`, no `Date`, no `fetch`, no `performance`, no `process`, no `require`, no `eval`.
- Everything is in METRES, and every solid is built in its own local frame and then placed with `.at()`.
- Every part names what it `touches`. A part that touches nothing and stands on nothing fails the gate.
- Run `node scripts/check-module.mjs subjects/facade_brick/facade.mjs` before you finish, and fix what it reports.
- End your final message with exactly one line beginning with `CHANGE: ` describing, factually, what you changed.
- Do not rate your own work and do not describe your result beyond that one clause.