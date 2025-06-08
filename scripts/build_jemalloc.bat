@echo off
REM Windows batch script for building jemalloc static library
setlocal enabledelayedexpansion

echo Building jemalloc static library
echo =================================

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set JEMALLOC_SOURCE_DIR=%PROJECT_ROOT%\deps\jemalloc
set JEMALLOC_LIB_FILE=%JEMALLOC_SOURCE_DIR%\lib\jemalloc.lib

REM Check if jemalloc source directory exists
if not exist "%JEMALLOC_SOURCE_DIR%" (
    echo Error: jemalloc source directory not found: %JEMALLOC_SOURCE_DIR%
    echo Tip: Initialize git submodules: git submodule update --init --recursive
    exit /b 1
)

echo jemalloc source directory exists: %JEMALLOC_SOURCE_DIR%

REM Check if jemalloc static library already exists and is valid
if exist "%JEMALLOC_LIB_FILE%" (
    echo Found existing jemalloc library: %JEMALLOC_LIB_FILE%
    echo Library info:
    dir "%JEMALLOC_LIB_FILE%"

    REM Check if the file is actually a valid library (not empty)
    for %%F in ("%JEMALLOC_LIB_FILE%") do set SIZE=%%~zF
    if !SIZE! gtr 1000 (
        echo jemalloc static library exists (!SIZE! bytes)
        echo Verifying CMake can find the library...

        REM Test if CMake can find the library by doing a quick existence check
        REM Using the same path that CMake will use
        set CMAKE_LIB_PATH=%PROJECT_ROOT%\deps\jemalloc\lib\jemalloc.lib
        if exist "%CMAKE_LIB_PATH%" (
            echo Library accessible to CMake at: %CMAKE_LIB_PATH%
            echo Skipping jemalloc build (already built)
            exit /b 0
        ) else (
            echo Library not accessible to CMake - path mismatch
            echo Expected: %CMAKE_LIB_PATH%
            echo Actual: %JEMALLOC_LIB_FILE%
        )
    ) else (
        echo Existing library file is too small (!SIZE! bytes) - rebuilding
        del /q "%JEMALLOC_LIB_FILE%" 2>nul
    )
)

echo Building jemalloc static library...
echo Source: %JEMALLOC_SOURCE_DIR%
echo Target: %JEMALLOC_LIB_FILE%

REM Navigate to jemalloc source directory
cd /d "%JEMALLOC_SOURCE_DIR%"

REM Clean any previous build artifacts
echo.
echo Cleaning previous build artifacts...
if exist "msvc\x64\Release" rmdir /s /q "msvc\x64\Release"
if exist "msvc\x64\Debug" rmdir /s /q "msvc\x64\Debug"
if exist "lib\jemalloc.lib" del /q "lib\jemalloc.lib"
if exist "configure" del /q "configure"
if exist "include\jemalloc\jemalloc.h" del /q "include\jemalloc\jemalloc.h"

REM Check for required build tools
echo.
echo Checking build environment...

REM Check for bash (required for autogen.sh)
where bash >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: bash not found. jemalloc Windows build requires bash.
    echo Please install Git for Windows or MSYS2 to get bash.
    echo Make sure bash is in your PATH.
    exit /b 1
)
echo Found bash:
bash --version | head -1

REM Check for autoconf (required for configuration)
bash -c "which autoconf" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: autoconf not found. jemalloc Windows build requires autoconf.
    echo Please install MSYS2 and run: pacman -S autoconf autogen
    echo Or use Git for Windows with autoconf installed.
    exit /b 1
)
echo Found autoconf:
bash -c "autoconf --version" | head -1

REM Check for make (required for building)
bash -c "which make" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: make not found. jemalloc Windows build requires make.
    echo Please install MSYS2 and run: pacman -S make
    echo Or use Git for Windows with make installed.
    exit /b 1
)
echo Found make:
bash -c "make --version" | head -1

REM Check for Visual Studio tools
where cl >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Visual Studio compiler (cl.exe):
    cl 2>&1 | head -1
    set CC=cl
) else (
    echo Warning: Visual Studio compiler (cl.exe) not found in PATH
    echo Trying to find and setup Visual Studio environment...

    REM Try to find Visual Studio
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (
        call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
    ) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" (
        call "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" x64
    ) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" (
        call "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" x64
    ) else if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat" (
        call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
    ) else (
        echo Error: Visual Studio not found. Please install Visual Studio Build Tools.
        exit /b 1
    )

    where cl >nul 2>&1
    if %errorlevel% equ 0 (
        echo Visual Studio environment setup successful
        set CC=cl
    ) else (
        echo Error: Could not setup Visual Studio environment
        exit /b 1
    )
)

