@echo off
REM Windows batch script for running Catzilla examples
setlocal enabledelayedexpansion

REM Script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Debug flags
set DEBUG_C=0
set DEBUG_PY=0
set EXAMPLE_PATH=

REM Function to print usage
:print_usage
echo Usage: %~nx0 [debug_options] ^<example_path^>
echo.
echo Debug Options:
echo   --debug     Enable both C and Python debug logging
echo   --debug_c   Enable C debug logging only
echo   --debug_py  Enable Python debug logging only
echo.
echo Examples:
echo   %~nx0 examples\hello_world\main.py
echo   %~nx0 --debug examples\hello_world\main.py
echo   %~nx0 --debug_c examples\hello_world\main.py
echo   %~nx0 --debug_py examples\hello_world\main.py
echo.
echo Debug Environment Variables:
echo   CATZILLA_C_DEBUG=1  - Shows C-level debugging (server, router, HTTP parsing)
echo   CATZILLA_DEBUG=1    - Shows Python-level debugging (types, app, request processing)
goto :eof

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :check_example_path
if "%~1"=="--debug" (
    set DEBUG_C=1
    set DEBUG_PY=1
    shift
    goto :parse_args
)
if "%~1"=="--debug_c" (
    set DEBUG_C=1
    shift
    goto :parse_args
)
if "%~1"=="--debug_py" (
    set DEBUG_PY=1
    shift
    goto :parse_args
)
if "%~1"=="-h" goto :help
if "%~1"=="--help" goto :help

REM Assume remaining argument is the example path
set EXAMPLE_PATH=%~1
shift
goto :parse_args

:help
call :print_usage
exit /b 0

:check_example_path
if "%EXAMPLE_PATH%"=="" (
    echo Error: No example path provided
    echo.
    call :print_usage
    exit /b 1
)

REM Check if example file exists
if not exist "%PROJECT_ROOT%\%EXAMPLE_PATH%" (
    echo Error: Example file '%EXAMPLE_PATH%' not found
    echo Make sure the path is relative to the project root.
    exit /b 1
)

REM Set debug environment variables
if %DEBUG_C%==1 (
    echo Enabling C debug logging...
    set CATZILLA_C_DEBUG=1
)

if %DEBUG_PY%==1 (
    echo Enabling Python debug logging...
    set CATZILLA_DEBUG=1
)

REM Configure jemalloc for optimal performance
call "%SCRIPT_DIR%jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo Warning: jemalloc configuration failed. Example may run slower.
) else (
    echo jemalloc configured successfully
)

REM Set PYTHONPATH to include the python directory
set PYTHONPATH=%PROJECT_ROOT%\python;%PYTHONPATH%

REM Change to project root directory
cd /d "%PROJECT_ROOT%"

REM Display startup message
echo 🚀 Starting Catzilla example: %EXAMPLE_PATH%
echo.

if %DEBUG_C%==1 echo C Debug Mode: ENABLED
if %DEBUG_PY%==1 echo Python Debug Mode: ENABLED
if %DEBUG_C%==0 if %DEBUG_PY%==0 echo Debug Mode: DISABLED (use --debug to enable)

echo ────────────────────────────────────────
echo.

REM Run the example
python "%EXAMPLE_PATH%"
set exit_code=%errorlevel%

echo.
echo ────────────────────────────────────────

if %exit_code%==0 (
    echo ✅ Example completed successfully
) else (
    echo ❌ Example failed with exit code %exit_code%
)

exit /b %exit_code%

REM Start by parsing arguments
call :parse_args %*
