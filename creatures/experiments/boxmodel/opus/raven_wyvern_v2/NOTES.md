# raven_wyvern v2 (Opus) — rebuild from a new stage 1

Brief: `../raven_wyvern/review/ad_notes.md` (both ADs: REBUILD, it read as a parrot). The wyvern
cues go IN the base: S-neck, a reptile tail longer than the body, wing forelimbs (upper arm,
forearm, a long finger with the membrane) with a high wrist, raven bill 2:1.

## Blueprint
Side: bill 0.27 m on a 0.2 m skull, S-neck from the breast to the skull (~0.45 m along its
centreline), body 0.62 m (chest y -0.27 to rump 0.33), tail 0.85 m (0.33 to 1.18). Folded wing:
wrist high (z 1.22) behind the neck base, the finger LE running back to a free tip above the tail
root (0.50, 0.96), a notch of negative space between the wing tip and the tail.

## Stage 1
Trunk: 21 six-vertex half-rings tail tip -> bill tip. Legs from v1 (2-face patch on the lower
flank at h0-h2). Wing: 2-face patch on the upper flank (c1-c0) -> shoulder -> elbow -> elbow
knuckle; the forearm is extruded from the two knuckle faces that face the wrist; wrist -> wrist
knuckle; the finger/membrane sail from the two wrist-knuckle faces that face back.
- s1 r01 — first build, 904 tris. Gate FAIL: 40 self-intersecting pairs, all in the wing.
  Critique (az090): the forearm folds back over the upper arm (a 160 deg V at the elbow) and the
  first sail section drops through the forearm.
- s1 r02 — Fix: open the elbow V (elbow back to y 0.04, wrist to y -0.16 z 1.22); pick knuckle
  faces by their centre direction (fresh extrusions have untrusted normals); the first sail
  section starts at the wrist height (TE 1.15). Result: 0 intersections, gates PASS, 904 tris,
  IoU side 0.88. Critique: the wing reads as a HANDLE on the back — forearm and finger make a
  closed loop with a hole under it, the sail is a flat board above; from the front the forearms
  are two posts (raised arms). The neck is a thick column (no S yet).
- s1 r03 — Fix: the membrane moves INSIDE the forearm (sail x 0.22-0.29, forearm x ~0.31) and its
  front section reaches down to z 0.97 behind the forearm; wrist leans in. Result: the hole is
  filled; az090 shows a triangular folded wing with the forearm strut in front. 928 tris. Next:
  it still reads heron/cormorant — the neck is a thick column merging with the breast.
- s1 r04 — Fix: neck rings thinner (W 0.15 -> 0.135 .. 0.09), the neck base (n0 B) raised to z
  0.86 above a forward chest keel (c1 B -0.33, 0.62), head lifted 5 cm. Result: a neck distinct
  from the chest; better. 928 tris. Next: head reads heron/stork (small, pointed, no skull).
- s1 r05 — Fix: skull bigger (W 0.12-0.14, 0.23 deep) with the occiput jutting back over the nape
  (k0 T y -0.34), bill root 0.17 deep. Result: a heavier head, but a hornbill: the skull top runs
  straight into the culmen.
- s1 r06 — Fix: the wing is the signature mass: wrist to z 1.30, tip back to y 0.62, and the sail
  sections zig-zag the trailing edge into two finger points (z 0.78 / 0.76) with scallops between.
  Result: az090/az135 now show a bat-wing sail with a scalloped edge — the first real dragon cue
  in grey. 952 tris.
- s1 r07 — Fix: wrist in to x 0.235, elbow out to 0.33 (A-shape from the front, not raised arms).
  Result: front posts lean in; slightly better. 952 tris.
- s1 r08 — Fix: raven bill with a stop: brow ring k2 up to 1.535, bill root down to 1.465 and
  narrower (W 0.068), hook tip lower. Result: reads raven, not hornbill. 952 tris.
- s1 r09 — Fix: chunkier mass: torso W +12-15 % (c0 0.24), shank/heel/sole sections +15 %,
  drumstick wider; upper arm moved out (shoulder x 0.29, elbow 0.35) after 6 flank hits. Result:
  less wading-bird; gates PASS. 952 tris.
- s1 r10 — Fix: a real S: n1/n2 bow forward (B -0.545/-0.585), n3 pulled back under the skull
  (T -0.37). Result: az090 wire shows the S (forward bow, back bow, head forward). 952 tris.
- s1 r11 — Fix: wing bones as limb masses: upper arm 0.065/0.095, forearm 0.046-0.04, wrist
  knuckle 0.055. Result: forearm reads as a bone, not a strut. 952 tris.
- s1 r12 — Fix: deeper scallops (finger points 0.74 / 0.72) and the wing tip back to y 0.68.
  LOCKED (952 tris, edge sha256 d051cd6f461c71f7...). IoU vs blueprint side 0.77 / front 0.73 /
  top 0.83 (the blueprint's wing was drawn smaller). Honest read of the grey: side and back-3/4
  read as a bird-headed wyvern (S-neck, bat sail with scallops, long reptile tail); the front and
  the high hero view still lean bird (raven head, upright keel chest, bird legs) — horns, spars,
  wrist claw and dorsal spikes in stage 3 must finish the read there.
- s1 RE-LOCK (before any stage-2 work): the first stage-2 run failed "stage 1 changed after the
  lock" with no code change; 3 plain stage-1 reruns passed 1 of 3. Diagnosis: two sources of
  run-to-run variation — extrude()'s side faces come sorted by stale face indices (my knuckle-face
  picker broke ties in that order), and bmesh's region extrude orders new vertices by pointer
  hash, so the lock's vertex ids changed. Fix (no shape change): the picker sorts by position,
  and stage1() ends with a canonical rebuild (vertices/faces in position order). 3/3 reruns now
  match. Deleted the non-reproducible lock and re-locked: 952 tris, edge sha256 fdcb63c41f915842.

