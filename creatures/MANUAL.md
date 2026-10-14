# anyCreature 1.3.2 — text → game-ready 3D creature, one shot

> **STOP — read this before you write a single line of code.**
> You do not need to build a GLB writer, a renderer, a screenshot tool, a
> measuring script or a modelling script. They are all in this folder, they work,
> and they are the product. If you find yourself starting one, you have already
> left the pipeline: the quality gates you would be skipping are the entire
> reason this harness exists, and delivery REFUSES any file this engine did not
> build. Two field runs were lost to exactly this. The whole interface is:
> write one JSON spec → `node engine/cli.js spec.json out/creature.glb` → follow
> the cards in `cards/`. Nothing else needs writing.

Author: **Ariescar**. The engine and the harness scripts are original work. One third-party component IS bundled: `harness/assets/three-bundle.js` is a build of three.js (MIT, © 2010-2025 Three.js Authors) used by the delivered offline showroom viewer — its licence notice travels in the file and in `THIRD-PARTY-NOTICES.md`. Everything else npm installs at setup time. Licence: MIT (`LICENSE`); third-party attributions in `THIRD-PARTY-NOTICES.md`.

A session receives an order like "make me a menacing mountain giant", asks exactly
ONE question (card 01), and delivers a skinned, animated, vertex-coloured, **AO-baked GLB**
plus an offline showroom viewer — and, with the user's explicit yes, publishes it
to the Gobkit community under CC0.

## Quickstart for the executing session

```bash
bash setup.sh                      # deps + red/green ruler calibration (must print "calibrate OK")
# then read cards/ in order: 00_START → 01_LOW → 02_MID → 03_HIGH → 04_SHIP  (SYNTAX.md when building)
```

Pipeline: interview (≤2Q) → silhouette brief → **LOW: design free + two gates** →
MID (2 rounds, whitelist part blind-reads) → HIGH (1 round, colour + 3 animations)
→ SHIP (scripted delivery, closing dialogue, optional publish).

## The doctrine in one paragraph

Head-to-head experiments showed the model designs BOLDLY when left free, and every
attempt to teach it design upfront made the output tamer — so this harness ships a
**clean painter and a strict inspector**: the creation side gets only the order, the
engine syntax, and a short pit-map of engine-local traps; ALL quality control lives
in gates read by context-free reader agents (never self-graded). Gate 1: RECOGNISED
on the 8+2 orbit — an oblique and the brief's identity view among the views that read. Gate 2: rounds may only make the silhouette BOLDER — LOW's
deliverable is an exaggerated silhouette, not a correct one. MID blind-reads the
whitelisted parts (face, signature, order-named) with one question: what is this?
Same symptom failed twice = concept restart, never a third tweak. Form beats
obedience, everywhere.

## Folder map (accurate — trust this over memory)

```
MANUAL.md            this file
README.md            repository front page (humans)
LICENSE              MIT
THIRD-PARTY-NOTICES.md  bundled + installed dependency licences
SECURITY.md          what runs locally (no sockets, no browser), the public key, untrusted input
VERSION              1.3.2
setup.sh / setup.ps1 deps + example self-check + red/green calibration ("calibrate OK")
cards/               00_START · 01_LOW · 02_MID · 03_HIGH · 04_SHIP · SYNTAX.md · STYLE.md (art direction)
engine/              cli.js + core/ — the ACS engine v2
  core/normals.js    angle-weighted normals + `smooth_angle` creases (bodies stay smooth)
harness/
  outline.py         THE measuring tool: the 8+2 orbit by default (az000..az315 at 45°,
                     az000 = the face, found from the skin's head joint; top; bottom) —
                     silhouettes + thumbs, a colour render per view, orbit_sheet.png and
                     orbit_sil_sheet.png, layout and boldness measures, the head per view
                     (share, outline clear of the body), orbit flags (blob, head_merged,
                     head_hidden, head_small — advice), per-part shares off a z-buffer,
                     colour off the recorded palette, and the hero shot. `--views legacy`
                     = front/side/top/hero, unchanged. All from the vertices — no browser
  judge.mjs          claims judge over outline.py's numbers (part shares, focal contrast,
                     styles, saturated area, orbit_consistent + head_reads (advice), rig/anim/tri)
  deliver.py         stamped GLB + showroom viewer + hero.png + orbit sheets + backup upload pack
  publish.mjs        Gobkit publisher — ONLY after the user's explicit yes (card 04).
                     ALWAYS attempt the upload; the drag-and-drop page is the
                     fallback for a `blocked` result, never the opening move
  gobkit.json        endpoint + release key for publish.mjs
  claims.json        the one claims sheet (boss standard for every creature)
  gates.json/.py     the map: every check tagged block-or-advise and
                     allocate-or-verify. `python3 harness/gates.py [STAGE]`
  roundcheck.py      counts repair rounds and refuses the third tweak (iron law 3)
  round.py           one round in one command: build, silhouettes, measures, pre-check
  brief.py           the brief checked for presence (never content) + the two-pole distance
  identity.py        Gate 1's identity verdict, counted from the reader's words
  partreads.py       MID part reads built and batched in one command
  fit.py             applies the engine's arithmetic fixes (root, proportion, size)
  autofix.mjs        ground offset, loop closure, aim compensation in the clips
  graft.py           transplants a part between creatures at spec level
  wash.py            rewrites a GLB clean; glbcheck.mjs checks the output contract
  ship.py            the closing in one command (package, and publish only on a yes)
  calibrate.py       the red/green ruler calibration setup runs
  synccheck.py       pre-push consistency check (versions, promises, dead references, leaks)
  canary/            decoy images for the blind reads; specs/ the spec template
  assets/            showroom.html + three-bundle.js for the delivered offline viewer
calibration/         wolf_green (must build) · wolf_red + red_5050 (must be blocked, each for its own fault)
example/             wolf.json + wolf.glb — a bred, approved light quadruped
docs/                OUTPUT_CONTRACT.md — what every shipped GLB guarantees
tools/               test.sh (the whole self-check suite, what CI runs) · sync-contract.mjs
```

