#!/usr/bin/env python3
"""Sync check — proves the tree about to ship is INTERNALLY CONSISTENT.

Born from a real leak: before the first public push, two finished features
(part_seat, the browser install) existed in one working copy but not in the
one that got pushed. Three copies, no gatekeeper. This script IS the
gatekeeper: run it before every push (CI runs it too).

    python3 harness/synccheck.py        # exit 0 = ship, exit 1 = stop

What it verifies:
  1. versions agree      VERSION == CHANGELOG's top entry (the engine reads
                         VERSION at build time, so the GLB stamp follows)
  2. promised features   every feature the CHANGELOG promises is present in
                         the code that ships (the 1.2.0 leak class)
  3. required files      everything the cards and scripts point at exists
  4. leak scan           strings that must never appear in a public tree
  5. no dangling docs    a shipped file may not point at a doc that stayed home
  6. no forward refs     nothing ships describing a version that is not out yet
"""
import os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
bad = []

def read(p):
    try:
        return open(os.path.join(ROOT, p), encoding='utf-8').read()
    except OSError:
        return None

# ── 1. versions agree ────────────────────────────────────────────────────────
version = (read('VERSION') or '').strip()
chlog = read('CHANGELOG.md') or ''
m = re.search(r'^## (\d+\.\d+\.\d+)', chlog, re.M)
top = m.group(1) if m else '?'
if not version:
    bad.append('VERSION file missing or empty')
elif top != version:
    bad.append(f'version drift: VERSION says {version}, CHANGELOG top entry says {top}')

# the version is also written into prose and into a README badge; those drift
# silently because nothing reads them back. 1.3.1 shipped with three 1.3.0
# strings still in place, which is how this check got written.
if version:
    for p, pat in (('MANUAL.md', r'anyCreature (\d+\.\d+\.\d+)'),
                   ('MANUAL.md', r'^VERSION\s+(\d+\.\d+\.\d+)'),
                   ('README.md', r'badge/version-(\d+\.\d+\.\d+)')):
        for found in re.findall(pat, read(p) or '', re.M):
            if found != version:
                bad.append(f'version drift: {p} still says {found}, VERSION says {version}')

