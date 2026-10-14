# wolf, cage method (c2): stage 1 notes

Sheet vs brief: the sheet is 1.70 long, 0.41 wide (brief 0.5); the sheet wins on shape. The plan view puts the paws
further out (x 0.205) than the front view (0.164); the side/front views win, the top IoU pays for it.
Paws: each limb ends in a 6-vertex ring at z 0.09 (the ring a library paw joins); below it is a placeholder paw block.

## Round 1
- Critique: first cage. Gate: kneeL 1 loop. Front view too narrow below the ruff (front IoU 0.889).
- Diagnosis: knee J sat 0.077 from the second stifle ring (band 0.08); N2/C0 lower corners at x 0.10 / w 0.18.
- Fix: knee J to (0.26, 0.335) (between the two stifle rings); bib and shoulder widened to the front view (0.193 at z 0.51).
- Result: 748 tris, quad 99%, IoU side 0.967 front 0.889 top 0.907, proportions max 3.5%.

## Round 2
- Critique: gates pass (front 0.895, top 0.913). Worst: the ruff reads as two machined collars (az090, back34): the
  tier edges are planar rings parallel to their step rings.
- Diagnosis: N1/N1s and N2/N2s are coplanar pairs, so the shelf is a uniform band all round the neck.
- Fix: sec(sweep=): the widest vertex of each tier edge swept back 0.055-0.065 (N2's lower corner 0.03), so each tier
  ends in a chevron point on the flank and overhangs its step like a fur clump.
- Result (round 3): WORSE on gates: 8 self-intersecting face pairs (the overhang cut the next band) and neck 1 loop
  (the swept N2s lined its edges up with C0, the loop finder merged the rings). Side view did read less like a collar.

## Round 3 -> 4
- Critique: same problem (collar ruff), fix overshot.
- Diagnosis: sweep 0.055-0.065 puts the edge ring behind its step ring.
- Fix: sweep 0.03 on N1 and N1s together (no undercut), 0.025 on N2 only.
- Result (round 4): gates PASS, 748 tris, IoU 0.967 / 0.895 / 0.914. Ruff still two parallel straps in az090.

## Round 5
- Critique: the two ruff tiers are parallel and 0.08 apart: a collar, not fur masses (az090, az135).
- Diagnosis: N1 and N2 share one slope; tier 2 is a thin band.
- Fix: tier 2 fans back over the withers: N2 top to (-0.19, 0.845), N2s (-0.20, 0.815); C0..C2 tops move back
  along the sheet's back line. Tier 2 becomes a shoulder cape, wide at the top, meeting tier 1 at the bib.
- Result (round 5): BETTER to the eye (tier 2 reads as a shoulder cape), side 0.965; but neck 1 loop: N2s's widest
  vertex now sits straight above C0's, the edge between them is square to the neck axis and the loop finder merges
  N2/N2s with C0 (mean out of band).

## Round 6
- Fix: C0's widest vertex swept back 0.05 (the point of the shoulder, over the leg), so that edge runs along the body.
- Result (round 6): gates PASS, 748 tris, IoU 0.965 / 0.895 / 0.917, proportions max 3.5%.

## Round 7
- Critique: the head reads fox (hero): a thin muzzle and a narrow skull; the concept has a broad muzzle box and wide
  cheek ruff.
- Diagnosis: H0..H5 widths were the plan-view trace, then fit_to_guide pulled H1..H4 onto the (thin) hull.
- Fix: muzzle and skull widths up about 20-30% (H1 0.048, H2 0.066, H3 0.104, H4 0.150, H5 0.178), head rings no
  longer fitted to the guide (B0, B1 only); placeholder paws to the front view's width (0.066).
- Result (round 7): head BETTER (reads wolf, broad muzzle); gates WORSE: neck/head width -14.6% (skull too wide at the
  head joint), neck 1 loop (H5's lower corner at x 0.14 lined up with N1's), top IoU 0.884.

## Round 8
- Fix: H4 width back to 0.138 (the sheet's skull), H5 0.180 with its lower corner at 0.122; the muzzle keeps its width.
- Result (round 8): gates PASS, 748 tris, IoU 0.965 / 0.890 / 0.888, proportions max 5.0%.

## Round 9
- Critique: the legs are constant-section planks from the hero view; no elbow or thigh mass in the width.
- Diagnosis: leg rings rx 0.046 -> 0.038 (fore), 0.050 -> 0.038 (hind): almost no taper.
- Fix: elbow ring rx 0.052 and its back vertex out to y -0.205, forearm tapering to 0.036 at the wrist; stifle ring
  0.058, shin 0.049, metatarsus 0.036.
- Result (round 9): legs BETTER (taper reads in hero and front); kneeL 1 loop: the knee axis ran along the front
  edge of the second stifle ring, so the ring no longer went round the bone. Side 0.967, front 0.890, top 0.887.

## Round 10
- Critique: gate kneeL; and the side silhouette misses the sheet's flank fold in front of the stifle (blue wedge).
- Fix: knee J to (0.28, 0.34), inside both stifle rings; stifle ring front to (0.155, 0.383), second ring front to
  (0.245, 0.305) on the sheet's shin line.
- Result (round 10): gates PASS. 748 tris, quad share 99%, loops 2 at elbow/wrist/knee/hock/neck, IoU side 0.968
  front 0.890 top 0.886, proportions max 7.8% (hind limb thickness). ROM 39 tris / 4.49% area fold (bear pilot 4.48%).
  Blockout packet built from this round; NOT locked.
- Still weak: ruff tiers are full rings (strap-like from behind); front view shows the tail between the fore legs
  (sheet has a gap); the plan view's paws sit wider than the model's; hind leg crumples at the stifle in the fold pose;
  ears are thick blocks.

# Finishing pass (blockout review applied, stages 2-4)

State found: wolf.py had been edited after the round-10 blockout (ears removed for a library ear, library paws welded
with 4 open edges, front IoU 0.819, body length / height +10.4%). Kept as `wolf.py.pre_review.bak`.

## Stage 1, round 11 - blockout review applied (956 tris)
- Review items: (1) hind leg: thigh ring 0.27 deep tapering to a forward knee, shank raking back to a hock point at
  (0.48, 0.238), metatarsus slanting forward: a Z; (2) three knee loops and two hock loops 4-5 cm apart, knee J down to
  z 0.345; (3) fore leg: upper arm 0.22 deep with the elbow point back at y -0.17, wrist 0.10, paw centre 1 cm outside
  the elbow; (4) ruff: N1s and the second tier removed, ONE mane wedge with a single back edge and a 2 cm step, bib
  point down to z 0.40; (5) skull 0.138 -> 0.124, back of skull 0.200 -> 0.165, hips 0.172/0.190/0.158 -> 0.185/0.205/0.172.
- Ears: library `ear_cup` was the plan (ears out of the base), but then the front IoU is 0.82 against the 0.85 floor
  (the ears are 6.5% of the front view) and three proportion ratios move 7-10%. So the ear stays in the base (one
  extrusion of the skull-corner face to a tip quad) and gets its cup as a stage-2 inset. KIT NOTE: the stage-1 IoU gate
  cannot pass a big-eared creature whose ears are library pieces.
- Paw weld: the 2-face end cap was removed face by face, leaving its middle edge as a wire (4 open edges); now
  `bmesh.ops.delete(context='FACES')`.
- Result: FAIL - 10 self-intersecting pairs (thigh ring back past the rump bottom), hind thickness +40% (the model
  filled the sheet's notch between the leg's back and the tail), front 0.836.

## Round 12
- Fix: hind rings' back edge on the sheet's notch line (0.405 / 0.393 / 0.388 / 0.398), thigh 1 cm narrower, tail T2/T3 narrower.
- Result: front 0.85, proportions max 7.4%; 6 intersecting pairs left at the armpit (first fore ring inside the chest bottom).

## Round 13
- Fix: first fore ring out to cx 0.103 and down to z 0.362/0.380.
- Result: gates PASS. IoU side 0.936 / front 0.850 / top 0.898, loops elbow 3, wrist 3, knee 3, hock 2, neck 2.
  Blockout rebuilt: mane reads as one mass, hind leg has thigh / knee / hock, fore leg tapers. ROM 55 tris, 3.38% of
  area (was 4.06%); the review's 1% target is NOT met: the folds are the inside faces of the 80-90 degree knee bend.

## Rounds 14-15 - lock
- Round 14 locked. Stage 2 then showed 16 sliver triangles in the paw joins (the library paw's root ring sat at the
  same height as the leg's last ring), so the lock was redone: paw 0.066 tall under a 2.5 cm join band. Round 15:
  gates PASS, locked, edge hash 33feea8b4ad01a16, 956 tris.

## Stage 2 (1004 tris)
- Round 1: three logged ops: a mane ridge loop (N1-N2), a cheek ruff loop (H5-N1), the inner-ear inset. Moves: ridge
  proud and zigzag, cheek ruff flared, brow over the eye, deeper stop, cheekbone, hip bone, shoulder point, tail tier
  rings and both sock rings zigzag. FAIL: slivers 28 (2.8%): 16 in the paw joins, 4 on the ear rim, the mane step band.
- Round 2: paw join fixed in stage 1 (above), mane edge and step moved together, ear inset 0.42. PASS: slivers 6,
  IoU vs stage 1 min 0.97.

## Stage 3
- Round 1 (1804 tris, 7 colours): painted by station bands; toes + claws (the welded paw_canine's rest), eye_set,
  nose_pad, four fur_clumps. Critique: everything a value too dark in the workbench sheet, mane side patchy.
- Round 2: palette lifted (fur #8f8c8b, saddle #56565e, light #b8b1a8, cream #f1e8d6, tan #dcb990, black, amber iris).
- Round 3 (1708 tris): cheek clump removed (a lump on the mane, and it came off the skin in the attack: drift 3 shells);
  mane grey within 15 cm of the neck's top line, light below; saddle starts at the mane step; eyes 0.019 -> 0.023.
- Parts: paw_canine x4 (toe_segs=1, welded; toes and claws as pieces), eye_set 'angry' softened (brow 13, lid 0.26) x2,
  nose_pad canine, fur_clump n=3 x3 (bib, nape, withers). Not used: ear_cup (see stage 1), tooth_row (mouth closed in
  the concept), tail_tuft (the brush is in the cage). No hand-built pieces.

## Stage 4
- Round 1: rig on J (roll auto), idle 48 f, trot 24 f, pounce attack 32 f. FAIL: cheek clump drift.
- Round 2: PASS, 0 fold-overs. Critique: tail swung INTO the hind legs in the leap (104 tris clip): tail bones take
  +X = tip forward, like limbs.
- Round 3: tail signs flipped: clip 20 tris (0.99%). Round 4: final with orbit.
- Round 4 result: all gates PASS, 1708 tris, 0.12% posed fold-overs, glbcheck OK (idle / move / attack). WARN: 31
  tris (1.05%) clip in a pose (bib tuft and hind toes in the leap). Review packet and side_by_side.jpg built.

## Still weak
- The mane and flank show their quad bands as rectangular colour patches (ring-band tell); c1's mane has more fur break-up.
- Ears are solid pyramids with an inset cup, large dark slabs from the side; the muzzle is long and thin (fox-like).
- Blockout ROM 3.38% at 80-90 degree bends (target 1% not met); the clips stay under 50 degrees so the posed gate is clean.
- Front IoU sits exactly on the 0.85 floor (the tail shows between the fore legs; the sheet's front view has none).
