@echo off
REM Windows batch script for Catzilla development build
setlocal enabledelayedexpansion

REM Colors for output
set GREEN=[32m
set YELLOW=[33m
set RED=[31m
set NC=[0m

echo %YELLOW%🔨 Starting Catzilla development build...%NC%

REM 1. Clean previous builds
echo.
echo %GREEN%Cleaning previous builds...%NC%
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%d in (*.egg-info) do rmdir /s /q "%%d"
for /r . %%f in (*.pyd) do del "%%f" 2>nul
for /r . %%f in (*.pyc) do del "%%f" 2>nul
for /d /r . %%d in (__pycache__) do rmdir /s /q "%%d" 2>nul

REM 2. Create build directory
echo.
echo %GREEN%Creating build directory...%NC%
mkdir build
cd build

REM 3. Configure jemalloc for optimal build performance
echo.
echo %GREEN%Configuring with CMake...%NC%

REM Configure jemalloc for optimal build performance
call "%~dp0jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo %YELLOW%Warning: jemalloc configuration failed. Build may be slower.%NC%
)

REM Find Python executable
where python >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
) else (
    where python3 >nul 2>&1
    if %errorlevel% == 0 (
        for /f "tokens=*" %%i in ('where python3') do set PYTHON_EXE=%%i
    ) else (
        echo %RED%Error: Python not found in PATH%NC%
        echo Tip: Install Python from python.org
        exit /b 1
    )
)

REM Detect number of cores for parallel build
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value ^| find "=" 2^>nul') do set cores=%%i
REM Strip any whitespace/newlines from cores variable
for /f "tokens=* delims= " %%a in ("!cores!") do set cores=%%a
if "!cores!"=="" set cores=2

REM Configure with CMake
echo %GREEN%Passing jemalloc environment variables to CMake...%NC%
if defined JEMALLOC_LIBRARY (
    echo %GREEN%Using jemalloc from: %JEMALLOC_LIBRARY%%NC%
    cmake .. -DCMAKE_BUILD_TYPE=Debug -DPython3_EXECUTABLE="%PYTHON_EXE%" ^
        -DJEMALLOC_LIBRARY="%JEMALLOC_LIBRARY%" ^
        -DJEMALLOC_INCLUDE_DIR="%JEMALLOC_INCLUDE_DIR%"
) else (
    cmake .. -DCMAKE_BUILD_TYPE=Debug -DPython3_EXECUTABLE="%PYTHON_EXE%"
)

if %errorlevel% neq 0 (
    echo %RED%CMake configuration failed!%NC%
    exit /b 1
)

REM 4. Build
echo.
echo %GREEN%Building...%NC%
cmake --build . -j%cores%
if %errorlevel% neq 0 (
    echo %RED%Build failed!%NC%
    exit /b 1
)
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

REM 5. Copy the built extension to the right place
echo.
echo %GREEN%Installing...%NC%
cd ..

REM Uninstall any existing version
python -m pip uninstall -y catzilla 2>nul

REM Install in development mode
python -m pip install -e .
if %errorlevel% neq 0 (
    echo %RED%Installation failed!%NC%
    exit /b 1
)

echo.
echo %GREEN%✅ Build complete!%NC%
echo %YELLOW%You can now run examples with: scripts\run_example.bat examples\hello_world\main.py%NC%
exit /b 0
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
