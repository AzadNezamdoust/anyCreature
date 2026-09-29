# Box-model build brief

You are building ONE creature as a hand-made-looking, stylised low-poly game
asset, by writing a box-modelling program for headless Blender 5.1 with the kit
in `experiments/boxmodel/kit/`. This brief is the whole contract; read it all
before writing code.

## 1. The bar, and what failed before

The owner's verdict on everything so far: it does not look made by a person.

- The **engine creatures** (`example/wolf.glb`, `example/gallery/*.glb`) read as
  lofted tubes: round sections everywhere, blobby joins, smooth gradients, no
  deliberate planes.
- The **first box-model protos** (`docs/research/img/research_opus_blender_wolf_vs_ours.jpg`)
  failed differently: plank legs with arbitrary bends, a crate for a body, a
  stiff tail, the face a flat wedge. Fur chunks were stuck on in a way that tore
  the neck apart. The owner said: *"you change topology of the mesh for small
  details that you should keep for later — the neck of the wolf is fully
  deformed because you wanted some fur details."*

The target is the look of a good commercial stylised low-poly asset: the
Quaternius or Synty kind of creature. That means:

- a strong, designed silhouette from every side;
- a few confident planes per form;
- chunky, appealing proportions (`cards/STYLE.md`: a bigger head, a thick neck,
  chunky limbs, a clear face with brow, eye and nose);
- 4–8 flat colours, with the colour borders on edges.

A person looking at it should not be able to tell a program made it.

## 2. Craft rules: what makes low poly read as hand-made

1. **Silhouette first.** Every view (front, side, top, 3/4) has a readable
   outline with clear negative space: between the legs, under the belly,
   between the neck and the back, between the arms and the body. Look at the
   silhouette before the shading.
2. **Plan the planes.** Flat shading turns every face into a visible facet, so
   placing faces *is* the drawing. Put plane changes (creases) where anatomy
   turns: brow ridge, cheekbone, jaw line, the side of the muzzle, shoulder
   blade, rib cage, hip bone, knee, hock, elbow, wrist. Make big forms from few
   large faces. Flatten groups of vertices that should read as one plane
   (`flatten`). Avoid long runs of equal thin quads; that is the tube look.
3. **Sections are not circles.** A head is a wedge or box, a muzzle a tapered
   box, a neck a thick trapezoid, a chest a deep keel (narrow at the bottom),
   the belly tucked, the hips squarer. Limbs are deeper front-to-back than
   side-to-side, with narrow wrists and ankles, broad paws, hands and feet.
   Use 6–8 sided sections on the torso and 4–6 on limbs; never a uniform
   12-gon.
4. **Rhythm.** Loops are dense where form changes (face, joints) and sparse
   across big planes (flank, back). Ring spacing is never uniform.
5. **Anatomy for the pose.**
   - Quadrupeds stand on the toes: the foreleg is nearly straight with the
     elbow tucked behind the chest bottom and a small forward wrist. The hind
     leg has a thigh, a knee (stifle) forward and a hock angled back.
   - Bipeds: slightly bent knees, the weight over the feet, arms hanging
     slightly forward of the torso, and an A-pose angle (not a T-pose).
6. **Faces carry the character.** Build a brow that overhangs the eye and an
   eye socket; put a stop (step) between the skull and the muzzle, give the
   nose a distinct block, and make the mouth line or jaw read. Eyes are in the
   topology (a socket in stage 2) plus a separate small low-poly eye piece in
   stage 3, never a sphere stuck on the surface.
7. **Small things are few and bold** (STYLE.md §1): claws, teeth, tufts, crest
   blades. They are separate pieces in stage 3, never edits of the base.
8. **Colour follows topology**: the belly, muzzle or saddle colour border runs
   along an edge loop you placed for it.

## 3. The protocol (the kit enforces it)

Conventions: metres, Z up, the creature faces **-Y**, its LEFT flank is **+X**,
the feet on **z = 0**. Model the left half (x >= 0). Seam vertices sit exactly
on x = 0, nothing goes below x = 0, and no face lies in the x = 0 plane
(`object_from_bm` adds the live Mirror: X, clipping, merge).

- **Stage 0: blueprint** (recommended; it is cheap). Write `blueprint.json`
  with side, front and top outlines (20–50 points each) and a few landmarks,
  then run `run.py <prog> --blueprint` to draw `blueprint.png`. Fix the drawing
  until the proportions read (STYLE.md numbers). Stage-1 renders then overlay
  the model's orthographic silhouettes on it and print an IoU per view.
  Format:
  ```json
  {"side":  {"outline": [[y, z], ...], "marks": {"eye": [y, z]}},
   "front": {"outline": [[x, z], ...]},
   "top":   {"outline": [[x, y], ...]}}
  ```
  The side view looks at the left flank, with the head (-Y) on the image's
  left. Front and top outlines may be the x >= 0 half; they are mirrored.
