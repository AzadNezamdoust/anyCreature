# Creature-method lab — results log

LLM (Opus) builds 10 animals per method from memory, no references, isolated
folder. Sheets rendered by `render.py`, shuffled by `blind.py`, judged blind by
Opus and Fable: open-answer animal ID + quality 1-10 vs AAA creature form.

Animals: wolf, horse, elephant, giraffe, crocodile, eagle, shark, frog, tortoise, kangaroo.

## Round 1 — five methods (2026-10-12)

| method | recognised O / F | quality O / F |
|---|---|---|
| SDF + smooth-min, marching cubes | 9 / 9 | **3.6 / 4.9** |
| engine skeleton spec (anyCreature) | **10 / 10** | 2.7 / 3.9 |
| mesh-as-text (raw OBJ numbers) | 9 / 8 | 2.9 / 4.5 |
| Fourier tubes (`fourier3d.py`) | 9 / 9 | 2.7 / 3.9 |
| primitive code (ellipsoids/capsules) | 8 / 8 | 2.0 / 2.8 |

(Round-1 sheets used a flat-shaded painter renderer; "surface noise" notes on SDF
were partly renderer artifacts. GPU renderer from round 2 on.)

## Round 2 — the two leaders, with judge notes + anatomy brief

| method | recognised O / F | quality O / F |
|---|---|---|
| **SDF v2** (bone landmarks, muscle masses, carved heads, flat fins) | 10 / 10 | **5.9 / 5.9** |
| SDF v1 (baseline, same renderer) | 10 / 10 | 4.2 / 4.2 |
| engine spec v2 | 9 / 10 | 3.0 / 3.0 |
| engine spec v1 | 10 / 10 | 2.1 / 2.7 |

Best single models (7/10): SDF v2 frog, eagle, horse, tortoise, elephant.
Recurring defects on SDF v2: tube limbs / balloon joints, blobby bodies,
detached flat ears, soft heads and hooves, tube tails.

Takeaway so far: implicit SDF with smooth blending is the only method that
climbs with iteration; the engine's ring-section spec plateaus at ~3.

## Round 3 — SDF v3, self-critique only

| | recognised O / F | quality O / F |
|---|---|---|
| SDF v3 | 9 / 10 | 4.8 / 5.2 |
| SDF v2 (same session baseline) | 10 / 10 | 4.6 / 5.1 |

Plateau: one artist critiquing itself stops improving around 5/10. Same defects
persist (tube limbs, lumpy muscles, crude heads/feet). Judges' absolute scale
drifts between sessions — compare only within a round.

Next: reusable SDF anatomy kit (parts built once and iterated), animals as
parameters on it, and an independent Fable critic per animal.

## Round 4a — SDF anatomy kit v3 (horse, wolf) vs freehand SDF v3

| model | Opus | Fable |
|---|---|---|
| kit3 horse | 4 | 5 |
| r3 horse | 4 | 6 |
| kit3 wolf | 3 | 4 |
| r3 wolf | 4 | 5 |

Kit removed artifacts but did not raise scores. Defects shifted to PROPORTION:
barrel/sagging belly, stick legs, hollow back, hind leg too straight/small.
Next: proportion canon (measurements from memory, written by a separate lane)
+ numeric landmark check before any visual judging.

## Round 5 — kit + proportion canon (numbers before pictures), 10 animals

| | recognised O / F | quality O / F |
|---|---|---|
| kit + canon (r5) | 9 / 10 | 3.9 / 3.6 |
| freehand SDF v3 (r3) | 10 / 10 | 4.5 / 4.5 |

Canon checks passed (most measures in range) but the judged look got WORSE.
Matching numeric proportions does not make forms read better; freehand
gesture beat measured stiffness. Five rounds: LLM-from-memory geometry
ceiling ~5/10 on a strict AAA scale, regardless of representation.

## Round 6 — LLM-directed local text-to-3D (HunyuanDiT -> Hunyuan3D-2.0)

LLM writes art-directed prompts, picks best of 3+ seeds from rendered sheets,
pipeline cleans floor slab, decimates to <= 100k tris. Shape only, no texture.

