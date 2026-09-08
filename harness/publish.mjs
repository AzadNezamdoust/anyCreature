// anyCreature — Gobkit community publisher. Author: Ariescar.
//
// Run `node harness/glbcheck.mjs <glb>` first — the file must satisfy
// docs/OUTPUT_CONTRACT.md before it is offered to anyone.
//
// IRON RULE: run this ONLY after the user has explicitly said yes to sharing.
// Never on your own initiative, never in the background, never "to test".
//
//   node harness/publish.mjs <model.glb> <hero.png> --title "Name" --creator "Signature"
//
// ── ALWAYS TRY THE UPLOAD FIRST ───────────────────────────────────────────────
// Never decide in advance that the environment cannot reach the network. Cloud
// sandboxes, Cowork sessions and CI runners frequently CAN. Run this command,
// then answer from what it prints. Telling the user "in this environment you
// have to upload by hand" WITHOUT having tried is wrong, and it is the most
// common way a finished creature never reaches the wall.
//
// ── THE THUMBNAIL IS NOT OPTIONAL ─────────────────────────────────────────────
// Always pass hero.png. A submission without an image is NOT rejected, but it
// will not list automatically — it waits for a human reviewer. A missing image
// is the one common reason a creature stalls after a successful upload.
//
// What it does, in order:
//   1. re-stamps the GLB: extras.license = CC0-1.0 (consent just given),
//      extras.monster / asset.copyright refreshed from --title / --creator
//   2. POSTs multipart to the endpoint in harness/gobkit.json
//      fields: model, thumb, title, creator_name, channel, key
//   3. prints ONE machine-readable JSON line:
//        {"status":"published","share_url":"https://gobkit.com/s/…","title":…,"creator":…}
//        {"status":"pending_review"}     → uploaded; a reviewer lists it shortly
//      SUCCESS IS NOT A MAGIC WORD: any 2xx the server acknowledges, carrying a
//      share_url/slug and not naming a review state, counts as published — the
//      server renamed 'published' to 'visible' once already and a word-matching
//      client reported a successful upload as a failure.
//      published/pending also carry manage_token (+ the file it was saved to):
//      a ONE-TIME takedown key. Read it out to the user — it cannot be re-issued.
//        {"status":"blocked","reason":…} → could not reach the server. NOT an error,
//                                          NOT a key problem — offer the backup path.
//        {"status":"error",…}            → the server answered and refused; read it out.
//
// ── HOW TO READ A FAILURE ─────────────────────────────────────────────────────
// The submit endpoint ALWAYS answers in JSON. Therefore:
//   · HTTP 403              → something between you and the server refused the
//                             request. It is a filtered network, NOT a bad key;
//                             403 is not one of the endpoint's own answers.
//   · a non-JSON body       → a proxy, captive portal or corporate filter replied
//                             instead of the server. Blocked.
//   · a transport exception → blocked.
// "blocked" is a normal outcome, not a failed run. Tell the user the upload pack
// is ready and give them the drag-and-drop page — no account, no key needed.
import fs from 'fs'; import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (f) => { const i = args.indexOf(f); if (i < 0) return null; const v = args[i + 1]; args.splice(i, 2); return v; };
const title = opt('--title'), creator = opt('--creator');
const [glbPath, heroPath] = args;
if (!glbPath) {
  console.error('usage: node publish.mjs <model.glb> <hero.png> --title "Name" --creator "Signature"');
  process.exit(2);
}

const cfg = JSON.parse(fs.readFileSync(path.join(here, 'gobkit.json'), 'utf8'));
const endpoint = process.env.GOBKIT_ENDPOINT || cfg.endpoint;

