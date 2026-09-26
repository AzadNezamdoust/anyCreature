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
  The claim reads the PALETTE (the albedo the engine records before lighting)
  with a floor on the share at HSV S >= 0.30 and a ceiling on the share at
  S >= 0.50. Both directions of both bars, on shipped files:
    good   example/wolf.json (a muted natural palette) and the gallery
           raven_wyvern (a vivid crest and beak, dusky wings) must pass both
    grey   a DESATURATED copy of the wolf — geometry untouched, every colour
           greyed (palette record, baseColorFactor and COLOR_0) — must be
           refused by the floor
    loud   a SATURATED copy — every colour pushed to HSV S >= 0.80, hue and
           value kept — must be refused by the ceiling
  A ruler is calibrated by proving it separates. The colour samples are the
  shipped examples, not wolf_green: wolf_green's palette is deliberately plain
  (fur S 0.17, 0.2% coloured), it exists to exercise the engine blocks. The
  gallery giant is judged against the same band by tools/test.sh.

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


def _recolour(src, dst, fn):
    """A twin of a built GLB with every colour passed through fn — geometry and
    animation untouched, so the only thing that changes is exactly the quantity
    the colour ruler claims to measure.

    fn maps an (n, 3) array of sRGB 0..1 colours to the same. Every place a
    colour lives is rewritten: the palette record (asset.extras.albedo, what the
    ruler reads) and the baked colour — baseColorFactor x COLOR_0, folded into
    COLOR_0 with the base set to white, since a recoloured vertex no longer fits
    under its material's old per-channel maximum."""
    import base64
    import numpy as np
    enc = lambda l: np.where(l <= 0.0031308, l * 12.92, 1.055 * np.power(np.clip(l, 0, None), 1 / 2.4) - 0.055)
    dec = lambda c: np.where(c <= 0.04045, c / 12.92, np.power((c + 0.055) / 1.055, 2.4))
    d = open(src, 'rb').read()
    jl, = struct.unpack('<I', d[12:16])
    g = json.loads(d[20:20 + jl])
    rest = bytearray(d[20 + jl:])
    x = (g.get('asset', {}) or {}).get('extras', {}) or {}
    rec = x.get('albedo')
    if isinstance(rec, dict) and rec.get('data'):
        raw = np.frombuffer(base64.b64decode(rec['data']), dtype=np.uint8).reshape(-1, 3) / 255.0
        rec['data'] = base64.b64encode(np.clip(np.round(fn(raw) * 255), 0, 255)
                                       .astype(np.uint8).tobytes()).decode()
    mats = g.get('materials', [])
    bases = [list((m.get('pbrMetallicRoughness', {}) or {}).get('baseColorFactor', [1, 1, 1, 1])) for m in mats]
    views, off0 = g.get('bufferViews', []), 8      # rest = 8-byte BIN header + payload
    for mesh in g.get('meshes', []):
        for prim in mesh.get('primitives', []):
            ai = prim.get('attributes', {}).get('COLOR_0')
            if ai is None:
                continue
            a = g['accessors'][ai]
            if a.get('componentType') != 5126 or a.get('type') not in ('VEC3', 'VEC4'):
                continue                           # only float colours are rewritten
            n = 3 if a['type'] == 'VEC3' else 4
            bv = views[a['bufferView']]
            off = off0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            stride = bv.get('byteStride') or 4 * n
            base = np.array((bases[prim['material']] if 'material' in prim else [1, 1, 1, 1])[:3])
            lin = np.array([struct.unpack_from('<fff', rest, off + i * stride) for i in range(a['count'])]) * base
            out = dec(np.clip(fn(np.clip(enc(lin), 0, 1)), 0, 1))
            for i, c in enumerate(out):
                struct.pack_into('<fff', rest, off + i * stride, *map(float, c))
    for m in mats:
        p = m.setdefault('pbrMetallicRoughness', {})
        b = p.get('baseColorFactor', [1, 1, 1, 1])
        p['baseColorFactor'] = [1.0, 1.0, 1.0, b[3] if len(b) > 3 else 1]
    js = json.dumps(g).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    out = b'glTF' + struct.pack('<II', 2, 0) + struct.pack('<II', len(js), 0x4E4F534A) + js + bytes(rest)
    out = out[:8] + struct.pack('<I', len(out)) + out[12:]
    open(dst, 'wb').write(out)


