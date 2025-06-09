@echo off
setlocal enabledelayedexpansion

REM Windows jemalloc build script
REM This script builds jemalloc as a static library for Windows using autotools + make or Visual Studio

echo Building jemalloc for Windows...

REM Check if we're in the correct directory
if not exist "Makefile.in" (
    echo Error: This script must be run from the jemalloc source directory
    echo Expected to find Makefile.in in the current directory
    exit /b 1
)

set "CURRENT_DIR=%CD%"
echo Current directory: %CURRENT_DIR%

echo.
echo Cleaning previous build artifacts...
if exist "msvc\x64\Release" rmdir /s /q "msvc\x64\Release"
if exist "msvc\x64\Debug" rmdir /s /q "msvc\x64\Debug"
if exist "lib\jemalloc.lib" del /q "lib\jemalloc.lib"
if exist "configure" del /q "configure"
if exist "include\jemalloc\jemalloc.h" del /q "include\jemalloc\jemalloc.h"

echo.
echo Checking build environment...

REM Check for bash
where bash >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: bash not found. Trying MSBuild approach instead.
    goto :msbuild_approach
)
echo Found bash

REM Check for autoconf
bash -c "which autoconf" >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: autoconf not found. Trying MSBuild approach instead.
    goto :msbuild_approach
)
echo Found autoconf

REM Check for make
bash -c "which make" >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: make not found. Trying MSBuild approach instead.
    goto :msbuild_approach
)
echo Found make

REM Check for Visual Studio tools
where cl >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Visual Studio compiler
) else (
    echo Setting up Visual Studio environment...
    call :setup_vs_environment
    if !errorlevel! neq 0 exit /b 1
)

echo.
echo Step 1: Generating configuration files...
bash -c "export CC=cl && ./autogen.sh"
if %errorlevel% neq 0 (
    echo Error: autogen.sh failed
    exit /b 1
)

echo Step 2: Running configure script...
bash -c "export CC=cl && ./configure --enable-static --disable-shared --with-malloc-conf=background_thread:true"
if %errorlevel% neq 0 (
    echo Error: configure failed
    exit /b 1
)

echo Step 3: Building jemalloc with make...
bash -c "make clean && make -j%NUMBER_OF_PROCESSORS%"
if %errorlevel% neq 0 (
    echo Error: make build failed, trying Visual Studio...
    goto :try_vs_build
)

goto :install_library

:try_vs_build
echo Trying Visual Studio build...
if exist "msvc\jemalloc_vc2022.sln" (
    msbuild "msvc\jemalloc_vc2022.sln" /p:Configuration=Release /p:Platform=x64 /m /nologo
    if !errorlevel! equ 0 goto :install_library
)
if exist "msvc\jemalloc_vc2019.sln" (
    msbuild "msvc\jemalloc_vc2019.sln" /p:Configuration=Release /p:Platform=x64 /m /nologo
    if !errorlevel! equ 0 goto :install_library
)
echo Error: All build methods failed
exit /b 1

:msbuild_approach
echo Using MSBuild approach...
where msbuild >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: MSBuild not found
    exit /b 1
)

set BUILD_SUCCESS=0
if exist "msvc\jemalloc_vc2022.sln" (
    echo Building with VS2022...
    msbuild "msvc\jemalloc_vc2022.sln" /p:Configuration=Release /p:Platform=x64 /m /nologo
    if !errorlevel! equ 0 set BUILD_SUCCESS=1
)
if !BUILD_SUCCESS! equ 0 (
    if exist "msvc\jemalloc_vc2019.sln" (
        echo Building with VS2019...
        msbuild "msvc\jemalloc_vc2019.sln" /p:Configuration=Release /p:Platform=x64 /m /nologo
        if !errorlevel! equ 0 set BUILD_SUCCESS=1
    )
)
if !BUILD_SUCCESS! equ 0 (
    echo Error: MSBuild failed
    exit /b 1
)

:install_library
echo Step 4: Installing library...

if not exist "lib" mkdir lib

set LIBRARY_FOUND=0

REM Check make outputs
if exist "lib\libjemalloc.a" (
    echo Found make library: lib\libjemalloc.a
    copy "lib\libjemalloc.a" "lib\jemalloc.lib" >nul 2>&1
    if !errorlevel! equ 0 set LIBRARY_FOUND=1
)

if !LIBRARY_FOUND! equ 0 (
    if exist ".libs\libjemalloc.a" (
        echo Found make library: .libs\libjemalloc.a
        copy ".libs\libjemalloc.a" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    )
)

REM Check Visual Studio outputs
if !LIBRARY_FOUND! equ 0 (
    for %%f in ("msvc\x64\Release\jemalloc*.lib") do (
        if exist "%%f" (
            echo Found VS library: %%f
            copy "%%f" "lib\jemalloc.lib" >nul 2>&1
            if !errorlevel! equ 0 set LIBRARY_FOUND=1
            goto :check_final
        )
    )
)

:check_final
if !LIBRARY_FOUND! equ 1 (
    if exist "lib\jemalloc.lib" (
        echo.
        echo jemalloc build complete!
        dir "lib\jemalloc.lib"
        for %%F in ("lib\jemalloc.lib") do set FINAL_SIZE=%%~zF
        if !FINAL_SIZE! gtr 1000 (
            echo Library size: !FINAL_SIZE! bytes - looks valid
            echo Ready for Catzilla build!
            exit /b 0
        ) else (
            echo Error: Library file too small
            exit /b 1
        )
    ) else (
        echo Error: Failed to copy library
        exit /b 1
    )
) else (
    echo Error: Could not find built library
    exit /b 1
)

:setup_vs_environment
set "VCVARSALL_FOUND="
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARSALL_FOUND=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARSALL_FOUND=C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARSALL_FOUND=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARSALL_FOUND=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat"

if defined VCVARSALL_FOUND (
    echo Found Visual Studio at: !VCVARSALL_FOUND!
    call "!VCVARSALL_FOUND!" x64
    where cl >nul 2>&1
    if !errorlevel! equ 0 (
        echo Visual Studio environment setup successful
        exit /b 0
    ) else (
        echo Error: Could not setup Visual Studio environment
        exit /b 1
    )
) else (
    echo Error: Visual Studio not found
    exit /b 1
)
