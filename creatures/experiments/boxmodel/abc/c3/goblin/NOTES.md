# goblin c3: stage-1 cage on the part guide (grey; rebuilt after review_topology.md, locked at r26)

Earlier rounds r1-r13 (first c3 cage, 956 tris, 12-sided torso): see git history of this file; the review scored it
form 7.0 / topology 7.5, verdict FIX. This file covers the rebuild on the improved part base.

## Layout (one closed quad shell, left half, 1128 tris, 0 triangles, 0 n-gons, 0 valence-6)
- torso  6 rings x 16 sides (hip loop, haunch, pot belly, waist, under-chest, shoulder ring); bottom and top grids 3 x 2 per half.
- arm    out of the two side faces under the shoulder ring; 12 rings, 6-sided rounded boxes (flat front / back 0.55 x width).
         Root top corners are grid corners whose only torso edge runs to a valence-4 vertex: 4 of 6 lengthwise edges run on.
- leg    out of the bottom grid's outer column (hip loop over the joint); 6 rings to the ankle, level ankle base, tilted heel
         ring, mid foot, toe base, toe tip.
- neck   base loop on the shoulders (its two valence-5 poles stay there), two loops inside the joint band, the skull's hole.
- head   5 rings front -> back (12 sides), back-of-skull grid; face ring; nose 8-sided out of the inner column, closed on a
         seam vertex; eye socket loop in the quad between the face ring and F's brow / cheekbone; mouth = lip loop + sunk loop.
- ear    4-sided blade out of the temple face (unchanged in kind).

J: `chest` moved to (0, 0.05, 0.675) (on the spine, at shoulder height): the neck band is 4.9 cm and its planes tilt
with the hunched neck, so chin, mouth and nose tip poles are outside it. `clothF / clothB` only feed META['later'].

## Rounds (rebuild; each: worst problem -> cause -> fix -> result)
- r14 rebuild on the new base (two debug runs): crotch self-intersection (first thigh ring inside the crotch grid) -> ring
  to t 0.17, narrower, 1 cm out; head edge ratio 4.9 (tiny mouth / nose-tip edges) -> bigger; 10 poles in the neck band
  (band is an infinite slab: chin, mouth corner, nose tip, skull base fall in it) -> chest joint back and down, skull base
  and hole raised, shoulder base lowered. Topology gates pass; IoU 0.853 / 0.817.
- r15 valence-6 fan at the inner brow: the eye loop and the nose loop shared an edge, both add an edge to its two ends ->
  eye loop moved one quad out (inner corners on the face ring, outer on F), a buffer quad between nose and eye. 0 fans.
- r16 arms and hands to the blueprint polygon: front 0.854 but arm profile RMS 3.6% (the polygon's arm is a 0.09 band, the
  sheet mask's own runs are 0.055-0.068) -> rejected in r17.
- r17 arm widths from the sheet mask's runs (deltoid, thin upper arm, elbow 0.098, thin forearm); hand ring twisted about the
  arm (palm turned in) so the side view sees its width; loincloth declared META['later']. Side 0.873, front 0.831.
- r18 sloped shoulders, wider jaw corners (jowl), hand 0.15, foot flare, belly / back to the side view. 0.893 / 0.836.
- r19 mouth and chin forward, jaw line lower over the neck notch, nape in, ear edges, elbow depth = width. Side 0.905.
- r20 trapezius up to the neck, deltoid 0.08, forearm +0.8 cm, finger twist 65 deg. 0.911 / 0.842.
- r21 forearm out, ear top by the front view; `leg limb thickness` declared intended (below). Ear edge ratio 5.2 (tip 8 mm).
- r22-r23 ear tip 2 cm; crown corners in 5 mm. IoU 0.901 / 0.849.
- r24 hand 1.2 cm in, ankle-to-foot flare, knee back. All gates pass: 0.902 / 0.857.
- r25 neck loops narrower than base and hole (0.88) and 0.0425 apart (0.25 x width); finger row 20% narrower (review 5).
  Side 0.899.
- r26 fingers thicker than the palm (curled). All gates pass, orbit holds; locked.

## Review fixes
1. Head front masses: done. Crown corner 0.108-0.115 (was 0.10-0.11; the blueprint polygon cuts the dome, so less than the
   12% asked), cheekbone 0.176-0.180 (+10%), jaw corner 0.14 low at the jowl, chin 0.05 (0.3 x cheek), brow shelf over
   sunk eye sockets, nose root from brow to lip, sunk grin.
2. Mouth and eye loops: done (table: eye present, mouth present). +21 faces per half on the head.
3. Neck loops: done differently. 4 loops 0.0425 apart (0.25 x width): base, 2 in the band, hole. Three loops INSIDE the band at
   that spacing do not fit: the base and hole loops carry poles and must stay outside it. Poles are on the shoulder loop,
   one face below the first neck loop.
4. Shoulder flow: 4 of 6 arm edges run on (by count; table says 0.83, see kit problems). Arm-root-top pole now on the
   neck-base loop (trapezius). Elbow rings 0.047-0.051 apart (0.51 x width).
5. Ankle 3 rings (0.53 x width); heel / sole re-gridded, worst face 4.9:1 on the whole body (was 7.6); finger row 20%
   narrower. Palm kept at the sheet's 0.146 (the profile reference there is the guide's 0.082, one finger row). No finger
   stubs: hands are a stage-3 library piece (BRIEF 3).