## The engine in seven lines

- ONE JSON spec: relational joints, chains, mirrored twins (+`joints_R` staggered
  pose), tube volumes with profile rows (superellipse / **named concave sections**),
  `sharp` breaks, per-volume colour arcs, keyframe animations, `touch` connection
  declarations.
- Parts: `curve` (bending horns/tusks/trunks), `membrane` (wings, frills, sails —
  close the outline back to the body or the compiler warns), `fin` (plates,
  conforming onto surfaces by default), `eye`, `paw`, `spike`.
- Normals carry a smoothing angle (`core/normals.js`, default `smooth_angle` 50,
  per volume/part): faces within the angle average, vertices split only at real
  creases. `faceted` on a VOLUME is a BLOCK (`faceted_body`) — bodies break with
  `sharp` rows; `"build":"rigid"` is the escape hatch for machines.
- ONE spec-level `shading` pass — value ramp over the whole body's Y range plus
  grain sized as a fraction of the model diagonal, on every mesh, parts included —
  then **per-vertex AO bakes at compile** into COLOR_0: the solid look ships in
  the file.
- Blocking checks incl. `attack_reach` (an attack must lunge half a body span);
  `warn:` measures (part overlap) are yours to judge; refused builds cost no
  round. The compiler also NARRATES (`info:` lines) — where a curve really bent,
  how far a plate conformed. Free QC; read it.
- Shipped GLBs: primitives merged per material, public bone names (`LArm1Sh`
  convention), mesh `creature` / skin `creature_rig`, harness stamp in `asset`.
- Every GLB embeds its authored spec + parts manifest (`extras.source_spec`) —
  extract, edit, recompile; `harness/graft.py` transplants parts between
  creatures and the normal gates judge the transplant. `embed_spec: false` opts out.
- `node engine/cli.js spec.json out.glb` — that's the whole interface.

## Scale discipline

24px reads FEEL (heavy/fast/sharp); 48px reads IDENTITY (what creature). Judge each
at its own scale. Only the FRONT view (az000, and az180 behind it) may be left-right
symmetric — and paired features (four wings) still stagger. Every azimuth of the orbit
is a view someone will see the creature from: the in-between ones (az045, az135) are
where a pose built for two cameras collapses, and the head has to read from the front
half of the ring, not only in profile. Model-level looks are the final judge.

## Delivery & publish

Card 04 is the whole flow, now ONE command (`harness/ship.py`): gate stamp → name + signature questions (once;
`~/.anyCreature.json` remembers the signature) → `deliver.py` (stamped GLB,
offline showroom viewer, hero.png, backup upload pack) → the share ask LAST →
`publish.mjs` only on an explicit yes — and then RUN it, never assume the
environment is offline. hero.png must be attached or the listing waits for a
human reviewer. CC0 is stamped at consent time, not before.

## Versioning

Semver; old zips never change; every release adds a CHANGELOG entry and a README
row. (1.2.0 was the first public release — earlier development history was
renumbered 0.3.0–0.12.0; the mapping lives in the version-library README.)
