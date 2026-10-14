"""validate.py - check finished creature assets; writes report.json, exit 1 on any error.

    python validate.py <asset_dir>  [--no-rig]          (numpy only; raw GLB parse, no extra deps)

textured.glb : mesh present, TEXCOORD_0, material baseColorTexture -> image present, triangle count, size.
rigged.glb   : mesh + skin, joints >= 2, inverseBindMatrices count == joints, JOINTS_0/WEIGHTS_0,
               weights sum ~1 (|s-1| < 0.01 for all verts), animations 'idle' and 'walk' with channels.
lp_1500/5000.obj : face counts. Missing rigged.glb is an error unless --no-rig or rig_skip.json exists.
"""
import json, os, struct, sys
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
LIMITS = dict(textured_tris=(1000, 2_000_000), rigged_tris=(500, 100_000), textured_mb=80, rigged_mb=40)


def load_glb(p):
    b = open(p, 'rb').read()
    magic, ver, ln = struct.unpack_from('<III', b, 0)
    assert magic == 0x46546C67, 'not a GLB'
    o, js, bin_ = 12, None, b''
    while o < ln:
        cl, ct = struct.unpack_from('<II', b, o); d = b[o + 8:o + 8 + cl]
        if ct == 0x4E4F534A: js = json.loads(d)
        elif ct == 0x004E4942: bin_ = d
        o += 8 + cl
    return js, bin_


