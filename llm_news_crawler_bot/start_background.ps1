$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $Root "server.pid"
$LogFile = Join-Path $Root "server.cmd.log"

Set-Location $Root

$existing = netstat -ano | Select-String "127.0.0.1:8010\s+.*LISTENING"
if ($existing) {
  $serverPid = (($existing[0].ToString() -split "\s+") | Where-Object { $_ })[-1]
  Write-Host "Server already listening on http://127.0.0.1:8010 (PID $serverPid)"
  Set-Content -Path $PidFile -Value $serverPid
  exit 0
}

$args = "/c `"cd /d `"$Root`" && python -m uvicorn news_crawler_bot.api:app --host 127.0.0.1 --port 8010 --loop asyncio > `"$LogFile`" 2>&1`""
$proc = Start-Process -FilePath cmd.exe -ArgumentList $args -WindowStyle Hidden -PassThru
Set-Content -Path $PidFile -Value $proc.Id
Write-Host "Started dashboard background launcher PID $($proc.Id)"
Write-Host "URL: http://127.0.0.1:8010/"
Write-Host "Log: $LogFile"
