# boar k3 NOTES

Reference present (sheet G/O). Blueprint untouched except marks (eye, shoulder, hip, hock, wrist, snout, ear_tip).
Conflict: the reference top view is shorter than the side view (hind hooves at y~0.26 vs 0.44-0.55 in side); side wins.

## Stage 1
- r01: Critique: body reads as a crate - flank is a vertical wall (az090/az000), no keel, rump a flat plate. Diagnosis: SECT v3 at x~0.225 ~= v2, rump ends in one section. Fix: v3 pulled in to ~0.19-0.205 (keel chest, tucked belly rising to 0.31), widths taper shoulder->loin, extra rump-rounding section at y=0.56. Result: 444 tris before; see r02.
- r02: Critique: legs read as thin stilts pinned to the body (az090, hero); the reference has a thick forearm and a ham that runs down to the hock. Diagnosis: FRONT_LEG/HIND_LEG ring 1 no wider than the root face, wrist/hock too thin. Fix: ring 1 flared (forearm hy .074, ham hy .082), wrist/hock slightly thicker, hooves broader. Result: 464 tris (keel/taper change of r01 subtle but in); see r03.
- r03: legs thicker (subtle but right; 464 tris). Critique: head does not read as a separate wedge - the top line ramps straight from snout to hump, ears sit mid-slope (az090 vs ref side, where the nape dips behind the ears and the hump rises). Diagnosis: SECT y=-0.33 top at .76 continues the forehead line. Fix: nape section top dropped to .715 (v1 .68), cheeks at y=-0.43 widened to .165 for jowls. Result: see r04.
- r04: nape dip and jowls read in the single az090 render (the 400px sheet tiles hide small moves; checking single PNGs too). 464 tris. Critique: rear end is a vertical plate with the tail stuck on it; the ref rump rounds off above the tail and recedes under it to the ham (az090, az135). Diagnosis: last two SECT rows (y .52/.56) are flat y-planes. Fix: rump row at .505 raised, rounding row given per-vertex y (top and bottom recede, middle proud). Result: see r05.
- r05: rump rounding row now recedes top/bottom (464 tris); reading hero/az090 PNGs via a 2x2 montage since sheet tiles are too small. Critique: head reads as a thin cone/anteater snout (hero), the ref has a thick wedge muzzle and a big snout disc. Diagnosis: SECT rows y -.665..-.52 narrow (x .076-.12) and low-topped. Fix: disc enlarged (half-width .084, z .21-.345), muzzle rows thickened/raised, face row widened to .135. Result: see r06.
- r06: disc/muzzle enlarged (verified in the s1.glb: disc half-width .084); 464 tris. Critique: the spine crest - the boar's signature - is barely there; back line is a soft slope and the top of the ref side outline (crest at .87-.90 over the shoulder) is missed (az090, az000). Diagnosis: seam-top v0 only ~.07 above v1 on rows y -.33..+.25. Fix: v0 raised +.03 on those five rows, a sharper keel ridge from nape to mid-back. Result: see r07.
- r07: crest ridge now reads in az000/az135/hero; side IoU .840 -> .857; 464 tris. Critique: hind leg is a straight post (az090) - no hock angle, the ref's hind cannon slants forward from a hock set back under the ham. Diagnosis: HIND_LEG hock ring at y .515 sits between stifle .478 and fetlock .495. Fix: stifle ring forward to .465, hock ring back to .535 (z .155), fetlock .500; J updated to match. Lock on this round.
- r08 LOCK: hock angle reads in az090; 464 tris; IoU side .858 front .899 top .810; orbit rc=0. Locked (edge sha ad05e5aafb2ec007).

## Stage 2
- r01: plan: neck loop (nape->hump) and mid-back loop for deformation, eye socket inset under a brow overhang, keep_valleys on the socket.
  Result: gates PASS except slivers 20 (3.8%). Diagnosis (triangles measured from s2.glb): all < 6 deg are the tail's two long thin quad segments (0.1 m long, 0.012-0.018 m radius).
- r02: Fix: two loops around the tail (root bend, mid bend) halve the segment length; also the tail's bend points for the rig.
  Result r02: all s2 gates PASS, slivers under limit, 560 tris, IoU vs s1 min .997. Eye socket and brow read in hero wire.

