@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo TrendRadar MCP one-click deployment (Windows)
echo ==========================================
echo.

REM fix: use the directory where the script is located instead of the current working directory
set "PROJECT_ROOT=%~dp0"
REM removes trailing backslash
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo 📍 Project directory: %PROJECT_ROOT%
echo.

REM switches to the project directory
cd /d "%PROJECT_ROOT%"
if %errorlevel% neq 0 (
    echo ❌ Unable to access project directory
    pause
    exit /b 1
)

REM Validation Project Structure
echo [0/4] 🔍 Verify project structure...
if not exist "pyproject.toml" (
    echo ❌ pyproject.toml file not found: %PROJECT_ROOT%
    echo.
    echo please check:
    echo 1. Is setup-windows.bat in the project root directory?
    echo 2. Are the project files complete?
    echo.
    echo current directory contents:
    dir /b
    echo.
    pause
    exit /b 1
)
echo ✅ pyproject.toml found
echo.

REM check Python
echo [1/4] 🐍 Check Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not detected, please install Python 3.10+ first
    echo download address: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i
echo.

REM Check UV
echo [2/4] 🔧 Check UV...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo UV is not installed and is being installed automatically...
    echo.
    
    echo Try method 1: PowerShell installation...
    powershell -ExecutionPolicy Bypass -Command "try { irm https://astral.sh/uv/install.ps1 | iex; exit 0 } catch { Write-Host 'PowerShell installation failed'; exit 1 }"
    
    if %errorlevel% neq 0 (
        echo.
        echo method 1 fails, try method 2: pip installation...
        python -m pip install --upgrade uv
        
        if %errorlevel% neq 0 (
            echo.
            echo ❌ Automatic installation failed
            echo.
            echo Please install UV manually, optional method:
            echo.
            echo method 1 - pip:
            echo     python -m pip install uv
            echo.
            echo method 2 - pipx:
            echo     pip install pipx
            echo     pipx install uv
            echo.
            echo method 3 - manual download:
            echo visit: https://docs.astral.sh/uv/getting-started/installation/
            echo.
            pause
            exit /b 1
        )
    )
    
    echo.
    echo ✅ UV installation completed!
    echo.
    echo ⚠️ IMPORTANT: Please follow these steps:
    echo 1. Close this window
    echo 2. Reopen the command prompt (or PowerShell)
    echo 3. Return to the project directory: %PROJECT_ROOT%
    echo 4. Rerun this script: setup-windows.bat
    echo.
    pause
    exit /b 0
) else (
    for /f "tokens=*" %%i in ('uv --version') do echo ✅ %%i
)
echo.

echo [3/4] 📦 Install project dependencies...
echo working directory: %PROJECT_ROOT%
echo.

REM ensures execution in the project directory
cd /d "%PROJECT_ROOT%"
uv sync
if %errorlevel% neq 0 (
    echo.
    echo ❌ Dependency installation failed
    echo.
    echo Possible reasons:
    echo 1. Network connection problem
    echo 2. Python version is incompatible (requires ^>= 3.10)
    echo 3. pyproject.toml file format error
    echo.
    echo troubleshooting:
    echo - Check network connection
    echo - Verify Python version: python --version
    echo - try verbose output: uv sync --verbose
    echo.
    echo project directory: %PROJECT_ROOT%
    echo.
    pause
    exit /b 1
)
echo.
echo ✅ Dependencies installed successfully
echo.

echo [4/4] ⚙️ Check configuration file...
if not exist "config\config.yaml" (
    echo ⚠️ The configuration file does not exist: config\config.yaml
    if exist "config\config.example.yaml" (
        echo.
        echo creates the configuration file:
        echo 1. Copy: copy config\config.example.yaml config\config.yaml
        echo 2. Edit: notepad config\config.yaml
        echo 3. Fill in the API key
    )
    echo.
) else (
    echo ✅ config\config.yaml already exists
)
echo.

REM Get UV path
for /f "tokens=*" %%i in ('where uv 2^>nul') do set "UV_PATH=%%i"
if not defined UV_PATH (
    set "UV_PATH=uv"
)

echo.
echo ==========================================
echo deployment completed!
echo ==========================================
echo.
echo 📋 MCP server configuration information (for Claude Desktop):
echo.
echo command: %UV_PATH%
echo working directory: %PROJECT_ROOT%
echo.
echo parameters (fill in line by line):
echo     --directory
echo     %PROJECT_ROOT%
echo     run
echo     python
echo     -m
echo     mcp_server.server
echo.
echo 📖 Detailed tutorial: README-Cherry-Studio.md
echo.
echo.
pause