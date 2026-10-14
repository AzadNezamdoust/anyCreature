# pg/1 — attachment program DSL (M6)

You write a **program**, not a model. You never write a world coordinate, a
rotation matrix, or a vertex. You declare primitives in **metres** and say what
each one is attached to. A deterministic compiler resolves every transform.

Units: metres, y-up, right-handed. One spec compiles to one merged mesh with one
material.

## Top level

```jsonc
{ "schema": "pg/1", "subject": "crate", "seed": 1, "class": "prop",
  "unit": {"part": "door_l", "m": 2.0},        // optional real-world anchor
  "palette": {"wood": "#b98a4e", "band": "#6d5030"},
  "parts": [ ... ] }
```

`palette` maps **zone** names to `#rrggbb`. Every part names a zone; colour is
never a literal on a part, so a palette swap repaints the whole asset.

## Parts

```jsonc
{"id": "lid", "prim": "plate", "dims": [0.64, 0.05, 0.64], "zone": "band",
 "role": "lid",
 "attach": {"to": "body", "face": "+Y", "uv": [0.5, 0.5], "contact": "rests-on-top"}}
```

- `id` — unique. `parts` is a **DAG in file order**: `attach.to` must name a part
  declared *earlier*. Forward or circular references are a V0 failure.
- `prim` — a PRIM or a COMPOSITE (below). Prims:
  | prim | genus | what it is |
  |---|---|---|
  | `box` | 0 | hard box |
  | `bevelBox` | 0 | chamfered box — what stops massing reading as Minecraft cubes |
  | `plate` | 0 | thin slab: coping, sills, treads, seats. `d` is the thickness |
  | `prism` | 0 | n-sided vertical extrusion, capped. `sides` (default 6) |
  | `wedge` | 0 | tapered box: awning, arch head, finial |
  | `tube` | 0 | solid round rod: pipe, rope, handrail. `sides` (default 8) |
  | `ring` | **1** | hollow open ring — bin body, collar, tyre. `wall` = wall thickness; `axis` (`"y"` default, `"x"` for a side-mounted wheel) turns the bore |
  | `stepStack` | 0 | a staircase as ONE solid. `steps` (default 3); treads ascend toward +Z |

  Every prim fills its declared `dims` box exactly, whatever its section, because
  the solver measures contacts from `dims` and never looks at a vertex.
  `ring` is the only genus-1 prim: V1 checks chi against the DECLARED genus
  (chi = 2 - 2*genus), never against 2.
- `dims` — always `[w, h, d]`, metres, all positive. Every prim occupies exactly
  `[-w/2, w/2] x [0, h] x [-d/2, d/2]` in its own local frame: centred in x and
  z, bottom at y = 0.
- `zone` — a key of `palette`.
- `role` — free text; advisory in M0, keys the scale table (V7) later.
- `ground: true` — this part is rooted at the world origin, bottom on y = 0. A
  part has **exactly one of** `attach` or `ground: true`, and at least one part
  must be `ground: true`.
- `bevel` — optional chamfer in metres for `bevelBox` / `plate`.
- `sides`, `steps`, `wall` — optional prim options, as in the table above.
- `axis` — `ring` only: `"y"` (default) or `"x"`, the axis its bore runs along.
  The only prim option that is a string, not a number.
- `params` — composite prims only; overrides that composite's defaults.
- `zones` — composite prims only; maps a composite's own zone keys to palette
  zones (`vent` has a `louvre` key).

## attach

| key | meaning |
|---|---|
| `to` | id of an earlier part — the parent. A **composite** id means its root sub-part; `<composite>.<sub>` names one of its sub-parts |
| `face` | which parent face: `+X -X +Y -Y +Z -Z` |
| `uv` | where on that face, `0..1` along its two tangents. Default `[0.5, 0.5]` |
| `contact` | `flush`, `rests-on-top`, `socket`, `hangs-below`, `embedded` |
| `embed` | intended penetration in metres. Default `0`; `socket` defaults `0.05` |
| `align` | which child extreme sits on the point along `v`: `bottom`, `center` (default), `top` |
| `alignU` | the same along `u`: `start`, `center` (default), `end` |
| `instance` | which instances of a repeated/mirrored parent this child rides: `"all"` (default) or `0` (the anchor only) |
| `rot` | degrees about the attach normal. The only rotation in v0 |

