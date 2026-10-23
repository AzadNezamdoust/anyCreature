import json, copy, sys
o = sys.argv[1]
base = json.load(open(o + r'\pole_a.json'))
def fins(s, k, pred=lambda p: True):
    for p in s['parts']:
        if p['type'] == 'fin' and pred(p):
            p['points'] = [[u, v * k if v > 0 else v] for u, v in p['points']]
def vol(s, c): return [v for v in s['volumes'] if v['chain'] == c][0]
def scale_prof(s, c, k):
    for r in vol(s, c)['profile'][1:]:
        r[1] *= k; r[2] *= k
J = lambda s: s['joints']
# A: front-loaded - giant head and jaw
a = copy.deepcopy(base); fins(a, 1.2)
for n in ('Skull', 'Snout', 'Snout2', 'NoseTip', 'Jaw1', 'JawTip'):
    J(a)[n]['fwd'] *= 1.35
scale_prof(a, 'head', 1.3); scale_prof(a, 'jaw', 1.3)
J(a)['JawRoot']['up'] *= 1.3
for p in a['parts']:
    if p['name'].startswith('tooth'):
        p['offset'] = [p['offset'][0]*1.15, p['offset'][1]*(0.6 if 'up' in p['name'] else 0.8), p['offset'][2]*1.35]
        for sg in p['segments']: sg['len'] *= 1.4; sg['r'] *= 1.3
    if p['name'] == 'eye': p['size'] *= 1.3
# B: rear-loaded - massive tail with huge crest
b = copy.deepcopy(base); fins(b, 1.7, lambda p: p['name'].startswith('crest')); fins(b, 1.2, lambda p: p['name'].startswith('scute'))
scale_prof(b, 'tail', 1.45)
for n in ('Tail1', 'Tail2', 'Tail3', 'TailTip'): J(b)[n]['fwd'] *= 1.0
for p in b['parts']:
    if p['name'].startswith('tooth_up'): p['offset'][1] += 0.045
    if p['name'].startswith('tooth_lo'): p['offset'][1] -= 0.035
# C: reared - chest and head lifted, jaw agape
c = copy.deepcopy(base); fins(c, 1.3)
J(c)['Shoulders']['up'] = 0.08; J(c)['Neck']['up'] = 0.1; J(c)['Chest']['up'] = 0.05
J(c)['Jaw1']['up'] = -0.085; J(c)['JawTip']['up'] = -0.04
for p in c['parts']:
    if p['name'] == 'tooth_lo1': p['offset'][1] = 0.0
for n, s in (('push_a', a), ('push_b', b), ('push_c', c)):
    json.dump(s, open(o + '\\' + n + '.json', 'w'), indent=1)






