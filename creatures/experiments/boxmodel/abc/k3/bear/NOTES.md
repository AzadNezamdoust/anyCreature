# bear (k3) build notes

Reference sheet present: blueprint.json (traced) is the stage-1 target; brief wins on identity/palette/clips, sheet on shape.

## Stage 1
- r01: first blockout, 17 half-sections nose->tail (7 verts each), 6-sided legs extruded from 2 lower-flank quads, 2-step ears. 676 tris, IoU side/front/top 0.922/0.858/0.888.
  - Critique: head reads as a long tapered cone (polar bear/wolf), not the reference's broad boxy bear head with a high forehead and a short muzzle block (az090, hero).
  - Diagnosis: H1-H5 sections are too narrow and the forehead too low/too far back (H3 zt 0.66 at y -0.68, H4 w 0.165).
  - Fix: raise and widen H3/H4 (brow 0.69, skull 0.75, widths 0.15/0.18), square the muzzle H1/H2.
  - Result r02: head profile now has a stop and a higher brow (az090 crop), still reads small; 676 tris, IoU 0.920/0.858/0.880.
- r02 -> r03:
  - Critique: front view (az000) is narrow and pillar-like; the reference's shoulders and upper forelegs bulge out to x 0.33 at z 0.3-0.55 (front IoU 0.858, the lowest).
  - Diagnosis: T1-T3 lower-flank vert 4 sits at 0.88w (x 0.255) and the foreleg's top rings reach only x 0.30.
  - Fix: T1-T3 w4 -> 0.97-1.0 and w up 0.01; foreleg top two rings cx +0.015, rx 0.12/0.108 (outer x 0.33).
  - Result r03: front IoU 0.858 -> 0.904, shoulders read heavier in az000/az045. 676 tris.
- r03 -> r04:
  - Critique: top view reads as a straight bottle; the reference's shoulders flare out right behind the head (x 0.28-0.30 from y -0.35) and the brow is narrower than ours (top IoU 0.879, lowest).
  - Diagnosis: T0 (w 0.20) and T1 (w 0.27) too narrow; H3 brow w 0.15 wider than the traced 0.09-0.12.
  - Fix: T0 w 0.235, T1 w 0.30; H3 w 0.125.
  - Result r04: top IoU 0.881 (+0.002) only; the overlay shows the loss is at the rear (hind heels + haunch corners stick out where the traced rump tapers) and the side view wins on proportions there, so I keep the heels. 676 tris.
- r04 -> r05:
  - Critique: ears are thin spikes (az000, hero) -- a bear needs round cupped ears standing out at the skull corners.
  - Diagnosis: ear extrusion 1 scales y 0.55 with no outward move; extrusion 2 pinches x to 0.6.
  - Fix: ear step 1 widened x1.25, moved out 0.03/up 0.045; step 2 x0.7 y0.75, up 0.028 (a rounded stub).
  - Result r05: ears now read as round stubs at the skull corners in az000/top. 676 tris, IoU 0.921/0.903/0.878.
- r05 -> r06:
  - Critique: the face from the front (az000 wire) is a cone of concentric rings; the reference muzzle is a straight-sided box with a broad nose and a square jaw.
  - Diagnosis: H0-H2 shrink uniformly (w 0.04/0.07/0.095) and the jaw keel (t5 0.45) is a V.
  - Fix: muzzle H0/H1/H2 w 0.055/0.085/0.098 (near-parallel sides, w4 0.95), jaw t5 0.6-0.75 on H0-H4 (flat underside).
  - Result r06: muzzle now a straight-sided block with a flat jaw underside (az000, hero). 676 tris, IoU 0.921/0.903/0.876.
- r06 -> r07:
  - Critique: from behind (az180) the rump is a flat disc with a concentric knob tail; the reference rump is a full rounded mass with the stub tail set high.
  - Diagnosis: T8 (w 0.15, z 0.47-0.66) is too small and too close in size to the T9 tail root, making a flat plate.
  - Fix: T8 w 0.185, z 0.45-0.69, y 0.745; tail root/tip T9/T10 moved back and up (z 0.53-0.64, y 0.775/0.81).
  - Result r07: rump is a full rounded mass with the tail set high (az180, az135). 676 tris, IoU 0.917/0.903/0.874.
- r08: lock. Reads as a heavy bear from every view: hump highest, head low, thick legs, round ears, boxed muzzle. Remaining stage-1 compromise: the flank is still an even run of rings (planes come in stage 2), top IoU held below 0.9 because the side view wins at the hind heels.
- LOCKED r08: 340 verts, 332 faces, 676 tris, edge sha256 bf9cebb404d1f014. Stage 1 rounds: 8.

