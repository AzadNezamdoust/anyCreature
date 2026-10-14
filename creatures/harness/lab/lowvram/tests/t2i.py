# t2i.py <mode> <out.png> [res] [steps]  mode: base | offload | seq
import sys, os; sys.path.insert(0, 'E:/gen3d/lowvram'); import cap, time, torch
sys.path.insert(0, 'E:/gen3d'); from refs import prompts
from diffusers import AutoPipelineForText2Image
mode, out = sys.argv[1], sys.argv[2]; res = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
steps = int(sys.argv[4]) if len(sys.argv) > 4 else 25
t = time.time()
pipe = AutoPipelineForText2Image.from_pretrained("Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled",
        torch_dtype=torch.float16, enable_pag=True, pag_applied_layers=["blocks.(16|17|18|19)"])
if mode == 'base': pipe.to('cuda')
elif mode == 'offload': pipe.enable_model_cpu_offload()
else: pipe.enable_sequential_cpu_offload()
pipe.vae.enable_tiling(); pipe.vae.enable_slicing()
print('load', round(time.time()-t), flush=True); t = time.time()
pos = ",白色背景,3D风格,最佳质量"
neg = "文本,特写,裁剪,出框,最差质量,低质量,JPEG伪影,PGLY,重复,病态,残缺,多余的手指,变异的手,画得不好的手,画得不好的脸,变异,畸形,模糊,脱水,糟糕的解剖学,糟糕的比例,多余的肢体,克隆的脸,毁容,恶心的比例,畸形的肢体,缺失的手臂,缺失的腿,额外的手臂,额外的腿,融合的手指,手指太多,长脖子"
p = prompts(sys.argv[5])[int(sys.argv[6])]
im = pipe(prompt=p[:60] + pos, negative_prompt=neg, num_inference_steps=steps, pag_scale=1.3, width=res, height=res,
          generator=torch.Generator('cpu').manual_seed(int(sys.argv[7]))).images[0]
print('gen', round(time.time()-t), flush=True); im.save(out)
