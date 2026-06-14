@echo off
chcp 65001 >nul

echo ============================================================
echo TrendRadar MCP Server (HTTP mode)
echo ============================================================
echo.



echo [mode] HTTP (suitable for remote access)
echo [address] http://localhost:3333/mcp
echo [Prompt] Press Ctrl+C to stop the service
echo.

set PYTHONUTF8=1
uv run python -m mcp_server.server --transport http --host 0.0.0.0 --port 3333

pause
