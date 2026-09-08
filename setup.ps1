# anyCreature one-command start (Windows PowerShell).
# Same steps as setup.sh: deps -> browser -> calibration -> browser probe.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
npm install three@0.180.0 playwright@1.62.1 --no-fund --no-audit
# Same rule as setup.sh: a download is the normal path, skipped only when
# Playwright can already launch a browser (prebuilt images, warm CI caches).
# No hunting for chrome.exe, no remembered path — PW_CHROMIUM_PATH is the only
# pin, and whoever sets it owns it.
if ($env:PW_CHROMIUM_PATH) {
  Write-Output "browser: pinned by PW_CHROMIUM_PATH"
} else {
  node harness/pwprobe.mjs *> $null
  if ($LASTEXITCODE -eq 0) {
    Write-Output "browser: Playwright can already launch one, skipping the download"
  } else {
    # Same bound as setup.sh: a blocked CDN must fail in minutes, not tens of
    # them. A measured run lost ~minutes to an install that could never
    # finish, because nothing capped it.
    $limit = if ($env:PW_INSTALL_TIMEOUT) { [int]$env:PW_INSTALL_TIMEOUT } else { 420 }
    Write-Output "browser: downloading chromium (up to ${limit}s)…"
    $p = Start-Process -FilePath "npx" -ArgumentList "playwright","install","chromium" `
                       -NoNewWindow -PassThru
    if (-not $p.WaitForExit($limit * 1000)) {
      try { $p.Kill($true) } catch {}
      $code = 124
    } else { $code = $p.ExitCode }
    if ($code -ne 0) {
      Write-Output ""
      Write-Output "browser download did not finish (exit $code)."
      Write-Output "If this machine cannot reach the Playwright CDN, point PW_CHROMIUM_PATH at a"
      Write-Output "Chromium or Chrome you already have and run setup.ps1 again:"
      Write-Output '    $env:PW_CHROMIUM_PATH="C:\path\to\chrome.exe"; .\setup.ps1'
      Write-Output 'A slow-but-working line just needs longer:  $env:PW_INSTALL_TIMEOUT=1200'
      exit 1
    }
  }
}
pip install numpy pillow scipy -q
python -c "import numpy, PIL, scipy.ndimage"
python harness/calibrate.py
node harness/pwprobe.mjs
Write-Output "calibrate OK"
