# Pass P1 — pickup

You are authoring one procedural module that builds a vehicle through a closed kernel API.
Everything you are allowed to use is documented below. Read it before you write anything.

---

# KERNEL API

# Kernel API — everything an authored module may use

You write ONE file, `subjects/<subject>/<name>.mjs`. It imports the kernel and nothing else:

```js
import * as K from "../../src/kernel/index.mjs";
```

It exports `meta` and `build()`. `build()` returns `parts[]`; each part is
`{ id, solid, zone, role, touches?: [ids], embed?: true }`. `id` is unique, `zone` is a key of
`meta.palette`, and `role` comes from the class's closed role list (the class rules follow this API). Parts
are NEVER booleaned together — one solid per part; the validators union them.

Units are **metres**. `scripts/check-module.mjs <file>` is the gate; the harness runs it, and the validator chain, on
the module you deliver.

## Contact — the one policy for `touches` and `embed`
- You do NOT declare contact: the harness measures it. A part flush against another, or sunk into it by a volume
  fraction no greater than 0.02 of the smaller part, is in contact.
- A deeper penetration fails `V6_CLASH_UNDECLARED` unless it is declared as a SEAT: `touches: [hostId]` together with
  `embed: true`, only for a part MEANT to sit deep inside its host (a bar socketed into a landing). Never write
  `touches` without `embed: true`. A part may not be 90 % swallowed.
- **Every structural part must join the solid union; a positive gap fails V3 even within contact tolerance.** Seat a
  part with a positive overlap no greater than 0.02 of its volume: a pane 1 mm in front of its
  recess floor "touches" by distance and still comes apart from the body as a separate lump.

## Frame

Solid frames are **local**: build each solid at the origin, then place it with `.at([x, y, z])`.
The ASSEMBLY frame is fixed and you do not choose it: the class rules below say which way is up and which face the
camera is shown. Never rotate the assembly to frame it; the validators measure your parts unrotated.

Banned: any other `import`, `Math.random`, `Date`, `fetch`, `performance`, `require`, `process`, `import(`, `eval`, `new Function`. Same text must always give the same mesh — no host state.


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
- `K.cut` throws `V5_THIN` when the cut would leave a wall thinner than **MIN_FEAT = 0.04 m** standing (a 0.32 m
  reveal in a 0.35 m wall throws; a 0.25 m one leaves 0.10 m and passes). It compares bounding boxes, so it is a
  floor, not a guarantee — cut clean through, or leave at least 0.04 m of material.

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
`BAD_ARG`, `BAD_PROFILE`, `V5_THIN`. Read the code and fix the call.
(`await K.init()` loads the WASM; the harness calls it before `build()` — you never do.)


# Class rules — vehicle

Appended to the kernel API for every subject whose `subject.json` says `"class": "vehicle"`. Numbers in braces are
filled in from the config the gate reads (`limits.json`, `KERNEL_LIMIT_DEFAULTS`) when the prompt is assembled.

## Frame
- **+Y is up, y = 0 is the ground. LENGTH runs along Z, WIDTH along X.** The NOSE (grille, headlights, hood) faces
  **+Z**; the tailgate faces −Z. The vehicle is centred on x = 0 (the mirror plane). Build each mirror as TWO parts: the head (role mirror, the larger block; mirror.head.w / mirror.head.h) and a separate thin arm (role mirror) joining it to the cab, never one merged block.
- **Declare `meta.front: "+X"`.** For the renderer `front` is the PRESENTED face, not the nose: it turns the declared
  face onto +X before the camera sees it, and `"+X"` is a turn of 0°. So you build in the frame the camera sees — the
  +X flank (doors, near wheels, bed side) faces the camera and rises toward screen-right, and the +Z nose shows on the
  screen-LEFT, exactly as in the target. Never rotate the assembly; the validators measure your parts unrotated.
- Handedness: sitting in the cab facing +Z, YOUR LEFT is +x and your right is −x.

