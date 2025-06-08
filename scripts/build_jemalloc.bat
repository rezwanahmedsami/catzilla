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

REM Debug: Check current state
echo 🔍 Checking for existing jemalloc library...
echo    Expected location: %JEMALLOC_LIB_FILE%
if exist "%JEMALLOC_LIB_FILE%" (
    echo ✅ Library file exists
    dir "%JEMALLOC_LIB_FILE%"
) else (
    echo ❌ Library file does not exist
)

REM Force rebuild for debugging - comment out the existing file check
echo 🔧 Force rebuilding jemalloc for debugging...
echo 🧹 Cleaning any existing library files...
if exist "%JEMALLOC_LIB_FILE%" (
    echo Removing existing library: %JEMALLOC_LIB_FILE%
    del /q "%JEMALLOC_LIB_FILE%" 2>nul
)

REM REM Check if jemalloc static library already exists and is valid
REM if exist "%JEMALLOC_LIB_FILE%" (
REM     echo 🔍 Found existing jemalloc library: %JEMALLOC_LIB_FILE%
REM     echo 📊 Library info:
REM     dir "%JEMALLOC_LIB_FILE%"
REM
REM     REM Check if the file is actually a valid library (not empty)
REM     for %%F in ("%JEMALLOC_LIB_FILE%") do set SIZE=%%~zF
REM     if !SIZE! gtr 1000 (
REM         echo ✅ jemalloc static library exists (!SIZE! bytes)
REM         echo 🔍 Verifying CMake can find the library...
REM
REM         REM Test if CMake can find the library by doing a quick existence check
REM         REM Using the same path that CMake will use
REM         set CMAKE_LIB_PATH=%PROJECT_ROOT%\deps\jemalloc\lib\jemalloc.lib
REM         if exist "%CMAKE_LIB_PATH%" (
REM             echo ✅ Library accessible to CMake at: %CMAKE_LIB_PATH%
REM             echo 🚀 Skipping jemalloc build (already built)
REM             exit /b 0
REM         ) else (
REM             echo ❌ Library not accessible to CMake - path mismatch
REM             echo Expected: %CMAKE_LIB_PATH%
REM             echo Actual: %JEMALLOC_LIB_FILE%
REM         )
REM     ) else (
REM         echo ⚠️  Existing library file is too small (!SIZE! bytes) - rebuilding
REM         del /q "%JEMALLOC_LIB_FILE%" 2>nul
REM     )
REM )

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

REM Check for Visual Studio tools (comprehensive check)
echo.
echo 🔍 Environment Info:
echo    Script Dir: %SCRIPT_DIR%
echo    Current Dir: %CD%
echo    Visual Studio:

where msbuild >nul 2>&1
if %errorlevel% equ 0 (
    echo "✅ MSBuild found in PATH"
    msbuild /version 2>nul | findstr /C:"Microsoft" || echo "MSBuild version check failed"
) else (
    echo "❌ MSBuild not found in PATH"

    REM Try to find MSBuild in common Visual Studio locations
    set MSBUILD_FOUND=0

    REM VS 2022 Enterprise
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe" (
        set MSBUILD_PATH=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe
        set MSBUILD_FOUND=1
    )

    REM VS 2022 Professional
    if %MSBUILD_FOUND% equ 0 if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe" (
        set MSBUILD_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe
        set MSBUILD_FOUND=1
    )

    REM VS 2022 Community
    if %MSBUILD_FOUND% equ 0 if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
        set MSBUILD_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe
        set MSBUILD_FOUND=1
    )

    REM VS 2019 Enterprise
    if %MSBUILD_FOUND% equ 0 if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe" (
        set MSBUILD_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe
        set MSBUILD_FOUND=1
    )

    if %MSBUILD_FOUND% equ 1 (
        echo "✅ MSBuild found at: %MSBUILD_PATH%"
        set PATH=%MSBUILD_PATH%;%PATH%
    ) else (
        echo "❌ MSBuild not found in standard locations"
        echo "💡 Tip: Install Visual Studio Build Tools or Visual Studio Community"
        echo "💡 Or run from Visual Studio Developer Command Prompt"
        exit /b 1
    )
)

echo 🔍 jemalloc source directory exists: %JEMALLOC_SOURCE_DIR%

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
