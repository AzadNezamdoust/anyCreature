# LLM 3D modeling research: creatures, hard surface, functional (2026-10-21)

Six research agents ran, all on Opus, with no Fable:

1. creature modeling;
2. hard-surface modeling;
3. functional modeling (rig and game);
4. the LLM agent loop;
5. what this repo has already learned;
6. the YouTube video EyA4NH1fTvA.

Agents 1–4 were mostly working from their own knowledge, with only 0–2 web searches each. Treat every paper reference below as unverified until someone checks it. The repo findings (agent 5) are from real files.

## 0. What the repo already proved (do not redo)
- **Creatures:**
  - The only owner-accepted route is the t7 hand box model: a spine loft of half rings, extruded limbs, seated detail pieces, built in stages S1 to S4. `abc/t7x/wolf_base` is the look reference.
  - The c2 cage, c1 voxel carve, SDF, GLSL, engine JSON lofts, GPT-run lofts, mesh-as-text and image-to-3D were all rejected.
- **Hard surface:**
  - The v10 direct pipeline is the authority (`hard_surface/HANDOFF.md`, `WORKFLOW-V10.md`): concept, then a 4-view sheet, then a Blender look build with 6 or more render-compare passes, then one review and ONE polish, then rig tests.
  - v9/v10 got the only owner "much better and accurate" verdict in the repo.
  - **Conflict:** v10's review seat is Fable. Under the owner's 2026-10-20 no-Fable rule it has to become Opus.
- **Agent loops:** AI judges drift. The wolf peaked at round 1 and fell after that. The fixes are:
  - owner rules written verbatim into every prompt;
  - anchor images;
  - always compare against the best-so-far ("champion");
  - lock the good parts;
  - stop early.

## 1. Creature modeling: recommended techniques
Keep the box model. The research says LL3M, MeshCoder and mesh-token LLMs produce worse organic geometry than ours. What is worth taking from them is the process, not their mesh method.

1. **Typed parametric blueprint.** Spine samples, named rings (`neck_2`, `shoulder_ring`), a limb graph and ratios measured from the ortho views. The LLM edits numbers; the kit code stays fixed. (SceneCraft, 3D-GPT)
2. **Silhouette-fitting optimizer.** Automatically tune ring radii and limb parameters against the front, side and top masks (`masks.npz` already exists), with topology fixed. This removes "thinner than the sheet" drift, which every new build showed.
3. **Joint graph as the source of truth.** Each joint declares its type, axis and range of motion. The kit inserts 3 loops at hinges and 5 at twisting joints, and places the pivot on the joint. This is how shoulder and hip topology should be generated.
4. **Junction guide for multi-branch hubs.** Use the Skin modifier as a guide shape only. The final mesh stays hand rings, built with the kit's proven tricks: the deltoid as the torso's widest ring, and the 45%-inset leg transition ring.
5. **Kit plus lessons library with a promotion rule.** A helper becomes kit code only after it passes on two or more creatures, as `smooth_borders`, the junction tricks and `detail_gate` did. The planner reads the lessons before it writes the blueprint.

## 2. Hard-surface modeling: recommended techniques (kept separate)
1. **Locked part tree plus dimensional plan** in real units before any modeling. The result must match within 2–5% on measured bounding boxes.
2. **Hybrid tooling.** build123d or CadQuery for precise mechanical parts, then Blender for bevel, Weighted Normal, UVs and LODs. Pure bpy for modular and kitbash work. Shape grammars for buildings.
3. **Question-driven checks (CADCodeVerify).** Write a yes/no checklist first, answer it on 4–6 rendered views, and fix only the items that fail. One Opus judge, 3 retries.
4. **Hard-surface helper kit, pinned to the Blender version.** Safe boolean (jitter away coplanar faces, then check manifold and volume), bevel plus weighted-normal presets, trim-sheet UVs, an LOD generator.
5. **Function from the start.** One object per moving part, with the pivot on its real axis. Mechanical parts get rigid weights; destruction chunks are pre-fractured.
- **The video** ("Opus 5.5 + Blender MCP – Detailed Mecha" by Muska): only the metadata could be read. It is hard surface: a live Blender MCP session, building from primitives, with a screenshot-critique loop.
  - Take: quick cheap renders after every piece.
  - Skip: its asset/image-to-3D pulls, and live non-reproducible sessions.

## 3. Functional modeling (both)
| Area | Creatures | Hard surface |
|---|---|---|
| Topology | 3 loops at hinges, 4–5 at twisting joints, a loop radiating from the shoulder, extra hip loops | support loops only where it will be subdivided |
| Rig | skeleton from the build's own joint graph, then heat weights; at most 4 influences per vertex, normalised; learned riggers (UniRig, Make-It-Animatable) only as a fallback | separate parented parts; hinge = Limit Rotation on one axis; piston = Damped Track pair |
| Animation | procedural gait tables (walk/trot/gallop) with IK foot plant; text-to-motion is still humanoid-only | keyframed pivots |
| Game pack | per-bone hurtbox capsules, LODs at 50/25/10%, readable at 64–128 px | `UCX_`/`UBX_` collision, `socket_` empties, LODs |
| Export | glTF plus FBX with engine presets (Unity Y-up in metres, Unreal Z-up in cm), checked by re-importing | same |

Automatic verification for both:
- **ROM sweep:** drive each joint to its limits. Check volume kept at the joint (70% or more), stretch (2x or less), and inverted normals.
- **Pose collision:** BVH overlap between parts in every posed frame.
- **Weight QA.**
- **Clip QA:** foot slide, ground penetration, clean loops.
- **LOD silhouette:** IoU against LOD0 of 0.9 or more.
- **Export round-trip.**

## 4. LLM thinking process (both)
1. Blueprint first, as typed JSON. The code only realises it.
2. Numeric gates run before any visual judge, so the judge only looks at semantics.
3. The critic answers a frozen per-species checklist of 10–20 yes/no questions, each tied to a view. No free-form "make it better". Every critique has to name a concrete edit to a loop or parameter.
4. Keep a version tree:
   - 2–3 variants per round;
   - pairwise A/B judged in both orders (a flip counts as a tie, and a tie goes to the baseline);
   - revert any regression;
   - about 5 rounds per stage at most.
5. Keep a judge-vs-owner log. Any rubric item that agrees with the owner less than 70% of the time becomes owner-only.
6. Roles: one Opus planner, a builder, and a critic that never sees the builder's reasoning. Never Fable unless the owner asks.

## 5. Proposed next steps (owner to pick)
1. Creatures: silhouette-fitting optimizer + typed blueprint JSON in the kit; pilot on 2 thin builds (griffin, eagle).
2. Functional: joint-graph loops + ROM sweep gate + game pack emitter (hurtboxes, LODs, sockets, glTF/FBX round-trip).
3. Loop: frozen per-species checklist + version tree/champion rule in WORKFLOW.md.
4. Hard surface: swap v10's Fable seat to Opus; add safe-boolean/bevel/trim-UV helper kit; trial build123d for one weapon.
