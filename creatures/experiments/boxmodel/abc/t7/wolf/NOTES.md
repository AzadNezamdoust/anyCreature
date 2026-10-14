# wolf (t7) — NOTES

Stage 0: blueprint drawn from the brief (1.1 m to ear tips, nose y=-0.90 to tail tip y=+0.82). One spine loft (tail tip -> nose, 6-vert half rings = 10-gon full), legs extruded as 2-face (hexagon) regions from the lower flank, ears as 1-face extrusions from the skull's top-outer face.

## Stage 1
- r1: Critique: every view reads canine, but the top/front views are a greyhound: torso half-width 0.16, the whole animal ~0.3 m wide against the brief's 0.5 m; legs stilt-thin. Diagnosis: SECS W column (R0..N1) and the blueprint's front/top were drawn thin. Fix: widen torso/neck W x1.3, move leg centres x 0.10 -> 0.13; widen blueprint front/top to match the brief width. Tris 712. IoU side/front/top 0.881/0.892/0.929.
- r2: Result of r1: better, top view now has a chest and hips; front IoU fell to 0.794 because the widened blueprint head is wider than the model's. Critique: the head is a small narrow wedge (W 0.10-0.11 on a 0.205 chest, ~0.5x), front view shows a pin head; ears are thin spikes. Diagnosis: H0..H4 W and EAR rx. Fix: head W x1.3 (skull 0.13-0.145, muzzle 0.09-0.048), ears rx 0.048 at x 0.11. Tris 712.
- r3: Result of r2: better, the front view has a real head and ears read; front IoU 0.839. Critique: legs are sticks (forearm rx 0.035, wrist 0.03) under a now-wide body: the stilt look STYLE §3 bans, worst in az000/az180. Diagnosis: FORE/HIND rx/ry. Fix: legs thicker ~1.25x (forearm 0.044x0.058, wrist 0.036x0.042, gaskin 0.045x0.062, hock 0.034x0.048), paws broader 0.054x0.075. Tris 712.
- r4: Result of r3: better, legs now read as limbs with a real forearm and gaskin; IoU 0.879/0.878/0.914. Critique: az090 — the neck is a thin, concave-topped stalk between skull and withers, where a wolf has its thickest mass (the ruff); the head looks perched. Diagnosis: N0/N1 T/B 0.14/0.115 with centres low. Fix: N0 (c z 0.75, tilt 35, T 0.16, B 0.15, W 0.165), N1 (c -0.535/0.81, T 0.135, B 0.12). Tris 712.
- r5: Result of r4: mixed — the neck is fuller in az045/hero, but the top view shows a dark crease across the neck: N0's top (z 0.881) now sits 5 cm above C2's (0.828) over 2 cm of y, a near-vertical step. Critique: that notch breaks the crest line from skull to withers. Diagnosis: C2 centre/T too low for the new N0. Fix: C2 c z 0.635 -> 0.655, T 0.21 (top 0.858) so the crest ramps C1 -> C2 -> N0. Tris 712, IoU 0.874/0.884/0.916.
- r6: Result of r5: better, the crest now ramps withers -> neck -> skull without the notch; IoU 0.872/0.885/0.916. Critique: az090/hero — the head is a shallow wedge (skull 0.19 deep) on a 0.30-deep neck; STYLE wants the head sized UP, and the jaw line is thin. Diagnosis: H0..H3 T/B. Fix: skull T 0.105-0.112, B 0.105-0.12 (deeper jaw), W +0.005; muzzle B 0.074/0.052; ears follow the higher skull (E1 z 1.045, tip 1.105). Tris 712.
- r7: Result of r6: better, the skull is deeper and the jaw reads from az090; ears still end at 1.105. IoU 0.867/0.882/0.912. Critique: az090 — the underline runs almost straight from brisket to stifle, so the brief's "deep chest with a clear tuck-up" is weak; the torso reads as a tube. Diagnosis: W0/R2 bottoms at 0.50-0.515, M0 at 0.445. Fix: raise W0 bottom to 0.545 and R2 to 0.53 (M0 0.455) so the belly lifts sharply behind the ribs. Lock this round if gates pass. Tris 712.
- r8 (LOCK): Result of r7: better — a clear tuck-up behind the ribs in az090, deep chest reads. Gates PASS, locked: 358 verts, 712 tris, edge sha256 9bdaed8a74f731af. Blueprint IoU side/front/top 0.858/0.882/0.912 (the side drop is the tuck-up and the thicker neck against the drawing). Orbit: holds, no collapse.

