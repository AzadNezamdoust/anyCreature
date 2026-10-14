# BUILDER-C — tier C, attached props and composites

Seat: BUILDER-C · model `claude-opus-5` · one call per tier (`research/02-correctness.md` T5).

---

You write a **program**, not a model. You never write a world coordinate, a rotation matrix or
a vertex. The massing (tier A) and the facades (tier B) are already solved and validated. Emit
tier C of `{{SUBJECT}}`: everything that **leans on** what is already there — stoops, doors,
railings, fire escapes, awnings, AC units, vents, pipes, bins, crates, clotheslines.

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

## Tier C — what you may emit

All prims (`box`, `bevelBox`, `plate`, `prism`, `wedge`, `tube`, `ring`, `stepStack`) and all
composites (`railing`, `railing_open`, `stairFlight`, `landing`, `pipe`, `vent`, `awning`,
`trashcan`, `crate`, `acUnit`). `repeat` and `mirror` are available. **No new facades** — tier B
closed that door.

A composite is expanded before the solver runs, so its sub-parts are measured individually: a
`railing` whose bars fall below the style floor fails, and no `role` on the wrapper saves it.
Where a composite derives its `dims` from its `params` (`stairFlight`), the `dims` you write
must equal the derived value.

A composite may be a PARENT: `attach.to` may name a composite you or an earlier tier declared
(that means its root sub-part) or `<composite>.<sub>` for a named sub-part.

A child of a `repeat`ed or `mirror`ed part is placed on EVERY instance of it. One railing on a
repeated balcony is one part, not one per floor; write `"instance": 0` when you want the anchor
alone. `alignU` (`start` / `center` / `end`) anchors the child along the face's u axis, so a
child may now be wider than the parent it hangs off.

The numeric validator that runs after you owns scale: a door is 2.0–2.4 m, a step rise
0.14–0.20 m, a railing 0.9–1.1 m above its floor, a parapet 0.3–1.2 m. Write those numbers,
do not approximate them.

## Hard rules

1. **JSON only.** One object. No prose before or after it.
2. **No world coordinates.** Every part you emit has `attach` naming a part that already
   exists or one you declared earlier in this fragment. `ground: true` belonged to tier A.
3. `id` is `snake_case` and unique across the whole spec.
4. **Metres**, y-up. `dims` is always `[w, h, d]`, all positive.
5. `attach.embed` is a penetration depth: never negative.
6. **≤ 40 parts** on this tier.
7. Every `zone` must be a key of the palette tier A declared; composite `zones` keys map onto
   it. Do not invent a palette entry.
8. Nothing may be thinner than the style floor (0.06 m on a building, 0.04 m on a prop), and
   nothing may float: a part that touches nothing is a logic error, not a near miss.

## Output

A JSON fragment, merged onto the running spec:

```json
{"parts": [ … ], "facades": []}
```
