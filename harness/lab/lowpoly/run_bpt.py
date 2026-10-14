"""BPT (Tencent-Hunyuan/bpt, weights HF whaohan/bpt, Hunyuan community license).
  E:/gen3d/venv_lp/Scripts/python run_bpt.py [--in-root E:/gen3d/r8]
        [--out-root E:/gen3d/lowpoly] [--animals ...] [--temp 0.5]
No face-count control: the model decides (up to ~8k). The raw result is saved as
<animal>_raw.obj; <animal>_1500/_5000.obj are QEM-decimated from it only when it
exceeds the budget (otherwise copied; log says budget_hit false)."""
import argparse, glob, json, os, shutil, subprocess, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp_common as C
REPO = os.path.join(HERE, 'repos', 'bpt')

ap = argparse.ArgumentParser()
ap.add_argument('--in-root', default='E:/gen3d/r8')
ap.add_argument('--out-root', default='E:/gen3d/lowpoly')
ap.add_argument('--animals', default=','.join(C.ANIMALS))
ap.add_argument('--temp', default='0.5')
a = ap.parse_args()
od = os.path.join(a.out_root, 'bpt'); os.makedirs(od, exist_ok=True)
work = os.path.join(od, '_work'); ind = os.path.join(work, 'in'); outd = os.path.join(work, 'out')
shutil.rmtree(work, ignore_errors=True); os.makedirs(ind); os.makedirs(outd)
for an in a.animals.split(','):
    m = C.load_tri(os.path.join(a.in_root, an, 'final.obj'))
    m.vertices = C.normalize(m.vertices)
    m.export(os.path.join(ind, an + '.obj'))
t0 = time.time()
subprocess.run([sys.executable, 'main.py', '--config', 'config/BPT-open-8k-8-16.yaml',
                '--model_path', 'weights/bpt-8-16-500m.safe.pt', '--input_dir', ind,
                '--input_type', 'mesh', '--output_path', outd, '--batch_size', '1',
                '--temperature', a.temp], cwd=REPO, check=True)
per = (time.time() - t0) / len(a.animals.split(','))
import pymeshlab as ml
for an in a.animals.split(','):
    f = os.path.join(outd, an + '_mesh.obj')
    if not os.path.exists(f):
        continue
    ms = ml.MeshSet(); ms.load_new_mesh(f)
    ms.meshing_remove_duplicate_vertices()
    raw = ms.current_mesh().face_number()
    V = C.normalize(ms.current_mesh().vertex_matrix())
    C.write_obj_polys(os.path.join(od, f'{an}_raw.obj'), V, ms.current_mesh().face_matrix().tolist())
    for b in C.BUDGETS:
        ms2 = ml.MeshSet(); ms2.add_mesh(ml.Mesh(V, ms.current_mesh().face_matrix()))
        if raw > b:
            ms2.meshing_decimation_quadric_edge_collapse(targetfacenum=b, preservenormal=True,
                                                         preserveboundary=True, planarquadric=True)
        mm = ms2.current_mesh(); P = mm.face_matrix().tolist()
        C.write_obj_polys(os.path.join(od, f'{an}_{b}.obj'), C.normalize(mm.vertex_matrix()), P)
        rec = dict(animal=an, budget=b, method='bpt', ok=True, raw_faces=raw,
                   decimated=raw > b, sec=round(per, 1), **C.stats(P))
        print(json.dumps(rec))
        open(os.path.join(od, 'log.jsonl'), 'a').write(json.dumps(rec) + '\n')
