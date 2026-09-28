# Frog (opus) — round notes

Stage 0: blueprint.json (blueprint.png): sitting frog 0.50 m long, 0.34 m tall to the eye domes, body
tilted up at the front, wide flat head, eye domes on top, folded Z hind legs, short planted arms.
Build plan: one stack of 12 eight-point half rings along the body (snout -> rump; cols: top seam,
back, dorsolateral ridge, upper side, MOUTH LINE / mid flank, jaw / lower flank, belly side, belly
seam). Sockets left open in the stack: eye domes (2x2 on the skull, swept up 8-sided), front legs
(N->B0 cols 4-6, swept down, 6 -> 10 zipped into a flat hand, 4 toes), hind legs (B2->B3 cols 4-6,
swept through a thigh-forward / shin-back / foot-forward Z with parallel-transported frames; 6 -> 12
zipped into a webbed paddle, 5 toes). Snout cap split at the mouth line by a seam vertex.

## Stage 1
- r01 — 1206 tris; FAIL self-intersection (16 pairs). Reads as a frog already (az045, hero).
  Critique: the gate — the thigh root cuts into the flank (faces at x .12-.15, y .075-.09) and the
  heel fold folds into itself (x .23-.24, y .07-.12). Diagnosis: thigh sections T0/T1 at x .135/.178
  with r .044/.050 overlap the B1-B2 flank (half-width .126); ankle (0.222, .11) and first foot section
  (0.255, .118) are 4 cm apart with radii summing to 4.8 cm. Fix: thigh root/mid out to x .142/.186 and
  slimmer; heel and foot out to x .246/.276/.288 (ball .298).
- r02 — 1206 tris, all gates PASS; blueprint IoU side .84 / front .72 / top .74. Result: intersections
  gone. Critique: the signature eyes are square boxes (top view, az000: flat-topped blocks with
  corners), not bulging domes. Diagnosis: tube() normalises the socket loop per axis, so the 8-loop
  template is a square and every dome section keeps its corners. Fix: sweep the dome on the loop's
  angles projected to a circle (an octagon template).
- r03 — 1206 tris, PASS; IoU .835/.716/.739. Result: better — round octagonal eye domes (top, az000).
  Critique: the hind legs, the frog's second signature, are thin slabs pressed flat to the flank
  (top view: narrow pontoons; az180: no haunch mass); blueprint top overlay wants a wide rear.
  Diagnosis: thigh sections at x .142-.19 squashed to 0.72-0.85 in X to clear the body. Fix: move the
  whole Z-fold out (thigh x .15/.20/.215, knee .225, shin .23-.24, heel .268, ball .315) and let
  the thigh be fat (r .046/.052, squash only .85-.95).
- r04 — 1206 tris, PASS (after one retry: the wider fold first clipped shin/thigh and shin/foot —
  thigh raised to z .13, shin to .047, foot out to x .30/.314). Result: better — fat haunches in
  hero/az045. Critique: in profile (az090) the body is a level loaf — a flat back at z .25 from head
  to hip and a vertical rump wall at z .05-.15 — not a SITTING frog tilted up at the front.
  Diagnosis: ring tops B0-B5 all .24-.256 and the rear rings stand off the ground (zb .03-.05).
  Fix: slope the back down from the head (B0 .25 -> B1 .238 -> B2 .218 -> B3 .188 -> B4 .15 -> B5 .108)
  and sit the rump on the ground (zb .036/.024/.020/.030).
- r05 — 1206 tris, PASS; IoU side .78 (the blueprint was drawn level; the tilt is the design).
  Result: better — a sitting profile, back sloping down to a rump on the ground (az090). Critique:
  the thigh is a flat vertical plank beside the body (hero: one big flat outer face, a board), not a
  round haunch. Diagnosis: the leg sweeps the socket loop normalised per axis — a tall 2x1 socket
  becomes a box-hexagon whose flat side faces out. Fix: sweep the leg on the loop's angles on a
  circle (roundt), so every leg section is a true hexagon.
- r06 — 1206 tris, PASS. Result: better — the thigh is a round haunch (hero, az045). Critique: the
  signature eyes are straight-sided cylinders standing on the skull (az000: two bear ears, inside the
  head outline), not bulging balls. Diagnosis: dome sections r .050/.046/.028 on a vertical axis —
  the widest ring is the lowest, the sides are vertical. Fix: a ball — r .052 low, the equator .056 at
  +5 cm pushed out 1.6 cm past the head's side, .036 near the top, apex at +8.7 cm.