# ── 2. promised features exist in the shipping code ──────────────────────────
# One line per promise. ADD A LINE WHEN YOU ADD A FEATURE — this list is the
# contract between the release notes and the code.
FEATURES = [
    ('engine/core/checks.js',   'part_seat',        'declared joins / exposed-root check'),
    ('engine/core/checks.js',   'attack_reach',     'attack must lunge'),
    ('engine/core/checks.js',   'gait_direction',   'a planted foot must sweep backward'),
    ('harness/fit.py',          'FIXABLE',          'the arithmetic blocks are applied, not hand-fixed'),
    ('cards/01_LOW.md',         'harness/fit.py',   'the card runs the fitter before the first round'),
    ('engine/core/checks.js',   'root_drive',       'a lunge is driven on the skeleton root'),
    ('harness/pwlaunch.mjs',    'findCachedChromium', 'the cached browser is found before any download'),
    ('engine/core/checks.js',   'touch:',           'declared adjacency'),
    ('engine/core/checks.js',   'part_overlap',     'part interpenetration measure'),
    ('engine/core/checks.js',   'faceted_body',     'faceted volumes blocked'),
    ('engine/core/checks.js',   'soft_mass',        'the rounded-sausage volume is blocked'),
    ('cards/SYNTAX.md',         '"soft": true',     'the soft_mass opt-out is documented'),
    ('engine/core/compile.js',  '_seatIdx',         'parts carry their base ring'),
    ('engine/core/compile.js',  'applyShading',     'whole-body shading pass (1.2.0 fallback)'),
    ('engine/core/shade.js',    'shadeStack',       'L1-L8 vertex-colour stack'),
    ('engine/core/shade.js',    'inGamut',          'L4 chroma walks back to the sRGB edge'),
    ('engine/core/shade.js',    'classOf',          'flesh / hardware / feature classification'),
    ('engine/core/glb.js',      'boneField',        'L8 normals softened toward the bone field'),
    ('engine/core/compile.js',  'chain: m.chain',   'mirrored volumes keep their chain name'),
    ('engine/core/relative.js', 'joints_R',         'right-side pose overrides'),
    ('engine/core/ao.js',       'bakeAO',           'vertex AO bake'),
    ('engine/core/normals.js',  'smoothSplit',      'smoothing-angle normals'),
    ('harness/pwlaunch.mjs',    'launchBrowser',    'shared browser launcher'),
    ('setup.sh',                'playwright install', 'browser installed at setup'),
    ('setup.sh',                'pwprobe',          'browser probed at setup'),
    ('cards/02_MID.md',         'join',             'join doctrine in the MID card'),
    ('cards/SYNTAX.md',         '"join"',           'join in the syntax page'),
    ('engine/core/compile.js',  'buildHand',        'hand part type (palm/fingers/thumb)'),
    ('engine/core/compile.js',  'p.toes',           'paw toes'),
    ('engine/core/checks.js',   'size: spec declares height', 'declared-height gate'),
    ('README.md',               'Read MANUAL.md in this folder and follow it exactly', 'copy-paste agent prompt'),
    ('cards/03_HIGH.md',        'Gait for many legs', 'multi-leg gait doctrine'),
    ('cards/02_MID.md',         '"type":"hand"',    'hands doctrine in MID card'),
    ('cards/01_LOW.md',         'ASSUME EVERY READER IS LAZY', 'reader verification protocol'),
    ('cards/01_LOW.md',         'canary',           'canary decoys in blind reads'),
    ('cards/00_START.md',       'never trust a reader', 'reader distrust doctrine'),
    ('engine/cli.js',           'source_spec',      'embedded birth certificate'),
    ('harness/graft.py',        'source_spec',      'graft tool reads embedded specs'),
    ('cards/SYNTAX.md',         'embed_spec',       'embed opt-out documented'),
    ('harness/glbcheck.mjs',    'checkGLB',         'output conformance checker'),
    ('cards/04_SHIP.md',        'Conformance is automatic', 'card states conformance is enforced, not manual'),
    ('cards/01_LOW.md',         'harness/claims.json', 'single claims sheet, no role tiers'),
    ('cards/01_LOW.md',         'expand the order yourself, never ask', 'thin orders are expanded, not queried'),
    ('cards/01_LOW.md',         'Discard your first three ideas', 'anti-trope rule'),
    ('cards/01_LOW.md',         'ONE question — REQUIRED', 'the single question is mandatory'),
    ('cards/00_START.md',       'Never ask about:', 'forbidden question list'),
    ('engine/cli.js',           'example_copy',     'recoloured-example builds are refused'),
    ('cards/01_LOW.md',         'The verdict is SCORED', 'identity is scored by rank and view count'),
    ('harness/identity.py',     'def verdict',      'the identity score is counted, not argued'),
    ('harness/publish.mjs',     'manage_token',     'one-time takedown token surfaced'),
    ('harness/ship.py',         '--publish',        'one-command closing (package [+ publish])'),
    ('cards/04_SHIP.md',        'ship.py',          'card uses the one-command closing'),
    ('docs/OUTPUT_CONTRACT.md', 'exactly two',      'output contract documented'),
    ('engine/cli.js',           'BLOCK: contract',  'every build is contract-checked'),
    ('harness/deliver.py',      'OUTPUT_CONTRACT',  'delivery re-checks the stamped file'),
    ('harness/deliver.py',      'was not built by this engine', 'delivery refuses foreign GLBs'),
    ('MANUAL.md',               'STOP — read this before you write a single line of code', 'anti-bypass opener'),
    ('harness/publish.mjs',     'checkGLB',         'publish refuses non-conforming files'),
    ('engine/core/glb.js',      'the hue lives in baseColorFactor', 'hue split into the material'),
    ('harness/glbcheck.mjs',    'flat_white_base',  'white-base portability warning'),
    ('harness/glbcheck.mjs',    'high_metal',       'metal-without-environment warning'),
    ('cards/03_HIGH.md',        'Keep `metal` low', 'material limits stated in the card'),
    ('harness/glbcheck.mjs',    'anisotropy_without_direction', 'anisotropy without UV/TANGENT is blocked'),
    ('cards/03_HIGH.md',        'No anisotropy',    'anisotropy limit stated in the card'),
    ('harness/publish.mjs',     'SUCCESS IS NOT A MAGIC WORD', 'upload success is not matched by a literal word'),
    ('harness/judge.mjs',       'ALBEDO = baseColorFactor', 'the colour ruler reads the material, not COLOR_0 alone'),
    ('harness/calibrate.py',    'saturation_area', 'the colour ruler is calibrated both ways'),
    ('harness/roundcheck.py',   'def preflight',    'the reader is gated BEFORE it is spent'),
    ('cards/01_LOW.md',         '--preflight',      'card runs the pre-check before the read'),
    ('cards/01_LOW.md',         'TWO OPPOSITE POLES', 'a round builds two opposite poles, not three near-copies'),
    ('cards/01_LOW.md',         'chains: LClaw, RClaw', 'the brief names the chains it means'),
    ('harness/brief.py',        'POLE_MIN', 'the two-pole floor is a named constant, not a magic number'),
    ('cards/01_LOW.md',         'Two speeds of repair', 'trap repair depends on which trap tripped'),
    ('harness/roundcheck.py',   'def variant_metrics', 'preflight judges a round by its best variant'),
    ('cards/02_MID.md',         'The isolated part read is deleted', 'the isolated part read is gone; MID reads the whole body once'),
    ('harness/round.py',        'def promote',      'a whole round is one command'),
    ('harness/partreads.py',    'ANSWER KEY',       'part reads are built and batched in one command'),
    ('cards/01_LOW.md',         'A whole round is ONE command', 'card uses the one-command round'),
    ('cards/00_START.md',       'The thing that actually costs money: TURNS', 'turn cost stated up front'),
    ('cards/01_LOW.md',         'Build THREE different pushes', 'Gate 2 judges three pushes in one round'),
    ('cards/02_MID.md',         'MID SPENDS NO READER', 'MID spends no reader at all'),
    ('engine/core/checks.js',   'contrast_adjacent', 'part-vs-host colour distance is computed, not read'),
    ('cards/02_MID.md',         'still BLOCKS',     'part presence is a machine check on the spec, not a read'),
    ('engine/core/checks.js',   'value_order',      'the value plan is sorted by the machine, not eyeballed'),
    ('harness/gates.json',      '"kind": "legality"', 'every check is tagged legality vs style'),
    ('harness/gates.json',      '"by": "B"',       'every check names which source judges it'),
    ('cards/01_LOW.md',         'this gate is FINISHED', 'Gate 2 stops when the incumbent wins'),
    ('cards/02_MID.md',         'Author the WHOLE part set in one pass', 'parts are authored in one pass, not incrementally'),
    ('cards/04_SHIP.md',        'ONE line. Not a narrative', 'the closing DEVLOG is one line'),
    ('engine/cli.js',           'ENGINE_CHECKS',    'the engine writes its own gate stamp'),
    ('cards/04_SHIP.md',        'checks.json',      'card 04 copies the stamp instead of retyping it'),
    ('cards/03_HIGH.md',        'Write all three, then build ONCE', 'all three clips authored in one pass'),
    ('harness/outline.py',      'def render_mask',  'silhouettes computed from geometry, no browser'),
    ('harness/round.py',        'outline.py',       'the round loop uses the geometry silhouette'),
    ('cards/00_START.md',       'LOW no longer needs a browser', 'the LOW loop is browser-free'),
    ('harness/roundcheck.py',   'RESTART_IOU',      'an identity repair has a minimum change'),
    ('cards/01_LOW.md',         'IDENTITY VIEW ONLY', 'variants are read on one image each'),
    ('harness/judge.mjs',       "includes('--json')", 'the judge prints a summary, not the blob'),
    ('harness/outline.py',      'def material_shares', 'part shares come from a z-buffer, not a GPU'),
    ('harness/outline.py',      'def exaggeration', 'boldness measures computed, not eyeballed'),
    ('engine/core/checks.js',   'Move joint',       'blocks say how far to move, not just which way'),
    ('engine/core/checks.js',   'multiply every joint coordinate', 'size states the scale factor'),
]
for path, needle, label in FEATURES:
    s = read(path)
    if s is None:
        bad.append(f'promised file missing: {path} ({label})')
    elif needle not in s:
        bad.append(f'promised feature missing: "{needle}" not in {path} ({label})')

