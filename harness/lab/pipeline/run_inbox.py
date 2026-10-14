"""run_inbox.py - reference images -> finished creature asset, by calling the existing stage scripts.

  python run_inbox.py <animal> [--seeds 0,1] [--lowvram]            # generate + clean + render candidates
  python run_inbox.py <animal> --pick <candidate>                   # + texture, QuadriFlow, rig, assets

Input : E:/gen3d/inbox/<animal>/hero.png (+ optional side.png, front.png, back.png)
Work  : E:/gen3d/inbox/<animal>/work/   (masks, raw/clean candidates, sheets, logs, timings.json)
Output: E:/gen3d/assets/<animal>/{hi.obj,textured.glb,lp_1500.obj,lp_5000.obj,rigged.glb,sheet.png,wire.png}
See INBOX.md.
"""
import argparse, json, os, re, shutil, subprocess, sys, time

G = 'E:/gen3d'
LAB = 'E:/Github/anyCreature/harness/lab'
VENV = f'{G}/venv/Scripts/python.exe'        # torch cu128, hunyuan, pymeshlab, trimesh, scipy
VENV_LP = f'{G}/venv_lp/Scripts/python.exe'  # pyquadriflow
SYS_PY = sys.executable                      # system python: render.py / wire.py (numpy+PIL)
NODE = 'node'
CUDA13_DLL = f'{G}/cuda134/nvidia/cu13/bin/x86_64'   # paint21.py also add_dll_directory()s this
NO_RIG = {'eagle', 'shark', 'frog', 'kangaroo'}      # non-quadrupeds: skeleton spec is quadruped-only
VIEWS = ['hero', 'side', 'front', 'back']
LV = f'{G}/lowvram/tests'                    # measured 8 GB stage code (paint.py, rigrun.py); shape/mv chain is inlined below

# prepended to every GPU stage script: optional VRAM cap (VRAM_CAP env, GiB) + PEAK line at exit (parsed from the log)
CAP_PREFIX = """import os as _o, atexit as _ae, time as _tm
import torch as _t
_CAP = float(_o.environ.get('VRAM_CAP', '0') or 0); _T0 = _tm.time()
if _CAP > 0 and _t.cuda.is_available():
    _t.cuda.set_per_process_memory_fraction(min(1.0, _CAP / (_t.cuda.get_device_properties(0).total_memory / 2**30)))
def _peak(tag='exit'):
    if _t.cuda.is_available():
        print(f'PEAK {tag} cap={_CAP} alloc {_t.cuda.max_memory_allocated()/2**30:.2f} GiB reserved {_t.cuda.max_memory_reserved()/2**30:.2f} GiB t {_tm.time()-_T0:.0f}s', flush=True)
_ae.register(_peak, 'exit')
"""

# low-VRAM shape: load on CPU, accelerate cpu_offload_with_hook chain conditioner -> DiT -> VAE (bit-identical mesh, 6.45 GiB peak)
OFFLOAD_CHAIN = """{v} = {ctor}
from accelerate import cpu_offload_with_hook as _cow
_h = None
for _n in ('conditioner', 'model', 'vae'):
    _, _h = _cow(getattr({v}, _n), 'cuda', prev_module_hook=_h)
{v}.device = torch.device('cuda')
"""


def ts(): return time.strftime('%H:%M:%S')


