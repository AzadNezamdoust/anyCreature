# boar (t7) build notes

No reference/ folder: stage 0 is mine (blueprint.json drawn from the brief: 0.9 m crest, 1.4 m long, 0.46 m wide).
Tusks are built as stage-3 pieces (brief lists them as detail pieces); the base carries the hump, the long wedge head, the flat snout disc and a dorsal ridge for the crest.

## Stage 1
- r01: 560 tris, IoU side .93 / front .927 / top .959. Critique: the head reads as a long round cone (anteater) in az090/hero, the jaw line flat and high, no wedge. Diagnosis: SEC 2-6 bottoms 0.28-0.35 and narrow belly x. Fix: deepen jowl/throat (bottom to 0.245-0.26 at S4/S5), widen belly x, make cheek sides near-vertical planes (low x >= side x).
  Result r02: better, jaw now drops to a jowl; 560 tris, IoU .933/.93/.962.
- r02: Critique: legs long and spindly, the body rides high on stilts (az090, hero) instead of a chunky front-heavy boar. Diagnosis: belly bottoms 0.35-0.43 in SEC 6-11 and leg ring widths .028-.055. Fix: deepen chest/belly (bottoms 0.30-0.41), elbow/stifle rings down to 0.24, thicken every leg ring ~15%.
  Result r03: better: deep chest, chunky legs, jowl reads (single az090 PNG; the sheet thumbnails looked unchanged, checked the PNGs). 560 tris, IoU .919/.932/.955.
- r03: Critique: the back line is almost level behind the hump (az090), so the body is not front-heavy. Diagnosis: SEC 10-12 tops 0.775/0.75/0.72. Fix: drop the rump line (0.76/0.725/0.69) and the tail root with it.
  Result r04: better, the back now slopes from the hump to a lower rump; 560 tris, IoU .919/.932/.955.
- r04: Critique: the spine reads as a soft round back (az000/az180), no bristle ridge for the crest to sit on. Diagnosis: SEC 6-9 upper vertices only 0.03-0.06 below the seam top. Fix: pull the upper row in and down (0.07-0.09 below the top) so the back is a keel ridge from nape to mid-back.
  Result r05: better, a keel ridge runs nape to mid-back in az000/az180; 560 tris, IoU .919/.909/.955.
- r06 (lock): reads as a boar from every view: deep wedge head with a flat disc, high hump, sloping back, short chunky legs. Remaining grey issues deferred to stage 2 (straight foreleg pillar, boxy hooves). Lock.
  Lock r06: 560 tris, edge sha256 beb68c21752586b8, IoU .919/.909/.955 (min .909). Orbit holds.

## Stage 2
- r01: 5 loops (neck, mouth corner, mid-spine, below elbow, gaskin) + nostril and eye-socket insets; wedge hooves, brow pushed out. 692 tris, IoU vs s1 min .996. FAIL slivers 20 (2.9%). Critique: needle triangles on the rump-to-tail annulus, the tail tube and the ear tips (back34 tech). Diagnosis: TAIL radii .012-.020 over 0.07 segments; EAR tip ring .006 x .004. Fix: scale the tail rings x1.6-2.4 about their centres and the ear tip ring x2 (vertex moves only).
  Result r02: PASS; slivers 2 (0.3%), IoU vs s1 min .989, 692 tris. Eye socket, nostrils, brow and wedge hooves read. Moving on (stage 2 = 2 rounds).

## Stage 3
- r01: paint (6 colours: body, bristle saddle + crest, snout disc, tusk, hoof, eye) + pieces tusk, eye, crest (7 clumps), tuft. 940 tris, all gates PASS, slivers 1.1%. Critique: the tusks are thin cream needles barely visible in hero/az000; the "upward tusks" cue is weak. Diagnosis: tusk rings r .013-.003 and only 0.13 m of curve. Fix: thicker (r .020 base), longer, curving further out and up to z .485.
  Result r02: better, cream tusks now curve up beside the muzzle in hero/az000; 940 tris.
- r02: Critique: the crest reads as a row of sharp saw teeth (az090, hero), not the brief's blunt bristle clumps. Diagnosis: crest front ring only 0.025h above the ridge vs 0.09h at the back, a thin topside (x .02). Fix: raise the front ring to 0.05h, widen the topside to x .026-.028, back to 0.085h: each clump is a blunt leaning block.
  Result r03 (orbit): better, blunt leaning clumps on the hump; 940 tris, all gates PASS, orbit holds.

## Stage 4
- r01: rig (12 bones + .R mirrors, roll auto), skin, pieces bound with body= weights; idle (rooting, 48f), move (trot, 25f), attack (crouch, lunge, tusk toss, 33f). All gates PASS (folds 0, drift 0, slivers 1.1%). Critique: move f07 az090, the lifted forehoof's toe dips below the ground. Diagnosis: forearm -30 / fhoof -20 rolls the toe (0.065 in front of the wrist axis) down more than the wrist rises. Fix: flex the lifted foreleg harder (upperarm +12, forearm -50, fhoof -35) so the wrist lifts the toe clear.
  Result r02 (final, orbit + glbcheck): better, the lifted forehoof folds back clear of the ground; all gates PASS, glbcheck OK (attack/idle/move). Orbit advice: az000 head merges into the body outline (head seen end-on against the chest).

Triangles: stage 1 560, stage 2 692, stage 3/4 940 total. Rounds: s1 6 (lock r06), s2 2, s3 3, s4 2.
