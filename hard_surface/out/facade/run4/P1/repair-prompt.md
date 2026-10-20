# Pass P1 — facade_brick

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
  shade: { ao: 0.08, upTint: 0.12, sideTint: -0.43 },
  palette: {
    brick: "#b5412f", trim: "#5a2a22", glass: "#8fc1d6", iron: "#2b2e33",
    roof: "#88817c", fixture: "#999f9d",
    coping: "#bc8c7e", surround: "#ad8067", canopy: "#528b50",
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
  const T = 0.04 * W, slabH = 0.0048 * H;
  const capH = 0.016 * W;
  const parts = [];
  const add = (id, solid, zone, role, touches) =>
    parts.push({ id, solid, zone, role, touches });

  // P1 measured layout: glass dimensions, bay centres from min x, and rows.
  const paneW = 0.089 * W, paneH = 0.12 * H;
  const headGap = 0.038 * H, rowPitch = 0.283 * H;
  // frame.widthRatio and frame.proud are UNVERIFIED: these are visual choices.
  const frame = 0.012 * W, proud = 0.016 * W;
  const seam = 0.0001 * W; // Sub-millimetre seating at shared surfaces.
  // MISSING KEY storefront.w, storefront.centreX, storefront.bottom,
  // door.w, door.centreX: provisional shop division, not measured layout.
  const openings = [];
  for (const [bay, fraction] of [0.231, 0.808].entries()) {
    for (let row = 0; row < 2; row += 1) {
      openings.push({ id: `window_${bay}_${row}`, role: "window",
        x: -W / 2 + fraction * W,
        y: H - headGap - row * rowPitch - paneH - frame,
        w: paneW, h: paneH });
    }
  }
  openings.push({ id: "shop", role: "storefront", x: 0.15 * W,
    y: 0.037 * H, w: 0.45 * W, h: 0.08 * H });
  openings.push({ id: "entrance", role: "door", x: -0.29 * W,
    y: frame, w: 0.16 * W, h: 0.127 * H - 2 * frame });
  const openingTools = K.union(openings.map((o) =>
    K.box([o.w + 2 * frame - 2 * seam,
      o.h + 2 * frame + (o.role === "door" ? 2 * seam : -2 * seam), T + 2 * proud])
      .at([o.x, o.y - frame + (o.role === "door" ? -seam : seam), T / 2])));

  // Four enclosing walls, with side walls running the entire depth.
  // A separate solid core supplies continuous bearing below the roof.
  const walls = ["wall_front", "wall_back", "wall_left", "wall_right"];
  add("wall_front", K.cut(K.box([W - 2 * T, H, T]).at([0, 0, T / 2]), openingTools),
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
  const parapetH = crownH - slabH - capH;
  const ring = K.cut(
    K.box([W, parapetH, D]),
    K.box([W - 2 * T, parapetH * 3, D - 2 * T]).at([0, -parapetH, 0]),
  );
  add("parapet", ring.at([0, H + slabH, D / 2]),
    "brick", "parapet", ["roof_slab"]);

  // A stepped SECTION, extruded along each wall; the cap bears on the ring.
  // cornice.projection is UNVERIFIED; keep the moulding shallow.
  const capProfile = K.profile.stepped([
    { w: T, h: capH / 2 }, { w: T + proud, h: capH / 2 },
  ]);
  const capY = H + crownH - capH;
  const capEnd = T + proud / 2;
  for (const [name, z] of [["front", T / 2], ["back", D - T / 2]]) {
    add(`coping_${name}`, K.extrude(capProfile, W + proud).rotY(90)
      .at([-(W + proud) / 2, capY, z]), "coping", "cornice",
    ["parapet", "coping_left", "coping_right"]);
  }
  for (const [name, x] of [["left", (W - T) / 2], ["right", -(W - T) / 2]]) {
    add(`coping_${name}`, K.extrude(capProfile, D - 2 * capEnd)
      .at([x, capY, capEnd]), "coping", "cornice", ["parapet"]);
  }

  for (const o of openings) {
    const surround = K.extrude(
      K.profile.rect({ w: o.w + 2 * frame, h: o.h + 2 * frame }),
      T + proud,
      { holes: [K.profile.rect({ w: o.w, h: o.h })
        .map(([x, y]) => [x, y + frame])] },
    ).at([o.x, o.y - frame, -proud]);
    add(`${o.id}_frame`, surround, "surround", o.role, ["wall_front", "block_core"]);
    // Glass fronts are behind the frame; their backs meet the solid interior.
    const glassFront = -proud + frame - seam;
    add(`${o.id}_glass`, K.box([o.w + 2 * seam, o.h + 2 * seam, T - glassFront])
      .at([o.x, o.y - seam, (T + glassFront) / 2]),
    "glass", o.role, [`${o.id}_frame`, "block_core"]);
    if (o.role === "window") {
      add(`${o.id}_sash`, K.box([o.w + 2 * seam, frame, frame])
        .at([o.x, o.y + (o.h - frame) / 2, -proud + frame / 2]),
      "trim", "window", [`${o.id}_frame`, `${o.id}_glass`]);
      add(`${o.id}_sill`, K.box([o.w + 4 * frame, frame, T / 2 + proud])
        .at([o.x, o.y - 2 * frame, (T / 2 - proud) / 2]),
      "surround", "sill", ["wall_front", `${o.id}_frame`]);
      parts[parts.length - 1].embed = true; // Sill tail seated inside the brick.
    }
  }

  // Four separate vertical bands: canopy, sign/AC, then P2's lower deck.
  const awningBottom = 0.163 * H, awningTop = 0.278 * H;
  const signTop = 0.368 * H, signH = 0.075 * H;
  const awningSpan = 0.904 * W;
  // MISSING KEY awning.centreX, awning.depth, signbox.w, signbox.centreX,
  // signbox.depth, ac.size, ac.position: provisional construction choices.
  const canopyX = 0.015 * W, canopyDepth = 0.12 * W;
  const seat = 0.008 * W;
  const awning = K.extrude(K.profile.wedge({
    w: canopyDepth + seat, h: awningTop - awningBottom,
    run: canopyDepth,
  }), awningSpan).rotY(-90)
    .at([canopyX + awningSpan / 2, awningBottom, -canopyDepth]);
  add("shop_awning", awning, "canopy", "awning", ["wall_front", "wall_left"]);
  const signW = 0.61 * W, signX = -0.115 * W, signD = 0.025 * W;
  add("shop_sign", K.box([signW, signH, signD])
    .at([signX, signTop - signH, -signD / 2]),
  "canopy", "signbox", ["wall_front"]);
  const acW = 0.20 * W, acH = signH, acD = 0.09 * W;
  const acX = signX + signW / 2 + acW / 2;
  add("shop_ac", K.box([acW, acH, acD])
    .at([acX, signTop - acH, -acD / 2]),
  "fixture", "ac", ["wall_front", "shop_sign"]);
  // Recessed grille face, with a few broad slats readable at capture scale.
  for (let i = 0; i < 5; i += 1) {
    add(`ac_grille_${i}`, K.box([acW * 0.78, seat, seat])
      .at([acX, signTop - acH + acH * (0.16 + i * 0.15), -acD - seat / 2 + seam]),
    "iron", "ac", ["shop_ac"]);
  }

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

# THIS PASS — P1: openings + trims: 2 bays x 2 rows of windows, storefront, door, cornice, sills, awning, sign box, AC - four separate ground-floor bands

Cut the openings and add every trim that hangs off the face, in ONE pass - the openings and the things that frame them are the same measurement. The target's brick front has 2 BAYS and 2 upper window ROWS - 4 windows, counted and frozen in subjects/facade_brick/census.json, so do not count them off the image - plus one storefront opening across the ground floor (role storefront) and a RECTANGULAR glazed shop entrance beside it (role door; this building has no arch anywhere). Cut each opening through the wall and put the frame and the glass in it, with the FRAME STANDING PROUD of the brick and the glass just behind the frame's front face. There is no reveal rule and no 'nothing sits proud' rule - the target's frames are proud with a lit inner face. are UNVERIFIED in layout.json: nothing gates them, so build what reads and do not pretend a number. Then the trims: a cornice built with K.profile.stepped and extruded ALONG the run of the parapet (role cornice, bearing on the parapet under it); a sill under each UPPER window only, projecting 0.05-0.15 m from the brick (role sill) - the storefront gets a flush stall riser, never a knee-height ledge; one awning over the storefront, built as an extruded K.profile.wedge section, projecting no more than 1.5 m (role awning); the sign box over the awning (role signbox) and the AC unit beside it, on the sign box's street-left side and VISIBLE at the solved camera, not tucked under a deck (role ac). In the target the deck, the sign, the AC and the awning are four SEPARATE bands, and awning.top, awning.bottom, signbox.top and signbox.h are what keeps them apart - read all four and stack them, do not let one swallow another. Every trim carries load: none may overhang more than 1.0 m past the thing it bears on. Layout keys this pass must satisfy: window.w, window.h, window.centreX, window.headBelowCoping, window.rowPitch, storefront.h, door.h, crown.height, signbox.h, signbox.top, awning.span, awning.top, awning.bottom. Every one of them is a fraction of the W or H you built in P0 - read the number off subjects/facade_brick/layout.json and multiply, do not invent a metre. window.centreX is measured from the STREET-RIGHT edge of the face, which is your massing's MIN x. No ironwork yet. Done looks like: from the solved camera the window pairs sit where the target's do, their frames catch the light in front of the brick, the top of the building reads as a thin moulded coping, and the shopfront reads as a wide canopy with a sign band clear above it. You may reopen any earlier part if the LOOK checklist for it failed; the previous review lists the failed rows.

---

# REVIEW OF THE PREVIOUS PASS (P0)

# Fable review — P0 (run 4)
| # | Row | Verdict | Note |
|---|---|---|---|
| 1 | orientation | PASS | front on the right-hand face |
| 2 | door side | n/a | no openings yet |
| 3 | reads as the target | PASS (massing stage) | depth from the measured layout (0.874 W); one repair spent tuning meta.shade.sideTint to the measured side/front ratio — that number should come from calibrate-palette, not a seat (round-4 note) |

---

# LIKENESS OF WHAT YOU JUST WROTE, MEASURED AGAINST IMAGE 1

Images 2 and 3 are YOUR render of the module above, at the judged camera and
at three-quarter. Every number below is a script comparing those pixels with
the target's; a FAIL row is as blocking as a validator row.

```
FAIL: 7 likeness row(s) [LK_VALUE, LK_HUE].
- LK_VALUE glass: zone glass renders at the wrong value (measured 1.20x (#8abbcf vs #80a9ac), limit 0.85-1.15)
- LK_HUE glass: zone glass renders at the wrong hue (measured 13 deg (#8abbcf vs #80a9ac), limit <= 12 deg)
- LK_VALUE ac: zone ac renders at the wrong value (measured 0.80x (#949a98 vs #c0c0bf), limit 0.85-1.15)
- LK_HUE ac: zone ac renders at the wrong hue (measured 100 deg (#949a98 vs #c0c0bf), limit <= 12 deg)
- LK_VALUE door: zone door renders at the wrong value (measured 1.18x (#8abbcf vs #81acaf), limit 0.85-1.15)
- LK_HUE door: zone door renders at the wrong hue (measured 14 deg (#8abbcf vs #81acaf), limit <= 12 deg)
- LK_VALUE storefront: zone storefront renders at the wrong value (measured 1.16x (#8abbcf vs #85adb2), limit 0.85-1.15)
(partial pass: colour rows only — LK_AREA / LK_OVERLAP / LK_VISIBLE are judged on the finished assembly)
```

| zone | role | target | render | value ratio | d hue | whole-picture share r/t (informational) |
|---|---|---|---|---|---|---|
| brick_front | massing | #a85643 V0.659 | #b3412f V0.702 | 1.06 | 3° | 67.8% / 28.9% |
| brick_side_strip | massing | #843b2e V0.518 | #8a2f21 V0.541 | 1.04 | 1° | 67.8% / 13.8% |
| roof | roof | #918680 V0.569 | #8f8883 V0.561 | 0.99 | 4° | 8.3% / 20.2% |
| coping | parapet | #a77b6f V0.655 | #af3f2d V0.686 | 1.05 | 5° | 2.5% / 5.5% |
| glass | window | #80a9ac V0.675 | #8abbcf V0.812 | 1.20 | 13° | 3.0% / 1.6% |
| frame | window | #8b7e73 V0.545 | #96755f V0.588 | 1.08 | 4° | 3.0% / 3.6% |
| sill | sill | #be9589 V0.745 | #a87c64 V0.659 | 0.88 | 8° | 0.1% / 5.1% |
| iron_landing_upper | landing | #887768 V0.533 | — | — | — | 0.0% / 1.5% |
| iron_landing_lower | landing | #887568 V0.533 | — | — | — | 0.0% / 4.7% |
| awning | awning | #538c54 V0.549 | #518a4f V0.541 | 0.99 | 3° | 6.3% / 6.1% |
| signbox | signbox | #668865 V0.533 | #4f874d V0.529 | 0.99 | 0° | 2.0% / 3.7% |
| ac | ac | #c0c0bf V0.753 | #949a98 V0.604 | 0.80 | 100° | 1.3% / 0.8% |
| door | door | #81acaf V0.686 | #8abbcf V0.812 | 1.18 | 14° | 1.1% / 1.6% |
| storefront | storefront | #85adb2 V0.698 | #8abbcf V0.812 | 1.16 | 11° | 2.0% / 3.0% |

front brick #b3412f vs palette: 0.989x (limit 0.90–1.05); side #8a2f21 / front: 0.771x (band 0.736–0.836, = target 0.786 ± 0.05)

LK_AREA — share of the FRONT FACE quad, same classifier both sides:
| family | target share | render share | ratio | verdict |
|---|---|---|---|---|
| brick | 55.8% | 3.7% | 0.07x | FAIL |
| glass | 11.5% | 3.3% | 0.29x | FAIL |
| iron | 12.3% | 6.3% | 0.51x | FAIL |
| green | 19.4% | 86.7% | 4.47x | FAIL |
| grey | 1.0% | 0.0% | 0.00x | FAIL |

target quad: FALLBACK — no measured face quad in subjects/facade_brick/layout.measured.json; Fable r3 audit x 556-764, wall top y 345, ground y 895 at x 556; parallelogram, face slope 0.521 px/px taken from the render's own front quad

LK_VISIBLE — separate blobs of ≥ 50 id-pass px, against the frozen census:
| role | instances seen | census | verdict |
|---|---|---|---|
| window | 4 | 4 | PASS |
| storefront | 1 | 1 | PASS |
| door | 1 | 1 | PASS |
| landing | 0 | 2 | FAIL |
| stringer | 0 | 1 | FAIL |
| ladder | 0 | 2 | FAIL |
| signbox | 1 | 1 | PASS |
| ac | 1 | 1 | PASS |
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