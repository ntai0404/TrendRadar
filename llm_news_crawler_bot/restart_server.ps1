$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root "stop_server.ps1")
Start-Sleep -Seconds 1
& (Join-Path $Root "start_background.ps1")
