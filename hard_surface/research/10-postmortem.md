# 10 — Post-mortem (merged verdict, Fable 5.1, 2026-09-12)

Inputs: `10-postmortem-fable.md` (Fable seat, empty start) and `10-postmortem-astra.md`
(GPT Astra, reasoning high, Codex CLI, shell access). Same brief, no fixes applied. Where the
two disagree it is noted; otherwise both say it.

## Verdict, ranked

1. **Additive-only was never a ruling. It was inherited from an uncited score and then
   frozen by the validators.** `03-landscape.md` ranked the box-only DSL 5/5/5 over CSG with
   no tenement-level comparison; `PLAN.md:9` made it an axiom; `PLAN.md:55-60` still lists
   `lathe, extrudeProfile(+holes)` but `prims.js` never built them; M2's brief allowed "arch
   ≈ box, MVP-STUB"; `grammar.js:359-368` records the moment ("a true arch needs an
   XY-plane extruder … more prim vocabulary than M2 is allowed to add"). V1/V2/V5/V6 then
   defined "a part IS its dims box" (`obb.js:7-8`), so subtraction became impossible without
   a rewrite. Both seats. (Astra adds: polygon construction exists *inside* the compiler —
   loft, stepStack extrusion, chamfers, bored ring — what is missing is **author-facing**
   profiles, cuts and mesh ops.)
2. **The DSL did not stop coordinate authoring, it disguised it.** The shipped spec carries
   17 stair treads at six-decimal `uv`, stringers at `rot 121.391`, and `embed: 6` used as a
   translation. The premise "the LLM never emits a world coordinate" is violated and no
   validator sees it. Fable seat; Astra concurs on the mechanism (`socket` = penetration,
   never subtraction; windows are boxes standing proud).
3. **Correctness was overstated.** Contacts and overlaps are measured on bounding boxes;
   V3's boolean cross-check stayed deferred; `02-correctness.md:214-218` itself warned
   against bounding-box-only structure. Both seats.
4. **The Blind Loop was applied one stage too early.** 11 runs, ≥145 recorded minutes,
   30 judge verdicts for 9 one-edit merges; judges unanimous in 7 of 8 rounds; about half the
   wall-clock lost to avoidable plumbing (junction deletion, missing `.bin`, relative adapter
   paths, scope gaming, stacked merges, occlusion churn) that one dry round would have
   caught. Three same-model judges did not catch a shared misread (r10 "left edge" → all three
   picked the right half). Both seats.
5. **Composition was wrong before topology mattered.** The camera azimuth shows the tan side
   wall while the authored mint side windows sit on `−X`; parapets are whole-footprint slabs.
   Additive geometry could already have fixed these. Astra seat; Fable concurs from the
   stills.
6. **Effort split (estimate, UNVERIFIED as tokens):** ~20 % research, ~40 % harness and
   integration, ~25 % compiler/validators, ~15 % the asset. Astra's figure; Fable's reading
   is the same order.

## What the constraints cost the model
Workers saw one item sentence, never the target, and could edit only the spec inside an
eight-primitive vocabulary. Missing profiles became parameter search. Astra's strength
(writing geometry) was fenced off; the M3 baseline was authored by Opus, not Astra
(README:56). Both seats.

## v2, one paragraph (both seats, same shape)
Hybrid procedural modeller: profile extrusion (with holes) for walls, cornices, awnings,
bulkheads; CSG via `manifold-3d` for reveals, arches and door openings; ordinary meshes for
ironwork and props. Author writes a procedural asset module in local coordinates with named
attachment frames, loops, profiles, cuts; the target image is in the author's context.
Validators keep: finite geometry, units, winding, thickness, budgets, one material,
determinism; contact/penetration measured on real surfaces, not AABBs; support graph per
intended assembly, not one global solid. Loop only for uncertain refinements after a
global likeness review; one judge, more only on disagreement. Delete: the eight-prim
ceiling, single-parent placement for every detail, automatic opening deletion,
full-suite-only gating, 3×3 voting for obvious corrections. First acceptance artifact: one
façade with arched opening, recessed window, shaped cornice, open balcony, with
edit-to-preview time and tokens measured before any new harness layer.

## What stays valid
The relay/model channels (Astra via Codex, Fable judges, Opus implementers), the capture
determinism contract, the frozen-target + camera-solve pair, the scope guard, and the
"validate after every merge" rule. The correctness layer can sit under a richer generator.
