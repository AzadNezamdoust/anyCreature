#!/usr/bin/env python3
"""The brief, checked for PRESENCE — never for content.

    python3 harness/brief.py <brief.md> [--spec spec.json] [--poles A/metrics.json B/metrics.json]

WHAT THIS DOES AND DOES NOT DO. It never judges what you wrote. Declare any
height, any identity, any palette — this passes all of them. It refuses exactly
one thing: a BLANK slot, and only for the slots a later stage actually consumes.
The brief is where the creature is designed and design has no right answer; the
downstream rulers, however, read specific fields, and a field nobody filled in
does not make them lenient — it makes them VANISH.

WHY BLANK IS WORSE THAN WRONG. Read out of the engine and the cards:

  height        engine/core/checks.js guards the size gate with `if (spec.height)`.
                No declaration, no check — silently. A creature ships at the
                wrong scale and not one line of output ever mentions it.
  identity      identity.py falls back to a placeholder noun when --noun is
                missing, so Gate 1 prints a verdict about nothing at all. That
                is worse than failing, because it looks like passing.
  signature     card 01 §1's single customer question IS this slot. Law 7
                forbids asking a second one, so a signature that was not written
                down cannot be recovered — only guessed. Five consumers read it:
                Gate 1's identity view, part_exists (block), part_signature, the
                MID whitelist and HIGH's main colour.
  value plan    `value_order` prints every material sorted by OKLab lightness on
                every build, but a sorted list only says what IS brightest — the
                brief is the only thing that says what SHOULD be. No plan, no
                bar. (Colour and VALUE only. Material is not judged anywhere in
                this pipeline and does not belong in the slot.)
  feel          the 24px read costs a whole subagent (tokens minimum) and
                has nothing to be compared against.
  exaggeration  §4b's two poles are two stagings of it. No exaggeration, nothing
                to stage.

The other four slots — mass hierarchy, two focals, stance, attack — lose an
ADVISORY at most, or nothing at all (balance is computed from the geometry
whatever the brief says). Those are noted, never blocked. Blocking them would
buy nothing and cost design freedom, which is the whole point of this stage.

THE NAMED-CHAIN CONTRACT. Slots that name PARTS may end with

    ... chains: LClaw, RClaw

and those names must exist in the spec. This is still presence, not content —
you invent the names, the check only asks that what you promised got built. It
exists because of a measured failure: one boss brief named "the boulder in the
iron net at the beam's tip" as its second focal in minute four, part_exists sits
at stage MID, and nothing required that part until MID — so rounds 1 to 3 built
an incomplete brief and the shape the customer eventually singled out did not
appear until round 4.

TWO POLES, NOT THREE NEAR-COPIES (--poles). Card 01 §4b builds TWO variants that
are opposite extremes of one declared axis, and this measures whether they
really are. The ruler is where the mass sits in thirds of the frame, in the view
the reader will actually be shown, because iou_vs_prev cannot tell two designs
apart: it counts overlapping pixels, so changing proportions moves it a long way
while the design stands still. Three rounds that were meant to be three attempts
can sit 0.08 to 0.20 apart on this ruler — closer than any two different
creatures — while their iou reads 0.6 to 0.7, which sounds like a great deal of
change and is not.
"""
import sys, os, json, re

VIEWS = ('front', 'side', 'top', 'hero')

# Slot -> (must be filled?, who reads it later). Order is the card's order.
SLOTS = [
    ('identity',       True,  'Gate 1 — identity.py has no noun without it'),
    ('feel',           True,  'the 24px read has nothing to be judged against'),
    ('height',         True,  'the engine size gate is skipped entirely without it'),
    ('signature',      True,  'Gate 1 identity view, part_exists, MID whitelist, HIGH main colour'),
    ('mass hierarchy', False, 'share_hierarchy (advice only)'),
    ('two focals',     False, 'focal_contrast (advice only)'),
    ('stance',         False, 'nothing mechanical — balance is computed from the geometry'),
    ('attack',         False, 'nothing mechanical — attack_reach measures the clip, not the brief'),
    ('value plan',     True,  'value_order has nothing to compare its lightness table against (colour and value only — material is not judged)'),
]
# Slots that name parts and must therefore declare the chains they mean.
NEEDS_CHAINS = ('signature', 'two focals')

