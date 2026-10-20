# Boar (opus) — round notes

## Stage 0: blueprint
Side/front/top outlines from the design numbers: shoulder hump 0.86, nose-to-rump 1.35 (disc -0.785 to rump 0.56),
head ~0.52 long (1:2.5 of nose-to-rump), chest keel 0.30, legs ~0.30, front-heavy top view (0.215 half-width at the
hump, 0.185 at the loin). The drawing reads boar: long straight forehead-to-disc line, high withers, low rump.

## Stage 1
- **r01** Critique: gates FAIL (20 open edges, 2 face-pair hits); visually it already reads "pig", but the head is an
  aardvark cone. Diagnosis: extruding a two-face leg region leaves its middle edge as a loose wire (kit `extrude`
  deletes FACES_ONLY) = the 20 edges; the ear's inner base vertices sit inside x of the H5/H6 back-edge vertex, so the
  ear's inner wall folds through the skull-top face. Fix (gate hygiene, part 1): delete the loose interior edge after
  each region extrude. Result: 0 open edges; 2 hits remain (ear). 668 tris.
- **r02** Critique: gates (ear hits). Fix: ear base centre moved out/up (0.118,0.735 -> 0.132,0.748), base half-width
  0.050 -> 0.042 so its inner wall rises from the back-edge vertices instead of folding inward. Result: all gates
  PASS, 668 tris. Visual: unchanged, head still an aardvark cone.
- **r03** Critique: hero/az090 — the head is an aardvark cone (thin snout, uniform taper). Diagnosis: H1-H4 too
  thin (snout depth 0.17 at H2). Fix: fatter H1-H4 and nose moved back to -0.75. Result: barely visible — the
  sections are still trapezoids narrower on top, which is what reads as a cone. 668 tris.
- **r04** Fix: head sections made boxy (flat snout top, v1 nearly as wide as v3), nose to -0.735 (nose-to-rump
  1.30). Result: head reads heavier in az000/hero, still weakly defined; not the worst problem any more. 668 tris.
  Worst now: hero/az045 — the legs are PLANKS: each leg's outer wall is one flat vertical quad from the widest flank
  point (z 0.6) straight down to the elbow; no shoulder or ham mass.
- **r05** Fix: a tilted shoulder level (outer z .44 / inner .31, outer x .222) and a ham level (outer x .206) as the
  first leg loop. Result: the shoulder and ham now break the flank with a crease, subtle but right; 716 tris.
  Worst now (az090): a domestic-pig sausage — level back, rump as deep as the chest; a boar is a wedge.
- **r06** Fix: front-heavy wedge — hump 0.86 -> 0.90, loin/hip/rump tops 0.73/0.66/0.60, hind sections narrower
  (B4 half-width 0.15), tail root lowered with the rump. Result: az135/az090 now a boar wedge, clearly better; 716 tris.
  Worst now (hero/az045): the head is a tapir cone — all the taper is on the top line, the jaw line is flat, so the
  snout reads long and thin.
- **r07** Fix: head wedge — jaw line now slopes up to a lower disc (disc centre 0.43, jowl 0.32), snout shortened
  (disc at -0.72), H3 wider for the tusk bulge. Result: az090 reads boar (heavy jowl, straight forehead line); 716 tris.
  Worst now (hero): the near ear sprouts from the side of the nape like a fin — its root face runs from the skull
  edge down to the cheek (v1-v2 of H5-H6), and it is a knife edge from the side.
- **r08** Fix: ear root moved up onto a wider skull plane (H5/H6 back-edge vertex out to x .112/.118, v2 raised),
  ear leaf turned ~25 deg so its cup faces forward-out. Result: ears sit on top of the skull and show area from the
  side and top; 716 tris. Worst now (az090/hero): forelegs are straight posts — the elbow is not tucked, forearm does
  not taper to a wrist, the pastern does not slant.
- **r09** Fix: foreleg profile — elbow tucked back (cy -0.092, wide 0.066/0.090), forearm tapering to a narrow wrist
  (0.038), pastern slanting forward to the hoof; hind hock narrowed and set back. Result: az090 legs now have joints
  (elbow knob, wrist pinch, Z-shaped hind leg); 716 tris. Remaining (for stage 2): flank spans read as even vertical
  strips (B1-B3), no face features yet (brow, eye socket, mouth line, nostrils) — those are secondary, not blockout.
