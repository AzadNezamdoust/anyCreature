#!/usr/bin/env python3
"""Calibration: prove the rulers tell good from bad, per ruler, on THIS machine.

    python3 harness/calibrate.py        # exit 0 = the rulers separate, 1 = do not start

setup.sh and setup.ps1 run this and print "calibrate OK" only when it exits 0.

ENGINE rulers (engine/cli.js)
  wolf_green  known-good — must build: exit 0, no BLOCK line, an `"ok":true` report
  wolf_red    known-bad  — must be refused, and refused for ITS faults:
                           proportion, root_containment and limb_clearance
  red_5050    violates ONLY the 50:50 rule — must be refused by `proportion` and
                           by nothing else. A red sample that fails for other
                           reasons proves nothing about the ruler it was built for.

"Refused" means exit code non-zero AND at least one `BLOCK:` line. A crash also
exits non-zero, and counting a stack trace as a block is how a broken engine
would pass calibration.

COLOUR ruler (harness/judge.mjs over harness/outline.py)
  The shipped example wolf must read as coloured (saturated area over the 10%
  floor), and a DESATURATED copy of that same file — geometry untouched, only
  the albedo greyed — must be refused by saturation_area. Both directions, one
  sample: a ruler is calibrated by proving it separates. The colour sample is
  example/wolf.json, not wolf_green: wolf_green's palette is deliberately plain,
  it exists to exercise the engine blocks.

This file was retired in 1.3.2 together with the browser; setup kept printing
that it calibrated while nothing did. It is back, browser-free.
"""
import subprocess, os, sys, tempfile, json, struct, shutil

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
CLI = os.path.join(R, 'engine', 'cli.js')

# block kind -> the samples that must be refused by it
WOLF_RED_MUST = {'proportion', 'root_containment', 'limb_clearance'}
RED_5050_ONLY = {'proportion'}


