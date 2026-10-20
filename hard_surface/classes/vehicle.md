# Class rules — vehicle

<!-- skip: vehicle/P1 -->
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
tread ring. Windshield and side glass are `window`; lamp lenses `headlight`. Minimum section {MIN_FEAT} m on every axis.
{PALETTE_ZONE_LIST}

<!-- skip: vehicle/P1 -->
## Ground and wheels
- **Wheels touch the ground and nothing else does** (`VEH_GROUND`): only `wheel`/`tyre` parts may reach y = 0, every
  wheel's bottom sits on y = 0, and the chassis underside is {GROUND_CLEARANCE} m above the ground.
- `VEH_WHEELS`: 4 wheel assemblies on 2 axles (wheels sharing a z centre), all the same diameter, diameter over the
  vehicle's longer horizontal extent inside {WHEEL_DIAMETER_FRAC_OF_LENGTH}. A wheel's axis runs along X: revolve a
  disc about Y, then `.rotZ(90)`, then place it.
- Contact is measured: the chassis (or an `axle`) must meet each wheel's inner face; body parts rest on the chassis.

<!-- /skip -->

<!-- skip: vehicle/P1 -->
## Grooves, recesses and glass
- Panel lines, grille slots and recesses are SHALLOW grooves: cut at most {GROOVE_DEPTH_MAX} m into ONE face of a part and leave at least {MIN_FEAT} m of material behind AND beside every groove or slot, so only a panel at least {MIN_PANEL} m thick ({MIN_FEAT} + {GROOVE_DEPTH_MAX}) may be grooved; a thinner cut is reported as `V5_THIN` with its part and tool box.
  Never cut through a part's base, its whole section, or the face it is seated on another part with — a cut that splits a part, or lifts it off its seat, fails `V3_FLOAT`.
- Windows, lamps, the grille and mirrors are built with the K.assemble detail calls (kernel API above): they seat on
  their host face by construction (**Contact** in the kernel API). A hand-placed detail is the `VEH_HANDBUILT` advisory.

V4-5A details: wheels.hub `{ r, ring, cap }`, K.assemble.hoodPanel, seam `door: {…}` (cab-relative), lamp `flush: true`, mirror `head.round`.

## Mirror pairs
`VEH_MIRROR`: every `wheel`, `headlight` and `mirror` assembly has a partner mirrored across x = the body's centre
plane (same y and z bounds, x bounds reflected, within 0.02 m) — build one side and place the other with the negated x,
or `.mirrorX()` the solid. A part that straddles the centre plane must be symmetric about it itself.

<!-- skip: vehicle/P1 -->
## Layout and passes
`subjects/<subject>/layout.json` gives every dimension as a fraction: **L** = your body length (z extent of chassis,
body, cab, hood, bed, bed_wall, tailgate), **W** = their x extent, **H** = the model's top. Fractions along L are
measured from the **nose** (the body's max z) backwards. `V12_LAYOUT` measures them off part AABBs by role; a key whose
role is not built yet stands down; an `unverified` key is reported and never enforced. Read the number and multiply —
never invent a metre; if a key you need is missing add `MISSING KEY: <name>` after your CHANGE line.
**P0 body** (chassis, cab, hood, bed + walls + tailgate, bumpers, wheels) → **P1 details** (windows, grille,
headlights, mirrors). The palette is a script (`scripts/calibrate-palette.mjs`); the target is flat cel
paint, so keep `meta.shade = { ao: 0, upTint: 0 }` and let the script set `sideTint`.
<!-- /skip -->