- **r10 (lock)** No geometry change. Reads boar from every view: high hump sloping to a light rump, big low wedge
  head with a flat disc, pointed ears, short jointed legs with cloven hooves, drooping thin tail. Locked.

## Stage 2
- **r01** Critique: hero — no face: the skull is blank from ear to disc. Fix: eye socket = inset in the H4-H5 upper
  side face (almond, sunk 12 mm, nudged down/forward) + the brow vertex H4.v1 pushed out 20 mm to overhang it.
  Result: a readable socket under a brow in hero/az045; IoU min 0.998; 732 tris.
- **r02** Critique: hero — the snout is a blank tube end: no nostrils, no mouth. Fix: nostril = inset in the half
  disc cap (one oval per side, sunk 12 mm); mouth line = partial loop (t .45) through the v3-v4 strip from the disc
  rim to the cheek quad under the eye, fan terminators at both ends, creased 10 mm in and lifted toward the corner.
  Result: az045/hero read a lipped jaw and a pig disc; 772 tris, IoU min 0.998.
- **r03** Critique: az045/hero — the snout top/side and barrel are gently curving strips (loft look). Fix: flatten
  the snout-top edge line, the snout side (disc rim to tusk bulge) and the barrel's lower-flank quads (B2-B3) into
  single planes. Result: subtle — the snout side now reads as one facet in az045; IoU 0.998; 772 tris.
- **r04** Critique: hero — the ears are flat cards (a person cups a pig ear). Fix: inset in the ear's forward face,
  pushed 10 mm back. Result: near ear reads cupped in hero; 788 tris; IoU 0.998.
- **r05 (final s2)** Critique: az045 — the forequarter is soft: no tusk boss, no jowl weight, no hip point. Fix:
  vertex moves only — tusk boss +12 mm, jowl out/down 12 mm, hip bone point up/out, shoulder-blade top. Result: jaw
  and cheek read heavier in az045/az000; IoU min 0.99; 788 tris. Stage 2 done: 4 logged topo ops (eye socket,
  nostril, mouth partial loop, ear cup), lock assertion PASS.

## Stage 3
- **r01** Paint (5 body regions on stage-1/2 loops) + eye, tusk, crest, tuft pieces. Result: reads "wild boar" at a
  glance in colour. 932 tris, 8 colours. Critique: hero/az090 colour — the tusks, the boar's signature, are 1 cm
  slivers you have to hunt for. Diagnosis: sweep radii 0.013->0 over 0.11 m, exiting inside the lip.
- **r02** Fix: tusks 1.5x thicker (base r .019), 0.16 m arc, exiting outside the lip, curling up then back.
  Result: hero shows a clear ivory tusk; 944 tris. Worst now: az000/hero — the crest is 8 near-identical upright
  spikes (a gear / stegosaur), and the poll spike reads as a unicorn horn from the front.
- **r03** Fix: crest redesigned as 7 clumps that lie back (tip 60-105 mm behind the base), low at the poll, tallest
  over the withers, alternating a few mm of side lean. Result: az090 reads a swept mane, no unicorn spike from the
  front; 938 tris. Worst now: hero/az090 colour — one flat brown mass; the dark back strip is only a 1-face sliver,
  so there is no value plan for the front-heavy mass.
- **r04 (final s3)** Fix: a dark "cape" over neck and hump (faces facing up between the nape and mid-back, bordered
  by the widest-flank loop). Result: az090 colour — the front-heavy mass now has a value plan (dark mane cape, mid
  hide, dark legs, pink disc, ivory tusks); 938 tris, 8 colours.

## Stage 4
- **r01** Rig (13 bones + .R mirrors from J), auto weights, crest bound with body weights, eyes/tusks to head, tuft to
  tail2; idle 48f, move 25f, attack 32f. Gates PASS, glbcheck OK. Posed renders: neck bends without collapse
  (attack f8 head-down), sign check: +X swings a leg back / the head down. Critique: move f7 az090 — the recovering
  foreleg swings forward stiff-kneed with the hoof pointing forward (forearm was rotated, not the carpus).