## Stage 3
- r01: plan: paint body/bristle saddle/snout/hoof; pieces crest (7 blunt clumps nape->mid-back), tusks, eye lenses in the sockets, nostril blocks, tail tuft.
  Result r01: all s3 gates PASS; 694 tris; 6 colours. Reads as a boar (crest, disc, hump).
- r02: Critique: tusks are tiny slivers (hero, az000), the ref's big cream tusks are a main identity cue. Diagnosis: tusk tube radius .017 -> .010, tip only .13 above base. Fix: tusk thicker (r .022/.019/.014), longer, tip out and up to (.19,-.555,.425).
  Result r02: s3 PASS, 694 tris, tusks read in hero/az000. Palette renders darker than the ref under workbench light (brief values kept).

## Stage 4
- r01: rig on J (spine/hips/neck/head/ears/legs/tail, roll auto), skin, all pieces bound with body weights; idle root-sniff, move diagonal trot, attack head-down charge + toss. Final run with orbit + glbcheck.
  Result r01: all gates PASS except posed flips 50 (7.2% tris, 0.59% area). Diagnosis from techqa.json: 46 on the eye (flattened octahedron: its neighbour-normal average is ~0, so the fold test flips on noise) + 4 on the belly behind the elbow (tech heatmap az090) from the 22-deg trot swing. glbcheck OK.
- r02: Fix: eye rebuilt as a lens (rim, low front apex, smaller back quad) seated proud in the socket; trot swing 22->14 deg, forearm fold 30->22, attack reach 15->10.
  Result r02: eye flips gone; body still 4 flips (0.57% tris, 0.54% area), unchanged by the smaller swing -> a topology/weights problem, not amplitude. Heatmap: belly behind the elbow, one big face between rows y -.08 and +.08.
- r03: Fix: stage-2 barrel loop (logged topo op) just behind the elbow, splitting that long belly/flank band so the elbow skin has a vertex row to bend on.
  Result r03: still 4 flips, same area -> not the elbow. Located the purple in s4_az090_tech.png pixels: under the throat (y~-.3, the nape->hump band) - head-down poses swing throat verts (far below the head pivot at z .58) back into the chest.
- r04: Fix: neck/head joint J['neck'] lowered to (0,-.33,.47) so the throat sits near the pivot; head-down angles eased (idle -10/-11, attack -14/-16, toss 18).
  Result r04: ALL s4 gates PASS (2 flips = 0.28% tris, 0.28% area; 0 drift), glbcheck OK, orbit rc=0 (advisories: head merges with body at az000, hidden at az180). Totals: s1 464 tris, s2 body ~572, s3/s4 726 total.

## Repair pass (K=1, 2026-09-28, notes review/ad_notes.md; stage 1 locked, no unlock)
- r09 baseline (new kit): all s4 gates PASS (3 flips 0.41% tris / 0.38% area, clip 0). No item 0.
- r10 item 1 crest. Critique: 7 identical needle spikes (az090). Diagnosis: one apex triangle per spike, equal spacing. Fix: crest rebuilt as ONE connected strip of 5 clumps (h .100/.074/.086/.060/.046, tallest at nape), two-vert flat tops, 4-vert half sections, bases raycast onto the body and sunk. Result: gates PASS, 872 tris; but deep valleys read as separate plates (stegosaurus again).
- r11 crest. Diagnosis: valleys drop to the spine. Fix: valleys raised to 35% of the lower neighbour; long front slope, tip combed back. Result: one ridge of uneven clumps; top reads a bit castellated.
- r12 crest. Fix: back top vertex lowered to 0.70h, so each clump top slopes back like a combed tuft. Result: reads as blunt tufts (az090).
- r13 item 2 mantle. Critique: dark box on the flank with vertical edges. Diagnosis: rule painted the whole v1-v2 band y -0.34..0.02. Fix: stage-2 slide of the -0.08 row's v1/v2 verts (raked edge); paint = back band (v0-v1) nape->mid-back loop + upper flank only between neck loop and the raked edge. Result: gates PASS, IoU min .996.
- r14 item 3 tail. Fix: stage-2 tail verts scaled about the tail axis 1.5x root -> 1.2x tip. Result: tail has section in back34; but slivers 6 (0.7%): 2 body (r13 slide put v1 .021 from the barrel loop), 4 crest (r12 back top too close to the next valley).
- r15 slivers. Fix: slid v1 only to y -0.062; crest tops at 0.55L/0.86L. Result: slivers 0.
- r16 item 3 tuft. Fix: tuft rebuilt as one blunt wedge (pentagon outline, flat 2-vert tip, one side ridge vert, 10 tris, thickness ~0.06 vs width 0.076), rooted 20% into the tail tip. Result: PASS, reads as a stub (too small).
- r17 tuft enlarged (L .13, width .076). Result: reads as a tuft in az090/back34.
- r18 item 4 eye lens 1.5x (rim .0315/.0225, depth 1.5x). Result: two eyes visible in az000; eye flips 0, z-fight 0.
- r19 item 4 brow: the socket face's top-edge verts out .009, forward .006. Result: IoU .99; overhang subtle.
- r20 item 5 nostrils: 6-sided discs r .021 (25% of the disc), front face .0035 proud. Result: round, flush, z-fight 0; 890 tris.
- r21 should-fix ears: back verts of the ear base ring +.007 y. Result: flips 3 -> 2 (0.22% / 0.17%).
- r22 final (orbit + glbcheck OK; advisory az000 head_merged), --review, --compare. clip 0.

