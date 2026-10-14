# CUDA extensions without a system CUDA Toolkit (2026-10-13)

All from official PyPI NVIDIA wheels (sha256 checked vs PyPI JSON) + installed VS 18 (2026) Community MSVC.
No system install, no PATH change outside a cmd session, no admin.

## 1. Toolkit from pip wheels
- `nvidia-cuda-nvcc-cu12` 12.8.93 / 12.9.86 **Windows wheels contain only ptxas.exe + nvvm dll (no nvcc.exe,
  cicc, cudafe++)** -> unusable as a compiler on Windows. (Installed 12.8 nvcc/runtime/cccl into E:\gen3d\venv
  while probing; harmless.)
- CUDA 13 split wheels DO ship a full compiler: `nvidia-cuda-nvcc`, `nvidia-cuda-runtime`, `nvidia-cuda-cccl`,
  `nvidia-cuda-crt`, `nvidia-nvvm` (nvvm/bin/cicc.exe). Layout `nvidia/cu13/{bin,include,lib/x64,nvvm}`.
- 13.0.88 nvcc: `cudafe++ died with status 0xC0000005` with MSVC 14.50/14.51 (VS 18 is the only MSVC here; no
  VS2022 toolset). -> use **13.4.92** (nvcc/runtime/crt/nvvm 13.4.92, cccl 13.3.4.3.1): works.
- pip itself hung/very slow on this box (busy CPU, many python procs) -> wheels fetched with curl from
  files.pythonhosted.org URLs taken from the PyPI JSON API, sha256 verified, unzipped with python zipfile:
  `E:\gen3d\cuda134\nvidia\cu13` (CUDA_HOME). Wheels kept in `E:\gen3d\cuda13_whl\134`.
- Torch headers need cusparse/cublas/cusolver/curand/cufft headers: `E:\gen3d\cudatest\fetch_hdr.py` pulls newest
  win_amd64 wheels of nvidia-cublas 13.8.0.4, nvidia-cusparse 12.8.6.72, nvidia-cusolver 12.3.4.7,
  nvidia-curand 10.4.4.72, nvidia-cufft 12.4.0.43 and extracts include/ + *.lib only into the same tree.
