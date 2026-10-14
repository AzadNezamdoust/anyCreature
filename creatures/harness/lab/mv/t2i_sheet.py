import os, sys
os.environ.setdefault("HF_HOME", r"E:\gen3d\hf")
sys.path.insert(0, r"E:\gen3d\Hunyuan3D-2")
import torch
from hy3dgen.text2image import HunyuanDiTPipeline
t = HunyuanDiTPipeline("Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled")
desc = dict(wolf="a gray wolf", horse="a brown horse", eagle="a bald eagle with spread wings standing",
            frog="a green frog")
for an in sys.argv[1].split(","):
    os.makedirs(f"E:/gen3d/mv/{an}", exist_ok=True)
    p = (f"character turnaround sheet of {desc[an]}: side view, front view, back view, same animal, same pose, "
         "three views in a row, full body, white background, 3D render")
    for s in range(int(sys.argv[2]) if len(sys.argv) > 2 else 4):
        torch.manual_seed(s)
        im = t.pipe(prompt=p + t.pos_txt, negative_prompt=t.neg_txt, num_inference_steps=25, pag_scale=1.3,
                    width=1536, height=768, generator=torch.Generator("cuda").manual_seed(s), return_dict=False)[0][0]
        im.save(f"E:/gen3d/mv/{an}/sheet_s{s}.png"); print(an, s, flush=True)