- **r02** Fix: trot fold moved to the carpus (forefoot +57 deg, forearm -12) and stifle/hock (shin +18, hindfoot
  +38). Result: move f7 az090 — the recovering hind hoof tucks back and up, no stiff-knee reach; gates PASS.
- **r03** Critique (orchestrator + own): beauty renders — the prescribed browns are near-black, so the flat facets
  do not read. Fix (stage-3 paint, re-run through stage 4): hide #5a4636 -> #6e5543, back/legs #3e3029 -> #4f3d33;
  bristles #2e2622 and hooves #2a2420 stay the darkest accents.
  Result: s4_r03 — facets and the cape/hide/leg value steps now read in hero and back34; gates PASS, glbcheck OK.
  Harness orbit ran at stage 4 (advise: az000 head_merged, head 55% of the front view — expected for a boar).

## Triangles per stage
stage 1: 716 (locked, edge sha256 5585951446b8ea42...) · stage 2: 788 · stage 3: 938 total (body 788 + pieces) ·
stage 4: 938. Rounds: s1 10 (r10 = lock), s2 5, s3 4 (+1 repaint re-run), s4 3.

## Repair pass (AD notes round 1, `review/ad_notes.md`)
- **r60 (s3, note 1 tusks)** The old sweep started at the lip and exited through the cheek (hit 2). Fix: TUSK path
  table rooted INSIDE the lower jaw (centre x .064, 2.4 cm under the surface, base r .019 = 3.8 cm), out under the
  upper-lip overhang (1.7 cm clear), up and slightly back; BVH debug clearance printed per ring (tip 5 cm off the
  muzzle). Result: hit 0, float 0; tusks now splay outside the head width in az000. 938 tris.
- **r61 (s3, notes 5/6/8 paint + tusk size)** Disc #b78f86 -> dusky mauve #6a5a5d, nostrils near-black (eye key);
  hide #6e5543 -> #7d614d (+13%), dark saddle unchanged; cape now stops at the hump loop (B1) and continues only as
  the spine-to-back-edge strip: a stepped V along loops instead of a rectangle. Tusk radii +10%, tip up to z .532.
  Result: gates PASS; the disc no longer reads domestic pig; saddle tapers. 938 tris.
- **r62 (s3, note 3 crest)** Rebuilt the crest as ONE closed strip: per column a top vertex, a shoulder row and a
  base row each side (sunk 2.2 cm under the ridge), bottom closed; tips at 30 deg lean. Result: fused and wide from
  the front, hit/float 0, but az090 still read as an even saw. 1062 tris.
- **r63 (s3, note 3)** Tips swept further back (52 deg off vertical), valleys at 52%, base 6.8 cm wide at the peaks.
  Result: still 8 evenly spaced teeth (a saw). 1062 tris, slivers 1.7%.
- **r64 (s3, note 3)** 6 clumps with uneven spacing and heights (tallest 10.6 cm over the hump), the back of each
  clump slanting 3.4 cm down into the next (valley 60%), tips leaning +-7 mm L/R alternately. Result: az090 reads
  as a swept, layered mane rather than a saw; hit 0. 1022 tris.
- **r65 (s2, note 2 ears)** Vertex moves on the ear: root quad scaled 1.3 (wider, thicker), tip quad x2 (blunt),
  everything above the root 40% shorter along the ear axis, then rotated 24 deg out/down about the ear's thickness
  axis. Result: az000 ears inside the head width, no ear slivers; IoU min 0.956; gates PASS. 1022 tris.
- **r66 (s2+s3, note 4 face)** Brow vertices H4.v1 / H5.v1 pulled a further 1 cm out (+6 mm up); the mouth partial
  loop creased 18 mm in (was 10) and lifted 14 mm to the corner; stage 3 paints the lower jaw below the mouth line
  (stage 2 records its points) in the dark key so the mouth reads as a value border; eye piece 1.2x. Result: az090
  reads a lipped jaw and a brow over the eye; tusk still hit 0. 1022 tris.
