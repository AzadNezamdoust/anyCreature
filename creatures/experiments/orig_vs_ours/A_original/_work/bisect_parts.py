import json, subprocess, sys, copy, re
src = sys.argv[1]
s = json.load(open(src))
tmp = src.replace('.json', '_bis.json')
def run(sp):
    json.dump(sp, open(tmp, 'w'))
    r = subprocess.run(['node', 'engine/cli.js', tmp, tmp.replace('.json', '.glb')], capture_output=True, text=True)
    m = re.search(r'bind pose has (\d+) flipped', r.stdout + r.stderr)
    return int(m.group(1)) if m else 0
print('all', run(s))
for p in s['parts']:
    sp = copy.deepcopy(s); sp['parts'] = [q for q in sp['parts'] if q['name'] != p['name']]
    print('-', p['name'], run(sp))