- r07 — 1206 tris, PASS. Result: better — the eyes are bulging balls standing out past the head's
  side (az000, top). Critique: from the top the body is a coffin — straight parallel sides from the
  head (.15) to the hips (.114), so head and body read as one long slab, not a head on a pear body.
  Diagnosis: ring half-widths E2 .15 / N .14 / B0 .134 / B1 .126 / B2 .114 fall off evenly.
  Fix: a waist behind the head (N .13), the belly swelling (B0 .138, B1 .136, B2 .122) and the
  rear rings 0.7-1.7 cm shorter (B3 .138, B4 .172, B5 .196).
- r08 — 1206 tris, PASS. Result: better — top view now head / waist / swelling belly / tapering rump.
  Critique: the front legs are spindly struts (az000: thin sticks splaying from under the chin, an
  insect's legs) — STYLE asks for chunky limbs and a stylised frog's arms are stubby and thick.
  Diagnosis: arm sections r .034/.025/.023/.019 on a 16 cm arm; palm .032, knuckles .042 half-width.
  Fix: r .040/.030/.029/.022 (a forearm that stays thick), palm .036, knuckles .048, toes 10% thicker.
- r09 — 1206 tris, PASS. Result: better — stubby thick forelegs and bigger hands (az000, az045).
  Critique: the rump ends in a flat oval end cap facing straight back (az135, az180: the cut end
  of a tube). Diagnosis: ring B5 closed by three vertical strip quads in one plane at y .196.
  Fix: close B5 with a fan to a vent point 1.8 cm behind it (y .214, z .062): a blunt rounded rump.
- r10 — 1208 tris, PASS; IoU .776/.674/.706 (the blueprint is level-backed; the model is tilted by
  design). Result: better — a blunt rounded rump (az135, top). Decision: the base reads as a frog
  from every view — wide flat head, bulging eye balls on the skull, sitting tilt, stubby planted
  forelegs, fat folded haunches with the Z of thigh/shin/foot, long feet, 4 + 5 toes. Planes (flat
  crown, dorsolateral ridge), the mouth line and eye sockets are stage-2 work. Lock at r11.
- r11 — LOCK. 606 verts, 636 faces, 1208 tris, edge sha256 629f07b3a3b2b18b (stage1_lock.json).
  Orbit (harness/outline.py) holds on every azimuth.

## Stage 2
- r01 — 1216 tris, PASS, min IoU .996. Fix (from the lock critique: no mouth): topo #1 partial loop
  in the jaw band (cols 4-5) from the snout cap (fan terminator at the seam vertex) to the corner
  ring E2 (fan terminator), 22% under the lip line; lower lip tucked in 10%, upper lip out 6 mm.
  Result: better — a wide smile crease wraps from the snout round the side of the head (close-up
  az090, az000). Critique: the eye domes are blank balls (az045, az090) — no socket for the eye, so
  the stage-3 eye would sit on a bald surface. Diagnosis: no topology on the dome's outer-front
  side. Fix: inset the two outer-front faces of the dome's equator bands, pushed in 4 mm.
- r02 — 1256 tris, PASS, min IoU .996. Result: better — a socket window on the outer-front of each
  dome (hero close-up), to be filled by the stage-3 eye. Critique: the back is a smooth lofted
  gradient (az090, az135: even strips shading evenly from the spine to the flank) — no plane change,
  the tube look. Diagnosis: cols 0-2 of N..B3 lie on one even arc. Fix: vertex moves — the frog's
  dorsolateral ridge: col 2 out 4 mm and up 3-7 mm from E2 to B3, cols 0-1 pressed 2-4 mm down, so
  a flat back plane breaks over a crease into the flank plane.
- r03 — 1256 tris, PASS, min IoU .996. Result: marginal — a readable crease runs along the back
  (close-up az135) but the flank still shades softly. Critique (rig readiness, the hop): the thigh
  meets the body in ONE band (socket ring -> thigh-root section, wire hero), so extending the leg
  will fold the haunch. Diagnosis: build_leg's first section is the only ring near the hip.
  Fix: topo loop through the socket -> root band (t .5), swelled 10% so the haunch grows out.
- r04 — 1280 tris, PASS, min IoU .996 (two retries in-round: the edge pick first ran the loop along
  the body — picked by max x, it grabbed B1-B2 — then a 10%/3% swell of the new ring pushed its front
  into the flank; now the edge is the one leaving the stack, and the ring is eased 4 mm out instead).
  Result: the thigh root now has socket / hip loop / root section (wire). Critique: see r05.
- r05 — Critique (r04 renders): the skull between the eyes is a soft dome (hero close-up: 6 facets
  shading into each other from the snout to the neck) — a frog's crown is a flat plate. Diagnosis:
  cols 0-1 of S1..E2 follow the section arc. Fix: flatten those 8 vertices into one plane.
  (first try: kit flatten() fits any plane, so it pulled the seam vertices off x = 0 — 10 open edges;
  replaced by a seam-safe flatten that fits the plane in y-z, containing the X axis.)
  Result: better — the skull top is one flat plate between the eyes (hero close-up). 1280 tris,
  PASS, min IoU .992, orbit holds. Stage 2 done: 3 topo ops (mouth partial loop, eye-socket inset,
  hip loop); vertex moves for the lips, ridge and crown.

## Stage 3
- r01 — 2024 tris (body 1280 + pieces 744), 8 colours, gates PASS. Paint on placed loops: mouth band
  (lip line -> stage-2 loop), belly/throat/jaw (cols 5-7 + the lower-lip loop), soles by normal, bars
  across the folded leg; pieces: gold lens eyes + horizontal pupils + glints, tympanum discs, 7
  ray-cast spots, toe pads on all 9 toes, scalloped webbing between the hind toes, a tongue hidden in
  the mouth for the attack. Reads as a frog at once (beauty close-up). Orchestrator review agrees.
  Critique: the signature eyes are small lenses looking sideways (az000: little gold chips at the
  sides, blank from the front). Diagnosis: lens r .030 centred on the stage-2 sockets, facing
  (0.80, -0.58, 0.12). Fix: a big lens (r .041 x .038, pupil .025 x .011) ray-cast onto the dome
  along (0.52, -0.80, 0.30): forward, out and up, filling the front-top of the mound.
- r02 — 2024 tris, PASS. Result: better — two big gold eyes with wide horizontal pupils read from
  the front and 3/4 (beauty close-up az000/hero). Critique (with the orchestrator's): the back green
  #5f9a3a sits too dark under the key light (colour sheet: facets go olive), and the glint sits on
  the lens rim. Diagnosis: palette value; glint offset .012/.016 off-centre. Fix: back #6aa840
  (spots #3f6e2a keep the value step); glint .007/.013. The throat/belly is already #e3d9a0 on the
  cols 5-7 loops (light in the beauty front view; the workbench sheet darkens down-facing faces).
- r03 — 2024 tris (body 1280 + pieces 744), 8 colours, PASS, orbit holds. Result: better — a
  brighter mid green with the dark spots still a clear step (hero colour); glint on the lens.

## Stage 4
- r01 — gates PASS (clips, weights, lock, glbcheck OK). Posed wire: no collapse at the neck, hip
  or knees; the tongue shoots out of the mouth (attack f016). Probed bone axes (AXES print):
  hips/spine/head/jaw have local Z pointing DOWN, thigh/shin Z up, upper arm Z back.
  Critique: every body pitch is inverted — the hop dives nose-first with the legs folding under
  (move f012), the lunge nods down and the jaw closes INTO the head. Diagnosis: signs written for a
  Z-up spine; hips loc Z is down too. Fix: flip hips/spine/head/jaw X and the hips loc; hind leg
  kick to thigh -125 / shin -150 / foot -140 (the foot trails back) at the top of the hop.
- r02 — PASS (glbcheck OK). Result: better — the jaw drops on the lip line with the tongue flicking
  out (attack f016 az090), the hop now rises nose-up. Critique: at the top of the hop the hind legs
  hang straight DOWN under a near-vertical body (move f012 az090) instead of trailing back; the lunge
  lifts the hind feet off the ground (attack f016). Diagnosis: the thigh's X axis is skewed (the
  thigh points out-forward) and the knee/heel folds are nearly horizontal, so pure X swings aim the
  leg down; the attack rotated hips and thighs. Fix: solve the kick from the probed axes — thigh
  (-150, 0, -54), shin Z -140, foot Z +140, body pitch halved; attack keeps hips/legs still and lunges
  with a hips slide + spine/head pitch.
- r03 — PASS (orbit holds, glbcheck OK). Result: better — the top of the hop is a real leap: body
  nose-up, hind legs trailing straight back (move f012 az090/hero); skin holds at hip, knee, neck.
  Critique: the attack frame f016 shows the hind legs still kicked back — the attack clip never keys
  the legs, so it inherits the last pose (the posed render sets clips in sequence; an engine that
  blends clips would do the same). Diagnosis: clip() keys only the bones named in a clip. Fix (final
  round): key every bone in every clip at its first frame (rest where unused).
- r04 — all gates PASS (clips, every vertex weighted, final lock assertion; orbit holds; glbcheck
  OK). Result: better — the attack keeps the hind feet planted while the head lifts, the jaw drops on
  the lip line into a dark mouth and the tongue shoots out (attack f016 az090/hero); idle shows the
  throat pulse and blink; the hop crouches, leaps nose-up with the legs trailing, lands. Stage-4
  round budget spent.

## Totals
- Triangles: stage 1 1208 (locked), stage 2 1280, stage 3/4 2024 (body 1280 + pieces 744).
- Rounds: stage 1 11 (lock at r11), stage 2 5, stage 3 3, stage 4 4. Lock edge sha256 629f07b3a3b2b18b...
- side_by_side.jpg written (no engine frog: two columns).
- Remaining weaknesses: the eye pieces are placed by ray-cast, not seated in the stage-2 socket
  (the socket windows sit partly under the lens rim); the hind foot is a long flat board and the
  toes are square sticks under the pads; the open mouth is a stretched band, no cavity or lower lip
  shape, and the hop's extended leg shows the long thin shin/foot as a straight rod.

## Repair pass (from review/ad_notes.md, rounds 60+)
- r60 — note 1 (webbing) + note 6 (tongue). Change: web plates -> closed scalloped wedges z .006-.012
  (6 mm, ~40% of the toe's depth) sunk into both toes and the sole; tongue -> a rounded bar (thick
  ~0.45x width) from y -.06 to a tip 2 mm behind the snout's inner surface (ray-cast), attack slide
  .17 -> .15 so ~25% stays in the mouth. Result: open edges 164 -> 84 (spots only), float 1 -> 0;
  tongue reads as a bar in attack f016. New: tongue slivers (16; 7 cm rows). 2136 tris.
- r61 — note 2 (spots) + note 4 (tympanum), + the tongue sliver fix. Change: spots piece and the
  leg bars removed; stage 2 logs topo #4 (inset in 5 back faces per side, inner quads scaled
  unevenly per corner, none on the thighs) and topo #5 (ear-drum inset behind the eye dome, sunk
  2 mm); paint 'spot' / new 'drum' mid-green #579336 on the inner faces (pads merged into the
  cream to stay at 8 colours); tongue 5 rows x 6-gon. First try turned the insets (and put one on
  the upper flank): 4 self-hits + slivers, so no turn and 5 spots. Result: open 0, z-fight 0,
  slivers 18 (0.9%), no cyan. Flip rose 32 -> 44 (spot inner verts kept heat weights). 2092 tris.
