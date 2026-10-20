import os, sys, numpy as np, types
from PIL import Image
sys.path.insert(0, r'E:\gen3d\Hunyuan3D-2')
from hy3dgen.texgen.utils.dehighlight_utils import Light_Shadow_Remover
REFS = dict(wolf=r'E:\gen3d\r8\wolf\ref_rgba.png', crocodile=r'E:\gen3d\r8\crocodile\ref_rgba.png',
            eagle=r'E:\gen3d\r8\eagle\ref_rgba.png', frog=r'E:\gen3d\r8\frog\ref_rgba.png')
for a, k in dict(horse=5, elephant=9, giraffe=3, shark=3, tortoise=3, kangaroo=4).items():
    REFS[a] = rf'E:\gen3d\r9\{a}\ref_c{k}.png'
cfg = types.SimpleNamespace(device='cuda', light_remover_ckpt_path=r'E:\gen3d\hf\hub\models--tencent--Hunyuan3D-2\snapshots\9cd649ba6913f7a852e3286bad86bfa9a2d83dcf\hunyuan3d-delight-v2-0')
names = sys.argv[1].split(',') if len(sys.argv) > 1 else list(REFS)
m = Light_Shadow_Remover(cfg)
for a in names:
    im = Image.open(REFS[a]); print(a, im.mode, im.size)
    if im.mode != 'RGBA':
        rgb = np.array(im.convert('RGB')); al = (rgb.min(-1) < 245).astype(np.uint8) * 255
        im = Image.fromarray(np.dstack([rgb, al]))
    alpha = im.getchannel('A').resize((512, 512))
    out = m(im)  # RGB on white, 512
    Image.fromarray(np.dstack([np.array(out), np.array(alpha)])).save(rf'E:\gen3d\tex12\_refs\{a}_delit.png')
    w = Image.new('RGB', (1024, 512), 'white'); src = Image.new('RGB', im.size, 'white'); src.paste(im, mask=im.getchannel('A'))
    w.paste(src.resize((512, 512)), (0, 0)); w.paste(out, (512, 0)); w.save(rf'E:\gen3d\tex12\_refs\{a}_cmp.png')
