#!/usr/bin/env python3
"""Wash — rebuild a GLB as a clean, standardised file. Whitelist, not blacklist.

A GLB is a moving box: loaders only look at the furniture they recognise and
SKIP everything else — which is exactly where a bad actor hides an executable
or where private metadata (EXIF GPS, local paths) survives. Scanning for bad
things loses to the next new trick; washing wins by construction: parse the
incoming file and carry ONLY recognised furniture into a brand-new box.
Anything hidden simply does not get moved.

    python3 harness/wash.py <in.glb> <out.glb>       # out may equal in

What survives:   geometry, skeleton, skins, animations, material parameters,
                 texture PIXELS (re-encoded PNG — EXIF/XMP die), sanitised
                 names, and OUR OWN asset fields (whitelisted keys only).
What dies:       extra chunks, trailing bytes, gaps between buffer views,
                 unknown extensions, every foreign `extras`, image metadata.
What REJECTS the file (exit 1, machine-readable reason on stdout):
                 external URIs (a downloader would phone another server),
                 required extensions we cannot parse (Draco/Meshopt),
                 broken images, structures that fail to re-parse.

deliver.py runs this on every delivery; publish.mjs runs it again right
before upload. The harness is open source, so a modified copy can skip this —
the server MUST still keep its own cheap gate (chunk count, no external URI).
Washing here is standardisation and courtesy; the server's gate is the law.
"""
import sys, os, json, struct, io, re

KEEP_TOP = ['scene', 'scenes', 'nodes', 'meshes', 'accessors', 'bufferViews',
            'buffers', 'materials', 'textures', 'images', 'samplers', 'skins',
            'animations', 'cameras']
EXT_WHITELIST = {'KHR_texture_transform', 'KHR_materials_unlit',
                 'KHR_materials_emissive_strength'}
ASSET_EXTRAS_KEYS = {'harness', 'harness_version', 'spec', 'monster', 'author',
                     'license', 'gate', 'parts', 'source_spec'}
MAX_SOURCE_SPEC = 64 * 1024

def fail(reason, detail=''):
    print(json.dumps({'ok': False, 'error': reason, 'detail': detail}))
    sys.exit(1)

def clean_str(s, cap=80):
    if not isinstance(s, str): return None
    s = re.sub(r'[<>\x00-\x1f\x7f]', '', s).strip()
    return s[:cap] if s else None

def strip_obj(o, notes, keep_name=True):
    """Remove extras + unknown extensions from one glTF object, sanitise name."""
    if not isinstance(o, dict): return
    if 'extras' in o:
        del o['extras']; notes.add('foreign extras dropped')
    if 'extensions' in o:
        bad = [k for k in o['extensions'] if k not in EXT_WHITELIST]
        for k in bad:
            del o['extensions'][k]; notes.add(f'extension stripped: {k}')
        if not o['extensions']: del o['extensions']
    if keep_name and 'name' in o:
        nm = clean_str(o['name'])
        if nm is None: o.pop('name', None)
        else: o['name'] = nm