- **Reference sheet (settings G/O).** When your creature folder has a
  `reference/` folder, the orchestrator ran `kit/refs.py` on a generated
  turnaround sheet. `reference/` holds `sheet.png`, the four views cropped
  (a 2 x 2 sheet: `side.png` facing left, `front.png`, `rear.png`, `top.png`
  turned head-up like the kit's top render; an older 1 x 4 row: `front`,
  `side`, `back`, `threeq`), `trace.png` (the traced outlines over the views)
  and `refs.json` (layout, scale, warnings, source). `blueprint.json` was
  traced from it: the side outline, the symmetrised front half and (2 x 2) the
  symmetrised top half from the plan view, scaled so the side height is the
  brief's height, **the side and top bounding boxes centred on y = 0**, feet
  on z = 0.
  It is the stage-1 target: the IoU is measured against it, so do not redraw
  it; add marks (eye, joints) only. **Read the four reference views before
  stage 1 and every round**: the round sheets and the review packet show them
  next to the matching renders. Where the views disagree with each other or
  with the brief, the side view wins for proportions; note the choice.
- **Stage 1: blockout.** One connected, closed, mirrored low-poly base with no
  self-intersections and 400–1,500 triangles (counted after the mirror).
  - Masses and silhouette come first.
  - Legs, arms, ears, tail and neck are extruded out of torso or head faces
    (`extrude`). There are no separate shells and no intersecting parts.
  - Edge loops go only where the body bends (2–3 per major joint) and where
    the form changes.

  Iterate grey (see §5) until the base reads as the creature on its own. Then
  lock it with `run.py <prog> --stage 1 --lock`. After the lock, stage1() is
  frozen: any change fails the gate. Later shape changes go in stage2().
- **Stage 2: secondary.** Vertex moves, `flatten` planes, loop slides and
  asymmetry are free. Connectivity changes happen ONLY inside
  `with k.topo(bm, kind, reason):` blocks. Allowed changes:
  - a full loop at a joint or on the face (`loopcut`);
  - a local loop that ends in a terminator (`partial_loop`). Use it to add
    density in the face, paw or hand without running a loop through the whole
    body: the topology cheat sheet's 2-1 / 3-1 reductions. Put the terminator
    where nothing bends (skull, cheek, mid-back, flat of the thigh). **Never
    at the neck or a joint.**
  - a crease (`chamfer`, i.e. two loops hugging an edge);
  - an eye socket or nostril (`inset`, a loop inside one face).

  Each change is logged with its reason. Extrusions and deletions are not
  allowed in stage 2. Gates:
  - the base collapses back to the lock hash;
  - the silhouette IoU against stage 1 is > 0.9 on every orbit view;
  - the base is still one closed shell with no self-intersection.
- **Stage 3: tertiary.** Detail pieces are SEPARATE low-poly objects: fur
  ruff, tail brush, claws, eyes, teeth, tusks, crest, moss, cloth. Paint 4–8
  region colours (`paint`). Stage 3 may not touch the base geometry at all;
  painting its faces is fine. Total 500–3,000 triangles.
- **Stage 4: rig and clips.**
  - Build the armature from the same joint positions you built the model on:
    keep a `J = {...}` dict of joints at the top of the program and use it in
    stage 1 AND stage 4.
  - Skin the body with `skin` (automatic weights; this applies the mirror).
  - `bind` each piece: rigidly to one bone (claws, eyes, teeth), or with
    `body=` so it borrows the body's weights (ruffs, crests).
  - Make three clips named exactly `idle`, `move` and `attack`, each 16–48
    frames and looping (the first frame equals the last).
  - The run exports the GLB, runs glbcheck and the orbit, and renders posed
    frames. **Check the posed wire renders: joints, and above all the neck,
    must bend without collapsing.**

## 4. Kit API (`from bmkit import *`)

Program skeleton (`experiments/boxmodel/opus/<creature>/<creature>.py`):

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='wolf', model='opus', engine_glb='example/wolf.glb')   # engine_glb: '' if none
J = dict(hip=(0.0, 0.30, 0.62), ...)            # the skeleton the model is built on

def stage1(k):
    bm = bmesh.new()
    ...                                          # rings, bridge, cap, extrude, loopcut, moves
    return object_from_bm('body', bm)            # adds the live Mirror

def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'second elbow loop: the bend'):
        loopcut(bm, edge_near(bm, (0.13, -0.40, 0.42)), t=0.5)
    for v in verts_where(bm, lambda c: c.z > 0.9 and c.y < -1.0): v.co.z += 0.02
    commit(body, bm)
    # apply_mirror(body) then edit/commit again for asymmetric moves (optional)