## Stage 2
- r01: neck loop (H5-T0) and withers loop (T0-T1) for the neck bend; brow pulled forward over an inset eye socket; flattened muzzle top/side and forehead planes; cheekbone out; shoulder blade out, waist in, hip bone out; flat back plane T3-T5.
  - Result s2 r01: all gates PASS, 740 tris, min orbit IoU vs s1 0.987, slivers 0.3%. Brow overhang and socket read in hero; flank now breaks into shoulder/waist/hip planes. Stage 2 done in 1 round.

## Stage 3
- r01: paint 6 colours (fur, dark lower legs below the 0.21/0.17 rings, pale muzzle behind ring H2 + pale chest plane, black nose cap, claws, eyes); pieces: hex bipyramid eye lenses set proud in the socket, 5 claws per paw rooted inside the toe.
  - Result s3 r01: all gates PASS, 884 tris, 6 colours.
- r01 -> r02:
  - Critique: az000 colour: the whole muzzle front is a black square (the nose cap n-gon is the full muzzle end) and the pale chest bib barely shows; the reference has a small nose pad on a pale muzzle and a big pale bib under the throat.
  - Diagnosis: body_rule paints the H0 cap 'nose'; the chest rule's window (z<0.53, x<0.17, n.z<0.3) misses most chest faces.
  - Fix: cap goes 'muzzle'; a separate mirrored nose-pad block (piece) on the front-top of the muzzle; chest window widened to y -0.56..-0.16, z<0.58, x<0.20.
  - Result s3 r02: nose pad reads as a small black block on a pale muzzle (az000, hero); 904 tris. But the widened chest window leaked pale onto the fore paws and the neck side (hero/az090 colour).
- r02 -> r03:
  - Critique: pale patches on the fore paws/inner forelegs and on the side of the neck; the bib should sit only on the front of the chest between the forelegs.
  - Diagnosis: chest rule has no lower z bound and accepts side-facing faces.
  - Fix: chest window z 0.33-0.56, x < 0.17, y -0.56..-0.20, |n.x| < 0.75.
  - Result s3 r03: leak gone; paws dark, muzzle pale, nose pad black; bib now small (mostly under the throat, barely visible head-on). 904 tris, all gates PASS. Stage 3 rounds: 3.

## Stage 4
- r01: rig from J (spine, chest, neck, head, tail, upperarm/forearm/paw, thigh/shin/foot; roll auto), skin, all pieces bound with body= weights; idle (breathe + sniff, 48f), move (diagonal heavy walk, 33f), attack (rear + left paw swipe + lunge, 40f).
  - Result s4 r01: all gates PASS (hit 0, float 0, z-fight 0, slivers 0.2%, flips 0.00%/0.00% area, drift 0, lock PASS). Posed wires: upperarm +X reaches forward (attack f10), forearm -X flexes the paw back in the swing (move f09), head nods down on idle f12; neck ring holds, no collapse.
- r02: final round, no change to the program, run with the orbit + glbcheck.
  - Result s4 r02: all gates PASS; glbcheck OK (attack/idle/move); orbit advises head merged with the body from az000 and hidden at az180. Review packet built (review/).

## Triangles per stage
s1 676 | s2 740 | s3 904 (body 740 + eyes, claws, nose pad) | s4 904. Rounds: s1 8 (lock r08), s2 1, s3 3, s4 2.