- r62 — note 3 (hip fold-over). Change: blend_hips() after skin: thigh share root 100% / hip loop
  80% / socket ring 50% / faces round the socket 20% / rest of body 0 (hips); kick eased to thigh
  (-105, 0, -40). Result: flip 44 -> 32 but moved to the spot faces, and the legs hung straight
  down (move f012 az090) — worse pose.
- r63 — note 3 cont. Change: spot/drum inset verts join the body (thigh 0); kick restored to
  (-150, 0, -54). Result: flip 32 -> 10 (0.48%, PASS), legs trail back again (move f012).
- r64 — note 3 cont.: cap the knee opening. Change: shin Z -140 -> -105, foot +140 -> +115.
  Result: flip 8 (0.38%) PASS; the hop's legs trail back with a slight knee bend, thigh keeps its
  section at the hip (move f012 hero wire, az090).
- r65 — note 5 (eyes). Change: stage 2 rounds the eye dome's flat lid (top ring x1.25 out, +4 mm;
  apex +1.7 cm; IoU min .969); stage 3 replaces the gold coin with a gold eyeball (r .038, 8 x 3
  ring low-poly ball, pole on the look axis (.55, -.70, .45)) seated ~42% into the front of the
  dome, a closed lozenge pupil that follows the ball's curve 2.5 mm proud, a small glint pyramid on
  the pupil. Result: bulging balls read from the front and 3/4; no coin edge. But the front cap
  (one 45-degree fan) still read as a flat octagon and the pupil was small. Gates PASS, 2116 tris.
