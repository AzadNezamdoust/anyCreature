# Kernel API — everything an authored module may use

You write ONE file, `subjects/<subject>/<name>.mjs`. It imports the kernel and nothing else:

```js
import * as K from "../../src/kernel/index.mjs";
```

It exports `meta` and `build()`. `build()` returns `parts[]`; each part is
`{ id, solid, zone, role, touches?: [ids], embed?: true }`. `id` is unique, `zone` is a key of
`meta.palette`, and `role` comes from the class's closed role list (the class rules follow this API). Parts
are NEVER booleaned together — one solid per part; the validators union them.

<!-- skip: vehicle/P1 -->
Units are **metres**. `scripts/check-module.mjs <file>` is the gate; the harness runs it, and the validator chain, on
the module you deliver. Every gate number in this prompt comes from gate configuration `{GATE_DIGEST}`: the kernel
and the validators measure your module under that same configuration.

## Contact — the one policy for `touches` and `embed`
- You do NOT declare contact: the harness measures it. A part flush against another, or sunk into it by a volume
  fraction no greater than {INFERRED_CONTACT_FRAC} of the smaller part, is in contact.
- A deeper penetration fails `V6_CLASH_UNDECLARED` unless it is declared as a SEAT: `touches: [hostId]` together with
  `embed: true`, only for a part MEANT to sit deep inside its host (a bar socketed into a landing). Never write
  `touches` without `embed: true`. A part may not be 90 % swallowed.
- **Every structural part must join the solid union; a positive gap fails V3 even within contact tolerance.** Seat a
  part with a positive overlap no greater than {INFERRED_CONTACT_FRAC} of its volume: a pane 1 mm in front of its
  recess floor "touches" by distance and still comes apart from the body as a separate lump.


## Frame

Solid frames are **local**: build each solid at the origin, then place it with `.at([x, y, z])`.
The ASSEMBLY frame is fixed and you do not choose it: the class rules below say which way is up and which face the
camera is shown. Never rotate the assembly to frame it; the validators measure your parts unrotated.
<!-- class:building -->
**+Y is up, y = 0 is the ground, and the
populated face — windows, door, ironwork — is built facing −Z** (declare `meta.front: "-Z"`).
Depth runs into +Z, so "along the façade" always means x and "off the wall" always means z.
**Handedness: stand on the street looking at the −Z front — YOUR RIGHT IS −x, your left is +x.**
"The door right of the shop window" therefore means door.x < storefront.x.

Never rotate the assembly to frame it: the renderer turns your −Z face onto +X before the camera sees it, because that is
the only side of the solved camera whose horizontals rise toward screen-right the way the target's do. The validators
measure your parts unrotated — build the front on −Z and the picture comes out right.
<!-- /class -->

Banned: any other `import`, `Math.random`, `Date`, `fetch`, `performance`, `require`, `process`, `import(`, `eval`, `new Function`. Same text must always give the same mesh — no host state.

