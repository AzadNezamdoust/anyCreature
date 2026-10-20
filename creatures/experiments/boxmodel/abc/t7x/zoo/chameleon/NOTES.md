# chameleon (t7x zoo) — NOTES

Technique: the base wolf's loft (one spine loft of 6-vertex half rings, tail tip -> nose; legs extruded from 2-face flank regions), stage 2 joint rings + eye socket, stage 3 lens eye and pieces, colour by region rule, stage 4 rig + idle/move/attack. Height 1.1 m to the casque tip. Reference traced from sheet_2.png with kit/refs.py.

Body plan: the tail is part of the loft — 3 sections down the back, then 13 sections on a shrinking 45-degree-step spiral about (y 0.70, z 0.15), each section standing across the path with its top seam on the outside of the curl. The casque is the tall narrow top of the head sections (explicit half rings), its back edge vertical behind the head. No ears.

## Stage 1
- r1: first fit. Gates PASS, 796 tris, IoU side/front/top 0.753/0.680/0.763. Critique: az090 — legs are stilts. Diagnosis: limb rx/ry 0.036-0.055. Fix: chunkier limb sections.
- r2: Result: slightly better, IoU 0.761/0.684/0.777. Critique: top — body a plank against the ref's 0.2 half-width. Diagnosis: body W 0.135-0.165. Fix: W 0.15-0.19.
- r3: Result: top better (0.813), front 0.674. Critique: hero — pointed cone snout, blade casque. Diagnosis: H3/H4 half-widths 0.03-0.07, casque top vertex x 0.03. Fix: blunter snout, casque thicker at the top.
- r4: Result: better, IoU 0.761/0.689/0.813. Critique: az090 — limb hexagons still thin front-to-back. Diagnosis: corner factor 0.55. Fix: corner 0.8.
- r5 (LOCK): gates PASS, 400 verts, 796 tris, edge sha256 776f51c7edf2bb90; IoU 0.761/0.689/0.818 (front pays for the traced ref filling the gap under the belly, and the staggered leg pairs in side).

## Stage 2
- r1: elbow, knee and neck rings, eye socket inset, slight brow, flat snout side, tail tip ring widened. Gates PASS, 880 tris, min IoU vs s1 1.0.

## Stage 3
- r1: Plan: 5 colours (sage green, yellow and teal bands across body and along the tail path, cream belly/jaw/feet, dark claws); small lens eye (r 3 cm) with a dark pupil; dorsal crest of 11 half spikes on the mirror plane; clamp feet = opposed toe bundles + claws. Result: FAIL, z-fight 32 faces (toe bundles).
- r2: Diagnosis: bundle bottoms coplanar with each other. Fix: stagger heights. Result: 8 left.
- r3: Fix: two opposed bundles per foot (front/back clamp). Result: still 8.
- r4: Diagnosis: bundle bottoms 1 mm above the body sole. Fix: lift to 6 mm. Result: gates PASS, 1186 tris total.

## Stage 4
- r1: rig: hips/spine/chest/neck/head, 8-bone tail chain along the spiral, 3-bone legs (+ .R). Clips idle (breathing, casque sway, tail curl), move (diagonal walk + body sway), attack (rock back, head strike). All gates PASS: hit/float/zfight 0, slivers 0, fold-overs 0, drift 0, lock OK.
- orbit18_sheet.jpg: all 18 views read, no collapse. Separation (rest mesh): tail-hind 30 cm, fore L-R 26 cm, hind L-R 25 cm: PASS.

Weaknesses: one symmetric leg pair where the ref staggers them; colour bands are hard-edged and the belly cream reads large from below; no gular crest; eye has no turret.

## Fix pass (reviews: fable + opus)
Merged fix list (shape first): casque spike/hat, feet mittens with pin claws, eye without turret, noisy dorsal nubs.
- Stage 1 re-locked (r6, r7): casque top widened into a ridge (H0 top 1.075 -> 1.04, shoulder vertex 0.05 -> 0.07 wide, H1/H2 tops raised) so it slopes back as a plate, not a cone; tall casque kept per the sheet (Opus "lower 30%" rejected). Gates PASS, 796 tris, IoU 0.762/0.699/0.820.
- Stage 3: eye = small cone turret (base r 5 cm, 4 cm tall) with a 2 cm lens and pupil; dorsal crest 11 nubs -> 6 larger wedges; feet = two opposed cream grip pads per foot in a V, pin claws dropped, foot block green; casque colour green with a yellow back rim.
- Stage 4: all gates PASS (hit/float/zfight 0, fold-overs 0, lock OK); separation PASS (tail-hind 30 cm, fore 26 cm, hind 25 cm). Orbit 18 all colour.
- Not fixed: the casque cannot lean back (sections are fixed-y rings); one symmetric leg pair.