## Repair pass (NGO, K=1, 2026-09-28; stage 1 locked, no unlock)
- r09 baseline (current kit, every keyed frame): all gates PASS, clip 0. No item 0.
- r10 (item 1, s3): Critique: pale floods the face to the brow (az000). Diagnosis: the brow move pulled H3 to y -0.697, so the H2-H3 band centres fell inside `c.y < -0.705`. Fix: muzzle rule also needs z < 0.60 (below the socket). Result: pale stops under the eyes, brown between eyes and ears. 904 tris.
- r11 (item 1, s3): Critique: pale jaw/throat stripe in az090. Diagnosis: chest rule accepted side/down-facing throat faces. Fix: bib rule = y -0.56..-0.10, z 0.30-0.58, x < 0.20, n.y < -0.3, |n.x| < 0.5. Result: stripe gone, but no bib visible (face dump: every chest face points down, n.z about -0.95).
- r12-r13 (item 1, s2): Diagnosis: there is no forward-facing chest plane for a bib. Fix: drop the T0/withers keel (r12 -0.07/-0.045, r13 -0.11/-0.08) into a brisket. Result r13: a pale V bib shows under the muzzle in az000 and on the chest in hero-low. IoU min 0.982.
- r14-r15 (item 2, s2): Critique: pointed ears. Diagnosis: the tilted ear slab's inner-back top corner (z 0.816) was the tip. Fix r14: inner top down 0.03, outer top up/out, flatten ear front; r15: back-top down, front-top up/forward (the side view was still a fin). Result: round cup stubs in az000/hero/az090. Slivers 0.2% -> 0.4%.
- r16-r17 (item 2, s3): eye lens r 0.013 -> 0.021 (1.6x), up 0.016, socket faces painted `dark`; r17 lens normal turned 0.5 toward -Y so it reads head-on. Result: eyes read as dots in az000, hero and az090; hit/float/z-fight 0.
- r18 (item 3, s2): withers top (T1, withers loop, T2) +0.02..+0.04, back top (T4-T7) -0.016..-0.03. Result: highest point over the forelegs, back falls about 25% of height to the rump; IoU min 0.966.
- r19-r20 (item 4, s2): Diagnosis: the elbow ring's inner verts (x 0.09-0.114) sat inside the flank line (x 0.135), so the inner leg face tilted up (dark fan). Fix r19: elbow ring down 0.025, inner verts out 0.03, T2/T3 keel up 0.02; r20: T1 keel down 0.03 so brisket -> chest is one slope. Result: near armpit clean; a thinner down-facing fan remains at the far armpit (stage-1 fan topology): partly done.
- r21 (item 5, s2): wrist ring scaled 0.82/0.85, hind cannon ring 0.86/0.88; the paw rings untouched. Result: forelegs narrow visibly elbow -> wrist in az090; IoU min 0.958.
- r22 final (orbit + glbcheck): all gates PASS; hit 0, float 0, z-fight 0, slivers 4 (0.4%), flips 0.00%/0.00% area, drift 0, clip 0, lock PASS, IoU min 0.958, glbcheck OK. Orbit advisories unchanged (head merged az000, hidden az180). Review packet and side_by_side rebuilt.
- Should-fix: claws/nose pad left as they were; muzzle-front flatten not done (it risks the nose-pad seat, low value).
- Triangles: s1 676 | s2 740 | s3 904 | s4 904. Repair rounds r09-r22 (13 fix rounds + baseline + final; three face/vert dump runs were debug only, their sheets deleted).

## Repair pass 2 (K=2, 2026-10-03; stage 1 locked, no unlock; notes review/ad_notes_r2.md)
- r23 baseline (current kit): all gates PASS, clip 0, stretch 0. No item 0.
- r24 (item 1, s3): Critique: the eye is a proud 8-face gem (2_closeups head wire). Diagnosis: `bipyramid` put a point 0.016 out of the socket. Fix: `dome()`: 8 sides, sunk back ring (r 0.8x), rim, low front cap; depth 0.015 (35% of 0.042 width), front 0.005 proud; same width, lens still turned toward -Y, socket paint kept. First try left the band open (8 open edges, bridge needs closed=True). Result: a flat-fronted dot set in the socket; hit/float/z-fight 0.
- r25 (item 2, s3): Critique: a comb of identical needle spikes. Diagnosis: `claw()` = thin pyramids, h 0.011, all equal, parallel, 0.03 apart. Fix: `hook()`: base 0.028 wide (1/7 paw), mid quad lower and 0.6x, tip bent down to z 0.002; length 0.040 (60%), outer pair 80%, fan 0/±6/±12 deg, rooted 25% into the toe; hind 70%. Result: separate blunt dark hooks; 1100 tris; gates PASS.
- r26 (item 3, s2): Critique: muzzle is one flat wedge, no stop. Diagnosis: the H0-H2 top plane runs straight into the brow. Fix: H2 top verts down 4% head height and back 0.006, H1 top up 2%, flatten H0 (nose face). Result: rounded muzzle top with a step under the brow (close-up head, az090); IoU min 0.958.
- r27 (item 4, s2): Critique: tail is a disc with a spoke fan. Diagnosis: the T10 n-gon cap sits flush on the rump. Fix: T10 ring scaled 0.6 and pulled back 0.07 / down 0.04, T9 back 0.025. Result: stub cone, but r29's beauty az090 showed a long thin wedge -> r30.
- r28 (should-fix, s2): paw-top ring scaled 0.9 and its front verts down 0.007 so the paw slopes to the toes (first try picked the hind paw's back verts; fixed). IoU min 0.948.
- r29: orbit + glbcheck run; beauty showed the tail wedge.
- r30 (item 4, s2): T10 scale 0.8, back 0.045 / down 0.03. Result: a short stub hanging back and down in az090 and back34. IoU min 0.949.
- Should-fix far-armpit fan: not done (turn budget kept for the final).
- Triangles: s1 676 | s2 740 | s3 1100 | s4 1100.
- r31 final (orbit + glbcheck): all gates PASS; hit 0, float 0, z-fight 0, slivers 2 (0.2%), flips 0.00%/0.00% area, drift 0, clip 0, stretch 0, lock PASS, IoU min 0.949, glbcheck OK. 4_posed: no stray line above the brow (the dropped item stays dropped). Review packet and side_by_side rebuilt.
