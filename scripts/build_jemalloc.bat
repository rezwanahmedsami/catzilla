@echo off
setlocal enabledelayedexpansion

echo Building jemalloc for Windows...

REM Check if we're in the correct directory
if not exist "Makefile.in" (
    echo Error: This script must be run from the jemalloc source directory
    echo Expected to find Makefile.in in the current directory
    exit /b 1
)

echo Current directory: %CD%

echo.
echo Cleaning previous build artifacts...
if exist "msvc\x64\Release" rmdir /s /q "msvc\x64\Release"
if exist "msvc\x64\Debug" rmdir /s /q "msvc\x64\Debug"
if exist "lib\jemalloc.lib" del /q "lib\jemalloc.lib"

echo.
echo Checking build environment...

REM Check for Visual Studio solution files (native Windows build)
if not exist "msvc\jemalloc_vc2022.sln" (
    if not exist "msvc\jemalloc_vc2019.sln" (
        echo Error: No Visual Studio solution files found in msvc directory
        echo Expected jemalloc_vc2022.sln or jemalloc_vc2019.sln
        exit /b 1
    )
)
echo Found Visual Studio solution files

echo Setting up Visual Studio environment...
set "VCVARSALL_FOUND="
if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARSALL_FOUND=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARSALL_FOUND=C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARSALL_FOUND=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
)

if defined VCVARSALL_FOUND (
    echo Found Visual Studio at: !VCVARSALL_FOUND!
    call "!VCVARSALL_FOUND!" x64
    if !errorlevel! neq 0 (
        echo Error: Failed to setup Visual Studio environment
        exit /b 1
    )
    echo Visual Studio environment setup successful
) else (
    echo Error: Visual Studio not found
    exit /b 1
)

echo.
echo Step 1: Using native Windows MSVC build (skipping autotools)...
REM Skip problematic autogen.sh/configure - use native MSVC solution files directly
echo Jemalloc for Windows uses native MSVC project files - no autotools needed
echo This avoids pthread.h and MSYS environment detection issues

echo Step 2: Building with MSBuild...
set LIBRARY_FOUND=0

REM Try VS2022 first
if exist "msvc\jemalloc_vc2022.sln" (
    echo Building with VS2022 solution: msvc\jemalloc_vc2022.sln
    msbuild "msvc\jemalloc_vc2022.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
    if !errorlevel! equ 0 (
        echo VS2022 build successful
        goto :check_library
    ) else (
        echo VS2022 build failed with exit code !errorlevel!
    )
)

REM Try VS2019 as fallback
if exist "msvc\jemalloc_vc2019.sln" (
    echo Building with VS2019 solution: msvc\jemalloc_vc2019.sln
    msbuild "msvc\jemalloc_vc2019.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
    if !errorlevel! equ 0 (
        echo VS2019 build successful
        goto :check_library
    ) else (
        echo VS2019 build failed with exit code !errorlevel!
    )
)

echo Error: All MSBuild attempts failed
exit /b 1

:check_library
echo.
echo Step 3: Checking for output libraries...

REM Create lib directory if it doesn't exist
if not exist "lib" mkdir lib

REM Check VS2022 output first
if exist "msvc\projects\vc2022\jemalloc\x64\Release\jemalloc.lib" (
    echo Found VS2022 library: msvc\projects\vc2022\jemalloc\x64\Release\jemalloc.lib
    copy "msvc\projects\vc2022\jemalloc\x64\Release\jemalloc.lib" "lib\jemalloc.lib" >nul 2>&1
    if !errorlevel! equ 0 set LIBRARY_FOUND=1
)

if !LIBRARY_FOUND! equ 0 (
    if exist "msvc\projects\vc2019\jemalloc\x64\Release\jemalloc.lib" (
        echo Found VS2019 library: msvc\projects\vc2019\jemalloc\x64\Release\jemalloc.lib
        copy "msvc\projects\vc2019\jemalloc\x64\Release\jemalloc.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    )
)

if !LIBRARY_FOUND! equ 0 (
    echo Error: No jemalloc library found after build
    echo.
    echo Debugging: Searching for library files...
    if exist "msvc\projects\" (
        echo Available project directories:
        dir "msvc\projects\" /s /b | findstr /i "jemalloc.lib"
    )
    exit /b 1
)

echo.
echo ✅ jemalloc Windows build completed successfully
echo Library created: lib\jemalloc.lib
exit /b 0