# How far apart two poles must sit on the mass-layout ruler. Measured, not
# guessed, and deliberately set as a FLOOR rather than a target:
#
#   0.08 0.14 0.20   the three "variants" of a build's r1-r3 — one
#                    design adjusted three times, which is the waste this stops
#   0.15             r3 -> r4 of the same build
#   0.38             two poses of ONE locked spec, authored here as opposites
#                    (tail hauled back vs tail whipped forward) and built green
#   0.42 0.56 0.61   the same build's rounds either side of a concept restart
#
# 0.25 clears every same-idea pair by a wide margin and passes every deliberate
# restaging. It is a first cut off one creature's history plus one authored
# pair; re-cut it when more runs exist, the way RESTART_IOU was.
POLE_MIN = 0.25

# A pole can be far away on the layout ruler and still be junk — the authored
# pair above proved it. Whipping the tail forward moved the mass a long way and
# folded the signature part flat onto the shell, and the silhouette stopped
# reading as a creature at all. The number that catches that already exists:
# FILL, the share of the bounding box the silhouette actually occupies. That
# pole measured 0.514 against its twin's 0.319, and against 0.222-0.393 across
# all thirteen rounds the creature ever had. High fill is a blob. It is advice,
# not a block: one weak pole out of two is normal, and which one is weak is a
# judgment for the reader.
FILL_BLOB = 0.45


def norm(s):
    return re.sub(r'[^a-z ]', '', s.lower()).strip()


def parse(path):
    """brief.md -> {slot: value}, exaggeration text, [discards]."""
    txt = open(path, encoding='utf-8').read()
    slots, section, exag, disc = {}, None, '', []
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith('#'):
            h = norm(s)
            section = ('exag' if 'exaggeration' in h else
                       'disc' if 'discard' in h else None)
            continue
        if s.startswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if len(cells) >= 2 and not set(cells[0]) <= set('-: '):
                k = norm(cells[0])
                if k and k not in ('slot',):
                    slots[k] = cells[1]
            continue
        if not s:
            continue
        if section == 'exag':
            exag += ' ' + s
        elif section == 'disc':
            if re.match(r'^\d+[.)]', s) or s.startswith(('-', '*')):
                disc.append(s)
    return slots, exag.strip(), disc


def declared_chains(value):
    m = re.search(r'chains?\s*[:：]\s*(.+)$', value, re.I)
    if not m:
        return []
    return [c.strip().strip('`*_"\'') for c in re.split(r'[,、]', m.group(1)) if c.strip()]


def spec_chains(spec):
    names = set()
    for key in ('volumes', 'parts'):
        for o in spec.get(key, []) or []:
            for f in ('chain', 'name', 'id'):
                if o.get(f):
                    names.add(str(o[f]))
    for c in (spec.get('chains') or {}):
        names.add(str(c))
    return names


def check(brief_path, spec_path=None):
    """Returns (blocks, notes, facts)."""
    slots, exag, disc = parse(brief_path)
    blocks, notes, facts = [], [], {}

    for name, must, who in SLOTS:
        val = slots.get(name, '').strip()
        empty = (not val) or val in ('-', '—', 'TBD', 'tbd', '?')
        if empty:
            (blocks if must else notes).append(
                f'{name}: not filled in — {who}.')
            continue
        if name == 'height':
            m = re.search(r'(\d+(?:\.\d+)?)', val)
            if not m or float(m.group(1)) <= 0:
                blocks.append('height: no number in it. The engine needs a metre '
                              'value to scale to; any value passes, a blank does not.')
            else:
                facts['height'] = float(m.group(1))
        if name == 'identity':
            m = re.search(r'reads as\s*[:：]?\s*\**([^*|(]+)', val, re.I)
            facts['noun'] = (m.group(1) if m else val).strip().strip('*` ')
        if name == 'signature':
            v = [w for w in VIEWS if w in val.lower()]
            if not v:
                blocks.append('signature: no view named. Gate 1 requires the '
                              'brief\'s own identity view to be one of the views '
                              'that read — name one of ' + '/'.join(VIEWS) + '.')
            else:
                facts['identity_view'] = v[0]
        if name in NEEDS_CHAINS and not declared_chains(val):
            blocks.append(f'{name}: names no chains. End the cell with '
                          f'"chains: a, b" so the spec check can confirm the '
                          f'thing you ordered was actually built. Any names you '
                          f'like — the check only asks that they exist.')

    if not exag:
        blocks.append('the one exaggeration: missing. §4b builds two opposite '
                      'stagings of it, so there is nothing to stage without it.')
    if len(disc) < 3:
        notes.append(f'discarded ideas: {len(disc)} listed, the rule asks for 3. '
                     f'Nothing downstream reads them, so this does not block — but '
                     f'they are the mechanism that produced the design worth keeping.')

    if spec_path:
        try:
            spec = json.load(open(spec_path, encoding='utf-8'))
        except Exception as e:
            blocks.append(f'spec {spec_path} could not be read: {e}')
            return blocks, notes, facts
        have = spec_chains(spec)
        for name, _, _ in SLOTS:
            for c in declared_chains(slots.get(name, '')):
                if c not in have:
                    blocks.append(
                        f'{name} promised chain "{c}" and the spec has no such '
                        f'chain. Build it now, at r1, or change the brief — a part '
                        f'the brief named and the spec skipped is not caught until '
                        f'MID, which is exactly how one boss build reached round 4 '
                        f'before its second focal existed.')
        if 'height' in facts and spec.get('height'):
            d = abs(spec['height'] - facts['height']) / facts['height']
            if d > 0.15:
                blocks.append(
                    f'height: the brief declares {facts["height"]}m and the spec '
                    f'{spec["height"]}m — {d * 100:.0f}% apart, and the engine '
                    f'refuses over 15%. Fix it here, before anything is built on it.')
        elif not spec.get('height'):
            blocks.append('spec has no "height" — the engine SKIPS the size check '
                          'entirely when it is absent (checks.js), so the creature '
                          'can ship at any scale and nothing will say so.')
    return blocks, notes, facts


