# LISTER — reference → part inventory

Seat: LISTER · model `claude-fable-5-1` · runs once per TARGET, output frozen with the target.
Source: `research/04-image-and-judge.md` technique 6 (part-listing prompt), verbatim rules plus
the reference-mode note below.

---

You are reading one reference of a hard-surface object for low-poly modelling.

Subject: `{{SUBJECT}}`

## Reference

{{REFERENCE_MODE}}

{{REFERENCE}}

## Task

List parts as JSON. Rules:

- `name`: lowercase snake_case, unique, suffix `_1`..`_n` for repeats you can individually see.
- `parent`: the name of the part it is physically attached to, or `"root"`.
- `attach_face`: which face of the parent it sits on: `+x -x +y -y +z -z`.
- `rel_size`: its longest dimension as a fraction of the whole object's height. Estimate.
- `unit_ref`: `true` for exactly one part whose real-world size is standard (a door, a step,
  a storey). State the real size in metres in `unit.unit_m`.
- Do NOT count anything you cannot individually point at; write `"count_uncertain": true`
  on that part instead.

Everything numeric you return is a **hypothesis**. A later measurement pass overwrites any
number it can measure, and a numeric validator rejects the rest. Do not guess precision you
do not have — an honest `count_uncertain` is worth more than a confident wrong count.

## Output

Return JSON only. No prose, no code fence commentary, no trailing text.

```json
{
  "parts": [
    {"name": "mass_left", "parent": "root", "attach_face": "+y", "rel_size": 1.0,
     "count_uncertain": false},
    {"name": "balcony_2", "parent": "mass_right", "attach_face": "+z", "rel_size": 0.22,
     "count_uncertain": false}
  ],
  "unit": {"name": "door_front", "unit_m": 2.0}
}
```
