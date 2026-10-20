"""post.py <outdir> : GLB -> raw.obj (+ textured obj copy), clean8 -> E:/gen3d/t2cpp/<animal>/final.obj, render."""
import sys, os, shutil, subprocess, trimesh
src = sys.argv[1]
names = sys.argv[2:] or ["wolf","crocodile","eagle","frog","horse","elephant","giraffe","shark","tortoise","kangaroo"]
for a in names:
    glb = os.path.join(src, a + ".glb")
    if not os.path.exists(glb): print(a, "missing"); continue
    d = f"E:/gen3d/t2cpp/{a}"; os.makedirs(d, exist_ok=True)
    sc = trimesh.load(glb)
    m = sc.dump(concatenate=True) if isinstance(sc, trimesh.Scene) else sc
    m.export(f"{d}/raw.obj")                       # textured obj + mtl + png
    shutil.copy(glb, f"{d}/final.glb")              # trellis.cpp's own textured GLB
    r = subprocess.run([r"E:\gen3d\venv\Scripts\python.exe", "E:/gen3d/clean8.py", f"{d}/raw.obj", f"{d}/final.obj"], capture_output=True, text=True)
    print(a, r.stdout.strip(), r.stderr.strip()[-300:])
    r = subprocess.run(["python", "E:/Github/anyCreature/creatures/harness/lab/render.py", f"{d}/final.obj", f"{d}/final.png"], capture_output=True, text=True)
    print(a, "render", r.returncode, r.stderr.strip()[-300:])

