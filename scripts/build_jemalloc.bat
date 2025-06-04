@echo off
REM Windows batch script for building jemalloc static library
setlocal enabledelayedexpansion

REM Colors for output
set GREEN=[32m
set YELLOW=[33m
set RED=[31m
set BLUE=[34m
set NC=[0m

echo %BLUE%🧠 jemalloc Build Script%NC%
echo %BLUE%========================%NC%

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set JEMALLOC_SOURCE_DIR=%PROJECT_ROOT%\deps\jemalloc
set JEMALLOC_LIB_FILE=%JEMALLOC_SOURCE_DIR%\lib\jemalloc.lib

REM Check if jemalloc source directory exists
if not exist "%JEMALLOC_SOURCE_DIR%" (
    echo %RED%❌ Error: jemalloc source directory not found: %JEMALLOC_SOURCE_DIR%%NC%
    echo %YELLOW%💡 Tip: Initialize git submodules: git submodule update --init --recursive%NC%
    exit /b 1
)

REM Check if jemalloc static library already exists
if exist "%JEMALLOC_LIB_FILE%" (
    echo %GREEN%✅ jemalloc static library already exists: %JEMALLOC_LIB_FILE%%NC%
    echo %YELLOW%📊 Library info:%NC%
    dir "%JEMALLOC_LIB_FILE%"
    echo %GREEN%🚀 Skipping jemalloc build (already built)%NC%
    exit /b 0
)

echo %YELLOW%🔨 Building jemalloc static library...%NC%
echo %BLUE%Source: %JEMALLOC_SOURCE_DIR%%NC%
echo %BLUE%Target: %JEMALLOC_LIB_FILE%%NC%

REM Navigate to jemalloc source directory
cd /d "%JEMALLOC_SOURCE_DIR%"

REM Check for Visual Studio tools
call "%~dp0jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo %RED%❌ Error: Visual Studio tools not found%NC%
    echo %YELLOW%💡 Tip: Install Visual Studio Build Tools or Visual Studio Community%NC%
    exit /b 1
)

REM Use Visual Studio project files for Windows build
echo.
echo %GREEN%🔨 Building jemalloc with Visual Studio...%NC%

REM Try building with MSBuild
if exist "msvc\jemalloc_vc2017.sln" (
    echo Building with Visual Studio 2017+ solution...
    msbuild "msvc\jemalloc_vc2017.sln" /p:Configuration=Release /p:Platform=x64 /m
    if %errorlevel% equ 0 (
        REM Copy the built library to expected location
        if not exist "lib" mkdir lib
        copy "msvc\x64\Release\jemalloc-vc141-Release.lib" "lib\jemalloc.lib" >nul 2>&1
        if exist "lib\jemalloc.lib" (
            echo %GREEN%✅ jemalloc build complete!%NC%
            echo %YELLOW%📊 Library info:%NC%
            dir "lib\jemalloc.lib"
            echo %GREEN%🚀 Ready for Catzilla build!%NC%
            exit /b 0
        )
    )
)

REM Fallback: Try using vcpkg approach
echo %YELLOW%Trying vcpkg-based build...%NC%
REM Note: This would require vcpkg to be installed and configured
echo %RED%❌ Error: jemalloc Windows build failed%NC%
echo %YELLOW%💡 Tip: Consider using vcpkg to install jemalloc:%NC%
echo %YELLOW%   vcpkg install jemalloc:x64-windows-static%NC%
exit /b 1
