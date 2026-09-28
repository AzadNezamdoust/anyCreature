# raven_wyvern (fable) — round notes

Rebuild from a new stage 1 (both art directors: the old build read as a parrot). Build: one trunk of
5-vert half-rings, each a slice perpendicular to a hand-drawn centreline (tail tip -> hips -> keeled
chest -> S-neck -> raven skull -> bill). Bird legs (drumstick, reversed hock, shank, foot, 3+1 toes)
from a 2-face patch on the lower flank; folded wing forelimbs from a 2-face patch on the upper flank:
deltoid stub -> upper arm back to the elbow -> forearm up/forward to a high wrist knob (branched off
the upper arm's top faces) -> one long finger back over the body (branched off the forearm's top
faces) whose sections are sails: bone ridge on top, a 3 cm membrane hanging below, scalloped.

## Stage 0
- blueprint.json: side outline with the S-neck, the wing tent (wrist peak, finger to past the tail
  root) and a tail longer than the body; front/top halves. blueprint.png reads as a wyvern.

## Stage 1
- r01 — Critique: 6 self-intersections at the shoulder; wings are thin sticks (a bird skeleton), az000
  and az090. Diagnosis: the first upper-arm section (y -0.12) sat inside the shoulder patch's y-span
  (-0.29..-0.06), so the side faces folded through each other. Fix: first section behind the patch;
  finger sections became sails (membrane in the base). Result r02: reads as a folded wing; still
  10 hits. 860 tris.
- r02 — Critique: hits remain at the root: the extrusion's side faces sweep from the patch's front
  edge back to the bar and cut the flank bulge. Fix: a deltoid stub first (patch pushed out along
  its normal), then the bar. Result r03: 12 hits, worse. 884 tris.
- r03 — Diagnosis: the tube bends from "out" to "back" about Z, so the patch's FRONT verts must land
  on the bar's OUTER side; my order sent them inward and the tube twisted through itself. Fix:
  section order [TO,T,TI,BI,B,BO]. Result r04: 0 hits, gates PASS. 884 tris.
- r04 — Critique: a heron-like bird: rod tail, flat back, smooth leaf wing. Fix: tail S-curve (sags
  then curls up), thicker root, tail 0.74 vs body 0.70. Result r05: reptile tail reads in az090.
- r05 — Critique: flat back into a smooth C-neck (bird). Fix: withers hump (c0-c2 taller), throat
  bulge at n1 receding at n2 (the S). Result r06: hump and S read slightly; still bird-first.
- r06 — Critique: the wing is one smooth leaf = the strongest bird cue (az090). Fix: six sail
  sections with two hanging finger tips (scalloped trailing edge), tips clear of the elbow and tail.
  Result r07: az090/az135 read as a folded bat wing; better. 932 tris.
- r07 — Critique: small smooth bird head. Fix: boxier skull (flat wide crown row, narrower jaw),
  larger skull rings, bill deeper at the root with the hook only at the tip. Result r08: a raven
  skull with a stop at the bill; better.
