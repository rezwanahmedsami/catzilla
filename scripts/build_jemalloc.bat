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

REM For Windows CI, prefer MSBuild approach to avoid MSYS2 environment conflicts
REM The autotools approach in MSYS2 detects the system as "x86_64-pc-msys" which is unsupported
echo Windows detected - using Visual Studio MSBuild approach for better compatibility

REM Check for Visual Studio tools first
where cl >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Visual Studio compiler
) else (
    echo Setting up Visual Studio environment...
    call :setup_vs_environment
    if !errorlevel! neq 0 exit /b 1
)

REM Go straight to MSBuild approach for Windows
goto :msbuild_approach

:msbuild_approach
echo Using MSBuild approach...
where msbuild >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: MSBuild not found
    exit /b 1
)

set BUILD_SUCCESS=0
if exist "msvc\jemalloc_vc2022.sln" (
    echo Building with VS2022 solution: msvc\jemalloc_vc2022.sln
    echo MSBuild command: msbuild "msvc\jemalloc_vc2022.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
    msbuild "msvc\jemalloc_vc2022.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
    if !errorlevel! equ 0 (
        echo VS2022 build succeeded
        set BUILD_SUCCESS=1
    ) else (
        echo VS2022 build failed with exit code !errorlevel!
    )
)

if !BUILD_SUCCESS! equ 0 (
    if exist "msvc\jemalloc_vc2019.sln" (
        echo Building with VS2019 solution: msvc\jemalloc_vc2019.sln
        echo MSBuild command: msbuild "msvc\jemalloc_vc2019.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
        msbuild "msvc\jemalloc_vc2019.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
        if !errorlevel! equ 0 (
            echo VS2019 build succeeded
            set BUILD_SUCCESS=1
        ) else (
            echo VS2019 build failed with exit code !errorlevel!
        )
    )
)

if !BUILD_SUCCESS! equ 0 (
    if exist "msvc\jemalloc_vc2017.sln" (
        echo Building with VS2017 solution: msvc\jemalloc_vc2017.sln
        echo MSBuild command: msbuild "msvc\jemalloc_vc2017.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
        msbuild "msvc\jemalloc_vc2017.sln" /p:Configuration=Release /p:Platform=x64 /m /verbosity:minimal
        if !errorlevel! equ 0 (
            echo VS2017 build succeeded
            set BUILD_SUCCESS=1
        ) else (
            echo VS2017 build failed with exit code !errorlevel!
        )
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

echo Searching for built jemalloc library...
echo Current directory: %CD%

REM Check make outputs first (though we're not using make on Windows now)
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

REM Check Visual Studio outputs - look in project-specific directories
if !LIBRARY_FOUND! equ 0 (
    REM Check VC2022 output
    if exist "msvc\projects\vc2022\jemalloc\x64\Release\jemalloc.lib" (
        echo Found VS2022 library: msvc\projects\vc2022\jemalloc\x64\Release\jemalloc.lib
        copy "msvc\projects\vc2022\jemalloc\x64\Release\jemalloc.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    )
)

if !LIBRARY_FOUND! equ 0 (
    REM Check VC2019 output
    if exist "msvc\projects\vc2019\jemalloc\x64\Release\jemalloc.lib" (
        echo Found VS2019 library: msvc\projects\vc2019\jemalloc\x64\Release\jemalloc.lib
        copy "msvc\projects\vc2019\jemalloc\x64\Release\jemalloc.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    )
)

if !LIBRARY_FOUND! equ 0 (
    REM Check VC2017 output
    if exist "msvc\projects\vc2017\jemalloc\x64\Release\jemalloc.lib" (
        echo Found VS2017 library: msvc\projects\vc2017\jemalloc\x64\Release\jemalloc.lib
        copy "msvc\projects\vc2017\jemalloc\x64\Release\jemalloc.lib" "lib\jemalloc.lib" >nul 2>&1
        if !errorlevel! equ 0 set LIBRARY_FOUND=1
    )
)

if !LIBRARY_FOUND! equ 0 (
    REM Check alternative output locations
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
    echo Error: Could not find built jemalloc library in any expected location
    echo.
    echo Debugging: Searching all possible output locations...
    echo Make-style outputs:
    if exist "lib\libjemalloc.*" (
        dir "lib\libjemalloc.*"
    ) else (
        echo   No files found in lib\libjemalloc.*
    )
    if exist ".libs\libjemalloc.*" (
        dir ".libs\libjemalloc.*"
    ) else (
        echo   No files found in .libs\libjemalloc.*
    )
    echo.
    echo Visual Studio outputs:
    echo Checking msvc\projects\vc2022\jemalloc\x64\Release\:
    if exist "msvc\projects\vc2022\jemalloc\x64\Release\" (
        dir "msvc\projects\vc2022\jemalloc\x64\Release\*.*"
    ) else (
        echo   Directory does not exist
    )
    echo Checking msvc\projects\vc2019\jemalloc\x64\Release\:
    if exist "msvc\projects\vc2019\jemalloc\x64\Release\" (
        dir "msvc\projects\vc2019\jemalloc\x64\Release\*.*"
    ) else (
        echo   Directory does not exist
    )
    echo Checking msvc\x64\Release\:
    if exist "msvc\x64\Release\" (
        dir "msvc\x64\Release\*.*"
    ) else (
        echo   Directory does not exist
    )
    echo.
    echo Available msvc directory structure:
    if exist "msvc\" (
        dir "msvc\" /s
    ) else (
        echo   msvc directory does not exist
    )
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
