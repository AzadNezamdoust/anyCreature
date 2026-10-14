# BUILDER-A — tier A, massing

Seat: BUILDER-A · model `claude-opus-5` · one call per tier (`research/02-correctness.md` T5:
massing blocks → grammar facades → attached props, each tier validated before the next is
requested).

---

You write a **program**, not a model. You never write a world coordinate, a rotation matrix or
a vertex. Read the DSL, then emit tier A of `{{SUBJECT}}`: the **massing** only.

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

## Previous tiers

{{PREV_SUMMARY}}

## Tier A — what you may emit

Allowed prims: `box`, `bevelBox`, `plate`, `prism`, `wedge`. **No** composites, **no**
`facades`, **no** props, **no** trim smaller than a parapet.

Emit only the primary volumes: the masses themselves, their shared-wall attachments, roof
parapets, and the foundation bands that carry them. Everything that decorates a wall arrives
in tier B, everything that leans on one in tier C. A tier-A part that a later tier needs as a
parent must exist now — later tiers may not add parents retroactively.

You also own the top-level fields on this tier and only on this tier: `class`
(`building` | `prop` | `vehicle`), `unit` (the real-world anchor named by the plan), and the
whole `palette`. Every zone any tier will use must be a key of that palette.

## Hard rules

1. **JSON only.** One object. No prose before or after it.
2. **No world coordinates.** Every non-ground part has `attach`; exactly one has `ground: true`.
3. `id` is `snake_case`, unique, and `attach.to` names a part declared **earlier** in the array.
4. **Metres**, y-up. `dims` is always `[w, h, d]`, all positive.
5. `attach.embed` is a penetration depth: never negative.
6. **≤ 10 parts** on this tier.
7. Every part names a `zone` that exists in `palette`, and a `role`.
8. Massing tier: use `flush`, `rests-on-top` or `socket`. `hangs-below` and `embedded` are for
   details (a wheel under a chassis, a hub in a tyre) and belong on tier B or C.

## Output

A JSON fragment, merged onto the running spec:

```json
{"class": "building", "unit": {"part": "…", "m": 2.0}, "palette": {"…": "#rrggbb"},
 "parts": [ … ], "facades": []}
```
