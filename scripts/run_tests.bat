@echo off
REM Windows batch script for running Catzilla tests
setlocal enabledelayedexpansion

REM Script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Default values
set run_all=true
set run_python=false
set run_c=false
set verbose=false

REM Function to print usage
:print_usage
echo [33mUsage: %~nx0 [OPTIONS][0m
echo Options:
echo   -h, --help     Show this help message
echo   -a, --all      Run all tests (default)
echo   -p, --python   Run only Python tests
echo   -c, --c        Run only C tests
echo   -v, --verbose  Run tests with verbose output
goto :eof

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :start_tests
if "%~1"=="-h" goto :help
if "%~1"=="--help" goto :help
if "%~1"=="-a" goto :set_all
if "%~1"=="--all" goto :set_all
if "%~1"=="-p" goto :set_python
if "%~1"=="--python" goto :set_python
if "%~1"=="-c" goto :set_c
if "%~1"=="--c" goto :set_c
if "%~1"=="-v" goto :set_verbose
if "%~1"=="--verbose" goto :set_verbose
echo [31mUnknown option: %~1[0m
call :print_usage
exit /b 1

:help
call :print_usage
exit /b 0

:set_all
set run_all=true
set run_python=false
set run_c=false
shift
goto :parse_args

:set_python
set run_all=false
set run_python=true
set run_c=false
shift
goto :parse_args

:set_c
set run_all=false
set run_python=false
set run_c=true
shift
goto :parse_args

:set_verbose
set verbose=true
shift
goto :parse_args

REM Function to run Python tests
:run_python_tests
echo [33mRunning Python tests...[0m

REM Configure jemalloc for tests
call "%SCRIPT_DIR%jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo [33mWarning: jemalloc configuration failed. Tests may be slower or less stable.[0m
)

REM Set PYTHONPATH to include the python directory
set PYTHONPATH=%PROJECT_ROOT%\python;%PYTHONPATH%

REM Check for potential segfault-causing tests
echo [33mChecking for known problematic test patterns...[0m
findstr /R /C:"test_memory_usage_validation\|test_special_characters_in_static_files\|test_nested_resource_routing" "%PROJECT_ROOT%\tests\python\*.py" >nul 2>&1
if %errorlevel% == 0 (
    echo [33mNote: Running tests that previously caused segfaults. These have been fixed.[0m
)

REM Run pytest with or without verbose flag
if "%verbose%"=="true" (
    python -m pytest "%PROJECT_ROOT%\tests\python" -v
) else (
    python -m pytest "%PROJECT_ROOT%\tests\python"
)

if %errorlevel% == 0 (
    echo [32mPython tests passed![0m
    set python_success=true
) else (
    echo [31mPython tests failed![0m
    set python_success=false
)
goto :eof

REM Function to run C tests
:run_c_tests
echo [33mRunning C tests...[0m

REM Ensure build directory exists
if not exist "%PROJECT_ROOT%\build" mkdir "%PROJECT_ROOT%\build"

REM Build the project if needed
cd /d "%PROJECT_ROOT%"
cmake -S . -B build
if %errorlevel% neq 0 (
    echo [31mCMake configuration failed![0m
    set c_success=false
    goto :eof
)

cmake --build build --config Debug
if %errorlevel% neq 0 (
    echo [31mBuild failed![0m
    set c_success=false
    goto :eof
)

REM List of C test executables to run
set test_executables=test_router test_advanced_router test_server_integration test_validation_engine
set all_passed=true

REM Run each C test executable
for %%t in (%test_executables%) do (
    if exist "%PROJECT_ROOT%\build\Debug\%%t.exe" (
        echo [33mRunning %%t...[0m

        if "%verbose%"=="true" (
            "%PROJECT_ROOT%\build\Debug\%%t.exe" -v
        ) else (
            "%PROJECT_ROOT%\build\Debug\%%t.exe"
        )

        if !errorlevel! == 0 (
            echo [32m%%t passed![0m
        ) else (
            echo [31m%%t failed![0m
            set all_passed=false
        )
    ) else if exist "%PROJECT_ROOT%\build\%%t.exe" (
        echo [33mRunning %%t...[0m

        if "%verbose%"=="true" (
            "%PROJECT_ROOT%\build\%%t.exe" -v
        ) else (
            "%PROJECT_ROOT%\build\%%t.exe"
        )

        if !errorlevel! == 0 (
            echo [32m%%t passed![0m
        ) else (
            echo [31m%%t failed![0m
            set all_passed=false
        )
    ) else (
        echo [31mC test executable %%t.exe not found![0m
        set all_passed=false
    )
)

if "%all_passed%"=="true" (
    echo [32mAll C tests passed![0m
    set c_success=true
) else (
    echo [31mSome C tests failed![0m
    set c_success=false
)
goto :eof

:start_tests
REM Track overall success
set success=true

REM Run tests based on flags
if "%run_all%"=="true" (
    call :run_python_tests
    if "%python_success%"=="false" set success=false

    call :run_c_tests
    if "%c_success%"=="false" set success=false
) else if "%run_python%"=="true" (
    call :run_python_tests
    if "%python_success%"=="false" set success=false
) else if "%run_c%"=="true" (
    call :run_c_tests
    if "%c_success%"=="false" set success=false
)

REM Exit with appropriate status
if "%success%"=="true" (
    echo [32mAll requested tests passed![0m
    exit /b 0
) else (
    echo [31mSome tests failed![0m
    exit /b 1
)

REM Start by parsing arguments
call :parse_args %*