# ── 3. required files ────────────────────────────────────────────────────────
REQUIRED = [
    'MANUAL.md', 'README.md', 'CHANGELOG.md', 'LICENSE', 'SECURITY.md',
    'setup.sh', 'setup.ps1',
    'cards/00_START.md', 'cards/01_LOW.md', 'cards/02_MID.md',
    'cards/03_HIGH.md', 'cards/04_SHIP.md', 'cards/SYNTAX.md',
    'engine/cli.js',
    'harness/silmetrics.mjs', 'harness/maskmetrics.py', 'harness/judge.mjs',
    'harness/deliver.py', 'harness/hero.mjs', 'harness/publish.mjs',
    'harness/pwlaunch.mjs', 'harness/pwprobe.mjs', 'harness/calibrate.py',
    'harness/gobkit.json', 'harness/assets/showroom.html',
    'harness/assets/three-bundle.js',
    'harness/claims.json', 'harness/roundcheck.py',
    'harness/gates.json', 'harness/gates.py',
    'harness/round.py', 'harness/partreads.py', 'harness/outline.py', 'harness/brief.py',
    'harness/fit.py',
    'harness/identity.py',
    'engine/core/shade.js',
    'calibration/wolf_green.json', 'calibration/wolf_red.json',
    'calibration/red_5050.json',
    'example/wolf.json', 'example/wolf.glb',
    'harness/graft.py', 'harness/glbcheck.mjs', 'engine/core/contract.js',
    'harness/ship.py',
    'tools/sync-contract.mjs',
    'docs/OUTPUT_CONTRACT.md', 'docs/HANDOVER_sanitize.md',
    'harness/canary/answers.json', 'harness/canary/ball.png',
    'harness/canary/spike.png', 'harness/canary/wolf_side.png',
]
for p in REQUIRED:
    if not os.path.isfile(os.path.join(ROOT, p)):
        bad.append(f'required file missing: {p}')

