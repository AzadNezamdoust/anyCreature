#!/usr/bin/env python3
"""Print the gate map: every check in the system, tagged on five axes.

usage: python3 harness/gates.py [LOW|MID|HIGH|SHIP|any]
       python3 harness/gates.py --by dept|kind|by

Five questions, asked of every check. The first two are about ENFORCEMENT, the
last three are about ARCHITECTURE — they exist so a piece can be swapped without
the pipeline changing shape.

  · does it BLOCK or only ADVISE?
  · is it ALLOCATED before the build, or VERIFIED after?
  · WHICH SOURCE decides it — A, B or C?
  · WHAT KIND — legality (a defect, no debate) or style (taste with a number)?
  · WHICH DEPARTMENT — model / material / skeleton / animation / process?

"allocate vs verify" is where the money is: anything decidable up front that is
only checked afterwards is a rebuild waiting to happen. "legality vs style" is
where the FLEXIBILITY is: a legality check only ever gets better, while every
style threshold is a candidate to become a swappable profile, and none of them
should ever be mistaken for a law.
"""
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, 'gates.json'), encoding='utf-8'))
want = (sys.argv[1].upper() if len(sys.argv) > 1 else None)

def w(s, n):
    width = sum(2 if ord(c) > 127 else 1 for c in s)
    return s + ' ' * max(0, n - width)

rows = [c for c in G['checks'] if not want or c['stage'].upper() == want]
order = {'LOW': 0, 'MID': 1, 'HIGH': 2, 'SHIP': 3, 'ANY': 4}
rows.sort(key=lambda c: (order.get(c['stage'].upper(), 9), c['enforce'], c['id']))

print()
for k, v in G['stages'].items():
    print(f'  {k:5} {v}')
print()
print(w('stage', 7) + w('enforce', 22) + w('when', 10) + w('id', 20) + 'what it is')
print('-' * 100)
# ▣ = advises the first time, blocks if the next round still has not fixed it
MARK = {'block': '■', 'advise': '·', 'advise-then-block': '▣'}
last = None
for c in rows:
    if c['stage'] != last:
        print()
        last = c['stage']
    print(w(c['stage'], 7) + w(MARK.get(c['enforce'], '?') + ' ' + c['enforce'], 22)
          + w(c['when'], 10) + w(c['id'], 20) + c['plain'])

# ── the architecture axes ────────────────────────────────────────────────
def group(field, title, note):
    from collections import defaultdict
    g = defaultdict(list)
    for c in rows:
        g[c.get(field, '?')].append(c['id'])
    print()
    print(f'  {title}')
    for k in sorted(g, key=lambda k: -len(g[k])):
        print(f'    {w(k, 11)} {len(g[k]):>2}   ' + ', '.join(sorted(g[k]))[:74])
    print(f'    {note}')

if len(sys.argv) > 2 and sys.argv[1] == '--by':
    pass
group('kind', 'BY KIND — legality is a defect and only gets better; style is taste with a number on it',
      'every style row is a candidate to become a swappable profile. None of them is a law.')
group('by', 'BY SOURCE — which source produces the verdict for this check',
      'the source is fixed per check in gates.json; changing it changes what the check costs to run.')
group('dept', 'BY DEPARTMENT — two checks in one department should share their tools',
      'a measure defined twice is a measure that will drift; synccheck.py lists any that are.')

nb = sum(1 for c in rows if c['enforce'] == 'block')
nt = sum(1 for c in rows if c['enforce'] == 'advise-then-block')
na = len(rows) - nb - nt
al = sum(1 for c in rows if c['when'] == 'allocate')
mis = [c for c in rows if c['when'] == 'allocate' and c['enforce'] == 'block']
print()
print(f'  {nb} block · {na} advise · {nt} advise-then-block · '
      f'{al} of {len(rows)} are decidable before the build')
if mis:
    print()
    print('  Blocking, but decidable up front — each of these can refuse a build over')
    print('  something that should simply have been budgeted:')
    for c in mis:
        print(f'    · {c["id"]}: {c["plain"]}')
print()