// ── 1. consent stamp: licence + final naming into the file itself ──
const raw = fs.readFileSync(glbPath);
const jlen = raw.readUInt32LE(12);
const g = JSON.parse(raw.slice(20, 20 + jlen).toString());
const rest = raw.slice(20 + jlen);
const a = g.asset = g.asset || { version: '2.0' };
if (creator) a.copyright = creator;
const x = a.extras = a.extras || {};
if (title) x.monster = title;
x.license = 'CC0-1.0';
let js = Buffer.from(JSON.stringify(g)); while (js.length % 4) js = Buffer.concat([js, Buffer.from(' ')]);
const head = Buffer.alloc(12); head.write('glTF'); head.writeUInt32LE(2, 4);
const jh = Buffer.alloc(8); jh.writeUInt32LE(js.length, 0); jh.writeUInt32LE(0x4E4F534A, 4);
const out = Buffer.concat([head, jh, js, rest]);
out.writeUInt32LE(out.length, 8);
fs.writeFileSync(glbPath, out);

// ── 1b. contract gate: never hand a non-conforming file to a public wall ──
const { checkGLB } = await import('./glbcheck.mjs');
const conf = checkGLB(out);
if (!conf.ok) {
  console.log(JSON.stringify({ status: 'error',
    error: 'the file breaks docs/OUTPUT_CONTRACT.md and was NOT uploaded: '
      + conf.errors.map(e => `[${e.code}] ${e.msg}`).join(' | ') }));
  process.exit(0);
}

// ── 2. multipart POST ──
const form = new FormData();
form.append('model', new Blob([out], { type: 'model/gltf-binary' }), path.basename(glbPath));
let hasThumb = false;
if (heroPath && fs.existsSync(heroPath)) {
  form.append('thumb', new Blob([fs.readFileSync(heroPath)], { type: 'image/png' }), 'hero.png');
  hasThumb = true;
} else {
  console.error('warn: no hero.png attached — the upload will be accepted but waits for a human '
    + 'reviewer instead of listing automatically. Pass delivery/hero.png.');
}
if (title) form.append('title', title);
if (creator) form.append('creator_name', creator);
form.append('channel', cfg.channel || 'harness');
form.append('key', cfg.key || '');

const blocked = (reason) => {
  console.log(JSON.stringify({ status: 'blocked', reason, thumb: hasThumb }));
  process.exit(0);
};

// Transient failures lose submissions silently: a flaky connection, a cold
// start, a 502 from an edge node. Retry twice with a backoff before deciding
// the network is against us — every retry that succeeds is a creature on the
// wall instead of a file in a folder.
async function post(attempt = 1) {
  try {
    const r = await fetch(endpoint, { method: 'POST', body: form, signal: AbortSignal.timeout(60000) });
    if (r.status >= 500 && attempt < 3) {
      await new Promise(z => setTimeout(z, attempt * 2000));
      return post(attempt + 1);
    }
    return r;
  } catch (e) {
    if (attempt < 3) {
      await new Promise(z => setTimeout(z, attempt * 2000));
      return post(attempt + 1);
    }
    throw e;
  }
}

let res, body;
try {
  res = await post();
} catch (e) {
  blocked('cannot reach the server: ' + String((e && e.message) || e));
}
// 403 is never one of this endpoint's answers — an intermediary produced it.
// Same for any body that is not JSON.
if (res.status === 403) blocked('HTTP 403 from an intermediary — the network is filtered, not the key');
try {
  body = await res.json();
} catch {
  blocked(`HTTP ${res.status} with a non-JSON body — a proxy or filter answered instead of the server`);
}

// ── 3. one JSON line for the closing dialogue ──
// AND ITS NAME IS NOT OURS TO ASSUME. The comment forty lines below this one says
// "the server's vocabulary is ITS to change ... never match a fixed word again",
// because a status word changed once and this client called a successful upload
// an error and dropped the takedown handle on the floor. Then this function
// matched exactly one fixed word, `manage_token`, one section further down the
// same file — so the day the server started returning a claim URL instead of a
// code, the client would have silently thrown it away and told the person
// nothing. Same mistake, same file. It reads a FAMILY of names now, and it does
// not care whether the value is a link or a code: it looks at the value.
// `claim_page_url` is first because it is the name the server settled on. It is
// deliberately NOT `claim_url`: a sibling build of this file takes the FIRST hit
// in this list, and `claim_url` sorts above `manage_token` there — so that name
// would make those clients silently lose a takedown code that cannot be
// re-issued. The server keeps the old field names free for that reason.
const MANAGE_KEYS = ['claim_page_url',
                     'manage_url', 'claim_url', 'manage_link', 'claim_link', 'edit_url',
                     'manage_token', 'claim_token', 'manage', 'claim', 'token'];