| | recognised O / F | quality O / F |
|---|---|---|
| **LLM-directed generator** | 10 / 10 | **6.3 / 6.8** |
| freehand SDF v3 (r3) | 10 / 10 | 4.1 / 4.7 |

Best: eagle 8/8, kangaroo 8/7, horse 6/8, wolf/tortoise/shark 7/7.
Weak: crocodile 4/5 (stands upright, model ignores "sprawling"), giraffe 4/5
(short neck, camel hump). Defects: open foot soles from slab removal, noisy
fur geometry, bloated torsos. Peak VRAM ~9.6 GB (T2I) / 5.6 GB (shape).

## Round 7 — critic-picked references, octree 512, watertight cleanup

| | quality O / F |
|---|---|
| r7 (critic refs + hole-fill/Taubin/remesh) | 4.9 / 5.4 |
| r6 (seed-pick only) | 5.4 / 5.9 |

Better references helped (elephant 7/7, giraffe 6/7, shark 7/7) but the
cleanup hurt more: hole-filling the cut feet made flat planar caps/slabs
(frog 3/4, crocodile, kangaroo, wolf "flat paw caps"), the eagle's thin tail
fan tore (3/3), tortoise shell flap. Lesson: never cut the floor through the
feet and planar-cap the hole; fix floors at the image/mask stage, fill holes
with faired (curved) patches only.

## Round 8 — Hunyuan3D-2.1, mask-stage floor removal, faired hole fill

| | quality O / F |
|---|---|
| **r8** (2.1 + critic refs + clean8) | **5.6 / 6.1** |
| r6 (2.0, seed-pick) | 5.3 / 5.9 |

Best so far overall. Floors removed in the image mask (no foot slicing), only
thin-sheet deletion by ray-cast thickness, curved hole patches. Remaining
defects: soft/blobby generic forms, fused "pancake" toes (frog), open hoof
soles, stringy mane/tail, fur noise. Single-image-to-3D shape tops out ~6/10
on a strict AAA geometry scale; AAA also needs retopo, UVs, PBR textures, rig.

## Round 10 — low-poly / quad retopo of r8 meshes (~1500 faces), judged on shape + topology sheet

| method | recognised O / F | quality O / F |
|---|---|---|
| **QuadriFlow** (100% quads) | 10 / 9 | **5.1 / 5.8** |
| Instant Meshes (100% quads) | 10 / 9 | 4.0 / 5.4 |
| quadric decimate (tris) | 8 / 9 | 3.9 / 5.1 |
| BPT (learned artist tris) | 9 / 8 | 4.0 / 4.7 |
| MeshAnything V2 (learned) | 10 / 9 | 2.1 / 2.2 |

Classical quad remesh beats the learned artist-mesh models today. No open
quad-native learned generator has released weights (QuadGPT, Mesh-Pro).
Every method breaks thin open parts (wings, toes, fins, tail strands).
TRELLIS.2 and Hunyuan PBR texturing blocked on CUDA Toolkit (user installing).

## Round 9 — best-of-12 Hunyuan3D-2.1 meshes per animal, Fable critic picks

| | quality O / F |
|---|---|
| r9 (critic best-of-12) | 5.5 / 5.8 |
| r8 (critic ref, best-of-2) | 5.6 / 5.5 |

No real gain: more candidates do not lift the ceiling. Untextured
single-image Hunyuan3D-2.1 shape plateaus ~5.5-6/10 on a strict AAA scale.

## Status / next levers

Best workflow so far: LLM art-directs prompts -> HunyuanDiT refs -> critic
picks ref -> Hunyuan3D-2.1 shape -> mask-stage floor removal + faired cleanup
-> QuadriFlow quad retopo for low-poly. Remaining AAA gaps: textures (PBR),
TRELLIS.2 comparison (both need CUDA Toolkit), multi-view input, thin-part
handling, rigging. Not AAA yet.

## Rig stage prototype (wolf, horse; QuadriFlow 5000-quad input)

