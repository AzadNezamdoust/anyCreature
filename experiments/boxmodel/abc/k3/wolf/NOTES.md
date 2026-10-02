# wolf (k3) build notes

## Stage 1
- r01 Critique: first blockout reads canine; worst problem is the neck/throat (side, az090): the throat line starts far back and the chest bib sits behind the blueprint, so there is no thick ruff mass hanging under the head. Diagnosis: rings 4-7 under/bottom verts at y -0.49..-0.43. Fix: bring jaw-back, nape, mid-neck and chest-front under/bottom verts forward ~0.05 m and down. Tris 524, IoU side/front/top 0.742/0.758/0.857.
  Result r02: better (side IoU 0.742 -> 0.759), tris 524; the throat now drops under the jaw.
- r02 Critique: the tail (top, az090) is a thin stiff stick; the brief and sheet want a bushy brush carried low, ~0.18 m across mid-tail. Diagnosis: tail rings r/w 0.075/0.072 max. Fix: tail1/tail2 half-sizes to ~0.09, tip ring 0.05, tip lowered to z 0.17.
  Result r03: FAIL, 2 self-intersecting face pairs: the fatter tail1 underside folded back through the rump-to-tail0 band (tail0 bottom sat in front of the rump bottom).
- r03b Fix (same diagnosis, repair): tail root moved back/down to (0.58, 0.63) and the rump bottom raised/forward to (0.53, 0.54) so the under-tail crease is a clean V.
  Result r04: PASS, tail reads bushy and low; tris 524; IoU 0.756/0.776/0.853.
- r04 Critique: top and front views read as a uniform plank; the sheet shows a broad neck ruff/shoulder mass (~0.19 m half width) narrowing to a slim waist. Diagnosis: neck rings 5-7 side x 0.148-0.182 and waist w 0.135. Fix: widen rings 5-7 (side to 0.165/0.195/0.19, upper and under with them) and narrow the waist to 0.125.
  Result r05: better, the neck/shoulder ruff mass reads in top and front; tris 524; IoU 0.756/0.781/0.853.
- r05 Critique: the legs (az000, hero) are thin sticks against the sheet's chunky forearms and big thighs (STYLE: chunky limbs). Diagnosis: leg ring half sizes (elbow 0.040x0.060, forearm 0.034x0.045, stifle 0.048x0.072, shin 0.036x0.046). Fix: thicken elbow/forearm/wrist and stifle/shin/hock rings ~12-15%, keeping the wrist and ankle narrow relative to them.
  Result r06: slightly better, legs read chunkier (forearm, thigh); tris 524; IoU 0.763/0.780/0.846.
- r06 Critique: the paws (az090, hero) are flat shoe slabs with a hard step at the pastern; the sheet has oval paws, toes leading. Diagnosis: the last two leg rings were equal boxes at z 0.03 and 0. Fix: a paw() helper: a pastern ring at z 0.06, a domed knuckle ring (toes low and forward, heel high) and a sole ring tapered at the toe.
  Result r07: better, paws read as oval pads with toes leading; tris 524; IoU 0.762/0.779/0.846.
- r07 Critique: the head (az000, hero) is small and pinched against the ruff; the sheet's skull is broad at the cheeks (~0.145 half width) under the ears. Diagnosis: brow/skull rings 3-4 side x 0.128/0.138. Fix: widen cheek verts to 0.146/0.152 (upper verts slightly) and follow with the ear base ring.
  Result r08: better, the skull is broad under the ears and the head holds its own against the ruff; tris 524; IoU 0.762/0.781/0.846.
- r08 Critique: the hind leg (az090, az135) has a low hock (z 0.18) and a metatarsus leaning forward, so it reads as a plank from thigh to paw; the sheet has a high hock angled back over a near-vertical metatarsus. Diagnosis: J hockL (0.48, 0.18), hpawL y 0.42, mid-shin ring z 0.29. Fix: hock to (0.505, 0.235), paw back to y 0.455, mid-shin up to z 0.325.
  Result r09: better, the hock sits high and angled back over a near-vertical metatarsus; tris 524; IoU 0.770/0.785/0.842.
- r10 Lock: the base reads as a wolf from every view (wedge head, tall ears, ruff mass, deep chest and tuck-up, long legs, low bushy tail). Remaining shape work (brow, stop, eye socket, joint loops) belongs in stage 2. Locked with the orbit.
Stage 1: 10 rounds (r03 intersect fixed inside the round), locked at 524 tris, edge sha256 d2526b9b14739dd8; min blueprint IoU 0.742 (side, r01).

