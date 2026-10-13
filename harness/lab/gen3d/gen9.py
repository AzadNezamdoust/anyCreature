from concurrent.futures import ThreadPoolExecutor
import os, sys, time, glob, shutil, subprocess, torch
sys.path.insert(0, r"E:\gen3d\Hunyuan3D-2.1\hy3dshape")
from PIL import Image, ImageDraw
from mask8 import remove_bg8
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from hy3dshape.postprocessors import FloaterRemover, DegenerateFaceRemover
picks = dict(crocodile=4, eagle=3, elephant=8, frog=3, giraffe=2, horse=3, kangaroo=1, shark=2, tortoise=1, wolf=3)
ans = list(picks); seeds = [0, 1]; t0 = time.time(); fails = []; procs = []
def log(*a): print(time.strftime('%X'), *a, flush=True)
SYS = r"C:\Windows\py.exe"
def post(raw, o):
    r1 = subprocess.run(["E:/gen3d/venv/Scripts/python.exe", "clean8.py", raw, o], capture_output=True, text=True)
    r = r1
    if r1.returncode == 0: r = subprocess.run(["python", "E:/Github/anyCreature/harness/lab/render.py", o, o[:-4] + ".png"], capture_output=True, text=True)
    log("clean/render", o, "rc", r.returncode, (r.stdout + r.stderr).strip()[-200:])
    if r.returncode: fails.append(o)
    return r.returncode
shp = None; ex = ThreadPoolExecutor(5); futs = []
for an in ans:
    d = f"r9/{an}"; os.makedirs(d, exist_ok=True)
    cands = sorted(glob.glob(f"r7/{an}/c[0-9]*.png"), key=lambda p: int(os.path.basename(p)[1:-4]))
    log(an, len(cands), "candidates")
    for p in cands:
        k = int(os.path.basename(p)[1:-4]); rgba = None
        for s in seeds:
            o = f"{d}/c{k}_s{s}.obj"
            if os.path.exists(o[:-4] + ".png"): continue
            if k == picks[an] and os.path.exists(f"r8/{an}/c21_s{s}.png"):
                shutil.copy(f"r8/{an}/c21_s{s}.obj", o); shutil.copy(f"r8/{an}/c21_s{s}.png", o[:-4] + ".png"); log("copied", o); continue
            try:
                if shp is None: shp = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1")
                if rgba is None:
                    rgba = remove_bg8(Image.open(p)); rgba.save(f"{d}/ref_c{k}.png")
                raw = f"{d}/raw_c{k}_s{s}.obj"
                if os.path.exists(raw): futs.append(ex.submit(post, raw, o)); continue
                m = shp(image=rgba, num_inference_steps=50, octree_resolution=380, generator=torch.manual_seed(s))[0]
                m = DegenerateFaceRemover()(FloaterRemover()(m))
                raw = f"{d}/raw_c{k}_s{s}.obj"; m.export(raw); log("gen", an, k, s, len(m.faces))
                futs.append(ex.submit(post, raw, o))
            except Exception as e:
                log("FAIL", an, k, s, repr(e)); fails.append(o); torch.cuda.empty_cache()
    for f in futs: f.result()
    futs.clear()
    pngs = sorted(glob.glob(f"{d}/c[0-9]*_s[0-9].png"))
    if pngs:
        ims = [Image.open(q).convert("RGB") for q in pngs]
        cols = 2 if ims[0].width > 1000 else 3; tw = min(1200, 2480 // cols) ; th = int(ims[0].height * tw / ims[0].width)
        rows = (len(ims) + cols - 1) // cols; sh = Image.new("RGB", (cols * tw, rows * th), "white")
        for i, (im, q) in enumerate(zip(ims, pngs)):
            t = im.resize((tw, th), Image.LANCZOS); dr = ImageDraw.Draw(t); dr.rectangle([0, 0, 150, 22], fill="white")
            dr.text((4, 4), os.path.basename(q)[:-4], fill="black"); sh.paste(t, ((i % cols) * tw, (i // cols) * th))
        sh.save(f"{d}/contact.png")
log("DONE failures:", fails, "runtime s", int(time.time() - t0))
