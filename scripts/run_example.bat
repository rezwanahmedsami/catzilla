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
echo [33mUsage: %~nx0 [debug_options] ^<example_path^>[0m
echo.
echo [34mDebug Options:[0m
echo   [36m--debug[0m     Enable both C and Python debug logging
echo   [36m--debug_c[0m   Enable C debug logging only
echo   [36m--debug_py[0m  Enable Python debug logging only
echo.
echo [34mExamples:[0m
echo   %~nx0 examples\hello_world\main.py
echo   %~nx0 --debug examples\hello_world\main.py
echo   %~nx0 --debug_c examples\hello_world\main.py
echo   %~nx0 --debug_py examples\hello_world\main.py
echo.
echo [34mDebug Environment Variables:[0m
echo   [36mCATZILLA_C_DEBUG=1[0m  - Shows C-level debugging (server, router, HTTP parsing)
echo   [36mCATZILLA_DEBUG=1[0m    - Shows Python-level debugging (types, app, request processing)
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
    echo [31mError: No example path provided[0m
    echo.
    call :print_usage
    exit /b 1
)

REM Check if example file exists
if not exist "%PROJECT_ROOT%\%EXAMPLE_PATH%" (
    echo [31mError: Example file '%EXAMPLE_PATH%' not found[0m
    echo [33mMake sure the path is relative to the project root.[0m
    exit /b 1
)

REM Set debug environment variables
if %DEBUG_C%==1 (
    echo [36mEnabling C debug logging...[0m
    set CATZILLA_C_DEBUG=1
)

if %DEBUG_PY%==1 (
    echo [36mEnabling Python debug logging...[0m
    set CATZILLA_DEBUG=1
)

REM Set PYTHONPATH to include the python directory
set PYTHONPATH=%PROJECT_ROOT%\python;%PYTHONPATH%

REM Change to project root directory
cd /d "%PROJECT_ROOT%"

REM Display startup message
echo [32m🚀 Starting Catzilla example: %EXAMPLE_PATH%[0m
echo.

if %DEBUG_C%==1 echo [36mC Debug Mode: ENABLED[0m
if %DEBUG_PY%==1 echo [36mPython Debug Mode: ENABLED[0m
if %DEBUG_C%==0 if %DEBUG_PY%==0 echo [33mDebug Mode: DISABLED (use --debug to enable)[0m

echo [33m────────────────────────────────────────[0m
echo.

REM Run the example
python "%EXAMPLE_PATH%"
set exit_code=%errorlevel%

echo.
echo [33m────────────────────────────────────────[0m

if %exit_code%==0 (
    echo [32m✅ Example completed successfully[0m
) else (
    echo [31m❌ Example failed with exit code %exit_code%[0m
)

exit /b %exit_code%

REM Start by parsing arguments
call :parse_args %*