## Stage 2
- r01 Critique: every joint (neck, shoulder, elbow, hip, stifle) has a single ring, so the stage-4 bends would fold at one edge (the neck is the owner's red line). Diagnosis: long bands between rings 5-6, face-to-elbow, elbow-forearm, face-to-stifle, stifle-shin. Fix: five logged full loops, one per joint band.
  Result r01: PASS, tris 604, min IoU vs s1 1.0; bands now have two rings per joint.
- r02 Critique: the face (hero, az045) is a smooth wedge with no eye, brow or cheek: no character. Diagnosis: the brow-cheek quad between rings 2-3 is one flat face. Fix: inset it as an eye socket (0.32, 10 mm in), pull the brow vertex forward/out over it and drop the cheek vertex a touch; keep_valleys protects the socket fold.
  Result r02: PASS, tris 620, min IoU 0.998; a socket reads under the brow in the hero view.
- r03 Critique: flank and muzzle (az090, hero) still break into twisted facets that read as a lofted tube rather than drawn planes. Diagnosis: the non-planar quads between rings 8-10 (upper/side) and 1-2 (muzzle side). Fix: flatten the rib-cage vertex group into one plane and the muzzle side quad into one plane. Final stage-2 round, with orbit.
  Result r03: PASS, tris 620, min IoU 0.992; flank and muzzle side now read as single planes. Stage 2: 3 rounds, 620 tris.

## Stage 3
- r01 Plan: paint the base in six flat colours with borders on existing loops (mouth line = muzzle side verts, belly = side/under edges, saddle on up-facing back faces, tan below z 0.40), then separate pieces: amber eye lenses proud of the socket, ruff and cream bib clumps (raycast-rooted spikes swept back/down), dark withers hackles, tail brush with dark tip, four claws per paw.
  Result r01: PASS, 1016 tris, 6 colours, no hits/floats/z-fight.
- r02 Critique: the ruff, hackles and tail clumps (az090, top, az000) stand straight off the surface as thin thorns: the wolf reads as a porcupine, not a shaggy ruff. Diagnosis: blade dir = 0.65 normal + 0.55 sweep, width 0.06 for length 0.085. Fix: lay the clumps down (0.40 normal + 0.90 sweep) and widen them to ~0.08 so they read as overlapping fur plates.
  Result r02: PASS, 1016 tris; the clumps now lie down as overlapping plates; ruff reads shaggy rather than spiky.
- r03 Critique: the front view (az000 colour) is wrong in two linked ways: the amber eye fills the whole socket (a goggle patch) and the chest is grey, so the cream bib the brief asks for is missing. Diagnosis: eye lens built at 0.12-0.35 of the socket face; the bib rule only caught faces with n.y < -0.35. Fix: lens shrunk to 0.50-0.66 of the socket, bib rule also takes chest faces inside x < 0.13 below z 0.78. Final stage-3 round, with orbit.
  Result r03: PASS, 1016 tris, 6 colours; the eye is a small amber lens under the brow. The bib stays mostly hidden under the ruff clumps from the front. Stage 3: 3 rounds, 1016 tris total.

## Stage 4
- r01 Plan: armature from J (spine, chest, neck, head, ears, 3 tail, 3 per leg; roll auto), automatic weights, all pieces bound with body= weights; idle (breath, ear twitch), move (diagonal trot), attack (rear back, head-down lunge, snap).
- r01 Result: FAIL on drift only (1 ruff shell); folds 0.20% tris / 0.19% area, neck bends cleanly in the attack. Critique: the drifting clump is on the shoulder (az090 tech, brown): the y -0.28 low clumps and the outer bib clump were rooted on the upper-arm band, so their borrowed weights slide against the swinging leg skin. Fix: drop the two lowest clumps of the y -0.28 row and raise the outer bib clump to z 0.64, off the leg root (stage-3 piece change only; base untouched).
  Result r02: PASS on every gate; drift 0, folds 0.20% / 0.20% area.
- r03 Final: the same program with the orbit and glbcheck (no change).
  Result r03: PASS; orbit holds, glbcheck OK (attack/idle/move). Stage 4: 3 rounds. Review packet built (--review).
Triangles: stage 1 524, stage 2 620, stage 3 1016 total, stage 4 992 total (body 620 + pieces 372, after dropping two shoulder clumps).

## Repair pass (K=1, from review/ad_notes.md; stage 1 locked, no unlock)
- r11 Baseline (current kit): every gate PASS; flips 2 (0.20% / 0.20% area), clip warning 14 tris (0.79% area). No item 0.
- r12 Critique (must-fix 1): the ruff is a spray of thin triangle spikes, some rooted on the shoulder/upper-arm band and reading as shards (1_beauty hero, 2_closeups front limb). Diagnosis: `blade()` spikes 0.085 wide in four y-rows down to y -0.28/z 0.70 plus three front bib clumps down to z 0.53. Fix: new `shingle()` piece (base 0.15 x 0.04, a broad shoulder ring at 55% length, blunt point; sunk 20% of its thickness plus the neck-curvature sag), two rows of three per side cast perpendicular to the neck axis (roots asserted z > 0.64 and in front of the withers), lengths 0.10-0.14, the s3 r02 sweep kept; the throat plates cream, the nape/side plates grey (nearest-root paint); the chest bib stays paint only.
  Result: PASS every gate, 992 tris; plates are wide and overlapping round the neck only, none on the shoulder; clip warning 0.79% -> 0.53% area. They still stand a little proud (32 deg off the skin).
- r13 Critique (must-fix 2): a comb of identical dark spikes runs down the withers (az090, back34). Diagnosis: `piece_hackles`, three equal `blade()` spikes on the spine. Fix: delete the piece; the saddle is paint only.
  Result: PASS, 956 tris; az090 shows one smooth dark mantle, no comb; clip warning 0.33% area.
- r14 Critique (must-fix 3): the posed fold-over (purple, 3_tech az000/hero). Diagnosis (a temporary per-frame fold probe, removed after): the 2 flipped faces are the throat triangle (ring-5 bottom, ring-5 under, neck-loop bottom) at (+-0.037, -0.537, 0.634), folding in attack f14/f17/f19 when the head drops; ring 5's bottom vert bulges 0.01-0.018 forward of ring 4 and the neck loop, so the nod turns it over. It is the throat, not the brisket. Fix (stage 2, vertex move): ring-5 bottom vert +0.014 y, +0.008 z, so the throat line runs straight from jaw to neck.
  Result: PASS, flips 0 (0.00% / 0.00% area); IoU min 0.992; no purple in the tech views.
- r15 Critique (must-fix 4): the tail reads dark along its whole underside and rear (az090, back34), and its underside near the root was tan. Diagnosis: `body_rule` painted every face with y > 0.72 saddle, the up-facing tail faces saddle, and the tail faces below z 0.40 fell into the `tan` leg rule; the brush clumps went saddle for y > 0.74. Fix: a tail rule first (y > 0.58, z < 0.66): saddle below z 0.26 (the last 30%) and on the up-facing root faces above z 0.50, grey elsewhere; brush clumps saddle only below z 0.27.
  Result: PASS, 956 tris; a grey brush with a dark tip; the saddle runs onto the root. The rear edge still reads darker in the workbench shade (it faces away from the key).
- r16 Critique (must-fix 5): the paws are blocks the width of the cannon with claws on the front face (2_closeups). Diagnosis: the stage-1 `paw()` sole and knuckle rings are near-rectangles as wide as the pastern. Fix (stage 2 vertex moves; claws in stage 3): sole toe verts pulled in to +-0.026 and pushed 0.012 forward, sole heel verts in to +-0.030, knuckle heel verts in to +-0.036, so the pad tapers to a leading toe; middle claws 0.032 -> 0.038, outer claws splayed +-8 deg, all claws aimed inside the narrower toe (+-0.007/0.019). First run failed z-fight (8 claw faces lying on the sloped toe/sole); claw roots raised z 0.013 -> 0.017 and pitched -0.30 -> -0.24.
  Result: PASS, 956 tris, IoU min 0.985; the paw tapers to the toe with the middle claws leading. With a 4-vert ring it is a tapered pad, not a true oval.
- r17 Critique (must-fix 1, second look): the new shingles stand 32 deg off the neck with blunt tips and read as armour slabs (hero). Diagnosis: `shingle()` direction 0.40 normal + 0.90 sweep, shoulder ring 0.42 w, tip lifted 0.45 t. Fix: 0.25 normal (same sweep), shoulder ring 0.36 w, tip lift 0.25 t.
  Result: PASS, 956 tris; the plates lie down along the neck as tapered overlapping shingles; clip warning cleared.
- r18 Critique (should-fix, AD): the amber eye is a small diamond (2_closeups head). Diagnosis: lens rings at 0.50/0.66 of the socket face. Fix: 0.30/0.524 (1.4x), still proud 0.008 under the brow. The temporary fold probe was deleted from the program.
  Result: PASS, 956 tris; the eye reads as an amber almond under the brow, no z-fight.
- r19 Final: the same program with the orbit and glbcheck. Result: PASS every gate; hit/float/z-fight 0/0/0, slivers 2 (0.2%), flips 0 (0.00% / 0.00% area), drift 0, clip 0; IoU min 0.985; glbcheck OK. --review and --compare rebuilt.
  Checked in review/ (idle frame 1): no plate on the shoulder or foreleg, no detached shard, no spine comb, no purple, grey tail with a dark tip, larger eye. Open: the dark point between the forelegs in 1_beauty az000 is the tail tip (z 0.17, x 0) seen through the legs, not the chest; the brisket move and chest loop from note 3 were not needed for the fold and were not made. Paws taper but stay 4-vert pads.
Repair pass: 9 rounds (r11-r19), 956 tris (body 620 + pieces 336).

## Repair pass (K=2, from review/ad_notes_r2.md; stage 1 locked, no unlock)
- r20 Baseline (current kit): every gate PASS, clip 0, flips 0. No item 0.
- r21 Critique (must-fix 1): the ruff is six big flat slabs on the neck (2_closeups ruff). Diagnosis: two rows of three `shingle()` plates 0.15 x 0.04, L 0.10-0.14. Fix: three rows round the neck axis (cheek y -0.50 x3, mid y -0.43 x4, rear y -0.36 x3 per side), plates 0.09 x 0.024, L 0.075-0.085, sunk 30%; cheek/throat cream, nape and rear grey.
  Result: PASS, 1068 tris; a layered collar, but clip warning 18 tris (0.65% area) on the low throat clumps in the head-down attack.
- r22-r26 Critique: the pink (posed clip) is on the low throat clumps. Diagnosis: at 0.25 normal the small, deeper-sunk clumps lie in the throat crease that closes when the head drops. Fix (one per round): clumps below 25 deg lifted to 0.42 normal (r22, 0.18%); cheek row moved back to y -0.48 (r23, 0.16%); a=-40 tried and reverted (r24 worse, 0.46%); whole cheek row lifted (r25, no change); mid-row throat clump a -30 -> -22, L 0.065 (r26, 0.10%). r27 rear-row probe: no change, reverted.
- r28 Critique: the new clumps read as square chips, and the top cheek clump was cream behind the ear. Diagnosis: shingle shoulder ring 0.36 w at 55% L gives a blunt rectangle. Fix: `shingle(sh=)` parameter, ruff uses shoulder 0.30 w at 35% L (pointed tip); the 55-deg cheek clump grey.
  Result: PASS; pointed clumps sweeping back and down; clip 10 tris (0.17% area, warning only, small pink at the cheek-row low clump).
- r29 Critique (must-fix 2): needle claws on a plain tan block paw. Diagnosis: claws 0.013 x 0.011, L 0.024/0.038, pitch -0.24. Fix: claws t 0.020 (2x), w 0.012 (fits the 4 toes without touching), L 0.024/0.030 (~70% of middle), pitched -0.50/-0.62 so tips reach the ground line; body faces z < 0.045 facing forward painted dark grey (toe fronts).
  Result: PASS, z-fight 0; dark toe tips with four dark claws, middle pair leading. From the front the claws still read thin.
- r30-r31 Critique (must-fix 3): the eye is an amber triangle with no brow. Diagnosis: the lens copied the 4-vert socket face; the brow vert overhung only +0.010 x. Fix: stage 2 brow vert +0.009 x, -0.006 y more (3%/2% of head width); stage 3 a 6-point almond lens (long axis along -Y in the socket plane, sharp front/back corners), socket faces within 0.03 of EYE painted dark grey (rim). r31: almond lengthened (0.95 x 0.55 of the socket extents) after r30 gave a small hexagon.
  Result: PASS, z-fight 0, IoU 0.985; an amber almond in a dark rim under a brow.
- r32 Critique (must-fix 4): the underline runs level to the hind legs (az090). Diagnosis: waist ring y 0.28 bottom at z 0.52, below the y 0.17 ring. Fix (stage 2): bottom and under verts of rings y 0.17 / 0.28 raised 0.03 / 0.06, under verts in 0.011; brisket untouched.
  Result: PASS, flips 0, IoU 0.985; az090 underline rises clearly from chest to flank.
- r33-r34 Critique (must-fix 5b): the dark tail tip shows between the forelegs in az000. Fix: tail0 pitched on every idle key; r33 +12 swung the tail forward (wrong sign), r34 -12 back.
  Result: PASS; tail back and low, but the tip still showed between the legs.
- r35 Should-fix: pastern rings (z 0.06) scaled 0.82 x / 0.85 y, so the leg tapers into the paw. PASS, IoU 0.985.
- r36 Orbit run and --review (PASS every gate); the packet showed the tip still between the forelegs.
- r37-r38 Critique: az000 still shows the dark tip through the leg gap (the tail is on the centre line). Fix: tail0 also swung 12 (r37), then 20 deg (r38) sideways on every idle key, so the tip sits behind the left hind leg.
  Result: PASS; 1_beauty az000 shows nothing dark between the forelegs. Nape tab: not seen in 4_posed attack_f016 after the ruff rebuild.
- r39 Final with orbit and glbcheck: PASS every gate; hit/float/z-fight 0/0/0, slivers 2 (0.2%), flips 0 (0.00% / 0.00% area), drift 0, clip warning 10 tris (0.17% area), IoU min 0.985, glbcheck OK. --review and --compare rebuilt.
Repair pass K=2: rounds r20-r39, 1084 tris (body 620 + pieces 464).
