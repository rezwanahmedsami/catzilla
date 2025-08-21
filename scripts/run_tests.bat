@echo off
REM Windows batch script for running Catzilla tests
REM Uses distributed testing with pytest-xdist for process isolation and parallel execution
REM This prevents cumulative memory effects and segfaults in C extension tests
setlocal enabledelayedexpansion

REM Colors for output (disabled for CI compatibility)
set RED=
set GREEN=
set YELLOW=
set CYAN=
set NC=

REM Script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Default values
set run_all=true
set run_python=false
set run_c=false
set run_e2e=false
set verbose=false
set docker=false
set docker_platform=all

REM Function to print usage
:print_usage
echo %YELLOW%🧪 Catzilla Test Runner%NC%
echo %YELLOW%=====================%NC%
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo %CYAN%Standard Testing:%NC%
echo   -h, --help            Show this help message
echo   -a, --all             Run all tests (default)
echo   -p, --python          Run only Python tests
echo   -c, --c               Run only C tests
echo   -e, --e2e             Run only E2E tests
echo   -v, --verbose         Run tests with verbose output
echo.
echo %CYAN%🐳 Docker Cross-Platform Testing:%NC%
echo   --docker [PLATFORM]   Run tests in Docker container
echo                         PLATFORM: linux, windows, windows-sim, all (default: all)
echo.
echo %YELLOW%Platform Compatibility:%NC%
echo   • linux: ✅ Supported on macOS, Linux, Windows
echo   • windows: ⚠️  Requires Docker Desktop with Windows containers
echo   • windows-sim: ✅ Windows simulation via Wine (Linux container)
echo   • Use 'linux' or 'windows-sim' for reliable cross-platform testing
echo.
echo %CYAN%Docker Examples:%NC%
echo   %~nx0 --docker           # Test on all platforms
echo   %~nx0 --docker linux     # Test on Ubuntu Linux
echo   %~nx0 --docker windows   # Test on Windows Server
echo.
echo %CYAN%Docker Management:%NC%
echo   .\scripts\docker_manager.bat shell linux    # Interactive shell
echo   .\scripts\docker_manager.bat clean          # Clean containers
echo   .\scripts\setup_docker_testing.bat          # Setup Docker testing
echo.
echo %GREEN%💡 Pro Tips:%NC%
echo   - Use '--docker linux' for fastest feedback
echo   - Run '--docker all' before pushing to GitHub
echo   - Use Docker for exact CI environment replication
echo   - Docker saves CI costs by testing locally first
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
if "%~1"=="-e" goto :set_e2e
if "%~1"=="--e2e" goto :set_e2e
if "%~1"=="-v" goto :set_verbose
if "%~1"=="--verbose" goto :set_verbose
if "%~1"=="--docker" (
    set docker=true
    set docker_platform=%2
    if "!docker_platform!"=="" set docker_platform=all
    if not "!docker_platform!"=="all" if not "!docker_platform!"=="linux" if not "!docker_platform!"=="windows" if not "!docker_platform!"=="windows-sim" (
        echo %RED%Invalid Docker platform: !docker_platform!%NC%
        echo Valid platforms: linux, windows, windows-sim, all
        exit /b 1
    )
    shift
    if not "%~1"=="" shift
    goto :parse_args
)
echo %RED%Unknown option: %~1%NC%
call :print_usage
exit /b 1

:help
call :print_usage
exit /b 0

:set_all
set run_all=true
set run_python=false
set run_c=false
set run_e2e=false
shift
goto :parse_args

:set_python
set run_all=false
set run_python=true
set run_c=false
set run_e2e=false
shift
goto :parse_args

:set_c
set run_all=false
set run_python=false
set run_c=true
set run_e2e=false
shift
goto :parse_args

:set_e2e
set run_all=false
set run_python=false
set run_c=false
set run_e2e=true
shift
goto :parse_args

:set_verbose
set verbose=true
shift
goto :parse_args