# cards may reference harness/engine paths — every referenced path must exist
for card in ('cards/00_START.md', 'cards/01_LOW.md', 'cards/02_MID.md',
             'cards/03_HIGH.md', 'cards/04_SHIP.md', 'MANUAL.md'):
    s = read(card) or ''
    for ref in set(re.findall(r'(?:harness|engine|cards|calibration|example)/[A-Za-z0-9_./-]+\.(?:json|mjs|py|js|md|sh|ps1)', s)):
        if not os.path.isfile(os.path.join(ROOT, ref)):
            bad.append(f'{card} points at a file that does not ship: {ref}')

# ── 3b. the contract check exists in both module systems, byte-identically ──
# engine/core/contract.js is generated from harness/glbcheck.mjs; if someone
# edits one and not the other, builds and submissions would be judged by two
# different rulers. Regenerate with: node tools/sync-contract.mjs
esm = read('harness/glbcheck.mjs') or ''
cjs = read('engine/core/contract.js') or ''
if esm and cjs:
    core = esm[esm.find("'use strict';"):esm.find('// \u2500\u2500 CLI \u2500\u2500')]
    core = core.replace('export function checkGLB', 'function checkGLB')
    if core.strip() and core.strip() not in cjs:
        bad.append('contract drift: engine/core/contract.js is out of date — '
                   'run `node tools/sync-contract.mjs`')

# ── 3b. one measure, one definition ──────────────────────────────────────────
# Departments share their tools. A number defined in two files has to be kept in
# agreement BY HAND, and it was not: outline.py's first thinnest_px48 re-derived
# maskmetrics' definition, took the global minimum of the distance transform
# instead of the per-appendage inscribed radius, and read ~0.25px on every
# creature — a bar nothing could pass, discovered only by comparing pixels.
# This does not fail the build; it prints the standing work queue, the way
# gates.py prints the blocking-but-allocatable list.
MEASURES = ['thirds_cols', 'thirds_rows', 'protrusions', 'thinnest_px48',
            'sq_fill', 'mirror_sym', 'compactness', 'W_over_H']