## Repair pass (K=2, 2026-10-03, notes review/ad_notes_r2.md; stage 1 locked, no unlock)
- r23 baseline: all s4 gates PASS (2 flips 0.22%/0.17%, clip 0, drift 0). No item 0.
- r24 item 1 mantle. Critique: dark box on the shoulder, vertical back edge (az090, hero, top). Diagnosis: r13 rule painted the whole v1-v2 band between the neck loop and the -0.08 row. Fix: per-face rule vs top_z(y): depth 0.18 (nape) -> 0.12 (withers) -> spine faces only. Result: PASS; top still boxy to y 0.
- r25 mantle: depth 0.12 -> 0.04 at -0.08, 0 behind (crest carries the dark to mid-back). Result: wedge nape -> withers, then the crest strip.
- r26 item 2 tusks. Critique: short horns on the cheek. Diagnosis: root at (.095,-.57,.262), above the lip line, well behind the disc. Fix: root at the lower-jaw corner y -0.60/-0.612 (~15% head length behind the disc), sunk ~0.045 into the jaw, 4 rings sweeping out then up to a tip (.18,-.656,.385) just above the snout top, base r .030 (~1/3 length). Result: PASS; az000 reads like the reference front (tusks frame the disc).
- r27 item 3 crest. Fix: 6 clumps, lengths .06-.13 (uneven), heights .034 nape-between-ears, .063, .105 withers, .084, .058, .037; back three lean further (top 0.60-0.90L). Result: ridge rises to the withers and falls; drift FAIL 1 (crest) + clip 3: one strip across the head/neck bend.
- r28 drift. Fix: the nape clump split into its own piece 'crestnape' (body= bound). Result: drift 0, clip 0, all PASS.
- r29 item 4 attack. Diagnosis: the old toss peaked at f20, between the packet's f008/f016 samples. Fix: down held f8-f10 (spine -5, neck -8, head -12, hinds gathered), toss held f16-f18 (neck +10, head +15 roll 10, spine loc +0.12 forward), settle f25, rest f32. Result: PASS, flips 1; head left the az090 frame at f016.
- r30 lunge 0.12 -> 0.06 (5% of body length, partly) so the head stays in frame. Result: PASS; f008 head down, f016 head up with tusks over the snout line.
- r31 item 5 legs. Fix (stage 2 vertex moves): wrist ring to ~85% of the forearm (sx 1.36, sy 1.57) with front verts +1 cm forward, pastern ring 0.93x, hind hock ring 1.2x. Result: PASS, IoU min .972; foreleg a column with knee and slim pastern, no hourglass.
- r32 final (orbit + glbcheck OK; advisory az000 head_merged); review showed a dark vertical strip behind the ear at the nape.
- r33 mantle nape depth 0.18 -> 0.13: the nape v1-v2 quad made a vertical border; topology cannot slant it. r34 final: all PASS, 950 tris, clip 0, flips 1 (0.11%/0.08%), --review, --compare.