def stage3(k, body):
    paint(body, {'fur': '#7d7973', 'belly': '#efe6cf', ...}, lambda c, n, i: 'belly' if n.z < -0.5 else 'fur')
    ...                                          # pieces: build a bmesh, object_from_bm('eye', bm, mirror=True), paint it
    return [pieces]

def stage4(k, body, pieces):
    rig = armature([('hips', J['hip'], J['spine'], None), ('thigh.L', J['hipL'], J['kneeL'], 'hips'), ...])
    skin(body, rig)
    for p in pieces: bind(p, rig, bone='head')   # or bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 24: {'chest': (3, 0, 0)}, 48: {}})
    clip(rig, 'move', {...}); clip(rig, 'attack', {...})
    return rig

run(META, stage1, stage2, stage3, stage4)
```

Verbs:

- **Creating geometry:**
  - `ring(bm, pts)` makes vertices.
  - `bridge(bm, a, b, closed=False)` fills quads between two rows.
  - `cap(bm, verts)` makes one n-gon.
  - `extrude(bm, faces, offset=None)` returns `{'faces', 'verts', 'sides'}`;
    the original faces are removed.
  - `inset(bm, faces, amount, depth)`.
- **Moving vertices:** `move(verts, d)`, `scale(verts, s, pivot)`,
  `rotate(verts, axis, deg, pivot)`, `place(verts, pts)`, `flatten(verts)`,
  `slide([(v, target), ...], t)`, `snap_seam(bm)`.
- **Finding things:**
  - `face_near(bm, p, n=None)`: the nearest face centre, optionally with a
    normal filter; use the filter, ties are common.
  - `edge_near(bm, p)`, `vert_near(bm, p)`, `faces_where(bm, pred(c, n))`,
    `verts_where(bm, pred(c))`.
  - `edge_ring(edge)`: the ring a cut would cross.
- **Loops:**
  - `loopcut(bm, edge, t=0.5, near=None)` cuts a full loop across the quad
    ring that crosses `edge`. To add a ring around a leg, pass an edge that
    runs ALONG the leg.
  - `partial_loop(bm, start, end, t, terminate='fan'|'quad')`.
  - `chamfer(bm, edge, frac)`.
- **Objects and colour:**
  - `object_from_bm(name, bm, mirror=True)`, `edit(ob)`, `commit(ob, bm)`,
    `apply_mirror(ob)`.
  - `paint(ob, palette, rule(centre, normal, face_index) -> key)`, with sRGB
    hex colours.
  - `report(ob)` returns counts, components, open edges and intersections.
- **Rig:**
  - `armature([(name, head, tail, parent[, connect]), ...])`: a name ending
    `.L` on +X gets its `.R` mirror automatically.
  - `skin(body, rig)`, `bind(piece, rig, bone=None, body=None)`.
  - `clip(rig, name, {frame: {bone: (rx, ry, rz) degrees}}, loc=None)`.
  - Bone-local rotation: Y runs along the bone (twist), X bends a limb
    forward or back, and Z bends it sideways. Check the posed renders and
    flip signs if a knee bends the wrong way.

Iteration speed: add `--no-orbit` to skip the harness orbit on ordinary
rounds. Run it without the flag on the lock round and on each stage's final
round. Other builders run Blender at the same time, so a round takes 10–40 s.

Gotchas: extrude only faces away from the seam (a leg comes from a side or
lower-side face, never a quad touching x = 0). A half ring runs from a top
seam vertex to a bottom seam vertex; cap the ends with it. Keep legs and arms
clear of the body (no intersections).

## 5. The round loop

One command per round, from the repo root:

```
py -3.11 experiments/boxmodel/kit/run.py experiments/boxmodel/opus/<creature>/<creature>.py --stage N --round R [--lock]
```

It prints the gates (PASS/FAIL), writes `stageN/` renders and composes
`rounds/sN_rRR.jpg`, a contact sheet with seven clay views, three wire views
and the blueprint overlay. **Read the sheet image every round** (and single
PNGs from `stageN/` when you need detail). Then write `NOTES.md` in 3–5 lines:

- **Critique:** name the single worst problem, the view it shows in, and what
  it should look like.
- **Diagnosis:** which rings or vertices in the code cause it.
- **Fix:** ONE change.
- **Result:** after the next render, better or worse, plus the triangle count.

Rules:

- One diagnosed fix per round.
- Stage 1 gets up to 14 rounds; lock when it reads as the creature from every
  view. Stage 2 up to 6, stage 3 up to 5, stage 4 up to 4.
- If a gate fails three times running for the same reason, stop and report
  it.
- Be your own harshest critic: compare against the bar in §1, not against
  the last round.

## 6. Deliverables (all under `experiments/boxmodel/opus/<creature>/`)

- the program;
- `blueprint.json` and `blueprint.png`;
- `stage1_lock.json`, `stage2_log.json` and `lock_assert.json`;
- `stage1/` … `stage4/`: renders, wireframes, GLBs, `orbit/` sheets and
  stats; stage 4 also has `glbcheck.txt` and the `posed/` renders;
- `rounds/`: every round's sheet;
- `NOTES.md`: every round, plus triangles per stage;
- `side_by_side.jpg`, from `run.py <prog> --compare` after stage 4.

Final report (your last message, max 15 lines):

- the gates at stage 4 (PASS/FAIL);
- triangles per stage;
- the lock edge hash;
- the number of rounds per stage;
- the three biggest remaining weaknesses, stated honestly;
- the paths to `side_by_side.jpg` and `stage4/sheet.jpg`.

Do not commit. Do not touch files outside your creature folder; the kit is
shared. If the kit blocks you, report the exact error rather than editing it.

## 7. Lessons from batch 1 (wolf, raven-wyvern, giant, boar, goblin)

- **Identity comes first.** The raven-wyvern passed every gate and still read
  as "parrot". Pieces added in stage 3 could not rescue a stage-1 silhouette
  that said "bird". Put the creature's defining silhouette cue in the locked
  base: antlers can wait, but the body plan cannot.
- **Palette value.** Use mid values, so facets read under the key light.
  Dark creatures (raven, bear) go dark but not black, around #3a-#55 in value.
  Never wash a creature out to grey.
- **Bone signs.** On limb bones, positive bone-local X swings the bone
  backward. Check the posed renders before trusting a knee.
- **Turn budget.** You run in chunks of about 60 tool calls. Keep rounds lean:
  use `--no-orbit` except on lock and final rounds, and read one sheet per
  round. If you are cut off, the orchestrator resumes you from your files.
- `extrude()` on multi-face regions is fixed, so do not delete loose edges
  yourself. Grey-stage orbits now work.

## 8. Tech QA and art direction (from the owner's close-up review of batch 2)

Close crops showed errors that no gate measured: an antler through an ear,
paper-thin cape and ruff plates reading as shards, and pinched creases at a
shoulder. The kit now measures them from stage 2 on (`kit/techqa.py`).

- **Folds follow the form.** Before export every non-planar face is
  triangulated and its edge turned so it folds OUT (a ridge), not IN (a
  pinch). A socket that should dent in is kept with
  `META['keep_valleys'] = lambda c: ...`.
- **Gates:**
  - no piece shell passes through a surface twice;
  - no floating piece (a gap);
  - z-fighting ≤ 2 faces, so an eye lens must sit proud of its socket, not
    flush;
  - slivers ≤ 2% of triangles;
  - posed fold-overs and collapses ≤ 0.5%;
  - open (single-sided) pieces are warned: give capes, ruffs and webbing a
    little thickness.
- **Renders:** each stage 2–4 sheet shows the tech heatmap, with the legend
  in `review/3_tech.jpg`. Stage 4 adds close-ups (head, a front limb, a hind
  limb, the largest piece); set your own with
  `META['closeups'] = [(name, (x, y, z), radius, view)]`.
- **Rolls:** `armature(..., roll='auto')` gives consistent bone rolls (+X
  swings a hanging limb's tip forward, on both sides). Use it for new builds.
- `flatten()` keeps seam vertices on x = 0.
- **Review packet:** `run.py <prog> --review` builds `review/`. The art
  director reviews it against `ART_DIRECTOR.md`; a repair pass works from
  those notes.
- **Gates added after the round-2 art direction:**
  - posed fold-overs must stay ≤ 0.5% of the surface AREA as well as of the
    triangle count;
  - no piece may come off or slide over the body in a pose (`drift`). Bind
    face pieces with the same weights as the skin under them (`bind(body=)`),
    or weight the skin under a rigid piece 100% to that piece's bone.
- New locks sort stage 1 into a canonical vertex/face order, so the lock is
  stable across runs.
- **Kit fixes after the N/G/O builds (2026-09-28):**
  - `extrude()` returns `sides` in a fixed order with fresh normals, and
    `move`, `scale`, `rotate`, `place`, `flatten` and `slide` refresh the
    normals of the faces they touch. Picking a face by its normal after a
    move is now safe.
  - Posed QA checks every keyed frame of each clip, plus 20/40/60/80%. A
    blink or a snap keyed between those points is checked now. A triangle
    counts once however many frames it folds in.
  - `clip` (pink, a warning for now): triangles that cross another part in a
    pose but not at rest, such as a limb through a flap or a paw through the
    cheek. The count is in `techqa.json`.
  - `stretch` (teal, a warning): a triangle whose longest edge grows past 2×
    its rest length in a pose. It means a stray weight, unless the part
    stretches by design, like a tongue.
  - The wire overlay no longer uses even offset, which drew needle spikes
    at sharp corners.