DEFINES = ['harness/outline.py', 'harness/maskmetrics.py', 'harness/silmetrics.mjs']
dupes = []
for m in MEASURES:
    where = [f for f in DEFINES if re.search(r"['\"]?" + m + r"['\"]?\s*[:=]", read(f) or '')]
    if len(where) > 1:
        dupes.append((m, where))
if dupes:
    print('[synccheck] SHARED-TOOL QUEUE — one measure should have one definition:')
    for m, where in dupes:
        print(f'    {m:16} defined in {len(where)}: ' + ', '.join(where))
    print('    No card invokes maskmetrics.py or silmetrics.mjs any more (partreads.py')
    print('    moved to outline.py). They are superseded, kept one release for anyone')
    print('    calling them by hand, and the definitions above are the reason to finish.')

# ── 3c. STRATEGY LEAK — the harness ships the architecture, not the reasoning ──
# What the pipeline DOES is the product. Why it was tuned that way, what each
# round cost, how long a build took, and which creature failed are the
# operator's business and do not leave the local machine.
# State a rule and its threshold; never state where the threshold came from.
STRATEGY = [
    (r'\b\d{1,3},\d{3}\s*(?:tokens|characters|turns|reads|weighted)', 'a raw cost count'),
    (r'~?\d+(?:\.\d+)?\s*[kKmM]?\s*tokens',      'a token cost'),
    (r'\b\d+h\d+m\b|\b\d+m\d+s\b',            'a wall-clock timing'),
    (r'\b\d+\s*minutes?\b',                      'a wall-clock timing'),
    (r'[Mm]easured (?:on|across|in|,)',            'a field-report citation'),
    (r'a (?:shipped|delivered|measured|real) (?:build|creature|boss|run)', 'a field-report citation'),
    (r'field report|its customer|a customer (?:said|singled|rejected)', 'a customer reference'),
    (r'\b(?:322|327|315) turns\b',                 'a run-length citation'),
    (r'\b\d+(?:\.\d+)?[x×] the (?:tokens|wall clock|model turns|cost)', 'a cost ratio'),
    (r'(?i)\b(scorpion|salamander|cassowary|bison|hippo|pagoda|millipede|elephant|boar|snail|gryphon|mammoth|naga|avian)\b[^.\n]{0,60}\b(?:read|round|run|build|shipped|failed|took)\b', 'a named creature tied to a run'),
]
SKIP = ('node_modules', '.git', 'example/', 'calibration/', 'assets/',
        'harness/synccheck.py')   # this file IS the pattern list
leaks = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git')]
    for fn in files:
        if not fn.endswith(('.md', '.py', '.js', '.mjs', '.json', '.sh', '.ps1')):
            continue
        rel = os.path.relpath(os.path.join(root, fn), ROOT).replace(os.sep, '/')
        if any(k in rel for k in SKIP):
            continue
        txt = read(rel) or ''
        for pat, what in STRATEGY:
            for mm in re.finditer(pat, txt):
                line = txt[:mm.start()].count('\n') + 1
                leaks.append((rel, line, what, mm.group(0)[:40]))
if leaks:
    bad.append(f'strategy leak: {len(leaks)} place(s) state WHY, not WHAT — '
               'the harness ships the architecture only')
    for rel, line, what, frag in leaks[:40]:
        print(f'    {rel}:{line}  {what}: "{frag}"')