## Waivers (4 + 1 later part), why
- `leg length / body height` (+66%): the sheet's centre-line clearance is the loincloth tip; loincloth = stage-3 piece.
- `iou_floor top 0.45` (0.479): the plan view contradicts the side view (ears straight vs swept, hands, toes); side wins.
- `head profile` RMS 18.8%, depth taper 42: stations on neck > head cut both ears and run into the shoulders; one has
  near-zero model depth (the plane leaves the head). Not a measure of the head.
- `leg limb thickness / length` (-56%): the sheet's side run at mid shin is shin + hanging hand (0.17 m); the model's hand
  hangs 1-2 cm clear of the shin in that view. The leg profile gate passes unwaived (RMS 2.44%).
- `later: loincloth` (capsule r 0.06 between the legs and behind the thighs): IoU measured outside it, model and sheet alike.

## Sizes: where each came from
part_rings budget followed: limbs 6 sides, 3 rings at elbow / knee / wrist / ankle, one mass ring per bone, ends. Torso is
16-sided, not the suggested 8: the 3 x 2 end grids are what give the arm and leg roots their edge flow and keep the neck
poles off the arm root; density stays even (torso 0.91 x, edge ratio 2.75). Nose 8-sided, not 4 (it carries the brow-to-lip
loop). Arm widths = sheet runs on the guide's stations; thigh and knee by eye (guide = prior); shin, ankle, foot = guide.

## Kit problems (not edited)
- topology(): the arm's `root` is reported as a 36-vertex loop at t 1.58 (centre near the knee), so `flow 0.83`, `verts`
  and `poles` in roots.arm are not the arm root's. The gates still read loop / over_joint True.
- joint band = an infinite slab square to the bisector: for an upright biped the neck band takes in chin, mouth and nose
  tip, and the pole gate fires on face poles 20 cm from the neck. Limit it to the ring's own radius.
- part_profiles / proportions: where the hand hangs in front of the leg the sheet's side run is leg + hand (thigh 0.133,
  knee 0.19, shin 0.155-0.18); whether the model's run fuses the same way flips on 1-2 mm (leg RMS 2.4 <-> 4.4, thickness
  -19% <-> -56%). Palm station: sheet 0.146 is rejected for the guide's 0.082.
- blueprint.json front polygon (21 points) is fatter than the sheet mask in the arms and cuts the cranium dome and the
  shoulders with chords; the IoU gate itself uses the masks.
- Sheet feet sit 2.3 cm above z = 0 in both views: a constant red band under the feet in the IoU.
- Eye loop + nose loop on a 12-sided head: if they share an edge both ends go to valence 6; stage-2 `inset` on the
  quad next to the nose would do the same.
- orbit: "no head found" although J has `head`.
