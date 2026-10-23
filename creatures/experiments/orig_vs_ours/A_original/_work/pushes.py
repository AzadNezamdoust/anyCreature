import json, copy, sys
o = sys.argv[1]
base = json.load(open(o + r'\pole_a.json'))
def scale_scutes(s, k):
    for p in s['parts']:
        if p['type'] == 'fin':
            p['points'] = [[u, v * k if v > 0 else v] for u, v in p['points']]
a = copy.deepcopy(base); scale_scutes(a, 1.5)
b = copy.deepcopy(base); scale_scutes(b, 1.15)
b['joints']['Jaw1']['up'] = -0.085; b['joints']['JawTip']['up'] = -0.04
c = copy.deepcopy(base); scale_scutes(c, 1.25)
c['joints']['Tail2']['side'] = 0.14; c['joints']['Tail3']['side'] = 0.2; c['joints']['TailTip']['side'] = 0.22
for n, s in (('push_a', a), ('push_b', b), ('push_c', c)):
    json.dump(s, open(o + '\\' + n + '.json', 'w'), indent=1)