### Face frames

Origin is the face centre. `u` and `v` are the face tangents; `n` is the outward
normal. `v` is up (or the nearest thing to up) on every face, so `uv[1] = 0` is
always the low edge.

| face | n | u | v |
|---|---|---|---|
| `+X` | +X | +Z | +Y |
| `-X` | -X | -Z | +Y |
| `+Y` | +Y | +X | +Z |
| `-Y` | -Y | +X | -Z |
| `+Z` | +Z | -X | +Y |
| `-Z` | -Z | +X | +Y |

### Order of operations, per child

1. The child geometry exists at the origin at `dims`.
2. `rot` degrees about the attach normal `n`.
3. The child's contact face is the one whose outward normal is `-n`. You never
   name it; it follows from `face`.
4. `align` picks which child extreme along `v` is anchored: `bottom` = its `-v`
   extreme, `top` = its `+v` extreme, `center` = its centre. `alignU` does the
   same along `u`: `start` = its `-u` extreme, `end` = its `+u` extreme,
   `center` (the default) = its centre.
5. The parent point is the face centre displaced by `(uv - 0.5) * 2 * halfExtent`
   along `u` and `v`.
6. The child moves so its anchor sits on that point, then slides `-n` by `embed`
   so the two surfaces genuinely overlap.
7. Multiply by the parent's world matrix.

### Contacts

- **`flush`** — side-by-side or face-to-face. Two masses in a terrace:
  `{"to":"mass_l","face":"+X","uv":[0.5,0.0],"contact":"flush","align":"bottom"}`
  — `uv[0]=0.5` keeps their z centres in line, `align:"bottom"` levels their
  bases whatever their heights.
- **`rests-on-top`** — the child's underside sits on the parent's top face.
  Use `face:"+Y"`; `uv` slides it around the roof. A parapet:
  `{"to":"mass_l","face":"+Y","uv":[0.5,0.5],"contact":"rests-on-top"}`.
- **`socket`** — the child pushes *into* the parent by `embed`, so the union is
  connected and no seam can open. A door:
  `{"to":"mass_l","face":"+Z","uv":[0.28,0.0],"contact":"socket","embed":0.08,"align":"bottom"}`.

- **`hangs-below`** — the child hangs UNDER the parent: its `+Y`-most face
  touches the parent's `-Y` face, and `embed` pushes it up into the parent as
  usual. Only legal on `face: "-Y"` (V0 rejects it anywhere else — a part on a
  side face is `flush`). A wheel under a chassis:
  `{"to":"body","face":"-Y","uv":[0.1,0.5],"contact":"hangs-below","embed":0}`.
- **`embedded`** — the child lives INSIDE the parent: its **centre** (not its
  contact face) lands on the parent point, then slides `embed` further in along
  `-n`. Default `embed` 0.05. V2 measures it as a volume: at least 50 % of the
  child must be inside the parent, so this is the one contact where the child
  should be the SMALLER part. A hub inside a tyre's bore:
  `{"to":"tyre","face":"+X","uv":[0.5,0.5],"contact":"embedded","embed":0.06}`
  — an `embed` of half the parent's extent along `n` puts the two centres on top
  of each other.

### What the attach algebra will and will not do

`align` and `alignU` between them anchor the child on both face tangents, so a
child CAN butt its edge to a point on `u` and a part may be wider than the
parent it hangs off. That is new in M6, and it is what makes `railing_open`
possible: its top rail is a child of one 0.06 m post and still spans the whole
railing. The older `railing` composite carries an `infill` web because it was
authored before `alignU` existed; both ship (the frozen M2 baseline references
`railing`).

Still not expressible: a rotation that is not about the attach normal, and a
contact measured on a rotated child's exact rectangle rather than its bounding
interval.

## repeat

```jsonc
"repeat": {"axis": "+Y", "count": 3, "pitch": 3.2}
```

`axis` is **parent-local**; `count` is the total number of instances including
the original; `pitch` is the metre spacing. Instances are `id`, `id#1`, `id#2`.
The compiler writes the resolved world direction into `solved.json`.

## mirror

```jsonc
"mirror": true
```

Duplicates the part at `u -> 1 - u` on the same parent face; the copy is
`id~m`. Combine with `repeat` and every mirrored instance repeats too.