def build(spec, tmp):
    out = os.path.join(tmp, os.path.basename(spec).replace('.json', '') + '.glb')
    p = subprocess.run(['node', CLI, spec, out], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    text = (p.stdout or '') + (p.stderr or '')
    kinds = set()
    for line in text.splitlines():
        if line.startswith('BLOCK:'):
            body = line[len('BLOCK:'):].strip()
            kinds.add(body.split(':')[0].split(' ')[0].strip())
    ok = p.returncode == 0 and not kinds and '"ok":true' in (p.stdout or '')
    return {'rc': p.returncode, 'kinds': kinds, 'ok': ok, 'out': out, 'text': text}


def tail(text, n=4):
    return '\n'.join('        ' + l[:160] for l in text.strip().splitlines()[-n:])


def desaturate(src, dst):
    """A grey twin of a built GLB: every colour replaced by its own luminance.

    Both halves of the albedo — baseColorFactor AND the float COLOR_0 stream —
    because the L1-L8 stack puts real chroma in the vertices. Geometry and
    animation are untouched, so the only thing that changes is exactly the
    quantity this ruler claims to measure."""
    d = open(src, 'rb').read()
    jl, = struct.unpack('<I', d[12:16])
    g = json.loads(d[20:20 + jl])
    rest = bytearray(d[20 + jl:])
    for m in g.get('materials', []):
        p = m.setdefault('pbrMetallicRoughness', {})
        b = p.get('baseColorFactor', [1, 1, 1, 1])
        lum = 0.2126 * b[0] + 0.7152 * b[1] + 0.0722 * b[2]
        p['baseColorFactor'] = [lum, lum, lum, b[3] if len(b) > 3 else 1]
    acc_ids = {prim['attributes']['COLOR_0']
               for mesh in g.get('meshes', []) for prim in mesh.get('primitives', [])
               if 'COLOR_0' in prim.get('attributes', {})}
    views, base = g.get('bufferViews', []), 8      # rest = 8-byte BIN header + payload
    for ai in acc_ids:
        a = g['accessors'][ai]
        if a.get('componentType') != 5126 or a.get('type') not in ('VEC3', 'VEC4'):
            continue                               # only float colours are rewritten
        n = 3 if a['type'] == 'VEC3' else 4
        bv = views[a['bufferView']]
        off = base + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = bv.get('byteStride') or 4 * n
        for i in range(a['count']):
            o = off + i * stride
            r, gg, bb = struct.unpack_from('<fff', rest, o)
            L = 0.2126 * r + 0.7152 * gg + 0.0722 * bb
            struct.pack_into('<fff', rest, o, L, L, L)
    js = json.dumps(g).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    out = b'glTF' + struct.pack('<II', 2, 0) + struct.pack('<II', len(js), 0x4E4F534A) + js + bytes(rest)
    out = out[:8] + struct.pack('<I', len(out)) + out[12:]
    open(dst, 'wb').write(out)


SAT_CLAIM = {'name': 'colour-ruler', 'claims': [
    {'type': 'saturation_area', 'view': 'hero', 'min': 0.10,
     'label': 'must not read as a grey mass (floor 10%)'}]}


def judge(glb, claims, tmp, tag):
    p = subprocess.run(['node', os.path.join(H, 'judge.mjs'), glb, os.path.join(tmp, tag),
                        tag, '--spec', claims, '--json'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    text = (p.stdout or '') + (p.stderr or '')
    share = None
    for line in text.splitlines():
        if line.startswith('{') and 'hi_sat_share' in line:
            try:
                share = json.loads(line)['hi_sat_share'].get('hero')
            except Exception:
                pass
    return p.returncode, text, share


def main():
    tmp = tempfile.mkdtemp(prefix='calib_')
    try:
        return run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(tmp):
    cal = lambda n: os.path.join(R, 'calibration', n)
    fails = 0

    g = build(cal('wolf_green.json'), tmp)
    if g['ok']:
        print('green    (known-good)      -> builds ✓')
    else:
        fails += 1
        why = ('blocked by ' + ', '.join(sorted(g['kinds']))) if g['kinds'] else f'exit {g["rc"]}, no report'
        print(f'green    (known-good)      -> {why} ✗ (ruler too strict, or the sample rotted)')
        print(tail(g['text']))

    r = build(cal('wolf_red.json'), tmp)
    missing = WOLF_RED_MUST - r['kinds']
    if r['rc'] != 0 and r['kinds'] and not missing:
        extra = r['kinds'] - WOLF_RED_MUST
        print('red      (legacy faults)   -> blocked by ' + ', '.join(sorted(WOLF_RED_MUST)) + ' ✓'
              + (f'  (also: {", ".join(sorted(extra))})' if extra else ''))
    else:
        fails += 1
        if r['rc'] == 0:
            print('red      (legacy faults)   -> PASSED ✗ (ruler too loose)')
        elif not r['kinds']:
            print(f'red      (legacy faults)   -> exit {r["rc"]} with no BLOCK line ✗ (the engine crashed, it did not judge)')
            print(tail(r['text']))
        else:
            print('red      (legacy faults)   -> blocked, but NOT by ' + ', '.join(sorted(missing))
                  + f' ✗ (got: {", ".join(sorted(r["kinds"]))})')

    f = build(cal('red_5050.json'), tmp)
    if f['rc'] != 0 and f['kinds'] == RED_5050_ONLY:
        print('red_5050 (only 50:50)      -> blocked by proportion, and only by it ✓')
    else:
        fails += 1
        if f['rc'] == 0:
            print('red_5050 (only 50:50)      -> PASSED ✗ (the proportion ruler does not bite)')
        elif not f['kinds']:
            print(f'red_5050 (only 50:50)      -> exit {f["rc"]} with no BLOCK line ✗ (crash, not a verdict)')
            print(tail(f['text']))
        else:
            print(f'red_5050 (only 50:50)      -> blocked by {", ".join(sorted(f["kinds"]))} ✗ '
                  '(must be proportion and nothing else, or it proves nothing about that ruler)')

    # ── the colour ruler ────────────────────────────────────────────────────
    c = build(os.path.join(R, 'example', 'wolf.json'), tmp)
    if not c['ok']:
        fails += 1
        print('colour ruler              -> example/wolf.json did not build ✗')
        print(tail(c['text']))
    else:
        claims = os.path.join(tmp, 'sat.json')
        json.dump(SAT_CLAIM, open(claims, 'w'))
        rc_c, txt_c, share = judge(c['out'], claims, tmp, 'colour')
        grey = os.path.join(tmp, 'grey.glb')
        desaturate(c['out'], grey)
        rc_g, txt_g, share_g = judge(grey, claims, tmp, 'grey')
        if share is None:
            fails += 1
            print('colour ruler              -> the judge measured nothing ✗')
            print(tail(txt_c))
        else:
            if rc_c == 0:
                print(f'colour   (example wolf)    -> reads as coloured ✓ ({share * 100:.1f}% saturated)')
            else:
                fails += 1
                print(f'colour   (example wolf)    -> BLOCKED ✗ ({share * 100:.1f}% — the ruler is not '
                      'seeing baseColorFactor x COLOR_0, or the example went grey)')
            if rc_g != 0 and 'saturated' in txt_g:
                print(f'colour   (desaturated)     -> blocked by saturation_area ✓ ({(share_g or 0) * 100:.1f}%)')
            else:
                fails += 1
                print('colour   (desaturated)     -> NOT blocked ✗ (the colour ruler passes anything)')

    if fails:
        print(f'[calibrate] FAILED — {fails} ruler(s) do not separate good from bad. '
              'Do not start work; report this.')
        return 1
    print('[calibrate] OK: the rulers separate good from bad.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
