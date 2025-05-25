@echo off
REM Windows batch script for building Catzilla
setlocal enabledelayedexpansion

echo [33m🔨 Starting Catzilla development build...[0m

REM 1. Clean previous builds
echo.
echo [32mCleaning previous builds...[0m
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%d in (*.egg-info) do rmdir /s /q "%%d"
for /r . %%f in (*.pyd) do del "%%f"
for /r . %%f in (*.pyc) do del "%%f"
for /d /r . %%d in (__pycache__) do rmdir /s /q "%%d"

REM 2. Create build directory
echo.
echo [32mCreating build directory...[0m
mkdir build
cd build

REM 3. Configure with CMake
echo.
echo [32mConfiguring with CMake...[0m

REM Detect number of cores for parallel build
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value ^| find "="') do set cores=%%i

REM Find Python executable
where python >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
) else (
    where python3 >nul 2>&1
    if %errorlevel% == 0 (
        for /f "tokens=*" %%i in ('where python3') do set PYTHON_EXE=%%i
    ) else (
        echo [31mError: Python not found in PATH[0m
        exit /b 1
    )
)

echo Using Python: !PYTHON_EXE!

cmake .. -DCMAKE_BUILD_TYPE=Debug -DPython3_EXECUTABLE="!PYTHON_EXE!"
if %errorlevel% neq 0 (
    echo [31mCMake configuration failed![0m
    exit /b 1
)

REM 4. Build
echo.
echo [32mBuilding...[0m
cmake --build . --config Debug -j %cores%
if %errorlevel% neq 0 (
    echo [31mBuild failed![0m
    exit /b 1
)

REM 5. Install
echo.
echo [32mInstalling...[0m
cd ..

REM Uninstall any existing version
python -m pip uninstall -y catzilla 2>nul

REM Install in development mode
python -m pip install -e .
if %errorlevel% neq 0 (
    echo [31mInstallation failed![0m
    exit /b 1
)

echo.
echo [32m✅ Build complete![0m
echo [33mYou can now run examples with: scripts\run_example.bat examples\hello_world\main.py[0m
