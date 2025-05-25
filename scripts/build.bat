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
    echo [33m🔍 Detecting optimal build configuration...[0m
    set BUILD_TYPE=auto
)

echo [33m🔨 Starting Catzilla professional build...[0m
echo [33m📋 Build Configuration: %BUILD_TYPE%[0m

REM 1. Clean previous builds
echo.
echo [32m🧹 Cleaning previous builds...[0m
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%d in (*.egg-info) do rmdir /s /q "%%d"
for /r . %%f in (*.pyd) do del "%%f" 2>nul
for /r . %%f in (*.pyc) do del "%%f" 2>nul
for /d /r . %%d in (__pycache__) do rmdir /s /q "%%d" 2>nul

REM 2. Create build directory
echo.
echo [32m📁 Creating build directory...[0m
mkdir build
cd build

REM 3. Detect Python and system configuration
echo.
echo [32m🐍 Detecting Python configuration...[0m

REM Find Python executable
where python >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
) else (
    where python3 >nul 2>&1
    if %errorlevel% == 0 (
        for /f "tokens=*" %%i in ('where python3') do set PYTHON_EXE=%%i
    ) else (
        echo [31m❌ Error: Python not found in PATH[0m
        echo [33m💡 Tip: Install Python from python.org or use 'winget install Python.Python.3'[0m
        exit /b 1
    )
)

echo [32m   ✅ Python found: !PYTHON_EXE![0m

REM Detect number of cores for parallel build
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value ^| find "=" 2^>nul') do set cores=%%i
if "!cores!"=="" set cores=2
echo [32m   ✅ CPU cores detected: !cores![0m

REM 4. Configure with CMake
echo.
echo [32m⚙️  Configuring with CMake...[0m

if "%BUILD_TYPE%"=="auto" (
    echo [33m   🎯 Using automatic build type detection (using Release for maximum compatibility)[0m
    cmake .. -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE="!PYTHON_EXE!"
) else if "%BUILD_TYPE%"=="Debug" (
    echo [33m   ⚠️  Debug build requested - checking for Python debug libraries...[0m
    python -c "import sys; import os; debug_lib = os.path.join(os.path.dirname(sys.executable), 'libs', f'python{sys.version_info.major}{sys.version_info.minor}_d.lib'); print('✅ Debug libraries found' if os.path.exists(debug_lib) else '❌ Debug libraries not found'); exit(0 if os.path.exists(debug_lib) else 1)" 2>nul
    if !errorlevel! neq 0 (
        echo [31m   ❌ Python debug libraries not found![0m
        echo [33m   💡 Using RelWithDebInfo instead (optimized + debug symbols)[0m
        echo [33m      This provides debugging capabilities without requiring Python debug libraries[0m
        set BUILD_TYPE=RelWithDebInfo
    )
    echo [33m   🎯 Using build type: !BUILD_TYPE![0m
    cmake .. -DCMAKE_BUILD_TYPE=!BUILD_TYPE! -DPython3_EXECUTABLE="!PYTHON_EXE!"
) else (
    echo [33m   🎯 Using explicit build type: %BUILD_TYPE%[0m
    cmake .. -DCMAKE_BUILD_TYPE=%BUILD_TYPE% -DPython3_EXECUTABLE="!PYTHON_EXE!"
)

if %errorlevel% neq 0 (
    echo [31m❌ CMake configuration failed![0m
    echo [33m💡 Common solutions:[0m
    echo [33m   - Ensure CMake is installed: 'winget install Kitware.CMake'[0m
    echo [33m   - Ensure Visual Studio Build Tools are installed[0m
    echo [33m   - Try running from Visual Studio Developer Command Prompt[0m
    exit /b 1
)

REM 5. Build with appropriate configuration
echo.
echo [32m🔧 Building Catzilla...[0m

if "%BUILD_TYPE%"=="auto" (
    REM For auto detection, we're using Release mode for maximum compatibility
    cmake --build . --config Release -j !cores!
) else (
    REM For explicit build type, use it for the build step too
    cmake --build . --config %BUILD_TYPE% -j !cores!
)

if %errorlevel% neq 0 (
    echo [31m❌ Build failed![0m
    echo [33m💡 Common solutions:[0m
    echo [33m   - Check if Python development headers are installed[0m
    echo [33m   - Try different build type: build.bat Release[0m
    echo [33m   - For Debug builds, ensure Python debug libraries are available[0m
    exit /b 1
)

REM 6. Install in development mode
echo.
echo [32m📦 Installing in development mode...[0m
cd ..

REM Uninstall any existing version
python -m pip uninstall -y catzilla 2>nul

REM Install in development mode
python -m pip install -e .
if %errorlevel% neq 0 (
    echo [31m❌ Installation failed![0m
    echo [33m💡 Try: python -m pip install --user -e .[0m
    exit /b 1
)

echo.
echo [32m🎉 Build completed successfully![0m
echo [33m📋 Build Summary:[0m
echo [33m   - Configuration: %BUILD_TYPE%[0m
echo [33m   - Python: !PYTHON_EXE![0m
echo [33m   - Cores used: !cores![0m
echo.
echo [33m🚀 Next steps:[0m
echo [33m   - Run examples: scripts\run_example.bat examples\hello_world\main.py[0m
echo [33m   - Run tests: scripts\run_tests.bat[0m
echo [33m   - Check performance: cd benchmarks && run_all.bat[0m
goto :eof

:show_help
echo [33m🔧 Catzilla Professional Build Script[0m
echo.
echo [32mUsage:[0m
echo   build.bat [BUILD_TYPE] [OPTIONS]
echo.
echo [32mBuild Types:[0m
echo   auto         Use Release mode for maximum compatibility (default)
echo   Debug        Full debugging symbols (automatically falls back to RelWithDebInfo if Python debug libs unavailable)
echo   Release      Optimized build (recommended for production)
echo   RelWithDebInfo   Optimized + debug symbols (best for development)
echo   MinSizeRel   Minimal size optimized build
echo.
echo [32mOptions:[0m
echo   --help, -h, /?   Show this help message
echo.
echo [32mExamples:[0m
echo   build.bat                    # Auto-detect optimal configuration
echo   build.bat Release           # Build optimized release version
echo   build.bat Debug             # Build with full debugging
echo   build.bat RelWithDebInfo    # Build optimized with debug symbols
echo.
echo [33m💡 Tips:[0m
echo   - Use 'auto' for best compatibility across different Python installations (uses Release)
echo   - Use 'RelWithDebInfo' for development on Windows (debugging without Python debug libs)
echo   - Use 'Release' for production builds or benchmarking
echo   - Use 'Debug' for full debugging (auto-falls back to RelWithDebInfo if needed)
goto :eof
