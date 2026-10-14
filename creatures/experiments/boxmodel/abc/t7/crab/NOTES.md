# crab (t7) build notes

No reference/ folder: blueprint.json written by hand (stage 0).

## Stage 1
- r01 Critique: 6 self-intersections (gate FAIL); legs read spidery-thin and the palm is a thin plank from the top. Diagnosis: coxa section (LEG_PROF[0], r=0.04 z=0.185) rises so steeply that its upper corners tilt back into the carapace side slope over legs 1-2. Fix: coxa out further and lower (r 0.06, z 0.168; merus r 0.13 z 0.24). 1104 tris.
- r02 Result: 0 intersections, all gates PASS, 1104 tris. Critique: legs are pencil-thin stilts (az000, top): reads as a spider crab at best, not a chunky stylised crab. Diagnosis: LEG_PROF hu/hw 0.02-0.036. Fix: legs ~1.4x thicker (merus 0.050 x 0.032), joints still pinched.
- r03 Result: better, legs read as chunky crab legs; 1104 tris. Critique: the claws are the hero cue but read as long thin planks (top, az000: a tiny dark block), the arm is too long. Diagnosis: CLAW palm hw 0.05-0.056 and palm 0.25 m in front of the carapace. Fix: palm swollen (hu 0.095, hw 0.075), arm shortened by ~0.06 m, fingers thicker.
- r04 Result: better, the palm reads as a swollen claw from front and 3/4; 1104 tris. Critique: the carapace reads as an egg in the top view (as long as wide, widest mid-body), front teeth invisible. Diagnosis: ST half-widths peak 0.40 at y=0 and taper evenly both ways. Fix: carapace widest in the front third (W 0.44 at y -0.08), a steep toothed anterolateral margin (teeth +0.035), leg reach scaled 0.8-0.9 to keep the 1.5 m span; claw arm root moved out with the rim.
- r05 Result: better, top view now a wide crab carapace with a toothed front margin; 1104 tris. Critique: the claw reads as a box with a slot (az090, hero): the fingers are stubs (0.07 m against a 0.15 m palm). Diagnosis: DACTYL/POLLEX have 3 short sections. Fix: 4-section fingers ~0.13 m long that bow apart (0.056 m gap mid-way) and close at the tips.
- r06 Result: better, the claws read as open pincers in hero and side; 1136 tris. Critique: from the front (az000) the claws cover the whole carapace front up to its top: no face zone left for the eye stalks and the toothed rim. Diagnosis: CLAW palm/fingers sit at z 0.20-0.30. Fix: carpus-to-fingers lowered 0.03 m (arm eased down), claws now below the front rim.
- r07 Result: better, the carapace front and top line clear the claws in az000; claws still read as the hero; 1136 tris. Reads as a crab from every view: lock (r08, no change). The carapace top is many thin strips (tube-ish): that is a stage-2 flatten job.
- r08 LOCK: 1136 tris, edge sha256 63324afd8f1f5797. Blueprint IoU side 0.737 / front 0.665 / top 0.572 (min 0.572: the hand-drawn top outline has fat triangle legs).

## Stage 2
- r01 plan: the front cap is one flat hexagon (no face) and the dorsal carapace is 14 thin strips (tube look in hero wire). Fix: inset the front cap into a recessed socket (eye orbit, 0.016 deep) and flatten the carapace top rows into three planes (front slope, dorsal plate, rear slope).
- r01 Result: better, top view shows three dorsal plates and a V rostrum between two sockets; gates PASS, 1148 tris, min IoU 0.991. Critique: the side slopes of the carapace (p1-p2 band) still read as a rounded ribbon of strips in hero/back34. Diagnosis: the p1/p2 rows follow the curved W(y) plan. Fix: flatten them into a mid-lateral (stations 6-9) and a rear-lateral (11-14) facet.
- r02 Result: better, the side slopes now break into two big facets per side (hero, top); gates PASS, 1148 tris, min IoU 0.991. Stage 2 done (2 rounds).

## Stage 3
- r01 plan: paint shell / ridge (flank under the rim, sockets, knuckles) / cream belly / dark leg and finger tips; pieces: 5-sided eye stalks out of the sockets with 6-sided black bulbs, 4 finger teeth (ray-cast onto the inner finger edges), 3 barnacle cones on the rear rim (one side).
- r01 Result: gates PASS, 1440 tris, 6 colours. Critique: in colour (hero, az090) the whole crab is one flat red: ridge and shell are too close and the cream belly is hidden underneath, so no colour design reads. Diagnosis: body_rule gives cream only to faces with n.z < -0.45/-0.55 and ridge only to the flank under the rim. Fix: a dark-red dorsal saddle plate (central band, stations -0.20..0.17), cream on every down-facing claw and leg face (claw n.z < -0.05, legs n.z < -0.15): two-tone limbs.
- r02 Result: better: dark saddle on the dorsal plate, cream claw undersides and two-tone legs read in hero and top; 1440 tris, gates PASS. Critique: the small pieces are timid: eye bulbs are specks from the top and the barnacles vanish at hero distance (STYLE: few and bold). Diagnosis: bulb radius 0.027, barnacle heights 0.014-0.022. Fix: bulbs r 0.034 (top at z 0.39, the brief's 0.4 height), barnacles 1.5x.
- r03 Result: better: bold eye bulbs top the silhouette at z 0.39, the barnacle cluster reads on the rear rim (az135); 1440 tris, all gates PASS. Stage 3 done (3 rounds).

## Stage 4
- r01 plan: 35 bones from J (body; per leg a/b/c = root-knee-bend-tip; claw a/b/hand + dactyl and pollex), roll='auto'; eye bulbs rigid on body, stalks/teeth/barnacles with body= weights. idle 48 f (two claw clicks, breath), move 25 f (alternating leg groups, body sway), attack 32 f (rear, open wide, lunge, snap).
- r01 Result: all gates PASS (0 fold-overs, 0 drift), 1440 tris. Posed: attack f008 opens the dactyl upward into a wide gape and rears the front (signs right); idle clicks read. Critique: the scuttle is too subtle: in move f007 (az090) the lifted group's tips rise only ~1 cm, so it reads as a shiver, not a scuttle. Diagnosis: leg_a lift +14 deg, leg_c -8. Fix: lift 22 deg, tip tuck -12.
- r02 (final, orbit + glbcheck): better, move f007 shows the lifted group clearly; all gates PASS (hit 0, float 0, z-fight 0, sliver 1.1%, flips 0.00%/0.00% area, drift 0), glbcheck OK, 1440 tris. Stage 4 done (2 rounds).

## Triangles per stage
s1 1136 (locked, edge sha256 63324afd8f1f5797) / s2 1148 / s3 1440 total / s4 1440.