- r08 — Critique: top view a bowling pin with two rails and daylight to the flanks; az000 a narrow
  chest. Fix: chest/hips W +0.015-0.02, wing chain 2 cm in, membranes lean inward (20% of the drop).
  Result r09: 4 hits (upper arm's inner verts inside the deltoid stub). Top IoU 0.855.
- r09 — Fix: upper arm back to its r04 x (clean), forearm/finger/sails kept tucked. Result r10:
  gates PASS; reads bird-dragon/drake in az090 and az135; az000 still egg body + posts. 932 tris.
- r10 — Critique: az000 narrow skull, wrists as thin posts, narrow stance. Fix: skull W +0.015-0.02
  with a flatter crown, stance 2 cm wider, thicker wrist knob. Result r11: reads bird-dragon /
  drake in az090, az045, az135; az000 still the weakest (egg chest). 932 tris.
- r12 — Lock round (no geometry change, with the orbit). LOCKED: 468 verts, 932 tris, edge sha256
  978b96f824538c8e... Honest call: the grey base reads as a horned-less "bird-drake" (bat-scalloped
  folded wings, curled reptile tail, raven skull, S-neck); a stranger would say dragon-bird or
  pterodactyl rather than plain bird, but not yet "wyvern" without the pieces.

## Stage 2
- r01 — Fix (face first): `inset` eye socket in the upper-side face between skull ring k1 and face
  ring k2, inner ring 2.2 cm in; brow verts out/forward/down over it; gape pressed in along the
  bill to a mouth corner; one flattened cheek/jaw plane. Result: gates PASS except slivers 8.2%
  (the membranes' 1 cm lower-edge strips and the tiny finger/tail tip rings). 948 tris, IoU 0.984.
- r02 — Fix: keel the membrane edges (ridge 2.5 cm below the edge verts), finger tip ring x2.2,
  tail tip ring x1.7. Result: slivers 2.1%, but 4 hits (the wrist-end keel pushed into the forearm
  root). IoU 0.971.
- r03 — Fix: no keel at the wrist section, keel 3.5 cm elsewhere, taller ridge on the last two bone
  strips, finger tip ring x2.5 and 5 cm closer, bill tip ring x1.8, deltoid ring 2 cm out. Result:
  slivers 1.3% PASS, but the deltoid push recreated the r09 shoulder hits.
- r04 — Fix: deltoid push reverted. Result: all gates PASS, 948 tris, IoU min 0.970.
- r05 — Fix: `loopcut` a supporting loop each side of the hock ring (thigh side scaled 1.12 as the
  feather cuff, shank side 0.90); belly bottom verts up 2-3 cm (the tuck). Stage-2 final with the
  orbit: 996 tris, 3 logged ops, IoU min 0.969, slivers 0.8%, tech QA PASS.
- (s3 r03 amendment, vertex moves only) the two hanging membrane tips lean in 2-2.5 cm less so the
  spars clear the flank. IoU min 0.962.

## Stage 3
Palette (8): plumage #4f546c, dark #383c4b (crown, saddle, wing bones, legs), under #626890 (belly,
breast, throat, hackles), membrane #7a5ab8 (membranes, dorsal spikes, tail fan), horn #2e2a2e (bill,
main horns, spars, thumb, talons), bone #d9cfb5 (bill tip, cheek horns, glint), amber #f0a020 (eye),
ink #14121a (pupil, socket).
- r01 — paint + pieces: eye (disc/pupil/glint), 2+2 horns, 8 dorsal wedges (unmirrored), 5 hackle
  clumps/side, wing (thumb claw, 2 spars/side), 4 talons/foot, 3 fan vanes/side. Gates: 2 hit
  shells + slivers 7.2%, all in the spars (straight tubes leave the membrane between sections; long
  thin segments). 1984 tris.
- r02 — Fix: spar points ray-cast onto the membrane surface with midpoints (segments <= 12 cm,
  radius >= 1.6 cm); palette lifted. Result: slivers 0, still 2 hit shells: spar 1 clips the FLANK
  under the first hanging tip. 2128 tris.
- r03 — Fix: (stage 2) tips lean in less; spar 1 ends at 92% of the edge, tips protrude from the
  last ray-cast point. Result: all gates PASS. 2128 tris.
