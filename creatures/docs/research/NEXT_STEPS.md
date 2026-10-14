# Next step: the staged box-model experiment

Written to hand this work over to a local session. Everything before it is on
branch `claude/awesome-sagan-u9memm`: pipeline fixes, engine passes 1–7, the
8+2 orbit, and the research in this folder (`README.md`).

## Where things stand

- The engine (`engine/`) and harness (`harness/`) are green: `bash setup.sh`
  prints `calibrate OK`, and `bash tools/test.sh` passes 101/101.
- The owner's verdict on the engine output: it reads as lofted tubes, not a
  hand-made low-poly model. Seven tuning passes did not change that, because
  every spec setting is a parameter of a tube.
- Both independent research passes rank the same approach first: the LLM
  writes a **box-modelling program** in headless Blender, driven by a
  render → critique → one-fix loop, with the existing harness as the judge.
  See the proofs in `proto/`.
- Owner feedback that defines the protocol below: *"you change topology of
  the mesh for small details that you should keep for later — the neck of the
  wolf is fully deformed because you wanted some fur details."*

## Setup (local)

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install bpy tbb numpy pillow scipy
# Linux without a desktop GL stack:
#   apt-get install -y libegl1 libgl1 libopengl0 libgl1-mesa-dri libegl-mesa0
#   export LD_LIBRARY_PATH=$PWD/.venv/lib
python -c "import bpy; print(bpy.app.version_string)"   # 5.0.x
```

Blender itself with `blender -b -P script.py` works the same way.

## Protocol: primary → secondary → tertiary, the base topology locked

Each stage is its own function in the bpy program, with its output archived.

1. **Primary (blockout).** One connected, mirrored (mirror + clipping)
   low-poly base mesh from box-modelling verbs:
   - masses and silhouette first;
   - legs, ears and tail extruded out of torso and head faces, with no
     intersecting shells;
   - edge loops only where the body bends (2–3 per major joint) and where the
     form changes;
   - flat-shaded, 400–1,500 triangles.

   Iterate this stage alone, grey, with render → critique → one diagnosed fix
   per round. Look at front, side and three-quarter renders, plus the orbit
   from `python3 harness/outline.py <glb> <dir>`. Stop when the base reads as
   the creature on its own. Then **lock** it: write the vertex count, face
   count and a hash of the sorted edge list to `stage1_lock.json`.
2. **Secondary.** Planes, bevels, vertex moves and loop slides on the locked
   base. Vertex positions may move. Connectivity may change only by inserting
   a full edge loop at a joint or in the face, each logged with its reason.
   Report the orbit silhouette IoU against stage 1 per view (expect > 0.9).
3. **Tertiary.** Fur ruff, tail brush, claws, eye detail, tusks, crest and
   moss are **separate low-poly pieces** weighted to the nearest bones, or
   flat colour (4–8 region colours). At the end, assert the base connectivity
   still matches the lock plus the logged stage-2 loops. A tertiary detail
   never edits the base mesh.
4. **Rig and animation.** The armature comes from the same skeleton the model
   was built on, with automatic weights and idle / move / attack clips. Export
   glTF with vertex colours, then run `node harness/glbcheck.mjs` and the
   orbit. The harness accepted Blender GLBs unchanged during the research.

Total 500–3,000 triangles, in the stylised-game look of `cards/STYLE.md`: a
slightly larger head, chunky limbs, a clear face with brow, eye and nose, and
separate fingers and toes where visible.

## The run

- Creatures: the wolf (built twice, once by each model, for a direct
  comparison), the raven-wyvern, and the mountain giant (separate fingers and
  knuckles on the fists).
- Deliverables go under `experiments/boxmodel/<model>/`:
  - the staged program;
  - per-stage renders, including wireframes;
  - orbit sheets and GLBs;
  - `stage1_lock.json` and the lock-assertion output;
  - `NOTES.md`: each round's critique and fix, and triangles per stage;
  - a side-by-side image: current engine creature | stage-1 grey base | final.
- Judge: the existing blind identity reads, plus a new blind pairwise read,
  "which of these was made by a person?", asked in both orders to cancel
  position bias. Compare against the shipped engine creature, and against a
  CC0 hand-made reference rendered the same way if one is available.
- `harness/synccheck.py` may need an `experiments/` exemption like the one it
  has for `docs/research/`.

## If it wins

- Replace the tube-loft engine as the modelling step, or port the box-model
  verbs to the Node engine if zero dependencies stays a hard rule.
- Drop the checks that only police loft artefacts (`soft_mass`,
  `root_containment`, junction blends, L1–L8 as requirements).
- Rewrite `cards/STYLE.md` and the syntax card in loop and ring terms.
- Recalibrate the triangle budget to 0.5–3k.
