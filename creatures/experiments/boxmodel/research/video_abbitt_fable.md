# Grant Abbitt, "Blender Low Poly Character: PS1 Style Modeling for Beginners"

https://youtu.be/uIHuqFLa_X0, Blender 4.5.3. Read from the
auto transcript and the chapter list, not watched. Reviewer: Fable 5.1 as a
senior game character artist. Date: 2026-10-04.

## 1. What he teaches, step by step

**00:00–02:50 Reference setup.** Drag a front/side sheet into the viewport,
Alt G / Alt R to clear transforms, R X 90 to stand it up, numpad 1 for front.
Object data > opacity 0.2, X-ray (Alt Z) so the mesh is see-through. Shift D
+ R Z 90 for the side copy, both pushed back in Y so he models in front of
them. He nudges the sheet, not the model, when the centre line is off:
"doesn't have to be perfect".

**02:50–09:15 Head and neck (one object).** Default cube scaled to head
width. Ctrl R loop down the middle, delete the right half, Mirror modifier
with clipping and on-cage. Then, in this order:
- front view: box-select vertex rows (including the back ones) and G them
  to the chin line; 2–3 horizontal loop cuts, moved to the cheekbone and the
  jaw; "obviously I need more topology around here";
- side view: pull rows in and out for forehead/neck, rotate a row;
- the rounding trick: ONE vertical loop cut down the side face, then select
  the new column (Ctrl-click shortest path) and GG edge-slide it toward the
  front, GG back; the box becomes a 6-sided section with a flat front and
  back and two bevelled corners. Same on the back column. He says "it's
  very kind of square and flat at the front" before, "much closer" after;
- neck: E on the bottom face, pull down INTO the future torso, scale and
  move back; one optional loop. "So we can overlap what will be the body";
- nose: a horizontal loop at nose height, pull the columns in, E one face,
  scale down, S X; he rejects the "loop around the nose" version as awkward;
- eyes: he shows I (inset) + loop cuts, then undoes it: "more complicated
  than we need to be";
- ear: I on two side faces, E, move the corner verts in front view;
- finish by GG-sliding rows "to smooth it out". Sculpt mode is mentioned as
  optional.
Resulting head: a 6-sided ring in plan, about 5 rows (crown, brow, cheek,
jaw, neck), one nose block, one ear block. Roughly 60–80 faces per half.

**09:15–12:16 Torso and pelvis (two objects).** Shift right-click sets the
3D cursor, a new cube, same mirror routine (he forgets clipping twice and
fixes it with S X 0 on the seam). Front view: one loop cut "ready for that
arm socket", one at the waist; side view: "we're going to need some more
loop cuts in here just to make this a little more circular", again one
vertical loop per side face, GG-slid. Torso ring: 6–8 sides, 3–4 rows. The
pelvis is a SEPARATE cube: "PlayStation 1 graphics tended to have big
blocky pieces". Optional loops for the bum and the hips; he keeps it blocky.

**12:16–15:46 Arms and hands (five objects per side).** He mentions
icospheres for shoulders "if you're not too worried about the polygons",
then does the cheap version: a cube, S Z, rotated, pushed into the torso
("make sure it overlaps nicely"). Arms are drawn slightly BACK on the sheet
"so it's easy to model the arms and easy to rig as well". Upper arm: one
loop cut, one edge moved up (the deltoid), the end face scaled down (the
elbow). Shift D for the forearm, rotate, scale the end for the wrist (S Y
on the wrist loop, Alt-click to select a loop), one loop in the middle,
GG-slid to swell the forearm. Hand: a cube, S X thin, one loop, the knuckle
verts pulled up; E the end face, rotate, S X, E again: a two-segment
mitten. Thumb: E a side face, rotate, scale, E again. Section counts: arms
4 sides (a box) with one longitudinal loop on the outer face where he
wants a curve, 1–2 rings per bone segment.

**15:46–18:23 Legs and feet.** Shift D the pelvis cube, S Shift Z, S X, move
rows; "I'm probably going to want a little bit more topology": one loop,
GG. Shift D for the shin, scale, overlap. Foot: a cube, E the front face
twice (instep, toes), a loop at the toe line pulled down, top view: rotate
the toe segment outward "a little bit of a curve to the foot".

