#!/usr/bin/env python3
"""Blind judging material for the box-model run.

    py -3.11 experiments/boxmodel/judge/prepare.py --blind <dir> --key <file> [--seed N]

1. Renders every box-model final, engine creature and CC0 reference the same way
   (kit/render_glb.py, beauty: hero + side). References modelled in a T-pose are
   shown at their Idle clip's first frame.
2. Pair sheets: two models side by side (A left, B right), each from the same two
   views. Which side holds the box model is random per pair; a flipped twin set
   swaps every pair, so one judge seat sees set 1 and another sees set 2 and
   position bias cancels.
3. Identity sheets: the harness read set (az000, az045, az090, az135, az180, top)
   of each final as silhouettes (from harness/outline.py) and a colour hero.

Everything a judge sees goes to --blind under neutral names (no creature, method
or maker in any path); the key goes to --key, which no judge is shown.
"""
import argparse, json, os, random, subprocess, sys, glob, shutil
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'kit'))
import run as kitrun                                    # blender_exe, font

CREATURES = ['wolf', 'raven_wyvern', 'giant', 'boar', 'goblin']
ENGINE = {'wolf': 'example/wolf.glb', 'raven_wyvern': 'example/gallery/raven_wyvern.glb',
          'giant': 'example/gallery/giant.glb'}
REFS = {'wolf': ('wolf_quaternius.glb', None), 'giant': ('giant_quaternius.glb', 'Idle'),
        'boar': ('pig_quaternius.glb', None), 'goblin': ('goblin_quaternius.glb', 'Idle')}
REFDIR = os.path.join(ROOT, 'out', 'boxmodel', 'refs')
WORK = os.path.join(ROOT, 'out', 'boxmodel', 'judge')
VIEWS = ['hero', 'az090']
READ = ['az000', 'az045', 'az090', 'az135', 'az180', 'top']


def final_glb(c):
    return os.path.join(ROOT, 'experiments', 'boxmodel', 'opus', c, 'stage4', f'{c}.glb')


def render_all():
    jobs, models = [], {}
    for c in CREATURES:
        g = final_glb(c)
        if os.path.exists(g):
            models[f'{c}:box'] = (g, None)
        if c in ENGINE:
            models[f'{c}:engine'] = (os.path.join(ROOT, ENGINE[c]), None)
        if c in REFS and os.path.exists(os.path.join(REFDIR, REFS[c][0])):
            models[f'{c}:ref'] = (os.path.join(REFDIR, REFS[c][0]), REFS[c][1])
    for k, (g, pose) in models.items():
        jobs.append(dict(glb=g, out=os.path.join(WORK, 'renders'), prefix=k.replace(':', '__'), mode='beauty',
                         views=VIEWS, res=640, pose=pose))
    jp = os.path.join(WORK, 'jobs.json')
    os.makedirs(WORK, exist_ok=True)
    json.dump(jobs, open(jp, 'w'), indent=1)
    p = subprocess.run([kitrun.blender_exe(), '-b', '--factory-startup', '-P',
                        os.path.join(HERE, '..', 'kit', 'render_glb.py'), '--', '--jobs', jp],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if 'Traceback' in p.stdout + p.stderr:
        print((p.stdout + p.stderr)[-3000:]); sys.exit(2)
    return models


def pair_sheet(left, right, out):
    t = 560
    im = Image.new('RGB', (2 * t + 24, 2 * t + 60), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for col, key in enumerate((left, right)):
        x = col * (t + 24)
        d.text((x + t // 2 - 12, 8), 'AB'[col], fill=(0, 0, 0), font=kitrun.font(40))
        for row, v in enumerate(VIEWS):
            p = os.path.join(WORK, 'renders', f"{key.replace(':', '__')}_{v}.png")
            im.paste(Image.open(p).convert('RGB').resize((t, t), Image.LANCZOS), (x, 60 + row * t))
    im.save(out, quality=88)


def read_sheet(c, out, colour=False):
    t = 320
    if colour:
        p = os.path.join(WORK, 'renders', f'{c}__box_hero.png')
        Image.open(p).convert('RGB').resize((640, 640), Image.LANCZOS).save(out, quality=88)
        return True
    src = os.path.join(ROOT, 'out', 'boxmodel', 'opus', c, 'orbit_stage4')
    if not os.path.exists(os.path.join(src, 'sil_az000.png')):
        return False
    im = Image.new('RGB', (3 * t, 2 * (t + 30)), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for i, v in enumerate(READ):
        x, y = (i % 3) * t, (i // 3) * (t + 30)
        d.text((x + 8, y + 4), v, fill=(0, 0, 0), font=kitrun.font(20))
        im.paste(Image.open(os.path.join(src, f'sil_{v}.png')).convert('RGB').resize((t, t), Image.LANCZOS), (x, y + 30))
    im.save(out, quality=88)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--blind', required=True)
    ap.add_argument('--key', required=True)
    ap.add_argument('--seed', type=int, default=20260926)
    ap.add_argument('--creatures', default=','.join(CREATURES))
    a = ap.parse_args()
    CREATURES[:] = a.creatures.split(',')
    rng = random.Random(a.seed)
    models = render_all()
    shutil.rmtree(a.blind, ignore_errors=True)
    os.makedirs(a.blind)
    pairs = []
    for c in CREATURES:
        if f'{c}:box' not in models:
            continue
        for other in ('engine', 'ref'):
            if f'{c}:{other}' in models:
                pairs.append((c, other))
    rng.shuffle(pairs)
    key = {'pairs': {}, 'identity': {}}
    for i, (c, other) in enumerate(pairs, 1):
        box_left = rng.random() < 0.5
        for s, flip in ((1, False), (2, True)):
            bl = box_left != flip
            L, R = (f'{c}:box', f'{c}:{other}') if bl else (f'{c}:{other}', f'{c}:box')
            name = f'set{s}_image{i}.jpg'
            pair_sheet(L, R, os.path.join(a.blind, name))
            key['pairs'][name] = dict(creature=c, against=other, box_side='A' if bl else 'B')
    order = CREATURES[:]
    rng.shuffle(order)
    for i, c in enumerate(order, 1):
        if f'{c}:box' not in models:
            continue
        if read_sheet(c, os.path.join(a.blind, f'shape{i}.jpg')):
            key['identity'][f'shape{i}.jpg'] = c
        read_sheet(c, os.path.join(a.blind, f'look{i}.jpg'), colour=True)
        key['identity'][f'look{i}.jpg'] = c
    json.dump(key, open(a.key, 'w'), indent=1)
    print(f'{len(pairs)} pairs x 2 sets, {len(key["identity"])} identity sheets -> {a.blind}; key -> {a.key}')


if __name__ == '__main__':
    main()
