# bear, cage method, stage 1 (v2 of the pilot)

The pilot's lock (rounds 1-5) is set aside as `stage1_lock.pilot.json.bak`, its program and packet in `pilot/`:
stage 1 is reopened to fix the pilot's blockout weaknesses (wedge head, block ears, banded flank, folding leg roots).
Not locked again; the blockout review decides.

## Round 6 (rebuild of the cage layout) - 716 tris
- Critique: pilot head a lofted wedge, legs hang from the belly so shoulder/thigh are not masses.
- Fix: head = muzzle block + stop + broad face plane + skull; leg roots raised to the shoulder/hip point
  (the root ring runs shoulder -> armpit, first ring is the upper arm / thigh mass); stations sheared in y.
- Result: gates FAIL only on neck width / head width +10.4% (ruff step NK too wide). IoU 0.974/0.934/0.826.

## Round 7 - head
- Critique (az000): the head reads narrow and roof-shaped against the sheet's broad flat forehead; ears are slabs.
- Diagnosis: H3-H6 upper corners at x 0.09-0.13; NK at w 0.235 is wider than the skull (sheet has a notch there).
- Fix: upper corners out to 0.11-0.155, cheeks 0.205-0.222 and lower; NK 0.205; ear a bigger disc (0.13 wide).
- Result: better - the forehead is broad and flat, the ears read as round ears. Neck / head width now -14.5% (NK too
  narrow against the ear span). 716 tris. IoU 0.974/0.934/0.818.

## Round 8 - flank
- Critique (az045, hero): the flank is still vertical light/dark stripes; shoulder and haunch do not read as masses.
- Diagnosis: the widest vertex of T1..T8 jumps in height (0.52-0.63) and width station to station, so each band twists.
- Fix: one continuous shoulder-to-hip line (z 0.56-0.62), upper corners 0.17-0.20 for a broad back/hump plane,
  T4/T5/T6 sheared (shoulder rear edge and thigh front edge run diagonally). NK back to 0.232 (the ruff step).
- Result: better - gates PASS (716 tris, IoU 0.975/0.929/0.82, max proportion diff 4.5%); the shoulder and the
  haunch read as masses, the stripes are gone from the back. Blockout ROM: 36 tris fold (4.66% of area).

