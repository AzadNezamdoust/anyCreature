# Reference-image test: N vs G vs O (owner request, 2026-09-27)

**The question.** Does a builder make a better creature when it gets a
generated multi-view reference sheet than from the text brief alone? And
which generator's sheet helps more: Gemini's or GPT's?

## Settings (the same 10 creatures in each)

| setting | what the builder gets |
|---|---|
| **N** | The text brief `refs/briefs/<c>.md`. The builder draws its own `blueprint.json`, as in every build so far. |
| **G** | The same brief, plus a Gemini-generated turnaround sheet in `reference/` and a `blueprint.json` traced from it by `kit/refs.py`. |
| **O** | The same brief, plus a GPT-generated turnaround sheet, handled the same way. |

**Creatures:** wolf, giant, boar, goblin, raven-wyvern, bear, stag, frog, owl
and crab.

**Everything else is identical across settings:**

- the builder model, Opus 5.5;
- the kit and its gates, `BRIEF.md` stages 0–4;
- the budget: at most 14 stage-1 rounds, and about 70 tool turns with
  resumes allowed;
- no repair loop, so the test measures the effect of the reference alone.

## References

- `refs/gen_refs.py --provider gemini|openai` sends the same prompt to both
  providers, built from `briefs/briefs.json`. It uses the newest image model
  the key can see, and records the model id in `meta_<n>.json`.
- Each creature gets at most 3 attempts per provider. The first sheet that
  ingests cleanly is used:
  - 4 views are found;
  - the front and side heights agree within about 10%.
- Every attempt is recorded. How reliable each provider's sheets are is
  itself a result.
- A G or O builder must read the reference views. The traced
  `blueprint.json` is the stage-1 silhouette target, measured by the kit's
  blueprint overlay IoU. The builder may refine that blueprint only where
  the sheet is inconsistent, and must log it.

## Builds

- 30 fresh builds go in `abc/<id>/<creature>/`. `<id>` is a random neutral
  folder name, and the mapping to the settings is kept in
  `abc/key.json`, which no judge sees.
- The orchestrator stops before the builds start: **the owner switches the
  session effort from max to high first.**

## Blind evaluation

Conditions are hidden behind random labels, and every path a judge sees is
neutral.

1. **Tech gates** from each build's `stage4/techqa.json`.
2. **Identity.** One Fable 5.1 reader per silhouette sheet, scored by
   `harness/identity.py` against `judge/<c>.brief.md`.
3. **Art direction.** A Fable 5.1 seat and an Opus 5.5 seat each see, per
   creature, the three packets labelled A, B and C in random order. Each
   seat scores every packet on the `ART_DIRECTOR.md` contract and ranks the
   three.
4. **Reported per setting:**
   - the mean art-director score;
   - the rank-1 count;
   - the identity pass rate;
   - the gate pass rate;
   - the blocker and major counts;
   - the cost.

## Decision rule

A setting wins when both of these hold:

- its mean score beats each of the others by at least 0.5;
- it ranks first for at least 6 of 10 creatures in both seats.

Otherwise the result is "no clear difference", and the cheapest setting
stays. That threshold is the orchestrator's proposal; the owner can change
it before the evaluation runs.

## Cost (rough)

- Builds: 30 full builds.
- Reviews: two seats over every creature.
- Images: 20–60 sheets, billed to the owner's image APIs.
