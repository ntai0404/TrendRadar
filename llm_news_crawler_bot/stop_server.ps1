$ErrorActionPreference = "SilentlyContinue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $Root "server.pid"

$pids = @()
if (Test-Path $PidFile) {
  $pids += Get-Content $PidFile
}

$listeners = netstat -ano | Select-String "127.0.0.1:8010\s+.*LISTENING"
foreach ($line in $listeners) {
  $pids += (($line.ToString() -split "\s+") | Where-Object { $_ })[-1]
}

$pids = $pids | Where-Object { $_ -match "^\d+$" } | Select-Object -Unique
foreach ($serverPid in $pids) {
  Stop-Process -Id ([int]$serverPid) -Force
  Write-Host "Stopped PID $serverPid"
}

Remove-Item $PidFile -Force