- **r67 (s2, note 7 underline/legs)** Keel seam dropped 2.0/2.6 cm at B0/B1 (brisket), raised at B3/B4 with the
  belly sides (groin +3.4 cm) so the underline rises to the flank; foreleg elbow level x1.15, forearm x1.08, pastern
  x0.90 in plan. Only seam keel verts move at the brisket: the belly-side verts root the foreleg. Result: az090
  underline rises brisket-to-groin, the forearm is heavier over a narrow pastern; IoU min 0.939; gates PASS.
- **r68 (s4 re-run)** No change; the rig, weights and clips re-run over the repaired base and pieces (default rolls
  kept, clip signs unchanged). Result: all gates PASS incl. qa hit 0 / float 0 / z-fight 0 / slivers 1.6% / posed
  fold-over 0%; glbcheck OK; attack f8 head-down and move f7 fold read clean; tusks and crest follow the head/body.
- **r69 (s4 final, with orbit)** No change. All gates PASS (s1 lock match, s2 IoU min 0.939, qa hit/float/z-fight 0,
  slivers 1.6%, posed fold-over 0%); glbcheck OK; orbit advise az000 head_merged (expected for a boar front view).
  `--review` and `--compare` rebuilt. Remaining: the cape still steps as a dark quad over the shoulder (face-granular
  loops, no diagonal loop to put a true V border on); the tallest crest clump reads as a single spike from az000;
  the hindquarters are plain planes.

Repair-pass triangles: stage 1 716 (lock unchanged) · stage 2 788 · stage 3/4 1022 (body 788 + pieces 234).
Rounds 60-69 (10).

## Repair pass 2 (AD notes round 2, `review/ad_notes_r2.md`, K=2)
- **r90 (s4 baseline)** No change; first run on the drift + area-weighted fold-over gates. All gates PASS: hit/float/
  z-fight 0, slivers 16 (1.6%: crest 8, body 8 = ear front wall, foreleg roots, hind-leg root), flips 0% tris / 0%
  area, drift 0; lock PASS; IoU min 0.939. 1022 tris. Added a BOAR_DEBUG sliver locator (runs the kit's own
  triangulate_convex on a copy) to find each needle triangle.
