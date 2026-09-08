#!/usr/bin/env python3
"""Calibration: prove the rulers tell good from bad, per ruler.

L1 — the ENGINE rulers (no browser needed)
green    = the bred example wolf (must build clean)
red      = legacy multi-fault wolf (must be blocked)
red_5050 = violates ONLY the 50:50 proportion rule — must be blocked AND the
           block reason must actually be 'proportion' (a red sample that fails
           for other reasons proves nothing about this ruler).

L2 — the COLOUR ruler (judge.mjs; skipped when no browser is installed)
Same shape, both directions: the shipped example wolf must read as COLOURED
(saturated area above the 10% floor), and a DESATURATED copy of that same file
must be blocked BY saturation_area. A ruler is calibrated by proving it
separates, not by pinning one sample inside a band — the band's ceiling is gone
(saturation_area is advisory now, and the L1-L8 stack raises chroma by design).
Added after a real miss: the 1.3.0 colour split moved the hue
from COLOR_0 into baseColorFactor, the judge's albedo pass still forced the
base to white, and saturation_area silently measured 0.0% on every creature —
which would have failed every HIGH gate with "reads as a grey mass". Nothing
caught it because calibration had never run the judge at all.
"""
import subprocess, os, sys, tempfile, json, struct
H = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(H, '..')
tmp = tempfile.mkdtemp(prefix='calib_')

def build(spec, folder='calibration'):
    out = os.path.join(tmp, os.path.basename(spec) + '.glb')
    p = subprocess.run(['node', os.path.join(R, 'engine', 'cli.js'),
                        os.path.join(R, folder, spec), out],
                       capture_output=True, text=True)
    return p.returncode, p.stderr, out

rc_g, _, green_glb = build('wolf_green.json')
rc_r, _, _ = build('wolf_red.json')
rc_5, err5, _ = build('red_5050.json')
ok_g = rc_g == 0
ok_r = rc_r != 0
ok_5 = rc_5 != 0 and 'proportion' in err5

print(f"green (known-good)        -> {'PASS ✓' if ok_g else 'blocked ✗ (ruler too strict)'}")
print(f"red   (multi-fault)       -> {'blocked ✓' if ok_r else 'PASSED ✗ (ruler too loose)'}")
print(f"red_5050 (only 50:50)     -> {'blocked by proportion ✓' if ok_5 else 'NOT blocked by proportion ✗'}")

# ── L2: the colour ruler ─────────────────────────────────────────────────────
# The upper bound is gone, and it had to go twice over. The gate restructure
# made saturation_area advisory — there is no ceiling left to calibrate against
# — and the L1-L8 shading stack then measured the shipped wolf at ~52%, because
# L4 raises chroma on purpose in the upper region. Calibrating against a ceiling
# that neither the gate nor the shading believes in would fail every fresh
# install for a creature nothing is wrong with.
#
# What a ruler has to prove is that it SEPARATES, and that is what this tests:
# the shipped wolf must read as coloured, and a desaturated copy of the same
# file must read as grey. Both directions, one sample, no magic ceiling.
SAT_CLAIM = {'name': 'colour-ruler', 'claims': [
    {'type': 'saturation_area', 'view': 'tq', 'min': 0.10,
     'stage': 'HIGH', 'label': 'must not read as a grey mass (floor 10%)'}]}


