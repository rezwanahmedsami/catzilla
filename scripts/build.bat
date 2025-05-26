@echo off
REM Professional Windows build script for Catzilla
REM Supports multiple build configurations and provides clear error handling
setlocal enabledelayedexpansion

REM Parse command line arguments
set BUILD_TYPE=%1
set VERBOSE=%2

REM Show help if requested
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="/?" goto :show_help

REM Set default build type based on Python installation
if "%BUILD_TYPE%"=="" (
    echo Detecting optimal build configuration...
    set BUILD_TYPE=auto
)

echo Starting Catzilla professional build...
echo Build Configuration: %BUILD_TYPE%

REM 1. Clean previous builds
echo.
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%d in (*.egg-info) do rmdir /s /q "%%d"
for /r . %%f in (*.pyd) do del "%%f" 2>nul
for /r . %%f in (*.pyc) do del "%%f" 2>nul
for /d /r . %%d in (__pycache__) do rmdir /s /q "%%d" 2>nul

REM 2. Create build directory
echo.
echo Creating build directory...
mkdir build
cd build

REM 3. Detect Python and system configuration
echo.
echo Detecting Python configuration...

REM Find Python executable
where python >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
) else (
    where python3 >nul 2>&1
    if %errorlevel% == 0 (
        for /f "tokens=*" %%i in ('where python3') do set PYTHON_EXE=%%i
    ) else (
        echo Error: Python not found in PATH
        echo Tip: Install Python from python.org or use 'winget install Python.Python.3'
        exit /b 1
    )
)

echo   Python found: !PYTHON_EXE!

REM Detect number of cores for parallel build
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value ^| find "=" 2^>nul') do set cores=%%i
REM Strip any whitespace/newlines from cores variable
for /f "tokens=* delims= " %%a in ("!cores!") do set cores=%%a
if "!cores!"=="" set cores=2
echo   CPU cores detected: !cores!

REM 4. Configure with CMake
echo.
echo Configuring with CMake...

REM Determine the actual build type to use - using immediate assignment
if "%BUILD_TYPE%"=="auto" (
    echo   Using Release build (auto mode default for maximum compatibility)
    goto :set_release
) else if "%BUILD_TYPE%"=="Debug" (
    echo   Debug build requested - using Release for maximum compatibility
    echo   Note: Python debug libraries are rarely available, using Release build
    goto :set_release
) else (
    echo   Using explicit build type: %BUILD_TYPE%
    goto :set_explicit
)

:set_release
set ACTUAL_BUILD_TYPE=Release
goto :continue_build

:set_debug
set ACTUAL_BUILD_TYPE=Debug
goto :continue_build

:set_relwithdebinfo
set ACTUAL_BUILD_TYPE=RelWithDebInfo
goto :continue_build

:set_explicit
set ACTUAL_BUILD_TYPE=%BUILD_TYPE%
goto :continue_build

:continue_build
echo   Final build type: %ACTUAL_BUILD_TYPE%
echo   DEBUG: BUILD_TYPE="%BUILD_TYPE%", ACTUAL_BUILD_TYPE="%ACTUAL_BUILD_TYPE%"

REM Run CMake configuration only once
cmake .. -DCMAKE_BUILD_TYPE=%ACTUAL_BUILD_TYPE% -DPython3_EXECUTABLE="!PYTHON_EXE!"

if %errorlevel% neq 0 (
    echo CMake configuration failed!
    echo Common solutions:
    echo   - Ensure CMake is installed: 'winget install Kitware.CMake'
    echo   - Ensure Visual Studio Build Tools are installed
    echo   - Try running from Visual Studio Developer Command Prompt
    exit /b 1
)

REM 5. Build with appropriate configuration
echo.
echo Building Catzilla...
echo   DEBUG: About to build with config "%ACTUAL_BUILD_TYPE%" and !cores! cores

REM Use the determined build type for building
echo   Running: cmake --build . --config %ACTUAL_BUILD_TYPE% --parallel !cores!
cmake --build . --config %ACTUAL_BUILD_TYPE% --parallel !cores!

if %errorlevel% neq 0 (
    echo Build failed!
    echo Common solutions:
    echo   - Check if Python development headers are installed
    echo   - Try different build type: build.bat Release
    echo   - For Debug builds, ensure Python debug libraries are available
    exit /b 1
)

REM 6. Install in development mode
echo.
echo Installing in development mode...
cd ..

REM Uninstall any existing version
python -m pip uninstall -y catzilla 2>nul

REM Install in development mode
python -m pip install -e .
if %errorlevel% neq 0 (
    echo Installation failed!
    echo Try: python -m pip install --user -e .
    exit /b 1
)

echo.
echo Build completed successfully!
echo Build Summary:
echo   - Configuration: %ACTUAL_BUILD_TYPE%
echo   - Python: !PYTHON_EXE!
echo   - Cores used: !cores!
echo.
echo Next steps:
echo   - Run examples: scripts\run_example.bat examples\hello_world\main.py
echo   - Run tests: scripts\run_tests.bat
echo   - Check performance: cd benchmarks && run_all.bat
goto :eof

:show_help
echo Catzilla Professional Build Script
echo.
echo Usage:
echo   build.bat [BUILD_TYPE] [OPTIONS]
echo.
echo Build Types:
echo   auto         Use Release mode for maximum compatibility (default)
echo   Debug        Use Release mode (Python debug libs rarely available)
echo   Release      Optimized build (recommended for production)
echo   RelWithDebInfo   Optimized + debug symbols (best for development)
echo   MinSizeRel   Minimal size optimized build
echo.
echo Options:
echo   --help, -h, /?   Show this help message
echo.
echo Examples:
echo   build.bat                    # Auto-detect optimal configuration
echo   build.bat Release           # Build optimized release version
echo   build.bat Debug             # Build with full debugging
echo   build.bat RelWithDebInfo    # Build optimized with debug symbols
echo.
echo Tips:
echo   - Use 'auto' for best compatibility across different Python installations (uses Release)
echo   - Use 'RelWithDebInfo' for development on Windows (debugging without Python debug libs)
echo   - Use 'Release' for production builds or benchmarking
echo   - Debug mode also uses Release since Python debug libraries are rarely available
goto :eof
