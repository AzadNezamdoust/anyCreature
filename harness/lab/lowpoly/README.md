# Low-poly / quad retopology lab

Inputs: `<in-root>/<animal>/final.obj` (default `E:/gen3d/r8`; for TRELLIS.2 pass `--in-root E:/gen3d/t2 --out-root E:/gen3d/lowpoly_t2`).
Outputs: `<out-root>/<method>/<animal>_<budget>.obj` (y-up, ground y=0, height 1), plus `log.jsonl`
(faces, quads, tris, quad_pct, sec) per method. Budgets: 1500 and 5000 *polygons* (one quad = one face).

Env: `E:/gen3d/venv_lp` (py3.12, torch 2.8.0+cu128, trimesh, pymeshlab, mesh2sdf, scikit-image,
pyquadriflow, transformers 4.39.3, accelerate 0.28.0, x-transformers 1.26.6, ...). No nvcc needed.
`PY=E:/gen3d/venv_lp/Scripts/python`, run from `E:/gen3d/lowpoly`.

## Methods

| dir | command | source |
|---|---|---|
| decimate | `$PY run_classic.py decimate [--in-root R] [--out-root O]` | pymeshlab quadric edge collapse (PyPI) |
| instant | `$PY run_classic.py instant` | Instant Meshes Windows binary from the official README link (`instant-meshes.s3.eu-central-1.amazonaws.com/Release/instant-meshes-windows.zip`) -> `bin/instant-meshes/`. Pure-quad mode, -f auto-corrected (pure-quad subdivides ~4x). |
| quadriflow | `$PY run_classic.py quadriflow` | PyPI `pyquadriflow` 0.0.4 (ctypes wrapper bundling a QuadriFlow DLL; official repo hjwdzh/QuadriFlow ships only linux/osx binaries). Budget auto-corrected, seed retry on internal failure. |
| meshanything | `$PY run_meshanything.py` | github.com/buaacyw/MeshAnythingV2 + HF Yiwen-ntu/meshanythingv2, patched (`meshanything_v2_windows.patch`). Only the 1500 budget (model cap 1600 tris). |
| bpt | `$PY bpt_convert_ckpt.py repos/bpt/weights/bpt-8-16-500m.pt repos/bpt/weights/bpt-8-16-500m.safe.pt` once, then `$PY run_bpt.py` | github.com/Tencent-Hunyuan/bpt + HF whaohan/bpt (Hunyuan 3D community license; not EU/UK/KR). Patched (`bpt_windows.patch`). |

Options: `--animals wolf,horse`, `--budgets 1500,5000`; classic methods also `--solid 256 --tag <dir>`
(watertight SDF + marching-cubes rebuild before remeshing; fixes thin-sheet breakage, ~100 s/mesh CPU).

Render (system python): `python render_all.py <method> [<out-root>]` -> `<obj>.png` (shape sheet via
harness/lab/render.py) and `<obj>_wire.png` (topology via harness/lab/wire.py);
`python montage.py <method> <budget>` -> `<method>/_montage_<budget>.png`.

## Patches needed on Windows / torch 2.8 (no flash-attn)
- MeshAnythingV2: attention `flash_attention_2` -> `eager` with a 4D causal mask in `shape_opt.py`;
  BetterTransformer/optimum call dropped; uid path split fixed; **fp16 must be off** (fp16 + eager attention
  overflows -> 1-face output); precision via env `LP_PREC` (default `no` = fp32). Input goes through the
  official `--mc` marching-cubes preprocess (without it: holes, slivers).
- BPT: HF checkpoint pickles deepspeed objects -> `bpt_convert_ckpt.py` re-saves tensors only
  (weights_only load with inert stubs); `utils.sample_pc` accepts a Trimesh (newer trimesh).
  No face-count control: `<animal>_raw.obj` is the model output; budget files are QEM-decimated from it only when larger.

## Results (r8 Hunyuan3D-2.1 inputs, 2026-10-13)
Contact sheets: `<method>/_montage_<budget>.png`.

| method | works | budget hit (1500 / 5000) | quad % | time/mesh | failure modes |
|---|---|---|---|---|---|
| decimate | 10/10 | exact | 0 | ~1.5 s | thin parts (eagle wing tips, frog toes, horse tail strands) become flat shards; faceted at 1500 |
| instant | 10/10 | 1402-1573 / 4784-5159 | 100 | ~1 s (one frog hang -> 60 s timeout+retry) | thin/open sheets (eagle wings, frog toes, horse hooves, elephant ear, giraffe tail tip) break into floating fragments; best clean quad flow on solid bodies |
| quadriflow | 10/10 | 1389-1601 / 4402-5573 | 100 | 2-7 s (shark@5000 37 s) | collapses thin fins (shark tail -> sticks), kangaroo tail -> ribbon, occasional internal failure (seed retry); smaller fragments than instant |
| meshanything | 2/10 clean (wolf, shark) | 1500 only; 1518-2324 tris | 0 | ~370 s (fp32 eager) | most animals become self-overlapping slabs/streaks (sequence runs past the 1600 cap and degrades); no budget control |
| bpt | 7-8/10 clean raw | none (raw 1134-4677 tris; budget files decimated from raw) | 0 | ~600 s | eagle and frog truncated (upper body missing / open sheets); artist-like triangle layout otherwise, feet/ears/tail survive |

`--solid 256` (watertight rebuild) test on eagle/frog/shark/horse: fixes shark tail and horse tail for
instant/quadriflow, but mesh2sdf sign errors open holes on the frog, quadriflow failed eagle; ~100-150 s/mesh. Optional, not default.

Unavailable learned methods: QuadGPT, Mesh-Pro (no code/weights); DeepMesh (needs flash-attn source build = nvcc, triton);
FastMesh (flash-attn required; weights on a non-official HF account); TreeMeshGPT (weights only on Google Drive,
outside approved sources); MeshFlow (Meta, gated HF); TriFlow (non-commercial license + MeshLib proprietary dep). Not attempted.
