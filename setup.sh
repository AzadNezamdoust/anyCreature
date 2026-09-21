#!/bin/bash
# anyCreature one-command start.
set -e
cd "$(dirname "$0")"

# NO BROWSER. Until 1.3.2 this script installed Playwright and downloaded a
# Chromium, because the silhouettes, the part shares and the colour numbers were
# all read back off a rendered frame. None of them needed to be: a silhouette is
# a projection, occlusion is a z-buffer, and the baked colour IS the albedo. All
# of it moved into harness/outline.py, so the browser — and the install failures
# a blocked CDN used to cause — is gone. The offline viewer that ships with a
# delivery is HTML the customer opens themselves; nothing here launches one.
npm install three@0.180.0 --no-fund --no-audit

# Python does every measurement. scipy is NOT optional: protrusions, thinnest
# feature, convexity and mirror symmetry come from it, and without it those
# gates have nothing to read — so every build would pass them by default.
pip install numpy pillow scipy --break-system-packages -q 2>/dev/null || pip install numpy pillow scipy -q
python3 -c "import numpy, PIL, scipy.ndimage" || { echo "python deps missing"; exit 1; }

# Prove the whole chain on the shipped example before a line is authored: the
# engine builds it, the checks pass it, and the measures compute on the result.
mkdir -p out
node engine/cli.js example/wolf.json out/_setup.glb >/dev/null
python3 harness/outline.py out/_setup.glb out/_setup >/dev/null
node harness/judge.mjs out/_setup.glb out/_setup _setup >/dev/null
echo "setup OK — engine builds, checks pass, measures compute. No browser required."
