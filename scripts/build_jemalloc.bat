@echo off
REM Windows batch script for building jemalloc static library
setlocal enabledelayedexpansion

echo 🧠 jemalloc Build Script
echo ========================

REM Debug: Show environment info
echo 🔍 Environment Info:
echo    Script Dir: %~dp0
echo    Current Dir: %CD%
echo    Visual Studio:
where msbuild 2>nul || echo "MSBuild not found"
msbuild /version 2>nul || echo "MSBuild version check failed"

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set JEMALLOC_SOURCE_DIR=%PROJECT_ROOT%\deps\jemalloc
set JEMALLOC_LIB_FILE=%JEMALLOC_SOURCE_DIR%\lib\jemalloc.lib

REM Check if jemalloc source directory exists
if not exist "%JEMALLOC_SOURCE_DIR%" (
    echo ❌ Error: jemalloc source directory not found: %JEMALLOC_SOURCE_DIR%
    echo 💡 Tip: Initialize git submodules: git submodule update --init --recursive
    exit /b 1
)

echo 🔍 jemalloc source directory exists: %JEMALLOC_SOURCE_DIR%

REM Check if jemalloc static library already exists
if exist "%JEMALLOC_LIB_FILE%" (
    echo ✅ jemalloc static library already exists: %JEMALLOC_LIB_FILE%
    echo 📊 Library info:
    dir "%JEMALLOC_LIB_FILE%"
    echo 🚀 Skipping jemalloc build (already built)
    exit /b 0
)

echo 🔨 Building jemalloc static library...
echo Source: %JEMALLOC_SOURCE_DIR%
echo Target: %JEMALLOC_LIB_FILE%

REM Navigate to jemalloc source directory
cd /d "%JEMALLOC_SOURCE_DIR%"

REM Clean any previous build artifacts
echo.
echo 🧹 Cleaning previous build artifacts...
if exist "msvc\x64\Release" rmdir /s /q "msvc\x64\Release"
if exist "msvc\x64\Debug" rmdir /s /q "msvc\x64\Debug"
if exist "lib\jemalloc.lib" del /q "lib\jemalloc.lib"

REM Check for Visual Studio tools (simplified check)
where msbuild >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: MSBuild not found - Visual Studio tools required
    echo 💡 Tip: Install Visual Studio Build Tools or Visual Studio Community
    echo 💡 Or run from Visual Studio Developer Command Prompt
    exit /b 1
)

REM Use Visual Studio project files for Windows build
echo.
echo 🔨 Building jemalloc with Visual Studio...

REM Try building with MSBuild - prefer newer versions first
set BUILD_SUCCESS=0

REM Try VS 2022 first
if exist "msvc\jemalloc_vc2022.sln" (
    echo Building with Visual Studio 2022 solution...
    msbuild "msvc\jemalloc_vc2022.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal /nologo
    if %errorlevel% equ 0 set BUILD_SUCCESS=1
)

REM Try VS 2019 if 2022 failed
if %BUILD_SUCCESS% equ 0 if exist "msvc\jemalloc_vc2019.sln" (
    echo Building with Visual Studio 2019 solution...
    msbuild "msvc\jemalloc_vc2019.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal /nologo
    if %errorlevel% equ 0 set BUILD_SUCCESS=1
)

REM Try VS 2017 if others failed
if %BUILD_SUCCESS% equ 0 if exist "msvc\jemalloc_vc2017.sln" (
    echo Building with Visual Studio 2017 solution...
    msbuild "msvc\jemalloc_vc2017.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal /nologo
    if %errorlevel% equ 0 set BUILD_SUCCESS=1
)

if %BUILD_SUCCESS% equ 1 (
        REM Copy the built library to expected location
        if not exist "lib" mkdir lib

        REM Look for various possible output names (VS 2017-2022 variations)
        if exist "msvc\x64\Release\jemalloc-vc143-Release.lib" (
            copy "msvc\x64\Release\jemalloc-vc143-Release.lib" "lib\jemalloc.lib" >nul 2>&1
        ) else if exist "msvc\x64\Release\jemalloc-vc142-Release.lib" (
            copy "msvc\x64\Release\jemalloc-vc142-Release.lib" "lib\jemalloc.lib" >nul 2>&1
        ) else if exist "msvc\x64\Release\jemalloc-vc141-Release.lib" (
            copy "msvc\x64\Release\jemalloc-vc141-Release.lib" "lib\jemalloc.lib" >nul 2>&1
        ) else if exist "msvc\x64\Release\jemalloc.lib" (
            copy "msvc\x64\Release\jemalloc.lib" "lib\jemalloc.lib" >nul 2>&1
        )

        if exist "lib\jemalloc.lib" (
            echo.
            echo ✅ jemalloc build complete!
            echo 📊 Library info:
            dir "lib\jemalloc.lib"
            echo 🚀 Ready for Catzilla build!
            exit /b 0
        ) else (
            echo ❌ Error: Could not find built jemalloc library
            echo 🔍 Available files in msvc\x64\Release:
            dir "msvc\x64\Release" 2>nul
            exit /b 1
        )
    ) else (
        echo ❌ Error: MSBuild failed for all Visual Studio versions
        echo 🔍 Available solution files:
        dir "msvc\*.sln" 2>nul
        echo 🔍 MSBuild version:
        msbuild /version 2>nul || echo "MSBuild version detection failed"
        exit /b 1
    )
) else (
    echo ❌ Error: No Visual Studio solution files found
    echo 🔍 Available files in msvc directory:
    dir "msvc" 2>nul
    exit /b 1
)

REM This point should not be reached
echo ❌ Error: Unexpected end of script
exit /b 1