- r66 — note 5 cont. + note 7 (belly). Change: ball rings at 25/60/95/135 deg (round front), pupil
  +/-36 x 14 deg; belly #e3d9a0 -> warmer cream #f0d8a2. Result: rounder eyeball, wide horizontal
  pupil (head close-up); gates PASS, flip .37%, 2148 tris.
- r67 — note 7 (head/back facets, head lid/snout). Change (stage 2 vertex moves, no topo):
  cheek = one flat plane (S1..E2 cols 3-4, before the lip moves so the upper lip still
  overhangs); snout top sloped down (S0 cols 0-2 -10/-10/-5 mm, S1 cols 0-1 -6 mm, then the crown
  plate flattens with the slope); back = a flat plate across the spine (cols 0-1) and a flat flank
  plate (cols 2-3) on the front half (N-B1) and rear half (B2-B4). Result: the back reads as
  two big plates with a bevel strip over the ridge (back34), crown slopes to the nose; IoU min
  .967, slivers 24 (1.1%), gates PASS. Critique: the spots are small, regular parallelograms
  (back34) — a grid of windows, still machine-like. Lid chamfer not done (a chamfer here is a
  full-length loop, +~100 tris).
- r68 — note 2 cont. Change: spot insets at 0.30 (larger) with one corner pulled in to 45-50%:
  irregular kites. Result: bigger, irregular spots (back34), no grid of windows; slivers 32 (1.5%),
  flip 10 (.47%), PASS.