## Children of a repeated or mirrored part

A child of a part that has `repeat` or `mirror` is expanded **once per parent
instance**: one authored railing lands on every balcony, one authored hub sits
in every mirrored tyre. The copies take their parent instance's tail, so the
child of `balcony#1` is `rail#1` and the child of `wheel~m` is `hub~m`.

```jsonc
"attach": {"to": "balcony", "face": "+Y", "uv": [0.5, 0.97], "contact": "rests-on-top"}
// -> a railing on balcony AND on balcony#1

"attach": {"to": "post", "face": "+Y", "uv": [0, 0.5], "contact": "rests-on-top",
           "alignU": "start", "instance": 0}
// -> one top rail, on post 0 - but on post 0 of EVERY balcony
```

`"instance": 0` means the anchor of the parent's own `repeat`/`mirror`. It does
**not** collapse the chain above it: a railing that is already on two balconies
keeps both its top rails. `"all"` is the default and may be written out.

MVP-STUB: a part that is both expanded per parent instance and repeated itself
can generate the same `#k` twice; the compiler appends `@2`, `@3` ... to keep
solved ids unique.

## What the compiler guarantees, and what it does not

Guaranteed: no part can float free of its parent, because a placement is derived
from a contact, never typed in. Every part is rooted to a `ground` part.

Guaranteed too: a facade's openings sit on the face they were declared on, and a
composite's sub-parts stay inside the box you gave it.

**Not** guaranteed: that a rotated part's contact is measured on its exact
rotated rectangle (V2/V6 use the bounding interval), or that an occluder's
footprint is exact rather than its transformed AABB. Both over-report, never
under-report.


## Composite prims

A composite is not geometry. It is a versioned spec fragment in
`src/parts/lib/<name>.json`, expanded into ordinary parts before the solver
runs — so V1–V10 measure a railing's four sub-parts, never a "railing".

| composite | dims | params (defaults) |
|---|---|---|
| `railing` | `[length, height, depth]` | `railThickness .06`, `infillThickness .06`, `postThickness .06`, `postCount 6` |
| `railing_open` | `[length, height, depth]` | `railThickness .06`, `postThickness .06`, `postCount 6` |
| `stairFlight` | **derived** | `steps 6`, `rise .18`, `run .26`, `width .9` |
| `landing` | `[width, height, depth]` | `deckThickness .12`, `railHeight .95`, `railThickness .06` |
| `pipe` | `[diameter, height, diameter]` | `capThickness .08`, `capOverhang .06`, `sides 8` |
| `vent` | `[w, h, d]` | `louvreThickness .06`, `louvreInsetU .14`, `louvreInsetV .2` |
| `awning` | `[width, height, projection]` | `valanceDrop .24`, `valanceThickness .06` |
| `trashcan` | `[diameter, height, diameter]` | `wall .06`, `lidThickness .08`, `lidOverhang .04`, `sides 12` |
| `crate` | `[w, h, d]` | `bandHeight .14`, `bandThickness .06`, `bandInset .08`, `bevel .04` |
| `acUnit` | `[w, h, d]` | `grilleInsetU .1`, `grilleInsetV .1`, `grilleThickness .06`, `bevel .03` |
| `wheel` | `[width, diameter, diameter]` | `hubFrac .7`, `wallFrac .18` |

Zone keys a composite exposes through `zones`: `vent` → `louvre`, `awning` →
`valance`, `trashcan` → `lid`, `crate` → `band`, `acUnit` → `grille`, `wheel` →
`hub`. A key you leave unmapped falls back to the composite's own `zone`.

`railing` and `railing_open` are the same railing twice. `railing` fills the gap
between its rails with a thin `infill` web and stands the posts proud of it;
`railing_open` is bars - bottom rail, posts, top rail, nothing between them.
Pick `railing_open` unless the bars would go sub-pixel at capture, where a web
reads better and V5 will tell you so.

`wheel` is a road wheel: a `ring` tyre with its bore along **X** plus a box hub
`embedded` at its centre. That fixes the vehicle convention the rest of the
toolchain assumes — **left/right is X, length is Z** — because that is the only
way a wheel rolls forwards. V7 measures the wheel radius against the longer
horizontal bound, and V9 mirrors about X.