## Roles — a CLOSED list
`chassis`, `body`, `cab`, `hood`, `bed`, `bed_wall`, `tailgate`, `wheel`, `tyre`, `hub`, `axle`, `bumper`,
`headlight`, `grille`, `window`, `mirror`, `prop`. An unknown role fails `V7_ROLE`.
The cab box and its door panels are `cab`; the bed floor is `bed`, its two sides and front bulkhead `bed_wall`, the back
`tailgate`. Each wheel is ONE `wheel` part (the tyre disc); a hub cap on its face is `hub`; `tyre` only for a separate
tread ring. Windshield and side glass are `window`; lamp lenses `headlight`. Minimum section 0.04 m on every axis.

## Ground and wheels
- **Wheels touch the ground and nothing else does** (`VEH_GROUND`): only `wheel`/`tyre` parts may reach y = 0, every
  wheel's bottom sits on y = 0, and the chassis underside is 0.15–0.5 m above the ground.
- `VEH_WHEELS`: 4 wheel assemblies on 2 axles (wheels sharing a z centre), all the same diameter, diameter over the
  vehicle's longer horizontal extent inside 0.1–0.2. A wheel's axis runs along X: revolve a
  disc about Y, then `.rotZ(90)`, then place it.
- Contact is measured: the chassis (or an `axle`) must meet each wheel's inner face; body parts rest on the chassis.

## Grooves, recesses and glass
- Panel lines, door lines, shut lines and recesses are SHALLOW grooves: cut at most 0.02 m into ONE face
  of a part. Never cut through a part's base, through its whole section, or through the face it is seated on another
  part with — a cut that splits a part, or lifts it off its seat, fails `V3_FLOAT` (the model comes apart into pieces).
- Windows are panes SEATED in a recess (or a thin proud slab on the face), never a hole that splits the body and never a
  pane floating a millimetre off the recess — **Contact** in the kernel API: the pane's back face overlaps the recess
  floor by a positive overlap no greater than 0.02 of its volume.

