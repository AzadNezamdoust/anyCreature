# Pass P2 — facade_brick

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
    brick: "#b5412f", trim: "#5a2a22", glass: "#80a9ac", iron: "#2b2e33",
    roof: "#88817c", fixture: "#999f9d", ac: "#c0c0bf",
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
  add("block_core", K.box([W - 2 * T + 2 * seam, H + seam, D - 2 * T + 2 * seam]).at([0, 0, D / 2]),
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
  "ac", "ac", ["wall_front", "shop_sign"]);
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
  // P2 construction spec. Only the vertical offsets and roof-ladder location
  // are measured. MISSING KEY landing.span, landing.centreX, stair.run,
  // stair.width, ladder.roof.bottom, ladder.drop.position, ladder.drop.length.
  // landing.depth is UNVERIFIED: choose a 1.4 m deck with a rear walkway
  // and an open stairwell in the upper grate, not a plate across the flight.
  const bar = 0.04, deckD = 1.4, deckW = 5.5;
  const deckMin = -deckW / 2, deckMax = deckW / 2;
  const upperY = openings[0].y - frame - 0.072 * H;
  const lowerY = upperY - rowPitch;
  const axial = [];
  const iron = (id, solid, role, touches = [], axisAligned = true, embed = false) => {
    const part = { id, solid, zone: "iron", role, touches };
    if (embed) part.embed = true;
    parts.push(part);
    if (axisAligned) axial.push(part);
    return part;
  };
  const stairRun = 3.8, stairLoX = stairRun / 2, stairHiX = -stairRun / 2;
  const stairZ = -0.97, stairW = 0.72;
  const riseCount = 26, rise = rowPitch / riseCount, going = stairRun / riseCount;
  const angle = Math.atan2(stairRun, rowPitch) * 180 / Math.PI;
  const flightLength = Math.sqrt(stairRun * stairRun + rowPitch * rowPitch);
  // Sloping members have their local lower end at the origin. Rotate first,
  // then place; the lower/upper endpoints remain inside both deck extents.
  const slope = (y, z) => K.box([bar, flightLength, bar]).rotZ(angle)
    .at([stairLoX, y, z]);
  const dropX = -1.1, dropW = 0.58, dropZ = -deckD - bar / 2;
  const gateMin = dropX - dropW / 2 - 0.3 - bar;
  const gateMax = dropX + dropW / 2 + 0.3 + bar;

  for (const [level, top] of [["lower", lowerY], ["upper", upperY]]) {
    // Edge beams carry the individual grate bars. Only the grate bars have
    // role landing: each one runs back to the brick, including at the hatch.
    iron(`${level}_ledger`, K.box([deckW, bar, bar])
      .at([0, top - 2 * bar, -0.05]), "support");
    iron(`${level}_edge`, K.box([deckW, bar, bar])
      .at([0, top - 2 * bar, -deckD + 0.75 * bar]), "support");
    K.repeat(24, (deckW - bar) / 23, (i, offset) => {
      const x = deckMin + bar / 2 + offset;
      const hatch = level === "upper" && x > stairHiX + going / 2 && x < stairLoX + going;
      const depth = hatch ? 0.60 : deckD;
      iron(`${level}_grate_${i}`, K.box([bar, bar, depth + seam])
        .at([x, top - bar, (-depth + seam) / 2]), "landing", ["wall_front"]);
    });
    // Two full-depth cantilever bearers, one below each end of the grate.
    for (const [end, x] of [["right", deckMin + bar / 2], ["left", deckMax - bar / 2]]) {
      iron(`${level}_bearer_${end}`, K.box([bar, bar, deckD + seam])
        .at([x, top - 3 * bar, (-deckD + seam) / 2]), "support", ["wall_front"]);
      iron(`${level}_return_${end}`, K.box([bar, bar, deckD + seam])
        .at([x, top + 1 - bar, (-deckD + seam) / 2]), "railing", ["wall_front"]);
      K.repeat(2, deckD - bar, (i, offset) =>
        iron(`${level}_${end}_upright_${i}`, K.box([bar, 1, bar])
          .at([x, top - bar / 2, -bar / 2 - offset]), "baluster", [], true, true));
    }
    const rails = level === "lower" ? [[deckMin, gateMin], [gateMax, deckMax]] : [[deckMin, deckMax]];
    for (const [segment, [left, right]] of rails.entries()) {
      iron(`${level}_front_rail_${segment}`, K.box([right - left, bar, bar])
        .at([(left + right) / 2, top + 1 - bar, -deckD + bar / 2]), "railing");
      const count = Math.ceil((right - left) / 0.82);
      K.repeat(count, (right - left) / count, (i, offset) => {
        // End posts already belong to the returns; infill stays within each
        // separate rail segment, leaving the drop-ladder head entirely clear.
        const x = left + (right - left) / (2 * count) + offset;
        iron(`${level}_front_upright_${segment}_${i}`, K.box([bar, 1 + bar, bar])
          .at([x, top - 1.5 * bar, -deckD + bar / 2]), "baluster", [], true, true);
      });
    }
  }

  const stringIds = ["flight_string_back", "flight_string_front"];
  for (const [level, x, top] of [["lower", stairLoX, lowerY], ["upper", stairHiX, upperY]]) {
    iron(`${level}_threshold`, K.box([0.28, bar, stairW + bar])
      .at([x, top - bar, stairZ]), "support", [], true, true);
  }
  for (const [i, z] of [stairZ + stairW / 2, stairZ - stairW / 2].entries()) {
    iron(stringIds[i], slope(lowerY - bar, z), "stringer",
      ["lower_threshold", "upper_threshold"], false);
  }
  K.repeat(riseCount - 1, going, (i, offset) => {
    iron(`flight_step_${i}`, K.box([going + bar, bar, stairW + bar])
      .at([stairLoX - going - offset, lowerY + (i + 1) * rise - bar, stairZ]),
    "step", [...stringIds]);
  });
  iron("flight_handrail", slope(lowerY + 1 - bar, stairZ - stairW / 2),
    "railing", [], false);
  K.repeat(3, stairRun / 2, (i, offset) => {
    const x = stairLoX - offset;
    iron(`flight_upright_${i}`, K.box([bar, 1 + bar, bar])
      .at([x, lowerY - bar + i * rowPitch / 2, stairZ - stairW / 2]),
    "baluster", [stringIds[1], "flight_handrail"]);
  });

  // Drop ladder hangs outside the lower front edge. Its head ends at the
  // grate top; the split guard above it leaves a clear exit onto the deck.
  const dropBottom = lowerY - 0.16 * H;
  for (const [i, x] of [dropX - dropW / 2, dropX + dropW / 2].entries()) {
    iron(`drop_stile_${i}`, K.box([bar, lowerY - dropBottom, bar])
      .at([x, dropBottom, dropZ + seam]), "ladder", ["lower_edge"]);
  }
  const dropRungs = 8;
  K.repeat(dropRungs, (lowerY - dropBottom - 0.25) / dropRungs, (i, offset) =>
    iron(`drop_rung_${i}`, K.box([dropW, bar, bar])
      .at([dropX, dropBottom + 0.12 + offset, dropZ + seam]), "rung"));

  // Street-left is +x. This ladder lies in the SIDE plane, with foot space
  // between the rung line and brick, and no over-coping handholds.
  const roofLadderZ = 0.177 * W, roofLadderX = W / 2 + 0.20;
  const roofLadderTop = H + crownH - 0.037 * H;
  const roofLadderBottom = 0.21 * H, roofLadderW = 0.58;
  for (const [i, z] of [roofLadderZ - roofLadderW / 2, roofLadderZ + roofLadderW / 2].entries()) {
    iron(`roof_stile_${i}`, K.box([bar, roofLadderTop - roofLadderBottom, bar])
      .at([roofLadderX, roofLadderBottom, z]), "ladder");
    K.repeat(2, roofLadderTop - roofLadderBottom - 0.4, (j, offset) =>
      iron(`roof_mount_${i}_${j}`, K.box([0.20 + bar, bar, bar])
        .at([W / 2 + 0.10, roofLadderBottom + 0.18 + offset, z]),
      "support", ["wall_left"]));
  }
  const roofRungs = Math.ceil((roofLadderTop - roofLadderBottom - 0.3) / 0.34);
  K.repeat(roofRungs, (roofLadderTop - roofLadderBottom - 0.3) / (roofRungs - 1), (i, offset) =>
    iron(`roof_rung_${i}`, K.box([bar, bar, roofLadderW])
      .at([roofLadderX, roofLadderBottom + 0.12 + offset, roofLadderZ]), "rung"));

  // Axis-aligned iron members are boxes, so intersecting bounds are exact
  // contacts, including flush welds. Record those joints without fusing solids.
  // Sloping members have explicit contacts above; their AABBs are not solids.
  for (let i = 0; i < axial.length; i += 1) {
    const a = axial[i], ab = a.solid.aabb();
    for (let j = i + 1; j < axial.length; j += 1) {
      const b = axial[j], bb = b.solid.aabb();
      if ([0, 1, 2].every((axis) =>
        Math.min(ab.max[axis], bb.max[axis]) >= Math.max(ab.min[axis], bb.min[axis]) - 1e-9)) {
        if (!a.touches.includes(b.id)) a.touches.push(b.id);
        if (!b.touches.includes(a.id)) b.touches.push(a.id);
      }
    }
  }
  return parts;
}

