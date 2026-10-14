"""MeshAnything V2 (official repo, attention patched flash_attention_2 -> eager).
  E:/gen3d/venv_lp/Scripts/python run_meshanything.py [--in-root E:/gen3d/r8]
        [--out-root E:/gen3d/lowpoly] [--animals ...] [--seeds 0,1,2]
Single budget: the model emits <=1600 tris (only the ~1500 budget applies).
Conditions on 8192-pt point cloud+normals sampled from the normalized input.
Runs every seed, keeps the one with the most faces (truncation = failure mode).
Output <out-root>/meshanything/<animal>_1500.obj"""
import argparse, glob, json, os, shutil, subprocess, sys, time
import numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp_common as C
REPO = os.path.join(HERE, 'repos', 'MeshAnythingV2')
PY = sys.executable

ap = argparse.ArgumentParser()
ap.add_argument('--in-root', default='E:/gen3d/r8')
ap.add_argument('--out-root', default='E:/gen3d/lowpoly')
ap.add_argument('--animals', default=','.join(C.ANIMALS))
ap.add_argument('--seeds', default='0')
ap.add_argument('--no-mc', dest='mc', action='store_false',
                help='skip the official marching-cubes preprocess (worse: holes/slivers)')
ap.add_argument('--prec', default='no', help="no (fp32) | bf16; fp16 overflows")
ap.add_argument('--tag', default='meshanything')
a = ap.parse_args()
od = os.path.join(a.out_root, a.tag); os.makedirs(od, exist_ok=True)
work = os.path.join(od, '_work'); pcd = os.path.join(work, 'pc')
shutil.rmtree(work, ignore_errors=True); os.makedirs(pcd)
for an in a.animals.split(','):
    m = C.load_tri(os.path.join(a.in_root, an, 'final.obj'))
    m.vertices = C.normalize(m.vertices)
    if a.mc:
        m.export(os.path.join(pcd, an + '.obj'))
    else:
        pts, fi = trimesh.sample.sample_surface(m, 50000, seed=0)
        np.save(os.path.join(pcd, an + '.npy'),
                np.concatenate([pts, m.face_normals[fi]], 1).astype(np.float32))
best, t0 = {}, time.time()
env = dict(os.environ, LP_PREC=a.prec)
for s in a.seeds.split(','):
    sd = os.path.join(work, 's' + s)
    extra = ['--input_type', 'mesh', '--mc'] if a.mc else ['--input_type', 'pc_normal']
    subprocess.run([PY, 'main.py', '--input_dir', pcd, '--out_dir', sd,
                    '--seed', s] + extra, cwd=REPO, check=True, env=env)
    for f in glob.glob(os.path.join(sd, '*', '*_gen.obj')):
        an = os.path.basename(f)[:-8]
        n = len(trimesh.load(f, force='mesh').faces)
        if n > best.get(an, (0, ''))[0]:
            best[an] = (n, f)
per = (time.time() - t0) / max(len(best), 1)
for an, (n, f) in best.items():
    m = trimesh.load(f, force='mesh')
    out = os.path.join(od, f'{an}_1500.obj')
    C.write_obj_polys(out, C.normalize(m.vertices), m.faces.tolist())
    rec = dict(animal=an, budget=1500, method=a.tag, ok=True,
               sec=round(per, 1), **C.stats(m.faces.tolist()))
    print(json.dumps(rec))
    open(os.path.join(od, 'log.jsonl'), 'a').write(json.dumps(rec) + '\n')
