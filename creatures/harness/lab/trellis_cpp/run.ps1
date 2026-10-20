param([string]$backend="cuda",[string]$models="E:\gen3d\trellis_cpp\models\f16",[string]$outdir="E:\gen3d\trellis_cpp\out_cuda",[string]$extra="--res 512",[string[]]$only=@())
$jobs=[ordered]@{wolf="E:\gen3d\r8\wolf\ref_rgba.png";crocodile="E:\gen3d\r8\crocodile\ref_rgba.png";eagle="E:\gen3d\r8\eagle\ref_rgba.png";frog="E:\gen3d\r8\frog\ref_rgba.png";
horse="E:\gen3d\r9\horse\ref_c5.png";elephant="E:\gen3d\r9\elephant\ref_c9.png";giraffe="E:\gen3d\r9\giraffe\ref_c3.png";shark="E:\gen3d\r9\shark\ref_c3.png";tortoise="E:\gen3d\r9\tortoise\ref_c3.png";kangaroo="E:\gen3d\r9\kangaroo\ref_c4.png"}
New-Item -ItemType Directory -Force $outdir | Out-Null
$exe="E:\gen3d\trellis_cpp\bin\$backend\trellis-cli.exe"
foreach($a in $jobs.Keys){
  if($only.Count -and -not ($only -contains $a)){continue}
  $base=(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | Select -First 1).Trim()
  $sw=[Diagnostics.Stopwatch]::StartNew()
  $p=Start-Process $exe -ArgumentList "`"$($jobs[$a])`" `"$outdir\$a.glb`" -m $models --webp off -v $extra" -PassThru -NoNewWindow -RedirectStandardOutput "$outdir\$a.log" -RedirectStandardError "$outdir\$a.err"
  $null=$p.Handle; $peakApp=0;$peakTot=0
  while(-not $p.HasExited){
    try{ $c=(Get-Counter "\GPU Process Memory(pid_$($p.Id)*)\Dedicated Usage" -EA Stop).CounterSamples | Measure-Object CookedValue -Sum; $m=[int]($c.Sum/1MB); if($m -gt $peakApp){$peakApp=$m} }catch{}
    $t=[int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | Select -First 1); if($t -gt $peakTot){$peakTot=$t}
    Start-Sleep -Milliseconds 250
  }
  $sw.Stop()
  "$a backend=$backend exit=$($p.ExitCode) sec=$([math]::Round($sw.Elapsed.TotalSeconds,1)) peakAppMiB=$peakApp peakTotMiB=$peakTot baseMiB=$base extra=$extra" | Tee-Object -Append "$outdir\summary.txt"
}