**18:23–end Assembly.** Deepen the overlaps: "the overlap is there for the
rigging, so when we move this arm around it won't separate". Mirror
modifier on the upper arm with the torso as the mirror object; select the
other arm/leg parts, the mirrored one last, Ctrl L > copy modifiers. Done.
Total: about 14 objects, every one a closed box with 1–2 loops.

**UVs and texture.** The description promises "an easy UV map and
texture"; the transcript has NOTHING on it. Either cut from the upload or
in a follow-up. Treat this video as modelling only.

## 2. What answers our problems, what does not

**Answers.**
- *Tube-like medium forms.* His sections are never circles: a box, plus one
  slid loop per side face, read as a rounded box with a flat front and back.
  Our `part_rings` already has a superellipse exponent `p`; his look is
  p ≈ 3–4 with 4–6 vertices, not p = 2 with 8. His limb is also one shaped
  box per bone: deltoid edge up, elbow face scaled, forearm loop slid out,
  wrist scaled flat. That is exactly the "a limb has the masses a real one
  has" line in BRIEF.md, done with 2 rings per bone.
- *Topology / density.* One loop per bone segment, placed where the form
  turns (deltoid, forearm swell, knuckles, toe line), never to stripe. Loops
  for shoulder and hip do not exist: the joint is an overlap. The head gets
  its rows at brow, cheek, jaw: the same landmarks BRIEF.md rule 3 names.
- *Budget on eyes.* He builds nose and ear as one extrusion each and
  deliberately skips eye topology. Supports the owner's point: eyes are a
  paint job or a 60-triangle part, not cage topology.
- *Order.* He says chest-first is better than head-first; and he reaches a
  readable whole figure with boxes before any loop is slid. That is a
  blockout gate before refinement, which we have (`--blockout`) but run
  after loops exist.

**Does not fit.**
- *PS1 separate parts for the whole body.* The look is "bits of a toy";
  our target is Quaternius/Synty: welded, flat-shaded, a continuous
  silhouette at the shoulder and the hip. Under flat shading an
  intersecting part shows a hard crossing line on every facet it cuts; at
  the hip and shoulder this reads as a seam, not a crease.
- *Deformation.* His parts are rigid per bone and overlap deep enough to
  hide the gap at the elbow. At a 90° knee or an attack swing the inner
  side gaps and the outer side stacks. Our posed gates (pass-through,
  z-fight, fold) would all fire by design.
- *Humanoid only, by eye, no measures.* No quadruped, no tail, no
  proportion check; "doesn't have to be perfect" is a person's eye, our
  pipeline needs the numbers.
- *No UV/texture content* (see above).
- *Mirror as separate objects* is a Blender-UI convenience we already have
  in `object_from_bm`.

## 3. Changes for our pipeline, ranked

1. **Cage per part from `part_rings`, welded only where it deforms**
   (`kit/bmkit.py`, new `cage_part(part, sides, stations, p)` next to
   `ring`/`bridge`; BRIEF stage 1). Each part of `part_guide` (torso, neck,
   head, each limb chain, extras) becomes its own closed box loft: the
   station list from `part_rings(k.guide_parts, part, n)` gives centre,
   width, depth, p; `sides` = 6 for limbs, 8 for the torso, 6 for the head.
   Then: limbs are joined to the torso at their root ring with
   `bridge_uneven` (the one junction that must deform), while head-to-neck,
   hands, feet, ears and tail stay separate closed parts, pushed into the
   parent by ≥ 0.5 × their own width and bound rigidly (`bind(bone=)`).
   Gain: no junction n-gons or fans anywhere except the two root rings,
   limb profiles follow the stations instead of a lofted average, the
   builder writes no bridge code by hand. Cost: ~150 lines of kit, the
   "one closed shell" gate becomes "one shell per listed part" with a
   whitelist of intended overlaps in `META['overlaps']` so techqa's
   pass-through and z-fight gates skip them; 10–20% hidden triangles.