- **r91 (s3, must-fix 1 crest)** Critique: az000 a single fin, every clump a needle (8 crest slivers). Diagnosis: the
  tent section had one top vertex per column. Fix: hexagon section with a 2 cm flat top, a front and back tip column
  per clump (a flat end in profile too), shoulder at 50% height at 78% of the base width, tallest clump 0.106 ->
  0.090, heights re-varied, clumps rolled +-12 deg. Result: blunt tips, still one column from az000; 8 slivers (end
  caps, a valley column meeting the next clump's forward shoulder). 1120 tris.
- **r92 (s3, must-fix 1)** Fix: lean 52 -> 45 deg, valleys midway between clumps, the forward shoulder shift clamped to
  clear the previous column, bigger end columns, rolls +-16 deg with +-1 cm alternate side offset. Result: az000 two
  blunt clumps side by side, crest width ~50% of its visible height; az090 a stepped tuft line, not a saw; crest
  slivers 8 -> 1; hit/float 0. 1120 tris.
- **r93 (s3, must-fix 2 saddle)** Critique: az090/hero the saddle is a hard quadrilateral (vertical border at the B1
  ring, horizontal bottom on the widest-flank loop). Fix: saddle rule rewritten as a stepped V: neck column down
  to the lower-flank loop, hump down to the widest-flank loop, the front walls of the leg root and the upper arm
  down to the elbow. Result (EEVEE review render): the V reaches the elbow from the front, but the B0-B1 upper
  flank is one face, so the rear border is still a straight vertical at B1. 1120 tris.
- **r94 (s2+s3, must-fix 2)** Diagnosis: no loop runs diagonally across the upper flank. Fix: a logged partial loop
  along the upper flank, H6 ring edge to B2 ring edge (cuts B0, B1; fans in the nape and barrel quads), its B0 vertex
  slid to 80% down toward the widest-flank loop and its B1 vertex to 30%; stage 3 paints the saddle above that line.
  Result: az090 the saddle's rear/bottom border is one diagonal rising from the chest front to behind the hump, no
  horizontal edge; IoU min 0.939 (unchanged); slivers 9 (0.8%).
- **r95 (s2, must-fix 3 ears)** Critique: 3_tech az000 yellow on the ear's inner edge; az090 a tall upright cone.
  Diagnosis: the ear's front wall quad (H5.v1, H5.v2, root front corners) has H5.v1 on the line H5.v2 -> root
  front-inner corner (the round-1 brow push put it there): a needle. Fix: H5.v1 brow push 1.6 -> 0.6 cm, root
  front-inner corner +1.5 cm x; tip segment 15% shorter; forward 20 / out 6 deg turns about the root centre.
  Result: the old needle is gone but 4 new ones: the turns swing the mid ring's outer side down into the root.
- **r96 (s2, must-fix 3)** Fix: graded turns (0 at the root, full at the tip), then hinges: the splay on the root's
  outer edge, the fold on its front edge. Result: the leaning side no longer dips, but the 49% shortening squeezes
  the cup-inset border (2 needles).
- **r97 (s2, must-fix 3)** Fix: the lower segment keeps the round-1 length (40%), the tip segment takes the further
  15% (49%), the tip folds a further 24 deg on the mid ring's front edge (second hinge), lower fold 10 deg. Result:
  ear slivers 0 (total 7 = 0.6%), but az090 still near upright.
- **r98 (s2, must-fix 3)** Fix: lower fold 10 -> 22 deg on the front-edge hinge, tip fold 20 deg. Result: az090 the
  ear leans forward over the brow with a blunt flat tip, az000 splayed; no ear slivers; IoU min 0.936. The tip is
  still level with (not below) the front crest clump.
- **r99 (s3, must-fix 4 tusk)** Critique: az090 the tusk tip stays inside the head outline (no hook). Diagnosis: the
  sweep rose straight up at y -0.52, where the snout top is 0.625 high. Fix: the TUSK path runs out and forward
  past the lip, up to z 0.56 at y -0.59 and hooks back to a tip at (0.177, -0.568, 0.602), radii graded to the
  point, root unchanged inside the jaw. Result: az090 the tip breaks the snout top line by ~3 cm; hero both tips
  clear; hit 0, float 0 (tip 10 cm off the muzzle).
- **r100 (s3, should-fix O6 stockings)** Critique: front-limb close-up the stockings go near-black, the facets vanish.
  Fix: a 'stocking' colour #5d493c (+15% over the saddle #4f3d33) below the elbow/stifle loop; the hooves take the
  'bristle' key (#2e2622, was a separate #2a2420 key) so the palette stays at 8. Result: leg facets read, the hooves
  stay the darkest value; 8 colours.
- **r101 (s2, should-fix O3 nostrils)** Critique: az000 two tall slots (a power socket). Fix: nostril inset scaled
  0.85 x 0.62 and tilted 20 deg top-out. Result: pig teardrops, but 4 needles in the disc border.
- **r102 (s2, O3)** Fix: 0.85 x 0.70, 14 deg. Result: 2 needles left (the disc's top-outer corner in line with two
  nostril verts).
- **r103 (s2, O3)** Fix: nostrils 8 mm toward the septum. Result: az000 tilted ovals on the disc; slivers 7 (0.6%:
  6 body triangles at the fore/hind-leg roots + 1 crest); IoU min 0.936; z-fight 0.
- **r104 (s4 final, with orbit)** No change. All gates PASS: lock match, IoU min 0.936, hit/float/z-fight 0, slivers
  7 (0.6%), fold-overs 0% tris / 0% area, drift 0; glbcheck OK; orbit advise az000 head_merged (expected, a boar
  head-on). `--review` and `--compare` rebuilt. Remaining: the saddle's front border behind the jowl is still the
  vertical H6 ring line (only its rear/bottom border is diagonal); the ear tip is level with, not below, the front
  crest clump; the tusk is long and thin; F5 (mouth line, brow) was not reworked beyond round 1.

Repair-pass-2 triangles: stage 1 716 (lock unchanged) · stage 2 796 (+ saddle partial loop) · stage 3/4 1140.
Rounds 90-104 (15).
