# r18 driver: python r18.py shape <cfg> | tex <cfg> <shapecfg> ; runs run_inbox.py per animal (wolf, horse, eagle)
import os, sys, shutil, subprocess, json
G = 'E:/gen3d'; R = f'{G}/r18'; PY = sys.executable
AN = dict(wolf=(f'{G}/r9/wolf/ref_c4.png', 1, f'{G}/tex12/_refs/wolf_delit.png'),
          horse=(f'{G}/r9/horse/ref_c5.png', 1, None), eagle=(f'{G}/r8/eagle/ref_rgba.png', 0, None))
BASE = ['--lowvram', '--vram-cap', '7.0', '--turing', '--no-rig']
SHAPE = {'base': [], 's100': ['--steps', '100'], 'g75': ['--guidance', '7.5'], 'g35': ['--guidance', '3.5'],
         'o1024': ['--octree', '1024', '--chunks', '8000'], 'declast': ['--decimate-last']}
TEX = {'tbase': [], 'tseam': ['--tex-seam', '24'], 'ttrust': ['--tex-trust-inpaint', '0.003'], 'tnosr': ['--no-esrgan'], 'best': []}
def run(args, log):
    with open(log, 'w') as f: return subprocess.run([PY, f'{G}/run_inbox.py'] + args, stdout=f, stderr=subprocess.STDOUT).returncode
mode, cfg = sys.argv[1], sys.argv[2]
ans = sys.argv[4].split(',') if len(sys.argv) > 4 else list(AN)
for an in ans:
    ref, seed, tref = AN[an]
    if mode == 'shape':
        flags = sum((SHAPE[k] for k in cfg.split('+')), [])
        inb = f'{R}/{cfg}/_in/{an}'; os.makedirs(f'{inb}/work', exist_ok=True); shutil.copy(ref, f'{inb}/hero.png')
        if cfg == 'declast':   # same raw as base, only cleanup order differs
            src = f'{R}/base/_in/{an}/work/raw21_s{seed}.obj'
            if os.path.exists(src): shutil.copy(src, f'{inb}/work/raw21_s{seed}.obj')
        rc = run([an, '--seeds', str(seed), '--inbox-root', f'{R}/{cfg}/_in', '--assets-root', f'{R}/{cfg}'] + BASE + flags, f'{inb}/run.log')
        o = f'{R}/{cfg}/{an}'; os.makedirs(o, exist_ok=True)
        if os.path.exists(f'{inb}/work/sheets/h21_s{seed}.png'): shutil.copy(f'{inb}/work/sheets/h21_s{seed}.png', f'{o}/sheet.png')
    else:   # tex <cfg> <shapecfg>: paint the clean mesh of shape config <shapecfg>
        scfg = sys.argv[3]; sinb = f'{R}/{scfg}/_in/{an}'
        inb = f'{R}/{cfg}/_in/{an}'; shutil.rmtree(inb, ignore_errors=True); shutil.copytree(sinb, inb, ignore=shutil.ignore_patterns('tex', 'logs', '_stage', 'lp*'))
        if tref:   # tex13 used the de-lit wolf ref for paint
            from PIL import Image; Image.open(tref).convert('RGBA').resize((1024, 1024), Image.LANCZOS).save(f'{inb}/work/ref_rgba.png')
        flags = sum((TEX[k] for k in cfg.split('+')), [])
        rc = run([an, '--seeds', str(seed), '--pick', f'h21_s{seed}', '--texture-only', '--inbox-root', f'{R}/{cfg}/_in', '--assets-root', f'{R}/{cfg}'] + BASE + flags, f'{inb}/run.log')
    print(mode, cfg, an, 'rc', rc, flush=True)
