#!/bin/bash

# Color definition
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║ TrendRadar MCP One-Click Deployment (Mac) ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "📍 Project directory: ${BLUE}${PROJECT_ROOT}${NC}"
echo ""

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[1/3] 🔧 UV is not installed and is being installed automatically...${NC}"
    echo "Tip: UV is a fast Python package manager that only needs to be installed once"
    echo ""
    curl -LsSf https://astral.sh/uv/install.sh | sh

    echo ""
    echo "Refreshing PATH environment variable..."
    echo ""

    # Add UVs to PATH
    export PATH="$HOME/.cargo/bin:$PATH"

    # Verify whether UV is actually available
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ [Error] UV installation failed ${NC}"
        echo ""
        echo "Possible reasons:"
        echo "1. Network connection problem, unable to download the installation script"
        echo "2. Insufficient permissions on the installation path"
        echo "3. Installation script execution exception"
        echo ""
        echo "Solution:"
        echo "1. Check whether the network connection is normal"
        echo "2. Manual installation: https://docs.astral.sh/uv/getting-started/installation/"
        echo " 3. Or run: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    echo -e "${GREEN}✅ [Success] UV installed ${NC}"
    echo -e "${YELLOW}⚠️ Please rerun this script to continue ${NC}"
    exit 0
else
    echo -e "${GREEN}[1/3] ✅ UV has been installed ${NC}"
    uv --version
fi

echo ""
echo "[2/3] 📦 Install project dependencies..."
echo "Tip: This may take 1-2 minutes, please be patient"
echo ""

# Create a virtual environment and install dependencies
uv sync

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ [Error] Dependency installation failed ${NC}"
    echo "Please check the network connection and try again"
    exit 1
fi

echo ""
echo -e "${GREEN}[3/3] ✅ Check configuration file...${NC}"
echo ""

# Check configuration file
if [ ! -f "config/config.yaml" ]; then
    echo -e "${YELLOW}⚠️ [Warning] Configuration file not found: config/config.yaml${NC}"
    echo "Please make sure the configuration file exists"
    echo ""
fi

#Add execution permissions
chmod +x start-http.sh 2>/dev/null || true

# Get UV path
UV_PATH=$(which uv)

echo ""
echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║ Deployment completed! ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
echo ""
echo "📋 Next steps:"
echo ""
echo " 1️⃣ Open Cherry Studio"
echo " 2️⃣ Go to Settings > MCP Servers > Add Server"
echo " 3️⃣ Fill in the following configuration:"
echo ""
echo "name: TrendRadar"
echo "Description: News hotspot aggregation tool"
echo "Type: STDIO"
echo -e "Command: ${BLUE}${UV_PATH}${NC}"
echo "Parameters (one line each):"
echo -e "        ${BLUE}--directory${NC}"
echo -e "        ${BLUE}${PROJECT_ROOT}${NC}"
echo -e "        ${BLUE}run${NC}"
echo -e "        ${BLUE}python${NC}"
echo -e "        ${BLUE}-m${NC}"
echo -e "        ${BLUE}mcp_server.server${NC}"
echo ""
echo " 4️⃣ Save and enable MCP switch"
echo ""
echo "📖 For detailed tutorials, please view: README-Cherry-Studio.md. Don't close this window. You will use it to fill in the parameters later."
echo ""
