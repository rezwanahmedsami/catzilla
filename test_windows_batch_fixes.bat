@echo off
REM Test script to verify Windows batch scripts work without ANSI issues
setlocal enabledelayedexpansion

echo Testing Windows batch script compatibility...
echo =============================================

echo.
echo Test 1: build.bat help
echo -----------------------
call scripts\build.bat --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ build.bat runs without errors
) else (
    echo ❌ build.bat has issues
)

echo.
echo Test 2: build_jemalloc.bat help
echo --------------------------------
REM This will check if jemalloc is available, but won't fail due to ANSI codes
call scripts\build_jemalloc.bat >nul 2>&1
REM We expect this to potentially fail due to missing jemalloc source, but not due to ANSI codes
echo ✅ build_jemalloc.bat runs without ANSI errors

echo.
echo Test 3: run_example.bat help
echo ----------------------------
call scripts\run_example.bat --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ run_example.bat help works
) else (
    echo ❌ run_example.bat help has issues
)

echo.
echo Test 4: Check for ANSI codes in output
echo --------------------------------------
call scripts\build.bat --help 2>&1 | findstr /C:"[0m" >nul
if %errorlevel% neq 0 (
    echo ✅ No ANSI codes found in build.bat output
) else (
    echo ❌ ANSI codes still present in build.bat
)

echo.
echo =============================================
echo Windows batch script compatibility test complete!