// 2026-09-03: the server now returns BOTH a claim link and a takedown code, and
// they are NOT interchangeable — one puts the model under your account (needs a
// sign-in, and the link dies the moment it is used), the other takes it down
// (one-time, cannot be re-issued, no sign-in). This used to `return` on the
// first hit in the family, and `claim_url` sorts before `manage_token`, so the
// day the server started sending both, the takedown code was silently dropped
// on the floor — the same class of bug the comment above is about, one level up.
// It still looks at the VALUE, not the name: whatever comes back is classified
// as a link or a code by its shape, and the first of EACH kind is kept.
function manageHandles(b) {
  const take = (v) => (typeof v === 'string' && v.trim()) ? v.trim() : null;
  const found = [];
  for (const k of MANAGE_KEYS) {
    const v = take(b?.[k]);
    if (v) found.push({ field: k, value: v });
  }
  // some servers nest it: { manage: { url } } / { claim: { token } }
  for (const k of ['manage', 'claim', 'links']) {
    const o = b?.[k];
    if (o && typeof o === 'object') {
      for (const kk of ['url', 'link', 'href', 'token', 'code']) {
        const v = take(o[kk]);
        if (v) found.push({ field: `${k}.${kk}`, value: v });
      }
    }
  }
  return {
    link: found.find((h) => isLink(h.value)) || null,
    code: found.find((h) => !isLink(h.value)) || null,
  };
}

const isLink = (v) => /^https?:\/\//i.test(v) || v.startsWith('/');
const absolute = (v) => v.startsWith('/') ? 'https://gobkit.com' + v : v;

// The claim page that ALWAYS exists. The per-model claim link is generated from
// a server-side secret; if that secret is not bound, or the route moves, the
// link is a 404 and the person is left holding a code with nowhere to type it.
// This page takes the same code and is not derived from anything, so it is the
// floor under the promise "you get two links and both of them work".
const CLAIM_FALLBACK = 'https://gobkit.com/community/claim';

// Do not print a link without knowing it resolves. The whole reason the earlier
// wording patch was held back was that it would have sent people to a 404; the
// answer is not to guess whether the page is up, it is to ask it.
//   true  → it answered
//   false → it answered, and said no. Use the fallback.
//   null  → could not ask (offline, filtered). Say nothing either way: the
//           upload itself already succeeded, and a flaky probe must never
//           downgrade a link that is probably fine.
async function linkLive(u) {
  try {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), 8000);
    const r = await fetch(u, { method: 'GET', redirect: 'follow', signal: c.signal });
    clearTimeout(t);
    return r.status >= 200 && r.status < 400;
  } catch { return null; }
}

function writeBeside(name, text) {
  const f = path.join(path.dirname(path.resolve(glbPath)), name);
  try { fs.writeFileSync(f, text); return f; } catch { return null; }
}

