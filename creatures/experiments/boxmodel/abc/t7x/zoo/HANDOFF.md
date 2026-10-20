# Handoff: creature box-model workflow (2026-10-18)

Paste this into a new session, or use it as the compaction summary.

## Repo and layout
- Repo: `D:\Git\anyCreature`, branch `claude/awesome-sagan-u9memm`.
  - Split into `creatures/` and `hard_surface/`; local commits 0b4f307c and 4e361b19, tag `pre-split-20261014`.
  - Nothing pushed. Latest `main` is merged.
- Work root: `creatures/experiments/boxmodel/`. The kit is in `kit/`.
- Zoo: `abc/t7x/zoo/<creature>/`, holding `<creature>.py`, `NOTES.md`, `stage4/`, `orbit18_sheet.jpg`, `side_by_side.jpg`, `reference/`, `owner_crops/`, `before*/`, `pass3/`.
- Concept sheets: `refs/gpt/v3/<creature>/sheet_N.png`.
  - Wolf: `refs/gpt/wolf_sdf/sheet_ortho_1.png`.
  - Octopus: `refs/gpt/octopus/sheet_h2fix.png`.
- Python: `C:\Users\AZAD\AppData\Local\Programs\Python\Python311` (numpy, PIL, scipy). A `python3.exe` copy was added there. Set `PYTHONUTF8=1`. Blender 5.x runs headless.

## Owner rules (binding)
- **Technique:** the t7 hand box model only.
  - One spine loft of half rings.
  - Legs, arms, ears and fins extruded from regions; detail pieces added on top.
  - Staged S1 lock, then S2 joints and eye socket, then S3 pieces and colour, then S4 rig with idle, move and attack clips.
  - Kit gates must pass.
- **Rejected:**
  - image-to-3D (Hunyuan, TRELLIS, Meshy and the like);
  - SDF or voxel remesh as the final mesh;
  - subdivision cages;
  - GLSL implicit;
  - the anyCreature JSON engine output;
  - the c2 cage.
- **Best reference look:** `abc/t7x/wolf_base`: crisp flat planes, flat colour, low-to-mid poly.
- **Face:** SIMPLE.
  - A small, clear, round lens eye in a clean socket.
  - No face masks, liners, or big cartoon eyes.
  - A chin and jaw are present on bipeds.
- **Priorities:** shape before colour, and read as the species from every angle.
- **Density:** the owner wants the 2x density, mainly on the body loft. Never revert density to fix problems. Fix problems inside the dense mesh: rings set on clean flat planes, no rib bands, density where the outline bends.
- **Junctions are the #1 visible flaw.**
  - Defects to find: arm, shoulder, leg, ear, tail and wing joins showing slits, holes, white specks, knife folds, narrow seam strips, pinches, paper-thin membranes, pieces poking through, strap gaps.
  - Joins must be broad and blended: a shoulder sits over the ribcage, a leg rises out of the flank.
  - The gates do NOT catch these. Probe them and zoom-render them.
- **Owner taste beats AI judge scores.** Fresh blind AI judges drift and oscillate.
  - When used, put the owner rules in every judge prompt.
  - Use the concept sheet as referee when reviews disagree.
- **Process:**
  - Opus models solo, with at most 5 agents at once and one Blender process per agent.
  - GPT, via the Codex CLI, is used for images only, at most 2 at a time, each a fresh session with positive wording.
  - NO Fable unless the owner explicitly asks (owner 2026-10-20).
  - When the owner says something is bad: stop and wait.
  - No commits unless asked.

## Zoo status (20 creatures)
- **Animals:** fox, bear, boar, tiger, stag, snake, crocodile, shark, koi, chameleon.
- **Others:** dragon, goblin, golem, ogre, knight, octopus, spider, crab, owl, raven_wyvern.
- **Passes so far:**
  1. build;
  2. review fixes, round 1 (Fable + Opus reviews);
  3. review fixes, round 2 (sheet as referee);
  4. 2x poly;
  5. verdict mix/revert (a mistake: lost density);
  6. owner fixes (tiger, ogre, fox, dragon, boar eyes);
  7. owner crop fixes (junctions);
  8. dragon: slim legs, wing hole;
  9. "dense+fix": restore 2x density and fix inside it.
- **Dense+fix done:** tiger, boar, stag, bear, fox, snake, koi, goblin, crocodile, chameleon, octopus, knight, golem.
- **Dense+fix still running:** owl.
- **Ogre:** shoulder-join fix in progress. The owner's red line marks a narrow creased seam strip between chest and arm; it needs a broad deltoid-over-ribcage blend.
- **Known open issues:**
  - raven_wyvern reads as a plain raven (the sheet is a raven);
  - shark and koi fins sit near the floor;
  - fox tail clips the hind legs in the trot (5.8%);
  - boar shows a small gap between the hind legs;
  - tiger chest is grey;
  - spider rear reads as a disc.
- **Review files:**
  - `zoo/review_*.md`, `review2_*.md`, `review_poly2x.md`;
  - sheets `zoo20_*.jpg`, `owner_fix5.jpg`, `crop_fix_all.jpg`.

## Next (owner request, 2026-10-18)
1. **Lessons into the kit.** Turn the lessons into a workflow upgrade in `zoo/WORKFLOW.md` plus kit helpers:
   - a junction probe gate (folds, open edges, shell gaps, seam-strip width at limb roots);
   - zoomed junction renders every round;
   - an eye-visibility check;
   - a density rule;
   - a chin/shoulder anatomy checklist for bipeds;
   - a membrane-thickness check.
2. **20 NEW creatures**, varied, not only animals (fantasy, humanoid, insects, birds, sea creatures):
   - fresh GPT concept sheets (true ortho, symmetric legs, chunky near-real style);
   - built with the upgraded workflow;
   - each reviewed by looking at zoomed crops like the owner does, to find and fix flaws.
3. **RECREATE the current 20** with the upgraded workflow (rebuild, not patch).
4. **Show the owner** before/after sheets. Owner taste decides.

## Wave-new status (2026-10-18)
- Done (new workflow): scorpion, griffin, rhino, minotaur, troll (+shoulder fix), beetle, mantis, imp. werewolf built, fix pass running (thigh knives, colour stairs, tail).
- Running: elephant, gorilla, lizardman. Queue: yeti, frog, turtle, penguin, eagle, manta_ray, seahorse, hippo.
- Kit TODO (from builders): techqa drift anchors on first 12 vertex indices not skin-contact verts; eye gate head length = bbox incl. ears (forces big eyes); junction probe misses flat shoulder shelves (troll T-bar) — add top-view shelf check; run.py --compare overwrites side_by_side.jpg; orbit harness writes to creatures/out/.
- Proven tricks: shoulder = torso widest ring, arm from 2x3 region on it, unshrunk first ring; leg roots = 4x3 flank window + 45% inset transition ring; ears leave head side, ring morph from root shape, keep root vertex angles (don't use ellipse_roles).
- Owner 2026-10-21: colour borders via kit/smooth_borders.py (approved, "awesome"). Details (fingers, toes, claws, horns, spines, antennae) must be CHUNKY and readable at game distance, never thin sticks.
- Detail tiers by creature size: tier 3 (large) gets many more details (owner 10-21)
