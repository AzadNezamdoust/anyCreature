#!/usr/bin/env python3
"""judge_pack.py — blind judging packs outside the repo.

    python kit/judge_pack.py <sheet.jpg | dir | glob> ... [--name NAME] [--out DIR] [--brief FILE ...]

Copies every sheet into a neutral temp dir OUTSIDE the git repo (default: %TEMP%/judge_<NAME>_<rand>/) under a
random id (e.g. 7f3a9c.jpg), so the judge sees no creature name, model name, folder or git history. The key
(id -> original repo-relative path, sha256) is written INSIDE the repo at judge/results/key_<NAME>.json and is
never copied to the pack. Briefs (--brief) are copied as brief_<n>.md. Run the judge agent with its cwd = the
printed pack dir; give it only that dir. Exit 1 if the pack dir would land inside a git work tree.
"""
import argparse, glob, hashlib, json, os, secrets, shutil, sys, tempfile, time

KIT = os.path.dirname(os.path.abspath(__file__))
BOX = os.path.dirname(KIT)
IMG = ('.jpg', '.jpeg', '.png', '.webp')


def in_git(path):
    p = os.path.abspath(path)
    while True:
        if os.path.exists(os.path.join(p, '.git')):
            return True
        up = os.path.dirname(p)
        if up == p:
            return False
        p = up


def sheets(args):
    out = []
    for a in args:
        hits = glob.glob(a) or [a]
        for h in hits:
            if os.path.isdir(h):
                out += sorted(os.path.join(r, f) for r, _, fs in os.walk(h) for f in fs if f.lower().endswith(IMG))
            elif os.path.isfile(h):
                out.append(h)
            else:
                sys.exit(f'no such sheet: {h}')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheets', nargs='+')
    ap.add_argument('--name', default=time.strftime('%Y%m%d_%H%M%S'))
    ap.add_argument('--out', help='pack dir (must be outside any git work tree)')
    ap.add_argument('--brief', nargs='*', default=[])
    a = ap.parse_args()
    files = sheets(a.sheets)
    if not files:
        sys.exit('no sheets')
    out = a.out or os.path.join(tempfile.gettempdir(), f'judge_{secrets.token_hex(4)}')
    if in_git(out):
        sys.exit(f'refusing: {out} is inside a git work tree (judges must run outside the repo)')
    kp = os.path.join(BOX, 'judge', 'results', f'key_{a.name}.json')
    if os.path.exists(kp):
        sys.exit(f'key exists, pick another --name: {kp}')
    os.makedirs(out, exist_ok=True)
    order = list(files)
    secrets.SystemRandom().shuffle(order)                      # pack order carries no information either
    key = dict(name=a.name, pack=out, made=time.strftime('%Y-%m-%d %H:%M:%S'), sheets={})
    used = set()
    for f in order:
        i = secrets.token_hex(3)
        while i in used:
            i = secrets.token_hex(3)
        used.add(i)
        ext = os.path.splitext(f)[1].lower()
        shutil.copyfile(f, os.path.join(out, i + ext))          # copyfile: no metadata, no original name
        key['sheets'][i] = dict(src=os.path.relpath(os.path.abspath(f), BOX).replace('\\', '/'),
                                sha256=hashlib.sha256(open(f, 'rb').read()).hexdigest())
    for n, b in enumerate(a.brief):
        shutil.copyfile(b, os.path.join(out, f'brief_{n}.md'))
    os.makedirs(os.path.dirname(kp), exist_ok=True)
    with open(kp, 'w', encoding='utf-8') as fh:
        json.dump(key, fh, indent=1)
    print(f'pack: {out}  ({len(order)} sheets)')
    print(f'key:  {kp}  (in repo; never give it to the judge)')
    print(f'run the judge with cwd={out}')


if __name__ == '__main__':
    main()