class Ctx:
    def __init__(s, a):
        s.a = a; s.an = a.animal
        s.inbox = f'{G}/inbox/{s.an}'; s.work = f'{s.inbox}/work'
        s.stage = f'{s.work}/_stage'; s.logs = f'{s.work}/logs'
        s.out = f'{G}/assets/{s.an}'
        for d in (s.work, s.stage, s.logs, f'{s.work}/cand', f'{s.work}/sheets'): os.makedirs(d, exist_ok=True)
        s.tfile = f'{s.work}/timings.json'
        s.timings = json.load(open(s.tfile)) if os.path.exists(s.tfile) else {}

    def run(s, name, cmd, cwd=G, env=None, check=True, cpu=False):
        # CUDA-13 DLL dir: paint21.py add_dll_directory()s CUDA13_DLL itself (PATH prepend breaks torch DLL load)
        """run a stage subprocess, log to work/logs/<name>.log, record wall time."""
        e = dict(os.environ); e['PYTHONIOENCODING'] = 'utf-8'
        if env: e.update(env)
        if cpu and s.a.lowvram: e['CUDA_VISIBLE_DEVICES'] = ''      # mask/clean/quadriflow/rig are CPU-only in lowvram mode
        if s.a.vram_cap: e['VRAM_CAP'] = str(s.a.vram_cap)
        if s.a.lowvram or s.a.vram_cap: e['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
        t = time.time(); print(f'[{ts()}] {name}: {" ".join(os.path.basename(str(c)) if i == 0 else str(c) for i, c in enumerate(cmd))[:200]}', flush=True)
        with open(f'{s.logs}/{name}.log', 'w', encoding='utf-8') as lf:
            r = subprocess.run([str(c) for c in cmd], cwd=cwd, env=e, stdout=lf, stderr=subprocess.STDOUT)
        dt = time.time() - t; s.timings[name] = round(dt, 1)
        pk = re.findall(r'^PEAK .*$', open(f'{s.logs}/{name}.log', encoding='utf-8', errors='replace').read(), re.M)
        if pk: s.timings['peak_' + name] = pk[-1]; print(f'[{ts()}]   {pk[-1]}', flush=True)
        json.dump(s.timings, open(s.tfile, 'w'), indent=1)
        print(f'[{ts()}]   -> rc {r.returncode} in {dt:.0f}s', flush=True)
        if check and r.returncode:
            print(open(f'{s.logs}/{name}.log', encoding='utf-8', errors='replace').read()[-3000:])
            sys.exit(f'stage {name} failed (log: {s.logs}/{name}.log)')
        return r.returncode

    def templated(s, name, src, subs, py, args, gpu=False, **kw):
        """Run an existing stage script with a few path/seed literals swapped (internals untouched)."""
        txt = open(src, encoding='utf-8').read()
        for old, new in subs:
            if old not in txt: sys.exit(f'template drift: {old!r} not found in {src}')
            txt = txt.replace(old, new)
        if gpu: txt = CAP_PREFIX + txt
        p = f'{s.stage}/{name}.py'
        open(p, 'w', encoding='utf-8').write(txt)
        return s.run(name, [py, p] + list(args), cpu=not gpu, **kw)


# ---------------------------------------------------------------- masking (runs in venv via --_mask)
def mask_views(an):
    sys.path.insert(0, G)
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    from mask8 import remove_bg8
    inbox = f'{G}/inbox/{an}'; work = f'{inbox}/work'
    def lcc(r):
        a = np.array(r); lab, n = ndimage.label(a[..., 3] > 128)
        if n > 1:
            sz = ndimage.sum(np.ones(lab.shape), lab, range(1, n + 1)); a[..., 3][lab != 1 + int(np.argmax(sz))] = 0
        return Image.fromarray(a)
    for v in VIEWS:
        p = f'{inbox}/{v}.png'
        if not os.path.exists(p): continue
        im = Image.open(p)
        if im.mode in ('RGBA', 'LA') and np.asarray(im.convert('RGBA'))[..., 3].min() < 250:
            r = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); r0 = r   # real alpha: keep
            s = max(r.size); c = Image.new('RGBA', (s, s), (255, 255, 255, 0)); c.paste(r, ((s - r.width) // 2, (s - r.height) // 2))
            r = c.resize((1024, 1024), Image.LANCZOS)
        else:
            im = im.convert('RGB'); s = max(im.size)
            c = Image.new('RGB', (s, s), 'white'); c.paste(im, ((s - im.width) // 2, (s - im.height) // 2))
            r = remove_bg8(c.resize((1024, 1024), Image.LANCZOS))
        if v != 'hero': r = lcc(r)
        out = {'hero': 'ref_rgba'}.get(v, v)
        r.save(f'{work}/{out}.png'); print('masked', v, '->', out, flush=True)
        if v == 'side': r.transpose(Image.FLIP_LEFT_RIGHT).save(f'{work}/side_mirror.png')
        bgc = Image.new('RGBA', r.size, (255, 0, 255, 255)); bgc.alpha_composite(r)
        bgc.convert('RGB').resize((384, 384)).save(f'{work}/mask_{out}.png')


# ---------------------------------------------------------------- stages
def stage_generate(c):
    a = c.a; W = c.work
    seeds = [int(x) for x in a.seeds.split(',')]
    have_mv = os.path.exists(f'{c.inbox}/side.png')
    c.run('mask', [VENV, os.path.abspath(__file__), '--_mask', c.an], cpu=True)
    if a.lowvram: print('--lowvram: shape = accelerate offload chain (conditioner->DiT->VAE); CPU-only mask/clean/quadriflow/rig')
    cands = []
    seed_t = ', '.join(map(str, seeds))
    # Hunyuan3D-2.1, single image (hero)
    if not all(os.path.exists(f'{W}/raw21_s{s}.obj') for s in seeds) or a.force:
        subs = [('seeds = [0, 1]', f'seeds = [{seed_t}]'), ('r8/{an}', W)]
        if a.lowvram:
            old = 'shp = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1")\n'
            subs.append((old, OFFLOAD_CHAIN.format(v='shp', ctor='Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1", device="cpu")')))
        c.templated('gen21', f'{G}/gen21.py', subs, VENV, [c.an], gpu=True)
    for s in seeds: cands.append(dict(name=f'h21_s{s}', raw=f'{W}/raw21_s{s}.obj', method='hunyuan2.1-single', seed=s))
    # Hunyuan3D-2mv, multi-view
    if have_mv:
        var = ['af', 'bf'] if os.path.exists(f'{c.inbox}/front.png') else ['a', 'b']
        if not all(os.path.exists(f'{W}/raw_{v}_s{s}.obj') for v in var for s in seeds) or a.force:
            subs = [('D = "E:/gen3d/mv"', f'D = "{c.inbox}"'), ('for s in (0, 1):', f'for s in ({seed_t},):')]
            if a.lowvram:   # same offload chain as 2.1 (untested: no 2mv inbox run yet); num_chunks 20000 -> 8000
                old = "p = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2mv', subfolder='hunyuan3d-dit-v2-mv', variant='fp16')\n"
                subs += [(old, OFFLOAD_CHAIN.format(v='p', ctor="Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2mv', subfolder='hunyuan3d-dit-v2-mv', variant='fp16', device='cpu')")),
                         ('num_chunks=20000', 'num_chunks=8000')]
            c.templated('gen_mv', f'{G}/mv/gen_mv.py', subs, VENV, [f'work:{v}' for v in var], gpu=True)
        for v in var:
            for s in seeds: cands.append(dict(name=f'mv{v}_s{s}', raw=f'{W}/raw_{v}_s{s}.obj', method=f'hunyuan2mv-{v}', seed=s))
    else:
        print('no side.png -> single-view path only')
    if os.path.exists(f'{c.inbox}/back.png'): print('NOTE: back.png is masked but gen_mv.py has no back slot; unused by 2mv.')
    # clean8 + render sheets
    for k in cands:
        k['clean'] = f'{W}/cand/{k["name"]}.obj'; k['sheet'] = f'{W}/sheets/{k["name"]}.png'
        if not os.path.exists(k['raw']): k['error'] = 'raw missing'; continue
        if not os.path.exists(k['clean']) or a.force:
            c.run(f'clean8_{k["name"]}', [VENV, f'{G}/clean8.py', k['raw'], k['clean']], cpu=True)
        c.run(f'render_{k["name"]}', [SYS_PY, f'{LAB}/render.py', k['clean'], k['sheet']], cwd=LAB)
    contact_sheet(c, [k for k in cands if 'error' not in k])
    json.dump(dict(animal=c.an, views=[v for v in VIEWS if os.path.exists(f'{c.inbox}/{v}.png')],
                   contact_sheet=f'{W}/contact_sheet.png', candidates=cands, chosen=None), open(f'{W}/candidates.json', 'w'), indent=1)
    print(f'[{ts()}] candidates.json written ({len(cands)} candidates); contact sheet {W}/contact_sheet.png')


def contact_sheet(c, cands):
    from PIL import Image, ImageDraw
    tiles = []
    for k in cands:
        im = Image.open(k['sheet']).convert('RGB').resize((768, 512)); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 200, 22), fill=(0, 0, 0)); d.text((6, 5), k['name'], fill=(255, 255, 255)); tiles.append(im)
    cols = 2; rows = (len(tiles) + cols - 1) // cols
    out = Image.new('RGB', (768 * cols, 512 * rows), 'white')
    for i, t in enumerate(tiles): out.paste(t, ((i % cols) * 768, (i // cols) * 512))
    out.save(f'{c.work}/contact_sheet.png')


def stage_finish(c, pick):
    W = c.work; cj = json.load(open(f'{W}/candidates.json'))
    ck = next((k for k in cj['candidates'] if k['name'] == pick), None)
    if not ck or 'error' in ck: sys.exit(f'unknown/failed candidate {pick!r}; have {[k["name"] for k in cj["candidates"]]}')
    cj['chosen'] = pick; json.dump(cj, open(f'{W}/candidates.json', 'w'), indent=1)
    O = c.out; os.makedirs(O, exist_ok=True)
    hi = f'{O}/hi.obj'; shutil.copy(ck['clean'], hi)
    c.run('render_hi', [SYS_PY, f'{LAB}/render.py', hi, f'{O}/sheet.png'], cwd=LAB)
    # texture: Hunyuan Paint 2.1 + RealESRGAN (paint13.py), hero as reference
    td = f'{W}/tex'; shutil.rmtree(f'{td}/{c.an}', ignore_errors=True)
    hero = f'{W}/ref_rgba.png'
    if c.a.lowvram:   # lowvram/tests/paint.py: 6 views, UNet/VAE on GPU only during diffusion, DINOv2/CLIP staged, FF chunking, VAE tiling, ESRGAN tile 256
        c.templated('paint13', f'{LV}/paint.py',
                    [("sys.path.insert(0, 'E:/gen3d/lowvram'); import cap", 'import sys'), ("cap.peak('paint')", "_peak('paint')")],
                    VENV, [hi, hero, f'{td}/{c.an}', 'v=6', 'off=1', 'tile=256', 'vt=1', 'dil=0', 'ds=1'], gpu=True, check=False)
    else:
        c.templated('paint13', f'{G}/tex13/paint13.py',
                    [("rf'E:\\gen3d\\r9pick\\{a}.obj'", "os.environ['PAINT_MESH']"),
                     ('import importlib, utils.image_super_utils as isu',
                      "ORIG[jobs[0].split(':')[0]] = os.environ['PAINT_REF']\nimport importlib, utils.image_super_utils as isu")],
                    VENV, [td, f'{c.an}:ref=orig'], env=dict(PAINT_MESH=hi, PAINT_REF=hero), gpu=True, check=False)
    tg = f'{td}/{c.an}/textured.glb'
    if os.path.exists(tg): shutil.copy(tg, f'{O}/textured.glb')
    else: print('WARNING: texture stage produced no textured.glb (see logs/paint13.log)')
    # low-poly: QuadriFlow 1500 & 5000
    lpin = f'{W}/lp_in/inbox_{c.an}'; os.makedirs(lpin, exist_ok=True); shutil.copy(hi, f'{lpin}/final.obj')
    c.run('quadriflow', [VENV_LP, f'{G}/lowpoly/run_classic.py', 'quadriflow', '--in-root', f'{W}/lp_in', '--out-root', f'{W}/lp',
                         '--animals', f'inbox_{c.an}', '--budgets', '1500,5000'], cwd=f'{G}/lowpoly', cpu=True)
    for b in (1500, 5000):
        src = f'{W}/lp/quadriflow/inbox_{c.an}_{b}.obj'
        if os.path.exists(src): shutil.copy(src, f'{O}/lp_{b}.obj')
        else: print(f'WARNING: missing lp_{b}')
    if os.path.exists(f'{O}/lp_5000.obj'):
        c.run('wire', [SYS_PY, f'{LAB}/wire.py', f'{O}/lp_5000.obj', f'{O}/wire.png'], cwd=LAB)
    # rig (quadrupeds only)
    rigged = False
    if c.an in NO_RIG or c.a.no_rig:
        print(f'rig skipped: {c.an} is not a quadruped (quadruped-only skeleton).')
    elif os.path.exists(f'{O}/lp_5000.obj'):
        nm = f'inbox_{c.an}'
        # always rigrun.py's leak-proof voxel fill around rig.voxelize (rig.py itself untouched)
        rc = c.templated('rig', f'{LV}/rigrun.py',
                         [("a, src, here = sys.argv[1:4]; rig.SRC = src; rig.HERE = here; rig.main(a)",
                           f"a = sys.argv[1]; rig.SRC = '{W}/lp/quadriflow/%s_5000.obj'; rig.HERE = '{G}/rig'; rig.main(a)")],
                         VENV, [nm], cwd=f'{G}/rig', check=False)
        if rc == 0:
            rc = c.run('rig_export', [NODE, f'{G}/rig/export_glb.js', f'{G}/rig/out/{nm}_build.json', f'{O}/rigged.glb'], cwd=f'{G}/rig', check=False, cpu=True)
            rigged = rc == 0
        if not rigged: print('WARNING: rig failed (see logs/rig.log, logs/rig_export.log)')
    prev = f'{td}/{c.an}/preview.png'
    if os.path.exists(prev): shutil.copy(prev, f'{O}/textured_preview.png')
    files = sorted(os.listdir(O))
    json.dump(dict(animal=c.an, chosen=pick, files=files, timings=c.timings), open(f'{O}/manifest.json', 'w'), indent=1)
    print('peaks:', {k: v for k, v in c.timings.items() if k.startswith('peak_')})
    print(f'[{ts()}] DONE assets in {O}: {files}')


def main():
    if len(sys.argv) > 2 and sys.argv[1] == '--_mask': return mask_views(sys.argv[2])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('animal'); ap.add_argument('--seeds', default='0,1')
    ap.add_argument('--lowvram', action='store_true', help='8 GB-class settings: offloaded shape, 6-view low-mem paint, CPU-only mask/clean/quadriflow/rig')
    ap.add_argument('--vram-cap', type=float, default=0, help='GiB; torch per-process memory cap in every GPU stage (verify --lowvram on a big card)')
    ap.add_argument('--pick', help='candidate name from candidates.json: texture + lowpoly + rig + assets')
    ap.add_argument('--force', action='store_true', help='regenerate even if outputs exist')
    ap.add_argument('--no-rig', action='store_true')
    a = ap.parse_args(); c = Ctx(a)
    if not os.path.exists(f'{c.inbox}/hero.png'): sys.exit(f'missing {c.inbox}/hero.png')
    if not os.path.exists(f'{c.work}/candidates.json') or a.force or not a.pick: stage_generate(c)
    if a.pick: stage_finish(c, a.pick)


if __name__ == '__main__':
    main()
