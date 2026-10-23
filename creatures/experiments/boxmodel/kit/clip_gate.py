#!/usr/bin/env python3
"""clip_gate.py - the stage-4 clip gate (QA, optional repair, contact sheet). kit/clipkit.py measures and
repairs inside Blender; run.py <prog> --clips calls gate().

    py -3.11 creatures/experiments/boxmodel/kit/clip_gate.py <glb> <outdir> [--fix out.glb] [--tag s4] [--no-sheet]

Gates (every clip): ground penetration <= 0.5 % H below the rest floor; planted-foot slide (std of planted
sole speed, the game_pack metric) <= 0.3 % H/frame; idle/attack planted sole speed <= 0.3 % H/frame (a plant
must stay put; move clips may treadmill); loop gap <= 0.5 % H; no NaN keys; no flipped quaternion keys.
--fix: writes the repaired GLB (animation only), re-measures the written file, and checks that the mesh
(positions) and skin (joint names + weights per vertex) are identical to the input.
Writes <outdir>/<tag>_clips.json and <outdir>/<tag>_clip_sheet.jpg. Exit 0 only when every gate passed.
"""
import json, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
import run as R

GATES = dict(penetration_pctH=0.5, foot_slide_std_pctH=0.3, loop_gap_pctH=0.5)
PLANT_SPEED = 0.3        # idle / attack only
CLIPS = ('idle', 'move', 'attack')


def judge(clips):
    ok, lines = True, []
    for n, c in sorted(clips.items()):
        bad = [f'{k} {c[k]} > {v}' for k, v in GATES.items() if c.get(k, 0) > v]
        if n != 'move' and c.get('foot_speed_planted_pctH', 0) > PLANT_SPEED:
            bad.append(f"plant speed {c['foot_speed_planted_pctH']} > {PLANT_SPEED}")
        if c.get('nan_keys'):
            bad.append(f"NaN keys {c['nan_keys']}")
        if c.get('quat_flips'):
            bad.append(f"quat flips {c['quat_flips']}")
        ok &= not bad
        lines.append(f"BMK clip {n:7s} {'PASS' if not bad else 'FAIL'}  pen {c['penetration_pctH']:.3f}  slide {c['foot_slide_std_pctH']:.3f}"
                     f"  plant {c.get('foot_speed_planted_pctH', 0):.3f}  loop {c['loop_gap_pctH']:.3f}" + ('  ' + '; '.join(bad) if bad else ''))
    return ok, lines