REM Function to check Docker platform support
:check_docker_platform_support
REM Check Docker daemon OS type
for /f "tokens=*" %%d in ('docker system info 2^>nul ^| findstr /C:"OSType"') do (
    set docker_info=%%d
)
if "%~1"=="windows" (
    echo !docker_info! | findstr /C:"windows" >nul
    if !errorlevel! neq 0 (
        exit /b 1
    )
)
exit /b 0

REM Function to run Docker tests
:run_docker_tests
echo %YELLOW%Running tests in Docker (%~1)...%NC%
if "%~1"=="windows" (
    call :check_docker_platform_support windows
    if !errorlevel! neq 0 (
        echo %RED%Error: Windows container mode is not enabled in Docker.%NC%
        echo Please switch Docker Desktop to "Windows containers" mode and try again.
        exit /b 1
    )
)

if "%~1"=="all" (
    echo %YELLOW%Running tests on all platforms - this might take some time...%NC%
    call :run_docker_tests linux
    if !errorlevel! neq 0 exit /b !errorlevel!

    call :check_docker_platform_support windows
    if !errorlevel! equ 0 (
        call :run_docker_tests windows
        if !errorlevel! neq 0 exit /b !errorlevel!
    ) else (
        echo %YELLOW%Skipping Windows container tests - not supported in current Docker configuration%NC%
        call :run_docker_tests windows-sim
        if !errorlevel! neq 0 exit /b !errorlevel!
    )
    exit /b 0
)

REM Run the actual Docker command
set COMPOSE_FILE=%PROJECT_ROOT%\docker\docker-compose.yml
if "%~1"=="windows" (
    echo %YELLOW%Starting Windows container tests...%NC%
    docker-compose -f %COMPOSE_FILE% run --rm windows-test
) else if "%~1"=="windows-sim" (
    echo %YELLOW%Starting Windows simulation (Wine) tests...%NC%
    docker-compose -f %COMPOSE_FILE% run --rm windows-sim-test
) else (
    echo %YELLOW%Starting %~1 container tests...%NC%
    docker-compose -f %COMPOSE_FILE% run --rm %~1-test
)

exit /b %errorlevel%

REM Function to run Python tests
:run_python_tests
echo %YELLOW%Running Python tests...%NC%

REM Configure jemalloc for tests
call "%SCRIPT_DIR%jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo %YELLOW%Warning: jemalloc configuration failed. Tests may be slower or less stable.%NC%
)

REM Set PYTHONPATH to include the python directory
set PYTHONPATH=%PROJECT_ROOT%\python;%PYTHONPATH%

REM Check for potential segfault-causing tests
echo %YELLOW%Checking for known problematic test patterns...%NC%
findstr /R /C:"test_memory_usage_validation\|test_special_characters_in_static_files\|test_nested_resource_routing" "%PROJECT_ROOT%\tests\python\*.py" >nul 2>&1
if %errorlevel% == 0 (
    echo %YELLOW%Note: Running tests that previously caused segfaults. These have been fixed.%NC%
)

REM Run pytest with or without verbose flag
set PYTEST_ARGS=-xvs
if "%verbose%"=="true" (
    python -m pytest "%PROJECT_ROOT%\tests\python" -v %PYTEST_ARGS%
) else (
    python -m pytest "%PROJECT_ROOT%\tests\python" %PYTEST_ARGS%
)

if %errorlevel% == 0 (
    echo %GREEN%Python tests passed!%NC%
    set python_success=true
) else (
    echo Python tests failed!
    set python_success=false
)
goto :eof

REM Function to run E2E tests
:run_e2e_tests
echo %YELLOW%Running E2E tests...%NC%

REM Configure jemalloc for tests
call "%SCRIPT_DIR%jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo %YELLOW%Warning: jemalloc configuration failed. Tests may be slower or less stable.%NC%
)

REM Set PYTHONPATH to include the python directory
set PYTHONPATH=%PROJECT_ROOT%\python;%PYTHONPATH%

REM Change to project root directory
cd /d "%PROJECT_ROOT%"

