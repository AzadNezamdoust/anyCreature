# wolf c3 cage: form and topology review

Evidence: `blockout/` packet of c3 (1_grey, 3_proportions, 4_topology, 4_topology_table, 5_profiles, 5_rom, topology.json), concept `refs/gpt/wolf/concept_2.png`, previous cage `abc/c2/wolf/blockout/` (1_grey, 4_topology).

## Scores

| | form /10 | topology /10 |
|---|---|---|
| c3 (new) | 7.0 | 7.0 |
| c2 (previous) | 5.5 | 4.0 |

Verdict: **FIX** (one small stage-1 round; no gate fails, the fixes are deformation and medium-form items that are cheap now).

## Form (c3)

- Head: reads as skull + stop + muzzle + ears inside the ruff, not a wedge. Profile RMS 2.71 %, taper within 11 %. Weak points: the lower jaw is not a separate mass (muzzle underside is one flat plane, the reference has a jaw step at station 4 where the model's depth curve goes flat and misses the bump, max error 6.19 %), and from the front the skull between the ears is narrow against the ruff, so cheeks merge straight into the ruff.
- Fore limb: profile matches the sheet (RMS 1.34 %), but the sheet limb is itself near a tube (0.85) and the cage adds nothing above the elbow: no upper-arm / shoulder mass shows outside the ruff in side or front view, the leg leaves the chest as a post. Paw wedge is good. Width at the root is +9 % wide.
- Hind limb: the best part. Thigh mass, narrow stifle, back-set hock, thin metatarsus, broad paw (tube 0.68 vs 0.63). Calf swell slightly under-stated.
- Torso/tail: rib cage, waist tuck and haunch separate in the top view; tail swells and tapers. Front view: stance is narrow, fore legs nearly touch under the chest.
- Versus c2: c2 had a single faceted block for the ruff, peg legs with a collar step at each paw and a flat plank tail. c3 is clearly the more designed cage.

## Topology (c3)

- Density: even. Edge p90/p10 2.63 body, torso 1.78; 0 % over 5:1; all quads; no valence-6 poles. Torso is a little sparse (0.72x) and the head carries the outliers (10 % over 3:1, p90/p10 3.35) around the eye pocket and ear bases.
- Loops: closed shoulder and hip loops over the joint, limb edges run into the torso (flow 0.33, just over the 0.3 limit), no caps or fans. Ruff rings are slanted with the ruff, which follows the form. Every joint has exactly 2 loops: the minimum, and it shows in the ROM sheet.
- Neck: the two neck rings sit 0.16 x width apart: a pinched thin band behind the ruff (visible in hero and top views) with wide faces either side. The table calls this "2 loops"; my eye says it works as one loop, the table is too generous here.
- Poles: 0 in joint bands by the table, but the valence-5 at the front of the shoulder loop sits at the armpit/elbow top, and three poles (two valence-5, one valence-3) cluster at the hip/tail root, both in zones that move. The 8 valence-3 corners of each inset eye pocket are acceptable for a blockout but there is no eye or mouth loop declared (the one warn FAIL).
- ROM: 3.62 % of area folds over (32 of 744 tris). Fold and crouch: the hind leg collapses into the belly/groin at the stifle. Swing: the back of the fore root opens a hard crease at the armpit. Elbow, wrist and hock bend cleanly.
- Versus c2: c2 had valence-6 fans at the eyes, n-gon paw caps, ruff faces 4-5x the size of the leg faces, ring stacks on the paws and a ruff that met the torso in a hard step with no shared ring. c3 removes all of that. A large step up (+3), not a polish.

## Fixes (max 5)

1. **Neck rings: spread the pinched pair.** Neck / back of ruff. Move the two neck rings apart from 0.16 to about 0.4-0.5 x neck width (roughly +0.10 to +0.15 m between them) so the neck has two working loops and the face size matches the ruff and withers.
2. **Third loop at knee (stifle) and elbow.** Add one ring at each, on the flexion side spacing about 0.3 x limb width from the joint ring, and give the groin/armpit one extra edge of slack. Target: ROM fold-over under 1.5 % of area (now 3.62 %).
3. **Move the root poles off the bending zones.** Shoulder: slide the front valence-5 of the shoulder loop up about one face (about 0.08-0.10 m) onto the flat of the shoulder blade. Hip: separate the three-pole cluster at the hip/tail root, pushing the valence-5 pair one face forward onto the haunch flat so the tail root ring is pole-free.
4. **Upper-arm mass on the fore limb.** Fore root, above the elbow. Add an upper-arm/shoulder swell of about +10-15 % depth at the first station below the chest and narrow the root width by about 8 % toward the sheet, so the leg reads shoulder > elbow > forearm > wrist > paw rather than a post under the ruff; widen the front stance by about 10 % of chest width.
5. **Head: jaw step and face loops.** Drop a lower-jaw plane under the muzzle at station 4 (depth +5-6 % of head length there, to close the 6.19 % max error) and widen the skull at the cheek by about 5-8 %; declare an eye loop and a mouth loop in META['landmarks'] and re-route the eye-pocket corner poles into a closed ring.