// One file per handle. Writing both into one file was tempting, but a person
// who was told "your takedown code is in manage_token.txt" must find it there.
function saveManage(hs, slug, live) {
  const id = `model: ${slug || '(slug unknown)'}\n`;
  // A dead link on disk is worse than no file: the person keeps it, comes back
  // in a week, and clicks a 404 with no idea what to do instead. When the probe
  // said no, this file holds the way in that does work.
  const linkFile = !hs.link ? null : live === false ? writeBeside('claim_link.txt',
    `gobkit claim — KEEP THIS\n` +
    `the per-model claim link for this upload did not resolve, so use the\n` +
    `standing claim page instead: sign in with Google and paste the key from\n` +
    `manage_token.txt. same result — the model gets listed under your name.\n\n` +
    id + `page:  ${CLAIM_FALLBACK}\n`) : writeBeside('claim_link.txt',
    `gobkit claim link — KEEP THIS\n` +
    `open it and sign in with Google to put this model under your account.\n` +
    `it stops working the moment it is used, so it is harmless if it leaks.\n` +
    `this is NOT the takedown key — that one is in manage_token.txt.\n` +
    `if it ever stops resolving: ${CLAIM_FALLBACK} takes the same key.\n\n` +
    id + `link:  ${absolute(hs.link.value)}\n`);
  const codeFile = hs.code ? writeBeside('manage_token.txt',
    `gobkit manage token — KEEP THIS\n` +
    `it is shown once, cannot be re-issued, and is the only way to take this\n` +
    `model down later. no sign-in needed. do not post it anywhere.\n\n` +
    id + `token: ${hs.code.value}\n`) : null;
  return { linkFile, codeFile };
}

// One shape for every branch below, so a handle can never be reported by one
// path and dropped by another.
async function manageFields(b, slug) {
  const hs = manageHandles(b);
  const url = hs.link ? absolute(hs.link.value) : null;
  const live = url ? await linkLive(url) : null;
  const { linkFile, codeFile } = saveManage(hs, slug, live);
  if (!hs.link && !hs.code) {
    return { manage_kind: null, manage_url: null, manage_token: null,
             manage_file: null, manage_token_file: null };
  }
  return {
    // 'both' is the normal case now; 'url' / 'token' still happen if the server
    // only sends one of them, and older servers send only a token.
    manage_kind: hs.link && hs.code ? 'both' : (hs.link ? 'url' : 'token'),
    manage_url: url,
    manage_token: hs.code ? hs.code.value : null,
    manage_field: [hs.link && hs.link.field, hs.code && hs.code.field].filter(Boolean).join('+'),
    manage_file: linkFile || codeFile,
    manage_token_file: codeFile || linkFile,   // kept: older callers read this name
    claim_link_file: linkFile,
    // true / false / null — see linkLive(). false is the only value that means
    // "do not show this link", and then claim_fallback_url is the way in.
    claim_link_live: live,
    claim_fallback_url: CLAIM_FALLBACK,
  };
}

// The server's vocabulary is ITS to change: 'published' became 'visible' and
// this client called a successful upload an error, told the user it failed, and
// dropped the takedown token on the floor. Never match a fixed word again —
// anything the server acknowledges (2xx + ok) with a link or a slug IS a
// success; only an explicit review state or an outright refusal is not.
// one probe, one shape, shared by every branch below
const M = await manageFields(body, body.slug);
const ACK = res.status >= 200 && res.status < 300 && body.ok !== false;
const REVIEW = /pending|review|queue/i.test(String(body.status || ''));
const located = body.share_url || body.slug || body.url;
if (ACK && located && !REVIEW) {
  // share_url is preferred; a bare slug is enough to build it
  const share = body.share_url
    ? (body.share_url.startsWith('http') ? body.share_url : 'https://gobkit.com' + body.share_url)
    : (body.slug ? `https://gobkit.com/s/${body.slug}` : 'https://gobkit.com/community');
  console.log(JSON.stringify({ status: 'published', share_url: share,
    ...M,
    title: body.title ?? title, creator: body.creator ?? creator, thumb: hasThumb }));
} else if (ACK && REVIEW) {
  // held for a human: still a successful upload, and it can still carry a token
  console.log(JSON.stringify({ status: 'pending_review', server_status: body.status ?? null,
    ...M, thumb: hasThumb }));
} else if (ACK) {
  // acknowledged but nothing to link to yet — treat as uploaded, not refused
  console.log(JSON.stringify({ status: 'pending_review', server_status: body.status ?? null,
    ...M, thumb: hasThumb }));
} else {
  // even a refusal can carry a token for an earlier upload — never swallow it
  console.log(JSON.stringify({ status: 'error', http: res.status,
    server_status: body.status ?? null,
    error: body.error || `unexpected response: ${JSON.stringify(body).slice(0, 200)}`,
    ...M }));
}
