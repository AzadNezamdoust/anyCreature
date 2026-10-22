#!/usr/bin/env python3
"""rom_gate.py - ROM sweep gate on a rigged GLB (kit/rom_probe.py measures in headless Blender).

    py -3.11 creatures/experiments/boxmodel/kit/rom_gate.py <glb> <outdir> [--tag t] [--joints joints.json|auto]
                                                             [--reweight cfg.json|default] [--no-render]
Gates per pose (single joint at its limit): volume kept >= 0.70, edge stretch <= 2.0, flipped tris <= 0,
new self-overlap pairs <= max(overlap_new_max, overlap_new_frac * region tris) (auto joints: frac 0.05).
Writes <outdir>/<tag>.json, pose renders and joint crops. run.py <prog> --rom calls gate(). Exit 0 only on PASS.
"""
import json, os, sys

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
import run as R


def gate(glb, outdir, scr, tag='rom', joints='auto', reweight=None, render=True):
    os.makedirs(outdir, exist_ok=True)
    args = [glb, outdir, '--tag', tag, '--joints', joints] + (['--reweight', reweight] if reweight else []) \
        + ([] if render else ['--no-render'])
    rc, lines, tb = R.blender(os.path.join(KIT, 'rom_probe.py'), args, os.path.join(scr, f'rom_{tag}.log'))
    jp = os.path.join(outdir, f'{tag}.json')
    if tb or not os.path.exists(jp):
        return False, lines + tb, None
    rep = json.load(open(jp, encoding='utf-8'))
    return bool(rep['summary']['ok']), lines, rep


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    out = os.path.abspath(a[1])
    ok, lines, rep = gate(os.path.abspath(a[0]), out, out, opt('--tag', 'rom'), opt('--joints', 'auto'),
                          opt('--reweight'), '--no-render' not in a)
    for l in lines:
        print(l)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
