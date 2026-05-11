@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "JEMALLOC_SOURCE_DIR=%PROJECT_ROOT%\deps\jemalloc"
set "DID_PUSHD="

echo Building jemalloc for Windows...

REM Allow invocation from the repo root or the jemalloc source directory.
if not exist "Makefile.in" (
    if exist "%JEMALLOC_SOURCE_DIR%\Makefile.in" (
        echo Switching to jemalloc source directory: %JEMALLOC_SOURCE_DIR%
        pushd "%JEMALLOC_SOURCE_DIR%"
        set "DID_PUSHD=1"
    ) else (
        echo Error: jemalloc source directory not found
        echo Expected to find Makefile.in in the current directory or at %JEMALLOC_SOURCE_DIR%
        exit /b 1
    )
)

set "JEMALLOC_SOURCE_DIR=%CD%"
set "STAGE_ROOT=%PROJECT_ROOT%\.catzilla-cache\jemalloc-windows"
set "STAGED_LIB_DIR=%STAGE_ROOT%\lib"
set "STAGED_LIB_FILE=%STAGED_LIB_DIR%\jemalloc.lib"
set "STAGED_INCLUDE_DIR=%STAGE_ROOT%\include\jemalloc"
set "VCPKG_TRIPLET=x64-windows-static-md"
set "OVERLAY_TRIPLETS=%PROJECT_ROOT%\cmake\vcpkg-triplets"
set "CATZILLA_VCPKG_ROOT=%VCPKG_ROOT%"
if not defined CATZILLA_VCPKG_ROOT set "CATZILLA_VCPKG_ROOT=%PROJECT_ROOT%\.catzilla-cache\tools\vcpkg"
set "VCPKG_INSTALL_ROOT=%CATZILLA_VCPKG_ROOT%\installed\%VCPKG_TRIPLET%"

echo Current directory: %CD%
echo Repo root: %PROJECT_ROOT%

echo.
echo Cleaning previous staged artifacts...
if exist "%STAGE_ROOT%" rmdir /s /q "%STAGE_ROOT%"
if not exist "%STAGED_LIB_DIR%" mkdir "%STAGED_LIB_DIR%"
if not exist "%STAGED_INCLUDE_DIR%" mkdir "%STAGED_INCLUDE_DIR%"

echo.
echo Step 1: Trying the INSTALL.md vcpkg flow for Windows...
if not exist "%OVERLAY_TRIPLETS%\%VCPKG_TRIPLET%.cmake" (
    echo Error: Missing vcpkg triplet file: %OVERLAY_TRIPLETS%\%VCPKG_TRIPLET%.cmake
    exit /b 1
)

if not exist "%CATZILLA_VCPKG_ROOT%\vcpkg.exe" (
    where git >nul 2>&1
    if errorlevel 1 (
        echo Error: git is not available, cannot bootstrap vcpkg automatically
        exit /b 1
    )

    for %%I in ("%CATZILLA_VCPKG_ROOT%\..") do set "VCPKG_PARENT=%%~fI"
    if not exist "!VCPKG_PARENT!" mkdir "!VCPKG_PARENT!"

    if not exist "%CATZILLA_VCPKG_ROOT%\.git" (
        echo Cloning vcpkg into %CATZILLA_VCPKG_ROOT%...
        git clone --depth 1 https://github.com/microsoft/vcpkg.git "%CATZILLA_VCPKG_ROOT%"
        if errorlevel 1 (
            echo Error: Failed to clone vcpkg
            exit /b 1
        )
    )

    echo Bootstrapping vcpkg...
    call "%CATZILLA_VCPKG_ROOT%\bootstrap-vcpkg.bat" -disableMetrics
    if errorlevel 1 (
        echo Error: Failed to bootstrap vcpkg
        exit /b 1
    )
)

echo Installing jemalloc via vcpkg triplet %VCPKG_TRIPLET%...
"%CATZILLA_VCPKG_ROOT%\vcpkg.exe" install jemalloc --triplet "%VCPKG_TRIPLET%" --overlay-triplets "%OVERLAY_TRIPLETS%"
if errorlevel 1 (
    echo Error: vcpkg install jemalloc failed
    exit /b 1
)

set "VCPKG_LIB_CANDIDATE="
if exist "%VCPKG_INSTALL_ROOT%\lib\jemalloc.lib" set "VCPKG_LIB_CANDIDATE=%VCPKG_INSTALL_ROOT%\lib\jemalloc.lib"
if not defined VCPKG_LIB_CANDIDATE if exist "%VCPKG_INSTALL_ROOT%\lib\jemalloc_s.lib" set "VCPKG_LIB_CANDIDATE=%VCPKG_INSTALL_ROOT%\lib\jemalloc_s.lib"

if not defined VCPKG_LIB_CANDIDATE (
    echo Error: vcpkg completed but no static jemalloc library was found in %VCPKG_INSTALL_ROOT%\lib
    exit /b 1
)

if not exist "%VCPKG_INSTALL_ROOT%\include\jemalloc\jemalloc.h" (
    echo Error: vcpkg completed but jemalloc headers were not found in %VCPKG_INSTALL_ROOT%\include
    exit /b 1
)

echo Staging vcpkg jemalloc artifacts into .catzilla-cache\jemalloc-windows...
copy /y "%VCPKG_LIB_CANDIDATE%" "%STAGED_LIB_FILE%" >nul
if errorlevel 1 (
    echo Error: Failed to stage jemalloc.lib from vcpkg
    exit /b 1
)

PowerShell -NoLogo -NoProfile -Command "Copy-Item -Path '%VCPKG_INSTALL_ROOT%\include\jemalloc\*' -Destination '%STAGED_INCLUDE_DIR%' -Recurse -Force"
if errorlevel 1 (
    echo Error: Failed to stage jemalloc headers from vcpkg
    exit /b 1
)

if not exist "%STAGED_INCLUDE_DIR%\jemalloc.h" (
    echo Error: Staged jemalloc headers are incomplete: jemalloc.h is missing
    exit /b 1
)

echo.
echo jemalloc Windows build completed successfully via vcpkg
echo Library created: .catzilla-cache\jemalloc-windows\lib\jemalloc.lib
echo Headers staged under: .catzilla-cache\jemalloc-windows\include\jemalloc
if defined DID_PUSHD popd
exit /b 0
