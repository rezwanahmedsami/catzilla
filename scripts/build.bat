@echo off
REM Windows batch script for Catzilla development build
setlocal enabledelayedexpansion

echo 🔨 Starting Catzilla development build...

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Build jemalloc if needed
echo.
echo Step 1: Building jemalloc (if needed)...

REM Check if jemalloc source directory exists
echo DEBUG: Checking for jemalloc at: "%PROJECT_ROOT%\deps\jemalloc"
if not exist "%PROJECT_ROOT%\deps\jemalloc" (
    echo ⚠️  Warning: jemalloc source directory not found
    echo ⚠️  Tip: Initialize git submodules: git submodule update --init --recursive
    echo.
    echo DEBUG: PROJECT_ROOT = %PROJECT_ROOT%
    echo DEBUG: Contents of deps directory:
    if exist "%PROJECT_ROOT%\deps" (
        dir "%PROJECT_ROOT%\deps" /b
    ) else (
        echo DEBUG: deps directory does not exist
    )
    echo ⚠️  Continuing with system malloc - performance may be reduced
    set JEMALLOC_BUILD_RESULT=1
) else (
    echo DEBUG: Found jemalloc directory
    echo DEBUG: Contents of jemalloc directory:
    dir "%PROJECT_ROOT%\deps\jemalloc" /b | head -10

    REM Navigate to jemalloc directory and run build script
    cd /d "%PROJECT_ROOT%\deps\jemalloc"
    call "%SCRIPT_DIR%build_jemalloc.bat"
    set JEMALLOC_BUILD_RESULT=!errorlevel!

    REM Return to project root
    cd /d "%PROJECT_ROOT%"

    if !JEMALLOC_BUILD_RESULT! neq 0 (
        echo ⚠️  Warning: jemalloc build failed with exit code !JEMALLOC_BUILD_RESULT!
        echo ⚠️  Continuing with system malloc - performance may be reduced
    ) else (
        echo ✅ jemalloc build completed successfully
    )
)

REM Clean previous builds
echo.
echo Step 2: Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
for /d %%d in (*.egg-info) do (
    if exist "%%d" rmdir /s /q "%%d"
)
del /q /s *.pyd >nul 2>&1
del /q /s *.pyc >nul 2>&1
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

REM Create build directory
echo.
echo Step 3: Creating build directory...
mkdir build
cd build

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
echo.
echo Step 4: Configuring with CMake...
cmake .. -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE="%PYTHON_EXE%"

if %errorlevel% neq 0 (
    echo CMake configuration failed!
    echo Common solutions:
    echo   - Ensure CMake is installed: 'winget install Kitware.CMake'
    echo   - Ensure Visual Studio Build Tools are installed
    echo   - Try running from Visual Studio Developer Command Prompt
    exit /b 1
)

REM Build
echo.
echo Step 5: Building...
cmake --build . --config Release -j%cores%

if %errorlevel% neq 0 (
    echo Build failed!
    echo Common solutions:
    echo   - Check if Python development headers are installed
    echo   - Try different build type: build.bat Release
    echo   - For Debug builds, ensure Python debug libraries are available
    exit /b 1
)

REM Install in development mode
echo.
echo Step 6: Installing...
cd ..

REM Uninstall any existing version
python -m pip uninstall -y catzilla 2>nul

REM Install in development mode
python -m pip install -e .
if %errorlevel% neq 0 (
    echo Installation failed!
    exit /b 1
)

echo.
echo ✅ Build complete!
echo You can now run examples with: scripts\run_example.bat examples\hello_world\main.py
