@echo off
REM Windows script to test jemalloc detection and integration
setlocal enabledelayedexpansion

echo [32m====================================[0m
echo [32m    CATZILLA JEMALLOC TEST SCRIPT   [0m
echo [32m====================================[0m

REM 1. Configure jemalloc
echo.
echo [33m1. Configuring jemalloc environment[0m
call "%~dp0jemalloc_helper.bat"

if %errorlevel% neq 0 (
    echo [31mJemalloc configuration failed! This test will likely fail.[0m
) else (
    echo [32mJemalloc configuration completed successfully.[0m
)

REM 2. Display environment variables
echo.
echo [33m2. Jemalloc environment variables:[0m
echo   CATZILLA_JEMALLOC_PATH: %CATZILLA_JEMALLOC_PATH%
echo   JEMALLOC_INCLUDE_DIR: %JEMALLOC_INCLUDE_DIR%
echo   JEMALLOC_LIBRARY: %JEMALLOC_LIBRARY%

REM 3. Check if files exist
echo.
echo [33m3. Checking if jemalloc files exist:[0m

if exist "%CATZILLA_JEMALLOC_PATH%" (
    echo [32m✓ DLL found: %CATZILLA_JEMALLOC_PATH%[0m
) else (
    echo [31m✗ DLL not found: %CATZILLA_JEMALLOC_PATH%[0m
)

if exist "%JEMALLOC_LIBRARY%" (
    echo [32m✓ LIB found: %JEMALLOC_LIBRARY%[0m
) else (
    echo [31m✗ LIB not found: %JEMALLOC_LIBRARY%[0m
)

REM 4. Create a temporary directory for CMake test
echo.
echo [33m4. Testing CMake jemalloc detection[0m
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
echo [33m5. Test results:[0m
if %errorlevel% neq 0 (
    echo [31m✗ CMake configuration failed[0m
    echo.
    echo [33mThis indicates jemalloc was not properly detected.[0m
    echo [33mCheck the paths and environment variables shown above.[0m
    echo.
    echo [33mFor more information, please read:[0m
    echo [33m  docs/windows_jemalloc_fix.md[0m
) else (
    echo [32m✓ CMake configuration succeeded[0m

    REM Try to build the test
    echo.
    echo Building test_jemalloc...
    cmake --build .

    if %errorlevel% neq 0 (
        echo [31m✗ Build failed[0m
        echo [33mThis indicates issues with jemalloc integration.[0m
    else (
        echo [32m✓ Build succeeded[0m

        REM Try to run the test
        if exist "Debug\test_jemalloc.exe" (
            echo.
            echo Running test_jemalloc.exe...
            Debug\test_jemalloc.exe

            if %errorlevel% neq 0 (
                echo [31m✗ Test run failed[0m
            else (
                echo [32m✓ Test run succeeded[0m
                echo [32m===================================[0m
                echo [32m  JEMALLOC TEST PASSED COMPLETELY  [0m
                echo [32m===================================[0m
            )
        ) else if exist "test_jemalloc.exe" (
            echo.
            echo Running test_jemalloc.exe...
            test_jemalloc.exe

            if %errorlevel% neq 0 (
                echo [31m✗ Test run failed[0m
            else (
                echo [32m✓ Test run succeeded[0m
                echo [32m===================================[0m
                echo [32m  JEMALLOC TEST PASSED COMPLETELY  [0m
                echo [32m===================================[0m
            )
        ) else (
            echo [31m✗ Could not find test executable[0m
        )
    )
)

REM Clean up
cd "%~dp0"
echo.
echo Cleaning up temporary files...
rmdir /s /q "%TEST_DIR%"

echo.
echo [32mTest script completed.[0m