<!-- class:building -->
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
               zone: "trim", role: "door" });
  return parts;
}
```
<!-- /class -->

<!-- skip: vehicle/P1 -->
## Solid constructors
- `K.box([w, h, d])` → solid. x and z **centred** on the origin, y from **0 (bottom) to h**.
- `K.extrude(profile, depth, { holes })` → solid. The 2D profile lies in XY and is pushed along
  **+Z, from z = 0 to z = depth**. `holes` = profiles in the same frame, subtracted. `depth > 0`.
- `K.revolve(profile, segs)` → solid. The profile sweeps around the **local +Y axis**: x is the radius (keep it >= 0),
  y the height, so a profile based at y = 0 gives a solid based at y = 0. `segs` = facets round the full turn,
  integer >= 3.
- `K.taper(profile, h, scaleTop)` → `extrude` whose top (z = h) is scaled about the profile origin by `scaleTop`
  (number or `[sx, sy]`, 0 = apex): frustums, tapered posts.
- `K.hull(...solids | [x, y, z] points)` → convex hull (rounded/bevelled blocks: hull a few boxes). Flat input throws.
- `K.beam(p0, p1, { w, h })` → straight bar p0 → p1, `w` × `h` section square to it (`[a, b]` tapers); 12 tris.

<!-- skip: vehicle/P1 -->
## Booleans (inputs are never modified; the result is a new solid)
- `K.cut(a, b)` — a minus b.
- `K.union(a, b, ...)` / `K.intersect(a, b, ...)` — arrays are flattened, so
  `K.cut(wall, K.union(tools))` is one call and ~3x faster than twenty sequential cuts.
- A cut that leaves a wall thinner than **MIN_FEAT = {MIN_FEAT} m** standing (a 0.32 m reveal in a 0.35 m wall) does
  not throw: the gate reports it as a `V5_THIN` row naming the part, the side and the tool box. It compares bounding
  boxes, so it is a floor, not a guarantee — cut clean through, or leave at least {MIN_FEAT} m of material beside and
  behind every cut. **The thinnest panel you may groove {GROOVE_DEPTH_MAX} m deep is {MIN_PANEL} m** ({MIN_FEAT} +
  {GROOVE_DEPTH_MAX}); a slot field needs {MIN_FEAT} m margins.


## Solid methods (all transforms return a NEW solid, so a tool can be reused)
- `.at([x, y, z])` — translate, metres. `.mirrorX()` — mirror across the x = 0 plane.
- `.rotY(deg)`, `.rotX(deg)`, `.rotZ(deg)` — rotate about the local axis, degrees, about the
  origin (rotate first, place second).
- `.volume()` → m³. `.aabb()` → `{ min: [x,y,z], max: [x,y,z] }`. `.triCount()` → triangles.
- `.status()` → manifold status; `"NoError"` is the only healthy value. `.genus()` → 0 for a ball,
  1 per through-hole. `.decompose()` → solid[]; length 1 means one connected lump.

<!-- skip: vehicle/P1 -->
## Profiles (2D, metres, returned as `[[x, y], ...]` wound CCW, base at y = 0)

Feed any of these to `K.extrude` / `K.revolve`, or to `K.profile.offset`.
- `K.profile.rect({ w, h })` — centred on x = 0, base at y = 0.
<!-- class:building -->
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
<!-- /class -->
- `K.profile.poly(points)` — raw `[[x, y], ...]`: >= 3 points, simple, non-zero area; CCW out.
- `K.profile.fillet(profile, r | r[], segs = 3)` — tangent arc of radius `r` at every corner (`r[]` = one per point,
  0 = sharp); `segs` facets per arc, **1 = chamfer**. Each arc is clamped to half its shorter edge.
- `K.profile.roundRect({ w, h, r, segs })` — rounded rectangle like `rect` (or `{ x: [x0, x1], y: [y0, y1], r, segs }`).

<!-- skip: vehicle/P1 -->
## Helper
- `K.repeat(n, pitch, fn)` → `[fn(0, 0), fn(1, pitch), ... fn(n-1, (n-1)*pitch)]`. `fn` returns a
  solid, a part or an array. This is how you write a bay of windows or a run of balusters.
<!-- /skip -->

<!-- class:vehicle -->
## Details — one call each (K.assemble)
Each call returns ready `parts[]` (push them) seated on its host face by construction, so V3/V5/V6 pass; MEASURED
NUMBERS prints every call READY, arguments in metres. Bounds: `K.span({ x: [lo, hi], y: [lo, hi], z: [lo, hi] })`.
- `pane({ host, face, bounds | poly })` — one glass pane (role window) on the PART `host` (the template's `cab`), face
  "+x" / "-x" / "+z" / "-z"; `poly` = a tapered outline ([z, y] on a flank, [x, y] on ±z); it follows a raked face and cuts
  its own recess (<= {GROOVE_DEPTH_MAX} m) into the host.
- `seam({ host, face, path, closed })` / `handle({ host, face, bounds })` — a door seam line / handle as an inlay in its measured tone.
- `lamp({ body: parts, face: "nose", centre: [x, y], diameter })` — the headlight PAIR (x and its mirror) on the nose.
- `grille({ body: parts, face: "nose", bounds, slots })` — `bounds` = the slot field: dark slot inlays between body-tone bars.
- `mirror({ body: parts, side, centreY, z, head: { w, h }, arm })` — the mirror PAIR: heads on arms seated in the flank.
They refuse (`BAD_ARG`) bounds outside the host, a lamp or grille prouder than the bumper, an arm that meets no flank.
<!-- /class -->

<!-- class:building -->
## Assemblies — ironwork and frames in one call
`K.assemble.*` return ready `parts[]` (`[{ id, solid, role, zone }]`, push them with `parts.push(...)`). Every member is
>= {MIN_FEAT} m and every joint is a sub-millimetre seat the harness reads as contact, so V2/V3/V5/V6 and the class
rows pass by construction. Numbers default from the gate config; `roles`, `zone`/`zones`, `bar`, `idPrefix` override.
- `wallPlanes(parts)` → `{ front, back, streetRight, streetLeft, ground, top, W, H, depth }` of your massing parts,
  metres. Take every wall plane from it; never type one.
- `fireEscape({ wall: parts, centreX, span, depth, levels: [y, ...], dropLadder: { bottom }, idPrefix })` — the whole
  fire escape in one call: a landing at every deck-top `y` in `levels` (bottom first) seated on the front plane of
  `wall`, one flight between each pair whose treads start and end ON the decks (a hatch opens over it), front rails
  with a gate only over the drop ladder, and the drop ladder under the lowest deck ending at `dropLadder.bottom`.
  Optional: `flightWidth`, `railHeight`, `dropLadder.x` / `.width`. It refuses (`BAD_ARG`) a drop ladder that would
  hang past an awning, and a depth too shallow for the flight.
- `ladder({ base: [x, y, z], height, width, rungPitch, face })` — `face: "front"`: base = [centre x, bottom y, plane z],
  built toward −z; `"side"`: base = [side plane x, bottom y, centre z], built toward +x. `width` = stile centres.
- `grate({ w, d, at: [x, topY, backPlaneZ] })`, `landing({ span, depth, at: [x, topY], wall: parts })` and
  `flight({ bottom, top, width, decks })` are the parts `fireEscape` is made of; a flight given `decks` refuses ends
  that are not on them.
- `frame({ w, h, frameWidth, proud, glassInset, sill: { depth, height }, at: [x, glassBottomY, wallFaceZ] })` — four
  members `proud` of the brick, glass behind their front face, optional sill carried on brackets.
```js
const wall = K.assemble.wallPlanes(parts);                   // the massing you already built: front face z, sides, W/H
parts.push(...K.assemble.fireEscape({ wall: parts, centreX: 0.2, span: 4.3, depth: 1.4, levels: [6.58, 10.51],
  dropLadder: { bottom: 4.59 }, idPrefix: "fe" }));          // every number: a MEASURED NUMBERS datum
```
<!-- /class -->

## Failure messages
Every kernel throw is a `KernelError` whose message starts with its code: `KERNEL_UNINIT`,
`BAD_ARG`, `BAD_PROFILE`. Read the code and fix the call. (`V5_THIN` is a gate row, not a throw.)
<!-- skip: vehicle/P1 -->
(`await K.init()` loads the WASM; the harness calls it before `build()` — you never do.)
<!-- /skip -->
