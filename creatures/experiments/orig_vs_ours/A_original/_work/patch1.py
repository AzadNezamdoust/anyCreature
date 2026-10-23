import json,sys
for p in sys.argv[1:]:
    s=json.load(open(p))
    for v in s['volumes']:
        if v['chain']=='LBackLeg': v['ring_step']=0.05
    json.dump(s,open(p,'w'),indent=1)
