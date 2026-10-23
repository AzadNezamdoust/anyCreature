import json, subprocess, sys, copy, re
src = sys.argv[1]
s = json.load(open(src))
tmp = src.replace('.json', '_bis.json')
def run(sp):
    json.dump(sp, open(tmp, 'w'))
    r = subprocess.run(['node', 'engine/cli.js', tmp, tmp.replace('.json', '.glb')], capture_output=True, text=True)
    m = re.search(r'bind pose has (\d+) flipped', r.stdout + r.stderr)
    return int(m.group(1)) if m else 0
def vol(sp, c): return [v for v in sp['volumes'] if v['chain'] == c][0]
tests = {
 'fleg_sides': lambda sp: vol(sp, 'LFrontLeg').__setitem__('sides', 14),
 'bleg_sides': lambda sp: vol(sp, 'LBackLeg').__setitem__('sides', 14),
 'fleg_step': lambda sp: vol(sp, 'LFrontLeg').__setitem__('ring_step', 0.05),
 'bleg_step': lambda sp: vol(sp, 'LBackLeg').__setitem__('ring_step', 0.05),
 'head_nosharp': lambda sp: vol(sp, 'head')['profile'][2][3].pop('sharp'),
 'tail_step': lambda sp: vol(sp, 'tail').__setitem__('ring_step', 0.05),
 'body_step': lambda sp: vol(sp, 'body').__setitem__('ring_step', 0.06),
 'no_parts': lambda sp: sp.__setitem__('parts', []),}
for k, f in tests.items():
    sp = copy.deepcopy(s); f(sp); print(k, run(sp))

