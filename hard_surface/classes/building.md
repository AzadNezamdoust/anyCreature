# Class rules — building

Appended to the kernel API for every subject whose `subject.json` says `"class": "building"`. Every number below
that the gate enforces is filled in from the config the gate reads (`limits.json`, `KERNEL_LIMIT_DEFAULTS`) when the prompt is assembled.

## Roles — a CLOSED list

Every part carries exactly one `role` from this list; an unknown role fails `V7_ROLE` — a part with an invented role
is a part no rule measures.
`massing`, `roof`, `parapet`, `cornice`, `sill`, `window`, `storefront`, `door`, `awning`,
`signbox`, `ac`, `landing`, `support`, `stringer`, `step`, `railing`, `baluster`, `ladder`,
`rung`, `roof_fixture`, `prop`.
A stair board is a `step`, its string a `stringer`, a handrail a `railing`, an upright a `baluster`, a ladder side a
`ladder`, its bars `rung`s. Window frame AND glass are both `window`; the shop window is `storefront`, not `window`.
Shading is flat cartoon: `meta.shade = { ao: 0.08, upTint: 0.12 }` is the default; palette hex = what the capture shows on the front face; side −12 %.

{PALETTE_ZONE_LIST}

## What the rules expect of each role
- **Projection off the wall:** sills 0.05–0.15 m, cornice per `layout.json`, awning ≤ 1.5 m.
- **Frames:** a window frame stands **proud** of the brick, glass just behind its front face. There is no reveal rule and no “nothing sits proud” rule — that one was ours.
- **Joining the union:** every frame, pane, trim and bar joins the solid union by the **Contact** rule of the kernel
  API — a positive overlap no greater than {INFERRED_CONTACT_FRAC} of its volume, never a millimetre gap.
- **Bearing:** `roof`, `cornice`, `sill`, `awning`, `landing` and `parapet` carry load. No point on their underside
  may be more than **{BEARING_SPAN} m** from something beneath it: a roof over a full-depth block is fine, on 1.1 m returns is not.
- **Stairs:** consecutive `step` tops (and the landing tops at each end) rise {STEP_RISE} m, within {STEP_RISE_VARIATION} m of each
  other; every `stringer` needs a `railing` over its run, {STAIR_RAIL_BAND} m above the treads.
- **Landings:** the back of a `landing` sits within {LANDING_GAP_MAX} m of the massing; adjacent deck members
  leave no clear slot wider than {DECK_GAP_MAX} m — a deck is an open grate, not a plate. Every landing is guarded: a
  `railing` along its open front and a return at each exposed end, its top {RAILING_H} m above the deck, broken only by the gate-width gaps below.
- **Ladders:** where a `ladder` reaches a landing, leave a gate-width gap — no `railing` or
  `baluster` within {LADDER_HEAD_SLACK} m either side of it, from the deck top up to {LADDER_HEAD_BAND} m.
- **Ironwork MUST use the helpers:** the landings, flights and drop ladder are ONE `K.assemble.fireEscape` call (every
  flight lands ON its decks, the only gate is over the drop ladder); the roof ladder is `K.assemble.ladder`. Hand-placed
  decks, stringers and stiles are reported (`V11_HANDBUILT`). Frames: `K.assemble.frame`.
- **Bands:** `door` {DOOR_H} m tall, `railing` {RAILING_H} m, `parapet` per `layout.json` (`crown.height`,
  inside the {PARAPET_H} m V7 band), a `window` shorter than one storey, an `awning` above the door head.

## Layout, and the three passes
`subjects/<subject>/layout.json` dimensions what `census.json` only counts: every window, trim, deck and ladder as a
**fraction of the face width W and the wall height H** you build in P0. Fractions along W are measured from the
**street-right** edge, which is your massing's **min x**. `V12_LAYOUT` measures it off part AABBs by role, within each
key's own `tol`; a key whose role is not built yet stands down, and a key marked `unverified` is reported but **never
enforced** — nothing gates it, so build what reads and do not read a number into the silence.
**A layout key is a measurement with evidence** (`scripts/measure-target.mjs` writes the file): if a key you need is
missing, add one line `MISSING KEY: <name>, <name>` after your CHANGE line — do not guess. Read the number and
multiply by your W or H — never invent a metre. **P0 massing** → **P1 openings + trims** → **P2 ironwork**; the palette
is a script (`scripts/calibrate-palette.mjs`), not a pass. After capture the harness compares your render with the
target; a failed likeness row comes back to you with both images — reopen the responsible parameter, palette work included.

## WORKFLOW v4 — KNOBS
`node scripts/template-building.mjs --subject <id> --knobs` emits the whole building (massing, openings, trims,
shop bands, roof fixtures, fire escape, roof ladder) as one `export const KNOBS` block (metres, author frame) that
`build()` reads. W / H / D are locked to the registration anchor; a keyed knob ranges over its layout key's `tol`,
the rest over `knobPriors` in `classes/building.json`. `scripts/fit.mjs` moves only the `v:` numbers. Edit a number
through its knob, never by a literal in `build()`; the ironwork stays one `K.assemble.fireEscape` + one
`K.assemble.ladder` call.
