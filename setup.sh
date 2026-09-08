#!/bin/bash
# anyCreature one-command start: install deps → red/green ruler calibration
set -e
cd "$(dirname "$0")"
npm install three@0.180.0 playwright@1.62.1 --no-fund --no-audit
# The npm package alone ships NO browser. Without a browser, setup prints
# "calibrate OK" and then every render tool (silmetrics/hero/judge) dies at its
# first launch on a fresh machine — so a download here is the normal path and
# must stay the normal path.
#
# The one case worth skipping: Playwright can ALREADY launch. Some CI images and
# prebuilt containers ship a browser cache, and there the installer runs, fails,
# retries six times and gives up ~minutes later for nothing. Ask Playwright
# itself — one probe, its own resolution, no guessing where a browser might be.
# We do NOT go hunting for chrome on PATH and we do NOT remember a path in a
# file: a pinned absolute path is how 1.2.0 broke every clone on macOS and
# Windows, and re-deriving it automatically is the same bug wearing a hat. An
# environment that needs a specific binary sets PW_CHROMIUM_PATH and owns it.
if [ -n "$PW_CHROMIUM_PATH" ]; then
  echo "browser: pinned by PW_CHROMIUM_PATH"
elif node harness/pwprobe.mjs >/dev/null 2>&1; then
  echo "browser: Playwright can already launch one, skipping the download"
else
  # Nothing used to bound this. On a machine whose network blocks the Playwright
  # CDN the installer retries and retries: a build lost ~minutes here,
  # 21% of the whole build, to a download that was never going to complete. The
  # 1.3.1 fix above only covers "a browser already works, don't download" — it
  # said nothing about how long failing is allowed to take.
  #
  # A watchdog rather than `timeout`: timeout(1) is GNU coreutils and is NOT on
  # a stock macOS (there it is `gtimeout`, if it is there at all). Reaching for
  # it would be the same mistake as pinning a browser path — works here, breaks
  # on someone else's machine.
  echo "browser: downloading chromium (up to ${PW_INSTALL_TIMEOUT:-420}s)…"
  npx playwright install chromium & PW_PID=$!
  ( sleep "${PW_INSTALL_TIMEOUT:-420}"; kill -TERM "$PW_PID" 2>/dev/null ) & PW_WD=$!
  wait "$PW_PID"; PW_RC=$?
  kill -TERM "$PW_WD" 2>/dev/null
  if [ "$PW_RC" -ne 0 ]; then
    echo ""
    echo "browser download did not finish (exit $PW_RC)."
    echo "If this machine cannot reach the Playwright CDN, point PW_CHROMIUM_PATH at a"
    echo "Chromium or Chrome you already have and run setup.sh again:"
    echo "    PW_CHROMIUM_PATH=/path/to/chromium bash setup.sh"
    echo "A slow-but-working line just needs longer:  PW_INSTALL_TIMEOUT=1200 bash setup.sh"
    exit 1
  fi
fi
# scipy is NOT optional: harness/maskmetrics.py imports scipy.ndimage. Leaving it
# out let setup print "calibrate OK" and then blow up mid-LOW on the first measure.
pip install numpy pillow scipy --break-system-packages -q 2>/dev/null || pip install numpy pillow scipy -q
python3 -c "import numpy, PIL, scipy.ndimage" || { echo "python deps missing"; exit 1; }
python3 harness/calibrate.py
# probe an actual browser launch NOW — a missing/broken browser must fail setup
# loudly here, not mid-LOW on the first silhouette
node harness/pwprobe.mjs
echo "calibrate OK"
