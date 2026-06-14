#!/bin/bash

echo "╔════════════════════════════════════════╗"
echo "║ TrendRadar MCP Server (HTTP mode) ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ [Error] Virtual environment not found"
    echo "Please run ./setup-mac.sh first to deploy"
    echo ""
    exit 1
fi

echo "[Mode] HTTP (suitable for remote access)"
echo "[address] http://localhost:3333/mcp"
echo "[Prompt] Press Ctrl+C to stop the service"
echo ""

uv run python -m mcp_server.server --transport http --host 0.0.0.0 --port 3333
