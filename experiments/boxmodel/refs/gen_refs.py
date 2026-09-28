#!/usr/bin/env python3
"""Multi-view reference sheets for the N/G/O test, made on the owner's SUBSCRIPTIONS (no API keys).

    py -3.11 experiments/boxmodel/refs/gen_refs.py --provider gemini|gpt [--creatures a,b] [--attempt N] [--model ID]

  gemini  Antigravity CLI `agy --print` (Google AI Ultra login); its agent calls `generate_image`.
          Default agent model gemini-3.8-flash-high.
  gpt     Codex CLI `codex exec` (ChatGPT login); the model's built-in `image_gen` tool.
          Default model gpt-6-astra, reasoning effort low.

The method follows D:/Git/checkout/tools/LLMModeling (research/v7/IMAGEGEN-AB.md, 2026-09-27): ONE image holding
a 2 x 2 orthographic turnaround (side, front, rear, top) beats one image per view for both generators. The prompt is
byte-identical for both providers and is built from refs/briefs/briefs.json, the briefs every setting shares.

Output: experiments/boxmodel/refs/<provider>/<creature>/sheet_<attempt>.png + meta_<attempt>.json (the reply, the
command line minus the prompt, the time). Invocation lessons from the owner's other projects:
  - codex exec waits on stdin when it has no TTY: stdin is closed; it runs from the output directory;
  - the codex binary sits under a hash folder that changes with app updates: resolved at run time;
  - agy's agent wanders after generating: it is told to call generate_image once and reply with the path only.
"""
import argparse, glob, json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
BRIEFS = json.load(open(os.path.join(HERE, 'briefs', 'briefs.json'), encoding='utf-8'))
LOCAL = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))

SHEET = (
    "One image: a 2 x 2 orthographic turnaround sheet of ONE stylised low-poly 3D game creature, four views of the "
    "same creature: top-left the SIDE view, top-right the FRONT view, bottom-left the REAR view, bottom-right the TOP "
    "view. All four views at one common scale (the same number of pixels per metre in every view), each centred in its "
    "own quarter, separated by wide plain white gutters with NO lines between the quarters. No text, no labels, no "
    "numbers, no arrows, no frames, no borders, no divider lines. "
    "The creature: {desc}. Size: {size}. Pose: {pose}, the same pose in every view. "
    "The views: "
    "SIDE view: looking straight at the creature's left flank, its head pointing to the LEFT of the image. "
    "FRONT view: a straight-on front elevation, looking exactly head-on at its face; the creature is left-right "
    "symmetric about the vertical centre line of its quarter, its body hidden behind its chest, never a three-quarter "
    "view; the creature's left flank is on the RIGHT of the image. "
    "REAR view: a straight-on rear elevation, looking exactly tail-on; left-right symmetric about the centre line, its "
    "body hidden behind its rump, never a three-quarter view; its left flank is on the LEFT of the image. "
    "TOP view: a plan view looking straight down; its head points to the LEFT of the image and its left flank is at the "
    "BOTTOM of the image. "
    "Each feature appears only in the views that can see it. Each view is a true orthographic projection, no perspective. "
    "Style: stylised low-poly 3D game creature, faceted flat-shaded planes, flat colours ({palette}), soft even light, "
    "no cast shadows, plain pure white background.")


REF_SENTENCE = (' The reference image shows this exact character design: keep its design exactly (the same parts, shapes, '
                'colours and proportions); only the viewing direction changes.')


def prompt_for(c, ref=None):
    b = BRIEFS[c]
    return (REF_SENTENCE.strip() + ' ' if ref else '') + SHEET.format(desc=b['image_description'], size=b['size'], pose=b['pose'],
                        palette=', '.join(n for n, _ in b['palette']))


def codex_exe():
    hits = sorted(glob.glob(os.path.join(LOCAL, 'OpenAI', 'Codex', 'bin', '*', 'codex.exe')), key=os.path.getmtime)
    if not hits:
        sys.exit('no codex.exe under %LOCALAPPDATA%/OpenAI/Codex/bin (is the Codex app installed and signed in?)')
    return hits[-1]


