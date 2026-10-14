# Turnaround image generation A/B — GPT vs Gemini, sheet vs per-view (orchestrator Opus 5.5, 2026-09-27)

Owner: "try gemini as well, because 3d model problems can be from image gen multiple view". Question: which generator and
which method give a turnaround that describes ONE object — the concept's — so the modeller is not chasing contradictions.

## Protocol
- Subjects: tractor, school_bus, fire_truck, forklift, icecream_van (final concepts; ambulance / garbage_truck wait for
  their concept fixes). Same concept as the input image, one byte-identical prompt template for both generators (the
  frozen STYLE with "true orthographic elevation", the concept's parts and colours, the measured L : W : H, the view
  conventions and the projection rules of RUNBOOK §0), ONE attempt per call, no cherry-picking; 50 calls, 0 failures.
- GPT: Codex CLI 0.158.0-alpha.2.1, `-m gpt-6-astra`, built-in image_gen (C2PA: "gpt-image"), concept via `-i`.
- Gemini: Antigravity `agy` 1.2.11, agent `gemini-3.8-flash-high`, `generate_image` with the concept as `ImagePaths`
  (C2PA lists it as an input ingredient; the image model is not exposed — "Google Generative AI").
- Methods: SHEET = one image, 2 × 2 (side, front, rear, top), split on the gutters; VIEWS = one image per view.
  Normalised like the live sets (`scripts/v7/normalize-views.mjs`, e12464f). Files: out/imagegen-ab/<s>/.
- Metric: `scripts/v7/hull.mjs` (eaf657e; research/v7/HULL-BASELINE.md): viewOnly = share of a view's foreground the
  other views carve away (cross-view contradiction; worst view shown), conceptOnly = share of the concept's foreground
  outside the views' visual hull, in ≥ 20 px blobs (view-vs-concept contradiction; a consistent set has 0), concept IoU of
  the hull, residual = largest registration |W / L / H| (the doctor's ±3 % rows). "live" = the current curated GPT set
  (several attempts + proportion drafts per view).

## Results (hull.mjs, one attempt each)
| subject | worst viewOnly % live / gpt-sheet / gpt-views / gemini-sheet / gemini-views | conceptOnly % (same order) |
|---|---|---|
| tractor | 12.4 / 14.6 / 18.4 / 13.7 / 35.0 | 5.4 / 4.8 / 10.8 / 5.0 / 20.2 |
| school_bus | 4.0 / 5.4 / 6.0 / 4.3 / 26.9 | 2.9 / 1.6 / 14.5 / 1.6 / 4.8 |
| fire_truck | 5.0 / 12.8 / 12.7 / 14.1 / 8.0 | 3.3 / 3.0 / 6.8 / 2.4 / 1.2 |
| forklift | 13.8 / 11.1 / 14.0 / 7.1 / 20.6 | 7.4 / 8.6 / 8.5 / 4.5 / 15.6 |
| icecream_van | 7.5 / 11.3 / 7.5 / 7.0 / 48.8 | 4.5 / 3.9 / 9.5 / 1.9 / 6.9 |
| **mean** | **8.6 / 11.0 / 11.7 / 9.2 / 27.9** | **4.7 / 4.4 / 10.0 / 3.0 / 9.8** |

Concept IoU of the hull, mean: live .882, gpt-sheet .878, gpt-views .831, gemini-sheet .892, gemini-views .815.
Residual max, mean: live 6.9 %, gpt-sheet 6.5 %, gpt-views 9.8 %, gemini-sheet 7.1 %, gemini-views 27.1 % (every
single-shot set but one has a residual BLOCK; the curated live sets 3 / 5).
Gemini VIEWS returned the concept itself instead of the asked view 6 / 20 times (tractor front, forklift side, ice-cream
side / front / rear, bus top) — the per-view Gemini mode is unusable as is.

## Findings (numbers)
1. One image with all four views beats one image per view, for both generators: conceptOnly 4.4 vs 10.0 % (GPT),
   3.0 vs 9.8 % (Gemini). Views drawn together share one object; views drawn apart each re-invent it.
2. Gemini SHEET is the most concept-consistent set: conceptOnly 3.0 % (better or equal than GPT sheet in 4 / 5 subjects)
   and lower than the curated live GPT sets (4.7 %) from a single attempt; worst-view contradiction 9.2 % vs 11.0 %.
3. No generator makes front and rear mirror-consistent: the worst viewOnly sits in front or rear in 23 / 25 sets
   (4–18 % outside the failed Gemini VIEWS sets). This needs a setup step, not a better generator (see "Next").

## Semantic check (blind, AUDITOR.md task 0)
A blind Fable 5.1 judge saw live / gpt-sheet / gemini-sheet per subject under shuffled A / B / C labels
(out/imagegen-ab/SEMANTIC-BLIND.md; key unblinded after): DEFECT counts (wrong / missing / moved feature, wrong projection).
| subject | live (curated GPT) | gpt-sheet | gemini-sheet | judge's pick |
|---|---|---|---|---|
| tractor | 4 (exhaust stack on the wrong flank in front / rear / top, step flipped in rear) | 2 | 1 (seat missing in side) | gemini |
| school_bus | 0 | 4 (window count, STOP sign missing ×3) | 2 (domed roof in front / rear) | live |
| fire_truck | 3 (ladder length shown front / rear, light bar lengthwise in side) | 0 | 0 | gemini = gpt |
| forklift | 0 | 2 (beacon flank, 7 slats vs 4) | 0 | gemini = live |
| icecream_van | 3 (awning / shelf missing front / rear, cone side-on in top) | 2 | 1 (awning also on the right flank in rear) | gemini |
| **total** | **10** | **10** | **4** | gemini best or tied in 4 / 5 |

## Decision (orchestrator; the owner approves each subject's regenerated views at the setup gate)
Turnarounds are generated as ONE 2 × 2 sheet by Gemini (agy, gemini-3.8-flash-high, the concept as the reference image):
fewest feature defects (4 vs 10 / 10) and the lowest view-vs-concept contradiction (3.0 vs 4.4 / 4.7 %) from a single
attempt. GPT stays as the second generator (edits, and the fallback when a Gemini sheet fails). Per-view generation is
dropped for both. A single sheet still carries proportion residuals (bus 11 %, fire truck 13 %) and front / rear
contradictions (4–14 %), and the curated live sets carry feature errors their curation never looked for (the tractor's
exhaust stack is on the wrong flank in three live views) — so every sheet goes through: normalise → hull.mjs + residuals →
repair the contradicted view (regenerate with a proportion / mirrored-silhouette draft, keep only if the hull numbers
improve) → semantic audit (AUDITOR.md task 0) → owner setup gate.