```

---

# THIS PASS — P2: ironwork: open-grate landings, flight, drop ladder, roof ladder on the SIDE wall

Add the fire escape, OPEN, so daylight passes through it. The frozen count in subjects/facade_brick/census.json is 2 landings, 1 flight of stairs, and 2 ladder assemblies - the roof-access ladder and the drop ladder under the lower landing. Every bar, baluster, tread, stringer, stile and rung is its own part and no two of them are booleaned together. Roles: landing for deck members, support for brackets, stringer for the stair strings, step for the treads, railing for handrails, baluster for the uprights, ladder for the stiles, rung for the rungs. The roof ladder stands on the street-left SIDE wall, 0.18 W behind the front plane, never in front of the face. Bars are 0.04 m; a deck is an open grate - the wall must show through it. The rest of the rules the ironwork has to satisfy: the flight rises INSIDE the landing's x-range, not hung off the outside of the decks; the deck tops sit BELOW the window sills by layout landing.rowY, which is negative - the target's landings do not hang off the sill line; the roof ladder's top stops layout ladder.topBelowCoping under the coping and nothing of it stands above the coping, so no handholds over the roof edge; the back of every landing sits within 0.15 m of the brick; a deck leaves no clear slot wider than 0.20 m between adjacent members; the flight rises 0.14-0.20 m per tread, all risers within 0.01 m of each other, and it carries at least one railing 0.9-1.1 m above the tread line; and the head of a ladder that reaches a landing has a gate-width gap in the railing over it (nothing in the railing family within 0.3 m either side of the ladder, from the deck up to 1.1 m). layout is UNVERIFIED - the scan could not resolve a deck's depth off the still, so nothing gates it; build a deck you could stand on and do not read a number into the silence. Use K.repeat for the balusters, the treads and the rungs, not hand-placed copies, and keep the total under the triangle budget. Where a bar is genuinely seated into a landing, declare embed: true on it and name what it touches; a part that penetrates anything it has NOT named in touches fails the gate. Layout keys this pass must satisfy: landing.rowY, ladder.topBelowCoping, ladder.roof.face, ladder.roof.backFromCorner. Done looks like: the ironwork in image 1 - you can see the wall through the railings, the landings stand under the window sills, the roof ladder climbs the side wall well behind the corner, and you could climb it. You may reopen any earlier part if the LOOK checklist for it failed; the previous review lists the failed rows.

---

# REVIEW OF THE PREVIOUS PASS (P1)

# Fable review — P1 openings + trims (run 4)
| # | Row | Verdict | Note |
|---|---|---|---|
| 1 | orientation | PASS | unchanged |
| 2 | door side | PASS | glazed door street-right |
| 3 | reads as the target | PASS (closest yet) | tall narrow window slots near the corners, sign band + AC + awning band stacked as in the target, storefront low and wide, door short; face reads slightly narrower/taller than the target's; sash bars a nice touch |
Measured: gate PASS, layout PASS (measured keys), likeness clean. One repair spent on glazing/AC palette (should be script-only in P4-less flow: calibrate-palette before the seat, round-4 note). Author reported MISSING KEY for storefront/door/awning/signbox x-positions and sizes — candidates for measure-target.

---

# VALIDATOR REPORT ON WHAT YOU JUST WROTE

```
FAIL: 171 violation(s) [V5].
- V5 lower_ledger: grow "lower_ledger" on z from 0.040 m to 0.060 m — thinner than the building style floor and it disappears at capture (measured 0.040 m on z, limit >= 0.060 m)
- V5 lower_edge: grow "lower_edge" on y from 0.040 m to 0.060 m — thinner than the building style floor and it disappears at capture (measured 0.040 m on y, limit >= 0.060 m)
- V5 lower_grate_0: grow "lower_grate_0" on x from 0.040 m to 0.060 m — thinner than the building style floor and it disappears at capture (measured 0.040 m on x, limit >= 0.060 m)
- V5 lower_grate_1: grow "lower_grate_1" on x from 0.040 m to 0.060 m — thinner than the building style floor and it disappears at capture (measured 0.040 m on x, limit >= 0.060 m)
- V5 lower_grate_2: grow "lower_grate_2" on x from 0.040 m to 0.060 m — thinner than the building style floor and it disappears at capture (measured 0.040 m on x, limit >= 0.060 m)
- V5 lower_grate_3: grow "lower_grate_3" on x from 0.040 m to 0.060 m — thinner than the building style floor and it disappears at capture (measured 0.040 m on x, limit >= 0.060 m)
- … and 165 more of the same class.
```

Fix only this. Change nothing else: no new features, no tidying, no renaming.

---

# LIKENESS OF WHAT YOU JUST WROTE, MEASURED AGAINST IMAGE 1

Images 2 and 3 are YOUR render of the module above, at the judged camera and
at three-quarter. Every number below is a script comparing those pixels with
the target's; a FAIL row is as blocking as a validator row.

```
FAIL: 12 likeness row(s) [LK_VALUE, LK_HUE, LK_AREA, LK_OVERLAP, LK_VISIBLE].
- LK_VALUE iron_landing_upper: zone iron_landing_upper renders at the wrong value (measured 0.31x (#22252a vs #887768), limit 0.85-1.15)
- LK_HUE iron_landing_upper: zone iron_landing_upper renders at the wrong hue (measured 171 deg (#22252a vs #887768), limit <= 12 deg)
- LK_VALUE iron_landing_lower: zone iron_landing_lower renders at the wrong value (measured 0.31x (#22252a vs #887568), limit 0.85-1.15)
- LK_HUE iron_landing_lower: zone iron_landing_lower renders at the wrong hue (measured 167 deg (#22252a vs #887568), limit <= 12 deg)
- LK_AREA brick: family brick covers the wrong share of the FRONT FACE (measured 11.0% vs 55.8% (0.20x), limit within +-30% of the target share)
- LK_AREA glass: family glass covers the wrong share of the FRONT FACE (measured 24.3% vs 11.5% (2.12x), limit within +-30% of the target share)
- … and 6 more of the same class.
- ADVISORY LK_AREA target-quad: every LK_AREA row above is built on the FALLBACK frame, not a measurement (measured FALLBACK — no measured face quad in subjects/facade_brick/layout.measured.json; Fable r3 audit x 556-764, wall top y 345, ground y 895 at x 556; parallelogram, face slope 0.521 px/px taken from the render's own front quad)
```

| zone | role | target | render | value ratio | d hue | whole-picture share r/t (informational) |
|---|---|---|---|---|---|---|
| brick_front | massing | #a85643 V0.659 | #b3412f V0.702 | 1.06 | 3° | 63.6% / 28.9% |
| brick_side_strip | massing | #843b2e V0.518 | #8a2f21 V0.541 | 1.04 | 1° | 63.6% / 13.8% |
| roof | roof | #918680 V0.569 | #8f8883 V0.561 | 0.99 | 4° | 8.6% / 20.2% |
| coping | parapet | #a77b6f V0.655 | #af3f2d V0.686 | 1.05 | 5° | 2.6% / 5.5% |
| glass | window | #80a9ac V0.675 | #7ca4a7 V0.655 | 0.97 | 0° | 2.7% / 1.6% |
| frame | window | #8b7e73 V0.545 | #966e59 V0.588 | 1.08 | 7° | 2.7% / 3.6% |
| sill | sill | #be9589 V0.745 | #a87c64 V0.659 | 0.88 | 8° | 0.1% / 5.1% |
| iron_landing_upper | landing | #887768 V0.533 | #22252a V0.165 | 0.31 | 171° | 0.7% / 1.5% |
| iron_landing_lower | landing | #887568 V0.533 | #22252a V0.165 | 0.31 | 167° | 0.7% / 4.7% |
| awning | awning | #538c54 V0.549 | #518a4f V0.541 | 0.99 | 3° | 6.5% / 6.1% |
| signbox | signbox | #668865 V0.533 | #4f874d V0.529 | 0.99 | 0° | 1.9% / 3.7% |
| ac | ac | #c0c0bf V0.753 | #b0b0af V0.69 | 0.92 | 0° | 1.3% / 0.8% |
| door | door | #81acaf V0.686 | #7ca4a7 V0.655 | 0.95 | 0° | 1.1% / 1.6% |
| storefront | storefront | #85adb2 V0.698 | #7ca4a7 V0.655 | 0.94 | 3° | 2.0% / 3.0% |

front brick #b3412f vs palette: 0.989x (limit 0.90–1.05); side #8a2f21 / front: 0.771x (band 0.736–0.836, = target 0.786 ± 0.05)

LK_AREA — share of the FRONT FACE quad, same classifier both sides:
| family | target share | render share | ratio | verdict |
|---|---|---|---|---|
| brick | 55.8% | 11.1% | 0.20x | FAIL |
| glass | 11.5% | 24.3% | 2.12x | FAIL |
| iron | 12.3% | 2.2% | 0.18x | FAIL |
| green | 19.4% | 57.5% | 2.97x | FAIL |
| grey | 1.0% | 4.9% | 4.66x | FAIL |

target quad: FALLBACK — no measured face quad in subjects/facade_brick/layout.measured.json; Fable r3 audit x 556-764, wall top y 345, ground y 895 at x 556; parallelogram, face slope 0.521 px/px taken from the render's own front quad

LK_VISIBLE — separate blobs of ≥ 50 id-pass px, against the frozen census:
| role | instances seen | census | verdict |
|---|---|---|---|
| window | 4 | 4 | PASS |
| storefront | 1 | 1 | PASS |
| door | 1 | 1 | PASS |
| landing | 1 | 2 | FAIL |
| stringer | 0 | 1 | FAIL |
| ladder | 2 | 2 | PASS |
| signbox | 6 | 1 | PASS |
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