- r04 — Fix: palette one value step up (plumage #4f546c, membrane #7a5ab8) so facets and the purple
  read. Stage-3 final with the orbit: PASS, 2128 tris (body 996 + pieces 1132), 8 colours.

## Stage 4
Rig (roll='auto'): hips, chest, neck0-2, head, bill, tail0-3, fan, thigh/shin/foot/toes.L,
upperarm/forearm/finger0-2.L (+ .R) = 32 bones. skin() then a weight cleanup: wing bones only on
wing verts (+chest), leg bones only on leg verts (+hips), fan off the body; the deltoid ring is a
60/40 chest/upper-arm blend. Pieces: eye/horns -> head, tailfan -> fan, hackles/spines/wingbones/
claws -> body weights.
- r01 — Gates PASS except posed fold-overs 20 (0.94%). Attack signs right (windup rears back, lunge
  drives forward with the wings flared) but the lunge over-rotates: bill to the ground.
- r02 — Fix: lunge pitch net ~18 deg. Result: fold-overs unchanged (20): they are the shoulder stub
  faces sheared by the 60 deg abduction, not the neck.
- r03 — Fix: abduction capped at 35 deg, the spread taken from the forearm/finger unfold. Result: 14
  (0.66%), still FAIL.
- r04 — Fix: deltoid ring weighted 60/40 chest/upper-arm, abduction 30 deg. Result: 8 (0.38%),
  every gate PASS, glbcheck OK, orbit holds. Stage-4 final.

## Totals
- Triangles: stage 1 932 | stage 2 996 | stage 3 2128 (body 996 + pieces 1132) | stage 4 2128.
- Rounds: stage 1 12 (11 fixes + lock) | stage 2 5 | stage 3 4 | stage 4 4.
- Lock edge sha256 978b96f824538c8e (full hash in stage1_lock.json).

## Repair pass (K=2, from review/ad_notes.md), rounds r90+
- r90 — Baseline stage 4: every gate PASS (flips 8 = 0.38%), 2128 tris. No item 0.
- r91 — Critique (must-fix 1): hackles are 5 flat chips over the neck side and chest (head close-up).
  Diagnosis: `blade()` chips rooted on n0/c2 side verts, side axis (0,1,0) = edge-on splinters. Fix: 3 wedge
  clumps/side (`clump()`: roof-topped section, keel, widest at 1/3) rooted by nearest-surface under the jaw
  on the n1 bulge, tips down and back ~16 deg off the throat, shingled. Result: ruff reads in az090, chest
  clean, all gates PASS.
- r92 — Critique (must-fix 4): 8 lilac blades crowded between neck and wing. Fix: 5 blades graded, ray-cast
  onto the ridge from neck base to tail root, spacing 0.13-0.17, raked 30 deg, horn near-black. Result:
  gates PASS on a rerun but flips alternate 8/16 on identical input (kit non-determinism at the margin);
  spines hidden in az090 (raked off the ridge normal, which already leans back).
- r93-r95 — Fix: rake from world vertical, heights 0.34..0.17. Result: the front 2-3 spines clear the wing
  line in az090; 5 graded spines in hero/back34; no purple at the shoulder.
- r96-r99 — Critique: the flip gate flips between 8 and 16 run to run. Diagnosis (debug hook): one needle
  triangle on the deltoid top (3 near-colinear verts) folds in `attack` only; cutting the raise did not
  change it. Fix: (stage 2 vertex move) the deltoid's upper-back vertex lifted 1.4 cm so the stub top is a
  convex ridge; (item 9) attack upper-arm raise cut 30 -> 17 deg (spread kept on forearm/finger).
  Result: flips 6 (0.29%), stable over two runs.
- r100 — Critique (must-fix 2): spars are constant square tubes with Z kinks, open pipe at the wrist.
  Fix: solid 3-ring knuckle bulb capping the wrist knob with the thumb seated in it; 3-sided spars
  (`spar3`, ridge out along the membrane normal) tapering to 40%, on a quadratic (one soft bend) path
  ray-cast onto the membrane, tips at 97% of the keeled edge. Result: hit 2 + spar flips 30: spar 1's path
  crossed the elbow, so its ray-cast jumped onto the arm.
- r101 — Fix: bend control points moved behind the elbow (spar 1 bends at sail 2, spar 2 at sail 3).
  Result: all gates PASS; two curved tapering fingers, no rod past the membrane.
- r102 — Critique (must-fix 3): legs one near-black, knee/hock lost against the underside, posts from the
  front. Fix: stage 2: drumstick ring x1.15 wide and 1.5 cm up (tucked), shank-side hock loop 0.90 ->
  0.65, ankle ring x0.82, heel verts 2 cm back and pinched; stage 3: thigh painted plumage slate,
  hock-down a new 'shank' #6e665e grey-brown, talons horn; 'ink' merged into horn (pupil, socket) to stay at
  8 colours. Result: gates PASS, IoU min 0.957, 3 values on the hind limb (slate / grey-brown / black).
- r103 — Fix (minors 6, 7): main horns raked back ~15 deg more with the tips out, cheek spurs half length
  in horn; eye piece sunk 8 mm. Result: az000 horns sweep back; the eye ring went half under the brow.
- r104 — Fix: eye sunk 4 mm instead (net). Final with the orbit: every gate PASS, glbcheck OK, orbit
  holds; `--review` and `--compare` rebuilt. Triangles: base 1002 (stage 2) | total 1998.
- Not done: tail mid-ring slide (5), throat notch (8). Residual: rear spines 4-5 sit below the wing
  line in az090 (the locked wing tops the ridge by 0.2-0.35 m there).
