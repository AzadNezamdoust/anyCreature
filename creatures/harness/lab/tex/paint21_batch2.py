import sys, re, time, traceback, runpy
src = open(r'E:\gen3d\paint21.py').read()
head = src.split("p = pipe(")[0]
pick = dict(crocodile=4, eagle=3, frog=3)
sys.argv = ['paint21.py', 'x', 'x', 'x']
g = {'__name__': '__main__'}
exec(compile(head, 'paint21_head', 'exec'), g)
import os
for a, k in pick.items():
    t = time.time(); d = rf'E:\gen3d\tex\{a}'; os.makedirs(d, exist_ok=True)
    try:
        g['pipe'](mesh_path=rf'E:\gen3d\r9pick\{a}.obj', image_path=rf'E:\gen3d\r8\{a}\ref_rgba.png', output_mesh_path=rf'{d}\textured.obj', use_remesh=False)
        sys.argv = ['g', d]; runpy.run_path(r'E:\gen3d\glb_preview21.py', run_name='__main__')
        print(f'RESULT {a} ok {time.time()-t:.0f}s', flush=True)
    except Exception:
        traceback.print_exc(); print(f'RESULT {a} FAIL {time.time()-t:.0f}s', flush=True)