## Stage 2
Logged topology: eye-socket inset (k1-k2 upper-side face), a loop each side of the reversed heel
(scaled 1.12 / 0.92), a loop halfway down the upper arm (for the wing lift). Moves: brow verts out,
forward and down over the socket; the gape pressed in and run back to a mouth corner; the hook
only in the last quarter of the culmen; one flattened cheek/jaw plane. keep_valleys on the socket.
- s2 r01 — gates FAIL: slivers 44 (4.2 %). Diagnosis (per-face min-angle dump): the tail-tip
  segment (t0 ring W 0.022), the bill tip, the wing-tip section (sail t 0.012) and the membrane's
  trailing-edge strip (2 cm wide over 15 cm long).
- s2 r02 — Fix: t0 ring opened x1.9/1.5, bill tip x1.4, every sail's TE-in vert 1.4 cm inward (TE now
  ~3.5 cm thick: not paper), the wing-tip section scaled 2.6/1.6 into a blunt knuckle. Result:
  slivers 12 (1.2 %), IoU min 0.979, gates PASS. 1040 tris.

## Stage 3
Palette (8): body #4a5167, dark #343949 (saddle, skull cap, tail end, wing bones), bill dark horn
#3b352f with a bone #cfc3a3 tip, legs #5f564d, ink #1d1e24 (socket, pupil, talons), membrane
#6c4f98, eye #ffb21e. Membrane faces = the sail's bone-in..bone-out slots (colour border on the
bone edge loop). Pieces (all closed solids): eye (iris prism proud of the socket, pupil, glint),
horns (2 main 6-sided swept-back cones, base 0.10 on 0.36 long, + 2 cheek horns), 6 throat
hackle clumps 6 cm thick, 9 graduated dorsal wedges nape->tail swept 32 deg (+ the fan's centre
vane, unmirrored), 4 thick tail-fan vanes, wing thumb claw + 2 finger spars (5-sided tubes,
4.8 -> 3.2 cm, seated 4 mm into the membrane by ray cast, running 13 cm past the trailing edge),
4 talons per foot.
- s3 r01 — 1896 tris, 8 colours. Gate FAIL: 1 hit shell — the fan's centre vane touches both
  side vanes (two contact patches). Read: horns + membrane + fan make it a horned raven-dragon at
  last; body renders near-black in the workbench.
- s3 r02 — Fix: centre vane lifted 2 cm and narrower, side vanes lowered (no contact); body/dark
  lifted one value step (#4a5167 / #343949). Result: gates PASS, 1896 tris (body 1040 + pieces 856).
- s3 r03 — (after the first EEVEE review render) Fix: the eye read as an amber box on the skull
  (4.5 cm deep prism 1.4 cm proud): lens 2.6 cm deep, 4 mm proud, pupil 1.2 cm. Result: reads as an
  eye with a pupil under the brow; gates PASS, 1896 tris.

## Stage 4
Rig (roll='auto'), 23 bones: hips, chest, neck, neck2, head, tail0-2, thigh/shin/foot.L, arm/fore/
finger/tip.L (+ .R). Weight cleanup: wing bones only on wing verts, shin/foot only on leg verts,
the skull (above the n3 plane) rigid to head, the shoulder ring shared 50/50 arm/chest. Pieces:
eye/horns -> head; hackles, spines, tailfan, spars, claws -> body weights; thumb -> nearest bone.
- s4 r01 — fold-overs 3.5 % (63 on the wingbones piece: the thumb claw's transferred weights
  collapse it). Attack ran backwards: -X pitched the neck forward-down (so +X = back/up on this rig),
  and arm Z swung the wing forward instead of out.
- s4 r02 — Fix: thumb its own rigid piece; skull verts rigid to head; SPINE_SIGN -1; the wing lift
  is a twist of the upper arm about its own axis (Y). Fold-overs 15 (0.79 %).
- s4 r03 — Fix: smaller stride thighs (+-17). No change (15): not the walk.
- s4 r04 — Fix: no forearm twist. No change. Diagnosis dump per clip: attack only, flank under the
  shoulder root (+-0.24, -0.12, 0.78).
- s4 r05 — Fix: shoulder ring weights 50/50 arm/chest, lift 40-48 deg. Fold-overs 0; all gates
  PASS, glbcheck OK. (Over the 4-round guide by one; logged.)
- s4 r06 — final with orbit after s3 r03; gates PASS, glbcheck OK; --review and --compare built.

## Totals
- Triangles: stage 1 952 | stage 2 1040 | stage 3 1896 (body 1040 + pieces 856) | stage 4 1896.
- Rounds: stage 1 12 (+ a no-change re-lock for determinism) | stage 2 2 | stage 3 3 | stage 4 6.
- Lock edge sha256 fdcb63c41f915842...
