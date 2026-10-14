import os, sys, numpy as np
sys.path[:0] = [r'E:\gen3d', r'E:\gen3d\Hunyuan3D-2']; os.chdir(r'E:\gen3d')
from PIL import Image
from refs import A, STY
from mask8 import remove_bg8
LIGHT = ", flat even soft studio lighting, no shadows, no specular highlights, high detail natural fur and skin texture, realistic natural colouring"
PICK = dict(wolf=3, kangaroo=4, tortoise=3, horse=5, elephant=9, giraffe=3, crocodile=4, eagle=3, shark=3, frog=3)
OLD = lambda a: rf'E:\gen3d\r8\{a}\ref_rgba.png' if a in ('wolf', 'crocodile', 'eagle', 'frog') else rf'E:\gen3d\r9\{a}\ref_c{PICK[a]}.png'
def sil(im):
    a = np.array(im.getchannel('A').resize((256, 256))) > 127
    ys, xs = np.nonzero(a); a = a[ys.min():ys.max()+1, xs.min():xs.max()+1]   # bbox-normalise
    return np.array(Image.fromarray(a.astype(np.uint8) * 255).resize((128, 128))) > 127
from hy3dgen.text2image import HunyuanDiTPipeline
t2i = HunyuanDiTPipeline("Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled")
for a in sys.argv[1].split(','):
    k = PICK[a]; key = 'eagle (perched)' if a == 'eagle' else a
    if k >= 6: print(a, 'pick was a FLUX candidate; skip'); continue
    p = "flat even soft studio lighting, no shadows, no highlights, high detail natural fur and skin texture, realistic natural colouring, " + f"{A[key][k % 2]}, {STY[k % 3]}" + ", single creature, full body, side three-quarter view, isolated on pure white background, no ground, no floor, no base, no text"
    s0 = sil(Image.open(OLD(a)).convert('RGBA')); best = None
    for seed in [100 + k, 1, 2, 3, 4, 5]:
        rgba = remove_bg8(t2i(p, seed=seed)); s1 = sil(rgba)
        iou = (s0 & s1).sum() / (s0 | s1).sum(); print(a, seed, f'IoU {iou:.3f}', flush=True)
        rgba.save(rf'E:\gen3d\tex12\_refs\{a}_new_s{seed}.png')
        if best is None or iou > best[0]: best = (iou, seed, rgba)
    best[2].save(rf'E:\gen3d\tex12\_refs\{a}_new.png'); print('BEST', a, best[1], f'{best[0]:.3f}', flush=True)