## Round 9 - joint loops
- Critique (5_rom fold/crouch): wrists and hocks crush; fold-over is above the pilot's 3.3%.
- Diagnosis: the two loops of each joint sit 5.5-6.5 cm apart on a 24 cm thick limb.
- Fix: spread each pair to 9-10 cm (still inside the gate's band of the joint).
- Result: no better (37 tris, 5.2% of area). A locator (BEAR_DIAG=1) puts the folds on the inside of the bends: back
  of the stifle, front of the hock, back of the elbow - not at the leg roots, which now swing clean.

## Round 10 - a third loop per joint
- Critique: same as round 9. Diagnosis: 80-90 degree bends on a 0.3 m deep limb with one face to take the compression.
- Fix: three loops at elbow, wrist, stifle and hock (BRIEF: 2-3 at every joint), spread over 10-11 cm.
- Result: slightly better (46 of 812 tris, 4.5% of area; elbow 3, stifle 3, hock 3 loops, wrist counted 2). The rest
  is the inside face of 80-90 degree bends on a very thick limb; kept, reported as a weakness. 812 tris.

## Round 11 - muzzle, brow, ear angle
- Critique (hero, az090): the muzzle is a thin spike against the sheet's short deep block; the ear is edge-on from the side.
- Diagnosis: H0-H2 widths 0.036-0.072; ear disc lies in a y plane.
- Fix: muzzle box 0.044-0.082 wide with square corners, cheek front 0.165, brow corner pulled 1.2 cm forward (overhang);
  ear turned ~30 degrees outward; eye loop smaller and up under the brow.
- Result: better - the muzzle is a block with a stop, the ear shows its disc from the side. Gates PASS, 812 tris,
  IoU 0.972/0.928/0.82, max proportion diff 6.0%.

## Round 12 - rump
- Critique (az180): the rump is a peaked roof with slab legs under it; the sheet's rear is a broad round haunch.
- Diagnosis: T6-T8 upper corners at x 0.14-0.19 leave a steep roof plane from the spine to the hip point.
- Fix: upper corners out to 0.185-0.225 (a broad croup plane, then the haunch drops), T8 0.285 wide, tail ball 0.085.
- Result: better - broad croup, bigger tail ball. Final (orbit run): gates PASS, 812 tris, quad share 99%,
  loops elbow 3 / wrist 2 / stifle 3 / hock 3 / neck 2, IoU side 0.972 / front 0.928 / top 0.819, max proportion
  diff 6.0% (fore limb thickness). Blockout ROM 46 tris, 4.48% of area. NOT locked (blockout review first).

## Still weak
- Paws are plank blocks under a clean 6-ring at the wrist/hock; the library paw_bear should be welded there
  (bridge_part(..., bm=bm)) before the lock or laid over in stage 3. Leaving the ring open fails the closed-shell gate.
- ROM folds sit on the inside of stifle, hock and elbow bends (not the roots); 4.5% of area, above the pilot's 3.3%.
- Head: the face is still shallow in the hero view (brow overhang 1.2 cm, eye loop only); legs are near-constant
  hexagonal columns from the rear; neck ruff is one 2.5 cm step, not a stepped fur mass.

## Rounds 13-15 (earlier session, not noted then)
- Library paw_bear welded onto each limb's last ring (bridge_part bm=bm, toe_segs=1), third wrist loop; locked at round 15.
  That lock is kept as `stage1_lock.r15.json.bak`.

## Round 16 - blockout review applied (stage 1 UNLOCKED: the review's verdict was FIX) - 1164 tris
- Review items, checked in blockout/: (1) head: cranium and cheeks wider (H4-H6 0.224-0.242), brow/stop raised 1 cm;
  ears come from the library in stage 3 on the skull corners. (2) torso: T1/TN wider in front of the leg (shoulder mass),
  T2/T3 top corners in to 0.14 (hump narrows upward), waist T4/T5 in to 0.278/0.255. (3) hind leg: knee forward (front
  edge 0.375 at z 0.36), shank front falls back to 0.52, hock point at the back 0.848, section tapers 0.14 -> 0.098;
  fore: elbow point back to 0.135, forearm thicker (fore thickness -5.6% -> +1.4%). (4) paws: library wedges, 0.10 tall,
  wider than the leg, fore turned out. (5) ROM: NOT met - 56 tris, 3.95% of area (target 2%); the folds are the inside
  faces of 80-90 degree bends on 0.25-0.3 m thick limbs (DIAG), not a loop-count problem.
- Result: gates PASS. IoU side 0.965 / front 0.909 / top 0.813, proportions max 4%, loops elbow 3 wrist 3 knee 3 hock 2
  neck 2. Locked, edge hash 71567290dc4c3eef.

## Stage 2, round 2 - 1244 tris
- Critique: sliver gate FAIL (28-48 needle triangles) on the lower-leg ring stack and at the leg roots' inner columns.
- Diagnosis: bands under 2 cm on 15-20 cm wide faces (min angle < 6 deg): sock ring zigzag against its neighbours, inner
  root rings 0.5-2 cm apart, the tail's root band.
- Fix: respaced the lower-leg rings (no band under 2.3 cm), inner columns evenly spaced, tail ball 2 cm off the rump.
- Result: PASS, slivers 18 (all in the library paw's own side walls: kit note). 4 logged loops (forehead, neck ruff,
  two sock borders). IoU vs stage 1 min 0.991.

## Stage 3
- Round 1 (2112 tris): five fur clumps (hump crest, chest, cheek, elbow, haunch). Critique: they read as spikes glued
  on, the crest breaks the hump outline, haunch clumps hit. Fix: keep only jowl and chest ruff, lying flat.
- Round 2: chest ruff still passes through the chest keel twice (hit). Fix round 3: chest ruff removed (the bib is
  painted); palette lightened (fur #a2683f, sock #55372a, cream #e0c39a) - round 2 read muddy-dark. PASS, 1824 tris.
- Round 4: the sock border was a level line. Fix: every other facet of the band above the ring painted sock (fur
  points on edges); ears 0.135 long. PASS, 1824 tris, 6 colours (accent: amber iris).
- Parts: paw_bear x4 (welded, claws as pieces), eye_set 'angry' with brow x2, ear_cup round x2, nose_pad bear,
  fur_clump n=3 jowl ruff (mirrored). No hand-built pieces. Tried and dropped: fur_clump chest/hump/elbow/haunch.

## Stage 4
- Round 1: rig on J (roll auto), idle / move / attack. All gates PASS, 0 fold-overs. Critique: hind swing foot flipped up.
- Round 2: hind swing keys (thigh 8, shin -26, foot -6). Round 3: final with orbit. PASS. WARN: 44 tris (3.3%) clip in a
  pose (raised paw against the jowl ruff / chest in the attack).

## Still weak
- The head hangs low and the back/flank still shows ring bands in the 3/4 view; the cage follows the sheet's side view.
- Sock border points are square facets, not the concept's long zigzag; jowl ruff reads as a lump from the side.
- Blockout ROM 3.95% at 80-90 degree bends; clips stay under 35 degrees per joint so the posed gate is clean.
