"""ref_critic.py - anatomy critic slot for the reference stage (runs before shape). System python.

    python ref_critic.py <inbox_dir> --species roach [--regen N] [--server] [--image other.png] [--critic CMD]

Checks <inbox_dir>/hero.png against anatomy_checklists.json (_default + species) with an Opus critic
(Claude Code headless: `claude -p --model opus`, Read tool only). Writes <inbox_dir>/ref_critic.json.
Exit 0 = pass, 1 = fail, 2 = critic unavailable.
--regen N: on fail, generate N HunyuanDiT candidates (t2i_refs.py, prompts from E:/gen3d/refs.py when the species is
there, else '<species>, full body ...'), critic each, and the first that passes replaces hero.png (old one ->
hero_rejected_<time>.png). With --server the T2I model stays loaded in model_server.py.
--critic CMD: replace the critic with any command that takes the image path + checklist file and prints the JSON
(hook for another model / Nano Banana refs workflow; the slot contract is the JSON below).
Critic JSON: {"pass": bool, "species_guess": str, "checks": [{"item": str, "ok": bool, "note": str}], "summary": str}
"""
import argparse, json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
G = 'E:/gen3d'; VENV = f'{G}/venv/Scripts/python.exe'
CLAUDE = os.environ.get('CLAUDE_BIN') or shutil.which('claude') or os.path.expanduser('~/.local/bin/claude.exe')

PROMPT = """You are a strict anatomy critic for 3D-generation reference images. Use the Read tool to open this image:
{img}
The image should show: {species}.
Check EVERY item below and mark ok=true only if it is clearly visible and true in the image (count legs carefully,
per side; if unsure, ok=false). Items:
{items}
Reply with ONLY one JSON object, no prose, no code fence:
{{"pass": <true only if every item ok>, "species_guess": "<what animal this actually looks like>", "checks": [{{"item": "...", "ok": true, "note": "..."}}], "summary": "<one line>"}}"""


def checklist(species):
    cl = json.load(open(f'{HERE}/anatomy_checklists.json', encoding='utf-8'))
    key = species.split()[0].lower()
    if key not in cl: print(f'WARNING: no checklist for {key!r}; using _default only', flush=True)
    return cl['_default'] + cl.get(key, [])


def critic(img, species, items, cmd=None):
    if cmd:
        tf = img + '.checklist.json'; json.dump(dict(species=species, items=items), open(tf, 'w'))
        out = subprocess.run(cmd.split() + [img, tf], capture_output=True, text=True, encoding='utf-8').stdout
    else:
        if not os.path.exists(CLAUDE): return None
        p = PROMPT.format(img=os.path.abspath(img).replace('\\', '/'), species=species, items='\n'.join(f'- {i}' for i in items))
        r = subprocess.run([CLAUDE, '-p', p, '--model', 'opus', '--allowedTools', 'Read', '--add-dir', os.path.dirname(os.path.abspath(img))],
                           capture_output=True, text=True, encoding='utf-8', timeout=600)
        out = r.stdout
        if r.returncode or 'Not logged in' in out:   # headless Claude not logged in -> leave the prompt for an Opus lane
            open(img + '.critic_prompt.txt', 'w', encoding='utf-8').write(p)
            print(f'critic unavailable ({out.strip()[:60]}); prompt -> {img}.critic_prompt.txt; '
                  f'run it in an Opus lane and pass the JSON back via --critic "python -c ..." or fix `claude /login`', flush=True)
            return None
    m = re.search(r'\{.*\}', out or '', re.S)
    if not m: print('critic output unparsable:', (out or '')[-500:], flush=True); return None
    try: return json.loads(m.group(0))
    except json.JSONDecodeError: print('critic JSON bad:', m.group(0)[-500:], flush=True); return None


def regen(inbox, species, n, server, port=8765):
    d = f'{inbox}/ref_tries'; os.makedirs(d, exist_ok=True)
    args = [d, species, str(n), str(int(time.time()) % 1000 * 10)]
    if server:
        import urllib.request
        j = dict(script=f'{HERE}/t2i_refs.py', argv=args, cwd=G, env={'PYTHONIOENCODING': 'utf-8'}, log=f'{d}/t2i.log')
        urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}/run', data=json.dumps(j).encode(), method='POST'), timeout=7200).read()
    else:
        subprocess.run([VENV, f'{HERE}/t2i_refs.py', *args], cwd=G, check=False)
    return sorted(os.path.join(d, f) for f in os.listdir(d) if re.fullmatch(r't\d+_\d+\.png', f))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('inbox'); ap.add_argument('--species', required=True)
    ap.add_argument('--regen', type=int, default=0); ap.add_argument('--server', action='store_true')
    ap.add_argument('--image'); ap.add_argument('--critic')
    ap.add_argument('--answer', help='critic JSON written by an Opus lane (manual mode when headless claude is unavailable)')
    a = ap.parse_args()
    items = checklist(a.species); img = a.image or f'{a.inbox}/hero.png'
    log = dict(species=a.species, items=items, tries=[])
    t = time.time(); r = json.load(open(a.answer, encoding='utf-8')) if a.answer else critic(img, a.species, items, a.critic)
    log['tries'].append(dict(image=img, result=r, s=round(time.time() - t, 1)))
    if r is None:
        json.dump(log, open(f'{a.inbox}/ref_critic.json', 'w'), indent=1); print('critic unavailable'); sys.exit(2)
    print(('PASS ' if r.get('pass') else 'FAIL ') + img, '|', r.get('species_guess'), '|', r.get('summary'), flush=True)
    for c in r.get('checks', []):
        if not c.get('ok'): print('  x', c.get('item'), '-', c.get('note'))
    ok = bool(r.get('pass'))
    if not ok and a.regen:
        for cand in regen(a.inbox, a.species, a.regen, a.server):
            t = time.time(); rr = critic(cand, a.species, items, a.critic)
            log['tries'].append(dict(image=cand, result=rr, s=round(time.time() - t, 1)))
            print(('PASS ' if rr and rr.get('pass') else 'FAIL ') + cand, '|', rr and rr.get('summary'), flush=True)
            if rr and rr.get('pass'):
                if os.path.exists(f'{a.inbox}/hero.png'):
                    shutil.move(f'{a.inbox}/hero.png', f'{a.inbox}/hero_rejected_{time.strftime("%H%M%S")}.png')
                shutil.copy(cand, f'{a.inbox}/hero.png'); log['replaced_with'] = cand; ok = True; break
    log['pass'] = ok
    json.dump(log, open(f'{a.inbox}/ref_critic.json', 'w'), indent=1)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
