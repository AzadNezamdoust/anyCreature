# snake (t9 RECREATE, 2026-10-23) — NOTES

Owner-approved rebuild from scratch of zoo/snake (zoo stays champion). Concept: refs/gpt/v3/snake/sheet_1.png
(kit/refs.py --height 0.5; the zoo snake was built from sheet_4). Judge's reason the zoo model fails: "sheet is a chunky
python with raised S-neck, coiled body mass and big soft blotches; model is a thin flat worm with tiny head and small
square blotches". Fix at S1: mass, proportion, silhouette vs the sheet masks, before anything else.

Identity cue: a heavy python — body thicker than the head is tall, a big wedge head on a thick raised S-neck, the
mid-body arched into a loop, big soft dark blotches over khaki with a cream throat/belly.

Technique (t7 hand box model): one spine loft of 12-vertex half rings (2x density), snout -> tail tip, no limbs. The
kit base is a mirrored half, so stages 1-3 are built straight in plan, carrying the sheet's VERTICAL form (raised head,
vertical neck with a 90 deg turn into the body, the arched loop with the belly lifted 10 cm, the tail tip curling up).
Stage 4 lays the body into the sheet's plan S (snake_shape.bend: straight y -> arc length along the plan centreline,
x -> the curve's left normal, z kept; the neck rings yaw rigidly ring by ring, 6 deg at the skull to -32 deg at the
neck base). Tables: snake_shape.py. S1 target = posed IoU vs UNSYMMETRISED sheet masks (tools/prep_masks.py,
tools/design.py, every round); the kit blueprint IoU is meaningless here (refs.py symmetrises an S-curve plan).
Sheet inconsistencies (noted, side wins): the plan view is drawn 10 % small (scaled x1.10 about the snout) and the
front/rear views are ~1.6x wider than the plan (plan lateral stretched x1.2 as a compromise).
Sheet measurements (m): head L 0.20, W 0.20, H 0.12; neck 0.16 wide, 0.14-0.22 deep (flares into the body);
body 0.18-0.23 wide, 0.17-0.23 tall; arched loop top 0.33 (side); plan centreline 1.26 m behind the neck base.

Zoo champion for scale: body W 0.20 on a 3.0 m snake (ratio 15), head 0.12 wide; this build: W 0.23 on ~1.9 m (ratio 8).

## S1
- r1: first loft from the tables. 3,340 tris. FAIL self-intersection at the body top behind the neck (y -0.10).
  Critique: hero — the loop's arch rings tip forward into their neighbours. Diagnosis: rings perpendicular to the
  spine where the linear lift keys kink. Fix: body tables box-filtered (8 cm x2), rings tilt half the spine slope;
  nose station so the snout cap is small. Posed IoU side/top/front 0.656/0.776/0.619 (first fit, before tuning).
- design rounds (numpy, tools/design.py, no Blender): body keys from the sheet (W 0.23, H 0.22 mid; loop lift 0.10);
  neck dorsal 0.06 -> 0.11 flare, ventral throat bulge; head yaw + steep plan start (the chest bulge under the head in
  the plan); plan lateral x1.2; keys stretched to the plan length -> posed IoU 0.794/0.883/0.706.
- r2: gates PASS, 3,384 tris. Posed preview (tools/pv_s1): Critique: az45 — stair-step facets at the neck base.
  Diagnosis: the neck yaw blended by vertex height shears each horizontal neck ring. Fix: yaw per ring (station_of:
  the ring plane a point lies on), smoothstep from the skull to the neck base.
