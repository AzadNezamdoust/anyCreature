"""Normal + albedo bake for game LODs (run_inbox.py --bake-normals).
usage: bake_lods.py <hi textured.obj> <out dir> <lod.obj>[:res] ... [--detail] [--vram-cap 7.0] [--strength 1.5] [--head x,y,z]
Per LOD -> <out>/lod<name>/{lod.obj (UVs), albedo.png, n_tan.png, n_tan_detail.png}; sheets in <out>/compare_{full,head}.png
"""
import os, sys, json, time, subprocess
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
BL = f'{G}/blender/blender-5.2.2-windows-x64/blender.exe'; VPY = f'{G}/venv/Scripts/python.exe'; S = f'{H}/bake_normals_bl.py'

def bl(mode, **a):
    r = subprocess.run([BL, '-b', '--factory-startup', '-P', S, '--', mode, json.dumps(a)], capture_output=True, text=True)
    if r.returncode or 'Traceback' in r.stdout + r.stderr: sys.exit(f'blender {mode} failed:\n{r.stdout[-3000:]}\n{r.stderr[-2000:]}')

def main():
    av = sys.argv[1:]; flag = lambda k, d=None: av[av.index(k) + 1] if k in av else d
    detail = '--detail' in av; cap = flag('--vram-cap', '0'); st = flag('--strength', '1.5')
    head = [float(x) for x in flag('--head', '-0.82,0,0.98').split(',')]
    pos = [x for i, x in enumerate(av) if not x.startswith('--') and (i == 0 or av[i - 1] not in ('--vram-cap', '--strength', '--head'))]
    hi, out, lods = pos[0], pos[1], pos[2:]; os.makedirs(out, exist_ok=True); T = {}
    if detail:   # image -> normal detail (GPU, fp16 Marigold LCM, ~3.8 GiB alloc)
        t = time.time(); vd = f'{out}/views'
        bl('views', hi=hi, out=vd, n=12, res=768)
        bl('exr2npy', files=[f'{vd}/{f}' for f in os.listdir(vd) if f.endswith('.exr')])
        subprocess.run([VPY, f'{H}/detail_normals.py', 'marigold', vd, '--vram-cap', cap], check=True)
        T['detail_views_marigold'] = round(time.time() - t, 1); T['marigold'] = json.load(open(f'{vd}/marigold.json'))
    for spec in lods:
        p, res = (spec.rsplit(':', 1) + ['2048'])[:2] if spec.rsplit(':', 1)[-1].isdigit() else (spec, '2048')
        name = os.path.splitext(os.path.basename(p))[0].split('_')[-1]; ld = f'{out}/lod{name}'; os.makedirs(ld, exist_ok=True)
        t = time.time(); bl('bake', hi=hi, lp=p, out=ld, res=int(res), ext=0.03, ray=0.06)
        nrm = ['', f'{ld}/n_tan.png']; lab = ['none', 'baked']
        if detail:
            bl('exr2npy', files=[f'{ld}/pos.exr', f'{ld}/n_obj.exr'])
            subprocess.run([VPY, f'{H}/detail_normals.py', 'project', f'{out}/views', ld, st], check=True)
            bl('npy2exr', npy=f'{ld}/n_obj_detail.npy', out=f'{ld}/n_obj_detail.exr')
            bl('retan', lod=f'{ld}/lod.blend', nobj=f'{ld}/n_obj_detail.exr', out=f'{ld}/n_tan_detail.png', res=int(res))
            nrm.append(f'{ld}/n_tan_detail.png'); lab.append('detail')
        T[f'bake_{name}'] = round(time.time() - t, 1)
        os.makedirs(f'{out}/sheets', exist_ok=True)
        bl('render', lod=f'{ld}/lod.blend', albedo=f'{ld}/albedo.png', normals=nrm, labels=lab, out=f'{out}/sheets/lod{name}',
           head=head, dir=[-0.5, -1, 0.3], hdir=[-1, -0.9, 0.25], key=[-0.8, -0.5, 0.7])
    if detail: subprocess.run([VPY, f'{H}/sheet.py', out])
    json.dump(T, open(f'{out}/bake_timings.json', 'w'), indent=1); print(json.dumps(T))

if __name__ == '__main__': main()
