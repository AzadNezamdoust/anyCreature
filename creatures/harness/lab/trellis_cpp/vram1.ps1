param([string]$backend="cuda",[string]$models="E:\gen3d\trellis_cpp\models\f16",[string]$img="E:\gen3d\r8\wolf\ref_rgba.png",[string]$out="E:\gen3d\trellis_cpp\vram\t.glb",[string]$extra="--res 512")
New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
$sw=[Diagnostics.Stopwatch]::StartNew()
$p=Start-Process "E:\gen3d\trellis_cpp\bin\$backend\trellis-cli.exe" -ArgumentList "`"$img`" `"$out`" -m $models --webp off $extra" -PassThru -NoNewWindow -RedirectStandardOutput "$out.log" -RedirectStandardError "$out.err"
$null=$p.Handle; $pk=0
while(-not $p.HasExited){
  try{ $s=(Get-Counter "\GPU Process Memory(pid_$($p.Id)_*)\Dedicated Usage" -EA Stop).CounterSamples; $m=[int](($s|Measure-Object CookedValue -Sum).Sum/1MB); if($m -gt $pk){$pk=$m} }catch{}
}
"$backend exit=$($p.ExitCode) sec=$([math]::Round($sw.Elapsed.TotalSeconds,1)) peakDedicatedMiB=$pk models=$models extra=$extra"