Pane in a recess (windshield on the cab's +Z face; `cab`, `cabFront`, `paneW`, `paneH`, `paneY` are yours):
```js
const recessD = 0.015, paneT = 0.04, seat = 0.0005;   // recess <= 0.02 m, ONE face; seat / paneT = 1.25 % <= 0.02
cab = K.cut(cab, K.box([paneW, paneH, recessD + 0.01]).at([0, paneY, cabFront - recessD + (recessD + 0.01) / 2]));
// the pane's BACK face sits `seat` INSIDE the recess floor (z = cabFront - recessD): positive overlap, never a gap
const pane = K.box([paneW - 0.002, paneH - 0.002, paneT]).at([0, paneY + 0.001, cabFront - recessD - seat + paneT / 2]);
parts.push({ id: "windshield", solid: pane, zone: "glass", role: "window" });
```

## Mirror pairs
`VEH_MIRROR`: every `wheel`, `headlight` and `mirror` assembly has a partner mirrored across x = the body's centre
plane (same y and z bounds, x bounds reflected, within 0.02 m) — build one side and place the other with the negated x,
or `.mirrorX()` the solid. A part that straddles the centre plane must be symmetric about it itself.

## Layout and passes
`subjects/<subject>/layout.json` gives every dimension as a fraction: **L** = your body length (z extent of chassis,
body, cab, hood, bed, bed_wall, tailgate), **W** = their x extent, **H** = the model's top. Fractions along L are
measured from the **nose** (the body's max z) backwards. `V12_LAYOUT` measures them off part AABBs by role; a key whose
role is not built yet stands down; an `unverified` key is reported and never enforced. Read the number and multiply —
never invent a metre; if a key you need is missing add `MISSING KEY: <name>` after your CHANGE line.
**P0 body** (chassis, cab, hood, bed + walls + tailgate, bumpers, wheels) → **P1 details** (windows, grille,
headlights, mirrors, door line). The palette is a script (`scripts/calibrate-palette.mjs`); the target is flat cel
paint, so keep `meta.shade = { ao: 0, upTint: 0 }` and let the script set `sideTint`.


---

# CURRENT MODULE — subjects/pickup/module.mjs

```js
// GENERATED by scripts/template-vehicle.mjs — subject pickup, through P0, inputs 5870ec7c09eed005.
// Generated starting point; edits required by this pass or its LOOK failures are allowed.
// Every dimension below is a layout.json fraction of L, W or H,
// a census count, or a class default (MVP-STUB where a key is unverified or missing). Palette hex are
// placeholders that scripts/calibrate-palette.mjs rewrites from the target.
// Roles (class prior): chassis, cab, hood, bed, bed_wall, tailgate, wheel, tyre, hub, bumper.
// Layout keys due: wheel.diameterOverL, wheel.centreFromFront, wheelbase.overL, height.overL, width.overL, cab.start, cab.end, bed.start, bed.end, hood.top, cab.roof, bedWall.top, bumper.front.top, bumper.front.h, bumper.rear.h.
// Census due: wheels 4, bumpers 2.
import * as K from "../../src/kernel/index.mjs";

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  palette: {
    body: "#808080",
    bed: "#808080",
    tyre: "#808080",
    hub: "#808080",
    bumper: "#808080",
    tread: "#808080",
  },
};

export function build() {
  // L / W / H rule (scripts/template-vehicle.mjs header). Nose at +Z, centred on x = 0 and z = 0.
  const L = 4.8;                   // class default body length (m), refs/pickup_truck.README.md
  const W = 0.412 * L;        // layout: width.overL
  const H = 0.546 * L;        // layout: height.overL
  const zFront = L / 2;
  const fromNose = (fraction) => zFront - fraction * L;
  const seam = 0.001;
  const parts = [];
  // Contact is measured (kernel API, Contact): no part here is seated deep, so none declares touches.
  const add = (id, solid, zone, role) => {
    parts.push({ id, solid, zone, role });
  };
  /** A box spanning x centred on `x`, y0..y1 and z0..z1. */
  const slab = (w, y0, y1, z0, z1, x = 0) => K.box([w, y1 - y0, z1 - z0]).at([x, y0, (z0 + z1) / 2]);

  // ------------------------------------------------------------ wheels + chassis
  const R = 0.198 * L / 2;             // layout: wheel.diameterOverL (diameter over L)
  const axles = [["f", fromNose(0.197)], ["r", fromNose(0.82)]];   // layout: wheel.centreFromFront; wheelbase.overL 0.623 agrees (0.623)
  // class defaults (m): tyre width, sidewall, tread depth, hub radius (x R), hub proud, facets
  const tyreW = 0.3, sidewall = 0.06, treadT = 0.06, hubR = 0.62 * R, hubT = 0.06, segs = 24;
  const bumperTop = 0.368 * H;      // layout: bumper.front.top
  // body underside: the nose face starts on the front bumper's top, never below the wheel tops
  const baseY = Math.max(bumperTop, 2 * R + seam);
  const clearance = 0.3;        // MVP-STUB: unverified key chassis.clearance — class default (m), inside limits.v7.ground_clearance
  // The chassis runs between the wheels' inner faces from the tail to the front wheels' leading edge; every body
  // part rests on it. It stops short of the nose whenever the front bumper can seat on the hood instead, so the far
  // front tyre shows under the front bumper at the solved camera, as in the target (classes/vehicle.json visibleInstances).
  const chassisFront = bumperTop >= baseY - seam ? Math.min(zFront, axles[0][1] + R) : zFront;
  const chassisRear = zFront - L;
  add("chassis", K.box([W - 2 * tyreW + 2 * seam, baseY - clearance, chassisFront - chassisRear]).at([0, clearance, (chassisFront + chassisRear) / 2]), "tyre", "chassis");

  // One wheel = tyre disc (sidewall + core, role wheel) + tread ring (role tyre) + hub disc (role hub).
  // Profiles are [radius, axial]; revolved about Y, .rotZ(90) turns the axis onto X with the outer face at x = 0
  // and the disc running toward -x. Outer face flush with the flank; the inner face seats a seam into the chassis.
  const tyre = K.revolve([[0, 0], [R, 0], [R, sidewall], [R - treadT + seam, sidewall], [R - treadT + seam, tyreW], [0, tyreW]], segs).rotZ(90);
  const tread = K.revolve([[R - treadT, sidewall - seam], [R, sidewall - seam], [R, tyreW], [R - treadT, tyreW]], segs).rotZ(90);
  const hub = K.revolve([[0, 0], [hubR, 0], [hubR, hubT], [0, hubT]], segs).rotZ(90);
  // +x is the cab's left (l); the -x partner is the exact mirror across x = 0 (VEH_MIRROR).
  const sides = [["l", (solid) => solid], ["r", (solid) => solid.mirrorX()]];
  for (const [axle, z] of axles) {
    for (const [side, place] of sides) {
      const id = `${axle}${side}`;
      add(`wheel_${id}`, place(tyre.at([W / 2, R, z])), "tyre", "wheel");
      add(`tread_${id}`, place(tread.at([W / 2, R, z])), "tread", "tyre");
      add(`hub_${id}`, place(hub.at([W / 2 + hubT - seam, R, z])), "hub", "hub");
    }
  }

  // ------------------------------------------------------------ hood + cab (lengths from the nose)
  const cabFront = fromNose(0.327);      // layout: cab.start
  const cabRear = fromNose(0.585);       // layout: cab.end
  const hoodTop = 0.591 * H;         // layout: hood.top
  const cabTop = 1 * H;            // layout: cab.roof (the cab is the tallest part: it realises H)
  add("hood", slab(W, baseY - seam, hoodTop, cabFront - seam, zFront), "body", "hood");
  // MVP-STUB: missing key windshield rake — the cab front is a vertical face
  add("cab", slab(W, baseY - seam, cabTop, cabRear, cabFront), "body", "cab");

  // ------------------------------------------------------------ OPEN bed: floor, side walls, bulkhead, tailgate
  // No lid: from the solved camera you see down into the floor over the near wall.
  const bedFront = Math.min(fromNose(0.594), cabRear - seam);   // layout: bed.start (never into the cab)
  const bedRear = fromNose(1);       // layout: bed.end
  const wallTop = 0.616 * H;         // layout: bedWall.top
  const floorT = 0.1, wallT = 0.08;     // class defaults (m)
  const wallBase = baseY + floorT - seam;
  add("bed_floor", slab(W, baseY - seam, baseY + floorT, bedRear, bedFront), "bed", "bed");
  add("bed_side_l", slab(wallT, wallBase, wallTop, bedRear, bedFront, (W - wallT) / 2), "body", "bed_wall");
  add("bed_side_r", slab(wallT, wallBase, wallTop, bedRear, bedFront, -(W - wallT) / 2), "body", "bed_wall");
  add("bed_bulkhead", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedFront - wallT, bedFront), "bed", "bed_wall");
  add("tailgate", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedRear, bedRear + wallT), "body", "tailgate");

  // ------------------------------------------------------------ bumpers across the full width
  const bumperD = 0.06;          // class default depth (m)
  const frontH = 0.101 * H;         // layout: bumper.front.h
  const rearH = 0.152 * H;          // layout: bumper.rear.h
  const rearTop = 0.368 * H;        // MVP-STUB: unverified key bumper.rear.top — the front bumper's top
  add("bumper_front", slab(W, bumperTop - frontH, bumperTop, zFront - seam, zFront + bumperD), "bumper", "bumper");
  add("bumper_rear", slab(W, rearTop - rearH, rearTop, zFront - L - bumperD, zFront - L + seam), "bumper", "bumper");
  return parts;
}

```

---

# THIS PASS — P1: details: windows, grille, headlights, mirrors, door line

Add the details that read the truck, on the body built in P0. The frozen count in subjects/pickup/census.json is 3 windows (the windshield plus one side window per door, role window, a glass pane seated in a recess at most 0.02 m deep in the cab face, its back overlapping the recess floor - never a hole through the cab), 2 headlights (role headlight, a mirror pair on the nose face either side of the grille) and 2 mirrors (role mirror, a mirror pair on the cab sides, each on a short arm that meets the cab). Add the grille between the headlights (role grille), recessed slots on the nose face, and a door line on each cab side as a shallow groove at most 0.02 m deep cut into the side face only, or a thin proud strip (role cab) - never a cut through the cab, its base or its seat on the chassis. Mirror pairs are exact: place one side and put its partner at the negated x, same y and z. Sizes and positions from subjects/pickup/layout.json: the headlight centres sit at headlight.centreY of H and headlight.offsetX of W either side of the centre plane, each lamp headlight.diameter of W across; the grille slot field is grille.w of W by grille.h of H; the mirror centres sit at mirror.centreY of H and mirror.offsetX of W, each head mirror.head.w of W by mirror.head.h of H on an arm mirror.arm.length of W long; the windshield pane is window.front.w of W wide with its lower edge at window.front.bottom of H; the near side window runs from window.side.start to window.side.end of L from the nose, between window.side.bottom and window.side.top of H. Read the numbers and multiply - do not invent a metre. Every part is at least 0.04 m on every axis, touches the body, and does not reach the ground. Build each mirror as TWO parts: the head (role mirror, the larger block, measured by mirror.head.w and mirror.head.h) and a separate thin arm (role mirror) joining it to the cab; never one merged block. Layout keys this pass must satisfy: headlight.centreY, headlight.offsetX, headlight.diameter, grille.w, grille.h, mirror.centreY, mirror.offsetX, mirror.head.w, mirror.head.h, mirror.arm.length, window.front.w, window.front.bottom, window.side.start, window.side.end, window.side.bottom, window.side.top. Done looks like: from the solved camera the windshield and the near side window read as pale glass in the cab, two round yellow lamps flank a dark grille on the nose at screen-left, and a mirror stands out from each A-pillar. You may reopen any earlier part if the LOOK checklist for it failed; the previous review lists the failed rows.

---

# MEASURED NUMBERS (layout.json + census.json; do not invent others)

- headlight.centreY: 0.483 H (tol +-0.072)
- headlight.offsetX: -0.38 / 0.38 W (tol +-0.057)
- headlight.diameter: 0.143 W (tol +-0.021)
- grille.w: 0.453 W (tol +-0.068)
- grille.h: 0.114 H (tol +-0.02)
- mirror.centreY: 0.688 H (tol +-0.103)
- mirror.offsetX: -0.612 / 0.612 W (tol +-0.092)
- mirror.head.w: 0.126 W (tol +-0.02)
- mirror.head.h: 0.152 H (tol +-0.023)
- mirror.arm.length: 0.049 W (tol +-0.02)
- window.front.w: 0.866 W (tol +-0.13)
- window.front.bottom: 0.633 H (tol +-0.095)
- window.side.start: 0.358 L (tol +-0.054)
- window.side.end: 0.516 L (tol +-0.077)
- window.side.bottom: 0.667 H (tol +-0.1)
- window.side.top: 0.93 H (tol +-0.14)
- census due now: wheels 4, bumpers 2, headlights 2, mirrors 2, windows 3

L is your body length (the z extent of chassis/body/cab/hood/bed/bed_wall/tailgate), W their x extent, H the model's height: a value in L, W or H multiplies those. Fix L, W and H once, in P0.

Use supplied measurements for appearance and labelled defaults for construction; if a required appearance dimension is absent, return MISSING KEY.

---

# CONSTRUCTION DEFAULTS (labelled construction numbers, not target measurements)

- window.recessDepth: 0.015 m — the recess each pane sits in, cut into ONE cab face only; at most 0.02 m
- pane.thickness: 0.04 m — the minimum section; a pane thicker than its recess stands proud of the cab face
- seat.overlap: 0.0005 m — how far a pane, lamp, grille or mirror arm sinks into its host: a positive overlap no greater than 0.02 of the part's volume, never a gap
- grille.slotDepth: 0.015 m — grille slots are grooves cut into the nose face; at most 0.02 m
- doorLine.depth: 0.01 m — the door line is a groove in the cab side face only; at most 0.02 m
- lamp.thickness: 0.04 m — lens disc depth along +Z, the minimum section
- mirror.section: 0.04 m — arm cross-section and head depth along Z, the minimum section

---

# ACCEPTANCE (scripts/likeness.mjs measures these on your render at Image 1's camera; a FAIL row is blocking)

LK_VISIBLE — every instance is its own blob of id-pass pixels at the solved camera, judged from this pass on:

| role | census count | visible instances required | px per instance |
|---|---|---|---|
| wheel | 4 | 3 (the target hides the rest) | >= 50 |
| bumper | 2 | 2 | >= 50 |
| headlight | 2 | 2 | >= 50 |
| mirror | 2 | 2 | >= 50 |
| window | 3 | 2 (the target hides the rest) | >= 50 |

- LK_VALUE: every zone renders at 0.85–1.15 x the target's value (zones: body_side/cab, body_front/hood, bed_inside/bed, glass/window, mirror/mirror, tyre/wheel, tread/tyre, hub/hub, bumper/bumper, headlight/headlight, grille/grille); the body_side face at 0.9–1.05 x its palette hex "body"; body_front/body_side within +-0.05 of the target's own ratio.
- LK_HUE: every zone within 12 deg of the target's hue.
- LK_AREA: each family's share of the front-face quad within +-30 % of the target's share: body (body_side+body_front+bed_inside), glass (glass+mirror), dark (tyre+tread+grille), light (hub+bumper), lamp (headlight).

---

# TRIANGLE BUDGET

- the current module uses 2040 of 4000 triangles; everything you add or change must fit in the remaining 1960.
- prefer K.assemble.* helpers, low revolve/arch segment counts, and K.repeat over hand-placed copies.

---

PREVIOUS REVIEW: UNREVIEWED — no review.md exists for P0, so its LOOK rows were never judged; nothing about the previous pass's look is known to be clean.

---

## Rules

- Image 1 is the TARGET: it is the STYLE and the MODEL, not a trace. You are never copying pixels —
  you are building the same vehicle, in the same idiom, at the same proportions.
- Images 2 and 3, when present, are the current render of the module above (target view, three-quarter view).
- The module is `subjects/pickup/module.mjs`. The harness replaces it with the module you return; no other file changes.
- Use ONLY `K.*` from the kernel API above. No other import. No raw 3D mesh vertices or indices; numeric 2D profiles for K.profile.poly, K.extrude and K.revolve are allowed.
  No `Math.random`, no `Date`, no `fetch`, no `performance`, no `process`, no `require`, no `eval`.
- Everything is in METRES, and every solid is built in its own local frame and then placed with `.at()`.
- A part that touches nothing and stands on nothing fails the gate; contact, seating and `touches` follow the Contact section of the kernel API above.
- The harness runs check-module, the validator chain, the capture and the likeness on what you return.
- Do not rate your own work and do not describe your result beyond the CHANGE clause.

Do not run commands or read files. Reply with the COMPLETE module in one ```js fence, then one line `CHANGE: …`, then optionally one line `MISSING KEY: k1, k2`.