## Fix pass 2 (reviews: review2_fable + review2_opus, concept sheet as referee)
Merged fix list (shape first): legs straight stilts -> bent, elbows/knees out (both); casque taller, head shorter (both); mitten feet (both; the two opposed grip pads already form it, kept); stripe contrast down (Opus) skipped, the sheet's bands are strong.
- Stage 1 lock deleted and re-locked (r08): elbow/knee x 0.195 -> 0.235, mid-leg ring x 0.205 -> 0.25 at z 0.20 (bowed crouch), mid ring y tilted (fore back, hind forward); casque crown H0 1.04 -> 1.12, H1 0.975 -> 1.02; H2-H4 y compressed x0.85, nose -0.88 -> -0.84. Gates PASS, 796 tris, IoU 0.756/0.611/0.810 (front pays for the bowed legs).
- Stage 4 (r04): all gates PASS; techqa zfight 2 (advisory). Separation PASS (tail-hind 32 cm, fore 31 cm, hind 31 cm). Orbit 18 all colour. side_by_side now concept views vs model.
- Not fixed: casque cannot lean back; one symmetric leg pair.

## Poly pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- Old lock, script, stage-3 stats and hero/orbit/side sheets kept in before3/.
- Base change, stage 1 re-locked. Half rings 6 -> 10 vertices (a Catmull-Rom rounded point in each of the first four spans, ring mirrored across the seam) for body, tail and head rings. Spine stations 28 -> 40: rump R0b, hip R1b, belly M0b, girth M1b, shoulder C0b (tops/bellies read off the side trace's top and belly lines); head H0b (casque back), H1b (cheek under the casque), H2b (snout bridge) as explicit rings; tail root off the rump and three half steps on the outer spiral turn, placed on the spiral. Legs: 4-face root strip, 10-vertex elliptical rings.
- r09 PASS; r10 LOCK: 920 verts, 1836 tris, edge sha256 26ce40115495088f, IoU 0.755/0.605/0.812 (was 0.756/0.611/0.810). Budgets: stage 1 1400-2800, total 1800-4500.
- Stage 2: elbow, knee and neck rings re-aimed at the new rings; eye socket = inset of the four faces round H1b[3]; brow on H1 and H1b; snout flats over the new H3/H4 side points; tail tip ring = the new first section. Stage 3: lens seated on the socket centre; tail bands and tail bones keep the original path stations.
- Stage 4 r05: all gates PASS (hit/float/zfight 0, fold 0, drift 0), lock assert PASS, glbcheck OK, slivers 1.1 %. Separation PASS (tail-hind 32 cm, fore 31, hind 31).
- Tris 1148 -> 2284 (1.99x): body 880 -> 2016, details 268 unchanged (100 % of the increase in the body). orbit18_sheet.jpg, side_by_side.jpg, before_after3.jpg rebuilt.

## Poly pass 4 (review_poly2x verdict MIX: keep body + casque, restore before3 legs)
- 2x-pass script, lock, hero, orbit and side sheets kept in pass3/.
- Base change, stage 1 re-locked (r11, r12). Legs: the 10-vertex leg rings go back to the before3 hexagon section (role k linear between corners, so the u +-0.5 vertices lie on the flat planes, no elliptical flare); the 4-face root strip's mid vertices (ring 5, 7) flattened onto the before3 root planes, so no flank "knee fin". Body, casque, head, eye and tail rings unchanged from pass 3.
- r12 LOCK: 920 verts, 1836 tris, edge sha256 26ce40115495088f (topology unchanged), IoU 0.755/0.605/0.811.
- Stage 4 r07: gates PASS (hit/float 0, fold 0, techqa zfight 2 advisory, slivers 2.0 %), lock assert PASS, glbcheck OK. Separation PASS (tail-hind 32 cm, fore 31, hind 31). Tris 2284.
- orbit18_sheet.jpg, side_by_side.jpg rebuilt; before_after4.jpg = before3 | 2x pass | now.

## Fix pass 9 (owner: keep the 2x density, fix the problems inside it)
- Start: pass 4 already kept the full 2x body (2284 tris); before9/ holds the renders, lock and script before this pass.
- review_poly2x WORSE: knee "fins" / noisy leg planes. Cause: the tall flank root strip extruded straight to the elbow/knee ring, a long web. Fix: a short tilted shoulder / hip collar ring (outer side up) as the first leg section, so the root becomes a stubby upper limb; before3 hexagon leg planes kept. Collar colour forced green (no cream wedge on the hip). Body, casque, head and eye rings unchanged (eye same size).
- Stage 1: r13 FAIL (flat collar cut the flank), r14 PASS with the tilted collar, r15 LOCK: 960 verts, 1916 tris, edge sha256 e83bc80b089a9db3, IoU 0.756/0.563/0.806 (front pays for the wider shoulders).
- Stage 4 r09: all gates PASS (hit/float/zfight 0, fold 0, drift 0, slivers 0.3 %), lock assert PASS, glbcheck OK. Separation PASS (tail-hind 32 cm, fore 31, hind 31). Tris 2284 -> 2364.
- orbit18_sheet.jpg, side_by_side.jpg rebuilt; fix9.jpg = before9 | after hero + fore shoulder and hind hip close-ups.