def desaturate(src, dst):
    """The grey twin: every colour replaced by its own luminance."""
    def grey(c):
        L = (0.2126 * c[:, 0] + 0.7152 * c[:, 1] + 0.0722 * c[:, 2])[:, None]
        return c * 0 + L
    _recolour(src, dst, grey)


def saturate(src, dst, floor=0.80):
    """The loud twin: every colour's HSV S raised to at least `floor`, hue and
    value kept. Greys (no hue to keep) stay grey — a pupil, an eye white."""
    import numpy as np

    def loud(c):
        mx, mn = c.max(axis=1), c.min(axis=1)
        s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0.0)
        s2 = np.where(s > 0.02, np.maximum(s, floor), s)
        # keep V (the max channel) and the hue: scale every channel's distance from the max
        k = np.where(s > 1e-9, s2 / np.maximum(s, 1e-9), 1.0)[:, None]
        return mx[:, None] - (mx[:, None] - c) * k
    _recolour(src, dst, loud)


SAT_CLAIM = {'name': 'colour-ruler', 'claims': [
    {'type': 'saturation_area', 'view': 'hero', 'min': 0.10, 'max': 0.50,
     'label': 'coloured, not a grey mass (floor 10% at S 0.30); loud colour a spotlight (ceiling 50% at S 0.50)'}]}


def judge(glb, claims, tmp, tag):
    p = subprocess.run(['node', os.path.join(H, 'judge.mjs'), glb, os.path.join(tmp, tag),
                        tag, '--spec', claims, '--json'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    text = (p.stdout or '') + (p.stderr or '')
    share = None
    for line in text.splitlines():
        if line.startswith('{') and 'hi_sat_share' in line:
            try:
                j = json.loads(line)
                share = (j.get('coloured_share', {}).get('hero'), j['hi_sat_share'].get('hero'),
                         j.get('palette_source', {}).get('hero'))
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
    claims = os.path.join(tmp, 'sat.json')
    json.dump(SAT_CLAIM, open(claims, 'w'))
    fmt = lambda sh: f'{sh[0] * 100:.1f}% coloured, {sh[1] * 100:.1f}% loud, ' \
                     + ('on the palette' if sh[2] == 'albedo' else 'on the baked colour')
    wolf = None
    for tag, spec in (('example wolf', os.path.join(R, 'example', 'wolf.json')),
                      ('gallery wyvern', os.path.join(R, 'example', 'gallery', 'raven_wyvern.json'))):
        c = build(spec, tmp)
        if not c['ok']:
            fails += 1
            print(f'colour   ({tag:<14}) -> did not build ✗')
            print(tail(c['text']))
            continue
        rc, txt, share = judge(c['out'], claims, tmp, tag.split()[-1])
        if share is None or share[0] is None:
            fails += 1
            print(f'colour   ({tag:<14}) -> the judge measured nothing ✗')
            print(tail(txt))
        elif share[2] != 'albedo':
            fails += 1
            print(f'colour   ({tag:<14}) -> measured the baked colour, not the palette ✗ '
                  '(the build wrote no asset.extras.albedo, or outline.py could not place it)')
        elif rc == 0:
            print(f'colour   ({tag:<14}) -> in band ✓ ({fmt(share)})')
        else:
            fails += 1
            print(f'colour   ({tag:<14}) -> REFUSED ✗ ({fmt(share)} — the band is off, or the example drifted)')
            print(tail(txt))
        if tag == 'example wolf':
            wolf = c['out']
    if wolf:
        for tag, make, want in (('desaturated', desaturate, 'Too little colour'),
                                ('saturated', saturate, 'Too much loud colour')):
            twin = os.path.join(tmp, tag + '.glb')
            make(wolf, twin)
            rc, txt, share = judge(twin, claims, tmp, tag)
            got = fmt(share) if share and share[0] is not None else 'nothing measured'
            if rc != 0 and want in txt:
                print(f'colour   ({tag:<14}) -> refused ✓ ({got})')
            else:
                fails += 1
                print(f'colour   ({tag:<14}) -> NOT refused ✗ ({got}; the colour ruler passes anything)')

    if fails:
        print(f'[calibrate] FAILED — {fails} ruler(s) do not separate good from bad. '
              'Do not start work; report this.')
        return 1
    print('[calibrate] OK: the rulers separate good from bad.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
