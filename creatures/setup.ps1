# anyCreature one-command start (Windows).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# NO BROWSER. Until 1.3.2 this installed Playwright and downloaded a Chromium,
# because the silhouettes, part shares and colour numbers were read back off a
# rendered frame. None of them needed to be — see setup.sh for the long version.
npm install three@0.180.0 --no-fund --no-audit
if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed"; exit 1 }

pip install numpy pillow scipy -q
python3 -c "import numpy, PIL, scipy.ndimage"
if ($LASTEXITCODE -ne 0) { Write-Error "python deps missing"; exit 1 }

New-Item -ItemType Directory -Force -Path out | Out-Null
node engine/cli.js example/wolf.json out/_setup.glb | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "the engine did not build the shipped example"; exit 1 }
python3 harness/outline.py out/_setup.glb out/_setup | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "outline.py could not measure the shipped example"; exit 1 }
node harness/judge.mjs out/_setup.glb out/_setup _setup | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "the shipped example did not judge"; exit 1 }

# The rulers must separate good from bad on this machine (see setup.sh).
python3 harness/calibrate.py
if ($LASTEXITCODE -ne 0) { Write-Output "calibrate FAILED - do not start work; report this."; exit 1 }
Write-Output "calibrate OK - engine builds, rulers separate good from bad. No browser required."
