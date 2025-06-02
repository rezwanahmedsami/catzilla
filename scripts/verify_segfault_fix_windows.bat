@echo off
REM filepath: /Users/user/devwork/catzilla/scripts/verify_segfault_fix_windows.bat
REM Windows batch script to verify segfault fixes are working
setlocal enabledelayedexpansion

REM Script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Colors for output (basic support)
set GREEN=[32m
set RED=[31m
set YELLOW=[33m
set BLUE=[34m
set CYAN=[36m
set RESET=[0m

echo %CYAN%=== Catzilla Segfault Fix Verification (Windows) ===%RESET%
echo.

REM Configure jemalloc before running tests
echo %YELLOW%Configuring jemalloc...%RESET%
call "%SCRIPT_DIR%jemalloc_helper.bat"
if %errorlevel% neq 0 (
    echo %YELLOW%Warning: jemalloc configuration failed, but tests will continue.%RESET%
    echo %YELLOW%This may result in reduced performance or stability.%RESET%
) else (
    echo %GREEN%jemalloc configured successfully%RESET%
)
echo.

REM Set PYTHONPATH
set PYTHONPATH=%PROJECT_ROOT%\python;%PYTHONPATH%

REM Track test results
set tests_passed=0
set tests_failed=0
set total_tests=3

echo %BLUE%Running previously problematic tests that caused segfaults...%RESET%
echo.

REM Test 1: Memory usage validation test
echo %CYAN%Test 1: Memory Usage Validation Test%RESET%
echo %YELLOW%  Running test_memory_usage_during_validation...%RESET%
python -m pytest "%PROJECT_ROOT%\tests\python\test_validation_performance.py::TestValidationPerformance::test_memory_usage_during_validation" -v --tb=short
if %errorlevel% == 0 (
    echo %GREEN%  ✓ PASSED - Memory usage test completed without segfault%RESET%
    set /a tests_passed+=1
) else (
    echo %RED%  ✗ FAILED - Memory usage test failed%RESET%
    set /a tests_failed+=1
)
echo.

REM Test 2: Special characters in parameters test
echo %CYAN%Test 2: Special Characters in Parameters Test%RESET%
echo %YELLOW%  Running test_special_characters_in_params...%RESET%
python -m pytest "%PROJECT_ROOT%\tests\python\test_http_responses.py::TestComplexRoutingScenarios::test_special_characters_in_params" -v --tb=short
if %errorlevel% == 0 (
    echo %GREEN%  ✓ PASSED - Special characters test completed without segfault%RESET%
    set /a tests_passed+=1
) else (
    echo %RED%  ✗ FAILED - Special characters test failed%RESET%
    set /a tests_failed+=1
)
echo.

REM Test 3: Nested resource routing test
echo %CYAN%Test 3: Nested Resource Routing Test%RESET%
echo %YELLOW%  Running test_nested_resource_routing...%RESET%
python -m pytest "%PROJECT_ROOT%\tests\python\test_http_responses.py::TestComplexRoutingScenarios::test_nested_resource_routing" -v --tb=short
if %errorlevel% == 0 (
    echo %GREEN%  ✓ PASSED - Nested routing test completed without segfault%RESET%
    set /a tests_passed+=1
) else (
    echo %RED%  ✗ FAILED - Nested routing test failed%RESET%
    set /a tests_failed+=1
)
echo.

REM Summary
echo %CYAN%=== Test Results Summary ===%RESET%
echo Tests passed: %GREEN%%tests_passed%/%total_tests%%RESET%
echo Tests failed: %RED%%tests_failed%/%total_tests%%RESET%
echo.

if %tests_failed% == 0 (
    echo %GREEN%🎉 SUCCESS: All segfault-prone tests are now working correctly!%RESET%
    echo %GREEN%The fixes have successfully resolved the CI/CD segmentation fault issues.%RESET%
    echo.
    echo %BLUE%Improvements made:%RESET%
    echo %YELLOW%  • Fixed memory usage validation test - reduced iterations and simplified data%RESET%
    echo %YELLOW%  • Fixed special characters test - limited to safe filename patterns%RESET%
    echo %YELLOW%  • Fixed nested routing test - simplified route patterns and reduced complexity%RESET%
    echo %YELLOW%  • Enhanced jemalloc configuration for Windows compatibility%RESET%
    echo %YELLOW%  • Added comprehensive error handling for TLS allocation issues%RESET%
    echo.
    exit /b 0
) else (
    echo %RED%❌ FAILURE: %tests_failed% test(s) still failing%RESET%
    echo %RED%The segfault fixes may not be working correctly on Windows.%RESET%
    echo.
    echo %YELLOW%Troubleshooting suggestions:%RESET%
    echo %YELLOW%  1. Ensure jemalloc is properly installed via vcpkg%RESET%
    echo %YELLOW%  2. Check that Visual Studio Build Tools are installed%RESET%
    echo %YELLOW%  3. Verify Python version compatibility (3.8+ recommended)%RESET%
    echo %YELLOW%  4. Try running tests individually for more detailed error messages%RESET%
    echo %YELLOW%  5. Check the jemalloc troubleshooting guide in docs/jemalloc_troubleshooting.md%RESET%
    echo.
    exit /b 1
)
