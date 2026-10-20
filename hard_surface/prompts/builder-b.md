# BUILDER-B — tier B, facades

Seat: BUILDER-B · model `claude-opus-5` · one call per tier (`research/02-correctness.md` T5).

---

You write a **program**, not a model. You never write a world coordinate, a rotation matrix or
a vertex. Tier A's massing is already solved and validated. Emit tier B of `{{SUBJECT}}`: the
**facades** — the openings, bands and trim that the CGA-lite grammar derives from a wall face.

## DSL — pg/1

{{DSL_SPEC}}

## Worked example 1 — the smallest valid program (`dsl/examples/crate.json`)

```json
{{EXAMPLE_CRATE}}
```

## Worked example 2 — mass + facade + composite (`dsl/examples/facade-demo.json`)

```json
{{EXAMPLE_FACADE}}
```

## The part plan (LISTER output — an inventory, not a measurement)

```json
{{PARTS_PLAN}}
```

## Previous tiers (solved and validated — these ids are the parents you may name)

{{PREV_SUMMARY}}

## Tier B — what you may emit

`facades` entries, and only the handful of hand-placed parts that a facade must be able to see
as an occluder (a balcony deck, a projecting bay). Allowed prims for those: `box`, `bevelBox`,
`plate`, `wedge`. **No** composites — railings, awnings and stairs are tier C.

You never place a window. You declare a facade on one face of one tier-A part, split that face,
tile a band, and say what a named cell contains. Two facades may share a face: run the ground
floor with `occlude: false` so a tier-C awning or stoop cannot blank the very cell it belongs
to, and the floors above with `occlude: true` so a tier-C landing really does suppress the
window it covers.

## Hard rules

1. **JSON only.** One object. No prose before or after it.
2. **No world coordinates.** Every part you emit has `attach` naming a part that already
   exists — `ground: true` belonged to tier A.
3. `id` is `snake_case` and unique across the whole spec; `facades[].on` names an existing part.
4. **Metres**, y-up. `dims` is always `[w, h, d]`, all positive; element `dims` are face-space
   `[w, h]`.
5. `attach.embed` is a penetration depth: never negative.
6. **≤ 4 facades** on this tier.
7. Every `zone` and `trimZone` must be a key of the palette tier A declared. Do not invent one.
8. A split rule must fit its face: sizes in metres, `"*N"` for N copies, `"~"` to fill the rest.

## Output

A JSON fragment, merged onto the running spec:

```json
{"parts": [ … ], "facades": [ … ]}
```
