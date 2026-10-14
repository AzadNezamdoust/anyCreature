# REPAIR — solver-feedback re-prompt

Seat: REPAIR · model `claude-opus-5` · ≤ 2 calls per tier.
Source: `research/04-image-and-judge.md` technique 7 (Holodeck's solver-feedback loop, cheap
version): the LLM sees the **validator message only** and re-emits the spec, not the code.

You are shown the fragment and the validator's report. You are shown nothing else — no
reference image, no render, no earlier reasoning, and no commentary from whoever wrote the
fragment. Everything you need to fix it is in the numbers.

---

## The fragment that failed (tier {{TIER}})

```json
{{FRAGMENT}}
```

## Validator report

```
{{REPORT}}
```

## Task

Return the **corrected fragment** — the same shape, every part the fragment had, with only the
declarations the report names changed. Each hint states the move in metres; make that move.

- An orphan is a logic error, not a near miss: re-parent it to the part it is meant to touch,
  or fix the `repeat` / `uv` that walked it off. Do not delete it to silence the check.
- A gap or an over-deep socket is an `embed` / `contact` / `align` mistake. Fix the
  declaration, never the world position — there are no world positions.
- A part under the style floor grows on its thin axis, keeping its attached face.
- A scale violation (door, step rise, railing height, parapet) means the written metres are
  wrong. Write the metres the rule allows.

Do not restructure what the report did not name. Do not add parts. Do not add prose.

## Output

JSON only — the whole corrected fragment:

```json
{"parts": [ … ], "facades": [ … ]}
```
