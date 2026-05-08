@echo off
REM Windows batch script for Catzilla development build
setlocal enabledelayedexpansion

echo 🔨 Starting Catzilla development build...

REM Get script directory and project root
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"

cd /d "%PROJECT_ROOT%"

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
    dir "%PROJECT_ROOT%\deps\jemalloc" /b

    REM Navigate to jemalloc directory and run build script
    pushd "%PROJECT_ROOT%\deps\jemalloc"
    call "%SCRIPT_DIR%build_jemalloc.bat"
    set JEMALLOC_BUILD_RESULT=!errorlevel!

    REM Return to project root
    popd

    if !JEMALLOC_BUILD_RESULT! neq 0 (
        echo ⚠️  Warning: jemalloc build failed with exit code !JEMALLOC_BUILD_RESULT!
        echo ⚠️  Continuing with system malloc - performance may be reduced
        set "CATZILLA_USE_JEMALLOC="
    ) else (
        echo ✅ jemalloc build completed successfully
        set "CATZILLA_USE_JEMALLOC=1"
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
set "PYTHON_EXE="
if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe"
) else (
    if defined VIRTUAL_ENV (
        if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
            set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
        )
    )
)

if not defined PYTHON_EXE (
    where python3 >nul 2>&1
    if %errorlevel% == 0 (
        for /f "delims=" %%i in ('where python3') do (
            set "PYTHON_EXE=%%i"
            goto :python_found
        )
    ) else (
        where python >nul 2>&1
        if %errorlevel% == 0 (
            for /f "delims=" %%i in ('where python') do (
                set "PYTHON_EXE=%%i"
                goto :python_found
            )
        ) else (
            echo Error: Python not found in PATH
            echo Tip: Install Python from python.org
            exit /b 1
        )
    )
)

:python_found
echo Using Python: "%PYTHON_EXE%"

REM Find CMake executable
set "CMAKE_EXE="
where cmake >nul 2>&1
if %errorlevel% == 0 (
    for /f "delims=" %%i in ('where cmake') do (
        set "CMAKE_EXE=%%i"
        goto :cmake_found
    )
)

for %%i in (
    "C:\Program Files\CMake\bin\cmake.exe"
    "C:\Program Files (x86)\CMake\bin\cmake.exe"
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
    "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
) do (
    if exist "%%~i" (
        set "CMAKE_EXE=%%~fi"
        goto :cmake_found
    )
)

echo Error: CMake not found
echo Tip: Install CMake from https://cmake.org/download/ or with 'winget install Kitware.CMake'
exit /b 1

:cmake_found
echo Using CMake: "%CMAKE_EXE%"

REM Detect number of cores for parallel build
set "CORES=%NUMBER_OF_PROCESSORS%"
if "%CORES%"=="" set "CORES=2"

REM Configure with CMake
echo.
echo Step 4: Configuring with CMake...
"%CMAKE_EXE%" .. -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE="%PYTHON_EXE%"

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
"%CMAKE_EXE%" --build . --config Release --parallel %CORES%

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

REM Ensure packaging toolchain is compatible with editable installs in CI
echo Updating packaging tools...
"%PYTHON_EXE%" -m pip install --upgrade "packaging>=24.2" setuptools wheel
if %errorlevel% neq 0 (
    echo Warning: Failed to update packaging tools. Continuing with existing toolchain...
)

REM Uninstall any existing version
"%PYTHON_EXE%" -m pip uninstall -y catzilla 2>nul

REM Install in development mode
"%PYTHON_EXE%" -m pip install -e . --no-build-isolation
if %errorlevel% neq 0 (
    if defined GITHUB_ACTIONS (
        echo Editable install failed in CI, retrying with a standard install...
        "%PYTHON_EXE%" -m pip install . --no-build-isolation
        if %errorlevel% equ 0 goto :install_success
    )
    echo Installation failed!
    exit /b 1
)

:install_success

echo.
echo ✅ Build complete!
echo You can now run examples with: scripts\run_example.bat examples\hello_world\main.py