## Stage 2
- r1: Plan: joint rings at elbow, stifle and mid-neck (loopcut); eye socket = inset in the stop face pushed 12 mm in; brow corner forward/out; cheekbone out; flatten muzzle side and bridge into single planes.
  Result: gates PASS (min IoU vs s1 0.992, 796 tris, 56 edges turned, 0 stuck). The socket reads under the brow in hero; the muzzle has a flat side.
- r2: Critique: az000/az045 — the nose is the loft's flat end cap, a round disc facing straight forward: reads as a pipe end, not a nose pad. Diagnosis: H4 ring is vertical and as wide as the muzzle. Fix: H4 top verts forward 22 mm, chin verts back 18 mm, H4 narrowed x0.85 — a forward-down slanted pad for the black nose piece.
  Result: gates PASS (min IoU 0.992, 796 tris); the nose now ends in a slanted wedge, no disc. Stage 2 done in 2 rounds (orbit holds).

## Stage 3
- r1: Plan: paint 6 colours on the base along existing loops (saddle on the back faces, cream throat/bib/belly/lip, tan legs, black nose pad, dark tail tip); pieces: amber lens eyes with a black pupil fan proud of the socket floor, neck ruff clumps (7/side), cream bib clumps (3/side), tail brush clumps (4/side, dark at the tip), 3 claws per paw.
  Result: gates PASS (1284 tris, 6 colours, hit/float/zfight 0). Reads as a grey wolf: ruff, bib, dark tail tip, amber eyes, black nose.
- r2: Critique: hero/az135 colour — the saddle covers every upward-ish face from withers to rump and reads as a dark blanket thrown over the back, not a saddle along the spine. Diagnosis: body_rule saddle test n.z > 0.5. Fix: n.z > 0.72 and z > 0.68 (the top band of faces only).
  Result: gates PASS; the saddle is now a spine band from withers to croup, flanks stay grey. 1284 tris, 6 colours.

## Stage 4
- r1: Rig built on J (16 bones + .R mirrors, roll='auto'), skin + body-weighted binds for all pieces; clips idle 48 / move 24 (diagonal trot) / attack 32 (rear back, head-down lunge, snap). All gates PASS: 0 hit/float/zfight, slivers 0.6%, fold-overs 0.00%, drift 0, glbcheck OK. Posed az090 checked: flexed foreleg folds the paw back in swing, thigh swings forward, head goes down-forward in the lunge.
- r2: Critique: attack f16 az090 — with 26 deg on the neck alone the ruff clumps on the neck crest lift off as scales and the crest folds sharply. Diagnosis: the lunge bend concentrated in one bone. Fix: spread it — neck 26 -> 20, chest -8 -> -11, head 10 -> 8 (snap 22 -> 20). Final round with orbit.
  Result: all gates PASS again (0 hit/float/zfight, slivers 8 = 0.6%, fold-overs 0.00% tris / 0.00% area, drift 0, lock OK, glbcheck OK); orbit holds. Review packet built.

Triangles: stage 1 712 · stage 2 796 · stage 3/4 1284 total. Rounds: s1 8 (lock r8), s2 2, s3 2, s4 2.
Weaknesses: the cream belly rule catches the lower flank faces, so az090 shows a flat cream stripe along the side; from the front the nose pad is a large black hexagon; the body stays lean (coyote proportions) with straight tan "stocking" legs.