Auto skeleton (34 joints, engine naming) fitted inside the voxelised volume
(medial paths + leg-slab detection), geodesic 1/d^4 weights, 4 influences,
GLB via the engine's own buildSkeleton/compileAnims/writeGLB, idle + walk.
Walk is clean (no candy-wrapper, no collapse); remaining: belly/armpit
stretch between legs (edge stretch up to ~2.4x), ~1.5 cm ground sink, jaw
split unchecked. Scripts in harness/lab/rig.

## Multi-view input test (Hunyuan3D-2mv; wolf, horse, eagle, frog)

2mv runs without nvcc (~35 s/seed), but no open nvcc-free generator makes
consistent front/side/back views; HunyuanDiT turnaround sheets repeat one
angle and never draw a back. Using side + mirrored side (+ front): horse
slightly better, wolf mixed, eagle same, frog worse vs r8. Not adopted.
Next cheap test: r8 hero ref + its mirror in 2mv side slots.

## Round 11 — PBR textured assets (Hunyuan3D-2.1 paint on r9 picks), full-asset judging

Mean O / F: **4.9 / 5.6** (form + texture vs AAA). Best: elephant 6/7,
giraffe 6/7, wolf 5/7. Weak: kangaroo 4/4 (flat red, cartoon), crocodile 4/4
(dark, mushy), tortoise 3/5 (smeared shell). Judges' recurring texture
defects: baked lighting in albedo, blurry/smeared detail (Lanczos instead of
RealESRGAN), flat colour, seam smears on back views.
Texturing runs with pip CUDA 13.4 + VS 18 MSVC, no system install.

## Round 12 — texture fixes (de-light refs, 9 views, true 4K, UV dilation)

| | quality O / F |
|---|---|
| r12 | 5.0 / 5.1 |
| r11 | 5.3 / 5.2 |

No measurable gain at preview resolution (de-light hurt horse/eagle/shark
colour, fixed by fallback; 768 views blurrier). Texture plateau ~5/10:
limited by reference quality (cartoon/dark refs) and the Lanczos stand-in
for RealESRGAN. Next levers need user decisions: RealESRGAN weights source,
triton-windows + DINOv3 licence for TRELLIS.2.

## Round 13 — real RealESRGAN x4plus super-resolution (official weights)

r13 vs r12 with head close-ups: O 3.8 / 3.8, F 5.3 / 5.3. Both judges saw
each pair as near-identical and scored them the same. Sharper fur/feather
pixels are not what limits the score; close-ups exposed baked lighting,
smeared texture and broken head geometry (giraffe, crocodile). Texture-side
tweaks are exhausted; quality is bounded by the reference image and the
generated geometry.

## Round 14 — TRELLIS v1 (microsoft/TRELLIS-image-large, MIT) vs Hunyuan3D-2.1, same refs, untextured

| | quality O / F |
|---|---|
| Hunyuan3D-2.1 (critic-picked r9) | 6.0 / 5.6 |
| TRELLIS v1 | 5.2 / 5.6 |

Tie-ish; Hunyuan slightly ahead per Opus. TRELLIS v1 runs nvcc-free on
Blackwell (spconv-cu126 wheel, xformers->SDPA shim), ~10-11 GB, 10-40 s.
TRELLIS.2 needs DINOv3 (gated) — blocked without the user's HF login.

## Overall (14 rounds, ~400 models)

| family | best judged quality (O / F) |
|---|---|
| LLM writes geometry from memory (SDF, Fourier, mesh text, primitives, engine spec, anatomy kit) | ~4.5-5.9 |
| LLM directs open image->3D (Hunyuan3D-2.0/2.1, TRELLIS v1) | ~5.6-6.8 |
| + PBR texture (Hunyuan Paint 2.1, de-light, RealESRGAN) | ~5.0-5.6 as full asset |
| low-poly quad retopo (QuadriFlow best) | 5.1 / 5.8 |

No configuration reached AAA (~9-10). Ceiling is set by the open
generators and the single reference image; remaining gaps: thin parts,
baked lighting, generic soft forms, open-source quad-native generators
unavailable.

## Round 15 — thin-part repair (thin15.py) + per-animal Hunyuan/TRELLIS ensemble