- Env: `E:\gen3d\cuda13_env.bat` (vcvars64 from VS 18 with the VS Installer dir on PATH for vswhere; CUDA_HOME,
  PATH (+bin\x86_64 for cudart64_13.dll, nvvm\bin), INCLUDE, LIB, TORCH_CUDA_ARCH_LIST=12.0, DISTUTILS_USE_SDK=1,
  `NVCC_APPEND_FLAGS=-Xcompiler /Zc:preprocessor` (CCCL 13 #errors on MSVC traditional preprocessor)).
- Hello world `E:\gen3d\cudatest\h.cu` -> `nvcc -arch=sm_120` -> prints `0 2 4 6`. OK.
- torch version check: torch raises on CUDA major mismatch (cu128 torch vs nvcc 13). `E:\gen3d\cudatest\build_ext.py
  <dir> <setup args>` runs a setup.py with `torch.utils.cpp_extension._check_cuda_version` disabled.
  Resulting .pyd links cudart64_13.dll -> at runtime `os.add_dll_directory(r'E:\gen3d\cuda134\nvidia\cu13\bin\x86_64')`.
  Mixing torch's cudart 12.8 + extension's cudart 13 in one process works (driver 597.16).

## 2. (A) Hunyuan3D-2.1 paint extensions, built into E:\gen3d\venv (torch 2.11.0+cu128) — BUILT + RAN
- mesh_inpaint_processor: plain C++/pybind11 (no CUDA). Built with cl directly (`E:\gen3d\cudatest\mip.bat`)
  -> `hy3dpaint\DifferentiableRenderer\mesh_inpaint_processor.cp312-win_amd64.pyd`.
- custom_rasterizer: `E:\gen3d\cudatest\cr.bat <dir>` (env bat + build_ext.py ... bdist_wheel -d E:\gen3d\wheels_cu134),
  then `pip install --no-deps E:\gen3d\wheels_cu134\custom_rasterizer-0.1-cp312-cp312-win_amd64.whl`.
  Source patches needed for MSVC/Windows (originals saved as *.orig):
  - grid_neighbor.cpp: `torch::zeros({vec.size()/3, 3})` narrowing error C2398 -> cast each dim to (int64_t).
  - grid_neighbor.cpp / rasterizer.cpp / rasterizer_gpu.cu: `long` -> `int64_t` (data_ptr<long> is an unresolved
    LNK2001 on Windows where long is 32-bit).
  - `setup.py install` makes a zipped egg whose stub import yields an empty module -> install via wheel instead.
  Smoke test: rasterize 1 triangle 64x64 -> 512 px covered. OK.
- Runner `E:\gen3d\paint21.py <mesh> <ref> <out.obj> [views=6] [res=512]` (HF_HOME=E:/gen3d/hf):
  - add_dll_directory(cudart13); stub `bpy` module (only used by convert_obj_to_glb -> GLB step done separately);
  - huggingface_hub symlink creation fails (WinError 1314, no symlink privilege) -> are_symlinks_supported=False;
  - RealESRGAN x4 super-res weights are a GitHub release of xinntao (not approved) -> replaced by x4 Lanczos;
  - use_remesh=False (repo's remesh -> fast_simplification "target_reduction must be between 0 and 1" on this mesh).
  Weights downloaded: tencent/Hunyuan3D-2.1 hunyuan3d-paintpbr-v2-1, facebook/dinov2-giant (HF official).
- Result wolf (E:\gen3d\r8\wolf\final.obj 59k V / 98k F, ref_rgba.png), 6 views @512, 4K texture:
  model load 136 s (incl. download), paint 192 s, torch peak alloc 13.4 GiB.
  Out: E:\gen3d\tex\wolf\textured.obj/.jpg/_metallic.jpg/_roughness.jpg.
- `E:\gen3d\glb_preview21.py <dir>`: builds PBR `textured.glb` with trimesh (baseColor + metallicRoughness G=rough,
  B=metal) and `preview.png` (4 azimuths, albedo, rasterized with the new custom_rasterizer). Looks correct.

## 3. (B) TRELLIS.2 — extensions BUILT, pipeline NOT RUN (3 blockers below)
- venv: `E:\gen3d\venv_trellis2` (py 3.12). pip install of torch cu130 from download.pytorch.org hung twice on this
  box (stuck extracting, then WinError 32 lock between two pip processes) -> torch 2.11.0+cu128 / torchvision
  0.26.0+cu128 copied from E:\gen3d\venv site-packages (same official wheels). cuda=True.
- Sources: github.com/JeffreyXiang/CuMesh (recursive -> submodule JeffreyXiang/cubvh), JeffreyXiang/FlexGEMM,
  NVlabs/nvdiffrast tag v0.4.0, in `E:\gen3d\ext\`. o-voxel from TRELLIS.2; its submodule
  `o-voxel/third_party/eigen` was fetched from gitlab.com/libeigen/eigen (official Eigen; pinned by TRELLIS.2 —
  NOTE: not in the named source list, header-only).
- Built with `E:\gen3d\cudatest\cr.bat <dir>` (built in E:\gen3d\venv's python — identical torch) -> wheels in
  `E:\gen3d\wheels_cu134\`: cumesh-0.0.1, flex_gemm-1.0.0, nvdiffrast-0.4.0, o_voxel-0.0.1 (all sm_120).
  CuMesh/FlexGEMM/nvdiffrast built unmodified. o-voxel needed MSVC patches (originals *.orig):
  `E:\gen3d\cudatest\msvc_narrow_fix.py` (int64_t casts in torch::zeros/empty({..}) in hash.cu, filter_neighbor.cpp,
  filter_parent.cpp, rasterize.cu), svo.cpp from_blob `{(int64_t)v.size()}`, flexible_dual_grid.cpp `1e-6d`/`0.0d`
  literal suffix (GCC-only) -> `1e-6`/`0.0`.
- Installed into venv_trellis2 (+ PyPI deps: transformers 5.19, timm, kornia, trimesh, opencv-headless, ... and
  xformers 0.0.35 from download.pytorch.org/whl/cu128).
- Smoke test `E:\gen3d\cudatest\t2_smoke.py`: cumesh OK, nvdiffrast OK (cuda raster 1 tri -> 512 px), raw .pyd of
  flex_gemm.kernels.cuda / o_voxel._C / cumesh._C all load.
### Blockers (exact)
1. `import flex_gemm` / `import o_voxel` -> `ModuleNotFoundError: No module named 'triton'`. FlexGEMM's sparse conv
   kernels are Triton; PyPI `triton` 3.8.0 has no Windows wheel, pytorch.org index has none either. Only community
   `triton-windows` exists (not an official source -> not installed). Needs Azad's call (or run under WSL/Linux).
2. Attention: xformers 0.0.35 win wheel has no sm_120 kernels ("requires device with capability <= (9, 0) ... (12, 0)
   too new"; fa2 "operator wasn't built"); flash-attn is sdist-only. TRELLIS.2 sparse attention supports only
   xformers/flash_attn/flash_attn_3 -> would need a small patch to use torch SDPA.
3. Weights: microsoft/TRELLIS.2-4B pipeline.json needs `facebook/dinov3-vitl16-pretrain-lvd1689m` (gated: HTTP 401,
   no HF token on this box) and `briaai/RMBG-2.0` (gated; avoidable since ref_rgba.png has alpha). Requires Azad to
   accept the DINOv3 licence on HF and provide a token.
No E:\gen3d\t2\wolf output produced.