- r69 — note 7 (thigh taper). Change: the two thigh rings between the drumstick and the knee pulled
  in to 84% / 86% (knee ~60% of the hip loop). Result: the thigh tapers to the knee (hind close-up);
  IoU min .961; flip rose to 12 (.56%, FAIL) — new fold at the knee's outer face.
- r70 — note 3 margin. Change: the kick eased to thigh (-138, 0, -50); the two rear spots moved off
  the socket's weight gradient (B2-B3 col 1, B3-B4 col 0 — the last pair meets over the spine).
  Result: flip 10 (.47%) PASS; legs still trail back at the top of the hop (move f012 az090).
- r71 — final stage 4 (with orbit): every gate PASS — hit 0, float 0, z-fight 0, slivers 34
  (1.6%), posed flip 10 (.47%), open edges 0; IoU min .961; orbit holds; glbcheck OK. Then
  --review and --compare rebuilt review/ and side_by_side.jpg.
- Repair totals: body 1380 tris after stage 2 (topo #4 spots and #5 drum added), 2148 with pieces.
  Notes: 1 web, 2 spots, 3 hip, 4 drum, 5 eyes, 6 tongue fixed; 7 partly (belly, back/cheek
  plates, snout slope, thigh taper done; lid chamfer and the mouth/foot slivers not done).

## Repair pass 2 (from review/ad_notes_r2.md, rounds 90+)
- r90 — baseline stage 4 on the current kit: every gate PASS except drift FAIL (1 shell: the tongue);
  flip 10 (.47% tris / .47% area), slivers 34 (1.6%). Must-fix 0 = the tongue drift.
- r91 — items 0 + 3 (tongue). Diagnosis: the whole tongue rode the tongue bone, so its seated verts
  slid 15 cm off the mouth floor. Fix: stretch_tongue(): bind(body=) weights on the root rows (y > -.125,
  created first), ramping to 100% tongue bone by y -.20; the tip is a pad, not a needle. Result: drift
  0, root stays in the mouth (attack f016). Still a thin stick.
- r92 — item 3 cont.: neck 1.6 cm wide, pad 2.6 cm (1.6x), thicker rows. Result: a bar ending in a
  wider rounded pad (attack f016 hero). 2196 tris.
- r93 — diagnostic only (FROG_DBG): flips all in the hop — rump behind the socket, knee outer face,
  socket top, one spine spot.
- r94 — item 1: hip loop share 80 -> 60% thigh, hop hip swing eased 12 deg (thigh -138 -> -126, Z -50 -> -46).
  Result: flip 9 (.41% / .20% area), but the thigh necked at the hip ring (move f012 wire).
- r95 — item 1 cont.: hip loop 70%. Result: flip 7 (.32% / .19%); neck gone.
- r96 — knee opening capped (shin -105 -> -95). Result: worse (9); reverted — the knee fold is not
  from the knee opening.
- r97 — B4 flank behind the socket 20 -> 30% thigh. Result: no change (the fold sits on the socket
  ring's own step); reverted. Added per-frame flip diagnostics.
- r98 — diagnostic: flips at f10 (knee, spine spot, hip) and f14 (socket top, rump).
- r99 — Diagnosis: blend_hips only folded the SAME-side thigh; near the spine the other thigh's heat
  weight dragged the skin. Fix: fold both thighs into the blend. Result: flip 6 (.27%), spine gone.
- r100 — the two hip flips sit on the socket-ring step (50% -> 20%). Fix: socket 40%, ring around it
  25%. Result: flip 2 (.09% tris / .01% area), only the outer knee face at f10; no purple on the hips.
- r101 — diagnostic: body slivers per side — spot rims 6, shin/heel/foot column 4, snout fan 2, eye rim 1;
  web 2.
- r102 — item 2: spot kites capped at 0.85 per corner (1.05-1.15 left 5 mm rims on 6 cm edges).
  Result: slivers 34 -> 24.
- r103 — item 2: the lower-leg rings carried the socket loop's uneven angles (one column 6-9 mm
  wide over 7-8 cm): angles evened per ring (squash-aware on the flat foot). Result: 24 -> 14; IoU .960.
- r104 — item 2: eye-socket inset 0.18 -> 0.30 (6 mm rim). Result: 14 -> 10 (.46%).
- r105 — item 2 (mouth groove): the snout cap fans from the seam vertex M to S0 cols 2-5, a ~7 deg
  span seen from M. Fix: col 2 +8 mm, col 3 +4.5 mm, col 5 -7 mm (kept in the belly paint), and the
  loop's snout vertex slid along S4-S5 to the angular midpoint. Result: slivers 6 (.3%): none on the
  body's mouth, 2 in the web; heatmap clean in every view.
- r106 — item 4 (eye nut face-on). Change: the ball's pole and the pupil turned 20 deg forward-down-in
  (the seat stays on the old axis), a 5-ring ball whose front is a dome (apex +30% of the radius,
  falling off to the plain ball at 60 deg), and a mid ring in the pupil so it follows the dome. No
  bevel-ring colour exists: the ring was the fan edge, now gone. Result: az000 domes with the pupils on
  the front; but az090 reads as an acorn pointing forward. 2252 tris.
- r107 — item 4 cont.: dome apex +22%. Result: az000 still domes with front pupils; az090 rounder.
- r108 — final stage 4 (with orbit): every gate PASS — hit 0, float 0, z-fight 0, slivers 6 (0.3%),
  flip 2 (.09% tris / .01% area), drift 0, lock PASS, IoU min .960, orbit holds, glbcheck OK. Then
  --review and --compare rebuilt review/ and side_by_side.jpg.
- Pass-2 totals: 2252 tris (body 1380 + pieces 872); rounds 90-108 (19, 5 of them diagnostic/reverted).
  Must-fix 0 drift, 1 hip, 2 slivers, 3 tongue, 4 eyes done (4 at a 22% dome, not 30%, to keep the
  profile ball). Should-fix: none attempted (the belly cream was already #f0d8a2 from pass 1).

## Repair pass 3 (from review/ad_notes_r3.md, rounds 130+)
- r130 — baseline stage 4 on the current kit: every gate PASS (hit/float/z 0, slivers 6 = 0.3%, flip 2 =
  .09% / .01% area, drift 0, lock PASS, IoU min .96). No must-fix 0.
- r131 — item 1 (hop leg). Critique: move f012, the extended leg reads as a thin rod on a hip neck, and az090
  shows the two legs at different angles. Diagnosis: (a) bone heat bled thigh/shin/foot into each other
  (the Z-folded segments lie side by side); (b) the .R keys were (x, -y, -z) of .L, but the default rolls
  are not mirrored, so the far leg bent differently; (c) the hip ring blended hips/thigh across 130 deg.
  Fix: the leg rings are recorded in stage 1 (LEG), followed through stage 2, and weighted ring by ring in
  stage 4 (LEGW; blends only at the knee and heel rings); a hipmid.L/R helper bone turns half the thigh's
  angle and carries the hip loop; .R keys are the true mirror through each bone's rest frame. A gauge
  (FROG_GAUGE) prints segment lengths, the hip-loop/thigh section and the L/R mirror gap per frame.
  Result: shank 23.7 -> 23.9 cm (rest length kept), mirror gap 0, hip loop r 3.8 vs drumstick 4.8 (79%);
  but flip 2 -> 10 (the hip loop, 1.3 cm from the socket ring, swings 30% more than it and folds).
- r132 — item 1 cont. Sweeps (thigh cut, hip shares, knee shares). Fix: thigh kick cut 20 deg
  (-126/-46 -> -106/-40) with the knee and heel opened less (shin -105 -> -80, foot 115 -> 80), so the leg
  keeps a Z instead of a straight rod; socket ring 40% of the thigh angle (hipmid .8), the ring round it
  15%, the hip loop 50%, the root 75%; knee rings thigh/shin .7/.3, .4/.6, .1/.9; stage 2 swells the
  shank rings 30% (ankle 15%; r .021 -> .027, still under the thigh at rest, 0 hits, IoU .954).
  Result: flip 4 (.18% / .05% area); move f012 wire: the thigh flows into the body with no neck, both
  legs the same, the shank reads as a limb (hero clay). Legs now hang more down than back (az090).
- r133 — item 2 (toe pads). Diagnosis: the bulb's back ring, 1.25x the toe's width 4 mm behind the tip,
  left through the toe side walls. Fix: back ring 6 mm inside the toe at 70% of its section, the bulb
  (0.8x) swelling only past the tip cap. Result: front close-up, no cream outside any toe; hit/float 0.
- r134 — item 3 (pupils). Fix: pupil and glint on their own axis, the ball's pole turned 22 deg down about
  the ball's horizontal axis (radius still follows the ball's dome). Result: az000 gold above and below
  each lozenge; hero pupil still on the ball's face. Gates PASS.
- r135 — item 4 (spots). Fix: stage-2 spot insets (topo #4) removed; stage 3 paints 8 whole back faces as
  4 spots per side (a bent hexagon behind the head, an L of 3 on the back, a pair over the arm, one at the
  rump tip joining its mirror): 7 blotches of mixed size, no rims. First layout (10 faces, 2 on the spine)
  read as bands from the top; replaced. Slivers 6, unchanged.
- r136-r138 — item 5 (triangles). Pads -> 6-sided bipyramids (396 -> 216), eyeball 5 -> 4 rings
  (160 -> 128), eye-socket inset (topo #2) removed (body 1296 -> 1264). A 6- and 7-row tongue both
  drifted (the root anchor lost its skin row); the 9-row tongue restored (drift 0). 2252 -> 1928 tris.
- r139 — should-fix: belly #f0d8a2 -> #fae8c0 (lighter warm cream; pads/glint share it); web a wedge,
  11 mm at the toe roots tapering to 5 mm at the notch. Gates PASS.
- r140 — final stage 4 with orbit: every gate PASS — hit 0, float 0, z-fight 0, slivers 6 (0.3%), flip 4
  (.21% tris / .05% area), drift 0, lock PASS, IoU min .954, orbit holds, glbcheck OK; --review and
  --compare rebuilt. Stage 1 NOT unlocked (turn budget): the head is still the locked ring stack.
- Pass-3 totals: 1928 tris (body 1264 + pieces 664); rounds 130-140. Items 1-4 done, 5 partly (1928,
  not <= 1800; no stage-1 head reduction). Known: the hop's legs hang more down than back (thigh cut 20 deg).
