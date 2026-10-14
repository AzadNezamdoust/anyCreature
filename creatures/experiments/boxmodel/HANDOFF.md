# Hand-off notes: box-model experiment (2026-10-05)

## Where things stand

Work is paused by the owner. The current task is raising stage-1 topology and form to AAA level before any detail, colour or rig work.

- **Last commit:** `8cd5405` (v2 concepts and turnaround sheets). Everything after it is local only.
- **Owner asked for "commit and push"**, then paused before anything was staged. The commit is still owed when work resumes.
- **Round two of the four-legged template was stopped mid-run.** `kit/template.py`, `kit/bmkit.py` and `kit/carve.py` compile, but it is not known whether round two left partial edits. Rerun the c4 wolf and bear before trusting them.

## The overall workflow and where it is written down

This file is a status hand-off. The workflow itself lives in these files:

| File | What it holds | Up to date? |
|---|---|---|
| `WORKFLOW.md` | the pipeline end to end, model tiers, lessons | up to the cage method; does not describe the topology template |
| `BRIEF.md` | the builder's contract: stages, gates, topology rules, parts | up to the part-wise base; does not describe the topology template |
| `ART_DIRECTOR.md` | the review contract: blockout and topology review, verdicts | up to the cage method |
| `REPAIR.md` | the one-round repair pass | current |
| `refs/SHEETS.md`, `refs/BUILD.md` | concept and turnaround-sheet generation (GPT only) | current |
| `RESULTS.md` | every blind comparison and its numbers | up to the cage pilot; the c3 and c4 rounds are not written up |

The pipeline as it runs today:

1. **Concept:** GPT draws a single-view shape concept from the brief (`refs/gen_refs.py --concept`).
2. **Sheet:** GPT draws a 2x2 turnaround from the concept; it is oriented, fitted and selected (`refs/orient.py`, `refs/select_sheets.py`).
3. **Guide:** the sheet becomes a hidden part-wise implicit surface (`kit/carve.py`).
4. **Stage 1, cage:** a grey quad cage is built over the guide and checked for silhouette, proportions, part profiles, topology and pose folding. The owner signs off the blockout. This stage is being reworked: per-creature ring lofts are being replaced by a kit-owned topology template per body type (`kit/template.py`).
5. **Stage 2:** logged detail loops and vertex moves.
6. **Stage 3:** separate pieces from the parts library (`kit/parts.py`) and colour.
7. **Stage 4:** rig, idle/move/attack clips, technical checks, glTF export.
8. **Review:** one art-director pass, one repair round, the rest goes to the owner.

Steps 5–8 are proven on the older sets but have not been run on the new cages.

## What the owner said (most recent first)

1. Pause; write hand-off notes.
2. Commit and push.
3. GPT "sol 6.1 high" may be used as an extra seat if wanted (optional; the global rules file still says GPT is image generation only).
4. The topology study is "ok but far from good", "extremely basic", "not even half the quality we need"; the bar is AAA. Two senior-artist reviews were ordered (Fable 5.1 and Opus 5.5).
5. Earlier: too much focus on eyes and small details; form on head, legs and arms is weaker than the concept; no need to copy a reference's topology; no Gemini.

## Method history, in one table

| Set | Method | Result |
|---|---|---|
| `abc/k3` | hand-built, GPT sheets, repair rounds | baseline |
| `abc/c1` | carve + detail | preferred over k3 in 7 of 8 blind comparisons |
| `abc/c2` | quad cage over a carve guide (bear, goblin, wolf) | preferred over c1 in 6 of 6 |
| `abc/c3` | grey cages on a part-wise implicit base, topology gates | goblin and wolf locked, bear not; owner rejected the topology level |
| `abc/c4` | kit-owned four-legged topology template (wolf, bear) | first pass failed sign-off; round two stopped |

## The two artist reviews

Files: `research/topology_aaa_opus.md`, `research/topology_aaa_fable.md`. They agree.

- **Cause:** every part is a ring stack lofted down a bone and bridged. Edges follow bones, not forms; limb sockets are accidental; sections are symmetric ovals; about a third of the triangle budget is used; the gates check cleanliness, not anatomy.
- **Cure:** one hand-designed topology template per body type, with named vertices, fitted onto the guide. Limbs, neck, muzzle, tail and ears grow from socket blocks. Three converging rings at hinges. Brow, jaw, eye and mouth lines are part of the head layout. Plane breaks are placed on purpose. Stage-1 cage of 1300–1800 triangles.

## Four-legged template, first pass (`abc/c4`, sheet `topology_c3_vs_c4.jpg`)