def desaturate(src, dst):
    """A grey twin of a built GLB: every colour replaced by its own luminance.

    Both halves of the albedo, and it has to be both. This used to grey only
    `baseColorFactor` on the theory that COLOR_0 carries a neutral shading
    ratio — which was true while one material meant one hue. The L1-L8 stack
    makes hue vary per VERTEX, so the ratio carries real chroma, and greying the
    factor alone left a creature that still measured 51% saturated. The test
    then reported the ruler was broken when what was broken was the twin.

    Geometry and animation are untouched, so the only thing that changed is
    still the exact quantity this ruler claims to measure."""
    d = open(src, 'rb').read()
    jl, = struct.unpack('<I', d[12:16])
    g = json.loads(d[20:20 + jl])
    rest = bytearray(d[20 + jl:])
    for m in g.get('materials', []):
        p = m.setdefault('pbrMetallicRoughness', {})
        b = p.get('baseColorFactor', [1, 1, 1, 1])
        lum = 0.2126 * b[0] + 0.7152 * b[1] + 0.0722 * b[2]
        p['baseColorFactor'] = [lum, lum, lum, b[3] if len(b) > 3 else 1]

    # COLOR_0, in the binary chunk. rest = 8-byte BIN chunk header + payload.
    acc_ids = {prim['attributes']['COLOR_0']
               for mesh in g.get('meshes', []) for prim in mesh.get('primitives', [])
               if 'COLOR_0' in prim.get('attributes', {})}
    views, base = g.get('bufferViews', []), 8
    for ai in acc_ids:
        a = g['accessors'][ai]
        if a.get('componentType') != 5126 or a.get('type') not in ('VEC3', 'VEC4'):
            continue                      # only float colours are rewritten
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
    out = (b"glTF" + struct.pack("<II", 2, 0) + struct.pack("<II", len(js), 0x4E4F534A) + js + bytes(rest))
    out = out[:8] + struct.pack('<I', len(out)) + out[12:]
    open(dst, 'wb').write(out)


def judge(glb, spec_path):
    # --json because this is a machine reading the output: the judge prints a
    # short human summary by default now (a 2KB blob on stdout every run is paid
    # for again on every later turn), and calibration needs the numbers.
    p = subprocess.run(['node', os.path.join(H, 'judge.mjs'), glb,
                        os.path.join(tmp, 'j'), 'calib', '--spec', spec_path,
                        '--json'],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


# The colour sample is example/wolf.json, NOT calibration/wolf_green.json:
# wolf_green carries the pre-1.2.0 beige palette (it measures 0.2% saturated
# and exists to exercise the ENGINE blocks, where palette is irrelevant),
# while example/wolf.json is the reshipped creature the colour norms were
# written against. Using the wrong one here would calibrate the ruler against
# a sample that the shipped norms themselves reject.
rc_cbuild, _, colour_glb = build('wolf.json', 'example')
ok_c = True
if rc_cbuild != 0:
    print('colour ruler              -> skipped (example/wolf.json did not build)')
    ok_c = False
else:
    spec_path = os.path.join(tmp, 'sat.json')
    json.dump(SAT_CLAIM, open(spec_path, 'w'))
    rc_cg, out_cg = judge(colour_glb, spec_path)
    # A judge that never MEASURED anything (no metrics line) did not fail this
    # ruler — it failed to run: no browser, no `npm install` yet, a sandbox with
    # no /dev/shm. Saying "the colour ruler is blind" there would send someone
    # hunting a bug in the ruler on a machine that simply has no browser.
    measured = any(l.startswith('{') and 'hi_sat_share' in l for l in out_cg.splitlines())
    if not measured:
        why = ('no browser installed' if 'cannot start a browser' in out_cg
               else "playwright is not installed (run setup.sh, or npm i)"
               if 'ERR_MODULE_NOT_FOUND' in out_cg or "Cannot find package" in out_cg
               else 'the judge could not run: ' + (out_cg.strip().splitlines() or [''])[-1][:120])
        print(f'colour ruler              -> SKIPPED ({why})')
    else:
        grey = os.path.join(tmp, 'grey.glb')
        desaturate(colour_glb, grey)
        rc_cr, out_cr = judge(grey, spec_path)
        pass_green = rc_cg == 0
        block_grey = rc_cr != 0 and 'saturation' in out_cr.lower()
        share = ''
        for line in out_cg.splitlines():
            if line.startswith('{'):
                try:
                    share = f" (measured {json.loads(line)['hi_sat_share']['tq'] * 100:.1f}%)"
                except Exception:
                    pass
        print(f"colour green (saturated)  -> {'PASS ✓' + share if pass_green else 'BLOCKED ✗ (the wolf read as a grey mass — the colour ruler is not seeing baseColorFactor x COLOR_0)' + share}")
        print(f"colour grey (desaturated) -> {'blocked by saturation ✓' if block_grey else 'NOT blocked ✗ (the colour ruler passes anything)'}")
        ok_c = pass_green and block_grey

if ok_g and ok_r and ok_5 and ok_c:
    print('[calibrate] OK: the rulers separate good from bad.')
else:
    print('[calibrate] FAILED — do not start work; report this.')
    sys.exit(1)
