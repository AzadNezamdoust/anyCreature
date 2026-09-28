# boar (w4) build notes

## Stage 1
- r01: first blockout, 15 half-rings (6 verts, 10-gon), hexagonal legs extruded from the lower-side faces, 4-sided ears. 536 tris. IoU side/front/top 0.845/0.88/0.902.
  Critique: the body reads as a crate with a near-straight back; the shoulder hump (the identity cue) is weak and the rump is a flat cut (side, az090).
  Diagnosis/fix chosen first: the legs are the cheapest large miss — front and hind legs read as thin poles (hw 0.045, hd 0.055) and sit inside the traced leg masses. Fix: thicker forearm/gaskin levels (hd 0.068-0.072, hw 0.05), hind hoof forward to y 0.43.
- r02: 536 tris, IoU 0.853/0.875/0.900. Result: legs better, still slim but read. Critique: the head reads as a thin cone, not a boar wedge (az045, hero): the forehead is a ridge.
  Diagnosis: HEAD profile ku=0.50 puts the upper vertex at half width, so R11-R14 peak along the seam. Fix: new MUZZ profile (ku 0.80, hs 0.55, kl 0.96) on R11-R14 for a flat broad forehead and square muzzle; R9/R10 keep the narrow top as the ear seat.
- r03: 536 tris, IoU 0.853/0.875/0.901. Result: better — the forehead is a broad plane and the muzzle a tapered box. Critique: the ears are thin upright spikes (az000, hero); the reference ears are broad leaves splayed up-and-out and tipped forward.
  Diagnosis: ear levels E1-E3 rise nearly vertically from x 0.13 to 0.18, broad axis almost horizontal. Fix: tip out to x 0.21 and forward to y -0.305, wider mid (ha 0.044), broad axis tilted (1, 0, -0.55) so the leaf faces forward-out.
- r04: 536 tris, IoU 0.852/0.849/0.894. Result: better — ears read as splayed leaves in front and hero. Critique: the rump ends in a big flat octagon plate (az180, az135); the reference rump rounds off into the hams.
  Diagnosis: cap ring R0 is 0.14 wide x 0.20 tall right behind R1. Fix: R0 shrunk (w 0.055, z 0.42-0.55, y 0.562) so R0-R1 becomes a rounded, sloping rump; R1 hams slightly wider (w 0.135).
- r05: 536 tris, IoU 0.854/0.849/0.898. Result: better — the rump rounds into the hams (az135, az180). Critique: the torso still reads as a crate: flat top, vertical flanks, sharp horizontal top edge (hero, az045); the shoulder hump is weak.
  Diagnosis: BODY upper vertex at 0.72w only 0.10H below the top. Fix: section top narrowed and dropped (ku 0.64, hu 0.15; hump rings ku 0.52 hu 0.12) and R7/R8 raised to 0.845, so the back becomes a sloping-shouldered barrel with a ridge over the withers.
- r06: 536 tris, IoU 0.858/0.848/0.898. Result: better — sloping-shouldered barrel with a withers ridge; reads as a boar from hero/az045/az090. Remaining: the head is a smooth cone without jowl/brow/stop planes; that is vertex work and face loops, so it goes to stage 2.
- r07: lock round, no geometry change (orbit on).

## Stage 2
- r01: +2 limb loops (upper foreleg, upper hind leg), eye-socket inset, nostril inset; brow, jowl, snout-lip and belly-tuck vertex moves. 584 tris-ish; gates PASS, IoU vs s1 min 0.984, tech QA clean. Result: the socket reads under the brow in hero; the disc has a lip. Critique left for stage 3: identity cues still missing (tusks, crest, colour), not base shape; stage 2 closed after 1 round.

## Stage 3
- r01: body paint (brown, dark saddle over the withers on the R9-R6 loops, snout disc, hooves below the fetlock loop), eye lens, tusks, 7 crest clumps, tufted tail. 802 tris, 6 colours, QA clean. Result: reads as a boar from every view.
  Critique: the crest is a row of separate thin teeth — a dinosaur spine, not a bristle mane (az090, back34, top). Diagnosis: clump top edge 0.02 wide on 0.06-wide bases with gaps. Fix: blunt wide clumps (base 0.08 x 0.078, top edge 0.044 wide) that butt end to end.
- r02: 802 tris, QA clean. Result: blunter but now square battlements — blocks, not hair (hero colour). Diagnosis: top edge sits over the base centre, so each clump is an upright slab. Fix: sweep each tuft back (top edge at y+0.058, past the base end, 0.024 wide) for the swept sawtooth mane of the reference.
- r03: 802 tris, QA clean. Result: better — a swept sawtooth mane like the reference (az090, back34). Critique: tusks are thin sticks lying along the face (az000 colour, hero); the reference has thick cream crescents sweeping out then up. Diagnosis: tusk path stays within x 0.14 and radii 0.017-0.008. Fix: radii 0.024-0.011 and the path sweeps out to x 0.156 before turning up.
- r04: 802 tris, QA clean. Result: better — thick cream crescents read in the front view like the reference. Stage 3 closed.

## Stage 4
- r01: 10 deform bones (hips, spine, neck, head, 3 per leg, mirrored), roll auto, bone-heat skin; all pieces bound with body= weights. Clips idle 48 (sniff/root), move 25 (diagonal trot), attack 32 (head-down charge, lunge, tusk toss). All gates PASS: 0 flips, 0 drift. Posed side renders: head drops in idle/attack, lifted forearm folds backward, lifted hind hoof tucks — signs correct; neck holds without collapse.
- r02: final round with orbit + glbcheck, no change.

Triangles: stage 1 = 536; stage 2 = 584 (base); stage 3/4 total = 802.