# ---------------- glb mesh / skin identity ----------------
def _glb(path):
    b = open(path, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    js = json.loads(b[20:20 + n]); off = 20 + n
    bn = struct.unpack_from('<I', b, off)[0]
    return js, b[off + 8: off + 8 + bn]


def _acc(js, bin_, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    ct = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}[a['componentType']]
    nc = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = bv.get('byteStride', 0) or np.dtype(ct).itemsize * nc
    raw = np.frombuffer(bin_, np.uint8, count=st * (a['count'] - 1) + np.dtype(ct).itemsize * nc, offset=o)
    out = np.lib.stride_tricks.as_strided(raw, (a['count'], np.dtype(ct).itemsize * nc), (st, 1)).copy()
    out = out.view(ct).reshape(a['count'], nc).astype(np.float64)
    if a.get('normalized') and ct != np.float32:
        out /= np.iinfo(ct).max
    return out


def mesh_signature(path):
    js, bin_ = _glb(path)
    nodes = js['nodes']; rows = []
    for nd in nodes:
        if 'mesh' not in nd:
            continue
        joints = [nodes[j].get('name', str(j)) for j in js['skins'][nd['skin']]['joints']] if 'skin' in nd else []
        for p in js['meshes'][nd['mesh']]['primitives']:
            at = p['attributes']
            P = _acc(js, bin_, at['POSITION'])
            J = _acc(js, bin_, at['JOINTS_0']) if 'JOINTS_0' in at else None
            Wt = _acc(js, bin_, at['WEIGHTS_0']) if 'WEIGHTS_0' in at else None
            for k in range(len(P)):
                w = {}
                if J is not None:
                    for j, x in zip(J[k], Wt[k]):
                        if x > 1e-3:
                            w[joints[int(j)]] = w.get(joints[int(j)], 0) + x
                rows.append((nd.get('name', ''), tuple(np.round(P[k], 4)), w))
    return rows


def same_mesh(a, b):
    A, B = mesh_signature(a), mesh_signature(b)
    da = {}
    for n, p, w in A:
        da.setdefault((p,), []).append(w)
    if len(A) != len(B):
        return False, f'vertex count {len(A)} -> {len(B)}'
    worst = 0.0; miss = 0
    for n, p, w in B:
        c = da.get((p,))
        if not c:
            miss += 1; continue
        d = min(max([abs(w.get(k, 0) - x.get(k, 0)) for k in set(w) | set(x)] or [0]) for x in c)
        worst = max(worst, d)
    ok = miss == 0 and worst < 0.01
    return ok, f'verts {len(B)}, unmatched positions {miss}, max weight diff {worst:.4f}'


def _write_glb(path, js, bin_):
    j = json.dumps(js, separators=(',', ':')).encode()
    j += b' ' * (-len(j) % 4); bin_ += b'\0' * (-len(bin_) % 4)
    js_len = len(j); total = 12 + 8 + js_len + 8 + len(bin_)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', js_len, 0x4E4F534A)); f.write(j)
        f.write(struct.pack('<II', len(bin_), 0x004E4942)); f.write(bin_)


def splice(orig, anim_src, out):
    """out = orig (meshes, skins, nodes, materials byte-identical in content) + the animations of anim_src.
    Channels are re-targeted by node name; orig's old animation data is dropped."""
    A, abin = _glb(orig)
    S, sbin = _glb(anim_src)
    keep_acc = set()
    for m in A.get('meshes', []):
        for p in m['primitives']:
            keep_acc |= set(p['attributes'].values())
            if 'indices' in p:
                keep_acc.add(p['indices'])
            for t in p.get('targets', []):
                keep_acc |= set(t.values())
    for s in A.get('skins', []):
        if 'inverseBindMatrices' in s:
            keep_acc.add(s['inverseBindMatrices'])
    keep_bv = {A['accessors'][i]['bufferView'] for i in keep_acc if 'bufferView' in A['accessors'][i]}
    keep_bv |= {im['bufferView'] for im in A.get('images', []) if 'bufferView' in im}
    new_bin = bytearray(); bvs = []; bv_map = {}

    def add_view(bv, src):
        o = bv.get('byteOffset', 0)
        new_bin.extend(b'\0' * (-len(new_bin) % 4))
        nb = dict(bv); nb['buffer'] = 0; nb['byteOffset'] = len(new_bin)
        new_bin.extend(src[o:o + bv['byteLength']])
        bvs.append(nb)
        return len(bvs) - 1
    for i in sorted(keep_bv):
        bv_map[i] = add_view(A['bufferViews'][i], abin)
    accs = []; acc_map = {}
    for i in sorted(keep_acc):
        a = dict(A['accessors'][i])
        if 'bufferView' in a:
            a['bufferView'] = bv_map[a['bufferView']]
        accs.append(a); acc_map[i] = len(accs) - 1
    for m in A.get('meshes', []):
        for p in m['primitives']:
            p['attributes'] = {k: acc_map[v] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = acc_map[p['indices']]
            if 'targets' in p:
                p['targets'] = [{k: acc_map[v] for k, v in t.items()} for t in p['targets']]
    for s in A.get('skins', []):
        if 'inverseBindMatrices' in s:
            s['inverseBindMatrices'] = acc_map[s['inverseBindMatrices']]
    for im in A.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = bv_map[im['bufferView']]
    jset = {j for sk in A.get('skins', []) for j in sk['joints']}
    by_name = {n.get('name'): i for i, n in enumerate(A['nodes']) if i not in jset}
    by_name.update({A['nodes'][i].get('name'): i for i in jset})   # a bone and a mesh may share a name: the joint wins
    sbv_map = {}; anims = []
    for an in S.get('animations', []):
        samplers = []
        for sm in an['samplers']:
            ns = dict(sm)
            for k in ('input', 'output'):
                a = dict(S['accessors'][sm[k]])
                if a['bufferView'] not in sbv_map:
                    sbv_map[a['bufferView']] = add_view(S['bufferViews'][a['bufferView']], sbin)
                a['bufferView'] = sbv_map[a['bufferView']]
                accs.append(a); ns[k] = len(accs) - 1
            samplers.append(ns)
        chans = []
        for ch in an['channels']:
            nm = S['nodes'][ch['target']['node']].get('name')
            if nm not in by_name:
                raise RuntimeError(f'splice: node {nm} missing in {orig}')
            chans.append(dict(sampler=ch['sampler'], target=dict(node=by_name[nm], path=ch['target']['path'])))
        anims.append(dict(name=an.get('name'), samplers=samplers, channels=chans))
    A['animations'] = anims; A['accessors'] = accs; A['bufferViews'] = bvs
    A['buffers'] = [dict(byteLength=len(new_bin))]
    _write_glb(out, A, bytes(new_bin))


def same_rest(a, b):
    """joint rest TRS of a and b match by name (animation values are absolute local TRS)."""
    A, _ = _glb(a); B, _ = _glb(b)
    jn = {A['nodes'][j].get('name') for s in A.get('skins', []) for j in s['joints']}
    bj = {j for sk in B.get('skins', []) for j in sk['joints']}
    bn = {n.get('name'): n for i, n in enumerate(B['nodes']) if i not in bj}
    bn.update({B['nodes'][i].get('name'): B['nodes'][i] for i in bj})
    worst = 0.0
    aj = {j for sk in A.get('skins', []) for j in sk['joints']}
    for i, n in enumerate(A['nodes']):
        if i in aj and n['name'] in bn:
            m = bn[n['name']]
            for k, d in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])):
                x, y = np.array(n.get(k, d)), np.array(m.get(k, d))
                if k == 'rotation' and np.dot(x, y) < 0:
                    y = -y
                worst = max(worst, float(np.abs(x - y).max()))
    return worst


