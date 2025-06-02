@echo off
REM Test Windows emoji compatibility in Catzilla scripts
setlocal enabledelayedexpansion

REM Script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Set PYTHONPATH
set PYTHONPATH=%PROJECT_ROOT%\python;%PYTHONPATH%

echo === Testing Windows Emoji Compatibility ===
echo.

REM Run the emoji compatibility test
python "%SCRIPT_DIR%test_windows_emoji.py"
if %errorlevel% neq 0 (
    echo Error running emoji compatibility test
    exit /b 1
)

echo.
echo If no Unicode errors occurred, the emoji compatibility fix is working correctly.
echo.