- r3: Critique: face 3/4 — head as wide as the neck, a flat 8 cm snout cap (sheet: head 1.25x the neck, round snout).
  Fix: head W 0.204 at the jaw, two nose stations (cap 3 cm). FAIL self-intersection at the neck base: duplicate
  station (last neck ring 1.5 cm from the body's first ring).
- r4: fix: neck stations stop 2 cm short of the body's first ring. FAIL self-intersection under the jaw (y -0.38):
  the head -> neck turn (radius 6 cm) is tighter than the 6.5 cm jaw offset. 
- r5: fix: neck ring tilt from a +-3.5 cm chord (rings turn gradually). Gates PASS, 3,560 tris.
- r6: Critique: design.png side — the loop top 4 cm under the sheet, the tail rises too early, thin nape.
  Fix: loop H 0.23 / lift 0.10, tail curl keys later, nape dorsal +1.2 cm. Gates PASS, 3,560 tris, posed IoU
  0.819/0.881/0.716 (zoo champion posed: plan 0.84 vs its own sheet_4, side 0.62).
- r7 (LOCK 0b9df0d0): 1,782 verts, 3,560 tris, orbit OK. Stage 1 frozen = snake_shape tables + PLAN (PLAN.L sets the
  body stations), so the plan is frozen with it.

## S2
- r1: flat crown (vertices 0-2) and cheek (5-6) planes over the head stations 2+, brow edge (3) out 5 mm over the eye,
  lip vertex (7) in 3 mm (mouth line); logged eye-socket inset (face 4-5 at y -0.425, 4 mm in). Gates PASS, 3,576
  tris, min IoU vs s1 0.98.

## S3
- r1: 5 colours (tan, brown, cream, amber, black), smooth_borders(iters 8, despeckle off, brown kept), lens eye
  r 11.5 mm looking 20 deg forward, chunky forked tongue (13 mm prongs). Gates PASS, 3,712 tris. Critique: bent
  preview az90/hero — the flank blotches are small blocky bars (u-angle discs). Fix: blotches as two overlapping
  discs in surface metres (s along the spine, arc round the ring), saddle + staggered flank blotch per 0.215 m.
- r2: Result: big soft blotches, but they merge into bands (top: brown dominates). Fix: discs smaller (saddle r 6.6,
  flank 5.0 cm), flank blotch lower (arc 0.168). Tongue prongs splay to a V (tip x 2.65 cm).
- r3: Result: separate rounded blotches with tan between (top/hero), close to the sheet. Gates PASS.

## S4
- r1: bend into the plan S, 13-bone chain (spine root at the arched loop, chest/neck2/neck1/neck/head forward,
  tail0-6 back), roll = dorsal normal (rot X pitch, rot Z sway). All gates PASS; junction PASS (eyes L/R visible
  front 0.40/0.23, 3/4 0.82/0.76, side 0.70/0.77; 22 mm = 10 % head); detail PASS 5 groups. Critique: posed
  attack f016 — the strike lifts the head up and back. Fix: attack X signs swapped.
- r2: Result: wind-up rears back, strike lunges forward-down; neck bends without collapse. Gates PASS, 3,712 tris.
  --clips --fix-clips PASS (before: attack pen 7.3 %H, move 2.5 %H -> 0), --rom audit 57/58 (neck1 twist -30
  overlap), --pack PASS (LOD 3712/1856/942/584, IoU >= 0.985, round-trip PASS), --review, --compare.

## Fix loop (WORKFLOW 11; CHECKLIST.md frozen, 14 questions)
- r0 champion = s4 r2 (before_fix1/): 10/14 YES. NO: 4 (coil mass mostly on one side from the front), 10 (tongue
  reads as two square bars), 11 (tail curl weak), 13 (thin brown sliver bars + a pale cream wedge at the arched
  loop's inner bend, closeup "arched loop").
- r1 targets 13 + 10. Variant A (s4 r3): blotch discs measured on the posed surface + round 6-sided tapered prongs.
  Gate row NO: detail tongue p10 10.4 mm < 12.1 (hex prong tapers to r 6.4 mm) -> rejected by the gate rule.
  Variant B (s4 r4): straight-space discs with the plan-bend squeeze corrected per face, flank blotches 10 % higher
  and 8 % smaller, despeckle on (keep_area 12 cm2) + a stubby round 6-sided fork (r 7.8-8.2 mm). Gates PASS
  (detail tongue PASS). Checklist 10/14 (13 still NO: the slivers thin but stay, the cream wedge stays; 10 still NO).
  Judge (fresh Opus seats): order champion|B -> champion ("B has ring blotches with a khaki centre, hollow diamonds");
  order B|champion -> champion (same reason). Champion wins both orders -> B reverted (SNAKE_VARIANT unset).
- r2 targets 13. Diagnosis: the plan's first turn (h 0.10-0.35) has R 0.10-0.14 m against a body half-width of
  0.10-0.11 m: the inner flank squeezes to 4-25 % of its length, a pinched wedge (the cream "fin") and sliver
  blotch bars. (A pose curve smoothed per zone kinked at the zone ends: IoU top 0.88 -> 0.75, dropped.)
  Variants: the inner-side lateral offset soft-clamped (tanh) so the squeeze stays >= INNER_MIN: C 0.40, D 0.25
  (snake_shape.bend; S1 untouched; design.py posed IoU top 0.881 -> 0.854 / 0.863).

## Fast-path finish (2026-10-24, WORKFLOW FAST PATH)
- r2 variants C/D not adopted (unjudged; S1 untouched). Rebuilt champion settings (env unset) as s4 r7: 3,712 tris.
  Gates once: kit PASS (qa WARN 6 posed-clip tris 0.14 %, not visible), --junctions PASS (eyes L/R), --details PASS
  (5 groups, tongue p10 13.2 mm), --clips --fix-clips PASS (attack 7.3 -> 0, move 2.5 -> 0 %H), --pack PASS
  (LOD 3712/1856/942/584, IoU >= 0.985, round-trip PASS), --review, --compare. Orbit18 re-rendered.
- A/B vs zoo/snake stage4 (fresh renders both, sheet referee, fresh Opus seat per order): t9|zoo -> t9; zoo|t9 -> t9.
  Verdict ADOPT (candidate for promotion; zoo untouched). ab_vs_zoo.jpg, orbit18_sheet.jpg.
- Residual: tongue reads as two flat black bars; thin sliver blotch bars + pale wedge at the arched loop's inner bend;
  orbit advise head_merged az000 (head 13 % clear of body from the front, as on the sheet).
