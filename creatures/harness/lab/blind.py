#!/usr/bin/env python3
"""Shuffle lab sheets into a blind folder; keep the key outside it.

    python blind.py <judge_dir> <key.json> <sheet.png>...      # make blind set
    python blind.py --score <key.json> <answers.txt>            # score answers

answers.txt lines:  <id>: <animal guess> | <quality 1-10> | <note>
Sheet paths must look like .../<method>/<animal>.png.
"""
import sys, os, json, random, shutil, re


def make(jdir, key, sheets):
    os.makedirs(jdir, exist_ok=True)
    rng = random.SystemRandom()
    ids = rng.sample(range(100, 1000), len(sheets))
    k = {}
    for i, s in zip(ids, sheets):
        method = os.path.basename(os.path.dirname(s))
        animal = os.path.splitext(os.path.basename(s))[0]
        shutil.copy(s, os.path.join(jdir, f'{i}.png'))
        k[str(i)] = {'method': method, 'animal': animal}
    json.dump(k, open(key, 'w'), indent=1)
    print(f'{len(sheets)} sheets -> {jdir}')


SYN = {'tortoise': ['turtle'], 'crocodile': ['alligator', 'gator', 'caiman'],
       'wolf': ['dog', 'husky'], 'eagle': ['hawk', 'falcon', 'bird of prey', 'raptor']}


def score(key, ans):
    k = json.load(open(key))
    rows = {}
    for line in open(ans, encoding='utf-8'):
        m = re.match(r'\s*(\d+)\s*:\s*([^|]*)\|\s*([\d.]+)', line)
        if m:
            rows[m.group(1)] = (m.group(2).strip().lower(), float(m.group(3)))
    agg = {}
    for i, e in k.items():
        g, q = rows.get(i, ('', 0))
        names = [e['animal']] + SYN.get(e['animal'], [])
        hit = any(n in g for n in names)
        a = agg.setdefault(e['method'], {'n': 0, 'hit': 0, 'q': 0.0})
        a['n'] += 1; a['hit'] += hit; a['q'] += q
    for mth, a in sorted(agg.items()):
        print(f"{mth}: recognised {a['hit']}/{a['n']}, mean quality {a['q'] / a['n']:.2f}")
    return agg


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--score':
        score(a[1], a[2])
    else:
        make(a[0], a[1], a[2:])