def agy_exe():
    p = os.environ.get('AGY_BIN') or os.path.join(LOCAL, 'agy', 'bin', 'agy.exe')
    if not os.path.exists(p):
        sys.exit(f'no agy at {p} (Antigravity CLI; set AGY_BIN)')
    return p


def run(cmd, cwd, timeout):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=timeout)
    return r, time.time() - t0


def gen_gemini(prompt, work, model, ref=None):
    png = os.path.join(work, 'sheet.png')
    instruction = ' '.join([
        f'Use your generate_image tool ONCE to create this image and save the PNG file as {png}',
        (f'Pass the image {ref} to generate_image as its reference image (ImagePaths).' if ref else ''),
        '(the file must exist on disk when you finish). Do not list folders or do anything else.',
        f'Prompt for the image: {prompt}',
        'Reply with the saved path and the image model used, nothing else.'])
    cmd = [agy_exe(), '--print', instruction, '--add-dir', work] + (['--add-dir', os.path.dirname(ref)] if ref else []) + [
           '--dangerously-skip-permissions', '--effort', 'high',
           '--output-format', 'text', '--print-timeout', '8m', '--model', model]
    r, dt = run(cmd, work, 11 * 60)
    return png, r, dt, cmd[:1] + ['--print', '<instruction>'] + cmd[3:]


def gen_gpt(prompt, work, model, ref=None):
    png = os.path.join(work, 'sheet.png')
    msg = f'{prompt} Use your built-in image generation tool once, and save the image as sheet.png in the current directory.'
    last = os.path.join(work, 'reply.txt')
    cmd = [codex_exe(), 'exec', '--skip-git-repo-check', '-s', 'workspace-write', '-m', model,
           '-c', 'model_reasoning_effort="low"', '-o', last] + (['-i', ref, '--'] if ref else []) + [msg]   # -i takes many files: end it with --
    r, dt = run(cmd, work, 25 * 60)
    if not os.path.exists(png):            # the tool sometimes names the file itself
        pngs = sorted(glob.glob(os.path.join(work, '*.png')), key=os.path.getmtime)
        if pngs:
            shutil.move(pngs[-1], png)
    return png, r, dt, cmd[:-1] + ['<prompt>']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['gemini', 'gpt'], required=True)
    ap.add_argument('--creatures', default=','.join(BRIEFS))
    ap.add_argument('--attempt', type=int, default=1)
    ap.add_argument('--model')
    ap.add_argument('--ref', help='a concept image both providers get as the design reference')
    a = ap.parse_args()
    model = a.model or ('gemini-3.8-flash-high' if a.provider == 'gemini' else 'gpt-6-astra')
    ok = True
    for c in a.creatures.split(','):
        out = os.path.join(HERE, a.provider, c)
        os.makedirs(out, exist_ok=True)
        ref = os.path.abspath(a.ref) if a.ref else None
        p = prompt_for(c, ref)
        work = tempfile.mkdtemp(prefix=f'refs-{a.provider}-{c}-')
        png, r, dt, shown = (gen_gemini if a.provider == 'gemini' else gen_gpt)(p, work, model, ref)
        good = os.path.exists(png) and os.path.getsize(png) > 20000
        dst = os.path.join(out, f'sheet_{a.attempt}.png')
        if good:
            shutil.copy(png, dst)
        reply = (r.stdout or '')[-1500:]
        json.dump(dict(provider=a.provider, model=model, attempt=a.attempt, ok=good, seconds=round(dt, 1), exit=r.returncode,
                       prompt=p, reference=a.ref, command=shown, reply=reply, stderr=(r.stderr or '')[-800:],
                       created=time.strftime('%Y-%m-%d %H:%M:%S')),
                  open(os.path.join(out, f'meta_{a.attempt}.json'), 'w', encoding='utf-8'), indent=1)
        print(f'{c}: {"OK " + os.path.relpath(dst, HERE) if good else "FAIL (no image; see meta)"}  {dt:.0f}s  exit {r.returncode}')
        ok &= good
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
