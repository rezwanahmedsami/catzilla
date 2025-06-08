@echo off
REM Windows script to test jemalloc detection and integration
setlocal enabledelayedexpansion

echo ====================================
echo     CATZILLA JEMALLOC TEST SCRIPT
echo ====================================

REM 1. Configure jemalloc
echo.
echo 1. Configuring jemalloc environment
call "%~dp0jemalloc_helper.bat"

if %errorlevel% neq 0 (
    echo Jemalloc configuration failed! This test will likely fail.
) else (
    echo Jemalloc configuration completed successfully.
)

REM 2. Display environment variables
echo.
echo 2. Jemalloc environment variables:
echo   CATZILLA_JEMALLOC_PATH: %CATZILLA_JEMALLOC_PATH%
echo   JEMALLOC_INCLUDE_DIR: %JEMALLOC_INCLUDE_DIR%
echo   JEMALLOC_LIBRARY: %JEMALLOC_LIBRARY%

REM 3. Check if files exist
echo.
echo 3. Checking if jemalloc files exist:

if exist "%CATZILLA_JEMALLOC_PATH%" (
    echo ✓ DLL found: %CATZILLA_JEMALLOC_PATH%
) else (
    echo ✗ DLL not found: %CATZILLA_JEMALLOC_PATH%
)

if exist "%JEMALLOC_LIBRARY%" (
    echo ✓ LIB found: %JEMALLOC_LIBRARY%
) else (
    echo ✗ LIB not found: %JEMALLOC_LIBRARY%
)

REM 4. Create a temporary directory for CMake test
echo.
echo 4. Testing CMake jemalloc detection
set TEST_DIR=%TEMP%\catzilla_jemalloc_test
if exist "%TEST_DIR%" rmdir /s /q "%TEST_DIR%"
mkdir "%TEST_DIR%"
cd "%TEST_DIR%"

REM Create a simple CMakeLists.txt
echo Writing test CMakeLists.txt...
(
echo cmake_minimum_required^(VERSION 3.14^)
echo project^(jemalloc_test^)
echo.
echo # Set paths for jemalloc detection
echo if^(DEFINED ENV{JEMALLOC_LIBRARY}^)
echo     message^(STATUS "JEMALLOC_LIBRARY from env: $ENV{JEMALLOC_LIBRARY}"^)
echo     set^(JEMALLOC_LIBRARY "$ENV{JEMALLOC_LIBRARY}"^)
echo endif^(^)
echo.
echo if^(DEFINED ENV{JEMALLOC_INCLUDE_DIR}^)
echo     message^(STATUS "JEMALLOC_INCLUDE_DIR from env: $ENV{JEMALLOC_INCLUDE_DIR}"^)
echo     set^(JEMALLOC_INCLUDE_DIR "$ENV{JEMALLOC_INCLUDE_DIR}"^)
echo endif^(^)
echo.
echo # Try to find jemalloc
echo if^(JEMALLOC_LIBRARY AND JEMALLOC_INCLUDE_DIR^)
echo     message^(STATUS "✅ jemalloc found manually: ${JEMALLOC_LIBRARY}"^)
echo     message^(STATUS "   Include dirs: ${JEMALLOC_INCLUDE_DIR}"^)
echo     set^(JEMALLOC_FOUND TRUE^)
echo else^(^)
echo     find_path^(JEMALLOC_INCLUDE_DIR jemalloc/jemalloc.h^)
echo     find_library^(JEMALLOC_LIBRARY NAMES jemalloc^)
echo.
echo     if^(JEMALLOC_INCLUDE_DIR AND JEMALLOC_LIBRARY^)
echo         message^(STATUS "✅ jemalloc found by auto-detection: ${JEMALLOC_LIBRARY}"^)
echo         message^(STATUS "   Include dirs: ${JEMALLOC_INCLUDE_DIR}"^)
echo         set^(JEMALLOC_FOUND TRUE^)
echo     else^(^)
echo         message^(WARNING "⚠️ jemalloc not found!"^)
echo     endif^(^)
echo endif^(^)
echo.
echo # Create a test target that links against jemalloc
echo if^(JEMALLOC_FOUND^)
echo     add_executable^(test_jemalloc test_jemalloc.c^)
echo     target_include_directories^(test_jemalloc PRIVATE ${JEMALLOC_INCLUDE_DIR}^)
echo     target_link_libraries^(test_jemalloc PRIVATE ${JEMALLOC_LIBRARY}^)
echo endif^(^)
) > CMakeLists.txt

REM Create a simple C file to test linking against jemalloc
echo Writing test_jemalloc.c...
(
echo #include ^<stdio.h^>
echo #include ^<jemalloc/jemalloc.h^>
echo.
echo int main^(void^) {
echo     printf^("Testing jemalloc integration\n"^);
echo     void *ptr = malloc^(1024^);
echo     if ^(ptr^) {
echo         printf^("✓ malloc works\n"^);
echo         free^(ptr^);
echo         printf^("✓ free works\n"^);
echo     } else {
echo         printf^("✗ malloc failed\n"^);
echo         return 1;
echo     }
echo     return 0;
echo }
) > test_jemalloc.c

REM Run CMake
echo.
echo Running CMake configuration...
cmake . 2>&1

REM Check outcome
echo.
echo 5. Test results:
if %errorlevel% neq 0 (
    echo ✗ CMake configuration failed
    echo.
    echo This indicates jemalloc was not properly detected.
    echo Check the paths and environment variables shown above.
    echo.
    echo For more information, please read:
    echo   docs/windows_jemalloc_fix.md
) else (
    echo ✓ CMake configuration succeeded

    REM Try to build the test
    echo.
    echo Building test_jemalloc...
    cmake --build . --config Release

    if %errorlevel% neq 0 (
        echo ✗ Build failed
        echo This indicates issues with jemalloc integration.
    else (
        echo ✓ Build succeeded

        REM Try to run the test
        if exist "Release\test_jemalloc.exe" (
            echo.
            echo Running test_jemalloc.exe...
            Release\test_jemalloc.exe

            if %errorlevel% neq 0 (
                echo ✗ Test run failed
            else (
                echo ✓ Test run succeeded
                echo ===================================
                echo   JEMALLOC TEST PASSED COMPLETELY
                echo ===================================
            )
        ) else if exist "test_jemalloc.exe" (
            echo.
            echo Running test_jemalloc.exe...
            test_jemalloc.exe

            if %errorlevel% neq 0 (
                echo ✗ Test run failed
            else (
                echo ✓ Test run succeeded
                echo ===================================
                echo   JEMALLOC TEST PASSED COMPLETELY
                echo ===================================
            )
        ) else (
            echo ✗ Could not find test executable
        )
    )
)

REM Clean up
cd "%~dp0"
echo.
echo Cleaning up temporary files...
rmdir /s /q "%TEST_DIR%"

echo.
echo Test script completed.