| Gate | Wolf | Bear |
|---|---|---|
| Socket: 8 verts, valence 4, flow ≥ 0.9 | pass | pass |
| Pole share ≤ 0.10 | fail 0.127 | fail 0.145 |
| Hinge ratio 0.4–0.7 | pass | pass |
| Edge ratio ≤ 2.5 | fail 2.85–4.87 | fail 4.35–6.67 |
| Density 0.7–1.6 | fail (torso 0.61, tail 0.67) | fail (head 2.19) |
| Pose fold ≤ 1% per pose | fail (worst 1.22) | fail (worst 2.52) |
| Triangles 1200–2200 | 1380 | 1208 |
| Self-intersection | 0 | 26 pairs |

- **By eye:** the wolf is slightly better than c3 in wireframe (shoulder and haunch masses, sockets, hinge fans, eye loop) but noisier shaded. The bear is not better: ring-stack head and neck, stubby lower legs, flank notch.
- **Old builds:** the c3 builds rerun with identical gate results after the kit changes.

## Round-two fix list (not done)

1. One clean muzzle-head layout that works for a short bear head and a long wolf head; zero self-intersections as a hard gate.
2. Upper-limb masses (scapula and upper arm, haunch and thigh) so limbs swell and taper; fix the bear's stubby lower legs and flank notch.
3. Planarity pass, fixed diagonal rule, straight lengthwise lines; gate on warped quads (over 12 degrees, at most 5% outside hinges). Wolf ruff as two or three stepped planes.
4. Ring spacing by local width; fewer rings on the head, more on trunk and tail.
5. Pose folding under 1%; the pinched fold at the wolf's tail root.
6. Wolf front silhouette match (0.808 against a 0.83 floor), head profile, ears.

Decisions already taken for round two: pole gate becomes share ≤ 0.15 plus a count equal to the template signature; the eye loop stays; limb blocks on trunk columns 4–5; `torso_fill` is opt-in so old builds are unchanged.

## After the four-legged template

1. Owner signs off the template on wolf and bear (nothing in c4 is locked).
2. Blind review with Opus and Sonnet; GPT sol 6.1 high as an optional third seat.
3. Two-legged template (16-side torso with crotch strip, face layout, palm and thumb, foot ball ring), then rebuild the goblin.
4. Only then: stages 2–4 (detail, parts, colour, rig), and the other eight creatures from the v2 sheets.

## Open owner decisions

- Sign-off on the template look once round two lands.
- Which library parts in `parts_demo/parts_sheet.jpg` are approved.
- Whether limbs may be separate overlapping pieces at shoulder and hip (both reviews advise against).
- Whether to change the global rules file to allow GPT beyond image generation.

## Known kit problems

- Four-legged base: the torso is almost zero width under the limb roots unless `torso_fill` is on; the bear's hind-leg profile got worse in the last base change.
- The giant fails on the part-wise base (head buried under the shoulders).
- Goblin c3: mitten hands, faceted skull, slab feet; several waivers listed in its `NOTES.md`.
- Pose-fold measure rewards small crease faces and does not say where the folds are.
- `abc/c3/*/part_guide.npz` are stale caches (left in place; the cache key no longer matches).

## Commit checklist for whoever resumes

1. Rerun `abc/c4/wolf` and `abc/c4/bear` to confirm the kit runs; run `kit/regress.py <tag> abc/c3`.
2. Run `harness/synccheck.py` (no token counts, timings, field-report wording or local user paths in committed files).
3. Stage with explicit pathspecs, never the whole tree. Modified tracked files: `ART_DIRECTOR.md`, `BRIEF.md`, `RESULTS.md`, `WORKFLOW.md`, `kit/bmkit.py`, `kit/carve.py`, `kit/run.py`, `refs/BUILD.md`, `refs/accept.py`, `refs/gen_refs.py`, `refs/select_sheets.py`.
4. New files worth committing: `kit/parts.py`, `kit/regress.py`, `kit/template.py`, `kit/template_signatures.json`, `parts_demo/`, `research/`, `abc/c2`, `abc/c3`, `abc/c4`, the gallery sheets in the experiment root, `judge/results/ad_c2c1_*`, this file.
5. Many other untracked files are render outputs from older sets (`abc/c1`, `k3`, `t7`, `w4`, `opus/`, `fable/`, `kit/selftest`); decide with the owner whether those go in.
6. Push goes over SSH to the `github-new` remote alias; no force-push.

## Standing rules

- Models: Opus 5.5 and Sonnet 5.5 for all work; Fable 5.1 only when the owner asks or for a tie-break; no Haiku; no Gemini.
- One judge per visual gate; owner-called reviews run Opus and Sonnet blind, then reconciled; one repair round.
- Commits and pushes only when the owner asks. No permanent deletes, force-pushes or history rewrites.
- Scratch output goes to `out/boxmodel/` (ignored by git).
