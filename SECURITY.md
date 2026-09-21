# Security notes

## What this package runs on your machine

**Nothing here opens a socket or launches a browser.** As of 1.3.2 every
measurement is arithmetic on the vertices (`harness/outline.py`), so the tools
read files and write files and that is all.

Before 1.3.2 three tools each started a local HTTP server so a headless Chromium
could load the model. If you are on an older copy: those servers bound to
`127.0.0.1` from 1.2.0 onward, but **before 1.2.0 `judge.mjs` resolved served
paths with `path.join` and no containment check while listening on `0.0.0.0`** —
any host on the same network could read arbitrary files, `/etc/passwd` and
`/proc/self/environ` among them, for as long as a judge run lasted. Update, or
do not run that copy on an untrusted network.

The only network call this package can make is the explicit `publish.mjs`
upload, which runs only after the user says yes.

## The Gobkit key in `harness/gobkit.json`

Public by design. It is an anonymous submission key for the community wall — it
authorises posting, nothing else, and abuse is bounded server-side by rate
limiting and review. Finding it in this repository is not a leak.

It does mean two things:

- **Rotation does not retract.** A key committed to git stays readable in the
  history forever. Retiring one has to happen server-side.
- The endpoint is effectively open to anyone who clones this repo, so the
  server's rate limiting and moderation are the only real controls.

## Untrusted input

Creature names and signatures come from a human and are written into three
places: the delivered `_viewer.html`, the GLB's `asset.copyright` /
`extras.monster`, and the community listing. `deliver.py` HTML-escapes them
before substitution — a creature named `</h1><script>…` used to execute in the
viewer. **Any service rendering `extras.monster` must escape it independently.**
Do not rely on this package having done it.

Spec JSON is executed as data, not code — there is no `eval`, no dynamic
`require`, and the only subprocess calls are fixed argument lists to `node`.
Nothing in the pipeline fetches a URL except `publish.mjs`, and only after
explicit consent.

## Reporting

Open a GitHub issue for anything non-sensitive. For something exploitable,
please report privately first.
