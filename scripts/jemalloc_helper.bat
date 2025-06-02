@echo off
REM Catzilla Jemalloc Helper Script for Windows
REM This script helps detect and configure jemalloc for Windows environments

setlocal enabledelayedexpansion

echo [36mCatzilla Jemalloc Helper for Windows[0m
echo [36m===================================[0m

REM Check if jemalloc is available via vcpkg
if exist "C:\vcpkg\installed\x64-windows\bin\jemalloc.dll" (
    echo [32mFound jemalloc via vcpkg[0m
    set "JEMALLOC_PATH=C:\vcpkg\installed\x64-windows\bin\jemalloc.dll"
    goto :configure
)

REM Check local vcpkg installation
if exist "%USERPROFILE%\vcpkg\installed\x64-windows\bin\jemalloc.dll" (
    echo [32mFound jemalloc in user vcpkg installation[0m
    set "JEMALLOC_PATH=%USERPROFILE%\vcpkg\installed\x64-windows\bin\jemalloc.dll"
    goto :configure
)

REM Check if jemalloc is in system PATH
where jemalloc.dll >nul 2>&1
if %errorlevel% == 0 (
    echo [32mFound jemalloc in system PATH[0m
    for /f "tokens=*" %%i in ('where jemalloc.dll') do set "JEMALLOC_PATH=%%i"
    goto :configure
)

echo [33mjemalloc not found. Attempting automatic installation...[0m
goto :install

:install
REM Install jemalloc via vcpkg if available
if exist "C:\vcpkg\vcpkg.exe" (
    echo [33mInstalling jemalloc via vcpkg...[0m
    C:\vcpkg\vcpkg.exe install jemalloc:x64-windows
    if %errorlevel% == 0 (
        set "JEMALLOC_PATH=C:\vcpkg\installed\x64-windows\bin\jemalloc.dll"
        echo [32mSuccessfully installed jemalloc[0m
        goto :configure
    )
)

echo [31mFailed to install jemalloc automatically.[0m
echo [33mPlease install manually using one of these methods:[0m
echo [33m  1. Install vcpkg and run: vcpkg install jemalloc:x64-windows[0m
echo [33m  2. Download from: https://github.com/jemalloc/jemalloc/releases[0m
goto :end

:configure
echo [32mConfiguring jemalloc for Catzilla...[0m
echo [33mJemalloc path: %JEMALLOC_PATH%[0m

REM Get directory containing jemalloc.dll
for %%i in ("%JEMALLOC_PATH%") do set "JEMALLOC_DIR=%%~dpi"

REM Add to PATH if not already there
echo %PATH% | findstr /C:"%JEMALLOC_DIR%" >nul
if %errorlevel% neq 0 (
    set "PATH=%JEMALLOC_DIR%;%PATH%"
    echo [32mAdded jemalloc directory to PATH[0m
) else (
    echo [32mjemalloc directory already in PATH[0m
)

REM Set environment variables for CMake to find jemalloc
set "CATZILLA_JEMALLOC_PATH=%JEMALLOC_PATH%"
set "JEMALLOC_INCLUDE_DIR=%JEMALLOC_DIR%\..\include"
set "JEMALLOC_LIBRARY=%JEMALLOC_DIR%\..\lib\jemalloc.lib"

REM Verify lib file exists
if exist "%JEMALLOC_LIBRARY%" (
    echo [32mFound jemalloc library at %JEMALLOC_LIBRARY%[0m
) else (
    echo [33mWarning: jemalloc library file not found at %JEMALLOC_LIBRARY%[0m
    echo [33mCMake may fail to detect jemalloc properly[0m
)

echo [32mJemalloc environment variables set:[0m
echo [32m  CATZILLA_JEMALLOC_PATH=%CATZILLA_JEMALLOC_PATH%[0m
echo [32m  JEMALLOC_INCLUDE_DIR=%JEMALLOC_INCLUDE_DIR%[0m
echo [32m  JEMALLOC_LIBRARY=%JEMALLOC_LIBRARY%[0m

echo [32mJemalloc configuration complete![0m
exit /b 0

:end
echo [31mJemalloc configuration failed[0m
exit /b 1