# ── 4. leak scan ─────────────────────────────────────────────────────────────
# Only GENERIC patterns ship. Site-specific words — the names of whatever else
# lives on the author's disk — must never be written here: a list of names you
# refuse to publish is itself a publication, and this file is public. Put one
# regex per line in SITE_WORDS instead; it is git-ignored, is not packed, and
# its absence simply means the generic scan runs alone.
SITE_WORDS = 'harness/leakwords.local.txt'
FORBIDDEN = [
    # An author's own absolute path: a drive letter and at least TWO real path
    # segments. One segment matches documentation ("C:\path\to\chrome.exe" is a
    # placeholder, not a leak) and a bare "e:\n" is a string escape, not a path.
    r'[A-Za-z]:\\[A-Za-z][\w .-]*\\[A-Za-z][\w .-]*\\',
    r'/home/[a-z][a-z0-9_-]*/',            # any absolute POSIX home path
    r'/Users/[A-Za-z][\w.-]*/',
    # An e-mail address. The TLD must be letters, or npm version specifiers
    # like "three@0.180.0" match.
    r'[\w.+-]+@[\w-]+\.[A-Za-z]{2,}',
]
_site = read(SITE_WORDS)
if _site:
    FORBIDDEN += [ln.strip() for ln in _site.splitlines()
                  if ln.strip() and not ln.lstrip().startswith('#')]
PLACEHOLDERS = ('C:\\path\\to\\', '/path/to/', 'D:\\path\\to\\')
SCAN_EXT = ('.md', '.js', '.mjs', '.py', '.sh', '.json', '.html', '.ps1', '.yml')
for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'out', 'delivery')]
    for f in files:
        if not f.endswith(SCAN_EXT) or f in ('three-bundle.js', 'synccheck.py'):
            continue
        rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
        s = read(rel) or ''
        # Documentation placeholders are structurally identical to a real path,
        # so they are named explicitly rather than pattern-matched around. The
        # list fails safe: anything NOT on it still blocks.
        for ph in PLACEHOLDERS:
            s = s.replace(ph, '<placeholder>')
        for pat in FORBIDDEN:
            mm = re.search(pat, s)
            if mm:
                bad.append(f'leaked string in {rel}: "{mm.group(0)}"')

# ── 5. no shipped file points at a doc that does not ship ────────────────────
# A dangling docs/ path is worse than a broken link: the FILENAME is the leak.
# "see docs/<name>.md" tells a reader that an internal document exists and what
# it is called, and then no one can open it. Four of these survived 1.3.1's
# first pack, left behind when their targets were held back from the release.
for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'out', 'delivery')]
    for f in files:
        if not f.endswith(SCAN_EXT) or f == 'three-bundle.js':
            continue
        rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
        for ref in sorted(set(re.findall(r'docs/[A-Za-z0-9_.-]+\.md', read(rel) or ''))):
            if not os.path.exists(os.path.join(ROOT, ref)):
                bad.append(f'{rel} points at {ref}, which does not ship')

# ── 6. nothing describes a version that has not been released ────────────────
# A public tree that says it behaves "identically to" a version that is not out
# announces that version, its feature set, and that it has users. Three such
# lines survived into the first pack of this release, backported from work that
# has not shipped. CHANGELOG entries BELOW the current release are history and
# exempt — old numbering schemes live there legitimately.
# Skipped: npm specifiers (pkg@1.2.3) and dotted quads (127.0.0.1).
VER_RE = re.compile(r'(?<![\w@.])(\d+)\.(\d+)\.(\d+)(?![\w.])')
here = tuple(int(x) for x in version.split('.')) if re.fullmatch(r'\d+\.\d+\.\d+', version) else None
if here:
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'out', 'delivery')]
        for f in files:
            if not f.endswith(SCAN_EXT) or f == 'three-bundle.js':
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
            s = read(rel) or ''
            if rel.replace('\\', '/') == 'CHANGELOG.md':
                parts = re.split(r'^## ', s, flags=re.M)
                s = '## '.join(parts[:2])
            for mm in VER_RE.finditer(s):
                if tuple(int(g) for g in mm.groups()) > here:
                    line = s[:mm.start()].count('\n') + 1
                    bad.append(f'{rel}:{line} describes {mm.group(0)}, which is newer than {version}')

# ── verdict ──────────────────────────────────────────────────────────────────
if bad:
    print(f'[synccheck] {len(bad)} problem(s) — DO NOT PUSH:')
    for b in bad:
        print('  - ' + b)
    sys.exit(1)
print(f'[synccheck] OK — version {version}, {len(FEATURES)} promised features present, '
      f'{len(REQUIRED)} required files present, no leaked strings. Safe to ship.')