# ---------------- sheet ----------------
def compose(rep, out, title):
    rows = []
    for tag in ('before', 'after', 'qa'):
        ps = rep.get(f'sheet_{tag}') or (rep.get('sheet') if tag == 'qa' else None)
        if ps:
            rows.append((tag, ps))
    if not rows:
        return None
    tw, th = 240, 200
    n = max(len(p) for _, p in rows)
    im = Image.new('RGB', (n * tw, 40 + len(rows) * (th + 22)), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((8, 8), title, fill=(0, 0, 0), font=R.font(20))
    for r, (tag, ps) in enumerate(rows):
        y = 40 + r * (th + 22)
        for c, p in enumerate(ps):
            if os.path.exists(p):
                im.paste(Image.open(p).convert('RGB').resize((tw, th)), (c * tw, y + 20))
            d.text((c * tw + 4, y + 2), f'{tag}: ' + os.path.basename(p)[len(tag) + 1:-4], fill=(0, 0, 0), font=R.font(13))
    im.save(out, quality=88)
    return out


def gate(glb, outdir, scr, tag='s4', fix=None, sheet=True, title='', base=None, cfg=None):
    """glb = clips source; base = GLB whose meshes/skin/nodes are kept (default glb)."""
    base = base or glb
    cargs = ['--cfg', os.path.abspath(cfg)] if cfg and os.path.exists(cfg) else []   # per-creature clips.json
    os.makedirs(outdir, exist_ok=True); os.makedirs(scr, exist_ok=True)
    qa = os.path.join(outdir, f'{tag}_clips.json')
    frames = os.path.abspath(os.path.join(outdir, f'{tag}_frames'))
    fixrep = None
    if fix:   # repair in Blender -> tmp glb; splice its animations onto the untouched source glb
        tmp = os.path.join(scr, f'clips_{tag}_blender.glb'); fq = os.path.join(scr, f'clips_{tag}_fix.json')
        args = ['--glb', os.path.abspath(glb), '--qa', fq, '--fix', tmp] + (['--sheet', frames] if sheet else []) + cargs
        rc, lines, tb = R.blender(os.path.join(KIT, 'clipkit.py'), args, os.path.join(scr, f'clips_{tag}_fix.log'))
        if tb or not os.path.exists(tmp):
            return False, ['BMK clip fix: Blender error'] + tb, None, None
        fixrep = json.load(open(fq))
        splice(base, tmp, fix)
    src = fix or glb
    args = ['--glb', os.path.abspath(src), '--qa', qa] + (['--sheet', frames, '--sheet-tag', 'after' if fix else 'qa'] if sheet else []) + cargs
    rc, lines, tb = R.blender(os.path.join(KIT, 'clipkit.py'), args, os.path.join(scr, f'clips_{tag}.log'))
    if tb or not os.path.exists(qa):
        return False, ['BMK clip gate: Blender error'] + tb, None, None
    rep = json.load(open(qa))
    if fixrep:
        rep.update(before=fixrep['before'], fix=fixrep['fix'], sheet_before=fixrep.get('sheet_before'),
                   blender_roundtrip=fixrep['clips'], rest_drift=same_rest(base, fix))
    ok, out = judge(rep['clips'])
    miss = [c for c in CLIPS if c not in rep['clips']]
    if miss:
        ok = False; out.append(f'BMK clip set FAIL: missing {miss}')
    if fix:
        mok, msg = same_mesh(base, fix)
        ok &= mok
        out.append(f"BMK clip mesh/skin identity {'PASS' if mok else 'FAIL'}: {msg}")
        rep['mesh_identity'] = dict(ok=mok, detail=msg)
        for n, c in sorted(rep.get('before', {}).items()):
            out.insert(0, f"BMK clip before {n:7s} pen {c['penetration_pctH']:.3f}  slide {c['foot_slide_std_pctH']:.3f}"
                          f"  plant {c.get('foot_speed_planted_pctH', 0):.3f}  loop {c['loop_gap_pctH']:.3f}")
    out.append(f"BMK clip gate {'PASS' if ok else 'FAIL'} (feet {rep['feet']}, gait {rep.get('gait')})")
    rep['gate'] = dict(ok=ok, lines=out)
    json.dump(rep, open(qa, 'w'), indent=1)
    sh = compose(rep, os.path.join(outdir, f'{tag}_clip_sheet.jpg'), title or os.path.basename(glb)) if sheet else None
    return ok, out, rep, sh


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); return 2
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    scr = get('--scratch', a[1])
    ok, lines, _, sh = gate(a[0], a[1], scr, tag=get('--tag', 's4'), fix=get('--fix'), sheet='--no-sheet' not in a,
                            title=get('--title', ''))
    for l in lines:
        print(l)
    print('BMK clip sheet:', sh)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
