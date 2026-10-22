# builds zoo/rom_audit.md from zoo/<c>/stage4/rom/s4_rom.json
import json, os, glob
Z = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 't7x', 'zoo')
rows, worst = [], {}
for d in sorted(glob.glob(os.path.join(Z, '*', 'stage4', 'rom', 's4_rom.json'))):
    c = d.split(os.sep)[-4]
    j = json.load(open(d))
    s = j['summary']
    fails = [r for r in j['rows'] if not r['ok']]
    for r in fails:
        for f in r['fail']:
            worst[f] = worst.get(f, 0) + 1
    vmin = min(j['rows'], key=lambda r: r['vol'], default=None)
    top = '; '.join(f"{r['bone']} {r['pose']} ({','.join(r['fail'])})" for r in fails[:3])
    rows.append(f"| {c} | {s['pass_']}/{s['poses']} | {s['min_vol']}" + (f" ({vmin['bone']} {vmin['pose']})" if vmin else '') +
                f" | {s['max_stretch']} | {s['inverted_total']} ({s['fail_inv']}) | {s['overlap_new_total']} ({s['fail_ov']}) | {top} |")
txt = ['# Zoo ROM audit (2026-10-22, bone-heat weights, kit/rom_gate.py auto joints)', '',
       'Gates per pose: volume kept >= 0.70, stretch <= 2.0, flipped tris 0, new self-overlap <= 5% of joint region tris.',
       'Weights v2 (kit/weights.py) was REJECTED on the werewolf pilot (judge preferred baseline in both orders, 2 rounds;',
       'see abc/t8/weights/RESULT.md), so this is the current-weights audit only; no S4 changed.', '',
       '| creature | poses pass | min vol | max stretch | inverted (poses) | new overlap (poses) | first fails |',
       '|---|---|---|---|---|---|---|'] + rows + ['', 'Fail counts by gate (poses): ' + ', '.join(f'{k} {v}' for k, v in sorted(worst.items())),
       f'Creatures audited: {len(rows)}']
open(os.path.join(Z, 'rom_audit.md'), 'w', encoding='utf-8').write('\n'.join(txt) + '\n')
print(len(rows), worst)