def acc(g, bin_, i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']]); n = NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); stride = bv.get('byteStride', 0)
    if stride and stride != dt.itemsize * n:
        raw = np.frombuffer(bin_, np.uint8, a['count'] * stride, off).reshape(a['count'], stride)[:, :dt.itemsize * n]
        x = raw.copy().view(dt).reshape(a['count'], n)
    else:
        x = np.frombuffer(bin_, dt, a['count'] * n, off).reshape(a['count'], n)
    if a.get('normalized'): x = x.astype(np.float32) / np.iinfo(dt).max
    return x


def tris(g, bin_):
    t = 0
    for m in g.get('meshes', []):
        for p in m['primitives']:
            if p.get('mode', 4) != 4: continue
            t += (g['accessors'][p['indices']]['count'] if 'indices' in p else g['accessors'][p['attributes']['POSITION']]['count']) // 3
    return t


def check_textured(p, E, R):
    g, bin_ = load_glb(p); r = R['textured'] = dict(size_mb=round(os.path.getsize(p) / 2**20, 2))
    prims = [q for m in g.get('meshes', []) for q in m['primitives']]
    if not prims: E.append('textured: no mesh'); return
    r['tris'] = tris(g, bin_); r['verts'] = sum(g['accessors'][q['attributes']['POSITION']]['count'] for q in prims)
    if not all('TEXCOORD_0' in q['attributes'] for q in prims): E.append('textured: primitive without TEXCOORD_0 (UV)')
    else:
        uv = np.concatenate([acc(g, bin_, q['attributes']['TEXCOORD_0']) for q in prims])
        r['uv_range'] = [round(float(uv.min()), 3), round(float(uv.max()), 3)]
        if not np.isfinite(uv).all(): E.append('textured: non-finite UVs')
    mats = g.get('materials', [])
    bct = [m.get('pbrMetallicRoughness', {}).get('baseColorTexture') for m in mats]
    if not any(bct): E.append('textured: no baseColorTexture')
    else:
        ti = next(x for x in bct if x)['index']; src = g['textures'][ti].get('source')
        img = g.get('images', [])[src] if src is not None and src < len(g.get('images', [])) else None
        if img is None: E.append('textured: baseColor texture has no image')
        else:
            r['basecolor_mime'] = img.get('mimeType')
            if 'bufferView' in img:
                r['basecolor_kb'] = round(g['bufferViews'][img['bufferView']]['byteLength'] / 1024)
                if r['basecolor_kb'] < 4: E.append('textured: baseColor image suspiciously small')
    r['textures'] = len(g.get('textures', []))
    lo, hi = LIMITS['textured_tris']
    if not lo <= r['tris'] <= hi: E.append(f'textured: tris {r["tris"]} outside [{lo},{hi}]')
    if r['size_mb'] > LIMITS['textured_mb']: E.append(f'textured: {r["size_mb"]} MB > {LIMITS["textured_mb"]}')


def check_rigged(p, E, R):
    g, bin_ = load_glb(p); r = R['rigged'] = dict(size_mb=round(os.path.getsize(p) / 2**20, 2))
    prims = [q for m in g.get('meshes', []) for q in m['primitives']]
    if not prims: E.append('rigged: no mesh'); return
    r['tris'] = tris(g, bin_)
    skins = g.get('skins', [])
    if not skins: E.append('rigged: no skin'); return
    sk = skins[0]; nj = len(sk.get('joints', [])); r['joints'] = nj
    if nj < 2: E.append(f'rigged: only {nj} joints')
    if 'inverseBindMatrices' not in sk: E.append('rigged: no inverseBindMatrices')
    else:
        ibm = acc(g, bin_, sk['inverseBindMatrices']); r['ibm'] = len(ibm)
        if len(ibm) != nj: E.append(f'rigged: {len(ibm)} inverse binds for {nj} joints')
        if not np.isfinite(ibm).all(): E.append('rigged: non-finite inverse binds')
    if not any('skin' in n for n in g.get('nodes', [])): E.append('rigged: no node references the skin')
    ws = []
    for q in prims:
        at = q['attributes']
        if 'JOINTS_0' not in at or 'WEIGHTS_0' not in at: E.append('rigged: primitive without JOINTS_0/WEIGHTS_0'); continue
        w = acc(g, bin_, at['WEIGHTS_0']).astype(np.float64); j = acc(g, bin_, at['JOINTS_0'])
        ws.append(w.sum(1))
        if j.max() >= nj: E.append(f'rigged: joint index {int(j.max())} >= {nj}')
    if ws:
        s = np.concatenate(ws); r['weight_sum'] = [round(float(s.min()), 4), round(float(s.max()), 4)]
        bad = int((abs(s - 1) > 0.01).sum()); r['weight_bad_verts'] = bad
        if bad: E.append(f'rigged: {bad} verts with weight sum off 1 by >0.01')
    an = {a.get('name'): len(a.get('channels', [])) for a in g.get('animations', [])}; r['animations'] = an
    for need in ('idle', 'walk'):
        if not an.get(need): E.append(f'rigged: animation {need!r} missing or empty')
    lo, hi = LIMITS['rigged_tris']
    if not lo <= r['tris'] <= hi: E.append(f'rigged: tris {r["tris"]} outside [{lo},{hi}]')
    if r['size_mb'] > LIMITS['rigged_mb']: E.append(f'rigged: {r["size_mb"]} MB > {LIMITS["rigged_mb"]}')


def obj_faces(p):
    n = 0
    for l in open(p):
        if l.startswith('f '): n += 1
    return n


def main(d, no_rig=False):
    E, W, R = [], [], {'dir': d}
    for f, fn in (('textured.glb', check_textured), ('rigged.glb', check_rigged)):
        p = f'{d}/{f}'
        if os.path.exists(p):
            try: fn(p, E, R)
            except Exception as e: E.append(f'{f}: unreadable ({type(e).__name__}: {e})')
        elif f == 'rigged.glb' and (no_rig or os.path.exists(f'{d}/rig_skip.json')):
            W.append('rigged.glb absent: rig skipped' + (f' ({json.load(open(d + "/rig_skip.json")).get("why")})' if os.path.exists(f'{d}/rig_skip.json') else ''))
        else: E.append(f'{f} missing')
    for b in (1500, 5000):
        p = f'{d}/lp_{b}.obj'
        if os.path.exists(p): R[f'lp_{b}_faces'] = obj_faces(p)
        else: W.append(f'lp_{b}.obj missing')
    R['files'] = {f: os.path.getsize(f'{d}/{f}') for f in sorted(os.listdir(d)) if os.path.isfile(f'{d}/{f}')}
    R['errors'], R['warnings'], R['ok'] = E, W, not E
    json.dump(R, open(f'{d}/report.json', 'w'), indent=1)
    for w in W: print('WARN ', w)
    for e in E: print('ERROR', e)
    print(('VALID ' if not E else 'INVALID ') + d + f'  (report.json; textured tris {R.get("textured", {}).get("tris")}, rigged joints {R.get("rigged", {}).get("joints")})')
    return 0 if not E else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], '--no-rig' in sys.argv))
