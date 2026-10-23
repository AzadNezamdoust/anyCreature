import json, sys
o = sys.argv[1]
b = json.load(open(o + r'\push_b.json'))
for p in b['parts']:
    if p['name'] == 'tooth_lo1': p['offset'][1] = 0.0
json.dump(b, open(o + r'\push_b.json', 'w'), indent=1)
c = json.load(open(o + r'\push_c.json'))
for p in c['parts']:
    if p['name'] in ('crest3', 'crest4'): p['mirrored'] = False; p['anchor']['around'] = 0
json.dump(c, open(o + r'\push_c.json', 'w'), indent=1)