2. **Rounded-box sections as the default** (`carve.part_rings` default
   `p`; BRIEF rule 3). Default p = 3.5 for limbs and neck, 3 for the torso,
   4 for the head and muzzle; limb rings 6 vertices: front, back, and two
   per outer/inner face, with the outer face's mid vertex slid toward the
   front (his GG) so the section is deeper than wide. Gain: the single
   biggest fix for "tube-like" at no triangle cost. Cost: one afternoon,
   regress on the c2 builds.
3. **Ring budget per bone** (BRIEF topology rule 2 made numeric;
   `topology()` gate). Per bone segment: a root ring, ONE mid ring where the
   mass swells (his deltoid, forearm, calf), an end ring; joint bands get
   their 2 loops only where the limb is welded. Anything above 3 rings per
   segment outside a joint band fails. Gain: the "constant-section columns
   with ring bands" note from the c2 review goes away. Cost: small; some
   current builds will fail and must be relocked.
4. **Head recipe and an eye cap** (BRIEF rule 6; `kit/parts.py`). Head =
   6-sided box with rows at crown, brow, cheekbone, jaw, neck; one slid
   vertical loop; nose = one face extruded and scaled (no loop ring around
   it); ear = inset + extrude of two faces, or `ear_cup`; eyes = `eye_set`
   lite (60) or paint only. Gate: head ≤ 30% of base triangles, eye parts
   ≤ 120 triangles total. Gain: budget back to silhouette and limbs. Cost:
   a paragraph and one gate line.
5. **Order of work and an earlier blockout look** (BRIEF §5; `--blockout`).
   Torso and pelvis first (they set scale and stance), then head, then
   limbs, then extremities from the library; a grey render after the box
   stage, before any loop cut or slide. Gain: the reviewer sees proportions
   before density hides them; fewer relocks (the c1 giant/goblin relocked
   several times). Cost: one extra render per build.
6. **Shoulder ball option** (`parts.py` `shoulder_mass`, his icosphere
   remark). A 6–8 sided closed ball at the shoulder/hip, separate, rigidly
   bound, under the limb root. Gain: the arm can swing without the torso
   junction stretching, which the c2 review flagged ("raised limbs stretch
   in the attack"). Cost: 40–60 triangles per joint; only worth it where
   the attack clip raises a limb. Try after 1.

On the three questions asked:
- **(a) Separate overlapping parts.** Yes for the LLM pipeline: it removes
  junction topology and limb-to-torso flow entirely, and each part becomes
  a short, checkable program. The visual cost is acceptable for head,
  hands, feet, ears, tail and the neck join (many shipped stylised assets
  do exactly this), and NOT acceptable at the shoulder and the hip in a
  Synty-style flat-shaded creature: the crossing line reads as a seam and
  the posed gap shows in the attack clip. Hence the hybrid in change 1.
- **(b) His counts as `part_rings` defaults.** Sides: yes, 4–6 limbs, 6–8
  torso, 6 head: matches BRIEF rule 3 already, the news is the exponent
  and the slid loop (change 2). Rings: 2–3 per bone (change 3). Loops at the
  shoulder/hip: he has none; we need 2 where we weld.
- **(c) His order.** Torso first, head, limbs, extremities, loops last.
  Adopt (change 5). His eyes-last-or-never is also right for us.

## 4. Verdict

**Partly useful.** As a tutorial it is a beginner's box-modelling pass with
no UV or texture content, nothing on quadrupeds and nothing measurable. But
it demonstrates, cleanly, the three things our c2 wires lack: a shaped
rounded-box section instead of an ellipse, one mass ring per bone instead
of bands, and parts that end where a bone ends instead of flowing through
a hand-written junction. And it validates the direction already under way:
a part-by-part implicit base is his overlapping-parts method with the weld
done by the field. **First thing to try:** on the goblin (his biped case),
build stage 1 as separate closed box lofts straight from `part_rings`
(p = 3.5, 6 sides, 3 rings per bone), limbs bridged to the torso at the
root ring only, head/hands/feet as rigid overlapping parts; render the
grey blockout next to the c2 cage and run the attack clip through techqa.
If the blind pair prefers it and the posed gap at the elbow/knee stays
under the fold gate, make change 1 the default and move to the bear.
