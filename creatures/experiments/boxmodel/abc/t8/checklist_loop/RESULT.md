# checklist_loop A/B: gorilla, 3 fix rounds from the zoo/gorilla stage 4 copy

**Verdict: MIXED, leaning ADOPT.** The checklist arm (B) beat free-form review (A) in both judge orders. Against the untouched baseline the judge showed no consistent preference, so the tie goes to the baseline. My own read is that B is clearly better: crest, forearm shape and saddle taper.

| | baseline zoo/gorilla | A free-form (r15) | B checklist + champion (r18b) |
|---|---|---|---|
| Kit gates / glbcheck | PASS | PASS | PASS |
| Junction probe (upperarm knife / strip; thigh knife / strip) | 0 / 0.86r; 0.89r / 0.62r | 0 / 0.86r; 0.88r / 0.75r | 0 / 0.86r; 0.89r / 0.62r |
| Detail gate | PASS, 6 groups | PASS, 6 | PASS, 6 |
| Eye (front / 3q / side) | 0.47 / 0.73 / 0.42 | 0.46 / 0.72 / 0.42 | 0.46 / 0.72 / 0.42 |
| IoU vs S1 lock (min) | 1.0 | 0.986 | 0.981 |
| Posed clip (warn) | 0.65% | 0.66% | 0.65% |
| Tris (body) | 2796 (2316) | 2796 (2316) | 2796 (2316) |
| Builds / wall time / turns | - | 4 builds, ~40 min, ~45 turns | 7 builds, ~36 min, ~60 turns |
| Checklist score (of 16, B's own grading) | 7 | not scored | 14 (still NO: Q3 visor face, Q12 fingers at 192 px) |

The silhouette IoU against the sheet masks is unchanged from the S1 lock, because both arms kept the lock: side / front / top 0.937 / 0.903 / 0.883.

## Judge (one Opus seat, blind, owner rules in the prompt, sheet as referee)
- **A vs B:** B won in both orders. The judge's reason: A's silver runs down the hind legs like a blanket.
- **Baseline vs B:** one tie and one B win. That is not a consistent preference, so the result is a tie and goes to the baseline.
- **Baseline vs A:** one tie and one baseline win, so A is no better than the baseline (slightly worse).
- **Shared flaw:** in every pair the judge noted a visor-like face plate and a weak crest.

## My read (all images opened)
- **B:**
  - The saddle tapers to the shoulders and sits on the back and rump, like the sheet's rear and top views.
  - The crest is a peak.
  - The forearm has a swell and the elbow a pinch.
  - The face is still a dark visor.
  - Flaw: the lower saddle border on the haunch is saw-toothed at az135 and az225.
- **A:**
  - The crest cone is good.
  - The saddle now has a curved front edge, but the silver runs down the backs of the legs to the ankles. That is a new defect against the sheet.
  - The arms are still tubes.
- **Process:**
  - B turned every critique into an edit to a named target, and its two variants per round (accept only on a both-order win) fixed three of the three known weak spots partially, against A's two.
  - The cost is about 1.75x the builds for similar wall time.

Images: `ab_compare.jpg` (rows baseline / A / B; 6 views plus 192 px thumbnails), `ab/` (renders and the judge pairs j1-j6).