def layout(metrics, view=None):
    """The six numbers that say where the mass sits, in ONE view."""
    v = metrics.get('views', metrics)
    pick = None
    for k in ([view] if view else []) + ['side', 'hero', 'front', 'top']:
        if k and isinstance(v.get(k), dict) and v[k].get('thirds_cols'):
            pick = v[k]
            break
        kk = f'sil_{k}' if k else None
        if kk and isinstance(v.get(kk), dict) and v[kk].get('thirds_cols'):
            pick = v[kk]
            break
    if not pick:
        return None
    return pick['thirds_cols'] + pick['thirds_rows']


def poles_apart(a, b, view=None):
    """(distance, ok) for two variants' metrics dicts."""
    la, lb = layout(a, view), layout(b, view)
    if la is None or lb is None:
        return None, None
    d = round(sum(abs(x - y) for x, y in zip(la, lb)), 3)
    return d, d >= POLE_MIN


def fill_of(metrics, view=None):
    v = metrics.get('views', metrics)
    for k in ([view] if view else []) + ['side', 'hero', 'front', 'top']:
        for kk in ((k, f'sil_{k}') if k else ()):
            if isinstance(v.get(kk), dict) and v[kk].get('fill') is not None:
                return v[kk]['fill']
    return None


def report(blocks, notes, facts, label='brief'):
    for n in notes:
        print(f'  note   {n}')
    for b in blocks:
        print(f'  BLOCK  {b}')
    if not blocks:
        bits = [f'{k}={v}' for k, v in facts.items()]
        print(f'[{label}] every slot a later stage reads is filled'
              + (f' — {", ".join(bits)}' if bits else '') + '.')
    return 1 if blocks else 0


def main():
    a = sys.argv[1:]
    if not a or (a[0].startswith('--') and '--poles' not in a):
        print(__doc__)
        return 2
    if '--poles' in a:
        i = a.index('--poles')
        pa, pb = a[i + 1], a[i + 2]
        va = a[a.index('--view') + 1] if '--view' in a else None
        ma = json.load(open(pa, encoding='utf-8'))
        mb = json.load(open(pb, encoding='utf-8'))
        d, ok = poles_apart(ma, mb, va)
        if d is None:
            print('BLOCK: neither metrics file carries thirds — rerun outline.py.')
            return 2
        print(f'[poles] mass-layout distance {d:.2f} (needs {POLE_MIN:.2f})')
        for tag, m in (('A', ma), ('B', mb)):
            f = fill_of(m, va)
            if f is not None and f >= FILL_BLOB:
                print(f'  note   pole {tag} fills {f:.2f} of its own box — that is a '
                      f'BLOB, not a pose. Something has folded flat onto the body; '
                      f'check it before you show it to anyone.')
        if ok:
            print('  the two poles are genuinely opposite. Read them.')
            return 0
        print('  BLOCK: these are one idea built twice. Do not spend a reader on')
        print('  them — a reader shown two versions of the same design tells you')
        print('  what it already told you. Name the axis (coiled/released,')
        print('  reared/flattened, front-loaded/rear-loaded) and push BOTH ends.')
        return 1
    brief = a[0]
    spec = a[a.index('--spec') + 1] if '--spec' in a else None
    blocks, notes, facts = check(brief, spec)
    return report(blocks, notes, facts)


if __name__ == '__main__':
    sys.exit(main())
