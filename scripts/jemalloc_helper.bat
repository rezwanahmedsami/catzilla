@echo off
REM Catzilla Jemalloc Helper Script for Windows
REM This script helps detect and configure jemalloc for Windows environments

setlocal enabledelayedexpansion

echo Catzilla Jemalloc Helper for Windows
echo ===================================

REM Check if jemalloc is available via vcpkg
if exist "C:\vcpkg\installed\x64-windows\bin\jemalloc.dll" (
    echo Found jemalloc via vcpkg
    set "JEMALLOC_PATH=C:\vcpkg\installed\x64-windows\bin\jemalloc.dll"
    goto :configure
)

REM Check local vcpkg installation
if exist "%USERPROFILE%\vcpkg\installed\x64-windows\bin\jemalloc.dll" (
    echo Found jemalloc in user vcpkg installation
    set "JEMALLOC_PATH=%USERPROFILE%\vcpkg\installed\x64-windows\bin\jemalloc.dll"
    goto :configure
)

REM Check if jemalloc is in system PATH
where jemalloc.dll >nul 2>&1
if %errorlevel% == 0 (
    echo Found jemalloc in system PATH
    for /f "tokens=*" %%i in ('where jemalloc.dll') do set "JEMALLOC_PATH=%%i"
    goto :configure
)

echo jemalloc not found. Attempting automatic installation...
goto :install

:install
REM Install jemalloc via vcpkg if available
if exist "C:\vcpkg\vcpkg.exe" (
    echo Installing jemalloc via vcpkg...
    C:\vcpkg\vcpkg.exe install jemalloc:x64-windows
    if %errorlevel% == 0 (
        set "JEMALLOC_PATH=C:\vcpkg\installed\x64-windows\bin\jemalloc.dll"
        echo Successfully installed jemalloc
        goto :configure
    )
)

echo Failed to install jemalloc automatically.
echo Please install manually using one of these methods:
echo   1. Install vcpkg and run: vcpkg install jemalloc:x64-windows
echo   2. Download from: https://github.com/jemalloc/jemalloc/releases
goto :end

:configure
echo Configuring jemalloc for Catzilla...
echo Jemalloc path: %JEMALLOC_PATH%

REM Get directory containing jemalloc.dll
for %%i in ("%JEMALLOC_PATH%") do set "JEMALLOC_DIR=%%~dpi"

REM Add to PATH if not already there
echo %PATH% | findstr /C:"%JEMALLOC_DIR%" >nul
if %errorlevel% neq 0 (
    set "PATH=%JEMALLOC_DIR%;%PATH%"
    echo Added jemalloc directory to PATH
) else (
    echo jemalloc directory already in PATH
)

REM Set environment variables for CMake to find jemalloc
set "CATZILLA_JEMALLOC_PATH=%JEMALLOC_PATH%"
set "JEMALLOC_INCLUDE_DIR=%JEMALLOC_DIR%\..\include"
set "JEMALLOC_LIBRARY=%JEMALLOC_DIR%\..\lib\jemalloc.lib"

REM Verify lib file exists
if exist "%JEMALLOC_LIBRARY%" (
    echo Found jemalloc library at %JEMALLOC_LIBRARY%
) else (
    echo Warning: jemalloc library file not found at %JEMALLOC_LIBRARY%
    echo CMake may fail to detect jemalloc properly
)

echo Jemalloc environment variables set:
echo   CATZILLA_JEMALLOC_PATH=%CATZILLA_JEMALLOC_PATH%
echo   JEMALLOC_INCLUDE_DIR=%JEMALLOC_INCLUDE_DIR%
echo   JEMALLOC_LIBRARY=%JEMALLOC_LIBRARY%

echo Jemalloc configuration complete!
exit /b 0

:end
echo Jemalloc configuration failed
exit /b 1