echo.
echo Step 1: Generating configuration files...
REM Use bash to run autogen.sh which generates the configure script and header files
bash -c "CC=%CC% ./autogen.sh"
if %errorlevel% neq 0 (
    echo Error: autogen.sh failed
    echo This step generates configure script and header files required for Windows build
    exit /b 1
)

echo Step 2: Running configure script...
REM Configure jemalloc for Windows static library build
bash -c "CC=%CC% ./configure --enable-static --disable-shared --with-malloc-conf=background_thread:true"
if %errorlevel% neq 0 (
    echo Error: configure failed
    echo This step configures jemalloc build settings
    exit /b 1
)

echo Step 3: Building jemalloc with make...
REM Build jemalloc using make (works better than MSBuild for cross-platform)
bash -c "make clean && make -j%NUMBER_OF_PROCESSORS%"
if %errorlevel% neq 0 (
    echo Error: make build failed
    echo Trying alternative build approach...

    REM Fallback: try Visual Studio solution if make fails
    echo Step 3b: Falling back to Visual Studio build...

    REM Check if Visual Studio solution files exist
    if exist "msvc\jemalloc_vc2022.sln" (
        echo Building with Visual Studio 2022 solution...
        msbuild "msvc\jemalloc_vc2022.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal /nologo
        if !errorlevel! equ 0 (
            goto :vs_build_success
        )
    )
    if exist "msvc\jemalloc_vc2019.sln" (
        echo Building with Visual Studio 2019 solution...
        msbuild "msvc\jemalloc_vc2019.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal /nologo
        if !errorlevel! equ 0 (
            goto :vs_build_success
        )
    )
    if exist "msvc\jemalloc_vc2017.sln" (
        echo Building with Visual Studio 2017 solution...
        msbuild "msvc\jemalloc_vc2017.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal /nologo
        if !errorlevel! equ 0 (
            goto :vs_build_success
        )
    )

    echo Error: All build methods failed
    exit /b 1

    :vs_build_success
    echo Visual Studio build completed successfully
)

echo Step 4: Installing library to expected location...

REM Create lib directory if it doesn't exist
if not exist "lib" mkdir lib

REM Look for the built library in various possible locations
set LIBRARY_FOUND=0

REM First check make build output
if exist "lib\libjemalloc.a" (
    echo Found make-built library: lib\libjemalloc.a
    copy "lib\libjemalloc.a" "lib\jemalloc.lib" >nul 2>&1
    if !errorlevel! equ 0 set LIBRARY_FOUND=1
)

REM Check Unix-style output locations
if !LIBRARY_FOUND! equ 0 (
    if exist ".libs\libjemalloc.a" (
        echo Found make-built library: .libs\libjemalloc.a
        copy ".libs\libjemalloc.a" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    )
)

REM Check Visual Studio build outputs
if !LIBRARY_FOUND! equ 0 (
    if exist "msvc\x64\Release\jemalloc-vc143-Release.lib" (
        echo Found VS2022-built library: msvc\x64\Release\jemalloc-vc143-Release.lib
        copy "msvc\x64\Release\jemalloc-vc143-Release.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    ) else if exist "msvc\x64\Release\jemalloc-vc142-Release.lib" (
        echo Found VS2019-built library: msvc\x64\Release\jemalloc-vc142-Release.lib
        copy "msvc\x64\Release\jemalloc-vc142-Release.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    ) else if exist "msvc\x64\Release\jemalloc-vc141-Release.lib" (
        echo Found VS2017-built library: msvc\x64\Release\jemalloc-vc141-Release.lib
        copy "msvc\x64\Release\jemalloc-vc141-Release.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    ) else if exist "msvc\x64\Release\jemalloc.lib" (
        echo Found VS-built library: msvc\x64\Release\jemalloc.lib
        copy "msvc\x64\Release\jemalloc.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    )
)

if !LIBRARY_FOUND! equ 1 (
    if exist "lib\jemalloc.lib" (
        echo.
        echo jemalloc build complete!
        echo Library info:
        dir "lib\jemalloc.lib"
        echo.
        echo Verifying library file...
        for %%F in ("lib\jemalloc.lib") do set FINAL_SIZE=%%~zF
        if !FINAL_SIZE! gtr 1000 (
            echo Library size: !FINAL_SIZE! bytes - looks valid
            echo Ready for Catzilla build!
            exit /b 0
        ) else (
            echo Error: Library file is too small (!FINAL_SIZE! bytes)
            exit /b 1
        )
    ) else (
        echo Error: Failed to copy library to expected location
        exit /b 1
    )
) else (
    echo Error: Could not find built jemalloc library in any expected location
    echo.
    echo Available files:
    echo make outputs:
    dir "lib\libjemalloc.*" 2>nul
    dir ".libs\libjemalloc.*" 2>nul
    echo Visual Studio outputs:
    dir "msvc\x64\Release\jemalloc*.lib" 2>nul
    exit /b 1
)