thin15: voxel thin-sheet detection, solidify to min thickness, rebuild
watertight, snap untouched regions back. On Hunyuan it finds almost nothing
(safe no-op); on TRELLIS it closes shark fins / horse mane-tail but adds lumps
and cannot turn paper feathers into anatomy. Critic choices: 8/10 stay the
Hunyuan r9 pick; frog -> TRELLIS v1; tortoise -> Hunyuan + thin15. Not
blind-judged (8 of 10 identical to r9). Thin parts need better input images,
not mesh repair.

## Pipeline + prompt pack
- harness/lab/pipeline/run_inbox.py: external reference images (Nano Banana /
  GPT Image) -> candidates + contact sheet -> pick -> textured GLB, quad LODs,
  rigged GLB. Tested end-to-end on wolf (~23 min on shared GPU).
- harness/lab/PROMPTS_reference_images.md: per-animal prompts for hero +
  consistent side/front/back views.

## 8 GB VRAM study (emulated cap 7.5 GiB per process)

Whole workflow fits: T2I 4.0 GiB (CPU offload + VAE tiling, identical image),
Hunyuan3D-2.1 shape 6.5 GiB (manual accelerate offload chain; bit-identical
mesh), Paint 2.1 6.5/7.3 GiB at 6 views (9 views OOM; slight quality cost),
mask/clean/QuadriFlow/rig CPU-only. Wolf end-to-end ~5 min. Texture headroom
~0.2 GiB reserved: confirm on a real 8 GB card. GTX-1050-class (2-4 GB)
cannot run it (shape weights alone 5.7 GiB). Details: harness/lab/lowvram/REPORT.md.

## UniForge3D check (2026-10-20)

Multi-view unposed images -> 3D (TRELLIS.2 + VGGT based). Blocked: needs gated
DINOv3 (same as TRELLIS.2). Weights CC BY-NC 4.0 (non-commercial). Pipeline has
low_vram mode (per-stage GPU loading), 8 GB fit untested. Details:
harness/lab/UniForge3D_TEST.md.

## Round 16 — TRELLIS.2 via trellis.cpp v0.8.1 (community GGUF, res 512) vs Hunyuan3D-2.1, untextured shape

| | recognised O / F | quality O / F |
|---|---|---|
| **Hunyuan3D-2.1** (r9 picks) | 10 / 10 | **6.4 / 6.8** |
| TRELLIS.2 (trellis.cpp) | 10 / 10 | 3.4 / 4.4 |

Hunyuan wins clearly. TRELLIS.2 thin parts (tails, feathers, toes, shell plates,
fur) come out as open jagged sheets; crocodile 1-2/10. Wins on cost: peak VRAM
~3.5 GB CUDA / ~2.9 GB Vulkan (fits 8 GB without offload), ~12 s GPU, texture
bake without nvdiffrast (MIT + DINOv3 terms). 1024 cascade untested (weights
download stalled). Scripts: trellis_cpp/.

## Round 17 — commercial-safe texturers vs Hunyuan Paint 2.1 (unlit albedo, 5 animals, two blind Opus judges)

| method | licence | quality O1 / O2 | VRAM @7.5 GiB cap |
|---|---|---|---|
| **MV-Adapter ig2mv (SDXL) + own moderngl bake** | Apache-2.0 + OpenRAIL++ | **5.8 / 5.0** | 6.5 GiB, ~2 min |
| Hunyuan Paint 2.1 (tex13) | Tencent (EU/UK/KR excluded) | 5.4 / 4.8 | 7.3 GiB |
| Sequential inpaint (SDXL depth CN + IP-Adapter) | Apache-2.0 + OpenRAIL++ | 2.8 / 2.4 | 6.3 GiB, 8-13 min |

Judges scored MV-Adapter slightly higher, but owner review (Azad): only Hunyuan
Paint gives a true unlit albedo; MV-Adapter and seq-inpaint bake lighting/sheen
into the colour map, which breaks in-engine lighting. Hunyuan Paint stays default;
MV-Adapter is the commercial-safe fallback and needs a delighting pass. Defects shared by both: baked shading/specular, flat
cartoon kangaroo. Seq-inpaint views drift (one side bleached white). Albedo
only (fixed metallic/roughness). Scripts + report: texc/.