def wash(src_path, out_path):
    try:
        from PIL import Image
    except ImportError:
        fail('missing_dependency', 'pillow (pip install pillow)')
    raw = open(src_path, 'rb').read()
    if raw[:4] != b'glTF' or len(raw) < 20: fail('parse_error', 'not a GLB')
    jlen, jtype = struct.unpack('<II', raw[12:20])
    if jtype != 0x4E4F534A: fail('parse_error', 'first chunk is not JSON')
    try:
        g = json.loads(raw[20:20 + jlen])
    except Exception as e:
        fail('parse_error', str(e)[:120])
    off = 20 + jlen
    body = b''
    if off + 8 <= len(raw):
        blen, btype = struct.unpack('<II', raw[off:off + 8])
        if btype == 0x004E4942: body = raw[off + 8: off + 8 + blen]
    notes = set()
    tail = len(raw) - (off + 8 + len(body) + (-len(body)) % 4)
    if tail > 0: notes.add(f'{tail} trailing bytes discarded')

    # ── red flags that reject the whole file ──
    for b in g.get('buffers', []) or []:
        u = b.get('uri', '')
        if u and not u.startswith('data:'): fail('external_uri', u[:100])
    for im in g.get('images', []) or []:
        u = im.get('uri', '')
        if u and not u.startswith('data:'): fail('external_uri', u[:100])
    for ext in g.get('extensionsRequired', []) or []:
        if ext not in EXT_WHITELIST: fail('unsupported_compression', ext)

    # ── new document: only recognised furniture moves in ──
    out = {}
    for k in KEEP_TOP:
        if k in g: out[k] = g[k]

    # asset: version + whitelisted own fields, everything else dies
    a = g.get('asset', {}) or {}
    na = {'version': '2.0'}
    if isinstance(a.get('generator'), str): na['generator'] = clean_str(a['generator'], 60)
    if isinstance(a.get('copyright'), str): na['copyright'] = clean_str(a['copyright'], 60)
    x = a.get('extras', {}) or {}
    nx = {}
    for k in ASSET_EXTRAS_KEYS:
        if k not in x: continue
        v = x[k]
        if k == 'source_spec':
            try:
                s2 = json.dumps(v, separators=(',', ':'))
                if len(s2) <= MAX_SOURCE_SPEC: nx[k] = json.loads(s2)
                else: notes.add('source_spec over 64KB dropped')
            except Exception: notes.add('source_spec unparseable, dropped')
        elif isinstance(v, str):
            c = clean_str(v)
            if c: nx[k] = c
        else:
            nx[k] = json.loads(json.dumps(v))   # re-serialise: kills exotica
    if nx: na['extras'] = nx
    out['asset'] = na

    # strip extras/unknown extensions on every object that can carry them
    for key in KEEP_TOP:
        for o in (out.get(key) or ([] if key != 'scene' else [])):
            if isinstance(o, dict):
                strip_obj(o, notes)
                for sub in ('pbrMetallicRoughness', 'primitives', 'channels', 'samplers'):
                    v = o.get(sub)
                    if isinstance(v, dict): strip_obj(v, notes, keep_name=False)
                    if isinstance(v, list):
                        for it in v:
                            if isinstance(it, dict): strip_obj(it, notes, keep_name=False)
    if 'extensionsUsed' in g:
        used = [e for e in g['extensionsUsed'] if e in EXT_WHITELIST]
        if used: out['extensionsUsed'] = used
    g.pop('extensionsRequired', None)   # nothing left requires anything

    # ── repack the binary: views copied tightly, images re-encoded ──
    img_view = {im['bufferView']: i for i, im in enumerate(out.get('images', []))
                if isinstance(im, dict) and 'bufferView' in im}
    nbin = bytearray(); nviews = []
    for vi, v in enumerate(out.get('bufferViews', []) or []):
        start = v.get('byteOffset', 0); data = body[start:start + v['byteLength']]
        if vi in img_view:
            try:
                pic = Image.open(io.BytesIO(bytes(data))); pic.load()
                buf = io.BytesIO()
                pic.save(buf, format='PNG', optimize=False)   # pixels only — metadata dies
                data = buf.getvalue()
                out['images'][img_view[vi]]['mimeType'] = 'image/png'
                notes.add('images re-encoded')
            except Exception as e:
                fail('broken_image', str(e)[:120])
        while len(nbin) % 4: nbin.append(0)
        nv = {'buffer': 0, 'byteOffset': len(nbin), 'byteLength': len(data)}
        for k in ('byteStride', 'target'):
            if k in v: nv[k] = v[k]
        nbin.extend(data); nviews.append(nv)
    if nviews:
        out['bufferViews'] = nviews
        out['buffers'] = [{'byteLength': len(nbin)}]
    else:
        out.pop('buffers', None)

    # ── write: exactly two chunks, exact declared length, nothing after ──
    js = json.dumps(out, separators=(',', ':')).encode()
    js += b' ' * ((-len(js)) % 4)
    bb = bytes(nbin) + b'\x00' * ((-len(nbin)) % 4)
    total = 12 + 8 + len(js) + (8 + len(bb) if bb else 0)
    w = bytearray(struct.pack('<4sII', b'glTF', 2, total))
    w += struct.pack('<II', len(js), 0x4E4F534A) + js
    if bb: w += struct.pack('<II', len(bb), 0x004E4942) + bb
    open(out_path, 'wb').write(w)

    # self-check: the washed file must re-parse
    chk = open(out_path, 'rb').read()
    jl2, = struct.unpack('<I', chk[12:16]); json.loads(chk[20:20 + jl2])
    print(json.dumps({'ok': True, 'bytes_in': len(raw), 'bytes_out': len(chk),
                      'notes': sorted(notes)}))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('usage: python3 wash.py <in.glb> <out.glb>')
    wash(sys.argv[1], sys.argv[2])
