#!/usr/bin/env python3
"""Ship — the whole closing in ONE command: package, then (only if asked) publish.

    python3 harness/ship.py out/creature.glb --name "Ash Wolf" --author "Ariescar"
    python3 harness/ship.py out/creature.glb --name "Ash Wolf" --author "Ariescar" --publish

Without --publish it packages and stops. With --publish it packages and uploads,
and prints the share link and the one-time takedown token. --publish must only
ever be passed after the person has said yes, in this session (card 04).

Why this exists: the closing used to be two commands with the same arguments
typed twice, so the signature drifted between the file and the listing, and the
upload got skipped when the second command was forgotten. One command, one set
of arguments, one report.

The signature is remembered in ~/.anyCreature.json after the first time — pass
--author once, never again; --author on a later run updates it.
"""
import sys, os, json, subprocess, re

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(os.path.expanduser('~'), '.anyCreature.json')


def remembered_author():
    try:
        return (json.load(open(STORE)).get('author') or '').strip() or None
    except Exception:
        return None


def remember_author(a):
    try:
        d = {}
        if os.path.exists(STORE):
            d = json.load(open(STORE))
        d['author'] = a
        json.dump(d, open(STORE, 'w'))
    except Exception:
        pass


def main():
    args = sys.argv[1:]

    def opt(flag, default=None):
        if flag in args:
            i = args.index(flag); v = args[i + 1]; del args[i:i + 2]; return v
        return default

    publish = '--publish' in args
    if publish:
        args.remove('--publish')
    # --upload-only: the package already exists (they said no earlier, or the
    # upload failed). Publish it as-is; never rebuild, never re-stamp.
    upload_only = '--upload-only' in args
    if upload_only:
        args.remove('--upload-only'); publish = True
    name = opt('--name')
    author = opt('--author')
    gate = opt('--gate')
    outdir = opt('--out', 'delivery')
    if not args:
        sys.exit(__doc__)
    src = args[0]
    if not os.path.isfile(src):
        sys.exit(f'[ship] no such model: {src}')

    if author:
        remember_author(author)
    else:
        author = remembered_author()

    slug = re.sub(r'[^A-Za-z0-9_.-]', '_', (name or os.path.basename(src).rsplit('.', 1)[0])).strip('_') or 'creature'

    if upload_only:
        glb = src if src.endswith('.glb') else os.path.join(outdir, f'{slug}.glb')
        outdir = os.path.dirname(os.path.abspath(glb)) or outdir
        hero = os.path.join(outdir, 'hero.png')
        print(f'[ship] uploading the existing package in {outdir}/ (nothing rebuilt)')
        return do_publish(glb, hero, name, author, outdir)

    cmd = ['python3', os.path.join(HERE, 'deliver.py'), src, outdir, slug]
    if name: cmd += ['--title', name]
    if author: cmd += ['--author', author]
    if gate: cmd += ['--gate', gate]
    if subprocess.run(cmd).returncode != 0:
        sys.exit('[ship] delivery failed — nothing was published')

    glb = os.path.join(outdir, f'{slug}.glb')
    hero = os.path.join(outdir, 'hero.png')
    print(f'[ship] packaged → {outdir}/  ({slug}.glb · {slug}_viewer.html · hero · upload/)')

    if not publish:
        print('[ship] not published (no --publish). The files are the deliverable; '
              'pass --publish only after the person says yes.')
        print(f'[ship] to upload later, one command: python3 harness/ship.py {glb} --upload-only')
        return

    return do_publish(glb, hero, name, author, outdir)


def do_publish(glb, hero, name, author, outdir):
    HERE_ = HERE
    pcmd = ['node', os.path.join(HERE_, 'publish.mjs'), glb]
    pcmd += [hero] if os.path.exists(hero) else []
    if name: pcmd += ['--title', name]
    if author: pcmd += ['--creator', author]
    res = subprocess.run(pcmd, capture_output=True, text=True)
    line = (res.stdout or '').strip().splitlines()[-1] if res.stdout.strip() else '{}'
    try:
        r = json.loads(line)
    except Exception:
        sys.exit(f'[ship] publisher said something unreadable:\n{res.stdout}{res.stderr}')

    st = r.get('status')
    # Same lesson as publish.mjs: never let an unrecognised word turn a
    # successful upload into "the server refused". A link is proof of success.
    if st == 'published' or (r.get('share_url') and st not in ('blocked', 'error')):
        print(f'[ship] PUBLISHED → {r["share_url"]}')
    elif st == 'pending_review':
        print('[ship] UPLOADED — the server is verifying it; it will appear shortly.')
    elif st == 'blocked':
        print('[ship] could not reach Gobkit. The upload pack is ready in '
              f'{outdir}/upload/ — drag creature.glb into https://gobkit.com/community/upload '
              '(no account, no key needed).')
    else:
        print(f'[ship] the server refused: {r.get("error", line)}')

    # 認領那條連結,publish.mjs 上傳完會實際去敲一次:
    #   claim_link_live is True  → 敲得到,直接給連結
    #   claim_link_live is None  → 敲不到(離線/被擋),不因為探測失敗就降級
    #   claim_link_live is False → 它真的回 404。這時候給那頁「一定在」的認領頁,
    #                              下面那組碼貼進去一樣認得回來 —— 絕不叫人去點 404。
    fallback = r.get('claim_fallback_url') or 'https://gobkit.com/community/claim'
    if r.get('manage_url') and r.get('claim_link_live') is not False:
        where = r.get('claim_link_file') or r.get('manage_file') or outdir
        print(f'[ship] claim link  (saved to {where}): {r["manage_url"]}')
        print('[ship]   -> open it, sign in with Google, and the model is yours;'
              ' then you can enter it in the Arena')
    elif r.get('manage_token'):
        print(f'[ship] claim page: {fallback}')
        print('[ship]   -> sign in with Google there and paste the code below —'
              ' that is how this model gets listed under your name')
    if r.get('manage_token'):
        where = r.get('manage_token_file') or outdir
        print(f'[ship] takedown code (shown ONCE, saved to {where}): {r["manage_token"]}')
        print('[ship]   -> the only way to take the model down later, and it cannot'
              f' be re-issued. it is also the key you paste at {fallback}')
    # one machine-readable line last, so the calling agent can quote it verbatim
    print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