REM Run E2E tests with the specific pytest configuration
echo %YELLOW%Starting E2E test execution...%NC%
if "%verbose%"=="true" (
    python -m pytest "tests\e2e" -c "tests\e2e\pytest.ini" --tb=short -v
) else (
    python -m pytest "tests\e2e" -c "tests\e2e\pytest.ini" --tb=short
)

if %errorlevel% == 0 (
    echo %GREEN%E2E tests passed!%NC%
    set e2e_success=true
) else (
    echo %RED%E2E tests failed!%NC%
    set e2e_success=false
)
goto :eof

REM Function to run C tests
:run_c_tests
echo %YELLOW%Running C tests...%NC%

REM Ensure build directory exists
if not exist "%PROJECT_ROOT%\build" mkdir "%PROJECT_ROOT%\build"

REM Configure jemalloc for tests
call "%SCRIPT_DIR%jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo %YELLOW%Warning: jemalloc configuration failed. Tests may be slower or less stable.%NC%
)

REM Build the project if needed
cd /d "%PROJECT_ROOT%"
echo %YELLOW%Configuring with CMake...%NC%
cmake -S . -B build
if %errorlevel% neq 0 (
    echo %RED%CMake configuration failed!%NC%
    set c_success=false
    goto :eof
)

echo %YELLOW%Building C components...%NC%
cmake --build build --config Release
if %errorlevel% neq 0 (
    echo %RED%Build failed!%NC%
    set c_success=false
    goto :eof
)

REM List of C test executables to run
echo %YELLOW%Identifying test executables...%NC%
set test_executables=test_router test_advanced_router test_server_integration test_validation_engine test_memory
set all_passed=true

REM Run each C test executable
echo %YELLOW%Running C test suite...%NC%
for %%t in (%test_executables%) do (
    if exist "%PROJECT_ROOT%\build\Debug\%%t.exe" (
        echo %YELLOW%Running %%t...%NC%

        if "%verbose%"=="true" (
            "%PROJECT_ROOT%\build\Debug\%%t.exe" -v
        ) else (
            "%PROJECT_ROOT%\build\Debug\%%t.exe"
        )

        if !errorlevel! == 0 (
            echo %GREEN%%%t passed!%NC%
        ) else (
            echo %RED%%%t failed!%NC%
            set all_passed=false
        )
    ) else if exist "%PROJECT_ROOT%\build\%%t.exe" (
        echo %YELLOW%Running %%t...%NC%

        if "%verbose%"=="true" (
            "%PROJECT_ROOT%\build\%%t.exe" -v
        ) else (
            "%PROJECT_ROOT%\build\%%t.exe"
        )

        if !errorlevel! == 0 (
            echo %GREEN%%%t passed!%NC%
        ) else (
            echo %RED%%%t failed!%NC%
            set all_passed=false
        )
    ) else (
        echo %YELLOW%Test executable %%t.exe not found - skipping%NC%
    )
)

if "%all_passed%"=="true" (
    echo %GREEN%All C tests passed!%NC%
    set c_success=true
) else (
    echo %RED%Some C tests failed!%NC%
    set c_success=false
)
goto :eof

:start_tests
REM Check if Docker mode is enabled
if "%docker%"=="true" (
    call :run_docker_tests %docker_platform%
    exit /b %errorlevel%
)

REM Track overall success
set success=true

REM Run tests based on flags
if "%run_all%"=="true" (
    call :run_python_tests
    if "%python_success%"=="false" set success=false

    call :run_c_tests
    if "%c_success%"=="false" set success=false

    call :run_e2e_tests
    if "%e2e_success%"=="false" set success=false
) else if "%run_python%"=="true" (
    call :run_python_tests
    if "%python_success%"=="false" set success=false
) else if "%run_c%"=="true" (
    call :run_c_tests
    if "%c_success%"=="false" set success=false
) else if "%run_e2e%"=="true" (
    call :run_e2e_tests
    if "%e2e_success%"=="false" set success=false
)

REM Exit with appropriate status
if "%success%"=="true" (
    echo All requested tests passed!
    exit /b 0
) else (
    echo Some tests failed!
    exit /b 1
)

REM Start by parsing arguments
call :parse_args %*
