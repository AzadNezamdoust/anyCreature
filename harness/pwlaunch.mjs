// One browser launcher for every render tool. Author: Ariescar.
// PW_CHROMIUM_PATH pins a binary; PW_NO_SANDBOX=1 only where the OS sandbox
// genuinely cannot run. On failure, dies with ONE actionable line — the fix is
// always the same and a stack trace never says it.
//
// AND IT LOOKS IN THE BROWSER CACHE BEFORE IT GIVES UP. Playwright asks for the
// exact build number its own package was pinned to, so a machine holding
// chromium-1194 while the installed playwright wants 1234 reports "Executable
// doesn't exist" and the setup script goes off to download one. On a host whose
// egress is filtered that download can never succeed: measured, one run spent
// a run on four retries of a fetch that was never going to complete, on a
// container that already had a working Chromium in /opt/pw-browsers. A build
// number mismatch is not a missing browser. Look first, download second.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const BIN = ['chrome', 'chrome-headless-shell', 'headless_shell', 'chrome.exe'];

export function findCachedChromium() {
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH,
                 path.join(process.env.HOME || '', '.cache', 'ms-playwright'),
                 path.join(process.env.LOCALAPPDATA || '', 'ms-playwright')].filter(Boolean);
  const hits = [];
  const walk = (dir, depth) => {
    if (depth > 4) return;
    let ents;
    try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p, depth + 1);
      else if (BIN.includes(e.name)) hits.push(p);
    }
  };
  for (const r of roots) walk(r, 0);
  // a full chromium beats a headless shell: the render tools take screenshots
  hits.sort((a, b) => (a.includes('headless') ? 1 : 0) - (b.includes('headless') ? 1 : 0));
  return hits[0] || null;
}

export async function launchBrowser() {
  const args = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    .concat(process.env.PW_NO_SANDBOX === '1' ? ['--no-sandbox'] : []);
  const tries = [process.env.PW_CHROMIUM_PATH || undefined];
  let first = null;
  for (const executablePath of tries) {
    try { return await chromium.launch({ executablePath, args }); }
    catch (e) { first = e; }
  }
  // playwright could not find its own pinned build — look for ANY cached one
  const found = findCachedChromium();
  if (found) {
    try {
      const br = await chromium.launch({ executablePath: found, args });
      console.error(`note: playwright's pinned build is absent; using the cached browser at ${found}`);
      return br;
    } catch (e) { first = e; }
  }
  console.error('render tool cannot start a browser: ' + String(first && first.message || first).split('\n')[0]);
  console.error('Fix: run  npx playwright install chromium   (or set PW_CHROMIUM_PATH to a Chromium/Chrome binary)');
  process.exit(3);
}
