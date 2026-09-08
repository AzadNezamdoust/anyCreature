// Launch-and-quit probe: proves the render tools can start a browser.
// Prints ONE actionable line on failure instead of a stack trace.
import { launchBrowser } from './pwlaunch.mjs';
try {
  const br = await launchBrowser();
  await br.close();
  console.log('render tools OK (browser launches)');
} catch (e) {
  console.error(String(e && e.message || e).split('\n')[0]);
  console.error('render tools need a browser. Fix: run  npx playwright install chromium');
  console.error('(or point PW_CHROMIUM_PATH at an existing Chromium/Chrome binary)');
  process.exit(3);
}