```jsonc
{"id": "rail_r", "prim": "railing", "dims": [2.4, 0.95, 0.06], "role": "railing",
 "zone": "iron", "params": {"postCount": 8},
 "attach": {"to": "balcony_r", "face": "+Y", "uv": [0.5, 0.97], "contact": "rests-on-top"}}
```

Rules:

- Sub-part ids are `<yourId>.<subId>`. The FIRST sub-part is the root: it takes
  your `attach` (or `ground: true`) plus any `repeat` / `mirror` you wrote.
- A sub-part inherits your `zone` unless the library gives it a zone key, which
  you fill in through `zones`.
- A library fragment may DERIVE its dims from its params (`stairFlight`:
  `[width, steps*rise, steps*run]`). Then the `dims` you write must equal the
  derived value — V0 rejects a spec that says otherwise, so the file never lies
  about the model.
- Composites may nest (`landing` contains three `railing`s), up to 4 deep.
- `role` on a composite still keys the V7 scale table, even though after
  expansion no single sub-part carries that role.
- A composite may be a **parent**. `attach.to: "deck1"` attaches to that
  composite's ROOT sub-part; `attach.to: "deck1.deck"` names a sub-part by id.
  Expansion rewrites both to an ordinary part, so every validator downstream
  measures a box, not a "landing".

## facades — the CGA-lite grammar

You never place a window. You declare a facade on one face of one part, split
that face, tile a band, and say what a named cell contains.

```jsonc
"facades": [
  {"id": "fac_front", "on": "mass", "face": "+Z", "occlude": true, "trimZone": "trim",
   "split": {"axis": "Y", "rule": [["floor", 3.4, "*3"], ["cornice", 0.6]]},
   "tile":  {"floor": {"axis": "X", "rule": [["pier", 0.6], ["bay", 2.6, "*3"], ["pier", 0.6]]}},
   "elements": {
     "bay": {"window": {"dims": [1.3, 1.8], "inset": 0.12, "zone": "glass",
                        "sill": 0.08, "lintel": "flat"}},
     "cornice": {"band": {"h": 0.5, "depth": 0.2, "zone": "trim"}}}}
]
```

- `split.axis` — `"Y"` divides the face up its height, `"X"` across its width.
- Rule entries: `[name, size]` metres · `[name, size, "*N"]` N copies ·
  `[name, "~"]` fill what is left, shared equally between all `~` entries.
- `tile.<bandName>` splits every band of that name the other way. A band with no
  tile entry is one cell.
- `elements.<cellName>` says what that cell contains. A cell with no entry is
  empty — that is what makes `pier`, `wall`, `base` and `cornice` structure
  rather than decoration.
- Cell ids are `<facadeId>/<band><i>/<cell><j>`, 1-based, and derived part ids
  append the element: `fac_front/floor2/bay3/window`.
- An element's `dims` are **face-space** — `w` across the face, `h` up it, the
  depth into it. The compiler maps them onto the child's own x/y/z, so the same
  declaration works on a `+Z` face and on a `-X` one.
- More than one facade may sit on the same face. That is how a ground floor runs
  with `occlude: false` (so a hand-placed awning or stoop cannot blank the very
  cell it belongs to) while the floors above run with `occlude: true`.

### Elements

| element | emits |
|---|---|
| `window` | a `box` socketed `inset` deep, 3 cm proud of the reveal so V6 cannot call it a duplicate. `dims: [w, h]` on the face |
| `door` | the same, standing on the cell floor rather than centred |
| `storefront` | a big window plus an `awning` wedge if `awning: [w, h, d]` is given |
| `sill` | with `sill: <overhang>` on the opening: a `plate` under it |
| `lintel` | with `lintel: "flat"` a `plate` over it; `"arch"` a `wedge`. **MVP-STUB**: a real half-round needs an XY-plane extruder, which M2 does not add |
| `band` | on a `cornice`/`base` cell: a `plate` across the whole cell |

### Occlusion

`occlude` (default true) blanks any tile a solved part already covers. The
grammar runs AFTER attach and AFTER `repeat`/`mirror` expansion, so a balcony
repeated up `+Y` suppresses every tile it lands on (08:G6). A part only counts
as an occluder if it stands **proud** of the face: the next house in a terrace,
flush with the same wall plane, hides nothing and blanks nothing. Blanked tiles
are recorded in `solved.tiles` with `occludedBy`.
