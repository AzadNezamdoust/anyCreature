# anyCreature one-command start (Windows).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# NO BROWSER. Until 1.3.2 this installed Playwright and downloaded a Chromium,
# because the silhouettes, part shares and colour numbers were read back off a
# rendered frame. None of them needed to be — see setup.sh for the long version.
npm install three@0.180.0 --no-fund --no-audit

pip install numpy pillow scipy -q
python3 -c "import numpy, PIL, scipy.ndimage"
if ($LASTEXITCODE -ne 0) { Write-Error "python deps missing"; exit 1 }

New-Item -ItemType Directory -Force -Path out | Out-Null
node engine/cli.js example/wolf.json out/_setup.glb | Out-Null
python3 harness/outline.py out/_setup.glb out/_setup | Out-Null
node harness/judge.mjs out/_setup.glb out/_setup _setup | Out-Null
Write-Output "setup OK - engine builds, checks pass, measures compute. No browser required."
