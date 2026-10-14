# gen3d setup log (Git Bash)
```
mkdir -p /e/gen3d && cd /e/gen3d
py -3.12 -m venv venv
./venv/Scripts/python -m pip install --upgrade pip
./venv/Scripts/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128   # -> torch 2.11.0+cu128
./venv/Scripts/python -c "import torch;print(torch.cuda.is_available());a=torch.randn(4096,4096,device='cuda');print((a@a).sum())"
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2
./venv/Scripts/pip install diffusers einops opencv-python numpy transformers omegaconf tqdm trimesh pymeshlab pygltflib xatlas accelerate sentencepiece protobuf ninja pybind11
cd Hunyuan3D-2 && ../venv/Scripts/pip install -e .
```
Skipped: gradio/fastapi/uvicorn (demo only), rembg+onnxruntime (its u2net weights download from a non-approved
GitHub account) -> make.py does white-background flood-fill matting instead. Texture CUDA extensions
(custom_rasterizer, differentiable_renderer) not built: shape only.

Models (auto-downloaded to HF_HOME=E:\gen3d\hf):
- T2I: Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled (repo's own hy3dgen/text2image.py)
- Shape: tencent/Hunyuan3D-2, subfolder hunyuan3d-dit-v2-0 (+ its VAE)

Run:
```
cd /e/gen3d && HF_HOME=E:/gen3d/hf ./venv/Scripts/python make.py "<prompt>" <out_dir> [seed]
```

## Version pins required (fixes)
- transformers 5.x renamed Dinov2 weights -> shape conditioner load_state_dict fails. Fix: `pip install transformers==4.48.3`
- then diffusers (latest) needs newer huggingface_hub -> `pip uninstall -y gradio gradio-client; pip install diffusers==0.32.2 "huggingface-hub<1"`
- Final working: torch 2.11.0+cu128, transformers 4.48.3, diffusers 0.32.2, hy3dgen 2.0.2 (editable)

## Test (wolf, seed 0) 2026-10-13
t2i load 12.5s, t2i 8.9s, shape load 13.1s, shape 20.0s (50 steps, octree 380). Peak VRAM t2i 9.6 GiB, shape 5.6 GiB.
737,654 tris / 368,817 verts. HF cache ~35 GB (whole tencent/Hunyuan3D-2 repo snapshot).
